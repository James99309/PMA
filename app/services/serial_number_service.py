# -*- coding: utf-8 -*-
"""
序列号生成服务

序列号格式: {supplier_code}-{serial_code}-{batch}-{seq}
示例: HWI-BS001-2601A-0001

编码规则:
- supplier_code: 3-4位字母，供应商编码
- serial_code: 5位字母数字，产品序列号编码
- batch: 5位，年月+字母 (YYMML)
  - YY: 年份后两位
  - MM: 月份01-12
  - L: 当月批次字母A-Z
- seq: 4位序号，0001-9999
"""
from datetime import datetime
from app import db
from app.models.product_serial_number import ProductSerialNumber, SerialNumberHistory


def generate_batch_code(purchase_order):
    """
    生成批次号

    格式: YYMML
    - YY: 年份后两位
    - MM: 月份
    - L: 当月批次字母（A开始，同供应商同产品当月递增）

    Args:
        purchase_order: 采购订单对象

    Returns:
        str: 批次号
    """
    now = datetime.now()
    year = str(now.year)[2:]  # 后两位年份
    month = str(now.month).zfill(2)  # 两位月份

    # 当月批次基础前缀
    prefix = f"{year}{month}"

    # 查找当月已有的批次号，确定字母
    # 按供应商分组，同一供应商同月递增
    existing = ProductSerialNumber.query.filter(
        ProductSerialNumber.batch_number.like(f"{prefix}%"),
        ProductSerialNumber.supplier_id == purchase_order.company_id
    ).distinct(ProductSerialNumber.batch_number).all()

    existing_batches = set(sn.batch_number for sn in existing if sn.batch_number)

    # 找到下一个可用字母
    for i in range(26):  # A-Z
        letter = chr(65 + i)  # A=65
        batch = f"{prefix}{letter}"
        if batch not in existing_batches:
            return batch

    # 超过26个批次，使用双字母
    return f"{prefix}Z"


def generate_serial_number(supplier_code, serial_code, batch_number, sequence):
    """
    生成完整序列号

    Args:
        supplier_code: 供应商编码 (3-4字符)
        serial_code: 产品序列号编码 (5字符)
        batch_number: 批次号 (5字符)
        sequence: 序号 (整数)

    Returns:
        str: 完整序列号
    """
    seq_str = str(sequence).zfill(4)
    return f"{supplier_code}-{serial_code}-{batch_number}-{seq_str}"


def get_next_sequence(supplier_code, serial_code, batch_number):
    """
    获取下一个可用序号

    Args:
        supplier_code: 供应商编码
        serial_code: 产品序列号编码
        batch_number: 批次号

    Returns:
        int: 下一个序号
    """
    prefix = f"{supplier_code}-{serial_code}-{batch_number}-"

    # 查找当前批次最大序号
    last_sn = ProductSerialNumber.query.filter(
        ProductSerialNumber.serial_number.like(f"{prefix}%")
    ).order_by(ProductSerialNumber.serial_number.desc()).first()

    if last_sn:
        try:
            # 提取序号部分
            last_seq = int(last_sn.serial_number.split('-')[-1])
            return last_seq + 1
        except (ValueError, IndexError):
            pass

    return 1


def generate_serial_numbers_for_order(purchase_order, created_by_id):
    """
    为采购订单生成所有产品的序列号

    此函数应在采购订单审批通过后调用。

    Args:
        purchase_order: 采购订单对象
        created_by_id: 创建人ID

    Returns:
        dict: {
            'success': bool,
            'message': str,
            'serial_numbers': list[ProductSerialNumber],
            'errors': list[str]
        }
    """
    from app.models.inventory import PurchaseOrder, PurchaseOrderDetail
    from app.models.product import Product
    from app.models.customer import Company

    errors = []
    created_sns = []

    # 验证订单状态
    if purchase_order.status not in ['approved', 'confirmed']:
        return {
            'success': False,
            'message': f'订单状态不正确，当前状态: {purchase_order.status}',
            'serial_numbers': [],
            'errors': ['订单必须为已审批或已确认状态']
        }

    # 获取供应商编码
    supplier = purchase_order.company
    if not supplier:
        return {
            'success': False,
            'message': '找不到供应商信息',
            'serial_numbers': [],
            'errors': ['订单未关联供应商']
        }

    supplier_code = supplier.supplier_code
    if not supplier_code:
        return {
            'success': False,
            'message': f'供应商 {supplier.company_name} 未设置供应商编码',
            'serial_numbers': [],
            'errors': [f'请先为供应商 "{supplier.company_name}" 设置供应商编码(supplier_code)']
        }

    # 生成批次号
    batch_number = generate_batch_code(purchase_order)

    # 检查是否已生成过序列号
    existing_count = ProductSerialNumber.query.filter_by(
        purchase_order_id=purchase_order.id
    ).count()

    if existing_count > 0:
        return {
            'success': False,
            'message': f'该订单已生成 {existing_count} 个序列号',
            'serial_numbers': [],
            'errors': ['不可重复生成序列号']
        }

    # 遍历订单明细，生成序列号
    for detail in purchase_order.details:
        product = detail.product
        if not product:
            errors.append(f'订单明细 ID:{detail.id} 未关联产品')
            continue

        serial_code = product.serial_code
        if not serial_code:
            errors.append(f'产品 "{product.name}" 未设置序列号编码(serial_code)')
            continue

        # 获取起始序号
        start_seq = get_next_sequence(supplier_code, serial_code, batch_number)

        # 为每个数量生成序列号
        for i in range(detail.quantity):
            seq = start_seq + i
            sn_str = generate_serial_number(supplier_code, serial_code, batch_number, seq)

            # 创建序列号记录
            sn = ProductSerialNumber(
                serial_number=sn_str,
                product_id=product.id,
                purchase_order_id=purchase_order.id,
                purchase_detail_id=detail.id,
                batch_number=batch_number,
                supplier_id=supplier.id,
                status='registered',
                created_by_id=created_by_id
            )
            db.session.add(sn)
            created_sns.append(sn)

            # 记录历史
            history = SerialNumberHistory(
                serial_number_id=None,  # flush后更新
                action='register',
                status_before=None,
                status_after='registered',
                reference_type='purchase_order',
                reference_id=purchase_order.id,
                description=f'采购订单 {purchase_order.order_number} 审批通过后自动生成',
                operated_by_id=created_by_id
            )
            db.session.add(history)

    if errors and not created_sns:
        return {
            'success': False,
            'message': '序列号生成失败',
            'serial_numbers': [],
            'errors': errors
        }

    try:
        db.session.flush()

        # 更新历史记录的serial_number_id
        # (需要优化，这里简化处理)

        db.session.commit()

        return {
            'success': True,
            'message': f'成功生成 {len(created_sns)} 个序列号',
            'serial_numbers': created_sns,
            'errors': errors
        }
    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'message': f'数据库错误: {str(e)}',
            'serial_numbers': [],
            'errors': [str(e)]
        }


def validate_encoding_setup(purchase_order):
    """
    验证编码设置是否完整

    在生成序列号前调用，检查供应商和产品的编码是否已设置。

    Args:
        purchase_order: 采购订单对象

    Returns:
        dict: {
            'valid': bool,
            'errors': list[str]
        }
    """
    errors = []

    # 检查供应商编码
    supplier = purchase_order.company
    if not supplier:
        errors.append('订单未关联供应商')
    elif not supplier.supplier_code:
        errors.append(f'供应商 "{supplier.company_name}" 未设置供应商编码')

    # 检查产品序列号编码
    for detail in purchase_order.details:
        product = detail.product
        if not product:
            errors.append(f'订单明细 ID:{detail.id} 未关联产品')
        elif not product.serial_code:
            errors.append(f'产品 "{product.name}" 未设置序列号编码')

    return {
        'valid': len(errors) == 0,
        'errors': errors
    }
