#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
修复auth.py中的缩进错误
"""

import os
import re

# 文件路径
auth_file_path = os.path.join('app', 'views', 'auth.py')

# 读取文件内容
with open(auth_file_path, 'r', encoding='utf-8') as file:
    content = file.read()

# 查找并修复常见的缩进错误
print("开始修复auth.py中的缩进错误...")

# 确保文件没有混合使用Tab和空格
content = content.replace('\t', '    ')

# 正则表达式修复"return redirect(url_for('auth.login'))"前有额外缩进的问题
content = re.sub(r'\n\s+return redirect\(url_for\(\'auth\.login\'\)\)', 
                 r'\nreturn redirect(url_for(\'auth.login\'))', 
                 content)

# 保存修复后的文件
with open(auth_file_path, 'w', encoding='utf-8') as file:
    file.write(content)

print(f"文件修复完成: {auth_file_path}") 