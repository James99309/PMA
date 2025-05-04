#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复Jinja模板语法错误
"""

import os
import re

def fix_quotation_template():
    """修复quotation/list.html中的模板语法错误"""
    template_path = "app/templates/quotation/list.html"
    
    if not os.path.exists(template_path):
        print(f"错误: 找不到文件 {template_path}")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # 检查开始和结束的block标签是否匹配
    block_starts = re.findall(r'{%\s*block\s+(\w+)\s*%}', content)
    block_ends = re.findall(r'{%\s*endblock(?:\s+(\w+))?\s*%}', content)
    
    print(f"找到 {len(block_starts)} 个block开始标签和 {len(block_ends)} 个endblock结束标签")
    
    # 检查是否有多余的endblock标签
    if len(block_ends) > len(block_starts):
        print("警告: 有多余的endblock标签，尝试修复...")
        
        # 查找可疑的模式
        content = re.sub(r'{%\s*endblock\s*content\s*%}%', '{% endblock content %}', content)
        print("修复: 删除endblock后的多余百分号")
        
        # 查找文件末尾的可疑标记
        if content.strip().endswith('%'):
            content = content.rstrip('%').rstrip() + '\n'
            print("修复: 删除文件末尾的多余百分号")
    
    # 检查block嵌套错误
    scripts_block_re = re.search(r'{%\s*block\s+scripts\s*%}(.*?){%\s*endblock(?:\s+scripts)?\s*%}', content, re.DOTALL)
    content_block_re = re.search(r'{%\s*block\s+content\s*%}(.*?){%\s*endblock(?:\s+content)?\s*%}', content, re.DOTALL)
    
    if scripts_block_re and content_block_re:
        scripts_block = scripts_block_re.group(0)
        scripts_end_pos = content.find(scripts_block) + len(scripts_block)
        content_end_pos = content.find('{% endblock content %}', scripts_end_pos)
        
        if content_end_pos > 0:
            print("发现scripts块后的额外endblock content标签，正在修复...")
            # 删除额外的endblock content标签
            content = content[:content_end_pos] + content[content_end_pos + len('{% endblock content %}'):]
            print("修复: 删除scripts块后的额外endblock content标签")
    
    # 修复所有漏掉的block标签
    if block_starts and 'content' in block_starts and not re.search(r'{%\s*endblock(?:\s+content)?\s*%}', content):
        content += '\n{% endblock content %}\n'
        print("修复: 添加缺失的endblock content标签")
    
    # 编写到临时文件检查语法
    tmp_file = template_path + ".fixed"
    with open(tmp_file, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print(f"已写入修复后的模板到 {tmp_file}")
    
    # 确认正确后覆盖原文件
    with open(template_path, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print(f"成功修复 {template_path}")
    return True

def main():
    """主函数"""
    print("开始修复模板语法错误...")
    
    fixed = fix_quotation_template()
    
    if fixed:
        print("\n建议执行以下命令提交更改并重新部署:")
        print("git add app/templates/quotation/list.html")
        print("git commit -m \"修复quotation/list.html模板语法错误\"")
        print("git push")
    else:
        print("\n修复失败，请手动检查模板文件。")
    
    print("\n请尝试重新部署您的应用。")

if __name__ == "__main__":
    main() 