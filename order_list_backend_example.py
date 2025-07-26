"""
订单列表 - 通用列表组件系统示例
展示如何将现有订单列表迁移到新的通用组件系统
"""

from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from app.decorators import permission_required
from app.models.inventory import PurchaseOrder
from app.models.company import Company
from sqlalchemy import func

@inventory.route('/order_list_new')
@login_required
@permission_required('inventory', 'view')
def order_list_new():
    """使用通用列表组件的订单列表页面"""
    
    # 获取筛选参数（用于初始统计）
    search = request.args.get('search', '')
    company_id = request.args.get('company_id', '')
    status = request.args.get('status', '')
    inventory_status = request.args.get('inventory_status', '')
    
    # 构建基础查询
    query = PurchaseOrder.query
    
    # 应用筛选条件（用于统计）
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
    all_orders = query.all()
    
    # 分类统计
    total_count = len(all_orders)
    total_amount = sum(order.total_amount or 0 for order in all_orders)
    
    pending_orders = [o for o in all_orders if o.inventory_status == 'pending']
    pending_count = len(pending_orders)
    pending_amount = sum(order.total_amount or 0 for order in pending_orders)
    
    partial_orders = [o for o in all_orders if o.inventory_status == 'partially_received']
    partial_count = len(partial_orders)
    partial_amount = sum(order.total_amount or 0 for order in partial_orders)
    
    completed_orders = [o for o in all_orders if o.inventory_status == 'fully_received']
    completed_count = len(completed_orders)
    completed_amount = sum(order.total_amount or 0 for order in completed_orders)
    
    # 获取公司列表供筛选使用
    companies = Company.query.filter(Company.is_deleted == False).order_by(Company.company_name).all()
    
    # 构建筛选配置（复用现有配置）
    filter_config = {
        'action_url': url_for('inventory.order_list_new'),
        'form_id': 'orderFilterForm',
        'reset_url': url_for('inventory.order_list_new'),
        
        'search_field': {
            'name': 'search',
            'label': '搜索',
            'placeholder': '订单号或公司名称',
            'value': search,
            'col_width': 4
        },
        
        'filter_fields': [
            {
                'name': 'company_id',
                'label': '公司',
                'all_option_text': '全部公司',
                'current_value': company_id,
                'col_width': 3,
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
                'col_width': 3,
                'options': [
                    {'value': 'draft', 'label': '草稿', 'translate': True},
                    {'value': 'pending', 'label': '审批中', 'translate': True},
                    {'value': 'approved', 'label': '已审批', 'translate': True},
                    {'value': 'rejected', 'label': '已拒绝', 'translate': True}
                ]
            },
            {
                'name': 'inventory_status',
                'label': '入库状态',
                'all_option_text': '全部状态',
                'current_value': inventory_status,
                'col_width': 2,
                'options': [
                    {'value': 'pending', 'label': '待入库', 'translate': True},
                    {'value': 'partially_received', 'label': '部分入库', 'translate': True},
                    {'value': 'fully_received', 'label': '已入库', 'translate': True}
                ]
            }
        ],
        
        'search_button_text': '搜索',
        'reset_button_text': '重置'
    }
    
    # 构建通用列表配置
    list_config = {
        'module_name': 'order',
        'title': '订单列表 - 通用组件示例',
        'ajax_mode': True,  # 启用AJAX模式
        
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
                    'clickable': True,
                    'click_params': {},  # 点击时清空筛选
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
                    'clickable': True,
                    'click_params': {'inventory_status': 'pending'},
                    'data_key': 'pending'
                },
                {
                    'id': 'partial',
                    'title': '部分入库',
                    'icon': 'fas fa-exclamation-triangle',
                    'value': partial_count,
                    'amount': partial_amount,
                    'unit': '单',
                    'amount_unit': '万元',
                    'color': 'info',
                    'clickable': True,
                    'click_params': {'inventory_status': 'partially_received'},
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
                    'clickable': True,
                    'click_params': {'inventory_status': 'fully_received'},
                    'data_key': 'completed'
                }
            ]
        },
        
        # 筛选配置（复用现有筛选组件）
        'filter': filter_config,
        
        # 表格配置
        'table': {
            'ajax_target': 'orderTableBody',
            'title': '订单列表',
            'icon': 'fas fa-table',
            'badge_text': (
                '全部订单' if not inventory_status else 
                '待入库订单' if inventory_status == 'pending' else
                '部分入库订单' if inventory_status == 'partially_received' else
                '已入库订单' if inventory_status == 'fully_received' else
                '筛选结果'
            ),
            'columns': [
                {
                    'key': 'order_number',
                    'label': '订单号',
                    'type': 'link',
                    'url_template': '/inventory/order/{id}',
                    'width': '140px'
                },
                {
                    'key': 'company_name',
                    'label': '公司',
                    'type': 'text',
                    'width': '180px'
                },
                {
                    'key': 'order_date',
                    'label': '订单日期',
                    'type': 'date',
                    'format': '%Y-%m-%d',
                    'width': '120px'
                },
                {
                    'key': 'expected_date',
                    'label': '预期日期',
                    'type': 'date',
                    'format': '%Y-%m-%d',
                    'width': '120px'
                },
                {
                    'key': 'total_quantity',
                    'label': '总数量',
                    'type': 'number',
                    'align': 'center',
                    'width': '80px'
                },
                {
                    'key': 'total_amount',
                    'label': '总金额',
                    'type': 'number',
                    'format': 'wan',
                    'align': 'end',
                    'width': '100px'
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
                    'key': 'owner_name',
                    'label': '创建人',
                    'type': 'badge',
                    'width': '120px'
                }
            ]
        }
    }
    
    return render_template('inventory/order_list_new.html', 
                         list_config=list_config,
                         filter_config=filter_config,
                         total_count=total_count,
                         total_amount=total_amount,
                         pending_count=pending_count,
                         pending_amount=pending_amount,
                         partial_count=partial_count,
                         partial_amount=partial_amount,
                         completed_count=completed_count,
                         completed_amount=completed_amount,
                         inventory_status=inventory_status)

@inventory.route('/api/order_list_new_ajax', methods=['GET'])
@login_required  
@permission_required('inventory', 'view')
def order_list_new_ajax():
    """订单列表新版AJAX端点 - 通用组件格式"""
    
    # 获取搜索和筛选参数
    search = request.args.get('search', '')
    company_id = request.args.get('company_id', '')
    status = request.args.get('status', '')
    inventory_status = request.args.get('inventory_status', '')
    
    # 分页参数
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 20, type=int)
    
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
        all_orders = query.order_by(PurchaseOrder.created_at.desc()).all()
        filtered_orders = [order for order in all_orders if order.inventory_status == inventory_status]
        
        # 手动分页
        total_count = len(filtered_orders)
        orders = filtered_orders[offset:offset + limit]
    else:
        # 普通查询可以使用数据库分页
        total_count = query.count()
        orders = query.order_by(PurchaseOrder.created_at.desc()).offset(offset).limit(limit).all()
    
    # 生成HTML行数据
    html_rows = []
    for order in orders:
        # 获取公司名称
        company_name = order.company.company_name if order.company else '-'
        
        # 获取创建人信息
        owner_display = order.owner.real_name if order.owner and order.owner.real_name else (
            order.owner.username if order.owner else '未知'
        )
        
        # 生成表格行HTML
        html_row = f"""
        <tr>
            <td>
                <a href="{url_for('inventory.order_detail', id=order.id)}" class="text-decoration-none">
                    {order.order_number}
                </a>
            </td>
            <td title="{company_name}">{company_name}</td>
            <td>{order.order_date.strftime('%Y-%m-%d') if order.order_date else '-'}</td>
            <td>{order.expected_date.strftime('%Y-%m-%d') if order.expected_date else '-'}</td>
            <td class="text-center">{order.total_quantity or 0}</td>
            <td class="text-end">¥{(order.total_amount or 0)/10000:.2f}万</td>
            <td>
                <span class="badge badge-pill order-status-{order.status}">
                    {get_status_display(order.status)}
                </span>
            </td>
            <td>
                <span class="badge badge-pill inventory-status-{order.inventory_status or 'pending'}">
                    {get_inventory_status_display(order.inventory_status)}
                </span>
            </td>
            <td>
                <span class="badge bg-secondary">{owner_display}</span>
            </td>
        </tr>
        """
        html_rows.append(html_row)
    
    # 计算统计数据（用于更新统计卡片）
    all_orders_for_stats = query.all()
    
    # 按状态分类统计
    total_stats_count = len(all_orders_for_stats)
    total_stats_amount = sum(order.total_amount or 0 for order in all_orders_for_stats)
    
    pending_orders = [o for o in all_orders_for_stats if o.inventory_status == 'pending']
    pending_stats_count = len(pending_orders)
    pending_stats_amount = sum(order.total_amount or 0 for order in pending_orders)
    
    partial_orders = [o for o in all_orders_for_stats if o.inventory_status == 'partially_received']
    partial_stats_count = len(partial_orders)
    partial_stats_amount = sum(order.total_amount or 0 for order in partial_orders)
    
    completed_orders = [o for o in all_orders_for_stats if o.inventory_status == 'fully_received']
    completed_stats_count = len(completed_orders)
    completed_stats_amount = sum(order.total_amount or 0 for order in completed_orders)
    
    # 构建统计数据（用于前端更新统计卡片）
    statistics = {
        'total_count': total_stats_count,
        'total_amount': total_stats_amount,
        'pending_count': pending_stats_count,
        'pending_amount': pending_stats_amount,
        'partial_count': partial_stats_count,
        'partial_amount': partial_stats_amount,
        'completed_count': completed_stats_count,
        'completed_amount': completed_stats_amount
    }
    
    return jsonify({
        'success': True,
        'html': '\n'.join(html_rows),
        'total_count': total_count,
        'loaded_count': len(orders),
        'statistics': statistics  # 用于更新统计卡片
    })

def get_status_display(status):
    """获取状态显示文本"""
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

def get_inventory_status_display(inventory_status):
    """获取入库状态显示文本"""
    status_map = {
        'pending': '待入库',
        'partially_received': '部分入库',
        'fully_received': '已入库'
    }
    return status_map.get(inventory_status, '待入库')