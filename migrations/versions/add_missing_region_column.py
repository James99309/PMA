"""确保companies表有region列

Revision ID: add_missing_region_column
Revises: add_region_column
Create Date: 2025-05-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_missing_region_column'
down_revision = 'add_region_column'  # 设置为上一个迁移版本
branch_labels = None
depends_on = None


def upgrade():
    # 检查companies表是否存在region列，如果不存在则添加
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    has_table = False
    
    # 检查companies表是否存在
    for table_name in inspector.get_table_names():
        if table_name == 'companies':
            has_table = True
            break
            
    if not has_table:
        # 如果表不存在，则不需要添加列
        return
    
    # 获取表的列
    columns = [column['name'] for column in inspector.get_columns('companies')]
    
    # 检查region列是否存在
    if 'region' not in columns:
        op.add_column('companies', sa.Column('region', sa.String(50), nullable=True))
        print("成功添加region列到companies表")
        
        # 如果存在province列，将数据从province移到region
        if 'province' in columns:
            # 创建一个临时表来存储公司ID和province值
            op.execute(
                """
                UPDATE companies 
                SET region = province 
                WHERE province IS NOT NULL AND province != ''
                """
            )
            print("已将province列数据迁移到region列")


def downgrade():
    # 此操作不可逆，我们不希望在回滚时删除数据
    pass 