#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复模板语法错误的脚本

此脚本专门修复Jinja2模板文件中的语法错误,尤其是:
1. 未闭合的block标签
2. 错误的endblock标签格式
3. 嵌套错误的block标签
"""

import os
import re
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_quotation_list_template():
    """修复quotation/list.html中的模板语法错误"""
    template_path = "app/templates/quotation/list.html"
    
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
    else:
        logger.info(f"检查完成,未发现需要修复的模板语法错误: {template_path}")
        return False

def main():
    """运行模板修复函数"""
    logger.info("开始修复模板语法错误...")
    
    # 修复quotation/list.html模板
    fixed = fix_quotation_list_template()
    
    if fixed:
        logger.info("成功修复所有模板语法错误")
    else:
        logger.info("未发现需要修复的模板语法错误或修复失败")
    
    logger.info("模板语法错误修复操作已完成")

if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-
"""
修复模板语法错误的脚本

此脚本专门修复Jinja2模板文件中的语法错误,尤其是:
1. 未闭合的block标签
2. 错误的endblock标签格式
3. 嵌套错误的block标签
"""

import os
import re
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_quotation_list_template():
    """修复quotation/list.html中的模板语法错误"""
    template_path = "app/templates/quotation/list.html"
    
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
    else:
        logger.info(f"检查完成,未发现需要修复的模板语法错误: {template_path}")
        return False

def main():
    """运行模板修复函数"""
    logger.info("开始修复模板语法错误...")
    
    # 修复quotation/list.html模板
    fixed = fix_quotation_list_template()
    
    if fixed:
        logger.info("成功修复所有模板语法错误")
    else:
        logger.info("未发现需要修复的模板语法错误或修复失败")
    
    logger.info("模板语法错误修复操作已完成")

if __name__ == "__main__":
    main() 