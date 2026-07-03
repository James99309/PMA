# -*- coding: utf-8 -*-
"""通用实体附件上传/删除 —— 任意业务对象(模型上有 attachments Text(JSON) 列)
复用同一套端点,避免每个实体各写一遍上传逻辑。

接入新实体:在 _registry() 加一行 + 给该模型加 attachments Text 列即可。

文件名规则(按需求):保留上传文件原名;重名时在文件名后追加上传日期(YYYYMMDD)以区分,
再重名则追加到秒级时间戳。不做 -1/-2 计数式改名。

存储底层复用 smart_storage(NAS/本地自动切换);元数据(文件名/url/大小/上传时间)存实体 JSON。
"""
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.utils.access_control import can_edit_data
from app.utils.smart_storage_manager import get_smart_storage

attachments_bp = Blueprint('attachments', __name__, url_prefix='/api/attachments')

ALLOWED_EXT = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
               'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp',
               'dwg', 'dxf', 'zip', 'rar', '7z', 'txt', 'csv'}
MAX_SIZE = 20 * 1024 * 1024  # 20MB


def _registry():
    """entity_type -> 配置。新增实体在此加一行(模型需有 attachments Text 列)。"""
    from app.models.project import Project
    return {
        'project': {'model': Project, 'business_type': 'project', 'bucket_type': 'invoice'},
    }


def _se_pm_can_access_project(entity_type, entity):
    """角色开口:方案经理/产品经理若能查看该项目,可上传项目附件(删除仅限本人所传)。
    与 project 详情页附件卡「创建人隔离」口径一致:SE/PM 是技术参与方,附件是其交付物。"""
    if entity_type != 'project':
        return False
    if getattr(current_user, 'role', None) not in ('solution_manager', 'product_manager'):
        return False
    from app.utils.access_control import can_view_project
    return can_view_project(current_user, entity)


def _load(entity_type, entity_id):
    cfg = _registry().get(entity_type)
    if not cfg:
        return None, None, '不支持的附件类型'
    entity = cfg['model'].query.get(entity_id)
    if not entity:
        return None, None, '对象不存在'
    return entity, cfg, None


def _att_list(entity):
    raw = getattr(entity, 'attachments', None)
    if not raw:
        return []
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return []


def _dedup_name(name, existing):
    """保留原名主体,始终在文件名后追加上传日期(YYYYMMDD)以区分;
    同日重名再追加到秒级时间戳。不做 -1/-2 计数式改名。
    显示名与下载名一致,均带日期后缀。"""
    if '.' in name:
        base, ext = name.rsplit('.', 1)
    else:
        base, ext = name, ''
    date = datetime.now().strftime('%Y%m%d')
    cand = f"{base}_{date}.{ext}" if ext else f"{base}_{date}"
    if cand not in existing:
        return cand
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"{base}_{ts}.{ext}" if ext else f"{base}_{ts}"


@attachments_bp.route('/<entity_type>/<int:entity_id>/upload', methods=['POST'])
@login_required
def upload(entity_type, entity_id):
    entity, cfg, err = _load(entity_type, entity_id)
    if err:
        return jsonify({'success': False, 'message': err}), 404
    if not (can_edit_data(entity, current_user) or _se_pm_can_access_project(entity_type, entity)):
        return jsonify({'success': False, 'message': '您没有权限上传该对象的附件'}), 403

    file = request.files.get('file')
    if not file or not file.filename:
        return jsonify({'success': False, 'message': '未选择文件'}), 400

    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext and ext not in ALLOWED_EXT:
        return jsonify({'success': False, 'message': f'不支持的文件类型: .{ext}'}), 400

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > MAX_SIZE:
        return jsonify({'success': False, 'message': '文件超过 20MB 上限'}), 400

    existing = [a.get('filename') for a in _att_list(entity)]
    filename = _dedup_name(file.filename, existing)

    try:
        storage = get_smart_storage()
        result = storage.upload_file(
            object_id=entity.id, file=file, filename=filename,
            file_type='attachment', bucket_type=cfg['bucket_type'],
            business_type=cfg['business_type'])
    except Exception as e:
        return jsonify({'success': False, 'message': f'上传失败: {e}'}), 500

    if not (result and result.get('url')):
        return jsonify({'success': False, 'message': '上传失败,存储未返回地址'}), 500

    atts = _att_list(entity)
    atts.append({
        'filename': filename,
        'url': result.get('url'),
        'size': size,
        'type': 'attachment',
        'uploaded_at': datetime.now().isoformat(),
        'uploaded_by': getattr(current_user, 'id', None),
        'uploaded_by_name': getattr(current_user, 'real_name', None) or getattr(current_user, 'username', None),
    })
    entity.attachments = json.dumps(atts)
    db.session.commit()

    return jsonify({'success': True, 'message': '上传成功', 'data': {
        'filename': filename, 'url': result.get('url'), 'size': size,
        'index': len(atts) - 1,
    }})


@attachments_bp.route('/<entity_type>/<int:entity_id>/delete/<int:index>', methods=['POST', 'DELETE'])
@login_required
def delete(entity_type, entity_id, index):
    entity, cfg, err = _load(entity_type, entity_id)
    if err:
        return jsonify({'success': False, 'message': err}), 404
    atts = _att_list(entity)
    if not (0 <= index < len(atts)):
        return jsonify({'success': False, 'message': '附件不存在'}), 404

    # 权限:项目负责人/编辑者可删任意附件;SE/PM 仅能删自己上传的
    _can = can_edit_data(entity, current_user)
    if not _can and _se_pm_can_access_project(entity_type, entity):
        _can = atts[index].get('uploaded_by') == current_user.id
    if not _can:
        return jsonify({'success': False, 'message': '您没有权限删除该对象的附件'}), 403

    atts.pop(index)
    entity.attachments = json.dumps(atts) if atts else None
    db.session.commit()
    return jsonify({'success': True, 'message': '已删除'})
