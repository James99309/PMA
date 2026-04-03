#!/usr/bin/env python3
"""修正产品 snapshot 中的编码字符，与 product_specs.field_code 同步"""
import subprocess, json

fixes = [
    # (NAS, product_id, field_name, old_code, new_code)
    ('CN', 238, '信道间隔', 'W', '4'),
    ('CN', 238, '输出功率', 'U', '6'),
    ('SG', 107, '工作频率', '4', '7'),
    ('SG', 109, '工作频率', '4', 'W'),
]

CN_SSH = "ssh -p 72 -o ConnectTimeout=10 -o BatchMode=yes james.sh@100.118.231.15"
SG_SSH = "ssh -o ConnectTimeout=10 -o BatchMode=yes admin@100.87.155.40"

def run_sql(nas, sql, raw=False):
    if nas == 'CN':
        if raw:
            cmd = f"""{CN_SSH} "sudo /usr/local/bin/docker exec -i pma-postgres psql -U pma pma_synology -t -A" <<'SQLEOF'\n{sql}\nSQLEOF"""
        else:
            cmd = f"""{CN_SSH} "sudo /usr/local/bin/docker exec -i pma-postgres psql -U pma pma_synology" <<'SQLEOF'\n{sql}\nSQLEOF"""
    else:
        if raw:
            cmd = f"""{SG_SSH} "sudo sh -c 'export PATH=/usr/local/bin:\\$PATH && docker exec -i pma-postgres psql -U pma pma_sa -t -A'" <<'SQLEOF'\n{sql}\nSQLEOF"""
        else:
            cmd = f"""{SG_SSH} "sudo sh -c 'export PATH=/usr/local/bin:\\$PATH && docker exec -i pma-postgres psql -U pma pma_sa'" <<'SQLEOF'\n{sql}\nSQLEOF"""
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    return r.stdout.strip()

# Group fixes by (NAS, product_id)
from collections import defaultdict
grouped = defaultdict(list)
for nas, pid, fname, old, new in fixes:
    grouped[(nas, pid)].append((fname, old, new))

for (nas, pid), field_fixes in grouped.items():
    raw = run_sql(nas, f"SELECT code_definition_snapshot::text FROM products WHERE id = {pid};", raw=True)
    if not raw:
        print(f"  ⚠️ [{nas}] 产品{pid}: 无 snapshot")
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
        result = run_sql(nas, f"UPDATE products SET code_definition_snapshot = '{snapshot_json}'::json WHERE id = {pid};")
        fixes_desc = ', '.join(f"{f}: {o}→{n}" for f, o, n in field_fixes)
        if 'UPDATE 1' in result:
            print(f"  ✅ [{nas}] 产品{pid}: snapshot {fixes_desc}")
        else:
            print(f"  ❌ [{nas}] 产品{pid}: 更新失败")
