#!/usr/bin/env python3
"""
PMA云端数据库智能升级脚本
直接连接云端数据库，检查状态并完成升级
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CloudDatabaseUpgrader:
    def __init__(self):
        # 云端数据库URL
        self.cloud_db_url = 'postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d'
        self.engine = None
        self.inspector = None
        
    def connect_database(self):
        """连接云端数据库"""
        try:
            logger.info("连接云端数据库...")
            self.engine = create_engine(self.cloud_db_url)
            self.inspector = inspect(self.engine)
            
            # 测试连接
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("✅ 云端数据库连接成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {str(e)}")
            return False
    
    def check_current_state(self):
        """检查当前数据库状态"""
        logger.info("🔍 检查当前数据库状态...")
        
        state = {
            'alembic_version': None,
            'projects_rating_type': None,
            'quotations_has_confirmed_fields': False,
            'project_rating_records_rating_type': None,
            'constraints': [],
            'indexes': []
        }
        
        try:
            with self.engine.connect() as conn:
                # 检查Alembic版本
                result = conn.execute(text("SELECT version_num FROM alembic_version")).fetchone()
                if result:
                    state['alembic_version'] = result[0]
                    logger.info(f"当前迁移版本: {state['alembic_version']}")
                
                # 检查projects.rating类型
                result = conn.execute(text("""
                    SELECT data_type FROM information_schema.columns 
                    WHERE table_name = 'projects' AND column_name = 'rating'
                """)).fetchone()
                if result:
                    state['projects_rating_type'] = result[0]
                    logger.info(f"projects.rating 类型: {state['projects_rating_type']}")
                
                # 检查quotations表确认字段
                confirmed_fields = ['confirmed_at', 'confirmation_badge_status', 'product_signature']
                for field in confirmed_fields:
                    result = conn.execute(text(f"""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'quotations' AND column_name = '{field}'
                    """)).fetchone()
                    if result:
                        state['quotations_has_confirmed_fields'] = True
                        break
                
                # 检查project_rating_records.rating类型
                result = conn.execute(text("""
                    SELECT data_type FROM information_schema.columns 
                    WHERE table_name = 'project_rating_records' AND column_name = 'rating'
                """)).fetchone()
                if result:
                    state['project_rating_records_rating_type'] = result[0]
                    logger.info(f"project_rating_records.rating 类型: {state['project_rating_records_rating_type']}")
                
                # 检查约束
                constraints = conn.execute(text("""
                    SELECT constraint_name FROM information_schema.table_constraints 
                    WHERE table_name = 'project_rating_records' 
                    AND constraint_type = 'UNIQUE'
                """)).fetchall()
                state['constraints'] = [row[0] for row in constraints]
                logger.info(f"project_rating_records 约束: {state['constraints']}")
                
                # 检查索引
                indexes = conn.execute(text("""
                    SELECT indexname FROM pg_indexes 
                    WHERE tablename = 'project_rating_records'
                """)).fetchall()
                state['indexes'] = [row[0] for row in indexes]
                logger.info(f"project_rating_records 索引: {state['indexes']}")
                
        except Exception as e:
            logger.error(f"检查状态时出错: {e}")
        
        return state
    
    def execute_sql_safe(self, conn, sql, description):
        """安全执行SQL语句"""
        try:
            logger.info(f"执行: {description}")
            conn.execute(text(sql))
            logger.info(f"✅ {description} 成功")
            return True
        except Exception as e:
            logger.warning(f"⚠️ {description} 失败: {e}")
            return False
    
    def upgrade_projects_table(self, conn):
        """升级projects表"""
        logger.info("🔧 升级 projects 表...")
        
        return self.execute_sql_safe(
            conn,
            "ALTER TABLE projects ALTER COLUMN rating TYPE INTEGER USING rating::integer;",
            "修改 projects.rating 列类型为 INTEGER"
        )
    
    def upgrade_project_stage_history_table(self, conn):
        """升级project_stage_history表"""
        logger.info("🔧 升级 project_stage_history 表...")
        
        success = True
        success &= self.execute_sql_safe(
            conn,
            "DROP INDEX IF EXISTS ix_project_stage_history_user_id;",
            "删除 ix_project_stage_history_user_id 索引"
        )
        success &= self.execute_sql_safe(
            conn,
            "ALTER TABLE project_stage_history DROP COLUMN IF EXISTS user_id;",
            "删除 project_stage_history.user_id 列"
        )
        
        return success
    
    def upgrade_quotations_table(self, conn):
        """升级quotations表"""
        logger.info("🔧 升级 quotations 表...")
        
        success = True
        
        # 删除不需要的列
        old_columns = ['approval_required_fields', 'approval_comments', 'approved_at', 'approved_by']
        for col in old_columns:
            success &= self.execute_sql_safe(
                conn,
                f"ALTER TABLE quotations DROP COLUMN IF EXISTS {col};",
                f"删除 quotations.{col} 列"
            )
        
        # 添加新的列
        new_columns = [
            ("confirmed_at", "TIMESTAMP WITHOUT TIME ZONE"),
            ("confirmation_badge_color", "VARCHAR(20) DEFAULT NULL"),
            ("product_signature", "VARCHAR(64) DEFAULT NULL"),
            ("confirmed_by", "INTEGER"),
            ("confirmation_badge_status", "VARCHAR(20) DEFAULT 'none'")
        ]
        
        for col_name, col_def in new_columns:
            success &= self.execute_sql_safe(
                conn,
                f"ALTER TABLE quotations ADD COLUMN IF NOT EXISTS {col_name} {col_def};",
                f"添加 quotations.{col_name} 列"
            )
        
        # 添加外键约束
        success &= self.execute_sql_safe(
            conn,
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints 
                    WHERE constraint_name = 'quotations_confirmed_by_fkey'
                    AND table_name = 'quotations'
                ) THEN
                    ALTER TABLE quotations ADD CONSTRAINT quotations_confirmed_by_fkey 
                    FOREIGN KEY (confirmed_by) REFERENCES users(id);
                END IF;
            END $$;
            """,
            "添加 quotations_confirmed_by_fkey 外键约束"
        )
        
        return success
    
    def upgrade_event_registry_table(self, conn):
        """升级event_registry表"""
        logger.info("🔧 升级 event_registry 表...")
        
        return self.execute_sql_safe(
            conn,
            "DROP INDEX IF EXISTS ix_event_registry_event_key;",
            "删除 ix_event_registry_event_key 索引"
        )
    
    def upgrade_project_rating_records_table(self, conn):
        """升级project_rating_records表"""
        logger.info("🔧 升级 project_rating_records 表...")
        
        success = True
        
        # 删除多余的列
        success &= self.execute_sql_safe(
            conn,
            "ALTER TABLE project_rating_records DROP COLUMN IF EXISTS comment;",
            "删除 project_rating_records.comment 列"
        )
        
        # 修改rating列类型
        success &= self.execute_sql_safe(
            conn,
            "ALTER TABLE project_rating_records ALTER COLUMN rating TYPE INTEGER USING rating::integer;",
            "修改 project_rating_records.rating 列类型为 INTEGER"
        )
        
        # 彻底清理所有旧的约束和索引
        old_constraints = ['uq_project_rating_project_user', 'uq_project_user_rating']
        for constraint in old_constraints:
            success &= self.execute_sql_safe(
                conn,
                f"ALTER TABLE project_rating_records DROP CONSTRAINT IF EXISTS {constraint};",
                f"删除约束 {constraint}"
            )
        
        old_indexes = [
            'idx_project_rating_records_created_at',
            'uq_project_rating_project_user', 
            'idx_project_rating_records_project_id',
            'idx_project_rating_records_user_id',
            'uq_project_user_rating'
        ]
        for index in old_indexes:
            success &= self.execute_sql_safe(
                conn,
                f"DROP INDEX IF EXISTS {index};",
                f"删除索引 {index}"
            )
        
        # 创建新的唯一约束
        success &= self.execute_sql_safe(
            conn,
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints 
                    WHERE constraint_name = 'uq_project_user_rating'
                    AND table_name = 'project_rating_records'
                ) THEN
                    ALTER TABLE project_rating_records 
                    ADD CONSTRAINT uq_project_user_rating UNIQUE (project_id, user_id);
                END IF;
            END $$;
            """,
            "创建新的唯一约束 uq_project_user_rating"
        )
        
        return success
    
    def update_alembic_version(self, conn):
        """更新Alembic版本"""
        logger.info("🔧 更新 Alembic 版本...")
        
        return self.execute_sql_safe(
            conn,
            "UPDATE alembic_version SET version_num = 'c1308c08d0c9';",
            "更新 Alembic 迁移版本到 c1308c08d0c9"
        )
    
    def verify_upgrade(self, conn):
        """验证升级结果"""
        logger.info("🔍 验证升级结果...")
        
        verification_passed = True
        
        try:
            # 检查Alembic版本
            result = conn.execute(text("SELECT version_num FROM alembic_version")).fetchone()
            if result and result[0] == 'c1308c08d0c9':
                logger.info("✅ Alembic版本正确: c1308c08d0c9")
            else:
                logger.error(f"❌ Alembic版本错误: {result[0] if result else 'None'}")
                verification_passed = False
            
            # 检查projects.rating列类型
            result = conn.execute(text("""
                SELECT data_type FROM information_schema.columns 
                WHERE table_name = 'projects' AND column_name = 'rating'
            """)).fetchone()
            if result and result[0] == 'integer':
                logger.info("✅ projects.rating 列类型正确: integer")
            else:
                logger.error(f"❌ projects.rating 列类型错误: {result[0] if result else 'None'}")
                verification_passed = False
            
            # 检查quotations表新列
            new_columns = ['confirmed_at', 'confirmation_badge_status', 'product_signature']
            for col_name in new_columns:
                result = conn.execute(text(f"""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'quotations' AND column_name = '{col_name}'
                """)).fetchone()
                if result:
                    logger.info(f"✅ quotations.{col_name} 列存在")
                else:
                    logger.error(f"❌ quotations.{col_name} 列不存在")
                    verification_passed = False
            
            # 检查project_rating_records.rating列类型
            result = conn.execute(text("""
                SELECT data_type FROM information_schema.columns 
                WHERE table_name = 'project_rating_records' AND column_name = 'rating'
            """)).fetchone()
            if result and result[0] == 'integer':
                logger.info("✅ project_rating_records.rating 列类型正确: integer")
            else:
                logger.error(f"❌ project_rating_records.rating 列类型错误: {result[0] if result else 'None'}")
                verification_passed = False
            
            # 检查新约束
            result = conn.execute(text("""
                SELECT constraint_name FROM information_schema.table_constraints 
                WHERE table_name = 'project_rating_records' 
                AND constraint_name = 'uq_project_user_rating'
            """)).fetchone()
            if result:
                logger.info("✅ 新约束 uq_project_user_rating 存在")
            else:
                logger.error("❌ 新约束 uq_project_user_rating 不存在")
                verification_passed = False
                
        except Exception as e:
            logger.error(f"❌ 验证过程中出错: {e}")
            verification_passed = False
        
        return verification_passed
    
    def execute_upgrade(self):
        """执行完整的升级流程"""
        logger.info("🚀 开始执行云端数据库智能升级")
        
        if not self.connect_database():
            return False
        
        # 检查当前状态
        current_state = self.check_current_state()
        
        try:
            with self.engine.connect() as conn:
                trans = conn.begin()
                
                try:
                    success = True
                    
                    # 根据当前状态决定需要执行的步骤
                    if current_state['projects_rating_type'] != 'integer':
                        success &= self.upgrade_projects_table(conn)
                    else:
                        logger.info("✅ projects.rating 已是 integer 类型，跳过")
                    
                    success &= self.upgrade_project_stage_history_table(conn)
                    
                    if not current_state['quotations_has_confirmed_fields']:
                        success &= self.upgrade_quotations_table(conn)
                    else:
                        logger.info("✅ quotations 表确认字段已存在，跳过")
                    
                    success &= self.upgrade_event_registry_table(conn)
                    
                    if current_state['project_rating_records_rating_type'] != 'integer':
                        success &= self.upgrade_project_rating_records_table(conn)
                    else:
                        logger.info("✅ project_rating_records.rating 已是 integer 类型，跳过")
                    
                    if current_state['alembic_version'] != 'c1308c08d0c9':
                        success &= self.update_alembic_version(conn)
                    else:
                        logger.info("✅ Alembic 版本已是最新，跳过")
                    
                    if success:
                        # 验证升级结果
                        if self.verify_upgrade(conn):
                            trans.commit()
                            logger.info("🎉 数据库升级成功并验证通过！")
                            return True
                        else:
                            trans.rollback()
                            logger.error("❌ 升级验证失败，已回滚")
                            return False
                    else:
                        trans.rollback()
                        logger.error("❌ 升级过程中有步骤失败，已回滚")
                        return False
                        
                except Exception as e:
                    trans.rollback()
                    logger.error(f"❌ 升级失败，已回滚: {e}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            return False

def main():
    """主函数"""
    print("🔧 PMA云端数据库智能升级工具")
    print("=" * 60)
    print("直接连接云端数据库，智能检查并完成升级")
    print("=" * 60)
    
    try:
        upgrader = CloudDatabaseUpgrader()
        
        if upgrader.execute_upgrade():
            print("\n🎉 数据库升级完成！")
            print("\n📋 升级摘要:")
            print("- ✅ projects.rating 列类型已修改为 INTEGER")
            print("- ✅ quotations 表已添加确认相关字段")
            print("- ✅ project_rating_records 表结构已更新")
            print("- ✅ 约束和索引已正确重建")
            print("- ✅ Alembic 迁移版本已更新到 c1308c08d0c9")
            print("\n✅ 云端数据库已成功同步到本地版本！")
            return True
        else:
            print("\n❌ 数据库升级失败")
            return False
            
    except Exception as e:
        print(f"❌ 升级过程中出现意外错误: {e}")
        logger.exception("详细错误信息:")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 