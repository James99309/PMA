#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出辅助API端点
提供客户搜索、联系人搜索等功能，支持导出信息补充组件
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from sqlalchemy import or_, and_
from app.models.customer import Company, Contact
from app.models.user import User
from app.decorators import permission_required
from app.utils.access_control import get_viewable_data
from app.utils.dictionary_helpers import company_type_label, company_type_color, industry_label
from flask_login import current_user
import logging
import traceback

logger = logging.getLogger(__name__)

# 创建蓝图
export_helpers_api = Blueprint('export_helpers_api', __name__, url_prefix='/api/export-helpers')


@export_helpers_api.route('/customers/search', methods=['GET'])
@login_required
@permission_required('customer', 'view')
def search_customers():
    """
    搜索客户列表
    支持关键词搜索公司名称、地址等字段
    支持按company_type过滤（可选）
    支持按has_inventory过滤（可选）
    """
    try:
        # 【调试】步骤1: 获取搜索参数
        logger.info("🔍 [DEBUG] 步骤1: 开始获取搜索参数")
        search_query = request.args.get('search', '').strip()
        # 安全解析 limit 参数，处理 undefined/null/非数字情况
        limit_str = request.args.get('limit', '20')
        try:
            limit = min(int(limit_str), 50) if limit_str and limit_str.isdigit() else 20
        except (ValueError, TypeError):
            limit = 20
        customer_id = request.args.get('customer_id', '')  # 可选的客户ID过滤
        company_type = request.args.get('company_type', '').strip()  # 可选的公司类型过滤
        has_inventory = request.args.get('has_inventory', '').strip().lower()  # 可选的库存过滤
        logger.info(f"🔍 [DEBUG] 参数: search='{search_query}', limit={limit}, company_type='{company_type}', has_inventory='{has_inventory}'")

        # 【调试】步骤2: 检查当前用户
        logger.info(f"🔍 [DEBUG] 步骤2: 当前用户 = {current_user.id if current_user else 'None'}, username = {current_user.username if current_user else 'None'}")

        # 【调试】步骤3: 构建基础查询
        logger.info("🔍 [DEBUG] 步骤3: 开始调用 get_viewable_data")
        query = get_viewable_data(Company, current_user)
        logger.info("🔍 [DEBUG] 步骤3: get_viewable_data 调用成功")

        # 应用公司类型过滤
        if company_type:
            logger.info(f"🔍 [DEBUG] 步骤4a: 应用公司类型过滤: {company_type}")
            types = [t.strip() for t in company_type.split(',') if t.strip()]
            if types:
                query = query.filter(Company.company_type.in_(types))

        # 应用库存过滤
        if has_inventory == 'true':
            logger.info("🔍 [DEBUG] 步骤4b: 应用库存过滤")
            from app.models.inventory import Inventory
            from app import db
            company_ids_with_inventory = db.session.query(Inventory.company_id)\
                .filter(Inventory.quantity > 0)\
                .distinct()\
                .subquery()
            query = query.filter(Company.id.in_(company_ids_with_inventory))

        # 应用搜索条件
        if search_query:
            logger.info(f"🔍 [DEBUG] 步骤4c: 应用搜索条件: {search_query}")
            search_conditions = or_(
                Company.company_name.ilike(f'%{search_query}%'),
                Company.company_code.ilike(f'%{search_query}%'),
                Company.address.ilike(f'%{search_query}%')
            )
            query = query.filter(search_conditions)

        # 如果指定了客户ID，直接查找该客户
        if customer_id:
            logger.info(f"🔍 [DEBUG] 步骤4d: 应用客户ID过滤: {customer_id}")
            query = query.filter(Company.id == customer_id)

        # 【调试】步骤5: 执行查询
        logger.info("🔍 [DEBUG] 步骤5: 开始执行数据库查询")
        customers = query.limit(limit).all()
        logger.info(f"🔍 [DEBUG] 步骤5: 查询返回 {len(customers)} 条记录")
        total_count = query.count() if len(customers) == limit else len(customers)

        # 【调试】步骤6: 格式化结果
        logger.info("🔍 [DEBUG] 步骤6: 开始格式化结果")
        results = []
        for idx, customer in enumerate(customers):
            try:
                # 获取主要联系人信息
                primary_contact = None
                if customer.contacts:
                    primary_contact = next((c for c in customer.contacts if c.is_primary), customer.contacts[0] if customer.contacts else None)

                customer_data = {
                    'id': customer.id,
                    'company_name': customer.company_name or '',
                    'company_code': customer.company_code or '',
                    'contact_person': primary_contact.name if primary_contact else '',
                    'contact_phone': primary_contact.phone if primary_contact else '',
                    'contact_email': primary_contact.email if primary_contact else '',
                    'industry': industry_label(customer.industry) if customer.industry else '',
                    'company_type': customer.company_type or '',
                    # 使用通用函数返回徽章信息（复用系统标准）
                    'company_type_label': company_type_label(customer.company_type) if customer.company_type else '',
                    'company_type_color': company_type_color(customer.company_type) if customer.company_type else '#6c757d',
                    'created_at': customer.created_at.strftime('%Y-%m-%d') if customer.created_at else '',
                    # 添加拥有者信息
                    'owner': {
                        'id': customer.owner.id if customer.owner else None,
                        'username': customer.owner.username if customer.owner else '',
                        'real_name': customer.owner.real_name if customer.owner else '',
                        'is_vendor_user': customer.owner.is_vendor_user() if customer.owner else False
                    } if customer.owner else None
                }
                results.append(customer_data)
            except Exception as item_error:
                logger.error(f"🔍 [DEBUG] 步骤6: 格式化第{idx}条记录失败 (id={customer.id}): {item_error}")
                logger.error(f"🔍 [DEBUG] 完整堆栈:\n{traceback.format_exc()}")
                raise

        logger.info(f"✅ 客户搜索成功: 查询='{search_query}', 结果={len(results)}条")

        return jsonify({
            'success': True,
            'results': results,
            'total': total_count,
            'query': search_query
        })

    except Exception as e:
        logger.error(f"❌ 客户搜索失败: {e}")
        logger.error(f"❌ 完整堆栈:\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e),
            'results': []
        }), 500


@export_helpers_api.route('/contacts/search', methods=['GET'])
@login_required
@permission_required('customer', 'view')
def search_contacts():
    """
    搜索联系人列表
    支持根据客户ID过滤和关键词搜索
    """
    try:
        # 获取搜索参数
        search_query = request.args.get('search', '').strip()
        customer_id = request.args.get('customer_id', '')
        limit = min(int(request.args.get('limit', 15)), 30)  # 最大30条
        
        # 构建基础查询 - 直接查询Contact表
        # 通过公司关联确保权限控制
        viewable_companies = get_viewable_data(Company, current_user)
        company_ids = [c.id for c in viewable_companies.all()]
        
        # 构建联系人查询
        query = Contact.query.filter(Contact.company_id.in_(company_ids))
        
        # 应用客户ID过滤
        if customer_id:
            try:
                customer_id_int = int(customer_id)
                query = query.filter(Contact.company_id == customer_id_int)
            except ValueError:
                pass  # 忽略无效的customer_id
        
        # 应用搜索条件
        if search_query:
            search_conditions = or_(
                Contact.name.ilike(f'%{search_query}%'),
                Contact.phone.ilike(f'%{search_query}%'),
                Contact.email.ilike(f'%{search_query}%'),
                Contact.position.ilike(f'%{search_query}%'),
                Contact.department.ilike(f'%{search_query}%')
            )
            query = query.filter(search_conditions)
        
        # 执行查询，包含公司信息
        contacts = query.join(Company).limit(limit).all()
        total_count = query.count() if len(contacts) == limit else len(contacts)
        
        # 格式化结果
        results = []
        for contact in contacts:
            contact_data = {
                'id': contact.id,
                'company_id': contact.company.id,
                'name': contact.name,
                'position': contact.position or '',
                'department': contact.department or '',
                'phone': contact.phone or '',
                'email': contact.email or '',
                'company_name': contact.company.company_name,
                'address': contact.company.address or '',
                'is_primary': contact.is_primary
            }
            results.append(contact_data)
        
        logger.info(f"✅ 联系人搜索成功: 查询='{search_query}', 客户ID={customer_id}, 结果={len(results)}条")
        
        return jsonify({
            'success': True,
            'results': results,
            'total': total_count,
            'query': search_query,
            'customer_id': customer_id
        })
        
    except Exception as e:
        logger.error(f"❌ 联系人搜索失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'results': []
        }), 500


@export_helpers_api.route('/customers/<int:customer_id>/contacts', methods=['GET'])
@login_required
@permission_required('customer', 'view')
def get_customer_contacts(customer_id):
    """
    获取指定客户的联系人列表
    """
    try:
        # 验证客户访问权限
        customer = get_viewable_data(Company, current_user).filter(Company.id == customer_id).first()
        
        if not customer:
            return jsonify({
                'success': False,
                'error': '客户未找到或无访问权限',
                'results': []
            }), 404
        
        # 构建联系人数据（基于当前的数据结构）
        contacts = []
        if customer.contact_person:
            contact_data = {
                'id': f"company_{customer.id}",
                'company_id': customer.id,
                'name': customer.contact_person,
                'position': '联系人',
                'phone': customer.contact_phone or '',
                'email': customer.contact_email or '',
                'company_name': customer.company_name,
                'address': customer.address or ''
            }
            contacts.append(contact_data)
        
        return jsonify({
            'success': True,
            'results': contacts,
            'total': len(contacts),
            'customer': {
                'id': customer.id,
                'company_name': customer.company_name,
                'address': customer.address
            }
        })
        
    except Exception as e:
        logger.error(f"❌ 获取客户联系人失败: customer_id={customer_id}, error={e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'results': []
        }), 500


@export_helpers_api.route('/export-templates', methods=['GET'])
@login_required
def get_export_templates():
    """
    获取导出模板列表
    用于提供预设的备注模板等
    """
    try:
        template_type = request.args.get('type', 'notes')
        
        templates = {
            'notes': [
                {
                    'id': 'default_quotation',
                    'name': '默认报价单备注',
                    'content': '交付条款：项目现场交付\n交付时间：合同签订后 4-6 周\n质保：12个月标准质保\n付款条款：合同签订后30天内付款\n其他：价格有效期30天'
                },
                {
                    'id': 'simple_quotation',
                    'name': '简化报价单备注',
                    'content': '交付时间：4-6周\n质保：12个月\n付款条款：30天内付款'
                },
                {
                    'id': 'custom_service',
                    'name': '定制服务备注',
                    'content': '本报价为定制化服务方案\n具体实施细节需进一步沟通确认\n价格可根据实际需求调整'
                }
            ]
        }
        
        return jsonify({
            'success': True,
            'templates': templates.get(template_type, []),
            'type': template_type
        })
        
    except Exception as e:
        logger.error(f"❌ 获取导出模板失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'templates': []
        }), 500


# 错误处理
@export_helpers_api.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': '请求参数错误',
        'details': str(error)
    }), 400


@export_helpers_api.errorhandler(403)
def forbidden(error):
    return jsonify({
        'success': False,
        'error': '权限不足',
        'details': str(error)
    }), 403


@export_helpers_api.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': '资源未找到',
        'details': str(error)
    }), 404


@export_helpers_api.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': '服务器内部错误',
        'details': str(error)
    }), 500