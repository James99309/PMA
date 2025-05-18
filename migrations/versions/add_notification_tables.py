"""添加通知系统相关表

Revision ID: add_notification_tables
Revises: 
Create Date: 2025-05-17

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'add_notification_tables'
down_revision = None  # 根据实际情况修改
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    # 创建事件注册表（幂等）
    if 'event_registry' not in inspector.get_table_names():
        op.create_table(
            'event_registry',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('event_key', sa.String(50), nullable=False),
            sa.Column('label_zh', sa.String(100), nullable=False),
            sa.Column('label_en', sa.String(100), nullable=False), 
            sa.Column('default_enabled', sa.Boolean(), default=True),
            sa.Column('enabled', sa.Boolean(), default=True),
            sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
            sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('event_key', name='uq_event_registry_event_key')
        )
    # 创建用户事件订阅表（幂等）
    if 'user_event_subscriptions' not in inspector.get_table_names():
        op.create_table(
            'user_event_subscriptions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('target_user_id', sa.Integer(), nullable=False),
            sa.Column('event_id', sa.Integer(), nullable=False),
            sa.Column('enabled', sa.Boolean(), default=True),
            sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
            sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.ForeignKeyConstraint(['target_user_id'], ['users.id']),
            sa.ForeignKeyConstraint(['event_id'], ['event_registry.id']),
            sa.UniqueConstraint('user_id', 'target_user_id', 'event_id', name='uq_user_target_event')
        )
    # 插入初始事件类型数据（仅在表存在且无数据时插入）
    if 'event_registry' in inspector.get_table_names():
        conn = op.get_bind()
        result = conn.execute(sa.text('SELECT COUNT(*) FROM event_registry'))
        count = result.scalar()
        if count == 0:
            op.bulk_insert(
                sa.table(
                    'event_registry',
                    sa.Column('event_key', sa.String(50)),
                    sa.Column('label_zh', sa.String(100)),
                    sa.Column('label_en', sa.String(100)),
                    sa.Column('default_enabled', sa.Boolean()),
                    sa.Column('enabled', sa.Boolean()),
                    sa.Column('created_at', sa.DateTime()),
                    sa.Column('updated_at', sa.DateTime())
                ),
                [
                    {
                        'event_key': 'project_status_updated',
                        'label_zh': '项目阶段变更',
                        'label_en': 'Project Stage Changed',
                        'default_enabled': True,
                        'enabled': True,
                        'created_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    },
                    {
                        'event_key': 'project_created',
                        'label_zh': '创建新项目',
                        'label_en': 'New Project Created',
                        'default_enabled': True,
                        'enabled': True,
                        'created_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    },
                    {
                        'event_key': 'quotation_created',
                        'label_zh': '创建报价单',
                        'label_en': 'New Quotation Created',
                        'default_enabled': True,
                        'enabled': True,
                        'created_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    },
                    {
                        'event_key': 'quotation_updated',
                        'label_zh': '修改报价单',
                        'label_en': 'Quotation Updated',
                        'default_enabled': True,
                        'enabled': True,
                        'created_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    },
                    {
                        'event_key': 'quotation_deleted',
                        'label_zh': '删除报价单',
                        'label_en': 'Quotation Deleted',
                        'default_enabled': True,
                        'enabled': True,
                        'created_at': datetime.utcnow(),
                        'updated_at': datetime.utcnow()
                    }
                ]
            )


def downgrade():
    op.drop_table('user_event_subscriptions')
    op.drop_table('event_registry') 