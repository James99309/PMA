#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
添加account_id字段到project_stage_history表
并填充已有数据的account_id
"""

from app import create_app, db
from app.models.projectpm_stage_history import ProjectStageHistory
from app.models.project import Project
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_column_exists(table, column):
    """检查表中是否存在指定列"""
    try:
        from sqlalchemy import text
        sql = text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='{table}' AND column_name='{column}'
        """)
        
        result = db.session.execute(sql).fetchone()
        return result is not None
    except Exception as e:
        logger.error(f"检查列是否存在时出错: {str(e)}")
        return False

def add_column():
    """添加account_id字段到project_stage_history表"""
    try:
        from sqlalchemy import text
        
        # 检查字段是否已存在
        if check_column_exists('project_stage_history', 'account_id'):
            logger.info("account_id字段已存在，跳过添加")
            return True
            
        # 添加account_id字段
        sql = text("""
            ALTER TABLE project_stage_history 
            ADD COLUMN account_id INTEGER;
        """)
        db.session.execute(sql)
        
        # 创建索引
        index_sql = text("""
            CREATE INDEX IF NOT EXISTS ix_project_stage_history_account_id 
            ON project_stage_history (account_id);
        """)
        db.session.execute(index_sql)
        
        db.session.commit()
        logger.info("成功添加account_id字段和索引")
        return True
    except Exception as e:
        logger.error(f"添加字段失败: {str(e)}")
        db.session.rollback()
        return False

def fill_account_data():
    """填充已有数据的account_id字段"""
    try:
        # 查询所有历史记录
        records = ProjectStageHistory.query.filter(ProjectStageHistory.account_id.is_(None)).all()
        
        if not records:
            logger.info("没有需要更新的历史记录")
            return True
            
        logger.info(f"找到 {len(records)} 条需要更新account_id的历史记录")
        
        updated = 0
        for record in records:
            # 获取项目创建者ID
            project = Project.query.get(record.project_id)
            if project and project.created_by:
                record.account_id = project.created_by
                updated += 1
        
        if updated > 0:
            db.session.commit()
            logger.info(f"更新了 {updated} 条历史记录的账户信息")
        else:
            logger.warning("没有更新任何记录")
            
        return True
    except Exception as e:
        logger.error(f"填充账户数据失败: {str(e)}")
        db.session.rollback()
        return False

def run_migration():
    """运行迁移脚本"""
    app = create_app()
    
    with app.app_context():
        logger.info("开始执行数据库迁移...")
        
        # 添加字段
        if add_column():
            # 填充数据
            fill_account_data()
            
            # 验证结果
            if check_column_exists('project_stage_history', 'account_id'):
                logger.info("迁移成功：account_id字段已添加并填充数据")
                return True
            else:
                logger.error("迁移失败：account_id字段未添加")
                return False
        else:
            logger.error("添加字段失败，无法继续")
            return False

if __name__ == "__main__":
    import sys
    
    success = run_migration()
    if success:
        logger.info("迁移脚本执行成功")
        sys.exit(0)
    else:
        logger.error("迁移脚本执行失败")
        sys.exit(1) 