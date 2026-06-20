# -*- coding: utf-8 -*-
"""
AT 项目详情专用 helpers — 与 `at_purchase_order_helpers` 同范式

把项目 ORM + `_get_project_approval_flow_impl()` 返回结果转成 AT 通用宏所需的 dict。
"""


def build_approval_data(project, approval_flow_impl_result=None):
    """
    Project 专用 thin wrapper — 通用逻辑见 app.helpers.at_approval_helpers.build_approval_data

    Args:
        project: Project ORM(`p.owner` 作为第 0 节点的发起人,started_at 作为提交时间)
        approval_flow_impl_result: `_get_project_approval_flow_impl(project_id)` 的返回
            (dict 或 (dict, status_code) 元组,本 helper 会兜底解元组)

    Returns:
        dict 或 None
    """
    from app.helpers.at_approval_helpers import build_approval_data as _build

    # 兜底解元组(_impl 异常路径返回 (dict, code))
    flow_result = approval_flow_impl_result
    if isinstance(flow_result, tuple):
        flow_result = flow_result[0]

    # 起始时间:优先用 approval_flow.started_at,fallback 项目创建时间
    started_at = None
    if flow_result and isinstance(flow_result, dict):
        af = flow_result.get('approval_flow') or {}
        started_at = af.get('started_at')
    if not started_at and project is not None:
        started_at = getattr(project, 'created_at', None)

    submitter = getattr(project, 'owner', None)
    return _build(submitter=submitter, submitted_at=started_at, flow_result=flow_result)
