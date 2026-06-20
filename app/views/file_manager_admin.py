# -*- coding: utf-8 -*-
"""管理员视角的文件管理路由。仅 admin/ceo 可访问。"""
import logging
from io import BytesIO
from flask import Blueprint, jsonify, request, render_template, send_file, abort
from flask_login import current_user, login_required

from app.models import User
from app.models.file_manager import UserFileRef
from app.services.file_admin_service import (
    list_users_with_stats, list_user_files_flat,
    set_admin_lock, transfer_file,
)

logger = logging.getLogger(__name__)
file_manager_admin_bp = Blueprint('file_manager_admin', __name__)


def _require_admin():
    """Returns (jsonify_response, status_code) tuple if not admin/ceo, else None."""
    if current_user.role not in ('admin', 'ceo'):
        return jsonify({'success': False, 'message': '仅管理员可访问'}), 403
    return None


@file_manager_admin_bp.route('/file-manager/admin')
@login_required
def admin_page():
    if current_user.role not in ('admin', 'ceo'):
        abort(403)
    return render_template('files/at_file_manager_admin.html')


@file_manager_admin_bp.route('/api/file-manager/admin/users', methods=['GET'])
@login_required
def list_users():
    deny = _require_admin()
    if deny:
        return deny
    return jsonify({'success': True, 'data': list_users_with_stats()})


@file_manager_admin_bp.route('/api/file-manager/admin/files', methods=['GET'])
@login_required
def list_files():
    deny = _require_admin()
    if deny:
        return deny
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'success': False, 'message': '缺少 user_id'}), 400
    rows = list_user_files_flat(
        user_id,
        include_deleted=request.args.get('include_deleted', '0') == '1',
        search=(request.args.get('search') or '').strip(),
        file_type=(request.args.get('file_type') or '').strip(),
        sort=(request.args.get('sort') or 'recent').strip(),
    )
    return jsonify({'success': True, 'data': rows})


@file_manager_admin_bp.route('/api/file-manager/admin/files/<int:file_ref_id>/lock', methods=['POST'])
@login_required
def lock_file(file_ref_id):
    deny = _require_admin()
    if deny:
        return deny
    locked = bool((request.get_json(silent=True) or {}).get('locked', True))
    ok, msg = set_admin_lock(file_ref_id, locked=locked, by_user=current_user)
    return jsonify({'success': ok, 'message': msg}), (200 if ok else 400)


@file_manager_admin_bp.route('/api/file-manager/admin/files/<int:file_ref_id>/transfer', methods=['PATCH'])
@login_required
def transfer(file_ref_id):
    deny = _require_admin()
    if deny:
        return deny
    data = request.get_json(silent=True) or {}
    to_user_id = data.get('to_user_id')
    to_folder_id = data.get('to_folder_id')
    if not to_user_id:
        return jsonify({'success': False, 'message': '缺少 to_user_id'}), 400
    ok, msg = transfer_file(
        file_ref_id, to_user_id=int(to_user_id),
        to_folder_id=int(to_folder_id) if to_folder_id else None,
        by_user=current_user,
    )
    return jsonify({'success': ok, 'message': msg}), (200 if ok else 400)


# 已移除：管理员侧 wiki-ingest 端点
# 现在管理员前端直接调用个人侧 /api/wiki/raw-files/from-file-ref，
# 复用其异步编译 + 通知流程（避免双份实现 + 同步状态 bug）


@file_manager_admin_bp.route('/api/file-manager/admin/files/<int:file_ref_id>/download', methods=['GET'])
@login_required
def download(file_ref_id):
    deny = _require_admin()
    if deny:
        return deny
    ref = UserFileRef.query.get(file_ref_id)
    if not ref:
        abort(404)
    lib = ref.file_library
    if not lib:
        abort(404)
    from app.services.file_manager_service import FileManagerService
    content = FileManagerService.read_file_content_auto_decompress(lib)
    if content is None:
        abort(500)
    inline = request.args.get('inline') in ('1', 'true', 'yes')
    return send_file(
        BytesIO(content),
        download_name=lib.original_filename,
        as_attachment=not inline,
        mimetype=lib.mime_type or 'application/octet-stream',
    )


@file_manager_admin_bp.route('/api/file-manager/admin/files/<int:file_ref_id>/preview-pdf', methods=['GET'])
@login_required
def preview_office_as_pdf(file_ref_id):
    """管理员侧 Office 文档转 PDF。"""
    deny = _require_admin()
    if deny:
        return deny
    ref = UserFileRef.query.get(file_ref_id)
    if not ref:
        abort(404)
    lib = ref.file_library
    if not lib:
        abort(404)

    from app.services.file_manager_service import FileManagerService
    from app.services.office_preview_service import (
        is_office_file, get_or_convert_pdf, hash_content,
    )

    if not is_office_file(mime_type=lib.mime_type, filename=lib.original_filename):
        return jsonify({'success': False, 'message': '该文件不是 Office 文档'}), 400

    content = FileManagerService.read_file_content_auto_decompress(lib)
    if content is None:
        return jsonify({'success': False, 'message': '读取文件失败'}), 500

    sha = lib.sha256_hash or hash_content(content)
    ok, result = get_or_convert_pdf(content=content, sha256=sha, filename=lib.original_filename)
    if not ok:
        return jsonify({'success': False, 'message': result}), 500

    return send_file(result, mimetype='application/pdf', as_attachment=False)
