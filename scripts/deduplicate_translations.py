#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻译文件去重脚本
删除重复的msgid条目，保留第一个出现的翻译
"""

import re
import sys
from collections import OrderedDict

def deduplicate_po_file(file_path):
    """
    去重PO翻译文件
    """
    print(f"正在处理文件: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 分离文件头部和翻译条目
    lines = content.split('\n')
    header_lines = []
    translation_section = []
    
    # 找到翻译部分开始的位置（第一个msgid ""之后）
    in_header = True
    for i, line in enumerate(lines):
        if in_header and line.strip().startswith('msgid ""') and i == 4:
            # 跳过文件头部的msgid ""
            continue
        elif in_header and line.strip().startswith('#') or line.strip().startswith('"') or line.strip() == '':
            header_lines.append(line)
        else:
            in_header = False
            translation_section = lines[i:]
            break
    
    # 解析翻译条目
    translations = OrderedDict()
    current_msgid = None
    current_msgstr = None
    current_comments = []
    
    i = 0
    while i < len(translation_section):
        line = translation_section[i].strip()
        
        if line.startswith('#'):
            current_comments.append(translation_section[i])
        elif line.startswith('msgid '):
            # 开始新的翻译条目
            if current_msgid is not None:
                # 保存前一个条目（只保留第一次出现的）
                if current_msgid not in translations:
                    translations[current_msgid] = {
                        'comments': current_comments[:],
                        'msgstr': current_msgstr
                    }
                else:
                    print(f"跳过重复的msgid: {current_msgid}")
            
            # 处理多行msgid
            current_msgid = line[6:].strip()  # 去掉'msgid '
            current_comments = current_comments[:]
            current_msgstr = None
            
            # 检查是否有继续的行
            j = i + 1
            while j < len(translation_section) and translation_section[j].strip().startswith('"'):
                current_msgid = current_msgid[:-1] + translation_section[j].strip()[1:]  # 去掉引号并连接
                j += 1
            i = j - 1
            
        elif line.startswith('msgstr '):
            # 处理多行msgstr
            current_msgstr = line[7:].strip()  # 去掉'msgstr '
            
            # 检查是否有继续的行
            j = i + 1
            while j < len(translation_section) and translation_section[j].strip().startswith('"'):
                current_msgstr = current_msgstr[:-1] + translation_section[j].strip()[1:]  # 去掉引号并连接
                j += 1
            i = j - 1
            
        elif line == '':
            # 空行，重置注释
            if translation_section[i] == '':
                current_comments = []
        
        i += 1
    
    # 保存最后一个条目
    if current_msgid is not None and current_msgid not in translations:
        translations[current_msgid] = {
            'comments': current_comments[:],
            'msgstr': current_msgstr
        }
    
    print(f"原始条目数: {len(translation_section)}")
    print(f"去重后条目数: {len(translations)}")
    
    # 重新构建文件内容
    new_content = '\n'.join(header_lines) + '\n\n'
    
    for msgid, data in translations.items():
        # 添加注释
        for comment in data['comments']:
            new_content += comment + '\n'
        
        # 添加msgid和msgstr
        new_content += f'msgid {msgid}\n'
        new_content += f'msgstr {data["msgstr"]}\n\n'
    
    # 创建备份
    backup_path = file_path + '.backup'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"原文件已备份到: {backup_path}")
    
    # 写入新文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"去重完成！")
    return len(translations)

if __name__ == '__main__':
    # 处理英文翻译文件
    en_file = 'app/translations/en/LC_MESSAGES/messages.po'
    
    try:
        count = deduplicate_po_file(en_file)
        print(f"\n✅ 成功去重，最终条目数: {count}")
        print("\n建议操作:")
        print("1. 检查去重后的文件是否正确")
        print("2. 重新编译翻译文件: pybabel compile -d app/translations -l en")
        print("3. 测试应用确保翻译正常工作")
        print("4. 如果一切正常，可以删除备份文件")
        
    except Exception as e:
        print(f"❌ 去重过程中出现错误: {e}")
        sys.exit(1)