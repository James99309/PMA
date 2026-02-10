"""add quotation_confirmation_tasks table

Revision ID: ad89878592c6
Revises: a1b2c3d4e502
Create Date: 2026-02-09 22:18:01.285037

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'ad89878592c6'
down_revision = 'a1b2c3d4e502'
branch_labels = None
depends_on = None


def upgrade():
    # 使用原生SQL的IF NOT EXISTS确保NAS部署安全
    op.execute("""
        CREATE TABLE IF NOT EXISTS quotation_confirmation_tasks (
            id SERIAL PRIMARY KEY,
            quotation_id INTEGER NOT NULL REFERENCES quotations(id),
            assignee_id INTEGER NOT NULL REFERENCES users(id),
            requester_id INTEGER NOT NULL REFERENCES users(id),
            message TEXT,
            due_date TIMESTAMP,
            status VARCHAR(20) DEFAULT 'pending',
            confirmed_at TIMESTAMP,
            workitem_id INTEGER REFERENCES work_items(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_qct_quotation_id ON quotation_confirmation_tasks(quotation_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_qct_assignee_id ON quotation_confirmation_tasks(assignee_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_qct_status ON quotation_confirmation_tasks(status)")


def downgrade():
    op.execute("DROP TABLE IF EXISTS quotation_confirmation_tasks")
