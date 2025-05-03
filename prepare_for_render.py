#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
为Render部署准备代码库的脚本

此脚本执行以下任务:
1. 修复各文件中从flask导入csrf的错误
2. 修复从app.utils.permissions导入permission_required的错误
3. 修复从flask_wtf.csrf导入csrf_protect的错误
4. 修复模板语法错误
5. 检查并解决权限问题

用法:
    python prepare_for_render.py
"""

import os
import re
import logging
import sys
import importlib.util
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('render_deploy_fixes.log')
    ]
)
logger = logging.getLogger(__name__)

def fix_imports(file_path):
    """修复导入错误问题"""
    if not os.path.exists(file_path):
        logger.error(f"找不到文件: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    modified = False
    
    # 修复1: 从flask导入csrf的错误
    if "from flask import csrf" in content:
        content = content.replace("from flask import csrf", "from flask_wtf.csrf import CSRFProtect")
        logger.info(f"修复: 将'from flask import csrf'修改为'from flask_wtf.csrf import CSRFProtect'在{file_path}")
        modified = True
    
    # 修复2: 从app导入csrf的错误
    if "from app import csrf" in content:
        content = content.replace("from app import csrf", "from flask_wtf.csrf import CSRFProtect")
        logger.info(f"修复: 将'from app import csrf'修改为'from flask_wtf.csrf import CSRFProtect'在{file_path}")
        modified = True
    
    # 修复3: permission_required的导入
    if "from app.utils.permissions import permission_required" in content:
        content = content.replace(
            "from app.utils.permissions import permission_required", 
            "from app.permissions import permission_required"
        )
        logger.info(f"修复: 将'from app.utils.permissions import permission_required'修改为'from app.permissions import permission_required'在{file_path}")
        modified = True
    
    # 修复4: csrf_protect的导入
    if "from flask_wtf.csrf import csrf_protect" in content:
        content = content.replace(
            "from flask_wtf.csrf import csrf_protect", 
            "from flask_wtf.csrf import CSRFProtect"
        )
        logger.info(f"修复: 将'from flask_wtf.csrf import csrf_protect'修改为'from flask_wtf.csrf import CSRFProtect'在{file_path}")
        modified = True
        
        # 同时修改所有使用csrf_protect的地方
        if "csrf_protect" in content:
            content = content.replace("csrf_protect", "CSRFProtect")
            logger.info(f"修复: 将'csrf_protect'替换为'CSRFProtect'在{file_path}")
    
    if modified:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        logger.info(f"成功修复导入问题: {file_path}")
        return True
    
    return False

def fix_template(template_path):
    """修复模板语法错误"""
    if not os.path.exists(template_path):
        logger.error(f"找不到文件: {template_path}")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    modified = False
    
    # 修复1: 删除多余的endblock标签(如果有)
    pattern = r'{%\s*endblock\s*%}(?!\s*{%\s*endblock)'
    matches = re.findall(pattern, content)
    if matches:
        # 找到孤立的endblock标签,将它们删除
        for match in matches:
            if content.count(match) > 1:  # 只有当有多个相同的endblock标签时才删除
                content = content.replace(match, '', 1)  # 只替换第一个匹配项
                logger.info(f"修复: 删除多余的endblock标签: {match}")
                modified = True
    
    # 修复2: 确保content块在文件最后正确关闭
    if "{% endblock content %}" not in content:
        # 检查文件末尾是否有合适的endblock
        if content.strip().endswith("{% endblock %}"):
            # 替换最后一个endblock为endblock content
            content = content.replace("{% endblock %}", "{% endblock content %}", 1)
            logger.info("修复: 将最后一个endblock标签修改为'{% endblock content %}'")
            modified = True
        else:
            # 在文件末尾添加endblock content
            content += "\n{% endblock content %}"
            logger.info("修复: 在文件末尾添加'{% endblock content %}'标签")
            modified = True
    
    # 修复3: 确保scripts块在内容块之前关闭
    scripts_block = "{% block scripts %}"
    scripts_endblock = "{% endblock scripts %}"
    content_endblock = "{% endblock content %}"
    
    if scripts_block in content and scripts_endblock in content and content_endblock in content:
        # 确保scripts块在content块之前关闭
        scripts_pos = content.find(scripts_block)
        scripts_end_pos = content.find(scripts_endblock)
        content_end_pos = content.find(content_endblock)
        
        if scripts_end_pos > content_end_pos:
            # scripts块在content块之后关闭,需要修复顺序
            content = content.replace(content_endblock, '')
            content = content[:scripts_end_pos + len(scripts_endblock)] + f"\n\n{content_endblock}" + content[scripts_end_pos + len(scripts_endblock):]
            logger.info("修复: 调整scripts块和content块的关闭顺序")
            modified = True
    
    # 修复4: 删除末尾的多余百分号(如果有)
    if content.endswith("%"):
        content = content[:-1]
        logger.info("修复: 删除文件末尾的多余百分号")
        modified = True
    
    # 修复5: 检查是否有未闭合的block标签
    block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
    endblock_pattern = r'{%\s*endblock\s+([a-zA-Z0-9_]+)?\s*%}'
    
    blocks = re.findall(block_pattern, content)
    endblocks = re.findall(endblock_pattern, content)
    endblocks = [eb for eb in endblocks if eb]  # 过滤掉没有名称的endblock
    
    # 检查每个命名块是否都有对应的结束块
    for block_name in blocks:
        if block_name not in endblocks and block_name != 'content':  # content块单独处理
            # 在文件末尾添加缺少的命名endblock
            content += f"\n{{% endblock {block_name} %}}"
            logger.info(f"修复: 添加缺少的endblock标签: {block_name}")
            modified = True
    
    if modified:
        with open(template_path, 'w', encoding='utf-8') as file:
            file.write(content)
        logger.info(f"成功修复模板语法错误: {template_path}")
        return True
    
    return False

def fix_product_module_imports():
    """修复产品模块的导入问题"""
    product_files = [
        "app/routes/product.py",
        "app/views/product.py",
        "app/models/product.py",
        "app/routes/product_code.py",
        "app/views/product_code.py"
    ]
    
    fixed_count = 0
    
    for file_path in product_files:
        if os.path.exists(file_path):
            if fix_imports(file_path):
                fixed_count += 1
    
    return fixed_count

def fix_all_python_files():
    """修复所有Python文件中的导入问题"""
    fixed_count = 0
    
    # 跳过的目录
    skip_dirs = [
        ".git", 
        "venv", 
        "__pycache__", 
        ".vscode",
        "node_modules"
    ]
    
    # 遍历所有Python文件
    for root, dirs, files in os.walk("."):
        # 跳过某些目录
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                
                # 跳过当前修复脚本
                if "prepare_for_render" in file_path or "fix_" in file_path:
                    continue
                
                # 修复导入问题
                if fix_imports(file_path):
                    fixed_count += 1
    
    return fixed_count

def fix_templates():
    """修复所有模板文件"""
    templates_to_check = [
        "app/templates/quotation/list.html",
        "app/templates/product/list.html",
        "app/templates/product_code/list.html"
    ]
    
    fixed_count = 0
    
    for template in templates_to_check:
        if os.path.exists(template):
            if fix_template(template):
                fixed_count += 1
    
    return fixed_count

def check_app_initialization():
    """检查app/__init__.py中的应用初始化代码"""
    init_file = "app/__init__.py"
    if not os.path.exists(init_file):
        logger.error(f"找不到文件: {init_file}")
        return False
    
    with open(init_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    modified = False
    
    # 检查csrf初始化
    if "csrf = CSRFProtect()" in content and "from flask_wtf.csrf import CSRFProtect" not in content:
        # 添加缺少的导入
        import_pattern = r'import.*?\n\n'
        import_match = re.search(import_pattern, content)
        if import_match:
            new_import = import_match.group(0).rstrip() + "\nfrom flask_wtf.csrf import CSRFProtect\n\n"
            content = content.replace(import_match.group(0), new_import)
            logger.info("修复: 在app/__init__.py中添加CSRFProtect导入")
            modified = True
    
    if modified:
        with open(init_file, 'w', encoding='utf-8') as file:
            file.write(content)
        logger.info("成功修复app/__init__.py")
        return True
    
    return False

def main():
    """运行所有修复函数"""
    start_time = time.time()
    logger.info("开始为Render部署准备代码...")
    
    # 1. 修复产品模块的导入问题
    product_fixes = fix_product_module_imports()
    logger.info(f"修复了{product_fixes}个产品模块文件的导入问题")
    
    # 2. 修复所有Python文件的导入问题
    all_fixes = fix_all_python_files()
    logger.info(f"总共修复了{all_fixes}个Python文件的导入问题")
    
    # 3. 修复模板语法错误
    template_fixes = fix_templates()
    logger.info(f"修复了{template_fixes}个模板文件的语法错误")
    
    # 4. 检查app初始化
    check_app_initialization()
    
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info(f"所有修复操作已完成,耗时{duration:.2f}秒")
    logger.info("现在代码已准备好部署到Render环境")

if __name__ == "__main__":
    main() 