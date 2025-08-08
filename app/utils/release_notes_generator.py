#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用户友好的版本升级说明生成器

此模块提供：
1. 基于文件变更分析功能改进
2. 生成结构化的升级说明
3. 支持中英文双语说明
4. 用户友好的格式化输出
"""

import os
import re
import logging
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class FeatureChange:
    """功能变更数据类"""
    module: str
    type: str  # 'feature', 'fix', 'improvement', 'ui'
    title: str
    description: str
    impact: str  # 'major', 'minor', 'patch'
    files: List[str]

class ReleaseNotesGenerator:
    """升级说明生成器"""
    
    def __init__(self):
        self.module_mapping = {
            # 前端文件映射
            'expense': '报销管理',
            'customer': '客户管理', 
            'project': '项目管理',
            'quotation': '报价管理',
            'product': '产品管理',
            'user': '用户管理',
            'version': '版本管理',
            'main': '系统主页',
            'admin': '系统管理',
            
            # 后端文件映射
            'views/expense': '报销管理',
            'views/customer': '客户管理',
            'views/project': '项目管理', 
            'views/quotation': '报价管理',
            'views/product': '产品管理',
            'views/user': '用户管理',
            'views/main': '系统主页',
            'views/version': '版本管理',
            
            # 特殊文件
            'static/js': '前端交互',
            'static/css': '界面样式',
            'templates/macros': '通用组件',
            'templates/base.html': '页面基础',
            'translations': '国际化',
            'utils': '系统工具',
        }
        
        self.change_patterns = {
            # 功能关键词
            'feature': [
                r'新增|添加|增加|支持|实现',
                r'feat|feature|add',
                r'新功能|功能增强|enhancement'
            ],
            # 修复关键词  
            'fix': [
                r'修复|修正|解决|问题|错误',
                r'fix|bug|issue|error',
                r'故障|异常|崩溃'
            ],
            # 界面优化
            'ui': [
                r'界面|UI|样式|布局|显示',
                r'优化|美化|调整',
                r'徽章|组件|模板'
            ],
            # 性能改进
            'improvement': [
                r'优化|改进|提升|完善',
                r'performance|optimize|improve',
                r'重构|升级'
            ]
        }
    
    def analyze_git_changes(self, from_commit: Optional[str] = None) -> List[FeatureChange]:
        """分析Git变更生成功能变更列表"""
        try:
            # 获取变更的文件列表
            if from_commit:
                cmd = ['git', 'diff', '--name-status', f'{from_commit}..HEAD']
            else:
                cmd = ['git', 'diff', '--name-status', '--cached']
                if not subprocess.run(cmd, capture_output=True).stdout.strip():
                    cmd = ['git', 'status', '--porcelain']
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Git命令执行失败: {result.stderr}")
                return []
            
            changes = []
            changed_files = self._parse_git_output(result.stdout)
            
            # 按模块分组分析变更
            module_changes = self._group_changes_by_module(changed_files)
            
            for module, files in module_changes.items():
                change = self._analyze_module_changes(module, files)
                if change:
                    changes.append(change)
            
            return changes
            
        except Exception as e:
            logger.error(f"分析Git变更失败: {str(e)}")
            return []
    
    def _parse_git_output(self, output: str) -> List[Tuple[str, str]]:
        """解析Git输出格式"""
        changes = []
        for line in output.strip().split('\\n'):
            if not line:
                continue
            
            # Git diff格式: M filename 或 A filename
            if line.startswith(('M', 'A', 'D', 'R', '??')):
                parts = line.split('\\t') if '\\t' in line else line.split()
                if len(parts) >= 2:
                    status = parts[0].strip()
                    filename = parts[-1].strip()
                    changes.append((status, filename))
            
        return changes
    
    def _group_changes_by_module(self, changed_files: List[Tuple[str, str]]) -> Dict[str, List[str]]:
        """按模块分组变更文件"""
        module_files = {}
        
        for status, filepath in changed_files:
            if filepath.startswith('.') or filepath in ['README.md', 'requirements.txt']:
                continue
                
            module = self._detect_module_from_path(filepath)
            if module not in module_files:
                module_files[module] = []
            module_files[module].append(filepath)
        
        return module_files
    
    def _detect_module_from_path(self, filepath: str) -> str:
        """从文件路径检测所属模块"""
        # 标准化路径
        filepath = filepath.replace('\\\\', '/')
        
        # 优先匹配具体路径模式
        for pattern, module in self.module_mapping.items():
            if pattern in filepath:
                return module
        
        # 基于文件名模式
        filename = os.path.basename(filepath)
        for pattern, module in self.module_mapping.items():
            if pattern in filename:
                return module
        
        return '系统核心'
    
    def _analyze_module_changes(self, module: str, files: List[str]) -> Optional[FeatureChange]:
        """分析模块级别的变更"""
        try:
            # 分析文件内容获取变更详情
            change_details = []
            change_types = set()
            
            for filepath in files[:3]:  # 限制分析前3个文件避免过度分析
                if os.path.exists(filepath):
                    detail = self._analyze_file_changes(filepath)
                    if detail:
                        change_details.append(detail)
                        change_types.add(detail['type'])
            
            if not change_details:
                return None
            
            # 合并分析结果
            primary_type = self._determine_primary_change_type(change_types)
            title, description = self._generate_change_description(module, change_details, primary_type)
            impact = self._determine_impact_level(change_details, primary_type)
            
            return FeatureChange(
                module=module,
                type=primary_type,
                title=title,
                description=description,
                impact=impact,
                files=files
            )
            
        except Exception as e:
            logger.error(f"分析模块变更失败 {module}: {str(e)}")
            return None
    
    def _analyze_file_changes(self, filepath: str) -> Optional[Dict]:
        """分析单个文件的变更内容"""
        try:
            # 获取文件的Git diff
            result = subprocess.run(
                ['git', 'diff', 'HEAD~1', filepath],
                capture_output=True, text=True
            )
            
            if result.returncode != 0:
                return None
            
            diff_content = result.stdout
            return self._extract_change_info_from_diff(diff_content, filepath)
            
        except Exception as e:
            logger.error(f"分析文件变更失败 {filepath}: {str(e)}")
            return None
    
    def _extract_change_info_from_diff(self, diff_content: str, filepath: str) -> Optional[Dict]:
        """从diff内容提取变更信息"""
        # 分析添加的行（+开头）
        added_lines = []
        for line in diff_content.split('\\n'):
            if line.startswith('+') and not line.startswith('+++'):
                added_lines.append(line[1:].strip())
        
        # 基于文件类型和变更内容推断变更类型
        change_type = 'improvement'  # 默认
        key_changes = []
        
        # 分析关键变更
        for line in added_lines[:10]:  # 分析前10行
            for type_key, patterns in self.change_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        change_type = type_key
                        key_changes.append(line)
                        break
        
        if not key_changes:
            return None
            
        return {
            'type': change_type,
            'changes': key_changes,
            'file': filepath
        }
    
    def _determine_primary_change_type(self, change_types: set) -> str:
        """确定主要变更类型"""
        # 优先级: feature > fix > ui > improvement
        priority = ['feature', 'fix', 'ui', 'improvement']
        
        for change_type in priority:
            if change_type in change_types:
                return change_type
        
        return 'improvement'
    
    def _generate_change_description(self, module: str, change_details: List[Dict], change_type: str) -> Tuple[str, str]:
        """生成变更描述"""
        # 根据模块和变更类型生成标题和描述
        type_titles = {
            'feature': f'{module}功能增强',
            'fix': f'{module}问题修复', 
            'ui': f'{module}界面优化',
            'improvement': f'{module}性能改进'
        }
        
        title = type_titles.get(change_type, f'{module}更新')
        
        # 生成描述
        descriptions = []
        for detail in change_details:
            for change in detail['changes'][:2]:  # 每个文件最多取2个关键变更
                if len(change) > 20:  # 过滤掉太短的变更
                    descriptions.append(f"- {change[:100]}")  # 限制长度
        
        description = '\\n'.join(descriptions) if descriptions else f'{module}模块相关更新'
        
        return title, description
    
    def _determine_impact_level(self, change_details: List[Dict], change_type: str) -> str:
        """确定影响级别"""
        # 基于变更类型和文件数量确定影响级别
        file_count = len(change_details)
        
        if change_type == 'feature':
            return 'minor' if file_count > 2 else 'patch'
        elif change_type == 'fix':
            return 'patch'
        else:
            return 'patch'
    
    def generate_release_notes(self, version: str, changes: List[FeatureChange]) -> str:
        """生成格式化的升级说明"""
        # 获取当前日期
        today = datetime.now().strftime('%Y年%m月%d日')
        
        # 按类型分组变更
        grouped_changes = {
            'feature': [],
            'fix': [],
            'ui': [],
            'improvement': []
        }
        
        for change in changes:
            if change.type in grouped_changes:
                grouped_changes[change.type].append(change)
        
        # 生成Markdown格式的升级说明
        notes = f"""# PMA 项目管理系统 {version} 升级说明

## 📅 发布信息
- **版本号**: {version}
- **发布日期**: {today}
- **升级类型**: {'功能增强版本' if grouped_changes['feature'] else '问题修复版本' if grouped_changes['fix'] else '优化改进版本'}

---

## 🎯 本次升级亮点
"""
        
        # 添加各类型变更
        type_sections = {
            'feature': ('✨ **新功能增强**', '新增功能和特性'),
            'fix': ('🔧 **问题修复**', '修复的问题和错误'),
            'ui': ('🎨 **界面优化**', '用户界面改进'),
            'improvement': ('⚡ **性能改进**', '系统优化和性能提升')
        }
        
        for change_type, (section_title, section_desc) in type_sections.items():
            if grouped_changes[change_type]:
                notes += f"\n### {section_title}\n"
                for change in grouped_changes[change_type]:
                    notes += f"- **{change.title}**: {change.description[:200]}\n"
        
        # 添加详细说明部分
        notes += """
---

## 📋 详细功能说明
"""
        
        # 按模块添加详细说明
        modules = set(change.module for change in changes)
        for module in sorted(modules):
            module_changes = [c for c in changes if c.module == module]
            if module_changes:
                notes += f"\n### 🗂️ **{module}模块**\n"
                for change in module_changes:
                    notes += f"- {change.description}\n"
        
        # 添加技术信息
        notes += f"""
---

## 🔧 技术改进

### **文件变更统计**
- 修改文件: {len([c for c in changes if any('M' in str(f) for f in c.files)])} 个
- 新增文件: {len([c for c in changes if any('A' in str(f) for f in c.files)])} 个
- 涉及模块: {len(modules)} 个

---

## 🚀 升级建议

### **推荐升级场景**
"""
        
        # 基于变更类型添加升级建议
        if grouped_changes['fix']:
            notes += "- ✅ **问题修复**: 建议立即升级解决已知问题\n"
        if grouped_changes['feature']:
            notes += "- ✅ **功能增强**: 推荐升级获得新功能特性\n"
        if grouped_changes['ui']:
            notes += "- ✅ **界面优化**: 提升用户体验，推荐升级\n"
        
        notes += f"""
---

*PMA开发团队*  
*{today}*
"""
        
        return notes

def create_release_notes_for_version(version: str, from_commit: Optional[str] = None) -> str:
    """为指定版本创建升级说明"""
    generator = ReleaseNotesGenerator()
    changes = generator.analyze_git_changes(from_commit)
    return generator.generate_release_notes(version, changes)

# 使用示例和测试函数
if __name__ == "__main__":
    # 测试生成当前版本的升级说明
    notes = create_release_notes_for_version("v1.3.6")
    print(notes)