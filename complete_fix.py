#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import shutil
import logging
import subprocess
from app import create_app, db
from app.models.user import User

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger('系统修复')

def fix_template_syntax():
    """修复模板语法问题"""
    from fix_templates import fix_jinja_templates
    logger.info("开始修复模板语法...")
    fix_jinja_templates()
    logger.info("模板语法修复完成")

def fix_user_accounts():
    """修复用户账户问题"""
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if admin:
            logger.info(f"找到admin用户 (ID: {admin.id})")
            
            # 确保admin的is_active为True
            admin.is_active = True
            
            # 确保密码是正确的
            from werkzeug.security import generate_password_hash, check_password_hash
            expected_password = "1505562299AaBb"
            if not admin.check_password(expected_password):
                logger.info("重置admin用户密码...")
                admin.password_hash = generate_password_hash(expected_password)
            
            try:
                db.session.commit()
                logger.info("用户账户修复完成")
            except Exception as e:
                db.session.rollback()
                logger.error(f"用户账户修复失败: {e}")
        else:
            logger.error("找不到admin用户，请检查数据库")

def check_api_module():
    """检查API模块的问题"""
    api_file = 'app/routes/api.py'
    if os.path.exists(api_file):
        logger.info(f"检查API模块: {api_file}")
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查常见的导入错误
        errors = []
        if 'from flask_wtf.csrf import CSRFProtect' in content:
            errors.append("发现错误: 'from flask_wtf.csrf import CSRFProtect'")
        if 'from flask_wtf.csrf import CSRFProtect' in content:
            errors.append("发现错误: 'from flask_wtf.csrf import CSRFProtect'")
        if 'from flask_wtf.csrf import CSRFProtect' in content:
            errors.append("发现错误: 'from flask_wtf.csrf import CSRFProtect'")
        
        if errors:
            logger.warning(f"API模块存在以下问题:\n" + "\n".join(errors))
            logger.info("建议执行 python fix_api.py 修复API模块")
        else:
            logger.info("API模块没有发现明显问题")
    else:
        logger.warning(f"找不到API模块: {api_file}")

def test_database_access():
    """测试数据库连接"""
    app = create_app()
    with app.app_context():
        try:
            users = User.query.all()
            logger.info(f"数据库连接正常，系统中有 {len(users)} 个用户")
        except Exception as e:
            logger.error(f"数据库连接测试失败: {e}")

def verify_flask_startup():
    """验证Flask应用是否可以启动"""
    logger.info("验证Flask应用启动...")
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8082))
        if result == 0:
            logger.info("Flask应用已在端口8082上运行")
            sock.close()
        else:
            logger.warning("Flask应用未运行，尝试启动")
            sock.close()
            # 尝试启动Flask应用
            subprocess.Popen(['python', 'run.py'])
            logger.info("已尝试启动Flask应用")
    except Exception as e:
        logger.error(f"验证Flask应用启动时出错: {e}")

def main():
    """综合修复主函数"""
    logger.info("开始进行系统综合修复...")
    
    # 执行各种修复
    fix_template_syntax()
    fix_user_accounts()
    check_api_module()
    test_database_access()
    verify_flask_startup()
    
    logger.info("\n全部修复完成。请尝试使用admin账户登录，密码: 1505562299AaBb")

if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-

import os
import re
import shutil
import logging
import subprocess
from app import create_app, db
from app.models.user import User

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger('系统修复')

def fix_template_syntax():
    """修复模板语法问题"""
    from fix_templates import fix_jinja_templates
    logger.info("开始修复模板语法...")
    fix_jinja_templates()
    logger.info("模板语法修复完成")

def fix_user_accounts():
    """修复用户账户问题"""
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if admin:
            logger.info(f"找到admin用户 (ID: {admin.id})")
            
            # 确保admin的is_active为True
            admin.is_active = True
            
            # 确保密码是正确的
            from werkzeug.security import generate_password_hash, check_password_hash
            expected_password = "1505562299AaBb"
            if not admin.check_password(expected_password):
                logger.info("重置admin用户密码...")
                admin.password_hash = generate_password_hash(expected_password)
            
            try:
                db.session.commit()
                logger.info("用户账户修复完成")
            except Exception as e:
                db.session.rollback()
                logger.error(f"用户账户修复失败: {e}")
        else:
            logger.error("找不到admin用户，请检查数据库")

def check_api_module():
    """检查API模块的问题"""
    api_file = 'app/routes/api.py'
    if os.path.exists(api_file):
        logger.info(f"检查API模块: {api_file}")
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查常见的导入错误
        errors = []
        if 'from flask_wtf.csrf import CSRFProtect' in content:
            errors.append("发现错误: 'from flask_wtf.csrf import CSRFProtect'")
        if 'from flask_wtf.csrf import CSRFProtect' in content:
            errors.append("发现错误: 'from flask_wtf.csrf import CSRFProtect'")
        if 'from flask_wtf.csrf import CSRFProtect' in content:
            errors.append("发现错误: 'from flask_wtf.csrf import CSRFProtect'")
        
        if errors:
            logger.warning(f"API模块存在以下问题:\n" + "\n".join(errors))
            logger.info("建议执行 python fix_api.py 修复API模块")
        else:
            logger.info("API模块没有发现明显问题")
    else:
        logger.warning(f"找不到API模块: {api_file}")

def test_database_access():
    """测试数据库连接"""
    app = create_app()
    with app.app_context():
        try:
            users = User.query.all()
            logger.info(f"数据库连接正常，系统中有 {len(users)} 个用户")
        except Exception as e:
            logger.error(f"数据库连接测试失败: {e}")

def verify_flask_startup():
    """验证Flask应用是否可以启动"""
    logger.info("验证Flask应用启动...")
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8082))
        if result == 0:
            logger.info("Flask应用已在端口8082上运行")
            sock.close()
        else:
            logger.warning("Flask应用未运行，尝试启动")
            sock.close()
            # 尝试启动Flask应用
            subprocess.Popen(['python', 'run.py'])
            logger.info("已尝试启动Flask应用")
    except Exception as e:
        logger.error(f"验证Flask应用启动时出错: {e}")

def main():
    """综合修复主函数"""
    logger.info("开始进行系统综合修复...")
    
    # 执行各种修复
    fix_template_syntax()
    fix_user_accounts()
    check_api_module()
    test_database_access()
    verify_flask_startup()
    
    logger.info("\n全部修复完成。请尝试使用admin账户登录，密码: 1505562299AaBb")

if __name__ == "__main__":
    main() 