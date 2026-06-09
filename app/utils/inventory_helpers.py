from app import db
from app.models.inventory import Inventory, InventoryTransaction, Settlement, SettlementDetail, PurchaseOrder
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def get_vendor_warehouse_label():
    """返回厂商自营仓库的展示名称(取自字典 type='company' AND is_vendor=true 的 value)。

    厂商在系统中只存在于 dictionaries 表(不在 companies),这里读字典作为单一
    数据来源,UI 展示时用 "{value} · 自营仓" 形态;字典为空时返回 "厂商自营仓"。
    """
    from app.models.dictionary import Dictionary
    d = Dictionary.query.filter_by(
        type='company', is_vendor=True, is_active=True
    ).order_by(Dictionary.sort_order).first()
    base = (d.value if d else '厂商') if d else '厂商'
    return f"{base} · 自营仓"

def update_inventory(company_id, product_id, quantity_change, transaction_type,
                     description=None, reference_type=None, reference_id=None, user_id=None,
                     target_type='customer'):
    """
    更新库存数量并记录变动

    Args:
        company_id: 公司ID (target_type='vendor' 时忽略,可传 None)
        product_id: 产品ID
        quantity_change: 变动数量（正数入库，负数出库）
        transaction_type: 变动类型 ('in', 'out', 'settlement', 'adjustment')
        description: 变动说明
        reference_type: 关联单据类型
        reference_id: 关联单据ID
        user_id: 操作用户ID
        target_type: 'customer' (默认, 落到 company_id 的公司仓) 或
                     'vendor' (落到厂商自营仓库, is_vendor_warehouse=true, company_id=NULL)

    Returns:
        tuple: (success, message, inventory_obj)
    """
    try:
        # 查找或创建库存记录(按 target_type 分流)
        if target_type == 'vendor':
            inventory = Inventory.query.filter_by(
                is_vendor_warehouse=True,
                product_id=product_id
            ).first()
        else:
            inventory = Inventory.query.filter_by(
                company_id=company_id,
                product_id=product_id,
                is_vendor_warehouse=False
            ).first()

        if not inventory:
            # 如果是出库或结算操作且没有库存记录，则失败
            if quantity_change < 0:
                return False, "库存不足，无法进行出库操作", None

            # 创建新的库存记录
            inventory = Inventory(
                company_id=(None if target_type == 'vendor' else company_id),
                is_vendor_warehouse=(target_type == 'vendor'),
                product_id=product_id,
                quantity=0,
                created_by_id=user_id
            )
            db.session.add(inventory)
            db.session.flush()  # 获取ID
        
        # 记录变动前数量
        quantity_before = inventory.quantity
        
        # 检查库存是否足够（针对出库操作）
        if quantity_change < 0 and quantity_before + quantity_change < 0:
            return False, f"库存不足，当前库存：{quantity_before}，尝试出库：{abs(quantity_change)}", None
        
        # 更新库存数量
        inventory.quantity += quantity_change
        quantity_after = inventory.quantity
        
        # 记录库存变动
        transaction = InventoryTransaction(
            inventory_id=inventory.id,
            transaction_type=transaction_type,
            quantity=quantity_change,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
            created_by_id=user_id
        )
        db.session.add(transaction)
        
        db.session.commit()
        
        _target_label = '[厂商仓]' if target_type == 'vendor' else f'公司ID {company_id}'
        logger.info(f"库存更新成功：{_target_label}，产品ID {product_id}，变动 {quantity_change}")
        return True, "库存更新成功", inventory

    except Exception as e:
        db.session.rollback()
        logger.error(f"库存更新失败：{str(e)}")
        return False, f"库存更新失败：{str(e)}", None


def link_serials_to_inventory(purchase_detail_id, inventory_id, user_id=None):
    """备货入库后，将该采购明细下尚未绑定库存的序列号绑定到对应库存记录。

    序列号在创建发货单时已写入 ProductSerialNumber（关联 purchase_detail_id），
    但入库时未回填 inventory_id —— 此处补上，使库存/SN管理器能追踪 SN 的入库归属。
    不提交事务，由调用方统一 commit。
    """
    from app.models.product_serial_number import ProductSerialNumber
    updates = {'inventory_id': inventory_id}
    if user_id:
        updates['received_by_id'] = user_id
    ProductSerialNumber.query.filter_by(
        purchase_detail_id=purchase_detail_id,
        inventory_id=None
    ).update(updates, synchronize_session=False)

def process_settlement(company_id, settlement_items, description=None, user_id=None):
    """
    处理库存结算
    
    Args:
        company_id: 公司ID
        settlement_items: 结算项目列表 [{'product_id': 1, 'quantity': 10}, ...]
        description: 结算说明
        user_id: 操作用户ID
        
    Returns:
        tuple: (success, message, settlement_obj)
    """
    try:
        # 生成结算单号
        settlement_number = generate_settlement_number()
        
        # 创建结算单
        settlement = Settlement(
            settlement_number=settlement_number,
            company_id=company_id,
            description=description,
            created_by_id=user_id,
            status='pending'
        )
        db.session.add(settlement)
        db.session.flush()  # 获取ID
        
        total_items = 0
        settlement_details = []
        
        # 处理每个结算项目
        for item in settlement_items:
            product_id = item['product_id']
            quantity = item['quantity']
            
            # 检查库存
            inventory = Inventory.query.filter_by(
                company_id=company_id,
                product_id=product_id
            ).first()
            
            if not inventory or inventory.quantity < quantity:
                db.session.rollback()
                return False, f"产品ID {product_id} 库存不足", None
            
            # 记录结算前后数量
            quantity_before = inventory.quantity
            quantity_after = inventory.quantity - quantity
            
            # 更新库存
            success, message, _ = update_inventory(
                company_id=company_id,
                product_id=product_id,
                quantity_change=-quantity,
                transaction_type='settlement',
                description=f"结算出库 - {settlement_number}",
                reference_type='settlement',
                reference_id=settlement.id,
                user_id=user_id
            )
            
            if not success:
                db.session.rollback()
                return False, message, None
            
            # 创建结算明细
            detail = SettlementDetail(
                settlement_id=settlement.id,
                inventory_id=inventory.id,
                product_id=product_id,
                quantity_settled=quantity,
                quantity_before=quantity_before,
                quantity_after=quantity_after,
                unit=inventory.unit,
                notes=item.get('notes', '')
            )
            settlement_details.append(detail)
            total_items += quantity
        
        # 添加结算明细
        for detail in settlement_details:
            db.session.add(detail)
        
        # 更新结算单总数
        settlement.total_items = total_items
        settlement.status = 'completed'
        
        db.session.commit()
        
        logger.info(f"结算处理成功：结算单号 {settlement_number}")
        return True, "结算处理成功", settlement
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"结算处理失败：{str(e)}")
        return False, f"结算处理失败：{str(e)}", None

def generate_settlement_number():
    """生成结算单号"""
    now = datetime.now()
    date_str = now.strftime('%Y%m%d')
    
    # 查找当天最大的结算单号
    latest = Settlement.query.filter(
        Settlement.settlement_number.like(f'SET{date_str}%')
    ).order_by(Settlement.settlement_number.desc()).first()
    
    if latest:
        # 提取序号并加1
        try:
            seq = int(latest.settlement_number[-3:]) + 1
        except:
            seq = 1
    else:
        seq = 1
    
    return f'SET{date_str}{seq:03d}'

def generate_order_number():
    """生成订单号 - 格式：PUO年份月份-XXX"""
    now = datetime.now()
    year_month = now.strftime('%Y%m')
    
    # 查找当月最大的订单号
    latest = PurchaseOrder.query.filter(
        PurchaseOrder.order_number.like(f'PUO{year_month}-%')
    ).order_by(PurchaseOrder.order_number.desc()).first()
    
    if latest:
        # 提取序号并加1
        try:
            seq = int(latest.order_number.split('-')[-1]) + 1
        except:
            seq = 1
    else:
        seq = 1
    
    return f'PUO{year_month}-{seq:03d}'

def get_inventory_status(company_id, product_id):
    """获取库存状态"""
    inventory = Inventory.query.filter_by(
        company_id=company_id,
        product_id=product_id
    ).first()
    
    if not inventory:
        return {
            'quantity': 0,
            'status': 'no_stock',
            'warning': None
        }
    
    status = 'normal'
    warning = None
    
    if inventory.min_stock > 0 and inventory.quantity <= inventory.min_stock:
        status = 'low_stock'
        warning = f'库存不足，当前：{inventory.quantity}，最低：{inventory.min_stock}'
    elif inventory.max_stock > 0 and inventory.quantity >= inventory.max_stock:
        status = 'over_stock'
        warning = f'库存过多，当前：{inventory.quantity}，最高：{inventory.max_stock}'
    
    return {
        'quantity': inventory.quantity,
        'status': status,
        'warning': warning,
        'inventory': inventory
    }

def calculate_order_totals(order_details):
    """计算订单总计"""
    total_quantity = 0
    total_amount = 0
    
    for detail in order_details:
        total_quantity += detail.quantity
        total_amount += detail.calculated_total
    
    return total_quantity, total_amount 