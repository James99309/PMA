# -*- coding: utf-8 -*-
"""学习伙伴小源 + 课程考核 学员端 API。

判分全在服务端(app/services/course_exam/service.py),任何响应在提交前都不含答案/解析。
只支持 HTML 互动课件(media_type == 'html');视频 / PPT 课程一律 404。
CSRF:本蓝图不豁免,前端 POST 统一带 X-CSRFToken 头(取 meta[name=csrf-token])。
"""
import os
from collections import defaultdict

from flask import Blueprint, jsonify, request, abort, url_for
from flask_babel import gettext as _
from flask_login import login_required, current_user

from app import db
from app.models.course import InteractiveCourse
from app.models.course_exam import CourseQuizQuestion, CourseLearningProgress, CourseExamSetting
from app.services.course_exam import service as S
from app.services.course_exam import logic as L

learning_bp = Blueprint('learning', __name__)

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
    return code


def _fail(code, status):
    return jsonify({'success': False, 'error': code, 'message': _error_message(code)}), status


def _course_or_404(key):
    """只支持 HTML 课件。返回 (row, pages)。"""
    # 延迟导入,避免 knowledge_wiki ↔ learning 循环依赖
    from app.views.knowledge_wiki import _find_course, _get_course_pages
    course, path = _find_course(key)
    if not course or (course.get('media_type') or 'html') != 'html':
        abort(404)
    row = InteractiveCourse.query.filter_by(key=course['key']).first()
    if row is None:
        abort(404)
    return row, _get_course_pages(course['key'], path)


def _require_unlocked(row):
    """未达阅读要求 → 403 locked 响应;已解锁返回 None。只读,不插行。"""
    p = S.get_progress(current_user.id, row.key)
    if p is None or p.unlocked_at is None:
        return _fail('locked', 403)
    return None


# ---------- 单课:进度 / 阅读上报 ----------

@learning_bp.route('/api/learning/<key>/progress')
@login_required
def progress(key):
    row, pages = _course_or_404(key)
    return jsonify({'success': True, 'data': S.read_status(current_user.id, row.key, pages)})


@learning_bp.route('/api/learning/<key>/read-ping', methods=['POST'])
@login_required
def read_ping(key):
    row, pages = _course_or_404(key)
    data = request.get_json(silent=True) or {}
    # page / seconds 原样透传,由 logic.record_ping 校验(非法值忽略,不报错)
    return jsonify({'success': True, 'data': S.record_read(
        current_user.id, row.key, pages, data.get('page'), data.get('seconds'))})


# ---------- 单课:考核 ----------

@learning_bp.route('/api/learning/<key>/exam/current')
@login_required
def exam_current(key):
    row, _pages = _course_or_404(key)
    locked = _require_unlocked(row)
    if locked:
        return locked
    return jsonify({'success': True, 'data': S.current_question(current_user.id, row.key)})


@learning_bp.route('/api/learning/<key>/exam/answer', methods=['POST'])
@login_required
def exam_answer(key):
    row, _pages = _course_or_404(key)
    locked = _require_unlocked(row)
    if locked:
        return locked
    data = request.get_json(silent=True) or {}
    r = S.submit_answer(current_user.id, row.key, data.get('answer'))
    code = r.get('error')
    if code:
        return _fail(code, _ERROR_STATUS.get(code, 400))
    return jsonify({'success': True, 'data': r})


@learning_bp.route('/api/learning/<key>/exam/next', methods=['POST'])
@login_required
def exam_next(key):
    row, _pages = _course_or_404(key)
    locked = _require_unlocked(row)
    if locked:
        return locked
    return jsonify({'success': True, 'data': S.next_question(current_user.id, row.key)})


# ---------- 小源:课程外面板 ----------

@learning_bp.route('/api/learning/buddy')
@login_required
def buddy():
    """小源面板:开关状态 + 待学课程(HTML 课 + 题库健康 + 本人未满分)。

    固定 4 条查询(课程 / 进度 / 题库 / 课程设置),不随课程数增长。
    """
    from app.views.knowledge_wiki import _course_html_path, _get_course_pages

    uid = current_user.id
    rows = InteractiveCourse.query.filter(InteractiveCourse.media_type == 'html').all()
    # 课件文件不在盘上的课点进去会 404,不列
    rows = [r for r in rows if os.path.isfile(_course_html_path(r.key))]
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
                pages = _get_course_pages(r.key, _course_html_path(r.key))
                read_percent = S.progress_dict(p, pages, overrides.get(r.key))['read']['percent']
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
    data = request.get_json(silent=True) or {}
    enabled = data.get('enabled')
    if not isinstance(enabled, bool):
        return jsonify({'success': False, 'error': 'bad_params',
                        'message': _('参数不正确')}), 400
    return jsonify({'success': True, 'data': {'enabled': S.set_buddy_enabled(current_user.id, enabled)}})
