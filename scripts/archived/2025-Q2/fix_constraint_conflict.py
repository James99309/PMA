#!/usr/bin/env python3
"""
修复约束冲突的紧急脚本
专门解决 uq_scoring_config 约束已存在的问题
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConstraintConflictFixer:
    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL环境变量未设置")
        
        self.engine = create_engine(self.database_url)
        self.inspector = inspect(self.engine)
    
    def check_constraint_exists(self, table_name, constraint_name):
        """检查约束是否存在"""
        try:
            unique_constraints = self.inspector.get_unique_constraints(table_name)
            return any(constraint['name'] == constraint_name for constraint in unique_constraints)
        except:
            return False
    
    def check_table_exists(self, table_name):
        """检查表是否存在"""
        return table_name in self.inspector.get_table_names()
    
    def list_existing_constraints(self, table_name):
        """列出表的所有约束"""
        try:
            unique_constraints = self.inspector.get_unique_constraints(table_name)
            logger.info(f"表 {table_name} 的唯一约束:")
            for constraint in unique_constraints:
                logger.info(f"  - {constraint['name']}: {constraint['column_names']}")
            return unique_constraints
        except Exception as e:
            logger.error(f"获取约束信息失败: {e}")
            return []
    
    def fix_constraint_conflicts(self):
        """修复约束冲突"""
        logger.info("🔧 开始修复约束冲突")
        
        try:
            with self.engine.connect() as conn:
                trans = conn.begin()
                
                try:
                    # 1. 检查 project_scoring_config 表
                    if self.check_table_exists('project_scoring_config'):
                        logger.info("=== 检查 project_scoring_config 表约束 ===")
                        self.list_existing_constraints('project_scoring_config')
                        
                        # 如果 uq_scoring_config 已存在，则跳过创建
                        if self.check_constraint_exists('project_scoring_config', 'uq_scoring_config'):
                            logger.info("✓ uq_scoring_config 约束已存在，无需创建")
                        else:
                            logger.info("创建 uq_scoring_config 约束...")
                            conn.execute(text("ALTER TABLE project_scoring_config ADD CONSTRAINT uq_scoring_config UNIQUE (category, field_name)"))
                            logger.info("✓ uq_scoring_config 约束创建成功")
                    
                    # 2. 检查 project_scoring_records 表
                    if self.check_table_exists('project_scoring_records'):
                        logger.info("=== 检查 project_scoring_records 表约束 ===")
                        self.list_existing_constraints('project_scoring_records')
                        
                        # 如果 uq_scoring_record_with_user 已存在，则跳过创建
                        if self.check_constraint_exists('project_scoring_records', 'uq_scoring_record_with_user'):
                            logger.info("✓ uq_scoring_record_with_user 约束已存在，无需创建")
                        else:
                            logger.info("创建 uq_scoring_record_with_user 约束...")
                            conn.execute(text("ALTER TABLE project_scoring_records ADD CONSTRAINT uq_scoring_record_with_user UNIQUE (project_id, category, field_name, awarded_by)"))
                            logger.info("✓ uq_scoring_record_with_user 约束创建成功")
                    
                    # 3. 删除可能存在的旧约束（如果存在）
                    logger.info("=== 清理可能存在的旧约束 ===")
                    
                    # 删除 project_scoring_config 的旧约束
                    if self.check_constraint_exists('project_scoring_config', 'project_scoring_config_category_field_name_key'):
                        logger.info("删除旧约束: project_scoring_config_category_field_name_key")
                        conn.execute(text("ALTER TABLE project_scoring_config DROP CONSTRAINT project_scoring_config_category_field_name_key"))
                        logger.info("✓ 旧约束删除成功")
                    
                    # 删除 project_scoring_records 的旧约束
                    if self.check_constraint_exists('project_scoring_records', 'project_scoring_records_project_id_category_field_name_key'):
                        logger.info("删除旧约束: project_scoring_records_project_id_category_field_name_key")
                        conn.execute(text("ALTER TABLE project_scoring_records DROP CONSTRAINT project_scoring_records_project_id_category_field_name_key"))
                        logger.info("✓ 旧约束删除成功")
                    
                    trans.commit()
                    logger.info("✅ 约束冲突修复完成")
                    return True
                    
                except Exception as e:
                    trans.rollback()
                    logger.error(f"修复失败，已回滚: {e}")
                    return False
                    
        except Exception as e:
            logger.error(f"连接数据库失败: {e}")
            return False
    
    def run_flask_migration(self):
        """运行Flask迁移"""
        logger.info("🚀 执行Flask数据库迁移")
        
        try:
            import subprocess
            result = subprocess.run(['flask', 'db', 'upgrade'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Flask迁移执行成功")
                logger.info(result.stdout)
                return True
            else:
                logger.error("❌ Flask迁移执行失败")
                logger.error(result.stderr)
                return False
        except Exception as e:
            logger.error(f"执行Flask迁移时出错: {e}")
            return False
    
    def verify_final_state(self):
        """验证最终状态"""
        logger.info("🔍 验证最终状态")
        
        try:
            # 检查迁移版本
            import subprocess
            result = subprocess.run(['flask', 'db', 'current'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                current_version = result.stdout.strip().split('\n')[-1]
                logger.info(f"当前迁移版本: {current_version}")
            
            # 检查约束状态
            logger.info("=== 最终约束状态 ===")
            if self.check_table_exists('project_scoring_config'):
                self.list_existing_constraints('project_scoring_config')
            
            if self.check_table_exists('project_scoring_records'):
                self.list_existing_constraints('project_scoring_records')
            
            return True
            
        except Exception as e:
            logger.error(f"验证过程中出错: {e}")
            return False

def main():
    """主函数"""
    print("🔧 PMA系统约束冲突修复工具")
    print("=" * 40)
    
    try:
        fixer = ConstraintConflictFixer()
        
        # 1. 修复约束冲突
        if not fixer.fix_constraint_conflicts():
            print("❌ 约束冲突修复失败")
            return False
        
        # 2. 运行Flask迁移
        if not fixer.run_flask_migration():
            print("❌ Flask迁移失败")
            return False
        
        # 3. 验证最终状态
        if not fixer.verify_final_state():
            print("❌ 状态验证失败")
            return False
        
        print("\n🎉 约束冲突修复成功完成！")
        print("\n📋 接下来可以:")
        print("1. 重新启动应用")
        print("2. 测试关键功能")
        print("3. 检查项目列表筛选功能")
        
        return True
        
    except Exception as e:
        print(f"❌ 修复过程中出现错误: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 