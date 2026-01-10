# -*- coding: utf-8 -*-
"""
工作日历与日志模块 - 视图层

提供日历页面渲染和 AJAX API 接口
"""
import logging
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from flask_babel import gettext as _

logger = logging.getLogger(__name__)

from datetime import datetime
from zoneinfo import ZoneInfo
from app import db
from app.models.worklog import WorkItem, WorkLog
from app.models.user import User, Affiliation
from app.models.project import Project
from app.models.customer import Company, Contact
from app.models.quotation import Quotation
from app.models.pricing_order import PricingOrder
from app.models.action import Action
from app.utils.access_control import get_viewable_data
from app.utils.sharing import get_shareable_users_tree
from sqlalchemy import func, or_, cast, text
from sqlalchemy.dialects.postgresql import JSONB


def get_local_time():
    """获取本地时间（北京时区）"""
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


worklog = Blueprint('worklog', __name__, url_prefix='/worklog')


# ===== 工具函数 =====

def get_subordinate_user_ids(user):
    """获取下属用户ID列表（可查看其数据的用户）"""
    # 通过 Affiliation 表查询：viewer_id 是当前用户，owner_id 是下属
    # Affiliation 表示：viewer 可以查看 owner 的数据
    affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
    return [a.owner_id for a in affiliations]


def can_manage_work_item(user, work_item):
    """检查用户是否可以管理工作项"""
    # 自己的工作项
    if work_item.owner_id == user.id:
        return True
    # 管理员可以管理所有
    if user.role in ['admin', 'ceo']:
        return True
    return False


def can_view_work_item(user, work_item):
    """检查用户是否可以查看工作项"""
    # 自己的工作项
    if work_item.owner_id == user.id:
        return True
    # 管理员可以查看所有
    if user.role in ['admin', 'ceo']:
        return True
    # 可以查看下属的工作项
    subordinate_ids = get_subordinate_user_ids(user)
    if work_item.owner_id in subordinate_ids:
        return True
    # 共享给当前用户的工作项
    if work_item.shared_with_users and user.id in work_item.shared_with_users:
        return True
    return False


def get_leader_ids(user):
    """获取需要通知的领导ID列表（部门负责人、团队负责人、管理员）"""
    from app.models.user import User
    leader_ids = set()

    # 1. 部门负责人（同部门同公司的 is_department_manager=True）
    if user.department and user.company_name:
        dept_managers = User.query.filter(
            User.department == user.department,
            User.company_name == user.company_name,
            User.is_department_manager == True,
            User.id != user.id  # 排除自己
        ).all()
        for dm in dept_managers:
            leader_ids.add(dm.id)

    # 2. 团队负责人（通过 EmployeeSalaryConfig 和 SalesTeamConfig 表查询）
    try:
        from app.models.salary_config import EmployeeSalaryConfig, SalesTeamConfig
        from datetime import datetime
        current_year = datetime.now().year
        # 查询用户的薪资配置，获取团队ID
        employee_config = EmployeeSalaryConfig.query.filter(
            EmployeeSalaryConfig.user_id == user.id,
            EmployeeSalaryConfig.year == current_year
        ).first()
        if employee_config and employee_config.team_id:
            team = SalesTeamConfig.query.get(employee_config.team_id)
            if team and team.team_leader_id and team.team_leader_id != user.id:
                leader_ids.add(team.team_leader_id)
    except Exception:
        pass  # 薪资配置表可能不存在或查询失败，忽略

    # 3. 管理员（admin/ceo 角色）
    admins = User.query.filter(
        User.role.in_(['admin', 'ceo']),
        User.id != user.id
    ).all()
    for admin in admins:
        leader_ids.add(admin.id)

    return leader_ids


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


# ===== 页面路由 =====

@worklog.route('/calendar')
@login_required
def calendar():
    """日历主页面"""
    # 从模型获取工作类型选项（支持国际化）
    work_type_options = [(key, _(label)) for key, label in WorkItem.TYPE_LABELS.items()]
    # 工作类型映射（用于前端 JavaScript）
    work_type_labels_json = {key: _(label) for key, label in WorkItem.TYPE_LABELS.items()}

    # 工作类型分组数据（用于组合输入框组件）
    work_type_groups = [
        {'key': 'common', 'label': _('通用'), 'options': [
            {'value': 'meeting', 'label': _('会议')},
            {'value': 'internal_training', 'label': _('内部培训')},
            {'value': 'other', 'label': _('其他')}
        ]},
        {'key': 'sales', 'label': _('行销'), 'options': [
            {'value': 'customer_visit', 'label': _('拜访客户')},
            {'value': 'presales_support', 'label': _('售前支持')},
            {'value': 'business_negotiation', 'label': _('商务洽谈')},
            {'value': 'customer_maintenance', 'label': _('客户维护')}
        ]},
        {'key': 'marketing', 'label': _('市场'), 'options': [
            {'value': 'market_planning', 'label': _('市场策划')},
            {'value': 'brand_promotion', 'label': _('品牌推广')},
            {'value': 'event_execution', 'label': _('活动执行')}
        ]},
        {'key': 'service', 'label': _('服务'), 'options': [
            {'value': 'onsite_maintenance', 'label': _('现场运维')},
            {'value': 'service_response', 'label': _('服务响应')},
            {'value': 'technical_support', 'label': _('技术支持')},
            {'value': 'troubleshooting', 'label': _('故障处理')}
        ]},
        {'key': 'admin', 'label': _('行政'), 'options': [
            {'value': 'admin_affairs', 'label': _('行政事务')},
            {'value': 'office_management', 'label': _('办公管理')},
            {'value': 'asset_management', 'label': _('资产管理')}
        ]},
        {'key': 'hr', 'label': _('人事'), 'options': [
            {'value': 'hr_affairs', 'label': _('人事事务')},
            {'value': 'recruitment', 'label': _('招聘面试')},
            {'value': 'employee_relations', 'label': _('员工关系')},
            {'value': 'performance_management', 'label': _('绩效管理')}
        ]},
        {'key': 'finance', 'label': _('财务'), 'options': [
            {'value': 'finance_work', 'label': _('财务工作')},
            {'value': 'expense_review', 'label': _('报销审核')},
            {'value': 'accounting', 'label': _('账务处理')}
        ]},
        {'key': 'product', 'label': _('产品'), 'options': [
            {'value': 'product_research', 'label': _('产品调研')},
            {'value': 'requirement_analysis', 'label': _('需求分析')},
            {'value': 'product_planning', 'label': _('产品规划')}
        ]},
        {'key': 'supply_chain', 'label': _('供应链'), 'options': [
            {'value': 'procurement', 'label': _('采购管理')},
            {'value': 'inventory_management', 'label': _('库存管理')},
            {'value': 'logistics', 'label': _('物流协调')},
            {'value': 'quality_tracking', 'label': _('品质跟踪')}
        ]}
    ]

    # 检查是否有下属（用于显示团队日志按钮）
    # 有下属的用户可以查看团队日志
    subordinate_ids = get_subordinate_user_ids(current_user)
    has_manage_permission = len(subordinate_ids) > 0 or current_user.role in ['admin', 'ceo']

    # 获取用户可访问的项目列表（限制数量避免过大）
    projects_query = get_viewable_data(Project, current_user, [Project.is_active == True])
    projects = projects_query.order_by(Project.project_name).limit(100).all()

    # 获取用户可访问的客户列表（限制数量避免过大）
    customers_query = get_viewable_data(Company, current_user, [Company.is_deleted == False])
    customers = customers_query.order_by(Company.company_name).limit(100).all()

    # 获取可共享用户树（用于用户选择器组件）
    shareable_users_tree = get_shareable_users_tree(current_user)

    return render_template(
        'worklog/tw_calendar.html',
        work_type_options=work_type_options,
        work_type_labels_json=work_type_labels_json,
        work_type_groups=work_type_groups,
        has_manage_permission=has_manage_permission,
        projects=projects,
        customers=customers,
        shareable_users_tree=shareable_users_tree
    )


# ===== AJAX API =====

@worklog.route('/api/customers/<int:customer_id>/contacts', methods=['GET'])
@login_required
def get_customer_contacts(customer_id):
    """获取客户下的联系人列表（权限过滤）"""
    from app.utils.access_control import can_view_contact

    # 验证客户存在
    customer = Company.query.get(customer_id)
    if not customer or customer.is_deleted:
        return jsonify({'success': False, 'message': _('客户不存在')}), 404

    # 获取该客户下的联系人（权限过滤）
    contacts = Contact.query.filter_by(company_id=customer_id).all()
    viewable_contacts = [c for c in contacts if can_view_contact(current_user, c)]

    return jsonify({
        'success': True,
        'data': [
            {'id': c.id, 'name': c.name, 'position': c.position, 'department': c.department}
            for c in viewable_contacts
        ]
    })


@worklog.route('/api/items', methods=['GET'])
@login_required
def get_items():
    """获取日历事件列表（FullCalendar 数据源）"""
    # 获取日期范围参数（FullCalendar 会传递 start 和 end）
    start_str = request.args.get('start')
    end_str = request.args.get('end')

    # 解析日期
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

    # 获取可选的 owner_id 参数（用于查看他人日历）
    owner_id = request.args.get('owner_id', type=int)

    if owner_id:
        # 检查权限：管理员/CEO 或 部门负责人可以查看他人日历
        from app.permissions import is_admin_or_ceo
        can_view_others = is_admin_or_ceo() or current_user.is_department_manager

        if not can_view_others:
            return jsonify({'error': '无权查看他人日历', 'events': [], 'datesWithItems': []}), 403

        # 部门负责人只能查看管理部门的成员
        if current_user.is_department_manager and not is_admin_or_ceo():
            from app.models.user import User
            from app.models.expense import Department
            target_user = User.query.get(owner_id)

            # 获取用户管理的所有部门名称
            managed_depts = Department.query.filter_by(manager_id=current_user.id).all()
            managed_dept_names = [d.name for d in managed_depts]
            if current_user.department and current_user.department not in managed_dept_names:
                managed_dept_names.append(current_user.department)

            if not target_user or target_user.department not in managed_dept_names:
                return jsonify({'error': '只能查看管理部门成员日历', 'events': [], 'datesWithItems': []}), 403

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
                WorkItem.owner_id == current_user.id,
                # 检查 shared_with_users JSON数组是否包含当前用户ID
                # 使用 text() 包装JSONB字面量确保正确转换
                cast(WorkItem.shared_with_users, JSONB).op('@>')(text(f"'[{current_user.id}]'::jsonb"))
            )
        )

    items = query.order_by(WorkItem.planned_date, WorkItem.start_time).all()

    # 转换为 FullCalendar 事件格式，传入当前用户ID用于判断是否是所有者
    events = [item.to_calendar_event(current_user_id=current_user.id) for item in items]

    # 获取有工作项的日期集合（用于前端高亮）
    dates_with_items = list(set(item.planned_date.isoformat() for item in items))

    result = {
        'events': events,
        'datesWithItems': dates_with_items
    }

    # 如果查看他人日历，额外返回日志已读/未读状态
    if owner_id:
        from app.models.worklog_read import WorklogRead

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
            read_log_ids = WorklogRead.get_read_worklog_ids(current_user.id, log_ids)

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
            WorkLog.owner_id == current_user.id,
            WorkLog.log_date >= start_date,
            WorkLog.log_date < end_date,
            WorkLog.status == 'submitted'
        ).all()
        result['datesWithSubmittedLogs'] = list(set(
            log.log_date.isoformat() for log in submitted_logs
        ))

    return jsonify(result)


@worklog.route('/api/items', methods=['POST'])
@login_required
def create_item():
    """创建工作项"""
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'message': _('无效的请求数据')}), 400

    # 验证必填字段
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'success': False, 'message': _('标题不能为空')}), 400

    planned_date_str = data.get('planned_date')
    if not planned_date_str:
        return jsonify({'success': False, 'message': _('计划日期不能为空')}), 400

    try:
        planned_date = datetime.strptime(planned_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': _('日期格式无效')}), 400

    # 解析结束日期（可选）
    end_date = None
    end_date_str = data.get('end_date')
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            # 确保结束日期不早于开始日期
            if end_date < planned_date:
                end_date = None
        except ValueError:
            end_date = None

    # 解析时间（可选）
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

    # 处理可选字段（空字符串转为 None）
    estimated_hours = data.get('estimated_hours')
    if estimated_hours == '' or estimated_hours is None:
        estimated_hours = None
    else:
        try:
            estimated_hours = float(estimated_hours)
        except (ValueError, TypeError):
            estimated_hours = None

    project_id = data.get('project_id')
    if project_id == '' or project_id is None:
        project_id = None
    else:
        try:
            project_id = int(project_id)
        except (ValueError, TypeError):
            project_id = None

    customer_id = data.get('customer_id')
    if customer_id == '' or customer_id is None:
        customer_id = None
    else:
        try:
            customer_id = int(customer_id)
        except (ValueError, TypeError):
            customer_id = None

    contact_id = data.get('contact_id')
    if contact_id == '' or contact_id is None:
        contact_id = None
    else:
        try:
            contact_id = int(contact_id)
        except (ValueError, TypeError):
            contact_id = None

    # 处理共享用户
    shared_with_users = data.get('shared_with_users', [])
    if isinstance(shared_with_users, list):
        # 过滤无效值，确保都是整数
        shared_with_users = [int(uid) for uid in shared_with_users if uid and str(uid).isdigit()]
    else:
        shared_with_users = []

    # 创建工作项
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
        project_id=project_id,
        customer_id=customer_id,
        contact_id=contact_id,
        work_type=data.get('work_type', 'other'),
        owner_id=current_user.id,
        shared_with_users=shared_with_users if shared_with_users else None
    )

    db.session.add(work_item)
    db.session.commit()

    # 发送共享通知给被共享的用户
    if shared_with_users:
        from app.models.message import Message
        for user_id in shared_with_users:
            if user_id != current_user.id:  # 不通知自己
                msg = Message.create_workitem_shared(
                    sender_id=current_user.id,
                    recipient_id=user_id,
                    work_item=work_item
                )
                db.session.add(msg)
        db.session.commit()

    return jsonify({
        'success': True,
        'message': _('创建成功'),
        'data': work_item.to_dict()
    })


@worklog.route('/api/items/<int:item_id>', methods=['GET'])
@login_required
def get_item(item_id):
    """获取单个工作项详情"""
    work_item = WorkItem.query.get(item_id)

    if not work_item or work_item.is_deleted:
        return jsonify({'success': False, 'message': _('工作项不存在')}), 404

    if not can_view_work_item(current_user, work_item):
        return jsonify({'success': False, 'message': _('无权查看此工作项')}), 403

    return jsonify({
        'success': True,
        'data': work_item.to_dict()
    })


@worklog.route('/api/items/<int:item_id>', methods=['PUT'])
@login_required
def update_item(item_id):
    """更新工作项"""
    work_item = WorkItem.query.get(item_id)

    if not work_item or work_item.is_deleted:
        return jsonify({'success': False, 'message': _('工作项不存在')}), 404

    # 只有所有者可以编辑（共享用户不能编辑）
    if work_item.owner_id != current_user.id:
        return jsonify({'success': False, 'message': _('只有创建人可以修改此行程')}), 403

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': _('无效的请求数据')}), 400

    # 记录更新前的值，用于发送通知
    old_planned_date = work_item.planned_date
    old_shared_users = set(work_item.shared_with_users or [])

    # 更新字段
    if 'title' in data:
        work_item.title = data['title'].strip()
    if 'description' in data:
        work_item.description = data['description'].strip() or None
    if 'planned_date' in data:
        try:
            work_item.planned_date = datetime.strptime(data['planned_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': _('日期格式无效')}), 400
    if 'end_date' in data:
        if data['end_date']:
            try:
                end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
                # 确保结束日期不早于开始日期
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

    # 处理共享用户
    if 'shared_with_users' in data:
        shared_with_users = data['shared_with_users']
        if isinstance(shared_with_users, list):
            # 过滤无效值，确保都是整数
            shared_with_users = [int(uid) for uid in shared_with_users if uid and str(uid).isdigit()]
            work_item.shared_with_users = shared_with_users if shared_with_users else None
        else:
            work_item.shared_with_users = None

    db.session.commit()

    # 发送通知
    from app.models.message import Message
    new_shared_users = set(work_item.shared_with_users or [])

    # 1. 时间变更通知 - 通知所有共享用户（包括新增和原有的）
    if work_item.planned_date != old_planned_date:
        all_shared_users = old_shared_users | new_shared_users
        for user_id in all_shared_users:
            if user_id != current_user.id:
                msg = Message.create_workitem_time_changed(
                    sender_id=current_user.id,
                    recipient_id=user_id,
                    work_item=work_item,
                    old_date=old_planned_date,
                    new_date=work_item.planned_date
                )
                db.session.add(msg)

    # 2. 共享用户变更通知
    # 被移除的用户
    removed_users = old_shared_users - new_shared_users
    for user_id in removed_users:
        if user_id != current_user.id:
            msg = Message.create_workitem_unshared(
                sender_id=current_user.id,
                recipient_id=user_id,
                work_item=work_item
            )
            db.session.add(msg)

    # 新增的用户（如果时间没变更，才发送共享通知；时间变更时已经发送了时间变更通知）
    if work_item.planned_date == old_planned_date:
        added_users = new_shared_users - old_shared_users
        for user_id in added_users:
            if user_id != current_user.id:
                msg = Message.create_workitem_shared(
                    sender_id=current_user.id,
                    recipient_id=user_id,
                    work_item=work_item
                )
                db.session.add(msg)

    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('更新成功'),
        'data': work_item.to_dict()
    })


@worklog.route('/api/items/<int:item_id>', methods=['DELETE'])
@login_required
def delete_item(item_id):
    """删除工作项（软删除或作废）"""
    work_item = WorkItem.query.get(item_id)

    if not work_item or work_item.is_deleted:
        return jsonify({'success': False, 'message': _('工作项不存在')}), 404

    # 只有所有者可以删除
    if work_item.owner_id != current_user.id:
        return jsonify({'success': False, 'message': _('只有创建人可以删除此行程')}), 403

    from datetime import date as date_type
    today = date_type.today()

    if work_item.planned_date > today:
        # 未来行程：标记为无效（中划线显示），保留记录
        work_item.is_invalidated = True
        db.session.commit()

        # 通知共享用户
        if work_item.shared_with_users:
            from app.models.message import Message
            for user_id in work_item.shared_with_users:
                if user_id != current_user.id:
                    msg = Message.create_workitem_invalidated(
                        sender_id=current_user.id,
                        recipient_id=user_id,
                        work_item=work_item
                    )
                    db.session.add(msg)
            db.session.commit()

        return jsonify({
            'success': True,
            'message': _('已作废')
        })
    else:
        # 当天或过去的行程：软删除
        work_item.is_deleted = True
        db.session.commit()

        return jsonify({
            'success': True,
            'message': _('删除成功')
        })


@worklog.route('/api/items/<int:item_id>/complete', methods=['POST'])
@login_required
def complete_item(item_id):
    """标记工作项完成"""
    work_item = WorkItem.query.get(item_id)

    if not work_item or work_item.is_deleted:
        return jsonify({'success': False, 'message': _('工作项不存在')}), 404

    # 只有所有者可以标记完成
    if work_item.owner_id != current_user.id:
        return jsonify({'success': False, 'message': _('只有创建人可以标记此行程完成')}), 403

    data = request.get_json() or {}

    work_item.status = 'completed'
    work_item.completed_at = get_local_time()
    actual_hours = data.get('actual_hours')
    work_item.actual_hours = float(actual_hours) if actual_hours else work_item.estimated_hours
    work_item.execution_notes = data.get('execution_notes', '').strip() or None

    # 更新行动记录内容（如果传入）
    description = data.get('description', '').strip()
    if description:
        work_item.description = description

    # 关联到当天的日志
    worklog = WorkLog.get_or_create(current_user.id, work_item.planned_date)
    work_item.worklog_id = worklog.id

    # 更新日志总工时（使用智能计算：去重、扣除午休、上限8小时）
    worklog.total_hours = worklog.calculate_smart_hours()

    # 如果关联了客户或项目，且有行动记录内容，则同步创建 Action 记录
    sync_action = data.get('sync_action', False)
    action_content = description or work_item.description
    if sync_action and action_content and (work_item.customer_id or work_item.project_id):
        # 获取结束日期（跨天任务用 end_date，否则用 planned_date）
        action_date = work_item.end_date or work_item.planned_date

        action = Action(
            date=action_date,
            contact_id=work_item.contact_id,  # 可选，可以为空
            company_id=work_item.customer_id,
            project_id=work_item.project_id,
            communication=action_content,
            owner_id=current_user.id,
            is_shared=True
        )
        db.session.add(action)

    db.session.commit()

    # 发送完成通知给被共享的用户
    if work_item.shared_with_users:
        from app.models.message import Message
        for user_id in work_item.shared_with_users:
            if user_id != current_user.id:  # 不通知自己
                msg = Message.create_workitem_completed(
                    sender_id=current_user.id,
                    recipient_id=user_id,
                    work_item=work_item
                )
                db.session.add(msg)
        db.session.commit()

    return jsonify({
        'success': True,
        'message': _('标记完成'),
        'data': work_item.to_dict()
    })


@worklog.route('/api/items/<int:item_id>/cancel', methods=['POST'])
@login_required
def cancel_item(item_id):
    """标记工作项取消"""
    work_item = WorkItem.query.get(item_id)

    if not work_item or work_item.is_deleted:
        return jsonify({'success': False, 'message': _('工作项不存在')}), 404

    # 只有所有者可以取消
    if work_item.owner_id != current_user.id:
        return jsonify({'success': False, 'message': _('只有创建人可以取消此行程')}), 403

    data = request.get_json() or {}

    work_item.status = 'cancelled'
    work_item.execution_notes = data.get('execution_notes', '').strip() or None

    db.session.commit()

    # 发送取消通知给被共享的用户
    if work_item.shared_with_users:
        from app.models.message import Message
        for user_id in work_item.shared_with_users:
            if user_id != current_user.id:  # 不通知自己
                msg = Message.create_workitem_cancelled(
                    sender_id=current_user.id,
                    recipient_id=user_id,
                    work_item=work_item
                )
                db.session.add(msg)
        db.session.commit()

    return jsonify({
        'success': True,
        'message': _('已取消'),
        'data': work_item.to_dict()
    })


@worklog.route('/api/daily/<log_date>', methods=['GET'])
@login_required
def get_daily_log(log_date):
    """获取日志数据

    支持查看他人日志：传入 owner_id 参数时，返回该用户的日志（只读模式）
    """
    try:
        target_date = datetime.strptime(log_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': _('日期格式无效')}), 400

    # 检查是否查看他人日志
    owner_id = request.args.get('owner_id', type=int)
    is_readonly = False

    if owner_id and owner_id != current_user.id:
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
            return jsonify({
                'success': True,
                'data': {
                    'log': None,
                    'completed_items': [],
                    'pending_items': [],
                    'cancelled_items': [],
                    'statistics': {},
                    'activities': {},
                    'is_readonly': True,
                    'no_log': True
                }
            })
    else:
        # 查看自己的日志 - 可编辑
        target_user_id = current_user.id
        worklog = WorkLog.get_or_create(current_user.id, target_date)
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

    return jsonify({
        'success': True,
        'data': {
            'log': log_data,
            'completed_items': completed_items,
            'pending_items': pending_items,
            'cancelled_items': cancelled_items,
            'statistics': stats,
            'activities': activities,
            'is_readonly': is_readonly
        }
    })


@worklog.route('/api/daily/<log_date>', methods=['PUT'])
@login_required
def update_daily_log(log_date):
    """更新日志补充内容"""
    try:
        target_date = datetime.strptime(log_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': _('日期格式无效')}), 400

    data = request.get_json() or {}

    worklog = WorkLog.get_or_create(current_user.id, target_date)
    worklog.additional_notes = data.get('additional_notes', '').strip() or None

    # 保存 @ 用户和 # 项目引用数据
    mentioned_users = data.get('mentioned_users', [])
    if isinstance(mentioned_users, list):
        worklog.mentioned_users = mentioned_users if mentioned_users else None
    mentioned_projects = data.get('mentioned_projects', [])
    if isinstance(mentioned_projects, list):
        worklog.mentioned_projects = mentioned_projects if mentioned_projects else None

    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('更新成功'),
        'data': worklog.to_dict()
    })


@worklog.route('/api/daily/<log_date>/mark-read', methods=['POST'])
@login_required
def mark_log_read(log_date):
    """标记日志为已读（查看他人日志时调用）"""
    try:
        target_date = datetime.strptime(log_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': _('日期格式无效')}), 400

    # 获取要标记的日志所有者ID
    owner_id = request.args.get('owner_id', type=int)
    if not owner_id:
        return jsonify({'success': False, 'message': '缺少 owner_id 参数'}), 400

    # 不能标记自己的日志为已读
    if owner_id == current_user.id:
        return jsonify({'success': True, 'message': '无需标记自己的日志'})

    # 查找日志
    worklog = WorkLog.query.filter_by(
        owner_id=owner_id,
        log_date=target_date
    ).first()

    if not worklog:
        return jsonify({'success': False, 'message': '日志不存在'}), 404

    # 标记为已读
    from app.models.worklog_read import WorklogRead
    WorklogRead.mark_as_read(worklog.id, current_user.id)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '已标记为已读'
    })


@worklog.route('/api/daily/<log_date>/submit', methods=['POST'])
@login_required
def submit_daily_log(log_date):
    """提交日志"""
    try:
        target_date = datetime.strptime(log_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': _('日期格式无效')}), 400

    worklog = WorkLog.get_or_create(current_user.id, target_date)

    if worklog.status == 'submitted':
        return jsonify({'success': False, 'message': _('日志已提交')}), 400

    # 保存日志内容
    data = request.get_json() or {}
    if 'additional_notes' in data:
        worklog.additional_notes = data.get('additional_notes', '').strip() or None

    # 保存 @ 用户和 # 项目引用数据
    mentioned_users = data.get('mentioned_users', [])
    if isinstance(mentioned_users, list):
        worklog.mentioned_users = mentioned_users if mentioned_users else None

        # 创建@消息通知
        if mentioned_users:
            from app.models.message import Message
            for user_id in mentioned_users:
                if user_id != current_user.id:  # 不给自己发消息
                    msg = Message.create_worklog_mention(
                        sender_id=current_user.id,
                        recipient_id=user_id,
                        worklog=worklog
                    )
                    db.session.add(msg)

    mentioned_projects = data.get('mentioned_projects', [])
    if isinstance(mentioned_projects, list):
        worklog.mentioned_projects = mentioned_projects if mentioned_projects else None

    # 更新状态
    worklog.status = 'submitted'
    worklog.submitted_at = get_local_time()

    # 更新总工时（使用智能计算，包含共享给当前用户的工作项）
    # 查询共享给当前用户但不属于当前用户的工作项
    shared_items = WorkItem.query.filter(
        WorkItem.planned_date == target_date,
        WorkItem.status == 'completed',
        WorkItem.is_deleted == False,
        WorkItem.owner_id != current_user.id,  # 排除自己的（已在 worklog.work_items 中）
        cast(WorkItem.shared_with_users, JSONB).op('@>')(text(f"'[{current_user.id}]'::jsonb"))
    ).all()
    worklog.total_hours = worklog.calculate_smart_hours(extra_items=shared_items)

    db.session.commit()

    # 发送日志提交通知给领导
    leader_ids = get_leader_ids(current_user)
    if leader_ids:
        from app.models.message import Message
        for leader_id in leader_ids:
            msg = Message.create_worklog_submitted(
                sender_id=current_user.id,
                recipient_id=leader_id,
                worklog=worklog
            )
            db.session.add(msg)
        db.session.commit()

    return jsonify({
        'success': True,
        'message': _('提交成功'),
        'data': worklog.to_dict()
    })


@worklog.route('/api/daily/<log_date>/delete', methods=['DELETE', 'POST'])
@login_required
def delete_daily_log(log_date):
    """删除日志（创建者或管理员可删除）"""
    try:
        target_date = datetime.strptime(log_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': _('日期格式无效')}), 400

    # 获取要删除日志的用户ID（管理员可能删除他人日志）
    data = request.get_json() or {}
    target_user_id = data.get('user_id', current_user.id)

    worklog = WorkLog.query.filter_by(
        owner_id=target_user_id,
        log_date=target_date,
        log_type='daily'
    ).first()

    if not worklog:
        return jsonify({'success': False, 'message': _('日志不存在')}), 404

    # 权限检查：只有创建者或管理员可以删除
    is_owner = worklog.owner_id == current_user.id
    is_admin = current_user.role in ['admin', 'ceo']

    if not is_owner and not is_admin:
        return jsonify({'success': False, 'message': _('无权删除此日志')}), 403

    try:
        # 先删除云端附件文件
        attachments = worklog.attachments_list
        if attachments:
            from app.utils.supabase_client import get_supabase_client
            supabase_client = get_supabase_client()
            for att in attachments:
                file_url = att.get('url')
                if file_url:
                    try:
                        supabase_client.delete_file_by_url(file_url, bucket_type='invoice')
                        logger.info(f"已删除附件: {att.get('filename')}")
                    except Exception as e:
                        logger.warning(f"删除附件失败: {att.get('filename')} - {e}")

        # 删除关联的阅读记录
        from sqlalchemy import text
        db.session.execute(
            text('DELETE FROM worklog_reads WHERE worklog_id = :wid'),
            {'wid': worklog.id}
        )

        # 删除日志
        db.session.delete(worklog)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': _('日志已删除')
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"删除日志失败: {e}")
        return jsonify({'success': False, 'message': f'{_("删除失败")}: {str(e)}'}), 500


# ============================================================
# 日志附件上传相关 API
# ============================================================

@worklog.route('/api/daily/<log_date>/upload-attachment', methods=['POST'])
@login_required
def upload_worklog_attachment(log_date):
    """上传日志附件（图片或PDF）"""
    from app.utils.supabase_client import get_supabase_client
    from werkzeug.utils import secure_filename
    import uuid

    # 解析日期
    try:
        target_date = datetime.strptime(log_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': _('日期格式无效')}), 400

    # 获取或创建日志
    worklog = WorkLog.query.filter_by(
        owner_id=current_user.id,
        log_date=target_date,
        log_type='daily'
    ).first()

    if not worklog:
        # 创建新日志
        worklog = WorkLog(
            owner_id=current_user.id,
            log_date=target_date,
            log_type='daily'
        )
        db.session.add(worklog)
        db.session.flush()

    # 权限检查：只有创建者可以上传附件
    if worklog.owner_id != current_user.id:
        return jsonify({'success': False, 'message': _('无权操作此日志')}), 403

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': _('未选择文件')})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': _('未选择文件')})

    # 验证文件类型
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'heic', 'heif', 'pdf'}
    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        return jsonify({'success': False, 'message': _('不支持的文件格式，支持：PNG、JPG、GIF、WEBP、HEIC、PDF')})

    try:
        # 获取文件大小
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)

        # 检查文件大小（5MB 限制）
        if file_size > 5 * 1024 * 1024:
            return jsonify({'success': False, 'message': _('文件大小超过5MB限制')})

        # 保留原始文件名（支持中文）
        original_filename = file.filename
        ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'bin'

        # 检查是否有同名文件，如果有则添加递增后缀
        existing_names = [att.get('filename') for att in worklog.attachments_list]
        if original_filename in existing_names:
            base = original_filename.rsplit('.', 1)[0] if '.' in original_filename else original_filename
            counter = 1
            while f"{base}-{counter}.{ext}" in existing_names:
                counter += 1
            original_filename = f"{base}-{counter}.{ext}"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        new_filename = f"worklog_{log_date}_{timestamp}_{unique_id}.{ext}"

        # 确定文件类型
        file_type = 'pdf' if ext == 'pdf' else 'image'

        # 上传到 Supabase
        supabase_client = get_supabase_client()

        # 重置文件指针（之前已读取过）
        file.seek(0)

        result = supabase_client.upload_file(
            object_id=worklog.id,
            file=file,
            filename=original_filename,
            file_type='attachment',  # 使用简洁格式
            bucket_type='invoice',  # 复用 invoice-images 桶
            business_type='worklog'  # 工作日志类型
        )

        logger.info(f"upload_file 返回结果: {result}")

        if result and result.get('url'):
            # 保存到数据库
            worklog.add_attachment(
                filename=original_filename,
                url=result.get('url'),
                size=file_size,
                file_type=file_type
            )
            db.session.commit()

            return jsonify({
                'success': True,
                'message': _('上传成功'),
                'data': {
                    'filename': original_filename,
                    'url': result.get('url'),
                    'size': file_size,
                    'type': file_type,
                    'index': len(worklog.attachments_list) - 1
                }
            })
        else:
            return jsonify({'success': False, 'message': _('上传失败')})

    except Exception as e:
        logger.error(f"上传日志附件失败: {e}")
        return jsonify({'success': False, 'message': f'{_("上传失败")}: {str(e)}'}), 500


@worklog.route('/api/daily/<log_date>/delete-attachment/<int:index>', methods=['DELETE', 'POST'])
@login_required
def delete_worklog_attachment(log_date, index):
    """删除日志附件"""
    # 解析日期
    try:
        target_date = datetime.strptime(log_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': _('日期格式无效')}), 400

    worklog = WorkLog.query.filter_by(
        owner_id=current_user.id,
        log_date=target_date,
        log_type='daily'
    ).first()

    if not worklog:
        return jsonify({'success': False, 'message': _('日志不存在')}), 404

    # 权限检查
    if worklog.owner_id != current_user.id:
        return jsonify({'success': False, 'message': _('无权操作此日志')}), 403

    # 获取附件信息
    attachment = worklog.get_attachment(index)
    if not attachment:
        return jsonify({'success': False, 'message': _('附件不存在')}), 404

    # 从数据库移除
    if worklog.remove_attachment(index):
        db.session.commit()
        return jsonify({'success': True, 'message': _('删除成功')})
    else:
        return jsonify({'success': False, 'message': _('删除失败')}), 500


@worklog.route('/api/daily/<log_date>/preview-attachment/<int:index>')
@login_required
def preview_worklog_attachment(log_date, index):
    """预览/下载日志附件"""
    import requests
    from flask import Response

    # 解析日期
    try:
        target_date = datetime.strptime(log_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': _('日期格式无效')}), 400

    worklog = WorkLog.query.filter_by(
        owner_id=current_user.id,
        log_date=target_date,
        log_type='daily'
    ).first()

    if not worklog:
        return jsonify({'success': False, 'message': _('日志不存在')}), 404

    attachment = worklog.get_attachment(index)
    if not attachment:
        return jsonify({'success': False, 'message': _('附件不存在')}), 404

    url = attachment.get('url')
    filename = attachment.get('filename', 'attachment')
    file_type = attachment.get('type', 'image')

    # 判断是否强制下载
    force_download = request.args.get('download') == '1'

    try:
        # 云端文件，代理下载
        if url and (url.startswith('http://') or url.startswith('https://')):
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                # 确定 MIME 类型
                if file_type == 'pdf':
                    mime_type = 'application/pdf'
                else:
                    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'bin'
                    mime_map = {
                        'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
                        'png': 'image/png', 'gif': 'image/gif',
                        'webp': 'image/webp', 'heic': 'image/heic'
                    }
                    mime_type = mime_map.get(ext, 'application/octet-stream')

                # 对文件名进行 RFC 5987 编码以支持中文
                from urllib.parse import quote
                encoded_filename = quote(filename, safe='')
                disposition_type = 'attachment' if force_download else 'inline'

                headers = {'Content-Type': mime_type}
                # 使用 filename* 参数支持 UTF-8 编码的文件名
                headers['Content-Disposition'] = f"{disposition_type}; filename*=UTF-8''{encoded_filename}"

                return Response(resp.content, headers=headers)
            else:
                return jsonify({'success': False, 'message': _('文件获取失败')}), 404
        else:
            return jsonify({'success': False, 'message': _('无效的文件URL')}), 400

    except Exception as e:
        logger.error(f"预览日志附件失败: {e}")
        return jsonify({'success': False, 'message': f'{_("预览失败")}: {str(e)}'}), 500


@worklog.route('/api/team/logs', methods=['GET'])
@login_required
def get_team_logs():
    """获取下属日志列表"""
    # 检查是否有下属或管理员权限
    subordinate_ids = get_subordinate_user_ids(current_user)
    if not subordinate_ids and current_user.role not in ['admin', 'ceo']:
        return jsonify({'success': False, 'message': _('无权查看团队日志')}), 403

    # 获取日期范围
    start_str = request.args.get('start')
    end_str = request.args.get('end')

    try:
        if start_str:
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        else:
            start_date = date.today() - timedelta(days=7)

        if end_str:
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
        else:
            end_date = date.today()
    except ValueError:
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()

    # subordinate_ids 已在权限检查时获取
    if not subordinate_ids:
        return jsonify({
            'success': True,
            'data': []
        })

    # 查询下属日志
    logs = WorkLog.query.filter(
        WorkLog.owner_id.in_(subordinate_ids),
        WorkLog.log_date >= start_date,
        WorkLog.log_date <= end_date
    ).order_by(WorkLog.log_date.desc(), WorkLog.owner_id).all()

    return jsonify({
        'success': True,
        'data': [log.to_dict() for log in logs]
    })


@worklog.route('/api/today-status', methods=['GET'])
@login_required
def get_today_status():
    """获取今天的待办状态（用于日历图标提示）"""
    today = date.today()

    # 检查今天是否有未完成的工作项（状态为 planned 表示未完成）
    # 条件：今天的单日行程 或 跨天行程包含今天
    pending_items = WorkItem.query.filter(
        WorkItem.owner_id == current_user.id,
        WorkItem.is_deleted == False,
        WorkItem.status == 'planned',
        db.or_(
            # 单日行程：planned_date 是今天
            db.and_(
                WorkItem.planned_date == today,
                db.or_(WorkItem.end_date.is_(None), WorkItem.end_date == today)
            ),
            # 跨天行程：今天在 planned_date 和 end_date 之间
            db.and_(
                WorkItem.planned_date <= today,
                WorkItem.end_date >= today
            )
        )
    ).count()

    # 检查今天的日志是否已提交
    today_log = WorkLog.query.filter_by(
        owner_id=current_user.id,
        log_date=today,
        log_type='daily'
    ).first()

    log_not_submitted = today_log is None or today_log.status != 'submitted'

    # 有待办事项的条件：有未完成的工作项 或 日志未提交
    has_pending = pending_items > 0 or log_not_submitted

    return jsonify({
        'success': True,
        'has_pending': has_pending,
        'pending_items': pending_items,
        'log_submitted': not log_not_submitted
    })


# ===== 日志评论 API =====

def can_view_worklog(user, worklog):
    """检查用户是否可以查看日志"""
    # 自己的日志
    if worklog.owner_id == user.id:
        return True

    # 管理员/CEO 可以查看所有
    if user.role in ['admin', 'ceo']:
        return True

    # 被@提及的用户可以查看
    # 注意：mentioned_users 存储的是字符串ID，需要同时检查整数和字符串
    if worklog.mentioned_users:
        if user.id in worklog.mentioned_users or str(user.id) in worklog.mentioned_users:
            return True

    # 部门负责人可以查看本部门成员日志
    if user.is_department_manager:
        log_owner = User.query.get(worklog.owner_id)
        if log_owner and log_owner.department == user.department and log_owner.company_name == user.company_name:
            return True

    # 可以查看下属的日志
    subordinate_ids = get_subordinate_user_ids(user)
    if worklog.owner_id in subordinate_ids:
        return True

    # 收到过该日志相关消息的用户可以查看（如日志提交通知）
    # 通过 sender_id（日志作者）和 log_date（存储在 extra_data 中）匹配
    from app.models.message import Message
    from sqlalchemy import String
    log_date_str = worklog.log_date.isoformat() if worklog.log_date else None
    has_notification = Message.query.filter(
        Message.recipient_id == user.id,
        Message.sender_id == worklog.owner_id,
        Message.related_object_type == 'worklog',
        cast(Message.extra_data['log_date'], String) == f'"{log_date_str}"'
    ).first()
    if has_notification:
        return True

    return False


@worklog.route('/api/daily/<log_date>/comments', methods=['GET'])
@login_required
def get_worklog_comments(log_date):
    """获取日志评论列表"""
    try:
        target_date = datetime.strptime(log_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': _('日期格式无效')}), 400

    # 获取 owner_id 参数（查看他人日志时使用）
    owner_id = request.args.get('owner_id', type=int)
    target_user_id = owner_id if owner_id else current_user.id

    # 查找日志
    worklog_obj = WorkLog.query.filter_by(
        owner_id=target_user_id,
        log_date=target_date,
        log_type='daily'
    ).first()

    if not worklog_obj:
        return jsonify({'success': True, 'data': []})

    # 权限检查：只有能查看日志的人才能看评论
    if not can_view_worklog(current_user, worklog_obj):
        return jsonify({'success': False, 'message': _('无权查看此日志评论')}), 403

    # 获取评论（排除已删除的）
    # 查询该日期+该作者的所有日志的评论（包括历史日志，防止日志重建后丢失评论）
    from app.models.worklog import WorkLogComment
    all_worklogs = WorkLog.query.filter_by(
        owner_id=target_user_id,
        log_date=target_date,
        log_type='daily'
    ).all()
    all_worklog_ids = [w.id for w in all_worklogs]

    comments = WorkLogComment.query.filter(
        WorkLogComment.worklog_id.in_(all_worklog_ids),
        WorkLogComment.is_deleted == False
    ).order_by(WorkLogComment.created_at.desc()).all()

    # 转换为字典并设置 can_delete 权限
    result = []
    for comment in comments:
        data = comment.to_dict()
        data['can_delete'] = (
            current_user.id == comment.owner_id or
            current_user.role in ['admin', 'ceo']
        )
        result.append(data)

    return jsonify({
        'success': True,
        'data': result
    })


@worklog.route('/api/daily/<log_date>/comments', methods=['POST'])
@login_required
def add_worklog_comment(log_date):
    """添加日志评论"""
    try:
        target_date = datetime.strptime(log_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': _('日期格式无效')}), 400

    data = request.get_json() or {}
    content = data.get('content', '').strip()

    if not content:
        return jsonify({'success': False, 'message': _('评论内容不能为空')}), 400

    # 获取 owner_id 参数
    owner_id = data.get('owner_id') or request.args.get('owner_id', type=int)
    target_user_id = owner_id if owner_id else current_user.id

    # 查找日志（必须是已提交的日志才能评论）
    worklog_obj = WorkLog.query.filter_by(
        owner_id=target_user_id,
        log_date=target_date,
        log_type='daily',
        status='submitted'
    ).first()

    if not worklog_obj:
        return jsonify({'success': False, 'message': _('日志不存在或未提交')}), 404

    # 权限检查：只有能查看日志的人才能评论
    if not can_view_worklog(current_user, worklog_obj):
        return jsonify({'success': False, 'message': _('无权评论此日志')}), 403

    # 创建评论
    from app.models.worklog import WorkLogComment
    comment = WorkLogComment(
        worklog_id=worklog_obj.id,
        content=content,
        owner_id=current_user.id
    )
    db.session.add(comment)

    # 发送消息通知给日志作者（如果评论者不是作者本人）
    if current_user.id != worklog_obj.owner_id:
        from app.models.message import Message
        msg = Message.create_worklog_comment(
            sender_id=current_user.id,
            recipient_id=worklog_obj.owner_id,
            worklog=worklog_obj,
            comment_content=content
        )
        db.session.add(msg)

    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('评论成功'),
        'data': {
            **comment.to_dict(),
            'can_delete': True  # 刚创建的评论自己可以删除
        }
    })


@worklog.route('/api/comments/<int:comment_id>', methods=['DELETE', 'POST'])
@login_required
def delete_worklog_comment(comment_id):
    """删除日志评论"""
    from app.models.worklog import WorkLogComment
    comment = WorkLogComment.query.get(comment_id)

    if not comment or comment.is_deleted:
        return jsonify({'success': False, 'message': _('评论不存在')}), 404

    # 权限检查：评论者本人或管理员可删除
    if comment.owner_id != current_user.id and current_user.role not in ['admin', 'ceo']:
        return jsonify({'success': False, 'message': _('无权删除此评论')}), 403

    # 软删除
    comment.is_deleted = True
    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('删除成功')
    })
