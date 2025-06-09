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
        'pricing_order': '批价单',
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


def render_standard_tabs(tabs, current_tab, base_url, extra_params=None):
    """渲染标准页签
    
    Args:
        tabs: 页签列表，每个元素为字典 {'key': 'tab_key', 'label': '页签名称', 'icon': 'fas fa-icon'}
        current_tab: 当前激活的页签key
        base_url: 基础URL（不含参数）
        extra_params: 额外的URL参数字典
        
    Returns:
        HTML页签元素字符串
    """
    if extra_params is None:
        extra_params = {}
    
    tab_html = '<ul class="nav nav-tabs card-header-tabs" role="tablist">'
    
    for tab in tabs:
        tab_key = tab['key']
        tab_label = tab['label']
        tab_icon = tab.get('icon', '')
        
        # 构建URL参数
        url_params = {'tab': tab_key}
        url_params.update(extra_params)
        
        # 构建完整URL
        param_str = '&'.join([f'{k}={v}' for k, v in url_params.items()])
        full_url = f'{base_url}?{param_str}'
        
        # 判断是否为当前激活页签
        active_class = 'active' if tab_key == current_tab else ''
        
        # 图标HTML
        icon_html = f'<i class="{tab_icon} me-1"></i>' if tab_icon else ''
        
        tab_html += f'''
        <li class="nav-item">
            <a class="nav-link {active_class}" href="{full_url}" role="tab">
                {icon_html}{tab_label}
            </a>
        </li>
        '''
    
    tab_html += '</ul>'
    return tab_html 