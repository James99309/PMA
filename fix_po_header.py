#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复PO文件头部，添加必要的元数据头部信息
"""

def fix_po_header(file_path):
    """添加PO文件必需的头部信息"""
    
    # 读取当前内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # PO文件标准头部
    header = '''# English translations for PMA.
# Copyright (C) 2024 PMA
# This file is distributed under the same license as the PMA project.
#
msgid ""
msgstr ""
"Project-Id-Version: PMA 1.0\\n"
"Report-Msgid-Bugs-To: support@pma.com\\n"
"POT-Creation-Date: 2024-12-15 10:00+0800\\n"
"PO-Revision-Date: 2025-07-13 17:54+0800\\n"
"Last-Translator: PMA Team\\n"
"Language: en\\n"
"Language-Team: en <support@pma.com>\\n"
"Plural-Forms: nplurals=2; plural=(n != 1)\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=utf-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Generated-By: Babel 2.17.0\\n"

# ================================================================================
# 翻译文件维护说明 / Translation File Maintenance Notes
# ================================================================================
# 
# 在添加新翻译条目前，请检查是否已存在相同的中文msgid：
# Before adding new translation entries, please check if the same Chinese msgid already exists:
# 
# 1. 搜索文件中是否已有相同的中文文本
#    Search the file for the same Chinese text
# 
# 2. 如果已存在，请跳过添加，或检查是否需要使用msgctxt来区分上下文
#    If it exists, skip adding, or check if msgctxt is needed to distinguish context
# 
# 3. 避免重复条目以保持文件清洁和维护性
#    Avoid duplicate entries to keep the file clean and maintainable
# 
# 4. 如发现重复，请保留第一个出现的条目，删除后续重复项
#    If duplicates are found, keep the first occurrence and remove subsequent duplicates
# 
# ================================================================================

'''
    
    # 查找第一个msgid（跳过文件头的维护说明）
    import re
    first_msgid_match = re.search(r'msgid "您没有权限查看此客户信息"', content)
    if first_msgid_match:
        # 从第一个真正的翻译条目开始
        entries_content = content[first_msgid_match.start():]
        
        # 合并头部和内容
        new_content = header + entries_content
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ PO文件头部已修复")
        return True
    else:
        print("❌ 找不到翻译条目开始位置")
        return False

if __name__ == '__main__':
    po_file = '/Users/nijie/Documents/PMA/app/translations/en/LC_MESSAGES/messages.po'
    try:
        success = fix_po_header(po_file)
        if success:
            print("后续步骤: pybabel compile -d app/translations -l en")
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()