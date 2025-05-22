from flask import current_app
from flask_login import current_user
from app import db
from app.models.project import Project
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def lock_project(project_id, reason="审批流程锁定", user_id=None):
    """锁定项目，防止编辑
    
    Args:
        project_id: 项目ID
        reason: 锁定原因
        user_id: 锁定人ID，默认为当前登录用户
        
    Returns:
        布尔值，表示是否成功锁定
    """
    if user_id is None and current_user.is_authenticated:
        user_id = current_user.id
    
    project = Project.query.get(project_id)
    if not project:
        logger.error(f"项目不存在: {project_id}")
        return False
    
    # 如果项目已经被锁定，返回False
    if project.is_locked:
        logger.warning(f"项目已被锁定: {project_id}, 原因: {project.locked_reason}")
        return False
    
    try:
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
        
        lock_time = project.locked_at.strftime('%Y-%m-%d %H:%M') if project.locked_at else "未知时间"
        
        return False, f"项目已被锁定，原因: {project.locked_reason}, 锁定人: {locker_name}, 时间: {lock_time}"
    
    # 检查项目是否存在授权编号（有授权编号的项目不允许修改某些字段）
    if project.authorization_code:
        return True, "项目已授权，某些字段不可修改"
    
    return True, None 