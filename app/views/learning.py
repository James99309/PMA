# -*- coding: utf-8 -*-
"""学习伙伴小源 + 课程考核 学员端 API。

判分全在服务端(app/services/course_exam/service.py),任何响应在提交前都不含答案/解析。
只支持 HTML 互动课件(media_type == 'html');视频 / PPT 课程一律 404。
权限:只要求登录(@login_required),与课程播放页 play_course 一致;所有查询都限定 current_user 本人。
课件解析不出页面(非 deck 格式)的课视为「暂不支持考核」:进度带 unavailable,上报空转,考核 403。
CSRF:本蓝图不豁免,前端 POST 统一带 X-CSRFToken 头;token 过期时返回 JSON error='csrf',
前端调 GET /api/learning/csrf 取新 token 后重试。
"""
import logging
import os
from collections import defaultdict

from flask import Blueprint, jsonify, request, abort, url_for
from flask_babel import gettext as _
from flask_login import login_required, current_user
from flask_wtf.csrf import CSRFError, generate_csrf

from app import db
from app.models.course import InteractiveCourse
from app.models.course_exam import CourseQuizQuestion, CourseLearningProgress, CourseExamSetting
from app.services.course_exam import service as S
from app.services.course_exam import logic as L

learning_bp = Blueprint('learning', __name__)
logger = logging.getLogger(__name__)

# 服务层错误码 → HTTP 状态码
_ERROR_STATUS = {
    'no_question': 400,
    'bad_answer': 400,
    'already_answered': 409,
    'stale_question': 409,
}


def _error_message(code):
    # 每个分支写成字面量,便于 pybabel extract 抽取
    if code == 'no_question':
        return _('当前没有题目，请刷新')
    if code == 'already_answered':
        return _('这道题已经提交过了')
    if code == 'bad_answer':
        return _('答案格式不正确')
    if code == 'stale_question':
        return _('题目已更新，请重新作答')
    if code == 'locked':
        return _('阅读达标后才能开始考核')
    if code == 'unavailable':
        return _('该课程暂不支持考核')
    if code == 'csrf':
        return _('页面已过期，请刷新后重试')
    return _('操作失败')


def _fail(code, status):
    return jsonify({'success': False, 'error': code, 'message': _error_message(code)}), status


@learning_bp.errorhandler(CSRFError)
def _csrf_error(e):
    """蓝图级处理器:只接管本蓝图路由的 CSRF 失败,其余路径行为不变。"""
    return _fail('csrf', 400)


def _json_obj():
    """请求体须为 JSON 对象;数组 / 字符串 / 非 JSON 一律当空对象。"""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def _course_or_404(key):
    """只支持 HTML 课件。返回 (course_key, pages);pages 可能为 [](暂不支持考核)。"""
    # 延迟导入,避免 knowledge_wiki ↔ learning 循环依赖
    from app.views.knowledge_wiki import _find_course, _get_course_pages
    course, path = _find_course(key)
    if not course or (course.get('media_type') or 'html') != 'html':
        abort(404)
    return course['key'], _get_course_pages(course['key'], path)


def _exam_gate(course_key, pages):
    """考核前置:无页面 → 403 unavailable;未达阅读要求 → 403 locked;通过返回 None。只读,不插行。"""
    if not pages:
        return _fail('unavailable', 403)
    p = S.get_progress(current_user.id, course_key)
    if p is None or p.unlocked_at is None:
        return _fail('locked', 403)
    return None


_buddy_pref_warned = False


@learning_bp.app_context_processor
def _inject_course_buddy():
    """模板里判断是否挂载小源:cb_buddy_enabled() 仅在登录态下查一次偏好行(无行默认开启)。"""
    def cb_buddy_enabled():
        if not current_user.is_authenticated:
            return False
        try:
            # 保存点包住查询:出错只回滚保存点,不波及页面所在请求的外层事务
            with db.session.begin_nested():
                return S.buddy_enabled(current_user.id)
        except Exception:
            global _buddy_pref_warned
            if not _buddy_pref_warned:
                _buddy_pref_warned = True
                logger.warning('小源偏好查询失败,本页不挂载小源(每进程只记一次)', exc_info=True)
            return False
    return {'cb_buddy_enabled': cb_buddy_enabled}


@learning_bp.route('/api/learning/csrf')
@login_required
def csrf_token():
    """CSRF token 过期后前端取新 token 重试。"""
    return jsonify({'success': True, 'token': generate_csrf()})


# ---------- 单课:进度 / 阅读上报 ----------

@learning_bp.route('/api/learning/<key>/progress')
@login_required
def progress(key):
    ck, pages = _course_or_404(key)
    data = S.read_status(current_user.id, ck, pages)
    if not pages:
        data['read']['unavailable'] = True
    return jsonify({'success': True, 'data': data})


@learning_bp.route('/api/learning/<key>/read-ping', methods=['POST'])
@login_required
def read_ping(key):
    ck, pages = _course_or_404(key)
    if not pages:
        # 无页面可计时:空转,不建进度行
        data = S.read_status(current_user.id, ck, pages)
        data['read']['unavailable'] = True
        return jsonify({'success': True, 'data': data})
    data = _json_obj()
    # page / seconds 原样透传,由 logic.record_ping 校验(非法值忽略,不报错)
    return jsonify({'success': True, 'data': S.record_read(
        current_user.id, ck, pages, data.get('page'), data.get('seconds'))})


# ---------- 单课:考核 ----------

@learning_bp.route('/api/learning/<key>/exam/current')
@login_required
def exam_current(key):
    ck, pages = _course_or_404(key)
    blocked = _exam_gate(ck, pages)
    if blocked:
        return blocked
    return jsonify({'success': True, 'data': S.current_question(current_user.id, ck)})


@learning_bp.route('/api/learning/<key>/exam/answer', methods=['POST'])
@login_required
def exam_answer(key):
    ck, pages = _course_or_404(key)
    blocked = _exam_gate(ck, pages)
    if blocked:
        return blocked
    r = S.submit_answer(current_user.id, ck, _json_obj().get('answer'))
    code = r.get('error')
    if code:
        return _fail(code, _ERROR_STATUS.get(code, 400))
    return jsonify({'success': True, 'data': r})


@learning_bp.route('/api/learning/<key>/exam/next', methods=['POST'])
@login_required
def exam_next(key):
    ck, pages = _course_or_404(key)
    blocked = _exam_gate(ck, pages)
    if blocked:
        return blocked
    return jsonify({'success': True, 'data': S.next_question(current_user.id, ck)})


# ---------- 小源:课程外面板 ----------

@learning_bp.route('/api/learning/buddy')
@login_required
def buddy():
    """小源面板:开关状态 + 待学课程(HTML 课 + 有页面 + 题库健康 + 本人未满分)。

    DB 查询次数固定(课程 / 进度 / 题库 / 课程设置 / 小源开关),不随课程数增长;
    页面解析走 _get_course_pages 的 mtime 缓存,每课只多一次 stat。
    """
    from app.views.knowledge_wiki import _course_html_path, _get_course_pages

    uid = current_user.id
    # page_count == 0 是登记时就解析不出页面的课,先在 SQL 里排除,不碰文件
    rows = InteractiveCourse.query.filter(InteractiveCourse.media_type == 'html',
                                          InteractiveCourse.page_count > 0).all()
    pages_by_key = {}
    for r in rows:
        path = _course_html_path(r.key)
        if not os.path.isfile(path):            # 课件不在盘上,点进去会 404
            continue
        pages = _get_course_pages(r.key, path)
        if pages:                               # 解析不出页面 = 暂不支持考核
            pages_by_key[r.key] = pages
    rows = [r for r in rows if r.key in pages_by_key]
    keys = [r.key for r in rows]

    courses = []
    if keys:
        progress = {p.course_key: p for p in CourseLearningProgress.query.filter(
            CourseLearningProgress.user_id == uid,
            CourseLearningProgress.course_key.in_(keys)).all()}
        bank = defaultdict(list)
        for ck, qtype, diff in (db.session.query(CourseQuizQuestion.course_key,
                                                 CourseQuizQuestion.qtype,
                                                 CourseQuizQuestion.difficulty)
                                .filter(CourseQuizQuestion.course_key.in_(keys),
                                        CourseQuizQuestion.status == 'active').all()):
            bank[ck].append({'qtype': qtype, 'difficulty': diff})
        overrides = {ck: sec for ck, sec in db.session.query(
            CourseExamSetting.course_key, CourseExamSetting.min_read_seconds).filter(
            CourseExamSetting.course_key.in_(keys)).all()}

        for r in rows:
            if not L.bank_health(bank.get(r.key, []))['ok']:
                continue
            p = progress.get(r.key)
            if p is not None and p.perfect_at:
                continue
            if p is None:
                read_percent = 0
            else:
                read_percent = S.progress_dict(p, pages_by_key[r.key],
                                               overrides.get(r.key))['read']['percent']
            courses.append({
                'key': r.key,
                'title': r.title,
                'score': p.score if p else 0,
                'read_percent': read_percent,
                'unlocked': bool(p and p.unlocked_at),
                'passed': bool(p and p.passed_at),
                'perfect': False,
                'play_url': url_for('knowledge_wiki.play_course', course_key=r.key),
            })
    courses.sort(key=lambda c: (not c['unlocked'], c['title']))
    return jsonify({'success': True, 'data': {'enabled': S.buddy_enabled(uid), 'courses': courses}})


@learning_bp.route('/api/learning/buddy/toggle', methods=['POST'])
@login_required
def buddy_toggle():
    enabled = _json_obj().get('enabled')
    if not isinstance(enabled, bool):
        return jsonify({'success': False, 'error': 'bad_params',
                        'message': _('参数不正确')}), 400
    return jsonify({'success': True, 'data': {'enabled': S.set_buddy_enabled(current_user.id, enabled)}})
