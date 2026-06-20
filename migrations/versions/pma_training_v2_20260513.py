"""add pma-training v2 tables

为 pma-training skill v2.0 加 4 张表:
- training_module_state
- training_quiz_attempt
- training_streak
- training_application_submission

非破坏性: 只新增表, 不动任何现有表/字段.

Revision ID: a1b2c3d4e5f6
Revises: d2f5c9b7e3a1
Create Date: 2026-05-13
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'pma_training_v2_20260513'
down_revision = 'd2f5c9b7e3a1'
branch_labels = None
depends_on = None


def upgrade():
    # ── 1. training_module_state ────────────────────────────────────────────
    op.create_table(
        'training_module_state',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('course_slug', sa.String(length=80), nullable=False),
        sa.Column('module_slug', sa.String(length=80), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='not_started'),
        sa.Column('current_chapter', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('current_section', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('chapters_passed', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('final_exam_score', sa.Integer(), nullable=True),
        sa.Column('final_exam_passed_at', sa.DateTime(), nullable=True),
        sa.Column('badge_awarded', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_training_module_state_user_id', 'training_module_state', ['user_id'])
    op.create_index('ix_training_module_state_course_slug', 'training_module_state', ['course_slug'])
    op.create_index('ix_training_module_state_module_slug', 'training_module_state', ['module_slug'])
    op.create_index('ix_training_module_state_status', 'training_module_state', ['status'])
    op.create_index('ix_tms_user_course_module', 'training_module_state',
                    ['user_id', 'course_slug', 'module_slug'], unique=True)
    op.create_index('ix_tms_user_status', 'training_module_state', ['user_id', 'status'])

    # ── 2. training_quiz_attempt ────────────────────────────────────────────
    op.create_table(
        'training_quiz_attempt',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('course_slug', sa.String(length=80), nullable=False),
        sa.Column('module_slug', sa.String(length=80), nullable=False),
        sa.Column('chapter', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.String(length=64), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(length=20), nullable=True),
        sa.Column('user_answer', sa.Text(), nullable=True),
        sa.Column('correct_answer', sa.Text(), nullable=True),
        sa.Column('is_correct', sa.Boolean(), nullable=False),
        sa.Column('attempted_at', sa.DateTime(), nullable=False),
        sa.Column('scheduled_review_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_count', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_training_quiz_attempt_user_id', 'training_quiz_attempt', ['user_id'])
    op.create_index('ix_training_quiz_attempt_module_slug', 'training_quiz_attempt', ['module_slug'])
    op.create_index('ix_training_quiz_attempt_question_id', 'training_quiz_attempt', ['question_id'])
    op.create_index('ix_training_quiz_attempt_attempted_at', 'training_quiz_attempt', ['attempted_at'])
    op.create_index('ix_training_quiz_attempt_scheduled_review_at',
                    'training_quiz_attempt', ['scheduled_review_at'])
    op.create_index('ix_tqa_user_due_review', 'training_quiz_attempt',
                    ['user_id', 'scheduled_review_at'])

    # ── 3. training_streak ──────────────────────────────────────────────────
    op.create_table(
        'training_streak',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('last_learned_date', sa.Date(), nullable=True),
        sa.Column('current_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('longest_streak', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('streak_freeze_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id'),
    )

    # ── 4. training_application_submission ──────────────────────────────────
    op.create_table(
        'training_application_submission',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('course_slug', sa.String(length=80), nullable=False),
        sa.Column('module_slug', sa.String(length=80), nullable=False),
        sa.Column('task_id', sa.String(length=80), nullable=False),
        sa.Column('submission_text', sa.Text(), nullable=False),
        sa.Column('ai_feedback', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=False),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('reviewer_comment', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_training_application_submission_user_id',
                    'training_application_submission', ['user_id'])
    op.create_index('ix_training_application_submission_module_slug',
                    'training_application_submission', ['module_slug'])


def downgrade():
    op.drop_index('ix_training_application_submission_module_slug',
                  table_name='training_application_submission')
    op.drop_index('ix_training_application_submission_user_id',
                  table_name='training_application_submission')
    op.drop_table('training_application_submission')

    op.drop_table('training_streak')

    op.drop_index('ix_tqa_user_due_review', table_name='training_quiz_attempt')
    op.drop_index('ix_training_quiz_attempt_scheduled_review_at', table_name='training_quiz_attempt')
    op.drop_index('ix_training_quiz_attempt_attempted_at', table_name='training_quiz_attempt')
    op.drop_index('ix_training_quiz_attempt_question_id', table_name='training_quiz_attempt')
    op.drop_index('ix_training_quiz_attempt_module_slug', table_name='training_quiz_attempt')
    op.drop_index('ix_training_quiz_attempt_user_id', table_name='training_quiz_attempt')
    op.drop_table('training_quiz_attempt')

    op.drop_index('ix_tms_user_status', table_name='training_module_state')
    op.drop_index('ix_tms_user_course_module', table_name='training_module_state')
    op.drop_index('ix_training_module_state_status', table_name='training_module_state')
    op.drop_index('ix_training_module_state_module_slug', table_name='training_module_state')
    op.drop_index('ix_training_module_state_course_slug', table_name='training_module_state')
    op.drop_index('ix_training_module_state_user_id', table_name='training_module_state')
    op.drop_table('training_module_state')
