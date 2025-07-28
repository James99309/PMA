from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from flask_babel import get_locale
from datetime import datetime, date
from app import db
from app.models.performance import PerformanceTarget, PerformanceStatistics, FiveStarProjectBaseline
from app.models.user import User
from app.services.performance_service import PerformanceService
from app.services.exchange_rate_service import exchange_rate_service
from app.utils.permissions import get_accessible_users
from app.permissions import permission_required

import json

performance_bp = Blueprint('performance', __name__, url_prefix='/performance')


@performance_bp.route('/')
@login_required
@permission_required('performance_management', 'view')
def index():
    """绩效管理首页"""
    try:
        current_year = datetime.now().year
        current_tab = request.args.get('tab', 'overview')
        
        # 获取可访问的用户列表（基于权限）
        accessible_users = get_accessible_users(current_user, 'performance_management')
        
        # 获取有绩效目标设置的用户列表
        users_with_targets = db.session.query(User).join(
            PerformanceTarget, User.id == PerformanceTarget.user_id
        ).filter(
            User.id.in_([u.id for u in accessible_users])
        ).distinct().all()
        
        # 获取有绩效数据的年份列表
        available_years = db.session.query(PerformanceTarget.year).filter(
            PerformanceTarget.user_id.in_([u.id for u in accessible_users])
        ).distinct().order_by(PerformanceTarget.year.desc()).all()
        available_years = [year[0] for year in available_years]
        
        # 获取当前筛选年份，默认为当年
        current_year = request.args.get('year', datetime.now().year, type=int)
        
        # 确保年份数据存在，如果当年没有数据但其他年份有数据，使用最近的年份
        if current_year not in available_years and available_years:
            # 优先使用当年，如果当年没有数据则使用最近的年份
            if datetime.now().year in available_years:
                current_year = datetime.now().year
            else:
                current_year = available_years[0]  # 使用最近的年份
        elif not available_years:
            # 如果没有任何年份数据，使用当年
            current_year = datetime.now().year
        
        # 默认查看当前用户的数据（绩效看板以个人数据为主）
        selected_user_id = request.args.get('user_id', current_user.id, type=int)
        
        # 检查用户是否有权限查看选定用户的数据，无权限时回退到查看自己的数据
        if selected_user_id and selected_user_id not in [u.id for u in accessible_users]:
            selected_user_id = current_user.id
        
        selected_user = User.query.get(selected_user_id)
        if not selected_user:
            flash('用户不存在', 'error')
            return redirect(url_for('performance.index'))
        
        # 获取年度统计数据
        yearly_stats = PerformanceService.get_yearly_statistics(selected_user_id, current_year)
        
        # 获取年度目标数据
        yearly_targets = {}
        for month in range(1, 13):
            target = PerformanceTarget.query.filter_by(
                user_id=selected_user_id, year=current_year, month=month
            ).first()
            yearly_targets[month] = target
        
        # 获取用户显示货币设置（从最近的目标记录中获取）
        display_currency = 'CNY'
        recent_target = PerformanceTarget.query.filter_by(
            user_id=selected_user_id
        ).order_by(PerformanceTarget.updated_at.desc()).first()
        if recent_target:
            display_currency = recent_target.display_currency
        
        # 准备简化的数据（移除图表相关数据）
        chart_data = {
            'months': [f'{m}月' for m in range(1, 13)],
            'implant_actual': [],
            'sales_actual': []
        }
        
        # 汇总当年累计数据
        total_actual = {
            'implant': 0.0, 'sales': 0.0, 'customers': 0, 'projects': 0, 'five_star': 0
        }
        total_target = {
            'implant': 0.0, 'sales': 0.0, 'customers': 0, 'projects': 0, 'five_star': 0
        }
        
        for month in range(1, 13):
            stats = yearly_stats[month - 1] if yearly_stats and len(yearly_stats) > month - 1 else None
            target = yearly_targets.get(month)
            
            # 处理实际值
            if stats:
                implant_actual = float(stats.implant_amount_actual or 0)
                sales_actual = float(stats.sales_amount_actual or 0)
                
                # 货币转换（如果需要）
                if display_currency != 'CNY':
                    try:
                        implant_actual = exchange_rate_service.convert_amount(
                            implant_actual, 'CNY', display_currency
                        )
                        sales_actual = exchange_rate_service.convert_amount(
                            sales_actual, 'CNY', display_currency
                        )
                    except Exception:
                        pass  # 转换失败时保持原值
                
                chart_data['implant_actual'].append(round(implant_actual, 2))
                chart_data['sales_actual'].append(round(sales_actual, 2))
                
                # 累计实际值
                total_actual['implant'] += float(implant_actual)
                total_actual['sales'] += float(sales_actual)
                total_actual['customers'] += int(stats.new_customers_actual or 0)
                total_actual['projects'] += int(stats.new_projects_actual or 0)
                total_actual['five_star'] += int(stats.five_star_projects_actual or 0)
            else:
                chart_data['implant_actual'].append(0)
                chart_data['sales_actual'].append(0)
            
            # 处理目标值
            if target:
                implant_target = float(target.implant_amount_target or 0)
                sales_target = float(target.sales_amount_target or 0)
                
                # 货币转换（如果需要）
                if display_currency != 'CNY':
                    try:
                        implant_target = exchange_rate_service.convert_amount(
                            implant_target, 'CNY', display_currency
                        )
                        sales_target = exchange_rate_service.convert_amount(
                            sales_target, 'CNY', display_currency
                        )
                    except Exception:
                        pass  # 转换失败时保持原值
                
                # 累计目标值
                total_target['implant'] += float(implant_target)
                total_target['sales'] += float(sales_target)
                total_target['customers'] += int(target.new_customers_target or 0)
                total_target['projects'] += int(target.new_projects_target or 0)
                total_target['five_star'] += int(target.five_star_projects_target or 0)
        
        # 计算年度达成率
        achievement_rates = {}
        for key in total_actual:
            achievement_rates[key] = PerformanceService.get_achievement_rate(
                total_actual[key], total_target[key]
            )
        
        # 计算每月的达成率
        monthly_rates = {}
        for month in range(1, 13):
            stats = yearly_stats[month - 1] if yearly_stats and len(yearly_stats) > month - 1 else None
            target = yearly_targets.get(month)
            
            monthly_rates[month] = {}
            if stats and target:
                monthly_rates[month]['implant'] = PerformanceService.get_achievement_rate(
                    stats.implant_amount_actual or 0, target.implant_amount_target or 0
                )
                monthly_rates[month]['sales'] = PerformanceService.get_achievement_rate(
                    stats.sales_amount_actual or 0, target.sales_amount_target or 0
                )
                monthly_rates[month]['customers'] = PerformanceService.get_achievement_rate(
                    stats.new_customers_actual or 0, target.new_customers_target or 0
                )
                monthly_rates[month]['projects'] = PerformanceService.get_achievement_rate(
                    stats.new_projects_actual or 0, target.new_projects_target or 0
                )
                monthly_rates[month]['five_star'] = PerformanceService.get_achievement_rate(
                    stats.five_star_projects_actual or 0, target.five_star_projects_target or 0
                )
            else:
                monthly_rates[month] = {'implant': 0.0, 'sales': 0.0, 'customers': 0.0, 'projects': 0.0, 'five_star': 0.0}
        
        # 获取行业统计（当年累计）
        industry_summary = PerformanceService.calculate_industry_statistics(selected_user_id, current_year)
        
        # 获取月度行业统计
        monthly_industry_stats = PerformanceService.get_monthly_industry_statistics(selected_user_id, current_year)
        
        # 检测语言环境，用于金额显示格式化
        from flask import session, g
        try:
            current_language = getattr(g, 'current_language', 'zh') or session.get('language', 'zh')
        except:
            current_language = 'zh'
        is_english = current_language == 'en'
        
        # 根据语言环境格式化金额显示
        if is_english:
            # 英文环境：M (百万)
            implant_title = 'Implantation (M)'
            sales_title = 'Sales (M)'
            implant_value = round(total_actual['implant'] / 1000000, 2)
            implant_amount = round(total_target['implant'] / 1000000, 2)
            sales_value = round(total_actual['sales'] / 1000000, 2)
            sales_amount = round(total_target['sales'] / 1000000, 2)
            amount_unit = 'M'
            target_text = 'Target'
        else:
            # 中文环境：万元
            implant_title = '植入额(万元)'
            sales_title = '销售额(万元)'
            implant_value = round(total_actual['implant'] / 10000, 2)
            implant_amount = round(total_target['implant'] / 10000, 2)
            sales_value = round(total_actual['sales'] / 10000, 2)
            sales_amount = round(total_target['sales'] / 10000, 2)
            amount_unit = '万元'
            target_text = '目标'
        
        # 构建通用组件配置
        list_config = {
            'module_name': 'performance',
            'title': '绩效管理',
            'ajax_mode': True,
            
            # 统计卡片配置
            'stats': {
                'cards': [
                    {
                        'id': 'implant',
                        'title': implant_title,
                        'icon': 'fas fa-tooth',
                        'value': implant_value,
                        'amount': implant_amount,
                        'unit': amount_unit,
                        'amount_unit': target_text,
                        'color': 'primary',
                        'clickable': True,
                        'click_params': {'metric': 'implant'},
                        'data_key': 'implant'
                    },
                    {
                        'id': 'sales',
                        'title': sales_title,
                        'icon': 'fas fa-dollar-sign',
                        'value': sales_value,
                        'amount': sales_amount,
                        'unit': amount_unit,
                        'amount_unit': target_text,
                        'color': 'success',
                        'clickable': True,
                        'click_params': {'metric': 'sales'},
                        'data_key': 'sales'
                    },
                    {
                        'id': 'customers',
                        'title': 'New Customers' if is_english else '新增客户',
                        'icon': 'fas fa-users',
                        'value': total_actual['customers'],
                        'amount': total_target['customers'],
                        'unit': 'Count' if is_english else '个',
                        'amount_unit': target_text,
                        'color': 'info',
                        'clickable': True,
                        'click_params': {'metric': 'customers'},
                        'data_key': 'customers'
                    },
                    {
                        'id': 'projects',
                        'title': 'New Projects' if is_english else '新增项目',
                        'icon': 'fas fa-project-diagram',
                        'value': total_actual['projects'],
                        'amount': total_target['projects'],
                        'unit': 'Count' if is_english else '个',
                        'amount_unit': target_text,
                        'color': 'warning',
                        'clickable': True,
                        'click_params': {'metric': 'projects'},
                        'data_key': 'projects'
                    }
                ]
            },
            
            # 筛选配置
            'filter': {
                'action_url': url_for('performance.index'),
                'form_id': 'performanceFilterForm',
                'reset_url': url_for('performance.index'),
                
                'search_field': {
                    'name': 'search',
                    'label': '搜索',
                    'placeholder': '项目名称或客户名称',
                    'value': request.args.get('search', ''),
                    'col_width': 4
                },
                
                'filter_fields': [
                    {
                        'name': 'user_id',
                        'label': '账户',
                        'all_option_text': '全部账户',
                        'current_value': str(selected_user_id),  # 使用已计算的默认用户ID
                        'col_width': 3,
                        'options': [
                            {'value': str(user.id), 'label': user.real_name or user.username, 'translate': False}
                            for user in users_with_targets
                        ]
                    },
                    {
                        'name': 'year',
                        'label': '年份',
                        'all_option_text': '全部年份',
                        'current_value': str(current_year),  # 使用已计算的默认年份
                        'col_width': 3,
                        'options': [
                            {'value': str(year), 'label': f'{year}年', 'translate': False}
                            for year in available_years
                        ]
                    }
                ],
                
                'search_button_text': '搜索',
                'reset_button_text': '重置'
            },
            
            # 表格配置
            'table': {
                'ajax_target': 'performanceTableBody',
                'title': '绩效统计',
                'icon': 'fas fa-chart-bar',
                'show_header': True,
                'columns': [
                    {
                        'key': 'month',
                        'label': '月份',
                        'type': 'text',
                        'width': '80px'
                    },
                    {
                        'key': 'implant_actual',
                        'label': '植入额',
                        'type': 'text',
                        'align': 'end',
                        'width': '120px'
                    },
                    {
                        'key': 'implant_target',
                        'label': '植入目标',
                        'type': 'text',
                        'align': 'end',
                        'width': '120px'
                    },
                    {
                        'key': 'implant_rate',
                        'label': '达成率',
                        'type': 'text',
                        'align': 'center',
                        'width': '80px'
                    },
                    {
                        'key': 'sales_actual',
                        'label': '销售额',
                        'type': 'text',
                        'align': 'end',
                        'width': '120px'
                    },
                    {
                        'key': 'sales_target',
                        'label': '销售目标',
                        'type': 'text',
                        'align': 'end',
                        'width': '120px'
                    },
                    {
                        'key': 'sales_rate',
                        'label': '达成率',
                        'type': 'text',
                        'align': 'center',
                        'width': '80px'
                    },
                    {
                        'key': 'customers_actual',
                        'label': '新增用户',
                        'type': 'number',
                        'align': 'end',
                        'width': '90px'
                    },
                    {
                        'key': 'projects_actual',
                        'label': '新增项目',
                        'type': 'number',
                        'align': 'end',
                        'width': '90px'
                    }
                ]
            }
        }
        
        return render_template('performance/index.html',
                             selected_user=selected_user,
                             accessible_users=accessible_users,
                             users_with_targets=users_with_targets,
                             available_years=available_years,
                             current_year=current_year,
                             current_month=datetime.now().month,
                             current_tab=current_tab,
                             chart_data=chart_data,
                             total_actual=total_actual,
                             total_target=total_target,
                             achievement_rates=achievement_rates,
                             monthly_rates=monthly_rates,
                             industry_summary=industry_summary,
                             monthly_industry_stats=monthly_industry_stats,
                             display_currency=display_currency,
                             yearly_stats=yearly_stats,
                             yearly_targets=yearly_targets,
                             list_config=list_config)
    
    except Exception as e:
        # 回滚任何未完成的事务
        db.session.rollback()
        
        # 记录详细错误信息
        import traceback
        print(f"绩效数据加载错误: {str(e)}")
        print(f"错误堆栈: {traceback.format_exc()}")
        
        flash(f'加载绩效数据失败: {str(e)}', 'error')
        
        # 尝试回退到基本视图
        try:
            # 获取基本用户信息
            accessible_users = get_accessible_users(current_user, 'performance_management')
            selected_user_id = request.args.get('user_id', current_user.id, type=int)
            selected_user = User.query.get(selected_user_id) or current_user
            
            # 返回空白的绩效页面，允许用户手动刷新数据
            return render_template('performance/index.html',
                                 selected_user=selected_user,
                                 accessible_users=accessible_users,
                                 current_year=datetime.now().year,
                                 current_month=datetime.now().month,
                                 current_tab='overview',
                                 chart_data={'months': [f'{m}月' for m in range(1, 13)],
                                           'implant_actual': [0]*12,
                                           'sales_actual': [0]*12},
                                 total_actual={'implant': 0, 'sales': 0, 'customers': 0, 'projects': 0, 'five_star': 0},
                                 total_target={'implant': 0, 'sales': 0, 'customers': 0, 'projects': 0, 'five_star': 0},
                                 achievement_rates={'implant': 0, 'sales': 0, 'customers': 0, 'projects': 0, 'five_star': 0},
                                 monthly_rates={},
                                 industry_summary={},
                                 monthly_industry_stats={},
                                 display_currency='CNY',
                                 yearly_stats=[],
                                 yearly_targets={},
                                 list_config=None)
        except Exception as fallback_error:
            print(f"回退视图也失败: {fallback_error}")
            return redirect(url_for('main.index'))


@performance_bp.route('/target_settings')
@login_required
@permission_required('performance_management', 'edit')
def target_settings():
    """绩效目标设置页面"""
    try:
        # 获取可管理的用户列表 - 基于数据访问权限
        accessible_users = get_accessible_users(current_user, 'performance_management')
        accessible_user_ids = [u.id for u in accessible_users]
        
        # 调试信息
        print(f"当前用户: {current_user.username} (ID: {current_user.id})")
        print(f"可访问用户ID列表: {accessible_user_ids}")
        print(f"可访问用户: {[f'{u.real_name or u.username}({u.id})' for u in accessible_users]}")
        
        # 设置可选年份范围（2025-2030）
        available_years = list(range(2025, 2031))  # 2025到2030年
        current_year = datetime.now().year
        
        selected_user_id = request.args.get('user_id', current_user.id, type=int)
        selected_year = request.args.get('year', current_year, type=int)
        
        print(f"请求的用户ID: {selected_user_id}")
        print(f"请求的年份: {selected_year}")
        
        # 检查权限：只能查看有权限访问的用户
        if selected_user_id not in accessible_user_ids:
            print(f"用户ID {selected_user_id} 不在可访问列表中")
            
            # 如果是管理员，允许访问所有活跃用户
            if current_user.role == 'admin':
                selected_user = User.query.filter(User.id == selected_user_id, User._is_active == True).first()
                if selected_user:
                    print(f"管理员权限：允许访问用户 {selected_user.username} (ID: {selected_user_id})")
                    # 将该用户添加到可访问列表中
                    accessible_users.append(selected_user)
                    accessible_user_ids.append(selected_user_id)
                else:
                    print(f"用户ID {selected_user_id} 不存在或已禁用，重置为当前用户ID {current_user.id}")
                    selected_user_id = current_user.id
            else:
                print(f"非管理员用户，重置为当前用户ID {current_user.id}")
                selected_user_id = current_user.id
        else:
            print(f"用户ID {selected_user_id} 访问权限验证通过")
        
        # 检查是否有编辑权限
        can_edit_targets = (
            current_user.role == 'admin' or 
            (current_user.has_permission('user_management', 'edit') and selected_user_id in [u.id for u in accessible_users])
        )
        
        selected_user = User.query.get(selected_user_id)
        
        if not selected_user:
            print(f"错误：找不到用户ID {selected_user_id}")
            flash(f'找不到指定用户 (ID: {selected_user_id})', 'error')
            return redirect(url_for('performance.target_settings', user_id=current_user.id))
        
        print(f"成功获取用户: {selected_user.real_name or selected_user.username} (ID: {selected_user.id})")
        
        # 获取当前年度的目标设置
        targets = {}
        targets_found = 0
        for month in range(1, 13):
            target = PerformanceTarget.query.filter_by(
                user_id=selected_user_id, year=selected_year, month=month
            ).first()
            targets[month] = target
            if target:
                targets_found += 1
        
        print(f"用户 {selected_user.username} 在 {selected_year} 年已设置 {targets_found}/12 个月的目标")
        
        # 获取合格值数据（从任一现有记录中获取，因为所有月份的合格值应该一致）
        rate_values = None
        for target in targets.values():
            if target and (target.implant_rate or target.sales_rate or target.customers_rate or target.projects_rate):
                rate_values = target
                break
        
        print(f"合格值数据: {rate_values.implant_rate if rate_values else '无'}, {rate_values.sales_rate if rate_values else '无'}, {rate_values.customers_rate if rate_values else '无'}, {rate_values.projects_rate if rate_values else '无'}")
        
        # 为管理员获取所有用户选项
        if current_user.role == 'admin':
            all_active_users = User.query.filter(User._is_active == True).order_by(User.real_name, User.username).all()
            user_options = [
                {'value': str(user.id), 'label': user.real_name or user.username, 'translate': False}
                for user in all_active_users
            ]
            print(f"管理员权限：筛选器包含 {len(all_active_users)} 个用户选项")
        else:
            user_options = [
                {'value': str(user.id), 'label': user.real_name or user.username, 'translate': False}
                for user in accessible_users
            ]
            print(f"普通用户权限：筛选器包含 {len(accessible_users)} 个用户选项")
        
        # 构建筛选配置
        filter_config = {
            'action_url': url_for('performance.target_settings'),
            'form_id': 'targetFilterForm',
            'reset_url': url_for('performance.target_settings'),
            'show_search': False,  # 不显示搜索框
            'show_buttons': False,  # 不显示搜索和重置按钮
            
            'filter_fields': [
                {
                    'name': 'user_id',
                    'label': '账户',
                    'all_option_text': '请选择账户',
                    'current_value': selected_user_id,
                    'col_width': 6,
                    'options': user_options
                },
                {
                    'name': 'year',
                    'label': '年份',
                    'all_option_text': '请选择年份',
                    'current_value': selected_year,
                    'col_width': 6,
                    'options': [
                        {'value': str(year), 'label': f'{year}年', 'translate': False}
                        for year in available_years
                    ]
                }
            ]
        }
        
        return render_template('performance/target_settings.html',
                             selected_user=selected_user,
                             accessible_users=accessible_users,
                             available_years=available_years,
                             selected_year=selected_year,
                             current_month=datetime.now().month,
                             targets=targets,
                             rate_values=rate_values,
                             can_edit_targets=can_edit_targets,
                             filter_config=filter_config)
    
    except Exception as e:
        flash(f'加载目标设置页面失败: {str(e)}', 'error')
        return redirect(url_for('main.index'))


@performance_bp.route('/save_targets_batch', methods=['POST'])
@login_required
@permission_required('performance_management', 'edit')
def save_targets_batch():
    """批量保存绩效目标"""
    try:
        print(f"💾 保存目标请求 - 用户: {current_user.username} (ID: {current_user.id})")
        print(f"💾 请求方法: {request.method}")
        print(f"💾 Content-Type: {request.content_type}")
        
        data = request.get_json()
        print(f"💾 接收到的数据: {data}")
        
        if not data:
            print("❌ 无法解析JSON数据")
            return jsonify({'success': False, 'message': '无法解析请求数据'})
        
        targets_data = data.get('targets', [])
        print(f"💾 目标数据数量: {len(targets_data)}")
        
        if not targets_data:
            print("❌ 没有提供目标数据")
            return jsonify({'success': False, 'message': '没有提供目标数据'})
        
        # 权限检查
        accessible_users = get_accessible_users(current_user, 'performance_management')
        accessible_user_ids = [u.id for u in accessible_users]
        print(f"💾 可访问用户ID列表: {accessible_user_ids}")
        print(f"💾 当前用户角色: {current_user.role}")
        
        # 检查所有用户权限
        for target_data in targets_data:
            user_id = target_data.get('user_id')
            print(f"💾 检查用户ID {user_id} 的权限")
            
            can_edit = (
                current_user.role == 'admin' or 
                (current_user.has_permission('user_management', 'edit') and user_id in accessible_user_ids)
            )
            
            print(f"💾 用户ID {user_id} 权限检查结果: {can_edit}")
            
            if not can_edit:
                print(f"❌ 没有权限设置用户ID {user_id} 的绩效目标")
                return jsonify({'success': False, 'message': f'没有权限设置用户ID {user_id} 的绩效目标'})
        
        # 批量保存
        saved_count = 0
        for target_data in targets_data:
            user_id = target_data.get('user_id')
            year = target_data.get('year')
            month = target_data.get('month')
            
            # 查找或创建目标记录
            target = PerformanceTarget.query.filter_by(
                user_id=user_id, year=year, month=month
            ).first()
            
            if not target:
                target = PerformanceTarget(
                    user_id=user_id,
                    year=year,
                    month=month,
                    created_by=current_user.id
                )
                db.session.add(target)
            
            # 更新修改者信息
            target.updated_by = current_user.id
            
            # 更新目标数据
            target.implant_amount_target = target_data.get('implant_amount_target', 0)
            target.sales_amount_target = target_data.get('sales_amount_target', 0)
            target.new_customers_target = target_data.get('new_customers_target', 0)
            target.new_projects_target = target_data.get('new_projects_target', 0)
            target.five_star_projects_target = target_data.get('five_star_projects_target', 0)
            
            # 更新合格值数据
            target.implant_rate = target_data.get('implant_rate', 0)
            target.sales_rate = target_data.get('sales_rate', 0)
            target.customers_rate = target_data.get('customers_rate', 0)
            target.projects_rate = target_data.get('projects_rate', 0)
            
            target.display_currency = 'CNY'  # 默认人民币
            
            print(f"💾 保存月份 {month} 的数据 - 植入目标: {target.implant_amount_target}")
            
            saved_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'成功保存 {saved_count} 条目标设置'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'})


@performance_bp.route('/save_target', methods=['POST'])
@login_required
def save_target():
    """保存绩效目标（单个）"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        year = data.get('year')
        month = data.get('month')
        
        # 权限检查：只有管理员或具备用户管理编辑权限的用户可以设置目标
        accessible_users = get_accessible_users(current_user, 'performance_management')
        accessible_user_ids = [u.id for u in accessible_users]
        
        can_edit = (
            current_user.role == 'admin' or 
            (current_user.has_permission('user_management', 'edit') and user_id in accessible_user_ids)
        )
        
        if not can_edit:
            return jsonify({'success': False, 'message': '没有权限设置绩效目标'})
        
        # 查找或创建目标记录
        target = PerformanceTarget.query.filter_by(
            user_id=user_id, year=year, month=month
        ).first()
        
        if not target:
            target = PerformanceTarget(
                user_id=user_id,
                year=year,
                month=month,
                created_by=current_user.id
            )
            db.session.add(target)
        
        # 更新修改者信息
        target.updated_by = current_user.id
        
        # 更新目标数据
        target.implant_amount_target = data.get('implant_amount_target', 0)
        target.sales_amount_target = data.get('sales_amount_target', 0)
        target.new_customers_target = data.get('new_customers_target', 0)
        target.new_projects_target = data.get('new_projects_target', 0)
        target.five_star_projects_target = data.get('five_star_projects_target', 0)
        target.display_currency = data.get('display_currency', 'CNY')
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': '目标设置已保存'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'})


@performance_bp.route('/refresh_statistics')
@login_required
def refresh_statistics():
    """刷新统计数据"""
    try:
        user_id = request.args.get('user_id', current_user.id, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        
        # 权限检查
        accessible_users = get_accessible_users(current_user, 'performance_management')
        if user_id not in [u.id for u in accessible_users]:
            return jsonify({'success': False, 'message': '没有权限访问该用户数据'})
        
        # 刷新统计数据
        success = PerformanceService.refresh_all_statistics(user_id, year)
        
        if success:
            return jsonify({'success': True, 'message': '统计数据已刷新'})
        else:
            return jsonify({'success': False, 'message': '刷新统计数据失败'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'刷新失败: {str(e)}'})


@performance_bp.route('/list_ajax')
@login_required
@permission_required('performance_management', 'view')
def list_ajax():
    """绩效管理列表AJAX端点"""
    try:
        # 获取参数
        user_id_param = request.args.get('user_id', '')
        year_param = request.args.get('year', '')
        search = request.args.get('search', '')
        tab = request.args.get('tab', 'overview')
        
        # 处理筛选参数
        user_id = int(user_id_param) if user_id_param else None
        year = int(year_param) if year_param else None
        
        # 权限检查
        accessible_users = get_accessible_users(current_user, 'performance_management')
        accessible_user_ids = [u.id for u in accessible_users]
        
        # 处理"全部账户"和"全部年份"的情况
        if user_id and user_id not in accessible_user_ids:
            return jsonify({'success': False, 'message': '没有权限访问该用户数据'})
        
        # 获取有绩效目标的用户和年份
        targets_query = db.session.query(PerformanceTarget).filter(
            PerformanceTarget.user_id.in_(accessible_user_ids)
        )
        
        if user_id:
            targets_query = targets_query.filter(PerformanceTarget.user_id == user_id)
        if year:
            targets_query = targets_query.filter(PerformanceTarget.year == year)
        
        targets = targets_query.all()
        
        if not targets:
            return jsonify({
                'success': True,
                'html': '<tr><td colspan="9" class="text-center py-4">暂无绩效目标设置</td></tr>',
                'total_count': 0,
                'loaded_count': 0,
                'statistics': {'implant': 0, 'implant_amount': 0, 'sales': 0, 'sales_amount': 0, 'customers': 0, 'customers_amount': 0, 'projects': 0, 'projects_amount': 0}
            })
        
        # 构建HTML数据
        html_rows = []
        total_actual = {'implant': 0.0, 'sales': 0.0, 'customers': 0, 'projects': 0}
        total_target = {'implant': 0.0, 'sales': 0.0, 'customers': 0, 'projects': 0}
        
        # 简化逻辑：目前只支持特定用户特定年份的查询
        if not user_id or not year:
            return jsonify({
                'success': True,
                'html': '<tr><td colspan="9" class="text-center py-4">请选择具体的账户和年份查看数据</td></tr>',
                'total_count': 0,
                'loaded_count': 0,
                'statistics': {'implant': 0, 'implant_amount': 0, 'sales': 0, 'sales_amount': 0, 'customers': 0, 'customers_amount': 0, 'projects': 0, 'projects_amount': 0}
            })
        
        # 获取年度统计数据
        yearly_stats = PerformanceService.get_yearly_statistics(user_id, year)
        yearly_targets = {}
        for m in range(1, 13):
            target = PerformanceTarget.query.filter_by(
                user_id=user_id, year=year, month=m
            ).first()
            yearly_targets[m] = target
        
        # 获取当前月份，用于判断哪些月份还未开始
        from datetime import datetime
        current_date = datetime.now()
        current_month = current_date.month
        current_year_actual = current_date.year
        
        # 显示12个月的数据
        for m in range(1, 13):
            stats = yearly_stats[m - 1] if yearly_stats and len(yearly_stats) > m - 1 else None
            target = yearly_targets.get(m)
            
            # 判断是否是未开始的月份（只对当前年份判断）
            is_future_month = (year == current_year_actual and m > current_month)
            
            if stats:
                implant_actual = float(stats.implant_amount_actual or 0)
                sales_actual = float(stats.sales_amount_actual or 0)
                customers_actual = int(stats.new_customers_actual or 0)
                projects_actual = int(stats.new_projects_actual or 0)
                
                # 只有已开始的月份才累加到总数中
                if not is_future_month:
                    total_actual['implant'] += implant_actual
                    total_actual['sales'] += sales_actual
                    total_actual['customers'] += customers_actual
                    total_actual['projects'] += projects_actual
            else:
                implant_actual = sales_actual = customers_actual = projects_actual = 0
            
            if target:
                implant_target = float(target.implant_amount_target or 0)
                sales_target = float(target.sales_amount_target or 0)
                
                total_target['implant'] += implant_target
                total_target['sales'] += sales_target
                total_target['customers'] += int(target.new_customers_target or 0)
                total_target['projects'] += int(target.new_projects_target or 0)
            else:
                implant_target = sales_target = 0
            
            # 计算各指标达成率（带颜色判断，未开始月份显示为"-"）
            implant_rate = "-"
            sales_rate = "-"
            
            if not is_future_month:
                # 只对已开始的月份计算达成率
                if implant_target > 0:
                    rate_value = int((implant_actual / implant_target) * 100)
                    # 获取合格值用于颜色判断
                    implant_qualifying_rate = target.implant_rate if target else None
                    if implant_qualifying_rate and implant_qualifying_rate > 0:
                        # 有设置合格值，根据达成率与合格值比较设置颜色
                        color_class = "text-success" if rate_value >= implant_qualifying_rate else "text-danger"
                        implant_rate = f'<span class="{color_class}">{rate_value}%</span>'
                    else:
                        # 没有设置合格值，使用正常黑色
                        implant_rate = f"{rate_value}%"
                
                if sales_target > 0:
                    rate_value = int((sales_actual / sales_target) * 100)
                    # 获取合格值用于颜色判断
                    sales_qualifying_rate = target.sales_rate if target else None
                    if sales_qualifying_rate and sales_qualifying_rate > 0:
                        # 有设置合格值，根据达成率与合格值比较设置颜色
                        color_class = "text-success" if rate_value >= sales_qualifying_rate else "text-danger"
                        sales_rate = f'<span class="{color_class}">{rate_value}%</span>'
                    else:
                        # 没有设置合格值，使用正常黑色
                        sales_rate = f"{rate_value}%"
            
            # 格式化金额显示（根据语言显示单位）
            from flask import session, g
            
            # 检测语言环境，与应用其他部分保持一致
            try:
                current_language = getattr(g, 'current_language', 'zh') or session.get('language', 'zh')
            except:
                current_language = 'zh'
            is_english = current_language == 'en'
            
            # 格式化金额显示（未开始的月份显示为"-"）
            if is_future_month:
                # 未开始的月份显示为"-"
                implant_actual_display = "-"
                sales_actual_display = "-"
                if implant_target > 0:
                    if is_english:
                        implant_target_display = f"¥{implant_target / 1000000:.2f}M"
                    else:
                        implant_target_display = f"¥{implant_target / 10000:.2f}万元"
                else:
                    implant_target_display = "-"
                    
                if sales_target > 0:
                    if is_english:
                        sales_target_display = f"¥{sales_target / 1000000:.2f}M"
                    else:
                        sales_target_display = f"¥{sales_target / 10000:.2f}万元"
                else:
                    sales_target_display = "-"
            elif is_english:
                # 英文环境：元转换为百万（M），1M = 1,000,000元
                implant_actual_display = f"¥{implant_actual / 1000000:.2f}M"
                sales_actual_display = f"¥{sales_actual / 1000000:.2f}M"
                
                if implant_target > 0:
                    implant_target_display = f"¥{implant_target / 1000000:.2f}M"
                else:
                    implant_target_display = "-"
                    
                if sales_target > 0:
                    sales_target_display = f"¥{sales_target / 1000000:.2f}M"
                else:
                    sales_target_display = "-"
            else:
                # 中文环境：显示万元
                implant_actual_display = f"¥{implant_actual / 10000:.2f}万元"
                sales_actual_display = f"¥{sales_actual / 10000:.2f}万元"
                
                if implant_target > 0:
                    implant_target_display = f"¥{implant_target / 10000:.2f}万元"
                else:
                    implant_target_display = "-"
                    
                if sales_target > 0:
                    sales_target_display = f"¥{sales_target / 10000:.2f}万元"
                else:
                    sales_target_display = "-"
            
            # 添加当前月份的底纹样式（使用更深的灰色背景）
            row_class = 'bg-secondary bg-opacity-25' if (year == current_year_actual and m == current_month) else ''
            
            # 处理新增客户和新增项目的显示（未开始月份显示为"-"）
            customers_display = "-" if is_future_month else str(customers_actual)
            projects_display = "-" if is_future_month else str(projects_actual)
            
            html_row = f'''
            <tr class="{row_class}">
                <td>{m}月</td>
                <td class="text-end">{implant_actual_display}</td>
                <td class="text-end">{implant_target_display}</td>
                <td class="text-center">{implant_rate}</td>
                <td class="text-end">{sales_actual_display}</td>
                <td class="text-end">{sales_target_display}</td>
                <td class="text-center">{sales_rate}</td>
                <td class="text-end">{customers_display}</td>
                <td class="text-end">{projects_display}</td>
            </tr>
            '''
            html_rows.append(html_row)
        
        # 计算统计数据用于更新卡片（与主页面的语言环境一致）
        # 使用data-list.js期望的扁平化格式
        if is_english:
            # 英文环境：使用百万（M）
            statistics = {
                'implant': round(total_actual['implant'] / 1000000, 2),
                'implant_amount': round(total_target['implant'] / 1000000, 2),
                'sales': round(total_actual['sales'] / 1000000, 2),
                'sales_amount': round(total_target['sales'] / 1000000, 2),
                'customers': total_actual['customers'],
                'customers_amount': total_target['customers'],
                'projects': total_actual['projects'],
                'projects_amount': total_target['projects']
            }
        else:
            # 中文环境：使用万元
            statistics = {
                'implant': round(total_actual['implant'] / 10000, 2),
                'implant_amount': round(total_target['implant'] / 10000, 2),
                'sales': round(total_actual['sales'] / 10000, 2),
                'sales_amount': round(total_target['sales'] / 10000, 2),
                'customers': total_actual['customers'],
                'customers_amount': total_target['customers'],
                'projects': total_actual['projects'],
                'projects_amount': total_target['projects']
            }
        
        return jsonify({
            'success': True,
            'html': '\n'.join(html_rows),
            'total_count': len(html_rows),
            'loaded_count': len(html_rows),
            'statistics': statistics
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'数据加载失败: {str(e)}'})


@performance_bp.route('/api/monthly_data')
@login_required
def api_monthly_data():
    """获取月度绩效数据API"""
    try:
        user_id = request.args.get('user_id', current_user.id, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', datetime.now().month, type=int)
        
        # 权限检查
        accessible_users = get_accessible_users(current_user, 'performance_management')
        if user_id not in [u.id for u in accessible_users]:
            return jsonify({'success': False, 'message': '没有权限访问该用户数据'})
        
        # 获取统计数据
        stats = PerformanceStatistics.query.filter_by(
            user_id=user_id, year=year, month=month
        ).first()
        
        if not stats:
            stats = PerformanceService.calculate_monthly_statistics(user_id, year, month)
        
        # 获取目标数据
        target = PerformanceTarget.query.filter_by(
            user_id=user_id, year=year, month=month
        ).first()
        
        # 组装返回数据
        result = {
            'success': True,
            'data': {
                'actual': {
                    'implant_amount': stats.implant_amount_actual if stats else 0,
                    'sales_amount': stats.sales_amount_actual if stats else 0,
                    'new_customers': stats.new_customers_actual if stats else 0,
                    'new_projects': stats.new_projects_actual if stats else 0,
                    'five_star_projects': stats.five_star_projects_actual if stats else 0
                },
                'target': {
                    'implant_amount': target.implant_amount_target if target else 0,
                    'sales_amount': target.sales_amount_target if target else 0,
                    'new_customers': target.new_customers_target if target else 0,
                    'new_projects': target.new_projects_target if target else 0,
                    'five_star_projects': target.five_star_projects_target if target else 0
                },
                'industry_statistics': stats.industry_statistics if stats else {}
            }
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取数据失败: {str(e)}'}) 