# -*- coding: utf-8 -*-
"""
聊天模块 - 视图层

提供聊天系统所需的 API 接口：
- 对话的 CRUD（私聊、群聊、AI 对话）
- 消息收发与已读标记
- 用户搜索（@提及）
- AI SSE 流式响应
"""
import copy
import json
import logging
import os
import re
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
# 表单交互 Schema 定义
# ---------------------------------------------------------------------------

FORM_SCHEMAS = {
    'create_customer': {
        'title': '新建客户', 'entity_type': 'customer', 'action': 'create',
        'context': '请补充以下客户信息：',
        'fields': [
            {'name': 'company_name', 'label': '企业名称', 'type': 'text', 'required': True},
            {'name': 'company_type', 'label': '企业类型', 'type': 'select', 'options_key': 'company_type', 'required': True},
            {'name': 'source', 'label': '来源', 'type': 'select', 'options_key': 'source', 'required': True},
            {'name': 'country', 'label': '国家', 'type': 'select', 'options_key': 'country', 'required': False},
            {'name': 'address', 'label': '地址', 'type': 'text', 'required': False},
            {'name': 'industry', 'label': '行业', 'type': 'select', 'options_key': 'industry', 'required': False},
            {'name': 'notes', 'label': '备注', 'type': 'textarea', 'required': False},
        ]
    },
    'edit_customer': {
        'title': '修改客户信息', 'entity_type': 'customer', 'action': 'edit',
        'context': '修改需要更新的字段：',
        'fields': [
            {'name': 'id', 'type': 'hidden'},
            {'name': 'company_name', 'label': '企业名称', 'type': 'text', 'required': False},
            {'name': 'company_type', 'label': '企业类型', 'type': 'select', 'options_key': 'company_type', 'required': False},
            {'name': 'source', 'label': '来源', 'type': 'select', 'options_key': 'source', 'required': False},
            {'name': 'country', 'label': '国家', 'type': 'select', 'options_key': 'country', 'required': False},
            {'name': 'address', 'label': '地址', 'type': 'text', 'required': False},
            {'name': 'industry', 'label': '行业', 'type': 'select', 'options_key': 'industry', 'required': False},
            {'name': 'notes', 'label': '备注', 'type': 'textarea', 'required': False},
        ]
    },
    'create_contact': {
        'title': '新建联系人', 'entity_type': 'contact', 'action': 'create',
        'context': '请补充联系人信息：',
        'fields': [
            {'name': 'company_id', 'type': 'hidden'},
            {'name': 'name', 'label': '姓名', 'type': 'text', 'required': True},
            {'name': 'department', 'label': '部门', 'type': 'text', 'required': False},
            {'name': 'position', 'label': '职位', 'type': 'text', 'required': False},
            {'name': 'phone', 'label': '电话', 'type': 'text', 'required': False},
            {'name': 'email', 'label': '邮箱', 'type': 'text', 'required': False},
            {'name': 'notes', 'label': '备注', 'type': 'textarea', 'required': False},
        ]
    },
    'edit_contact': {
        'title': '修改联系人', 'entity_type': 'contact', 'action': 'edit',
        'context': '修改需要更新的字段：',
        'fields': [
            {'name': 'id', 'type': 'hidden'},
            {'name': 'company_id', 'type': 'hidden'},
            {'name': 'name', 'label': '姓名', 'type': 'text', 'required': False},
            {'name': 'department', 'label': '部门', 'type': 'text', 'required': False},
            {'name': 'position', 'label': '职位', 'type': 'text', 'required': False},
            {'name': 'phone', 'label': '电话', 'type': 'text', 'required': False},
            {'name': 'email', 'label': '邮箱', 'type': 'text', 'required': False},
            {'name': 'notes', 'label': '备注', 'type': 'textarea', 'required': False},
        ]
    },
    'create_project': {
        'title': '新建项目', 'entity_type': 'project', 'action': 'create',
        'context': '请补充项目信息：',
        'fields': [
            {'name': 'project_name', 'label': '项目名称', 'type': 'text', 'required': True},
            {'name': 'project_type', 'label': '项目类型', 'type': 'select', 'options_key': 'project_type', 'required': True},
            {'name': 'report_source', 'label': '信息来源', 'type': 'select', 'options_key': 'report_source', 'required': True},
            {'name': 'report_time', 'label': '上报日期', 'type': 'date', 'required': True},
            {'name': 'industry', 'label': '行业', 'type': 'select', 'options_key': 'industry'},
            {'name': 'product_situation', 'label': '产品情况', 'type': 'select', 'options_key': 'product_situation'},
            {'name': 'delivery_forecast', 'label': '预计交付日期', 'type': 'date'},
            {'name': 'address', 'label': '地址', 'type': 'text'},
            {'name': 'stage_description', 'label': '阶段描述', 'type': 'textarea'},
        ]
    },
    'edit_project': {
        'title': '修改项目信息', 'entity_type': 'project', 'action': 'edit',
        'context': '修改需要更新的字段：',
        'fields': [
            {'name': 'id', 'type': 'hidden'},
            {'name': 'project_name', 'label': '项目名称', 'type': 'text'},
            {'name': 'project_type', 'label': '项目类型', 'type': 'select', 'options_key': 'project_type'},
            {'name': 'report_source', 'label': '信息来源', 'type': 'select', 'options_key': 'report_source'},
            {'name': 'industry', 'label': '行业', 'type': 'select', 'options_key': 'industry'},
            {'name': 'product_situation', 'label': '产品情况', 'type': 'select', 'options_key': 'product_situation'},
            {'name': 'delivery_forecast', 'label': '预计交付日期', 'type': 'date'},
            {'name': 'address', 'label': '地址', 'type': 'text'},
            {'name': 'stage_description', 'label': '阶段描述', 'type': 'textarea'},
        ]
    },
    'create_expense': {
        'title': '新建报销单', 'entity_type': 'expense', 'action': 'create',
        'context': '请填写报销信息：',
        'fields': [
            {'name': 'expense_category', 'label': '费用类别', 'type': 'select', 'options_key': 'expense_category', 'required': True},
            {'name': 'expense_date', 'label': '费用日期', 'type': 'date', 'required': True},
            {'name': 'description', 'label': '费用说明', 'type': 'text', 'required': True},
            {'name': 'invoice_amount', 'label': '金额', 'type': 'number', 'required': True},
            {'name': 'currency', 'label': '币种', 'type': 'select', 'options_key': 'currency'},
        ]
    },
    'create_action': {
        'title': '快速跟进记录', 'entity_type': 'action', 'action': 'create',
        'context': '请输入跟进信息：',
        'fields': [
            {'name': 'company_id', 'type': 'hidden'},
            {'name': 'contact_id', 'type': 'hidden'},
            {'name': 'communication', 'label': '跟进内容', 'type': 'textarea', 'required': True},
            {'name': 'date', 'label': '日期', 'type': 'date'},
        ]
    },
}

FORM_MARKER_RE = re.compile(r'\[\[FORM:(\w+)\|(\{.*?\})\]\]', re.DOTALL)
# [[CHOICES:action_key|名称1:ID1|名称2:ID2]] — action_key + 带ID的选项
CHOICES_MARKER_RE = re.compile(r'\[\[CHOICES:(.*?)\]\]', re.DOTALL)


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

        user_msg_id = user_msg_result.get('data', {}).get('id')

        # 2. 构建 SSE 流（OpenClaw 通过 sessionKey 自行管理对话上下文，无需传历史）
        def generate():
            full_response = ''
            ai_model = None
            ai_prompt_tokens = 0
            ai_completion_tokens = 0
            _form_marker_detected = False  # 检测到 [[FORM: 后停止向前端输出内容
            try:
                from app.services.chat_ai_service import get_ai_response_stream

                oc_session_id = f'pma-u{current_user.id}-conv-{conversation_id}'

                for chunk in get_ai_response_stream(content, current_user,
                                                    session_id=oc_session_id,
                                                    conversation_id=conversation_id):
                    chunk_type = chunk.get('type')
                    if chunk_type == 'content':
                        full_response += chunk.get('text', '')
                        # 检测到表单标记或选项标记开头后，停止向前端输出后续内容
                        if not _form_marker_detected and ('[[FORM:' in full_response or '[[CHOICES:' in full_response):
                            _form_marker_detected = True
                            continue  # 不再发送，标记及之后的内容由 done 阶段处理
                        if _form_marker_detected:
                            continue  # 标记后续内容不发给前端
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

                    # 检测并处理表单标记 [[FORM:action|{json}]]
                    form_schema_event = None
                    form_match = FORM_MARKER_RE.search(full_response)
                    if form_match:
                        try:
                            action_key = form_match.group(1)
                            prefill = json.loads(form_match.group(2))
                            if action_key in FORM_SCHEMAS:
                                schema = copy.deepcopy(FORM_SCHEMAS[action_key])
                                # edit_customer: 从数据库加载现有数据作为 prefill 底层
                                if action_key == 'edit_customer' and prefill.get('id'):
                                    try:
                                        from app.models.customer import Company
                                        company = Company.query.get(int(prefill['id']))
                                        if company:
                                            db_data = {
                                                'company_name': company.company_name or '',
                                                'company_type': company.company_type or '',
                                                'source': company.source or '',
                                                'country': company.country or '',
                                                'address': company.address or '',
                                                'industry': company.industry or '',
                                                'notes': company.notes or '',
                                            }
                                            # AI prefill 覆盖数据库值（AI 提供的是用户想改的）
                                            db_data.update(prefill)
                                            prefill = db_data
                                    except Exception as e:
                                        logger.warning(f"加载客户现有数据失败: {e}")
                                # edit_contact: 从数据库加载现有联系人数据
                                if action_key == 'edit_contact' and prefill.get('id'):
                                    try:
                                        from app.models.customer import Contact
                                        contact = Contact.query.get(int(prefill['id']))
                                        if contact:
                                            db_data = {
                                                'name': contact.name or '',
                                                'department': contact.department or '',
                                                'position': contact.position or '',
                                                'phone': contact.phone or '',
                                                'email': contact.email or '',
                                                'notes': contact.notes or '',
                                                'company_id': contact.company_id,
                                            }
                                            db_data.update(prefill)
                                            prefill = db_data
                                    except Exception as e:
                                        logger.warning(f"加载联系人现有数据失败: {e}")
                                # edit_project: 从数据库加载现有项目数据
                                if action_key == 'edit_project' and prefill.get('id'):
                                    try:
                                        from app.models.project import Project
                                        from datetime import date
                                        project = Project.query.get(int(prefill['id']))
                                        if project:
                                            db_data = {}
                                            for field in schema['fields']:
                                                fname = field['name']
                                                if fname != 'id' and hasattr(project, fname):
                                                    val = getattr(project, fname)
                                                    if isinstance(val, date):
                                                        val = val.isoformat()
                                                    if val is not None:
                                                        db_data[fname] = str(val) if not isinstance(val, str) else val
                                            db_data.update(prefill)
                                            prefill = db_data
                                    except Exception as e:
                                        logger.warning(f"加载项目现有数据失败: {e}")
                                # create_action: 查出所属客户名称
                                if action_key == 'create_action' and prefill.get('company_id'):
                                    try:
                                        from app.models.customer import Company
                                        company = Company.query.get(int(prefill['company_id']))
                                        if company:
                                            schema['company_name'] = company.company_name
                                    except Exception as e:
                                        logger.warning(f"查询跟进记录所属客户失败: {e}")
                                # create_contact / edit_contact: 查出所属客户名称
                                if action_key in ('create_contact', 'edit_contact') and prefill.get('company_id'):
                                    try:
                                        from app.models.customer import Company
                                        company = Company.query.get(int(prefill['company_id']))
                                        if company:
                                            schema['company_name'] = company.company_name
                                    except Exception as e:
                                        logger.warning(f"查询联系人所属客户失败: {e}")
                                for field in schema['fields']:
                                    if field['name'] in prefill:
                                        field['prefill'] = prefill[field['name']]
                                form_schema_event = json.dumps({
                                    'type': 'form_request',
                                    'form_schema': schema,
                                }, ensure_ascii=False)
                            # 剥离标记后保存纯文本
                            full_response = FORM_MARKER_RE.sub('', full_response).strip()
                        except (json.JSONDecodeError, KeyError) as fe:
                            logger.warning(f"表单标记解析失败: {fe}")

                    # 检测并处理选项标记 [[CHOICES:action_key|名称1:ID1|名称2:ID2]]
                    choices_event = None
                    choices_match = CHOICES_MARKER_RE.search(full_response)
                    if choices_match:
                        try:
                            raw = choices_match.group(1)
                            parts = [p.strip() for p in raw.split('|') if p.strip()]
                            if parts:
                                action_key = parts[0] if parts[0] in FORM_SCHEMAS else None
                                option_list = []
                                for p in (parts[1:] if action_key else parts):
                                    if ':' in p:
                                        label, eid = p.rsplit(':', 1)
                                        option_list.append({'label': label.strip(), 'id': eid.strip()})
                                    else:
                                        option_list.append({'label': p})
                                if option_list:
                                    evt = {'type': 'choices', 'options': option_list}
                                    if action_key:
                                        evt['action_key'] = action_key
                                    choices_event = json.dumps(evt, ensure_ascii=False)
                            full_response = CHOICES_MARKER_RE.sub('', full_response).strip()
                        except Exception as ce:
                            logger.warning(f"选项标记解析失败: {ce}")

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
                        'ai_model': ai_model,
                    }, ensure_ascii=False)
                    yield f'data: {done_data}\n\n'

                    # 发送表单请求事件（在 done 之后，确保前端已处理完消息）
                    if form_schema_event:
                        yield f'data: {form_schema_event}\n\n'

                    # 发送选项事件（供用户点击快捷选择）
                    if choices_event:
                        yield f'data: {choices_event}\n\n'

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


# ---------------------------------------------------------------------------
# 17. 表单选项 API
# ---------------------------------------------------------------------------

@chat.route('/api/forms/options', methods=['GET'])
@login_required
def form_options():
    """返回表单下拉选项"""
    try:
        from app.utils.dictionary_helpers import (
            get_company_type_options,
            get_report_source_options,
            get_industry_options,
            get_project_type_options,
            get_product_situation_options,
            get_currency_type_options,
            get_country_options,
        )
        from app.models.expense import EXPENSE_CATEGORIES
        return jsonify({
            'success': True,
            'data': {
                'company_type': [{'value': k, 'label': v} for k, v in get_company_type_options()],
                'source': [{'value': k, 'label': v} for k, v in get_report_source_options()],
                'industry': [{'value': k, 'label': v} for k, v in get_industry_options()],
                'project_type': [{'value': k, 'label': v} for k, v in get_project_type_options()],
                'report_source': [{'value': k, 'label': v} for k, v in get_report_source_options()],
                'product_situation': [{'value': k, 'label': v} for k, v in get_product_situation_options()],
                'expense_category': [{'value': k, 'label': v} for k, v in EXPENSE_CATEGORIES],
                'currency': [{'value': k, 'label': v} for k, v in get_currency_type_options()],
                'country': [{'value': k, 'label': v} for k, v in get_country_options()],
            }
        })
    except Exception as e:
        logger.error(f"获取表单选项失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@chat.route('/api/forms/prefill', methods=['POST'])
@login_required
def form_prefill():
    """根据 action_key + entity_id 返回预填充的表单 schema（用于选项点击直达）"""
    try:
        data = request.get_json() or {}
        action_key = data.get('action_key', '')
        entity_id = data.get('entity_id')

        if action_key not in FORM_SCHEMAS:
            return jsonify({'success': False, 'message': f'未知表单类型: {action_key}'}), 400

        schema = copy.deepcopy(FORM_SCHEMAS[action_key])
        prefill = {'id': entity_id} if entity_id else {}

        # 复用 SSE 流中的 DB prefill 逻辑
        if action_key == 'edit_customer' and entity_id:
            from app.models.customer import Company
            company = Company.query.get(int(entity_id))
            if not company:
                return jsonify({'success': False, 'message': '未找到该客户'}), 404
            prefill.update({
                'company_name': company.company_name or '',
                'company_type': company.company_type or '',
                'source': company.source or '',
                'country': company.country or '',
                'address': company.address or '',
                'industry': company.industry or '',
                'notes': company.notes or '',
            })
        elif action_key == 'edit_contact' and entity_id:
            from app.models.customer import Contact
            contact = Contact.query.get(int(entity_id))
            if not contact:
                return jsonify({'success': False, 'message': '未找到该联系人'}), 404
            prefill.update({
                'name': contact.name or '',
                'department': contact.department or '',
                'position': contact.position or '',
                'phone': contact.phone or '',
                'email': contact.email or '',
                'notes': contact.notes or '',
                'company_id': contact.company_id,
            })
            if contact.company_id:
                from app.models.customer import Company
                company = Company.query.get(contact.company_id)
                if company:
                    schema['company_name'] = company.company_name
        elif action_key == 'edit_project' and entity_id:
            from app.models.project import Project
            from datetime import date
            project = Project.query.get(int(entity_id))
            if not project:
                return jsonify({'success': False, 'message': '未找到该项目'}), 404
            for field in schema['fields']:
                fname = field['name']
                if fname != 'id' and hasattr(project, fname):
                    val = getattr(project, fname)
                    if isinstance(val, date):
                        val = val.isoformat()
                    if val is not None:
                        prefill[fname] = str(val) if not isinstance(val, str) else val

        for field in schema['fields']:
            if field['name'] in prefill:
                field['prefill'] = prefill[field['name']]

        return jsonify({'success': True, 'form_schema': schema})
    except Exception as e:
        logger.error(f"表单预填充失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


# ---------------------------------------------------------------------------
# 18. 表单提交 API
# ---------------------------------------------------------------------------

@chat.route('/api/forms/submit', methods=['POST'])
@login_required
def form_submit():
    """统一表单提交端点"""
    try:
        data = request.get_json() or {}
        entity_type = data.get('entity_type')
        action = data.get('action')
        conversation_id = data.get('conversation_id')
        form_data = data.get('form_data', {})
        entity_id = data.get('entity_id')

        if entity_type == 'customer' and action == 'create':
            return _handle_create_customer(form_data, conversation_id, current_user)
        elif entity_type == 'customer' and action == 'edit':
            if not entity_id:
                return jsonify({'success': False, 'message': '缺少 entity_id'}), 400
            return _handle_edit_customer(entity_id, form_data, conversation_id, current_user)
        elif entity_type == 'contact' and action == 'create':
            return _handle_create_contact(form_data, conversation_id, current_user)
        elif entity_type == 'contact' and action == 'edit':
            return _handle_edit_contact(entity_id, form_data, conversation_id, current_user)
        elif entity_type == 'project' and action == 'create':
            return _handle_create_project(form_data, conversation_id, current_user)
        elif entity_type == 'project' and action == 'edit':
            if not entity_id:
                return jsonify({'success': False, 'message': '缺少 entity_id'}), 400
            return _handle_edit_project(entity_id, form_data, conversation_id, current_user)
        elif entity_type == 'expense' and action == 'create':
            return _handle_create_expense(form_data, conversation_id, current_user)
        elif entity_type == 'action' and action == 'create':
            return _handle_create_action(form_data, conversation_id, current_user)
        else:
            return jsonify({'success': False, 'message': f'不支持的操作: {entity_type}/{action}'}), 400

    except Exception as e:
        logger.error(f"表单提交失败: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


def _handle_create_customer(form_data, conversation_id, user):
    """处理创建客户表单"""
    from app.models.customer import Company
    from app.permissions import has_permission

    if not has_permission('customer', 'create'):
        return jsonify({'success': False, 'message': '没有创建客户的权限'}), 403

    company_name = (form_data.get('company_name') or '').strip()
    company_type = (form_data.get('company_type') or '').strip()
    source = (form_data.get('source') or '').strip()

    if not company_name:
        return jsonify({'success': False, 'message': '企业名称不能为空'}), 400
    if not company_type:
        return jsonify({'success': False, 'message': '企业类型不能为空'}), 400
    if not source:
        return jsonify({'success': False, 'message': '来源不能为空'}), 400

    company = Company(
        company_name=company_name,
        company_type=company_type,
        source=source,
        country=form_data.get('country', ''),
        address=form_data.get('address', ''),
        industry=form_data.get('industry', ''),
        notes=form_data.get('notes', ''),
        owner_id=user.id,
        status='active',
    )
    db.session.add(company)
    db.session.flush()  # 获取 ID

    # 创建 form_result_card 消息
    if conversation_id:
        _save_form_result_card(conversation_id, 'customer', 'create', company.id, company_name)

    db.session.commit()

    return jsonify({
        'success': True,
        'data': {
            'entity_type': 'customer',
            'entity_id': company.id,
            'entity_name': company_name,
        }
    })


def _handle_edit_customer(entity_id, form_data, conversation_id, user):
    """处理修改客户表单"""
    from app.models.customer import Company
    from app.utils.access_control import can_view_company

    company = Company.query.filter_by(id=entity_id, is_deleted=False).first()
    if not company:
        return jsonify({'success': False, 'message': '客户不存在'}), 404
    if not can_view_company(user, company):
        return jsonify({'success': False, 'message': '没有权限修改此客户'}), 403

    # 只更新用户填了的字段
    updatable = ['company_name', 'company_type', 'source', 'country', 'address', 'industry', 'notes']
    for field in updatable:
        val = form_data.get(field)
        if val is not None and str(val).strip():
            setattr(company, field, str(val).strip())

    if conversation_id:
        _save_form_result_card(conversation_id, 'customer', 'edit', company.id, company.company_name)

    db.session.commit()

    return jsonify({
        'success': True,
        'data': {
            'entity_type': 'customer',
            'entity_id': company.id,
            'entity_name': company.company_name,
        }
    })


def _handle_create_contact(form_data, conversation_id, user):
    """处理创建联系人表单"""
    from app.models.customer import Company, Contact
    from app.utils.access_control import can_view_company

    company_id = form_data.get('company_id')
    if not company_id:
        return jsonify({'success': False, 'message': '缺少 company_id'}), 400

    company = Company.query.filter_by(id=company_id, is_deleted=False).first()
    if not company:
        return jsonify({'success': False, 'message': '客户公司不存在'}), 404
    if not can_view_company(user, company):
        return jsonify({'success': False, 'message': '没有权限操作此客户'}), 403

    name = (form_data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': '联系人姓名不能为空'}), 400

    contact = Contact(
        company_id=company_id,
        name=name,
        department=form_data.get('department', ''),
        position=form_data.get('position', ''),
        phone=form_data.get('phone', ''),
        email=form_data.get('email', ''),
        notes=form_data.get('notes', ''),
        owner_id=user.id,
    )
    db.session.add(contact)
    db.session.flush()

    if conversation_id:
        _save_form_result_card(
            conversation_id, 'contact', 'create', contact.id,
            f'{name} ({company.company_name})',
        )

    db.session.commit()

    return jsonify({
        'success': True,
        'data': {
            'entity_type': 'contact',
            'entity_id': contact.id,
            'entity_name': name,
            'company_id': company_id,
            'company_name': company.company_name,
        }
    })


def _handle_edit_contact(entity_id, form_data, conversation_id, user):
    """处理修改联系人表单"""
    from app.models.customer import Company, Contact
    from app.utils.access_control import can_view_company

    contact = Contact.query.get(entity_id)
    if not contact:
        return jsonify({'success': False, 'message': '联系人不存在'}), 404

    company = Company.query.get(contact.company_id)
    if company and not can_view_company(user, company):
        return jsonify({'success': False, 'message': '没有权限修改此联系人'}), 403

    updatable = ['name', 'department', 'position', 'phone', 'email', 'notes']
    for field in updatable:
        val = form_data.get(field)
        if val is not None and str(val).strip():
            setattr(contact, field, str(val).strip())

    if conversation_id:
        company_name = company.company_name if company else ''
        _save_form_result_card(
            conversation_id, 'contact', 'edit', contact.id,
            f'{contact.name} ({company_name})',
        )

    db.session.commit()

    return jsonify({
        'success': True,
        'data': {
            'entity_type': 'contact',
            'entity_id': contact.id,
            'entity_name': contact.name,
            'company_id': contact.company_id,
            'company_name': company.company_name if company else '',
        }
    })


def _handle_create_project(form_data, conversation_id, user):
    """处理创建项目表单"""
    from app.models.project import Project
    from app.permissions import has_permission
    from datetime import date

    if not has_permission('project', 'create'):
        return jsonify({'success': False, 'message': '没有创建项目的权限'}), 403

    project_name = (form_data.get('project_name') or '').strip()
    project_type = (form_data.get('project_type') or '').strip()
    report_source = (form_data.get('report_source') or '').strip()
    report_time_str = (form_data.get('report_time') or '').strip()

    if not project_name:
        return jsonify({'success': False, 'message': '项目名称不能为空'}), 400
    if not project_type:
        return jsonify({'success': False, 'message': '项目类型不能为空'}), 400
    if not report_source:
        return jsonify({'success': False, 'message': '信息来源不能为空'}), 400
    if not report_time_str:
        return jsonify({'success': False, 'message': '上报日期不能为空'}), 400

    # 重名检查
    existing = Project.query.filter_by(project_name=project_name).first()
    if existing:
        return jsonify({'success': False, 'message': f'项目名称 "{project_name}" 已存在'}), 400

    # 解析日期
    try:
        report_time = date.fromisoformat(report_time_str)
    except ValueError:
        return jsonify({'success': False, 'message': '上报日期格式无效'}), 400

    delivery_forecast = None
    df_str = (form_data.get('delivery_forecast') or '').strip()
    if df_str:
        try:
            delivery_forecast = date.fromisoformat(df_str)
        except ValueError:
            pass

    # 如果当前用户是厂商账户，自动设置为厂商负责人
    vendor_sales_manager_id = None
    if user.is_vendor_user():
        vendor_sales_manager_id = user.id

    project = Project(
        project_name=project_name,
        project_type=project_type,
        report_source=report_source,
        report_time=report_time,
        industry=form_data.get('industry', ''),
        product_situation=form_data.get('product_situation', ''),
        delivery_forecast=delivery_forecast,
        address=form_data.get('address', ''),
        stage_description=form_data.get('stage_description', ''),
        current_stage='discover',
        status='draft',
        owner_id=user.id,
        created_by=user.id,
        vendor_sales_manager_id=vendor_sales_manager_id,
    )
    db.session.add(project)
    db.session.flush()

    if conversation_id:
        _save_form_result_card(conversation_id, 'project', 'create', project.id, project_name)

    db.session.commit()

    return jsonify({
        'success': True,
        'data': {
            'entity_type': 'project',
            'entity_id': project.id,
            'entity_name': project_name,
        }
    })


def _handle_edit_project(entity_id, form_data, conversation_id, user):
    """处理修改项目表单"""
    from app.models.project import Project
    from app.utils.access_control import get_viewable_data
    from datetime import date

    project = Project.query.get(entity_id)
    if not project:
        return jsonify({'success': False, 'message': '项目不存在'}), 404

    # 权限验证：确认用户能查看此项目
    viewable = get_viewable_data(Project, user, [Project.id == entity_id])
    if not viewable.first():
        return jsonify({'success': False, 'message': '没有权限修改此项目'}), 403

    updatable_text = ['project_name', 'project_type', 'report_source', 'industry',
                      'product_situation', 'address', 'stage_description']
    for field in updatable_text:
        val = form_data.get(field)
        if val is not None and str(val).strip():
            setattr(project, field, str(val).strip())

    # 日期字段单独处理
    for date_field in ['delivery_forecast']:
        val = (form_data.get(date_field) or '').strip()
        if val:
            try:
                setattr(project, date_field, date.fromisoformat(val))
            except ValueError:
                pass

    if conversation_id:
        _save_form_result_card(conversation_id, 'project', 'edit', project.id, project.project_name)

    db.session.commit()

    return jsonify({
        'success': True,
        'data': {
            'entity_type': 'project',
            'entity_id': project.id,
            'entity_name': project.project_name,
        }
    })


def _handle_create_expense(form_data, conversation_id, user):
    """处理创建报销单表单（简化版：不关联客户模式）"""
    from app.models.expense import Expense, ExpenseDetail
    from app.permissions import has_permission
    from datetime import date, datetime, timezone

    if not has_permission('expense', 'create'):
        return jsonify({'success': False, 'message': '没有创建报销单的权限'}), 403

    expense_category = (form_data.get('expense_category') or '').strip()
    expense_date_str = (form_data.get('expense_date') or '').strip()
    description = (form_data.get('description') or '').strip()
    invoice_amount_str = (form_data.get('invoice_amount') or '').strip()

    if not expense_category:
        return jsonify({'success': False, 'message': '费用类别不能为空'}), 400
    if not expense_date_str:
        return jsonify({'success': False, 'message': '费用日期不能为空'}), 400
    if not description:
        return jsonify({'success': False, 'message': '费用说明不能为空'}), 400
    if not invoice_amount_str:
        return jsonify({'success': False, 'message': '金额不能为空'}), 400

    try:
        invoice_amount = float(invoice_amount_str)
    except ValueError:
        return jsonify({'success': False, 'message': '金额格式无效'}), 400
    if invoice_amount <= 0:
        return jsonify({'success': False, 'message': '金额必须大于0'}), 400

    try:
        expense_date = date.fromisoformat(expense_date_str)
    except ValueError:
        return jsonify({'success': False, 'message': '费用日期格式无效'}), 400

    currency = (form_data.get('currency') or 'CNY').strip()
    user_name = getattr(user, 'real_name', None) or getattr(user, 'username', '') or ''
    desc_prefix = description[:10] if len(description) > 10 else description
    timestamp = datetime.now().strftime('%m%d%H%M')
    title = f'不关联（{desc_prefix}）-{user_name}-{timestamp}'

    expense = Expense(
        title=title,
        owner_id=user.id,
        description=description,
        currency=currency,
        total_amount=invoice_amount,
        status='draft',
    )
    db.session.add(expense)
    db.session.flush()

    detail = ExpenseDetail(
        expense_id=expense.id,
        expense_date=expense_date,
        expense_category=expense_category,
        description=description,
        invoice_amount=invoice_amount,
        current_amount=invoice_amount,
        currency=currency,
        exchange_rate=1.0,
    )
    db.session.add(detail)

    if conversation_id:
        _save_form_result_card(conversation_id, 'expense', 'create', expense.id, title)

    db.session.commit()

    return jsonify({
        'success': True,
        'data': {
            'entity_type': 'expense',
            'entity_id': expense.id,
            'entity_name': title,
        }
    })


def _handle_create_action(form_data, conversation_id, user):
    """处理创建跟进记录表单"""
    from app.models.action import Action
    from app.models.customer import Company, Contact
    from app.utils.access_control import can_view_company
    from datetime import date

    company_id = form_data.get('company_id')
    contact_id = form_data.get('contact_id')
    communication = (form_data.get('communication') or '').strip()

    if not company_id:
        return jsonify({'success': False, 'message': '缺少 company_id'}), 400
    if not contact_id:
        return jsonify({'success': False, 'message': '缺少 contact_id'}), 400
    if not communication:
        return jsonify({'success': False, 'message': '跟进内容不能为空'}), 400

    company = Company.query.filter_by(id=int(company_id), is_deleted=False).first()
    if not company:
        return jsonify({'success': False, 'message': '客户不存在'}), 404
    if not can_view_company(user, company):
        return jsonify({'success': False, 'message': '没有权限操作此客户'}), 403

    contact = Contact.query.get(int(contact_id))
    if not contact or contact.company_id != int(company_id):
        return jsonify({'success': False, 'message': '联系人不存在或不属于该客户'}), 400

    # 日期：用户提供或默认今天
    action_date_str = (form_data.get('date') or '').strip()
    if action_date_str:
        try:
            action_date = date.fromisoformat(action_date_str)
        except ValueError:
            action_date = date.today()
    else:
        action_date = date.today()

    action = Action(
        date=action_date,
        communication=communication,
        owner_id=user.id,
        company_id=int(company_id),
        contact_id=int(contact_id),
        is_shared=True,
    )
    db.session.add(action)
    db.session.flush()

    if conversation_id:
        _save_form_result_card(
            conversation_id, 'action', 'create', action.id,
            f'{contact.name} ({company.company_name})',
        )

    db.session.commit()

    return jsonify({
        'success': True,
        'data': {
            'entity_type': 'action',
            'entity_id': action.id,
            'entity_name': contact.name,
            'company_id': int(company_id),
            'company_name': company.company_name,
        }
    })


def _save_form_result_card(conversation_id, entity_type, action, entity_id, entity_name):
    """保存 form_result_card 消息到对话"""
    from datetime import datetime, timezone

    card_data = json.dumps({
        'entity_type': entity_type,
        'action': action,
        'entity_id': entity_id,
        'entity_name': entity_name,
    }, ensure_ascii=False)

    msg = ChatMessage(
        conversation_id=conversation_id,
        sender_id=None,
        content=card_data,
        message_type='form_result_card',
        is_ai_response=True,
        source_language='zh',
    )
    db.session.add(msg)

    conv = ChatConversation.query.get(conversation_id)
    if conv:
        conv.updated_at = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# 19. AI 文件上传 API（供 OpenClaw 等外部 AI 上传生成的文件到聊天）
# ---------------------------------------------------------------------------

@chat.route('/api/ai/upload-file', methods=['POST'])
@_require_ai_token
def ai_upload_file():
    """供 OpenClaw 调用的文件上传 API（token 认证）

    AI 生成文件后，通过此接口上传到对应聊天对话，用户即可直接下载。

    请求: multipart/form-data
        - file: 文件
        - conversation_id: 对话 ID
        - user_id: 发起请求的用户 ID
    """
    try:
        conversation_id = request.form.get('conversation_id', type=int)
        user_id = request.form.get('user_id', type=int)

        if not conversation_id:
            return jsonify({'success': False, 'error': 'conversation_id 不能为空'}), 400
        if not user_id:
            return jsonify({'success': False, 'error': 'user_id 不能为空'}), 400

        file = request.files.get('file')
        if not file or not file.filename:
            return jsonify({'success': False, 'error': '请提供文件'}), 400

        # 验证用户存在
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': f'用户 {user_id} 不存在'}), 404

        # 验证对话存在
        conv = ChatConversation.query.get(conversation_id)
        if not conv:
            return jsonify({'success': False, 'error': f'对话 {conversation_id} 不存在'}), 404

        # 验证用户是对话参与者
        participant = ChatParticipant.query.filter_by(
            conversation_id=conversation_id, user_id=user_id
        ).first()
        if not participant:
            return jsonify({'success': False, 'error': '用户不是该对话的参与者'}), 403

        # 文件大小检查 (50MB)
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
        if file_size > 50 * 1024 * 1024:
            return jsonify({'success': False, 'error': '文件大小不能超过 50MB'}), 400

        # 检测文件类型
        filename = file.filename
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        image_exts = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg'}
        video_exts = {'mp4', 'mov', 'avi', 'webm', 'mkv'}
        if ext in image_exts:
            message_type = 'image'
            storage_file_type = 'image'
        elif ext in video_exts:
            message_type = 'video'
            storage_file_type = 'video'
        else:
            message_type = 'file'
            storage_file_type = 'attachment'

        # 生成唯一文件名
        unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"

        # 上传到 NAS
        file_url = None
        try:
            from app.utils.smart_storage_manager import get_smart_storage
            smart_storage = get_smart_storage()
            result = smart_storage.upload_file(
                object_id=conversation_id,
                file=file,
                filename=unique_name,
                file_type=storage_file_type,
                bucket_type='chat',
                business_type='chat'
            )
            if result:
                file_url = result.get('storage_path', '')
        except Exception as ue:
            logger.warning(f"AI 文件上传 SmartStorage 失败，尝试本地回退: {ue}")

        # 本地回退
        if not file_url:
            local_dir = os.path.join('.', 'storage', 'chat_files', str(conversation_id))
            os.makedirs(local_dir, exist_ok=True)
            local_path = os.path.join(local_dir, unique_name)
            file.seek(0)
            with open(local_path, 'wb') as f:
                f.write(file.read())
            file_url = f"chat_files/{conversation_id}/{unique_name}"
            logger.info(f"AI 文件本地保存: {local_path}")

        # 创建 AI 文件消息（sender_id=None 表示 AI 发送）
        from datetime import datetime, timezone
        msg = ChatMessage(
            conversation_id=conversation_id,
            sender_id=None,
            content=None,
            message_type=message_type,
            file_url=file_url,
            file_name=filename,
            file_size=file_size,
            is_ai_response=True,
            source_language=chat_service.detect_language(filename),
        )
        db.session.add(msg)

        # 更新对话 updated_at
        conv.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        # 构建下载 URL
        external_url = os.environ.get('EXTERNAL_URL', '').rstrip('/')
        download_url = f"{external_url}/storage/chat/{file_url}" if external_url else ''

        logger.info(f"AI 文件上传成功: {filename} -> 对话 {conversation_id}")
        return jsonify({
            'success': True,
            'data': {
                'message_id': msg.id,
                'file_name': filename,
                'file_size': file_size,
                'file_url': file_url,
                'download_url': download_url,
                'message_type': message_type,
            }
        })

    except Exception as e:
        logger.error(f"AI 文件上传异常: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
