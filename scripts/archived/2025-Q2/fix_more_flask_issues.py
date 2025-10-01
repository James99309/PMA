#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复Flask 2.3 JSON API兼容性更严重的问题

Flask 2.3+中对JSON处理做了大量重构，这个脚本修复导入错误
"""

import os
import re
import glob

def fix_file(file_path):
    """修复文件中Flask JSON相关的导入和使用"""
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 记录原始内容以检测变化
    original_content = content
    
    # 1. 修复 JSONEncoderify 错误导入 - 这个类在Flask中不存在
    if 'JSONEncoderify' in content:
        # 完全替换这个不存在的类，改用标准JSONEncoder
        content = content.replace('from flask.json.provider import JSONEncoderify', 
                                 'from flask.json.provider import JSONProvider')
        content = content.replace('JSONEncoderify', 'JSONProvider')
    
    # 2. 修复 flask.json.JSONEncoder 为 flask.json.provider.JSONEncoder
    if 'json.JSONEncoder' in content and 'flask.json.provider.JSONEncoder' not in content:
        content = content.replace('from flask import json', 
                                 'from flask import json\nfrom flask.json.provider import JSONEncoder')
        content = content.replace('json.JSONEncoder', 'JSONEncoder')
    
    # 3. 修复直接使用 flask.json 模块的代码
    if 'flask.json' in content or 'from flask import json' in content:
        # 添加兼容层代码
        compat_code = """
# Flask 2.3+ JSON兼容层
try:
    from flask.json import jsonify, loads, dumps
except (ImportError, AttributeError):
    from flask import current_app
    
    def jsonify(*args, **kwargs):
        return current_app.json.response(*args, **kwargs)
    
    def dumps(*args, **kwargs):
        return current_app.json.dumps(*args, **kwargs)
    
    def loads(*args, **kwargs):
        return current_app.json.loads(*args, **kwargs)
"""
        # 检查是否已经有这段兼容代码
        if compat_code.strip() not in content:
            # 在导入语句后添加兼容层
            import_pattern = r'(from flask import .*?\n|import flask.*?\n)'
            match = re.search(import_pattern, content)
            if match:
                pos = match.end()
                content = content[:pos] + compat_code + content[pos:]
    
    # 4. 修复 app.routes/product.py 中的问题 (从之前的日志看到这个有问题)
    if file_path.endswith('app/routes/product.py') and 'json.' in content:
        content = content.replace('json.JSONEncoder', 'JSONEncoder')
        content = content.replace('json.jsonify', 'jsonify')
    
    # 5. 只有在内容变更时才写入文件
    if content != original_content:
        print(f"修复文件: {file_path}")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    return False

def find_problematic_files():
    """查找可能包含Flask JSON相关问题的文件"""
    problematic_files = []
    
    # 特别检查这些已知可能有问题的文件
    priority_files = [
        'app/routes/product.py',
        'app/api/v1/utils.py',
        'app/utils/auth.py'
    ]
    
    for file_path in priority_files:
        if os.path.exists(file_path):
            if 'JSONEncoderify' in open(file_path, 'r', encoding='utf-8').read():
                problematic_files.append(file_path)
    
    # 搜索整个代码库中可能使用JSONEncoderify的文件
    for py_file in glob.glob('app/**/*.py', recursive=True):
        if py_file not in problematic_files:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'JSONEncoderify' in content or ('json.' in content and 'flask' in content):
                    problematic_files.append(py_file)
    
    return problematic_files

def main():
    """主程序"""
    print("开始修复Flask 2.3 JSON API相关问题...")
    
    problematic_files = find_problematic_files()
    fixed_count = 0
    
    if problematic_files:
        print(f"找到 {len(problematic_files)} 个可能有问题的文件:")
        for file_path in problematic_files:
            print(f"  - {file_path}")
            if fix_file(file_path):
                fixed_count += 1
    else:
        print("未找到可能有问题的文件，尝试修复所有可能相关的文件...")
        # 尝试修复已知文件
        for file_path in [
            'app/routes/product.py',
            'app/api/v1/utils.py',
            'app/utils/auth.py',
            'app/routes/api.py',
            'app/__init__.py'
        ]:
            if os.path.exists(file_path):
                if fix_file(file_path):
                    fixed_count += 1
    
    if fixed_count > 0:
        print(f"\n成功修复 {fixed_count} 个文件")
        print("\n请执行以下命令提交变更:")
        print("git add .")
        print("git commit -m \"修复Flask 2.3 JSONEncoderify导入错误\"")
        print("git push")
    else:
        print("\n没有文件需要修复")
    
    print("\n建议重新部署应用程序")

if __name__ == "__main__":
    main() 