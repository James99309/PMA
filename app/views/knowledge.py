# -*- coding: utf-8 -*-
"""
知识库 API 视图

提供知识库标签管理、文档管理、批量操作和状态查询等 API 端点。
"""
import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app import db
from app.models.knowledge import KnowledgeTag, KnowledgeDocument, KnowledgeChunk, knowledge_document_tags
from app.models.file_manager import UserFileRef

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

    # 批量查询标签文档计数，避免 N+1
    tag_ids = [t.id for t in tags]
    count_map = {}
    if tag_ids:
        counts = db.session.query(
            knowledge_document_tags.c.tag_id,
            db.func.count(knowledge_document_tags.c.document_id)
        ).filter(
            knowledge_document_tags.c.tag_id.in_(tag_ids)
        ).group_by(knowledge_document_tags.c.tag_id).all()
        count_map = dict(counts)

    result = []
    for t in tags:
        d = t.to_dict()
        d['document_count'] = count_map.get(t.id, 0)
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

    # 检查重名（包括已停用的标签）
    existing = KnowledgeTag.query.filter_by(name=name).first()
    if existing:
        if not existing.is_active:
            # 重新启用已停用的同名标签
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
        # 检查重名（排除自身）
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
# 文档操作
# ------------------------------------------------------------------

def _can_access_document(doc):
    """检查当前用户是否有权访问指定文档"""
    if _is_admin():
        return True
    return doc.added_by == current_user.id


def _base_document_query():
    """构建文档基础查询（根据权限过滤）"""
    query = KnowledgeDocument.query
    if not _is_admin():
        query = query.filter(KnowledgeDocument.added_by == current_user.id)
    return query


@knowledge_bp.route('/documents/add', methods=['POST'])
@login_required
def add_documents():
    """将文件添加到知识库"""
    data = request.get_json(silent=True) or {}
    file_ref_ids = data.get('file_ref_ids', [])
    tag_ids = data.get('tag_ids', [])

    if not file_ref_ids:
        return jsonify({'success': False, 'message': '请选择要添加的文件'}), 400

    # 预加载标签
    tags = []
    if tag_ids:
        tags = KnowledgeTag.query.filter(
            KnowledgeTag.id.in_(tag_ids),
            KnowledgeTag.is_active == True,
        ).all()

    created_docs = []
    errors = []

    for ref_id in file_ref_ids:
        ref = UserFileRef.query.filter_by(id=ref_id, user_id=current_user.id).first()
        if not ref:
            errors.append(f'文件引用 {ref_id} 不存在或无权访问')
            continue

        # 检查是否已在知识库中（同一用户、同一文件）
        existing = KnowledgeDocument.query.filter_by(
            file_library_id=ref.file_library_id,
            user_file_ref_id=ref.id,
        ).first()
        if existing:
            errors.append(f'文件 "{ref.display_name}" 已在知识库中')
            continue

        doc = KnowledgeDocument(
            file_library_id=ref.file_library_id,
            user_file_ref_id=ref.id,
            title=ref.display_name,
            added_by=current_user.id,
            status='pending',
        )
        for tag in tags:
            doc.tags.append(tag)

        db.session.add(doc)
        db.session.flush()  # 获取 doc.id

        created_docs.append(doc)

    db.session.commit()

    # 异步处理每个文档
    for doc in created_docs:
        try:
            from app.services.knowledge_processing_service import process_document_async
            process_document_async(doc.id)
        except Exception as e:
            logger.error(f'启动文档处理失败 (doc_id={doc.id}): {e}')

    result = {
        'success': True,
        'data': [d.to_dict() for d in created_docs],
    }
    if errors:
        result['warnings'] = errors

    return jsonify(result)


@knowledge_bp.route('/documents/batch-add', methods=['POST'])
@login_required
def batch_add_documents():
    """批量添加文件到知识库（与 /documents/add 相同实现）"""
    return add_documents()


@knowledge_bp.route('/documents/<int:doc_id>/remove', methods=['POST'])
@login_required
def remove_document(doc_id):
    """从知识库移除文档（级联删除分块）"""
    doc = KnowledgeDocument.query.get(doc_id)
    if not doc:
        return jsonify({'success': False, 'message': '文档不存在'}), 404

    if not _can_access_document(doc):
        return jsonify({'success': False, 'message': '权限不足'}), 403

    title = doc.title
    db.session.delete(doc)
    db.session.commit()

    logger.info(f'用户 {current_user.username} 从知识库移除文档: {title} (ID={doc_id})')
    return jsonify({'success': True, 'message': f'已从知识库移除 "{title}"'})


@knowledge_bp.route('/documents/batch-remove', methods=['POST'])
@login_required
def batch_remove_documents():
    """批量从知识库移除文档"""
    data = request.get_json(silent=True) or {}
    document_ids = data.get('document_ids', [])

    if not document_ids:
        return jsonify({'success': False, 'message': '请选择要移除的文档'}), 400

    removed = []
    errors = []

    for doc_id in document_ids:
        doc = KnowledgeDocument.query.get(doc_id)
        if not doc:
            errors.append(f'文档 {doc_id} 不存在')
            continue
        if not _can_access_document(doc):
            errors.append(f'文档 "{doc.title}" 权限不足')
            continue

        removed.append(doc.title)
        db.session.delete(doc)

    db.session.commit()

    result = {
        'success': True,
        'message': f'已移除 {len(removed)} 个文档',
        'removed': removed,
    }
    if errors:
        result['warnings'] = errors

    return jsonify(result)


@knowledge_bp.route('/documents/<int:doc_id>/reprocess', methods=['POST'])
@login_required
def reprocess_document(doc_id):
    """重新处理文档"""
    doc = KnowledgeDocument.query.get(doc_id)
    if not doc:
        return jsonify({'success': False, 'message': '文档不存在'}), 404

    if not _can_access_document(doc):
        return jsonify({'success': False, 'message': '权限不足'}), 403

    # 重置状态
    doc.status = 'pending'
    doc.processing_error = None
    db.session.commit()

    try:
        from app.services.knowledge_processing_service import process_document_async
        process_document_async(doc.id)
    except Exception as e:
        logger.error(f'启动文档重新处理失败 (doc_id={doc.id}): {e}')
        return jsonify({'success': False, 'message': f'启动处理失败: {str(e)}'}), 500

    return jsonify({'success': True, 'data': doc.to_dict(), 'message': '已提交重新处理'})


@knowledge_bp.route('/documents', methods=['GET'])
@login_required
def list_documents():
    """列出知识库文档（支持筛选和分页）"""
    tag_id = request.args.get('tag_id', type=int)
    status = request.args.get('status', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # 限制每页数量
    per_page = min(per_page, 100)

    query = _base_document_query()

    if tag_id:
        query = query.filter(KnowledgeDocument.tags.any(KnowledgeTag.id == tag_id))
    if status:
        query = query.filter(KnowledgeDocument.status == status)

    query = query.order_by(KnowledgeDocument.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'success': True,
        'data': [d.to_dict() for d in pagination.items],
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev,
        },
    })


@knowledge_bp.route('/documents/<int:doc_id>', methods=['GET'])
@login_required
def get_document(doc_id):
    """获取单个文档详情"""
    doc = KnowledgeDocument.query.get(doc_id)
    if not doc:
        return jsonify({'success': False, 'message': '文档不存在'}), 404

    if not _can_access_document(doc):
        return jsonify({'success': False, 'message': '权限不足'}), 403

    return jsonify({'success': True, 'data': doc.to_dict()})


# ------------------------------------------------------------------
# 统计
# ------------------------------------------------------------------

@knowledge_bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    """获取知识库统计数据（单次条件聚合查询）"""
    query = _base_document_query()

    stats = query.with_entities(
        db.func.count().label('total'),
        db.func.sum(db.case((KnowledgeDocument.status == 'pending', 1), else_=0)).label('pending'),
        db.func.sum(db.case((KnowledgeDocument.status == 'processing', 1), else_=0)).label('processing'),
        db.func.sum(db.case((KnowledgeDocument.status == 'ready', 1), else_=0)).label('ready'),
        db.func.sum(db.case((KnowledgeDocument.status == 'error', 1), else_=0)).label('error'),
        db.func.coalesce(db.func.sum(KnowledgeDocument.chunk_count), 0).label('total_chunks'),
    ).first()

    return jsonify({
        'success': True,
        'data': {
            'total_documents': stats.total or 0,
            'status_counts': {
                'pending': int(stats.pending or 0),
                'processing': int(stats.processing or 0),
                'ready': int(stats.ready or 0),
                'error': int(stats.error or 0),
            },
            'total_chunks': int(stats.total_chunks),
        },
    })


# ------------------------------------------------------------------
# 文件状态查询（供文件管理器使用）
# ------------------------------------------------------------------

@knowledge_bp.route('/documents/file-status', methods=['POST'])
@login_required
def get_file_status():
    """查询文件在知识库中的状态（供文件管理器显示徽章用）"""
    data = request.get_json(silent=True) or {}
    file_ref_ids = data.get('file_ref_ids', [])

    if not file_ref_ids:
        return jsonify({'success': True, 'data': {}})

    # 查询这些文件引用对应的知识库文档
    query = KnowledgeDocument.query.filter(
        KnowledgeDocument.user_file_ref_id.in_(file_ref_ids)
    )
    # 非管理员只能看到自己添加的
    if not _is_admin():
        query = query.filter(KnowledgeDocument.added_by == current_user.id)

    docs = query.all()

    # 按 user_file_ref_id 分组
    status_map = {}
    for doc in docs:
        status_map[doc.user_file_ref_id] = {
            'in_knowledge_base': True,
            'document_id': doc.id,
            'status': doc.status,
            'tags': [{'id': t.id, 'name': t.name, 'color': t.color} for t in doc.tags],
        }

    # 不在知识库中的文件标记为 False
    for ref_id in file_ref_ids:
        if ref_id not in status_map:
            status_map[ref_id] = {
                'in_knowledge_base': False,
            }

    return jsonify({'success': True, 'data': status_map})
