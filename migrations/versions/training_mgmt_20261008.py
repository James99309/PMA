"""培训管理:课程开放模式 / 指定学员 / 题库审核人(纯新增表)

零停机:update.sh 先重启 app 再 upgrade,其间启动 create_all 只建新表不加列,
故本迁移只新增表,不 ALTER 任何已有表;每张表 _has_table 幂等。

Revision ID: training_mgmt_20261008
Revises: course_exam_bank_20261007
"""
from alembic import op
import sqlalchemy as sa

revision = 'training_mgmt_20261008'
down_revision = 'course_exam_bank_20261007'
branch_labels = None
depends_on = None


def _has_table(name):
    return name in sa.inspect(op.get_bind()).get_table_names()


def upgrade():
    # 幂等:生产 app 启动 create_all 可能已抢先建表
    if not _has_table('course_access'):
        op.create_table(
            'course_access',
            sa.Column('course_key', sa.String(80), primary_key=True),
            sa.Column('mode', sa.String(12), nullable=False, server_default='open'),
            sa.Column('updated_by', sa.Integer(), sa.ForeignKey('users.id')),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
    if not _has_table('course_enrollments'):
        op.create_table(
            'course_enrollments',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('course_key', sa.String(80), nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('source', sa.String(12), nullable=False, server_default='user'),
            sa.Column('source_detail', sa.String(100)),
            sa.Column('added_by', sa.Integer(), sa.ForeignKey('users.id')),
            sa.Column('added_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_course_enrollments_user_id', 'course_enrollments', ['user_id'])
        op.create_index('ux_course_enroll', 'course_enrollments', ['course_key', 'user_id'], unique=True)
    if not _has_table('course_reviewers'):
        op.create_table(
            'course_reviewers',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('course_key', sa.String(80), nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('added_by', sa.Integer(), sa.ForeignKey('users.id')),
            sa.Column('added_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_course_reviewers_user_id', 'course_reviewers', ['user_id'])
        op.create_index('ux_course_reviewer', 'course_reviewers', ['course_key', 'user_id'], unique=True)


def downgrade():
    for name in ('course_reviewers', 'course_enrollments', 'course_access'):
        if _has_table(name):
            op.drop_table(name)
