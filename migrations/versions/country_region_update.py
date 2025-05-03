"""将 province 重命名为 region，删除 city 字段

Revision ID: country_region_update
Revises: 25af362bc651
Create Date: 2025-05-01

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'country_region_update'
down_revision = '25af362bc651'  # 设置为当前的头部版本
branch_labels = None
depends_on = None

def upgrade():
    # 1. 重命名 province 列为 region
    op.alter_column('companies', 'province', new_column_name='region')
    
    # 2. 将 city 数据合并到 region 列中（如有需要）
    # 这是一个示例，根据实际数据情况可能需要调整
    conn = op.get_bind()
    companies = conn.execute("SELECT id, region, city FROM companies WHERE city IS NOT NULL AND city != ''").fetchall()
    
    for company in companies:
        company_id, region, city = company
        # 如果 region 为空但 city 不为空，则使用 city 值
        if (not region or region.strip() == '') and city and city.strip() != '':
            conn.execute(f"UPDATE companies SET region = '{city}' WHERE id = {company_id}")
    
    # 3. 删除 city 列
    op.drop_column('companies', 'city')

def downgrade():
    # 1. 添加 city 列
    op.add_column('companies', sa.Column('city', sa.String(50), nullable=True))
    
    # 2. 重命名 region 列为 province
    op.alter_column('companies', 'region', new_column_name='province') 
 