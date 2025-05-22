#!/usr/bin/env python3
# 直接执行SQL添加字段
# 使用方法: python3 add_fields.py

from app import create_app, db
from sqlalchemy import text
import sys

def add_fields():
    """直接添加字段"""
    app = create_app()
    with app.app_context():
        conn = db.engine.connect()
        
        try:
            # 为项目表添加锁定相关字段
            print('正在添加项目表锁定相关字段...')
            
            # 添加is_locked字段
            conn.execute(text('ALTER TABLE projects ADD COLUMN IF NOT EXISTS is_locked BOOLEAN DEFAULT FALSE'))
            print('projects.is_locked字段已添加')
            
            # 添加locked_reason字段
            conn.execute(text('ALTER TABLE projects ADD COLUMN IF NOT EXISTS locked_reason VARCHAR(100)'))
            print('projects.locked_reason字段已添加')
            
            # 添加locked_by字段
            conn.execute(text('ALTER TABLE projects ADD COLUMN IF NOT EXISTS locked_by INTEGER REFERENCES users(id)'))
            print('projects.locked_by字段已添加')
            
            # 添加locked_at字段
            conn.execute(text('ALTER TABLE projects ADD COLUMN IF NOT EXISTS locked_at TIMESTAMP'))
            print('projects.locked_at字段已添加')
            
            # 提交事务
            conn.commit()
            print('所有操作已提交')
        except Exception as e:
            print(f'错误: {str(e)}')
            return False
            
        return True

if __name__ == "__main__":
    success = add_fields()
    sys.exit(0 if success else 1) 