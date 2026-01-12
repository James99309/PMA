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
        """
        生成客户订单号
        格式: SO202501-001
        """
        today = datetime.now()
        prefix = f"SO{today.strftime('%Y%m')}"

        latest_order = SalesOrder.query.filter(
            SalesOrder.order_number.like(f"{prefix}%")
        ).order_by(SalesOrder.order_number.desc()).first()

        if latest_order:
            try:
                latest_num = int(latest_order.order_number.split('-')[-1])
                new_num = latest_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1

        return f"{prefix}-{new_num:03d}"

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

                detail = SalesOrderDetail(
                    sales_order_id=sales_order.id,
                    pricing_detail_id=pd.id,
                    product_id=product_id,
                    product_name=pd.product_name,
                    product_model=pd.product_model,
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
    def cancel_order(order_id, current_user_id, reason=None):
        """
        取消订单

        Args:
            order_id: 订单ID
            current_user_id: 当前用户ID
            reason: 取消原因

        Returns:
            (success, message)
        """
        try:
            order = SalesOrder.query.get(order_id)
            if not order:
                return False, '订单不存在'

            # 只有草稿和已确认状态可以取消
            if order.status not in ['draft', 'confirmed']:
                return False, f'当前状态 {order.status} 不允许取消'

            # 检查是否有发货记录
            if order.shipped_quantity > 0:
                return False, '已有发货记录，不能取消'

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
    def get_order_statistics(user=None, filters=None):
        """
        获取订单统计数据

        Args:
            user: 当前用户（用于权限过滤）
            filters: 筛选条件

        Returns:
            dict 统计数据
        """
        from app.utils.access_control import get_viewable_data

        # 基础查询
        if user:
            query = get_viewable_data(SalesOrder, user)
        else:
            query = SalesOrder.query

        # 统计各状态数量
        stats = {
            'total': query.count(),
            'draft': query.filter(SalesOrder.status == 'draft').count(),
            'confirmed': query.filter(SalesOrder.status == 'confirmed').count(),
            'preparing': query.filter(SalesOrder.status == 'preparing').count(),
            'shipped': query.filter(SalesOrder.status == 'shipped').count(),
            'delivered': query.filter(SalesOrder.status == 'delivered').count(),
            'completed': query.filter(SalesOrder.status == 'completed').count(),
            'cancelled': query.filter(SalesOrder.status == 'cancelled').count()
        }

        return stats
