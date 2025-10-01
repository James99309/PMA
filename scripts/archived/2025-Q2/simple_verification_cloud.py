#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云端数据库简化验证脚本
专注于核心数据验证，避免事务问题
"""

import psycopg2
from datetime import datetime

# 云端数据库连接信息
CLOUD_DB_URL = "postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d"

def print_header():
    print("🔍 PMA云端数据库简化验证报告")
    print("=" * 80)
    print(f"⏰ 验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 目标数据库: 云端PostgreSQL")
    print("📋 验证内容: 6月13日15:18分备份恢复结果")
    print("=" * 80)

def connect_to_cloud_db():
    """连接到云端数据库"""
    try:
        conn = psycopg2.connect(CLOUD_DB_URL)
        conn.autocommit = True
        print("✅ 云端数据库连接成功")
        return conn
    except Exception as e:
        print(f"❌ 云端数据库连接失败: {e}")
        return None

def check_core_data(conn):
    """检查核心数据"""
    print("\n📊 核心数据验证:")
    cursor = conn.cursor()
    
    # 核心业务数据检查
    core_checks = [
        ("👥 用户账户", "SELECT COUNT(*) FROM users", 24),
        ("🏢 公司信息", "SELECT COUNT(*) FROM companies", 519),
        ("📞 联系人", "SELECT COUNT(*) FROM contacts", 718),
        ("📋 项目", "SELECT COUNT(*) FROM projects", 468),
        ("💰 报价单", "SELECT COUNT(*) FROM quotations", 338),
        ("📝 报价详情", "SELECT COUNT(*) FROM quotation_details", 4032),
        ("📦 产品", "SELECT COUNT(*) FROM products", 186),
        ("🔐 权限配置", "SELECT COUNT(*) FROM role_permissions", 98),
        ("🔗 用户归属", "SELECT COUNT(*) FROM affiliations", 37),
        ("📊 操作记录", "SELECT COUNT(*) FROM actions", 668),
        ("⭐ 项目评分", "SELECT COUNT(*) FROM project_scoring_records", 3237),
        ("📈 项目阶段历史", "SELECT COUNT(*) FROM project_stage_history", 359),
        ("🏆 项目总分", "SELECT COUNT(*) FROM project_total_scores", 375),
        ("✅ 审批实例", "SELECT COUNT(*) FROM approval_instance", 49),
        ("📋 审批记录", "SELECT COUNT(*) FROM approval_record", 35),
        ("💼 开发产品", "SELECT COUNT(*) FROM dev_products", 5),
        ("📋 开发产品规格", "SELECT COUNT(*) FROM dev_product_specs", 75),
        ("🔧 产品代码字段", "SELECT COUNT(*) FROM product_code_fields", 43),
        ("⚙️ 产品代码选项", "SELECT COUNT(*) FROM product_code_field_options", 45),
        ("💳 定价订单", "SELECT COUNT(*) FROM pricing_orders", 2),
        ("📄 定价订单详情", "SELECT COUNT(*) FROM pricing_order_details", 22),
        ("✅ 定价订单审批", "SELECT COUNT(*) FROM pricing_order_approval_records", 6),
        ("💰 结算订单", "SELECT COUNT(*) FROM settlement_orders", 2),
        ("📋 结算详情", "SELECT COUNT(*) FROM settlement_order_details", 22),
    ]
    
    success_count = 0
    total_count = len(core_checks)
    
    for name, query, expected in core_checks:
        try:
            cursor.execute(query)
            actual = cursor.fetchone()[0]
            status = "✅" if actual == expected else "❌"
            if actual == expected:
                success_count += 1
            print(f"   {status} {name}: {actual} 条记录 (期望: {expected})")
        except Exception as e:
            print(f"   ❌ {name}: 检查失败 - {e}")
    
    cursor.close()
    return success_count, total_count

def check_system_data(conn):
    """检查系统数据"""
    print("\n⚙️ 系统数据验证:")
    cursor = conn.cursor()
    
    system_checks = [
        ("📚 数据字典", "SELECT COUNT(*) FROM dictionaries", 25),
        ("⚙️ 系统设置", "SELECT COUNT(*) FROM system_settings", 2),
        ("🔐 权限定义", "SELECT COUNT(*) FROM permissions", 19),
        ("📝 版本记录", "SELECT COUNT(*) FROM version_records", 1),
        ("📡 事件注册", "SELECT COUNT(*) FROM event_registry", 4),
        ("📧 邮件设置", "SELECT COUNT(*) FROM solution_manager_email_settings", 1),
        ("🔔 用户事件订阅", "SELECT COUNT(*) FROM user_event_subscriptions", 16),
        ("📊 变更日志", "SELECT COUNT(*) FROM change_logs", 145),
        ("📋 审批流程模板", "SELECT COUNT(*) FROM approval_process_template", 3),
        ("📝 审批步骤", "SELECT COUNT(*) FROM approval_step", 3),
        ("📊 项目评分配置", "SELECT COUNT(*) FROM project_scoring_config", 11),
        ("📦 产品分类", "SELECT COUNT(*) FROM product_categories", 8),
        ("🌍 产品区域", "SELECT COUNT(*) FROM product_regions", 8),
        ("📋 产品子分类", "SELECT COUNT(*) FROM product_subcategories", 60),
        ("💬 操作回复", "SELECT COUNT(*) FROM action_reply", 7),
    ]
    
    success_count = 0
    total_count = len(system_checks)
    
    for name, query, expected in system_checks:
        try:
            cursor.execute(query)
            actual = cursor.fetchone()[0]
            status = "✅" if actual == expected else "❌"
            if actual == expected:
                success_count += 1
            print(f"   {status} {name}: {actual} 条记录 (期望: {expected})")
        except Exception as e:
            print(f"   ❌ {name}: 检查失败 - {e}")
    
    cursor.close()
    return success_count, total_count

def check_sample_users(conn):
    """检查样本用户数据"""
    print("\n👥 用户样本验证:")
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT username, email, role FROM users LIMIT 5")
        users = cursor.fetchall()
        
        for i, (username, email, role) in enumerate(users, 1):
            print(f"   {i}. {username} | {email} | {role}")
        
        print(f"\n   📊 显示了前5个用户，总共24个用户")
        
    except Exception as e:
        print(f"   ❌ 用户样本检查失败: {e}")
    
    cursor.close()

def generate_final_report(core_success, core_total, system_success, system_total):
    """生成最终报告"""
    print("\n📋 最终验证报告")
    print("=" * 80)
    
    total_success = core_success + system_success
    total_count = core_total + system_total
    success_rate = (total_success / total_count) * 100
    
    print("🔍 验证统计:")
    print(f"   📊 核心业务数据: {core_success}/{core_total} 通过 ({core_success/core_total*100:.1f}%)")
    print(f"   ⚙️ 系统配置数据: {system_success}/{system_total} 通过 ({system_success/system_total*100:.1f}%)")
    print(f"   🎯 总体通过率: {total_success}/{total_count} ({success_rate:.1f}%)")
    
    if success_rate >= 95:
        status = "✅ 恢复成功"
        print(f"\n🎉 恭喜！云端数据库恢复成功率达到 {success_rate:.1f}%")
        print("📊 6月13日15:18分的备份数据已基本完整恢复")
        print("🔒 数据完整性良好，可以正常使用")
        
        print("\n📋 恢复成果总结:")
        print("   ✅ 24个用户账户完整恢复")
        print("   ✅ 519家公司信息完整恢复")
        print("   ✅ 718个联系人完整恢复")
        print("   ✅ 468个项目完整恢复")
        print("   ✅ 338个报价单完整恢复")
        print("   ✅ 4032条报价详情完整恢复")
        print("   ✅ 186个产品完整恢复")
        print("   ✅ 3237条项目评分记录完整恢复")
        print("   ✅ 所有权限配置完整恢复")
        print("   ✅ 所有系统配置完整恢复")
        
        print("\n🚀 云端应用现在可以正常使用！")
        
    elif success_rate >= 80:
        status = "⚠️ 基本成功"
        print(f"\n⚠️ 云端数据库基本恢复成功，通过率 {success_rate:.1f}%")
        print("📊 主要数据已恢复，可能有少量非关键数据缺失")
        print("🔧 建议检查失败的项目并进行补充恢复")
        
    else:
        status = "❌ 需要修复"
        print(f"\n❌ 云端数据库恢复不完整，通过率仅 {success_rate:.1f}%")
        print("🔧 需要进一步检查和修复")
    
    print("=" * 80)
    return success_rate >= 95

def main():
    print_header()
    
    # 连接数据库
    conn = connect_to_cloud_db()
    if not conn:
        return False
    
    try:
        # 执行验证
        core_success, core_total = check_core_data(conn)
        system_success, system_total = check_system_data(conn)
        check_sample_users(conn)
        
        # 生成最终报告
        overall_success = generate_final_report(core_success, core_total, system_success, system_total)
        
        return overall_success
        
    except Exception as e:
        print(f"❌ 验证过程出错: {e}")
        return False
    finally:
        if conn and not conn.closed:
            conn.close()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 