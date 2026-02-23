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
from app.utils.dictionary_helpers import company_type_label, project_stage_label
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
        back_url=url_for('project.view_project', project_id=project.id),
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
            role_label = company_type_label(a.company.company_type) if a.company.company_type else ''
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

    # 报价单（排除失败阶段）
    quotations = Quotation.query.filter(
        Quotation.project_id == project.id,
        db.or_(Quotation.project_stage != 'failed', Quotation.project_stage.is_(None)),
    ).order_by(desc(Quotation.created_at)).limit(15).all()
    for q in quotations:
        qid = f'quotation_{q.id}'
        nodes[qid] = _quotation_node(q)
        links.append({'source': pid, 'target': qid, 'label': '报价'})
        # 报价→企业
        if q.customer_id and f'company_{q.customer_id}' in nodes:
            links.append({'source': qid, 'target': f'company_{q.customer_id}', 'label': '客户'})

    # 活动时间链（工作活动 + 任务合并，按时间排序）
    _build_timeline_chain(pid, project.id, 'project', nodes, links, users)

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

    # 报价单（排除失败阶段）
    quotations = Quotation.query.filter(
        Quotation.customer_id == company.id,
        db.or_(Quotation.project_stage != 'failed', Quotation.project_stage.is_(None)),
    ).order_by(desc(Quotation.created_at)).limit(15).all()
    for q in quotations:
        qid = f'quotation_{q.id}'
        nodes[qid] = _quotation_node(q)
        links.append({'source': cid, 'target': qid, 'label': '报价'})
        # 报价→项目
        if q.project_id and f'project_{q.project_id}' in nodes:
            links.append({'source': qid, 'target': f'project_{q.project_id}', 'label': '项目'})

    # 活动时间链（工作活动 + 任务合并，按时间排序）
    _build_timeline_chain(cid, company.id, 'company', nodes, links, users)

    return {
        'centerId': cid,
        'nodes': list(nodes.values()),
        'links': _dedup_links(links),
    }


# ── 时间链构造 ────────────────────────────────────────────

def _build_timeline_chain(center_id, entity_id, entity_type, nodes, links, users):
    """将工作活动和任务合并为一条时间链，最近的连中心，其余虚线串联"""
    from datetime import date as _date

    # 查询工作活动
    if entity_type == 'project':
        work_items = WorkItem.query.filter(
            WorkItem.project_id == entity_id,
            WorkItem.is_deleted == False,
        ).order_by(desc(WorkItem.planned_date)).limit(10).all()
        tasks = Task.query.filter(
            Task.project_id == entity_id,
            Task.is_deleted == False,
            Task.status.notin_(['completed', 'cancelled']),
        ).order_by(desc(Task.created_at)).limit(10).all()
    else:  # company
        work_items = WorkItem.query.filter(
            WorkItem.customer_id == entity_id,
            WorkItem.is_deleted == False,
        ).order_by(desc(WorkItem.planned_date)).limit(5).all()
        tasks = Task.query.filter(
            Task.customer_id == entity_id,
            Task.is_deleted == False,
            Task.status.notin_(['completed', 'cancelled']),
        ).order_by(desc(Task.created_at)).limit(5).all()

    # 合并并按日期排序（最近在前）
    timeline = []
    for w in work_items:
        d = w.planned_date
        if isinstance(d, _date):
            from datetime import datetime
            d = datetime.combine(d, datetime.min.time())
        timeline.append(('workitem', w, d))
    for t in tasks:
        d = t.due_date or t.created_at
        if isinstance(d, _date) and not hasattr(d, 'hour'):
            from datetime import datetime
            d = datetime.combine(d, datetime.min.time())
        timeline.append(('task', t, d))

    timeline.sort(key=lambda x: x[2] or _date.min, reverse=True)
    timeline = timeline[:8]  # 限制总数

    if not timeline:
        return

    # 构建节点和链式连接
    prev_nid = None
    for i, (typ, obj, dt) in enumerate(timeline):
        if typ == 'workitem':
            nid = f'workitem_{obj.id}'
            nodes[nid] = _workitem_node(obj)
        else:
            nid = f'task_{obj.id}'
            nodes[nid] = _task_node(obj, users)

        if i == 0:
            # 最近的连到中心
            links.append({'source': center_id, 'target': nid, 'label': '活动'})
        else:
            # 后续的串联到前一个，标记为 timeline 类型
            links.append({
                'source': prev_nid, 'target': nid,
                'label': '', 'linkType': 'timeline',
            })
        prev_nid = nid

        # 工作活动关联的联系人、客户、项目（如果已在图中则连线点亮）
        if typ == 'workitem':
            if obj.contact_id:
                ct_nid = f'contact_{obj.contact_id}'
                if ct_nid in nodes:
                    links.append({'source': nid, 'target': ct_nid, 'label': ''})
            if obj.customer_id:
                co_nid = f'company_{obj.customer_id}'
                if co_nid in nodes and co_nid != center_id:
                    links.append({'source': nid, 'target': co_nid, 'label': ''})
            if obj.project_id:
                p_nid = f'project_{obj.project_id}'
                if p_nid in nodes and p_nid != center_id:
                    links.append({'source': nid, 'target': p_nid, 'label': ''})


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
        'url': url_for('project.view_project', project_id=p.id),
        'extra': {
            'stage': project_stage_label(p.current_stage) if p.current_stage else '',
            'amount': amount_str,
        },
    }


def _company_node(c):
    return {
        'id': f'company_{c.id}',
        'name': c.company_name or '',
        'nodeType': 'company',
        'url': url_for('customer.view_company', company_id=c.id),
        'extra': {
            'role': company_type_label(c.company_type) if c.company_type else '',
        },
    }


def _contact_node(ct):
    return {
        'id': f'contact_{ct.id}',
        'name': ct.name or '',
        'nodeType': 'contact',
        'url': url_for('customer.view_contact', contact_id=ct.id),
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
        'url': url_for('user.user_detail', user_id=u.id),
        'extra': {
            'role': _role_label(role),
            'dept': '',
        },
    }


def _quotation_node(q):
    from app.utils.dictionary_helpers import get_amount_unit_config, get_currency_symbol
    from app.models.quotation import QuotationApprovalStatus
    unit_cfg = get_amount_unit_config()
    symbol = get_currency_symbol()
    amount_str = ''
    if q.amount:
        amount_str = f'{symbol}{q.amount / unit_cfg["divisor"]:.{unit_cfg["decimal_places"]}f}{unit_cfg["unit"]}'
    status_label = ''
    if q.approval_status:
        status_info = QuotationApprovalStatus.get_status_label(q.approval_status)
        status_label = status_info.get('label', q.approval_status) if isinstance(status_info, dict) else str(status_info)
    return {
        'id': f'quotation_{q.id}',
        'name': q.quotation_number or '',
        'nodeType': 'quotation',
        'url': url_for('quotation.view_quotation', id=q.id),
        'extra': {
            'amount': amount_str,
            'status': status_label,
        },
    }


def _workitem_node(w):
    date_str = ''
    if w.planned_date:
        date_str = w.planned_date.strftime('%Y-%m-%d')
    desc = (w.description or '')[:80]
    if w.description and len(w.description) > 80:
        desc += '...'
    return {
        'id': f'workitem_{w.id}',
        'name': w.title or '',
        'nodeType': 'workitem',
        'extra': {
            'workType': w.get_type_label() if w.work_type else '',
            'date': date_str,
            'desc': desc,
        },
    }


def _task_node(t, users=None):
    assignee_name = ''
    if users and t.assignee_id and t.assignee_id in users:
        u = users[t.assignee_id]
        assignee_name = u.real_name or u.username or ''
    due_str = ''
    if t.due_date:
        due_str = t.due_date.strftime('%Y-%m-%d')
    created_str = ''
    if t.created_at:
        created_str = t.created_at.strftime('%Y-%m-%d')
    desc = (t.description or '')[:80]
    if t.description and len(t.description) > 80:
        desc += '...'
    return {
        'id': f'task_{t.id}',
        'name': t.title or '',
        'nodeType': 'task',
        'extra': {
            'status': t.status or '',
            'assignee': assignee_name,
            'dueDate': due_str,
            'createdAt': created_str,
            'desc': desc,
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
