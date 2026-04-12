"""create wiki knowledge base tables (knowledge_raw_files + knowledge_wiki_articles)

Revision ID: wiki_tables_20260409
Revises: drop_rag_20260409
Create Date: 2026-04-09

Context
-------
新增基于 Karpathy LLM Wiki 方案的两张表：
- knowledge_raw_files: 原始文件登记表（磁盘文件的数据库索引）
- knowledge_wiki_articles: Wiki 文章元数据，正文存磁盘 Markdown

在 knowledge_wiki_articles 上建立 PostgreSQL GIN 全文检索索引，
作为 Wiki 查询（Phase 6 querier.py）的检索基础，替代向量检索。

幂等性
-------
PMA 在 app 启动时会调用 db.create_all()，表可能已由 SQLAlchemy 先行创建。
所以这份 migration 全部用 CREATE TABLE IF NOT EXISTS / CREATE INDEX IF NOT EXISTS
写成幂等形式，确保 create_all() 和 alembic 都能安全共存。

参见实施方案 docs/plans/2026-04-09-wiki-knowledge-base.md 的 Phase 2。
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'wiki_tables_20260409'
down_revision = 'drop_rag_20260409'
branch_labels = None
depends_on = None


def upgrade():
    # ── knowledge_raw_files ─────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_raw_files (
            id SERIAL PRIMARY KEY,
            file_library_id INTEGER NOT NULL REFERENCES file_library(id),
            topic VARCHAR(100) NOT NULL,
            raw_path VARCHAR(500) NOT NULL,
            title VARCHAR(500) NOT NULL,
            ingest_status VARCHAR(20) NOT NULL DEFAULT 'pending',
            ingest_error TEXT,
            ingested_at TIMESTAMP WITHOUT TIME ZONE,
            added_by INTEGER NOT NULL REFERENCES users(id),
            created_at TIMESTAMP WITHOUT TIME ZONE
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_knowledge_raw_files_file_library_id "
               "ON knowledge_raw_files (file_library_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_knowledge_raw_files_topic "
               "ON knowledge_raw_files (topic)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_knowledge_raw_files_ingest_status "
               "ON knowledge_raw_files (ingest_status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_knowledge_raw_topic_status "
               "ON knowledge_raw_files (topic, ingest_status)")

    # ── knowledge_wiki_articles ────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_wiki_articles (
            id SERIAL PRIMARY KEY,
            topic VARCHAR(100) NOT NULL,
            slug VARCHAR(200) NOT NULL,
            title VARCHAR(500) NOT NULL,
            file_path VARCHAR(500) NOT NULL UNIQUE,
            summary TEXT,
            content_length INTEGER DEFAULT 0,
            source_raw_ids JSON,
            outbound_refs JSON,
            last_compiled_at TIMESTAMP WITHOUT TIME ZONE,
            compile_model VARCHAR(100),
            created_at TIMESTAMP WITHOUT TIME ZONE,
            updated_at TIMESTAMP WITHOUT TIME ZONE
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_knowledge_wiki_articles_topic "
               "ON knowledge_wiki_articles (topic)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_wiki_article_topic_slug "
               "ON knowledge_wiki_articles (topic, slug)")

    # PG 全文检索 GIN 索引 —— title + summary
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_wiki_article_fts ON knowledge_wiki_articles
        USING GIN (to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(summary, '')))
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_wiki_article_fts")
    op.execute("DROP INDEX IF EXISTS ix_wiki_article_topic_slug")
    op.execute("DROP INDEX IF EXISTS ix_knowledge_wiki_articles_topic")
    op.execute("DROP TABLE IF EXISTS knowledge_wiki_articles")

    op.execute("DROP INDEX IF EXISTS ix_knowledge_raw_topic_status")
    op.execute("DROP INDEX IF EXISTS ix_knowledge_raw_files_ingest_status")
    op.execute("DROP INDEX IF EXISTS ix_knowledge_raw_files_topic")
    op.execute("DROP INDEX IF EXISTS ix_knowledge_raw_files_file_library_id")
    op.execute("DROP TABLE IF EXISTS knowledge_raw_files")
