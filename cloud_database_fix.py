#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云端数据库紧急修复脚本
修复 projects.rating 字段缺失问题

问题：云端数据库中缺少 projects.rating 字段，导致系统启动报错
解决：添加 rating 字段到 projects 表

运行方法：
python cloud_database_fix.py
"""

import sys
import os
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    """主修复流程"""
    print("=" * 60)
    print("🚨 PMA 云端数据库紧急修复脚本")
    print("修复问题: projects.rating 字段缺失")
    print("=" * 60)
    
    try:
        # 添加应用路径
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        # 导入应用
        from app import create_app, db
        from sqlalchemy import text
        
        # 创建应用上下文
        app = create_app()
        
        with app.app_context():
            print("\n🔍 检查数据库连接...")
            
            # 测试数据库连接
            try:
                result = db.session.execute(text("SELECT 1")).fetchone()
                print("✅ 数据库连接正常")
            except Exception as e:
                print(f"❌ 数据库连接失败: {str(e)}")
                return False
            
            print("\n🔍 检查 projects.rating 字段是否存在...")
            
            # 检查字段是否已存在
            check_column_sql = """
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'projects' AND column_name = 'rating';
            """
            
            result = db.session.execute(text(check_column_sql)).fetchone()
            
            if result:
                print("✅ rating 字段已存在")
                print(f"   字段类型: {result[1]}")
                print(f"   可为空: {result[2]}")
                print("✅ 无需修复，数据库状态正常")
                return True
            
            print("❌ rating 字段不存在，开始修复...")
            
            # 添加 rating 字段
            print("\n🔧 添加 projects.rating 字段...")
            
            add_column_sql = """
            ALTER TABLE projects 
            ADD COLUMN rating INTEGER NULL 
            CHECK (rating IS NULL OR (rating >= 1 AND rating <= 5));
            """
            
            try:
                db.session.execute(text(add_column_sql))
                print("✅ rating 字段添加成功")
            except Exception as e:
                print(f"❌ 添加字段失败: {str(e)}")
                db.session.rollback()
                return False
            
            # 添加字段注释
            print("\n📝 添加字段注释...")
            
            add_comment_sql = """
            COMMENT ON COLUMN projects.rating IS '项目评分(1-5星)，NULL表示未评分';
            """
            
            try:
                db.session.execute(text(add_comment_sql))
                print("✅ 字段注释添加成功")
            except Exception as e:
                print(f"⚠️  添加注释失败（可忽略）: {str(e)}")
                # 注释失败不影响功能，继续执行
            
            # 提交事务
            print("\n💾 提交数据库更改...")
            
            try:
                db.session.commit()
                print("✅ 数据库更改已提交")
            except Exception as e:
                print(f"❌ 提交失败: {str(e)}")
                db.session.rollback()
                return False
            
            # 验证修复结果
            print("\n🔍 验证修复结果...")
            
            verify_result = db.session.execute(text(check_column_sql)).fetchone()
            
            if verify_result:
                print("✅ 验证成功!")
                print(f"   字段名: {verify_result[0]}")
                print(f"   字段类型: {verify_result[1]}")
                print(f"   可为空: {verify_result[2]}")
            else:
                print("❌ 验证失败，字段未创建")
                return False
            
            print("\n" + "=" * 60)
            print("🎉 数据库修复完成!")
            print("✅ projects.rating 字段已成功添加")
            print("✅ 系统现在应该可以正常启动")
            print("=" * 60)
            
            return True
            
    except ImportError as e:
        print(f"❌ 导入错误: {str(e)}")
        print("请确保在 PMA 项目根目录下运行此脚本")
        return False
    except Exception as e:
        print(f"❌ 修复过程中出现错误: {str(e)}")
        return False

def test_application_startup():
    """测试应用启动"""
    print("\n🧪 测试应用启动...")
    
    try:
        from app import create_app
        from app.models.project import Project
        
        app = create_app()
        
        with app.app_context():
            # 测试 Project 模型查询（会涉及 rating 字段）
            try:
                count = Project.query.count()
                print(f"✅ Project 模型查询成功，共 {count} 条记录")
                return True
            except Exception as e:
                print(f"❌ Project 模型查询失败: {str(e)}")
                return False
                
    except Exception as e:
        print(f"❌ 应用启动测试失败: {str(e)}")
        return False

if __name__ == '__main__':
    print("开始执行云端数据库修复...")
    
    # 执行主修复流程
    if main():
        # 修复成功，测试应用启动
        if test_application_startup():
            print("\n🎉 所有测试通过，修复成功!")
            print("现在可以重新启动 PMA 应用了。")
            sys.exit(0)
        else:
            print("\n⚠️  修复完成但应用启动测试失败")
            print("请检查其他可能的问题。")
            sys.exit(1)
    else:
        print("\n❌ 修复失败")
        print("请检查错误信息并手动修复。")
        sys.exit(1) 