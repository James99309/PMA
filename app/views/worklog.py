# -*- coding: utf-8 -*-
"""
工作日历与日志模块 - 视图层

提供日历页面渲染和 AJAX API 接口
"""
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from flask_babel import gettext as _

from datetime import datetime
from zoneinfo import ZoneInfo
from app import db
from app.models.worklog import WorkItem, WorkLog
from app.models.user import Affiliation
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
    created_actions = Action.query.filter(
        Action.owner_id == user_id,
        Action.date == target_date
    ).all()
    activities['actions']['created'] = [
        {
            'id': a.id,
            'name': (a.communication[:30] + '...' if len(a.communication) > 30 else a.communication) if a.communication else f'行动#{a.id}',
            'project_name': a.project.project_name if a.project else None,
            'customer_name': a.company.company_name if a.company else None
        }
        for a in created_actions
    ]
    activities['summary']['actions_created'] = len(created_actions)

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

        # 部门负责人只能查看同部门成员
        if current_user.is_department_manager and not is_admin_or_ceo():
            from app.models.user import User
            target_user = User.query.get(owner_id)
            if not target_user or target_user.department != current_user.department:
                return jsonify({'error': '只能查看同部门成员日历', 'events': [], 'datesWithItems': []}), 403

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

    return jsonify({
        'events': events,
        'datesWithItems': dates_with_items
    })


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

    return jsonify({
        'success': True,
        'message': _('更新成功'),
        'data': work_item.to_dict()
    })


@worklog.route('/api/items/<int:item_id>', methods=['DELETE'])
@login_required
def delete_item(item_id):
    """删除工作项（软删除）"""
    work_item = WorkItem.query.get(item_id)

    if not work_item or work_item.is_deleted:
        return jsonify({'success': False, 'message': _('工作项不存在')}), 404

    # 只有所有者可以删除
    if work_item.owner_id != current_user.id:
        return jsonify({'success': False, 'message': _('只有创建人可以删除此行程')}), 403

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

    # 更新日志总工时
    worklog.total_hours = sum(
        i.actual_hours or 0
        for i in worklog.work_items
        if i.status == 'completed' and not i.is_deleted
    )

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

    return jsonify({
        'success': True,
        'message': _('已取消'),
        'data': work_item.to_dict()
    })


@worklog.route('/api/daily/<log_date>', methods=['GET'])
@login_required
def get_daily_log(log_date):
    """获取日志数据"""
    try:
        target_date = datetime.strptime(log_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': _('日期格式无效')}), 400

    # 获取或创建日志
    worklog = WorkLog.get_or_create(current_user.id, target_date)
    db.session.commit()

    # 获取当天的所有工作项（包括未关联到日志的 + 共享给当前用户的）
    work_items = WorkItem.query.filter(
        WorkItem.planned_date == target_date,
        WorkItem.is_deleted == False,
        or_(
            WorkItem.owner_id == current_user.id,
            cast(WorkItem.shared_with_users, JSONB).op('@>')(text(f"'[{current_user.id}]'::jsonb"))
        )
    ).order_by(WorkItem.created_at).all()

    # 分类工作项
    completed_items = [i.to_dict() for i in work_items if i.status == 'completed']
    pending_items = [i.to_dict() for i in work_items if i.status == 'planned']
    cancelled_items = [i.to_dict() for i in work_items if i.status == 'cancelled']

    # 计算统计数据
    stats = {
        'total_items': len(work_items),
        'completed_items': len(completed_items),
        'pending_items': len(pending_items),
        'total_hours': sum(i.actual_hours or 0 for i in work_items if i.status == 'completed'),
        'project_count': len(set(i.project_id for i in work_items if i.project_id)),
        'customer_count': len(set(i.customer_id for i in work_items if i.customer_id))
    }

    # 查询当天的行动记录（创建或修改的业务数据）
    activities = get_daily_activities(current_user.id, target_date)

    return jsonify({
        'success': True,
        'data': {
            'log': worklog.to_dict(),
            'completed_items': completed_items,
            'pending_items': pending_items,
            'cancelled_items': cancelled_items,
            'statistics': stats,
            'activities': activities
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
    mentioned_projects = data.get('mentioned_projects', [])
    if isinstance(mentioned_projects, list):
        worklog.mentioned_projects = mentioned_projects if mentioned_projects else None

    # 更新状态
    worklog.status = 'submitted'
    worklog.submitted_at = get_local_time()

    # 更新总工时（包含共享给当前用户的已完成工作项）
    work_items = WorkItem.query.filter(
        WorkItem.planned_date == target_date,
        WorkItem.status == 'completed',
        WorkItem.is_deleted == False,
        or_(
            WorkItem.owner_id == current_user.id,
            cast(WorkItem.shared_with_users, JSONB).op('@>')(text(f"'[{current_user.id}]'::jsonb"))
        )
    ).all()
    worklog.total_hours = sum(i.actual_hours or 0 for i in work_items)

    db.session.commit()

    # TODO: 可以在这里发送通知给上级

    return jsonify({
        'success': True,
        'message': _('提交成功'),
        'data': worklog.to_dict()
    })


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
