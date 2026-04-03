#!/usr/bin/env python3
"""完整审计：CN/SG NAS 产品编码与 CN 规格字典一致性"""
import subprocess, json

CN_SSH = "ssh -p 72 -o ConnectTimeout=10 -o BatchMode=yes james.sh@100.118.231.15"
SG_SSH = "ssh -o ConnectTimeout=10 -o BatchMode=yes admin@100.87.155.40"

def run_sql(nas, sql):
    if nas == 'CN':
        cmd = f"""{CN_SSH} "sudo /usr/local/bin/docker exec -i pma-postgres psql -U pma pma_synology -t -A -F'|'" <<'SQLEOF'\n{sql}\nSQLEOF"""
    else:
        cmd = f"""{SG_SSH} "sudo sh -c 'export PATH=/usr/local/bin:\\$PATH && docker exec -i pma-postgres psql -U pma pma_sa -t -A -F\\\"|\\\"\'" <<'SQLEOF'\n{sql}\nSQLEOF"""
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    return r.stdout.strip()

# ============ 加载 CN 字典 ============
print("加载 CN 规格字典...")
dict_raw = run_sql('CN', """
SELECT sd.name, so.value, so.code
FROM specification_options so
JOIN specification_dictionary sd ON so.spec_id = sd.id;
""")
cn_dict = {}
for line in dict_raw.split('\n'):
    if not line.strip(): continue
    parts = line.split('|')
    if len(parts) == 3:
        cn_dict[(parts[0], parts[1])] = parts[2]
print(f"  共 {len(cn_dict)} 条映射\n")

# ============ 加载 CN 模版编码字段 ============
tmpl_raw = run_sql('CN', """
SELECT st.model, sd.name
FROM spec_template_items sti
JOIN spec_templates st ON sti.template_id = st.id
JOIN specification_dictionary sd ON sti.spec_dict_id = sd.id
WHERE sti.use_in_code = true AND st.deleted_at IS NULL;
""")
cn_templates = {}  # model → set(field_names)
for line in tmpl_raw.split('\n'):
    if not line.strip(): continue
    parts = line.split('|')
    if len(parts) == 2:
        cn_templates.setdefault(parts[0], set()).add(parts[1])

for nas_label, nas_key in [('CN', 'CN'), ('SG', 'SG')]:
    db = 'pma_synology' if nas_key == 'CN' else 'pma_sa'
    print("=" * 60)
    print(f"审计 {nas_label} NAS")
    print("=" * 60)

    # ---- 审计1: 新产品 MN vs 配置 ----
    if nas_key == 'CN':
        mn_mismatch = run_sql(nas_key, """
            SELECT p.id, p.model, p.product_mn, pc.mn_code
            FROM products p
            JOIN product_configurations pc ON p.source_configuration_id = pc.id
            WHERE p.is_deleted = false AND pc.deleted_at IS NULL AND p.product_mn != pc.mn_code
            ORDER BY p.model;
        """)
        print("\n[1] 新产品 MN vs 配置:")
        if mn_mismatch:
            for line in mn_mismatch.split('\n'):
                if line.strip():
                    p = line.split('|')
                    print(f"  ❌ 产品{p[0]} ({p[1]}): product_mn={p[2]} ≠ config={p[3]}")
        else:
            print("  ✅ 全部一致")

    # ---- 审计2: snapshot 编码字段 code vs 字典 ----
    snapshot_data = run_sql(nas_key, """
        SELECT p.id, p.model, p.product_mn,
               elem->>'field_name', elem->>'value', elem->>'code'
        FROM products p,
             json_array_elements(p.code_definition_snapshot->'code_parts') elem
        WHERE p.is_deleted = false
          AND p.code_definition_snapshot IS NOT NULL
          AND (elem->>'use_in_code')::boolean = true
          AND elem->>'code' != '';
    """)

    print(f"\n[2] Snapshot 编码字段 vs 字典:")
    snap_issues = []
    for line in snapshot_data.split('\n'):
        if not line.strip(): continue
        parts = line.split('|')
        if len(parts) != 6: continue
        pid, model, mn, fname, fval, scode = [p.strip() for p in parts]
        dict_code = cn_dict.get((fname, fval))
        if dict_code is None:
            snap_issues.append(f"  ⚠️  产品{pid} ({model}): {fname}={fval}, code={scode}, 字典无此值")
        elif dict_code != scode:
            snap_issues.append(f"  ❌ 产品{pid} ({model}): {fname}={fval}, snapshot={scode}, 字典={dict_code}")

    if snap_issues:
        for s in snap_issues:
            print(s)
    else:
        print("  ✅ 全部一致")

    # ---- 审计3: field_code vs snapshot code ----
    fc_vs_snap = run_sql(nas_key, """
        SELECT p.id, p.model, ps.field_name, ps.field_code,
               (SELECT elem->>'code' FROM json_array_elements(p.code_definition_snapshot->'code_parts') elem
                WHERE elem->>'field_name' = ps.field_name AND (elem->>'use_in_code')::boolean = true LIMIT 1)
        FROM products p
        JOIN product_specs ps ON ps.product_id = p.id
        WHERE p.is_deleted = false
          AND p.code_definition_snapshot IS NOT NULL
          AND ps.field_code IS NOT NULL AND ps.field_code != '';
    """)

    print(f"\n[3] field_code vs snapshot code:")
    fc_issues = []
    for line in fc_vs_snap.split('\n'):
        if not line.strip(): continue
        parts = line.split('|')
        if len(parts) != 5: continue
        pid, model, fname, fc, sc = [p.strip() for p in parts]
        if sc and fc != sc:
            fc_issues.append(f"  ❌ 产品{pid} ({model}): {fname}, field_code={fc}, snapshot={sc}")

    if fc_issues:
        for f in fc_issues:
            print(f)
    else:
        print("  ✅ 全部一致")

    # ---- 审计4: snapshot use_in_code vs 模版 ----
    if nas_key == 'SG':
        print(f"\n[4] Snapshot use_in_code vs CN 模版:")
        uic_data = run_sql(nas_key, """
            SELECT p.id, p.model,
                   elem->>'field_name', (elem->>'use_in_code')::boolean
            FROM products p,
                 json_array_elements(p.code_definition_snapshot->'code_parts') elem
            WHERE p.is_deleted = false
              AND p.code_definition_snapshot IS NOT NULL
              AND (elem->>'use_in_code')::boolean = true
              AND elem->>'code' != '';
        """)
        uic_issues = []
        for line in uic_data.split('\n'):
            if not line.strip(): continue
            parts = line.split('|')
            if len(parts) != 4: continue
            pid, model, fname, uic = [p.strip() for p in parts]
            tmpl_fields = cn_templates.get(model, None)
            if tmpl_fields is not None and fname not in tmpl_fields:
                uic_issues.append(f"  ❌ 产品{pid} ({model}): {fname} use_in_code=true 但模版中非编码")
        if uic_issues:
            for u in uic_issues:
                print(u)
        else:
            print("  ✅ 全部一致")

    print()
