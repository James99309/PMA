#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render全面修复工具

集成所有修复功能:
1. 数据库布尔值字段类型修复
2. 模板语法错误修复
3. API导入错误修复
"""

import os
import sys
import logging
import subprocess
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('render_fix_all.log')
    ]
)
logger = logging.getLogger('Render全面修复')

def run_script(script_path):
    """运行指定的脚本"""
    try:
        logger.info(f"正在运行脚本: {script_path}")
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"脚本 {script_path} 运行成功")
        logger.debug(f"输出: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"脚本 {script_path} 运行失败: {e}")
        logger.error(f"错误输出: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"运行脚本 {script_path} 时出错: {str(e)}")
        return False

def fix_database():
    """修复数据库问题"""
    script_path = Path('database_migration_tools/render_db_fix.py')
    if not script_path.exists():
        logger.error(f"数据库修复脚本不存在: {script_path}")
        return False
    
    return run_script(script_path)

def fix_templates():
    """修复模板语法错误"""
    script_path = Path('database_migration_tools/fix_template_errors.py')
    if not script_path.exists():
        logger.error(f"模板修复脚本不存在: {script_path}")
        return False
    
    return run_script(script_path)

def fix_api_imports():
    """修复API导入问题"""
    script_path = Path('database_migration_tools/fix_api_imports.py')
    if not script_path.exists():
        logger.error(f"API修复脚本不存在: {script_path}")
        return False
    
    return run_script(script_path)

def fix_user_module():
    """修复用户管理模块问题"""
    script_path = Path('database_migration_tools/fix_user_module.py')
    if not script_path.exists():
        logger.error(f"用户管理模块修复脚本不存在: {script_path}")
        return False
    
    return run_script(script_path)

def check_environment():
    """检查环境变量"""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.warning("环境变量DATABASE_URL未设置，数据库修复可能无法正常工作")
    
    flask_env = os.environ.get('FLASK_ENV')
    logger.info(f"当前环境: {flask_env or '未设置'}")
    
    return True

def restart_application():
    """尝试重启应用程序"""
    try:
        # 在Render环境中，创建restart.txt文件将触发应用重启
        tmp_dir = Path('tmp')
        tmp_dir.mkdir(exist_ok=True)
        
        restart_file = tmp_dir / 'restart.txt'
        restart_file.touch()
        
        logger.info("已创建重启标记文件，应用程序将在一分钟内重启")
        return True
    except Exception as e:
        logger.error(f"重启应用程序时出错: {str(e)}")
        return False

def main():
    """主函数"""
    logger.info("=== 开始全面修复Render应用 ===")
    
    # 检查环境
    check_environment()
    
    # 执行模板修复
    templates_fixed = fix_templates()
    logger.info(f"模板修复{'成功' if templates_fixed else '失败'}")
    
    # 执行API导入修复
    api_fixed = fix_api_imports()
    logger.info(f"API修复{'成功' if api_fixed else '失败'}")
    
    # 执行数据库修复
    db_fixed = fix_database()
    logger.info(f"数据库修复{'成功' if db_fixed else '失败'}")
    
    # 执行用户模块修复
    user_fixed = fix_user_module()
    logger.info(f"用户模块修复{'成功' if user_fixed else '失败'}")
    
    # 如果有任何修复成功，重启应用
    if templates_fixed or api_fixed or db_fixed or user_fixed:
        restart_application()
    
    logger.info("=== Render应用全面修复完成 ===")

if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-
"""
Render全面修复工具

集成所有修复功能:
1. 数据库布尔值字段类型修复
2. 模板语法错误修复
3. API导入错误修复
"""

import os
import sys
import logging
import subprocess
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('render_fix_all.log')
    ]
)
logger = logging.getLogger('Render全面修复')

def run_script(script_path):
    """运行指定的脚本"""
    try:
        logger.info(f"正在运行脚本: {script_path}")
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"脚本 {script_path} 运行成功")
        logger.debug(f"输出: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"脚本 {script_path} 运行失败: {e}")
        logger.error(f"错误输出: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"运行脚本 {script_path} 时出错: {str(e)}")
        return False

def fix_database():
    """修复数据库问题"""
    script_path = Path('database_migration_tools/render_db_fix.py')
    if not script_path.exists():
        logger.error(f"数据库修复脚本不存在: {script_path}")
        return False
    
    return run_script(script_path)

def fix_templates():
    """修复模板语法错误"""
    script_path = Path('database_migration_tools/fix_template_errors.py')
    if not script_path.exists():
        logger.error(f"模板修复脚本不存在: {script_path}")
        return False
    
    return run_script(script_path)

def fix_api_imports():
    """修复API导入问题"""
    script_path = Path('database_migration_tools/fix_api_imports.py')
    if not script_path.exists():
        logger.error(f"API修复脚本不存在: {script_path}")
        return False
    
    return run_script(script_path)

def fix_user_module():
    """修复用户管理模块问题"""
    script_path = Path('database_migration_tools/fix_user_module.py')
    if not script_path.exists():
        logger.error(f"用户管理模块修复脚本不存在: {script_path}")
        return False
    
    return run_script(script_path)

def check_environment():
    """检查环境变量"""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.warning("环境变量DATABASE_URL未设置，数据库修复可能无法正常工作")
    
    flask_env = os.environ.get('FLASK_ENV')
    logger.info(f"当前环境: {flask_env or '未设置'}")
    
    return True

def restart_application():
    """尝试重启应用程序"""
    try:
        # 在Render环境中，创建restart.txt文件将触发应用重启
        tmp_dir = Path('tmp')
        tmp_dir.mkdir(exist_ok=True)
        
        restart_file = tmp_dir / 'restart.txt'
        restart_file.touch()
        
        logger.info("已创建重启标记文件，应用程序将在一分钟内重启")
        return True
    except Exception as e:
        logger.error(f"重启应用程序时出错: {str(e)}")
        return False

def main():
    """主函数"""
    logger.info("=== 开始全面修复Render应用 ===")
    
    # 检查环境
    check_environment()
    
    # 执行模板修复
    templates_fixed = fix_templates()
    logger.info(f"模板修复{'成功' if templates_fixed else '失败'}")
    
    # 执行API导入修复
    api_fixed = fix_api_imports()
    logger.info(f"API修复{'成功' if api_fixed else '失败'}")
    
    # 执行数据库修复
    db_fixed = fix_database()
    logger.info(f"数据库修复{'成功' if db_fixed else '失败'}")
    
    # 执行用户模块修复
    user_fixed = fix_user_module()
    logger.info(f"用户模块修复{'成功' if user_fixed else '失败'}")
    
    # 如果有任何修复成功，重启应用
    if templates_fixed or api_fixed or db_fixed or user_fixed:
        restart_application()
    
    logger.info("=== Render应用全面修复完成 ===")

if __name__ == "__main__":
    main() 
 
 
# -*- coding: utf-8 -*-
"""
Render全面修复工具

集成所有修复功能:
1. 数据库布尔值字段类型修复
2. 模板语法错误修复
3. API导入错误修复
"""

import os
import sys
import logging
import subprocess
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('render_fix_all.log')
    ]
)
logger = logging.getLogger('Render全面修复')

def run_script(script_path):
    """运行指定的脚本"""
    try:
        logger.info(f"正在运行脚本: {script_path}")
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"脚本 {script_path} 运行成功")
        logger.debug(f"输出: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"脚本 {script_path} 运行失败: {e}")
        logger.error(f"错误输出: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"运行脚本 {script_path} 时出错: {str(e)}")
        return False

def fix_database():
    """修复数据库问题"""
    script_path = Path('database_migration_tools/render_db_fix.py')
    if not script_path.exists():
        logger.error(f"数据库修复脚本不存在: {script_path}")
        return False
    
    return run_script(script_path)

def fix_templates():
    """修复模板语法错误"""
    script_path = Path('database_migration_tools/fix_template_errors.py')
    if not script_path.exists():
        logger.error(f"模板修复脚本不存在: {script_path}")
        return False
    
    return run_script(script_path)

def fix_api_imports():
    """修复API导入问题"""
    script_path = Path('database_migration_tools/fix_api_imports.py')
    if not script_path.exists():
        logger.error(f"API修复脚本不存在: {script_path}")
        return False
    
    return run_script(script_path)

def fix_user_module():
    """修复用户管理模块问题"""
    script_path = Path('database_migration_tools/fix_user_module.py')
    if not script_path.exists():
        logger.error(f"用户管理模块修复脚本不存在: {script_path}")
        return False
    
    return run_script(script_path)

def check_environment():
    """检查环境变量"""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.warning("环境变量DATABASE_URL未设置，数据库修复可能无法正常工作")
    
    flask_env = os.environ.get('FLASK_ENV')
    logger.info(f"当前环境: {flask_env or '未设置'}")
    
    return True

def restart_application():
    """尝试重启应用程序"""
    try:
        # 在Render环境中，创建restart.txt文件将触发应用重启
        tmp_dir = Path('tmp')
        tmp_dir.mkdir(exist_ok=True)
        
        restart_file = tmp_dir / 'restart.txt'
        restart_file.touch()
        
        logger.info("已创建重启标记文件，应用程序将在一分钟内重启")
        return True
    except Exception as e:
        logger.error(f"重启应用程序时出错: {str(e)}")
        return False

def main():
    """主函数"""
    logger.info("=== 开始全面修复Render应用 ===")
    
    # 检查环境
    check_environment()
    
    # 执行模板修复
    templates_fixed = fix_templates()
    logger.info(f"模板修复{'成功' if templates_fixed else '失败'}")
    
    # 执行API导入修复
    api_fixed = fix_api_imports()
    logger.info(f"API修复{'成功' if api_fixed else '失败'}")
    
    # 执行数据库修复
    db_fixed = fix_database()
    logger.info(f"数据库修复{'成功' if db_fixed else '失败'}")
    
    # 执行用户模块修复
    user_fixed = fix_user_module()
    logger.info(f"用户模块修复{'成功' if user_fixed else '失败'}")
    
    # 如果有任何修复成功，重启应用
    if templates_fixed or api_fixed or db_fixed or user_fixed:
        restart_application()
    
    logger.info("=== Render应用全面修复完成 ===")

if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-
"""
Render全面修复工具

集成所有修复功能:
1. 数据库布尔值字段类型修复
2. 模板语法错误修复
3. API导入错误修复
"""

import os
import sys
import logging
import subprocess
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('render_fix_all.log')
    ]
)
logger = logging.getLogger('Render全面修复')

def run_script(script_path):
    """运行指定的脚本"""
    try:
        logger.info(f"正在运行脚本: {script_path}")
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"脚本 {script_path} 运行成功")
        logger.debug(f"输出: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"脚本 {script_path} 运行失败: {e}")
        logger.error(f"错误输出: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"运行脚本 {script_path} 时出错: {str(e)}")
        return False

def fix_database():
    """修复数据库问题"""
    script_path = Path('database_migration_tools/render_db_fix.py')
    if not script_path.exists():
        logger.error(f"数据库修复脚本不存在: {script_path}")
        return False
    
    return run_script(script_path)

def fix_templates():
    """修复模板语法错误"""
    script_path = Path('database_migration_tools/fix_template_errors.py')
    if not script_path.exists():
        logger.error(f"模板修复脚本不存在: {script_path}")
        return False
    
    return run_script(script_path)

def fix_api_imports():
    """修复API导入问题"""
    script_path = Path('database_migration_tools/fix_api_imports.py')
    if not script_path.exists():
        logger.error(f"API修复脚本不存在: {script_path}")
        return False
    
    return run_script(script_path)

def fix_user_module():
    """修复用户管理模块问题"""
    script_path = Path('database_migration_tools/fix_user_module.py')
    if not script_path.exists():
        logger.error(f"用户管理模块修复脚本不存在: {script_path}")
        return False
    
    return run_script(script_path)

def check_environment():
    """检查环境变量"""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.warning("环境变量DATABASE_URL未设置，数据库修复可能无法正常工作")
    
    flask_env = os.environ.get('FLASK_ENV')
    logger.info(f"当前环境: {flask_env or '未设置'}")
    
    return True

def restart_application():
    """尝试重启应用程序"""
    try:
        # 在Render环境中，创建restart.txt文件将触发应用重启
        tmp_dir = Path('tmp')
        tmp_dir.mkdir(exist_ok=True)
        
        restart_file = tmp_dir / 'restart.txt'
        restart_file.touch()
        
        logger.info("已创建重启标记文件，应用程序将在一分钟内重启")
        return True
    except Exception as e:
        logger.error(f"重启应用程序时出错: {str(e)}")
        return False

def main():
    """主函数"""
    logger.info("=== 开始全面修复Render应用 ===")
    
    # 检查环境
    check_environment()
    
    # 执行模板修复
    templates_fixed = fix_templates()
    logger.info(f"模板修复{'成功' if templates_fixed else '失败'}")
    
    # 执行API导入修复
    api_fixed = fix_api_imports()
    logger.info(f"API修复{'成功' if api_fixed else '失败'}")
    
    # 执行数据库修复
    db_fixed = fix_database()
    logger.info(f"数据库修复{'成功' if db_fixed else '失败'}")
    
    # 执行用户模块修复
    user_fixed = fix_user_module()
    logger.info(f"用户模块修复{'成功' if user_fixed else '失败'}")
    
    # 如果有任何修复成功，重启应用
    if templates_fixed or api_fixed or db_fixed or user_fixed:
        restart_application()
    
    logger.info("=== Render应用全面修复完成 ===")

if __name__ == "__main__":
    main() 
 
 