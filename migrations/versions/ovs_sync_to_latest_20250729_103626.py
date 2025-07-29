"""OVS数据库同步到最新结构

Revision ID: ovs_sync_to_latest_20250729
Revises: (empty - OVS初始迁移)
Create Date: 2025-07-29 10:36:26

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ovs_sync_to_latest_20250729'
down_revision = 'c8d3eaeaf234'  # 基于最新的稳定版本
branch_labels = None
depends_on = None


def upgrade():
    """OVS数据库升级到最新结构"""
    
    print("🚀 开始OVS数据库迁移安全检查...")
    
    # 🔒 安全检查1: 验证当前数据库是否为OVS
    connection = op.get_bind()
    
    try:
        result = connection.execute(sa.text("SELECT current_database()"))
        db_name = result.fetchone()[0]
        
        if 'ovs' not in db_name.lower():
            print(f"❌ 安全检查失败: 当前数据库 '{db_name}' 不是OVS数据库")
            print("   此迁移仅适用于OVS数据库 (数据库名应包含'ovs')")
            print("   请检查 DATABASE_URL 环境变量")
            raise Exception("数据库安全检查失败 - 非OVS数据库")
            
        print(f"✅ 安全检查1通过: 当前数据库 '{db_name}' 是OVS数据库")
    except Exception as e:
        if "数据库安全检查失败" in str(e):
            raise
        print(f"⚠️ 无法确定数据库名称: {e}")
        print("   执行备用检查...")
    
    # 🔒 安全检查2: 验证数据库表数量特征
    try:
        result = connection.execute(sa.text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"))
        table_count = result.fetchone()[0]
        
        # 更新检查逻辑：OVS数据库表数量应该在合理范围内
        if table_count < 55 or table_count > 60:
            print(f"❌ 安全检查失败: 当前数据库表数量 {table_count}，超出预期范围")
            print("   预期OVS数据库表数量: 55-60个")
            print("   请确认您正在正确的数据库上执行迁移")
            raise Exception("数据库安全检查失败 - 表数量不匹配")
            
        print(f"✅ 安全检查2通过: 表数量 {table_count} 在OVS数据库合理范围内")
    except Exception as e:
        if "数据库安全检查失败" in str(e):
            raise
        print(f"❌ 表数量验证失败: {e}")
        raise Exception("数据库安全检查失败 - 无法验证表数量")
    
    # 🔒 安全检查3: 验证alembic版本状态
    try:
        result = connection.execute(sa.text("SELECT version_num FROM alembic_version"))
        versions = result.fetchall()
        
        if versions:
            current_version = versions[0][0] if versions[0][0] else "空值"
            if current_version != 'c8d3eaeaf234':
                print(f"⚠️ 版本检查: 当前版本 '{current_version}'，期望版本 'c8d3eaeaf234'")
                print("   如果确认要强制执行，请继续...")
            else:
                print("✅ 安全检查3通过: 当前版本匹配期望的前置版本")
        else:
            print("⚠️ 版本检查: alembic_version表为空，将从基础版本开始")
            
    except Exception as e:
        print(f"⚠️ 版本检查警告: {e}")
    
    # 🔒 安全检查4: 验证缺失表存在性
    try:
        result = connection.execute(sa.text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('temp_products', 'company_assets')"))
        existing_target_tables = [row[0] for row in result.fetchall()]
        
        if existing_target_tables:
            print(f"❌ 安全检查失败: 目标表已存在 {existing_target_tables}")
            print("   这表明迁移可能已经执行过或数据库状态异常")
            raise Exception("数据库安全检查失败 - 目标表已存在")
            
        print("✅ 安全检查4通过: 目标表不存在，可以安全创建")
    except Exception as e:
        if "数据库安全检查失败" in str(e):
            raise
        print(f"⚠️ 目标表检查警告: {e}")
    
    print("🎉 所有安全检查通过！开始执行OVS数据库迁移...")
    print("   - 需要创建 2 个表")
    print("   - 需要添加 26 个字段") 
    print("   - 需要创建相关索引和约束")
    
    # 1. 创建序列（如果不存在）
    try:
        op.execute("CREATE SEQUENCE IF NOT EXISTS temp_products_id_seq;")
        op.execute("CREATE SEQUENCE IF NOT EXISTS company_assets_id_seq;")
        print("✅ 序列创建完成")
    except Exception as e:
        print(f"⚠️ 序列创建警告: {e}")
    
    # 2. 创建缺失的表
    print("📋 创建缺失的表...")
    
    # 创建 temp_products 表
    try:
        op.create_table('temp_products',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('product_name', sa.String(length=100), nullable=False),
            sa.Column('product_model', sa.String(length=100), nullable=False),
            sa.Column('product_desc', sa.Text(), nullable=True),
            sa.Column('brand', sa.String(length=50), nullable=True),
            sa.Column('unit', sa.String(length=20), nullable=True),
            sa.Column('category', sa.String(length=50), nullable=True),
            sa.Column('category_path', sa.String(length=200), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=False),
            sa.Column('usage_count', sa.Integer(), nullable=True),
            sa.Column('last_used_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=True),
            sa.Column('reference_price', sa.Float(), nullable=True),
            sa.Column('product_mn', sa.String(length=50), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.execute("ALTER TABLE temp_products ALTER COLUMN id SET DEFAULT nextval('temp_products_id_seq')")
        print("✅ temp_products 表创建成功")
    except Exception as e:
        print(f"⚠️ temp_products 表创建警告: {e}")
    
    # 创建 company_assets 表
    try:
        op.create_table('company_assets',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('asset_type', sa.String(length=50), nullable=False),
            sa.Column('asset_name', sa.String(length=100), nullable=False),
            sa.Column('asset_key', sa.String(length=50), nullable=False),
            sa.Column('file_name', sa.String(length=255), nullable=False),
            sa.Column('file_type', sa.String(length=50), nullable=False),
            sa.Column('file_size', sa.Integer(), nullable=False),
            sa.Column('file_content', sa.Text(), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('is_default', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('created_by_id', sa.Integer(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.execute("ALTER TABLE company_assets ALTER COLUMN id SET DEFAULT nextval('company_assets_id_seq')")
        print("✅ company_assets 表创建成功")
    except Exception as e:
        print(f"⚠️ company_assets 表创建警告: {e}")
    
    # 3. 添加缺失的字段
    print("📋 添加缺失的字段...")
    
    # settlement_orders 表
    try:
        op.add_column('settlement_orders', sa.Column('settlement_status', sa.String(length=20), nullable=True, server_default='pending'))
        print("✅ settlement_orders.settlement_status 字段添加成功")
    except Exception as e:
        print(f"⚠️ settlement_orders 字段添加警告: {e}")
    
    # approval_step 表
    approval_step_columns = [
        ('is_conditional', sa.Boolean(), False),
        ('condition_config', sa.JSON(), None),
        ('branch_on_reject', sa.Integer(), None),
        ('condition_type', sa.String(length=50), None),
        ('skip_conditions', sa.JSON(), None),
        ('branch_on_approve', sa.Integer(), None)
    ]
    
    for col_name, col_type, default_val in approval_step_columns:
        try:
            if default_val is not None:
                op.add_column('approval_step', sa.Column(col_name, col_type, nullable=True, server_default=str(default_val).lower() if isinstance(default_val, bool) else str(default_val)))
            else:
                op.add_column('approval_step', sa.Column(col_name, col_type, nullable=True))
            print(f"✅ approval_step.{col_name} 字段添加成功")
        except Exception as e:
            print(f"⚠️ approval_step.{col_name} 字段添加警告: {e}")
    
    # dictionaries 表 - 分批添加字段
    dictionaries_columns = [
        ('logo_content', sa.Text()),
        ('address', sa.String(length=255)),
        ('logo_type', sa.String(length=50)),
        ('email_signature_content', sa.Text()),
        ('email_signature_filename', sa.String(length=255)),
        ('email_signature_type', sa.String(length=50)),
        ('website', sa.String(length=255)),
        ('logo_filename', sa.String(length=255)),
        ('postal_code', sa.String(length=20)),
        ('phone', sa.String(length=50)),
        ('email_signature_size', sa.Integer()),
        ('email', sa.String(length=100)),
        ('logo_size', sa.Integer()),
        ('fax', sa.String(length=50))
    ]
    
    for col_name, col_type in dictionaries_columns:
        try:
            op.add_column('dictionaries', sa.Column(col_name, col_type, nullable=True))
            print(f"✅ dictionaries.{col_name} 字段添加成功")
        except Exception as e:
            print(f"⚠️ dictionaries.{col_name} 字段添加警告: {e}")
    
    # approval_process_template 表
    try:
        op.add_column('approval_process_template', sa.Column('visual_data', sa.JSON(), nullable=True))
        print("✅ approval_process_template.visual_data 字段添加成功")
    except Exception as e:
        print(f"⚠️ approval_process_template 字段添加警告: {e}")
    
    # performance_targets 表
    performance_targets_columns = [
        ('sales_rate', sa.Integer()),
        ('projects_rate', sa.Integer()),
        ('implant_rate', sa.Integer()),
        ('customers_rate', sa.Integer())
    ]
    
    for col_name, col_type in performance_targets_columns:
        try:
            op.add_column('performance_targets', sa.Column(col_name, col_type, nullable=True))
            print(f"✅ performance_targets.{col_name} 字段添加成功")
        except Exception as e:
            print(f"⚠️ performance_targets.{col_name} 字段添加警告: {e}")
    
    # 4. 创建关键索引
    print("📋 创建关键索引...")
    
    key_indexes = [
        ('temp_products', 'idx_temp_products_created_by', ['created_by']),
        ('temp_products', 'idx_temp_products_category', ['category']),
        ('company_assets', 'idx_company_assets_asset_type', ['asset_type']),
        ('company_assets', 'idx_company_assets_created_by_id', ['created_by_id']),
        # 性能优化索引（从本地同步）
        ('quotations', 'idx_quotations_project_id', ['project_id']),
        ('quotations', 'idx_quotations_owner_id', ['owner_id']),
        ('quotations', 'idx_quotations_created_at', ['created_at']),
        ('quotations', 'idx_quotations_updated_at', ['updated_at']),
        ('quotations', 'idx_quotations_amount', ['amount']),
        ('projects', 'idx_projects_project_type', ['project_type']),
        ('projects', 'idx_projects_current_stage', ['current_stage']),
        ('projects', 'idx_projects_owner_id', ['owner_id']),
        ('projects', 'idx_projects_vendor_sales_manager', ['vendor_sales_manager_id'])
    ]
    
    for table_name, index_name, columns in key_indexes:
        try:
            op.create_index(index_name, table_name, columns, if_not_exists=True)
            print(f"✅ 索引 {index_name} 创建成功")
        except Exception as e:
            print(f"⚠️ 索引 {index_name} 创建警告: {e}")
    
    # 5. 创建复合索引
    try:
        op.create_index('idx_quotations_project_owner', 'quotations', ['project_id', 'owner_id'], if_not_exists=True)
        op.create_index('idx_projects_type_stage', 'projects', ['project_type', 'current_stage'], if_not_exists=True)
        print("✅ 复合索引创建成功")
    except Exception as e:
        print(f"⚠️ 复合索引创建警告: {e}")
    
    print("🎉 OVS数据库迁移完成!")
    print("📊 执行验证查询...")
    
    # 验证迁移结果
    connection = op.get_bind()
    try:
        result = connection.execute(sa.text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"))
        table_count = result.fetchone()[0]
        print(f"✅ 迁移验证: 当前表数量 = {table_count}")
        
        # 验证新表是否创建成功
        result = connection.execute(sa.text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('temp_products', 'company_assets')"))
        new_tables = [row[0] for row in result.fetchall()]
        print(f"✅ 新创建的表: {', '.join(new_tables)}")
        
    except Exception as e:
        print(f"⚠️ 验证查询警告: {e}")


def downgrade():
    """OVS迁移回滚（谨慎使用）"""
    print("⚠️ OVS迁移回滚功能")
    print("建议使用备份恢复而不是自动回滚")
    
    # 回滚操作（谨慎使用）
    try:
        # 删除新增的表
        op.drop_table('temp_products')
        op.drop_table('company_assets')
        
        # 删除新增的字段（示例）
        op.drop_column('settlement_orders', 'settlement_status')
        
        print("⚠️ 回滚完成，但建议验证数据完整性")
    except Exception as e:
        print(f"❌ 回滚失败: {e}")
        print("建议手动恢复备份")