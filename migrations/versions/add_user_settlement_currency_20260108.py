"""add settlement_currency field to users table

Revision ID: add_user_settlement_currency_20260108
Revises:
Create Date: 2026-01-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_user_settlement_currency_20260108'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """添加用户结算货币字段"""
    # 检查字段是否已存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]

    if 'settlement_currency' not in columns:
        op.add_column('users', sa.Column('settlement_currency', sa.String(10), nullable=True))
        print("Added settlement_currency column to users table")
    else:
        print("settlement_currency column already exists in users table")


def downgrade():
    """移除用户结算货币字段"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]

    if 'settlement_currency' in columns:
        op.drop_column('users', 'settlement_currency')
        print("Removed settlement_currency column from users table")
