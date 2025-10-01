#!/usr/bin/env python3
"""
调试报价单AJAX端点错误
"""

def test_ajax_imports():
    """测试AJAX函数所需的imports"""
    print("🔍 测试AJAX函数imports...")
    
    try:
        # 模拟AJAX函数中的关键imports
        from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
        from app.models.quotation import Quotation
        from app.models.project import Project
        from app.models.user import User
        from sqlalchemy import or_, func
        from sqlalchemy.orm import joinedload
        from app.utils.access_control import get_viewable_data
        from flask_login import current_user
        from app import db
        
        print("✅ 所有关键imports成功")
        return True
        
    except ImportError as e:
        print(f"❌ Import错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

def check_quotation_rows_template():
    """检查quotation_rows模板是否存在语法错误"""
    print("\n🔍 检查quotation_rows模板...")
    
    try:
        with open("app/templates/quotation/quotation_rows.html", "r", encoding="utf-8") as f:
            content = f.read()
        
        # 检查可能的模板语法错误
        potential_errors = [
            # 检查未闭合的模板标签
            (content.count("{{"), content.count("}}")),
            (content.count("{%"), content.count("%}")),
        ]
        
        for open_count, close_count in potential_errors:
            if open_count != close_count:
                print(f"❌ 模板标签不匹配: 开放{open_count}, 闭合{close_count}")
                return False
        
        # 检查可能导致错误的模式
        problematic_patterns = [
            "quotation.total_amount",  # 应该是amount
            "quotation.currency_type",  # 应该是currency
            "render_approval_status_badge",  # 已删除的函数
        ]
        
        found_issues = []
        for pattern in problematic_patterns:
            if pattern in content:
                found_issues.append(pattern)
        
        if found_issues:
            print(f"❌ 发现问题模式: {found_issues}")
            return False
        
        print("✅ 模板语法检查通过")
        return True
        
    except Exception as e:
        print(f"❌ 模板检查失败: {e}")
        return False

def check_ajax_function_structure():
    """检查AJAX函数结构"""
    print("\n🔍 检查AJAX函数结构...")
    
    try:
        with open("app/views/quotation.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # 找到AJAX函数
        ajax_start = content.find("def quotations_list_ajax():")
        if ajax_start == -1:
            print("❌ 未找到quotations_list_ajax函数")
            return False
        
        # 检查函数中的关键部分
        ajax_function = content[ajax_start:ajax_start+5000]  # 取函数的前5000字符
        
        required_parts = [
            "get_viewable_data(Quotation, current_user)",
            "render_template('quotation/quotation_rows.html'",
            "return jsonify({",
            "'success': True",
            "'html': html"
        ]
        
        missing_parts = []
        for part in required_parts:
            if part not in ajax_function:
                missing_parts.append(part)
        
        if missing_parts:
            print(f"❌ AJAX函数缺少部分: {missing_parts}")
            return False
        
        print("✅ AJAX函数结构完整")
        return True
        
    except Exception as e:
        print(f"❌ AJAX函数检查失败: {e}")
        return False

def check_filter_configuration():
    """检查筛选配置是否正确"""
    print("\n🔍 检查筛选配置...")
    
    try:
        with open("app/views/quotation.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # 检查筛选配置的关键字段
        config_checks = [
            ("'auto_submit': True", "启用自动提交"),
            ("'ajax_mode': True", "启用AJAX模式"),
            ("'filter_fields': [", "筛选字段配置"),
            ("'owner_filter'", "负责人筛选"),
            ("'project_type_filter'", "项目类型筛选")
        ]
        
        missing_configs = []
        for config, description in config_checks:
            if config not in content:
                missing_configs.append(f"{description} ({config})")
        
        if missing_configs:
            print(f"❌ 缺少配置: {missing_configs}")
            return False
        
        print("✅ 筛选配置完整")
        return True
        
    except Exception as e:
        print(f"❌ 筛选配置检查失败: {e}")
        return False

def main():
    """运行所有检查"""
    print("🚀 开始调试报价单AJAX错误...")
    print("=" * 50)
    
    tests = [
        ("Imports测试", test_ajax_imports),
        ("模板语法检查", check_quotation_rows_template),
        ("AJAX函数结构检查", check_ajax_function_structure),
        ("筛选配置检查", check_filter_configuration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 通过")
            else:
                print(f"❌ {test_name} 失败")
        except Exception as e:
            print(f"❌ {test_name} 异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"🎯 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("💡 所有检查通过，错误可能是:")
        print("   1. 数据库连接问题")
        print("   2. 权限检查错误")
        print("   3. 数据查询异常")
        print("   4. 模板渲染时的数据问题")
        print("\n🔧 建议调试步骤:")
        print("   1. 检查Flask应用日志")
        print("   2. 在AJAX函数中添加调试日志")
        print("   3. 测试简化的查询")
    else:
        print("⚠️ 发现问题，需要先解决上述失败的检查")

if __name__ == "__main__":
    main()