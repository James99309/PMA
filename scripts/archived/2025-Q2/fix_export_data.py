#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite导出数据修复工具
修复从SQLite导出的JSON数据中的类型问题，用于PostgreSQL导入
"""

import json
import logging
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data_fix.log')
    ]
)
logger = logging.getLogger('数据修复')

# 字段类型定义字典 - 根据字段名定义类型
BOOLEAN_FIELDS = [
    "is_active", "is_required", "is_primary", "is_deleted", "is_profile_complete", 
    "can_view", "can_add", "can_edit", "can_delete", "is_admin", "include_in_code",
    "is_enabled", "is_default", "is_superuser", "is_staff", "is_global", "is_public",
    "include_in_name", "is_customer", "is_supplier", "is_partner", "is_department_manager"
]

# 需要处理的表和字段对应关系 - 为了处理特殊情况
TABLE_BOOLEAN_FIELDS = {
    "users": ["is_active", "is_admin", "is_profile_complete", "is_department_manager"],
    "projects": ["is_deleted"],
    "companies": ["is_deleted"],
    "contacts": ["is_primary"],
    "permissions": ["can_view", "can_add", "can_edit", "can_delete"],
    "dictionaries": ["is_active"],
    "product_code_fields": ["is_required", "include_in_code", "is_active"],
    "product_code_field_options": ["is_active"],
}

def fix_boolean_values(data):
    """修复JSON数据中的布尔值"""
    fixed_data = {}
    
    for table_name, records in data.items():
        logger.info(f"处理表 {table_name}...")
        if not records:
            fixed_data[table_name] = []
            continue
        
        fixed_records = []
        boolean_fields = set()
        
        # 确定该表中的布尔字段
        if table_name in TABLE_BOOLEAN_FIELDS:
            boolean_fields.update(TABLE_BOOLEAN_FIELDS[table_name])
        
        # 添加通用布尔字段
        for field in BOOLEAN_FIELDS:
            for record in records:
                if field in record:
                    boolean_fields.add(field)
                    break
        
        logger.info(f"表 {table_name} 中发现以下布尔字段: {list(boolean_fields)}")
        
        # 修复每条记录
        for record in records:
            fixed_record = {}
            
            for field, value in record.items():
                # 如果是布尔字段，转换为布尔值
                if field in boolean_fields and value is not None:
                    if isinstance(value, int):
                        fixed_record[field] = bool(value)
                        # 只记录第一次发现的转换，避免日志过多
                        if field not in boolean_fields:
                            logger.info(f"转换字段 {field} 的值 {value} 为布尔值 {bool(value)}")
                    else:
                        fixed_record[field] = value
                else:
                    fixed_record[field] = value
            
            fixed_records.append(fixed_record)
        
        fixed_data[table_name] = fixed_records
        logger.info(f"表 {table_name} 处理完成，共 {len(fixed_records)} 条记录")
    
    return fixed_data

def main():
    if len(sys.argv) < 3:
        logger.error("用法: python fix_export_data.py <输入JSON文件> <输出JSON文件>")
        return 1
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        # 加载JSON数据
        logger.info(f"加载JSON数据文件: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"JSON数据加载成功，包含 {len(data)} 个表")
        
        # 修复布尔值
        fixed_data = fix_boolean_values(data)
        
        # 保存修复后的数据
        logger.info(f"保存修复后的数据到: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(fixed_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"数据修复完成！")
        return 0
    
    except Exception as e:
        logger.error(f"数据修复失败: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-
"""
SQLite导出数据修复工具
修复从SQLite导出的JSON数据中的类型问题，用于PostgreSQL导入
"""

import json
import logging
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data_fix.log')
    ]
)
logger = logging.getLogger('数据修复')

# 字段类型定义字典 - 根据字段名定义类型
BOOLEAN_FIELDS = [
    "is_active", "is_required", "is_primary", "is_deleted", "is_profile_complete", 
    "can_view", "can_add", "can_edit", "can_delete", "is_admin", "include_in_code",
    "is_enabled", "is_default", "is_superuser", "is_staff", "is_global", "is_public",
    "include_in_name", "is_customer", "is_supplier", "is_partner", "is_department_manager"
]

# 需要处理的表和字段对应关系 - 为了处理特殊情况
TABLE_BOOLEAN_FIELDS = {
    "users": ["is_active", "is_admin", "is_profile_complete", "is_department_manager"],
    "projects": ["is_deleted"],
    "companies": ["is_deleted"],
    "contacts": ["is_primary"],
    "permissions": ["can_view", "can_add", "can_edit", "can_delete"],
    "dictionaries": ["is_active"],
    "product_code_fields": ["is_required", "include_in_code", "is_active"],
    "product_code_field_options": ["is_active"],
}

def fix_boolean_values(data):
    """修复JSON数据中的布尔值"""
    fixed_data = {}
    
    for table_name, records in data.items():
        logger.info(f"处理表 {table_name}...")
        if not records:
            fixed_data[table_name] = []
            continue
        
        fixed_records = []
        boolean_fields = set()
        
        # 确定该表中的布尔字段
        if table_name in TABLE_BOOLEAN_FIELDS:
            boolean_fields.update(TABLE_BOOLEAN_FIELDS[table_name])
        
        # 添加通用布尔字段
        for field in BOOLEAN_FIELDS:
            for record in records:
                if field in record:
                    boolean_fields.add(field)
                    break
        
        logger.info(f"表 {table_name} 中发现以下布尔字段: {list(boolean_fields)}")
        
        # 修复每条记录
        for record in records:
            fixed_record = {}
            
            for field, value in record.items():
                # 如果是布尔字段，转换为布尔值
                if field in boolean_fields and value is not None:
                    if isinstance(value, int):
                        fixed_record[field] = bool(value)
                        # 只记录第一次发现的转换，避免日志过多
                        if field not in boolean_fields:
                            logger.info(f"转换字段 {field} 的值 {value} 为布尔值 {bool(value)}")
                    else:
                        fixed_record[field] = value
                else:
                    fixed_record[field] = value
            
            fixed_records.append(fixed_record)
        
        fixed_data[table_name] = fixed_records
        logger.info(f"表 {table_name} 处理完成，共 {len(fixed_records)} 条记录")
    
    return fixed_data

def main():
    if len(sys.argv) < 3:
        logger.error("用法: python fix_export_data.py <输入JSON文件> <输出JSON文件>")
        return 1
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        # 加载JSON数据
        logger.info(f"加载JSON数据文件: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"JSON数据加载成功，包含 {len(data)} 个表")
        
        # 修复布尔值
        fixed_data = fix_boolean_values(data)
        
        # 保存修复后的数据
        logger.info(f"保存修复后的数据到: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(fixed_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"数据修复完成！")
        return 0
    
    except Exception as e:
        logger.error(f"数据修复失败: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
 
 
# -*- coding: utf-8 -*-
"""
SQLite导出数据修复工具
修复从SQLite导出的JSON数据中的类型问题，用于PostgreSQL导入
"""

import json
import logging
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data_fix.log')
    ]
)
logger = logging.getLogger('数据修复')

# 字段类型定义字典 - 根据字段名定义类型
BOOLEAN_FIELDS = [
    "is_active", "is_required", "is_primary", "is_deleted", "is_profile_complete", 
    "can_view", "can_add", "can_edit", "can_delete", "is_admin", "include_in_code",
    "is_enabled", "is_default", "is_superuser", "is_staff", "is_global", "is_public",
    "include_in_name", "is_customer", "is_supplier", "is_partner", "is_department_manager"
]

# 需要处理的表和字段对应关系 - 为了处理特殊情况
TABLE_BOOLEAN_FIELDS = {
    "users": ["is_active", "is_admin", "is_profile_complete", "is_department_manager"],
    "projects": ["is_deleted"],
    "companies": ["is_deleted"],
    "contacts": ["is_primary"],
    "permissions": ["can_view", "can_add", "can_edit", "can_delete"],
    "dictionaries": ["is_active"],
    "product_code_fields": ["is_required", "include_in_code", "is_active"],
    "product_code_field_options": ["is_active"],
}

def fix_boolean_values(data):
    """修复JSON数据中的布尔值"""
    fixed_data = {}
    
    for table_name, records in data.items():
        logger.info(f"处理表 {table_name}...")
        if not records:
            fixed_data[table_name] = []
            continue
        
        fixed_records = []
        boolean_fields = set()
        
        # 确定该表中的布尔字段
        if table_name in TABLE_BOOLEAN_FIELDS:
            boolean_fields.update(TABLE_BOOLEAN_FIELDS[table_name])
        
        # 添加通用布尔字段
        for field in BOOLEAN_FIELDS:
            for record in records:
                if field in record:
                    boolean_fields.add(field)
                    break
        
        logger.info(f"表 {table_name} 中发现以下布尔字段: {list(boolean_fields)}")
        
        # 修复每条记录
        for record in records:
            fixed_record = {}
            
            for field, value in record.items():
                # 如果是布尔字段，转换为布尔值
                if field in boolean_fields and value is not None:
                    if isinstance(value, int):
                        fixed_record[field] = bool(value)
                        # 只记录第一次发现的转换，避免日志过多
                        if field not in boolean_fields:
                            logger.info(f"转换字段 {field} 的值 {value} 为布尔值 {bool(value)}")
                    else:
                        fixed_record[field] = value
                else:
                    fixed_record[field] = value
            
            fixed_records.append(fixed_record)
        
        fixed_data[table_name] = fixed_records
        logger.info(f"表 {table_name} 处理完成，共 {len(fixed_records)} 条记录")
    
    return fixed_data

def main():
    if len(sys.argv) < 3:
        logger.error("用法: python fix_export_data.py <输入JSON文件> <输出JSON文件>")
        return 1
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        # 加载JSON数据
        logger.info(f"加载JSON数据文件: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"JSON数据加载成功，包含 {len(data)} 个表")
        
        # 修复布尔值
        fixed_data = fix_boolean_values(data)
        
        # 保存修复后的数据
        logger.info(f"保存修复后的数据到: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(fixed_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"数据修复完成！")
        return 0
    
    except Exception as e:
        logger.error(f"数据修复失败: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-
"""
SQLite导出数据修复工具
修复从SQLite导出的JSON数据中的类型问题，用于PostgreSQL导入
"""

import json
import logging
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data_fix.log')
    ]
)
logger = logging.getLogger('数据修复')

# 字段类型定义字典 - 根据字段名定义类型
BOOLEAN_FIELDS = [
    "is_active", "is_required", "is_primary", "is_deleted", "is_profile_complete", 
    "can_view", "can_add", "can_edit", "can_delete", "is_admin", "include_in_code",
    "is_enabled", "is_default", "is_superuser", "is_staff", "is_global", "is_public",
    "include_in_name", "is_customer", "is_supplier", "is_partner", "is_department_manager"
]

# 需要处理的表和字段对应关系 - 为了处理特殊情况
TABLE_BOOLEAN_FIELDS = {
    "users": ["is_active", "is_admin", "is_profile_complete", "is_department_manager"],
    "projects": ["is_deleted"],
    "companies": ["is_deleted"],
    "contacts": ["is_primary"],
    "permissions": ["can_view", "can_add", "can_edit", "can_delete"],
    "dictionaries": ["is_active"],
    "product_code_fields": ["is_required", "include_in_code", "is_active"],
    "product_code_field_options": ["is_active"],
}

def fix_boolean_values(data):
    """修复JSON数据中的布尔值"""
    fixed_data = {}
    
    for table_name, records in data.items():
        logger.info(f"处理表 {table_name}...")
        if not records:
            fixed_data[table_name] = []
            continue
        
        fixed_records = []
        boolean_fields = set()
        
        # 确定该表中的布尔字段
        if table_name in TABLE_BOOLEAN_FIELDS:
            boolean_fields.update(TABLE_BOOLEAN_FIELDS[table_name])
        
        # 添加通用布尔字段
        for field in BOOLEAN_FIELDS:
            for record in records:
                if field in record:
                    boolean_fields.add(field)
                    break
        
        logger.info(f"表 {table_name} 中发现以下布尔字段: {list(boolean_fields)}")
        
        # 修复每条记录
        for record in records:
            fixed_record = {}
            
            for field, value in record.items():
                # 如果是布尔字段，转换为布尔值
                if field in boolean_fields and value is not None:
                    if isinstance(value, int):
                        fixed_record[field] = bool(value)
                        # 只记录第一次发现的转换，避免日志过多
                        if field not in boolean_fields:
                            logger.info(f"转换字段 {field} 的值 {value} 为布尔值 {bool(value)}")
                    else:
                        fixed_record[field] = value
                else:
                    fixed_record[field] = value
            
            fixed_records.append(fixed_record)
        
        fixed_data[table_name] = fixed_records
        logger.info(f"表 {table_name} 处理完成，共 {len(fixed_records)} 条记录")
    
    return fixed_data

def main():
    if len(sys.argv) < 3:
        logger.error("用法: python fix_export_data.py <输入JSON文件> <输出JSON文件>")
        return 1
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        # 加载JSON数据
        logger.info(f"加载JSON数据文件: {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"JSON数据加载成功，包含 {len(data)} 个表")
        
        # 修复布尔值
        fixed_data = fix_boolean_values(data)
        
        # 保存修复后的数据
        logger.info(f"保存修复后的数据到: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(fixed_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"数据修复完成！")
        return 0
    
    except Exception as e:
        logger.error(f"数据修复失败: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
 
 