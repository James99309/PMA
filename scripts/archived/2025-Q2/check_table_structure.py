#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查恢复后的表结构
"""

import psycopg2
from urllib.parse import urlparse
from config import CLOUD_DB_URL

def check_table_structure():
    """检查关键表的结构"""
    parsed_url = urlparse(CLOUD_DB_URL)
    
    try:
        conn = psycopg2.connect(
            host=parsed_url.hostname,
            port=parsed_url.port or 5432,
            database=parsed_url.path.strip('/'),
            user=parsed_url.username,
            password=parsed_url.password
        )
        
        tables_to_check = [
            'quotation_details', 'quotations', 'projects', 
            'companies', 'contacts', 'products'
        ]
        
        with conn.cursor() as cursor:
            for table_name in tables_to_check:
                print(f"\n📋 表 {table_name} 的结构:")
                print("-" * 50)
                
                cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' 
                    ORDER BY ordinal_position
                """)
                
                columns = cursor.fetchall()
                
                if columns:
                    for col_name, data_type, is_nullable, default in columns:
                        nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
                        default_str = f" DEFAULT {default}" if default else ""
                        print(f"  {col_name:<25} {data_type:<15} {nullable}{default_str}")
                else:
                    print(f"  表 {table_name} 不存在或无权限访问")
                
                # 检查记录数
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"  📊 记录数: {count:,}")
                except Exception as e:
                    print(f"  ❌ 无法获取记录数: {str(e)}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查表结构失败: {str(e)}")

if __name__ == "__main__":
    check_table_structure() 