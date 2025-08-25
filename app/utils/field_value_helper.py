"""
字段值获取助手模块

用于获取各种对象字段的可选值，支持映射处理和频次统计
"""

from flask import current_app
from app import db
from sqlalchemy import text, inspect
import logging

logger = logging.getLogger(__name__)

# 对象类型到数据表的映射
OBJECT_TYPE_TABLE_MAPPING = {
    'project': 'projects',
    'quotation': 'quotations', 
    'pricing_order': 'pricing_orders',
    'settlement_order': 'settlement_orders',
    'expense': 'expenses',
    'company': 'companies',
    'user': 'users',
    'contact': 'contacts'
}

# 字段映射配置 - 定义哪些字段有显示映射
FIELD_MAPPING_CONFIG = {
    'project_type': {
        'mapping_function': 'get_project_type_mapping',
        'has_mapping': True
    },
    'project_stage': {
        'mapping_function': 'get_project_stage_mapping',
        'has_mapping': True
    },
    'report_source': {
        'mapping_function': 'get_report_source_mapping',
        'has_mapping': True
    },
    'authorization_status': {
        'mapping_function': 'get_authorization_status_mapping',
        'has_mapping': True
    },
    'company_type': {
        'mapping_function': 'get_company_type_mapping',
        'has_mapping': True
    }
}


def get_field_available_values(object_type, field_name):
    """
    获取指定字段的可选值
    
    Args:
        object_type (str): 对象类型
        field_name (str): 字段名称
    
    Returns:
        list: 字段值列表，格式为:
        [
            {
                'value': '实际值',
                'display': '显示值', 
                'count': 使用次数
            }
        ]
    """
    
    # 获取对应的数据表名
    table_name = OBJECT_TYPE_TABLE_MAPPING.get(object_type)
    if not table_name:
        raise ValueError(f"不支持的对象类型: {object_type}")
    
    # 处理嵌套字段（如 project.project_type）
    if '.' in field_name:
        return _get_nested_field_values(object_type, field_name)
    
    # 处理特殊字段：批价单的 project_type 字段通过关联项目表获取
    if field_name == 'project_type' and object_type in ['quotation', 'pricing_order']:
        return _get_project_field_values(field_name)
    
    # 验证字段是否存在
    if not _field_exists(table_name, field_name):
        raise ValueError(f"字段 {field_name} 在表 {table_name} 中不存在")
    
    # 查询字段值和频次
    raw_values = _query_field_values(table_name, field_name)
    
    # 应用映射处理
    processed_values = _apply_field_mapping(field_name, raw_values)
    
    # 排序：按频次降序，同频次按字母序
    processed_values.sort(key=lambda x: (-x['count'], x['display']))
    
    logger.info(f"获取字段值成功: {object_type}.{field_name}, 共 {len(processed_values)} 个值")
    return processed_values


def _field_exists(table_name, field_name):
    """检查字段是否存在于数据表中"""
    try:
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return field_name in columns
    except Exception as e:
        logger.error(f"检查字段存在性失败: {str(e)}")
        return False


def _query_field_values(table_name, field_name):
    """查询字段的所有唯一值和使用频次"""
    try:
        # 排除空值和NULL值，限制返回数量避免性能问题
        query = text(f"""
            SELECT DISTINCT {field_name} as field_value, COUNT(*) as count
            FROM {table_name} 
            WHERE {field_name} IS NOT NULL 
            AND {field_name} != ''
            GROUP BY {field_name}
            ORDER BY count DESC, {field_name} ASC
            LIMIT 100
        """)
        
        result = db.session.execute(query)
        
        values = []
        for row in result:
            if row.field_value:  # 再次确保值不为空
                values.append({
                    'value': str(row.field_value),
                    'count': row.count
                })
        
        return values
        
    except Exception as e:
        logger.error(f"查询字段值失败: {str(e)}")
        return []


def _apply_field_mapping(field_name, raw_values):
    """对字段值应用映射处理"""
    
    # 检查是否需要映射
    field_config = FIELD_MAPPING_CONFIG.get(field_name)
    if not field_config or not field_config['has_mapping']:
        # 无映射，直接使用原值作为显示值
        return [
            {
                'value': item['value'],
                'display': item['value'],
                'count': item['count']
            }
            for item in raw_values
        ]
    
    # 获取映射函数
    mapping_function_name = field_config['mapping_function']
    mapping_function = globals().get(mapping_function_name)
    
    if not mapping_function:
        logger.warning(f"映射函数 {mapping_function_name} 不存在，使用原值")
        return [
            {
                'value': item['value'],
                'display': item['value'],
                'count': item['count']
            }
            for item in raw_values
        ]
    
    # 应用映射并去重
    mapping_dict = mapping_function()
    reverse_mapping = {v: k for k, v in mapping_dict.items()}  # 反向映射：显示值->代码值
    
    # 用于去重和合并频次的字典
    merged_values = {}
    
    for item in raw_values:
        value = item['value']
        
        # 判断这个值是代码值还是显示值
        if value in mapping_dict:
            # 这是一个代码值，使用映射
            code_value = value
            display_value = mapping_dict[value]
        elif value in reverse_mapping:
            # 这是一个显示值，转换为代码值
            code_value = reverse_mapping[value]
            display_value = value
        else:
            # 不在映射中的值，保持原值
            code_value = value
            display_value = value
        
        # 合并相同代码值的频次
        if code_value in merged_values:
            merged_values[code_value]['count'] += item['count']
        else:
            merged_values[code_value] = {
                'value': code_value,
                'display': display_value,
                'count': item['count']
            }
    
    # 返回去重后的结果
    return list(merged_values.values())


def _get_nested_field_values(object_type, field_name):
    """处理嵌套字段值获取（如 project.project_type）"""
    
    parts = field_name.split('.')
    if len(parts) != 2:
        raise ValueError(f"不支持的嵌套字段格式: {field_name}")
    
    relation_name, target_field = parts
    
    # 目前主要支持 project.* 格式
    if relation_name == 'project' and object_type in ['quotation', 'pricing_order']:
        return _get_project_field_values(target_field)
    
    raise ValueError(f"不支持的嵌套字段: {field_name}")


def _get_project_field_values(field_name):
    """获取项目字段的值（用于嵌套字段访问）"""
    return get_field_available_values('project', field_name)


# 映射函数定义
def get_project_type_mapping():
    """获取项目类型映射"""
    from app.utils.dictionary_helpers import PROJECT_TYPE_LABELS
    from app.utils.i18n import get_current_language
    
    try:
        lang_code = get_current_language()
    except:
        lang_code = 'zh'
    
    return {k: v[lang_code] for k, v in PROJECT_TYPE_LABELS.items()}


def get_project_stage_mapping():
    """获取项目阶段映射"""
    from app.utils.dictionary_helpers import PROJECT_STAGE_LABELS
    from app.utils.i18n import get_current_language
    
    try:
        lang_code = get_current_language()
    except:
        lang_code = 'zh'
    
    return {k: v[lang_code] for k, v in PROJECT_STAGE_LABELS.items()}


def get_report_source_mapping():
    """获取报备来源映射"""
    from app.utils.dictionary_helpers import REPORT_SOURCE_LABELS
    from app.utils.i18n import get_current_language
    
    try:
        lang_code = get_current_language()
    except:
        lang_code = 'zh'
    
    return {k: v[lang_code] for k, v in REPORT_SOURCE_LABELS.items()}


def get_authorization_status_mapping():
    """获取授权状态映射"""
    from app.utils.dictionary_helpers import AUTHORIZATION_STATUS_LABELS
    from app.utils.i18n import get_current_language
    
    try:
        lang_code = get_current_language()
    except:
        lang_code = 'zh'
    
    return {k: v[lang_code] for k, v in AUTHORIZATION_STATUS_LABELS.items()}


def get_company_type_mapping():
    """获取企业类型映射"""
    from app.utils.dictionary_helpers import COMPANY_TYPE_LABELS
    from app.utils.i18n import get_current_language
    
    try:
        lang_code = get_current_language()
    except:
        lang_code = 'zh'
    
    return {k: v[lang_code] for k, v in COMPANY_TYPE_LABELS.items()}


def get_supported_fields_for_object(object_type):
    """
    获取对象类型支持的分支条件字段（使用统一映射管理器）
    
    Args:
        object_type (str): 对象类型
    
    Returns:
        list: 支持的字段列表
    """
    
    # 获取对应的数据表名
    table_name = OBJECT_TYPE_TABLE_MAPPING.get(object_type)
    if not table_name:
        logger.warning(f"不支持的对象类型: {object_type}")
        return []
    
    try:
        # 使用统一映射管理器获取字段
        from app.utils.chinese_mapping_manager import mapping_manager
        
        configured_fields = mapping_manager.get_supported_fields_for_table(table_name)
        
        if configured_fields:
            logger.info(f"获取 {object_type} 字段成功，共 {len(configured_fields)} 个字段")
            # 添加嵌套字段
            nested_fields = _get_nested_fields_for_object(object_type)
            configured_fields.extend(nested_fields)
            return configured_fields
        
        # 最终降级到硬编码字段列表
        logger.warning(f"无法获取 {table_name} 的字段，使用降级方案")
        return _get_fallback_fields(object_type)
        
    except Exception as e:
        logger.error(f"获取支持字段失败: {str(e)}")
        # 最终降级到硬编码字段列表
        return _get_fallback_fields(object_type)


def _get_configured_fields(table_name):
    """
    从data_field_config表获取已配置的字段
    
    Args:
        table_name (str): 数据表名
    
    Returns:
        list: 配置的字段列表
    """
    try:
        # 查询配置表中is_filterable=true且表处于活跃状态的字段
        query = text("""
            SELECT 
                dfc.field_name,
                dfc.display_name,
                dfc.data_type,
                dfc.is_aggregatable
            FROM data_field_config dfc
            JOIN data_table_config dtc ON dfc.table_config_id = dtc.id
            WHERE dtc.table_name = :table_name
            AND dtc.is_active = true
            AND dfc.is_filterable = true
            AND dfc.field_name NOT IN ('id', 'created_at', 'updated_at', 'created_by', 'updated_by')
            ORDER BY dfc.field_name
        """)
        
        result = db.session.execute(query, {'table_name': table_name})
        
        configured_fields = []
        for row in result:
            field_name = row.field_name
            display_name = row.display_name
            
            # 如果display_name是英文，尝试生成中文标签
            if _is_english_name(display_name):
                chinese_label = _generate_field_label(field_name)
                if chinese_label != display_name:
                    display_name = chinese_label
                    logger.info(f"为字段 {field_name} 生成中文标签: {chinese_label}")
            
            # 检查是否有映射
            has_mapping = field_name in FIELD_MAPPING_CONFIG
            
            configured_fields.append({
                'field': field_name,
                'label': display_name,
                'has_mapping': has_mapping,
                'type': str(row.data_type),
                'is_aggregatable': row.is_aggregatable
            })
        
        return configured_fields
        
    except Exception as e:
        logger.error(f"获取配置字段失败: {str(e)}")
        return []


def _is_english_name(name):
    """判断名称是否为英文"""
    if not name:
        return True
    # 简单判断：如果包含中文字符则不是英文
    for char in name:
        if '\u4e00' <= char <= '\u9fff':  # 中文字符范围
            return False
    return True


def _get_dynamic_fields(table_name, object_type):
    """
    动态发现数据库字段（降级方案）
    
    Args:
        table_name (str): 数据表名
        object_type (str): 对象类型
        
    Returns:
        list: 动态发现的字段列表
    """
    try:
        # 动态获取数据库表字段
        inspector = inspect(db.engine)
        columns = inspector.get_columns(table_name)
        
        # 过滤出适合作为条件的字段
        supported_fields = []
        
        for column in columns:
            field_name = column['name']
            field_type = str(column['type'])
            
            # 跳过不适合作为条件的字段
            if _should_skip_field(field_name, field_type):
                continue
            
            # 生成字段标签
            field_label = _generate_field_label(field_name)
            
            # 检查是否有映射
            has_mapping = field_name in FIELD_MAPPING_CONFIG
            
            supported_fields.append({
                'field': field_name,
                'label': field_label,
                'has_mapping': has_mapping,
                'type': field_type
            })
        
        # 按字段名排序
        supported_fields.sort(key=lambda x: x['field'])
        
        logger.info(f"动态发现 {object_type} 字段成功，共 {len(supported_fields)} 个字段")
        return supported_fields
        
    except Exception as e:
        logger.error(f"动态字段发现失败: {str(e)}")
        return []


def _should_skip_field(field_name, field_type):
    """判断字段是否应该跳过"""
    
    # 跳过的字段类型
    skip_patterns = [
        'id',           # 主键
        'created_at',   # 时间戳
        'updated_at',   # 时间戳
        'deleted_at',   # 软删除时间戳
        'password',     # 密码字段
        'token',        # 令牌字段
        'secret',       # 秘密字段
        'hash',         # 哈希字段
    ]
    
    # 跳过特定字段名
    if any(pattern in field_name.lower() for pattern in skip_patterns):
        return True
    
    # 跳过二进制类型
    if 'BLOB' in field_type.upper() or 'BINARY' in field_type.upper():
        return True
    
    # 跳过JSON类型（太复杂）
    if 'JSON' in field_type.upper():
        return True
    
    return False


def _generate_field_label(field_name):
    """生成字段的中文标签"""
    
    # 扩展的字段标签映射 - 基于实际数据库字段
    field_labels = {
        # 项目相关字段
        'project_type': '项目类型',
        'project_stage': '项目阶段',
        'project_name': '项目名称',
        'report_source': '报备来源',
        'report_time': '报备时间',
        'authorization_status': '授权状态',
        'authorization_code': '授权编号',
        'current_stage': '当前阶段',
        'stage_description': '阶段描述',
        'activity_reason': '活动原因',
        'quotation_customer': '报价金额',
        'delivery_forecast': '交付预测',
        'last_activity_date': '最后活动日期',
        'rating': '评级',
        'feedback': '反馈',
        'design_issues': '设计问题',
        'product_situation': '产品情况',
        'industry': '行业',
        'contractor': '承包商',
        'dealer': '经销商',
        'end_user': '最终用户',
        'system_integrator': '系统集成商',
        'vendor_sales_manager_id': '供应商销售经理',
        
        # 通用字段
        'total_amount': '总金额',
        'amount': '金额',
        'department': '部门',
        'priority': '优先级',
        'status': '状态',
        'name': '名称',
        'title': '标题',
        'description': '描述',
        'currency': '货币',
        'company_type': '企业类型',
        'approval_status': '审核状态',
        'owner_id': '负责人',
        'is_active': '是否激活',
        'is_deleted': '是否删除',
        'is_locked': '是否锁定',
        'locked_at': '锁定时间',
        'locked_by': '锁定人',
        'locked_reason': '锁定原因',
        'share_enabled': '共享启用',
        'shared_with_users': '共享用户',
        
        # 报价单相关字段
        'quotation_number': '报价单号',
        'quotation_date': '报价日期',
        'valid_until': '有效期至',
        'terms_conditions': '条款条件',
        
        # 订单相关字段
        'order_number': '订单号',
        'order_date': '订单日期',
        'delivery_date': '交付日期',
        
        # 联系人相关字段
        'contact_person': '联系人',
        'phone': '电话',
        'mobile': '手机',
        'email': '邮箱',
        'wechat': '微信',
        'qq': 'QQ',
        'address': '地址',
        'city': '城市',
        'province': '省份',
        'country': '国家',
        'region': '地区',
        'postal_code': '邮政编码',
        
        # 时间字段
        'created_at': '创建时间',
        'updated_at': '更新时间',
        'deleted_at': '删除时间',
        'created_by': '创建者',
        'updated_by': '更新者',
        
        # 财务相关字段
        'unit_price': '单价',
        'quantity': '数量',
        'discount': '折扣',
        'tax_rate': '税率',
        'total_price': '总价',
        'payment_terms': '付款条件',
        'payment_status': '付款状态',
        
        # 产品相关字段
        'product_code': '产品代码',
        'product_name': '产品名称',
        'specification': '规格',
        'model': '型号',
        'brand': '品牌',
        'category': '类别',
        
        # 用户相关字段
        'username': '用户名',
        'real_name': '真实姓名',
        'role': '角色',
        'is_department_manager': '是否部门经理'
    }
    
    # 如果有预定义标签，使用预定义的
    if field_name in field_labels:
        return field_labels[field_name]
    
    # 否则生成简单的标签
    # 将下划线替换为空格，首字母大写
    label = field_name.replace('_', ' ').title()
    return label


def _get_nested_fields_for_object(object_type):
    """获取对象的嵌套字段"""
    
    nested_fields = []
    
    # 为报价单和订单等添加项目相关字段（使用直接字段名）
    if object_type in ['quotation', 'pricing_order', 'settlement_order']:
        project_fields = [
            {'field': 'project_type', 'label': '项目类型', 'has_mapping': True, 'type': 'standard'},
            {'field': 'project_stage', 'label': '项目阶段', 'has_mapping': True, 'type': 'standard'},
            {'field': 'report_source', 'label': '报备来源', 'has_mapping': True, 'type': 'standard'},
            {'field': 'authorization_status', 'label': '授权状态', 'has_mapping': True, 'type': 'standard'},
        ]
        nested_fields.extend(project_fields)
    
    return nested_fields


def _get_fallback_fields(object_type):
    """获取降级的硬编码字段列表"""
    
    fallback_definitions = {
        'project': [
            {'field': 'project_type', 'label': '项目类型', 'has_mapping': True},
            {'field': 'project_stage', 'label': '项目阶段', 'has_mapping': True},
            {'field': 'report_source', 'label': '报备来源', 'has_mapping': True},
            {'field': 'authorization_status', 'label': '授权状态', 'has_mapping': True},
        ],
        'quotation': [
            {'field': 'project_type', 'label': '项目类型', 'has_mapping': True},
            {'field': 'amount', 'label': '报价金额', 'has_mapping': False},
            {'field': 'currency', 'label': '货币类型', 'has_mapping': False},
            {'field': 'approval_status', 'label': '审核状态', 'has_mapping': False},
        ]
    }
    
    return fallback_definitions.get(object_type, [])