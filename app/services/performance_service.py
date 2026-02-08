from datetime import datetime, date
from sqlalchemy import func, extract, and_, or_, text, case
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
    """绩效统计服务 - 使用实时统计模式"""
    
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
    def calculate_industry_statistics(user_id, year=None, month=None, year_month=None):
        """计算行业维度统计（基于项目的行业字段）

        Args:
            user_id: 用户ID
            year: 年份（可选，None表示全局分析）
            month: 月份（可选，需配合year使用）
            year_month: 年月字符串格式 'YYYY-MM'（可选，用于跨年月份查询）

        Returns:
            dict: 行业统计数据 {行业名: 数量}
        """
        try:
            # 按行业统计新增项目
            industry_stats = {}

            # 构建项目查询条件
            project_filter = [Project.owner_id == user_id]

            # 支持三种模式：
            # 1. year_month: 跨年月份查询（优先级最高）
            # 2. year + month: 指定年月
            # 3. year: 指定年份
            # 4. 无参数: 全局分析（所有数据）
            if year_month:
                # 解析 'YYYY-MM' 格式
                ym_year, ym_month = map(int, year_month.split('-'))
                project_filter.append(extract('year', Project.created_at) == ym_year)
                project_filter.append(extract('month', Project.created_at) == ym_month)
            elif year is not None:
                project_filter.append(extract('year', Project.created_at) == year)
                if month is not None:
                    project_filter.append(extract('month', Project.created_at) == month)
            # else: 全局模式，不添加时间过滤条件

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
        """计算并保存用户指定月份的绩效统计到数据库（可选功能，主要用于手动刷新缓存）

        注意：此函数将结果保存到performance_statistics表，但系统默认使用实时统计，
        不依赖此缓存数据。仅在需要手动刷新历史缓存时使用。
        """
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
        """获取用户年度统计数据 - 批量计算模式（1次SQL替代12次）"""
        try:
            logger.info(f"批量计算用户{user_id}的{year}年度绩效数据")
            monthly_stats = PerformanceService.calculate_yearly_statistics_batch(user_id, year)
            logger.info(f"批量计算用户{user_id}年度{year}统计完成，共{len(monthly_stats)}个月")
            return monthly_stats
        except Exception as e:
            logger.error(f"获取年度统计失败: {e}，回退到逐月计算")
            # 回退到逐月计算
            try:
                monthly_stats = []
                for month in range(1, 13):
                    try:
                        stats = PerformanceService.calculate_monthly_statistics_realtime(user_id, year, month)
                        monthly_stats.append(stats)
                    except Exception as month_error:
                        logger.warning(f"实时计算第{month}月统计失败: {month_error}")
                        monthly_stats.append(PerformanceService._create_empty_stats())
                return monthly_stats
            except Exception as e2:
                logger.error(f"逐月计算也失败: {e2}")
                return []

    @staticmethod
    def calculate_yearly_statistics_batch(user_id, year):
        """批量计算用户全年12个月的绩效统计（1次SQL替代12次）

        将原来12次 calculate_monthly_statistics_realtime 调用合并为
        单次按月 GROUP BY 的聚合查询，大幅减少数据库往返。
        """
        result = db.session.execute(text("""
            WITH all_months AS (
                SELECT generate_series(1, 12) AS month
            ),
            monthly_projects AS (
                SELECT EXTRACT(month FROM p.created_at)::int AS month,
                       COUNT(DISTINCT p.id) AS new_projects,
                       SUM(CASE WHEN p.rating = 5 THEN 1 ELSE 0 END) AS five_star_projects,
                       string_agg(DISTINCT p.industry, '|') AS industries
                FROM projects p
                WHERE p.owner_id = :user_id
                  AND EXTRACT(year FROM p.created_at) = :year
                GROUP BY EXTRACT(month FROM p.created_at)
            ),
            implant_data AS (
                SELECT EXTRACT(month FROM q.created_at)::int AS month,
                       COALESCE(SUM(qd.quantity * qd.market_price), 0) AS implant_amount
                FROM quotation_details qd
                JOIN quotations q ON qd.quotation_id = q.id
                WHERE q.owner_id = :user_id
                  AND EXTRACT(year FROM q.created_at) = :year
                GROUP BY EXTRACT(month FROM q.created_at)
            ),
            customer_data AS (
                SELECT EXTRACT(month FROM c.created_at)::int AS month,
                       COUNT(*) AS new_customers
                FROM companies c
                WHERE c.owner_id = :user_id
                  AND EXTRACT(year FROM c.created_at) = :year
                GROUP BY EXTRACT(month FROM c.created_at)
            ),
            sales_data AS (
                SELECT EXTRACT(month FROM po.approved_at)::int AS month,
                       COALESCE(SUM(po.pricing_total_amount), 0) AS sales_amount
                FROM pricing_orders po
                WHERE po.created_by = :user_id
                  AND po.status = 'approved'
                  AND EXTRACT(year FROM po.approved_at) = :year
                GROUP BY EXTRACT(month FROM po.approved_at)
            )
            SELECT
                am.month,
                COALESCE(mp.new_projects, 0) AS new_projects,
                COALESCE(mp.five_star_projects, 0) AS five_star_projects,
                COALESCE(mp.industries, '') AS industries,
                COALESCE(id.implant_amount, 0) AS implant_amount,
                COALESCE(cd.new_customers, 0) AS new_customers,
                COALESCE(sd.sales_amount, 0) AS sales_amount
            FROM all_months am
            LEFT JOIN monthly_projects mp ON am.month = mp.month
            LEFT JOIN implant_data id ON am.month = id.month
            LEFT JOIN customer_data cd ON am.month = cd.month
            LEFT JOIN sales_data sd ON am.month = sd.month
            ORDER BY am.month
        """), {'user_id': user_id, 'year': year}).fetchall()

        monthly_stats = []
        for row in result:
            # 处理行业统计
            industries_str = row.industries if row.industries else ''
            industry_stats = {}
            if industries_str:
                for industry in industries_str.split('|'):
                    if industry and industry.strip():
                        name = industry.strip()
                        industry_stats[name] = industry_stats.get(name, 0) + 1

            stats = type('RealtimeStats', (), {
                'implant_amount_actual': float(row.implant_amount or 0),
                'sales_amount_actual': float(row.sales_amount or 0),
                'new_customers_actual': int(row.new_customers or 0),
                'new_projects_actual': int(row.new_projects or 0),
                'five_star_projects_actual': int(row.five_star_projects or 0),
                'industry_statistics': industry_stats,
                'calculated_at': datetime.now()
            })()
            monthly_stats.append(stats)

        # 确保返回12个月数据
        while len(monthly_stats) < 12:
            monthly_stats.append(PerformanceService._create_empty_stats())

        return monthly_stats
    
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
    def get_monthly_industry_statistics(user_id, year=None):
        """获取用户按月份的行业统计数据

        Args:
            user_id: 用户ID
            year: 年份（可选，None表示全局模式返回最近12个月）

        Returns:
            dict: 月度行业统计数据
                - 指定年份模式: {1: {...}, 2: {...}, ...}
                - 全局模式: {'2024-02': {...}, '2024-03': {...}, ...}
        """
        try:
            monthly_industry_stats = {}

            if year is not None:
                # 指定年份模式：返回该年1-12月
                for month in range(1, 13):
                    month_stats = PerformanceService.calculate_industry_statistics(user_id, year, month)
                    monthly_industry_stats[month] = month_stats
            else:
                # 全局模式：返回最近12个月（跨年）
                from datetime import datetime
                from dateutil.relativedelta import relativedelta

                now = datetime.now()
                for i in range(11, -1, -1):  # 从11个月前到当前月
                    target_date = now - relativedelta(months=i)
                    year_month = target_date.strftime('%Y-%m')

                    month_stats = PerformanceService.calculate_industry_statistics(
                        user_id, year_month=year_month
                    )
                    monthly_industry_stats[year_month] = month_stats

            return monthly_industry_stats
        except Exception as e:
            logger.error(f"获取月度行业统计失败: {e}")
            return {}

    @staticmethod
    def calculate_customer_type_statistics(user_id, year=None, month=None, year_month=None):
        """计算客户类型分布统计

        Args:
            user_id: 用户ID
            year: 年份（可选，None表示全局分析）
            month: 月份（可选，需配合year使用）
            year_month: 年月字符串格式 'YYYY-MM'（可选，用于跨年月份查询）

        Returns:
            dict: 客户类型统计数据 {类型名: 数量}
        """
        try:
            customer_stats = {}

            # 构建查询条件
            company_filter = [Company.owner_id == user_id, Company.is_deleted == False]

            # 支持三种模式：
            # 1. year_month: 跨年月份查询（优先级最高）
            # 2. year + month: 指定年月
            # 3. year: 指定年份
            # 4. 无参数: 全局分析（所有数据）
            if year_month:
                ym_year, ym_month = map(int, year_month.split('-'))
                company_filter.append(extract('year', Company.created_at) == ym_year)
                company_filter.append(extract('month', Company.created_at) == ym_month)
            elif year is not None:
                company_filter.append(extract('year', Company.created_at) == year)
                if month is not None:
                    company_filter.append(extract('month', Company.created_at) == month)
            # else: 全局模式，不添加时间过滤条件

            # 按客户类型统计
            query = db.session.query(
                Company.company_type,
                func.count(Company.id).label('count')
            ).filter(*company_filter).group_by(Company.company_type)

            for company_type, count in query.all():
                type_name = company_type or 'other'
                customer_stats[type_name] = count

            return customer_stats
        except Exception as e:
            logger.error(f"计算客户类型统计失败: {e}")
            return {}

    @staticmethod
    def get_monthly_customer_statistics(user_id, year=None):
        """获取用户按月份的客户类型统计数据

        Args:
            user_id: 用户ID
            year: 年份（可选，None表示全局模式返回最近12个月）

        Returns:
            dict: 月度客户类型统计数据
                - 指定年份模式: {1: {...}, 2: {...}, ...}
                - 全局模式: {'2024-02': {...}, '2024-03': {...}, ...}
        """
        try:
            monthly_customer_stats = {}

            if year is not None:
                # 指定年份模式：返回该年1-12月
                for month in range(1, 13):
                    month_stats = PerformanceService.calculate_customer_type_statistics(user_id, year, month)
                    # 添加月度总计
                    total = sum(month_stats.values())
                    month_stats['total'] = total
                    monthly_customer_stats[month] = month_stats
            else:
                # 全局模式：返回最近12个月（跨年）
                from datetime import datetime
                from dateutil.relativedelta import relativedelta

                now = datetime.now()
                for i in range(11, -1, -1):  # 从11个月前到当前月
                    target_date = now - relativedelta(months=i)
                    year_month = target_date.strftime('%Y-%m')

                    month_stats = PerformanceService.calculate_customer_type_statistics(
                        user_id, year_month=year_month
                    )
                    # 添加月度总计
                    total = sum(month_stats.values())
                    month_stats['total'] = total
                    monthly_customer_stats[year_month] = month_stats

            return monthly_customer_stats
        except Exception as e:
            logger.error(f"获取月度客户类型统计失败: {e}")
            return {}

    @staticmethod
    def calculate_customer_activity_rate(user_id):
        """计算客户活跃度健康比率

        公式: (highly_active + active + normal) / 总客户数 × 100%

        活跃度状态基于 Company.status 字段（6级）：
        - highly_active: 高度活跃
        - active: 活跃
        - normal: 正常（算作健康）
        - inactive: 不活跃
        - dormant: 休眠
        - lost: 流失

        Args:
            user_id: 用户ID

        Returns:
            dict: {
                'rate': float,  # 健康度百分比 (0-100)
                'highly_active_count': int,
                'active_count': int,
                'normal_count': int,
                'total_count': int
            }
        """
        try:
            result = db.session.query(
                func.count(Company.id).label('total'),
                func.count(case(
                    (Company.status.in_(['highly_active', 'active', 'normal']), Company.id)
                )).label('healthy'),
                func.count(case(
                    (Company.status == 'highly_active', Company.id)
                )).label('highly_active'),
                func.count(case(
                    (Company.status == 'active', Company.id)
                )).label('active'),
                func.count(case(
                    (Company.status == 'normal', Company.id)
                )).label('normal')
            ).filter(
                Company.owner_id == user_id,
                Company.is_deleted == False
            ).first()

            total_count = result.total or 0
            healthy_count = result.healthy or 0
            highly_active_count = result.highly_active or 0
            active_count = result.active or 0
            normal_count = result.normal or 0

            rate = (healthy_count / total_count * 100) if total_count > 0 else 0

            return {
                'rate': round(rate, 2),
                'highly_active_count': highly_active_count,
                'active_count': active_count,
                'normal_count': normal_count,
                'total_count': total_count
            }
        except Exception as e:
            logger.error(f"计算客户活跃度失败: {e}")
            return {
                'rate': 0,
                'highly_active_count': 0,
                'active_count': 0,
                'normal_count': 0,
                'total_count': 0
            }

    @staticmethod
    def calculate_project_activity_rate(user_id):
        """计算项目活跃度健康比率

        公式: (highly_active + active + normal) / 非冻结项目总数 × 100%
        frozen 状态项目（终态）不计入分母。
        """
        try:
            result = db.session.query(
                func.count(Project.id).label('total'),
                func.count(case(
                    (Project.activity_status.in_(['highly_active', 'active', 'normal']), Project.id)
                )).label('healthy'),
                func.count(case(
                    (Project.activity_status == 'frozen', Project.id)
                )).label('frozen_count')
            ).filter(
                Project.owner_id == user_id
            ).first()

            total = result.total or 0
            healthy = result.healthy or 0
            frozen_count = result.frozen_count or 0
            active_total = total - frozen_count

            rate = (healthy / active_total * 100) if active_total > 0 else 0

            return {
                'rate': round(rate, 2),
                'healthy_count': healthy,
                'total_count': total,
                'active_total': active_total,
                'frozen_count': frozen_count
            }
        except Exception as e:
            logger.error(f"计算项目活跃度失败: {e}")
            return {
                'rate': 0,
                'healthy_count': 0,
                'total_count': 0,
                'active_total': 0,
                'frozen_count': 0
            }

    @staticmethod
    def refresh_all_statistics(user_id, year):
        """刷新用户年度所有统计数据到缓存表（可选功能）

        注意：系统默认使用实时统计，此函数仅用于特殊需求（如离线分析）。
        正常业务流程不需要调用此函数。
        """
        try:
            for month in range(1, 13):
                PerformanceService.calculate_monthly_statistics(user_id, year, month)
            return True
        except Exception as e:
            logger.error(f"刷新统计数据失败: {e}")
            return False