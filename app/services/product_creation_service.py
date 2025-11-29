"""
产品创建统一服务
提供research产品和standard产品的统一创建逻辑
"""
from flask import request, flash, redirect, url_for, current_app
from flask_login import current_user
from decimal import Decimal, InvalidOperation
from app.extensions import db
from app.models.dev_product import DevProduct
from app.models.product import Product
from app.models.product_code import ProductCategory, ProductSubcategory, ProductCodeField
from app.routes.product_management import save_dev_product_specs
from app.routes.product import save_product_specs


class ProductCreationService:
    """统一的产品创建服务（研发产品 + 标准产品）"""

    @staticmethod
    def save_product(product_type='research'):
        """
        统一保存产品逻辑

        Args:
            product_type (str): 产品类型 'research' 或 'standard'

        Returns:
            Flask Response: 重定向响应
        """
        try:
            # 1. 通用字段获取
            category_id = request.form.get('category_id')
            subcategory_id = request.form.get('subcategory_id')
            region_id = request.form.get('region_id') or None
            model = request.form.get('product_model')  # 表单字段名是product_model
            product_name = request.form.get('name') or None  # 独立的产品名称字段（研发产品）
            unit = request.form.get('unit') or ""
            retail_price = request.form.get('retail_price')
            currency = request.form.get('currency', 'CNY')
            description = request.form.get('description') or ""
            development_purpose = request.form.get('development_purpose') or ""
            mn_code = request.form.get('mn_code_preview', '').strip()

            # 2. 验证必填字段
            missing_fields = []
            if not category_id:
                missing_fields.append('产品分类')
            if not subcategory_id:
                missing_fields.append('产品系列')
            if not region_id:
                missing_fields.append('销售区域')
            # 研发产品必填产品名称
            if product_type == 'research' and not product_name:
                missing_fields.append('产品名称')
            if not model:
                missing_fields.append('产品型号')

            if missing_fields:
                flash(f'请填写以下必填字段: {", ".join(missing_fields)}', 'danger')
                current_app.logger.warning(f'创建产品验证失败 - 缺失字段: {missing_fields}')
                current_app.logger.debug(f'表单数据: category_id={category_id}, subcategory_id={subcategory_id}, model={model}')
                return ProductCreationService._redirect_to_create_page(product_type)

            # 3. 验证MN编码唯一性（跨库）
            if mn_code:
                from app.routes.product_management import check_mn_code_duplicate_internal
                duplicate_check = check_mn_code_duplicate_internal(mn_code, exclude_dev_product_id=None)
                if duplicate_check['is_duplicate']:
                    duplicate_info = ProductCreationService._format_duplicate_info(duplicate_check)
                    flash(f'MN编号 {mn_code} 已存在重复产品！\n\n重复产品详细信息:\n{duplicate_info}', 'danger')
                    return ProductCreationService._redirect_to_create_page(product_type)

            # 4. 处理零售价格
            retail_price_decimal = ProductCreationService._parse_retail_price(retail_price)
            if retail_price and retail_price_decimal is None:
                flash('零售价格格式不正确', 'danger')
                return ProductCreationService._redirect_to_create_page(product_type)

            # 5. 根据产品类型创建产品实例
            if product_type == 'research':
                new_product = ProductCreationService._create_research_product(
                    category_id, subcategory_id, region_id, model, product_name, unit,
                    retail_price_decimal, currency, description, development_purpose, mn_code
                )
                redirect_url = 'product_management.index'
                success_message = '新产品已成功添加到研发产品库'
            else:
                # 标准产品特有字段
                product_type_field = request.form.get('type') or None
                product_status = request.form.get('status', 'active')
                brand = request.form.get('brand') or None
                is_vendor_product = request.form.get('is_vendor_product') == 'on'

                new_product = ProductCreationService._create_standard_product(
                    product_type_field, product_status, category_id, subcategory_id,
                    region_id, model, brand, unit, retail_price_decimal, currency,
                    description, mn_code, is_vendor_product
                )
                redirect_url = 'product_route.list'
                success_message = '产品创建成功'

            # 6. 保存产品到数据库
            db.session.add(new_product)
            db.session.flush()

            current_app.logger.debug(f"新产品ID: {new_product.id}, 类型: {product_type}")

            # 7. 保存规格数据
            success = ProductCreationService._save_product_specs(new_product.id, product_type)
            if not success:
                db.session.rollback()
                flash('保存规格数据失败', 'danger')
                return ProductCreationService._redirect_to_create_page(product_type)

            # 7.5. 生成编码定义快照（仅标准产品，研发产品在入库时生成）
            if product_type == 'standard':
                from app.utils.product_helpers import generate_product_snapshot
                snapshot = generate_product_snapshot(
                    product=new_product,
                    source="manual_create"
                )
                if snapshot:
                    new_product.code_definition_snapshot = snapshot
                    current_app.logger.info(f'生成编码快照成功: 产品ID={new_product.id}')
                else:
                    # 快照生成失败不阻止产品创建，只记录警告
                    current_app.logger.warning(f'快照生成跳过: 产品ID={new_product.id}（规格数据可能不完整）')

            # 8. 提交事务
            db.session.commit()

            current_app.logger.info(f'产品创建成功: ID={new_product.id}, MN={mn_code}, 型号={model}, 类型={product_type}')
            flash(success_message, 'success')

            return redirect(url_for(redirect_url))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'创建产品失败: {str(e)}', exc_info=True)
            flash(f'创建产品失败: {str(e)}', 'danger')
            return ProductCreationService._redirect_to_create_page(product_type)

    @staticmethod
    def _create_research_product(category_id, subcategory_id, region_id, model, product_name, unit,
                                retail_price, currency, description, development_purpose, mn_code):
        """创建研发产品实例"""
        # 直接使用region_id（已统一到ProductCodeField）
        return DevProduct(
            category_id=category_id,
            subcategory_id=subcategory_id,
            region_id=region_id if region_id else None,
            name=product_name if product_name else model,  # 优先使用独立产品名称，否则使用型号
            model=model,
            description=description,
            development_purpose=development_purpose,
            unit=unit,
            retail_price=retail_price,
            currency=currency,
            status='调研中',  # 研发产品默认状态
            mn_code=mn_code,
            created_by=current_user.id,
            owner_id=current_user.id
        )

    @staticmethod
    def _create_standard_product(product_type, product_status, category_id, subcategory_id,
                                 region_id, model, brand, unit, retail_price, currency,
                                 description, mn_code, is_vendor_product):
        """创建标准产品实例"""
        return Product(
            type=product_type,
            status=product_status,
            category_id=int(category_id),
            subcategory_id=int(subcategory_id),
            region_id=int(region_id) if region_id else None,
            model=model,
            product_mn=mn_code,
            brand=brand,
            unit=unit,
            retail_price=retail_price,
            currency=currency,
            specification=description,  # 使用旧字段存储描述
            is_vendor_product=is_vendor_product,
            source_type='manual',  # 手动创建
            owner_id=current_user.id
        )

    @staticmethod
    def _save_product_specs(product_id, product_type):
        """保存规格数据"""
        spec_names = request.form.getlist('spec_name[]')
        spec_values = request.form.getlist('spec_value[]')
        spec_codes = request.form.getlist('spec_option_codes[]')

        if not spec_names:
            return True  # 没有规格数据也算成功

        # 构建规格数据列表
        spec_data_list = []
        for i in range(len(spec_names)):
            if spec_names[i].strip():  # 只处理非空规格
                spec_data_list.append({
                    'field_name': spec_names[i],
                    'field_value': spec_values[i] if i < len(spec_values) else '',
                    'field_code': spec_codes[i] if i < len(spec_codes) and spec_codes[i] != '0' else None,
                    'action': 'create'
                })

        if not spec_data_list:
            return True

        # 根据产品类型调用不同的保存函数
        if product_type == 'research':
            success, saved_specs, error = save_dev_product_specs(
                product_id,
                spec_data_list,
                current_app.logger
            )
        else:
            success, saved_specs, error = save_product_specs(product_id, spec_data_list)

        if success:
            current_app.logger.debug(f'保存了 {len(saved_specs)} 条规格数据')
        else:
            current_app.logger.error(f'保存规格失败: {error}')

        return success

    @staticmethod
    def _parse_retail_price(retail_price_str):
        """解析零售价格"""
        if not retail_price_str:
            return None
        try:
            return Decimal(retail_price_str)
        except (InvalidOperation, ValueError):
            return None

    @staticmethod
    def _format_duplicate_info(duplicate_check):
        """格式化重复产品信息"""
        duplicate_info = []
        for product in duplicate_check['dev_products']:
            duplicate_info.append(
                f"研发产品库: {product['name']} "
                f"(型号: {product['model']}, 状态: {product['status']})"
            )
        for product in duplicate_check['standard_products']:
            duplicate_info.append(
                f"标准产品库: {product['name']} "
                f"(型号: {product['model']}, 状态: {product['status']})"
            )
        return "\n".join(duplicate_info)

    @staticmethod
    def _redirect_to_create_page(product_type):
        """根据产品类型重定向到创建页面"""
        if product_type == 'research':
            return redirect(url_for('product_management.new_product'))
        else:
            return redirect(url_for('product_route.create_product_page'))
