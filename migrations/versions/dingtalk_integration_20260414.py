"""add dingtalk integration tables + work_items sync fields

Revision ID: dingtalk_integration_20260414
Revises: cli_tbl_tier2_20260413
Create Date: 2026-04-14

新增:
- dingtalk_user_mappings: PMA 用户 ↔ 钉钉 userid 映射
- dingtalk_sync_queue:    WorkItem → 钉钉日程的异步推送队列
- work_items 追加 3 列:   dingtalk_event_id, dingtalk_synced_at, sync_source

幂等: 所有 DDL 使用 IF NOT EXISTS / IF EXISTS。
"""
from alembic import op


revision = 'dingtalk_integration_20260414'
down_revision = 'cli_tbl_tier2_20260413'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS dingtalk_user_mappings (
            id SERIAL PRIMARY KEY,
            pma_user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
            dingtalk_userid VARCHAR(128) NOT NULL UNIQUE,
            dingtalk_unionid VARCHAR(128),
            matched_by VARCHAR(20) DEFAULT 'mobile',
            note VARCHAR(200),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            last_verified_at TIMESTAMP
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_dingtalk_user_mappings_userid ON dingtalk_user_mappings (dingtalk_userid);")

    op.execute("""
        CREATE TABLE IF NOT EXISTS dingtalk_sync_queue (
            id SERIAL PRIMARY KEY,
            work_item_id INTEGER REFERENCES work_items(id),
            action VARCHAR(20) NOT NULL,
            dingtalk_event_id VARCHAR(128),
            dingtalk_userid VARCHAR(128),
            payload_snapshot TEXT,
            status VARCHAR(20) DEFAULT 'pending',
            attempts INTEGER DEFAULT 0,
            last_error TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            next_retry_at TIMESTAMP
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_dingtalk_sync_queue_work_item_id ON dingtalk_sync_queue (work_item_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_dingtalk_sync_queue_created_at ON dingtalk_sync_queue (created_at);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_dingtalk_sync_queue_status_retry ON dingtalk_sync_queue (status, next_retry_at);")

    op.execute("ALTER TABLE work_items ADD COLUMN IF NOT EXISTS dingtalk_event_id VARCHAR(128);")
    op.execute("ALTER TABLE work_items ADD COLUMN IF NOT EXISTS dingtalk_synced_at TIMESTAMP;")
    op.execute("ALTER TABLE work_items ADD COLUMN IF NOT EXISTS sync_source VARCHAR(20);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_work_items_dingtalk_event_id ON work_items (dingtalk_event_id);")


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_work_items_dingtalk_event_id;")
    op.execute("ALTER TABLE work_items DROP COLUMN IF EXISTS sync_source;")
    op.execute("ALTER TABLE work_items DROP COLUMN IF EXISTS dingtalk_synced_at;")
    op.execute("ALTER TABLE work_items DROP COLUMN IF EXISTS dingtalk_event_id;")
    op.execute("DROP TABLE IF EXISTS dingtalk_sync_queue;")
    op.execute("DROP TABLE IF EXISTS dingtalk_user_mappings;")
