# -*- coding: utf-8 -*-
"""
AT 审批流 · 通用数据构造

把后端 `_get_approval_flow_impl` / `get_approval_flow` 之类的 jsonify 结果
转换成 `at_approval_flow` 宏期望的形态:

    {
      'status': 'approved' | 'pending' | 'rejected',
      'nodes': [{role, name, status, date, action, rejected?, skipped?}],
      'duration': <int days>,
      'instance_id': <int|None>,
      'can_approve': <bool>,
    }

不耦合任何特定业务对象(PO / SO / Quotation / Expense ...),调用方按本对象
情况传入 `submitter` + `submitted_at`(作为第 0 节点)即可。
"""
from datetime import datetime, date


def _fmt_date(d):
    """统一日期格式化为 YYYY-MM-DD;接受 datetime / date / str。"""
    if not d:
        return None
    if isinstance(d, (datetime, date)):
        return d.strftime('%Y-%m-%d')
    s = str(d)
    if len(s) >= 10:
        return s[:10]
    return s


def _to_date(s):
    if not s:
        return None
    if isinstance(s, datetime):
        return s.date()
    if isinstance(s, date):
        return s
    try:
        return datetime.strptime(str(s)[:10], '%Y-%m-%d').date()
    except Exception:
        return None


def build_approval_data(submitter, submitted_at, flow_result):
    """
    Args:
        submitter:     User ORM(或 None),用作"提交审批"第 0 节点的人名
        submitted_at:  datetime / date / str,第 0 节点完成时间
        flow_result:   `_get_approval_flow_impl()` 等价物的返回(已 unwrap jsonify
                       成 dict),需含:
                         success: bool
                         approval_flow: {status, instance_id, stages, started_at}
                         control_info: {can_approve, ...}

    Returns:
        dict 或 None(未提交审批 / 无数据)
    """
    if not flow_result or not flow_result.get('success'):
        return None
    flow = flow_result.get('approval_flow')
    if not flow:
        return None

    raw_status = (flow.get('status') or '').lower()
    if raw_status in ('approved', 'completed'):
        status = 'approved'
    elif raw_status in ('rejected', 'failed'):
        status = 'rejected'
    else:
        status = 'pending'

    stages = flow.get('stages', [])
    nodes = []
    started = flow.get('started_at') or _fmt_date(submitted_at)
    ended_dates = []

    # 第 0 节点:发起人提交(只要审批已启动就一定完成)
    submitter_name = '—'
    if submitter is not None:
        submitter_name = getattr(submitter, 'real_name', None) or getattr(submitter, 'username', None) or '—'
    nodes.append({
        'role':   '提交审批',
        'name':   submitter_name,
        'status': 'done',
        'date':   _fmt_date(submitted_at),
        'action': '已提交',
        'rejected': False,
        'skipped':  False,
    })

    for st in stages:
        st_status = st.get('status', 'pending')
        if st_status == 'approved':
            node_status = 'done'
        elif st_status == 'current':
            node_status = 'current'
        elif st_status == 'rejected':
            node_status = 'done'   # 节点本身已完成(以驳回收尾)
        elif st_status == 'skipped':
            node_status = 'done'
        else:
            node_status = 'pending'

        completed_time = st.get('completed_time')
        if completed_time:
            ended_dates.append(completed_time)

        action_label = None
        if st_status == 'approved':
            action_label = '已通过'
        elif st_status == 'rejected':
            action_label = '已驳回'
        elif st_status == 'skipped':
            action_label = '已跳过'

        nodes.append({
            'role':   st.get('stage_name') or '审批',
            'name':   st.get('approver_name') or '待分配',
            'status': node_status,
            'date':   _fmt_date(completed_time) if completed_time else None,
            'action': action_label,
            'rejected': st_status == 'rejected',
            'skipped':  st_status == 'skipped',
        })

    # 总时长(天)— 仅 approved 显示
    duration = 0
    if status == 'approved' and ended_dates and started:
        try:
            last = max(_to_date(d) for d in ended_dates if _to_date(d))
            first = _to_date(started)
            if last and first:
                duration = (last - first).days
        except Exception:
            duration = 0

    control_info = flow_result.get('control_info') or {}
    return {
        'status':       status,
        'nodes':        nodes,
        'duration':     max(0, duration),
        'instance_id':  flow.get('instance_id'),
        'can_approve':  bool(control_info.get('can_approve')),
    }
