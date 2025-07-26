#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logo服务
管理公司Logo的数据库存储和读取
"""

import os
import base64
import mimetypes
import logging
from pathlib import Path
from flask import current_app
from app import db
from app.models.company_asset import CompanyAsset

logger = logging.getLogger(__name__)

class LogoService:
    """Logo管理服务"""
    
    @staticmethod
    def get_company_logo(logo_key='evertac_logo'):
        """
        获取公司Logo的Base64 Data URL
        
        Args:
            logo_key: Logo标识符
            
        Returns:
            str: Base64 Data URL 或 None
        """
        try:
            # 优先查找指定key的Logo
            logo = CompanyAsset.get_logo(logo_key)
            
            # 如果没找到，尝试获取默认Logo
            if not logo:
                logo = CompanyAsset.get_default_logo()
            
            if logo:
                logger.debug(f"✅ 从数据库获取Logo: {logo.asset_name} ({logo.file_size_kb}KB)")
                return logo.base64_data_url
            else:
                logger.warning("⚠️ 数据库中未找到Logo，尝试回退到静态文件")
                return LogoService._fallback_to_static_logo()
                
        except Exception as e:
            logger.error(f"❌ 获取Logo失败: {e}")
            return LogoService._fallback_to_static_logo()
    
    @staticmethod
    def _fallback_to_static_logo():
        """回退到静态文件Logo"""
        try:
            # 尝试从静态文件加载Logo（开发环境备用）
            logo_files = [
                'evertac_logo.svg',
                'evertac_logo.png', 
                'company_logo.png',
                'logo.png'
            ]
            
            if current_app:
                static_dir = Path(current_app.static_folder) / 'images'
            else:
                static_dir = Path(__file__).parent.parent / 'static' / 'images'
            
            for logo_file in logo_files:
                logo_path = static_dir / logo_file
                if logo_path.exists():
                    with open(logo_path, 'rb') as f:
                        file_data = f.read()
                    
                    base64_content = base64.b64encode(file_data).decode('utf-8')
                    file_type = mimetypes.guess_type(str(logo_path))[0] or 'image/png'
                    
                    logger.info(f"📁 使用静态文件Logo: {logo_file}")
                    return f"data:{file_type};base64,{base64_content}"
            
            logger.warning("⚠️ 未找到任何Logo文件")
            return None
            
        except Exception as e:
            logger.error(f"❌ 静态Logo回退失败: {e}")
            return None
    
    @staticmethod
    def upload_logo(file_data, filename, asset_name=None, asset_key=None, created_by_id=None):
        """
        上传Logo到数据库
        
        Args:
            file_data: 文件二进制数据
            filename: 原始文件名
            asset_name: 资产名称
            asset_key: 资产键名
            created_by_id: 创建人ID
            
        Returns:
            CompanyAsset: 创建的资产对象
        """
        try:
            # 默认参数
            if not asset_name:
                asset_name = f"公司Logo - {filename}"
            if not asset_key:
                asset_key = 'evertac_logo'
            
            # 获取文件信息
            file_size = len(file_data)
            file_type = mimetypes.guess_type(filename)[0] or 'image/png'
            
            # Base64编码
            base64_content = base64.b64encode(file_data).decode('utf-8')
            
            # 检查是否已存在相同key的Logo
            existing_logo = CompanyAsset.get_logo(asset_key)
            if existing_logo:
                # 更新现有Logo
                existing_logo.asset_name = asset_name
                existing_logo.file_name = filename
                existing_logo.file_type = file_type
                existing_logo.file_size = file_size
                existing_logo.file_content = base64_content
                existing_logo.is_active = True
                
                db.session.commit()
                logger.info(f"✅ Logo已更新: {asset_name} ({file_size/1024:.1f}KB)")
                return existing_logo
            else:
                # 创建新Logo
                logo = CompanyAsset(
                    asset_type='logo',
                    asset_name=asset_name,
                    asset_key=asset_key,
                    file_name=filename,
                    file_type=file_type,
                    file_size=file_size,
                    file_content=base64_content,
                    created_by_id=created_by_id,
                    is_default=True  # 新上传的Logo设为默认
                )
                
                # 清除其他默认Logo标记
                CompanyAsset.query.filter_by(
                    asset_type='logo', 
                    is_default=True
                ).update({'is_default': False})
                
                db.session.add(logo)
                db.session.commit()
                
                logger.info(f"✅ 新Logo已创建: {asset_name} ({file_size/1024:.1f}KB)")
                return logo
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Logo上传失败: {e}")
            raise
    
    @staticmethod
    def init_default_logo():
        """初始化默认Logo到数据库"""
        try:
            # 检查是否已有Logo
            existing_logo = CompanyAsset.query.filter_by(asset_type='logo').first()
            if existing_logo:
                logger.info("✅ 数据库中已存在Logo，跳过初始化")
                return existing_logo
            
            # 查找SVG Logo文件
            svg_content = '''<svg width="240" height="50" viewBox="0 0 240 50" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:#4A90A4;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#5DA0B4;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#7FC7D9;stop-opacity:1" />
    </linearGradient>
  </defs>
  
  <!-- EVERTAC文字 -->
  <text x="5" y="30" 
        font-family="Arial, Helvetica, sans-serif" 
        font-size="28" 
        font-weight="bold" 
        fill="url(#logoGradient)"
        letter-spacing="2px">EVERTAC</text>
  
  <!-- SOLUTIONS文字 -->
  <text x="8" y="45" 
        font-family="Arial, Helvetica, sans-serif" 
        font-size="10" 
        font-weight="normal" 
        fill="#333"
        letter-spacing="1px">SOLUTIONS</text>
</svg>'''
            
            # 创建默认Logo
            svg_data = svg_content.encode('utf-8')
            base64_content = base64.b64encode(svg_data).decode('utf-8')
            
            logo = CompanyAsset(
                asset_type='logo',
                asset_name='EVERTAC Solutions Logo',
                asset_key='evertac_logo',
                file_name='evertac_logo.svg',
                file_type='image/svg+xml',
                file_size=len(svg_data),
                file_content=base64_content,
                description='EVERTAC公司默认Logo，包含渐变效果',
                is_default=True,
                is_active=True
            )
            
            db.session.add(logo)
            db.session.commit()
            
            logger.info(f"✅ 默认Logo已初始化到数据库: {logo.asset_name} ({logo.file_size_kb}KB)")
            return logo
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ 初始化默认Logo失败: {e}")
            raise
    
    @staticmethod
    def list_logos():
        """获取所有Logo列表"""
        try:
            logos = CompanyAsset.query.filter_by(
                asset_type='logo',
                is_active=True
            ).order_by(CompanyAsset.is_default.desc(), CompanyAsset.created_at.desc()).all()
            
            return [logo.to_dict() for logo in logos]
            
        except Exception as e:
            logger.error(f"❌ 获取Logo列表失败: {e}")
            return []
    
    @staticmethod
    def delete_logo(logo_id):
        """删除Logo"""
        try:
            logo = CompanyAsset.query.get(logo_id)
            if not logo or logo.asset_type != 'logo':
                return False
            
            # 软删除
            logo.is_active = False
            
            # 如果删除的是默认Logo，需要设置新的默认Logo
            if logo.is_default:
                logo.is_default = False
                # 找到下一个Logo设为默认
                next_logo = CompanyAsset.query.filter_by(
                    asset_type='logo',
                    is_active=True
                ).filter(CompanyAsset.id != logo_id).first()
                
                if next_logo:
                    next_logo.is_default = True
            
            db.session.commit()
            logger.info(f"✅ Logo已删除: {logo.asset_name}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ 删除Logo失败: {e}")
            return False

# 便捷函数
def get_company_logo_base64(logo_key='evertac_logo'):
    """获取公司Logo的Base64编码（兼容原有接口）"""
    return LogoService.get_company_logo(logo_key)