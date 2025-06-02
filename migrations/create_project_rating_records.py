#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建项目评分记录表
记录每个用户对项目的评分操作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def create_project_rating_records_table():
    """创建项目评分记录表"""
    app = create_app()
    
    with app.app_context():
        print("创建项目评分记录表...")
        
        # 创建项目评分记录表
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS project_rating_records (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            rating INTEGER NOT NULL CHECK (rating = 1),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(project_id, user_id)
        );
        """
        
        # 添加索引
        create_indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_project_rating_records_project_id ON project_rating_records(project_id);",
            "CREATE INDEX IF NOT EXISTS idx_project_rating_records_user_id ON project_rating_records(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_project_rating_records_created_at ON project_rating_records(created_at);"
        ]
        
        # 添加注释
        add_comments_sql = [
            "COMMENT ON TABLE project_rating_records IS '项目评分记录表';",
            "COMMENT ON COLUMN project_rating_records.id IS '记录ID';",
            "COMMENT ON COLUMN project_rating_records.project_id IS '项目ID';",
            "COMMENT ON COLUMN project_rating_records.user_id IS '用户ID';",
            "COMMENT ON COLUMN project_rating_records.rating IS '评分值(固定为1星)';",
            "COMMENT ON COLUMN project_rating_records.created_at IS '创建时间';",
            "COMMENT ON COLUMN project_rating_records.updated_at IS '更新时间';"
        ]
        
        try:
            # 执行创建表
            db.session.execute(text(create_table_sql))
            print("✅ 项目评分记录表创建成功")
            
            # 执行创建索引
            for sql in create_indexes_sql:
                db.session.execute(text(sql))
            print("✅ 索引创建成功")
            
            # 执行添加注释
            for sql in add_comments_sql:
                db.session.execute(text(sql))
            print("✅ 注释添加成功")
            
            # 提交事务
            db.session.commit()
            print("✅ 项目评分记录表迁移完成")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 迁移失败: {str(e)}")
            raise

if __name__ == '__main__':
    create_project_rating_records_table() 
# -*- coding: utf-8 -*-
"""
创建项目评分记录表
记录每个用户对项目的评分操作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def create_project_rating_records_table():
    """创建项目评分记录表"""
    app = create_app()
    
    with app.app_context():
        print("创建项目评分记录表...")
        
        # 创建项目评分记录表
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS project_rating_records (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            rating INTEGER NOT NULL CHECK (rating = 1),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(project_id, user_id)
        );
        """
        
        # 添加索引
        create_indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_project_rating_records_project_id ON project_rating_records(project_id);",
            "CREATE INDEX IF NOT EXISTS idx_project_rating_records_user_id ON project_rating_records(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_project_rating_records_created_at ON project_rating_records(created_at);"
        ]
        
        # 添加注释
        add_comments_sql = [
            "COMMENT ON TABLE project_rating_records IS '项目评分记录表';",
            "COMMENT ON COLUMN project_rating_records.id IS '记录ID';",
            "COMMENT ON COLUMN project_rating_records.project_id IS '项目ID';",
            "COMMENT ON COLUMN project_rating_records.user_id IS '用户ID';",
            "COMMENT ON COLUMN project_rating_records.rating IS '评分值(固定为1星)';",
            "COMMENT ON COLUMN project_rating_records.created_at IS '创建时间';",
            "COMMENT ON COLUMN project_rating_records.updated_at IS '更新时间';"
        ]
        
        try:
            # 执行创建表
            db.session.execute(text(create_table_sql))
            print("✅ 项目评分记录表创建成功")
            
            # 执行创建索引
            for sql in create_indexes_sql:
                db.session.execute(text(sql))
            print("✅ 索引创建成功")
            
            # 执行添加注释
            for sql in add_comments_sql:
                db.session.execute(text(sql))
            print("✅ 注释添加成功")
            
            # 提交事务
            db.session.commit()
            print("✅ 项目评分记录表迁移完成")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 迁移失败: {str(e)}")
            raise

if __name__ == '__main__':
    create_project_rating_records_table() 
# -*- coding: utf-8 -*-
"""
创建项目评分记录表
记录每个用户对项目的评分操作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def create_project_rating_records_table():
    """创建项目评分记录表"""
    app = create_app()
    
    with app.app_context():
        print("创建项目评分记录表...")
        
        # 创建项目评分记录表
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS project_rating_records (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            rating INTEGER NOT NULL CHECK (rating = 1),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(project_id, user_id)
        );
        """
        
        # 添加索引
        create_indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_project_rating_records_project_id ON project_rating_records(project_id);",
            "CREATE INDEX IF NOT EXISTS idx_project_rating_records_user_id ON project_rating_records(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_project_rating_records_created_at ON project_rating_records(created_at);"
        ]
        
        # 添加注释
        add_comments_sql = [
            "COMMENT ON TABLE project_rating_records IS '项目评分记录表';",
            "COMMENT ON COLUMN project_rating_records.id IS '记录ID';",
            "COMMENT ON COLUMN project_rating_records.project_id IS '项目ID';",
            "COMMENT ON COLUMN project_rating_records.user_id IS '用户ID';",
            "COMMENT ON COLUMN project_rating_records.rating IS '评分值(固定为1星)';",
            "COMMENT ON COLUMN project_rating_records.created_at IS '创建时间';",
            "COMMENT ON COLUMN project_rating_records.updated_at IS '更新时间';"
        ]
        
        try:
            # 执行创建表
            db.session.execute(text(create_table_sql))
            print("✅ 项目评分记录表创建成功")
            
            # 执行创建索引
            for sql in create_indexes_sql:
                db.session.execute(text(sql))
            print("✅ 索引创建成功")
            
            # 执行添加注释
            for sql in add_comments_sql:
                db.session.execute(text(sql))
            print("✅ 注释添加成功")
            
            # 提交事务
            db.session.commit()
            print("✅ 项目评分记录表迁移完成")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 迁移失败: {str(e)}")
            raise

if __name__ == '__main__':
    create_project_rating_records_table() 
# -*- coding: utf-8 -*-
"""
创建项目评分记录表
记录每个用户对项目的评分操作
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def create_project_rating_records_table():
    """创建项目评分记录表"""
    app = create_app()
    
    with app.app_context():
        print("创建项目评分记录表...")
        
        # 创建项目评分记录表
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS project_rating_records (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            rating INTEGER NOT NULL CHECK (rating = 1),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(project_id, user_id)
        );
        """
        
        # 添加索引
        create_indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_project_rating_records_project_id ON project_rating_records(project_id);",
            "CREATE INDEX IF NOT EXISTS idx_project_rating_records_user_id ON project_rating_records(user_id);",
            "CREATE INDEX IF NOT EXISTS idx_project_rating_records_created_at ON project_rating_records(created_at);"
        ]
        
        # 添加注释
        add_comments_sql = [
            "COMMENT ON TABLE project_rating_records IS '项目评分记录表';",
            "COMMENT ON COLUMN project_rating_records.id IS '记录ID';",
            "COMMENT ON COLUMN project_rating_records.project_id IS '项目ID';",
            "COMMENT ON COLUMN project_rating_records.user_id IS '用户ID';",
            "COMMENT ON COLUMN project_rating_records.rating IS '评分值(固定为1星)';",
            "COMMENT ON COLUMN project_rating_records.created_at IS '创建时间';",
            "COMMENT ON COLUMN project_rating_records.updated_at IS '更新时间';"
        ]
        
        try:
            # 执行创建表
            db.session.execute(text(create_table_sql))
            print("✅ 项目评分记录表创建成功")
            
            # 执行创建索引
            for sql in create_indexes_sql:
                db.session.execute(text(sql))
            print("✅ 索引创建成功")
            
            # 执行添加注释
            for sql in add_comments_sql:
                db.session.execute(text(sql))
            print("✅ 注释添加成功")
            
            # 提交事务
            db.session.commit()
            print("✅ 项目评分记录表迁移完成")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 迁移失败: {str(e)}")
            raise

if __name__ == '__main__':
    create_project_rating_records_table() 