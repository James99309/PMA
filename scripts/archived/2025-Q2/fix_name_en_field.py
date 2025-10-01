#!/usr/bin/env python3
import sqlite3
import os

# 确保我们在项目根目录
db_path = "app.db"
if not os.path.exists(db_path):
    print(f"错误：找不到数据库文件 {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

def has_column(table, column):
    """检查表是否有指定列"""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [col["name"] for col in cursor.fetchall()]
    return column in columns

def fix_name_en_field():
    """确保name_en字段存在并正确设置"""
    print("开始修复产品编码字段表的name_en列...")
    
    # 检查name_en字段是否存在
    if not has_column("product_code_fields", "name_en"):
        print("name_en字段不存在，正在添加...")
        cursor.execute("ALTER TABLE product_code_fields ADD COLUMN name_en VARCHAR(100)")
        print("name_en字段已添加")
    else:
        print("name_en字段已存在")
    
    # 更新所有name_en为NULL的记录
    cursor.execute("UPDATE product_code_fields SET name_en = name WHERE name_en IS NULL")
    updated_rows = cursor.rowcount
    print(f"已将{updated_rows}条记录的name_en设置为name的值")
    
    # 提交更改
    conn.commit()
    
    # 验证更改
    cursor.execute("SELECT COUNT(*) FROM product_code_fields WHERE name_en IS NULL AND field_type = 'origin_location'")
    null_count = cursor.fetchone()[0]
    
    if null_count > 0:
        print(f"警告：仍有{null_count}条'origin_location'类型的记录没有name_en值")
    else:
        print("所有'origin_location'类型的记录现在都有name_en值")
    
    print("修复完成")

def update_field_to_1():
    """更新所有产地区字段的position和max_length为1"""
    print("更新所有产地区字段的位置和最大长度...")
    
    cursor.execute("""
        UPDATE product_code_fields 
        SET position = 1, max_length = 1, is_required = 1 
        WHERE field_type = 'origin_location'
    """)
    updated_rows = cursor.rowcount
    print(f"已更新{updated_rows}条记录")
    
    conn.commit()
    print("更新完成")

if __name__ == "__main__":
    try:
        fix_name_en_field()
        update_field_to_1()
        print("所有修复已完成")
    except Exception as e:
        print(f"修复过程中发生错误: {e}")
    finally:
        conn.close() 