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
    """角色绩效配置主页面"""
    try:
        # 获取所有可配置的角色
        available_roles = get_available_roles()
        
        # 获取当前用户的默认角色（如果有的话）
        default_role = request.args.get('role', available_roles[0]['role_code'] if available_roles else 'sales_director')
        
        return render_template('performance/role_config_optimized.html',
                             available_roles=available_roles,
                             default_role=default_role)
    
    except Exception as e:
        logger.error(f"加载角色绩效配置页面失败: {e}")
        flash('页面加载失败', 'error')
        return redirect(url_for('user.index'))

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
        # 查询角色配置
        from app.models.performance_config import RolePerformanceConfig, RolePerformanceItem
        
        role_config = RolePerformanceConfig.query.filter_by(role=role_code).first()
        
        if not role_config:
            # 返回默认配置
            return jsonify({
                'success': True,
                'data': {
                    'role': role_code,
                    'config_name': f'{get_role_display_name_from_dict(role_code)}绩效方案',
                    'description': '待配置的绩效方案',
                    'access_scope': 'personal',
                    'is_active': True,
                    'items': []
                }
            })
        
        # 获取配置项目
        items = RolePerformanceItem.query.filter_by(
            role_config_id=role_config.id,
            is_enabled=True
        ).order_by(RolePerformanceItem.sort_order).all()
        
        config_data = {
            'role': role_config.role,
            'config_name': role_config.config_name,
            'description': role_config.description,
            'access_scope': get_role_access_scope(role_code),
            'is_active': role_config.is_active,
            'items': [item.to_dict() for item in items]
        }
        
        return jsonify({
            'success': True,
            'data': config_data
        })
        
    except Exception as e:
        logger.error(f"获取角色配置失败 {role_code}: {e}")
        return jsonify({
            'success': False,
            'message': f'获取角色配置失败: {str(e)}'
        })

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
    required_fields = ['config_name', 'access_scope']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'success': False,
                'message': f'缺少必要字段: {field}'
            })
    
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
        
        # 保存新的配置项目
        items = data.get('items', [])
        for i, item_data in enumerate(items):
            # 验证项目数据
            if not validate_performance_item(item_data):
                return jsonify({
                    'success': False,
                    'message': f'第{i+1}个项目数据无效'
                })
            
            # 创建绩效项目
            item = create_performance_item(role_config, item_data)
            db.session.add(item)
        
        # 保存访问权限配置
        save_role_access_config(role_code, data['access_scope'])
        
        db.session.commit()
        
        logger.info(f"角色绩效配置保存成功: {role_code}, 项目数: {len(items)}")
        
        return jsonify({
            'success': True,
            'message': f'角色配置保存成功，共配置{len(items)}个绩效项目'
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

# ===== 辅助函数 =====

def get_available_roles():
    """获取所有可配置的角色列表"""
    # 从用户表获取所有存在的角色
    existing_roles = db.session.query(User.role).distinct().all()
    existing_roles = [role[0] for role in existing_roles if role[0]]
    
    # 从role_permissions表获取已配置权限的角色
    permission_roles = db.session.query(RolePermission.role).filter_by(
        module='performance_management'
    ).distinct().all()
    permission_roles = [role[0] for role in permission_roles if role[0]]
    
    # 合并并去重
    all_roles = list(set(existing_roles + permission_roles))
    
    # 排除admin角色（admin默认有所有权限）
    all_roles = [role for role in all_roles if role not in ['admin']]
    
    # 构建角色信息
    roles_info = []
    for role in sorted(all_roles):
        # 检查是否已有绩效配置
        from app.models.performance_config import RolePerformanceConfig
        has_config = RolePerformanceConfig.query.filter_by(role=role).first() is not None
        
        roles_info.append({
            'role_code': role,
            'display_name': get_role_display_name_from_dict(role),
            'has_config': has_config,
            'user_count': User.query.filter_by(role=role).count()
        })
    
    return roles_info

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