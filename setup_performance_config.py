#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
角色绩效配置功能部署脚本
用于初始化和部署角色绩效配置系统
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.role_permissions import RolePermission
from app.models.performance_config import (
    PerformanceMetricsDefinition, RolePerformanceConfig, RolePerformanceItem,
    PerformanceFormulaTemplate, RolePerformanceAccess
)
from flask_migrate import upgrade
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_database_migration():
    """执行数据库迁移"""
    print("\n=== 执行数据库迁移 ===")
    
    app = create_app()
    with app.app_context():
        try:
            # 执行迁移
            upgrade()
            print("✅ 数据库迁移执行成功")
            return True
        except Exception as e:
            print(f"❌ 数据库迁移失败: {e}")
            return False

def setup_default_permissions():
    """设置默认权限配置"""
    print("\n=== 设置默认权限配置 ===")
    
    app = create_app()
    with app.app_context():
        try:
            # 为管理员和人力绩效经理配置权限
            roles_permissions = [
                {
                    'role': 'admin',
                    'can_view': True,
                    'can_create': True,
                    'can_edit': True,
                    'can_delete': True,
                    'permission_level': 'system'
                },
                {
                    'role': 'hrdp_manager',
                    'can_view': True,
                    'can_create': True,
                    'can_edit': True,
                    'can_delete': True,
                    'permission_level': 'system'
                },
                {
                    'role': 'ceo',
                    'can_view': True,
                    'can_create': False,
                    'can_edit': False,
                    'can_delete': False,
                    'permission_level': 'system'
                },
                {
                    'role': 'sales_director',
                    'can_view': True,
                    'can_create': False,
                    'can_edit': False,
                    'can_delete': False,
                    'permission_level': 'department'
                },
                {
                    'role': 'service_manager',
                    'can_view': True,
                    'can_create': False,
                    'can_edit': False,
                    'can_delete': False,
                    'permission_level': 'department'
                },
                {
                    'role': 'channel_manager',
                    'can_view': True,
                    'can_create': False,
                    'can_edit': False,
                    'can_delete': False,
                    'permission_level': 'department'
                }
            ]
            
            added_count = 0
            updated_count = 0
            
            for perm_config in roles_permissions:
                role = perm_config.pop('role')
                
                # 检查是否已存在
                existing_perm = RolePermission.query.filter_by(
                    role=role,
                    module='performance_management'
                ).first()
                
                if existing_perm:
                    # 更新现有权限
                    for key, value in perm_config.items():
                        setattr(existing_perm, key, value)
                    updated_count += 1
                    print(f"✅ 更新 {role} 权限配置")
                else:
                    # 创建新权限
                    new_perm = RolePermission(
                        role=role,
                        module='performance_management',
                        **perm_config
                    )
                    db.session.add(new_perm)
                    added_count += 1
                    print(f"✅ 新增 {role} 权限配置")
            
            db.session.commit()
            print(f"✅ 权限配置完成 - 新增: {added_count}, 更新: {updated_count}")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 设置权限配置失败: {e}")
            return False

def create_sample_configurations():
    """创建示例配置"""
    print("\n=== 创建示例配置 ===")
    
    app = create_app()
    with app.app_context():
        try:
            # 为销售总监创建示例配置
            sales_director_config = RolePerformanceConfig.query.filter_by(role='sales_director').first()
            if not sales_director_config:
                # 获取admin用户作为创建者
                admin_user = User.query.filter_by(role='admin').first()
                if not admin_user:
                    print("⚠️ 未找到admin用户，跳过创建示例配置")
                    return True
                
                sales_director_config = RolePerformanceConfig(
                    role='sales_director',
                    config_name='销售总监绩效方案',
                    description='主要考核销售团队整体业绩和团队管理能力',
                    is_active=True,
                    created_by=admin_user.id,
                    updated_by=admin_user.id
                )
                db.session.add(sales_director_config)
                db.session.flush()
                
                # 创建配置项
                sales_amount_metric = PerformanceMetricsDefinition.query.filter_by(metric_code='sales_amount').first()
                customer_count_metric = PerformanceMetricsDefinition.query.filter_by(metric_code='customer_count').first()
                
                if sales_amount_metric:
                    sales_item = RolePerformanceItem(
                        role_config_id=sales_director_config.id,
                        metric_id=sales_amount_metric.id,
                        item_name='团队销售金额',
                        item_code='team_sales_amount',
                        sort_order=1,
                        is_enabled=True,
                        stat_scope='department',
                        calculation_method='sum',
                        qualified_threshold=200.0,
                        good_threshold=300.0,
                        excellent_threshold=500.0,
                        qualification_rate=80,
                        display_unit='万元',
                        decimal_places=2,
                        weight=0.6
                    )
                    db.session.add(sales_item)
                
                if customer_count_metric:
                    customer_item = RolePerformanceItem(
                        role_config_id=sales_director_config.id,
                        metric_id=customer_count_metric.id,
                        item_name='团队客户增长',
                        item_code='team_customer_growth',
                        sort_order=2,
                        is_enabled=True,
                        stat_scope='department',
                        calculation_method='count',
                        qualified_threshold=10,
                        good_threshold=15,
                        excellent_threshold=20,
                        qualification_rate=75,
                        display_unit='个',
                        decimal_places=0,
                        weight=0.4
                    )
                    db.session.add(customer_item)
                
                # 创建访问权限配置
                access_config = RolePerformanceAccess(
                    role='sales_director',
                    access_scope='department',
                    description='销售总监可以查看部门级别的绩效数据'
                )
                db.session.add(access_config)
                
                db.session.commit()
                print("✅ 创建销售总监示例配置成功")
            else:
                print("✅ 销售总监配置已存在")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 创建示例配置失败: {e}")
            return False

def verify_installation():
    """验证安装"""
    print("\n=== 验证安装 ===")
    
    app = create_app()
    with app.app_context():
        try:
            # 检查数据表
            tables_status = {}
            tables_to_check = [
                'performance_metrics_definition',
                'role_performance_config',
                'role_performance_items', 
                'performance_formula_templates',
                'role_performance_access'
            ]
            
            for table in tables_to_check:
                try:
                    count = db.session.execute(db.text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    tables_status[table] = count
                    print(f"✅ 表 {table}: {count} 条记录")
                except Exception as e:
                    tables_status[table] = f"错误: {e}"
                    print(f"❌ 表 {table}: {e}")
            
            # 检查权限配置
            perm_count = RolePermission.query.filter_by(module='performance_management').count()
            print(f"✅ 绩效管理权限配置: {perm_count} 个角色")
            
            # 检查系统指标
            metrics_count = PerformanceMetricsDefinition.query.filter_by(is_system_metric=True).count()
            print(f"✅ 系统内置指标: {metrics_count} 个")
            
            # 检查公式模板
            templates_count = PerformanceFormulaTemplate.query.filter_by(is_system_template=True).count()
            print(f"✅ 系统公式模板: {templates_count} 个")
            
            # 检查示例配置
            config_count = RolePerformanceConfig.query.count()
            print(f"✅ 角色配置: {config_count} 个")
            
            return all(isinstance(status, int) for status in tables_status.values())
            
        except Exception as e:
            print(f"❌ 验证安装失败: {e}")
            return False

def main():
    """主函数"""
    print("🚀 开始部署角色绩效配置功能...")
    
    steps = [
        ("数据库迁移", run_database_migration),
        ("设置默认权限", setup_default_permissions),
        ("创建示例配置", create_sample_configurations),
        ("验证安装", verify_installation),
    ]
    
    all_success = True
    
    for step_name, step_func in steps:
        print(f"\n{'='*60}")
        print(f"📋 步骤: {step_name}")
        print(f"{'='*60}")
        
        try:
            success = step_func()
            if not success:
                all_success = False
                print(f"❌ 步骤 {step_name} 失败")
            else:
                print(f"✅ 步骤 {step_name} 完成")
        except Exception as e:
            print(f"❌ 步骤 {step_name} 异常: {e}")
            all_success = False
    
    print(f"\n{'='*60}")
    print("📊 部署结果")
    print(f"{'='*60}")
    
    if all_success:
        print("🎉 角色绩效配置功能部署成功！")
        print("\n📝 接下来可以做的事情：")
        print("1. 启动应用服务器")
        print("2. 访问 /performance/config/ 进行配置")
        print("3. 为更多角色创建绩效配置方案")
        print("4. 运行测试脚本验证功能: python test_performance_config.py")
    else:
        print("❌ 部署过程中出现错误，请检查日志并修复问题")
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)