from flask import url_for
from app.utils.dictionary_helpers import COMPANY_TYPE_OPTIONS, INDUSTRY_OPTIONS
from app.utils.dictionary_helpers import company_type_label, industry_label
from app.utils.notification_helpers import trigger_event_notification
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def notify_project_created(project, creator):
    """
    在项目创建成功后触发通知
    
    Args:
        project: 项目实例
        creator: 创建者（一般为current_user）
    
    Returns:
        bool: 是否成功触发通知
    """
    try:
        return trigger_event_notification(
            event_key='project_created',
            target_user_id=project.owner_id,
            context={
                'project': project,
                'create_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'project_url': url_for('project.view_project', project_id=project.id, _external=True),
                'current_year': datetime.now().year
            }
        )
    except Exception as e:
        logger.warning(f"触发项目创建通知失败: {str(e)}")
        return False
        
def notify_project_status_updated(project, modifier, previous_stage=None):
    """
    在项目阶段变更后触发通知
    
    Args:
        project: 项目实例，其中project.current_stage已经是新的阶段值
        modifier: 修改者（一般为current_user）
        previous_stage: 变更前的阶段值，如果未提供则仅显示新值
    
    Returns:
        bool: 是否成功触发通知
    """
    from app.utils.dictionary_helpers import project_stage_label
    try:
        context = {
            'project': project,
            'new_stage': project_stage_label(project.current_stage),
            'change_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'project_url': url_for('project.view_project', project_id=project.id, _external=True),
            'current_year': datetime.now().year,
            'modifier': modifier
        }
        
        # 更健壮地处理 previous_stage，保证模板渲染不会因其缺失或空字符串而失败
        if not previous_stage or str(previous_stage).strip() == "":
            context['previous_stage'] = "未知"
        else:
            context['previous_stage'] = project_stage_label(previous_stage)
        
        return trigger_event_notification(
            event_key='project_status_updated',
            target_user_id=project.owner_id,
            context=context
        )
    except Exception as e:
        logger.warning(f"触发项目阶段变更通知失败: {str(e)}")
        return False

def notify_quotation_created(quotation, creator):
    return trigger_event_notification(
        event_key='quotation_created',
        target_user_id=creator.id,
        context={
            'quotation': quotation,
            'create_time': datetime.utcnow(),
            'quotation_url': url_for('quotation.view', id=quotation.id, _external=True)
        }
    )


# 新增：客户创建通知
def notify_customer_created(company, user):
    context = {
        'target': company,
        'user': user,
        'recipient_name': user.real_name or user.username,
        'company_type_label': company_type_label(company.company_type),
        'industry_label': industry_label(company.industry),
        'owner_label': user.real_name or user.username,
        'customer_url': url_for('customer.view_company', company_id=company.id, _external=True),
        'current_year': datetime.utcnow().year,
    }
    trigger_event_notification('customer_created', user.id, context)