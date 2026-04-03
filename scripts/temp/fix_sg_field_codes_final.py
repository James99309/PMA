#!/usr/bin/env python3
"""批量修正 SG NAS 产品的 field_code 和 snapshot，对齐 CN 规格字典"""
import subprocess, json
from collections import defaultdict

SG_SSH = "ssh -o ConnectTimeout=10 -o BatchMode=yes admin@100.87.155.40"
SG_DB = "pma_sa"

def run_sg_raw(sql):
    cmd = f"""{SG_SSH} "sudo sh -c 'export PATH=/usr/local/bin:\\$PATH && docker exec -i pma-postgres psql -U pma {SG_DB} -t -A'" <<'SQLEOF'\n{sql}\nSQLEOF"""
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    return r.stdout.strip()

def run_sg_exec(sql):
    cmd = f"""{SG_SSH} "sudo sh -c 'export PATH=/usr/local/bin:\\$PATH && docker exec -i pma-postgres psql -U pma {SG_DB}'" <<'SQLEOF'\n{sql}\nSQLEOF"""
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    return r.stdout.strip()

# ============ 修正清单 ============
# (product_id, field_name, field_value, old_code, new_code)
fixes = [
    # 输入电压(AC) 110V±15%: 1→4
    (71, '输入电压(AC)', '110V±15%', '1', '4'),
    (72, '输入电压(AC)', '110V±15%', '1', '4'),
    # 外形尺寸 430×300×150: 5→9
    (74, '外形尺寸', '430  × 300 × 150', '5', '9'),
    # 耦合度: 1→7, 5→9, 2→A
    (29, '耦合度', '10', '1', '7'),
    (30, '耦合度', '15', '5', '9'),
    (31, '耦合度', '20', '2', 'A'),
    (35, '耦合度', '10', '1', '7'),
    (36, '耦合度', '15', '5', '9'),
    (37, '耦合度', '20', '2', 'A'),
    # Mark1000 MAX: 信道数量 1→4, 输出功率 2→6
    (1, '信道数量', '16', '1', '4'),
    (1, '输出功率', '25', '2', '6'),
    # MNR3500: 信道间隔 1→4
    (97, '信道间隔', '12.5/25', '1', '4'),
]

# E-ANTO EX (24): 无 CN 模版，所有编码字段应改为 use_in_code=false
anto_ex_fix = 24

# ============ Step 1: 修 field_code ============
print("Step 1: 修正 product_specs.field_code")
for pid, fname, fval, old_code, new_code in fixes:
    escaped_val = fval.replace("'", "''")
    result = run_sg_exec(
        f"UPDATE product_specs SET field_code = '{new_code}' "
        f"WHERE product_id = {pid} AND field_name = '{fname}' AND field_code = '{old_code}';"
    )
    if 'UPDATE 1' in result:
        print(f"  ✅ 产品{pid}: {fname} {old_code}→{new_code}")
    else:
        print(f"  ❌ 产品{pid}: {fname} 更新失败: {result}")

# ============ Step 2: 修 snapshot ============
print("\nStep 2: 修正 snapshot")
grouped = defaultdict(list)
for pid, fname, fval, old_code, new_code in fixes:
    grouped[pid].append((fname, old_code, new_code))

for pid, field_fixes in grouped.items():
    raw = run_sg_raw(f"SELECT code_definition_snapshot::text FROM products WHERE id = {pid};")
    if not raw:
        print(f"  ⚠️ 产品{pid}: 无 snapshot")
        continue

    snapshot = json.loads(raw)
    changed = False
    for fname, old_code, new_code in field_fixes:
        for part in snapshot.get('code_parts', []):
            if part.get('field_name') == fname and part.get('code') == old_code:
                part['code'] = new_code
                part['field_code'] = new_code
                changed = True
                break

    if changed:
        snapshot_json = json.dumps(snapshot, ensure_ascii=False).replace("'", "''")
        result = run_sg_exec(f"UPDATE products SET code_definition_snapshot = '{snapshot_json}'::json WHERE id = {pid};")
        desc = ', '.join(f"{f}: {o}→{n}" for f, o, n in field_fixes)
        if 'UPDATE 1' in result:
            print(f"  ✅ 产品{pid}: {desc}")
        else:
            print(f"  ❌ 产品{pid}: 更新失败")

# ============ Step 3: E-ANTO EX (24) snapshot 修正 ============
print("\nStep 3: E-ANTO EX (24) - 无 CN 模版，编码字段全改 use_in_code=false")
raw = run_sg_raw(f"SELECT code_definition_snapshot::text FROM products WHERE id = {anto_ex_fix};")
if raw:
    snapshot = json.loads(raw)
    changed = False
    for part in snapshot.get('code_parts', []):
        if part.get('use_in_code') == True:
            part['use_in_code'] = False
            part['code'] = ''
            part['field_code'] = ''
            changed = True
    if changed:
        snapshot_json = json.dumps(snapshot, ensure_ascii=False).replace("'", "''")
        result = run_sg_exec(f"UPDATE products SET code_definition_snapshot = '{snapshot_json}'::json WHERE id = {anto_ex_fix};")
        if 'UPDATE 1' in result:
            print(f"  ✅ 产品24: 所有编码字段改为 use_in_code=false")
        else:
            print(f"  ❌ 产品24: 更新失败")

print("\n完成！")
