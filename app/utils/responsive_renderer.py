"""
响应式渲染器 - 统一的移动端和桌面端列表渲染服务

功能:
1. 自动检测设备类型并选择对应的渲染方式
2. 支持配置驱动的移动端卡片渲染
3. 智能配置支持：基于桌面端模板自动生成移动端配置
4. 向后兼容现有桌面端模板

使用方式:
```python
from app.utils.responsive_renderer import render_responsive_list

html = render_responsive_list(
    items=items,
    module_name='quotation'
)
```
"""

from flask import render_template, render_template_string, request
from app.utils.mobile_helpers import is_mobile_request
from app.utils.smart_module_configs import get_smart_module_config
import logging

class ResponsiveRenderer:
    """统一的响应式列表渲染器"""
    
    @classmethod
    def render_list_response(cls, items, module_config, **kwargs):
        """
        统一的响应式列表渲染入口
        
        Args:
            items: 数据列表
            module_config: 模块配置字典
            **kwargs: 额外的模板变量
        
        Returns:
            str: 渲染后的HTML字符串
        """
        try:
            if is_mobile_request():
                return cls._render_mobile_cards(items, module_config, **kwargs)
            else:
                return cls._render_desktop_table(items, module_config, **kwargs)
        except Exception as e:
            logging.error(f"响应式渲染失败: {e}")
            return cls._render_error_fallback(str(e), module_config)
    
    @classmethod
    def _render_mobile_cards(cls, items, module_config, **kwargs):
        """
        渲染移动端卡片
        
        Args:
            items: 数据列表
            module_config: 模块配置
            **kwargs: 额外的模板变量
        
        Returns:
            str: 移动端HTML
        """
        # 检查是否使用智能卡片
        use_smart_card = request.args.get('use_smart_card', 'true').lower() == 'true'
        
        if use_smart_card and 'mobile_card' in module_config:
            # 使用智能移动端卡片配置
            return cls._render_smart_mobile_cards(items, module_config['mobile_card'], **kwargs)
        elif 'mobile_template' in module_config:
            # 使用传统移动端模板
            return cls._render_traditional_mobile_template(items, module_config['mobile_template'], **kwargs)
        else:
            # 回退到智能卡片（如果配置了）或错误信息
            if 'mobile_card' in module_config:
                return cls._render_smart_mobile_cards(items, module_config['mobile_card'], **kwargs)
            else:
                logging.warning(f"模块配置缺少移动端配置: {module_config.get('module', 'unknown')}")
                return cls._render_fallback_mobile_cards(items, module_config, **kwargs)
    
    @classmethod
    def _render_desktop_table(cls, items, module_config, **kwargs):
        """
        渲染桌面端表格
        
        Args:
            items: 数据列表  
            module_config: 模块配置
            **kwargs: 额外的模板变量
        
        Returns:
            str: 桌面端HTML
        """
        desktop_template = module_config.get('desktop_template')
        if not desktop_template:
            raise ValueError(f"模块配置缺少 desktop_template: {module_config.get('module', 'unknown')}")
        
        # 合并默认的模板变量
        template_vars = {
            'items': items,
            **kwargs
        }
        
        # 如果配置中有特定的变量名映射，使用它
        items_var_name = module_config.get('items_var_name', 'items')
        template_vars[items_var_name] = items
        
        return render_template(desktop_template, **template_vars)
    
    @classmethod  
    def _render_smart_mobile_cards(cls, items, card_config, **kwargs):
        """
        使用智能卡片配置渲染移动端
        
        Args:
            items: 数据列表
            card_config: 智能卡片配置
            **kwargs: 额外的模板变量
        
        Returns:
            str: 智能卡片HTML
        """
        template_vars = {
            'items': items,
            'card_config': card_config,
            **kwargs
        }
        
        return render_template_string('''
            {% from 'macros/ui_helpers.html' import render_smart_mobile_cards %}
            {{ render_smart_mobile_cards(items, card_config) }}
        ''', **template_vars)
    
    @classmethod
    def _render_traditional_mobile_template(cls, items, mobile_template, **kwargs):
        """
        使用传统移动端模板渲染
        
        Args:
            items: 数据列表
            mobile_template: 移动端模板路径
            **kwargs: 额外的模板变量
        
        Returns:
            str: 传统移动端HTML
        """
        template_vars = {
            'items': items,
            **kwargs
        }
        
        return render_template(mobile_template, **template_vars)
    
    @classmethod
    def _render_fallback_mobile_cards(cls, items, module_config, **kwargs):
        """
        回退的移动端卡片渲染（当配置不完整时）
        
        Args:
            items: 数据列表
            module_config: 模块配置
            **kwargs: 额外的模板变量
        
        Returns:
            str: 简单的回退卡片HTML
        """
        module_name = module_config.get('module', 'generic')
        
        # 生成基础的智能卡片配置
        fallback_config = {
            'module': module_name,
            'title_field': cls._detect_title_field(items),
            'badges': [],
            'details': cls._generate_basic_details(items)
        }
        
        return cls._render_smart_mobile_cards(items, fallback_config, **kwargs)
    
    @classmethod
    def _render_error_fallback(cls, error_message, module_config):
        """
        渲染错误回退内容
        
        Args:
            error_message: 错误信息
            module_config: 模块配置
        
        Returns:
            str: 错误HTML
        """
        if is_mobile_request():
            return f'''
                <div class="mobile-card" data-module="error">
                    <div class="mobile-card-body">
                        <div class="text-center text-danger p-3">
                            <i class="fas fa-exclamation-triangle"></i>
                            <div class="mt-2">渲染失败</div>
                            <div class="text-muted small">{error_message}</div>
                        </div>
                    </div>
                </div>
            '''
        else:
            # 检测桌面端列数
            column_count = cls._detect_column_count(module_config)
            return f'<tr><td colspan="{column_count}" class="text-center text-danger">渲染失败: {error_message}</td></tr>'
    
    @classmethod
    def _detect_column_count(cls, module_config):
        """
        检测桌面端表格列数
        
        Args:
            module_config: 模块配置
        
        Returns:
            int: 列数
        """
        # 如果有智能配置，从中推算列数
        if 'mobile_card' in module_config:
            mobile_card = module_config['mobile_card']
            badges_count = len(mobile_card.get('badges', []))
            details_count = len(mobile_card.get('details', []))
            # 估算列数：标题列 + 徽章列 + 详情列 + 操作列
            return max(4, badges_count + details_count + 2)
        
        # 默认列数
        return 6
    
    @classmethod
    def _detect_title_field(cls, items):
        """
        智能检测标题字段
        
        Args:
            items: 数据列表
        
        Returns:
            dict: 标题字段配置
        """
        if not items:
            return {'field': 'id'}
        
        first_item = items[0]
        
        # 常见的标题字段优先级
        title_fields = [
            'name', 'title', 'company_name', 'project_name', 'product_name',
            'quotation_number', 'order_number', 'authorization_code'
        ]
        
        for field in title_fields:
            if hasattr(first_item, field) and getattr(first_item, field):
                return {'field': field}
        
        # 回退到ID
        return {'field': 'id'}
    
    @classmethod
    def _generate_basic_details(cls, items):
        """
        生成基础的详情配置
        
        Args:
            items: 数据列表
        
        Returns:
            list: 详情配置列表
        """
        if not items:
            return []
        
        first_item = items[0]
        details = []
        
        # 常见的详情字段
        detail_fields = [
            ('owner', '负责人'),
            ('status', '状态'),
            ('created_at', '创建时间'),
            ('updated_at', '更新时间'),
            ('amount', '金额'),
            ('industry', '行业'),
            ('type', '类型')
        ]
        
        for field, label in detail_fields:
            if hasattr(first_item, field):
                detail_config = {'field': field, 'label': label}
                
                # 根据字段类型设置格式
                if 'time' in field or 'date' in field:
                    detail_config['format'] = 'datetime'
                elif field == 'amount':
                    detail_config['format'] = 'currency'
                
                details.append(detail_config)
        
        return details[:6]  # 限制最多6个详情字段


# 创建全局渲染器实例
responsive_renderer = ResponsiveRenderer()

def render_responsive_list(items, module_name=None, module_config=None, **kwargs):
    """
    便利函数：渲染响应式列表（支持智能配置）
    
    Args:
        items: 数据列表
        module_name: 模块名称（优先使用智能配置）
        module_config: 模块配置（传统方式，向后兼容）
        **kwargs: 额外的模板变量
    
    Returns:
        渲染后的HTML字符串
    """
    # 优先使用智能配置
    if module_name:
        smart_config = get_smart_module_config(module_name)
        if smart_config:
            logging.info(f"✅ 使用智能配置渲染模块: {module_name}")
            return responsive_renderer.render_list_response(items, smart_config, **kwargs)
        else:
            logging.warning(f"⚠️ 智能配置不存在，尝试传统配置: {module_name}")
    
    # 回退到传统配置
    if module_config:
        logging.info(f"✅ 使用传统配置渲染")
        return responsive_renderer.render_list_response(items, module_config, **kwargs)
    
    # 尝试从传统注册表获取配置
    if module_name:
        try:
            from app.utils.module_configs import get_module_config
            traditional_config = get_module_config(module_name)
            if traditional_config:
                logging.info(f"✅ 使用传统注册表配置渲染模块: {module_name}")
                return responsive_renderer.render_list_response(items, traditional_config, **kwargs)
        except ImportError:
            logging.warning(f"⚠️ 无法导入传统配置模块")
            pass
    
    # 所有方法都失败
    logging.error(f"❌ 无法找到模块配置: {module_name}")
    return '<tr><td colspan="10" class="text-center py-4 text-danger">配置错误：无法找到模块配置</td></tr>'

def render_responsive_list_legacy(items, module_config, **kwargs):
    """
    便利函数：渲染响应式列表（传统方式，向后兼容）
    
    Args:
        items: 数据列表
        module_config: 模块配置
        **kwargs: 额外的模板变量
    
    Returns:
        渲染后的HTML字符串
    """
    return responsive_renderer.render_list_response(items, module_config, **kwargs)