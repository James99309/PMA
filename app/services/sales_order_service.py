# -*- coding: utf-8 -*-
"""
客户订单服务层
处理销售订单的创建、状态流转等业务逻辑
"""
from datetime import datetime
from decimal import Decimal
from app import db
from app.models.sales_order import SalesOrder, SalesOrderDetail
from app.models.pricing_order import PricingOrder, PricingOrderDetail
from app.models.product import Product
import logging

logger = logging.getLogger(__name__)


class SalesOrderService:
    """客户订单服务类"""

    @staticmethod
    def generate_order_number():
        """生成客户订单号 SO<YYYYMM>-NNN — 走统一生成器"""
        from app.utils.doc_number import generate_doc_number
        return generate_doc_number('SO', SalesOrder)

    @staticmethod
    def create_from_pricing_order(pricing_order_id, delivery_info, current_user_id):
        """
        从批价单创建客户订单

        Args:
            pricing_order_id: 批价单ID
            delivery_info: 交付信息字典 {
                'delivery_date': datetime (可选),
                'delivery_address': str (可选),
                'delivery_contact': str (可选),
                'delivery_phone': str (可选),
                'delivery_email': str (可选),
                'shipping_method': str (可选),
                'freight_terms': str (可选),
                'incoterms': str (可选),
                'notes': str (可选)
            }
            current_user_id: 当前用户ID

        Returns:
            (SalesOrder, error_message) - 成功返回(订单对象, None)，失败返回(None, 错误信息)
        """
        try:
            # 获取批价单
            pricing_order = PricingOrder.query.get(pricing_order_id)
            if not pricing_order:
                return None, '批价单不存在'

            # 验证批价单状态
            if pricing_order.status != 'approved':
                return None, '只有已批准的批价单才能创建客户订单'

            # 检查是否已创建过客户订单
            existing = SalesOrder.query.filter_by(pricing_order_id=pricing_order_id).first()
            if existing:
                return None, f'该批价单已创建客户订单 {existing.order_number}'

            # 获取批价单明细
            pricing_details = PricingOrderDetail.query.filter_by(
                pricing_order_id=pricing_order_id
            ).all()

            if not pricing_details:
                return None, '批价单没有明细数据'

            # 确定客户ID (优先经销商，其次分销商)
            customer_id = pricing_order.dealer_id or pricing_order.distributor_id
            if not customer_id:
                return None, '批价单未关联客户'

            # 创建客户订单
            sales_order = SalesOrder(
                order_number=SalesOrderService.generate_order_number(),
                pricing_order_id=pricing_order_id,
                project_id=pricing_order.project_id,
                customer_id=customer_id,
                currency=pricing_order.currency or 'CNY',
                status='draft',
                created_by_id=current_user_id,
                # 交付信息
                delivery_date=delivery_info.get('delivery_date'),
                delivery_address=delivery_info.get('delivery_address'),
                delivery_contact=delivery_info.get('delivery_contact'),
                delivery_phone=delivery_info.get('delivery_phone'),
                delivery_email=delivery_info.get('delivery_email'),
                shipping_method=delivery_info.get('shipping_method'),
                freight_terms=delivery_info.get('freight_terms'),
                incoterms=delivery_info.get('incoterms'),
                notes=delivery_info.get('notes')
            )

            db.session.add(sales_order)
            db.session.flush()  # 获取ID

            # 创建订单明细
            total_amount = Decimal('0')
            total_quantity = 0

            for pd in pricing_details:
                # 尝试查找产品ID
                product_id = SalesOrderService._find_product_id(pd)

                # MN 编码:优先用批价单明细自带,fallback 查产品库
                _mn = (getattr(pd, 'product_mn', None) or '').strip()
                if not _mn and product_id:
                    from app.models.product import Product
                    _p = Product.query.get(product_id)
                    if _p:
                        _mn = (_p.product_mn or '').strip()

                detail = SalesOrderDetail(
                    sales_order_id=sales_order.id,
                    pricing_detail_id=pd.id,
                    product_id=product_id,
                    product_name=pd.product_name,
                    product_model=pd.product_model,
                    product_mn=_mn or None,
                    specification=pd.product_desc,
                    quantity=pd.quantity,
                    unit=pd.unit,
                    unit_price=Decimal(str(pd.unit_price)) if pd.unit_price else Decimal('0'),
                    discount=Decimal(str(pd.discount_rate)) if pd.discount_rate else Decimal('1'),
                    total_price=Decimal(str(pd.total_price)) if pd.total_price else Decimal('0'),
                    status='pending'
                )
                db.session.add(detail)

                total_amount += detail.total_price
                total_quantity += detail.quantity

            # 更新订单汇总
            sales_order.total_amount = total_amount
            sales_order.total_quantity = total_quantity

            db.session.commit()
            logger.info(f"从批价单 {pricing_order.order_number} 创建客户订单 {sales_order.order_number}")
            return sales_order, None

        except Exception as e:
            db.session.rollback()
            logger.error(f"创建客户订单失败: {str(e)}")
            return None, f'创建失败: {str(e)}'

    @staticmethod
    def _find_product_id(pricing_detail):
        """
        根据批价单明细查找产品ID

        尝试多种方式匹配：
        1. 通过报价单明细ID查找
        2. 通过MN号查找
        3. 通过产品名称+型号查找
        """
        # 方法1: 通过报价单明细ID
        if pricing_detail.source_quotation_detail_id:
            from app.models.quotation import QuotationDetail
            qd = QuotationDetail.query.get(pricing_detail.source_quotation_detail_id)
            if qd and qd.product_id:
                return qd.product_id

        # 方法2: 通过MN号
        if pricing_detail.product_mn:
            product = Product.query.filter_by(mn=pricing_detail.product_mn).first()
            if product:
                return product.id

        # 方法3: 通过产品名称+型号
        if pricing_detail.product_name:
            query = Product.query.filter_by(name=pricing_detail.product_name)
            if pricing_detail.product_model:
                query = query.filter_by(model=pricing_detail.product_model)
            product = query.first()
            if product:
                return product.id

        # 找不到则返回None，后续可能需要手动关联
        logger.warning(f"无法找到产品ID: {pricing_detail.product_name} / {pricing_detail.product_model}")
        return None

    @staticmethod
    def confirm_order(order_id, current_user_id):
        """
        确认订单 draft -> confirmed

        Args:
            order_id: 订单ID
            current_user_id: 当前用户ID

        Returns:
            (success, message)
        """
        try:
            order = SalesOrder.query.get(order_id)
            if not order:
                return False, '订单不存在'

            if order.status != 'draft':
                return False, f'当前状态 {order.status} 不允许确认'

            order.status = 'confirmed'
            order.updated_at = datetime.now()
            db.session.commit()

            logger.info(f"客户订单 {order.order_number} 已确认")
            return True, '订单已确认'

        except Exception as e:
            db.session.rollback()
            logger.error(f"确认订单失败: {str(e)}")
            return False, f'操作失败: {str(e)}'

    @staticmethod
    def is_referenced_by_po(order):
        """订单的任一明细被 PO 引用过 → True。草稿态不应有引用,确认后才可能。"""
        return any(getattr(d, 'purchase_details', None) for d in order.details)

    @staticmethod
    def cancel_order(order_id, current_user_id, reason=None):
        """
        取消订单(只保留记录,标记 cancelled)。草稿态请走 delete_order。

        约束:
          - 草稿不能取消(应该删除)
          - 已发货(shipped_quantity>0)不能取消
          - 已被关联 PO 引用 → 不能取消(走 PO 链路逆向处理)
          - 已完成/已取消 不能取消
        """
        try:
            order = SalesOrder.query.get(order_id)
            if not order:
                return False, '订单不存在'

            if order.status == 'draft':
                return False, '草稿订单请使用删除,而非取消'

            if order.status in ('cancelled', 'completed'):
                return False, f'当前状态 {order.status} 不允许取消'

            if order.shipped_quantity and order.shipped_quantity > 0:
                return False, '已有发货记录,不能取消'

            if SalesOrderService.is_referenced_by_po(order):
                return False, '订单已生成关联采购单,不能取消'

            order.status = 'cancelled'
            if reason:
                order.notes = f"{order.notes or ''}\n取消原因: {reason}".strip()
            order.updated_at = datetime.now()
            db.session.commit()

            logger.info(f"客户订单 {order.order_number} 已取消")
            return True, '订单已取消'

        except Exception as e:
            db.session.rollback()
            logger.error(f"取消订单失败: {str(e)}")
            return False, f'操作失败: {str(e)}'

    @staticmethod
    def delete_order(order_id, current_user_id):
        """
        删除草稿订单(物理删除 SalesOrder + 级联明细)。仅 draft 可删。
        """
        try:
            order = SalesOrder.query.get(order_id)
            if not order:
                return False, '订单不存在'

            if order.status != 'draft':
                return False, '仅草稿订单可以删除,非草稿订单请使用取消'

            # 双重保险:草稿理论上不会被 PO 引用,但万一异常数据也拦一道
            if SalesOrderService.is_referenced_by_po(order):
                return False, '订单已被采购单引用,不能删除'

            order_number = order.order_number
            # 物理删除明细
            SalesOrderDetail.query.filter_by(sales_order_id=order.id).delete()
            db.session.delete(order)
            db.session.commit()

            logger.info(f"客户订单 {order_number} 已删除(物理)")
            return True, '订单已删除'

        except Exception as e:
            db.session.rollback()
            logger.error(f"删除订单失败: {str(e)}")
            return False, f'操作失败: {str(e)}'

    @staticmethod
    def update_delivery_info(order_id, delivery_info, current_user_id):
        """
        更新交付信息

        Args:
            order_id: 订单ID
            delivery_info: 交付信息字典
            current_user_id: 当前用户ID

        Returns:
            (success, message)
        """
        try:
            order = SalesOrder.query.get(order_id)
            if not order:
                return False, '订单不存在'

            # 更新字段
            if 'delivery_date' in delivery_info:
                order.delivery_date = delivery_info['delivery_date']
            if 'delivery_address' in delivery_info:
                order.delivery_address = delivery_info['delivery_address']
            if 'delivery_contact' in delivery_info:
                order.delivery_contact = delivery_info['delivery_contact']
            if 'delivery_phone' in delivery_info:
                order.delivery_phone = delivery_info['delivery_phone']
            if 'delivery_email' in delivery_info:
                order.delivery_email = delivery_info['delivery_email']
            if 'shipping_method' in delivery_info:
                order.shipping_method = delivery_info['shipping_method']
            if 'freight_terms' in delivery_info:
                order.freight_terms = delivery_info['freight_terms']
            if 'incoterms' in delivery_info:
                order.incoterms = delivery_info['incoterms']

            order.updated_at = datetime.now()
            db.session.commit()

            return True, '交付信息已更新'

        except Exception as e:
            db.session.rollback()
            logger.error(f"更新交付信息失败: {str(e)}")
            return False, f'操作失败: {str(e)}'

    @staticmethod
    def update_order_status(order_id, new_status):
        """
        更新订单状态

        Args:
            order_id: 订单ID
            new_status: 新状态

        Returns:
            (success, message)
        """
        valid_statuses = ['draft', 'confirmed', 'preparing', 'shipped', 'delivered', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            return False, f'无效的状态: {new_status}'

        try:
            order = SalesOrder.query.get(order_id)
            if not order:
                return False, '订单不存在'

            order.status = new_status
            order.updated_at = datetime.now()
            db.session.commit()

            return True, f'状态已更新为 {new_status}'

        except Exception as e:
            db.session.rollback()
            logger.error(f"更新订单状态失败: {str(e)}")
            return False, f'操作失败: {str(e)}'

    @staticmethod
    def get_order_statistics(base_query=None, user=None):
        """
        获取订单统计数据（单次 case 聚合）

        Args:
            base_query: 已构建的基础查询（避免重复 get_viewable_data）
            user: 当前用户（用于权限过滤，base_query 为空时使用）

        Returns:
            dict 统计数据
        """
        from sqlalchemy import case, func

        if base_query is None:
            from app.utils.access_control import get_viewable_data
            base_query = get_viewable_data(SalesOrder, user) if user else SalesOrder.query

        result = base_query.with_entities(
            func.count(SalesOrder.id).label('total'),
            func.count(case((SalesOrder.status == 'draft', SalesOrder.id))).label('draft'),
            func.count(case((SalesOrder.status == 'confirmed', SalesOrder.id))).label('confirmed'),
            func.count(case((SalesOrder.status == 'preparing', SalesOrder.id))).label('preparing'),
            func.count(case((SalesOrder.status == 'shipped', SalesOrder.id))).label('shipped'),
            func.count(case((SalesOrder.status == 'delivered', SalesOrder.id))).label('delivered'),
            func.count(case((SalesOrder.status == 'completed', SalesOrder.id))).label('completed'),
            func.count(case((SalesOrder.status == 'cancelled', SalesOrder.id))).label('cancelled'),
        ).first()

        return {
            'total': result.total or 0,
            'draft': result.draft or 0,
            'confirmed': result.confirmed or 0,
            'preparing': result.preparing or 0,
            'shipped': result.shipped or 0,
            'delivered': result.delivered or 0,
            'completed': result.completed or 0,
            'cancelled': result.cancelled or 0,
        }
