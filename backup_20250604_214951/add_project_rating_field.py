#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为projects表添加rating字段
修复云端数据库缺少rating字段的问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def add_project_rating_field():
    """为projects表添加rating字段"""
    app = create_app()
    
    with app.app_context():
        print("为projects表添加rating字段...")
        
        try:
            # 检查字段是否已存在
            check_column_sql = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'projects' AND column_name = 'rating';
            """
            result = db.session.execute(text(check_column_sql)).fetchone()
            
            if result:
                print("✅ rating字段已存在，跳过添加")
                return
            
            # 添加rating字段
            add_column_sql = """
            ALTER TABLE projects 
            ADD COLUMN rating INTEGER NULL 
            CHECK (rating IS NULL OR (rating >= 1 AND rating <= 5));
            """
            
            # 添加字段注释
            add_comment_sql = """
            COMMENT ON COLUMN projects.rating IS '项目评分(1-5星)，NULL表示未评分';
            """
            
            # 执行添加字段
            db.session.execute(text(add_column_sql))
            print("✅ rating字段添加成功")
            
            # 添加注释
            db.session.execute(text(add_comment_sql))
            print("✅ 字段注释添加成功")
            
            # 提交事务
            db.session.commit()
            print("✅ projects表rating字段迁移完成")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 迁移失败: {str(e)}")
            raise

if __name__ == '__main__':
    add_project_rating_field() 