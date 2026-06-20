# -*- coding: utf-8 -*-
"""
用户操作自动记录日历工作项

提供 record_activity() 函数，将用户在 PMA 系统中的操作
（报价单创建/编辑/确认、项目创建/推进、客户创建、产品管理等）
自动记录为日历工作项（WorkItem）。

去重规则：同一用户、同一天、同一标题的操作只记录一次，
重复操作累加 actual_hours 并追加描述。create 类操作不去重。

时长计算：传入 start_time_str（操作开始时间）自动计算本次操作时长，
不传则不计算时长（仅记录时间点）。
"""
import logging
from datetime import datetime, date, time as dt_time
from flask_babel import gettext as _

logger = logging.getLogger(__name__)

# 标题前缀映射（中文 msgid，运行时通过 _() 翻译）
_TITLE_MAP_KEYS = {
    ('quotation', 'create'): '创建报价单',
    ('quotation', 'edit'): '编辑报价单',
    ('quotation', 'confirm'): '报价单确认',
    ('project', 'create'): '创建项目',
    ('project', 'advance_stage'): '项目推进',
    ('customer', 'create'): '创建客户',
    ('customer', 'edit'): '编辑客户',
    ('contact', 'create'): '创建联系人',
    ('contact', 'edit'): '编辑联系人',
    ('action', 'create'): '添加行动记录',
    ('product', 'create'): '创建产品',
    ('product', 'edit'): '编辑产品',
}


def _get_title_prefix(module, action):
    """获取翻译后的标题前缀"""
    key = _TITLE_MAP_KEYS.get((module, action))
    return _(key) if key else f'{action} {module}'

# 模块 → work_type 映射
WORK_TYPE_MAP = {
    'quotation': 'presales_support',
    'project': 'presales_support',
    'customer': 'customer_visit',
    'contact': 'customer_visit',
    'action': 'customer_maintenance',
    'product': 'product_research',
}



def _parse_time(time_str):
    """解析时间字符串 HH:MM:SS 或 HH:MM:SS.xxx"""
    try:
        parts = time_str.split(':')
        return dt_time(int(parts[0]), int(parts[1]),
                       int(parts[2].split('.')[0]))
    except (ValueError, IndexError):
        return None


def _calc_duration_hours(start_time, end_time):
    """计算两个 time 对象之间的小时数"""
    start_secs = start_time.hour * 3600 + start_time.minute * 60 + start_time.second
    end_secs = end_time.hour * 3600 + end_time.minute * 60 + end_time.second
    diff = end_secs - start_secs
    if diff < 0:
        diff = 0
    return round(diff / 3600, 2)


def record_activity(action, module, object_name, user,
                    project_id=None, customer_id=None,
                    start_time_str=None, description=None):
    """记录用户操作到日历工作项

    Args:
        action: 操作类型 (create/edit/confirm/advance_stage)
        module: 模块名 (quotation/project/customer/contact/action/product)
        object_name: 对象显示名称 (如报价单号、项目名、产品名)
        user: 当前用户对象
        project_id: 关联项目ID (可选)
        customer_id: 关联客户ID (可选)
        start_time_str: 操作开始时间 "HH:MM:SS" (可选，用于计算时长)
        description: 操作描述 (可选，去重时追加到已有描述)

    Returns:
        WorkItem 或 None
    """
    from app.models.worklog import WorkItem
    from app import db

    try:
        prefix = _get_title_prefix(module, action)
        title = f'{prefix}: {object_name}'
        work_type = WORK_TYPE_MAP.get(module, 'other')

        now = datetime.now()
        now_time = now.time().replace(microsecond=0)
        today = date.today()

        # 解析开始时间并计算时长
        start_time = now_time
        duration_hours = None
        if start_time_str:
            parsed = _parse_time(start_time_str)
            if parsed:
                start_time = parsed
                duration_hours = _calc_duration_hours(parsed, now_time)

        # 生成带时间戳的操作记录行
        time_str = now_time.strftime('%H:%M')
        log_line = f'{time_str} {description or prefix}'

        # ── 项目级聚合：有 project_id 时,同一天/同一人/同一项目的所有动作
        #    (建项目/改项目/项目下报价单增改确认/项目级跟进)合并为一条 ──
        if project_id:
            try:
                from app.models.project import Project
                _p = Project.query.get(project_id)
                proj_name = _p.project_name if _p else object_name
            except Exception:
                proj_name = object_name
            agg_title = f"{_('项目动态')}: {proj_name}"
            existing = WorkItem.query.filter(
                WorkItem.owner_id == user.id,
                WorkItem.planned_date == today,
                WorkItem.title == agg_title,
                WorkItem.is_deleted == False,
            ).first()
            if existing:
                existing.end_time = now_time
                existing.completed_at = now
                if duration_hours:
                    existing.actual_hours = round((existing.actual_hours or 0) + duration_hours, 2)
                if log_line not in (existing.description or ''):
                    existing.description = ((existing.description or '') + '\n' + log_line).strip()
                if not existing.customer_id and customer_id:
                    existing.customer_id = customer_id
                db.session.commit()
                return existing
            work_item = WorkItem(
                title=agg_title, description=log_line, planned_date=today,
                is_all_day=False, start_time=start_time, end_time=now_time,
                work_type=work_type, status='completed', completed_at=now,
                actual_hours=duration_hours, owner_id=user.id,
                project_id=project_id, customer_id=customer_id,
            )
            db.session.add(work_item)
            db.session.commit()
            return work_item

        # 去重检查：同天同用户同模块同对象合并（不跨模块）
        from sqlalchemy import or_ as sql_or
        module_titles = [
            f'{v}: {object_name}'
            for (m, _), v in _TITLE_MAP_KEYS.items() if m == module
        ]
        existing = WorkItem.query.filter(
            WorkItem.owner_id == user.id,
            WorkItem.planned_date == today,
            WorkItem.title.in_(module_titles)
        ).first() if module_titles else None
        if existing:
            existing.end_time = now_time
            existing.completed_at = now
            # 累加时长
            if duration_hours:
                existing.actual_hours = round(
                    (existing.actual_hours or 0) + duration_hours, 2)
            # 追加操作记录行（避免完全重复）
            if log_line not in (existing.description or ''):
                existing.description = (
                    (existing.description or '') + '\n' + log_line).strip()
            db.session.commit()
            return existing

        work_item = WorkItem(
            title=title,
            description=log_line,
            planned_date=today,
            is_all_day=False,
            start_time=start_time,
            end_time=now_time,
            work_type=work_type,
            status='completed',
            completed_at=now,
            actual_hours=duration_hours,
            owner_id=user.id,
            project_id=project_id,
            customer_id=customer_id,
        )
        db.session.add(work_item)
        db.session.commit()
        return work_item

    except Exception as e:
        logger.warning(f"记录活动失败 [{module}.{action}]: {e}")
        return None


# 任务动作标签（中文，聚合到 WorkItem 标题和描述）
_TASK_ACTION_LABELS = {
    'create': '创建',
    'subtask': '添加节点',
    'reply': '进展更新',
}


def _build_task_title(task_title, action_labels):
    """构建聚合任务 WorkItem 标题"""
    if action_labels == ['创建']:
        return f'创建任务: {task_title}'
    tag = '+'.join(action_labels)
    return f'任务跟进 [{tag}]: {task_title}'


def record_task_activity(action, task_id, task_title, user,
                         project_id=None, customer_id=None):
    """记录任务操作到日历工作项（同任务同天聚合为一条）

    去重规则：同一用户、同一天、同一任务（task_id）只保留一条 WorkItem，
    后续操作追加到描述并更新标题以反映所有动作。

    Args:
        action: 'create' | 'subtask' | 'reply'
        task_id: Task.id
        task_title: Task.title（显示用）
        user: 当前用户对象
        project_id: Task.project_id（可选，关联项目）
        customer_id: Task.customer_id（可选，关联客户）
    """
    from app.models.worklog import WorkItem
    from app import db

    try:
        now = datetime.now()
        now_time = now.time().replace(microsecond=0)
        today = date.today()

        action_label = _TASK_ACTION_LABELS.get(action, action)
        time_str = now_time.strftime('%H:%M')
        log_line = f'{time_str} {action_label}'
        # 描述首行作为任务标识，用于精确去重
        marker = f'#T{task_id}'

        existing = WorkItem.query.filter(
            WorkItem.owner_id == user.id,
            WorkItem.planned_date == today,
            WorkItem.work_type == 'task_work',
            WorkItem.description.like(f'{marker}%')
        ).first()

        if existing:
            # 从描述中解析已有动作（跳过首行 marker）
            lines = (existing.description or '').split('\n')
            existing_labels = [
                ln.split(' ', 1)[1] for ln in lines[1:]
                if ln.strip() and ' ' in ln
            ]
            if action_label not in existing_labels:
                existing_labels.append(action_label)
                existing.title = _build_task_title(task_title, existing_labels)
                existing.description = existing.description + '\n' + log_line
            existing.end_time = now_time
            existing.completed_at = now
            db.session.commit()
            return existing

        work_item = WorkItem(
            title=_build_task_title(task_title, [action_label]),
            description=f'{marker}\n{log_line}',
            planned_date=today,
            is_all_day=False,
            start_time=now_time,
            end_time=now_time,
            work_type='task_work',
            status='completed',
            completed_at=now,
            owner_id=user.id,
            project_id=project_id,
            customer_id=customer_id,
        )
        db.session.add(work_item)
        db.session.commit()
        return work_item

    except Exception as e:
        logger.warning(f"记录任务活动失败 [{action} T{task_id}]: {e}")
        return None
