#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
这个脚本用于在Render上运行迁移命令，确保数据库结构同步
"""

import os
import sys

def main():
    """运行数据库迁移命令，确保数据库结构同步"""
    print("开始执行数据库迁移...")
    
    # 检查是否在Render环境中
    if os.environ.get('RENDER'):
        print("正在Render环境中执行数据库迁移")
    else:
        print("警告：不在Render环境中，但仍将执行迁移命令")
    
    # 执行迁移命令
    try:
        from flask_migrate import upgrade
        from app import create_app
        
        app = create_app()
        with app.app_context():
            # 应用所有迁移
            print("正在应用数据库迁移...")
            upgrade()
            print("数据库迁移应用成功！")
            
    except Exception as e:
        print(f"迁移过程中出错: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-

"""
这个脚本用于在Render上运行迁移命令，确保数据库结构同步
"""

import os
import sys

def main():
    """运行数据库迁移命令，确保数据库结构同步"""
    print("开始执行数据库迁移...")
    
    # 检查是否在Render环境中
    if os.environ.get('RENDER'):
        print("正在Render环境中执行数据库迁移")
    else:
        print("警告：不在Render环境中，但仍将执行迁移命令")
    
    # 执行迁移命令
    try:
        from flask_migrate import upgrade
        from app import create_app
        
        app = create_app()
        with app.app_context():
            # 应用所有迁移
            print("正在应用数据库迁移...")
            upgrade()
            print("数据库迁移应用成功！")
            
    except Exception as e:
        print(f"迁移过程中出错: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 