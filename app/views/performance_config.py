from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from flask_login import login_required, current_user
from flask_babel import get_locale
from datetime import datetime
from app import db
from app.models.user import User
from app.models.role_permissions import RolePermission
from app.models.performance_config import (
    PerformanceMetricsDefinition, RolePerformanceConfig, RolePerformanceItem,
    PerformanceFormulaTemplate, RolePerformanceAccess, ConfigurablePerformanceService,
    RolePerformanceTarget, UserPerformanceTarget, get_user_effective_target
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
@permission_required('config_management', 'view')
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
@permission_required('config_management', 'view')
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
@permission_required('config_management', 'view')
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
@permission_required('config_management', 'edit')
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

@performance_config_bp.route('/api/metrics/active')
@login_required
@permission_required('config_management', 'view')
def api_get_active_metrics():
    """获取已启用的绩效指标列表API（用于下拉选择等场景）"""
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
@permission_required('config_management', 'view')
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
@permission_required('config_management', 'view')
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
@permission_required('config_management', 'view')
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
@permission_required('config_management', 'view')
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
@permission_required('config_management', 'view')
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
@permission_required('config_management', 'view')
def api_get_preset_items():
    """获取预置绩效项目列表API - 从数据库读取"""
    try:
        logger.info("=== API: 获取预置绩效项目列表 ===")

        # 使用新的函数从数据库获取绩效指标
        items_data = get_preset_performance_items()

        logger.info(f"找到 {len(items_data)} 个预置绩效项目")

        # 按类别分组
        grouped_items = {}
        for item in items_data:
            category = item.get('category') or '其他'
            if category not in grouped_items:
                grouped_items[category] = []
            grouped_items[category].append(item)

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


# ============ 绩效指标管理 API ============

@performance_config_bp.route('/api/metrics')
@login_required
@permission_required('config_management', 'view')
def api_get_metrics():
    """获取所有绩效指标（含已禁用的）"""
    try:
        from app.models.performance_config import PerformanceMetricsDefinition

        metrics = PerformanceMetricsDefinition.query.order_by(
            PerformanceMetricsDefinition.metric_category,
            PerformanceMetricsDefinition.metric_code
        ).all()

        return jsonify({
            'success': True,
            'data': [m.to_dict() for m in metrics]
        })

    except Exception as e:
        logger.error(f"获取绩效指标列表失败: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@performance_config_bp.route('/api/metrics', methods=['POST'])
@login_required
@permission_required('config_management', 'edit')
def api_create_metric():
    """创建新的绩效指标"""
    try:
        from app.models.performance_config import PerformanceMetricsDefinition

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400

        # 验证必填字段
        metric_code = data.get('metric_code', '').strip()
        metric_name = data.get('metric_name', '').strip()
        data_type = data.get('data_type', 'amount')

        if not metric_code or not metric_name:
            return jsonify({'success': False, 'message': '指标代码和名称不能为空'}), 400

        # 检查代码是否已存在
        existing = PerformanceMetricsDefinition.query.filter_by(metric_code=metric_code).first()
        if existing:
            return jsonify({'success': False, 'message': f'指标代码 {metric_code} 已存在'}), 400

        # 创建新指标
        metric = PerformanceMetricsDefinition(
            metric_code=metric_code,
            metric_name=metric_name,
            metric_category=data.get('metric_category', '其他'),
            data_type=data_type,
            default_unit=data.get('default_unit'),
            description=data.get('description'),
            available_sources=data.get('available_sources'),
            is_system_metric=False,  # 用户创建的都不是系统指标
            is_active=True
        )

        db.session.add(metric)
        db.session.commit()

        logger.info(f"创建绩效指标: {metric_code}")

        return jsonify({
            'success': True,
            'message': '绩效指标创建成功',
            'data': metric.to_dict()
        })

    except IntegrityError as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': '指标代码已存在'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建绩效指标失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@performance_config_bp.route('/api/metrics/<int:metric_id>', methods=['PUT'])
@login_required
@permission_required('config_management', 'edit')
def api_update_metric(metric_id):
    """更新绩效指标"""
    try:
        from app.models.performance_config import PerformanceMetricsDefinition

        metric = PerformanceMetricsDefinition.query.get(metric_id)
        if not metric:
            return jsonify({'success': False, 'message': '指标不存在'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400

        # 系统指标只能修改部分字段
        if metric.is_system_metric:
            # 系统指标只能修改：名称、描述、分类、是否启用
            if 'metric_name' in data:
                metric.metric_name = data['metric_name']
            if 'description' in data:
                metric.description = data['description']
            if 'metric_category' in data:
                metric.metric_category = data['metric_category']
            if 'is_active' in data:
                metric.is_active = data['is_active']
        else:
            # 用户创建的指标可以修改所有字段
            for field in ['metric_name', 'metric_category', 'data_type', 'default_unit',
                          'description', 'available_sources', 'is_active']:
                if field in data:
                    setattr(metric, field, data[field])

        db.session.commit()

        logger.info(f"更新绩效指标: {metric.metric_code}")

        return jsonify({
            'success': True,
            'message': '绩效指标更新成功',
            'data': metric.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"更新绩效指标失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@performance_config_bp.route('/api/metrics/<int:metric_id>', methods=['DELETE'])
@login_required
@permission_required('config_management', 'edit')
def api_delete_metric(metric_id):
    """删除绩效指标（仅限用户创建的）"""
    try:
        from app.models.performance_config import PerformanceMetricsDefinition

        metric = PerformanceMetricsDefinition.query.get(metric_id)
        if not metric:
            return jsonify({'success': False, 'message': '指标不存在'}), 404

        if metric.is_system_metric:
            return jsonify({'success': False, 'message': '系统指标不能删除，只能禁用'}), 400

        metric_code = metric.metric_code
        db.session.delete(metric)
        db.session.commit()

        logger.info(f"删除绩效指标: {metric_code}")

        return jsonify({
            'success': True,
            'message': '绩效指标已删除'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"删除绩效指标失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@performance_config_bp.route('/api/metrics/data-source-presets')
@login_required
@permission_required('config_management', 'view')
def api_get_data_source_presets():
    """获取可用的数据源预设配置"""
    presets = {
        'PricingOrder': {
            'label': '批价单',
            'default_field': 'pricing_total_amount',
            'default_filter': {'status': 'approved'},
            'default_date_field': 'approved_at',
            'default_aggregate': 'sum',
            'available_fields': [
                {'field': 'pricing_total_amount', 'label': '批价总金额', 'type': 'amount'},
                {'field': 'pricing_total_discount_rate', 'label': '折扣率', 'type': 'percentage'},
            ]
        },
        'Quotation': {
            'label': '报价单',
            'default_field': 'implant_amount',
            'default_filter': {},
            'default_date_field': 'created_at',
            'default_aggregate': 'sum',
            'available_fields': [
                {'field': 'implant_amount', 'label': '植入金额', 'type': 'amount'},
                {'field': 'total_amount', 'label': '报价总金额', 'type': 'amount'},
            ]
        },
        'Project': {
            'label': '项目',
            'default_field': 'id',
            'default_filter': {},
            'default_date_field': 'created_at',
            'default_aggregate': 'count',
            'available_fields': [
                {'field': 'id', 'label': '项目数量', 'type': 'count'},
            ]
        },
        'Company': {
            'label': '客户',
            'default_field': 'id',
            'default_filter': {'company_type': 'customer'},
            'default_date_field': 'created_at',
            'default_aggregate': 'count',
            'available_fields': [
                {'field': 'id', 'label': '客户数量', 'type': 'count'},
            ]
        },
        'manual': {
            'label': '手动录入',
            'description': '不自动采集，需要手动输入实际值',
            'default_aggregate': 'manual'
        }
    }

    return jsonify({
        'success': True,
        'data': presets
    })

@performance_config_bp.route('/api/shareable-users-tree')
@login_required
@permission_required('config_management', 'view')
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
@permission_required('config_management', 'view')
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

# ===== 绩效目标配置 API =====

@performance_config_bp.route('/api/role/<role_code>/targets/<int:year>')
@login_required
@permission_required('config_management', 'view')
def api_get_role_targets(role_code, year):
    """获取角色的年度绩效目标配置"""
    try:
        logger.info(f"=== API: 获取角色目标配置 {role_code}/{year} ===")

        # 获取该角色的所有目标配置
        targets = RolePerformanceTarget.query.filter_by(
            role_code=role_code,
            year=year
        ).all()

        # 获取预置绩效项目（用于返回完整的项目列表）
        preset_items = get_preset_performance_items()

        # 角色写死考核方案:有方案的角色只回方案项(锁定+权重+岗位默认目标兜底)
        from app.services.role_kpi_schemes import get_role_scheme
        scheme = get_role_scheme(role_code)
        scheme_map = {it['item_code']: it for it in scheme} if scheme else {}

        # 构建响应数据
        items_data = []
        for item in preset_items:
            if scheme and item['code'] not in scheme_map:
                continue
            # 查找该项目的目标配置
            target = next((t for t in targets if t.item_code == item['code']), None)

            item_data = {
                'item_code': item['code'],
                'item_name': item['name'],
                'unit': item['unit'],
                'data_type': item['data_type'],
                'scoring_mode': item.get('scoring_mode', 'target'),
                'description': item.get('description', ''),
                'enabled': (target is not None) or bool(scheme),
                'locked': bool(scheme),
                'weight': (float(target.weight) if (target and getattr(target, 'weight', None) is not None)
                           else (scheme_map[item['code']]['weight'] if scheme else None)),
                'annual_target': float(target.annual_target) if target and target.annual_target
                                 else (scheme_map[item['code']].get('default_annual') if scheme else None),
                'enable_quarterly': target.enable_quarterly if target else False,
                'q1_target': float(target.q1_target) if target and target.q1_target else None,
                'q2_target': float(target.q2_target) if target and target.q2_target else None,
                'q3_target': float(target.q3_target) if target and target.q3_target else None,
                'q4_target': float(target.q4_target) if target and target.q4_target else None,
                'enable_monthly': target.enable_monthly if target else False,
                'monthly_targets': target.monthly_targets if target else None
            }
            items_data.append(item_data)

        if scheme:
            _order = {it['item_code']: i for i, it in enumerate(scheme)}
            items_data.sort(key=lambda d: _order.get(d['item_code'], 99))

        logger.info(f"返回 {len(items_data)} 个绩效项目配置")

        return jsonify({
            'success': True,
            'data': {
                'role_code': role_code,
                'year': year,
                'items': items_data
            }
        })

    except Exception as e:
        logger.error(f"获取角色目标配置失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取配置失败: {str(e)}'
        }), 500


@performance_config_bp.route('/api/role/<role_code>/targets/<int:year>', methods=['POST'])
@login_required
@permission_required('config_management', 'edit')
def api_save_role_targets(role_code, year):
    """保存角色的年度绩效目标配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据为空'})

        logger.info(f"=== API: 保存角色目标配置 {role_code}/{year} ===")

        items = data.get('items', [])
        if not items:
            return jsonify({'success': False, 'message': '未提供任何配置项'})

        # 权重校验:启用项的权重合计不得超过 100%
        _w_total = sum(float(it.get('weight') or 0) for it in items if it.get('enabled'))
        if _w_total > 100.0001:
            return jsonify({'success': False,
                            'message': f'权重合计 {round(_w_total, 1)}% 超过 100%,请调整后再保存'}), 400

        # 验证并保存每个项目的目标配置
        saved_count = 0
        validation_errors = []

        for item_data in items:
            if not item_data.get('enabled'):
                # 如果项目未启用，删除可能存在的配置
                RolePerformanceTarget.query.filter_by(
                    role_code=role_code,
                    year=year,
                    item_code=item_data['item_code']
                ).delete()
                continue

            # 验证目标层级
            is_valid, error_msg = validate_target_hierarchy(item_data)
            if not is_valid:
                validation_errors.append(f"{item_data.get('item_name', item_data['item_code'])}: {error_msg}")
                continue

            # 查找或创建目标配置
            target = RolePerformanceTarget.query.filter_by(
                role_code=role_code,
                year=year,
                item_code=item_data['item_code']
            ).first()

            if not target:
                target = RolePerformanceTarget(
                    role_code=role_code,
                    year=year,
                    item_code=item_data['item_code'],
                    created_by=current_user.id
                )
                db.session.add(target)

            # 更新目标值
            target.annual_target = item_data.get('annual_target')
            target.weight = item_data.get('weight')   # 角色级权重覆盖(空=岗位方案默认)
            target.enable_quarterly = item_data.get('enable_quarterly', False)
            target.q1_target = item_data.get('q1_target')
            target.q2_target = item_data.get('q2_target')
            target.q3_target = item_data.get('q3_target')
            target.q4_target = item_data.get('q4_target')
            target.enable_monthly = item_data.get('enable_monthly', False)
            target.monthly_targets = item_data.get('monthly_targets')
            target.target_unit = item_data.get('unit', '万元')
            target.updated_by = current_user.id
            target.updated_at = datetime.utcnow()

            saved_count += 1

        db.session.commit()

        if validation_errors:
            return jsonify({
                'success': True,
                'message': f'保存完成，{saved_count}项成功，{len(validation_errors)}项有验证错误',
                'warnings': validation_errors
            })

        logger.info(f"保存成功: {saved_count} 项")
        return jsonify({
            'success': True,
            'message': f'保存成功，共{saved_count}个配置项'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"保存角色目标配置失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'保存失败: {str(e)}'
        }), 500


@performance_config_bp.route('/api/preset-items-with-units')
@login_required
@permission_required('config_management', 'view')
def api_get_preset_items_with_units():
    """获取预置绩效项目及其单位类型"""
    try:
        items = get_preset_performance_items()
        return jsonify({
            'success': True,
            'data': items
        })
    except Exception as e:
        logger.error(f"获取预置项目失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


def get_performance_unit_config():
    """
    获取绩效单位配置（基于数据库类型，与语言设置解耦）

    货币和单位由数据库类型决定，不随用户语言切换而改变：
    - SP8D/本地 数据库 → CNY (¥), 万元, 除以10000
    - OVS 数据库 → USD ($), M (million), 除以1000000
    """
    from config import Config

    return {
        'currency': Config.DEFAULT_CURRENCY,     # CNY / USD
        'symbol': Config.CURRENCY_SYMBOL,        # ¥ / $
        'amount_unit': Config.AMOUNT_UNIT,       # 万元 / M
        'count_unit': Config.COUNT_UNIT,         # 个 / pcs
        'divisor': Config.AMOUNT_DIVISOR,        # 10000 / 1000000
        'is_ovs': Config.IS_OVS,
        'is_sp8d': Config.IS_SP8D,
        'lang': session.get('language', 'zh')    # 语言设置
    }


def get_default_metrics_definitions():
    """获取默认的绩效指标定义（用于初始化数据库）"""
    return [
        {
            'metric_code': 'sales_target',
            'metric_name': '销售目标',
            'metric_name_en': 'Sales Target',
            'metric_category': '销售业绩',
            'data_type': 'amount',
            'description': '批价单审批通过金额',
            'description_en': 'Approved pricing order amount',
            'is_system_metric': True,
            'available_sources': {
                'model': 'PricingOrder',
                'field': 'pricing_total_amount',
                'aggregate': 'sum',
                'filter': {'status': 'approved', 'created_by': '{user_id}'},
                'date_field': 'approved_at'
            }
        },
        {
            'metric_code': 'implant_amount',
            'metric_name': '植入额',
            'metric_name_en': 'Implant',
            'metric_category': '销售业绩',
            'data_type': 'amount',
            'description': '报价单植入金额',
            'description_en': 'Quotation implant amount',
            'is_system_metric': True,
            'available_sources': {
                'model': 'Quotation',
                'field': 'implant_amount',
                'aggregate': 'sum',
                'filter': {'owner_id': '{user_id}'},
                'date_field': 'created_at'
            }
        },
        {
            'metric_code': 'new_customers',
            'metric_name': '新增客户',
            'metric_name_en': 'New Customers',
            'metric_category': '客户管理',
            'data_type': 'count',
            'description': '新建客户数量',
            'description_en': 'New customers count',
            'is_system_metric': True,
            'available_sources': {
                'model': 'Company',
                'field': 'id',
                'aggregate': 'count',
                'filter': {'company_type': 'customer', 'owner_id': '{user_id}'},
                'date_field': 'created_at'
            }
        },
        {
            'metric_code': 'new_projects',
            'metric_name': '新增项目',
            'metric_name_en': 'New Projects',
            'metric_category': '项目管理',
            'data_type': 'count',
            'description': '新建项目数量',
            'description_en': 'New projects count',
            'is_system_metric': True,
            'available_sources': {
                'model': 'Project',
                'field': 'id',
                'aggregate': 'count',
                'filter': {'owner_id': '{user_id}'},
                'date_field': 'created_at'
            }
        },
        {
            'metric_code': 'high_price_amount',
            'metric_name': '高批价金额',
            'metric_name_en': 'High Price Amount',
            'metric_category': '销售业绩',
            'data_type': 'amount',
            'description': '折扣率≥85%的批价单金额',
            'description_en': 'High discount (≥85%) pricing amount',
            'is_system_metric': True,
            'available_sources': {
                'model': 'PricingOrder',
                'field': 'pricing_total_amount',
                'aggregate': 'sum',
                'filter': {'status': 'approved', 'created_by': '{user_id}', 'pricing_total_discount_rate__gte': 0.85},
                'date_field': 'approved_at'
            }
        },
        {
            'metric_code': 'quotation_count',
            'metric_name': '报价单数量',
            'metric_name_en': 'Quotation Count',
            'metric_category': '销售业绩',
            'data_type': 'count',
            'description': '提交的报价单数量',
            'description_en': 'Submitted quotations count',
            'is_system_metric': True,
            'available_sources': {
                'model': 'Quotation',
                'field': 'id',
                'aggregate': 'count',
                'filter': {'owner_id': '{user_id}'},
                'date_field': 'created_at'
            }
        },
        {
            'metric_code': 'customer_activity_rate',
            'metric_name': '客户活跃度',
            'metric_name_en': 'Customer Activity Rate',
            'metric_category': '客户管理',
            'data_type': 'percentage',
            'description': '活跃和高度活跃客户占总客户的比例',
            'description_en': 'Percentage of active and highly active customers',
            'is_system_metric': True,
            'available_sources': {
                'model': 'Company',
                'field': 'activity_status',
                'aggregate': 'custom',
                'formula': '(highly_active + active) / total * 100'
            }
        },
        {
            'metric_code': 'pm_implant_amount',
            'metric_name': '产品植入额',
            'metric_name_en': 'Product Implant Amount',
            'metric_category': '产品管理',
            'data_type': 'amount',
            'description': '产品经理名下产品的报价单植入金额（仅厂商产品）',
            'description_en': 'Quotation implant amount for products owned by product manager (vendor products only)',
            'is_system_metric': True,
            'available_sources': {
                'model': 'QuotationDetail',
                'field': 'quantity * market_price',
                'aggregate': 'sum',
                'filter': {'product.owner_id': '{user_id}', 'product.is_vendor_product': True},
                'date_field': 'quotation.created_at'
            }
        },
        {
            'metric_code': 'pm_sales_amount',
            'metric_name': '产品批价额',
            'metric_name_en': 'Product Pricing Amount',
            'metric_category': '产品管理',
            'data_type': 'amount',
            'description': '产品经理名下产品的已审批批价单金额（仅厂商产品）',
            'description_en': 'Approved pricing order amount for products owned by product manager (vendor products only)',
            'is_system_metric': True,
            'available_sources': {
                'model': 'PricingOrderDetail',
                'field': 'total_price',
                'aggregate': 'sum',
                'filter': {'product.owner_id': '{user_id}', 'pricing_order.status': 'approved'},
                'date_field': 'pricing_order.approved_at'
            }
        },
        {
            'metric_code': 'se_implant_amount',
            'metric_name': '方案植入额',
            'metric_name_en': 'Solution Implant Amount',
            'metric_category': '技术支持',
            'data_type': 'amount',
            'description': '解决方案经理支持项目的报价单植入金额',
            'description_en': 'Quotation implant amount for supported projects',
            'is_system_metric': True,
            'available_sources': {
                'model': 'QuotationDetail',
                'field': 'quantity * market_price',
                'aggregate': 'sum',
                'filter': {'project_member.role': 'solution_engineer'},
                'date_field': 'quotation.created_at'
            }
        },
        {
            'metric_code': 'se_sales_amount',
            'metric_name': '方案批价额',
            'metric_name_en': 'Solution Pricing Amount',
            'metric_category': '技术支持',
            'data_type': 'amount',
            'description': '解决方案经理支持项目的已审批批价单金额',
            'description_en': 'Approved pricing order amount for supported projects',
            'is_system_metric': True,
            'available_sources': {
                'model': 'PricingOrder',
                'field': 'pricing_total_amount',
                'aggregate': 'sum',
                'filter': {'project_member.role': 'solution_engineer', 'status': 'approved'},
                'date_field': 'approved_at'
            }
        }
    ]


def initialize_default_metrics():
    """初始化默认的绩效指标到数据库"""
    from app.models.performance_config import PerformanceMetricsDefinition

    defaults = get_default_metrics_definitions()
    created_count = 0

    for item in defaults:
        existing = PerformanceMetricsDefinition.query.filter_by(
            metric_code=item['metric_code']
        ).first()

        if not existing:
            metric = PerformanceMetricsDefinition(
                metric_code=item['metric_code'],
                metric_name=item['metric_name'],
                metric_category=item['metric_category'],
                data_type=item['data_type'],
                description=item['description'],
                available_sources=item['available_sources'],
                is_system_metric=item['is_system_metric'],
                is_active=True
            )
            db.session.add(metric)
            created_count += 1

    if created_count > 0:
        db.session.commit()
        logger.info(f"初始化了 {created_count} 个默认绩效指标")

    return PerformanceMetricsDefinition.query.filter_by(is_active=True).all()


def get_preset_performance_items():
    """获取绩效项目列表（从数据库读取，支持动态配置）"""
    from app.models.performance_config import PerformanceMetricsDefinition
    from app.helpers.scoring_modes import default_scoring_mode as _sm_default

    unit_config = get_performance_unit_config()
    amount_unit = unit_config['amount_unit']
    count_unit = unit_config['count_unit']
    lang = unit_config['lang']
    # 金额单位带货币符号,明确币种+量级: CN ¥万 / SG $M(去掉 CNY 的"元"冗余)
    _sym = unit_config['symbol']
    _mag = '万' if unit_config['currency'] == 'CNY' else amount_unit
    amount_unit_disp = f"{_sym}{_mag}"

    # 从数据库获取所有激活的绩效指标
    metrics = PerformanceMetricsDefinition.query.filter_by(is_active=True).all()

    # 如果数据库为空，初始化默认数据
    if not metrics:
        try:
            metrics = initialize_default_metrics()
        except Exception as e:
            logger.warning(f"初始化默认指标失败: {e}，使用硬编码备用")
            # 回退到硬编码（兼容性保障）
            return _get_hardcoded_preset_items(unit_config, lang)

    # 图标映射
    icon_map = {
        'sales_target': 'trending_up',
        'implant_amount': 'download',
        'new_customers': 'person_add',
        'new_projects': 'folder_open',
        'high_price_amount': 'price_check',
        'quotation_count': 'description',
        'customer_activity_rate': 'person_check',
        'pm_implant_amount': 'inventory_2',
        'pm_sales_amount': 'sell',
        'se_implant_amount': 'engineering',
        'se_sales_amount': 'handshake',
        'se_confirm_count': 'task_alt',
        'se_sales_support': 'group',
        'se_confirm_quality': 'verified',
    }

    # 分类图标映射
    category_icon_map = {
        '销售业绩': 'trending_up',
        '客户管理': 'people',
        '项目管理': 'folder_open',
        '质量管理': 'verified',
        '产品管理': 'inventory_2',
        '技术支持': 'engineering',
        'default': 'assessment'
    }

    result = []
    for m in metrics:
        # 根据数据类型选择单位
        if m.data_type == 'amount':
            unit = amount_unit_disp   # 带货币符号(¥万 / $M)
        elif m.data_type == 'count':
            unit = count_unit
        elif m.data_type == 'percentage':
            unit = '%'
        else:
            unit = m.default_unit or ''

        # 获取图标
        icon = icon_map.get(m.metric_code, category_icon_map.get(m.metric_category, 'assessment'))

        from app.helpers.metric_i18n import metric_label, metric_desc
        result.append({
            'id': m.id,
            'code': m.metric_code,
            'name': metric_label(m.metric_code, m.metric_name),
            'unit': unit,
            'data_type': m.data_type,
            'scoring_mode': (m.scoring_mode or _sm_default(m.metric_code)),
            'description': metric_desc(m.metric_code, m.description or ''),
            'icon': icon,
            'category': m.metric_category or '其他',
            'is_system_metric': m.is_system_metric,
            'data_source_config': m.available_sources,
            'result_unit': unit
        })

    return result


def _get_hardcoded_preset_items(unit_config, lang):
    """硬编码的备用绩效项目（用于数据库不可用时）"""
    amount_unit = unit_config['amount_unit']
    count_unit = unit_config['count_unit']

    names = {
        'zh': {
            'sales_target': '销售目标',
            'implant_amount': '植入额',
            'new_customers': '新增客户',
            'new_projects': '新增项目',
            'high_price_amount': '高批价金额',
            'quotation_count': '报价单数量',
            'customer_activity_rate': '客户活跃度'
        },
        'en': {
            'sales_target': 'Sales Target',
            'implant_amount': 'Implant',
            'new_customers': 'New Customers',
            'new_projects': 'New Projects',
            'high_price_amount': 'High Price Amount',
            'quotation_count': 'Quotation Count',
            'customer_activity_rate': 'Customer Activity Rate'
        }
    }

    descriptions = {
        'zh': {
            'sales_target': '批价单审批通过金额',
            'implant_amount': '报价单植入金额',
            'new_customers': '新建客户数量',
            'new_projects': '新建项目数量',
            'high_price_amount': '折扣率≥85%的批价单金额',
            'quotation_count': '提交的报价单数量',
            'customer_activity_rate': '活跃和高度活跃客户占总客户的比例'
        },
        'en': {
            'sales_target': 'Approved pricing order amount',
            'implant_amount': 'Quotation implant amount',
            'new_customers': 'New customers count',
            'new_projects': 'New projects count',
            'high_price_amount': 'High discount (≥85%) pricing amount',
            'quotation_count': 'Submitted quotations count',
            'customer_activity_rate': 'Percentage of active and highly active customers'
        }
    }

    name_dict = names.get(lang, names['zh'])
    desc_dict = descriptions.get(lang, descriptions['zh'])

    return [
        {'id': 1, 'code': 'sales_target', 'name': name_dict['sales_target'], 'unit': amount_unit,
         'data_type': 'amount', 'description': desc_dict['sales_target'], 'icon': 'trending_up',
         'category': '销售业绩', 'is_system_metric': True, 'result_unit': amount_unit},
        {'id': 2, 'code': 'implant_amount', 'name': name_dict['implant_amount'], 'unit': amount_unit,
         'data_type': 'amount', 'description': desc_dict['implant_amount'], 'icon': 'download',
         'category': '销售业绩', 'is_system_metric': True, 'result_unit': amount_unit},
        {'id': 3, 'code': 'new_customers', 'name': name_dict['new_customers'], 'unit': count_unit,
         'data_type': 'count', 'description': desc_dict['new_customers'], 'icon': 'person_add',
         'category': '客户管理', 'is_system_metric': True, 'result_unit': count_unit},
        {'id': 4, 'code': 'new_projects', 'name': name_dict['new_projects'], 'unit': count_unit,
         'data_type': 'count', 'description': desc_dict['new_projects'], 'icon': 'folder_open',
         'category': '项目管理', 'is_system_metric': True, 'result_unit': count_unit},
        {'id': 5, 'code': 'high_price_amount', 'name': name_dict['high_price_amount'], 'unit': amount_unit,
         'data_type': 'amount', 'description': desc_dict['high_price_amount'], 'icon': 'price_check',
         'category': '销售业绩', 'is_system_metric': True, 'result_unit': amount_unit},
        {'id': 6, 'code': 'quotation_count', 'name': name_dict['quotation_count'], 'unit': count_unit,
         'data_type': 'count', 'description': desc_dict['quotation_count'], 'icon': 'description',
         'category': '销售业绩', 'is_system_metric': True, 'result_unit': count_unit},
        {'id': 7, 'code': 'customer_activity_rate', 'name': name_dict['customer_activity_rate'], 'unit': '%',
         'data_type': 'percentage', 'description': desc_dict['customer_activity_rate'], 'icon': 'person_check',
         'category': '客户管理', 'is_system_metric': True, 'result_unit': '%'}
    ]


@performance_config_bp.route('/api/role/<role_code>/available-years')
@login_required
def api_get_role_available_years(role_code):
    """获取角色有绩效目标数据的年份列表"""
    try:
        logger.info(f"=== API: 获取角色可用年份 role_code={role_code} ===")

        from datetime import datetime
        current_year = datetime.now().year

        # 查询该角色已有数据的年份
        existing_years = db.session.query(RolePerformanceTarget.year).filter_by(
            role_code=role_code
        ).distinct().all()
        existing_years = sorted([y[0] for y in existing_years if y[0]])

        # 构建可用年份列表：当前年 + 次年 + 有数据的历史年份
        available_years = set()
        available_years.add(current_year)      # 当前年始终可选
        available_years.add(current_year + 1)  # 次年始终可选

        # 添加有数据的历史年份
        for year in existing_years:
            available_years.add(year)

        # 排序（降序，最新年份在前）
        years_list = sorted(list(available_years), reverse=True)

        logger.info(f"角色 {role_code} 可用年份: {years_list}")

        return jsonify({
            'success': True,
            'data': {
                'role_code': role_code,
                'years': years_list,
                'current_year': current_year
            }
        })

    except Exception as e:
        logger.error(f"获取角色可用年份失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取可用年份失败: {str(e)}'
        }), 500


def validate_target_hierarchy(item_data):
    """
    验证目标层级：
    - 季度合计 ≤ 年度
    - 月度合计 ≤ 季度
    比率类(%)指标:各期为「水平目标」(每期独立,不累加,如每季 4% 失败率),
    不做合计校验,否则会被误判超额而跳过保存(失败率/客户活跃度/项目活跃度等)。
    """
    if (item_data.get('unit') or '') == '%':
        return True, None

    annual = float(item_data.get('annual_target') or 0)

    if item_data.get('enable_quarterly'):
        q_total = sum([
            float(item_data.get('q1_target') or 0),
            float(item_data.get('q2_target') or 0),
            float(item_data.get('q3_target') or 0),
            float(item_data.get('q4_target') or 0)
        ])
        if annual > 0 and q_total > annual:
            return False, f'季度合计({q_total})不能超过年度目标({annual})'

    if item_data.get('enable_monthly') and item_data.get('monthly_targets'):
        monthly = item_data.get('monthly_targets', {})
        for q in range(1, 5):
            q_target = float(item_data.get(f'q{q}_target') or 0)
            if q_target == 0:
                continue

            # 获取该季度对应的月份
            months = {
                1: ['1', '2', '3'],
                2: ['4', '5', '6'],
                3: ['7', '8', '9'],
                4: ['10', '11', '12']
            }
            m_total = sum([float(monthly.get(m, 0) or 0) for m in months[q]])
            if m_total > q_target:
                return False, f'Q{q}月度合计({m_total})不能超过季度目标({q_target})'

    return True, None


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
        logger.info("从权限表查询有配置管理权限的角色...")
        permission_roles = db.session.query(RolePermission.role).filter_by(
            module='config_management'
        ).distinct().all()
        permission_roles = [role[0] for role in permission_roles if role[0]]
        logger.info(f"有配置管理权限的角色: {permission_roles}")
        
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

# ===== 用户绩效目标覆盖 API =====

@performance_config_bp.route('/api/user/<int:user_id>/targets/<int:year>')
@login_required
def api_get_user_targets(user_id, year):
    """获取用户的年度绩效目标配置（包含角色默认值和个人覆盖）"""
    try:
        if not _can_read_person_perf(user_id, year):
            return jsonify({'success': False, 'message': '无权限'}), 403
        logger.info(f"=== API: 获取用户目标配置 user_id={user_id}, year={year} ===")

        # 获取用户信息
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404

        # 权限检查：只能查看自己的或有权限的用户
        if current_user.id != user_id and current_user.role not in ['admin', 'ceo', 'hr_manager', 'hrdp_manager']:
            # 检查是否是直属上级
            from app.models.affiliation import Affiliation
            is_supervisor = Affiliation.query.filter_by(
                subordinate_id=user_id,
                supervisor_id=current_user.id,
                is_active=True
            ).first() is not None
            if not is_supervisor:
                return jsonify({'success': False, 'message': '无权限查看该用户的绩效目标'}), 403

        # 获取角色默认目标
        role_targets = RolePerformanceTarget.query.filter_by(
            role_code=user.role,
            year=year
        ).all()
        role_targets_dict = {t.item_code: t for t in role_targets}

        # 获取用户个人覆盖
        user_targets = UserPerformanceTarget.query.filter_by(
            user_id=user_id,
            year=year
        ).all()
        user_targets_dict = {t.item_code: t for t in user_targets}

        # 获取预置绩效项目
        preset_items = get_preset_performance_items()

        # 构建响应数据
        items_data = []
        for item in preset_items:
            item_code = item['code']
            role_target = role_targets_dict.get(item_code)
            user_target = user_targets_dict.get(item_code)

            # 确定有效值（个人覆盖 > 角色默认）
            def get_effective_value(field_name, override_field_name=None):
                override_field = override_field_name or f'{field_name}_override'
                if user_target:
                    override_val = getattr(user_target, override_field, None)
                    if override_val is not None:
                        return float(override_val) if isinstance(override_val, (int, float)) or (hasattr(override_val, '__float__')) else override_val
                if role_target:
                    role_val = getattr(role_target, field_name, None)
                    if role_val is not None:
                        return float(role_val) if isinstance(role_val, (int, float)) or (hasattr(role_val, '__float__')) else role_val
                return None

            item_data = {
                'item_code': item_code,
                'item_name': item['name'],
                'unit': item['unit'],
                'data_type': item['data_type'],
                'has_role_default': role_target is not None,
                # 角色默认值
                'role_annual_target': float(role_target.annual_target) if role_target and role_target.annual_target else None,
                'role_enable_quarterly': role_target.enable_quarterly if role_target else False,
                'role_q1_target': float(role_target.q1_target) if role_target and role_target.q1_target else None,
                'role_q2_target': float(role_target.q2_target) if role_target and role_target.q2_target else None,
                'role_q3_target': float(role_target.q3_target) if role_target and role_target.q3_target else None,
                'role_q4_target': float(role_target.q4_target) if role_target and role_target.q4_target else None,
                'role_enable_monthly': role_target.enable_monthly if role_target else False,
                'role_monthly_targets': role_target.monthly_targets if role_target else None,
                # 个人覆盖值
                'has_override': user_target is not None,
                'annual_target_override': float(user_target.annual_target_override) if user_target and user_target.annual_target_override else None,
                'enable_quarterly_override': user_target.enable_quarterly_override if user_target else None,
                'q1_target_override': float(user_target.q1_target_override) if user_target and user_target.q1_target_override else None,
                'q2_target_override': float(user_target.q2_target_override) if user_target and user_target.q2_target_override else None,
                'q3_target_override': float(user_target.q3_target_override) if user_target and user_target.q3_target_override else None,
                'q4_target_override': float(user_target.q4_target_override) if user_target and user_target.q4_target_override else None,
                'enable_monthly_override': user_target.enable_monthly_override if user_target else None,
                'monthly_targets_override': user_target.monthly_targets_override if user_target else None,
                # 有效值（合并后）
                'effective_annual_target': get_effective_value('annual_target'),
                'effective_enable_quarterly': user_target.enable_quarterly_override if user_target and user_target.enable_quarterly_override is not None else (role_target.enable_quarterly if role_target else False),
                'effective_q1_target': get_effective_value('q1_target'),
                'effective_q2_target': get_effective_value('q2_target'),
                'effective_q3_target': get_effective_value('q3_target'),
                'effective_q4_target': get_effective_value('q4_target'),
            }
            items_data.append(item_data)

        logger.info(f"返回 {len(items_data)} 个绩效项目配置")

        return jsonify({
            'success': True,
            'data': {
                'user_id': user_id,
                'user_name': user.real_name or user.username,
                'role_code': user.role,
                'year': year,
                'items': items_data
            }
        })

    except Exception as e:
        logger.error(f"获取用户目标配置失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取配置失败: {str(e)}'
        }), 500


@performance_config_bp.route('/api/user/<int:user_id>/targets/<int:year>', methods=['POST'])
@login_required
def api_save_user_targets(user_id, year):
    """保存用户的年度绩效目标覆盖配置"""
    try:
        if not can_access_person_tab(user_id, 'pc_performance', need_edit=True):
            return jsonify({'success': False, 'message': '无权限'}), 403
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据为空'})

        logger.info(f"=== API: 保存用户目标配置 user_id={user_id}, year={year} ===")

        # 获取用户信息
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404

        # 权限检查：只能编辑自己的或有权限的用户
        if current_user.id != user_id and current_user.role not in ['admin', 'ceo', 'hr_manager', 'hrdp_manager']:
            from app.models.affiliation import Affiliation
            is_supervisor = Affiliation.query.filter_by(
                subordinate_id=user_id,
                supervisor_id=current_user.id,
                is_active=True
            ).first() is not None
            if not is_supervisor:
                return jsonify({'success': False, 'message': '无权限修改该用户的绩效目标'}), 403

        items = data.get('items', [])
        saved_count = 0

        for item_data in items:
            item_code = item_data.get('item_code')
            if not item_code:
                continue

            # 检查是否有任何覆盖值
            has_any_override = any([
                item_data.get('annual_target_override') is not None,
                item_data.get('enable_quarterly_override') is not None,
                item_data.get('q1_target_override') is not None,
                item_data.get('q2_target_override') is not None,
                item_data.get('q3_target_override') is not None,
                item_data.get('q4_target_override') is not None,
                item_data.get('enable_monthly_override') is not None,
                item_data.get('monthly_targets_override') is not None
            ])

            if not has_any_override:
                # 没有覆盖值，删除现有记录
                UserPerformanceTarget.query.filter_by(
                    user_id=user_id,
                    year=year,
                    item_code=item_code
                ).delete()
                continue

            # 查找或创建目标配置
            target = UserPerformanceTarget.query.filter_by(
                user_id=user_id,
                year=year,
                item_code=item_code
            ).first()

            if not target:
                target = UserPerformanceTarget(
                    user_id=user_id,
                    year=year,
                    item_code=item_code,
                    created_by=current_user.id
                )
                db.session.add(target)

            # 更新覆盖值
            target.annual_target_override = item_data.get('annual_target_override')
            target.enable_quarterly_override = item_data.get('enable_quarterly_override')
            target.q1_target_override = item_data.get('q1_target_override')
            target.q2_target_override = item_data.get('q2_target_override')
            target.q3_target_override = item_data.get('q3_target_override')
            target.q4_target_override = item_data.get('q4_target_override')
            target.enable_monthly_override = item_data.get('enable_monthly_override')
            target.monthly_targets_override = item_data.get('monthly_targets_override')
            target.updated_by = current_user.id
            target.updated_at = datetime.utcnow()

            saved_count += 1

        db.session.commit()

        logger.info(f"保存成功: {saved_count} 项")
        return jsonify({
            'success': True,
            'message': f'保存成功，共{saved_count}个覆盖配置'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"保存用户目标配置失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'保存失败: {str(e)}'
        }), 500


@performance_config_bp.route('/api/user/<int:user_id>/targets/<int:year>/clear', methods=['POST'])
@login_required
def api_clear_user_targets(user_id, year):
    """清除用户的所有个人覆盖配置，恢复使用角色默认值"""
    try:
        if not can_access_person_tab(user_id, 'pc_performance', need_edit=True):
            return jsonify({'success': False, 'message': '无权限'}), 403
        logger.info(f"=== API: 清除用户目标覆盖 user_id={user_id}, year={year} ===")

        # 获取用户信息
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404

        # 权限检查
        if current_user.id != user_id and current_user.role not in ['admin', 'ceo', 'hr_manager', 'hrdp_manager']:
            from app.models.affiliation import Affiliation
            is_supervisor = Affiliation.query.filter_by(
                subordinate_id=user_id,
                supervisor_id=current_user.id,
                is_active=True
            ).first() is not None
            if not is_supervisor:
                return jsonify({'success': False, 'message': '无权限修改该用户的绩效目标'}), 403

        # 企业隔离:非 admin 只能操作本公司用户
        if current_user.role != 'admin' and (user.company_name or '') != (current_user.company_name or ''):
            return jsonify({'success': False, 'message': '无权操作其他公司用户的目标'}), 403

        # 删除所有个人覆盖
        deleted_count = UserPerformanceTarget.query.filter_by(
            user_id=user_id,
            year=year
        ).delete()

        db.session.commit()

        logger.info(f"清除成功: 删除 {deleted_count} 条覆盖记录")
        return jsonify({
            'success': True,
            'message': f'已清除所有个人覆盖配置，将使用角色默认值'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"清除用户目标覆盖失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'清除失败: {str(e)}'
        }), 500


@performance_config_bp.route('/api/users/targets/batch', methods=['POST'])
@login_required
def api_batch_user_targets():
    """批量获取或保存多个用户的绩效目标配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据为空'})

        user_ids = data.get('user_ids', [])
        year = data.get('year', datetime.now().year)
        items = data.get('items')  # 如果有 items，则是保存操作

        if not user_ids:
            return jsonify({'success': False, 'message': '未提供用户ID列表'})

        logger.info(f"=== API: 批量用户目标配置 user_ids={user_ids}, year={year}, is_save={items is not None} ===")

        if items is not None:
            # ===== 保存操作需要edit权限 =====
            if not current_user.has_permission('config_management', 'edit'):
                return jsonify({'success': False, 'message': '没有编辑权限'}), 403
            # 防自评:非 admin 不能编辑自己的绩效目标(录入人须 ≠ 被考核人,由上级录入)
            if current_user.role != 'admin' and current_user.id in user_ids:
                return jsonify({'success': False, 'message': '不能编辑自己的绩效目标,请由上级录入'}), 403
            # 企业隔离:非 admin 只能写本公司用户
            if current_user.role != 'admin':
                my_company = current_user.company_name or ''
                others = User.query.filter(User.id.in_(user_ids),
                                           User.company_name != my_company).count()
                if others:
                    return jsonify({'success': False, 'message': '无权配置其他公司用户的目标'}), 403
            # HRBP 隔离:hr_manager 只能配自己负责部门的人
            from app.helpers.hrbp_helpers import is_hrbp, hrbp_scope_user_ids
            if is_hrbp(current_user):
                scope = hrbp_scope_user_ids(current_user)
                if any(uid not in scope for uid in user_ids):
                    return jsonify({'success': False, 'message': '只能配置你负责部门的成员绩效'}), 403
            return _batch_save_user_targets(user_ids, year, items)
        else:
            # ===== 获取操作:需 config/user view 权限,或为该人绩效结算审批人(只读单人) =====
            from app.helpers.hrbp_helpers import is_hrbp as _is_hrbp, hrbp_scope_user_ids as _hrbp_ids
            if _is_hrbp(current_user):
                scope = _hrbp_ids(current_user)
                if any(uid not in scope for uid in user_ids):
                    return jsonify({'success': False, 'message': '只能查看你负责部门的成员绩效'}), 403
                return _batch_get_user_targets(user_ids, year)
            # 非 HRBP:逐人按数据范围校验(_can_read_person_perf 已含 person_config /
            # config_management / user_management 各自 scope 的兜底,personal 不能越权看他人)
            if any(not _can_read_person_perf(uid, year) for uid in user_ids):
                return jsonify({'success': False, 'message': '无权限'}), 403
            return _batch_get_user_targets(user_ids, year)

    except Exception as e:
        logger.error(f"批量用户目标配置操作失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'操作失败: {str(e)}'
        }), 500


def _batch_get_user_targets(user_ids, year):
    """批量获取用户绩效目标（内部函数）"""
    # 获取这些用户的信息
    users = User.query.filter(User.id.in_(user_ids)).all()
    user_dict = {u.id: u for u in users}

    if not users:
        return jsonify({'success': False, 'message': '未找到指定的用户'})

    # 收集所有角色
    roles = list(set(u.role for u in users if u.role))

    # 获取所有相关角色的默认目标
    role_targets_all = RolePerformanceTarget.query.filter(
        RolePerformanceTarget.role_code.in_(roles),
        RolePerformanceTarget.year == year
    ).all()
    role_targets_by_role = {}
    for t in role_targets_all:
        if t.role_code not in role_targets_by_role:
            role_targets_by_role[t.role_code] = {}
        role_targets_by_role[t.role_code][t.item_code] = t

    # 获取所有用户的覆盖
    user_targets_all = UserPerformanceTarget.query.filter(
        UserPerformanceTarget.user_id.in_(user_ids),
        UserPerformanceTarget.year == year
    ).all()
    user_targets_by_user = {}
    for t in user_targets_all:
        if t.user_id not in user_targets_by_user:
            user_targets_by_user[t.user_id] = {}
        user_targets_by_user[t.user_id][t.item_code] = t

    # 获取预置绩效项目
    preset_items = get_preset_performance_items()

    # 角色写死考核方案:所有目标用户同角色且该角色有方案时,
    # 项目由方案决定(锁定勾选、带权重、目标可用岗位默认值),不再自由勾选
    from app.services.role_kpi_schemes import get_role_scheme
    scheme = None
    user_roles = {u.role for u in users if u}
    if len(user_roles) == 1:
        scheme = get_role_scheme(next(iter(user_roles)))
    scheme_map = {it['item_code']: it for it in scheme} if scheme else {}

    # 确定共同的有效配置（如果多用户有不同值，显示为 None）
    items_data = []
    for item in preset_items:
        item_code = item['code']
        if scheme and item_code not in scheme_map:
            continue  # 方案角色只显示方案内项目

        # 收集所有用户对该项目的有效值
        annual_targets = []
        enabled_states = []
        quarterly_enabled_states = []
        q1_targets, q2_targets, q3_targets, q4_targets = [], [], [], []
        monthly_enabled_states, monthly_dicts = [], []

        for user_id in user_ids:
            user = user_dict.get(user_id)
            if not user:
                continue

            role_targets = role_targets_by_role.get(user.role, {})
            role_target = role_targets.get(item_code)
            user_target = user_targets_by_user.get(user_id, {}).get(item_code)

            # 计算有效值
            effective_annual = None
            effective_enabled = False
            effective_quarterly = False
            effective_q1, effective_q2, effective_q3, effective_q4 = None, None, None, None

            if user_target and user_target.annual_target_override is not None:
                effective_annual = float(user_target.annual_target_override)
            elif role_target and role_target.annual_target is not None:
                effective_annual = float(role_target.annual_target)

            if role_target:
                effective_enabled = True
            if user_target:
                effective_enabled = True

            if user_target and user_target.enable_quarterly_override is not None:
                effective_quarterly = user_target.enable_quarterly_override
            elif role_target:
                effective_quarterly = role_target.enable_quarterly

            # 季度目标
            for q, q_list in [(1, q1_targets), (2, q2_targets), (3, q3_targets), (4, q4_targets)]:
                override_val = getattr(user_target, f'q{q}_target_override', None) if user_target else None
                role_val = getattr(role_target, f'q{q}_target', None) if role_target else None
                if override_val is not None:
                    q_list.append(float(override_val))
                elif role_val is not None:
                    q_list.append(float(role_val))

            annual_targets.append(effective_annual)
            enabled_states.append(effective_enabled)
            quarterly_enabled_states.append(effective_quarterly)

            # 月度(个人覆盖 > 角色默认)
            if user_target and user_target.enable_monthly_override is not None:
                monthly_enabled_states.append(bool(user_target.enable_monthly_override))
                monthly_dicts.append(user_target.monthly_targets_override or {})
            elif role_target:
                monthly_enabled_states.append(bool(getattr(role_target, 'enable_monthly', False)))
                monthly_dicts.append(getattr(role_target, 'monthly_targets', None) or {})
            else:
                monthly_enabled_states.append(False)
                monthly_dicts.append({})

        # 判断值是否一致
        def get_common_value(values):
            unique = set(v for v in values if v is not None)
            if len(unique) == 1:
                return list(unique)[0]
            return None  # 不一致或全为空

        item_data = {
            'item_code': item_code,
            'item_name': item['name'],
            'unit': item['unit'],
            'data_type': item['data_type'],
            'scoring_mode': item.get('scoring_mode', 'target'),
            'description': item.get('description', ''),
            'enabled': any(enabled_states),
            'annual_target': get_common_value(annual_targets),
            'enable_quarterly': any(quarterly_enabled_states),
            'q1_target': get_common_value(q1_targets),
            'q2_target': get_common_value(q2_targets),
            'q3_target': get_common_value(q3_targets),
            'q4_target': get_common_value(q4_targets),
            # 月度:单用户返回真实有效值;多用户(批量)不回传以免误覆盖
            'enable_monthly': any(monthly_enabled_states) if len(user_ids) == 1 else False,
            'monthly_targets': (monthly_dicts[0] if (len(user_ids) == 1 and monthly_dicts) else None),
            # 来源标记(单用户):该行是否存在个人覆盖(user_performance_targets 有行)
            'overridden': (len(user_ids) == 1 and
                           bool(user_targets_by_user.get(user_ids[0], {}).get(item_code))),
            # 标记值是否一致
            'values_consistent': len(set(v for v in annual_targets if v is not None)) <= 1
        }
        if scheme:
            sc = scheme_map[item_code]
            item_data['enabled'] = True          # 方案项强制考核
            item_data['locked'] = True           # 前端锁定勾选框
            item_data['weight'] = sc['weight']   # 考核权重(%):默认方案权重
            if item_data['annual_target'] is None:
                item_data['annual_target'] = sc.get('default_annual')  # 岗位默认目标
        # 个人权重覆盖(单用户):有覆盖则优先;并标记 overridden 以出现「↺ 继承」
        if len(user_ids) == 1:
            _ut = user_targets_by_user.get(user_ids[0], {}).get(item_code)
            if _ut is not None and getattr(_ut, 'weight_override', None) is not None:
                item_data['weight'] = float(_ut.weight_override)
                item_data['overridden'] = True
        items_data.append(item_data)

    if scheme:
        _order = {it['item_code']: i for i, it in enumerate(scheme)}
        items_data.sort(key=lambda d: _order.get(d['item_code'], 99))

    # 角色是否已定义绩效:有 KPI 方案 或 有角色级目标(否则个人页应提示去配置管理定义)
    role_defined = bool(scheme)
    if not role_defined and len(user_ids) == 1:
        _u = user_dict.get(user_ids[0])
        role_defined = bool(_u and _u.role and role_targets_by_role.get(_u.role))

    return jsonify({
        'success': True,
        'role_defined': role_defined,
        'data': {
            'user_count': len(user_ids),
            'year': year,
            'items': items_data
        }
    })


def _batch_save_user_targets(user_ids, year, items):
    """批量保存用户绩效目标（内部函数）"""
    from app.services.role_kpi_schemes import get_role_scheme
    saved_count = 0

    for user_id in user_ids:
        user = User.query.get(user_id)
        if not user:
            continue
        # 方案默认权重(用于判断个人权重是否覆盖:与默认相同则存 None 继承)
        _scheme = get_role_scheme(user.role) if user.role else None
        _def_weight = {it['item_code']: it.get('weight') for it in (_scheme or [])}

        for item_data in items:
            if not item_data.get('enabled'):
                # 如果项目未启用，删除可能存在的覆盖
                UserPerformanceTarget.query.filter_by(
                    user_id=user_id,
                    year=year,
                    item_code=item_data['item_code']
                ).delete()
                continue

            # 查找或创建用户目标覆盖
            target = UserPerformanceTarget.query.filter_by(
                user_id=user_id,
                year=year,
                item_code=item_data['item_code']
            ).first()

            if not target:
                target = UserPerformanceTarget(
                    user_id=user_id,
                    year=year,
                    item_code=item_data['item_code'],
                    created_by=current_user.id
                )
                db.session.add(target)

            # 更新覆盖值
            target.annual_target_override = item_data.get('annual_target')
            target.enable_quarterly_override = item_data.get('enable_quarterly', False)
            target.q1_target_override = item_data.get('q1_target')
            target.q2_target_override = item_data.get('q2_target')
            target.q3_target_override = item_data.get('q3_target')
            target.q4_target_override = item_data.get('q4_target')
            target.enable_monthly_override = item_data.get('enable_monthly', False)
            target.monthly_targets_override = item_data.get('monthly_targets')
            # 权重覆盖:与方案默认相同存 None(继承),不同则存覆盖
            _w = item_data.get('weight')
            _dw = _def_weight.get(item_data['item_code'])
            if _w is None or (_dw is not None and abs(float(_w) - float(_dw)) < 0.001):
                target.weight_override = None
            else:
                target.weight_override = float(_w)
            target.updated_by = current_user.id
            target.updated_at = datetime.utcnow()

            saved_count += 1

    db.session.commit()

    logger.info(f"批量保存成功: {len(user_ids)} 个用户, {saved_count} 条配置")
    return jsonify({
        'success': True,
        'message': f'保存成功，为 {len(user_ids)} 个用户保存了配置'
    })


@performance_config_bp.route('/api/users/targets/clear', methods=['POST'])
@login_required
@permission_required('config_management', 'edit')
def api_batch_clear_user_targets():
    """批量清除用户个人绩效目标配置（恢复使用角色默认值）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据为空'})

        user_ids = data.get('user_ids', [])
        year = data.get('year', datetime.now().year)

        if not user_ids:
            return jsonify({'success': False, 'message': '未提供用户ID列表'})

        logger.info(f"=== API: 批量清除用户目标配置 user_ids={user_ids}, year={year} ===")

        # 删除用户的个人目标配置
        deleted_count = UserPerformanceTarget.query.filter(
            UserPerformanceTarget.user_id.in_(user_ids),
            UserPerformanceTarget.year == year
        ).delete(synchronize_session=False)

        db.session.commit()

        logger.info(f"批量清除成功: 删除 {deleted_count} 条个人配置")
        return jsonify({
            'success': True,
            'message': f'已清除 {deleted_count} 条个人配置',
            'data': {'deleted': deleted_count}
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"批量清除用户目标配置失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'操作失败: {str(e)}'
        }), 500


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

def can_access_person_tab(user_id, feature_id, need_edit=False):
    """个人配置某 tab 的数据 API 放行(供 budget/salary 等复用):纯功能开关驱动 ——
    admin,或 person_config view/edit + 对应 feature + 目标在数据范围内。"""
    u = current_user
    if u.role == 'admin':
        return True
    # 防自评/自定薪:非 admin 不能"编辑"自己的绩效/薪资(录入人须 ≠ 被考核人;查看不限)
    if need_edit and user_id == u.id and feature_id in ('pc_performance', 'pc_salary'):
        return False
    # HRBP 隔离(固定):hr_manager 的绩效/薪资只能访问自己负责部门的人
    if feature_id in ('pc_performance', 'pc_salary'):
        from app.helpers.hrbp_helpers import is_hrbp, in_hrbp_scope
        if is_hrbp(u):
            from app.models.user import User as _U2
            if not in_hrbp_scope(u, _U2.query.get(user_id)):
                return False
    act = 'edit' if need_edit else 'view'
    try:
        if u.has_permission('person_config', act) and u.has_feature('person_config', feature_id):
            from app.models.user import User as _U
            tgt = _U.query.get(user_id)
            if tgt and u.can_view_person(tgt, 'person_config'):
                return True
    except Exception:
        pass
    return False


def _can_read_person_perf(user_id, year=None):
    """读个人绩效数据放行(标准权限+数据范围,不再硬编码上级):
    - person_config view 且目标在数据范围内(can_view_person)
    - 兼容旧 config/user_management view(过渡)
    - 该人绩效结算当前审批人(功能性兜底,审批不被卡)"""
    try:
        from app.models.user import User as _U
        tgt = _U.query.get(user_id)
        # HRBP 隔离(固定):hr_manager 只能看自己负责部门的人(本人始终可见)
        from app.helpers.hrbp_helpers import is_hrbp, in_hrbp_scope
        if is_hrbp(current_user):
            return in_hrbp_scope(current_user, tgt)
        if tgt and current_user.can_view_person(tgt, 'person_config'):
            return True
        # 兼容旧 config/user_management view —— 但须遵守该模块数据范围(personal 不能越权看他人)
        for _m in ('config_management', 'user_management'):
            if current_user.has_permission(_m, 'view') and tgt and current_user.can_view_person(tgt, _m):
                return True
        from app.helpers.perf_settlement_helpers import is_settlement_approver_of
        return is_settlement_approver_of(current_user.id, user_id)
    except Exception:
        return False


@performance_config_bp.route('/api/user/<int:user_id>/actuals/<int:year>')
@login_required
def api_user_actuals(user_id, year):
    """个人目标页「实际/目标」双值显示的实际值数据源。

    每个 item_code 返回 月(1-12)/季(1-4)/年 三套窗口各自计算的实际值
    (率类/快照类按窗口直算才正确,不能由月值二次聚合);
    未开始的期间返回 None(前端不显示);金额类 元→万元 与目标同单位。
    codes 由前端传当前表格行,避免全量指标空算。
    """
    if not _can_read_person_perf(user_id, year):
        return jsonify({'success': False, 'message': '无权限'}), 403
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        codes = [c for c in (request.args.get('codes') or '').split(',') if c]
        if not codes:
            return jsonify({'success': True, 'data': {}})

        from app.helpers.at_dashboard_helpers import _KPI_ACTUAL_FNS
        from config import Config
        _DIVISOR = float(Config.AMOUNT_DIVISOR)       # 基础币种→显示单位(CN万=10000 / SG千=1000)
        _ALIAS = {'sales_target': 'sales_amount'}     # 定义表 code → 看板 code
        _AMOUNT = {
            'sales_target', 'implant_amount',
            'pm_implant_amount', 'pm_sales_amount',
            'se_implant_amount', 'se_sales_amount',
            'team_sales_amount', 'team_implant_amount',
            'channel_sales_amount', 'channel_implant_amount',
        }

        now = datetime.now()
        out = {}
        for code in codes:
            fn = _KPI_ACTUAL_FNS.get(_ALIAS.get(code, code))
            if not fn:
                continue
            scale = _DIVISOR if code in _AMOUNT else 1.0   # 金额按实例进制(CN万/SG千)折算,与目标/单位一致
            row = {'m': {}, 'q': {}, 'y': None}
            for m in range(1, 13):
                s = datetime(year, m, 1)
                if s > now:
                    row['m'][m] = None
                    continue
                e = datetime(year + 1, 1, 1) if m == 12 else datetime(year, m + 1, 1)
                row['m'][m] = round(fn(user, s, e) / scale, 2)
            for q in range(1, 5):
                sm = (q - 1) * 3 + 1
                s = datetime(year, sm, 1)
                if s > now:
                    row['q'][q] = None
                    continue
                e = datetime(year + 1, 1, 1) if q == 4 else datetime(year, sm + 3, 1)
                row['q'][q] = round(fn(user, s, e) / scale, 2)
            if datetime(year, 1, 1) <= now:
                row['y'] = round(fn(user, datetime(year, 1, 1), datetime(year + 1, 1, 1)) / scale, 2)
            out[code] = row

        return jsonify({'success': True, 'data': out})
    except Exception as e:
        logger.error(f"获取用户实际值失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@performance_config_bp.route('/api/user/<int:user_id>/settlement', methods=['POST'])
@login_required
@permission_required('config_management', 'edit')
def api_submit_settlement(user_id):
    """HR 发起季度绩效结算(得分由前端按当季显示传入,快照存档)。"""
    try:
        data = request.get_json() or {}
        year = int(data.get('year') or datetime.now().year)
        quarter = int(data.get('quarter') or 0)
        score = data.get('score')
        snapshot = data.get('snapshot') or []
        from app.helpers.perf_settlement_helpers import submit_settlement
        st, inst, err = submit_settlement(user_id, year, quarter, score, snapshot, current_user.id)
        if err:
            return jsonify({'success': False, 'message': err}), 400
        return jsonify({'success': True, 'message': f'已发起 {year}Q{quarter} 绩效结算审批',
                        'data': st.to_dict()})
    except Exception as e:
        logger.error(f"发起绩效结算失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@performance_config_bp.route('/api/user/<int:user_id>/settlements/<int:year>')
@login_required
def api_get_settlements(user_id, year):
    """某用户某年各季度结算状态(绩效页面板 + 薪资页锁定用)。"""
    if not _can_read_person_perf(user_id, year):
        return jsonify({'success': False, 'message': '无权限'}), 403
    try:
        from app.models.performance_settlement import PerformanceSettlement
        rows = PerformanceSettlement.query.filter_by(user_id=user_id, year=year).all()
        return jsonify({'success': True, 'data': {str(r.quarter): r.to_dict() for r in rows}})
    except Exception as e:
        logger.error(f"获取结算状态失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@performance_config_bp.route('/api/settlement-approval/<int:settlement_id>/flow')
@login_required
def api_settlement_flow(settlement_id):
    """绩效结算审批流(供 at_approval_dropdown chip 浮层渲染)。"""
    from app.helpers.perf_settlement_helpers import build_settlement_flow
    return jsonify(build_settlement_flow(settlement_id, current_user.id))


@performance_config_bp.route('/api/settlement-approval/<int:settlement_id>/editable-fields')
@login_required
def api_settlement_editable_fields(settlement_id):
    """绩效结算无可编辑字段(审批人只同意/驳回)。"""
    return jsonify({'success': True, 'can_edit': False, 'editable_fields': []})
