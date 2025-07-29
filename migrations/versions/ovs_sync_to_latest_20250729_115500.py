"""OVS数据库同步到最新结构

Revision ID: ovs_sync_to_latest_20250729_115500
Revises: c8d3eaeaf234
Create Date: 2025-07-29 11:55:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ovs_sync_to_latest_20250729_115500'
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
        return result.fetchone()[0] > 0
    except Exception:
        return False


def upgrade():
    """OVS数据库升级到最新结构"""
    
    print("🚀 开始OVS数据库迁移...")
    print("   - 需要添加 26 个字段")
    
    # 1. approval_step 表字段
    with op.batch_alter_table('approval_step', schema=None) as batch_op:
        if not column_exists('approval_step', 'condition_config'):
            batch_op.add_column(sa.Column('condition_config', sa.JSON(), nullable=True))
        if not column_exists('approval_step', 'is_conditional'):
            batch_op.add_column(sa.Column('is_conditional', sa.Boolean(), nullable=True, server_default='false'))
        if not column_exists('approval_step', 'branch_on_reject'):
            batch_op.add_column(sa.Column('branch_on_reject', sa.Integer(), nullable=True))
        if not column_exists('approval_step', 'skip_conditions'):
            batch_op.add_column(sa.Column('skip_conditions', sa.JSON(), nullable=True))
        if not column_exists('approval_step', 'condition_type'):
            batch_op.add_column(sa.Column('condition_type', sa.String(length=50), nullable=True))
        if not column_exists('approval_step', 'branch_on_approve'):
            batch_op.add_column(sa.Column('branch_on_approve', sa.Integer(), nullable=True))
    print("✅ approval_step 表字段添加完成")
    
    # 2. performance_targets 表字段
    with op.batch_alter_table('performance_targets', schema=None) as batch_op:
        if not column_exists('performance_targets', 'customers_rate'):
            batch_op.add_column(sa.Column('customers_rate', sa.Integer(), nullable=True, server_default='0'))
        if not column_exists('performance_targets', 'implant_rate'):
            batch_op.add_column(sa.Column('implant_rate', sa.Integer(), nullable=True, server_default='0'))
        if not column_exists('performance_targets', 'sales_rate'):
            batch_op.add_column(sa.Column('sales_rate', sa.Integer(), nullable=True, server_default='0'))
        if not column_exists('performance_targets', 'projects_rate'):
            batch_op.add_column(sa.Column('projects_rate', sa.Integer(), nullable=True, server_default='0'))
    print("✅ performance_targets 表字段添加完成")
    
    # 3. dictionaries 表字段
    with op.batch_alter_table('dictionaries', schema=None) as batch_op:
        if not column_exists('dictionaries', 'email_signature_content'):
            batch_op.add_column(sa.Column('email_signature_content', sa.Text(), nullable=True))
        if not column_exists('dictionaries', 'website'):
            batch_op.add_column(sa.Column('website', sa.String(length=200), nullable=True))
        if not column_exists('dictionaries', 'postal_code'):
            batch_op.add_column(sa.Column('postal_code', sa.String(length=20), nullable=True))
        if not column_exists('dictionaries', 'logo_filename'):
            batch_op.add_column(sa.Column('logo_filename', sa.String(length=100), nullable=True))
        if not column_exists('dictionaries', 'email'):
            batch_op.add_column(sa.Column('email', sa.String(length=100), nullable=True))
        if not column_exists('dictionaries', 'email_signature_type'):
            batch_op.add_column(sa.Column('email_signature_type', sa.String(length=50), nullable=True))
        if not column_exists('dictionaries', 'email_signature_size'):
            batch_op.add_column(sa.Column('email_signature_size', sa.Integer(), nullable=True))
        if not column_exists('dictionaries', 'address'):
            batch_op.add_column(sa.Column('address', sa.String(length=500), nullable=True))
        if not column_exists('dictionaries', 'logo_content'):
            batch_op.add_column(sa.Column('logo_content', sa.Text(), nullable=True))
        if not column_exists('dictionaries', 'email_signature_filename'):
            batch_op.add_column(sa.Column('email_signature_filename', sa.String(length=100), nullable=True))
        if not column_exists('dictionaries', 'logo_size'):
            batch_op.add_column(sa.Column('logo_size', sa.Integer(), nullable=True))
        if not column_exists('dictionaries', 'phone'):
            batch_op.add_column(sa.Column('phone', sa.String(length=50), nullable=True))
        if not column_exists('dictionaries', 'fax'):
            batch_op.add_column(sa.Column('fax', sa.String(length=50), nullable=True))
        if not column_exists('dictionaries', 'logo_type'):
            batch_op.add_column(sa.Column('logo_type', sa.String(length=50), nullable=True))
    print("✅ dictionaries 表字段添加完成")
    
    # 4. approval_process_template 表字段
    with op.batch_alter_table('approval_process_template', schema=None) as batch_op:
        if not column_exists('approval_process_template', 'visual_data'):
            batch_op.add_column(sa.Column('visual_data', sa.JSON(), nullable=True))
    print("✅ approval_process_template 表字段添加完成")
    
    # 5. settlement_orders 表字段
    with op.batch_alter_table('settlement_orders', schema=None) as batch_op:
        if not column_exists('settlement_orders', 'settlement_status'):
            batch_op.add_column(sa.Column('settlement_status', sa.String(length=20), nullable=True, server_default="'pending'"))
    print("✅ settlement_orders 表字段添加完成")
    
    # 6. 创建关键索引
    print("📋 创建关键索引...")
    
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
            print(f"✅ 索引 {index_name} 创建成功")
        except Exception as e:
            print(f"⚠️ 索引 {index_name} 创建警告: {e}")
    
    # 7. 创建复合索引
    try:
        op.create_index('idx_quotations_project_owner', 'quotations', ['project_id', 'owner_id'], if_not_exists=True)
        op.create_index('idx_projects_type_stage', 'projects', ['project_type', 'current_stage'], if_not_exists=True)
        print("✅ 复合索引创建成功")
    except Exception as e:
        print(f"⚠️ 复合索引创建警告: {e}")
    
    print("🎉 OVS数据库迁移完成!")


def downgrade():
    """OVS迁移回滚（谨慎使用）"""
    print("⚠️ OVS迁移回滚功能")
    print("建议使用备份恢复而不是自动回滚")
    pass