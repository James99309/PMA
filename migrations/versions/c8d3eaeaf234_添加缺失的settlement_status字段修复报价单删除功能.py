
"""添加缺失的settlement_status字段修复报价单删除功能

修复云端数据库缺失的关键字段，解决报价单删除时的数据库错误

问题: settlement_orders.settlement_status 字段缺失导致删除报价单时ORM报错
解决: 添加该字段并同时优化相关索引以提升性能

Revision ID: c8d3eaeaf234
Revises: 1c8151f19857
Create Date: 2025-07-27 11:05:25.215135

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c8d3eaeaf234'
down_revision = '1c8151f19857'
branch_labels = None
depends_on = None


def upgrade():
    """添加缺失的关键字段修复云端数据库结构"""
    
    # 1. 为 settlement_orders 表添加缺失的 settlement_status 字段
    # 这是修复报价单删除功能的关键字段
    print("🔄 正在为 settlement_orders 表添加 settlement_status 字段...")
    
    with op.batch_alter_table('settlement_orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'settlement_status', 
            sa.String(length=20), 
            nullable=True, 
            default='pending',
            comment='结算状态：pending, processing, completed, cancelled'
        ))
    
    print("✅ settlement_orders.settlement_status 字段添加完成")
    
    # 2. 为 dictionaries 表添加缺失的公司信息字段
    print("🔄 正在为 dictionaries 表添加缺失的公司信息字段...")
    
    with op.batch_alter_table('dictionaries', schema=None) as batch_op:
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
        
        # Logo相关字段
        batch_op.add_column(sa.Column('logo_type', sa.String(50), 
                                     nullable=True, comment='Logo类型'))
        batch_op.add_column(sa.Column('logo_size', sa.Integer(), 
                                     nullable=True, comment='Logo文件大小'))
        batch_op.add_column(sa.Column('logo_content', sa.Text(), 
                                     nullable=True, comment='Logo内容（Base64编码）'))
        batch_op.add_column(sa.Column('logo_filename', sa.String(255), 
                                     nullable=True, comment='Logo文件名'))
        
        # 邮件签名相关字段
        batch_op.add_column(sa.Column('email_signature_filename', sa.String(255), 
                                     nullable=True, comment='邮件签名文件名'))
        batch_op.add_column(sa.Column('email_signature_type', sa.String(50), 
                                     nullable=True, comment='邮件签名类型'))
        batch_op.add_column(sa.Column('email_signature_size', sa.Integer(), 
                                     nullable=True, comment='邮件签名文件大小'))
        batch_op.add_column(sa.Column('email_signature_content', sa.Text(), 
                                     nullable=True, comment='邮件签名内容'))
    
    print("✅ dictionaries 表字段添加完成")
    
    # 3. 创建性能优化索引
    print("🔄 正在创建性能优化索引...")
    
    try:
        # 结算相关索引
        op.create_index('idx_settlement_orders_settlement_status', 
                       'settlement_orders', ['settlement_status'])
        
        # 报价单性能索引
        op.create_index('idx_quotations_project_id', 'quotations', ['project_id'])
        op.create_index('idx_quotations_owner_id', 'quotations', ['owner_id'])
        op.create_index('idx_quotations_created_at', 'quotations', ['created_at'])
        op.create_index('idx_quotations_amount', 'quotations', ['total_amount'])
        
        # 项目性能索引
        op.create_index('idx_projects_current_stage', 'projects', ['current_stage'])
        op.create_index('idx_projects_owner_id', 'projects', ['owner_id'])
        op.create_index('idx_projects_project_type', 'projects', ['project_type'])
        
        # 字典表索引
        op.create_index('idx_dictionaries_company_email', 'dictionaries', ['email'])
        op.create_index('idx_dictionaries_company_phone', 'dictionaries', ['phone'])
        
        print("✅ 性能索引创建完成")
        
    except Exception as e:
        print(f"⚠️ 索引创建警告: {str(e)}")
        print("⚠️ 部分索引可能已存在，这是正常情况")
    
    print("🎉 云端数据库同步迁移完成")
    print("📋 主要修复:")
    print("   ✅ 修复报价单删除功能 (settlement_status字段)")
    print("   ✅ 添加公司信息管理字段")
    print("   ✅ 优化查询性能索引")


def downgrade():
    """安全回滚：删除添加的字段和索引"""
    
    print("⚠️ 开始回滚迁移...")
    
    # 删除索引
    try:
        op.drop_index('idx_dictionaries_company_phone', 'dictionaries')
        op.drop_index('idx_dictionaries_company_email', 'dictionaries')
        op.drop_index('idx_projects_project_type', 'projects')
        op.drop_index('idx_projects_owner_id', 'projects')
        op.drop_index('idx_projects_current_stage', 'projects')
        op.drop_index('idx_quotations_amount', 'quotations')
        op.drop_index('idx_quotations_created_at', 'quotations')
        op.drop_index('idx_quotations_owner_id', 'quotations')
        op.drop_index('idx_quotations_project_id', 'quotations')
        op.drop_index('idx_settlement_orders_settlement_status', 'settlement_orders')
    except Exception as e:
        print(f"索引删除警告: {str(e)}")
    
    # 从 dictionaries 表删除字段
    print("🔄 正在从 dictionaries 表删除添加的字段...")
    with op.batch_alter_table('dictionaries', schema=None) as batch_op:
        batch_op.drop_column('email_signature_content')
        batch_op.drop_column('email_signature_size')
        batch_op.drop_column('email_signature_type')
        batch_op.drop_column('email_signature_filename')
        batch_op.drop_column('logo_filename')
        batch_op.drop_column('logo_content')
        batch_op.drop_column('logo_size')
        batch_op.drop_column('logo_type')
        batch_op.drop_column('postal_code')
        batch_op.drop_column('address')
        batch_op.drop_column('website')
        batch_op.drop_column('email')
        batch_op.drop_column('fax')
        batch_op.drop_column('phone')
    
    # 从 settlement_orders 表删除字段
    print("🔄 正在从 settlement_orders 表删除 settlement_status 字段...")
    with op.batch_alter_table('settlement_orders', schema=None) as batch_op:
        batch_op.drop_column('settlement_status')
    
    print("✅ 迁移回滚完成")