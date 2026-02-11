#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查产品模板中的指标和编码是否已正确迁移到字典规格中

诊断项目:
1. SpecTemplateItem 中 use_in_code=True 且 options 为 JSON 自定义的项
2. 对比 SpecificationDictionary + SpecificationOption 中已有的标准字典
3. 找出产品模板中有自定义编码/指标但未在字典中注册的规格
4. ProductCodeField 中的自定义选项（非引用字典的）
"""
import sys, os

def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = '/opt/homebrew/lib'

from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("=" * 80)
    print("产品模板指标与字典规格迁移检查报告")
    print("=" * 80)

    # ============================================================
    # 1. 检查 SpecificationDictionary 中已有的标准规格
    # ============================================================
    print("\n📖 [1] 规格字典 (SpecificationDictionary) 现有内容")
    print("-" * 60)

    result = db.session.execute(text("""
        SELECT sd.id, sd.name, sd.unit, sd.is_active,
               COUNT(so.id) as option_count
        FROM specification_dictionary sd
        LEFT JOIN specification_options so ON so.spec_id = sd.id
        GROUP BY sd.id, sd.name, sd.unit, sd.is_active
        ORDER BY sd.display_order, sd.id
    """))
    dict_specs = result.fetchall()

    if not dict_specs:
        print("  ⚠️ 规格字典为空！")
    else:
        print(f"  共 {len(dict_specs)} 个规格定义:")
        for spec in dict_specs:
            status = "✅" if spec.is_active else "❌"
            print(f"  {status} [{spec.id}] {spec.name} (单位: {spec.unit or '-'}) - {spec.option_count}个指标")

    # 获取所有字典指标详情
    print("\n  📋 字典指标详情:")
    result = db.session.execute(text("""
        SELECT sd.name as spec_name, so.value, so.code, so.is_active
        FROM specification_options so
        JOIN specification_dictionary sd ON sd.id = so.spec_id
        ORDER BY sd.display_order, sd.id, so.position
    """))
    dict_options = result.fetchall()

    if dict_options:
        current_spec = None
        for opt in dict_options:
            if opt.spec_name != current_spec:
                current_spec = opt.spec_name
                print(f"\n    【{current_spec}】")
            status = "✅" if opt.is_active else "❌"
            print(f"      {status} 值: {opt.value} → 编码: {opt.code}")

    # ============================================================
    # 2. 检查 SpecDefinition 中的全局规格字典
    # ============================================================
    print("\n\n📖 [2] 全局规格字典 (SpecDefinition) 现有内容")
    print("-" * 60)

    result = db.session.execute(text("""
        SELECT sd.id, sd.name, sd.name_en, sd.unit, sc.name as category_name,
               sd.is_active
        FROM spec_definitions sd
        LEFT JOIN spec_categories sc ON sc.id = sd.category_id
        ORDER BY sc.display_order, sd.display_order, sd.id
    """))
    global_defs = result.fetchall()

    if not global_defs:
        print("  ⚠️ 全局规格字典为空！")
    else:
        print(f"  共 {len(global_defs)} 个规格定义:")
        current_cat = None
        for d in global_defs:
            if d.category_name != current_cat:
                current_cat = d.category_name
                print(f"\n  📂 {current_cat or '未分类'}")
            status = "✅" if d.is_active else "❌"
            print(f"    {status} [{d.id}] {d.name} ({d.name_en or '-'}) 单位: {d.unit or '-'}")

    # ============================================================
    # 3. 检查 SpecTemplate 中的模板规格项
    # ============================================================
    print("\n\n📖 [3] 产品模板 (SpecTemplate) 规格项详情")
    print("-" * 60)

    result = db.session.execute(text("""
        SELECT st.id as template_id, st.model, st.name as template_name,
               st.version, st.is_active
        FROM spec_templates st
        WHERE st.is_active = true
        ORDER BY st.id
    """))
    templates = result.fetchall()

    if not templates:
        print("  ⚠️ 没有活跃的产品模板！")
    else:
        print(f"  共 {len(templates)} 个活跃模板:")

        for tmpl in templates:
            print(f"\n  🔧 模板 [{tmpl.template_id}]: {tmpl.model} - {tmpl.template_name or ''} (版本: {tmpl.version})")

            # 获取该模板的所有规格项
            result = db.session.execute(text("""
                SELECT sti.id, sti.definition_id,
                       sd.name as def_name, sd.name_en as def_name_en, sd.unit,
                       sc.name as category_name,
                       sti.general_value, sti.options,
                       sti.use_in_code, sti.code_length,
                       sti.display_order
                FROM spec_template_items sti
                LEFT JOIN spec_definitions sd ON sd.id = sti.definition_id
                LEFT JOIN spec_categories sc ON sc.id = sd.category_id
                WHERE sti.template_id = :tid
                ORDER BY sti.display_order
            """), {'tid': tmpl.template_id})
            items = result.fetchall()

            if not items:
                print("    (无规格项)")
                continue

            for item in items:
                code_flag = "📦编码" if item.use_in_code else ""
                def_status = f"引用字典[{item.definition_id}]: {item.def_name}" if item.definition_id else "❌ 无字典引用"

                print(f"    [{item.id}] {def_status} (单位: {item.unit or '-'}) {code_flag}")

                if item.general_value:
                    print(f"         通用值: {item.general_value}")

                if item.options:
                    import json
                    opts = item.options if isinstance(item.options, (list, dict)) else json.loads(item.options)
                    print(f"         自定义选项 (JSON): {json.dumps(opts, ensure_ascii=False)}")

    # ============================================================
    # 4. 核心检查: 模板中的自定义选项 vs 字典指标
    # ============================================================
    print("\n\n" + "=" * 80)
    print("🔍 [4] 核心检查: 模板自定义选项 vs 字典指标对比")
    print("=" * 80)

    # 获取所有模板项的options和对应的字典
    result = db.session.execute(text("""
        SELECT sti.id as item_id, sti.template_id,
               st.model as template_model,
               sti.definition_id, sd.name as spec_name, sd.unit,
               sti.options, sti.use_in_code, sti.code_length
        FROM spec_template_items sti
        JOIN spec_templates st ON st.id = sti.template_id
        LEFT JOIN spec_definitions sd ON sd.id = sti.definition_id
        WHERE st.is_active = true AND sti.options IS NOT NULL
        ORDER BY st.model, sti.display_order
    """))
    items_with_options = result.fetchall()

    # 获取字典中的所有指标 (按名称索引)
    result = db.session.execute(text("""
        SELECT sd.name as spec_name, so.value, so.code
        FROM specification_options so
        JOIN specification_dictionary sd ON sd.id = so.spec_id
        WHERE so.is_active = true
    """))
    dict_option_map = {}
    for row in result.fetchall():
        if row.spec_name not in dict_option_map:
            dict_option_map[row.spec_name] = {}
        dict_option_map[row.spec_name][row.value] = row.code

    import json

    issues = []

    for item in items_with_options:
        opts = item.options if isinstance(item.options, (list, dict)) else json.loads(item.options)
        if not opts:
            continue

        spec_name = item.spec_name or f"未知规格(item_id={item.item_id})"

        # 检查选项是否在字典中
        dict_opts = dict_option_map.get(spec_name, {})

        if isinstance(opts, dict):
            # options 格式: {"value": "code", ...}
            for value, code in opts.items():
                if spec_name not in dict_option_map:
                    issues.append({
                        'type': 'spec_not_in_dict',
                        'template': item.template_model,
                        'spec_name': spec_name,
                        'value': value,
                        'code': code,
                        'use_in_code': item.use_in_code,
                        'message': f'规格 "{spec_name}" 不在规格字典中'
                    })
                elif value not in dict_opts:
                    issues.append({
                        'type': 'option_not_in_dict',
                        'template': item.template_model,
                        'spec_name': spec_name,
                        'value': value,
                        'code': code,
                        'use_in_code': item.use_in_code,
                        'dict_code': None,
                        'message': f'指标值 "{value}" 不在字典的 "{spec_name}" 选项中'
                    })
                elif dict_opts[value] != code:
                    issues.append({
                        'type': 'code_mismatch',
                        'template': item.template_model,
                        'spec_name': spec_name,
                        'value': value,
                        'code': code,
                        'dict_code': dict_opts[value],
                        'use_in_code': item.use_in_code,
                        'message': f'编码不一致: 模板用 "{code}", 字典用 "{dict_opts[value]}"'
                    })
        elif isinstance(opts, list):
            # options 格式: [{"value": "xxx", "code": "x"}, ...]
            for opt_item in opts:
                if isinstance(opt_item, dict):
                    value = opt_item.get('value', '')
                    code = opt_item.get('code', '')
                else:
                    value = str(opt_item)
                    code = ''

                if spec_name not in dict_option_map:
                    issues.append({
                        'type': 'spec_not_in_dict',
                        'template': item.template_model,
                        'spec_name': spec_name,
                        'value': value,
                        'code': code,
                        'use_in_code': item.use_in_code,
                        'message': f'规格 "{spec_name}" 不在规格字典中'
                    })
                elif value and value not in dict_opts:
                    issues.append({
                        'type': 'option_not_in_dict',
                        'template': item.template_model,
                        'spec_name': spec_name,
                        'value': value,
                        'code': code,
                        'use_in_code': item.use_in_code,
                        'dict_code': None,
                        'message': f'指标值 "{value}" 不在字典的 "{spec_name}" 选项中'
                    })

    if not issues:
        print("\n  ✅ 所有模板自定义选项均已在字典中注册，无问题！")
    else:
        print(f"\n  ⚠️ 发现 {len(issues)} 个问题:")

        # 按问题类型分组
        by_type = {}
        for issue in issues:
            t = issue['type']
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(issue)

        if 'spec_not_in_dict' in by_type:
            unique_specs = set()
            print(f"\n  🔴 规格未在字典中注册 ({len(by_type['spec_not_in_dict'])} 个):")
            for issue in by_type['spec_not_in_dict']:
                key = f"{issue['spec_name']}"
                if key not in unique_specs:
                    unique_specs.add(key)
                    code_flag = " [参与编码]" if issue['use_in_code'] else ""
                    print(f"    - 规格: {issue['spec_name']}{code_flag}")
                    print(f"      模板: {issue['template']}, 示例值: {issue['value']} → 编码: {issue['code']}")

        if 'option_not_in_dict' in by_type:
            print(f"\n  🟡 指标值未在字典中注册 ({len(by_type['option_not_in_dict'])} 个):")
            for issue in by_type['option_not_in_dict']:
                code_flag = " [参与编码]" if issue['use_in_code'] else ""
                print(f"    - 模板 {issue['template']}: {issue['spec_name']}{code_flag}")
                print(f"      值: {issue['value']} → 编码: {issue['code']}")

        if 'code_mismatch' in by_type:
            print(f"\n  🟠 编码不一致 ({len(by_type['code_mismatch'])} 个):")
            for issue in by_type['code_mismatch']:
                print(f"    - 模板 {issue['template']}: {issue['spec_name']}")
                print(f"      值: {issue['value']}, 模板编码: {issue['code']}, 字典编码: {issue['dict_code']}")

    # ============================================================
    # 5. 检查 ProductCodeField 中的自定义选项
    # ============================================================
    print("\n\n📖 [5] ProductCodeField 中的选项来源检查")
    print("-" * 60)

    result = db.session.execute(text("""
        SELECT pcf.id as field_id, pcf.name, pcf.field_type, pcf.use_in_code,
               pcf.category_id, pcf.subcategory_id,
               pc.name as cat_name,
               ps.name as subcat_name,
               pcfo.id as option_id, pcfo.value, pcfo.code,
               pcfo.spec_option_id, pcfo.subcategory_id as option_subcat_id
        FROM product_code_fields pcf
        LEFT JOIN product_code_field_options pcfo ON pcfo.field_id = pcf.id
        LEFT JOIN product_categories pc ON pc.id = pcf.category_id
        LEFT JOIN product_subcategories ps ON ps.id = pcf.subcategory_id
        WHERE pcf.field_type = 'spec'
        ORDER BY pcf.category_id, pcf.subcategory_id, pcf.position, pcfo.position
    """))

    field_options = result.fetchall()

    custom_count = 0
    dict_ref_count = 0
    current_field = None

    for row in field_options:
        if row.field_id != current_field:
            current_field = row.field_id
            scope = f"分类: {row.cat_name}" if row.cat_name else f"子分类: {row.subcat_name}"
            code_flag = "📦编码" if row.use_in_code else ""
            print(f"\n  字段 [{row.field_id}]: {row.name} ({scope}) {code_flag}")

        if row.option_id:
            if row.spec_option_id:
                dict_ref_count += 1
                print(f"    ✅ [{row.option_id}] {row.value} → {row.code} (引用字典指标 #{row.spec_option_id})")
            else:
                custom_count += 1
                print(f"    ⚠️ [{row.option_id}] {row.value} → {row.code} (自定义，未引用字典)")

    print(f"\n  统计: 引用字典 {dict_ref_count} 个, 自定义 {custom_count} 个")

    # ============================================================
    # 6. 总结
    # ============================================================
    print("\n\n" + "=" * 80)
    print("📊 总结")
    print("=" * 80)
    print(f"  规格字典条目数: {len(dict_specs)}")
    print(f"  全局规格定义数: {len(global_defs)}")
    print(f"  活跃模板数: {len(templates)}")
    print(f"  模板中有自定义选项的项数: {len(items_with_options)}")
    print(f"  发现的问题数: {len(issues)}")
    print(f"  ProductCodeField 中引用字典: {dict_ref_count}, 自定义: {custom_count}")
    print()
