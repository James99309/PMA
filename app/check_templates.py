#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板语法检查修复工具

用于在应用启动时自动检查和修复Jinja模板语法错误
特别是解决quotation/list.html和user/list.html文件中的问题
"""

import os
import re
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('模板检查')

def analyze_template(content):
    """分析模板中的block和endblock标签"""
    # 找出所有的block标签
    block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
    blocks = re.findall(block_pattern, content)
    
    # 找出所有的endblock标签
    endblock_pattern = r'{%\s*endblock(?:\s+([a-zA-Z0-9_]+))?\s*%}'
    endblocks_with_names = re.findall(endblock_pattern, content)
    
    # 去除None值和空字符串
    endblocks = [name for name in endblocks_with_names if name]
    
    # 统计各block出现的次数
    block_counts = {}
    for block in blocks:
        if block in block_counts:
            block_counts[block] += 1
        else:
            block_counts[block] = 1
    
    # 统计各endblock出现的次数
    endblock_counts = {}
    for endblock in endblocks:
        if endblock in endblock_counts:
            endblock_counts[endblock] += 1
        else:
            endblock_counts[endblock] = 1
    
    # 检查不匹配的情况
    missing_endblocks = []
    for block, count in block_counts.items():
        if block not in endblock_counts or endblock_counts[block] < count:
            missing_endblocks.append(block)
    
    extra_endblocks = []
    for endblock, count in endblock_counts.items():
        if endblock not in block_counts or endblock_counts[endblock] > block_counts[endblock]:
            extra_endblocks.append(endblock)
    
    unnamed_endblocks = len(endblocks_with_names) - len(endblocks)
    
    return {
        'blocks': blocks,
        'endblocks': endblocks,
        'block_counts': block_counts,
        'endblock_counts': endblock_counts,
        'missing_endblocks': missing_endblocks,
        'extra_endblocks': extra_endblocks,
        'unnamed_endblocks': unnamed_endblocks,
        'total_blocks': len(blocks),
        'total_endblocks': len(endblocks_with_names)
    }

def fix_template(file_path, backup=True):
    """修复模板文件的语法错误"""
    if not os.path.exists(file_path):
        logger.error(f"错误: 文件不存在 {file_path}")
        return False
    
    logger.info(f"处理文件: {file_path}")
    
    # 读取原始内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 分析模板
    analysis = analyze_template(content)
    logger.info(f"分析结果:")
    logger.info(f"  总block数: {analysis['total_blocks']}")
    logger.info(f"  总endblock数: {analysis['total_endblocks']}")
    logger.info(f"  未命名endblock数: {analysis['unnamed_endblocks']}")
    
    # 创建备份文件
    if backup:
        backup_path = f"{file_path}.bak"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"已创建备份文件: {backup_path}")
    
    # 记录原始内容以检测变化
    original_content = content
    
    # 以下是针对可能的问题的修复逻辑
    
    # 1. 修复无名称的endblock
    if analysis['unnamed_endblocks'] > 0 and "{% block content %}" in content:
        logger.info("修复无名称的endblock标签...")
        content = re.sub(r'{%\s*endblock\s*%}', '{% endblock content %}', content)
    
    # 2. 修复缺少的endblock标签
    if analysis['missing_endblocks']:
        logger.info(f"发现缺少endblock标签: {analysis['missing_endblocks']}")
        for block in analysis['missing_endblocks']:
            # 在文件末尾添加缺少的endblock
            content += f"\n{{% endblock {block} %}}\n"
        logger.info(f"已在文件末尾添加缺少的endblock标签")
    
    # 3. 删除额外的endblock标签
    if analysis['extra_endblocks'] or analysis['total_endblocks'] > analysis['total_blocks']:
        logger.info(f"发现额外的endblock标签")
        
        # 特殊处理: 尝试找到无名称的多余endblock并删除
        extra_endblock_pattern = r'{%\s*endblock\s*%}'
        content = re.sub(extra_endblock_pattern, '<!-- 已删除无名称endblock -->', content)
        
        # 处理有特定名称的多余endblock
        for extra in analysis['extra_endblocks']:
            extra_named_pattern = r'{%\s*endblock\s+' + re.escape(extra) + r'\s*%}'
            content = re.sub(extra_named_pattern, f'<!-- 已删除多余endblock {extra} -->', content)
        
        logger.info(f"已删除额外的endblock标签")
    
    # 4. 特殊处理: 确保文件末尾不存在错误的标签
    if content.endswith("%}"):
        content = content[:-2] + "\n"
        logger.info("已修复文件末尾格式")
    
    # 5. 只有在内容变更时才写入文件
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"已修复文件: {file_path}")
        return True
    else:
        logger.info(f"文件无需修复")
        return False

def check_templates():
    """检查并修复模板文件"""
    logger.info("开始检查模板文件...")
    base_dir = Path.cwd()
    templates_dir = base_dir / 'app' / 'templates'
    
    if not templates_dir.exists():
        logger.error(f"模板目录不存在: {templates_dir}")
        return False
    
    # 优先检查已知有问题的文件
    problem_files = [
        templates_dir / 'user' / 'list.html',
        templates_dir / 'quotation' / 'list.html',
        templates_dir / 'product' / 'list.html'
    ]
    
    for file_path in problem_files:
        if file_path.exists():
            fix_template(str(file_path))
    
    # 是否返回所有修复的文件数量
    return True

if __name__ == "__main__":
    check_templates() 
# -*- coding: utf-8 -*-
"""
模板语法检查修复工具

用于在应用启动时自动检查和修复Jinja模板语法错误
特别是解决quotation/list.html和user/list.html文件中的问题
"""

import os
import re
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('模板检查')

def analyze_template(content):
    """分析模板中的block和endblock标签"""
    # 找出所有的block标签
    block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
    blocks = re.findall(block_pattern, content)
    
    # 找出所有的endblock标签
    endblock_pattern = r'{%\s*endblock(?:\s+([a-zA-Z0-9_]+))?\s*%}'
    endblocks_with_names = re.findall(endblock_pattern, content)
    
    # 去除None值和空字符串
    endblocks = [name for name in endblocks_with_names if name]
    
    # 统计各block出现的次数
    block_counts = {}
    for block in blocks:
        if block in block_counts:
            block_counts[block] += 1
        else:
            block_counts[block] = 1
    
    # 统计各endblock出现的次数
    endblock_counts = {}
    for endblock in endblocks:
        if endblock in endblock_counts:
            endblock_counts[endblock] += 1
        else:
            endblock_counts[endblock] = 1
    
    # 检查不匹配的情况
    missing_endblocks = []
    for block, count in block_counts.items():
        if block not in endblock_counts or endblock_counts[block] < count:
            missing_endblocks.append(block)
    
    extra_endblocks = []
    for endblock, count in endblock_counts.items():
        if endblock not in block_counts or endblock_counts[endblock] > block_counts[endblock]:
            extra_endblocks.append(endblock)
    
    unnamed_endblocks = len(endblocks_with_names) - len(endblocks)
    
    return {
        'blocks': blocks,
        'endblocks': endblocks,
        'block_counts': block_counts,
        'endblock_counts': endblock_counts,
        'missing_endblocks': missing_endblocks,
        'extra_endblocks': extra_endblocks,
        'unnamed_endblocks': unnamed_endblocks,
        'total_blocks': len(blocks),
        'total_endblocks': len(endblocks_with_names)
    }

def fix_template(file_path, backup=True):
    """修复模板文件的语法错误"""
    if not os.path.exists(file_path):
        logger.error(f"错误: 文件不存在 {file_path}")
        return False
    
    logger.info(f"处理文件: {file_path}")
    
    # 读取原始内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 分析模板
    analysis = analyze_template(content)
    logger.info(f"分析结果:")
    logger.info(f"  总block数: {analysis['total_blocks']}")
    logger.info(f"  总endblock数: {analysis['total_endblocks']}")
    logger.info(f"  未命名endblock数: {analysis['unnamed_endblocks']}")
    
    # 创建备份文件
    if backup:
        backup_path = f"{file_path}.bak"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"已创建备份文件: {backup_path}")
    
    # 记录原始内容以检测变化
    original_content = content
    
    # 以下是针对可能的问题的修复逻辑
    
    # 1. 修复无名称的endblock
    if analysis['unnamed_endblocks'] > 0 and "{% block content %}" in content:
        logger.info("修复无名称的endblock标签...")
        content = re.sub(r'{%\s*endblock\s*%}', '{% endblock content %}', content)
    
    # 2. 修复缺少的endblock标签
    if analysis['missing_endblocks']:
        logger.info(f"发现缺少endblock标签: {analysis['missing_endblocks']}")
        for block in analysis['missing_endblocks']:
            # 在文件末尾添加缺少的endblock
            content += f"\n{{% endblock {block} %}}\n"
        logger.info(f"已在文件末尾添加缺少的endblock标签")
    
    # 3. 删除额外的endblock标签
    if analysis['extra_endblocks'] or analysis['total_endblocks'] > analysis['total_blocks']:
        logger.info(f"发现额外的endblock标签")
        
        # 特殊处理: 尝试找到无名称的多余endblock并删除
        extra_endblock_pattern = r'{%\s*endblock\s*%}'
        content = re.sub(extra_endblock_pattern, '<!-- 已删除无名称endblock -->', content)
        
        # 处理有特定名称的多余endblock
        for extra in analysis['extra_endblocks']:
            extra_named_pattern = r'{%\s*endblock\s+' + re.escape(extra) + r'\s*%}'
            content = re.sub(extra_named_pattern, f'<!-- 已删除多余endblock {extra} -->', content)
        
        logger.info(f"已删除额外的endblock标签")
    
    # 4. 特殊处理: 确保文件末尾不存在错误的标签
    if content.endswith("%}"):
        content = content[:-2] + "\n"
        logger.info("已修复文件末尾格式")
    
    # 5. 只有在内容变更时才写入文件
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"已修复文件: {file_path}")
        return True
    else:
        logger.info(f"文件无需修复")
        return False

def check_templates():
    """检查并修复模板文件"""
    logger.info("开始检查模板文件...")
    base_dir = Path.cwd()
    templates_dir = base_dir / 'app' / 'templates'
    
    if not templates_dir.exists():
        logger.error(f"模板目录不存在: {templates_dir}")
        return False
    
    # 优先检查已知有问题的文件
    problem_files = [
        templates_dir / 'user' / 'list.html',
        templates_dir / 'quotation' / 'list.html',
        templates_dir / 'product' / 'list.html'
    ]
    
    for file_path in problem_files:
        if file_path.exists():
            fix_template(str(file_path))
    
    # 是否返回所有修复的文件数量
    return True

if __name__ == "__main__":
    check_templates() 
 
 
# -*- coding: utf-8 -*-
"""
模板语法检查修复工具

用于在应用启动时自动检查和修复Jinja模板语法错误
特别是解决quotation/list.html和user/list.html文件中的问题
"""

import os
import re
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('模板检查')

def analyze_template(content):
    """分析模板中的block和endblock标签"""
    # 找出所有的block标签
    block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
    blocks = re.findall(block_pattern, content)
    
    # 找出所有的endblock标签
    endblock_pattern = r'{%\s*endblock(?:\s+([a-zA-Z0-9_]+))?\s*%}'
    endblocks_with_names = re.findall(endblock_pattern, content)
    
    # 去除None值和空字符串
    endblocks = [name for name in endblocks_with_names if name]
    
    # 统计各block出现的次数
    block_counts = {}
    for block in blocks:
        if block in block_counts:
            block_counts[block] += 1
        else:
            block_counts[block] = 1
    
    # 统计各endblock出现的次数
    endblock_counts = {}
    for endblock in endblocks:
        if endblock in endblock_counts:
            endblock_counts[endblock] += 1
        else:
            endblock_counts[endblock] = 1
    
    # 检查不匹配的情况
    missing_endblocks = []
    for block, count in block_counts.items():
        if block not in endblock_counts or endblock_counts[block] < count:
            missing_endblocks.append(block)
    
    extra_endblocks = []
    for endblock, count in endblock_counts.items():
        if endblock not in block_counts or endblock_counts[endblock] > block_counts[endblock]:
            extra_endblocks.append(endblock)
    
    unnamed_endblocks = len(endblocks_with_names) - len(endblocks)
    
    return {
        'blocks': blocks,
        'endblocks': endblocks,
        'block_counts': block_counts,
        'endblock_counts': endblock_counts,
        'missing_endblocks': missing_endblocks,
        'extra_endblocks': extra_endblocks,
        'unnamed_endblocks': unnamed_endblocks,
        'total_blocks': len(blocks),
        'total_endblocks': len(endblocks_with_names)
    }

def fix_template(file_path, backup=True):
    """修复模板文件的语法错误"""
    if not os.path.exists(file_path):
        logger.error(f"错误: 文件不存在 {file_path}")
        return False
    
    logger.info(f"处理文件: {file_path}")
    
    # 读取原始内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 分析模板
    analysis = analyze_template(content)
    logger.info(f"分析结果:")
    logger.info(f"  总block数: {analysis['total_blocks']}")
    logger.info(f"  总endblock数: {analysis['total_endblocks']}")
    logger.info(f"  未命名endblock数: {analysis['unnamed_endblocks']}")
    
    # 创建备份文件
    if backup:
        backup_path = f"{file_path}.bak"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"已创建备份文件: {backup_path}")
    
    # 记录原始内容以检测变化
    original_content = content
    
    # 以下是针对可能的问题的修复逻辑
    
    # 1. 修复无名称的endblock
    if analysis['unnamed_endblocks'] > 0 and "{% block content %}" in content:
        logger.info("修复无名称的endblock标签...")
        content = re.sub(r'{%\s*endblock\s*%}', '{% endblock content %}', content)
    
    # 2. 修复缺少的endblock标签
    if analysis['missing_endblocks']:
        logger.info(f"发现缺少endblock标签: {analysis['missing_endblocks']}")
        for block in analysis['missing_endblocks']:
            # 在文件末尾添加缺少的endblock
            content += f"\n{{% endblock {block} %}}\n"
        logger.info(f"已在文件末尾添加缺少的endblock标签")
    
    # 3. 删除额外的endblock标签
    if analysis['extra_endblocks'] or analysis['total_endblocks'] > analysis['total_blocks']:
        logger.info(f"发现额外的endblock标签")
        
        # 特殊处理: 尝试找到无名称的多余endblock并删除
        extra_endblock_pattern = r'{%\s*endblock\s*%}'
        content = re.sub(extra_endblock_pattern, '<!-- 已删除无名称endblock -->', content)
        
        # 处理有特定名称的多余endblock
        for extra in analysis['extra_endblocks']:
            extra_named_pattern = r'{%\s*endblock\s+' + re.escape(extra) + r'\s*%}'
            content = re.sub(extra_named_pattern, f'<!-- 已删除多余endblock {extra} -->', content)
        
        logger.info(f"已删除额外的endblock标签")
    
    # 4. 特殊处理: 确保文件末尾不存在错误的标签
    if content.endswith("%}"):
        content = content[:-2] + "\n"
        logger.info("已修复文件末尾格式")
    
    # 5. 只有在内容变更时才写入文件
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"已修复文件: {file_path}")
        return True
    else:
        logger.info(f"文件无需修复")
        return False

def check_templates():
    """检查并修复模板文件"""
    logger.info("开始检查模板文件...")
    base_dir = Path.cwd()
    templates_dir = base_dir / 'app' / 'templates'
    
    if not templates_dir.exists():
        logger.error(f"模板目录不存在: {templates_dir}")
        return False
    
    # 优先检查已知有问题的文件
    problem_files = [
        templates_dir / 'user' / 'list.html',
        templates_dir / 'quotation' / 'list.html',
        templates_dir / 'product' / 'list.html'
    ]
    
    for file_path in problem_files:
        if file_path.exists():
            fix_template(str(file_path))
    
    # 是否返回所有修复的文件数量
    return True

if __name__ == "__main__":
    check_templates() 
# -*- coding: utf-8 -*-
"""
模板语法检查修复工具

用于在应用启动时自动检查和修复Jinja模板语法错误
特别是解决quotation/list.html和user/list.html文件中的问题
"""

import os
import re
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('模板检查')

def analyze_template(content):
    """分析模板中的block和endblock标签"""
    # 找出所有的block标签
    block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
    blocks = re.findall(block_pattern, content)
    
    # 找出所有的endblock标签
    endblock_pattern = r'{%\s*endblock(?:\s+([a-zA-Z0-9_]+))?\s*%}'
    endblocks_with_names = re.findall(endblock_pattern, content)
    
    # 去除None值和空字符串
    endblocks = [name for name in endblocks_with_names if name]
    
    # 统计各block出现的次数
    block_counts = {}
    for block in blocks:
        if block in block_counts:
            block_counts[block] += 1
        else:
            block_counts[block] = 1
    
    # 统计各endblock出现的次数
    endblock_counts = {}
    for endblock in endblocks:
        if endblock in endblock_counts:
            endblock_counts[endblock] += 1
        else:
            endblock_counts[endblock] = 1
    
    # 检查不匹配的情况
    missing_endblocks = []
    for block, count in block_counts.items():
        if block not in endblock_counts or endblock_counts[block] < count:
            missing_endblocks.append(block)
    
    extra_endblocks = []
    for endblock, count in endblock_counts.items():
        if endblock not in block_counts or endblock_counts[endblock] > block_counts[endblock]:
            extra_endblocks.append(endblock)
    
    unnamed_endblocks = len(endblocks_with_names) - len(endblocks)
    
    return {
        'blocks': blocks,
        'endblocks': endblocks,
        'block_counts': block_counts,
        'endblock_counts': endblock_counts,
        'missing_endblocks': missing_endblocks,
        'extra_endblocks': extra_endblocks,
        'unnamed_endblocks': unnamed_endblocks,
        'total_blocks': len(blocks),
        'total_endblocks': len(endblocks_with_names)
    }

def fix_template(file_path, backup=True):
    """修复模板文件的语法错误"""
    if not os.path.exists(file_path):
        logger.error(f"错误: 文件不存在 {file_path}")
        return False
    
    logger.info(f"处理文件: {file_path}")
    
    # 读取原始内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 分析模板
    analysis = analyze_template(content)
    logger.info(f"分析结果:")
    logger.info(f"  总block数: {analysis['total_blocks']}")
    logger.info(f"  总endblock数: {analysis['total_endblocks']}")
    logger.info(f"  未命名endblock数: {analysis['unnamed_endblocks']}")
    
    # 创建备份文件
    if backup:
        backup_path = f"{file_path}.bak"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"已创建备份文件: {backup_path}")
    
    # 记录原始内容以检测变化
    original_content = content
    
    # 以下是针对可能的问题的修复逻辑
    
    # 1. 修复无名称的endblock
    if analysis['unnamed_endblocks'] > 0 and "{% block content %}" in content:
        logger.info("修复无名称的endblock标签...")
        content = re.sub(r'{%\s*endblock\s*%}', '{% endblock content %}', content)
    
    # 2. 修复缺少的endblock标签
    if analysis['missing_endblocks']:
        logger.info(f"发现缺少endblock标签: {analysis['missing_endblocks']}")
        for block in analysis['missing_endblocks']:
            # 在文件末尾添加缺少的endblock
            content += f"\n{{% endblock {block} %}}\n"
        logger.info(f"已在文件末尾添加缺少的endblock标签")
    
    # 3. 删除额外的endblock标签
    if analysis['extra_endblocks'] or analysis['total_endblocks'] > analysis['total_blocks']:
        logger.info(f"发现额外的endblock标签")
        
        # 特殊处理: 尝试找到无名称的多余endblock并删除
        extra_endblock_pattern = r'{%\s*endblock\s*%}'
        content = re.sub(extra_endblock_pattern, '<!-- 已删除无名称endblock -->', content)
        
        # 处理有特定名称的多余endblock
        for extra in analysis['extra_endblocks']:
            extra_named_pattern = r'{%\s*endblock\s+' + re.escape(extra) + r'\s*%}'
            content = re.sub(extra_named_pattern, f'<!-- 已删除多余endblock {extra} -->', content)
        
        logger.info(f"已删除额外的endblock标签")
    
    # 4. 特殊处理: 确保文件末尾不存在错误的标签
    if content.endswith("%}"):
        content = content[:-2] + "\n"
        logger.info("已修复文件末尾格式")
    
    # 5. 只有在内容变更时才写入文件
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"已修复文件: {file_path}")
        return True
    else:
        logger.info(f"文件无需修复")
        return False

def check_templates():
    """检查并修复模板文件"""
    logger.info("开始检查模板文件...")
    base_dir = Path.cwd()
    templates_dir = base_dir / 'app' / 'templates'
    
    if not templates_dir.exists():
        logger.error(f"模板目录不存在: {templates_dir}")
        return False
    
    # 优先检查已知有问题的文件
    problem_files = [
        templates_dir / 'user' / 'list.html',
        templates_dir / 'quotation' / 'list.html',
        templates_dir / 'product' / 'list.html'
    ]
    
    for file_path in problem_files:
        if file_path.exists():
            fix_template(str(file_path))
    
    # 是否返回所有修复的文件数量
    return True

if __name__ == "__main__":
    check_templates() 
 
 