"""
公司主体（多公司报价单抬头配置）

每个 entity 代表一个开票/报价主体：
- 中国主体：增值税(价内) + 中文 + CNY
- 新加坡主体：GST(价外) + 英文 + SGD
- 马来西亚主体：SST(价外) + 英文 + MYR

报价单 quotations.entity_id 引用 entity.id，决定：
- 抬头 LOGO + 三行文字
- 编辑器/PDF 显示语言
- 税务模式（价内/价外）和默认税标签
- 默认货币
"""
from datetime import datetime
from app import db


class CompanyEntity(db.Model):
    __tablename__ = 'company_entities'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), nullable=False, unique=True)  # CN_DEFAULT / SG_DEFAULT / MY_DEFAULT ...
    name = db.Column(db.String(255), nullable=False)              # 显示名（用户选择时看到）
    region = db.Column(db.String(8), nullable=False)              # CN / SG / MY
    language = db.Column(db.String(8), nullable=False, default='en')        # zh / en (UI/PDF 语言)
    tax_mode = db.Column(db.String(16), nullable=False, default='exclusive')  # inclusive (价内) / exclusive (价外)
    tax_label = db.Column(db.String(32), nullable=True)           # GST / 增值税 / SST / VAT ...
    currency_code = db.Column(db.String(8), nullable=False, default='CNY')

    logo_url = db.Column(db.String(512), nullable=True)
    line1 = db.Column(db.String(255), nullable=True)  # 公司名
    line2 = db.Column(db.String(255), nullable=True)  # 地址
    line3 = db.Column(db.String(255), nullable=True)  # UEN / 网站 / 电话

    sort_order = db.Column(db.Integer, nullable=False, default=0)
    is_default = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'region': self.region,
            'language': self.language,
            'tax_mode': self.tax_mode,
            'tax_label': self.tax_label,
            'currency_code': self.currency_code,
            'logo_url': self.logo_url,
            'line1': self.line1 or '',
            'line2': self.line2 or '',
            'line3': self.line3 or '',
            'is_default': self.is_default,
        }

    def __repr__(self):
        return f'<CompanyEntity {self.code} ({self.region})>'
