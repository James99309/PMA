#!/usr/bin/env python3
# 用于直接添加action_type和action_params字段到approval_step表
# 使用方法: python3 add_approval_action_type.py

from app import create_app, db
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey, text
import sys

def add_approval_action_type():
    app = create_app()
    with app.app_context():
        try:
            # 连接数据库
            connection = db.engine.connect()
            
            # 检查approval_step表是否有action_type字段
            result = connection.execute(text("SELECT column_name FROM information_schema.columns "
                                       "WHERE table_name='approval_step' AND column_name='action_type'"))
            has_action_type = result.scalar() is not None
            
            # 如果没有action_type字段，则添加
            if not has_action_type:
                print("正在添加approval_step.action_type字段...")
                connection.execute(text("ALTER TABLE approval_step ADD COLUMN action_type VARCHAR(50)"))
                print("approval_step.action_type字段添加成功")
            else:
                print("approval_step.action_type字段已存在")
            
            # 检查approval_step表是否有action_params字段
            result = connection.execute(text("SELECT column_name FROM information_schema.columns "
                                       "WHERE table_name='approval_step' AND column_name='action_params'"))
            has_action_params = result.scalar() is not None
            
            # 如果没有action_params字段，则添加
            if not has_action_params:
                print("正在添加approval_step.action_params字段...")
                connection.execute(text("ALTER TABLE approval_step ADD COLUMN action_params JSON"))
                print("approval_step.action_params字段添加成功")
            else:
                print("approval_step.action_params字段已存在")
            
            # 检查projects表是否有is_locked字段
            result = connection.execute(text("SELECT column_name FROM information_schema.columns "
                                       "WHERE table_name='projects' AND column_name='is_locked'"))
            has_is_locked = result.scalar() is not None
            
            # 如果没有is_locked字段，则添加
            if not has_is_locked:
                print("正在添加projects.is_locked字段...")
                connection.execute(text("ALTER TABLE projects ADD COLUMN is_locked BOOLEAN DEFAULT FALSE"))
                print("projects.is_locked字段添加成功")
            else:
                print("projects.is_locked字段已存在")
            
            # 检查projects表是否有locked_reason字段
            result = connection.execute(text("SELECT column_name FROM information_schema.columns "
                                       "WHERE table_name='projects' AND column_name='locked_reason'"))
            has_locked_reason = result.scalar() is not None
            
            # 如果没有locked_reason字段，则添加
            if not has_locked_reason:
                print("正在添加projects.locked_reason字段...")
                connection.execute(text("ALTER TABLE projects ADD COLUMN locked_reason VARCHAR(100)"))
                print("projects.locked_reason字段添加成功")
            else:
                print("projects.locked_reason字段已存在")
            
            # 检查projects表是否有locked_by字段
            result = connection.execute(text("SELECT column_name FROM information_schema.columns "
                                       "WHERE table_name='projects' AND column_name='locked_by'"))
            has_locked_by = result.scalar() is not None
            
            # 如果没有locked_by字段，则添加
            if not has_locked_by:
                print("正在添加projects.locked_by字段...")
                connection.execute(text("ALTER TABLE projects ADD COLUMN locked_by INTEGER REFERENCES users(id)"))
                print("projects.locked_by字段添加成功")
            else:
                print("projects.locked_by字段已存在")
            
            # 检查projects表是否有locked_at字段
            result = connection.execute(text("SELECT column_name FROM information_schema.columns "
                                       "WHERE table_name='projects' AND column_name='locked_at'"))
            has_locked_at = result.scalar() is not None
            
            # 如果没有locked_at字段，则添加
            if not has_locked_at:
                print("正在添加projects.locked_at字段...")
                connection.execute(text("ALTER TABLE projects ADD COLUMN locked_at TIMESTAMP"))
                print("projects.locked_at字段添加成功")
            else:
                print("projects.locked_at字段已存在")
            
            connection.close()
            print("数据库字段已全部添加完成")
            return True
        
        except Exception as e:
            print(f"错误: {str(e)}")
            return False

if __name__ == "__main__":
    result = add_approval_action_type()
    sys.exit(0 if result else 1) 