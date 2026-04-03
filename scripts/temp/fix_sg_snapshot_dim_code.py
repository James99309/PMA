#!/usr/bin/env python3
"""修复 SG NAS 产品 111/112 的 snapshot 中外形尺寸 code 7→8"""
import subprocess, json

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

for pid in [111, 112]:
    raw = run_sg_raw(f"SELECT code_definition_snapshot::text FROM products WHERE id = {pid};")
    if not raw:
        print(f"  ⚠️ 产品 {pid}: 无 snapshot")
        continue

    snapshot = json.loads(raw)
    changed = False
    for part in snapshot.get('code_parts', []):
        if part.get('field_name') == '外形尺寸' and part.get('code') == '7':
            part['code'] = '8'
            part['field_code'] = '8'
            changed = True

    if changed:
        # 更新 full_code
        new_mn = run_sg_raw(f"SELECT product_mn FROM products WHERE id = {pid};")
        snapshot['full_code'] = new_mn

        snapshot_json = json.dumps(snapshot, ensure_ascii=False).replace("'", "''")
        result = run_sg_exec(f"UPDATE products SET code_definition_snapshot = '{snapshot_json}'::json WHERE id = {pid};")
        if 'UPDATE 1' in result:
            print(f"  ✅ 产品 {pid} snapshot: 外形尺寸 code 7→8, full_code→{new_mn}")
        else:
            print(f"  ❌ 产品 {pid} 更新失败: {result}")
    else:
        print(f"  ⏭️ 产品 {pid} 无需更新")
