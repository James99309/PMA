#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jinja2模板错误修复工具

专门用于修复模板语法错误，尤其是endblock标签问题
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
        logging.FileHandler('template_fix.log')
    ]
)
logger = logging.getLogger('模板修复')

def analyze_template(content):
    """分析模板中的block和endblock标签"""
    # 找出所有的block标签
    block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
    blocks = re.findall(block_pattern, content)
    
    # 找出所有的endblock标签
    endblock_pattern = r'{%\s*endblock(?:\s+([a-zA-Z0-9_]+))?\s*%}'
    endblocks_raw = re.findall(endblock_pattern, content)
    
    # 去除None值或空字符串
    endblocks = [name for name in endblocks_raw if name]
    
    # 检查是否有未命名的endblock
    unnamed_endblocks = len(endblocks_raw) - len(endblocks)
    
    logger.info(f"模板中的block标签: {blocks}")
    logger.info(f"模板中的命名endblock标签: {endblocks}")
    logger.info(f"模板中的未命名endblock标签数量: {unnamed_endblocks}")
    
    # 检查block和endblock是否匹配
    missing_endblocks = set(blocks) - set(endblocks)
    if missing_endblocks and len(blocks) > unnamed_endblocks:
        logger.warning(f"以下block没有对应的命名endblock: {missing_endblocks}")
    
    return blocks, endblocks, unnamed_endblocks

def fix_template(file_path):
    """修复模板文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"开始分析模板: {file_path}")
        blocks, endblocks, unnamed_endblocks = analyze_template(content)
        
        # 如果没有检测到问题，跳过修复
        if not (set(blocks) - set(endblocks)) and len(blocks) == len(endblocks) + unnamed_endblocks:
            logger.info(f"模板 {file_path} 没有检测到block/endblock匹配问题")
            return False
        
        # 找出最后一个endblock标签
        last_endblock_pattern = r'({%\s*endblock(?:\s+[a-zA-Z0-9_]+)?\s*%})'
        last_endblock_match = list(re.finditer(last_endblock_pattern, content))
        
        if not last_endblock_match:
            logger.warning(f"模板 {file_path} 中没有找到endblock标签")
            
            # 尝试寻找最后一个block标签，为其添加endblock
            last_block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
            last_block_matches = list(re.finditer(last_block_pattern, content))
            
            if last_block_matches:
                last_block = last_block_matches[-1]
                block_name = re.search(r'block\s+([a-zA-Z0-9_]+)', last_block.group(0)).group(1)
                
                # 在文件末尾添加缺失的endblock
                new_content = content + f"\n{{% endblock {block_name} %}}\n"
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                logger.info(f"已添加缺失的endblock: {block_name}")
                return True
            
            return False
        
        modified = False
        new_content = content
        
        # 修复未命名的endblock标签
        for block in blocks:
            if block not in endblocks:
                # 查找对应的unnamed endblock并替换为named endblock
                unnamed_pattern = r'{%\s*endblock\s*%}'
                if re.search(unnamed_pattern, new_content):
                    new_content = re.sub(unnamed_pattern, f"{{% endblock {block} %}}", new_content, count=1)
                    logger.info(f"将未命名的endblock替换为: endblock {block}")
                    modified = True
        
        # 在最后添加缺失的endblock
        for block in set(blocks) - set(endblocks):
            if not re.search(f"{{% endblock {block} %}}", new_content):
                new_content += f"\n{{% endblock {block} %}}\n"
                logger.info(f"添加缺失的endblock: {block}")
                modified = True
        
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            logger.info(f"已修复模板: {file_path}")
        
        return modified
    
    except Exception as e:
        logger.error(f"修复模板 {file_path} 时出错: {str(e)}")
        return False

def fix_quotation_list_template():
    """修复quotation/list.html模板"""
    file_path = Path('app/templates/quotation/list.html')
    
    if not file_path.exists():
        logger.warning(f"文件不存在: {file_path}")
        return False
    
    logger.info(f"开始修复特定模板: {file_path}")
    return fix_template(file_path)

def fix_user_list_template():
    """修复user/list.html模板"""
    file_path = Path('app/templates/user/list.html')
    
    if not file_path.exists():
        logger.warning(f"文件不存在: {file_path}")
        return False
    
    logger.info(f"开始修复特定模板: {file_path}")
    return fix_template(file_path)

def scan_and_fix_all_templates():
    """扫描并修复所有模板文件"""
    templates_dir = Path('app/templates')
    
    if not templates_dir.exists():
        logger.warning(f"模板目录不存在: {templates_dir}")
        return
    
    fixed_count = 0
    error_count = 0
    
    for template_file in templates_dir.glob('**/*.html'):
        try:
            logger.info(f"检查模板: {template_file}")
            if fix_template(template_file):
                fixed_count += 1
        except Exception as e:
            logger.error(f"处理模板 {template_file} 时出错: {str(e)}")
            error_count += 1
    
    logger.info(f"模板修复完成. 已修复: {fixed_count}, 错误: {error_count}")

def main():
    """主函数"""
    logger.info("=== 开始修复Jinja2模板错误 ===")
    
    # 修复特定的问题模板
    fix_quotation_list_template()
    fix_user_list_template()
    
    # 扫描并修复所有模板
    scan_and_fix_all_templates()
    
    logger.info("=== 模板修复完成 ===")

if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-
"""
Jinja2模板错误修复工具

专门用于修复模板语法错误，尤其是endblock标签问题
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
        logging.FileHandler('template_fix.log')
    ]
)
logger = logging.getLogger('模板修复')

def analyze_template(content):
    """分析模板中的block和endblock标签"""
    # 找出所有的block标签
    block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
    blocks = re.findall(block_pattern, content)
    
    # 找出所有的endblock标签
    endblock_pattern = r'{%\s*endblock(?:\s+([a-zA-Z0-9_]+))?\s*%}'
    endblocks_raw = re.findall(endblock_pattern, content)
    
    # 去除None值或空字符串
    endblocks = [name for name in endblocks_raw if name]
    
    # 检查是否有未命名的endblock
    unnamed_endblocks = len(endblocks_raw) - len(endblocks)
    
    logger.info(f"模板中的block标签: {blocks}")
    logger.info(f"模板中的命名endblock标签: {endblocks}")
    logger.info(f"模板中的未命名endblock标签数量: {unnamed_endblocks}")
    
    # 检查block和endblock是否匹配
    missing_endblocks = set(blocks) - set(endblocks)
    if missing_endblocks and len(blocks) > unnamed_endblocks:
        logger.warning(f"以下block没有对应的命名endblock: {missing_endblocks}")
    
    return blocks, endblocks, unnamed_endblocks

def fix_template(file_path):
    """修复模板文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"开始分析模板: {file_path}")
        blocks, endblocks, unnamed_endblocks = analyze_template(content)
        
        # 如果没有检测到问题，跳过修复
        if not (set(blocks) - set(endblocks)) and len(blocks) == len(endblocks) + unnamed_endblocks:
            logger.info(f"模板 {file_path} 没有检测到block/endblock匹配问题")
            return False
        
        # 找出最后一个endblock标签
        last_endblock_pattern = r'({%\s*endblock(?:\s+[a-zA-Z0-9_]+)?\s*%})'
        last_endblock_match = list(re.finditer(last_endblock_pattern, content))
        
        if not last_endblock_match:
            logger.warning(f"模板 {file_path} 中没有找到endblock标签")
            
            # 尝试寻找最后一个block标签，为其添加endblock
            last_block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
            last_block_matches = list(re.finditer(last_block_pattern, content))
            
            if last_block_matches:
                last_block = last_block_matches[-1]
                block_name = re.search(r'block\s+([a-zA-Z0-9_]+)', last_block.group(0)).group(1)
                
                # 在文件末尾添加缺失的endblock
                new_content = content + f"\n{{% endblock {block_name} %}}\n"
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                logger.info(f"已添加缺失的endblock: {block_name}")
                return True
            
            return False
        
        modified = False
        new_content = content
        
        # 修复未命名的endblock标签
        for block in blocks:
            if block not in endblocks:
                # 查找对应的unnamed endblock并替换为named endblock
                unnamed_pattern = r'{%\s*endblock\s*%}'
                if re.search(unnamed_pattern, new_content):
                    new_content = re.sub(unnamed_pattern, f"{{% endblock {block} %}}", new_content, count=1)
                    logger.info(f"将未命名的endblock替换为: endblock {block}")
                    modified = True
        
        # 在最后添加缺失的endblock
        for block in set(blocks) - set(endblocks):
            if not re.search(f"{{% endblock {block} %}}", new_content):
                new_content += f"\n{{% endblock {block} %}}\n"
                logger.info(f"添加缺失的endblock: {block}")
                modified = True
        
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            logger.info(f"已修复模板: {file_path}")
        
        return modified
    
    except Exception as e:
        logger.error(f"修复模板 {file_path} 时出错: {str(e)}")
        return False

def fix_quotation_list_template():
    """修复quotation/list.html模板"""
    file_path = Path('app/templates/quotation/list.html')
    
    if not file_path.exists():
        logger.warning(f"文件不存在: {file_path}")
        return False
    
    logger.info(f"开始修复特定模板: {file_path}")
    return fix_template(file_path)

def fix_user_list_template():
    """修复user/list.html模板"""
    file_path = Path('app/templates/user/list.html')
    
    if not file_path.exists():
        logger.warning(f"文件不存在: {file_path}")
        return False
    
    logger.info(f"开始修复特定模板: {file_path}")
    return fix_template(file_path)

def scan_and_fix_all_templates():
    """扫描并修复所有模板文件"""
    templates_dir = Path('app/templates')
    
    if not templates_dir.exists():
        logger.warning(f"模板目录不存在: {templates_dir}")
        return
    
    fixed_count = 0
    error_count = 0
    
    for template_file in templates_dir.glob('**/*.html'):
        try:
            logger.info(f"检查模板: {template_file}")
            if fix_template(template_file):
                fixed_count += 1
        except Exception as e:
            logger.error(f"处理模板 {template_file} 时出错: {str(e)}")
            error_count += 1
    
    logger.info(f"模板修复完成. 已修复: {fixed_count}, 错误: {error_count}")

def main():
    """主函数"""
    logger.info("=== 开始修复Jinja2模板错误 ===")
    
    # 修复特定的问题模板
    fix_quotation_list_template()
    fix_user_list_template()
    
    # 扫描并修复所有模板
    scan_and_fix_all_templates()
    
    logger.info("=== 模板修复完成 ===")

if __name__ == "__main__":
    main() 
 
 
# -*- coding: utf-8 -*-
"""
Jinja2模板错误修复工具

专门用于修复模板语法错误，尤其是endblock标签问题
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
        logging.FileHandler('template_fix.log')
    ]
)
logger = logging.getLogger('模板修复')

def analyze_template(content):
    """分析模板中的block和endblock标签"""
    # 找出所有的block标签
    block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
    blocks = re.findall(block_pattern, content)
    
    # 找出所有的endblock标签
    endblock_pattern = r'{%\s*endblock(?:\s+([a-zA-Z0-9_]+))?\s*%}'
    endblocks_raw = re.findall(endblock_pattern, content)
    
    # 去除None值或空字符串
    endblocks = [name for name in endblocks_raw if name]
    
    # 检查是否有未命名的endblock
    unnamed_endblocks = len(endblocks_raw) - len(endblocks)
    
    logger.info(f"模板中的block标签: {blocks}")
    logger.info(f"模板中的命名endblock标签: {endblocks}")
    logger.info(f"模板中的未命名endblock标签数量: {unnamed_endblocks}")
    
    # 检查block和endblock是否匹配
    missing_endblocks = set(blocks) - set(endblocks)
    if missing_endblocks and len(blocks) > unnamed_endblocks:
        logger.warning(f"以下block没有对应的命名endblock: {missing_endblocks}")
    
    return blocks, endblocks, unnamed_endblocks

def fix_template(file_path):
    """修复模板文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"开始分析模板: {file_path}")
        blocks, endblocks, unnamed_endblocks = analyze_template(content)
        
        # 如果没有检测到问题，跳过修复
        if not (set(blocks) - set(endblocks)) and len(blocks) == len(endblocks) + unnamed_endblocks:
            logger.info(f"模板 {file_path} 没有检测到block/endblock匹配问题")
            return False
        
        # 找出最后一个endblock标签
        last_endblock_pattern = r'({%\s*endblock(?:\s+[a-zA-Z0-9_]+)?\s*%})'
        last_endblock_match = list(re.finditer(last_endblock_pattern, content))
        
        if not last_endblock_match:
            logger.warning(f"模板 {file_path} 中没有找到endblock标签")
            
            # 尝试寻找最后一个block标签，为其添加endblock
            last_block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
            last_block_matches = list(re.finditer(last_block_pattern, content))
            
            if last_block_matches:
                last_block = last_block_matches[-1]
                block_name = re.search(r'block\s+([a-zA-Z0-9_]+)', last_block.group(0)).group(1)
                
                # 在文件末尾添加缺失的endblock
                new_content = content + f"\n{{% endblock {block_name} %}}\n"
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                logger.info(f"已添加缺失的endblock: {block_name}")
                return True
            
            return False
        
        modified = False
        new_content = content
        
        # 修复未命名的endblock标签
        for block in blocks:
            if block not in endblocks:
                # 查找对应的unnamed endblock并替换为named endblock
                unnamed_pattern = r'{%\s*endblock\s*%}'
                if re.search(unnamed_pattern, new_content):
                    new_content = re.sub(unnamed_pattern, f"{{% endblock {block} %}}", new_content, count=1)
                    logger.info(f"将未命名的endblock替换为: endblock {block}")
                    modified = True
        
        # 在最后添加缺失的endblock
        for block in set(blocks) - set(endblocks):
            if not re.search(f"{{% endblock {block} %}}", new_content):
                new_content += f"\n{{% endblock {block} %}}\n"
                logger.info(f"添加缺失的endblock: {block}")
                modified = True
        
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            logger.info(f"已修复模板: {file_path}")
        
        return modified
    
    except Exception as e:
        logger.error(f"修复模板 {file_path} 时出错: {str(e)}")
        return False

def fix_quotation_list_template():
    """修复quotation/list.html模板"""
    file_path = Path('app/templates/quotation/list.html')
    
    if not file_path.exists():
        logger.warning(f"文件不存在: {file_path}")
        return False
    
    logger.info(f"开始修复特定模板: {file_path}")
    return fix_template(file_path)

def fix_user_list_template():
    """修复user/list.html模板"""
    file_path = Path('app/templates/user/list.html')
    
    if not file_path.exists():
        logger.warning(f"文件不存在: {file_path}")
        return False
    
    logger.info(f"开始修复特定模板: {file_path}")
    return fix_template(file_path)

def scan_and_fix_all_templates():
    """扫描并修复所有模板文件"""
    templates_dir = Path('app/templates')
    
    if not templates_dir.exists():
        logger.warning(f"模板目录不存在: {templates_dir}")
        return
    
    fixed_count = 0
    error_count = 0
    
    for template_file in templates_dir.glob('**/*.html'):
        try:
            logger.info(f"检查模板: {template_file}")
            if fix_template(template_file):
                fixed_count += 1
        except Exception as e:
            logger.error(f"处理模板 {template_file} 时出错: {str(e)}")
            error_count += 1
    
    logger.info(f"模板修复完成. 已修复: {fixed_count}, 错误: {error_count}")

def main():
    """主函数"""
    logger.info("=== 开始修复Jinja2模板错误 ===")
    
    # 修复特定的问题模板
    fix_quotation_list_template()
    fix_user_list_template()
    
    # 扫描并修复所有模板
    scan_and_fix_all_templates()
    
    logger.info("=== 模板修复完成 ===")

if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-
"""
Jinja2模板错误修复工具

专门用于修复模板语法错误，尤其是endblock标签问题
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
        logging.FileHandler('template_fix.log')
    ]
)
logger = logging.getLogger('模板修复')

def analyze_template(content):
    """分析模板中的block和endblock标签"""
    # 找出所有的block标签
    block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
    blocks = re.findall(block_pattern, content)
    
    # 找出所有的endblock标签
    endblock_pattern = r'{%\s*endblock(?:\s+([a-zA-Z0-9_]+))?\s*%}'
    endblocks_raw = re.findall(endblock_pattern, content)
    
    # 去除None值或空字符串
    endblocks = [name for name in endblocks_raw if name]
    
    # 检查是否有未命名的endblock
    unnamed_endblocks = len(endblocks_raw) - len(endblocks)
    
    logger.info(f"模板中的block标签: {blocks}")
    logger.info(f"模板中的命名endblock标签: {endblocks}")
    logger.info(f"模板中的未命名endblock标签数量: {unnamed_endblocks}")
    
    # 检查block和endblock是否匹配
    missing_endblocks = set(blocks) - set(endblocks)
    if missing_endblocks and len(blocks) > unnamed_endblocks:
        logger.warning(f"以下block没有对应的命名endblock: {missing_endblocks}")
    
    return blocks, endblocks, unnamed_endblocks

def fix_template(file_path):
    """修复模板文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        logger.info(f"开始分析模板: {file_path}")
        blocks, endblocks, unnamed_endblocks = analyze_template(content)
        
        # 如果没有检测到问题，跳过修复
        if not (set(blocks) - set(endblocks)) and len(blocks) == len(endblocks) + unnamed_endblocks:
            logger.info(f"模板 {file_path} 没有检测到block/endblock匹配问题")
            return False
        
        # 找出最后一个endblock标签
        last_endblock_pattern = r'({%\s*endblock(?:\s+[a-zA-Z0-9_]+)?\s*%})'
        last_endblock_match = list(re.finditer(last_endblock_pattern, content))
        
        if not last_endblock_match:
            logger.warning(f"模板 {file_path} 中没有找到endblock标签")
            
            # 尝试寻找最后一个block标签，为其添加endblock
            last_block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
            last_block_matches = list(re.finditer(last_block_pattern, content))
            
            if last_block_matches:
                last_block = last_block_matches[-1]
                block_name = re.search(r'block\s+([a-zA-Z0-9_]+)', last_block.group(0)).group(1)
                
                # 在文件末尾添加缺失的endblock
                new_content = content + f"\n{{% endblock {block_name} %}}\n"
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                logger.info(f"已添加缺失的endblock: {block_name}")
                return True
            
            return False
        
        modified = False
        new_content = content
        
        # 修复未命名的endblock标签
        for block in blocks:
            if block not in endblocks:
                # 查找对应的unnamed endblock并替换为named endblock
                unnamed_pattern = r'{%\s*endblock\s*%}'
                if re.search(unnamed_pattern, new_content):
                    new_content = re.sub(unnamed_pattern, f"{{% endblock {block} %}}", new_content, count=1)
                    logger.info(f"将未命名的endblock替换为: endblock {block}")
                    modified = True
        
        # 在最后添加缺失的endblock
        for block in set(blocks) - set(endblocks):
            if not re.search(f"{{% endblock {block} %}}", new_content):
                new_content += f"\n{{% endblock {block} %}}\n"
                logger.info(f"添加缺失的endblock: {block}")
                modified = True
        
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            logger.info(f"已修复模板: {file_path}")
        
        return modified
    
    except Exception as e:
        logger.error(f"修复模板 {file_path} 时出错: {str(e)}")
        return False

def fix_quotation_list_template():
    """修复quotation/list.html模板"""
    file_path = Path('app/templates/quotation/list.html')
    
    if not file_path.exists():
        logger.warning(f"文件不存在: {file_path}")
        return False
    
    logger.info(f"开始修复特定模板: {file_path}")
    return fix_template(file_path)

def fix_user_list_template():
    """修复user/list.html模板"""
    file_path = Path('app/templates/user/list.html')
    
    if not file_path.exists():
        logger.warning(f"文件不存在: {file_path}")
        return False
    
    logger.info(f"开始修复特定模板: {file_path}")
    return fix_template(file_path)

def scan_and_fix_all_templates():
    """扫描并修复所有模板文件"""
    templates_dir = Path('app/templates')
    
    if not templates_dir.exists():
        logger.warning(f"模板目录不存在: {templates_dir}")
        return
    
    fixed_count = 0
    error_count = 0
    
    for template_file in templates_dir.glob('**/*.html'):
        try:
            logger.info(f"检查模板: {template_file}")
            if fix_template(template_file):
                fixed_count += 1
        except Exception as e:
            logger.error(f"处理模板 {template_file} 时出错: {str(e)}")
            error_count += 1
    
    logger.info(f"模板修复完成. 已修复: {fixed_count}, 错误: {error_count}")

def main():
    """主函数"""
    logger.info("=== 开始修复Jinja2模板错误 ===")
    
    # 修复特定的问题模板
    fix_quotation_list_template()
    fix_user_list_template()
    
    # 扫描并修复所有模板
    scan_and_fix_all_templates()
    
    logger.info("=== 模板修复完成 ===")

if __name__ == "__main__":
    main() 
 
 