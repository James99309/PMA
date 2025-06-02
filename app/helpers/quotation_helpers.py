"""
报价单相关帮助函数
"""

from app import db
from app.models.quotation import Quotation
from flask import current_app
from datetime import datetime


def lock_quotation(quotation_id, reason, user_id):
    """锁定报价单
    
    Args:
        quotation_id: 报价单ID
        reason: 锁定原因
        user_id: 锁定人ID
        
    Returns:
        布尔值，表示是否成功锁定
    """
    try:
        quotation = Quotation.query.get(quotation_id)
        if not quotation:
            current_app.logger.error(f"报价单不存在: {quotation_id}")
            return False
        
        if quotation.is_locked:
            current_app.logger.warning(f"报价单已被锁定: {quotation_id}")
            return True
        
        quotation.lock(reason, user_id)
        db.session.commit()
        
        current_app.logger.info(f"报价单已锁定: {quotation_id}, 原因: {reason}")
        return True
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"锁定报价单失败: {quotation_id}, 错误: {str(e)}")
        return False


def unlock_quotation(quotation_id, user_id):
    """解锁报价单
    
    Args:
        quotation_id: 报价单ID
        user_id: 解锁人ID
        
    Returns:
        布尔值，表示是否成功解锁
    """
    try:
        quotation = Quotation.query.get(quotation_id)
        if not quotation:
            current_app.logger.error(f"报价单不存在: {quotation_id}")
            return False
        
        if not quotation.is_locked:
            current_app.logger.warning(f"报价单未被锁定: {quotation_id}")
            return True
        
        quotation.unlock(user_id)
        db.session.commit()
        
        current_app.logger.info(f"报价单已解锁: {quotation_id}")
        return True
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"解锁报价单失败: {quotation_id}, 错误: {str(e)}")
        return False


def is_quotation_editable(quotation_id, user_id=None):
    """检查报价单是否可编辑
    
    Args:
        quotation_id: 报价单ID
        user_id: 用户ID
        
    Returns:
        布尔值，表示是否可编辑
    """
    try:
        quotation = Quotation.query.get(quotation_id)
        if not quotation:
            return False
        
        # 检查是否被锁定
        if quotation.is_locked:
            return False
        
        return True
        
    except Exception as e:
        current_app.logger.error(f"检查报价单编辑权限失败: {quotation_id}, 错误: {str(e)}")
        return False


def get_quotation_detail_fields():
    """获取报价单明细字段列表
    
    Returns:
        字段列表
    """
    return [
        'product_name',      # 产品名称
        'product_model',     # 产品型号
        'product_desc',      # 产品描述
        'brand',            # 品牌
        'unit',             # 单位
        'quantity',         # 数量
        'discount',         # 折扣率
        'market_price',     # 市场价
        'unit_price',       # 单价
        'total_price',      # 总价
        'product_mn'        # 产品料号
    ]


def get_quotation_fields():
    """获取报价单字段列表
    
    Returns:
        字段列表
    """
    return [
        'quotation_number',  # 报价单编号
        'project_id',       # 项目ID
        'contact_id',       # 联系人ID
        'amount',           # 总金额
        'project_stage',    # 项目阶段
        'project_type'      # 项目类型
    ] 