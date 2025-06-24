from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, date
from app import db
from app.models.performance import PerformanceTarget, PerformanceStatistics, FiveStarProjectBaseline
from app.models.user import User
from app.services.performance_service import PerformanceService
from app.services.exchange_rate_service import exchange_rate_service
from app.utils.permissions import get_accessible_users

import json

performance_bp = Blueprint('performance', __name__, url_prefix='/performance')


@performance_bp.route('/')
@login_required
def index():
    """绩效统计首页"""
    try:
        current_year = datetime.now().year
        
        # 获取可访问的用户列表（基于权限）
        accessible_users = get_accessible_users(current_user)
        
        # 默认查看当前用户的数据
        selected_user_id = request.args.get('user_id', current_user.id, type=int)
        
        # 检查用户是否有权限查看选定用户的数据
        if selected_user_id not in [u.id for u in accessible_users]:
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
        
        # 准备图表数据
        chart_data = {
            'months': [f'{m}月' for m in range(1, 13)],
            'implant_actual': [],
            'implant_target': [],
            'sales_actual': [],
            'sales_target': [],
            'customers_actual': [],
            'customers_target': [],
            'projects_actual': [],
            'projects_target': [],
            'five_star_actual': [],
            'five_star_target': []
        }
        
        # 汇总当年累计数据
        total_actual = {
            'implant': 0, 'sales': 0, 'customers': 0, 'projects': 0, 'five_star': 0
        }
        total_target = {
            'implant': 0, 'sales': 0, 'customers': 0, 'projects': 0, 'five_star': 0
        }
        
        for month in range(1, 13):
            stats = yearly_stats[month - 1] if yearly_stats and len(yearly_stats) > month - 1 else None
            target = yearly_targets.get(month)
            
            # 处理实际值
            if stats:
                implant_actual = stats.implant_amount_actual or 0
                sales_actual = stats.sales_amount_actual or 0
                
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
                chart_data['customers_actual'].append(stats.new_customers_actual or 0)
                chart_data['projects_actual'].append(stats.new_projects_actual or 0)
                chart_data['five_star_actual'].append(stats.five_star_projects_actual or 0)
                
                # 累计实际值
                total_actual['implant'] += implant_actual
                total_actual['sales'] += sales_actual
                total_actual['customers'] += stats.new_customers_actual or 0
                total_actual['projects'] += stats.new_projects_actual or 0
                total_actual['five_star'] += stats.five_star_projects_actual or 0
            else:
                chart_data['implant_actual'].append(0)
                chart_data['sales_actual'].append(0)
                chart_data['customers_actual'].append(0)
                chart_data['projects_actual'].append(0)
                chart_data['five_star_actual'].append(0)
            
            # 处理目标值
            if target:
                implant_target = target.implant_amount_target or 0
                sales_target = target.sales_amount_target or 0
                
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
                
                chart_data['implant_target'].append(round(implant_target, 2))
                chart_data['sales_target'].append(round(sales_target, 2))
                chart_data['customers_target'].append(target.new_customers_target or 0)
                chart_data['projects_target'].append(target.new_projects_target or 0)
                chart_data['five_star_target'].append(target.five_star_projects_target or 0)
                
                # 累计目标值
                total_target['implant'] += implant_target
                total_target['sales'] += sales_target
                total_target['customers'] += target.new_customers_target or 0
                total_target['projects'] += target.new_projects_target or 0
                total_target['five_star'] += target.five_star_projects_target or 0
            else:
                chart_data['implant_target'].append(0)
                chart_data['sales_target'].append(0)
                chart_data['customers_target'].append(0)
                chart_data['projects_target'].append(0)
                chart_data['five_star_target'].append(0)
        
        # 计算年度达成率
        achievement_rates = {}
        for key in total_actual:
            achievement_rates[key] = PerformanceService.get_achievement_rate(
                total_actual[key], total_target[key]
            )
        
        # 获取行业统计（当年累计）
        industry_summary = PerformanceService.calculate_industry_statistics(selected_user_id, current_year)
        
        # 获取月度行业统计
        monthly_industry_stats = PerformanceService.get_monthly_industry_statistics(selected_user_id, current_year)
        
        return render_template('performance/index.html',
                             selected_user=selected_user,
                             accessible_users=accessible_users,
                             current_year=current_year,
                             current_month=datetime.now().month,
                             chart_data=chart_data,
                             total_actual=total_actual,
                             total_target=total_target,
                             achievement_rates=achievement_rates,
                             industry_summary=industry_summary,
                             monthly_industry_stats=monthly_industry_stats,
                             display_currency=display_currency,
                             yearly_stats=yearly_stats,
                             yearly_targets=yearly_targets)
    
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
            accessible_users = get_accessible_users(current_user)
            selected_user_id = request.args.get('user_id', current_user.id, type=int)
            selected_user = User.query.get(selected_user_id) or current_user
            
            # 返回空白的绩效页面，允许用户手动刷新数据
            return render_template('performance/index.html',
                                 selected_user=selected_user,
                                 accessible_users=accessible_users,
                                 current_year=datetime.now().year,
                                 current_month=datetime.now().month,
                                 chart_data={'months': [f'{m}月' for m in range(1, 13)],
                                           'implant_actual': [0]*12, 'implant_target': [0]*12,
                                           'sales_actual': [0]*12, 'sales_target': [0]*12,
                                           'customers_actual': [0]*12, 'customers_target': [0]*12,
                                           'projects_actual': [0]*12, 'projects_target': [0]*12,
                                           'five_star_actual': [0]*12, 'five_star_target': [0]*12},
                                 total_actual={'implant': 0, 'sales': 0, 'customers': 0, 'projects': 0, 'five_star': 0},
                                 total_target={'implant': 0, 'sales': 0, 'customers': 0, 'projects': 0, 'five_star': 0},
                                 achievement_rates={'implant': 0, 'sales': 0, 'customers': 0, 'projects': 0, 'five_star': 0},
                                 industry_summary={},
                                 monthly_industry_stats={},
                                 display_currency='CNY',
                                 yearly_stats=[],
                                 yearly_targets={})
        except Exception as fallback_error:
            print(f"回退视图也失败: {fallback_error}")
            return redirect(url_for('main.index'))


@performance_bp.route('/target_settings')
@login_required
def target_settings():
    """绩效目标设置页面"""
    try:
        # 获取可管理的用户列表
        if current_user.role == 'admin':
            manageable_users = User.query.filter(User.is_active == True).all()
        else:
            # 非管理员只能设置自己的目标
            manageable_users = [current_user]
        
        selected_user_id = request.args.get('user_id', current_user.id, type=int)
        
        # 检查权限
        if selected_user_id not in [u.id for u in manageable_users]:
            selected_user_id = current_user.id
        
        selected_user = User.query.get(selected_user_id)
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # 获取当前年度的目标设置
        targets = {}
        for month in range(1, 13):
            target = PerformanceTarget.query.filter_by(
                user_id=selected_user_id, year=current_year, month=month
            ).first()
            targets[month] = target
        
        # 获取货币选项（参考报价单的货币选择范围）
        currency_options = [
            {'code': 'CNY', 'name': '人民币'},
            {'code': 'USD', 'name': '美元'},
            {'code': 'EUR', 'name': '欧元'},
            {'code': 'JPY', 'name': '日元'},
            {'code': 'GBP', 'name': '英镑'},
        ]
        
        return render_template('performance/target_settings.html',
                             selected_user=selected_user,
                             manageable_users=manageable_users,
                             current_year=current_year,
                             current_month=current_month,
                             targets=targets,
                             currency_options=currency_options)
    
    except Exception as e:
        flash(f'加载目标设置页面失败: {str(e)}', 'error')
        return redirect(url_for('main.index'))


@performance_bp.route('/save_target', methods=['POST'])
@login_required
def save_target():
    """保存绩效目标"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        year = data.get('year')
        month = data.get('month')
        
        # 权限检查
        if current_user.role != 'admin' and user_id != current_user.id:
            return jsonify({'success': False, 'message': '没有权限设置其他用户的目标'})
        
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
        accessible_users = get_accessible_users(current_user)
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


@performance_bp.route('/api/monthly_data')
@login_required
def api_monthly_data():
    """获取月度绩效数据API"""
    try:
        user_id = request.args.get('user_id', current_user.id, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', datetime.now().month, type=int)
        
        # 权限检查
        accessible_users = get_accessible_users(current_user)
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