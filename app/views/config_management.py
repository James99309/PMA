"""配置管理视图

提供全局配置管理功能，包括：
- 权限配置：配置各角色的默认权限
- 绩效配置：配置角色绩效项目
- 财务配置：批量设置用户年度报销预算
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import func
from app import db
from app.models.user import User
from app.models.dictionary import Dictionary
from app.models.role_permissions import RolePermission
from app.models.expense_budget import ExpenseBudget
from app.models.salary_config import (
    SalaryGradeConfig, SalaryGradeBandwidth, SalaryBaseParams, SalaryStepRules,
    SalaryFormulaConfig, SalesTeamConfig, EmployeeSalaryConfig
)
from app.permissions import permission_required
from app.utils.dictionary_helpers import get_role_display_name_from_dict, get_currency_type_options, get_currency_symbol
from app.utils.sharing import get_shareable_users_tree
from app.services.exchange_rate_service import exchange_rate_service
from config import Config
import logging

logger = logging.getLogger(__name__)

# =============================================
# 公式变量字典 - 用于前端显示友好名称
# =============================================

def get_formula_variable_groups():
    """
    动态获取公式变量分组（包含绩效指标）

    返回结构:
    {
        'performance': {...},    # 固定的业绩数据变量
        'salary': {...},         # 薪资配置变量
        'weight': {...},         # 权重变量
        'result': {...},         # 计算结果变量
        'kpi': {...}             # 动态KPI指标变量（从数据库加载）
    }
    """
    # 1. 基础变量组（保持不变）
    groups = {
        'performance': {
            'label': '业绩数据',
            'icon': 'trending_up',
            'items': [
                {'code': 'personal_rate', 'name': '个人完成率', 'unit': '%', 'source': '季度业绩'},
                {'code': 'team_rate', 'name': '团队完成率', 'unit': '%', 'source': '团队汇总'},
                {'code': 'comprehensive_rate', 'name': '综合完成率', 'unit': '%', 'source': '计算得出'},
                {'code': 'achievement', 'name': '业绩金额', 'unit': '万', 'source': '季度业绩'},
                {'code': 'high_price_ratio', 'name': '高批价占比', 'unit': '%', 'source': '季度业绩'},
                {'code': 'high_price_rate', 'name': '高批价率', 'unit': '%', 'source': '季度业绩'},
            ]
        },
        'salary': {
            'label': '薪资配置',
            'icon': 'payments',
            'items': [
                {'code': 'monthly_base_salary', 'name': '月基础工资', 'unit': '元', 'source': '职级配置'},
                {'code': 'monthly_performance_base', 'name': '月绩效基数', 'unit': '元', 'source': '职级配置'},
                {'code': 'annual_target', 'name': '年度目标', 'unit': '万', 'source': '职级配置'},
                {'code': 'annual_base_salary', 'name': '年基础工资', 'unit': '万', 'source': '计算'},
            ]
        },
        'weight': {
            'label': '权重',
            'icon': 'balance',
            'items': [
                {'code': 'personal_weight', 'name': '个人权重', 'unit': '', 'source': '职级配置'},
                {'code': 'team_weight', 'name': '团队权重', 'unit': '', 'source': '1-个人权重'},
            ]
        },
        'result': {
            'label': '计算结果',
            'icon': 'calculate',
            'items': [
                {'code': 'performance_salary', 'name': '绩效工资', 'unit': '万', 'source': '计算'},
                {'code': 'final_commission', 'name': '最终提成', 'unit': '万', 'source': '计算'},
                {'code': 'annual_bonus', 'name': '年终奖', 'unit': '万', 'source': '计算'},
            ]
        }
    }

    # 2. 动态加载KPI指标变量（从数据库）
    try:
        from app.models.performance_config import PerformanceMetricsDefinition

        metrics = PerformanceMetricsDefinition.query.filter_by(is_active=True).all()

        if metrics:
            kpi_items = []
            seen_codes = set()

            for metric in metrics:
                if metric.metric_code in seen_codes:
                    continue
                seen_codes.add(metric.metric_code)

                # 确定单位
                unit = ''
                if metric.data_type == 'amount':
                    unit = '万'
                elif metric.data_type == 'count':
                    unit = '个'
                elif metric.data_type == 'percentage':
                    unit = '%'

                # 实际值变量
                kpi_items.append({
                    'code': f'kpi_{metric.metric_code}',
                    'name': metric.metric_name,
                    'unit': unit,
                    'source': 'KPI实际值'
                })
                # 目标值变量
                kpi_items.append({
                    'code': f'kpi_{metric.metric_code}_target',
                    'name': f'{metric.metric_name}目标',
                    'unit': unit,
                    'source': 'KPI目标配置'
                })
                # 完成率变量
                kpi_items.append({
                    'code': f'kpi_{metric.metric_code}_rate',
                    'name': f'{metric.metric_name}完成率',
                    'unit': '%',
                    'source': '计算'
                })

            if kpi_items:
                groups['kpi'] = {
                    'label': 'KPI指标',
                    'icon': 'assessment',
                    'items': kpi_items
                }

    except Exception as e:
        logger.warning(f"加载KPI变量失败: {e}")

    return groups


# 保留原有常量用于向后兼容
FORMULA_VARIABLE_GROUPS = {
    'performance': {
        'label': '业绩数据',
        'icon': 'trending_up',
        'items': [
            {'code': 'personal_rate', 'name': '个人完成率', 'unit': '%', 'source': '季度业绩'},
            {'code': 'team_rate', 'name': '团队完成率', 'unit': '%', 'source': '团队汇总'},
            {'code': 'comprehensive_rate', 'name': '综合完成率', 'unit': '%', 'source': '计算得出'},
            {'code': 'achievement', 'name': '业绩金额', 'unit': '万', 'source': '季度业绩'},
            {'code': 'high_price_ratio', 'name': '高批价占比', 'unit': '%', 'source': '季度业绩'},
            {'code': 'high_price_rate', 'name': '高批价率', 'unit': '%', 'source': '季度业绩'},
        ]
    },
    'salary': {
        'label': '薪资配置',
        'icon': 'payments',
        'items': [
            {'code': 'monthly_base_salary', 'name': '月基础工资', 'unit': '元', 'source': '职级配置'},
            {'code': 'monthly_performance_base', 'name': '月绩效基数', 'unit': '元', 'source': '职级配置'},
            {'code': 'annual_target', 'name': '年度目标', 'unit': '万', 'source': '职级配置'},
            {'code': 'annual_base_salary', 'name': '年基础工资', 'unit': '万', 'source': '计算'},
        ]
    },
    'weight': {
        'label': '权重',
        'icon': 'balance',
        'items': [
            {'code': 'personal_weight', 'name': '个人权重', 'unit': '', 'source': '职级配置'},
            {'code': 'team_weight', 'name': '团队权重', 'unit': '', 'source': '1-个人权重'},
        ]
    },
    'result': {
        'label': '计算结果',
        'icon': 'calculate',
        'items': [
            {'code': 'performance_salary', 'name': '绩效工资', 'unit': '万', 'source': '计算'},
            {'code': 'final_commission', 'name': '最终提成', 'unit': '万', 'source': '计算'},
            {'code': 'annual_bonus', 'name': '年终奖', 'unit': '万', 'source': '计算'},
        ]
    }
}

# 阶梯规则类型映射
STEP_RULE_TYPES = {
    'performance_coefficient': '绩效系数',
    'commission_rate': '提成比例',
    'commission_release': '提成发放比例',
    'annual_bonus': '年终奖月数',
}

config_management_bp = Blueprint('config_management', __name__, url_prefix='/config-management')


@config_management_bp.route('/')
@login_required
def index():
    """配置管理主页面"""
    # 需要配置管理权限
    if not current_user.has_permission('config_management', 'view'):
        abort(403)

    try:
        # 获取角色字典
        role_dict = {d.key: d.value for d in Dictionary.query.filter_by(type='role', is_active=True).all()}

        # 获取可配置的角色列表
        available_roles = get_available_roles()

        # 获取模块列表（用于权限配置）- 按菜单顺序排列
        modules = get_ordered_modules()

        # 获取当前年份
        current_year = datetime.now().year

        # 获取用户树数据（用于归属配置）
        users_tree = get_shareable_users_tree(current_user, 'user')

        # 检查编辑权限
        can_edit = current_user.has_permission('config_management', 'edit')

        return render_template('config_management/tw_index.html',
                             role_dict=role_dict,
                             available_roles=available_roles,
                             modules=modules,
                             current_year=current_year,
                             users_tree=users_tree,
                             can_edit=can_edit,
                             currency_options=get_currency_type_options())
    except Exception as e:
        logger.error(f"加载配置管理页面失败: {e}", exc_info=True)
        flash(f'页面加载失败: {str(e)}', 'error')
        return redirect(url_for('main.index'))


# =============================================
# 权限配置 API
# =============================================

@config_management_bp.route('/api/roles')
@login_required
@permission_required('config_management', 'view')
def api_get_roles():
    """获取可配置角色列表"""
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
        }), 500


@config_management_bp.route('/api/cli-table-modules')
@login_required
@permission_required('config_management', 'view')
def api_get_cli_table_modules():
    """只读返回 CLI 表归属清单（仅管理员）"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '仅管理员可访问'}), 403
    try:
        from app.models.cli_table_module import CliTableModule
        rows = (
            CliTableModule.query
            .filter_by(is_active=True)
            .order_by(CliTableModule.sort_order, CliTableModule.table_name)
            .all()
        )
        return jsonify({
            'success': True,
            'data': [r.to_dict() for r in rows],
        })
    except Exception as e:
        logger.error(f"获取 CLI 表归属清单失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@config_management_bp.route('/api/role-permissions/<role>')
@login_required
@permission_required('config_management', 'view')
def api_get_role_permissions(role):
    """获取角色默认权限（性能优化版）"""
    from flask import session
    from app.models.permission_module import PermissionModule, PermissionModuleFeature, RoleFeaturePermission

    try:
        lang = session.get('language', 'zh')

        # === 性能优化：一次性查询所有模块 ===
        db_modules = PermissionModule.query.filter_by(is_active=True)\
            .order_by(PermissionModule.sort_order).all()

        # === 性能优化：一次性查询所有子功能，避免 N+1 问题 ===
        module_ids = [m.module_id for m in db_modules]
        all_features = PermissionModuleFeature.query.filter(
            PermissionModuleFeature.module_id.in_(module_ids),
            PermissionModuleFeature.is_active == True
        ).order_by(PermissionModuleFeature.sort_order).all()

        # 按模块ID分组子功能
        features_by_module = {}
        for f in all_features:
            if f.module_id not in features_by_module:
                features_by_module[f.module_id] = []
            features_by_module[f.module_id].append(f)

        # 构建模块列表
        modules = []
        for m in db_modules:
            module_features = features_by_module.get(m.module_id, [])
            modules.append({
                'id': m.module_id,
                'name': m.name_en if lang == 'en' and m.name_en else m.name,
                'icon': m.icon,
                'description': m.description_en if lang == 'en' and m.description_en else m.description,
                'group': m.group_name_en if lang == 'en' and m.group_name_en else m.group_name,
                'group_name': m.group_name,
                'supports_discount': m.supports_discount,
                'supports_owner_change': m.supports_owner_change,
                'supports_affiliation': m.supports_affiliation,
                'supports_content_filter': m.supports_content_filter,
                'supports_export_email': getattr(m, 'supports_export_email', False),
                'features': [f.to_dict(lang) for f in module_features]
            })

        # 如果数据库为空，使用回退
        if not modules:
            modules = get_ordered_modules()

        # 获取角色权限
        role_permissions = RolePermission.query.filter_by(role=role).all()
        permissions_dict = {}
        for perm in role_permissions:
            permissions_dict[perm.module] = {
                'module': perm.module,
                'can_view': perm.can_view,
                'can_create': perm.can_create,
                'can_edit': perm.can_edit,
                'can_delete': perm.can_delete,
                'can_change_owner': perm.can_change_owner,
                'can_export_email': getattr(perm, 'can_export_email', False),
                'permission_level': perm.permission_level or 'personal',
                'pricing_discount_limit': perm.pricing_discount_limit,
                'settlement_discount_limit': perm.settlement_discount_limit,
                'content_filter': perm.content_filters,
                'cli_can_query': bool(getattr(perm, 'cli_can_query', False)),
                'cli_permission_level': getattr(perm, 'cli_permission_level', None),
            }

        # 获取角色子功能权限
        feature_perms = RoleFeaturePermission.query.filter_by(role=role).all()
        feature_permissions = {}
        for fp in feature_perms:
            if fp.module_id not in feature_permissions:
                feature_permissions[fp.module_id] = {}
            feature_permissions[fp.module_id][fp.feature_id] = fp.is_enabled

        # 获取内容筛选配置选项
        content_filter_options = get_content_filter_options()

        return jsonify({
            'success': True,
            'data': {
                'role': role,
                'role_display': get_role_display_name_from_dict(role),
                'modules': modules,
                'permissions': permissions_dict,
                'feature_permissions': feature_permissions,
                'content_filter_options': content_filter_options
            }
        })
    except Exception as e:
        logger.error(f"获取角色权限失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取角色权限失败: {str(e)}'
        }), 500


@config_management_bp.route('/api/role-permissions/<role>', methods=['POST'])
@login_required
@permission_required('config_management', 'edit')
def api_save_role_permissions(role):
    """保存角色默认权限（性能优化版，包括子功能权限）"""
    import time
    from app.models.permission_module import RoleFeaturePermission

    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400

        permissions = data.get('permissions', {})
        feature_permissions = data.get('feature_permissions', {})

        # 非管理员保存时不得覆盖 CLI 字段 —— 先快照现有值
        existing_cli = {}
        for p in RolePermission.query.filter_by(role=role).all():
            existing_cli[p.module] = (
                bool(getattr(p, 'cli_can_query', False)),
                getattr(p, 'cli_permission_level', None),
            )

        # === 性能优化：批量删除 ===
        RolePermission.query.filter_by(role=role).delete(synchronize_session=False)

        # === 性能优化：构建批量插入数据 ===
        role_perm_records = []
        for module, perm_data in permissions.items():
            # CLI 字段：payload 未提供则保留原值（非管理员没有这两个字段）
            if 'cli_can_query' in perm_data:
                cli_can_query = bool(perm_data.get('cli_can_query', False))
                cli_permission_level = perm_data.get('cli_permission_level') or None
            else:
                cli_can_query, cli_permission_level = existing_cli.get(module, (False, None))

            role_perm_records.append({
                'role': role,
                'module': module,
                'can_view': perm_data.get('can_view', False),
                'can_create': perm_data.get('can_create', False),
                'can_edit': perm_data.get('can_edit', False),
                'can_delete': perm_data.get('can_delete', False),
                'can_change_owner': perm_data.get('can_change_owner', False),
                'can_export_email': perm_data.get('can_export_email', False),
                'permission_level': perm_data.get('permission_level', 'personal'),
                'pricing_discount_limit': perm_data.get('pricing_discount_limit'),
                'settlement_discount_limit': perm_data.get('settlement_discount_limit'),
                'content_filters': perm_data.get('content_filter'),
                'cli_can_query': cli_can_query,
                'cli_permission_level': cli_permission_level,
            })

        # === 性能优化：批量插入角色权限 ===
        if role_perm_records:
            db.session.bulk_insert_mappings(RolePermission, role_perm_records)

        # 保存子功能权限
        if feature_permissions:
            now = time.time()
            # === 性能优化：先删除该角色的所有子功能权限，再批量插入 ===
            RoleFeaturePermission.query.filter_by(role=role).delete(synchronize_session=False)

            feature_records = []
            for module_id, features in feature_permissions.items():
                for feature_id, is_enabled in features.items():
                    feature_records.append({
                        'role': role,
                        'module_id': module_id,
                        'feature_id': feature_id,
                        'is_enabled': is_enabled,
                        'created_at': now,
                        'updated_at': now
                    })

            if feature_records:
                db.session.bulk_insert_mappings(RoleFeaturePermission, feature_records)

        db.session.commit()
        logger.info(f"角色 {role} 权限保存成功，共 {len(role_perm_records)} 个模块权限")

        return jsonify({
            'success': True,
            'message': '权限保存成功'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"保存角色权限失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'保存失败: {str(e)}'
        }), 500


# =============================================
# 用户权限配置 API（支持多选批量配置）
# =============================================

@config_management_bp.route('/api/role/<role>/users')
@login_required
@permission_required('config_management', 'view')
def api_get_role_users(role):
    """获取角色下的用户列表（含权限覆盖状态）"""
    try:
        from app.models.user import User, Permission

        # 获取该角色下的所有活跃用户
        users = User.query.filter(
            User._is_active.is_(True),
            User.role == role
        ).order_by(User.real_name).all()

        # 获取这些用户中有个人权限覆盖的用户ID
        user_ids = [u.id for u in users]
        users_with_override = set()
        if user_ids:
            override_users = db.session.query(Permission.user_id).filter(
                Permission.user_id.in_(user_ids)
            ).distinct().all()
            users_with_override = {u[0] for u in override_users}

        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'real_name': user.real_name or user.username,
                'role': user.role,
                'department': user.department or '',
                'has_override': user.id in users_with_override
            })

        return jsonify({
            'success': True,
            'data': {
                'role': role,
                'role_display': get_role_display_name_from_dict(role),
                'users': users_data,
                'total_count': len(users_data)
            }
        })
    except Exception as e:
        logger.error(f"获取角色用户列表失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取用户列表失败: {str(e)}'
        }), 500


@config_management_bp.route('/api/users/permissions/batch', methods=['POST'])
@login_required
@permission_required('config_management', 'view')
def api_batch_get_user_permissions():
    """批量获取用户权限（多选用户时获取共同权限）"""
    try:
        from app.models.user import User, Permission

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400

        user_ids = data.get('user_ids', [])
        if not user_ids:
            return jsonify({'success': False, 'message': '请选择至少一个用户'}), 400

        # 获取模块列表
        modules = get_ordered_modules()

        # 获取这些用户的所有权限
        all_permissions = Permission.query.filter(
            Permission.user_id.in_(user_ids)
        ).all()

        # 按模块分组
        module_permissions = {}
        for perm in all_permissions:
            if perm.module not in module_permissions:
                module_permissions[perm.module] = []
            module_permissions[perm.module].append({
                'user_id': perm.user_id,
                'can_view': perm.can_view,
                'can_create': perm.can_create,
                'can_edit': perm.can_edit,
                'can_delete': perm.can_delete,
                'can_change_owner': perm.can_change_owner,
                'can_export_email': getattr(perm, 'can_export_email', False),
                'permission_level': perm.permission_level or 'personal',
                'pricing_discount_limit': perm.pricing_discount_limit,
                'settlement_discount_limit': perm.settlement_discount_limit,
                'content_filter': perm.content_filters,
            })

        # 构建共同权限数据（如果所有用户在某模块权限一致，则显示该权限）
        permissions = {}
        for module in modules:
            module_id = module['id']
            module_perms = module_permissions.get(module_id, [])

            if len(module_perms) == len(user_ids):
                # 所有用户都有该模块的权限配置
                # 检查是否所有权限一致
                first_perm = module_perms[0]
                all_same = all(
                    p['can_view'] == first_perm['can_view'] and
                    p['can_create'] == first_perm['can_create'] and
                    p['can_edit'] == first_perm['can_edit'] and
                    p['can_delete'] == first_perm['can_delete'] and
                    p['can_change_owner'] == first_perm['can_change_owner'] and
                    p['can_export_email'] == first_perm['can_export_email'] and
                    p['permission_level'] == first_perm['permission_level']
                    for p in module_perms
                )

                if all_same:
                    permissions[module_id] = {
                        'can_view': first_perm['can_view'],
                        'can_create': first_perm['can_create'],
                        'can_edit': first_perm['can_edit'],
                        'can_delete': first_perm['can_delete'],
                        'can_change_owner': first_perm['can_change_owner'],
                        'can_export_email': first_perm['can_export_email'],
                        'permission_level': first_perm['permission_level'],
                        'pricing_discount_limit': first_perm['pricing_discount_limit'],
                        'settlement_discount_limit': first_perm['settlement_discount_limit'],
                        'content_filter': first_perm['content_filter'],
                        'mixed': False
                    }
                else:
                    # 权限不一致，标记为混合状态
                    permissions[module_id] = {
                        'can_view': None,
                        'can_create': None,
                        'can_edit': None,
                        'can_delete': None,
                        'can_change_owner': None,
                        'can_export_email': None,
                        'permission_level': None,
                        'pricing_discount_limit': None,
                        'settlement_discount_limit': None,
                        'content_filter': None,
                        'mixed': True
                    }
            elif len(module_perms) > 0:
                # 部分用户有权限配置，标记为混合状态
                permissions[module_id] = {
                    'can_view': None,
                    'can_create': None,
                    'can_edit': None,
                    'can_delete': None,
                    'can_change_owner': None,
                    'can_export_email': None,
                    'permission_level': None,
                    'pricing_discount_limit': None,
                    'settlement_discount_limit': None,
                    'content_filter': None,
                    'mixed': True
                }
            # 如果没有用户有权限配置，则不包含该模块

        # 获取内容筛选选项（与角色权限保持一致）
        content_filter_options = get_content_filter_options()

        # 获取子功能权限（暂时为空，批量模式下不处理子功能）
        feature_permissions = {}

        return jsonify({
            'success': True,
            'data': {
                'user_ids': user_ids,
                'user_count': len(user_ids),
                'modules': modules,
                'permissions': permissions,
                'content_filter_options': content_filter_options,
                'feature_permissions': feature_permissions
            }
        })
    except Exception as e:
        logger.error(f"批量获取用户权限失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取权限失败: {str(e)}'
        }), 500


@config_management_bp.route('/api/users/permissions/batch-save', methods=['POST'])
@login_required
@permission_required('config_management', 'edit')
def api_batch_save_user_permissions():
    """批量保存用户权限覆盖（性能优化版）"""
    try:
        from app.models.user import User, Permission
        from app.utils.module_metadata import get_all_modules

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400

        user_ids = data.get('user_ids', [])
        permissions_data = data.get('permissions', {})

        if not user_ids:
            return jsonify({'success': False, 'message': '请选择至少一个用户'}), 400

        if not permissions_data:
            return jsonify({'success': False, 'message': '权限数据不能为空'}), 400

        # 验证用户存在
        users = User.query.filter(User.id.in_(user_ids)).all()
        if len(users) != len(user_ids):
            return jsonify({'success': False, 'message': '部分用户不存在'}), 400

        # 获取所有权限模块列表
        all_modules = get_all_modules()
        all_module_ids = list(all_modules.keys())

        # === 性能优化：批量删除 ===
        Permission.query.filter(Permission.user_id.in_(user_ids)).delete(synchronize_session=False)

        # === 性能优化：预先构建所有权限记录 ===
        permission_records = []

        for user_id in user_ids:
            # 添加选中模块的权限
            for module, perm_data in permissions_data.items():
                # 跳过混合状态的权限（不覆盖）
                if perm_data.get('skip_mixed'):
                    continue

                permission_records.append({
                    'user_id': user_id,
                    'module': module,
                    'can_view': perm_data.get('can_view', False),
                    'can_create': perm_data.get('can_create', False),
                    'can_edit': perm_data.get('can_edit', False),
                    'can_delete': perm_data.get('can_delete', False),
                    'can_change_owner': perm_data.get('can_change_owner', False),
                    'can_export_email': perm_data.get('can_export_email', False),
                    'permission_level': perm_data.get('permission_level', 'personal'),
                    'pricing_discount_limit': perm_data.get('pricing_discount_limit'),
                    'settlement_discount_limit': perm_data.get('settlement_discount_limit'),
                    'content_filters': perm_data.get('content_filter')
                })

            # 为未选中的模块添加"无权限"记录
            for module_id in all_module_ids:
                if module_id not in permissions_data:
                    permission_records.append({
                        'user_id': user_id,
                        'module': module_id,
                        'can_view': False,
                        'can_create': False,
                        'can_edit': False,
                        'can_delete': False,
                        'can_change_owner': False,
                        'can_export_email': False,
                        'permission_level': 'none'
                    })

        # === 性能优化：批量插入 ===
        if permission_records:
            db.session.bulk_insert_mappings(Permission, permission_records)

        db.session.commit()
        logger.info(f"批量更新 {len(user_ids)} 个用户的权限成功，共 {len(permission_records)} 条记录")

        return jsonify({
            'success': True,
            'message': f'已成功更新 {len(user_ids)} 个用户的权限'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"批量保存用户权限失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'保存失败: {str(e)}'
        }), 500


@config_management_bp.route('/api/users/<int:user_id>/permissions/reset', methods=['POST'])
@login_required
@permission_required('config_management', 'edit')
def api_reset_user_permissions(user_id):
    """重置用户权限为角色默认（删除个人覆盖）"""
    try:
        from app.models.user import User, Permission

        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404

        # 删除该用户的所有个人权限
        deleted_count = Permission.query.filter_by(user_id=user_id).delete()
        db.session.commit()

        logger.info(f"已重置用户 {user_id} 的权限，删除了 {deleted_count} 条权限记录")

        return jsonify({
            'success': True,
            'message': f'已重置用户权限为角色默认设置',
            'deleted_count': deleted_count
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"重置用户权限失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'重置失败: {str(e)}'
        }), 500


# =============================================
# 财务配置 API
# =============================================

@config_management_bp.route('/api/expense-budgets')
@login_required
@permission_required('config_management', 'view')
def api_get_expense_budgets():
    """获取用户预算列表"""
    try:
        year = request.args.get('year', datetime.now().year, type=int)
        role_filter = request.args.get('role', '')
        search = request.args.get('search', '').strip()

        # 查询用户列表
        query = User.query.filter(User._is_active == True)

        # 角色筛选
        if role_filter:
            query = query.filter(User.role == role_filter)

        # 搜索筛选
        if search:
            query = query.filter(
                db.or_(
                    User.username.ilike(f'%{search}%'),
                    User.real_name.ilike(f'%{search}%')
                )
            )

        users = query.order_by(User.real_name).all()

        # 获取这些用户的预算数据
        user_ids = [u.id for u in users]
        budgets = ExpenseBudget.query.filter(
            ExpenseBudget.user_id.in_(user_ids),
            ExpenseBudget.year == year
        ).all()

        budget_map = {b.user_id: b for b in budgets}

        # 构建返回数据
        users_data = []
        for user in users:
            budget = budget_map.get(user.id)
            users_data.append({
                'id': user.id,
                'username': user.username,
                'real_name': user.real_name or user.username,
                'role': user.role,
                'role_display': get_role_display_name_from_dict(user.role) if user.role else '-',
                'department': user.department or '-',
                'budget': {
                    'total': float(budget.total_budget or 0) if budget else 0,
                    'entertainment': float(budget.entertainment_budget or 0) if budget else 0,
                    'travel': float(budget.travel_budget or 0) if budget else 0,
                    'transport': float(budget.transport_budget or 0) if budget else 0,
                    'office': float(budget.office_budget or 0) if budget else 0,
                    'communication': float(budget.communication_budget or 0) if budget else 0,
                    'other': float(budget.other_budget or 0) if budget else 0
                } if budget else None
            })

        return jsonify({
            'success': True,
            'data': {
                'year': year,
                'users': users_data,
                'total_count': len(users_data)
            }
        })
    except Exception as e:
        logger.error(f"获取预算列表失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取预算列表失败: {str(e)}'
        }), 500


@config_management_bp.route('/api/expense-budgets/batch', methods=['POST'])
@login_required
@permission_required('config_management', 'edit')
def api_batch_set_expense_budgets():
    """批量设置用户预算"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400

        user_ids = data.get('user_ids', [])
        year = data.get('year', datetime.now().year)
        budget_data = data.get('budget', {})

        if not user_ids:
            return jsonify({'success': False, 'message': '请选择至少一个用户'}), 400

        # 批量更新或创建预算
        updated_count = 0
        created_count = 0

        for user_id in user_ids:
            # 查找现有预算
            budget = ExpenseBudget.query.filter_by(
                user_id=user_id,
                year=year
            ).first()

            if budget:
                # 更新现有预算
                budget.total_budget = budget_data.get('total', 0)
                budget.entertainment_budget = budget_data.get('entertainment', 0)
                budget.travel_budget = budget_data.get('travel', 0)
                budget.transport_budget = budget_data.get('transport', 0)
                budget.office_budget = budget_data.get('office', 0)
                budget.communication_budget = budget_data.get('communication', 0)
                budget.other_budget = budget_data.get('other', 0)
                budget.updated_at = datetime.utcnow()
                budget.updated_by = current_user.id
                updated_count += 1
            else:
                # 创建新预算
                budget = ExpenseBudget(
                    user_id=user_id,
                    year=year,
                    total_budget=budget_data.get('total', 0),
                    entertainment_budget=budget_data.get('entertainment', 0),
                    travel_budget=budget_data.get('travel', 0),
                    transport_budget=budget_data.get('transport', 0),
                    office_budget=budget_data.get('office', 0),
                    communication_budget=budget_data.get('communication', 0),
                    other_budget=budget_data.get('other', 0),
                    created_by=current_user.id
                )
                db.session.add(budget)
                created_count += 1

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'预算设置成功，更新 {updated_count} 条，新建 {created_count} 条',
            'data': {
                'updated': updated_count,
                'created': created_count
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"批量设置预算失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'设置失败: {str(e)}'
        }), 500


# =============================================
# 费用预算配置 API（新版 - 角色级别支持）
# =============================================

@config_management_bp.route('/api/role/<role_code>/budget', methods=['GET', 'POST'])
@login_required
@permission_required('config_management', 'view')
def api_role_budget(role_code):
    """获取或保存角色默认费用预算"""
    try:
        from app.models.expense_budget import RoleExpenseBudget

        # POST 请求需要 edit 权限
        if request.method == 'POST':
            if not current_user.has_permission('config_management', 'edit'):
                return jsonify({'success': False, 'message': '没有编辑权限'}), 403

        if request.method == 'GET':
            year = request.args.get('year', datetime.now().year, type=int)

            # 查找角色预算
            budget = RoleExpenseBudget.query.filter_by(
                role_code=role_code,
                year=year
            ).first()

            return jsonify({
                'success': True,
                'data': {
                    'role_code': role_code,
                    'year': year,
                    'budget': budget.get_budget_dict() if budget else {
                        'total': 0,
                        'entertainment': 0,
                        'travel': 0,
                        'transport': 0,
                        'office': 0,
                        'communication': 0,
                        'other': 0
                    }
                }
            })
        else:  # POST
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'message': '无效的请求数据'}), 400

            year = data.get('year', datetime.now().year)
            budget_data = data.get('budget', {})

            # 查找或创建角色预算
            budget = RoleExpenseBudget.query.filter_by(
                role_code=role_code,
                year=year
            ).first()

            if budget:
                # 更新现有预算
                budget.total_budget = budget_data.get('total', 0)
                budget.entertainment_budget = budget_data.get('entertainment', 0)
                budget.travel_budget = budget_data.get('travel', 0)
                budget.transport_budget = budget_data.get('transport', 0)
                budget.office_budget = budget_data.get('office', 0)
                budget.communication_budget = budget_data.get('communication', 0)
                budget.other_budget = budget_data.get('other', 0)
                budget.updated_at = datetime.utcnow()
                budget.updated_by = current_user.id
            else:
                # 创建新预算
                budget = RoleExpenseBudget(
                    role_code=role_code,
                    year=year,
                    total_budget=budget_data.get('total', 0),
                    entertainment_budget=budget_data.get('entertainment', 0),
                    travel_budget=budget_data.get('travel', 0),
                    transport_budget=budget_data.get('transport', 0),
                    office_budget=budget_data.get('office', 0),
                    communication_budget=budget_data.get('communication', 0),
                    other_budget=budget_data.get('other', 0),
                    created_by=current_user.id
                )
                db.session.add(budget)

            db.session.commit()

            return jsonify({
                'success': True,
                'message': '角色预算保存成功'
            })

    except Exception as e:
        db.session.rollback()
        logger.error(f"角色预算操作失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'操作失败: {str(e)}'
        }), 500


@config_management_bp.route('/api/users/budget/batch', methods=['POST'])
@login_required
@permission_required('config_management', 'view')  # 基础权限是view，保存操作在内部检查edit权限
def api_batch_user_budget():
    """批量获取或保存用户费用预算"""
    try:
        from app.models.expense_budget import RoleExpenseBudget

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400

        user_ids = data.get('user_ids', [])
        year = data.get('year', datetime.now().year)
        budget_data = data.get('budget')  # 如果有 budget，则是保存操作

        if not user_ids:
            return jsonify({'success': False, 'message': '请提供用户ID列表'}), 400

        if budget_data is not None:
            # ===== 保存操作需要edit权限 =====
            if not current_user.has_permission('config_management', 'edit'):
                return jsonify({'success': False, 'message': '没有编辑权限'}), 403
            updated_count = 0
            created_count = 0

            for user_id in user_ids:
                budget = ExpenseBudget.query.filter_by(
                    user_id=user_id,
                    year=year
                ).first()

                if budget:
                    budget.total_budget = budget_data.get('total', 0)
                    budget.entertainment_budget = budget_data.get('entertainment', 0)
                    budget.travel_budget = budget_data.get('travel', 0)
                    budget.transport_budget = budget_data.get('transport', 0)
                    budget.office_budget = budget_data.get('office', 0)
                    budget.communication_budget = budget_data.get('communication', 0)
                    budget.other_budget = budget_data.get('other', 0)
                    budget.updated_at = datetime.utcnow()
                    budget.updated_by = current_user.id
                    updated_count += 1
                else:
                    budget = ExpenseBudget(
                        user_id=user_id,
                        year=year,
                        total_budget=budget_data.get('total', 0),
                        entertainment_budget=budget_data.get('entertainment', 0),
                        travel_budget=budget_data.get('travel', 0),
                        transport_budget=budget_data.get('transport', 0),
                        office_budget=budget_data.get('office', 0),
                        communication_budget=budget_data.get('communication', 0),
                        other_budget=budget_data.get('other', 0),
                        created_by=current_user.id
                    )
                    db.session.add(budget)
                    created_count += 1

            db.session.commit()

            return jsonify({
                'success': True,
                'message': f'预算设置成功，为 {len(user_ids)} 位用户保存了配置',
                'data': {
                    'updated': updated_count,
                    'created': created_count
                }
            })
        else:
            # ===== 获取操作 =====
            # 获取用户信息
            users = User.query.filter(User.id.in_(user_ids)).all()
            user_dict = {u.id: u for u in users}

            if not users:
                return jsonify({'success': False, 'message': '未找到指定的用户'}), 400

            # 获取所有角色
            roles = list(set(u.role for u in users if u.role))

            # 获取角色默认预算
            role_budgets = RoleExpenseBudget.query.filter(
                RoleExpenseBudget.role_code.in_(roles),
                RoleExpenseBudget.year == year
            ).all()
            role_budget_map = {rb.role_code: rb for rb in role_budgets}

            # 获取用户预算
            user_budgets = ExpenseBudget.query.filter(
                ExpenseBudget.user_id.in_(user_ids),
                ExpenseBudget.year == year
            ).all()
            user_budget_map = {ub.user_id: ub for ub in user_budgets}

            # 计算有效预算（用户覆盖 > 角色默认）
            budget_fields = ['total', 'entertainment', 'travel', 'transport', 'office', 'communication', 'other']
            effective_budget = {}
            personal_config_flags = []  # 记录每个用户是否有个人配置

            # 单用户时获取用户的结算货币（用于角色默认预算的货币转换）
            user_currency = None
            if len(user_ids) == 1:
                user = user_dict.get(user_ids[0])
                if user:
                    user_currency = user.settlement_currency or Config.DEFAULT_CURRENCY

            for field in budget_fields:
                values = []
                for user_id in user_ids:
                    user = user_dict.get(user_id)
                    if not user:
                        continue

                    user_budget = user_budget_map.get(user_id)
                    role_budget = role_budget_map.get(user.role)

                    # 记录是否有个人配置（只在第一个字段时记录）
                    if field == 'total':
                        personal_config_flags.append(user_budget is not None)

                    # 优先用户值（已按用户货币存储），其次角色值（需要货币转换）
                    if user_budget:
                        field_name = f'{field}_budget' if field != 'total' else 'total_budget'
                        value = getattr(user_budget, field_name, 0)
                    elif role_budget:
                        field_name = f'{field}_budget' if field != 'total' else 'total_budget'
                        value = getattr(role_budget, field_name, 0)
                        # 角色默认预算使用系统货币，转换为用户结算货币
                        if user_currency and user_currency != Config.DEFAULT_CURRENCY and value:
                            value = exchange_rate_service.convert_amount(
                                float(value), Config.DEFAULT_CURRENCY, user_currency
                            )
                    else:
                        value = 0

                    values.append(float(value or 0))

                # 如果所有用户值相同，返回该值；否则返回0（表示不一致）
                unique_values = set(values)
                if len(unique_values) == 1:
                    effective_budget[field] = list(unique_values)[0]
                else:
                    effective_budget[field] = 0

            # 计算配置来源状态
            # True: 所有用户都有个人配置
            # False: 所有用户都没有个人配置（使用角色默认）
            # 'mixed': 混合情况
            if all(personal_config_flags):
                has_personal_config = True
            elif not any(personal_config_flags):
                has_personal_config = False
            else:
                has_personal_config = 'mixed'

            return jsonify({
                'success': True,
                'data': {
                    'user_count': len(user_ids),
                    'year': year,
                    'budget': effective_budget,
                    'has_personal_config': has_personal_config,
                    'user_currency': user_currency  # 返回用户的结算货币
                }
            })

    except Exception as e:
        db.session.rollback()
        logger.error(f"批量用户预算操作失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'操作失败: {str(e)}'
        }), 500


@config_management_bp.route('/api/users/budget/clear', methods=['POST'])
@login_required
@permission_required('config_management', 'edit')
def api_clear_user_budget():
    """清除用户个人费用预算配置（恢复使用角色默认值）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400

        user_ids = data.get('user_ids', [])
        year = data.get('year', datetime.now().year)

        if not user_ids:
            return jsonify({'success': False, 'message': '请提供用户ID列表'}), 400

        # 删除用户的个人预算配置
        deleted_count = ExpenseBudget.query.filter(
            ExpenseBudget.user_id.in_(user_ids),
            ExpenseBudget.year == year
        ).delete(synchronize_session=False)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'已清除 {deleted_count} 条个人配置',
            'data': {'deleted': deleted_count}
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"清除用户预算失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'操作失败: {str(e)}'
        }), 500


# =============================================
# 辅助函数
# =============================================

def get_ordered_modules():
    """
    获取按菜单顺序排列的模块列表（数据库驱动）

    优先从数据库读取，失败时使用硬编码回退

    Returns:
        list: [{'id': 'customer', 'name': '客户管理', 'icon': 'contacts', ...}, ...]
    """
    from flask import session
    from app.models.permission_module import PermissionModule

    lang = session.get('language', 'zh')

    try:
        modules = PermissionModule.query.filter_by(is_active=True)\
            .order_by(PermissionModule.sort_order).all()

        if modules:
            result = []
            for m in modules:
                result.append({
                    'id': m.module_id,
                    'name': m.name_en if lang == 'en' and m.name_en else m.name,
                    'icon': m.icon,
                    'description': m.description_en if lang == 'en' and m.description_en else m.description,
                    'group': m.group_name_en if lang == 'en' and m.group_name_en else m.group_name,
                    'group_name': m.group_name,
                    'supports_discount': m.supports_discount,
                    'supports_owner_change': m.supports_owner_change,
                    'supports_affiliation': m.supports_affiliation,
                    'supports_content_filter': m.supports_content_filter,
                    'supports_export_email': getattr(m, 'supports_export_email', False)
                })
            return result
    except Exception:
        pass

    # 回退：硬编码模块列表（数据库为空或查询失败时）
    ORDERED_MODULES_FALLBACK = [
        # 业务管理
        {'id': 'customer', 'name': '客户管理', 'icon': 'contacts', 'description': '管理客户信息和联系人', 'group': '业务管理'},
        {'id': 'project', 'name': '项目管理', 'icon': 'cases', 'description': '管理销售项目和跟进', 'group': '业务管理'},
        {'id': 'quotation', 'name': '报价管理', 'icon': 'request_quote', 'description': '管理产品报价', 'group': '业务管理'},
        {'id': 'expense', 'name': '报销管理', 'icon': 'receipt_long', 'description': '管理员工报销申请', 'group': '业务管理'},
        # 产品管理
        {'id': 'product', 'name': '产品管理', 'icon': 'inventory_2', 'description': '管理产品信息和价格', 'group': '产品管理'},
        {'id': 'product_code', 'name': '产品编码', 'icon': 'category', 'description': '管理产品编码系统', 'group': '产品管理'},
        # 订单结算
        {'id': 'order', 'name': '订单管理', 'icon': 'list_alt', 'description': '管理销售订单', 'group': '订单结算'},
        {'id': 'settlement', 'name': '结算管理', 'icon': 'payments', 'description': '管理财务结算', 'group': '订单结算'},
        {'id': 'inventory', 'name': '库存管理', 'icon': 'warehouse', 'description': '管理产品库存', 'group': '订单结算'},
        {'id': 'pricing_order', 'name': '批价单管理', 'icon': 'sell', 'description': '管理批价单', 'group': '订单结算'},
        {'id': 'settlement_order', 'name': '结算单管理', 'icon': 'credit_card', 'description': '管理结算单', 'group': '订单结算'},
        # 账户管理
        {'id': 'user_management', 'name': '用户管理', 'icon': 'group', 'description': '管理系统用户', 'group': '账户管理'},
        {'id': 'config_management', 'name': '配置管理', 'icon': 'settings', 'description': '管理系统权限和配置', 'group': '账户管理'},
        {'id': 'dictionary_management', 'name': '字典管理', 'icon': 'menu_book', 'description': '管理系统字典数据', 'group': '账户管理'},
        # 系统管理
        {'id': 'approval', 'name': '审批中心', 'icon': 'task_alt', 'description': '管理审批流程和审批记录', 'group': '系统管理'},
        {'id': 'system_settings', 'name': '系统参数设置', 'icon': 'settings_applications', 'description': '管理系统参数配置', 'group': '系统管理'},
        {'id': 'version_management', 'name': '版本管理', 'icon': 'update', 'description': '管理系统版本', 'group': '系统管理'},
        {'id': 'approval_config', 'name': '审批流程配置', 'icon': 'rule', 'description': '配置审批流程模板', 'group': '系统管理'},
        {'id': 'change_history', 'name': '历史记录', 'icon': 'history', 'description': '查看操作历史记录', 'group': '系统管理'},
        {'id': 'backup', 'name': '数据库备份', 'icon': 'cloud_upload', 'description': '管理数据库备份', 'group': '系统管理'},
    ]
    return ORDERED_MODULES_FALLBACK


def get_content_filter_options():
    """
    获取内容筛选选项配置（从数据库读取）

    返回各模块支持的内容筛选选项，用于权限面板的内容筛选配置

    Returns:
        dict: {
            'module_id': {
                'filter_key': {
                    'label': '筛选项名称',
                    'options': [(key, label), ...]
                },
                ...
            },
            ...
        }
    """
    from app.utils.dictionary_helpers import (
        get_project_type_options, get_project_stage_options,
        get_report_source_options, get_company_type_options,
        get_industry_options, get_business_type_options
    )
    from flask_babel import lazy_gettext as _l

    return {
        # 项目模块筛选选项
        'project': {
            'project_type': {
                'label': str(_l('项目类型')),
                'options': get_project_type_options()
            },
            'current_stage': {
                'label': str(_l('项目阶段')),
                'options': get_project_stage_options()
            },
            'report_source': {
                'label': str(_l('报备来源')),
                'options': get_report_source_options()
            }
        },
        # 客户模块筛选选项
        'customer': {
            'company_type': {
                'label': str(_l('企业类型')),
                'options': get_company_type_options()
            },
            'industry': {
                'label': str(_l('行业分类')),
                'options': get_industry_options()
            },
            'source': {
                'label': str(_l('来源')),
                'options': get_report_source_options()
            }
        },
        # 批价单模块筛选选项
        'pricing_order': {
            'business_type': {
                'label': str(_l('业务类型')),
                'options': get_business_type_options()
            }
        },
        # 结算单模块筛选选项
        'settlement_order': {
            'business_type': {
                'label': str(_l('业务类型')),
                'options': get_business_type_options()
            }
        },
        # 报价单模块筛选选项
        'quotation': {
            'project_type': {
                'label': str(_l('项目类型')),
                'options': get_project_type_options(),
                # 需要 JOIN 项目表来过滤
                'join_config': {
                    'model': 'Project',
                    'join_on': 'project_id',
                    'filter_attr': 'project_type'
                }
            }
        }
    }


def get_available_roles():
    """获取可配置的角色列表"""
    try:
        # 角色图标映射
        role_icons = {
            'sales_director': 'supervisor_account',
            'sales_manager': 'badge',
            'sales': 'person',
            'channel_manager': 'share',
            'customer_sales': 'support_agent',
            'dealer': 'storefront',
            'finance_director': 'account_balance',
            'finance': 'payments',
            'ceo': 'verified_user',
            'product_manager': 'inventory_2',
            'service_manager': 'engineering',
            'business_admin': 'manage_accounts',
            'rd_manager': 'science',
        }

        # 从用户表获取所有存在的角色及其用户数量
        # 注意：User.is_active 是 property，实际列名是 _is_active
        role_counts = db.session.query(
            User.role,
            func.count(User.id)
        ).filter(
            User._is_active.is_(True),
            User.role.isnot(None),
            User.role != ''
        ).group_by(User.role).all()

        logger.info(f"角色用户数量: {dict(role_counts)}")

        role_count_dict = {role: count for role, count in role_counts}
        existing_roles = list(role_count_dict.keys())

        # 从角色字典获取所有角色
        dict_roles = Dictionary.query.filter_by(type='role', is_active=True).all()
        dict_role_keys = [d.key for d in dict_roles]

        # 合并并去重
        all_roles = list(set(existing_roles + dict_role_keys))

        # 排除admin角色
        all_roles = [role for role in all_roles if role not in ['admin']]

        # 构建角色信息
        roles_info = []
        for role in sorted(all_roles):
            # 获取用户数量
            user_count = role_count_dict.get(role, 0)

            # 检查是否有权限配置
            has_permissions = RolePermission.query.filter_by(role=role).first() is not None

            roles_info.append({
                'role_code': role,
                'display_name': get_role_display_name_from_dict(role),
                'user_count': user_count,
                'has_permissions': has_permissions,
                'icon': role_icons.get(role, 'person')
            })

        return roles_info
    except Exception as e:
        logger.error(f"获取角色列表失败: {e}", exc_info=True)
        return []


# =============================================
# 厂商用户 API
# =============================================

@config_management_bp.route('/api/vendor-users')
@login_required
@permission_required('config_management', 'view')
def api_get_vendor_users():
    """获取厂商公司的所有用户（扁平列表，用于薪资分配或绩效配置）"""
    try:
        from flask import session
        from datetime import datetime
        # 获取搜索关键字、年份和配置类型参数
        search = request.args.get('search', '').strip()
        year = request.args.get('year', datetime.now().year, type=int)
        # config_type: 'salary' 薪资配置, 'performance' 绩效目标配置
        config_type = request.args.get('config_type', 'salary')

        # 获取角色字典用于显示名称转换
        role_dict = {d.key: d.value for d in Dictionary.query.filter_by(type='role', is_active=True).all()}

        # 1. 获取所有公司名称（包括厂商和第三方）
        all_companies = Dictionary.query.filter_by(
            type='company', is_active=True
        ).all()
        company_names = [c.value for c in all_companies]

        if not company_names:
            return jsonify({
                'success': True,
                'data': {
                    'users': [],
                    'total': 0
                }
            })

        # 2. 查询属于这些公司的用户（包含未激活用户）
        query = User.query.filter(
            User.company_name.in_(company_names)
        )

        # 3. 搜索过滤
        if search:
            query = query.filter(
                db.or_(
                    User.real_name.ilike(f'%{search}%'),
                    User.username.ilike(f'%{search}%')
                )
            )

        # 4. 排序并获取用户
        users = query.order_by(User.real_name).all()

        # 5. 获取配置状态（根据 config_type 查询不同的表）
        user_ids = [u.id for u in users]
        configs = {}
        users_with_performance = set()

        if user_ids:
            if config_type == 'performance':
                # 绩效目标配置：有实际目标值（任一目标 > 0）才算已配置
                from app.models.performance import PerformanceTarget
                targets = PerformanceTarget.query.filter(
                    PerformanceTarget.user_id.in_(user_ids),
                    PerformanceTarget.year == year,
                    db.or_(
                        PerformanceTarget.sales_amount_target > 0,
                        PerformanceTarget.implant_amount_target > 0,
                        PerformanceTarget.new_customers_target > 0,
                        PerformanceTarget.new_projects_target > 0
                    )
                ).all()
                users_with_performance = {t.user_id for t in targets}
            elif config_type == 'affiliation':
                # 归属配置：作为 viewer 有归属记录（该用户配置了可以查看谁）
                from app.models.user import Affiliation
                affiliations = Affiliation.query.filter(
                    Affiliation.viewer_id.in_(user_ids)
                ).all()
                users_with_performance = {a.viewer_id for a in affiliations}
            elif config_type == 'expense':
                # 费用配置：有费用预算记录
                from app.models.expense_budget import ExpenseBudget
                budgets = ExpenseBudget.query.filter(
                    ExpenseBudget.user_id.in_(user_ids),
                    ExpenseBudget.year == year
                ).all()
                users_with_performance = {b.user_id for b in budgets}
            elif config_type == 'none':
                # 不需要绿色标记的页面（如基本配置）
                users_with_performance = set()
            else:
                # 薪资配置：查询 EmployeeSalaryConfig 表
                from app.models.salary_config import EmployeeSalaryConfig
                salary_configs = EmployeeSalaryConfig.query.filter(
                    EmployeeSalaryConfig.user_id.in_(user_ids),
                    EmployeeSalaryConfig.year == year
                ).all()
                configs = {c.user_id: c for c in salary_configs}

        # 5.5 获取团队信息（用于排序显示）
        from app.models.salary_config import SalesTeamConfig
        teams = SalesTeamConfig.query.filter_by(is_active=True).all()
        team_dict = {t.id: t for t in teams}
        # 团队领导ID集合
        team_leader_ids = {t.team_leader_id for t in teams if t.team_leader_id}

        # 6. 构建返回数据
        users_data = []
        for u in users:
            if config_type in ('performance', 'affiliation', 'expense', 'none'):
                # 绩效/归属/费用/none配置：使用 users_with_performance 集合判断
                has_actual_config = u.id in users_with_performance
                grade_id = None
                team_id = None
            else:
                # 薪资配置：有 grade_id 或 team_id 才算已配置
                config = configs.get(u.id)
                has_actual_config = config is not None and (config.grade_id is not None or config.team_id is not None)
                grade_id = config.grade_id if config else None
                team_id = config.team_id if config else None

            # 角色显示名称：优先使用字典映射，否则使用原始值
            role_display = role_dict.get(u.role, u.role) if u.role else ''

            # 获取团队名称
            team_name = None
            if team_id and team_id in team_dict:
                team_name = team_dict[team_id].team_name

            users_data.append({
                'id': u.id,
                'username': u.username,
                'real_name': u.real_name or u.username,
                'company_name': u.company_name,
                'department': u.department,
                'role': role_display,
                'has_config': has_actual_config,
                'grade_id': grade_id,
                'team_id': team_id,
                'team_name': team_name,
                'is_active': u.is_active,
                'is_department_manager': u.is_department_manager or False,
                'is_team_leader': u.id in team_leader_ids,
                'settlement_currency': u.settlement_currency
            })

        return jsonify({
            'success': True,
            'data': {
                'users': users_data,
                'total': len(users_data)
            }
        })
    except Exception as e:
        logger.error(f"获取厂商用户列表失败: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取用户列表失败: {str(e)}'
        }), 500


# =============================================
# 薪资配置 API
# =============================================

@config_management_bp.route('/api/salary/grades')
@login_required
@permission_required('config_management', 'view')
def api_get_salary_grades():
    """获取职级配置列表"""
    try:
        grade_type = request.args.get('type', '')  # L/M 或 空表示全部

        query = SalaryGradeConfig.query.filter_by(is_active=True)
        if grade_type:
            query = query.filter_by(grade_type=grade_type)

        grades = query.order_by(SalaryGradeConfig.grade_type, SalaryGradeConfig.sort_order).all()

        return jsonify({
            'success': True,
            'data': [g.to_dict() for g in grades]
        })
    except Exception as e:
        logger.error(f"获取职级配置失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'获取职级配置失败: {str(e)}'}), 500


@config_management_bp.route('/api/salary/grades', methods=['POST'])
@login_required
@permission_required('config_management', 'edit')
def api_save_salary_grade():
    """保存职级配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400

        grade_id = data.get('id')
        grade_code = data.get('grade_code', '').strip()
        grade_name = data.get('grade_name', '').strip()
        grade_type = data.get('grade_type', 'L')

        if not grade_code or not grade_name:
            return jsonify({'success': False, 'message': '职级代码和名称不能为空'}), 400

        if grade_id:
            # 更新现有记录
            grade = SalaryGradeConfig.query.get(grade_id)
            if not grade:
                return jsonify({'success': False, 'message': '职级不存在'}), 404
        else:
            # 检查代码是否重复
            existing = SalaryGradeConfig.query.filter_by(grade_code=grade_code).first()
            if existing:
                return jsonify({'success': False, 'message': f'职级代码 {grade_code} 已存在'}), 400
            grade = SalaryGradeConfig()

        # 更新字段
        grade.grade_code = grade_code
        grade.grade_name = grade_name
        grade.grade_type = grade_type
        grade.annual_target = data.get('annual_target')
        grade.monthly_base_salary = data.get('monthly_base_salary')
        grade.monthly_performance_base = data.get('monthly_performance_base')
        grade.monthly_management_allowance = data.get('monthly_management_allowance', 0)
        grade.personal_weight = data.get('personal_weight', 1)
        grade.sort_order = data.get('sort_order', 0)

        if not grade_id:
            db.session.add(grade)

        db.session.flush()

        # 处理薪资带宽
        bandwidth_data = data.get('bandwidth')
        if bandwidth_data:
            bandwidth = grade.bandwidth
            if not bandwidth:
                bandwidth = SalaryGradeBandwidth(grade_id=grade.id)
                db.session.add(bandwidth)

            bandwidth.base_salary_min = bandwidth_data.get('base_salary_min')
            bandwidth.base_salary_mid = bandwidth_data.get('base_salary_mid')
            bandwidth.base_salary_max = bandwidth_data.get('base_salary_max')
            bandwidth.performance_base_min = bandwidth_data.get('performance_base_min')
            bandwidth.performance_base_mid = bandwidth_data.get('performance_base_mid')
            bandwidth.performance_base_max = bandwidth_data.get('performance_base_max')
            bandwidth.target_min = bandwidth_data.get('target_min')
            bandwidth.target_mid = bandwidth_data.get('target_mid')
            bandwidth.target_max = bandwidth_data.get('target_max')

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '职级保存成功',
            'data': grade.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"保存职级配置失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'}), 500


@config_management_bp.route('/api/salary/grades/<int:grade_id>', methods=['DELETE'])
@login_required
@permission_required('config_management', 'edit')
def api_delete_salary_grade(grade_id):
    """删除职级配置"""
    try:
        grade = SalaryGradeConfig.query.get(grade_id)
        if not grade:
            return jsonify({'success': False, 'message': '职级不存在'}), 404

        # 检查是否有员工使用此职级
        employee_count = EmployeeSalaryConfig.query.filter_by(grade_id=grade_id).count()
        if employee_count > 0:
            return jsonify({'success': False, 'message': f'此职级有 {employee_count} 名员工正在使用，无法删除'}), 400

        grade.is_active = False
        db.session.commit()

        return jsonify({'success': True, 'message': '职级删除成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除职级配置失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500


@config_management_bp.route('/api/salary/base-params')
@login_required
@permission_required('config_management', 'view')
def api_get_salary_base_params():
    """获取基础参数配置"""
    try:
        params = SalaryBaseParams.query.filter_by(is_active=True).all()
        return jsonify({
            'success': True,
            'data': [p.to_dict() for p in params]
        })
    except Exception as e:
        logger.error(f"获取基础参数失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'获取基础参数失败: {str(e)}'}), 500


@config_management_bp.route('/api/salary/base-params', methods=['POST'])
@login_required
@permission_required('config_management', 'edit')
def api_save_salary_base_param():
    """保存基础参数"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400

        param_id = data.get('id')
        param_code = data.get('param_code', '').strip()
        param_name = data.get('param_name', '').strip()

        if not param_code or not param_name:
            return jsonify({'success': False, 'message': '参数代码和名称不能为空'}), 400

        if param_id:
            param = SalaryBaseParams.query.get(param_id)
            if not param:
                return jsonify({'success': False, 'message': '参数不存在'}), 404
        else:
            existing = SalaryBaseParams.query.filter_by(param_code=param_code).first()
            if existing:
                return jsonify({'success': False, 'message': f'参数代码 {param_code} 已存在'}), 400
            param = SalaryBaseParams()

        param.param_code = param_code
        param.param_name = param_name
        param.param_value = data.get('param_value')
        param.param_unit = data.get('param_unit')
        param.description = data.get('description')

        if not param_id:
            db.session.add(param)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '参数保存成功',
            'data': param.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"保存基础参数失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'}), 500


@config_management_bp.route('/api/salary/step-rules')
@login_required
@permission_required('config_management', 'view')
def api_get_salary_step_rules():
    """获取阶梯规则列表"""
    try:
        rule_type = request.args.get('type', '')

        query = SalaryStepRules.query.filter_by(is_active=True)
        if rule_type:
            query = query.filter_by(rule_type=rule_type)

        rules = query.order_by(SalaryStepRules.rule_type, SalaryStepRules.min_threshold.desc()).all()

        # 始终返回数组格式，前端会按类型过滤
        return jsonify({
            'success': True,
            'data': [rule.to_dict() for rule in rules]
        })
    except Exception as e:
        logger.error(f"获取阶梯规则失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'获取阶梯规则失败: {str(e)}'}), 500


@config_management_bp.route('/api/salary/step-rules', methods=['POST'])
@login_required
@permission_required('config_management', 'edit')
def api_save_salary_step_rule():
    """保存阶梯规则"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400

        rule_id = data.get('id')
        rule_type = data.get('rule_type', '').strip()

        if not rule_type:
            return jsonify({'success': False, 'message': '规则类型不能为空'}), 400

        if rule_id:
            rule = SalaryStepRules.query.get(rule_id)
            if not rule:
                return jsonify({'success': False, 'message': '规则不存在'}), 404
        else:
            rule = SalaryStepRules()

        rule.rule_type = rule_type
        rule.min_threshold = data.get('min_threshold')
        rule.max_threshold = data.get('max_threshold')
        rule.coefficient = data.get('coefficient')
        rule.description = data.get('description')
        rule.sort_order = data.get('sort_order', 0)

        if not rule_id:
            db.session.add(rule)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '规则保存成功',
            'data': rule.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"保存阶梯规则失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'}), 500


@config_management_bp.route('/api/salary/step-rules/<int:rule_id>', methods=['DELETE'])
@login_required
@permission_required('config_management', 'edit')
def api_delete_salary_step_rule(rule_id):
    """删除阶梯规则"""
    try:
        rule = SalaryStepRules.query.get(rule_id)
        if not rule:
            return jsonify({'success': False, 'message': '规则不存在'}), 404

        rule.is_active = False
        db.session.commit()

        return jsonify({'success': True, 'message': '规则删除成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除阶梯规则失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500


@config_management_bp.route('/api/salary/formulas')
@login_required
@permission_required('config_management', 'view')
def api_get_salary_formulas():
    """获取公式配置列表"""
    try:
        formulas = SalaryFormulaConfig.query.filter_by(is_active=True)\
            .order_by(SalaryFormulaConfig.sort_order).all()

        return jsonify({
            'success': True,
            'data': [f.to_dict() for f in formulas]
        })
    except Exception as e:
        logger.error(f"获取公式配置失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'获取公式配置失败: {str(e)}'}), 500


@config_management_bp.route('/api/salary/formula-variables')
@login_required
@permission_required('config_management', 'view')
def api_get_formula_variables():
    """获取公式可用变量列表（分组）- 包含动态KPI指标"""
    try:
        # 使用动态函数获取变量组（包含KPI指标）
        variable_groups = get_formula_variable_groups()

        return jsonify({
            'success': True,
            'data': {
                'variableGroups': variable_groups,
                'stepRuleTypes': STEP_RULE_TYPES
            }
        })
    except Exception as e:
        logger.error(f"获取公式变量失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@config_management_bp.route('/api/salary/formulas', methods=['POST'])
@login_required
@permission_required('config_management', 'edit')
def api_save_salary_formula():
    """保存公式配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400

        formula_id = data.get('id')
        formula_code = data.get('formula_code', '').strip()
        formula_name = data.get('formula_name', '').strip()

        if not formula_code or not formula_name:
            return jsonify({'success': False, 'message': '公式代码和名称不能为空'}), 400

        if formula_id:
            formula = SalaryFormulaConfig.query.get(formula_id)
            if not formula:
                return jsonify({'success': False, 'message': '公式不存在'}), 404
        else:
            existing = SalaryFormulaConfig.query.filter_by(formula_code=formula_code).first()
            if existing:
                return jsonify({'success': False, 'message': f'公式代码 {formula_code} 已存在'}), 400
            formula = SalaryFormulaConfig()

        formula.formula_code = formula_code
        formula.formula_name = formula_name
        formula.description = data.get('description')
        formula.variables = data.get('variables')
        formula.result_unit = data.get('result_unit')
        formula.sort_order = data.get('sort_order', 0)

        # 新增字段：适用职级类型和结构化公式元素
        formula.applicable_grade_type = data.get('applicable_grade_type', 'ALL')
        formula.formula_elements = data.get('formula_elements')

        # 如果有结构化公式元素，自动生成表达式
        if formula.formula_elements:
            formula.formula_expression = SalaryFormulaConfig.elements_to_expression(formula.formula_elements)
        else:
            formula.formula_expression = data.get('formula_expression')

        if not formula_id:
            db.session.add(formula)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '公式保存成功',
            'data': formula.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"保存公式配置失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'}), 500


@config_management_bp.route('/api/salary/teams')
@login_required
@permission_required('config_management', 'view')
def api_get_salary_teams():
    """获取团队配置列表"""
    try:
        teams = SalesTeamConfig.query.filter_by(is_active=True).all()

        return jsonify({
            'success': True,
            'data': [t.to_dict() for t in teams]
        })
    except Exception as e:
        logger.error(f"获取团队配置失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'获取团队配置失败: {str(e)}'}), 500


@config_management_bp.route('/api/salary/teams', methods=['POST'])
@login_required
@permission_required('config_management', 'edit')
def api_save_salary_team():
    """保存团队配置"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400

        team_id = data.get('id')
        team_name = data.get('team_name', '').strip()

        if not team_name:
            return jsonify({'success': False, 'message': '团队名称不能为空'}), 400

        if team_id:
            team = SalesTeamConfig.query.get(team_id)
            if not team:
                return jsonify({'success': False, 'message': '团队不存在'}), 404
        else:
            team = SalesTeamConfig()

        team.team_name = team_name
        team.team_leader_id = data.get('team_leader_id')
        team.leader_grade = data.get('leader_grade')
        team.annual_target = data.get('annual_target')

        if not team_id:
            db.session.add(team)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '团队保存成功',
            'data': team.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"保存团队配置失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'}), 500


@config_management_bp.route('/api/salary/teams/<int:team_id>', methods=['DELETE'])
@login_required
@permission_required('config_management', 'edit')
def api_delete_salary_team(team_id):
    """删除团队配置"""
    try:
        team = SalesTeamConfig.query.get(team_id)
        if not team:
            return jsonify({'success': False, 'message': '团队不存在'}), 404

        # 检查是否有员工在此团队
        employee_count = EmployeeSalaryConfig.query.filter_by(team_id=team_id).count()
        if employee_count > 0:
            return jsonify({'success': False, 'message': f'此团队有 {employee_count} 名成员，无法删除'}), 400

        team.is_active = False
        db.session.commit()

        return jsonify({'success': True, 'message': '团队删除成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除团队配置失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500


# =============================================
# 用户薪资配置 API
# =============================================

@config_management_bp.route('/api/salary/user/<int:user_id>/config')
@login_required
@permission_required('config_management', 'view')
def get_user_salary_config(user_id):
    """获取用户薪资配置"""
    try:
        from app.models.salary_config import EmployeeSalaryConfig

        year = request.args.get('year', datetime.now().year, type=int)
        config = EmployeeSalaryConfig.query.filter_by(user_id=user_id, year=year).first()

        if config:
            return jsonify({
                'success': True,
                'data': config.to_dict()
            })
        else:
            return jsonify({
                'success': True,
                'data': None
            })
    except Exception as e:
        logger.error(f"获取用户薪资配置失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@config_management_bp.route('/api/salary/users/batch-config', methods=['POST'])
@login_required
@permission_required('config_management', 'edit')
def batch_save_user_salary_config():
    """批量保存用户薪资配置"""
    try:
        from app.models.salary_config import EmployeeSalaryConfig

        data = request.get_json()
        user_ids = data.get('user_ids', [])
        config_data = data.get('config', {})
        year = data.get('year', datetime.now().year)

        if not user_ids:
            return jsonify({'success': False, 'message': '请选择用户'}), 400

        for user_id in user_ids:
            # 按 user_id 和 year 查找配置
            config = EmployeeSalaryConfig.query.filter_by(user_id=user_id, year=year).first()

            if not config:
                config = EmployeeSalaryConfig(user_id=user_id, year=year)
                db.session.add(config)

            # 更新配置
            if 'grade_id' in config_data:
                config.grade_id = config_data['grade_id'] or None
            if 'team_id' in config_data:
                config.team_id = config_data['team_id'] or None
            if 'use_custom_config' in config_data:
                config.use_custom_config = config_data['use_custom_config']
            if 'monthly_base_salary_override' in config_data:
                config.monthly_base_salary_override = config_data['monthly_base_salary_override']
            if 'monthly_performance_base_override' in config_data:
                config.monthly_performance_base_override = config_data['monthly_performance_base_override']
            if 'annual_target_override' in config_data:
                config.annual_target_override = config_data['annual_target_override']

            config.configured_by = current_user.id
            config.configured_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'已保存 {len(user_ids)} 位用户的 {year} 年薪资配置'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"批量保存用户薪资配置失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@config_management_bp.route('/api/salary/users/apply-role-config', methods=['POST'])
@login_required
@permission_required('config_management', 'edit')
def apply_role_salary_config():
    """应用角色默认配置到用户"""
    try:
        from app.models.salary_config import EmployeeSalaryConfig, SalaryGradeConfig

        data = request.get_json()
        user_ids = data.get('user_ids', [])
        role_code = data.get('role_code', '')
        year = data.get('year', datetime.now().year)

        if not user_ids or not role_code:
            return jsonify({'success': False, 'message': '参数不完整'}), 400

        # 根据角色获取默认职级（这里可以根据业务需求扩展）
        # 目前简单处理：清除用户的自定义配置
        for user_id in user_ids:
            config = EmployeeSalaryConfig.query.filter_by(user_id=user_id, year=year).first()

            if config:
                config.use_custom_config = False
                config.monthly_base_salary_override = None
                config.monthly_performance_base_override = None
                config.annual_target_override = None
                config.configured_by = current_user.id
                config.configured_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'已应用角色配置到 {len(user_ids)} 位用户（{year}年）'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"应用角色配置失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@config_management_bp.route('/api/salary/users/clear-config', methods=['POST'])
@login_required
@permission_required('config_management', 'edit')
def clear_user_salary_config():
    """清除用户个人薪资配置"""
    try:
        from app.models.salary_config import EmployeeSalaryConfig

        data = request.get_json()
        user_ids = data.get('user_ids', [])
        year = data.get('year', datetime.now().year)

        if not user_ids:
            return jsonify({'success': False, 'message': '请选择用户'}), 400

        for user_id in user_ids:
            config = EmployeeSalaryConfig.query.filter_by(user_id=user_id, year=year).first()

            if config:
                # 清除所有配置（包括职级和团队）
                config.grade_id = None
                config.team_id = None
                config.use_custom_config = False
                config.monthly_base_salary_override = None
                config.monthly_performance_base_override = None
                config.monthly_management_allowance_override = None
                config.annual_target_override = None
                config.personal_weight_override = None
                config.commission_rate_multiplier = 1
                config.bonus_multiplier = 1
                config.team_share_rate_override = None
                config.configured_by = current_user.id
                config.configured_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'已清除 {len(user_ids)} 位用户的 {year} 年个人配置'
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"清除用户配置失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


# =============================================
# 用户基本配置 API
# =============================================

@config_management_bp.route('/api/user/<int:user_id>/basic-info', methods=['GET'])
@login_required
@permission_required('config_management', 'view')
def get_user_basic_info(user_id):
    """获取用户基本信息"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': '用户不存在'}), 404

        # 获取AI配置
        employee_config = EmployeeSalaryConfig.query.filter_by(user_id=user_id).first()
        is_manager = False
        if employee_config and employee_config.grade:
            is_manager = employee_config.grade.grade_type == 'M'

        return jsonify({
            'success': True,
            'data': {
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'real_name': user.real_name,
                    'email': user.email,
                    'phone': user.phone,
                    'company_name': user.company_name,
                    'department': user.department,
                    'role': user.role,
                    'settlement_currency': user.settlement_currency,
                    'is_active': user.is_active,
                    'is_department_manager': user.is_department_manager,
                    'managed_department_ids': user.managed_department_ids
                },
                'ai_config': {
                    'enabled': employee_config.ai_analysis_enabled if employee_config else False
                },
                'is_manager': is_manager
            }
        })
    except Exception as e:
        logger.error(f"获取用户基本信息失败: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@config_management_bp.route('/api/user/<int:user_id>/ai-config', methods=['GET'])
@login_required
@permission_required('config_management', 'view')
def get_user_ai_config(user_id):
    """获取用户AI分析配置"""
    try:
        employee_config = EmployeeSalaryConfig.query.filter_by(user_id=user_id).first()
        is_manager = False
        if employee_config and employee_config.grade:
            is_manager = employee_config.grade.grade_type == 'M'

        return jsonify({
            'success': True,
            'data': {
                'enabled': employee_config.ai_analysis_enabled if employee_config else False,
                'is_manager': is_manager
            }
        })
    except Exception as e:
        logger.error(f"获取用户AI配置失败: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@config_management_bp.route('/api/user/<int:user_id>/ai-config', methods=['POST'])
@login_required
@permission_required('config_management', 'edit')
def save_user_ai_config(user_id):
    """保存用户AI分析配置"""
    try:
        data = request.get_json()
        employee_config = EmployeeSalaryConfig.query.filter_by(user_id=user_id).first()

        if not employee_config:
            # 如果没有配置记录，创建一个（year 是必填字段）
            from datetime import datetime
            employee_config = EmployeeSalaryConfig(user_id=user_id, year=datetime.now().year)
            db.session.add(employee_config)

        employee_config.ai_analysis_enabled = data.get('enabled', False)

        db.session.commit()
        return jsonify({'success': True, 'message': 'AI配置保存成功'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"保存用户AI配置失败: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================
# 绩效数据手工录入 API
# =============================================

@config_management_bp.route('/api/manual-entries/<int:user_id>/<int:year>')
@login_required
@permission_required('config_management', 'view')
def api_get_manual_entries(user_id, year):
    """获取用户某年所有手工录入数据（含附件URL）"""
    try:
        from app.models.performance_manual_entry import PerformanceManualEntry
        from app.models.performance_config import PerformanceMetricsDefinition, RolePerformanceItem

        entries = PerformanceManualEntry.query.filter_by(
            user_id=user_id, year=year
        ).all()

        # 获取该用户已配置的绩效指标
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404

        # 查找用户角色的绩效配置中包含的指标
        from app.models.performance_config import RolePerformanceConfig
        config = RolePerformanceConfig.query.filter_by(role=user.role, is_active=True).first()
        configured_codes = set()
        if config:
            items = RolePerformanceItem.query.filter_by(
                config_id=config.id, is_active=True
            ).all()
            configured_codes = {item.item_code for item in items}

        # 获取指标定义（只返回该用户已配置的）
        metrics = PerformanceMetricsDefinition.query.filter(
            PerformanceMetricsDefinition.is_active == True,
            PerformanceMetricsDefinition.metric_code.in_(configured_codes)
        ).all() if configured_codes else []

        return jsonify({
            'success': True,
            'data': {
                'entries': [e.to_dict() for e in entries],
                'metrics': [m.to_dict() for m in metrics],
                'user': {
                    'id': user.id,
                    'real_name': user.real_name or user.username,
                    'role': user.role,
                }
            }
        })
    except Exception as e:
        logger.error(f"获取手工录入数据失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@config_management_bp.route('/api/manual-entries/<int:user_id>/<int:year>', methods=['POST'])
@login_required
@permission_required('config_management', 'edit')
def api_save_manual_entries(user_id, year):
    """批量保存手工录入数据（UPSERT）"""
    try:
        from app.models.performance_manual_entry import PerformanceManualEntry
        data = request.get_json()
        entries_data = data.get('entries', [])

        saved_count = 0
        for item in entries_data:
            metric_code = item.get('metric_code')
            period_type = item.get('period_type')
            period = item.get('period')
            value = item.get('value')
            note = item.get('note', '')

            if not metric_code or not period_type or not period:
                continue

            # UPSERT
            entry = PerformanceManualEntry.query.filter_by(
                user_id=user_id,
                metric_code=metric_code,
                year=year,
                period_type=period_type,
                period=period
            ).first()

            if entry:
                entry.value = value
                entry.note = note
                entry.entered_by = current_user.id
                entry.updated_at = datetime.utcnow()
            else:
                entry = PerformanceManualEntry(
                    user_id=user_id,
                    metric_code=metric_code,
                    year=year,
                    period_type=period_type,
                    period=period,
                    value=value,
                    note=note,
                    entered_by=current_user.id,
                )
                db.session.add(entry)
            saved_count += 1

        db.session.commit()
        return jsonify({'success': True, 'message': f'已保存{saved_count}条数据'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"保存手工录入数据失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@config_management_bp.route('/api/manual-entries/upload', methods=['POST'])
@login_required
@permission_required('config_management', 'edit')
def api_upload_manual_attachment():
    """上传手工录入附件"""
    try:
        from app.models.performance_manual_entry import PerformanceManualEntry, PerformanceManualAttachment

        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '请选择文件'}), 400

        file = request.files['file']
        if not file.filename:
            return jsonify({'success': False, 'message': '文件名为空'}), 400

        entry_id = request.form.get('entry_id')
        if not entry_id:
            return jsonify({'success': False, 'message': '缺少录入记录ID'}), 400

        entry = PerformanceManualEntry.query.get(int(entry_id))
        if not entry:
            return jsonify({'success': False, 'message': '录入记录不存在'}), 404

        filename = file.filename
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)

        from app.utils.smart_storage_manager import get_smart_storage
        smart_storage = get_smart_storage()
        result = smart_storage.upload_file(
            object_id=entry_id,
            file=file,
            filename=filename,
            file_type='attachment',
            bucket_type='performance',
            business_type='performance_manual'
        )

        if not result:
            return jsonify({'success': False, 'message': '文件上传失败'}), 500

        attachment = PerformanceManualAttachment(
            entry_id=int(entry_id),
            filename=filename,
            storage_path=result.get('storage_path', ''),
            file_size=file_size,
            file_type=file_ext,
            uploaded_by=current_user.id,
        )
        db.session.add(attachment)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '附件上传成功',
            'data': attachment.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"上传手工录入附件失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@config_management_bp.route('/api/manual-entries/attachment/<int:attachment_id>', methods=['DELETE'])
@login_required
@permission_required('config_management', 'edit')
def api_delete_manual_attachment(attachment_id):
    """删除手工录入附件"""
    try:
        from app.models.performance_manual_entry import PerformanceManualAttachment

        attachment = PerformanceManualAttachment.query.get(attachment_id)
        if not attachment:
            return jsonify({'success': False, 'message': '附件不存在'}), 404

        db.session.delete(attachment)
        db.session.commit()
        return jsonify({'success': True, 'message': '附件已删除'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除附件失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500
