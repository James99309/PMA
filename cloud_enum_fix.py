#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
云端审批状态枚举快速修复脚本

专门解决云端部署中 approvalstatus 枚举缺少 RECALLED 值的问题

使用方法：
1. 上传到云端服务器
2. python cloud_enum_fix.py
3. 重启应用服务

特点：
- 专注解决单一问题
- 简单直接，适合紧急修复
- 包含完整的验证步骤
"""

import os
import sys
import logging

# 简单日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def quick_fix():
    """快速修复审批状态枚举"""
    
    print("=" * 50)
    print("🔧 云端审批状态枚举修复工具")
    print("=" * 50)
    
    try:
        # 初始化应用
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from app.extensions import db
            from sqlalchemy import text
            
            print("🔍 检查当前枚举值...")
            
            # 检查枚举值
            result = db.session.execute(text("""
                SELECT enumlabel 
                FROM pg_enum e
                JOIN pg_type t ON e.enumtypid = t.oid 
                WHERE t.typname = 'approvalstatus'
                ORDER BY e.enumsortorder
            """))
            
            enum_values = [row[0] for row in result.fetchall()]
            print(f"📋 当前枚举值: {enum_values}")
            
            # 检查是否缺少 RECALLED
            if 'RECALLED' in enum_values or 'recalled' in enum_values:
                print("✅ RECALLED 值已存在，无需修复")
                return True
            
            print("⚠️  发现问题：缺少 RECALLED 枚举值")
            print("🔧 开始修复...")
            
            # 提交当前事务
            db.session.commit()
            
            # 使用原始连接执行 ALTER TYPE
            connection = db.engine.raw_connection()
            try:
                cursor = connection.cursor()
                cursor.execute("ALTER TYPE approvalstatus ADD VALUE 'RECALLED'")
                connection.commit()
                print("✅ 成功添加 RECALLED 到枚举类型")
                
                # 验证
                cursor.execute("""
                    SELECT enumlabel 
                    FROM pg_enum e
                    JOIN pg_type t ON e.enumtypid = t.oid 
                    WHERE t.typname = 'approvalstatus'
                    ORDER BY e.enumsortorder
                """)
                
                new_values = [row[0] for row in cursor.fetchall()]
                print(f"✅ 验证成功，新枚举值: {new_values}")
                
            finally:
                cursor.close()
                connection.close()
            
            # 测试应用功能
            print("🧪 测试功能...")
            from app.models.approval import ApprovalStatus
            print(f"📝 ApprovalStatus.RECALLED = {ApprovalStatus.RECALLED.value}")
            
            return True
            
    except Exception as e:
        print(f"❌ 修复失败: {str(e)}")
        return False

def main():
    success = quick_fix()
    
    if success:
        print()
        print("=" * 50)
        print("✅ 修复完成！")
        print("=" * 50)
        print()
        print("📋 后续操作：")
        print("1. 重启应用服务")
        print("2. 测试报销功能")
        print("3. 检查错误日志")
        print()
        return 0
    else:
        print()
        print("=" * 50)
        print("❌ 修复失败！")
        print("=" * 50)
        print()
        print("🔧 手动修复方法：")
        print("1. 连接数据库: psql -h [host] -U [user] -d [database]")
        print("2. 执行命令: ALTER TYPE approvalstatus ADD VALUE 'RECALLED';")
        print("3. 重启应用服务")
        print()
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)