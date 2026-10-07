# -*- coding: utf-8 -*-
"""课程考核 DB 编排。纯规则全部委托 logic.py;本模块只管读写与事务。

并发:所有会改进度行的入口都先 SELECT ... FOR UPDATE 锁住本人本课那一行,
避免同一用户多标签页/重复点击时重复计时、重复加分、断点被覆盖。
"""
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
