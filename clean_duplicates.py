#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理messages.po文件中的重复翻译条目
保留每个中文msgid的第一次出现，移除后续重复项
"""

import re
from collections import OrderedDict

def clean_duplicate_translations(file_path):
    """清理PO文件中的重复翻译条目"""
    print(f"正在清理文件: {file_path}")
    
    # 创建备份
    backup_path = file_path + '.backup_clean'
    with open(file_path, 'r', encoding='utf-8') as src, open(backup_path, 'w', encoding='utf-8') as dst:
        dst.write(src.read())
    print(f"已创建备份: {backup_path}")
    
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 分离文件头部和翻译条目
    header_match = re.search(r'(.*?)\n(?=msgid "[^"]*")', content, re.DOTALL)
    if header_match:
        header = header_match.group(1)
    else:
        header = ""
    
    # 添加维护说明到头部注释
    maintenance_comment = '''
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
    
    # 在原有注释后添加维护说明
    header = header + maintenance_comment
    
    # 提取所有翻译条目
    entry_pattern = r'(msgid\s+"[^"]*"(?:\s*"[^"]*")*\s*msgstr\s+"[^"]*"(?:\s*"[^"]*")*(?:\s*\n)*)'
    entries = re.findall(entry_pattern, content, re.MULTILINE)
    
    # 用于跟踪已见过的msgid
    seen_msgids = OrderedDict()
    duplicates_removed = 0
    
    # 处理每个条目
    for entry in entries:
        # 提取msgid
        msgid_match = re.search(r'msgid\s+"([^"]*)"', entry)
        if msgid_match:
            msgid_text = msgid_match.group(1)
            
            # 如果是空字符串（文件头），跳过
            if msgid_text == '':
                continue
                
            # 如果没见过这个msgid，保存它
            if msgid_text not in seen_msgids:
                seen_msgids[msgid_text] = entry
            else:
                duplicates_removed += 1
                print(f"移除重复条目: {msgid_text}")
    
    print(f"原始条目数: {len(entries)}")
    print(f"移除重复条目数: {duplicates_removed}")
    print(f"清理后条目数: {len(seen_msgids)}")
    
    # 重新构建文件内容
    new_content = header + '\n'
    
    # 添加所有唯一的条目
    for msgid_text, entry in seen_msgids.items():
        new_content += entry + '\n'
    
    # 写入清理后的文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ 清理完成！")
    return len(seen_msgids), duplicates_removed

if __name__ == '__main__':
    po_file = '/Users/nijie/Documents/PMA/app/translations/en/LC_MESSAGES/messages.po'
    try:
        final_count, removed_count = clean_duplicate_translations(po_file)
        print(f"\n结果统计:")
        print(f"- 最终条目数: {final_count}")
        print(f"- 移除重复数: {removed_count}")
        print(f"- 减少比例: {removed_count/(final_count+removed_count)*100:.1f}%")
        print("\n后续步骤:")
        print("1. 重新编译翻译: pybabel compile -d app/translations -l en")
        print("2. 测试应用翻译功能")
        print("3. 如果正常，可删除备份文件")
    except Exception as e:
        print(f"❌ 清理失败: {e}")
        import traceback
        traceback.print_exc()