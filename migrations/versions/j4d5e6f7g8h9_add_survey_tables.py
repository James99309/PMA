"""add manual entry tables and metrics definitions

Revision ID: j4d5e6f7g8h9
Revises: i3c4d5e6f7g8
Create Date: 2026-02-25 09:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'j4d5e6f7g8h9'
down_revision = 'i3c4d5e6f7g8'
branch_labels = None
depends_on = None


def upgrade():
    # 绩效手工录入表（IF NOT EXISTS 防止 db.create_all() 已建表时报错）
    op.execute("""
        CREATE TABLE IF NOT EXISTS performance_manual_entries (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            metric_code VARCHAR(50) NOT NULL,
            year INTEGER NOT NULL,
            period_type VARCHAR(10) NOT NULL,
            period INTEGER NOT NULL,
            value NUMERIC(10, 2),
            note VARCHAR(500),
            entered_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP WITHOUT TIME ZONE,
            updated_at TIMESTAMP WITHOUT TIME ZONE,
            CONSTRAINT uq_manual_entry UNIQUE (user_id, metric_code, year, period_type, period)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_manual_entries_user_id ON performance_manual_entries (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_manual_entries_metric_code ON performance_manual_entries (metric_code)")

    # 绩效手工录入附件表
    op.execute("""
        CREATE TABLE IF NOT EXISTS performance_manual_attachments (
            id SERIAL PRIMARY KEY,
            entry_id INTEGER NOT NULL REFERENCES performance_manual_entries(id) ON DELETE CASCADE,
            filename VARCHAR(255) NOT NULL,
            storage_path VARCHAR(500) NOT NULL,
            file_size INTEGER DEFAULT 0,
            file_type VARCHAR(100),
            uploaded_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP WITHOUT TIME ZONE
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_manual_attachments_entry_id ON performance_manual_attachments (entry_id)")

    # 指标定义表新增录入频率字段
    op.execute("""
        ALTER TABLE performance_metrics_definition
        ADD COLUMN IF NOT EXISTS entry_frequency VARCHAR(10) DEFAULT 'monthly'
    """)

    # 插入辅助指标定义数据
    op.execute("""
        INSERT INTO performance_metrics_definition (metric_code, metric_name, metric_category, data_type, default_unit, is_system_metric, is_active, entry_frequency)
        SELECT v.metric_code, v.metric_name, v.metric_category, v.data_type, v.default_unit, v.is_system_metric, v.is_active, v.entry_frequency
        FROM (VALUES
            ('se_response_rate', '响应时效达标率', '技术支持', 'percentage', '%', true, true, 'monthly'),
            ('se_training_count', '培训次数', '技术支持', 'count', '次', true, true, 'monthly'),
            ('se_content_output', '内容产出', '技术支持', 'count', '份', true, true, 'monthly'),
            ('se_satisfaction', '满意度评分', '技术支持', 'score', '分', true, true, 'quarterly')
        ) AS v(metric_code, metric_name, metric_category, data_type, default_unit, is_system_metric, is_active, entry_frequency)
        WHERE NOT EXISTS (
            SELECT 1 FROM performance_metrics_definition pmd WHERE pmd.metric_code = v.metric_code
        )
    """)

    # 更新已有记录的 entry_frequency
    op.execute("""
        UPDATE performance_metrics_definition SET entry_frequency = 'quarterly'
        WHERE metric_code = 'se_satisfaction' AND (entry_frequency IS NULL OR entry_frequency = 'monthly')
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS performance_manual_attachments")
    op.execute("DROP TABLE IF EXISTS performance_manual_entries")
    op.execute("ALTER TABLE performance_metrics_definition DROP COLUMN IF EXISTS entry_frequency")
    op.execute("""
        DELETE FROM performance_metrics_definition
        WHERE metric_code IN ('se_response_rate', 'se_training_count', 'se_content_output', 'se_satisfaction')
    """)
