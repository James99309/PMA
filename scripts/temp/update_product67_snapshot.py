#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""更新产品67的规格快照 - 使用原始SQL绕过ORM schema不匹配"""
import sys, os, json
from datetime import datetime

def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

project_root = get_project_root()
sys.path.insert(0, project_root)

import psycopg2

DB_URL = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

# 获取产品基本信息
cur.execute("""
    SELECT p.id, p.product_mn, p.spec_mn, p.category_id, p.subcategory_id,
           pc.name as cat_name, pc.code_letter as cat_code,
           ps.name as subcat_name, ps.code_letter as subcat_code
    FROM products p
    LEFT JOIN product_categories pc ON p.category_id = pc.id
    LEFT JOIN product_subcategories ps ON p.subcategory_id = ps.id
    WHERE p.id = 67
""")
row = cur.fetchone()
if not row:
    print("❌ 产品67不存在")
    sys.exit(1)

pid, product_mn, spec_mn, cat_id, subcat_id, cat_name, cat_code, subcat_name, subcat_code = row
print(f"产品: {product_mn} (ID={pid})")

# 获取规格数据，按display_order排序
cur.execute("""
    SELECT ps.field_name, ps.field_value, ps.field_code
    FROM product_specs ps
    WHERE ps.product_id = 67
    ORDER BY ps.display_order, ps.id
""")
specs = cur.fetchall()

# 获取SpecDefinition信息用于丰富快照
field_names = [s[0] for s in specs if s[0]]
if field_names:
    cur.execute("""
        SELECT sd.name, sd.unit, sd.display_order, sc.display_order as cat_order
        FROM spec_definitions sd
        LEFT JOIN spec_categories sc ON sd.category_id = sc.id
        WHERE sd.name = ANY(%s)
    """, (field_names,))
    def_rows = cur.fetchall()
    name_to_def = {r[0]: {'unit': r[1], 'def_order': r[2], 'cat_order': r[3]} for r in def_rows}
else:
    name_to_def = {}

# 构建快照
snapshot = {
    "version": "1.0",
    "source": "manual_update",
    "generated_at": datetime.utcnow().isoformat(),
    "full_code": spec_mn or product_mn,
    "category": {
        "id": cat_id,
        "name": cat_name or "",
        "code_letter": cat_code or ""
    },
    "subcategory": {
        "id": subcat_id,
        "name": subcat_name or "",
        "code_letter": subcat_code or ""
    },
    "code_parts": []
}

for idx, (field_name, field_value, field_code) in enumerate(specs):
    defn = name_to_def.get(field_name, {})
    use_in_code = bool(field_code and field_code.strip())
    snapshot["code_parts"].append({
        "position": idx,
        "field_name": field_name,
        "field_code": field_code or "",
        "code": field_code or "",
        "value": field_value or "",
        "use_in_code": use_in_code,
        "unit": defn.get('unit') or ""
    })

# 更新快照到数据库
snapshot_json = json.dumps(snapshot, ensure_ascii=False)
cur.execute("""
    UPDATE products
    SET code_definition_snapshot = %s::jsonb
    WHERE id = 67
""", (snapshot_json,))

conn.commit()
print(f"✅ 快照已更新，包含 {len(snapshot['code_parts'])} 个规格项")

cur.close()
conn.close()
