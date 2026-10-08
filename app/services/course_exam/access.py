# -*- coding: utf-8 -*-
"""培训管理:课程开放模式 / 指定学员 / 题库审核人 / 成绩汇总。

可见性规则(restricted 课未授权 = 视同不存在,路由一律 404):
  管理员(admin / ceo / hr_manager,= service.BANK_MANAGER_ROLES)与该课审核人始终可见;
  mode == 'open'(无 course_access 行即 open)全员可见;restricted 课仅已拉入的学员可见。
公开二维码路由 /wiki/pub/ 不走本模块。

成绩可见范围:管理员看全部;其他人仅看自己的直属下属(Affiliation: viewer_id=上级 → owner_id=下属,一级);
学员看自己(我的培训)。

上半部分是纯函数(可无 DB 单测),下半部分是批量查询(禁止 N+1)。
写操作自行 commit;通知只建站内 Message(不推送),与主数据同一事务提交。
"""
import logging
from collections import defaultdict

from sqlalchemy import case, func

from app import db
from app.models.course_exam import (
    CourseAccess, CourseEnrollment, CourseReviewer,
    CourseLearningProgress, CourseQuizQuestion, CourseExamSetting,
)
from app.models.training import TrainingQuizAttempt, get_local_time
from app.services.course_exam import logic as L
from app.services.course_exam import service as S

logger = logging.getLogger(__name__)

MODES = ('open', 'restricted')
DEFAULT_MODE = 'open'
REPEATED_WRONG_MIN = 2
REPEATED_WRONG_TOP = 5


# ══════════ 纯函数 ══════════

def normalize_mode(mode):
    if not isinstance(mode, str) or mode not in MODES:
        raise ValueError('bad mode')
    return mode


def normalize_user_ids(raw):
    """[int|数字串] → 去重保序的正整数列表;任何非法元素整体报 ValueError。"""
    if not isinstance(raw, list):
        raise ValueError('user_ids must be a list')
    out = []
    for v in raw:
        if isinstance(v, bool):
            raise ValueError('bad user id')
        if isinstance(v, str) and v.strip().isdigit():
            v = int(v.strip())
        if not isinstance(v, int) or v <= 0:
            raise ValueError('bad user id')
        if v not in out:
            out.append(v)
    return out


def decide_visible(keys, modes, enrolled, reviewing, manager):
    """按顺序去重返回可见的课程 key。modes 缺 key = open;非 open 一律按受限处理。"""
    out = []
    for k in dict.fromkeys(keys):
        if manager or modes.get(k, DEFAULT_MODE) == 'open' or k in enrolled or k in reviewing:
            out.append(k)
    return out


def report_population(enrolled_ids, progress_ids, manager, subordinates):
    """成绩表的人员范围 = (已拉入 ∪ 有进度);非管理员再 ∩ 直属下属。"""
    pop = set(enrolled_ids) | set(progress_ids)
    return pop if manager else pop & set(subordinates)


def question_stats(rows, current):
    """按题作答统计。rows: [(question_id_str, question_text, is_correct)];
    current: {question_id_str: 当前题干}。只认作答时题干与当前题干一致的留痕(同题库实测难度的口径)。"""
    agg = {}
    for qid, text, ok in rows:
        qid = str(qid)
        if current.get(qid) is None or current[qid] != text:
            continue
        a = agg.setdefault(qid, {'question_id': int(qid), 'question': current[qid],
                                 'attempts': 0, 'correct': 0, 'wrong': 0})
        a['attempts'] += 1
        if ok:
            a['correct'] += 1
        else:
            a['wrong'] += 1
    return sorted(agg.values(), key=lambda a: a['question_id'])


def repeated_wrong(rows, current, min_wrong=REPEATED_WRONG_MIN, top=REPEATED_WRONG_TOP):
    """反复错题:同一题(当前题干)错 >= min_wrong 次,按错次降序取前 top。"""
    hits = [a for a in question_stats(rows, current) if a['wrong'] >= min_wrong]
    hits.sort(key=lambda a: (-a['wrong'], a['question_id']))
    return hits[:top]


def _iso(dt):
    return dt.isoformat() if dt else None


def _max_dt(*dts):
    vals = [d for d in dts if d is not None]
    return max(vals) if vals else None


# ══════════ 角色 / 可见性 ══════════

def is_manager(user):
    return S.can_manage_bank(user)


def _authed_id(user):
    if user is None or not getattr(user, 'is_authenticated', False):
        return None
    return getattr(user, 'id', None)


def course_mode(key):
    row = db.session.get(CourseAccess, key)
    return row.mode if row else DEFAULT_MODE


def set_course_mode(key, mode, user_id):
    mode = normalize_mode(mode)
    row = db.session.get(CourseAccess, key)
    if row is None:
        row = CourseAccess(course_key=key, mode=mode, updated_by=user_id)
        db.session.add(row)
    else:
        row.mode = mode
        row.updated_by = user_id
    db.session.commit()
    return row.mode


def is_reviewer(user, key):
    uid = _authed_id(user)
    if not uid:
        return False
    return db.session.query(CourseReviewer.id).filter_by(course_key=key, user_id=uid).first() is not None


def is_enrolled(user_id, key):
    return db.session.query(CourseEnrollment.id).filter_by(
        course_key=key, user_id=user_id).first() is not None


def can_review_bank(user, key):
    """题库审核(查看/编辑/停用/改难度/通过待审/单题重出):管理员或该课审核人。"""
    if _authed_id(user) is None:
        return False
    return is_manager(user) or is_reviewer(user, key)


def can_view_course(user, key):
    uid = _authed_id(user)
    if uid is None:
        return False
    if is_manager(user) or course_mode(key) == 'open':
        return True
    return is_enrolled(uid, key) or is_reviewer(user, key)


def reviewing_keys(user, keys=None):
    """当前用户担任审核人的课程 key 集合(一次查询)。"""
    uid = _authed_id(user)
    if uid is None:
        return set()
    q = db.session.query(CourseReviewer.course_key).filter(CourseReviewer.user_id == uid)
    if keys is not None:
        keys = list(keys)
        if not keys:
            return set()
        q = q.filter(CourseReviewer.course_key.in_(keys))
    return {k for (k,) in q.all()}


def visible_course_keys(user, keys):
    """批量可见性过滤(列表页用):最多 3 次查询,与课程数无关。保持入参顺序。"""
    keys = list(dict.fromkeys(keys))
    uid = _authed_id(user)
    if uid is None or not keys:
        return []
    if is_manager(user):
        return keys
    modes = {k: m for k, m in db.session.query(CourseAccess.course_key, CourseAccess.mode)
             .filter(CourseAccess.course_key.in_(keys)).all()}
    restricted = [k for k in keys if modes.get(k, DEFAULT_MODE) != 'open']
    enrolled, reviewing = set(), set()
    if restricted:
        enrolled = {k for (k,) in db.session.query(CourseEnrollment.course_key).filter(
            CourseEnrollment.user_id == uid, CourseEnrollment.course_key.in_(restricted)).all()}
        reviewing = reviewing_keys(user, restricted)
    return decide_visible(keys, modes, enrolled, reviewing, manager=False)


# ══════════ 课程元数据 / 链接 ══════════

def _course_row(key):
    from app.models.course import InteractiveCourse
    return InteractiveCourse.query.filter_by(key=key).first()


def _url(endpoint, fallback, **values):
    """请求上下文外(脚本)url_for 会失败,回落到固定路径。"""
    from flask import url_for
    try:
        return url_for(endpoint, **values)
    except Exception:
        return fallback


def course_url(key, media_type):
    """学员打开课程的入口链接:html=播放页 / video=视频页 / ppt=下载。"""
    if media_type == 'video':
        return _url('knowledge_wiki.play_video', f'/wiki/video/{key}', course_key=key)
    if media_type == 'ppt':
        return _url('knowledge_wiki.course_download', f'/wiki/play/{key}/download', course_key=key)
    return _url('knowledge_wiki.play_course', f'/wiki/play/{key}', course_key=key)


def bank_url(key):
    return _url('learning.bank_page', f'/wiki/play/{key}/bank', key=key)


def _user_brief(u):
    return {'id': u.id, 'name': u.real_name or u.username, 'department': u.department or '',
            'company_name': u.company_name or '', 'active': bool(u._is_active)}


def _active_users(ids):
    from app.models.user import User
    if not ids:
        return []
    return User.query.filter(User.id.in_(list(ids)), User._is_active == True).all()  # noqa: E712


def _add_message(sender_id, recipient_id, mtype, title, content, course_row, url):
    from app.models.message import Message
    if not sender_id or not recipient_id or sender_id == recipient_id:
        return
    db.session.add(Message(
        sender_id=sender_id, recipient_id=recipient_id, message_type=mtype,
        title=title[:200], content=content,
        related_object_type='course', related_object_id=course_row.id if course_row else None,
        extra_data={'course_key': course_row.key if course_row else None, 'url': url}))


# ══════════ 指定学员 ══════════

def enroll_users(key, user_ids, by, source='user', source_detail=None):
    """拉入学员(只拉当前在职的人;已存在跳过)。返回新增人数。为新增的人建站内通知。会 commit。"""
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    ids = [u.id for u in _active_users(normalize_user_ids(list(user_ids)))]
    if not ids:
        return 0
    now = get_local_time()
    stmt = (pg_insert(CourseEnrollment.__table__)
            .values([{'course_key': key, 'user_id': uid, 'source': source,
                      'source_detail': (source_detail or None) and source_detail[:100],
                      'added_by': by, 'added_at': now} for uid in ids])
            .on_conflict_do_nothing(index_elements=['course_key', 'user_id'])
            .returning(CourseEnrollment.__table__.c.user_id))
    new_ids = [r[0] for r in db.session.execute(stmt).fetchall()]
    if new_ids:
        row = _course_row(key)
        title = row.title if row else key
        url = course_url(key, (row.media_type if row else None) or 'html')
        for uid in new_ids:
            _add_message(by, uid, 'course_enrolled', f'你已加入培训《{title}》',
                         f'你已被加入培训课程《{title}》，请及时学习：{url}', row, url)
    db.session.commit()
    return len(new_ids)


def department_user_ids(dept, company_name=None):
    from app.models.user import User
    q = db.session.query(User.id).filter(User._is_active == True, User.department == dept)  # noqa: E712
    if company_name:
        q = q.filter(User.company_name == company_name)
    return [i for (i,) in q.order_by(User.id).all()]


def enroll_department(key, dept, by, company_name=None):
    """按部门一次性快照拉入(当前在职);之后新入职不自动加入。返回新增人数。"""
    dept = (dept or '').strip()
    if not dept:
        raise ValueError('department required')
    ids = department_user_ids(dept, company_name)
    if not ids:
        return 0
    return enroll_users(key, ids, by, source='department', source_detail=dept)


def unenroll(key, user_id):
    n = CourseEnrollment.query.filter_by(course_key=key, user_id=user_id).delete(synchronize_session=False)
    db.session.commit()
    return n > 0


def list_enrollments(key):
    from app.models.user import User
    rows = (db.session.query(CourseEnrollment, User)
            .join(User, User.id == CourseEnrollment.user_id)
            .filter(CourseEnrollment.course_key == key)
            .order_by(CourseEnrollment.added_at.desc(), CourseEnrollment.id.desc()).all())
    adders = {u.id: u for u in _users_by_ids({e.added_by for e, _ in rows if e.added_by})}
    out = []
    for e, u in rows:
        d = _user_brief(u)
        d.update({'source': e.source, 'source_detail': e.source_detail or '',
                  'added_at': _iso(e.added_at),
                  'added_by': (adders[e.added_by].real_name or adders[e.added_by].username)
                  if e.added_by in adders else ''})
        out.append(d)
    return out


def _users_by_ids(ids):
    from app.models.user import User
    ids = [i for i in ids if i]
    return User.query.filter(User.id.in_(ids)).all() if ids else []


def departments(company_name=None):
    """在职人员的去重部门列表 + 人数(按公司 + 部门)。"""
    from app.models.user import User
    q = (db.session.query(User.company_name, User.department, func.count(User.id))
         .filter(User._is_active == True, User.department.isnot(None), User.department != ''))  # noqa: E712
    if company_name:
        q = q.filter(User.company_name == company_name)
    rows = q.group_by(User.company_name, User.department).order_by(User.company_name, User.department).all()
    return [{'company_name': c or '', 'department': d, 'count': int(n)} for c, d, n in rows]


def active_users(company_name=None):
    from app.models.user import User
    q = User.query.filter(User._is_active == True)  # noqa: E712
    if company_name:
        q = q.filter(User.company_name == company_name)
    return [_user_brief(u) for u in q.order_by(User.department, User.real_name, User.id).all()]


# ══════════ 审核人 ══════════

def list_reviewers(key):
    from app.models.user import User
    rows = (db.session.query(User).join(CourseReviewer, CourseReviewer.user_id == User.id)
            .filter(CourseReviewer.course_key == key).order_by(CourseReviewer.added_at, User.id).all())
    return [_user_brief(u) for u in rows]


def _reviewer_rows(key):
    """{user_id: CourseReviewer} —— 本课当前审核人(单独成函数,便于测试模拟并发旧快照)。"""
    return {r.user_id: r for r in CourseReviewer.query.filter_by(course_key=key).all()}


def set_reviewers(key, user_ids, by):
    """全量覆盖审核人(只接受在职的人;非法 id 忽略)。新增的人发站内通知。会 commit。"""
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    want = [u.id for u in _active_users(normalize_user_ids(list(user_ids)))]
    have = _reviewer_rows(key)
    removed = [uid for uid in have if uid not in want]
    if removed:
        CourseReviewer.query.filter(CourseReviewer.course_key == key,
                                    CourseReviewer.user_id.in_(removed)).delete(synchronize_session=False)
    todo = [uid for uid in want if uid not in have]
    added = []
    if todo:
        # 并发安全:别的请求已插入同一 (课程, 人) 时跳过,只给真正新增的人发通知
        now = get_local_time()
        stmt = (pg_insert(CourseReviewer.__table__)
                .values([{'course_key': key, 'user_id': uid, 'added_by': by, 'added_at': now} for uid in todo])
                .on_conflict_do_nothing(index_elements=['course_key', 'user_id'])
                .returning(CourseReviewer.__table__.c.user_id))
        added = [r[0] for r in db.session.execute(stmt).fetchall()]
    if added:
        row = _course_row(key)
        title = row.title if row else key
        url = bank_url(key)
        for uid in added:
            _add_message(by, uid, 'course_reviewer', f'你被指定为《{title}》题库审核人',
                         f'你被指定为培训课程《{title}》的题库审核人，请前往题库页审核：{url}', row, url)
    db.session.commit()
    return {'added': added, 'removed': removed}


# ══════════ 成绩汇总 ══════════

def subordinate_ids(viewer_id):
    """直属下属(一级):Affiliation viewer_id=上级 → owner_id=下属。"""
    from app.models.user import Affiliation
    if not viewer_id:
        return set()
    return {o for (o,) in db.session.query(Affiliation.owner_id).filter(
        Affiliation.viewer_id == viewer_id, Affiliation.owner_id != viewer_id).all()}


def has_subordinates(user_id):
    """是否有直属下属(一次 EXISTS 查询)。培训管理入口 / 成绩页门禁用。"""
    from app.models.user import Affiliation
    if not user_id:
        return False
    return db.session.query(db.session.query(Affiliation.id).filter(
        Affiliation.viewer_id == user_id, Affiliation.owner_id != user_id).exists()).scalar()


def can_view_training(user):
    """培训管理入口可见性(侧栏 / 知识库按钮共用):管理员不查库;其他人同一请求只查一次
    「是否有直属下属」(缓存在 flask.g,按用户 id 记,防跨请求串号)。查询失败按无入口处理。"""
    from flask import g
    uid = _authed_id(user)
    if uid is None:
        return False
    if is_manager(user):
        return True
    cached = getattr(g, '_cb_training', None)
    if cached is None or cached[0] != uid:
        try:
            with db.session.begin_nested():
                val = has_subordinates(uid)
        except Exception:
            logger.warning('培训管理入口判断失败', exc_info=True)
            val = False
        cached = (uid, bool(val))
        g._cb_training = cached
    return cached[1]


def training_page_mode(user):
    """培训管理页访问级别:'full'(管理员)/ 'scores'(有直属下属,只看成绩)/ None(无权)。"""
    uid = _authed_id(user)
    if uid is None:
        return None
    if is_manager(user):
        return 'full'
    return 'scores' if has_subordinates(uid) else None


def can_view_user_report(viewer, user_id):
    uid = _authed_id(viewer)
    if uid is None:
        return False
    return is_manager(viewer) or uid == user_id or user_id in subordinate_ids(uid)


def _pages_for(key):
    """HTML 课逐页讲解(走 _get_course_pages 的 mtime 缓存);课件缺失返回 []。"""
    import os
    import app.views.knowledge_wiki as KW      # 按模块属性取,测试可改指课件目录
    path = KW._course_html_path(key)
    if not os.path.isfile(path):
        return []
    return KW._get_course_pages(key, path)


def _overrides(keys):
    if not keys:
        return {}
    return {k: s for k, s in db.session.query(CourseExamSetting.course_key, CourseExamSetting.min_read_seconds)
            .filter(CourseExamSetting.course_key.in_(list(keys))).all()}


def _html_cell(p, pages, override):
    if p is None:
        return {'read_percent': 0, 'unlocked': False, 'score': 0, 'passed': False, 'perfect': False,
                'passed_at': None, 'perfect_at': None, 'last_activity': None}
    if p.unlocked_at:
        percent = 100
    else:
        percent = L.read_percent(L.norm_page_seconds(p.page_seconds), pages, override) if pages else 0
    return {'read_percent': percent, 'unlocked': bool(p.unlocked_at), 'score': p.score or 0,
            'passed': bool(p.passed_at), 'perfect': bool(p.perfect_at),
            'passed_at': _iso(p.passed_at), 'perfect_at': _iso(p.perfect_at),
            'last_activity': _max_dt(p.updated_at, p.last_ping_at)}


def _video_cell(v):
    if v is None:
        return {'read_percent': 0, 'unlocked': False, 'score': 0, 'passed': False, 'perfect': False,
                'passed_at': None, 'perfect_at': None, 'last_activity': None}
    return {'read_percent': int(round(min(1.0, v.max_progress or 0.0) * 100)), 'unlocked': bool(v.completed),
            'score': 0, 'passed': bool(v.completed), 'perfect': False,
            'passed_at': _iso(v.completed_at), 'perfect_at': None, 'last_activity': v.updated_at}


def _progress_map(keys_by_media, user_ids=None):
    """{(course_key, user_id): progress/watch 行};html 查 CourseLearningProgress,video 查 VideoWatchState。"""
    from app.models.video_watch import VideoWatchState
    out = {}
    html = keys_by_media.get('html') or []
    video = keys_by_media.get('video') or []
    if user_ids is not None and not user_ids:
        return out
    if html:
        q = CourseLearningProgress.query.filter(CourseLearningProgress.course_key.in_(html))
        if user_ids is not None:
            q = q.filter(CourseLearningProgress.user_id.in_(list(user_ids)))
        for p in q.all():
            out[(p.course_key, p.user_id)] = p
    if video:
        q = VideoWatchState.query.filter(VideoWatchState.course_key.in_(video))
        if user_ids is not None:
            q = q.filter(VideoWatchState.user_id.in_(list(user_ids)))
        for v in q.all():
            out[(v.course_key, v.user_id)] = v
    return out


def _cell(media, prog, pages, override):
    if media == 'video':
        return _video_cell(prog)
    if media == 'html':
        return _html_cell(prog, pages, override)
    return _html_cell(None, [], None)       # ppt:无进度


def course_report(key, viewer):
    """单课成绩表。返回 None = 课程不存在;'forbidden' = 无权(非管理员且无直属下属)。"""
    from app.models.user import User
    # 先判权限再查课程:无权者无法用 key 探测课程是否存在
    manager = is_manager(viewer)
    subs = set() if manager else subordinate_ids(_authed_id(viewer))
    if not manager and not subs:
        return 'forbidden'
    row = _course_row(key) if key else None
    if row is None:
        return None
    media = row.media_type or 'html'
    eq = CourseEnrollment.query.filter_by(course_key=key)
    if not manager:
        eq = eq.filter(CourseEnrollment.user_id.in_(list(subs)))
    enrolled = {e.user_id: e for e in eq.all()}
    prog = {uid: p for (_k, uid), p in _progress_map({media: [key]}, None if manager else subs).items()}
    pop = report_population(enrolled, prog, manager, subs)
    users = {u.id: u for u in (User.query.filter(User.id.in_(list(pop))).all() if pop else [])}
    att = {}
    if pop:
        for uid, n, c, last in (db.session.query(
                TrainingQuizAttempt.user_id, func.count(TrainingQuizAttempt.id),
                func.sum(case((TrainingQuizAttempt.is_correct == True, 1), else_=0)),  # noqa: E712
                func.max(TrainingQuizAttempt.attempted_at))
                .filter(TrainingQuizAttempt.course_slug == key, TrainingQuizAttempt.module_slug == S.MODULE_SLUG,
                        TrainingQuizAttempt.user_id.in_(list(pop)))
                .group_by(TrainingQuizAttempt.user_id).all()):
            att[uid] = (int(n), int(c or 0), last)
    reviewers = {u for (u,) in db.session.query(CourseReviewer.user_id).filter(
        CourseReviewer.course_key == key, CourseReviewer.user_id.in_(list(pop))).all()} if pop else set()
    pages = _pages_for(key) if media == 'html' else []
    override = S.get_min_read_seconds(key) if media == 'html' else None
    rows = []
    for uid in pop:
        u = users.get(uid)
        if u is None:
            continue
        cell = _cell(media, prog.get(uid), pages, override)
        n, c, last = att.get(uid, (0, 0, None))
        e = enrolled.get(uid)
        cell['last_activity'] = _iso(_max_dt(cell['last_activity'], last))
        cell.update({'user': _user_brief(u), 'enrolled': e is not None, 'is_reviewer': uid in reviewers,
                     'enrolled_at': _iso(e.added_at) if e else None,
                     'attempts': n, 'correct': c})
        rows.append(cell)
    rows.sort(key=lambda r: (not r['enrolled'], -r['score'], -r['read_percent'], r['user']['name']))
    return {'course': {'key': row.key, 'title': row.title, 'media_type': media, 'mode': course_mode(key)},
            'scope': 'all' if manager else 'subordinates', 'rows': rows}


def overview(viewer):
    """全课程 × 人 成绩矩阵(范围规则同 course_report)。返回 'forbidden' = 无权。"""
    from app.models.course import InteractiveCourse
    from app.models.user import User
    manager = is_manager(viewer)
    subs = set() if manager else subordinate_ids(_authed_id(viewer))
    if not manager and not subs:
        return 'forbidden'
    courses = InteractiveCourse.query.order_by(InteractiveCourse.created_at.desc()).all()
    media_of = {c.key: (c.media_type or 'html') for c in courses}
    keys_by_media = defaultdict(list)
    for k, m in media_of.items():
        keys_by_media[m].append(k)
    keys = list(media_of)
    modes = {k: m for k, m in db.session.query(CourseAccess.course_key, CourseAccess.mode)
             .filter(CourseAccess.course_key.in_(keys)).all()} if keys else {}
    eq = CourseEnrollment.query.filter(CourseEnrollment.course_key.in_(keys)) if keys else None
    if eq is not None and not manager:
        eq = eq.filter(CourseEnrollment.user_id.in_(list(subs)))
    enrolled = {(e.course_key, e.user_id) for e in (eq.all() if eq is not None else [])}
    prog = _progress_map(keys_by_media, None if manager else subs)
    pairs = enrolled | set(prog)
    rq = db.session.query(CourseReviewer.course_key, CourseReviewer.user_id).filter(
        CourseReviewer.course_key.in_(keys)) if keys else None
    if rq is not None and not manager:
        rq = rq.filter(CourseReviewer.user_id.in_(list(subs)))
    reviewer_pairs = set(rq.all()) if rq is not None else set()
    pages = {k: _pages_for(k) for k in {k for k, _ in pairs if media_of.get(k) == 'html'}}
    overrides = _overrides(pages.keys())
    cells = defaultdict(dict)
    summary = {k: {'enrolled': 0, 'started': 0, 'passed': 0, 'perfect': 0} for k in keys}
    for k, uid in pairs:
        if k not in media_of:
            continue
        c = _cell(media_of[k], prog.get((k, uid)), pages.get(k, []), overrides.get(k))
        c['last_activity'] = _iso(c['last_activity'])
        c['enrolled'] = (k, uid) in enrolled
        c['is_reviewer'] = (k, uid) in reviewer_pairs
        cells[uid][k] = c
        s = summary[k]
        s['enrolled'] += c['enrolled']
        s['started'] += (k, uid) in prog
        s['passed'] += c['passed']
        s['perfect'] += c['perfect']
    uids = list(cells)
    users = User.query.filter(User.id.in_(uids)).all() if uids else []
    shown = keys if manager else [k for k in keys if any(k in cells[u] for u in cells)]
    return {
        'scope': 'all' if manager else 'subordinates',
        'courses': [{'key': c.key, 'title': c.title, 'media_type': media_of[c.key],
                     'mode': modes.get(c.key, DEFAULT_MODE), 'summary': summary[c.key]}
                    for c in courses if c.key in set(shown)],
        'users': sorted((_user_brief(u) for u in users), key=lambda d: (d['department'], d['name'])),
        'cells': {str(uid): v for uid, v in cells.items()},
    }


def user_detail(key, user_id, viewer):
    """某人某课明细。None = 课程/人不存在;'forbidden' = 无权(非管理员、非本人、非直属上级)。"""
    from app.models.user import User
    if not can_view_user_report(viewer, user_id):
        return 'forbidden'                           # 先判权限再查课程,无权者无法探测 key
    row = _course_row(key) if key else None
    u = db.session.get(User, user_id)
    if row is None or u is None:
        return None
    vid = _authed_id(viewer)
    if vid == user_id and not is_manager(viewer) and not can_view_course(viewer, row.key):
        return None      # 本人看自己:受限课未授权视同不存在(上级看下属不受此限)
    media = row.media_type or 'html'
    out = {'course': {'key': row.key, 'title': row.title, 'media_type': media},
           'user': _user_brief(u),
           'enrolled': is_enrolled(user_id, key)}
    if media == 'video':
        from app.models.video_watch import VideoWatchState
        v = VideoWatchState.query.filter_by(user_id=user_id, course_key=key).first()
        out['watch'] = v.to_dict() if v else {'last_position': 0, 'max_progress': 0, 'completed': False,
                                               'completed_at': None}
        return out
    if media != 'html':
        return out
    pages = _pages_for(key)
    p = S.get_progress(user_id, key)
    pd = S.progress_dict(p, pages, S.get_min_read_seconds(key))
    ps = pd['read']['page_seconds']
    out['read'] = {k: pd['read'][k] for k in ('percent', 'unlocked', 'required_seconds',
                                              'effective_seconds', 'pages_seen', 'pages_total')}
    out['read']['total_seconds'] = sum(ps.values())
    out['read']['pages'] = [{'page': i + 1, 'label': pg.get('label') or '', 'seconds': ps.get(str(i + 1), 0)}
                            for i, pg in enumerate(pages)]
    out['exam'] = {'score': p.score if p else 0,
                   'passed_at': _iso(p.passed_at) if p else None,
                   'perfect_at': _iso(p.perfect_at) if p else None}
    rows = (db.session.query(TrainingQuizAttempt.question_id, TrainingQuizAttempt.question_text,
                             TrainingQuizAttempt.is_correct)
            .filter_by(user_id=user_id, course_slug=key, module_slug=S.MODULE_SLUG)
            .order_by(TrainingQuizAttempt.attempted_at, TrainingQuizAttempt.id).all())
    current = {str(i): q for i, q in db.session.query(CourseQuizQuestion.id, CourseQuizQuestion.question)
               .filter(CourseQuizQuestion.course_key == key).all()}
    out['exam']['attempts'] = len(rows)
    out['exam']['correct'] = sum(1 for r in rows if r[2])
    out['questions'] = question_stats(rows, current)
    out['repeated_wrong'] = repeated_wrong(rows, current)
    return out


def my_training(user):
    """我的培训:可见课程中「我被拉入的 + open 课里我有进度的」。"""
    from app.models.course import InteractiveCourse
    uid = _authed_id(user)
    if uid is None:
        return []
    courses = InteractiveCourse.query.order_by(InteractiveCourse.created_at.desc()).all()
    if not courses:
        return []
    keys = [c.key for c in courses]
    media_of = {c.key: (c.media_type or 'html') for c in courses}
    modes = {k: m for k, m in db.session.query(CourseAccess.course_key, CourseAccess.mode)
             .filter(CourseAccess.course_key.in_(keys)).all()}
    enrolled = {e.course_key: e for e in CourseEnrollment.query.filter(
        CourseEnrollment.user_id == uid, CourseEnrollment.course_key.in_(keys)).all()}
    keys_by_media = defaultdict(list)
    for k, m in media_of.items():
        keys_by_media[m].append(k)
    prog = {k: p for (k, _u), p in _progress_map(keys_by_media, {uid}).items()}
    overrides = _overrides([k for k in prog if media_of[k] == 'html'])
    out = []
    for c in courses:
        k = c.key
        mode = modes.get(k, DEFAULT_MODE)
        if not (k in enrolled or (mode == 'open' and k in prog)):
            continue
        # enrolled 本身即可见;open 课全员可见 —— 无需再判 can_view_course
        media = media_of[k]
        pages = _pages_for(k) if media == 'html' and k in prog else []
        cell = _cell(media, prog.get(k), pages, overrides.get(k))
        cell['last_activity'] = _iso(cell['last_activity'])
        cell.update({'key': k, 'title': c.title, 'subtitle': c.subtitle or '', 'media_type': media,
                     'mode': mode, 'enrolled': k in enrolled,
                     'enrolled_at': _iso(enrolled[k].added_at) if k in enrolled else None,
                     'url': course_url(k, media)})
        out.append(cell)
    out.sort(key=lambda d: (d['perfect'], not d['enrolled'], d['title']))
    return out


# ══════════ 管理总览 ══════════

def admin_courses():
    """所有课程 + 开放模式 + 学员数 + 审核人 + 题库健康(HTML 课)。固定次数查询。"""
    from app.models.course import InteractiveCourse
    from app.models.user import User
    courses = InteractiveCourse.query.order_by(InteractiveCourse.created_at.desc()).all()
    keys = [c.key for c in courses]
    if not keys:
        return []
    modes = {k: m for k, m in db.session.query(CourseAccess.course_key, CourseAccess.mode)
             .filter(CourseAccess.course_key.in_(keys)).all()}
    counts = {k: int(n) for k, n in db.session.query(CourseEnrollment.course_key, func.count(CourseEnrollment.id))
              .filter(CourseEnrollment.course_key.in_(keys)).group_by(CourseEnrollment.course_key).all()}
    reviewers = defaultdict(list)
    for k, u in (db.session.query(CourseReviewer.course_key, User)
                 .join(User, User.id == CourseReviewer.user_id)
                 .filter(CourseReviewer.course_key.in_(keys))
                 .order_by(CourseReviewer.added_at, User.id).all()):
        reviewers[k].append(_user_brief(u))
    html = [c.key for c in courses if (c.media_type or 'html') == 'html']
    bank = defaultdict(list)
    status_count = defaultdict(lambda: {'active': 0, 'review': 0, 'disabled': 0})
    if html:
        for k, t, d, st in (db.session.query(CourseQuizQuestion.course_key, CourseQuizQuestion.qtype,
                                             CourseQuizQuestion.difficulty, CourseQuizQuestion.status)
                            .filter(CourseQuizQuestion.course_key.in_(html)).all()):
            if st in status_count[k]:
                status_count[k][st] += 1
            if st == 'active':
                bank[k].append({'qtype': t, 'difficulty': d})
    out = []
    for c in courses:
        media = c.media_type or 'html'
        d = {'key': c.key, 'title': c.title, 'subtitle': c.subtitle or '', 'media_type': media,
             'mode': modes.get(c.key, DEFAULT_MODE), 'enrolled_count': counts.get(c.key, 0),
             'reviewers': reviewers.get(c.key, []), 'page_count': c.page_count or 0,
             'url': course_url(c.key, media), 'bank': None}
        if media == 'html':
            h = L.bank_health(bank.get(c.key, []))
            d['bank'] = dict(status_count[c.key], ok=h['ok'], max_score=h['max_score'],
                             bank_url=bank_url(c.key))
        out.append(d)
    return out
