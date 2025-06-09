from app import db
from app.models.project import Project
from app.models.projectpm_stage_history import ProjectStageHistory
from app.utils.access_control import get_viewable_data
from sqlalchemy import func, cast, String, and_, or_, not_, desc, distinct
from datetime import datetime, timedelta
from flask_login import current_user
import logging
import json
from app.utils.dictionary_helpers import PROJECT_STAGE_LABELS

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 主线阶段定义（含签约）
MAINLINE_STAGES = [k for k in PROJECT_STAGE_LABELS.keys() if k not in ('lost', 'paused')]

# 阶段颜色定义
STAGE_COLORS = {k: v['zh'] for k, v in PROJECT_STAGE_LABELS.items()}

# 排序顺序
STAGE_ORDER = list(PROJECT_STAGE_LABELS.keys()) + ['unset']

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

            # 有效项目：主线阶段，且排除签约阶段
            valid_stages = [k for k in MAINLINE_STAGES if k != 'signed']
            valid_projects = [p for p in all_projects if (p.current_stage in valid_stages)]
            stats = {}
            stats['total_valid_projects'] = len(valid_projects)
            stats['total_valid_amount'] = sum(p.quotation_customer or 0 for p in valid_projects)

            # 各阶段项目数量
            default_stages = list(PROJECT_STAGE_LABELS.keys()) + ['unset']
            stage_counts = {stage: 0 for stage in default_stages}
            for p in all_projects:
                stage = p.current_stage or 'unset'
                if stage in stage_counts:
                    stage_counts[stage] += 1
                else:
                    stage_counts[stage] = 1
            stats['stage_counts'] = stage_counts

            # 各阶段金额
            stage_amounts = {stage: 0 for stage in default_stages}
            for p in all_projects:
                stage = p.current_stage or 'unset'
                amount = p.quotation_customer or 0
                if stage in stage_amounts:
                    stage_amounts[stage] += amount
                else:
                    stage_amounts[stage] = amount
            stats['stage_amounts'] = stage_amounts

            # 招标中项目统计
            bidding_projects = [p for p in all_projects if p.current_stage == 'tendering']
            stats['tendering_projects_count'] = len(bidding_projects)
            stats['tendering_projects_amount'] = sum(p.quotation_customer or 0 for p in bidding_projects)

            # 中标项目统计
            won_projects = [p for p in all_projects if p.current_stage == 'awarded']
            stats['won_projects_count'] = len(won_projects)
            stats['won_projects_amount'] = sum(p.quotation_customer or 0 for p in won_projects)

            # 批价项目统计
            quoted_projects = [p for p in all_projects if p.current_stage == 'quoted']
            stats['quoted_projects_count'] = len(quoted_projects)
            stats['quoted_projects_amount'] = sum(p.quotation_customer or 0 for p in quoted_projects)

            # 发现阶段项目统计
            discover_projects = [p for p in all_projects if p.current_stage == 'discover']
            stats['discover_projects_count'] = len(discover_projects)
            stats['discover_projects_amount'] = sum(p.quotation_customer or 0 for p in discover_projects)

            # 植入阶段项目统计
            embed_projects = [p for p in all_projects if p.current_stage == 'embed']
            stats['embed_projects_count'] = len(embed_projects)
            stats['embed_projects_amount'] = sum(p.quotation_customer or 0 for p in embed_projects)

            # 招标前阶段项目统计
            pre_tender_projects = [p for p in all_projects if p.current_stage == 'pre_tender']
            stats['pre_tender_projects_count'] = len(pre_tender_projects)
            stats['pre_tender_projects_amount'] = sum(p.quotation_customer or 0 for p in pre_tender_projects)

            # 失败阶段项目统计
            lost_projects = [p for p in all_projects if p.current_stage == 'lost']
            stats['lost_projects_count'] = len(lost_projects)
            stats['lost_projects_amount'] = sum(p.quotation_customer or 0 for p in lost_projects)

            # 搁置阶段项目统计
            paused_projects = [p for p in all_projects if p.current_stage == 'paused']
            stats['paused_projects_count'] = len(paused_projects)
            stats['paused_projects_amount'] = sum(p.quotation_customer or 0 for p in paused_projects)

            # 业务推进统计（本月主线阶段推进，且不含切换到失败/搁置）
            today = datetime.now().date()
            start_date = today.replace(day=1)
            
            # 查询本月主线阶段推进的历史记录
            history_query = db.session.query(ProjectStageHistory.project_id).filter(
                ProjectStageHistory.change_date >= start_date,
                ProjectStageHistory.from_stage.in_(MAINLINE_STAGES),
                ProjectStageHistory.to_stage.in_(MAINLINE_STAGES),
                ProjectStageHistory.to_stage.notin_(['lost', 'paused'])
            )
            if account_id:
                history_query = history_query.filter(ProjectStageHistory.account_id == account_id)
            project_ids = set([row.project_id for row in history_query.distinct()])
            # 修正：直接查找所有有授权编码且在project_ids中的项目
            updated_projects_query = get_viewable_data(Project, target_user).filter(
                Project.id.in_(project_ids),
                Project.authorization_code.isnot(None),
                func.length(Project.authorization_code) > 0
            )
            if account_id:
                updated_projects_query = updated_projects_query.filter(Project.owner_id == account_id)
            updated_projects = updated_projects_query.all()
            stats['updated_projects_count'] = len(updated_projects)
            stats['updated_projects_amount'] = sum(p.quotation_customer or 0 for p in updated_projects)

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
            default_stages = list(PROJECT_STAGE_LABELS.keys()) + ['unset']
            return {
                'total_valid_projects': 0,
                'total_valid_amount': 0,
                'stage_counts': {stage: 0 for stage in default_stages},
                'stage_amounts': {stage: 0 for stage in default_stages},
                'new_projects_count': 0,
                'new_projects_amount': 0,
                'updated_projects_count': 0,
                'updated_projects_amount': 0,
                'tendering_projects_count': 0,
                'tendering_projects_amount': 0,
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
            # 修改为PostgreSQL的时间格式化函数
            time_extract = func.to_char(ProjectStageHistory.change_date, 'YYYYWW')
            period_label = '周'
        else:
            start_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            start_date = start_date.replace(month=((start_date.month - 23) % 12) or 12, 
                                          year=start_date.year - ((start_date.month - 23) <= 0))
            # 修改为PostgreSQL的时间格式化函数
            time_extract = func.to_char(ProjectStageHistory.change_date, 'YYYYMM')
            period_label = '月'

        try:
            viewable_projects_query = get_viewable_data(Project, target_user)
            viewable_projects_query = viewable_projects_query.filter(
                Project.authorization_code.isnot(None),
                func.length(Project.authorization_code) > 0
            )
            viewable_project_ids = [p.id for p in viewable_projects_query.all()]
            logger.debug(f"可见的项目IDs: {viewable_project_ids}")
            
            if not viewable_project_ids:
                logger.debug("没有可见的项目")
                return {"labels": [], "data": [], "period": period}

            # 构建历史记录查询，添加账户过滤条件和时间范围过滤
            history_query = db.session.query(ProjectStageHistory).filter(
                ProjectStageHistory.project_id.in_(viewable_project_ids),
                ProjectStageHistory.to_stage == stage,
                ProjectStageHistory.change_date >= start_date,  # 添加时间范围过滤
                ProjectStageHistory.change_date <= datetime.now()  # 添加时间范围过滤
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
            
            # 添加调试日志
            logger.debug(f"趋势查询结果: {result}")
            logger.debug(f"查询开始日期: {start_date}, 结束日期: {today}")
            logger.debug(f"SQL查询: {str(query.statement.compile(compile_kwargs={'literal_binds': True}))}")

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

            # 添加调试日志
            logger.debug(f"生成的时间点: {time_points}")

            result_dict = {str(r[0]): r[1] for r in result}
            trend_data = []
            labels = []
            for time_key, time_label in time_points:
                labels.append(time_label)
                trend_data.append(result_dict.get(str(time_key), 0))

            # 添加调试日志
            logger.debug(f"最终趋势数据: labels={labels}, data={trend_data}")

            return_data = {
                "labels": labels,
                "data": trend_data,
                "color": STAGE_COLORS.get(stage, '#1890ff'),
                "period": period,
                "stage": stage,
                "total_periods": len(time_points),
                "account_id": account_id
            }
            logger.debug(f"返回数据: {return_data}")
            return return_data
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
        key_stages = [stage for stage in STAGE_ORDER if stage != 'unset']
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