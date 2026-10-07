# -*- coding: utf-8 -*-
"""课程考核 AI 出题器 —— 三批分档出题 + 独立复核 + 相似去重。

设计见 docs/plans/2026-10-07-course-exam-bank-design.md §5 / §7:
- 素材:课件逐页讲解 pages=[{'label','notes'}],带页号;
- 按难度分三批出题(每批只给本档规则与题型约束),批间把已有题干传给 AI 防重复;
- 另起一次调用独立复核(不告知原难度):重评难度 + 校验唯一正确答案且课件有依据;
  一致 → active,不一致或答案存疑 → review(不进抽题池,待管理员确认);
- 题干去标点空白后相似度 ≥0.85 视为重复,保留先出现的。

纯函数部分(prompt / normalize / dedupe / merge_review / generate_course)不碰 DB,
AI client 可注入,便于离线单测;run_generation_job 才落库 + 发站内通知。
"""
import difflib
import json
import logging
import re
import threading

from app.services import course_quiz
from app.services.course_exam import logic as L
from app.services.wiki import claude_client

logger = logging.getLogger(__name__)

# ---------- 规则常量 ----------

DIFF_NAMES = {1: '易', 2: '中', 3: '难'}
DIFF_RULES = {
    1: '易:课件单页原话可答,记忆类',
    2: '中:理解/比较,需联系同一主题 2 个知识点',
    3: '难:客户场景应用,跨页综合,干扰项似是而非',
}
TYPE_ALLOWED = {1: ('single', 'judge'), 2: ('single', 'multi', 'judge'), 3: ('single', 'multi')}
TYPE_NAMES = {'single': '单选', 'multi': '多选', 'judge': '判断'}
TYPE_SHARE = {'single': 70, 'multi': 10, 'judge': 20}
DEFAULT_PLAN = {1: 50, 2: 30, 3: 20}

BATCH_SIZE = 25          # 单次调用最多出多少题
REVIEW_SIZE = 40         # 单次复核最多多少题
EXISTING_LIMIT = 200     # 「已存在题干」最多附多少条
MAX_PER_LEVEL = 100      # 每档上限,防误传超大值
DUP_RATIO = 0.85

_JSON_RULE = (
    "【关键】字符串值内严禁出现英文双引号(\"),需要引用时一律用中文书名号「」;"
    "所有内容必须是合法 JSON(能被 JSON.parse 解析),特殊字符正确转义。\n"
    "只输出 JSON,不要任何解释或 markdown 代码围栏。"
)

_GEN_SYSTEM = (
    "你是企业内训出题助手。根据给定的培训课件逐页讲解内容出考核题,"
    "检验学员是否真正理解了产品卖点与关键信息。要求:\n"
    "1. 题目紧扣讲解内容,不出课件里没有的知识;\n"
    "2. 严格按要求的难度档与题型出题,覆盖不同页的要点,不要都集中在某一页;\n"
    "3. 每题只有唯一正确答案(多选题为唯一正确组合),干扰项要合理、不能一眼假;\n"
    "4. 每题给简短解析(explain),说明正确答案的依据;\n"
    "5. " + _JSON_RULE
)

_REVIEW_SYSTEM = (
    "你是独立的考题质量审核员,对照培训课件逐页讲解审核一批考题。要求:\n"
    "1. 按难度定义独立评定每题难度(1 易 / 2 中 / 3 难),只看题目本身;\n"
    "2. 校验给出的答案是否唯一正确且在课件中有依据;干扰项过假(一眼可排除)也视为不合格;\n"
    "3. 不合格时在 note 里用一句话说明理由;\n"
    "4. " + _JSON_RULE
)


# ---------- prompt ----------

def _pages_text(pages):
    parts = ["以下是课件逐页讲解(label=页名, notes=讲解):\n"]
    for i, p in enumerate(pages, 1):
        parts.append(f"【第{i}页·{p.get('label', '')}】{p.get('notes', '')}")
    return "\n".join(parts)


_EXAMPLES = {
    'single': '{"type":"single","question":"题干","options":["选项A","选项B","选项C","选项D"],"answer":0,"explain":"解析","page":1}',
    'multi': '{"type":"multi","question":"题干","options":["选项A","选项B","选项C","选项D"],"answer":[0,2],"explain":"解析","page":2}',
    'judge': '{"type":"judge","question":"题干","answer":true,"explain":"解析","page":3}',
}
_ANSWER_RULES = {
    'single': 'single 的 answer 是正确选项下标(从 0 起)',
    'multi': 'multi 的 answer 是 ≥2 个正确选项下标的列表(且少于选项数,选项 4 个)',
    'judge': 'judge 的 answer 是 true/false',
}


def type_mix(difficulty):
    """本档允许题型的目标占比(按 单选70/多选10/判断20 归一),返回 [(qtype, 百分比)]。"""
    allowed = TYPE_ALLOWED[difficulty]
    total = sum(TYPE_SHARE[t] for t in allowed)
    return [(t, round(TYPE_SHARE[t] * 100 / total)) for t in allowed]


def build_batch_prompt(pages, difficulty, n, existing_questions=None, focus_page=None, avoid=None):
    """单档出题 prompt。focus_page / avoid 供单题重出:限定页号、换角度。"""
    allowed = TYPE_ALLOWED[difficulty]
    mix = '、'.join(f"{TYPE_NAMES[t]} 约{pct}%" for t, pct in type_mix(difficulty))
    parts = [_pages_text(pages), '']
    parts.append(f"请出 {n} 道【{DIFF_NAMES[difficulty]}】档题目。")
    parts.append(f"难度定义 —— {DIFF_RULES[difficulty]}。")
    parts.append(f"题型只允许:{'/'.join(allowed)}({'、'.join(TYPE_NAMES[t] for t in allowed)})。")
    parts.append(f"题型配比:{mix}。")
    if focus_page:
        parts.append(f"题目必须出自第{focus_page}页的讲解内容,page 填 {focus_page}。")
    if avoid:
        parts.append(f"这是对原题「{avoid}」的重出:考查同一页内容,但换一个角度,不得与原题实质相同。")
    existing = [q for q in (existing_questions or []) if q][-EXISTING_LIMIT:]
    if existing:
        parts.append("以下题干已存在,不得重复或换汤不换药:")
        parts.extend(f"- {q}" for q in existing)
    examples = ',\n'.join(f'  {_EXAMPLES[t]}' for t in allowed)
    rules = ';'.join(_ANSWER_RULES[t] for t in allowed)
    parts.append(
        "\n严格输出如下 JSON 结构:\n"
        '{"questions":[\n' + examples + '\n]}\n'
        + rules + ";page 是出处页号(从 1 起)。"
    )
    return "\n".join(parts)


def _answer_text(q):
    if q['qtype'] == 'judge':
        return '正确' if q['answer'] else '错误'
    letters = 'ABCDEFGHIJ'
    idx = q['answer'] if isinstance(q['answer'], list) else [q['answer']]
    return ','.join(letters[i] if i < len(letters) else str(i) for i in idx)


def build_review_prompt(pages, qs):
    """复核 prompt:只给题干/选项/答案,不给原难度。"""
    letters = 'ABCDEFGHIJ'
    parts = [_pages_text(pages), '', "难度定义:"]
    parts.extend(f"{d} = {DIFF_RULES[d]}" for d in (1, 2, 3))
    parts.append("\n待审核的题目:")
    for i, q in enumerate(qs):
        parts.append(f"[{i}]({TYPE_NAMES.get(q['qtype'], q['qtype'])}){q['question']}")
        for j, o in enumerate(q.get('options') or []):
            parts.append(f"   {letters[j] if j < len(letters) else j}. {o}")
        parts.append(f"   给定答案:{_answer_text(q)}")
    parts.append(
        "\n逐题输出(index 与上面方括号编号一致,每题都要有):\n"
        '{"reviews":[{"index":0,"difficulty":1,"answer_ok":true,"note":""}]}\n'
        "difficulty 为你独立评定的难度 1/2/3;answer_ok 为 true 表示答案唯一正确、课件有依据且干扰项合理。"
    )
    return "\n".join(parts)


# ---------- 解析 / 清洗 ----------

def _strip_fence(text):
    t = (text or '').strip()
    t = re.sub(r'^```(?:json)?\s*', '', t)
    return re.sub(r'\s*```$', '', t)


def _salvage(text, marker):
    """整体解析失败时,从第一个 '[' 之后逐个顶层 {...} 抠(兼容被 max_tokens 截断的输出)。"""
    t = _strip_fence(text)
    start = t.find('[')
    out = []
    for obj in course_quiz._scan_objects(t[start + 1:] if start >= 0 else t):
        if marker not in obj:
            continue
        try:
            out.append(json.loads(obj))
        except ValueError:
            continue
    return out


def parse_questions(text):
    try:
        return course_quiz._extract_json(text)
    except ValueError:
        got = [o for o in _salvage(text, '"question"') if isinstance(o, dict) and 'type' in o]
        if got:
            logger.warning('出题 JSON 整体解析失败,容错捞回 %d 道', len(got))
            return {'questions': got}
        raise


def parse_review(text):
    t = _strip_fence(text)
    try:
        data = json.loads(t)
        if isinstance(data, list):
            data = {'reviews': data}
        if isinstance(data, dict):
            return data
    except ValueError:
        pass
    got = _salvage(text, '"index"')
    if got:
        logger.warning('复核 JSON 整体解析失败,容错捞回 %d 条', len(got))
        return {'reviews': got}
    raise ValueError('复核输出无法解析为 JSON')


def _page_no(x, n_pages):
    p = L._as_int(x)
    if p is None or p < 1 or (n_pages is not None and p > n_pages):
        return None
    return p


def normalize(raw, difficulty, n_pages=None):
    """AI 原始输出 → 模型字段名的题目 dict 列表;结构校验交给 logic.normalize_question。"""
    items = raw if isinstance(raw, list) else ((raw or {}).get('questions') or [])
    out, dropped = [], 0
    for item in items:
        try:
            if not isinstance(item, dict):
                raise ValueError('非对象')
            qtype = item.get('type')
            if qtype not in TYPE_ALLOWED[difficulty]:
                raise ValueError('题型不符合本档约束')
            question = item.get('question')
            if not isinstance(question, str) or not question.strip():
                raise ValueError('题干为空')
            opts = item.get('options')
            if qtype == 'judge':
                opts = None
            elif isinstance(opts, list):
                opts = [o.strip() if isinstance(o, str) else o for o in opts]
            q = L.normalize_question({'qtype': qtype, 'difficulty': difficulty, 'options': opts,
                                      'answer': item.get('answer')})
            explain = item.get('explain')
            out.append({'qtype': qtype, 'difficulty': difficulty, 'question': question.strip(),
                        'options': q.get('options'), 'answer': q['answer'],
                        'explain': explain.strip() if isinstance(explain, str) else '',
                        'source_page': _page_no(item.get('page'), n_pages)})
        except ValueError:
            dropped += 1
    if dropped:
        logger.info('出题清洗:难度 %s 丢弃 %d 道不合格题', difficulty, dropped)
    return out


# ---------- 去重 / 复核合并 ----------

def _norm_text(s):
    return re.sub(r'[\W_]+', '', s or '')


def _similar(a, b):
    return a == b or difflib.SequenceMatcher(None, a, b).ratio() >= DUP_RATIO


def dedupe(qs, existing=None):
    """题干相似度去重,保留先出现的;existing 为已有题干(只用于比对,不返回)。"""
    seen = [_norm_text(t) for t in (existing or []) if _norm_text(t)]
    out = []
    for q in qs:
        t = _norm_text(q.get('question'))
        if not t or any(_similar(t, s) for s in seen):
            continue
        seen.append(t)
        out.append(q)
    return out


def merge_review(qs, review):
    """把复核结果并回题目:ai_difficulty 写入;答案无疑且难度一致 → active,否则 review。"""
    by_idx = {}
    for r in ((review or {}).get('reviews') or []):
        if isinstance(r, dict):
            i = L._as_int(r.get('index'))
            if i is not None and 0 <= i < len(qs) and i not in by_idx:
                by_idx[i] = r
    out = []
    for i, q in enumerate(qs):
        q = dict(q)
        r = by_idx.get(i)
        if r is None:
            q.update(status='review', ai_difficulty=None, review_note='复核未返回该题结果')
            out.append(q)
            continue
        ai_d = L._as_int(r.get('difficulty'))
        ai_d = ai_d if ai_d in L.POINTS else None
        answer_ok = r.get('answer_ok') is True
        q['ai_difficulty'] = ai_d
        if answer_ok and ai_d == q['difficulty']:
            q.update(status='active', review_note=None)
        else:
            notes = []
            if not answer_ok:
                notes.append('答案存疑')
            if ai_d != q['difficulty']:
                notes.append(f"难度不一致:标注 {q['difficulty']} / 复核 {ai_d if ai_d else '未评'}")
            note = r.get('note')
            if isinstance(note, str) and note.strip():
                notes.append(note.strip())
            q.update(status='review', review_note=';'.join(notes))
        out.append(q)
    return out


# ---------- 编排 ----------

def _clean_plan(plan):
    out = {}
    for k, v in (plan or {}).items():
        d, n = L._as_int(k), L._as_int(v)
        if d in L.POINTS and n and n > 0:
            out[d] = min(n, MAX_PER_LEVEL)
    return out


def _gen_call(client, pages, difficulty, n, existing, **kw):
    resp = client.complete(
        system=_GEN_SYSTEM,
        user=build_batch_prompt(pages, difficulty, n, existing, **kw),
        model=claude_client.QUERY_MODEL,
        max_tokens=min(16000, 2000 + n * 600),
    )
    return normalize(parse_questions(resp.text), difficulty, n_pages=len(pages))


def _review_chunk(client, pages, chunk):
    try:
        resp = client.complete(
            system=_REVIEW_SYSTEM,
            user=build_review_prompt(pages, chunk),
            model=claude_client.QUERY_MODEL,
            max_tokens=min(16000, 1000 + len(chunk) * 150),
        )
        return merge_review(chunk, parse_review(resp.text))
    except Exception as e:      # 复核失败不丢题,整块转人工待审
        logger.exception('题目复核调用失败,本块 %d 题转待审', len(chunk))
        return [dict(q, status='review', ai_difficulty=None, review_note=f'复核失败:{str(e)[:100]}')
                for q in chunk]


def generate_course(pages, plan=DEFAULT_PLAN, client=None, existing_questions=None):
    """三档分批出题 → 去重 → 复核。返回带 status/ai_difficulty/review_note 的题目 dict 列表。

    existing_questions:课程已有题干(追加出题时传入,防重复)。
    """
    plan = _clean_plan(plan)
    own = client is None
    if own:
        client = claude_client.WikiClaudeClient()
    try:
        existing = [q for q in (existing_questions or []) if q]
        made = []
        failures = 0
        for d in (1, 2, 3):
            remaining = plan.get(d, 0)
            while remaining > 0:
                k = min(BATCH_SIZE, remaining)
                remaining -= k
                try:
                    got = dedupe(_gen_call(client, pages, d, k, existing + [q['question'] for q in made]),
                                 existing=existing + [q['question'] for q in made])
                except Exception:
                    failures += 1
                    logger.exception('出题调用失败:难度 %s,本批 %d 题', d, k)
                    continue
                made.extend(got)
        if not made:
            raise ValueError('AI 未生成有效题目' + (f'(失败 {failures} 批)' if failures else ''))
        out = []
        for i in range(0, len(made), REVIEW_SIZE):
            out.extend(_review_chunk(client, pages, made[i:i + REVIEW_SIZE]))
        return out
    finally:
        if own:
            client.close()


def regenerate_one(pages, q, client=None):
    """单题 AI 重出:同难度、同页、换角度。返回清洗后的新题 dict;输出不可用抛 ValueError。"""
    d = L._as_int(q.get('difficulty'))
    if d not in L.POINTS:
        raise ValueError('原题难度非法')
    page = _page_no(q.get('source_page'), len(pages))
    own = client is None
    if own:
        client = claude_client.WikiClaudeClient()
    try:
        got = _gen_call(client, pages, d, 1, [q.get('question') or ''],
                        focus_page=page, avoid=q.get('question') or '')
    finally:
        if own:
            client.close()
    got = dedupe(got, existing=[q.get('question') or ''])
    if not got:
        raise ValueError('AI 未生成可用的新题')
    new = got[0]
    new['source_page'] = page
    return new


# ---------- 后台任务 ----------

_RUNNING = set()
_LOCK = threading.Lock()


def is_running(course_key):
    with _LOCK:
        return course_key in _RUNNING


def _notify(user_id, title, content, course_id):
    from app.models.message import Message
    from app import db
    db.session.add(Message(
        message_type='course_bank_ready', sender_id=user_id, recipient_id=user_id,
        title=title, content=content, related_object_type='course', related_object_id=course_id))


def run_generation_job(app, course_key, pages, user_id, plan=DEFAULT_PLAN, replace=False, client=None):
    """后台线程体:出题 → (replace 时停用旧 AI 题)→ 落库 → 站内通知。异常写失败通知。"""
    try:
        with app.app_context():
            from app import db
            from app.models.course import InteractiveCourse
            from app.models.course_exam import CourseQuizQuestion
            course = InteractiveCourse.query.filter_by(key=course_key).first()
            course_id = course.id if course else None
            title = course.title if course else course_key
            existing = []
            if not replace:
                existing = [r.question for r in CourseQuizQuestion.query.filter(
                    CourseQuizQuestion.course_key == course_key,
                    CourseQuizQuestion.status != 'disabled').all()]
            db.session.rollback()       # 出题耗时数分钟,别挂着空闲事务
            try:
                qs = generate_course(pages, plan=plan, client=client, existing_questions=existing)
                if replace:
                    CourseQuizQuestion.query.filter(
                        CourseQuizQuestion.course_key == course_key,
                        CourseQuizQuestion.origin == 'ai',
                        CourseQuizQuestion.status != 'disabled',
                    ).update({'status': 'disabled'}, synchronize_session=False)
                for q in qs:
                    db.session.add(CourseQuizQuestion(
                        course_key=course_key, qtype=q['qtype'], difficulty=q['difficulty'],
                        ai_difficulty=q.get('ai_difficulty'), question=q['question'],
                        options=q.get('options'), answer=q['answer'], explain=q.get('explain') or None,
                        source_page=q.get('source_page'), status=q['status'], origin='ai',
                        review_note=q.get('review_note'), created_by=user_id))
                n_active = sum(1 for q in qs if q['status'] == 'active')
                _notify(user_id, '题库生成完成',
                        f'{title}:启用 {n_active} 题,待审 {len(qs) - n_active} 题', course_id)
                db.session.commit()
                logger.info('题库生成完成 %s:启用 %d,待审 %d', course_key, n_active, len(qs) - n_active)
            except Exception as e:
                db.session.rollback()
                logger.exception('题库生成失败 %s', course_key)
                try:
                    _notify(user_id, '题库生成失败', f'{title}:{str(e)[:200]}', course_id)
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                    logger.exception('题库生成失败通知写入失败 %s', course_key)
    finally:
        with _LOCK:
            _RUNNING.discard(course_key)


def start_generation(app, course_key, pages, user_id, plan=DEFAULT_PLAN, replace=False):
    """起后台线程出题;同一课已在生成中返回 False。app 须为真实对象(current_app._get_current_object())。"""
    with _LOCK:
        if course_key in _RUNNING:
            return False
        _RUNNING.add(course_key)
    try:
        threading.Thread(target=run_generation_job, name=f'course-exam-gen-{course_key}', daemon=True,
                         args=(app, course_key, pages, user_id, plan, replace)).start()
    except Exception:
        with _LOCK:
            _RUNNING.discard(course_key)
        raise
    return True
