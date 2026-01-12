# -*- coding: utf-8 -*-
"""
序列号管理服务层
处理序列号的录入、入库、出库和全生命周期追溯
"""
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from app import db
from app.models.product_serial_number import ProductSerialNumber, SerialNumberHistory
from app.models.product import Product
from app.models.inventory import Inventory
import logging

logger = logging.getLogger(__name__)


class ProductSNService:
    """序列号服务类"""

    # 状态定义
    STATUS_REGISTERED = 'registered'  # 已登记
    STATUS_IN_STOCK = 'in_stock'      # 库存中
    STATUS_RESERVED = 'reserved'       # 已预留
    STATUS_SHIPPED = 'shipped'         # 已发货
    STATUS_DELIVERED = 'delivered'     # 已交付
    STATUS_RETURNED = 'returned'       # 已退回
    STATUS_DEFECTIVE = 'defective'     # 故障

    @staticmethod
    def get_statistics() -> Dict:
        """获取序列号统计数据"""
        total = ProductSerialNumber.query.count()
        registered = ProductSerialNumber.query.filter_by(status='registered').count()
        in_stock = ProductSerialNumber.query.filter_by(status='in_stock').count()
        reserved = ProductSerialNumber.query.filter_by(status='reserved').count()
        shipped = ProductSerialNumber.query.filter_by(status='shipped').count()
        delivered = ProductSerialNumber.query.filter_by(status='delivered').count()

        return {
            'total': total,
            'registered': registered,
            'in_stock': in_stock,
            'reserved': reserved,
            'shipped': shipped,
            'delivered': delivered
        }

    @staticmethod
    def create_serial_number(
        serial_number: str,
        product_id: int,
        user_id: int,
        purchase_order_id: Optional[int] = None,
        purchase_detail_id: Optional[int] = None,
        batch_number: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Tuple[Optional[ProductSerialNumber], Optional[str]]:
        """
        创建单个序列号

        Args:
            serial_number: 序列号
            product_id: 产品ID
            user_id: 操作用户ID
            purchase_order_id: 采购订单ID（可选）
            purchase_detail_id: 采购明细ID（可选）
            batch_number: 批次号（可选）
            notes: 备注（可选）

        Returns:
            (序列号对象, 错误消息)
        """
        try:
            # 检查序列号是否已存在
            existing = ProductSerialNumber.query.filter_by(serial_number=serial_number).first()
            if existing:
                return None, f'序列号 {serial_number} 已存在'

            # 检查产品是否存在
            product = Product.query.get(product_id)
            if not product:
                return None, '产品不存在'

            # 创建序列号
            sn = ProductSerialNumber(
                serial_number=serial_number,
                product_id=product_id,
                purchase_order_id=purchase_order_id,
                purchase_detail_id=purchase_detail_id,
                batch_number=batch_number,
                status='registered',
                notes=notes,
                created_by_id=user_id
            )
            db.session.add(sn)
            db.session.flush()

            # 记录历史
            history = SerialNumberHistory(
                serial_number_id=sn.id,
                action='register',
                status_before=None,
                status_after='registered',
                description='序列号登记',
                operated_by_id=user_id
            )
            db.session.add(history)
            db.session.commit()

            return sn, None

        except Exception as e:
            db.session.rollback()
            logger.error(f"创建序列号失败: {str(e)}")
            return None, f'创建失败: {str(e)}'

    @staticmethod
    def batch_create_serial_numbers(
        serial_numbers_data: List[Dict],
        user_id: int
    ) -> Tuple[int, int, List[Dict]]:
        """
        批量创建序列号

        Args:
            serial_numbers_data: 序列号数据列表 [{serial_number, product_id, batch_number, ...}]
            user_id: 操作用户ID

        Returns:
            (成功数量, 失败数量, 错误列表)
        """
        success_count = 0
        fail_count = 0
        errors = []

        for i, data in enumerate(serial_numbers_data, 1):
            serial_number = data.get('serial_number', '').strip()
            product_id = data.get('product_id')

            if not serial_number:
                errors.append({'row': i, 'error': '序列号为空'})
                fail_count += 1
                continue

            if not product_id:
                errors.append({'row': i, 'serial_number': serial_number, 'error': '产品ID为空'})
                fail_count += 1
                continue

            sn, error = ProductSNService.create_serial_number(
                serial_number=serial_number,
                product_id=product_id,
                user_id=user_id,
                purchase_order_id=data.get('purchase_order_id'),
                purchase_detail_id=data.get('purchase_detail_id'),
                batch_number=data.get('batch_number'),
                notes=data.get('notes')
            )

            if error:
                errors.append({'row': i, 'serial_number': serial_number, 'error': error})
                fail_count += 1
            else:
                success_count += 1

        return success_count, fail_count, errors

    @staticmethod
    def stock_in(
        serial_number_id: int,
        warehouse_location: str,
        user_id: int,
        inventory_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        序列号入库

        Args:
            serial_number_id: 序列号ID
            warehouse_location: 仓库位置
            user_id: 操作用户ID
            inventory_id: 库存记录ID（可选）
            notes: 备注

        Returns:
            (是否成功, 消息)
        """
        try:
            sn = ProductSerialNumber.query.get(serial_number_id)
            if not sn:
                return False, '序列号不存在'

            if sn.status not in ['registered']:
                return False, f'当前状态 {sn.status_label} 不能入库'

            old_status = sn.status
            sn.status = 'in_stock'
            sn.warehouse_location = warehouse_location
            sn.warehouse_in_date = datetime.now()
            sn.received_by_id = user_id
            if inventory_id:
                sn.inventory_id = inventory_id

            # 记录历史
            history = SerialNumberHistory(
                serial_number_id=sn.id,
                action='stock_in',
                status_before=old_status,
                status_after='in_stock',
                location=warehouse_location,
                description=notes or '序列号入库',
                operated_by_id=user_id
            )
            db.session.add(history)
            db.session.commit()

            return True, '入库成功'

        except Exception as e:
            db.session.rollback()
            logger.error(f"序列号入库失败: {str(e)}")
            return False, f'入库失败: {str(e)}'

    @staticmethod
    def reserve(
        serial_number_id: int,
        sales_order_id: int,
        user_id: int
    ) -> Tuple[bool, str]:
        """
        预留序列号（关联到客户订单）

        Args:
            serial_number_id: 序列号ID
            sales_order_id: 客户订单ID
            user_id: 操作用户ID

        Returns:
            (是否成功, 消息)
        """
        try:
            sn = ProductSerialNumber.query.get(serial_number_id)
            if not sn:
                return False, '序列号不存在'

            if sn.status != 'in_stock':
                return False, f'当前状态 {sn.status_label} 不能预留'

            old_status = sn.status
            sn.status = 'reserved'
            sn.sales_order_id = sales_order_id

            # 记录历史
            history = SerialNumberHistory(
                serial_number_id=sn.id,
                action='reserve',
                status_before=old_status,
                status_after='reserved',
                reference_type='sales_order',
                reference_id=sales_order_id,
                description='预留给客户订单',
                operated_by_id=user_id
            )
            db.session.add(history)
            db.session.commit()

            return True, '预留成功'

        except Exception as e:
            db.session.rollback()
            logger.error(f"序列号预留失败: {str(e)}")
            return False, f'预留失败: {str(e)}'

    @staticmethod
    def ship(
        serial_number_id: int,
        shipment_id: int,
        destination: str,
        user_id: int
    ) -> Tuple[bool, str]:
        """
        序列号发货出库

        Args:
            serial_number_id: 序列号ID
            shipment_id: 发货单ID
            destination: 目的地
            user_id: 操作用户ID

        Returns:
            (是否成功, 消息)
        """
        try:
            sn = ProductSerialNumber.query.get(serial_number_id)
            if not sn:
                return False, '序列号不存在'

            if sn.status not in ['in_stock', 'reserved']:
                return False, f'当前状态 {sn.status_label} 不能发货'

            old_status = sn.status
            sn.status = 'shipped'
            sn.shipment_id = shipment_id
            sn.ship_out_date = datetime.now()
            sn.destination = destination
            sn.shipped_by_id = user_id

            # 记录历史
            history = SerialNumberHistory(
                serial_number_id=sn.id,
                action='ship',
                status_before=old_status,
                status_after='shipped',
                reference_type='shipment',
                reference_id=shipment_id,
                location=destination,
                description='发货出库',
                operated_by_id=user_id
            )
            db.session.add(history)
            db.session.commit()

            return True, '发货成功'

        except Exception as e:
            db.session.rollback()
            logger.error(f"序列号发货失败: {str(e)}")
            return False, f'发货失败: {str(e)}'

    @staticmethod
    def deliver(
        serial_number_id: int,
        customer_id: int,
        user_id: int,
        project_id: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        确认序列号交付

        Args:
            serial_number_id: 序列号ID
            customer_id: 客户ID
            user_id: 操作用户ID
            project_id: 项目ID（可选）

        Returns:
            (是否成功, 消息)
        """
        try:
            sn = ProductSerialNumber.query.get(serial_number_id)
            if not sn:
                return False, '序列号不存在'

            if sn.status != 'shipped':
                return False, f'当前状态 {sn.status_label} 不能确认交付'

            old_status = sn.status
            sn.status = 'delivered'
            sn.customer_id = customer_id
            if project_id:
                sn.project_id = project_id

            # 记录历史
            history = SerialNumberHistory(
                serial_number_id=sn.id,
                action='deliver',
                status_before=old_status,
                status_after='delivered',
                description='客户签收确认',
                operated_by_id=user_id
            )
            db.session.add(history)
            db.session.commit()

            return True, '交付确认成功'

        except Exception as e:
            db.session.rollback()
            logger.error(f"序列号交付确认失败: {str(e)}")
            return False, f'确认失败: {str(e)}'

    @staticmethod
    def get_timeline(serial_number_id: int) -> List[Dict]:
        """
        获取序列号生命周期时间线

        Args:
            serial_number_id: 序列号ID

        Returns:
            时间线列表
        """
        histories = SerialNumberHistory.query.filter_by(
            serial_number_id=serial_number_id
        ).order_by(SerialNumberHistory.operated_at.desc()).all()

        timeline = []
        for h in histories:
            timeline.append({
                'id': h.id,
                'action': h.action,
                'action_label': h.action_label,
                'status_before': h.status_before,
                'status_after': h.status_after,
                'description': h.description,
                'location': h.location,
                'reference_type': h.reference_type,
                'reference_id': h.reference_id,
                'operated_by': h.operated_by.real_name if h.operated_by else '',
                'operated_at': h.operated_at.strftime('%Y-%m-%d %H:%M') if h.operated_at else ''
            })

        return timeline

    @staticmethod
    def get_available_serial_numbers(
        product_id: int,
        status: str = 'in_stock',
        limit: int = 100
    ) -> List[Dict]:
        """
        获取可用的序列号列表（用于发货选择）

        Args:
            product_id: 产品ID
            status: 状态筛选
            limit: 返回数量限制

        Returns:
            序列号列表
        """
        query = ProductSerialNumber.query.filter_by(
            product_id=product_id,
            status=status
        ).order_by(ProductSerialNumber.created_at.desc()).limit(limit)

        return [{
            'id': sn.id,
            'serial_number': sn.serial_number,
            'batch_number': sn.batch_number,
            'warehouse_location': sn.warehouse_location,
            'warehouse_in_date': sn.formatted_warehouse_in_date
        } for sn in query.all()]

    @staticmethod
    def search_serial_number(query: str) -> Optional[ProductSerialNumber]:
        """
        搜索序列号

        Args:
            query: 搜索关键词

        Returns:
            序列号对象
        """
        return ProductSerialNumber.query.filter(
            ProductSerialNumber.serial_number.ilike(f'%{query}%')
        ).first()

    @staticmethod
    def validate_import_data(data: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        验证导入数据

        Args:
            data: 导入数据列表

        Returns:
            (有效数据, 重复数据, 错误数据)
        """
        valid = []
        duplicates = []
        errors = []

        existing_sns = set()
        db_sns = set(sn.serial_number for sn in ProductSerialNumber.query.with_entities(
            ProductSerialNumber.serial_number
        ).all())

        for i, row in enumerate(data, 1):
            sn = row.get('serial_number', '').strip()
            product_id = row.get('product_id')

            if not sn:
                errors.append({**row, 'row': i, 'error': '序列号为空'})
                continue

            if not product_id:
                errors.append({**row, 'row': i, 'error': '产品ID为空'})
                continue

            # 检查数据库重复
            if sn in db_sns:
                duplicates.append({**row, 'row': i, 'error': '数据库已存在'})
                continue

            # 检查文件内重复
            if sn in existing_sns:
                duplicates.append({**row, 'row': i, 'error': '文件内重复'})
                continue

            existing_sns.add(sn)
            valid.append({**row, 'row': i})

        return valid, duplicates, errors
