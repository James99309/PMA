"""星图视图 — 项目/客户关系可视化"""
from flask import Blueprint, render_template, request, jsonify, url_for
from flask_login import login_required, current_user
from app.decorators import permission_required
from app.models.project import Project
from app.models.customer import Company, Contact
from app.models.quotation import Quotation
from app.models.relation import ProjectMember
from app.models.project_customer_association import ProjectCustomerAssociation
from app.models.worklog import WorkItem
from app.models.task import Task
from app.models.user import User
from app.extensions import db
from sqlalchemy import desc

star_graph = Blueprint('star_graph', __name__, url_prefix='/star-graph')


# ── 页面路由 ──────────────────────────────────────────────

@star_graph.route('/project/<int:project_id>')
@login_required
@permission_required('project', 'view')
def project_graph(project_id):
    project = Project.query.get_or_404(project_id)
    return render_template(
        'star_graph/tw_star_graph.html',
        center_type='project',
        center_id=project.id,
        center_name=project.project_name,
        back_url=url_for('project.get_project', project_id=project.id),
    )


@star_graph.route('/company/<int:company_id>')
@login_required
@permission_required('customer', 'view')
def company_graph(company_id):
    company = Company.query.get_or_404(company_id)
    return render_template(
        'star_graph/tw_star_graph.html',
        center_type='company',
        center_id=company.id,
        center_name=company.company_name,
        back_url=url_for('customer.view_company', company_id=company.id),
    )


# ── 数据 API ─────────────────────────────────────────────

@star_graph.route('/api/data')
@login_required
def api_graph_data():
    center_type = request.args.get('center_type', '')
    center_id = request.args.get('center_id', 0, type=int)

    if center_type == 'project':
        return jsonify(_build_project_graph(center_id))
    elif center_type == 'company':
        return jsonify(_build_company_graph(center_id))
    else:
        return jsonify({'error': 'Invalid center_type'}), 400


# ── 以项目为中心 ─────────────────────────────────────────

def _build_project_graph(project_id):
    project = Project.query.get(project_id)
    if not project:
        return {'centerId': '', 'nodes': [], 'links': []}

    nodes = {}
    links = []
    user_ids = set()

    # 中心节点：项目
    pid = f'project_{project.id}'
    nodes[pid] = _project_node(project)

    # 关联企业
    assocs = ProjectCustomerAssociation.query.filter_by(project_id=project.id).all()
    company_ids = set()
    for a in assocs:
        if a.company:
            cid = f'company_{a.company_id}'
            company_ids.add(a.company_id)
            nodes[cid] = _company_node(a.company)
            role_label = a.company.company_type or ''
            links.append({'source': pid, 'target': cid, 'label': role_label})

    # 企业联系人
    if company_ids:
        contacts = Contact.query.filter(Contact.company_id.in_(company_ids)).all()
        for ct in contacts:
            ctid = f'contact_{ct.id}'
            nodes[ctid] = _contact_node(ct)
            links.append({
                'source': f'company_{ct.company_id}',
                'target': ctid,
                'label': '',
            })

    # 项目成员
    members = ProjectMember.query.filter_by(project_id=project.id).all()
    for m in members:
        user_ids.add(m.user_id)

    # owner / vendor_sales_manager
    if project.owner_id:
        user_ids.add(project.owner_id)
    if project.vendor_sales_manager_id:
        user_ids.add(project.vendor_sales_manager_id)

    # 批量加载用户
    if user_ids:
        users = {u.id: u for u in User.query.filter(User.id.in_(user_ids)).all()}
    else:
        users = {}

    # 添加成员节点
    for m in members:
        u = users.get(m.user_id)
        if not u:
            continue
        mid = f'member_{u.id}'
        if mid not in nodes:
            nodes[mid] = _member_node(u, m.role)
        links.append({'source': pid, 'target': mid, 'label': _role_label(m.role)})

    # owner
    if project.owner_id and project.owner_id in users:
        mid = f'member_{project.owner_id}'
        if mid not in nodes:
            nodes[mid] = _member_node(users[project.owner_id], 'owner')
        links.append({'source': pid, 'target': mid, 'label': '负责人'})

    # vendor_sales_manager
    if project.vendor_sales_manager_id and project.vendor_sales_manager_id in users:
        mid = f'member_{project.vendor_sales_manager_id}'
        if mid not in nodes:
            nodes[mid] = _member_node(users[project.vendor_sales_manager_id], 'sales_manager')
        links.append({'source': pid, 'target': mid, 'label': '销售经理'})

    # 报价单
    quotations = Quotation.query.filter_by(
        project_id=project.id,
    ).order_by(desc(Quotation.created_at)).limit(15).all()
    for q in quotations:
        qid = f'quotation_{q.id}'
        nodes[qid] = _quotation_node(q)
        links.append({'source': pid, 'target': qid, 'label': '报价'})
        # 报价→企业
        if q.customer_id and f'company_{q.customer_id}' in nodes:
            links.append({'source': qid, 'target': f'company_{q.customer_id}', 'label': '客户'})

    # 工作活动（最近10条）
    work_items = WorkItem.query.filter(
        WorkItem.project_id == project.id,
        WorkItem.is_deleted == False,
    ).order_by(desc(WorkItem.planned_date)).limit(10).all()
    for w in work_items:
        wid = f'workitem_{w.id}'
        nodes[wid] = _workitem_node(w)
        links.append({'source': pid, 'target': wid, 'label': '活动'})

    # 活跃任务
    tasks = Task.query.filter(
        Task.project_id == project.id,
        Task.is_deleted == False,
        Task.status.notin_(['completed', 'cancelled']),
    ).order_by(desc(Task.created_at)).limit(10).all()
    for t in tasks:
        tid = f'task_{t.id}'
        nodes[tid] = _task_node(t, users)
        links.append({'source': pid, 'target': tid, 'label': '任务'})

    # 关联项目（通过共享企业）
    if company_ids:
        related_assocs = ProjectCustomerAssociation.query.filter(
            ProjectCustomerAssociation.company_id.in_(company_ids),
            ProjectCustomerAssociation.project_id != project.id,
        ).all()
        related_project_ids = {a.project_id for a in related_assocs}
        if related_project_ids:
            related_projects = Project.query.filter(
                Project.id.in_(related_project_ids),
            ).limit(8).all()
            for rp in related_projects:
                rpid = f'project_{rp.id}'
                if rpid not in nodes:
                    nodes[rpid] = _project_node(rp)
                # 找到共享的企业建立连线
                for a in related_assocs:
                    if a.project_id == rp.id and f'company_{a.company_id}' in nodes:
                        links.append({
                            'source': f'company_{a.company_id}',
                            'target': rpid,
                            'label': '',
                        })

    return {
        'centerId': pid,
        'nodes': list(nodes.values()),
        'links': _dedup_links(links),
    }


# ── 以客户为中心 ─────────────────────────────────────────

def _build_company_graph(company_id):
    company = Company.query.get(company_id)
    if not company:
        return {'centerId': '', 'nodes': [], 'links': []}

    nodes = {}
    links = []
    user_ids = set()

    # 中心节点
    cid = f'company_{company.id}'
    nodes[cid] = _company_node(company)

    # 联系人
    contacts = Contact.query.filter_by(company_id=company.id).all()
    for ct in contacts:
        ctid = f'contact_{ct.id}'
        nodes[ctid] = _contact_node(ct)
        links.append({'source': cid, 'target': ctid, 'label': ''})

    # 关联项目
    assocs = ProjectCustomerAssociation.query.filter_by(company_id=company.id).all()
    project_ids = set()
    for a in assocs:
        project_ids.add(a.project_id)

    if project_ids:
        projects = Project.query.filter(
            Project.id.in_(project_ids),
        ).all()
        for p in projects:
            pid = f'project_{p.id}'
            nodes[pid] = _project_node(p)
            links.append({'source': cid, 'target': pid, 'label': ''})
            # 收集项目成员
            if p.owner_id:
                user_ids.add(p.owner_id)
            members = ProjectMember.query.filter_by(project_id=p.id).all()
            for m in members:
                user_ids.add(m.user_id)

    # 批量加载用户
    if user_ids:
        users = {u.id: u for u in User.query.filter(User.id.in_(user_ids)).all()}
    else:
        users = {}

    # 添加项目成员节点
    if project_ids:
        projects_list = Project.query.filter(
            Project.id.in_(project_ids),
        ).all()
        for p in projects_list:
            pid = f'project_{p.id}'
            if p.owner_id and p.owner_id in users:
                mid = f'member_{p.owner_id}'
                if mid not in nodes:
                    nodes[mid] = _member_node(users[p.owner_id], 'owner')
                links.append({'source': pid, 'target': mid, 'label': '负责人'})

    # 报价单
    quotations = Quotation.query.filter_by(
        customer_id=company.id,
    ).order_by(desc(Quotation.created_at)).limit(15).all()
    for q in quotations:
        qid = f'quotation_{q.id}'
        nodes[qid] = _quotation_node(q)
        links.append({'source': cid, 'target': qid, 'label': '报价'})
        # 报价→项目
        if q.project_id and f'project_{q.project_id}' in nodes:
            links.append({'source': qid, 'target': f'project_{q.project_id}', 'label': '项目'})

    # 工作活动
    work_items = WorkItem.query.filter(
        WorkItem.customer_id == company.id,
        WorkItem.is_deleted == False,
    ).order_by(desc(WorkItem.planned_date)).limit(10).all()
    for w in work_items:
        wid = f'workitem_{w.id}'
        nodes[wid] = _workitem_node(w)
        links.append({'source': cid, 'target': wid, 'label': '活动'})

    # 任务
    tasks = Task.query.filter(
        Task.customer_id == company.id,
        Task.is_deleted == False,
        Task.status.notin_(['completed', 'cancelled']),
    ).order_by(desc(Task.created_at)).limit(10).all()
    for t in tasks:
        tid = f'task_{t.id}'
        nodes[tid] = _task_node(t, users)
        links.append({'source': cid, 'target': tid, 'label': '任务'})

    return {
        'centerId': cid,
        'nodes': list(nodes.values()),
        'links': _dedup_links(links),
    }


# ── 节点构造辅助函数 ─────────────────────────────────────

def _project_node(p):
    from app.utils.dictionary_helpers import get_amount_unit_config, get_currency_symbol
    unit_cfg = get_amount_unit_config()
    symbol = get_currency_symbol()
    amount_str = ''
    if p.quotation_customer:
        amount_str = f'{symbol}{p.quotation_customer / unit_cfg["divisor"]:.{unit_cfg["decimal_places"]}f}{unit_cfg["unit"]}'
    return {
        'id': f'project_{p.id}',
        'name': p.project_name or '',
        'nodeType': 'project',
        'extra': {
            'stage': p.current_stage or '',
            'amount': amount_str,
        },
    }


def _company_node(c):
    return {
        'id': f'company_{c.id}',
        'name': c.company_name or '',
        'nodeType': 'company',
        'extra': {
            'role': c.company_type or '',
        },
    }


def _contact_node(ct):
    return {
        'id': f'contact_{ct.id}',
        'name': ct.name or '',
        'nodeType': 'contact',
        'extra': {
            'position': ct.position or '',
            'parentCompany': f'company_{ct.company_id}',
        },
    }


def _member_node(u, role=''):
    return {
        'id': f'member_{u.id}',
        'name': u.real_name or u.username or '',
        'nodeType': 'member',
        'extra': {
            'role': _role_label(role),
            'dept': '',
        },
    }


def _quotation_node(q):
    from app.utils.dictionary_helpers import get_amount_unit_config, get_currency_symbol
    unit_cfg = get_amount_unit_config()
    symbol = get_currency_symbol()
    amount_str = ''
    if q.amount:
        amount_str = f'{symbol}{q.amount / unit_cfg["divisor"]:.{unit_cfg["decimal_places"]}f}{unit_cfg["unit"]}'
    return {
        'id': f'quotation_{q.id}',
        'name': q.quotation_number or '',
        'nodeType': 'quotation',
        'extra': {
            'amount': amount_str,
            'status': q.approval_status or '',
        },
    }


def _workitem_node(w):
    date_str = ''
    if w.planned_date:
        date_str = w.planned_date.strftime('%m-%d')
    return {
        'id': f'workitem_{w.id}',
        'name': w.title or '',
        'nodeType': 'workitem',
        'extra': {
            'workType': w.work_type or '',
            'date': date_str,
        },
    }


def _task_node(t, users=None):
    assignee_name = ''
    if users and t.assignee_id and t.assignee_id in users:
        u = users[t.assignee_id]
        assignee_name = u.real_name or u.username or ''
    due_str = ''
    if t.due_date:
        due_str = t.due_date.strftime('%m-%d')
    return {
        'id': f'task_{t.id}',
        'name': t.title or '',
        'nodeType': 'task',
        'extra': {
            'status': t.status or '',
            'assignee': assignee_name,
            'dueDate': due_str,
        },
    }


def _role_label(role):
    labels = {
        'owner': '负责人',
        'sales_manager': '销售经理',
        'member': '成员',
        'solution_engineer': '方案工程师',
        'product_manager': '产品经理',
    }
    return labels.get(role, role or '')


def _dedup_links(links):
    seen = set()
    result = []
    for l in links:
        key = f"{l['source']}|{l['target']}"
        rev_key = f"{l['target']}|{l['source']}"
        if key not in seen and rev_key not in seen:
            seen.add(key)
            result.append(l)
    return result
