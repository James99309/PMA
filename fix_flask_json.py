#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复Flask JSON API变化问题

Flask 2.3+中，flask.json模块被重构，JSONEncoder被移至flask.json.provider
此脚本自动修复使用旧API的代码
"""

import os
import re
import sys

def fix_json_imports(filepath):
    """修复flask.json导入问题"""
    if not os.path.exists(filepath):
        print(f"错误: 文件不存在 {filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # 检查是否有需要修复的导入
    has_changes = False
    
    # 修复 flask.json.JSONEncoder
    if 'json.JSONEncoder' in content:
        content = content.replace('json.JSONEncoder', 'json.provider.JSONEncoder')
        has_changes = True
        print(f"修复: {filepath} 中的 json.JSONEncoder")
    
    if 'from flask import json' in content:
        # 添加正确的导入
        if 'json.provider' not in content:
            content = content.replace(
                'from flask import json', 
                'from flask import json\nfrom flask.json.provider import JSONEncoder'
            )
            has_changes = True
            print(f"修复: {filepath} 中的 flask json 导入")
    
    # 仅当有变化时写入文件
    if has_changes:
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(content)
        print(f"成功修复 {filepath}")
        return True
    else:
        print(f"无需修改 {filepath}")
        return False

def scan_and_fix(directory='.'):
    """扫描并修复目录中的Python文件"""
    fixed_files = []
    
    for root, dirs, files in os.walk(directory):
        # 跳过隐藏目录和虚拟环境
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'venv']
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if fix_json_imports(filepath):
                    fixed_files.append(filepath)
    
    return fixed_files

def main():
    """主函数"""
    print("开始修复Flask JSON API问题...")
    
    # 优先检查特定文件
    priority_files = [
        'app/routes/api.py',
        'app/templates/quotation/list.html',
        'app/views/quotation.py',
        'app/extensions.py',
        'app/__init__.py',
        'wsgi.py'
    ]
    
    for filepath in priority_files:
        if os.path.exists(filepath):
            fix_json_imports(filepath)
    
    # 扫描整个项目
    fixed_files = scan_and_fix('app')
    
    if fixed_files:
        print(f"\n已修复 {len(fixed_files)} 个文件:")
        for filepath in fixed_files:
            print(f"  - {filepath}")
        print("\n建议执行以下命令提交更改并重新部署:")
        print("git add .")
        print("git commit -m \"修复Flask 2.3 JSON API兼容性问题\"")
        print("git push")
    else:
        print("\n未找到需要修复的文件。")
    
    print("\n请尝试重新部署您的应用。")

if __name__ == "__main__":
    main() 