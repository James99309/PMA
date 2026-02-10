"""add tasks, task_attachments, task_replies tables

Revision ID: add_tasks_tables_20260210
Revises: ad89878592c6
Create Date: 2026-02-10 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_tasks_tables_20260210'
down_revision = 'ad89878592c6'
branch_labels = None
depends_on = None


def upgrade():
    # tasks 表
    op.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            creator_id INTEGER NOT NULL REFERENCES users(id),
            assignee_id INTEGER NOT NULL REFERENCES users(id),
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            priority VARCHAR(20) NOT NULL DEFAULT 'normal',
            due_date TIMESTAMP,
            calendar_date DATE,
            completed_at TIMESTAMP,
            external_link VARCHAR(500),
            external_link_label VARCHAR(100),
            project_id INTEGER REFERENCES projects(id),
            quotation_id INTEGER REFERENCES quotations(id),
            customer_id INTEGER REFERENCES companies(id),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            is_deleted BOOLEAN DEFAULT FALSE
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_tasks_status ON tasks (status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tasks_calendar_date ON tasks (calendar_date)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tasks_assignee_status ON tasks (assignee_id, status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tasks_creator_status ON tasks (creator_id, status)")

    # task_attachments 表
    op.execute("""
        CREATE TABLE IF NOT EXISTS task_attachments (
            id SERIAL PRIMARY KEY,
            task_id INTEGER NOT NULL REFERENCES tasks(id),
            filename VARCHAR(255) NOT NULL,
            storage_path VARCHAR(500) NOT NULL,
            file_size INTEGER DEFAULT 0,
            file_type VARCHAR(100),
            uploaded_by INTEGER NOT NULL REFERENCES users(id),
            created_at TIMESTAMP DEFAULT NOW(),
            is_deleted BOOLEAN DEFAULT FALSE
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_task_attachments_task_id ON task_attachments (task_id)")

    # task_replies 表
    op.execute("""
        CREATE TABLE IF NOT EXISTS task_replies (
            id SERIAL PRIMARY KEY,
            task_id INTEGER NOT NULL REFERENCES tasks(id),
            author_id INTEGER NOT NULL REFERENCES users(id),
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            is_deleted BOOLEAN DEFAULT FALSE
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_task_replies_task_id ON task_replies (task_id)")


def downgrade():
    op.execute("DROP TABLE IF EXISTS task_replies")
    op.execute("DROP TABLE IF EXISTS task_attachments")
    op.execute("DROP TABLE IF EXISTS tasks")
