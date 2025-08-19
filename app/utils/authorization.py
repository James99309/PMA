"""
项目授权编号生成工具

此模块提供了用于生成标准化项目授权编号的函数。
授权编号格式为 {前缀}{年份}{月份}-{序号}，例如：SPJ202304-001
"""

from datetime import datetime
from flask import current_app
import re
import logging

logger = logging.getLogger(__name__)

# 项目类型对应的授权编号前缀（支持中英文项目类型）
PROJECT_TYPE_PREFIXES = {
    # 中文项目类型
    '销售重点': 'SPJ',
    '渠道跟进': 'CPJ',
    '客户服务': 'APJ',  # 客户服务类型项目（原业务机会），使用APJ前缀
    # 英文项目类型
    'sales_focus': 'SPJ',
    'channel_follow': 'CPJ',
    'business_opportunity': 'APJ',
    'sales_key': 'SPJ'  # 销售重点的另一种英文表示
}

def generate_authorization_code(project_type):
    """
    生成项目的授权编号
    
    Args:
        project_type (str): 项目类型，可以是'销售重点'、'渠道跟进'、'业务机会'或'客户服务'
    
    Returns:
        str: 格式化的授权编号，格式为{前缀}{年份}{月份}-{序号}，例如 SPJ202304-001
             如果项目类型不支持授权，返回None
    """
    # 在函数内部导入Project，避免循环导入
    from app.models.project import Project
    
    # 检查项目类型是否支持授权
    if project_type not in PROJECT_TYPE_PREFIXES:
        logger.warning(f"不支持的项目类型: {project_type}")
        return None
        
    prefix = PROJECT_TYPE_PREFIXES[project_type]
    current_date = datetime.now()
    year_month = current_date.strftime('%Y%m')
    
    # 查找当前年月的最大序号
    last_project = Project.query.filter(
        Project.authorization_code.like(f'{prefix}{year_month}-%')
    ).order_by(Project.authorization_code.desc()).first()
    
    # 提取序号并递增
    if last_project and last_project.authorization_code:
        match = re.search(r'-(\d{3})$', last_project.authorization_code)
        if match:
            seq_num = int(match.group(1)) + 1
        else:
            logger.warning(f"无法解析现有授权编号格式: {last_project.authorization_code}")
            seq_num = 1
    else:
        seq_num = 1
        
    # 格式化授权编号: 前缀 + 年月 + 序号
    authorization_code = f"{prefix}{year_month}-{str(seq_num).zfill(3)}"
    logger.info(f"生成授权编号: {authorization_code}")
    
    return authorization_code


def generate_project_authorization_code(project_type, project_id, approver_id):
    """
    生成项目授权编号（专项授权）
    
    Args:
        project_type (str): 项目类型
        project_id (int): 项目ID
        approver_id (int): 审批人ID
    
    Returns:
        str: 格式化的项目授权编号，格式为SPJ{YYYYMM}-{XX}
    """
    # 在函数内部导入Project，避免循环导入
    from app.models.project import Project
    
    # 项目授权固定使用SPJ前缀
    prefix = 'SPJ'
    current_date = datetime.now()
    year_month = current_date.strftime('%Y%m')
    
    # 查找当前年月的最大序号
    last_project = Project.query.filter(
        Project.authorization_code.like(f'{prefix}{year_month}-%')
    ).order_by(Project.authorization_code.desc()).first()
    
    # 提取序号并递增
    if last_project and last_project.authorization_code:
        # 优先匹配新格式（2位序号）
        match = re.search(r'-(\d{2})$', last_project.authorization_code)
        if not match:
            # 向后兼容旧格式（3位序号）
            match = re.search(r'-(\d{3})$', last_project.authorization_code)
        
        if match:
            seq_num = int(match.group(1)) + 1
        else:
            seq_num = 1
    else:
        seq_num = 1
        
    authorization_code = f"{prefix}{year_month}-{str(seq_num).zfill(2)}"
    logger.info(f"生成项目授权编号: {authorization_code}, 项目ID: {project_id}, 审批人ID: {approver_id}")
    
    return authorization_code


def generate_channel_authorization_code(project_type, project_id, approver_id):
    """
    生成渠道授权编号（专项授权）
    
    Args:
        project_type (str): 项目类型
        project_id (int): 项目ID
        approver_id (int): 审批人ID
    
    Returns:
        str: 格式化的渠道授权编号，格式为CPJ{YYYYMM}-{XX}
    """
    # 在函数内部导入Project，避免循环导入
    from app.models.project import Project
    
    # 渠道授权固定使用CPJ前缀
    prefix = 'CPJ'
    current_date = datetime.now()
    year_month = current_date.strftime('%Y%m')
    
    # 查找当前年月的最大序号
    last_project = Project.query.filter(
        Project.authorization_code.like(f'{prefix}{year_month}-%')
    ).order_by(Project.authorization_code.desc()).first()
    
    # 提取序号并递增
    if last_project and last_project.authorization_code:
        # 优先匹配新格式（2位序号）
        match = re.search(r'-(\d{2})$', last_project.authorization_code)
        if not match:
            # 向后兼容旧格式（3位序号）
            match = re.search(r'-(\d{3})$', last_project.authorization_code)
        
        if match:
            seq_num = int(match.group(1)) + 1
        else:
            seq_num = 1
    else:
        seq_num = 1
        
    authorization_code = f"{prefix}{year_month}-{str(seq_num).zfill(2)}"
    logger.info(f"生成渠道授权编号: {authorization_code}, 项目ID: {project_id}, 审批人ID: {approver_id}")
    
    return authorization_code


def generate_business_authorization_code(project_type, project_id, approver_id):
    """
    生成业务授权编号（专项授权）- 保留向后兼容
    
    Args:
        project_type (str): 项目类型
        project_id (int): 项目ID
        approver_id (int): 审批人ID
    
    Returns:
        str: 格式化的业务授权编号，格式为APJ{YYYYMM}-{XX}
    """
    # 重定向到客服授权函数
    return generate_customer_service_authorization_code(project_type, project_id, approver_id)


def generate_customer_service_authorization_code(project_type, project_id, approver_id):
    """
    生成客服授权编号（专项授权）
    
    Args:
        project_type (str): 项目类型
        project_id (int): 项目ID
        approver_id (int): 审批人ID
    
    Returns:
        str: 格式化的客服授权编号，格式为APJ{YYYYMM}-{XX}
    """
    # 在函数内部导入Project，避免循环导入
    from app.models.project import Project
    
    # 客服授权固定使用APJ前缀
    prefix = 'APJ'
    current_date = datetime.now()
    year_month = current_date.strftime('%Y%m')
    
    # 查找当前年月的最大序号
    last_project = Project.query.filter(
        Project.authorization_code.like(f'{prefix}{year_month}-%')
    ).order_by(Project.authorization_code.desc()).first()
    
    # 提取序号并递增
    if last_project and last_project.authorization_code:
        # 优先匹配新格式（2位序号）
        match = re.search(r'-(\d{2})$', last_project.authorization_code)
        if not match:
            # 向后兼容旧格式（3位序号）
            match = re.search(r'-(\d{3})$', last_project.authorization_code)
        
        if match:
            seq_num = int(match.group(1)) + 1
        else:
            seq_num = 1
    else:
        seq_num = 1
        
    authorization_code = f"{prefix}{year_month}-{str(seq_num).zfill(2)}"
    logger.info(f"生成客服授权编号: {authorization_code}, 项目ID: {project_id}, 审批人ID: {approver_id}")
    
    return authorization_code 