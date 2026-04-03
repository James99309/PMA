#!/usr/bin/env python3
"""批量修正产品规格的 display_order，按 CN 模版顺序对齐"""
import subprocess, json

CN_SSH = "ssh -p 72 -o ConnectTimeout=10 -o BatchMode=yes james.sh@100.118.231.15"
SG_SSH = "ssh -o ConnectTimeout=10 -o BatchMode=yes admin@100.87.155.40"

def run_sql(nas, sql, raw=True):
    if nas == 'CN':
        if raw:
            cmd = f"""{CN_SSH} "sudo /usr/local/bin/docker exec -i pma-postgres psql -U pma pma_synology -t -A -F'|'" <<'SQLEOF'\n{sql}\nSQLEOF"""
        else:
            cmd = f"""{CN_SSH} "sudo /usr/local/bin/docker exec -i pma-postgres psql -U pma pma_synology" <<'SQLEOF'\n{sql}\nSQLEOF"""
    else:
        if raw:
            cmd = f"""{SG_SSH} "sudo sh -c 'export PATH=/usr/local/bin:\\$PATH && docker exec -i pma-postgres psql -U pma pma_sa -t -A -F\\\"|\\\"\'" <<'SQLEOF'\n{sql}\nSQLEOF"""
        else:
            cmd = f"""{SG_SSH} "sudo sh -c 'export PATH=/usr/local/bin:\\$PATH && docker exec -i pma-postgres psql -U pma pma_sa'" <<'SQLEOF'\n{sql}\nSQLEOF"""
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    return r.stdout.strip()

# ============ Step 1: 从 CN 加载所有模版的 field_name → display_order 映射 ============
print("Step 1: 加载 CN 模版排序")
tmpl_raw = run_sql('CN', """
SELECT st.model, sd.name, sti.display_order
FROM spec_template_items sti
JOIN spec_templates st ON sti.template_id = st.id
JOIN specification_dictionary sd ON sti.spec_dict_id = sd.id
WHERE st.deleted_at IS NULL
ORDER BY st.model, sti.display_order;
""")

# model → {field_name: display_order}
template_orders = {}
for line in tmpl_raw.split('\n'):
    if not line.strip(): continue
    parts = line.split('|')
    if len(parts) != 3: continue
    model, field_name, order = parts[0].strip(), parts[1].strip(), int(parts[2].strip())
    if model not in template_orders:
        template_orders[model] = {}
    template_orders[model][field_name] = order

print(f"  已加载 {len(template_orders)} 个模版的排序定义")

# ============ Step 2: 对每个 NAS 批量更新 ============
for nas_label in ['CN', 'SG']:
    db = 'pma_synology' if nas_label == 'CN' else 'pma_sa'
    print(f"\n{'='*60}")
    print(f"Step 2: 修正 {nas_label} NAS 产品规格排序")
    print(f"{'='*60}")

    # 获取所有产品及其 model
    products_raw = run_sql(nas_label, """
SELECT p.id, p.model FROM products p WHERE p.is_deleted = false AND p.model IS NOT NULL ORDER BY p.model, p.id;
""")

    products = []
    for line in products_raw.split('\n'):
        if not line.strip(): continue
        parts = line.split('|')
        if len(parts) == 2:
            products.append((int(parts[0].strip()), parts[1].strip()))

    updated_products = 0
    updated_specs = 0
    skipped_no_template = 0

    for pid, model in products:
        order_map = template_orders.get(model)
        if not order_map:
            skipped_no_template += 1
            continue

        # 构建批量 UPDATE SQL
        # 对每个 field_name 设置 display_order，模版没有的放到最后（999+原顺序）
        cases = []
        for field_name, order in order_map.items():
            escaped = field_name.replace("'", "''")
            cases.append(f"WHEN field_name = '{escaped}' THEN {order}")

        if not cases:
            continue

        sql = f"""
UPDATE product_specs SET display_order = CASE
    {chr(10).join(f'    {c}' for c in cases)}
    ELSE 900 + id % 100
END
WHERE product_id = {pid};
"""
        result = run_sql(nas_label, sql, raw=False)
        if 'UPDATE' in result:
            count = int(result.split('UPDATE ')[1]) if 'UPDATE ' in result else 0
            if count > 0:
                updated_products += 1
                updated_specs += count

    print(f"  更新: {updated_products} 个产品, {updated_specs} 条规格")
    print(f"  跳过（无模版）: {skipped_no_template} 个产品")

print("\n完成！")
