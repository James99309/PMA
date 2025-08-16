"""
桌面端模板解析器 - 自动提取字段和渲染器信息

功能:
1. 解析桌面端模板文件，提取字段定义和渲染器
2. 分析条件渲染逻辑和链接结构
3. 生成字段元数据供移动端使用
4. 保持桌面端和移动端渲染的一致性

使用方式:
```python
from app.utils.template_parser import DesktopTemplateParser

parser = DesktopTemplateParser()
fields = parser.parse_template('quotation/quotation_rows.html')
```
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class DesktopTemplateParser:
    """桌面端模板解析器"""
    
    def __init__(self, templates_dir: str = None):
        """
        初始化模板解析器
        
        Args:
            templates_dir: 模板目录路径，默认为app/templates
        """
        if templates_dir is None:
            # 获取当前文件的目录，然后找到templates目录
            current_dir = Path(__file__).parent
            self.templates_dir = current_dir.parent / 'templates'
        else:
            self.templates_dir = Path(templates_dir)
    
    def parse_template(self, template_path: str) -> Dict[str, Any]:
        """
        解析桌面端模板文件
        
        Args:
            template_path: 模板文件路径（相对于templates目录）
        
        Returns:
            字段元数据字典
        """
        try:
            full_path = self.templates_dir / template_path
            if not full_path.exists():
                logger.error(f"模板文件不存在: {full_path}")
                return {}
            
            with open(full_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            return self._analyze_template_content(template_content, template_path)
            
        except Exception as e:
            logger.error(f"解析模板文件失败 {template_path}: {e}")
            return {}
    
    def _analyze_template_content(self, content: str, template_path: str) -> Dict[str, Any]:
        """
        分析模板内容，提取字段信息
        
        Args:
            content: 模板内容
            template_path: 模板路径
        
        Returns:
            解析结果
        """
        result = {
            'template_path': template_path,
            'fields': [],
            'imports': [],
            'variables': [],
            'title_field': None,
            'link_patterns': []
        }
        
        # 1. 提取import语句，获取可用的渲染器
        result['imports'] = self._extract_imports(content)
        
        # 2. 提取变量循环（如{% for quotation in quotations %}）
        result['variables'] = self._extract_loop_variables(content)
        
        # 3. 提取字段定义和渲染器调用
        result['fields'] = self._extract_fields(content)
        
        # 4. 识别标题字段（通常是第一个带链接的字段）
        result['title_field'] = self._identify_title_field(result['fields'])
        
        # 5. 提取链接模式
        result['link_patterns'] = self._extract_link_patterns(content)
        
        return result
    
    def _extract_imports(self, content: str) -> List[Dict[str, Any]]:
        """提取import语句，获取可用的渲染器"""
        imports = []
        
        # 匹配 {% from 'macros/ui_helpers.html' import ... %}
        from_pattern = r'{%\s*from\s+[\'"]([^\'"]+)[\'"]\s+import\s+([^%]+)\s*%}'
        for match in re.finditer(from_pattern, content):
            module = match.group(1)
            imports_str = match.group(2)
            
            # 解析导入的函数名
            imported_functions = [func.strip() for func in imports_str.split(',')]
            
            imports.append({
                'module': module,
                'functions': imported_functions
            })
        
        # 匹配 {% import 'macros/ui_helpers.html' as ui %}
        import_pattern = r'{%\s*import\s+[\'"]([^\'"]+)[\'"]\s+as\s+(\w+)\s*%}'
        for match in re.finditer(import_pattern, content):
            module = match.group(1)
            alias = match.group(2)
            
            imports.append({
                'module': module,
                'alias': alias,
                'type': 'import_as'
            })
        
        return imports
    
    def _extract_loop_variables(self, content: str) -> List[str]:
        """提取循环变量名"""
        variables = []
        
        # 匹配 {% for variable in variables %}
        pattern = r'{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%}'
        for match in re.finditer(pattern, content):
            item_var = match.group(1)  # 单个项目变量名，如quotation
            list_var = match.group(2)  # 列表变量名，如quotations
            variables.append({
                'item': item_var,
                'list': list_var
            })
        
        return variables
    
    def _extract_fields(self, content: str) -> List[Dict[str, Any]]:
        """提取字段定义和渲染器调用"""
        fields = []
        
        # 按<td>标签分割内容来分析每个字段
        td_pattern = r'<td[^>]*>(.*?)</td>'
        td_matches = re.finditer(td_pattern, content, re.DOTALL)
        
        column_index = 0
        for match in td_matches:
            td_content = match.group(1).strip()
            if not td_content:
                continue
            
            field_info = self._analyze_field_content(td_content, column_index)
            if field_info:
                fields.append(field_info)
            
            column_index += 1
        
        return fields
    
    def _analyze_field_content(self, td_content: str, column_index: int) -> Optional[Dict[str, Any]]:
        """分析单个字段的内容"""
        field_info = {
            'column_index': column_index,
            'raw_content': td_content,
            'field_name': None,
            'renderer': None,
            'has_link': False,
            'link_url': None,
            'conditions': [],
            'is_nested': False,
            'format_type': None
        }
        
        # 1. 检查是否有链接
        link_match = re.search(r'<a[^>]+href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>', td_content, re.DOTALL)
        if link_match:
            field_info['has_link'] = True
            field_info['link_url'] = link_match.group(1)
            link_content = link_match.group(2)
            # 分析链接内容中的渲染器调用
            self._extract_renderer_call(link_content, field_info)
        
        # 2. 提取渲染器调用
        if not field_info['renderer']:
            self._extract_renderer_call(td_content, field_info)
        
        # 3. 提取直接字段访问（如{{ quotation.project_name }}）
        if not field_info['field_name']:
            direct_field_match = re.search(r'{{\s*(\w+)\.(\w+)\s*}}', td_content)
            if direct_field_match:
                object_name = direct_field_match.group(1)
                field_name = direct_field_match.group(2)
                field_info['field_name'] = field_name
                field_info['object_name'] = object_name
        
        # 4. 检查条件语句
        field_info['conditions'] = self._extract_conditions(td_content)
        
        # 5. 检查嵌套对象访问（如quotation.project.project_name）
        nested_match = re.search(r'(\w+)\.(\w+)\.(\w+)', td_content)
        if nested_match:
            field_info['is_nested'] = True
            field_info['object_name'] = nested_match.group(1)
            field_info['nested_object'] = nested_match.group(2)
            field_info['nested_field'] = nested_match.group(3)
        
        # 6. 检查格式化类型（基于CSS类和内容推断）
        if 'text-end' in td_content:
            field_info['format_type'] = 'currency'
        elif re.search(r'strftime|datetime', td_content):
            field_info['format_type'] = 'date'
        
        return field_info if field_info['field_name'] or field_info['renderer'] else None
    
    def _extract_renderer_call(self, content: str, field_info: Dict[str, Any]):
        """提取渲染器调用信息"""
        # 改进的正则表达式，支持带条件的渲染器调用
        # 匹配 {{ render_function(args) }} 和 {{ render_function(args) if condition else ... }}
        renderer_pattern = r'{{\s*(render_\w+)\s*\(([^)]+)\)'
        match = re.search(renderer_pattern, content)
        
        if match:
            field_info['renderer'] = match.group(1)
            args_str = match.group(2).strip()
            
            # 从参数中提取字段信息
            field_match = re.search(r'(\w+)\.(\w+)', args_str)
            if field_match:
                object_name = field_match.group(1)
                field_name = field_match.group(2)
                field_info['field_name'] = field_name
                field_info['object_name'] = object_name
                
                # 提取完整的渲染器参数
                field_info['renderer_args'] = [args_str]
                
                # 检查是否有更多参数（用逗号分隔）
                if ',' in args_str:
                    field_info['renderer_args'] = [arg.strip() for arg in args_str.split(',')]
        
        # 如果第一个模式没匹配到，尝试更严格的模式（向后兼容）
        if not field_info.get('renderer'):
            fallback_pattern = r'{{\s*(render_\w+)\s*\([^)]*(\w+)\.(\w+)[^)]*\)\s*}}'
            fallback_match = re.search(fallback_pattern, content)
            
            if fallback_match:
                field_info['renderer'] = fallback_match.group(1)
                object_name = fallback_match.group(2)
                field_name = fallback_match.group(3)
                field_info['field_name'] = field_name
                field_info['object_name'] = object_name
                
                # 提取渲染器参数
                full_call = fallback_match.group(0)
                args_match = re.search(r'\((.*?)\)', full_call)
                if args_match:
                    field_info['renderer_args'] = [arg.strip() for arg in args_match.group(1).split(',')]
    
    def _extract_conditions(self, content: str) -> List[Dict[str, Any]]:
        """提取条件语句"""
        conditions = []
        
        # 匹配 {% if condition %}
        if_pattern = r'{%\s*if\s+([^%]+)\s*%}'
        for match in re.finditer(if_pattern, content):
            condition = match.group(1).strip()
            conditions.append({
                'type': 'if',
                'condition': condition
            })
        
        # 匹配 {% else %}
        if re.search(r'{%\s*else\s*%}', content):
            conditions.append({
                'type': 'else'
            })
        
        return conditions
    
    def _identify_title_field(self, fields: List[Dict[str, Any]]) -> Optional[str]:
        """识别标题字段（通常是第一个带链接的字段）"""
        for field in fields:
            if field.get('has_link') and field.get('field_name'):
                return field['field_name']
        
        # 如果没有带链接的字段，返回第一个字段
        if fields:
            return fields[0].get('field_name')
        
        return None
    
    def _extract_link_patterns(self, content: str) -> List[Dict[str, Any]]:
        """提取链接模式"""
        links = []
        
        # 匹配 href="{{ url_for(...) }}"
        url_for_pattern = r'href=[\'"]{{\\s*url_for\\s*\\([^)]+\\)\\s*}}[\'"]'
        for match in re.finditer(url_for_pattern, content):
            links.append({
                'pattern': match.group(0),
                'type': 'url_for'
            })
        
        return links
    
    def generate_mobile_config(self, template_path: str, priority_fields: List[str] = None, 
                             badge_fields: List[str] = None, exclude_fields: List[str] = None) -> Dict[str, Any]:
        """
        基于桌面端模板生成移动端配置
        
        Args:
            template_path: 桌面端模板路径
            priority_fields: 优先显示的字段列表
            badge_fields: 作为徽章显示的字段列表
            exclude_fields: 排除的字段列表
        
        Returns:
            移动端卡片配置
        """
        parsed = self.parse_template(template_path)
        if not parsed or not parsed['fields']:
            return {}
        
        priority_fields = priority_fields or []
        badge_fields = badge_fields or []
        exclude_fields = exclude_fields or []
        
        # 生成配置
        config = {
            'source_template': template_path,
            'title_field': {'field': parsed['title_field']} if parsed['title_field'] else None,
            'badges': [],
            'details': []
        }
        
        # 处理字段
        for field in parsed['fields']:
            field_name = field.get('field_name')
            if not field_name or field_name in exclude_fields:
                continue
            
            # 构建字段配置
            field_config = {
                'field': field_name,
                'label': self._field_name_to_label(field_name)
            }
            
            # 添加渲染器
            if field.get('renderer'):
                field_config['renderer'] = field['renderer']
            
            # 添加格式化
            if field.get('format_type'):
                field_config['format'] = field['format_type']
            
            # 决定字段位置：徽章还是详情
            if field_name in badge_fields:
                config['badges'].append(field_config)
            else:
                config['details'].append(field_config)
        
        # 根据优先级排序
        if priority_fields:
            config['details'].sort(key=lambda x: priority_fields.index(x['field']) 
                                  if x['field'] in priority_fields else 999)
        
        return config
    
    def _field_name_to_label(self, field_name: str) -> str:
        """将字段名转换为显示标签"""
        # 基本的字段名到中文标签的映射
        field_labels = {
            'quotation_number': '报价单号',
            'owner': '负责人',
            'project_name': '项目名称',
            'amount': '金额',
            'current_stage': '当前阶段',
            'project_type': '项目类型',
            'updated_at': '更新时间',
            'created_at': '创建时间',
            'company_name': '公司名称',
            'status': '状态',
            'approval_status': '审核状态',
            'product_name': '产品名称',
            'product_model': '产品型号',
            'quantity': '数量',
            'unit_price': '单价',
            'total_price': '总价',
            'expense_number': '报销单号',
            'title': '标题',
            'customer_name': '客户名称',
            'contact_name': '联系人',
            'currency': '币种'
        }
        
        return field_labels.get(field_name, field_name)


# 创建全局解析器实例
template_parser = DesktopTemplateParser()

def parse_desktop_template(template_path: str) -> Dict[str, Any]:
    """
    便利函数：解析桌面端模板
    
    Args:
        template_path: 模板路径
    
    Returns:
        解析结果
    """
    return template_parser.parse_template(template_path)

def generate_mobile_config_from_template(template_path: str, **kwargs) -> Dict[str, Any]:
    """
    便利函数：从桌面端模板生成移动端配置
    
    Args:
        template_path: 模板路径
        **kwargs: 其他配置参数
    
    Returns:
        移动端配置
    """
    return template_parser.generate_mobile_config(template_path, **kwargs)