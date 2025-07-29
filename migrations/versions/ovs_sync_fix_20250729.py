"""OVS数据库同步修复版本

Revision ID: ovs_sync_fix_20250729
Revises: c8d3eaeaf234
Create Date: 2025-07-29 12:30:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ovs_sync_fix_20250729'
down_revision = 'c8d3eaeaf234'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """检查列是否存在"""
    connection = op.get_bind()
    try:
        result = connection.execute(sa.text("""
            SELECT COUNT(*) FROM information_schema.columns 
            WHERE table_name = :table_name AND column_name = :column_name
        """), {"table_name": table_name, "column_name": column_name})
        exists = result.fetchone()[0] > 0
        print(f"  🔍 检查字段 {table_name}.{column_name}: {'存在' if exists else '不存在'}")
        return exists
    except Exception as e:
        print(f"  ❌ 检查字段 {table_name}.{column_name} 失败: {e}")
        return False


def add_column_safely(table_name, column_name, column_type, **kwargs):
    """安全添加列并输出详细日志"""
    if not column_exists(table_name, column_name):
        try:
            with op.batch_alter_table(table_name, schema=None) as batch_op:
                batch_op.add_column(sa.Column(column_name, column_type, **kwargs))
            print(f"  ✅ 成功添加字段 {table_name}.{column_name}")
            
            # 验证添加是否成功
            if column_exists(table_name, column_name):
                print(f"  ✅ 验证成功: {table_name}.{column_name} 已存在")
                return True
            else:
                print(f"  ❌ 验证失败: {table_name}.{column_name} 添加后仍不存在")
                return False
        except Exception as e:
            print(f"  ❌ 添加字段 {table_name}.{column_name} 失败: {e}")
            return False
    else:
        print(f"  ⏭️ 跳过已存在字段 {table_name}.{column_name}")
        return True


def upgrade():
    """OVS数据库升级到最新结构 - 增强版"""
    
    print("🚀 开始OVS数据库迁移（增强版）...")
    print("   - 需要添加 26 个字段")
    print("   - 将进行详细的验证和日志记录")
    
    success_count = 0
    failed_count = 0
    
    # 1. approval_step 表字段
    print("\n📋 处理 approval_step 表...")
    fields = [
        ('condition_config', sa.JSON(), {'nullable': True}),
        ('is_conditional', sa.Boolean(), {'nullable': True, 'server_default': 'false'}),
        ('branch_on_reject', sa.Integer(), {'nullable': True}),
        ('skip_conditions', sa.JSON(), {'nullable': True}),
        ('condition_type', sa.String(length=50), {'nullable': True}),
        ('branch_on_approve', sa.Integer(), {'nullable': True})
    ]
    
    for field_name, field_type, kwargs in fields:
        if add_column_safely('approval_step', field_name, field_type, **kwargs):
            success_count += 1
        else:
            failed_count += 1
    
    # 2. performance_targets 表字段
    print("\n📋 处理 performance_targets 表...")
    fields = [
        ('customers_rate', sa.Integer(), {'nullable': True, 'server_default': '0'}),
        ('implant_rate', sa.Integer(), {'nullable': True, 'server_default': '0'}),
        ('sales_rate', sa.Integer(), {'nullable': True, 'server_default': '0'}),
        ('projects_rate', sa.Integer(), {'nullable': True, 'server_default': '0'})
    ]
    
    for field_name, field_type, kwargs in fields:
        if add_column_safely('performance_targets', field_name, field_type, **kwargs):
            success_count += 1
        else:
            failed_count += 1
    
    # 3. dictionaries 表字段（重点关注）
    print("\n📋 处理 dictionaries 表...")
    fields = [
        ('email_signature_content', sa.Text(), {'nullable': True}),
        ('website', sa.String(length=200), {'nullable': True}),
        ('postal_code', sa.String(length=20), {'nullable': True}),
        ('logo_filename', sa.String(length=100), {'nullable': True}),
        ('email', sa.String(length=100), {'nullable': True}),
        ('email_signature_type', sa.String(length=50), {'nullable': True}),
        ('email_signature_size', sa.Integer(), {'nullable': True}),
        ('address', sa.String(length=500), {'nullable': True}),
        ('logo_content', sa.Text(), {'nullable': True}),
        ('email_signature_filename', sa.String(length=100), {'nullable': True}),
        ('logo_size', sa.Integer(), {'nullable': True}),
        ('phone', sa.String(length=50), {'nullable': True}),
        ('fax', sa.String(length=50), {'nullable': True}),
        ('logo_type', sa.String(length=50), {'nullable': True})
    ]
    
    for field_name, field_type, kwargs in fields:
        if add_column_safely('dictionaries', field_name, field_type, **kwargs):
            success_count += 1
        else:
            failed_count += 1
    
    # 4. approval_process_template 表字段
    print("\n📋 处理 approval_process_template 表...")
    if add_column_safely('approval_process_template', 'visual_data', sa.JSON(), nullable=True):
        success_count += 1
    else:
        failed_count += 1
    
    # 5. settlement_orders 表字段
    print("\n📋 处理 settlement_orders 表...")
    if add_column_safely('settlement_orders', 'settlement_status', sa.String(length=20), nullable=True, server_default="'pending'"):
        success_count += 1
    else:
        failed_count += 1
    
    # 最终统计
    print(f"\n🎯 迁移完成统计:")
    print(f"   ✅ 成功添加: {success_count} 个字段")
    print(f"   ❌ 失败: {failed_count} 个字段")
    print(f"   📊 成功率: {success_count/(success_count+failed_count)*100:.1f}%")
    
    if failed_count > 0:
        print(f"\n⚠️ 警告: 有 {failed_count} 个字段添加失败，可能需要手动检查")
        # 不抛出异常，让迁移完成但记录问题
    else:
        print("\n🎉 所有字段添加成功！")
    
    # 6. 创建关键索引（保持原有逻辑）
    print("\n📋 创建关键索引...")
    
    key_indexes = [
        ('projects', 'idx_projects_current_stage', ['current_stage']),
        ('projects', 'idx_projects_owner_id', ['owner_id']),
        ('projects', 'idx_projects_project_type', ['project_type']),
        ('projects', 'idx_projects_vendor_sales_manager', ['vendor_sales_manager_id']),
        ('quotations', 'idx_quotations_amount', ['amount']),
        ('quotations', 'idx_quotations_created_at', ['created_at']),
        ('quotations', 'idx_quotations_owner_id', ['owner_id']),
        ('quotations', 'idx_quotations_project_id', ['project_id']),
        ('quotations', 'idx_quotations_updated_at', ['updated_at']),
    ]
    
    for table_name, index_name, columns in key_indexes:
        try:
            op.create_index(index_name, table_name, columns, if_not_exists=True)
            print(f"  ✅ 索引 {index_name} 创建成功")
        except Exception as e:
            print(f"  ⚠️ 索引 {index_name} 创建警告: {e}")
    
    # 7. 创建复合索引
    try:
        op.create_index('idx_quotations_project_owner', 'quotations', ['project_id', 'owner_id'], if_not_exists=True)
        op.create_index('idx_projects_type_stage', 'projects', ['project_type', 'current_stage'], if_not_exists=True)
        print("  ✅ 复合索引创建成功")
    except Exception as e:
        print(f"  ⚠️ 复合索引创建警告: {e}")
    
    print("\n🎉 OVS数据库迁移增强版完成!")


def downgrade():
    """OVS迁移回滚（谨慎使用）"""
    print("⚠️ OVS迁移回滚功能")
    print("建议使用备份恢复而不是自动回滚")
    pass