"""
活跃度追踪模块

实现6级活跃度状态计算（客户和项目共用）:
- highly_active (高度活跃): 30天内有报价单/阶段推进活动
- active (活跃): 30天内有项目/跟进活动，或30-60天内有报价单活动
- normal (正常): 30-60天内有项目/跟进活动，或60天内有联系人/客户更新
- to_follow (待跟进): 60-90天内有活动
- dormant (休眠): 90-120天内有活动
- churned (流失): 超过120天无活动
"""

from app import db
from app.models.customer import Company, Contact
from app.models.action import Action, ActionReply
from app.models.project import Project
from app.models.settings import SystemSettings
from datetime import datetime, timedelta
from sqlalchemy import or_, and_, func
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# 状态常量定义
# =============================================================================

ACTIVITY_STATUS = {
    'highly_active': '高度活跃',
    'active': '活跃',
    'normal': '正常',
    'to_follow': '待跟进',
    'dormant': '休眠',
    'churned': '流失'
}

# 状态优先级（数值越高越好）
STATUS_PRIORITY = {
    'highly_active': 6,
    'active': 5,
    'normal': 4,
    'to_follow': 3,
    'dormant': 2,
    'churned': 1
}

# 时间阈值（天）
TIME_THRESHOLDS = {
    'active': 30,      # 30天内
    'normal': 60,      # 60天内
    'to_follow': 90,   # 90天内
    'dormant': 120     # 120天内
}

# 行为类型标签
ACTIVITY_TYPE_LABELS = {
    'quotation': '报价单',
    'project': '项目',
    'action': '跟进记录',
    'reply': '跟进回复',
    'contact': '联系人更新',
    'company': '客户信息更新'
}


# =============================================================================
# 活动时间获取函数
# =============================================================================

def get_latest_quotation_date(company_id):
    """获取客户最近的报价单活动时间"""
    from app.models.quotation import Quotation

    # 查找与客户关联的项目
    company = Company.query.get(company_id)
    if not company:
        return None

    # 通过项目关联查找报价单
    related_projects = Project.query.filter(
        or_(
            Project.end_user == company.company_name,
            Project.design_issues == company.company_name,
            Project.contractor == company.company_name,
            Project.system_integrator == company.company_name,
            Project.dealer == company.company_name
        )
    ).all()

    if not related_projects:
        return None

    project_ids = [p.id for p in related_projects]

    # 查找最近的报价单
    latest_quotation = Quotation.query.filter(
        Quotation.project_id.in_(project_ids)
    ).order_by(Quotation.updated_at.desc()).first()

    return latest_quotation.updated_at if latest_quotation else None


def get_latest_project_date(company_id, company_name):
    """获取客户最近的项目活动时间"""
    # 通过公司名称关联查找项目
    latest_project = Project.query.filter(
        or_(
            Project.end_user == company_name,
            Project.design_issues == company_name,
            Project.contractor == company_name,
            Project.system_integrator == company_name,
            Project.dealer == company_name
        )
    ).order_by(Project.updated_at.desc()).first()

    return latest_project.updated_at if latest_project else None


def get_latest_action_date(company_id):
    """获取客户最近的跟进记录时间"""
    # 客户级别的跟进记录
    latest_action = Action.query.filter(
        Action.company_id == company_id
    ).order_by(Action.created_at.desc()).first()

    company_action_date = latest_action.created_at if latest_action else None

    # 项目级别的跟进记录
    company = Company.query.get(company_id)
    if company:
        related_projects = Project.query.filter(
            or_(
                Project.end_user == company.company_name,
                Project.design_issues == company.company_name,
                Project.contractor == company.company_name,
                Project.system_integrator == company.company_name,
                Project.dealer == company.company_name
            )
        ).all()

        if related_projects:
            project_ids = [p.id for p in related_projects]
            latest_project_action = Action.query.filter(
                Action.project_id.in_(project_ids)
            ).order_by(Action.created_at.desc()).first()

            if latest_project_action:
                project_action_date = latest_project_action.created_at
                if company_action_date is None or project_action_date > company_action_date:
                    return project_action_date

    return company_action_date


def get_latest_reply_date(company_id):
    """获取客户跟进记录的最近回复时间"""
    # 获取客户的所有跟进记录
    actions = Action.query.filter(Action.company_id == company_id).all()
    action_ids = [a.id for a in actions]

    if not action_ids:
        return None

    latest_reply = ActionReply.query.filter(
        ActionReply.action_id.in_(action_ids)
    ).order_by(ActionReply.created_at.desc()).first()

    return latest_reply.created_at if latest_reply else None


def get_latest_contact_date(company_id):
    """获取客户联系人的最近更新时间"""
    latest_contact = Contact.query.filter(
        Contact.company_id == company_id
    ).order_by(Contact.updated_at.desc()).first()

    return latest_contact.updated_at if latest_contact else None


# =============================================================================
# 状态计算函数
# =============================================================================

def get_status_by_type_and_days(activity_type, days):
    """
    根据行为类型和天数返回对应状态

    行为类型与活跃度对应表:
    | 行为类型 | 30天内 | 30-60天 | 60-90天 | 90-120天 | >120天 |
    |----------|--------|---------|---------|----------|--------|
    | 报价单活动 | 高度活跃 | 活跃 | 待跟进 | 休眠 | 流失 |
    | 项目活动 | 活跃 | 正常 | 待跟进 | 休眠 | 流失 |
    | 跟进记录 | 活跃 | 正常 | 待跟进 | 休眠 | 流失 |
    | 跟进回复 | 活跃 | 正常 | 待跟进 | 休眠 | 流失 |
    | 联系人更新 | 正常 | 正常 | 待跟进 | 休眠 | 流失 |
    | 客户信息更新 | 正常 | 正常 | 待跟进 | 休眠 | 流失 |
    """
    # 报价单活动（最高优先级）
    if activity_type == 'quotation':
        if days <= 30:
            return 'highly_active'
        elif days <= 60:
            return 'active'
        elif days <= 90:
            return 'to_follow'
        elif days <= 120:
            return 'dormant'
        else:
            return 'churned'

    # 项目/跟进记录/跟进回复
    elif activity_type in ('project', 'action', 'reply'):
        if days <= 30:
            return 'active'
        elif days <= 60:
            return 'normal'
        elif days <= 90:
            return 'to_follow'
        elif days <= 120:
            return 'dormant'
        else:
            return 'churned'

    # 联系人/客户信息更新
    elif activity_type in ('contact', 'company'):
        if days <= 60:
            return 'normal'
        elif days <= 90:
            return 'to_follow'
        elif days <= 120:
            return 'dormant'
        else:
            return 'churned'

    return 'churned'


def compare_status(status1, status2):
    """
    比较两个状态的优先级

    返回:
        > 0: status1 优先级更高
        < 0: status1 优先级更低
        = 0: 相同优先级
    """
    return STATUS_PRIORITY.get(status1, 0) - STATUS_PRIORITY.get(status2, 0)


def calculate_company_activity_status(company_id):
    """
    计算单个客户的活跃度状态

    返回: (status, reason, last_activity_date)
    """
    now = datetime.now()
    company = Company.query.get(company_id)

    if not company:
        return 'churned', '客户不存在', None

    # 收集所有活动时间
    activities = []

    # 1. 报价单活动（最高优先级）
    quotation_date = get_latest_quotation_date(company_id)
    if quotation_date:
        activities.append(('quotation', quotation_date))

    # 2. 项目活动
    project_date = get_latest_project_date(company_id, company.company_name)
    if project_date:
        activities.append(('project', project_date))

    # 3. 跟进记录
    action_date = get_latest_action_date(company_id)
    if action_date:
        activities.append(('action', action_date))

    # 4. 跟进回复
    reply_date = get_latest_reply_date(company_id)
    if reply_date:
        activities.append(('reply', reply_date))

    # 5. 联系人更新
    contact_date = get_latest_contact_date(company_id)
    if contact_date:
        activities.append(('contact', contact_date))

    # 6. 客户信息更新
    if company.updated_at:
        activities.append(('company', company.updated_at))

    if not activities:
        return 'churned', '无任何活动记录', None

    # 按规则计算最终状态
    best_status = 'churned'
    best_reason = ''
    last_activity = None

    for activity_type, activity_date in activities:
        days = (now - activity_date).days
        status = get_status_by_type_and_days(activity_type, days)

        if compare_status(status, best_status) > 0:
            best_status = status
            best_reason = f"{ACTIVITY_TYPE_LABELS.get(activity_type, activity_type)}({days}天前)"
            last_activity = activity_date

    return best_status, best_reason, last_activity


def update_company_activity(company_id, commit=True):
    """
    更新单个客户的活跃度状态

    Args:
        company_id: 客户ID
        commit: 是否提交事务

    Returns:
        (old_status, new_status, reason): 旧状态、新状态、原因
    """
    company = Company.query.get(company_id)
    if not company:
        return None, None, '客户不存在'

    old_status = company.status
    new_status, reason, last_activity = calculate_company_activity_status(company_id)

    if old_status != new_status:
        company.status = new_status
        db.session.add(company)
        if commit:
            db.session.commit()
        logger.info(f"客户 {company.company_name} (ID:{company_id}) 状态从 {old_status} 变更为 {new_status}，原因: {reason}")

    return old_status, new_status, reason


def batch_update_all_company_activity():
    """
    批量更新所有客户活跃度（定时任务使用）

    Returns:
        (updated_count, total_count): 更新数量、总数量
    """
    companies = Company.query.filter_by(is_deleted=False).all()
    updated_count = 0
    total_count = len(companies)

    logger.info(f"开始批量更新客户活跃度，共 {total_count} 个客户")

    for company in companies:
        old_status = company.status
        new_status, reason, last_activity = calculate_company_activity_status(company.id)

        if old_status != new_status:
            company.status = new_status
            db.session.add(company)
            updated_count += 1
            logger.debug(f"客户 {company.company_name} 状态变更: {old_status} -> {new_status}")

    db.session.commit()
    logger.info(f"批量更新完成，共更新 {updated_count}/{total_count} 条记录")

    return updated_count, total_count


# =============================================================================
# 兼容旧接口
# =============================================================================

def check_company_activity(company_id=None, days_threshold=None):
    """
    检查客户活跃度并更新状态（保留向后兼容）

    Args:
        company_id: 客户ID，如果为None则检查所有客户
        days_threshold: 不活跃天数阈值（新版本中忽略此参数）

    Returns:
        (updated_count, active_count, inactive_count)
    """
    logger.info("开始检查客户活跃度（使用新的6级状态系统）")

    if company_id:
        companies_query = Company.query.filter_by(id=company_id, is_deleted=False)
    else:
        companies_query = Company.query.filter_by(is_deleted=False)

    updated_count = 0
    status_counts = {
        'highly_active': 0,
        'active': 0,
        'normal': 0,
        'to_follow': 0,
        'dormant': 0,
        'churned': 0
    }

    for company in companies_query.all():
        old_status = company.status
        new_status, reason, last_activity = calculate_company_activity_status(company.id)

        if old_status != new_status:
            company.status = new_status
            db.session.add(company)
            updated_count += 1
            logger.info(f"客户 {company.company_name} 状态变更: {old_status} -> {new_status}")

        status_counts[new_status] = status_counts.get(new_status, 0) + 1

    if updated_count > 0:
        db.session.commit()
        logger.info(f"完成客户活跃度检查，共更新 {updated_count} 个客户状态")
    else:
        logger.info("完成客户活跃度检查，没有客户状态需要更新")

    # 计算活跃/非活跃数量（兼容旧接口）
    active_count = status_counts['highly_active'] + status_counts['active'] + status_counts['normal']
    inactive_count = status_counts['to_follow'] + status_counts['dormant'] + status_counts['churned']

    return updated_count, active_count, inactive_count


# =============================================================================
# 项目活跃度计算（6级状态系统）
# =============================================================================

PROJECT_ACTIVITY_TYPE_LABELS = {
    'stage_progression': '阶段推进',
    'quotation': '报价活动',
    'action': '跟进记录',
    'reply': '跟进回复',
    'project_update': '项目信息更新'
}


def get_project_status_by_type_and_days(activity_type, days):
    """
    根据项目活动类型和天数返回对应状态

    项目活跃度评估矩阵:
    | 活动类型       | ≤30天      | 30-60天 | 60-90天  | 90-120天 | >120天 |
    |---------------|------------|---------|---------|----------|--------|
    | 阶段推进       | highly_active | active | to_follow | dormant | churned |
    | 报价活动       | highly_active | active | to_follow | dormant | churned |
    | 跟进记录       | active     | normal  | to_follow | dormant | churned |
    | 跟进回复       | active     | normal  | to_follow | dormant | churned |
    | 项目信息更新   | normal     | normal  | to_follow | dormant | churned |
    """
    # 阶段推进和报价活动（最强信号）
    if activity_type in ('stage_progression', 'quotation'):
        if days <= 30:
            return 'highly_active'
        elif days <= 60:
            return 'active'
        elif days <= 90:
            return 'to_follow'
        elif days <= 120:
            return 'dormant'
        else:
            return 'churned'

    # 跟进记录/跟进回复（中等信号）
    elif activity_type in ('action', 'reply'):
        if days <= 30:
            return 'active'
        elif days <= 60:
            return 'normal'
        elif days <= 90:
            return 'to_follow'
        elif days <= 120:
            return 'dormant'
        else:
            return 'churned'

    # 项目信息更新（弱信号）
    elif activity_type == 'project_update':
        if days <= 60:
            return 'normal'
        elif days <= 90:
            return 'to_follow'
        elif days <= 120:
            return 'dormant'
        else:
            return 'churned'

    return 'churned'


def get_latest_project_stage_date(project_id):
    """获取项目最近的阶段推进时间"""
    from app.models.projectpm_stage_history import ProjectStageHistory

    latest = ProjectStageHistory.query.filter(
        ProjectStageHistory.project_id == project_id
    ).order_by(ProjectStageHistory.change_date.desc()).first()

    return latest.change_date if latest else None


def get_latest_project_quotation_date(project_id):
    """获取项目最近的报价单活动时间"""
    from app.models.quotation import Quotation

    latest = Quotation.query.filter(
        Quotation.project_id == project_id
    ).order_by(Quotation.updated_at.desc()).first()

    return latest.updated_at if latest else None


def get_latest_project_action_date(project_id):
    """获取项目最近的跟进记录时间"""
    latest = Action.query.filter(
        Action.project_id == project_id
    ).order_by(Action.created_at.desc()).first()

    return latest.created_at if latest else None


def get_latest_project_reply_date(project_id):
    """获取项目跟进记录的最近回复时间"""
    # 获取项目的所有跟进记录
    action_ids = db.session.query(Action.id).filter(
        Action.project_id == project_id
    ).all()
    action_ids = [a[0] for a in action_ids]

    if not action_ids:
        return None

    latest = ActionReply.query.filter(
        ActionReply.action_id.in_(action_ids)
    ).order_by(ActionReply.created_at.desc()).first()

    return latest.created_at if latest else None


def calculate_project_activity_status(project_id):
    """
    计算单个项目的活跃度状态

    返回: (status, reason, last_activity_date)
    """
    now = datetime.now()
    project = Project.query.get(project_id)

    if not project:
        return 'churned', '项目不存在', None

    # 收集所有活动时间
    activities = []

    # 1. 阶段推进（最强信号）
    stage_date = get_latest_project_stage_date(project_id)
    if stage_date:
        activities.append(('stage_progression', stage_date))

    # 2. 报价活动（最强信号）
    quotation_date = get_latest_project_quotation_date(project_id)
    if quotation_date:
        activities.append(('quotation', quotation_date))

    # 3. 跟进记录
    action_date = get_latest_project_action_date(project_id)
    if action_date:
        activities.append(('action', action_date))

    # 4. 跟进回复
    reply_date = get_latest_project_reply_date(project_id)
    if reply_date:
        activities.append(('reply', reply_date))

    # 5. 项目信息更新
    if project.updated_at:
        activities.append(('project_update', project.updated_at))

    if not activities:
        return 'churned', '无任何活动记录', None

    # 按规则计算最终状态（取最优结果）
    best_status = 'churned'
    best_reason = ''
    last_activity = None

    for activity_type, activity_date in activities:
        days = (now - activity_date).days
        status = get_project_status_by_type_and_days(activity_type, days)

        if compare_status(status, best_status) > 0:
            best_status = status
            best_reason = f"{PROJECT_ACTIVITY_TYPE_LABELS.get(activity_type, activity_type)}({days}天前)"
            last_activity = activity_date

    return best_status, best_reason, last_activity


def update_project_activity(project_id, commit=True):
    """
    更新单个项目的活跃度状态

    Args:
        project_id: 项目ID
        commit: 是否提交事务

    Returns:
        (old_status, new_status, reason): 旧状态、新状态、原因
    """
    project = Project.query.get(project_id)
    if not project:
        return None, None, '项目不存在'

    old_status = project.activity_status
    new_status, reason, last_activity = calculate_project_activity_status(project_id)

    # 同步更新 activity_status 和 is_active（派生字段）
    new_is_active = new_status in ('highly_active', 'active', 'normal')

    if old_status != new_status or project.is_active != new_is_active:
        project.activity_status = new_status
        project.is_active = new_is_active
        project.activity_reason = reason
        if last_activity:
            project.last_activity_date = last_activity
        db.session.add(project)
        if commit:
            db.session.commit()
        logger.info(f"项目 {project.project_name} (ID:{project_id}) 状态从 {old_status} 变更为 {new_status}，原因: {reason}")

    return old_status, new_status, reason


def batch_update_all_project_activity():
    """
    批量更新所有项目活跃度（定时任务使用）

    排除 lost/paused 阶段的项目。

    Returns:
        (updated_count, total_count): 更新数量、总数量
    """
    projects = Project.query.filter(
        Project.current_stage.notin_(['lost', 'paused'])
    ).all()
    updated_count = 0
    total_count = len(projects)

    logger.info(f"开始批量更新项目活跃度，共 {total_count} 个项目")

    for project in projects:
        old_status = project.activity_status
        new_status, reason, last_activity = calculate_project_activity_status(project.id)
        new_is_active = new_status in ('highly_active', 'active', 'normal')

        if old_status != new_status or project.is_active != new_is_active:
            project.activity_status = new_status
            project.is_active = new_is_active
            project.activity_reason = reason
            if last_activity:
                project.last_activity_date = last_activity
            db.session.add(project)
            updated_count += 1
            logger.debug(f"项目 {project.project_name} 状态变更: {old_status} -> {new_status}")

    db.session.commit()
    logger.info(f"项目活跃度批量更新完成，共更新 {updated_count}/{total_count} 条记录")

    return updated_count, total_count


def check_project_activity(project_id=None, days_threshold=None):
    """
    检查项目活跃度并更新状态（保留向后兼容）

    Args:
        project_id: 项目ID，如果为None则检查所有项目
        days_threshold: 不活跃天数阈值（新版本中忽略此参数）

    Returns:
        (active_projects, inactive_projects): 活跃项目列表，不活跃项目列表
    """
    logger.info("开始检查项目活跃度（使用新的6级状态系统）")

    if project_id:
        projects = Project.query.filter_by(id=project_id).all()
    else:
        projects = Project.query.all()

    active_projects = []
    inactive_projects = []

    for project in projects:
        old_status, new_status, reason = update_project_activity(project.id, commit=False)

        if new_status in ('highly_active', 'active', 'normal'):
            active_projects.append(project)
        else:
            inactive_projects.append(project)

    if active_projects or inactive_projects:
        db.session.commit()

    logger.info(f"完成项目活跃度检查，活跃项目 {len(active_projects)} 个，不活跃项目 {len(inactive_projects)} 个")

    return active_projects, inactive_projects


def update_active_status(entity, days_threshold=None, commit=True):
    """
    根据实体的活动数据更新活跃状态（保留向后兼容）

    Args:
        entity: 需要更新活跃状态的实体对象（客户或项目）
        days_threshold: 不活跃天数阈值（新版本中忽略此参数）
        commit: 是否自动提交事务

    Returns:
        bool: 是否活跃
    """
    if isinstance(entity, Company):
        # 使用新的活跃度计算逻辑
        old_status, new_status, reason = update_company_activity(entity.id, commit)
        # 返回是否为活跃状态（highly_active, active, normal 视为活跃）
        return new_status in ('highly_active', 'active', 'normal')
    elif isinstance(entity, Project):
        # 使用新的6级项目活跃度计算逻辑
        old_status, new_status, reason = update_project_activity(entity.id, commit)
        return new_status in ('highly_active', 'active', 'normal')

    return False
