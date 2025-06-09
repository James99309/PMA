#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
将本地数据库结构同步到云端PostgreSQL数据库
"""

import os
import sys
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade, init, migrate
from config import Config, CLOUD_DB_URL
from sqlalchemy import create_engine, text, inspect
import subprocess

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_migration_app():
    """创建用于迁移的Flask应用"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 确保使用云端数据库URL
    app.config['SQLALCHEMY_DATABASE_URI'] = CLOUD_DB_URL
    logger.info(f"使用云端数据库: {CLOUD_DB_URL[:50]}...")
    
    return app

def verify_cloud_connection():
    """验证云端数据库连接"""
    try:
        engine = create_engine(CLOUD_DB_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"✓ 云端数据库连接成功")
            logger.info(f"PostgreSQL版本: {version}")
            return True
    except Exception as e:
        logger.error(f"✗ 云端数据库连接失败: {str(e)}")
        return False

def check_migration_status():
    """检查迁移状态"""
    try:
        from app import create_app
        app = create_app()
        
        # 设置云端数据库
        app.config['SQLALCHEMY_DATABASE_URI'] = CLOUD_DB_URL
        
        with app.app_context():
            from flask_migrate import current
            try:
                head = current()
                if head:
                    logger.info(f"当前迁移版本: {head}")
                else:
                    logger.info("数据库尚未初始化迁移")
                return head
            except Exception as e:
                logger.warning(f"无法获取当前迁移版本: {str(e)}")
                return None
    except Exception as e:
        logger.error(f"检查迁移状态失败: {str(e)}")
        return None

def initialize_migration():
    """初始化迁移（如果需要）"""
    try:
        if not os.path.exists('migrations'):
            logger.info("初始化迁移环境...")
            result = subprocess.run(['flask', 'db', 'init'], 
                                  capture_output=True, text=True, 
                                  env={**os.environ, 'FLASK_APP': 'run.py'})
            if result.returncode == 0:
                logger.info("✓ 迁移环境初始化成功")
            else:
                logger.error(f"迁移环境初始化失败: {result.stderr}")
                return False
        else:
            logger.info("迁移环境已存在")
        return True
    except Exception as e:
        logger.error(f"初始化迁移失败: {str(e)}")
        return False

def create_migration():
    """创建新的迁移"""
    try:
        logger.info("生成新的迁移文件...")
        result = subprocess.run([
            'flask', 'db', 'migrate', 
            '-m', 'sync_to_cloud_database'
        ], capture_output=True, text=True, 
           env={**os.environ, 'FLASK_APP': 'run.py'})
        
        if result.returncode == 0:
            logger.info("✓ 迁移文件生成成功")
            logger.info(result.stdout)
            return True
        else:
            logger.warning(f"迁移文件生成: {result.stderr}")
            # 可能没有新的变更，这不是错误
            if "No changes in schema detected" in result.stderr:
                logger.info("没有检测到模式变更")
                return True
            return False
    except Exception as e:
        logger.error(f"生成迁移文件失败: {str(e)}")
        return False

def apply_migrations():
    """应用迁移到云端数据库"""
    try:
        logger.info("应用迁移到云端数据库...")
        result = subprocess.run(['flask', 'db', 'upgrade'], 
                              capture_output=True, text=True,
                              env={**os.environ, 'FLASK_APP': 'run.py'})
        
        if result.returncode == 0:
            logger.info("✓ 迁移应用成功")
            logger.info(result.stdout)
            return True
        else:
            logger.error(f"迁移应用失败: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"应用迁移失败: {str(e)}")
        return False

def verify_sync():
    """验证同步结果"""
    try:
        engine = create_engine(CLOUD_DB_URL)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        logger.info(f"✓ 云端数据库包含 {len(tables)} 个表:")
        for table in sorted(tables):
            logger.info(f"  - {table}")
        
        return True
    except Exception as e:
        logger.error(f"验证同步结果失败: {str(e)}")
        return False

def main():
    """主同步流程"""
    logger.info("=" * 60)
    logger.info("开始将本地数据库结构同步到云端PostgreSQL")
    logger.info("=" * 60)
    
    # 设置环境变量
    os.environ['FLASK_APP'] = 'run.py'
    os.environ['DATABASE_URL'] = CLOUD_DB_URL
    
    # 步骤1: 验证云端数据库连接
    logger.info("\n步骤1: 验证云端数据库连接")
    if not verify_cloud_connection():
        logger.error("无法连接到云端数据库，同步失败")
        return False
    
    # 步骤2: 检查迁移状态
    logger.info("\n步骤2: 检查迁移状态")
    current_version = check_migration_status()
    
    # 步骤3: 初始化迁移（如果需要）
    logger.info("\n步骤3: 初始化迁移环境")
    if not initialize_migration():
        logger.error("迁移环境初始化失败")
        return False
    
    # 步骤4: 生成迁移文件
    logger.info("\n步骤4: 生成迁移文件")
    if not create_migration():
        logger.warning("迁移文件生成有问题，但继续执行")
    
    # 步骤5: 应用迁移
    logger.info("\n步骤5: 应用迁移到云端数据库")
    if not apply_migrations():
        logger.error("迁移应用失败")
        return False
    
    # 步骤6: 验证同步结果
    logger.info("\n步骤6: 验证同步结果")
    if not verify_sync():
        logger.error("同步验证失败")
        return False
    
    logger.info("\n" + "=" * 60)
    logger.info("🎉 数据库结构同步到云端完成!")
    logger.info("=" * 60)
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        if success:
            logger.info("同步成功完成")
            sys.exit(0)
        else:
            logger.error("同步失败")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n用户中断同步过程")
        sys.exit(1)
    except Exception as e:
        logger.error(f"同步过程发生异常: {str(e)}")
        sys.exit(1) 