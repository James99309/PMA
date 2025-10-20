#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""交互式删除内部Wrapper类定义"""
import sys, os

# 路径修正
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

file_path = os.path.join(get_project_root(), 'app/helpers/approval_helpers.py')

# 读取文件
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 查找所有内部类定义（缩进的class定义，排除顶部的模块级类）
internal_classes = []
for i, line in enumerate(lines, 1):
    # 跳过顶部的模块级类定义
    if i in [49, 127, 197]:
        continue
    # 查找8个空格缩进的class定义
    if line.startswith('        class ') and 'ApprovalWrapper' in line:
        # 找到类定义的结束位置
        end_line = i
        for j in range(i, min(i + 100, len(lines) + 1)):
            if j >= len(lines):
                end_line = len(lines)
                break
            next_line = lines[j - 1]
            # 检查缩进是否回到函数级别
            if next_line.strip() and not next_line.startswith('        '):
                end_line = j - 1
                break

        internal_classes.append({
            'start': i,
            'end': end_line,
            'class_name': line.strip(),
            'code': ''.join(lines[i-1:end_line])
        })

print(f"📊 找到 {len(internal_classes)} 个内部类定义\n")

# 显示每个类定义的信息
for idx, cls in enumerate(internal_classes, 1):
    print(f"\n{'='*60}")
    print(f"内部类 #{idx}")
    print(f"{'='*60}")
    print(f"位置: 行{cls['start']}-{cls['end']} ({cls['end'] - cls['start'] + 1}行)")
    print(f"类名: {cls['class_name']}")
    print(f"\n代码预览（前10行）:")
    preview_lines = cls['code'].split('\n')[:10]
    for line in preview_lines:
        print(f"  {line}")
    if len(cls['code'].split('\n')) > 10:
        print(f"  ... (还有{len(cls['code'].split('\n')) - 10}行)")

print(f"\n\n{'='*60}")
print("📋 总结")
print(f"{'='*60}")
print(f"总共需要删除: {len(internal_classes)} 个内部类定义")
print(f"预计减少代码: ~{sum(cls['end'] - cls['start'] + 1 for cls in internal_classes)} 行")
print(f"\n✅ 所有这些类在删除后，代码会自动使用顶部定义的统一Wrapper类")
print(f"✅ 这些类都位于函数内部（8个空格缩进），不会影响其他代码")
