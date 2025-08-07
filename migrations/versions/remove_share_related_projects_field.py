"""Remove unused share_related_projects field from companies table

Revision ID: remove_share_related_projects
Revises: add_universal_sharing_fields
Create Date: 2025-08-07 10:56:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'remove_share_related_projects'
down_revision = 'add_sharing_support_20250807'
branch_labels = None
depends_on = None

def upgrade():
    # 删除不再使用的 share_related_projects 字段（如果存在）
    # 先检查字段是否存在，避免在云端环境中因字段不存在而导致迁移失败
    connection = op.get_bind()
    result = connection.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'companies' AND column_name = 'share_related_projects'
    """))
    
    if result.fetchone():
        # 字段存在，可以安全删除
        op.drop_column('companies', 'share_related_projects')

def downgrade():
    # 恢复 share_related_projects 字段
    op.add_column('companies', sa.Column('share_related_projects', sa.Boolean(), nullable=False, server_default='false'))