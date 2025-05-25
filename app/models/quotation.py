from datetime import datetime
from zoneinfo import ZoneInfo
from app import db
from sqlalchemy import event, Date, text
from sqlalchemy.exc import SQLAlchemyError
from app.models.project import Project
import random
import string

class Quotation(db.Model):
    __tablename__ = 'quotations'

    id = db.Column(db.Integer, primary_key=True)
    quotation_number = db.Column(db.String(20), unique=True, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'))
    amount = db.Column(db.Float)
    project_stage = db.Column(db.String(20))  # 项目阶段：发现、品牌植入、招标前、招标中、中标、失败
    project_type = db.Column(db.String(20))   # 项目类型：销售重点、渠道跟进
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo('Asia/Shanghai')))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 所有者字段（关联到用户表）
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    owner = db.relationship('User', backref=db.backref('quotations', lazy='dynamic'))
    
    # 关联关系
    project = db.relationship('Project', back_populates='quotations')
    contact = db.relationship('Contact', backref='quotations')
    details = db.relationship('QuotationDetail', backref='quotation', cascade='all, delete-orphan', 
                             order_by='QuotationDetail.id')  # 按明细ID排序，保持添加顺序

    def __init__(self, **kwargs):
        if 'quotation_number' not in kwargs:
            kwargs['quotation_number'] = self.generate_quotation_number()
        super(Quotation, self).__init__(**kwargs)

    def generate_quotation_number(self):
        # 生成格式：QU + 年份(4位) + 月份(2位) + "-" + 序号(3位)
        year = str(datetime.now().year)  # 使用4位年份
        month = str(datetime.now().month).zfill(2)
        prefix = f"QU{year}{month}-"
        
        # 查找当前年月最大的序号
        latest_quotation = Quotation.query.filter(
            Quotation.quotation_number.like(f"{prefix}%")
        ).order_by(Quotation.quotation_number.desc()).first()
        
        if latest_quotation:
            # 从最近的报价单编号中提取序号部分
            try:
                latest_sequence = int(latest_quotation.quotation_number.split('-')[1])
                sequence = latest_sequence + 1
            except (ValueError, IndexError):
                # 如果提取序号失败，则从001开始
                sequence = 1
        else:
            # 当月第一个报价单
            sequence = 1
        
        # 格式化为三位数
        formatted_sequence = str(sequence).zfill(3)
        number = f"{prefix}{formatted_sequence}"
        
        return number

    def __repr__(self):
        return f'<Quotation {self.quotation_number}>'

    @property
    def formatted_amount(self):
        """返回格式化的金额"""
        return '{:,.2f}'.format(self.amount) if self.amount else '0.00'

    @property
    def formatted_created_at(self):
        """返回格式化的创建时间"""
        return self.created_at.strftime('%Y-%m-%d') if self.created_at else ''

    @property
    def formatted_updated_at(self):
        """返回格式化的更新时间"""
        return self.updated_at.strftime('%Y-%m-%d') if self.updated_at else ''

# 添加SQLAlchemy事件监听器
@event.listens_for(Quotation, 'after_insert')
@event.listens_for(Quotation, 'after_update')
def update_project_quotation(mapper, connection, target):
    """在报价单保存或更新后自动更新项目报价总额和更新时间（北京时间）"""
    try:
        if target.project_id:
            now = datetime.now(ZoneInfo('Asia/Shanghai'))
            sql = text("""
                UPDATE projects 
                SET quotation_customer = (
                    SELECT COALESCE(SUM(amount), 0.0) 
                    FROM quotations 
                    WHERE project_id = :project_id
                ),
                updated_at = :now
                WHERE id = :project_id
            """)
            connection.execute(sql, {"project_id": target.project_id, "now": now})
    except Exception as e:
        print(f"更新项目报价总额时发生错误: {str(e)}")

@event.listens_for(Quotation, 'after_delete')
def update_project_quotation_on_delete(mapper, connection, target):
    """在报价单删除后自动更新项目报价总额和更新时间（北京时间）"""
    try:
        if target.project_id:
            now = datetime.now(ZoneInfo('Asia/Shanghai'))
            sql = text("""
                UPDATE projects 
                SET quotation_customer = (
                    SELECT COALESCE(SUM(amount), 0.0) 
                    FROM quotations 
                    WHERE project_id = :project_id
                ),
                updated_at = :now
                WHERE id = :project_id
            """)
            connection.execute(sql, {"project_id": target.project_id, "now": now})
    except Exception as e:
        print(f"更新项目报价总额时发生错误: {str(e)}")

class QuotationDetail(db.Model):
    __tablename__ = 'quotation_details'
    
    id = db.Column(db.Integer, primary_key=True)
    quotation_id = db.Column(db.Integer, db.ForeignKey('quotations.id'))
    product_name = db.Column(db.String(100))
    product_model = db.Column(db.String(100))
    product_desc = db.Column(db.Text)
    brand = db.Column(db.String(50))
    unit = db.Column(db.String(20))
    quantity = db.Column(db.Integer, default=1)
    discount = db.Column(db.Float, default=1.0)  # 折扣率，1.0表示无折扣
    market_price = db.Column(db.Float)  # 市场价
    unit_price = db.Column(db.Float)  # 单价（计算得出）
    total_price = db.Column(db.Float)  # 总价（计算得出）
    product_mn = db.Column(db.String(100))  # 产品料号
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def calculate_prices(self):
        """计算单价和总价"""
        self.unit_price = self.market_price * self.discount
        self.total_price = self.unit_price * self.quantity 