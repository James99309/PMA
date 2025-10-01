#!/usr/bin/env python
# -*- coding: utf-8 -*-

template_path = "app/templates/quotation/list.html"

# 读取原始内容
with open(template_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 创建新内容
new_content = content

# 确保末尾标签是正确的 - 删除任何可能存在的结束标签
if '{% endblock scripts %}' in new_content:
    new_content = new_content.replace('{% endblock scripts %}', '')
if '{% endblock content %}' in new_content:
    new_content = new_content.replace('{% endblock content %}', '')

# 添加正确的结束标签
new_content = new_content.rstrip() + '\n\n{% endblock scripts %}\n\n{% endblock content %}\n'

# 写入文件
with open(template_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("已修复quotation/list.html模板") 
# -*- coding: utf-8 -*-

template_path = "app/templates/quotation/list.html"

# 读取原始内容
with open(template_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 创建新内容
new_content = content

# 确保末尾标签是正确的 - 删除任何可能存在的结束标签
if '{% endblock scripts %}' in new_content:
    new_content = new_content.replace('{% endblock scripts %}', '')
if '{% endblock content %}' in new_content:
    new_content = new_content.replace('{% endblock content %}', '')

# 添加正确的结束标签
new_content = new_content.rstrip() + '\n\n{% endblock scripts %}\n\n{% endblock content %}\n'

# 写入文件
with open(template_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("已修复quotation/list.html模板") 
 
 