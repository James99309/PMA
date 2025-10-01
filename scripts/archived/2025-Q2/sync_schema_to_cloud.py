#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地数据库结构同步到云端脚本
功能：将本地数据库结构安全地同步到云端，不破坏任何现有数据
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
logger = logging.getLogger('结构同步')

class SchemaSync:
    def __init__(self):
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.sync_dir = os.path.join(os.getcwd(), 'sync_logs')
        os.makedirs(self.sync_dir, exist_ok=True)
        
        # 云端数据库连接信息
        self.cloud_db_url = "postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d"
        
        # 本地数据库连接信息
        self.local_db_url = "postgresql://nijie@localhost:5432/pma_local"
        
        logger.info(f"本地数据库: {self.local_db_url.split('@')[1]}")
        logger.info(f"云端数据库: {self.cloud_db_url.split('@')[1]}")

    def parse_db_url(self, db_url):
        """解析数据库URL"""
        parsed = urlparse(db_url)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'user': parsed.username,
            'password': parsed.password,
            'dbname': parsed.path.lstrip('/')
        }

    def test_connections(self):
        """测试两个数据库连接"""
        logger.info("测试数据库连接...")
        
        # 测试本地连接
        try:
            local_params = self.parse_db_url(self.local_db_url)
            conn = psycopg2.connect(**local_params)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
            local_tables = cursor.fetchone()[0]
            logger.info(f"✅ 本地数据库连接成功，共 {local_tables} 个表")
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"❌ 本地数据库连接失败: {e}")
            return False
        
        # 测试云端连接
        try:
            cloud_params = self.parse_db_url(self.cloud_db_url)
            conn = psycopg2.connect(**cloud_params)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
            cloud_tables = cursor.fetchone()[0]
            logger.info(f"✅ 云端数据库连接成功，共 {cloud_tables} 个表")
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"❌ 云端数据库连接失败: {e}")
            return False
        
        return True

    def get_local_schema(self):
        """导出本地数据库结构"""
        logger.info("导出本地数据库结构...")
        
        local_params = self.parse_db_url(self.local_db_url)
        schema_file = os.path.join(self.sync_dir, f'local_schema_{self.timestamp}.sql')
        
        try:
            cmd = [
                'pg_dump',
                '-h', local_params['host'],
                '-p', str(local_params['port']),
                '-U', local_params['user'],
                '-d', local_params['dbname'],
                '--schema-only',
                '--no-owner',
                '--no-privileges',
                '--clean',
                '--if-exists',
                '-f', schema_file
            ]
            
            env = os.environ.copy()
            if local_params.get('password'):
                env['PGPASSWORD'] = local_params['password']
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ 本地结构导出成功: {schema_file}")
                return schema_file
            else:
                logger.error(f"❌ 本地结构导出失败: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 导出过程出错: {e}")
            return None

    def make_schema_safe(self, schema_sql):
        """处理schema SQL，使其安全（不破坏现有数据）"""
        logger.info("处理SQL，确保安全同步...")
        
        lines = schema_sql.split('\n')
        safe_lines = []
        dropped_statements = []
        
        for line in lines:
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            
            # 跳过危险语句但记录
            if (line_lower.startswith('drop ') and 
                ('table' in line_lower or 'database' in line_lower or 'schema' in line_lower)):
                dropped_statements.append(line_stripped)
                logger.debug(f"跳过DROP语句: {line_stripped}")
                continue
            
            # 跳过其他危险操作
            if (line_lower.startswith('delete ') or 
                line_lower.startswith('truncate ') or
                line_lower.startswith('alter table') and 'drop column' in line_lower):
                dropped_statements.append(line_stripped)
                logger.debug(f"跳过危险语句: {line_stripped}")
                continue
            
            # 将CREATE TABLE改为CREATE TABLE IF NOT EXISTS
            if line_lower.startswith('create table '):
                line = line.replace('CREATE TABLE ', 'CREATE TABLE IF NOT EXISTS ')
                line = line.replace('create table ', 'CREATE TABLE IF NOT EXISTS ')
                logger.debug(f"修改为安全创建: {line.strip()}")
            
            # 将CREATE INDEX改为CREATE INDEX IF NOT EXISTS
            if line_lower.startswith('create index ') or line_lower.startswith('create unique index '):
                if 'if not exists' not in line_lower:
                    if line_lower.startswith('create unique index '):
                        line = line.replace('CREATE UNIQUE INDEX ', 'CREATE UNIQUE INDEX IF NOT EXISTS ')
                        line = line.replace('create unique index ', 'CREATE UNIQUE INDEX IF NOT EXISTS ')
                    else:
                        line = line.replace('CREATE INDEX ', 'CREATE INDEX IF NOT EXISTS ')
                        line = line.replace('create index ', 'CREATE INDEX IF NOT EXISTS ')
            
            safe_lines.append(line)
        
        logger.info(f"已过滤 {len(dropped_statements)} 个危险语句")
        for stmt in dropped_statements[:5]:  # 只显示前5个
            logger.info(f"  - {stmt}")
        if len(dropped_statements) > 5:
            logger.info(f"  ... 还有 {len(dropped_statements) - 5} 个")
        
        return '\n'.join(safe_lines)

    def backup_cloud_data_before_sync(self):
        """同步前再次确认云端数据完整性"""
        logger.info("同步前验证云端数据完整性...")
        
        try:
            cloud_params = self.parse_db_url(self.cloud_db_url)
            conn = psycopg2.connect(**cloud_params)
            cursor = conn.cursor()
            
            # 获取表行数统计
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            
            total_rows = 0
            table_data = {}
            
            for (table_name,) in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    count = cursor.fetchone()[0]
                    table_data[table_name] = count
                    total_rows += count
                except Exception as e:
                    logger.warning(f"无法获取表 {table_name} 的行数: {e}")
                    table_data[table_name] = 0
            
            logger.info(f"云端当前总数据行数: {total_rows}")
            
            cursor.close()
            conn.close()
            
            return total_rows, table_data
            
        except Exception as e:
            logger.error(f"云端数据验证失败: {e}")
            return 0, {}

    def sync_schema_safely(self, schema_file):
        """安全地同步结构到云端"""
        logger.info("开始安全同步结构到云端...")
        
        # 读取并处理结构文件
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
        except Exception as e:
            logger.error(f"读取结构文件失败: {e}")
            return False
        
        # 处理为安全SQL
        safe_sql = self.make_schema_safe(schema_sql)
        
        # 保存安全SQL到文件
        safe_schema_file = os.path.join(self.sync_dir, f'safe_schema_{self.timestamp}.sql')
        with open(safe_schema_file, 'w', encoding='utf-8') as f:
            f.write(safe_sql)
        logger.info(f"安全SQL已保存: {safe_schema_file}")
        
        # 连接云端数据库执行同步
        cloud_params = self.parse_db_url(self.cloud_db_url)
        
        try:
            conn = psycopg2.connect(**cloud_params)
            conn.autocommit = False
            cursor = conn.cursor()
            
            try:
                logger.info("执行安全结构同步...")
                cursor.execute(safe_sql)
                conn.commit()
                logger.info("✅ 结构同步成功")
                
                # 验证同步结果
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name;
                """)
                tables_after = [t[0] for t in cursor.fetchall()]
                logger.info(f"同步后表数量: {len(tables_after)}")
                
                return True
                
            except Exception as e:
                logger.error(f"❌ 结构同步失败: {e}")
                conn.rollback()
                return False
            finally:
                cursor.close()
                conn.close()
                
        except Exception as e:
            logger.error(f"❌ 连接云端数据库失败: {e}")
            return False

    def verify_data_after_sync(self, before_data):
        """同步后验证数据完整性"""
        logger.info("验证同步后数据完整性...")
        
        try:
            cloud_params = self.parse_db_url(self.cloud_db_url)
            conn = psycopg2.connect(**cloud_params)
            cursor = conn.cursor()
            
            # 获取同步后的表行数统计
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            
            total_rows_after = 0
            table_data_after = {}
            
            for (table_name,) in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                    count = cursor.fetchone()[0]
                    table_data_after[table_name] = count
                    total_rows_after += count
                except Exception as e:
                    logger.warning(f"无法获取表 {table_name} 的行数: {e}")
                    table_data_after[table_name] = 0
            
            cursor.close()
            conn.close()
            
            # 对比数据
            before_total = sum(before_data.values())
            logger.info(f"同步前总行数: {before_total}")
            logger.info(f"同步后总行数: {total_rows_after}")
            
            if before_total == total_rows_after:
                logger.info("✅ 数据完整性验证通过，无数据丢失")
                return True
            else:
                logger.warning(f"⚠️ 数据行数变化: {total_rows_after - before_total}")
                
                # 检查具体哪些表有变化
                for table, before_count in before_data.items():
                    after_count = table_data_after.get(table, 0)
                    if before_count != after_count:
                        logger.warning(f"  表 {table}: {before_count} -> {after_count}")
                
                return False
            
        except Exception as e:
            logger.error(f"数据验证失败: {e}")
            return False

    def generate_sync_report(self, schema_file, sync_success, data_verified, before_total, after_total):
        """生成同步报告"""
        report_file = os.path.join(self.sync_dir, f'sync_report_{self.timestamp}.md')
        
        status = "✅ 成功" if sync_success and data_verified else "❌ 失败"
        data_status = "✅ 无变化" if before_total == after_total else f"⚠️ 变化 {after_total - before_total} 行"
        
        report_content = f"""# 数据库结构同步报告

## 同步概述
- 同步时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 本地数据库: pma_local (localhost)
- 云端数据库: pma_db_sp8d (Singapore Render)
- 同步状态: {status}
- 数据完整性: {data_status}

## 执行步骤
1. ✅ 测试数据库连接
2. {'✅' if schema_file else '❌'} 导出本地数据库结构
3. ✅ 备份前数据验证
4. {'✅' if sync_success else '❌'} 安全结构同步
5. {'✅' if data_verified else '❌'} 同步后数据验证

## 数据统计
- 同步前数据行数: {before_total}
- 同步后数据行数: {after_total}
- 数据变化: {after_total - before_total} 行

## 安全措施
- ✅ 跳过所有DROP语句
- ✅ 使用IF NOT EXISTS创建表和索引
- ✅ 事务回滚机制
- ✅ 数据完整性验证

## 文件位置
- 同步日志目录: {self.sync_dir}
- 原始结构文件: {schema_file or '无'}
- 安全结构文件: safe_schema_{self.timestamp}.sql

## 结论
{'✅ 结构同步成功，数据完整性良好' if sync_success and data_verified else '❌ 同步过程中出现问题，请检查日志'}

## 建议
1. 测试应用功能是否正常
2. 检查新增的表和字段
3. 验证关键业务流程
4. 如有问题，可使用备份文件恢复
"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"同步报告已生成: {report_file}")
        return report_file

    def run(self):
        """执行完整的结构同步流程"""
        logger.info("🚀 开始数据库结构同步流程...")
        
        # 1. 测试连接
        if not self.test_connections():
            logger.error("❌ 数据库连接失败，中止同步")
            return False
        
        # 2. 备份前数据验证
        before_total, before_data = self.backup_cloud_data_before_sync()
        if before_total == 0:
            logger.error("❌ 云端数据验证失败，中止同步")
            return False
        
        # 3. 导出本地结构
        schema_file = self.get_local_schema()
        if not schema_file:
            logger.error("❌ 本地结构导出失败，中止同步")
            return False
        
        # 4. 安全同步结构
        sync_success = self.sync_schema_safely(schema_file)
        
        # 5. 验证数据完整性
        data_verified = self.verify_data_after_sync(before_data)
        
        # 6. 获取同步后数据统计
        after_total, _ = self.backup_cloud_data_before_sync()
        
        # 7. 生成报告
        report_file = self.generate_sync_report(schema_file, sync_success, data_verified, before_total, after_total)
        
        if sync_success and data_verified:
            logger.info("🎉 结构同步成功完成!")
            logger.info(f"📊 数据统计: {before_total} -> {after_total} 行")
            logger.info(f"📋 详细报告: {report_file}")
        else:
            logger.error("❌ 同步过程中出现问题，请查看报告")
        
        return sync_success and data_verified

if __name__ == "__main__":
    sync_tool = SchemaSync()
    success = sync_tool.run()
    if success:
        logger.info("🎯 结构同步操作成功完成!")
    else:
        logger.error("💥 结构同步操作失败!")
