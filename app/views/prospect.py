from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from flask_babel import gettext as _
from app import db
from app.models.prospect_project import ProspectProject, ProspectStakeholder, PROSPECT_STAGES, STAKEHOLDER_TYPES
from app.models.customer import Company, Contact
from app.models.project import Project
from app.models.user import User
from app.permissions import admin_required, permission_required, is_admin_or_ceo
from app.utils.dictionary_helpers import get_industry_options
from sqlalchemy import or_, func
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

prospect_bp = Blueprint('prospect', __name__)


@prospect_bp.route('/')
@login_required
@permission_required('project', 'view')
def list_view():
    """市场情报库列表（默认）+ 流失项目 tab。

    通过 ?tab=lost 路由到流失项目子视图；其余 tab 值（含缺省）走原情报列表。
    """
    tab = request.args.get('tab', 'intel')
    if tab == 'lost':
        return _list_lost_projects()
    return _list_intel()


def _list_intel():
    """市场情报列表 — 仅展示 link_type='converted' 的潜在项目记录。"""
    search  = request.args.get('search', '').strip()
    industry = request.args.get('industry', '')
    region  = request.args.get('region', '')
    stage   = request.args.get('stage', '')
    claimed = request.args.get('claimed', '')   # '' / 'unclaimed' / 'mine' / 'claimed'
    sort    = request.args.get('sort', 'updated_desc')
    sort_col = request.args.get('sort_col', '')
    sort_order_dir = request.args.get('order', 'desc')

    query = ProspectProject.query.filter(
        ProspectProject.is_deleted == False,
        ProspectProject.link_type == 'converted',
    )

    if search:
        query = query.filter(
            or_(
                ProspectProject.project_name.ilike(f'%{search}%'),
                ProspectProject.city.ilike(f'%{search}%'),
                ProspectProject.region.ilike(f'%{search}%'),
                ProspectProject.description.ilike(f'%{search}%'),
            )
        )
    if industry:
        query = query.filter(ProspectProject.industry == industry)
    if region:
        query = query.filter(ProspectProject.region.ilike(f'%{region}%'))
    if stage:
        query = query.filter(ProspectProject.stage == stage)

    if claimed == 'unclaimed':
        query = query.filter(ProspectProject.claimed_by_id == None)
    elif claimed == 'mine':
        query = query.filter(ProspectProject.claimed_by_id == current_user.id)
    elif claimed == 'claimed':
        query = query.filter(ProspectProject.claimed_by_id != None)

    # 排序：表头点击（sort_col+order）优先于下拉（sort）
    _col_map = {
        'project_name':    ProspectProject.project_name,
        'industry':        ProspectProject.industry,
        'region':          ProspectProject.region,
        'total_investment':ProspectProject.total_investment,
        'info_updated_at': ProspectProject.info_updated_at,
    }
    if sort_col and sort_col in _col_map:
        col = _col_map[sort_col]
        if sort_order_dir == 'asc':
            query = query.order_by(col.asc().nullslast())
        else:
            query = query.order_by(col.desc().nullslast())
    elif sort_col == 'stage':
        stage_order = func.case(
            (ProspectProject.stage == 'construction', 1),
            (ProspectProject.stage == 'designing', 2),
            (ProspectProject.stage == 'planning', 3),
            (ProspectProject.stage == 'completed', 4),
            else_=5
        )
        query = query.order_by(stage_order if sort_order_dir == 'asc' else stage_order.desc())
    elif sort == 'updated_asc':
        query = query.order_by(ProspectProject.info_updated_at.asc().nullslast())
    elif sort == 'stage_hot':
        stage_order = func.case(
            (ProspectProject.stage == 'construction', 1),
            (ProspectProject.stage == 'designing', 2),
            (ProspectProject.stage == 'planning', 3),
            (ProspectProject.stage == 'completed', 4),
            else_=5
        )
        query = query.order_by(stage_order)
    elif sort == 'created_desc':
        query = query.order_by(ProspectProject.created_at.desc())
    else:  # updated_desc (default)
        query = query.order_by(ProspectProject.info_updated_at.desc().nullslast(),
                               ProspectProject.created_at.desc())

    projects = query.all()

    # 统计各阶段数量（全量，不受筛选影响）
    stage_counts = {}
    for stg in ('planning', 'designing', 'construction', 'completed'):
        stage_counts[stg] = ProspectProject.query.filter(
            ProspectProject.is_deleted == False,
            ProspectProject.stage == stg
        ).count()

    total_count = ProspectProject.query.filter(ProspectProject.is_deleted == False).count()

    # 地区选项（去重）
    regions = [r[0] for r in db.session.query(ProspectProject.region)
               .filter(ProspectProject.is_deleted == False, ProspectProject.region != None)
               .distinct().order_by(ProspectProject.region).all()]

    return render_template(
        'prospect/tw_list.html',
        tab='intel',
        projects=projects,
        total_count=total_count,
        stage_counts=stage_counts,
        regions=regions,
        industry_labels=get_industry_options(),
        search=search,
        industry=industry,
        region=region,
        sort_col=sort_col,
        sort_order_dir=sort_order_dir,
        stage=stage,
        claimed=claimed,
        sort=sort,
    )


# ─── 流失项目 tab ──────────────────────────────────────────────

def _list_lost_projects():
    """渲染流失项目列表（activity_status='churned' 且当前阶段未冻结）。"""
    from app.utils.activity_tracker import FROZEN_STAGES

    region   = (request.args.get('region') or '').strip()
    industry = (request.args.get('industry') or '').strip()
    stage    = (request.args.get('stage') or '').strip()

    q = Project.query.filter(
        Project.is_deleted == False,
        Project.activity_status == 'churned',
        ~Project.current_stage.in_(FROZEN_STAGES),
    )
    if region:
        q = q.filter(Project.region.ilike(f'%{region}%'))
    if industry == '__none__':
        q = q.filter((Project.industry.is_(None)) | (Project.industry == ''))
    elif industry:
        q = q.filter(Project.industry == industry)
    if stage:
        q = q.filter(Project.current_stage == stage)

    projects = q.order_by(Project.last_activity_date.desc().nullslast()).all()

    # 附加 _research（link_type='research' 的 ProspectProject 记录）以便模板内联展示
    if projects:
        ids = [p.id for p in projects]
        research_records = ProspectProject.query.filter(
            ProspectProject.link_type == 'research',
            ProspectProject.converted_project_id.in_(ids),
        ).all()
        research_map = {r.converted_project_id: r for r in research_records}
        for p in projects:
            p._research = research_map.get(p.id)

    # 地区下拉：从流失项目集合中聚合
    lost_regions = sorted({(p.region or '').strip() for p in projects if (p.region or '').strip()})

    return render_template(
        'prospect/tw_list.html',
        tab='lost',
        lost_projects=projects,
        # 兼容现有 tw_list.html 共用部分（Phase 4 会替换为 lost-tab UI）
        projects=[],
        total_count=len(projects),
        stage_counts={},
        regions=lost_regions,
        industry_labels=get_industry_options(),
        search='',
        industry=industry,
        region=region,
        sort_col='',
        sort_order_dir='desc',
        stage=stage,
        claimed='',
        sort='',
    )


# ─── 流失项目 详情 / 申请参与 / AI 调研 ────────────────────────

def _can_see_lost_sensitive(user, project):
    """是否可以查看流失项目中的敏感联系人/报价/跟进信息。

    复用项目级权限阶梯（拥有人 / 共享 / 部门管理 / 管理员）。
    """
    from app.utils.access_control import can_view_project
    return can_view_project(user, project)


@prospect_bp.route('/lost/<int:project_id>')
@login_required
@permission_required('project', 'view')
def lost_detail(project_id):
    """流失项目公开详情页（Phase 4 提供模板，Phase 3 仅落路由）。"""
    from app.models.prospect_claim_request import ProspectClaimRequest
    from app.utils.activity_tracker import FROZEN_STAGES

    project = Project.query.filter_by(id=project_id, is_deleted=False).first_or_404()

    if (project.activity_status != 'churned'
            or project.current_stage in FROZEN_STAGES):
        flash('该项目当前不属于流失项目', 'warning')
        return redirect(url_for('prospect.list_view', tab='lost'))

    research = ProspectProject.query.filter_by(
        converted_project_id=project.id,
        link_type='research',
    ).first()

    can_view_sensitive = _can_see_lost_sensitive(current_user, project)
    has_applied = ProspectClaimRequest.query.filter_by(
        project_id=project.id,
        applicant_id=current_user.id,
    ).first() is not None

    return render_template(
        'prospect/tw_lost_detail.html',
        project=project,
        research=research,
        can_view_sensitive=can_view_sensitive,
        has_applied=has_applied,
    )


@prospect_bp.route('/lost/<int:project_id>/apply', methods=['POST'])
@login_required
@permission_required('project', 'view')
def lost_apply(project_id):
    """申请参与流失项目：创建 ProspectClaimRequest + 通知项目原负责人/管理员。"""
    from app.models.prospect_claim_request import ProspectClaimRequest
    from app.models.message import Message
    from app.utils.activity_tracker import FROZEN_STAGES
    from app.utils.access_control import can_view_project

    project = Project.query.filter_by(id=project_id, is_deleted=False).first_or_404()

    if project.activity_status != 'churned' or project.current_stage in FROZEN_STAGES:
        return jsonify(success=False, message='项目不在流失状态'), 400

    if can_view_project(current_user, project):
        return jsonify(success=False, message='您已拥有此项目权限，无需申请'), 400

    payload = request.get_json(silent=True) or request.form
    reason = (payload.get('reason') or '').strip()
    if len(reason) < 10:
        return jsonify(success=False, message='申请理由至少 10 个字'), 400
    if len(reason) > 500:
        return jsonify(success=False, message='申请理由不超过 500 字'), 400

    existing = ProspectClaimRequest.query.filter_by(
        project_id=project.id, applicant_id=current_user.id
    ).first()
    if existing:
        return jsonify(success=False, message='您已申请过此项目，等待负责人处理'), 409

    cr = ProspectClaimRequest(
        project_id=project.id,
        applicant_id=current_user.id,
        reason=reason,
    )
    db.session.add(cr)
    db.session.flush()

    # 接收人：优先项目负责人；若无负责人则发给所有 admin（启用账号）
    if project.owner_id:
        recipient_ids = [project.owner_id]
    else:
        admins = User.query.filter(
            User.role == 'admin',
            User._is_active == True,
        ).all()
        recipient_ids = [u.id for u in admins]

    applicant_name = current_user.real_name or current_user.username
    title = f'{applicant_name} 申请参与流失项目《{project.project_name}》'

    for rid in recipient_ids:
        msg = Message(
            recipient_id=rid,
            sender_id=current_user.id,
            message_type='prospect_claim_request',
            title=title,
            content=reason,
            related_object_type='project',
            related_object_id=project.id,
            extra_data={'claim_request_id': cr.id},
        )
        db.session.add(msg)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(success=False, message='您已申请过此项目，等待负责人处理'), 409

    return jsonify(success=True, message='申请已提交，等待负责人处理')


@prospect_bp.route('/lost/<int:project_id>/ai-research', methods=['POST'])
@login_required
@permission_required('project', 'view')
def lost_ai_research(project_id):
    """触发流失项目的 AI 调研（同步）。

    AI 调研结果只写入 prospect_projects（link_type='research'）+
    prospect_stakeholders 两张表，**不会**回写到 projects.ai_research_data，
    以保持"AI 可以补全，但不会同步回项目"的设计意图。
    """
    from app.utils.access_control import can_view_project
    from app.services.claude_research_provider import send_claude_research_request
    import json
    import re

    project = Project.query.filter_by(id=project_id, is_deleted=False).first_or_404()

    if not can_view_project(current_user, project):
        return jsonify(success=False, message='无权限触发 AI 调研'), 403

    research = ProspectProject.query.filter_by(
        converted_project_id=project.id,
        link_type='research',
    ).first()

    if not research:
        research = ProspectProject(
            project_name=project.project_name,
            industry=project.industry,
            region=project.region,
            stage='planning',
            converted_project_id=project.id,
            link_type='research',
            source='ai',
        )
        db.session.add(research)
        db.session.flush()

    prompt = (
        f"请对以下项目做调研，输出严格 JSON：\n\n"
        f"项目名称：{project.project_name}\n"
        f"行业：{project.industry or '未知'}\n"
        f"地区：{project.region or '未知'}\n"
        f"投资规模：{project.total_investment or '未知'}\n\n"
        "请输出如下 JSON 结构：\n"
        "{\n"
        '  "description": "项目详细描述（2~5 句）",\n'
        '  "progress": "项目最新进展（1~3 句，可包含日期）",\n'
        '  "stakeholders": [\n'
        '    {\n'
        '      "stakeholder_type": "owner|design|epc|construction|other",\n'
        '      "company_name": "公司全称",\n'
        '      "department": "部门/null",\n'
        '      "address": "公司地址/null",\n'
        '      "phone": "电话/null",\n'
        '      "contact_person": "联系人/null",\n'
        '      "email": "邮箱/null",\n'
        '      "website": "官网/null",\n'
        '      "business_scope": "业务范围/null",\n'
        '      "notes": "其他/null"\n'
        '    }\n'
        "  ]\n"
        "}\n\n"
        "找不到的字段设为 null。stakeholder_type 必须是上述五种枚举之一。"
    )

    try:
        raw = send_claude_research_request(prompt, timeout=180)

        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if not m:
            return jsonify(success=False, message='AI 未返回有效结果'), 500

        data = json.loads(m.group())

        # 更新调研记录主字段
        desc = data.get('description')
        if isinstance(desc, str) and desc.strip():
            research.description = desc.strip()
        prog = data.get('progress')
        if isinstance(prog, str) and prog.strip():
            research.progress = prog.strip()
        research.info_updated_at = datetime.utcnow()
        research.info_updated_by = current_user.username

        # 替换利益相关方
        ProspectStakeholder.query.filter_by(prospect_id=research.id).delete(
            synchronize_session=False
        )

        valid_types = set(STAKEHOLDER_TYPES.keys())
        stakeholders_payload = data.get('stakeholders') or []
        if not isinstance(stakeholders_payload, list):
            stakeholders_payload = []

        def _clean(v):
            """把 None / 'null' / 空串统一成 None；列表压平为换行字符串。"""
            if v is None:
                return None
            if isinstance(v, list):
                joined = '\n'.join(str(x).strip() for x in v if x)
                return joined or None
            s = str(v).strip()
            if not s or s.lower() in ('null', 'none'):
                return None
            return s

        added = 0
        for entry in stakeholders_payload:
            if not isinstance(entry, dict):
                continue
            company_name = _clean(entry.get('company_name'))
            if not company_name:
                continue
            stype = (entry.get('stakeholder_type') or 'other').strip().lower()
            if stype not in valid_types:
                stype = 'other'
            sk = ProspectStakeholder(
                prospect_id=research.id,
                stakeholder_type=stype,
                company_name=company_name[:200],
                department=_clean(entry.get('department')),
                address=_clean(entry.get('address')),
                phone=_clean(entry.get('phone')),
                contact_person=_clean(entry.get('contact_person')),
                email=_clean(entry.get('email')),
                website=_clean(entry.get('website')),
                business_scope=_clean(entry.get('business_scope')),
                notes=_clean(entry.get('notes')),
            )
            db.session.add(sk)
            added += 1

        db.session.commit()
        return jsonify(success=True, message='AI 调研完成', stakeholders_count=added)
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Lost-project AI research failed")
        return jsonify(success=False, message=f'调研失败：{str(e)[:200]}'), 500


@prospect_bp.route('/<int:id>/panel')
@login_required
@permission_required('project', 'view')
def detail_panel(id):
    """返回 JSON，供列表页 modal 通过 fetch 注入"""
    p = ProspectProject.query.filter_by(id=id, is_deleted=False).first_or_404()

    panel_tmpl = current_app.jinja_env.get_template('prospect/tw_panel.html')
    stage_badge_html    = panel_tmpl.module.render_stage_badge(p.stage)
    body_html           = panel_tmpl.module.render_body(p)
    footer_left_html    = panel_tmpl.module.render_footer_left(p, current_user)
    footer_actions_html = panel_tmpl.module.render_footer_actions(p, current_user)

    return jsonify({
        'project_name':        p.project_name,
        'city':                p.city or '',
        'region':              p.region or '',
        'stage_badge_html':    stage_badge_html,
        'body_html':           body_html,
        'footer_left_html':    footer_left_html,
        'footer_actions_html': footer_actions_html,
    })


@prospect_bp.route('/<int:id>/claim', methods=['POST'])
@login_required
@permission_required('project', 'view')
def claim(id):
    p = ProspectProject.query.filter_by(id=id, is_deleted=False).first_or_404()
    if p.is_claimed and not is_admin_or_ceo():
        return jsonify({'success': False, 'message': '该项目已被申领'}), 400
    p.claimed_by_id = current_user.id
    p.claimed_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True, 'claimed_by': current_user.real_name or current_user.username})


@prospect_bp.route('/<int:id>/unclaim', methods=['POST'])
@login_required
@permission_required('project', 'view')
def unclaim(id):
    p = ProspectProject.query.filter_by(id=id, is_deleted=False).first_or_404()
    # 申领人自己可取消，管理员也可取消
    if p.claimed_by_id != current_user.id and not is_admin_or_ceo():
        return jsonify({'success': False, 'message': '无权操作'}), 403
    p.claimed_by_id = None
    p.claimed_at = None
    db.session.commit()
    return jsonify({'success': True})


@prospect_bp.route('/<int:id>/check-import')
@login_required
@permission_required('project', 'view')
def check_import(id):
    import difflib, re

    def _strip_suffix(name):
        return re.sub(r'(有限公司|股份有限公司|集团|分公司|工程公司|设计院|研究院|工程设计|工程咨询)$', '', name).strip()

    def _similarity(a, b):
        return int(difflib.SequenceMatcher(None, _strip_suffix(a), _strip_suffix(b)).ratio() * 100)

    p = ProspectProject.query.filter_by(id=id, is_deleted=False).first_or_404()
    all_companies = Company.query.filter_by(is_deleted=False).all()

    result = []
    for s in p.stakeholders.all():
        item = {
            'id': s.id,
            'company_name': s.company_name,
            'stakeholder_type': s.stakeholder_type,
            'department': s.department or '',
            'contact_person': s.contact_person or '',
            'phone': s.phone or '',
            'address': s.address or '',
            'notes': s.notes or '',
        }

        # 公司查重
        exact = next((c for c in all_companies if c.company_name == s.company_name), None)
        if exact:
            item['company_status'] = 'exact'
            item['similar_companies'] = [{'id': exact.id, 'name': exact.company_name, 'score': 100}]
        else:
            similar = sorted(
                [{'id': c.id, 'name': c.company_name, 'score': _similarity(c.company_name, s.company_name)}
                 for c in all_companies if _similarity(c.company_name, s.company_name) >= 70],
                key=lambda x: -x['score']
            )
            item['company_status'] = 'similar' if similar else 'new'
            item['similar_companies'] = similar[:3]

        # 联系人查重
        item['contact_status'] = 'none'
        item['duplicate_contact'] = None
        if s.contact_person:
            dup_name = Contact.query.filter_by(name=s.contact_person).first()
            dup_phone = Contact.query.filter_by(phone=s.phone).first() if s.phone else None
            if dup_name:
                item['contact_status'] = 'duplicate_name'
                item['duplicate_contact'] = {
                    'id': dup_name.id, 'name': dup_name.name,
                    'phone': dup_name.phone or '',
                    'company_name': dup_name.company.company_name if dup_name.company else ''
                }
            elif dup_phone:
                item['contact_status'] = 'duplicate_phone'
                item['duplicate_contact'] = {
                    'id': dup_phone.id, 'name': dup_phone.name,
                    'phone': dup_phone.phone or '',
                    'company_name': dup_phone.company.company_name if dup_phone.company else ''
                }
            else:
                item['contact_status'] = 'new'

        result.append(item)

    return jsonify({'stakeholders': result})


@prospect_bp.route('/<int:id>/import-stakeholders', methods=['POST'])
@login_required
@permission_required('project', 'view')
def import_stakeholders(id):
    import random, string

    def _gen_company_code():
        while True:
            code = 'C' + ''.join(random.choices(string.digits, k=6))
            if not Company.query.filter_by(company_code=code).first():
                return code

    p = ProspectProject.query.filter_by(id=id, is_deleted=False).first_or_404()
    if p.claimed_by_id != current_user.id and not is_admin_or_ceo():
        return jsonify({'success': False, 'message': '只有申领人才能导入'}), 403

    items = request.json.get('items', [])
    summary = {'created_companies': 0, 'merged_companies': 0, 'created_contacts': 0, 'skipped': 0}

    type_map = {
        'owner': '用户', 'design': '设计院及顾问',
        'epc': '总承包单位', 'construction': '总承包单位', 'other': '用户'
    }

    for item in items:
        if item.get('skip'):
            summary['skipped'] += 1
            continue

        s = ProspectStakeholder.query.filter_by(id=item['stakeholder_id'], prospect_id=id).first()
        if not s:
            continue

        if item.get('company_action') == 'merge':
            company = Company.query.get(item['merge_company_id'])
            summary['merged_companies'] += 1
        else:
            company = Company(
                company_code=_gen_company_code(),
                company_name=s.company_name,
                address=s.address,
                industry=p.industry,
                company_type=type_map.get(s.stakeholder_type, '用户'),
                source='销售线索',
                owner_id=current_user.id,
            )
            db.session.add(company)
            db.session.flush()
            summary['created_companies'] += 1

        if s.contact_person and item.get('contact_action') == 'create':
            contact = Contact(
                company_id=company.id,
                name=s.contact_person,
                department=s.department,
                phone=s.phone,
            )
            db.session.add(contact)
            summary['created_contacts'] += 1

    db.session.commit()
    return jsonify({'success': True, 'summary': summary})


# ─── AI 调研 ──────────────────────────────────────────────────

@prospect_bp.route('/<int:id>/stakeholder/<int:sid>/ai-enrich', methods=['POST'])
@login_required
@permission_required('project', 'view')
def stakeholder_ai_enrich(id, sid):
    p = ProspectProject.query.filter_by(id=id, is_deleted=False).first_or_404()
    s = ProspectStakeholder.query.filter_by(id=sid, prospect_id=id).first_or_404()

    type_names = {
        'owner': '业主/建设单位', 'design': '设计院/工程咨询',
        'epc': 'EPC总承包商', 'construction': '施工单位', 'other': '相关单位'
    }
    type_name = type_names.get(s.stakeholder_type, '相关单位')

    ctx = [f"项目名称：{p.project_name}"]
    if p.city or p.region:
        ctx.append(f"项目位置：{' '.join(filter(None, [p.city, p.region]))}")
    if p.industry:
        ctx.append(f"项目行业：{p.industry}")

    known = []
    if s.department:
        known.append(f"已知部门：{s.department}")
    if s.contact_person:
        known.append(f"已知联系人：{s.contact_person}")
    if s.phone:
        known.append(f"已知电话：{s.phone}")

    prompt = (
        "你是商务情报调研助手。请通过网络搜索，调研下列企业的结构化联系信息，用于商业拜访。\n\n"
        "背景：\n" + "\n".join(ctx) + "\n\n"
        f"调研对象：{s.company_name}（角色：{type_name}）\n"
        + ("\n".join(known) + "\n" if known else "")
        + "\n请搜索官网、招聘平台、企查查、招标公告等，尽量找出：\n"
        "1. 关键对口部门及负责人（招标/采购/技术/项目/电信仪表 等），"
           "如果存在多个部门联系人，全部返回\n"
        "2. 企业主地址 + 备选地址（官网登记 vs 工商登记可能不同，都要列出）\n"
        "3. 官网 URL、对外邮箱（招聘/招标）、主营业务范围\n\n"
        "返回严格 JSON，不含其他文字，结构如下：\n"
        '{\n'
        '  "primary": {\n'
        '    "department": "对口部门名(选最相关的一个)",\n'
        '    "contact_person": "姓名(可附职位)",\n'
        '    "phone": "电话",\n'
        '    "email": "邮箱",\n'
        '    "address": "最权威的主地址",\n'
        '    "alternative_addresses": ["备选地址1", "备选地址2"],\n'
        '    "website": "官网URL",\n'
        '    "business_scope": "主营业务/营业范围",\n'
        '    "notes": "其他补充信息(招标平台/招聘邮箱/总机等)"\n'
        '  },\n'
        '  "additional_contacts": [\n'
        '    {"department":"另一个部门","contact_person":"姓名","phone":"...","email":"...","role_description":"职责说明"}\n'
        '  ],\n'
        '  "confidence": "high|medium|low",\n'
        '  "sources": ["来源URL或平台"]\n'
        '}\n'
        '说明：找不到的字段设为 null（数组找不到设为空数组 []）。'
        'additional_contacts 仅放与 primary 不同部门/不同人的联系人，避免重复。'
    )

    try:
        from app.services.claude_research_provider import send_claude_research_request
        import json, re

        raw = send_claude_research_request(prompt, timeout=120)

        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if not m:
            return jsonify({'success': False, 'message': 'AI未返回有效结果'}), 500

        sug = json.loads(m.group())
        primary = sug.get('primary') or {}

        # 兼容旧 prompt 形态：如果没有 primary 包装，把顶层视作 primary
        if not primary and any(k in sug for k in ('contact_person', 'phone', 'address')):
            primary = {k: sug.get(k) for k in (
                'contact_person', 'phone', 'address', 'notes',
                'email', 'website', 'business_scope', 'department',
            ) if sug.get(k)}
            alt = sug.get('alternative_addresses')
            if alt:
                primary['alternative_addresses'] = alt

        # primary 字段对照现有值
        existing = {
            'department':            s.department or '',
            'contact_person':        s.contact_person or '',
            'phone':                 s.phone or '',
            'email':                 s.email or '',
            'address':               s.address or '',
            'alternative_addresses': s.alternative_addresses or '',
            'website':               s.website or '',
            'business_scope':        s.business_scope or '',
            'notes':                 s.notes or '',
        }

        fields = {}
        for field in existing.keys():
            val = primary.get(field)
            # alternative_addresses 是数组，转成换行字符串
            if field == 'alternative_addresses' and isinstance(val, list):
                val = '\n'.join(str(x).strip() for x in val if x)
            if val and str(val).strip().lower() not in ('', 'null', 'none'):
                fields[field] = {
                    'suggested': str(val).strip(),
                    'existing':  existing[field],
                    'is_new':    not existing[field],
                }

        # 过滤 additional_contacts：去掉空记录和与 primary 重复的
        primary_person = (primary.get('contact_person') or '').strip()
        additional = []
        for item in (sug.get('additional_contacts') or []):
            if not isinstance(item, dict):
                continue
            person = (item.get('contact_person') or '').strip()
            phone  = (item.get('phone') or '').strip()
            dept   = (item.get('department') or '').strip()
            if not (person or phone or dept):
                continue
            if person and person == primary_person:
                continue
            additional.append({
                'department':       dept,
                'contact_person':   person,
                'phone':            phone,
                'email':            (item.get('email') or '').strip(),
                'role_description': (item.get('role_description') or '').strip(),
            })

        return jsonify({
            'success':        True,
            'stakeholder_id': sid,
            'company_name':   s.company_name,
            'fields':         fields,
            'additional':     additional,
            'confidence':     sug.get('confidence', 'medium'),
            'sources':        sug.get('sources', []),
        })

    except Exception as e:
        logger.error(f"AI enrich stakeholder {sid}: {e}")
        return jsonify({'success': False, 'message': f'调研失败：{e}'}), 500


@prospect_bp.route('/<int:id>/stakeholder/<int:sid>/update-fields', methods=['POST'])
@login_required
@permission_required('project', 'view')
def stakeholder_update_fields(id, sid):
    p = ProspectProject.query.filter_by(id=id, is_deleted=False).first_or_404()
    s = ProspectStakeholder.query.filter_by(id=sid, prospect_id=id).first_or_404()

    data    = request.json or {}
    fields  = data.get('fields', {})
    additional = data.get('additional_contacts', []) or []
    allowed = {
        'department', 'contact_person', 'phone', 'email',
        'address', 'alternative_addresses', 'website',
        'business_scope', 'notes',
    }
    updated = []

    for field, value in fields.items():
        if field in allowed:
            setattr(s, field, str(value).strip() if value else None)
            updated.append(field)

    # 为每个被勾选的 additional contact 创建一个新的 ProspectStakeholder 行
    # 同 prospect_id、同 company_name、同 stakeholder_type，department/contact_person 区分
    created_ids = []
    for item in additional:
        if not isinstance(item, dict):
            continue
        person = (item.get('contact_person') or '').strip()
        phone  = (item.get('phone') or '').strip()
        dept   = (item.get('department') or '').strip()
        if not (person or phone or dept):
            continue
        new_row = ProspectStakeholder(
            prospect_id=p.id,
            stakeholder_type=s.stakeholder_type,
            company_name=s.company_name,
            department=dept or None,
            contact_person=person or None,
            phone=phone or None,
            email=(item.get('email') or '').strip() or None,
            notes=(item.get('role_description') or '').strip() or None,
        )
        db.session.add(new_row)
        db.session.flush()
        created_ids.append(new_row.id)

    if updated or created_ids:
        p.info_updated_at = datetime.utcnow()
        p.info_updated_by = f'AI调研 ({current_user.real_name or current_user.username})'
        db.session.commit()

    return jsonify({
        'success': True,
        'updated': updated,
        'created_ids': created_ids,
    })


# ─── 管理员 CRUD ───────────────────────────────────────────────

@prospect_bp.route('/admin/new', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_new():
    if request.method == 'POST':
        return _save_prospect(None)
    return render_template('prospect/admin_form.html',
                           prospect=None,
                           stakeholders=[],
                           stage_options=PROSPECT_STAGES,
                           stakeholder_types=STAKEHOLDER_TYPES,
                           industry_options=get_industry_options())


@prospect_bp.route('/admin/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit(id):
    p = ProspectProject.query.filter_by(id=id, is_deleted=False).first_or_404()
    if request.method == 'POST':
        return _save_prospect(p)
    return render_template('prospect/admin_form.html',
                           prospect=p,
                           stakeholders=p.stakeholders.all(),
                           stage_options=PROSPECT_STAGES,
                           stakeholder_types=STAKEHOLDER_TYPES,
                           industry_options=get_industry_options())


@prospect_bp.route('/admin/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete(id):
    p = ProspectProject.query.filter_by(id=id, is_deleted=False).first_or_404()
    p.is_deleted = True
    db.session.commit()
    flash('潜在项目已删除', 'success')
    return redirect(url_for('prospect.list_view'))


@prospect_bp.route('/admin/<int:id>/stakeholder/add', methods=['POST'])
@login_required
@admin_required
def admin_add_stakeholder(id):
    p = ProspectProject.query.filter_by(id=id, is_deleted=False).first_or_404()
    data = request.json or {}
    s = ProspectStakeholder(
        prospect_id=id,
        stakeholder_type=data.get('stakeholder_type', 'other'),
        company_name=data.get('company_name', ''),
        department=data.get('department', ''),
        address=data.get('address', ''),
        phone=data.get('phone', ''),
        contact_person=data.get('contact_person', ''),
        notes=data.get('notes', ''),
    )
    db.session.add(s)
    p.info_updated_at = datetime.utcnow()
    p.info_updated_by = '人工更新'
    db.session.commit()
    return jsonify({'success': True, 'id': s.id})


@prospect_bp.route('/admin/stakeholder/<int:sid>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_stakeholder(sid):
    s = ProspectStakeholder.query.get_or_404(sid)
    db.session.delete(s)
    db.session.commit()
    return jsonify({'success': True})


def _save_prospect(prospect):
    data = request.form
    is_new = prospect is None
    if is_new:
        prospect = ProspectProject()

    prospect.project_name    = data.get('project_name', '').strip()
    prospect.industry        = data.get('industry') or None
    prospect.region          = data.get('region', '').strip() or None
    prospect.city            = data.get('city', '').strip() or None
    prospect.stage           = data.get('stage', 'planning')
    prospect.total_investment = data.get('total_investment', '').strip() or None
    prospect.description     = data.get('description', '').strip() or None
    prospect.source          = data.get('source') or None
    prospect.info_updated_at = datetime.utcnow()
    prospect.info_updated_by = '人工更新'

    kw_raw = data.get('keywords', '').strip()
    prospect.keywords = [k.strip() for k in kw_raw.split(',') if k.strip()] if kw_raw else []

    if is_new:
        db.session.add(prospect)

    db.session.commit()
    flash('保存成功', 'success')
    return redirect(url_for('prospect.admin_edit', id=prospect.id))
