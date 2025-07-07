from datetime import datetime, date
from sqlalchemy import func, extract, and_, or_, text
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
    
    # 配置：是否启用实时统计（True=实时，False=缓存）
    ENABLE_REALTIME_STATS = True
    
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
        """获取用户年度统计数据 - 支持实时/缓存模式切换"""
        try:
            if PerformanceService.ENABLE_REALTIME_STATS:
                # 实时计算模式
                logger.info(f"使用实时统计模式计算用户{user_id}的{year}年度数据")
                monthly_stats = []
                
                for month in range(1, 13):
                    try:
                        # 直接实时计算，不使用缓存
                        stats = PerformanceService.calculate_monthly_statistics_realtime(user_id, year, month)
                        monthly_stats.append(stats)
                    except Exception as month_error:
                        logger.warning(f"实时计算第{month}月统计失败: {month_error}")
                        monthly_stats.append(PerformanceService._create_empty_stats())
                
                logger.info(f"实时计算用户{user_id}年度{year}统计完成")
                return monthly_stats
            else:
                # 缓存模式（原有逻辑）
                logger.info(f"使用缓存统计模式计算用户{user_id}的{year}年度数据")
                db.session.rollback()
                
                monthly_stats = []
                for month in range(1, 13):
                    try:
                        stats = PerformanceStatistics.query.filter_by(
                            user_id=user_id, year=year, month=month
                        ).first()
                        
                        if not stats:
                            # 如果没有缓存数据，实时计算并保存
                            stats = PerformanceService.calculate_monthly_statistics(user_id, year, month)
                        
                        monthly_stats.append(stats)
                    except Exception as month_error:
                        logger.warning(f"缓存模式计算第{month}月统计失败: {month_error}")
                        monthly_stats.append(None)
                        db.session.rollback()
                
                return monthly_stats
            
        except Exception as e:
            logger.error(f"获取年度统计失败: {e}")
            return []
    
    @staticmethod
    def calculate_monthly_statistics_realtime(user_id, year, month):
        """实时计算用户指定月份的绩效统计（不使用缓存）- 优化版本"""
        try:
            # 使用单个查询批量计算所有指标，提高性能
            result = db.session.execute(text("""
                WITH monthly_data AS (
                    -- 新增项目统计
                    SELECT 
                        COUNT(DISTINCT p.id) as new_projects,
                        SUM(CASE WHEN p.rating = 5 THEN 1 ELSE 0 END) as five_star_projects,
                        string_agg(DISTINCT p.industry, '|') as industries
                    FROM projects p
                    WHERE p.owner_id = :user_id 
                      AND EXTRACT(year FROM p.created_at) = :year 
                      AND EXTRACT(month FROM p.created_at) = :month
                ),
                implant_data AS (
                    -- 植入额统计
                    SELECT COALESCE(SUM(qd.quantity * qd.market_price), 0) as implant_amount
                    FROM quotation_details qd
                    JOIN quotations q ON qd.quotation_id = q.id
                    WHERE q.owner_id = :user_id
                      AND EXTRACT(year FROM q.created_at) = :year
                      AND EXTRACT(month FROM q.created_at) = :month
                ),
                customer_data AS (
                    -- 新增客户统计
                    SELECT COUNT(*) as new_customers
                    FROM companies c
                    WHERE c.owner_id = :user_id
                      AND EXTRACT(year FROM c.created_at) = :year
                      AND EXTRACT(month FROM c.created_at) = :month
                ),
                sales_data AS (
                    -- 销售额统计
                    SELECT COALESCE(SUM(po.pricing_total_amount), 0) as sales_amount
                    FROM pricing_orders po
                    WHERE po.created_by = :user_id
                      AND po.status = 'approved'
                      AND EXTRACT(year FROM po.approved_at) = :year
                      AND EXTRACT(month FROM po.approved_at) = :month
                )
                SELECT 
                    COALESCE(md.new_projects, 0) as new_projects,
                    COALESCE(md.five_star_projects, 0) as five_star_projects,
                    COALESCE(md.industries, '') as industries,
                    COALESCE(id.implant_amount, 0) as implant_amount,
                    COALESCE(cd.new_customers, 0) as new_customers,
                    COALESCE(sd.sales_amount, 0) as sales_amount
                FROM monthly_data md
                CROSS JOIN implant_data id
                CROSS JOIN customer_data cd
                CROSS JOIN sales_data sd
            """), {
                'user_id': user_id,
                'year': year,
                'month': month
            }).fetchone()
            
            if result:
                # 处理行业统计
                industries = result.industries.split('|') if result.industries else []
                industry_stats = {}
                for industry in industries:
                    if industry and industry.strip():
                        industry_name = industry.strip()
                        industry_stats[industry_name] = industry_stats.get(industry_name, 0) + 1
                
                # 五星项目增量计算（简化版，当月新增的五星项目数）
                five_star_increment = result.five_star_projects or 0
                
                # 创建动态统计对象（不保存到数据库）
                stats = type('RealtimeStats', (), {
                    'implant_amount_actual': float(result.implant_amount or 0),
                    'sales_amount_actual': float(result.sales_amount or 0),
                    'new_customers_actual': int(result.new_customers or 0),
                    'new_projects_actual': int(result.new_projects or 0),
                    'five_star_projects_actual': int(five_star_increment),
                    'industry_statistics': industry_stats,
                    'calculated_at': datetime.now()
                })()
                
                logger.debug(f"实时计算用户{user_id} {year}年{month}月统计: 项目{result.new_projects}个, 植入额{result.implant_amount}")
                return stats
            else:
                # 如果查询无结果，返回空统计
                return PerformanceService._create_empty_stats()
                
        except Exception as e:
            logger.error(f"实时计算月度统计失败: {e}")
            return PerformanceService._create_empty_stats()
    
    @staticmethod
    def _create_empty_stats():
        """创建空的统计对象"""
        return type('EmptyStats', (), {
            'implant_amount_actual': 0,
            'sales_amount_actual': 0,
            'new_customers_actual': 0,
            'new_projects_actual': 0,
            'five_star_projects_actual': 0,
            'industry_statistics': {}
        })()
    
    @staticmethod
    def get_achievement_rate(actual, target):
        """计算达成率"""
        try:
            if not target or target == 0:
                return 0.0
            
            # 确保数据类型兼容性，转换为float进行计算
            actual_float = float(actual) if actual is not None else 0.0
            target_float = float(target) if target is not None else 0.0
            
            if target_float == 0:
                return 0.0
                
            return round((actual_float / target_float) * 100, 2)
        except (TypeError, ValueError, ZeroDivisionError) as e:
            logger.warning(f"计算达成率时出错: actual={actual}, target={target}, error={e}")
            return 0.0
    
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