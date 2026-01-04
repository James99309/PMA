# -*- coding: utf-8 -*-
"""
薪资配置模型
包含职级配置、基础参数、阶梯规则、公式配置、团队配置、员工薪资配置等
"""

from app import db
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Numeric, ForeignKey, JSON, Boolean, UniqueConstraint, Index
from sqlalchemy.orm import relationship
import logging

logger = logging.getLogger(__name__)


class SalaryGradeConfig(db.Model):
    """职级薪资配置表"""
    __tablename__ = 'salary_grade_config'

    id = Column(Integer, primary_key=True)
    grade_code = Column(String(10), unique=True, nullable=False, index=True)  # L1, L2, M1, M2...
    grade_name = Column(String(50), nullable=False)  # 初级业务员, 主管...
    grade_type = Column(String(10), nullable=False)  # L=专业序列, M=管理序列

    annual_target = Column(Numeric(15, 2))  # 年度目标(万)
    monthly_base_salary = Column(Numeric(15, 2))  # 月基础工资
    monthly_performance_base = Column(Numeric(15, 2))  # 月绩效基数
    monthly_management_allowance = Column(Numeric(15, 2), default=0)  # 月管理津贴
    personal_weight = Column(Numeric(5, 2), default=1)  # 个人权重（M级使用）

    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    bandwidth = relationship('SalaryGradeBandwidth', backref='grade', uselist=False,
                            cascade='all, delete-orphan')
    employee_configs = relationship('EmployeeSalaryConfig', backref='grade', lazy='dynamic')

    def __init__(self, **kwargs):
        super(SalaryGradeConfig, self).__init__(**kwargs)
        if not self.created_at:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self):
        return {
            'id': self.id,
            'grade_code': self.grade_code,
            'grade_name': self.grade_name,
            'grade_type': self.grade_type,
            'annual_target': float(self.annual_target) if self.annual_target else None,
            'monthly_base_salary': float(self.monthly_base_salary) if self.monthly_base_salary else None,
            'monthly_performance_base': float(self.monthly_performance_base) if self.monthly_performance_base else None,
            'monthly_management_allowance': float(self.monthly_management_allowance) if self.monthly_management_allowance else 0,
            'personal_weight': float(self.personal_weight) if self.personal_weight else 1,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'bandwidth': self.bandwidth.to_dict() if self.bandwidth else None
        }


class SalaryGradeBandwidth(db.Model):
    """职级薪资带宽表 - 定义每个职级的薪资范围"""
    __tablename__ = 'salary_grade_bandwidth'

    id = Column(Integer, primary_key=True)
    grade_id = Column(Integer, ForeignKey('salary_grade_config.id'), nullable=False, unique=True)

    # 月基础工资带宽
    base_salary_min = Column(Numeric(15, 2))  # 最低
    base_salary_mid = Column(Numeric(15, 2))  # 中位值（职级默认值）
    base_salary_max = Column(Numeric(15, 2))  # 最高

    # 月绩效基数带宽
    performance_base_min = Column(Numeric(15, 2))
    performance_base_mid = Column(Numeric(15, 2))
    performance_base_max = Column(Numeric(15, 2))

    # 年度目标带宽
    target_min = Column(Numeric(15, 2))
    target_mid = Column(Numeric(15, 2))
    target_max = Column(Numeric(15, 2))

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'grade_id': self.grade_id,
            'base_salary_min': float(self.base_salary_min) if self.base_salary_min else None,
            'base_salary_mid': float(self.base_salary_mid) if self.base_salary_mid else None,
            'base_salary_max': float(self.base_salary_max) if self.base_salary_max else None,
            'performance_base_min': float(self.performance_base_min) if self.performance_base_min else None,
            'performance_base_mid': float(self.performance_base_mid) if self.performance_base_mid else None,
            'performance_base_max': float(self.performance_base_max) if self.performance_base_max else None,
            'target_min': float(self.target_min) if self.target_min else None,
            'target_mid': float(self.target_mid) if self.target_mid else None,
            'target_max': float(self.target_max) if self.target_max else None,
            'is_active': self.is_active
        }


class SalaryBaseParams(db.Model):
    """薪资基础参数配置表"""
    __tablename__ = 'salary_base_params'

    id = Column(Integer, primary_key=True)
    param_code = Column(String(50), unique=True, nullable=False, index=True)  # 参数代码
    param_name = Column(String(100), nullable=False)  # 参数名称
    param_value = Column(Numeric(15, 4))  # 参数值
    param_unit = Column(String(20))  # 单位（%/倍/元）
    description = Column(Text)  # 说明

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'param_code': self.param_code,
            'param_name': self.param_name,
            'param_value': float(self.param_value) if self.param_value else None,
            'param_unit': self.param_unit,
            'description': self.description,
            'is_active': self.is_active
        }


class SalaryStepRules(db.Model):
    """薪资阶梯规则配置表（通用）"""
    __tablename__ = 'salary_step_rules'

    id = Column(Integer, primary_key=True)
    rule_type = Column(String(50), nullable=False, index=True)  # performance_coefficient/commission_rate/commission_release/annual_bonus
    min_threshold = Column(Numeric(10, 4))  # 最低阈值
    max_threshold = Column(Numeric(10, 4))  # 最高阈值（NULL=无上限）
    coefficient = Column(Numeric(10, 4))  # 系数/比例
    description = Column(String(100))  # 说明

    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_step_rules_type_threshold', 'rule_type', 'min_threshold'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'rule_type': self.rule_type,
            'min_threshold': float(self.min_threshold) if self.min_threshold is not None else None,
            'max_threshold': float(self.max_threshold) if self.max_threshold is not None else None,
            'coefficient': float(self.coefficient) if self.coefficient is not None else None,
            'description': self.description,
            'sort_order': self.sort_order,
            'is_active': self.is_active
        }

    @staticmethod
    def get_coefficient(rule_type, value):
        """根据规则类型和值查找对应的系数"""
        rules = SalaryStepRules.query.filter_by(
            rule_type=rule_type,
            is_active=True
        ).order_by(SalaryStepRules.min_threshold.desc()).all()

        for rule in rules:
            min_val = float(rule.min_threshold) if rule.min_threshold is not None else 0
            if value >= min_val:
                return float(rule.coefficient) if rule.coefficient is not None else 0
        return 0


class SalaryFormulaConfig(db.Model):
    """薪资计算公式配置表"""
    __tablename__ = 'salary_formula_config'

    id = Column(Integer, primary_key=True)
    formula_code = Column(String(50), unique=True, nullable=False, index=True)  # 公式代码
    formula_name = Column(String(100), nullable=False)  # 公式名称
    formula_expression = Column(Text)  # 公式表达式
    description = Column(Text)  # 说明

    # 公式变量定义 (JSON)
    variables = Column(JSON)
    # 格式: [{"code": "personal_rate", "name": "个人完成率", "source": "quarterly_data.completion_rate"}]

    # 适用职级类型 (ALL=全部, L=专业序列, M=管理序列)
    applicable_grade_type = Column(String(10), default='ALL')

    # 结构化公式元素 (JSON)
    # 格式: [{"type": "variable", "code": "personal_rate"}, {"type": "operator", "value": "*"}, ...]
    formula_elements = Column(JSON)

    result_unit = Column(String(20))  # 结果单位（%/元/万）
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'formula_code': self.formula_code,
            'formula_name': self.formula_name,
            'formula_expression': self.formula_expression,
            'description': self.description,
            'variables': self.variables,
            'applicable_grade_type': self.applicable_grade_type or 'ALL',
            'formula_elements': self.formula_elements,
            'result_unit': self.result_unit,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @staticmethod
    def elements_to_expression(elements):
        """将结构化公式元素转换为表达式字符串"""
        if not elements:
            return ''

        parts = []
        for elem in elements:
            if elem.get('type') == 'variable':
                parts.append('{' + elem.get('code', '') + '}')
            elif elem.get('type') == 'operator':
                parts.append(elem.get('value', ''))
            elif elem.get('type') == 'number':
                parts.append(str(elem.get('value', '')))
            elif elem.get('type') == 'step':
                # STEP函数：STEP({variable}, "rule_type")
                var_code = elem.get('variable', '')
                rule_type = elem.get('rule_type', '')
                parts.append(f'STEP({{{var_code}}}, "{rule_type}")')
            elif elem.get('type') == 'paren':
                parts.append(elem.get('value', ''))

        return ' '.join(parts)


class SalesTeamConfig(db.Model):
    """销售团队配置表"""
    __tablename__ = 'sales_team_config'

    id = Column(Integer, primary_key=True)
    team_name = Column(String(100), nullable=False)  # 团队名称
    team_leader_id = Column(Integer, ForeignKey('users.id'))  # 团队负责人
    leader_grade = Column(String(10))  # 负责人职级

    # 团队目标（可选，也可从成员汇总）
    annual_target = Column(Numeric(15, 2))  # 团队年度目标(万)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    team_leader = relationship('User', foreign_keys=[team_leader_id], backref='led_teams')
    members = relationship('EmployeeSalaryConfig', backref='team', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'team_name': self.team_name,
            'team_leader_id': self.team_leader_id,
            'team_leader_name': self.team_leader.real_name if self.team_leader else None,
            'leader_grade': self.leader_grade,
            'annual_target': float(self.annual_target) if self.annual_target else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class EmployeeSalaryConfig(db.Model):
    """员工薪资配置表 - 支持个人覆盖全局配置，按年份存储"""
    __tablename__ = 'employee_salary_config'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    year = Column(Integer, nullable=False, index=True)  # 年份
    team_id = Column(Integer, ForeignKey('sales_team_config.id'))
    grade_id = Column(Integer, ForeignKey('salary_grade_config.id'))
    supervisor_id = Column(Integer, ForeignKey('users.id'))  # 上级ID

    # ========== 配置模式 ==========
    use_custom_config = Column(Boolean, default=False)  # 是否使用个人自定义配置

    # ========== 薪资带宽覆盖 ==========
    # NULL表示使用职级默认值，有值则覆盖
    monthly_base_salary_override = Column(Numeric(15, 2))  # 月基础工资覆盖
    monthly_performance_base_override = Column(Numeric(15, 2))  # 月绩效基数覆盖
    monthly_management_allowance_override = Column(Numeric(15, 2))  # 月管理津贴覆盖

    # ========== 目标值覆盖 ==========
    annual_target_override = Column(Numeric(15, 2))  # 个人年度目标(万)覆盖
    monthly_targets = Column(JSON)  # 月度目标配置 {"1": 10, "2": 12, ...} 单位：万元

    # ========== 权重覆盖 ==========
    personal_weight_override = Column(Numeric(5, 2))  # 个人权重覆盖（M级）

    # ========== 奖励比例覆盖 ==========
    commission_rate_multiplier = Column(Numeric(5, 2), default=1)  # 提成比例系数（1=100%，1.2=120%）
    bonus_multiplier = Column(Numeric(5, 2), default=1)  # 年终奖系数
    team_share_rate_override = Column(Numeric(5, 2))  # 团队分成比例覆盖

    # ========== 元数据 ==========
    config_notes = Column(Text)  # 配置备注（如调薪原因）
    configured_by = Column(Integer, ForeignKey('users.id'))  # 配置人
    configured_at = Column(DateTime)  # 配置时间

    # ========== AI分析配置 ==========
    ai_analysis_enabled = Column(Boolean, default=False)  # 是否开启AI分析

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship('User', foreign_keys=[user_id], backref='salary_configs')
    supervisor = relationship('User', foreign_keys=[supervisor_id], backref='subordinate_salary_configs')
    configured_by_user = relationship('User', foreign_keys=[configured_by])

    __table_args__ = (
        UniqueConstraint('user_id', 'year', name='uq_employee_salary_config_user_year'),
        Index('idx_employee_salary_config_user_year', 'user_id', 'year'),
    )

    def get_effective_value(self, field_name, default=None):
        """获取有效的配置值（个人覆盖或职级默认值）"""
        if self.use_custom_config:
            override_field = f"{field_name}_override"
            override_value = getattr(self, override_field, None)
            if override_value is not None:
                return float(override_value)

        # 返回职级默认值
        if self.grade:
            grade_value = getattr(self.grade, field_name, None)
            if grade_value is not None:
                return float(grade_value)

        return default

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.real_name if self.user else None,
            'year': self.year,
            'team_id': self.team_id,
            'team_name': self.team.team_name if self.team else None,
            'grade_id': self.grade_id,
            'grade_code': self.grade.grade_code if self.grade else None,
            'grade_name': self.grade.grade_name if self.grade else None,
            'supervisor_id': self.supervisor_id,
            'supervisor_name': self.supervisor.real_name if self.supervisor else None,
            'use_custom_config': self.use_custom_config,
            'monthly_base_salary_override': float(self.monthly_base_salary_override) if self.monthly_base_salary_override else None,
            'monthly_performance_base_override': float(self.monthly_performance_base_override) if self.monthly_performance_base_override else None,
            'monthly_management_allowance_override': float(self.monthly_management_allowance_override) if self.monthly_management_allowance_override else None,
            'annual_target_override': float(self.annual_target_override) if self.annual_target_override else None,
            'monthly_targets': self.monthly_targets,
            'personal_weight_override': float(self.personal_weight_override) if self.personal_weight_override else None,
            'commission_rate_multiplier': float(self.commission_rate_multiplier) if self.commission_rate_multiplier else 1,
            'bonus_multiplier': float(self.bonus_multiplier) if self.bonus_multiplier else 1,
            'team_share_rate_override': float(self.team_share_rate_override) if self.team_share_rate_override else None,
            'config_notes': self.config_notes,
            'configured_by': self.configured_by,
            'configured_by_name': self.configured_by_user.real_name if self.configured_by_user else None,
            'configured_at': self.configured_at.isoformat() if self.configured_at else None,
            'is_active': self.is_active,
            # AI分析配置
            'ai_analysis_enabled': self.ai_analysis_enabled or False,
            # 有效值（考虑覆盖后的实际值）
            'effective_monthly_base_salary': self.get_effective_value('monthly_base_salary'),
            'effective_monthly_performance_base': self.get_effective_value('monthly_performance_base'),
            'effective_annual_target': self.get_effective_value('annual_target'),
            'effective_personal_weight': self.get_effective_value('personal_weight', 1)
        }


class QuarterlyPerformanceData(db.Model):
    """季度业绩数据表"""
    __tablename__ = 'quarterly_performance_data'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    year = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False)  # 1-4

    # 业绩数据（可从系统自动采集或手工录入）
    achievement = Column(Numeric(15, 2))  # 季度业绩(万)
    completion_rate = Column(Numeric(10, 4))  # 完成率
    high_price_ratio = Column(Numeric(10, 4))  # 高批价占比
    high_price_rate = Column(Numeric(10, 4))  # 高批价率

    data_source = Column(String(20), default='system')  # system/manual
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship('User', backref='quarterly_performances')

    __table_args__ = (
        UniqueConstraint('user_id', 'year', 'quarter', name='uq_user_year_quarter'),
        Index('idx_quarterly_performance_user_year', 'user_id', 'year'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.real_name if self.user else None,
            'year': self.year,
            'quarter': self.quarter,
            'achievement': float(self.achievement) if self.achievement else 0,
            'completion_rate': float(self.completion_rate) if self.completion_rate else 0,
            'high_price_ratio': float(self.high_price_ratio) if self.high_price_ratio else 0,
            'high_price_rate': float(self.high_price_rate) if self.high_price_rate else 0,
            'data_source': self.data_source
        }


class SalaryPeriodSnapshot(db.Model):
    """薪资周期快照表 - 保存已结算的薪资数据，支持财务调整"""
    __tablename__ = 'salary_period_snapshots'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    year = Column(Integer, nullable=False)
    period_type = Column(String(20), nullable=False)  # 'monthly' 或 'quarterly'
    period_value = Column(Integer, nullable=False)    # 月份1-12 或 季度1-4

    # ========== 系统计算值（不可修改，保留审计） ==========
    # 基础工资（月度）
    calculated_base_salary = Column(Numeric(12, 2))
    # 管理津贴（月度）
    calculated_management_allowance = Column(Numeric(12, 2))
    # 绩效工资（季度发放）
    calculated_performance_salary = Column(Numeric(12, 2))
    # 个人提成（季度发放）
    calculated_commission = Column(Numeric(12, 2))
    # 团队分成（季度发放，M级）
    calculated_team_share = Column(Numeric(12, 2))
    # 本期合计
    calculated_total = Column(Numeric(12, 2))

    # ========== 财务调整值（可修改） ==========
    # NULL表示使用计算值，有值则覆盖
    adjusted_base_salary = Column(Numeric(12, 2))
    adjusted_management_allowance = Column(Numeric(12, 2))
    adjusted_performance_salary = Column(Numeric(12, 2))
    adjusted_commission = Column(Numeric(12, 2))
    adjusted_team_share = Column(Numeric(12, 2))
    adjusted_total = Column(Numeric(12, 2))

    # ========== 计算参数快照（用于审计追溯） ==========
    # 存储计算时使用的关键参数，便于追溯
    calculation_params = Column(JSON)
    # 格式: {
    #   "grade_code": "L2",
    #   "annual_target": 350,
    #   "monthly_target": 29.17,
    #   "completion_rate": 0.85,
    #   "performance_coefficient": 0.8,
    #   "commission_multiplier": 1.0,
    #   ...
    # }

    # ========== 调整信息 ==========
    adjustment_reason = Column(Text)  # 调整原因
    adjusted_by = Column(Integer, ForeignKey('users.id'))
    adjusted_at = Column(DateTime)

    # ========== 状态管理 ==========
    status = Column(String(20), default='draft')
    # draft: 草稿（可重新计算）
    # confirmed: 已确认（锁定计算值）
    # published: 已发布（锁定所有值）

    confirmed_at = Column(DateTime)
    confirmed_by = Column(Integer, ForeignKey('users.id'))
    published_at = Column(DateTime)
    published_by = Column(Integer, ForeignKey('users.id'))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user = relationship('User', foreign_keys=[user_id], backref='salary_snapshots')
    adjuster = relationship('User', foreign_keys=[adjusted_by])
    confirmer = relationship('User', foreign_keys=[confirmed_by])
    publisher = relationship('User', foreign_keys=[published_by])

    __table_args__ = (
        UniqueConstraint('user_id', 'year', 'period_type', 'period_value',
                        name='uq_salary_snapshot_user_period'),
        Index('idx_salary_snapshot_user_year', 'user_id', 'year'),
        Index('idx_salary_snapshot_status', 'status'),
    )

    def get_final_value(self, field_name):
        """获取最终值（调整值优先，否则使用计算值）"""
        adjusted = getattr(self, f'adjusted_{field_name}', None)
        if adjusted is not None:
            return float(adjusted)
        calculated = getattr(self, f'calculated_{field_name}', None)
        return float(calculated) if calculated is not None else 0

    @property
    def final_base_salary(self):
        return self.get_final_value('base_salary')

    @property
    def final_management_allowance(self):
        return self.get_final_value('management_allowance')

    @property
    def final_performance_salary(self):
        return self.get_final_value('performance_salary')

    @property
    def final_commission(self):
        return self.get_final_value('commission')

    @property
    def final_team_share(self):
        return self.get_final_value('team_share')

    @property
    def final_total(self):
        return self.get_final_value('total')

    @property
    def has_adjustment(self):
        """检查是否有财务调整"""
        return any([
            self.adjusted_base_salary is not None,
            self.adjusted_management_allowance is not None,
            self.adjusted_performance_salary is not None,
            self.adjusted_commission is not None,
            self.adjusted_team_share is not None,
            self.adjusted_total is not None,
        ])

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.real_name if self.user else None,
            'year': self.year,
            'period_type': self.period_type,
            'period_value': self.period_value,
            'period_label': self._get_period_label(),
            # 计算值
            'calculated_base_salary': float(self.calculated_base_salary) if self.calculated_base_salary else 0,
            'calculated_management_allowance': float(self.calculated_management_allowance) if self.calculated_management_allowance else 0,
            'calculated_performance_salary': float(self.calculated_performance_salary) if self.calculated_performance_salary else 0,
            'calculated_commission': float(self.calculated_commission) if self.calculated_commission else 0,
            'calculated_team_share': float(self.calculated_team_share) if self.calculated_team_share else 0,
            'calculated_total': float(self.calculated_total) if self.calculated_total else 0,
            # 调整值
            'adjusted_base_salary': float(self.adjusted_base_salary) if self.adjusted_base_salary else None,
            'adjusted_management_allowance': float(self.adjusted_management_allowance) if self.adjusted_management_allowance else None,
            'adjusted_performance_salary': float(self.adjusted_performance_salary) if self.adjusted_performance_salary else None,
            'adjusted_commission': float(self.adjusted_commission) if self.adjusted_commission else None,
            'adjusted_team_share': float(self.adjusted_team_share) if self.adjusted_team_share else None,
            'adjusted_total': float(self.adjusted_total) if self.adjusted_total else None,
            # 最终值
            'final_base_salary': self.final_base_salary,
            'final_management_allowance': self.final_management_allowance,
            'final_performance_salary': self.final_performance_salary,
            'final_commission': self.final_commission,
            'final_team_share': self.final_team_share,
            'final_total': self.final_total,
            # 状态
            'has_adjustment': self.has_adjustment,
            'adjustment_reason': self.adjustment_reason,
            'adjusted_by': self.adjusted_by,
            'adjusted_by_name': self.adjuster.real_name if self.adjuster else None,
            'adjusted_at': self.adjusted_at.isoformat() if self.adjusted_at else None,
            'status': self.status,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None,
            'confirmed_by_name': self.confirmer.real_name if self.confirmer else None,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'published_by_name': self.publisher.real_name if self.publisher else None,
            'calculation_params': self.calculation_params,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def _get_period_label(self):
        """获取周期标签"""
        if self.period_type == 'monthly':
            return f'{self.year}年{self.period_value}月'
        elif self.period_type == 'quarterly':
            return f'{self.year}年Q{self.period_value}'
        return f'{self.year}-{self.period_value}'


class SalaryCalculationResult(db.Model):
    """薪资计算结果表"""
    __tablename__ = 'salary_calculation_result'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    year = Column(Integer, nullable=False)

    # 基础信息
    team_id = Column(Integer, ForeignKey('sales_team_config.id'))
    grade_code = Column(String(10))

    # 业绩汇总
    annual_target = Column(Numeric(15, 2))  # 年度目标(万)
    annual_achievement = Column(Numeric(15, 2))  # 年度业绩(万)
    personal_completion_rate = Column(Numeric(10, 4))  # 个人完成率
    team_completion_rate = Column(Numeric(10, 4))  # 团队完成率
    personal_weight = Column(Numeric(5, 2))  # 个人权重
    team_weight = Column(Numeric(5, 2))  # 团队权重
    comprehensive_completion_rate = Column(Numeric(10, 4))  # 综合完成率

    # 薪资明细（万元）
    annual_base_salary = Column(Numeric(15, 4))  # 年基础工资
    management_allowance = Column(Numeric(15, 4))  # 管理津贴
    performance_salary = Column(Numeric(15, 4))  # 绩效工资
    personal_commission_base = Column(Numeric(15, 4))  # 个人提成基数
    team_commission_share = Column(Numeric(15, 4))  # 团队分成
    commission_total = Column(Numeric(15, 4))  # 提成合计
    commission_release_rate = Column(Numeric(10, 4))  # 发放比例
    final_commission = Column(Numeric(15, 4))  # 最终提成
    annual_bonus = Column(Numeric(15, 4))  # 年终奖

    # 汇总
    annual_total_income = Column(Numeric(15, 4))  # 年总收入
    total_cost = Column(Numeric(15, 4))  # 总成本
    net_contribution = Column(Numeric(15, 4))  # 净贡献
    efficiency_ratio = Column(Numeric(10, 4))  # 人效比

    # 状态
    status = Column(String(20), default='draft')  # draft/confirmed/paid
    calculated_at = Column(DateTime, default=datetime.utcnow)
    confirmed_by = Column(Integer, ForeignKey('users.id'))
    confirmed_at = Column(DateTime)

    # 关系
    user = relationship('User', foreign_keys=[user_id], backref='salary_results')
    team = relationship('SalesTeamConfig', backref='salary_results')
    confirmer = relationship('User', foreign_keys=[confirmed_by])

    __table_args__ = (
        UniqueConstraint('user_id', 'year', name='uq_salary_result_user_year'),
        Index('idx_salary_result_year_status', 'year', 'status'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.real_name if self.user else None,
            'year': self.year,
            'team_id': self.team_id,
            'team_name': self.team.team_name if self.team else None,
            'grade_code': self.grade_code,
            'annual_target': float(self.annual_target) if self.annual_target else 0,
            'annual_achievement': float(self.annual_achievement) if self.annual_achievement else 0,
            'personal_completion_rate': float(self.personal_completion_rate) if self.personal_completion_rate else 0,
            'team_completion_rate': float(self.team_completion_rate) if self.team_completion_rate else 0,
            'personal_weight': float(self.personal_weight) if self.personal_weight else 1,
            'team_weight': float(self.team_weight) if self.team_weight else 0,
            'comprehensive_completion_rate': float(self.comprehensive_completion_rate) if self.comprehensive_completion_rate else 0,
            'annual_base_salary': float(self.annual_base_salary) if self.annual_base_salary else 0,
            'management_allowance': float(self.management_allowance) if self.management_allowance else 0,
            'performance_salary': float(self.performance_salary) if self.performance_salary else 0,
            'personal_commission_base': float(self.personal_commission_base) if self.personal_commission_base else 0,
            'team_commission_share': float(self.team_commission_share) if self.team_commission_share else 0,
            'commission_total': float(self.commission_total) if self.commission_total else 0,
            'commission_release_rate': float(self.commission_release_rate) if self.commission_release_rate else 0,
            'final_commission': float(self.final_commission) if self.final_commission else 0,
            'annual_bonus': float(self.annual_bonus) if self.annual_bonus else 0,
            'annual_total_income': float(self.annual_total_income) if self.annual_total_income else 0,
            'total_cost': float(self.total_cost) if self.total_cost else 0,
            'net_contribution': float(self.net_contribution) if self.net_contribution else 0,
            'efficiency_ratio': float(self.efficiency_ratio) if self.efficiency_ratio else 0,
            'status': self.status,
            'calculated_at': self.calculated_at.isoformat() if self.calculated_at else None,
            'confirmed_by': self.confirmed_by,
            'confirmed_by_name': self.confirmer.real_name if self.confirmer else None,
            'confirmed_at': self.confirmed_at.isoformat() if self.confirmed_at else None
        }
