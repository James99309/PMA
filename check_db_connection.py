#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
用于检查数据库连接和结构的实用脚本
"""

import os
import sys
from sqlalchemy import inspect, text

def main():
    """检查数据库连接并显示数据库结构"""
    try:
        from app import create_app, db
        
        app = create_app()
        with app.app_context():
            # 检查数据库连接
            print("尝试连接到数据库...")
            try:
                result = db.engine.execute(text("SELECT 1")).scalar()
                print(f"数据库连接成功! 测试查询结果: {result}")
            except Exception as e:
                print(f"数据库连接失败: {e}")
                return 1
            
            # 获取并显示companies表结构
            inspector = inspect(db.engine)
            print("\n===== 数据库表结构 =====")
            
            if 'companies' in inspector.get_table_names():
                print("\n表: companies")
                columns = inspector.get_columns('companies')
                for column in columns:
                    print(f"  - {column['name']}: {column['type']}")
            else:
                print("警告: companies表不存在")
                
            print("\n===== 迁移历史 =====")
            try:
                from flask_migrate import current
                version = current()
                print(f"当前数据库版本: {version}")
            except Exception as e:
                print(f"无法获取迁移历史: {e}")
            
    except Exception as e:
        print(f"执行过程中出错: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 