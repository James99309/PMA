"""
全局字段中文映射配置
统一管理所有数据库字段的中文显示名称
"""

# 通用字段映射（适用于多个表的共同字段）
COMMON_FIELDS = {
    # 基础标识字段
    'id': 'ID',
    'name': '名称',
    'title': '标题',
    'description': '描述',
    'code': '代码',
    'type': '类型',
    'status': '状态',
    'category': '类别',
    'priority': '优先级',
    'level': '级别',
    'order': '序号',
    'sort_order': '排序',
    'position': '位置',
    'rank': '排名',
    'rating': '评级',
    'score': '分数',
    'weight': '权重',
    'percentage': '百分比',
    
    # 时间相关字段
    'created_at': '创建时间',
    'updated_at': '更新时间',
    'deleted_at': '删除时间',
    'created_by': '创建者',
    'updated_by': '更新者',
    'deleted_by': '删除者',
    'create_time': '创建时间',
    'update_time': '更新时间',
    'start_time': '开始时间',
    'end_time': '结束时间',
    'start_date': '开始日期',
    'end_date': '结束日期',
    'due_date': '截止日期',
    'valid_until': '有效期至',
    'expired_at': '过期时间',
    'last_activity_date': '最后活动日期',
    'report_time': '报备时间',
    'delivery_date': '交付日期',
    'delivery_forecast': '交付预测',
    
    # 状态控制字段
    'is_active': '活跃度',
    'is_deleted': '是否删除',
    'is_enabled': '是否启用',
    'is_locked': '是否锁定',
    'is_public': '是否公开',
    'is_private': '是否私有',
    'is_required': '是否必需',
    'is_optional': '是否可选',
    'is_visible': '是否可见',
    'is_editable': '是否可编辑',
    'is_primary': '是否主要',
    'is_default': '是否默认',
    'locked_at': '锁定时间',
    'locked_by': '锁定人',
    'locked_reason': '锁定原因',
    
    # 关联字段
    'user_id': '用户ID',
    'created_by': '创建人',
    'owner_id': '负责人',
    'manager_id': '管理员ID',
    'parent_id': '父级ID',
    'company_id': '公司ID',
    'project_id': '项目ID',
    'product_id': '产品ID',
    'department_id': '部门ID',
    'role_id': '角色ID',
    
    # 共享和权限字段
    'share_enabled': '共享启用',
    'shared_with_users': '共享用户',
    'permissions': '权限',
    'access_level': '访问级别',
    
    # 财务金额字段
    'amount': '金额',
    'total_amount': '总金额',
    'unit_price': '单价',
    'total_price': '总价',
    'cost': '成本',
    'price': '价格',
    'discount': '折扣',
    'tax': '税费',
    'tax_rate': '税率',
    'currency': '货币',
    'exchange_rate': '汇率',
    'payment_terms': '付款条件',
    'payment_status': '付款状态',
    
    # 数量和计量字段
    'quantity': '数量',
    'count': '计数',
    'total': '总计',
    'subtotal': '小计',
    'unit': '单位',
    'measurement': '计量',
    'size': '尺寸',
    'length': '长度',
    'width': '宽度',
    'height': '高度',
    'volume': '体积',
    'area': '面积',
    
    # 联系信息字段
    'contact_person': '联系人',
    'phone': '电话',
    'mobile': '手机',
    'fax': '传真',
    'email': '邮箱',
    'website': '网站',
    'wechat': '微信',
    'qq': 'QQ',
    'skype': 'Skype',
    'address': '地址',
    'city': '城市',
    'province': '省份',
    'country': '国家',
    'region': '地区',
    'postal_code': '邮政编码',
    'zip_code': '邮编',
    
    # 备注和说明字段
    'note': '备注',
    'notes': '备注',
    'comment': '评论',
    'comments': '评论',
    'remark': '说明',
    'remarks': '说明',
    'memo': '备忘',
    'feedback': '反馈',
    'review': '审查',
    'summary': '摘要',
    'details': '详情',
    'specification': '规格',
    'specs': '规格',
    'features': '特性',
    'attributes': '属性',
    'tags': '标签',
    'keywords': '关键词',
}

# 项目相关字段映射
PROJECT_FIELDS = {
    'project_name': '项目名称',
    'project_type': '项目类型',
    'project_stage': '项目阶段',
    'current_stage': '当前阶段',
    'stage_description': '阶段描述',
    'authorization_status': '授权状态',
    'authorization_code': '授权编号',
    'report_source': '报备来源',
    'activity_reason': '活动原因',
    'quotation_customer': '报价金额',
    'design_issues': '设计问题',
    'product_situation': '产品情况',
    'industry': '行业',
    'contractor': '承包商',
    'dealer': '经销商',
    'end_user': '最终用户',
    'system_integrator': '系统集成商',
    'vendor_sales_manager_id': '厂商销售',
    'project_number': '项目编号',
    'project_manager': '项目经理',
    'project_status': '项目状态',
    'project_progress': '项目进度',
    'estimated_value': '预估价值',
    'actual_value': '实际价值',
    'win_probability': '赢单概率',
    'competitor': '竞争对手',
    'risk_assessment': '风险评估',
    'next_steps': '下一步计划',
}

# 公司客户相关字段映射
COMPANY_FIELDS = {
    'company_name': '公司名称',
    'company_type': '企业类型',
    'company_code': '公司代码',
    'business_license': '营业执照',
    'tax_number': '税号',
    'registration_address': '注册地址',
    'business_scope': '经营范围',
    'established_date': '成立日期',
    'employee_count': '员工数量',
    'annual_revenue': '年营业额',
    'credit_rating': '信用等级',
    'payment_terms': '付款条件',
    'cooperation_status': '合作状态',
    'relationship_level': '关系等级',
    'customer_source': '客户来源',
    'sales_representative': '销售代表',
    'key_contact': '关键联系人',
    'decision_maker': '决策人',
    'procurement_contact': '采购联系人',
    'technical_contact': '技术联系人',
}

# 用户相关字段映射
USER_FIELDS = {
    'username': '用户名',
    'real_name': '真实姓名',
    'display_name': '显示名称',
    'first_name': '名',
    'last_name': '姓',
    'full_name': '全名',
    'nickname': '昵称',
    'employee_id': '员工编号',
    'department': '部门',
    'job_title': '职位',
    'role': '角色',
    'manager': '上级主管',
    'hire_date': '入职日期',
    'salary': '薪资',
    'is_department_manager': '是否部门经理',
    'avatar': '头像',
    'signature': '签名',
    'bio': '个人简介',
    'skills': '技能',
    'experience': '工作经验',
    'education': '教育背景',
    'certification': '认证资质',
    'language': '语言',
    'timezone': '时区',
    'last_login': '最后登录',
    'login_count': '登录次数',
}

# 产品相关字段映射
PRODUCT_FIELDS = {
    'product_name': '产品名称',
    'product_code': '产品代码',
    'product_number': '产品编号',
    'product_type': '产品类型',
    'product_category': '产品类别',
    'product_line': '产品线',
    'brand': '品牌',
    'model': '型号',
    'version': '版本',
    'manufacturer': '制造商',
    'supplier': '供应商',
    'origin': '产地',
    'material': '材质',
    'color': '颜色',
    'weight': '重量',
    'dimensions': '尺寸',
    'warranty_period': '保修期',
    'shelf_life': '保质期',
    'stock_quantity': '库存数量',
    'minimum_order': '最小订购量',
    'lead_time': '交货周期',
    'discontinued': '是否停产',
}

# 订单相关字段映射
ORDER_FIELDS = {
    'order_number': '订单号',
    'order_date': '订单日期',
    'order_type': '订单类型',
    'order_status': '订单状态',
    'quotation_number': '报价单号',
    'quotation_date': '报价日期',
    'customer_po': '客户采购单号',
    'sales_order': '销售订单',
    'purchase_order': '采购订单',
    'invoice_number': '发票号',
    'invoice_date': '发票日期',
    'shipping_address': '收货地址',
    'billing_address': '账单地址',
    'shipping_method': '运输方式',
    'tracking_number': '跟踪号',
    'delivery_status': '交付状态',
    'payment_method': '付款方式',
    'terms_conditions': '条款条件',
    'approval_status': '审批状态',
    'approved_by': '审批人',
    'approved_at': '审批时间',
}

# 审批流程相关字段映射
APPROVAL_FIELDS = {
    'template_name': '模板名称',
    'process_name': '流程名称',
    'step_name': '步骤名称',
    'step_type': '步骤类型',
    'step_order': '步骤顺序',
    'action_type': '动作类型',
    'approver_type': '审批人类型',
    'approver_id': '审批人ID',
    'approval_result': '审批结果',
    'approval_comment': '审批意见',
    'approval_time': '审批时间',
    'instance_status': '实例状态',
    'current_step': '当前步骤',
    'object_type': '对象类型',
    'object_id': '对象ID',
    'initiated_by': '发起人',
    'initiated_at': '发起时间',
    'completed_at': '完成时间',
    'duration': '持续时间',
    'branch_condition': '分支条件',
    'is_parallel': '是否并行',
    'cc_users': '抄送用户',
    'send_email': '发送邮件',
}

# 绩效相关字段映射
PERFORMANCE_FIELDS = {
    'metric_name': '指标名称',
    'metric_type': '指标类型',
    'metric_category': '指标类别',
    'target_value': '目标值',
    'actual_value': '实际值',
    'achievement_rate': '达成率',
    'performance_period': '绩效周期',
    'calculation_method': '计算方法',
    'data_source': '数据源',
    'responsible_person': '负责人',
    'review_frequency': '评估频率',
    'improvement_plan': '改进计划',
    'benchmark': '基准值',
    'threshold': '阈值',
    'kpi_code': 'KPI代码',
    'measurement_unit': '计量单位',
}

# 表单字段映射（专门针对表单输入字段的标签）
FORM_FIELD_MAPPINGS = {
    # 客户管理表单字段
    'company_name': '企业名称',
    'contact_name': '联系人姓名',
    'contact_department': '部门',
    'contact_position': '职位',
    'contact_phone': '电话',
    'contact_email': '邮箱',
    'contact_notes': '备注',
    'country': '国家/地区',
    'region': '省/州',
    'address': '详细地址',
    'industry': '行业',
    'company_type': '企业类型',
    'notes': '备注',
    
    # 项目管理表单字段
    'project_name': '项目名称',
    'project_type': '项目类型',
    'project_stage': '项目阶段',
    'authorization_status': '授权状态',
    'authorization_code': '授权编号',
    'report_source': '报备来源',
    'activity_reason': '活动原因',
    'quotation_customer': '报价金额',
    'design_issues': '设计问题',
    'product_situation': '产品情况',
    'contractor': '承包商',
    'dealer': '经销商',
    'end_user': '最终用户',
    'system_integrator': '系统集成商',
    'vendor_sales_manager_id': '厂商销售',
    'delivery_date': '交付日期',
    'delivery_forecast': '交付预测',
    'project_manager': '项目经理',
    'estimated_value': '预估价值',
    'win_probability': '赢单概率',
    'competitor': '竞争对手',
    'risk_assessment': '风险评估',
    'next_steps': '下一步计划',
    
    # 报价单管理表单字段
    'quotation_number': '报价单号',
    'quotation_date': '报价日期',
    'valid_until': '有效期至',
    'payment_terms': '付款条件',
    'delivery_terms': '交付条件',
    'remarks': '备注说明',
    'customer_contact': '客户联系人',
    'customer_phone': '客户电话',
    'customer_email': '客户邮箱',
    'sales_representative': '销售代表',
    'quotation_status': '报价状态',
    'approval_status': '审批状态',
    'discount_rate': '折扣率',
    'tax_rate': '税率',
    'shipping_cost': '运费',
    'total_amount': '总金额',
    
    # 产品分析表单字段
    'product_name': '产品名称',
    'product_model': '型号/规格',
    'product_category': '产品类别',
    'manufacturer': '制造商',
    'supplier': '供应商',
    'unit_price': '单价',
    'stock_quantity': '库存数量',
    'minimum_order': '最小订购量',
    'lead_time': '交货周期',
    'warranty_period': '保修期',
    'technical_specs': '技术规格',
    'application_area': '应用领域',
    'market_segment': '市场细分',
    'sales_volume': '销售量',
    'profit_margin': '利润率',
    'competition_level': '竞争程度',
    
    # 报销管理表单字段
    'expense_number': '报销单编号',
    'title': '报销标题',
    'description': '报销说明',
    'customer_id': '客户',
    'contact_id': '联系人',
    'project_id': '关联项目',
    'total_amount': '总金额',
    'status': '审批状态',
    'owner_id': '申请人',
    'approved_by': '审批人',
    'approved_at': '审批时间',
    'approval_notes': '审批备注',
    'payment_status': '支付状态',
    'payment_amount': '支付金额',
    'payment_date': '支付日期',
    'payment_method': '支付方式',
    'payment_reference': '支付凭证号',
    'payment_notes': '支付备注',
    'paid_by': '支付操作人',
    'is_locked': '锁定状态',
    # 虚拟字段
    'detail_count': '明细数量',
    'expense_date': '报销日期',
    'expense_type': '报销类型',
    'expense_category': '费用类别',
    'amount': '金额',
    'currency': '货币',
    'exchange_rate': '汇率',
    'invoice_number': '发票号',
    'vendor_name': '供应商名称',
    'business_purpose': '业务目的',
    'expense_description': '费用描述',
    'receipt_attachment': '发票附件',
    'approval_workflow': '审批流程',
    'department_manager': '部门经理',
    'finance_approval': '财务审批',
    'reimbursement_status': '报销状态',
    'reimbursement_date': '报销到账日期',
    
    # 用户管理表单字段
    'username': '用户名',
    'real_name': '真实姓名',
    'email': '邮箱',
    'phone': '电话',
    'mobile': '手机',
    'department': '部门',
    'job_title': '职位',
    'role': '角色',
    'manager': '上级主管',
    'hire_date': '入职日期',
    'is_active': '活跃度',
    'is_department_manager': '是否部门经理',
    'avatar': '头像',
    'signature': '签名',
    'timezone': '时区',
    'language': '语言',
    'last_login': '最后登录',
    
    # 权限和共享字段
    'permissions': '权限',
    'access_level': '访问级别',
    'share_enabled': '启用共享',
    'shared_with_users': '共享用户',
    'visibility': '可见性',
    'owner': '所有者',
    'created_by': '创建者',
    'updated_by': '更新者',
    
    # 审批流程字段
    'template_name': '模板名称',
    'process_name': '流程名称',
    'step_name': '步骤名称',
    'step_order': '步骤顺序',
    'action_type': '动作类型',
    'approver_type': '审批人类型',
    'approver_id': '审批人',
    'approval_result': '审批结果',
    'approval_comment': '审批意见',
    'cc_users': '抄送用户',
    'send_email': '发送邮件',
    'is_parallel': '是否并行',
    'branch_condition': '分支条件',
    
    # 通用表单控件字段
    'search': '搜索',
    'keyword': '关键词',
    'filter': '筛选',
    'sort_by': '排序方式',
    'sort_order': '排序顺序',
    'page_size': '每页显示',
    'export_format': '导出格式',
    'date_range': '日期范围',
    'start_date': '开始日期',
    'end_date': '结束日期',
    'status_filter': '状态筛选',
    'category_filter': '类别筛选',
    'priority_filter': '优先级筛选',
}

# 合并所有字段映射
ALL_FIELD_MAPPINGS = {
    **COMMON_FIELDS,
    **PROJECT_FIELDS,
    **COMPANY_FIELDS,
    **USER_FIELDS,
    **PRODUCT_FIELDS,
    **ORDER_FIELDS,
    **APPROVAL_FIELDS,
    **PERFORMANCE_FIELDS,
    **FORM_FIELD_MAPPINGS,
}

def get_field_chinese_name(field_name):
    """
    获取字段的中文名称
    
    Args:
        field_name (str): 英文字段名
    
    Returns:
        str: 中文字段名，如果未找到映射则返回格式化的字段名
    """
    chinese_name = ALL_FIELD_MAPPINGS.get(field_name)
    if chinese_name:
        return chinese_name
    
    # 如果没有找到映射，尝试生成友好的中文名称
    return _generate_friendly_chinese_name(field_name)

def _generate_friendly_chinese_name(field_name):
    """
    为未映射的字段生成友好的中文名称
    
    Args:
        field_name (str): 英文字段名
    
    Returns:
        str: 生成的中文名称
    """
    # 简单的规则：将下划线替换为空格，保持原格式
    return field_name.replace('_', ' ').title()

def get_all_field_mappings():
    """
    获取所有字段映射
    
    Returns:
        dict: 完整的字段映射字典
    """
    return ALL_FIELD_MAPPINGS.copy()

def get_fields_by_category():
    """
    按类别获取字段映射
    
    Returns:
        dict: 按类别分组的字段映射
    """
    return {
        'common': COMMON_FIELDS,
        'project': PROJECT_FIELDS,
        'company': COMPANY_FIELDS,
        'user': USER_FIELDS,
        'product': PRODUCT_FIELDS,
        'order': ORDER_FIELDS,
        'approval': APPROVAL_FIELDS,
        'performance': PERFORMANCE_FIELDS,
        'form': FORM_FIELD_MAPPINGS,
    }

def is_field_mapped(field_name):
    """
    检查字段是否已有中文映射
    
    Args:
        field_name (str): 字段名
    
    Returns:
        bool: 是否已映射
    """
    return field_name in ALL_FIELD_MAPPINGS

def get_field_mapping_suggestions(field_names):
    """
    为字段列表生成映射建议
    
    Args:
        field_names (list): 字段名列表
    
    Returns:
        dict: 字段映射建议
    """
    suggestions = {}
    for field_name in field_names:
        if is_field_mapped(field_name):
            suggestions[field_name] = get_field_chinese_name(field_name)
        else:
            suggestions[field_name] = _generate_friendly_chinese_name(field_name)
    
    return suggestions

def get_form_field_chinese_name(field_name, table_name=None):
    """
    专门为表单字段获取中文名称
    
    Args:
        field_name (str): 字段名
        table_name (str, optional): 表名，用于更精确的映射
    
    Returns:
        str: 表单字段的中文标签
    """
    # 优先从表单字段映射中查找
    if field_name in FORM_FIELD_MAPPINGS:
        return FORM_FIELD_MAPPINGS[field_name]
    
    # 降级到通用字段映射
    return get_field_chinese_name(field_name)

def get_form_fields_by_module():
    """
    按模块获取表单字段映射
    
    Returns:
        dict: 按模块分组的表单字段映射
    """
    return {
        'customer': {
            'company_name': '企业名称',
            'contact_name': '联系人姓名',
            'contact_department': '部门',
            'contact_position': '职位',
            'contact_phone': '电话',
            'contact_email': '邮箱',
            'contact_notes': '备注',
            'country': '国家/地区',
            'region': '省/州',
            'address': '详细地址',
            'industry': '行业',
            'company_type': '企业类型',
            'notes': '备注',
        },
        'project': {
            'project_name': '项目名称',
            'project_type': '项目类型',
            'project_stage': '项目阶段',
            'authorization_status': '授权状态',
            'authorization_code': '授权编号',
            'report_source': '报备来源',
            'created_by': '创建人',
            'owner_id': '负责人',
            'vendor_sales_manager_id': '厂商销售',
            'current_stage': '当前阶段',
            'delivery_forecast': '交付预测',
            'activity_reason': '活动原因',
            'quotation_customer': '报价金额',
            'design_issues': '设计问题',
            'product_situation': '产品情况',
            'contractor': '承包商',
            'dealer': '经销商',
            'end_user': '最终用户',
            'system_integrator': '系统集成商',
            'vendor_sales_manager_id': '厂商销售',
            'delivery_date': '交付日期',
            'delivery_forecast': '交付预测',
            'project_manager': '项目经理',
            'estimated_value': '预估价值',
            'win_probability': '赢单概率',
            'competitor': '竞争对手',
            'risk_assessment': '风险评估',
            'next_steps': '下一步计划',
        },
        'quotation': {
            'quotation_number': '报价单号',
            'quotation_date': '报价日期',
            'valid_until': '有效期至',
            'payment_terms': '付款条件',
            'delivery_terms': '交付条件',
            'remarks': '备注说明',
            'customer_contact': '客户联系人',
            'customer_phone': '客户电话',
            'customer_email': '客户邮箱',
            'sales_representative': '销售代表',
            'quotation_status': '报价状态',
            'approval_status': '审批状态',
            'discount_rate': '折扣率',
            'tax_rate': '税率',
            'shipping_cost': '运费',
            'total_amount': '总金额',
        },
        'product_analysis': {
            'product_name': '产品名称',
            'product_model': '型号/规格',
            'product_category': '产品类别',
            'manufacturer': '制造商',
            'supplier': '供应商',
            'unit_price': '单价',
            'stock_quantity': '库存数量',
            'minimum_order': '最小订购量',
            'lead_time': '交货周期',
            'warranty_period': '保修期',
            'technical_specs': '技术规格',
            'application_area': '应用领域',
            'market_segment': '市场细分',
            'sales_volume': '销售量',
            'profit_margin': '利润率',
            'competition_level': '竞争程度',
        },
        'expense': {
            'expense_number': '报销单编号',
            'title': '报销标题',
            'description': '报销说明',
            'customer_id': '客户',
            'contact_id': '联系人',
            'project_id': '关联项目',
            'total_amount': '总金额',
            'currency': '货币',
            'status': '审批状态',
            'owner_id': '申请人',
            'created_at': '创建时间',
            'updated_at': '更新时间',
            'approved_by': '审批人',
            'approved_at': '审批时间',
            'approval_notes': '审批备注',
            'payment_status': '支付状态',
            'payment_amount': '支付金额',
            'payment_date': '支付日期',
            'payment_method': '支付方式',
            'payment_reference': '支付凭证号',
            'payment_notes': '支付备注',
            'paid_by': '支付操作人',
            'is_locked': '锁定状态',
            # 虚拟字段
            'detail_count': '明细数量',
            # 报销明细字段
            'expense_date': '报销日期',
            'expense_type': '报销类型',
            'expense_category': '费用类别',
            'amount': '金额',
            'exchange_rate': '汇率',
            'invoice_number': '发票号',
            'vendor_name': '供应商名称',
            'business_purpose': '业务目的',
            'expense_description': '费用描述',
            'receipt_attachment': '发票附件',
            'approval_workflow': '审批流程',
            'department_manager': '部门经理',
            'finance_approval': '财务审批',
            'reimbursement_status': '报销状态',
            'reimbursement_date': '报销到账日期',
        }
    }

def is_form_field_mapped(field_name):
    """
    检查表单字段是否已有中文映射
    
    Args:
        field_name (str): 字段名
    
    Returns:
        bool: 是否已映射
    """
    return field_name in FORM_FIELD_MAPPINGS