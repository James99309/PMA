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
import os
import uuid
from functools import wraps

from flask import Blueprint, jsonify, request, Response, stream_with_context
from flask_login import login_required, current_user

from app import db
from app.models.user import User
from app.models.chat import ChatConversation, ChatMessage, ChatParticipant
from app.services import chat_service

logger = logging.getLogger(__name__)

chat = Blueprint('chat', __name__, url_prefix='/chat')


# ---------------------------------------------------------------------------
# Bearer token 认证装饰器（供 AI 外部调用 API 使用）
# ---------------------------------------------------------------------------

def _require_ai_token(f):
    """验证 Authorization: Bearer <PMA_AI_QUERY_TOKEN>"""
    @wraps(f)
    def decorated(*args, **kwargs):
        expected = os.environ.get('PMA_AI_QUERY_TOKEN', '')
        if not expected:
            return jsonify({'success': False, 'message': 'PMA_AI_QUERY_TOKEN 未配置'}), 500

        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'message': '缺少 Authorization 头'}), 401

        token = auth_header[7:]
        if token != expected:
            return jsonify({'success': False, 'message': '无效的 token'}), 401

        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# 1. 对话列表
# ---------------------------------------------------------------------------

@chat.route('/api/conversations', methods=['GET'])
@login_required
def get_conversations():
    """获取当前用户的所有对话列表"""
    try:
        viewer_lang = getattr(current_user, 'language_preference', None) or 'zh'
        result = chat_service.get_user_conversations(current_user.id, viewer_language=viewer_lang)
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
        reply_to_id = data.get('reply_to_id')

        if not content:
            return jsonify({'success': False, 'message': '消息内容不能为空'}), 400

        result = chat_service.send_message(
            conversation_id=id,
            sender_id=current_user.id,
            content=content,
            reply_to_id=reply_to_id,
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
# 8. 删除对话
# ---------------------------------------------------------------------------

@chat.route('/api/conversations/<int:id>', methods=['DELETE'])
@login_required
def delete_conversation_api(id):
    """软删除对话"""
    try:
        result = chat_service.delete_conversation(id, current_user.id)
        status = 200 if result['success'] else 400
        return jsonify(result), status
    except Exception as e:
        logger.error(f"删除对话失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------------------------------------------------------------------------
# 9. 撤回消息
# ---------------------------------------------------------------------------

@chat.route('/api/messages/<int:id>/recall', methods=['POST'])
@login_required
def recall_message_api(id):
    """撤回消息（仅发送者，2分钟内）"""
    try:
        result = chat_service.recall_message(id, current_user.id)
        status = 200 if result['success'] else 400
        return jsonify(result), status
    except Exception as e:
        logger.error(f"撤回消息失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------------------------------------------------------------------------
# 9b. 转发消息
# ---------------------------------------------------------------------------

@chat.route('/api/messages/<int:id>/forward', methods=['POST'])
@login_required
def forward_message_api(id):
    """转发消息到一个或多个对话，也可直接转发给用户（自动创建私聊）"""
    try:
        data = request.get_json() or {}
        target_conversation_ids = list(data.get('conversation_ids', []))
        user_ids = data.get('user_ids', [])
        note = data.get('note')

        # 为每个 user_id 找到或创建私聊对话
        for uid in user_ids:
            conv_result = chat_service.create_conversation(
                creator_id=current_user.id,
                participant_ids=[uid],
            )
            if conv_result.get('success') and conv_result.get('data', {}).get('id'):
                conv_id = conv_result['data']['id']
                if conv_id not in target_conversation_ids:
                    target_conversation_ids.append(conv_id)

        if not target_conversation_ids:
            return jsonify({'success': False, 'message': '请选择转发目标'}), 400

        result = chat_service.forward_message(
            message_id=id,
            sender_id=current_user.id,
            target_conversation_ids=target_conversation_ids,
            note=note,
        )
        status = 200 if result['success'] else 400
        return jsonify(result), status
    except Exception as e:
        logger.error(f"转发消息失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------------------------------------------------------------------------
# 10. 文件上传（附件消息）
# ---------------------------------------------------------------------------

@chat.route('/api/conversations/<int:id>/upload', methods=['POST'])
@login_required
def upload_attachment(id):
    """上传文件附件到对话中"""
    try:
        # 验证参与者
        participant = ChatParticipant.query.filter_by(
            conversation_id=id, user_id=current_user.id
        ).first()
        if not participant:
            return jsonify({'success': False, 'message': '您不是该对话的参与者'}), 403

        file = request.files.get('file')
        if not file or not file.filename:
            return jsonify({'success': False, 'message': '请选择文件'}), 400

        # 文件大小检查 (50MB)
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
        if file_size > 50 * 1024 * 1024:
            return jsonify({'success': False, 'message': '文件大小不能超过 50MB'}), 400

        # 检测文件类型
        filename = file.filename
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        image_exts = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg'}
        video_exts = {'mp4', 'mov', 'avi', 'webm', 'mkv'}
        if ext in image_exts:
            message_type = 'image'
        elif ext in video_exts:
            message_type = 'video'
        else:
            message_type = 'file'

        # 生成存储路径
        unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"

        # 根据消息类型选择正确的 file_type（本地存储回退时需要匹配扩展名校验）
        if message_type == 'image':
            storage_file_type = 'image'
        elif message_type == 'video':
            storage_file_type = 'video'
        else:
            storage_file_type = 'attachment'

        # 上传到 NAS
        file_url = None
        try:
            from app.utils.smart_storage_manager import get_smart_storage
            smart_storage = get_smart_storage()

            result = smart_storage.upload_file(
                object_id=id,
                file=file,
                filename=unique_name,
                file_type=storage_file_type,
                bucket_type='chat',
                business_type='chat'
            )
            if result:
                file_url = result.get('storage_path', '')
        except Exception as ue:
            logger.warning(f"SmartStorage 上传失败，尝试本地回退: {ue}")

        # 本地回退：直接写文件到 ./storage/chat_files/
        if not file_url:
            import os
            local_dir = os.path.join('.', 'storage', 'chat_files', str(id))
            os.makedirs(local_dir, exist_ok=True)
            local_path = os.path.join(local_dir, unique_name)
            file.seek(0)
            with open(local_path, 'wb') as f:
                f.write(file.read())
            file_url = f"chat_files/{id}/{unique_name}"
            logger.info(f"聊天附件本地保存: {local_path}")

        # 创建附件消息
        from datetime import datetime, timezone
        msg = ChatMessage(
            conversation_id=id,
            sender_id=current_user.id,
            content=None,
            message_type=message_type,
            file_url=file_url,
            file_name=filename,
            file_size=file_size,
            source_language=chat_service.detect_language(filename),
        )
        db.session.add(msg)
        db.session.commit()

        # 更新对话 updated_at
        from app.models.chat import ChatConversation
        conv = ChatConversation.query.get(id)
        if conv:
            conv.updated_at = datetime.now(timezone.utc)
            db.session.commit()

        return jsonify({
            'success': True,
            'data': msg.to_dict(),
        })

    except Exception as e:
        logger.error(f"上传附件失败: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------------------------------------------------------------------------
# 11. 用户搜索（@ 提及）
# ---------------------------------------------------------------------------

@chat.route('/api/users/search', methods=['GET'])
@login_required
def search_users():
    """搜索用户，用于 @ 提及功能"""
    try:
        q = request.args.get('q', '').strip()

        # 搜索活跃用户，排除当前用户
        query = User.query.filter(
            User._is_active == True,
            User.id != current_user.id,
        )
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
                'lang': u.language_preference or 'zh',
            })

        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"搜索用户失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------------------------------------------------------------------------
# 12. AI SSE 流式响应
# ---------------------------------------------------------------------------

@chat.route('/api/ai/stream', methods=['POST'])
@login_required
def ai_stream():
    """AI 对话的 SSE 流式响应"""
    try:
        data = request.get_json() or {}
        content = data.get('content', '').strip()
        conversation_id = data.get('conversation_id')
        provider = data.get('provider', 'deepseek')

        # 权限检查：非管理员强制使用 deepseek
        if provider == 'openclaw' and getattr(current_user, 'role', '') not in ('admin', 'ceo'):
            provider = 'deepseek'

        if not content:
            return jsonify({'success': False, 'message': '消息内容不能为空'}), 400

        if not conversation_id:
            # 创建新的 AI 对话
            ai_conv = chat_service.create_ai_conversation(current_user.id)
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

        # 2. 获取对话历史（最近 20 条）
        conversation_history = []
        try:
            recent_msgs = ChatMessage.query.filter_by(
                conversation_id=conversation_id
            ).order_by(ChatMessage.created_at.desc()).limit(20).all()

            # 按时间正序排列，排除刚发的那条用户消息
            recent_msgs.reverse()
            user_msg_id = user_msg_result.get('data', {}).get('id')
            for m in recent_msgs:
                if m.id == user_msg_id:
                    continue
                if m.is_ai_response:
                    conversation_history.append({'role': 'assistant', 'content': m.content or ''})
                else:
                    conversation_history.append({'role': 'user', 'content': m.content or ''})
        except Exception as he:
            logger.warning(f"获取对话历史失败: {he}")

        # 3. 构建 SSE 流
        def generate():
            full_response = ''
            ai_model = None
            ai_prompt_tokens = 0
            ai_completion_tokens = 0
            try:
                from app.services.chat_ai_service import get_ai_response_stream

                # OpenClaw 使用 conversation_id 作为 session_id 保持上下文
                oc_session_id = f'pma-conv-{conversation_id}' if provider == 'openclaw' else None

                for chunk in get_ai_response_stream(content, current_user, conversation_history,
                                                    provider=provider, session_id=oc_session_id):
                    chunk_type = chunk.get('type')
                    if chunk_type == 'content':
                        full_response += chunk.get('text', '')
                    elif chunk_type == 'done':
                        ai_model = chunk.get('model')
                        ai_prompt_tokens = chunk.get('prompt_tokens', 0)
                        ai_completion_tokens = chunk.get('completion_tokens', 0)
                        continue  # 不转发，等 DB 保存后发带 message_id 的 done
                    event_data = json.dumps(chunk, ensure_ascii=False)
                    yield f'data: {event_data}\n\n'

                # 4. 流结束后保存 AI 回复到数据库
                if full_response:
                    from datetime import datetime, timezone
                    from app.services.chat_ai_service import _clean_dsml
                    full_response = _clean_dsml(full_response)

                if full_response:
                    from datetime import datetime, timezone

                    ai_msg = ChatMessage(
                        conversation_id=conversation_id,
                        sender_id=None,
                        content=full_response,
                        source_language=chat_service.detect_language(full_response),
                        is_ai_response=True,
                        ai_model=ai_model,
                        ai_prompt_tokens=ai_prompt_tokens,
                        ai_completion_tokens=ai_completion_tokens,
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

                    # 发送完成事件（携带 user_message_id 供前端去重）
                    done_data = json.dumps({
                        'type': 'done',
                        'message_id': ai_msg.id,
                        'user_message_id': user_msg_id,
                        'conversation_id': conversation_id,
                    }, ensure_ascii=False)
                    yield f'data: {done_data}\n\n'

                    # 自动生成话题标题（仅首次，done 之后发送以确保前端对话对象已创建）
                    try:
                        conv_obj = ChatConversation.query.get(conversation_id)
                        if conv_obj and conv_obj.type == 'ai' and not conv_obj.topic:
                            from app.services.chat_ai_service import generate_conversation_topic
                            topic = generate_conversation_topic(content, full_response)
                            if topic:
                                conv_obj.topic = topic
                                db.session.commit()
                                topic_event = json.dumps({
                                    'type': 'topic_update',
                                    'topic': topic,
                                    'conversation_id': conversation_id,
                                }, ensure_ascii=False)
                                yield f'data: {topic_event}\n\n'
                    except Exception as te:
                        logger.warning(f"生成话题标题失败: {te}")
                else:
                    done_data = json.dumps({
                        'type': 'done',
                        'user_message_id': user_msg_id,
                        'conversation_id': conversation_id,
                    }, ensure_ascii=False)
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
                'Connection': 'close',
            },
        )

    except Exception as e:
        logger.error(f"AI 流式接口异常: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------------------------------------------------------------------------
# 13. 实体搜索 API（# 触发器）
# ---------------------------------------------------------------------------

@chat.route('/api/entity/companies', methods=['GET'])
@login_required
def search_entity_companies():
    """搜索客户公司（权限过滤），q 为空时返回最近客户"""
    keyword = request.args.get('q', '').strip()

    try:
        from app.models.customer import Company
        from app.utils.access_control import get_viewable_data

        filters = [Company.is_deleted == False]
        if keyword:
            filters.append(Company.company_name.ilike(f'%{keyword}%'))

        query = get_viewable_data(Company, current_user, filters)
        companies = query.order_by(Company.company_name).limit(20).all()

        return jsonify({'success': True, 'data': [{
            'id': c.id,
            'company_name': c.company_name,
            'country': c.country or '',
            'region': c.region or '',
        } for c in companies]})
    except Exception as e:
        logger.error(f"搜索客户公司失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@chat.route('/api/entity/companies/<int:company_id>/contacts', methods=['GET'])
@login_required
def get_entity_company_contacts(company_id):
    """获取公司联系人列表"""
    try:
        from app.models.customer import Company, Contact
        from app.utils.access_control import can_view_company

        company = Company.query.filter_by(id=company_id, is_deleted=False).first()
        if not company or not can_view_company(current_user, company):
            return jsonify({'success': False, 'message': '无权限'}), 403

        contacts = Contact.query.filter_by(company_id=company_id).all()
        return jsonify({'success': True, 'data': [{
            'id': ct.id,
            'name': ct.name,
            'position': ct.position or '',
        } for ct in contacts]})
    except Exception as e:
        logger.error(f"获取公司联系人失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@chat.route('/api/entity/projects', methods=['GET'])
@login_required
def search_entity_projects():
    """搜索项目（权限过滤），q 为空时返回最近项目"""
    keyword = request.args.get('q', '').strip()

    try:
        from app.models.project import Project
        from app.utils.access_control import get_viewable_data
        from app.utils.dictionary_helpers import project_stage_label

        filters = []
        if keyword:
            filters.append(Project.project_name.ilike(f'%{keyword}%'))

        query = get_viewable_data(Project, current_user, filters)
        projects = query.order_by(Project.created_at.desc()).limit(20).all()

        return jsonify({'success': True, 'data': [{
            'id': p.id,
            'project_name': p.project_name,
            'current_stage': project_stage_label(p.current_stage) if p.current_stage else '',
            'quotation_customer': p.quotation_customer or 0,
        } for p in projects]})
    except Exception as e:
        logger.error(f"搜索项目失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@chat.route('/api/entity/projects/<int:project_id>/quotations', methods=['GET'])
@login_required
def get_entity_project_quotations(project_id):
    """获取项目关联的报价单"""
    try:
        from app.models.project import Project
        from app.models.quotation import Quotation

        project = Project.query.get(project_id)
        if not project:
            return jsonify({'success': False, 'message': '项目不存在'}), 404

        quotations = Quotation.query.filter_by(project_id=project_id).order_by(
            Quotation.created_at.desc()
        ).all()

        return jsonify({'success': True, 'data': [{
            'id': q.id,
            'quotation_number': q.quotation_number,
            'amount': q.amount or 0,
            'approval_status': q.approval_status or '',
        } for q in quotations]})
    except Exception as e:
        logger.error(f"获取项目报价单失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------------------------------------------------------------------------
# 14. 发送卡片消息
# ---------------------------------------------------------------------------

@chat.route('/api/conversations/<int:conv_id>/card-message', methods=['POST'])
@login_required
def send_card_message_api(conv_id):
    """发送业务实体卡片消息"""
    try:
        data = request.get_json() or {}
        message_type = data.get('message_type')
        card_data = data.get('card_data')

        if message_type not in ('customer_card', 'project_card'):
            return jsonify({'success': False, 'message': '无效的卡片类型'}), 400
        if not card_data:
            return jsonify({'success': False, 'message': '卡片数据不能为空'}), 400

        result = chat_service.send_card_message(conv_id, current_user.id, message_type, card_data)
        if result.get('success'):
            return jsonify(result)
        return jsonify(result), 400
    except Exception as e:
        logger.error(f"发送卡片消息失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------------------------------------------------------------------------
# 15. AI 外部查询 API（供 OpenClaw 等外部 AI 调用）
# ---------------------------------------------------------------------------

@chat.route('/api/ai/db-query', methods=['POST'])
@_require_ai_token
def ai_db_query():
    """供 OpenClaw 调用的数据库查询 API（token 认证）

    请求体: {"sql": "SELECT ...", "user_id": 5}
    响应: execute_safe_query() 的返回格式
    """
    try:
        data = request.get_json() or {}
        sql = data.get('sql', '').strip()
        user_id = data.get('user_id')

        if not sql:
            return jsonify({'success': False, 'error': 'sql 不能为空'}), 400
        if not user_id:
            return jsonify({'success': False, 'error': 'user_id 不能为空'}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': f'用户 {user_id} 不存在'}), 404

        from app.services.chat_db_query import execute_safe_query
        result = execute_safe_query(sql, user)
        status = 200 if result.get('success') else 400
        return jsonify(result), status

    except Exception as e:
        logger.error(f"AI DB Query API 异常: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@chat.route('/api/ai/db-schema', methods=['GET'])
@_require_ai_token
def ai_db_schema():
    """返回数据库 schema 和用户权限上下文

    查询参数: ?user_id=5
    响应: {"success": true, "schema": "...", "permission_context": "..."}
    """
    try:
        user_id = request.args.get('user_id', type=int)
        if not user_id:
            return jsonify({'success': False, 'error': 'user_id 不能为空'}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': f'用户 {user_id} 不存在'}), 404

        from app.services.chat_db_query import get_db_schema, get_permission_context
        return jsonify({
            'success': True,
            'schema': get_db_schema(),
            'permission_context': get_permission_context(user),
        })

    except Exception as e:
        logger.error(f"AI DB Schema API 异常: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
