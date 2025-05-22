#!/usr/bin/env python
# -*- coding: utf-8 -*-

from app import create_app
from app.helpers.approval_helpers import get_available_templates
from app.context_processors import inject_approval_functions

def check_context_processors():
    app = create_app()
    
    # 测试函数调用
    print("======== 测试函数调用 ========")
    with app.app_context():
        # 测试直接调用函数
        templates = get_available_templates('project')
        print(f"直接调用 get_available_templates('project') 结果: {templates}")
        print(f"模板数量: {len(templates)}")
        
        # 测试上下文处理器
        print("\n======== 测试上下文处理器 ========")
        context = inject_approval_functions()
        print(f"函数是否在上下文中: {'get_available_templates' in context}")
        
        # 获取上下文函数，测试调用
        available_templates_func = context.get('get_available_templates')
        if available_templates_func:
            print(f"函数对象: {available_templates_func}")
            # 尝试调用函数
            results = available_templates_func('project')
            print(f"通过上下文调用结果: {results}")
            print(f"模板数量: {len(results)}")
        else:
            print("函数未在上下文中找到!")
            
if __name__ == "__main__":
    check_context_processors() 