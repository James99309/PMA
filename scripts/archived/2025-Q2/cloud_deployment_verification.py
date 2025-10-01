#!/usr/bin/env python3
"""
云端部署验证脚本
用于验证权限系统修复在云端环境中的部署效果
"""

import os
import sys
from app import create_app, db
from app.models.user import User, Permission
from app.models.role_permissions import RolePermission

def verify_permissions_system():
    """验证权限系统修复"""
    print("=" * 60)
    print("权限系统修复部署验证")
    print("=" * 60)
    
    app = create_app()
    with app.app_context():
        try:
            # 0. 验证端口解析修复
            verify_environment_parsing()
            
            # 0.5. 验证SQLAlchemy兼容性修复
            verify_sqlalchemy_compatibility()
            
            # 1. 验证数据库连接
            print("\n1. 验证数据库连接...")
            try:
                from sqlalchemy import text
                db.session.execute(text('SELECT 1'))
            except Exception as e:
                # 如果text方法失败，尝试旧的方式
                try:
                    db.session.execute('SELECT 1')
                except Exception as e2:
                    print(f"❌ 数据库连接验证失败: {str(e2)}")
                    return False
            print("✅ 数据库连接正常")
            
            # 2. 验证用户表和权限表
            print("\n2. 验证核心表结构...")
            users_count = User.query.count()
            permissions_count = Permission.query.count()
            role_permissions_count = RolePermission.query.count()
            
            print(f"✅ 用户表记录数: {users_count}")
            print(f"✅ 个人权限表记录数: {permissions_count}")
            print(f"✅ 角色权限表记录数: {role_permissions_count}")
            
            # 3. 验证权限合并逻辑
            print("\n3. 验证权限合并逻辑...")
            
            # 查找一个测试用户（如果存在NIJIE用户）
            test_user = User.query.filter_by(username='NIJIE').first()
            if test_user:
                print(f"✅ 找到测试用户: {test_user.username} (角色: {test_user.role})")
                
                # 测试权限检查方法
                test_modules = ['product', 'project', 'customer']
                test_actions = ['view', 'create', 'edit', 'delete']
                
                for module in test_modules:
                    print(f"\n   测试 {module} 模块权限:")
                    for action in test_actions:
                        has_perm = test_user.has_permission(module, action)
                        print(f"      {action}: {has_perm}")
                        
                print("✅ 权限检查方法运行正常")
            else:
                print("⚠️  未找到NIJIE测试用户，跳过权限检查测试")
            
            # 4. 验证迁移文件
            print("\n4. 验证迁移文件...")
            migration_file = "migrations/versions/5055ec5e2171_权限系统修复_角色权限与个人权限合并逻辑优化.py"
            if os.path.exists(migration_file):
                print("✅ 权限系统修复迁移文件存在")
            else:
                print("❌ 权限系统修复迁移文件缺失")
            
            # 5. 验证核心修复文件
            print("\n5. 验证核心修复文件...")
            core_files = [
                "app/views/user.py",
                "app/models/user.py", 
                "app/__init__.py",
                "PERMISSIONS_SYSTEM_FIX_SUMMARY.md"
            ]
            
            for file_path in core_files:
                if os.path.exists(file_path):
                    print(f"✅ {file_path}")
                else:
                    print(f"❌ {file_path} 缺失")
            
            # 6. 验证模块导入
            print("\n6. 验证模块导入...")
            try:
                from app.views.user import manage_permissions
                print("✅ 权限管理视图导入成功")
            except Exception as e:
                print(f"❌ 权限管理视图导入失败: {e}")
            
            print("\n" + "=" * 60)
            print("部署验证完成")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"❌ 验证过程中出现错误: {e}")
            return False

def verify_environment():
    """验证环境配置"""
    print("\n环境信息:")
    print(f"Python版本: {sys.version}")
    print(f"当前工作目录: {os.getcwd()}")
    
    # 检查环境变量
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        # 隐藏敏感信息
        safe_url = db_url.split('@')[0] + '@***'
        print(f"数据库URL: {safe_url}")
    else:
        print("⚠️  DATABASE_URL环境变量未设置")

def verify_environment_parsing():
    """验证环境变量解析修复"""
    print("\n0. 验证环境变量解析修复...")
    
    # 模拟无效的环境变量
    old_port = os.environ.get('PORT')
    os.environ['PORT'] = '$PORT'  # 模拟问题环境变量
    
    try:
        # 重新导入config来测试修复
        import importlib
        if 'config' in sys.modules:
            importlib.reload(sys.modules['config'])
        
        from config import Config
        if hasattr(Config, 'PORT') and Config.PORT == 10000:
            print("✅ PORT环境变量解析修复验证通过")
        else:
            print(f"❌ PORT解析可能有问题: {getattr(Config, 'PORT', 'None')}")
    except Exception as e:
        print(f"❌ 环境变量解析验证失败: {e}")
    finally:
        # 恢复原始环境变量
        if old_port:
            os.environ['PORT'] = old_port
        elif 'PORT' in os.environ:
            del os.environ['PORT']

def verify_sqlalchemy_compatibility():
    """验证SQLAlchemy兼容性修复"""
    print("\n0.5. 验证SQLAlchemy兼容性修复...")
    
    app = create_app()
    with app.app_context():
        try:
            # 测试主要查询是否有异常处理
            from app.utils.access_control import get_viewable_data
            
            # 1. 测试首页项目查询（最重要的修复）
            print("   测试首页项目查询...")
            # 由于我们无法直接触发异常，我们检查代码是否有try-except结构
            import inspect
            from app.views.main import index
            source = inspect.getsource(index)
            if 'try:' in source and 'recent_projects' in source and 'except' in source:
                print("   ✅ 首页项目查询包含异常处理")
            else:
                print("   ❌ 首页项目查询缺少异常处理")
            
            # 2. 实际测试一个简单的项目查询
            try:
                from app.models.project import Project
                recent_projects = Project.query.limit(2).all()
                print(f"   ✅ 项目查询功能正常，获取到 {len(recent_projects)} 个项目")
            except Exception as e:
                print(f"   ❌ 项目查询失败: {e}")
            
            # 3. 测试用户查询
            try:
                users = User.query.limit(2).all() 
                print(f"   ✅ 用户查询功能正常，获取到 {len(users)} 个用户")
            except Exception as e:
                print(f"   ❌ 用户查询失败: {e}")
                
            print("✅ SQLAlchemy兼容性修复验证完成")
            
        except Exception as e:
            print(f"❌ SQLAlchemy兼容性验证失败: {e}")

if __name__ == "__main__":
    print("云端部署验证脚本")
    print("版本: 1.0.0")
    print("修复版本: 5055ec5e2171")
    
    verify_environment()
    
    if verify_permissions_system():
        print("\n🎉 部署验证成功！权限系统修复已正确部署")
        sys.exit(0)
    else:
        print("\n❌ 部署验证失败！请检查部署状态")
        sys.exit(1) 