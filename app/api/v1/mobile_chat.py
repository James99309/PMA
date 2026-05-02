# -*- coding: utf-8 -*-
"""
移动端聊天接口 —— 复用 chat_service 业务逻辑
对应 web 端 app/views/chat.py 的核心端点，仅改换为 JWT 认证

URL prefix: /api/v1/mobile/chat
"""
import logging
from flask import request, jsonify, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity, decode_token
from app.api.v1 import api_v1_bp
from app.api.v1.utils import api_response
from app.models.user import User
from app.models.chat import ChatMessage
from app.services import chat_service
from app import db

logger = logging.getLogger(__name__)


def _current_user():
    """从 JWT 取当前用户对象（多个端点共用）"""
    user_id = int(get_jwt_identity())
    return User.query.get(user_id), user_id


# ─── 1. 会话列表 ──────────────────────────────────────────────────
@api_v1_bp.route('/mobile/chat/conversations', methods=['GET'])
@jwt_required()
def mobile_chat_conversations():
    user, user_id = _current_user()
    if not user:
        return api_response(success=False, code=401, message="用户不存在")
    try:
        viewer_lang = getattr(user, 'language_preference', None) or 'zh'
        return jsonify(chat_service.get_user_conversations(user_id, viewer_language=viewer_lang))
    except Exception as e:
        logger.error(f"mobile chat list error: {e}", exc_info=True)
        return api_response(success=False, code=500, message=str(e))


# ─── 2. 创建对话 ──────────────────────────────────────────────────
@api_v1_bp.route('/mobile/chat/conversations', methods=['POST'])
@jwt_required()
def mobile_chat_create():
    user, user_id = _current_user()
    if not user:
        return api_response(success=False, code=401, message="用户不存在")
    try:
        data = request.get_json() or {}
        return jsonify(chat_service.create_conversation(
            creator_id=user_id,
            participant_ids=data.get('participant_ids', []),
            conv_type=data.get('type'),
            name=data.get('name'),
            sync_metadata=data.get('sync_metadata'),
        ))
    except Exception as e:
        logger.error(f"mobile chat create error: {e}", exc_info=True)
        return api_response(success=False, code=500, message=str(e))


# ─── 3. 拉消息历史 ────────────────────────────────────────────────
@api_v1_bp.route('/mobile/chat/conversations/<int:conv_id>/messages', methods=['GET'])
@jwt_required()
def mobile_chat_messages(conv_id):
    user, user_id = _current_user()
    if not user:
        return api_response(success=False, code=401, message="用户不存在")
    try:
        return jsonify(chat_service.get_messages(
            conversation_id=conv_id,
            user_id=user_id,
            since=request.args.get('since'),
            limit=request.args.get('limit', 50, type=int),
        ))
    except Exception as e:
        logger.error(f"mobile chat get messages error: {e}", exc_info=True)
        return api_response(success=False, code=500, message=str(e))


# ─── 4. 发文本消息 ────────────────────────────────────────────────
@api_v1_bp.route('/mobile/chat/conversations/<int:conv_id>/messages', methods=['POST'])
@jwt_required()
def mobile_chat_send(conv_id):
    user, user_id = _current_user()
    if not user:
        return api_response(success=False, code=401, message="用户不存在")
    try:
        data = request.get_json() or {}
        content = (data.get('content') or '').strip()
        if not content:
            return api_response(success=False, code=400, message="消息内容不能为空")
        return jsonify(chat_service.send_message(
            conversation_id=conv_id,
            sender_id=user_id,
            content=content,
            reply_to_id=data.get('reply_to_id'),
        ))
    except Exception as e:
        logger.error(f"mobile chat send error: {e}", exc_info=True)
        return api_response(success=False, code=500, message=str(e))


# ─── 5. 标记已读（会话级）─────────────────────────────────────────
@api_v1_bp.route('/mobile/chat/conversations/<int:conv_id>/read', methods=['POST'])
@jwt_required()
def mobile_chat_read(conv_id):
    user, user_id = _current_user()
    if not user:
        return api_response(success=False, code=401, message="用户不存在")
    try:
        return jsonify(chat_service.mark_as_read(conversation_id=conv_id, user_id=user_id))
    except Exception as e:
        logger.error(f"mobile chat read error: {e}", exc_info=True)
        return api_response(success=False, code=500, message=str(e))


# ─── 6. 未读总数 ──────────────────────────────────────────────────
@api_v1_bp.route('/mobile/chat/unread-count', methods=['GET'])
@jwt_required()
def mobile_chat_unread_count():
    user, user_id = _current_user()
    if not user:
        return api_response(success=False, code=401, message="用户不存在")
    try:
        return jsonify(chat_service.get_total_unread_count(user_id))
    except Exception as e:
        logger.error(f"mobile chat unread error: {e}", exc_info=True)
        return api_response(success=False, code=500, message=str(e))


# ─── 6b. 会话详情（用于群聊设置页）─────────────────────────────
@api_v1_bp.route('/mobile/chat/conversations/<int:conv_id>', methods=['GET'])
@jwt_required()
def mobile_chat_conversation_detail(conv_id):
    user, user_id = _current_user()
    if not user:
        return api_response(success=False, code=401, message="用户不存在")
    try:
        result = chat_service.get_conversation_detail(conv_id, user_id)
        return jsonify(result), (200 if result.get('success') else 404)
    except Exception as e:
        logger.error(f"mobile chat conv detail error: {e}", exc_info=True)
        return api_response(success=False, code=500, message=str(e))


# ─── 7. 添加群成员 ────────────────────────────────────────────────
@api_v1_bp.route('/mobile/chat/conversations/<int:conv_id>/participants', methods=['POST'])
@jwt_required()
def mobile_chat_add_participants(conv_id):
    user, user_id = _current_user()
    if not user:
        return api_response(success=False, code=401, message="用户不存在")
    try:
        data = request.get_json() or {}
        ids = data.get('user_ids', [])
        if not ids:
            return api_response(success=False, code=400, message="请指定要添加的用户")
        return jsonify(chat_service.add_participants(
            conversation_id=conv_id, user_ids=ids, current_user_id=user_id,
        ))
    except Exception as e:
        logger.error(f"mobile chat add participants error: {e}", exc_info=True)
        return api_response(success=False, code=500, message=str(e))


# ─── 7b. 移除群成员（owner 移除他人 / 自己退群）───────────────
@api_v1_bp.route('/mobile/chat/conversations/<int:conv_id>/participants/<int:target_user_id>',
                 methods=['DELETE'])
@jwt_required()
def mobile_chat_remove_participant(conv_id, target_user_id):
    user, user_id = _current_user()
    if not user:
        return api_response(success=False, code=401, message="用户不存在")
    try:
        result = chat_service.remove_participant(
            conversation_id=conv_id,
            target_user_id=target_user_id,
            current_user_id=user_id,
        )
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        logger.error(f"mobile chat remove participant error: {e}", exc_info=True)
        return api_response(success=False, code=500, message=str(e))


# ─── 8. 删除/退出对话 ────────────────────────────────────────────
@api_v1_bp.route('/mobile/chat/conversations/<int:conv_id>', methods=['DELETE'])
@jwt_required()
def mobile_chat_delete(conv_id):
    user, user_id = _current_user()
    if not user:
        return api_response(success=False, code=401, message="用户不存在")
    try:
        result = chat_service.delete_conversation(conv_id, user_id)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        logger.error(f"mobile chat delete error: {e}", exc_info=True)
        return api_response(success=False, code=500, message=str(e))


# ─── 9. 撤回消息 ──────────────────────────────────────────────────
@api_v1_bp.route('/mobile/chat/messages/<int:msg_id>/recall', methods=['POST'])
@jwt_required()
def mobile_chat_recall(msg_id):
    user, user_id = _current_user()
    if not user:
        return api_response(success=False, code=401, message="用户不存在")
    try:
        result = chat_service.recall_message(msg_id, user_id)
        return jsonify(result), (200 if result.get('success') else 400)
    except Exception as e:
        logger.error(f"mobile chat recall error: {e}", exc_info=True)
        return api_response(success=False, code=500, message=str(e))


# ─── 10. 转发消息 ─────────────────────────────────────────────────
@api_v1_bp.route('/mobile/chat/messages/<int:msg_id>/forward', methods=['POST'])
@jwt_required()
def mobile_chat_forward(msg_id):
    user, user_id = _current_user()
    if not user:
        return api_response(success=False, code=401, message="用户不存在")
    try:
        data = request.get_json() or {}
        target_ids = list(data.get('conversation_ids', []))
        for uid in data.get('user_ids', []):
            r = chat_service.create_conversation(creator_id=user_id, participant_ids=[uid])
            if r.get('success') and r.get('data', {}).get('id'):
                cid = r['data']['id']
                if cid not in target_ids: target_ids.append(cid)
        if not target_ids:
            return api_response(success=False, code=400, message="请选择转发目标")
        return jsonify(chat_service.forward_message(
            message_id=msg_id, sender_id=user_id,
            target_conversation_ids=target_ids, note=data.get('note'),
        ))
    except Exception as e:
        logger.error(f"mobile chat forward error: {e}", exc_info=True)
        return api_response(success=False, code=500, message=str(e))


# ─── 11. @ 用户搜索 ──────────────────────────────────────────────
# 支持 scope 过滤：
#   - conversation_id：限制为该群聊的参与者（@ 群成员）
#   - project_id：限制为该项目的成员（owner + shared_with_users），用于项目讨论卡
#   - 都不传：全员（仅供新建聊天 / 添加成员等用户选择器场景）
@api_v1_bp.route('/mobile/chat/users/search', methods=['GET'])
@jwt_required()
def mobile_chat_users_search():
    user, user_id = _current_user()
    if not user:
        return api_response(success=False, code=401, message="用户不存在")
    try:
        from app.models.chat import ChatConversation, ChatParticipant
        q = request.args.get('q', '').strip()
        conv_id = request.args.get('conversation_id', type=int)
        project_id = request.args.get('project_id', type=int)

        # ── 计算允许的 user_id 集合
        allowed_ids = None  # None 表示无 scope，走全员

        if conv_id:
            conv = ChatConversation.query.get(conv_id)
            if not conv or conv.is_deleted:
                return jsonify({'success': True, 'data': []})
            # 必须是参与者才能搜该群成员
            me_part = ChatParticipant.query.filter_by(
                conversation_id=conv_id, user_id=user_id
            ).first()
            if not me_part:
                return jsonify({'success': True, 'data': []})
            allowed_ids = {p.user_id for p in conv.participants.all()}
        elif project_id:
            from app.models.project import Project
            from app.utils.access_control import can_view_project
            project = Project.query.get(project_id)
            if not project or not can_view_project(user, project):
                return jsonify({'success': True, 'data': []})
            allowed_ids = set()
            if project.owner_id:
                allowed_ids.add(project.owner_id)
            allowed_ids.update(project.shared_with_users or [])

        # ── 构造查询
        query = User.query.filter(User._is_active == True, User.id != user_id)
        if allowed_ids is not None:
            if not allowed_ids:
                return jsonify({'success': True, 'data': []})
            query = query.filter(User.id.in_(allowed_ids))
        if q:
            query = query.filter(db.or_(
                User.real_name.ilike(f'%{q}%'),
                User.username.ilike(f'%{q}%'),
                User.department.ilike(f'%{q}%'),
            ))
        users = query.limit(20).all()
        data = []
        for u in users:
            name = u.real_name or u.username or ''
            data.append({
                'id': u.id,
                'name': name,
                'avatar': name[0] if name else '?',
                'dept': u.department or '',
            })
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"mobile chat users search error: {e}", exc_info=True)
        return api_response(success=False, code=500, message=str(e))


# ─── 12. # 项目搜索（权限过滤）────────────────────────────────
@api_v1_bp.route('/mobile/chat/entity/projects', methods=['GET'])
@jwt_required()
def mobile_chat_entity_projects():
    user, user_id = _current_user()
    if not user:
        return api_response(success=False, code=401, message="用户不存在")
    try:
        from app.models.project import Project
        from app.utils.access_control import get_viewable_data
        from app.utils.dictionary_helpers import project_stage_label

        keyword = request.args.get('q', '').strip()
        filters = []
        if keyword:
            filters.append(Project.project_name.ilike(f'%{keyword}%'))
        projects = get_viewable_data(Project, user, filters).order_by(
            Project.created_at.desc()
        ).limit(20).all()
        return jsonify({'success': True, 'data': [{
            'id': p.id,
            'project_name': p.project_name,
            'current_stage': project_stage_label(p.current_stage) if p.current_stage else '',
            'quotation_customer': p.quotation_customer or 0,
        } for p in projects]})
    except Exception as e:
        logger.error(f"mobile chat search projects error: {e}", exc_info=True)
        return api_response(success=False, code=500, message=str(e))


# ─── 13. $ 客户搜索（权限过滤）────────────────────────────────
@api_v1_bp.route('/mobile/chat/entity/companies', methods=['GET'])
@jwt_required()
def mobile_chat_entity_companies():
    user, user_id = _current_user()
    if not user:
        return api_response(success=False, code=401, message="用户不存在")
    try:
        from app.models.customer import Company
        from app.utils.access_control import get_viewable_data

        keyword = request.args.get('q', '').strip()
        filters = [Company.is_deleted == False]
        if keyword:
            filters.append(Company.company_name.ilike(f'%{keyword}%'))
        companies = get_viewable_data(Company, user, filters).order_by(
            Company.company_name
        ).limit(20).all()
        return jsonify({'success': True, 'data': [{
            'id': c.id,
            'company_name': c.company_name,
            'country': c.country or '',
            'region': c.region or '',
        } for c in companies]})
    except Exception as e:
        logger.error(f"mobile chat search companies error: {e}", exc_info=True)
        return api_response(success=False, code=500, message=str(e))


# ─── 14. AI SSE 流式 ─────────────────────────────────────────────
# 注意：EventSource 不能传自定义 header，所以 token 走 query string
# 调用：fetch('/api/v1/mobile/chat/ai/stream?token=JWT', { method: 'POST', body: ... })
@api_v1_bp.route('/mobile/chat/ai/stream', methods=['POST'])
def mobile_chat_ai_stream():
    """AI 对话 SSE 流式 —— 复用 web 端逻辑，token 走 query string 兼容 EventSource"""
    import json as _json
    from app.services.chat_agent.config import CHAT_CONTEXT_REJECT

    # 从 query string 取 token（EventSource 不支持自定义 header）
    token = request.args.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return api_response(success=False, code=401, message="缺少认证 token")
    try:
        # 用 PyJWT 直解，配 app 的 JWT_SECRET_KEY，避免 flask_jwt_extended 的内部上下文问题
        import jwt as _pyjwt
        from flask import current_app
        secret = current_app.config.get('JWT_SECRET_KEY') or current_app.config.get('SECRET_KEY')
        decoded = _pyjwt.decode(token, secret, algorithms=['HS256'])
        user_id = int(decoded['sub'])
    except Exception as e:
        logger.warning(f"AI stream token decode failed: {type(e).__name__}: {e}")
        return api_response(success=False, code=401, message=f"无效 token: {e}")

    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")

    data = request.get_json() or {}
    content = (data.get('content') or '').strip()
    conversation_id = data.get('conversation_id')

    if not content:
        return api_response(success=False, code=400, message="消息内容不能为空")

    if not conversation_id:
        ai_conv = chat_service.create_ai_conversation(user_id)
        if not ai_conv.get('success'):
            return jsonify(ai_conv), 500
        conversation_id = ai_conv['data']['id']

    # 上下文耗尽预检查
    last_ai_msg = ChatMessage.query.filter_by(
        conversation_id=conversation_id, is_ai_response=True
    ).order_by(ChatMessage.id.desc()).first()
    if last_ai_msg and (last_ai_msg.ai_prompt_tokens or 0) > CHAT_CONTEXT_REJECT:
        chat_service.send_message(conversation_id=conversation_id, sender_id=user_id, content=content)
        sys_msg = ChatMessage(
            conversation_id=conversation_id, sender_id=None,
            content='对话上下文已满，请开启新对话继续与 AI 交流。',
            message_type='context_exhausted', is_ai_response=False,
        )
        db.session.add(sys_msg)
        db.session.commit()
        def _gen_exhausted():
            yield f'data: {_json.dumps({"type": "context_exhausted", "message_id": sys_msg.id}, ensure_ascii=False)}\n\n'
        return Response(_gen_exhausted(), content_type='text/event-stream',
                        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no', 'Connection': 'close'})

    user_msg_result = chat_service.send_message(
        conversation_id=conversation_id, sender_id=user_id, content=content,
    )
    if not user_msg_result.get('success'):
        return jsonify(user_msg_result), 500
    user_msg_id = user_msg_result.get('data', {}).get('id')

    def generate():
        full_response = ''
        try:
            from app.services.chat_agent.agent_loop import ChatAgentLoop
            _loop = ChatAgentLoop(conversation_id=conversation_id, user=user)

            # 先发个 user_message 事件，让客户端能加 message bubble
            yield f'data: {_json.dumps({"type": "user_message", "id": user_msg_id, "content": content}, ensure_ascii=False)}\n\n'

            for ev in _loop.run(content):
                t = ev.get('type')
                if t == 'content':
                    txt = ev.get('text', '')
                    full_response += txt
                    yield f'data: {_json.dumps({"type": "content", "text": txt}, ensure_ascii=False)}\n\n'
                elif t in ('thinking', 'tool_status'):
                    yield f'data: {_json.dumps({"type": "status", "phase": ev.get("phase", ""), "message": ev.get("message", "")}, ensure_ascii=False)}\n\n'
                elif t in ('artifact', 'download'):
                    yield f'data: {_json.dumps(ev, ensure_ascii=False)}\n\n'
                elif t == 'done':
                    yield f'data: {_json.dumps({"type": "done", "conversation_id": conversation_id}, ensure_ascii=False)}\n\n'
                    break
                elif t == 'error':
                    yield f'data: {_json.dumps({"type": "error", "message": ev.get("message", "AI 服务异常")}, ensure_ascii=False)}\n\n'
                    break
        except Exception as e:
            logger.error(f"mobile AI stream error: {e}", exc_info=True)
            yield f'data: {_json.dumps({"type": "error", "message": str(e)}, ensure_ascii=False)}\n\n'

    return Response(stream_with_context(generate()),
                    content_type='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no', 'Connection': 'keep-alive'})
