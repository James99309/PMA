"""
数据源配置模型
用于绩效系统的数据表和字段管理
"""

from app import db
from datetime import datetime
import json


class DataTableConfig(db.Model):
    """数据表配置"""
    __tablename__ = 'data_table_config'
    
    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(100), nullable=False, unique=True, comment='数据表名')
    display_name = db.Column(db.String(200), nullable=False, comment='显示名称')
    description = db.Column(db.Text, comment='表描述')
    category = db.Column(db.String(50), comment='表分类：business/system/reference')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    is_performance_source = db.Column(db.Boolean, default=True, comment='是否可用作绩效数据源')
    
    # 表统计信息
    total_records = db.Column(db.Integer, default=0, comment='记录总数')
    last_updated = db.Column(db.DateTime, comment='数据最后更新时间')
    
    # 系统字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # 关联字段配置
    field_configs = db.relationship('DataFieldConfig', backref='table_config', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'table_name': self.table_name,
            'display_name': self.display_name,
            'description': self.description,
            'category': self.category,
            'is_active': self.is_active,
            'is_performance_source': self.is_performance_source,
            'total_records': self.total_records,
            'field_count': self.field_configs.count(),
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class DataFieldConfig(db.Model):
    """数据字段配置"""
    __tablename__ = 'data_field_config'
    
    id = db.Column(db.Integer, primary_key=True)
    table_config_id = db.Column(db.Integer, db.ForeignKey('data_table_config.id'), nullable=False)
    field_name = db.Column(db.String(100), nullable=False, comment='字段名')
    display_name = db.Column(db.String(200), nullable=False, comment='显示名称')
    description = db.Column(db.Text, comment='字段描述')
    
    # 字段属性
    data_type = db.Column(db.String(50), nullable=False, comment='数据类型')
    is_nullable = db.Column(db.Boolean, default=True, comment='是否可为空')
    is_primary_key = db.Column(db.Boolean, default=False, comment='是否主键')
    is_foreign_key = db.Column(db.Boolean, default=False, comment='是否外键')
    foreign_table = db.Column(db.String(100), comment='外键关联表')
    foreign_field = db.Column(db.String(100), comment='外键关联字段')
    
    # 业务属性
    is_numeric = db.Column(db.Boolean, default=False, comment='是否数值字段')
    is_monetary = db.Column(db.Boolean, default=False, comment='是否金额字段')
    is_date = db.Column(db.Boolean, default=False, comment='是否日期字段')
    is_aggregatable = db.Column(db.Boolean, default=False, comment='是否可聚合统计')
    is_filterable = db.Column(db.Boolean, default=True, comment='是否可过滤')
    
    # 绩效相关
    is_performance_metric = db.Column(db.Boolean, default=False, comment='是否绩效指标')
    performance_category = db.Column(db.String(50), comment='绩效分类：sales/customer/project/quality')
    calculation_priority = db.Column(db.Integer, default=0, comment='计算优先级')
    
    # 显示配置
    display_format = db.Column(db.String(50), comment='显示格式')
    default_unit = db.Column(db.String(20), comment='默认单位')
    decimal_places = db.Column(db.Integer, default=2, comment='小数位数')
    
    # 字段统计信息（可选）
    sample_values = db.Column(db.Text, comment='样本值JSON')
    value_range = db.Column(db.Text, comment='值范围JSON')
    
    # 系统字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # 唯一约束：同一个表中字段名不能重复
    __table_args__ = (
        db.UniqueConstraint('table_config_id', 'field_name', name='uq_table_field'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'table_config_id': self.table_config_id,
            'field_name': self.field_name,
            'display_name': self.display_name,
            'description': self.description,
            'data_type': self.data_type,
            'is_nullable': self.is_nullable,
            'is_primary_key': self.is_primary_key,
            'is_foreign_key': self.is_foreign_key,
            'foreign_table': self.foreign_table,
            'foreign_field': self.foreign_field,
            'is_numeric': self.is_numeric,
            'is_monetary': self.is_monetary,
            'is_date': self.is_date,
            'is_aggregatable': self.is_aggregatable,
            'is_filterable': self.is_filterable,
            'is_performance_metric': self.is_performance_metric,
            'performance_category': self.performance_category,
            'calculation_priority': self.calculation_priority,
            'display_format': self.display_format,
            'default_unit': self.default_unit,
            'decimal_places': self.decimal_places,
            'sample_values': json.loads(self.sample_values) if self.sample_values else None,
            'value_range': json.loads(self.value_range) if self.value_range else None
        }
    
    @property
    def full_field_name(self):
        """返回完整字段名：table_name.field_name"""
        return f"{self.table_config.table_name}.{self.field_name}"
    
    @property
    def formula_reference(self):
        """返回公式中的引用格式"""
        return f"{{{self.table_config.table_name}.{self.field_name}}}"


class FormulaTemplate(db.Model):
    """公式模板扩展"""
    __tablename__ = 'formula_templates_extended'
    
    id = db.Column(db.Integer, primary_key=True)
    template_name = db.Column(db.String(100), nullable=False, comment='模板名称')
    template_category = db.Column(db.String(50), comment='模板分类')
    description = db.Column(db.Text, comment='模板描述')
    
    # 公式定义
    formula_expression = db.Column(db.Text, nullable=False, comment='公式表达式')
    required_tables = db.Column(db.Text, comment='需要的数据表JSON')
    required_fields = db.Column(db.Text, comment='需要的字段JSON')
    
    # 模板配置
    result_type = db.Column(db.String(50), default='numeric', comment='结果类型：numeric/percentage/count')
    result_unit = db.Column(db.String(20), comment='结果单位')
    is_system_template = db.Column(db.Boolean, default=False, comment='是否系统模板')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    
    # 使用统计
    usage_count = db.Column(db.Integer, default=0, comment='使用次数')
    last_used_at = db.Column(db.DateTime, comment='最后使用时间')
    
    # 系统字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'template_name': self.template_name,
            'template_category': self.template_category,
            'description': self.description,
            'formula_expression': self.formula_expression,
            'required_tables': json.loads(self.required_tables) if self.required_tables else [],
            'required_fields': json.loads(self.required_fields) if self.required_fields else [],
            'result_type': self.result_type,
            'result_unit': self.result_unit,
            'is_system_template': self.is_system_template,
            'is_active': self.is_active,
            'usage_count': self.usage_count,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None
        }


class DataSourceInitializer:
    """数据源初始化器 - 自动发现并配置数据表和字段"""
    
    def __init__(self):
        self.business_tables = {
            # 核心业务表
            'quotations': {
                'display_name': '报价单',
                'description': '项目报价单信息',
                'category': 'business'
            },
            'pricing_orders': {
                'display_name': '批价单',
                'description': '批价订单信息',
                'category': 'business'
            },
            'projects': {
                'display_name': '项目',
                'description': '项目基础信息',
                'category': 'business'
            },
            'companies': {
                'display_name': '公司客户',
                'description': '客户公司信息',
                'category': 'business'
            },
            'contacts': {
                'display_name': '联系人',
                'description': '客户联系人信息',
                'category': 'business'
            },
            'products': {
                'display_name': '产品',
                'description': '产品信息',
                'category': 'reference'
            },
            'users': {
                'display_name': '用户',
                'description': '系统用户信息',
                'category': 'system'
            },
            'expenses': {
                'display_name': '费用',
                'description': '费用记录',
                'category': 'business'
            },
            'settlements': {
                'display_name': '结算',
                'description': '结算信息',
                'category': 'business'
            }
        }
        
        self.performance_fields = {
            # 金额相关字段
            'amount': {'is_monetary': True, 'is_aggregatable': True, 'performance_category': 'sales'},
            'pricing_total_amount': {'is_monetary': True, 'is_aggregatable': True, 'performance_category': 'sales'},
            'settlement_total_amount': {'is_monetary': True, 'is_aggregatable': True, 'performance_category': 'sales'},
            'implant_total_amount': {'is_monetary': True, 'is_aggregatable': True, 'performance_category': 'sales'},
            'quotation_customer': {'is_monetary': True, 'is_aggregatable': True, 'performance_category': 'sales'},
            
            # 计数相关字段
            'id': {'is_aggregatable': True, 'performance_category': 'general'},
            
            # 日期相关字段
            'created_at': {'is_date': True, 'is_filterable': True, 'performance_category': 'general'},
            'updated_at': {'is_date': True, 'is_filterable': True, 'performance_category': 'general'},
            'approved_at': {'is_date': True, 'is_filterable': True, 'performance_category': 'general'},
            'report_time': {'is_date': True, 'is_filterable': True, 'performance_category': 'general'},
            
            # 状态相关字段  
            'status': {'is_filterable': True, 'performance_category': 'quality'},
            'approval_status': {'is_filterable': True, 'performance_category': 'quality'},
            'current_stage': {'is_filterable': True, 'performance_category': 'project'},
            'project_type': {'is_filterable': True, 'performance_category': 'project'},
        }
    
    def discover_and_create_configs(self):
        """自动发现数据库表和字段，创建配置"""
        from sqlalchemy import text
        
        try:
            # 获取所有业务表的信息
            query = text("""
                SELECT 
                    t.table_name,
                    COUNT(c.column_name) as column_count,
                    COALESCE(
                        (SELECT reltuples::bigint 
                         FROM pg_class 
                         WHERE relname = t.table_name), 0
                    ) as estimated_rows
                FROM information_schema.tables t
                LEFT JOIN information_schema.columns c ON t.table_name = c.table_name
                WHERE t.table_schema = 'public' 
                AND t.table_type = 'BASE TABLE'
                AND t.table_name NOT LIKE '%alembic%'
                AND t.table_name NOT LIKE '%migration%'
                GROUP BY t.table_name, t.table_name
                ORDER BY t.table_name
            """)
            
            result = db.session.execute(query).fetchall()
            
            for row in result:
                table_name = row[0]
                column_count = row[1]
                estimated_rows = row[2]
                
                # 只处理我们定义的业务表
                if table_name not in self.business_tables:
                    continue
                
                table_info = self.business_tables[table_name]
                
                # 创建或更新表配置
                table_config = DataTableConfig.query.filter_by(table_name=table_name).first()
                if not table_config:
                    table_config = DataTableConfig(
                        table_name=table_name,
                        display_name=table_info['display_name'],
                        description=table_info['description'],
                        category=table_info['category'],
                        total_records=estimated_rows,
                        last_updated=datetime.utcnow()
                    )
                    db.session.add(table_config)
                    db.session.flush()  # 获取ID
                
                # 获取字段信息
                field_query = text("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns 
                    WHERE table_name = :table_name
                    AND table_schema = 'public'
                    ORDER BY ordinal_position
                """)
                
                field_result = db.session.execute(field_query, {'table_name': table_name}).fetchall()
                
                for field_row in field_result:
                    field_name = field_row[0]
                    data_type = field_row[1]
                    is_nullable = field_row[2] == 'YES'
                    
                    # 检查字段是否已存在
                    field_config = DataFieldConfig.query.filter_by(
                        table_config_id=table_config.id,
                        field_name=field_name
                    ).first()
                    
                    if not field_config:
                        # 分析字段属性
                        field_props = self._analyze_field_properties(field_name, data_type)
                        
                        field_config = DataFieldConfig(
                            table_config_id=table_config.id,
                            field_name=field_name,
                            display_name=self._generate_display_name(field_name),
                            data_type=data_type,
                            is_nullable=is_nullable,
                            is_primary_key=(field_name == 'id'),
                            is_foreign_key=field_name.endswith('_id'),
                            **field_props
                        )
                        
                        db.session.add(field_config)
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"数据源初始化失败: {e}")
            return False
    
    def _analyze_field_properties(self, field_name, data_type):
        """分析字段属性"""
        props = {
            'is_numeric': data_type in ['integer', 'bigint', 'double precision', 'numeric', 'real'],
            'is_monetary': False,
            'is_date': data_type in ['timestamp with time zone', 'timestamp without time zone', 'date'],
            'is_aggregatable': False,
            'is_performance_metric': False,
            'performance_category': None,
            'display_format': None,
            'default_unit': None
        }
        
        # 检查是否是绩效相关字段
        if field_name in self.performance_fields:
            field_config = self.performance_fields[field_name]
            props.update({
                'is_monetary': field_config.get('is_monetary', False),
                'is_aggregatable': field_config.get('is_aggregatable', False),
                'is_performance_metric': True,
                'performance_category': field_config.get('performance_category')
            })
        
        # 基于字段名推断属性
        if 'amount' in field_name.lower() or 'price' in field_name.lower():
            props.update({
                'is_monetary': True,
                'is_aggregatable': True,
                'is_performance_metric': True,
                'performance_category': 'sales',
                'default_unit': '元',
                'decimal_places': 2
            })
        
        if field_name == 'id':
            props.update({
                'is_aggregatable': True,
                'is_performance_metric': True,
                'performance_category': 'general'
            })
        
        return props
    
    def _generate_display_name(self, field_name):
        """生成字段显示名称"""
        name_mapping = {
            'id': 'ID',
            'amount': '金额',
            'pricing_total_amount': '批价总金额',
            'settlement_total_amount': '结算总金额',
            'implant_total_amount': '植入总金额',
            'quotation_customer': '报价金额',
            'created_at': '创建时间',
            'updated_at': '更新时间',
            'approved_at': '审批时间',
            'status': '状态',
            'approval_status': '审批状态',
            'current_stage': '当前阶段',
            'project_type': '项目类型',
            'project_name': '项目名称',
            'company_name': '公司名称',
            'quotation_number': '报价单号',
            'order_number': '订单号',
            'owner_id': '负责人ID',
            'project_id': '项目ID'
        }
        
        return name_mapping.get(field_name, field_name.replace('_', ' ').title())