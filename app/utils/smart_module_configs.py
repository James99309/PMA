"""
智能模块配置系统 - 基于桌面端模板的自动化配置

功能:
1. 从桌面端模板自动生成移动端配置
2. 支持配置优先级和字段分类
3. 简化模块配置为声明式
4. 保持桌面端和移动端的完全一致性

使用方式:
```python
from app.utils.smart_module_configs import SmartModuleConfigRegistry

# 注册模块配置
SmartModuleConfigRegistry.register('quotation', {
    'source_template': 'quotation/tw_list_rows.html',
    'title_field': 'quotation_number',
    'priority_fields': ['owner', 'amount', 'project_name'],
    'badge_fields': ['approval_status', 'amount'],
    'exclude_fields': ['updated_at']
})

# 获取生成的配置
config = SmartModuleConfigRegistry.get('quotation')
```
"""

from typing import Dict, List, Any, Optional
import logging
from app.utils.template_parser import template_parser

logger = logging.getLogger(__name__)

class SmartModuleConfigRegistry:
    """智能模块配置注册表"""
    
    _configs = {}
    _generated_configs = {}  # 缓存生成的配置
    
    @classmethod
    def register(cls, module_name: str, config: Dict[str, Any]):
        """
        注册模块配置
        
        Args:
            module_name: 模块名称
            config: 简化配置
                {
                    'source_template': 'quotation/tw_list_rows.html',  # 来源桌面端模板
                    'title_field': 'quotation_number',                   # 标题字段
                    'priority_fields': ['owner', 'amount'],              # 优先显示字段
                    'badge_fields': ['approval_status', 'amount'],       # 徽章字段
                    'exclude_fields': ['updated_at'],                    # 排除字段
                    'desktop_template': 'quotation/tw_list_rows.html', # 桌面端模板(可选)
                    'items_var_name': 'quotations',                      # 变量名(可选)
                    'link_url': '/quotation/view/{id}',                  # 详情链接(可选)
                }
        """
        cls._configs[module_name] = config
        # 清除缓存，强制重新生成
        if module_name in cls._generated_configs:
            del cls._generated_configs[module_name]
        
        logger.info(f"✅ 智能模块配置已注册: {module_name}")
    
    @classmethod
    def get(cls, module_name: str) -> Optional[Dict[str, Any]]:
        """
        获取模块配置（自动生成移动端配置）
        
        Args:
            module_name: 模块名称
        
        Returns:
            完整的模块配置，包含自动生成的移动端配置
        """
        if module_name not in cls._configs:
            return None
        
        # 检查缓存
        if module_name in cls._generated_configs:
            return cls._generated_configs[module_name]
        
        # 生成配置
        smart_config = cls._configs[module_name]
        full_config = cls._generate_full_config(module_name, smart_config)
        
        # 缓存结果
        cls._generated_configs[module_name] = full_config
        return full_config
    
    @classmethod
    def _generate_full_config(cls, module_name: str, smart_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于智能配置生成完整配置
        
        Args:
            module_name: 模块名称
            smart_config: 智能配置
        
        Returns:
            完整的模块配置
        """
        try:
            source_template = smart_config.get('source_template')
            if not source_template:
                logger.error(f"模块 {module_name} 缺少 source_template 配置")
                return cls._fallback_config(module_name, smart_config)
            
            # 解析桌面端模板
            parsed_template = template_parser.parse_template(source_template)
            if not parsed_template or not parsed_template.get('fields'):
                logger.warning(f"无法解析模板 {source_template}，使用回退配置")
                return cls._fallback_config(module_name, smart_config)
            
            # 生成移动端配置
            mobile_config = cls._generate_mobile_config(parsed_template, smart_config)
            
            # 构建完整配置
            full_config = {
                'module': module_name,
                'desktop_template': smart_config.get('desktop_template', source_template),
                'items_var_name': smart_config.get('items_var_name', cls._guess_items_var_name(module_name)),
                'mobile_card': mobile_config,
                'source_template': source_template,
                'smart_config': smart_config  # 保留原始智能配置
            }
            
            logger.info(f"✅ 成功生成模块 {module_name} 的完整配置")
            return full_config
            
        except Exception as e:
            logger.error(f"生成模块 {module_name} 配置失败: {e}")
            return cls._fallback_config(module_name, smart_config)
    
    @classmethod
    def _generate_mobile_config(cls, parsed_template: Dict[str, Any], smart_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成移动端卡片配置
        
        Args:
            parsed_template: 解析后的模板信息
            smart_config: 智能配置
        
        Returns:
            移动端卡片配置
        """
        fields = parsed_template.get('fields', [])
        if not fields:
            return {}
        
        # 获取配置参数
        title_field = smart_config.get('title_field', parsed_template.get('title_field'))
        priority_fields = smart_config.get('priority_fields', [])
        badge_fields = smart_config.get('badge_fields', [])
        exclude_fields = smart_config.get('exclude_fields', [])
        link_url = smart_config.get('link_url')
        
        # 构建移动端配置
        mobile_config = {
            'title_field': {'field': title_field} if title_field else None,
            'badges': [],
            'details': []
        }
        
        # 如果有link_url配置，使用它；否则尝试从模板中提取
        if link_url:
            mobile_config['link_url'] = link_url
        else:
            # 尝试从第一个带链接的字段中推断链接模式
            for field in fields:
                if field.get('has_link') and field.get('link_url'):
                    # 简化链接URL模式
                    url = field['link_url']
                    if 'url_for(' in url and '.id)' in url:
                        # 提取模块和动作
                        module_part = url.split("'")[1] if "'" in url else ''
                        if '.' in module_part:
                            module, action = module_part.split('.', 1)
                            mobile_config['link_url'] = f'/{module.replace("_", "/")}/{{{field.get("field_name", "id")}}}'
                    break
        
        # 处理字段映射
        processed_fields = set()
        
        # 1. 先处理徽章字段
        for field in fields:
            field_name = field.get('field_name')
            if not field_name or field_name in exclude_fields or field_name in processed_fields:
                continue
            
            if field_name in badge_fields:
                badge_config = cls._create_field_config(field, 'badge')
                if badge_config:
                    mobile_config['badges'].append(badge_config)
                    processed_fields.add(field_name)
        
        # 2. 处理详情字段
        # 按优先级排序字段
        sorted_fields = []
        for priority_field in priority_fields:
            for field in fields:
                if field.get('field_name') == priority_field and priority_field not in processed_fields:
                    sorted_fields.append(field)
                    processed_fields.add(priority_field)
                    break
        
        # 添加剩余字段
        for field in fields:
            field_name = field.get('field_name')
            if field_name and field_name not in exclude_fields and field_name not in processed_fields:
                sorted_fields.append(field)
                processed_fields.add(field_name)
        
        # 生成详情配置
        for field in sorted_fields:
            detail_config = cls._create_field_config(field, 'detail')
            if detail_config:
                mobile_config['details'].append(detail_config)
        
        return mobile_config
    
    @classmethod
    def _create_field_config(cls, field: Dict[str, Any], field_type: str) -> Optional[Dict[str, Any]]:
        """
        创建字段配置
        
        Args:
            field: 解析的字段信息
            field_type: 字段类型 ('badge' 或 'detail')
        
        Returns:
            字段配置
        """
        field_name = field.get('field_name')
        if not field_name:
            return None
        
        config = {
            'field': field_name,
            'label': cls._field_name_to_label(field_name)
        }
        
        # 添加渲染器
        if field.get('renderer'):
            config['renderer'] = field['renderer']
            # 保留渲染器参数
            if field.get('renderer_args'):
                config['renderer_args'] = field['renderer_args']
        
        # 添加格式化
        if field.get('format_type'):
            config['format'] = field['format_type']
        
        # 为徽章添加颜色
        if field_type == 'badge':
            if 'status' in field_name.lower() or 'approval' in field_name.lower():
                config['color'] = 'info'
            elif 'amount' in field_name.lower() or 'price' in field_name.lower():
                config['color'] = 'success'
            else:
                config['color'] = 'secondary'
        
        # 处理嵌套字段
        if field.get('is_nested'):
            config['nested'] = {
                'object': field.get('nested_object'),
                'field': field.get('nested_field')
            }
        
        # 处理条件渲染
        if field.get('conditions'):
            config['conditions'] = field['conditions']
        
        return config
    
    @classmethod
    def _field_name_to_label(cls, field_name: str) -> str:
        """将字段名转换为显示标签"""
        field_labels = {
            # 基础信息字段
            'company_name': '公司名称',
            'customer_name': '客户名称', 
            'product_name': '产品名称',
            'project_name': '项目名称',
            'quotation_number': '报价单号',
            'expense_number': '报销单号',
            'title': '标题',
            
            # 类型和状态字段
            'company_type': '企业类型',
            'industry': '行业',
            'status': '状态',
            'approval_status': '审核状态',
            'current_stage': '当前阶段',
            'project_type': '项目类型',
            'confirmation_badge_status': '确认状态',
            
            # 人员字段
            'owner': '负责人',
            'contact_name': '联系人',
            'main_contact_name': '主要联系人',
            
            # 金额字段
            'amount': '金额',
            'unit_price': '单价',
            'total_price': '总价',
            'currency': '币种',
            
            # 产品字段
            'product_model': '产品型号',
            'quantity': '数量',
            
            # 时间字段
            'created_at': '创建时间',
            'updated_at': '更新时间',
            
            # 项目字段
            'project': '项目'
        }
        
        return field_labels.get(field_name, field_name)
    
    @classmethod
    def _guess_items_var_name(cls, module_name: str) -> str:
        """推断项目变量名"""
        # 大部分模块使用复数形式
        if module_name.endswith('s'):
            return module_name
        elif module_name == 'quotation':
            return 'quotations'
        elif module_name == 'product_analysis':
            return 'items'
        elif module_name == 'expense':
            return 'expenses'
        else:
            return f"{module_name}s"
    
    @classmethod
    def _fallback_config(cls, module_name: str, smart_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成回退配置
        
        Args:
            module_name: 模块名称
            smart_config: 智能配置
        
        Returns:
            基础配置
        """
        return {
            'module': module_name,
            'desktop_template': smart_config.get('desktop_template', f'{module_name}/{module_name}_rows.html'),
            'items_var_name': smart_config.get('items_var_name', cls._guess_items_var_name(module_name)),
            'mobile_card': {
                'title_field': {'field': smart_config.get('title_field', 'name')},
                'badges': [],
                'details': []
            },
            'smart_config': smart_config
        }
    
    @classmethod
    def get_all(cls) -> Dict[str, Dict[str, Any]]:
        """获取所有注册的模块配置"""
        result = {}
        for module_name in cls._configs:
            result[module_name] = cls.get(module_name)
        return result
    
    @classmethod
    def list_modules(cls) -> List[str]:
        """列出所有注册的模块名称"""
        return list(cls._configs.keys())
    
    @classmethod
    def reload_module(cls, module_name: str):
        """重新加载模块配置（清除缓存）"""
        if module_name in cls._generated_configs:
            del cls._generated_configs[module_name]
            logger.info(f"✅ 已重新加载模块 {module_name} 的配置")


# 注册所有模块的智能配置
def register_all_smart_module_configs():
    """注册所有模块的智能配置"""
    
    # 客户管理模块
    SmartModuleConfigRegistry.register('customer', {
        'source_template': 'customer/customer_rows.html',
        'desktop_template': 'customer/customer_rows.html',
        'items_var_name': 'companies',
        'title_field': 'company_name',
        'link_url': '/customer/{id}/view',
        'priority_fields': ['owner', 'industry', 'main_contact_name'],
        'badge_fields': ['company_type', 'status'],
        'exclude_fields': []
    })
    
    # 项目管理模块
    SmartModuleConfigRegistry.register('project', {
        'source_template': 'project/project_rows_standard.html',
        'desktop_template': 'project/project_rows_standard.html',
        'items_var_name': 'projects',
        'title_field': 'project_name',
        'link_url': '/project/view/{id}',
        'priority_fields': ['owner', 'vendor_sales_manager', 'industry'],
        'badge_fields': ['current_stage', 'is_active', 'project_type'],
        'exclude_fields': []
    })
    
    # 报价单管理模块
    SmartModuleConfigRegistry.register('quotation', {
        'source_template': 'quotation/tw_list_rows.html',
        'desktop_template': 'quotation/tw_list_rows.html',
        'items_var_name': 'quotations',
        'title_field': 'quotation_number',
        'link_url': '/quotation/view/{id}',
        'priority_fields': ['owner', 'amount', 'project_name'],
        'badge_fields': ['approval_status', 'amount'],
        'exclude_fields': ['updated_at']
    })
    
    # 产品分析模块
    SmartModuleConfigRegistry.register('product_analysis', {
        'source_template': 'product_analysis/product_analysis_rows_simple.html',
        'desktop_template': 'product_analysis/product_analysis_rows_simple.html',
        'items_var_name': 'items',
        'title_field': 'product_name',
        'link_url': '/project/view/{project_id}',
        'priority_fields': ['product_model', 'project_name', 'owner_name'],
        'badge_fields': ['current_stage', 'total_price'],
        'exclude_fields': []
    })
    
    # 产品库模块
    SmartModuleConfigRegistry.register('product', {
        'source_template': 'product/tw_list_rows.html',
        'desktop_template': 'product/tw_list_rows.html',
        'items_var_name': 'products',
        'title_field': 'product_name',
        'link_url': '/product/view/{id}',
        'priority_fields': ['product_mn', 'category', 'brand'],
        'badge_fields': ['type', 'status'],
        'exclude_fields': []
    })

    # 研发库模块
    SmartModuleConfigRegistry.register('product_management', {
        'source_template': 'product_management/tw_list_rows.html',
        'desktop_template': 'product_management/tw_list_rows.html',
        'items_var_name': 'products',
        'title_field': 'model',
        'link_url': '/product-management/{id}',
        'priority_fields': ['mn_code', 'category', 'creator'],
        'badge_fields': ['status'],
        'exclude_fields': []
    })

    # 报销管理模块
    SmartModuleConfigRegistry.register('expense', {
        'source_template': 'expense/tw_list_rows.html',
        'desktop_template': 'expense/tw_list_rows.html',
        'items_var_name': 'expenses',
        'title_field': 'expense_number',
        'link_url': '/expense/detail/{id}',
        'priority_fields': ['title', 'owner', 'total_amount'],
        'badge_fields': ['status', 'total_amount'],
        'exclude_fields': []
    })
    
    print("✅ 所有智能模块配置已注册")


# 便利函数
def get_smart_module_config(module_name: str) -> Optional[Dict[str, Any]]:
    """
    便利函数：获取智能模块配置
    
    Args:
        module_name: 模块名称
    
    Returns:
        模块配置
    """
    return SmartModuleConfigRegistry.get(module_name)

def reload_smart_module_config(module_name: str):
    """
    便利函数：重新加载智能模块配置
    
    Args:
        module_name: 模块名称
    """
    return SmartModuleConfigRegistry.reload_module(module_name)

# 自动注册所有配置
register_all_smart_module_configs()