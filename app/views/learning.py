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
import threading
from collections import defaultdict

from flask import Blueprint, jsonify, request, abort, url_for, render_template, current_app, g
from flask_babel import gettext as _
from flask_login import login_required, current_user
from flask_wtf.csrf import CSRFError, generate_csrf

from sqlalchemy import text

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
    'forbidden': 403,
    'not_found': 404,
    'unavailable': 400,
    'invalid_plan': 400,
    'running': 409,
    'bad_params': 400,
    'regenerate_failed': 422,
    'busy': 409,
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
    if code == 'forbidden':
        return _('无权管理题库')
    if code == 'not_found':
        return _('题目不存在')
    if code == 'invalid_plan':
        return _('出题数量不正确：每档为非负整数，总数 1~300')
    if code == 'running':
        return _('本课程正在生成题库，请等待完成')
    if code == 'bad_params':
        return _('参数不正确')
    if code == 'regenerate_failed':
        return _('AI 重出失败，请稍后再试')
    if code == 'busy':
        return _('这道题正在 AI 重出，请稍候')
    if code == 'no_pages':
        return _('该课程没有逐页讲解，无法出题')
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


def _seed_quietly(keys):
    """首次访问自动导入随代码发布的种子题库(本进程记忆已检查过的课,常态零查询)。
    导入失败只记日志,不影响页面 / 考核本身。"""
    try:
        S.ensure_seeded_many(keys)
    except Exception:
        db.session.rollback()
        logger.exception('种子题库导入失败 %s', keys)


_buddy_pref_warned = False


@learning_bp.app_context_processor
def _inject_course_buddy():
    """模板里判断是否挂载小源:cb_buddy_enabled() 仅在登录态下查一次偏好行(无行默认开启)。"""
    def cb_buddy_enabled():
        if not current_user.is_authenticated:
            return False
        # 侧栏开关 + 挂载片段同页各问一次,只查一次库;按用户 id 记,防 g 跨请求复用时串号
        cached = getattr(g, '_cb_buddy_enabled', None)
        if cached is not None and cached[0] == current_user.id:
            return cached[1]
        val = _query_buddy_enabled()
        g._cb_buddy_enabled = (current_user.id, val)
        return val

    def _query_buddy_enabled():
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
    _seed_quietly([ck])
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
    _seed_quietly([ck])
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
        _seed_quietly(keys)          # 题库健康要按导入后的题算
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
    g.pop('_cb_buddy_enabled', None)
    return jsonify({'success': True, 'data': {'enabled': S.set_buddy_enabled(current_user.id, enabled)}})


# ══════════ 题库管理(admin / CEO / HR):生成 / 审题 / 编辑 / 停用 / 重出 / 实测难度 ══════════
# 权限见 S.can_manage_bank;页面无权 → 403 页,API 无权 → 403 JSON。

_STATUSES = ('active', 'review', 'disabled')
REGEN_TIMEOUT = 120             # 单题重出是同步请求,AI 调用超时收短,别长时间占住 worker
_REGEN_INFLIGHT = set()         # 本进程在途的单题重出(按题 id),防重复点击并发出题
_REGEN_LOCK = threading.Lock()


def _regen_client():
    from app.services.wiki.claude_client import WikiClaudeClient
    return WikiClaudeClient(timeout=REGEN_TIMEOUT)
_CONTENT_FIELDS = ('qtype', 'question', 'options', 'answer', 'explain')


def _bank_forbidden():
    return None if S.can_manage_bank(current_user) else _fail('forbidden', 403)


def _bank_question(course_key, qid):
    q = db.session.get(CourseQuizQuestion, qid)
    return q if q is not None and q.course_key == course_key else None


def _first_attempt_stats(course_key):
    """每人每题只看首次作答 → {question_id(str): (n_first, correct_first)}。

    只认作答时题干与当前题干一致的留痕:题目改过字 / AI 重出后,旧题的作答不再算进实测难度。
    """
    rows = db.session.execute(text("""
        SELECT question_id, count(*) AS n, sum(CASE WHEN is_correct THEN 1 ELSE 0 END) AS c
        FROM (SELECT DISTINCT ON (a.user_id, a.question_id) a.question_id, a.is_correct
              FROM training_quiz_attempt a
              JOIN course_quiz_questions q
                ON q.id::text = a.question_id AND a.question_text = q.question
              WHERE a.course_slug = :k AND a.module_slug = :m AND q.course_key = :k
              ORDER BY a.user_id, a.question_id, a.attempted_at, a.id) first_try
        GROUP BY question_id"""), {'k': course_key, 'm': S.MODULE_SLUG}).fetchall()
    return {str(qid): (int(n), int(c or 0)) for qid, n, c in rows}


def _bank_payload(course_key, pages):
    from app.services.course_exam import generator
    qs = (CourseQuizQuestion.query.filter_by(course_key=course_key)
          .order_by(CourseQuizQuestion.id).all())
    stats = _first_attempt_stats(course_key)
    out = []
    for q in qs:
        d = q.to_admin_dict()
        n, c = stats.get(str(q.id), (0, 0))
        d['stats'] = {'n_first': n, 'correct_first': c,
                      'empirical': L.empirical_difficulty(c, n),
                      'suspicious': L.suspicious(c, n)}
        out.append(d)
    active = [q.as_logic() for q in qs if q.status == 'active']
    return {
        'health': L.bank_health(active),
        'questions': out,
        'min_read_seconds': S.get_min_read_seconds(course_key),
        'auto_read_seconds': L.required_read_seconds(pages) if pages else 0,
        'pages': len(pages),
        'generating': generator.is_running(course_key),
    }


@learning_bp.route('/wiki/play/<key>/bank')
@login_required
def bank_page(key):
    if not S.can_manage_bank(current_user):
        abort(403)
    ck, pages = _course_or_404(key)
    import app.views.knowledge_wiki as KW     # 按模块属性取,测试可改指课件目录
    from app.services.course_exam import generator
    _seed_quietly([ck])              # 种子优先;仍为空才导旧版 .quiz.json
    try:
        S.import_legacy_json(ck, KW.COURSE_ASSETS_DIR)
    except Exception:
        db.session.rollback()
        logger.exception('旧题库导入失败 %s', ck)
    row = InteractiveCourse.query.filter_by(key=ck).first()
    return render_template('knowledge/at_course_bank.html', course_key=ck,
                           course_title=row.title if row else ck,
                           page_labels=[p.get('label') or '' for p in pages],
                           default_plan=generator.DEFAULT_PLAN)


@learning_bp.route('/api/learning/<key>/bank')
@login_required
def bank_list(key):
    denied = _bank_forbidden()
    if denied:
        return denied
    ck, pages = _course_or_404(key)
    return jsonify({'success': True, 'data': _bank_payload(ck, pages)})


@learning_bp.route('/api/learning/<key>/bank/generate', methods=['POST'])
@login_required
def bank_generate(key):
    denied = _bank_forbidden()
    if denied:
        return denied
    ck, pages = _course_or_404(key)
    if not pages:
        return _fail('no_pages', 400)
    from app.services.course_exam import generator
    data = _json_obj()
    plan = data.get('plan') if 'plan' in data else generator.DEFAULT_PLAN
    replace = data.get('replace') is True
    try:
        # 先调用:它会 commit 当前 session(抢占跨进程生成标记)
        started = generator.start_generation(current_app._get_current_object(), ck, pages,
                                             current_user.id, plan, replace)
    except ValueError:
        return _fail('invalid_plan', 400)
    if not started:
        return _fail('running', 409)
    return jsonify({'success': True, 'data': {'generating': True}})


@learning_bp.route('/api/learning/<key>/bank/<int:qid>', methods=['PUT'])
@login_required
def bank_update(key, qid):
    denied = _bank_forbidden()
    if denied:
        return denied
    ck, pages = _course_or_404(key)
    q = _bank_question(ck, qid)
    if q is None:
        return _fail('not_found', 404)
    data = _json_obj()
    status = data.get('status', q.status)
    if status not in _STATUSES:
        return _fail('bad_params', 400)
    merged = {'qtype': data.get('qtype', q.qtype),
              'difficulty': data.get('difficulty', q.difficulty),
              'options': data.get('options', q.options),
              'answer': data.get('answer', q.answer)}
    question = data.get('question', q.question)
    explain = data.get('explain', q.explain)
    try:
        if not isinstance(question, str) or not question.strip():
            raise ValueError(_('题干不能为空'))
        if explain is not None and not isinstance(explain, str):
            raise ValueError(_('解析须为文本'))
        source_page = q.source_page
        if 'source_page' in data:
            raw = data.get('source_page')
            if raw is None or raw == '':
                source_page = None
            else:
                source_page = L._as_int(raw)
                if source_page is None or not 1 <= source_page <= len(pages):
                    raise ValueError(_('出处页须为 1~%(n)s 的整数', n=len(pages)))
        if merged['qtype'] == 'judge':
            merged['options'] = None
        norm = L.normalize_question(merged)
    except ValueError as e:
        return jsonify({'success': False, 'error': 'invalid_question', 'message': str(e)}), 400
    question = question.strip()
    explain = (explain or '').strip() or None
    content_changed = (norm['qtype'] != q.qtype or question != q.question
                       or (norm.get('options') if norm['qtype'] != 'judge' else None) != q.options
                       or norm['answer'] != q.answer or explain != q.explain)
    q.qtype = norm['qtype']
    q.difficulty = norm['difficulty']
    q.question = question
    q.options = norm['options'] if norm['qtype'] != 'judge' else None
    q.answer = norm['answer']
    q.explain = explain
    q.source_page = source_page
    q.status = status
    if content_changed:
        q.origin = 'edited'      # 人工改过内容:重建题库时保留
    db.session.commit()
    return jsonify({'success': True, 'data': q.to_admin_dict()})


@learning_bp.route('/api/learning/<key>/bank/<int:qid>/regenerate', methods=['POST'])
@login_required
def bank_regenerate(key, qid):
    denied = _bank_forbidden()
    if denied:
        return denied
    ck, pages = _course_or_404(key)
    q = _bank_question(ck, qid)
    if q is None:
        return _fail('not_found', 404)
    if not pages:
        return _fail('no_pages', 400)
    from app.services.course_exam import generator
    if generator.is_running(ck):
        # 整库生成(尤其 replace)会改动题库,期间不做单题重出
        return _fail('running', 409)
    with _REGEN_LOCK:
        if qid in _REGEN_INFLIGHT:
            return _fail('busy', 409)
        _REGEN_INFLIGHT.add(qid)
    try:
        src = q.to_admin_dict()
        others = [t for (t,) in db.session.query(CourseQuizQuestion.question).filter(
            CourseQuizQuestion.course_key == ck, CourseQuizQuestion.id != q.id,
            CourseQuizQuestion.status != 'disabled').all()]
        db.session.rollback()       # AI 调用耗时较长,别挂着空闲事务
        client = None
        try:
            client = _regen_client()
            new = generator.regenerate_one(pages, src, client=client, existing_questions=others)
            norm = L.normalize_question({'qtype': new.get('qtype'), 'difficulty': new.get('difficulty'),
                                         'options': new.get('options'), 'answer': new.get('answer')})
            question = new.get('question')
            if not isinstance(question, str) or not question.strip():
                raise ValueError('empty question')
        except ValueError:
            logger.warning('单题重出无可用结果 %s#%s', ck, qid, exc_info=True)
            return _fail('regenerate_failed', 422)
        except Exception:
            logger.exception('单题重出调用失败 %s#%s', ck, qid)
            return _fail('regenerate_failed', 502)
        finally:
            if client is not None:
                try:
                    client.close()
                except Exception:
                    pass
        return _apply_regenerated(ck, qid, new, norm, question)
    finally:
        with _REGEN_LOCK:
            _REGEN_INFLIGHT.discard(qid)


def _apply_regenerated(ck, qid, new, norm, question):
    q = _bank_question(ck, qid)
    if q is None:
        return _fail('not_found', 404)
    q.qtype = norm['qtype']
    q.difficulty = norm['difficulty']
    q.question = question.strip()
    q.options = norm['options'] if norm['qtype'] != 'judge' else None
    q.answer = norm['answer']
    q.explain = (new.get('explain') or '').strip() or None
    q.source_page = new.get('source_page')
    q.ai_difficulty = None
    q.status = 'review'
    q.origin = 'ai'
    q.review_note = '单题重出'
    db.session.commit()
    return jsonify({'success': True, 'data': q.to_admin_dict()})


@learning_bp.route('/api/learning/<key>/bank/approve-all', methods=['POST'])
@login_required
def bank_approve_all(key):
    denied = _bank_forbidden()
    if denied:
        return denied
    ck, _pages = _course_or_404(key)
    n = CourseQuizQuestion.query.filter_by(course_key=ck, status='review').update(
        {'status': 'active'}, synchronize_session=False)
    db.session.commit()
    return jsonify({'success': True, 'data': {'approved': n}})


@learning_bp.route('/api/learning/<key>/settings', methods=['POST'])
@login_required
def bank_settings(key):
    denied = _bank_forbidden()
    if denied:
        return denied
    ck, pages = _course_or_404(key)
    raw = _json_obj().get('min_read_seconds')
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        value = None
    else:
        value = L._as_int(raw)
        if value is None or not 0 <= value <= S.MAX_MIN_READ_SECONDS:
            return _fail('bad_params', 400)
    value = S.set_min_read_seconds(ck, value, current_user.id)
    return jsonify({'success': True, 'data': {
        'min_read_seconds': value,
        'auto_read_seconds': L.required_read_seconds(pages) if pages else 0}})
