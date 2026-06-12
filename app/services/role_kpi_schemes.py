# -*- coding: utf-8 -*-
"""角色写死考核方案(Role KPI Schemes)。

设计(2026-06-11 与用户确认):
  - 有方案的角色:考核项由本常量决定,配置页不再勾选(锁定显示),只设目标;
    避免"自由勾选选错口径指标"(如 SM 勾到 owner 口径的植入额)。
  - 无方案的角色:维持原有自由勾选(user_performance_targets enabled 语义)。
  - 权重用于季度加权评分;目标有岗位默认值,个人可在配置页覆盖
    (个人覆盖 > 角色默认 RolePerformanceTarget > 本方案 default)。

指标算法均按 metric_code 焊死(见 PerformanceService),方案只收录
"对该角色口径正确"的指标:solution_manager 全部为 confirmed_by 口径的 se_*。
"""

# default_annual: 金额类单位=万元(与 user_performance_targets 一致);
#                 count=个/年;rate=%(参考值,月度沿用系统现有 rate 约定)。
# 销售个人方案(销售经理/客户销售共用)与团队管理方案(营销总监/服务经理共用)
# 在 dict 尾部以同一列表引用挂载多角色,调整一处全部生效。
ROLE_KPI_SCHEMES = {
    'solution_manager': [
        {'item_code': 'se_confirm_count',   'weight': 30, 'default_annual': 240},
        {'item_code': 'se_implant_amount',  'weight': 30, 'default_annual': 12000},
        {'item_code': 'se_confirm_quality', 'weight': 15, 'default_annual': 30},
        {'item_code': 'se_sales_support',   'weight': 15, 'default_annual': 60},
        {'item_code': 'se_sales_amount',    'weight': 10, 'default_annual': 2000},
    ],
    # 销售经理(2026-06-12 与用户确认固化):
    # 销售目标(批价)/植入额/新增客户/新增项目/客户活跃度/项目活跃度(共 6 项);
    # 金额数量类 default_annual 留空(因人差异大,在角色默认或个人覆盖中填),
    # 率类给参考水平值;权重为默认值,配置页可调。
    'sales_manager': [
        {'item_code': 'sales_target',           'weight': 30, 'default_annual': None},
        {'item_code': 'implant_amount',         'weight': 20, 'default_annual': None},
        {'item_code': 'new_projects',           'weight': 15, 'default_annual': None},
        {'item_code': 'new_customers',          'weight': 15, 'default_annual': None},
        {'item_code': 'customer_activity_rate', 'weight': 10, 'default_annual': 100},
        {'item_code': 'project_activity_rate',  'weight': 10, 'default_annual': 90},
        # 反向指标(≤目标为达标):目标与权重自行在配置页设定,默认不占权重
        {'item_code': 'fail_rate',              'weight': 0,  'default_annual': None},
    ],
    # 营销总监(管理岗,2026-06-12 确认):全部团队(=本部门成员含本人)口径,
    # 结构对齐销售经理;团队项目活跃度目标 80%(超期 ≤20%)。
    'sales_director': [
        {'item_code': 'team_sales_amount',           'weight': 30, 'default_annual': None},
        {'item_code': 'team_implant_amount',         'weight': 20, 'default_annual': None},
        {'item_code': 'team_new_projects',           'weight': 15, 'default_annual': None},
        {'item_code': 'team_new_customers',          'weight': 15, 'default_annual': None},
        {'item_code': 'team_customer_activity_rate', 'weight': 10, 'default_annual': 100},
        {'item_code': 'team_project_activity_rate',  'weight': 10, 'default_annual': 80},
        # 反向指标(≤目标为达标):目标与权重自行在配置页设定,默认不占权重
        {'item_code': 'team_fail_rate',               'weight': 0,  'default_annual': None},
    ],
}

# 客户销售 = 销售经理同款个人方案;服务经理 = 营销总监同款团队方案(2026-06-12 确认)
ROLE_KPI_SCHEMES['customer_sales'] = ROLE_KPI_SCHEMES['sales_manager']
ROLE_KPI_SCHEMES['service_manager'] = ROLE_KPI_SCHEMES['sales_director']

# 渠道经理:销售方案同构,但口径为全量渠道业务(report_source/source='channel',不限负责人)
ROLE_KPI_SCHEMES['channel_manager'] = [
    {'item_code': 'channel_sales_amount',           'weight': 30, 'default_annual': None},
    {'item_code': 'channel_implant_amount',         'weight': 20, 'default_annual': None},
    {'item_code': 'channel_new_projects',           'weight': 10, 'default_annual': None},
    {'item_code': 'channel_new_customers',          'weight': 10, 'default_annual': None},
    {'item_code': 'channel_new_dealers',            'weight': 10, 'default_annual': None},
    {'item_code': 'channel_customer_activity_rate', 'weight': 10, 'default_annual': 100},
    {'item_code': 'channel_project_activity_rate',  'weight': 10, 'default_annual': 90},
    {'item_code': 'channel_fail_rate',              'weight': 0,  'default_annual': None},
]


def get_role_scheme(role):
    """返回角色的写死考核方案(list[dict]),无方案返回 None。"""
    return ROLE_KPI_SCHEMES.get(role)


def get_role_scheme_codes(role):
    """返回角色方案的 item_code 列表,无方案返回 None。"""
    scheme = ROLE_KPI_SCHEMES.get(role)
    return [it['item_code'] for it in scheme] if scheme else None
