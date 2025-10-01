#!/usr/bin/env python3
"""
PMA数据库同步工具
比较本地和云端数据库结构，生成精确的升级脚本
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
import json
from datetime import datetime

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseSyncTool:
    def __init__(self):
        # 本地数据库URL (从环境变量或默认值)
        self.local_db_url = os.environ.get('DATABASE_URL', 'postgresql://nijie@localhost:5432/pma_local')
        
        # 云端数据库URL
        self.cloud_db_url = 'postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d'
        
        self.local_engine = None
        self.cloud_engine = None
        self.local_inspector = None
        self.cloud_inspector = None
        
    def connect_databases(self):
        """连接到本地和云端数据库"""
        try:
            logger.info("连接本地数据库...")
            self.local_engine = create_engine(self.local_db_url)
            self.local_inspector = inspect(self.local_engine)
            
            logger.info("连接云端数据库...")
            self.cloud_engine = create_engine(self.cloud_db_url)
            self.cloud_inspector = inspect(self.cloud_engine)
            
            # 测试连接
            with self.local_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✓ 本地数据库连接成功")
            
            with self.cloud_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✓ 云端数据库连接成功")
            
            return True
            
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            return False
    
    def get_table_structure(self, inspector, table_name):
        """获取表结构详细信息"""
        try:
            structure = {
                'columns': inspector.get_columns(table_name),
                'indexes': inspector.get_indexes(table_name),
                'unique_constraints': inspector.get_unique_constraints(table_name),
                'foreign_keys': inspector.get_foreign_keys(table_name),
                'primary_key': inspector.get_pk_constraint(table_name),
                'check_constraints': inspector.get_check_constraints(table_name) if hasattr(inspector, 'get_check_constraints') else []
            }
            return structure
        except Exception as e:
            logger.warning(f"获取表 {table_name} 结构失败: {e}")
            return None
    
    def compare_databases(self):
        """比较本地和云端数据库结构"""
        logger.info("🔍 开始比较数据库结构...")
        
        # 获取表列表
        local_tables = set(self.local_inspector.get_table_names())
        cloud_tables = set(self.cloud_inspector.get_table_names())
        
        logger.info(f"本地数据库表数量: {len(local_tables)}")
        logger.info(f"云端数据库表数量: {len(cloud_tables)}")
        
        # 分析差异
        differences = {
            'missing_tables': local_tables - cloud_tables,  # 云端缺失的表
            'extra_tables': cloud_tables - local_tables,    # 云端多余的表
            'common_tables': local_tables & cloud_tables,   # 共同的表
            'table_differences': {}
        }
        
        logger.info(f"云端缺失表: {differences['missing_tables']}")
        logger.info(f"云端多余表: {differences['extra_tables']}")
        logger.info(f"共同表: {len(differences['common_tables'])}")
        
        # 比较共同表的结构差异
        for table_name in differences['common_tables']:
            local_structure = self.get_table_structure(self.local_inspector, table_name)
            cloud_structure = self.get_table_structure(self.cloud_inspector, table_name)
            
            if local_structure and cloud_structure:
                table_diff = self.compare_table_structure(table_name, local_structure, cloud_structure)
                if table_diff:
                    differences['table_differences'][table_name] = table_diff
        
        return differences
    
    def compare_table_structure(self, table_name, local_structure, cloud_structure):
        """比较单个表的结构差异"""
        differences = {}
        
        # 比较列
        local_columns = {col['name']: col for col in local_structure['columns']}
        cloud_columns = {col['name']: col for col in cloud_structure['columns']}
        
        missing_columns = set(local_columns.keys()) - set(cloud_columns.keys())
        extra_columns = set(cloud_columns.keys()) - set(local_columns.keys())
        changed_columns = []
        
        # 检查列的差异
        for col_name in set(local_columns.keys()) & set(cloud_columns.keys()):
            local_col = local_columns[col_name]
            cloud_col = cloud_columns[col_name]
            
            # 比较列类型、可空性等
            if (str(local_col['type']) != str(cloud_col['type']) or 
                local_col['nullable'] != cloud_col['nullable'] or
                local_col.get('default') != cloud_col.get('default')):
                changed_columns.append({
                    'name': col_name,
                    'local': local_col,
                    'cloud': cloud_col
                })
        
        if missing_columns or extra_columns or changed_columns:
            differences['columns'] = {
                'missing': missing_columns,
                'extra': extra_columns,
                'changed': changed_columns
            }
        
        # 比较索引
        local_indexes = {idx['name']: idx for idx in local_structure['indexes']}
        cloud_indexes = {idx['name']: idx for idx in cloud_structure['indexes']}
        
        missing_indexes = set(local_indexes.keys()) - set(cloud_indexes.keys())
        extra_indexes = set(cloud_indexes.keys()) - set(local_indexes.keys())
        
        if missing_indexes or extra_indexes:
            differences['indexes'] = {
                'missing': missing_indexes,
                'extra': extra_indexes,
                'local_indexes': local_indexes,
                'cloud_indexes': cloud_indexes
            }
        
        # 比较约束
        local_constraints = {const['name']: const for const in local_structure['unique_constraints']}
        cloud_constraints = {const['name']: const for const in cloud_structure['unique_constraints']}
        
        missing_constraints = set(local_constraints.keys()) - set(cloud_constraints.keys())
        extra_constraints = set(cloud_constraints.keys()) - set(local_constraints.keys())
        
        if missing_constraints or extra_constraints:
            differences['constraints'] = {
                'missing': missing_constraints,
                'extra': extra_constraints,
                'local_constraints': local_constraints,
                'cloud_constraints': cloud_constraints
            }
        
        return differences if differences else None
    
    def generate_upgrade_script(self, differences):
        """生成升级脚本"""
        logger.info("📝 生成数据库升级脚本...")
        
        sql_statements = []
        
        # 1. 删除多余的表
        for table_name in differences['extra_tables']:
            if table_name != 'alembic_version':  # 保留Alembic版本表
                sql_statements.append(f"-- 删除多余的表: {table_name}")
                sql_statements.append(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
                sql_statements.append("")
        
        # 2. 创建缺失的表 (这个需要从本地获取完整的CREATE语句)
        for table_name in differences['missing_tables']:
            sql_statements.append(f"-- 需要创建表: {table_name}")
            sql_statements.append(f"-- 请从本地数据库导出 {table_name} 表的CREATE语句")
            sql_statements.append("")
        
        # 3. 修改现有表结构
        for table_name, table_diff in differences['table_differences'].items():
            sql_statements.append(f"-- 修改表: {table_name}")
            
            # 处理列差异
            if 'columns' in table_diff:
                col_diff = table_diff['columns']
                
                # 删除多余的列
                for col_name in col_diff.get('extra', []):
                    sql_statements.append(f"ALTER TABLE {table_name} DROP COLUMN IF EXISTS {col_name};")
                
                # 添加缺失的列
                for col_name in col_diff.get('missing', []):
                    sql_statements.append(f"-- 需要添加列: {table_name}.{col_name}")
                    sql_statements.append(f"-- ALTER TABLE {table_name} ADD COLUMN {col_name} ...;")
                
                # 修改变更的列
                for col_change in col_diff.get('changed', []):
                    col_name = col_change['name']
                    local_col = col_change['local']
                    cloud_col = col_change['cloud']
                    
                    sql_statements.append(f"-- 修改列: {table_name}.{col_name}")
                    sql_statements.append(f"-- 本地: {local_col['type']}, 可空: {local_col['nullable']}")
                    sql_statements.append(f"-- 云端: {cloud_col['type']}, 可空: {cloud_col['nullable']}")
                    
                    # 类型转换
                    if str(local_col['type']) != str(cloud_col['type']):
                        sql_statements.append(f"ALTER TABLE {table_name} ALTER COLUMN {col_name} TYPE {local_col['type']};")
                    
                    # 可空性修改
                    if local_col['nullable'] != cloud_col['nullable']:
                        if local_col['nullable']:
                            sql_statements.append(f"ALTER TABLE {table_name} ALTER COLUMN {col_name} DROP NOT NULL;")
                        else:
                            sql_statements.append(f"ALTER TABLE {table_name} ALTER COLUMN {col_name} SET NOT NULL;")
            
            # 处理索引差异
            if 'indexes' in table_diff:
                idx_diff = table_diff['indexes']
                
                # 删除多余的索引
                for idx_name in idx_diff.get('extra', []):
                    sql_statements.append(f"DROP INDEX IF EXISTS {idx_name};")
                
                # 创建缺失的索引
                for idx_name in idx_diff.get('missing', []):
                    if idx_name in idx_diff['local_indexes']:
                        idx_info = idx_diff['local_indexes'][idx_name]
                        columns = ', '.join(idx_info['column_names'])
                        unique_clause = 'UNIQUE ' if idx_info.get('unique', False) else ''
                        sql_statements.append(f"CREATE {unique_clause}INDEX {idx_name} ON {table_name} ({columns});")
            
            # 处理约束差异
            if 'constraints' in table_diff:
                const_diff = table_diff['constraints']
                
                # 删除多余的约束
                for const_name in const_diff.get('extra', []):
                    sql_statements.append(f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS {const_name};")
                
                # 创建缺失的约束
                for const_name in const_diff.get('missing', []):
                    if const_name in const_diff['local_constraints']:
                        const_info = const_diff['local_constraints'][const_name]
                        columns = ', '.join(const_info['column_names'])
                        sql_statements.append(f"ALTER TABLE {table_name} ADD CONSTRAINT {const_name} UNIQUE ({columns});")
            
            sql_statements.append("")
        
        return sql_statements
    
    def execute_upgrade(self, sql_statements):
        """执行升级脚本"""
        logger.info("🚀 开始执行数据库升级...")
        
        try:
            with self.cloud_engine.connect() as conn:
                trans = conn.begin()
                
                try:
                    executed_count = 0
                    for sql in sql_statements:
                        sql = sql.strip()
                        if sql and not sql.startswith('--'):
                            logger.info(f"执行: {sql[:100]}...")
                            conn.execute(text(sql))
                            executed_count += 1
                    
                    trans.commit()
                    logger.info(f"✅ 升级成功，执行了 {executed_count} 条SQL语句")
                    return True
                    
                except Exception as e:
                    trans.rollback()
                    logger.error(f"升级失败，已回滚: {e}")
                    return False
                    
        except Exception as e:
            logger.error(f"连接云端数据库失败: {e}")
            return False
    
    def save_upgrade_script(self, sql_statements):
        """保存升级脚本到文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"cloud_db_upgrade_{timestamp}.sql"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("-- PMA云端数据库升级脚本\n")
            f.write(f"-- 生成时间: {datetime.now()}\n")
            f.write("-- 将云端数据库结构同步到本地版本\n\n")
            f.write("BEGIN;\n\n")
            
            for sql in sql_statements:
                f.write(sql + '\n')
            
            f.write("\nCOMMIT;\n")
        
        logger.info(f"✅ 升级脚本已保存到: {filename}")
        return filename
    
    def sync_databases(self):
        """执行完整的数据库同步流程"""
        logger.info("🔄 开始数据库同步流程...")
        
        # 1. 连接数据库
        if not self.connect_databases():
            return False
        
        # 2. 比较结构差异
        differences = self.compare_databases()
        
        # 3. 生成升级脚本
        sql_statements = self.generate_upgrade_script(differences)
        
        # 4. 保存脚本
        script_file = self.save_upgrade_script(sql_statements)
        
        # 5. 显示差异摘要
        logger.info("\n📊 数据库差异摘要:")
        logger.info(f"云端缺失表: {len(differences['missing_tables'])}")
        logger.info(f"云端多余表: {len(differences['extra_tables'])}")
        logger.info(f"需要修改的表: {len(differences['table_differences'])}")
        
        # 6. 询问是否执行升级
        print(f"\n升级脚本已生成: {script_file}")
        print("请检查脚本内容，确认无误后可以执行升级。")
        
        return True

def main():
    """主函数"""
    print("🔧 PMA数据库同步工具")
    print("=" * 40)
    
    try:
        sync_tool = DatabaseSyncTool()
        
        if sync_tool.sync_databases():
            print("\n🎉 数据库结构分析完成！")
            print("\n📋 下一步:")
            print("1. 检查生成的SQL脚本")
            print("2. 在云端执行升级脚本")
            print("3. 验证升级结果")
            return True
        else:
            print("\n❌ 数据库同步失败")
            return False
            
    except Exception as e:
        print(f"❌ 同步过程中出现错误: {e}")
        logger.exception("详细错误信息:")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 