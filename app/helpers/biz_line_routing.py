# -*- coding: utf-8 -*-
"""审批的业务线分流:项目 → 业务线 → 审批角色链。单一来源,禁止再各处拷贝。

为什么要收口(2026-07-14):
  同一套「渠道/服务/销售」分流在 4 处各写各的,判据还不一致 ——
    · 项目报备/失败/搁置:`project_type == 'channel_follow' or report_source == 'channel'`
    · 项目成功锁定:  只看 report_source,压根没看类型
    · 报备通过回填厂商销售负责人:同样掺了 report_source
  结果「国航股份浙江分公司新园区」类型明明是 sales_focus(销售重点),只因报备来源是
  channel,报备审批就被派给了渠道经理,而不是营销总监。

规则(用户 2026-07-14 确认):
  **业务线只看项目类型(project_type),不看报备来源(report_source)。**
  报备来源是"这条线索哪来的",与"该谁审"无关 —— 渠道来源的销售项目仍是销售项目。

渠道线审批人 = 渠道总监(channel_director) 优先,缺位再退渠道经理 → 营销总监。
"""

# 业务线 → 审批角色链(按优先级;逐个找在职用户,找不到就退下一个)
APPROVER_ROLE_CHAIN = {
    'service': ['service_manager', 'sales_director'],
    # 2026-08-31 用户确认:渠道线审批统一走商务(business_admin=童蕾)。
    # 渠道总监(刘军)已停用、渠道经理(徐侠)不再参与审批 —— 把 business_admin 置于
    # 渠道链首位,而不是删模板步骤:人事是暂时空缺,将来渠道岗补齐只需摘掉这一位,
    # 流程结构不动。销售/服务两线不受影响。
    # 副作用(已确认为期望行为):报备三级里商务初审与业务线经理会解析成同一人,
    # submit_project_report_approval 的逐级去重会自动跳过商务初审级,童蕾只批一次。
    'channel': ['business_admin', 'channel_director', 'channel_manager', 'sales_director'],
    'sales':   ['sales_director'],
}

# 渠道线可担任审批的角色(用于反向识别:某审批人是不是渠道线负责人)
CHANNEL_APPROVER_ROLES = ('channel_director', 'channel_manager')


def biz_line_of(project, owner=None):
    """项目 → 业务线('service' | 'channel' | 'sales')。

    只认 project_type;另外负责人本身属服务线(服务经理/服务部门)时归服务线 ——
    这是既有规则,保留:服务经理的项目该由其上级审,不能落到平级营销总监。
    """
    owner = owner if owner is not None else getattr(project, 'owner', None)
    project_type = (getattr(project, 'project_type', '') or '')

    owner_is_service = bool(owner) and (
        (owner.role == 'service_manager') or ('服务' in (owner.department or ''))
    )
    if project_type == 'business_opportunity' or owner_is_service:
        return 'service'
    if project_type == 'channel_follow':
        return 'channel'
    return 'sales'   # sales_focus / sales_key / 其余


def approver_role_chain(project, owner=None):
    """项目 → 按优先级排列的审批角色链。"""
    return APPROVER_ROLE_CHAIN[biz_line_of(project, owner)]
