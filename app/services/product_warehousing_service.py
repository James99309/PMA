#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
研发产品入库服务

负责将研发库（dev_products）中的产品转移到产品库（products）
包含MN编号重复检测、规格数据复制等核心逻辑
"""
from datetime import datetime
from flask import current_app
from app import db
from app.models.product import Product
from app.models.product_spec import ProductSpec
from app.models.dev_product import DevProduct, DevProductSpec


class ProductWarehousingService:
    """研发产品入库服务"""

    def transfer_dev_product_to_production(self, dev_product_id, approver_id):
        """将研发产品转移到产品库

        完整流程：
        1. 验证研发产品存在
        2. 检查MN编号重复
        3. 创建Product记录（设置来源标记）
        4. 复制dev_product_specs → product_specs
        5. 更新研发产品状态为"已入库"

        Args:
            dev_product_id (int): 研发产品ID
            approver_id (int): 审批人ID

        Returns:
            tuple: (success: bool, message: str, product_id: int or None)
        """
        try:
            # 1. 获取研发产品
            dev_product = DevProduct.query.get(dev_product_id)
            if not dev_product:
                return False, "研发产品不存在", None

            current_app.logger.info(f"开始入库研发产品: ID={dev_product_id}, MN={dev_product.mn_code}, 型号={dev_product.model}")

            # 2. 检查MN编号重复
            if dev_product.mn_code:
                duplicate = Product.query.filter_by(
                    product_mn=dev_product.mn_code
                ).first()
                if duplicate:
                    error_msg = f"MN编号 {dev_product.mn_code} 已存在于产品库（产品ID: {duplicate.id}）"
                    current_app.logger.warning(error_msg)
                    return False, error_msg, None
            else:
                current_app.logger.warning(f"研发产品 {dev_product_id} 没有MN编号，将继续入库但建议补充MN")

            # 3. 创建产品记录
            product = Product(
                # 分类信息（外键）
                category_id=dev_product.category_id,
                subcategory_id=dev_product.subcategory_id,
                region_id=dev_product.region_id,

                # 基本信息
                product_mn=dev_product.mn_code,
                model=dev_product.model,
                brand='',  # 研发产品导入时品牌留空，待后续手动填写
                unit=dev_product.unit,
                retail_price=dev_product.retail_price,
                currency=dev_product.currency or 'CNY',
                status='active',  # 默认为生产中状态
                # 产品描述/规格说明（研发产品的description → 产品库的specification）
                specification=dev_product.description or '',

                # 文件路径
                image_path=dev_product.image_path,
                pdf_path=dev_product.pdf_path,

                # 产品来源标记（核心字段）
                source_type='from_dev',
                source_dev_product_id=dev_product.id,
                productized_at=datetime.now(),

                # MN编码锁定（防止修改）
                is_mn_locked=True,

                # 所有者（优先使用研发产品所有者，否则使用审批人）
                owner_id=dev_product.owner_id or approver_id,

                # 创建时间
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            db.session.add(product)
            db.session.flush()  # 获取product.id但不提交事务

            current_app.logger.info(f"创建产品记录成功: Product ID={product.id}")

            # 3.5. 复制规格数据（必须先复制规格，因为快照是从ProductSpec读取的）
            specs_count = self._copy_specs(dev_product, product)
            current_app.logger.info(f"复制规格数据: {specs_count} 条规格记录")

            # 3.6. 生成产品编码定义快照（使用通用函数）
            from app.utils.product_helpers import generate_product_snapshot
            snapshot = generate_product_snapshot(
                product=product,
                source="dev_product",
                dev_product=dev_product
            )
            if snapshot:
                product.code_definition_snapshot = snapshot
            else:
                current_app.logger.warning(f"编码快照生成失败或跳过（规格数据可能不完整）")

            # 5. 更新研发产品状态
            dev_product.status = '已入库'
            dev_product.updated_at = datetime.now()

            # 提交事务
            db.session.commit()

            success_msg = f"入库成功: 研发产品 #{dev_product_id} → 产品库 #{product.id}, 共复制 {specs_count} 条规格"
            current_app.logger.info(success_msg)

            return True, success_msg, product.id

        except Exception as e:
            db.session.rollback()
            error_msg = f"入库失败: {str(e)}"
            current_app.logger.error(error_msg)
            import traceback
            current_app.logger.error(traceback.format_exc())
            return False, error_msg, None

    def _copy_specs(self, dev_product, product):
        """复制规格数据

        将dev_product_specs表中的规格复制到product_specs表

        Args:
            dev_product: DevProduct对象
            product: Product对象

        Returns:
            int: 复制的规格数量
        """
        count = 0
        dev_specs = DevProductSpec.query.filter_by(dev_product_id=dev_product.id).all()

        for idx, dev_spec in enumerate(dev_specs):
            product_spec = ProductSpec(
                product_id=product.id,
                field_name=dev_spec.field_name,
                field_value=dev_spec.field_value,
                field_code=dev_spec.field_code,  # 保留编码用于MN生成
                display_order=idx,  # 按原顺序排列
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(product_spec)
            count += 1

        return count

    def check_mn_duplicate(self, mn_code, exclude_product_id=None):
        """检查MN编号是否重复

        Args:
            mn_code (str): MN编号
            exclude_product_id (int, optional): 排除的产品ID（用于编辑场景）

        Returns:
            dict: {'exists': bool, 'product': Product or None}
        """
        if not mn_code:
            return {'exists': False, 'product': None}

        query = Product.query.filter_by(product_mn=mn_code)
        if exclude_product_id:
            query = query.filter(Product.id != exclude_product_id)

        duplicate = query.first()

        return {
            'exists': duplicate is not None,
            'product': duplicate
        }

    def get_dev_products_ready_for_warehousing(self, user_id=None):
        """获取可入库的研发产品列表

        筛选条件：
        - 状态为"待入库"或其他允许入库的状态
        - 有MN编号（推荐但不强制）
        - 未被删除

        Args:
            user_id (int, optional): 用户ID，用于权限过滤

        Returns:
            list: DevProduct对象列表
        """
        query = DevProduct.query.filter(
            DevProduct.status.in_(['待入库', '已入库', '研发完成', '测试通过'])
        )

        # 如果指定了用户，只显示该用户的产品
        if user_id:
            query = query.filter(DevProduct.owner_id == user_id)

        products = query.order_by(DevProduct.updated_at.desc()).all()
        return products

    def update_dev_product_status(self, dev_product_id, new_status):
        """更新研发产品状态

        Args:
            dev_product_id (int): 研发产品ID
            new_status (str): 新状态

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            dev_product = DevProduct.query.get(dev_product_id)
            if not dev_product:
                return False, "研发产品不存在"

            old_status = dev_product.status
            dev_product.status = new_status
            dev_product.updated_at = datetime.now()

            db.session.commit()

            current_app.logger.info(f"更新研发产品状态: ID={dev_product_id}, {old_status} → {new_status}")
            return True, "状态更新成功"

        except Exception as e:
            db.session.rollback()
            error_msg = f"状态更新失败: {str(e)}"
            current_app.logger.error(error_msg)
            return False, error_msg
