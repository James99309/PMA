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

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

from app import db
from app.models.file_manager import FileLibrary
from app.models.knowledge import KnowledgeRawFile, KnowledgeWikiArticle
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


# ══════════════════════════════════════════════════════════════════
# 前端页面
# ══════════════════════════════════════════════════════════════════

@knowledge_wiki_bp.route('/wiki')
@login_required
def wiki_page():
    """Wiki 主页面 —— 侧栏目录 + 正文 + 问答区"""
    ensure_wiki_structure()
    return render_template('knowledge/tw_wiki.html', is_admin=_is_admin())


# ══════════════════════════════════════════════════════════════════
# 原始文件管理
# ══════════════════════════════════════════════════════════════════

@knowledge_wiki_bp.route('/api/wiki/raw-files', methods=['GET'])
@login_required
def list_raw_files():
    topic = (request.args.get('topic') or '').strip()
    q = KnowledgeRawFile.query
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
    """
    guard = _require_admin()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    fl_id = data.get('file_library_id')
    topic = (data.get('topic') or '').strip()
    title = (data.get('title') or '').strip()

    if not fl_id or not topic:
        return jsonify({'success': False, 'message': 'file_library_id 和 topic 必填'}), 400

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

    raw = KnowledgeRawFile(
        file_library_id=fl.id,
        topic=topic,
        raw_path=raw_path,
        title=title or fl.original_filename,
        added_by=current_user.id,
    )
    db.session.add(raw)
    db.session.commit()
    logger.info(f'[Wiki] user={current_user.id} 新增 raw_file id={raw.id} topic={topic}')
    return jsonify({'success': True, 'data': raw.to_dict()})


@knowledge_wiki_bp.route('/api/wiki/raw-files/<int:raw_id>/ingest', methods=['POST'])
@login_required
def trigger_ingest(raw_id):
    """触发 Claude Opus 编译一个原始文件。**同步**阻塞约 30-60 秒。"""
    guard = _require_admin()
    if guard:
        return guard

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
    """删除原始文件登记 + 磁盘文件。**不会删除已生成的文章**。"""
    guard = _require_admin()
    if guard:
        return guard

    raw = KnowledgeRawFile.query.get(raw_id)
    if not raw:
        return jsonify({'success': False, 'message': '记录不存在'}), 404

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
    topic = (request.args.get('topic') or '').strip()
    q = KnowledgeWikiArticle.query
    if topic:
        q = q.filter_by(topic=topic)
    items = q.order_by(KnowledgeWikiArticle.topic, KnowledgeWikiArticle.slug).all()
    return jsonify({'success': True, 'data': [a.to_dict() for a in items]})


@knowledge_wiki_bp.route('/api/wiki/articles/<int:article_id>', methods=['GET'])
@login_required
def get_article(article_id):
    art = KnowledgeWikiArticle.query.get(article_id)
    if not art:
        return jsonify({'success': False, 'message': '文章不存在'}), 404
    return jsonify({'success': True, 'data': art.to_dict(include_content=True)})


@knowledge_wiki_bp.route('/api/wiki/tree', methods=['GET'])
@login_required
def get_tree():
    """返回 topic → [articles] 的树结构，供前端侧栏渲染。"""
    items = (
        KnowledgeWikiArticle.query
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
            'updated_at': art.updated_at.isoformat() if art.updated_at else None,
        })
    return jsonify({'success': True, 'data': tree})


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
