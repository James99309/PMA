#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
字典数据初始化脚本
用于将现有的用户角色等硬编码选项转换为字典表数据
"""

import logging
from app import db
from app.models.dictionary import Dictionary
from app.models.user import User
from sqlalchemy import func

# 配置日志
logger = logging.getLogger(__name__)

# 角色字典的预设选项
DEFAULT_ROLES = [
    {"key": "admin", "value": "系统管理员", "sort_order": 10},
    {"key": "user", "value": "普通用户", "sort_order": 20},
    {"key": "sales", "value": "销售人员", "sort_order": 30},
    {"key": "product_manager", "value": "产品经理", "sort_order": 40},
    {"key": "solution_manager", "value": "解决方案经理", "sort_order": 50},
    {"key": "service", "value": "服务", "sort_order": 60},
    {"key": "service_manager", "value": "服务经理", "sort_order": 70},
    {"key": "channel_manager", "value": "渠道经理", "sort_order": 80},
    {"key": "sales_director", "value": "营销总监", "sort_order": 90},
    {"key": "dealer", "value": "代理商", "sort_order": 100}
]

def init_dictionary():
    """初始化字典数据"""
    try:
        # 初始化角色字典
        init_role_dictionary()
        logger.info("字典数据初始化完成")
        return True
    except Exception as e:
        logger.error(f"字典数据初始化失败: {str(e)}")
        return False

def init_role_dictionary():
    """初始化角色字典数据"""
    logger.info("开始初始化角色字典...")
    
    # 获取现有角色
    existing_roles = Dictionary.query.filter_by(type='role').all()
    existing_keys = {role.key.lower() for role in existing_roles}
    
    # 查询当前所有使用的角色值
    current_roles = db.session.query(User.role).distinct().all()
    current_role_keys = {role[0].lower() for role in current_roles if role[0]}
    
    # 添加默认角色
    for role in DEFAULT_ROLES:
        role_key = role["key"].lower()
        
        # 如果角色已在字典中，跳过
        if role_key in existing_keys:
            continue
        
        # 添加新角色
        new_role = Dictionary(
            type='role',
            key=role["key"],
            value=role["value"],
            sort_order=role["sort_order"],
            is_active=True
        )
        db.session.add(new_role)
        logger.info(f"添加角色字典: {role['key']} - {role['value']}")
    
    # 添加系统中已使用但不在默认选项中的角色
    default_keys = {role["key"].lower() for role in DEFAULT_ROLES}
    for role_key in current_role_keys:
        if role_key and role_key not in default_keys and role_key not in existing_keys:
            # 查询使用该角色的第一个用户，获取角色名
            user = User.query.filter(func.lower(User.role) == role_key).first()
            if user and user.role:
                # 获取最大排序号
                max_order = db.session.query(func.max(Dictionary.sort_order)).filter(
                    Dictionary.type == 'role'
                ).scalar() or 0
                
                # 添加新角色到字典
                new_role = Dictionary(
                    type='role',
                    key=user.role,  # 使用用户中存储的原始大小写
                    value=user.role,  # 临时使用键为值，后续可手动修改
                    sort_order=max_order + 10,
                    is_active=True
                )
                db.session.add(new_role)
                logger.info(f"从用户数据添加角色字典: {user.role}")
    
    try:
        db.session.commit()
        logger.info(f"角色字典初始化完成，共 {len(DEFAULT_ROLES)} 个预设角色")
    except Exception as e:
        db.session.rollback()
        logger.error(f"角色字典初始化失败: {str(e)}")
        raise e 