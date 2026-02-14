# -*- coding: utf-8 -*-
"""
文件管理视图

提供文件管理主页面和所有 API 端点。
"""
import logging
from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user

from app import db
from app.services.file_manager_service import FileManagerService

logger = logging.getLogger(__name__)

file_manager_bp = Blueprint('file_manager', __name__, url_prefix='/files')


# ------------------------------------------------------------------
# 页面路由
# ------------------------------------------------------------------

@file_manager_bp.route('/')
@login_required
def index():
    """文件管理主页面"""
    folder_id = request.args.get('folder_id', None, type=int)
    return render_template(
        'files/tw_file_manager.html',
        active_page='file_manager',
        initial_folder_id=folder_id,
    )


# ------------------------------------------------------------------
# 文件夹 API
# ------------------------------------------------------------------

@file_manager_bp.route('/api/folders', methods=['GET'])
@login_required
def get_folder_tree():
    """获取文件夹树"""
    tree = FileManagerService.get_folder_tree(current_user)
    return jsonify({'success': True, 'data': tree})


@file_manager_bp.route('/api/folders', methods=['POST'])
@login_required
def create_folder():
    """创建文件夹"""
    data = request.get_json(silent=True) or {}
    name = data.get('name', '')
    parent_id = data.get('parent_id')

    ok, result = FileManagerService.create_folder(current_user, name, parent_id)
    if not ok:
        return jsonify({'success': False, 'message': result}), 400
    return jsonify({'success': True, 'data': result})


@file_manager_bp.route('/api/folders/<int:folder_id>', methods=['PUT'])
@login_required
def rename_folder(folder_id):
    """重命名文件夹"""
    data = request.get_json(silent=True) or {}
    new_name = data.get('name', '')

    ok, result = FileManagerService.rename_folder(current_user, folder_id, new_name)
    if not ok:
        return jsonify({'success': False, 'message': result}), 400
    return jsonify({'success': True, 'data': result})


@file_manager_bp.route('/api/folders/<int:folder_id>', methods=['DELETE'])
@login_required
def delete_folder(folder_id):
    """删除文件夹"""
    ok, result = FileManagerService.delete_folder(current_user, folder_id)
    if not ok:
        return jsonify({'success': False, 'message': result}), 400
    return jsonify({'success': True, 'message': result})


# ------------------------------------------------------------------
# 文件列表 / 导航
# ------------------------------------------------------------------

@file_manager_bp.route('/api/list', methods=['GET'])
@login_required
def list_files():
    """列出文件夹内容"""
    folder_id = request.args.get('folder_id', None, type=int)
    data = FileManagerService.list_files(current_user, folder_id)

    # 面包屑
    breadcrumbs = FileManagerService.get_breadcrumbs(current_user, folder_id)

    # 配额
    quota = FileManagerService.get_quota_info(current_user)

    return jsonify({
        'success': True,
        'data': data,
        'breadcrumbs': breadcrumbs,
        'quota': quota,
        'current_folder_id': folder_id,
    })


# ------------------------------------------------------------------
# 文件上传
# ------------------------------------------------------------------

@file_manager_bp.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    """上传文件"""
    file = request.files.get('file')
    if not file:
        return jsonify({'success': False, 'message': '未选择文件'}), 400

    folder_id = request.form.get('folder_id', None, type=int)
    ok, result = FileManagerService.upload_file(current_user, file, folder_id)
    if not ok:
        return jsonify({'success': False, 'message': result}), 400
    return jsonify({'success': True, 'data': result})


# ------------------------------------------------------------------
# 文件操作
# ------------------------------------------------------------------

@file_manager_bp.route('/api/files/<int:file_id>/rename', methods=['POST'])
@login_required
def rename_file(file_id):
    """重命名文件"""
    data = request.get_json(silent=True) or {}
    new_name = data.get('name', '')

    ok, result = FileManagerService.rename_file(current_user, file_id, new_name)
    if not ok:
        return jsonify({'success': False, 'message': result}), 400
    return jsonify({'success': True, 'data': result})


@file_manager_bp.route('/api/files/<int:file_id>/move', methods=['POST'])
@login_required
def move_file(file_id):
    """移动文件"""
    data = request.get_json(silent=True) or {}
    target_folder_id = data.get('folder_id')

    ok, result = FileManagerService.move_file(current_user, file_id, target_folder_id)
    if not ok:
        return jsonify({'success': False, 'message': result}), 400
    return jsonify({'success': True, 'data': result})


@file_manager_bp.route('/api/files/move-batch', methods=['POST'])
@login_required
def move_files_batch():
    """批量移动文件"""
    data = request.get_json(silent=True) or {}
    file_ids = data.get('file_ids', [])
    target_folder_id = data.get('folder_id')

    if not file_ids:
        return jsonify({'success': False, 'message': '未选择文件'}), 400

    ok, result = FileManagerService.move_files_batch(current_user, file_ids, target_folder_id)
    if not ok:
        return jsonify({'success': False, 'message': result}), 400
    return jsonify({'success': True, 'message': result})


@file_manager_bp.route('/api/files/<int:file_id>/delete', methods=['POST'])
@login_required
def delete_file(file_id):
    """软删除文件（移入回收站）"""
    ok, result = FileManagerService.soft_delete_file(current_user, file_id)
    if not ok:
        return jsonify({'success': False, 'message': result}), 400
    return jsonify({'success': True, 'message': result})


@file_manager_bp.route('/api/files/delete-batch', methods=['POST'])
@login_required
def delete_files_batch():
    """批量软删除"""
    data = request.get_json(silent=True) or {}
    file_ids = data.get('file_ids', [])

    if not file_ids:
        return jsonify({'success': False, 'message': '未选择文件'}), 400

    ok, result = FileManagerService.soft_delete_files_batch(current_user, file_ids)
    if not ok:
        return jsonify({'success': False, 'message': result}), 400
    return jsonify({'success': True, 'message': result})


# ------------------------------------------------------------------
# 回收站
# ------------------------------------------------------------------

@file_manager_bp.route('/api/trash', methods=['GET'])
@login_required
def list_trash():
    """列出回收站"""
    data = FileManagerService.list_trash(current_user)
    return jsonify({'success': True, 'data': data})


@file_manager_bp.route('/api/trash/<int:file_id>/restore', methods=['POST'])
@login_required
def restore_file(file_id):
    """从回收站恢复"""
    ok, result = FileManagerService.restore_file(current_user, file_id)
    if not ok:
        return jsonify({'success': False, 'message': result}), 400
    return jsonify({'success': True, 'data': result})


@file_manager_bp.route('/api/trash/<int:file_id>/permanent', methods=['DELETE'])
@login_required
def permanent_delete(file_id):
    """永久删除"""
    ok, result = FileManagerService.permanent_delete(current_user, file_id)
    if not ok:
        return jsonify({'success': False, 'message': result}), 400
    return jsonify({'success': True, 'message': result})


@file_manager_bp.route('/api/trash/empty', methods=['POST'])
@login_required
def empty_trash():
    """清空回收站"""
    ok, result = FileManagerService.empty_trash(current_user)
    if not ok:
        return jsonify({'success': False, 'message': result}), 400
    return jsonify({'success': True, 'message': result})


# ------------------------------------------------------------------
# 搜索
# ------------------------------------------------------------------

@file_manager_bp.route('/api/search', methods=['GET'])
@login_required
def search_files():
    """搜索文件"""
    keyword = request.args.get('q', '').strip()
    if not keyword:
        return jsonify({'success': True, 'data': []})

    results = FileManagerService.search_files(current_user, keyword)
    return jsonify({'success': True, 'data': results})


# ------------------------------------------------------------------
# 配额
# ------------------------------------------------------------------

@file_manager_bp.route('/api/quota', methods=['GET'])
@login_required
def get_quota():
    """获取配额信息"""
    quota = FileManagerService.get_quota_info(current_user)
    return jsonify({'success': True, 'data': quota})


# ------------------------------------------------------------------
# 文件下载/预览（代理NAS文件）
# ------------------------------------------------------------------

@file_manager_bp.route('/api/files/<int:file_id>/download', methods=['GET'])
@login_required
def download_file(file_id):
    """下载文件"""
    from flask import Response
    from app.models.file_manager import UserFileRef

    ref = UserFileRef.query.filter_by(
        id=file_id, user_id=current_user.id
    ).first()

    if not ref:
        abort(404)

    lib = ref.file_library
    if not lib:
        abort(404)

    # 通过存储代理获取文件
    try:
        from app.utils.smart_storage_manager import SmartStorageManager
        storage = SmartStorageManager()
        nas_subdir = storage.bucket_mapping.get('file_library', 'file-library')
        full_path = f"{nas_subdir}/{lib.storage_path}"

        if storage.nas_enabled and storage.is_nas_available():
            content = storage.nas_client.download_file(full_path)
            if content:
                return Response(
                    content,
                    mimetype=lib.mime_type or 'application/octet-stream',
                    headers={
                        'Content-Disposition': f'attachment; filename="{ref.display_name}"',
                        'Content-Length': str(lib.file_size),
                    }
                )
    except Exception as e:
        logger.error(f"文件下载失败: {e}")

    abort(404)


@file_manager_bp.route('/api/files/<int:file_id>/preview', methods=['GET'])
@login_required
def preview_file(file_id):
    """预览文件（返回内联内容）"""
    from flask import Response
    from app.models.file_manager import UserFileRef

    ref = UserFileRef.query.filter_by(
        id=file_id, user_id=current_user.id
    ).first()
    if not ref:
        abort(404)

    lib = ref.file_library
    if not lib:
        abort(404)

    try:
        from app.utils.smart_storage_manager import SmartStorageManager
        storage = SmartStorageManager()
        nas_subdir = storage.bucket_mapping.get('file_library', 'file-library')
        full_path = f"{nas_subdir}/{lib.storage_path}"

        if storage.nas_enabled and storage.is_nas_available():
            content = storage.nas_client.download_file(full_path)
            if content:
                return Response(
                    content,
                    mimetype=lib.mime_type or 'application/octet-stream',
                    headers={
                        'Content-Disposition': f'inline; filename="{ref.display_name}"',
                    }
                )
    except Exception as e:
        logger.error(f"文件预览失败: {e}")

    abort(404)
