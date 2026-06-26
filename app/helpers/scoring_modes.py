# -*- coding: utf-8 -*-
"""绩效计分方式(scoring_mode)单一事实源(2026-06-14)

把原本散落在前后端多处的"反向/累计/率类"判断收敛到指标的一个属性,杜绝口径漂移。

计分方式(scoring_mode,与 data_type 正交):
- target     目标制(默认):达成率 = min(实际÷目标, 100%) × 权重
- inverse    反向目标制:实际 ≤ 目标 = 满分;否则 目标÷实际 × 权重(失败率类)
- cumulative 积分制:得分 = min(实际 × 单项得分, 权重);权重恒计入分母(不做=0分,不归一)
- tiered     固定档位制(无目标,阈值写死):实际(均值)按 及格/良好 两线换算达成率——
             及格线(TIERED_PASS=3)→50%、良好线(TIERED_GOOD=5)→100%,两线间线性,
             低于及格按比例(实际÷及格×50%),高于良好封顶 100%;权重恒计入分母。
             用于「植入品质」:目标固定不可配,配置页不出目标输入。

聚合方式(跨期取平均 vs 累加)仍由 data_type 决定:percentage/score → 取平均(水平值),
其余 → 累加。

运行时以 performance_metrics_definition.scoring_mode 为准;DB 未设(NULL)时用下方默认兜底,
保证新指标/未迁移环境也有合理行为。迁移按此默认播种 DB。
"""

# DB 未设时的兜底默认(也用于迁移播种)
SCORING_MODE_DEFAULTS = {
    # 反向(失败率类:越低越好)
    'fail_rate': 'inverse',
    'team_fail_rate': 'inverse',
    'channel_fail_rate': 'inverse',
    # 积分制(无目标,按单项得分累计封顶到权重)
    'pm_quality_rate': 'cumulative',
    'pm_new_launch': 'cumulative',
    'pm_support_count': 'cumulative',
    # 固定档位制(无目标,阈值写死):植入品质
    'se_confirm_quality': 'tiered',
}

VALID_MODES = ('target', 'inverse', 'cumulative', 'tiered')

# 固定档位阈值(植入品质,写死不可配):及格→50%、良好→100%
TIERED_PASS = 3.0   # 及格线 → 达成率 50%
TIERED_GOOD = 5.0   # 良好线 → 达成率 100%(优秀 7 仅作展示评价,KPI 封顶 100%)


def tiered_achievement(avg):
    """固定档位换算达成率(0~100):及格3→50、良好5→100,两线间线性,低于及格按比例,高于良好封顶。"""
    try:
        v = float(avg or 0)
    except (TypeError, ValueError):
        v = 0.0
    p, g = TIERED_PASS, TIERED_GOOD
    if v >= g:
        return 100.0
    if v >= p:
        return 50.0 + (v - p) / (g - p) * 50.0
    return (v / p) * 50.0 if p > 0 else 0.0


def default_scoring_mode(code):
    return SCORING_MODE_DEFAULTS.get(code, 'target')


def load_metric_meta():
    """返回 {metric_code: {'scoring_mode':..., 'data_type':...}}(全量指标,含兜底)。"""
    from app.models.performance_config import PerformanceMetricsDefinition
    out = {}
    for m in PerformanceMetricsDefinition.query.all():
        mode = getattr(m, 'scoring_mode', None) or default_scoring_mode(m.metric_code)
        out[m.metric_code] = {'scoring_mode': mode, 'data_type': m.data_type}
    return out


def scoring_mode_of(code, meta=None):
    """取单个指标的计分方式;meta 为 load_metric_meta() 结果(可选,批量时传入避免重复查)。"""
    if meta is not None:
        info = meta.get(code)
        if info:
            return info.get('scoring_mode') or default_scoring_mode(code)
    from app.models.performance_config import PerformanceMetricsDefinition
    m = PerformanceMetricsDefinition.query.filter_by(metric_code=code).first()
    return (getattr(m, 'scoring_mode', None) if m else None) or default_scoring_mode(code)


def is_avg_aggregated(data_type):
    """跨期取平均(水平值)而非累加:率类/评分类。"""
    return data_type in ('percentage', 'score')


# 水平/对齐型计数指标(2026-06-26):
# 这些是"广度/快照型"去重计数,目标是一个水平值——每期(月/季)目标都等于年度目标,
# 不做 /12、/4 摊分;实际值由 collector 按当期窗口去重计算。
# 典型:销售配合广度(se_sales_support)=本期配合过的不同销售数,年度8 即每季度都期望达到 8。
# 注意:与"流量型"计数(如技术培训次数 se_training_count,全年累计)不同,后者仍按期摊分。
LEVEL_TARGET_CODES = {'se_sales_support'}


def is_level_target(code, data_type):
    """该指标的目标是否为"水平值"(每期目标=年度值,不摊分):
    率/评分类(data_type) 或 显式登记的水平型计数(LEVEL_TARGET_CODES)。"""
    return is_avg_aggregated(data_type) or code in LEVEL_TARGET_CODES
