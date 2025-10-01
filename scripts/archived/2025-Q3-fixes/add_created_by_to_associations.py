#!/usr/bin/env python3
"""
为 project_customer_associations 表添加 created_by 字段的迁移脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from sqlalchemy import text

def add_created_by_column():
    """为 project_customer_associations 表添加 created_by 字段"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("开始为 project_customer_associations 表添加 created_by 字段...")
            
            # 检查列是否已存在
            check_column_sql = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'project_customer_associations' 
            AND column_name = 'created_by'
            """
            
            result = db.session.execute(text(check_column_sql)).fetchone()
            
            if result:
                print("✅ created_by 字段已存在，无需添加")
                return True
            
            # 添加字段
            add_column_sql = """
            ALTER TABLE project_customer_associations 
            ADD COLUMN created_by INTEGER REFERENCES users(id)
            """
            
            db.session.execute(text(add_column_sql))
            
            # 为现有记录设置默认创建者（如果需要的话，可以设置为项目拥有者）
            # 这里我们先设置为 NULL，表示历史数据创建者未知
            
            db.session.commit()
            print("✅ 成功添加 created_by 字段")
            
            # 验证字段是否添加成功
            verify_sql = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'project_customer_associations' 
            AND column_name = 'created_by'
            """
            
            result = db.session.execute(text(verify_sql)).fetchone()
            if result:
                print(f"✅ 字段验证成功: {result.column_name} ({result.data_type}, nullable: {result.is_nullable})")
            else:
                print("❌ 字段验证失败")
                return False
                
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 添加字段失败: {e}")
            return False

if __name__ == '__main__':
    success = add_created_by_column()
    if success:
        print("\n🎉 数据库迁移完成！")
        print("\n注意事项:")
        print("1. 现有的客户关联记录的 created_by 字段为 NULL，表示创建者未知")
        print("2. 新添加的客户关联将正确记录创建者")
        print("3. 只有关联的创建者（或管理员/项目拥有者）才能移除该关联")
    else:
        print("\n❌ 数据库迁移失败！")