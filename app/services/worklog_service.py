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

def get_viewable_items(user, start_date, end_date, owner_id=None):
    """获取日历事件列表（FullCalendar 数据源）忠实抽取 get_items

    owner_id 为空 → 自己+共享给自己的工作项
    owner_id 非空 → 校验权限矩阵后返回该用户工作项 + 日志已读/未读状态
    返回 dict: {events, datesWithItems, [datesWith{Submitted/Unread/Read}Logs]}
    """
    if owner_id:
        # 校验权限：基于 worklog 模块权限配置(用户不存在抛 WorklogUserNotFound→404)
        if not can_view_user(user, owner_id):
            raise WorklogPermissionDenied()

        # 查询指定用户的工作项
        query = WorkItem.query.filter(
            WorkItem.is_deleted == False,
            WorkItem.planned_date >= start_date,
            WorkItem.planned_date < end_date,
            WorkItem.owner_id == owner_id
        )
    else:
        # 默认：查询当前用户的工作项 + 共享给当前用户的工作项
        query = WorkItem.query.filter(
            WorkItem.is_deleted == False,
            WorkItem.planned_date >= start_date,
            WorkItem.planned_date < end_date,
            or_(
                WorkItem.owner_id == user.id,
                # 检查 shared_with_users JSON数组是否包含当前用户ID
                # 使用 text() 包装JSONB字面量确保正确转换
                cast(WorkItem.shared_with_users, JSONB).op('@>')(text(f"'[{user.id}]'::jsonb"))
            )
        )

    items = query.order_by(WorkItem.planned_date, WorkItem.start_time).all()

    # 转换为 FullCalendar 事件格式，传入当前用户ID用于判断是否是所有者
    events = [item.to_calendar_event(current_user_id=user.id) for item in items]

    # 获取有工作项的日期集合（用于前端高亮）
    dates_with_items = list(set(item.planned_date.isoformat() for item in items))

    result = {
        'events': events,
        'datesWithItems': dates_with_items
    }

    # 如果查看他人日历，额外返回日志已读/未读状态
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

            result['datesWithUnreadLogs'] = list(set(dates_with_unread_logs))
            result['datesWithReadLogs'] = list(set(dates_with_read_logs))
        else:
            result['datesWithUnreadLogs'] = []
            result['datesWithReadLogs'] = []
    else:
        # 如果查看自己的日历，返回已提交日志的日期（显示绿点）
        submitted_logs = WorkLog.query.filter(
            WorkLog.owner_id == user.id,
            WorkLog.log_date >= start_date,
            WorkLog.log_date < end_date,
            WorkLog.status == 'submitted'
        ).all()
        result['datesWithSubmittedLogs'] = list(set(
            log.log_date.isoformat() for log in submitted_logs
        ))

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
