from app import db
from datetime import datetime
import random
import string

def generate_company_code():
    # 生成格式：年份(2位) + 月份字母(1位) + 日期(2位) + 自然数(3位)
    # 例如: 25A02001，表示2025年1月2日第1号企业
    year = str(datetime.now().year)[2:]
    
    # 月份转换为字母 (1=A, 2=B, ..., 12=L)
    month_letter = chr(64 + datetime.now().month)  # 65是ASCII码中'A'的值，-1是因为月份从1开始
    
    day = str(datetime.now().day).zfill(2)
    
    # 查询当天最大的自然数序号
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_pattern = f"{year}{month_letter}{day}"
    
    latest_company = Company.query.filter(
        Company.company_code.like(f"{today_pattern}%")
    ).order_by(Company.id.desc()).first()
    
    if latest_company:
        try:
            # 提取最后3位数字并加1
            sequence_num = int(latest_company.company_code[-3:]) + 1
        except (ValueError, IndexError):
            # 如果提取失败，从001开始
            sequence_num = 1
    else:
        # 当天第一个编号
        sequence_num = 1
    
    sequence = str(sequence_num).zfill(3)
    code = f"{year}{month_letter}{day}{sequence}"
    
    return code

class Company(db.Model):
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    company_code = db.Column(db.String(20), unique=True, nullable=False)  # 企业代码
    company_name = db.Column(db.String(100), nullable=False)  # 企业名称
    country = db.Column(db.String(50))  # 国家/地区
    region = db.Column(db.String(50))  # 省/州
    address = db.Column(db.String(200))  # 详细地址
    industry = db.Column(db.String(50))  # 行业
    company_type = db.Column(db.String(20))  # 企业类型（用户/经销商/系统集成商/设计院及顾问/总承包单位）
    status = db.Column(db.String(20))  # 状态
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.Text)  # 备注
    is_deleted = db.Column(db.Boolean, default=False)  # 是否删除
    
    # 所有者字段（关联到用户表）
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    owner = db.relationship('User', backref=db.backref('companies', lazy='dynamic'))
    
    # 关联联系人
    contacts = db.relationship('Contact', backref='company', lazy=True, cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        if 'company_code' not in kwargs:
            kwargs['company_code'] = generate_company_code()
        super(Company, self).__init__(**kwargs)

    def __repr__(self):
        return f'<Company {self.company_name}>'

class Contact(db.Model):
    __tablename__ = 'contacts'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)  # 联系人姓名
    department = db.Column(db.String(50))  # 部门
    position = db.Column(db.String(50))  # 职位
    phone = db.Column(db.String(20))  # 电话
    email = db.Column(db.String(100))  # 邮箱
    is_primary = db.Column(db.Boolean, default=False)  # 是否为主要联系人
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.Text)  # 备注
    
    # 所有者字段（关联到用户表）
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    owner = db.relationship('User', backref=db.backref('contacts', lazy='dynamic'))

    def set_as_primary(self):
        """将当前联系人设置为主要联系人，同时取消同一企业其他联系人的主要联系人状态"""
        # 先将同一企业的所有联系人设置为非主要联系人
        Contact.query.filter_by(company_id=self.company_id).update({'is_primary': False})
        # 将当前联系人设置为主要联系人
        self.is_primary = True
        db.session.commit()

    def __repr__(self):
        return f'<Contact {self.name} of {self.company.company_name}>'

COMPANY_TYPES = [
    ('用户', '用户'),
    ('设计院及顾问', '设计院及顾问'),
    ('总承包', '总承包'),
    ('系统集成商', '系统集成商'),
    ('经销商', '经销商')
] 