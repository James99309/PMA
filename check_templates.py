#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查Jinja模板是否有语法错误
"""

import os
import glob
import re

def check_template(file_path):
    """检查单个模板文件"""
    print(f"检查文件: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查block和endblock匹配
    block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
    blocks = re.findall(block_pattern, content)
    
    endblock_pattern = r'{%\s*endblock(?:\s+([a-zA-Z0-9_]+))?\s*%}'
    endblocks_with_names = re.findall(endblock_pattern, content)
    
    # 去除None值和空字符串
    endblocks = [name for name in endblocks_with_names if name]
    
    print(f"  找到{len(blocks)}个block标签: {blocks}")
    print(f"  找到{len(endblocks)}个有名称的endblock标签: {endblocks}")
    print(f"  找到{len(endblocks_with_names) - len(endblocks)}个无名称的endblock标签")
    
    # 检查是否有不成对的标签
    block_set = set(blocks)
    endblock_set = set(endblocks)
    
    missing_endblocks = block_set - endblock_set
    extra_endblocks = endblock_set - block_set
    
    if missing_endblocks:
        print(f"  警告: 缺少以下block的endblock标签: {missing_endblocks}")
    
    if extra_endblocks:
        print(f"  警告: 存在以下多余的endblock标签: {extra_endblocks}")
    
    # 检查是否有未闭合的块
    if len(blocks) != len(endblocks_with_names):
        print(f"  警告: block标签数({len(blocks)})与endblock标签数({len(endblocks_with_names)})不匹配")
    
    # 检查文件末尾特殊问题
    if content.strip().endswith('%'):
        print(f"  警告: 文件末尾有多余的%符号")
    
    print()

def main():
    """主程序"""
    print("开始检查模板文件...\n")
    
    # 查找所有模板文件
    templates = glob.glob('app/templates/**/*.html', recursive=True)
    print(f"找到{len(templates)}个模板文件\n")
    
    # 先检查已知有问题的模板
    critical_templates = ['app/templates/quotation/list.html']
    for template in critical_templates:
        if os.path.exists(template):
            check_template(template)
    
    # 询问是否检查所有模板
    response = input("是否检查所有模板文件？(y/n): ")
    if response.lower() == 'y':
        for template in templates:
            if template not in critical_templates:
                check_template(template)
    
    print("检查完成")

if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-
"""
检查Jinja模板是否有语法错误
"""

import os
import glob
import re

def check_template(file_path):
    """检查单个模板文件"""
    print(f"检查文件: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查block和endblock匹配
    block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
    blocks = re.findall(block_pattern, content)
    
    endblock_pattern = r'{%\s*endblock(?:\s+([a-zA-Z0-9_]+))?\s*%}'
    endblocks_with_names = re.findall(endblock_pattern, content)
    
    # 去除None值和空字符串
    endblocks = [name for name in endblocks_with_names if name]
    
    print(f"  找到{len(blocks)}个block标签: {blocks}")
    print(f"  找到{len(endblocks)}个有名称的endblock标签: {endblocks}")
    print(f"  找到{len(endblocks_with_names) - len(endblocks)}个无名称的endblock标签")
    
    # 检查是否有不成对的标签
    block_set = set(blocks)
    endblock_set = set(endblocks)
    
    missing_endblocks = block_set - endblock_set
    extra_endblocks = endblock_set - block_set
    
    if missing_endblocks:
        print(f"  警告: 缺少以下block的endblock标签: {missing_endblocks}")
    
    if extra_endblocks:
        print(f"  警告: 存在以下多余的endblock标签: {extra_endblocks}")
    
    # 检查是否有未闭合的块
    if len(blocks) != len(endblocks_with_names):
        print(f"  警告: block标签数({len(blocks)})与endblock标签数({len(endblocks_with_names)})不匹配")
    
    # 检查文件末尾特殊问题
    if content.strip().endswith('%'):
        print(f"  警告: 文件末尾有多余的%符号")
    
    print()

def main():
    """主程序"""
    print("开始检查模板文件...\n")
    
    # 查找所有模板文件
    templates = glob.glob('app/templates/**/*.html', recursive=True)
    print(f"找到{len(templates)}个模板文件\n")
    
    # 先检查已知有问题的模板
    critical_templates = ['app/templates/quotation/list.html']
    for template in critical_templates:
        if os.path.exists(template):
            check_template(template)
    
    # 询问是否检查所有模板
    response = input("是否检查所有模板文件？(y/n): ")
    if response.lower() == 'y':
        for template in templates:
            if template not in critical_templates:
                check_template(template)
    
    print("检查完成")

if __name__ == "__main__":
    main() 
 
 