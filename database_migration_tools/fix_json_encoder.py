#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复Flask JSON问题

这个脚本专门解决flask.json.JSONEncoder导入问题
"""

import re
import os

def fix_recaptcha_widgets(filepath="venv/lib/python3.11/site-packages/flask_wtf/recaptcha/widgets.py"):
    """
    修复flask_wtf中recaptcha widgets.py文件中的JSONEncoder导入问题
    """
    if not os.path.exists(filepath):
        filepath = "venv/lib/python3.13/site-packages/flask_wtf/recaptcha/widgets.py"
    
    if not os.path.exists(filepath):
        print(f"错误: 未找到文件 {filepath}")
        print("尝试查找正确路径...")
        
        # 尝试查找真实路径
        import glob
        paths = glob.glob("venv/lib/python*/site-packages/flask_wtf/recaptcha/widgets.py")
        if not paths:
            print("错误: 无法找到flask_wtf recaptcha widgets.py文件")
            return False
        filepath = paths[0]
        print(f"找到文件: {filepath}")
    
    print(f"修复文件: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份原始文件
    with open(f"{filepath}.bak", 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 修复导入问题
    if 'JSONEncoder = json.JSONEncoder' in content:
        # 新版Flask中，JSONEncoder在flask.json.provider中
        new_content = content.replace(
            'JSONEncoder = json.JSONEncoder', 
            """
# 兼容不同版本的Flask
try:
    # 适用于Flask 2.3+
    from flask.json.provider import JSONEncoder
except ImportError:
    # 适用于旧版Flask
    JSONEncoder = json.JSONEncoder
"""
        )
        
        # 写入修改后的文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"成功修复 {filepath} 中的JSONEncoder导入")
        return True
    else:
        print(f"文件 {filepath} 中未找到需要修复的内容")
        return False

def main():
    """主函数"""
    print("开始修复Flask JSON问题...")
    
    # 修复recaptcha widgets.py
    fixed = fix_recaptcha_widgets()
    
    if fixed:
        print("\n问题已修复，请尝试重新部署")
    else:
        print("\n注意: 未能自动修复问题")
        print("建议手动修改依赖包中使用了json.JSONEncoder的文件")
    
    print("\n如需提交更改，请执行:")
    print("git add fix_json_encoder.py")
    print("git commit -m \"添加修复Flask JSON问题的脚本\"")
    print("git push")

if __name__ == "__main__":
    main() 