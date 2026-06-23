# -*- coding: utf-8 -*-
"""
工作日历与日志模块 - 视图层

提供日历页面渲染和 AJAX API 接口
"""
import logging
import os
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from flask_babel import gettext as _

logger = logging.getLogger(__name__)

from datetime import datetime
from zoneinfo import ZoneInfo
from app import db
from app.models.worklog import WorkItem, WorkLog, WorkLogReaction
from app.models.user import User, Affiliation
from app.models.project import Project
from app.models.customer import Company, Contact
from app.models.quotation import Quotation
from app.models.pricing_order import PricingOrder
from app.models.action import Action
from app.utils.access_control import get_viewable_data
from app.utils.sharing import get_shareable_users_tree
from app.data.holidays import get_holidays_for_api, SUPPORTED_COUNTRIES
from sqlalchemy import func, or_, cast, text
from sqlalchemy.dialects.postgresql import JSONB

# C-BE1: 读侧逻辑已抽入 app/services/worklog_service.py(web/mobile 单一来源)
# 反向 import 保持向后兼容(app/views/main.py 等仍 from app.views.worklog import get_subordinate_user_ids)
from app.services.worklog_service import (  # noqa: F401
    get_subordinate_user_ids,
    manageable_user_ids,
    get_daily_activities,
    get_leader_ids,
)


def get_local_time():
    """获取本地时间（北京时区）"""
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


worklog = Blueprint('worklog', __name__, url_prefix='/worklog')


# ===== 工具函数 =====
# get_subordinate_user_ids 已迁入 app/services/worklog_service.py(文件顶部反向 import)


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
    """检查用户是否可以查看工作项(委托 service 单一来源,口径含部门/公司级)。"""
    from app.services import worklog_service
    return worklog_service.can_view_item(user, work_item)


# get_leader_ids 已迁入 app/services/worklog_service.py(文件顶部反向 import)


# get_daily_activities 已迁入 app/services/worklog_service.py(文件顶部反向 import)


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
            {'value': 'video_production', 'label': _('视频制作')},
            {'value': 'material_design', 'label': _('物料设计')},
            {'value': 'social_media_operation', 'label': _('社媒运营')},
            {'value': 'channel_activity', 'label': _('渠道活动')},
            {'value': 'brand_event', 'label': _('品牌活动')}
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

    # 团队日志按钮:有「可管理成员」(数据归属下属 + 管辖部门成员)的用户可见
    # 用 MANAGE 口径(含部门负责人),与团队日志接口一致;不再只看数据归属下属
    has_manage_permission = len(manageable_user_ids(current_user)) > 0 or current_user.role in ['admin', 'ceo']

    # 获取用户可访问的项目列表（限制数量避免过大）
    projects_query = get_viewable_data(Project, current_user, [Project.is_active == True])
    projects = projects_query.order_by(Project.project_name).limit(100).all()

    # 获取用户可访问的客户列表（限制数量避免过大）
    customers_query = get_viewable_data(Company, current_user, [Company.is_deleted == False])
    customers = customers_query.order_by(Company.company_name).limit(100).all()

    # 获取可共享用户树（用于用户选择器组件）
    shareable_users_tree = get_shareable_users_tree(current_user)

    # 检查用户是否有查看他人日志的权限（用于显示账户选择器）
    worklog_permission = current_user.get_permission_level('worklog')
    can_view_others_worklog = (
        current_user.role in ['admin', 'ceo'] or
        current_user.is_department_manager or
        worklog_permission in ['company', 'department', 'system'] or
        len(subordinate_ids) > 0  # 有数据归属下属的用户也可以查看
    )

    # 假期数据（当前年份）
    current_year = date.today().year
    holidays_data = get_holidays_for_api(current_year)

    return render_template(
        'worklog/tw_calendar.html',
        work_type_options=work_type_options,
        work_type_labels_json=work_type_labels_json,
        work_type_groups=work_type_groups,
        has_manage_permission=has_manage_permission,
        projects=projects,
        customers=customers,
        shareable_users_tree=shareable_users_tree,
        can_view_others_worklog=can_view_others_worklog,
        holidays_data=holidays_data,
        supported_countries=SUPPORTED_COUNTRIES
    )


@worklog.route('/at-calendar')
@login_required
def at_calendar():
    """AT 风格工作日历(纯手写月历网格;复用 /worklog/api/* 后端)。
    工作类型 = 通用(人人可见) + 按当前角色考核领域追加的专属组(如 HR 才显示人事类)。
    日报/团队/评论/reaction/共享 后续迭代。"""
    # 考核驱动:每个角色的「可记录活动」取自其 KPI 考核中的活动型项(非自动统计指标)。
    # 组目录(key → (组名, [(工作类型值, 标签)]))
    _CATALOG = {
        'solution': ('解决方案', [('se_quote_confirm', _('报价确认')), ('se_sales_support', _('销售支持'))]),
        'sales':    ('行销', [('customer_visit', _('拜访客户')), ('business_negotiation', _('商务洽谈')), ('customer_maintenance', _('客户维护'))]),
        'channel':  ('渠道', [('customer_visit', _('拜访客户')), ('channel_activity', _('渠道活动'))]),
        'marketing':('市场', [('video_production', _('视频制作')), ('material_design', _('物料设计')), ('social_media_operation', _('社媒运营')), ('channel_activity', _('渠道活动')), ('brand_event', _('品牌活动'))]),
        'service':  ('服务', [('onsite_maintenance', _('现场运维')), ('service_response', _('服务响应')), ('technical_support', _('技术支持')), ('troubleshooting', _('故障处理'))]),
        'product':  ('产品', [('pm_rd_task', _('研发任务')), ('pm_quality_task', _('质量处理')), ('pm_launch_support', _('上市支持'))]),
        'hr':       ('人事', [('recruitment', _('招聘面试')), ('hr_training', _('培训')), ('hr_team_build', _('团建')), ('admin_affairs', _('行政事务'))]),
        'finance':  ('财务', [('finance_work', _('财务工作')), ('expense_review', _('报销审核')), ('accounting', _('账务处理'))]),
        'supply_chain': ('供应链', [('procurement', _('采购管理')), ('inventory_management', _('库存管理')), ('logistics', _('物流协调')), ('quality_tracking', _('品质跟踪'))]),
        'admin':    ('行政', [('admin_affairs', _('行政事务')), ('office_management', _('办公管理')), ('asset_management', _('资产管理'))]),
    }
    # 角色 → 考核组(只有该角色进入才显示;按 role_kpi_schemes 的活动型考核项)
    _ROLE_GROUPS = {
        'solution_manager': ['solution'],
        'sales_manager': ['sales'], 'customer_sales': ['sales'], 'sales_director': ['sales'],
        'channel_manager': ['channel'], 'dealer': ['channel'],
        'marketing_manager': ['marketing'], 'marketingplan': ['marketing'],
        'service_manager': ['service'], 'engineer': ['service'],
        'hr_manager': ['hr'],
        'finance_supervisor': ['finance'], 'finace_director': ['finance'], 'finance': ['finance'], 'Treasurer': ['finance'],
        'product_manager': ['product'],
        'supplychain_manager': ['supply_chain'], 'Buyer': ['supply_chain'],
        'business_admin': ['admin'],
    }
    _role = current_user.role or ''
    _keys = list(_CATALOG.keys()) if _role in ('admin', 'ceo') else _ROLE_GROUPS.get(_role, [])

    work_type_groups = [{'key': 'common', 'label': _('通用'), 'options': [
        {'value': 'meeting', 'label': _('会议')},
        {'value': 'internal_training', 'label': _('内部培训')},
        {'value': 'other', 'label': _('其他')},
    ]}]
    for _k in _keys:
        if _k in _CATALOG:
            _name, _opts = _CATALOG[_k]
            work_type_groups.append({'key': _k, 'label': _(_name),
                                     'options': [{'value': v, 'label': lb} for v, lb in _opts]})

    work_type_labels_json = {key: _(label) for key, label in WorkItem.TYPE_LABELS.items()}

    # 节假日:发送全部国家数据(前后一年,便于跨年导航),前端按选中国家过滤
    _db_type = (os.environ.get('PMA_DB_TYPE') or os.environ.get('SUPABASE_DB_TYPE') or 'sp8d').lower()
    _default_countries = ['SG', 'MY'] if _db_type == 'ovs' else ['CN']
    _yr = date.today().year
    holidays_data = {}
    for _y in (_yr - 1, _yr, _yr + 1):
        for _ds, _entries in get_holidays_for_api(_y).items():
            holidays_data.setdefault(_ds, []).extend(_entries)

    # 是否显示账户选择器(可查看他人日历):本人之外还有可查看账户即显示
    from app.services import worklog_service
    _acct_ids = worklog_service.list_viewable_account_ids(current_user)
    _can_view_others = len(_acct_ids - {current_user.id}) > 0

    return render_template(
        'worklog/at_calendar.html',
        work_type_groups=work_type_groups,
        work_type_labels_json=work_type_labels_json,
        holidays_data=holidays_data,
        supported_countries=SUPPORTED_COUNTRIES,
        default_countries=_default_countries,
        can_view_others=_can_view_others,
    )


# ===== AJAX API =====

@worklog.route('/api/holidays/<int:year>', methods=['GET'])
@login_required
def get_holidays(year):
    """获取指定年份的假期数据"""
    countries = request.args.get('countries', '').split(',')
    countries = [c.strip() for c in countries if c.strip()]
    data = get_holidays_for_api(year, countries if countries else None)
    return jsonify({'success': True, 'data': data})


@worklog.route('/api/calendar-accounts', methods=['GET'])
@login_required
def get_calendar_accounts():
    """可查看工作日历的账户列表(本人 + 下属/部门/公司/全员,按权限)。
    供 AT 日历账户选择器列举可切换查看的人。"""
    from app.services import worklog_service
    ids = worklog_service.list_viewable_account_ids(current_user)
    ids.discard(current_user.id)  # 本人单独置顶
    accounts = []
    if ids:
        users = User.query.filter(User.id.in_(list(ids))).all()
        for u in users:
            accounts.append({
                'id': u.id,
                'name': u.real_name or u.username,
                'department': u.department or '',
                'active': bool(u.is_active),   # 停用(离职)账号排到最下面
            })
        # 在职优先,停用(将离职)沉底;各自按部门+姓名
        accounts.sort(key=lambda a: (not a['active'], a['department'], a['name']))
    return jsonify({'success': True, 'accounts': accounts})


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


@worklog.route('/api/my-tasks', methods=['GET'])
@login_required
def get_my_unfinished_tasks():
    """工作项「关联任务」用:未完成的(自建/负责/共享/审核)任务 + 其未完成子任务(二级)。"""
    from app.models.task import Task, TaskReviewer
    from app.models.subtask import SubTask
    _UNDONE = ['pending', 'in_progress', 'paused', 'pending_review']
    reviewer_ids = db.session.query(TaskReviewer.task_id).filter(
        TaskReviewer.reviewer_id == current_user.id).subquery()
    tasks = Task.query.filter(
        or_(Task.assignee_id == current_user.id, Task.creator_id == current_user.id,
            Task.id.in_(reviewer_ids)),
        Task.is_deleted == False, Task.status.in_(_UNDONE)
    ).order_by(Task.created_at.desc()).limit(50).all()
    out = []
    for t in tasks:
        subs = SubTask.query.filter(
            SubTask.task_id == t.id, SubTask.is_deleted == False, SubTask.status.in_(_UNDONE)
        ).order_by(SubTask.sort_order).all()
        out.append({'id': t.id, 'title': t.title,
                    'subtasks': [{'id': s.id, 'title': s.title} for s in subs]})
    return jsonify({'success': True, 'tasks': out})


@worklog.route('/api/items/<int:item_id>/comments', methods=['GET'])
@login_required
def list_item_comments(item_id):
    """工作项评论列表。"""
    from app.services import worklog_service
    from app.models.worklog import WorkItemComment
    wi = WorkItem.query.get(item_id)
    if not wi or wi.is_deleted:
        return jsonify({'success': False, 'message': _('工作项不存在')}), 404
    if not worklog_service.can_view_item(current_user, wi):
        return jsonify({'success': False, 'message': _('无权查看')}), 403
    cs = WorkItemComment.query.filter_by(work_item_id=item_id, is_deleted=False) \
        .order_by(WorkItemComment.created_at.asc()).all()
    out = []
    for c in cs:
        d = c.to_dict()
        d['can_delete'] = (c.owner_id == current_user.id or current_user.role in ('admin', 'ceo'))
        out.append(d)
    return jsonify({'success': True, 'comments': out})


@worklog.route('/api/items/<int:item_id>/comments', methods=['POST'])
@login_required
def add_item_comment(item_id):
    """新增工作项评论;镜像到关联任务(TaskReply)与关联项目(Action 跟进)。"""
    from app.services import worklog_service
    from app.models.worklog import WorkItemComment
    wi = WorkItem.query.get(item_id)
    if not wi or wi.is_deleted:
        return jsonify({'success': False, 'message': _('工作项不存在')}), 404
    if not worklog_service.can_view_item(current_user, wi):
        return jsonify({'success': False, 'message': _('无权评论')}), 403
    content = ((request.get_json() or {}).get('content') or '').strip()
    if not content:
        return jsonify({'success': False, 'message': _('评论不能为空')}), 400
    c = WorkItemComment(work_item_id=item_id, content=content, owner_id=current_user.id)
    db.session.add(c)
    try:
        if wi.related_task_id:
            from app.models.task import TaskReply
            db.session.add(TaskReply(
                task_id=wi.related_task_id, subtask_id=wi.related_subtask_id,
                author_id=current_user.id, content='[工作项] ' + content, reply_type='comment'))
        if wi.project_id:
            # 评论作为工作项跟进记录(Action)下的回复(ActionReply),不再单独成一条跟进
            from app.models.action import ActionReply
            owner_user = User.query.get(wi.owner_id) or current_user
            aid = worklog_service.sync_work_item_action(wi, owner_user)
            if aid:
                db.session.add(ActionReply(action_id=aid, content=content, owner_id=current_user.id))
        # 通知工作项创建者(评论者非本人)→ 进「@我」代办
        if wi.owner_id and wi.owner_id != current_user.id:
            from app.models.message import Message
            db.session.add(Message.create_workitem_comment(current_user.id, wi.owner_id, wi, content))
    except Exception as _e:
        logger.warning(f'工作项评论镜像/通知失败: {_e}')
    db.session.commit()
    return jsonify({'success': True, 'comment': dict(c.to_dict(), can_delete=True)})


@worklog.route('/api/items/comments/<int:comment_id>', methods=['DELETE', 'POST'])
@login_required
def delete_item_comment(comment_id):
    """删除工作项评论(本人或管理员;仅删工作项侧,镜像不动)。"""
    from app.models.worklog import WorkItemComment
    c = WorkItemComment.query.get(comment_id)
    if not c or c.is_deleted:
        return jsonify({'success': False, 'message': _('评论不存在')}), 404
    if c.owner_id != current_user.id and current_user.role not in ('admin', 'ceo'):
        return jsonify({'success': False, 'message': _('只能删除自己的评论')}), 403
    c.is_deleted = True
    db.session.commit()
    return jsonify({'success': True})


@worklog.route('/api/items', methods=['GET'])
@login_required
def get_items():
    """获取日历事件列表（FullCalendar 数据源）

    薄壳:逻辑见 app/services/worklog_service.get_viewable_items(web/mobile 单一来源)
    """
    from app.services import worklog_service

    start_date, end_date = worklog_service.parse_calendar_range(
        request.args.get('start'), request.args.get('end')
    )
    owner_id = request.args.get('owner_id', type=int)

    try:
        result = worklog_service.get_viewable_items(
            current_user, start_date, end_date, owner_id
        )
    except worklog_service.WorklogUserNotFound:
        return jsonify({'error': '用户不存在', 'events': [], 'datesWithItems': []}), 404
    except worklog_service.WorklogPermissionDenied:
        return jsonify({'error': '无权查看该用户日历', 'events': [], 'datesWithItems': []}), 403

    return jsonify(result)


@worklog.route('/api/items', methods=['POST'])
@login_required
def create_item():
    """创建工作项(薄壳:逻辑+共享通知见 worklog_service.create_item)"""
    from app.services import worklog_service
    try:
        wi = worklog_service.create_item(current_user, request.get_json())
    except worklog_service.WorklogItemError as e:
        return jsonify({'success': False, 'message': e.message}), e.code
    return jsonify({'success': True, 'message': _('创建成功'), 'data': wi.to_dict()})


@worklog.route('/api/items/<int:item_id>', methods=['GET'])
@login_required
def get_item(item_id):
    """获取单个工作项详情(薄壳)"""
    from app.services import worklog_service
    try:
        data = worklog_service.get_item_detail(current_user, item_id)
    except worklog_service.WorklogItemError as e:
        return jsonify({'success': False, 'message': e.message}), e.code
    return jsonify({'success': True, 'data': data})


@worklog.route('/api/items/<int:item_id>', methods=['PUT'])
@login_required
def update_item(item_id):
    """更新工作项(薄壳:逻辑+时间变更/共享通知见 worklog_service.update_item)"""
    from app.services import worklog_service
    try:
        wi = worklog_service.update_item(current_user, item_id, request.get_json())
    except worklog_service.WorklogItemError as e:
        return jsonify({'success': False, 'message': e.message}), e.code
    return jsonify({'success': True, 'message': _('更新成功'), 'data': wi.to_dict()})


@worklog.route('/api/items/<int:item_id>', methods=['DELETE'])
@login_required
def delete_item(item_id):
    """删除工作项(薄壳:未来作废+通知 / 过去软删见 worklog_service.delete_item)"""
    from app.services import worklog_service
    try:
        action = worklog_service.delete_item(current_user, item_id)
    except worklog_service.WorklogItemError as e:
        return jsonify({'success': False, 'message': e.message}), e.code
    return jsonify({'success': True,
                    'message': _('已作废') if action == 'invalidated' else _('删除成功')})


@worklog.route('/api/items/<int:item_id>/complete', methods=['POST'])
@login_required
def complete_item(item_id):
    """标记工作项完成(薄壳:状态/智能工时/Action同步/通知见 worklog_service.complete_item)"""
    from app.services import worklog_service
    try:
        wi = worklog_service.complete_item(current_user, item_id, request.get_json() or {})
    except worklog_service.WorklogItemError as e:
        return jsonify({'success': False, 'message': e.message}), e.code
    return jsonify({'success': True, 'message': _('标记完成'), 'data': wi.to_dict()})


@worklog.route('/api/items/<int:item_id>/cancel', methods=['POST'])
@login_required
def cancel_item(item_id):
    """标记工作项取消(薄壳:状态+取消通知见 worklog_service.cancel_item)"""
    from app.services import worklog_service
    try:
        wi = worklog_service.cancel_item(current_user, item_id, request.get_json() or {})
    except worklog_service.WorklogItemError as e:
        return jsonify({'success': False, 'message': e.message}), e.code
    return jsonify({'success': True, 'message': _('已取消'), 'data': wi.to_dict()})


@worklog.route('/api/daily/<log_date>', methods=['GET'])
@login_required
def get_daily_log(log_date):
    """获取日志数据（支持传 owner_id 查看他人已提交日志，只读）

    薄壳:逻辑见 app/services/worklog_service.get_day(web/mobile 单一来源)
    """
    from app.services import worklog_service

    try:
        target_date = datetime.strptime(log_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': _('日期格式无效')}), 400

    owner_id = request.args.get('owner_id', type=int)
    data = worklog_service.get_day(current_user, target_date, owner_id)

    return jsonify({'success': True, 'data': data})


@worklog.route('/api/daily/<log_date>', methods=['PUT'])
@login_required
def update_daily_log(log_date):
    """更新日志补充内容(薄壳:逻辑见 worklog_service.update_log_draft)"""
    from app.services import worklog_service
    try:
        target_date = datetime.strptime(log_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': _('日期格式无效')}), 400
    wl = worklog_service.update_log_draft(current_user, target_date, request.get_json() or {})
    return jsonify({'success': True, 'message': _('更新成功'), 'data': wl.to_dict()})


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
    """提交日志(薄壳:@提及/智能工时/质量分/积分/领导通知见 worklog_service.submit_daily_log)"""
    from app.services import worklog_service
    try:
        target_date = datetime.strptime(log_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': _('日期格式无效')}), 400
    try:
        wl = worklog_service.submit_daily_log(current_user, target_date, request.get_json() or {})
    except worklog_service.WorklogItemError as e:
        return jsonify({'success': False, 'message': e.message}), e.code
    return jsonify({'success': True, 'message': _('提交成功'), 'data': wl.to_dict()})


@worklog.route('/api/daily/<log_date>/ai-draft', methods=['POST'])
@login_required
def ai_draft_daily_log(log_date):
    """AI 梳理当天工作项+业务动态为工作描述草稿(仅本人,手动触发)。"""
    from app.services import worklog_service
    try:
        target_date = datetime.strptime(log_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': _('日期格式无效')}), 400
    try:
        draft = worklog_service.generate_daily_draft(current_user, target_date)
    except worklog_service.WorklogItemError as e:
        return jsonify({'success': False, 'message': e.message}), e.code
    return jsonify({'success': True, 'draft': draft})


def _resolve_log_for_comment(log_date_str, create_if_self=False):
    """解析日报(date[+owner_id]) + 权限。返回 (worklog 或 None, error_response 或 None)。"""
    from app.services import worklog_service
    from app.models.worklog import WorkLog
    try:
        target_date = datetime.strptime(log_date_str, '%Y-%m-%d').date()
    except ValueError:
        return None, (jsonify({'success': False, 'message': _('日期格式无效')}), 400)
    owner_id = request.args.get('owner_id', type=int) or current_user.id
    if owner_id != current_user.id and not worklog_service.can_view_user(current_user, owner_id):
        return None, (jsonify({'success': False, 'message': _('无权查看')}), 403)
    if owner_id == current_user.id and create_if_self:
        wl = WorkLog.get_or_create(current_user.id, target_date)
        db.session.commit()
    else:
        wl = WorkLog.query.filter_by(owner_id=owner_id, log_date=target_date).first()
    return wl, None


@worklog.route('/api/daily/<log_date>/comments', methods=['GET'])
@login_required
def list_log_comments(log_date):
    """日报评论列表。"""
    from app.models.worklog import WorkLogComment
    wl, err = _resolve_log_for_comment(log_date)
    if err:
        return err
    if not wl:
        return jsonify({'success': True, 'comments': []})
    cs = WorkLogComment.query.filter_by(worklog_id=wl.id, is_deleted=False) \
        .order_by(WorkLogComment.created_at.asc()).all()
    out = []
    for c in cs:
        d = c.to_dict()
        d['can_delete'] = (c.owner_id == current_user.id or current_user.role in ('admin', 'ceo'))
        out.append(d)
    return jsonify({'success': True, 'comments': out})


@worklog.route('/api/daily/<log_date>/comments', methods=['POST'])
@login_required
def add_log_comment(log_date):
    """新增日报评论(可对自己或有权查看的他人日报)。"""
    from app.models.worklog import WorkLogComment
    wl, err = _resolve_log_for_comment(log_date, create_if_self=True)
    if err:
        return err
    if not wl:
        return jsonify({'success': False, 'message': _('日志不存在')}), 404
    content = ((request.get_json() or {}).get('content') or '').strip()
    if not content:
        return jsonify({'success': False, 'message': _('评论不能为空')}), 400
    c = WorkLogComment(worklog_id=wl.id, content=content, owner_id=current_user.id)
    db.session.add(c)
    # 通知日报创建者(评论者非本人)→ 进「@我」代办
    if wl.owner_id and wl.owner_id != current_user.id:
        try:
            from app.models.message import Message
            db.session.add(Message.create_worklog_comment(current_user.id, wl.owner_id, wl, content))
        except Exception as _e:
            logger.warning(f'日报评论通知失败: {_e}')
    db.session.commit()
    return jsonify({'success': True, 'comment': dict(c.to_dict(), can_delete=True)})


@worklog.route('/api/daily/comments/<int:comment_id>', methods=['DELETE', 'POST'])
@login_required
def delete_log_comment(comment_id):
    """删除日报评论(本人或管理员)。"""
    from app.models.worklog import WorkLogComment
    c = WorkLogComment.query.get(comment_id)
    if not c or c.is_deleted:
        return jsonify({'success': False, 'message': _('评论不存在')}), 404
    if c.owner_id != current_user.id and current_user.role not in ('admin', 'ceo'):
        return jsonify({'success': False, 'message': _('只能删除自己的评论')}), 403
    c.is_deleted = True
    db.session.commit()
    return jsonify({'success': True})


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
# 工作项附件相关 API
# ============================================================

@worklog.route('/api/items/<int:item_id>/upload-attachment', methods=['POST'])
@login_required
def upload_workitem_attachment(item_id):
    """上传工作项附件（图片或PDF）"""
    from werkzeug.utils import secure_filename
    import uuid

    from app.services import worklog_service
    work_item = WorkItem.query.get(item_id)
    if not work_item or work_item.is_deleted:
        return jsonify({'success': False, 'message': _('工作项不存在')}), 404

    # 本人 + 被共享/可查看者(下属管理/admin)均可上传附件
    if not worklog_service.can_view_item(current_user, work_item):
        return jsonify({'success': False, 'message': _('无权操作此工作项')}), 403

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': _('未选择文件')})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': _('未选择文件')})

    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'heic', 'heif', 'pdf'}
    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        return jsonify({'success': False, 'message': _('不支持的文件格式，支持：PNG、JPG、GIF、WEBP、HEIC、PDF')})

    try:
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)

        if file_size > 5 * 1024 * 1024:
            return jsonify({'success': False, 'message': _('文件大小超过5MB限制')})

        original_filename = file.filename
        ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'bin'

        existing_names = [att.get('filename') for att in work_item.attachments_list]
        if original_filename in existing_names:
            base = original_filename.rsplit('.', 1)[0] if '.' in original_filename else original_filename
            counter = 1
            while f"{base}-{counter}.{ext}" in existing_names:
                counter += 1
            original_filename = f"{base}-{counter}.{ext}"

        file_type = 'pdf' if ext == 'pdf' else 'image'

        from app.utils.smart_storage_manager import get_smart_storage
        file.seek(0)
        smart_storage = get_smart_storage()

        result = smart_storage.upload_file(
            object_id=work_item.id,
            file=file,
            filename=original_filename,
            file_type='attachment',
            bucket_type='invoice',
            business_type='workitem'
        )

        logger.info(f"工作项附件上传结果: {result}")

        if result and result.get('url'):
            work_item.add_attachment(
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
                    'index': len(work_item.attachments_list) - 1
                }
            })
        else:
            return jsonify({'success': False, 'message': _('上传失败')})

    except Exception as e:
        logger.error(f"上传工作项附件失败: {e}")
        return jsonify({'success': False, 'message': f'{_("上传失败")}: {str(e)}'}), 500


@worklog.route('/api/upload-image', methods=['POST'])
@login_required
def upload_worklog_inline_image():
    """通用内嵌图片上传:供工作描述/日报正文「插入图片」用,返回 url 供 Markdown 引用。
    不挂任何对象(新建态也可用),仅落存储。"""
    file = request.files.get('file')
    if not file or not file.filename:
        return jsonify({'success': False, 'message': _('未选择文件')}), 400
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in {'png', 'jpg', 'jpeg', 'gif', 'webp', 'heic', 'heif'}:
        return jsonify({'success': False, 'message': _('仅支持图片:PNG、JPG、GIF、WEBP、HEIC')}), 400
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > 5 * 1024 * 1024:
        return jsonify({'success': False, 'message': _('图片大小超过5MB限制')}), 400
    try:
        from app.utils.smart_storage_manager import get_smart_storage
        from datetime import datetime as _dt
        safe = f"img_{current_user.id}_{_dt.now().strftime('%Y%m%d%H%M%S')}.{ext}"
        result = get_smart_storage().upload_file(
            object_id=current_user.id, file=file, filename=safe,
            file_type='image', bucket_type='invoice', business_type='worklog_note')
        if result and result.get('url'):
            return jsonify({'success': True, 'data': {'url': result.get('url'), 'filename': file.filename}})
        return jsonify({'success': False, 'message': _('上传失败')}), 500
    except Exception as e:
        logger.error(f"内嵌图片上传失败: {e}")
        return jsonify({'success': False, 'message': f'{_("上传失败")}: {str(e)}'}), 500


@worklog.route('/api/items/<int:item_id>/delete-attachment/<int:index>', methods=['DELETE', 'POST'])
@login_required
def delete_workitem_attachment(item_id, index):
    """删除工作项附件"""
    work_item = WorkItem.query.get(item_id)
    if not work_item or work_item.is_deleted:
        return jsonify({'success': False, 'message': _('工作项不存在')}), 404

    if work_item.owner_id != current_user.id:
        return jsonify({'success': False, 'message': _('无权操作此工作项')}), 403

    attachment = work_item.get_attachment(index)
    if not attachment:
        return jsonify({'success': False, 'message': _('附件不存在')}), 404

    if work_item.remove_attachment(index):
        db.session.commit()
        return jsonify({'success': True, 'message': _('删除成功')})
    else:
        return jsonify({'success': False, 'message': _('删除失败')}), 500


@worklog.route('/api/items/<int:item_id>/preview-attachment/<int:index>')
@login_required
def preview_workitem_attachment(item_id, index):
    """预览/下载工作项附件"""
    import requests as http_requests
    from flask import Response
    from urllib.parse import quote

    work_item = WorkItem.query.get(item_id)
    if not work_item or work_item.is_deleted:
        return jsonify({'success': False, 'message': _('工作项不存在')}), 404

    if not can_view_work_item(current_user, work_item):
        return jsonify({'success': False, 'message': _('无权查看此工作项')}), 403

    attachment = work_item.get_attachment(index)
    if not attachment:
        return jsonify({'success': False, 'message': _('附件不存在')}), 404

    url = attachment.get('url')
    filename = attachment.get('filename', 'attachment')
    file_type = attachment.get('type', 'image')

    force_download = request.args.get('download') == '1'

    if file_type == 'pdf':
        mime_type = 'application/pdf'
    else:
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'bin'
        mime_map = {
            'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
            'png': 'image/png', 'gif': 'image/gif',
            'webp': 'image/webp', 'heic': 'image/heic',
            'pdf': 'application/pdf'
        }
        mime_type = mime_map.get(ext, 'application/octet-stream')

    encoded_filename = quote(filename, safe='')
    disposition_type = 'attachment' if force_download else 'inline'

    try:
        if url and url.startswith('/storage/nas/'):
            from app.views.storage import _get_file_with_fallback
            from urllib.parse import urlparse, parse_qs

            parsed = urlparse(url)
            path_parts = parsed.path.split('/')
            bucket_type = path_parts[3] if len(path_parts) > 3 else 'invoice'
            query_params = parse_qs(parsed.query)
            nas_path = query_params.get('path', [''])[0]

            if nas_path:
                file_content, source = _get_file_with_fallback(nas_path, bucket_type)
                if file_content:
                    headers = {
                        'Content-Type': mime_type,
                        'Content-Disposition': f"{disposition_type}; filename*=UTF-8''{encoded_filename}",
                        'X-Storage-Source': source or 'unknown'
                    }
                    return Response(file_content, headers=headers)
                else:
                    return jsonify({'success': False, 'message': _('文件获取失败')}), 404

        elif url and (url.startswith('http://') or url.startswith('https://')):
            resp = http_requests.get(url, timeout=30)
            if resp.status_code == 200:
                headers = {
                    'Content-Type': mime_type,
                    'Content-Disposition': f"{disposition_type}; filename*=UTF-8''{encoded_filename}"
                }
                return Response(resp.content, headers=headers)
            else:
                return jsonify({'success': False, 'message': _('文件获取失败')}), 404
        elif url and url.startswith('/storage/'):
            # 本地存储(FORCE_LOCAL_STORAGE):直接读 ./storage 下文件返回
            import os
            from flask import current_app
            rel = url.split('?', 1)[0][len('/storage/'):]
            storage_dir = os.path.abspath(os.path.join(current_app.root_path, '..', 'storage'))
            fpath = os.path.abspath(os.path.join(storage_dir, rel))
            if fpath.startswith(storage_dir) and os.path.exists(fpath):
                with open(fpath, 'rb') as _f:
                    content = _f.read()
                headers = {
                    'Content-Type': mime_type,
                    'Content-Disposition': f"{disposition_type}; filename*=UTF-8''{encoded_filename}"
                }
                return Response(content, headers=headers)
            return jsonify({'success': False, 'message': _('文件不存在')}), 404
        else:
            return jsonify({'success': False, 'message': _('无效的文件URL')}), 400

    except Exception as e:
        logger.error(f"预览工作项附件失败: {e}")
        return jsonify({'success': False, 'message': f'{_("预览失败")}: {str(e)}'}), 500


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

        # 使用智能存储（NAS 优先，Supabase 回退）
        from app.utils.smart_storage_manager import get_smart_storage

        # 重置文件指针（之前已读取过）
        file.seek(0)

        smart_storage = get_smart_storage()

        result = smart_storage.upload_file(
            object_id=worklog.id,
            file=file,
            filename=original_filename,
            file_type='attachment',
            bucket_type='invoice',  # 复用 invoice bucket
            business_type='worklog'
        )

        logger.info(f"智能存储上传结果: {result}")

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

    # 确定 MIME 类型
    if file_type == 'pdf':
        mime_type = 'application/pdf'
    else:
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'bin'
        mime_map = {
            'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
            'png': 'image/png', 'gif': 'image/gif',
            'webp': 'image/webp', 'heic': 'image/heic',
            'pdf': 'application/pdf'
        }
        mime_type = mime_map.get(ext, 'application/octet-stream')

    # 对文件名进行 RFC 5987 编码以支持中文
    from urllib.parse import quote
    encoded_filename = quote(filename, safe='')
    disposition_type = 'attachment' if force_download else 'inline'

    try:
        # 处理 NAS 智能存储路径
        if url and url.startswith('/storage/nas/'):
            from app.views.storage import _get_file_with_fallback
            from urllib.parse import urlparse, parse_qs

            parsed = urlparse(url)
            path_parts = parsed.path.split('/')
            bucket_type = path_parts[3] if len(path_parts) > 3 else 'invoice'
            query_params = parse_qs(parsed.query)
            nas_path = query_params.get('path', [''])[0]

            if nas_path:
                file_content, source = _get_file_with_fallback(nas_path, bucket_type)
                if file_content:
                    logger.info(f"Worklog 附件从 {source} 获取成功")
                    headers = {
                        'Content-Type': mime_type,
                        'Content-Disposition': f"{disposition_type}; filename*=UTF-8''{encoded_filename}",
                        'X-Storage-Source': source or 'unknown'
                    }
                    return Response(file_content, headers=headers)
                else:
                    return jsonify({'success': False, 'message': _('文件获取失败')}), 404

        # 云端文件（Supabase URL），代理下载
        elif url and (url.startswith('http://') or url.startswith('https://')):
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                headers = {
                    'Content-Type': mime_type,
                    'Content-Disposition': f"{disposition_type}; filename*=UTF-8''{encoded_filename}"
                }
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
    # 检查是否有「可管理成员」(数据归属下属 + 管辖部门成员)或管理员权限
    subordinate_ids = manageable_user_ids(current_user)
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

    # 被@提及的用户可以查看
    # 注意：mentioned_users 存储的是字符串ID，需要同时检查整数和字符串
    if worklog.mentioned_users:
        if user.id in worklog.mentioned_users or str(user.id) in worklog.mentioned_users:
            return True

    # 与日历查看口径一致:能看其工作日历(本人/admin/ceo/system/company/department/下属)
    # 即能看其日报。收口到 can_view_user 单一来源,不再单独判 admin/部门负责人/下属。
    from app.services import worklog_service
    try:
        if worklog_service.can_view_user(user, worklog.owner_id):
            return True
    except worklog_service.WorklogUserNotFound:
        pass

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


# ===== 日志反馈 API（匿名点赞/点踩）=====

@worklog.route('/api/daily/<log_date>/react', methods=['POST'])
@login_required
def react_to_worklog(log_date):
    """对日志进行反馈（大拇指/小拇指）

    请求体: {"type": "up"} 或 {"type": "down"}

    业务逻辑：
    - 已提交的日志才能被反馈
    - 不能给自己的日志反馈
    - 点一次添加，再点同一个取消
    - 点不同的自动切换（大拇指→小拇指 或 反之）
    - 匿名：不记录谁点的到返回数据中
    """
    try:
        target_date = datetime.strptime(log_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'success': False, 'message': _('日期格式无效')}), 400

    # 获取日志所有者ID
    owner_id = request.args.get('owner_id', type=int)
    if not owner_id:
        return jsonify({'success': False, 'message': _('缺少 owner_id 参数')}), 400

    # 查找日志
    worklog_obj = WorkLog.query.filter_by(
        owner_id=owner_id,
        log_date=target_date
    ).first()

    if not worklog_obj:
        return jsonify({'success': False, 'message': _('日志不存在')}), 404

    # 权限检查：只能给已提交的日志反馈
    if worklog_obj.status != 'submitted':
        return jsonify({'success': False, 'message': _('只能对已提交的日志进行反馈')}), 400

    # 权限检查：不能给自己的日志反馈
    if worklog_obj.owner_id == current_user.id:
        return jsonify({'success': False, 'message': _('不能给自己的日志点赞')}), 400

    # 获取反馈类型
    data = request.get_json()
    if not data or 'type' not in data:
        return jsonify({'success': False, 'message': _('缺少反馈类型')}), 400

    reaction_type = data['type']
    if reaction_type not in ['up', 'down']:
        return jsonify({'success': False, 'message': _('无效的反馈类型')}), 400

    # 查找现有反馈
    existing_reaction = WorkLogReaction.query.filter_by(
        worklog_id=worklog_obj.id,
        user_id=current_user.id
    ).first()

    action = None  # 记录操作类型
    from sqlalchemy import text

    if existing_reaction:
        # 立即提取需要的信息，然后从 session 中移除，防止 SQLAlchemy 自动同步
        reaction_id = existing_reaction.id
        old_reaction_type = existing_reaction.reaction_type
        db.session.expunge(existing_reaction)

        if old_reaction_type == reaction_type:
            # 相同类型：取消反馈
            if reaction_type == 'up':
                worklog_obj.thumbs_up_count = max(0, (worklog_obj.thumbs_up_count or 0) - 1)
            else:
                worklog_obj.thumbs_down_count = max(0, (worklog_obj.thumbs_down_count or 0) - 1)
            # 使用原生 SQL 删除
            db.session.execute(
                text('DELETE FROM worklog_reactions WHERE id = :id'),
                {'id': reaction_id}
            )
            action = 'removed'
            user_reaction = None
        else:
            # 不同类型：切换反馈
            if old_reaction_type == 'up':
                worklog_obj.thumbs_up_count = max(0, (worklog_obj.thumbs_up_count or 0) - 1)
                worklog_obj.thumbs_down_count = (worklog_obj.thumbs_down_count or 0) + 1
            else:
                worklog_obj.thumbs_down_count = max(0, (worklog_obj.thumbs_down_count or 0) - 1)
                worklog_obj.thumbs_up_count = (worklog_obj.thumbs_up_count or 0) + 1
            # 使用原生 SQL 更新
            db.session.execute(
                text('UPDATE worklog_reactions SET reaction_type = :type, created_at = :time WHERE id = :id'),
                {'type': reaction_type, 'time': get_local_time(), 'id': reaction_id}
            )
            action = 'switched'
            user_reaction = reaction_type
    else:
        # 新增反馈
        new_reaction = WorkLogReaction(
            worklog_id=worklog_obj.id,
            user_id=current_user.id,
            reaction_type=reaction_type
        )
        db.session.add(new_reaction)
        if reaction_type == 'up':
            worklog_obj.thumbs_up_count = (worklog_obj.thumbs_up_count or 0) + 1
        else:
            worklog_obj.thumbs_down_count = (worklog_obj.thumbs_down_count or 0) + 1
        action = 'added'
        user_reaction = reaction_type

    db.session.commit()

    return jsonify({
        'success': True,
        'action': action,
        'reactions': {
            'thumbs_up': worklog_obj.thumbs_up_count or 0,
            'thumbs_down': worklog_obj.thumbs_down_count or 0,
            'user_reaction': user_reaction
        }
    })
