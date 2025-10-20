
"""remove_customer_type_from_unique_constraint

Revision ID: 7ad5fc6d3bac
Revises: c9a7b9ea3a42
Create Date: 2025-10-18 12:26:59.487976

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7ad5fc6d3bac'
down_revision = 'c9a7b9ea3a42'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 删除旧的唯一约束（包含 customer_type）
    # 兼容不同环境的约束名称
    connection = op.get_bind()
    result = connection.execute(sa.text("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'project_customer_associations'
        AND constraint_type = 'UNIQUE'
        AND constraint_name LIKE '%project%company%type%'
    """))
    constraint_name = result.fetchone()

    if constraint_name:
        constraint_name = constraint_name[0]
        with op.batch_alter_table('project_customer_associations', schema=None) as batch_op:
            batch_op.drop_constraint(constraint_name, type_='unique')
    else:
        print("⚠️  未找到旧的唯一约束，可能已被删除")

    # 2. 清理重复数据：对于同一个 (project_id, company_id) 组合，只保留最早的记录
    connection = op.get_bind()

    # 查找并删除重复记录（保留 id 最小的，即最早创建的）
    connection.execute(sa.text("""
        DELETE FROM project_customer_associations
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM project_customer_associations
            GROUP BY project_id, company_id
        )
    """))

    # 3. 创建新的唯一约束（只有 project_id + company_id）
    with op.batch_alter_table('project_customer_associations', schema=None) as batch_op:
        batch_op.create_unique_constraint('unique_project_company', ['project_id', 'company_id'])

        # 4. 将 customer_type 字段改为允许 NULL（标记为废弃但保留）
        batch_op.alter_column('customer_type',
                             existing_type=sa.String(length=50),
                             nullable=True,
                             comment='DEPRECATED: 该字段已废弃，请使用 company.company_type')


def downgrade():
    # 回滚操作：恢复旧的约束
    with op.batch_alter_table('project_customer_associations', schema=None) as batch_op:
        # 1. 删除新约束
        batch_op.drop_constraint('unique_project_company', type_='unique')

        # 2. 恢复旧约束
        batch_op.create_unique_constraint('unique_project_company_type',
                                         ['project_id', 'company_id', 'customer_type'])

        # 3. 恢复 customer_type 为 NOT NULL
        batch_op.alter_column('customer_type',
                             existing_type=sa.String(length=50),
                             nullable=False,
                             comment=None)