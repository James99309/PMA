#!/usr/bin/env python3
"""
更新绩效管理权限脚本
为所有用户重新分配包含performance_management模块的默认权限
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User, Permission
from app.utils.permissions import assign_user_default_permissions

def main():
    """主函数"""
    app = create_app()
    
    with app.app_context():
        print("🚀 开始更新绩效管理权限...")
        
        # 获取所有用户
        users = User.query.all()
        print(f"📊 共找到 {len(users)} 个用户")
        
        success_count = 0
        error_count = 0
        
        for user in users:
            try:
                print(f"⚙️  正在更新用户: {user.username} ({user.role})")
                
                # 重新分配默认权限（包含新的performance_management模块）
                if assign_user_default_permissions(user):
                    success_count += 1
                    print(f"✅ 用户 {user.username} 权限更新成功")
                    
                    # 检查performance_management权限
                    perf_perm = Permission.query.filter_by(
                        user_id=user.id, 
                        module='performance_management'
                    ).first()
                    
                    if perf_perm:
                        print(f"   📋 绩效管理权限: 查看={perf_perm.can_view}, 创建={perf_perm.can_create}, 编辑={perf_perm.can_edit}, 删除={perf_perm.can_delete}")
                    else:
                        print(f"   ❌ 未找到绩效管理权限记录")
                else:
                    error_count += 1
                    print(f"❌ 用户 {user.username} 权限更新失败")
                    
            except Exception as e:
                error_count += 1
                print(f"❌ 用户 {user.username} 权限更新出错: {str(e)}")
        
        print(f"\n🎉 权限更新完成！")
        print(f"✅ 成功: {success_count} 个用户")
        print(f"❌ 失败: {error_count} 个用户")
        
        # 特别检查liuq用户
        liuq_user = User.query.filter_by(username='liuq').first()
        if liuq_user:
            print(f"\n🔍 特别检查liuq用户:")
            print(f"   用户名: {liuq_user.username}")
            print(f"   角色: {liuq_user.role}")
            print(f"   真实姓名: {liuq_user.real_name}")
            
            perf_perm = Permission.query.filter_by(
                user_id=liuq_user.id, 
                module='performance_management'
            ).first()
            
            if perf_perm:
                print(f"   📋 绩效管理权限: 查看={perf_perm.can_view}, 创建={perf_perm.can_create}, 编辑={perf_perm.can_edit}, 删除={perf_perm.can_delete}")
                
                if perf_perm.can_view:
                    print("   ✅ liuq用户现在可以访问绩效看板了！")
                else:
                    print("   ❌ liuq用户仍然无法访问绩效看板")
            else:
                print("   ❌ 未找到liuq用户的绩效管理权限记录")
        else:
            print("\n❌ 未找到liuq用户")

if __name__ == '__main__':
    main()