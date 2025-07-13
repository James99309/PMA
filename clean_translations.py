#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Babel库清理和去重翻译文件
"""

from babel.messages import Catalog
from babel.messages.pofile import read_po, write_po
from collections import OrderedDict
import io

def clean_po_file(file_path):
    """清理PO文件，去除重复条目"""
    print(f"清理文件: {file_path}")
    
    # 创建备份
    backup_path = file_path + '.backup'
    with open(file_path, 'rb') as src, open(backup_path, 'wb') as dst:
        dst.write(src.read())
    print(f"已创建备份: {backup_path}")
    
    # 读取PO文件
    with open(file_path, 'rb') as f:
        catalog = read_po(f)
    
    print(f"原始消息数量: {len(catalog)}")
    
    # 创建新的目录，去重
    new_catalog = Catalog(
        locale=catalog.locale,
        domain=catalog.domain,
        header_comment=catalog.header_comment,
        project=catalog.project,
        version=catalog.version,
        copyright_holder=catalog.copyright_holder,
        msgid_bugs_address=catalog.msgid_bugs_address,
        creation_date=catalog.creation_date,
        revision_date=catalog.revision_date,
        fuzzy=catalog.fuzzy
    )
    
    # 复制头部元数据
    if hasattr(catalog, 'metadata'):
        for key, value in catalog.metadata.items():
            new_catalog.metadata[key] = value
    
    # 去重添加消息
    seen_msgids = set()
    duplicates = 0
    
    for message in catalog:
        if message.id == '':  # 跳过文件头
            continue
            
        msgid = message.id
        if isinstance(msgid, tuple):  # 处理复数形式
            msgid_key = msgid[0] if msgid[0] else msgid[1]
        else:
            msgid_key = msgid
            
        if msgid_key not in seen_msgids:
            seen_msgids.add(msgid_key)
            new_catalog.add(
                msgid,
                string=message.string,
                locations=message.locations,
                flags=message.flags,
                auto_comments=message.auto_comments,
                user_comments=message.user_comments,
                previous_id=message.previous_id,
                lineno=message.lineno
            )
        else:
            duplicates += 1
            print(f"跳过重复: {msgid_key[:50]}...")
    
    print(f"重复条目数: {duplicates}")
    print(f"清理后消息数量: {len(new_catalog)}")
    
    # 写入清理后的文件
    with open(file_path, 'wb') as f:
        write_po(f, new_catalog, sort_output=True, sort_by_file=False)
    
    print("✅ 清理完成！")
    return len(new_catalog)

if __name__ == '__main__':
    en_file = 'app/translations/en/LC_MESSAGES/messages.po'
    try:
        result = clean_po_file(en_file)
        print(f"\n最终条目数: {result}")
        print("\n后续步骤:")
        print("1. 重新编译翻译: pybabel compile -d app/translations -l en")
        print("2. 测试应用翻译功能")
        print("3. 如果正常，可删除备份文件")
    except Exception as e:
        print(f"❌ 清理失败: {e}")
        import traceback
        traceback.print_exc()