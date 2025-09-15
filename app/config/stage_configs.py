# -*- coding: utf-8 -*-
"""
通用阶段跟踪配置管理
定义不同对象类型的阶段配置，支持项目、研发产品等多种对象的阶段管理
"""

# 项目阶段配置
PROJECT_STAGES = {
    'mainStages': [
        {
            'id': 0,
            'key': 'discover',
            'name': '发现',
            'zh_name': '发现',
            'en_name': 'Discovery',
            'description': '项目发现阶段，收集项目信息和需求',
            'order': 0
        },
        {
            'id': 1,
            'key': 'embed',
            'name': '植入',
            'zh_name': '植入',
            'en_name': 'Embedding',
            'description': '项目植入阶段，建立合作关系',
            'order': 1
        },
        {
            'id': 2,
            'key': 'pre_tender',
            'name': '招标前',
            'zh_name': '招标前',
            'en_name': 'Pre-tender',
            'description': '招标准备阶段，完善项目方案',
            'order': 2
        },
        {
            'id': 3,
            'key': 'tendering',
            'name': '招标中',
            'zh_name': '招标中',
            'en_name': 'Tendering',
            'description': '招标进行阶段，参与竞标',
            'order': 3
        },
        {
            'id': 4,
            'key': 'awarded',
            'name': '中标',
            'zh_name': '中标',
            'en_name': 'Awarded',
            'description': '中标阶段，获得项目机会',
            'order': 4
        },
        {
            'id': 5,
            'key': 'quoted',
            'name': '批价',
            'zh_name': '批价',
            'en_name': 'Pricing',
            'description': '批价阶段，进行价格审核',
            'order': 5
        },
        {
            'id': 6,
            'key': 'signed',
            'name': '签约',
            'zh_name': '签约',
            'en_name': 'Contracted',
            'description': '签约阶段，完成合同签署',
            'order': 6
        }
    ],
    'branchStages': [
        {
            'id': 7,
            'key': 'lost',
            'name': '失败',
            'zh_name': '失败',
            'en_name': 'Failed',
            'description': '项目失败，无法继续推进',
            'order': 7,
            'type': 'failure'
        },
        {
            'id': 8,
            'key': 'paused',
            'name': '搁置',
            'zh_name': '搁置',
            'en_name': 'Paused',
            'description': '项目暂时搁置，等待时机',
            'order': 8,
            'type': 'suspension'
        }
    ]
}

# 研发产品阶段配置
RD_PRODUCT_STAGES = {
    'mainStages': [
        {
            'id': 0,
            'key': 'research',
            'name': '调研中',
            'zh_name': '调研中',
            'en_name': 'Research',
            'description': '产品调研阶段，收集市场需求和技术信息',
            'order': 0,
            # 可选颜色配置：main为主色，light用于浅色背景
            'colors': {
                'main': '#92D050',   # 调研 主阶段 绿色
                'sub':  '#C6EFCE'    # 子阶段 浅绿色
            }
        },
        {
            'id': 1,
            'key': 'planning',
            'name': '立项中',
            'zh_name': '立项中',
            'en_name': 'Planning',
            'description': '产品立项阶段，确定产品规划和资源配置',
            'order': 1,
            'colors': {
                'main': '#CC99FF',   # 立项 主阶段 紫色
                'sub':  '#E5B8EC'    # 子阶段 浅紫色
            }
        },
        {
            'id': 2,
            'key': 'development',
            'name': '研发中',
            'zh_name': '研发中',
            'en_name': 'Development',
            'description': '产品研发阶段，进行技术开发和测试',
            'order': 2,
            'colors': {
                'main': '#F4B183',   # 研发 主阶段 橙色
                'sub':  '#FCE5CD'    # 子阶段 浅橙色
            }
        },
        {
            'id': 3,
            'key': 'apply_storage',
            'name': '申请入库',
            'zh_name': '申请入库',
            'en_name': 'Apply Storage',
            'description': '申请入库阶段，准备产品上线',
            'order': 3,
            'colors': {
                'main': '#8ECDF1',   # 申请入库 主阶段 青蓝色
                'sub':  '#BDD7EE'    # 子阶段 浅青蓝色
            }
        },
        {
            'id': 4,
            'key': 'stored',
            'name': '已入库',
            'zh_name': '已入库',
            'en_name': 'Stored',
            'description': '产品已入库，可以正式使用',
            'order': 4,
            'colors': {
                'main': '#5B9BD5',   # 已入库 主阶段 蓝色
                'sub':  '#B4C6E7'    # 子阶段 浅蓝色
            }
        }
    ],
    'branchStages': [
        {
            'id': 5,
            'key': 'cancelled',
            'name': '已取消',
            'zh_name': '已取消',
            'en_name': 'Cancelled',
            'description': '产品研发被取消，不再继续',
            'order': 5,
            'type': 'cancellation'
        },
        {
            'id': 6,
            'key': 'suspended',
            'name': '暂停',
            'zh_name': '暂停',
            'en_name': 'Suspended',
            'description': '产品研发暂停，等待条件成熟',
            'order': 6,
            'type': 'suspension'
        }
    ]
}

# 标准产品阶段配置
PRODUCT_STAGES = {
    'mainStages': [
        {
            'id': 0,
            'key': 'active',
            'name': '生产中',
            'zh_name': '生产中',
            'en_name': 'Active',
            'description': '产品正在生产中，可正常销售',
            'order': 0
        },
        {
            'id': 1,
            'key': 'discontinued',
            'name': '已停产',
            'zh_name': '已停产',
            'en_name': 'Discontinued',
            'description': '产品已停产，不再生产',
            'order': 1
        }
    ],
    'branchStages': []
}

# 所有阶段配置的映射
STAGE_CONFIGS = {
    'project': PROJECT_STAGES,
    'rd_product': RD_PRODUCT_STAGES,
    'product': PRODUCT_STAGES
}

# 状态到阶段的映射配置（用于数据迁移）
STATUS_TO_STAGE_MAPPING = {
    'rd_product': {
        '调研中': 'research',
        '立项中': 'planning',
        '研发中': 'development',
        '申请入库': 'apply_storage',
        '已入库': 'stored',
        '已取消': 'cancelled',
        '暂停': 'suspended'
    },
    'project': {
        '发现': 'discover',
        '植入': 'embed',
        '招标前': 'pre_tender',
        '招标中': 'tendering',
        '中标': 'awarded',
        '批价': 'quoted',
        '签约': 'signed',
        '失败': 'lost',
        '搁置': 'paused'
    },
    'product': {
        '生产中': 'active',
        '已停产': 'discontinued',
        'active': 'active',
        'inactive': 'discontinued'
    }
}

# 阶段到状态的反向映射
STAGE_TO_STATUS_MAPPING = {
    object_type: {stage: status for status, stage in mapping.items()}
    for object_type, mapping in STATUS_TO_STAGE_MAPPING.items()
}

# 国际化文本配置
I18N_TEXTS = {
    'zh': {
        'confirmAdvanceTitle': '确认阶段推进',
        'confirmAdvanceMessage': '您确定要将{object_type}从「{current}」阶段推进到「{next}」阶段吗？',
        'confirmRestore': '确认恢复到主线',
        'confirmRestoreMessage': '您确定要将{object_type}从「{branch}」状态恢复到主线「{main}」阶段吗？',
        'confirmSwitchTitle': '确认切换到分支状态',
        'confirmSwitchMessage': '您确定要将{object_type}从「{current}」阶段切换为「{branch}」状态吗？',
        'operationNote': '此操作将更新当前阶段状态，推进后将无法直接回退。',
        'restoreNote': '将重新进入正常的阶段流程中。',
        'lostNote': '将被标记为失败状态。',
        'pausedNote': '将被暂时搁置。',
        'confirmAdvance': '确认推进',
        'confirmRestore': '确认恢复',
        'confirmSwitch': '确认切换',
        'cancel': '取消',
        'stageUpdating': '阶段更新中，请稍候',
        'unknown': '未知',
        'days': '天',
        'object_types': {
            'project': '项目',
            'rd_product': '研发产品',
            'product': '产品'
        }
    },
    'en': {
        'confirmAdvanceTitle': 'Confirm Stage Advancement',
        'confirmAdvanceMessage': 'Are you sure you want to advance the {object_type} from "{current}" stage to "{next}" stage?',
        'confirmRestore': 'Confirm Return to Main Track',
        'confirmRestoreMessage': 'Are you sure you want to restore the {object_type} from "{branch}" status back to main track "{main}" stage?',
        'confirmSwitchTitle': 'Confirm Switch to Branch Status',
        'confirmSwitchMessage': 'Are you sure you want to switch the {object_type} from "{current}" stage to "{branch}" status?',
        'operationNote': 'This operation will update the current stage status and cannot be directly reverted after advancement.',
        'restoreNote': 'Will re-enter the normal stage workflow.',
        'lostNote': 'Will be marked as failed status.',
        'pausedNote': 'Will be temporarily suspended.',
        'confirmAdvance': 'Confirm Advance',
        'confirmRestore': 'Confirm Restore',
        'confirmSwitch': 'Confirm Switch',
        'cancel': 'Cancel',
        'stageUpdating': 'Stage updating, please wait',
        'unknown': 'Unknown',
        'days': 'days',
        'object_types': {
            'project': 'Project',
            'rd_product': 'R&D Product',
            'product': 'Product'
        }
    }
}

def get_stage_config(object_type):
    """
    获取指定对象类型的阶段配置
    
    Args:
        object_type (str): 对象类型，如 'project', 'rd_product', 'product'
        
    Returns:
        dict: 阶段配置字典，包含 mainStages 和 branchStages
    """
    return STAGE_CONFIGS.get(object_type, {})

def get_stage_by_key(object_type, stage_key):
    """
    根据阶段键值获取阶段信息
    
    Args:
        object_type (str): 对象类型
        stage_key (str): 阶段键值
        
    Returns:
        dict: 阶段信息字典，如果未找到返回None
    """
    config = get_stage_config(object_type)
    all_stages = config.get('mainStages', []) + config.get('branchStages', [])
    
    for stage in all_stages:
        if stage['key'] == stage_key:
            return stage
    return None

def get_next_stage(object_type, current_stage_key):
    """
    获取下一个阶段
    
    Args:
        object_type (str): 对象类型
        current_stage_key (str): 当前阶段键值
        
    Returns:
        dict: 下一个阶段信息，如果没有下一个阶段返回None
    """
    config = get_stage_config(object_type)
    main_stages = config.get('mainStages', [])
    
    # 查找当前阶段在主线阶段中的位置
    current_index = -1
    for i, stage in enumerate(main_stages):
        if stage['key'] == current_stage_key:
            current_index = i
            break
    
    # 如果当前阶段不在主线中或已是最后一个阶段，返回None
    if current_index == -1 or current_index >= len(main_stages) - 1:
        return None
        
    return main_stages[current_index + 1]

def status_to_stage_key(object_type, status):
    """
    将状态字符串转换为阶段键值
    
    Args:
        object_type (str): 对象类型
        status (str): 状态字符串
        
    Returns:
        str: 阶段键值，如果未找到映射返回原状态字符串
    """
    mapping = STATUS_TO_STAGE_MAPPING.get(object_type, {})
    return mapping.get(status, status)

def stage_key_to_status(object_type, stage_key):
    """
    将阶段键值转换为状态字符串
    
    Args:
        object_type (str): 对象类型
        stage_key (str): 阶段键值
        
    Returns:
        str: 状态字符串，如果未找到映射返回原阶段键值
    """
    mapping = STAGE_TO_STATUS_MAPPING.get(object_type, {})
    return mapping.get(stage_key, stage_key)

def get_i18n_texts(language='zh'):
    """
    获取国际化文本
    
    Args:
        language (str): 语言代码，默认为 'zh'
        
    Returns:
        dict: 国际化文本字典
    """
    return I18N_TEXTS.get(language, I18N_TEXTS['zh'])

def get_object_type_name(object_type, language='zh'):
    """
    获取对象类型的显示名称
    
    Args:
        object_type (str): 对象类型
        language (str): 语言代码，默认为 'zh'
        
    Returns:
        str: 对象类型显示名称
    """
    texts = get_i18n_texts(language)
    return texts.get('object_types', {}).get(object_type, object_type)

def validate_stage_transition(object_type, current_stage, target_stage):
    """
    验证阶段转换是否有效
    
    Args:
        object_type (str): 对象类型
        current_stage (str): 当前阶段
        target_stage (str): 目标阶段
        
    Returns:
        tuple: (is_valid, message) - 是否有效和消息
    """
    config = get_stage_config(object_type)
    if not config:
        return False, f"未知的对象类型: {object_type}"
    
    all_stages = config.get('mainStages', []) + config.get('branchStages', [])
    stage_keys = [stage['key'] for stage in all_stages]
    
    if current_stage not in stage_keys:
        return False, f"未知的当前阶段: {current_stage}"
        
    if target_stage not in stage_keys:
        return False, f"未知的目标阶段: {target_stage}"
    
    # 在这里可以添加更复杂的业务逻辑验证
    # 例如：某些阶段不能直接跳转、需要满足特定条件等
    
    return True, "阶段转换有效"

# 导出主要函数和配置
__all__ = [
    'STAGE_CONFIGS',
    'PROJECT_STAGES',
    'RD_PRODUCT_STAGES',
    'PRODUCT_STAGES',
    'STATUS_TO_STAGE_MAPPING',
    'STAGE_TO_STATUS_MAPPING',
    'I18N_TEXTS',
    'get_stage_config',
    'get_stage_by_key',
    'get_next_stage',
    'status_to_stage_key',
    'stage_key_to_status',
    'get_i18n_texts',
    'get_object_type_name',
    'validate_stage_transition'
]
