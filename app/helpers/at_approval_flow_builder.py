# -*- coding: utf-8 -*-
"""通用审批流数据构建 —— AT 审批 chip / 审批卡的单一数据来源。

背景:同一套「实例 → steps → records → stages」的组装逻辑此前在
`project.py:_get_project_approval_flow_impl` 与
`purchase_order_routes.py:_get_approval_flow_impl` 各写了一份(约 200 行/份),
新增 dealer_apply 时本会出现第三份。这里抽为公用函数,由各业务视图薄封装:
自己做「取对象 + 权限校验」,流程组装一律交给本模块。

当前接入方(2026-07-30):
  • project      — 项目报备审批(object_type='project')
  • project_hold — 项目失败/搁置审核(object_type='project_hold')
  • dealer_apply — 客户渠道身份审批(object_type='dealer_apply')

未接入:purchase_order —— 其 `_get_approval_flow_impl` 返回 Flask Response 且额外
带 `templates` / `can_submit`(草稿态发起用),契约与本函数不同,单独排期迁移。

返回结构(对齐 at_approval_helpers.build_approval_data + at-approval-dropdown.js 期望):
  {
    'success': True,
    'has_approval': bool,
    'approval_flow': {instance_id, stages[], current_stage, status,
                      can_approve, can_recall, can_resubmit,
                      is_creator, creator_id, started_at},
    'control_info': {can_approve, can_recall, can_resubmit},
  }
失败时返回 (dict, http_code) 二元组,与既有 project 实现一致,便于调用方
`if isinstance(result, tuple): return jsonify(result[0]), result[1]`。
"""
import logging


def build_object_approval_flow(object_type, object_id, business_object=None,
                              user_id=None, include_rejected=False,
                              no_approval_message='暂无审批流程'):
    """组装某业务对象的审批流程数据。

    Args:
        object_type:     审批实例的 object_type(project / project_hold / dealer_apply …)
        object_id:       业务对象 ID
        business_object: 业务对象实例,仅用于评估 step 的 execution_condition;
                         无条件分支的审批类型可传 None
        user_id:         视角用户(决定 can_approve / can_recall / is_creator);
                         默认当前登录用户
        include_rejected: 是否把 REJECTED 实例也纳入查找(查看历史时用)
        no_approval_message: 无审批实例时的提示文案

    Returns:
        dict 或 (dict, http_code)
    """
    from flask_login import current_user
    from app.helpers.approval_helpers import (
        get_object_approval_instance, can_recall_approval, can_resubmit_approval,
        get_step_actual_approver, _check_step_execution_condition,
    )
    from app.models.approval import ApprovalRecord

    if user_id is None:
        user_id = current_user.id

    try:
        instance = get_object_approval_instance(object_type, object_id,
                                               include_rejected=include_rejected)
        if not instance:
            return {'success': True, 'has_approval': False, 'message': no_approval_message}

        steps = instance.get_steps()
        if not steps:
            return {'success': False, 'message': '审批流程配置错误'}

        records = (ApprovalRecord.query
                   .filter_by(instance_id=instance.id)
                   .order_by(ApprovalRecord.timestamp.asc()).all())

        # current_step 可能存的是 step_order,也可能是 step_id —— 两种都认
        current_step_value = instance.current_step
        current_step_order = None
        for step in steps:
            if step.get('step_order') == current_step_value:
                current_step_order = current_step_value
                break
        if current_step_order is None:
            for step in steps:
                if step.get('step_id') == current_step_value:
                    current_step_order = step.get('step_order')
                    break

        stages_data = []
        for i, step in enumerate(steps):
            actual_approver = get_step_actual_approver(step, instance)

            step_records = []
            if step.get('step_id'):
                step_records = [r for r in records if r.step_id == step['step_id']]

            # 兜底:模板快照模式下动态 step_id 写入记录时为 NULL,按顺序对位
            if not step_records and records:
                acted = [r for r in records if r.action in ('approve', 'reject')]
                if acted and all(r.step_id is None for r in acted):
                    step_order = step.get('step_order', i + 1)
                    if step_order <= len(acted):
                        step_records = [acted[step_order - 1]]

            # 尚未到达的步骤:执行条件不满足的不显示
            if not step_records and step['step_order'] != current_step_order:
                exec_condition = step.get('execution_condition')
                if exec_condition and isinstance(exec_condition, dict):
                    if _check_step_execution_condition(step, business_object) is False:
                        continue

            stage_data = {
                'id': step['step_id'],
                'stage_name': step['step_name'],
                'stage_order': step['step_order'],
                'approver_name': actual_approver.real_name if actual_approver else '待确定',
                'approver_id': actual_approver.id if actual_approver else None,
                'status': 'pending',
                'completed_time': None,
                'comment': None,
                'action': None,
                'arrived_at': None,
                'can_approve': False,
            }

            if step_records:
                latest = step_records[-1]
                if latest.action == 'skipped':
                    continue        # 跳级的步骤不显示
                stage_data.update({
                    'status': 'approved' if latest.action == 'approve' else 'rejected',
                    'completed_time': latest.timestamp.isoformat(),
                    'comment': latest.comment,
                    'action': latest.action,
                    'arrived_at': latest.timestamp.isoformat(),
                })
            elif step['step_order'] == current_step_order:
                stage_data['status'] = 'current'
                stage_data['can_approve'] = bool(actual_approver and actual_approver.id == user_id)
            elif current_step_order and step['step_order'] < current_step_order:
                stage_data['status'] = 'approved'

            stages_data.append(stage_data)

        actual_status = (instance.status.value if hasattr(instance.status, 'value')
                         else str(instance.status).lower())
        last_record = records[-1] if records else None
        if last_record and last_record.action == 'recall':
            actual_status = 'recalled'

        _can_approve = any(s.get('can_approve', False) for s in stages_data)
        _can_recall = can_recall_approval(object_type, object_id, user_id)
        _can_resubmit = can_resubmit_approval(object_type, object_id, user_id)

        return {
            'success': True,
            'has_approval': True,
            'approval_flow': {
                'instance_id': instance.id,
                'stages': stages_data,
                'current_stage': current_step_order,
                'can_approve': _can_approve,     # 保留旧位置(向后兼容老前端)
                'status': actual_status,
                'can_recall': _can_recall,
                'can_resubmit': _can_resubmit,
                'is_creator': instance.created_by == user_id,
                'creator_id': instance.created_by,
                'started_at': (instance.started_at.strftime('%Y-%m-%d %H:%M')
                               if instance.started_at else None),
            },
            'control_info': {
                'can_approve': _can_approve,
                'can_recall': _can_recall,
                'can_resubmit': _can_resubmit,
            },
        }
    except Exception as e:
        logging.error(f"构建审批流程失败({object_type}:{object_id}):{e}")
        return ({'success': False, 'message': f'获取失败：{e}'}, 500)


def prepend_origin_node(result, initiator=None, started_at=None, comment='',
                        stage_name='发起申请'):
    """在 stages 头部插入「发起申请」节点(展示发起人 + 申请理由)。

    project_hold / dealer_apply 这类「挂在已有实体上的附加审批」都需要:
    审批人得先看到是谁、为什么发起,再决定同意与否。原地修改并返回 result。
    """
    try:
        if not (result.get('success') and result.get('has_approval')
                and result.get('approval_flow')):
            return result
        ts = started_at.isoformat() if hasattr(started_at, 'isoformat') else started_at
        result['approval_flow'].setdefault('stages', [])
        result['approval_flow']['stages'].insert(0, {
            'id': 'initiator', 'stage_name': stage_name, 'stage_order': 0,
            'approver_name': ((initiator.real_name or initiator.username)
                              if initiator else '发起人'),
            'approver_id': initiator.id if initiator else None,
            'status': 'approved', 'completed_time': ts,
            'comment': comment or '', 'action': 'submit',
            'arrived_at': ts, 'can_approve': False,
        })
    except Exception as e:
        logging.warning(f"前置发起节点失败: {e}")
    return result
