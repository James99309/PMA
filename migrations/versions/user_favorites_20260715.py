"""个人关注(收藏)通用表 user_favorites

Revision ID: user_favorites_20260715
Revises: interactive_courses_20260628
Create Date: 2026-07-15

幂等实现:app/__init__.py 启动时会无条件 create_all,新表可能已被抢先建好,
非幂等的 create_table 会在部署时撞 DuplicateTable 并让整批迁移回滚。
"""
from alembic import op
import sqlalchemy as sa

revision = 'user_favorites_20260715'
down_revision = 'interactive_courses_20260628'
branch_labels = None
depends_on = None


def _has_table(name):
    return sa.inspect(op.get_bind()).has_table(name)


def _index_names(table):
    insp = sa.inspect(op.get_bind())
    return {ix['name'] for ix in insp.get_indexes(table)}


def upgrade():
    if not _has_table('user_favorites'):
        op.create_table(
            'user_favorites',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('object_type', sa.String(length=32), nullable=False),
            sa.Column('object_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False,
                      server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id', 'object_type', 'object_id',
                                name='uq_user_favorite_object'),
        )
    if 'ix_user_favorites_user_type' not in _index_names('user_favorites'):
        op.create_index('ix_user_favorites_user_type', 'user_favorites',
                        ['user_id', 'object_type'])


def downgrade():
    if _has_table('user_favorites'):
        op.drop_index('ix_user_favorites_user_type', table_name='user_favorites')
        op.drop_table('user_favorites')
