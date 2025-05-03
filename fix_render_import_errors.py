#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复Render部署导入错误问题的脚本

此脚本修复以下内容：
1. 修复各文件中从flask导入csrf的错误
2. 修复从app.utils.permissions导入permission_required的错误
3. 修复从flask_wtf.csrf导入csrf_protect的错误
4. 修复quotation/list.html中的模板语法错误
"""

import os
import re
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_flask_csrf_imports(file_path):
    """修复从flask错误导入csrf的问题"""
    if not os.path.exists(file_path):
        logger.error(f"找不到文件: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    modified = False
    
    # 修复从flask导入csrf的错误
    if "from flask import csrf" in content:
        content = content.replace("from flask import csrf", "from flask_wtf.csrf import CSRFProtect")
        logger.info(f"修复: 将'from flask import csrf'修改为'from flask_wtf.csrf import CSRFProtect'在{file_path}")
        modified = True
    
    # 修复从app导入csrf的错误
    if "from app import csrf" in content:
        content = content.replace("from app import csrf", "from flask_wtf.csrf import CSRFProtect")
        logger.info(f"修复: 将'from app import csrf'修改为'from flask_wtf.csrf import CSRFProtect'在{file_path}")
        modified = True
    
    # 如果文件被修改,写回文件
    if modified:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        logger.info(f"成功修复csrf导入问题: {file_path}")
        return True
    
    return False

def fix_permission_required_imports(file_path):
    """修复从app.utils.permissions导入permission_required的错误"""
    if not os.path.exists(file_path):
        logger.error(f"找不到文件: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    modified = False
    
    # 修复permission_required的导入
    if "from app.utils.permissions import permission_required" in content:
        # 替换为从正确的模块导入
        content = content.replace(
            "from app.utils.permissions import permission_required", 
            "from app.permissions import permission_required"
        )
        logger.info(f"修复: 将'from app.utils.permissions import permission_required'修改为'from app.permissions import permission_required'在{file_path}")
        modified = True
    
    # 如果文件被修改,写回文件
    if modified:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        logger.info(f"成功修复permission_required导入问题: {file_path}")
        return True
    
    return False

def fix_flask_wtf_csrf_imports(file_path):
    """修复从flask_wtf.csrf导入csrf_protect的错误"""
    if not os.path.exists(file_path):
        logger.error(f"找不到文件: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    modified = False
    
    # 修复csrf_protect的导入
    if "from flask_wtf.csrf import csrf_protect" in content:
        content = content.replace(
            "from flask_wtf.csrf import csrf_protect", 
            "from flask_wtf.csrf import CSRFProtect"
        )
        logger.info(f"修复: 将'from flask_wtf.csrf import csrf_protect'修改为'from flask_wtf.csrf import CSRFProtect'在{file_path}")
        modified = True
    
    # 如果出现了csrf_protect的使用,也需要替换为CSRFProtect
    if "csrf_protect" in content and modified:
        content = content.replace("csrf_protect", "CSRFProtect")
        logger.info(f"修复: 将'csrf_protect'替换为'CSRFProtect'在{file_path}")
    
    # 如果文件被修改,写回文件
    if modified:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        logger.info(f"成功修复csrf_protect导入问题: {file_path}")
        return True
    
    return False

def fix_quotation_template():
    """修复quotation/list.html中的模板语法错误"""
    template_path = "app/templates/quotation/list.html"
    
    if not os.path.exists(template_path):
        logger.error(f"找不到文件: {template_path}")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    modified = False
    
    # 修复多余的endblock标签问题
    if content.endswith("%"):
        # 删除最后一个字符如果是多余的%
        content = content[:-1]
        logger.info(f"修复: 删除{template_path}中的多余百分号")
        modified = True
    
    # 确保模板块正确结束
    if "{% endblock content %}%" in content:
        content = content.replace("{% endblock content %}%", "{% endblock content %}")
        logger.info(f"修复: 修正{template_path}中的endblock标签格式")
        modified = True
    
    # 检查是否有未闭合的block标签
    block_count = content.count("{% block")
    endblock_count = content.count("{% endblock")
    
    if block_count > endblock_count:
        logger.info(f"检测到未闭合的block标签: {block_count}个block, {endblock_count}个endblock")
        # 在文件末尾添加缺少的endblock标签
        for i in range(block_count - endblock_count):
            content += "\n{% endblock %}"
        logger.info(f"修复: 在{template_path}末尾添加{block_count - endblock_count}个缺少的endblock标签")
        modified = True
    
    # 如果文件被修改,写回文件
    if modified:
        with open(template_path, 'w', encoding='utf-8') as file:
            file.write(content)
        logger.info(f"成功修复模板语法错误: {template_path}")
        return True
    
    return False

def fix_all_python_files():
    """修复所有Python文件中的导入问题"""
    fixed_files = 0
    
    # 遍历所有Python文件
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                
                # 跳过当前修复脚本
                if "fix_render" in file_path or "fix_all" in file_path:
                    continue
                
                # 修复各种导入问题
                fixed1 = fix_flask_csrf_imports(file_path)
                fixed2 = fix_permission_required_imports(file_path)
                fixed3 = fix_flask_wtf_csrf_imports(file_path)
                
                if fixed1 or fixed2 or fixed3:
                    fixed_files += 1
    
    return fixed_files

def main():
    """运行所有修复函数"""
    logger.info("开始修复Render部署导入错误问题...")
    
    # 修复所有Python文件中的导入问题
    fixed_files = fix_all_python_files()
    logger.info(f"已修复{fixed_files}个Python文件的导入问题")
    
    # 修复模板语法错误
    template_fixed = fix_quotation_template()
    if template_fixed:
        logger.info("成功修复报价单模板语法错误")
    else:
        logger.info("报价单模板检查完成,未发现需要修复的问题")
    
    logger.info("所有修复操作已完成")

if __name__ == "__main__":
    main() 