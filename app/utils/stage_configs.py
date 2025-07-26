"""
阶段配置文件
统一管理不同业务场景的阶段定义、颜色、标签等配置
"""

from app.utils.dictionary_helpers import project_stage_label

# 项目阶段配置 - 与现有项目管理模块保持一致
PROJECT_STAGE_CONFIG = {
    'stage_field': 'current_stage',
    'stage_order': [
        'discover', 'embed', 'pre_tender', 'tendering', 
        'awarded', 'quoted', 'signed', 'lost', 'paused', 'unset'
    ],
    'stage_labels': {
        'discover': '发现',
        'embed': '植入', 
        'pre_tender': '招标前',
        'tendering': '招标中',
        'awarded': '中标',
        'quoted': '批价',
        'signed': '签约',
        'lost': '失败',
        'paused': '搁置',
        'unset': '未设置'
    },
    # 颜色配置 - 与徽章样式保持一致
    'stage_colors': {
        'quantity': {
            'discover': 'rgba(2, 103, 5, 0.05)',      # 026705 透明度 5%
            'embed': 'rgba(2, 103, 5, 0.2)',         # 026705 透明度 20%
            'pre_tender': 'rgba(2, 103, 5, 0.3)',    # 026705 透明度 30%
            'tendering': 'rgba(2, 103, 5, 0.5)',     # 026705 透明度 50%
            'awarded': 'rgba(2, 103, 5, 0.7)',       # 026705 透明度 70%
            'quoted': 'rgba(2, 103, 5, 0.8)',        # 026705 透明度 80%
            'signed': 'rgba(2, 103, 5, 1)',          # 026705 透明度 100%
            'lost': 'rgba(108, 3, 3, 1)',            # 6C0303 透明度 100%
            'paused': 'rgba(189, 194, 189, 1)',      # BDC2BD 透明度 100%
            'unset': 'rgba(189, 194, 189, 0.5)'      # BDC2BD 透明度 50%
        },
        'amount': {
            'discover': 'rgba(7, 70, 160, 0.05)',    # 0746A0 透明度 5%
            'embed': 'rgba(7, 70, 160, 0.2)',        # 0746A0 透明度 20%
            'pre_tender': 'rgba(7, 70, 160, 0.3)',   # 0746A0 透明度 30%
            'tendering': 'rgba(7, 70, 160, 0.5)',    # 0746A0 透明度 50%
            'awarded': 'rgba(7, 70, 160, 0.7)',      # 0746A0 透明度 70%
            'quoted': 'rgba(7, 70, 160, 0.8)',       # 0746A0 透明度 80%
            'signed': 'rgba(7, 70, 160, 1)',         # 0746A0 透明度 100%
            'lost': 'rgba(108, 3, 3, 1)',            # 6C0303 透明度 100%
            'paused': 'rgba(189, 194, 189, 1)',      # BDC2BD 透明度 100%
            'unset': 'rgba(189, 194, 189, 0.5)'      # BDC2BD 透明度 50%
        }
    },
    # 徽章样式CSS类映射 - 与现有徽章组件保持一致
    'badge_classes': {
        'discover': 'bg-success bg-opacity-10 text-success',
        'embed': 'bg-success bg-opacity-25 text-success',
        'pre_tender': 'bg-success bg-opacity-50 text-success',
        'tendering': 'bg-success bg-opacity-75 text-success',
        'awarded': 'bg-success text-white',
        'quoted': 'bg-primary bg-opacity-75 text-white',
        'signed': 'bg-primary text-white',
        'lost': 'bg-danger text-white',
        'paused': 'bg-secondary text-white',
        'unset': 'bg-secondary bg-opacity-50 text-muted'
    }
}

# 订单状态配置示例（可扩展）
ORDER_STATUS_CONFIG = {
    'stage_field': 'status',
    'stage_order': ['pending', 'processing', 'shipped', 'delivered', 'cancelled'],
    'stage_labels': {
        'pending': '待处理',
        'processing': '处理中', 
        'shipped': '已发货',
        'delivered': '已送达',
        'cancelled': '已取消'
    },
    'stage_colors': {
        'quantity': {
            'pending': 'rgba(255, 193, 7, 0.2)',
            'processing': 'rgba(13, 202, 240, 0.2)',
            'shipped': 'rgba(25, 135, 84, 0.2)',
            'delivered': 'rgba(25, 135, 84, 1)',
            'cancelled': 'rgba(220, 53, 69, 1)'
        },
        'amount': {
            'pending': 'rgba(255, 193, 7, 0.3)',
            'processing': 'rgba(13, 202, 240, 0.3)',
            'shipped': 'rgba(25, 135, 84, 0.3)',
            'delivered': 'rgba(25, 135, 84, 1)',
            'cancelled': 'rgba(220, 53, 69, 1)'
        }
    },
    'badge_classes': {
        'pending': 'bg-warning text-dark',
        'processing': 'bg-info text-white',
        'shipped': 'bg-success bg-opacity-75 text-white',
        'delivered': 'bg-success text-white',
        'cancelled': 'bg-danger text-white'
    }
}

def get_stage_config(config_name):
    """获取指定的阶段配置"""
    configs = {
        'project': PROJECT_STAGE_CONFIG,
        'order': ORDER_STATUS_CONFIG
    }
    return configs.get(config_name)

def get_stage_label(stage_key, config_name='project'):
    """获取阶段标签"""
    config = get_stage_config(config_name)
    if config and stage_key in config['stage_labels']:
        return config['stage_labels'][stage_key]
    
    # 回退到现有的项目阶段标签函数
    if config_name == 'project':
        return project_stage_label(stage_key, 'zh')
    
    return stage_key

def get_stage_color(stage_key, metric_type='quantity', config_name='project'):
    """获取阶段颜色"""
    config = get_stage_config(config_name)
    if config and 'stage_colors' in config:
        colors = config['stage_colors'].get(metric_type, {})
        return colors.get(stage_key, colors.get('unset', 'rgba(189, 194, 189, 0.5)'))
    return 'rgba(189, 194, 189, 0.5)'

def get_stage_badge_class(stage_key, config_name='project'):
    """获取阶段徽章CSS类"""
    config = get_stage_config(config_name)
    if config and 'badge_classes' in config:
        return config['badge_classes'].get(stage_key, 'bg-secondary text-muted')
    return 'bg-secondary text-muted'