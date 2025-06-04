from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

def upgrade():
    # 获取当前数据库连接
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    
    # 检查表是否存在
    if 'actions' in inspector.get_table_names():
        # 修改company_id列为可为空
        op.alter_column('actions', 'company_id',
                existing_type=sa.Integer(),
                nullable=True)
        
        # 修改contact_id列为可为空
        op.alter_column('actions', 'contact_id',
                existing_type=sa.Integer(),
                nullable=True)
        
        print("已成功更新actions表，company_id和contact_id字段现在允许为空")
    else:
        print("actions表不存在，无需迁移")

def downgrade():
    # 获取当前数据库连接
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    
    # 检查表是否存在
    if 'actions' in inspector.get_table_names():
        # 回滚修改，恢复company_id列为不可为空
        op.alter_column('actions', 'company_id',
                existing_type=sa.Integer(),
                nullable=False)
        
        # 回滚修改，恢复contact_id列为不可为空
        op.alter_column('actions', 'contact_id',
                existing_type=sa.Integer(),
                nullable=False)
        
        print("已回滚actions表结构，company_id和contact_id字段现在不允许为空")
    else:
        print("actions表不存在，无需回滚") 