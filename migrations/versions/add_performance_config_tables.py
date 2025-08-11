"""添加角色绩效配置表

Revision ID: add_performance_config
Revises: 
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_performance_config'
down_revision = None  # 替换为实际的前一个revision
branch_labels = None
depends_on = None


def upgrade():
    # 创建绩效指标定义表
    op.create_table('performance_metrics_definition',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('metric_code', sa.String(length=50), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('metric_category', sa.String(length=50), nullable=True),
        sa.Column('data_type', sa.String(length=20), nullable=False),
        sa.Column('default_unit', sa.String(length=20), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('available_sources', sa.JSON(), nullable=True),
        sa.Column('is_system_metric', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('metric_code')
    )
    op.create_index('idx_performance_metrics_code', 'performance_metrics_definition', ['metric_code'], unique=False)

    # 创建角色绩效配置主表
    op.create_table('role_performance_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('config_name', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role')
    )
    op.create_index('idx_role_performance_config_role', 'role_performance_config', ['role'], unique=False)

    # 创建角色绩效项目配置表
    op.create_table('role_performance_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role_config_id', sa.Integer(), nullable=False),
        sa.Column('metric_id', sa.Integer(), nullable=True),
        sa.Column('item_name', sa.String(length=100), nullable=False),
        sa.Column('item_code', sa.String(length=50), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=True),
        sa.Column('stat_scope', sa.String(length=20), nullable=False),
        sa.Column('stat_scope_description', sa.Text(), nullable=True),
        sa.Column('calculation_method', sa.String(length=20), nullable=True),
        sa.Column('calculation_formula', sa.Text(), nullable=True),
        sa.Column('data_source_config', sa.JSON(), nullable=True),
        sa.Column('qualification_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('excellent_threshold', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('good_threshold', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('qualified_threshold', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('display_unit', sa.String(length=20), nullable=True),
        sa.Column('decimal_places', sa.Integer(), nullable=True),
        sa.Column('color_config', sa.JSON(), nullable=True),
        sa.Column('weight', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['metric_id'], ['performance_metrics_definition.id'], ),
        sa.ForeignKeyConstraint(['role_config_id'], ['role_performance_config.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role_config_id', 'item_code', name='uq_role_item_code')
    )
    op.create_index('idx_role_items_config', 'role_performance_items', ['role_config_id'], unique=False)
    op.create_index('idx_role_items_metric', 'role_performance_items', ['metric_id'], unique=False)

    # 创建绩效计算公式模板表
    op.create_table('performance_formula_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_name', sa.String(length=100), nullable=False),
        sa.Column('template_category', sa.String(length=50), nullable=True),
        sa.Column('formula_expression', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('variables_definition', sa.JSON(), nullable=True),
        sa.Column('example_usage', sa.Text(), nullable=True),
        sa.Column('is_system_template', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建角色绩效数据访问权限表
    op.create_table('role_performance_access',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('access_scope', sa.String(length=20), nullable=False),
        sa.Column('access_conditions', sa.JSON(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role', 'access_scope', name='uq_role_access_scope')
    )
    op.create_index('idx_role_access', 'role_performance_access', ['role', 'access_scope'], unique=False)

    # 插入系统内置指标数据
    performance_metrics = [
        {
            'metric_code': 'sales_amount',
            'metric_name': '销售金额',
            'metric_category': 'financial',
            'data_type': 'amount',
            'default_unit': '万元',
            'description': '已审批批价单的销售总额',
            'is_system_metric': True,
            'is_active': True
        },
        {
            'metric_code': 'implant_amount',
            'metric_name': '植入金额',
            'metric_category': 'financial',
            'data_type': 'amount',
            'default_unit': '万元',
            'description': '报价单中产品的市场价值总额',
            'is_system_metric': True,
            'is_active': True
        },
        {
            'metric_code': 'customer_count',
            'metric_name': '新增客户数',
            'metric_category': 'customer',
            'data_type': 'count',
            'default_unit': '个',
            'description': '新增客户公司数量',
            'is_system_metric': True,
            'is_active': True
        },
        {
            'metric_code': 'project_count',
            'metric_name': '新增项目数',
            'metric_category': 'project',
            'data_type': 'count',
            'default_unit': '个',
            'description': '新增项目数量',
            'is_system_metric': True,
            'is_active': True
        },
        {
            'metric_code': 'five_star_projects',
            'metric_name': '五星项目数',
            'metric_category': 'project',
            'data_type': 'count',
            'default_unit': '个',
            'description': '五星级项目数量',
            'is_system_metric': True,
            'is_active': True
        },
        {
            'metric_code': 'quotation_count',
            'metric_name': '报价单数',
            'metric_category': 'business',
            'data_type': 'count',
            'default_unit': '个',
            'description': '创建的报价单数量',
            'is_system_metric': True,
            'is_active': True
        },
        {
            'metric_code': 'approval_efficiency',
            'metric_name': '审批效率',
            'metric_category': 'business',
            'data_type': 'percentage',
            'default_unit': '%',
            'description': '审批通过率',
            'is_system_metric': True,
            'is_active': True
        }
    ]
    
    # 批量插入指标数据
    metrics_table = sa.table('performance_metrics_definition',
        sa.column('metric_code'),
        sa.column('metric_name'),
        sa.column('metric_category'),
        sa.column('data_type'),
        sa.column('default_unit'),
        sa.column('description'),
        sa.column('is_system_metric'),
        sa.column('is_active'),
        sa.column('created_at'),
        sa.column('updated_at')
    )
    
    import datetime
    now = datetime.datetime.utcnow()
    for metric in performance_metrics:
        metric['created_at'] = now
        metric['updated_at'] = now
        op.execute(metrics_table.insert().values(**metric))

    # 插入公式模板数据
    formula_templates = [
        {
            'template_name': '销售金额统计',
            'template_category': 'financial',
            'formula_expression': 'SUM(pricing_orders.pricing_total_amount) WHERE status = \'approved\'',
            'description': '统计已审批批价单的销售总额',
            'variables_definition': '{"variables": [{"name": "pricing_total_amount", "description": "批价单总额", "type": "amount"}]}',
            'is_system_template': True,
            'created_at': now
        },
        {
            'template_name': '植入金额统计',
            'template_category': 'financial',
            'formula_expression': 'SUM(quotation_details.quantity * quotation_details.market_price)',
            'description': '统计报价单明细的植入总额',
            'variables_definition': '{"variables": [{"name": "quantity", "description": "数量"}, {"name": "market_price", "description": "市场价格"}]}',
            'is_system_template': True,
            'created_at': now
        },
        {
            'template_name': '客户增长率',
            'template_category': 'customer',
            'formula_expression': '(当月新增客户数 - 上月新增客户数) / 上月新增客户数 * 100',
            'description': '计算客户增长百分比',
            'variables_definition': '{"variables": [{"name": "current_count", "description": "当月客户数"}, {"name": "previous_count", "description": "上月客户数"}]}',
            'is_system_template': True,
            'created_at': now
        },
        {
            'template_name': '综合业绩评分',
            'template_category': 'comprehensive',
            'formula_expression': 'sales_amount * 0.4 + implant_amount * 0.3 + customer_count * 100 * 0.3',
            'description': '综合业绩加权评分',
            'variables_definition': '{"variables": [{"name": "sales_amount", "description": "销售金额"}, {"name": "implant_amount", "description": "植入金额"}, {"name": "customer_count", "description": "客户数量"}]}',
            'is_system_template': True,
            'created_at': now
        }
    ]
    
    templates_table = sa.table('performance_formula_templates',
        sa.column('template_name'),
        sa.column('template_category'),
        sa.column('formula_expression'),
        sa.column('description'),
        sa.column('variables_definition'),
        sa.column('is_system_template'),
        sa.column('created_at')
    )
    
    for template in formula_templates:
        op.execute(templates_table.insert().values(**template))


def downgrade():
    # 删除所有创建的表
    op.drop_table('role_performance_access')
    op.drop_table('performance_formula_templates')
    op.drop_table('role_performance_items')
    op.drop_table('role_performance_config')
    op.drop_table('performance_metrics_definition')