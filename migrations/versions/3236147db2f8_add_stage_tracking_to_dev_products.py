
"""Add stage tracking to dev_products

Revision ID: 3236147db2f8
Revises: create_approval_branch_condition_table
Create Date: 2025-09-07 13:41:40.299493

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '3236147db2f8'
down_revision = 'create_approval_branch_condition_table'
branch_labels = None
depends_on = None


def upgrade():
    # 添加阶段跟踪字段到dev_products表
    op.add_column('dev_products', sa.Column('stage_history', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('dev_products', sa.Column('stage_description', sa.Text(), nullable=True))
    
    # 数据迁移：基于现有status字段生成初始的stage_history
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE dev_products SET stage_history = 
        CASE 
            WHEN status = '调研中' THEN 
                jsonb_build_array(
                    jsonb_build_object(
                        'stage', 'research',
                        'startDate', created_at::text,
                        'endDate', null,
                        'user_id', created_by,
                        'description', '初始状态：调研中'
                    )
                )
            WHEN status = '立项中' THEN 
                jsonb_build_array(
                    jsonb_build_object(
                        'stage', 'planning',
                        'startDate', created_at::text,
                        'endDate', null,
                        'user_id', created_by,
                        'description', '初始状态：立项中'
                    )
                )
            WHEN status = '研发中' THEN 
                jsonb_build_array(
                    jsonb_build_object(
                        'stage', 'development',
                        'startDate', created_at::text,
                        'endDate', null,
                        'user_id', created_by,
                        'description', '初始状态：研发中'
                    )
                )
            WHEN status = '申请入库' THEN 
                jsonb_build_array(
                    jsonb_build_object(
                        'stage', 'apply_storage',
                        'startDate', created_at::text,
                        'endDate', null,
                        'user_id', created_by,
                        'description', '初始状态：申请入库'
                    )
                )
            WHEN status = '已入库' THEN 
                jsonb_build_array(
                    jsonb_build_object(
                        'stage', 'stored',
                        'startDate', created_at::text,
                        'endDate', null,
                        'user_id', created_by,
                        'description', '初始状态：已入库'
                    )
                )
            ELSE 
                jsonb_build_array(
                    jsonb_build_object(
                        'stage', 'research',
                        'startDate', created_at::text,
                        'endDate', null,
                        'user_id', created_by,
                        'description', '初始状态：调研中（默认）'
                    )
                )
        END
        WHERE stage_history IS NULL
    """))


def downgrade():
    # 移除阶段跟踪字段
    op.drop_column('dev_products', 'stage_description')
    op.drop_column('dev_products', 'stage_history')