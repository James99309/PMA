# -*- coding: utf-8 -*-
"""绩效考核指标 名称/说明 的中英映射(渲染层 i18n)。

背景: PerformanceMetricsDefinition 表只有单字段中文 metric_name/description,
SG(英文)界面会显示中文。此处在渲染层按语言取名称/说明,无需 DB 迁移。
中文也在此处统一成「员工/HR 易懂」的口径(去掉 report_source/company_type 等技术黑话)。

用法:
    from app.helpers.metric_i18n import metric_label, metric_desc
    name = metric_label(code, fallback=m.metric_name)
    desc = metric_desc(code, fallback=m.description)
语言自动取自 session['language'](与配置页/仪表盘一致),未命中映射回退 DB 文案。
"""

# code -> {'name': {zh,en}, 'desc': {zh,en}}
METRIC_I18N = {
    # ── 销售个人 ──────────────────────────────────────────────
    'sales_target': {
        'name': {'zh': '销售额', 'en': 'Sales (closed)'},
        'desc': {'zh': '本人成交金额:已审批通过的批价单金额合计。',
                 'en': 'Your closed deals — total amount of approved pricing orders.'},
    },
    'implant_amount': {
        'name': {'zh': '植入额', 'en': 'Implant value'},
        'desc': {'zh': '本人报价单中植入的厂商产品金额合计。',
                 'en': 'Total value of vendor products embedded in your quotations.'},
    },
    'new_projects': {
        'name': {'zh': '新增项目', 'en': 'New projects'},
        'desc': {'zh': '本期本人新建的项目数量。',
                 'en': 'Number of new projects you created in the period.'},
    },
    'new_customers': {
        'name': {'zh': '新增客户', 'en': 'New customers'},
        'desc': {'zh': '本期本人新建的客户数量。',
                 'en': 'Number of new customers you added in the period.'},
    },
    'customer_activity_rate': {
        'name': {'zh': '客户活跃度', 'en': 'Customer activity rate'},
        'desc': {'zh': '本人名下客户中保持活跃(高度活跃/活跃/正常)的占比。',
                 'en': 'Share of your customers that remain active (highly active / active / normal).'},
    },
    'project_activity_rate': {
        'name': {'zh': '项目活跃度', 'en': 'Project activity rate'},
        'desc': {'zh': '本人在跟项目中近 20 天内有跟进的占比(目标 ≥90%)。',
                 'en': 'Share of your open projects followed up within the last 20 days (target ≥90%).'},
    },
    'fail_rate': {
        'name': {'zh': '个人失败率', 'en': 'Personal loss rate'},
        'desc': {'zh': '主要因个人因素丢单的项目占比;反向指标,越低越好。',
                 'en': 'Share of projects lost mainly due to personal factors; lower is better.'},
    },
    'high_price_amount': {
        'name': {'zh': '高毛利批价额', 'en': 'High-margin deal amount'},
        'desc': {'zh': '折扣率不低于 85% 的批价单金额合计。',
                 'en': 'Total pricing-order amount with a discount rate of 85% or higher.'},
    },
    'quotation_count': {
        'name': {'zh': '报价单数量', 'en': 'Quotations submitted'},
        'desc': {'zh': '本期提交的报价单数量。',
                 'en': 'Number of quotations you submitted in the period.'},
    },

    # ── 渠道经理 ──────────────────────────────────────────────
    'channel_sales_amount': {
        'name': {'zh': '渠道销售额', 'en': 'Channel sales'},
        'desc': {'zh': '渠道项目成交金额:渠道项目已审批批价单金额合计(全渠道,不限负责人)。',
                 'en': 'Closed amount from channel projects — total approved pricing orders across all channels.'},
    },
    'channel_implant_amount': {
        'name': {'zh': '渠道植入额', 'en': 'Channel implant value'},
        'desc': {'zh': '渠道项目报价中植入的厂商产品金额合计。',
                 'en': 'Total vendor-product value embedded in channel project quotations.'},
    },
    'channel_new_projects': {
        'name': {'zh': '渠道新增项目', 'en': 'New channel projects'},
        'desc': {'zh': '本期新建的渠道项目数量(全渠道)。',
                 'en': 'Number of new channel projects created in the period.'},
    },
    'channel_new_customers': {
        'name': {'zh': '渠道新增客户', 'en': 'New channel customers'},
        'desc': {'zh': '本期经销商账户名下新增的客户数量。',
                 'en': 'New customers added under dealer accounts in the period.'},
    },
    'channel_new_dealers': {
        'name': {'zh': '渠道发展(新经销商/分销商)', 'en': 'Channel development (new dealers/distributors)'},
        'desc': {'zh': '本期新增的经销商/分销商数量。',
                 'en': 'Number of new dealers/distributors recruited in the period.'},
    },
    'channel_customer_activity_rate': {
        'name': {'zh': '渠道客户活跃度', 'en': 'Channel customer activity rate'},
        'desc': {'zh': '经销商名下客户中保持活跃的占比。',
                 'en': "Share of dealers' customers that remain active."},
    },
    'channel_project_activity_rate': {
        'name': {'zh': '渠道项目活跃度', 'en': 'Channel project activity rate'},
        'desc': {'zh': '在跟渠道项目中近 20 天内有跟进的占比。',
                 'en': 'Share of open channel projects followed up within the last 20 days.'},
    },
    'channel_fail_rate': {
        'name': {'zh': '渠道失败率', 'en': 'Channel loss rate'},
        'desc': {'zh': '渠道项目中丢单的占比;反向指标(仅监控),越低越好。',
                 'en': 'Share of channel projects lost; reverse indicator (monitored), lower is better.'},
    },

    # ── 团队(销售总监/服务经理) ───────────────────────────────
    'team_sales_amount': {
        'name': {'zh': '团队销售额', 'en': 'Team sales'},
        'desc': {'zh': '本部门(含本人)成交金额合计。',
                 'en': 'Total closed amount of your department (including you).'},
    },
    'team_implant_amount': {
        'name': {'zh': '团队植入额', 'en': 'Team implant value'},
        'desc': {'zh': '本部门(含本人)报价单植入金额合计。',
                 'en': 'Total implant value in your department’s quotations (including you).'},
    },
    'team_new_projects': {
        'name': {'zh': '团队新增项目', 'en': 'Team new projects'},
        'desc': {'zh': '本部门(含本人)本期新建项目数量。',
                 'en': 'New projects created by your department (including you).'},
    },
    'team_new_customers': {
        'name': {'zh': '团队新增客户', 'en': 'Team new customers'},
        'desc': {'zh': '本部门(含本人)本期新建客户数量。',
                 'en': 'New customers added by your department (including you).'},
    },
    'team_customer_activity_rate': {
        'name': {'zh': '团队客户活跃度', 'en': 'Team customer activity rate'},
        'desc': {'zh': '本部门(含本人)名下客户中保持活跃的占比。',
                 'en': "Share of the department's customers that remain active (including yours)."},
    },
    'team_project_activity_rate': {
        'name': {'zh': '团队项目活跃度', 'en': 'Team project activity rate'},
        'desc': {'zh': '本部门(含本人)在跟项目中近 20 天内有跟进的占比(目标 ≥80%)。',
                 'en': "Share of the department's open projects followed up within 20 days (target ≥80%)."},
    },
    'team_fail_rate': {
        'name': {'zh': '团队失败率', 'en': 'Team loss rate'},
        'desc': {'zh': '部门因团队管理失责导致丢单的占比;反向指标,越低越好。',
                 'en': 'Share of department deals lost due to team-management lapses; lower is better.'},
    },
    'team_pass_rate': {
        'name': {'zh': '团队绩效合格率', 'en': 'Team pass rate'},
        'desc': {'zh': '所辖部门当季绩效达标(得分 ≥60)的成员占比(目标 80%)。',
                 'en': 'Share of your team members scoring ≥60 this quarter (target 80%).'},
    },

    # ── 解决方案经理 ─────────────────────────────────────────
    'se_implant_amount': {
        'name': {'zh': '方案植入额', 'en': 'Solution implant value'},
        'desc': {'zh': '你支持的活跃项目报价中的植入金额合计。',
                 'en': 'Implant value in the active projects you supported.'},
    },
    'se_sales_support': {
        'name': {'zh': '销售配合广度', 'en': 'Sales coverage'},
        'desc': {'zh': '本期你确认报价覆盖的销售人数。',
                 'en': 'Number of salespeople whose quotations you confirmed in the period.'},
    },
    'se_confirm_quality': {
        'name': {'zh': '植入品质', 'en': 'Implant quality'},
        'desc': {'zh': '你确认报价中推荐产品的品质均值(推荐系数越高越好)。',
                 'en': 'Average quality of recommended products in your confirmed quotations.'},
    },
    'se_training_count': {
        'name': {'zh': '技术培训', 'en': 'Technical training'},
        'desc': {'zh': '本期交付的技术培训次数。',
                 'en': 'Number of technical training sessions delivered in the period.'},
    },

    # ── 产品经理 ─────────────────────────────────────────────
    'pm_implant_amount': {
        'name': {'zh': '产品植入额', 'en': 'Product implant value'},
        'desc': {'zh': '你负责产品在报价单中的植入金额(仅厂商产品)。',
                 'en': 'Implant value of your products in quotations (vendor products only).'},
    },
    'pm_sales_amount': {
        'name': {'zh': '产品批价额', 'en': 'Product deal amount'},
        'desc': {'zh': '你负责产品的已审批批价单金额(仅厂商产品)。',
                 'en': 'Approved pricing-order amount for your products (vendor products only).'},
    },
    'pm_dev_rate': {
        'name': {'zh': '研发计划达成', 'en': 'R&D plan completion'},
        'desc': {'zh': '当期研发/迭代里程碑按计划完成的比例(按月录入,可附凭证)。',
                 'en': 'Share of R&D/iteration milestones completed on plan (entered monthly, evidence optional).'},
    },
    'pm_new_launch': {
        'name': {'zh': '新品上市', 'en': 'New product launches'},
        'desc': {'zh': '你负责范围内本期新上市的在产产品数量。',
                 'en': 'Number of products newly launched under your scope in the period.'},
    },
    'pm_quality_rate': {
        'name': {'zh': '质量处理', 'en': 'Quality pass rate'},
        'desc': {'zh': '生产批次合格率(按月录入,可上传质检报告)。',
                 'en': 'Production batch pass rate (entered monthly, QC report optional).'},
    },
    'pm_support_count': {
        'name': {'zh': '上市支持', 'en': 'Launch support'},
        'desc': {'zh': '培训/产品资料/技术支持的产出次数(按月录入)。',
                 'en': 'Count of training / product-material / technical-support outputs (entered monthly).'},
    },

    # ── 人事经理 / HRBP ──────────────────────────────────────
    'hr_recruit_count': {
        'name': {'zh': '招聘到岗', 'en': 'Hires onboarded'},
        'desc': {'zh': '本期成功到岗的人数(目标按季招聘计划设定)。',
                 'en': 'Number of hires onboarded in the period (target set by quarterly hiring plan).'},
    },
    'hr_training_count': {
        'name': {'zh': '培训组织', 'en': 'Trainings organized'},
        'desc': {'zh': '本期组织的培训次数(默认 8 次/年)。',
                 'en': 'Number of trainings organized in the period (default 8 per year).'},
    },
    'hr_team_build_count': {
        'name': {'zh': '团队建设', 'en': 'Team-building activities'},
        'desc': {'zh': '本期团建/文化活动次数(默认 4 次/年)。',
                 'en': 'Number of team-building / culture activities in the period (default 4 per year).'},
    },
    'hr_admin_count': {
        'name': {'zh': '行政/合规事务', 'en': 'Admin & compliance tasks'},
        'desc': {'zh': '本期完成的行政/合规事务次数(默认 24 次/年)。',
                 'en': 'Number of admin/compliance tasks completed in the period (default 24 per year).'},
    },
}


def _lang():
    """渲染语言: session['language'] 起头 en → 'en',否则 'zh'(与配置页/仪表盘一致)。"""
    try:
        from flask import session
        return 'en' if (session.get('language') or 'zh').lower().startswith('en') else 'zh'
    except Exception:
        return 'zh'


def metric_label(code, fallback=''):
    """指标名称(按当前语言);未命中映射回退 fallback(DB metric_name)。"""
    e = METRIC_I18N.get(code)
    if not e:
        return fallback or code
    n = e['name']
    return n.get(_lang()) or n.get('zh') or fallback or code


def metric_desc(code, fallback=''):
    """指标说明(按当前语言);未命中映射回退 fallback(DB description)。"""
    e = METRIC_I18N.get(code)
    if not e:
        return fallback or ''
    d = e['desc']
    return d.get(_lang()) or d.get('zh') or fallback or ''
