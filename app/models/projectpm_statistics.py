from app import db
from app.models.project import Project
from app.models.projectpm_stage_history import ProjectStageHistory
from app.utils.access_control import get_viewable_data
from sqlalchemy import func, cast, String, and_, or_, not_, desc, distinct
from datetime import datetime, timedelta
from flask_login import current_user
import logging
import json

logger = logging.getLogger(__name__)

# 主线阶段定义
MAINLINE_STAGES = [
    '发现', '品牌植入', '招标前', '投标中', '中标'
]

# 阶段颜色定义
STAGE_COLORS = {
    '发现': '#8FD14F',       # 淡绿色
    '品牌植入': '#9370DB',   # 淡紫色
    '招标前': '#FFA500',     # 橘黄色
    '投标中': '#FF4500',     # 橘红色
    '中标': '#1E90FF',       # 蓝色
    '签约': '#228B22',       # 深绿色
    '失败': '#FF0000',       # 红色
    '搁置': '#AAAAAA',       # 淡灰色
    '未设置': '#CCCCCC'      # 灰色
}

# 排序顺序
STAGE_ORDER = ['发现', '品牌植入', '招标前', '投标中', '中标', '签约', '失败', '搁置', '未设置']

class ProjectStatistics:
    """项目统计模型"""
    
    @staticmethod
    def get_project_statistics(user=None, period='all', account_id=None):
        """
        获取项目统计数据（新版逻辑）
        
        Args:
            user: 用户对象，用于数据权限过滤
            period: 周期类型 'all', 'week', 'month'
            account_id: 账户ID，用于按账户过滤统计数据
            
        Returns:
            dict: 统计数据字典
        """
        target_user = user or current_user
        try:
            query = get_viewable_data(Project, target_user)
            # 只统计有授权编码的项目
            query = query.filter(Project.authorization_code.isnot(None), func.length(Project.authorization_code) > 0)
            if account_id:
                query = query.filter(Project.owner_id == account_id)
            all_projects = query.all()

            # 有效项目：主线阶段
            valid_stages = MAINLINE_STAGES
            valid_projects = [p for p in all_projects if (p.current_stage in valid_stages)]
            stats = {}
            stats['total_valid_projects'] = len(valid_projects)
            stats['total_valid_amount'] = sum(p.quotation_customer or 0 for p in valid_projects)

            # 各阶段项目数量
            default_stages = MAINLINE_STAGES + ['签约', '失败', '搁置', '未设置']
            stage_counts = {stage: 0 for stage in default_stages}
            for p in all_projects:
                stage = p.current_stage or '未设置'
                if stage in stage_counts:
                    stage_counts[stage] += 1
                else:
                    stage_counts[stage] = 1
            stats['stage_counts'] = stage_counts

            # 各阶段金额
            stage_amounts = {stage: 0 for stage in default_stages}
            for p in all_projects:
                stage = p.current_stage or '未设置'
                amount = p.quotation_customer or 0
                if stage in stage_amounts:
                    stage_amounts[stage] += amount
                else:
                    stage_amounts[stage] = amount
            stats['stage_amounts'] = stage_amounts

            # 投标中项目统计
            bidding_projects = [p for p in all_projects if p.current_stage == '投标中']
            stats['bidding_projects_count'] = len(bidding_projects)
            stats['bidding_projects_amount'] = sum(p.quotation_customer or 0 for p in bidding_projects)

            # 中标项目统计
            won_projects = [p for p in all_projects if p.current_stage == '中标']
            stats['won_projects_count'] = len(won_projects)
            stats['won_projects_amount'] = sum(p.quotation_customer or 0 for p in won_projects)

            # 业务推进统计（本月/本周主线阶段变更，且不含切换到失败/搁置）
            today = datetime.now().date()
            if period == 'week':
                start_date = today - timedelta(days=today.weekday())
            elif period == 'month':
                start_date = today.replace(day=1)
            else:
                start_date = None

            def is_mainline_change(project):
                # 只统计主线阶段变更，且不统计切换到失败/搁置
                if not project.stage_description:
                    return False
                # 查找本期内的主线阶段变更记录
                import re
                pattern = re.compile(r'\[阶段变更\][^\n]*?([\u4e00-\u9fa5A-Za-z0-9_]+) ?(?:→|-) ?([\u4e00-\u9fa5A-Za-z0-9_]+).*?时间: (\d{4}-\d{2}-\d{2})')
                matches = list(pattern.finditer(project.stage_description))
                for m in matches:
                    from_stage, to_stage, change_date = m.group(1), m.group(2), m.group(3)
                    try:
                        change_dt = datetime.strptime(change_date, '%Y-%m-%d').date()
                    except Exception:
                        continue
                    if start_date and change_dt < start_date:
                        continue
                    # 只统计主线阶段变更且目标阶段不是失败/搁置
                    if from_stage in MAINLINE_STAGES and to_stage in MAINLINE_STAGES and to_stage not in ['失败', '搁置']:
                        return True
                return False

            if period in ['week', 'month']:
                updated_projects = [p for p in all_projects if is_mainline_change(p)]
                stats['updated_projects_count'] = len(updated_projects)
                stats['updated_projects_amount'] = sum(p.quotation_customer or 0 for p in updated_projects)
            else:
                stats['updated_projects_count'] = 0
                stats['updated_projects_amount'] = 0

            # 新建项目统计（本期新建且有授权编码且主线阶段）
            if period in ['week', 'month'] and start_date:
                new_projects = [p for p in all_projects if p.created_at and p.created_at.date() >= start_date and p.current_stage in MAINLINE_STAGES]
                stats['new_projects_count'] = len(new_projects)
                stats['new_projects_amount'] = sum(p.quotation_customer or 0 for p in new_projects)
            else:
                stats['new_projects_count'] = 0
                stats['new_projects_amount'] = 0

            # 金额四舍五入
            for key in stats:
                if 'amount' in key and isinstance(stats[key], (int, float)):
                    stats[key] = round(stats[key], 2)
            for stage in stats['stage_amounts']:
                stats['stage_amounts'][stage] = round(stats['stage_amounts'][stage], 2)
            return stats
        except Exception as e:
            logger.error(f"生成项目统计数据出错: {str(e)}", exc_info=True)
            # 返回空统计数据
            default_stages = MAINLINE_STAGES + ['签约', '失败', '搁置', '未设置']
            return {
                'total_valid_projects': 0,
                'total_valid_amount': 0,
                'stage_counts': {stage: 0 for stage in default_stages},
                'stage_amounts': {stage: 0 for stage in default_stages},
                'new_projects_count': 0,
                'new_projects_amount': 0,
                'updated_projects_count': 0,
                'updated_projects_amount': 0,
                'bidding_projects_count': 0,
                'bidding_projects_amount': 0,
                'won_projects_count': 0,
                'won_projects_amount': 0
            } 
    
    @staticmethod
    def get_stage_trend_data(stage, period='week', user=None, account_id=None):
        """
        获取指定阶段的趋势数据（只统计首次进入该阶段的项目）
        
        Args:
            stage: 要查询的阶段
            period: 周期类型 'week' 或 'month'
            user: 用户对象，用于数据权限过滤
            account_id: 账户ID，用于按账户过滤统计数据
            
        Returns:
            dict: 趋势数据字典
        """
        target_user = user or current_user
        today = datetime.now().date()
        if period == 'week':
            start_date = today - timedelta(days=today.weekday() + 7*23)
            time_extract = func.strftime('%Y%W', ProjectStageHistory.change_date)
            period_label = '周'
        else:
            start_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            start_date = start_date.replace(month=((start_date.month - 23) % 12) or 12, 
                                          year=start_date.year - ((start_date.month - 23) <= 0))
            time_extract = func.strftime('%Y%m', ProjectStageHistory.change_date)
            period_label = '月'

        try:
            viewable_projects_query = get_viewable_data(Project, target_user)
            viewable_projects_query = viewable_projects_query.filter(
                Project.authorization_code.isnot(None),
                func.length(Project.authorization_code) > 0
            )
            viewable_project_ids = [p.id for p in viewable_projects_query.all()]
            if not viewable_project_ids:
                return {"labels": [], "data": [], "period": period}

            # 构建历史记录查询，添加账户过滤条件
            history_query = db.session.query(ProjectStageHistory).filter(
                ProjectStageHistory.project_id.in_(viewable_project_ids),
                ProjectStageHistory.to_stage == stage
            )
            
            # 如果指定了账户，添加账户过滤条件
            if account_id:
                history_query = history_query.filter(ProjectStageHistory.account_id == account_id)
            
            # 只统计首次进入该阶段的变更
            subquery = db.session.query(
                ProjectStageHistory.project_id,
                func.min(ProjectStageHistory.change_date).label('first_date')
            ).filter(
                ProjectStageHistory.project_id.in_(viewable_project_ids),
                ProjectStageHistory.to_stage == stage
            )
            
            # 如果指定了账户，添加账户过滤条件
            if account_id:
                subquery = subquery.filter(ProjectStageHistory.account_id == account_id)
                
            subquery = subquery.group_by(ProjectStageHistory.project_id).subquery()

            # 按周期分组统计首次进入该阶段的项目数
            query = db.session.query(
                time_extract.label('time_point'),
                func.count().label('project_count')
            ).select_from(ProjectStageHistory).join(
                subquery, 
                (ProjectStageHistory.project_id == subquery.c.project_id) & 
                (ProjectStageHistory.change_date == subquery.c.first_date),
                isouter=False
            )
            
            # 如果指定了账户，添加账户过滤条件
            if account_id:
                query = query.filter(ProjectStageHistory.account_id == account_id)
                
            query = query.group_by('time_point').order_by('time_point')

            result = query.all()

            # 生成所有时间点
            time_points = []
            current_date = start_date
            if period == 'week':
                while current_date <= today:
                    week_num = int(current_date.strftime('%W'))
                    year = current_date.year
                    time_points.append((
                        int(f"{year}{week_num:02d}"),
                        f"{year}-{week_num:02d}{period_label}"
                    ))
                    current_date += timedelta(days=7)
            else:
                while current_date <= today:
                    month = current_date.month
                    year = current_date.year
                    time_points.append((
                        int(f"{year}{month:02d}"),
                        f"{year}-{month:02d}{period_label}"
                    ))
                    if month == 12:
                        current_date = current_date.replace(year=year+1, month=1)
                    else:
                        current_date = current_date.replace(month=month+1)

            result_dict = {r[0]: r[1] for r in result}
            trend_data = []
            labels = []
            for time_key, time_label in time_points:
                labels.append(time_label)
                trend_data.append(result_dict.get(time_key, 0))

            return {
                "labels": labels,
                "data": trend_data,
                "color": STAGE_COLORS.get(stage, '#1890ff'),
                "period": period,
                "stage": stage,
                "total_periods": len(time_points),
                "account_id": account_id
            }
        except Exception as e:
            logger.error(f"获取阶段趋势数据出错: {str(e)}", exc_info=True)
            return {"labels": [], "data": [], "period": period}
    
    @staticmethod
    def get_all_stage_trends(period='week', user=None, account_id=None):
        """获取所有关键阶段的趋势数据
        
        Args:
            period: 周期类型 'week' 或 'month'
            user: 用户对象，用于数据权限过滤
            account_id: 账户ID，用于按账户过滤统计数据
            
        Returns:
            dict: 包含所有阶段趋势数据的字典
        """
        # 关键阶段 - 去掉未设置阶段
        key_stages = [stage for stage in STAGE_ORDER if stage != '未设置']
        result = {}
        
        for stage in key_stages:
            result[stage] = ProjectStatistics.get_stage_trend_data(stage, period, user, account_id)
            
        return {
            "trends": result,
            "period": period,
            "stages": key_stages,
            "colors": STAGE_COLORS,
            "account_id": account_id
        } 