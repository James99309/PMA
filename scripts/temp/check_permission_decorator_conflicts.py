#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检测项目中 @permission_required 装饰器与数据归属检查的冲突

问题：如果删除/编辑函数同时使用了：
1. @permission_required 装饰器（模块级权限检查）
2. can_edit_data() 或其他数据归属检查

则会导致创建者无法操作自己的数据（即使数据归属检查允许）
因为装饰器会先拦截没有模块权限的用户。
"""
import os
import re

# 路径修正
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

project_root = get_project_root()

# 需要检查的目录
check_dirs = [
    os.path.join(project_root, 'app', 'views'),
    os.path.join(project_root, 'app', 'routes')
]

# 数据归属检查函数列表
data_check_functions = [
    'can_edit_data',
    'can_view_data',
    'can_delete_company',
    'can_edit_company',
    'can_delete_project',
    'can_edit_project',
    'can_delete_product',
    'can_edit_product',
    'can_view_company',
    'can_view_project'
]

def analyze_function(file_path, func_lines, func_start_line):
    """分析一个函数是否有装饰器与数据检查冲突"""
    func_text = '\n'.join(func_lines)

    # 检查是否有 @permission_required 装饰器
    has_decorator = '@permission_required' in func_text

    # 检查是否有数据归属检查
    has_data_check = any(check_func in func_text for check_func in data_check_functions)

    # 提取函数名
    func_name_match = re.search(r'def\s+(\w+)\s*\(', func_text)
    func_name = func_name_match.group(1) if func_name_match else 'unknown'

    # 提取装饰器中的操作类型
    decorator_match = re.search(r"@permission_required\(['\"](\w+)['\"],\s*['\"](\w+)['\"]\)", func_text)
    module_name = decorator_match.group(1) if decorator_match else 'unknown'
    action = decorator_match.group(2) if decorator_match else 'unknown'

    return {
        'file': file_path,
        'function': func_name,
        'line': func_start_line,
        'module': module_name,
        'action': action,
        'has_decorator': has_decorator,
        'has_data_check': has_data_check,
        'conflict': has_decorator and has_data_check
    }

def scan_file(file_path):
    """扫描单个文件"""
    conflicts = []

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 查找所有函数定义
    i = 0
    while i < len(lines):
        line = lines[i]

        # 找到函数定义
        if re.match(r'^\s*def\s+\w+\s*\(', line):
            # 向上查找装饰器（最多10行）
            func_start = max(0, i - 10)
            func_lines = []

            # 收集装饰器和函数定义
            for j in range(func_start, i + 1):
                func_lines.append(lines[j].rstrip())

            # 收集函数体（最多50行或到下一个函数定义）
            body_lines = 0
            for j in range(i + 1, min(i + 51, len(lines))):
                if re.match(r'^\s*def\s+\w+\s*\(', lines[j]) or re.match(r'^@\w+', lines[j]):
                    break
                func_lines.append(lines[j].rstrip())
                body_lines += 1

            # 分析函数
            result = analyze_function(file_path, func_lines, i + 1)
            if result['conflict']:
                conflicts.append(result)

        i += 1

    return conflicts

def main():
    """主函数"""
    print("=" * 80)
    print("检测 @permission_required 装饰器与数据归属检查的冲突")
    print("=" * 80)

    all_conflicts = []

    # 扫描所有文件
    for check_dir in check_dirs:
        if not os.path.exists(check_dir):
            continue

        for root, dirs, files in os.walk(check_dir):
            # 跳过备份文件和缓存
            if '__pycache__' in root or '.bak' in root or 'backup' in root:
                continue

            for file in files:
                if file.endswith('.py') and not file.startswith('.'):
                    file_path = os.path.join(root, file)
                    try:
                        conflicts = scan_file(file_path)
                        all_conflicts.extend(conflicts)
                    except Exception as e:
                        print(f"⚠️  扫描文件出错 {file_path}: {e}")

    # 按模块和操作分组
    by_module = {}
    for conflict in all_conflicts:
        key = f"{conflict['module']}.{conflict['action']}"
        if key not in by_module:
            by_module[key] = []
        by_module[key].append(conflict)

    # 输出结果
    print(f"\n找到 {len(all_conflicts)} 个潜在冲突:")
    print()

    for key in sorted(by_module.keys()):
        conflicts = by_module[key]
        print(f"\n【{key}】- {len(conflicts)} 个函数")
        print("-" * 80)

        for c in conflicts:
            rel_path = c['file'].replace(project_root, '')
            print(f"  📄 {rel_path}:{c['line']}")
            print(f"     函数: {c['function']}()")
            print()

    # 总结
    print("=" * 80)
    print("总结:")
    print(f"  - 检测到 {len(all_conflicts)} 个函数可能存在权限冲突")
    print(f"  - 涉及 {len(by_module)} 个模块操作")
    print()
    print("建议:")
    print("  1. 检查这些函数是否真的需要 @permission_required 装饰器")
    print("  2. 如果函数内已有数据归属检查（can_edit_data等），应移除装饰器")
    print("  3. 保留装饰器会导致创建者无法操作自己的数据")
    print("=" * 80)

if __name__ == '__main__':
    main()
