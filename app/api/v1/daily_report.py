# -*- coding: utf-8 -*-
"""
每日智能分析报告API

提供AI生成的每日业绩分析报告
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import date
import logging

logger = logging.getLogger(__name__)
daily_report_api = Blueprint('daily_report_api', __name__, url_prefix='/api/v1/daily-report')


@daily_report_api.route('/check', methods=['GET'])
@login_required
def check_report_status():
    """
    检查是否应该显示每日报告

    Returns:
        {
            'success': bool,
            'should_show': bool,      # 是否应该显示报告
            'has_cache': bool,        # 是否有有效缓存
            'api_available': bool,    # AI API是否可用
            'generating': bool        # 是否正在生成中
        }
    """
    from app.models.ai_analysis_cache import AIAnalysisCache, UserDailyLoginRecord
    from app.services.ai_analysis_service import AIAnalysisService
    from app.models.salary_config import EmployeeSalaryConfig

    try:
        user_id = current_user.id

        # 检查API是否可用
        api_available = AIAnalysisService.check_api_availability()
        if not api_available:
            return jsonify({
                'success': True,
                'should_show': False,
                'has_cache': False,
                'api_available': False,
                'generating': False,
                'reason': 'AI服务未配置'
            })

        # 检查用户是否启用了AI分析
        employee_config = EmployeeSalaryConfig.query.filter_by(user_id=user_id).first()
        ai_enabled = employee_config.ai_analysis_enabled if employee_config else False
        if not ai_enabled:
            return jsonify({
                'success': True,
                'should_show': False,
                'has_cache': False,
                'api_available': api_available,
                'generating': False,
                'reason': '用户未启用AI分析'
            })

        # 检查是否应该显示（用户是否勾选了今日不再显示）
        should_show = UserDailyLoginRecord.should_show_report(user_id)

        # 检查缓存状态
        cache = AIAnalysisCache.get_latest_analysis(user_id)
        has_cache = cache is not None and cache.status == 'success'
        generating = cache is not None and cache.status == 'generating'

        return jsonify({
            'success': True,
            'should_show': should_show,
            'has_cache': has_cache,
            'api_available': api_available,
            'generating': generating
        })

    except Exception as e:
        logger.error(f"检查报告状态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@daily_report_api.route('/generate', methods=['POST'])
@login_required
def generate_report():
    """
    生成或获取每日分析报告

    如果有有效缓存且数据未变化，返回缓存
    否则调用AI生成新报告
    """
    from app.services.ai_analysis_service import AIAnalysisService
    from app.models.ai_analysis_cache import UserDailyLoginRecord

    try:
        user_id = current_user.id
        data = request.get_json(silent=True) or {}
        year = data.get('year')
        force = data.get('force', False)

        # 记录今日登录
        UserDailyLoginRecord.record_login(user_id)

        # 检查API是否可用
        if not AIAnalysisService.check_api_availability():
            return jsonify({
                'success': False,
                'error': 'AI服务未配置，无法生成分析报告'
            })

        # 生成报告
        result = AIAnalysisService.generate_daily_report(user_id, year, force_regenerate=force)

        return jsonify(result)

    except Exception as e:
        logger.error(f"生成报告失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@daily_report_api.route('/dismiss', methods=['POST'])
@login_required
def dismiss_report():
    """
    用户关闭报告（今日不再显示）
    """
    from app.models.ai_analysis_cache import UserDailyLoginRecord

    try:
        user_id = current_user.id

        # 记录登录并标记为已关闭
        UserDailyLoginRecord.record_login(user_id)
        UserDailyLoginRecord.mark_report_dismissed(user_id)

        return jsonify({'success': True})

    except Exception as e:
        logger.error(f"关闭报告失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@daily_report_api.route('/regenerate', methods=['POST'])
@login_required
def regenerate_report():
    """
    强制重新生成报告（忽略缓存）
    """
    from app.services.ai_analysis_service import AIAnalysisService

    try:
        user_id = current_user.id
        data = request.get_json(silent=True) or {}
        year = data.get('year')

        # 检查API是否可用
        if not AIAnalysisService.check_api_availability():
            return jsonify({
                'success': False,
                'error': 'AI服务未配置，无法生成分析报告'
            })

        # 强制重新生成
        result = AIAnalysisService.generate_daily_report(user_id, year, force_regenerate=True)

        return jsonify(result)

    except Exception as e:
        logger.error(f"重新生成报告失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@daily_report_api.route('/mark-read', methods=['POST'])
@login_required
def mark_report_read():
    """
    标记报告为已读
    """
    from app.models.ai_analysis_cache import UserDailyLoginRecord

    try:
        user_id = current_user.id
        UserDailyLoginRecord.mark_report_read(user_id)
        return jsonify({'success': True})

    except Exception as e:
        logger.error(f"标记报告已读失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@daily_report_api.route('/status', methods=['GET'])
@login_required
def get_report_status():
    """
    获取报告状态（用于顶部图标显示）

    Returns:
        {
            'success': bool,
            'has_report': bool,      # 是否有可用的报告
            'is_read': bool,         # 是否已读
            'generating': bool       # 是否正在生成
        }
    """
    from app.models.ai_analysis_cache import AIAnalysisCache, UserDailyLoginRecord

    try:
        user_id = current_user.id

        # 检查是否有报告
        cache = AIAnalysisCache.get_latest_analysis(user_id)
        has_report = cache is not None and cache.status == 'success'
        generating = cache is not None and cache.status == 'generating'

        # 检查是否已读
        is_read = UserDailyLoginRecord.is_report_read(user_id)

        return jsonify({
            'success': True,
            'has_report': has_report,
            'is_read': is_read,
            'generating': generating
        })

    except Exception as e:
        logger.error(f"获取报告状态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@daily_report_api.route('/history', methods=['GET'])
@login_required
def get_report_history():
    """
    获取历史分析报告列表
    """
    from app.models.ai_analysis_cache import AIAnalysisCache

    try:
        user_id = current_user.id
        limit = request.args.get('limit', 10, type=int)

        reports = AIAnalysisCache.query.filter_by(
            user_id=user_id,
            analysis_type='daily_report',
            status='success'
        ).order_by(AIAnalysisCache.analysis_date.desc()).limit(limit).all()

        return jsonify({
            'success': True,
            'data': [{
                'date': r.analysis_date.isoformat(),
                'score': r.analysis_result.get('score') if r.analysis_result else None,
                'overall': r.analysis_result.get('overall') if r.analysis_result else None
            } for r in reports]
        })

    except Exception as e:
        logger.error(f"获取历史报告失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@daily_report_api.route('/team-info', methods=['GET'])
@login_required
def get_team_info():
    """
    获取M级用户的团队信息

    Returns:
        {
            'success': bool,
            'is_manager': bool,
            'team': {'id': int, 'name': str} or null,
            'members': [{'user_id': int, 'name': str, 'grade': str}]
        }
    """
    from app.services.ai_analysis_service import AIAnalysisService

    try:
        team_info = AIAnalysisService._get_user_team_info(current_user.id)
        return jsonify({'success': True, **team_info})

    except Exception as e:
        logger.error(f"获取团队信息失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@daily_report_api.route('/member/<int:member_id>/report', methods=['GET'])
@login_required
def get_member_report(member_id):
    """
    获取团队成员的分析报告

    只有团队负责人可以查看其团队成员的报告
    """
    from app.services.ai_analysis_service import AIAnalysisService
    from app.models.ai_analysis_cache import AIAnalysisCache

    try:
        # 验证当前用户是该成员的团队负责人
        team_info = AIAnalysisService._get_user_team_info(current_user.id)
        member_ids = [m['user_id'] for m in team_info.get('members', [])]

        if member_id not in member_ids:
            return jsonify({
                'success': False,
                'error': '无权查看该成员报告'
            }), 403

        # 获取成员最新报告
        cache = AIAnalysisCache.get_latest_analysis(member_id)
        if cache and cache.status == 'success':
            return jsonify({
                'success': True,
                'has_report': True,
                'data': cache.analysis_result,
                'date': cache.analysis_date.isoformat(),
                'score': cache.analysis_result.get('score') if cache.analysis_result else None
            })

        return jsonify({
            'success': True,
            'has_report': False,
            'generating': cache.status == 'generating' if cache else False
        })

    except Exception as e:
        logger.error(f"获取成员报告失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@daily_report_api.route('/member/<int:member_id>/generate', methods=['POST'])
@login_required
def generate_member_report(member_id):
    """
    为团队成员生成分析报告

    只有团队负责人可以为其团队成员生成报告
    """
    from app.services.ai_analysis_service import AIAnalysisService

    try:
        # 验证权限
        team_info = AIAnalysisService._get_user_team_info(current_user.id)
        member_ids = [m['user_id'] for m in team_info.get('members', [])]

        if member_id not in member_ids:
            return jsonify({
                'success': False,
                'error': '无权为该成员生成报告'
            }), 403

        # 为成员生成报告
        result = AIAnalysisService.generate_daily_report(member_id)
        return jsonify(result)

    except Exception as e:
        logger.error(f"生成成员报告失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@daily_report_api.route('/team-analysis/generate', methods=['POST'])
@login_required
def generate_team_analysis():
    """
    生成团队分析（M级管理者专用）

    分阶段生成：个人报告完成后，异步调用此接口生成团队分析
    """
    from app.services.ai_analysis_service import AIAnalysisService

    try:
        result = AIAnalysisService.generate_team_analysis(current_user.id)
        return jsonify(result)

    except Exception as e:
        logger.error(f"生成团队分析失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@daily_report_api.route('/team-analysis/status', methods=['GET'])
@login_required
def get_team_analysis_status():
    """
    获取团队分析状态

    Returns:
        {
            'success': bool,
            'status': 'pending' | 'completed',
            'data': {...} (仅当completed时)
        }
    """
    from app.models.ai_analysis_cache import AIAnalysisCache

    try:
        cache = AIAnalysisCache.get_latest_analysis(current_user.id)

        if cache and cache.analysis_result:
            team_analysis = cache.analysis_result.get('team_analysis')
            if team_analysis:
                return jsonify({
                    'success': True,
                    'status': 'completed',
                    'data': team_analysis
                })

        return jsonify({
            'success': True,
            'status': 'pending'
        })

    except Exception as e:
        logger.error(f"获取团队分析状态失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
