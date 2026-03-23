# -*- coding: utf-8 -*-
"""
采购订单辅助函数模块

提取自 purchase_order_routes.py 的通用逻辑，避免代码重复
"""
import os
import uuid
import base64
import logging
from datetime import datetime
from flask import current_app

from app import db
from app.models.inventory import PurchaseOrderDetail
from app.models.sales_order import SalesOrderDetail
from app.models.product import Product

logger = logging.getLogger(__name__)


def process_order_detail_item(order_id, item, existing_detail=None):
    """
    处理单个订单明细项（创建或更新）

    Args:
        order_id: 订单ID
        item: 明细数据字典
        existing_detail: 如果是更新，传入现有明细对象

    Returns:
        PurchaseOrderDetail 对象或 None（如果是空行）
    """
    product_id = item.get('product_id')
    product_name = item.get('product_name', '')

    # 跳过没有产品名称的空行
    if not product_name or not product_name.strip():
        return None

    quantity = int(item.get('quantity', 1))
    unit_price = float(item.get('unit_price', 0))
    discount = float(item.get('discount', 1))
    total_price = quantity * unit_price * discount

    # 获取产品信息
    product_model = item.get('product_model', '')
    brand = item.get('brand', '')

    if product_id:
        product = Product.query.get(product_id)
        if product:
            # 创建时使用产品信息，更新时保留用户修改
            if not existing_detail:
                product_name = product.name
            product_model = product.model or product_model
            brand = product.brand or brand

    sales_order_detail_id = item.get('sales_order_detail_id')

    if existing_detail:
        # 更新现有明细
        existing_detail.product_id = product_id
        existing_detail.product_name = product_name
        existing_detail.product_model = product_model
        existing_detail.product_desc = item.get('product_desc', '')
        existing_detail.brand = brand
        existing_detail.quantity = quantity
        existing_detail.unit = item.get('unit', '台')
        existing_detail.unit_price = unit_price
        existing_detail.discount = discount
        existing_detail.total_price = total_price
        existing_detail.notes = item.get('notes')
        existing_detail.sales_order_detail_id = sales_order_detail_id
        return existing_detail
    else:
        # 创建新明细
        return PurchaseOrderDetail(
            order_id=order_id,
            product_id=product_id,
            product_name=product_name,
            product_model=product_model,
            product_desc=item.get('product_desc', ''),
            brand=brand,
            quantity=quantity,
            unit=item.get('unit', '台'),
            unit_price=unit_price,
            discount=discount,
            total_price=total_price,
            notes=item.get('notes'),
            sales_order_detail_id=sales_order_detail_id
        )


def process_order_details(order, details_data, is_update=False):
    """
    统一处理订单明细创建/更新逻辑

    Args:
        order: PurchaseOrder 对象
        details_data: 明细数据列表
        is_update: 是否为更新操作（影响是否删除不在列表中的明细）

    Returns:
        处理的明细数量
    """
    if not details_data:
        return 0

    existing_ids = {d.id for d in order.details} if is_update else set()
    incoming_ids = set()
    processed_count = 0

    for item in details_data:
        detail_id = item.get('id') or item.get('item_id')

        if is_update and detail_id and detail_id in existing_ids:
            # 更新现有明细
            existing_detail = PurchaseOrderDetail.query.get(detail_id)
            if existing_detail:
                result = process_order_detail_item(order.id, item, existing_detail)
                if result:
                    incoming_ids.add(detail_id)
                    processed_count += 1
        else:
            # 新增明细
            detail = process_order_detail_item(order.id, item)
            if detail:
                db.session.add(detail)
                processed_count += 1

    # 删除不在传入列表中的明细（仅更新操作）
    if is_update:
        for detail in order.details:
            if detail.id not in incoming_ids and detail.id in existing_ids:
                db.session.delete(detail)

    # 更新订单汇总
    db.session.flush()
    order.total_quantity = sum(d.quantity for d in order.details) if order.details else 0
    order.total_amount = sum(float(d.total_price or 0) for d in order.details) if order.details else 0

    # 同步更新关联的客户订单需求的 procured_quantity
    refresh_procured_quantities(order)

    return processed_count


def refresh_procured_quantities(order):
    """
    刷新与该采购订单关联的所有客户订单明细的 procured_quantity。
    通过聚合所有关联的PO明细数量来计算。
    """
    # 收集本PO所有关联的SO明细ID
    so_detail_ids = set()
    for d in order.details:
        if d.sales_order_detail_id:
            so_detail_ids.add(d.sales_order_detail_id)

    # 对每个关联的SO明细，重新计算所有PO关联的总采购量
    for so_detail_id in so_detail_ids:
        so_detail = SalesOrderDetail.query.get(so_detail_id)
        if so_detail:
            total_procured = db.session.query(
                db.func.coalesce(db.func.sum(PurchaseOrderDetail.quantity), 0)
            ).filter(
                PurchaseOrderDetail.sales_order_detail_id == so_detail_id
            ).scalar()
            so_detail.procured_quantity = total_procured


def upload_file_to_storage(order, file_content, filename, content_type, subfolder=''):
    """
    统一的文件上传处理（支持云端和本地存储）

    Args:
        order: PurchaseOrder 对象
        file_content: 文件内容（bytes）
        filename: 文件名
        content_type: MIME类型
        subfolder: 子文件夹（可选）

    Returns:
        成功返回文件URL，失败返回None
    """
    try:
        # 清理订单号中的特殊字符
        order_number = order.order_number.replace('/', '-').replace('\\', '-')

        # 判断是否使用云端存储
        use_cloud = os.environ.get('FORCE_CLOUD_UPLOAD', '').lower() == 'true' or \
                    'supabase' in os.environ.get('DATABASE_URL', '').lower()

        if use_cloud:
            return _upload_to_cloud(order_number, file_content, filename, content_type, subfolder)
        else:
            return _upload_to_local(order_number, file_content, filename, subfolder)

    except Exception as e:
        logger.error(f"上传文件失败: {str(e)}")
        return None


def _upload_to_cloud(order_number, file_content, filename, content_type, subfolder=''):
    """上传到云端存储"""
    from app.utils.supabase_client import SupabaseStorageClient
    storage_client = SupabaseStorageClient()

    if not storage_client.client:
        logger.error("Supabase客户端未初始化")
        return None

    # 获取系统标识
    system_id = storage_client._get_system_identifier()

    # 构建存储路径
    path_parts = ['purchase_order_files', system_id, order_number]
    if subfolder:
        path_parts.append(subfolder)
    path_parts.append(filename)
    storage_path = '/'.join(path_parts)

    bucket_name = storage_client.get_bucket_name('invoice')

    # 上传到Supabase
    result = storage_client.client.storage.from_(bucket_name).upload(
        path=storage_path,
        file=file_content,
        file_options={"content-type": content_type}
    )

    # 获取公共URL
    public_url = storage_client.client.storage.from_(bucket_name).get_public_url(storage_path)
    logger.info(f"☁️ 文件上传成功: {public_url}")
    return public_url


def _upload_to_local(order_number, file_content, filename, subfolder=''):
    """上传到本地存储"""
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')

    # 构建本地目录
    path_parts = [upload_folder, 'purchase_order_files', order_number]
    if subfolder:
        path_parts.append(subfolder)
    local_dir = os.path.join(*path_parts)

    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    local_path = os.path.join(local_dir, filename)
    with open(local_path, 'wb') as f:
        f.write(file_content)

    # 返回相对URL
    url_parts = ['/uploads/purchase_order_files', order_number]
    if subfolder:
        url_parts.append(subfolder)
    url_parts.append(filename)
    file_url = '/'.join(url_parts)

    logger.info(f"📁 文件本地保存: {file_url}")
    return file_url


def upload_signature_image(order, base64_data):
    """
    上传签名图片（从 base64 转换）

    Args:
        order: PurchaseOrder 对象
        base64_data: base64 编码的图片数据 (data:image/png;base64,...)

    Returns:
        成功返回文件URL，失败返回None
    """
    try:
        # 解析 base64 数据
        if ',' in base64_data:
            header, data = base64_data.split(',', 1)
        else:
            data = base64_data

        # 解码 base64
        image_bytes = base64.b64decode(data)

        # 生成唯一文件名
        date_str = datetime.now().strftime('%Y%m%d')
        unique_id = uuid.uuid4().hex[:8]
        filename = f"signature_{date_str}_{unique_id}.png"

        return upload_file_to_storage(order, image_bytes, filename, 'image/png')

    except Exception as e:
        logger.error(f"上传签名图片失败: {str(e)}")
        return None


def upload_supplier_confirmation_file(order, file):
    """
    上传供应商确认回执文件

    Args:
        order: PurchaseOrder 对象
        file: 上传的文件对象

    Returns:
        成功返回文件URL，失败返回None
    """
    try:
        # 获取文件扩展名
        original_filename = file.filename
        file_ext = original_filename.rsplit('.', 1)[-1].lower() if '.' in original_filename else 'pdf'

        # 生成唯一文件名
        date_str = datetime.now().strftime('%Y%m%d')
        unique_id = uuid.uuid4().hex[:8]
        filename = f"supplier_confirm_{date_str}_{unique_id}.{file_ext}"

        # 确定content type
        content_types = {
            'pdf': 'application/pdf',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png'
        }
        content_type = content_types.get(file_ext, 'application/octet-stream')

        # 读取文件内容
        file_content = file.read()
        file.seek(0)

        return upload_file_to_storage(order, file_content, filename, content_type)

    except Exception as e:
        logger.error(f"上传供应商确认回执失败: {str(e)}")
        return None


def generate_order_number():
    """生成采购订单号 格式: CG-YYMM-XXX"""
    from app.models.inventory import PurchaseOrder

    today = datetime.now()
    prefix = f"CG-{today.strftime('%y%m')}"

    latest_order = PurchaseOrder.query.filter(
        PurchaseOrder.order_number.like(f"{prefix}%")
    ).order_by(PurchaseOrder.order_number.desc()).first()

    if latest_order:
        try:
            latest_num = int(latest_order.order_number.split('-')[-1])
            new_num = latest_num + 1
        except (ValueError, IndexError):
            new_num = 1
    else:
        new_num = 1

    return f"{prefix}-{new_num:03d}"


def parse_date(date_str):
    """解析日期字符串"""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return None


def get_order_statistics():
    """
    获取订单统计数据（优化版：单次分组查询）
    """
    from app.models.inventory import PurchaseOrder
    from sqlalchemy import func, case

    # 使用单次查询获取所有状态统计
    stats_query = db.session.query(
        func.count(PurchaseOrder.id).label('total'),
        func.sum(case((PurchaseOrder.status == 'draft', 1), else_=0)).label('draft'),
        func.sum(case((PurchaseOrder.status == 'pending', 1), else_=0)).label('pending'),
        func.sum(case((PurchaseOrder.status == 'approved', 1), else_=0)).label('approved'),
        func.sum(case((PurchaseOrder.status == 'confirmed', 1), else_=0)).label('confirmed'),
        func.sum(case((PurchaseOrder.status == 'producing', 1), else_=0)).label('producing'),
        func.sum(case((PurchaseOrder.status == 'tested', 1), else_=0)).label('tested'),
        func.sum(case((PurchaseOrder.status == 'shipped', 1), else_=0)).label('shipped'),
        func.sum(case((PurchaseOrder.status == 'stored', 1), else_=0)).label('stored'),
        func.sum(case((PurchaseOrder.status == 'completed', 1), else_=0)).label('completed'),
        func.sum(case((PurchaseOrder.is_overdue == True, 1), else_=0)).label('overdue')
    ).first()

    return {
        'total': stats_query.total or 0,
        'draft': stats_query.draft or 0,
        'pending': stats_query.pending or 0,
        'approved': stats_query.approved or 0,
        'confirmed': stats_query.confirmed or 0,
        'producing': stats_query.producing or 0,
        'tested': stats_query.tested or 0,
        'shipped': stats_query.shipped or 0,
        'stored': stats_query.stored or 0,
        'completed': stats_query.completed or 0,
        'overdue': stats_query.overdue or 0,
    }


def is_supply_chain_user(user):
    """判断用户是否是供应链人员"""
    if user.role == 'admin':
        return True
    # 检查用户角色
    if user.role in ['supply_chain', 'procurement']:
        return True
    # 检查用户部门
    if hasattr(user, 'department') and user.department:
        dept_name = user.department.name if hasattr(user.department, 'name') else str(user.department)
        if '供应链' in dept_name or '采购' in dept_name or 'supply' in dept_name.lower():
            return True
    return False


def get_condition_label(condition):
    """获取条件的中文标签"""
    labels = {
        'factory_test_passed': '工厂测试通过',
        'test_report_uploaded': '测试报告已上传',
        'test_signed': '测试报告已签证',
        'fat_completed_if_required': 'FAT完成（如需要）'
    }
    return labels.get(condition, condition)
