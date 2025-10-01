#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复Jinja模板语法错误
"""

import os
import re
import shutil
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger('模板修复')

def fix_jinja_templates(templates_dir='app/templates'):
    """修复Jinja2模板中的block/endblock问题"""
    logger.info(f"开始修复模板目录: {templates_dir}")
    
    # 遍历模板目录下的所有.html文件
    for root, _, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                logger.info(f"检查文件: {file_path}")
                
                try:
                    # 读取文件内容
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 创建备份
                    backup_path = f"{file_path}.bak"
                    if not os.path.exists(backup_path):
                        shutil.copy2(file_path, backup_path)
                        logger.info(f"已创建备份文件: {backup_path}")
                    
                    # 检查block和endblock匹配
                    blocks = re.findall(r'{%\s*block\s+(\w+)\s*%}', content)
                    endblocks = re.findall(r'{%\s*endblock\s*%}', content)
                    endblocks_named = re.findall(r'{%\s*endblock\s+(\w+)\s*%}', content)
                    
                    logger.info(f"分析结果:")
                    logger.info(f"  总block数: {len(blocks)}")
                    logger.info(f"  总endblock数: {len(endblocks) + len(endblocks_named)}")
                    logger.info(f"  未命名endblock数: {len(endblocks)}")
                    
                    fixed = False
                    # 修复未命名的endblock
                    if len(blocks) > (len(endblocks_named)) and len(endblocks) > 0:
                        logger.info(f"开始修复未命名的endblock")
                        
                        # 使用stack来跟踪block嵌套
                        stack = []
                        new_content = []
                        lines = content.split('\n')
                        
                        for line in lines:
                            block_match = re.search(r'{%\s*block\s+(\w+)\s*%}', line)
                            endblock_match = re.search(r'{%\s*endblock\s*%}', line)
                            endblock_named_match = re.search(r'{%\s*endblock\s+(\w+)\s*%}', line)
                            
                            if block_match:
                                stack.append(block_match.group(1))
                                new_content.append(line)
                            elif endblock_match and stack:
                                # 替换未命名endblock为命名endblock
                                block_name = stack.pop()
                                new_line = line.replace('{% endblock %}', f"{{% endblock {block_name} %}}")
                                new_content.append(new_line)
                                fixed = True
                                logger.info(f"修复: {{% endblock %}} -> {{% endblock {block_name} %}}")
                            elif endblock_named_match:
                                if stack:
                                    stack.pop()
                                new_content.append(line)
                            else:
                                new_content.append(line)
                        
                        if fixed:
                            # 写入修复后的内容
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write('\n'.join(new_content))
                            logger.info(f"已修复并保存: {file_path}")
                        else:
                            logger.info("文件无需修复")
                    else:
                        logger.info("文件无需修复")
                
                except Exception as e:
                    logger.error(f"处理文件 {file_path} 时出错: {e}")

def main():
    """主函数"""
    print("开始修复模板语法错误...")
    
    fix_jinja_templates()
    
    print("\n请尝试重新部署您的应用。")

if __name__ == "__main__":
    main() 

def main():
    """主函数"""
    print("开始修复模板语法错误...")
    
    fix_jinja_templates()
    
    print("\n请尝试重新部署您的应用。")

if __name__ == "__main__":
    main() 