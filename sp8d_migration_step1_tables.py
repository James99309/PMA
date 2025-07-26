"""add_missing_tables_company_assets_and_temp_products_to_sp8d

SP8D云端数据库迁移 - 第一阶段：添加缺失的表
创建 company_assets 和 temp_products 表

Revision ID: sp8d_missing_tables_001
Revises: None (SP8D首次迁移)
Create Date: 2025-07-26

安全说明：
- 此迁移只添加新表，不修改现有表
- 完全保护SP8D现有的所有数据和功能
- 支持完整回滚
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'sp8d_missing_tables_001'
down_revision = None  # SP8D的第一个迁移
branch_labels = None
depends_on = None


def upgrade():
    """添加SP8D缺失的表"""
    
    # 创建 company_assets 表 (14个字段)
    print("🔄 正在创建 company_assets 表...")
    op.create_table('company_assets',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('company_id', sa.Integer(), nullable=True, comment='关联的公司ID'),
        sa.Column('asset_type', sa.String(50), nullable=True, comment='资产类型：logo, signature等'),
        sa.Column('asset_content', sa.Text(), nullable=True, comment='资产内容（Base64编码）'),
        sa.Column('asset_filename', sa.String(255), nullable=True, comment='原始文件名'),
        sa.Column('asset_size', sa.Integer(), nullable=True, comment='文件大小（字节）'),
        sa.Column('asset_mime_type', sa.String(100), nullable=True, comment='MIME类型'),
        sa.Column('is_active', sa.Boolean(), default=True, comment='是否启用'),
        sa.Column('display_order', sa.Integer(), default=0, comment='显示顺序'),
        sa.Column('created_at', sa.DateTime(), 
                 default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), 
                 default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by_id', sa.Integer(), nullable=True, comment='创建者ID'),
        sa.Column('updated_by_id', sa.Integer(), nullable=True, comment='更新者ID'),
        sa.Column('notes', sa.Text(), nullable=True, comment='备注信息')
    )
    
    # 创建 temp_products 表 (16个字段)
    print("🔄 正在创建 temp_products 表...")
    op.create_table('temp_products',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('product_name', sa.String(255), nullable=True, comment='产品名称'),
        sa.Column('product_model', sa.String(255), nullable=True, comment='产品型号'),
        sa.Column('product_desc', sa.Text(), nullable=True, comment='产品描述'),
        sa.Column('brand', sa.String(100), nullable=True, comment='品牌'),
        sa.Column('unit', sa.String(20), nullable=True, comment='单位'),
        sa.Column('product_mn', sa.String(100), nullable=True, comment='产品编号'),
        sa.Column('market_price', sa.Float(), nullable=True, comment='市场价格'),
        sa.Column('reference_price', sa.Float(), nullable=True, comment='参考价格'),
        sa.Column('category', sa.String(100), nullable=True, comment='产品类别'),
        sa.Column('subcategory', sa.String(100), nullable=True, comment='产品子类别'),
        sa.Column('status', sa.String(50), default='active', comment='状态'),
        sa.Column('created_at', sa.DateTime(), 
                 default=sa.text('CURRENT_TIMESTAMP'), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), 
                 default=sa.text('CURRENT_TIMESTAMP'), comment='更新时间'),
        sa.Column('created_by_id', sa.Integer(), nullable=True, comment='创建者ID'),
        sa.Column('notes', sa.Text(), nullable=True, comment='备注信息')
    )
    
    # 添加外键约束（如果公司表存在）
    print("🔄 正在添加外键约束...")
    try:
        # 检查 companies 表是否存在
        op.create_foreign_key(
            'fk_company_assets_company_id', 
            'company_assets', 
            'companies',
            ['company_id'], 
            ['id'],
            ondelete='SET NULL'
        )
        print("✅ company_assets 外键约束创建成功")
    except Exception as e:
        print(f"⚠️  外键约束创建跳过: {str(e)}")
    
    # 创建索引以提高查询性能
    print("🔄 正在创建索引...")
    op.create_index('idx_company_assets_company_id', 'company_assets', ['company_id'])
    op.create_index('idx_company_assets_asset_type', 'company_assets', ['asset_type'])
    op.create_index('idx_temp_products_product_mn', 'temp_products', ['product_mn'])
    op.create_index('idx_temp_products_status', 'temp_products', ['status'])
    
    print("✅ 第一阶段迁移完成：已添加 company_assets 和 temp_products 表")


def downgrade():
    """安全回滚：删除添加的表"""
    
    print("⚠️  开始回滚第一阶段迁移...")
    
    # 删除索引
    try:
        op.drop_index('idx_temp_products_status', 'temp_products')
        op.drop_index('idx_temp_products_product_mn', 'temp_products')
        op.drop_index('idx_company_assets_asset_type', 'company_assets')
        op.drop_index('idx_company_assets_company_id', 'company_assets')
    except Exception as e:
        print(f"索引删除警告: {str(e)}")
    
    # 删除外键约束
    try:
        op.drop_constraint('fk_company_assets_company_id', 'company_assets', type_='foreignkey')
    except Exception as e:
        print(f"外键约束删除警告: {str(e)}")
    
    # 删除表
    op.drop_table('temp_products')
    op.drop_table('company_assets')
    
    print("✅ 第一阶段回滚完成：已删除添加的表")


# 迁移验证函数
def verify_migration():
    """验证迁移是否成功"""
    from sqlalchemy import create_engine, text
    import os
    
    # 连接数据库
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ 无法获取数据库连接")
        return False
    
    engine = create_engine(db_url)
    
    try:
        with engine.connect() as conn:
            # 检查表是否存在
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('company_assets', 'temp_products')
            """))
            
            tables = [row[0] for row in result.fetchall()]
            
            if 'company_assets' in tables and 'temp_products' in tables:
                print("✅ 迁移验证成功：两个表都已创建")
                
                # 检查表结构
                result = conn.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'company_assets' 
                    ORDER BY ordinal_position
                """))
                
                columns = len(result.fetchall())
                print(f"✅ company_assets 表有 {columns} 个字段")
                
                return True
            else:
                print(f"❌ 迁移验证失败：缺少表 {set(['company_assets', 'temp_products']) - set(tables)}")
                return False
                
    except Exception as e:
        print(f"❌ 迁移验证出错: {str(e)}")
        return False


if __name__ == "__main__":
    print("SP8D数据库迁移脚本 - 第一阶段")
    print("=" * 50)
    print("此脚本将安全地添加 company_assets 和 temp_products 表到SP8D数据库")
    print("⚠️  请确保已备份数据库！")
    print("=" * 50)