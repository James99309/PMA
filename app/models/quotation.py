from datetime import datetime
from zoneinfo import ZoneInfo
from app import db
from sqlalchemy import event, Date, text
from sqlalchemy.exc import SQLAlchemyError
from app.models.project import Project
import random
import string
import hashlib
import json

def get_local_time():
    """获取本地时间（北京时区）"""
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)

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

    # 审核状态颜色（标签文本从 dictionary_helpers.PROJECT_STAGE_LABELS 获取）
    STATUS_COLORS = {
        'pending': '#6c757d',
        'discover_approved': '#17a2b8',
        'embed_approved': '#007bff',
        'pre_tender_approved': '#28a745',
        'tendering_approved': '#ffc107',
        'awarded_approved': '#fd7e14',
        'quoted_approved': '#e83e8c',
        'signed_approved': '#6f42c1',
        'rejected': '#dc3545'
    }

    @classmethod
    def get_approval_status_by_stage(cls, stage):
        """根据项目阶段获取对应的审核状态"""
        return cls.STAGE_TO_APPROVAL.get(stage)

    @classmethod
    def get_status_label(cls, status, lang='zh'):
        """获取状态标签，从 dictionary_helpers 获取阶段名称"""
        from app.utils.dictionary_helpers import project_stage_label, approval_status_label

        color = cls.STATUS_COLORS.get(status, '#6c757d')

        # 解析状态：如 'discover_approved' -> 'discover'
        if status.endswith('_approved'):
            stage_key = status.replace('_approved', '')
            label = project_stage_label(stage_key, lang)
        elif status == 'pending':
            label = approval_status_label('pending', lang)
        elif status == 'rejected':
            label = approval_status_label('rejected', lang)
        else:
            label = status

        return {'label': label, 'color': color}

class Quotation(db.Model):
    __tablename__ = 'quotations'

    id = db.Column(db.Integer, primary_key=True)
    quotation_number = db.Column(db.String(20), unique=True, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)  # 客户字段（数据库可空，前端必填）
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'))  # 联系人可选
    amount = db.Column(db.Float)
    tax_rate = db.Column(db.Float, nullable=False, default=0)  # 整张报价共用的税率(0-100 浮点),合计 = 小计 × (1 + tax_rate/100)
    project_stage = db.Column(db.String(20))  # 项目阶段：发现、品牌植入、招标前、招标中、中标、失败
    project_type = db.Column(db.String(20))   # 项目类型：销售重点、渠道跟进
    
    # 新增审核相关字段
    approval_status = db.Column(db.String(50), default=QuotationApprovalStatus.PENDING)  # 审核状态
    approved_stages = db.Column(db.JSON, default=list)  # 已审核的阶段列表
    approval_history = db.Column(db.JSON, default=list)  # 审核历史记录
    
    # 统一确认徽章字段
    confirmation_badge_status = db.Column(db.String(20), default='none')  # none/pending/confirmed/reconfirm
    confirmation_badge_color = db.Column(db.String(20))  # 徽章颜色
    confirmed_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # 确认人
    confirmed_at = db.Column(db.DateTime)  # 确认时间
    product_signature = db.Column(db.String(64))  # 产品明细数字签名
    
    # 锁定相关字段
    is_locked = db.Column(db.Boolean, default=False)  # 是否被锁定
    lock_reason = db.Column(db.String(200))  # 锁定原因
    locked_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # 锁定人
    locked_at = db.Column(db.DateTime)  # 锁定时间
    
    # 植入总额合计字段
    implant_total_amount = db.Column(db.Float, default=0.0)  # 植入总额合计
    
    # 货币字段
    currency = db.Column(db.String(10), default='CNY')  # 货币类型
    notes = db.Column(db.Text, nullable=True, comment='报价单备注')

    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo('Asia/Shanghai')))
    updated_at = db.Column(db.DateTime, default=get_local_time)
    
    # 所有者字段（关联到用户表）
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    owner = db.relationship('User', foreign_keys=[owner_id], backref=db.backref('quotations', lazy='dynamic'))

    # 公司主体（多公司报价：CN/SG/MY 等）
    entity_id = db.Column(db.Integer, db.ForeignKey('company_entities.id'), nullable=True)
    entity = db.relationship('CompanyEntity', foreign_keys=[entity_id])

    # 非结构化字段：付款条件 / 交付条件 / 有效期 / Ref No 等（编辑器输入）
    extra_fields = db.Column(db.JSON, nullable=True)
    
    # 锁定人关联
    locker = db.relationship('User', foreign_keys=[locked_by], backref='locked_quotations')
    
    # 确认人关联
    confirmer = db.relationship('User', foreign_keys=[confirmed_by], backref='confirmed_quotations')
    
    # 关联关系
    project = db.relationship('Project', back_populates='quotations')
    customer = db.relationship('Company', backref='quotations')  # 客户关系
    contact = db.relationship('Contact', backref='quotations')  # 联系人关系
    details = db.relationship('QuotationDetail', backref='quotation', cascade='all, delete-orphan',
                             order_by='QuotationDetail.sort_order, QuotationDetail.id')  # 优先按 sort_order，回退到 id

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

    @property
    def formatted_implant_total_amount(self):
        """返回格式化的植入总额合计"""
        return '{:,.2f}'.format(self.implant_total_amount) if self.implant_total_amount else '0.00'

    def calculate_implant_total_amount(self):
        """计算植入总额合计（按报价单货币统一显示）"""
        from app.services.exchange_rate_service import exchange_rate_service
        
        total = 0.0
        quotation_currency = self.currency or 'CNY'
        
        for detail in self.details:
            # 直接使用已经计算好的植入小计
            if detail.implant_subtotal and detail.implant_subtotal > 0:
                implant_amount = detail.implant_subtotal
                detail_currency = detail.currency or 'CNY'
                
                # 如果明细货币与报价单货币不同，进行转换
                if detail_currency != quotation_currency:
                    try:
                        implant_amount = exchange_rate_service.convert_amount(
                            implant_amount, detail_currency, quotation_currency
                        )
                    except Exception as e:
                        print(f"植入总额货币转换失败 {detail_currency} -> {quotation_currency}: {e}")
                        # 转换失败时保持原值
                
                total += implant_amount
        
        self.implant_total_amount = round(total, 2)
        return self.implant_total_amount

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

    @property
    def currency_symbol(self):
        """获取货币符号"""
        from app.utils.dictionary_helpers import get_currency_symbol
        return get_currency_symbol(self.currency)

    def calculate_product_signature(self):
        """计算产品明细的数字签名，用于检测关键变化（行数和MN号）"""
        if not self.details:
            return None
        
        # 构造签名内容：只关注产品数量和各产品的MN号
        signature_data = {
            'count': len(self.details),
            'mn_list': []
        }
        
        for detail in self.details:
            # 只记录MN号，不关注数量变化
            signature_data['mn_list'].append(detail.product_mn or '')
        
        # 按MN号排序确保一致性
        signature_data['mn_list'].sort()
        
        # 生成MD5签名
        signature_string = json.dumps(signature_data, sort_keys=True)
        return hashlib.md5(signature_string.encode()).hexdigest()
    
    def update_product_signature(self):
        """更新产品明细签名"""
        new_signature = self.calculate_product_signature()
        old_signature = self.product_signature

        # 如果签名发生变化且当前已确认，转为再次确认状态
        if old_signature and new_signature != old_signature:
            if self.confirmation_badge_status == 'confirmed':
                self.confirmation_badge_status = 'reconfirm'
                self.confirmation_badge_color = '#f59e0b'  # 琥珀色

        self.product_signature = new_signature
    
    def set_confirmation_badge(self, color, user_id):
        """设置确认徽章"""
        self.confirmation_badge_status = 'confirmed'
        self.confirmation_badge_color = color
        self.confirmed_by = user_id
        self.confirmed_at = datetime.now()
        # 更新签名以匹配当前产品明细
        self.product_signature = self.calculate_product_signature()
    
    def clear_confirmation_badge(self):
        """清除确认徽章"""
        self.confirmation_badge_status = 'none'
        self.confirmation_badge_color = None
        self.confirmed_by = None
        self.confirmed_at = None
    
    def set_pending_confirmation_badge(self):
        """设置待确认徽章（创建报价单时自动添加）"""
        if self.confirmation_badge_status == 'none':
            self.confirmation_badge_status = 'pending'
            self.confirmation_badge_color = '#f97316'  # 橙色
            self.product_signature = self.calculate_product_signature()

    def set_reconfirm_badge(self):
        """设置再次确认徽章（已确认后配置变化时触发）"""
        if self.confirmation_badge_status == 'confirmed':
            self.confirmation_badge_status = 'reconfirm'
            self.confirmation_badge_color = '#f59e0b'  # 琥珀色

    @property
    def confirmation_badge_html(self):
        """获取确认徽章HTML"""
        if self.confirmation_badge_status == 'none':
            return ''

        if self.confirmation_badge_status == 'pending':
            return '<span class="badge confirmation-badge" style="background-color: #f97316; color: white; font-size: 0.75rem;" title="待确认">○</span>'
        elif self.confirmation_badge_status == 'reconfirm':
            return '<span class="badge confirmation-badge" style="background-color: #f59e0b; color: white; font-size: 0.75rem;" title="配置已变更，需再次确认">⟳</span>'
        elif self.confirmation_badge_status == 'confirmed':
            color = self.confirmation_badge_color or '#28a745'
            confirmer_name = self.confirmer.real_name if self.confirmer else '未知'
            confirmed_time = self.confirmed_at.strftime('%Y-%m-%d %H:%M') if self.confirmed_at else ''
            return f'<span class="badge confirmation-badge" style="background-color: {color}; color: white; font-size: 0.75rem;" title="已确认 - {confirmer_name} ({confirmed_time})">✓</span>'

        return ''

def _refresh_project_quotation_cache(connection, project_id):
    """刷新项目的 quotation_customer / quotation_currency 缓存

    字段语义（保持原样，与报价单明细显示一致）：
    - quotation_customer: **最新一张报价单的原金额**（不做汇率换算）
    - quotation_currency: **最新一张报价单的原货币**

    由 Quotation 的 after_insert / after_update / after_delete 事件调用。

    跨项目统计（`get_full_project_stats`）在读取端使用
    `MultiCurrencyAggregationService.sum_converted` 动态换算聚合，
    不依赖此缓存字段做跨货币求和。
    """
    from config import Config

    # 查询最新一张报价单的 amount 和 currency
    latest_sql = text("""
        SELECT amount, currency
        FROM quotations
        WHERE project_id = :project_id
        ORDER BY created_at DESC
        LIMIT 1
    """)
    row = connection.execute(latest_sql, {"project_id": project_id}).fetchone()

    if row is None:
        # 项目下没有报价单了（比如最后一张被删除）
        amount = 0.0
        currency = Config.DEFAULT_CURRENCY
    else:
        amount = float(row[0] or 0)
        currency = (row[1] or Config.DEFAULT_CURRENCY).upper()

    now = datetime.now(ZoneInfo('Asia/Shanghai'))
    update_sql = text("""
        UPDATE projects
        SET quotation_customer = :amount,
            quotation_currency = :currency,
            updated_at = :now
        WHERE id = :project_id
    """)
    connection.execute(update_sql, {
        "amount": amount,
        "currency": currency,
        "now": now,
        "project_id": project_id,
    })


# 添加SQLAlchemy事件监听器
@event.listens_for(Quotation, 'after_insert')
@event.listens_for(Quotation, 'after_update')
def update_project_quotation(mapper, connection, target):
    """报价单保存/更新后刷新项目的最新报价金额和货币缓存（原样，不换算）"""
    try:
        if target.project_id:
            _refresh_project_quotation_cache(connection, target.project_id)
    except Exception as e:
        print(f"更新项目最新报价金额时发生错误: {str(e)}")


@event.listens_for(Quotation, 'after_delete')
def update_project_quotation_on_delete(mapper, connection, target):
    """报价单删除后刷新项目的最新报价金额和货币缓存"""
    try:
        if target.project_id:
            _refresh_project_quotation_cache(connection, target.project_id)
    except Exception as e:
        print(f"删除报价单后更新项目金额时发生错误: {str(e)}")

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
    
    # 植入小计字段
    implant_subtotal = db.Column(db.Float, default=0.0)  # 植入小计：当产品品牌是和源通信时，零售价格 * 产品数量的值
    
    # 货币字段
    currency = db.Column(db.String(10), default='CNY')  # 货币类型
    item_note = db.Column(db.Text, nullable=True, comment='明细行备注')

    # 行类型 + 排序（Excel-like 编辑器）
    row_type = db.Column(db.String(16), default='product', nullable=False)  # 'product' / 'section'
    section_label = db.Column(db.String(255), nullable=True)  # 标注行的文字（仅 row_type='section' 时使用）
    sort_order = db.Column(db.Integer, nullable=True)  # 显式排序（默认 = id）

    # 配置产品字段（使用已存在的parent_item_id和is_accessory字段）
    parent_item_id = db.Column(db.Integer, db.ForeignKey('quotation_details.id', ondelete='CASCADE'), nullable=True)  # 父级产品行ID
    is_accessory = db.Column(db.Boolean, default=False, nullable=False)  # 是否为配置产品
    is_editable = db.Column(db.Boolean, default=True, nullable=False)  # 是否可编辑
    config_type = db.Column(db.String(50), nullable=True)  # 配置类型: 'required_accessory', 'required_mutual', 'recommended', 'optional_mutual'
    config_base_quantity = db.Column(db.Integer, nullable=True)  # 配置基础数量
    quantity_synced = db.Column(db.Boolean, default=True, nullable=False)  # 配置产品是否同步主产品数量

    # 动态规格配置字段
    configured_specs = db.Column(db.JSON, nullable=True)  # 配置规格快照，格式见计划文档
    configured_mn = db.Column(db.String(50), nullable=True)  # 配置后的MN编码
    price_adjustment_total = db.Column(db.Integer, default=0)  # 总价格增量（分）
    pending_product_creation = db.Column(db.Boolean, default=False)  # 是否需要在确认时创建新产品

    # 产品明细确认字段 - 暂时注释掉数据库字段，使用会话存储
    # is_confirmed = db.Column(db.Boolean, default=False)  # 是否确认
    # confirmed_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # 确认人
    # confirmed_at = db.Column(db.DateTime)  # 确认时间

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 配置产品关系
    configurations = db.relationship('QuotationDetail',
                                    backref=db.backref('parent_detail', remote_side=[id]),
                                    cascade='all, delete-orphan',
                                    foreign_keys=[parent_item_id])

    # 确认人关联 - 暂时注释掉
    # confirmer = db.relationship('User', foreign_keys=[confirmed_by], backref='confirmed_detail_items')
    
    def calculate_prices(self):
        """计算单价、总价和植入小计（考虑货币换算）"""
        # 只在单价为空或为0时才重新计算，否则保持用户输入的单价
        if not self.unit_price or self.unit_price == 0:
            self.unit_price = (self.market_price or 0) * (self.discount or 1)
        
        # 总价始终根据单价和数量重新计算
        self.total_price = (self.unit_price or 0) * (self.quantity or 0)
        
        # 计算植入小计
        self.calculate_implant_subtotal_only()

    def calculate_implant_subtotal_only(self):
        """只计算植入小计，不修改其他价格字段"""
        # 计算植入小计：通过产品MN查找产品的厂商标记
        from app.models.product import Product
        
        self.implant_subtotal = 0.0
        
        if self.product_mn:
            product = Product.query.filter_by(product_mn=self.product_mn).first()
            if product and product.is_vendor_product:
                # 使用报价明细中的市场价计算植入小计，避免货币转换问题
                try:
                    market_price = float(self.market_price or 0)
                    quantity = int(self.quantity or 0)
                    
                    if market_price > 0 and quantity > 0:
                        implant_amount = market_price * quantity
                    else:
                        implant_amount = 0
                        
                except (ValueError, TypeError) as e:
                    print(f"植入小计数据转换错误: {e}")
                    implant_amount = 0
                
                self.implant_subtotal = round(implant_amount, 2)
        
        # 兼容旧数据：如果没有product_mn但品牌是和源通信，也计算植入小计
        elif self.brand == '和源通信':
            self.implant_subtotal = round((self.market_price or 0) * (self.quantity or 0), 2)

    @property
    def formatted_implant_subtotal(self):
        """返回格式化的植入小计"""
        return '{:,.2f}'.format(self.implant_subtotal) if self.implant_subtotal else '0.00'

# 产品明细变化监听器
@event.listens_for(QuotationDetail, 'after_insert')
@event.listens_for(QuotationDetail, 'after_update')
@event.listens_for(QuotationDetail, 'after_delete')
def update_quotation_implant_total(mapper, connection, target):
    """产品明细变化时更新报价单的植入总额合计"""
    try:
        quotation_id = target.quotation_id
        if quotation_id:
            result = connection.execute(text("""
                SELECT COALESCE(SUM(implant_subtotal), 0) as implant_total
                FROM quotation_details
                WHERE quotation_id = :quotation_id
            """), {"quotation_id": quotation_id})

            row = result.fetchone()
            if row:
                connection.execute(text("""
                    UPDATE quotations
                    SET implant_total_amount = :implant_total
                    WHERE id = :quotation_id
                """), {"quotation_id": quotation_id, "implant_total": row[0]})
    except Exception as e:
        print(f"更新植入总额合计时发生错误: {str(e)}") 