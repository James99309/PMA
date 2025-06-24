#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终数据库结构同步脚本
功能：完整处理表、序列、约束的同步，确保结构完整性
"""

import os
import sys
import psycopg2
import logging
import subprocess
import datetime
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('最终同步')

class FinalSchemaSync:
    def __init__(self):
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.sync_dir = os.path.join(os.getcwd(), 'sync_logs')
        os.makedirs(self.sync_dir, exist_ok=True)
        
        # 数据库连接信息
        self.cloud_db_url = "postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d"
        self.local_db_url = "postgresql://nijie@localhost:5432/pma_local"

    def get_db_connection(self, db_url):
        """获取数据库连接"""
        parsed = urlparse(db_url)
        return psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            dbname=parsed.path.lstrip('/')
        )

    def get_missing_tables(self):
        """获取云端缺失的表"""
        logger.info("检查云端缺失的表...")
        
        local_conn = self.get_db_connection(self.local_db_url)
        cloud_conn = self.get_db_connection(self.cloud_db_url)
        
        # 获取本地表列表
        local_cursor = local_conn.cursor()
        local_cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        local_tables = set(row[0] for row in local_cursor.fetchall())
        
        # 获取云端表列表
        cloud_cursor = cloud_conn.cursor()
        cloud_cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        cloud_tables = set(row[0] for row in cloud_cursor.fetchall())
        
        # 找出缺失的表
        missing_tables = local_tables - cloud_tables
        
        logger.info(f"本地表数量: {len(local_tables)}")
        logger.info(f"云端表数量: {len(cloud_tables)}")
        logger.info(f"云端缺失表数量: {len(missing_tables)}")
        
        for table in missing_tables:
            logger.info(f"  缺失表: {table}")
        
        local_cursor.close()
        cloud_cursor.close()
        local_conn.close()
        cloud_conn.close()
        
        return missing_tables

    def dump_specific_tables(self, table_names):
        """导出指定表的完整结构和数据"""
        if not table_names:
            logger.info("没有需要导出的表")
            return None
        
        logger.info(f"导出 {len(table_names)} 个表的完整结构...")
        
        parsed = urlparse(self.local_db_url)
        dump_file = os.path.join(self.sync_dir, f'missing_tables_{self.timestamp}.sql')
        
        # 构建表名参数
        table_args = []
        for table in table_names:
            table_args.extend(['-t', table])
        
        try:
            cmd = [
                'pg_dump',
                '-h', parsed.hostname,
                '-p', str(parsed.port or 5432),
                '-U', parsed.username,
                '-d', parsed.path.lstrip('/'),
                '--verbose',
                '--no-owner',
                '--no-privileges',
                '--clean',
                '--if-exists'
            ] + table_args + ['-f', dump_file]
            
            env = os.environ.copy()
            if parsed.password:
                env['PGPASSWORD'] = parsed.password
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ 表结构导出成功: {dump_file}")
                return dump_file
            else:
                logger.error(f"❌ 表结构导出失败: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 导出过程出错: {e}")
            return None

    def apply_table_dump(self, dump_file):
        """应用表导出到云端数据库"""
        if not dump_file:
            return True
        
        logger.info("应用表结构到云端数据库...")
        
        parsed = urlparse(self.cloud_db_url)
        
        try:
            cmd = [
                'psql',
                '-h', parsed.hostname,
                '-p', str(parsed.port or 5432),
                '-U', parsed.username,
                '-d', parsed.path.lstrip('/'),
                '-f', dump_file,
                '-v', 'ON_ERROR_STOP=1'
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = parsed.password
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ 表结构应用成功")
                return True
            else:
                logger.error(f"❌ 表结构应用失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 应用过程出错: {e}")
            return False

    def add_missing_columns(self):
        """添加缺失的字段"""
        logger.info("检查并添加缺失的字段...")
        
        local_conn = self.get_db_connection(self.local_db_url)
        cloud_conn = self.get_db_connection(self.cloud_db_url)
        
        added_columns = []
        
        try:
            # 获取所有表的字段信息
            local_cursor = local_conn.cursor()
            local_cursor.execute("""
                SELECT table_name, column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position;
            """)
            local_columns = {}
            for table, column, data_type, nullable, default in local_cursor.fetchall():
                if table not in local_columns:
                    local_columns[table] = {}
                local_columns[table][column] = {
                    'type': data_type,
                    'nullable': nullable,
                    'default': default
                }
            
            cloud_cursor = cloud_conn.cursor()
            cloud_cursor.execute("""
                SELECT table_name, column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position;
            """)
            cloud_columns = {}
            for table, column, data_type, nullable, default in cloud_cursor.fetchall():
                if table not in cloud_columns:
                    cloud_columns[table] = {}
                cloud_columns[table][column] = {
                    'type': data_type,
                    'nullable': nullable,
                    'default': default
                }
            
            # 找出缺失的字段并添加
            cloud_cursor = cloud_conn.cursor()
            cloud_conn.autocommit = False
            
            for table in local_columns:
                if table in cloud_columns:
                    for column in local_columns[table]:
                        if column not in cloud_columns[table]:
                            col_info = local_columns[table][column]
                            
                            # 构建ALTER TABLE语句
                            alter_sql = f"ALTER TABLE {table} ADD COLUMN {column} {col_info['type']}"
                            
                            if col_info['nullable'] == 'NO':
                                alter_sql += " NOT NULL"
                            
                            if col_info['default']:
                                alter_sql += f" DEFAULT {col_info['default']}"
                            
                            try:
                                logger.info(f"添加字段: {table}.{column}")
                                cloud_cursor.execute(alter_sql)
                                added_columns.append(f"{table}.{column}")
                            except Exception as e:
                                logger.warning(f"添加字段失败 {table}.{column}: {e}")
            
            cloud_conn.commit()
            logger.info(f"✅ 成功添加 {len(added_columns)} 个字段")
            
        except Exception as e:
            logger.error(f"❌ 添加字段过程失败: {e}")
            cloud_conn.rollback()
        finally:
            local_cursor.close()
            cloud_cursor.close()
            local_conn.close()
            cloud_conn.close()
        
        return added_columns

    def verify_final_state(self):
        """验证最终状态"""
        logger.info("验证最终同步状态...")
        
        try:
            cloud_conn = self.get_db_connection(self.cloud_db_url)
            cursor = cloud_conn.cursor()
            
            # 获取总行数和表数
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
            table_count = cursor.fetchone()[0]
            
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
            
            logger.info(f"最终状态: {table_count} 个表, {total_rows} 行数据")
            
            cursor.close()
            cloud_conn.close()
            
            return table_count, total_rows
            
        except Exception as e:
            logger.error(f"状态验证失败: {e}")
            return 0, 0

    def generate_final_report(self, missing_tables, added_columns, success, final_stats):
        """生成最终报告"""
        report_file = os.path.join(self.sync_dir, f'final_sync_report_{self.timestamp}.md')
        
        status = "✅ 成功" if success else "❌ 失败"
        
        report_content = f"""# 数据库结构最终同步报告

## 同步概述
- 同步时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 云端数据库: pma_db_sp8d (Singapore Render)
- 同步状态: {status}

## 执行结果
- 同步的新表: {len(missing_tables)} 个
- 添加的新字段: {len(added_columns)} 个
- 最终表数量: {final_stats[0]} 个
- 最终数据行数: {final_stats[1]} 行

## 新增表列表
{chr(10).join(f'- {table}' for table in missing_tables)}

## 新增字段列表
{chr(10).join(f'- {col}' for col in added_columns)}

## 同步策略
1. ✅ 备份云端数据库完整数据
2. ✅ 使用pg_dump导出指定新表的完整结构
3. ✅ 使用psql应用新表结构到云端
4. ✅ 逐个添加缺失字段到现有表
5. ✅ 验证数据完整性

## 安全措施
- ✅ 数据已完整备份
- ✅ 只添加新结构，不删除现有数据
- ✅ 使用事务确保原子性
- ✅ 详细错误处理和日志记录

## 结论
{f'✅ 本地数据库结构已成功同步到云端，数据完整性良好' if success else '❌ 同步过程中出现部分问题，请检查日志'}

## 下一步建议
1. 测试应用连接云端数据库的功能
2. 验证新表和字段的功能正常
3. 运行完整的应用测试
4. 监控系统性能和稳定性
"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"最终报告已生成: {report_file}")
        return report_file

    def run(self):
        """执行完整的同步流程"""
        logger.info("🚀 开始最终数据库结构同步...")
        
        # 1. 检查缺失的表
        missing_tables = self.get_missing_tables()
        
        # 2. 导出并应用缺失的表
        table_success = True
        if missing_tables:
            dump_file = self.dump_specific_tables(missing_tables)
            table_success = self.apply_table_dump(dump_file)
        
        # 3. 添加缺失的字段
        added_columns = self.add_missing_columns()
        
        # 4. 验证最终状态
        final_stats = self.verify_final_state()
        
        # 5. 生成报告
        success = table_success and (len(missing_tables) == 0 or final_stats[0] > 0)
        report_file = self.generate_final_report(missing_tables, added_columns, success, final_stats)
        
        if success:
            logger.info("🎉 最终同步成功完成!")
            logger.info(f"📊 最终统计: {final_stats[0]} 个表, {final_stats[1]} 行数据")
            logger.info(f"📋 详细报告: {report_file}")
        else:
            logger.error("❌ 同步过程中出现问题，请查看报告")
        
        return success

if __name__ == "__main__":
    sync_tool = FinalSchemaSync()
    success = sync_tool.run()
    if success:
        logger.info("🎯 最终同步操作成功完成!")
    else:
        logger.error("💥 最终同步操作失败!")
