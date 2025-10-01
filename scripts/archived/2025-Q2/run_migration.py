#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库迁移脚本执行器
用于创建审批流程相关的表
"""

import os
import sys
import logging
import enum
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, Enum
from flask_migrate import Migrate
from config import Config

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建一个简化版应用实例，仅用于迁移
app = Flask(__name__)
app.config.from_object(Config)

# 初始化数据库
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# 定义枚举类型
class ApprovalStatus(enum.Enum):
    """审批状态枚举"""
    PENDING = "pending"    # 审批中
    APPROVED = "approved"  # 已通过
    REJECTED = "rejected"  # 已拒绝

class ApprovalAction(enum.Enum):
    """审批动作枚举"""
    APPROVE = "approve"  # 同意
    REJECT = "reject"    # 拒绝

# 应用上下文中运行
with app.app_context():
    # 导入所有模型以确保它们被注册
    from app.models.user import User, Permission
    from app.models.customer import Company, Contact
    from app.models.project import Project
    from app.models.action import Action
    from app.models.quotation import Quotation
    from app.models.product import Product
    
    # 直接创建审批流程相关的表
    class ApprovalProcessTemplate(db.Model):
        """审批流程模板"""
        __tablename__ = "approval_process_template"
    
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False, comment="流程名称")
        object_type = db.Column(db.String(50), nullable=False, comment="适用对象（如 quotation）")
        is_active = db.Column(db.Boolean, default=True, comment="是否启用")
        created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, comment="创建人账号ID")
        created_at = db.Column(db.DateTime, default=db.func.now(), comment="创建时间")
    
    class ApprovalStep(db.Model):
        """流程步骤"""
        __tablename__ = "approval_step"
    
        id = db.Column(db.Integer, primary_key=True)
        process_id = db.Column(db.Integer, db.ForeignKey("approval_process_template.id"), nullable=False, comment="所属流程模板")
        step_order = db.Column(db.Integer, nullable=False, comment="流程顺序")
        approver_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, comment="审批人账号ID")
        step_name = db.Column(db.String(100), nullable=False, comment="步骤说明（如\"财务审批\"）")
        send_email = db.Column(db.Boolean, default=True, comment="是否发送邮件通知")
    
    class ApprovalInstance(db.Model):
        """流程实例"""
        __tablename__ = "approval_instance"
    
        id = db.Column(db.Integer, primary_key=True)
        process_id = db.Column(db.Integer, db.ForeignKey("approval_process_template.id"), nullable=False, comment="流程模板ID")
        object_id = db.Column(db.Integer, nullable=False, comment="对应单据ID")
        object_type = db.Column(db.String(50), nullable=False, comment="单据类型（如 project）")
        current_step = db.Column(db.Integer, default=1, comment="当前步骤序号")
        status = db.Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING, comment="状态")
        started_at = db.Column(db.DateTime, default=db.func.now(), comment="流程发起时间")
        ended_at = db.Column(db.DateTime, comment="审批完成时间")
        created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, comment="发起人ID")
    
    class ApprovalRecord(db.Model):
        """审批记录"""
        __tablename__ = "approval_record"
    
        id = db.Column(db.Integer, primary_key=True)
        instance_id = db.Column(db.Integer, db.ForeignKey("approval_instance.id"), nullable=False, comment="审批流程实例")
        step_id = db.Column(db.Integer, db.ForeignKey("approval_step.id"), nullable=False, comment="流程步骤ID")
        approver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, comment="审批人ID")
        action = db.Column(Enum(ApprovalAction), nullable=False, comment="同意/拒绝")
        comment = db.Column(db.Text, comment="审批意见")
        timestamp = db.Column(db.DateTime, default=db.func.now(), comment="审批时间")
    
    # 创建表
    db.create_all()
    
    print("审批流程相关的数据库表已创建完成！")
    
    # 测试数据库连接
    try:
        db.session.execute(text('SELECT 1'))
        logger.info("数据库连接成功")
    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
        sys.exit(1) 