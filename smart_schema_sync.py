#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能数据库结构同步脚本
功能：只同步新增的表、字段和索引，不破坏现有结构和数据
"""

import os
import sys
import psycopg2
import logging
import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('智能同步')

class SmartSchemaSync:
    def __init__(self):
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.sync_dir = os.path.join(os.getcwd(), 'sync_logs')
        os.makedirs(self.sync_dir, exist_ok=True)
        
        # 数据库连接信息
        self.cloud_db_url = "postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d"
        self.local_db_url = "postgresql://nijie@localhost:5432/pma_local"

    def get_db_connection(self, db_url):
        """获取数据库连接"""
        from urllib.parse import urlparse
        parsed = urlparse(db_url)
        return psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            dbname=parsed.path.lstrip('/')
        )

    def get_table_schemas(self, conn):
        """获取数据库表结构信息"""
        cursor = conn.cursor()
        
        # 获取表信息
        cursor.execute("""
            SELECT table_name, table_type
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = {row[0]: row[1] for row in cursor.fetchall()}
        
        # 获取列信息
        cursor.execute("""
            SELECT table_name, column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position;
        """)
        columns = {}
        for table, column, data_type, nullable, default in cursor.fetchall():
            if table not in columns:
                columns[table] = {}
            columns[table][column] = {
                'type': data_type,
                'nullable': nullable,
                'default': default
            }
        
        # 获取索引信息
        cursor.execute("""
            SELECT schemaname, tablename, indexname, indexdef
            FROM pg_indexes 
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname;
        """)
        indexes = {}
        for schema, table, index_name, index_def in cursor.fetchall():
            if table not in indexes:
                indexes[table] = {}
            indexes[table][index_name] = index_def
        
        cursor.close()
        return tables, columns, indexes

    def compare_schemas(self):
        """比较本地和云端数据库结构"""
        logger.info("比较本地和云端数据库结构...")
        
        # 连接数据库
        local_conn = self.get_db_connection(self.local_db_url)
        cloud_conn = self.get_db_connection(self.cloud_db_url)
        
        # 获取结构信息
        local_tables, local_columns, local_indexes = self.get_table_schemas(local_conn)
        cloud_tables, cloud_columns, cloud_indexes = self.get_table_schemas(cloud_conn)
        
        # 找出差异
        new_tables = set(local_tables.keys()) - set(cloud_tables.keys())
        new_columns = {}
        
        for table in local_columns:
            if table in cloud_columns:
                new_cols = set(local_columns[table].keys()) - set(cloud_columns[table].keys())
                if new_cols:
                    new_columns[table] = {col: local_columns[table][col] for col in new_cols}
        
        logger.info(f"发现 {len(new_tables)} 个新表")
        logger.info(f"发现 {sum(len(cols) for cols in new_columns.values())} 个新字段")
        
        for table in new_tables:
            logger.info(f"  新表: {table}")
        
        for table, cols in new_columns.items():
            for col in cols:
                logger.info(f"  新字段: {table}.{col}")
        
        local_conn.close()
        cloud_conn.close()
        
        return new_tables, new_columns

    def generate_migration_sql(self, new_tables, new_columns):
        """生成迁移SQL"""
        logger.info("生成迁移SQL...")
        
        migration_sql = []
        
        # 为新表生成CREATE TABLE语句
        if new_tables:
            local_conn = self.get_db_connection(self.local_db_url)
            cursor = local_conn.cursor()
            
            for table in new_tables:
                # 获取表的完整创建语句
                cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = '{table}'
                    ORDER BY ordinal_position;
                """)
                columns = cursor.fetchall()
                
                if columns:
                    create_sql = f"CREATE TABLE IF NOT EXISTS {table} (\n"
                    col_defs = []
                    
                    for col_name, data_type, nullable, default in columns:
                        col_def = f"    {col_name} {data_type}"
                        if nullable == 'NO':
                            col_def += " NOT NULL"
                        if default:
                            col_def += f" DEFAULT {default}"
                        col_defs.append(col_def)
                    
                    create_sql += ",\n".join(col_defs)
                    create_sql += "\n);"
                    
                    migration_sql.append(create_sql)
                    logger.info(f"生成新表SQL: {table}")
            
            cursor.close()
            local_conn.close()
        
        # 为新字段生成ALTER TABLE语句
        for table, columns in new_columns.items():
            for col_name, col_info in columns.items():
                alter_sql = f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col_name} {col_info['type']}"
                if col_info['nullable'] == 'NO':
                    alter_sql += " NOT NULL"
                if col_info['default']:
                    alter_sql += f" DEFAULT {col_info['default']}"
                alter_sql += ";"
                
                migration_sql.append(alter_sql)
                logger.info(f"生成新字段SQL: {table}.{col_name}")
        
        return migration_sql

    def apply_migration(self, migration_sql):
        """应用迁移SQL"""
        if not migration_sql:
            logger.info("没有需要迁移的结构，跳过")
            return True
        
        logger.info(f"应用 {len(migration_sql)} 个迁移语句...")
        
        cloud_conn = self.get_db_connection(self.cloud_db_url)
        cloud_conn.autocommit = False
        cursor = cloud_conn.cursor()
        
        try:
            for i, sql in enumerate(migration_sql, 1):
                logger.info(f"执行 ({i}/{len(migration_sql)}): {sql[:50]}...")
                cursor.execute(sql)
            
            cloud_conn.commit()
            logger.info("✅ 所有迁移语句执行成功")
            
            cursor.close()
            cloud_conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ 迁移失败: {e}")
            cloud_conn.rollback()
            cursor.close()
            cloud_conn.close()
            return False

    def verify_migration(self):
        """验证迁移结果"""
        logger.info("验证迁移结果...")
        
        try:
            cloud_conn = self.get_db_connection(self.cloud_db_url)
            cursor = cloud_conn.cursor()
            
            # 获取总行数
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            
            total_rows = 0
            for (table_name,) in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    count = cursor.fetchone()[0]
                    total_rows += count
                except:
                    pass
            
            # 获取表数量
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
            table_count = cursor.fetchone()[0]
            
            logger.info(f"迁移后统计: {table_count} 个表, {total_rows} 行数据")
            
            cursor.close()
            cloud_conn.close()
            
            return total_rows, table_count
            
        except Exception as e:
            logger.error(f"验证失败: {e}")
            return 0, 0

    def save_migration_log(self, migration_sql, success, before_stats, after_stats):
        """保存迁移日志"""
        log_file = os.path.join(self.sync_dir, f'migration_log_{self.timestamp}.md')
        
        status = "✅ 成功" if success else "❌ 失败"
        
        log_content = f"""# 数据库智能迁移日志

## 迁移概述
- 迁移时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 迁移状态: {status}
- 迁移语句数量: {len(migration_sql)}

## 数据统计
- 迁移前: {before_stats[1]} 个表, {before_stats[0]} 行数据
- 迁移后: {after_stats[1]} 个表, {after_stats[0]} 行数据
- 新增表: {after_stats[1] - before_stats[1]} 个
- 数据变化: {after_stats[0] - before_stats[0]} 行

## 执行的SQL语句
```sql
{chr(10).join(migration_sql)}
```

## 结论
{f'✅ 迁移成功完成，所有新结构已同步到云端' if success else '❌ 迁移失败，请检查错误日志'}
"""
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(log_content)
        
        logger.info(f"迁移日志已保存: {log_file}")
        return log_file

    def run(self):
        """执行智能迁移"""
        logger.info("🚀 开始智能数据库结构同步...")
        
        # 获取迁移前统计
        before_rows, before_tables = self.verify_migration()
        
        # 比较结构差异
        new_tables, new_columns = self.compare_schemas()
        
        if not new_tables and not new_columns:
            logger.info("✅ 数据库结构已是最新，无需同步")
            return True
        
        # 生成迁移SQL
        migration_sql = self.generate_migration_sql(new_tables, new_columns)
        
        if not migration_sql:
            logger.info("✅ 无需要应用的迁移")
            return True
        
        # 应用迁移
        success = self.apply_migration(migration_sql)
        
        # 获取迁移后统计
        after_rows, after_tables = self.verify_migration()
        
        # 保存日志
        log_file = self.save_migration_log(migration_sql, success, 
                                         (before_rows, before_tables), 
                                         (after_rows, after_tables))
        
        if success:
            logger.info("🎉 智能迁移成功完成!")
            logger.info(f"📊 统计: 表 {before_tables} -> {after_tables}, 数据 {before_rows} -> {after_rows}")
            logger.info(f"📋 详细日志: {log_file}")
        else:
            logger.error("❌ 迁移失败，请查看日志")
        
        return success

if __name__ == "__main__":
    sync_tool = SmartSchemaSync()
    success = sync_tool.run()
    if success:
        logger.info("🎯 智能同步操作成功完成!")
    else:
        logger.error("💥 智能同步操作失败!")
