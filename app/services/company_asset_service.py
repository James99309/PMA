#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业资产管理服务
管理企业Logo、邮件签名图片等资产
"""

import os
import base64
import mimetypes
import logging
from pathlib import Path
from flask import request, current_app
from app import db
from app.models.customer import Company

logger = logging.getLogger(__name__)

class CompanyAssetService:
    """企业资产管理服务"""
    
    @staticmethod
    def upload_company_logo(company_id, file_data, filename):
        """
        上传企业Logo
        
        Args:
            company_id: 企业ID
            file_data: 文件二进制数据
            filename: 原始文件名
            
        Returns:
            dict: 上传结果
        """
        try:
            # 获取企业对象
            company = Company.query.get(company_id)
            if not company:
                return {'success': False, 'message': '企业不存在'}
            
            # 验证文件类型
            allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'image/svg+xml', 'image/gif']
            file_type = mimetypes.guess_type(filename)[0]
            
            if file_type not in allowed_types:
                return {'success': False, 'message': '不支持的文件类型，请使用PNG、JPG、SVG或GIF格式'}
            
            # 验证文件大小（限制5MB）
            max_size = 5 * 1024 * 1024  # 5MB
            if len(file_data) > max_size:
                return {'success': False, 'message': '文件大小不能超过5MB'}
            
            # 更新Logo
            company.update_logo(file_data, filename)
            db.session.commit()
            
            logger.info(f"✅ 企业Logo上传成功: {company.company_name} - {filename} ({len(file_data)/1024:.1f}KB)")
            
            return {
                'success': True,
                'message': 'Logo上传成功',
                'logo_info': {
                    'filename': company.logo_filename,
                    'size_kb': company.logo_size_kb,
                    'type': company.logo_type
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ 企业Logo上传失败: {e}")
            return {'success': False, 'message': f'上传失败: {str(e)}'}
    
    @staticmethod
    def upload_email_signature(company_id, file_data, filename):
        """
        上传邮件签名图片
        
        Args:
            company_id: 企业ID
            file_data: 文件二进制数据
            filename: 原始文件名
            
        Returns:
            dict: 上传结果
        """
        try:
            # 获取企业对象
            company = Company.query.get(company_id)
            if not company:
                return {'success': False, 'message': '企业不存在'}
            
            # 验证文件类型
            allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'image/svg+xml', 'image/gif']
            file_type = mimetypes.guess_type(filename)[0]
            
            if file_type not in allowed_types:
                return {'success': False, 'message': '不支持的文件类型，请使用PNG、JPG、SVG或GIF格式'}
            
            # 验证文件大小（限制3MB）
            max_size = 3 * 1024 * 1024  # 3MB
            if len(file_data) > max_size:
                return {'success': False, 'message': '文件大小不能超过3MB'}
            
            # 更新邮件签名
            company.update_email_signature(file_data, filename)
            db.session.commit()
            
            logger.info(f"✅ 邮件签名上传成功: {company.company_name} - {filename} ({len(file_data)/1024:.1f}KB)")
            
            return {
                'success': True,
                'message': '邮件签名上传成功',
                'signature_info': {
                    'filename': company.email_signature_filename,
                    'size_kb': company.email_signature_size_kb,
                    'type': company.email_signature_type
                }
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ 邮件签名上传失败: {e}")
            return {'success': False, 'message': f'上传失败: {str(e)}'}
    
    @staticmethod
    def get_company_logo(company_id):
        """
        获取企业Logo
        
        Args:
            company_id: 企业ID
            
        Returns:
            str: Base64 Data URL 或 None
        """
        try:
            company = Company.query.get(company_id)
            if company and company.logo_content:
                return company.logo_data_url
            return None
            
        except Exception as e:
            logger.error(f"❌ 获取企业Logo失败: {e}")
            return None
    
    @staticmethod
    def get_company_email_signature(company_id):
        """
        获取企业邮件签名
        
        Args:
            company_id: 企业ID
            
        Returns:
            str: Base64 Data URL 或 None
        """
        try:
            company = Company.query.get(company_id)
            if company and company.email_signature_content:
                return company.email_signature_data_url
            return None
            
        except Exception as e:
            logger.error(f"❌ 获取企业邮件签名失败: {e}")
            return None
    
    @staticmethod
    def delete_company_logo(company_id):
        """删除企业Logo"""
        try:
            company = Company.query.get(company_id)
            if not company:
                return {'success': False, 'message': '企业不存在'}
            
            if not company.logo_content:
                return {'success': False, 'message': '企业暂无Logo'}
            
            company.clear_logo()
            db.session.commit()
            
            logger.info(f"✅ 企业Logo已删除: {company.company_name}")
            return {'success': True, 'message': 'Logo删除成功'}
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ 删除企业Logo失败: {e}")
            return {'success': False, 'message': f'删除失败: {str(e)}'}
    
    @staticmethod
    def delete_email_signature(company_id):
        """删除邮件签名图片"""
        try:
            company = Company.query.get(company_id)
            if not company:
                return {'success': False, 'message': '企业不存在'}
            
            if not company.email_signature_content:
                return {'success': False, 'message': '企业暂无邮件签名'}
            
            company.clear_email_signature()
            db.session.commit()
            
            logger.info(f"✅ 企业邮件签名已删除: {company.company_name}")
            return {'success': True, 'message': '邮件签名删除成功'}
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ 删除邮件签名失败: {e}")
            return {'success': False, 'message': f'删除失败: {str(e)}'}
    
    @staticmethod
    def update_company_info(company_id, **kwargs):
        """
        更新企业详细信息
        
        Args:
            company_id: 企业ID
            **kwargs: 更新字段
        """
        try:
            company = Company.query.get(company_id)
            if not company:
                return {'success': False, 'message': '企业不存在'}
            
            # 允许更新的字段
            allowed_fields = [
                'detailed_address', 'postal_code', 'phone', 'fax', 
                'email', 'website', 'notes'
            ]
            
            updated_fields = []
            for field, value in kwargs.items():
                if field in allowed_fields and hasattr(company, field):
                    setattr(company, field, value)
                    updated_fields.append(field)
            
            if updated_fields:
                company.updated_at = company.get_local_time()
                db.session.commit()
                
                logger.info(f"✅ 企业信息更新成功: {company.company_name} - 更新字段: {', '.join(updated_fields)}")
                return {'success': True, 'message': '企业信息更新成功', 'updated_fields': updated_fields}
            else:
                return {'success': False, 'message': '没有有效的更新字段'}
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ 更新企业信息失败: {e}")
            return {'success': False, 'message': f'更新失败: {str(e)}'}
    
    @staticmethod
    def get_company_assets_info(company_id):
        """获取企业资产信息概览"""
        try:
            company = Company.query.get(company_id)
            if not company:
                return {'success': False, 'message': '企业不存在'}
            
            info = {
                'success': True,
                'company_info': {
                    'id': company.id,
                    'name': company.company_name,
                    'code': company.company_code,
                    'full_address': company.get_full_address(),
                    'phone': company.phone,
                    'email': company.email,
                    'website': company.website
                },
                'assets': {
                    'logo': {
                        'exists': bool(company.logo_content),
                        'filename': company.logo_filename,
                        'size_kb': company.logo_size_kb,
                        'type': company.logo_type
                    },
                    'email_signature': {
                        'exists': bool(company.email_signature_content),
                        'filename': company.email_signature_filename,
                        'size_kb': company.email_signature_size_kb,
                        'type': company.email_signature_type
                    }
                }
            }
            
            return info
            
        except Exception as e:
            logger.error(f"❌ 获取企业资产信息失败: {e}")
            return {'success': False, 'message': f'获取失败: {str(e)}'}
    
    @staticmethod
    def process_upload_file(file_obj):
        """
        处理上传文件对象
        
        Args:
            file_obj: Flask文件对象
            
        Returns:
            tuple: (file_data, filename) 或 (None, None)
        """
        try:
            if not file_obj or file_obj.filename == '':
                return None, None
            
            # 读取文件数据
            file_data = file_obj.read()
            filename = file_obj.filename
            
            # 重置文件指针（如果需要再次读取）
            file_obj.seek(0)
            
            return file_data, filename
            
        except Exception as e:
            logger.error(f"❌ 处理上传文件失败: {e}")
            return None, None

# 便捷函数
def get_company_logo_for_pdf(company_id):
    """为PDF生成获取企业Logo（兼容原有接口）"""
    return CompanyAssetService.get_company_logo(company_id)

def upload_company_logo_from_file(company_id, file_path):
    """从文件路径上传Logo（用于测试和批量导入）"""
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        filename = os.path.basename(file_path)
        return CompanyAssetService.upload_company_logo(company_id, file_data, filename)
        
    except Exception as e:
        logger.error(f"❌ 从文件上传Logo失败: {e}")
        return {'success': False, 'message': f'上传失败: {str(e)}'}