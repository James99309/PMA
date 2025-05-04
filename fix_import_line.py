#!/usr/bin/env python3
# -*- coding: utf-8 -*-

with open('app/templates/quotation/list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换导入语句行
import_start = '{% from'
import_end = '%}'
import_pattern = import_start + '.*?' + import_end

# 构建一行内的新导入语句
new_import = "{% from 'macros/ui_helpers.html' import render_project_type, render_owner, render_datetime, render_currency, render_quotation_number %}"

# 使用正则表达式搜索和替换
import re
fixed_content = re.sub(import_start + '.*?' + import_end, new_import, content, flags=re.DOTALL)

with open('app/templates/quotation/list.html', 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print("已修复导入语句") 
# -*- coding: utf-8 -*-

with open('app/templates/quotation/list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换导入语句行
import_start = '{% from'
import_end = '%}'
import_pattern = import_start + '.*?' + import_end

# 构建一行内的新导入语句
new_import = "{% from 'macros/ui_helpers.html' import render_project_type, render_owner, render_datetime, render_currency, render_quotation_number %}"

# 使用正则表达式搜索和替换
import re
fixed_content = re.sub(import_start + '.*?' + import_end, new_import, content, flags=re.DOTALL)

with open('app/templates/quotation/list.html', 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print("已修复导入语句") 
 
 
# -*- coding: utf-8 -*-

with open('app/templates/quotation/list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换导入语句行
import_start = '{% from'
import_end = '%}'
import_pattern = import_start + '.*?' + import_end

# 构建一行内的新导入语句
new_import = "{% from 'macros/ui_helpers.html' import render_project_type, render_owner, render_datetime, render_currency, render_quotation_number %}"

# 使用正则表达式搜索和替换
import re
fixed_content = re.sub(import_start + '.*?' + import_end, new_import, content, flags=re.DOTALL)

with open('app/templates/quotation/list.html', 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print("已修复导入语句") 
# -*- coding: utf-8 -*-

with open('app/templates/quotation/list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换导入语句行
import_start = '{% from'
import_end = '%}'
import_pattern = import_start + '.*?' + import_end

# 构建一行内的新导入语句
new_import = "{% from 'macros/ui_helpers.html' import render_project_type, render_owner, render_datetime, render_currency, render_quotation_number %}"

# 使用正则表达式搜索和替换
import re
fixed_content = re.sub(import_start + '.*?' + import_end, new_import, content, flags=re.DOTALL)

with open('app/templates/quotation/list.html', 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print("已修复导入语句") 
 
 