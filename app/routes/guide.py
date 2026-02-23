# -*- coding: utf-8 -*-
"""新功能说明书路由"""
import os
import re
from flask import Blueprint, render_template, send_from_directory, abort, request, jsonify, url_for
from flask_login import login_required, current_user

guide_bp = Blueprint('guide', __name__, url_prefix='/guide')

# 说明书截图存储目录
GUIDE_IMAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                               'scripts', 'temp', 'guide_images')


@guide_bp.route('/whats-new')
@login_required
def whats_new():
    from app.data.features_guide_data import get_features_data
    all_features = get_features_data()
    is_admin = current_user.role == 'admin'
    # published/beta: 所有人可见; draft: 仅管理员可见
    features = [f for f in all_features if f.get('status', 'published') != 'draft' or is_admin]
    return render_template('guide/whats_new.html', features=features)


@guide_bp.route('/image/<path:filename>')
@login_required
def guide_image(filename):
    """提供说明书截图文件"""
    if not os.path.isfile(os.path.join(GUIDE_IMAGE_DIR, filename)):
        abort(404)
    return send_from_directory(GUIDE_IMAGE_DIR, filename)


@guide_bp.route('/upload-image', methods=['POST'])
@login_required
def upload_guide_image():
    """上传说明书截图（仅管理员）"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '未选择文件'}), 400

    file = request.files['file']
    filename = request.form.get('filename', '').strip()

    # 验证文件类型
    if not file.filename or not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
        return jsonify({'success': False, 'message': '仅支持 PNG/JPG/WEBP 图片格式'}), 400

    # 验证目标文件名：只允许字母数字下划线短横线和点，且必须以图片扩展名结尾
    if not filename or not re.match(r'^[a-zA-Z0-9_\-]+\.(png|jpg|jpeg|webp)$', filename):
        return jsonify({'success': False, 'message': '无效文件名'}), 400

    os.makedirs(GUIDE_IMAGE_DIR, exist_ok=True)
    file.save(os.path.join(GUIDE_IMAGE_DIR, filename))

    return jsonify({
        'success': True,
        'url': url_for('guide.guide_image', filename=filename)
    })


@guide_bp.route('/gallery-image', methods=['POST'])
@login_required
def add_gallery_image():
    """添加图库图片（仅管理员）"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '未选择文件'}), 400

    file = request.files['file']
    feature_id = request.form.get('feature_id', '').strip()

    if not file.filename or not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
        return jsonify({'success': False, 'message': '仅支持 PNG/JPG/WEBP 图片格式'}), 400

    if not feature_id or not re.match(r'^[a-zA-Z0-9_\-]+$', feature_id):
        return jsonify({'success': False, 'message': '无效功能ID'}), 400

    from app.data.features_guide_data import get_features_data, save_features_data
    features = get_features_data()
    target = next((f for f in features if f['id'] == feature_id), None)
    if not target:
        return jsonify({'success': False, 'message': '功能不存在'}), 404

    gallery = target.get('gallery', [])
    ext = file.filename.rsplit('.', 1)[-1].lower()
    # Find next available index
    idx = len(gallery)
    filename = f'{feature_id}_gallery_{idx}.{ext}'
    while os.path.exists(os.path.join(GUIDE_IMAGE_DIR, filename)):
        idx += 1
        filename = f'{feature_id}_gallery_{idx}.{ext}'

    os.makedirs(GUIDE_IMAGE_DIR, exist_ok=True)
    file.save(os.path.join(GUIDE_IMAGE_DIR, filename))

    gallery.append(filename)
    target['gallery'] = gallery
    save_features_data(features)

    return jsonify({
        'success': True,
        'filename': filename,
        'url': url_for('guide.guide_image', filename=filename),
        'index': len(gallery) - 1
    })


@guide_bp.route('/gallery-image', methods=['DELETE'])
@login_required
def delete_gallery_image():
    """删除图库图片（仅管理员）"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403

    data = request.get_json()
    feature_id = data.get('feature_id', '')
    index = data.get('index')

    if index is None:
        return jsonify({'success': False, 'message': '缺少索引'}), 400

    from app.data.features_guide_data import get_features_data, save_features_data
    features = get_features_data()
    target = next((f for f in features if f['id'] == feature_id), None)
    if not target:
        return jsonify({'success': False, 'message': '功能不存在'}), 404

    gallery = target.get('gallery', [])
    if index < 0 or index >= len(gallery):
        return jsonify({'success': False, 'message': '索引超出范围'}), 400

    removed = gallery.pop(index)
    target['gallery'] = gallery
    save_features_data(features)

    # Delete file from disk
    filepath = os.path.join(GUIDE_IMAGE_DIR, removed)
    if os.path.isfile(filepath):
        os.remove(filepath)

    return jsonify({'success': True})


@guide_bp.route('/update-text', methods=['POST'])
@login_required
def update_guide_text():
    """更新说明书文字（仅管理员）"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403

    from app.data.features_guide_data import get_features_data, save_features_data

    data = request.get_json()
    feature_id = data.get('feature_id')
    field = data.get('field')
    value = data.get('value', '')
    index = data.get('index')
    sub_field = data.get('sub_field')

    features = get_features_data()

    target = next((f for f in features if f['id'] == feature_id), None)
    if not target:
        return jsonify({'success': False, 'message': '功能不存在'}), 404

    if field == 'scenarios' and index is not None and sub_field:
        if index < len(target.get('scenarios', [])):
            target['scenarios'][index][sub_field] = value
        else:
            return jsonify({'success': False, 'message': '索引超出范围'}), 400
    elif field in ('description', 'steps', 'keywords') and index is not None:
        if index < len(target.get(field, [])):
            target[field][index] = value
        else:
            return jsonify({'success': False, 'message': '索引超出范围'}), 400
    elif field in ('title', 'summary', 'entry'):
        target[field] = value
    else:
        return jsonify({'success': False, 'message': '无效字段'}), 400

    save_features_data(features)
    return jsonify({'success': True})
