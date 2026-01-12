"""Add approval external token table

Revision ID: add_approval_external_token_table_20260111
Revises:
Create Date: 2026-01-11

新增表:
- approval_external_tokens: 审批外部访问令牌表
  用于允许外部人员（无需登录）访问特定的审批步骤表单
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_approval_external_token_table_20260111'
down_revision = 'add_order_module_tables_20260110'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'approval_external_tokens' not in existing_tables:
        op.create_table('approval_external_tokens',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('token', sa.String(64), unique=True, nullable=False, index=True),

            # 关联信息
            sa.Column('step_id', sa.Integer(), sa.ForeignKey('approval_step.id'), nullable=True),
            sa.Column('instance_id', sa.Integer(), sa.ForeignKey('approval_instance.id'), nullable=True),
            sa.Column('object_type', sa.String(50), nullable=False),
            sa.Column('object_id', sa.Integer(), nullable=False),

            # 表单信息
            sa.Column('form_id', sa.String(50), nullable=True),

            # 有效期控制
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('max_uses', sa.Integer(), default=1),
            sa.Column('use_count', sa.Integer(), default=0),

            # 使用记录
            sa.Column('used_at', sa.DateTime(), nullable=True),
            sa.Column('used_ip', sa.String(50), nullable=True),
            sa.Column('submitted_at', sa.DateTime(), nullable=True),
            sa.Column('submitted_by_name', sa.String(100), nullable=True),

            # 元数据
            sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('notes', sa.Text(), nullable=True),
        )


def downgrade():
    op.drop_table('approval_external_tokens')
