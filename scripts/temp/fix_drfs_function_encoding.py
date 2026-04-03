#!/usr/bin/env python3
"""修复 SG NAS DRFS-400/M 产品18和73的 snapshot：
1. 功能字段加入编码 (use_in_code=true)
2. 产品73: 字段名 光模块接收灵敏度→光接收灵敏度
3. field_code 与字典对齐
"""
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

for pid in [18, 73]:
    raw = run_sg_raw(f"SELECT code_definition_snapshot::text FROM products WHERE id = {pid};")
    if not raw:
        print(f"  ⚠️ 产品{pid}: 无 snapshot")
        continue

    snapshot = json.loads(raw)
    changed = False

    for part in snapshot.get('code_parts', []):
        # 产品73: 统一字段名
        if part.get('field_name') == '光模块接收灵敏度':
            part['field_name'] = '光接收灵敏度'
            part['field_name_en'] = 'Optical RX Sensitivity'
            changed = True

        # 功能字段: 设为编码字段
        if part.get('field_name') == '功能':
            if not part.get('use_in_code'):
                part['use_in_code'] = True
                changed = True
            # 修正 code
            if pid == 18 and part.get('value') == 'None':
                part['code'] = '4'
                part['field_code'] = '4'
                changed = True
            elif pid == 73 and part.get('value') == 'Power Backup':
                part['code'] = 'E'
                part['field_code'] = 'E'
                changed = True

    if changed:
        snapshot_json = json.dumps(snapshot, ensure_ascii=False).replace("'", "''")
        result = run_sg_exec(f"UPDATE products SET code_definition_snapshot = '{snapshot_json}'::json WHERE id = {pid};")
        if 'UPDATE 1' in result:
            print(f"  ✅ 产品{pid}: snapshot 已更新")
        else:
            print(f"  ❌ 产品{pid}: 更新失败: {result}")
    else:
        print(f"  ⏭️ 产品{pid}: 无需更新")
