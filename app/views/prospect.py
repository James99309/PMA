from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from flask_babel import gettext as _
from app import db
from app.models.prospect_project import ProspectProject, ProspectStakeholder, ProspectResearchLog, PROSPECT_STAGES, STAKEHOLDER_TYPES
from app.models.customer import Company, Contact
from app.models.project import Project
from app.models.user import User
from app.permissions import admin_required, permission_required, is_admin_or_ceo
from app.utils.dictionary_helpers import get_industry_options
from sqlalchemy import or_, func
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import threading
import logging

logger = logging.getLogger(__name__)

# 全局并发限制：最多 2 个 AI 调研任务同时运行（适配单 worker Gunicorn）
_research_semaphore = threading.Semaphore(2)
_BATCH_DAILY_QUOTA = 3   # 非管理员每天批量调研最多 3 次
_STALE_MINUTES = 30      # running 超过此时长视为僵尸，标记 failed


def _recover_stale_logs():
    """将超过 30 分钟仍 running 的日志标记为 failed（崩溃恢复）。"""
    cutoff = datetime.utcnow() - timedelta(minutes=_STALE_MINUTES)
    stale = ProspectResearchLog.query.filter(
        ProspectResearchLog.status == 'running',
        ProspectResearchLog.created_at < cutoff,
    ).all()
    for log in stale:
        log.status = 'failed'
        log.completed_at = datetime.utcnow()
    if stale:
        db.session.commit()


def _batch_quota_remaining(user_id):
    """返回今日剩余批量调研次数（UTC 日期）。"""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    used = ProspectResearchLog.query.filter(
        ProspectResearchLog.user_id == user_id,
        ProspectResearchLog.job_type == 'batch',
        ProspectResearchLog.created_at >= today_start,
    ).count()
    return max(0, _BATCH_DAILY_QUOTA - used)


def _log_research(user_id, job_type):
    """插入 running 日志，返回记录对象（调用方负责在结束后更新状态）。"""
    log = ProspectResearchLog(user_id=user_id, job_type=job_type, status='running')
    db.session.add(log)
    db.session.commit()
    return log


def _finish_log(log, success):
    log.status = 'done' if success else 'failed'
    log.completed_at = datetime.utcnow()
    db.session.commit()

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
        if current_user.role != 'admin':
            return redirect(url_for('prospect.list_view'))
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

    _base = ProspectProject.query.filter(
        ProspectProject.is_deleted == False,
        ProspectProject.link_type == 'converted',
    )

    # 动态行业选项：从库中实际存在的行业值构建（映射到中文标签）
    _industry_label_map = dict(get_industry_options())
    _raw_industries = [r[0] for r in _base.filter(ProspectProject.industry != None)
                       .with_entities(ProspectProject.industry).distinct()
                       .order_by(ProspectProject.industry).all()]
    industry_options = [(v, _industry_label_map.get(v, v)) for v in _raw_industries]

    # 动态地区选项
    regions = [r[0] for r in _base.filter(ProspectProject.region != None)
               .with_entities(ProspectProject.region).distinct()
               .order_by(ProspectProject.region).all()]

    # 动态阶段选项（保持固定顺序但仅显示库中存在的）
    _stage_order = ['construction', 'designing', 'planning', 'completed']
    _stage_labels = {'construction': '在建', 'designing': '设计中', 'planning': '规划中', 'completed': '竣工'}
    _existing_stages = {r[0] for r in _base.filter(ProspectProject.stage != None)
                        .with_entities(ProspectProject.stage).distinct().all()}
    stage_options = [(s, _stage_labels[s]) for s in _stage_order if s in _existing_stages]

    return render_template(
        'prospect/tw_list.html',
        tab='intel',
        projects=projects,
        total_count=total_count,
        stage_counts=stage_counts,
        regions=regions,
        industry_options=industry_options,
        industry_label_map=_industry_label_map,
        stage_options=stage_options,
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

        # 预加载所有 research 记录的 stakeholders，避免模板里 lazy='dynamic' N+1 查询
        if research_map:
            research_ids = [r.id for r in research_map.values()]
            stakeholders_map = {}
            for s in ProspectStakeholder.query.filter(
                ProspectStakeholder.prospect_id.in_(research_ids)
            ).all():
                stakeholders_map.setdefault(s.prospect_id, []).append(s)
            for r in research_map.values():
                r._stakeholder_list = stakeholders_map.get(r.id, [])

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
        industry_options=list(get_industry_options()),
        industry_label_map=dict(get_industry_options()),
        stage_options=[],
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
        flash('该项目当前不在公共项目池', 'warning')
        return redirect(url_for('prospect.list_view', tab='lost'))

    research = ProspectProject.query.filter_by(
        converted_project_id=project.id,
        link_type='research',
    ).first()

    can_view_sensitive = is_admin_or_ceo() or (project.owner_id == current_user.id)
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
    title = f'{applicant_name} 申请参与公共项目《{project.project_name}》'

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
    from app.services.claude_research_provider import send_claude_research_request
    from config import Config
    import json
    import re

    project = Project.query.filter_by(id=project_id, is_deleted=False).first_or_404()
    is_ovs = bool(Config.IS_OVS)

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

    if is_ovs:
        prompt = (
            f"⚠️ LANGUAGE RULE (MANDATORY): Your entire JSON output MUST be in English only. "
            f"Do NOT use Chinese or any other non-English language.\n\n"
            f"Research the following project and output strict JSON.\n\n"
            f"Project name: {project.project_name}\n"
            f"Industry: {project.industry or 'unknown'}\n"
            f"Region: {project.region or 'unknown'}\n"
            f"Stage: {project.current_stage or 'unknown'}\n\n"
            f"Search strategy:\n"
            f'1. Search "[project name] developer owner" to find the client/owner.\n'
            f'2. Search "[project name] main contractor awarded" to find the general contractor.\n'
            f'3. Search "[project name] M&E consultant ELV security consultant" to find MEP/security consultants.\n'
            f'4. Search "[project name] ELV integrator security system integrator ICT" to find system integrators.\n'
            f'5. Search "[project name] latest news update" for progress.\n\n'
            "Output the following JSON structure (English only):\n"
            "{\n"
            '  "description": "2-5 sentence project overview — English only",\n'
            '  "progress": "Latest milestone with date (1-3 sentences) — English only — or null",\n'
            '  "stakeholders": [\n'
            '    {\n'
            '      "stakeholder_type": "owner|consultant|design|main_contractor|system_integrator|epc|other",\n'
            '      "company_name": "full registered company name in English",\n'
            '      "department": "department name in English or null",\n'
            '      "address": "address or null",\n'
            '      "phone": "phone or null",\n'
            '      "contact_person": "contact name (romanised) or null",\n'
            '      "email": "email or null",\n'
            '      "website": "official site or null",\n'
            '      "business_scope": "business scope in English or null",\n'
            '      "notes": "notes in English or null"\n'
            '    }\n'
            "  ]\n"
            "}\n\n"
            "Stakeholder type guide (choose the MOST SPECIFIC type):\n"
            "- owner:            Developer / Owner / Client / Employer\n"
            "- consultant:       MEP / ELV / Security / ICT consultant who writes specifications\n"
            "- design:           Architectural or structural design firm\n"
            "- main_contractor:  Main contractor / General contractor for overall construction\n"
            "- system_integrator: ELV / Security / ICT / AV system integrator who installs the systems\n"
            "- epc:              EPC design-and-build contractor\n"
            "- other:            Any other party (connectivity platform, utility, strategic partner, etc.)\n"
            "Set unknown fields to null. ALL text must be in English."
        )
    else:
        prompt = (
            f"请对以下项目做调研，输出严格 JSON：\n\n"
            f"项目名称：{project.project_name}\n"
            f"行业：{project.industry or '未知'}\n"
            f"地区：{project.region or '未知'}\n"
            f"阶段：{project.current_stage or '未知'}\n\n"
            "请输出如下 JSON 结构：\n"
            "{\n"
            '  "description": "项目详细描述（2~5 句）",\n'
            '  "progress": "项目最新进展（1~3 句，可包含日期）",\n'
            '  "stakeholders": [\n'
            '    {\n'
            '      "stakeholder_type": "owner|consultant|design|main_contractor|system_integrator|epc|construction|other",\n'
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
            "stakeholder_type 说明：owner=建设单位, consultant=机电/安防顾问, design=设计院, "
            "main_contractor=主承包商, system_integrator=系统集成商, epc=EPC/总承包, "
            "construction=施工单位, other=其他。找不到的字段设为 null。"
        )

    _recover_stale_logs()
    acquired = _research_semaphore.acquire(timeout=10)
    if not acquired:
        return jsonify(success=False, message='调研队列繁忙（最多2个并发），请稍后重试'), 429

    log = _log_research(current_user.id, 'lost')
    try:
        raw = send_claude_research_request(prompt, timeout=180, user_id=current_user.id)
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if not m:
            _finish_log(log, False)
            return jsonify(success=False, message='AI 未返回有效结果'), 500
        data = json.loads(m.group())
        _finish_log(log, True)
        return jsonify({
            'success': True,
            'prospect_id': research.id,
            'project_name': project.project_name,
            'description': (data.get('description') or '').strip(),
            'progress': (data.get('progress') or '').strip(),
            'stakeholders': data.get('stakeholders') or [],
        })
    except Exception as e:
        _finish_log(log, False)
        current_app.logger.exception("Lost-project AI research failed")
        return jsonify(success=False, message=f'调研失败：{str(e)[:200]}'), 500
    finally:
        _research_semaphore.release()


@prospect_bp.route('/<int:id>/ai-research', methods=['POST'])
@login_required
@permission_required('project', 'view')
def intel_ai_research(id):
    """触发情报库项目的 AI 调研，只返回结果不写入，由前端预览后确认写入。"""
    from app.services.claude_research_provider import send_claude_research_request
    from config import Config
    import json
    import re

    p = ProspectProject.query.filter_by(id=id, is_deleted=False).first_or_404()
    is_ovs = bool(Config.IS_OVS)

    if is_ovs:
        prompt = (
            f"⚠️ LANGUAGE RULE (MANDATORY): Your entire JSON output MUST be in English only. "
            f"Do NOT use Chinese or any other non-English language, even if search results are in other languages.\n\n"
            f"You are an intelligence analyst for an industrial communication systems vendor selling into Southeast Asia. "
            f"Use the web_search tool to research the following project and output strict JSON.\n\n"
            f"Project name: {p.project_name}\n"
            f"Industry: {p.industry or 'unknown'}\n"
            f"Region: {p.region or 'unknown'}\n\n"
            f"Search strategy:\n"
            f'1. Search "[project name] developer owner" to find the client/owner.\n'
            f'2. Search "[project name] main contractor awarded" to find the general contractor.\n'
            f'3. Search "[project name] M&E consultant" or "[project name] ELV consultant security consultant" to find MEP/security consultants.\n'
            f'4. Search "[project name] ELV integrator" or "[project name] security system integrator ICT" to find system integrators.\n'
            f'5. Search "[project name] latest news {p.region or ""}" for progress updates.\n\n'
            "Output the following JSON structure (English only):\n"
            "{\n"
            '  "description": "2-5 sentence project overview (scope, scale, technology) — English only",\n'
            '  "progress": "Latest milestone with date (1-3 sentences) — English only — or null",\n'
            '  "stakeholders": [\n'
            '    {\n'
            '      "stakeholder_type": "owner|consultant|design|main_contractor|system_integrator|epc|other",\n'
            '      "company_name": "full registered company name in English",\n'
            '      "department": "department name in English or null",\n'
            '      "address": "address or null",\n'
            '      "phone": "phone or null",\n'
            '      "contact_person": "contact name (romanised) or null",\n'
            '      "email": "email or null",\n'
            '      "website": "official site or null",\n'
            '      "business_scope": "business scope in English or null",\n'
            '      "notes": "notes in English or null"\n'
            '    }\n'
            "  ]\n"
            "}\n\n"
            "Stakeholder type guide (choose the MOST SPECIFIC type):\n"
            "- owner:            Developer / Owner / Client / Employer who funds the project\n"
            "- consultant:       MEP / ELV / Security / ICT consultant who writes specifications — NOT general infrastructure partners\n"
            "- design:           Architectural or structural design firm / design institute\n"
            "- main_contractor:  Main contractor / General contractor responsible for overall construction\n"
            "- system_integrator: ELV / Security / ICT / AV / IBMS system integrator who installs the systems\n"
            "- epc:              EPC design-and-build contractor holding both design and construction responsibility\n"
            "- other:            Any other party (e.g. connectivity platform, utility provider, strategic partner)\n\n"
            "Set unknown fields to null. ALL text must be in English."
        )
    else:
        prompt = (
            f"请对以下市场情报项目做调研，输出严格 JSON：\n\n"
            f"项目名称：{p.project_name}\n"
            f"行业：{p.industry or '未知'}\n"
            f"地区：{p.region or '未知'}\n\n"
            "请输出如下 JSON 结构：\n"
            "{\n"
            '  "description": "项目详细描述（2~5 句）",\n'
            '  "progress": "项目最新进展（1~3 句，可包含日期）",\n'
            '  "stakeholders": [\n'
            '    {\n'
            '      "stakeholder_type": "owner|consultant|design|main_contractor|system_integrator|epc|construction|other",\n'
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
            "stakeholder_type 说明：owner=建设单位, consultant=机电/安防顾问, design=设计院, "
            "main_contractor=主承包商, system_integrator=系统集成商, epc=EPC/总承包, "
            "construction=施工单位, other=其他。找不到的字段设为 null。"
        )

    _recover_stale_logs()
    acquired = _research_semaphore.acquire(timeout=10)
    if not acquired:
        return jsonify(success=False, message='调研队列繁忙（最多2个并发），请稍后重试'), 429

    log = _log_research(current_user.id, 'intel')
    try:
        raw = send_claude_research_request(prompt, timeout=180, user_id=current_user.id)
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if not m:
            _finish_log(log, False)
            return jsonify(success=False, message='AI 未返回有效结果'), 500
        data = json.loads(m.group())
        _finish_log(log, True)
        return jsonify({
            'success': True,
            'prospect_id': p.id,
            'project_name': p.project_name,
            'description': (data.get('description') or '').strip(),
            'progress': (data.get('progress') or '').strip(),
            'stakeholders': data.get('stakeholders') or [],
        })
    except Exception as e:
        _finish_log(log, False)
        current_app.logger.exception("Intel AI research failed")
        return jsonify(success=False, message=f'调研失败：{str(e)[:200]}'), 500
    finally:
        _research_semaphore.release()


def _build_batch_prompt_cn(provinces, industries, current_year):
    """中国大陆批量调研 prompt — 中文 + 省份。"""
    industry_name_map = {
        'chemical':          '石化化工（炼化/乙烯/PTA等大型装置）',
        'energy':            '能源（火电厂/变电站/油气储运）',
        'manufacturing':     '制造业（大型工厂/车间改造）',
        'shipbuilding':      '造船（船厂/船坞/修船厂）',
        'semiconductor':     '半导体（晶圆厂/封测厂）',
        'tunnel_underground':'隧道/地下工程（铁路隧道/地铁/矿山）',
        'transportation':    '交通（铁路/机场/港口）',
        'datacenter':        '数据中心',
    }
    industry_zh = [industry_name_map.get(i, i) for i in industries]
    province_str = '、'.join(provinces)
    industry_str = '；'.join(industry_zh)

    return f"""你是工业通信系统（对讲机/调度系统）销售的情报分析师。
使用 web_search 工具搜索以下省份和行业在 {current_year} 年的新建/改造大型工程项目。

目标省份：{province_str}
目标行业：{industry_str}

【搜索策略 - 按顺序执行多次搜索】

第1步：批量找项目（每个省份+行业组合分别搜索）
- 搜索词：「{province_str} [行业关键词] 新建 改造 {current_year} 项目 建设单位」
- 搜索词：「{province_str} [行业关键词] 环评公示 {current_year} 建设单位」
- 搜索词：「{province_str} {current_year}年重大项目 [行业关键词]」

第2步：找EPC承包商/设计院
- 对找到的每个项目搜索：「[项目名称] EPC 中标 设计院」
- 或：「[建设单位] [项目关键词] EPC 招标」

第3步：找设计院电信/通信部门
- 对找到的设计院搜索：「[设计院名] 电气电信室 联系方式」
- 或：「[设计院名] 电信专业 工程师」
- 招聘公告也能暴露部门名称：「[设计院名] 招聘 电信设计 岗位」

【重点关注的联系部门】
- 石化/化工项目：设计院的「电气电信室」或「仪表自控室」
- 能源/发电项目：「电气专业室」「通信专业室」
- 制造/船厂：「工程部」「电气部」

【输出格式 - 严格 JSON，只输出 JSON 不输出其他文字】
{{
  "projects": [
    {{
      "project_name": "项目全称",
      "region": "省份（如：广东）",
      "city": "城市（如：茂名）或 null",
      "industry": "industry key，只能是：chemical/energy/manufacturing/shipbuilding/semiconductor/tunnel_underground/transportation/datacenter/other",
      "stage": "根据实际进展判断：planning（规划/审批中）/ designing（设计阶段）/ construction（在建）/ completed（已竣工）",
      "total_investment": "投资额（如：50亿）或 null",
      "description": "项目背景和规模描述（2~4句）",
      "progress": "最新建设进展（含时间节点，1~3句）或 null",
      "stakeholders": [
        {{
          "stakeholder_type": "owner/consultant/design/main_contractor/system_integrator/epc/construction/other",
          "company_name": "公司全称",
          "department": "部门名称（如：电气电信室）或 null",
          "address": "地址或 null",
          "phone": "电话或 null",
          "contact_person": "联系人或 null",
          "email": "邮箱或 null",
          "website": "官网或 null",
          "business_scope": "业务范围或 null",
          "notes": "备注或 null"
        }}
      ]
    }}
  ]
}}

要求：
1. 至少搜索 3~5 次才输出结果
2. 每个省份+行业组合至少找 1~2 个项目（有条件找更多）
3. 每个项目至少包含1个业主(owner)和1个设计院(design)或主承包商(main_contractor)
   stakeholder_type说明：owner=建设单位, consultant=机电/安防顾问, design=设计院,
   main_contractor=主承包商, system_integrator=系统集成商, epc=EPC/总承包, construction=施工单位, other=其他
4. 没有公开信息的字段设为 null，不要编造
5. stage 必须是 planning/designing/construction/completed 四者之一，根据实际进展判断
6. 输出完整合法的 JSON"""


def _build_batch_prompt_sg(countries, industries, current_year):
    """SEA 批量调研 prompt — 英文 + 国家 + ELV/M&E 术语。"""
    industry_name_map = {
        'datacenter':        'Data Center (hyperscale / colocation / AI compute campus)',
        'hospitality':       'Hotel & Resort (5-star hotels, integrated resorts, serviced apartments)',
        'healthcare':        'Healthcare (hospitals, medical centers, specialty clinics)',
        'manufacturing':     'Manufacturing (industrial plants, EV/battery factories, large workshops)',
        'semiconductor':     'Semiconductor (wafer fab, OSAT, advanced packaging)',
        'transportation':    'Transportation (port, airport, MRT, rail, expressway)',
        'real_estate':       'Commercial Real Estate (mixed-use, Grade-A office, retail mall)',
        'shipbuilding':      'Shipbuilding & Marine (shipyard, dry dock, offshore yard)',
        'energy':            'Energy (power plant, LNG terminal, solar/renewable)',
        'education':         'Education (university campus, international school)',
        'government':        'Government (public infrastructure, civic complex)',
    }
    industry_en = [industry_name_map.get(i, i) for i in industries]
    country_str = ' / '.join(countries)
    industry_str = ' | '.join(industry_en)

    return f"""You are an intelligence analyst for an industrial communication systems vendor (two-way radios, dispatch consoles, IP intercom, public address) selling into Southeast Asia.
Use the web_search tool to find new-build / major-upgrade projects in {current_year} across the target countries and industries below.

⚠️ LANGUAGE RULE (MANDATORY): Your entire JSON output — every string value — MUST be written in English.
   Do NOT use Chinese, Malay, Thai, or any other language, even if your web search results are in those languages.
   Translate all names, departments, and descriptions into English before inserting them into the JSON.

TARGET COUNTRIES: {country_str}
TARGET INDUSTRIES: {industry_str}

[SEARCH STRATEGY — run several searches per country+industry]

Step 1 — Find projects (per country + industry combo):
- "[country] [industry keyword] new project {current_year} announcement developer"
- "[country] [industry keyword] groundbreaking {current_year} site"
- "[country] regulatory approval {current_year} [industry keyword]"  (BCA / URA / EDB for SG; CIDB for MY; PUPR / OSS for ID; BOI for TH)

Step 2 — Find Main Contractor / General Contractor:
- "[project name] main contractor awarded"
- "[project name] general contractor contract"
- "[developer] [project keyword] tender awarded main contractor"

Step 3 — Find M&E / ELV / Security Consultant (where radio + intercom + PA scope is specified):
- "[project name] M&E consultant" or "[project name] MEP consultant design"
- "[project name] ELV consultant" or "[project name] security consultant"
- "[project name] ICT consultant" / "[project name] IBMS consultant"
- "[M&E consultant firm] ELV department contact"

Step 4 — Find System Integrator for ELV / Security / ICT:
- "[project name] ELV system integrator"
- "[project name] security integrator CCTV access control"
- "[project name] PA intercom radio system integrator"
- "[project name] ICT system integrator LAN WiFi"

[KEY DEPARTMENTS WORTH NAMING]
- Data Center / Semiconductor / Hospital: ELV / ICT / IBMS team inside the M&E consultancy
- Manufacturing / Shipyard: Engineering / E&I (electrical & instrumentation) team
- Port / Airport / MRT: Communication & Control Systems team
- Hotel / Real Estate: Building Services / Smart Building team

[OUTPUT FORMAT — strict JSON, output JSON only, no surrounding prose]
{{
  "projects": [
    {{
      "project_name": "Full official project name (English)",
      "region": "country (e.g. Singapore, Malaysia, Indonesia, Thailand, Vietnam, Philippines, Cambodia, Myanmar)",
      "city": "city / district (e.g. Johor Bahru, Batam) or null",
      "industry": "industry key — must be one of: datacenter / hospitality / healthcare / manufacturing / semiconductor / transportation / real_estate / shipbuilding / energy / education / government / other",
      "stage": "determine from research: planning (approved/announced, not yet started) / designing (design phase) / construction (under construction) / completed (built and operational)",
      "total_investment": "amount with currency (e.g. USD 800M, SGD 1.2B, RM 500M) or null",
      "description": "2-4 sentence summary of project scope and scale — ENGLISH ONLY",
      "progress": "latest construction milestone with date (1-3 sentences) — ENGLISH ONLY — or null",
      "stakeholders": [
        {{
          "stakeholder_type": "owner / consultant / design / main_contractor / system_integrator / epc / other",
          "company_name": "full registered company name in English",
          "department": "department name in English (e.g. ELV Department, ICT Team) or null",
          "address": "address or null",
          "phone": "phone or null",
          "contact_person": "contact name (romanised / English) or null",
          "email": "email or null",
          "website": "official site or null",
          "business_scope": "business scope in English or null",
          "notes": "notes in English or null"
        }}
      ]
    }}
  ]
}}

Stakeholder type guide (choose the MOST SPECIFIC type that applies):
- owner            → Developer / Owner / Client / Employer who funds the project
- consultant       → MEP (Mechanical, Electrical, Plumbing) consultant / ELV consultant / Security consultant / ICT specialist / PMC who writes specifications — NOT general infrastructure partners
- design           → Architectural or structural design firm / design institute
- main_contractor  → Main contractor / General contractor responsible for overall site construction and coordination
- system_integrator → ELV / Security / ICT / AV / IBMS system integrator who supplies and installs the systems
- epc              → EPC (Engineering, Procurement, Construction) design-and-build contractor who holds both design and construction responsibility
- other            → Any other party that does not fit the above (e.g. strategic infrastructure platform, connectivity partner, utility provider)

Rules:
1. Run at least 4-6 searches before producing output.
2. Find 1-2 projects (more if available) per country + industry combo.
3. Each project must include at least: one owner, one main_contractor, and one consultant (MEP/ELV/Security).
4. If a system integrator for ELV/security/ICT is found, always include them — they are high priority.
5. Use null for any field not explicitly stated in search results — do not fabricate.
6. ALL text values in the JSON must be in English. Translate if necessary.
7. Output complete, valid JSON only."""


@prospect_bp.route('/batch-research', methods=['POST'])
@login_required
@permission_required('project', 'view')
def batch_research():
    """批量调研：按地区(省份/国家)+行业触发 AI 搜索。CN 用省份+中文 prompt，SG 用国家+英文 prompt。"""
    from app.services.claude_research_provider import send_claude_research_request
    from config import Config
    import json
    import re

    body = request.get_json() or {}
    is_ovs = bool(getattr(Config, 'IS_OVS', False))
    # SG 传 countries，CN 传 provinces；为兼容也接受任一键
    regions = body.get('countries') if is_ovs else body.get('provinces')
    if not regions:
        regions = body.get('provinces') or body.get('countries') or []
    industries = body.get('industries') or []

    if not regions or not industries:
        msg = _('请至少选择一个省份和一个行业') if not is_ovs else _('Please select at least one country and one industry')
        return jsonify(success=False, message=msg), 400

    regions = regions[:2]
    industries = industries[:2]

    current_year = datetime.now().year
    if is_ovs:
        prompt = _build_batch_prompt_sg(regions, industries, current_year)
    else:
        prompt = _build_batch_prompt_cn(regions, industries, current_year)

    _recover_stale_logs()

    # 非管理员每日配额检查
    if not is_admin_or_ceo(current_user):
        remaining = _batch_quota_remaining(current_user.id)
        if remaining <= 0:
            return jsonify(success=False, message=_('今日批量调研次数已达上限（3次），明日再试')), 429

    acquired = _research_semaphore.acquire(timeout=10)
    if not acquired:
        return jsonify(success=False, message=_('调研队列繁忙（最多2个并发），请稍后重试')), 429

    log = _log_research(current_user.id, 'batch')
    try:
        raw = send_claude_research_request(prompt, timeout=300, user_id=current_user.id)
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if not m:
            _finish_log(log, False)
            return jsonify(success=False, message=_('AI 未返回有效 JSON')), 500
        data = json.loads(m.group())
        ai_projects = data.get('projects') or []

        # 去重检查：与已有 ProspectProject（standalone intel）比对
        existing = {
            p.project_name.strip()
            for p in ProspectProject.query.filter(
                ProspectProject.is_deleted == False,
                ProspectProject.link_type.is_(None),
            ).all()
        }

        result = []
        for proj in ai_projects:
            if not isinstance(proj, dict):
                continue
            proj['in_library'] = proj.get('project_name', '').strip() in existing
            result.append(proj)

        _finish_log(log, True)
        remaining_after = (
            _batch_quota_remaining(current_user.id)
            if not is_admin_or_ceo(current_user) else None
        )
        return jsonify(success=True, projects=result, quota_remaining=remaining_after)
    except Exception as e:
        _finish_log(log, False)
        current_app.logger.exception("Batch research failed")
        return jsonify(success=False, message=f'调研失败：{str(e)[:200]}'), 500
    finally:
        _research_semaphore.release()


@prospect_bp.route('/batch-research/save', methods=['POST'])
@login_required
@permission_required('project', 'view')
def batch_research_save():
    """将用户从批量调研结果中选中的项目批量写入情报库。"""
    body = request.get_json() or {}
    projects_to_save = body.get('projects') or []

    def _clean(v):
        if v is None:
            return None
        if isinstance(v, list):
            joined = '\n'.join(str(x).strip() for x in v if x)
            return joined or None
        s = str(v).strip()
        return None if not s or s.lower() in ('null', 'none') else s

    valid_types = set(STAKEHOLDER_TYPES.keys())
    created = 0
    skipped = 0

    try:
        for proj in projects_to_save:
            if not isinstance(proj, dict):
                continue
            project_name = _clean(proj.get('project_name'))
            if not project_name:
                continue

            # 按项目名去重（忽略大小写）
            exists = ProspectProject.query.filter(
                ProspectProject.is_deleted == False,
                db.func.lower(ProspectProject.project_name) == project_name.lower()
            ).first()
            if exists:
                skipped += 1
                continue

            def _trunc(s, n):
                return s[:n] if s else s

            p = ProspectProject(
                project_name=project_name[:200],
                industry=_trunc(_clean(proj.get('industry')), 50),
                region=_trunc(_clean(proj.get('region')), 100),
                city=_trunc(_clean(proj.get('city')), 100),
                stage=proj.get('stage') if proj.get('stage') in PROSPECT_STAGES else 'planning',
                total_investment=_trunc(_clean(proj.get('total_investment')), 50),
                description=_clean(proj.get('description')),
                progress=_clean(proj.get('progress')),
                link_type=None,
                source='ai',
                info_updated_by=_trunc(f"{current_user.real_name or current_user.username} 调研", 50),
                info_updated_at=datetime.utcnow(),
            )
            db.session.add(p)
            db.session.flush()

            for entry in (proj.get('stakeholders') or []):
                if not isinstance(entry, dict):
                    continue
                company_name = _clean(entry.get('company_name'))
                if not company_name:
                    continue
                stype = (entry.get('stakeholder_type') or 'other').strip().lower()
                if stype not in valid_types:
                    stype = 'other'
                sk = ProspectStakeholder(
                    prospect_id=p.id,
                    stakeholder_type=stype,
                    company_name=company_name[:200],
                    department=_trunc(_clean(entry.get('department')), 100),
                    address=_clean(entry.get('address')),
                    phone=_trunc(_clean(entry.get('phone')), 50),
                    contact_person=_trunc(_clean(entry.get('contact_person')), 50),
                    email=_clean(entry.get('email')),
                    website=_clean(entry.get('website')),
                    business_scope=_clean(entry.get('business_scope')),
                    notes=_clean(entry.get('notes')),
                )
                db.session.add(sk)

            created += 1

        db.session.commit()
        return jsonify(success=True, created=created, skipped=skipped)
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Batch research save failed")
        return jsonify(success=False, message=str(e)[:200]), 500


@prospect_bp.route('/ai-research/<int:prospect_id>/save', methods=['POST'])
@login_required
@permission_required('project', 'view')
def save_ai_research(prospect_id):
    """将前端预览确认后的调研结果写入 ProspectProject + ProspectStakeholder。"""
    p = ProspectProject.query.filter_by(id=prospect_id, is_deleted=False).first_or_404()
    body = request.get_json() or {}

    if body.get('description'):
        p.description = body['description'].strip()
    if body.get('progress'):
        p.progress = body['progress'].strip()
    p.info_updated_at = datetime.utcnow()
    p.info_updated_by = current_user.username

    def _clean(v):
        if v is None:
            return None
        if isinstance(v, list):
            joined = '\n'.join(str(x).strip() for x in v if x)
            return joined or None
        s = str(v).strip()
        return None if not s or s.lower() in ('null', 'none') else s

    valid_types = set(STAKEHOLDER_TYPES.keys())
    added = 0
    for entry in (body.get('stakeholders') or []):
        if not isinstance(entry, dict):
            continue
        company_name = _clean(entry.get('company_name'))
        if not company_name:
            continue
        stype = (entry.get('stakeholder_type') or 'other').strip().lower()
        if stype not in valid_types:
            stype = 'other'
        sk = ProspectStakeholder(
            prospect_id=p.id,
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

    try:
        db.session.commit()
        return jsonify(success=True, stakeholders_added=added)
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Save AI research failed")
        return jsonify(success=False, message=str(e)[:200]), 500


@prospect_bp.route('/batch-research/quota', methods=['GET'])
@login_required
@permission_required('project', 'view')
def batch_research_quota():
    """返回当前用户今日剩余批量调研次数。"""
    if is_admin_or_ceo(current_user):
        return jsonify(is_admin=True, remaining=None)
    _recover_stale_logs()
    return jsonify(is_admin=False, remaining=_batch_quota_remaining(current_user.id), daily_limit=_BATCH_DAILY_QUOTA)


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


@prospect_bp.route('/lost/<int:project_id>/panel')
@login_required
@permission_required('project', 'view')
def lost_panel(project_id):
    """返回 JSON 供公共项目池列表页 modal 注入，布局与市场情报面板一致。"""
    from app.models.prospect_claim_request import ProspectClaimRequest
    from app.utils.activity_tracker import FROZEN_STAGES
    from app.models.project_customer_association import ProjectCustomerAssociation

    project = Project.query.filter_by(id=project_id, is_deleted=False).first_or_404()

    if project.activity_status != 'churned' or project.current_stage in FROZEN_STAGES:
        return jsonify(success=False, message='项目不在公共项目池'), 400

    research = ProspectProject.query.filter_by(
        converted_project_id=project.id,
        link_type='research',
    ).first()

    # CRM 关联企业（来自 ProjectCustomerAssociation，仅显示公司名+类型，不含联系人）
    crm_companies = ProjectCustomerAssociation.get_active_associations(project.id)

    # AI 调研权限：仅原负责人 + admin/ceo，避免 can_view_project 范围过宽
    # 导致公司内所有有查看权的用户都看不到"申请参与"按钮
    can_ai_research = is_admin_or_ceo() or (project.owner_id == current_user.id)
    has_applied = ProspectClaimRequest.query.filter_by(
        project_id=project.id,
        applicant_id=current_user.id,
    ).first() is not None

    tmpl = current_app.jinja_env.get_template('prospect/tw_lost_panel.html')
    stage_badge_html    = tmpl.module.render_stage_badge(project.current_stage)
    body_html           = tmpl.module.render_body(project, research, can_ai_research, crm_companies)
    footer_left_html    = tmpl.module.render_footer_left(project)
    footer_actions_html = tmpl.module.render_footer_actions(
        project.id, has_applied, can_ai_research, has_research=bool(research)
    )

    city  = project.city or (research.city if research else '') or ''
    region = project.region or (research.region if research else '') or ''

    return jsonify({
        'project_name':        project.project_name,
        'city':                city,
        'region':              region,
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

        raw = send_claude_research_request(prompt, timeout=120, user_id=current_user.id)

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


@prospect_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('project', 'view')
def delete_prospect(id):
    p = ProspectProject.query.filter_by(id=id, is_deleted=False).first_or_404()
    p.is_deleted = True
    db.session.commit()
    return jsonify(success=True)


@prospect_bp.route('/stakeholder/<int:sid>/delete', methods=['POST'])
@login_required
@permission_required('project', 'view')
def delete_stakeholder(sid):
    s = ProspectStakeholder.query.get_or_404(sid)
    db.session.delete(s)
    db.session.commit()
    return jsonify(success=True)


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
