#!/usr/bin/env python3
"""
函数检测和解析脚本
用于自动检测代码库中的函数变更并触发function-lifecycle-manager代理
"""

import os
import re
import json
import ast
import sys
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
import argparse
import logging


class FunctionDetector:
    """函数检测器"""
    
    def __init__(self, config_path: str = None):
        """初始化函数检测器"""
        self.config_path = config_path or ".claude/automation/agent-automation.json"
        self.config = self._load_config()
        self.logger = self._setup_logger()
        
        # 函数模式匹配
        self.python_patterns = [
            re.compile(r'^def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', re.MULTILINE),
            re.compile(r'^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', re.MULTILINE)
        ]
        
        self.js_patterns = [
            re.compile(r'^function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', re.MULTILINE),
            re.compile(r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*function', re.MULTILINE),
            re.compile(r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=>\s*', re.MULTILINE),
            re.compile(r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*function', re.MULTILINE)
        ]
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"配置文件未找到: {self.config_path}")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"配置文件格式错误: {e}")
            return {}
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('FunctionDetector')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def should_analyze_file(self, file_path: str) -> bool:
        """判断是否应该分析该文件"""
        file_patterns = self.config.get('rules', {}).get('function-lifecycle-manager', {}).get('file_patterns', {})
        include_patterns = file_patterns.get('include', [])
        exclude_patterns = file_patterns.get('exclude', [])
        
        # 检查排除模式
        for exclude_pattern in exclude_patterns:
            if self._match_pattern(file_path, exclude_pattern):
                return False
        
        # 检查包含模式
        if include_patterns:
            for include_pattern in include_patterns:
                if self._match_pattern(file_path, include_pattern):
                    return True
            return False
        
        return True
    
    def _match_pattern(self, file_path: str, pattern: str) -> bool:
        """模式匹配"""
        import fnmatch
        return fnmatch.fnmatch(file_path, pattern)
    
    def detect_functions_in_python(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """检测Python文件中的函数"""
        functions = []
        
        try:
            # 使用AST解析获取更准确的函数信息
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        'name': node.name,
                        'line_start': node.lineno,
                        'line_end': node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                        'args': [arg.arg for arg in node.args.args],
                        'decorators': [decorator.id if hasattr(decorator, 'id') else str(decorator) for decorator in node.decorator_list],
                        'docstring': ast.get_docstring(node),
                        'is_method': False,
                        'file_path': file_path,
                        'language': 'python'
                    }
                    functions.append(func_info)
                
                elif isinstance(node, ast.ClassDef):
                    # 检测类方法
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            func_info = {
                                'name': f"{node.name}.{item.name}",
                                'line_start': item.lineno,
                                'line_end': item.end_lineno if hasattr(item, 'end_lineno') else item.lineno,
                                'args': [arg.arg for arg in item.args.args],
                                'decorators': [decorator.id if hasattr(decorator, 'id') else str(decorator) for decorator in item.decorator_list],
                                'docstring': ast.get_docstring(item),
                                'is_method': True,
                                'class_name': node.name,
                                'file_path': file_path,
                                'language': 'python'
                            }
                            functions.append(func_info)
        
        except SyntaxError as e:
            self.logger.warning(f"语法错误，无法解析Python文件 {file_path}: {e}")
            # 回退到正则表达式匹配
            return self._detect_functions_by_regex(content, file_path, 'python')
        
        return functions
    
    def detect_functions_in_javascript(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """检测JavaScript文件中的函数"""
        return self._detect_functions_by_regex(content, file_path, 'javascript')
    
    def _detect_functions_by_regex(self, content: str, file_path: str, language: str) -> List[Dict[str, Any]]:
        """使用正则表达式检测函数"""
        functions = []
        lines = content.split('\n')
        
        patterns = self.python_patterns if language == 'python' else self.js_patterns
        
        for i, line in enumerate(lines, 1):
            for pattern in patterns:
                match = pattern.match(line)
                if match:
                    func_name = match.group(1)
                    func_info = {
                        'name': func_name,
                        'line_start': i,
                        'line_end': i,  # 简化处理，只记录开始行
                        'args': [],  # 正则匹配无法获取详细参数信息
                        'decorators': [],
                        'docstring': None,
                        'is_method': False,
                        'file_path': file_path,
                        'language': language
                    }
                    functions.append(func_info)
                    break
        
        return functions
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """分析单个文件"""
        if not self.should_analyze_file(file_path):
            return {'functions': [], 'skipped': True, 'reason': 'excluded_by_pattern'}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.logger.error(f"无法读取文件 {file_path}: {e}")
            return {'functions': [], 'error': str(e)}
        
        functions = []
        
        if file_path.endswith('.py'):
            functions = self.detect_functions_in_python(content, file_path)
        elif file_path.endswith(('.js', '.ts')):
            functions = self.detect_functions_in_javascript(content, file_path)
        
        # 计算文件哈希用于变更检测
        file_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        
        return {
            'file_path': file_path,
            'functions': functions,
            'file_hash': file_hash,
            'analyzed_at': datetime.now().isoformat(),
            'function_count': len(functions),
            'skipped': False
        }
    
    def analyze_directory(self, directory: str = '.') -> Dict[str, Any]:
        """分析整个目录"""
        results = {
            'summary': {
                'total_files': 0,
                'analyzed_files': 0,
                'skipped_files': 0,
                'total_functions': 0,
                'python_functions': 0,
                'javascript_functions': 0
            },
            'files': [],
            'analyzed_at': datetime.now().isoformat()
        }
        
        for root, dirs, files in os.walk(directory):
            # 跳过隐藏目录和常见的排除目录
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv']]
            
            for file in files:
                if file.endswith(('.py', '.js', '.ts')):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, directory)
                    
                    results['summary']['total_files'] += 1
                    
                    analysis = self.analyze_file(file_path)
                    analysis['relative_path'] = relative_path
                    
                    if analysis.get('skipped', False):
                        results['summary']['skipped_files'] += 1
                    else:
                        results['summary']['analyzed_files'] += 1
                        function_count = analysis.get('function_count', 0)
                        results['summary']['total_functions'] += function_count
                        
                        if file_path.endswith('.py'):
                            results['summary']['python_functions'] += function_count
                        else:
                            results['summary']['javascript_functions'] += function_count
                    
                    results['files'].append(analysis)
        
        return results
    
    def detect_changes(self, current_analysis: Dict[str, Any], previous_analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """检测函数变更"""
        if not previous_analysis:
            return {
                'new_functions': self._extract_all_functions(current_analysis),
                'modified_functions': [],
                'deleted_functions': [],
                'unchanged_functions': []
            }
        
        current_functions = self._extract_all_functions(current_analysis)
        previous_functions = self._extract_all_functions(previous_analysis)
        
        # 创建函数映射
        current_map = {f"{func['file_path']}:{func['name']}": func for func in current_functions}
        previous_map = {f"{func['file_path']}:{func['name']}": func for func in previous_functions}
        
        new_functions = []
        modified_functions = []
        deleted_functions = []
        unchanged_functions = []
        
        # 检测新增和修改的函数
        for key, current_func in current_map.items():
            if key not in previous_map:
                new_functions.append(current_func)
            else:
                previous_func = previous_map[key]
                if self._functions_different(current_func, previous_func):
                    modified_functions.append({
                        'current': current_func,
                        'previous': previous_func
                    })
                else:
                    unchanged_functions.append(current_func)
        
        # 检测删除的函数
        for key, previous_func in previous_map.items():
            if key not in current_map:
                deleted_functions.append(previous_func)
        
        return {
            'new_functions': new_functions,
            'modified_functions': modified_functions,
            'deleted_functions': deleted_functions,
            'unchanged_functions': unchanged_functions
        }
    
    def _extract_all_functions(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取分析结果中的所有函数"""
        all_functions = []
        for file_analysis in analysis.get('files', []):
            if not file_analysis.get('skipped', False):
                all_functions.extend(file_analysis.get('functions', []))
        return all_functions
    
    def _functions_different(self, func1: Dict[str, Any], func2: Dict[str, Any]) -> bool:
        """比较两个函数是否不同"""
        # 简单比较，可以根据需要扩展
        compare_fields = ['args', 'decorators', 'line_start', 'line_end']
        for field in compare_fields:
            if func1.get(field) != func2.get(field):
                return True
        return False
    
    def save_analysis(self, analysis: Dict[str, Any], output_path: str = None) -> str:
        """保存分析结果"""
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = '.claude/reports/function-analysis'
            os.makedirs(output_dir, exist_ok=True)
            output_path = f"{output_dir}/analysis_{timestamp}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        return output_path


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='函数检测和解析工具')
    parser.add_argument('--directory', '-d', default='.', help='要分析的目录路径')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--config', '-c', help='配置文件路径')
    parser.add_argument('--compare', help='与之前的分析结果比较')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger('FunctionDetector').setLevel(logging.DEBUG)
    
    # 初始化检测器
    detector = FunctionDetector(args.config)
    
    # 执行分析
    analysis = detector.analyze_directory(args.directory)
    
    # 如果需要比较
    if args.compare:
        try:
            with open(args.compare, 'r', encoding='utf-8') as f:
                previous_analysis = json.load(f)
            changes = detector.detect_changes(analysis, previous_analysis)
            analysis['changes'] = changes
            
            print(f"发现 {len(changes['new_functions'])} 个新函数")
            print(f"发现 {len(changes['modified_functions'])} 个修改的函数")
            print(f"发现 {len(changes['deleted_functions'])} 个删除的函数")
        except Exception as e:
            print(f"无法加载比较文件: {e}")
    
    # 保存结果
    output_path = detector.save_analysis(analysis, args.output)
    
    # 输出摘要
    summary = analysis['summary']
    print(f"\\n分析完成:")
    print(f"  总文件数: {summary['total_files']}")
    print(f"  已分析文件: {summary['analyzed_files']}")
    print(f"  跳过文件: {summary['skipped_files']}")
    print(f"  总函数数: {summary['total_functions']}")
    print(f"  Python函数: {summary['python_functions']}")
    print(f"  JavaScript函数: {summary['javascript_functions']}")
    print(f"\\n结果已保存到: {output_path}")


if __name__ == '__main__':
    main()