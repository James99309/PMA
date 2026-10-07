# -*- coding: utf-8 -*-
"""课程考核 DB 编排。纯规则全部委托 logic.py;本模块只管读写与事务。

并发:所有会改进度行的入口都先 SELECT ... FOR UPDATE 锁住本人本课那一行,
避免同一用户多标签页/重复点击时重复计时、重复加分、断点被覆盖。
"""
import random

from sqlalchemy.exc import IntegrityError

from app import db
from app.models.course_exam import CourseQuizQuestion, CourseLearningProgress
from app.models.training import TrainingQuizAttempt, get_local_time
from app.services.course_exam import logic as L

MODULE_SLUG = 'bank'


def _progress_query(user_id, course_key):
    return CourseLearningProgress.query.filter_by(user_id=user_id, course_key=course_key)


def _create_progress(user_id, course_key, lock=False):
    """新建进度行;并发重复创建撞唯一索引时回滚保存点后重新查。"""
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
        return q.first()


def get_or_create_progress(user_id, course_key):
    """只读路径用:不加锁。"""
    p = _progress_query(user_id, course_key).first()
    return p or _create_progress(user_id, course_key)


def _locked_progress(user_id, course_key):
    """写路径用:行锁 + 强制刷新属性(identity map 里可能是锁前的旧值)。"""
    p = _progress_query(user_id, course_key).with_for_update().populate_existing().first()
    return p or _create_progress(user_id, course_key, lock=True)


def progress_dict(p, pages, override=None):
    ps = L._norm_page_seconds(p.page_seconds)
    required = L.required_read_seconds(pages, override)
    eff = L.effective_read_seconds(ps, pages)
    unlocked = bool(p.unlocked_at)
    percent = 100 if unlocked else (min(99, int(eff * 100 / required)) if required else 0)
    return {
        'read': {'percent': percent, 'unlocked': unlocked, 'page_seconds': ps,
                 'required_seconds': required, 'effective_seconds': eff,
                 'pages_seen': sum(1 for i in range(1, len(pages) + 1) if ps.get(str(i), 0) > 0),
                 'pages_total': len(pages)},
        'exam': {'score': p.score, 'passed': bool(p.passed_at), 'perfect': bool(p.perfect_at)},
    }


def record_read(user_id, course_key, pages, page, seconds, override=None):
    """阅读上报。page/seconds 原样透传给 logic.record_ping 校验,这里不做 int()。"""
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


def _force_last_ping(user_id, course_key, seconds_ago):
    """仅测试用:把上次上报时间往前拨。"""
    from datetime import timedelta
    p = _locked_progress(user_id, course_key)
    p.last_ping_at = get_local_time() - timedelta(seconds=seconds_ago)
    db.session.commit()


# ---------- 考核:断点题 / 提交 / 下一题 ----------

def _active_bank(course_key):
    return CourseQuizQuestion.query.filter_by(course_key=course_key, status='active').all()


def _user_history(user_id, course_key):
    """本人在本课题库的作答:已答对题 id 集合 + 按时间旧→新的作答 id 列表。"""
    rows = (TrainingQuizAttempt.query
            .filter_by(user_id=user_id, course_slug=course_key, module_slug=MODULE_SLUG)
            .order_by(TrainingQuizAttempt.attempted_at, TrainingQuizAttempt.id).all())
    correct = {int(r.question_id) for r in rows if r.is_correct}
    recent = [int(r.question_id) for r in rows]
    return correct, recent


def public_question(q, order):
    """给前端的题面:绝不含 answer / explain;选项按本人乱序后的顺序给出。"""
    d = {'id': q.id, 'qtype': q.qtype, 'difficulty': q.difficulty,
         'points': L.POINTS[q.difficulty], 'question': q.question}
    if q.qtype != 'judge':
        d['options'] = [q.options[i] for i in order]
    return d


def _clear_current(p):
    p.current_question_id = None
    p.current_option_order = None
    p.current_answered = False
    p.current_result = None


def _needs_draw(p, q):
    # 停用且未作答 → 换题;已作答的保留结果展示
    return q is None or (q.status != 'active' and not p.current_answered)


def _is_stale(p, q):
    """断点题在作答期间被删/停用/改了选项数 → 断点失效。"""
    if q is None or q.status != 'active':
        return True
    if q.qtype == 'judge':
        return p.current_option_order is not None
    order = p.current_option_order
    return not isinstance(order, list) or len(order) != len(q.options or [])


def _exam_base(p):
    return {'score': p.score, 'passed': bool(p.passed_at), 'perfect': bool(p.perfect_at)}


def current_question(user_id, course_key, rng=None):
    """取断点题;没有就抽一题并落盘(幂等:反复打开看到同一题同一选项顺序)。"""
    p = get_or_create_progress(user_id, course_key)
    if p.perfect_at:
        return dict(_exam_base(p), done=True)
    q = db.session.get(CourseQuizQuestion, p.current_question_id) if p.current_question_id else None
    if _needs_draw(p, q):
        p = _locked_progress(user_id, course_key)     # 加锁后重判,防并发重复抽题
        q = db.session.get(CourseQuizQuestion, p.current_question_id) if p.current_question_id else None
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
    return dict(_exam_base(p), question=public_question(q, p.current_option_order),
                answered=p.current_answered, result=p.current_result)


def submit_answer(user_id, course_key, shown_answer):
    """服务端判分。shown_answer 为「显示位」(single=int / multi=[int] / judge=bool)。"""
    p = _locked_progress(user_id, course_key)
    if not p.current_question_id:
        db.session.commit()
        return {'error': 'no_question'}
    if p.current_answered:
        db.session.commit()
        return {'error': 'already_answered'}
    q = db.session.get(CourseQuizQuestion, p.current_question_id)
    if _is_stale(p, q):
        # 题目在作答期间被改/停用:作废断点,下次 current_question 重新抽
        _clear_current(p)
        db.session.commit()
        return {'error': 'bad_answer', 'message': '题目已更新,请重新作答'}
    try:
        original = L.to_original(q.qtype, shown_answer, p.current_option_order,
                                 n_options=len(q.options or []) if q.qtype != 'judge' else None)
    except ValueError as e:
        # 断点本身完好,只是提交值非法:不清断点(否则可借乱填跳过难题)
        db.session.commit()
        return {'error': 'bad_answer', 'message': str(e)}
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
    order = p.current_option_order
    if q.qtype == 'judge':
        shown_correct = q.answer
    elif q.qtype == 'single':
        shown_correct = order.index(q.answer)
    else:
        shown_correct = sorted(order.index(i) for i in q.answer)
    result = {'correct': ok, 'gained': p.score - before, 'score': p.score,
              'correct_answer': shown_correct, 'your_answer': shown_answer,
              'explain': q.explain or '', 'source_page': q.source_page,
              'just_passed': flags['passed'], 'just_perfect': flags['perfect']}
    p.current_answered = True
    p.current_result = result
    db.session.add(TrainingQuizAttempt(
        user_id=user_id, course_slug=course_key, module_slug=MODULE_SLUG, chapter=1,
        question_id=str(q.id), question_text=q.question, question_type=q.qtype,
        user_answer=str(original), correct_answer=str(q.answer), is_correct=ok, attempted_at=now))
    db.session.commit()
    return result


def next_question(user_id, course_key):
    """已作答才推进;未作答直接返回当前题。"""
    p = _locked_progress(user_id, course_key)
    if p.current_answered:
        _clear_current(p)
    db.session.commit()
    return current_question(user_id, course_key)


# ---------- 旧题库导入 ----------

def import_legacy_json(course_key, course_assets_dir):
    """旧版 <key>.quiz.json → 题库(仅当本课题库为空时)。返回导入条数。

    每题过 normalize_question,不合法的跳过;难度统一按 2(中)。
    """
    import json
    import os
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
        db.session.add(CourseQuizQuestion(
            course_key=course_key, qtype=norm['qtype'], difficulty=norm['difficulty'],
            question=question, options=norm['options'] if norm['qtype'] != 'judge' else None,
            answer=norm['answer'], explain=raw.get('explain') or None,
            status='active', origin='legacy'))
        n += 1
    db.session.commit()
    return n
