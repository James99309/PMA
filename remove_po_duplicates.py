#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻译文件去重工具
系统性地移除 PO 文件中的重复条目，保留第一次出现的条目
"""

import sys
import re
from collections import OrderedDict

def parse_po_file(file_path):
    """解析 PO 文件，返回条目列表"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 存储所有条目
    entries = []
    current_entry = {'comments': [], 'msgid': '', 'msgstr': '', 'line_start': 0}
    in_msgid = False
    in_msgstr = False
    line_num = 0
    
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # 处理注释和空行
        if line.startswith('#') or line.strip() == '':
            if current_entry['msgid'] == '' and current_entry['msgstr'] == '':
                current_entry['comments'].append(line)
            else:
                # 如果当前条目已有内容，保存并开始新条目
                if current_entry['msgid'] or current_entry['msgstr']:
                    entries.append(current_entry)
                current_entry = {'comments': [line], 'msgid': '', 'msgstr': '', 'line_start': line_num}
            continue
        
        # 处理 msgid
        if line.startswith('msgid '):
            if current_entry['msgid'] or current_entry['msgstr']:
                entries.append(current_entry)
            current_entry = {'comments': current_entry['comments'], 'msgid': '', 'msgstr': '', 'line_start': line_num}
            current_entry['msgid'] = line[6:].strip(' "')  # 移除 'msgid ' 和引号
            in_msgid = True
            in_msgstr = False
            continue
        
        # 处理 msgstr
        if line.startswith('msgstr '):
            current_entry['msgstr'] = line[7:].strip(' "')  # 移除 'msgstr ' 和引号
            in_msgid = False
            in_msgstr = True
            continue
        
        # 处理多行字符串
        if line.startswith('"') and line.endswith('"'):
            content_line = line[1:-1]  # 移除引号
            if in_msgid:
                current_entry['msgid'] += content_line
            elif in_msgstr:
                current_entry['msgstr'] += content_line
    
    # 添加最后一个条目
    if current_entry['msgid'] or current_entry['msgstr']:
        entries.append(current_entry)
    
    return entries

def remove_duplicates(entries):
    """移除重复的条目，保留第一次出现的"""
    seen_msgids = OrderedDict()
    unique_entries = []
    duplicate_count = 0
    
    for entry in entries:
        msgid = entry['msgid']
        
        # 跳过空的 msgid（通常是文件头部信息）
        if not msgid.strip():
            unique_entries.append(entry)
            continue
        
        # 检查是否重复
        if msgid in seen_msgids:
            print(f"发现重复条目: '{msgid}' (行 {entry['line_start']})")
            print(f"  首次出现: 行 {seen_msgids[msgid]['line_start']}")
            print(f"  重复出现: 行 {entry['line_start']}")
            print(f"  翻译内容: '{entry['msgstr']}'")
            print()
            duplicate_count += 1
        else:
            seen_msgids[msgid] = entry
            unique_entries.append(entry)
    
    print(f"总共移除了 {duplicate_count} 个重复条目")
    return unique_entries

def write_po_file(entries, file_path):
    """将条目写入 PO 文件"""
    lines = []
    
    for entry in entries:
        # 添加注释
        for comment in entry['comments']:
            lines.append(comment)
        
        # 添加 msgid
        if entry['msgid'].strip():  # 只有非空的 msgid 才添加
            lines.append(f'msgid "{entry["msgid"]}"')
            lines.append(f'msgstr "{entry["msgstr"]}"')
            lines.append('')  # 空行分隔
    
    # 写入文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

def main():
    if len(sys.argv) != 2:
        print("用法: python remove_po_duplicates.py <po_file_path>")
        sys.exit(1)
    
    po_file = sys.argv[1]
    backup_file = po_file + '.pre_dedup'
    
    print(f"正在处理文件: {po_file}")
    
    # 创建备份
    import shutil
    shutil.copy2(po_file, backup_file)
    print(f"备份已创建: {backup_file}")
    
    # 解析文件
    print("正在解析 PO 文件...")
    entries = parse_po_file(po_file)
    print(f"共解析到 {len(entries)} 个条目")
    
    # 移除重复
    print("\n正在移除重复条目...")
    unique_entries = remove_duplicates(entries)
    print(f"去重后剩余 {len(unique_entries)} 个条目")
    
    # 写入文件
    print(f"\n正在写入去重后的文件: {po_file}")
    write_po_file(unique_entries, po_file)
    
    print("\n✅ 去重完成！")
    print(f"原始文件备份: {backup_file}")
    print(f"去重后文件: {po_file}")

if __name__ == "__main__":
    main()