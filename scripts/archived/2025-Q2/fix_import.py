import json
import os
import psycopg2
from psycopg2.extras import Json

# 数据库连接参数
db_url = "postgresql://pma_user:pma_password@localhost:5432/pma_db_local"

# 处理JSON数据中的类型问题
def fix_boolean_fields(data):
    # 修复布尔值字段
    boolean_fields = {
        'contacts': ['is_primary'],
        'permissions': ['can_view', 'can_edit', 'can_create', 'can_delete'],
        'companies': ['is_deleted'],
        'product_code_field_options': ['is_active'],
        'dictionaries': ['is_active']
    }
    
    for table, fields in boolean_fields.items():
        if table in data:
            for row in data[table]:
                for field in fields:
                    if field in row and isinstance(row[field], int):
                        row[field] = bool(row[field])
    
    return data

# 创建所需的表
def ensure_tables(conn):
    cursor = conn.cursor()
    
    # 创建缺失的表
    tables_to_create = [
        "CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL, PRIMARY KEY (version_num))",
    ]
    
    for sql in tables_to_create:
        cursor.execute(sql)
    
    conn.commit()
    cursor.close()

# 修复架构问题
def fix_schema(conn):
    cursor = conn.cursor()
    
    # 检查并添加缺失的列
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS company_id INTEGER")
    except:
        conn.rollback()
    
    try:
        cursor.execute("ALTER TABLE product_code_fields ADD COLUMN IF NOT EXISTS name_en VARCHAR(255)")
    except:
        conn.rollback()
        
    try:
        cursor.execute("ALTER TABLE product_subcategories ADD COLUMN IF NOT EXISTS position INTEGER")
    except:
        conn.rollback()
    
    conn.commit()
    cursor.close()

# 按正确顺序导入数据
def import_in_order(conn, data):
    # 导入顺序，先导入没有外键依赖的表
    import_order = [
        "alembic_version",
        "product_categories",
        "product_regions",
        "product_subcategories",
        "users",
        "companies",
        "contacts",
        "projects",
        "quotations",
        "quotation_details",
        "products",
        "dev_products",
        "dev_product_specs",
        "dictionaries",
        # 其他表...
    ]
    
    cursor = conn.cursor()
    
    for table in import_order:
        if table not in data or not data[table]:
            print(f"跳过表 {table} (无数据)")
            continue
            
        print(f"导入表: {table} ({len(data[table])} 行)")
        
        # 尝试清空表
        try:
            cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
            conn.commit()
        except Exception as e:
            print(f"清空表 {table} 失败: {e}")
            conn.rollback()
            continue
        
        # 导入数据
        for row in data[table]:
            # 构建INSERT语句
            columns = row.keys()
            placeholders = ["%s"] * len(columns)
            values = [
                Json(v) if isinstance(v, (dict, list)) else v 
                for v in row.values()
            ]
            
            sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)}) ON CONFLICT DO NOTHING;"
            
            try:
                cursor.execute(sql, values)
                conn.commit()
            except Exception as e:
                print(f"插入数据到表 {table} 失败: {e}")
                conn.rollback()
                continue

    cursor.close()

def main():
    # 加载JSON数据
    with open('db_export.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 修复布尔值
    data = fix_boolean_fields(data)
    
    # 连接数据库
    conn = psycopg2.connect(db_url)
    
    # 确保表存在
    ensure_tables(conn)
    
    # 修复架构
    fix_schema(conn)
    
    # 导入数据
    import_in_order(conn, data)
    
    conn.close()
    print("数据修复和导入完成！")

if __name__ == "__main__":
    main() 
import os
import psycopg2
from psycopg2.extras import Json

# 数据库连接参数
db_url = "postgresql://pma_user:pma_password@localhost:5432/pma_db_local"

# 处理JSON数据中的类型问题
def fix_boolean_fields(data):
    # 修复布尔值字段
    boolean_fields = {
        'contacts': ['is_primary'],
        'permissions': ['can_view', 'can_edit', 'can_create', 'can_delete'],
        'companies': ['is_deleted'],
        'product_code_field_options': ['is_active'],
        'dictionaries': ['is_active']
    }
    
    for table, fields in boolean_fields.items():
        if table in data:
            for row in data[table]:
                for field in fields:
                    if field in row and isinstance(row[field], int):
                        row[field] = bool(row[field])
    
    return data

# 创建所需的表
def ensure_tables(conn):
    cursor = conn.cursor()
    
    # 创建缺失的表
    tables_to_create = [
        "CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL, PRIMARY KEY (version_num))",
    ]
    
    for sql in tables_to_create:
        cursor.execute(sql)
    
    conn.commit()
    cursor.close()

# 修复架构问题
def fix_schema(conn):
    cursor = conn.cursor()
    
    # 检查并添加缺失的列
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS company_id INTEGER")
    except:
        conn.rollback()
    
    try:
        cursor.execute("ALTER TABLE product_code_fields ADD COLUMN IF NOT EXISTS name_en VARCHAR(255)")
    except:
        conn.rollback()
        
    try:
        cursor.execute("ALTER TABLE product_subcategories ADD COLUMN IF NOT EXISTS position INTEGER")
    except:
        conn.rollback()
    
    conn.commit()
    cursor.close()

# 按正确顺序导入数据
def import_in_order(conn, data):
    # 导入顺序，先导入没有外键依赖的表
    import_order = [
        "alembic_version",
        "product_categories",
        "product_regions",
        "product_subcategories",
        "users",
        "companies",
        "contacts",
        "projects",
        "quotations",
        "quotation_details",
        "products",
        "dev_products",
        "dev_product_specs",
        "dictionaries",
        # 其他表...
    ]
    
    cursor = conn.cursor()
    
    for table in import_order:
        if table not in data or not data[table]:
            print(f"跳过表 {table} (无数据)")
            continue
            
        print(f"导入表: {table} ({len(data[table])} 行)")
        
        # 尝试清空表
        try:
            cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
            conn.commit()
        except Exception as e:
            print(f"清空表 {table} 失败: {e}")
            conn.rollback()
            continue
        
        # 导入数据
        for row in data[table]:
            # 构建INSERT语句
            columns = row.keys()
            placeholders = ["%s"] * len(columns)
            values = [
                Json(v) if isinstance(v, (dict, list)) else v 
                for v in row.values()
            ]
            
            sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)}) ON CONFLICT DO NOTHING;"
            
            try:
                cursor.execute(sql, values)
                conn.commit()
            except Exception as e:
                print(f"插入数据到表 {table} 失败: {e}")
                conn.rollback()
                continue

    cursor.close()

def main():
    # 加载JSON数据
    with open('db_export.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 修复布尔值
    data = fix_boolean_fields(data)
    
    # 连接数据库
    conn = psycopg2.connect(db_url)
    
    # 确保表存在
    ensure_tables(conn)
    
    # 修复架构
    fix_schema(conn)
    
    # 导入数据
    import_in_order(conn, data)
    
    conn.close()
    print("数据修复和导入完成！")

if __name__ == "__main__":
    main() 