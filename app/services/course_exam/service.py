# -*- coding: utf-8 -*-
"""课程考核 DB 编排。纯规则全部委托 logic.py;本模块只管读写与事务。

并发:所有会改进度行的入口都先 SELECT ... FOR UPDATE 锁住本人本课那一行,
避免同一用户多标签页/重复点击时重复计时、重复加分、断点被覆盖。
只读入口(get_progress / read_status)不加锁、不插行。
错误一律返回稳定错误码 {'error': code},文案由视图层翻译:
  no_question / already_answered / bad_answer(提交值非法,保留断点) / stale_question(题目已变,断点作废)
"""
import json
import logging
import os
import random

from sqlalchemy.exc import IntegrityError

from app import db
from app.models.course_exam import (
    CourseQuizQuestion, CourseLearningProgress, CourseExamSetting, LearningBuddyPref,
)
from app.models.training import TrainingQuizAttempt, get_local_time
from app.services.course_exam import logic as L

MODULE_SLUG = 'bank'


# ---------- 课程设置 / 小源开关 ----------

def get_min_read_seconds(course_key):
    """本课阅读时长覆盖值;无设置行返回 None(= 按讲解字数估算)。"""
    row = db.session.get(CourseExamSetting, course_key)
    return row.min_read_seconds if row else None


# 题库管理(生成/审题/编辑/阅读时长设置)只开放给这些角色
BANK_MANAGER_ROLES = ('admin', 'ceo', 'hr_manager')
MAX_MIN_READ_SECONDS = 36000


def can_manage_bank(user):
    return bool(user and getattr(user, 'is_authenticated', False)
                and getattr(user, 'role', None) in BANK_MANAGER_ROLES)


def set_min_read_seconds(course_key, value, user_id):
    """写本课阅读时长覆盖值;value 为 None = 恢复按讲解字数自动估算。会 commit。"""
    from app.services.course_exam.generator import _ensure_setting
    row = _ensure_setting(course_key)
    row.min_read_seconds = value
    row.updated_by = user_id
    db.session.commit()
    return row.min_read_seconds


def buddy_enabled(user_id):
    """小源是否显示;无偏好行默认开启。"""
    row = db.session.get(LearningBuddyPref, user_id)
    return True if row is None else bool(row.enabled)


def set_buddy_enabled(user_id, enabled):
    row = db.session.get(LearningBuddyPref, user_id)
    if row is None:
        try:
            with db.session.begin_nested():
                row = LearningBuddyPref(user_id=user_id, enabled=bool(enabled))
                db.session.add(row)
        except IntegrityError:
            row = (LearningBuddyPref.query.filter_by(user_id=user_id)
                   .populate_existing().first())
            if row is None:
                raise
    row.enabled = bool(enabled)
    db.session.commit()
    return row.enabled


# ---------- 进度行 ----------

def _progress_query(user_id, course_key):
    return CourseLearningProgress.query.filter_by(user_id=user_id, course_key=course_key)


def _create_progress(user_id, course_key, lock=False):
    """新建进度行;并发重复创建撞唯一索引时回滚保存点后重新查,查不到则原样抛出。"""
    try:
        with db.session.begin_nested():
            p = CourseLearningProgress(user_id=user_id, course_key=course_key,
                                       page_seconds={}, score=0)
            db.session.add(p)
        return p
    except IntegrityError:
        q = _progress_query(user_id, course_key)
        if lock:
            q = q.with_for_update().populate_existing()
        p = q.first()
        if p is None:
            raise           # 不是唯一冲突(如外键违例),抛原始错误
        return p


def get_progress(user_id, course_key):
    """只读:返回进度行或 None,绝不插行。"""
    return _progress_query(user_id, course_key).first()


def _locked_progress(user_id, course_key):
    """写路径用:行锁 + 强制刷新属性(identity map 里可能是锁前的旧值)。"""
    p = _progress_query(user_id, course_key).with_for_update().populate_existing().first()
    return p or _create_progress(user_id, course_key, lock=True)


def progress_dict(p, pages, override=None):
    """p 可为 None(尚无进度 = 空进度)。"""
    ps = L.norm_page_seconds(p.page_seconds if p else None)
    required = L.required_read_seconds(pages, override)
    eff = L.effective_read_seconds(ps, pages)
    unlocked = bool(p and p.unlocked_at)
    percent = 100 if unlocked else L.read_percent(ps, pages, override)
    return {
        'read': {'percent': percent, 'unlocked': unlocked, 'page_seconds': ps,
                 'required_seconds': required, 'effective_seconds': eff,
                 'pages_seen': sum(1 for i in range(1, len(pages) + 1) if ps.get(str(i), 0) > 0),
                 'pages_total': len(pages)},
        'exam': _exam_base(p),
    }


def read_status(user_id, course_key, pages):
    """只读的进度概览(课程页首屏用)。"""
    return progress_dict(get_progress(user_id, course_key), pages, get_min_read_seconds(course_key))


def record_read(user_id, course_key, pages, page, seconds):
    """阅读上报。page/seconds 原样透传给 logic.record_ping 校验,这里不做 int()。"""
    override = get_min_read_seconds(course_key)
    p = _locked_progress(user_id, course_key)
    if not p.unlocked_at:
        now = get_local_time()
        elapsed = (now - p.last_ping_at).total_seconds() if p.last_ping_at else None
        p.page_seconds = L.record_ping(p.page_seconds, pages, page, seconds, elapsed)
        p.last_ping_at = now
        if L.is_unlocked(p.page_seconds, pages, override):
            p.unlocked_at = now
    db.session.commit()     # 已解锁也提交,及时释放行锁
    return progress_dict(p, pages, override)


# ---------- 考核:断点题 / 提交 / 下一题 ----------

def bank_ready(course_key):
    """本课 active 题库是否健康(满分可达 100)。学员端考核门禁用。"""
    rows = (db.session.query(CourseQuizQuestion.qtype, CourseQuizQuestion.difficulty)
            .filter(CourseQuizQuestion.course_key == course_key, CourseQuizQuestion.status == 'active').all())
    return L.bank_health([{'qtype': t, 'difficulty': d} for t, d in rows])['ok']


def _active_bank(course_key):
    return CourseQuizQuestion.query.filter_by(course_key=course_key, status='active').all()


def _user_history(user_id, course_key):
    """本人在本课题库的作答:已答对题 id 集合 + 按时间旧→新的作答 id 列表。"""
    rows = (db.session.query(TrainingQuizAttempt.question_id, TrainingQuizAttempt.is_correct)
            .filter_by(user_id=user_id, course_slug=course_key, module_slug=MODULE_SLUG)
            .order_by(TrainingQuizAttempt.attempted_at, TrainingQuizAttempt.id).all())
    correct = {int(qid) for qid, ok in rows if ok}
    recent = [int(qid) for qid, _ in rows]
    return correct, recent


def public_question(q, order):
    """给前端的题面:绝不含 answer / explain;选项按本人乱序后的顺序给出。"""
    d = {'id': q.id, 'qtype': q.qtype, 'difficulty': q.difficulty,
         'points': L.POINTS[q.difficulty], 'question': q.question}
    if q.qtype != 'judge':
        d['options'] = [q.options[i] for i in order]
    return d


def _exam_base(p):
    if p is None:
        return {'score': 0, 'passed': False, 'perfect': False}
    return {'score': p.score, 'passed': bool(p.passed_at), 'perfect': bool(p.perfect_at)}


def _clear_current(p):
    p.current_question_id = None
    p.current_option_order = None
    p.current_answered = False
    p.current_result = None


def _is_stale(p, q):
    """断点题被删/停用/改了选项数 → 原乱序已无法套用。"""
    if q is None or q.status != 'active':
        return True
    if q.qtype == 'judge':
        return p.current_option_order is not None
    order = p.current_option_order
    return not isinstance(order, list) or len(order) != len(q.options or [])


def _needs_draw(p, q):
    # 已作答的保留结果快照展示(不再用旧顺序索引选项);未作答且断点失效 → 换题
    return not p.current_answered and _is_stale(p, q)


def _current_q(p):
    return db.session.get(CourseQuizQuestion, p.current_question_id) if p.current_question_id else None


def _render(p, q):
    base = _exam_base(p)
    if p.current_answered:
        res = p.current_result or {}
        return dict(base, question=res.get('question'), answered=True, result=res)
    return dict(base, question=public_question(q, p.current_option_order),
                answered=False, result=None)


def _ensure_current_locked(p, user_id, course_key, rng=None):
    """调用方已持有 p 的行锁:必要时抽题落盘,同一事务内提交并渲染。"""
    if p.perfect_at:
        db.session.commit()
        return dict(_exam_base(p), done=True)
    q = _current_q(p)
    if _needs_draw(p, q):
        rng = rng or random.SystemRandom()
        bank = [x.as_logic() for x in _active_bank(course_key)]
        correct, recent = _user_history(user_id, course_key)
        picked = L.pick_question(bank, p.score, correct, recent, rng)
        if not picked:
            _clear_current(p)
            db.session.commit()
            return dict(_exam_base(p), done=True, exhausted=True)
        q = db.session.get(CourseQuizQuestion, picked['id'])
        p.current_question_id = q.id
        p.current_option_order = L.option_order_for(q.as_logic(), rng)
        p.current_answered = False
        p.current_result = None
    db.session.commit()
    return _render(p, q)


def current_question(user_id, course_key, rng=None):
    """取断点题;没有/失效就抽一题并落盘(幂等:反复打开看到同一题同一选项顺序)。"""
    p = get_progress(user_id, course_key)
    if p is not None:
        if p.perfect_at:
            return dict(_exam_base(p), done=True)
        q = _current_q(p)
        if not _needs_draw(p, q):
            return _render(p, q)
    # 需要抽题:加锁后重判,防并发重复抽题
    return _ensure_current_locked(_locked_progress(user_id, course_key), user_id, course_key, rng)


def submit_answer(user_id, course_key, shown_answer):
    """服务端判分。shown_answer 为「显示位」(single=int / multi=[int] / judge=bool)。"""
    p = _locked_progress(user_id, course_key)
    if not p.current_question_id:
        db.session.commit()
        return {'error': 'no_question'}
    if p.current_answered:
        db.session.commit()
        return {'error': 'already_answered'}
    q = _current_q(p)
    if _is_stale(p, q):
        # 题目在作答期间被改/停用:作废断点,下次 current_question 重新抽
        _clear_current(p)
        db.session.commit()
        return {'error': 'stale_question'}
    order = p.current_option_order
    try:
        original = L.to_original(q.qtype, shown_answer, order,
                                 n_options=len(q.options or []) if q.qtype != 'judge' else None)
    except ValueError:
        # 断点本身完好,只是提交值非法:不清断点(否则可借乱填跳过难题)
        db.session.commit()
        return {'error': 'bad_answer'}
    # 规范化后的显示位(to_original 已校验过类型与范围)
    your_answer = sorted(set(shown_answer)) if q.qtype == 'multi' else shown_answer
    ok = L.is_correct(q.as_logic(), original)
    before = p.score
    if ok:
        p.score = L.apply_score(p.score, q.difficulty)
    flags = L.crossed(before, p.score)
    now = get_local_time()
    if p.score >= L.PASS_SCORE and not p.passed_at:
        p.passed_at = now
    if p.score >= L.FULL_SCORE and not p.perfect_at:
        p.perfect_at = now
    if q.qtype == 'judge':
        shown_correct = q.answer
    elif q.qtype == 'single':
        shown_correct = order.index(q.answer)
    else:
        shown_correct = sorted(order.index(i) for i in q.answer)
    result = {'correct': ok, 'gained': p.score - before, 'score': p.score,
              'correct_answer': shown_correct, 'your_answer': your_answer,
              'explain': q.explain or '', 'source_page': q.source_page,
              'just_passed': flags['passed'], 'just_perfect': flags['perfect'],
              # 题面快照:作答后题目即便被改,再打开仍按当时的选项顺序展示
              'question': public_question(q, order)}
    p.current_answered = True
    p.current_result = result
    db.session.add(TrainingQuizAttempt(
        user_id=user_id, course_slug=course_key, module_slug=MODULE_SLUG, chapter=1,
        question_id=str(q.id), question_text=q.question, question_type=q.qtype,
        user_answer=json.dumps(original, ensure_ascii=False),
        correct_answer=json.dumps(q.answer, ensure_ascii=False),
        is_correct=ok, attempted_at=now))
    db.session.commit()
    return result


def next_question(user_id, course_key, rng=None):
    """已作答才推进;清断点与抽新题在同一把锁、同一事务内完成。"""
    p = _locked_progress(user_id, course_key)
    if p.current_answered:
        _clear_current(p)
    return _ensure_current_locked(p, user_id, course_key, rng)


# ---------- 旧题库导入 ----------

def import_legacy_json(course_key, course_assets_dir):
    """旧版 <key>.quiz.json → 题库(仅当本课题库为空时)。返回导入条数。

    每题过 normalize_question,不合法的跳过;难度统一按 2(中)。
    """
    from sqlalchemy import text
    path = os.path.join(course_assets_dir, course_key + '.quiz.json')
    if not os.path.isfile(path):
        return 0
    if db.engine.dialect.name == 'postgresql':
        # 同课并发首访只让一个事务导入,防重复导入(事务结束自动释放)
        db.session.execute(text('SELECT pg_advisory_xact_lock(hashtext(:k))'),
                           {'k': 'course_exam_import:' + course_key})
    if CourseQuizQuestion.query.filter_by(course_key=course_key).first():
        db.session.commit()
        return 0
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, ValueError):
        db.session.commit()
        return 0
    n = 0
    for raw in (data.get('questions') or []) if isinstance(data, dict) else []:
        if not isinstance(raw, dict) or raw.get('type') not in ('single', 'judge'):
            continue
        question = str(raw.get('question') or '').strip()
        if not question:
            continue
        try:
            norm = L.normalize_question({'qtype': raw['type'], 'difficulty': 2,
                                         'options': raw.get('options'), 'answer': raw.get('answer')})
        except ValueError:
            continue
        explain = raw.get('explain')
        db.session.add(CourseQuizQuestion(
            course_key=course_key, qtype=norm['qtype'], difficulty=norm['difficulty'],
            question=question, options=norm['options'] if norm['qtype'] != 'judge' else None,
            answer=norm['answer'], explain=str(explain) if explain else None,
            status='active', origin='legacy'))
        n += 1
    db.session.commit()
    return n


# ---------- 种子题库导入(随代码发布的离线审定题库) ----------

_seed_log = logging.getLogger(__name__)

# app/course_exam_seeds/<course_key>.json —— 随代码发布(生产 app/ 只读挂载,只读取)
SEED_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           '..', '..', 'course_exam_seeds'))
_SEED_STATUSES = ('active', 'review', 'disabled')
# 本进程已确认「无需再导入」的课(已有题 / 无种子文件 / 已导入),命中即不再查库
_SEED_CHECKED = set()


def reset_seed_memo():
    """清空本进程的种子检查记忆(测试用)。"""
    _SEED_CHECKED.clear()


def _seed_path(course_key):
    # course_key 来自课程表,仍防路径穿越
    if not course_key or '/' in course_key or '\\' in course_key or course_key.startswith('.'):
        return None
    path = os.path.join(SEED_DIR, course_key + '.json')
    return path if os.path.isfile(path) else None


def _seed_rows(course_key, data):
    """种子文件 → CourseQuizQuestion 列表;每题再过一遍 normalize_question,不合法跳过并记日志。"""
    out = []
    qs = data.get('questions') if isinstance(data, dict) else None
    for i, raw in enumerate(qs or []):
        if not isinstance(raw, dict):
            _seed_log.warning('种子题库 %s 第 %d 题不是对象,跳过', course_key, i + 1)
            continue
        question = str(raw.get('question') or '').strip()
        try:
            if not question:
                raise ValueError('题干为空')
            norm = L.normalize_question({'qtype': raw.get('qtype'), 'difficulty': raw.get('difficulty'),
                                         'options': raw.get('options'), 'answer': raw.get('answer')})
        except ValueError as e:
            _seed_log.warning('种子题库 %s 第 %d 题不合法,跳过: %s', course_key, i + 1, e)
            continue
        status = raw.get('status') if raw.get('status') in _SEED_STATUSES else 'review'
        ai_d = L._as_int(raw.get('ai_difficulty'))
        page = L._as_int(raw.get('source_page'))
        explain, note = raw.get('explain'), raw.get('review_note')
        out.append(CourseQuizQuestion(
            course_key=course_key, qtype=norm['qtype'], difficulty=norm['difficulty'],
            ai_difficulty=ai_d if ai_d in L.POINTS else None, question=question,
            options=norm['options'] if norm['qtype'] != 'judge' else None, answer=norm['answer'],
            explain=str(explain) if explain else None, source_page=page,
            status=status, origin='ai', review_note=str(note) if note else None, created_by=None))
    return out


def ensure_seeded(course_key):
    """本课题库完全为空(任何状态都没有)且有种子文件 → 整体导入。返回导入条数。

    优先于旧版 .quiz.json:调用方先调本函数,仍为空才走 import_legacy_json。
    与 import_legacy_json 共用同一把 advisory 锁,锁内重判是否为空,并发首访只导一次。
    """
    if course_key in _SEED_CHECKED:
        return 0
    path = _seed_path(course_key)
    if path is None:
        _SEED_CHECKED.add(course_key)
        return 0
    from sqlalchemy import text
    if db.engine.dialect.name == 'postgresql':
        db.session.execute(text('SELECT pg_advisory_xact_lock(hashtext(:k))'),
                           {'k': 'course_exam_import:' + course_key})
    if CourseQuizQuestion.query.filter_by(course_key=course_key).first():
        db.session.commit()
        _SEED_CHECKED.add(course_key)
        return 0
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
    except (OSError, ValueError):
        db.session.commit()
        _seed_log.exception('种子题库 %s 读取失败', course_key)
        _SEED_CHECKED.add(course_key)
        return 0
    if isinstance(data, dict) and data.get('course_key') not in (None, course_key):
        db.session.commit()
        _seed_log.warning('种子题库 %s 的 course_key 不匹配(%s),不导入', course_key, data.get('course_key'))
        _SEED_CHECKED.add(course_key)
        return 0
    rows = _seed_rows(course_key, data)
    db.session.add_all(rows)
    db.session.commit()
    _SEED_CHECKED.add(course_key)
    _seed_log.info('种子题库 %s 导入 %d 题', course_key, len(rows))
    return len(rows)


def ensure_seeded_many(course_keys):
    """批量版(小源面板用):一次查询找出哪些课已有题,只对确实为空且有种子的课逐个导入。"""
    todo = [k for k in dict.fromkeys(course_keys) if k not in _SEED_CHECKED]
    with_seed = []
    for k in todo:
        if _seed_path(k) is None:
            _SEED_CHECKED.add(k)
        else:
            with_seed.append(k)
    if not with_seed:
        return 0
    have = {ck for (ck,) in db.session.query(CourseQuizQuestion.course_key)
            .filter(CourseQuizQuestion.course_key.in_(with_seed)).distinct().all()}
    _SEED_CHECKED.update(have)
    return sum(ensure_seeded(k) for k in with_seed if k not in have)
