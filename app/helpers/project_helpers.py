from flask import current_app
from flask_login import current_user
from app import db
from app.models.project import Project
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def lock_project(project_id, reason="审批流程锁定", user_id=None, force=False):
    """锁定项目，防止编辑
    
    Args:
        project_id: 项目ID
        reason: 锁定原因
        user_id: 锁定人ID，默认为当前登录用户
        force: 是否强制锁定（即使已锁定也会更新锁定状态）
        
    Returns:
        布尔值，表示是否成功锁定
    """
    if user_id is None and current_user.is_authenticated:
        user_id = current_user.id
    
    project = Project.query.get(project_id)
    if not project:
        logger.error(f"项目不存在: {project_id}")
        return False
    
    # 如果项目已经被锁定，且不是强制锁定，则返回False
    if project.is_locked and not force:
        logger.warning(f"项目已被锁定: {project_id}, 原因: {project.locked_reason}")
        return False
    
    try:
        # 无论之前是否锁定，都设置新的锁定状态
        project.is_locked = True
        project.locked_reason = reason
        project.locked_by = user_id
        project.locked_at = datetime.now()
        
        db.session.commit()
        logger.info(f"项目已锁定: {project_id}, 原因: {reason}, 锁定人: {user_id}")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"锁定项目失败: {project_id}, 错误: {str(e)}")
        return False


def unlock_project(project_id, user_id=None):
    """解锁项目
    
    Args:
        project_id: 项目ID
        user_id: 解锁人ID，默认为当前登录用户
        
    Returns:
        布尔值，表示是否成功解锁
    """
    if user_id is None and current_user.is_authenticated:
        user_id = current_user.id
    
    project = Project.query.get(project_id)
    if not project:
        logger.error(f"项目不存在: {project_id}")
        return False
    
    # 如果项目未被锁定，返回True
    if not project.is_locked:
        return True
    
    try:
        # 记录原始锁定信息到日志
        logger.info(f"解锁项目: {project_id}, 原始锁定人: {project.locked_by}, 原因: {project.locked_reason}, 解锁人: {user_id}")
        
        # 清除锁定状态
        project.is_locked = False
        project.locked_reason = None
        project.locked_by = None
        project.locked_at = None
        
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"解锁项目失败: {project_id}, 错误: {str(e)}")
        return False


def is_project_editable(project_id, user_id=None):
    """检查项目是否可编辑
    
    Args:
        project_id: 项目ID
        user_id: 用户ID，默认为当前登录用户
        
    Returns:
        布尔值和原因说明元组 (editable, reason)
    """
    if user_id is None and current_user.is_authenticated:
        user_id = current_user.id
        is_admin = current_user.role == 'admin'
    else:
        from app.models.user import User
        user = User.query.get(user_id)
        is_admin = user and user.role == 'admin'
    
    project = Project.query.get(project_id)
    if not project:
        return False, "项目不存在"
    
    # 管理员可以编辑被锁定的项目
    if project.is_locked and not is_admin:
        from app.models.user import User
        locker = User.query.get(project.locked_by) if project.locked_by else None
        locker_name = locker.username if locker else "未知用户"
        
        # 安全的日期格式化
        lock_time = "未知时间"
        if project.locked_at:
            try:
                if isinstance(project.locked_at, str):
                    from datetime import datetime
                    dt = datetime.fromisoformat(project.locked_at.replace('Z', '+00:00'))
                    lock_time = dt.strftime('%Y-%m-%d %H:%M')
                else:
                    lock_time = project.locked_at.strftime('%Y-%m-%d %H:%M')
            except (ValueError, AttributeError) as e:
                lock_time = str(project.locked_at)
        
        return False, f"项目已被锁定，原因: {project.locked_reason}, 锁定人: {locker_name}, 时间: {lock_time}"
    
    # 检查项目是否已签约（已签约的项目不允许编辑）
    if project.current_stage == 'signed':
        return False, "项目已签约，不允许编辑"
    
    # 检查项目是否存在授权编号（有授权编号的项目不允许修改某些字段）
    if project.authorization_code:
        return True, "项目已授权，某些字段不可修改"

    return True, None


# =============================================================================
# 项目类型按创建人角色锁定 (2026-06-24)
# 规则:
#   - 销售/渠道/服务三类角色建项目时, project_type 由角色决定且本人不可选/不可改;
#   - 其他角色(产品经理/方案经理/市场等)建项目时可自由选择类型;
#   - 管理员与商务助理始终可自由选择/修改类型(覆盖锁定),且为唯一可在编辑期改类型的角色。
# project_type 字典(sales_focus 销售 / channel_follow 渠道 / business_opportunity 服务)
# 在 CN/SG 完全一致, 角色码也通用, 故逻辑全通用、无需按区域分叉;
# SG 没有 dealer/customer_sales/service_manager 用户, 对应分支自然不触发。
# =============================================================================

# 角色 -> 强制项目类型 (project_type 字典 key)
ROLE_FORCED_PROJECT_TYPE = {
    'sales_manager':   'sales_focus',           # 区域销售 → 销售
    'sales_director':  'sales_focus',           # 营销总监 → 销售
    'channel_manager': 'channel_follow',        # 渠道销售 → 渠道
    'dealer':          'channel_follow',        # 代理商 → 渠道 (SG 无此角色)
    'customer_sales':  'business_opportunity',  # 客户销售 → 服务 (SG 无此角色)
    'service_manager': 'business_opportunity',  # 服务经理 → 服务 (SG 无此角色)
}

# 始终可自由选择/修改项目类型的角色(覆盖锁定)
PROJECT_TYPE_OVERRIDE_ROLES = {'admin', 'business_admin'}


def _role_of(user):
    return (getattr(user, 'role', None) or '').strip()


def forced_project_type_for(user):
    """返回该用户被强制锁定的项目类型; None 表示可自由选择。
    admin / business_admin 永远可选(返回 None)。"""
    role = _role_of(user)
    if role in PROJECT_TYPE_OVERRIDE_ROLES:
        return None
    return ROLE_FORCED_PROJECT_TYPE.get(role)


def can_edit_project_type(user):
    """项目建立后能否修改 project_type —— 仅管理员与商务助理。"""
    return _role_of(user) in PROJECT_TYPE_OVERRIDE_ROLES


def resolve_create_project_type(user, submitted):
    """创建项目时确定最终 project_type。
    锁定角色 → 忽略提交值并返回强制类型;
    其他角色 / admin / business_admin → 返回提交值原样(合法性由调用方校验)。"""
    forced = forced_project_type_for(user)
    return forced if forced is not None else submitted


def resolve_update_project_type(user, current_value, submitted):
    """更新项目时确定最终 project_type。
    仅 admin / business_admin 可改; 其他人一律保持原值。"""
    return submitted if can_edit_project_type(user) else current_value 