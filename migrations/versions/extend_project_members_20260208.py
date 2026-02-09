"""extend project_members with source, workitem ref, first_associated_at and unique constraint

Revision ID: a1b2c3d4e502
Revises: a1b2c3d4e501
Create Date: 2026-02-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers
revision = 'a1b2c3d4e502'
down_revision = 'a1b2c3d4e501'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('project_members')]

    if 'source' not in columns:
        op.add_column('project_members',
                       sa.Column('source', sa.String(50), server_default='manual',
                                 comment='关联来源: manual, retroactive'))

    if 'source_workitem_id' not in columns:
        op.add_column('project_members',
                       sa.Column('source_workitem_id', sa.Integer(),
                                 sa.ForeignKey('work_items.id'), nullable=True))

    if 'first_associated_at' not in columns:
        op.add_column('project_members',
                       sa.Column('first_associated_at', sa.DateTime(), nullable=True,
                                 comment='首次关联时间'))

    # Add unique constraint (idempotent: check if it already exists)
    constraints = inspector.get_unique_constraints('project_members')
    constraint_names = [c['name'] for c in constraints]
    if 'uq_project_member_user_role' not in constraint_names:
        # First, remove any duplicate rows that would violate the constraint
        conn.execute(sa.text("""
            DELETE FROM project_members
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM project_members
                GROUP BY project_id, user_id, role
            )
        """))
        op.create_unique_constraint('uq_project_member_user_role', 'project_members',
                                     ['project_id', 'user_id', 'role'])


def downgrade():
    conn = op.get_bind()
    inspector = inspect(conn)

    constraints = inspector.get_unique_constraints('project_members')
    constraint_names = [c['name'] for c in constraints]
    if 'uq_project_member_user_role' in constraint_names:
        op.drop_constraint('uq_project_member_user_role', 'project_members', type_='unique')

    columns = [c['name'] for c in inspector.get_columns('project_members')]

    if 'first_associated_at' in columns:
        op.drop_column('project_members', 'first_associated_at')
    if 'source_workitem_id' in columns:
        op.drop_column('project_members', 'source_workitem_id')
    if 'source' in columns:
        op.drop_column('project_members', 'source')
