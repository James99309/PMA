"""add knowledge_topics table (wiki topic 主数据)

Revision ID: wiki_topics_20260413
Revises: wiki_scope_20260412
Create Date: 2026-04-13

Context
-------
Wiki Phase 2.1：引入 knowledge_topics 主数据表，解决 "topic 需要 admin 预定义、
不依赖是否已有文章" 的问题。非 admin 上传时从本表取可选分类列表。

幂等性
-------
使用 CREATE TABLE IF NOT EXISTS，和 db.create_all() 安全共存。
"""
from alembic import op


revision = 'wiki_topics_20260413'
down_revision = 'wiki_scope_20260412'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_topics (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            description VARCHAR(500),
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_knowledge_topics_name ON knowledge_topics (name);")


def downgrade():
    op.execute("DROP TABLE IF EXISTS knowledge_topics;")
