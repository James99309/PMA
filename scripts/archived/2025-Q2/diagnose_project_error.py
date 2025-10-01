#!/usr/bin/env python3
"""
详细诊断项目查询错误
找出500错误的真正原因
"""

import os
import sys
import traceback

def diagnose_project_query():
    """诊断项目查询问题"""
    try:
        # 设置Flask应用上下文
        from app import create_app, db
        from app.models.project import Project
        from app.models.user import User
        
        app = create_app()
        
        with app.app_context():
            print("=== 项目查询诊断开始 ===")
            
            # 1. 检查数据库连接
            print("\n1. 检查数据库连接...")
            try:
                result = db.session.execute(db.text("SELECT 1"))
                print("✅ 数据库连接正常")
            except Exception as e:
                print(f"❌ 数据库连接失败: {str(e)}")
                return False
            
            # 2. 检查projects表结构
            print("\n2. 检查projects表结构...")
            try:
                result = db.session.execute(db.text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'projects' 
                    ORDER BY ordinal_position
                """))
                columns = [row[0] for row in result.fetchall()]
                print(f"✅ projects表有 {len(columns)} 个字段")
                print("字段列表:", ", ".join(columns))
                
                if 'dealer_manager_id' in columns:
                    print("❌ 警告: dealer_manager_id字段仍然存在!")
                else:
                    print("✅ dealer_manager_id字段已正确删除")
                    
            except Exception as e:
                print(f"❌ 检查表结构失败: {str(e)}")
                return False
            
            # 3. 测试简单的项目计数查询
            print("\n3. 测试项目计数查询...")
            try:
                count = db.session.execute(db.text("SELECT COUNT(*) FROM projects")).scalar()
                print(f"✅ 数据库中共有 {count} 个项目")
            except Exception as e:
                print(f"❌ 项目计数查询失败: {str(e)}")
                return False
            
            # 4. 测试Project模型的基本查询
            print("\n4. 测试Project模型查询...")
            try:
                count = Project.query.count()
                print(f"✅ Project.query.count() 成功: {count}")
            except Exception as e:
                print(f"❌ Project.query.count() 失败: {str(e)}")
                print("详细错误信息:")
                traceback.print_exc()
                return False
            
            # 5. 测试获取前5个项目（模拟错误查询）
            print("\n5. 测试获取前5个项目...")
            try:
                projects = Project.query.order_by(Project.updated_at.desc()).limit(5).all()
                print(f"✅ 成功获取 {len(projects)} 个项目")
                
                # 检查每个项目的字段
                if projects:
                    project = projects[0]
                    print(f"第一个项目: {project.project_name}")
                    print(f"拥有者ID: {project.owner_id}")
                    print(f"厂商销售负责人ID: {project.vendor_sales_manager_id}")
                    
                    # 检查是否有dealer_manager_id属性
                    if hasattr(project, 'dealer_manager_id'):
                        print("❌ 警告: Project模型仍然有dealer_manager_id属性!")
                    else:
                        print("✅ Project模型没有dealer_manager_id属性")
                        
            except Exception as e:
                print(f"❌ 获取项目列表失败: {str(e)}")
                print("详细错误信息:")
                traceback.print_exc()
                return False
            
            # 6. 检查关联查询
            print("\n6. 测试关联查询...")
            try:
                projects = Project.query.join(User, Project.owner_id == User.id).limit(3).all()
                print(f"✅ 关联查询成功，获取 {len(projects)} 个项目")
            except Exception as e:
                print(f"❌ 关联查询失败: {str(e)}")
                print("详细错误信息:")
                traceback.print_exc()
                return False
            
            # 7. 检查vendor_sales_manager关系
            print("\n7. 测试vendor_sales_manager关系...")
            try:
                projects_with_sales_manager = Project.query.filter(
                    Project.vendor_sales_manager_id.isnot(None)
                ).limit(3).all()
                print(f"✅ 有厂商销售负责人的项目: {len(projects_with_sales_manager)}")
                
                for project in projects_with_sales_manager:
                    try:
                        sales_manager = project.vendor_sales_manager
                        print(f"  项目 {project.project_name} 的销售负责人: {sales_manager.username if sales_manager else 'None'}")
                    except Exception as e:
                        print(f"  ❌ 获取项目 {project.project_name} 的销售负责人失败: {str(e)}")
                        
            except Exception as e:
                print(f"❌ 测试vendor_sales_manager关系失败: {str(e)}")
                print("详细错误信息:")
                traceback.print_exc()
                return False
            
            print("\n=== 诊断完成 ===")
            print("✅ 所有测试通过，Project模型工作正常")
            return True
            
    except Exception as e:
        print(f"❌ 诊断过程中发生错误: {str(e)}")
        print("详细错误信息:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = diagnose_project_query()
    sys.exit(0 if success else 1) 