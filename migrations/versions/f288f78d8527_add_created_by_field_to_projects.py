
"""add_created_by_field_to_projects

Revision ID: f288f78d8527
Revises: add_project_created_by_field
Create Date: 2025-10-01 16:28:01.580899

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f288f78d8527'
down_revision = 'add_project_created_by_field'
branch_labels = None
depends_on = None


def upgrade():
    # 添加 created_by 字段
    op.add_column('projects', sa.Column('created_by', sa.Integer(), nullable=True))

    # 用 owner_id 填充 created_by
    op.execute('UPDATE projects SET created_by = owner_id WHERE created_by IS NULL')

    # 设置 NOT NULL 约束
    op.alter_column('projects', 'created_by', nullable=False)

    # 添加外键约束
    op.create_foreign_key('projects_created_by_fkey', 'projects', 'users', ['created_by'], ['id'])


def downgrade():
    # 删除外键约束
    op.drop_constraint('projects_created_by_fkey', 'projects', type_='foreignkey')

    # 删除字段
    op.drop_column('projects', 'created_by')