#!/usr/bin/env python3
"""将未关联模版的旧产品关联到对应模版，创建独立的锁定配置"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from app import create_app, db
from app.models.product import Product
from app.models.product_spec import ProductSpec
from app.models.spec_template import (
    SpecTemplate, SpecTemplateItem, ProductConfiguration, ProductConfigValue
)
from app.models.product_code import SpecificationDictionary
from sqlalchemy import func

app = create_app()

with app.app_context():
    # 找所有有模版但未关联的活跃产品
    unlinked = db.session.query(Product, SpecTemplate).join(
        SpecTemplate,
        func.upper(SpecTemplate.model) == func.upper(Product.model)
    ).filter(
        Product.is_deleted == False,
        Product.status != 'discontinued',
        Product.source_configuration_id.is_(None),
        SpecTemplate.deleted_at.is_(None)
    ).all()

    print(f"找到 {len(unlinked)} 个未关联产品\n")

    created = 0
    errors = []

    for product, template in unlinked:
        try:
            # 读取产品的规格
            specs = ProductSpec.query.filter_by(product_id=product.id).all()
            spec_map = {s.field_name: s for s in specs}

            # 从产品MN推断区域码（第1个字符）
            region = product.product_mn[0] if product.product_mn else 'X'

            # 用产品MN作为 config_code（去除前3个字符：区域+分类+子分类）
            config_code = product.product_mn or f'legacy-{product.id}'

            # 创建配置
            config = ProductConfiguration(
                template_id=template.id,
                config_code=config_code,
                region=region,
                status='production',  # 锁定MN
                mn_code=product.product_mn,
                template_version=template.version
            )
            db.session.add(config)
            db.session.flush()  # 获取 config.id

            # 匹配 product_specs → template_items，创建 config values
            matched = 0
            for item in template.items:
                spec_name = item.spec_dict.name if item.spec_dict else None
                if not spec_name:
                    continue

                ps = spec_map.get(spec_name)
                if ps and ps.field_value:
                    cv = ProductConfigValue(
                        configuration_id=config.id,
                        template_item_id=item.id,
                        value=ps.field_value
                    )
                    db.session.add(cv)
                    matched += 1
                elif item.general_value:
                    # 产品无此规格但模版有默认值，用默认值
                    cv = ProductConfigValue(
                        configuration_id=config.id,
                        template_item_id=item.id,
                        value=item.general_value
                    )
                    db.session.add(cv)
                    matched += 1

            # 关联产品到配置
            product.source_configuration_id = config.id

            print(f"  ✅ {product.model} (id={product.id}) → config {config.id} "
                  f"({matched}/{len(template.items)} specs, MN={product.product_mn})")
            created += 1

        except Exception as e:
            errors.append(f"{product.model} (id={product.id}): {e}")
            print(f"  ❌ {product.model} (id={product.id}): {e}")

    if errors:
        print(f"\n⚠️ {len(errors)} 个错误，回滚")
        db.session.rollback()
    else:
        db.session.commit()
        print(f"\n✅ 完成: 创建 {created} 个配置并关联产品")
