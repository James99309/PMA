"""
移动端支持工具函数
提供统一的移动端检测和响应式列表渲染功能
"""

from flask import request, render_template


def is_mobile_request():
    """
    统一的移动端检测逻辑 - 与响应式管理器保持一致
    
    优先级:
    1. URL参数 mobile (用于前端窗口宽度检测结果)
    2. User-Agent检测 (兼容真实移动设备)
    
    Returns:
        bool: 如果是移动端请求返回True，否则返回False
    """
    # 检查URL参数（优先级最高，与前端响应式管理器同步）
    mobile_param = request.args.get('mobile', '').lower()
    if mobile_param == 'true':
        return True
    elif mobile_param == 'false':
        return False
    
    # 检查User-Agent（兼容真实移动设备，优先级较低）
    user_agent = request.headers.get('User-Agent', '').lower()
    mobile_keywords = ['mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone']
    
    return any(keyword in user_agent for keyword in mobile_keywords)


def render_responsive_list(items, mobile_template, desktop_template=None, **kwargs):
    """
    统一的响应式列表渲染
    
    Args:
        items: 数据列表
        mobile_template: 移动端模板路径
        desktop_template: 桌面端模板路径（可选）
        **kwargs: 传递给模板的额外参数
    
    Returns:
        str: 渲染后的HTML字符串
    """
    template_kwargs = {'items': items}
    template_kwargs.update(kwargs)
    
    if is_mobile_request():
        return render_template(mobile_template, **template_kwargs)
    elif desktop_template:
        return render_template(desktop_template, **template_kwargs)
    else:
        # 桌面端默认返回表格行片段
        return render_template('macros/default_table_rows.html', **template_kwargs)


def get_device_class():
    """
    获取设备类型CSS类名
    
    Returns:
        str: 设备类型CSS类名
    """
    return 'mobile-device' if is_mobile_request() else 'desktop-device'


def get_responsive_config(base_config):
    """
    根据设备类型调整配置
    
    Args:
        base_config: 基础配置字典
    
    Returns:
        dict: 调整后的配置
    """
    config = base_config.copy()
    
    if is_mobile_request():
        # 移动端调整
        config['device_type'] = 'mobile'
        config['adaptive_width'] = False  # 移动端禁用自适应宽度
        config['adaptive_button_layout'] = True  # 启用自适应按钮布局
    else:
        # 桌面端调整  
        config['device_type'] = 'desktop'
        config['adaptive_width'] = True
        config['adaptive_button_layout'] = True
    
    return config