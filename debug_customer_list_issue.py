#!/usr/bin/env python3
"""
Debug Customer List Issue - 调试admin用户看到63个客户而不是467个的问题
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

# 设置Flask应用上下文
from app import create_app, db
from app.models.user import User
from app.models.customer import Company
from app.utils.access_control import get_viewable_data

def debug_customer_access():
    """调试客户访问权限问题"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("客户列表权限问题调试报告")
        print("=" * 60)
        
        # 1. 获取admin用户
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("❌ 错误：找不到admin用户")
            return
            
        print(f"✅ Admin用户信息:")
        print(f"   用户名: {admin_user.username}")
        print(f"   ID: {admin_user.id}")
        print(f"   角色: {admin_user.role}")
        print(f"   是否激活: {admin_user._is_active}")
        print()
        
        # 2. 检查数据库中的客户总数
        total_companies = Company.query.count()
        active_companies = Company.query.filter(Company.is_deleted == False).count()
        deleted_companies = Company.query.filter(Company.is_deleted == True).count()
        
        print(f"📊 数据库客户统计:")
        print(f"   客户总数: {total_companies}")
        print(f"   未删除客户: {active_companies}")
        print(f"   已删除客户: {deleted_companies}")
        print()
        
        # 3. 测试get_viewable_data函数
        viewable_companies = get_viewable_data(Company, admin_user)
        viewable_count = viewable_companies.count()
        
        print(f"🔍 get_viewable_data函数测试:")
        print(f"   Admin可见客户数: {viewable_count}")
        print(f"   应该等于未删除客户数: {viewable_count == active_companies}")
        print()
        
        # 4. 检查lihuawei用户
        lihuawei_user = User.query.filter_by(username='lihuawei').first()
        if lihuawei_user:
            print(f"👤 lihuawei用户信息:")
            print(f"   用户名: {lihuawei_user.username}")
            print(f"   ID: {lihuawei_user.id}")
            print(f"   角色: {lihuawei_user.role}")
            
            # 检查lihuawei拥有的客户数
            lihuawei_companies = Company.query.filter(
                Company.is_deleted == False,
                Company.owner_id == lihuawei_user.id
            ).count()
            print(f"   拥有的客户数: {lihuawei_companies}")
            print()
        
        # 5. 分析63这个数字
        print(f"🔎 分析63这个数字的来源:")
        
        # 可能的筛选条件
        if lihuawei_user and lihuawei_companies == 63:
            print(f"   ⚠️  发现问题: 63 = lihuawei用户拥有的客户数")
            print(f"   这说明admin访问时可能被错误地应用了owner_id={lihuawei_user.id}的筛选")
        
        # 6. 模拟admin用户权限检查
        print(f"🛡️  Admin用户权限检查:")
        print(f"   角色是否为admin: {admin_user.role == 'admin'}")
        
        has_customer_permission = admin_user.has_permission('customer', 'view')
        print(f"   是否有客户查看权限: {has_customer_permission}")
        
        customer_permission_level = admin_user.get_permission_level('customer')
        print(f"   客户权限级别: {customer_permission_level}")
        
        # 7. 检查是否有特殊筛选条件影响
        print(f"\n🔧 可能的问题来源:")
        print(f"   1. URL参数中包含了owner_id参数")
        print(f"   2. 浏览器缓存了之前的筛选状态")
        print(f"   3. 代码中存在意外的筛选逻辑")
        print(f"   4. 权限配置异常")
        
        # 8. 详细检查Company模型的访问控制
        print(f"\n📋 Company模型访问控制详细检查:")
        
        # 直接查询，不经过get_viewable_data
        direct_query = Company.query.filter(Company.is_deleted == False)
        direct_count = direct_query.count()
        print(f"   直接查询未删除客户数: {direct_count}")
        
        # 通过get_viewable_data查询
        print(f"   通过权限控制查询: {viewable_count}")
        
        if direct_count != viewable_count:
            print(f"   ❌ 权限控制函数可能有问题")
        else:
            print(f"   ✅ 权限控制函数正常")
            
        print("\n" + "=" * 60)
        print("调试建议:")
        print("1. 检查admin访问客户列表时的URL参数")
        print("2. 检查浏览器开发者工具的Network面板")
        print("3. 查看实际发送的请求参数")
        print("4. 确认没有JavaScript代码自动设置筛选条件")
        print("=" * 60)

if __name__ == "__main__":
    debug_customer_access()