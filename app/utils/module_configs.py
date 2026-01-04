"""
模块配置定义 - 统一的移动端响应式配置

这个文件定义了各个模块的移动端卡片配置和桌面端模板配置。
所有模块的AJAX端点都应该使用这些配置来实现统一的响应式渲染。

配置格式:
{
    'module': '模块名称',
    'desktop_template': '桌面端模板路径',
    'items_var_name': '模板中数据变量名（可选，默认items）',
    'mobile_card': {
        'title_field': {'field': '标题字段名'},
        'link_url': '详情页URL模板',
        'badges': [徽章配置列表],
        'details': [详情配置列表],
        'actions': [操作配置列表（可选）]
    },
    'mobile_template': '传统移动端模板路径（可选）'
}
"""

from app.utils.responsive_renderer import ModuleConfigRegistry

def register_all_module_configs():
    """注册所有模块的配置"""
    
    # 客户管理模块配置
    ModuleConfigRegistry.register('customer', {
        'module': 'customer',
        'desktop_template': 'customer/customer_rows.html',
        'items_var_name': 'companies',
        'mobile_template': 'customer/customer_cards.html',  # 兼容现有模板
        'mobile_card': {
            'title_field': {'field': 'company_name'},
            'link_url': '/customer/{id}/view',
            'badges': [
                {'field': 'company_type', 'renderer': 'company_type_badge'},
                {'field': 'status', 'renderer': 'customer_status_badge'}
            ],
            'details': [
                {'field': 'owner', 'label': '负责人', 'renderer': 'owner'},
                {'field': 'industry', 'label': '行业', 'renderer': 'industry_badge'},
                {'custom_renderer': 'location', 'label': '地区'},
                {'field': 'main_contact_name', 'label': '主要联系人'},
                {'field': 'main_contact_phone', 'label': '联系电话', 'format': 'phone'},
                {'field': 'main_contact_email', 'label': '邮箱', 'format': 'email'},
                {'field': 'created_at', 'label': '创建时间', 'format': 'date'}
            ]
        }
    })
    
    # 项目管理模块配置
    ModuleConfigRegistry.register('project', {
        'module': 'project',
        'desktop_template': 'project/project_rows_standard.html',
        'items_var_name': 'projects',
        'mobile_card': {
            'title_field': {'field': 'project_name'},
            'link_url': '/project/view/{id}',
            'badges': [
                {'field': 'current_stage', 'renderer': 'project_stage'},
                {'field': 'is_active', 'renderer': 'status_badge'},
                {'field': 'project_type', 'renderer': 'project_type'}
            ],
            'details': [
                {'field': 'authorization_code', 'label': '授权编号'},
                {'field': 'owner', 'label': '拥有者', 'renderer': 'owner'},
                {'field': 'vendor_sales_manager', 'label': '厂商负责人', 'renderer': 'owner'},
                {'field': 'industry', 'label': '行业', 'renderer': 'industry_badge'},
                {'field': 'report_source', 'label': '来源', 'renderer': 'report_source_badge'},
                {'field': 'quotation_customer', 'label': '报价金额', 'format': 'currency'},
                {'field': 'delivery_forecast', 'label': '预测出货', 'format': 'date'},
                {'field': 'updated_at', 'label': '更新时间', 'format': 'datetime'}
            ]
        }
    })
    
    # 报价单管理模块配置
    ModuleConfigRegistry.register('quotation', {
        'module': 'quotation',
        'desktop_template': 'quotation/tw_list_rows.html',
        'items_var_name': 'quotations',
        'mobile_card': {
            'title_field': {'field': 'quotation_number'},
            'link_url': '/quotation/view/{id}',
            'badges': [
                {'field': 'approval_status', 'renderer': 'approval_status_badge'},
                {'field': 'amount', 'format': 'currency', 'color': 'success'}
            ],
            'details': [
                {'field': 'project_name', 'label': '项目名称'},
                {'field': 'owner', 'label': '负责人', 'renderer': 'owner'},
                {'field': 'amount', 'label': '报价金额', 'format': 'currency'},
                {'field': 'approval_status', 'label': '审核状态', 'renderer': 'approval_status_badge'},
                {'field': 'created_at', 'label': '创建时间', 'format': 'date'},
                {'field': 'updated_at', 'label': '更新时间', 'format': 'date'}
            ]
        }
    })
    
    # 产品分析模块配置
    ModuleConfigRegistry.register('product_analysis', {
        'module': 'product_analysis',
        'desktop_template': 'product_analysis/product_analysis_rows_simple.html',
        'items_var_name': 'items',
        'mobile_card': {
            'title_field': {'field': 'product_name'},
            'link_url': '/project/view/{project_id}',  # 链接到项目详情
            'badges': [
                {'field': 'current_stage', 'renderer': 'project_stage'},
                {'field': 'total_price', 'format': 'currency', 'color': 'success'}
            ],
            'details': [
                {'field': 'product_model', 'label': '产品型号'},
                {'field': 'product_mn', 'label': '产品编号'},
                {'field': 'project_name', 'label': '项目名称'},
                {'field': 'quotation_number', 'label': '报价单号'},
                {'field': 'owner_name', 'label': '负责人'},
                {'field': 'quantity', 'label': '数量'},
                {'field': 'unit_price', 'label': '单价', 'format': 'currency'},
                {'field': 'total_price', 'label': '总价', 'format': 'currency'}
            ]
        }
    })
    
    # 产品管理模块配置（产品库）
    ModuleConfigRegistry.register('product', {
        'module': 'product',
        'desktop_template': 'product/tw_list_rows.html',
        'items_var_name': 'products',
        'mobile_card': {
            'title_field': {'field': 'product_name'},
            'link_url': '/product/view/{id}',
            'badges': [
                {'field': 'type', 'renderer': 'product_type_badge'},
                {'field': 'status', 'renderer': 'product_status_badge'}
            ],
            'details': [
                {'field': 'product_mn', 'label': '型号'},
                {'field': 'category', 'label': '类别'},
                {'field': 'model', 'label': '规格型号'},
                {'field': 'brand', 'label': '品牌'},
                {'field': 'unit', 'label': '单位'},
                {'field': 'retail_price', 'label': '零售价', 'format': 'currency'},
                {'field': 'created_at', 'label': '创建时间', 'format': 'date'}
            ]
        }
    })

    # 研发库模块配置 - DEPRECATED (2025-12-26): 研发库已废弃，功能已由规格模板系统替代
    # ModuleConfigRegistry.register('product_management', {
    #     'module': 'product_management',
    #     'desktop_template': 'product_management/tw_list_rows.html',
    #     'items_var_name': 'products',
    #     'mobile_card': {
    #         'title_field': {'field': 'model'},
    #         'link_url': '/product-management/{id}',
    #         'badges': [
    #             {'field': 'status', 'renderer': 'dev_product_status_badge'}
    #         ],
    #         'details': [
    #             {'field': 'mn_code', 'label': '产品料号'},
    #             {'field': 'category_name', 'label': '产品分类'},
    #             {'field': 'subcategory_name', 'label': '子分类'},
    #             {'field': 'region_name', 'label': '销售区域'},
    #             {'field': 'creator_name', 'label': '创建人'},
    #             {'field': 'description', 'label': '产品描述'},
    #             {'field': 'created_at', 'label': '创建时间', 'format': 'date'}
    #         ]
    #     }
    # })
    
    # 报销管理模块配置
    ModuleConfigRegistry.register('expense', {
        'module': 'expense',
        'desktop_template': 'expense/tw_list_rows.html',
        'items_var_name': 'expenses',
        'mobile_card': {
            'title_field': {'field': 'expense_number'},
            'link_url': '/expense/detail/{id}',
            'badges': [
                {'field': 'status', 'renderer': 'expense_status_badge'},
                {'field': 'total_amount', 'format': 'currency', 'color': 'success'}
            ],
            'details': [
                {'field': 'title', 'label': '报销事由'},
                {'field': 'owner', 'label': '申请人'},
                {'field': 'total_amount', 'label': '报销金额', 'format': 'currency'},
                {'field': 'currency', 'label': '币种'},
                {'field': 'customer_name', 'label': '归属客户'},
                {'field': 'contact_name', 'label': '联系人'},
                {'field': 'project_name', 'label': '关联项目'},
                {'field': 'detail_count', 'label': '明细数量'},
                {'field': 'created_at', 'label': '创建时间', 'format': 'date'}
            ]
        }
    })
    
    print("✅ 所有模块配置已注册")


def get_module_config(module_name):
    """
    便利函数：获取指定模块的配置
    
    Args:
        module_name: 模块名称
    
    Returns:
        dict: 模块配置，如果不存在返回None
    """
    return ModuleConfigRegistry.get(module_name)


def list_registered_modules():
    """
    列出所有已注册的模块
    
    Returns:
        list: 模块名称列表
    """
    return list(ModuleConfigRegistry.get_all().keys())


# 自动注册所有配置
register_all_module_configs()