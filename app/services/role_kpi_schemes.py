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
ROLE_KPI_SCHEMES = {
    'solution_manager': [
        {'item_code': 'se_confirm_count',   'weight': 30, 'default_annual': 240},
        {'item_code': 'se_implant_amount',  'weight': 30, 'default_annual': 12000},
        {'item_code': 'se_confirm_quality', 'weight': 15, 'default_annual': 30},
        {'item_code': 'se_sales_support',   'weight': 15, 'default_annual': 60},
        {'item_code': 'se_sales_amount',    'weight': 10, 'default_annual': 2000},
    ],
}


def get_role_scheme(role):
    """返回角色的写死考核方案(list[dict]),无方案返回 None。"""
    return ROLE_KPI_SCHEMES.get(role)


def get_role_scheme_codes(role):
    """返回角色方案的 item_code 列表,无方案返回 None。"""
    scheme = ROLE_KPI_SCHEMES.get(role)
    return [it['item_code'] for it in scheme] if scheme else None
