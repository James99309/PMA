
"""补上任何本地新增模型变更

Revision ID: c1308c08d0c9
Revises: 5055ec5e2171
Create Date: 2025-06-02 20:21:17.089477

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c1308c08d0c9'
down_revision = '5055ec5e2171'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('project_rating_records', schema=None) as batch_op:
        batch_op.drop_index('idx_project_rating_records_created_at')
        batch_op.drop_index('idx_project_rating_records_project_id')
        batch_op.drop_index('idx_project_rating_records_user_id')

    op.drop_table('project_rating_records')
    with op.batch_alter_table('approval_instance', schema=None) as batch_op:
        batch_op.alter_column('template_snapshot',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               comment='创建时的模板快照',
               existing_nullable=True)
        batch_op.alter_column('template_version',
               existing_type=sa.VARCHAR(length=50),
               comment='模板版本号',
               existing_nullable=True)

    with op.batch_alter_table('approval_record', schema=None) as batch_op:
        batch_op.alter_column('step_id',
               existing_type=sa.INTEGER(),
               nullable=False,
               existing_comment='流程步骤ID')

    with op.batch_alter_table('approval_step', schema=None) as batch_op:
        batch_op.alter_column('action_type',
               existing_type=sa.VARCHAR(length=50),
               comment='步骤动作类型，如 authorization, quotation_approval',
               existing_comment='步骤动作类型，如 authorization',
               existing_nullable=True)

    with op.batch_alter_table('project_scoring_config', schema=None) as batch_op:
        batch_op.drop_index('idx_scoring_config_category')
        batch_op.drop_constraint('project_scoring_config_category_field_name_key', type_='unique')
        batch_op.create_unique_constraint('uq_scoring_config', ['category', 'field_name'])

    with op.batch_alter_table('project_scoring_records', schema=None) as batch_op:
        batch_op.drop_index('idx_scoring_records_category')
        batch_op.drop_index('idx_scoring_records_project')
        batch_op.drop_constraint('project_scoring_records_project_id_category_field_name_key', type_='unique')
        batch_op.create_unique_constraint('uq_scoring_record_with_user', ['project_id', 'category', 'field_name', 'awarded_by'])

    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.alter_column('rating',
               existing_type=sa.NUMERIC(precision=2, scale=1),
               type_=sa.Integer(),
               comment=None,
               existing_comment='项目评分(1-5星)，NULL表示未评分',
               existing_nullable=True)

    with op.batch_alter_table('quotations', schema=None) as batch_op:
        batch_op.alter_column('is_locked',
               existing_type=sa.BOOLEAN(),
               comment=None,
               existing_comment='是否被锁定',
               existing_nullable=True,
               existing_server_default=sa.text('false'))
        batch_op.alter_column('lock_reason',
               existing_type=sa.VARCHAR(length=200),
               comment=None,
               existing_comment='锁定原因',
               existing_nullable=True)
        batch_op.alter_column('locked_by',
               existing_type=sa.INTEGER(),
               comment=None,
               existing_comment='锁定人ID',
               existing_nullable=True)
        batch_op.alter_column('locked_at',
               existing_type=postgresql.TIMESTAMP(),
               comment=None,
               existing_comment='锁定时间',
               existing_nullable=True)
        batch_op.drop_index('idx_quotations_is_locked')
        batch_op.drop_index('idx_quotations_locked_by')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('quotations', schema=None) as batch_op:
        batch_op.create_index('idx_quotations_locked_by', ['locked_by'], unique=False)
        batch_op.create_index('idx_quotations_is_locked', ['is_locked'], unique=False)
        batch_op.alter_column('locked_at',
               existing_type=postgresql.TIMESTAMP(),
               comment='锁定时间',
               existing_nullable=True)
        batch_op.alter_column('locked_by',
               existing_type=sa.INTEGER(),
               comment='锁定人ID',
               existing_nullable=True)
        batch_op.alter_column('lock_reason',
               existing_type=sa.VARCHAR(length=200),
               comment='锁定原因',
               existing_nullable=True)
        batch_op.alter_column('is_locked',
               existing_type=sa.BOOLEAN(),
               comment='是否被锁定',
               existing_nullable=True,
               existing_server_default=sa.text('false'))

    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.alter_column('rating',
               existing_type=sa.Integer(),
               type_=sa.NUMERIC(precision=2, scale=1),
               comment='项目评分(1-5星)，NULL表示未评分',
               existing_nullable=True)

    with op.batch_alter_table('project_scoring_records', schema=None) as batch_op:
        batch_op.drop_constraint('uq_scoring_record_with_user', type_='unique')
        batch_op.create_unique_constraint('project_scoring_records_project_id_category_field_name_key', ['project_id', 'category', 'field_name'])
        batch_op.create_index('idx_scoring_records_project', ['project_id'], unique=False)
        batch_op.create_index('idx_scoring_records_category', ['category'], unique=False)

    with op.batch_alter_table('project_scoring_config', schema=None) as batch_op:
        batch_op.drop_constraint('uq_scoring_config', type_='unique')
        batch_op.create_unique_constraint('project_scoring_config_category_field_name_key', ['category', 'field_name'])
        batch_op.create_index('idx_scoring_config_category', ['category'], unique=False)

    with op.batch_alter_table('approval_step', schema=None) as batch_op:
        batch_op.alter_column('action_type',
               existing_type=sa.VARCHAR(length=50),
               comment='步骤动作类型，如 authorization',
               existing_comment='步骤动作类型，如 authorization, quotation_approval',
               existing_nullable=True)

    with op.batch_alter_table('approval_record', schema=None) as batch_op:
        batch_op.alter_column('step_id',
               existing_type=sa.INTEGER(),
               nullable=True,
               existing_comment='流程步骤ID')

    with op.batch_alter_table('approval_instance', schema=None) as batch_op:
        batch_op.alter_column('template_version',
               existing_type=sa.VARCHAR(length=50),
               comment=None,
               existing_comment='模板版本号',
               existing_nullable=True)
        batch_op.alter_column('template_snapshot',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               comment=None,
               existing_comment='创建时的模板快照',
               existing_nullable=True)

    op.create_table('project_rating_records',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False, comment='记录ID'),
    sa.Column('project_id', sa.INTEGER(), autoincrement=False, nullable=False, comment='项目ID'),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False, comment='用户ID'),
    sa.Column('rating', sa.INTEGER(), autoincrement=False, nullable=False, comment='评分值(固定为1星)'),
    sa.Column('created_at', postgresql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=True, comment='创建时间'),
    sa.Column('updated_at', postgresql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=True, comment='更新时间'),
    sa.CheckConstraint('rating = 1', name='project_rating_records_rating_check'),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], name='project_rating_records_project_id_fkey', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='project_rating_records_user_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='project_rating_records_pkey'),
    sa.UniqueConstraint('project_id', 'user_id', name='project_rating_records_project_id_user_id_key'),
    comment='项目评分记录表'
    )
    with op.batch_alter_table('project_rating_records', schema=None) as batch_op:
        batch_op.create_index('idx_project_rating_records_user_id', ['user_id'], unique=False)
        batch_op.create_index('idx_project_rating_records_project_id', ['project_id'], unique=False)
        batch_op.create_index('idx_project_rating_records_created_at', ['created_at'], unique=False)

    # ### end Alembic commands ###