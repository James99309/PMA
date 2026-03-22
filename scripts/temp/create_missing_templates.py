#!/usr/bin/env python3
"""为缺模版的高优先级产品创建模版、配置并关联"""
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


def find_spec_dict(name):
    """查找规格字典条目"""
    return SpecificationDictionary.query.filter_by(name=name).first()


def clone_template_for_model(model, name, source_template_id, extra_spec_names=None):
    """克隆已有模版结构，可选增加额外规格"""
    source = SpecTemplate.query.get(source_template_id)
    if not source:
        print(f"  ❌ 源模版 {source_template_id} 不存在")
        return None

    # 创建模版
    template = SpecTemplate(
        model=model,
        name=name,
        category_id=source.category_id,
        subcategory_id=source.subcategory_id,
        version='V1.0',
        created_by=source.created_by
    )
    db.session.add(template)
    db.session.flush()

    # 克隆模版项
    max_order = 0
    for item in sorted(source.items, key=lambda x: x.display_order):
        new_item = SpecTemplateItem(
            template_id=template.id,
            spec_dict_id=item.spec_dict_id,
            general_value=item.general_value,
            use_in_code=item.use_in_code,
            code_length=item.code_length,
            options=dict(item.options) if item.options else {},
            display_order=item.display_order,
            is_required=item.is_required,
            test_condition_id=item.test_condition_id,
            test_method_id=item.test_method_id,
        )
        db.session.add(new_item)
        max_order = max(max_order, item.display_order)

    # 增加额外规格
    if extra_spec_names:
        for idx, spec_name in enumerate(extra_spec_names):
            sd = find_spec_dict(spec_name)
            if sd:
                new_item = SpecTemplateItem(
                    template_id=template.id,
                    spec_dict_id=sd.id,
                    use_in_code=False,
                    code_length=1,
                    options={},
                    display_order=max_order + idx + 1,
                    is_required=False
                )
                db.session.add(new_item)

    db.session.flush()
    return template


def create_template_from_specs(model, name, category_id, subcategory_id, spec_names, code_fields=None, created_by=5):
    """从规格名称列表创建新模版"""
    template = SpecTemplate(
        model=model,
        name=name,
        category_id=category_id,
        subcategory_id=subcategory_id,
        version='V1.0',
        created_by=created_by
    )
    db.session.add(template)
    db.session.flush()

    code_fields = code_fields or []

    # 按字典排序创建模版项
    items_data = []
    for spec_name in spec_names:
        sd = find_spec_dict(spec_name)
        if sd:
            cat_order = 99
            if sd.category:
                cat_order = sd.category.display_order or 99
            items_data.append((sd, cat_order, sd.display_order or 0))

    # 编码字段在前，按字典排序
    items_data.sort(key=lambda x: (0 if x[0].name in code_fields else 1, x[1] * 1000 + x[2]))

    for idx, (sd, _, _) in enumerate(items_data):
        new_item = SpecTemplateItem(
            template_id=template.id,
            spec_dict_id=sd.id,
            use_in_code=sd.name in code_fields,
            code_length=1,
            options={},
            display_order=idx + 1,
            is_required=False
        )
        db.session.add(new_item)

    db.session.flush()
    return template


def link_product_to_template(product, template):
    """为产品创建锁定配置并关联"""
    specs = ProductSpec.query.filter_by(product_id=product.id).all()
    spec_map = {s.field_name: s for s in specs}

    region = product.product_mn[0] if product.product_mn else 'X'

    config = ProductConfiguration(
        template_id=template.id,
        config_code=product.product_mn or f'legacy-{product.id}',
        region=region,
        status='production',
        mn_code=product.product_mn,
        template_version=template.version
    )
    db.session.add(config)
    db.session.flush()

    matched = 0
    for item in template.items:
        spec_name = item.spec_dict.name if item.spec_dict else None
        if not spec_name:
            continue
        ps = spec_map.get(spec_name)
        if ps and ps.field_value:
            cv = ProductConfigValue(configuration_id=config.id, template_item_id=item.id, value=ps.field_value)
            db.session.add(cv)
            matched += 1
        elif item.general_value:
            cv = ProductConfigValue(configuration_id=config.id, template_item_id=item.id, value=item.general_value)
            db.session.add(cv)
            matched += 1

    product.source_configuration_id = config.id
    return config, matched


with app.app_context():
    errors = []
    created_templates = 0
    linked_products = 0

    # ========== 耦合器 ==========

    # EVDC-30 LT: 克隆 EVDC-6 LT (id=2)
    print("=== 耦合器 ===")
    t = clone_template_for_model('EVDC-30 LT', '定向耦合器', 2)
    if t:
        created_templates += 1
        p = Product.query.filter_by(model='EVDC-30 LT', is_deleted=False).first()
        if p:
            c, m = link_product_to_template(p, t)
            linked_products += 1
            print(f"  ✅ EVDC-30 LT → template {t.id}, config {c.id} ({m} specs)")

    # MADC系列: 从产品规格新建
    madc_specs = ['工作频率', '输入/输出驻波比', '射频阻抗', '耦合度', '承载功率',
                  '馈电通过', '工作温度', '工作湿度', '射频接口类型']
    madc_codes = ['工作频率', '耦合度', '射频接口类型']
    sub_coupler = ProductSubcategory.query.filter_by(name='耦合器').first()

    for model_name in ['MADC-6', 'MADC-10', 'MADC-15', 'MADC-20']:
        t = create_template_from_specs(model_name, '馈电定向耦合器',
                                        sub_coupler.category_id, sub_coupler.id,
                                        madc_specs, madc_codes)
        if t:
            created_templates += 1
            p = Product.query.filter_by(model=model_name, is_deleted=False).first()
            if p:
                c, m = link_product_to_template(p, t)
                linked_products += 1
                print(f"  ✅ {model_name} → template {t.id}, config {c.id} ({m} specs)")

    # ========== 分配器 ==========
    print("\n=== 分配器 ===")
    mapd_specs = ['工作频率', '输入/输出驻波比', '射频阻抗', '承载功率', '分配损耗',
                  '馈电通过', '工作温度', '工作湿度', '射频接口类型']
    mapd_codes = ['工作频率', '分配损耗', '射频接口类型']
    sub_splitter = ProductSubcategory.query.filter_by(name='分配器').first()

    t = create_template_from_specs('MAPD-2', '馈电功率分配器',
                                    sub_splitter.category_id, sub_splitter.id,
                                    mapd_specs, mapd_codes)
    if t:
        created_templates += 1
        p = Product.query.filter_by(model='MAPD-2', is_deleted=False).first()
        if p:
            c, m = link_product_to_template(p, t)
            linked_products += 1
            print(f"  ✅ MAPD-2 → template {t.id}, config {c.id} ({m} specs)")

    # ========== 合路器 ==========
    print("\n=== 合路器 ===")
    for model_name in ['E-FH150-2', 'E-FH150-4', 'E-FH350-4', 'E-FH400-2', 'E-FH400-4', 'E-FH400-6']:
        t = clone_template_for_model(model_name, '定向耦合合路器', 24)  # 克隆 E-FH400-8
        if t:
            created_templates += 1
            p = Product.query.filter_by(model=model_name, is_deleted=False).first()
            if p:
                c, m = link_product_to_template(p, t)
                linked_products += 1
                print(f"  ✅ {model_name} → template {t.id}, config {c.id} ({m} specs)")

    # ========== 双工器 ==========
    print("\n=== 双工器 ===")
    duplexer_specs = ['工作频率', '输入/输出驻波比', '上下行隔离度', '射频阻抗', '插入损耗',
                      '承载功率', '双工类型', '带外抑制', '工作温度', '工作湿度',
                      '安装方式', '射频接口类型', '防护等级']
    duplexer_codes = ['工作频率', '双工类型', '射频接口类型']
    sub_duplexer = ProductSubcategory.query.filter_by(name='双工器').first()

    for model_name in ['E-SGQ150D', 'E-SGQ350D', 'E-SGQ400D', 'E-SGQ400N', 'E-SGQ800D']:
        t = create_template_from_specs(model_name, '双工器',
                                        sub_duplexer.category_id, sub_duplexer.id,
                                        duplexer_specs, duplexer_codes)
        if t:
            created_templates += 1
            products = Product.query.filter_by(model=model_name, is_deleted=False).all()
            for p in products:
                if not p.source_configuration_id:
                    c, m = link_product_to_template(p, t)
                    linked_products += 1
                    print(f"  ✅ {model_name} (id={p.id}) → template {t.id}, config {c.id} ({m} specs)")

    # ========== 室内天线 ==========
    print("\n=== 室内天线 ===")
    # MA11: MA10 + 状态指示灯, 输入电压(DC)
    t = clone_template_for_model('MA11', '智能室内全向吸顶天线', 9,
                                  extra_spec_names=['状态指示灯', '输入电压(DC)'])
    if t:
        created_templates += 1
        p = Product.query.filter_by(model='MA11', is_deleted=False).first()
        if p:
            c, m = link_product_to_template(p, t)
            linked_products += 1
            print(f"  ✅ MA11 → template {t.id}, config {c.id} ({m} specs)")

    # MA12: MA10 + 蓝牙信标, 输入电压(DC)
    t = clone_template_for_model('MA12', '智能室内蓝牙全向吸顶天线', 9,
                                  extra_spec_names=['蓝牙信标', '输入电压(DC)'])
    if t:
        created_templates += 1
        p = Product.query.filter_by(model='MA12', is_deleted=False).first()
        if p:
            c, m = link_product_to_template(p, t)
            linked_products += 1
            print(f"  ✅ MA12 → template {t.id}, config {c.id} ({m} specs)")

    if errors:
        print(f"\n⚠️ {len(errors)} 个错误，回滚")
        for e in errors:
            print(f"  {e}")
        db.session.rollback()
    else:
        db.session.commit()
        print(f"\n✅ 完成: 创建 {created_templates} 个模版, 关联 {linked_products} 个产品")
