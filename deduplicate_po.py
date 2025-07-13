#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的PO文件去重脚本
删除重复的翻译条目，保留第一个出现的
"""

import re
from collections import OrderedDict

def deduplicate_po_file(file_path):
    """去重PO文件"""
    print(f"处理文件: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 创建备份
    backup_path = file_path + '.backup'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"已创建备份: {backup_path}")
    
    # 使用正则表达式匹配翻译条目
    # 匹配模式: (可选注释) + msgid + msgstr
    pattern = r'((?:^#.*\n)*?)^msgid\s+"([^"]*(?:"[^"]*")*[^"]*)"\s*\n^msgstr\s+"([^"]*(?:"[^"]*")*[^"]*)"\s*\n'
    
    matches = re.findall(pattern, content, re.MULTILINE)
    
    print(f"找到翻译条目: {len(matches)}")
    
    # 去重，保留第一次出现的
    seen_msgids = OrderedDict()
    duplicates = 0
    
    for comment, msgid, msgstr in matches:
        if msgid not in seen_msgids:
            seen_msgids[msgid] = (comment, msgstr)
        else:
            duplicates += 1
            print(f"跳过重复: {msgid[:50]}...")
    
    print(f"重复条目数: {duplicates}")
    print(f"去重后条目数: {len(seen_msgids)}")
    
    # 重新构建文件
    # 保留文件头部（到第一个翻译条目之前）
    header_match = re.search(r'^(.*?)(^#[^\n]*\n^msgid)', content, re.MULTILINE | re.DOTALL)
    if header_match:
        header = header_match.group(1)
    else:
        # 如果找不到模式，保留前20行作为头部
        lines = content.split('\n')
        header = '\n'.join(lines[:20]) + '\n\n'
    
    new_content = header
    
    # 添加去重后的翻译条目
    for msgid, (comment, msgstr) in seen_msgids.items():
        if comment.strip():
            new_content += comment
        new_content += f'msgid "{msgid}"\n'
        new_content += f'msgstr "{msgstr}"\n\n'
    
    # 写入新文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ 去重完成！")
    return len(seen_msgids)

if __name__ == '__main__':
    en_file = 'app/translations/en/LC_MESSAGES/messages.po'
    result = deduplicate_po_file(en_file)
    print(f"\n最终条目数: {result}")