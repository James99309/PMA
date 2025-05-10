"""
添加项目阶段历史记录表迁移脚本
用于记录项目阶段变更历史，支持阶段趋势分析
"""

from app import db
from flask import current_app
from sqlalchemy import Table, Column, Integer, String, DateTime, Text, ForeignKey, MetaData
from sqlalchemy.sql import func

def upgrade():
    """升级数据库，添加项目阶段历史记录表"""
    metadata = MetaData(bind=db.engine)
    
    # 创建项目阶段历史记录表
    project_stage_history = Table(
        'project_stage_history',
        metadata,
        Column('id', Integer, primary_key=True),
        Column('project_id', Integer, ForeignKey('projects.id'), nullable=False, index=True),
        Column('from_stage', String(64), nullable=True),
        Column('to_stage', String(64), nullable=False),
        Column('change_date', DateTime, nullable=False),
        Column('change_week', Integer, nullable=True),
        Column('change_month', Integer, nullable=True),
        Column('change_year', Integer, nullable=True),
        Column('remarks', Text, nullable=True),
        Column('created_at', DateTime, server_default=func.now()),
    )
    
    # 创建表
    project_stage_history.create(db.engine, checkfirst=True)
    
    # 创建从项目阶段描述中提取历史数据的函数或触发器
    # 这里可以添加从现有项目的stage_description字段中提取历史记录的代码
    # 由于可能需要复杂的文本解析，此处仅创建表结构
    
    current_app.logger.info("已成功创建项目阶段历史记录表")

def downgrade():
    """回滚数据库，删除项目阶段历史记录表"""
    metadata = MetaData(bind=db.engine)
    
    # 删除表
    project_stage_history = Table('project_stage_history', metadata, autoload=True)
    project_stage_history.drop(db.engine, checkfirst=True)
    
    current_app.logger.info("已成功删除项目阶段历史记录表") 