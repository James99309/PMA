#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import shutil
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger('API修复')

def fix_api_imports(api_file='app/routes/api.py'):
    """修复API模块中的导入问题"""
    if not os.path.exists(api_file):
        logger.error(f"API文件不存在: {api_file}")
        return False
    
    # 创建备份
    backup_file = f"{api_file}.bak"
    if not os.path.exists(backup_file):
        shutil.copy2(api_file, backup_file)
        logger.info(f"已创建备份文件: {backup_file}")
    
    try:
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复常见的导入问题
        fixed_content = content
        
        # 修复1: 从flask导入csrf的问题
        if re.search(r'from\s+flask\s+import\s+(?:[^,\n]+,\s*)*csrf(?:,|$|\s)', fixed_content):
            logger.info("检测到导入flask.csrf的错误")
            fixed_content = re.sub(
                r'from\s+flask\s+import\s+([^,\n]*,\s*)*csrf(,|$|\s)',
                lambda m: m.group(0).replace('csrf', ''),
                fixed_content
            )
            # 添加正确的导入
            if 'from flask_wtf.csrf import CSRFProtect' not in fixed_content:
                fixed_content = "from flask_wtf.csrf import CSRFProtect\n" + fixed_content
                logger.info("添加导入 flask_wtf.csrf 模块")
        
        # 修复2: 从flask_wtf.csrf导入CSRFProtect的问题
        if 'from flask_wtf.csrf import CSRFProtect' in fixed_content:
            logger.info("检测到导入flask_wtf.csrf.CSRFProtect的错误")
            fixed_content = fixed_content.replace(
                'from flask_wtf.csrf import CSRFProtect', 
                'from flask_wtf.csrf import CSRFProtect'
            )
            logger.info("修复导入 CSRFProtect 替代 CSRFProtect")
        
        # 修复3: 直接从app导入csrf的问题
        if 'from flask_wtf.csrf import CSRFProtect' in fixed_content:
            logger.info("检测到从app导入csrf的错误")
            fixed_content = fixed_content.replace(
                'from flask_wtf.csrf import CSRFProtect', 
                '# from flask_wtf.csrf import CSRFProtect - 已修复\nfrom flask_wtf.csrf import CSRFProtect\ncsrf = CSRFProtect()'
            )
            logger.info("创建本地csrf实例")
        
        # 修复4: 从app.utils.permissions导入permission_required的问题
        if 'from app.permissions import permission_required' in fixed_content:
            logger.info("检测到导入permission_required的错误")
            # 检查app/utils/permissions.py中是否存在该函数
            perm_file = 'app/utils/permissions.py'
            if os.path.exists(perm_file):
                with open(perm_file, 'r', encoding='utf-8') as f:
                    perm_content = f.read()
                if 'def permission_required' not in perm_content:
                    # 添加自定义权限装饰器
                    fixed_content = fixed_content.replace(
                        'from app.permissions import permission_required',
                        '# 自定义权限装饰器\nfrom functools import wraps\nfrom flask import abort, current_app\nfrom flask_login import current_user\n\ndef permission_required(permission):\n    def decorator(f):\n        @wraps(f)\n        def decorated_function(*args, **kwargs):\n            if not current_user.is_authenticated:\n                abort(403)\n            if current_user.role != "admin" and not hasattr(current_user, permission):\n                abort(403)\n            return f(*args, **kwargs)\n        return decorated_function\n    return decorator'
                    )
                    logger.info("添加自定义permission_required装饰器")
        
        # 写入修复后的内容
        if fixed_content != content:
            with open(api_file, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            logger.info(f"已修复并保存API文件 {api_file}")
            return True
        else:
            logger.info("API文件无需修复")
            return False
    
    except Exception as e:
        logger.error(f"修复API文件时出错: {e}")
        return False

if __name__ == "__main__":
    fix_api_imports() 
# -*- coding: utf-8 -*-

import os
import re
import shutil
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger('API修复')

def fix_api_imports(api_file='app/routes/api.py'):
    """修复API模块中的导入问题"""
    if not os.path.exists(api_file):
        logger.error(f"API文件不存在: {api_file}")
        return False
    
    # 创建备份
    backup_file = f"{api_file}.bak"
    if not os.path.exists(backup_file):
        shutil.copy2(api_file, backup_file)
        logger.info(f"已创建备份文件: {backup_file}")
    
    try:
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 修复常见的导入问题
        fixed_content = content
        
        # 修复1: 从flask导入csrf的问题
        if re.search(r'from\s+flask\s+import\s+(?:[^,\n]+,\s*)*csrf(?:,|$|\s)', fixed_content):
            logger.info("检测到导入flask.csrf的错误")
            fixed_content = re.sub(
                r'from\s+flask\s+import\s+([^,\n]*,\s*)*csrf(,|$|\s)',
                lambda m: m.group(0).replace('csrf', ''),
                fixed_content
            )
            # 添加正确的导入
            if 'from flask_wtf.csrf import CSRFProtect' not in fixed_content:
                fixed_content = "from flask_wtf.csrf import CSRFProtect\n" + fixed_content
                logger.info("添加导入 flask_wtf.csrf 模块")
        
        # 修复2: 从flask_wtf.csrf导入CSRFProtect的问题
        if 'from flask_wtf.csrf import CSRFProtect' in fixed_content:
            logger.info("检测到导入flask_wtf.csrf.CSRFProtect的错误")
            fixed_content = fixed_content.replace(
                'from flask_wtf.csrf import CSRFProtect', 
                'from flask_wtf.csrf import CSRFProtect'
            )
            logger.info("修复导入 CSRFProtect 替代 CSRFProtect")
        
        # 修复3: 直接从app导入csrf的问题
        if 'from flask_wtf.csrf import CSRFProtect' in fixed_content:
            logger.info("检测到从app导入csrf的错误")
            fixed_content = fixed_content.replace(
                'from flask_wtf.csrf import CSRFProtect', 
                '# from flask_wtf.csrf import CSRFProtect - 已修复\nfrom flask_wtf.csrf import CSRFProtect\ncsrf = CSRFProtect()'
            )
            logger.info("创建本地csrf实例")
        
        # 修复4: 从app.utils.permissions导入permission_required的问题
        if 'from app.permissions import permission_required' in fixed_content:
            logger.info("检测到导入permission_required的错误")
            # 检查app/utils/permissions.py中是否存在该函数
            perm_file = 'app/utils/permissions.py'
            if os.path.exists(perm_file):
                with open(perm_file, 'r', encoding='utf-8') as f:
                    perm_content = f.read()
                if 'def permission_required' not in perm_content:
                    # 添加自定义权限装饰器
                    fixed_content = fixed_content.replace(
                        'from app.permissions import permission_required',
                        '# 自定义权限装饰器\nfrom functools import wraps\nfrom flask import abort, current_app\nfrom flask_login import current_user\n\ndef permission_required(permission):\n    def decorator(f):\n        @wraps(f)\n        def decorated_function(*args, **kwargs):\n            if not current_user.is_authenticated:\n                abort(403)\n            if current_user.role != "admin" and not hasattr(current_user, permission):\n                abort(403)\n            return f(*args, **kwargs)\n        return decorated_function\n    return decorator'
                    )
                    logger.info("添加自定义permission_required装饰器")
        
        # 写入修复后的内容
        if fixed_content != content:
            with open(api_file, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            logger.info(f"已修复并保存API文件 {api_file}")
            return True
        else:
            logger.info("API文件无需修复")
            return False
    
    except Exception as e:
        logger.error(f"修复API文件时出错: {e}")
        return False

if __name__ == "__main__":
    fix_api_imports() 