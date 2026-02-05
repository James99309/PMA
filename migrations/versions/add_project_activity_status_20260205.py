"""添加项目6级活跃度状态字段

Revision ID: add_project_activity_status_20260205
Revises: lock_signed_projects_20260205
Create Date: 2026-02-05 10:00:00.000000

变更内容：
  - 添加 activity_status 列（String(20), nullable=False, server_default='normal'）
  - 扩展 activity_reason 从 String(50) 到 String(100)
  - 数据回填：is_active=True → 'normal'，is_active=False → 'churned'
  - 添加索引 ix_projects_activity_status
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_project_activity_status_20260205'
down_revision = 'lock_signed_projects_20260205'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 添加 activity_status 列
    op.add_column('projects', sa.Column('activity_status', sa.String(20), nullable=False, server_default='normal'))

    # 2. 扩展 activity_reason 列长度
    op.alter_column('projects', 'activity_reason',
                     existing_type=sa.String(50),
                     type_=sa.String(100),
                     existing_nullable=True)

    # 3. 数据回填：根据现有 is_active 值设置 activity_status
    conn = op.get_bind()
    # is_active=False 的项目设为 churned
    result = conn.execute(sa.text("""
        UPDATE projects SET activity_status = 'churned'
        WHERE is_active = false
    """))
    print(f'✅ 已将 {result.rowcount} 个非活跃项目的 activity_status 设为 churned')

    # is_active=True 的保持默认值 normal
    result2 = conn.execute(sa.text("""
        SELECT COUNT(*) FROM projects WHERE is_active = true
    """))
    count = result2.scalar()
    print(f'ℹ️  {count} 个活跃项目的 activity_status 保持为 normal（待批量计算后更新为精确状态）')

    # 4. 添加索引
    op.create_index('ix_projects_activity_status', 'projects', ['activity_status'])


def downgrade():
    # 删除索引
    op.drop_index('ix_projects_activity_status', table_name='projects')

    # 回滚 activity_reason 列长度
    op.alter_column('projects', 'activity_reason',
                     existing_type=sa.String(100),
                     type_=sa.String(50),
                     existing_nullable=True)

    # 删除 activity_status 列
    op.drop_column('projects', 'activity_status')
