"""
Training Internal API — pma-training skill (v2.0+) 专用内部接口

鉴权: X-Internal-Token + X-User-ID (复用 internal_api 的同套机制)
URL 前缀: /internal/api/training/*

提供给 PMA MCP Server 的 7 个工具背后的 HTTP 端点:
- GET  /user-context                                — 拿用户 company/role/department
- GET  /state                                       — 拿学员所有培训状态
- POST /state                                       — 写学员模块状态
- POST /quiz/attempt                                — 记答题(自动调度错题本)
- GET  /quiz/due-review                             — 拿今天该复习的错题
- POST /streak/update                               — 维护连续学习
- POST /application/submit                          — 应用任务交付
"""
import logging
from datetime import datetime, date, timedelta
from functools import wraps
from zoneinfo import ZoneInfo

from flask import Blueprint, request, jsonify, g
import hmac, os

from app import db
from app.models.user import User
from app.models.training import (
    TrainingModuleState, TrainingQuizAttempt,
    TrainingStreak, TrainingApplicationSubmission,
)


logger = logging.getLogger(__name__)

training_api_bp = Blueprint('training_api', __name__, url_prefix='/internal/api/training')


# ---------------------------------------------------------------------------
# 鉴权装饰器 (复制自 internal_api 以保持自包含)
# ---------------------------------------------------------------------------

def internal_auth_required(f):
    """验证 X-Internal-Token + X-User-ID, 成功后将 user 存入 g.current_user"""
    @wraps(f)
    def decorated(*args, **kwargs):
        expected = os.environ.get('INTERNAL_API_TOKEN', '').strip()
        if not expected:
            return jsonify({'error': 'INTERNAL_API_TOKEN not configured'}), 503

        provided = request.headers.get('X-Internal-Token', '')
        if not hmac.compare_digest(provided, expected):
            return jsonify({'error': 'Invalid or missing X-Internal-Token'}), 401

        raw = request.headers.get('X-User-ID', '').strip()
        if not raw:
            return jsonify({'error': 'Missing X-User-ID header'}), 400
        try:
            user_id = int(raw)
        except ValueError:
            return jsonify({'error': 'X-User-ID must be integer'}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': f'User {user_id} not found'}), 404

        g.current_user = user
        return f(*args, **kwargs)

    return decorated


def _today_local() -> date:
    return datetime.now(ZoneInfo('Asia/Shanghai')).date()


# ---------------------------------------------------------------------------
# 1. GET /user-context — 拿用户角色/部门/公司
# ---------------------------------------------------------------------------

@training_api_bp.route('/user-context', methods=['GET'])
@internal_auth_required
def get_user_context():
    """返回学员的角色 / 部门 / 公司信息, 供 curriculum 过滤用.

    company 推断逻辑(暂行):
    - 若 User 模型有 company_entity 字段(归属 CompanyEntity) -> 用之
    - 否则 fallback 到 env var PMA_DB_TYPE (sp8d=evertac_cn, ovs=evertac_sg) -> evertac
    """
    user = g.current_user
    # 推断 company: 默认 evertac (单租户场景)
    db_type = (os.environ.get('PMA_DB_TYPE') or '').strip().lower()
    company = 'evertac'  # 单租户默认值; 多企业部署时由 user.company_entity 决定

    department = ''
    if hasattr(user, 'department') and user.department:
        # User.department 可能是关系或字符串字段
        dep = user.department
        department = getattr(dep, 'name', None) or (dep if isinstance(dep, str) else '')

    return jsonify({
        'user_id': user.id,
        'username': user.username,
        'real_name': getattr(user, 'real_name', '') or user.username,
        'role': getattr(user, 'role', '') or 'employee',
        'department': department,
        'company': company,
        'db_region': 'cn' if db_type == 'sp8d' else ('sg' if db_type == 'ovs' else 'local'),
    })


# ---------------------------------------------------------------------------
# 2. GET /state — 拿学员所有培训状态
# ---------------------------------------------------------------------------

@training_api_bp.route('/state', methods=['GET'])
@internal_auth_required
def get_training_state():
    """返回学员 dashboard 需要的全部状态:
    - 各模块进度列表
    - streak
    - 错题本待复习数
    """
    user = g.current_user

    modules = TrainingModuleState.query.filter_by(user_id=user.id).all()

    streak_row = TrainingStreak.query.get(user.id)
    streak = streak_row.to_dict() if streak_row else {
        'user_id': user.id,
        'last_learned_date': None,
        'current_streak': 0,
        'longest_streak': 0,
        'streak_freeze_count': 0,
        'updated_at': None,
    }

    # 错题本待复习: scheduled_review_at <= now 的题目数
    now = datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)
    due_review_count = (
        TrainingQuizAttempt.query
        .filter(TrainingQuizAttempt.user_id == user.id)
        .filter(TrainingQuizAttempt.scheduled_review_at != None)  # noqa: E711
        .filter(TrainingQuizAttempt.scheduled_review_at <= now)
        .count()
    )

    return jsonify({
        'modules': [m.to_dict() for m in modules],
        'streak': streak,
        'due_review_count': due_review_count,
    })


# ---------------------------------------------------------------------------
# 3. POST /state — 写学员模块状态(upsert)
# ---------------------------------------------------------------------------

@training_api_bp.route('/state', methods=['POST'])
@internal_auth_required
def save_training_state():
    """Upsert TrainingModuleState. 必填: course_slug, module_slug.
    可选: status / current_chapter / current_section / chapters_passed /
          final_exam_score / final_exam_passed_at / badge_awarded
    """
    user = g.current_user
    data = request.get_json(silent=True) or {}

    course_slug = (data.get('course_slug') or '').strip()
    module_slug = (data.get('module_slug') or '').strip()
    if not course_slug or not module_slug:
        return jsonify({'error': 'course_slug and module_slug required'}), 400

    state = TrainingModuleState.query.filter_by(
        user_id=user.id, course_slug=course_slug, module_slug=module_slug
    ).first()

    if not state:
        state = TrainingModuleState(
            user_id=user.id,
            course_slug=course_slug,
            module_slug=module_slug,
        )
        db.session.add(state)

    # 选择性 patch
    for fld in ('status', 'current_chapter', 'current_section',
                'chapters_passed', 'final_exam_score', 'badge_awarded'):
        if fld in data:
            setattr(state, fld, data[fld])

    if 'final_exam_passed_at' in data and data['final_exam_passed_at']:
        try:
            state.final_exam_passed_at = datetime.fromisoformat(data['final_exam_passed_at'])
        except ValueError:
            pass

    db.session.commit()
    return jsonify({'state': state.to_dict()})


# ---------------------------------------------------------------------------
# 4. POST /quiz/attempt — 记一次答题 (自动调度错题本)
# ---------------------------------------------------------------------------

# 错题本间隔: 答错或第 N 次错的下次复习时间
REVIEW_INTERVALS_HOURS = [24, 72, 168, 336]  # 1d / 3d / 7d / 14d


@training_api_bp.route('/quiz/attempt', methods=['POST'])
@internal_auth_required
def record_quiz_attempt():
    """记一次答题. 必填: course_slug / module_slug / chapter / question_id /
       question_text / user_answer / is_correct.
       可选: question_type / correct_answer

    自动维护错题本:
    - is_correct=False -> scheduled_review_at = now + 24h, reviewed_count = 0
    - is_correct=True 且之前在错题本 -> 升级 (reviewed_count++, 间隔翻倍; >=3 次答对 -> 移出)
    - 全新答对的题不进错题本 (scheduled_review_at = None)
    """
    user = g.current_user
    data = request.get_json(silent=True) or {}

    required = ['course_slug', 'module_slug', 'chapter', 'question_id',
                'question_text', 'is_correct']
    for k in required:
        if k not in data:
            return jsonify({'error': f'{k} required'}), 400

    is_correct = bool(data['is_correct'])
    qid = (data.get('question_id') or '').strip()
    now = datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)

    # 错题本调度: 看这个题目是否已在错题本里
    prior = (
        TrainingQuizAttempt.query
        .filter_by(user_id=user.id, question_id=qid)
        .order_by(TrainingQuizAttempt.attempted_at.desc())
        .first()
    )

    if is_correct:
        if prior and prior.scheduled_review_at is not None:
            # 升级间隔: 已答错过 -> 这次答对, reviewed_count++
            new_reviewed = (prior.reviewed_count or 0) + 1
            if new_reviewed >= 3:
                scheduled = None  # 出错题本
            else:
                idx = min(new_reviewed, len(REVIEW_INTERVALS_HOURS) - 1)
                scheduled = now + timedelta(hours=REVIEW_INTERVALS_HOURS[idx])
            reviewed_count = new_reviewed
        else:
            # 全新答对 — 不进错题本
            scheduled = None
            reviewed_count = 0
    else:
        # 答错 -> 进错题本, 24h 后复习, 计数归 1
        scheduled = now + timedelta(hours=REVIEW_INTERVALS_HOURS[0])
        reviewed_count = 1

    rec = TrainingQuizAttempt(
        user_id=user.id,
        course_slug=data['course_slug'],
        module_slug=data['module_slug'],
        chapter=int(data['chapter']),
        question_id=qid,
        question_text=data['question_text'],
        question_type=data.get('question_type'),
        user_answer=data.get('user_answer'),
        correct_answer=data.get('correct_answer'),
        is_correct=is_correct,
        attempted_at=now,
        scheduled_review_at=scheduled,
        reviewed_count=reviewed_count,
    )
    db.session.add(rec)
    db.session.commit()

    return jsonify({'attempt': rec.to_dict()})


# ---------------------------------------------------------------------------
# 5. GET /quiz/due-review — 拿今天该复习的错题
# ---------------------------------------------------------------------------

@training_api_bp.route('/quiz/due-review', methods=['GET'])
@internal_auth_required
def get_due_review_questions():
    """返回 scheduled_review_at <= now 的最近一次答题记录, 每个 question_id 取最新."""
    user = g.current_user
    now = datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)
    limit = int(request.args.get('limit') or 20)

    # 子查询: 每个 question_id 取最新的 attempted_at
    from sqlalchemy import func
    latest = (
        db.session.query(
            TrainingQuizAttempt.question_id,
            func.max(TrainingQuizAttempt.attempted_at).label('latest_at'),
        )
        .filter(TrainingQuizAttempt.user_id == user.id)
        .filter(TrainingQuizAttempt.scheduled_review_at != None)  # noqa: E711
        .filter(TrainingQuizAttempt.scheduled_review_at <= now)
        .group_by(TrainingQuizAttempt.question_id)
        .subquery()
    )

    rows = (
        db.session.query(TrainingQuizAttempt)
        .join(latest,
              (TrainingQuizAttempt.question_id == latest.c.question_id) &
              (TrainingQuizAttempt.attempted_at == latest.c.latest_at))
        .filter(TrainingQuizAttempt.user_id == user.id)
        .order_by(TrainingQuizAttempt.scheduled_review_at.asc())
        .limit(limit)
        .all()
    )

    return jsonify({
        'count': len(rows),
        'questions': [r.to_dict() for r in rows],
    })


# ---------------------------------------------------------------------------
# 6. POST /streak/update — 维护连续学习
# ---------------------------------------------------------------------------

@training_api_bp.route('/streak/update', methods=['POST'])
@internal_auth_required
def update_streak():
    """学员有任意学习动作时调用. 自动:
    - 同日二次调用 -> 不变(已 maintain)
    - 昨天有学习记录 -> current_streak +1
    - 超过 1 天没学 -> 看 freeze 券, 有则消耗 1 张保持; 无则归 0
    """
    user = g.current_user
    today = _today_local()

    streak = TrainingStreak.query.get(user.id)
    if not streak:
        streak = TrainingStreak(
            user_id=user.id,
            last_learned_date=today,
            current_streak=1,
            longest_streak=1,
            streak_freeze_count=0,
        )
        db.session.add(streak)
        db.session.commit()
        return jsonify({'streak': streak.to_dict(), 'event': 'first_day'})

    if streak.last_learned_date == today:
        # 今天已有学习 -> 不变
        return jsonify({'streak': streak.to_dict(), 'event': 'already_today'})

    gap_days = (today - streak.last_learned_date).days if streak.last_learned_date else 999

    if gap_days == 1:
        # 昨天有学习 -> +1
        streak.current_streak = (streak.current_streak or 0) + 1
        streak.longest_streak = max(streak.longest_streak or 0, streak.current_streak)
        event = 'incremented'
    elif gap_days >= 2 and streak.streak_freeze_count and streak.streak_freeze_count > 0:
        # 用 freeze 券保持
        streak.streak_freeze_count -= 1
        event = 'freeze_used'
    else:
        # 中断 -> 归 1 (今天算第 1 天)
        streak.current_streak = 1
        event = 'broken_reset'

    streak.last_learned_date = today
    db.session.commit()
    return jsonify({'streak': streak.to_dict(), 'event': event})


# ---------------------------------------------------------------------------
# 7. POST /application/submit — 应用任务交付
# ---------------------------------------------------------------------------

@training_api_bp.route('/application/submit', methods=['POST'])
@internal_auth_required
def submit_application():
    """应用任务交付归档. 必填: course_slug / module_slug / task_id / submission_text.
    可选: ai_feedback
    """
    user = g.current_user
    data = request.get_json(silent=True) or {}

    required = ['course_slug', 'module_slug', 'task_id', 'submission_text']
    for k in required:
        if not data.get(k):
            return jsonify({'error': f'{k} required'}), 400

    sub = TrainingApplicationSubmission(
        user_id=user.id,
        course_slug=data['course_slug'],
        module_slug=data['module_slug'],
        task_id=data['task_id'],
        submission_text=data['submission_text'],
        ai_feedback=data.get('ai_feedback'),
    )
    db.session.add(sub)
    db.session.commit()

    return jsonify({'submission': sub.to_dict()})
