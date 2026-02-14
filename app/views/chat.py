# -*- coding: utf-8 -*-
"""
聊天模块 - 视图层

提供聊天系统所需的 API 接口：
- 对话的 CRUD（私聊、群聊、AI 对话）
- 消息收发与已读标记
- 用户搜索（@提及）
- AI SSE 流式响应
"""
import json
import logging

from flask import Blueprint, jsonify, request, Response, stream_with_context
from flask_login import login_required, current_user

from app import db
from app.models.user import User
from app.services import chat_service

logger = logging.getLogger(__name__)

chat = Blueprint('chat', __name__, url_prefix='/chat')


# ---------------------------------------------------------------------------
# 1. 对话列表
# ---------------------------------------------------------------------------

@chat.route('/api/conversations', methods=['GET'])
@login_required
def get_conversations():
    """获取当前用户的所有对话列表"""
    try:
        result = chat_service.get_user_conversations(current_user.id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取对话列表失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------------------------------------------------------------------------
# 2. 创建对话
# ---------------------------------------------------------------------------

@chat.route('/api/conversations', methods=['POST'])
@login_required
def create_conversation():
    """创建新对话（私聊/群聊/AI对话）"""
    try:
        data = request.get_json() or {}
        participant_ids = data.get('participant_ids', [])
        conv_type = data.get('type')
        name = data.get('name')

        result = chat_service.create_conversation(
            creator_id=current_user.id,
            participant_ids=participant_ids,
            conv_type=conv_type,
            name=name,
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"创建对话失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------------------------------------------------------------------------
# 3. 获取消息列表
# ---------------------------------------------------------------------------

@chat.route('/api/conversations/<int:id>/messages', methods=['GET'])
@login_required
def get_messages(id):
    """获取对话中的消息列表，支持增量拉取"""
    try:
        since = request.args.get('since')
        limit = request.args.get('limit', 50, type=int)

        result = chat_service.get_messages(
            conversation_id=id,
            user_id=current_user.id,
            since=since,
            limit=limit,
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取消息失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------------------------------------------------------------------------
# 4. 发送消息
# ---------------------------------------------------------------------------

@chat.route('/api/conversations/<int:id>/messages', methods=['POST'])
@login_required
def send_message(id):
    """发送消息到对话"""
    try:
        data = request.get_json() or {}
        content = data.get('content', '').strip()

        if not content:
            return jsonify({'success': False, 'message': '消息内容不能为空'}), 400

        result = chat_service.send_message(
            conversation_id=id,
            sender_id=current_user.id,
            content=content,
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"发送消息失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------------------------------------------------------------------------
# 5. 标记已读
# ---------------------------------------------------------------------------

@chat.route('/api/conversations/<int:id>/read', methods=['POST'])
@login_required
def mark_read(id):
    """标记对话为已读"""
    try:
        result = chat_service.mark_as_read(
            conversation_id=id,
            user_id=current_user.id,
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"标记已读失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------------------------------------------------------------------------
# 6. 未读消息总数（轻量接口，用于轮询）
# ---------------------------------------------------------------------------

@chat.route('/api/unread-count', methods=['GET'])
@login_required
def unread_count():
    """获取用户所有对话的未读消息总数"""
    try:
        result = chat_service.get_total_unread_count(current_user.id)
        return jsonify(result)
    except Exception as e:
        logger.error(f"获取未读计数失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------------------------------------------------------------------------
# 7. 添加群聊成员
# ---------------------------------------------------------------------------

@chat.route('/api/conversations/<int:id>/participants', methods=['POST'])
@login_required
def add_participants(id):
    """向群聊中添加新成员"""
    try:
        data = request.get_json() or {}
        user_ids = data.get('user_ids', [])

        if not user_ids:
            return jsonify({'success': False, 'message': '请指定要添加的用户'}), 400

        result = chat_service.add_participants(
            conversation_id=id,
            user_ids=user_ids,
            current_user_id=current_user.id,
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"添加成员失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------------------------------------------------------------------------
# 8. 用户搜索（@提及）
# ---------------------------------------------------------------------------

@chat.route('/api/users/search', methods=['GET'])
@login_required
def search_users():
    """搜索用户，用于 @ 提及功能"""
    try:
        q = request.args.get('q', '').strip()
        if not q:
            return jsonify({'success': True, 'data': []})

        # 搜索活跃用户，排除当前用户
        users = User.query.filter(
            User.is_active == True,
            User.id != current_user.id,
            db.or_(
                User.real_name.ilike(f'%{q}%'),
                User.username.ilike(f'%{q}%'),
                User.department.ilike(f'%{q}%'),
            )
        ).limit(20).all()

        data = []
        for u in users:
            name = u.real_name or u.username or ''
            data.append({
                'id': u.id,
                'name': name,
                'avatar': name[0] if name else '?',
                'dept': u.department or '',
                'lang': u.language_preference or 'zh',
            })

        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"搜索用户失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------------------------------------------------------------------------
# 9. AI SSE 流式响应
# ---------------------------------------------------------------------------

@chat.route('/api/ai/stream', methods=['POST'])
@login_required
def ai_stream():
    """AI 对话的 SSE 流式响应"""
    try:
        data = request.get_json() or {}
        content = data.get('content', '').strip()
        conversation_id = data.get('conversation_id')

        if not content:
            return jsonify({'success': False, 'message': '消息内容不能为空'}), 400

        if not conversation_id:
            # 自动创建或获取 AI 对话
            ai_conv = chat_service.ensure_ai_conversation(current_user.id)
            if not ai_conv.get('success'):
                return jsonify(ai_conv), 500
            conversation_id = ai_conv['data']['id']

        # 1. 先保存用户消息
        user_msg_result = chat_service.send_message(
            conversation_id=conversation_id,
            sender_id=current_user.id,
            content=content,
        )
        if not user_msg_result.get('success'):
            return jsonify(user_msg_result), 500

        # 2. 构建 SSE 流
        def generate():
            full_response = ''
            try:
                from app.services.chat_ai_service import get_ai_response_stream

                for chunk in get_ai_response_stream(content, conversation_id, current_user.id):
                    full_response += chunk
                    event_data = json.dumps({'type': 'content', 'text': chunk}, ensure_ascii=False)
                    yield f'data: {event_data}\n\n'

                # 3. 流结束后保存 AI 回复到数据库
                if full_response:
                    from app.models.chat import ChatMessage
                    from datetime import datetime, timezone

                    ai_msg = ChatMessage(
                        conversation_id=conversation_id,
                        sender_id=None,
                        content=full_response,
                        source_language=chat_service.detect_language(full_response),
                        is_ai_response=True,
                    )
                    db.session.add(ai_msg)
                    db.session.commit()

                    # 触发 AI 消息的翻译
                    try:
                        chat_service._trigger_translation(
                            ai_msg.id,
                            ai_msg.source_language,
                            conversation_id,
                        )
                    except Exception as te:
                        logger.warning(f"AI 消息翻译触发失败: {te}")

                    # 发送完成事件
                    done_data = json.dumps({
                        'type': 'done',
                        'message_id': ai_msg.id,
                    }, ensure_ascii=False)
                    yield f'data: {done_data}\n\n'
                else:
                    done_data = json.dumps({'type': 'done'}, ensure_ascii=False)
                    yield f'data: {done_data}\n\n'

            except ImportError:
                logger.warning("chat_ai_service 尚未实现，返回占位响应")
                placeholder = 'AI 服务尚未就绪，请稍后再试。'
                full_response = placeholder
                event_data = json.dumps({'type': 'content', 'text': placeholder}, ensure_ascii=False)
                yield f'data: {event_data}\n\n'

                done_data = json.dumps({'type': 'done'}, ensure_ascii=False)
                yield f'data: {done_data}\n\n'

            except Exception as e:
                logger.error(f"AI 流式响应失败: {e}", exc_info=True)
                error_data = json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)
                yield f'data: {error_data}\n\n'

        return Response(
            stream_with_context(generate()),
            content_type='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive',
            },
        )

    except Exception as e:
        logger.error(f"AI 流式接口异常: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500
