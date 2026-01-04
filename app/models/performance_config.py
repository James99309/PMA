from app import db
import time
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Numeric, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
import json
import logging

logger = logging.getLogger(__name__)

class PerformanceMetricsDefinition(db.Model):
    """绩效指标定义表 - 定义系统中所有可用的绩效指标"""
    __tablename__ = 'performance_metrics_definition'
    
    id = Column(Integer, primary_key=True)
    metric_code = Column(String(50), unique=True, nullable=False, index=True)
    metric_name = Column(String(100), nullable=False)
    metric_category = Column(String(50), default='custom')
    data_type = Column(String(20), nullable=False)  # amount, count, percentage, score
    default_unit = Column(String(20))
    description = Column(Text)
    available_sources = Column(JSON)  # 可用数据源配置
    is_system_metric = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super(PerformanceMetricsDefinition, self).__init__(**kwargs)
        if not self.created_at:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.id,
            'metric_code': self.metric_code,
            'metric_name': self.metric_name,
            'metric_category': self.metric_category,
            'data_type': self.data_type,
            'default_unit': self.default_unit,
            'description': self.description,
            'available_sources': self.available_sources,
            'is_system_metric': self.is_system_metric,
            'is_active': self.is_active
        }

class RolePerformanceConfig(db.Model):
    """角色绩效配置主表 - 每个角色的绩效配置方案"""
    __tablename__ = 'role_performance_config'
    
    id = Column(Integer, primary_key=True)
    role = Column(String(50), nullable=False, unique=True, index=True)
    config_name = Column(String(100))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    creator = relationship('User', foreign_keys=[created_by])
    updater = relationship('User', foreign_keys=[updated_by])
    items = relationship('RolePerformanceItem', backref='role_config', 
                        cascade='all, delete-orphan', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'config_name': self.config_name,
            'description': self.description,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class RolePerformanceItem(db.Model):
    """角色绩效项目表 - 每个角色具体的绩效考核项目"""
    __tablename__ = 'role_performance_items'
    
    id = Column(Integer, primary_key=True)
    role_config_id = Column(Integer, ForeignKey('role_performance_config.id'), nullable=False)
    metric_id = Column(Integer, ForeignKey('performance_metrics_definition.id'))
    
    # 项目基本配置
    item_name = Column(String(100), nullable=False)
    item_code = Column(String(50), nullable=False)
    sort_order = Column(Integer, default=0)
    is_enabled = Column(Boolean, default=True)
    
    # 统计范围配置
    stat_scope = Column(String(20), nullable=False, default='personal')
    stat_scope_description = Column(Text)
    
    # 计算方法配置
    calculation_method = Column(String(20), default='sum')
    calculation_formula = Column(Text)
    data_source_config = Column(JSON)
    
    # 合格标准配置
    qualification_rate = Column(Numeric(5,2))
    excellent_threshold = Column(Numeric(15,2))
    good_threshold = Column(Numeric(15,2))
    qualified_threshold = Column(Numeric(15,2))
    
    # 显示配置
    display_unit = Column(String(20))
    decimal_places = Column(Integer, default=2)
    color_config = Column(JSON)
    
    # 权重配置
    weight = Column(Numeric(5,2), default=1.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    metric = relationship('PerformanceMetricsDefinition', backref='role_items')
    
    __table_args__ = (
        db.UniqueConstraint('role_config_id', 'item_code', name='uq_role_item_code'),
        db.Index('idx_role_items_config', 'role_config_id'),
        db.Index('idx_role_items_metric', 'metric_id'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'role_config_id': self.role_config_id,
            'metric_id': self.metric_id,
            'item_name': self.item_name,
            'item_code': self.item_code,
            'sort_order': self.sort_order,
            'is_enabled': self.is_enabled,
            'stat_scope': self.stat_scope,
            'stat_scope_description': self.stat_scope_description,
            'calculation_method': self.calculation_method,
            'calculation_formula': self.calculation_formula,
            'data_source_config': self.data_source_config,
            'qualification_rate': float(self.qualification_rate) if self.qualification_rate else None,
            'excellent_threshold': float(self.excellent_threshold) if self.excellent_threshold else None,
            'good_threshold': float(self.good_threshold) if self.good_threshold else None,
            'qualified_threshold': float(self.qualified_threshold) if self.qualified_threshold else None,
            'display_unit': self.display_unit,
            'decimal_places': self.decimal_places,
            'color_config': self.color_config,
            'weight': float(self.weight) if self.weight else 1.0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class PerformanceFormulaTemplate(db.Model):
    """绩效计算公式模板表 - 预定义的常用计算公式"""
    __tablename__ = 'performance_formula_templates'
    
    id = Column(Integer, primary_key=True)
    template_name = Column(String(100), nullable=False)
    template_category = Column(String(50))
    formula_expression = Column(Text, nullable=False)
    description = Column(Text)
    variables_definition = Column(JSON)  # 变量定义
    example_usage = Column(Text)
    is_system_template = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'template_name': self.template_name,
            'template_category': self.template_category,
            'formula_expression': self.formula_expression,
            'description': self.description,
            'variables_definition': self.variables_definition,
            'example_usage': self.example_usage,
            'is_system_template': self.is_system_template,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class RolePerformanceAccess(db.Model):
    """角色绩效数据访问权限表 - 控制不同角色的数据访问范围"""
    __tablename__ = 'role_performance_access'
    
    id = Column(Integer, primary_key=True)
    role = Column(String(50), nullable=False, index=True)
    access_scope = Column(String(20), nullable=False)  # personal, department, company, system
    access_conditions = Column(JSON)  # 访问条件配置
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('role', 'access_scope', name='uq_role_access_scope'),
        db.Index('idx_role_access', 'role', 'access_scope'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'access_scope': self.access_scope,
            'access_conditions': self.access_conditions,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# 扩展原有的绩效服务类，支持基于角色配置的动态计算
class ConfigurablePerformanceService:
    """基于角色配置的绩效计算服务"""
    
    @staticmethod
    def get_role_performance_config(role_code):
        """获取角色的绩效配置"""
        config = RolePerformanceConfig.query.filter_by(
            role=role_code, 
            is_active=True
        ).first()
        
        if not config:
            return None
        
        items = RolePerformanceItem.query.filter_by(
            role_config_id=config.id,
            is_enabled=True
        ).order_by(RolePerformanceItem.sort_order).all()
        
        return {
            'config': config,
            'items': items
        }
    
    @staticmethod
    def calculate_performance_by_config(user_id, role_code, year, month):
        """基于角色配置计算绩效数据"""
        # 获取角色配置
        role_config = ConfigurablePerformanceService.get_role_performance_config(role_code)
        if not role_config:
            return {}
        
        results = {}
        
        # 遍历配置的绩效项目
        for item in role_config['items']:
            try:
                # 根据统计范围确定用户范围
                user_ids = ConfigurablePerformanceService.get_user_ids_by_scope(
                    user_id, item.stat_scope
                )
                
                # 根据计算方法计算值
                value = ConfigurablePerformanceService.calculate_item_value(
                    item, user_ids, year, month
                )
                
                results[item.item_code] = {
                    'value': value,
                    'item_name': item.item_name,
                    'display_unit': item.display_unit,
                    'thresholds': {
                        'excellent': float(item.excellent_threshold) if item.excellent_threshold else None,
                        'good': float(item.good_threshold) if item.good_threshold else None,
                        'qualified': float(item.qualified_threshold) if item.qualified_threshold else None
                    },
                    'achievement_rate': ConfigurablePerformanceService.calculate_achievement_rate(
                        value, item.qualified_threshold
                    ) if item.qualified_threshold else 0
                }
                
            except Exception as e:
                import logging
                logging.error(f"计算绩效项目失败 {item.item_code}: {e}")
                results[item.item_code] = {
                    'value': 0,
                    'item_name': item.item_name,
                    'error': str(e)
                }
        
        return results
    
    @staticmethod
    def get_user_ids_by_scope(base_user_id, scope):
        """根据统计范围获取用户ID列表"""
        from app.models.user import User
        
        if scope == 'personal':
            return [base_user_id]
        elif scope == 'department':
            # 获取同部门用户
            base_user = User.query.get(base_user_id)
            if not base_user or not base_user.department:
                return [base_user_id]
            
            dept_users = User.query.filter_by(
                department=base_user.department,
                company_name=base_user.company_name
            ).all()
            return [u.id for u in dept_users]
        elif scope == 'company':
            # 获取同公司用户
            base_user = User.query.get(base_user_id)
            if not base_user or not base_user.company_name:
                return [base_user_id]
            
            company_users = User.query.filter_by(
                company_name=base_user.company_name
            ).all()
            return [u.id for u in company_users]
        elif scope == 'system':
            # 获取所有用户
            all_users = User.query.all()
            return [u.id for u in all_users]
        else:
            return [base_user_id]
    
    @staticmethod
    def calculate_item_value(item, user_ids, year, month):
        """计算单个绩效项目的值"""
        from sqlalchemy import extract, func, text
        
        try:
            # 解析数据源配置
            data_source = item.data_source_config or {}
            table_name = data_source.get('table', 'quotations')  # 默认表
            
            # 根据计算方法和数据源进行查询
            if item.calculation_method == 'custom' and item.calculation_formula:
                # 自定义公式计算
                return ConfigurablePerformanceService.execute_custom_formula(
                    item.calculation_formula, user_ids, year, month
                )
            else:
                # 标准计算方法
                return ConfigurablePerformanceService.execute_standard_calculation(
                    item.calculation_method, table_name, user_ids, year, month
                )
                
        except Exception as e:
            import logging
            logging.error(f"计算项目值失败 {item.item_code}: {e}")
            return 0.0
    
    @staticmethod
    def execute_standard_calculation(method, table_name, user_ids, year, month):
        """执行标准计算方法"""
        # 这里可以根据不同的表和方法实现具体的查询逻辑
        # 为了简化，这里提供一个示例实现
        
        if table_name == 'quotations':
            from app.models.quotation import Quotation, QuotationDetail
            
            query = db.session.query(QuotationDetail).join(Quotation).filter(
                Quotation.owner_id.in_(user_ids),
                extract('year', Quotation.created_at) == year,
                extract('month', Quotation.created_at) == month
            )
            
            if method == 'sum':
                # 计算总金额
                total = query.with_entities(
                    func.sum(QuotationDetail.quantity * QuotationDetail.market_price)
                ).scalar()
                return float(total or 0)
            elif method == 'count':
                return query.count()
            elif method == 'avg':
                total = query.with_entities(
                    func.avg(QuotationDetail.quantity * QuotationDetail.market_price)
                ).scalar()
                return float(total or 0)
        
        elif table_name == 'pricing_orders':
            from app.models.pricing_order import PricingOrder
            
            query = db.session.query(PricingOrder).filter(
                PricingOrder.created_by.in_(user_ids),
                PricingOrder.status == 'approved',
                extract('year', PricingOrder.approved_at) == year,
                extract('month', PricingOrder.approved_at) == month
            )
            
            if method == 'sum':
                total = query.with_entities(
                    func.sum(PricingOrder.pricing_total_amount)
                ).scalar()
                return float(total or 0)
            elif method == 'count':
                return query.count()
        
        # 默认返回0
        return 0.0
    
    @staticmethod
    def execute_custom_formula(formula, user_ids, year, month):
        """执行自定义公式（简化版实现）"""
        # 这里可以实现一个公式解析器
        # 为了安全性，建议使用受限的表达式解析器
        try:
            # 简化实现：替换常用变量并计算
            # 实际实现应该使用更安全的公式解析器
            context = {
                'user_ids': user_ids,
                'year': year,
                'month': month
            }
            
            # 这里只是示例，实际需要实现安全的公式解析
            # 可以考虑使用专门的表达式引擎如 simpleeval
            return 0.0
            
        except Exception as e:
            import logging
            logging.error(f"执行自定义公式失败: {e}")
            return 0.0
    
    @staticmethod
    def calculate_achievement_rate(actual_value, target_value):
        """计算达成率"""
        if not target_value or target_value == 0:
            return 0.0

        return round((float(actual_value) / float(target_value)) * 100, 2)


class RolePerformanceTarget(db.Model):
    """角色绩效目标配置表 - 全局默认目标"""
    __tablename__ = 'role_performance_targets'

    id = Column(Integer, primary_key=True)
    role_code = Column(String(50), nullable=False, index=True)  # 角色代码
    year = Column(Integer, nullable=False)                       # 年份
    item_code = Column(String(50), nullable=False)               # 绩效项目代码

    # 目标值
    annual_target = Column(Numeric(15, 2))                       # 年度目标

    # 季度目标（可选，勾选后启用）
    enable_quarterly = Column(Boolean, default=False)
    q1_target = Column(Numeric(15, 2))                           # Q1目标
    q2_target = Column(Numeric(15, 2))                           # Q2目标
    q3_target = Column(Numeric(15, 2))                           # Q3目标
    q4_target = Column(Numeric(15, 2))                           # Q4目标

    # 月度目标（可选，勾选后启用）
    enable_monthly = Column(Boolean, default=False)
    monthly_targets = Column(JSON)                                # {"1": 10, "2": 12, ...}

    # 单位配置
    target_unit = Column(String(20), default='万元')              # 万元/个

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))

    # 关系
    creator = relationship('User', foreign_keys=[created_by])
    updater = relationship('User', foreign_keys=[updated_by])

    __table_args__ = (
        db.UniqueConstraint('role_code', 'year', 'item_code',
                           name='uq_role_perf_target_role_year_item'),
        db.Index('idx_role_perf_target_role_year', 'role_code', 'year'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'role_code': self.role_code,
            'year': self.year,
            'item_code': self.item_code,
            'annual_target': float(self.annual_target) if self.annual_target else None,
            'enable_quarterly': self.enable_quarterly,
            'q1_target': float(self.q1_target) if self.q1_target else None,
            'q2_target': float(self.q2_target) if self.q2_target else None,
            'q3_target': float(self.q3_target) if self.q3_target else None,
            'q4_target': float(self.q4_target) if self.q4_target else None,
            'enable_monthly': self.enable_monthly,
            'monthly_targets': self.monthly_targets,
            'target_unit': self.target_unit,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def get_quarterly_total(self):
        """获取季度目标合计"""
        if not self.enable_quarterly:
            return 0
        return sum([
            float(self.q1_target or 0),
            float(self.q2_target or 0),
            float(self.q3_target or 0),
            float(self.q4_target or 0)
        ])

    def get_monthly_total_by_quarter(self, quarter):
        """获取指定季度的月度目标合计"""
        if not self.enable_monthly or not self.monthly_targets:
            return 0
        months = {
            1: ['1', '2', '3'],
            2: ['4', '5', '6'],
            3: ['7', '8', '9'],
            4: ['10', '11', '12']
        }
        return sum([float(self.monthly_targets.get(m, 0) or 0) for m in months.get(quarter, [])])


class UserPerformanceTarget(db.Model):
    """用户绩效目标表 - 个人覆盖"""
    __tablename__ = 'user_performance_targets'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    year = Column(Integer, nullable=False)
    item_code = Column(String(50), nullable=False)

    # 覆盖值（NULL表示使用角色默认）
    annual_target_override = Column(Numeric(15, 2))
    enable_quarterly_override = Column(Boolean)
    q1_target_override = Column(Numeric(15, 2))
    q2_target_override = Column(Numeric(15, 2))
    q3_target_override = Column(Numeric(15, 2))
    q4_target_override = Column(Numeric(15, 2))
    enable_monthly_override = Column(Boolean)
    monthly_targets_override = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    updated_by = Column(Integer, ForeignKey('users.id'))

    # 关系
    user = relationship('User', foreign_keys=[user_id], backref='performance_target_overrides')
    creator = relationship('User', foreign_keys=[created_by])
    updater = relationship('User', foreign_keys=[updated_by])

    __table_args__ = (
        db.UniqueConstraint('user_id', 'year', 'item_code',
                           name='uq_user_perf_target_user_year_item'),
        db.Index('idx_user_perf_target_user_year', 'user_id', 'year'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'year': self.year,
            'item_code': self.item_code,
            'annual_target_override': float(self.annual_target_override) if self.annual_target_override else None,
            'enable_quarterly_override': self.enable_quarterly_override,
            'q1_target_override': float(self.q1_target_override) if self.q1_target_override else None,
            'q2_target_override': float(self.q2_target_override) if self.q2_target_override else None,
            'q3_target_override': float(self.q3_target_override) if self.q3_target_override else None,
            'q4_target_override': float(self.q4_target_override) if self.q4_target_override else None,
            'enable_monthly_override': self.enable_monthly_override,
            'monthly_targets_override': self.monthly_targets_override,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


def get_user_effective_target(user_id, year, item_code, period_type='annual', period=None):
    """
    获取用户有效目标值，优先级：
    1. 用户个人覆盖
    2. 角色默认配置
    3. 返回 None

    Args:
        user_id: 用户ID
        year: 年份
        item_code: 绩效项目代码
        period_type: 'annual', 'quarterly', 'monthly'
        period: 季度(1-4)或月份(1-12)

    Returns:
        目标值或 None
    """
    from app.models.user import User

    # 1. 检查个人覆盖
    user_target = UserPerformanceTarget.query.filter_by(
        user_id=user_id, year=year, item_code=item_code
    ).first()

    if user_target:
        if period_type == 'annual' and user_target.annual_target_override is not None:
            return float(user_target.annual_target_override)
        elif period_type == 'quarterly' and period:
            override = getattr(user_target, f'q{period}_target_override', None)
            if override is not None:
                return float(override)
        elif period_type == 'monthly' and period:
            if user_target.monthly_targets_override:
                value = user_target.monthly_targets_override.get(str(period))
                if value is not None:
                    return float(value)

    # 2. 查询角色默认
    user = User.query.get(user_id)
    if not user:
        return None

    role_target = RolePerformanceTarget.query.filter_by(
        role_code=user.role, year=year, item_code=item_code
    ).first()

    if role_target:
        if period_type == 'annual':
            return float(role_target.annual_target) if role_target.annual_target else None
        elif period_type == 'quarterly' and period:
            value = getattr(role_target, f'q{period}_target', None)
            return float(value) if value else None
        elif period_type == 'monthly' and period:
            if role_target.monthly_targets:
                value = role_target.monthly_targets.get(str(period))
                return float(value) if value else None

    return None