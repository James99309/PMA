from datetime import datetime, date
from sqlalchemy import func, extract, and_, or_
from app import db
from app.models.performance import PerformanceTarget, PerformanceStatistics, FiveStarProjectBaseline
from app.models.quotation import Quotation, QuotationDetail
from app.models.pricing_order import PricingOrder
from app.models.project import Project
from app.models.customer import Company
from app.models.user import User
from app.services.exchange_rate_service import exchange_rate_service
import logging

logger = logging.getLogger(__name__)


class PerformanceService:
    """绩效统计服务"""
    
    @staticmethod
    def calculate_implant_amount(user_id, year, month):
        """计算植入额（来自报价单明细）"""
        try:
            # 查询指定用户在指定年月创建的报价单明细
            query = db.session.query(QuotationDetail).join(Quotation).filter(
                Quotation.owner_id == user_id,
                extract('year', Quotation.created_at) == year,
                extract('month', Quotation.created_at) == month
            )
            
            total_amount = 0.0
            for detail in query.all():
                # 计算植入额：产品数量 × 产品库中市场价格
                amount = (detail.quantity or 0) * (detail.market_price or 0)
                
                # 货币转换为CNY
                detail_currency = detail.currency or 'CNY'
                if detail_currency != 'CNY':
                    try:
                        amount = exchange_rate_service.convert_amount(amount, detail_currency, 'CNY')
                    except Exception as e:
                        logger.warning(f"植入额货币转换失败 {detail_currency} -> CNY: {e}")
                
                total_amount += amount
            
            return round(total_amount, 2)
        except Exception as e:
            logger.error(f"计算植入额失败: {e}")
            return 0.0
    
    @staticmethod
    def calculate_sales_amount(user_id, year, month):
        """计算销售额（来自已审批通过的批价单）"""
        try:
            # 查询指定用户在指定年月的已审批批价单
            query = db.session.query(PricingOrder).filter(
                PricingOrder.created_by == user_id,
                PricingOrder.status == 'approved',
                extract('year', PricingOrder.approved_at) == year,
                extract('month', PricingOrder.approved_at) == month
            )
            
            total_amount = 0.0
            for order in query.all():
                amount = order.pricing_total_amount or 0
                
                # 货币转换为CNY
                order_currency = order.currency or 'CNY'
                if order_currency != 'CNY':
                    try:
                        amount = exchange_rate_service.convert_amount(amount, order_currency, 'CNY')
                    except Exception as e:
                        logger.warning(f"销售额货币转换失败 {order_currency} -> CNY: {e}")
                
                total_amount += amount
            
            return round(total_amount, 2)
        except Exception as e:
            logger.error(f"计算销售额失败: {e}")
            return 0.0
    
    @staticmethod
    def calculate_new_customers(user_id, year, month):
        """计算新增客户数"""
        try:
            count = db.session.query(Company).filter(
                Company.created_by == user_id,
                extract('year', Company.created_at) == year,
                extract('month', Company.created_at) == month
            ).count()
            return count
        except Exception as e:
            logger.error(f"计算新增客户数失败: {e}")
            return 0
    
    @staticmethod
    def calculate_new_projects(user_id, year, month):
        """计算新增项目数"""
        try:
            count = db.session.query(Project).filter(
                Project.owner_id == user_id,
                extract('year', Project.created_at) == year,
                extract('month', Project.created_at) == month
            ).count()
            return count
        except Exception as e:
            logger.error(f"计算新增项目数失败: {e}")
            return 0
    
    @staticmethod
    def calculate_five_star_projects_increment(user_id, year, month):
        """计算五星项目增量"""
        try:
            # 获取基线数据
            baseline = FiveStarProjectBaseline.query.filter_by(user_id=user_id).first()
            if not baseline:
                # 如果没有基线，创建基线（当前月为第一个统计月）
                current_count = db.session.query(Project).filter(
                    Project.owner_id == user_id,
                    Project.rating == 5
                ).count()
                
                baseline = FiveStarProjectBaseline(
                    user_id=user_id,
                    baseline_year=year,
                    baseline_month=month,
                    baseline_count=current_count
                )
                db.session.add(baseline)
                db.session.commit()
                return 0  # 基线月增量为0
            
            # 计算当前月末的五星项目总数
            current_month_end = date(year, month, 1)
            if month == 12:
                next_month_start = date(year + 1, 1, 1)
            else:
                next_month_start = date(year, month + 1, 1)
            
            current_total = db.session.query(Project).filter(
                Project.owner_id == user_id,
                Project.rating == 5,
                Project.created_at < next_month_start
            ).count()
            
            # 计算上月末的五星项目总数
            if month == 1:
                prev_month_start = date(year - 1, 12, 1)
            else:
                prev_month_start = date(year, month, 1)
            
            prev_total = db.session.query(Project).filter(
                Project.owner_id == user_id,
                Project.rating == 5,
                Project.created_at < prev_month_start
            ).count()
            
            # 增量 = 当前月末总数 - 上月末总数
            increment = current_total - prev_total
            return max(0, increment)  # 确保不为负数
        except Exception as e:
            logger.error(f"计算五星项目增量失败: {e}")
            return 0
    
    @staticmethod
    def calculate_industry_statistics(user_id, year, month=None):
        """计算行业维度统计（基于项目的行业字段）"""
        try:
            # 按行业统计新增项目
            industry_stats = {}
            
            # 构建项目查询条件
            project_filter = [
                Project.owner_id == user_id,
                extract('year', Project.created_at) == year
            ]
            
            # 如果指定了月份，添加月份条件
            if month is not None:
                project_filter.append(extract('month', Project.created_at) == month)
            
            # 按项目行业统计
            project_query = db.session.query(
                Project.industry,
                func.count(Project.id).label('count')
            ).filter(*project_filter).group_by(Project.industry)
            
            for industry, count in project_query.all():
                industry_name = industry or '未分类'
                industry_stats[industry_name] = count
            
            return industry_stats
        except Exception as e:
            logger.error(f"计算行业统计失败: {e}")
            return {}
    
    @staticmethod
    def calculate_monthly_statistics(user_id, year, month):
        """计算用户指定月份的绩效统计"""
        try:
            # 计算各项指标
            implant_amount = PerformanceService.calculate_implant_amount(user_id, year, month)
            sales_amount = PerformanceService.calculate_sales_amount(user_id, year, month)
            new_customers = PerformanceService.calculate_new_customers(user_id, year, month)
            new_projects = PerformanceService.calculate_new_projects(user_id, year, month)
            five_star_increment = PerformanceService.calculate_five_star_projects_increment(user_id, year, month)
            industry_stats = PerformanceService.calculate_industry_statistics(user_id, year, month)
            
            # 查找或创建统计记录
            stats = PerformanceStatistics.query.filter_by(
                user_id=user_id, year=year, month=month
            ).first()
            
            if not stats:
                stats = PerformanceStatistics(user_id=user_id, year=year, month=month)
                db.session.add(stats)
            
            # 更新统计数据
            stats.implant_amount_actual = implant_amount
            stats.sales_amount_actual = sales_amount
            stats.new_customers_actual = new_customers
            stats.new_projects_actual = new_projects
            stats.five_star_projects_actual = five_star_increment
            stats.industry_statistics = industry_stats
            stats.calculated_at = datetime.now()
            
            db.session.commit()
            return stats
        except Exception as e:
            logger.error(f"计算月度统计失败: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def get_yearly_statistics(user_id, year):
        """获取用户年度统计数据"""
        try:
            # 确保事务开始时是干净的
            db.session.rollback()
            
            # 获取或计算当年各月的统计数据
            monthly_stats = []
            for month in range(1, 13):
                try:
                    stats = PerformanceStatistics.query.filter_by(
                        user_id=user_id, year=year, month=month
                    ).first()
                    
                    if not stats:
                        # 如果没有缓存数据，实时计算
                        stats = PerformanceService.calculate_monthly_statistics(user_id, year, month)
                    
                    monthly_stats.append(stats)
                except Exception as month_error:
                    logger.warning(f"计算第{month}月统计失败: {month_error}")
                    # 添加空的统计对象
                    monthly_stats.append(None)
                    # 回滚失败的事务
                    db.session.rollback()
            
            return monthly_stats
        except Exception as e:
            logger.error(f"获取年度统计失败: {e}")
            db.session.rollback()
            return []
    
    @staticmethod
    def get_achievement_rate(actual, target):
        """计算达成率"""
        if not target or target == 0:
            return 0.0
        return round((actual / target) * 100, 2)
    
    @staticmethod
    def get_achievement_color(rate):
        """根据达成率获取颜色"""
        if rate >= 100:
            return 'success'  # 绿色
        elif rate >= 80:
            return 'warning'  # 黄色
        else:
            return 'danger'   # 红色
    
    @staticmethod
    def get_monthly_industry_statistics(user_id, year):
        """获取用户年度按月份的行业统计数据"""
        try:
            monthly_industry_stats = {}
            
            for month in range(1, 13):
                month_stats = PerformanceService.calculate_industry_statistics(user_id, year, month)
                monthly_industry_stats[month] = month_stats
            
            return monthly_industry_stats
        except Exception as e:
            logger.error(f"获取月度行业统计失败: {e}")
            return {}

    @staticmethod
    def refresh_all_statistics(user_id, year):
        """刷新用户年度所有统计数据"""
        try:
            for month in range(1, 13):
                PerformanceService.calculate_monthly_statistics(user_id, year, month)
            return True
        except Exception as e:
            logger.error(f"刷新统计数据失败: {e}")
            return False 