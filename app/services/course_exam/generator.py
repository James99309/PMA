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
MAX_PLAN_TOTAL = 300     # 一次出题总量上限
ECHO_LEN = 12            # 复核须回显题干前 12 字,用于校验 index 对位
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
    'multi': 'multi 的 answer 是正确选项下标的列表(至少 3 个选项、2 个及以上正确答案、且不能全选)',
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
        "\n逐题输出(index 与上面方括号编号一致,从 0 起,每题都要有;q 回显该题题干前 12 个字):\n"
        '{"reviews":[{"index":0,"q":"题干前12个字","difficulty":1,"answer_ok":true,"note":""}]}\n'
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


def _echo_key(s):
    return _norm_text(s)[:ECHO_LEN]       # 去标点空白:？/? 、「」/"" 之类差异不算错位


def _echo_matches(r, question):
    """复核回显的题干前缀与原题对得上(未回显视为对得上;互为前缀即可,容忍回显少于 12 字)。"""
    echo = r.get('q')
    a = _echo_key(echo) if isinstance(echo, str) else ''
    if not a:
        return True
    b = _echo_key(question)
    return a.startswith(b) or b.startswith(a)


def merge_review(qs, review):
    """把复核结果并回题目:ai_difficulty 写入;答案无疑且难度一致 → active,否则 review。

    index 对位容错:0 缺失而出现 len(qs) → 判定为从 1 起编号,整体 −1;
    回显题干前缀对不上的复核视为缺失(宁可转人工,也不把别题的结论安到这题上)。
    """
    by_idx = {}
    for r in ((review or {}).get('reviews') or []):
        if isinstance(r, dict):
            i = L._as_int(r.get('index'))
            if i is not None and i not in by_idx:
                by_idx[i] = r
    if qs and 0 not in by_idx and len(qs) in by_idx:
        by_idx = {i - 1: r for i, r in by_idx.items()}
    out = []
    for i, q in enumerate(qs):
        q = dict(q)
        r = by_idx.get(i)
        if r is not None and not _echo_matches(r, q.get('question')):
            r = None
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

def validate_plan(plan):
    """校验出题计划:键 ⊂ {1,2,3}、值为 ≥0 整数、总量 1..300;返回 {int: int},不合法抛 ValueError。"""
    if not isinstance(plan, dict) or not plan:
        raise ValueError('invalid plan')
    out = {}
    for k, v in plan.items():
        d, n = L._as_int(k), L._as_int(v)
        if d not in L.POINTS or n is None or n < 0:
            raise ValueError('invalid plan')
        out[d] = n
    if not 1 <= sum(out.values()) <= MAX_PLAN_TOTAL:
        raise ValueError('invalid plan')
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
        return merge_review(chunk, parse_review(resp.text)), True
    except Exception as e:      # 复核失败不丢题,整块转人工待审
        logger.exception('题目复核调用失败,本块 %d 题转待审', len(chunk))
        return [dict(q, status='review', ai_difficulty=None, review_note=f'复核失败:{str(e)[:100]}')
                for q in chunk], False


def generate_course(pages, plan=DEFAULT_PLAN, client=None, existing_questions=None, on_progress=None):
    """三档分批出题 → 去重 → 复核。返回 (questions, stats)。

    questions:带 status/ai_difficulty/review_note 的题目 dict 列表;
    stats:{requested, generated(去重后、复核前), failed_batches, review_failed_chunks}。
    existing_questions:课程里会保留的题干(用于防重复提示 + 去重)。
    on_progress:每完成一批出题 / 一组复核(成功或失败)后调用一次,后台任务用来给生成标记续心跳。
    """
    plan = validate_plan(plan)
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
                    got = []
                made.extend(got)
                if on_progress:
                    on_progress()
        if not made:
            raise ValueError('AI 未生成有效题目' + (f'(失败 {failures} 批)' if failures else ''))
        out, review_failed = [], 0
        for i in range(0, len(made), REVIEW_SIZE):
            got, ok = _review_chunk(client, pages, made[i:i + REVIEW_SIZE])
            out.extend(got)
            review_failed += 0 if ok else 1
            if on_progress:
                on_progress()
        stats = {'requested': sum(plan.values()), 'generated': len(made),
                 'failed_batches': failures, 'review_failed_chunks': review_failed}
        return out, stats
    finally:
        if own:
            client.close()


def regenerate_one(pages, q, client=None, existing_questions=None):
    """单题 AI 重出:同难度、同页、换角度。返回清洗后的新题 dict;输出不可用抛 ValueError。

    existing_questions:本课其余题干,用于防重复提示 + 去重。
    """
    d = L._as_int(q.get('difficulty'))
    if d not in L.POINTS:
        raise ValueError('原题难度非法')
    page = _page_no(q.get('source_page'), len(pages))
    avoid = [t for t in (existing_questions or []) if t] + [q.get('question') or '']
    own = client is None
    if own:
        client = claude_client.WikiClaudeClient()
    try:
        got = _gen_call(client, pages, d, 1, avoid, focus_page=page, avoid=q.get('question') or '')
    finally:
        if own:
            client.close()
    got = dedupe(got, existing=avoid)
    if not got:
        raise ValueError('AI 未生成可用的新题')
    new = got[0]
    new['source_page'] = page if page is not None else new.get('source_page')
    return new


# ---------- 后台任务 ----------
# 跨进程互斥(gunicorn 多 worker):course_exam_settings.generating_since 非空且未过期 = 生成中。
# generating_token = 抢到标记时的时间,作为本次任务的令牌(心跳 / 释放都按令牌匹配);
# generating_since = 最近一次心跳,每完成一块 AI 调用刷新一次。
# 线程异常退出 / 进程被杀后心跳停止,超过 STALE_MINUTES 即可被接管。

# 无心跳过期时限:须大于单次 AI 调用最长耗时(600s 超时),留足余量
STALE_MINUTES = 20
MIN_REPLACE_YIELD = 0.5      # 重建题库时因批次失败导致产出低于计划一半 → 不动旧题库


def replace_abort_reason(stats):
    """重建题库是否中止:只有「有批次生成失败」且产出 < 计划一半才中止(课件内容少导致题少不算)。

    返回中止原因文本,不中止返回 None。
    """
    if stats['failed_batches'] > 0 and stats['generated'] < stats['requested'] * MIN_REPLACE_YIELD:
        return (f'{stats["failed_batches"]} 批生成失败，产出不足(实际 {stats["generated"]}/'
                f'计划 {stats["requested"]})，旧题库保持不变')
    return None


def _now():
    from app.models.training import get_local_time
    return get_local_time()


def _stale_before():
    from datetime import timedelta
    return _now() - timedelta(minutes=STALE_MINUTES)


def _ensure_setting(course_key):
    """确保设置行存在;并发重复插入撞主键时回滚保存点后重新查。"""
    from sqlalchemy.exc import IntegrityError
    from app import db
    from app.models.course_exam import CourseExamSetting
    row = db.session.get(CourseExamSetting, course_key)
    if row is not None:
        return row
    try:
        with db.session.begin_nested():
            row = CourseExamSetting(course_key=course_key)
            db.session.add(row)
        return row
    except IntegrityError:
        row = CourseExamSetting.query.filter_by(course_key=course_key).populate_existing().first()
        if row is None:
            raise
        return row


def _acquire(course_key, user_id):
    """原子抢占生成标记;成功返回本次标记时间(释放时用作令牌),已被占用返回 None。会 commit。"""
    from app import db
    from app.models.course_exam import CourseExamSetting
    _ensure_setting(course_key)
    token = _now()
    n = CourseExamSetting.query.filter(
        CourseExamSetting.course_key == course_key,
        db.or_(CourseExamSetting.generating_since.is_(None),
               CourseExamSetting.generating_since < _stale_before()),
    ).update({'generating_since': token, 'generating_token': token, 'generating_by': user_id},
             synchronize_session=False)
    db.session.commit()
    return token if n else None


def _heartbeat(course_key, token):
    """续心跳:令牌仍是自己的才刷新 generating_since。返回是否刷新成功;失败只记日志。"""
    from app import db
    from app.models.course_exam import CourseExamSetting
    try:
        n = CourseExamSetting.query.filter(
            CourseExamSetting.course_key == course_key,
            CourseExamSetting.generating_token == token,
        ).update({'generating_since': _now()}, synchronize_session=False)
        db.session.commit()
        return bool(n)
    except Exception:
        db.session.rollback()
        logger.exception('出题标记心跳失败 %s', course_key)
        return False


def _release(course_key, token):
    """只清自己抢到的标记(过期被别人接管后不误清对方的)。独立小事务,失败只记日志。"""
    from app import db
    from app.models.course_exam import CourseExamSetting
    try:
        db.session.rollback()
        CourseExamSetting.query.filter(
            CourseExamSetting.course_key == course_key,
            CourseExamSetting.generating_token == token,
        ).update({'generating_since': None, 'generating_token': None, 'generating_by': None},
                 synchronize_session=False)
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception('清除出题标记失败 %s', course_key)


def is_running(course_key):
    """读库:有未过期的生成标记即视为生成中。"""
    from app.models.course_exam import CourseExamSetting
    row = CourseExamSetting.query.filter_by(course_key=course_key).populate_existing().first()
    return bool(row and row.generating_since and row.generating_since >= _stale_before())


def _notify(user_id, title, content, course_id):
    from app.models.message import Message
    from app import db
    db.session.add(Message(
        message_type='course_bank_ready', sender_id=user_id, recipient_id=user_id,
        title=title, content=content, related_object_type='course', related_object_id=course_id))


def _summary(n_active, n_review, stats):
    text = f'启用 {n_active} 题，待审 {n_review} 题'
    if stats.get('failed_batches'):
        text += f'；{stats["failed_batches"]} 批生成失败'
    if stats.get('review_failed_chunks'):
        text += f'；{stats["review_failed_chunks"]} 组复核失败(已转待审)'
    return text


def run_generation_job(app, course_key, pages, user_id, plan=DEFAULT_PLAN, replace=False,
                       client=None, lock_token=None):
    """后台线程体:出题 → (replace 时停用旧 AI 题)→ 落库 → 站内通知。

    任何异常都记日志并写「题库生成失败」通知(尽力而为);lock_token 非空时最后释放生成标记。
    """
    with app.app_context():
        from app import db
        course_id, title = None, course_key
        try:
            from app.models.course import InteractiveCourse
            from app.models.course_exam import CourseQuizQuestion
            course = InteractiveCourse.query.filter_by(key=course_key).first()
            if course is not None:
                course_id, title = course.id, course.title
            keep = CourseQuizQuestion.query.filter(CourseQuizQuestion.course_key == course_key,
                                                   CourseQuizQuestion.status != 'disabled')
            if replace:     # 重建只替换 AI 题,人工/导入题保留,出题时也要避开它们
                keep = keep.filter(CourseQuizQuestion.origin != 'ai')
            existing = [r.question for r in keep.all()]
            db.session.rollback()       # 出题耗时数分钟,别挂着空闲事务

            beat = (lambda: _heartbeat(course_key, lock_token)) if lock_token is not None else None
            qs, stats = generate_course(pages, plan=plan, client=client, existing_questions=existing,
                                        on_progress=beat)
            abort = replace_abort_reason(stats) if replace else None
            if abort:
                logger.warning('题库重建中止 %s:%s', course_key, stats)
                _notify(user_id, '题库生成失败', f'{title}：{abort}', course_id)
                db.session.commit()
                return
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
            _notify(user_id, '题库生成完成', f'{title}：{_summary(n_active, len(qs) - n_active, stats)}',
                    course_id)
            db.session.commit()
            logger.info('题库生成完成 %s:启用 %d,待审 %d,%s', course_key, n_active, len(qs) - n_active, stats)
        except Exception as e:
            logger.exception('题库生成失败 %s', course_key)
            try:
                db.session.rollback()
                _notify(user_id, '题库生成失败', f'{title}：{str(e)[:200]}', course_id)
                db.session.commit()
            except Exception:
                db.session.rollback()
                logger.exception('题库生成失败通知写入失败 %s', course_key)
        finally:
            if lock_token is not None:
                _release(course_key, lock_token)


def start_generation(app, course_key, pages, user_id, plan=DEFAULT_PLAN, replace=False, client=None):
    """抢占跨进程生成标记后起后台线程出题;同一课已在生成中返回 False。

    须在 app context 内调用(会 commit 当前 session);app 须为真实对象
    (current_app._get_current_object())。plan 不合法时在抢标记前抛 ValueError。
    """
    plan = validate_plan(plan)
    token = _acquire(course_key, user_id)
    if token is None:
        return False
    try:
        threading.Thread(target=run_generation_job, name=f'course-exam-gen-{course_key}', daemon=True,
                         args=(app, course_key, pages, user_id, plan, replace, client, token)).start()
    except Exception:
        _release(course_key, token)
        raise
    return True
