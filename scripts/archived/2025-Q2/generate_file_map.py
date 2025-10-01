#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
项目文件映射工具

此脚本用于生成项目中Python文件的依赖关系图，分析模块间的引用关系。
它会解析每个Python文件中的import语句，生成文件间的依赖关系，并输出为Markdown和JSON格式。

用法: python generate_file_map.py
"""

import os
import re
import sys
import json
import ast
from collections import defaultdict
from datetime import datetime

# 配置
PROJECT_ROOT = '.'  # 项目根目录
OUTPUT_FILE_MD = 'unused/analysis/file_dependency_map.md'  # Markdown格式输出文件
OUTPUT_FILE_JSON = 'unused/analysis/file_dependency_map.json'  # JSON格式输出文件
EXCLUDE_DIRS = ['venv', '.venv', '__pycache__', '.git', '.pytest_cache', 'unused', '.cursor']  # 排除目录

def parse_imports(file_path):
    """解析Python文件中的import语句
    
    参数:
        file_path: Python文件路径
        
    返回:
        导入模块的列表
    """
    imports = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        try:
            # 使用ast模块解析导入语句
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.append(name.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for name in node.names:
                        if module:
                            imports.append(f"{module}.{name.name}")
                        else:
                            imports.append(name.name)
        except SyntaxError:
            # 如果ast解析失败，尝试使用正则表达式解析
            import_pattern = r'^import\s+([^\s;]+)|^from\s+([^\s;]+)\s+import'
            for line in content.split('\n'):
                line = line.strip()
                match = re.match(import_pattern, line)
                if match:
                    module = match.group(1) or match.group(2)
                    if module:
                        imports.append(module)
    except Exception as e:
        print(f"解析文件 {file_path} 的导入语句时出错: {e}")
    
    return imports

def get_file_docstring(file_path):
    """提取文件的文档字符串
    
    参数:
        file_path: Python文件路径
        
    返回:
        文件的文档字符串或None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        tree = ast.parse(content)
        docstring = ast.get_docstring(tree)
        
        # 如果没有文件级别的docstring，尝试获取第一个类或函数的docstring
        if not docstring:
            for node in tree.body:
                if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                    docstring = ast.get_docstring(node)
                    if docstring:
                        break
        
        return docstring.strip() if docstring else None
    except Exception:
        return None

def get_functions_and_classes(file_path):
    """提取文件中定义的函数和类
    
    参数:
        file_path: Python文件路径
        
    返回:
        包含函数和类信息的字典
    """
    functions = []
    classes = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        tree = ast.parse(content)
        
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                function_info = {
                    'name': node.name,
                    'docstring': ast.get_docstring(node),
                    'line': node.lineno
                }
                functions.append(function_info)
            elif isinstance(node, ast.ClassDef):
                methods = []
                for method in node.body:
                    if isinstance(method, ast.FunctionDef):
                        method_info = {
                            'name': method.name,
                            'docstring': ast.get_docstring(method),
                            'line': method.lineno
                        }
                        methods.append(method_info)
                
                class_info = {
                    'name': node.name,
                    'docstring': ast.get_docstring(node),
                    'methods': methods,
                    'line': node.lineno
                }
                classes.append(class_info)
    except Exception as e:
        print(f"提取文件 {file_path} 的函数和类时出错: {e}")
    
    return {
        'functions': functions,
        'classes': classes
    }

def analyze_file(file_path):
    """分析Python文件的结构和依赖
    
    参数:
        file_path: Python文件路径
        
    返回:
        包含文件分析结果的字典
    """
    rel_path = os.path.relpath(file_path, PROJECT_ROOT)
    
    # 获取文件基本信息
    try:
        size = os.path.getsize(file_path)
        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        with open(file_path, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)
    except Exception as e:
        print(f"获取文件 {file_path} 的基本信息时出错: {e}")
        size = 0
        mtime = None
        line_count = 0
    
    # 分析导入语句
    imports = parse_imports(file_path)
    
    # 获取文档字符串
    docstring = get_file_docstring(file_path)
    
    # 获取函数和类
    structure = get_functions_and_classes(file_path)
    
    # 分析文件内容获取更多信息
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否是蓝图文件
        is_blueprint = 'Blueprint' in content
        
        # 检查是否是视图文件
        is_view = '@app.route' in content or '@blueprint.route' in content or 'render_template' in content
        
        # 检查是否是模型文件
        is_model = 'db.Model' in content or 'Column(' in content or 'relationship(' in content
        
        # 检查是否是配置文件
        is_config = 'Config' in content and ('DEBUG' in content or 'SQLALCHEMY_DATABASE_URI' in content)
        
        # 检查是否是测试文件
        is_test = 'unittest' in content or 'pytest' in content or 'def test_' in content
        
    except Exception:
        is_blueprint = False
        is_view = False
        is_model = False
        is_config = False
        is_test = False
    
    return {
        'path': rel_path,
        'size': size,
        'line_count': line_count,
        'last_modified': mtime.strftime('%Y-%m-%d %H:%M:%S') if mtime else None,
        'imports': imports,
        'docstring': docstring,
        'functions': structure['functions'],
        'classes': structure['classes'],
        'is_blueprint': is_blueprint,
        'is_view': is_view,
        'is_model': is_model,
        'is_config': is_config,
        'is_test': is_test
    }

def generate_dependency_map():
    """生成项目文件依赖关系图"""
    print("开始分析项目文件依赖关系...")
    
    # 存储分析结果
    file_info = {}
    dependency_map = defaultdict(list)
    
    # 遍历项目文件
    for root, dirs, files in os.walk(PROJECT_ROOT):
        # 排除列表中的目录
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, PROJECT_ROOT)
                
                # 分析文件
                file_info[rel_path] = analyze_file(file_path)
                
                # 打印进度信息
                print(f"已分析: {rel_path}")
    
    # 构建依赖关系图
    py_files = list(file_info.keys())
    module_map = {}
    
    # 创建模块到文件路径的映射
    for file_path in py_files:
        module_name = file_path.replace('/', '.').replace('\\', '.').replace('.py', '')
        module_map[module_name] = file_path
    
    # 建立依赖关系
    for file_path, info in file_info.items():
        for imported in info['imports']:
            # 检查导入是否在项目内
            for module in module_map:
                if imported == module or imported.startswith(module + '.'):
                    dependency_map[file_path].append(module_map[module])
                    break
    
    # 生成Markdown报告
    md_report = ["# 项目文件映射与依赖关系\n"]
    md_report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 概览部分
    md_report.append("## 概览\n")
    md_report.append(f"- 总文件数: {len(file_info)}")
    
    # 计算不同类型文件数量
    view_files = sum(1 for info in file_info.values() if info['is_view'])
    model_files = sum(1 for info in file_info.values() if info['is_model'])
    blueprint_files = sum(1 for info in file_info.values() if info['is_blueprint'])
    config_files = sum(1 for info in file_info.values() if info['is_config'])
    test_files = sum(1 for info in file_info.values() if info['is_test'])
    
    md_report.append(f"- 视图文件: {view_files}")
    md_report.append(f"- 模型文件: {model_files}")
    md_report.append(f"- 蓝图文件: {blueprint_files}")
    md_report.append(f"- 配置文件: {config_files}")
    md_report.append(f"- 测试文件: {test_files}\n")
    
    # 项目结构部分
    md_report.append("## 项目结构\n")
    
    # 按目录组织文件
    directories = defaultdict(list)
    for file_path in sorted(file_info.keys()):
        directory = os.path.dirname(file_path) or '.'
        directories[directory].append(file_path)
    
    for directory, files in sorted(directories.items()):
        md_report.append(f"### {directory}/\n")
        for file_path in sorted(files):
            info = file_info[file_path]
            file_type = []
            if info['is_view']:
                file_type.append("视图")
            if info['is_model']:
                file_type.append("模型")
            if info['is_blueprint']:
                file_type.append("蓝图")
            if info['is_config']:
                file_type.append("配置")
            if info['is_test']:
                file_type.append("测试")
            
            type_str = f" ({', '.join(file_type)})" if file_type else ""
            md_report.append(f"- **{os.path.basename(file_path)}**{type_str}: {info['line_count']} 行")
            if info['docstring']:
                doc_summary = info['docstring'].split('\n')[0]
                md_report.append(f"  - {doc_summary}")
    
    # 依赖关系部分
    md_report.append("\n## 文件依赖关系\n")
    
    for file_path in sorted(file_info.keys()):
        md_report.append(f"### {file_path}\n")
        
        # 文件依赖的其他文件
        if dependency_map[file_path]:
            md_report.append("依赖于:")
            for dep in sorted(dependency_map[file_path]):
                md_report.append(f"- {dep}")
        else:
            md_report.append("无内部依赖")
        
        # 哪些文件依赖这个文件
        dependents = [f for f, deps in dependency_map.items() if file_path in deps]
        if dependents:
            md_report.append("\n被以下文件依赖:")
            for dep in sorted(dependents):
                md_report.append(f"- {dep}")
        else:
            md_report.append("\n没有被其他文件依赖")
        
        md_report.append("")
    
    # 保存Markdown报告
    report_dir = os.path.dirname(OUTPUT_FILE_MD)
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
    
    with open(OUTPUT_FILE_MD, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_report))
    
    # 保存JSON数据
    json_data = {
        'files': file_info,
        'dependencies': {k: v for k, v in dependency_map.items()},
        'summary': {
            'total_files': len(file_info),
            'view_files': view_files,
            'model_files': model_files,
            'blueprint_files': blueprint_files,
            'config_files': config_files,
            'test_files': test_files
        }
    }
    
    with open(OUTPUT_FILE_JSON, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, default=str)
    
    print(f"分析完成，报告已保存到 {OUTPUT_FILE_MD} 和 {OUTPUT_FILE_JSON}")
    
    return {
        'file_info': file_info,
        'dependency_map': dependency_map
    }

def main():
    """主函数"""
    try:
        result = generate_dependency_map()
        if result:
            print(f"分析结果: 找到 {len(result['file_info'])} 个Python文件")
            
            # 找出最被依赖的文件
            dependents_count = defaultdict(int)
            for _, deps in result['dependency_map'].items():
                for dep in deps:
                    dependents_count[dep] += 1
            
            most_depended = sorted(dependents_count.items(), key=lambda x: x[1], reverse=True)[:5]
            if most_depended:
                print("\n最被依赖的文件:")
                for file_path, count in most_depended:
                    print(f"- {file_path}: 被 {count} 个文件依赖")
    except Exception as e:
        print(f"执行分析时出错: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 