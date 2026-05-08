# -*- coding: utf-8 -*-
"""
文件管理视图

提供文件管理主页面和所有 API 端点。
"""
import os
import logging
import tempfile
from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user

from app import db
from app.models.file_manager import FileLibrary
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
        is_admin=current_user.role in ('admin', 'ceo'),
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


@file_manager_bp.route('/api/upload/chunk', methods=['POST'])
@login_required
def upload_chunk():
    """分片上传接口，供大文件（>50MB）使用"""
    chunk = request.files.get('file')
    upload_id = request.form.get('upload_id', '').strip()
    filename = request.form.get('filename', '').strip()
    folder_id = request.form.get('folder_id', None, type=int)

    try:
        chunk_index = int(request.form.get('chunk_index', 0))
        total_chunks = int(request.form.get('total_chunks', 1))
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': '参数错误'}), 400

    if not chunk or not upload_id or not filename:
        return jsonify({'success': False, 'message': '缺少必要参数'}), 400

    # 安全校验：upload_id 只允许 UUID 格式
    import re
    if not re.match(r'^[0-9a-f-]{36}$', upload_id):
        return jsonify({'success': False, 'message': '无效的上传ID'}), 400

    tmp_dir = os.path.join(tempfile.gettempdir(), 'pma_chunks', upload_id)
    os.makedirs(tmp_dir, exist_ok=True)

    # 保存分片
    chunk_path = os.path.join(tmp_dir, f'{chunk_index:04d}')
    chunk.save(chunk_path)

    # 不是最后一片，返回 pending
    if chunk_index < total_chunks - 1:
        return jsonify({'success': False, 'pending': True, 'chunk': chunk_index})

    # 最后一片：合并所有分片
    try:
        merged = bytearray()
        for i in range(total_chunks):
            part_path = os.path.join(tmp_dir, f'{i:04d}')
            if not os.path.exists(part_path):
                return jsonify({'success': False, 'message': f'分片 {i} 缺失，请重新上传'}), 400
            with open(part_path, 'rb') as f:
                merged.extend(f.read())

        ok, result = FileManagerService.upload_file_from_bytes(
            current_user, bytes(merged), filename, folder_id
        )
        if not ok:
            return jsonify({'success': False, 'message': result}), 400
        return jsonify({'success': True, 'data': result})

    finally:
        # 清理临时目录
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)


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
# 文件下载/预览（按 storage_type 路由）
# ------------------------------------------------------------------

def _read_file_content(lib):
    """读取文件内容（归档文件自动解压 + 更新访问时间）"""
    return FileManagerService.read_file_content_auto_decompress(lib)


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

    try:
        content = _read_file_content(lib)
        if content:
            from urllib.parse import quote
            encoded_name = quote(ref.display_name)
            return Response(
                content,
                mimetype=lib.mime_type or 'application/octet-stream',
                headers={
                    'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_name}",
                    'Content-Length': str(len(content)),
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
        content = _read_file_content(lib)
        if content:
            from urllib.parse import quote
            encoded_name = quote(ref.display_name)
            return Response(
                content,
                mimetype=lib.mime_type or 'application/octet-stream',
                headers={
                    'Content-Disposition': f"inline; filename*=UTF-8''{encoded_name}",
                }
            )
    except Exception as e:
        logger.error(f"文件预览失败: {e}")

    abort(404)


@file_manager_bp.route('/api/files/<int:file_id>/preview-pdf', methods=['GET'])
@login_required
def preview_file_as_pdf(file_id):
    """Office 文档（doc/docx/ppt/pptx）转 PDF 后返回。"""
    from flask import send_file
    from app.models.file_manager import UserFileRef
    from app.services.office_preview_service import (
        is_office_file, get_or_convert_pdf, hash_content,
    )

    ref = UserFileRef.query.filter_by(id=file_id, user_id=current_user.id).first()
    if not ref:
        abort(404)
    lib = ref.file_library
    if not lib:
        abort(404)

    if not is_office_file(mime_type=lib.mime_type, filename=lib.original_filename):
        return jsonify({'success': False, 'message': '该文件不是 Office 文档'}), 400

    content = _read_file_content(lib)
    if not content:
        return jsonify({'success': False, 'message': '读取文件失败'}), 500

    sha = lib.sha256_hash or hash_content(content)
    ok, result = get_or_convert_pdf(content=content, sha256=sha, filename=lib.original_filename)
    if not ok:
        return jsonify({'success': False, 'message': result}), 500

    return send_file(result, mimetype='application/pdf', as_attachment=False)


# ------------------------------------------------------------------
# 管理员 — 归档管理
# ------------------------------------------------------------------

@file_manager_bp.route('/api/admin/archived', methods=['GET'])
@login_required
def admin_list_archived():
    """列出所有归档文件（管理员）"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    data = FileManagerService.list_archived_files(page, per_page)
    return jsonify({'success': True, 'data': data})


@file_manager_bp.route('/api/admin/archived/<int:lib_id>/restore', methods=['POST'])
@login_required
def admin_restore_archived(lib_id):
    """恢复归档文件（管理员）"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403

    data = request.get_json(silent=True) or {}
    target_user_id = data.get('target_user_id')
    if not target_user_id:
        return jsonify({'success': False, 'message': '请指定目标用户'}), 400

    ok, result = FileManagerService.admin_restore_archived_file(
        current_user, lib_id, target_user_id
    )
    if not ok:
        return jsonify({'success': False, 'message': result}), 400
    return jsonify({'success': True, 'data': result})


@file_manager_bp.route('/api/admin/archived/<int:lib_id>/preview', methods=['GET'])
@login_required
def admin_preview_archived(lib_id):
    """预览归档文件（管理员）"""
    if current_user.role != 'admin':
        abort(403)

    from flask import Response
    lib = FileLibrary.query.get(lib_id)
    if not lib or not lib.is_archived:
        abort(404)

    try:
        content = _read_file_content(lib)
        if content:
            from urllib.parse import quote
            encoded_name = quote(lib.original_filename or 'file')
            return Response(
                content,
                mimetype=lib.mime_type or 'application/octet-stream',
                headers={
                    'Content-Disposition': f"inline; filename*=UTF-8''{encoded_name}",
                }
            )
    except Exception as e:
        logger.error(f"归档文件预览失败: {e}")

    abort(404)


@file_manager_bp.route('/api/admin/archived/<int:lib_id>/download', methods=['GET'])
@login_required
def admin_download_archived(lib_id):
    """下载归档文件（管理员）"""
    if current_user.role != 'admin':
        abort(403)

    from flask import Response
    lib = FileLibrary.query.get(lib_id)
    if not lib or not lib.is_archived:
        abort(404)

    try:
        content = _read_file_content(lib)
        if content:
            from urllib.parse import quote
            encoded_name = quote(lib.original_filename or 'file')
            return Response(
                content,
                mimetype=lib.mime_type or 'application/octet-stream',
                headers={
                    'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_name}",
                    'Content-Length': str(len(content)),
                }
            )
    except Exception as e:
        logger.error(f"归档文件下载失败: {e}")

    abort(404)


@file_manager_bp.route('/api/admin/archived/<int:lib_id>', methods=['DELETE'])
@login_required
def admin_permanent_delete_archived(lib_id):
    """彻底删除归档文件（管理员）— 删除物理文件和数据库记录"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403

    lib = FileLibrary.query.get(lib_id)
    if not lib or not lib.is_archived:
        return jsonify({'success': False, 'message': '归档文件不存在'}), 404

    try:
        # 删除物理文件
        FileManagerService._delete_from_storage(lib.storage_path, lib.storage_type)

        # 删除关联的用户引用（如有残留）
        from app.models.file_manager import UserFileRef
        UserFileRef.query.filter_by(file_library_id=lib.id).delete()

        # 删除数据库记录
        db.session.delete(lib)
        db.session.commit()

        logger.info(f"管理员 {current_user.username} 彻底删除归档文件: {lib.original_filename} (ID={lib_id})")
        return jsonify({'success': True, 'message': '已彻底删除'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"彻底删除归档文件失败: {e}")
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500


@file_manager_bp.route('/api/admin/compress-inactive', methods=['POST'])
@login_required
def admin_compress_inactive():
    """手动触发压缩不活跃文件（管理员）"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403

    data = request.get_json(silent=True) or {}
    days = data.get('days', 90)
    count = FileManagerService.archive_inactive_files(days=days)
    return jsonify({'success': True, 'message': f'已归档 {count} 个不活跃文件'})
