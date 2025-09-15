
"""Add gantt chart support tables for milestones, attachments, reviews and dependencies

Revision ID: d43fb253b20c
Revises: cefa7a906d3f
Create Date: 2025-09-07 23:29:03.768762

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd43fb253b20c'
down_revision = 'cefa7a906d3f'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 创建dev_product_milestones表 - 里程碑表
    op.create_table(
        'dev_product_milestones',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('stage_key', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('planned_start_date', sa.DateTime(), nullable=True),
        sa.Column('planned_end_date', sa.DateTime(), nullable=True),
        sa.Column('actual_start_date', sa.DateTime(), nullable=True),
        sa.Column('actual_end_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='planned'),
        sa.Column('progress', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('priority', sa.Integer(), nullable=True, server_default='3'),
        sa.Column('order_index', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['product_id'], ['dev_products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. 创建stage_dependencies表 - 阶段依赖关系表  
    op.create_table(
        'stage_dependencies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('predecessor_stage', sa.String(length=50), nullable=False),
        sa.Column('successor_stage', sa.String(length=50), nullable=False),
        sa.Column('dependency_type', sa.String(length=30), nullable=True, server_default='finish_to_start'),
        sa.Column('lag_days', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['product_id'], ['dev_products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. 创建stage_attachments表 - 阶段附件表
    op.create_table(
        'stage_attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('stage_key', sa.String(length=50), nullable=False),
        sa.Column('milestone_id', sa.Integer(), nullable=True),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('file_type', sa.String(length=50), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('description', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['milestone_id'], ['dev_product_milestones.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['dev_products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. 创建stage_reviews表 - 阶段评审记录表
    op.create_table(
        'stage_reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('stage_key', sa.String(length=50), nullable=False),
        sa.Column('review_type', sa.String(length=50), nullable=True, server_default='stage_gate'),
        sa.Column('reviewer_id', sa.Integer(), nullable=True),
        sa.Column('review_result', sa.String(length=30), nullable=True),
        sa.Column('review_comments', sa.Text(), nullable=True),
        sa.Column('review_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['product_id'], ['dev_products.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. 为dev_products表添加增强字段
    op.add_column('dev_products', sa.Column('planned_duration_days', sa.Integer(), nullable=True))
    op.add_column('dev_products', sa.Column('actual_duration_days', sa.Integer(), nullable=True))  
    op.add_column('dev_products', sa.Column('risk_level', sa.String(length=20), nullable=True, server_default='medium'))
    op.add_column('dev_products', sa.Column('baseline_date', sa.DateTime(), nullable=True))
    op.add_column('dev_products', sa.Column('milestone_count', sa.Integer(), nullable=True, server_default='0'))

    # 6. 创建索引优化查询性能
    op.create_index('idx_milestones_product_stage', 'dev_product_milestones', ['product_id', 'stage_key'])
    op.create_index('idx_milestones_dates', 'dev_product_milestones', ['planned_start_date', 'planned_end_date'])
    op.create_index('idx_dependencies_product', 'stage_dependencies', ['product_id'])
    op.create_index('idx_dependencies_stages', 'stage_dependencies', ['predecessor_stage', 'successor_stage'])
    op.create_index('idx_attachments_product_stage', 'stage_attachments', ['product_id', 'stage_key'])
    op.create_index('idx_reviews_product_stage', 'stage_reviews', ['product_id', 'stage_key'])


def downgrade():
    # 删除索引
    op.drop_index('idx_reviews_product_stage', table_name='stage_reviews')
    op.drop_index('idx_attachments_product_stage', table_name='stage_attachments')
    op.drop_index('idx_dependencies_stages', table_name='stage_dependencies')
    op.drop_index('idx_dependencies_product', table_name='stage_dependencies')
    op.drop_index('idx_milestones_dates', table_name='dev_product_milestones')
    op.drop_index('idx_milestones_product_stage', table_name='dev_product_milestones')
    
    # 删除dev_products表的新增字段
    op.drop_column('dev_products', 'milestone_count')
    op.drop_column('dev_products', 'baseline_date')
    op.drop_column('dev_products', 'risk_level')
    op.drop_column('dev_products', 'actual_duration_days')
    op.drop_column('dev_products', 'planned_duration_days')
    
    # 删除新建的表
    op.drop_table('stage_reviews')
    op.drop_table('stage_attachments')
    op.drop_table('stage_dependencies')
    op.drop_table('dev_product_milestones')