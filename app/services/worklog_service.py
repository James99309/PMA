# -*- coding: utf-8 -*-
"""工作日历/日志「读侧」业务服务(鉴权无关) — web 路由与 mobile API 共用单一来源

从 app/views/worklog.py 的厚路由抽出,**忠实保留原行为与副作用顺序**:
- 权限矩阵 / 智能工时 / 质量评分回写 全部在此统一,使 web 与 mobile 行为 100% 一致
- get_subordinate_user_ids / get_daily_activities 迁入本模块,
  web(app/views/worklog.py) 反向 import 保持向后兼容

约定(与 app/services/task_service.py 一致):
- `user` 传 User 对象(web 传 current_user,mobile 传 User.query.get(uid))
- **鉴权由调用方在边缘做**;查看他人的权限矩阵忠实搬运在 can_view_user
- 用户不存在 → 抛 WorklogUserNotFound;无权查看 → 抛 WorklogPermissionDenied
  (调用方分别映射 404 / 403,与原 web 行为一致)
- 本服务自管 commit(与原 web 每路由 commit 一致)
"""
import logging
from datetime import datetime, date, timedelta

from sqlalchemy import or_, cast, text
from sqlalchemy.dialects.postgresql import JSONB

from app import db
from app.models.worklog import WorkItem, WorkLog, WorkLogReaction
from app.models.worklog_read import WorklogRead
from app.models.user import User, Affiliation
from app.models.expense import Department
from app.models.project import Project
from app.models.customer import Company, Contact
from app.models.quotation import Quotation
from app.models.pricing_order import PricingOrder
from app.models.action import Action
from app.permissions import is_admin_or_ceo
from flask_babel import gettext as _
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


class WorklogUserNotFound(Exception):
    """目标用户不存在(调用方映射 404)"""


class WorklogPermissionDenied(Exception):
    """无权查看目标用户的工作日历(调用方映射 403)"""


# ===== 工具函数(自 app/views/worklog.py 忠实迁入) =====

def get_subordinate_user_ids(user):
    """获取下属用户ID列表（可查看其数据的用户）"""
    # 通过 Affiliation 表查询：viewer_id 是当前用户，owner_id 是下属
    # Affiliation 表示：viewer 可以查看 owner 的数据
    affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
    return [a.owner_id for a in affiliations]


def get_daily_activities(user_id, target_date):
    """获取当天的行动记录（创建或修改的业务数据）"""
    # 目标日期的开始和结束时间
    start_of_day = datetime.combine(target_date, datetime.min.time())
    end_of_day = datetime.combine(target_date, datetime.max.time())

    activities = {
        'customers': {'created': [], 'updated': []},
        'contacts': {'created': [], 'updated': []},
        'projects': {'created': [], 'updated': []},
        'quotations': {'created': [], 'updated': []},
        'orders': {'created': [], 'updated': []},
        'actions': {'created': []},
        'summary': {
            'customers_created': 0,
            'customers_updated': 0,
            'contacts_created': 0,
            'contacts_updated': 0,
            'projects_created': 0,
            'projects_updated': 0,
            'quotations_created': 0,
            'quotations_updated': 0,
            'orders_created': 0,
            'orders_updated': 0,
            'actions_created': 0,
            'total_created': 0,
            'total_updated': 0
        }
    }

    # 查询客户（Company）
    created_customers = Company.query.filter(
        Company.owner_id == user_id,
        Company.is_deleted == False,
        Company.created_at >= start_of_day,
        Company.created_at <= end_of_day
    ).all()
    activities['customers']['created'] = [
        {'id': c.id, 'name': c.company_name}
        for c in created_customers
    ]
    activities['summary']['customers_created'] = len(created_customers)

    # 更新的客户（排除当天创建的）
    updated_customers_query = Company.query.filter(
        Company.owner_id == user_id,
        Company.is_deleted == False,
        Company.updated_at >= start_of_day,
        Company.updated_at <= end_of_day
    )
    if created_customers:
        updated_customers_query = updated_customers_query.filter(~Company.id.in_([c.id for c in created_customers]))
    updated_customers = updated_customers_query.all()
    activities['customers']['updated'] = [
        {'id': c.id, 'name': c.company_name}
        for c in updated_customers
    ]
    activities['summary']['customers_updated'] = len(updated_customers)

    # 查询联系人（Contact）- Contact 没有 is_deleted 字段
    created_contacts = Contact.query.filter(
        Contact.owner_id == user_id,
        Contact.created_at >= start_of_day,
        Contact.created_at <= end_of_day
    ).all()
    activities['contacts']['created'] = [
        {'id': c.id, 'name': c.name, 'company_name': c.company.company_name if c.company else None}
        for c in created_contacts
    ]
    activities['summary']['contacts_created'] = len(created_contacts)

    updated_contacts_query = Contact.query.filter(
        Contact.owner_id == user_id,
        Contact.updated_at >= start_of_day,
        Contact.updated_at <= end_of_day
    )
    if created_contacts:
        updated_contacts_query = updated_contacts_query.filter(~Contact.id.in_([c.id for c in created_contacts]))
    updated_contacts = updated_contacts_query.all()
    activities['contacts']['updated'] = [
        {'id': c.id, 'name': c.name, 'company_name': c.company.company_name if c.company else None}
        for c in updated_contacts
    ]
    activities['summary']['contacts_updated'] = len(updated_contacts)

    # 查询项目（Project）- 仅查询活跃项目
    created_projects = Project.query.filter(
        Project.owner_id == user_id,
        Project.is_active == True,
        Project.created_at >= start_of_day,
        Project.created_at <= end_of_day
    ).all()
    activities['projects']['created'] = [
        {'id': p.id, 'name': p.project_name}
        for p in created_projects
    ]
    activities['summary']['projects_created'] = len(created_projects)

    updated_projects_query = Project.query.filter(
        Project.owner_id == user_id,
        Project.is_active == True,
        Project.updated_at >= start_of_day,
        Project.updated_at <= end_of_day
    )
    if created_projects:
        updated_projects_query = updated_projects_query.filter(~Project.id.in_([p.id for p in created_projects]))
    updated_projects = updated_projects_query.all()
    activities['projects']['updated'] = [
        {'id': p.id, 'name': p.project_name}
        for p in updated_projects
    ]
    activities['summary']['projects_updated'] = len(updated_projects)

    # 查询报价单（Quotation）- Quotation 没有 is_deleted 字段
    created_quotations = Quotation.query.filter(
        Quotation.owner_id == user_id,
        Quotation.created_at >= start_of_day,
        Quotation.created_at <= end_of_day
    ).all()
    activities['quotations']['created'] = [
        {'id': q.id, 'name': q.quotation_number or f'报价单#{q.id}', 'customer_name': q.customer.company_name if q.customer else None}
        for q in created_quotations
    ]
    activities['summary']['quotations_created'] = len(created_quotations)

    updated_quotations_query = Quotation.query.filter(
        Quotation.owner_id == user_id,
        Quotation.updated_at >= start_of_day,
        Quotation.updated_at <= end_of_day
    )
    if created_quotations:
        updated_quotations_query = updated_quotations_query.filter(~Quotation.id.in_([q.id for q in created_quotations]))
    updated_quotations = updated_quotations_query.all()
    activities['quotations']['updated'] = [
        {'id': q.id, 'name': q.quotation_number or f'报价单#{q.id}', 'customer_name': q.customer.company_name if q.customer else None}
        for q in updated_quotations
    ]
    activities['summary']['quotations_updated'] = len(updated_quotations)

    # 查询批价单（PricingOrder）- 使用 created_by 字段
    created_orders = PricingOrder.query.filter(
        PricingOrder.created_by == user_id,
        PricingOrder.created_at >= start_of_day,
        PricingOrder.created_at <= end_of_day
    ).all()
    activities['orders']['created'] = [
        {'id': o.id, 'name': o.order_number or f'批价单#{o.id}', 'customer_name': o.dealer.company_name if o.dealer else None}
        for o in created_orders
    ]
    activities['summary']['orders_created'] = len(created_orders)

    updated_orders_query = PricingOrder.query.filter(
        PricingOrder.created_by == user_id,
        PricingOrder.updated_at >= start_of_day,
        PricingOrder.updated_at <= end_of_day
    )
    if created_orders:
        updated_orders_query = updated_orders_query.filter(~PricingOrder.id.in_([o.id for o in created_orders]))
    updated_orders = updated_orders_query.all()
    activities['orders']['updated'] = [
        {'id': o.id, 'name': o.order_number or f'批价单#{o.id}', 'customer_name': o.dealer.company_name if o.dealer else None}
        for o in updated_orders
    ]
    activities['summary']['orders_updated'] = len(updated_orders)

    # 查询行动记录（Action）- 项目/客户下添加的行动
    # 使用 Action.date（行动日期）而非 created_at（创建时间戳）
    # 这样当用户在今天完成昨天的工作项时，行动记录能正确显示在昨天的日志中

    # 获取当天已完成的带客户或项目关联的工作项，用于排除重复的行动记录
    # 当工作项完成时勾选"同步行动记录"会创建 Action，这里需要排除这些重复的
    completed_work_items = WorkItem.query.filter(
        WorkItem.owner_id == user_id,
        or_(WorkItem.planned_date == target_date, WorkItem.end_date == target_date),
        WorkItem.status == 'completed',
        WorkItem.is_deleted == False,
        or_(WorkItem.customer_id.isnot(None), WorkItem.project_id.isnot(None))
    ).all()

    # 收集需要排除的 (customer_id, project_id) 组合
    excluded_pairs = {(w.customer_id, w.project_id) for w in completed_work_items}

    # 查询当天的行动记录
    created_actions = Action.query.filter(
        Action.owner_id == user_id,
        Action.date == target_date
    ).all()

    # 过滤掉与工作项重复的行动记录（相同 customer_id + project_id 组合）
    filtered_actions = [
        a for a in created_actions
        if (a.company_id, a.project_id) not in excluded_pairs
    ]

    activities['actions']['created'] = [
        {
            'id': a.id,
            'content': a.communication or '',  # 返回完整内容
            'project_name': a.project.project_name if a.project else None,
            'customer_name': a.company.company_name if a.company else None
        }
        for a in filtered_actions
    ]
    activities['summary']['actions_created'] = len(filtered_actions)

    # 计算总数
    activities['summary']['total_created'] = (
        activities['summary']['customers_created'] +
        activities['summary']['contacts_created'] +
        activities['summary']['projects_created'] +
        activities['summary']['quotations_created'] +
        activities['summary']['orders_created'] +
        activities['summary']['actions_created']
    )
    activities['summary']['total_updated'] = (
        activities['summary']['customers_updated'] +
        activities['summary']['contacts_updated'] +
        activities['summary']['projects_updated'] +
        activities['summary']['quotations_updated'] +
        activities['summary']['orders_updated']
    )

    return activities


# ===== 权限矩阵(自 get_items 忠实搬运,鉴权无关) =====

def can_view_user(user, owner_id):
    """user 能否查看 owner_id 的工作日历(忠实搬 get_items 权限矩阵)

    - 目标用户不存在 → 抛 WorklogUserNotFound(调用方映射 404)
    - 有权 → True;无权 → False(调用方映射 403)
    """
    target_user = User.query.get(owner_id)
    if not target_user:
        raise WorklogUserNotFound()

    # 获取 worklog 模块权限级别
    worklog_permission = user.get_permission_level('worklog')

    # 判断是否有权查看目标用户
    can_view_target = False

    if is_admin_or_ceo(user) or worklog_permission == 'system':
        # 管理员/CEO 或 system 级权限：可查看所有人
        can_view_target = True
    elif worklog_permission == 'company':
        # company 级权限：可查看同公司用户
        can_view_target = target_user.company_name == user.company_name
    elif worklog_permission == 'department' or user.is_department_manager:
        # department 级权限或部门负责人：可查看同部门/管理部门的用户
        managed_depts = Department.query.filter_by(manager_id=user.id).all()
        managed_dept_names = [d.name for d in managed_depts]
        if user.department and user.department not in managed_dept_names:
            managed_dept_names.append(user.department)
        can_view_target = target_user.department in managed_dept_names

    # 检查是否是数据归属下属
    if not can_view_target:
        subordinate_ids = get_subordinate_user_ids(user)
        can_view_target = owner_id in subordinate_ids

    return can_view_target


# ===== 日期范围解析(供 web / mobile 共用,消除默认逻辑漂移) =====

def parse_calendar_range(start_str, end_str):
    """解析 FullCalendar/mobile 传入的 start/end,忠实搬 get_items 默认与容错逻辑"""
    try:
        if start_str:
            start_date = datetime.fromisoformat(start_str.replace('Z', '+00:00')).date()
        else:
            start_date = date.today().replace(day=1)

        if end_str:
            end_date = datetime.fromisoformat(end_str.replace('Z', '+00:00')).date()
        else:
            # 默认显示当月
            next_month = start_date.replace(day=28) + timedelta(days=4)
            end_date = next_month.replace(day=1)
    except (ValueError, AttributeError):
        start_date = date.today().replace(day=1)
        next_month = start_date.replace(day=28) + timedelta(days=4)
        end_date = next_month.replace(day=1)
    return start_date, end_date


# ===== 读侧主入口(自 get_items / get_daily_log 忠实抽取) =====

def _scoped_item_query(user, owner_id, start_date, end_date, columns=None):
    """统一「可见工作项」查询(忠实抽取 get_items 的权限+范围+日期过滤)。

    owner_id 非空 → can_view_user 权限校验(用户不存在抛 WorklogUserNotFound,
    无权抛 WorklogPermissionDenied);否则 本人 + 共享给本人。
    columns 为空 → 完整 ORM 查询(WorkItem.query,Agenda 事件用);
    给定列 → 轻量列查询(月视图聚合用,不触发关系/N+1)。
    """
    if owner_id:
        # 校验权限：基于 worklog 模块权限配置(用户不存在抛 WorklogUserNotFound→404)
        if not can_view_user(user, owner_id):
            raise WorklogPermissionDenied()
        scope = (WorkItem.owner_id == owner_id,)
    else:
        # 默认：当前用户的工作项 + 共享给当前用户的工作项
        scope = (
            or_(
                WorkItem.owner_id == user.id,
                # shared_with_users JSON 数组是否含当前用户ID(text() 包 JSONB 字面量)
                cast(WorkItem.shared_with_users, JSONB).op('@>')(text(f"'[{user.id}]'::jsonb"))
            ),
        )
    base = db.session.query(*columns) if columns else WorkItem.query
    return base.filter(
        WorkItem.is_deleted == False,
        WorkItem.planned_date >= start_date,
        WorkItem.planned_date < end_date,
        *scope
    )


def _log_status_dates(user, owner_id, start_date, end_date):
    """日志已读/未读/已提交日期集合(忠实抽取 get_items 同段,web/mobile 单一来源)。"""
    if owner_id:
        # 查询指定用户在日期范围内的日志
        logs = WorkLog.query.filter(
            WorkLog.owner_id == owner_id,
            WorkLog.log_date >= start_date,
            WorkLog.log_date < end_date,
            WorkLog.status == 'submitted'  # 只显示已提交的日志
        ).all()

        if logs:
            # 获取当前用户已读的日志ID
            log_ids = [log.id for log in logs]
            read_log_ids = WorklogRead.get_read_worklog_ids(user.id, log_ids)

            # 分类：未读和已读
            dates_with_unread_logs = []
            dates_with_read_logs = []

            for log in logs:
                date_str = log.log_date.isoformat()
                if log.id in read_log_ids:
                    dates_with_read_logs.append(date_str)
                else:
                    dates_with_unread_logs.append(date_str)

            return {
                'datesWithUnreadLogs': list(set(dates_with_unread_logs)),
                'datesWithReadLogs': list(set(dates_with_read_logs)),
            }
        return {'datesWithUnreadLogs': [], 'datesWithReadLogs': []}

    # 查看自己的日历：返回已提交日志的日期（显示绿点）
    submitted_logs = WorkLog.query.filter(
        WorkLog.owner_id == user.id,
        WorkLog.log_date >= start_date,
        WorkLog.log_date < end_date,
        WorkLog.status == 'submitted'
    ).all()
    return {'datesWithSubmittedLogs': list(set(
        log.log_date.isoformat() for log in submitted_logs
    ))}


def get_viewable_items(user, start_date, end_date, owner_id=None):
    """获取日历事件列表（FullCalendar 数据源）忠实抽取 get_items

    owner_id 为空 → 自己+共享给自己的工作项
    owner_id 非空 → 校验权限矩阵后返回该用户工作项 + 日志已读/未读状态
    返回 dict: {events, datesWithItems, [datesWith{Submitted/Unread/Read}Logs]}
    """
    query = _scoped_item_query(user, owner_id, start_date, end_date)
    items = query.order_by(WorkItem.planned_date, WorkItem.start_time).all()

    # 转换为 FullCalendar 事件格式，传入当前用户ID用于判断是否是所有者
    events = [item.to_calendar_event(current_user_id=user.id) for item in items]

    # 获取有工作项的日期集合（用于前端高亮）
    dates_with_items = list(set(item.planned_date.isoformat() for item in items))

    result = {
        'events': events,
        'datesWithItems': dates_with_items
    }
    result.update(_log_status_dates(user, owner_id, start_date, end_date))
    return result


def get_month_overview(user, start_date, end_date, owner_id=None):
    """月视图轻量聚合源(C2 perf):仅取 planned_date+work_type,不构建事件/不触关系。

    权限/范围/日志状态与 get_viewable_items 同一来源
    (_scoped_item_query / _log_status_dates),仅把逐条 to_calendar_event
    换成轻量列查询,大幅降月视图延迟。
    返回 {items:[(date_iso, work_type)], datesWithItems, datesWith*Logs}
    """
    rows = _scoped_item_query(
        user, owner_id, start_date, end_date,
        columns=[WorkItem.planned_date, WorkItem.work_type]
    ).all()
    items = [(r[0].isoformat(), r[1]) for r in rows]
    result = {
        'items': items,
        'datesWithItems': list({d for d, _wt in items}),
    }
    result.update(_log_status_dates(user, owner_id, start_date, end_date))
    return result


def get_day(user, target_date, owner_id=None):
    """获取某日日志数据 忠实抽取 get_daily_log(含质量评分回写)

    owner_id 非空且 != user.id → 查看他人(只读,仅 submitted;无则 no_log)
    否则 → 自己(可编辑,get_or_create)
    返回 data dict(调用方包 {'success': True, 'data': data})
    """
    # 检查是否查看他人日志
    is_readonly = False

    if owner_id and owner_id != user.id:
        # 查看他人日志 - 只读模式
        is_readonly = True
        target_user_id = owner_id

        # 只查询已提交的日志（草稿不对外展示）
        worklog = WorkLog.query.filter_by(
            owner_id=owner_id,
            log_date=target_date,
            status='submitted'  # 只返回已提交的日志
        ).first()

        if not worklog:
            return {
                'log': None,
                'completed_items': [],
                'pending_items': [],
                'cancelled_items': [],
                'statistics': {},
                'activities': {},
                'is_readonly': True,
                'no_log': True
            }
    else:
        # 查看自己的日志 - 可编辑
        target_user_id = user.id
        worklog = WorkLog.get_or_create(user.id, target_date)
        db.session.commit()

    # 获取当天的所有工作项
    work_items = WorkItem.query.filter(
        WorkItem.planned_date == target_date,
        WorkItem.is_deleted == False,
        WorkItem.owner_id == target_user_id
    ).order_by(WorkItem.created_at).all()

    # 分类工作项
    completed_items = [i.to_dict() for i in work_items if i.status == 'completed']
    pending_items = [i.to_dict() for i in work_items if i.status == 'planned']
    cancelled_items = [i.to_dict() for i in work_items if i.status == 'cancelled']

    # 计算统计数据（使用智能工时计算：去重、扣除午休、上限8小时）
    stats = {
        'total_items': len(work_items),
        'completed_items': len(completed_items),
        'pending_items': len(pending_items),
        'total_hours': WorkLog._calculate_hours_for_items(work_items),  # 智能计算
        'project_count': len(set(i.project_id for i in work_items if i.project_id)),
        'customer_count': len(set(i.customer_id for i in work_items if i.customer_id))
    }

    # 查询当天的行动记录（创建或修改的业务数据）
    activities = get_daily_activities(target_user_id, target_date)

    # 获取日志所有者信息
    log_data = worklog.to_dict()
    if is_readonly:
        owner = User.query.get(owner_id)
        if owner:
            log_data['owner_display_name'] = owner.real_name or owner.username

    # 获取反馈数据（匿名点赞/点踩）
    user_reaction = None
    if worklog.id:
        # 查询当前用户是否已反馈
        existing_reaction = WorkLogReaction.query.filter_by(
            worklog_id=worklog.id,
            user_id=user.id
        ).first()
        if existing_reaction:
            user_reaction = existing_reaction.reaction_type

    reactions_data = {
        'thumbs_up': worklog.thumbs_up_count or 0,
        'thumbs_down': worklog.thumbs_down_count or 0,
        'user_reaction': user_reaction,
        # 是否可以反馈：已提交的日志 且 不是自己的日志
        'can_react': worklog.status == 'submitted' and worklog.owner_id != user.id
    }

    # 获取质量评分（仅已提交日志）
    quality_score = None
    if worklog.status == 'submitted' and worklog.id:
        # 获取系统行为数据
        daily_activities = get_daily_activities(target_user_id, target_date)
        summary = daily_activities.get('summary', {})
        system_activities = {
            'new_customers': summary.get('customers_created', 0),
            'updated_customers': summary.get('customers_updated', 0),
            'new_contacts': summary.get('contacts_created', 0),
            'new_projects': summary.get('projects_created', 0),
            'updated_projects': summary.get('projects_updated', 0),
            'new_actions': summary.get('actions_created', 0),
            'new_quotations': summary.get('quotations_created', 0)
        }

        # 每次都用最新模型计算评分（确保与当前评分规则一致）
        quality_score = worklog.calculate_quality_score(system_activities=system_activities)
        # 更新数据库中的评分（如果有变化）
        if worklog.quality_score != quality_score['total'] or worklog.quality_issues != quality_score['issues']:
            worklog.quality_score = quality_score['total']
            worklog.quality_issues = quality_score['issues']
            db.session.commit()
        # 添加改进建议配置供前端使用
        quality_score['suggestions'] = WorkLog.IMPROVEMENT_SUGGESTIONS

    return {
        'log': log_data,
        'completed_items': completed_items,
        'pending_items': pending_items,
        'cancelled_items': cancelled_items,
        'statistics': stats,
        'activities': activities,
        'is_readonly': is_readonly,
        'reactions': reactions_data,
        'quality_score': quality_score
    }


def list_viewable_account_ids(user):
    """user 可查看工作日历的账户 id 集合(含本人)。

    can_view_user 权限矩阵的「集合化」版本(单一来源,逐条与 can_view_user 等价):
    供 mobile accounts 端点 / C2 ScopeSheet 列举可切换账户用。
    注意:与 can_view_user 一样,company/department 维度忠实保留原比较口径
    (department 维度不叠加 company 约束),不额外过滤 is_active(避免 User._is_active 查询陷阱)。
    """
    ids = set(get_subordinate_user_ids(user))
    ids.add(user.id)

    worklog_permission = user.get_permission_level('worklog')

    if is_admin_or_ceo(user) or worklog_permission == 'system':
        # 管理员/CEO 或 system:可查看所有人
        ids |= {row[0] for row in User.query.with_entities(User.id).all()}
    elif worklog_permission == 'company':
        # company:同公司
        ids |= {
            row[0] for row in User.query.with_entities(User.id).filter(
                User.company_name == user.company_name
            ).all()
        }
    elif worklog_permission == 'department' or user.is_department_manager:
        # department / 部门负责人:管辖部门 + 本部门(忠实 can_view_user,不叠加 company)
        managed_depts = Department.query.filter_by(manager_id=user.id).all()
        managed_dept_names = [d.name for d in managed_depts]
        if user.department and user.department not in managed_dept_names:
            managed_dept_names.append(user.department)
        if managed_dept_names:
            ids |= {
                row[0] for row in User.query.with_entities(User.id).filter(
                    User.department.in_(managed_dept_names)
                ).all()
            }

    return ids


# ===== 写侧(C3,忠实抽取 worklog.py 写路由,保留行为与副作用顺序) =====

class WorklogItemError(Exception):
    """工作项写操作错误,携带消息+HTTP码;调用方按 code 映射,消息与 web 原文一致。"""
    def __init__(self, message, code=400):
        super().__init__(message)
        self.message = message
        self.code = code


def _local_now():
    """北京时区当前时间(忠实 worklog.get_local_time)。"""
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


def _int_or_none(v):
    if v == '' or v is None:
        return None
    try:
        return int(v)
    except (ValueError, TypeError):
        return None


def can_view_item(user, work_item):
    """忠实 can_view_work_item:本人 / admin·ceo / 下属 / 被共享。"""
    if work_item.owner_id == user.id:
        return True
    if user.role in ['admin', 'ceo']:
        return True
    if work_item.owner_id in get_subordinate_user_ids(user):
        return True
    if work_item.shared_with_users and user.id in work_item.shared_with_users:
        return True
    return False


def get_item_detail(user, item_id):
    """单个工作项详情(忠实 get_item)。返回 to_dict()。"""
    work_item = WorkItem.query.get(item_id)
    if not work_item or work_item.is_deleted:
        raise WorklogItemError(_('工作项不存在'), 404)
    if not can_view_item(user, work_item):
        raise WorklogItemError(_('无权查看此工作项'), 403)
    return work_item.to_dict()


def create_item(user, data):
    """创建工作项(忠实 create_item + 共享通知)。返回 WorkItem。"""
    if not data:
        raise WorklogItemError(_('无效的请求数据'), 400)
    title = data.get('title', '').strip()
    if not title:
        raise WorklogItemError(_('标题不能为空'), 400)
    planned_date_str = data.get('planned_date')
    if not planned_date_str:
        raise WorklogItemError(_('计划日期不能为空'), 400)
    try:
        planned_date = datetime.strptime(planned_date_str, '%Y-%m-%d').date()
    except ValueError:
        raise WorklogItemError(_('日期格式无效'), 400)

    end_date = None
    end_date_str = data.get('end_date')
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            if end_date < planned_date:
                end_date = None
        except ValueError:
            end_date = None

    start_time = None
    end_time = None
    if data.get('start_time'):
        try:
            start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        except ValueError:
            pass
    if data.get('end_time'):
        try:
            end_time = datetime.strptime(data['end_time'], '%H:%M').time()
        except ValueError:
            pass

    estimated_hours = data.get('estimated_hours')
    if estimated_hours == '' or estimated_hours is None:
        estimated_hours = None
    else:
        try:
            estimated_hours = float(estimated_hours)
        except (ValueError, TypeError):
            estimated_hours = None

    shared_with_users = data.get('shared_with_users', [])
    if isinstance(shared_with_users, list):
        shared_with_users = [int(uid) for uid in shared_with_users if uid and str(uid).isdigit()]
    else:
        shared_with_users = []

    work_item = WorkItem(
        title=title,
        description=data.get('description', '').strip() or None,
        planned_date=planned_date,
        end_date=end_date,
        start_time=start_time,
        end_time=end_time,
        is_all_day=data.get('is_all_day', True),
        is_business_trip=data.get('is_business_trip', False),
        estimated_hours=estimated_hours,
        project_id=_int_or_none(data.get('project_id')),
        customer_id=_int_or_none(data.get('customer_id')),
        contact_id=_int_or_none(data.get('contact_id')),
        work_type=data.get('work_type', 'other'),
        owner_id=user.id,
        shared_with_users=shared_with_users if shared_with_users else None
    )
    db.session.add(work_item)
    db.session.commit()

    if shared_with_users:
        from app.models.message import Message
        for uid in shared_with_users:
            if uid != user.id:
                db.session.add(Message.create_workitem_shared(
                    sender_id=user.id, recipient_id=uid, work_item=work_item))
        db.session.commit()

    return work_item


def update_item(user, item_id, data):
    """更新工作项(忠实 update_item + 时间变更/取消共享/新增共享通知)。返回 WorkItem。"""
    work_item = WorkItem.query.get(item_id)
    if not work_item or work_item.is_deleted:
        raise WorklogItemError(_('工作项不存在'), 404)
    if work_item.owner_id != user.id:
        raise WorklogItemError(_('只有创建人可以修改此行程'), 403)
    if work_item.sync_source == 'dingtalk':
        raise WorklogItemError(_('钉钉日程请到钉钉 App 编辑'), 403)
    if not data:
        raise WorklogItemError(_('无效的请求数据'), 400)

    old_planned_date = work_item.planned_date
    old_shared_users = set(work_item.shared_with_users or [])

    if 'title' in data:
        work_item.title = data['title'].strip()
    if 'description' in data:
        work_item.description = data['description'].strip() or None
    if 'planned_date' in data:
        try:
            work_item.planned_date = datetime.strptime(data['planned_date'], '%Y-%m-%d').date()
        except ValueError:
            raise WorklogItemError(_('日期格式无效'), 400)
    if 'end_date' in data:
        if data['end_date']:
            try:
                end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
                if end_date >= work_item.planned_date:
                    work_item.end_date = end_date
                else:
                    work_item.end_date = None
            except ValueError:
                work_item.end_date = None
        else:
            work_item.end_date = None
    if 'start_time' in data:
        if data['start_time']:
            try:
                work_item.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
            except ValueError:
                pass
        else:
            work_item.start_time = None
    if 'end_time' in data:
        if data['end_time']:
            try:
                work_item.end_time = datetime.strptime(data['end_time'], '%H:%M').time()
            except ValueError:
                pass
        else:
            work_item.end_time = None
    if 'is_all_day' in data:
        work_item.is_all_day = data['is_all_day']
    if 'is_business_trip' in data:
        work_item.is_business_trip = data['is_business_trip']
    if 'estimated_hours' in data:
        val = data['estimated_hours']
        if val == '' or val is None:
            work_item.estimated_hours = None
        else:
            try:
                work_item.estimated_hours = float(val)
            except (ValueError, TypeError):
                work_item.estimated_hours = None
    if 'project_id' in data:
        val = data['project_id']
        if val == '' or val is None:
            work_item.project_id = None
        else:
            try:
                work_item.project_id = int(val)
            except (ValueError, TypeError):
                work_item.project_id = None
    if 'customer_id' in data:
        val = data['customer_id']
        if val == '' or val is None:
            work_item.customer_id = None
            work_item.contact_id = None  # 清空客户时也清空联系人
        else:
            try:
                work_item.customer_id = int(val)
            except (ValueError, TypeError):
                work_item.customer_id = None
    if 'contact_id' in data:
        val = data['contact_id']
        if val == '' or val is None:
            work_item.contact_id = None
        else:
            try:
                work_item.contact_id = int(val)
            except (ValueError, TypeError):
                work_item.contact_id = None
    if 'work_type' in data:
        work_item.work_type = data['work_type']

    if 'shared_with_users' in data:
        shared_with_users = data['shared_with_users']
        if isinstance(shared_with_users, list):
            shared_with_users = [int(uid) for uid in shared_with_users if uid and str(uid).isdigit()]
            work_item.shared_with_users = shared_with_users if shared_with_users else None
        else:
            work_item.shared_with_users = None

    db.session.commit()

    from app.models.message import Message
    new_shared_users = set(work_item.shared_with_users or [])

    # 1. 时间变更通知 - 通知所有共享用户(新增+原有)
    if work_item.planned_date != old_planned_date:
        for uid in (old_shared_users | new_shared_users):
            if uid != user.id:
                db.session.add(Message.create_workitem_time_changed(
                    sender_id=user.id, recipient_id=uid, work_item=work_item,
                    old_date=old_planned_date, new_date=work_item.planned_date))

    # 2. 被移除的共享用户
    for uid in (old_shared_users - new_shared_users):
        if uid != user.id:
            db.session.add(Message.create_workitem_unshared(
                sender_id=user.id, recipient_id=uid, work_item=work_item))

    # 3. 新增共享用户(时间未变更才发,时间变更已发时间变更通知)
    if work_item.planned_date == old_planned_date:
        for uid in (new_shared_users - old_shared_users):
            if uid != user.id:
                db.session.add(Message.create_workitem_shared(
                    sender_id=user.id, recipient_id=uid, work_item=work_item))

    db.session.commit()
    return work_item


def delete_item(user, item_id):
    """删除工作项(忠实 delete_item:未来作废+通知 / 过去软删)。返回 'invalidated'|'deleted'。"""
    work_item = WorkItem.query.get(item_id)
    if not work_item or work_item.is_deleted:
        raise WorklogItemError(_('工作项不存在'), 404)
    if work_item.owner_id != user.id:
        raise WorklogItemError(_('只有创建人可以删除此行程'), 403)
    if work_item.sync_source == 'dingtalk':
        raise WorklogItemError(_('钉钉日程请到钉钉 App 删除'), 403)

    from datetime import date as date_type
    today = date_type.today()

    if work_item.planned_date > today:
        # 未来行程:标记无效(中划线显示),保留记录
        work_item.is_invalidated = True
        db.session.commit()
        if work_item.shared_with_users:
            from app.models.message import Message
            for uid in work_item.shared_with_users:
                if uid != user.id:
                    db.session.add(Message.create_workitem_invalidated(
                        sender_id=user.id, recipient_id=uid, work_item=work_item))
            db.session.commit()
        return 'invalidated'
    else:
        # 当天或过去:软删除
        work_item.is_deleted = True
        db.session.commit()
        return 'deleted'


def complete_item(user, item_id, data):
    """标记完成(忠实 complete_item:状态+智能工时+worklog关联+可选Action同步+完成通知)。返回 WorkItem。"""
    work_item = WorkItem.query.get(item_id)
    if not work_item or work_item.is_deleted:
        raise WorklogItemError(_('工作项不存在'), 404)
    if work_item.owner_id != user.id:
        raise WorklogItemError(_('只有创建人可以标记此行程完成'), 403)
    if work_item.sync_source == 'dingtalk':
        raise WorklogItemError(_('钉钉日程请到钉钉 App 操作'), 403)

    data = data or {}
    work_item.status = 'completed'
    work_item.completed_at = _local_now()
    actual_hours = data.get('actual_hours')
    work_item.actual_hours = float(actual_hours) if actual_hours else work_item.estimated_hours
    work_item.execution_notes = data.get('execution_notes', '').strip() or None

    description = data.get('description', '').strip()
    if description:
        work_item.description = description

    # 关联当天日志 + 智能工时(去重/扣午休/上限8h)
    worklog = WorkLog.get_or_create(user.id, work_item.planned_date)
    work_item.worklog_id = worklog.id
    worklog.total_hours = worklog.calculate_smart_hours()

    # 同步行动记录(关联客户/项目且有内容)
    sync_action = data.get('sync_action', False)
    action_content = description or work_item.description
    if sync_action and action_content and (work_item.customer_id or work_item.project_id):
        action_date = work_item.end_date or work_item.planned_date
        db.session.add(Action(
            date=action_date,
            contact_id=work_item.contact_id,
            company_id=work_item.customer_id,
            project_id=work_item.project_id,
            communication=action_content,
            owner_id=user.id,
            is_shared=True
        ))

    db.session.commit()

    if work_item.shared_with_users:
        from app.models.message import Message
        for uid in work_item.shared_with_users:
            if uid != user.id:
                db.session.add(Message.create_workitem_completed(
                    sender_id=user.id, recipient_id=uid, work_item=work_item))
        db.session.commit()

    return work_item


def cancel_item(user, item_id, data):
    """标记取消(忠实 cancel_item:状态+取消通知)。返回 WorkItem。"""
    work_item = WorkItem.query.get(item_id)
    if not work_item or work_item.is_deleted:
        raise WorklogItemError(_('工作项不存在'), 404)
    if work_item.owner_id != user.id:
        raise WorklogItemError(_('只有创建人可以取消此行程'), 403)
    if work_item.sync_source == 'dingtalk':
        raise WorklogItemError(_('钉钉日程请到钉钉 App 取消'), 403)

    data = data or {}
    work_item.status = 'cancelled'
    work_item.execution_notes = data.get('execution_notes', '').strip() or None
    db.session.commit()

    if work_item.shared_with_users:
        from app.models.message import Message
        for uid in work_item.shared_with_users:
            if uid != user.id:
                db.session.add(Message.create_workitem_cancelled(
                    sender_id=user.id, recipient_id=uid, work_item=work_item))
        db.session.commit()

    return work_item
