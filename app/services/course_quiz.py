# -*- coding: utf-8 -*-
"""互动课程 AI 出题服务

- 用课件每页的讲解(data-speaker-notes)当素材,调 WikiClaudeClient 出题。
- 题目预生成一次,落盘 app/course_assets/<key>.quiz.json(gitignore),后续直接读。
- 题型:single(单选)/ judge(判断)。答案只留服务端,前端答题、服务端判分。
"""
import hashlib
import json
import logging
import os
import re

from app.services.wiki import claude_client

logger = logging.getLogger(__name__)

PASS_SCORE = 80
MIN_QUESTIONS = 6  # 兜底下限(极短课件也至少出这么多)


def target_num_questions(pages):
    """题量 = 页数 − 2(去掉封面/封底),并不低于下限。"""
    return max(MIN_QUESTIONS, len(pages) - 2)

_SYSTEM = (
    "你是企业内训出题助手。根据给定的培训课件逐页讲解内容,出一套考核题,"
    "检验学员是否真正理解了产品卖点与关键信息。要求:\n"
    "1. 题目紧扣讲解内容,不出课件里没有的知识;\n"
    "2. 题型只用 single(四选一单选)或 judge(判断对错);\n"
    "3. 难度适中,覆盖不同页的要点,不要都集中在某一页;\n"
    "4. 每题给简短解析(explain),说明正确答案的依据;\n"
    "5. 【关键】字符串值内严禁出现英文双引号(\"),需要引用时一律用中文书名号「」;"
    "所有内容必须是合法 JSON(能被 JSON.parse 解析),特殊字符正确转义。\n"
    "只输出 JSON,不要任何解释或 markdown 代码围栏。"
)


def _build_user_prompt(pages, num):
    parts = ["以下是课件逐页讲解(label=页名, notes=讲解):\n"]
    for i, p in enumerate(pages, 1):
        parts.append(f"【第{i}页·{p.get('label','')}】{p.get('notes','')}")
    parts.append(
        f"\n请出 {num} 道题。严格输出如下 JSON 结构:\n"
        '{"questions":[\n'
        '  {"type":"single","question":"题干","options":["选项A","选项B","选项C","选项D"],"answer":0,"explain":"解析"},\n'
        '  {"type":"judge","question":"题干","answer":true,"explain":"解析"}\n'
        ']}\n'
        "single 的 answer 是正确选项下标(0-3);judge 的 answer 是 true/false。"
    )
    return "\n".join(parts)


def _scan_objects(s):
    """按花括号深度切出顶层 {...} 对象(跳过字符串内的括号)。容错用。"""
    depth = 0
    start = None
    instr = False
    esc = False
    for i, ch in enumerate(s):
        if instr:
            if esc:
                esc = False
            elif ch == '\\':
                esc = True
            elif ch == '"':
                instr = False
            continue
        if ch == '"':
            instr = True
        elif ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}':
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    yield s[start:i + 1]
                    start = None


def _extract_json(text):
    """从模型输出里抠出题目 JSON(容错 ```json 围栏 / 整盘崩 → 逐题抠)。"""
    t = text.strip()
    t = re.sub(r'^```(?:json)?\s*', '', t)
    t = re.sub(r'\s*```$', '', t)
    # 1) 整体能解析最好
    try:
        return json.loads(t)
    except ValueError:
        pass
    # 2) 容错:逐个 {...} 题目对象单独解析,坏的跳过,捞回大多数
    salvaged = []
    for obj in _scan_objects(t):
        if '"type"' not in obj or '"question"' not in obj:
            continue
        try:
            salvaged.append(json.loads(obj))
        except ValueError:
            continue
    if salvaged:
        logger.warning('题目 JSON 整体解析失败,容错捞回 %d 道', len(salvaged))
        return {'questions': salvaged}
    raise ValueError('模型输出无法解析为 JSON')


def _normalize(course_key, raw):
    """清洗 + 补 id;过滤结构不合法的题。"""
    out = []
    for q in (raw.get('questions') or []):
        qtype = q.get('type')
        question = (q.get('question') or '').strip()
        explain = (q.get('explain') or '').strip()
        if qtype == 'single':
            opts = [str(o).strip() for o in (q.get('options') or []) if str(o).strip()]
            ans = q.get('answer')
            if len(opts) < 2 or not isinstance(ans, int) or not (0 <= ans < len(opts)):
                continue
            item = {'type': 'single', 'question': question, 'options': opts,
                    'answer': ans, 'explain': explain}
        elif qtype == 'judge':
            ans = q.get('answer')
            if not isinstance(ans, bool):
                continue
            item = {'type': 'judge', 'question': question, 'answer': ans, 'explain': explain}
        else:
            continue
        if not question:
            continue
        item['id'] = hashlib.md5((course_key + '|' + question).encode('utf-8')).hexdigest()[:16]
        out.append(item)
    return out


def _quiz_path(course_assets_dir, course_key):
    return os.path.join(course_assets_dir, course_key + '.quiz.json')


def generate_quiz(course_key, pages, num=None):
    """调 AI 生成题目(不落盘)。返回题目列表。"""
    if num is None:
        num = target_num_questions(pages)
    client = claude_client.WikiClaudeClient()
    try:
        resp = client.complete(
            system=_SYSTEM,
            user=_build_user_prompt(pages, num),
            model=claude_client.QUERY_MODEL,
            max_tokens=min(16000, 2000 + num * 600),
        )
    finally:
        client.close()
    questions = _normalize(course_key, _extract_json(resp.text))
    if not questions:
        raise ValueError('AI 未生成有效题目')
    return questions


def load_or_generate(course_key, pages, course_assets_dir, force=False):
    """有缓存读缓存,无则生成并落盘。返回题目列表(含答案,供服务端判分)。"""
    path = _quiz_path(course_assets_dir, course_key)
    if not force and os.path.isfile(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if data.get('questions'):
                return data['questions']
        except (OSError, ValueError):
            logger.warning('题库缓存损坏,重新生成: %s', path)
    questions = generate_quiz(course_key, pages)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'course_key': course_key, 'questions': questions},
                      f, ensure_ascii=False, indent=2)
    except OSError:
        logger.warning('题库写盘失败(仍返回内存题目): %s', path)
    return questions


def public_questions(questions):
    """剥掉答案/解析,给前端答题用。"""
    pub = []
    for q in questions:
        item = {'id': q['id'], 'type': q['type'], 'question': q['question']}
        if q['type'] == 'single':
            item['options'] = q['options']
        pub.append(item)
    return pub


def grade(questions, answers):
    """判分。answers: {question_id: 用户答案(single=下标int / judge=bool)}。

    返回 {score, passed, total, correct, details:[{id,is_correct,correct_answer,explain,user_answer}]}。
    """
    total = len(questions)
    correct = 0
    details = []
    for q in questions:
        ua = answers.get(q['id'])
        if q['type'] == 'single':
            ok = isinstance(ua, int) and ua == q['answer']
            corr = q['answer']
        else:  # judge
            ok = isinstance(ua, bool) and ua == q['answer']
            corr = q['answer']
        if ok:
            correct += 1
        details.append({
            'id': q['id'], 'type': q['type'], 'question': q['question'],
            'is_correct': ok, 'user_answer': ua, 'correct_answer': corr,
            'explain': q.get('explain', ''),
            'options': q.get('options'),
        })
    score = round(correct / total * 100) if total else 0
    return {'score': score, 'passed': score >= PASS_SCORE,
            'total': total, 'correct': correct, 'details': details}
