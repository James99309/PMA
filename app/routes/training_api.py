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
import base64
import hashlib
import json as _json
import time
from datetime import datetime, date, timedelta
from functools import wraps
from zoneinfo import ZoneInfo

from flask import Blueprint, request, jsonify, g, send_file, abort, current_app
import hmac, os

from app import db
from app.models.user import User
from app.models.training import (
    TrainingModuleState, TrainingQuizAttempt,
    TrainingStreak, TrainingApplicationSubmission,
)


logger = logging.getLogger(__name__)

training_api_bp = Blueprint('training_api', __name__, url_prefix='/internal/api/training')

# Separate blueprint for the PUBLIC image endpoint (no auth required, validates HMAC token).
# Mounted at root so URL is short: /wiki-img/<token>
wiki_image_public_bp = Blueprint('wiki_image_public', __name__)


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


# ---------------------------------------------------------------------------
# 8. GET /wiki/image-url — 生成签名 URL (供 AI 内联 ![](url) 到对话)
# ---------------------------------------------------------------------------

def _sign_image_token(article_id: int, asset_path: str, ttl_sec: int = 3600) -> str:
    """生成 HMAC 签名的 wiki 图片访问 token.

    payload = base64url(json({"a": article_id, "p": asset_path, "e": exp}))
    sig     = hex(hmac_sha256(INTERNAL_API_TOKEN, payload))
    token   = f"{payload}.{sig}"

    默认 TTL 1 小时.
    """
    secret = os.environ.get('INTERNAL_API_TOKEN', '').encode()
    if not secret:
        raise RuntimeError('INTERNAL_API_TOKEN not configured')
    exp = int(time.time()) + ttl_sec
    payload = _json.dumps({'a': article_id, 'p': asset_path, 'e': exp}, separators=(',', ':'))
    payload_b64 = base64.urlsafe_b64encode(payload.encode()).decode().rstrip('=')
    sig = hmac.new(secret, payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"


def _verify_image_token(token: str) -> tuple:
    """验证 token, 返回 (article_id, asset_path) 或抛异常."""
    secret = os.environ.get('INTERNAL_API_TOKEN', '').encode()
    if not secret:
        raise PermissionError('INTERNAL_API_TOKEN not configured')

    if '.' not in token:
        raise ValueError('malformed token')
    payload_b64, sig_provided = token.rsplit('.', 1)

    sig_expected = hmac.new(secret, payload_b64.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig_provided, sig_expected):
        raise PermissionError('invalid signature')

    # decode payload
    pad = '=' * (-len(payload_b64) % 4)
    try:
        payload = _json.loads(base64.urlsafe_b64decode(payload_b64 + pad))
    except Exception:
        raise ValueError('payload decode failed')

    if int(payload.get('e', 0)) < int(time.time()):
        raise PermissionError('token expired')

    article_id = int(payload['a'])
    asset_path = str(payload['p'])
    return article_id, asset_path


@training_api_bp.route('/wiki/image-url', methods=['GET'])
@internal_auth_required
def wiki_image_url():
    """返回一个签名 URL, AI 用 `![](signed_url)` 内联到对话即可.
    Cowork 客户端去拉图, 图片字节不进 Claude context.

    Query: article_id, asset_path, ttl (optional, default 3600s, max 86400s)
    """
    article_id_raw = request.args.get('article_id', '').strip()
    asset_path = (request.args.get('asset_path') or '').strip()
    if not article_id_raw or not asset_path:
        return jsonify({'error': 'article_id and asset_path required'}), 400
    try:
        article_id = int(article_id_raw)
    except ValueError:
        return jsonify({'error': 'article_id must be int'}), 400

    try:
        ttl = min(int(request.args.get('ttl') or 3600), 86400)
    except ValueError:
        ttl = 3600

    # Validate article exists + user has access (defense-in-depth: signed URL
    # later is public, but we don't issue a signed URL for non-existent assets).
    from app.models.knowledge import KnowledgeWikiArticle
    from app.services.wiki.paths import get_wiki_dir
    art = KnowledgeWikiArticle.query.get(article_id)
    if art is None:
        return jsonify({'error': f'article {article_id} not found'}), 404
    expected_prefix = f'_assets/{art.slug}/'
    if '..' in asset_path or not asset_path.startswith(expected_prefix):
        return jsonify({'error': 'invalid asset_path'}), 400
    abs_path = (get_wiki_dir() / art.topic / asset_path).resolve()
    base = (get_wiki_dir() / art.topic).resolve()
    try:
        abs_path.relative_to(base)
    except ValueError:
        return jsonify({'error': 'asset out of bounds'}), 400
    if not abs_path.is_file():
        return jsonify({'error': 'asset file missing'}), 404

    token = _sign_image_token(article_id, asset_path, ttl_sec=ttl)
    # Public URL — uses the same host PMA is served on (Tailscale IP / Cloudflare tunnel).
    # AI inlines this URL via ![alt](url); Cowork client-side renders it without
    # putting image bytes into Claude's context.
    base_url = (request.headers.get('X-Public-Base-URL') or '').strip()
    if not base_url:
        # Derive from request.url_root (works for Tailscale direct access).
        base_url = request.url_root.rstrip('/')
    url = f"{base_url}/wiki-img/{token}"

    return jsonify({
        'url': url,
        'expires_at': int(time.time()) + ttl,
        'article_id': article_id,
        'asset_path': asset_path,
    })


# ---------------------------------------------------------------------------
# 9. GET /wiki-img/<token> — PUBLIC (no auth, validates HMAC token)
# ---------------------------------------------------------------------------

@wiki_image_public_bp.route('/wiki-img/<path:token>', methods=['GET'])
def wiki_image_public(token):
    """Public endpoint serving a wiki image. Token = HMAC-signed (article_id, asset_path, exp).

    No login / no X-Internal-Token required — the HMAC IS the auth.
    Used by Cowork client-side image rendering for ![alt](url) markdown.
    """
    try:
        article_id, asset_path = _verify_image_token(token)
    except PermissionError as e:
        abort(403, description=str(e))
    except ValueError as e:
        abort(400, description=str(e))

    from app.models.knowledge import KnowledgeWikiArticle
    from app.services.wiki.paths import get_wiki_dir
    art = KnowledgeWikiArticle.query.get(article_id)
    if art is None:
        abort(404)

    expected_prefix = f'_assets/{art.slug}/'
    if '..' in asset_path or not asset_path.startswith(expected_prefix):
        abort(400)

    abs_path = (get_wiki_dir() / art.topic / asset_path).resolve()
    base = (get_wiki_dir() / art.topic).resolve()
    try:
        abs_path.relative_to(base)
    except ValueError:
        abort(400)
    if not abs_path.is_file():
        abort(404)

    # Optional resize via ?max_width=600 (uses Pillow if available, falls back
    # to serving original if not).
    max_w_raw = request.args.get('max_width', '').strip()
    if max_w_raw and max_w_raw.isdigit():
        max_w = int(max_w_raw)
        try:
            from PIL import Image
            import io
            with Image.open(str(abs_path)) as img:
                if img.width > max_w:
                    ratio = max_w / img.width
                    new_h = int(img.height * ratio)
                    img = img.resize((max_w, new_h), Image.LANCZOS)
                    buf = io.BytesIO()
                    fmt = (img.format or 'JPEG').upper()
                    if fmt not in ('JPEG', 'PNG', 'WEBP'):
                        fmt = 'JPEG'
                    save_kwargs = {'optimize': True}
                    if fmt == 'JPEG':
                        save_kwargs['quality'] = 80
                        if img.mode in ('RGBA', 'LA'):
                            img = img.convert('RGB')
                    img.save(buf, format=fmt, **save_kwargs)
                    buf.seek(0)
                    mime = {'JPEG': 'image/jpeg', 'PNG': 'image/png', 'WEBP': 'image/webp'}[fmt]
                    return send_file(buf, mimetype=mime)
        except ImportError:
            pass  # Pillow not available — serve original
        except Exception as e:
            logger.warning(f'[wiki-img] resize failed for {asset_path}: {e}; serving original')

    return send_file(str(abs_path))
