"""add salary config tables

Revision ID: add_salary_config_tables_20251228
Revises:
Create Date: 2025-12-28

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_salary_config_tables_20251228'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """创建薪资配置相关的9个表"""

    # 1. 职级薪资配置表
    op.create_table('salary_grade_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('grade_code', sa.String(10), nullable=False),
        sa.Column('grade_name', sa.String(50), nullable=False),
        sa.Column('grade_type', sa.String(10), nullable=False, comment='L=专业序列, M=管理序列'),
        sa.Column('annual_target', sa.Numeric(precision=15, scale=2), nullable=True, comment='年度目标(万)'),
        sa.Column('monthly_base_salary', sa.Numeric(precision=15, scale=2), nullable=True, comment='月基础工资'),
        sa.Column('monthly_performance_base', sa.Numeric(precision=15, scale=2), nullable=True, comment='月绩效基数'),
        sa.Column('monthly_management_allowance', sa.Numeric(precision=15, scale=2), server_default='0', nullable=True, comment='月管理津贴'),
        sa.Column('personal_weight', sa.Numeric(precision=5, scale=2), server_default='1', nullable=True, comment='个人权重（M级使用）'),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('grade_code', name='uq_salary_grade_code')
    )
    op.create_index('ix_salary_grade_config_grade_code', 'salary_grade_config', ['grade_code'])
    op.create_index('ix_salary_grade_config_grade_type', 'salary_grade_config', ['grade_type'])

    # 2. 职级薪资带宽表
    op.create_table('salary_grade_bandwidth',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('grade_id', sa.Integer(), nullable=False),
        sa.Column('base_salary_min', sa.Numeric(precision=15, scale=2), nullable=True, comment='月基础工资最低'),
        sa.Column('base_salary_mid', sa.Numeric(precision=15, scale=2), nullable=True, comment='月基础工资中位值'),
        sa.Column('base_salary_max', sa.Numeric(precision=15, scale=2), nullable=True, comment='月基础工资最高'),
        sa.Column('performance_base_min', sa.Numeric(precision=15, scale=2), nullable=True, comment='月绩效基数最低'),
        sa.Column('performance_base_mid', sa.Numeric(precision=15, scale=2), nullable=True, comment='月绩效基数中位值'),
        sa.Column('performance_base_max', sa.Numeric(precision=15, scale=2), nullable=True, comment='月绩效基数最高'),
        sa.Column('target_min', sa.Numeric(precision=15, scale=2), nullable=True, comment='年度目标最低'),
        sa.Column('target_mid', sa.Numeric(precision=15, scale=2), nullable=True, comment='年度目标中位值'),
        sa.Column('target_max', sa.Numeric(precision=15, scale=2), nullable=True, comment='年度目标最高'),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['grade_id'], ['salary_grade_config.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('grade_id', name='uq_salary_bandwidth_grade')
    )

    # 3. 薪资基础参数配置表
    op.create_table('salary_base_params',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('param_code', sa.String(50), nullable=False),
        sa.Column('param_name', sa.String(100), nullable=False),
        sa.Column('param_value', sa.Numeric(precision=15, scale=4), nullable=True),
        sa.Column('param_unit', sa.String(20), nullable=True, comment='单位（%/倍/元）'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('param_code', name='uq_salary_param_code')
    )
    op.create_index('ix_salary_base_params_param_code', 'salary_base_params', ['param_code'])

    # 4. 薪资阶梯规则配置表
    op.create_table('salary_step_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_type', sa.String(50), nullable=False, comment='performance_coefficient/commission_rate/commission_release/annual_bonus'),
        sa.Column('min_threshold', sa.Numeric(precision=10, scale=4), nullable=True, comment='最低阈值'),
        sa.Column('max_threshold', sa.Numeric(precision=10, scale=4), nullable=True, comment='最高阈值（NULL=无上限）'),
        sa.Column('coefficient', sa.Numeric(precision=10, scale=4), nullable=True, comment='系数/比例'),
        sa.Column('description', sa.String(100), nullable=True),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_salary_step_rules_rule_type', 'salary_step_rules', ['rule_type'])
    op.create_index('idx_step_rules_type_threshold', 'salary_step_rules', ['rule_type', 'min_threshold'])

    # 5. 薪资计算公式配置表
    op.create_table('salary_formula_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('formula_code', sa.String(50), nullable=False),
        sa.Column('formula_name', sa.String(100), nullable=False),
        sa.Column('formula_expression', sa.Text(), nullable=True, comment='公式表达式'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('variables', sa.JSON(), nullable=True, comment='公式变量定义'),
        sa.Column('result_unit', sa.String(20), nullable=True, comment='结果单位（%/元/万）'),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('formula_code', name='uq_salary_formula_code')
    )
    op.create_index('ix_salary_formula_config_formula_code', 'salary_formula_config', ['formula_code'])

    # 6. 销售团队配置表
    op.create_table('sales_team_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('team_name', sa.String(100), nullable=False),
        sa.Column('team_leader_id', sa.Integer(), nullable=True),
        sa.Column('leader_grade', sa.String(10), nullable=True, comment='负责人职级'),
        sa.Column('annual_target', sa.Numeric(precision=15, scale=2), nullable=True, comment='团队年度目标(万)'),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['team_leader_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sales_team_config_team_leader_id', 'sales_team_config', ['team_leader_id'])

    # 7. 员工薪资配置表
    op.create_table('employee_salary_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.Column('grade_id', sa.Integer(), nullable=True),
        sa.Column('supervisor_id', sa.Integer(), nullable=True, comment='上级ID'),
        sa.Column('use_custom_config', sa.Boolean(), server_default='false', nullable=True, comment='是否使用个人自定义配置'),
        sa.Column('monthly_base_salary_override', sa.Numeric(precision=15, scale=2), nullable=True, comment='月基础工资覆盖'),
        sa.Column('monthly_performance_base_override', sa.Numeric(precision=15, scale=2), nullable=True, comment='月绩效基数覆盖'),
        sa.Column('monthly_management_allowance_override', sa.Numeric(precision=15, scale=2), nullable=True, comment='月管理津贴覆盖'),
        sa.Column('annual_target_override', sa.Numeric(precision=15, scale=2), nullable=True, comment='个人年度目标(万)覆盖'),
        sa.Column('personal_weight_override', sa.Numeric(precision=5, scale=2), nullable=True, comment='个人权重覆盖（M级）'),
        sa.Column('commission_rate_multiplier', sa.Numeric(precision=5, scale=2), server_default='1', nullable=True, comment='提成比例系数'),
        sa.Column('bonus_multiplier', sa.Numeric(precision=5, scale=2), server_default='1', nullable=True, comment='年终奖系数'),
        sa.Column('team_share_rate_override', sa.Numeric(precision=5, scale=2), nullable=True, comment='团队分成比例覆盖'),
        sa.Column('config_notes', sa.Text(), nullable=True, comment='配置备注'),
        sa.Column('configured_by', sa.Integer(), nullable=True, comment='配置人'),
        sa.Column('configured_at', sa.DateTime(), nullable=True, comment='配置时间'),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['configured_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['grade_id'], ['salary_grade_config.id'], ),
        sa.ForeignKeyConstraint(['supervisor_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['sales_team_config.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_employee_salary_config_user')
    )
    op.create_index('ix_employee_salary_config_user_id', 'employee_salary_config', ['user_id'])
    op.create_index('ix_employee_salary_config_team_id', 'employee_salary_config', ['team_id'])
    op.create_index('ix_employee_salary_config_grade_id', 'employee_salary_config', ['grade_id'])

    # 8. 季度业绩数据表
    op.create_table('quarterly_performance_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('quarter', sa.Integer(), nullable=False, comment='1-4'),
        sa.Column('achievement', sa.Numeric(precision=15, scale=2), nullable=True, comment='季度业绩(万)'),
        sa.Column('completion_rate', sa.Numeric(precision=10, scale=4), nullable=True, comment='完成率'),
        sa.Column('high_price_ratio', sa.Numeric(precision=10, scale=4), nullable=True, comment='高批价占比'),
        sa.Column('high_price_rate', sa.Numeric(precision=10, scale=4), nullable=True, comment='高批价率'),
        sa.Column('data_source', sa.String(20), server_default='system', nullable=True, comment='system/manual'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'year', 'quarter', name='uq_user_year_quarter')
    )
    op.create_index('idx_quarterly_performance_user_year', 'quarterly_performance_data', ['user_id', 'year'])

    # 9. 薪资计算结果表
    op.create_table('salary_calculation_result',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=True),
        sa.Column('grade_code', sa.String(10), nullable=True),
        sa.Column('annual_target', sa.Numeric(precision=15, scale=2), nullable=True, comment='年度目标(万)'),
        sa.Column('annual_achievement', sa.Numeric(precision=15, scale=2), nullable=True, comment='年度业绩(万)'),
        sa.Column('personal_completion_rate', sa.Numeric(precision=10, scale=4), nullable=True, comment='个人完成率'),
        sa.Column('team_completion_rate', sa.Numeric(precision=10, scale=4), nullable=True, comment='团队完成率'),
        sa.Column('personal_weight', sa.Numeric(precision=5, scale=2), nullable=True, comment='个人权重'),
        sa.Column('team_weight', sa.Numeric(precision=5, scale=2), nullable=True, comment='团队权重'),
        sa.Column('comprehensive_completion_rate', sa.Numeric(precision=10, scale=4), nullable=True, comment='综合完成率'),
        sa.Column('annual_base_salary', sa.Numeric(precision=15, scale=4), nullable=True, comment='年基础工资(万)'),
        sa.Column('management_allowance', sa.Numeric(precision=15, scale=4), nullable=True, comment='管理津贴(万)'),
        sa.Column('performance_salary', sa.Numeric(precision=15, scale=4), nullable=True, comment='绩效工资(万)'),
        sa.Column('personal_commission_base', sa.Numeric(precision=15, scale=4), nullable=True, comment='个人提成基数(万)'),
        sa.Column('team_commission_share', sa.Numeric(precision=15, scale=4), nullable=True, comment='团队分成(万)'),
        sa.Column('commission_total', sa.Numeric(precision=15, scale=4), nullable=True, comment='提成合计(万)'),
        sa.Column('commission_release_rate', sa.Numeric(precision=10, scale=4), nullable=True, comment='发放比例'),
        sa.Column('final_commission', sa.Numeric(precision=15, scale=4), nullable=True, comment='最终提成(万)'),
        sa.Column('annual_bonus', sa.Numeric(precision=15, scale=4), nullable=True, comment='年终奖(万)'),
        sa.Column('annual_total_income', sa.Numeric(precision=15, scale=4), nullable=True, comment='年总收入(万)'),
        sa.Column('total_cost', sa.Numeric(precision=15, scale=4), nullable=True, comment='总成本(万)'),
        sa.Column('net_contribution', sa.Numeric(precision=15, scale=4), nullable=True, comment='净贡献(万)'),
        sa.Column('efficiency_ratio', sa.Numeric(precision=10, scale=4), nullable=True, comment='人效比'),
        sa.Column('status', sa.String(20), server_default='draft', nullable=True, comment='draft/confirmed/paid'),
        sa.Column('calculated_at', sa.DateTime(), nullable=True),
        sa.Column('confirmed_by', sa.Integer(), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['confirmed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['sales_team_config.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'year', name='uq_salary_result_user_year')
    )
    op.create_index('idx_salary_result_year_status', 'salary_calculation_result', ['year', 'status'])


def downgrade():
    """删除薪资配置相关的9个表"""

    # 按依赖关系倒序删除
    op.drop_index('idx_salary_result_year_status', table_name='salary_calculation_result')
    op.drop_table('salary_calculation_result')

    op.drop_index('idx_quarterly_performance_user_year', table_name='quarterly_performance_data')
    op.drop_table('quarterly_performance_data')

    op.drop_index('ix_employee_salary_config_grade_id', table_name='employee_salary_config')
    op.drop_index('ix_employee_salary_config_team_id', table_name='employee_salary_config')
    op.drop_index('ix_employee_salary_config_user_id', table_name='employee_salary_config')
    op.drop_table('employee_salary_config')

    op.drop_index('ix_sales_team_config_team_leader_id', table_name='sales_team_config')
    op.drop_table('sales_team_config')

    op.drop_index('ix_salary_formula_config_formula_code', table_name='salary_formula_config')
    op.drop_table('salary_formula_config')

    op.drop_index('idx_step_rules_type_threshold', table_name='salary_step_rules')
    op.drop_index('ix_salary_step_rules_rule_type', table_name='salary_step_rules')
    op.drop_table('salary_step_rules')

    op.drop_index('ix_salary_base_params_param_code', table_name='salary_base_params')
    op.drop_table('salary_base_params')

    op.drop_table('salary_grade_bandwidth')

    op.drop_index('ix_salary_grade_config_grade_type', table_name='salary_grade_config')
    op.drop_index('ix_salary_grade_config_grade_code', table_name='salary_grade_config')
    op.drop_table('salary_grade_config')
