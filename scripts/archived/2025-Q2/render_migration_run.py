#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render数据库迁移自动化执行脚本
按顺序执行全部迁移步骤，确保数据库成功迁移

作者: Claude
创建日期: 2025-05-03
"""

import os
import sys
import logging
import importlib.util
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('render_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('迁移执行器')

# 迁移脚本列表，按执行顺序排列
MIGRATION_SCRIPTS = [
    'update_db_config.py',         # 更新数据库配置
    'create_render_db_tables.py',  # 创建数据库表结构
    'migrate_data_to_render.py',   # 迁移数据
    'fix_dev_products_fk.py'       # 修复外键约束
]

def import_module_from_file(file_path):
    """动态导入Python模块"""
    try:
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        logger.error(f"导入模块 {file_path} 失败: {e}")
        return None

def run_migration():
    """按顺序执行所有迁移脚本"""
    start_time = time.time()
    logger.info("开始执行数据库迁移...")
    
    success_count = 0
    
    for script in MIGRATION_SCRIPTS:
        script_path = os.path.join(os.path.dirname(__file__), script)
        
        if not os.path.exists(script_path):
            logger.error(f"迁移脚本 {script} 不存在")
            continue
        
        try:
            logger.info(f"执行 {script}...")
            
            # 导入并执行脚本
            module = import_module_from_file(script_path)
            if module and hasattr(module, 'main'):
                result = module.main()
                
                if result == 0:
                    logger.info(f"脚本 {script} 执行成功")
                    success_count += 1
                else:
                    logger.error(f"脚本 {script} 执行失败，返回值: {result}")
            else:
                logger.error(f"脚本 {script} 不包含main函数")
        except Exception as e:
            logger.error(f"执行脚本 {script} 时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info(f"迁移执行完成，总耗时: {duration:.2f} 秒")
    logger.info(f"成功执行 {success_count}/{len(MIGRATION_SCRIPTS)} 个脚本")
    
    return 0 if success_count == len(MIGRATION_SCRIPTS) else 1

if __name__ == "__main__":
    sys.exit(run_migration()) 
# -*- coding: utf-8 -*-
"""
Render数据库迁移自动化执行脚本
按顺序执行全部迁移步骤，确保数据库成功迁移

作者: Claude
创建日期: 2025-05-03
"""

import os
import sys
import logging
import importlib.util
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('render_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('迁移执行器')

# 迁移脚本列表，按执行顺序排列
MIGRATION_SCRIPTS = [
    'update_db_config.py',         # 更新数据库配置
    'create_render_db_tables.py',  # 创建数据库表结构
    'migrate_data_to_render.py',   # 迁移数据
    'fix_dev_products_fk.py'       # 修复外键约束
]

def import_module_from_file(file_path):
    """动态导入Python模块"""
    try:
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        logger.error(f"导入模块 {file_path} 失败: {e}")
        return None

def run_migration():
    """按顺序执行所有迁移脚本"""
    start_time = time.time()
    logger.info("开始执行数据库迁移...")
    
    success_count = 0
    
    for script in MIGRATION_SCRIPTS:
        script_path = os.path.join(os.path.dirname(__file__), script)
        
        if not os.path.exists(script_path):
            logger.error(f"迁移脚本 {script} 不存在")
            continue
        
        try:
            logger.info(f"执行 {script}...")
            
            # 导入并执行脚本
            module = import_module_from_file(script_path)
            if module and hasattr(module, 'main'):
                result = module.main()
                
                if result == 0:
                    logger.info(f"脚本 {script} 执行成功")
                    success_count += 1
                else:
                    logger.error(f"脚本 {script} 执行失败，返回值: {result}")
            else:
                logger.error(f"脚本 {script} 不包含main函数")
        except Exception as e:
            logger.error(f"执行脚本 {script} 时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info(f"迁移执行完成，总耗时: {duration:.2f} 秒")
    logger.info(f"成功执行 {success_count}/{len(MIGRATION_SCRIPTS)} 个脚本")
    
    return 0 if success_count == len(MIGRATION_SCRIPTS) else 1

if __name__ == "__main__":
    sys.exit(run_migration()) 