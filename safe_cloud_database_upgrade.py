#!/usr/bin/env python3
"""
PMA系统安全云端数据库升级脚本
专门解决迁移中的存在性检查问题
"""

import os
import sys
import psycopg2
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SafeDatabaseUpgrade:
    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL环境变量未设置")
        
        self.engine = create_engine(self.database_url)
        self.inspector = inspect(self.engine)
    
    def check_table_exists(self, table_name):
        """检查表是否存在"""
        return table_name in self.inspector.get_table_names()
    
    def check_index_exists(self, table_name, index_name):
        """检查索引是否存在"""
        try:
            indexes = self.inspector.get_indexes(table_name)
            return any(idx['name'] == index_name for idx in indexes)
        except:
            return False
    
    def check_constraint_exists(self, table_name, constraint_name):
        """检查约束是否存在"""
        try:
            unique_constraints = self.inspector.get_unique_constraints(table_name)
            return any(constraint['name'] == constraint_name for constraint in unique_constraints)
        except:
            return False
    
    def check_column_nullable(self, table_name, column_name):
        """检查列是否允许NULL"""
        try:
            columns = self.inspector.get_columns(table_name)
            for col in columns:
                if col['name'] == column_name:
                    return col['nullable']
            return None
        except:
            return None
    
    def safe_drop_index(self, table_name, index_name):
        """安全删除索引"""
        if self.check_index_exists(table_name, index_name):
            sql = f"DROP INDEX IF EXISTS {index_name}"
            logger.info(f"删除索引: {index_name}")
            return sql
        else:
            logger.info(f"索引 {index_name} 不存在，跳过删除")
            return None
    
    def safe_drop_constraint(self, table_name, constraint_name, constraint_type='unique'):
        """安全删除约束"""
        if self.check_constraint_exists(table_name, constraint_name):
            sql = f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS {constraint_name}"
            logger.info(f"删除约束: {constraint_name}")
            return sql
        else:
            logger.info(f"约束 {constraint_name} 不存在，跳过删除")
            return None
    
    def safe_drop_table(self, table_name):
        """安全删除表"""
        if self.check_table_exists(table_name):
            sql = f"DROP TABLE IF EXISTS {table_name} CASCADE"
            logger.info(f"删除表: {table_name}")
            return sql
        else:
            logger.info(f"表 {table_name} 不存在，跳过删除")
            return None
    
    def fix_approval_record_step_id(self):
        """修复approval_record表的step_id NULL值问题"""
        logger.info("检查并修复approval_record.step_id NULL值...")
        
        with self.engine.connect() as conn:
            # 检查NULL值数量
            result = conn.execute(text("SELECT COUNT(*) FROM approval_record WHERE step_id IS NULL"))
            null_count = result.scalar()
            
            if null_count > 0:
                logger.warning(f"发现 {null_count} 条step_id为NULL的记录")
                
                # 获取一个有效的step_id
                result = conn.execute(text("SELECT MIN(id) FROM approval_step"))
                min_step_id = result.scalar()
                
                if min_step_id:
                    # 修复NULL值
                    conn.execute(text(f"UPDATE approval_record SET step_id = {min_step_id} WHERE step_id IS NULL"))
                    conn.commit()
                    logger.info(f"已将NULL值更新为step_id = {min_step_id}")
                else:
                    logger.error("找不到有效的step_id，无法修复NULL值")
                    return False
            else:
                logger.info("approval_record.step_id 无NULL值，无需修复")
        
        return True
    
    def generate_safe_migration_sql(self):
        """生成安全的迁移SQL"""
        safe_sql = []
        
        # 1. 安全删除project_rating_records表的索引
        logger.info("=== 处理project_rating_records表 ===")
        if self.check_table_exists('project_rating_records'):
            for index_name in ['idx_project_rating_records_created_at', 
                             'idx_project_rating_records_project_id', 
                             'idx_project_rating_records_user_id']:
                sql = self.safe_drop_index('project_rating_records', index_name)
                if sql:
                    safe_sql.append(sql)
            
            # 删除表
            sql = self.safe_drop_table('project_rating_records')
            if sql:
                safe_sql.append(sql)
        
        # 2. 安全删除project_scoring_config约束和索引
        logger.info("=== 处理project_scoring_config表 ===")
        if self.check_table_exists('project_scoring_config'):
            # 删除索引
            sql = self.safe_drop_index('project_scoring_config', 'idx_scoring_config_category')
            if sql:
                safe_sql.append(sql)
            
            # 删除约束
            sql = self.safe_drop_constraint('project_scoring_config', 'project_scoring_config_category_field_name_key')
            if sql:
                safe_sql.append(sql)
            
            # 创建新约束
            safe_sql.append("ALTER TABLE project_scoring_config ADD CONSTRAINT uq_scoring_config UNIQUE (category, field_name)")
        
        # 3. 安全删除project_scoring_records约束和索引
        logger.info("=== 处理project_scoring_records表 ===")
        if self.check_table_exists('project_scoring_records'):
            # 删除索引
            for index_name in ['idx_scoring_records_category', 'idx_scoring_records_project']:
                sql = self.safe_drop_index('project_scoring_records', index_name)
                if sql:
                    safe_sql.append(sql)
            
            # 删除约束
            sql = self.safe_drop_constraint('project_scoring_records', 'project_scoring_records_project_id_category_field_name_key')
            if sql:
                safe_sql.append(sql)
            
            # 创建新约束
            safe_sql.append("ALTER TABLE project_scoring_records ADD CONSTRAINT uq_scoring_record_with_user UNIQUE (project_id, category, field_name, awarded_by)")
        
        # 4. 安全删除quotations表的索引
        logger.info("=== 处理quotations表 ===")
        if self.check_table_exists('quotations'):
            for index_name in ['idx_quotations_is_locked', 'idx_quotations_locked_by']:
                sql = self.safe_drop_index('quotations', index_name)
                if sql:
                    safe_sql.append(sql)
        
        return safe_sql
    
    def execute_safe_migration(self):
        """执行安全迁移"""
        logger.info("🚀 开始安全数据库迁移")
        
        try:
            # 1. 修复数据完整性问题
            if not self.fix_approval_record_step_id():
                logger.error("数据完整性修复失败")
                return False
            
            # 2. 生成并执行安全迁移SQL
            safe_sql = self.generate_safe_migration_sql()
            
            if safe_sql:
                logger.info(f"准备执行 {len(safe_sql)} 条安全SQL语句")
                
                with self.engine.connect() as conn:
                    trans = conn.begin()
                    try:
                        for sql in safe_sql:
                            logger.info(f"执行: {sql}")
                            conn.execute(text(sql))
                        
                        trans.commit()
                        logger.info("✅ 安全迁移SQL执行成功")
                    except Exception as e:
                        trans.rollback()
                        logger.error(f"SQL执行失败: {e}")
                        return False
            else:
                logger.info("无需执行额外的安全迁移SQL")
            
            # 3. 执行Alembic迁移
            logger.info("执行Alembic数据库迁移...")
            import subprocess
            result = subprocess.run(['flask', 'db', 'upgrade'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Alembic迁移执行成功")
                logger.info(result.stdout)
                return True
            else:
                logger.error("❌ Alembic迁移执行失败")
                logger.error(result.stderr)
                return False
        
        except Exception as e:
            logger.error(f"迁移过程中出现错误: {e}")
            return False
    
    def verify_migration(self):
        """验证迁移结果"""
        logger.info("🔍 验证迁移结果")
        
        try:
            with self.engine.connect() as conn:
                # 检查当前迁移版本
                result = subprocess.run(['flask', 'db', 'current'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    current_version = result.stdout.strip().split('\n')[-1]
                    logger.info(f"当前迁移版本: {current_version}")
                    
                    if 'c1308c08d0c9' in current_version:
                        logger.info("✅ 迁移版本验证成功")
                    else:
                        logger.warning(f"⚠️ 迁移版本可能不正确: {current_version}")
                
                # 检查数据完整性
                result = conn.execute(text("SELECT COUNT(*) FROM approval_record WHERE step_id IS NULL"))
                null_count = result.scalar()
                
                if null_count == 0:
                    logger.info("✅ 数据完整性验证成功")
                else:
                    logger.error(f"❌ 仍有 {null_count} 条step_id为NULL的记录")
                    return False
                
                return True
        
        except Exception as e:
            logger.error(f"验证过程中出现错误: {e}")
            return False

def main():
    """主函数"""
    print("🚀 PMA系统安全云端数据库升级")
    print("=" * 50)
    
    try:
        upgrader = SafeDatabaseUpgrade()
        
        # 执行安全迁移
        if upgrader.execute_safe_migration():
            # 验证迁移结果
            if upgrader.verify_migration():
                print("\n🎉 数据库升级成功完成！")
                print("\n📋 下一步验证:")
                print("1. 访问应用确认正常启动")
                print("2. 测试项目列表筛选功能")
                print("3. 检查所有关键功能正常")
                return True
            else:
                print("\n❌ 数据库升级验证失败")
                return False
        else:
            print("\n❌ 数据库升级执行失败")
            return False
    
    except Exception as e:
        print(f"\n❌ 升级过程中出现严重错误: {e}")
        return False

if __name__ == "__main__":
    import subprocess
    success = main()
    sys.exit(0 if success else 1) 