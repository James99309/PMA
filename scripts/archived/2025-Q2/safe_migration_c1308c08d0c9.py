#!/usr/bin/env python3
"""
安全的数据库迁移脚本 - 替换 c1308c08d0c9
包含完整的存在性检查，避免删除不存在的索引和约束
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SafeMigrationExecutor:
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
            if not self.check_table_exists(table_name):
                return False
            indexes = self.inspector.get_indexes(table_name)
            return any(idx['name'] == index_name for idx in indexes)
        except:
            return False
    
    def check_constraint_exists(self, table_name, constraint_name):
        """检查约束是否存在"""
        try:
            if not self.check_table_exists(table_name):
                return False
            unique_constraints = self.inspector.get_unique_constraints(table_name)
            return any(constraint['name'] == constraint_name for constraint in unique_constraints)
        except:
            return False
    
    def check_column_exists(self, table_name, column_name):
        """检查列是否存在"""
        try:
            if not self.check_table_exists(table_name):
                return False
            columns = self.inspector.get_columns(table_name)
            return any(col['name'] == column_name for col in columns)
        except:
            return False
    
    def safe_execute_sql(self, sql, description=""):
        """安全执行SQL"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
                if description:
                    logger.info(f"✓ {description}")
                return True
        except Exception as e:
            logger.warning(f"⚠️ {description} - 跳过: {str(e)[:100]}")
            return False
    
    def execute_safe_migration(self):
        """执行安全迁移 - 模拟原始 c1308c08d0c9 的所有操作"""
        logger.info("🚀 开始执行安全数据库迁移 (c1308c08d0c9)")
        
        operations_executed = 0
        operations_skipped = 0
        
        try:
            with self.engine.connect() as conn:
                trans = conn.begin()
                
                try:
                    # 1. 处理 project_rating_records 表
                    logger.info("=== 处理 project_rating_records 表 ===")
                    if self.check_table_exists('project_rating_records'):
                        # 删除索引
                        indexes_to_drop = [
                            'idx_project_rating_records_created_at',
                            'idx_project_rating_records_project_id', 
                            'idx_project_rating_records_user_id'
                        ]
                        
                        for index_name in indexes_to_drop:
                            if self.check_index_exists('project_rating_records', index_name):
                                conn.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
                                logger.info(f"✓ 删除索引: {index_name}")
                                operations_executed += 1
                            else:
                                logger.info(f"⚠️ 索引不存在，跳过: {index_name}")
                                operations_skipped += 1
                        
                        # 删除表
                        conn.execute(text("DROP TABLE IF EXISTS project_rating_records CASCADE"))
                        logger.info("✓ 删除表: project_rating_records")
                        operations_executed += 1
                    else:
                        logger.info("⚠️ 表 project_rating_records 不存在，跳过相关操作")
                        operations_skipped += 4
                    
                    # 2. 处理 approval_record 表 - 修复 step_id NOT NULL
                    logger.info("=== 处理 approval_record 表 ===")
                    if self.check_table_exists('approval_record'):
                        # 首先修复可能的NULL值
                        result = conn.execute(text("SELECT COUNT(*) FROM approval_record WHERE step_id IS NULL"))
                        null_count = result.scalar()
                        
                        if null_count > 0:
                            logger.warning(f"发现 {null_count} 条step_id为NULL的记录，正在修复...")
                            # 获取一个有效的step_id
                            result = conn.execute(text("SELECT MIN(id) FROM approval_step"))
                            min_step_id = result.scalar()
                            
                            if min_step_id:
                                conn.execute(text(f"UPDATE approval_record SET step_id = {min_step_id} WHERE step_id IS NULL"))
                                logger.info(f"✓ 修复NULL值，设置为step_id = {min_step_id}")
                                operations_executed += 1
                            else:
                                logger.error("找不到有效的step_id，无法修复")
                                trans.rollback()
                                return False
                        
                        # 设置 step_id 为 NOT NULL
                        conn.execute(text("ALTER TABLE approval_record ALTER COLUMN step_id SET NOT NULL"))
                        logger.info("✓ 设置 approval_record.step_id 为 NOT NULL")
                        operations_executed += 1
                    
                    # 3. 处理 project_scoring_config 表
                    logger.info("=== 处理 project_scoring_config 表 ===")
                    if self.check_table_exists('project_scoring_config'):
                        # 删除索引
                        if self.check_index_exists('project_scoring_config', 'idx_scoring_config_category'):
                            conn.execute(text("DROP INDEX IF EXISTS idx_scoring_config_category"))
                            logger.info("✓ 删除索引: idx_scoring_config_category")
                            operations_executed += 1
                        else:
                            logger.info("⚠️ 索引 idx_scoring_config_category 不存在，跳过")
                            operations_skipped += 1
                        
                        # 删除旧约束（如果存在）
                        if self.check_constraint_exists('project_scoring_config', 'project_scoring_config_category_field_name_key'):
                            conn.execute(text("ALTER TABLE project_scoring_config DROP CONSTRAINT project_scoring_config_category_field_name_key"))
                            logger.info("✓ 删除约束: project_scoring_config_category_field_name_key")
                            operations_executed += 1
                        else:
                            logger.info("⚠️ 约束 project_scoring_config_category_field_name_key 不存在，跳过")
                            operations_skipped += 1
                        
                        # 创建新约束（如果不存在）
                        if not self.check_constraint_exists('project_scoring_config', 'uq_scoring_config'):
                            conn.execute(text("ALTER TABLE project_scoring_config ADD CONSTRAINT uq_scoring_config UNIQUE (category, field_name)"))
                            logger.info("✓ 创建约束: uq_scoring_config")
                            operations_executed += 1
                        else:
                            logger.info("⚠️ 约束 uq_scoring_config 已存在，跳过创建")
                            operations_skipped += 1
                    
                    # 4. 处理 project_scoring_records 表
                    logger.info("=== 处理 project_scoring_records 表 ===")
                    if self.check_table_exists('project_scoring_records'):
                        # 删除索引
                        indexes_to_drop = ['idx_scoring_records_category', 'idx_scoring_records_project']
                        for index_name in indexes_to_drop:
                            if self.check_index_exists('project_scoring_records', index_name):
                                conn.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
                                logger.info(f"✓ 删除索引: {index_name}")
                                operations_executed += 1
                            else:
                                logger.info(f"⚠️ 索引 {index_name} 不存在，跳过")
                                operations_skipped += 1
                        
                        # 删除旧约束（如果存在）
                        if self.check_constraint_exists('project_scoring_records', 'project_scoring_records_project_id_category_field_name_key'):
                            conn.execute(text("ALTER TABLE project_scoring_records DROP CONSTRAINT project_scoring_records_project_id_category_field_name_key"))
                            logger.info("✓ 删除约束: project_scoring_records_project_id_category_field_name_key")
                            operations_executed += 1
                        else:
                            logger.info("⚠️ 约束 project_scoring_records_project_id_category_field_name_key 不存在，跳过")
                            operations_skipped += 1
                        
                        # 创建新约束（如果不存在）
                        if not self.check_constraint_exists('project_scoring_records', 'uq_scoring_record_with_user'):
                            conn.execute(text("ALTER TABLE project_scoring_records ADD CONSTRAINT uq_scoring_record_with_user UNIQUE (project_id, category, field_name, awarded_by)"))
                            logger.info("✓ 创建约束: uq_scoring_record_with_user")
                            operations_executed += 1
                        else:
                            logger.info("⚠️ 约束 uq_scoring_record_with_user 已存在，跳过创建")
                            operations_skipped += 1
                    
                    # 5. 处理 quotations 表
                    logger.info("=== 处理 quotations 表 ===")
                    if self.check_table_exists('quotations'):
                        # 删除索引
                        indexes_to_drop = ['idx_quotations_is_locked', 'idx_quotations_locked_by']
                        for index_name in indexes_to_drop:
                            if self.check_index_exists('quotations', index_name):
                                conn.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
                                logger.info(f"✓ 删除索引: {index_name}")
                                operations_executed += 1
                            else:
                                logger.info(f"⚠️ 索引 {index_name} 不存在，跳过")
                                operations_skipped += 1
                    
                    # 6. 处理 projects 表 - 更改 rating 列类型
                    logger.info("=== 处理 projects 表 ===")
                    if self.check_table_exists('projects') and self.check_column_exists('projects', 'rating'):
                        # 检查当前列类型
                        columns = self.inspector.get_columns('projects')
                        rating_column = next((col for col in columns if col['name'] == 'rating'), None)
                        
                        if rating_column:
                            current_type = str(rating_column['type'])
                            if 'NUMERIC' in current_type or 'DECIMAL' in current_type:
                                # 需要转换为INTEGER
                                conn.execute(text("ALTER TABLE projects ALTER COLUMN rating TYPE INTEGER USING rating::integer"))
                                logger.info("✓ 更改 projects.rating 列类型为 INTEGER")
                                operations_executed += 1
                            else:
                                logger.info("⚠️ projects.rating 列已是整数类型，跳过转换")
                                operations_skipped += 1
                    
                    trans.commit()
                    logger.info(f"✅ 安全迁移完成: {operations_executed} 个操作成功, {operations_skipped} 个操作跳过")
                    return True
                    
                except Exception as e:
                    trans.rollback()
                    logger.error(f"迁移失败，已回滚: {e}")
                    return False
                    
        except Exception as e:
            logger.error(f"连接数据库失败: {e}")
            return False
    
    def mark_migration_as_applied(self):
        """标记迁移为已应用"""
        logger.info("🏷️ 标记迁移版本为已应用")
        
        try:
            with self.engine.connect() as conn:
                # 检查当前版本
                current_version = None
                try:
                    result = conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
                    current_version = result.scalar()
                    logger.info(f"当前迁移版本: {current_version}")
                except:
                    logger.warning("无法获取当前迁移版本")
                
                # 更新到目标版本
                target_version = 'c1308c08d0c9'
                if current_version != target_version:
                    if current_version:
                        conn.execute(text(f"UPDATE alembic_version SET version_num = '{target_version}'"))
                    else:
                        conn.execute(text(f"INSERT INTO alembic_version (version_num) VALUES ('{target_version}')"))
                    
                    conn.commit()
                    logger.info(f"✓ 迁移版本已更新为: {target_version}")
                else:
                    logger.info(f"✓ 迁移版本已是目标版本: {target_version}")
                
                return True
                
        except Exception as e:
            logger.error(f"标记迁移版本失败: {e}")
            return False
    
    def verify_migration_result(self):
        """验证迁移结果"""
        logger.info("🔍 验证迁移结果")
        
        try:
            with self.engine.connect() as conn:
                # 检查关键约束是否存在
                success_count = 0
                total_checks = 0
                
                # 1. 检查 project_scoring_config 约束
                total_checks += 1
                if self.check_constraint_exists('project_scoring_config', 'uq_scoring_config'):
                    logger.info("✓ project_scoring_config.uq_scoring_config 约束存在")
                    success_count += 1
                else:
                    logger.error("❌ project_scoring_config.uq_scoring_config 约束缺失")
                
                # 2. 检查 project_scoring_records 约束
                total_checks += 1
                if self.check_constraint_exists('project_scoring_records', 'uq_scoring_record_with_user'):
                    logger.info("✓ project_scoring_records.uq_scoring_record_with_user 约束存在")
                    success_count += 1
                else:
                    logger.error("❌ project_scoring_records.uq_scoring_record_with_user 约束缺失")
                
                # 3. 检查 approval_record.step_id 是否为 NOT NULL
                total_checks += 1
                if self.check_table_exists('approval_record'):
                    columns = self.inspector.get_columns('approval_record')
                    step_id_column = next((col for col in columns if col['name'] == 'step_id'), None)
                    if step_id_column and not step_id_column['nullable']:
                        logger.info("✓ approval_record.step_id 列为 NOT NULL")
                        success_count += 1
                    else:
                        logger.error("❌ approval_record.step_id 列仍允许 NULL")
                
                # 4. 检查不应存在的表
                total_checks += 1
                if not self.check_table_exists('project_rating_records'):
                    logger.info("✓ project_rating_records 表已删除")
                    success_count += 1
                else:
                    logger.warning("⚠️ project_rating_records 表仍存在")
                
                logger.info(f"验证结果: {success_count}/{total_checks} 项检查通过")
                return success_count == total_checks
                
        except Exception as e:
            logger.error(f"验证过程中出错: {e}")
            return False

def main():
    """主函数"""
    print("🔧 PMA系统安全迁移执行器 (c1308c08d0c9)")
    print("=" * 50)
    
    try:
        executor = SafeMigrationExecutor()
        
        # 1. 执行安全迁移
        if not executor.execute_safe_migration():
            print("❌ 安全迁移执行失败")
            return False
        
        # 2. 标记迁移为已应用
        if not executor.mark_migration_as_applied():
            print("❌ 标记迁移版本失败")
            return False
        
        # 3. 验证迁移结果
        if not executor.verify_migration_result():
            print("❌ 迁移结果验证失败")
            return False
        
        print("\n🎉 安全迁移执行成功完成！")
        print("\n📋 接下来可以:")
        print("1. 重新启动应用")
        print("2. 测试关键功能")
        print("3. 检查项目列表筛选功能")
        
        return True
        
    except Exception as e:
        print(f"❌ 迁移过程中出现错误: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 