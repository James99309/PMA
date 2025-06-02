#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查云端数据库结构

该脚本用于检查云端数据库的结构，特别是验证projects表是否有rating字段。
"""

import os
import sys
from sqlalchemy import create_engine, inspect, text

def main():
    # 连接云端数据库
    cloud_db_url = os.environ.get('RENDER_DATABASE_URL')
    
    if not cloud_db_url:
        print("❌ 未设置 RENDER_DATABASE_URL 环境变量")
        print("请先设置：export RENDER_DATABASE_URL=\"你的云端数据库URL\"")
        return
    
    print(f"连接云端数据库...")
    
    try:
        engine = create_engine(cloud_db_url)
        inspector = inspect(engine)
        
        # 获取所有表
        tables = inspector.get_table_names()
        print(f"\n云端数据库共有 {len(tables)} 个表:")
        
        for table in sorted(tables):
            print(f"  - {table}")
        
        # 特别检查projects表
        if 'projects' in tables:
            print(f"\n=== projects表结构 ===")
            columns = inspector.get_columns('projects')
            
            has_rating = False
            for column in columns:
                print(f"  {column['name']}: {column['type']} {'NOT NULL' if not column['nullable'] else 'NULL'}")
                if column['name'] == 'rating':
                    has_rating = True
                    print(f"✓ projects表已包含rating字段")
                    print(f"  rating字段详情: {column['type']} {'NOT NULL' if not column['nullable'] else 'NULL'} 默认值: {column.get('default', 'None')}")
            
            if not has_rating:
                print("❌ projects表缺少rating字段")
        else:
            print("❌ 未找到projects表")
        
        # 检查companies表
        if 'companies' in tables:
            print(f"\n=== companies表结构 ===")
            company_columns = inspector.get_columns('companies')
            
            has_region = False
            has_province = False
            
            for column in company_columns:
                if column['name'] == 'region':
                    has_region = True
                elif column['name'] == 'province':
                    has_province = True
            
            print(f"  region字段: {'✓ 存在' if has_region else '❌ 缺失'}")
            print(f"  province字段: {'✓ 存在' if has_province else '❌ 缺失'}")
        
        # 获取数据库信息
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            
            result = conn.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            
            print(f"\n=== 数据库连接信息 ===")
            print(f"PostgreSQL版本: {version}")
            print(f"当前数据库: {db_name}")
            print(f"表数量: {len(tables)}")
        
        print("\n✅ 云端数据库检查完成")
        
    except Exception as e:
        print(f"❌ 连接云端数据库失败: {e}")
        return

if __name__ == "__main__":
    main() 