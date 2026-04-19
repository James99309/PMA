"""Points system rebalance: source_id Integer→String, update behavior configs

Revision ID: points_rebalance_20260420
Revises: task_subtask_assoc_20260419
Create Date: 2026-04-20
"""
from alembic import op
import sqlalchemy as sa

revision = 'points_rebalance_20260420'
down_revision = 'task_subtask_assoc_20260419'
branch_labels = None
depends_on = None


def upgrade():
    # 1. source_id: Integer → String(128)
    #    先将已有整数值转为字符串，再改列类型
    op.alter_column(
        'points_transaction', 'source_id',
        existing_type=sa.Integer(),
        type_=sa.String(128),
        existing_nullable=True,
        postgresql_using='source_id::text',
    )

    # 2. 更新行为配置积分值（由 sync_registry_to_db 在启动时同步）
    #    此处做迁移级更新确保数据库即时生效
    conn = op.get_bind()
    updates = [
        ('wiki_create',                  5,  None),
        ('wiki_share',                  10,  None),
        ('wiki_cited',                   5,    50),
        ('wiki_cited_qa',                5,    30),
        ('task_create',                  5,    15),
        ('subtask_complete',            15,  None),
        ('task_complete',               30,  None),
        ('task_review_approved',         5,  None),
        ('project_approver_acted',       5,  None),
        ('pricing_order_approver_acted', 5,  None),
        ('contact_create',              10,    30),
        ('action_record_create',        10,    30),
    ]
    for code, pts, cap in updates:
        conn.execute(
            sa.text(
                "UPDATE points_behavior_config "
                "SET points = :pts, daily_cap = :cap "
                "WHERE behavior_code = :code"
            ),
            {'pts': pts, 'cap': cap, 'code': code},
        )


def downgrade():
    # Revert source_id back to Integer (data loss for non-numeric values)
    op.alter_column(
        'points_transaction', 'source_id',
        existing_type=sa.String(128),
        type_=sa.Integer(),
        existing_nullable=True,
        postgresql_using='CASE WHEN source_id ~ \'^[0-9]+$\' THEN source_id::integer ELSE NULL END',
    )
