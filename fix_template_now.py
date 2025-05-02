#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
彻底修复quotation/list.html模板语法错误
"""

import os
import re
import shutil

template_path = "app/templates/quotation/list.html"

# 读取模板内容
with open(template_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 创建备份
backup_path = f"{template_path}.bak"
shutil.copy2(template_path, backup_path)
print(f"已创建备份文件: {backup_path}")

# 计算每个block标签的数量
def count_blocks(content):
    block_counts = {}
    # 查找所有block开始标签
    start_blocks = re.finditer(r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}', content)
    for match in start_blocks:
        block_name = match.group(1)
        if block_name not in block_counts:
            block_counts[block_name] = {'start': 0, 'end': 0}
        block_counts[block_name]['start'] += 1
    
    # 查找所有block结束标签
    end_blocks = re.finditer(r'{%\s*endblock(?:\s+([a-zA-Z0-9_]+))?\s*%}', content)
    for match in end_blocks:
        block_name = match.group(1) if match.group(1) else None
        if block_name and block_name in block_counts:
            block_counts[block_name]['end'] += 1
        else:
            # 未命名的endblock，只统计总数
            for key in block_counts.keys():
                if block_counts[key]['end'] < block_counts[key]['start']:
                    block_counts[key]['end'] += 1
                    break
    
    return block_counts

blocks = count_blocks(content)
print(f"找到的block标签情况: {blocks}")

# 检查是否有多余的endblock标签
unbalanced_blocks = False
for block_name, counts in blocks.items():
    if counts['start'] < counts['end']:
        unbalanced_blocks = True
        print(f"块 '{block_name}' 有多余的endblock标签: {counts['start']} 开始 vs {counts['end']} 结束")

if unbalanced_blocks:
    # 找到文件末尾的多余endblock标签
    lines = content.split('\n')
    fixed_lines = []
    inside_script_block = False
    block_stack = []
    
    for line in lines:
        # 检测block开始
        block_start = re.search(r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}', line)
        if block_start:
            block_name = block_start.group(1)
            block_stack.append(block_name)
            inside_script_block = (block_name == 'scripts')
        
        # 检测block结束
        block_end = re.search(r'{%\s*endblock(?:\s+([a-zA-Z0-9_]+))?\s*%}', line)
        if block_end and block_stack:
            # 只有当还有打开的块时才弹出
            block_stack.pop()
            inside_script_block = False
        
        # 根据是否在script块内及是否是脚本结束来处理行
        if inside_script_block or not re.match(r'^\s*{%\s*endblock\s*%}\s*$', line):
            fixed_lines.append(line)
    
    # 确保最后正确关闭块
    if 'scripts' in blocks:
        fixed_lines.append('{% endblock scripts %}')
    
    fixed_lines.append('{% endblock content %}')
    
    # 写回文件
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(fixed_lines))
    print(f"已修复文件: {template_path}")
else:
    print("所有block标签都是平衡的，不需要修复")

# 验证模板
try:
    from jinja2 import Environment, FileSystemLoader
    env = Environment(loader=FileSystemLoader('app/templates'))
    template = env.get_template('quotation/list.html')
    print("模板语法验证成功！")
except Exception as e:
    print(f"模板语法验证失败: {str(e)}") 