from datetime import datetime
from zoneinfo import ZoneInfo
from app import db
from sqlalchemy import event, Date, text
from sqlalchemy.exc import SQLAlchemyError
from app.models.project import Project
import random
import string

class QuotationApprovalStatus:
    """报价审核状态常量"""
    PENDING = "pending"  # 待审核
    DISCOVER_APPROVED = "discover_approved"  # 发现阶段审核
    EMBED_APPROVED = "embed_approved"  # 植入阶段审核
    PRE_TENDER_APPROVED = "pre_tender_approved"  # 招标前审核
    TENDERING_APPROVED = "tendering_approved"  # 招标中审核
    AWARDED_APPROVED = "awarded_approved"  # 中标审核
    QUOTED_APPROVED = "quoted_approved"  # 批价审核
    SIGNED_APPROVED = "signed_approved"  # 签约审核
    REJECTED = "rejected"  # 审核被驳回

    # 阶段到审核状态的映射
    STAGE_TO_APPROVAL = {
        'discover': 'discover_approved',
        'embed': 'embed_approved', 
        'pre_tender': 'pre_tender_approved',
        'tendering': 'tendering_approved',
        'awarded': 'awarded_approved',
        'quoted': 'quoted_approved',
        'signed': 'signed_approved'
    }

    # 审核状态标签
    STATUS_LABELS = {
        'pending': {'zh': '待审核', 'color': '#6c757d'},
        'discover_approved': {'zh': '发现审核', 'color': '#17a2b8'},
        'embed_approved': {'zh': '植入审核', 'color': '#007bff'},
        'pre_tender_approved': {'zh': '招标前审核', 'color': '#28a745'},
        'tendering_approved': {'zh': '招标中审核', 'color': '#ffc107'},
        'awarded_approved': {'zh': '中标审核', 'color': '#fd7e14'},
        'quoted_approved': {'zh': '批价审核', 'color': '#e83e8c'},
        'signed_approved': {'zh': '签约审核', 'color': '#6f42c1'},
        'rejected': {'zh': '审核驳回', 'color': '#dc3545'}
    }

    @classmethod
    def get_approval_status_by_stage(cls, stage):
        """根据项目阶段获取对应的审核状态"""
        return cls.STAGE_TO_APPROVAL.get(stage)

    @classmethod
    def get_status_label(cls, status):
        """获取状态标签"""
        return cls.STATUS_LABELS.get(status, {'zh': status, 'color': '#6c757d'})

class Quotation(db.Model):
    __tablename__ = 'quotations'

    id = db.Column(db.Integer, primary_key=True)
    quotation_number = db.Column(db.String(20), unique=True, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'))
    amount = db.Column(db.Float)
    project_stage = db.Column(db.String(20))  # 项目阶段：发现、品牌植入、招标前、招标中、中标、失败
    project_type = db.Column(db.String(20))   # 项目类型：销售重点、渠道跟进
    
    # 新增审核相关字段
    approval_status = db.Column(db.String(50), default=QuotationApprovalStatus.PENDING)  # 审核状态
    approved_stages = db.Column(db.JSON, default=list)  # 已审核的阶段列表
    approval_history = db.Column(db.JSON, default=list)  # 审核历史记录
    
    # 锁定相关字段
    is_locked = db.Column(db.Boolean, default=False)  # 是否被锁定
    lock_reason = db.Column(db.String(200))  # 锁定原因
    locked_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # 锁定人
    locked_at = db.Column(db.DateTime)  # 锁定时间
    
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo('Asia/Shanghai')))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 所有者字段（关联到用户表）
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    owner = db.relationship('User', foreign_keys=[owner_id], backref=db.backref('quotations', lazy='dynamic'))
    
    # 锁定人关联
    locker = db.relationship('User', foreign_keys=[locked_by], backref='locked_quotations')
    
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

    def can_approve_for_stage(self, stage):
        """检查是否可以对指定阶段进行审核"""
        if not stage:
            return False
        # 检查该阶段是否已经审核过
        approved_stages = self.approved_stages or []
        return stage not in approved_stages

    def add_approval_record(self, stage, approver_id, action, comment=None):
        """添加审核记录"""
        approval_history = self.approval_history or []
        record = {
            'stage': stage,
            'approver_id': approver_id,
            'action': action,  # 'approve' 或 'reject'
            'comment': comment,
            'timestamp': datetime.now().isoformat()
        }
        approval_history.append(record)
        self.approval_history = approval_history
        
        if action == 'approve':
            # 更新已审核阶段
            approved_stages = self.approved_stages or []
            if stage not in approved_stages:
                approved_stages.append(stage)
            self.approved_stages = approved_stages
            
            # 更新审核状态
            approval_status = QuotationApprovalStatus.get_approval_status_by_stage(stage)
            if approval_status:
                self.approval_status = approval_status
        elif action == 'reject':
            self.approval_status = QuotationApprovalStatus.REJECTED

    @property
    def approval_status_label(self):
        """获取审核状态标签"""
        return QuotationApprovalStatus.get_status_label(self.approval_status)

    @property 
    def approval_badge_html(self):
        """获取审核状态徽章HTML"""
        if not self.approval_status or self.approval_status == QuotationApprovalStatus.PENDING:
            return ''
        
        status_info = self.approval_status_label
        return f'<span class="badge badge-approval" style="background-color: {status_info["color"]}; color: white; font-size: 0.75rem;">{status_info["zh"]}</span>'

    def lock(self, reason, user_id):
        """锁定报价单"""
        self.is_locked = True
        self.lock_reason = reason
        self.locked_by = user_id
        self.locked_at = datetime.now()
        
    def unlock(self, user_id):
        """解锁报价单"""
        self.is_locked = False
        self.lock_reason = None
        self.locked_by = None
        self.locked_at = None
        
    @property
    def is_editable(self):
        """检查报价单是否可编辑"""
        return not self.is_locked
        
    @property
    def lock_status_display(self):
        """获取锁定状态显示信息"""
        if not self.is_locked:
            return None
        
        return {
            'is_locked': True,
            'reason': self.lock_reason,
            'locked_by': self.locker.real_name or self.locker.username if self.locker else '未知',
            'locked_at': self.locked_at.strftime('%Y-%m-%d %H:%M:%S') if self.locked_at else ''
        }

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