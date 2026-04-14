# -*- coding: utf-8 -*-
"""Wiki 知识库 API（Karpathy LLM Wiki 方案）

Blueprint: knowledge_wiki_bp  url_prefix: ''  (前端页面和 /api/wiki/* 混在一起)

端点清单：
    GET    /wiki                              — Tailwind 前端主页面
    POST   /api/wiki/raw-files                — 从 file_library 选文件加入 Wiki
    GET    /api/wiki/raw-files                — 列出原始文件（可按 topic 过滤）
    POST   /api/wiki/raw-files/<id>/ingest    — 触发 Opus 编译
    DELETE /api/wiki/raw-files/<id>           — 删除原始文件登记（不删文章）
    GET    /api/wiki/articles                 — 文章列表（可按 topic 过滤）
    GET    /api/wiki/articles/<id>            — 文章详情（含 Markdown 正文）
    GET    /api/wiki/tree                     — topic → [articles] 树结构
    GET    /api/wiki/index                    — 读 wiki/index.md 原始 Markdown
    POST   /api/wiki/query                    — 基于 Wiki 问答
    POST   /api/wiki/lint                     — 触发整库质检

权限：
    - admin/ceo: 全部
    - 其他登录用户：只读 + query
"""
import logging
import threading

from flask import Blueprint, jsonify, render_template, request, current_app
from flask_login import current_user, login_required

from app import db
from app.models.file_manager import FileLibrary, UserFileRef
from app.models.knowledge import KnowledgeRawFile, KnowledgeWikiArticle, KnowledgePromotionRequest, KnowledgeTopic, KnowledgeShareGrant
from app.models.message import Message
from app.models.user import User
from app.services.file_manager_service import FileManagerService
from app.services.wiki import compiler, linter, querier, storage
from app.services.wiki.paths import ensure_wiki_structure

logger = logging.getLogger(__name__)

knowledge_wiki_bp = Blueprint('knowledge_wiki', __name__)


# ══════════════════════════════════════════════════════════════════
# 权限辅助
# ══════════════════════════════════════════════════════════════════

def _is_admin() -> bool:
    return getattr(current_user, 'role', None) in ('admin', 'ceo')


def _require_admin():
    if not _is_admin():
        return jsonify({'success': False, 'message': '仅管理员可执行此操作'}), 403
    return None


def _get_allowed_topic_names() -> set[str]:
    """返回主数据表中定义的所有 topic 名称集合。

    非 admin 上传 / 加入知识库时，用来校验 topic 是否在 admin 预定义列表中。
    """
    return {t[0] for t in db.session.query(KnowledgeTopic.name).all()}


# ══════════════════════════════════════════════════════════════════
# 前端页面
# ══════════════════════════════════════════════════════════════════

@knowledge_wiki_bp.route('/wiki')
@login_required
def wiki_page():
    """Wiki 主页面 —— 侧栏目录 + 正文 + 问答区"""
    ensure_wiki_structure()
    return render_template(
        'knowledge/tw_wiki.html',
        is_admin=_is_admin(),
        is_dept_manager=getattr(current_user, 'is_department_manager', False),
    )


# ══════════════════════════════════════════════════════════════════
# 原始文件管理
# ══════════════════════════════════════════════════════════════════

@knowledge_wiki_bp.route('/api/wiki/raw-files', methods=['GET'])
@login_required
def list_raw_files():
    from app.services.wiki.scope import visible_raw_files_query
    topic = (request.args.get('topic') or '').strip()
    q = visible_raw_files_query(current_user)
    if topic:
        q = q.filter_by(topic=topic)
    items = q.order_by(KnowledgeRawFile.created_at.desc()).all()
    return jsonify({'success': True, 'data': [r.to_dict() for r in items]})


@knowledge_wiki_bp.route('/api/wiki/raw-files', methods=['POST'])
@login_required
def add_raw_file():
    """把 file_library 中的文件登记为 Wiki 原始资料

    Body JSON:
        file_library_id: int (必填)
        topic: str (必填)
        title: str (可选，默认用 file_library.original_filename)
        scope: str (可选，默认 'personal')
    """
    # 不再要求 admin — scope 权限由 can_write_scope 控制
    data = request.get_json(silent=True) or {}
    fl_id = data.get('file_library_id')
    topic = (data.get('topic') or '').strip()
    title = (data.get('title') or '').strip()

    if not fl_id or not topic:
        return jsonify({'success': False, 'message': 'file_library_id 和 topic 必填'}), 400

    # 前置校验 topic 合法性，避免把非法输入交给 storage 层
    try:
        storage.validate_topic(topic)
    except storage.WikiPathError as e:
        return jsonify({'success': False, 'message': str(e)}), 400

    # 非管理员只能选 admin 预定义的 topic
    if current_user.role not in ('admin', 'ceo'):
        if topic not in _get_allowed_topic_names():
            return jsonify({'success': False, 'message': '只能选择已有的分类目录'}), 403

    fl = FileLibrary.query.get(fl_id)
    if not fl:
        return jsonify({'success': False, 'message': '文件不存在于 file_library'}), 404

    # 从 file_library 读原始字节
    content = FileManagerService.read_file_content_auto_decompress(fl)
    if content is None:
        return jsonify({'success': False, 'message': '无法读取 file_library 中的文件内容'}), 500

    ensure_wiki_structure()

    # 保存到 raw/<topic>/<safe-dated-name>
    safe_name = storage.dated_filename(fl.original_filename)
    raw_path = storage.save_raw_file(topic, safe_name, content)

    # scope 参数（默认 personal）
    scope = (data.get('scope') or 'personal').strip()
    if scope not in ('personal', 'department', 'company', 'system'):
        scope = 'personal'
    from app.services.wiki.scope import can_write_scope
    if not can_write_scope(current_user, scope):
        return jsonify({'success': False, 'message': f'无权限写入 {scope} 级别'}), 403

    raw = KnowledgeRawFile(
        file_library_id=fl.id,
        topic=topic,
        raw_path=raw_path,
        title=title or fl.original_filename,
        added_by=current_user.id,
        scope=scope,
        owner_id=current_user.id,
        owner_department=current_user.department,
    )
    db.session.add(raw)
    db.session.commit()
    logger.info(f'[Wiki] user={current_user.id} 新增 raw_file id={raw.id} topic={topic} scope={scope}')
    return jsonify({'success': True, 'data': raw.to_dict()})


@knowledge_wiki_bp.route('/api/wiki/upload-and-add', methods=['POST'])
@login_required
def upload_and_add():
    """直接上传文件 → file_library + raw_file 一步完成

    Form fields:
        file: 上传的文件 (必填)
        topic: str (必填)
        title: str (可选，默认用文件名)
        scope: str (可选，默认 'personal')
    """
    # 不再要求 admin — scope 权限由 can_write_scope 控制
    file_obj = request.files.get('file')
    topic = (request.form.get('topic') or '').strip()
    title = (request.form.get('title') or '').strip()

    if not file_obj or not file_obj.filename:
        return jsonify({'success': False, 'message': '请选择文件'}), 400
    if not topic:
        return jsonify({'success': False, 'message': 'topic 必填'}), 400

    try:
        storage.validate_topic(topic)
    except storage.WikiPathError as e:
        return jsonify({'success': False, 'message': str(e)}), 400

    # 非管理员只能选 admin 预定义的 topic
    if current_user.role not in ('admin', 'ceo'):
        if topic not in _get_allowed_topic_names():
            return jsonify({'success': False, 'message': '只能选择已有的分类目录'}), 403

    # 1. 上传到 file_library（SHA256 去重）
    success, result = FileManagerService.upload_file(current_user, file_obj)
    if not success:
        return jsonify({'success': False, 'message': result}), 400

    # result 是 UserFileRef.to_dict()，取 file_library_id
    fl_id = result.get('file_library_id')
    fl = FileLibrary.query.get(fl_id)
    if not fl:
        return jsonify({'success': False, 'message': '文件存储异常'}), 500

    # 2. 读取文件内容并保存到 raw 目录
    content = FileManagerService.read_file_content_auto_decompress(fl)
    if content is None:
        return jsonify({'success': False, 'message': '无法读取上传的文件内容'}), 500

    ensure_wiki_structure()

    safe_name = storage.dated_filename(fl.original_filename)
    raw_path = storage.save_raw_file(topic, safe_name, content)

    # scope 参数
    scope = (request.form.get('scope') or 'personal').strip()
    if scope not in ('personal', 'department', 'company', 'system'):
        scope = 'personal'
    from app.services.wiki.scope import can_write_scope
    if not can_write_scope(current_user, scope):
        return jsonify({'success': False, 'message': f'无权限写入 {scope} 级别'}), 403

    raw = KnowledgeRawFile(
        file_library_id=fl.id,
        topic=topic,
        raw_path=raw_path,
        title=title or fl.original_filename,
        added_by=current_user.id,
        scope=scope,
        owner_id=current_user.id,
        owner_department=current_user.department,
    )
    db.session.add(raw)
    db.session.commit()

    logger.info(f'[Wiki] upload-and-add user={current_user.id} raw_id={raw.id} topic={topic} scope={scope}')
    return jsonify({'success': True, 'data': raw.to_dict()})


@knowledge_wiki_bp.route('/api/wiki/raw-files/from-file-ref', methods=['POST'])
@login_required
def add_raw_from_file_ref():
    """从文件管理器的 UserFileRef 添加原始资料（文件管理器右键菜单用）

    Body JSON:
        user_file_ref_id: int (必填) — 文件管理器中的文件引用 ID
        topic: str (必填)
        title: str (可选)

    内部解析 file_ref → file_library_id，复用 add_raw_file 逻辑。
    权限由 scope + can_write_scope 控制，不再限制仅 admin。
    """
    data = request.get_json(silent=True) or {}
    ref_id = data.get('user_file_ref_id')
    topic = (data.get('topic') or '').strip()
    title = (data.get('title') or '').strip()

    if not ref_id or not topic:
        return jsonify({'success': False, 'message': 'user_file_ref_id 和 topic 必填'}), 400

    try:
        storage.validate_topic(topic)
    except storage.WikiPathError as e:
        return jsonify({'success': False, 'message': str(e)}), 400

    # 非管理员只能选 admin 预定义的 topic
    if current_user.role not in ('admin', 'ceo'):
        if topic not in _get_allowed_topic_names():
            return jsonify({'success': False, 'message': '只能选择已有的分类目录'}), 403

    from app.models.file_manager import UserFileRef
    ref = UserFileRef.query.get(ref_id)
    if not ref:
        return jsonify({'success': False, 'message': f'文件引用 ID {ref_id} 不存在'}), 404

    fl = FileLibrary.query.get(ref.file_library_id)
    if not fl:
        return jsonify({'success': False, 'message': '关联的 file_library 记录不存在'}), 404

    content = FileManagerService.read_file_content_auto_decompress(fl)
    if content is None:
        return jsonify({'success': False, 'message': '无法读取文件内容'}), 500

    ensure_wiki_structure()

    safe_name = storage.dated_filename(fl.original_filename)
    raw_path = storage.save_raw_file(topic, safe_name, content)

    # scope 参数
    scope = (data.get('scope') or 'personal').strip()
    if scope not in ('personal', 'department', 'company', 'system'):
        scope = 'personal'
    from app.services.wiki.scope import can_write_scope
    if not can_write_scope(current_user, scope):
        return jsonify({'success': False, 'message': f'无权限写入 {scope} 级别'}), 403

    raw = KnowledgeRawFile(
        file_library_id=fl.id,
        topic=topic,
        raw_path=raw_path,
        title=title or ref.display_name or fl.original_filename,
        added_by=current_user.id,
        scope=scope,
        owner_id=current_user.id,
        owner_department=current_user.department,
    )
    db.session.add(raw)
    db.session.commit()

    logger.info(f'[Wiki] from-file-ref user={current_user.id} ref={ref_id} → raw_id={raw.id} topic={topic} scope={scope}')

    # 异步触发 Ingest —— 不阻塞前端，编译完成后通过 Message 通知用户
    user_id = current_user.id
    app = current_app._get_current_object()
    threading.Thread(
        target=_async_ingest_and_notify,
        args=(raw.id, user_id, app),
        daemon=True,
    ).start()

    return jsonify({
        'success': True,
        'data': raw.to_dict(),
        'message': '已提交编译，完成后会收到系统通知',
    })


@knowledge_wiki_bp.route('/api/wiki/raw-files/<int:raw_id>/ingest', methods=['POST'])
@login_required
def trigger_ingest(raw_id):
    """触发 Claude Opus 编译一个原始文件。**同步**阻塞约 30-60 秒。
    权限：admin/ceo 或文件所有者可触发。
    """
    raw = KnowledgeRawFile.query.get(raw_id)
    if not raw:
        return jsonify({'success': False, 'message': '记录不存在'}), 404
    if not _is_admin() and raw.owner_id != current_user.id:
        return jsonify({'success': False, 'message': '只有文件所有者或管理员可以触发编译'}), 403

    try:
        result = compiler.ingest_raw_file(raw_id)
    except compiler.IngestError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception:
        logger.exception(f'[Wiki] ingest 失败 raw_id={raw_id}')
        return jsonify({'success': False, 'message': '编译失败，请查看服务器日志'}), 500

    return jsonify({'success': True, 'data': result})


@knowledge_wiki_bp.route('/api/wiki/raw-files/<int:raw_id>', methods=['DELETE'])
@login_required
def delete_raw_file(raw_id):
    """删除原始文件登记 + 磁盘文件。**不会删除已生成的文章**。
    权限：admin/ceo 或文件所有者可删除。
    """
    raw = KnowledgeRawFile.query.get(raw_id)
    if not raw:
        return jsonify({'success': False, 'message': '记录不存在'}), 404
    if not _is_admin() and raw.owner_id != current_user.id:
        return jsonify({'success': False, 'message': '只有文件所有者或管理员可以删除'}), 403

    try:
        storage.delete_raw_file(raw.raw_path)
    except Exception as e:
        logger.warning(f'[Wiki] 删除磁盘文件失败（继续删 DB 记录）: {e}')

    db.session.delete(raw)
    db.session.commit()
    return jsonify({'success': True, 'message': '已删除'})


# ══════════════════════════════════════════════════════════════════
# 文章浏览
# ══════════════════════════════════════════════════════════════════

@knowledge_wiki_bp.route('/api/wiki/articles', methods=['GET'])
@login_required
def list_articles():
    from app.services.wiki.scope import visible_articles_query
    topic = (request.args.get('topic') or '').strip()
    q = visible_articles_query(current_user)
    if topic:
        q = q.filter_by(topic=topic)
    items = q.order_by(KnowledgeWikiArticle.topic, KnowledgeWikiArticle.slug).all()
    return jsonify({'success': True, 'data': [a.to_dict() for a in items]})


@knowledge_wiki_bp.route('/api/wiki/articles/<int:article_id>', methods=['GET'])
@login_required
def get_article(article_id):
    from app.services.wiki.scope import visible_articles_query
    art = visible_articles_query(current_user).filter_by(id=article_id).first()
    if not art:
        return jsonify({'success': False, 'message': '文章不存在'}), 404
    return jsonify({'success': True, 'data': art.to_dict(include_content=True)})


@knowledge_wiki_bp.route('/api/wiki/articles/<int:article_id>', methods=['DELETE'])
@login_required
def delete_article(article_id):
    """删除文章（磁盘 + DB）。

    权限：admin/ceo、文章所有者、或管理同部门的部门经理。
    """
    from app.services.wiki.scope import can_manage_article

    art = KnowledgeWikiArticle.query.get(article_id)
    if not art:
        return jsonify({'success': False, 'message': '文章不存在'}), 404

    if not can_manage_article(current_user, art):
        return jsonify({'success': False, 'message': '没有权限删除此文章'}), 403

    # 删除磁盘文件
    try:
        storage.delete_article_file(art.file_path)
    except Exception as e:
        logger.warning(f'[Wiki] 删除文章磁盘文件失败（继续删 DB）: {e}')

    db.session.delete(art)
    db.session.commit()
    logger.info(f'[Wiki] user={current_user.id} 删除文章 id={article_id} title={art.title}')
    return jsonify({'success': True, 'message': '文章已删除'})


@knowledge_wiki_bp.route('/api/wiki/articles/<int:article_id>/scope', methods=['PATCH'])
@login_required
def change_article_scope(article_id):
    """调整文章 scope 等级。

    权限规则：
    - admin/ceo: 可任意调整
    - 普通用户 / 部门经理: 可在 personal ↔ department 之间直接调整自己可管理的文章
    - → company / system: 需提交晋升申请，由 admin/ceo 审批
    """
    from app.services.wiki.scope import can_manage_article

    art = KnowledgeWikiArticle.query.get(article_id)
    if not art:
        return jsonify({'success': False, 'message': '文章不存在'}), 404

    data = request.get_json(silent=True) or {}
    new_scope = data.get('scope', '').strip()
    valid_scopes = ('personal', 'department', 'company', 'system')
    if new_scope not in valid_scopes:
        return jsonify({'success': False, 'message': f'无效 scope: {new_scope}'}), 400

    if new_scope == art.scope:
        return jsonify({'success': True, 'message': '等级未变化', 'data': art.to_dict()})

    # 权限检查
    if not can_manage_article(current_user, art):
        return jsonify({'success': False, 'message': '没有权限管理此文章'}), 403

    # 非 admin/ceo：只有 company / system 需要审批，personal ↔ department 自由切换
    if current_user.role not in ('admin', 'ceo') and new_scope in ('company', 'system'):
        return jsonify({
            'success': False,
            'needs_approval': True,
            'message': '升级到公司 / 系统级别需要提交晋升申请',
        }), 403

    old_scope = art.scope
    art.scope = new_scope
    # 确保 owner 字段完整（"哪里来回哪里去"）
    if not art.owner_id:
        art.owner_id = current_user.id
    if not art.owner_department and art.owner:
        art.owner_department = art.owner.department
    db.session.commit()

    logger.info(f'[Wiki] user={current_user.id} 调整文章 id={article_id} scope: {old_scope} → {new_scope}')
    return jsonify({'success': True, 'message': f'已调整为{new_scope}级别', 'data': art.to_dict()})


@knowledge_wiki_bp.route('/api/wiki/articles/<int:article_id>/promote', methods=['POST'])
@login_required
def submit_promotion_request(article_id):
    """提交文章晋升申请。

    自动确定审核人：
    - → company: admin/ceo
    - → system: admin/ceo
    （→ department 不再需要审批，直接 PATCH scope 即可。）
    """
    try:
        from app.services.wiki.scope import visible_articles_query
        art = visible_articles_query(current_user).filter_by(id=article_id).first()
        if not art:
            return jsonify({'success': False, 'message': '文章不存在'}), 404

        data = request.get_json(silent=True) or {}
        to_scope = data.get('to_scope', '').strip()
        request_note = data.get('reason', '').strip()

        valid_scopes = ('company', 'system')
        if to_scope not in valid_scopes:
            return jsonify({'success': False, 'message': '无效的目标等级（仅 company / system 需要审批）'}), 400

        if not request_note:
            return jsonify({'success': False, 'message': '请填写申请理由'}), 400

        # 检查是否已有 pending 申请
        existing = KnowledgePromotionRequest.query.filter_by(
            article_id=article_id, status='pending'
        ).first()
        if existing:
            return jsonify({'success': False, 'message': '该文章已有待审核的晋升申请'}), 400

        # 确定审核人
        reviewer_id = _find_promotion_reviewer(to_scope, current_user)
        if not reviewer_id:
            return jsonify({'success': False, 'message': '找不到合适的审核人，请联系管理员'}), 400

        # 确保文章 owner_department 已填充
        if not art.owner_department:
            art.owner_department = current_user.department

        # 创建申请（先 flush 拿到 ID）
        req = KnowledgePromotionRequest(
            article_id=article_id,
            from_scope=art.scope,
            to_scope=to_scope,
            requested_by=current_user.id,
            request_note=request_note,
            assigned_to=reviewer_id,
        )
        db.session.add(req)
        db.session.flush()  # 分配 req.id

        # 通知审核人
        scope_labels = {'department': '部门', 'company': '公司', 'system': '系统'}
        requester_name = current_user.real_name or current_user.username
        reviewer = db.session.get(User, reviewer_id)
        reviewer_name = (reviewer.real_name or reviewer.username) if reviewer else '审核人'

        msg = Message(
            message_type='wiki_promotion_request',
            sender_id=current_user.id,
            recipient_id=reviewer_id,
            title=f'知识库晋升申请: {art.title}',
            content=f'{requester_name} 申请将「{art.title}」提升为{scope_labels.get(to_scope, to_scope)}级',
            related_object_type='wiki_promotion',
            related_object_id=article_id,
            extra_data={
                'promotion_request_id': req.id,
                'article_id': article_id,
                'article_title': art.title,
                'from_scope': art.scope,
                'to_scope': to_scope,
            },
        )
        db.session.add(msg)

        # 通知申请人（确认已提交）
        msg_self = Message(
            message_type='wiki_promotion_submitted',
            sender_id=current_user.id,
            recipient_id=current_user.id,
            title=f'晋升申请已提交',
            content=f'您的「{art.title}」晋升申请已提交给 {reviewer_name} 审核',
            related_object_type='wiki_promotion',
            related_object_id=article_id,
            extra_data={'article_id': article_id},
        )
        db.session.add(msg_self)

        db.session.commit()

        logger.info(f'[Wiki] user={current_user.id} 提交晋升申请 article={article_id} '
                    f'{art.scope}→{to_scope} reviewer={reviewer_id}')
        return jsonify({'success': True, 'message': f'申请已提交给 {reviewer_name}', 'data': req.to_dict()})
    except Exception as e:
        db.session.rollback()
        logger.error(f'[Wiki] 提交晋升申请失败: {e}', exc_info=True)
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500


@knowledge_wiki_bp.route('/api/wiki/promotion-requests/<int:request_id>', methods=['PATCH'])
@login_required
def review_promotion_request(request_id):
    """审核晋升申请（通过/拒绝）。"""
    try:
        req = KnowledgePromotionRequest.query.get(request_id)
        if not req:
            return jsonify({'success': False, 'message': '申请不存在'}), 404

        if req.status != 'pending':
            return jsonify({'success': False, 'message': '该申请已处理'}), 400

        # 只有指定审核人或 admin/ceo 可以审核
        if req.assigned_to != current_user.id and current_user.role not in ('admin', 'ceo'):
            return jsonify({'success': False, 'message': '没有审核权限'}), 403

        data = request.get_json(silent=True) or {}
        action = data.get('action', '').strip()
        review_note = data.get('review_note', '').strip()

        if action not in ('approve', 'reject'):
            return jsonify({'success': False, 'message': '无效的审核动作'}), 400

        from datetime import datetime
        from zoneinfo import ZoneInfo

        req.status = 'approved' if action == 'approve' else 'rejected'
        req.reviewed_by = current_user.id
        req.review_note = review_note
        req.reviewed_at = datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)

        # 如果通过，实际变更 scope
        art = req.article
        if action == 'approve' and art:
            old_scope = art.scope
            art.scope = req.to_scope
            # 确保 owner_department 填充（降级时自动回到原部门）
            if not art.owner_department and art.owner:
                art.owner_department = art.owner.department
            logger.info(f'[Wiki] 晋升审核通过 article={art.id} {old_scope}→{req.to_scope} by user={current_user.id}')

        # 通知申请人
        scope_labels = {'personal': '个人', 'department': '部门', 'company': '公司', 'system': '系统'}
        reviewer_name = current_user.real_name or current_user.username
        action_text = '通过' if action == 'approve' else '拒绝'
        msg = Message(
            message_type='wiki_promotion_result',
            sender_id=current_user.id,
            recipient_id=req.requested_by,
            title=f'晋升申请已{action_text}',
            content=f'{reviewer_name} 已{action_text}「{art.title}」提升为{scope_labels.get(req.to_scope, req.to_scope)}级'
                    + (f'，备注：{review_note}' if review_note else ''),
            related_object_type='wiki_promotion',
            related_object_id=art.id if art else None,
            extra_data={'article_id': art.id if art else None, 'action': action},
        )
        db.session.add(msg)
        db.session.commit()

        return jsonify({'success': True, 'message': f'已{action_text}', 'data': req.to_dict()})
    except Exception as e:
        db.session.rollback()
        logger.error(f'[Wiki] 审核晋升申请失败: {e}', exc_info=True)
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500


@knowledge_wiki_bp.route('/api/wiki/promotion-requests', methods=['GET'])
@login_required
def list_promotion_requests():
    """获取与当前用户相关的晋升申请列表。"""
    try:
        q = KnowledgePromotionRequest.query
        # 普通用户只看自己提交的和自己需要审核的
        if current_user.role not in ('admin', 'ceo'):
            q = q.filter(
                db.or_(
                    KnowledgePromotionRequest.requested_by == current_user.id,
                    KnowledgePromotionRequest.assigned_to == current_user.id,
                )
            )
        requests = q.order_by(KnowledgePromotionRequest.created_at.desc()).limit(50).all()
        return jsonify({'success': True, 'data': [r.to_dict() for r in requests]})
    except Exception as e:
        db.session.rollback()
        logger.error(f'[Wiki] 查询晋升申请失败: {e}', exc_info=True)
        return jsonify({'success': True, 'data': []})


def _find_promotion_reviewer(to_scope: str, requester) -> int | None:
    """根据目标 scope 确定审核人。

    规则：
    - department: 本部门经理（如果没有，找 admin/ceo）
    - company: admin/ceo
    - system: admin/ceo
    """
    if to_scope == 'department' and requester.department:
        # 找本部门经理
        manager = User.query.filter_by(
            department=requester.department,
            is_department_manager=True,
            is_active=True,
        ).filter(User.id != requester.id).first()
        if manager:
            return manager.id

    # company/system 或找不到部门经理 → 找 admin/ceo
    admin = User.query.filter(
        User.role.in_(['admin', 'ceo']),
        User.is_active == True,
        User.id != requester.id,
    ).first()
    if admin:
        return admin.id

    return None


@knowledge_wiki_bp.route('/api/wiki/articles/<int:article_id>/recompile', methods=['POST'])
@login_required
def recompile_article(article_id):
    """重新编译文章关联的 raw file。

    权限：admin/ceo、文章所有者、或管理同部门的部门经理。
    """
    from app.services.wiki.scope import can_manage_article

    art = KnowledgeWikiArticle.query.get(article_id)
    if not art:
        return jsonify({'success': False, 'message': '文章不存在'}), 404

    if not can_manage_article(current_user, art):
        return jsonify({'success': False, 'message': '没有权限重新编译此文章'}), 403

    raw_ids = art.source_raw_ids or []
    if not raw_ids:
        return jsonify({'success': False, 'message': '该文章没有关联的原始文件'}), 400

    # 编译第一个关联 raw file
    raw_id = raw_ids[0]
    raw = KnowledgeRawFile.query.get(raw_id)
    if not raw:
        return jsonify({'success': False, 'message': f'原始文件 raw_id={raw_id} 不存在'}), 404

    try:
        result = compiler.ingest_raw_file(raw_id)
    except compiler.IngestError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception:
        logger.exception(f'[Wiki] recompile 失败 article_id={article_id} raw_id={raw_id}')
        return jsonify({'success': False, 'message': '重新编译失败'}), 500

    return jsonify({'success': True, 'data': result})


@knowledge_wiki_bp.route('/api/wiki/tree', methods=['GET'])
@login_required
def get_tree():
    """返回 topic → [articles] 的树结构，供前端侧栏渲染。

    每篇文章带 scope/owner_name 字段，前端用于显示标签和过滤。
    """
    from app.services.wiki.scope import visible_articles_query, can_manage_article
    items = (
        visible_articles_query(current_user)
        .order_by(KnowledgeWikiArticle.topic, KnowledgeWikiArticle.slug)
        .all()
    )
    tree: dict[str, list[dict]] = {}
    for art in items:
        tree.setdefault(art.topic, []).append({
            'id': art.id,
            'slug': art.slug,
            'title': art.title,
            'summary': art.summary,
            'source_raw_ids': art.source_raw_ids or [],
            'updated_at': art.updated_at.isoformat() if art.updated_at else None,
            'scope': art.scope,
            'owner_id': art.owner_id,
            'owner_name': (art.owner.real_name or art.owner.username) if art.owner else None,
            'is_mine': art.owner_id == current_user.id,
            'can_manage': can_manage_article(current_user, art),
        })
    return jsonify({'success': True, 'data': tree})


@knowledge_wiki_bp.route('/api/wiki/topics', methods=['GET'])
@login_required
def list_topics():
    """返回 admin 预定义的 topic 列表（按 sort_order, name 排序）。

    前端上传 / 加入 Wiki 弹窗从此接口拉取可用分类。
    """
    topics = KnowledgeTopic.query.order_by(
        KnowledgeTopic.sort_order.asc(),
        KnowledgeTopic.name.asc(),
    ).all()
    # 兼容旧前端：返回纯字符串数组
    return jsonify({'success': True, 'data': [t.name for t in topics]})


@knowledge_wiki_bp.route('/api/wiki/topics/detail', methods=['GET'])
@login_required
def list_topics_detail():
    """返回 topic 详细列表（含 id / description / sort_order），供管理面板使用。"""
    topics = KnowledgeTopic.query.order_by(
        KnowledgeTopic.sort_order.asc(),
        KnowledgeTopic.name.asc(),
    ).all()
    return jsonify({'success': True, 'data': [t.to_dict() for t in topics]})


@knowledge_wiki_bp.route('/api/wiki/admin/topics', methods=['POST'])
@login_required
def create_topic():
    """管理员新建分类目录。

    Body: { name: str, description?: str, sort_order?: int }
    """
    err = _require_admin()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    description = (data.get('description') or '').strip() or None
    sort_order = int(data.get('sort_order') or 0)

    if not name:
        return jsonify({'success': False, 'message': 'name 必填'}), 400

    try:
        storage.validate_topic(name)
    except storage.WikiPathError as e:
        return jsonify({'success': False, 'message': str(e)}), 400

    if KnowledgeTopic.query.filter_by(name=name).first():
        return jsonify({'success': False, 'message': f'分类「{name}」已存在'}), 409

    try:
        topic = KnowledgeTopic(
            name=name,
            description=description,
            sort_order=sort_order,
            created_by=current_user.id,
        )
        db.session.add(topic)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.exception('[Wiki] create_topic failed')
        return jsonify({'success': False, 'message': f'创建失败: {e}'}), 500

    logger.info(f'[Wiki] user={current_user.id} 新建 topic={name}')
    return jsonify({'success': True, 'data': topic.to_dict()})


@knowledge_wiki_bp.route('/api/wiki/admin/topics/<int:topic_id>', methods=['PATCH'])
@login_required
def update_topic(topic_id):
    """管理员编辑分类目录（不允许改 name，只能改 description / sort_order）。

    Body: { description?: str, sort_order?: int }
    改 name 涉及物理目录和所有引用的迁移，暂不支持。
    """
    err = _require_admin()
    if err:
        return err

    topic = KnowledgeTopic.query.get(topic_id)
    if not topic:
        return jsonify({'success': False, 'message': '分类不存在'}), 404

    data = request.get_json(silent=True) or {}
    if 'description' in data:
        v = (data.get('description') or '').strip()
        topic.description = v or None
    if 'sort_order' in data:
        try:
            topic.sort_order = int(data.get('sort_order') or 0)
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': 'sort_order 必须是整数'}), 400

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.exception('[Wiki] update_topic failed')
        return jsonify({'success': False, 'message': f'更新失败: {e}'}), 500

    return jsonify({'success': True, 'data': topic.to_dict()})


@knowledge_wiki_bp.route('/api/wiki/admin/topics/<int:topic_id>', methods=['DELETE'])
@login_required
def delete_topic(topic_id):
    """管理员删除分类目录。仅在该分类下没有任何原始文件和文章时允许。"""
    err = _require_admin()
    if err:
        return err

    topic = KnowledgeTopic.query.get(topic_id)
    if not topic:
        return jsonify({'success': False, 'message': '分类不存在'}), 404

    raw_count = db.session.query(KnowledgeRawFile).filter_by(topic=topic.name).count()
    art_count = db.session.query(KnowledgeWikiArticle).filter_by(topic=topic.name).count()
    if raw_count or art_count:
        return jsonify({
            'success': False,
            'message': f'分类「{topic.name}」下仍有 {raw_count} 个原始文件、{art_count} 篇文章，请先清空',
        }), 409

    try:
        db.session.delete(topic)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.exception('[Wiki] delete_topic failed')
        return jsonify({'success': False, 'message': f'删除失败: {e}'}), 500

    logger.info(f'[Wiki] user={current_user.id} 删除 topic={topic.name}')
    return jsonify({'success': True})


@knowledge_wiki_bp.route('/api/wiki/index', methods=['GET'])
@login_required
def get_index():
    ensure_wiki_structure()
    return jsonify({'success': True, 'content': storage.read_index()})


# ══════════════════════════════════════════════════════════════════
# 问答
# ══════════════════════════════════════════════════════════════════

@knowledge_wiki_bp.route('/api/wiki/query', methods=['POST'])
@login_required
def query_endpoint():
    data = request.get_json(silent=True) or {}
    question = (data.get('question') or '').strip()
    topic = (data.get('topic') or '').strip() or None
    top_k = int(data.get('top_k') or 5)

    if not question:
        return jsonify({'success': False, 'message': '问题不能为空'}), 400

    try:
        result = querier.query_wiki(question, top_k=top_k, topic=topic)
    except querier.QueryError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception:
        logger.exception(f'[Wiki] query 失败: {question[:100]}')
        return jsonify({'success': False, 'message': '问答服务异常，请查看服务器日志'}), 500

    return jsonify({'success': True, 'data': result})


# ══════════════════════════════════════════════════════════════════
# 质检
# ══════════════════════════════════════════════════════════════════

@knowledge_wiki_bp.route('/api/wiki/lint', methods=['POST'])
@login_required
def lint_endpoint():
    guard = _require_admin()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    apply_fixes = bool(data.get('apply_auto_fixes'))
    topic = (data.get('topic') or '').strip() or None

    try:
        result = linter.lint_wiki(apply_auto_fixes=apply_fixes, topic=topic)
    except linter.LintError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception:
        logger.exception('[Wiki] lint 失败')
        return jsonify({'success': False, 'message': '质检服务异常，请查看服务器日志'}), 500

    return jsonify({'success': True, 'data': result})


# ══════════════════════════════════════════════════════════════════
# 文件 Wiki 状态查询（供文件管理器用）
# ══════════════════════════════════════════════════════════════════

@knowledge_wiki_bp.route('/api/wiki/file-wiki-status', methods=['POST'])
@login_required
def file_wiki_status():
    """查询一组 file_library_id 是否已在 Wiki 中（以及编译状态）。"""
    data = request.get_json(silent=True) or {}
    fl_ids = data.get('file_library_ids') or []
    if not fl_ids:
        return jsonify({'success': True, 'data': {}})

    raws = KnowledgeRawFile.query.filter(
        KnowledgeRawFile.file_library_id.in_(fl_ids)
    ).all()

    status_map = {}
    for raw in raws:
        fid = str(raw.file_library_id)
        if fid not in status_map or (raw.created_at and status_map.get(fid, {}).get('_t') and raw.created_at > status_map[fid]['_t']):
            status_map[fid] = {
                'in_wiki': raw.ingest_status == 'ingested',
                'raw_id': raw.id,
                'status': raw.ingest_status,
                'topic': raw.topic,
                '_t': raw.created_at,
            }

    for v in status_map.values():
        v.pop('_t', None)
    for fid in fl_ids:
        if str(fid) not in status_map:
            status_map[str(fid)] = {'in_wiki': False}

    return jsonify({'success': True, 'data': status_map})


# ══════════════════════════════════════════════════════════════════
# 异步编译 + 系统通知
# ══════════════════════════════════════════════════════════════════

def _async_ingest_and_notify(raw_id: int, user_id: int, app):
    """后台线程：编译 + 完成后发 PMA 系统通知。"""
    with app.app_context():
        try:
            result = compiler.ingest_raw_file(raw_id)
            ops = result.get('operations') or []
            article_count = len([o for o in ops if o.get('action') in ('create', 'update')])
            raw = db.session.get(KnowledgeRawFile, raw_id)
            title = raw.title if raw else f'raw_id={raw_id}'

            first_article_id = None
            if ops:
                art = KnowledgeWikiArticle.query.filter_by(
                    topic=ops[0].get('topic'), slug=ops[0].get('slug')
                ).first()
                if art:
                    first_article_id = art.id

            msg = Message(
                message_type='wiki_compile',
                sender_id=user_id,
                recipient_id=user_id,
                title=f'Wiki 编译完成：{title}',
                content=f'产生 {article_count} 篇文章',
                related_object_type='wiki_article',
                related_object_id=first_article_id,
                extra_data={'raw_id': raw_id, 'article_count': article_count, 'status': 'success'},
            )
            db.session.add(msg)
            db.session.commit()
            logger.info(f'[Wiki async] raw_id={raw_id} 编译成功，已通知 user_id={user_id}')

        except Exception as e:
            logger.exception(f'[Wiki async] raw_id={raw_id} 编译失败')
            try:
                raw = db.session.get(KnowledgeRawFile, raw_id)
                title = raw.title if raw else f'raw_id={raw_id}'
                msg = Message(
                    message_type='wiki_compile',
                    sender_id=user_id,
                    recipient_id=user_id,
                    title=f'Wiki 编译失败：{title}',
                    content=str(e)[:200],
                    related_object_type='wiki_raw_file',
                    related_object_id=raw_id,
                    extra_data={'raw_id': raw_id, 'status': 'error', 'error': str(e)[:500]},
                )
                db.session.add(msg)
                db.session.commit()
            except Exception:
                logger.exception(f'[Wiki async] 发送失败通知也失败了')


# ══════════════════════════════════════════════════════════════════
# 文章分享（跨部门/跨人/跨企业）
# ══════════════════════════════════════════════════════════════════

def _can_manage_shares(user, article) -> bool:
    """谁能管理分享授权：admin/ceo 或文章所有者。"""
    if user.role in ('admin', 'ceo'):
        return True
    return article.owner_id == user.id


def _serialize_grant(grant) -> dict:
    """给前端返回的授权信息，目标侧附上显示名。"""
    display_target = grant.grant_target
    if grant.grant_type == 'user':
        try:
            u = User.query.get(int(grant.grant_target))
            if u:
                display_target = u.real_name or u.username
        except (ValueError, TypeError):
            pass
    return {
        'id': grant.id,
        'grant_type': grant.grant_type,
        'grant_target': grant.grant_target,
        'display_target': display_target,
        'granted_by': grant.granted_by,
        'granter_name': (grant.granter.real_name or grant.granter.username) if grant.granter else None,
        'created_at': grant.created_at.isoformat() if grant.created_at else None,
    }


@knowledge_wiki_bp.route('/api/wiki/articles/<int:article_id>/shares', methods=['GET'])
@login_required
def list_article_shares(article_id):
    """列出文章当前的所有分享授权。"""
    art = KnowledgeWikiArticle.query.get(article_id)
    if not art:
        return jsonify({'success': False, 'message': '文章不存在'}), 404
    if not _can_manage_shares(current_user, art):
        return jsonify({'success': False, 'message': '没有权限管理此文章的分享'}), 403

    grants = KnowledgeShareGrant.query.filter_by(article_id=article_id).order_by(
        KnowledgeShareGrant.created_at.desc()
    ).all()
    return jsonify({'success': True, 'data': [_serialize_grant(g) for g in grants]})


@knowledge_wiki_bp.route('/api/wiki/articles/<int:article_id>/shares', methods=['POST'])
@login_required
def add_article_share(article_id):
    """新增一条分享授权。

    请求体：{ grant_type: 'user'|'department'|'company', grant_target: str }
    - grant_type=user: grant_target 为 user_id 字符串
    - grant_type=department: grant_target 为部门名
    - grant_type=company: grant_target 为企业名 (users.company_name)
    """
    art = KnowledgeWikiArticle.query.get(article_id)
    if not art:
        return jsonify({'success': False, 'message': '文章不存在'}), 404
    if not _can_manage_shares(current_user, art):
        return jsonify({'success': False, 'message': '没有权限管理此文章的分享'}), 403

    data = request.get_json(silent=True) or {}
    grant_type = (data.get('grant_type') or '').strip()
    grant_target = (data.get('grant_target') or '').strip()

    if grant_type not in ('user', 'department', 'company'):
        return jsonify({'success': False, 'message': '无效的授权类型'}), 400
    if not grant_target:
        return jsonify({'success': False, 'message': '请指定授权目标'}), 400

    # 校验目标存在
    if grant_type == 'user':
        try:
            uid = int(grant_target)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': '用户 ID 无效'}), 400
        target_user = User.query.get(uid)
        if not target_user:
            return jsonify({'success': False, 'message': '用户不存在'}), 400
        # 不允许分享给自己
        if target_user.id == art.owner_id:
            return jsonify({'success': False, 'message': '文章所有者已拥有访问权限'}), 400
    elif grant_type == 'department':
        exists = db.session.query(User.id).filter_by(department=grant_target).first()
        if not exists:
            return jsonify({'success': False, 'message': '部门不存在'}), 400
    elif grant_type == 'company':
        exists = db.session.query(User.id).filter_by(company_name=grant_target).first()
        if not exists:
            return jsonify({'success': False, 'message': '企业不存在'}), 400

    # 去重
    dup = KnowledgeShareGrant.query.filter_by(
        article_id=article_id,
        grant_type=grant_type,
        grant_target=grant_target,
    ).first()
    if dup:
        return jsonify({'success': False, 'message': '该目标已有授权'}), 400

    grant = KnowledgeShareGrant(
        article_id=article_id,
        grant_type=grant_type,
        grant_target=grant_target,
        granted_by=current_user.id,
    )
    db.session.add(grant)
    db.session.commit()

    logger.info(
        f'[Wiki] user={current_user.id} 给文章 id={article_id} 新增分享 '
        f'type={grant_type} target={grant_target}'
    )
    return jsonify({'success': True, 'message': '授权已添加', 'data': _serialize_grant(grant)})


@knowledge_wiki_bp.route(
    '/api/wiki/articles/<int:article_id>/shares/<int:grant_id>',
    methods=['DELETE'],
)
@login_required
def delete_article_share(article_id, grant_id):
    """撤销一条分享授权。"""
    art = KnowledgeWikiArticle.query.get(article_id)
    if not art:
        return jsonify({'success': False, 'message': '文章不存在'}), 404
    if not _can_manage_shares(current_user, art):
        return jsonify({'success': False, 'message': '没有权限管理此文章的分享'}), 403

    grant = KnowledgeShareGrant.query.filter_by(id=grant_id, article_id=article_id).first()
    if not grant:
        return jsonify({'success': False, 'message': '授权记录不存在'}), 404

    db.session.delete(grant)
    db.session.commit()

    logger.info(f'[Wiki] user={current_user.id} 撤销文章 id={article_id} 的分享 grant_id={grant_id}')
    return jsonify({'success': True, 'message': '授权已撤销'})


@knowledge_wiki_bp.route('/api/wiki/share-targets', methods=['GET'])
@login_required
def search_share_targets():
    """搜索可选的分享目标（给前端下拉补全用）。

    参数：
      - type: 'user' | 'department' | 'company'
      - q: 搜索关键字（模糊匹配）
      - limit: 返回条数上限（默认 20）
    """
    target_type = (request.args.get('type') or '').strip()
    q = (request.args.get('q') or '').strip()
    try:
        limit = min(int(request.args.get('limit', 20)), 50)
    except (ValueError, TypeError):
        limit = 20

    if target_type not in ('user', 'department', 'company'):
        return jsonify({'success': False, 'message': '无效的 type'}), 400

    results = []
    if target_type == 'user':
        query = User.query.filter(User.is_active == True)  # noqa: E712
        if q:
            like = f'%{q}%'
            query = query.filter(
                db.or_(
                    User.username.ilike(like),
                    User.real_name.ilike(like),
                )
            )
        users = query.order_by(User.real_name.nullslast(), User.username).limit(limit).all()
        results = [
            {
                'value': str(u.id),
                'label': u.real_name or u.username,
                'sub': f"{u.department or ''} {u.company_name or ''}".strip(),
            }
            for u in users
        ]
    elif target_type == 'department':
        query = db.session.query(User.department).filter(User.department.isnot(None))
        if q:
            query = query.filter(User.department.ilike(f'%{q}%'))
        rows = query.distinct().order_by(User.department).limit(limit).all()
        results = [{'value': r[0], 'label': r[0], 'sub': ''} for r in rows if r[0]]
    elif target_type == 'company':
        query = db.session.query(User.company_name).filter(User.company_name.isnot(None))
        if q:
            query = query.filter(User.company_name.ilike(f'%{q}%'))
        rows = query.distinct().order_by(User.company_name).limit(limit).all()
        results = [{'value': r[0], 'label': r[0], 'sub': ''} for r in rows if r[0]]

    return jsonify({'success': True, 'data': results})
