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
import io
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
    """库存列表"""
    try:
        logger.info("开始处理库存列表请求")
        
        # 获取查询参数
        search = request.args.get('search', '').strip()
        company_id = request.args.get('company_id')
        low_stock = request.args.get('low_stock')
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        logger.info(f"查询参数: search={search}, company_id={company_id}, low_stock={low_stock}")
        
        # 构建基础查询 - 使用左连接以包含所有库存记录
        query = Inventory.query.outerjoin(Company).outerjoin(Product)
        logger.info("基础查询构建完成（使用外连接）")
        
        # 搜索条件
        if search:
            search_filter = db.or_(
                Product.product_name.contains(search),
                Company.company_name.contains(search)
            )
            query = query.filter(search_filter)
            logger.info(f"应用搜索条件: {search}")
        
        # 公司过滤
        if company_id:
            query = query.filter(Inventory.company_id == company_id)
            logger.info(f"应用公司过滤: {company_id}")
        
        # 库存状态过滤
        if low_stock == '1':
            # 低库存：当前库存小于等于最低库存警戒线
            query = query.filter(Inventory.quantity <= Inventory.min_stock)
            logger.info("应用低库存过滤")
        elif low_stock == '0':
            # 正常库存：当前库存大于最低库存警戒线
            query = query.filter(Inventory.quantity > Inventory.min_stock)
            logger.info("应用正常库存过滤")
        
        # 排序
        query = query.order_by(Inventory.updated_at.desc())
        logger.info("应用排序完成")
        
        # 获取所有记录（暂时不分页）
        inventories = query.all()
        logger.info(f"查询结果数量: {len(inventories)}")
        
        # 打印前几条记录用于调试
        for i, inv in enumerate(inventories[:3]):
            logger.info(f"库存记录{i+1}: ID={inv.id}, 公司={inv.company.company_name if inv.company else '无'}, 产品={inv.product.product_name if inv.product else '无'}")
        
        # 简化统计数据
        total_items = len(inventories)
        normal_stock = len([i for i in inventories if i.quantity > i.min_stock])
        low_stock_count = len([i for i in inventories if i.quantity <= i.min_stock and i.quantity > 0])
        zero_stock = len([i for i in inventories if i.quantity == 0])
        
        logger.info(f"统计数据: total={total_items}, normal={normal_stock}, low={low_stock_count}, zero={zero_stock}")
        
        # 获取公司列表用于筛选 - 只显示有库存记录的公司
        # 使用子查询避免PostgreSQL JSON字段的DISTINCT问题
        company_ids_with_stock = select(Inventory.company_id).distinct()
        companies_with_stock = Company.query.filter(Company.id.in_(company_ids_with_stock)).order_by(Company.company_name).all()
        logger.info(f"有库存的公司列表数量: {len(companies_with_stock)}")
        
        # 创建简单的分页对象
        class SimplePagination:
            def __init__(self, items):
                self.items = items
                self.total = len(items)
                self.pages = 1
                self.page = 1
                self.has_prev = False
                self.has_next = False
        
        pagination = SimplePagination(inventories)
        
        # 记录要传递给模板的数据
        template_data = {
            'inventories': inventories,
            'pagination': pagination,
            'companies_with_stock': companies_with_stock,
            'search': search,
            'selected_company_id': company_id,
            'selected_low_stock': low_stock,
            'stats': {
                'total': total_items,
                'normal': normal_stock,
                'low': low_stock_count,
                'zero': zero_stock
            }
        }
        
        logger.info(f"模板数据准备完成，inventories数量: {len(template_data['inventories'])}")
        logger.info(f"模板数据stats: {template_data['stats']}")
        
        return render_template('inventory/stock_list.html', **template_data)
                             
    except Exception as e:
        logger.error(f"库存列表查询失败：{str(e)}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        flash(f'加载库存列表失败：{str(e)}', 'danger')
        return render_template('inventory/stock_list.html',
                             inventories=[],
                             pagination=None,
                             companies_with_stock=[],
                             search='',
                             selected_company_id='',
                             selected_low_stock='',
                             stats={
                                 'total': 0,
                                 'normal': 0,
                                 'low': 0,
                                 'zero': 0
                             })

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
    companies = Company.query.order_by(Company.company_name).all()
    products = Product.query.order_by(Product.product_name).all()
    
    return render_template('inventory/add_stock.html', 
                         companies=companies, 
                         products=products)

@inventory.route('/settlement')
@login_required
def settlement_list():
    """结算明细列表 - 使用新的结算状态字段"""
    try:
        # 获取查询参数
        search = request.args.get('search', '').strip()
        company_filter = request.args.get('company_filter')
        status_filter = request.args.get('status_filter')
        settlement_company_filter = request.args.get('settlement_company_filter')  # 新增：结算目标公司过滤
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
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
                query = query.filter(SettlementOrderDetail.settlement_status == 'completed')
            elif status_filter == 'pending':
                query = query.filter(SettlementOrderDetail.settlement_status == 'pending')
        
        # 排序
        query = query.order_by(SettlementOrder.created_at.desc(), SettlementOrderDetail.id.desc())
        
        # 分页
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        settlement_details_raw = pagination.items
        
        # 处理结算明细数据和统计
        settlement_details = []
        total_count = 0
        settled_count = 0
        pending_count = 0
        total_amount = 0
        settled_amount = 0
        pending_amount = 0
        thismonth_count = 0
        thismonth_amount = 0
        
        current_month = datetime.now().strftime('%Y-%m')
        
        for detail in settlement_details_raw:
            # 统计数据
            total_count += 1
            total_amount += float(detail.total_price or 0)
            
            is_settled = detail.settlement_status == 'completed'
            
            if is_settled:
                settled_count += 1
                settled_amount += float(detail.total_price or 0)
                
                # 检查是否为本月结算
                if detail.settlement_date and detail.settlement_date.strftime('%Y-%m') == current_month:
                    thismonth_count += 1
                    thismonth_amount += float(detail.total_price or 0)
            else:
                pending_count += 1
                pending_amount += float(detail.total_price or 0)
            
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
                'is_settled': is_settled  # 保持兼容性
            }
            
            settlement_details.append(detail_info)
        
        # 将处理后的数据添加到分页对象
        pagination.items = settlement_details
        
        # 获取公司列表用于筛选
        companies = Company.query.order_by(Company.company_name).all()
        
        # 获取有结算记录的公司列表（用于结算目标公司筛选）
        # 使用子查询避免PostgreSQL JSON字段的DISTINCT问题
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
        
        return render_template('inventory/settlement_list.html',
                             settlement_details=pagination,
                             companies=companies,
                             settlement_companies=settlement_companies,
                             search=search,
                             company_filter=company_filter,
                             settlement_company_filter=settlement_company_filter,
                             status_filter=status_filter,
                             total_count=total_count,
                             settled_count=settled_count,
                             pending_count=pending_count,
                             total_amount=total_amount / 10000,  # 转换为万元
                             settled_amount=settled_amount / 10000,
                             pending_amount=pending_amount / 10000,
                             thismonth_count=thismonth_count,
                             thismonth_amount=thismonth_amount / 10000)
                             
    except Exception as e:
        logger.error(f"获取结算明细列表失败：{str(e)}")
        import traceback
        logger.error(f"错误详情: {traceback.format_exc()}")
        flash(f'加载结算明细列表失败：{str(e)}', 'danger')
        return render_template('inventory/settlement_list.html',
                             settlement_details=[],
                             companies=[],
                             settlement_companies=[],
                             search='',
                             company_filter='',
                             settlement_company_filter='',
                             status_filter='',
                             total_count=0,
                             settled_count=0,
                             pending_count=0,
                             total_amount=0,
                             settled_amount=0,
                             pending_amount=0,
                             thismonth_count=0,
                             thismonth_amount=0)

@inventory.route('/settlement_orders')
@login_required
@permission_required('settlement', 'view')
def settlement_order_list():
    """结算单列表"""
    try:
        # 获取所有已审批批价单对应的结算单
        from app.models.pricing_order import PricingOrder
        settlement_orders = db.session.query(SettlementOrder).join(PricingOrder).filter(
            PricingOrder.status == 'approved'
        ).order_by(SettlementOrder.created_at.desc()).all()
        
        # 初始化统计变量
        completed_count = 0
        partial_count = 0
        pending_count = 0
        
        completed_amount = 0.0
        partial_amount = 0.0
        pending_amount = 0.0
        
        # 检查每个结算单的结算状态
        for order in settlement_orders:
            settled_count = 0
            total_count = len(order.details)
            order_amount = order.total_amount or 0.0
            
            # 检查是否有相关的库存结算记录
            existing_settlement = Settlement.query.filter_by(
                settlement_number=f"INV-{order.order_number}"
            ).first()
            
            if existing_settlement:
                # 统计已结算的产品数量
                settled_products = set()
                for detail in existing_settlement.details:
                    if detail.product and detail.product.product_name:
                        settled_products.add(detail.product.product_name)
                settled_count = len(settled_products)
            
            # 设置结算状态并统计
            if settled_count == 0:
                order.settlement_status = 'pending'
                pending_count += 1
                pending_amount += order_amount
            elif settled_count == total_count:
                order.settlement_status = 'completed'
                completed_count += 1
                completed_amount += order_amount
            else:
                order.settlement_status = 'partial'
                partial_count += 1
                partial_amount += order_amount
        
        # 计算总数和总金额
        total_count = len(settlement_orders)
        total_amount = sum(order.total_amount or 0.0 for order in settlement_orders)
        
        return render_template('inventory/settlement_order_list.html',
                             settlement_orders=settlement_orders,
                             total_count=total_count,
                             total_amount=total_amount / 10000,  # 转换为万元
                             completed_count=completed_count,
                             partial_count=partial_count,
                             pending_count=pending_count,
                             fully_settled_count=completed_count,
                             fully_settled_amount=completed_amount / 10000,
                             partially_settled_count=partial_count,
                             partially_settled_amount=partial_amount / 10000,
                             pending_amount=pending_amount / 10000)
                             
    except Exception as e:
        logger.error(f"获取结算单列表失败：{str(e)}")
        flash(f'获取结算单列表失败：{str(e)}', 'danger')
        return render_template('inventory/settlement_order_list.html',
                             settlement_orders=[],
                             total_count=0,
                             total_amount=0,
                             completed_count=0,
                             partial_count=0,
                             pending_count=0,
                             fully_settled_count=0,
                             fully_settled_amount=0,
                             partially_settled_count=0,
                             partially_settled_amount=0,
                             pending_amount=0)

@inventory.route('/settlement_process/<order_number>')
@login_required
def settlement_process(order_number):
    """结算处理页面"""
    try:
        settlement_order = SettlementOrder.query.filter_by(order_number=order_number).first_or_404()
        companies = Company.query.order_by(Company.company_name).all()
        
        return render_template('inventory/settlement_process.html',
                             settlement_order=settlement_order,
                             companies=companies)
                             
    except Exception as e:
        logger.error(f"获取结算处理页面失败：{str(e)}")
        flash(f'获取结算处理页面失败：{str(e)}', 'danger')
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
                'distributor_name': settlement_order.distributor.company_name if settlement_order.distributor else '无分销商',
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
    """订单列表"""
    # 获取搜索和筛选参数
    search = request.args.get('search', '')
    company_id = request.args.get('company_id', '')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
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
        query = query.filter(PurchaseOrder.company_id == company_id)
    
    # 排序和分页
    orders = query.order_by(PurchaseOrder.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # 获取有订单记录的公司列表用于筛选
    company_ids_with_orders = db.session.query(PurchaseOrder.company_id).distinct().subquery()
    companies = Company.query.filter(Company.id.in_(company_ids_with_orders)).order_by(Company.company_name).all()
    
    return render_template('inventory/order_list.html', 
                         orders=orders, 
                         companies=companies,
                         search=search,
                         company_id=company_id)

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
            payment_terms = request.form.get('payment_terms', '')
            delivery_address = request.form.get('delivery_address', '')
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
                payment_terms=payment_terms,
                delivery_address=delivery_address,
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
    
    # 获取公司列表 - 只显示经销商类型的公司（company_type='dealer'）
    companies = Company.query.filter(Company.company_type == 'dealer').order_by(Company.company_name).all()
    
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
    
    return render_template('inventory/order_detail.html', 
                         order=order,
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
    companies = Company.query.all()
    
    return render_template('inventory/edit_order.html', 
                         order=order, 
                         companies=companies)

@inventory.route('/orders/<int:id>/export_pdf')
@login_required
@permission_required('order', 'view')
def export_order_pdf(id):
    """导出订单PDF"""
    try:
        # 使用数据访问控制获取订单
        from app.utils.access_control import get_viewable_data
        viewable_orders = get_viewable_data(PurchaseOrder, current_user)
        order = viewable_orders.filter(PurchaseOrder.id == id).first_or_404()
        
        from app.services.pdf_generator import PDFGenerator
        
        # 生成PDF
        pdf_generator = PDFGenerator()
        pdf_result = pdf_generator.generate_order_pdf(order)
        pdf_content = pdf_result['content']
        filename = pdf_result['filename']
        
        # 返回PDF文件
        from flask import make_response
        from urllib.parse import quote
        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        # 使用URL编码处理中文文件名
        encoded_filename = quote(filename.encode('utf-8'))
        response.headers['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{encoded_filename}'
        
        return response
        
    except Exception as e:
        logger.error(f"导出订单PDF失败: {str(e)}")
        flash(f'导出PDF失败：{str(e)}', 'danger')
        return redirect(url_for('inventory.order_detail', id=id))

@inventory.route('/orders/<int:id>/submit_approval', methods=['POST'])
@login_required
@permission_required('order', 'edit')
def submit_order_approval(id):
    """提交订单审批"""
    try:
        # 使用数据访问控制获取订单
        from app.utils.access_control import get_viewable_data
        viewable_orders = get_viewable_data(PurchaseOrder, current_user)
        order = viewable_orders.filter(PurchaseOrder.id == id).first_or_404()
        
        # 检查订单状态
        if order.status != 'draft':
            flash('只有草稿状态的订单才能提交审批', 'warning')
            return redirect(url_for('inventory.order_detail', id=id))
        
        # 获取表单数据
        template_id = request.form.get('template_id', type=int)
        if not template_id:
            flash('请选择审批流程模板', 'danger')
            return redirect(url_for('inventory.order_detail', id=id))
        
        from app.helpers.approval_helpers import start_approval_process
        
        # 发起审批流程
        instance = start_approval_process(
            object_type='purchase_order',
            object_id=id,
            template_id=template_id,
            user_id=current_user.id
        )
        
        if instance:
            # 更新订单状态为审批中
            order.status = 'pending'
            db.session.commit()
            
            flash('订单审批已提交', 'success')
        else:
            flash('提交审批失败', 'danger')
            
        return redirect(url_for('inventory.order_detail', id=id))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"提交订单审批失败: {str(e)}")
        flash(f'提交审批失败：{str(e)}', 'danger')
        return redirect(url_for('inventory.order_detail', id=id))

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
                    <tr><td><strong>分销商：</strong></td><td>{settlement_order.distributor.company_name if settlement_order.distributor else '无分销商'}</td></tr>
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
                    <tr><td>结算公司:</td><td>{settlement_order.distributor.company_name if settlement_order.distributor else '无公司'}</td></tr>
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
        settlement_company = detail.settlement_order.distributor
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
        if detail.settlement_status == 'completed':
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
        
        # 检查库存是否充足
        if inventory.quantity < detail.quantity:
            return jsonify({'success': False, 'message': f'库存不足：当前库存 {inventory.quantity}，需要结算 {detail.quantity}'})
        
        # 记录变动前的库存
        quantity_before = inventory.quantity
        quantity_after = inventory.quantity - detail.quantity
        
        # 扣减库存数量（结算是出库操作）
        inventory.quantity -= detail.quantity
        inventory.updated_at = datetime.now()
        
        # 更新结算明细状态
        detail.settlement_company_id = company_id
        detail.settlement_status = 'completed'
        detail.settlement_date = datetime.now()
        detail.settlement_notes = notes or f'结算到 {settlement_company.company_name}'
        
        # 创建库存变动记录
        transaction = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type='out',
            quantity=detail.quantity,
            unit_price=detail.unit_price or 0,
            total_price=detail.total_price or 0,
            description=f'结算出库 - {detail.settlement_order.order_number}',
            reference_type='settlement',
            reference_id=detail.id,
            created_by_id=current_user.id
        )
        db.session.add(transaction)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'产品结算成功，已从 {settlement_company.company_name} 扣减库存 {detail.quantity} 件',
            'settlement_info': {
                'company_name': settlement_company.company_name,
                'quantity_before': quantity_before,
                'quantity_after': quantity_after,
                'settlement_date': detail.settlement_date.strftime('%Y-%m-%d %H:%M:%S')
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
    # 只获取 company_type 为 'dealer' 的公司
    companies = Company.query.filter(
        Company.company_type == 'dealer'
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