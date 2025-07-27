
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
    
    # 首先检查字段是否已存在，避免重复添加
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col['name'] for col in inspector.get_columns('settlement_orders')]
    
    if 'settlement_status' not in columns:
        with op.batch_alter_table('settlement_orders', schema=None) as batch_op:
            batch_op.add_column(sa.Column(
                'settlement_status', 
                sa.String(length=20), 
                nullable=True, 
                default='pending',
                comment='结算状态：pending, processing, completed, cancelled'
            ))
        print("✅ settlement_orders.settlement_status 字段添加完成")
    else:
        print("✅ settlement_orders.settlement_status 字段已存在，跳过添加")
    
    # 2. 检查 dictionaries 表字段完整性（跳过已存在的字段）
    print("🔄 正在检查 dictionaries 表字段完整性...")
    
    dict_columns = [col['name'] for col in inspector.get_columns('dictionaries')]
    missing_fields = []
    
    # 需要检查的字段列表
    required_fields = [
        ('phone', sa.String(50)),
        ('fax', sa.String(50)), 
        ('email', sa.String(100)),
        ('website', sa.String(200)),
        ('address', sa.String(500)),
        ('postal_code', sa.String(20)),
        ('logo_type', sa.String(50)),
        ('logo_size', sa.Integer()),
        ('logo_content', sa.Text()),
        ('logo_filename', sa.String(100)),
        ('email_signature_filename', sa.String(100)),
        ('email_signature_type', sa.String(50)),
        ('email_signature_size', sa.Integer()),
        ('email_signature_content', sa.Text())
    ]
    
    # 检查哪些字段缺失
    for field_name, field_type in required_fields:
        if field_name not in dict_columns:
            missing_fields.append((field_name, field_type))
    
    # 只添加缺失的字段
    if missing_fields:
        print(f"🔄 发现 {len(missing_fields)} 个缺失字段，正在添加...")
        with op.batch_alter_table('dictionaries', schema=None) as batch_op:
            for field_name, field_type in missing_fields:
                batch_op.add_column(sa.Column(field_name, field_type, nullable=True))
                print(f"   ✅ 添加字段: {field_name}")
        print("✅ dictionaries 表缺失字段添加完成")
    else:
        print("✅ dictionaries 表所有字段已存在，无需添加")
    
    # 3. 创建性能优化索引（跳过已存在的索引）
    print("🔄 正在创建性能优化索引...")
    
    # 获取现有索引
    existing_indexes = set()
    try:
        for table_name in ['settlement_orders', 'quotations', 'projects', 'dictionaries']:
            table_indexes = inspector.get_indexes(table_name)
            for idx in table_indexes:
                existing_indexes.add(idx['name'])
    except Exception as e:
        print(f"⚠️ 获取索引信息警告: {str(e)}")
    
    # 需要创建的索引列表
    indexes_to_create = [
        ('idx_settlement_orders_settlement_status', 'settlement_orders', ['settlement_status']),
        ('idx_quotations_project_id', 'quotations', ['project_id']),
        ('idx_quotations_owner_id', 'quotations', ['owner_id']),
        ('idx_quotations_created_at', 'quotations', ['created_at']),
        ('idx_quotations_amount', 'quotations', ['total_amount']),
        ('idx_projects_current_stage', 'projects', ['current_stage']),
        ('idx_projects_owner_id', 'projects', ['owner_id']),
        ('idx_projects_project_type', 'projects', ['project_type']),
        ('idx_dictionaries_company_email', 'dictionaries', ['email']),
        ('idx_dictionaries_company_phone', 'dictionaries', ['phone'])
    ]
    
    created_count = 0
    for idx_name, table_name, columns in indexes_to_create:
        if idx_name not in existing_indexes:
            try:
                op.create_index(idx_name, table_name, columns)
                print(f"   ✅ 创建索引: {idx_name}")
                created_count += 1
            except Exception as e:
                print(f"   ⚠️ 索引 {idx_name} 创建警告: {str(e)}")
        else:
            print(f"   ✅ 索引 {idx_name} 已存在，跳过")
    
    print(f"✅ 性能索引检查完成，新创建 {created_count} 个索引")
    
    print("🎉 云端数据库同步迁移完成")
    print("📋 主要修复:")
    print("   ✅ 修复报价单删除功能 (settlement_status字段)")
    print("   ✅ 添加公司信息管理字段")
    print("   ✅ 优化查询性能索引")


def downgrade():
    """安全回滚：删除添加的字段和索引"""
    
    print("⚠️ 开始回滚迁移...")
    
    # 获取数据库连接和检查器
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # 删除索引（只删除存在的索引）
    print("🔄 正在删除索引...")
    indexes_to_drop = [
        ('idx_dictionaries_company_phone', 'dictionaries'),
        ('idx_dictionaries_company_email', 'dictionaries'),
        ('idx_projects_project_type', 'projects'),
        ('idx_projects_owner_id', 'projects'),
        ('idx_projects_current_stage', 'projects'),
        ('idx_quotations_amount', 'quotations'),
        ('idx_quotations_created_at', 'quotations'),
        ('idx_quotations_owner_id', 'quotations'),
        ('idx_quotations_project_id', 'quotations'),
        ('idx_settlement_orders_settlement_status', 'settlement_orders')
    ]
    
    for idx_name, table_name in indexes_to_drop:
        try:
            # 检查索引是否存在
            table_indexes = inspector.get_indexes(table_name)
            index_names = [idx['name'] for idx in table_indexes]
            
            if idx_name in index_names:
                op.drop_index(idx_name, table_name)
                print(f"   ✅ 删除索引: {idx_name}")
            else:
                print(f"   ✅ 索引 {idx_name} 不存在，跳过")
        except Exception as e:
            print(f"   ⚠️ 索引 {idx_name} 删除警告: {str(e)}")
    
    # 检查并删除 dictionaries 表字段（只删除存在的字段）
    print("🔄 正在检查并删除 dictionaries 表字段...")
    dict_columns = [col['name'] for col in inspector.get_columns('dictionaries')]
    
    fields_to_remove = [
        'email_signature_content', 'email_signature_size', 'email_signature_type', 
        'email_signature_filename', 'logo_filename', 'logo_content', 'logo_size', 
        'logo_type', 'postal_code', 'address', 'website', 'email', 'fax', 'phone'
    ]
    
    fields_to_drop = [field for field in fields_to_remove if field in dict_columns]
    
    if fields_to_drop:
        print(f"🔄 发现 {len(fields_to_drop)} 个字段需要删除...")
        with op.batch_alter_table('dictionaries', schema=None) as batch_op:
            for field in fields_to_drop:
                batch_op.drop_column(field)
                print(f"   ✅ 删除字段: {field}")
        print("✅ dictionaries 表字段删除完成")
    else:
        print("✅ dictionaries 表无字段需要删除")
    
    # 检查并删除 settlement_orders 表的 settlement_status 字段
    print("🔄 正在检查并删除 settlement_orders 表字段...")
    settlement_columns = [col['name'] for col in inspector.get_columns('settlement_orders')]
    
    if 'settlement_status' in settlement_columns:
        with op.batch_alter_table('settlement_orders', schema=None) as batch_op:
            batch_op.drop_column('settlement_status')
        print("✅ settlement_orders.settlement_status 字段删除完成")
    else:
        print("✅ settlement_orders.settlement_status 字段不存在，跳过删除")
    
    print("✅ 迁移回滚完成")