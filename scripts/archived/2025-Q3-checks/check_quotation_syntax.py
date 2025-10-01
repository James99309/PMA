#!/usr/bin/env python3
"""
报价单模块语法检查脚本
检查可能导致Jinja2错误的语法问题
"""

import os
import re
import sys

def check_template_variables():
    """检查模板中的变量使用"""
    print("🧪 检查模板变量使用...")
    
    template_path = "app/templates/quotation/list.html"
    if not os.path.exists(template_path):
        print("❌ 模板文件不存在")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取所有模板变量
    variable_pattern = r'\{\{\s*([^}]+)\s*\}\}'
    variables = re.findall(variable_pattern, content)
    
    # 检查可能有问题的变量
    problematic_vars = []
    for var in variables:
        var = var.strip()
        # 跳过函数调用、过滤器等
        if ('(' in var or '|' in var or '_(' in var or 
            'url_for(' in var or 'csrf_token()' in var or
            'current_user.' in var or "'true'" in var or "'false'" in var):
            continue
        
        # 检查可能未定义的变量
        simple_var = var.split('.')[0].split('[')[0]
        if simple_var in ['offset', 'limit', 'has_more', 'total_count', 
                         'quotations', 'sort_field', 'sort_order',
                         'owner_filter', 'project_type_filter', 'project_stage_filter',
                         'list_config', 'filter_config']:
            print(f"✅ 发现标准变量: {var}")
        else:
            problematic_vars.append(var)
    
    if problematic_vars:
        print(f"⚠️ 发现可能有问题的变量: {problematic_vars}")
    else:
        print("✅ 模板变量检查通过")
    
    return len(problematic_vars) == 0

def check_backend_render_template():
    """检查后端render_template调用"""
    print("🧪 检查后端render_template调用...")
    
    py_path = "app/views/quotation.py"
    with open(py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找所有render_template调用
    render_pattern = r'render_template\s*\(\s*[\'"]quotation/list\.html[\'"]([^)]*)\)'
    matches = re.findall(render_pattern, content, re.DOTALL)
    
    required_params = [
        'quotations', 'sort_field', 'sort_order', 'offset', 'limit', 
        'has_more', 'total_count', 'owner_filter', 'project_type_filter',
        'project_stage_filter', 'filter_config', 'list_config'
    ]
    
    issues = []
    for i, match in enumerate(matches):
        print(f"✅ 检查第{i+1}个render_template调用...")
        for param in required_params:
            if param not in match:
                issues.append(f"render_template #{i+1} 缺少参数: {param}")
    
    if issues:
        for issue in issues:
            print(f"❌ {issue}")
        return False
    else:
        print("✅ 后端render_template检查通过")
        return True

def check_ajax_endpoint():
    """检查AJAX端点配置"""
    print("🧪 检查AJAX端点配置...")
    
    py_path = "app/views/quotation.py"
    with open(py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查AJAX端点存在
    if "def quotations_list_ajax():" not in content:
        print("❌ AJAX端点函数不存在")
        return False
    
    # 检查路由装饰器
    if "@quotation.route('/api/quotations/filter'" not in content:
        print("❌ AJAX端点路由不正确")
        return False
    
    # 检查返回JSON格式
    if "'html':" not in content or "'statistics':" not in content:
        print("❌ AJAX端点返回格式不完整")
        return False
    
    print("✅ AJAX端点配置检查通过")
    return True

def check_javascript_config():
    """检查JavaScript配置"""
    print("🧪 检查JavaScript配置...")
    
    template_path = "app/templates/quotation/list.html"
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查必需的JavaScript配置
    js_checks = [
        'quotationListConfig',
        'setupDataList',
        'data-list.js',
        'filter-search.js'
    ]
    
    missing_js = []
    for check in js_checks:
        if check not in content:
            missing_js.append(check)
    
    if missing_js:
        print(f"❌ JavaScript配置缺失: {missing_js}")
        return False
    else:
        print("✅ JavaScript配置检查通过")
        return True

def check_import_statements():
    """检查Python导入语句"""
    print("🧪 检查Python导入语句...")
    
    py_path = "app/views/quotation.py"
    with open(py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_imports = [
        'from flask_babel import gettext',
        'from flask import',
        'from app.models.quotation import Quotation'
    ]
    
    missing_imports = []
    for imp in required_imports:
        if imp not in content:
            missing_imports.append(imp)
    
    if missing_imports:
        print(f"❌ 缺少导入: {missing_imports}")
        return False
    else:
        print("✅ Python导入检查通过")
        return True

def main():
    """运行所有语法检查"""
    print("🚀 开始报价单模块语法检查...")
    print("=" * 50)
    
    checks = [
        check_template_variables,
        check_backend_render_template,
        check_ajax_endpoint,
        check_javascript_config,
        check_import_statements
    ]
    
    passed = 0
    total = len(checks)
    
    for check in checks:
        try:
            if check():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ 检查异常: {e}")
            print()
    
    print("=" * 50)
    print(f"🎯 检查结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 报价单模块语法检查全部通过！")
        print("💡 模块现在应该可以正常运行，没有Jinja2语法错误")
        return True
    else:
        print("⚠️ 部分检查未通过，仍可能存在语法问题")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)