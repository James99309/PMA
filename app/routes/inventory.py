from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from app import db
from app.models.inventory import Inventory, InventoryTransaction, Settlement, SettlementDetail, PurchaseOrder, PurchaseOrderDetail
from app.models.customer import Company
from app.models.product import Product
from app.utils.inventory_helpers import update_inventory, process_settlement, generate_order_number, get_inventory_status, calculate_order_totals
from app.decorators import permission_required, permission_required_with_approval_context
from datetime import datetime, date
import logging
from app.models.pricing_order import SettlementOrder, SettlementOrderDetail
from sqlalchemy import select
from sqlalchemy.sql import func
import io
import pandas as pd
from app.helpers.approval_helpers import get_object_approval_instance, get_available_templates

logger = logging.getLogger(__name__)

inventory = Blueprint('inventory', __name__, url_prefix='/inventory')

@inventory.route('/')
@login_required
def index():
    """库存管理主页"""
    try:
        # 获取库存统计数据
        total_inventory = Inventory.query.count()
        
        # 今日入库数量
        today = date.today()
        today_in = InventoryTransaction.query.filter(
            InventoryTransaction.transaction_type == 'in',
            InventoryTransaction.transaction_date >= today
        ).count()
        
        # 低库存预警数量
        low_stock_count = Inventory.query.filter(
            Inventory.quantity <= Inventory.min_stock,
            Inventory.min_stock > 0
        ).count()
        
        # 待处理结算数量
        pending_settlements = Settlement.query.filter_by(status='pending').count()
        
        stats = {
            'total_inventory': total_inventory,
            'today_in': today_in,
            'low_stock': low_stock_count,
            'pending_settlements': pending_settlements
        }
        
        return render_template('inventory/index.html', stats=stats)
    except Exception as e:
        logger.error(f"加载库存统计数据失败: {str(e)}")
        # 使用默认值
        stats = {
            'total_inventory': 0,
            'today_in': 0,
            'low_stock': 0,
            'pending_settlements': 0
        }
        return render_template('inventory/index.html', stats=stats)

@inventory.route('/stock')
@login_required
@permission_required('inventory', 'view')
def stock_list():
    """库存列表 - 标准筛选搜索功能"""
    try:
        from flask_babel import gettext as _
        from sqlalchemy import func, or_
        logger.info("开始处理库存列表请求")
        
        # 获取标准搜索和筛选参数
        search = request.args.get('search', '').strip()
        company_id = request.args.get('company_id', '')
        stock_status = request.args.get('stock_status', '')
        
        logger.info(f"查询参数: search={search}, company_id={company_id}, stock_status={stock_status}")
        
        if company_id:
            # 公司视图：显示该公司的单独产品记录
            logger.info(f"使用公司视图模式，公司ID: {company_id}")
            
            query = Inventory.query.join(Product).join(Company).filter(
                Inventory.company_id == company_id,
                Company.is_deleted == False
            )
            
            # 应用搜索条件：搜索MN号、型号或产品名称
            if search:
                query = query.filter(
                    or_(
                        Product.product_mn.ilike(f'%{search}%'),
                        Product.model.ilike(f'%{search}%'),
                        Product.product_name.ilike(f'%{search}%')
                    )
                )
                logger.info(f"应用搜索条件: {search}")
            
            # 应用库存状态筛选
            if stock_status == 'normal':
                query = query.filter(Inventory.quantity > Inventory.min_stock)
            elif stock_status == 'low':
                query = query.filter(
                    Inventory.quantity <= Inventory.min_stock,
                    Inventory.quantity > 0
                )
            elif stock_status == 'zero':
                query = query.filter(Inventory.quantity == 0)
            
            query = query.order_by(Product.product_name, Product.model)
            inventories = query.all()
            
            # 转换为产品记录格式
            product_records = []
            for inv in inventories:
                product_records.append({
                    'inventory_id': inv.id,
                    'product_id': inv.product.id,
                    'product_name': inv.product.product_name,
                    'model': inv.product.model,
                    'specification': inv.product.specification,
                    'product_mn': inv.product.product_mn,
                    'brand': inv.product.brand,
                    'unit': inv.product.unit,
                    'total_quantity': inv.quantity,
                    'min_stock': inv.min_stock,
                    'updated_at': inv.updated_at,
                    'company_name': inv.company.company_name,
                    'is_aggregate': False
                })
            
        else:
            # 产品聚合视图：显示所有公司的产品合计
            logger.info("使用产品聚合视图模式")
            
            # 构建聚合查询
            query = db.session.query(
                Product.id,
                Product.product_name,
                Product.model,
                Product.specification,
                Product.product_mn,
                Product.brand,
                Product.unit,
                func.sum(Inventory.quantity).label('total_quantity'),
                func.max(Inventory.updated_at).label('updated_at')
            ).join(Inventory, Inventory.product_id == Product.id)\
             .join(Company, Inventory.company_id == Company.id)\
             .filter(Company.is_deleted == False)
            
            # 应用搜索条件：搜索MN号、型号或产品名称
            if search:
                query = query.filter(
                    or_(
                        Product.product_mn.ilike(f'%{search}%'),
                        Product.model.ilike(f'%{search}%'),
                        Product.product_name.ilike(f'%{search}%')
                    )
                )
                logger.info(f"应用搜索条件: {search}")
            
            # 按产品分组
            query = query.group_by(
                Product.id,
                Product.product_name,
                Product.model,
                Product.specification,
                Product.product_mn,
                Product.brand,
                Product.unit
            ).order_by(Product.product_name, Product.model)
            
            results = query.all()
            
            # 转换为产品记录格式
            product_records = []
            for result in results:
                # 对于聚合视图，计算最低库存警戒线（取最大值作为参考）
                min_stock_query = db.session.query(func.max(Inventory.min_stock)).join(Product).filter(
                    Product.id == result.id
                ).scalar() or 0
                
                product_records.append({
                    'inventory_id': None,
                    'product_id': result.id,
                    'product_name': result.product_name,
                    'model': result.model,
                    'specification': result.specification,
                    'product_mn': result.product_mn,
                    'brand': result.brand,
                    'unit': result.unit,
                    'total_quantity': result.total_quantity or 0,
                    'min_stock': min_stock_query,
                    'updated_at': result.updated_at,
                    'company_name': '所有公司合计',
                    'is_aggregate': True
                })
            
            # 应用库存状态筛选（在Python中进行，因为涉及聚合后的数据）
            if stock_status == 'normal':
                product_records = [r for r in product_records if r['total_quantity'] > r['min_stock']]
            elif stock_status == 'low':
                product_records = [r for r in product_records if r['total_quantity'] <= r['min_stock'] and r['total_quantity'] > 0]
            elif stock_status == 'zero':
                product_records = [r for r in product_records if r['total_quantity'] == 0]
        
        logger.info(f"产品记录数量: {len(product_records)}")
        
        # 计算统计数据
        total_items = len(product_records)
        normal_stock = len([r for r in product_records if r['total_quantity'] > r['min_stock']])
        low_stock_count = len([r for r in product_records if r['total_quantity'] <= r['min_stock'] and r['total_quantity'] > 0])
        zero_stock = len([r for r in product_records if r['total_quantity'] == 0])
        
        logger.info(f"统计数据: total={total_items}, normal={normal_stock}, low={low_stock_count}, zero={zero_stock}")
        
        # 获取有库存的公司列表
        company_ids_with_stock = select(Inventory.company_id).distinct()
        companies_with_stock = Company.query.filter(
            Company.id.in_(company_ids_with_stock),
            Company.is_deleted == False
        ).order_by(Company.company_name).all()
        
        # 构建标准筛选搜索配置
        filter_config = {
            'action_url': url_for('inventory.stock_list'),
            'form_id': 'stockFilterForm',
            'reset_url': url_for('inventory.stock_list'),
            'auto_submit': True,                # 启用自动筛选
            'ajax_mode': True,                  # 启用AJAX模式
            'ajax_endpoint': url_for('inventory.stock_list_ajax'),
            'ajax_target': '#stockTableBody',
            'dynamic_reset_button': True,       # 启用动态重置按钮
            
            'search_field': {
                'name': 'search',
                'label': '搜索',
                'placeholder': 'MN号、型号或产品名称',
                'value': search,
                'col_width': 4
            },
            
            'filter_fields': [
                {
                    'name': 'company_id',
                    'label': '公司',
                    'all_option_text': '全部公司（聚合视图）',
                    'current_value': company_id,
                    'col_width': 3,
                    'options': [
                        {'value': company.id, 'label': company.company_name, 'translate': False} 
                        for company in companies_with_stock
                    ]
                },
                {
                    'name': 'stock_status',
                    'label': '库存状态',
                    'all_option_text': '全部状态',
                    'current_value': stock_status,
                    'col_width': 3,
                    'options': [
                        {'value': 'normal', 'label': '正常库存', 'translate': True},
                        {'value': 'low', 'label': '低库存', 'translate': True},
                        {'value': 'zero', 'label': '零库存', 'translate': True}
                    ]
                }
            ],
            
            'search_button_text': '搜索',
            'reset_button_text': '重置'
        }
        
        # 通用列表组件配置
        list_config = {
            'module_name': 'stock',
            'title': '库存管理',
            'ajax_mode': True,
            
            # 无限滚动配置
            'infinite_scroll': {
                'enabled': True,
                'page_size': 50,
                'scroll_threshold': 100,
                'container_selector': '.table-responsive',
                'scroll_mode': 'container'
            },
            
            # 统计卡片配置
            'stats': {
                'cards': [
                    {
                        'id': 'total',
                        'title': '总库存',
                        'icon': 'fas fa-boxes',
                        'value': total_items,
                        'unit': '种',
                        'color': 'primary',
                        'clickable': True,
                        'click_params': {},
                        'data_key': 'total'
                    },
                    {
                        'id': 'normal',
                        'title': '正常库存',
                        'icon': 'fas fa-check-circle',
                        'value': normal_stock,
                        'unit': '种',
                        'color': 'success',
                        'clickable': True,
                        'click_params': {'stock_status': 'normal'},
                        'data_key': 'normal'
                    },
                    {
                        'id': 'low',
                        'title': '库存不足',
                        'icon': 'fas fa-exclamation-triangle',
                        'value': low_stock_count,
                        'unit': '种',
                        'color': 'warning',
                        'clickable': True,
                        'click_params': {'stock_status': 'low'},
                        'data_key': 'low'
                    },
                    {
                        'id': 'zero',
                        'title': '库存为零',
                        'icon': 'fas fa-times-circle',
                        'value': zero_stock,
                        'unit': '种',
                        'color': 'danger',
                        'clickable': True,
                        'click_params': {'stock_status': 'zero'},
                        'data_key': 'zero'
                    }
                ]
            },
            
            # 筛选配置
            'filter': filter_config,
            
            # 表格配置
            'table': {
                'ajax_target': 'stockTableBody',
                'title': '库存列表',
                'icon': 'fas fa-table',
                'fixed_height_scroll': True,     # 启用固定高度滚动（蓝色滚动条）
                'enhanced_striping': True,       # 启用增强斑马纹效果
                'use_custom_rows': True,         # 使用自定义行模板
                'custom_rows_template': 'inventory/stock_rows.html',
                'columns': [
                    {
                        'key': 'product_name',
                        'label': '产品名称',
                        'type': 'text',
                        'width': '200px'
                    },
                    {
                        'key': 'model_spec',
                        'label': '型号/规格',
                        'type': 'text', 
                        'width': '180px'
                    },
                    {
                        'key': 'product_mn',
                        'label': 'MN号',
                        'type': 'text',
                        'width': '120px'
                    },
                    {
                        'key': 'total_quantity',
                        'label': '当前库存',
                        'type': 'number',
                        'width': '100px',
                        'align': 'end'
                    },
                    {
                        'key': 'min_stock',
                        'label': '最低库存',
                        'type': 'number',
                        'width': '100px',
                        'align': 'end'
                    },
                    {
                        'key': 'stock_status',
                        'label': '状态',
                        'type': 'badge',
                        'width': '100px',
                        'render': 'render_stock_status_badge'
                    },
                    {
                        'key': 'brand',
                        'label': '品牌',
                        'type': 'text',
                        'width': '100px'
                    },
                    {
                        'key': 'unit',
                        'label': '单位',
                        'type': 'text',
                        'width': '80px'
                    },
                    {
                        'key': 'updated_at',
                        'label': '更新时间',
                        'type': 'date',
                        'width': '150px'
                    }
                ]
            }
        }

        # 准备模板数据
        template_data = {
            'product_records': product_records,
            'companies_with_stock': companies_with_stock,
            'filter_config': filter_config,
            'list_config': list_config,
            'is_company_view': bool(company_id),
            'stats': {
                'total': total_items,
                'normal': normal_stock,
                'low': low_stock_count,
                'zero': zero_stock
            }
        }
        
        logger.info(f"模板数据准备完成，product_records数量: {len(product_records)}")
        
        return render_template('inventory/stock_list.html', **template_data)
                             
    except Exception as e:
        logger.error(f"库存列表查询失败：{str(e)}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        # 回滚事务
        try:
            db.session.rollback()
        except Exception:
            pass
        flash(f'加载库存列表失败：{str(e)}', 'danger')
        
        # 错误时的默认filter_config
        error_filter_config = {
            'action_url': url_for('inventory.stock_list'),
            'form_id': 'stockFilterForm',
            'reset_url': url_for('inventory.stock_list'),
            'search_field': {
                'name': 'search',
                'label': '搜索',
                'placeholder': 'MN号、型号或产品名称',
                'value': '',
                'col_width': 4
            },
            'filter_fields': [],
            'search_button_text': '搜索',
            'reset_button_text': '重置'
        }
        
        # 错误时的默认list_config
        error_list_config = {
            'module_name': 'stock',
            'title': '库存管理',
            'ajax_mode': True,
            'stats': {
                'cards': [
                    {
                        'id': 'total',
                        'title': '总库存',
                        'icon': 'fas fa-boxes',
                        'value': 0,
                        'unit': '种',
                        'color': 'primary',
                        'data_key': 'total'
                    },
                    {
                        'id': 'normal',
                        'title': '正常库存',
                        'icon': 'fas fa-check-circle',
                        'value': 0,
                        'unit': '种',
                        'color': 'success',
                        'data_key': 'normal'
                    },
                    {
                        'id': 'low',
                        'title': '库存不足',
                        'icon': 'fas fa-exclamation-triangle',
                        'value': 0,
                        'unit': '种',
                        'color': 'warning',
                        'data_key': 'low'
                    },
                    {
                        'id': 'zero',
                        'title': '库存为零',
                        'icon': 'fas fa-times-circle',
                        'value': 0,
                        'unit': '种',
                        'color': 'danger',
                        'data_key': 'zero'
                    }
                ]
            },
            'filter': error_filter_config,
            'table': {
                'ajax_target': 'stockTableBody',
                'title': '库存列表',
                'icon': 'fas fa-table',
                'columns': []
            },
            'infinite_scroll': {'enabled': False}
        }

        return render_template('inventory/stock_list.html',
                             product_records=[],
                             companies_with_stock=[],
                             filter_config=error_filter_config,
                             list_config=error_list_config,
                             is_company_view=False,
                             stats={
                                 'total': 0,
                                 'normal': 0,
                                 'low': 0,
                                 'zero': 0
                             })

@inventory.route('/api/stock/filter', methods=['GET'])
@login_required
@permission_required('inventory', 'view')
def stock_list_ajax():
    """库存列表AJAX筛选API"""
    try:
        from flask_babel import gettext as _
        from sqlalchemy import func, or_
        
        # 获取搜索和筛选参数
        search = request.args.get('search', '').strip()
        company_id = request.args.get('company_id', '')
        stock_status = request.args.get('stock_status', '')
        
        # 分页参数
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        # 限制每次加载数量的范围
        if limit not in [10, 20, 30, 50]:
            limit = 20
        
        if company_id:
            # 公司视图：显示该公司的单独产品记录
            query = Inventory.query.join(Product).join(Company).filter(
                Inventory.company_id == company_id,
                Company.is_deleted == False
            )
            
            # 应用搜索条件
            if search:
                query = query.filter(
                    or_(
                        Product.product_mn.ilike(f'%{search}%'),
                        Product.model.ilike(f'%{search}%'),
                        Product.product_name.ilike(f'%{search}%')
                    )
                )
            
            # 应用库存状态筛选
            if stock_status == 'normal':
                query = query.filter(Inventory.quantity > Inventory.min_stock)
            elif stock_status == 'low':
                query = query.filter(
                    Inventory.quantity <= Inventory.min_stock,
                    Inventory.quantity > 0
                )
            elif stock_status == 'zero':
                query = query.filter(Inventory.quantity == 0)
            
            # 执行查询
            total_count = query.count()
            inventories = query.order_by(Product.product_name, Product.model).offset(offset).limit(limit).all()
            
            # 转换为产品记录格式
            product_records = []
            for inv in inventories:
                product_records.append({
                    'inventory_id': inv.id,
                    'product_id': inv.product.id,
                    'product_name': inv.product.product_name,
                    'model': inv.product.model,
                    'specification': inv.product.specification,
                    'product_mn': inv.product.product_mn,
                    'brand': inv.product.brand,
                    'unit': inv.product.unit,
                    'total_quantity': inv.quantity,
                    'min_stock': inv.min_stock,
                    'updated_at': inv.updated_at,
                    'company_name': inv.company.company_name,
                    'is_aggregate': False
                })
            
        else:
            # 产品聚合视图
            query = db.session.query(
                Product.id,
                Product.product_name,
                Product.model,
                Product.specification,
                Product.product_mn,
                Product.brand,
                Product.unit,
                func.sum(Inventory.quantity).label('total_quantity'),
                func.max(Inventory.updated_at).label('updated_at')
            ).join(Inventory, Inventory.product_id == Product.id)\
             .join(Company, Inventory.company_id == Company.id)\
             .filter(Company.is_deleted == False)
            
            # 应用搜索条件
            if search:
                query = query.filter(
                    or_(
                        Product.product_mn.ilike(f'%{search}%'),
                        Product.model.ilike(f'%{search}%'),
                        Product.product_name.ilike(f'%{search}%')
                    )
                )
            
            # 按产品分组
            query = query.group_by(
                Product.id,
                Product.product_name,
                Product.model,
                Product.specification,
                Product.product_mn,
                Product.brand,
                Product.unit
            ).order_by(Product.product_name, Product.model)
            
            # 执行查询
            total_query_count = query.count()
            results = query.offset(offset).limit(limit).all()
            
            # 转换为产品记录格式
            product_records = []
            for result in results:
                min_stock_query = db.session.query(func.max(Inventory.min_stock)).join(Product).filter(
                    Product.id == result.id
                ).scalar() or 0
                
                product_records.append({
                    'inventory_id': None,
                    'product_id': result.id,
                    'product_name': result.product_name,
                    'model': result.model,
                    'specification': result.specification,
                    'product_mn': result.product_mn,
                    'brand': result.brand,
                    'unit': result.unit,
                    'total_quantity': result.total_quantity or 0,
                    'min_stock': min_stock_query,
                    'updated_at': result.updated_at,
                    'company_name': '所有公司合计',
                    'is_aggregate': True
                })
            
            total_count = total_query_count
            
            # 应用库存状态筛选（在Python中进行）
            if stock_status == 'normal':
                product_records = [r for r in product_records if r['total_quantity'] > r['min_stock']]
            elif stock_status == 'low':
                product_records = [r for r in product_records if r['total_quantity'] <= r['min_stock'] and r['total_quantity'] > 0]
            elif stock_status == 'zero':
                product_records = [r for r in product_records if r['total_quantity'] == 0]
        
        # 计算统计数据（用于更新统计卡片）
        all_records_query = query if company_id else query
        all_results = all_records_query.all() if company_id else query.all()
        
        if company_id:
            all_product_records = []
            for inv in all_results:
                all_product_records.append({
                    'total_quantity': inv.quantity,
                    'min_stock': inv.min_stock
                })
        else:
            all_product_records = []
            for result in all_results:
                min_stock_query = db.session.query(func.max(Inventory.min_stock)).join(Product).filter(
                    Product.id == result.id
                ).scalar() or 0
                all_product_records.append({
                    'total_quantity': result.total_quantity or 0,
                    'min_stock': min_stock_query
                })
        
        # 应用状态筛选到统计数据
        if stock_status == 'normal':
            all_product_records = [r for r in all_product_records if r['total_quantity'] > r['min_stock']]
        elif stock_status == 'low':
            all_product_records = [r for r in all_product_records if r['total_quantity'] <= r['min_stock'] and r['total_quantity'] > 0]
        elif stock_status == 'zero':
            all_product_records = [r for r in all_product_records if r['total_quantity'] == 0]
        
        # 计算统计数据
        total_stats = len(all_product_records)
        normal_stats = len([r for r in all_product_records if r['total_quantity'] > r['min_stock']])
        low_stats = len([r for r in all_product_records if r['total_quantity'] <= r['min_stock'] and r['total_quantity'] > 0])
        zero_stats = len([r for r in all_product_records if r['total_quantity'] == 0])
        
        # 构建统计数据
        statistics = {
            'total_count': total_stats,
            'normal_count': normal_stats,
            'low_stock_count': low_stats,
            'zero_count': zero_stats
        }
        
        # 渲染HTML片段
        html = render_template('inventory/stock_rows.html', 
                              product_records=product_records,
                              is_company_view=bool(company_id))
        
        # 计算是否还有更多数据
        has_more = (offset + limit) < total_count
        
        return jsonify({
            'success': True,
            'html': html,
            'has_more': has_more,
            'total_count': total_count,
            'loaded_count': len(product_records),
            'statistics': statistics  # 用于更新统计卡片
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@inventory.route('/stock/<int:id>')
@login_required
@permission_required('inventory', 'view')
def stock_detail(id):
    """库存详情"""
    inventory = Inventory.query.get_or_404(id)
    
    # 获取相关的库存变动记录
    transactions = InventoryTransaction.query.filter_by(inventory_id=id)\
        .order_by(InventoryTransaction.transaction_date.desc())\
        .limit(20).all()
    
    return render_template('inventory/stock_detail.html', 
                         inventory=inventory,
                         transactions=transactions)

@inventory.route('/product/<int:product_id>/stock')
@login_required
@permission_required('inventory', 'view')
def product_stock_detail(product_id):
    """产品库存聚合详情（显示该产品在所有公司的库存情况）"""
    product = Product.query.get_or_404(product_id)
    
    # 获取该产品在所有公司的库存记录
    inventories = Inventory.query.join(Company).join(Product).filter(
        Product.id == product_id,
        Company.is_deleted == False
    ).order_by(Company.company_name).all()
    
    if not inventories:
        flash('该产品暂无库存记录', 'warning')
        return redirect(url_for('inventory.stock_list'))
    
    # 计算汇总数据
    total_quantity = sum(inv.quantity for inv in inventories)
    total_companies = len(inventories)
    
    # 获取该产品相关的库存变动记录（所有公司）
    inventory_ids = [inv.id for inv in inventories]
    transactions = InventoryTransaction.query.filter(
        InventoryTransaction.inventory_id.in_(inventory_ids)
    ).order_by(InventoryTransaction.transaction_date.desc()).limit(50).all()
    
    return render_template('inventory/product_stock_detail.html',
                         product=product,
                         inventories=inventories,
                         total_quantity=total_quantity,
                         total_companies=total_companies,
                         transactions=transactions)

@inventory.route('/update_min_stock', methods=['POST'])
@login_required
@permission_required('inventory', 'edit')
def update_min_stock():
    """更新最低库存"""
    try:
        inventory_id = request.form.get('inventory_id')
        min_stock = request.form.get('min_stock')
        
        if not inventory_id or min_stock is None:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        inventory = Inventory.query.get_or_404(inventory_id)
        
        # 验证数值
        try:
            min_stock_value = int(min_stock)
            if min_stock_value < 0:
                return jsonify({'success': False, 'message': '最低库存不能为负数'})
        except ValueError:
            return jsonify({'success': False, 'message': '最低库存必须是有效数字'})
        
        # 更新最低库存
        inventory.min_stock = min_stock_value
        db.session.commit()
        
        logger.info(f"用户 {current_user.username} 更新了库存 {inventory.id} 的最低库存为 {min_stock_value}")
        
        return jsonify({
            'success': True,
            'message': '最低库存更新成功',
            'new_value': min_stock_value
        })
        
    except Exception as e:
        logger.error(f"更新最低库存失败：{str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新失败：{str(e)}'})

@inventory.route('/update_max_stock', methods=['POST'])
@login_required
@permission_required('inventory', 'edit')
def update_max_stock():
    """更新最高库存"""
    try:
        inventory_id = request.form.get('inventory_id')
        max_stock = request.form.get('max_stock')
        
        if not inventory_id or max_stock is None:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        inventory = Inventory.query.get_or_404(inventory_id)
        
        # 验证数值
        try:
            max_stock_value = int(max_stock)
            if max_stock_value < 0:
                return jsonify({'success': False, 'message': '最高库存不能为负数'})
        except ValueError:
            return jsonify({'success': False, 'message': '最高库存必须是有效数字'})
        
        # 更新最高库存（0表示不限制）
        inventory.max_stock = max_stock_value if max_stock_value > 0 else None
        db.session.commit()
        
        logger.info(f"用户 {current_user.username} 更新了库存 {inventory.id} 的最高库存为 {max_stock_value}")
        
        return jsonify({
            'success': True,
            'message': '最高库存更新成功',
            'new_value': max_stock_value
        })
        
    except Exception as e:
        logger.error(f"更新最高库存失败：{str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新失败：{str(e)}'})

@inventory.route('/stock_action', methods=['POST'])
@login_required
@permission_required('inventory', 'edit')
def stock_action():
    """库存操作（入库、出库、调整）"""
    try:
        inventory_id = request.form.get('inventory_id')
        action_type = request.form.get('action_type')
        quantity = request.form.get('quantity')
        description = request.form.get('description', '')
        
        if not inventory_id or not action_type or not quantity:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        inventory = Inventory.query.get_or_404(inventory_id)
        
        # 验证数量
        try:
            quantity_value = int(quantity)
            if quantity_value <= 0:
                return jsonify({'success': False, 'message': '数量必须大于0'})
        except ValueError:
            return jsonify({'success': False, 'message': '数量必须是有效数字'})
        
        # 根据操作类型确定数量变动
        if action_type == 'in':
            quantity_change = quantity_value
            trans_type = 'in'
            action_desc = f'手动入库：{description}' if description else '手动入库'
        elif action_type == 'out':
            quantity_change = -quantity_value
            trans_type = 'out'
            action_desc = f'手动出库：{description}' if description else '手动出库'
        elif action_type == 'adjustment':
            # 调整：设置为指定的绝对数量
            quantity_change = quantity_value - inventory.quantity
            trans_type = 'adjustment'
            action_desc = f'库存调整至{quantity_value}：{description}' if description else f'库存调整至{quantity_value}'
        else:
            return jsonify({'success': False, 'message': '无效的操作类型'})
        
        # 检查出库时库存是否足够
        if quantity_change < 0 and inventory.quantity + quantity_change < 0:
            return jsonify({'success': False, 'message': f'库存不足，当前库存：{inventory.quantity}'})
        
        # 执行库存变动
        success, message, updated_inventory = update_inventory(
            company_id=inventory.company_id,
            product_id=inventory.product_id,
            quantity_change=quantity_change,
            transaction_type=trans_type,
            description=action_desc,
            reference_type='manual',
            user_id=current_user.id
        )
        
        if success:
            logger.info(f"用户 {current_user.username} 对库存 {inventory_id} 执行了 {action_type} 操作，数量变动：{quantity_change}")
            return jsonify({
                'success': True,
                'message': message,
                'new_quantity': updated_inventory.quantity,
                'action_type': action_type,
                'quantity_change': quantity_change
            })
        else:
            return jsonify({'success': False, 'message': message})
        
    except Exception as e:
        logger.error(f"库存操作失败：{str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': f'操作失败：{str(e)}'})

@inventory.route('/add_stock', methods=['GET', 'POST'])
@login_required
@permission_required('inventory', 'create')
def add_stock():
    """添加库存"""
    if request.method == 'POST':
        try:
            company_id = request.form.get('company_id')
            product_id = request.form.get('product_id')
            quantity = int(request.form.get('quantity', 0))
            description = request.form.get('description', '')
            
            if not company_id or not product_id or quantity <= 0:
                flash('请填写完整的库存信息', 'danger')
                return redirect(url_for('inventory.add_stock'))
            
            success, message, _ = update_inventory(
                company_id=company_id,
                product_id=product_id,
                quantity_change=quantity,
                transaction_type='in',
                description=description,
                reference_type='manual',
                user_id=current_user.id
            )
            
            if success:
                flash('库存添加成功', 'success')
                return redirect(url_for('inventory.stock_list'))
            else:
                flash(f'库存添加失败：{message}', 'danger')
                
        except Exception as e:
            logger.error(f"添加库存失败：{str(e)}")
            flash(f'操作失败：{str(e)}', 'danger')
    
    # 获取公司和产品列表
    companies = Company.query.filter(
        Company.is_deleted == False
    ).order_by(Company.company_name).all()
    products = Product.query.order_by(Product.product_name).all()
    
    return render_template('inventory/add_stock.html', 
                         companies=companies, 
                         products=products)

@inventory.route('/settlement')
@login_required
@permission_required('settlement', 'view')
def settlement_list():
    """结算明细列表 - 使用通用列表组件架构"""
    try:
        # 确保数据库连接正常，如果有失败的事务则回滚
        try:
            db.session.rollback()
        except:
            pass
        
        # 获取查询参数
        search = request.args.get('search', '').strip()
        company_filter = request.args.get('company_filter')
        status_filter = request.args.get('status_filter')
        settlement_company_filter = request.args.get('settlement_company_filter')
        
        # 构建基础查询 - 只获取已审批批价单的结算单明细
        from app.models.pricing_order import SettlementOrderDetail, SettlementOrder, PricingOrder
        query = db.session.query(SettlementOrderDetail).join(SettlementOrder).join(PricingOrder)
        
        # 关键过滤：只显示已审批批价单的结算明细
        query = query.filter(PricingOrder.status == 'approved')
        
        # 应用筛选条件
        if search:
            search_filter = db.or_(
                SettlementOrder.order_number.contains(search),
                SettlementOrderDetail.product_name.contains(search),
                SettlementOrderDetail.product_mn.contains(search)
            )
            query = query.filter(search_filter)
        
        if company_filter:
            query = query.filter(SettlementOrder.distributor_id == company_filter)
        
        if settlement_company_filter:
            query = query.filter(SettlementOrderDetail.settlement_company_id == settlement_company_filter)
        
        if status_filter:
            if status_filter == 'completed':
                query = query.filter(SettlementOrderDetail.settlement_status == 'settled')
            elif status_filter == 'pending':
                query = query.filter(SettlementOrderDetail.settlement_status == 'pending')
        
        # 计算统计数据
        all_settlement_details = query.all()
        
        total_count = len(all_settlement_details)
        settled_count = len([d for d in all_settlement_details if d.settlement_status == 'settled'])
        pending_count = len([d for d in all_settlement_details if d.settlement_status == 'pending'])
        draft_count = total_count - settled_count - pending_count
        
        total_amount = sum(float(d.total_price or 0) for d in all_settlement_details) / 10000
        settled_amount = sum(float(d.total_price or 0) for d in all_settlement_details if d.settlement_status == 'settled') / 10000
        pending_amount = sum(float(d.total_price or 0) for d in all_settlement_details if d.settlement_status == 'pending') / 10000
        draft_amount = total_amount - settled_amount - pending_amount
        
        # 本月结算统计
        current_month = datetime.now().strftime('%Y-%m')
        thismonth_details = [d for d in all_settlement_details if d.settlement_status == 'settled' and d.settlement_date and d.settlement_date.strftime('%Y-%m') == current_month]
        thismonth_count = len(thismonth_details)
        thismonth_amount = sum(float(d.total_price or 0) for d in thismonth_details) / 10000
        
        # 获取公司列表用于筛选
        settlement_order_company_ids = db.session.query(
            SettlementOrder.distributor_id
        ).distinct().subquery()
        
        settlement_companies_all = db.session.query(Company).filter(
            Company.id.in_(
                db.session.query(settlement_order_company_ids.c.distributor_id)
            ),
            Company.is_deleted == False
        ).order_by(Company.company_name).all()
        
        settlement_company_ids = db.session.query(
            SettlementOrderDetail.settlement_company_id
        ).filter(
            SettlementOrderDetail.settlement_company_id.isnot(None)
        ).distinct().subquery()
        
        settlement_companies = db.session.query(Company).filter(
            Company.id.in_(
                db.session.query(settlement_company_ids.c.settlement_company_id)
            )
        ).order_by(Company.company_name).all()
        
        # 构建筛选搜索配置
        filter_config = {
            'action_url': url_for('inventory.settlement_list'),
            'form_id': 'settlementFilterForm',
            'reset_url': url_for('inventory.settlement_list'),
            'auto_submit': True,
            'ajax_mode': True,
            'ajax_endpoint': url_for('inventory.settlement_list_ajax'),
            'ajax_target': '#settlementTableBody',
            'ajax_columns': 12,
            'dynamic_reset_button': True,
            'search_field_id': 'search',
            
            'search_field': {
                'name': 'search',
                'label': '搜索',
                'placeholder': '结算单号、项目名称或产品名称',
                'value': search,
                'col_width': 3
            },
            
            'filter_fields': [
                {
                    'name': 'company_filter',
                    'label': '结算单公司',
                    'all_option_text': '全部公司',
                    'current_value': company_filter if company_filter and request.args else '',
                    'col_width': 2,
                    'options': [
                        {'value': company.id, 'label': company.company_name, 'translate': False} 
                        for company in settlement_companies_all
                    ]
                },
                {
                    'name': 'settlement_company_filter',
                    'label': '结算目标公司',
                    'all_option_text': '全部目标公司',
                    'current_value': settlement_company_filter if settlement_company_filter and request.args else '',
                    'col_width': 2,
                    'options': [
                        {'value': company.id, 'label': company.company_name, 'translate': False} 
                        for company in settlement_companies
                    ]
                },
                {
                    'name': 'status_filter',
                    'label': '结算状态',
                    'all_option_text': '全部状态',
                    'current_value': status_filter if status_filter and request.args else '',
                    'col_width': 2,
                    'options': [
                        {'value': 'completed', 'label': '已结算', 'translate': True},
                        {'value': 'pending', 'label': '待结算', 'translate': True}
                    ]
                }
            ],
            
            'search_button_text': '搜索',
            'reset_button_text': '重置'
        }
        
        # 构建通用列表配置
        list_config = {
            'module_name': 'settlement',
            'title': '结算明细管理',  # 设置为与页面标题一致
            'ajax_mode': True,
            
            # 无限滚动配置
            'infinite_scroll': {
                'enabled': True,
                'page_size': 50,
                'scroll_threshold': 100,
                'container_selector': '.table-responsive',
                'scroll_mode': 'container'  # 明确设置为容器滚动模式
            },
            
            # 统计卡片配置
            'stats': {
                'cards': [
                    {
                        'id': 'total',
                        'title': '全部明细',
                        'icon': 'fas fa-list',
                        'value': total_count,
                        'amount': total_amount,
                        'unit': '条',
                        'amount_unit': '万元',
                        'color': 'primary',
                        'data_key': 'total'
                    },
                    {
                        'id': 'settled',
                        'title': '已结算',
                        'icon': 'fas fa-check-circle',
                        'value': settled_count,
                        'amount': settled_amount,
                        'unit': '条',
                        'amount_unit': '万元',
                        'color': 'success',
                        'data_key': 'settled'
                    },
                    {
                        'id': 'pending',
                        'title': '待结算',
                        'icon': 'fas fa-clock',
                        'value': pending_count,
                        'amount': pending_amount,
                        'unit': '条',
                        'amount_unit': '万元',
                        'color': 'warning',
                        'data_key': 'pending'
                    },
                    {
                        'id': 'thismonth',
                        'title': '本月结算',
                        'icon': 'fas fa-calendar-check',
                        'value': thismonth_count,
                        'amount': thismonth_amount,
                        'unit': '条',
                        'amount_unit': '万元',
                        'color': 'info',
                        'data_key': 'thismonth'
                    }
                ]
            },
            
            # 筛选配置
            'filter': filter_config,
            
            # 表格配置
            'table': {
                'ajax_target': 'settlementTableBody',
                'title': '结算明细列表',
                'icon': 'fas fa-table',
                'show_header': True,
                'fixed_height_scroll': True,     # 启用固定高度滚动
                'enhanced_striping': True,       # 启用增强斑马纹效果
                'columns': [
                    {
                        'key': 'settlement_order.order_number',
                        'label': '结算单号',
                        'type': 'link',
                        'url_template': '/inventory/settlement_detail/{settlement_order.id}',
                        'width': '140px'
                    },
                    {
                        'key': 'settlement_order.project.project_name',
                        'label': '项目名称',
                        'type': 'text',
                        'width': '200px'
                    },
                    {
                        'key': 'product_name',
                        'label': '产品名称',
                        'type': 'text',
                        'width': '180px'
                    },
                    {
                        'key': 'product_model',
                        'label': '产品型号',
                        'type': 'text',
                        'width': '120px'
                    },
                    {
                        'key': 'brand',
                        'label': '品牌',
                        'type': 'text',
                        'width': '100px'
                    },
                    {
                        'key': 'product_mn',
                        'label': '产品MN',
                        'type': 'text',
                        'width': '120px'
                    },
                    {
                        'key': 'quantity',
                        'label': '数量',
                        'type': 'number',
                        'align': 'center',
                        'width': '80px'
                    },
                    {
                        'key': 'unit_price',
                        'label': '单价',
                        'type': 'number',
                        'format': 'currency',
                        'align': 'end',
                        'width': '100px'
                    },
                    {
                        'key': 'total_price',
                        'label': '总价',
                        'type': 'number',
                        'format': 'currency',
                        'align': 'end',
                        'width': '120px'
                    },
                    {
                        'key': 'settlement_company',
                        'label': '结算目标公司',
                        'type': 'text',
                        'width': '150px'
                    },
                    {
                        'key': 'settlement_status',
                        'label': '结算状态',
                        'type': 'badge',
                        'render': 'render_settlement_status_badge',
                        'width': '100px'
                    },
                    {
                        'key': 'settlement_date',
                        'label': '结算时间',
                        'type': 'date',
                        'format': '%Y-%m-%d',
                        'width': '120px'
                    }
                ]
            }
        }
        
        return render_template('inventory/settlement_list.html', list_config=list_config)
                             
    except Exception as e:
        logger.error(f"获取结算明细列表失败：{str(e)}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        flash(f'加载结算明细列表失败：{str(e)}', 'danger')
        
        # 错误时的默认list_config
        error_list_config = {
            'module_name': 'settlement',
            'title': '结算明细',  # 设置为与页面标题一致
            'ajax_mode': True,
            'stats': {'cards': []},
            'filter': {
                'action_url': url_for('inventory.settlement_list'),
                'form_id': 'settlementFilterForm',
                'reset_url': url_for('inventory.settlement_list'),
                'search_field': {
                    'name': 'search',
                    'label': '搜索',
                    'placeholder': '结算单号、项目名称或产品名称',
                    'value': '',
                    'col_width': 3
                },
                'filter_fields': [],
                'search_button_text': '搜索',
                'reset_button_text': '重置'
            },
            'table': {
                'ajax_target': 'settlementTableBody',
                'columns': []
            }
        }
        
        return render_template('inventory/settlement_list.html', list_config=error_list_config)

@inventory.route('/settlement/export')
@login_required
@permission_required('inventory', 'view')
def export_settlement_list():
    """导出结算明细列表为Excel"""
    try:
        # 获取查询参数（和settlement_list函数相同的逻辑）
        search = request.args.get('search', '').strip()
        company_filter = request.args.get('company_filter')
        status_filter = request.args.get('status_filter')
        settlement_company_filter = request.args.get('settlement_company_filter')
        
        # 构建基础查询 - 只获取已审批批价单的结算单明细
        from app.models.pricing_order import SettlementOrderDetail, SettlementOrder, PricingOrder
        query = db.session.query(SettlementOrderDetail).join(SettlementOrder).join(PricingOrder)
        
        # 关键过滤：只显示已审批批价单的结算明细
        query = query.filter(PricingOrder.status == 'approved')
        
        # 搜索条件
        if search:
            search_filter = db.or_(
                SettlementOrder.order_number.contains(search),
                SettlementOrderDetail.product_name.contains(search),
                SettlementOrderDetail.product_mn.contains(search)
            )
            query = query.filter(search_filter)
        
        # 结算单公司过滤（分销商）
        if company_filter:
            query = query.filter(SettlementOrder.distributor_id == company_filter)
        
        # 结算目标公司过滤
        if settlement_company_filter:
            query = query.filter(SettlementOrderDetail.settlement_company_id == settlement_company_filter)
        
        # 结算状态过滤
        if status_filter:
            if status_filter == 'completed':
                query = query.filter(SettlementOrderDetail.settlement_status == 'settled')
            elif status_filter == 'pending':
                query = query.filter(SettlementOrderDetail.settlement_status == 'pending')
        
        # 排序
        query = query.order_by(SettlementOrder.created_at.desc(), SettlementOrderDetail.id.desc())
        
        # 获取所有数据（不分页）
        settlement_details = query.all()
        
        # 准备筛选条件信息
        filter_info = []
        filter_info.append(['导出时间', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        filter_info.append(['数据总数', f'{len(settlement_details)} 条记录'])
        filter_info.append(['', ''])  # 空行
        filter_info.append(['筛选条件', ''])
        
        # 添加具体筛选条件
        if search:
            filter_info.append(['搜索关键词', search])
        
        if company_filter:
            # 获取公司名称
            from app.models.customer import Company
            company = Company.query.get(company_filter)
            company_name = company.company_name if company else f'ID:{company_filter}'
            filter_info.append(['结算单公司', company_name])
        
        if settlement_company_filter:
            from app.models.customer import Company
            company = Company.query.get(settlement_company_filter)
            company_name = company.company_name if company else f'ID:{settlement_company_filter}'
            filter_info.append(['结算目标公司', company_name])
        
        if status_filter:
            status_map = {
                'completed': '已结算',
                'pending': '待结算'
            }
            filter_info.append(['结算状态', status_map.get(status_filter, status_filter)])
        
        # 如果没有任何筛选条件
        if not any([search, company_filter, settlement_company_filter, status_filter]):
            filter_info.append(['筛选状态', '未应用筛选条件，显示全部数据'])
        
        filter_info.append(['', ''])  # 空行
        
        # 准备导出数据
        export_data = []
        for detail in settlement_details:
            export_data.append({
                '结算单号': detail.settlement_order.order_number,
                '项目名称': detail.settlement_order.project.project_name if detail.settlement_order.project else '无项目',
                '产品名称': detail.product_name if detail.product_name else '无产品',
                '产品型号': detail.product_model if detail.product_model else '-',
                '品牌': detail.brand if detail.brand else '-',
                '产品MN': detail.product_mn if detail.product_mn else '-',
                '数量': detail.quantity,
                '单价(元)': round(detail.unit_price, 2),
                '总价(元)': round(detail.total_price, 2),
                '结算目标公司': detail.settlement_company.company_name if detail.settlement_company else '未指定',
                '结算状态': '已结算' if detail.settlement_status == 'settled' else '待结算',
                '结算时间': detail.settlement_date.strftime('%Y-%m-%d %H:%M') if detail.settlement_date else '-'
            })
        
        # 创建DataFrame
        df = pd.DataFrame(export_data)
        
        # 创建筛选条件DataFrame
        filter_df = pd.DataFrame(filter_info, columns=['项目', '值'])
        
        # 生成文件名
        current_time = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f'结算明细表-{current_time}.xlsx'
        
        # 创建Excel文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 先写入筛选条件信息
            filter_df.to_excel(writer, sheet_name='结算明细', index=False, header=False, startrow=0)
            
            # 计算数据开始行（筛选条件行数 + 2行间距）
            data_start_row = len(filter_info) + 2
            
            # 写入数据表格
            df.to_excel(writer, sheet_name='结算明细', index=False, startrow=data_start_row)
            
            # 获取工作表并设置格式
            worksheet = writer.sheets['结算明细']
            
            # 设置筛选条件区域的格式
            from openpyxl.styles import Font, PatternFill, Alignment
            
            # 标题行格式（导出时间、数据总数等）
            title_font = Font(bold=True, size=12)
            filter_font = Font(bold=True, size=10, color='0066CC')
            
            for row in range(1, len(filter_info) + 1):
                cell_a = worksheet.cell(row=row, column=1)
                cell_b = worksheet.cell(row=row, column=2)
                
                # 设置关键信息的格式
                if row <= 2:  # 导出时间和数据总数
                    cell_a.font = title_font
                    cell_b.font = title_font
                elif cell_a.value == '筛选条件':  # 筛选条件标题
                    cell_a.font = filter_font
                elif cell_a.value and cell_a.value not in ['', '筛选条件']:  # 具体筛选项
                    cell_a.font = Font(bold=True, size=9)
            
            # 设置数据表格标题行格式
            header_row = data_start_row + 1
            header_font = Font(bold=True, size=11, color='FFFFFF')
            header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
            
            for col in range(1, len(df.columns) + 1):
                cell = worksheet.cell(row=header_row, column=col)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # 设置列宽
            column_widths = {
                'A': 18,  # 项目/结算单号
                'B': 25,  # 值/项目名称
                'C': 20,  # 产品名称
                'D': 15,  # 产品型号
                'E': 12,  # 品牌
                'F': 15,  # 产品MN
                'G': 10,  # 数量
                'H': 12,  # 单价
                'I': 12,  # 总价
                'J': 20,  # 结算目标公司
                'K': 12,  # 结算状态
                'L': 18,  # 结算时间
            }
            
            for col, width in column_widths.items():
                worksheet.column_dimensions[col].width = width
            
            # 设置数据区域的边框
            from openpyxl.styles import Border, Side
            thin_border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            
            # 为数据表格添加边框
            for row in range(header_row, header_row + len(df) + 1):
                for col in range(1, len(df.columns) + 1):
                    worksheet.cell(row=row, column=col).border = thin_border
        
        output.seek(0)
        
        logger.info(f"用户 {current_user.username} 导出结算明细列表，共 {len(settlement_details)} 条记录")
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        logger.error(f"导出结算明细列表失败：{str(e)}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        flash(f'导出失败：{str(e)}', 'danger')
        return redirect(url_for('inventory.settlement_list'))

@inventory.route('/settlement_orders')
@login_required
@permission_required('settlement', 'view')
def settlement_order_list():
    """结算单列表"""
    try:
        # 确保数据库事务状态干净
        try:
            db.session.rollback()
        except Exception:
            pass
            
        print("=== 执行了 settlement_order_list 函数 ===")
        logger.info("=== 执行了 settlement_order_list 函数 ===")
        
        # 获取搜索和筛选参数
        search = request.args.get('search', '').strip()
        settlement_company_id = request.args.get('settlement_company', '')
        settlement_status = request.args.get('settlement_status', '')
        
        # 调试信息：检查参数获取情况
        logger.info(f"=== 结算单列表参数调试 ===")
        logger.info(f"URL参数: {dict(request.args)}")
        logger.info(f"搜索关键词: '{search}'")
        logger.info(f"结算公司ID: '{settlement_company_id}'")
        logger.info(f"结算状态: '{settlement_status}'")
        
        # 构建基础查询：只获取来自已审批批价单的结算单
        from app.models.pricing_order import PricingOrder
        from app.models.project import Project
        
        query = SettlementOrder.query.join(
            PricingOrder, SettlementOrder.pricing_order_id == PricingOrder.id
        ).join(
            Project, SettlementOrder.project_id == Project.id
        ).filter(
            PricingOrder.status == 'approved'
        )
        
        # 应用搜索条件
        if search:
            query = query.filter(
                db.or_(
                    SettlementOrder.order_number.ilike(f'%{search}%'),
                    Project.project_name.ilike(f'%{search}%')
                )
            )
        
        # 应用公司筛选
        if settlement_company_id:
            query = query.filter(SettlementOrder.dealer_id == settlement_company_id)
        
        # 应用状态筛选
        if settlement_status:
            query = query.filter(SettlementOrder.settlement_status == settlement_status)
        
        # 执行查询，添加事务保护
        try:
            settlement_orders = query.order_by(SettlementOrder.created_at.desc()).all()
        except Exception as e:
            logger.error(f"结算单查询失败: {e}")
            # 回滚失败的事务
            try:
                db.session.rollback()
            except Exception:
                pass
            # 返回空结果，避免页面崩溃
            settlement_orders = []
        
        # 初始化统计变量
        fully_settled_count = 0
        partially_settled_count = 0
        pending_count = 0  # 正确初始化
        
        fully_settled_amount = 0.0
        partially_settled_amount = 0.0
        pending_amount = 0.0  # 正确初始化
        
        # 先统计数据库中实际的状态分布
        status_distribution = {}
        for order in settlement_orders:
            status = order.status
            if status not in status_distribution:
                status_distribution[status] = {'count': 0, 'amount': 0.0}
            status_distribution[status]['count'] += 1
            status_distribution[status]['amount'] += float(order.total_amount or 0.0)
        
        logger.info("=== 数据库中结算单实际状态分布 ===")
        for status, data in status_distribution.items():
            logger.info(f"状态 '{status}': {data['count']} 单, {data['amount']:.2f} 元")
        
        # 统计每个结算单的结算状态（只统计已审批批价单的结算单）
        for order in settlement_orders:
            order_amount = order.total_amount or 0.0
            # 确认是已审批批价单的结算单
            pricing_order = order.pricing_order_ref
            if pricing_order and pricing_order.status == 'approved':
                settlement_status = order.settlement_status
                
                logger.info(f"结算单 {order.order_number}: 批价单状态='{pricing_order.status}', 结算状态='{settlement_status}', 金额={order_amount}")
                
                # 根据settlement_status字段统计数量和金额
                if settlement_status == 'pending':
                    pending_count += 1
                    pending_amount += order_amount
                    logger.info(f"  -> 计入待结算: 当前待结算数量={pending_count}")
                elif settlement_status == 'fully_settled':
                    fully_settled_count += 1
                    fully_settled_amount += order_amount
                    logger.info(f"  -> 计入完全结算: 当前完全结算数量={fully_settled_count}")
                elif settlement_status == 'partially_settled':
                    partially_settled_count += 1
                    partially_settled_amount += order_amount
                    logger.info(f"  -> 计入部分结算: 当前部分结算数量={partially_settled_count}")
                else:
                    # 如果有其他状态，记录并按待结算处理
                    logger.warning(f"结算单 {order.order_number} 有未知结算状态: '{settlement_status}', 按待结算处理")
                    pending_count += 1
                    pending_amount += order_amount
                    logger.info(f"  -> 未知状态计入待结算: 当前待结算数量={pending_count}")
            else:
                logger.info(f"跳过非已审批批价单的结算单: {order.order_number} (批价单状态: {pricing_order.status if pricing_order else 'None'})")
        
        # 计算总数和总金额
        total_count = len(settlement_orders)
        total_amount = sum(float(order.total_amount or 0.0) for order in settlement_orders)
        
        # 输出调试信息
        logger.info(f"=== 结算单列表统计 ===")
        logger.info(f"总结算单数: {total_count}, 完全结算: {fully_settled_count}, 部分结算: {partially_settled_count}, 待结算: {pending_count}")
        logger.info(f"总金额: {total_amount}, 完全结算金额: {fully_settled_amount}, 部分结算金额: {partially_settled_amount}, 待结算金额: {pending_amount}")
        logger.info(f"传递给模板的待结算数量: {pending_count}, 待结算金额万元: {float(pending_amount) / 10000}")
        
        # 验证数学关系
        calculated_total = fully_settled_count + partially_settled_count + pending_count
        if calculated_total != total_count:
            logger.warning(f"结算单数量统计不匹配！计算值: {calculated_total}, 实际值: {total_count}")
        
        # 获取有结算单的公司用于筛选下拉框
        company_ids_with_settlements = db.session.query(Company.id.distinct()).join(
            SettlementOrder, Company.id == SettlementOrder.dealer_id
        ).join(
            PricingOrder, SettlementOrder.pricing_order_id == PricingOrder.id
        ).filter(
            PricingOrder.status == 'approved',
            Company.is_deleted == False
        ).all()
        
        company_ids = [row[0] for row in company_ids_with_settlements]
        companies = Company.query.filter(
            Company.id.in_(company_ids),
            Company.is_deleted == False
        ).order_by(Company.company_name).all()
        
        # 调试筛选配置构建
        logger.info(f"=== 构建筛选配置 ===")
        logger.info(f"即将传递给模板的 settlement_status: '{settlement_status}'")
        logger.info(f"settlement_status 是否为空: {settlement_status == ''}")
        logger.info(f"settlement_status 布尔值: {bool(settlement_status)}")
        
        # 构建筛选搜索配置
        filter_config = {
            'action_url': url_for('inventory.settlement_order_list'),
            'form_id': 'settlementOrderFilterForm',
            'reset_url': url_for('inventory.settlement_order_list'),
            'auto_submit': True,                # 启用自动筛选（关键配置）
            'ajax_mode': True,                  # 启用AJAX模式
            'ajax_endpoint': url_for('inventory.settlement_order_list_ajax'),
            'ajax_target': '#settlementTableBody',
            'ajax_columns': 7,
            'dynamic_reset_button': True,       # 启用动态重置按钮
            'search_field_id': 'search',        # 搜索字段ID（修复搜索功能）
            
            'search_field': {
                'name': 'search',
                'label': '搜索',
                'placeholder': '结算单编号或项目名称',
                'value': search,
                'col_width': 4
            },
            
            'filter_fields': [
                {
                    'name': 'settlement_company',
                    'label': '结算公司',
                    'all_option_text': '全部公司',
                    'current_value': settlement_company_id if settlement_company_id and request.args else '',
                    'col_width': 3,
                    'options': [
                        {'value': company.id, 'label': company.company_name, 'translate': False} 
                        for company in companies
                    ]
                },
                {
                    'name': 'settlement_status',
                    'label': '结算状态',
                    'all_option_text': '全部状态',
                    'current_value': settlement_status if settlement_status and request.args else '',
                    'col_width': 3,
                    'options': [
                        {'value': 'pending', 'label': '待结算', 'translate': True},
                        {'value': 'partially_settled', 'label': '部分结算', 'translate': True},
                        {'value': 'fully_settled', 'label': '已结算', 'translate': True}
                    ]
                }
            ],
            
            'search_button_text': '搜索',
            'reset_button_text': '重置'
        }
        
        # 统计数据
        stats = {
            'total': total_count,
            'total_amount': float(total_amount) / 10000,  # 转换为万元
            'fully_settled': fully_settled_count,
            'fully_settled_amount': float(fully_settled_amount) / 10000,
            'partially_settled': partially_settled_count,
            'partially_settled_amount': float(partially_settled_amount) / 10000,
            'pending': pending_count,  # 使用真实统计值
            'pending_amount': float(pending_amount) / 10000  # 使用真实统计值
        }
        
        # 构建通用列表配置
        list_config = {
            'module_name': 'settlement',
            'title': '结算管理',  # 设置为与页面标题一致
            'ajax_mode': True,
            
            # 无限滚动配置
            'infinite_scroll': {
                'enabled': True,
                'page_size': 60,
                'scroll_threshold': 100,
                'container_selector': '.table-responsive',
                'scroll_mode': 'container'  # 明确设置为容器滚动模式
            },
            
            # 统计卡片配置
            'stats': {
                'cards': [
                    {
                        'id': 'total',
                        'title': '总结算',
                        'icon': 'fas fa-list',
                        'value': stats['total'],
                        'amount': f"{stats['total_amount']:.2f}",
                        'unit': '单',
                        'amount_unit': '万元',
                        'color': 'primary',
                        'data_key': 'total'
                    },
                    {
                        'id': 'fullySettled',
                        'title': '已结算',
                        'icon': 'fas fa-check-circle',
                        'value': stats['fully_settled'],
                        'amount': f"{stats['fully_settled_amount']:.2f}",
                        'unit': '单',
                        'amount_unit': '万元',
                        'color': 'success',
                        'data_key': 'fully_settled'
                    },
                    {
                        'id': 'partiallySettled',
                        'title': '部分结算',
                        'icon': 'fas fa-exclamation-triangle',
                        'value': stats['partially_settled'],
                        'amount': f"{stats['partially_settled_amount']:.2f}",
                        'unit': '单',
                        'amount_unit': '万元',
                        'color': 'warning',
                        'data_key': 'partially_settled'
                    },
                    {
                        'id': 'pending',
                        'title': '待结算',
                        'icon': 'fas fa-clock',
                        'value': stats['pending'],
                        'amount': f"{stats['pending_amount']:.2f}",
                        'unit': '单',
                        'amount_unit': '万元',
                        'color': 'danger',
                        'data_key': 'pending'
                    }
                ]
            },
            
            # 筛选配置（复用现有筛选组件）
            'filter': filter_config,
            
            # 表格配置
            'table': {
                'ajax_target': 'settlementTableBody',
                'title': '结算单列表',
                'icon': 'fas fa-table',
                'show_batch_actions': False,
                'fixed_height_scroll': True,     # 启用固定高度滚动
                'enhanced_striping': True,       # 启用增强斑马纹效果
                'columns': [
                    {
                        'key': 'order_number',
                        'label': '结算单编号',
                        'type': 'link',
                        'width': '140px'
                    },
                    {
                        'key': 'project_name',
                        'label': '关联项目',
                        'type': 'text',
                        'width': '200px'
                    },
                    {
                        'key': 'dealer_name',
                        'label': '结算公司',
                        'type': 'text',
                        'width': '150px'
                    },
                    {
                        'key': 'product_count',
                        'label': '产品数量',
                        'type': 'number',
                        'align': 'end',
                        'width': '80px'
                    },
                    {
                        'key': 'total_amount',
                        'label': '总金额',
                        'type': 'text',  # 已格式化的金额字符串
                        'align': 'end',
                        'width': '120px'
                    },
                    {
                        'key': 'settlement_status',
                        'label': '结算情况',
                        'type': 'badge',
                        'render': 'render_settlement_situation_badge',
                        'width': '100px'
                    },
                    {
                        'key': 'created_time',
                        'label': '创建时间',
                        'type': 'text',
                        'width': '120px'
                    }
                ]
            }
        }
        
        logger.info(f"即将传递给模板的数据: pending_count={stats['pending']}, pending_amount={stats['pending_amount']}")
        
        return render_template('inventory/settlement_order_list.html', 
                             settlement_orders=settlement_orders,
                             list_config=list_config,
                             companies=companies)
                             
    except Exception as e:
        logger.error(f"获取结算单列表失败：{str(e)}")
        flash(f'获取结算单列表失败：{str(e)}', 'danger')
        # 获取有结算单的公司以供筛选使用
        try:
            companies = db.session.query(Company).join(
                SettlementOrder, Company.id == SettlementOrder.dealer_id
            ).join(
                PricingOrder, SettlementOrder.pricing_order_id == PricingOrder.id
            ).filter(
                PricingOrder.status == 'approved',
                Company.is_deleted == False
            ).distinct().order_by(Company.company_name).all()
        except:
            companies = []
        
        # 错误处理时的默认列表配置
        error_list_config = {
            'module_name': 'settlement',
            'title': '结算单列表',
            'ajax_mode': True,
            'stats': {
                'cards': [
                    {'id': 'total', 'title': '总结算', 'icon': 'fas fa-list', 'value': 0, 'amount': '0.00', 'unit': '单', 'amount_unit': '万元', 'color': 'primary', 'data_key': 'total'},
                    {'id': 'fullySettled', 'title': '已结算', 'icon': 'fas fa-check-circle', 'value': 0, 'amount': '0.00', 'unit': '单', 'amount_unit': '万元', 'color': 'success', 'data_key': 'fully_settled'},
                    {'id': 'partiallySettled', 'title': '部分结算', 'icon': 'fas fa-exclamation-triangle', 'value': 0, 'amount': '0.00', 'unit': '单', 'amount_unit': '万元', 'color': 'warning', 'data_key': 'partially_settled'},
                    {'id': 'pending', 'title': '待结算', 'icon': 'fas fa-clock', 'value': 0, 'amount': '0.00', 'unit': '单', 'amount_unit': '万元', 'color': 'danger', 'data_key': 'pending'}
                ]
            },
            'filter': {
                'action_url': url_for('inventory.settlement_order_list'),
                'form_id': 'settlementOrderFilterForm',
                'reset_url': url_for('inventory.settlement_order_list'),
                'search_field': {'name': 'search', 'label': '搜索', 'placeholder': '结算单编号或项目名称', 'value': '', 'col_width': 4},
                'filter_fields': [],
                'search_button_text': '搜索',
                'reset_button_text': '重置'
            },
            'table': {
                'ajax_target': 'settlementTableBody',
                'title': '结算单列表',
                'icon': 'fas fa-table',
                'show_batch_actions': False,
                'columns': []
            }
        }
        
        return render_template('inventory/settlement_order_list.html',
                             settlement_orders=[],
                             companies=companies,
                             list_config=error_list_config)

@inventory.route('/settlement_process/<order_number>')
@login_required
def settlement_process(order_number):
    """结算处理页面"""
    try:
        settlement_order = SettlementOrder.query.filter_by(order_number=order_number).first_or_404()
        # 只获取 company_type 为 'dealer' 且未删除的公司
        companies = Company.query.filter(
            Company.company_type == 'dealer',
            Company.is_deleted == False
        ).order_by(Company.company_name).all()
        
        # 获取URL参数中的选中公司ID
        selected_company_id = request.args.get('selected_company')
        
        return render_template('inventory/settlement_process.html',
                             settlement_order=settlement_order,
                             companies=companies,
                             selected_company_id=selected_company_id)
                             
    except Exception as e:
        logger.error(f"获取结算处理页面失败：{str(e)}")
        flash(f'获取结算处理页面失败：{str(e)}', 'danger')
        return redirect(url_for('inventory.settlement_order_list'))

@inventory.route('/settlement_orders/export')
@login_required
@permission_required('settlement', 'view')
def export_settlement_orders():
    """导出结算单列表为Excel"""
    try:
        # 获取筛选参数
        search = request.args.get('search', '').strip()
        settlement_company_id = request.args.get('settlement_company', '')
        settlement_status = request.args.get('settlement_status', '')
        
        # 构建查询（复用列表页面的逻辑）
        from app.models.pricing_order import PricingOrder
        from app.models.project import Project
        
        query = SettlementOrder.query.join(
            PricingOrder, SettlementOrder.pricing_order_id == PricingOrder.id
        ).join(
            Project, SettlementOrder.project_id == Project.id
        ).filter(
            PricingOrder.status == 'approved'
        )
        
        # 应用搜索条件
        if search:
            query = query.filter(
                db.or_(
                    SettlementOrder.order_number.ilike(f'%{search}%'),
                    Project.project_name.ilike(f'%{search}%')
                )
            )
        
        # 应用公司筛选
        if settlement_company_id:
            query = query.filter(SettlementOrder.dealer_id == settlement_company_id)
        
        # 应用状态筛选
        if settlement_status:
            query = query.filter(SettlementOrder.settlement_status == settlement_status)
        
        # 执行查询
        settlement_orders = query.order_by(SettlementOrder.created_at.desc()).all()
        
        # 准备筛选条件信息
        filter_info = []
        filter_info.append(['导出时间', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        filter_info.append(['数据总数', f'{len(settlement_orders)} 条记录'])
        filter_info.append(['', ''])  # 空行
        filter_info.append(['筛选条件', ''])
        
        # 添加具体筛选条件
        if search:
            filter_info.append(['搜索关键词', search])
        
        if settlement_company_id:
            company = Company.query.get(settlement_company_id)
            company_name = company.company_name if company else f'ID:{settlement_company_id}'
            filter_info.append(['结算公司', company_name])
        
        if settlement_status:
            status_map = {
                'pending': '待结算',
                'partially_settled': '部分结算',
                'fully_settled': '已结算'
            }
            filter_info.append(['结算状态', status_map.get(settlement_status, settlement_status)])
        
        # 如果没有任何筛选条件
        if not any([search, settlement_company_id, settlement_status]):
            filter_info.append(['筛选状态', '未应用筛选条件，显示全部数据'])
        
        filter_info.append(['', ''])  # 空行
        
        # 准备导出数据
        export_data = []
        for order in settlement_orders:
            status_map = {
                'fully_settled': '完全结算',
                'partially_settled': '部分结算',
                'pending': '待结算'
            }
            
            export_data.append({
                '结算单编号': order.order_number,
                '关联项目': order.project.project_name if order.project else '无项目',
                '结算公司': order.dealer.company_name if order.dealer else '无公司',
                '产品数量': len(order.details),
                '总金额(万元)': round(float(order.total_amount or 0.0) / 10000, 2),
                '结算情况': status_map.get(order.settlement_status, order.settlement_status),
                '创建时间': order.created_at.strftime('%Y-%m-%d %H:%M') if order.created_at else '-'
            })
        
        # 创建DataFrame
        df = pd.DataFrame(export_data)
        
        # 创建筛选条件DataFrame
        filter_df = pd.DataFrame(filter_info, columns=['项目', '值'])
        
        # 生成文件名
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'结算单统计-{current_time}.xlsx'
        
        # 创建Excel文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # 先写入筛选条件信息
            filter_df.to_excel(writer, sheet_name='结算单统计', index=False, header=False, startrow=0)
            
            # 计算数据开始行（筛选条件行数 + 2行间距）
            data_start_row = len(filter_info) + 2
            
            # 写入数据表格
            df.to_excel(writer, sheet_name='结算单统计', index=False, startrow=data_start_row)
            
            # 获取工作表并设置格式
            worksheet = writer.sheets['结算单统计']
            
            # 设置筛选条件区域的格式
            from openpyxl.styles import Font, PatternFill, Alignment
            
            # 标题行格式（导出时间、数据总数等）
            title_font = Font(bold=True, size=12)
            filter_font = Font(bold=True, size=10, color='0066CC')
            
            for row in range(1, len(filter_info) + 1):
                cell_a = worksheet.cell(row=row, column=1)
                cell_b = worksheet.cell(row=row, column=2)
                
                # 设置关键信息的格式
                if row <= 2:  # 导出时间和数据总数
                    cell_a.font = title_font
                    cell_b.font = title_font
                elif cell_a.value == '筛选条件':  # 筛选条件标题
                    cell_a.font = filter_font
                elif cell_a.value and cell_a.value not in ['', '筛选条件']:  # 具体筛选项
                    cell_a.font = Font(bold=True, size=9)
            
            # 设置数据表格标题行格式
            header_row = data_start_row + 1
            header_font = Font(bold=True, size=11, color='FFFFFF')
            header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
            
            for col in range(1, len(df.columns) + 1):
                cell = worksheet.cell(row=header_row, column=col)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # 设置列宽
            column_widths = {
                'A': 18,  # 结算单编号
                'B': 25,  # 关联项目
                'C': 20,  # 结算公司
                'D': 12,  # 产品数量
                'E': 15,  # 总金额
                'F': 12,  # 结算情况
                'G': 18,  # 创建时间
            }
            
            for col, width in column_widths.items():
                worksheet.column_dimensions[col].width = width
            
            # 设置数据区域的边框
            from openpyxl.styles import Border, Side
            thin_border = Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            )
            
            # 为数据表格添加边框
            for row in range(header_row, header_row + len(df) + 1):
                for col in range(1, len(df.columns) + 1):
                    worksheet.cell(row=row, column=col).border = thin_border
        
        output.seek(0)
        
        logger.info(f"用户 {current_user.username} 导出结算单列表，共 {len(settlement_orders)} 条记录")
        
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        logger.error(f"导出结算单列表失败：{str(e)}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        flash(f'导出失败：{str(e)}', 'danger')
        return redirect(url_for('inventory.settlement_order_list'))

@inventory.route('/settlement/create', methods=['GET', 'POST'])
@login_required
@permission_required('settlement', 'create')
def create_settlement():
    """创建结算 - 重定向到结算单列表"""
    return redirect(url_for('inventory.settlement_order_list'))

@inventory.route('/settlement/<int:id>')
@login_required
@permission_required('settlement', 'view')
def settlement_detail(id):
    """结算详情"""
    settlement_order = SettlementOrder.query.get_or_404(id)
    return render_template('inventory/settlement_detail.html', settlement_order=settlement_order)

@inventory.route('/inventory_settlement/<int:id>')
@login_required
@permission_required('settlement', 'view')
def inventory_settlement_detail(id):
    """库存结算详情"""
    settlement = Settlement.query.get_or_404(id)
    return render_template('inventory/inventory_settlement_detail.html', settlement=settlement)

@inventory.route('/settlement/<int:id>/execute', methods=['POST'])
@login_required
@permission_required('settlement', 'create')
def execute_settlement(id):
    """执行结算 - 将结算单与库存进行关联并扣减库存"""
    try:
        settlement_order = SettlementOrder.query.get_or_404(id)
        
        # 检查结算单状态
        if settlement_order.status != 'approved':
            return jsonify({'success': False, 'message': '只有已批准的结算单才能执行结算'})
        
        # 检查是否已经执行过结算
        existing_settlement = Settlement.query.filter_by(
            settlement_number=f"INV-{settlement_order.order_number}"
        ).first()
        if existing_settlement:
            return jsonify({'success': False, 'message': '该结算单已经执行过库存结算'})
        
        # 准备结算项目
        settlement_items = []
        for detail in settlement_order.details:
            # 根据产品名称和MN查找对应的产品
            product = None
            if detail.product_mn:
                product = Product.query.filter_by(product_mn=detail.product_mn).first()
            if not product and detail.product_name:
                product = Product.query.filter_by(product_name=detail.product_name).first()
            
            if product:
                settlement_items.append({
                    'product_id': product.id,
                    'quantity': detail.quantity,
                    'notes': f'结算单{settlement_order.order_number}执行'
                })
            else:
                logger.warning(f"未找到产品: {detail.product_name} (MN: {detail.product_mn})")
        
        if not settlement_items:
            return jsonify({'success': False, 'message': '未找到可结算的产品库存'})
        
        # 执行库存结算
        success, message, settlement = process_settlement(
            company_id=settlement_order.distributor_id,
            settlement_items=settlement_items,
            description=f'执行结算单 {settlement_order.order_number}',
            user_id=current_user.id
        )
        
        if success:
            # 更新结算单号以关联库存结算
            settlement.settlement_number = f"INV-{settlement_order.order_number}"
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': '结算执行成功，库存已更新',
                'settlement_id': settlement.id
            })
        else:
            return jsonify({'success': False, 'message': message})
            
    except Exception as e:
        logger.error(f"执行结算失败：{str(e)}")
        return jsonify({'success': False, 'message': f'执行结算失败：{str(e)}'})

@inventory.route('/api/settlement/<int:id>')
@login_required
@permission_required('settlement', 'view')
def get_settlement_info(id):
    """获取结算单详情API"""
    try:
        settlement_order = SettlementOrder.query.get_or_404(id)
        
        return jsonify({
            'success': True,
            'settlement': {
                'order_number': settlement_order.order_number,
                'distributor_name': settlement_order.dealer.company_name if settlement_order.dealer else '无经销商',
                'details_count': len(settlement_order.details),
                'total_amount': settlement_order.formatted_total_amount,
                'status': settlement_order.status
            }
        })
    except Exception as e:
        logger.error(f"获取结算详情失败：{str(e)}")
        return jsonify({'success': False, 'message': f'获取结算详情失败：{str(e)}'})

@inventory.route('/api/company/<int:company_id>/products')
@login_required
# @permission_required('inventory', 'view')  # 临时注释掉权限检查
def get_company_products(company_id):
    """获取公司库存产品API"""
    try:
        # 获取该公司的库存产品
        inventories = Inventory.query.filter_by(company_id=company_id).filter(Inventory.quantity > 0).all()
        
        products = []
        for inventory in inventories:
            products.append({
                'id': inventory.product_id,
                'product_name': inventory.product.product_name,
                'product_model': inventory.product.product_model,
                'quantity': inventory.quantity,
                'unit': inventory.unit
            })
        
        return jsonify({
            'success': True,
            'products': products
        })
    except Exception as e:
        logger.error(f"获取公司库存产品失败：{str(e)}")
        return jsonify({'success': False, 'message': f'获取库存产品失败：{str(e)}'})

@inventory.route('/api/company/<int:company_id>/inventory_details')
@login_required
def get_company_inventory_details(company_id):
    """获取公司库存详情API - 用于结算处理"""
    try:
        # 获取该公司的所有库存产品
        inventories = Inventory.query.filter_by(company_id=company_id).all()
        
        inventory_dict = {}
        for inventory in inventories:
            inventory_dict[inventory.product.product_name] = {
                'product_id': inventory.product_id,
                'product_name': inventory.product.product_name,
                'product_model': inventory.product.model or '',
                'product_mn': inventory.product.product_mn or '',
                'quantity': inventory.quantity,
                'unit': inventory.unit or '件',
                'min_stock': inventory.min_stock,
                'max_stock': inventory.max_stock
            }
        
        return jsonify({
            'success': True,
            'inventory': inventory_dict
        })
    except Exception as e:
        logger.error(f"获取公司库存详情失败：{str(e)}")
        return jsonify({'success': False, 'message': f'获取库存详情失败：{str(e)}'})

@inventory.route('/orders')
@login_required
@permission_required('order', 'view')
def order_list():
    """订单列表 - 使用通用列表组件架构"""
    try:
        # 确保数据库连接正常，如果有失败的事务则回滚
        try:
            db.session.rollback()
        except:
            pass
            
        # 获取搜索和筛选参数
        search = request.args.get('search', '').strip()
        company_id = request.args.get('company_id', '')
        status = request.args.get('status', '')
        inventory_status = request.args.get('inventory_status', '')
        
        # 构建基础查询
        query = PurchaseOrder.query
        
        # 应用筛选条件
        if search:
            query = query.filter(
                db.or_(
                    PurchaseOrder.order_number.contains(search),
                    PurchaseOrder.company.has(Company.company_name.contains(search))
                )
            )
        
        if company_id:
            query = query.filter(PurchaseOrder.company_id == company_id)
        
        if status:
            query = query.filter(PurchaseOrder.status == status)
        
        # 计算统计数据
        all_orders_for_stats = query.all()
        
        # 统计数据
        total_count = len(all_orders_for_stats)
        total_amount = sum(float(order.total_amount or 0) for order in all_orders_for_stats) / 10000  # 转换为万元
        
        # 按入库状态分类统计
        pending_orders = [order for order in all_orders_for_stats if order.inventory_status == 'pending']
        partial_orders = [order for order in all_orders_for_stats if order.inventory_status == 'partially_received']
        completed_orders = [order for order in all_orders_for_stats if order.inventory_status == 'fully_received']
        
        pending_count = len(pending_orders)
        pending_amount = sum(float(order.total_amount or 0) for order in pending_orders) / 10000
        
        partial_count = len(partial_orders)
        partial_amount = sum(float(order.total_amount or 0) for order in partial_orders) / 10000
        
        completed_count = len(completed_orders)
        completed_amount = sum(float(order.total_amount or 0) for order in completed_orders) / 10000
        
        # 获取筛选选项
        company_ids_with_orders = db.session.query(PurchaseOrder.company_id).distinct().all()
        company_ids = [row[0] for row in company_ids_with_orders if row[0]]
        companies = Company.query.filter(
            Company.id.in_(company_ids),
            Company.is_deleted == False
        ).order_by(Company.company_name).all()
        
        # 获取实际存在的订单状态
        existing_statuses = db.session.query(PurchaseOrder.status).distinct().all()
        available_statuses = []
        status_map = {
            'draft': '草稿',
            'pending': '审批中', 
            'approved': '已审批',
            'rejected': '已拒绝',
            'confirmed': '已确认',
            'shipped': '已发货',
            'completed': '已完成',
            'cancelled': '已取消'
        }
        
        for status_row in existing_statuses:
            status_val = status_row[0]
            if status_val and status_val in status_map:
                available_statuses.append({
                    'value': status_val,
                    'label': status_map[status_val]
                })
        
        # 获取实际存在的入库状态
        available_inventory_statuses = []
        inventory_status_map = {
            'pending': '待入库',
            'partially_received': '部分入库',
            'fully_received': '全部入库'
        }
        
        for inv_status in ['pending', 'partially_received', 'fully_received']:
            available_inventory_statuses.append({
                'value': inv_status,
                'label': inventory_status_map[inv_status]
            })
        
        # 构建筛选搜索配置
        filter_config = {
            'action_url': url_for('inventory.order_list'),
            'form_id': 'orderFilterForm',
            'reset_url': url_for('inventory.order_list'),
            'auto_submit': True,
            'ajax_mode': True,
            'ajax_endpoint': url_for('inventory.order_list_ajax'),
            'ajax_target': '#orderTableBody',
            'ajax_columns': 8,
            'dynamic_reset_button': True,
            'search_field_id': 'search',
            
            'search_field': {
                'name': 'search',
                'label': '搜索',
                'placeholder': '订单号或公司名称',
                'value': search,
                'col_width': 3
            },
            
            'filter_fields': [
                {
                    'name': 'company_id',
                    'label': '公司',
                    'all_option_text': '全部公司',
                    'current_value': company_id,
                    'col_width': 2,
                    'options': [
                        {'value': company.id, 'label': company.company_name, 'translate': False} 
                        for company in companies
                    ]
                },
                {
                    'name': 'status',
                    'label': '审批状态',
                    'all_option_text': '全部状态',
                    'current_value': status,
                    'col_width': 2,
                    'options': [
                        {'value': s['value'], 'label': s['label'], 'translate': True} 
                        for s in available_statuses
                    ]
                },
                {
                    'name': 'inventory_status',
                    'label': '入库状态',
                    'all_option_text': '全部状态',
                    'current_value': inventory_status,
                    'col_width': 2,
                    'options': [
                        {'value': s['value'], 'label': s['label'], 'translate': True} 
                        for s in available_inventory_statuses
                    ]
                }
            ],
            
            'search_button_text': '搜索',
            'reset_button_text': '重置'
        }
        
        # 构建通用列表配置
        list_config = {
            'module_name': 'order',
            'title': '订单管理',  # 设置为与页面标题一致
            'ajax_mode': True,
            
            # 无限滚动配置
            'infinite_scroll': {
                'enabled': True,
                'page_size': 50,
                'scroll_threshold': 100,
                'container_selector': '.table-responsive',
                'scroll_mode': 'container'  # 明确设置为容器滚动模式
            },
            
            # 统计卡片配置
            'stats': {
                'cards': [
                    {
                        'id': 'total',
                        'title': '全部订单',
                        'icon': 'fas fa-list-alt',
                        'value': total_count,
                        'amount': total_amount,
                        'unit': '单',
                        'amount_unit': '万元',
                        'color': 'primary',
                        'data_key': 'total'
                    },
                    {
                        'id': 'pending',
                        'title': '待入库',
                        'icon': 'fas fa-clock',
                        'value': pending_count,
                        'amount': pending_amount,
                        'unit': '单',
                        'amount_unit': '万元',
                        'color': 'warning',
                        'data_key': 'pending'
                    },
                    {
                        'id': 'partial',
                        'title': '部分入库',
                        'icon': 'fas fa-hourglass-half',
                        'value': partial_count,
                        'amount': partial_amount,
                        'unit': '单',
                        'amount_unit': '万元',
                        'color': 'info',
                        'data_key': 'partial'
                    },
                    {
                        'id': 'completed',
                        'title': '已入库',
                        'icon': 'fas fa-check-circle',
                        'value': completed_count,
                        'amount': completed_amount,
                        'unit': '单',
                        'amount_unit': '万元',
                        'color': 'success',
                        'data_key': 'completed'
                    }
                ]
            },
            
            # 筛选配置
            'filter': filter_config,
            
            # 表格配置
            'table': {
                'ajax_target': 'orderTableBody',
                'title': '订单列表',  # 恢复表格标题
                'icon': 'fas fa-table',
                'show_header': True,
                'fixed_height_scroll': True,     # 启用固定高度滚动
                'enhanced_striping': True,       # 启用增强斑马纹效果
                'columns': [
                    {
                        'key': 'order_number',
                        'label': '订单号',
                        'type': 'link',
                        'url_template': '/inventory/orders/{id}',
                        'width': '140px'
                    },
                    {
                        'key': 'company.company_name',
                        'label': '公司名称',
                        'type': 'text',
                        'width': '200px'
                    },
                    {
                        'key': 'total_amount',
                        'label': '总金额',
                        'type': 'number',
                        'format': 'wan',
                        'align': 'end',
                        'width': '120px'
                    },
                    {
                        'key': 'status',
                        'label': '审批状态',
                        'type': 'badge',
                        'render': 'render_order_status_badge',
                        'width': '100px'
                    },
                    {
                        'key': 'inventory_status',
                        'label': '入库状态',
                        'type': 'badge',
                        'render': 'render_inventory_status_badge',
                        'width': '100px'
                    },
                    {
                        'key': 'expected_date',
                        'label': '预期日期',
                        'type': 'date',
                        'format': '%Y-%m-%d',
                        'width': '120px'
                    },
                    {
                        'key': 'created_at',
                        'label': '创建时间',
                        'type': 'date',
                        'format': '%Y-%m-%d %H:%M',
                        'width': '150px'
                    },
                    {
                        'key': 'created_by',
                        'label': '创建人',
                        'type': 'badge',
                        'render': 'render_owner',
                        'width': '100px'
                    }
                ]
            }
        }
        
        return render_template('inventory/order_list.html', list_config=list_config)
        
    except Exception as e:
        logger.error(f"获取订单列表失败：{str(e)}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        flash(f'加载订单列表失败：{str(e)}', 'danger')
        
        # 错误时的默认list_config
        error_list_config = {
            'module_name': 'order',
            'title': '订单管理',  # 设置为与页面标题一致
            'ajax_mode': True,
            'stats': {'cards': []},
            'filter': {
                'action_url': url_for('inventory.order_list'),
                'form_id': 'orderFilterForm',
                'reset_url': url_for('inventory.order_list'),
                'search_field': {
                    'name': 'search',
                    'label': '搜索',
                    'placeholder': '订单号或公司名称',
                    'value': '',
                    'col_width': 3
                },
                'filter_fields': [],
                'search_button_text': '搜索',
                'reset_button_text': '重置'
            },
            'table': {
                'ajax_target': 'orderTableBody',
                'columns': []
            }
        }
        
        return render_template('inventory/order_list.html', list_config=error_list_config)

@inventory.route('/api/orders/filter', methods=['GET'])
@login_required
@permission_required('order', 'view')
def order_list_ajax():
    """订单列表AJAX筛选API"""
    # 获取搜索和筛选参数
    search = request.args.get('search', '')
    company_id = request.args.get('company_id', '')
    status = request.args.get('status', '')
    inventory_status = request.args.get('inventory_status', '')
    
    # 分页参数
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    # 限制每次加载数量的范围
    if limit not in [10, 20, 30, 50]:
        limit = 20
    
    # 构建查询
    query = PurchaseOrder.query
    
    # 搜索条件
    if search:
        query = query.filter(
            db.or_(
                PurchaseOrder.order_number.contains(search),
                PurchaseOrder.company.has(Company.company_name.contains(search))
            )
        )
    
    # 筛选条件
    if company_id:
        try:
            company_id = int(company_id)
            query = query.filter(PurchaseOrder.company_id == company_id)
        except (ValueError, TypeError):
            pass
    
    if status:
        query = query.filter(PurchaseOrder.status == status)
    
    # 处理入库状态筛选
    if inventory_status:
        # 需要先获取所有订单再筛选
        all_orders = query.order_by(PurchaseOrder.created_at.desc()).all()
        filtered_orders = [order for order in all_orders if order.inventory_status == inventory_status]
        
        # 手动分页
        total_count = len(filtered_orders)
        orders = filtered_orders[offset:offset + limit]
        has_more = (offset + limit) < total_count
    else:
        # 普通查询可以使用数据库分页
        total_count = query.count()
        orders = query.order_by(PurchaseOrder.created_at.desc()).offset(offset).limit(limit).all()
        has_more = (offset + limit) < total_count
    
    # 计算统计数据（用于更新统计卡片）
    all_orders_for_stats = query.all()
    
    # 安全的金额计算函数
    def safe_amount_sum(orders):
        total = 0
        for order in orders:
            amount = order.total_amount
            if amount is not None:
                try:
                    total += float(amount)
                except (ValueError, TypeError):
                    pass  # 忽略无效的金额值
        return round(total / 10000, 2)  # 转换为万元并保留2位小数
    
    # 分类统计
    total_stats_count = len(all_orders_for_stats)
    total_stats_amount = safe_amount_sum(all_orders_for_stats)
    
    pending_orders = [o for o in all_orders_for_stats if o.inventory_status == 'pending']
    pending_stats_count = len(pending_orders)
    pending_stats_amount = safe_amount_sum(pending_orders)
    
    partial_orders = [o for o in all_orders_for_stats if o.inventory_status == 'partially_received']
    partial_stats_count = len(partial_orders)
    partial_stats_amount = safe_amount_sum(partial_orders)
    
    completed_orders = [o for o in all_orders_for_stats if o.inventory_status == 'fully_received']
    completed_stats_count = len(completed_orders)
    completed_stats_amount = safe_amount_sum(completed_orders)
    
    # 构建统计数据
    statistics = {
        'total_count': int(total_stats_count),
        'total_amount': float(total_stats_amount),
        'pending_count': int(pending_stats_count),
        'pending_amount': float(pending_stats_amount),
        'partial_count': int(partial_stats_count),
        'partial_amount': float(partial_stats_amount),
        'completed_count': int(completed_stats_count),
        'completed_amount': float(completed_stats_amount)
    }
    
    # 渲染HTML片段
    html = render_template('inventory/order_rows.html', 
                          orders=orders)
    
    return jsonify({
        'success': True,
        'html': html,
        'has_more': has_more,
        'total_count': total_count,
        'loaded_count': offset + len(orders),
        'statistics': statistics  # 用于更新统计卡片
    })

@inventory.route('/api/settlement_orders/filter', methods=['GET'])
@login_required
@permission_required('settlement', 'view')
def settlement_order_list_ajax():
    """结算单列表AJAX筛选API"""
    try:
        # 确保数据库连接正常，如果有失败的事务则回滚
        try:
            db.session.rollback()
        except:
            pass
    except:
        pass
    
    # 获取搜索和筛选参数
    search = request.args.get('search', '')
    settlement_company = request.args.get('settlement_company', '')
    settlement_status = request.args.get('settlement_status', '')
    
    # 分页参数
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    # 限制每次加载数量的范围
    if limit not in [10, 20, 30, 50]:
        limit = 20
    
    # 构建查询：只获取来自已审批批价单的结算单
    from app.models.pricing_order import PricingOrder
    from app.models.project import Project
    
    query = SettlementOrder.query.join(
        PricingOrder, SettlementOrder.pricing_order_id == PricingOrder.id
    ).join(
        Project, SettlementOrder.project_id == Project.id
    ).filter(
        PricingOrder.status == 'approved'
    )
    
    # 搜索条件
    if search:
        query = query.filter(
            db.or_(
                SettlementOrder.order_number.ilike(f'%{search}%'),
                Project.project_name.ilike(f'%{search}%')
            )
        )
    
    # 筛选条件
    if settlement_company:
        try:
            company_id = int(settlement_company)
            query = query.filter(SettlementOrder.dealer_id == company_id)
        except (ValueError, TypeError):
            pass
    
    if settlement_status:
        query = query.filter(SettlementOrder.settlement_status == settlement_status)
    
    # 执行查询（按创建时间倒序）
    total_count = query.count()
    settlement_orders = query.order_by(SettlementOrder.created_at.desc()).offset(offset).limit(limit).all()
    has_more = (offset + limit) < total_count
    
    # 计算统计数据（用于更新统计卡片）
    all_orders_for_stats = query.all()
    
    # 分类统计
    total_stats_count = len(all_orders_for_stats)
    total_stats_amount = sum(float(order.total_amount or 0) for order in all_orders_for_stats) / 10000  # 转换为万元
    
    fully_settled_orders = [o for o in all_orders_for_stats if o.settlement_status == 'fully_settled']
    fully_settled_stats_count = len(fully_settled_orders)
    fully_settled_stats_amount = sum(float(order.total_amount or 0) for order in fully_settled_orders) / 10000
    
    partially_settled_orders = [o for o in all_orders_for_stats if o.settlement_status == 'partially_settled']
    partially_settled_stats_count = len(partially_settled_orders)
    partially_settled_stats_amount = sum(float(order.total_amount or 0) for order in partially_settled_orders) / 10000
    
    pending_orders = [o for o in all_orders_for_stats if o.settlement_status == 'pending']
    pending_stats_count = len(pending_orders)
    pending_stats_amount = sum(float(order.total_amount or 0) for order in pending_orders) / 10000
    
    # 构建统计数据
    statistics = {
        'total_count': total_stats_count,
        'total_amount': total_stats_amount,
        'fully_settled_count': fully_settled_stats_count,
        'fully_settled_amount': fully_settled_stats_amount,
        'partially_settled_count': partially_settled_stats_count,
        'partially_settled_amount': partially_settled_stats_amount,
        'pending_count': pending_stats_count,
        'pending_amount': pending_stats_amount
    }
    
    # 渲染HTML片段
    html = render_template('inventory/settlement_order_rows.html', 
                          settlement_orders=settlement_orders)
    
    return jsonify({
        'success': True,
        'html': html,
        'has_more': has_more,
        'total_count': total_count,
        'loaded_count': len(settlement_orders),
        'statistics': statistics  # 用于更新统计卡片
    })

@inventory.route('/api/settlement/filter', methods=['GET'])
@login_required
def settlement_list_ajax():
    """结算明细列表AJAX筛选API"""
    # 获取查询参数
    search = request.args.get('search', '').strip()
    company_filter = request.args.get('company_filter')
    status_filter = request.args.get('status_filter')
    settlement_company_filter = request.args.get('settlement_company_filter')
    
    # 分页参数
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    # 限制每次加载数量的范围
    if limit not in [10, 20, 30, 50]:
        limit = 20
    
    # 构建基础查询 - 只获取已审批批价单的结算单明细
    from app.models.pricing_order import SettlementOrderDetail, SettlementOrder, PricingOrder
    query = db.session.query(SettlementOrderDetail).join(SettlementOrder).join(PricingOrder)
    
    # 关键过滤：只显示已审批批价单的结算明细
    query = query.filter(PricingOrder.status == 'approved')
    
    # 搜索条件
    if search:
        search_filter = db.or_(
            SettlementOrder.order_number.contains(search),
            SettlementOrderDetail.product_name.contains(search),
            SettlementOrderDetail.product_mn.contains(search)
        )
        query = query.filter(search_filter)
    
    # 结算单公司过滤（分销商）
    if company_filter:
        query = query.filter(SettlementOrder.distributor_id == company_filter)
    
    # 结算目标公司过滤
    if settlement_company_filter:
        query = query.filter(SettlementOrderDetail.settlement_company_id == settlement_company_filter)
    
    # 结算状态过滤
    if status_filter:
        if status_filter == 'completed':
            query = query.filter(SettlementOrderDetail.settlement_status == 'settled')
        elif status_filter == 'pending':
            query = query.filter(SettlementOrderDetail.settlement_status == 'pending')
    
    # 排序
    query = query.order_by(SettlementOrder.created_at.desc(), SettlementOrderDetail.id.desc())
    
    # 执行查询（按创建时间倒序）
    total_count = query.count()
    settlement_details_raw = query.offset(offset).limit(limit).all()
    has_more = (offset + limit) < total_count
    
    # 处理结算明细数据用于显示
    settlement_details = []
    
    for detail in settlement_details_raw:
        # 获取产品信息（按MN号精确匹配）
        product = None
        if detail.product_mn:
            product = Product.query.filter_by(product_mn=detail.product_mn).first()
        
        # 构建明细信息
        detail_info = {
            'id': detail.id,
            'settlement_order': detail.settlement_order,
            'product': product,
            'product_name': detail.product_name,
            'product_model': detail.product_model,
            'product_mn': detail.product_mn,
            'brand': detail.brand,
            'quantity': detail.quantity,
            'unit': detail.unit,
            'unit_price': detail.unit_price,
            'total_price': detail.total_price,
            'settlement_status': detail.settlement_status,
            'settlement_company': detail.settlement_company,
            'settlement_date': detail.settlement_date,
            'settlement_notes': detail.settlement_notes,
            'is_settled': detail.settlement_status == 'settled'  # 保持兼容性
        }
        
        settlement_details.append(detail_info)
    
    # 计算统计数据（用于更新统计卡片）
    all_details_for_stats = query.all()
    
    # 分类统计
    total_stats_count = len(all_details_for_stats)
    total_stats_amount = sum(float(detail.total_price or 0) for detail in all_details_for_stats) / 10000  # 转换为万元
    
    settled_details = [d for d in all_details_for_stats if d.settlement_status == 'settled']
    settled_stats_count = len(settled_details)
    settled_stats_amount = sum(float(detail.total_price or 0) for detail in settled_details) / 10000
    
    pending_details = [d for d in all_details_for_stats if d.settlement_status == 'pending']
    pending_stats_count = len(pending_details)
    pending_stats_amount = sum(float(detail.total_price or 0) for detail in pending_details) / 10000
    
    # 本月结算统计
    from datetime import datetime
    current_month = datetime.now().strftime('%Y-%m')
    thismonth_details = [d for d in settled_details if d.settlement_date and d.settlement_date.strftime('%Y-%m') == current_month]
    thismonth_stats_count = len(thismonth_details)
    thismonth_stats_amount = sum(float(detail.total_price or 0) for detail in thismonth_details) / 10000
    
    # 构建统计数据
    statistics = {
        'total_count': total_stats_count,
        'total_amount': total_stats_amount,
        'settled_count': settled_stats_count,
        'settled_amount': settled_stats_amount,
        'pending_count': pending_stats_count,
        'pending_amount': pending_stats_amount,
        'thismonth_count': thismonth_stats_count,
        'thismonth_amount': thismonth_stats_amount
    }
    
    # 渲染HTML片段
    html = render_template('inventory/settlement_rows.html', 
                          settlement_details=settlement_details)
    
    return jsonify({
        'success': True,
        'html': html,
        'has_more': has_more,
        'total_count': total_count,
        'loaded_count': len(settlement_details),
        'statistics': statistics  # 用于更新统计卡片
    })

@inventory.route('/orders/create', methods=['GET', 'POST'])
@login_required
@permission_required('order', 'create')
def create_order():
    """创建订单"""
    if request.method == 'POST':
        try:
            # 获取基本信息
            company_id = request.form.get('company_id')
            expected_date = request.form.get('expected_date')
            description = request.form.get('description', '')
            
            if not company_id:
                flash('请选择公司', 'danger')
                return redirect(url_for('inventory.create_order'))
            
            # 处理日期
            expected_date_obj = None
            if expected_date:
                expected_date_obj = datetime.strptime(expected_date, '%Y-%m-%d')
            
            # 生成订单号
            order_number = generate_order_number()
            
            # 创建订单（默认为采购订单）
            order = PurchaseOrder(
                order_number=order_number,
                company_id=company_id,
                order_type='purchase',  # 默认为采购订单
                expected_date=expected_date_obj,
                description=description,
                created_by_id=current_user.id
            )
            db.session.add(order)
            db.session.flush()
            
            # 获取订单明细 - 处理新的表单格式
            order_details = []
            total_quantity = 0
            total_amount = 0
            
            # 获取数组形式的表单数据
            product_ids = request.form.getlist('product_id[]')
            quantities = request.form.getlist('quantity[]')
            unit_prices = request.form.getlist('unit_price[]')
            discounts = request.form.getlist('discount[]')
            notes_list = request.form.getlist('notes[]')
            
            logger.info(f"接收到的表单数据: product_ids={product_ids}, quantities={quantities}, unit_prices={unit_prices}, discounts={discounts}")
            
            for i, product_id in enumerate(product_ids):
                if product_id and i < len(quantities):
                    try:
                        quantity = int(quantities[i]) if quantities[i] else 0
                        unit_price = float(unit_prices[i]) if i < len(unit_prices) and unit_prices[i] else 0
                        discount_rate = float(discounts[i]) if i < len(discounts) and discounts[i] else 100
                        notes = notes_list[i] if i < len(notes_list) else ''
                        
                        logger.info(f"处理第{i+1}行: product_id={product_id}, quantity={quantity}, unit_price={unit_price}, discount_rate={discount_rate}")
                        
                        if quantity > 0 and unit_price >= 0:
                            product = Product.query.get(product_id)
                            if product:
                                # 折扣率转换为小数（100% = 1.0）
                                discount_decimal = discount_rate / 100.0
                                
                                # 计算总价
                                calculated_total = unit_price * quantity * discount_decimal
                                
                                detail = PurchaseOrderDetail(
                                    order_id=order.id,
                                    product_id=product_id,
                                    product_name=product.product_name,
                                    product_model=product.model or '',
                                    product_desc=product.specification or '',
                                    brand=product.brand or '',
                                    quantity=quantity,
                                    unit=product.unit or '',
                                    unit_price=unit_price,
                                    discount=discount_decimal,
                                    total_price=calculated_total,
                                    notes=notes
                                )
                                order_details.append(detail)
                                total_quantity += quantity
                                total_amount += calculated_total
                                
                                logger.info(f"成功添加订单明细: {product.product_name}, 数量={quantity}, 单价={unit_price}, 小计={calculated_total}")
                            else:
                                logger.warning(f"未找到产品ID: {product_id}")
                        else:
                            logger.warning(f"跳过无效行: quantity={quantity}, unit_price={unit_price}")
                    except (ValueError, TypeError) as e:
                        logger.error(f"处理订单明细时出错：{str(e)}")
                        continue
            
            if not order_details:
                flash('请至少添加一个有效的产品', 'danger')
                return redirect(url_for('inventory.create_order'))
            
            # 添加订单明细
            for detail in order_details:
                db.session.add(detail)
            
            # 更新订单总计
            order.total_quantity = total_quantity
            order.total_amount = total_amount
            
            db.session.commit()
            
            flash(f'订单创建成功！订单号：{order_number}', 'success')
            return redirect(url_for('inventory.order_detail', id=order.id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"创建订单失败：{str(e)}")
            flash(f'操作失败：{str(e)}', 'danger')
    
    # 获取公司列表 - 只显示经销商类型且未删除的公司
    companies = Company.query.filter(
        Company.company_type == 'dealer',
        Company.is_deleted != True
    ).order_by(Company.company_name).all()
    
    return render_template('inventory/create_order.html', companies=companies)

@inventory.route('/orders/<int:id>')
@login_required
@permission_required_with_approval_context('order', 'view')
def order_detail(id):
    """订单详情"""
    # 使用数据访问控制获取订单
    from app.utils.access_control import get_viewable_data
    viewable_orders = get_viewable_data(PurchaseOrder, current_user)
    order = viewable_orders.filter(PurchaseOrder.id == id).first_or_404()
    
    # 导入审批相关函数
    from app.helpers.approval_helpers import get_object_approval_instance, get_available_templates
    
    # 获取审批实例
    approval_instance = get_object_approval_instance('purchase_order', order.id)
    
    return render_template('inventory/order_detail.html', 
                         order=order,
                         approval_instance=approval_instance,
                         get_object_approval_instance=get_object_approval_instance,
                         get_available_templates=get_available_templates)

@inventory.route('/orders/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('order', 'edit')
def edit_order(id):
    """编辑订单"""
    # 使用数据访问控制获取订单
    from app.utils.access_control import get_viewable_data
    viewable_orders = get_viewable_data(PurchaseOrder, current_user)
    order = viewable_orders.filter(PurchaseOrder.id == id).first_or_404()
    
    # 只有草稿状态的订单才能编辑
    if order.status != 'draft':
        flash('只有草稿状态的订单才能编辑', 'warning')
        return redirect(url_for('inventory.order_detail', id=id))
    
    if request.method == 'POST':
        try:
            # 更新订单基本信息
            order.company_id = request.form.get('company_id')
            order.order_date = datetime.strptime(request.form.get('order_date'), '%Y-%m-%d').date()
            
            expected_date_str = request.form.get('expected_date')
            if expected_date_str:
                order.expected_date = datetime.strptime(expected_date_str, '%Y-%m-%d').date()
            else:
                order.expected_date = None
                
            order.payment_terms = request.form.get('payment_terms', '').strip()
            order.delivery_address = request.form.get('delivery_address', '').strip()
            order.description = request.form.get('description', '').strip()
            order.currency = request.form.get('currency', 'CNY')
            
            # 删除原有的订单明细
            PurchaseOrderDetail.query.filter_by(order_id=order.id).delete()
            
            # 重新处理订单明细
            order_details = []
            total_quantity = 0
            total_amount = 0
            
            # 获取产品明细数据
            product_ids = request.form.getlist('product_id[]')
            quantities = request.form.getlist('quantity[]')
            unit_prices = request.form.getlist('unit_price[]')
            discounts = request.form.getlist('discount[]')
            notes_list = request.form.getlist('notes[]')
            
            for i in range(len(product_ids)):
                try:
                    product_id = int(product_ids[i]) if product_ids[i] else None
                    quantity = int(quantities[i]) if quantities[i] else 0
                    unit_price = float(unit_prices[i]) if unit_prices[i] else 0
                    discount = float(discounts[i]) if discounts[i] else 100
                    notes = notes_list[i] if i < len(notes_list) else ''
                    
                    if product_id and quantity > 0 and unit_price > 0:
                        product = Product.query.get(product_id)
                        if product:
                            discount_decimal = discount / 100
                            calculated_total = quantity * unit_price * discount_decimal
                            
                            detail = PurchaseOrderDetail(
                                order_id=order.id,
                                product_id=product_id,
                                product_name=product.product_name,
                                product_model=product.product_model or '',
                                product_desc=product.specification or '',
                                brand=product.brand or '',
                                quantity=quantity,
                                unit=product.unit or '',
                                unit_price=unit_price,
                                discount=discount_decimal,
                                total_price=calculated_total,
                                notes=notes
                            )
                            order_details.append(detail)
                            total_quantity += quantity
                            total_amount += calculated_total
                except (ValueError, TypeError):
                    continue
            
            if not order_details:
                flash('请至少添加一个有效的产品', 'danger')
                return redirect(url_for('inventory.edit_order', id=id))
            
            # 添加订单明细
            for detail in order_details:
                db.session.add(detail)
            
            # 更新订单总计
            order.total_quantity = total_quantity
            order.total_amount = total_amount
            
            db.session.commit()
            
            flash('订单更新成功', 'success')
            return redirect(url_for('inventory.order_detail', id=id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'更新订单失败：{str(e)}', 'danger')
    
    # 获取公司列表
    companies = Company.query.filter(
        Company.is_deleted == False
    ).order_by(Company.company_name).all()
    
    return render_template('inventory/edit_order.html', 
                         order=order, 
                         companies=companies)



@inventory.route('/orders/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('order', 'delete')
def delete_order(id):
    """删除单个订单"""
    try:
        # 使用数据访问控制获取订单
        from app.utils.access_control import get_viewable_data
        viewable_orders = get_viewable_data(PurchaseOrder, current_user)
        order = viewable_orders.filter(PurchaseOrder.id == id).first_or_404()
        order_number = order.order_number
        
        # 删除订单明细
        PurchaseOrderDetail.query.filter_by(order_id=id).delete()
        
        # 删除订单
        db.session.delete(order)
        db.session.commit()
        
        logger.info(f"订单删除成功：{order_number}")
        return jsonify({'success': True, 'message': f'订单 {order_number} 删除成功'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除订单失败：{str(e)}")
        return jsonify({'success': False, 'message': f'删除失败：{str(e)}'})

@inventory.route('/orders/receive', methods=['POST'])
@login_required
@permission_required('order', 'edit')
def receive_order_item():
    """订单明细入库操作"""
    try:
        # 验证请求格式
        if not request.is_json:
            return jsonify({'success': False, 'message': '请求必须是JSON格式'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据为空'}), 400
        
        # 参数验证和类型转换
        try:
            detail_id = int(data.get('detail_id', 0))
            quantity = float(data.get('quantity', 0))
        except (ValueError, TypeError) as e:
            logger.error(f"参数类型转换失败: {e}, 原始数据: {data}")
            return jsonify({'success': False, 'message': f'参数格式错误: {str(e)}'}), 400
        
        if not detail_id or detail_id <= 0:
            return jsonify({'success': False, 'message': '订单明细ID无效'}), 400
            
        if quantity <= 0:
            return jsonify({'success': False, 'message': '入库数量必须大于0'}), 400
        
        # 获取订单明细
        detail = PurchaseOrderDetail.query.get(detail_id)
        if not detail:
            return jsonify({'success': False, 'message': '订单明细不存在'}), 404
        
        # 检查用户是否有权限操作此订单
        from app.utils.access_control import get_viewable_data
        viewable_orders = get_viewable_data(PurchaseOrder, current_user)
        if not viewable_orders.filter(PurchaseOrder.id == detail.order_id).first():
            return jsonify({'success': False, 'message': '无权限操作此订单'}), 403
        
        # 检查订单状态是否允许入库
        if detail.order.status not in ['approved', 'confirmed']:
            return jsonify({'success': False, 'message': f'订单状态为"{detail.order.status}"，不允许入库操作'}), 400
        
        # 检查入库数量
        remaining_qty = detail.remaining_quantity
        if quantity > remaining_qty:
            return jsonify({'success': False, 'message': f'入库数量不能超过待入库数量 {remaining_qty}'}), 400
        
        # 更新已收货数量
        detail.received_quantity += quantity
        
        # 获取或创建库存记录
        inventory = Inventory.query.filter_by(
            company_id=detail.order.company_id,
            product_id=detail.product_id
        ).first()
        
        if not inventory:
            # 创建新的库存记录
            inventory = Inventory(
                company_id=detail.order.company_id,
                product_id=detail.product_id,
                quantity=quantity,
                unit=detail.unit,
                created_by_id=current_user.id
            )
            db.session.add(inventory)
            # 刷新会话以获取新创建记录的ID
            db.session.flush()
        else:
            # 更新现有库存
            inventory.quantity += quantity
            inventory.updated_at = func.now()
        
        # 创建库存变动记录
        transaction = InventoryTransaction(
            inventory_id=inventory.id,  # 移除了条件判断，因为flush()后已有ID
            transaction_type='in',
            quantity=quantity,
            quantity_before=inventory.quantity - quantity,
            quantity_after=inventory.quantity,
            reference_type='order',
            reference_id=detail.order_id,
            description=f'订单入库：{detail.order.order_number} - {detail.product_name}',
            created_by_id=current_user.id
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        logger.info(f"用户 {current_user.username} 对订单 {detail.order.order_number} 的产品 {detail.product_name} 入库 {quantity} 件")
        
        return jsonify({
            'success': True, 
            'message': f'成功入库 {quantity} 件',
            'remaining_quantity': detail.remaining_quantity,
            'received_quantity': detail.received_quantity
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"订单入库失败：{str(e)}")
        return jsonify({'success': False, 'message': f'入库失败：{str(e)}'})

@inventory.route('/orders/<int:order_id>/receive_all', methods=['POST'])
@login_required
@permission_required('order', 'edit')
def receive_all_order_items(order_id):
    """批量入库订单所有待入库产品"""
    try:
        logger.info(f"开始批量入库订单 {order_id}")
        
        # 验证请求格式
        if not request.is_json:
            logger.error(f"批量入库请求格式错误，不是JSON格式")
            return jsonify({'success': False, 'message': '请求必须是JSON格式'}), 400
        
        # 获取订单
        order = PurchaseOrder.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'message': '订单不存在'}), 404
        
        # 检查用户是否有权限操作此订单
        from app.utils.access_control import get_viewable_data
        viewable_orders = get_viewable_data(PurchaseOrder, current_user)
        if not viewable_orders.filter(PurchaseOrder.id == order_id).first():
            return jsonify({'success': False, 'message': '无权限操作此订单'}), 403
        
        # 检查订单状态是否允许入库
        if order.status not in ['approved', 'confirmed']:
            return jsonify({'success': False, 'message': f'订单状态为"{order.status}"，不允许入库操作'}), 400
        
        # 获取所有待入库的明细
        pending_details = [detail for detail in order.details if detail.remaining_quantity > 0]
        
        if not pending_details:
            return jsonify({'success': False, 'message': '没有待入库的产品'}), 400
        
        success_count = 0
        
        for detail in pending_details:
            quantity = detail.remaining_quantity
            
            # 更新已收货数量
            detail.received_quantity += quantity
            
            # 获取或创建库存记录
            inventory = Inventory.query.filter_by(
                company_id=order.company_id,
                product_id=detail.product_id
            ).first()
            
            if not inventory:
                # 创建新的库存记录
                inventory = Inventory(
                    company_id=order.company_id,
                    product_id=detail.product_id,
                    quantity=quantity,
                    unit=detail.unit,
                    created_by_id=current_user.id
                )
                db.session.add(inventory)
                # 刷新会话以获取新创建记录的ID
                db.session.flush()
            else:
                # 更新现有库存
                inventory.quantity += quantity
                inventory.updated_at = func.now()
            
            # 创建库存变动记录
            transaction = InventoryTransaction(
                inventory_id=inventory.id,  # 移除了条件判断，因为flush()后已有ID
                transaction_type='in',
                quantity=quantity,
                quantity_before=inventory.quantity - quantity,
                quantity_after=inventory.quantity,
                reference_type='order',
                reference_id=order_id,
                description=f'批量入库：{order.order_number} - {detail.product_name}',
                created_by_id=current_user.id
            )
            
            db.session.add(transaction)
            success_count += 1
        
        db.session.commit()
        
        logger.info(f"用户 {current_user.username} 批量入库订单 {order.order_number}，共 {success_count} 个产品")
        
        return jsonify({
            'success': True, 
            'message': f'成功批量入库 {success_count} 个产品'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"批量入库失败：{str(e)}")
        return jsonify({'success': False, 'message': f'批量入库失败：{str(e)}'})

@inventory.route('/orders/<int:order_id>/export/pdf')
@login_required
@permission_required('order', 'view')
def export_order_pdf(order_id):
    """导出订单PDF"""
    try:
        # 获取订单
        from app.utils.access_control import get_viewable_data
        viewable_orders = get_viewable_data(PurchaseOrder, current_user)
        order = viewable_orders.filter(PurchaseOrder.id == order_id).first()
        
        if not order:
            flash('订单不存在或无权访问', 'error')
            return redirect(url_for('inventory.order_list'))
        
        # 生成PDF
        from app.utils.pdf_generator import generate_order_pdf
        pdf_buffer = generate_order_pdf(order)
        
        # 生成文件名：订单编号-日期时间 (YYMMDD HHMM)
        filename = f"{order.order_number}-{datetime.now().strftime('%y%m%d %H%M')}.pdf"
        
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"导出订单PDF失败：{str(e)}")
        flash(f'导出失败：{str(e)}', 'error')
        return redirect(url_for('inventory.order_detail', id=order_id))

@inventory.route('/orders/export/list')
@login_required
@permission_required('order', 'view')
def export_orders_list():
    """导出订单列表Excel"""
    try:
        # 使用数据访问控制获取订单列表
        from app.utils.access_control import get_viewable_data
        viewable_orders = get_viewable_data(PurchaseOrder, current_user)
        orders = viewable_orders.order_by(PurchaseOrder.created_at.desc()).all()
        
        # 创建Excel文件
        import pandas as pd
        from io import BytesIO
        
        # 准备订单数据
        orders_data = []
        for order in orders:
            orders_data.append({
                '订单编号': order.order_number,
                '采购商': order.company.company_name if order.company else '',
                '订单日期': order.order_date.strftime('%Y-%m-%d') if order.order_date else '',
                '预期日期': order.expected_date.strftime('%Y-%m-%d') if order.expected_date else '',
                '订单状态': get_status_text_for_export(order.status),
                '入库状态': get_inventory_status_text(order.inventory_status),
                '总数量': order.total_quantity or 0,
                '总金额': f'{order.total_amount:.2f}' if order.total_amount else '0.00',
                '创建人': order.created_by.real_name or order.created_by.username if order.created_by else '',
                '创建时间': order.created_at.strftime('%Y-%m-%d %H:%M') if order.created_at else '',
            })
        
        # 创建DataFrame
        df = pd.DataFrame(orders_data)
        
        # 生成Excel文件
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='订单列表', index=False)
        
        buffer.seek(0)
        
        # 生成文件名
        filename = f"订单列表-{datetime.now().strftime('%y%m%d %H%M')}.xlsx"
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        logger.error(f"导出订单列表失败：{str(e)}")
        flash(f'导出失败：{str(e)}', 'error')
        return redirect(url_for('inventory.order_list'))

def get_status_text_for_export(status):
    """获取状态的中文显示文本（用于导出）"""
    status_map = {
        'draft': '草稿',
        'pending': '审批中',
        'approved': '已审批',
        'confirmed': '已确认',
        'rejected': '已拒绝',
        'shipped': '已发货',
        'completed': '已完成',
        'cancelled': '已取消'
    }
    return status_map.get(status, status)

def get_inventory_status_text(inventory_status):
    """获取入库状态的中文显示文本"""
    if inventory_status is None:
        return '-'
    status_map = {
        'pending': '待入库',
        'partially_received': '部分入库',
        'fully_received': '全部入库'
    }
    return status_map.get(inventory_status, '未知')

@inventory.route('/api/company/<int:company_id>/product/<int:product_id>/stock')
@login_required
def get_product_stock(company_id, product_id):
    """获取指定公司的指定产品库存"""
    try:
        inventory = Inventory.query.filter_by(
            company_id=company_id,
            product_id=product_id
        ).first()
        
        stock = inventory.quantity if inventory else 0
        
        return jsonify({
            'success': True,
            'stock': stock
        })
        
    except Exception as e:
        logger.error(f"获取产品库存失败：{str(e)}")
        return jsonify({'success': False, 'message': f'获取库存失败：{str(e)}'})

@inventory.route('/orders/batch_delete', methods=['POST'])
@login_required
@permission_required('order', 'delete')
def batch_delete_orders():
    """批量删除订单"""
    try:
        data = request.get_json()
        order_ids = data.get('order_ids', [])
        
        if not order_ids:
            return jsonify({'success': False, 'message': '未选择要删除的订单'})
        
        # 使用数据访问控制获取要删除的订单
        from app.utils.access_control import get_viewable_data
        viewable_orders = get_viewable_data(PurchaseOrder, current_user)
        orders = viewable_orders.filter(PurchaseOrder.id.in_(order_ids)).all()
        order_numbers = [order.order_number for order in orders]
        
        # 删除订单明细
        PurchaseOrderDetail.query.filter(PurchaseOrderDetail.order_id.in_(order_ids)).delete(synchronize_session=False)
        
        # 删除订单
        PurchaseOrder.query.filter(PurchaseOrder.id.in_(order_ids)).delete(synchronize_session=False)
        
        db.session.commit()
        
        logger.info(f"批量删除订单成功：{', '.join(order_numbers)}")
        return jsonify({'success': True, 'message': f'成功删除 {len(orders)} 个订单'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"批量删除订单失败：{str(e)}")
        return jsonify({'success': False, 'message': f'批量删除失败：{str(e)}'})

# AJAX API接口
@inventory.route('/api/company_inventory/<int:company_id>')
@login_required
@permission_required('inventory', 'view')
def get_company_inventory(company_id):
    """获取公司库存"""
    inventories = Inventory.query.filter_by(company_id=company_id).join(Product).all()
    
    result = []
    for inv in inventories:
        status = get_inventory_status(company_id, inv.product_id)
        result.append({
            'product_id': inv.product_id,
            'product_name': inv.product.product_name,
            'product_mn': inv.product.product_mn,
            'quantity': inv.quantity,
            'unit': inv.unit,
            'status': status['status'],
            'warning': status['warning']
        })
    
    return jsonify(result)

@inventory.route('/api/product_info/<int:product_id>')
@login_required
@permission_required('inventory', 'view')
def get_product_info(product_id):
    """获取产品信息"""
    try:
        product = Product.query.get_or_404(product_id)
        return jsonify({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.product_name,
                'model': product.product_model,
                'desc': product.product_desc,
                'unit': product.unit,
                'mn': product.product_mn
            }
        })
    except Exception as e:
        logger.error(f"获取产品信息失败：{str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@inventory.route('/api/settle_product', methods=['POST'])
@login_required
@permission_required('settlement', 'create')
def settle_product():
    """将结算单明细中的产品结算到指定公司的库存"""
    try:
        data = request.get_json()
        detail_id = data.get('detail_id')
        company_id = data.get('company_id')
        notes = data.get('notes', '')
        
        if not detail_id or not company_id:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        # 获取结算单明细
        from app.models.pricing_order import SettlementOrderDetail
        detail = SettlementOrderDetail.query.get_or_404(detail_id)
        
        # 检查是否已经结算过
        order_number = detail.settlement_order.order_number
        existing_settlement = Settlement.query.filter_by(
            settlement_number=f"INV-{order_number}"
        ).first()
        
        if existing_settlement:
            # 检查该产品是否已经在结算记录中
            existing_detail = SettlementDetail.query.filter_by(
                settlement_id=existing_settlement.id
            ).join(Product).filter(
                Product.product_name == detail.product_name
            ).first()
            
            if existing_detail:
                return jsonify({'success': False, 'message': '该产品已经结算过了'})
        
        # 获取或创建产品
        product = None
        # SettlementOrderDetail没有product_id字段，需要根据产品名称和MN查找
        if detail.product_mn:
            product = Product.query.filter_by(product_mn=detail.product_mn).first()
        if not product and detail.product_name:
            product = Product.query.filter_by(product_name=detail.product_name).first()
        
        if not product:
            return jsonify({'success': False, 'message': f'未找到产品: {detail.product_name}'})
        
        # 检查或创建库存记录
        inventory = Inventory.query.filter_by(
            company_id=company_id,
            product_id=product.id
        ).first()
        
        if not inventory:
            # 创建新的库存记录
            inventory = Inventory(
                company_id=company_id,
                product_id=product.id,
                quantity=0,
                unit=detail.unit,
                created_by_id=current_user.id
            )
            db.session.add(inventory)
            db.session.flush()  # 获取ID
        
        # 记录变动前的库存
        quantity_before = inventory.quantity
        
        # 检查库存是否充足
        if inventory.quantity < detail.quantity:
            return jsonify({'success': False, 'message': f'库存不足：当前库存 {inventory.quantity}，需要结算 {detail.quantity}'})
        
        # 扣减库存数量（结算是出库操作）
        inventory.quantity -= detail.quantity
        inventory.updated_at = datetime.now()
        
        # 创建或更新结算记录
        if not existing_settlement:
            # 创建新的结算记录
            settlement = Settlement(
                settlement_number=f"INV-{order_number}",
                company_id=company_id,
                settlement_date=datetime.now(),
                status='completed',
                total_items=1,
                description=f'结算单 {order_number} 产品结算',
                created_by_id=current_user.id,
                approved_by_id=current_user.id,
                approved_at=datetime.now()
            )
            db.session.add(settlement)
            db.session.flush()
        else:
            settlement = existing_settlement
            settlement.total_items += 1
            settlement.updated_at = datetime.now()
        
        # 创建结算明细记录
        settlement_detail = SettlementDetail(
            settlement_id=settlement.id,
            inventory_id=inventory.id,
            product_id=product.id,
            quantity_settled=detail.quantity,
            quantity_before=quantity_before,
            quantity_after=inventory.quantity,
            unit=detail.unit,
            notes=notes or f'结算单{order_number}产品结算'
        )
        db.session.add(settlement_detail)
        
        # 创建库存变动记录
        transaction = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type='out',  # 改为出库
            quantity=detail.quantity,
            quantity_before=quantity_before,
            quantity_after=inventory.quantity,
            reference_type='settlement',
            reference_id=settlement.id,
            description=f'结算出库: {detail.product_name}',
            created_by_id=current_user.id
        )
        db.session.add(transaction)
        
        # 提交事务
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '产品结算成功',
            'settlement_id': settlement.id,
            'inventory_id': inventory.id,
            'new_quantity': inventory.quantity
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"产品结算失败：{str(e)}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'结算失败: {str(e)}'})

@inventory.route('/api/settlement_order/<int:settlement_order_id>')
@login_required
@permission_required('settlement', 'view')
def get_settlement_order_detail(settlement_order_id):
    """获取结算单详情（用于模态框显示）"""
    try:
        settlement_order = SettlementOrder.query.get_or_404(settlement_order_id)
        
        # 获取结算状态信息
        settled_products = {}
        settlement_companies = {}
        
        existing_settlement = Settlement.query.filter_by(
            settlement_number=f"INV-{settlement_order.order_number}"
        ).first()
        
        if existing_settlement:
            for detail in existing_settlement.details:
                if detail.product and detail.product.product_name:
                    key = detail.product.product_name
                    settled_products[key] = existing_settlement.settlement_date.strftime('%Y-%m-%d %H:%M') if existing_settlement.settlement_date else ''
                    settlement_companies[key] = existing_settlement.company.company_name if existing_settlement.company else ''
        
        # 构建HTML内容
        html_content = f"""
        <div class="row mb-4">
            <div class="col-md-6">
                <h6>结算单信息</h6>
                <table class="table table-sm">
                    <tr><td><strong>结算单号：</strong></td><td>{settlement_order.order_number}</td></tr>
                    <tr><td><strong>经销商：</strong></td><td>{settlement_order.dealer.company_name if settlement_order.dealer else '无经销商'}</td></tr>
                    <tr><td><strong>关联项目：</strong></td><td>{settlement_order.project.project_name if settlement_order.project else '无关联项目'}</td></tr>
                    <tr><td><strong>状态：</strong></td><td>
                        <span class="badge {'bg-success' if settlement_order.status == 'approved' else 'bg-warning' if settlement_order.status == 'pending' else 'bg-secondary'}">
                            {'已批准' if settlement_order.status == 'approved' else '审批中' if settlement_order.status == 'pending' else '草稿'}
                        </span>
                    </td></tr>
                    <tr><td><strong>创建时间：</strong></td><td>{settlement_order.created_at.strftime('%Y-%m-%d %H:%M') if settlement_order.created_at else '-'}</td></tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6>金额信息</h6>
                <table class="table table-sm">
                    <tr><td><strong>结算总金额：</strong></td><td class="text-success">¥{settlement_order.formatted_total_amount}</td></tr>
                    <tr><td><strong>产品项数：</strong></td><td>{len(settlement_order.details)}</td></tr>
                    <tr><td><strong>总折扣率：</strong></td><td>{settlement_order.discount_percentage}%</td></tr>
                </table>
            </div>
        </div>
        
        <h6>产品明细</h6>
        <div class="table-responsive">
            <table class="table table-hover">
                <thead class="table-light">
                    <tr>
                        <th>产品名称</th>
                        <th>型号</th>
                        <th>品牌</th>
                        <th>数量</th>
                        <th>单价</th>
                        <th>小计</th>
                        <th>结算状态</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for detail in settlement_order.details:
            is_settled = detail.product_name in settled_products
            settlement_date = settled_products.get(detail.product_name, '')
            settlement_company = settlement_companies.get(detail.product_name, '')
            
            status_html = ''
            if is_settled:
                status_html = f'''
                    <span class="badge bg-success">已结算</span><br>
                    <small class="text-muted">{settlement_company}</small><br>
                    <small class="text-muted">{settlement_date}</small>
                '''
            else:
                status_html = '<span class="badge bg-warning">待结算</span>'
            
            html_content += f"""
                <tr>
                    <td><strong>{detail.product_name}</strong></td>
                    <td>{detail.product_model or '-'}</td>
                    <td>{detail.brand or '-'}</td>
                    <td>{detail.quantity} {detail.unit or '件'}</td>
                    <td>¥{detail.unit_price:.2f}</td>
                    <td class="text-success">¥{detail.total_price:.2f}</td>
                    <td>{status_html}</td>
                </tr>
            """
        
        html_content += """
                </tbody>
            </table>
        </div>
        """
        
        return jsonify({
            'success': True,
            'html': html_content
        })
        
    except Exception as e:
        logger.error(f"获取结算单详情失败：{str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@inventory.route('/settlement_detail/<order_number>')
@login_required
def settlement_detail_api(order_number):
    """获取结算单详情API"""
    try:
        from app.models.pricing_order import SettlementOrder, SettlementOrderDetail
        
        # 获取结算单
        settlement_order = SettlementOrder.query.filter_by(order_number=order_number).first()
        if not settlement_order:
            return jsonify({'success': False, 'message': '结算单不存在'})
        
        # 获取结算单明细
        details = SettlementOrderDetail.query.filter_by(settlement_order_id=settlement_order.id).all()
        
        # 构建HTML内容
        html_content = f"""
        <div class="row mb-3">
            <div class="col-md-6">
                <h6>结算单信息</h6>
                <table class="table table-sm">
                    <tr><td>结算单号:</td><td>{settlement_order.order_number}</td></tr>
                    <tr><td>项目名称:</td><td>{settlement_order.project.project_name if settlement_order.project else '无项目'}</td></tr>
                    <tr><td>结算公司:</td><td>{settlement_order.dealer.company_name if settlement_order.dealer else '无公司'}</td></tr>
                    <tr><td>创建时间:</td><td>{settlement_order.created_at.strftime('%Y-%m-%d %H:%M') if settlement_order.created_at else '-'}</td></tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6>统计信息</h6>
                <table class="table table-sm">
                    <tr><td>产品数量:</td><td>{len(details)} 项</td></tr>
                    <tr><td>总金额:</td><td>¥{sum(d.total_price or 0 for d in details):,.2f}</td></tr>
                </table>
            </div>
        </div>
        
        <h6>产品明细</h6>
        <div class="table-responsive">
            <table class="table table-sm table-striped">
                <thead>
                    <tr>
                        <th>产品名称</th>
                        <th>型号</th>
                        <th>品牌</th>
                        <th>数量</th>
                        <th>单价</th>
                        <th>总价</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for detail in details:
            html_content += f"""
                    <tr>
                        <td>{detail.product_name or '-'}</td>
                        <td>{detail.product_model or '-'}</td>
                        <td>{detail.brand or '-'}</td>
                        <td>{detail.quantity}</td>
                        <td>¥{detail.unit_price or 0:,.2f}</td>
                        <td>¥{detail.total_price or 0:,.2f}</td>
                    </tr>
            """
        
        html_content += """
                </tbody>
            </table>
        </div>
        """
        
        return jsonify({'success': True, 'html': html_content})
        
    except Exception as e:
        logger.error(f"获取结算单详情失败：{str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@inventory.route('/settle_product/<int:detail_id>', methods=['POST'])
@login_required
def settle_single_product(detail_id):
    """结算单个产品到库存"""
    try:
        from app.models.pricing_order import SettlementOrderDetail
        
        # 获取结算明细
        detail = SettlementOrderDetail.query.get_or_404(detail_id)
        
        # 检查是否已经结算
        settlement_key = f"{detail.settlement_order.order_number}_{detail.product_name}"
        existing_settlement = Settlement.query.filter(
            Settlement.settlement_number == f"INV-{detail.settlement_order.order_number}"
        ).first()
        
        if existing_settlement:
            # 检查该产品是否已在结算中
            for settlement_detail in existing_settlement.details:
                if (settlement_detail.product and 
                    settlement_detail.product.product_name == detail.product_name):
                    return jsonify({'success': False, 'message': '该产品已经结算过了'})
        
        # 获取或创建产品
        product = None
        # SettlementOrderDetail没有product_id字段，需要根据产品名称和MN查找
        if detail.product_mn:
            product = Product.query.filter_by(product_mn=detail.product_mn).first()
        if not product and detail.product_name:
            product = Product.query.filter_by(product_name=detail.product_name).first()
        
        if not product:
            return jsonify({'success': False, 'message': '找不到对应的产品信息'})
        
        # 获取结算公司
        settlement_company = detail.settlement_order.dealer
        if not settlement_company:
            return jsonify({'success': False, 'message': '结算单没有指定结算公司'})
        
        # 创建或更新结算记录
        if not existing_settlement:
            existing_settlement = Settlement(
                settlement_number=f"INV-{detail.settlement_order.order_number}",
                company_id=settlement_company.id,
                settlement_date=datetime.now(),
                status='completed',
                notes=f"从结算单 {detail.settlement_order.order_number} 结算"
            )
            db.session.add(existing_settlement)
            db.session.flush()  # 获取ID
        
        # 创建结算明细
        settlement_detail = SettlementDetail(
            settlement_id=existing_settlement.id,
            product_id=product.id,
            quantity=detail.quantity,
            unit_price=detail.unit_price or 0,
            total_price=detail.total_price or 0,
            notes=f"从结算单明细 {detail_id} 结算"
        )
        db.session.add(settlement_detail)
        
        # 更新库存 - 结算应该是出库操作，减少库存
        inventory = Inventory.query.filter_by(
            product_id=product.id,
            company_id=settlement_company.id
        ).first()
        
        if not inventory:
            return jsonify({'success': False, 'message': f'公司 {settlement_company.company_name} 没有产品 {product.product_name} 的库存记录'})
        
        # 检查库存是否充足
        if inventory.quantity < detail.quantity:
            return jsonify({'success': False, 'message': f'库存不足：当前库存 {inventory.quantity}，需要结算 {detail.quantity}'})
        
        # 记录变动前后数量
        quantity_before = inventory.quantity
        quantity_after = inventory.quantity - detail.quantity
        
        # 扣减库存
        inventory.quantity -= detail.quantity
        inventory.updated_at = datetime.now()
        
        # 更新结算明细以包含库存变动信息
        settlement_detail.quantity_settled = detail.quantity
        settlement_detail.quantity_before = quantity_before
        settlement_detail.quantity_after = quantity_after
        settlement_detail.inventory_id = inventory.id
        
        # 创建库存变动记录
        transaction = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type='out',
            quantity=detail.quantity,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            unit_price=detail.unit_price or 0,
            total_price=detail.total_price or 0,
            transaction_date=datetime.now(),
            reference_type='settlement',
            reference_id=existing_settlement.id,
            description=f"结算出库：{detail.settlement_order.order_number}",
            created_by_id=current_user.id
        )
        db.session.add(transaction)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': '产品结算成功'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"结算产品失败：{str(e)}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'结算失败：{str(e)}'})

@inventory.route('/api/settle_product_to_company', methods=['POST'])
@login_required
@permission_required('settlement', 'create')
def settle_product_to_company():
    """将结算单明细中的产品结算到指定公司（新版本，支持MN号精确匹配和记录结算目标公司）"""
    try:
        data = request.get_json()
        detail_id = data.get('detail_id')
        company_id = data.get('company_id')
        notes = data.get('notes', '')
        
        if not detail_id or not company_id:
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        # 获取结算单明细
        from app.models.pricing_order import SettlementOrderDetail
        detail = SettlementOrderDetail.query.get_or_404(detail_id)
        
        # 检查是否已经结算过
        if detail.settlement_status == 'settled':
            return jsonify({'success': False, 'message': '该产品已经结算过了'})
        
        # 检查产品MN号
        if not detail.product_mn:
            return jsonify({'success': False, 'message': '该产品没有MN号，无法进行精确匹配结算'})
        
        # 获取或创建产品（按MN号精确匹配）
        product = Product.query.filter_by(product_mn=detail.product_mn).first()
        if not product:
            return jsonify({'success': False, 'message': f'未找到MN号为 {detail.product_mn} 的产品'})
        
        # 获取结算目标公司
        settlement_company = Company.query.get_or_404(company_id)
        
        # 检查或创建库存记录
        inventory = Inventory.query.filter_by(
            company_id=company_id,
            product_id=product.id
        ).first()
        
        if not inventory:
            return jsonify({'success': False, 'message': f'公司 {settlement_company.company_name} 没有产品 {product.product_name} (MN: {detail.product_mn}) 的库存记录'})
        
        # 检查库存数量，支持部分结算
        if inventory.quantity == 0:
            return jsonify({'success': False, 'message': f'库存为0，无法结算'})
        
        # 计算实际可结算数量
        actual_settle_quantity = min(inventory.quantity, detail.quantity)
        is_partial = actual_settle_quantity < detail.quantity
        
        # 记录变动前的库存
        quantity_before = inventory.quantity
        quantity_after = inventory.quantity - actual_settle_quantity
        
        # 扣减库存数量（结算是出库操作）
        inventory.quantity -= actual_settle_quantity
        inventory.updated_at = datetime.now()
        
        # 更新结算明细状态
        detail.settlement_company_id = company_id
        detail.settlement_status = 'settled'
        detail.settlement_date = datetime.now()
        detail.settlement_notes = notes or f'结算到 {settlement_company.company_name}'
        
        # 如果是部分结算，需要创建新的明细记录保留未结算部分
        if is_partial:
            remaining_quantity = detail.quantity - actual_settle_quantity
            detail.quantity = actual_settle_quantity  # 当前明细改为已结算数量
            
            # 创建新的明细记录保留未结算部分
            new_detail = SettlementOrderDetail(
                settlement_order_id=detail.settlement_order_id,
                product_name=detail.product_name,
                product_model=detail.product_model,
                product_desc=detail.product_desc,
                brand=detail.brand,
                product_mn=detail.product_mn,
                quantity=remaining_quantity,
                unit=detail.unit,
                unit_price=detail.unit_price,
                total_price=detail.unit_price * remaining_quantity if detail.unit_price else 0,
                settlement_status='pending'
            )
            db.session.add(new_detail)
        
        # 创建库存变动记录
        transaction = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type='out',
            quantity=actual_settle_quantity,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            description=f'结算出库 - {detail.settlement_order.order_number}',
            reference_type='settlement',
            reference_id=detail.id,
            created_by_id=current_user.id
        )
        db.session.add(transaction)
        
        # 更新结算单的settlement_status字段
        settlement_order = detail.settlement_order
        settlement_order.update_settlement_status()
        
        db.session.commit()
        
        message = f'产品结算成功，已从 {settlement_company.company_name} 扣减库存 {actual_settle_quantity} 件'
        if is_partial:
            remaining_quantity = detail.quantity - actual_settle_quantity
            message += f'，剩余 {remaining_quantity} 件未结算'
            
        return jsonify({
            'success': True, 
            'message': message,
            'settlement_info': {
                'company_name': settlement_company.company_name,
                'quantity_before': quantity_before,
                'quantity_after': quantity_after,
                'settled_quantity': actual_settle_quantity,
                'settlement_date': detail.settlement_date.strftime('%Y-%m-%d %H:%M:%S'),
                'is_partial': is_partial,
                'quantity_remaining': detail.quantity - actual_settle_quantity if is_partial else 0
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"结算产品到指定公司失败：{str(e)}")
        return jsonify({'success': False, 'message': f'结算失败：{str(e)}'})

@inventory.route('/add_inventory', methods=['GET', 'POST'])
@login_required
@permission_required('inventory', 'create')
def add_inventory():
    """批量添加库存页面"""
    # 只获取 company_type 为 'dealer' 且未删除的公司
    companies = Company.query.filter(
        Company.company_type == 'dealer',
        Company.is_deleted == False
    ).order_by(Company.company_name).all()
    return render_template('inventory/add_inventory.html', companies=companies)

@inventory.route('/add_inventory_bulk', methods=['POST'])
@login_required
@permission_required('inventory', 'create')
def add_inventory_bulk():
    """批量添加库存处理"""
    try:
        company_id = request.form.get('company_id')
        if not company_id:
            flash('请选择库存公司', 'danger')
            return redirect(url_for('inventory.add_inventory'))
        
        # 获取所有产品数据
        product_names = request.form.getlist('product_name[]')
        product_models = request.form.getlist('product_model[]')
        product_specs = request.form.getlist('product_spec[]')
        product_brands = request.form.getlist('product_brand[]')
        product_units = request.form.getlist('product_unit[]')
        quantities = request.form.getlist('quantity[]')
        product_mns = request.form.getlist('product_mn[]')
        
        success_count = 0
        error_messages = []
        
        # 处理每个产品
        for i in range(len(product_names)):
            if not product_names[i].strip():
                continue
                
            try:
                quantity = int(quantities[i]) if quantities[i] else 0
                if quantity <= 0:
                    continue
                
                # 查找产品（优先使用MN号匹配）
                product = None
                if product_mns[i]:
                    product = Product.query.filter_by(product_mn=product_mns[i]).first()
                
                if not product and product_names[i] and product_models[i]:
                    product = Product.query.filter(
                        Product.product_name == product_names[i],
                        Product.model == product_models[i]
                    ).first()
                
                if not product:
                    error_messages.append(f'未找到产品：{product_names[i]} - {product_models[i]}')
                    continue
                
                # 添加库存
                success, message, _ = update_inventory(
                    company_id=company_id,
                    product_id=product.id,
                    quantity_change=quantity,
                    transaction_type='in',
                    description=f'批量添加库存 - {product.product_name}',
                    reference_type='manual',
                    user_id=current_user.id
                )
                
                if success:
                    success_count += 1
                else:
                    error_messages.append(f'{product.product_name}: {message}')
                    
            except Exception as e:
                error_messages.append(f'处理产品 {product_names[i]} 时出错：{str(e)}')
        
        # 显示结果
        if success_count > 0:
            flash(f'成功添加 {success_count} 个产品的库存', 'success')
        
        if error_messages:
            for msg in error_messages[:5]:  # 只显示前5个错误
                flash(msg, 'warning')
            if len(error_messages) > 5:
                flash(f'另外还有 {len(error_messages) - 5} 个错误...', 'warning')
        
        if success_count == 0 and error_messages:
            flash('没有成功添加任何库存', 'danger')
            return redirect(url_for('inventory.add_inventory'))
        
        return redirect(url_for('inventory.stock_list'))
        
    except Exception as e:
        logger.error(f"批量添加库存失败：{str(e)}")
        flash(f'操作失败：{str(e)}', 'danger')
        return redirect(url_for('inventory.add_inventory'))

@inventory.route('/stock/<int:inventory_id>/settlements')
@login_required
@permission_required('inventory', 'view')
def view_stock_settlements(inventory_id):
    """查看库存相关的结算记录"""
    try:
        inventory = Inventory.query.get_or_404(inventory_id)
        
        # 获取相关的结算记录
        from app.models.pricing_order import SettlementOrderDetail
        
        # 通过库存变动记录找到结算相关的交易
        settlement_transactions = InventoryTransaction.query.filter(
            InventoryTransaction.inventory_id == inventory_id,
            InventoryTransaction.reference_type == 'settlement'
        ).order_by(InventoryTransaction.transaction_date.desc()).all()
        
        # 获取结算记录，只包含与当前产品相关的结算明细
        settlement_records = []
        for trans in settlement_transactions:
            if trans.reference_id:
                # 查找对应的结算明细
                settlement_detail = SettlementOrderDetail.query.filter_by(
                    id=trans.reference_id
                ).first()
                if settlement_detail and settlement_detail.settlement_order:
                    # 创建结算记录，包含结算单信息和相关的产品明细
                    settlement_record = {
                        'settlement_order': settlement_detail.settlement_order,
                        'settlement_detail': settlement_detail,
                        'transaction': trans
                    }
                    settlement_records.append(settlement_record)
        
        return render_template('inventory/stock_settlements.html',
                             inventory=inventory,
                             settlement_records=settlement_records)
                             
    except Exception as e:
        logger.error(f"查看库存结算记录失败：{str(e)}")
        flash(f'查看库存结算记录失败：{str(e)}', 'danger')
        return redirect(url_for('inventory.stock_detail', id=inventory_id))

# 产品选择相关API - 为创建订单页面提供支持
@inventory.route('/api/products/categories', methods=['GET'])
@login_required
@permission_required('inventory', 'view')
def get_product_categories_for_order():
    """获取产品类别列表 - 用于订单创建"""
    try:
        from app.models.product import Product
        
        # 获取所有有效产品的类别
        categories = db.session.query(Product.category).filter(
            Product.category.isnot(None),
            Product.status == 'active'
        ).distinct().all()
        
        # 提取类别名称并排序
        category_list = [c[0] for c in categories if c[0]]
        category_list.sort()
        
        logger.debug(f'找到 {len(category_list)} 个类别')
        return jsonify(category_list)
    except Exception as e:
        logger.error(f'获取产品类别列表时出错: {str(e)}')
        return jsonify({
            'error': '获取产品类别列表失败',
            'message': str(e)
        }), 500

@inventory.route('/api/products/by-category', methods=['GET'])
@login_required
@permission_required('inventory', 'view')
def get_products_by_category_for_order():
    """获取指定类别的产品列表 - 用于订单创建"""
    try:
        from app.models.product import Product
        from decimal import Decimal
        
        category = request.args.get('category', '')
        logger.debug(f'正在获取类别 "{category}" 的产品列表...')
        
        if not category:
            return jsonify([])
        
        # 查询指定类别的产品
        products = Product.query.filter_by(
            category=category,
            status='active'
        ).order_by(Product.id).all()
        
        logger.debug(f'找到 {len(products)} 个产品')
        
        def decimal_to_float(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            return obj
        
        result = []
        for p in products:
            try:
                product_dict = {
                    'id': p.id,
                    'product_name': p.product_name,
                    'model': p.model,
                    'specification': p.specification,
                    'brand': p.brand,
                    'unit': p.unit,
                    'retail_price': decimal_to_float(p.retail_price) if p.retail_price else 0,
                    'product_mn': p.product_mn
                }
                result.append(product_dict)
                logger.debug(f'成功处理产品: {p.product_name}, MN: {p.product_mn}')
            except Exception as e:
                logger.error(f'处理产品时出错: {p.id} - {str(e)}')
                continue
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f'获取类别产品列表时出错: {str(e)}')
        return jsonify({
            'error': '获取类别产品列表失败',
            'message': str(e)
        }), 500

# 订单审批相关API
# 标准化审批API路由

@inventory.route('/api/approval/order/templates')
@login_required
def get_order_approval_templates():
    """获取订单审批模板"""
    try:
        from app.helpers.approval_helpers import get_available_templates
        templates = get_available_templates('purchase_order')
        template_list = []
        for template in templates:
            template_list.append({
                'id': template.id,
                'name': template.name,
                'object_type': template.object_type,
                'is_active': template.is_active
            })
        
        return jsonify({
            'success': True,
            'templates': template_list
        })
    except Exception as e:
        logger.error(f"获取审批模板失败：{str(e)}")
        return jsonify({'success': False, 'message': f'获取失败：{str(e)}'})

@inventory.route('/api/approval/order/<int:object_id>/submit', methods=['POST'])
@login_required
@permission_required('order', 'edit')
def submit_order_approval_standard(object_id):
    """提交订单审批 - 标准化API"""
    try:
        # 获取订单
        from app.utils.access_control import get_viewable_data
        viewable_orders = get_viewable_data(PurchaseOrder, current_user)
        order = viewable_orders.filter(PurchaseOrder.id == object_id).first_or_404()
        
        # 检查订单状态
        if order.status != 'draft':
            return jsonify({'success': False, 'message': '只有草稿状态的订单才能提交审批'})
        
        # 导入审批相关函数
        from app.helpers.approval_helpers import start_approval_process, get_available_templates
        
        # 获取可用的审批模板
        templates = get_available_templates('purchase_order')
        if not templates:
            return jsonify({'success': False, 'message': '未找到适用的审批流程模板'})
        
        # 使用第一个可用模板
        template = templates[0]
        
        # 创建审批实例
        approval_instance = start_approval_process(
            object_type='purchase_order',
            object_id=order.id,
            template_id=template.id,
            user_id=current_user.id
        )
        
        if approval_instance:
            # 更新订单状态为审批中
            order.status = 'pending'
            db.session.commit()
            
            logger.info(f"用户 {current_user.username} 提交订单 {order.order_number} 审批")
            return jsonify({'success': True, 'message': '审批提交成功'})
        else:
            return jsonify({'success': False, 'message': '未找到适用的审批流程'})
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"提交订单审批失败：{str(e)}")
        return jsonify({'success': False, 'message': f'提交失败：{str(e)}'})

@inventory.route('/api/approval/order/<int:object_id>/flow')
@login_required
def get_order_approval_flow_standard(object_id):
    """获取订单审批流程信息 - 标准化API"""
    try:
        # 获取订单
        from app.utils.access_control import get_viewable_data
        viewable_orders = get_viewable_data(PurchaseOrder, current_user)
        order = viewable_orders.filter(PurchaseOrder.id == object_id).first_or_404()
        
        # 导入审批相关函数
        from app.helpers.approval_helpers import get_object_approval_instance
        from app.models.approval import ApprovalInstance, ApprovalRecord, ApprovalStep
        
        # 获取审批实例（包含被拒绝的实例）
        approval_instance = get_object_approval_instance('purchase_order', order.id, include_rejected=True)
        
        if not approval_instance:
            # 没有审批实例，可能是草稿状态或其他状态
            # 返回基本的控制信息，即使没有审批实例也要检查权限
            from app.helpers.approval_helpers import can_recall_approval, can_resubmit_approval
            control_info = {
                'status': order.status,
                'is_creator': order.created_by_id == current_user.id,
                'can_submit': order.status == 'draft' and order.created_by_id == current_user.id,
                'can_recall': can_recall_approval('purchase_order', object_id, current_user.id),
                'can_resubmit': can_resubmit_approval('purchase_order', object_id, current_user.id)
            }
            return jsonify({
                'success': False, 
                'message': '未找到审批流程', 
                'approval_flow': None,
                'control_info': control_info
            })
        
        # 获取审批步骤（从模板获取）
        steps = approval_instance.get_steps()
        if not steps:
            return jsonify({'success': False, 'message': '审批流程配置错误'})
        
        # 获取已有的审批记录
        records = ApprovalRecord.query.filter_by(
            instance_id=approval_instance.id
        ).order_by(ApprovalRecord.timestamp.asc()).all()
        
        # 构建响应数据
        stages_data = []
        
        logger.info(f"Debug: 当前步骤号: {approval_instance.current_step}")
        logger.info(f"Debug: 找到 {len(records)} 个审批记录")
        
        # 处理步骤数据（可能是模型对象或字典快照）
        for i, step in enumerate(steps):
            if isinstance(step, dict):
                # 快照数据
                step_name = step.get('step_name', f'步骤{i+1}')
                step_order = step.get('step_order', i+1)
                approver_user_id = step.get('approver_user_id')
            else:
                # 模型对象
                step_name = step.step_name
                step_order = step.step_order
                approver_user_id = step.approver_user_id
            
            # 查找对应的审批记录
            step_record = None
            
            # 首先尝试通过step_id精确匹配（适用于正常模板）
            if hasattr(step, 'id') and isinstance(step.id, int):
                step_record = next((r for r in records if r.step_id == step.id), None)
            
            # 如果没找到，可能是模板快照模式（step_id为None）
            if not step_record and records:
                # 检查是否所有记录的step_id都为None（模板快照模式）
                if all(r.step_id is None for r in records):
                    # 模板快照模式：按照审批顺序匹配
                    # 只有当当前步骤序号小于等于已有记录数时，才认为有记录
                    if step_order <= len(records):
                        step_record = records[step_order - 1]  # 第step_order个步骤对应第step_order-1个记录
            
            logger.info(f"Debug: 步骤 {step_order} ({step_name}), 找到记录: {'是' if step_record else '否'}")
            
            # 确定审批人姓名
            approver_name = '未分配'
            if approver_user_id:
                from app.models.user import User
                approver = User.query.get(approver_user_id)
                approver_name = approver.real_name if approver and approver.real_name else approver.username if approver else '未分配'
            
            # 确定步骤状态
            if step_record:
                # 有审批记录的步骤，根据实际审批结果设置状态
                status = 'approved' if step_record.action == 'approve' else 'rejected'
                processed_at = step_record.timestamp.isoformat() if step_record.timestamp else None
                logger.info(f"Debug: 步骤 {step_order} 状态: {status} (有记录)")
            elif step_order == approval_instance.current_step:
                # 当前待审批步骤
                status = 'pending'
                processed_at = None
                logger.info(f"Debug: 步骤 {step_order} 状态: pending (当前步骤)")
            else:
                # 其他步骤都是等待状态（无论是之前的还是之后的）
                status = 'waiting'
                processed_at = None
                logger.info(f"Debug: 步骤 {step_order} 状态: waiting (其他步骤)")
            
            # 获取评语
            comment = ''
            if step_record:
                comment = step_record.comment or ''
            
            stage_data = {
                'id': step.id if hasattr(step, 'id') else f'step_{i}',
                'stage_name': step_name,
                'stage_order': step_order,
                'status': status,
                'approver_name': approver_name,
                'arrived_at': approval_instance.started_at.isoformat() if step_order <= approval_instance.current_step else None,
                'processed_at': processed_at,
                'comment': comment
            }
            stages_data.append(stage_data)
        
        # 检查当前用户是否可以审批
        can_approve = False
        current_step = approval_instance.current_step
        
        if current_step:
            # 查找当前步骤
            current_step_info = None
            for step in steps:
                if isinstance(step, dict):
                    if step.get('step_order') == current_step:
                        current_step_info = step
                        break
                else:
                    if step.step_order == current_step:
                        current_step_info = step
                        break
            
            # 检查当前用户是否为当前步骤的审批人
            if current_step_info:
                approver_user_id = current_step_info.get('approver_user_id') if isinstance(current_step_info, dict) else current_step_info.approver_user_id
                if approver_user_id == current_user.id:
                    can_approve = True
        
        # 导入控制权限检查函数
        from app.helpers.approval_helpers import can_recall_approval, can_resubmit_approval
        
        # 获取实际状态（区分召回和拒绝）
        actual_status = approval_instance.status.value if hasattr(approval_instance.status, 'value') else approval_instance.status
        if actual_status == 'rejected':
            # 检查最后一个记录是否是召回
            last_record = ApprovalRecord.query.filter_by(
                instance_id=approval_instance.id
            ).order_by(ApprovalRecord.timestamp.desc()).first()
            if last_record and last_record.action == 'recall':
                actual_status = 'recalled'
        
        return jsonify({
            'success': True,
            'approval_flow': {
                'stages': stages_data,
                'current_stage': current_step,
                'can_approve': can_approve,
                'status': actual_status,
                'can_recall': can_recall_approval('purchase_order', object_id, current_user.id),
                'can_resubmit': can_resubmit_approval('purchase_order', object_id, current_user.id),
                'is_creator': approval_instance.created_by == current_user.id,
                'creator_id': approval_instance.created_by
            }
        })
        
    except Exception as e:
        logger.error(f"获取审批流程失败：{str(e)}")
        return jsonify({'success': False, 'message': f'获取失败：{str(e)}'})

@inventory.route('/api/approval/order/<int:object_id>/process', methods=['POST'])
@login_required
def process_order_approval_standard(object_id):
    """处理订单审批"""
    try:
        data = request.get_json()
        stage_id = data.get('stage_id')
        action = data.get('action')  # 'approved' 或 'rejected'
        comment = data.get('comment', '')
        
        # 获取订单
        from app.utils.access_control import get_viewable_data
        viewable_orders = get_viewable_data(PurchaseOrder, current_user)
        order = viewable_orders.filter(PurchaseOrder.id == object_id).first_or_404()
        
        # 导入审批相关函数
        from app.helpers.approval_helpers import get_object_approval_instance, process_approval
        from app.models.approval import ApprovalAction
        
        # 获取订单的审批实例
        approval_instance = get_object_approval_instance('purchase_order', order.id)
        if not approval_instance:
            return jsonify({'success': False, 'message': '未找到订单的审批流程'})
        
        # 转换action
        if action == 'approve':
            approval_action = ApprovalAction.APPROVE
        elif action == 'reject':
            approval_action = ApprovalAction.REJECT
        else:
            return jsonify({'success': False, 'message': f'无效的审批动作: {action}'})
        
        # 处理审批
        success = process_approval(
            instance_id=approval_instance.id,
            action=approval_action,
            comment=comment,
            user_id=current_user.id
        )
        
        if not success:
            return jsonify({'success': False, 'message': '审批处理失败'})
        
        # 重新查询实例状态
        db.session.refresh(approval_instance)
        
        # 构建结果
        result = {
            'success': True,
            'message': '审批处理成功',
            'approval_completed': approval_instance.status.value != 'pending',
            'final_status': approval_instance.status.value if approval_instance.status.value != 'pending' else None
        }
        
        # 根据审批结果更新订单状态
        if result.get('approval_completed'):
            if result.get('final_status') == 'approved':
                order.status = 'approved'
            elif result.get('final_status') == 'rejected':
                order.status = 'rejected'
        
        db.session.commit()
        
        logger.info(f"用户 {current_user.username} 处理订单 {order.order_number} 审批，动作：{action}")
        return jsonify(result)
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"处理订单审批失败：{str(e)}")
        return jsonify({'success': False, 'message': f'处理失败：{str(e)}'}) 


@inventory.route('/api/approval/order/<int:object_id>/recall', methods=['POST'])
@login_required
def recall_order_approval_standard(object_id):
    """召回订单审批流程"""
    try:
        # 导入召回函数
        from app.helpers.approval_helpers import recall_approval
        
        # 获取召回原因
        data = request.get_json() or {}
        reason = data.get('reason', '')
        
        # 执行召回
        result = recall_approval('purchase_order', object_id, current_user.id, reason)
        
        if result['success']:
            logger.info(f"用户 {current_user.username} 召回订单 #{object_id} 审批流程")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"召回订单审批失败：{str(e)}")
        return jsonify({'success': False, 'message': f'召回失败：{str(e)}'})


@inventory.route('/api/approval/order/<int:object_id>/resubmit', methods=['POST'])
@login_required
def resubmit_order_approval_standard(object_id):
    """重新提交订单审批流程"""
    try:
        # 导入重新提交函数
        from app.helpers.approval_helpers import resubmit_approval
        
        # 执行重新提交
        result = resubmit_approval('purchase_order', object_id, current_user.id)
        
        if result['success']:
            logger.info(f"用户 {current_user.username} 重新提交订单 #{object_id} 审批流程")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"重新提交订单审批失败：{str(e)}")
        return jsonify({'success': False, 'message': f'重新提交失败：{str(e)}'})


@inventory.route('/api/approval/order/<int:object_id>/control-info', methods=['GET'])
@login_required
def get_order_approval_control_info(object_id):
    """获取订单审批控制信息（召回、重新提交权限等）"""
    try:
        # 导入权限检查函数
        from app.helpers.approval_helpers import can_recall_approval, can_resubmit_approval, get_object_approval_instance
        
        # 获取审批实例
        approval_instance = get_object_approval_instance('purchase_order', object_id)
        
        result = {
            'success': True,
            'can_recall': can_recall_approval('purchase_order', object_id, current_user.id),
            'can_resubmit': can_resubmit_approval('purchase_order', object_id, current_user.id),
            'status': approval_instance.status.value if approval_instance else 'none',
            'is_creator': approval_instance.created_by == current_user.id if approval_instance else False
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"获取订单审批控制信息失败：{str(e)}")
        return jsonify({'success': False, 'message': f'获取失败：{str(e)}'}) 