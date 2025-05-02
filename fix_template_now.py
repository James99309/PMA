#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
彻底修复quotation/list.html模板语法错误
"""

import os
import re

template_path = "app/templates/quotation/list.html"

# 读取模板内容
with open(template_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 创建备份
with open(f"{template_path}.bak", 'w', encoding='utf-8') as f:
    f.write(content)
print(f"已创建备份文件: {template_path}.bak")

# 提取每个block标签
block_pattern = r'{%\s*block\s+([a-zA-Z0-9_]+)\s*%}'
blocks = re.findall(block_pattern, content)
print(f"找到以下block标签: {blocks}")

# 对于base layout，我们期望有这些block
expected_blocks = ['content', 'scripts']

# 删除所有现有的endblock标签
content = re.sub(r'{%\s*endblock(?:\s+[a-zA-Z0-9_]+)?\s*%}', '', content)
print("已删除所有现有endblock标签")

# 确保内容不以奇怪的字符结尾
content = content.rstrip() + "\n"

# 重新添加正确的endblock标签
for block in expected_blocks:
    if block in blocks:
        if block == 'scripts':
            # 先闭合scripts块
            content += f"\n{{% endblock scripts %}}\n"
        elif block == 'content':
            # 最后闭合content块
            content += f"\n{{% endblock content %}}\n"

# 写回文件
with open(template_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"已修复文件: {template_path}")

# 验证模板
try:
    from jinja2 import Environment, FileSystemLoader
    env = Environment(loader=FileSystemLoader('app/templates'))
    template = env.get_template('quotation/list.html')
    print("模板语法验证成功！")
except Exception as e:
    print(f"模板语法验证失败: {str(e)}") 