#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公司资产模型
用于存储公司Logo、印章等静态资源
"""

from datetime import datetime
from app import db

class CompanyAsset(db.Model):
    """公司资产表 - 存储Logo等静态资源"""
    
    __tablename__ = 'company_assets'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 资产信息
    asset_type = db.Column(db.String(50), nullable=False, comment='资产类型: logo, seal, etc.')
    asset_name = db.Column(db.String(100), nullable=False, comment='资产名称')
    asset_key = db.Column(db.String(50), unique=True, nullable=False, comment='资产唯一标识')
    
    # 文件信息
    file_name = db.Column(db.String(255), nullable=False, comment='原始文件名')
    file_type = db.Column(db.String(50), nullable=False, comment='文件类型: image/png, image/svg+xml, etc.')
    file_size = db.Column(db.Integer, nullable=False, comment='文件大小(字节)')
    
    # 文件内容 (Base64编码)
    file_content = db.Column(db.Text, nullable=False, comment='Base64编码的文件内容')
    
    # 元数据
    description = db.Column(db.Text, comment='资产描述')  
    is_active = db.Column(db.Boolean, default=True, nullable=False, comment='是否启用')
    is_default = db.Column(db.Boolean, default=False, nullable=False, comment='是否为默认资产')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 创建人
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_by = db.relationship('User', backref='created_assets', lazy='select')
    
    def __repr__(self):
        return f'<CompanyAsset {self.asset_name}({self.asset_key})>'
    
    @property
    def base64_data_url(self):
        """获取完整的Base64 Data URL"""
        return f"data:{self.file_type};base64,{self.file_content}"
    
    @property
    def file_size_kb(self):
        """获取文件大小(KB)"""
        return round(self.file_size / 1024, 2)
    
    @classmethod
    def get_logo(cls, logo_key='company_logo'):
        """获取指定的Logo"""
        return cls.query.filter_by(
            asset_type='logo',
            asset_key=logo_key,
            is_active=True
        ).first()
    
    @classmethod
    def get_default_logo(cls):
        """获取默认Logo"""
        return cls.query.filter_by(
            asset_type='logo',
            is_active=True,
            is_default=True
        ).first()
    
    @classmethod 
    def set_default_logo(cls, asset_id):
        """设置默认Logo"""
        # 清除所有默认标记
        cls.query.filter_by(asset_type='logo').update({'is_default': False})
        
        # 设置新的默认Logo
        asset = cls.query.get(asset_id)
        if asset and asset.asset_type == 'logo':
            asset.is_default = True
            return True
        return False
    
    @staticmethod
    def create_logo_from_file(file_path, asset_name, asset_key, created_by_id=None):
        """从文件创建Logo资产"""
        import os
        import base64
        import mimetypes
        from pathlib import Path
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 读取文件内容
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # 获取文件信息
        file_size = len(file_data)
        file_type = mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream'
        
        # Base64编码
        base64_content = base64.b64encode(file_data).decode('utf-8')
        
        # 创建资产记录
        asset = CompanyAsset(
            asset_type='logo',
            asset_name=asset_name,
            asset_key=asset_key,
            file_name=file_path.name,
            file_type=file_type,
            file_size=file_size,
            file_content=base64_content,
            created_by_id=created_by_id
        )
        
        return asset
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'asset_type': self.asset_type,
            'asset_name': self.asset_name,
            'asset_key': self.asset_key,
            'file_name': self.file_name,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'file_size_kb': self.file_size_kb,
            'description': self.description,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'base64_data_url': self.base64_data_url
        }