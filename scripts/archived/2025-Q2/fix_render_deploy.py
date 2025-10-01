#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复Render部署问题的脚本

此脚本修复以下内容：
1. quotation/list.html中的模板语法错误
2. 确保api.py导入正确的模块
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
    
    # 修复多余的endblock标签问题
    if content.endswith("%"):
        # 删除最后一个字符如果是多余的%
        content = content[:-1]
        print(f"修复: 删除{template_path}中的多余百分号")
    
    # 确保模板块正确结束
    if "{% endblock content %}%" in content:
        content = content.replace("{% endblock content %}%", "{% endblock content %}")
        print(f"修复: 修正{template_path}中的endblock标签格式")
    
    with open(template_path, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print(f"成功修复 {template_path}")
    return True

def fix_api_imports():
    """修复app/routes/api.py中的导入问题"""
    api_path = "app/routes/api.py"
    
    if not os.path.exists(api_path):
        print(f"错误: 找不到文件 {api_path}")
        return False
    
    with open(api_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # 确保使用正确的CSRFProtect导入
    if "from flask import csrf" in content:
        content = content.replace("from flask import csrf", "from flask_wtf.csrf import CSRFProtect")
        print(f"修复: 修正{api_path}中的csrf导入")
    
    if "from app import csrf" in content:
        content = content.replace("from app import csrf", "from flask_wtf.csrf import CSRFProtect")
        print(f"修复: 修正{api_path}中的csrf导入")
    
    if "from flask_wtf.csrf import csrf_protect" in content:
        content = content.replace("from flask_wtf.csrf import csrf_protect", "from flask_wtf.csrf import CSRFProtect")
        print(f"修复: 修正{api_path}中的csrf_protect导入")
    
    # 修复permission_required的导入
    if "from app.utils.permissions import permission_required" in content:
        # 检查是否需要修改
        if "permission_required" not in content:
            content = content.replace("from app.utils.permissions import permission_required", 
                                     "# Removed invalid import: from app.utils.permissions import permission_required")
            print(f"修复: 删除{api_path}中无效的permission_required导入")
    
    with open(api_path, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print(f"成功修复 {api_path}")
    return True

def main():
    """运行所有修复函数"""
    print("开始修复Render部署问题...")
    
    template_fixed = fix_quotation_template()
    api_fixed = fix_api_imports()
    
    if template_fixed and api_fixed:
        print("所有问题已修复，现在可以重新部署到Render")
    else:
        print("部分问题修复失败，请查看上面的错误信息")

if __name__ == "__main__":
    main() 