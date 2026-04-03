#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 SG NAS 产品的 code_definition_snapshot 中 use_in_code 标记

问题: batch_regenerate 生成的 snapshot 把所有字段都标为 use_in_code=true，
      但实际上应以 CN NAS 模版定义为准。

方案:
  1. 从 CN NAS 读取模版定义（哪些字段 use_in_code=true）
  2. 对 SG NAS 匹配到模版的产品，修正 snapshot 中的 use_in_code
  3. use_in_code=false 的字段同时清空 code（与新导入产品格式一致）
"""

import subprocess
import json
import sys

# ============ 配置 ============
CN_SSH = "ssh -p 72 -o ConnectTimeout=10 -o BatchMode=yes james.sh@100.118.231.15"
CN_DB = "pma_synology"
SG_SSH = "ssh -o ConnectTimeout=10 -o BatchMode=yes admin@100.87.155.40"
SG_DB = "pma_sa"
DRY_RUN = "--dry-run" in sys.argv  # 加 --dry-run 只预览不执行

def run_cn_sql(sql):
    cmd = f'{CN_SSH} "sudo /usr/local/bin/docker exec -i pma-postgres psql -U pma {CN_DB} -t -A -F\'|\'" <<\'SQLEOF\'\n{sql}\nSQLEOF'
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    return r.stdout.strip()

def run_sg_sql(sql):
    cmd = f'{SG_SSH} "sudo sh -c \'export PATH=/usr/local/bin:\\$PATH && docker exec -i pma-postgres psql -U pma {SG_DB}\'" <<\'SQLEOF\'\n{sql}\nSQLEOF'
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    return r.stdout.strip()

def run_sg_sql_raw(sql):
    """返回原始 -t -A 格式"""
    cmd = f'{SG_SSH} "sudo sh -c \'export PATH=/usr/local/bin:\\$PATH && docker exec -i pma-postgres psql -U pma {SG_DB} -t -A -F\\\"|\\\"\'" <<\'SQLEOF\'\n{sql}\nSQLEOF'
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    return r.stdout.strip()

# ============ Step 1: 从 CN NAS 读取模版编码字段定义 ============
print("=" * 60)
print("Step 1: 从 CN NAS 读取模版编码字段定义")
print("=" * 60)

cn_data = run_cn_sql("""
SELECT st.model, sd.name, sti.use_in_code
FROM spec_template_items sti
JOIN specification_dictionary sd ON sti.spec_dict_id = sd.id
JOIN spec_templates st ON sti.template_id = st.id
WHERE st.deleted_at IS NULL
ORDER BY st.model, sti.display_order;
""")

# 解析: model → set of encoding field names
template_encoding_fields = {}  # model → set(field_names with use_in_code=true)
template_all_fields = {}       # model → set(all field_names)

for line in cn_data.split('\n'):
    if not line.strip():
        continue
    parts = line.split('|')
    if len(parts) != 3:
        continue
    model, field_name, use_in_code = parts[0].strip(), parts[1].strip(), parts[2].strip()

    if model not in template_encoding_fields:
        template_encoding_fields[model] = set()
        template_all_fields[model] = set()

    template_all_fields[model].add(field_name)
    if use_in_code == 't':
        template_encoding_fields[model].add(field_name)

print(f"  已加载 {len(template_encoding_fields)} 个模版定义")
for model in sorted(template_encoding_fields):
    enc = template_encoding_fields[model]
    print(f"    {model}: {len(enc)} 个编码字段 → {', '.join(sorted(enc))}")

# ============ Step 2: 读取 SG NAS 需要修复的产品 ============
print()
print("=" * 60)
print("Step 2: 读取 SG NAS 需要修复的产品")
print("=" * 60)

sg_data = run_sg_sql_raw("""
SELECT p.id, p.model, p.code_definition_snapshot::text
FROM products p
WHERE p.is_deleted = false
  AND p.code_definition_snapshot IS NOT NULL
  AND p.is_vendor_product = true
ORDER BY p.model, p.id;
""")

products_to_fix = []
skipped_no_template = set()

for line in sg_data.split('\n'):
    if not line.strip():
        continue
    parts = line.split('|', 2)
    if len(parts) != 3:
        continue

    pid = int(parts[0].strip())
    model = parts[1].strip()
    snapshot_str = parts[2].strip()

    if model not in template_encoding_fields:
        skipped_no_template.add(model)
        continue

    try:
        snapshot = json.loads(snapshot_str)
    except json.JSONDecodeError:
        print(f"  ⚠️ 产品 {pid} ({model}): JSON解析失败，跳过")
        continue

    enc_fields = template_encoding_fields[model]
    code_parts = snapshot.get('code_parts', [])

    # 检查是否需要修改
    changes = []
    for part in code_parts:
        field_name = part.get('field_name', '')
        current_use = part.get('use_in_code', False)
        should_use = field_name in enc_fields

        if current_use != should_use:
            changes.append({
                'field_name': field_name,
                'was': current_use,
                'should_be': should_use
            })

    if changes:
        products_to_fix.append({
            'id': pid,
            'model': model,
            'snapshot': snapshot,
            'changes': changes
        })

print(f"  需要修复: {len(products_to_fix)} 个产品")
print(f"  无模版跳过: {len(skipped_no_template)} 个型号 ({', '.join(sorted(skipped_no_template)[:5])}...)")

# ============ Step 3: 预览修改 ============
print()
print("=" * 60)
print("Step 3: 修改预览")
print("=" * 60)

for prod in products_to_fix:
    true_to_false = [c for c in prod['changes'] if c['was'] == True]
    false_to_true = [c for c in prod['changes'] if c['was'] == False]

    print(f"\n  产品 {prod['id']} ({prod['model']}):")
    if true_to_false:
        print(f"    ↓ true→false ({len(true_to_false)}): {', '.join(c['field_name'] for c in true_to_false)}")
    if false_to_true:
        print(f"    ↑ false→true ({len(false_to_true)}): {', '.join(c['field_name'] for c in false_to_true)}")

# ============ Step 4: 执行修复 ============
if DRY_RUN:
    print()
    print("=" * 60)
    print("DRY RUN 模式 - 不执行实际更新")
    print("去掉 --dry-run 参数执行实际修改")
    print("=" * 60)
    sys.exit(0)

if not products_to_fix:
    print("\n无需修复，退出。")
    sys.exit(0)

print()
print("=" * 60)
print("Step 4: 执行修复")
print("=" * 60)

success = 0
failed = 0

for prod in products_to_fix:
    snapshot = prod['snapshot']
    enc_fields = template_encoding_fields[prod['model']]

    # 修正 code_parts
    for part in snapshot.get('code_parts', []):
        field_name = part.get('field_name', '')
        should_use = field_name in enc_fields
        part['use_in_code'] = should_use
        if not should_use:
            # 非编码字段清空 code（与新导入产品格式一致）
            part['code'] = ''

    # 更新来源标记
    snapshot['source'] = snapshot.get('source', '') + '_fixed'

    # 生成 UPDATE SQL
    snapshot_json = json.dumps(snapshot, ensure_ascii=False)
    # 转义单引号
    snapshot_escaped = snapshot_json.replace("'", "''")

    update_sql = f"UPDATE products SET code_definition_snapshot = '{snapshot_escaped}'::json WHERE id = {prod['id']};"

    result = run_sg_sql(update_sql)
    if 'UPDATE 1' in result:
        success += 1
        print(f"  ✅ 产品 {prod['id']} ({prod['model']}) 已更新")
    else:
        failed += 1
        print(f"  ❌ 产品 {prod['id']} ({prod['model']}) 更新失败: {result}")

print()
print(f"完成: 成功 {success}, 失败 {failed}, 总计 {len(products_to_fix)}")
