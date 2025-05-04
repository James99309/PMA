#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复Render环境中产品模块和用户模块的问题

此脚本修复以下问题：
1. 产品模块的权限错误 - 添加缺失的product_view权限
2. 用户模块的JSON解析错误
3. 其他可能的渲染问题
"""

import os
import re
import json
import logging
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('render_permissions_fixes.log')
    ]
)
logger = logging.getLogger(__name__)

def fix_product_permissions():
    """修复产品模块权限问题"""
    permissions_file = "app/permissions.py"
    
    if not os.path.exists(permissions_file):
        logger.error(f"找不到文件: {permissions_file}")
        return False
    
    with open(permissions_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    modified = False
    
    # 检查是否已经存在PRODUCT_VIEW权限
    if "PRODUCT_VIEW = 'product_view'" not in content:
        # 找到Permissions类定义的位置
        permissions_class_match = re.search(r'class Permissions:[^\}]*?\n', content, re.DOTALL)
        if permissions_class_match:
            # 在Permissions类中找到合适的位置添加PRODUCT_VIEW权限
            product_section_match = re.search(r'# 产品.*?相关权限', content)
            if product_section_match:
                # 如果找到产品相关权限注释，在该注释下添加PRODUCT_VIEW
                product_section_pos = product_section_match.end()
                # 寻找下一行的位置
                next_line_pos = content.find('\n', product_section_pos)
                if next_line_pos > 0:
                    # 在当前产品权限部分的第一行后插入PRODUCT_VIEW
                    content = content[:next_line_pos+1] + "    PRODUCT_VIEW = 'product_view'\n" + content[next_line_pos+1:]
                    logger.info("已添加PRODUCT_VIEW权限到产品权限部分")
                    modified = True
            else:
                # 如果没有找到产品相关权限注释，在类定义后添加PRODUCT_VIEW
                class_end = permissions_class_match.end()
                content = content[:class_end] + "\n    # 产品相关权限\n    PRODUCT_VIEW = 'product_view'\n" + content[class_end:]
                logger.info("已添加PRODUCT_VIEW权限和产品权限注释块")
                modified = True
        
        # 检查ROLE_PERMISSIONS映射是否包含新的PRODUCT_VIEW权限
        role_permissions_match = re.search(r'ROLE_PERMISSIONS\s*=\s*{[^}]*}', content, re.DOTALL)
        if role_permissions_match and modified:
            role_permissions = role_permissions_match.group(0)
            
            # 为每个角色添加PRODUCT_VIEW权限
            if "Permissions.PRODUCT_VIEW" not in role_permissions:
                # 为管理员添加权限
                admin_pattern = r'(\'admin\':\s*\[[^\]]*)'
                if re.search(admin_pattern, role_permissions):
                    content = re.sub(admin_pattern, r'\1, Permissions.PRODUCT_VIEW', content)
                
                # 为其他角色添加权限
                sales_pattern = r'(\'sales\':\s*\[[^\]]*)'
                if re.search(sales_pattern, role_permissions):
                    content = re.sub(sales_pattern, r'\1, Permissions.PRODUCT_VIEW', content)
                
                # 为产品经理添加权限
                product_manager_pattern = r'(\'product_manager\':\s*\[[^\]]*)'
                if re.search(product_manager_pattern, role_permissions):
                    content = re.sub(product_manager_pattern, r'\1, Permissions.PRODUCT_VIEW', content)
                
                # 为解决方案经理添加权限
                solution_manager_pattern = r'(\'solution_manager\':\s*\[[^\]]*)'
                if re.search(solution_manager_pattern, role_permissions):
                    content = re.sub(solution_manager_pattern, r'\1, Permissions.PRODUCT_VIEW', content)
                
                # 为普通用户添加权限
                user_pattern = r'(\'user\':\s*\[[^\]]*)'
                if re.search(user_pattern, role_permissions):
                    content = re.sub(user_pattern, r'\1, Permissions.PRODUCT_VIEW', content)
                
                logger.info("已为各角色添加PRODUCT_VIEW权限")
                modified = True
    
    # 保存修改
    if modified:
        with open(permissions_file, 'w', encoding='utf-8') as file:
            file.write(content)
        logger.info(f"成功修复产品模块权限问题: {permissions_file}")
        return True
    else:
        logger.info(f"产品模块权限已经存在，无需修复: {permissions_file}")
        return False

def fix_user_json_error():
    """修复用户模块的JSON解析错误"""
    user_views_file = "app/views/user.py"
    
    if not os.path.exists(user_views_file):
        logger.error(f"找不到文件: {user_views_file}")
        return False
    
    with open(user_views_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    modified = False
    
    # 查找可能导致JSON解析错误的代码
    json_parse_pattern = r'(json\.loads\([^)]+\))'
    json_parse_matches = re.finditer(json_parse_pattern, content)
    
    for match in json_parse_matches:
        json_parse_code = match.group(1)
        # 添加错误处理
        if "try:" not in json_parse_code and "except" not in json_parse_code:
            # 替换为带有错误处理的代码
            new_code = f"""try:
        {json_parse_code}
    except json.JSONDecodeError as e:
        current_app.logger.error(f"JSON解析错误: {{str(e)}}")
        return []  # 返回空列表以防止进一步的错误"""
            
            content = content.replace(json_parse_code, new_code)
            modified = True
            logger.info(f"已修复JSON解析代码: {json_parse_code}")
    
    # 保存修改
    if modified:
        with open(user_views_file, 'w', encoding='utf-8') as file:
            file.write(content)
        logger.info(f"成功修复用户模块JSON解析错误: {user_views_file}")
        return True
    else:
        logger.info(f"未发现需要修复的JSON解析代码: {user_views_file}")
        return False

def fix_product_routes():
    """修复产品路由相关问题"""
    routes_file = "app/routes/product.py"
    
    if not os.path.exists(routes_file):
        logger.error(f"找不到文件: {routes_file}")
        return False
    
    with open(routes_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    modified = False
    
    # 检查权限装饰器是否正确
    permission_pattern = r'@permission_required\(\'product\', \'view\'\)'
    permission_decorator_exists = re.search(permission_pattern, content) is not None
    
    if not permission_decorator_exists:
        # 在每个产品路由上添加正确的权限装饰器
        route_pattern = r'(@product_bp\.route.*?\n)(?!@permission_required)'
        route_matches = re.finditer(route_pattern, content)
        
        for match in route_matches:
            route_decorator = match.group(1)
            # 添加权限装饰器
            new_code = f"{route_decorator}@permission_required('product', 'view')\n"
            content = content.replace(route_decorator, new_code)
            modified = True
            logger.info(f"已添加产品视图权限装饰器到路由: {route_decorator.strip()}")
    
    # 保存修改
    if modified:
        with open(routes_file, 'w', encoding='utf-8') as file:
            file.write(content)
        logger.info(f"成功修复产品路由权限: {routes_file}")
        return True
    else:
        logger.info(f"产品路由权限已经正确设置: {routes_file}")
        return False

def main():
    """运行所有修复函数"""
    logger.info("开始修复Render环境中的产品和用户模块问题...")
    
    # 1. 修复产品模块权限问题
    permissions_fixed = fix_product_permissions()
    if permissions_fixed:
        logger.info("成功修复产品模块权限问题")
    else:
        logger.info("产品模块权限问题检查完成，未发现需要修复的地方")
    
    # 2. 修复用户模块JSON解析错误
    json_fixed = fix_user_json_error()
    if json_fixed:
        logger.info("成功修复用户模块JSON解析错误")
    else:
        logger.info("用户模块JSON解析错误检查完成，未发现需要修复的地方")
    
    # 3. 修复产品路由相关问题
    routes_fixed = fix_product_routes()
    if routes_fixed:
        logger.info("成功修复产品路由相关问题")
    else:
        logger.info("产品路由相关问题检查完成，未发现需要修复的地方")
    
    logger.info("所有修复操作已完成，请重新部署应用")

if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-
"""
修复Render环境中产品模块和用户模块的问题

此脚本修复以下问题：
1. 产品模块的权限错误 - 添加缺失的product_view权限
2. 用户模块的JSON解析错误
3. 其他可能的渲染问题
"""

import os
import re
import json
import logging
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('render_permissions_fixes.log')
    ]
)
logger = logging.getLogger(__name__)

def fix_product_permissions():
    """修复产品模块权限问题"""
    permissions_file = "app/permissions.py"
    
    if not os.path.exists(permissions_file):
        logger.error(f"找不到文件: {permissions_file}")
        return False
    
    with open(permissions_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    modified = False
    
    # 检查是否已经存在PRODUCT_VIEW权限
    if "PRODUCT_VIEW = 'product_view'" not in content:
        # 找到Permissions类定义的位置
        permissions_class_match = re.search(r'class Permissions:[^\}]*?\n', content, re.DOTALL)
        if permissions_class_match:
            # 在Permissions类中找到合适的位置添加PRODUCT_VIEW权限
            product_section_match = re.search(r'# 产品.*?相关权限', content)
            if product_section_match:
                # 如果找到产品相关权限注释，在该注释下添加PRODUCT_VIEW
                product_section_pos = product_section_match.end()
                # 寻找下一行的位置
                next_line_pos = content.find('\n', product_section_pos)
                if next_line_pos > 0:
                    # 在当前产品权限部分的第一行后插入PRODUCT_VIEW
                    content = content[:next_line_pos+1] + "    PRODUCT_VIEW = 'product_view'\n" + content[next_line_pos+1:]
                    logger.info("已添加PRODUCT_VIEW权限到产品权限部分")
                    modified = True
            else:
                # 如果没有找到产品相关权限注释，在类定义后添加PRODUCT_VIEW
                class_end = permissions_class_match.end()
                content = content[:class_end] + "\n    # 产品相关权限\n    PRODUCT_VIEW = 'product_view'\n" + content[class_end:]
                logger.info("已添加PRODUCT_VIEW权限和产品权限注释块")
                modified = True
        
        # 检查ROLE_PERMISSIONS映射是否包含新的PRODUCT_VIEW权限
        role_permissions_match = re.search(r'ROLE_PERMISSIONS\s*=\s*{[^}]*}', content, re.DOTALL)
        if role_permissions_match and modified:
            role_permissions = role_permissions_match.group(0)
            
            # 为每个角色添加PRODUCT_VIEW权限
            if "Permissions.PRODUCT_VIEW" not in role_permissions:
                # 为管理员添加权限
                admin_pattern = r'(\'admin\':\s*\[[^\]]*)'
                if re.search(admin_pattern, role_permissions):
                    content = re.sub(admin_pattern, r'\1, Permissions.PRODUCT_VIEW', content)
                
                # 为其他角色添加权限
                sales_pattern = r'(\'sales\':\s*\[[^\]]*)'
                if re.search(sales_pattern, role_permissions):
                    content = re.sub(sales_pattern, r'\1, Permissions.PRODUCT_VIEW', content)
                
                # 为产品经理添加权限
                product_manager_pattern = r'(\'product_manager\':\s*\[[^\]]*)'
                if re.search(product_manager_pattern, role_permissions):
                    content = re.sub(product_manager_pattern, r'\1, Permissions.PRODUCT_VIEW', content)
                
                # 为解决方案经理添加权限
                solution_manager_pattern = r'(\'solution_manager\':\s*\[[^\]]*)'
                if re.search(solution_manager_pattern, role_permissions):
                    content = re.sub(solution_manager_pattern, r'\1, Permissions.PRODUCT_VIEW', content)
                
                # 为普通用户添加权限
                user_pattern = r'(\'user\':\s*\[[^\]]*)'
                if re.search(user_pattern, role_permissions):
                    content = re.sub(user_pattern, r'\1, Permissions.PRODUCT_VIEW', content)
                
                logger.info("已为各角色添加PRODUCT_VIEW权限")
                modified = True
    
    # 保存修改
    if modified:
        with open(permissions_file, 'w', encoding='utf-8') as file:
            file.write(content)
        logger.info(f"成功修复产品模块权限问题: {permissions_file}")
        return True
    else:
        logger.info(f"产品模块权限已经存在，无需修复: {permissions_file}")
        return False

def fix_user_json_error():
    """修复用户模块的JSON解析错误"""
    user_views_file = "app/views/user.py"
    
    if not os.path.exists(user_views_file):
        logger.error(f"找不到文件: {user_views_file}")
        return False
    
    with open(user_views_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    modified = False
    
    # 查找可能导致JSON解析错误的代码
    json_parse_pattern = r'(json\.loads\([^)]+\))'
    json_parse_matches = re.finditer(json_parse_pattern, content)
    
    for match in json_parse_matches:
        json_parse_code = match.group(1)
        # 添加错误处理
        if "try:" not in json_parse_code and "except" not in json_parse_code:
            # 替换为带有错误处理的代码
            new_code = f"""try:
        {json_parse_code}
    except json.JSONDecodeError as e:
        current_app.logger.error(f"JSON解析错误: {{str(e)}}")
        return []  # 返回空列表以防止进一步的错误"""
            
            content = content.replace(json_parse_code, new_code)
            modified = True
            logger.info(f"已修复JSON解析代码: {json_parse_code}")
    
    # 保存修改
    if modified:
        with open(user_views_file, 'w', encoding='utf-8') as file:
            file.write(content)
        logger.info(f"成功修复用户模块JSON解析错误: {user_views_file}")
        return True
    else:
        logger.info(f"未发现需要修复的JSON解析代码: {user_views_file}")
        return False

def fix_product_routes():
    """修复产品路由相关问题"""
    routes_file = "app/routes/product.py"
    
    if not os.path.exists(routes_file):
        logger.error(f"找不到文件: {routes_file}")
        return False
    
    with open(routes_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    modified = False
    
    # 检查权限装饰器是否正确
    permission_pattern = r'@permission_required\(\'product\', \'view\'\)'
    permission_decorator_exists = re.search(permission_pattern, content) is not None
    
    if not permission_decorator_exists:
        # 在每个产品路由上添加正确的权限装饰器
        route_pattern = r'(@product_bp\.route.*?\n)(?!@permission_required)'
        route_matches = re.finditer(route_pattern, content)
        
        for match in route_matches:
            route_decorator = match.group(1)
            # 添加权限装饰器
            new_code = f"{route_decorator}@permission_required('product', 'view')\n"
            content = content.replace(route_decorator, new_code)
            modified = True
            logger.info(f"已添加产品视图权限装饰器到路由: {route_decorator.strip()}")
    
    # 保存修改
    if modified:
        with open(routes_file, 'w', encoding='utf-8') as file:
            file.write(content)
        logger.info(f"成功修复产品路由权限: {routes_file}")
        return True
    else:
        logger.info(f"产品路由权限已经正确设置: {routes_file}")
        return False

def main():
    """运行所有修复函数"""
    logger.info("开始修复Render环境中的产品和用户模块问题...")
    
    # 1. 修复产品模块权限问题
    permissions_fixed = fix_product_permissions()
    if permissions_fixed:
        logger.info("成功修复产品模块权限问题")
    else:
        logger.info("产品模块权限问题检查完成，未发现需要修复的地方")
    
    # 2. 修复用户模块JSON解析错误
    json_fixed = fix_user_json_error()
    if json_fixed:
        logger.info("成功修复用户模块JSON解析错误")
    else:
        logger.info("用户模块JSON解析错误检查完成，未发现需要修复的地方")
    
    # 3. 修复产品路由相关问题
    routes_fixed = fix_product_routes()
    if routes_fixed:
        logger.info("成功修复产品路由相关问题")
    else:
        logger.info("产品路由相关问题检查完成，未发现需要修复的地方")
    
    logger.info("所有修复操作已完成，请重新部署应用")

if __name__ == "__main__":
    main() 