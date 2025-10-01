#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全局修复脚本 - 解决Flask应用中的常见问题

修复内容:
1. CSRF导入问题: flask_wtf.csrf 替换不正确的导入
2. permission_required导入问题: 使用app.permissions中的函数
3. 修复模板语法错误: 检查模板中的block/endblock语法
"""

import os
import re
import shutil
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fix_all_issues.log')
    ]
)
logger = logging.getLogger('PMA修复')

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
        
        # 修复2: 从flask_wtf.csrf导入csrf_protect的问题
        if 'from flask_wtf.csrf import csrf_protect' in fixed_content:
            logger.info("检测到导入flask_wtf.csrf.csrf_protect的错误")
            fixed_content = fixed_content.replace(
                'from flask_wtf.csrf import csrf_protect', 
                'from flask_wtf.csrf import CSRFProtect'
            )
            logger.info("修复导入 CSRFProtect 替代 csrf_protect")
        
        # 修复3: 直接从app导入csrf的问题
        if 'from app import csrf' in fixed_content:
            logger.info("检测到从app导入csrf的错误")
            fixed_content = fixed_content.replace(
                'from app import csrf', 
                '# from app import csrf - 已修复\nfrom flask_wtf.csrf import CSRFProtect\ncsrf = CSRFProtect()'
            )
            logger.info("创建本地csrf实例")
        
        # 修复4: 从app.decorators导入permission_required的问题
        if 'from app.decorators import permission_required' in fixed_content:
            logger.info("检测到从app.decorators导入permission_required")
            fixed_content = fixed_content.replace(
                'from app.decorators import permission_required',
                'from app.permissions import permission_required'  
            )
            logger.info("修复导入权限函数从app.permissions模块")
        
        # 修复5: 添加CSRF实例化代码
        if 'from flask_wtf.csrf import CSRFProtect' in fixed_content and 'csrf = CSRFProtect()' not in fixed_content:
            # 在导入之后添加实例化代码
            lines = fixed_content.split('\n')
            import_index = -1
            
            for i, line in enumerate(lines):
                if 'from flask_wtf.csrf import CSRFProtect' in line:
                    import_index = i
                    break
            
            if import_index >= 0:
                # 找到logger行的位置
                logger_index = -1
                for i, line in enumerate(lines[import_index+1:], import_index+1):
                    if line.startswith('logger = '):
                        logger_index = i
                        break
                
                if logger_index >= 0:
                    # 在logger行之前插入CSRF实例化代码
                    lines.insert(logger_index, '# 创建CSRF保护实例')
                    lines.insert(logger_index + 1, 'csrf = CSRFProtect()')
                    lines.insert(logger_index + 2, '')  # 空行
                else:
                    # 在导入行之后直接插入
                    lines.insert(import_index + 1, '# 创建CSRF保护实例')
                    lines.insert(import_index + 2, 'csrf = CSRFProtect()')
                    lines.insert(import_index + 3, '')  # 空行
                
                fixed_content = '\n'.join(lines)
                logger.info("添加CSRF实例化代码")
        
        # 修复6: 从app.utils.permissions导入permission_required的问题
        if 'from app.utils.permissions import permission_required' in fixed_content:
            logger.info("检测到从app.utils.permissions导入permission_required")
            fixed_content = fixed_content.replace(
                'from app.utils.permissions import permission_required',
                'from app.permissions import permission_required'  
            )
            logger.info("修复导入权限函数从app.permissions模块")
        
        # 如果内容有变化，保存修改
        if content != fixed_content:
            with open(api_file, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            logger.info(f"已修复API文件: {api_file}")
            return True
        else:
            logger.info(f"API文件无需修改: {api_file}")
            return False
            
    except Exception as e:
        logger.error(f"修复API文件时出错: {str(e)}")
        return False

def fix_template_syntax(template_file='app/templates/quotation/list.html'):
    """修复模板语法错误"""
    if not os.path.exists(template_file):
        logger.error(f"模板文件不存在: {template_file}")
        return False
    
    # 创建备份
    backup_file = f"{template_file}.bak"
    if not os.path.exists(backup_file):
        shutil.copy2(template_file, backup_file)
        logger.info(f"已创建备份文件: {backup_file}")
    
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查block/endblock语法
        blocks = re.findall(r'{%\s*block\s+(\w+)\s*%}', content)
        endblocks = re.findall(r'{%\s*endblock(?:\s+(\w+))?\s*%}', content)
        
        # 规范化endblock匹配结果（考虑无命名参数的情况）
        normalized_endblocks = []
        for eb in endblocks:
            if isinstance(eb, tuple):
                if eb[0]:  # 有命名参数
                    normalized_endblocks.append(eb[0])
                else:  # 无命名参数
                    normalized_endblocks.append('')
            else:
                normalized_endblocks.append(eb if eb else '')
        
        logger.info(f"检测到 {len(blocks)} 个block标签和 {len(endblocks)} 个endblock标签")
        
        # 找到不匹配的标签
        block_counts = {}
        for block in blocks:
            block_counts[block] = block_counts.get(block, 0) + 1
        
        endblock_counts = {}
        for endblock in normalized_endblocks:
            if endblock:  # 忽略没有命名的endblock
                endblock_counts[endblock] = endblock_counts.get(endblock, 0) + 1
        
        # 检查是否有未闭合的block
        unclosed_blocks = []
        for block, count in block_counts.items():
            endblock_count = endblock_counts.get(block, 0)
            if count > endblock_count:
                unclosed_blocks.append(block)
                logger.warning(f"发现未闭合的block标签: {block}, block数量: {count}, endblock数量: {endblock_count}")
        
        # 检查是否有多余的endblock
        extra_endblocks = []
        for endblock, count in endblock_counts.items():
            block_count = block_counts.get(endblock, 0)
            if count > block_count:
                extra_endblocks.append(endblock)
                logger.warning(f"发现多余的endblock标签: {endblock}, block数量: {block_count}, endblock数量: {count}")
        
        # 检查单独的{% endblock %}标签（没有命名参数）
        unnamed_endblocks = content.count('{% endblock %}')
        if unnamed_endblocks > 0:
            logger.info(f"发现 {unnamed_endblocks} 个未命名的endblock标签")
        
        # 检查内容末尾是否有多余的endblock
        lines = content.split('\n')
        last_content_line = None
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip()
            if line and not line.startswith('{#') and not line.endswith('#}'):
                last_content_line = line
                break
        
        fixed_content = content
        
        # 修复: 如果末尾有多余的{% endblock content %}或类似标签，移除它
        if last_content_line and (
            last_content_line == '{% endblock content %}' or 
            last_content_line == '{% endblock %}' or
            re.match(r'{%\s*endblock\s+\w+\s*%}', last_content_line)
        ):
            # 检查是否有对应的block标签
            if 'endblock content' in last_content_line and 'content' not in blocks:
                logger.info("检测到末尾有多余的endblock content标签，但没有对应的block标签")
                # 移除这一行
                fixed_content = '\n'.join(lines[:-1])
                # 或者添加缺失的block标签
                # fixed_content = "{% block content %}\n" + fixed_content
                logger.info("移除了多余的endblock content标签")
        
        # 如果内容有变化，保存修改
        if content != fixed_content:
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            logger.info(f"已修复模板文件: {template_file}")
            return True
        else:
            logger.info(f"模板文件无需修改: {template_file}")
            return False
            
    except Exception as e:
        logger.error(f"修复模板文件时出错: {str(e)}")
        return False

def main():
    """主函数，修复所有已知问题"""
    logger.info("开始修复PMA应用的问题...")
    
    # 修复API导入问题
    api_file = 'app/routes/api.py'
    if os.path.exists(api_file):
        if fix_api_imports(api_file):
            logger.info(f"成功修复API文件: {api_file}")
        else:
            logger.warning(f"无法修复或不需要修复API文件: {api_file}")
    else:
        logger.error(f"API文件不存在: {api_file}")
    
    # 修复模板语法问题
    template_file = 'app/templates/quotation/list.html'
    if os.path.exists(template_file):
        if fix_template_syntax(template_file):
            logger.info(f"成功修复模板文件: {template_file}")
        else:
            logger.warning(f"无法修复或不需要修复模板文件: {template_file}")
    else:
        logger.error(f"模板文件不存在: {template_file}")
    
    logger.info("问题修复完成")

if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-
"""
全局修复脚本 - 解决Flask应用中的常见问题

修复内容:
1. CSRF导入问题: flask_wtf.csrf 替换不正确的导入
2. permission_required导入问题: 使用app.permissions中的函数
3. 修复模板语法错误: 检查模板中的block/endblock语法
"""

import os
import re
import shutil
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fix_all_issues.log')
    ]
)
logger = logging.getLogger('PMA修复')

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
        
        # 修复2: 从flask_wtf.csrf导入csrf_protect的问题
        if 'from flask_wtf.csrf import csrf_protect' in fixed_content:
            logger.info("检测到导入flask_wtf.csrf.csrf_protect的错误")
            fixed_content = fixed_content.replace(
                'from flask_wtf.csrf import csrf_protect', 
                'from flask_wtf.csrf import CSRFProtect'
            )
            logger.info("修复导入 CSRFProtect 替代 csrf_protect")
        
        # 修复3: 直接从app导入csrf的问题
        if 'from app import csrf' in fixed_content:
            logger.info("检测到从app导入csrf的错误")
            fixed_content = fixed_content.replace(
                'from app import csrf', 
                '# from app import csrf - 已修复\nfrom flask_wtf.csrf import CSRFProtect\ncsrf = CSRFProtect()'
            )
            logger.info("创建本地csrf实例")
        
        # 修复4: 从app.decorators导入permission_required的问题
        if 'from app.decorators import permission_required' in fixed_content:
            logger.info("检测到从app.decorators导入permission_required")
            fixed_content = fixed_content.replace(
                'from app.decorators import permission_required',
                'from app.permissions import permission_required'  
            )
            logger.info("修复导入权限函数从app.permissions模块")
        
        # 修复5: 添加CSRF实例化代码
        if 'from flask_wtf.csrf import CSRFProtect' in fixed_content and 'csrf = CSRFProtect()' not in fixed_content:
            # 在导入之后添加实例化代码
            lines = fixed_content.split('\n')
            import_index = -1
            
            for i, line in enumerate(lines):
                if 'from flask_wtf.csrf import CSRFProtect' in line:
                    import_index = i
                    break
            
            if import_index >= 0:
                # 找到logger行的位置
                logger_index = -1
                for i, line in enumerate(lines[import_index+1:], import_index+1):
                    if line.startswith('logger = '):
                        logger_index = i
                        break
                
                if logger_index >= 0:
                    # 在logger行之前插入CSRF实例化代码
                    lines.insert(logger_index, '# 创建CSRF保护实例')
                    lines.insert(logger_index + 1, 'csrf = CSRFProtect()')
                    lines.insert(logger_index + 2, '')  # 空行
                else:
                    # 在导入行之后直接插入
                    lines.insert(import_index + 1, '# 创建CSRF保护实例')
                    lines.insert(import_index + 2, 'csrf = CSRFProtect()')
                    lines.insert(import_index + 3, '')  # 空行
                
                fixed_content = '\n'.join(lines)
                logger.info("添加CSRF实例化代码")
        
        # 修复6: 从app.utils.permissions导入permission_required的问题
        if 'from app.utils.permissions import permission_required' in fixed_content:
            logger.info("检测到从app.utils.permissions导入permission_required")
            fixed_content = fixed_content.replace(
                'from app.utils.permissions import permission_required',
                'from app.permissions import permission_required'  
            )
            logger.info("修复导入权限函数从app.permissions模块")
        
        # 如果内容有变化，保存修改
        if content != fixed_content:
            with open(api_file, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            logger.info(f"已修复API文件: {api_file}")
            return True
        else:
            logger.info(f"API文件无需修改: {api_file}")
            return False
            
    except Exception as e:
        logger.error(f"修复API文件时出错: {str(e)}")
        return False

def fix_template_syntax(template_file='app/templates/quotation/list.html'):
    """修复模板语法错误"""
    if not os.path.exists(template_file):
        logger.error(f"模板文件不存在: {template_file}")
        return False
    
    # 创建备份
    backup_file = f"{template_file}.bak"
    if not os.path.exists(backup_file):
        shutil.copy2(template_file, backup_file)
        logger.info(f"已创建备份文件: {backup_file}")
    
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查block/endblock语法
        blocks = re.findall(r'{%\s*block\s+(\w+)\s*%}', content)
        endblocks = re.findall(r'{%\s*endblock(?:\s+(\w+))?\s*%}', content)
        
        # 规范化endblock匹配结果（考虑无命名参数的情况）
        normalized_endblocks = []
        for eb in endblocks:
            if isinstance(eb, tuple):
                if eb[0]:  # 有命名参数
                    normalized_endblocks.append(eb[0])
                else:  # 无命名参数
                    normalized_endblocks.append('')
            else:
                normalized_endblocks.append(eb if eb else '')
        
        logger.info(f"检测到 {len(blocks)} 个block标签和 {len(endblocks)} 个endblock标签")
        
        # 找到不匹配的标签
        block_counts = {}
        for block in blocks:
            block_counts[block] = block_counts.get(block, 0) + 1
        
        endblock_counts = {}
        for endblock in normalized_endblocks:
            if endblock:  # 忽略没有命名的endblock
                endblock_counts[endblock] = endblock_counts.get(endblock, 0) + 1
        
        # 检查是否有未闭合的block
        unclosed_blocks = []
        for block, count in block_counts.items():
            endblock_count = endblock_counts.get(block, 0)
            if count > endblock_count:
                unclosed_blocks.append(block)
                logger.warning(f"发现未闭合的block标签: {block}, block数量: {count}, endblock数量: {endblock_count}")
        
        # 检查是否有多余的endblock
        extra_endblocks = []
        for endblock, count in endblock_counts.items():
            block_count = block_counts.get(endblock, 0)
            if count > block_count:
                extra_endblocks.append(endblock)
                logger.warning(f"发现多余的endblock标签: {endblock}, block数量: {block_count}, endblock数量: {count}")
        
        # 检查单独的{% endblock %}标签（没有命名参数）
        unnamed_endblocks = content.count('{% endblock %}')
        if unnamed_endblocks > 0:
            logger.info(f"发现 {unnamed_endblocks} 个未命名的endblock标签")
        
        # 检查内容末尾是否有多余的endblock
        lines = content.split('\n')
        last_content_line = None
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip()
            if line and not line.startswith('{#') and not line.endswith('#}'):
                last_content_line = line
                break
        
        fixed_content = content
        
        # 修复: 如果末尾有多余的{% endblock content %}或类似标签，移除它
        if last_content_line and (
            last_content_line == '{% endblock content %}' or 
            last_content_line == '{% endblock %}' or
            re.match(r'{%\s*endblock\s+\w+\s*%}', last_content_line)
        ):
            # 检查是否有对应的block标签
            if 'endblock content' in last_content_line and 'content' not in blocks:
                logger.info("检测到末尾有多余的endblock content标签，但没有对应的block标签")
                # 移除这一行
                fixed_content = '\n'.join(lines[:-1])
                # 或者添加缺失的block标签
                # fixed_content = "{% block content %}\n" + fixed_content
                logger.info("移除了多余的endblock content标签")
        
        # 如果内容有变化，保存修改
        if content != fixed_content:
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            logger.info(f"已修复模板文件: {template_file}")
            return True
        else:
            logger.info(f"模板文件无需修改: {template_file}")
            return False
            
    except Exception as e:
        logger.error(f"修复模板文件时出错: {str(e)}")
        return False

def main():
    """主函数，修复所有已知问题"""
    logger.info("开始修复PMA应用的问题...")
    
    # 修复API导入问题
    api_file = 'app/routes/api.py'
    if os.path.exists(api_file):
        if fix_api_imports(api_file):
            logger.info(f"成功修复API文件: {api_file}")
        else:
            logger.warning(f"无法修复或不需要修复API文件: {api_file}")
    else:
        logger.error(f"API文件不存在: {api_file}")
    
    # 修复模板语法问题
    template_file = 'app/templates/quotation/list.html'
    if os.path.exists(template_file):
        if fix_template_syntax(template_file):
            logger.info(f"成功修复模板文件: {template_file}")
        else:
            logger.warning(f"无法修复或不需要修复模板文件: {template_file}")
    else:
        logger.error(f"模板文件不存在: {template_file}")
    
    logger.info("问题修复完成")

if __name__ == "__main__":
    main() 