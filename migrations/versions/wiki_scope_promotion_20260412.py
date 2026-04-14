"""add wiki scope columns, promotion_requests and share_grants tables

Revision ID: wiki_scope_20260412
Revises: wiki_tables_20260409
Create Date: 2026-04-12

Context
-------
为 Wiki 知识库添加 scope 分级权限支持：
- knowledge_raw_files: 新增 scope, owner_id, owner_department 列
- knowledge_wiki_articles: 新增 scope, owner_id, owner_department 列
- knowledge_promotion_requests: 晋升/降级审批申请表（新建）
- knowledge_share_grants: 跨部门/跨人分享授权表（新建）

幂等性
-------
全部用 IF NOT EXISTS / IF EXISTS，确保和 db.create_all() 安全共存。
"""
from alembic import op


revision = 'wiki_scope_20260412'
down_revision = 'wiki_tables_20260409'
branch_labels = None
depends_on = None


def upgrade():
    # ── 为 knowledge_raw_files 添加 scope 列 ──
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE knowledge_raw_files ADD COLUMN scope VARCHAR(20) NOT NULL DEFAULT 'personal';
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE knowledge_raw_files ADD COLUMN owner_id INTEGER REFERENCES users(id);
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE knowledge_raw_files ADD COLUMN owner_department VARCHAR(100);
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$
    """)
    # 回填：owner_id 默认 = added_by
    op.execute("""
        UPDATE knowledge_raw_files SET owner_id = added_by WHERE owner_id IS NULL
    """)
    # 设为 NOT NULL
    op.execute("""
        ALTER TABLE knowledge_raw_files ALTER COLUMN owner_id SET NOT NULL
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_knowledge_raw_files_scope ON knowledge_raw_files (scope)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_knowledge_raw_files_owner_department ON knowledge_raw_files (owner_department)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_knowledge_raw_scope_dept ON knowledge_raw_files (scope, owner_department)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_knowledge_raw_scope_owner ON knowledge_raw_files (scope, owner_id)")

    # ── 为 knowledge_wiki_articles 添加 scope 列 ──
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE knowledge_wiki_articles ADD COLUMN scope VARCHAR(20) NOT NULL DEFAULT 'personal';
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE knowledge_wiki_articles ADD COLUMN owner_id INTEGER REFERENCES users(id);
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$
    """)
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE knowledge_wiki_articles ADD COLUMN owner_department VARCHAR(100);
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$
    """)
    # 回填：从关联的 raw file 继承 owner_id，或用 admin (id=1) 兜底
    op.execute("""
        UPDATE knowledge_wiki_articles a
        SET owner_id = COALESCE(
            (SELECT r.owner_id FROM knowledge_raw_files r
             WHERE r.id = (a.source_raw_ids->>0)::int LIMIT 1),
            1
        )
        WHERE a.owner_id IS NULL
    """)
    op.execute("""
        ALTER TABLE knowledge_wiki_articles ALTER COLUMN owner_id SET NOT NULL
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_knowledge_wiki_articles_scope ON knowledge_wiki_articles (scope)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_knowledge_wiki_articles_owner_department ON knowledge_wiki_articles (owner_department)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_wiki_article_scope_dept ON knowledge_wiki_articles (scope, owner_department)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_wiki_article_scope_owner ON knowledge_wiki_articles (scope, owner_id)")

    # ── knowledge_promotion_requests ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_promotion_requests (
            id SERIAL PRIMARY KEY,
            article_id INTEGER NOT NULL REFERENCES knowledge_wiki_articles(id),
            from_scope VARCHAR(20) NOT NULL,
            to_scope VARCHAR(20) NOT NULL,
            requested_by INTEGER NOT NULL REFERENCES users(id),
            request_note TEXT,
            assigned_to INTEGER REFERENCES users(id),
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            reviewed_by INTEGER REFERENCES users(id),
            review_note TEXT,
            reviewed_at TIMESTAMP WITHOUT TIME ZONE,
            created_at TIMESTAMP WITHOUT TIME ZONE
        )
    """)
    # 补丁：如果表已由 db.create_all() 创建但缺少 assigned_to 列
    op.execute("""
        DO $$ BEGIN
            ALTER TABLE knowledge_promotion_requests ADD COLUMN assigned_to INTEGER REFERENCES users(id);
        EXCEPTION WHEN duplicate_column THEN NULL;
        END $$
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_promotion_article ON knowledge_promotion_requests (article_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_promotion_status ON knowledge_promotion_requests (status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_promotion_assigned_status ON knowledge_promotion_requests (assigned_to, status)")

    # ── knowledge_share_grants ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_share_grants (
            id SERIAL PRIMARY KEY,
            article_id INTEGER NOT NULL REFERENCES knowledge_wiki_articles(id),
            grant_type VARCHAR(20) NOT NULL,
            grant_target VARCHAR(100) NOT NULL,
            granted_by INTEGER NOT NULL REFERENCES users(id),
            created_at TIMESTAMP WITHOUT TIME ZONE
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_share_grant_article ON knowledge_share_grants (article_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_share_grant_target ON knowledge_share_grants (grant_type, grant_target)")


def downgrade():
    op.execute("DROP TABLE IF EXISTS knowledge_share_grants")
    op.execute("DROP TABLE IF EXISTS knowledge_promotion_requests")

    # 移除 knowledge_wiki_articles 的 scope 列
    op.execute("DROP INDEX IF EXISTS ix_wiki_article_scope_owner")
    op.execute("DROP INDEX IF EXISTS ix_wiki_article_scope_dept")
    op.execute("ALTER TABLE knowledge_wiki_articles DROP COLUMN IF EXISTS owner_department")
    op.execute("ALTER TABLE knowledge_wiki_articles DROP COLUMN IF EXISTS owner_id")
    op.execute("ALTER TABLE knowledge_wiki_articles DROP COLUMN IF EXISTS scope")

    # 移除 knowledge_raw_files 的 scope 列
    op.execute("DROP INDEX IF EXISTS ix_knowledge_raw_scope_owner")
    op.execute("DROP INDEX IF EXISTS ix_knowledge_raw_scope_dept")
    op.execute("ALTER TABLE knowledge_raw_files DROP COLUMN IF EXISTS owner_department")
    op.execute("ALTER TABLE knowledge_raw_files DROP COLUMN IF EXISTS owner_id")
    op.execute("ALTER TABLE knowledge_raw_files DROP COLUMN IF EXISTS scope")
