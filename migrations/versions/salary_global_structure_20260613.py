"""薪资结构改为全局基础结构(2026-06-13):主子层级,不分岗位,不含金额

替代按岗位的 role_salary_items(从未上生产,直接 drop):
- 新表 salary_structure_items:全局主项/子项 + 发放方式,无金额、无岗位、无年份
- 种子固定主项:基础薪资 / 绩效薪资(is_locked)
- user_salary_items / user_salary_profile 保留(个人金额 + 试用期)

幂等:DROP/CREATE IF [NOT] EXISTS;种子 ON CONFLICT DO NOTHING。

Revision ID: salary_global_structure_20260613
Revises: salary_probation_20260613
Create Date: 2026-06-13
"""
from alembic import op

revision = 'salary_global_structure_20260613'
down_revision = 'salary_probation_20260613'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        DROP TABLE IF EXISTS role_salary_items;

        CREATE TABLE IF NOT EXISTS salary_structure_items (
            id SERIAL PRIMARY KEY,
            item_code VARCHAR(50) NOT NULL UNIQUE,
            item_name VARCHAR(100) NOT NULL,
            parent_code VARCHAR(50),
            pay_cycle VARCHAR(10) DEFAULT 'monthly',
            is_locked BOOLEAN DEFAULT FALSE,
            sort_order INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            created_by INTEGER REFERENCES users(id),
            updated_by INTEGER REFERENCES users(id)
        );
        CREATE INDEX IF NOT EXISTS idx_salary_structure_parent
            ON salary_structure_items (parent_code);

        INSERT INTO salary_structure_items (item_code, item_name, parent_code, pay_cycle, is_locked, sort_order)
        VALUES
            ('base_salary', '基础薪资', NULL, 'monthly', TRUE, 0),
            ('performance_salary', '绩效薪资', NULL, 'monthly', TRUE, 1)
        ON CONFLICT (item_code) DO NOTHING;
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS salary_structure_items;")
