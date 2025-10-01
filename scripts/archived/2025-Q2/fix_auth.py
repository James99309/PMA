#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import shutil
import logging
from app import create_app, db
from app.models.user import User

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger('认证修复')

def fix_user_is_active():
    """修复用户的is_active状态，确保login_user可以正常工作"""
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if admin:
            logger.info(f"找到admin用户 (ID: {admin.id})")
            
            # 检查当前is_active状态
            logger.info(f"当前is_active状态: {admin.is_active}")
            
            # 检查UserMixin中is_active的实现
            class_methods = dir(User)
            if 'is_active' in class_methods and callable(getattr(User, 'is_active', None)):
                logger.info("is_active被定义为方法而不是属性，检查UserMixin实现")
                
                # 添加方法覆盖is_active属性
                code_file = 'app/models/user.py'
                if not os.path.exists(f"{code_file}.bak"):
                    shutil.copy2(code_file, f"{code_file}.bak")
                    logger.info(f"已创建备份文件: {code_file}.bak")
                
                with open(code_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 添加get_is_active方法
                if 'def get_is_active(self)' not in content:
                    user_class_end = re.search(r'class User\(.*?\):(.*?)class', content, re.DOTALL)
                    if user_class_end:
                        # 在User类中最后添加方法
                        user_class_content = user_class_end.group(1)
                        # 找到类中最后一个方法
                        methods = re.findall(r'def ([a-zA-Z_]+)\(', user_class_content)
                        if methods:
                            last_method = methods[-1]
                            # 在最后一个方法后添加新方法
                            new_method = f"""
    @property
    def is_active(self):
        # 管理员(admin)默认允许登录，其他用户仍需验证is_active字段
        if self.role == 'admin':
            return True
        # 使用数据库中的is_active字段
        return bool(self._is_active)
"""
                            content = content.replace('class User(db.Model, UserMixin):', 'class User(db.Model, UserMixin):\n    _is_active = db.Column(db.Boolean, default=False, name="is_active")  # 重命名原is_active字段')
                            content = re.sub(r'is_active = db\.Column\(db\.Boolean, default=False\).*?(\n)', '', content)
                            
                            # 在最后一个方法后添加
                            pattern = rf'def {re.escape(last_method)}\(.*?\n(\s+).*?\n\n'
                            match = re.search(pattern, content, re.DOTALL)
                            if match:
                                indent = match.group(1)
                                replacement = match.group(0) + indent + new_method.replace('\n    ', '\n' + indent)
                                content = content.replace(match.group(0), replacement)
                                
                                with open(code_file, 'w', encoding='utf-8') as f:
                                    f.write(content)
                                logger.info("已添加is_active属性方法")
            
            # 无论如何都确保admin用户的is_active为True
            if hasattr(admin, '_is_active'):
                admin._is_active = True
            else:
                admin.is_active = True
            
            try:
                db.session.commit()
                logger.info("已激活admin用户账户")
                
                # 重新查询确认更改已生效
                admin = User.query.filter_by(username='admin').first()
                if hasattr(admin, 'is_active'):
                    if callable(admin.is_active):
                        logger.info(f"最终is_active状态: {admin.is_active()}")
                    else:
                        logger.info(f"最终is_active状态: {admin.is_active}")
                else:
                    logger.warning("找不到is_active属性")
                
                logger.info("登录认证修复完成")
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"激活用户时出错: {e}")
        else:
            logger.error("admin用户不存在")

def fix_auth_view():
    """修复auth视图中的登录处理"""
    auth_file = 'app/views/auth.py'
    if not os.path.exists(auth_file):
        logger.error(f"认证视图文件不存在: {auth_file}")
        return False
    
    # 创建备份
    if not os.path.exists(f"{auth_file}.bak"):
        shutil.copy2(auth_file, f"{auth_file}.bak")
        logger.info(f"已创建备份文件: {auth_file}.bak")
    
    try:
        with open(auth_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查登录逻辑是否考虑了is_active状态
        login_pattern = r'if user and user\.check_password\(password\):'
        if re.search(login_pattern, content):
            fixed_login_code = """if user and user.check_password(password):
            # 检查账户是否激活
            if hasattr(user, 'is_active'):
                is_active = user.is_active() if callable(user.is_active) else user.is_active
                if not is_active and user.role != 'admin':  # admin用户总是允许登录
                    flash('账户未激活，请联系管理员')
                    return render_template('auth/login.html', form=form)"""
            
            # 替换登录代码，增加账户激活状态检查
            new_content = re.sub(login_pattern, fixed_login_code, content)
            
            if new_content != content:
                with open(auth_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                logger.info(f"已修复认证视图: {auth_file}")
            else:
                logger.info("认证视图无需修复")
        else:
            logger.info("未找到需要修复的登录逻辑")
    
    except Exception as e:
        logger.error(f"修复认证视图时出错: {e}")

def main():
    """主函数"""
    logger.info("开始修复登录认证问题...")
    fix_user_is_active()
    fix_auth_view()
    
    logger.info("\n请重启Flask应用以应用所有修复。")

if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-

import os
import re
import shutil
import logging
from app import create_app, db
from app.models.user import User

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger('认证修复')

def fix_user_is_active():
    """修复用户的is_active状态，确保login_user可以正常工作"""
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if admin:
            logger.info(f"找到admin用户 (ID: {admin.id})")
            
            # 检查当前is_active状态
            logger.info(f"当前is_active状态: {admin.is_active}")
            
            # 检查UserMixin中is_active的实现
            class_methods = dir(User)
            if 'is_active' in class_methods and callable(getattr(User, 'is_active', None)):
                logger.info("is_active被定义为方法而不是属性，检查UserMixin实现")
                
                # 添加方法覆盖is_active属性
                code_file = 'app/models/user.py'
                if not os.path.exists(f"{code_file}.bak"):
                    shutil.copy2(code_file, f"{code_file}.bak")
                    logger.info(f"已创建备份文件: {code_file}.bak")
                
                with open(code_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 添加get_is_active方法
                if 'def get_is_active(self)' not in content:
                    user_class_end = re.search(r'class User\(.*?\):(.*?)class', content, re.DOTALL)
                    if user_class_end:
                        # 在User类中最后添加方法
                        user_class_content = user_class_end.group(1)
                        # 找到类中最后一个方法
                        methods = re.findall(r'def ([a-zA-Z_]+)\(', user_class_content)
                        if methods:
                            last_method = methods[-1]
                            # 在最后一个方法后添加新方法
                            new_method = f"""
    @property
    def is_active(self):
        # 管理员(admin)默认允许登录，其他用户仍需验证is_active字段
        if self.role == 'admin':
            return True
        # 使用数据库中的is_active字段
        return bool(self._is_active)
"""
                            content = content.replace('class User(db.Model, UserMixin):', 'class User(db.Model, UserMixin):\n    _is_active = db.Column(db.Boolean, default=False, name="is_active")  # 重命名原is_active字段')
                            content = re.sub(r'is_active = db\.Column\(db\.Boolean, default=False\).*?(\n)', '', content)
                            
                            # 在最后一个方法后添加
                            pattern = rf'def {re.escape(last_method)}\(.*?\n(\s+).*?\n\n'
                            match = re.search(pattern, content, re.DOTALL)
                            if match:
                                indent = match.group(1)
                                replacement = match.group(0) + indent + new_method.replace('\n    ', '\n' + indent)
                                content = content.replace(match.group(0), replacement)
                                
                                with open(code_file, 'w', encoding='utf-8') as f:
                                    f.write(content)
                                logger.info("已添加is_active属性方法")
            
            # 无论如何都确保admin用户的is_active为True
            if hasattr(admin, '_is_active'):
                admin._is_active = True
            else:
                admin.is_active = True
            
            try:
                db.session.commit()
                logger.info("已激活admin用户账户")
                
                # 重新查询确认更改已生效
                admin = User.query.filter_by(username='admin').first()
                if hasattr(admin, 'is_active'):
                    if callable(admin.is_active):
                        logger.info(f"最终is_active状态: {admin.is_active()}")
                    else:
                        logger.info(f"最终is_active状态: {admin.is_active}")
                else:
                    logger.warning("找不到is_active属性")
                
                logger.info("登录认证修复完成")
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"激活用户时出错: {e}")
        else:
            logger.error("admin用户不存在")

def fix_auth_view():
    """修复auth视图中的登录处理"""
    auth_file = 'app/views/auth.py'
    if not os.path.exists(auth_file):
        logger.error(f"认证视图文件不存在: {auth_file}")
        return False
    
    # 创建备份
    if not os.path.exists(f"{auth_file}.bak"):
        shutil.copy2(auth_file, f"{auth_file}.bak")
        logger.info(f"已创建备份文件: {auth_file}.bak")
    
    try:
        with open(auth_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查登录逻辑是否考虑了is_active状态
        login_pattern = r'if user and user\.check_password\(password\):'
        if re.search(login_pattern, content):
            fixed_login_code = """if user and user.check_password(password):
            # 检查账户是否激活
            if hasattr(user, 'is_active'):
                is_active = user.is_active() if callable(user.is_active) else user.is_active
                if not is_active and user.role != 'admin':  # admin用户总是允许登录
                    flash('账户未激活，请联系管理员')
                    return render_template('auth/login.html', form=form)"""
            
            # 替换登录代码，增加账户激活状态检查
            new_content = re.sub(login_pattern, fixed_login_code, content)
            
            if new_content != content:
                with open(auth_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                logger.info(f"已修复认证视图: {auth_file}")
            else:
                logger.info("认证视图无需修复")
        else:
            logger.info("未找到需要修复的登录逻辑")
    
    except Exception as e:
        logger.error(f"修复认证视图时出错: {e}")

def main():
    """主函数"""
    logger.info("开始修复登录认证问题...")
    fix_user_is_active()
    fix_auth_view()
    
    logger.info("\n请重启Flask应用以应用所有修复。")

if __name__ == "__main__":
    main() 