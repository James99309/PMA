"""添加数据源配置表

Revision ID: add_data_source_config
Revises: add_performance_config_tables
Create Date: 2025-01-11 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_data_source_config'
down_revision = 'add_performance_config'
branch_labels = None
depends_on = None


def upgrade():
    # 创建数据表配置表
    op.create_table('data_table_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('table_name', sa.String(length=100), nullable=False, comment='数据表名'),
        sa.Column('display_name', sa.String(length=200), nullable=False, comment='显示名称'),
        sa.Column('description', sa.Text(), comment='表描述'),
        sa.Column('category', sa.String(length=50), comment='表分类：business/system/reference'),
        sa.Column('is_active', sa.Boolean(), default=True, comment='是否启用'),
        sa.Column('is_performance_source', sa.Boolean(), default=True, comment='是否可用作绩效数据源'),
        sa.Column('total_records', sa.Integer(), default=0, comment='记录总数'),
        sa.Column('last_updated', sa.DateTime(), comment='数据最后更新时间'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('table_name')
    )
    
    # 创建数据字段配置表
    op.create_table('data_field_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('table_config_id', sa.Integer(), nullable=False),
        sa.Column('field_name', sa.String(length=100), nullable=False, comment='字段名'),
        sa.Column('display_name', sa.String(length=200), nullable=False, comment='显示名称'),
        sa.Column('description', sa.Text(), comment='字段描述'),
        sa.Column('data_type', sa.String(length=50), nullable=False, comment='数据类型'),
        sa.Column('is_nullable', sa.Boolean(), default=True, comment='是否可为空'),
        sa.Column('is_primary_key', sa.Boolean(), default=False, comment='是否主键'),
        sa.Column('is_foreign_key', sa.Boolean(), default=False, comment='是否外键'),
        sa.Column('foreign_table', sa.String(length=100), comment='外键关联表'),
        sa.Column('foreign_field', sa.String(length=100), comment='外键关联字段'),
        sa.Column('is_numeric', sa.Boolean(), default=False, comment='是否数值字段'),
        sa.Column('is_monetary', sa.Boolean(), default=False, comment='是否金额字段'),
        sa.Column('is_date', sa.Boolean(), default=False, comment='是否日期字段'),
        sa.Column('is_aggregatable', sa.Boolean(), default=False, comment='是否可聚合统计'),
        sa.Column('is_filterable', sa.Boolean(), default=True, comment='是否可过滤'),
        sa.Column('is_performance_metric', sa.Boolean(), default=False, comment='是否绩效指标'),
        sa.Column('performance_category', sa.String(length=50), comment='绩效分类：sales/customer/project/quality'),
        sa.Column('calculation_priority', sa.Integer(), default=0, comment='计算优先级'),
        sa.Column('display_format', sa.String(length=50), comment='显示格式'),
        sa.Column('default_unit', sa.String(length=20), comment='默认单位'),
        sa.Column('decimal_places', sa.Integer(), default=2, comment='小数位数'),
        sa.Column('sample_values', sa.Text(), comment='样本值JSON'),
        sa.Column('value_range', sa.Text(), comment='值范围JSON'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['table_config_id'], ['data_table_config.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('table_config_id', 'field_name', name='uq_table_field')
    )
    
    # 创建扩展公式模板表
    op.create_table('formula_templates_extended',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_name', sa.String(length=100), nullable=False, comment='模板名称'),
        sa.Column('template_category', sa.String(length=50), comment='模板分类'),
        sa.Column('description', sa.Text(), comment='模板描述'),
        sa.Column('formula_expression', sa.Text(), nullable=False, comment='公式表达式'),
        sa.Column('required_tables', sa.Text(), comment='需要的数据表JSON'),
        sa.Column('required_fields', sa.Text(), comment='需要的字段JSON'),
        sa.Column('result_type', sa.String(length=50), default='numeric', comment='结果类型：numeric/percentage/count'),
        sa.Column('result_unit', sa.String(length=20), comment='结果单位'),
        sa.Column('is_system_template', sa.Boolean(), default=False, comment='是否系统模板'),
        sa.Column('is_active', sa.Boolean(), default=True, comment='是否启用'),
        sa.Column('usage_count', sa.Integer(), default=0, comment='使用次数'),
        sa.Column('last_used_at', sa.DateTime(), comment='最后使用时间'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 插入预定义的数据表配置
    op.execute("""
        INSERT INTO data_table_config (table_name, display_name, description, category, is_active, is_performance_source, created_at) VALUES
        ('quotations', '报价单', '项目报价单信息，包含金额和审批状态', 'business', true, true, NOW()),
        ('pricing_orders', '批价单', '批价订单信息，包含批价金额和结算金额', 'business', true, true, NOW()),
        ('projects', '项目', '项目基础信息，包含项目类型和阶段', 'business', true, true, NOW()),
        ('companies', '公司客户', '客户公司信息，包含行业和地区', 'business', true, true, NOW()),
        ('contacts', '联系人', '客户联系人信息', 'business', true, true, NOW()),
        ('products', '产品', '产品信息', 'reference', true, true, NOW()),
        ('users', '用户', '系统用户信息', 'system', true, false, NOW()),
        ('expenses', '费用', '费用记录', 'business', true, true, NOW()),
        ('settlements', '结算', '结算信息', 'business', true, true, NOW())
    """)
    
    # 插入预定义的扩展公式模板
    op.execute("""
        INSERT INTO formula_templates_extended (template_name, template_category, description, formula_expression, required_tables, required_fields, result_type, result_unit, is_system_template, is_active, created_at) VALUES
        ('销售总金额统计', 'sales', '统计指定时间范围内的销售总金额', 'SUM({quotations.amount}) WHERE {quotations.created_at} BETWEEN :start_date AND :end_date', '["quotations"]', '["quotations.amount", "quotations.created_at"]', 'numeric', '元', true, true, NOW()),
        
        ('批价单总金额统计', 'sales', '统计指定时间范围内批价单的总金额', 'SUM({pricing_orders.pricing_total_amount}) WHERE {pricing_orders.status} = ''approved'' AND {pricing_orders.created_at} BETWEEN :start_date AND :end_date', '["pricing_orders"]', '["pricing_orders.pricing_total_amount", "pricing_orders.status", "pricing_orders.created_at"]', 'numeric', '元', true, true, NOW()),
        
        ('植入金额统计', 'sales', '统计指定时间范围内的植入总金额', 'SUM({quotations.implant_total_amount}) WHERE {quotations.approval_status} = ''approved'' AND {quotations.created_at} BETWEEN :start_date AND :end_date', '["quotations"]', '["quotations.implant_total_amount", "quotations.approval_status", "quotations.created_at"]', 'numeric', '元', true, true, NOW()),
        
        ('新增客户数量', 'customer', '统计指定时间范围内新增的客户数量', 'COUNT({companies.id}) WHERE {companies.created_at} BETWEEN :start_date AND :end_date', '["companies"]', '["companies.id", "companies.created_at"]', 'count', '个', true, true, NOW()),
        
        ('新增项目数量', 'project', '统计指定时间范围内新增的项目数量', 'COUNT({projects.id}) WHERE {projects.created_at} BETWEEN :start_date AND :end_date', '["projects"]', '["projects.id", "projects.created_at"]', 'count', '个', true, true, NOW()),
        
        ('项目成功率', 'project', '计算项目的成功率（已完成项目占总项目的比例）', 'COUNT({projects.id} WHERE {projects.current_stage} = ''completed'') / COUNT({projects.id}) * 100', '["projects"]', '["projects.id", "projects.current_stage"]', 'percentage', '%', true, true, NOW()),
        
        ('平均报价金额', 'sales', '计算指定时间范围内报价单的平均金额', 'AVG({quotations.amount}) WHERE {quotations.created_at} BETWEEN :start_date AND :end_date', '["quotations"]', '["quotations.amount", "quotations.created_at"]', 'numeric', '元', true, true, NOW()),
        
        ('月度销售增长率', 'sales', '计算月度销售增长率', '(SUM({quotations.amount} WHERE EXTRACT(month FROM {quotations.created_at}) = EXTRACT(month FROM CURRENT_DATE)) - SUM({quotations.amount} WHERE EXTRACT(month FROM {quotations.created_at}) = EXTRACT(month FROM CURRENT_DATE - INTERVAL ''1 month''))) / SUM({quotations.amount} WHERE EXTRACT(month FROM {quotations.created_at}) = EXTRACT(month FROM CURRENT_DATE - INTERVAL ''1 month''))) * 100', '["quotations"]', '["quotations.amount", "quotations.created_at"]', 'percentage', '%', true, true, NOW()),
        
        ('客户转化率', 'customer', '计算客户转化率（有报价单的客户占总客户的比例）', 'COUNT(DISTINCT {quotations.contact_id}) / COUNT({companies.id}) * 100', '["quotations", "companies"]', '["quotations.contact_id", "companies.id"]', 'percentage', '%', true, true, NOW()),
        
        ('平均项目周期', 'project', '计算项目的平均周期（天数）', 'AVG(EXTRACT(days FROM ({projects.updated_at} - {projects.created_at}))) WHERE {projects.current_stage} = ''completed''', '["projects"]', '["projects.created_at", "projects.updated_at", "projects.current_stage"]', 'numeric', '天', true, true, NOW())
    """)


def downgrade():
    op.drop_table('formula_templates_extended')
    op.drop_table('data_field_config')
    op.drop_table('data_table_config')