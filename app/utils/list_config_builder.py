# -*- coding: utf-8 -*-
"""
通用列表配置构建器

用于统一构建Tailwind列表页面的配置，包括统计卡片、筛选栏、数据表格等。

使用示例:
    from app.utils.list_config_builder import ListConfigBuilder

    list_config = (
        ListConfigBuilder('project')
        .set_stats(cards=project_stats, display_limit=5)
        .set_filter(
            action_url=url_for('project.list_projects'),
            search_field={'name': 'search', 'value': search, 'placeholder': '搜索项目'},
            filter_fields=filter_fields,
            cols=7
        )
        .set_table(
            columns=columns,
            ajax_endpoint=url_for('project.project_list_ajax'),
            min_width='1400px'
        )
        .set_infinite_scroll(page_size=30)
        .build()
    )
"""

from typing import Dict, Any, List, Optional
from flask_babel import gettext as _


# ============================================================
# 图标和颜色映射
# ============================================================

# FontAwesome 到 Material Symbols 的图标映射
FA_TO_MATERIAL_ICONS = {
    # 项目相关
    'fas fa-project-diagram': 'account_tree',
    'fas fa-chart-line': 'trending_up',
    'fas fa-search': 'search',
    'fas fa-seedling': 'eco',
    'fas fa-clipboard-list': 'assignment',
    'fas fa-gavel': 'gavel',
    'fas fa-trophy': 'emoji_events',
    'fas fa-dollar-sign': 'attach_money',
    'fas fa-handshake': 'handshake',
    'fas fa-times-circle': 'cancel',
    'fas fa-pause-circle': 'pause_circle',

    # 客户相关
    'fas fa-building': 'business',
    'fas fa-users': 'groups',
    'fas fa-user': 'person',
    'fas fa-user-tie': 'badge',
    'fas fa-industry': 'factory',
    'fas fa-globe': 'public',
    'fas fa-map-marker-alt': 'location_on',
    'fas fa-phone': 'phone',
    'fas fa-envelope': 'email',

    # 通用
    'fas fa-check-circle': 'check_circle',
    'fas fa-exclamation-circle': 'error',
    'fas fa-info-circle': 'info',
    'fas fa-warning': 'warning',
    'fas fa-calendar': 'calendar_today',
    'fas fa-clock': 'schedule',
    'fas fa-edit': 'edit',
    'fas fa-trash': 'delete',
    'fas fa-plus': 'add',
    'fas fa-minus': 'remove',
    'fas fa-cog': 'settings',
    'fas fa-download': 'download',
    'fas fa-upload': 'upload',
    'fas fa-file': 'description',
    'fas fa-folder': 'folder',
    'fas fa-star': 'star',
    'fas fa-heart': 'favorite',
    'fas fa-bookmark': 'bookmark',
    'fas fa-tag': 'label',
    'fas fa-tags': 'sell',
    'fas fa-list': 'list',
    'fas fa-th': 'grid_view',
    'fas fa-filter': 'filter_alt',
    'fas fa-sort': 'sort',
    'fas fa-refresh': 'refresh',
    'fas fa-sync': 'sync',
    'fas fa-eye': 'visibility',
    'fas fa-eye-slash': 'visibility_off',
    'fas fa-lock': 'lock',
    'fas fa-unlock': 'lock_open',
    'fas fa-share': 'share',
    'fas fa-link': 'link',
    'fas fa-unlink': 'link_off',
    'fas fa-copy': 'content_copy',
    'fas fa-paste': 'content_paste',
    'fas fa-cut': 'content_cut',
}

# 颜色变体映射 (旧系统 -> Tailwind变体)
COLOR_TO_VARIANT = {
    'primary': 'default',
    'success': 'success',
    'info': 'info',
    'warning': 'warning',
    'danger': 'danger',
    'secondary': 'default',
    'error': 'danger',
    'light': 'default',
    'dark': 'default',
}


def convert_icon(fa_icon: str, default: str = 'analytics') -> str:
    """将FontAwesome图标转换为Material Symbols图标"""
    return FA_TO_MATERIAL_ICONS.get(fa_icon, default)


def convert_color(color: str, default: str = 'default') -> str:
    """将颜色名称转换为Tailwind变体"""
    return COLOR_TO_VARIANT.get(color, default)


# ============================================================
# 列表配置构建器
# ============================================================

class ListConfigBuilder:
    """
    通用列表配置构建器

    支持链式调用构建完整的列表页面配置。
    """

    def __init__(self, module_name: str):
        """
        初始化构建器

        Args:
            module_name: 模块名称 (如 'project', 'customer')
        """
        self.module_name = module_name
        self.config = {
            'module_name': module_name,
            'stats': {'cards': [], 'display_limit': 4},
            'filter_config': {},
            'table': {'columns': []},
            'infinite_scroll': {'enabled': True, 'page_size': 30},
            'actions': []
        }

    def set_stats(
        self,
        cards: List[Dict[str, Any]],
        display_limit: int = 4,
        auto_convert: bool = True
    ) -> 'ListConfigBuilder':
        """
        设置统计卡片配置

        Args:
            cards: 统计卡片列表
            display_limit: 显示的卡片数量限制
            auto_convert: 是否自动转换图标和颜色

        卡片格式:
            {
                'title': '标题',
                'value': 100,
                'unit': '个',
                'icon': 'fas fa-project-diagram',  # 或 Material Symbols
                'color': 'primary'  # 或 Tailwind变体
            }
        """
        if auto_convert:
            converted_cards = []
            for card in cards:
                converted = card.copy()
                if 'icon' in converted and converted['icon'].startswith('fas '):
                    converted['icon'] = convert_icon(converted['icon'])
                if 'color' in converted:
                    converted['variant'] = convert_color(converted['color'])
                converted_cards.append(converted)
            cards = converted_cards

        self.config['stats'] = {
            'cards': cards,
            'display_limit': display_limit
        }
        return self

    def set_filter(
        self,
        action_url: str,
        search_field: Optional[Dict[str, Any]] = None,
        filter_fields: Optional[List[Dict[str, Any]]] = None,
        cols: int = 5,
        form_id: str = 'filterForm'
    ) -> 'ListConfigBuilder':
        """
        设置筛选栏配置

        Args:
            action_url: 表单提交URL
            search_field: 搜索字段配置
            filter_fields: 筛选字段列表
            cols: 列数
            form_id: 表单ID

        搜索字段格式:
            {
                'name': 'search',
                'label': '搜索',
                'placeholder': '搜索提示',
                'value': ''
            }

        筛选字段格式:
            {
                'name': 'owner_id',
                'label': '负责人',
                'type': 'select',
                'options': [{'value': '1', 'label': '张三'}],
                'value': ''
            }
        """
        self.config['filter_config'] = {
            'action_url': action_url,
            'form_id': form_id,
            'search_field': search_field or {
                'name': 'search',
                'label': _('搜索'),
                'placeholder': _('输入关键词搜索'),
                'value': ''
            },
            'filter_fields': filter_fields or [],
            'cols': cols
        }
        return self

    def set_table(
        self,
        columns: List[Dict[str, Any]],
        ajax_endpoint: str,
        rows_template: Optional[str] = None,
        table_id: Optional[str] = None,
        min_width: str = '900px',
        max_height: str = 'calc(100vh - 420px)',
        min_height: str = '400px',
        show_loading: bool = True
    ) -> 'ListConfigBuilder':
        """
        设置数据表格配置

        Args:
            columns: 列配置列表
            ajax_endpoint: AJAX加载端点
            rows_template: 行模板路径
            table_id: 表格ID
            min_width: 最小宽度
            max_height: 最大高度
            min_height: 最小高度
            show_loading: 是否显示加载状态

        列格式:
            {
                'key': 'project_name',
                'label': '项目名称',
                'sortable': True,
                'width': '200px'
            }
        """
        if table_id is None:
            table_id = f'{self.module_name}Table'

        if rows_template is None:
            rows_template = f'{self.module_name}/tw_list_rows.html'

        self.config['table'] = {
            'columns': columns,
            'ajax_endpoint': ajax_endpoint,
            'rows_template': rows_template,
            'table_id': table_id,
            'min_width': min_width,
            'max_height': max_height,
            'min_height': min_height,
            'show_loading': show_loading
        }
        return self

    def set_infinite_scroll(
        self,
        enabled: bool = True,
        page_size: int = 30
    ) -> 'ListConfigBuilder':
        """
        设置无限滚动配置

        Args:
            enabled: 是否启用
            page_size: 每页数量
        """
        self.config['infinite_scroll'] = {
            'enabled': enabled,
            'page_size': page_size
        }
        return self

    def set_actions(
        self,
        actions: List[Dict[str, Any]]
    ) -> 'ListConfigBuilder':
        """
        设置操作按钮配置

        Args:
            actions: 操作按钮列表

        按钮格式:
            {
                'label': '创建项目',
                'url': url_for('project.add_project'),
                'icon': 'add',
                'variant': 'primary',  # 'primary', 'secondary', 'danger'
                'permission': ('project', 'create')  # 可选
            }
        """
        self.config['actions'] = actions
        return self

    def build(self) -> Dict[str, Any]:
        """
        构建最终配置

        Returns:
            完整的列表配置字典
        """
        return self.config


# ============================================================
# 便捷函数
# ============================================================

def create_stat_card(
    title: str,
    value: Any,
    unit: str = '',
    icon: str = 'analytics',
    variant: str = 'default'
) -> Dict[str, Any]:
    """
    创建统计卡片配置

    Args:
        title: 标题
        value: 值
        unit: 单位
        icon: 图标 (Material Symbols)
        variant: 变体 ('default', 'success', 'info', 'warning', 'danger')

    Returns:
        卡片配置字典
    """
    return {
        'title': title,
        'value': value,
        'unit': unit,
        'icon': icon,
        'variant': variant
    }


def create_filter_field(
    name: str,
    label: str,
    field_type: str = 'select',
    options: Optional[List[Dict[str, str]]] = None,
    value: str = '',
    placeholder: str = ''
) -> Dict[str, Any]:
    """
    创建筛选字段配置

    Args:
        name: 字段名
        label: 标签
        field_type: 类型 ('select', 'text', 'date', 'checkbox')
        options: 选项列表 (仅select类型)
        value: 当前值
        placeholder: 占位符

    Returns:
        字段配置字典
    """
    field = {
        'name': name,
        'label': label,
        'type': field_type,
        'value': value,
        'placeholder': placeholder
    }
    if options is not None:
        field['options'] = options
    return field


def create_table_column(
    key: str,
    label: str,
    sortable: bool = False,
    width: Optional[str] = None,
    align: str = 'left'
) -> Dict[str, Any]:
    """
    创建表格列配置

    Args:
        key: 列键名
        label: 列标签
        sortable: 是否可排序
        width: 列宽度
        align: 对齐方式 ('left', 'center', 'right')

    Returns:
        列配置字典
    """
    column = {
        'key': key,
        'label': label,
        'sortable': sortable,
        'align': align
    }
    if width is not None:
        column['width'] = width
    return column


def create_action_button(
    label: str,
    url: str,
    icon: str = 'add',
    variant: str = 'primary',
    permission: Optional[tuple] = None
) -> Dict[str, Any]:
    """
    创建操作按钮配置

    Args:
        label: 按钮标签
        url: 按钮链接
        icon: 图标 (Material Symbols)
        variant: 变体 ('primary', 'secondary', 'danger')
        permission: 权限元组 (module, action)

    Returns:
        按钮配置字典
    """
    button = {
        'label': label,
        'url': url,
        'icon': icon,
        'variant': variant
    }
    if permission is not None:
        button['permission'] = permission
    return button
