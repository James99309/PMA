# -*- coding: utf-8 -*-
"""
CLI Agent Blueprint

路由:
    GET   /cli                              主终端页面
    GET   /cli/api/sessions                 列出当前用户所有 active session
    POST  /cli/api/sessions                 新建 session
    POST  /cli/api/sessions/<id>/close      关闭 session
    POST  /cli/api/sessions/<id>/focus      切换焦点到该 session
    PATCH /cli/api/sessions/<id>/title      更新 session 标题
    GET   /cli/api/sessions/<id>/messages   获取 session 消息历史
    GET   /cli/api/sessions/history         列出所有 session(含 CLOSED)
    POST  /cli/api/stream                   流式对话 SSE

权限:
    所有路由要求 @login_required
    Feature flag: 环境变量 ENABLE_CLI_AGENT=true 或 current_user.role=='admin'

详见 docs/plans/2026-04-05-pma-cli-agent-design.md
"""
import json
import logging
import os
import uuid

from flask import (
    Blueprint,
    Response,
    abort,
    jsonify,
    render_template,
    request,
    stream_with_context,
)
from flask_login import current_user, login_required

from app import db
from app.models.cli_session import CliSession
from app.models.user_cli_state import UserCliState

logger = logging.getLogger(__name__)

cli_bp = Blueprint('cli', __name__, url_prefix='/cli')


# ─── Feature flag ───────────────────────────────────────────────────────

def _is_cli_enabled_for(user):
    if os.environ.get('ENABLE_CLI_AGENT', '').lower() in ('true', '1', 'yes'):
        return True
    role = getattr(user, 'role', None)
    return role in ('admin', 'hrdp_manager', 'hr_manager', 'ceo')


def _require_cli_access():
    if not _is_cli_enabled_for(current_user):
        abort(404)


# ─── 主页面 ─────────────────────────────────────────────────────────────

@cli_bp.route('', methods=['GET'])
@cli_bp.route('/', methods=['GET'])
@login_required
def terminal():
    _require_cli_access()

    state = UserCliState.get_or_create(current_user.id)

    # 确保至少有一个 active session,初次访问时自动建一个
    if not state.active_session_ids:
        session = CliSession(
            user_id=current_user.id,
            status=CliSession.STATUS_ACTIVE,
            messages=[],
            usage_total={},
        )
        db.session.add(session)
        db.session.flush()
        state.active_session_ids = [str(session.id)]
        state.current_session_id = str(session.id)
        db.session.commit()

    return render_template('cli/terminal.html')


# ─── Session API ────────────────────────────────────────────────────────

@cli_bp.route('/api/sessions', methods=['GET'])
@login_required
def list_sessions():
    _require_cli_access()
    state = UserCliState.get_or_create(current_user.id)
    db.session.commit()

    active_ids = state.active_session_ids or []
    # 按 active_session_ids 顺序返回
    sessions_by_id = {
        str(s.id): s
        for s in CliSession.query.filter(
            CliSession.user_id == current_user.id,
            CliSession.id.in_([uuid.UUID(i) for i in active_ids]) if active_ids else False,
        ).all()
    }
    active = [
        sessions_by_id[sid].to_dict()
        for sid in active_ids
        if sid in sessions_by_id
    ]
    return jsonify({
        'active': active,
        'current_session_id': state.current_session_id,
    })


@cli_bp.route('/api/sessions', methods=['POST'])
@login_required
def create_session():
    _require_cli_access()

    state = UserCliState.get_or_create(current_user.id)

    session = CliSession(
        user_id=current_user.id,
        status=CliSession.STATUS_ACTIVE,
        messages=[],
        usage_total={},
    )
    db.session.add(session)
    db.session.flush()

    active_ids = list(state.active_session_ids or [])
    active_ids.append(str(session.id))
    state.active_session_ids = active_ids
    state.current_session_id = str(session.id)
    db.session.commit()

    return jsonify({'success': True, 'session': session.to_dict()})


@cli_bp.route('/api/sessions/<session_id>/close', methods=['POST'])
@login_required
def close_session(session_id: str):
    _require_cli_access()

    try:
        sid_uuid = uuid.UUID(session_id)
    except ValueError:
        return jsonify({'success': False, 'error': 'session_id 格式错误'}), 400

    session = CliSession.query.filter_by(id=sid_uuid, user_id=current_user.id).first()
    if not session:
        return jsonify({'success': False, 'error': 'session 不存在'}), 404

    session.status = CliSession.STATUS_CLOSED
    state = UserCliState.get_or_create(current_user.id)
    active_ids = [i for i in (state.active_session_ids or []) if i != session_id]
    state.active_session_ids = active_ids
    if state.current_session_id == session_id:
        state.current_session_id = active_ids[-1] if active_ids else None
    db.session.commit()

    return jsonify({'success': True})


@cli_bp.route('/api/sessions/<session_id>/focus', methods=['POST'])
@login_required
def focus_session(session_id: str):
    _require_cli_access()

    state = UserCliState.get_or_create(current_user.id)
    if session_id not in (state.active_session_ids or []):
        return jsonify({'success': False, 'error': 'session 不在活跃列表'}), 400
    state.current_session_id = session_id
    db.session.commit()
    return jsonify({'success': True})


@cli_bp.route('/api/sessions/<session_id>/title', methods=['PATCH'])
@login_required
def update_session_title(session_id: str):
    """更新 session 标题(前端在首次发送消息时自动调用)"""
    _require_cli_access()

    try:
        sid_uuid = uuid.UUID(session_id)
    except ValueError:
        return jsonify({'success': False, 'error': 'session_id 格式错误'}), 400

    session = CliSession.query.filter_by(id=sid_uuid, user_id=current_user.id).first()
    if not session:
        return jsonify({'success': False, 'error': 'session 不存在'}), 404

    data = request.get_json(silent=True) or {}
    title = (data.get('title') or '').strip()[:120]
    if title:
        session.title = title
        db.session.commit()

    return jsonify({'success': True})


@cli_bp.route('/api/sessions/history', methods=['GET'])
@login_required
def session_history():
    """列出当前用户所有 session(含 CLOSED),供 /history 命令使用"""
    _require_cli_access()

    sessions = CliSession.query.filter(
        CliSession.user_id == current_user.id,
        CliSession.status != CliSession.STATUS_ARCHIVED,
    ).order_by(CliSession.last_active_at.desc()).limit(50).all()

    return jsonify({
        'success': True,
        'sessions': [s.to_dict() for s in sessions],
    })


@cli_bp.route('/api/sessions/<session_id>/messages', methods=['GET'])
@login_required
def get_session_messages(session_id: str):
    """获取单个 session 的完整消息历史(前端切换标签时调用)"""
    _require_cli_access()

    try:
        sid_uuid = uuid.UUID(session_id)
    except ValueError:
        return jsonify({'success': False, 'error': 'session_id 格式错误'}), 400

    session = CliSession.query.filter_by(id=sid_uuid, user_id=current_user.id).first()
    if not session:
        return jsonify({'success': False, 'error': 'session 不存在'}), 404

    return jsonify({
        'success': True,
        'session': session.to_dict(),
        'messages': session.messages or [],
    })


# ─── SSE 对话流 ──────────────────────────────────────────────────────────

@cli_bp.route('/api/stream', methods=['POST'])
@login_required
def stream_chat():
    """SSE 流式对话入口。

    请求体: {"session_id": "...", "input": "用户的自然语言问题"}
    响应: text/event-stream,每个事件是一行 data: {json}\\n\\n
    """
    _require_cli_access()

    data = request.get_json(silent=True) or {}
    session_id = (data.get('session_id') or '').strip()
    user_input = (data.get('input') or '').strip()

    if not session_id:
        return jsonify({'success': False, 'error': 'session_id 缺失'}), 400
    if not user_input:
        return jsonify({'success': False, 'error': 'input 缺失'}), 400

    try:
        sid_uuid = uuid.UUID(session_id)
    except ValueError:
        return jsonify({'success': False, 'error': 'session_id 格式错误'}), 400

    # 预加载 session 和 user,避免在生成器内因 scope 失效
    session = CliSession.query.filter_by(id=sid_uuid, user_id=current_user.id).first()
    if not session:
        return jsonify({'success': False, 'error': 'session 不存在'}), 404
    user = current_user._get_current_object()

    def generate():
        from app.services.cli_agent.agent_loop import AgentLoop
        try:
            loop = AgentLoop(session=session, user=user)
            for event in loop.run(user_input):
                yield f'data: {json.dumps(event, ensure_ascii=False)}\n\n'
        except Exception as e:
            logger.exception('[CLI Agent] stream 处理异常')
            err = {'type': 'error', 'message': f'服务器异常: {e}'}
            yield f'data: {json.dumps(err, ensure_ascii=False)}\n\n'

    return Response(
        stream_with_context(generate()),
        content_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',  # 禁用 nginx 缓冲
        },
    )


# ─── Skill API ──────────────────────────────────────────────────────────

@cli_bp.route('/api/skills', methods=['GET'])
@login_required
def list_skills():
    """列出当前用户可用的 Skill"""
    _require_cli_access()
    from app.models.cli_skill import CliSkill
    from sqlalchemy import or_

    skills = CliSkill.query.filter(
        CliSkill.is_active == True,
        or_(
            CliSkill.scope == 'global',
            CliSkill.created_by == current_user.id,
        ),
    ).order_by(CliSkill.title).all()

    return jsonify({
        'success': True,
        'skills': [s.to_dict() for s in skills],
    })


@cli_bp.route('/api/skills/<int:skill_id>', methods=['GET'])
@login_required
def get_skill(skill_id: int):
    """获取单个 Skill 详情"""
    _require_cli_access()
    from app.models.cli_skill import CliSkill

    skill = CliSkill.query.get(skill_id)
    if not skill:
        return jsonify({'success': False, 'error': 'Skill 不存在'}), 404

    return jsonify({'success': True, 'skill': skill.to_dict()})


@cli_bp.route('/api/skills/<int:skill_id>', methods=['DELETE'])
@login_required
def delete_skill(skill_id: int):
    """删除 Skill（仅创建者或 admin）"""
    _require_cli_access()
    from app.models.cli_skill import CliSkill

    skill = CliSkill.query.get(skill_id)
    if not skill:
        return jsonify({'success': False, 'error': 'Skill 不存在'}), 404

    is_admin = getattr(current_user, 'role', None) == 'admin'
    if skill.created_by != current_user.id and not is_admin:
        return jsonify({'success': False, 'error': '无权删除此 Skill'}), 403

    db.session.delete(skill)
    db.session.commit()
    return jsonify({'success': True})


# ─── 文件导出下载 ──────────────────────────────────────────────────────

# ─── Memory API ─────────────────────────────────────────────────────

@cli_bp.route('/api/memories', methods=['GET'])
@login_required
def list_memories():
    """列出当前用户可见的记忆"""
    _require_cli_access()
    from app.models.cli_memory import CliMemory
    from sqlalchemy import or_, and_

    user_role = getattr(current_user, 'role', '')
    memories = CliMemory.query.filter(
        CliMemory.is_active == True,
        or_(
            CliMemory.scope == 'system',
            CliMemory.scope == f'role:{user_role}',
            and_(CliMemory.scope == 'personal', CliMemory.user_id == current_user.id),
        )
    ).order_by(CliMemory.scope, CliMemory.id).all()

    return jsonify({
        'success': True,
        'memories': [m.to_dict() for m in memories],
    })


# ─── 文件导出下载 ──────────────────────────────────────────────────────

@cli_bp.route('/api/exports/<filename>', methods=['GET'])
@login_required
def download_export(filename: str):
    """下载 CLI Agent 导出的文件"""
    _require_cli_access()
    import os
    import urllib.parse
    from flask import send_file, current_app
    # 安全检查：防止路径穿越
    safe_name = os.path.basename(urllib.parse.unquote(filename))
    # 项目根目录/storage/exports
    project_root = current_app.root_path.rsplit('/app', 1)[0]
    storage_dir = os.path.join(project_root, 'storage', 'exports')
    file_path = os.path.join(storage_dir, safe_name)

    if not os.path.exists(file_path):
        return jsonify({'success': False, 'error': '文件不存在或已过期'}), 404

    return send_file(
        file_path,
        as_attachment=True,
        download_name=safe_name,
    )
