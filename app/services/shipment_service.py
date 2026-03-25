# -*- coding: utf-8 -*-
"""
发货管理服务层
处理发货单的创建、发货确认、签收等业务逻辑
"""
from datetime import datetime
from decimal import Decimal
import json
from app import db
from app.models.shipment import Shipment, ShipmentDetail
from app.models.sales_order import SalesOrder, SalesOrderDetail
import logging

logger = logging.getLogger(__name__)


class ShipmentService:
    """发货管理服务类"""

    @staticmethod
    def generate_shipment_number():
        """
        生成发货单号
        格式: SHP202501-001
        """
        today = datetime.now()
        prefix = f"SHP{today.strftime('%Y%m')}"

        latest = Shipment.query.filter(
            Shipment.shipment_number.like(f"{prefix}%")
        ).order_by(Shipment.shipment_number.desc()).first()

        if latest:
            try:
                latest_num = int(latest.shipment_number.split('-')[-1])
                new_num = latest_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1

        return f"{prefix}-{new_num:03d}"

    @staticmethod
    def create_shipment(sales_order_id, shipment_data, details, current_user_id):
        """
        创建发货单

        Args:
            sales_order_id: 客户订单ID
            shipment_data: 发货信息字典 {
                'carrier': str (可选),
                'tracking_number': str (可选),
                'shipping_method': str (可选),
                'ship_date': datetime (可选),
                'expected_arrival': datetime (可选),
                'freight_cost': Decimal (可选),
                'freight_payer': str (可选),
                'ship_from': str (可选),
                'ship_to': str (可选),
                'contact_name': str (可选),
                'contact_phone': str (可选),
                'total_packages': int (可选),
                'total_weight': Decimal (可选),
                'notes': str (可选)
            }
            details: 发货明细列表 [{
                'sales_order_detail_id': int,
                'quantity': int,
                'serial_numbers': list (可选)
            }]
            current_user_id: 当前用户ID

        Returns:
            (Shipment, error_message) - 成功返回(发货单对象, None)，失败返回(None, 错误信息)
        """
        try:
            # 获取客户订单
            sales_order = SalesOrder.query.get(sales_order_id)
            if not sales_order:
                return None, '客户订单不存在'

            # 验证订单状态
            if sales_order.status not in ['confirmed', 'preparing', 'shipped']:
                return None, f'订单状态 {sales_order.status} 不允许发货'

            # 验证明细
            if not details:
                return None, '请选择要发货的产品'

            # 创建发货单
            shipment = Shipment(
                shipment_number=ShipmentService.generate_shipment_number(),
                sales_order_id=sales_order_id,
                carrier=shipment_data.get('carrier'),
                tracking_number=shipment_data.get('tracking_number'),
                shipping_method=shipment_data.get('shipping_method'),
                ship_date=shipment_data.get('ship_date'),
                expected_arrival=shipment_data.get('expected_arrival'),
                freight_cost=shipment_data.get('freight_cost'),
                freight_payer=shipment_data.get('freight_payer'),
                ship_from=shipment_data.get('ship_from'),
                ship_to=shipment_data.get('ship_to') or sales_order.delivery_address,
                contact_name=shipment_data.get('contact_name') or sales_order.delivery_contact,
                contact_phone=shipment_data.get('contact_phone') or sales_order.delivery_phone,
                contact_email=sales_order.delivery_email,
                total_packages=shipment_data.get('total_packages', 1),
                total_weight=shipment_data.get('total_weight'),
                notes=shipment_data.get('notes'),
                status='pending',
                created_by_id=current_user_id
            )

            db.session.add(shipment)
            db.session.flush()

            # 创建发货明细
            for item in details:
                so_detail_id = item.get('sales_order_detail_id')
                quantity = item.get('quantity', 0)

                if not so_detail_id or quantity <= 0:
                    continue

                so_detail = SalesOrderDetail.query.get(so_detail_id)
                if not so_detail:
                    continue

                # 检查可发货数量
                remaining = so_detail.remaining_to_ship
                if quantity > remaining:
                    return None, f'{so_detail.product_name} 可发货数量不足，剩余 {remaining}'

                # 处理序列号
                serial_numbers = item.get('serial_numbers', [])
                serial_numbers_json = json.dumps(serial_numbers) if serial_numbers else None

                shipment_detail = ShipmentDetail(
                    shipment_id=shipment.id,
                    sales_order_detail_id=so_detail_id,
                    product_id=so_detail.product_id,
                    product_name=so_detail.product_name,
                    product_model=so_detail.product_model,
                    specification=so_detail.specification,
                    quantity=quantity,
                    unit=so_detail.unit,
                    serial_numbers=serial_numbers_json,
                    status='pending'
                )
                db.session.add(shipment_detail)

            db.session.commit()
            logger.info(f"创建发货单 {shipment.shipment_number}，关联订单 {sales_order.order_number}")
            return shipment, None

        except Exception as e:
            db.session.rollback()
            logger.error(f"创建发货单失败: {str(e)}")
            return None, f'创建失败: {str(e)}'

    @staticmethod
    def confirm_shipment(shipment_id, current_user_id, ship_date=None):
        """
        确认发货 pending -> shipped

        Args:
            shipment_id: 发货单ID
            current_user_id: 当前用户ID
            ship_date: 发货日期（可选，默认当前时间）

        Returns:
            (success, message)
        """
        try:
            shipment = Shipment.query.get(shipment_id)
            if not shipment:
                return False, '发货单不存在'

            if shipment.status != 'pending':
                return False, f'当前状态 {shipment.status} 不允许确认发货'

            # 更新发货单状态
            shipment.status = 'shipped'
            shipment.ship_date = ship_date or datetime.now()
            shipment.updated_at = datetime.now()

            # 更新发货明细状态
            for detail in shipment.details:
                detail.status = 'shipped'

            # 更新客户订单明细的发货数量
            ShipmentService._update_order_shipped_quantity(shipment)

            # 更新客户订单状态
            sales_order = shipment.sales_order
            if sales_order.status in ['confirmed', 'preparing']:
                # 检查是否全部发货
                if sales_order.shipped_quantity >= sales_order.total_quantity:
                    sales_order.status = 'shipped'
                else:
                    sales_order.status = 'preparing'  # 部分发货

            db.session.commit()
            logger.info(f"发货单 {shipment.shipment_number} 已发货")
            return True, '发货成功'

        except Exception as e:
            db.session.rollback()
            logger.error(f"确认发货失败: {str(e)}")
            return False, f'操作失败: {str(e)}'

    @staticmethod
    def _update_order_shipped_quantity(shipment):
        """更新客户订单明细的发货数量"""
        for detail in shipment.details:
            if detail.sales_order_detail_id:
                so_detail = SalesOrderDetail.query.get(detail.sales_order_detail_id)
                if so_detail:
                    so_detail.shipped_quantity = (so_detail.shipped_quantity or 0) + detail.quantity
                    # 更新明细状态
                    if so_detail.shipped_quantity >= so_detail.quantity:
                        so_detail.status = 'shipped'
                    elif so_detail.shipped_quantity > 0:
                        so_detail.status = 'partial_shipped'

    @staticmethod
    def confirm_receipt(shipment_id, receipt_info, current_user_id):
        """
        确认签收

        Args:
            shipment_id: 发货单ID
            receipt_info: 签收信息 {
                'received_by': str,
                'received_date': datetime (可选),
                'received_notes': str (可选),
                'delivery_proof': list (可选，签收凭证文件)
            }
            current_user_id: 当前用户ID

        Returns:
            (success, message)
        """
        try:
            shipment = Shipment.query.get(shipment_id)
            if not shipment:
                return False, '发货单不存在'

            if shipment.status not in ['shipped', 'in_transit', 'delivered']:
                return False, f'当前状态 {shipment.status} 不允许签收'

            # 更新签收信息
            shipment.status = 'received'
            shipment.received_by = receipt_info.get('received_by')
            shipment.received_date = receipt_info.get('received_date') or datetime.now()
            shipment.received_notes = receipt_info.get('received_notes')
            shipment.actual_arrival = shipment.received_date

            # 处理签收凭证
            delivery_proof = receipt_info.get('delivery_proof', [])
            if delivery_proof:
                shipment.delivery_proof = json.dumps(delivery_proof)

            shipment.updated_at = datetime.now()

            # 更新发货明细状态和签收数量
            for detail in shipment.details:
                detail.received_quantity = detail.quantity
                detail.status = 'received'

            # 更新关联的序列号状态为 delivered
            try:
                if shipment.id:
                    from app.models.product_serial_number import ProductSerialNumber
                    sn_records = ProductSerialNumber.query.filter_by(shipment_id=shipment.id).all()
                    for sn in sn_records:
                        sn.status = 'delivered'
                    # 也检查明细中记录的序列号
                    for detail in shipment.details:
                        if detail.serial_numbers:
                            import json as _json
                            try:
                                sn_list = _json.loads(detail.serial_numbers)
                                for sn_str in sn_list:
                                    sn_record = ProductSerialNumber.query.filter_by(serial_number=sn_str).first()
                                    if sn_record and sn_record.status != 'delivered':
                                        sn_record.status = 'delivered'
                            except (ValueError, TypeError):
                                pass
            except Exception as sn_err:
                logger.warning(f"更新序列号签收状态失败（非致命）: {sn_err}")

            # 更新客户订单明细的签收数量
            ShipmentService._update_order_received_quantity(shipment)

            # 更新客户订单状态
            sales_order = shipment.sales_order
            if sales_order:
                if sales_order.received_quantity >= sales_order.total_quantity:
                    sales_order.status = 'delivered'
                    sales_order.received_by = shipment.received_by
                    sales_order.received_date = shipment.received_date

                # 代理商签收后，自动增加代理商仓库库存
                if sales_order.customer_id:
                    from app.utils.inventory_helpers import update_inventory
                    for detail in shipment.details:
                        if detail.received_quantity and detail.received_quantity > 0:
                            update_inventory(
                                company_id=sales_order.customer_id,
                                product_id=detail.product_id,
                                quantity_change=detail.received_quantity,
                                transaction_type='in',
                                reference_type='shipment',
                                reference_id=shipment.id,
                                description=f'发货单 {shipment.shipment_number} 签收入库',
                                user_id=current_user_id
                            )

            db.session.commit()
            logger.info(f"发货单 {shipment.shipment_number} 已签收")
            return True, '签收成功'

        except Exception as e:
            db.session.rollback()
            logger.error(f"确认签收失败: {str(e)}")
            return False, f'操作失败: {str(e)}'

    @staticmethod
    def _update_order_received_quantity(shipment):
        """更新客户订单明细的签收数量"""
        for detail in shipment.details:
            if detail.sales_order_detail_id:
                so_detail = SalesOrderDetail.query.get(detail.sales_order_detail_id)
                if so_detail:
                    so_detail.received_quantity = (so_detail.received_quantity or 0) + detail.received_quantity
                    # 更新明细状态
                    if so_detail.received_quantity >= so_detail.quantity:
                        so_detail.status = 'received'
                    elif so_detail.received_quantity > 0:
                        so_detail.status = 'partial_received'

    @staticmethod
    def update_tracking(shipment_id, tracking_info, current_user_id):
        """
        更新物流跟踪信息

        Args:
            shipment_id: 发货单ID
            tracking_info: 物流信息 {
                'carrier': str (可选),
                'tracking_number': str (可选),
                'status': str (可选),
                'expected_arrival': datetime (可选)
            }
            current_user_id: 当前用户ID

        Returns:
            (success, message)
        """
        try:
            shipment = Shipment.query.get(shipment_id)
            if not shipment:
                return False, '发货单不存在'

            if 'carrier' in tracking_info:
                shipment.carrier = tracking_info['carrier']
            if 'tracking_number' in tracking_info:
                shipment.tracking_number = tracking_info['tracking_number']
            if 'status' in tracking_info and tracking_info['status'] in ['shipped', 'in_transit', 'delivered']:
                shipment.status = tracking_info['status']
            if 'expected_arrival' in tracking_info:
                shipment.expected_arrival = tracking_info['expected_arrival']

            shipment.updated_at = datetime.now()
            db.session.commit()

            return True, '物流信息已更新'

        except Exception as e:
            db.session.rollback()
            logger.error(f"更新物流信息失败: {str(e)}")
            return False, f'操作失败: {str(e)}'

    @staticmethod
    def get_tracking_timeline(shipment_id):
        """
        获取物流跟踪时间线

        Args:
            shipment_id: 发货单ID

        Returns:
            list 时间线数据
        """
        shipment = Shipment.query.get(shipment_id)
        if not shipment:
            return []

        timeline = []

        # 创建
        timeline.append({
            'title': '创建发货单',
            'time': shipment.created_at.strftime('%Y-%m-%d %H:%M') if shipment.created_at else '',
            'completed': True,
            'icon': 'add_box'
        })

        # 发货
        if shipment.ship_date or shipment.status in ['shipped', 'in_transit', 'delivered', 'received']:
            timeline.append({
                'title': '已发货',
                'time': shipment.ship_date.strftime('%Y-%m-%d %H:%M') if shipment.ship_date else '',
                'completed': True,
                'icon': 'local_shipping'
            })
        else:
            timeline.append({
                'title': '待发货',
                'time': '',
                'completed': False,
                'icon': 'local_shipping'
            })

        # 运输中
        if shipment.status in ['in_transit', 'delivered', 'received']:
            timeline.append({
                'title': '运输中',
                'time': '',
                'completed': True,
                'icon': 'flight_takeoff'
            })
        elif shipment.status == 'shipped':
            timeline.append({
                'title': '运输中',
                'time': '',
                'completed': False,
                'icon': 'flight_takeoff'
            })

        # 送达
        if shipment.status in ['delivered', 'received']:
            timeline.append({
                'title': '已送达',
                'time': shipment.actual_arrival.strftime('%Y-%m-%d %H:%M') if shipment.actual_arrival else '',
                'completed': True,
                'icon': 'where_to_vote'
            })
        elif shipment.status in ['shipped', 'in_transit']:
            timeline.append({
                'title': '待送达',
                'time': f'预计 {shipment.expected_arrival.strftime("%Y-%m-%d")}' if shipment.expected_arrival else '',
                'completed': False,
                'icon': 'where_to_vote'
            })

        # 签收
        if shipment.status == 'received':
            timeline.append({
                'title': '已签收',
                'time': shipment.received_date.strftime('%Y-%m-%d %H:%M') if shipment.received_date else '',
                'completed': True,
                'icon': 'check_circle',
                'detail': f'签收人: {shipment.received_by}' if shipment.received_by else ''
            })
        elif shipment.status in ['shipped', 'in_transit', 'delivered']:
            timeline.append({
                'title': '待签收',
                'time': '',
                'completed': False,
                'icon': 'check_circle'
            })

        return timeline

    @staticmethod
    def get_shipment_statistics(base_query=None, user=None):
        """
        获取发货统计数据（单次 case 聚合）

        Args:
            base_query: 已构建的基础查询
            user: 当前用户

        Returns:
            dict 统计数据
        """
        from sqlalchemy import case, func

        if base_query is None:
            base_query = Shipment.query

        result = base_query.with_entities(
            func.count(Shipment.id).label('total'),
            func.count(case((Shipment.status == 'pending', Shipment.id))).label('pending'),
            func.count(case((Shipment.status == 'shipped', Shipment.id))).label('shipped'),
            func.count(case((Shipment.status == 'in_transit', Shipment.id))).label('in_transit'),
            func.count(case((Shipment.status == 'delivered', Shipment.id))).label('delivered'),
            func.count(case((Shipment.status == 'received', Shipment.id))).label('received'),
            func.count(case((Shipment.status == 'exception', Shipment.id))).label('exception'),
        ).first()

        return {
            'total': result.total or 0,
            'pending': result.pending or 0,
            'shipped': result.shipped or 0,
            'in_transit': result.in_transit or 0,
            'delivered': result.delivered or 0,
            'received': result.received or 0,
            'exception': result.exception or 0,
        }
