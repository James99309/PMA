"""add_missing_columns_to_existing_tables_in_sp8d

SP8D云端数据库迁移 - 第二阶段：添加缺失的字段
为现有表添加本地数据库中存在但SP8D缺失的字段

Revision ID: sp8d_missing_columns_002
Revises: sp8d_missing_tables_001
Create Date: 2025-07-26

安全说明：
- 此迁移只添加新字段，不修改或删除现有字段
- 完全保护SP8D独有的审批功能字段
- 新字段默认值为NULL，不影响现有数据
- 支持完整回滚
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'sp8d_missing_columns_002'
down_revision = 'sp8d_missing_tables_001'
branch_labels = None
depends_on = None


def upgrade():
    """为现有表添加缺失的字段"""
    
    print("🔄 开始第二阶段迁移：添加缺失的字段")
    
    # 1. 为 dictionaries 表添加14个缺失字段（公司Logo和邮件签名相关）
    print("🔄 正在为 dictionaries 表添加14个字段...")
    
    with op.batch_alter_table('dictionaries', schema=None) as batch_op:
        # 邮件签名相关字段
        batch_op.add_column(sa.Column('email_signature_filename', sa.String(255), 
                                     nullable=True, comment='邮件签名文件名'))
        batch_op.add_column(sa.Column('email_signature_type', sa.String(50), 
                                     nullable=True, comment='邮件签名类型'))
        batch_op.add_column(sa.Column('email_signature_size', sa.Integer(), 
                                     nullable=True, comment='邮件签名文件大小'))
        batch_op.add_column(sa.Column('email_signature_content', sa.Text(), 
                                     nullable=True, comment='邮件签名内容'))
        
        # Logo相关字段
        batch_op.add_column(sa.Column('logo_type', sa.String(50), 
                                     nullable=True, comment='Logo类型'))
        batch_op.add_column(sa.Column('logo_size', sa.Integer(), 
                                     nullable=True, comment='Logo文件大小'))
        batch_op.add_column(sa.Column('logo_content', sa.Text(), 
                                     nullable=True, comment='Logo内容（Base64编码）'))
        batch_op.add_column(sa.Column('logo_filename', sa.String(255), 
                                     nullable=True, comment='Logo文件名'))
        
        # 公司联系信息字段
        batch_op.add_column(sa.Column('phone', sa.String(50), 
                                     nullable=True, comment='公司电话'))
        batch_op.add_column(sa.Column('fax', sa.String(50), 
                                     nullable=True, comment='公司传真'))
        batch_op.add_column(sa.Column('email', sa.String(255), 
                                     nullable=True, comment='公司邮箱'))
        batch_op.add_column(sa.Column('website', sa.String(255), 
                                     nullable=True, comment='公司网站'))
        batch_op.add_column(sa.Column('address', sa.Text(), 
                                     nullable=True, comment='公司地址'))
        batch_op.add_column(sa.Column('postal_code', sa.String(20), 
                                     nullable=True, comment='邮政编码'))
    
    print("✅ dictionaries 表字段添加完成")
    
    # 2. 为 settlement_orders 表添加1个缺失字段
    print("🔄 正在为 settlement_orders 表添加 settlement_status 字段...")
    
    with op.batch_alter_table('settlement_orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('settlement_status', sa.String(50), 
                                     nullable=True, 
                                     comment='结算状态：pending, processing, completed, cancelled'))
    
    print("✅ settlement_orders 表字段添加完成")
    
    # 3. 重要说明：完全保护 purchase_orders 表的SP8D独有字段
    print("✅ purchase_orders 表保护：以下SP8D独有字段完全保留：")
    print("   - approval_status (审批状态)")
    print("   - approval_completed_at (审批完成时间)")
    print("   - approval_submitted_at (审批提交时间)")
    
    # 4. 创建索引以提高查询性能
    print("🔄 正在创建新字段的索引...")
    
    try:
        # 为经常查询的字段创建索引
        op.create_index('idx_dictionaries_logo_type', 'dictionaries', ['logo_type'])
        op.create_index('idx_settlement_orders_settlement_status', 'settlement_orders', ['settlement_status'])
        print("✅ 索引创建完成")
    except Exception as e:
        print(f"⚠️  索引创建警告: {str(e)}")
    
    print("✅ 第二阶段迁移完成：已添加所有缺失字段")
    print("🛡️  SP8D独有功能完全保护，零业务影响")


def downgrade():
    """安全回滚：删除添加的字段"""
    
    print("⚠️  开始回滚第二阶段迁移...")
    
    # 删除索引
    try:
        op.drop_index('idx_settlement_orders_settlement_status', 'settlement_orders')
        op.drop_index('idx_dictionaries_logo_type', 'dictionaries')
    except Exception as e:
        print(f"索引删除警告: {str(e)}")
    
    # 从 settlement_orders 表删除字段
    print("🔄 正在从 settlement_orders 表删除字段...")
    with op.batch_alter_table('settlement_orders', schema=None) as batch_op:
        batch_op.drop_column('settlement_status')
    
    # 从 dictionaries 表删除字段（按添加的逆序删除）
    print("🔄 正在从 dictionaries 表删除14个字段...")
    with op.batch_alter_table('dictionaries', schema=None) as batch_op:
        batch_op.drop_column('postal_code')
        batch_op.drop_column('address')
        batch_op.drop_column('website')
        batch_op.drop_column('email')
        batch_op.drop_column('fax')
        batch_op.drop_column('phone')
        batch_op.drop_column('logo_filename')
        batch_op.drop_column('logo_content')
        batch_op.drop_column('logo_size')
        batch_op.drop_column('logo_type')
        batch_op.drop_column('email_signature_content')
        batch_op.drop_column('email_signature_size')
        batch_op.drop_column('email_signature_type')
        batch_op.drop_column('email_signature_filename')
    
    print("✅ 第二阶段回滚完成：已删除添加的字段")


def verify_columns_added():
    """验证字段是否成功添加"""
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
            # 检查 dictionaries 表的新字段
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'dictionaries' 
                AND column_name IN (
                    'email_signature_filename', 'logo_type', 'phone', 'address',
                    'email_signature_type', 'logo_size', 'fax', 'website',
                    'email_signature_size', 'email_signature_content', 
                    'logo_content', 'postal_code', 'email', 'logo_filename'
                )
            """))
            
            dict_columns = [row[0] for row in result.fetchall()]
            
            # 检查 settlement_orders 表的新字段
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'settlement_orders' 
                AND column_name = 'settlement_status'
            """))
            
            settlement_columns = [row[0] for row in result.fetchall()]
            
            # 验证SP8D独有字段仍然存在
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'purchase_orders' 
                AND column_name IN ('approval_status', 'approval_completed_at', 'approval_submitted_at')
            """))
            
            approval_columns = [row[0] for row in result.fetchall()]
            
            # 输出验证结果
            print(f"✅ dictionaries 表新增字段: {len(dict_columns)}/14")
            print(f"✅ settlement_orders 表新增字段: {len(settlement_columns)}/1")
            print(f"✅ purchase_orders 表保留SP8D字段: {len(approval_columns)}/3")
            
            if len(dict_columns) == 14 and len(settlement_columns) == 1:
                print("✅ 字段迁移验证成功")
                return True
            else:
                print("❌ 字段迁移验证失败")
                return False
                
    except Exception as e:
        print(f"❌ 字段验证出错: {str(e)}")
        return False


def show_sp8d_protection_status():
    """显示SP8D保护状态"""
    print("\n🛡️  SP8D数据库保护状态报告")
    print("=" * 50)
    print("✅ 完全保护的SP8D独有功能：")
    print("   📋 purchase_orders 表的审批流程功能")
    print("   🔐 approval_status - 审批状态字段")
    print("   ⏰ approval_completed_at - 审批完成时间")
    print("   📤 approval_submitted_at - 审批提交时间")
    print("\n✅ 新增的本地功能：")
    print("   🏢 company_assets 表 - 公司资产管理")
    print("   📦 temp_products 表 - 临时产品管理")
    print("   🖼️  dictionaries 表 - Logo和签名管理 (14个字段)")
    print("   💰 settlement_orders 表 - 结算状态管理")
    print("\n🎯 迁移结果：")
    print("   📈 功能增强：获得本地开发的新功能")
    print("   🛡️  零业务影响：SP8D审批流程完全保留")
    print("   🔄 可回滚：支持完整的迁移回滚")
    print("=" * 50)


if __name__ == "__main__":
    print("SP8D数据库迁移脚本 - 第二阶段")
    print("=" * 50)
    print("此脚本将安全地添加缺失字段到SP8D现有表")
    print("⚠️  请确保已完成第一阶段迁移！")
    show_sp8d_protection_status()
    print("=" * 50)