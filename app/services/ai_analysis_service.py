# -*- coding: utf-8 -*-
"""
AI分析服务

集成外部AI API（Claude 3.5 Sonnet）生成个性化分析报告
"""
import os
import json
import logging
import re
from datetime import date, datetime
from flask import current_app

logger = logging.getLogger(__name__)


class AIAnalysisService:
    """AI分析服务"""

    # 支持的AI提供商配置
    PROVIDERS = {
        'anthropic': {
            'api_key_env': 'ANTHROPIC_API_KEY',
            'default_model': 'claude-sonnet-4-20250514',
            'base_url': 'https://api.anthropic.com/v1'
        },
        'openai': {
            'api_key_env': 'OPENAI_API_KEY',
            'default_model': 'gpt-4o',
            'base_url': 'https://api.openai.com/v1'
        }
    }

    @classmethod
    def get_provider_config(cls):
        """获取AI提供商配置"""
        # 优先使用Anthropic（Claude）
        provider = os.environ.get('AI_PROVIDER', 'anthropic')
        if provider not in cls.PROVIDERS:
            provider = 'anthropic'

        config = cls.PROVIDERS[provider]
        api_key = os.environ.get(config['api_key_env'])

        return {
            'provider': provider,
            'api_key': api_key,
            'model': os.environ.get('AI_MODEL', config['default_model']),
            'base_url': config['base_url']
        }

    @classmethod
    def generate_daily_report(cls, user_id, year=None, force_regenerate=False):
        """
        生成每日分析报告

        Args:
            user_id: 用户ID
            year: 年份（默认当前年）
            force_regenerate: 是否强制重新生成

        Returns:
            dict: {
                'success': bool,
                'data': 分析结果,
                'cached': 是否使用缓存,
                'error': 错误信息
            }
        """
        from app.services.performance_dashboard_service import PerformanceDashboardService
        from app.models.ai_analysis_cache import AIAnalysisCache
        from app.models.user import User
        from app import db

        year = year or datetime.now().year
        today = date.today()

        # 1. 获取用户信息
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'error': '用户不存在'}

        # 2. 获取绩效数据
        try:
            dashboard_data = PerformanceDashboardService.get_dashboard_data(user_id, year)
            # 获取项目阶段统计
            project_stats = cls._get_project_statistics(user_id, year)
            dashboard_data['project_stages'] = project_stats
            # 获取本月数据和历史趋势
            monthly_trend = cls._get_monthly_trend_data(user_id, year)
            dashboard_data['monthly_trend'] = monthly_trend

            # 注意：团队分析已拆分为独立方法 generate_team_analysis()
            # 这里不再获取团队数据，避免超时问题

        except Exception as e:
            logger.error(f"获取绩效数据失败: {e}")
            return {'success': False, 'error': f'获取绩效数据失败: {str(e)}'}

        # 3. 计算数据哈希
        data_hash = AIAnalysisCache.calculate_data_hash(dashboard_data)

        # 4. 检查缓存是否有效
        if not force_regenerate:
            is_valid, cache = AIAnalysisCache.is_cache_valid(user_id, data_hash)
            if is_valid and cache:
                logger.info(f"使用缓存的分析报告: user_id={user_id}")
                return {
                    'success': True,
                    'data': cache.analysis_result,
                    'cached': True,
                    'cache_date': cache.analysis_date.isoformat()
                }

        # 5. 检查API配置
        config = cls.get_provider_config()
        if not config['api_key']:
            logger.warning(f"AI API密钥未配置: {config['provider']}")
            return {'success': False, 'error': 'AI服务未配置'}

        # 6. 创建或更新缓存记录
        cache = AIAnalysisCache.get_today_analysis(user_id)
        if not cache:
            cache = AIAnalysisCache(
                user_id=user_id,
                analysis_date=today,
                analysis_type='daily_report'
            )
            db.session.add(cache)

        cache.status = 'generating'
        cache.raw_data_snapshot = dashboard_data
        cache.data_hash = data_hash
        cache.ai_provider = config['provider']
        cache.ai_model = config['model']
        db.session.commit()

        # 7. 调用AI API生成分析
        try:
            analysis_result, tokens = cls._call_ai_api(user, dashboard_data, config)

            cache.analysis_result = analysis_result
            cache.status = 'success'
            cache.tokens_used = tokens
            cache.error_message = None
            db.session.commit()

            logger.info(f"AI分析生成成功: user_id={user_id}, tokens={tokens}")

            return {
                'success': True,
                'data': analysis_result,
                'cached': False
            }

        except Exception as e:
            logger.error(f"AI分析生成失败: {e}")
            cache.status = 'failed'
            cache.error_message = str(e)
            db.session.commit()

            return {
                'success': False,
                'error': f'AI分析生成失败: {str(e)}'
            }

    @classmethod
    def generate_team_analysis(cls, user_id, year=None):
        """
        生成团队分析（M级管理者专用）

        分阶段生成：
        1. 先通过 generate_daily_report() 生成个人分析
        2. 然后通过此方法异步生成团队分析
        """
        from app import db
        from app.models.user import User
        from app.models.ai_analysis_cache import AIAnalysisCache
        from datetime import datetime

        if year is None:
            year = datetime.now().year

        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'error': '用户不存在'}

        # 1. 检查是否为M级管理者
        team_info = cls._get_user_team_info(user_id)
        if not team_info.get('is_manager'):
            return {'success': False, 'error': '非M级管理者'}

        if not team_info.get('members'):
            return {'success': False, 'error': '无团队成员'}

        # 2. 获取团队汇总数据
        member_ids = [m['user_id'] for m in team_info['members']]
        team_data = cls._get_team_aggregate_data(member_ids, year)
        team_data['team_name'] = team_info.get('team', {}).get('name', '我的团队')

        # 3. 构建团队分析专用提示词
        prompt = cls._build_team_analysis_prompt(user, team_data)

        # 4. 获取AI配置
        config = cls.get_provider_config()
        if not config:
            return {'success': False, 'error': 'AI服务未配置'}

        # 5. 调用AI生成团队分析
        try:
            if config['provider'] == 'anthropic':
                team_analysis, tokens = cls._call_anthropic(config, prompt)
            else:
                team_analysis, tokens = cls._call_openai(config, prompt)

            # 6. 更新缓存中的team_analysis字段
            cache = AIAnalysisCache.get_latest_analysis(user_id)
            if cache and cache.analysis_result:
                cache.analysis_result['team_analysis'] = team_analysis
                db.session.commit()
                logger.info(f"团队分析生成成功: user_id={user_id}, tokens={tokens}")

            return {
                'success': True,
                'team_analysis': team_analysis
            }

        except Exception as e:
            logger.error(f"团队分析生成失败: {e}")
            return {
                'success': False,
                'error': f'团队分析生成失败: {str(e)}'
            }

    @classmethod
    def _build_team_analysis_prompt(cls, user, team_data):
        """构建团队分析专用提示词"""
        language = user.language_preference or 'zh'

        if language == 'zh':
            prompt = f"""你是一位资深销售管理顾问，请根据以下团队数据提供管理分析。

## 团队数据（{team_data.get('team_name', '我的团队')}，{team_data['member_count']}名成员）
- 团队植入额: 实际 {team_data['implant_amount']['actual']/10000:.2f}万 / 目标 {team_data['implant_amount']['target']/10000:.2f}万
- 团队销售额: 实际 {team_data['sales_amount']['actual']/10000:.2f}万 / 目标 {team_data['sales_amount']['target']/10000:.2f}万
- 团队新增客户: {team_data['new_customers']['actual']}个 (目标 {team_data['new_customers']['target']}个)
- 团队新增项目: {team_data['new_projects']['actual']}个 (目标 {team_data['new_projects']['target']}个)

## 输出要求
请以JSON格式输出团队分析，包含以下字段：
1. **team_performance** - 团队整体表现评价（2-3句话）
2. **top_performers** - 团队亮点（2-3条）
3. **areas_to_improve** - 需要改进的方面（1-2条）
4. **management_suggestions** - 给管理者的建议（2-3条）

## 输出格式
请直接输出JSON，不要有任何其他文字：
{{
    "team_performance": "团队整体表现评价",
    "top_performers": ["亮点1", "亮点2"],
    "areas_to_improve": ["改进点1"],
    "management_suggestions": ["管理建议1", "管理建议2"]
}}"""
        else:
            prompt = f"""You are a senior sales management consultant. Please provide management analysis based on the following team data.

## Team Data ({team_data.get('team_name', 'My Team')}, {team_data['member_count']} members)
- Team Implant Amount: Actual {team_data['implant_amount']['actual']/10000:.2f}K / Target {team_data['implant_amount']['target']/10000:.2f}K
- Team Sales Amount: Actual {team_data['sales_amount']['actual']/10000:.2f}K / Target {team_data['sales_amount']['target']/10000:.2f}K
- Team New Customers: {team_data['new_customers']['actual']} (Target: {team_data['new_customers']['target']})
- Team New Projects: {team_data['new_projects']['actual']} (Target: {team_data['new_projects']['target']})

## Output Requirements
Please output team analysis in JSON format with the following fields:
1. **team_performance** - Team overall performance (2-3 sentences)
2. **top_performers** - Team highlights (2-3 items)
3. **areas_to_improve** - Areas to improve (1-2 items)
4. **management_suggestions** - Management suggestions (2-3 items)

## Output Format
Please output JSON directly without any other text:
{{
    "team_performance": "Team overall performance evaluation",
    "top_performers": ["Highlight 1", "Highlight 2"],
    "areas_to_improve": ["Improvement area 1"],
    "management_suggestions": ["Management suggestion 1", "Management suggestion 2"]
}}"""

        return prompt

    @classmethod
    def _get_project_statistics(cls, user_id, year):
        """获取项目阶段统计"""
        from app.models.project import Project

        # 按阶段统计项目数
        stage_counts = {}
        stages = ['discover', 'embed', 'pre_tender', 'tendering', 'awarded', 'quoted', 'signed', 'lost', 'paused']

        for stage in stages:
            count = Project.query.filter(
                Project.owner_id == user_id,
                Project.current_stage == stage
            ).count()
            stage_counts[stage] = count

        # 五星项目数
        five_star_count = Project.query.filter(
            Project.owner_id == user_id,
            Project.rating == 5
        ).count()

        return {
            'stage_counts': stage_counts,
            'five_star_count': five_star_count,
            'total': sum(stage_counts.values())
        }

    @classmethod
    def _get_monthly_trend_data(cls, user_id, year):
        """获取本月数据、环比、同比趋势"""
        from app.services.performance_service import PerformanceService
        from datetime import datetime

        current_month = datetime.now().month
        last_year = year - 1

        # 获取当年和去年的月度数据
        current_year_stats = PerformanceService.get_yearly_statistics(user_id, year)
        last_year_stats = PerformanceService.get_yearly_statistics(user_id, last_year)

        def extract_month_data(stats_list, month_index):
            """从月度统计列表中提取指定月份数据"""
            if not stats_list or month_index < 0 or month_index >= len(stats_list):
                return {'implant': 0, 'sales': 0, 'customers': 0, 'projects': 0}
            s = stats_list[month_index]
            return {
                'implant': getattr(s, 'implant_amount_actual', 0) or 0,
                'sales': getattr(s, 'sales_amount_actual', 0) or 0,
                'customers': getattr(s, 'new_customers_actual', 0) or 0,
                'projects': getattr(s, 'new_projects_actual', 0) or 0
            }

        def calc_change_rate(current, previous):
            """计算变化率"""
            if previous == 0:
                return 100 if current > 0 else 0
            return round((current - previous) / previous * 100, 1)

        # 本月数据 (month_index = current_month - 1)
        this_month = extract_month_data(current_year_stats, current_month - 1)

        # 上月数据 (环比)
        if current_month > 1:
            last_month = extract_month_data(current_year_stats, current_month - 2)
        else:
            # 1月份，上月是去年12月
            last_month = extract_month_data(last_year_stats, 11)

        # 去年同月数据 (同比)
        same_month_last_year = extract_month_data(last_year_stats, current_month - 1)

        # 计算环比变化率
        mom_change = {
            'implant': calc_change_rate(this_month['implant'], last_month['implant']),
            'sales': calc_change_rate(this_month['sales'], last_month['sales']),
            'customers': calc_change_rate(this_month['customers'], last_month['customers']),
            'projects': calc_change_rate(this_month['projects'], last_month['projects'])
        }

        # 计算同比变化率
        yoy_change = {
            'implant': calc_change_rate(this_month['implant'], same_month_last_year['implant']),
            'sales': calc_change_rate(this_month['sales'], same_month_last_year['sales']),
            'customers': calc_change_rate(this_month['customers'], same_month_last_year['customers']),
            'projects': calc_change_rate(this_month['projects'], same_month_last_year['projects'])
        }

        # 最近3个月趋势
        recent_3_months = []
        for i in range(3):
            month_idx = current_month - 1 - i
            if month_idx >= 0:
                recent_3_months.append(extract_month_data(current_year_stats, month_idx))
            else:
                # 需要从去年数据获取
                recent_3_months.append(extract_month_data(last_year_stats, 12 + month_idx))

        return {
            'current_month': current_month,
            'this_month': this_month,
            'last_month': last_month,
            'same_month_last_year': same_month_last_year,
            'mom_change': mom_change,  # 环比
            'yoy_change': yoy_change,  # 同比
            'recent_3_months': recent_3_months  # 最近3个月趋势
        }

    @classmethod
    def _get_user_team_info(cls, user_id):
        """
        获取用户团队信息（含成员详情）

        用于M级管理者查看团队成员分析报告

        Returns:
            dict: {
                'is_manager': bool,  # 是否为M级管理者
                'team': {'id': int, 'name': str} or None,  # 团队信息
                'members': [{'user_id': int, 'name': str, 'grade': str}]  # 成员列表
            }
        """
        try:
            from app.models.salary_config import EmployeeSalaryConfig, SalesTeamConfig

            # 检查用户薪资配置
            employee_config = EmployeeSalaryConfig.query.filter_by(user_id=user_id).first()
            if not employee_config or not employee_config.grade:
                return {'is_manager': False, 'team': None, 'members': []}

            # 检查是否为M级
            is_manager = employee_config.grade.grade_type == 'M'
            if not is_manager:
                return {'is_manager': False, 'team': None, 'members': []}

            # 查找用户领导的团队
            team = SalesTeamConfig.query.filter_by(
                team_leader_id=user_id,
                is_active=True
            ).first()

            if not team:
                return {'is_manager': True, 'team': None, 'members': []}

            # 获取团队成员（排除自己）
            members = []
            for m in team.members:
                if m.user_id != user_id and m.user:
                    members.append({
                        'user_id': m.user_id,
                        'name': m.user.real_name or m.user.username,
                        'grade': m.grade.grade_code if m.grade else None
                    })

            return {
                'is_manager': True,
                'team': {'id': team.id, 'name': team.team_name},
                'members': members
            }

        except Exception as e:
            logger.error(f"获取用户团队信息失败: {e}")
            return {'is_manager': False, 'team': None, 'members': []}

    @classmethod
    def _get_team_aggregate_data(cls, team_member_ids, year):
        """
        汇总团队成员数据

        Args:
            team_member_ids: 团队成员用户ID列表
            year: 年份

        Returns:
            dict: 团队汇总数据
        """
        from app.services.performance_dashboard_service import PerformanceDashboardService

        team_data = {
            'implant_amount': {'actual': 0, 'target': 0},
            'sales_amount': {'actual': 0, 'target': 0},
            'new_customers': {'actual': 0, 'target': 0},
            'new_projects': {'actual': 0, 'target': 0},
            'member_count': len(team_member_ids),
            'members_summary': []
        }

        for member_id in team_member_ids:
            try:
                member_data = PerformanceDashboardService.get_dashboard_data(member_id, year)
                summary = member_data.get('summary', {})

                # 累加KPI
                for key in ['implant_amount', 'sales_amount', 'new_customers', 'new_projects']:
                    kpi = summary.get(key, {})
                    team_data[key]['actual'] += kpi.get('actual', 0) or 0
                    team_data[key]['target'] += kpi.get('target', 0) or 0

                # 记录成员简要
                team_data['members_summary'].append({
                    'user_id': member_id,
                    'implant': summary.get('implant_amount', {}).get('actual', 0) or 0,
                    'sales': summary.get('sales_amount', {}).get('actual', 0) or 0
                })
            except Exception as e:
                logger.error(f"获取成员{member_id}数据失败: {e}")

        return team_data

    @classmethod
    def _call_ai_api(cls, user, dashboard_data, config):
        """调用AI API"""
        # 构建提示词
        prompt = cls._build_prompt(user, dashboard_data)

        if config['provider'] == 'anthropic':
            return cls._call_anthropic(config, prompt)
        elif config['provider'] == 'openai':
            return cls._call_openai(config, prompt)
        else:
            raise ValueError(f"不支持的AI提供商: {config['provider']}")

    @classmethod
    def _build_prompt(cls, user, data):
        """构建AI提示词"""
        language = user.language_preference or 'zh'

        # 获取数据
        summary = data.get('summary', {})
        expense = data.get('expense_budget', {})
        activity = data.get('activity_score', {})
        project_stages = data.get('project_stages', {})
        stage_counts = project_stages.get('stage_counts', {})
        monthly_trend = data.get('monthly_trend', {})

        # 格式化数据
        def safe_get(d, *keys, default=0):
            for key in keys:
                if isinstance(d, dict):
                    d = d.get(key, default)
                else:
                    return default
            return d if d is not None else default

        if language == 'zh':
            prompt = f"""你是一位专业的业务分析师。请根据以下数据为用户生成一份全面的业绩分析报告。

## 用户信息
- 姓名: {user.real_name or user.username}
- 角色: {user.role}
- 部门: {user.department or '未设置'}

## 今年KPI数据（年度累计）
- 植入额: 实际 {safe_get(summary, 'implant_amount', 'actual')/10000:.2f}万 / 目标 {safe_get(summary, 'implant_amount', 'target')/10000:.2f}万 (完成率 {safe_get(summary, 'implant_amount', 'rate')}%)
- 销售额: 实际 {safe_get(summary, 'sales_amount', 'actual')/10000:.2f}万 / 目标 {safe_get(summary, 'sales_amount', 'target')/10000:.2f}万 (完成率 {safe_get(summary, 'sales_amount', 'rate')}%)
- 新增客户: {safe_get(summary, 'new_customers', 'actual')}个 (目标 {safe_get(summary, 'new_customers', 'target')}个, 完成率 {safe_get(summary, 'new_customers', 'rate')}%)
- 新增项目: {safe_get(summary, 'new_projects', 'actual')}个 (目标 {safe_get(summary, 'new_projects', 'target')}个, 完成率 {safe_get(summary, 'new_projects', 'rate')}%)

## 本月表现（{monthly_trend.get('current_month', 0)}月）
- 本月植入额: {safe_get(monthly_trend, 'this_month', 'implant', default=0)/10000:.2f}万
- 本月销售额: {safe_get(monthly_trend, 'this_month', 'sales', default=0)/10000:.2f}万
- 本月新增客户: {safe_get(monthly_trend, 'this_month', 'customers', default=0)}个
- 本月新增项目: {safe_get(monthly_trend, 'this_month', 'projects', default=0)}个

## 历史趋势对比
**环比（与上月对比）:**
- 植入额变化: {safe_get(monthly_trend, 'mom_change', 'implant', default=0):+.1f}%
- 销售额变化: {safe_get(monthly_trend, 'mom_change', 'sales', default=0):+.1f}%
- 新增客户变化: {safe_get(monthly_trend, 'mom_change', 'customers', default=0):+.1f}%
- 新增项目变化: {safe_get(monthly_trend, 'mom_change', 'projects', default=0):+.1f}%

**同比（与去年同月对比）:**
- 植入额变化: {safe_get(monthly_trend, 'yoy_change', 'implant', default=0):+.1f}%
- 销售额变化: {safe_get(monthly_trend, 'yoy_change', 'sales', default=0):+.1f}%
- 新增客户变化: {safe_get(monthly_trend, 'yoy_change', 'customers', default=0):+.1f}%
- 新增项目变化: {safe_get(monthly_trend, 'yoy_change', 'projects', default=0):+.1f}%

## 项目进展分析
- 各阶段项目数:
  - 发现(Discover): {stage_counts.get('discover', 0)}个
  - 植入(Embed): {stage_counts.get('embed', 0)}个
  - 预投标(Pre-tender): {stage_counts.get('pre_tender', 0)}个
  - 投标中(Tendering): {stage_counts.get('tendering', 0)}个
  - 中标(Awarded): {stage_counts.get('awarded', 0)}个
  - 已报价(Quoted): {stage_counts.get('quoted', 0)}个
  - 签约(Signed): {stage_counts.get('signed', 0)}个
  - 失败(Lost): {stage_counts.get('lost', 0)}个
  - 暂停(Paused): {stage_counts.get('paused', 0)}个
- 五星项目数: {project_stages.get('five_star_count', 0)}个
- 项目总数: {project_stages.get('total', 0)}个

## 费用支出分析
- 年度预算: {safe_get(expense, 'budget_total', default=0):.2f}元
- 已使用: {safe_get(expense, 'expense_total', default=0):.2f}元
- 使用率: {safe_get(expense, 'usage_rate', default=0)}%

## 活跃度评分
- 综合评分: {safe_get(activity, 'score', default=0)}分 (等级: {safe_get(activity, 'grade_text', default='未评定')})
- 行动记录数: {safe_get(activity, 'breakdown', 'action_count', 'value', default=0)}条
- 客户覆盖率: {safe_get(activity, 'breakdown', 'customer_coverage', 'value', default=0)}%

## 分析要求

请生成报告，重点关注本月表现和近期趋势，包含以下部分：

1. **overall** - 2-3句话总结当前业绩状态，重点评价本月表现和趋势变化

2. **kpi_highlights** - 2-3个业绩方面做得好的地方（优先突出本月亮点）

3. **monthly_focus** - 本月重点分析
   - performance: 本月表现评价（与年度目标进度是否匹配）
   - mom_trend: 环比趋势分析（上升/下降/持平，原因分析）
   - yoy_trend: 同比趋势分析（与去年同期对比）

4. **project_analysis** - 项目分析
   - funnel_health: 项目漏斗健康度评估
   - risk_projects: 需要关注的风险点
   - trend: 签约趋势判断

5. **expense_analysis** - 费用分析
   - efficiency: 费用效率评估
   - roi: 投入产出比
   - warnings: 超支风险提醒（如果有）

6. **improvements** - 3-5条具体可执行的改进建议，按优先级排序，要带量化指标

7. **next_month_forecast** - 基于当前趋势预测下月表现

8. **score** - 综合评分(1-100整数)

## 输出格式

请严格使用以下JSON格式返回，不要包含任何其他文字：

{{
    "overall": "整体评价文本",
    "kpi_highlights": ["亮点1", "亮点2"],
    "monthly_focus": {{
        "performance": "本月表现评价",
        "mom_trend": "环比趋势分析",
        "yoy_trend": "同比趋势分析"
    }},
    "project_analysis": {{
        "funnel_health": "漏斗健康度评估",
        "risk_projects": ["风险点1", "风险点2"],
        "trend": "签约趋势判断"
    }},
    "expense_analysis": {{
        "efficiency": "费用效率评估",
        "roi": "投入产出比分析",
        "warnings": ["预警信息"]
    }},
    "improvements": ["建议1", "建议2", "建议3"],
    "next_month_forecast": "下月预测",
    "score": 75
}}

## 注意事项
- 重点关注本月数据和近期趋势变化，给出针对性建议
- 建议要具体可执行，最好带数字（如"联系5位客户"而非"多联系客户"）
- 分析数据间的关联（如新客户少可能导致销售管道不足）
- 根据环比/同比变化判断业务走势，给出预警或鼓励
- 如果数据为0或缺失，给出相应的提醒"""

        else:
            # English version
            prompt = f"""You are a professional business analyst. Please generate a comprehensive performance analysis report based on the following data.

## User Information
- Name: {user.real_name or user.username}
- Role: {user.role}
- Department: {user.department or 'Not set'}

## This Year's KPI Data (Year-to-Date)
- Implant Amount: Actual {safe_get(summary, 'implant_amount', 'actual')/10000:.2f}K / Target {safe_get(summary, 'implant_amount', 'target')/10000:.2f}K ({safe_get(summary, 'implant_amount', 'rate')}% completion)
- Sales Amount: Actual {safe_get(summary, 'sales_amount', 'actual')/10000:.2f}K / Target {safe_get(summary, 'sales_amount', 'target')/10000:.2f}K ({safe_get(summary, 'sales_amount', 'rate')}% completion)
- New Customers: {safe_get(summary, 'new_customers', 'actual')} (Target: {safe_get(summary, 'new_customers', 'target')}, {safe_get(summary, 'new_customers', 'rate')}% completion)
- New Projects: {safe_get(summary, 'new_projects', 'actual')} (Target: {safe_get(summary, 'new_projects', 'target')}, {safe_get(summary, 'new_projects', 'rate')}% completion)

## This Month's Performance (Month {monthly_trend.get('current_month', 0)})
- Implant Amount: {safe_get(monthly_trend, 'this_month', 'implant', default=0)/10000:.2f}K
- Sales Amount: {safe_get(monthly_trend, 'this_month', 'sales', default=0)/10000:.2f}K
- New Customers: {safe_get(monthly_trend, 'this_month', 'customers', default=0)}
- New Projects: {safe_get(monthly_trend, 'this_month', 'projects', default=0)}

## Historical Trends
**Month-over-Month (vs Last Month):**
- Implant Amount: {safe_get(monthly_trend, 'mom_change', 'implant', default=0):+.1f}%
- Sales Amount: {safe_get(monthly_trend, 'mom_change', 'sales', default=0):+.1f}%
- New Customers: {safe_get(monthly_trend, 'mom_change', 'customers', default=0):+.1f}%
- New Projects: {safe_get(monthly_trend, 'mom_change', 'projects', default=0):+.1f}%

**Year-over-Year (vs Same Month Last Year):**
- Implant Amount: {safe_get(monthly_trend, 'yoy_change', 'implant', default=0):+.1f}%
- Sales Amount: {safe_get(monthly_trend, 'yoy_change', 'sales', default=0):+.1f}%
- New Customers: {safe_get(monthly_trend, 'yoy_change', 'customers', default=0):+.1f}%
- New Projects: {safe_get(monthly_trend, 'yoy_change', 'projects', default=0):+.1f}%

## Project Progress Analysis
- Projects by Stage:
  - Discover: {stage_counts.get('discover', 0)}
  - Embed: {stage_counts.get('embed', 0)}
  - Pre-tender: {stage_counts.get('pre_tender', 0)}
  - Tendering: {stage_counts.get('tendering', 0)}
  - Awarded: {stage_counts.get('awarded', 0)}
  - Quoted: {stage_counts.get('quoted', 0)}
  - Signed: {stage_counts.get('signed', 0)}
  - Lost: {stage_counts.get('lost', 0)}
  - Paused: {stage_counts.get('paused', 0)}
- Five-star Projects: {project_stages.get('five_star_count', 0)}
- Total Projects: {project_stages.get('total', 0)}

## Expense Analysis
- Annual Budget: {safe_get(expense, 'budget_total', default=0):.2f}
- Used: {safe_get(expense, 'expense_total', default=0):.2f}
- Usage Rate: {safe_get(expense, 'usage_rate', default=0)}%

## Activity Score
- Overall Score: {safe_get(activity, 'score', default=0)} (Grade: {safe_get(activity, 'grade', default='N/A')})
- Action Records: {safe_get(activity, 'breakdown', 'action_count', 'value', default=0)}
- Customer Coverage: {safe_get(activity, 'breakdown', 'customer_coverage', 'value', default=0)}%

## Analysis Requirements

Generate a report focusing on this month's performance and recent trends:

1. **overall** - 2-3 sentences summarizing current status, focusing on this month's performance and trend changes

2. **kpi_highlights** - 2-3 positive aspects of performance (prioritize this month's highlights)

3. **monthly_focus** - This month's analysis
   - performance: This month's performance evaluation (aligned with yearly target progress?)
   - mom_trend: Month-over-month trend analysis (up/down/flat, reason analysis)
   - yoy_trend: Year-over-year trend analysis (vs same period last year)

4. **project_analysis** - Project analysis
   - funnel_health: Project funnel health assessment
   - risk_projects: Risk points to watch
   - trend: Signing trend analysis

5. **expense_analysis** - Expense analysis
   - efficiency: Expense efficiency evaluation
   - roi: Return on investment
   - warnings: Overspending warnings (if any)

6. **improvements** - 3-5 specific actionable suggestions, prioritized, with metrics

7. **next_month_forecast** - Next month prediction based on current trends

8. **score** - Overall score (integer 1-100)

## Output Format

Return ONLY valid JSON in this format, no other text:

{{
    "overall": "Overall assessment text",
    "kpi_highlights": ["Highlight 1", "Highlight 2"],
    "monthly_focus": {{
        "performance": "This month's performance evaluation",
        "mom_trend": "Month-over-month trend analysis",
        "yoy_trend": "Year-over-year trend analysis"
    }},
    "project_analysis": {{
        "funnel_health": "Funnel health assessment",
        "risk_projects": ["Risk 1", "Risk 2"],
        "trend": "Trend analysis"
    }},
    "expense_analysis": {{
        "efficiency": "Efficiency evaluation",
        "roi": "ROI analysis",
        "warnings": ["Warning"]
    }},
    "improvements": ["Suggestion 1", "Suggestion 2", "Suggestion 3"],
    "next_month_forecast": "Next month forecast",
    "score": 75
}}"""

        # 注意：团队分析已拆分为独立方法 _build_team_analysis_prompt()
        # 这里不再添加团队数据，避免超时问题

        return prompt

    @classmethod
    def _call_anthropic(cls, config, prompt):
        """调用Anthropic Claude API"""
        import requests

        headers = {
            'x-api-key': config['api_key'],
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }

        payload = {
            'model': config['model'],
            'max_tokens': 1500,
            'messages': [
                {'role': 'user', 'content': prompt}
            ]
        }

        logger.info(f"调用 Anthropic API: model={config['model']}")

        response = requests.post(
            f'{config["base_url"]}/messages',
            headers=headers,
            json=payload,
            timeout=30
        )

        # 检查响应状态，提供更详细的错误信息
        if response.status_code != 200:
            error_text = response.text
            try:
                error_json = response.json()
                error_message = error_json.get('error', {}).get('message', error_text)
            except:
                error_message = error_text

            logger.error(f"Anthropic API 错误: status={response.status_code}, message={error_message}")
            raise ValueError(f"AI API 错误 ({response.status_code}): {error_message}")

        result = response.json()

        # 检查响应格式
        if 'content' not in result or not result['content']:
            logger.error(f"Anthropic API 响应格式异常: {result}")
            raise ValueError("AI API 返回了空响应")

        content = result['content'][0]['text']
        tokens = result.get('usage', {}).get('input_tokens', 0) + result.get('usage', {}).get('output_tokens', 0)

        logger.info(f"Anthropic API 调用成功: tokens={tokens}")

        # 提取JSON
        json_data = cls._extract_json(content)
        return json_data, tokens

    @classmethod
    def _call_openai(cls, config, prompt):
        """调用OpenAI API"""
        import requests

        headers = {
            'Authorization': f'Bearer {config["api_key"]}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': config['model'],
            'messages': [
                {'role': 'system', 'content': 'You are a professional business analyst. Always respond with valid JSON only, no markdown formatting.'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.7,
            'max_tokens': 1500,
            'response_format': {'type': 'json_object'}
        }

        response = requests.post(
            f'{config["base_url"]}/chat/completions',
            headers=headers,
            json=payload,
            timeout=30
        )

        response.raise_for_status()
        result = response.json()

        content = result['choices'][0]['message']['content']
        tokens = result.get('usage', {}).get('total_tokens', 0)

        return json.loads(content), tokens

    @classmethod
    def _extract_json(cls, content):
        """从响应中提取JSON"""
        # 尝试直接解析
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # 尝试从markdown代码块中提取
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试找到第一个{到最后一个}
        start = content.find('{')
        end = content.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(content[start:end+1])
            except json.JSONDecodeError:
                pass

        raise ValueError("无法从AI响应中提取有效的JSON")

    @classmethod
    def check_api_availability(cls):
        """检查API是否可用"""
        config = cls.get_provider_config()
        return bool(config['api_key'])
