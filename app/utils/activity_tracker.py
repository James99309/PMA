from app import db
from app.models.customer import Company
from app.models.action import Action, ActionReply
from app.models.project import Project
from app.models.settings import SystemSettings
from datetime import datetime, timedelta
from sqlalchemy import or_, and_, func
import logging

# 设置日志记录器
logger = logging.getLogger(__name__)

def check_company_activity(company_id=None, days_threshold=None):
    """
    检查客户活跃度并更新状态
    
    当连续n天没有客户数据的更新时，包括：
    - 客户数据更新
    - 客户下的跟进记录
    - 跟进记录的回复（不包括删除）
    - 客户下的项目的创建或者更新
    - 项目的跟进记录的创建和更新（不包括删除）
    则活跃度标签修改为不活跃
    
    Args:
        company_id: 客户ID，如果为None则检查所有客户
        days_threshold: 不活跃天数阈值，如果为None则使用系统设置的阈值
        
    Returns:
        (updated_count, active_count, inactive_count): 更新数量，活跃客户数量，不活跃客户数量
    """
    # 如果没有指定阈值，从系统设置获取
    if days_threshold is None:
        days_threshold = SystemSettings.get('customer_activity_threshold', 1)
    
    logger.info(f"开始检查客户活跃度，阈值为 {days_threshold} 天")
    
    # 计算时间阈值
    time_threshold = datetime.utcnow() - timedelta(days=days_threshold)
    
    # 准备查询
    if company_id:
        # 只检查指定的客户
        companies_query = Company.query.filter_by(id=company_id, is_deleted=False)
    else:
        # 检查所有非删除的客户
        companies_query = Company.query.filter_by(is_deleted=False)
    
    updated_count = 0
    active_count = 0
    inactive_count = 0
    
    # 遍历每个客户进行检查
    for company in companies_query.all():
        logger.debug(f"检查客户 ID: {company.id}, 名称: {company.company_name}")
        
        # 检查客户是否活跃
        is_active = False
        
        # 1. 检查客户自身更新时间
        if company.updated_at and company.updated_at > time_threshold:
            logger.debug(f"客户 {company.id} 最近更新时间: {company.updated_at}, 仍然活跃")
            is_active = True
        
        # 2. 检查客户联系人更新时间
        if not is_active:
            for contact in company.contacts:
                if contact.updated_at and contact.updated_at > time_threshold:
                    logger.debug(f"客户 {company.id} 的联系人 {contact.id} 最近更新时间: {contact.updated_at}, 仍然活跃")
                    is_active = True
                    break
        
        # 3. 检查客户跟进记录
        if not is_active:
            recent_action = Action.query.filter(
                and_(
                    Action.company_id == company.id,
                    Action.created_at > time_threshold
                )
            ).first()
            
            if recent_action:
                logger.debug(f"客户 {company.id} 有最近的跟进记录 ID: {recent_action.id}, 创建于 {recent_action.created_at}, 仍然活跃")
                is_active = True
        
        # 4. 检查跟进记录的回复
        if not is_active:
            # 查找客户的所有跟进记录ID
            action_ids = [action.id for action in company.actions]
            
            if action_ids:
                recent_reply = ActionReply.query.filter(
                    and_(
                        ActionReply.action_id.in_(action_ids),
                        ActionReply.created_at > time_threshold
                    )
                ).first()
                
                if recent_reply:
                    logger.debug(f"客户 {company.id} 的跟进记录有最近回复 ID: {recent_reply.id}, 创建于 {recent_reply.created_at}, 仍然活跃")
                    is_active = True
        
        # 5. 检查客户关联的项目更新
        if not is_active:
            # 查找与客户相关的项目
            related_projects = Project.query.filter(
                or_(
                    Project.end_user == company.company_name,
                    Project.design_issues == company.company_name,
                    Project.contractor == company.company_name,
                    Project.system_integrator == company.company_name,
                    Project.dealer == company.company_name
                )
            ).all()
            
            for project in related_projects:
                # 检查项目更新时间
                if project.updated_at and project.updated_at > time_threshold:
                    logger.debug(f"客户 {company.id} 关联的项目 {project.id} 最近更新时间: {project.updated_at}, 仍然活跃")
                    is_active = True
                    break
                
                # 检查项目的跟进记录
                if not is_active:
                    recent_project_action = Action.query.filter(
                        and_(
                            Action.project_id == project.id,
                            Action.created_at > time_threshold
                        )
                    ).first()
                    
                    if recent_project_action:
                        logger.debug(f"客户 {company.id} 关联的项目 {project.id} 有最近的跟进记录 ID: {recent_project_action.id}, 创建于 {recent_project_action.created_at}, 仍然活跃")
                        is_active = True
                        break
        
        # 根据活跃状态更新客户
        new_status = 'active' if is_active else 'inactive'
        if company.status != new_status:
            old_status = company.status
            company.status = new_status
            db.session.add(company)
            updated_count += 1
            logger.info(f"客户 ID: {company.id}, 名称: {company.company_name} 的状态从 {old_status} 变更为 {new_status}")
        
        # 统计活跃/不活跃客户数量
        if is_active:
            active_count += 1
        else:
            inactive_count += 1
    
    # 提交更改
    if updated_count > 0:
        db.session.commit()
        logger.info(f"完成客户活跃度检查，共更新 {updated_count} 个客户状态")
    else:
        logger.info("完成客户活跃度检查，没有客户状态需要更新")
    
    return updated_count, active_count, inactive_count


def check_project_activity(project_id=None, days_threshold=None):
    """
    检查项目活跃度
    
    当连续n天没有项目的活动时，标记为不活跃。判断活跃的条件包括：
    - 项目基本信息更新（updated_at时间）
    - 项目阶段推进变更
    - 项目重要字段修改（如项目名称、授权码等）
    - 项目管理的参与单位变更（如直接用户、经销商、系统集成商等）
    - 项目跟进记录的创建和更新
    - 客户跟进记录中引用了该项目
    - 项目报价单的创建和更新
    
    Args:
        project_id: 项目ID，如果为None则检查所有项目
        days_threshold: 不活跃天数阈值，如果为None则使用系统设置的阈值
        
    Returns:
        (active_projects, inactive_projects): 活跃项目列表，不活跃项目列表
    """
    # 如果没有指定阈值，从系统设置获取
    if days_threshold is None:
        days_threshold = SystemSettings.get('project_activity_threshold', 7)
        
    logger.info(f"开始检查项目活跃度，阈值为 {days_threshold} 天")
    
    # 计算时间阈值
    time_threshold = datetime.utcnow() - timedelta(days=days_threshold)
    
    # 准备查询
    if project_id:
        # 只检查指定的项目
        projects = Project.query.filter_by(id=project_id).all()
    else:
        # 检查所有项目
        projects = Project.query.all()
    
    active_projects = []
    inactive_projects = []
    
    # 遍历每个项目进行检查
    for project in projects:
        logger.debug(f"检查项目 ID: {project.id}, 名称: {project.project_name}")
        
        # 检查项目是否活跃
        is_active = False
        last_activity_time = None
        activity_reason = "无活动"
        
        # 1. 检查项目自身更新时间（基本数据更新）
        if project.updated_at and project.updated_at > time_threshold:
            logger.debug(f"项目 {project.id} 最近更新时间: {project.updated_at}, 仍然活跃")
            is_active = True
            last_activity_time = project.updated_at
            activity_reason = "项目基本信息更新"
        
        # 2. 检查项目阶段推进变更
        if not is_active:
            try:
                from app.models.projectpm_stage_history import ProjectStageHistory
                recent_stage_change = ProjectStageHistory.query.filter(
                    ProjectStageHistory.project_id == project.id,
                    ProjectStageHistory.change_date > time_threshold
                ).first()
                
                if recent_stage_change:
                    logger.debug(f"项目 {project.id} 有阶段变更记录，变更时间: {recent_stage_change.change_date}, 仍然活跃")
                    is_active = True
                    last_activity_time = recent_stage_change.change_date
                    activity_reason = "项目阶段变更"
            except Exception as e:
                logger.error(f"检查项目阶段变更时出错: {str(e)}")
        
        # 3. 检查项目跟进记录
        if not is_active:
            recent_action = Action.query.filter(
                and_(
                    Action.project_id == project.id,
                    Action.created_at > time_threshold
                )
            ).first()
            
            if recent_action:
                logger.debug(f"项目 {project.id} 有最近的跟进记录 ID: {recent_action.id}, 创建于 {recent_action.created_at}, 仍然活跃")
                is_active = True
                last_activity_time = recent_action.created_at
                activity_reason = "项目跟进记录"
        
        # 4. 检查客户跟进记录中引用了该项目
        if not is_active:
            # 查询引用了该项目的客户跟进记录
            recent_ref_actions = Action.query.filter(
                and_(
                    func.instr(Action.action_content, f"项目ID: {project.id}") > 0,
                    Action.created_at > time_threshold
                )
            ).first()
            
            if recent_ref_actions:
                logger.debug(f"项目 {project.id} 被引用于客户跟进记录 ID: {recent_ref_actions.id}, 创建于 {recent_ref_actions.created_at}, 仍然活跃")
                is_active = True
                last_activity_time = recent_ref_actions.created_at
                activity_reason = "客户跟进记录引用"
        
        # 5. 检查项目报价单更新
        if not is_active:
            # 查询该项目的报价单更新
            from app.models.quotation import Quotation
            recent_quotation = Quotation.query.filter(
                and_(
                    Quotation.project_id == project.id,
                    Quotation.updated_at > time_threshold
                )
            ).first()
            
            if recent_quotation:
                logger.debug(f"项目 {project.id} 有报价单更新，更新时间: {recent_quotation.updated_at}, 仍然活跃")
                is_active = True
                last_activity_time = recent_quotation.updated_at
                activity_reason = "项目报价单更新"
        
        # 根据活跃状态分类项目，并记录活跃原因和最后活动时间
        if is_active:
            # 更新最后活动时间
            project.last_activity_date = last_activity_time
            # 记录活跃原因
            project.activity_reason = activity_reason
            active_projects.append(project)
        else:
            # 清除活跃原因
            project.activity_reason = None
            inactive_projects.append(project)
    
    logger.info(f"完成项目活跃度检查，活跃项目 {len(active_projects)} 个，不活跃项目 {len(inactive_projects)} 个")
    
    return active_projects, inactive_projects


def update_active_status(entity, days_threshold=None):
    """
    根据实体的updated_at时间更新活跃状态
    
    Args:
        entity: 需要更新活跃状态的实体对象（客户或项目）
        days_threshold: 不活跃天数阈值，如果为None则使用系统设置的阈值
        
    Returns:
        bool: 是否活跃
    """
    logger.info(f"更新 {entity.__class__.__name__} ID: {entity.id} 的活跃状态")
    
    # 如果没有指定阈值，从系统设置获取
    if days_threshold is None:
        # 根据实体类型选择不同的阈值
        if isinstance(entity, Company):
            days_threshold = SystemSettings.get('customer_activity_threshold', 30)
        elif isinstance(entity, Project):
            days_threshold = SystemSettings.get('project_activity_threshold', 7)
        else:
            logger.warning(f"未知实体类型: {entity.__class__.__name__}, 使用默认阈值30天")
            days_threshold = 30
    
    # 计算时间阈值
    time_threshold = datetime.utcnow() - timedelta(days=days_threshold)
    
    # 检查实体更新时间
    is_active = entity.updated_at and entity.updated_at > time_threshold
    
    # 客户和项目使用不同的字段记录活跃状态
    if isinstance(entity, Company):
        new_status = 'active' if is_active else 'inactive'
        if entity.status != new_status:
            old_status = entity.status
            entity.status = new_status
            db.session.add(entity)
            db.session.commit()
            logger.info(f"{entity.__class__.__name__} ID: {entity.id} 的状态从 {old_status} 变更为 {new_status}")
    elif isinstance(entity, Project):
        if entity.is_active != is_active:
            entity.is_active = is_active
            db.session.add(entity)
            db.session.commit()
            logger.info(f"{entity.__class__.__name__} ID: {entity.id} 的活跃状态变更为 {'活跃' if is_active else '不活跃'}")
    
    return is_active 