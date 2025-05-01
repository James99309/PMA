#!/usr/bin/env python3
import sqlite3
import os
import string

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

def rename_table_columns():
    """从产地区改名为销售区域，并调整字段结构"""
    print("开始迁移产品编码字段表结构...")
    
    # 1. 检查并添加description字段
    if not has_column("product_code_fields", "description"):
        print("添加description字段...")
        cursor.execute("ALTER TABLE product_code_fields ADD COLUMN description TEXT")
        print("description字段已添加")
    else:
        print("description字段已存在")
    
    # 2. 检查并添加code字段
    code_exists = has_column("product_code_fields", "code")
    if not code_exists:
        print("添加code字段...")
        cursor.execute("ALTER TABLE product_code_fields ADD COLUMN code VARCHAR(10)")
        print("code字段已添加")
    else:
        print("code字段已存在")
    
    # 3. 如果有name_en字段，将其内容复制到code字段
    name_en_exists = has_column("product_code_fields", "name_en")
    if name_en_exists and code_exists:
        print("将name_en的值迁移到code字段...")
        cursor.execute("UPDATE product_code_fields SET code = name_en WHERE code IS NULL AND name_en IS NOT NULL")
        rows_updated = cursor.rowcount
        print(f"已更新{rows_updated}条记录")
    
    # 4. 获取所有'origin_location'类型的字段
    cursor.execute("SELECT id, name, code FROM product_code_fields WHERE field_type = 'origin_location'")
    fields = cursor.fetchall()
    
    # 5. 为没有code的字段生成唯一编码
    if fields:
        print(f"找到{len(fields)}个销售区域字段，开始生成编码...")
        
        # 获取所有已用的编码
        cursor.execute("SELECT code FROM product_code_field_options")
        options = cursor.fetchall()
        used_codes = {opt['code'] for opt in options if opt['code']}
        
        # 已经分配给字段的编码
        field_codes = {field['code'] for field in fields if field['code']}
        used_codes.update(field_codes)
        
        # 可用字母
        available_letters = [c for c in string.ascii_uppercase if c not in used_codes]
        
        for field in fields:
            field_id = field['id']
            if not field['code']:
                # 生成新编码
                new_code = None
                if available_letters:
                    new_code = available_letters.pop(0)
                else:
                    # 如果字母用完，使用数字
                    for num in range(1, 10):
                        num_code = str(num)
                        if num_code not in used_codes:
                            new_code = num_code
                            used_codes.add(num_code)
                            break
                
                if new_code:
                    print(f"为字段 '{field['name']}' 生成编码: {new_code}")
                    
                    # 更新字段的code
                    cursor.execute("UPDATE product_code_fields SET code = ? WHERE id = ?", 
                                 (new_code, field_id))
                    
                    # 检查是否已有关联选项
                    cursor.execute("SELECT id FROM product_code_field_options WHERE field_id = ?", (field_id,))
                    option = cursor.fetchone()
                    
                    if option:
                        # 更新现有选项
                        cursor.execute("""
                            UPDATE product_code_field_options 
                            SET code = ?, description = ? 
                            WHERE field_id = ?
                        """, (new_code, f"自动生成的销售区域编码: {field['name']}", field_id))
                    else:
                        # 创建新选项
                        cursor.execute("""
                            INSERT INTO product_code_field_options 
                            (field_id, value, code, description, is_active) 
                            VALUES (?, ?, ?, ?, 1)
                        """, (field_id, field['name'], new_code, f"自动生成的销售区域编码: {field['name']}"))
    
    # 提交所有更改
    conn.commit()
    print("数据库结构更新完成！")

if __name__ == "__main__":
    try:
        rename_table_columns()
        print("所有迁移已完成")
    except Exception as e:
        print(f"迁移过程中发生错误: {e}")
    finally:
        conn.close() 