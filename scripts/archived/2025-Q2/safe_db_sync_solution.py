#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全数据库同步解决方案

该脚本提供安全的数据库同步功能，特别关注约束问题的预防和处理：
1. 预检查约束冲突
2. 分步骤安全迁移
3. 回滚机制
4. 详细的风险评估

用法:
python3 safe_db_sync_solution.py [选项]

选项:
--check-constraints: 检查约束冲突风险
--safe-sync: 执行安全同步
--dry-run: 预览模式，不执行实际操作
--backup-first: 先备份再同步
--fix-constraints: 修复约束问题
"""

import os
import sys
import logging
import argparse
import json
import datetime
import subprocess
from pathlib import Path
from sqlalchemy import create_engine, inspect, text, MetaData

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('safe_db_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('安全数据库同步')

class SafeDatabaseSync:
    def __init__(self):
        self.local_db_url = os.environ.get('DATABASE_URL', 'postgresql://nijie@localhost:5432/pma_local')
        self.render_db_url = os.environ.get('RENDER_DATABASE_URL')
        
        # 确保URL格式正确
        if self.render_db_url and self.render_db_url.startswith('postgres://'):
            self.render_db_url = self.render_db_url.replace('postgres://', 'postgresql://', 1)
        
        self.local_engine = None
        self.render_engine = None
        
        # 风险评估结果
        self.risk_assessment = {
            'high_risk': [],
            'medium_risk': [],
            'low_risk': [],
            'safe': []
        }
    
    def connect_databases(self):
        """连接到本地和云端数据库"""
        try:
            logger.info("连接本地数据库...")
            self.local_engine = create_engine(self.local_db_url)
            
            if not self.render_db_url:
                logger.error("未设置RENDER_DATABASE_URL环境变量")
                logger.info("请设置云端数据库URL:")
                logger.info("export RENDER_DATABASE_URL='你的云端数据库URL'")
                return False
            
            logger.info("连接云端数据库...")
            self.render_engine = create_engine(self.render_db_url)
            
            # 测试连接
            with self.local_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✓ 本地数据库连接成功")
            
            with self.render_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✓ 云端数据库连接成功")
            
            return True
            
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            return False
    
    def check_constraint_risks(self):
        """检查约束冲突风险"""
        if not self.connect_databases():
            return False
        
        logger.info("开始约束风险评估...")
        
        # 获取数据库结构
        local_inspector = inspect(self.local_engine)
        render_inspector = inspect(self.render_engine)
        
        local_tables = local_inspector.get_table_names()
        render_tables = render_inspector.get_table_names()
        
        # 检查每个表的约束风险
        for table_name in local_tables:
            if table_name not in render_tables:
                self.risk_assessment['medium_risk'].append({
                    'type': 'missing_table',
                    'table': table_name,
                    'risk': '需要创建整个表结构',
                    'solution': '使用CREATE TABLE语句'
                })
                continue
            
            # 检查列差异
            local_columns = {col['name']: col for col in local_inspector.get_columns(table_name)}
            render_columns = {col['name']: col for col in render_inspector.get_columns(table_name)}
            
            # 检查新增列的风险
            for col_name, col_info in local_columns.items():
                if col_name not in render_columns:
                    risk_level = self._assess_column_add_risk(table_name, col_name, col_info)
                    self.risk_assessment[risk_level].append({
                        'type': 'missing_column',
                        'table': table_name,
                        'column': col_name,
                        'info': col_info,
                        'risk': self._get_column_risk_description(col_info),
                        'solution': self._get_column_add_solution(table_name, col_name, col_info)
                    })
            
            # 检查主键约束
            local_pk = local_inspector.get_pk_constraint(table_name)
            render_pk = render_inspector.get_pk_constraint(table_name)
            
            if local_pk != render_pk:
                self.risk_assessment['high_risk'].append({
                    'type': 'primary_key_diff',
                    'table': table_name,
                    'local': local_pk,
                    'render': render_pk,
                    'risk': '主键约束差异可能导致数据一致性问题',
                    'solution': '需要手动处理主键冲突'
                })
            
            # 检查外键约束
            local_fks = local_inspector.get_foreign_keys(table_name)
            render_fks = render_inspector.get_foreign_keys(table_name)
            
            if len(local_fks) != len(render_fks):
                self.risk_assessment['medium_risk'].append({
                    'type': 'foreign_key_diff',
                    'table': table_name,
                    'risk': '外键约束数量不匹配',
                    'solution': '逐个检查外键约束'
                })
        
        # 显示风险评估结果
        self._display_risk_assessment()
        
        return True
    
    def _assess_column_add_risk(self, table_name, col_name, col_info):
        """评估添加列的风险级别"""
        # 检查是否有数据
        try:
            with self.render_engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = result.fetchone()[0]
            
            # 如果表为空，风险较低
            if row_count == 0:
                return 'low_risk'
            
            # 如果是NOT NULL且没有默认值，风险较高
            if not col_info['nullable'] and col_info['default'] is None:
                return 'high_risk'
            
            # 如果有默认值或允许NULL，风险中等
            return 'medium_risk'
            
        except Exception:
            return 'medium_risk'
    
    def _get_column_risk_description(self, col_info):
        """获取列风险描述"""
        if not col_info['nullable'] and col_info['default'] is None:
            return 'NOT NULL列且无默认值，可能导致现有数据约束失败'
        elif col_info['default']:
            return '有默认值，相对安全'
        else:
            return '允许NULL，风险较低'
    
    def _get_column_add_solution(self, table_name, col_name, col_info):
        """获取添加列的解决方案"""
        col_type = col_info['type']
        
        if not col_info['nullable'] and col_info['default'] is None:
            # 需要先添加为NULL，然后设置默认值，最后设为NOT NULL
            return f"""
            -- 分步骤安全添加
            ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type} NULL;
            UPDATE {table_name} SET {col_name} = '适当的默认值' WHERE {col_name} IS NULL;
            ALTER TABLE {table_name} ALTER COLUMN {col_name} SET NOT NULL;
            """
        else:
            nullable = "NULL" if col_info['nullable'] else "NOT NULL"
            default = f"DEFAULT {col_info['default']}" if col_info['default'] else ""
            return f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {col_name} {col_type} {nullable} {default};"
    
    def _display_risk_assessment(self):
        """显示风险评估结果"""
        logger.info("=== 约束风险评估结果 ===")
        
        total_issues = (len(self.risk_assessment['high_risk']) + 
                       len(self.risk_assessment['medium_risk']) + 
                       len(self.risk_assessment['low_risk']))
        
        if total_issues == 0:
            logger.info("✅ 未发现约束风险，可以安全同步")
            return
        
        logger.warning(f"⚠️ 发现 {total_issues} 个潜在风险")
        
        # 高风险
        if self.risk_assessment['high_risk']:
            logger.error(f"🔴 高风险项目 ({len(self.risk_assessment['high_risk'])}个):")
            for item in self.risk_assessment['high_risk']:
                logger.error(f"  - {item['type']}: {item.get('table', '')} - {item['risk']}")
        
        # 中等风险
        if self.risk_assessment['medium_risk']:
            logger.warning(f"🟡 中等风险项目 ({len(self.risk_assessment['medium_risk'])}个):")
            for item in self.risk_assessment['medium_risk']:
                logger.warning(f"  - {item['type']}: {item.get('table', '')} - {item['risk']}")
        
        # 低风险
        if self.risk_assessment['low_risk']:
            logger.info(f"🟢 低风险项目 ({len(self.risk_assessment['low_risk'])}个):")
            for item in self.risk_assessment['low_risk']:
                logger.info(f"  - {item['type']}: {item.get('table', '')} - {item['risk']}")
    
    def generate_safe_migration_sql(self):
        """生成安全的迁移SQL"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 高风险操作单独文件
        high_risk_file = f"high_risk_migration_{timestamp}.sql"
        medium_risk_file = f"medium_risk_migration_{timestamp}.sql"
        low_risk_file = f"low_risk_migration_{timestamp}.sql"
        
        # 生成高风险SQL
        if self.risk_assessment['high_risk']:
            with open(high_risk_file, 'w', encoding='utf-8') as f:
                f.write("-- 高风险数据库迁移 - 请手动检查和执行\n")
                f.write(f"-- 生成时间: {datetime.datetime.now()}\n\n")
                f.write("-- ⚠️ 警告：以下操作有数据风险，请在测试环境验证后再执行\n\n")
                
                for item in self.risk_assessment['high_risk']:
                    f.write(f"-- {item['type']}: {item.get('table', '')}\n")
                    f.write(f"-- 风险: {item['risk']}\n")
                    f.write(f"-- 解决方案:\n")
                    f.write(f"{item['solution']}\n\n")
        
        # 生成中等风险SQL
        if self.risk_assessment['medium_risk']:
            with open(medium_risk_file, 'w', encoding='utf-8') as f:
                f.write("-- 中等风险数据库迁移\n")
                f.write(f"-- 生成时间: {datetime.datetime.now()}\n\n")
                f.write("BEGIN;\n\n")
                
                for item in self.risk_assessment['medium_risk']:
                    if item['type'] == 'missing_column':
                        f.write(f"-- 添加列: {item['table']}.{item['column']}\n")
                        f.write(f"{item['solution']}\n\n")
                
                f.write("COMMIT;\n")
        
        # 生成低风险SQL
        if self.risk_assessment['low_risk']:
            with open(low_risk_file, 'w', encoding='utf-8') as f:
                f.write("-- 低风险数据库迁移 - 可以安全执行\n")
                f.write(f"-- 生成时间: {datetime.datetime.now()}\n\n")
                f.write("BEGIN;\n\n")
                
                for item in self.risk_assessment['low_risk']:
                    if item['type'] == 'missing_column':
                        f.write(f"-- 添加列: {item['table']}.{item['column']}\n")
                        f.write(f"{item['solution']}\n\n")
                
                f.write("COMMIT;\n")
        
        logger.info("安全迁移SQL文件已生成:")
        if self.risk_assessment['high_risk']:
            logger.error(f"  🔴 高风险: {high_risk_file}")
        if self.risk_assessment['medium_risk']:
            logger.warning(f"  🟡 中等风险: {medium_risk_file}")
        if self.risk_assessment['low_risk']:
            logger.info(f"  🟢 低风险: {low_risk_file}")
    
    def backup_render_database(self):
        """备份云端数据库"""
        if not self.render_db_url:
            logger.error("未设置云端数据库URL，无法备份")
            return False
        
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"render_backup_{timestamp}.sql"
        
        logger.info(f"备份云端数据库到: {backup_file}")
        
        try:
            # 从URL中提取连接信息
            url_parts = self.render_db_url.replace('postgresql://', '').split('/')
            conn_parts = url_parts[0].split('@')
            
            user_pass = conn_parts[0].split(':')
            host_port = conn_parts[1].split(':')
            
            username = user_pass[0]
            password = user_pass[1] if len(user_pass) > 1 else ''
            host = host_port[0]
            port = host_port[1] if len(host_port) > 1 else '5432'
            dbname = url_parts[1].split('?')[0]
            
            # 设置环境变量
            env = os.environ.copy()
            env['PGPASSWORD'] = password
            
            # 执行pg_dump
            cmd = [
                'pg_dump',
                '-h', host,
                '-p', port,
                '-U', username,
                '-d', dbname,
                '--verbose',
                '--clean',
                '--if-exists',
                '-f', backup_file
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ 云端数据库备份成功: {backup_file}")
                return backup_file
            else:
                logger.error(f"备份失败: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"备份过程中出错: {str(e)}")
            return None
    
    def execute_safe_sync(self, dry_run=False, backup_first=True):
        """执行安全同步"""
        if not self.connect_databases():
            return False
        
        logger.info("开始安全数据库同步...")
        
        # 1. 备份
        if backup_first:
            backup_file = self.backup_render_database()
            if not backup_file:
                logger.error("备份失败，同步中止")
                return False
        
        # 2. 风险评估
        if not self.check_constraint_risks():
            return False
        
        # 3. 检查是否有高风险操作
        if self.risk_assessment['high_risk']:
            logger.error("⚠️ 检测到高风险操作，不能自动执行")
            logger.error("请手动检查并处理高风险项目后再试")
            self.generate_safe_migration_sql()
            return False
        
        # 4. 生成迁移SQL
        self.generate_safe_migration_sql()
        
        # 5. 执行低风险和中等风险操作
        if dry_run:
            logger.info("🔍 预览模式：以下是将要执行的操作")
            self._preview_operations()
            return True
        
        # 6. 确认执行
        total_operations = len(self.risk_assessment['medium_risk']) + len(self.risk_assessment['low_risk'])
        if total_operations == 0:
            logger.info("✅ 数据库已同步，无需操作")
            return True
        
        response = input(f"\n将执行 {total_operations} 个操作，是否继续？(y/N): ").lower()
        if response != 'y':
            logger.info("同步已取消")
            return False
        
        # 7. 执行迁移
        success = self._execute_migrations()
        
        if success:
            logger.info("✅ 安全同步完成")
        else:
            logger.error("❌ 同步过程中出现错误")
        
        return success
    
    def _preview_operations(self):
        """预览将要执行的操作"""
        for risk_level in ['low_risk', 'medium_risk']:
            if self.risk_assessment[risk_level]:
                logger.info(f"\n{risk_level.replace('_', ' ').title()}操作:")
                for item in self.risk_assessment[risk_level]:
                    if item['type'] == 'missing_column':
                        logger.info(f"  - 添加列: {item['table']}.{item['column']}")
                    elif item['type'] == 'missing_table':
                        logger.info(f"  - 创建表: {item['table']}")
    
    def _execute_migrations(self):
        """执行迁移操作"""
        try:
            with self.render_engine.connect() as conn:
                trans = conn.begin()
                
                try:
                    executed_count = 0
                    
                    # 执行低风险操作
                    for item in self.risk_assessment['low_risk']:
                        if item['type'] == 'missing_column':
                            sql = item['solution'].strip()
                            if sql and not sql.startswith('--'):
                                logger.info(f"执行: {sql[:100]}...")
                                conn.execute(text(sql))
                                executed_count += 1
                    
                    # 执行中等风险操作
                    for item in self.risk_assessment['medium_risk']:
                        if item['type'] == 'missing_column':
                            sql = item['solution'].strip()
                            if sql and not sql.startswith('--'):
                                logger.info(f"执行: {sql[:100]}...")
                                conn.execute(text(sql))
                                executed_count += 1
                    
                    trans.commit()
                    logger.info(f"✅ 成功执行 {executed_count} 个操作")
                    return True
                    
                except Exception as e:
                    trans.rollback()
                    logger.error(f"执行失败，已回滚: {str(e)}")
                    return False
                    
        except Exception as e:
            logger.error(f"连接数据库失败: {str(e)}")
            return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='安全数据库同步解决方案')
    parser.add_argument('--check-constraints', action='store_true', help='检查约束冲突风险')
    parser.add_argument('--safe-sync', action='store_true', help='执行安全同步')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不执行实际操作')
    parser.add_argument('--backup-first', action='store_true', default=True, help='先备份再同步')
    parser.add_argument('--fix-constraints', action='store_true', help='修复约束问题')
    
    args = parser.parse_args()
    
    # 创建同步工具实例
    sync_tool = SafeDatabaseSync()
    
    try:
        if args.check_constraints:
            # 仅检查约束风险
            success = sync_tool.check_constraint_risks()
            if success:
                sync_tool.generate_safe_migration_sql()
            return 0 if success else 1
        
        elif args.safe_sync:
            # 执行安全同步
            success = sync_tool.execute_safe_sync(
                dry_run=args.dry_run,
                backup_first=args.backup_first
            )
            return 0 if success else 1
        
        else:
            # 默认：检查约束风险
            logger.info("未指定操作，默认执行约束风险检查")
            logger.info("使用 --help 查看所有选项")
            success = sync_tool.check_constraint_risks()
            if success:
                sync_tool.generate_safe_migration_sql()
            return 0 if success else 1
    
    except KeyboardInterrupt:
        logger.info("操作被用户中断")
        return 1
    except Exception as e:
        logger.error(f"执行过程中出错: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 