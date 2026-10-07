"""课程考核题库 + 学习进度 + 课程考核设置 + 小源开关(纯新增表)

零停机:update.sh 先重启 app 再 upgrade,其间启动 create_all 只建新表不加列,
故本迁移只新增表,不 ALTER 任何已有表。

Revision ID: course_exam_bank_20261007
Revises: announcement_banner_20260913
"""
from alembic import op
import sqlalchemy as sa

revision = 'course_exam_bank_20261007'
down_revision = 'announcement_banner_20260913'
branch_labels = None
depends_on = None


def _has_table(name):
    return name in sa.inspect(op.get_bind()).get_table_names()


def upgrade():
    # 幂等:生产 app 启动 create_all 可能已抢先建表
    if not _has_table('course_quiz_questions'):
        op.create_table(
            'course_quiz_questions',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('course_key', sa.String(80), nullable=False),
            sa.Column('qtype', sa.String(10), nullable=False),
            sa.Column('difficulty', sa.Integer(), nullable=False, server_default='2'),
            sa.Column('ai_difficulty', sa.Integer()),
            sa.Column('question', sa.Text(), nullable=False),
            sa.Column('options', sa.JSON()),
            sa.Column('answer', sa.JSON(), nullable=False),
            sa.Column('explain', sa.Text()),
            sa.Column('source_page', sa.Integer()),
            sa.Column('status', sa.String(10), nullable=False, server_default='active'),
            sa.Column('origin', sa.String(10), nullable=False, server_default='ai'),
            sa.Column('review_note', sa.Text()),
            sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id')),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_course_quiz_questions_status', 'course_quiz_questions', ['status'])
        op.create_index('ix_cqq_course_status', 'course_quiz_questions', ['course_key', 'status'])
    if not _has_table('course_learning_progress'):
        op.create_table(
            'course_learning_progress',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('course_key', sa.String(80), nullable=False),
            sa.Column('page_seconds', sa.JSON(), nullable=False),
            sa.Column('last_ping_at', sa.DateTime()),
            sa.Column('unlocked_at', sa.DateTime()),
            sa.Column('score', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('current_question_id', sa.Integer()),
            sa.Column('current_option_order', sa.JSON()),
            sa.Column('current_answered', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('current_result', sa.JSON()),
            sa.Column('passed_at', sa.DateTime()),
            sa.Column('perfect_at', sa.DateTime()),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_course_learning_progress_course_key', 'course_learning_progress', ['course_key'])
        op.create_index('ix_clp_user_course', 'course_learning_progress', ['user_id', 'course_key'], unique=True)
    if not _has_table('course_exam_settings'):
        op.create_table(
            'course_exam_settings',
            sa.Column('course_key', sa.String(80), primary_key=True),
            sa.Column('min_read_seconds', sa.Integer()),
            sa.Column('generating_since', sa.DateTime()),
            sa.Column('generating_token', sa.DateTime()),
            sa.Column('generating_by', sa.Integer(), sa.ForeignKey('users.id')),
            sa.Column('updated_by', sa.Integer(), sa.ForeignKey('users.id')),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
    if not _has_table('learning_buddy_prefs'):
        op.create_table(
            'learning_buddy_prefs',
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), primary_key=True),
            sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )


def downgrade():
    for name in ('learning_buddy_prefs', 'course_exam_settings',
                 'course_learning_progress', 'course_quiz_questions'):
        if _has_table(name):
            op.drop_table(name)
