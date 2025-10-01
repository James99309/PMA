#!/usr/bin/env python3
"""
创建解决方案经理邮件设置表的迁移脚本
"""

from app import create_app
from app.extensions import db
from app.models.notification import SolutionManagerEmailSettings

def create_solution_manager_settings_table():
    """创建解决方案经理邮件设置表"""
    app = create_app()
    
    with app.app_context():
        try:
            # 创建表
            db.create_all()
            print("✅ 解决方案经理邮件设置表创建成功")
            
            # 检查表是否存在
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'solution_manager_email_settings' in tables:
                print("✅ 表 'solution_manager_email_settings' 已存在")
                
                # 显示表结构
                columns = inspector.get_columns('solution_manager_email_settings')
                print("\n表结构:")
                for column in columns:
                    print(f"  - {column['name']}: {column['type']}")
            else:
                print("❌ 表 'solution_manager_email_settings' 不存在")
                
        except Exception as e:
            print(f"❌ 创建表时出错: {str(e)}")
            return False
            
    return True

if __name__ == '__main__':
    create_solution_manager_settings_table() 