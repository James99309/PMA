#!/usr/bin/env python3
"""
解决方案经理邮件通知助手函数
"""

from app.models.notification import SolutionManagerEmailSettings
from app.models.user import User
from app.utils.email import send_email
import logging

logger = logging.getLogger(__name__)

def notify_solution_managers_quotation_created(quotation):
    """
    通知解决方案经理有新的报价单创建
    
    Args:
        quotation: 报价单对象
    """
    try:
        # 获取所有启用了报价单新建通知的解决方案经理
        settings_list = SolutionManagerEmailSettings.query.filter_by(quotation_created=True).all()
        
        if not settings_list:
            logger.info("没有解决方案经理启用了报价单新建通知")
            return
        
        # 获取用户信息
        user_ids = [s.user_id for s in settings_list]
        users = User.query.filter(User.id.in_(user_ids), User.role == 'solution_manager').all()
        
        if not users:
            logger.info("没有找到有效的解决方案经理用户")
            return
        
        # 准备邮件内容
        subject = f"新报价单创建通知 - {quotation.quotation_number}"
        
        # 获取项目信息
        project_info = ""
        if quotation.project:
            project_info = f"项目：{quotation.project.project_name} (ID: {quotation.project.id})"
        
        body = f"""
        尊敬的解决方案经理，
        
        系统中有新的报价单创建：
        
        报价单编号：{quotation.quotation_number}
        {project_info}
        创建人：{quotation.owner.real_name or quotation.owner.username if quotation.owner else '未知'}
        创建时间：{quotation.created_at.strftime('%Y-%m-%d %H:%M:%S') if quotation.created_at else '未知'}
        
        请及时关注并处理。
        
        此邮件由系统自动发送，请勿回复。
        """
        
        # 发送邮件给每个解决方案经理
        for user in users:
            if user.email:
                try:
                    send_email(
                        subject=subject,
                        recipient=user.email,
                        content=body
                    )
                    logger.info(f"报价单创建通知已发送给解决方案经理 {user.username}")
                except Exception as e:
                    logger.error(f"发送邮件给 {user.username} 失败: {str(e)}")
            else:
                logger.warning(f"解决方案经理 {user.username} 没有设置邮箱地址")
                
    except Exception as e:
        logger.error(f"通知解决方案经理报价单创建失败: {str(e)}")

def notify_solution_managers_quotation_updated(quotation):
    """
    通知解决方案经理报价单已更新
    
    Args:
        quotation: 报价单对象
    """
    try:
        # 获取所有启用了报价单更新通知的解决方案经理
        settings_list = SolutionManagerEmailSettings.query.filter_by(quotation_updated=True).all()
        
        if not settings_list:
            logger.info("没有解决方案经理启用了报价单更新通知")
            return
        
        # 获取用户信息
        user_ids = [s.user_id for s in settings_list]
        users = User.query.filter(User.id.in_(user_ids), User.role == 'solution_manager').all()
        
        if not users:
            logger.info("没有找到有效的解决方案经理用户")
            return
        
        # 准备邮件内容
        subject = f"报价单更新通知 - {quotation.quotation_number}"
        
        # 获取项目信息
        project_info = ""
        if quotation.project:
            project_info = f"项目：{quotation.project.project_name} (ID: {quotation.project.id})"
        
        body = f"""
        尊敬的解决方案经理，
        
        系统中的报价单已更新：
        
        报价单编号：{quotation.quotation_number}
        {project_info}
        更新时间：{quotation.updated_at.strftime('%Y-%m-%d %H:%M:%S')}
        
        请及时查看更新内容。
        
        此邮件由系统自动发送，请勿回复。
        """
        
        # 发送邮件给每个解决方案经理
        for user in users:
            if user.email:
                try:
                    send_email(
                        subject=subject,
                        recipient=user.email,
                        content=body
                    )
                    logger.info(f"报价单更新通知已发送给解决方案经理 {user.username}")
                except Exception as e:
                    logger.error(f"发送邮件给 {user.username} 失败: {str(e)}")
            else:
                logger.warning(f"解决方案经理 {user.username} 没有设置邮箱地址")
                
    except Exception as e:
        logger.error(f"通知解决方案经理报价单更新失败: {str(e)}")

def notify_solution_managers_project_created(project):
    """
    通知解决方案经理有新的项目创建
    
    Args:
        project: 项目对象
    """
    try:
        # 获取所有启用了项目新建通知的解决方案经理
        settings_list = SolutionManagerEmailSettings.query.filter_by(project_created=True).all()
        
        if not settings_list:
            logger.info("没有解决方案经理启用了项目新建通知")
            return
        
        # 获取用户信息
        user_ids = [s.user_id for s in settings_list]
        users = User.query.filter(User.id.in_(user_ids), User.role == 'solution_manager').all()
        
        if not users:
            logger.info("没有找到有效的解决方案经理用户")
            return
        
        # 准备邮件内容
        subject = f"新项目创建通知 - {project.project_name}"
        
        body = f"""
        尊敬的解决方案经理，
        
        系统中有新的项目创建：
        
        项目名称：{project.project_name}
        项目ID：{project.id}
        创建人：{project.owner.real_name or project.owner.username if project.owner else '未知'}
        创建时间：{project.created_at.strftime('%Y-%m-%d %H:%M:%S') if project.created_at else '未知'}
        项目阶段：{project.current_stage or '未设置'}
        
        请及时关注项目进展。
        
        此邮件由系统自动发送，请勿回复。
        """
        
        # 发送邮件给每个解决方案经理
        for user in users:
            if user.email:
                try:
                    send_email(
                        subject=subject,
                        recipient=user.email,
                        content=body
                    )
                    logger.info(f"项目创建通知已发送给解决方案经理 {user.username}")
                except Exception as e:
                    logger.error(f"发送邮件给 {user.username} 失败: {str(e)}")
            else:
                logger.warning(f"解决方案经理 {user.username} 没有设置邮箱地址")
                
    except Exception as e:
        logger.error(f"通知解决方案经理项目创建失败: {str(e)}")

def notify_solution_managers_project_stage_changed(project, old_stage, new_stage):
    """
    通知解决方案经理项目阶段已推进
    
    Args:
        project: 项目对象
        old_stage: 原阶段
        new_stage: 新阶段
    """
    try:
        # 获取所有启用了项目阶段推进通知的解决方案经理
        settings_list = SolutionManagerEmailSettings.query.filter_by(project_stage_changed=True).all()
        
        if not settings_list:
            logger.info("没有解决方案经理启用了项目阶段推进通知")
            return
        
        # 获取用户信息
        user_ids = [s.user_id for s in settings_list]
        users = User.query.filter(User.id.in_(user_ids), User.role == 'solution_manager').all()
        
        if not users:
            logger.info("没有找到有效的解决方案经理用户")
            return
        
        # 准备邮件内容
        subject = f"项目阶段推进通知 - {project.project_name}"
        
        body = f"""
        尊敬的解决方案经理，
        
        项目阶段已发生变更：
        
        项目名称：{project.project_name}
        项目ID：{project.id}
        原阶段：{old_stage or '未设置'}
        新阶段：{new_stage or '未设置'}
        更新时间：{project.updated_at.strftime('%Y-%m-%d %H:%M:%S') if project.updated_at else '未知'}
        
        请及时关注项目进展。
        
        此邮件由系统自动发送，请勿回复。
        """
        
        # 发送邮件给每个解决方案经理
        for user in users:
            if user.email:
                try:
                    send_email(
                        subject=subject,
                        recipient=user.email,
                        content=body
                    )
                    logger.info(f"项目阶段推进通知已发送给解决方案经理 {user.username}")
                except Exception as e:
                    logger.error(f"发送邮件给 {user.username} 失败: {str(e)}")
            else:
                logger.warning(f"解决方案经理 {user.username} 没有设置邮箱地址")
                
    except Exception as e:
        logger.error(f"通知解决方案经理项目阶段推进失败: {str(e)}")

def get_solution_manager_settings(user_id):
    """
    获取解决方案经理的邮件设置
    
    Args:
        user_id: 用户ID
        
    Returns:
        SolutionManagerEmailSettings对象或None
    """
    try:
        return SolutionManagerEmailSettings.query.filter_by(user_id=user_id).first()
    except Exception as e:
        logger.error(f"获取解决方案经理设置失败: {str(e)}")
        return None

def create_default_solution_manager_settings(user_id):
    """
    为解决方案经理创建默认邮件设置
    
    Args:
        user_id: 用户ID
        
    Returns:
        SolutionManagerEmailSettings对象
    """
    try:
        from app.extensions import db
        
        settings = SolutionManagerEmailSettings(
            user_id=user_id,
            quotation_created=True,
            quotation_updated=True,
            project_created=True,
            project_stage_changed=True
        )
        
        db.session.add(settings)
        db.session.commit()
        
        logger.info(f"为用户 {user_id} 创建了默认解决方案经理邮件设置")
        return settings
        
    except Exception as e:
        logger.error(f"创建默认解决方案经理设置失败: {str(e)}")
        from app.extensions import db
        db.session.rollback()
        return None 