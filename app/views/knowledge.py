# -*- coding: utf-8 -*-
"""
知识库 API 视图（过渡版）

旧 RAG 方案（KnowledgeDocument / 向量分块）已在 2026-04-09 下线，
迁移至基于 Karpathy LLM Wiki 的方案。

本文件当前仅保留标签管理端点 `/tags/*`，并为旧的文档相关端点保留
空实现的兼容层，以避免前端 file_manager 在过渡期崩溃。
新 Wiki 方案的端点在 `app/views/knowledge_wiki.py`（Phase 8 新增）。

前端迁移节奏：
1. 文件管理器 tw_file_manager.html 的"知识库"tab 暂时展示为空。
2. 加入知识库、重新处理、移除、状态查询等操作返回提示"功能升级中"。
3. 标签管理继续可用，未来 Wiki 可能复用。
"""
import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app import db
from app.models.knowledge import KnowledgeTag

logger = logging.getLogger(__name__)

knowledge_bp = Blueprint('knowledge', __name__, url_prefix='/api/knowledge')


def _is_admin():
    """检查当前用户是否为管理员"""
    return current_user.role in ('admin', 'ceo')


# ------------------------------------------------------------------
# 标签管理
# ------------------------------------------------------------------

@knowledge_bp.route('/tags', methods=['GET'])
@login_required
def list_tags():
    """获取所有活跃标签（所有登录用户可见）"""
    tags = KnowledgeTag.query.filter_by(is_active=True).order_by(KnowledgeTag.name).all()
    result = []
    for t in tags:
        d = t.to_dict()
        d['document_count'] = 0  # 兼容前端字段，Wiki 上线后由新系统填充
        result.append(d)
    return jsonify({'success': True, 'data': result})


@knowledge_bp.route('/tags', methods=['POST'])
@login_required
def create_tag():
    """创建标签（仅管理员）"""
    if not _is_admin():
        return jsonify({'success': False, 'message': '权限不足'}), 403

    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'message': '标签名称不能为空'}), 400

    existing = KnowledgeTag.query.filter_by(name=name).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            existing.color = data.get('color', existing.color)
            existing.description = data.get('description', existing.description)
            db.session.commit()
            return jsonify({'success': True, 'data': existing.to_dict()})
        return jsonify({'success': False, 'message': '标签名称已存在'}), 400

    tag = KnowledgeTag(
        name=name,
        color=data.get('color', 'blue'),
        description=data.get('description'),
        created_by=current_user.id,
    )
    db.session.add(tag)
    db.session.commit()
    return jsonify({'success': True, 'data': tag.to_dict()})


@knowledge_bp.route('/tags/<int:tag_id>', methods=['PUT'])
@login_required
def update_tag(tag_id):
    """更新标签（仅管理员）"""
    if not _is_admin():
        return jsonify({'success': False, 'message': '权限不足'}), 403

    tag = KnowledgeTag.query.get(tag_id)
    if not tag:
        return jsonify({'success': False, 'message': '标签不存在'}), 404

    data = request.get_json(silent=True) or {}

    if 'name' in data:
        new_name = (data['name'] or '').strip()
        if not new_name:
            return jsonify({'success': False, 'message': '标签名称不能为空'}), 400
        dup = KnowledgeTag.query.filter(
            KnowledgeTag.name == new_name,
            KnowledgeTag.id != tag_id,
        ).first()
        if dup:
            return jsonify({'success': False, 'message': '标签名称已存在'}), 400
        tag.name = new_name

    if 'color' in data:
        tag.color = data['color']
    if 'description' in data:
        tag.description = data['description']

    db.session.commit()
    return jsonify({'success': True, 'data': tag.to_dict()})


@knowledge_bp.route('/tags/<int:tag_id>', methods=['DELETE'])
@login_required
def delete_tag(tag_id):
    """软删除标签（仅管理员）"""
    if not _is_admin():
        return jsonify({'success': False, 'message': '权限不足'}), 403

    tag = KnowledgeTag.query.get(tag_id)
    if not tag:
        return jsonify({'success': False, 'message': '标签不存在'}), 404

    tag.is_active = False
    db.session.commit()
    return jsonify({'success': True, 'message': '标签已删除'})


# ------------------------------------------------------------------
# 文档相关端点（过渡兼容层 —— 旧 RAG 已下线）
# ------------------------------------------------------------------

_UPGRADE_MESSAGE = '知识库正在升级为新的 Wiki 方案，旧文档操作暂不可用'


@knowledge_bp.route('/documents', methods=['GET'])
@login_required
def list_documents():
    """过渡期返回空列表，避免前端文件管理器知识库 tab 崩溃"""
    return jsonify({
        'success': True,
        'data': [],
        'pagination': {
            'page': 1,
            'per_page': 0,
            'total': 0,
            'pages': 0,
            'has_next': False,
            'has_prev': False,
        },
    })


@knowledge_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    """过渡期返回零值统计"""
    return jsonify({
        'success': True,
        'data': {
            'total_documents': 0,
            'status_counts': {'pending': 0, 'processing': 0, 'ready': 0, 'error': 0},
            'total_chunks': 0,
        },
    })


@knowledge_bp.route('/documents/file-status', methods=['POST'])
@login_required
def get_file_status():
    """过渡期统一返回所有文件均不在知识库"""
    data = request.get_json(silent=True) or {}
    file_ref_ids = data.get('file_ref_ids', [])
    return jsonify({
        'success': True,
        'data': {rid: {'in_knowledge_base': False} for rid in file_ref_ids},
    })


@knowledge_bp.route('/documents/add', methods=['POST'])
@knowledge_bp.route('/documents/batch-add', methods=['POST'])
@login_required
def add_documents():
    return jsonify({'success': False, 'message': _UPGRADE_MESSAGE}), 503


@knowledge_bp.route('/documents/<int:doc_id>/remove', methods=['POST'])
@knowledge_bp.route('/documents/<int:doc_id>/reprocess', methods=['POST'])
@login_required
def document_single_op(doc_id):
    return jsonify({'success': False, 'message': _UPGRADE_MESSAGE}), 503


@knowledge_bp.route('/documents/batch-remove', methods=['POST'])
@login_required
def batch_remove_documents():
    return jsonify({'success': False, 'message': _UPGRADE_MESSAGE}), 503


@knowledge_bp.route('/documents/<int:doc_id>', methods=['GET'])
@login_required
def get_document(doc_id):
    return jsonify({'success': False, 'message': '文档不存在'}), 404
