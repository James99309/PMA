#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复工作频率字典中的编码冲突

问题：'800-870' 和 'TX：412-416 / RX：402-406' 都使用编码 '9'
方案：将 'TX：412-416 / RX：402-406' 的编码从 '9' 改为 'A'

影响范围：
1. specification_options → '工作频率' 下 TARGET_VALUE 的 code '9' → 'A'
2. spec_template_items → 含有该 value 的 options JSON 同步更新
3. product_configurations → 使用该频率值的配置，mn_code 校验位重算
   + code_rule_snapshot JSON 同步更新

使用方法:
    python scripts/temp/fix_freq_code_conflict.py [--dry-run | --execute]
"""
import sys
import os
import json
import argparse

# 路径修正
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

from app import create_app, db

# 编码安全字符集（与 app/models/spec_template.py 保持一致）
SAFE_CHARS = "346789ABCDEFGHJKLMNPRTUVWXY"

OLD_CODE = '9'
NEW_CODE = 'A'
DICT_NAME = '工作频率'
TARGET_VALUE = 'TX：412-416 / RX：402-406'


def calculate_check_digit(code):
    """计算校验位（Mod-27算法，带位置权重）- 与 spec_template.py 一致"""
    total = 0
    for i, char in enumerate(code):
        if char in SAFE_CHARS:
            total += (i + 1) * SAFE_CHARS.index(char)
    return SAFE_CHARS[total % len(SAFE_CHARS)]


def fix_conflict(dry_run=True):
    print("=" * 60)
    print("修复工作频率字典编码冲突")
    print(f"  '{TARGET_VALUE}': '{OLD_CODE}' → '{NEW_CODE}'")
    print("=" * 60)

    if dry_run:
        print("【试运行模式】不会实际修改数据\n")
    else:
        print("【执行模式】将修改数据库\n")

    # === 1. 验证当前状态 ===
    print("Step 1: 验证当前状态...")

    # 通过值查找字典选项（不依赖硬编码 ID）
    target_opt = db.session.execute(db.text("""
        SELECT so.id, so.spec_id, so.value, so.code
        FROM specification_options so
        JOIN specification_dictionary sd ON so.spec_id = sd.id
        WHERE sd.name = :dict_name AND so.value = :value
    """), {'dict_name': DICT_NAME, 'value': TARGET_VALUE}).fetchone()

    if not target_opt:
        print(f"  ❌ 未找到 '{DICT_NAME}' 下的 '{TARGET_VALUE}'!")
        return False

    opt_id = target_opt.id
    print(f"  字典选项: ID={opt_id}, value='{target_opt.value}', code='{target_opt.code}'")

    if target_opt.code != OLD_CODE:
        print(f"  ⚠ 编码已不是 '{OLD_CODE}'（当前: '{target_opt.code}'），可能已修复")
        return False

    # 确认冲突存在
    conflict = db.session.execute(db.text("""
        SELECT so.id, so.value, so.code
        FROM specification_options so
        JOIN specification_dictionary sd ON so.spec_id = sd.id
        WHERE sd.name = :dict_name AND so.code = :code
    """), {'dict_name': DICT_NAME, 'code': OLD_CODE}).fetchall()

    print(f"  '{DICT_NAME}' 下编码 '{OLD_CODE}' 的记录数: {len(conflict)}")
    for r in conflict:
        print(f"    ID={r.id}: '{r.value}' → '{r.code}'")

    if len(conflict) < 2:
        print("  ⚠ 未检测到冲突（编码不重复）")
        return False

    print("  ✅ 冲突已确认\n")

    # 查找含有该 value 的模版项（通过 definition 关联查找）
    template_items = db.session.execute(db.text("""
        SELECT sti.id, sti.options, st.name as template_name
        FROM spec_template_items sti
        JOIN spec_definitions sd ON sti.definition_id = sd.id
        JOIN spec_templates st ON sti.template_id = st.id
        WHERE sd.name = :dict_name
        ORDER BY sti.id
    """), {'dict_name': DICT_NAME}).fetchall()

    affected_items = []
    for item in template_items:
        opts = item.options if isinstance(item.options, dict) else (json.loads(item.options) if item.options else {})
        if TARGET_VALUE in opts and opts[TARGET_VALUE] == OLD_CODE:
            affected_items.append((item.id, item.template_name, opts))
            print(f"  模版项 ID={item.id} ({item.template_name}): '{TARGET_VALUE}' → '{opts[TARGET_VALUE]}'")

    if not affected_items:
        print(f"  ⚠ 未找到含 '{TARGET_VALUE}' 编码为 '{OLD_CODE}' 的模版项")

    # 查找使用该频率值的配置版本（通过 code_rule_snapshot 中的 value 匹配）
    configs = db.session.execute(db.text("""
        SELECT pc.id, pc.mn_code, pc.code_rule_snapshot, pc.status
        FROM product_configurations pc
        WHERE pc.code_rule_snapshot::text LIKE :pattern
    """), {'pattern': f'%{TARGET_VALUE}%'}).fetchall()

    print(f"\n  使用 '{TARGET_VALUE}' 的配置版本: {len(configs)} 个")
    for c in configs:
        print(f"    ID={c.id}: mn_code='{c.mn_code}', status='{c.status}'")

    # === 2. 更新字典选项 ===
    print("\nStep 2: 更新字典选项...")
    print(f"  specification_options ID={opt_id}: code '{OLD_CODE}' → '{NEW_CODE}'")
    if not dry_run:
        db.session.execute(db.text(
            "UPDATE specification_options SET code = :new_code WHERE id = :id"
        ), {'new_code': NEW_CODE, 'id': opt_id})

    # === 3. 更新模版 options JSON ===
    print("\nStep 3: 更新模版 options JSON...")
    for item_id, template_name, opts in affected_items:
        new_opts = dict(opts)
        new_opts[TARGET_VALUE] = NEW_CODE
        print(f"  spec_template_items ID={item_id} ({template_name}): '{TARGET_VALUE}' → '{NEW_CODE}'")
        if not dry_run:
            db.session.execute(db.text(
                "UPDATE spec_template_items SET options = :opts WHERE id = :id"
            ), {'opts': json.dumps(new_opts, ensure_ascii=False), 'id': item_id})

    # === 4. 更新配置 MN 码和 snapshot ===
    print("\nStep 4: 更新配置 MN 码和 snapshot...")
    for config in configs:
        config_id = config.id
        old_mn = config.mn_code
        snapshot = config.code_rule_snapshot
        if isinstance(snapshot, str):
            snapshot = json.loads(snapshot)

        print(f"\n  配置 ID={config_id}:")
        print(f"    原 mn_code: '{old_mn}'")

        # 找到 snapshot 中对应的 code_item 并确定其在 mn_code 中的位置
        new_mn = old_mn
        if snapshot and 'code_items' in snapshot:
            for item in snapshot['code_items']:
                if item.get('value') == TARGET_VALUE and item.get('code_char') == OLD_CODE:
                    item['code_char'] = NEW_CODE
                    if 'options' in item and TARGET_VALUE in item['options']:
                        item['options'][TARGET_VALUE] = NEW_CODE
                    print(f"    snapshot code_item 更新: code_char '{OLD_CODE}' → '{NEW_CODE}'")

            # 根据 snapshot 重建 mn_code
            if old_mn:
                main_code = old_mn[:-1]
                # 重建: 前3位(区域+分类+子分类) + code_items 各项的 code_char
                prefix = main_code[:3]
                code_chars = [item['code_char'] for item in snapshot['code_items']]
                new_main = prefix + ''.join(code_chars)
                new_check = calculate_check_digit(new_main)
                new_mn = new_main + new_check

                print(f"    新 main_code: '{new_main}'")
                print(f"    新校验位: '{new_check}'")
                print(f"    新 mn_code: '{new_mn}'")

        if 'full_code' in snapshot:
            snapshot['full_code'] = new_mn

        if not dry_run:
            db.session.execute(db.text(
                "UPDATE product_configurations SET mn_code = :mn, code_rule_snapshot = :snap WHERE id = :id"
            ), {
                'mn': new_mn,
                'snap': json.dumps(snapshot, ensure_ascii=False),
                'id': config_id,
            })

    # === 5. 提交 ===
    if not dry_run:
        db.session.commit()
        print("\n✅ 所有更改已提交!")

    # === 6. 验证 ===
    print("\n" + "=" * 60)
    print("验证结果")
    print("=" * 60)

    # 6a. 字典编码唯一性
    print(f"\n1. {DICT_NAME}字典选项:")
    rows = db.session.execute(db.text("""
        SELECT so.id, so.value, so.code
        FROM specification_options so
        JOIN specification_dictionary sd ON so.spec_id = sd.id
        WHERE sd.name = :dict_name
        ORDER BY so.id
    """), {'dict_name': DICT_NAME}).fetchall()
    codes_seen = {}
    all_unique = True
    for r in rows:
        print(f"   ID={r.id}: '{r.value}' → '{r.code}'")
        if r.code in codes_seen:
            print(f"   ❌ 编码 '{r.code}' 与 ID={codes_seen[r.code]} 冲突!")
            all_unique = False
        codes_seen[r.code] = r.id

    if all_unique:
        print("   ✅ 所有编码唯一")

    # 6b. 全局冲突检查
    print("\n2. 全局编码冲突检查:")
    conflicts = db.session.execute(db.text("""
        SELECT sd.name, so.code, COUNT(*) as cnt
        FROM specification_options so
        JOIN specification_dictionary sd ON so.spec_id = sd.id
        GROUP BY sd.name, so.code
        HAVING COUNT(*) > 1
    """)).fetchall()
    if conflicts:
        for c in conflicts:
            print(f"   ❌ {c.name}: 编码 '{c.code}' 出现 {c.cnt} 次")
    else:
        print("   ✅ 无冲突")

    # 6c. 模版 options
    print("\n3. 模版 options:")
    for item_id, template_name, _ in affected_items:
        row = db.session.execute(db.text(
            "SELECT options FROM spec_template_items WHERE id = :id"
        ), {'id': item_id}).fetchone()
        if row:
            opts = row.options if isinstance(row.options, dict) else json.loads(row.options)
            code = opts.get(TARGET_VALUE)
            status = "✅" if code == NEW_CODE else "❌"
            print(f"   {status} ID={item_id} ({template_name}): '{TARGET_VALUE}' → '{code}'")

    # 6d. MN 码
    print("\n4. 配置 MN 码:")
    for config in configs:
        row = db.session.execute(db.text(
            "SELECT mn_code FROM product_configurations WHERE id = :id"
        ), {'id': config.id}).fetchone()
        if row:
            mn = row.mn_code
            print(f"   ID={config.id}: mn_code='{mn}'")
            if mn and len(mn) >= 5:
                main = mn[:-1]
                check = calculate_check_digit(main)
                status = "✅" if check == mn[-1] else "❌"
                print(f"   {status} 校验位验证: 计算值='{check}', 实际值='{mn[-1]}'")

    print("\n完成!")
    return True


def main():
    parser = argparse.ArgumentParser(description='修复工作频率字典编码冲突')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dry-run', action='store_true', help='试运行（不修改数据）')
    group.add_argument('--execute', action='store_true', help='执行修复')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        fix_conflict(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
