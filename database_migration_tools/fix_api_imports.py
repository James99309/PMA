#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API导入问题修复工具

用于解决Flask CSRF和权限导入错误：
1. 修复'from flask_wtf.csrf import CSRFProtect'错误
2. 修复'from app.permissions import permission_required'错误
"""

import os
import re
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api_fix.log')
    ]
)
logger = logging.getLogger('API修复')

def fix_csrf_import(file_path):
    """修复CSRF导入问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否存在问题导入
        if 'from flask_wtf.csrf import CSRFProtect' in content:
            logger.info(f"文件 {file_path} 中存在错误的CSRF导入")
            
            # 替换为正确的导入
            modified_content = content.replace(
                'from flask_wtf.csrf import CSRFProtect',
                'from flask_wtf.csrf import CSRFProtect'
            )
            
            # 替换其他相关代码
            modified_content = modified_content.replace(
                'csrf_protect', 
                'CSRFProtect'
            )
            
            modified_content = modified_content.replace(
                'from flask_wtf.csrf import CSRFProtect', 
                'from flask_wtf.csrf import CSRFProtect'
            )
            
            # 替换csrf函数调用
            modified_content = re.sub(
                r'csrf\.exempt', 
                'csrf_exempt', 
                modified_content
            )
            
            # 如果内容有变化，写回文件
            if content != modified_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                logger.info(f"已修复文件 {file_path} 中的CSRF导入问题")
                return True
        
        return False
    
    except Exception as e:
        logger.error(f"修复文件 {file_path} 中的CSRF导入问题时出错: {str(e)}")
        return False

def fix_permission_required_import(file_path):
    """修复权限导入问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否存在问题导入
        if 'from app.permissions import permission_required' in content:
            logger.info(f"文件 {file_path} 中存在错误的权限导入")
            
            # 创建权限函数(如果不存在)
            permissions_file = Path('app/utils/permissions.py')
            if permissions_file.exists():
                with open(permissions_file, 'r', encoding='utf-8') as f:
                    permissions_content = f.read()
                
                # 如果权限函数不存在，添加它
                if 'def permission_required' not in permissions_content:
                    logger.info("权限函数不存在，创建它")
                    with open(permissions_file, 'a', encoding='utf-8') as f:
                        f.write("""
# 权限装饰器
from functools import wraps
from flask import abort, g, current_app, request
from flask_login import current_user

def permission_required(permission):
    \"\"\"检查用户是否拥有指定的权限\"\"\"
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 如果用户未登录或无权限，返回403错误
            if not current_user.is_authenticated or not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
""")
                    logger.info("已添加权限函数")
                    return True
            
            return False
        
        return False
    
    except Exception as e:
        logger.error(f"修复文件 {file_path} 中的权限导入问题时出错: {str(e)}")
        return False

def fix_api_routes_file():
    """修复API路由文件"""
    file_path = Path('app/routes/api.py')
    
    if not file_path.exists():
        logger.warning(f"文件不存在: {file_path}")
        return False
    
    logger.info(f"开始修复API路由文件: {file_path}")
    
    csrf_fixed = fix_csrf_import(file_path)
    permission_fixed = fix_permission_required_import(file_path)
    
    return csrf_fixed or permission_fixed

def scan_and_fix_all_py_files():
    """扫描并修复所有Python文件"""
    app_dir = Path('app')
    
    if not app_dir.exists():
        logger.warning(f"应用目录不存在: {app_dir}")
        return
    
    fixed_count = 0
    error_count = 0
    
    for py_file in app_dir.glob('**/*.py'):
        try:
            logger.info(f"检查文件: {py_file}")
            fixed_csrf = fix_csrf_import(py_file)
            fixed_permission = fix_permission_required_import(py_file)
            
            if fixed_csrf or fixed_permission:
                fixed_count += 1
        except Exception as e:
            logger.error(f"处理文件 {py_file} 时出错: {str(e)}")
            error_count += 1
    
    logger.info(f"API修复完成. 已修复: {fixed_count}, 错误: {error_count}")

def check_for_missing_permissions():
    """检查是否缺少权限工具文件"""
    permissions_file = Path('app/utils/permissions.py')
    
    if not permissions_file.exists():
        logger.warning("权限文件不存在，创建它")
        
        # 确保目录存在
        permissions_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 创建权限文件
        with open(permissions_file, 'w', encoding='utf-8') as f:
            f.write("""# -*- coding: utf-8 -*-
\"\"\"
权限管理工具

提供权限检查和装饰器功能
\"\"\"

from functools import wraps
from flask import abort, g, current_app, request
from flask_login import current_user

# 权限常量
class Permission:
    GENERAL = 0x01      # 一般权限，登录用户默认拥有
    ADMIN = 0x80        # 管理员权限
    
    @staticmethod
    def get_all_permissions():
        \"\"\"获取所有权限\"\"\"
        return {
            'GENERAL': Permission.GENERAL, 
            'ADMIN': Permission.ADMIN
        }

def permission_required(permission):
    \"\"\"检查用户是否拥有指定的权限\"\"\"
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 如果用户未登录或无权限，返回403错误
            if not current_user.is_authenticated or not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    \"\"\"检查用户是否拥有管理员权限\"\"\"
    return permission_required(Permission.ADMIN)(f)
""")
        logger.info("已创建权限文件")
        return True
    
    return False

def main():
    """主函数"""
    logger.info("=== 开始修复API导入问题 ===")
    
    # 检查权限文件
    check_for_missing_permissions()
    
    # 修复API路由文件
    fix_api_routes_file()
    
    # 扫描并修复所有Python文件
    scan_and_fix_all_py_files()
    
    logger.info("=== API修复完成 ===")

if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-
"""
API导入问题修复工具

用于解决Flask CSRF和权限导入错误：
1. 修复'from flask_wtf.csrf import CSRFProtect'错误
2. 修复'from app.permissions import permission_required'错误
"""

import os
import re
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api_fix.log')
    ]
)
logger = logging.getLogger('API修复')

def fix_csrf_import(file_path):
    """修复CSRF导入问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否存在问题导入
        if 'from flask_wtf.csrf import CSRFProtect' in content:
            logger.info(f"文件 {file_path} 中存在错误的CSRF导入")
            
            # 替换为正确的导入
            modified_content = content.replace(
                'from flask_wtf.csrf import CSRFProtect',
                'from flask_wtf.csrf import CSRFProtect'
            )
            
            # 替换其他相关代码
            modified_content = modified_content.replace(
                'csrf_protect', 
                'CSRFProtect'
            )
            
            modified_content = modified_content.replace(
                'from flask_wtf.csrf import CSRFProtect', 
                'from flask_wtf.csrf import CSRFProtect'
            )
            
            # 替换csrf函数调用
            modified_content = re.sub(
                r'csrf\.exempt', 
                'csrf_exempt', 
                modified_content
            )
            
            # 如果内容有变化，写回文件
            if content != modified_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                logger.info(f"已修复文件 {file_path} 中的CSRF导入问题")
                return True
        
        return False
    
    except Exception as e:
        logger.error(f"修复文件 {file_path} 中的CSRF导入问题时出错: {str(e)}")
        return False

def fix_permission_required_import(file_path):
    """修复权限导入问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否存在问题导入
        if 'from app.permissions import permission_required' in content:
            logger.info(f"文件 {file_path} 中存在错误的权限导入")
            
            # 创建权限函数(如果不存在)
            permissions_file = Path('app/utils/permissions.py')
            if permissions_file.exists():
                with open(permissions_file, 'r', encoding='utf-8') as f:
                    permissions_content = f.read()
                
                # 如果权限函数不存在，添加它
                if 'def permission_required' not in permissions_content:
                    logger.info("权限函数不存在，创建它")
                    with open(permissions_file, 'a', encoding='utf-8') as f:
                        f.write("""
# 权限装饰器
from functools import wraps
from flask import abort, g, current_app, request
from flask_login import current_user

def permission_required(permission):
    \"\"\"检查用户是否拥有指定的权限\"\"\"
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 如果用户未登录或无权限，返回403错误
            if not current_user.is_authenticated or not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
""")
                    logger.info("已添加权限函数")
                    return True
            
            return False
        
        return False
    
    except Exception as e:
        logger.error(f"修复文件 {file_path} 中的权限导入问题时出错: {str(e)}")
        return False

def fix_api_routes_file():
    """修复API路由文件"""
    file_path = Path('app/routes/api.py')
    
    if not file_path.exists():
        logger.warning(f"文件不存在: {file_path}")
        return False
    
    logger.info(f"开始修复API路由文件: {file_path}")
    
    csrf_fixed = fix_csrf_import(file_path)
    permission_fixed = fix_permission_required_import(file_path)
    
    return csrf_fixed or permission_fixed

def scan_and_fix_all_py_files():
    """扫描并修复所有Python文件"""
    app_dir = Path('app')
    
    if not app_dir.exists():
        logger.warning(f"应用目录不存在: {app_dir}")
        return
    
    fixed_count = 0
    error_count = 0
    
    for py_file in app_dir.glob('**/*.py'):
        try:
            logger.info(f"检查文件: {py_file}")
            fixed_csrf = fix_csrf_import(py_file)
            fixed_permission = fix_permission_required_import(py_file)
            
            if fixed_csrf or fixed_permission:
                fixed_count += 1
        except Exception as e:
            logger.error(f"处理文件 {py_file} 时出错: {str(e)}")
            error_count += 1
    
    logger.info(f"API修复完成. 已修复: {fixed_count}, 错误: {error_count}")

def check_for_missing_permissions():
    """检查是否缺少权限工具文件"""
    permissions_file = Path('app/utils/permissions.py')
    
    if not permissions_file.exists():
        logger.warning("权限文件不存在，创建它")
        
        # 确保目录存在
        permissions_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 创建权限文件
        with open(permissions_file, 'w', encoding='utf-8') as f:
            f.write("""# -*- coding: utf-8 -*-
\"\"\"
权限管理工具

提供权限检查和装饰器功能
\"\"\"

from functools import wraps
from flask import abort, g, current_app, request
from flask_login import current_user

# 权限常量
class Permission:
    GENERAL = 0x01      # 一般权限，登录用户默认拥有
    ADMIN = 0x80        # 管理员权限
    
    @staticmethod
    def get_all_permissions():
        \"\"\"获取所有权限\"\"\"
        return {
            'GENERAL': Permission.GENERAL, 
            'ADMIN': Permission.ADMIN
        }

def permission_required(permission):
    \"\"\"检查用户是否拥有指定的权限\"\"\"
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 如果用户未登录或无权限，返回403错误
            if not current_user.is_authenticated or not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    \"\"\"检查用户是否拥有管理员权限\"\"\"
    return permission_required(Permission.ADMIN)(f)
""")
        logger.info("已创建权限文件")
        return True
    
    return False

def main():
    """主函数"""
    logger.info("=== 开始修复API导入问题 ===")
    
    # 检查权限文件
    check_for_missing_permissions()
    
    # 修复API路由文件
    fix_api_routes_file()
    
    # 扫描并修复所有Python文件
    scan_and_fix_all_py_files()
    
    logger.info("=== API修复完成 ===")

if __name__ == "__main__":
    main() 
 
 
# -*- coding: utf-8 -*-
"""
API导入问题修复工具

用于解决Flask CSRF和权限导入错误：
1. 修复'from flask_wtf.csrf import CSRFProtect'错误
2. 修复'from app.permissions import permission_required'错误
"""

import os
import re
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api_fix.log')
    ]
)
logger = logging.getLogger('API修复')

def fix_csrf_import(file_path):
    """修复CSRF导入问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否存在问题导入
        if 'from flask_wtf.csrf import CSRFProtect' in content:
            logger.info(f"文件 {file_path} 中存在错误的CSRF导入")
            
            # 替换为正确的导入
            modified_content = content.replace(
                'from flask_wtf.csrf import CSRFProtect',
                'from flask_wtf.csrf import CSRFProtect'
            )
            
            # 替换其他相关代码
            modified_content = modified_content.replace(
                'csrf_protect', 
                'CSRFProtect'
            )
            
            modified_content = modified_content.replace(
                'from flask_wtf.csrf import CSRFProtect', 
                'from flask_wtf.csrf import CSRFProtect'
            )
            
            # 替换csrf函数调用
            modified_content = re.sub(
                r'csrf\.exempt', 
                'csrf_exempt', 
                modified_content
            )
            
            # 如果内容有变化，写回文件
            if content != modified_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                logger.info(f"已修复文件 {file_path} 中的CSRF导入问题")
                return True
        
        return False
    
    except Exception as e:
        logger.error(f"修复文件 {file_path} 中的CSRF导入问题时出错: {str(e)}")
        return False

def fix_permission_required_import(file_path):
    """修复权限导入问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否存在问题导入
        if 'from app.permissions import permission_required' in content:
            logger.info(f"文件 {file_path} 中存在错误的权限导入")
            
            # 创建权限函数(如果不存在)
            permissions_file = Path('app/utils/permissions.py')
            if permissions_file.exists():
                with open(permissions_file, 'r', encoding='utf-8') as f:
                    permissions_content = f.read()
                
                # 如果权限函数不存在，添加它
                if 'def permission_required' not in permissions_content:
                    logger.info("权限函数不存在，创建它")
                    with open(permissions_file, 'a', encoding='utf-8') as f:
                        f.write("""
# 权限装饰器
from functools import wraps
from flask import abort, g, current_app, request
from flask_login import current_user

def permission_required(permission):
    \"\"\"检查用户是否拥有指定的权限\"\"\"
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 如果用户未登录或无权限，返回403错误
            if not current_user.is_authenticated or not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
""")
                    logger.info("已添加权限函数")
                    return True
            
            return False
        
        return False
    
    except Exception as e:
        logger.error(f"修复文件 {file_path} 中的权限导入问题时出错: {str(e)}")
        return False

def fix_api_routes_file():
    """修复API路由文件"""
    file_path = Path('app/routes/api.py')
    
    if not file_path.exists():
        logger.warning(f"文件不存在: {file_path}")
        return False
    
    logger.info(f"开始修复API路由文件: {file_path}")
    
    csrf_fixed = fix_csrf_import(file_path)
    permission_fixed = fix_permission_required_import(file_path)
    
    return csrf_fixed or permission_fixed

def scan_and_fix_all_py_files():
    """扫描并修复所有Python文件"""
    app_dir = Path('app')
    
    if not app_dir.exists():
        logger.warning(f"应用目录不存在: {app_dir}")
        return
    
    fixed_count = 0
    error_count = 0
    
    for py_file in app_dir.glob('**/*.py'):
        try:
            logger.info(f"检查文件: {py_file}")
            fixed_csrf = fix_csrf_import(py_file)
            fixed_permission = fix_permission_required_import(py_file)
            
            if fixed_csrf or fixed_permission:
                fixed_count += 1
        except Exception as e:
            logger.error(f"处理文件 {py_file} 时出错: {str(e)}")
            error_count += 1
    
    logger.info(f"API修复完成. 已修复: {fixed_count}, 错误: {error_count}")

def check_for_missing_permissions():
    """检查是否缺少权限工具文件"""
    permissions_file = Path('app/utils/permissions.py')
    
    if not permissions_file.exists():
        logger.warning("权限文件不存在，创建它")
        
        # 确保目录存在
        permissions_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 创建权限文件
        with open(permissions_file, 'w', encoding='utf-8') as f:
            f.write("""# -*- coding: utf-8 -*-
\"\"\"
权限管理工具

提供权限检查和装饰器功能
\"\"\"

from functools import wraps
from flask import abort, g, current_app, request
from flask_login import current_user

# 权限常量
class Permission:
    GENERAL = 0x01      # 一般权限，登录用户默认拥有
    ADMIN = 0x80        # 管理员权限
    
    @staticmethod
    def get_all_permissions():
        \"\"\"获取所有权限\"\"\"
        return {
            'GENERAL': Permission.GENERAL, 
            'ADMIN': Permission.ADMIN
        }

def permission_required(permission):
    \"\"\"检查用户是否拥有指定的权限\"\"\"
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 如果用户未登录或无权限，返回403错误
            if not current_user.is_authenticated or not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    \"\"\"检查用户是否拥有管理员权限\"\"\"
    return permission_required(Permission.ADMIN)(f)
""")
        logger.info("已创建权限文件")
        return True
    
    return False

def main():
    """主函数"""
    logger.info("=== 开始修复API导入问题 ===")
    
    # 检查权限文件
    check_for_missing_permissions()
    
    # 修复API路由文件
    fix_api_routes_file()
    
    # 扫描并修复所有Python文件
    scan_and_fix_all_py_files()
    
    logger.info("=== API修复完成 ===")

if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-
"""
API导入问题修复工具

用于解决Flask CSRF和权限导入错误：
1. 修复'from flask_wtf.csrf import CSRFProtect'错误
2. 修复'from app.permissions import permission_required'错误
"""

import os
import re
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api_fix.log')
    ]
)
logger = logging.getLogger('API修复')

def fix_csrf_import(file_path):
    """修复CSRF导入问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否存在问题导入
        if 'from flask_wtf.csrf import CSRFProtect' in content:
            logger.info(f"文件 {file_path} 中存在错误的CSRF导入")
            
            # 替换为正确的导入
            modified_content = content.replace(
                'from flask_wtf.csrf import CSRFProtect',
                'from flask_wtf.csrf import CSRFProtect'
            )
            
            # 替换其他相关代码
            modified_content = modified_content.replace(
                'csrf_protect', 
                'CSRFProtect'
            )
            
            modified_content = modified_content.replace(
                'from flask_wtf.csrf import CSRFProtect', 
                'from flask_wtf.csrf import CSRFProtect'
            )
            
            # 替换csrf函数调用
            modified_content = re.sub(
                r'csrf\.exempt', 
                'csrf_exempt', 
                modified_content
            )
            
            # 如果内容有变化，写回文件
            if content != modified_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                logger.info(f"已修复文件 {file_path} 中的CSRF导入问题")
                return True
        
        return False
    
    except Exception as e:
        logger.error(f"修复文件 {file_path} 中的CSRF导入问题时出错: {str(e)}")
        return False

def fix_permission_required_import(file_path):
    """修复权限导入问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否存在问题导入
        if 'from app.permissions import permission_required' in content:
            logger.info(f"文件 {file_path} 中存在错误的权限导入")
            
            # 创建权限函数(如果不存在)
            permissions_file = Path('app/utils/permissions.py')
            if permissions_file.exists():
                with open(permissions_file, 'r', encoding='utf-8') as f:
                    permissions_content = f.read()
                
                # 如果权限函数不存在，添加它
                if 'def permission_required' not in permissions_content:
                    logger.info("权限函数不存在，创建它")
                    with open(permissions_file, 'a', encoding='utf-8') as f:
                        f.write("""
# 权限装饰器
from functools import wraps
from flask import abort, g, current_app, request
from flask_login import current_user

def permission_required(permission):
    \"\"\"检查用户是否拥有指定的权限\"\"\"
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 如果用户未登录或无权限，返回403错误
            if not current_user.is_authenticated or not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
""")
                    logger.info("已添加权限函数")
                    return True
            
            return False
        
        return False
    
    except Exception as e:
        logger.error(f"修复文件 {file_path} 中的权限导入问题时出错: {str(e)}")
        return False

def fix_api_routes_file():
    """修复API路由文件"""
    file_path = Path('app/routes/api.py')
    
    if not file_path.exists():
        logger.warning(f"文件不存在: {file_path}")
        return False
    
    logger.info(f"开始修复API路由文件: {file_path}")
    
    csrf_fixed = fix_csrf_import(file_path)
    permission_fixed = fix_permission_required_import(file_path)
    
    return csrf_fixed or permission_fixed

def scan_and_fix_all_py_files():
    """扫描并修复所有Python文件"""
    app_dir = Path('app')
    
    if not app_dir.exists():
        logger.warning(f"应用目录不存在: {app_dir}")
        return
    
    fixed_count = 0
    error_count = 0
    
    for py_file in app_dir.glob('**/*.py'):
        try:
            logger.info(f"检查文件: {py_file}")
            fixed_csrf = fix_csrf_import(py_file)
            fixed_permission = fix_permission_required_import(py_file)
            
            if fixed_csrf or fixed_permission:
                fixed_count += 1
        except Exception as e:
            logger.error(f"处理文件 {py_file} 时出错: {str(e)}")
            error_count += 1
    
    logger.info(f"API修复完成. 已修复: {fixed_count}, 错误: {error_count}")

def check_for_missing_permissions():
    """检查是否缺少权限工具文件"""
    permissions_file = Path('app/utils/permissions.py')
    
    if not permissions_file.exists():
        logger.warning("权限文件不存在，创建它")
        
        # 确保目录存在
        permissions_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 创建权限文件
        with open(permissions_file, 'w', encoding='utf-8') as f:
            f.write("""# -*- coding: utf-8 -*-
\"\"\"
权限管理工具

提供权限检查和装饰器功能
\"\"\"

from functools import wraps
from flask import abort, g, current_app, request
from flask_login import current_user

# 权限常量
class Permission:
    GENERAL = 0x01      # 一般权限，登录用户默认拥有
    ADMIN = 0x80        # 管理员权限
    
    @staticmethod
    def get_all_permissions():
        \"\"\"获取所有权限\"\"\"
        return {
            'GENERAL': Permission.GENERAL, 
            'ADMIN': Permission.ADMIN
        }

def permission_required(permission):
    \"\"\"检查用户是否拥有指定的权限\"\"\"
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 如果用户未登录或无权限，返回403错误
            if not current_user.is_authenticated or not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    \"\"\"检查用户是否拥有管理员权限\"\"\"
    return permission_required(Permission.ADMIN)(f)
""")
        logger.info("已创建权限文件")
        return True
    
    return False

def main():
    """主函数"""
    logger.info("=== 开始修复API导入问题 ===")
    
    # 检查权限文件
    check_for_missing_permissions()
    
    # 修复API路由文件
    fix_api_routes_file()
    
    # 扫描并修复所有Python文件
    scan_and_fix_all_py_files()
    
    logger.info("=== API修复完成 ===")

if __name__ == "__main__":
    main() 
 
 