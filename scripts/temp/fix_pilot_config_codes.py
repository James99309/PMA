#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 pilot/development 配置的编码：将模版 options 中的错误编码修正为规格字典编码
同步更新：配置MN码 → CN产品 → SG产品 → SG报价单明细

前提：spec_template_items.options 中的编码由哈希算法生成，与 specification_options 字典不一致
"""
import subprocess
import json
import sys

# ============ 配置 ============
CN_SSH = "ssh -p 72 -o ConnectTimeout=10 -o BatchMode=yes james.sh@100.118.231.15"
CN_DB = "pma_synology"
SG_SSH = "ssh -o ConnectTimeout=10 -o BatchMode=yes admin@100.87.155.40"
SG_DB = "pma_sa"
DRY_RUN = "--dry-run" in sys.argv

SAFE_CHARS = "346789ABCDEFGHJKLMNPRTUVWXY"

def calculate_check_digit(code):
    """Mod-27 校验位算法（与 app/models/spec_template.py 一致）"""
    total = 0
    for i, char in enumerate(code):
        if char in SAFE_CHARS:
            total += (i + 1) * SAFE_CHARS.index(char)
    return SAFE_CHARS[total % len(SAFE_CHARS)]

def run_cn_sql(sql):
    cmd = f'{CN_SSH} "sudo /usr/local/bin/docker exec -i pma-postgres psql -U pma {CN_DB} -t -A -F\'|\'" <<\'SQLEOF\'\n{sql}\nSQLEOF'
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    return r.stdout.strip()

def run_cn_exec(sql):
    cmd = f'{CN_SSH} "sudo /usr/local/bin/docker exec -i pma-postgres psql -U pma {CN_DB}" <<\'SQLEOF\'\n{sql}\nSQLEOF'
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    return r.stdout.strip()

def run_sg_exec(sql):
    cmd = f'{SG_SSH} "sudo sh -c \'export PATH=/usr/local/bin:\\$PATH && docker exec -i pma-postgres psql -U pma {SG_DB}\'" <<\'SQLEOF\'\n{sql}\nSQLEOF'
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    return r.stdout.strip()

# ============ Step 1: 获取需要修复的配置 ============
print("=" * 60)
print("Step 1: 获取需要修复的 pilot/dev 配置")
print("=" * 60)

# 14个已知的不一致配置
mismatches_raw = run_cn_sql("""
WITH config_codes AS (
    SELECT pc.id as config_id, pc.mn_code, pc.status,
           st.model as template_model,
           sd.name as field_name,
           sti.spec_dict_id, sti.id as item_id,
           pcv.value,
           sti.options as item_options,
           sti.display_order
    FROM product_configurations pc
    JOIN spec_templates st ON pc.template_id = st.id
    JOIN product_config_values pcv ON pcv.configuration_id = pc.id
    JOIN spec_template_items sti ON pcv.template_item_id = sti.id
    JOIN specification_dictionary sd ON sti.spec_dict_id = sd.id
    WHERE pc.deleted_at IS NULL AND st.deleted_at IS NULL
      AND sti.use_in_code = true
      AND pc.status IN ('pilot', 'development')
)
SELECT cc.config_id, cc.mn_code, cc.status, cc.template_model,
       cc.field_name, cc.value, cc.display_order,
       (cc.item_options::json->>cc.value) as template_code,
       so.code as dict_code, cc.item_id
FROM config_codes cc
LEFT JOIN specification_options so ON so.spec_id = cc.spec_dict_id AND so.value = cc.value
WHERE so.code IS NOT NULL AND so.code != (cc.item_options::json->>cc.value)
ORDER BY cc.mn_code, cc.display_order;
""")

configs_to_fix = {}  # mn_code → list of fixes

for line in mismatches_raw.split('\n'):
    if not line.strip():
        continue
    parts = line.split('|')
    if len(parts) != 10:
        continue
    config_id, mn_code, status, model, field_name, value, display_order, template_code, dict_code, item_id = [p.strip() for p in parts]

    if mn_code not in configs_to_fix:
        configs_to_fix[mn_code] = {
            'config_id': int(config_id),
            'model': model,
            'status': status,
            'fixes': []
        }
    configs_to_fix[mn_code]['fixes'].append({
        'field_name': field_name,
        'value': value,
        'old_code': template_code,
        'new_code': dict_code,
        'item_id': int(item_id)
    })

print(f"  需要修复 {len(configs_to_fix)} 个配置")
for mn, info in configs_to_fix.items():
    fixes_desc = ', '.join(f"{f['field_name']}: {f['old_code']}→{f['new_code']}" for f in info['fixes'])
    print(f"    {mn} ({info['model']}, {info['status']}): {fixes_desc}")

# ============ Step 2: 计算新 MN 码 ============
print()
print("=" * 60)
print("Step 2: 计算新 MN 码")
print("=" * 60)

mn_updates = {}  # old_mn → new_mn

for old_mn, info in configs_to_fix.items():
    # 获取完整的 code_rule_snapshot 来确定每个字段在 MN 中的位置
    snapshot_raw = run_cn_sql(f"""
        SELECT code_rule_snapshot::text FROM product_configurations WHERE id = {info['config_id']};
    """)

    if not snapshot_raw:
        print(f"  ⚠️ {old_mn}: 无 code_rule_snapshot，跳过")
        continue

    snapshot = json.loads(snapshot_raw)
    code_items = snapshot.get('code_items', [])

    # MN 结构: region(1) + category(1) + subcategory(1) + spec_codes(...) + checksum(1)
    # 每个 spec code 可能是 1 位或 2 位（code_length）
    main_code = old_mn[:-1]  # 去掉校验位
    prefix_len = 3  # region + category + subcategory

    # 计算每个 code_item 在 MN 中的起始位置
    item_positions = []  # [(start_pos, code_length, code_char)]
    pos = prefix_len
    for ci in code_items:
        cl = ci.get('code_length', 1)
        cc = ci.get('code_char', '')
        item_positions.append((pos, cl, cc, ci.get('definition_name', '')))
        pos += cl

    new_main = list(main_code)

    for fix in info['fixes']:
        for start, cl, cc, name in item_positions:
            if name == fix['field_name']:
                # 替换该位置的第一个字符（编码字符）
                if start < len(new_main):
                    # 对于 code_length=2 的字段，code_char 是 "4X" 这样的，只替换第一个字符
                    old_first = fix['old_code']
                    if new_main[start] == old_first:
                        new_main[start] = fix['new_code']
                break

    new_main_str = ''.join(new_main)
    new_check = calculate_check_digit(new_main_str)
    new_mn = new_main_str + new_check

    mn_updates[old_mn] = new_mn
    print(f"  {old_mn} → {new_mn}")

# ============ Step 3: 查找 CN NAS 和 SG NAS 上的关联产品 ============
print()
print("=" * 60)
print("Step 3: 查找关联产品")
print("=" * 60)

old_mns = list(mn_updates.keys())
mn_list_sql = ','.join(f"'{mn}'" for mn in old_mns)

# CN NAS 产品
cn_products_raw = run_cn_sql(f"""
    SELECT id, product_mn, model FROM products
    WHERE product_mn IN ({mn_list_sql}) AND is_deleted = false;
""")
cn_products = []
for line in cn_products_raw.split('\n'):
    if not line.strip():
        continue
    parts = line.split('|')
    if len(parts) == 3:
        cn_products.append({'id': int(parts[0].strip()), 'mn': parts[1].strip(), 'model': parts[2].strip()})

print(f"  CN NAS 产品: {len(cn_products)} 个")
for p in cn_products:
    print(f"    产品{p['id']} ({p['model']}): {p['mn']} → {mn_updates.get(p['mn'], '?')}")

# SG NAS 产品
sg_products_raw = subprocess.run(
    f'{SG_SSH} "sudo sh -c \'export PATH=/usr/local/bin:\\$PATH && docker exec -i pma-postgres psql -U pma {SG_DB} -t -A -F\\\"|\\\"\'" <<\'SQLEOF\'\nSELECT id, product_mn, model FROM products WHERE product_mn IN ({mn_list_sql}) AND is_deleted = false;\nSQLEOF',
    shell=True, capture_output=True, text=True, timeout=30
).stdout.strip()

sg_products = []
for line in sg_products_raw.split('\n'):
    if not line.strip():
        continue
    parts = line.split('|')
    if len(parts) == 3:
        sg_products.append({'id': int(parts[0].strip()), 'mn': parts[1].strip(), 'model': parts[2].strip()})

print(f"  SG NAS 产品: {len(sg_products)} 个")
for p in sg_products:
    print(f"    产品{p['id']} ({p['model']}): {p['mn']} → {mn_updates.get(p['mn'], '?')}")

# SG NAS 报价单明细
sg_quotations_raw = subprocess.run(
    f'{SG_SSH} "sudo sh -c \'export PATH=/usr/local/bin:\\$PATH && docker exec -i pma-postgres psql -U pma {SG_DB} -t -A -F\\\"|\\\"\'" <<\'SQLEOF\'\nSELECT qd.id, qd.product_mn, q.quotation_number FROM quotation_details qd JOIN quotations q ON qd.quotation_id = q.id WHERE qd.product_mn IN ({mn_list_sql});\nSQLEOF',
    shell=True, capture_output=True, text=True, timeout=30
).stdout.strip()

sg_quotation_details = []
for line in sg_quotations_raw.split('\n'):
    if not line.strip():
        continue
    parts = line.split('|')
    if len(parts) == 3:
        sg_quotation_details.append({'id': int(parts[0].strip()), 'mn': parts[1].strip(), 'qn': parts[2].strip()})

print(f"  SG NAS 报价单明细: {len(sg_quotation_details)} 个")
for qd in sg_quotation_details:
    print(f"    明细{qd['id']} ({qd['qn']}): {qd['mn']} → {mn_updates.get(qd['mn'], '?')}")

# ============ Step 4: 执行更新 ============
if DRY_RUN:
    print()
    print("=" * 60)
    print("DRY RUN 模式 - 不执行更新")
    print("=" * 60)
    sys.exit(0)

print()
print("=" * 60)
print("Step 4: 执行更新")
print("=" * 60)

# 4a: 更新 CN NAS 配置的 mn_code 和 template_item.options
for old_mn, new_mn in mn_updates.items():
    info = configs_to_fix[old_mn]

    # 更新配置 MN 码和 code_rule_snapshot 中的编码
    result = run_cn_exec(f"UPDATE product_configurations SET mn_code = '{new_mn}' WHERE id = {info['config_id']};")
    if 'UPDATE 1' in result:
        print(f"  ✅ [CN] 配置 {old_mn} → {new_mn}")
    else:
        print(f"  ❌ [CN] 配置 {old_mn} 更新失败: {result}")

    # 更新 template_item.options 中的编码映射
    for fix in info['fixes']:
        # 读取当前 options，替换编码
        opts_raw = run_cn_sql(f"SELECT options::text FROM spec_template_items WHERE id = {fix['item_id']};")
        if opts_raw:
            try:
                opts = json.loads(opts_raw)
                if fix['value'] in opts and opts[fix['value']] == fix['old_code']:
                    opts[fix['value']] = fix['new_code']
                    opts_json = json.dumps(opts, ensure_ascii=False).replace("'", "''")
                    run_cn_exec(f"UPDATE spec_template_items SET options = '{opts_json}'::json WHERE id = {fix['item_id']};")
                    print(f"    ✅ [CN] 模版项 {fix['item_id']} options: {fix['field_name']} {fix['old_code']}→{fix['new_code']}")
            except json.JSONDecodeError:
                print(f"    ⚠️ [CN] 模版项 {fix['item_id']} options JSON解析失败")

# 4b: 更新 CN NAS 产品
for p in cn_products:
    new_mn = mn_updates.get(p['mn'])
    if new_mn:
        result = run_cn_exec(f"UPDATE products SET product_mn = '{new_mn}' WHERE id = {p['id']};")
        if 'UPDATE 1' in result:
            print(f"  ✅ [CN] 产品 {p['id']} ({p['model']}): {p['mn']} → {new_mn}")
        else:
            print(f"  ❌ [CN] 产品 {p['id']} 更新失败: {result}")

# 4c: 更新 SG NAS 产品
for p in sg_products:
    new_mn = mn_updates.get(p['mn'])
    if new_mn:
        result = run_sg_exec(f"UPDATE products SET product_mn = '{new_mn}' WHERE id = {p['id']};")
        if 'UPDATE 1' in result:
            print(f"  ✅ [SG] 产品 {p['id']} ({p['model']}): {p['mn']} → {new_mn}")
        else:
            print(f"  ❌ [SG] 产品 {p['id']} 更新失败: {result}")

# 4d: 更新 SG NAS 报价单明细
for qd in sg_quotation_details:
    new_mn = mn_updates.get(qd['mn'])
    if new_mn:
        result = run_sg_exec(f"UPDATE quotation_details SET product_mn = '{new_mn}' WHERE id = {qd['id']};")
        if 'UPDATE 1' in result:
            print(f"  ✅ [SG] 报价单明细 {qd['id']} ({qd['qn']}): {qd['mn']} → {new_mn}")
        else:
            print(f"  ❌ [SG] 报价单明细 {qd['id']} 更新失败: {result}")

print()
print("完成！")
