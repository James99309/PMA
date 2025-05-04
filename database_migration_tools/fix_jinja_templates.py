#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复Jinja模板语法错误

此脚本检查和修复Jinja模板中的语法错误，特别是quotation/list.html中的问题
"""

import os
import re
import glob

def analyze_template(content):
    """分析模板中的block和endblock标签"""
    # 找出所有的block标签
    block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
    blocks = re.findall(block_pattern, content)
    
    # 找出所有的endblock标签
    endblock_pattern = r'{%\s*endblock(?:\s+([a-zA-Z0-9_]+))?\s*%}'
    endblocks_with_names = re.findall(endblock_pattern, content)
    
    # 去除None值和空字符串
    endblocks = [name for name in endblocks_with_names if name]
    
    # 统计各block出现的次数
    block_counts = {}
    for block in blocks:
        if block in block_counts:
            block_counts[block] += 1
        else:
            block_counts[block] = 1
    
    # 统计各endblock出现的次数
    endblock_counts = {}
    for endblock in endblocks:
        if endblock in endblock_counts:
            endblock_counts[endblock] += 1
        else:
            endblock_counts[endblock] = 1
    
    # 检查不匹配的情况
    missing_endblocks = []
    for block, count in block_counts.items():
        if block not in endblock_counts or endblock_counts[block] < count:
            missing_endblocks.append(block)
    
    extra_endblocks = []
    for endblock, count in endblock_counts.items():
        if endblock not in block_counts or endblock_counts[endblock] > block_counts[endblock]:
            extra_endblocks.append(endblock)
    
    unnamed_endblocks = len(endblocks_with_names) - len(endblocks)
    
    return {
        'blocks': blocks,
        'endblocks': endblocks,
        'block_counts': block_counts,
        'endblock_counts': endblock_counts,
        'missing_endblocks': missing_endblocks,
        'extra_endblocks': extra_endblocks,
        'unnamed_endblocks': unnamed_endblocks,
        'total_blocks': len(blocks),
        'total_endblocks': len(endblocks_with_names)
    }

def fix_template(file_path, backup=True):
    """修复模板文件的语法错误"""
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在 {file_path}")
        return False
    
    print(f"\n处理文件: {file_path}")
    
    # 读取原始内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 分析模板
    analysis = analyze_template(content)
    print(f"分析结果:")
    print(f"  总block数: {analysis['total_blocks']}")
    print(f"  总endblock数: {analysis['total_endblocks']}")
    print(f"  未命名endblock数: {analysis['unnamed_endblocks']}")
    
    # 创建备份文件
    if backup:
        backup_path = f"{file_path}.bak"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"已创建备份文件: {backup_path}")
    
    # 记录原始内容以检测变化
    original_content = content
    
    # 以下是针对可能的问题的修复逻辑
    
    # 1. 修复缺少的endblock标签
    if analysis['missing_endblocks']:
        print(f"发现缺少endblock标签: {analysis['missing_endblocks']}")
        for block in analysis['missing_endblocks']:
            # 在文件末尾添加缺少的endblock
            content += f"\n{{% endblock {block} %}}\n"
        print(f"已在文件末尾添加缺少的endblock标签")
    
    # 2. 删除额外的endblock标签
    if analysis['extra_endblocks'] or analysis['total_endblocks'] > analysis['total_blocks']:
        print(f"发现额外的endblock标签")
        
        # 特殊处理: 尝试找到无名称的多余endblock并删除
        extra_endblock_pattern = r'{%\s*endblock\s*%}'
        content = re.sub(extra_endblock_pattern, '<!-- 已删除无名称endblock -->', content)
        
        # 处理有特定名称的多余endblock
        for extra in analysis['extra_endblocks']:
            extra_named_pattern = r'{%\s*endblock\s+' + re.escape(extra) + r'\s*%}'
            content = re.sub(extra_named_pattern, f'<!-- 已删除多余endblock {extra} -->', content)
        
        print(f"已删除额外的endblock标签")
    
    # 3. 特殊处理: 检查文件末尾是否有错误的endblock格式 (例如带有额外的%)
    if content.strip().endswith('%'):
        content = content.rstrip('%')
        content += "\n"
        print(f"已删除文件末尾多余的%符号")
    
    # 4. 修复常见错误: {% endblock content %} 后面有多余的 %}
    content = content.replace('{% endblock content %}%', '{% endblock content %}')
    
    # 特别处理quotation/list.html
    if 'quotation/list.html' in file_path:
        # 确保文件末尾的标签正确
        end_content = content[-50:].strip()
        if 'endblock scripts' in end_content and 'endblock content' in end_content:
            # 如果发现同时存在这两个标签，确保顺序正确
            content = re.sub(
                r'{%\s*endblock\s+scripts\s*%}\s*{%\s*endblock\s+content\s*%}',
                '{% endblock scripts %}\n\n{% endblock content %}',
                content
            )
            print("已修复quotation/list.html文件末尾的标签顺序")
    
    # 5. 只有在内容变更时才写入文件
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"已修复文件: {file_path}")
        
        # 创建一个.fixed文件以供检查
        fixed_path = f"{file_path}.fixed"
        with open(fixed_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"已创建修复后的备份文件: {fixed_path}")
        
        return True
    else:
        print(f"文件无需修复")
        return False

def find_jinja_templates():
    """找出项目中所有Jinja模板文件"""
    template_files = []
    
    # 搜索app/templates目录下的所有.html文件
    for html_file in glob.glob('app/templates/**/*.html', recursive=True):
        template_files.append(html_file)
    
    return template_files

def main():
    """主程序"""
    print("开始修复Jinja模板语法错误...")
    
    # 首先修复已知有问题的文件
    critical_templates = ['app/templates/quotation/list.html']
    
    for template in critical_templates:
        if os.path.exists(template):
            fix_template(template)
    
    # 询问是否继续检查所有模板
    response = input("\n是否继续检查项目中的所有模板? (y/n): ")
    if response.lower() == 'y':
        templates = find_jinja_templates()
        print(f"\n找到 {len(templates)} 个模板文件")
        
        for template in templates:
            if template not in critical_templates:
                fix_template(template)
    
    print("\n模板修复完成")
    print("\n请执行以下命令提交变更:")
    print("git add .")
    print("git commit -m \"修复Jinja模板语法错误\"")
    print("git push")
    
    print("\n建议重新部署应用程序")

if __name__ == "__main__":
    main() 