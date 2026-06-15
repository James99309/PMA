"""季度绩效结算单(2026-06-13)Phase 1:数据模型

performance_settlements:HR 发起的季度绩效结算,经上级+总经理审批,
通过后折算绩效薪资并锁定该季度薪资绩效部分。
设计:docs/plans/2026-06-13-quarterly-perf-settlement-design.md

幂等:CREATE TABLE IF NOT EXISTS。

Revision ID: perf_settlement_20260613
Revises: user_probation_20260613
Create Date: 2026-06-13
"""
from alembic import op

revision = 'perf_settlement_20260613'
down_revision = 'user_probation_20260613'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS performance_settlements (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            year INTEGER NOT NULL,
            quarter INTEGER NOT NULL,
            score NUMERIC(6,2),
            base_amount NUMERIC(15,2),
            settled_amount NUMERIC(15,2),
            score_snapshot JSON,
            status VARCHAR(20) DEFAULT 'pending',
            is_locked BOOLEAN DEFAULT FALSE,
            initiated_by INTEGER REFERENCES users(id),
            approval_instance_id INTEGER,
            settled_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            CONSTRAINT uq_perf_settlement UNIQUE (user_id, year, quarter)
        );
        CREATE INDEX IF NOT EXISTS idx_perf_settlement_user ON performance_settlements (user_id, year);
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS performance_settlements;")
