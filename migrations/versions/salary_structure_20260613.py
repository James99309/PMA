"""岗位结构化薪资表(2026-06-13):角色级薪资结构 + 个人覆盖/专属项目

需求:薪资类似绩效表格,项目分类(基础薪资/绩效薪资/其他可添加),
岗位设置好后套用到个人;个人可覆盖金额、可添加专属项目。
仅 admin / ceo / hr_manager 可见可配。
旧职级带宽体系(salary_grade_config 等)保留不动,互不干扰。

幂等:IF NOT EXISTS。

Revision ID: salary_structure_20260613
Revises: nonscheme_kpi_cleanup_20260613
Create Date: 2026-06-13
"""
from alembic import op

revision = 'salary_structure_20260613'
down_revision = 'nonscheme_kpi_cleanup_20260613'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS role_salary_items (
            id SERIAL PRIMARY KEY,
            role_code VARCHAR(50) NOT NULL,
            year INTEGER NOT NULL,
            item_code VARCHAR(50) NOT NULL,
            item_name VARCHAR(100) NOT NULL,
            category VARCHAR(20) NOT NULL DEFAULT 'other',      -- base|performance|other
            pay_cycle VARCHAR(10) NOT NULL DEFAULT 'monthly',   -- monthly|yearly
            amount NUMERIC(15,2),
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            created_by INTEGER REFERENCES users(id),
            updated_by INTEGER REFERENCES users(id),
            CONSTRAINT uq_role_salary_item UNIQUE (role_code, year, item_code)
        );
        CREATE INDEX IF NOT EXISTS idx_role_salary_role_year
            ON role_salary_items (role_code, year);

        CREATE TABLE IF NOT EXISTS user_salary_items (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            year INTEGER NOT NULL,
            item_code VARCHAR(50) NOT NULL,
            item_name VARCHAR(100),                              -- 个人专属项目名;覆盖行可空(沿用角色名)
            category VARCHAR(20),
            pay_cycle VARCHAR(10),
            amount NUMERIC(15,2),
            is_personal BOOLEAN DEFAULT FALSE,                   -- true=个人专属项目;false=覆盖角色项金额
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            created_by INTEGER REFERENCES users(id),
            updated_by INTEGER REFERENCES users(id),
            CONSTRAINT uq_user_salary_item UNIQUE (user_id, year, item_code)
        );
        CREATE INDEX IF NOT EXISTS idx_user_salary_user_year
            ON user_salary_items (user_id, year);
    """)


def downgrade():
    op.execute("""
        DROP TABLE IF EXISTS user_salary_items;
        DROP TABLE IF EXISTS role_salary_items;
    """)
