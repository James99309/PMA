#!/usr/bin/env python3
"""为剩余中优先级产品创建模版并关联"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from app import create_app, db
from app.models.product import Product
from app.models.product_spec import ProductSpec
from app.models.spec_template import (
    SpecTemplate, SpecTemplateItem, ProductConfiguration, ProductConfigValue
)
from app.models.product_code import (
    ProductSubcategory, ProductCategory, SpecificationDictionary
)
from sqlalchemy import func

app = create_app()

ADMIN_USER_ID = 5


def find_spec_dict(name):
    return SpecificationDictionary.query.filter_by(name=name).first()


def clone_template(model, name, source_template_id):
    source = db.session.get(SpecTemplate, source_template_id)
    if not source:
        return None
    t = SpecTemplate(model=model, name=name, category_id=source.category_id,
                     subcategory_id=source.subcategory_id, version='V1.0',
                     created_by=source.created_by)
    db.session.add(t)
    db.session.flush()
    for item in sorted(source.items, key=lambda x: x.display_order):
        db.session.add(SpecTemplateItem(
            template_id=t.id, spec_dict_id=item.spec_dict_id,
            general_value=item.general_value, use_in_code=item.use_in_code,
            code_length=item.code_length, options=dict(item.options) if item.options else {},
            display_order=item.display_order, is_required=item.is_required))
    db.session.flush()
    return t


def create_template_from_product(model, name, subcategory_id, product_id, code_fields=None):
    sub = db.session.get(ProductSubcategory, subcategory_id)
    if not sub:
        return None
    specs = ProductSpec.query.filter_by(product_id=product_id).filter(
        ProductSpec.field_value.isnot(None), ProductSpec.field_value != ''
    ).all()
    if not specs:
        return None
    code_fields = code_fields or []
    t = SpecTemplate(model=model, name=name, category_id=sub.category_id,
                     subcategory_id=subcategory_id, version='V1.0', created_by=ADMIN_USER_ID)
    db.session.add(t)
    db.session.flush()
    items_data = []
    for s in specs:
        sd = find_spec_dict(s.field_name)
        if sd:
            cat_order = sd.category.display_order if sd.category else 99
            items_data.append((sd, cat_order, sd.display_order or 0, s.field_name))
    items_data.sort(key=lambda x: (0 if x[3] in code_fields else 1, x[1] * 1000 + x[2]))
    for idx, (sd, _, _, fn) in enumerate(items_data):
        db.session.add(SpecTemplateItem(
            template_id=t.id, spec_dict_id=sd.id, use_in_code=fn in code_fields,
            code_length=1, options={}, display_order=idx + 1, is_required=False))
    db.session.flush()
    return t


def link_products(model, template):
    products = Product.query.filter(
        func.upper(Product.model) == model.upper(),
        Product.is_deleted == False, Product.source_configuration_id.is_(None)
    ).all()
    count = 0
    for p in products:
        if p.status == 'discontinued':
            continue
        specs = ProductSpec.query.filter_by(product_id=p.id).all()
        spec_map = {s.field_name: s for s in specs}
        region = p.product_mn[0] if p.product_mn else 'X'
        config = ProductConfiguration(
            template_id=template.id, config_code=p.product_mn or f'legacy-{p.id}',
            region=region, status='production', mn_code=p.product_mn,
            template_version=template.version)
        db.session.add(config)
        db.session.flush()
        matched = 0
        for item in template.items:
            sn = item.spec_dict.name if item.spec_dict else None
            if not sn:
                continue
            ps = spec_map.get(sn)
            if ps and ps.field_value:
                db.session.add(ProductConfigValue(configuration_id=config.id, template_item_id=item.id, value=ps.field_value))
                matched += 1
            elif item.general_value:
                db.session.add(ProductConfigValue(configuration_id=config.id, template_item_id=item.id, value=item.general_value))
                matched += 1
        p.source_configuration_id = config.id
        count += 1
        print(f"  ✅ {p.model} (id={p.id}) → config {config.id} ({matched} specs)")
    return count


with app.app_context():
    total_templates = 0
    total_products = 0

    # === A. 克隆类 ===

    # 光纤近端机 DRFS: 克隆 DRFS-400/M (id=21)
    print("=== 光纤近端机 DRFS ===")
    for m in ['DRFS-88/M', 'DRFS-100/M', 'DRFS-300/M', 'DRFS-800/M']:
        t = clone_template(m, '数字智能光纤直放站 (近端)', 21)
        if t:
            total_templates += 1
            total_products += link_products(m, t)

    # 光纤远端直放站 DRFT: 克隆 DRFT-BDA410/M (id=22)
    print("\n=== 光纤远端直放站 DRFT ===")
    for m in ['DRFT-BDA88/M', 'DRFT-BDA110/M', 'DRFT-BDA310/M', 'DRFT-BDA810/M', 'DRFT-BDA410/MITW']:
        t = clone_template(m, '数字智能光纤直放站 (远端)', 22)
        if t:
            total_templates += 1
            total_products += link_products(m, t)

    # PNR2000: 克隆 MNR3500 (id=23)
    print("\n=== 数字对讲机 PNR2000 ===")
    t = clone_template('PNR2000', 'DMR常规对讲机', 23)
    if t:
        total_templates += 1
        total_products += link_products('PNR2000', t)

    # === B. 从规格新建 ===

    # 信号剥离器
    print("\n=== 信号剥离器 ===")
    p_ref = Product.query.filter_by(model='R-EVDC-BLST-4', is_deleted=False).first()
    if p_ref:
        specs_names = [s.field_name for s in ProductSpec.query.filter_by(product_id=p_ref.id).all() if s.field_value]
        code_fields = ['工作频率', '载波容量支持', '安装方式']
        for m, n in [('R-EVDC-BLST-4', '信号剥离矩阵'), ('R-EVDC-BLST-6', '信号剥离矩阵'),
                     ('R-EVDC-BLST-D', '下行信号剥离器'), ('R-EVDC-BLST-U', '上行信号剥离器')]:
            p1 = Product.query.filter_by(model=m, is_deleted=False).first()
            if p1:
                t = create_template_from_product(m, n, p1.subcategory_id, p1.id, code_fields)
                if t:
                    total_templates += 1
                    total_products += link_products(m, t)

    # 分路器
    print("\n=== 分路器 ===")
    p_ref = Product.query.filter_by(model='E-JF350/400-2', is_deleted=False).first()
    if p_ref:
        code_fields = ['工作频率', '射频接口类型']
        for m in ['E-JF150-2', 'E-JF150-4', 'E-JF350/400-2', 'E-JF350/400-4', 'E-JF350/400-6', 'E-JF350/400-8']:
            p1 = Product.query.filter_by(model=m, is_deleted=False).first()
            if p1:
                t = create_template_from_product(m, '分路器', p1.subcategory_id, p1.id, code_fields)
                if t:
                    total_templates += 1
                    total_products += link_products(m, t)

    # 多信道分合路器
    print("\n=== 多信道分合路器 ===")
    p_ref = Product.query.filter_by(model='FHJ400-2', is_deleted=False).first()
    if p_ref:
        code_fields = ['工作频率', '载波容量支持', '安装方式']
        for m in ['FHJ400-2', 'FHJ400-4', 'FHJ400-6']:
            p1 = Product.query.filter_by(model=m, is_deleted=False).first()
            if p1:
                t = create_template_from_product(m, '多信道分合路器', p1.subcategory_id, p1.id, code_fields)
                if t:
                    total_templates += 1
                    total_products += link_products(m, t)

    # 室外天线
    print("\n=== 室外天线 ===")
    code_fields = ['工作频率', '辐射方向', '安装方式', '射频接口类型']
    for m, n in [('E-ANTG-150', '室外全向玻璃钢天线'), ('E-ANTG 350', '室外全向玻璃钢天线'),
                 ('E-ANTG 400', '室外全向玻璃钢天线'), ('E-ANTD 400', '室外定向板状天线'),
                 ('E-ANTY 100', '室外八木定向天线')]:
        p1 = Product.query.filter_by(model=m, is_deleted=False).first()
        if p1:
            t = create_template_from_product(m, n, p1.subcategory_id, p1.id, code_fields)
            if t:
                total_templates += 1
                total_products += link_products(m, t)

    # 防爆天线
    print("\n=== 防爆天线 ===")
    p1 = Product.query.filter_by(model='MAEX 10', is_deleted=False).first()
    if p1:
        t = create_template_from_product('MAEX 10', '防爆型高防护全向天线', p1.subcategory_id, p1.id,
                                          ['工作频率', '辐射方向', '安装方式', '射频接口类型'])
        if t:
            total_templates += 1
            total_products += link_products('MAEX 10', t)

    # 射频直放站
    print("\n=== 射频直放站 ===")
    p1 = Product.query.filter_by(model='E-BDA400B LT', is_deleted=False).first()
    if p1:
        code_fields = ['工作频率', '最大输出功率', '光口类型', '输入电压(AC)', '显示方式', '外形尺寸', '安装方式']
        t = create_template_from_product('E-BDA400B LT', '常规射频直放站', p1.subcategory_id, p1.id, code_fields)
        if t:
            total_templates += 1
            total_products += link_products('E-BDA400B LT', t)

    # 充电器 CRCAB2000
    print("\n=== 充电器 ===")
    p1 = Product.query.filter_by(model='CRCAB2000', is_deleted=False).first()
    if p1:
        t = create_template_from_product('CRCAB2000', '多联充电柜', p1.subcategory_id, p1.id, [])
        if t:
            total_templates += 1
            total_products += link_products('CRCAB2000', t)

    db.session.commit()
    print(f"\n✅ 完成: 创建 {total_templates} 个模版, 关联 {total_products} 个产品")
