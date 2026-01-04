from app import db
from datetime import datetime
import time

class Dictionary(db.Model):
    """
    通用字典表模型
    用于管理系统中的字典字段，如角色、区域、行业、产品类别等
    """
    __tablename__ = 'dictionaries'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # 字典类型，如'role'、'region'等
    key = db.Column(db.String(50), nullable=False)   # 字典键，用于存储
    value = db.Column(db.String(100), nullable=False) # 字典值，用于显示（中文）
    value_en = db.Column(db.String(100), nullable=True) # 英文显示值
    is_active = db.Column(db.Boolean, default=True)   # 是否启用
    is_vendor = db.Column(db.Boolean, default=False)  # 是否为厂商（仅对企业字典有效）
    sort_order = db.Column(db.Integer, default=0)     # 排序顺序
    created_at = db.Column(db.Float, default=time.time)
    updated_at = db.Column(db.Float, default=time.time, onupdate=time.time)
    
    # 企业详细信息字段（仅对type='company'有效）
    address = db.Column(db.String(500))  # 详细地址
    postal_code = db.Column(db.String(20))  # 邮政编码
    phone = db.Column(db.String(50))  # 企业电话
    fax = db.Column(db.String(50))  # 传真
    email = db.Column(db.String(100))  # 企业邮箱
    website = db.Column(db.String(200))  # 网站地址
    
    # Logo和图片资产字段（Base64存储，仅对type='company'有效）
    logo_content = db.Column(db.Text)  # Logo的Base64内容
    logo_filename = db.Column(db.String(100))  # Logo原始文件名
    logo_type = db.Column(db.String(50))  # Logo文件类型 (image/png, image/svg+xml等)
    logo_size = db.Column(db.Integer)  # Logo文件大小（字节）
    
    email_signature_content = db.Column(db.Text)  # 邮件签名图片的Base64内容
    email_signature_filename = db.Column(db.String(100))  # 邮件签名原始文件名
    email_signature_type = db.Column(db.String(50))  # 邮件签名文件类型
    email_signature_size = db.Column(db.Integer)  # 邮件签名文件大小（字节）
    
    __table_args__ = (
        # 确保每种类型下的key是唯一的
        db.UniqueConstraint('type', 'key', name='uix_type_key'),
    )
    
    @property
    def logo_data_url(self):
        """获取Logo的Base64 Data URL（仅对企业字典有效）"""
        if self.type == 'company' and self.logo_content and self.logo_type:
            return f"data:{self.logo_type};base64,{self.logo_content}"
        return None
    
    @property
    def email_signature_data_url(self):
        """获取邮件签名图片的Base64 Data URL（仅对企业字典有效）"""
        if self.type == 'company' and self.email_signature_content and self.email_signature_type:
            return f"data:{self.email_signature_type};base64,{self.email_signature_content}"
        return None
    
    @property
    def logo_size_kb(self):
        """获取Logo文件大小(KB)"""
        return round(self.logo_size / 1024, 2) if self.logo_size else 0
    
    @property
    def email_signature_size_kb(self):
        """获取邮件签名文件大小(KB)"""
        return round(self.email_signature_size / 1024, 2) if self.email_signature_size else 0
    
    def update_logo(self, file_data, filename):
        """更新企业Logo（仅对企业字典有效）"""
        if self.type != 'company':
            return False
        
        import base64
        import mimetypes
        
        # Base64编码
        base64_content = base64.b64encode(file_data).decode('utf-8')
        file_type = mimetypes.guess_type(filename)[0] or 'image/png'
        file_size = len(file_data)
        
        # 更新字段
        self.logo_content = base64_content
        self.logo_filename = filename
        self.logo_type = file_type
        self.logo_size = file_size
        self.updated_at = time.time()
        
        return True
    
    def update_email_signature(self, file_data, filename):
        """更新邮件签名图片（仅对企业字典有效）"""
        if self.type != 'company':
            return False
        
        import base64
        import mimetypes
        
        # Base64编码
        base64_content = base64.b64encode(file_data).decode('utf-8')
        file_type = mimetypes.guess_type(filename)[0] or 'image/png'
        file_size = len(file_data)
        
        # 更新字段
        self.email_signature_content = base64_content
        self.email_signature_filename = filename
        self.email_signature_type = file_type
        self.email_signature_size = file_size
        self.updated_at = time.time()
        
        return True
    
    def clear_logo(self):
        """清除企业Logo（仅对企业字典有效）"""
        if self.type != 'company':
            return False
        
        self.logo_content = None
        self.logo_filename = None
        self.logo_type = None
        self.logo_size = None
        self.updated_at = time.time()
        return True
    
    def clear_email_signature(self):
        """清除邮件签名图片（仅对企业字典有效）"""
        if self.type != 'company':
            return False
        
        self.email_signature_content = None
        self.email_signature_filename = None
        self.email_signature_type = None
        self.email_signature_size = None
        self.updated_at = time.time()
        return True

    def to_dict(self):
        """将字典信息转为字典，用于API响应"""
        base_dict = {
            'id': self.id,
            'type': self.type,
            'key': self.key,
            'value': self.value,
            'value_en': self.value_en,
            'is_active': self.is_active,
            'is_vendor': self.is_vendor,
            'sort_order': self.sort_order,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        
        # 如果是企业字典，添加额外信息
        if self.type == 'company':
            base_dict.update({
                'address': self.address,
                'postal_code': self.postal_code,
                'phone': self.phone,
                'fax': self.fax,
                'email': self.email,
                'website': self.website,
                'has_logo': bool(self.logo_content),
                'logo_filename': self.logo_filename,
                'logo_size_kb': self.logo_size_kb,
                'has_email_signature': bool(self.email_signature_content),
                'email_signature_filename': self.email_signature_filename,
                'email_signature_size_kb': self.email_signature_size_kb
            })
        
        return base_dict
    
    def __repr__(self):
        return f'<Dictionary {self.type}:{self.key}={self.value}>' 