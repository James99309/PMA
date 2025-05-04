#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render PostgreSQL 数据导入布尔值修复工具
处理更多特殊的布尔字段
"""

import os
import sys
import json
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('fix_more_bool_fields.log')
    ]
)
logger = logging.getLogger('布尔值修复')

# 需要特殊处理的额外布尔字段
TABLE_EXTRA_BOOL_FIELDS = {
    "permissions": ["can_create"], 
    "product_code_fields": ["use_in_code"]
}

def load_json_data(json_file):
    """加载JSON数据文件"""
    logger.info(f"加载JSON数据文件: {json_file}")
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"JSON数据加载成功，包含 {len(data)} 个表")
        return data
    except Exception as e:
        logger.error(f"加载JSON数据失败: {str(e)}")
        sys.exit(1)

def fix_boolean_values(data):
    """修复布尔值字段"""
    for table_name, table_data in data.items():
        if table_name in TABLE_EXTRA_BOOL_FIELDS:
            bool_fields = TABLE_EXTRA_BOOL_FIELDS[table_name]
            logger.info(f"处理表 {table_name}...")
            logger.info(f"表 {table_name} 中发现以下布尔字段: {bool_fields}")
            
            # 修复每一条记录
            for record in table_data:
                for field in bool_fields:
                    if field in record and record[field] is not None:
                        # 将整数转换为布尔值
                        if isinstance(record[field], int):
                            record[field] = bool(record[field])
                            
            logger.info(f"表 {table_name} 处理完成，共 {len(table_data)} 条记录")
    
    return data

def main():
    """主函数"""
    if len(sys.argv) != 3:
        print("用法: python fix_more_bool_fields.py <input_json> <output_json>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # 加载JSON数据
    data = load_json_data(input_file)
    
    # 修复布尔值
    fixed_data = fix_boolean_values(data)
    
    # 保存修复后的数据
    logger.info(f"保存修复后的数据到: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(fixed_data, f, ensure_ascii=False, indent=2)
    
    logger.info("数据修复完成！")

if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-
"""
Render PostgreSQL 数据导入布尔值修复工具
处理更多特殊的布尔字段
"""

import os
import sys
import json
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('fix_more_bool_fields.log')
    ]
)
logger = logging.getLogger('布尔值修复')

# 需要特殊处理的额外布尔字段
TABLE_EXTRA_BOOL_FIELDS = {
    "permissions": ["can_create"], 
    "product_code_fields": ["use_in_code"]
}

def load_json_data(json_file):
    """加载JSON数据文件"""
    logger.info(f"加载JSON数据文件: {json_file}")
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"JSON数据加载成功，包含 {len(data)} 个表")
        return data
    except Exception as e:
        logger.error(f"加载JSON数据失败: {str(e)}")
        sys.exit(1)

def fix_boolean_values(data):
    """修复布尔值字段"""
    for table_name, table_data in data.items():
        if table_name in TABLE_EXTRA_BOOL_FIELDS:
            bool_fields = TABLE_EXTRA_BOOL_FIELDS[table_name]
            logger.info(f"处理表 {table_name}...")
            logger.info(f"表 {table_name} 中发现以下布尔字段: {bool_fields}")
            
            # 修复每一条记录
            for record in table_data:
                for field in bool_fields:
                    if field in record and record[field] is not None:
                        # 将整数转换为布尔值
                        if isinstance(record[field], int):
                            record[field] = bool(record[field])
                            
            logger.info(f"表 {table_name} 处理完成，共 {len(table_data)} 条记录")
    
    return data

def main():
    """主函数"""
    if len(sys.argv) != 3:
        print("用法: python fix_more_bool_fields.py <input_json> <output_json>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # 加载JSON数据
    data = load_json_data(input_file)
    
    # 修复布尔值
    fixed_data = fix_boolean_values(data)
    
    # 保存修复后的数据
    logger.info(f"保存修复后的数据到: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(fixed_data, f, ensure_ascii=False, indent=2)
    
    logger.info("数据修复完成！")

if __name__ == "__main__":
    main() 
 
 
# -*- coding: utf-8 -*-
"""
Render PostgreSQL 数据导入布尔值修复工具
处理更多特殊的布尔字段
"""

import os
import sys
import json
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('fix_more_bool_fields.log')
    ]
)
logger = logging.getLogger('布尔值修复')

# 需要特殊处理的额外布尔字段
TABLE_EXTRA_BOOL_FIELDS = {
    "permissions": ["can_create"], 
    "product_code_fields": ["use_in_code"]
}

def load_json_data(json_file):
    """加载JSON数据文件"""
    logger.info(f"加载JSON数据文件: {json_file}")
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"JSON数据加载成功，包含 {len(data)} 个表")
        return data
    except Exception as e:
        logger.error(f"加载JSON数据失败: {str(e)}")
        sys.exit(1)

def fix_boolean_values(data):
    """修复布尔值字段"""
    for table_name, table_data in data.items():
        if table_name in TABLE_EXTRA_BOOL_FIELDS:
            bool_fields = TABLE_EXTRA_BOOL_FIELDS[table_name]
            logger.info(f"处理表 {table_name}...")
            logger.info(f"表 {table_name} 中发现以下布尔字段: {bool_fields}")
            
            # 修复每一条记录
            for record in table_data:
                for field in bool_fields:
                    if field in record and record[field] is not None:
                        # 将整数转换为布尔值
                        if isinstance(record[field], int):
                            record[field] = bool(record[field])
                            
            logger.info(f"表 {table_name} 处理完成，共 {len(table_data)} 条记录")
    
    return data

def main():
    """主函数"""
    if len(sys.argv) != 3:
        print("用法: python fix_more_bool_fields.py <input_json> <output_json>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # 加载JSON数据
    data = load_json_data(input_file)
    
    # 修复布尔值
    fixed_data = fix_boolean_values(data)
    
    # 保存修复后的数据
    logger.info(f"保存修复后的数据到: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(fixed_data, f, ensure_ascii=False, indent=2)
    
    logger.info("数据修复完成！")

if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-
"""
Render PostgreSQL 数据导入布尔值修复工具
处理更多特殊的布尔字段
"""

import os
import sys
import json
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('fix_more_bool_fields.log')
    ]
)
logger = logging.getLogger('布尔值修复')

# 需要特殊处理的额外布尔字段
TABLE_EXTRA_BOOL_FIELDS = {
    "permissions": ["can_create"], 
    "product_code_fields": ["use_in_code"]
}

def load_json_data(json_file):
    """加载JSON数据文件"""
    logger.info(f"加载JSON数据文件: {json_file}")
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"JSON数据加载成功，包含 {len(data)} 个表")
        return data
    except Exception as e:
        logger.error(f"加载JSON数据失败: {str(e)}")
        sys.exit(1)

def fix_boolean_values(data):
    """修复布尔值字段"""
    for table_name, table_data in data.items():
        if table_name in TABLE_EXTRA_BOOL_FIELDS:
            bool_fields = TABLE_EXTRA_BOOL_FIELDS[table_name]
            logger.info(f"处理表 {table_name}...")
            logger.info(f"表 {table_name} 中发现以下布尔字段: {bool_fields}")
            
            # 修复每一条记录
            for record in table_data:
                for field in bool_fields:
                    if field in record and record[field] is not None:
                        # 将整数转换为布尔值
                        if isinstance(record[field], int):
                            record[field] = bool(record[field])
                            
            logger.info(f"表 {table_name} 处理完成，共 {len(table_data)} 条记录")
    
    return data

def main():
    """主函数"""
    if len(sys.argv) != 3:
        print("用法: python fix_more_bool_fields.py <input_json> <output_json>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # 加载JSON数据
    data = load_json_data(input_file)
    
    # 修复布尔值
    fixed_data = fix_boolean_values(data)
    
    # 保存修复后的数据
    logger.info(f"保存修复后的数据到: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(fixed_data, f, ensure_ascii=False, indent=2)
    
    logger.info("数据修复完成！")

if __name__ == "__main__":
    main() 
 
 