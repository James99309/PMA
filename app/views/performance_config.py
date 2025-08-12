from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from flask_babel import get_locale
from datetime import datetime
from app import db
from app.models.user import User
from app.models.role_permissions import RolePermission
from app.models.performance_config import (
    PerformanceMetricsDefinition, RolePerformanceConfig, RolePerformanceItem, 
    PerformanceFormulaTemplate, RolePerformanceAccess, ConfigurablePerformanceService
)
from app.models.data_source_config import DataTableConfig, DataFieldConfig, FormulaTemplate
from app.permissions import permission_required
from app.utils.dictionary_helpers import get_role_display_name_from_dict

import json
import logging
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

logger = logging.getLogger(__name__)

performance_config_bp = Blueprint('performance_config', __name__, url_prefix='/performance/config')

@performance_config_bp.route('/')
@login_required  
@permission_required('performance_management', 'edit')
def role_config():
    """绩效配置主页面"""
    try:
        # 详细的服务器端调试信息
        logger.info("=== 绩效配置页面加载开始 ===")
        logger.info(f"用户ID: {current_user.id}")
        logger.info(f"用户名: {current_user.username}")
        logger.info(f"用户角色: {current_user.role}")
        logger.info(f"请求URL: {request.url}")
        logger.info(f"请求方法: {request.method}")
        logger.info(f"请求参数: {request.args}")
        logger.info(f"用户代理: {request.headers.get('User-Agent', 'N/A')}")
        logger.info(f"会话语言: {get_locale()}")
        
        # 获取所有可配置的角色
        logger.info("正在获取可配置角色列表...")
        available_roles = get_available_roles()
        logger.info(f"找到 {len(available_roles)} 个可配置角色: {[r['role_code'] for r in available_roles]}")
        
        # 获取当前用户的默认角色（如果有的话）
        default_role = request.args.get('role', available_roles[0]['role_code'] if available_roles else 'sales_director')
        logger.info(f"默认角色: {default_role}")
        
        # 加载共享用户树（使用通用模组）
        shareable_users_tree = []
        try:
            from app.utils.sharing import get_shareable_users_tree
            shareable_users_tree = get_shareable_users_tree(current_user, 'performance')
            logger.info(f"加载共享用户树成功：{len(shareable_users_tree)} 个组织")
        except ImportError as e:
            logger.warning(f"未找到sharing模块：{e}")
        except Exception as e:
            logger.warning(f"加载共享用户树失败：{e}")
        
        # 检查模板是否存在
        template_path = 'performance/role_config_optimized_v2.html'
        logger.info(f"使用模板: {template_path}")
        
        logger.info("=== 绩效配置页面加载成功 ===")
        
        return render_template(template_path,
                             available_roles=available_roles,
                             default_role=default_role,
                             shareable_users_tree=shareable_users_tree)
    
    except Exception as e:
        logger.error(f"=== 绩效配置页面加载失败 ===")
        logger.error(f"错误类型: {type(e).__name__}")
        logger.error(f"错误消息: {str(e)}")
        logger.error(f"错误堆栈: ", exc_info=True)
        logger.error("=== 错误详情结束 ===")
        
        # 根据具体错误类型提供更详细的错误信息
        if "TemplateNotFound" in str(type(e)):
            error_msg = f"模板文件未找到: {e}"
        elif "permission" in str(e).lower():
            error_msg = f"权限检查失败: {e}"
        elif "database" in str(e).lower() or "sql" in str(e).lower():
            error_msg = f"数据库错误: {e}"
        else:
            error_msg = f"页面加载失败: {e}"
        
        flash(error_msg, 'error')
        return redirect(url_for('main.index'))

@performance_config_bp.route('/api/roles')
@login_required
@permission_required('performance_management', 'edit')  
def api_get_roles():
    """获取所有可配置角色列表API"""
    try:
        roles = get_available_roles()
        return jsonify({
            'success': True,
            'data': roles
        })
    except Exception as e:
        logger.error(f"获取角色列表失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取角色列表失败: {str(e)}'
        })

@performance_config_bp.route('/api/role/<role_code>')
@login_required
@permission_required('performance_management', 'edit')
def api_get_role_config(role_code):
    """获取指定角色的绩效配置API"""
    try:
        # 详细的API调试信息
        logger.info(f"=== API: 获取角色配置 {role_code} ===")
        logger.info(f"请求用户: {current_user.username} (ID: {current_user.id})")
        logger.info(f"请求时间: {datetime.utcnow()}")
        logger.info(f"用户代理: {request.headers.get('User-Agent', 'N/A')}")
        
        # 查询角色配置
        from app.models.performance_config import RolePerformanceConfig, RolePerformanceItem
        
        logger.info(f"正在查询角色 {role_code} 的配置...")
        role_config = RolePerformanceConfig.query.filter_by(role=role_code).first()
        
        if not role_config:
            logger.info(f"角色 {role_code} 暂无配置，返回默认配置")
            # 返回默认配置
            default_config = {
                'role': role_code,
                'config_name': f'{get_role_display_name_from_dict(role_code)}绩效方案',
                'description': '待配置的绩效方案',
                'access_scope': 'personal',
                'is_active': True,
                'items': []
            }
            logger.info(f"默认配置: {default_config}")
            return jsonify({
                'success': True,
                'data': default_config
            })
        
        logger.info(f"找到角色配置: ID={role_config.id}, 名称={role_config.config_name}")
        
        # 获取配置项目
        logger.info("正在获取绩效项目...")
        items = RolePerformanceItem.query.filter_by(
            role_config_id=role_config.id,
            is_enabled=True
        ).order_by(RolePerformanceItem.sort_order).all()
        
        logger.info(f"找到 {len(items)} 个启用的绩效项目")
        
        config_data = {
            'role': role_config.role,
            'config_name': role_config.config_name,
            'description': role_config.description,
            'access_scope': get_role_access_scope(role_code),
            'is_active': role_config.is_active,
            'items': [item.to_dict() for item in items]
        }
        
        logger.info(f"返回配置数据: {len(config_data['items'])} 个项目")
        logger.info("=== API调用成功 ===")
        
        return jsonify({
            'success': True,
            'data': config_data
        })
        
    except Exception as e:
        logger.error(f"=== API调用失败: 获取角色配置 {role_code} ===")
        logger.error(f"错误类型: {type(e).__name__}")
        logger.error(f"错误消息: {str(e)}")
        logger.error(f"错误堆栈: ", exc_info=True)
        logger.error("=== API错误详情结束 ===")
        
        return jsonify({
            'success': False,
            'message': f'获取角色配置失败: {str(e)}',
            'error_type': type(e).__name__,
            'debug_info': {
                'role_code': role_code,
                'user_id': current_user.id,
                'timestamp': datetime.utcnow().isoformat()
            }
        }), 500

@performance_config_bp.route('/api/role/<role_code>', methods=['POST'])
@login_required
@permission_required('performance_management', 'edit')
def api_save_role_config(role_code):
    """保存指定角色的绩效配置API"""
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'message': '请求数据为空'
        })
    
    # 验证数据
    required_fields = ['config_name']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'message': f'缺少必要字段: {field}'
            })
    
    # 验证选择的项目
    if 'selected_items' not in data or not data['selected_items']:
        return jsonify({
            'success': False,
            'message': '请至少选择一个绩效项目'
        })
    
    # 可选验证：如果有scope_users则使用，否则使用默认个人范围
    scope_users = data.get('scope_users', [])
    if not scope_users:
        # 使用默认个人范围
        data_scopes = ['personal']
    else:
        # 使用指定用户范围
        data_scopes = ['custom']
    
    from app.models.performance_config import RolePerformanceConfig, RolePerformanceItem
    
    # 查找或创建角色配置
    try:
        role_config = RolePerformanceConfig.query.filter_by(role=role_code).first()
        if not role_config:
            role_config = RolePerformanceConfig(
                role=role_code,
                created_by=current_user.id
            )
            db.session.add(role_config)
            db.session.flush()  # 获取ID但不提交
        
        # 更新基本配置
        role_config.config_name = data['config_name']
        role_config.description = data.get('description', '')
        role_config.is_active = data.get('is_active', True)
        role_config.updated_by = current_user.id
        role_config.updated_at = datetime.utcnow()
        
        # 删除现有的配置项目
        RolePerformanceItem.query.filter_by(role_config_id=role_config.id).delete()
        
        # 从选择的预置项目创建绩效项目
        selected_item_ids = data.get('selected_items', [])
        
        for i, item_id in enumerate(selected_item_ids):
            # 查找预置模板
            template = FormulaTemplate.query.get(item_id)
            if not template:
                return jsonify({
                    'success': False,
                    'message': f'预置项目 {item_id} 不存在'
                })
            
            # 从模板创建绩效项目
            item = create_performance_item_from_template_v2(role_config, template, scope_users, i + 1)
            db.session.add(item)
        
        # 保存访问权限配置（使用选择的数据范围）
        primary_scope = data_scopes[0] if data_scopes else 'personal'
        save_role_access_config(role_code, primary_scope)
        
        db.session.commit()
        
        logger.info(f"角色绩效配置保存成功: {role_code}, 项目数: {len(selected_item_ids)}")
        
        return jsonify({
            'success': True,
            'message': f'角色配置保存成功，共配置{len(selected_item_ids)}个绩效项目'
        })
        
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"数据完整性错误 {role_code}: {e}")
        return jsonify({
            'success': False,
            'message': '数据保存失败：存在重复的项目代码或其他约束冲突'
        })
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"数据库错误 {role_code}: {e}")
        return jsonify({
            'success': False,
            'message': '数据库操作失败，请重试'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"保存角色配置失败 {role_code}: {e}")
        return jsonify({
            'success': False,
            'message': f'保存失败: {str(e)}'
        })

@performance_config_bp.route('/api/metrics')
@login_required
@permission_required('performance_management', 'edit')
def api_get_metrics():
    """获取可用的绩效指标列表API"""
    try:
        from app.models.performance_config import PerformanceMetricsDefinition
        
        metrics = PerformanceMetricsDefinition.query.filter_by(is_active=True).all()
        
        metrics_data = []
        for metric in metrics:
            metrics_data.append({
                'id': metric.id,
                'metric_code': metric.metric_code,
                'metric_name': metric.metric_name,
                'metric_category': metric.metric_category,
                'data_type': metric.data_type,
                'default_unit': metric.default_unit,
                'description': metric.description,
                'is_system_metric': metric.is_system_metric
            })
        
        return jsonify({
            'success': True,
            'data': metrics_data
        })
        
    except Exception as e:
        logger.error(f"获取绩效指标失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取绩效指标失败: {str(e)}'
        })

@performance_config_bp.route('/api/formula-templates')
@login_required
@permission_required('performance_management', 'edit')
def api_get_formula_templates():
    """获取公式模板列表API"""
    try:
        from app.models.performance_config import PerformanceFormulaTemplate
        
        templates = PerformanceFormulaTemplate.query.all()
        
        templates_data = []
        for template in templates:
            templates_data.append({
                'id': template.id,
                'template_name': template.template_name,
                'template_category': template.template_category,
                'formula_expression': template.formula_expression,
                'description': template.description,
                'variables_definition': template.variables_definition,
                'example_usage': template.example_usage,
                'is_system_template': template.is_system_template
            })
        
        return jsonify({
            'success': True,
            'data': templates_data
        })
        
    except Exception as e:
        logger.error(f"获取公式模板失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取公式模板失败: {str(e)}'
        })

@performance_config_bp.route('/api/preview/<role_code>')
@login_required
@permission_required('performance_management', 'edit')
def api_preview_config(role_code):
    """预览角色配置效果API"""
    try:
        # 获取角色配置
        config_response = api_get_role_config(role_code)
        config_data = config_response.get_json()
        
        if not config_data.get('success'):
            return config_data
        
        role_config = config_data['data']
        
        # 模拟生成预览数据（实际数据）
        preview_data = generate_preview_data(role_code, role_config)
        
        return jsonify({
            'success': True,
            'data': {
                'role': role_code,
                'config': role_config,
                'preview': preview_data
            }
        })
        
    except Exception as e:
        logger.error(f"生成预览数据失败 {role_code}: {e}")
        return jsonify({
            'success': False,
            'message': f'生成预览失败: {str(e)}'
        })

@performance_config_bp.route('/api/data-tables')
@login_required
@permission_required('performance_management', 'edit')
def api_get_data_tables():
    """获取可用的数据表列表API"""
    try:
        logger.info("=== API: 获取数据表列表 ===")
        
        # 查询所有启用的绩效数据源表
        tables = DataTableConfig.query.filter_by(
            is_active=True, 
            is_performance_source=True
        ).order_by(DataTableConfig.category, DataTableConfig.display_name).all()
        
        logger.info(f"找到 {len(tables)} 个可用数据表")
        
        tables_data = []
        for table in tables:
            table_dict = table.to_dict()
            # 添加字段统计
            table_dict['field_count'] = table.field_configs.filter_by(is_performance_metric=True).count()
            tables_data.append(table_dict)
        
        # 按类别分组
        grouped_tables = {}
        for table in tables_data:
            category = table['category']
            if category not in grouped_tables:
                grouped_tables[category] = []
            grouped_tables[category].append(table)
        
        logger.info("=== 数据表列表获取成功 ===")
        
        return jsonify({
            'success': True,
            'data': {
                'tables': tables_data,
                'grouped_tables': grouped_tables,
                'total_count': len(tables_data)
            }
        })
        
    except Exception as e:
        logger.error(f"=== 获取数据表列表失败 ===")
        logger.error(f"错误: {e}", exc_info=True)
        
        return jsonify({
            'success': False,
            'message': f'获取数据表列表失败: {str(e)}'
        }), 500

@performance_config_bp.route('/api/table/<table_name>/fields')
@login_required
@permission_required('performance_management', 'edit')
def api_get_table_fields(table_name):
    """获取指定数据表的字段列表API"""
    try:
        logger.info(f"=== API: 获取表 {table_name} 的字段列表 ===")
        
        # 查找数据表配置
        table_config = DataTableConfig.query.filter_by(
            table_name=table_name,
            is_active=True
        ).first()
        
        if not table_config:
            return jsonify({
                'success': False,
                'message': f'数据表 {table_name} 不存在或未启用'
            }), 404
        
        # 获取字段配置
        fields = DataFieldConfig.query.filter_by(
            table_config_id=table_config.id
        ).order_by(
            DataFieldConfig.is_performance_metric.desc(),
            DataFieldConfig.performance_category,
            DataFieldConfig.field_name
        ).all()
        
        logger.info(f"找到 {len(fields)} 个字段")
        
        fields_data = []
        for field in fields:
            field_dict = field.to_dict()
            # 添加完整字段引用
            field_dict['full_field_name'] = field.full_field_name
            field_dict['formula_reference'] = field.formula_reference
            fields_data.append(field_dict)
        
        # 按类别分组
        grouped_fields = {}
        performance_fields = []
        
        for field in fields_data:
            if field['is_performance_metric']:
                performance_fields.append(field)
                
                category = field['performance_category'] or 'other'
                if category not in grouped_fields:
                    grouped_fields[category] = []
                grouped_fields[category].append(field)
        
        logger.info(f"其中 {len(performance_fields)} 个绩效字段")
        logger.info("=== 字段列表获取成功 ===")
        
        return jsonify({
            'success': True,
            'data': {
                'table_info': table_config.to_dict(),
                'fields': fields_data,
                'performance_fields': performance_fields,
                'grouped_fields': grouped_fields,
                'total_count': len(fields_data),
                'performance_count': len(performance_fields)
            }
        })
        
    except Exception as e:
        logger.error(f"=== 获取表字段失败: {table_name} ===")
        logger.error(f"错误: {e}", exc_info=True)
        
        return jsonify({
            'success': False,
            'message': f'获取表字段失败: {str(e)}'
        }), 500

@performance_config_bp.route('/api/formula-templates-extended')
@login_required
@permission_required('performance_management', 'edit')
def api_get_formula_templates_extended():
    """获取扩展公式模板列表API"""
    try:
        logger.info("=== API: 获取扩展公式模板列表 ===")
        
        templates = FormulaTemplate.query.filter_by(is_active=True).order_by(
            FormulaTemplate.template_category,
            FormulaTemplate.usage_count.desc(),
            FormulaTemplate.template_name
        ).all()
        
        logger.info(f"找到 {len(templates)} 个活动模板")
        
        templates_data = []
        for template in templates:
            templates_data.append(template.to_dict())
        
        # 按类别分组
        grouped_templates = {}
        for template in templates_data:
            category = template['template_category'] or 'other'
            if category not in grouped_templates:
                grouped_templates[category] = []
            grouped_templates[category].append(template)
        
        logger.info("=== 扩展公式模板列表获取成功 ===")
        
        return jsonify({
            'success': True,
            'data': {
                'templates': templates_data,
                'grouped_templates': grouped_templates,
                'total_count': len(templates_data)
            }
        })
        
    except Exception as e:
        logger.error(f"=== 获取扩展公式模板失败 ===")
        logger.error(f"错误: {e}", exc_info=True)
        
        return jsonify({
            'success': False,
            'message': f'获取扩展公式模板失败: {str(e)}'
        }), 500

@performance_config_bp.route('/api/preset-items')
@login_required
@permission_required('performance_management', 'edit')
def api_get_preset_items():
    """获取预置绩效项目列表API"""
    try:
        logger.info("=== API: 获取预置绩效项目列表 ===")
        
        # 查询所有启用的系统预置模板
        templates = FormulaTemplate.query.filter_by(
            is_active=True,
            is_system_template=True
        ).order_by(
            FormulaTemplate.template_category,
            FormulaTemplate.template_name
        ).all()
        
        logger.info(f"找到 {len(templates)} 个预置绩效项目")
        
        items_data = []
        for template in templates:
            item = {
                'id': template.id,
                'name': template.template_name,
                'category': template.template_category,
                'description': template.description,
                'formula': template.formula_expression,
                'result_type': template.result_type,
                'result_unit': template.result_unit,
                'icon': get_category_icon(template.template_category)
            }
            items_data.append(item)
        
        # 按类别分组
        grouped_items = {}
        for item in items_data:
            category = item['category'] or 'other'
            category_name = get_category_display_name(category)
            if category_name not in grouped_items:
                grouped_items[category_name] = []
            grouped_items[category_name].append(item)
        
        logger.info("=== 预置绩效项目列表获取成功 ===")
        
        return jsonify({
            'success': True,
            'data': {
                'items': items_data,
                'grouped_items': grouped_items,
                'total_count': len(items_data)
            }
        })
        
    except Exception as e:
        logger.error(f"=== 获取预置绩效项目失败 ===")
        logger.error(f"错误: {e}", exc_info=True)
        
        return jsonify({
            'success': False,
            'message': f'获取预置绩效项目失败: {str(e)}'
        }), 500

@performance_config_bp.route('/api/shareable-users-tree')
@login_required
@permission_required('performance_management', 'edit')
def api_get_shareable_users_tree():
    """获取可分享用户的组织架构数据API"""
    try:
        logger.info("=== API: 获取用户组织架构 ===")
        
        # 使用与共享设置相同的逻辑获取组织架构
        from app.utils.sharing_utils import get_shareable_users_tree
        
        # 获取组织架构数据
        users_tree = get_shareable_users_tree(current_user)
        
        logger.info(f"获取到 {len(users_tree)} 个顶级组织")
        
        # 转换为适合前端使用的格式
        tree_data = []
        for org in users_tree:
            org_data = {
                'id': org.id,
                'name': org.name,
                'type': org.type,
                'children': []
            }
            
            # 处理子组织和用户
            for child in org.children:
                child_data = {
                    'id': child.id,
                    'name': child.name,
                    'type': child.type,
                    'user_id': getattr(child, 'user_id', None),
                    'children': []
                }
                
                # 如果是部门，处理部门下的用户
                if hasattr(child, 'children'):
                    for user in child.children:
                        user_data = {
                            'id': user.id,
                            'name': user.name,
                            'type': user.type,
                            'user_id': user.user_id
                        }
                        child_data['children'].append(user_data)
                
                org_data['children'].append(child_data)
            
            tree_data.append(org_data)
        
        logger.info("=== 组织架构数据获取成功 ===")
        
        return jsonify({
            'success': True,
            'data': tree_data
        })
        
    except ImportError:
        # 如果没有sharing_utils，使用备用方案
        logger.warning("未找到sharing_utils，使用备用方案")
        return get_simple_users_tree()
        
    except Exception as e:
        logger.error(f"=== 获取组织架构失败 ===")
        logger.error(f"错误: {e}", exc_info=True)
        
        # 返回简单的用户列表作为备用
        return get_simple_users_tree()

@performance_config_bp.route('/api/field-values/<table_name>/<field_name>')
@login_required
@permission_required('performance_management', 'edit')
def api_get_field_values(table_name, field_name):
    """获取指定字段的实际值API"""
    try:
        logger.info(f"=== API: 获取字段值 {table_name}.{field_name} ===")
        
        # 验证表名和字段名
        valid_tables = ['quotations', 'pricing_orders', 'companies', 'projects', 'contacts', 'products', 'users', 'expenses', 'settlements']
        if table_name not in valid_tables:
            return jsonify({
                'success': False,
                'message': f'不支持的数据表: {table_name}'
            }), 400
        
        from sqlalchemy import text, inspect
        
        # 检查字段是否存在
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        if field_name not in columns:
            return jsonify({
                'success': False, 
                'message': f'字段 {field_name} 在表 {table_name} 中不存在'
            }), 400
        
        # 查询字段的不同值（限制数量避免性能问题）
        query = text(f"""
            SELECT DISTINCT {field_name} as field_value, COUNT(*) as count
            FROM {table_name} 
            WHERE {field_name} IS NOT NULL 
            GROUP BY {field_name}
            ORDER BY count DESC, {field_name}
            LIMIT 20
        """)
        
        result = db.session.execute(query).fetchall()
        
        values = [str(row.field_value) for row in result if row.field_value is not None]
        counts = {str(row.field_value): row.count for row in result if row.field_value is not None}
        
        # 生成使用示例
        examples = []
        if values:
            most_common_value = values[0] if values else None
            if most_common_value:
                examples.append(f"{{{table_name}.{field_name}}} = '{most_common_value}'")
                if len(values) > 1:
                    examples.append(f"{{{table_name}.{field_name}}} IN ('{values[0]}', '{values[1]}')")
        
        # 根据字段类型提供更多示例
        field_type_examples = {
            'status': [f"{{{table_name}.{field_name}}} = 'active'", f"{{{table_name}.{field_name}}} != 'deleted'"],
            'approval_status': [f"{{{table_name}.{field_name}}} = 'approved'", f"{{{table_name}.{field_name}}} IN ('pending', 'approved')"],
            'is_active': [f"{{{table_name}.{field_name}}} = true", f"{{{table_name}.{field_name}}} = false"],
            'created_at': [f"{{{table_name}.{field_name}}} >= '2024-01-01'", f"{{{table_name}.{field_name}}} >= CURRENT_DATE - INTERVAL '30 days'"],
        }
        
        if field_name in field_type_examples:
            examples.extend(field_type_examples[field_name])
        
        logger.info(f"字段 {table_name}.{field_name} 查询完成: {len(values)} 个不同值")
        
        return jsonify({
            'success': True,
            'data': {
                'values': values,
                'counts': counts,
                'examples': examples[:3],  # 最多返回3个示例
                'total_count': len(values),
                'sample_count': sum(counts.values()) if counts else 0
            }
        })
        
    except Exception as e:
        logger.error(f"=== 获取字段值失败: {table_name}.{field_name} ===")
        logger.error(f"错误: {e}", exc_info=True)
        
        return jsonify({
            'success': False,
            'message': f'获取字段值失败: {str(e)}'
        }), 500

# ===== 辅助函数 =====

def get_available_roles():
    """获取所有可配置的角色列表"""
    try:
        logger.info("=== 获取可配置角色列表开始 ===")
        
        # 从用户表获取所有存在的角色
        logger.info("从用户表查询现有角色...")
        existing_roles = db.session.query(User.role).distinct().all()
        existing_roles = [role[0] for role in existing_roles if role[0]]
        logger.info(f"用户表中的角色: {existing_roles}")
        
        # 从role_permissions表获取已配置权限的角色
        logger.info("从权限表查询有绩效管理权限的角色...")
        permission_roles = db.session.query(RolePermission.role).filter_by(
            module='performance_management'
        ).distinct().all()
        permission_roles = [role[0] for role in permission_roles if role[0]]
        logger.info(f"有绩效管理权限的角色: {permission_roles}")
        
        # 合并并去重
        all_roles = list(set(existing_roles + permission_roles))
        logger.info(f"合并后的角色列表: {all_roles}")
        
        # 排除admin角色（admin默认有所有权限）
        all_roles = [role for role in all_roles if role not in ['admin']]
        logger.info(f"排除admin后的角色列表: {all_roles}")
        
        # 如果没有找到任何角色，提供默认角色
        if not all_roles:
            logger.warning("未找到任何可配置角色，使用默认角色列表")
            all_roles = ['sales_director', 'product_manager', 'service_manager', 'channel_manager']
        
        # 构建角色信息
        roles_info = []
        for role in sorted(all_roles):
            try:
                logger.info(f"处理角色: {role}")
                
                # 检查是否已有绩效配置
                from app.models.performance_config import RolePerformanceConfig
                has_config = RolePerformanceConfig.query.filter_by(role=role).first() is not None
                
                # 获取该角色的用户数量
                user_count = User.query.filter_by(role=role).count()
                
                # 获取角色显示名称
                display_name = get_role_display_name_from_dict(role)
                
                role_info = {
                    'role_code': role,
                    'display_name': display_name,
                    'has_config': has_config,
                    'user_count': user_count
                }
                
                roles_info.append(role_info)
                logger.info(f"角色 {role} 信息: {role_info}")
                
            except Exception as role_error:
                logger.error(f"处理角色 {role} 时出错: {role_error}")
                # 继续处理其他角色，不中断整个流程
                continue
        
        logger.info(f"=== 获取到 {len(roles_info)} 个可配置角色 ===")
        return roles_info
        
    except Exception as e:
        logger.error(f"=== 获取可配置角色列表失败 ===")
        logger.error(f"错误类型: {type(e).__name__}")
        logger.error(f"错误消息: {str(e)}")
        logger.error(f"错误堆栈: ", exc_info=True)
        
        # 返回默认角色列表以防止页面完全崩溃
        logger.info("返回默认角色列表作为降级处理")
        return [
            {
                'role_code': 'sales_director',
                'display_name': '销售总监',
                'has_config': False,
                'user_count': 0
            },
            {
                'role_code': 'product_manager', 
                'display_name': '产品经理',
                'has_config': False,
                'user_count': 0
            }
        ]

def get_role_access_scope(role_code):
    """获取角色的默认数据访问范围"""
    # 基于角色返回合适的默认访问范围
    role_scopes = {
        'admin': 'system',
        'ceo': 'system', 
        'sales_director': 'department',
        'service_manager': 'department',
        'channel_manager': 'department',
        'hrdp_manager': 'company',
        'product_manager': 'company',
        'solution_manager': 'company'
    }
    
    return role_scopes.get(role_code, 'personal')

def validate_performance_item(item_data):
    """验证绩效项目数据"""
    required_fields = ['item_name', 'item_code', 'stat_scope']
    
    for field in required_fields:
        if field not in item_data or not item_data[field]:
            logger.warning(f"绩效项目缺少必要字段: {field}")
            return False
    
    # 验证数值字段
    numeric_fields = ['sort_order', 'weight', 'qualification_rate', 'decimal_places']
    for field in numeric_fields:
        if field in item_data and item_data[field] is not None:
            try:
                float(item_data[field])
            except (ValueError, TypeError):
                logger.warning(f"绩效项目字段 {field} 数值格式错误: {item_data[field]}")
                return False
    
    return True

def create_performance_item(role_config, item_data):
    """创建绩效项目对象"""
    return RolePerformanceItem(
        role_config_id=role_config.id,
        metric_id=item_data.get('metric_id'),
        item_name=item_data['item_name'],
        item_code=item_data['item_code'], 
        sort_order=int(item_data.get('sort_order', 0)),
        is_enabled=bool(item_data.get('is_enabled', True)),
        stat_scope=item_data['stat_scope'],
        stat_scope_description=item_data.get('stat_scope_description', ''),
        calculation_method=item_data.get('calculation_method', 'sum'),
        calculation_formula=item_data.get('calculation_formula', ''),
        data_source_config=json.dumps(item_data.get('data_source_config', {})),
        qualification_rate=float(item_data.get('qualification_rate', 80)),
        excellent_threshold=float(item_data['excellent_threshold']) if item_data.get('excellent_threshold') else None,
        good_threshold=float(item_data['good_threshold']) if item_data.get('good_threshold') else None, 
        qualified_threshold=float(item_data['qualified_threshold']) if item_data.get('qualified_threshold') else None,
        display_unit=item_data.get('display_unit', '元'),
        decimal_places=int(item_data.get('decimal_places', 2)),
        color_config=json.dumps(item_data.get('color_config', {})),
        weight=float(item_data.get('weight', 1.0)),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

def save_role_access_config(role_code, access_scope):
    """保存角色数据访问配置"""
    try:
        # 删除现有配置
        RolePerformanceAccess.query.filter_by(role=role_code).delete()
        
        # 创建新配置
        access_config = RolePerformanceAccess(
            role=role_code,
            access_scope=access_scope,
            description=f'{get_role_display_name_from_dict(role_code)}的数据访问权限配置'
        )
        
        db.session.add(access_config)
        
    except Exception as e:
        logger.warning(f"保存访问配置失败 {role_code}: {e}")

def generate_preview_data(role_code, role_config):
    """生成角色配置预览数据"""
    # 这里可以基于配置生成模拟的预览效果
    items = role_config.get('items', [])
    
    preview_items = []
    for item in items:
        preview_item = {
            'item_name': item.get('item_name', ''),
            'stat_scope_display': get_scope_display_name(item.get('stat_scope', '')),
            'calculation_display': get_calculation_display_name(item.get('calculation_method', '')),
            'threshold_display': item.get('qualified_threshold', '未设置'),
            'weight_display': item.get('weight', 1.0),
            'unit_display': item.get('display_unit', '元')
        }
        preview_items.append(preview_item)
    
    return {
        'role_name': get_role_display_name_from_dict(role_code),
        'config_name': role_config.get('config_name', ''),
        'access_scope': get_scope_display_name(role_config.get('access_scope', '')),
        'items_count': len(items),
        'items': preview_items
    }

def get_scope_display_name(scope):
    """获取范围的显示名称"""
    names = {
        'personal': '个人',
        'department': '部门',
        'company': '企业', 
        'system': '系统'
    }
    return names.get(scope, scope)

def get_calculation_display_name(method):
    """获取计算方法的显示名称"""  
    names = {
        'sum': '求和',
        'avg': '平均',
        'count': '计数',
        'max': '最大值',
        'min': '最小值',
        'custom': '自定义公式'
    }
    return names.get(method, method)

def get_category_icon(category):
    """获取类别图标"""
    icons = {
        'sales': 'fas fa-dollar-sign',
        'customer': 'fas fa-users',
        'project': 'fas fa-project-diagram',
        'quality': 'fas fa-medal',
        'service': 'fas fa-headset',
        'business': 'fas fa-briefcase',
        'financial': 'fas fa-chart-pie',
        'team': 'fas fa-user-friends'
    }
    return icons.get(category, 'fas fa-chart-bar')

def get_category_display_name(category):
    """获取类别显示名称"""
    names = {
        'sales': '销售业绩',
        'customer': '客户管理',
        'project': '项目管理',
        'quality': '质量管理',
        'service': '服务质量',
        'business': '业务发展',
        'financial': '财务指标',
        'team': '团队合作'
    }
    return names.get(category, '其他')

def create_performance_item_from_template(role_config, template, data_scopes, sort_order):
    """从预置模板创建绩效项目"""
    # 生成项目代码（基于模板名称和角色）
    item_code = f"{role_config.role}_{template.template_name.replace(' ', '_').lower()}"
    
    # 选择主要数据范围
    primary_scope = data_scopes[0] if data_scopes else 'personal'
    
    # 统计范围描述
    scope_descriptions = {
        'system': '统计系统全部数据',
        'company': '统计企业内所有数据', 
        'department': '统计部门成员数据',
        'personal': '仅统计个人数据'
    }
    
    scope_desc = ', '.join([scope_descriptions.get(scope, scope) for scope in data_scopes])
    
    return RolePerformanceItem(
        role_config_id=role_config.id,
        metric_id=None,  # 暂时不使用基础指标
        item_name=template.template_name,
        item_code=item_code,
        sort_order=sort_order,
        is_enabled=True,
        stat_scope=primary_scope,
        stat_scope_description=scope_desc,
        calculation_method='custom',
        calculation_formula=template.formula_expression,
        data_source_config=json.dumps({
            'template_id': template.id,
            'data_scopes': data_scopes,
            'required_tables': json.loads(template.required_tables) if template.required_tables else [],
            'required_fields': json.loads(template.required_fields) if template.required_fields else []
        }),
        qualification_rate=80.0,  # 默认合格率
        excellent_threshold=None,  # 可以后续配置
        good_threshold=None,
        qualified_threshold=None,
        display_unit=template.result_unit or '元',
        decimal_places=2 if template.result_type == 'numeric' else 0,
        color_config=json.dumps({}),
        weight=1.0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

def create_performance_item_from_template_v2(role_config, template, scope_users, sort_order):
    """从预置模板创建绩效项目 V2 - 支持用户范围配置"""
    # 生成项目代码（基于模板名称和角色）
    item_code = f"{role_config.role}_{template.template_name.replace(' ', '_').lower()}"
    
    # 根据选择的用户范围决定统计范围
    if scope_users:
        primary_scope = 'custom'
        scope_desc = f'自定义范围（包含 {len(scope_users)} 个用户/组织）'
    else:
        primary_scope = 'personal'
        scope_desc = '仅统计个人数据'
    
    return RolePerformanceItem(
        role_config_id=role_config.id,
        metric_id=None,
        item_name=template.template_name,
        item_code=item_code,
        sort_order=sort_order,
        is_enabled=True,
        stat_scope=primary_scope,
        stat_scope_description=scope_desc,
        calculation_method='custom',
        calculation_formula=template.formula_expression,
        data_source_config=json.dumps({
            'template_id': template.id,
            'scope_users': scope_users,  # 保存用户范围配置
            'required_tables': json.loads(template.required_tables) if template.required_tables else [],
            'required_fields': json.loads(template.required_fields) if template.required_fields else []
        }),
        qualification_rate=80.0,
        excellent_threshold=None,
        good_threshold=None,
        qualified_threshold=None,
        display_unit=template.result_unit or '元',
        decimal_places=2 if template.result_type == 'numeric' else 0,
        color_config=json.dumps({}),
        weight=1.0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

def get_simple_users_tree():
    """获取简化版的用户组织架构"""
    try:
        logger.info("使用简化版用户组织架构")
        
        # 查询所有激活用户
        users = User.query.filter_by(is_active=True).all()
        
        # 按部门分组用户
        departments = {}
        for user in users:
            dept = user.department or '未分组'
            if dept not in departments:
                departments[dept] = []
            departments[dept].append(user)
        
        # 构建简化的树状结构
        tree_data = []
        
        # 企业级别
        company_data = {
            'id': 'company_1',
            'name': '企业',
            'type': 'company',
            'children': []
        }
        
        # 添加部门和用户
        for dept_name, dept_users in departments.items():
            dept_data = {
                'id': f'dept_{dept_name}',
                'name': dept_name,
                'type': 'department',
                'children': []
            }
            
            # 添加部门下的用户
            for user in dept_users:
                user_data = {
                    'id': f'user_{user.id}',
                    'name': user.real_name or user.username,
                    'type': 'user',
                    'user_id': user.id
                }
                dept_data['children'].append(user_data)
            
            company_data['children'].append(dept_data)
        
        tree_data.append(company_data)
        
        return jsonify({
            'success': True,
            'data': tree_data
        })
        
    except Exception as e:
        logger.error(f"获取简化用户树失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取用户组织架构失败: {str(e)}'
        }), 500