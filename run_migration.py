#!/usr/bin/env python3
"""
数据库迁移脚本 - 修复DevProduct和DevProductSpec表结构
"""
from app import create_app, db
from app.models.dev_product import DevProduct, DevProductSpec
import sqlite3
import time

app = create_app()

def add_column_if_not_exists(table, column, column_type):
    """向表中添加列（如果不存在）"""
    try:
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        # 检查列是否存在
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [info[1] for info in cursor.fetchall()]
        
        if column not in columns:
            print(f"添加列：{table}.{column} ({column_type})")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
            conn.commit()
            print(f"成功添加列 {column}")
        else:
            print(f"列 {column} 已存在，跳过")
            
        conn.close()
        return True
    except Exception as e:
        print(f"添加列失败: {str(e)}")
        return False

def rename_column_if_exists(table, old_column, new_column):
    """重命名表中的列（如果存在）"""
    try:
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        # 检查列是否存在
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [info[1] for info in cursor.fetchall()]
        
        if old_column in columns and new_column not in columns:
            print(f"重命名列：{table}.{old_column} -> {new_column}")
            
            # SQLite不直接支持重命名列，需要创建新表、复制数据并重命名
            # 这里采用更简单的方法：创建新的列然后复制数据
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {new_column} TEXT")
            cursor.execute(f"UPDATE {table} SET {new_column} = {old_column}")
            conn.commit()
            print(f"成功重命名列 {old_column} -> {new_column}")
        else:
            if new_column in columns:
                print(f"目标列 {new_column} 已存在，跳过")
            else:
                print(f"源列 {old_column} 不存在，跳过")
            
        conn.close()
        return True
    except Exception as e:
        print(f"重命名列失败: {str(e)}")
        return False

with app.app_context():
    print("开始数据库迁移...")
    
    # 添加缺失的列到 dev_products 表
    add_column_if_not_exists('dev_products', 'name', 'TEXT')
    add_column_if_not_exists('dev_products', 'created_by', 'INTEGER')
    add_column_if_not_exists('dev_products', 'mn_code', 'TEXT')
    
    # 重命名 dev_product_specs 表中的列
    # 注意：这是不安全的方法。在生产环境应使用合适的数据库迁移工具
    rename_column_if_exists('dev_product_specs', 'product_id', 'dev_product_id')
    rename_column_if_exists('dev_product_specs', 'name', 'field_name')
    rename_column_if_exists('dev_product_specs', 'value', 'field_value')
    
    # 重新创建表结构
    print("更新数据库表结构...")
    db.create_all()
    
    print("数据库迁移完成，请重启应用程序") 