#!/usr/bin/env python3
"""
检查数据库中projects表的结构
确认dealer_manager_id字段是否已被删除
"""

import os
import sys
from sqlalchemy import create_engine, text

def check_projects_table_structure():
    """检查projects表的结构"""
    
    # 从环境变量获取数据库URL
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("错误: 未找到DATABASE_URL环境变量")
        return False
    
    try:
        # 创建数据库连接
        engine = create_engine(database_url)
        
        with engine.connect() as connection:
            # 查询projects表的所有列
            result = connection.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'projects' 
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            
            print("Projects表的当前结构:")
            print("-" * 50)
            
            dealer_manager_found = False
            for column in columns:
                column_name, data_type, is_nullable = column
                print(f"{column_name:<30} {data_type:<20} {'NULL' if is_nullable == 'YES' else 'NOT NULL'}")
                
                if column_name == 'dealer_manager_id':
                    dealer_manager_found = True
            
            print("-" * 50)
            
            if dealer_manager_found:
                print("❌ 错误: dealer_manager_id字段仍然存在于数据库中!")
                print("   请确认迁移是否已正确执行")
                return False
            else:
                print("✅ 正确: dealer_manager_id字段已从数据库中删除")
                
            # 检查外键约束
            constraint_result = connection.execute(text("""
                SELECT constraint_name
                FROM information_schema.table_constraints 
                WHERE table_name = 'projects' 
                AND constraint_type = 'FOREIGN KEY'
                AND constraint_name LIKE '%dealer_manager%'
            """))
            
            constraints = constraint_result.fetchall()
            if constraints:
                print("❌ 错误: 发现dealer_manager相关的外键约束:")
                for constraint in constraints:
                    print(f"   - {constraint[0]}")
                return False
            else:
                print("✅ 正确: 没有发现dealer_manager相关的外键约束")
                
            return True
            
    except Exception as e:
        print(f"错误: 检查数据库结构失败: {str(e)}")
        return False

if __name__ == "__main__":
    success = check_projects_table_structure()
    sys.exit(0 if success else 1) 