"""drop legacy RAG tables (knowledge_chunks + knowledge_documents + knowledge_document_tags)

Revision ID: drop_rag_20260409
Revises: cli_perm_20260411
Create Date: 2026-04-09

Context
-------
PMA 知识库从向量 RAG 方案迁移到 Karpathy LLM Wiki 模式。

- knowledge_chunks / knowledge_documents / knowledge_document_tags 是旧 RAG 方案的存储结构，
  此次迁移一次性删除（没有生产数据）。
- knowledge_tags 暂时保留，未来可能被 Wiki 模块作为文章分类复用。
- 新的 Wiki 模型（knowledge_raw_files / knowledge_wiki_articles）在后续迁移中创建。

参见实施方案 docs/plans/2026-04-09-wiki-knowledge-base.md 的 Phase 1。
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'drop_rag_20260409'
down_revision = 'cli_perm_20260411'
branch_labels = None
depends_on = None


def upgrade():
    # 先删依赖 knowledge_documents 的表
    op.execute("DROP TABLE IF EXISTS knowledge_chunks CASCADE")
    op.execute("DROP TABLE IF EXISTS knowledge_document_tags CASCADE")
    op.execute("DROP TABLE IF EXISTS knowledge_documents CASCADE")
    # knowledge_tags 保留


def downgrade():
    # 不提供回滚：旧 RAG 数据已失效，恢复表结构没有意义
    raise NotImplementedError(
        "drop_rag_20260409 不支持 downgrade；如需恢复旧 RAG 结构请从 a1b2c3d4e5f6 重建"
    )
