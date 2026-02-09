# -*- coding: utf-8 -*-
"""
公告管理视图
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.decorators import permission_required
from app.models.announcement import Announcement, AnnouncementRead, AnnouncementAttachment, get_local_time
from app.models.user import User
from app.utils.supabase_client import get_supabase_client
from app.utils.sharing import get_shareable_users_tree
from app.utils.permissions import get_accessible_users_by_permission_only
import logging

logger = logging.getLogger(__name__)

announcement_bp = Blueprint('announcement', __name__, url_prefix='/announcement')


# ========== 页面路由 ==========

@announcement_bp.route('/list')
@login_required
@permission_required('announcement', 'view')
def list_view():
    """公告列表页面（管理端）"""
    # 获取筛选参数
    status = request.args.get('status', '')
    announcement_type = request.args.get('type', '')
    search = request.args.get('search', '').strip()

    # 获取用户可访问的用户列表（基于权限级别）
    # 公告是系统管理类模块，不应受业务数据归属关系影响
    accessible_users = get_accessible_users_by_permission_only(current_user, 'announcement')
    accessible_user_ids = [u.id for u in accessible_users]

    # 构建查询 - 只显示可访问用户创建的公告
    query = Announcement.query.filter(
        Announcement.is_deleted == False,
        Announcement.created_by.in_(accessible_user_ids)
    )

    if status:
        query = query.filter(Announcement.status == status)
    if announcement_type:
        query = query.filter(Announcement.announcement_type == announcement_type)
    if search:
        query = query.filter(Announcement.title.ilike(f'%{search}%'))

    # 排序：最新的在前
    announcements = query.order_by(Announcement.created_at.desc()).all()

    # 统计数据 - 同样基于权限过滤
    base_query = Announcement.query.filter(
        Announcement.is_deleted == False,
        Announcement.created_by.in_(accessible_user_ids)
    )
    total_count = base_query.count()
    published_count = base_query.filter(Announcement.status == 'published').count()
    draft_count = total_count - published_count

    # 公告类型选项
    type_options = [
        {'value': 'system', 'label': '系统通知'},
        {'value': 'business', 'label': '业务公告'},
        {'value': 'urgent', 'label': '紧急通知'}
    ]

    # 状态选项
    status_options = [
        {'value': 'draft', 'label': '草稿'},
        {'value': 'published', 'label': '已发布'}
    ]

    # 获取用户树数据（用于用户选择器）
    shareable_users_tree = get_shareable_users_tree(current_user, 'announcement')

    return render_template(
        'announcement/tw_list.html',
        announcements=announcements,
        type_options=type_options,
        status_options=status_options,
        current_status=status,
        current_type=announcement_type,
        search=search,
        total_count=total_count,
        published_count=published_count,
        draft_count=draft_count,
        shareable_users_tree=shareable_users_tree
    )


# ========== API路由 ==========

@announcement_bp.route('/api/create', methods=['POST'])
@login_required
@permission_required('announcement', 'create')
def api_create():
    """创建公告API"""
    try:
        data = request.get_json()

        # 验证必填字段
        if not data.get('title'):
            return jsonify({'success': False, 'message': '请输入公告标题'}), 400
        if not data.get('content'):
            return jsonify({'success': False, 'message': '请输入公告内容'}), 400

        # 创建公告
        announcement = Announcement(
            title=data['title'],
            content=data['content'],
            announcement_type=data.get('announcement_type', 'system'),
            target_users=data.get('target_users', []),
            status='draft',
            created_by=current_user.id
        )

        db.session.add(announcement)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '公告创建成功',
            'data': {'id': announcement.id}
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"创建公告失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'创建失败: {str(e)}'}), 500


@announcement_bp.route('/api/update/<int:announcement_id>', methods=['POST'])
@login_required
@permission_required('announcement', 'edit')
def api_update(announcement_id):
    """更新公告API"""
    try:
        announcement = Announcement.query.get_or_404(announcement_id)

        # 检查是否可编辑
        if announcement.is_readonly:
            return jsonify({'success': False, 'message': '已发布的公告不可编辑'}), 400

        data = request.get_json()

        # 更新字段
        if 'title' in data:
            announcement.title = data['title']
        if 'content' in data:
            announcement.content = data['content']
        if 'announcement_type' in data:
            announcement.announcement_type = data['announcement_type']
        if 'target_users' in data:
            announcement.target_users = data['target_users']
        if 'scheduled_time' in data:
            from datetime import datetime
            if data['scheduled_time']:
                announcement.scheduled_time = datetime.fromisoformat(data['scheduled_time'])
            else:
                announcement.scheduled_time = None

        db.session.commit()

        return jsonify({'success': True, 'message': '公告更新成功'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"更新公告失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'}), 500


@announcement_bp.route('/api/publish/<int:announcement_id>', methods=['POST'])
@login_required
@permission_required('announcement', 'edit')
def api_publish(announcement_id):
    """发布公告API"""
    try:
        announcement = Announcement.query.get_or_404(announcement_id)

        if announcement.status == 'published':
            return jsonify({'success': False, 'message': '公告已发布'}), 400

        # 获取目标用户列表
        target_user_ids = announcement.target_users or []

        if not target_user_ids:
            return jsonify({'success': False, 'message': '请先选择发布对象'}), 400

        # 更新公告状态
        announcement.status = 'published'
        announcement.published_at = get_local_time()

        # 创建阅读记录
        for user_id in target_user_ids:
            read_record = AnnouncementRead(
                announcement_id=announcement.id,
                user_id=user_id,
                is_read=False
            )
            db.session.add(read_record)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'公告已发布，共通知{len(target_user_ids)}人'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"发布公告失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'发布失败: {str(e)}'}), 500


@announcement_bp.route('/api/delete/<int:announcement_id>', methods=['POST'])
@login_required
@permission_required('announcement', 'delete')
def api_delete(announcement_id):
    """删除公告API（软删除）"""
    try:
        announcement = Announcement.query.get_or_404(announcement_id)
        announcement.is_deleted = True
        db.session.commit()

        return jsonify({'success': True, 'message': '公告已删除'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"删除公告失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500


@announcement_bp.route('/api/get/<int:announcement_id>')
@login_required
def api_get(announcement_id):
    """获取公告详情API"""
    try:
        announcement = Announcement.query.get_or_404(announcement_id)

        if announcement.is_deleted:
            return jsonify({'success': False, 'message': '公告不存在'}), 404

        return jsonify({
            'success': True,
            'data': announcement.to_dict()
        })

    except Exception as e:
        logger.error(f"获取公告详情失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@announcement_bp.route('/api/upload_attachment/<int:announcement_id>', methods=['POST'])
@login_required
@permission_required('announcement', 'edit')
def api_upload_attachment(announcement_id):
    """上传附件API"""
    try:
        announcement = Announcement.query.get_or_404(announcement_id)

        if announcement.is_readonly:
            return jsonify({'success': False, 'message': '已发布的公告不可添加附件'}), 400

        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '未选择文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '未选择文件'}), 400

        # 验证文件类型
        allowed_extensions = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
                              'txt', 'zip', 'rar', 'jpg', 'jpeg', 'png', 'gif'}
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

        if file_ext not in allowed_extensions:
            return jsonify({'success': False, 'message': f'不支持的文件类型: {file_ext}'}), 400

        # 获取文件大小
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)

        # 使用智能存储（NAS 优先，Supabase 回退）
        from app.utils.smart_storage_manager import get_smart_storage

        smart_storage = get_smart_storage()

        result = smart_storage.upload_file(
            object_id=announcement_id,
            file=file,
            filename=file.filename,
            file_type='attachment',
            bucket_type='invoice',  # 复用 invoice bucket
            business_type='announcement'
        )

        if not result:
            return jsonify({'success': False, 'message': '文件上传失败'}), 500

        # 创建附件记录
        attachment = AnnouncementAttachment(
            announcement_id=announcement_id,
            filename=file.filename,
            storage_path=result.get('storage_path', ''),
            file_url=result['url'],
            file_size=file_size,
            file_type=file_ext
        )

        db.session.add(attachment)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '附件上传成功',
            'data': attachment.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"上传附件失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'上传失败: {str(e)}'}), 500


@announcement_bp.route('/api/delete_attachment/<int:attachment_id>', methods=['POST'])
@login_required
@permission_required('announcement', 'edit')
def api_delete_attachment(attachment_id):
    """删除附件API"""
    try:
        attachment = AnnouncementAttachment.query.get_or_404(attachment_id)
        announcement = attachment.announcement

        if announcement.is_readonly:
            return jsonify({'success': False, 'message': '已发布的公告不可删除附件'}), 400

        # 尝试删除云端文件
        try:
            storage_client = get_supabase_client()
            if hasattr(storage_client, 'delete_file_by_url'):
                storage_client.delete_file_by_url(attachment.file_url)
        except Exception as e:
            logger.warning(f"删除云端文件失败: {str(e)}")

        # 删除数据库记录
        db.session.delete(attachment)
        db.session.commit()

        return jsonify({'success': True, 'message': '附件已删除'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"删除附件失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500


@announcement_bp.route('/api/preview_attachment/<int:attachment_id>')
@login_required
def api_preview_attachment(attachment_id):
    """代理预览公告附件 - 支持 NAS 智能存储和云端回退"""
    import requests
    from flask import Response
    from urllib.parse import quote

    attachment = AnnouncementAttachment.query.get_or_404(attachment_id)
    url = attachment.file_url
    filename = attachment.filename

    # 根据文件扩展名确定 MIME 类型
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'bin'
    mime_map = {
        'pdf': 'application/pdf',
        'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
        'png': 'image/png', 'gif': 'image/gif',
        'webp': 'image/webp', 'bmp': 'image/bmp',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'ppt': 'application/vnd.ms-powerpoint',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'txt': 'text/plain',
        'zip': 'application/zip',
        'rar': 'application/x-rar-compressed'
    }
    mime_type = mime_map.get(ext, 'application/octet-stream')

    # 对文件名进行 RFC 5987 编码以支持中文
    encoded_filename = quote(filename, safe='')

    try:
        # 处理 NAS 智能存储路径
        if url and url.startswith('/storage/nas/'):
            from app.views.storage import _get_file_with_fallback
            from urllib.parse import urlparse, parse_qs

            parsed = urlparse(url)
            path_parts = parsed.path.split('/')
            bucket_type = path_parts[3] if len(path_parts) > 3 else 'invoice'
            query_params = parse_qs(parsed.query)
            nas_path = query_params.get('path', [''])[0]

            if nas_path:
                file_content, source = _get_file_with_fallback(nas_path, bucket_type)
                if file_content:
                    logger.info(f"公告附件从 {source} 获取成功")
                    headers = {
                        'Content-Type': mime_type,
                        'Content-Disposition': f"inline; filename*=UTF-8''{encoded_filename}",
                        'X-Storage-Source': source or 'unknown'
                    }
                    return Response(file_content, headers=headers)
                else:
                    return jsonify({'success': False, 'message': '文件获取失败'}), 404

        # 云端文件（Supabase URL），代理下载
        elif url and (url.startswith('http://') or url.startswith('https://')):
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                headers = {
                    'Content-Type': mime_type,
                    'Content-Disposition': f"inline; filename*=UTF-8''{encoded_filename}"
                }
                return Response(resp.content, headers=headers)
            else:
                return jsonify({'success': False, 'message': '文件获取失败'}), 404
        else:
            return jsonify({'success': False, 'message': '无效的文件URL'}), 400

    except Exception as e:
        logger.error(f"预览附件失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'预览失败: {str(e)}'}), 500


@announcement_bp.route('/api/read_stats/<int:announcement_id>')
@login_required
@permission_required('announcement', 'view')
def api_read_stats(announcement_id):
    """获取阅读统计API"""
    try:
        announcement = Announcement.query.get_or_404(announcement_id)

        return jsonify({
            'success': True,
            'data': {
                'total_count': announcement.target_user_count,
                'read_count': announcement.read_count,
                'unread_count': announcement.unread_count
            }
        })

    except Exception as e:
        logger.error(f"获取阅读统计失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@announcement_bp.route('/api/mark_read/<int:announcement_id>', methods=['POST'])
@login_required
def api_mark_read(announcement_id):
    """标记公告为已读API（用户端）"""
    try:
        AnnouncementRead.mark_as_read(announcement_id, current_user.id)
        db.session.commit()

        return jsonify({'success': True, 'message': '已标记为已读'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"标记已读失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@announcement_bp.route('/api/my_announcements')
@login_required
def api_my_announcements():
    """获取我的公告列表API（用户端）"""
    try:
        # 获取当前用户的公告
        read_records = AnnouncementRead.query.filter(
            AnnouncementRead.user_id == current_user.id
        ).join(Announcement).filter(
            Announcement.is_deleted == False,
            Announcement.status == 'published'
        ).order_by(Announcement.published_at.desc()).all()

        announcements = []
        for record in read_records:
            ann = record.announcement
            announcements.append({
                'id': ann.id,
                'title': ann.title,
                'announcement_type': ann.announcement_type,
                'published_at': ann.published_at.isoformat() if ann.published_at else None,
                'is_read': record.is_read,
                'read_at': record.read_at.isoformat() if record.read_at else None
            })

        return jsonify({
            'success': True,
            'data': announcements
        })

    except Exception as e:
        logger.error(f"获取公告列表失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@announcement_bp.route('/api/users')
@login_required
@permission_required('announcement', 'create')
def api_get_users():
    """获取用户列表API（用于发布范围选择）"""
    try:
        from app.utils.dictionary_helpers import get_role_options

        # 获取所有活跃用户，按角色分组
        users = User.query.filter(User._is_active == True).all()

        # 按角色分组
        role_options = get_role_options()
        role_map = {r['value']: r['label'] for r in role_options}

        roles_data = {}
        for user in users:
            role_code = user.role or 'unknown'
            if role_code not in roles_data:
                roles_data[role_code] = {
                    'role_code': role_code,
                    'display_name': role_map.get(role_code, role_code),
                    'users': []
                }
            roles_data[role_code]['users'].append({
                'id': user.id,
                'username': user.username,
                'real_name': user.real_name or user.username
            })

        return jsonify({
            'success': True,
            'data': list(roles_data.values())
        })

    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500
