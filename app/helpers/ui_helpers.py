from flask import url_for
import datetime

def render_action_button(text, url, btn_class="btn-primary", icon=None, small=False):
    """渲染操作按钮
    
    Args:
        text: 按钮文本
        url: 按钮链接
        btn_class: 按钮样式类
        icon: 图标类名（如"fa-eye"）
        small: 是否使用小按钮
        
    Returns:
        HTML按钮元素字符串
    """
    size_class = "btn-sm" if small else ""
    icon_html = f'<i class="fas {icon} mr-1"></i>' if icon else ""
    
    return f'''
    <a href="{url}" class="btn {btn_class} {size_class}">
        {icon_html}{text}
    </a>
    '''

def render_filter_button(text, type="submit", btn_class="btn-primary", icon=None, small=True):
    """渲染筛选按钮
    
    Args:
        text: 按钮文本
        type: 按钮类型 (submit/button/reset)
        btn_class: 按钮样式类
        icon: 图标类名（如"fa-filter"）
        small: 是否使用小按钮
        
    Returns:
        HTML按钮元素字符串
    """
    size_class = "btn-sm" if small else ""
    icon_html = f'<i class="fas {icon} me-1"></i>' if icon else ""
    
    return f'''
    <button type="{type}" class="btn {btn_class} {size_class}">
        {icon_html}{text}
    </button>
    '''

def render_user_badge(user, badge_class="bg-info"):
    """渲染用户徽章
    
    Args:
        user: 用户对象或用户名
        badge_class: 徽章样式类
        
    Returns:
        HTML徽章元素字符串
    """
    if not user:
        return '<span class="badge bg-secondary">无</span>'
    
    # 如果是用户对象，获取真实姓名或用户名
    if hasattr(user, 'real_name') and user.real_name:
        display_name = user.real_name
    elif hasattr(user, 'name'):
        display_name = user.name
    elif hasattr(user, 'username'):
        display_name = user.username
    else:
        display_name = str(user)
    
    return f'<span class="badge {badge_class}">{display_name}</span>'


def format_datetime(dt):
    """格式化日期时间
    
    Args:
        dt: datetime对象
        
    Returns:
        格式化的日期时间字符串
    """
    if not dt:
        return ""
    
    return dt.strftime("%Y-%m-%d %H:%M")


def get_object_type_display(object_type):
    """获取对象类型的显示名称
    
    Args:
        object_type: 对象类型代码
        
    Returns:
        对象类型的中文显示名称
    """
    type_map = {
        'project': '项目',
        'quotation': '报价单',
        'customer': '客户',
    }
    
    return type_map.get(object_type, object_type)

def get_user_display_name(user):
    """获取用户显示名称，优先显示真实姓名
    
    Args:
        user: 用户对象
        
    Returns:
        用户显示名称
    """
    if not user:
        return "未指定"
    
    if hasattr(user, 'real_name') and user.real_name:
        return user.real_name
    elif hasattr(user, 'name'):
        return user.name
    elif hasattr(user, 'username'):
        return user.username
    else:
        return str(user) 