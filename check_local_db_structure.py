#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查本地数据库结构

该脚本用于检查本地数据库的结构，特别是验证projects表是否有rating字段。
"""

import os
import sys
from sqlalchemy import create_engine, inspect, text

def main():
    # 连接本地数据库
    local_db_url = os.environ.get('DATABASE_URL', 'postgresql://pma_user:pma_password@localhost:5432/pma_db_local')
    
    print(f"连接本地数据库: {local_db_url}")
    
    try:
        engine = create_engine(local_db_url)
        inspector = inspect(engine)
        
        # 获取所有表
        tables = inspector.get_table_names()
        print(f"\n本地数据库共有 {len(tables)} 个表:")
        
        for table in sorted(tables):
            print(f"  - {table}")
        
        # 特别检查projects表
        if 'projects' in tables:
            print(f"\n=== projects表结构 ===")
            columns = inspector.get_columns('projects')
            
            for col in columns:
                print(f"  {col['name']}: {col['type']} {'NULL' if col['nullable'] else 'NOT NULL'}")
            
            # 检查rating字段
            rating_exists = any(col['name'] == 'rating' for col in columns)
            if rating_exists:
                print("\n✓ projects表已包含rating字段")
                
                # 查询rating字段的详细信息
                with engine.connect() as conn:
                    result = conn.execute(text("""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns 
                        WHERE table_name = 'projects' AND column_name = 'rating'
                    """))
                    
                    for row in result:
                        print(f"  rating字段详情: {row[1]} {'NULL' if row[2] == 'YES' else 'NOT NULL'} 默认值: {row[3]}")
            else:
                print("\n⚠ projects表缺少rating字段")
        else:
            print("\n❌ 未找到projects表")
        
        # 检查companies表
        if 'companies' in tables:
            print(f"\n=== companies表结构 ===")
            columns = inspector.get_columns('companies')
            
            region_exists = any(col['name'] == 'region' for col in columns)
            province_exists = any(col['name'] == 'province' for col in columns)
            
            print(f"  region字段: {'✓ 存在' if region_exists else '❌ 缺失'}")
            print(f"  province字段: {'✓ 存在' if province_exists else '❌ 缺失'}")
        
        print(f"\n=== 数据库连接信息 ===")
        with engine.connect() as conn:
            # 检查数据库版本
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"PostgreSQL版本: {version.split(',')[0]}")
            
            # 检查当前数据库
            result = conn.execute(text("SELECT current_database()"))
            db_name = result.fetchone()[0]
            print(f"当前数据库: {db_name}")
            
            # 检查表数量
            result = conn.execute(text("""
                SELECT count(*) FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """))
            table_count = result.fetchone()[0]
            print(f"用户表数量: {table_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ 连接失败: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 