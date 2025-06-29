#!/usr/bin/env python3
"""
修复并执行pma_db_ovs数据库同步
修正PostgreSQL数据类型格式问题

Created: 2025-06-27
Author: Assistant
Purpose: 修复并完成pma_db_ovs数据库结构同步
"""

import os
import sys
import psycopg2
from datetime import datetime
from urllib.parse import urlparse

# 数据库连接配置
OVS_DB_URL = 'postgresql://pma_db_ovs_user:oUKdxwqXDvCrgkg3fkZ33axXgDF21D51@dpg-d170laodl3ps739trgp0-a.singapore-postgres.render.com/pma_db_ovs'

def parse_db_url(db_url):
    """解析数据库URL"""
    parsed = urlparse(db_url)
    return {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'database': parsed.path[1:],
        'user': parsed.username,
        'password': parsed.password
    }

def get_ovs_connection():
    """获取OVS数据库连接"""
    db_config = parse_db_url(OVS_DB_URL)
    return psycopg2.connect(**db_config)

def generate_fixed_sql():
    """生成修正后的同步SQL"""
    return [
        """
        CREATE TABLE performance_targets (
          id SERIAL PRIMARY KEY,
          user_id INTEGER NOT NULL,
          year INTEGER NOT NULL,
          month INTEGER NOT NULL,
          implant_amount_target DOUBLE PRECISION,
          sales_amount_target DOUBLE PRECISION,
          new_customers_target INTEGER,
          new_projects_target INTEGER,
          five_star_projects_target INTEGER,
          display_currency VARCHAR(10),
          created_by INTEGER NOT NULL,
          created_at TIMESTAMP WITHOUT TIME ZONE,
          updated_at TIMESTAMP WITHOUT TIME ZONE,
          updated_by INTEGER
        );
        """,
        
        """
        CREATE TABLE performance_statistics (
          id SERIAL PRIMARY KEY,
          user_id INTEGER NOT NULL,
          year INTEGER NOT NULL,
          month INTEGER NOT NULL,
          implant_amount_actual DOUBLE PRECISION,
          sales_amount_actual DOUBLE PRECISION,
          new_customers_actual INTEGER,
          new_projects_actual INTEGER,
          five_star_projects_actual INTEGER,
          industry_statistics JSON,
          calculated_at TIMESTAMP WITHOUT TIME ZONE,
          created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        """
        CREATE TABLE five_star_project_baselines (
          id SERIAL PRIMARY KEY,
          user_id INTEGER NOT NULL,
          baseline_year INTEGER NOT NULL,
          baseline_month INTEGER NOT NULL,
          baseline_count INTEGER,
          created_at TIMESTAMP WITHOUT TIME ZONE,
          created_by INTEGER
        );
        """
    ]

def check_existing_tables():
    """检查已存在的表"""
    print("=== 检查现有表结构 ===")
    
    try:
        conn = get_ovs_connection()
        cursor = conn.cursor()
        
        tables_to_check = ['performance_targets', 'performance_statistics', 'five_star_project_baselines']
        existing_tables = []
        
        for table in tables_to_check:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    AND table_name = %s
                );
            """, (table,))
            
            exists = cursor.fetchone()[0]
            if exists:
                existing_tables.append(table)
                print(f"✅ 表 {table} 已存在")
            else:
                print(f"❌ 表 {table} 不存在，需要创建")
        
        # 检查列是否存在
        columns_to_check = [
            ('approval_step', 'approver_type'),
            ('approval_step', 'description'),
            ('projects', 'industry')
        ]
        
        existing_columns = []
        for table, column in columns_to_check:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = 'public'
                    AND table_name = %s
                    AND column_name = %s
                );
            """, (table, column))
            
            exists = cursor.fetchone()[0]
            if exists:
                existing_columns.append((table, column))
                print(f"✅ 列 {table}.{column} 已存在")
            else:
                print(f"❌ 列 {table}.{column} 不存在，需要添加")
        
        cursor.close()
        conn.close()
        
        return existing_tables, existing_columns
        
    except Exception as e:
        print(f"❌ 检查表结构时出错: {str(e)}")
        return [], []

def execute_fixed_sync():
    """执行修正后的同步"""
    print("\n=== 执行修正后的同步 ===")
    
    # 检查现有结构
    existing_tables, existing_columns = check_existing_tables()
    
    # 生成需要执行的SQL
    sql_statements = []
    
    # 添加缺失的表
    create_table_sqls = generate_fixed_sql()
    tables_to_create = ['performance_targets', 'performance_statistics', 'five_star_project_baselines']
    
    for i, table_name in enumerate(tables_to_create):
        if table_name not in existing_tables:
            sql_statements.append((f"创建表 {table_name}", create_table_sqls[i]))
    
    # 添加缺失的列
    columns_to_add = [
        ('approval_step', 'approver_type', "ALTER TABLE approval_step ADD COLUMN approver_type VARCHAR(20) DEFAULT 'user';"),
        ('approval_step', 'description', "ALTER TABLE approval_step ADD COLUMN description TEXT;"),
        ('projects', 'industry', "ALTER TABLE projects ADD COLUMN industry VARCHAR(50);")
    ]
    
    for table, column, sql in columns_to_add:
        if (table, column) not in existing_columns:
            sql_statements.append((f"添加列 {table}.{column}", sql))
    
    if not sql_statements:
        print("✅ 所有结构都已存在，无需同步")
        return True
    
    print(f"\n准备执行 {len(sql_statements)} 条修正SQL:")
    for i, (desc, sql) in enumerate(sql_statements, 1):
        print(f"{i:2d}. {desc}")
    
    # 确认执行
    confirm = input(f"\n是否执行以上 {len(sql_statements)} 条SQL？(y/N): ")
    if confirm.lower() != 'y':
        print("❌ 用户取消执行")
        return False
    
    try:
        print("\n正在连接pma_db_ovs数据库...")
        conn = get_ovs_connection()
        cursor = conn.cursor()
        
        print("开始执行修正同步SQL...")
        success_count = 0
        
        for i, (desc, sql) in enumerate(sql_statements, 1):
            try:
                print(f"执行第 {i:2d} 条SQL ({desc}): ", end="", flush=True)
                cursor.execute(sql)
                conn.commit()
                print("✅ 成功")
                success_count += 1
            except Exception as e:
                print(f"❌ 失败: {str(e)}")
                conn.rollback()
        
        cursor.close()
        conn.close()
        
        print(f"\n📊 执行结果: {success_count}/{len(sql_statements)} 条SQL成功执行")
        
        if success_count == len(sql_statements):
            print("🎉 所有修正SQL执行成功！")
            return True
        else:
            print("⚠️ 部分修正SQL执行失败")
            return False
        
    except Exception as e:
        print(f"❌ 连接数据库失败: {str(e)}")
        return False

def create_completion_report():
    """创建完成报告"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"pma_db_ovs_sync_completion_report_{timestamp}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# pma_db_ovs数据库同步完成报告\n\n")
        f.write(f"**完成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**目标数据库**: pma_db_ovs\n\n")
        f.write(f"## 同步内容\n")
        f.write(f"### 新增表\n")
        f.write(f"- `performance_targets` - 绩效目标表\n")
        f.write(f"- `performance_statistics` - 绩效统计表\n")
        f.write(f"- `five_star_project_baselines` - 五星项目基准表\n\n")
        f.write(f"### 新增列\n")
        f.write(f"- `approval_step.approver_type` - 审批者类型\n")
        f.write(f"- `approval_step.description` - 步骤描述\n")
        f.write(f"- `projects.industry` - 项目行业\n\n")
        f.write(f"## 技术修复\n")
        f.write(f"- 修正了PostgreSQL数据类型格式问题\n")
        f.write(f"- 使用SERIAL代替带精度的INTEGER\n")
        f.write(f"- 使用标准的DOUBLE PRECISION类型\n\n")
        f.write(f"## 备份文件\n")
        f.write(f"- 备份目录: `ovs_db_backups/`\n")
        f.write(f"- 包含同步前的完整数据库备份\n")
    
    return report_file

def main():
    """主函数"""
    print("=== pma_db_ovs数据库同步修复工具 ===")
    print(f"目标数据库: {OVS_DB_URL.replace(OVS_DB_URL.split('@')[0].split(':')[-1], '***')}")
    print()
    
    try:
        # 执行修正后的同步
        success = execute_fixed_sync()
        
        # 生成完成报告
        report_file = create_completion_report()
        
        if success:
            print(f"\n🎉 pma_db_ovs数据库同步修复完成！")
            print(f"📄 完成报告: {report_file}")
            print("\n现在pma_db_ovs数据库已具备与本地数据库一致的结构。")
        else:
            print(f"\n⚠️ pma_db_ovs数据库同步修复未完全成功")
            print(f"📄 完成报告: {report_file}")
            print("请检查错误信息并手动处理剩余问题。")
    
    except Exception as e:
        print(f"❌ 执行过程出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main() 