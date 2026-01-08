#!/usr/bin/env python3
import psycopg2

DB_URL = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

conn = psycopg2.connect(DB_URL)
cursor = conn.cursor()

tonglei_id = 18
lihuawei_id = 15

# 1. 获取同部门同公司的用户
print("=== 1. 同部门同公司的用户 ===")
cursor.execute("""
    SELECT id, username, real_name
    FROM users
    WHERE department = '销售部' AND company_name = '和源通信（上海）股份有限公司'
""")
dept_users = cursor.fetchall()
dept_user_ids = []
for u in dept_users:
    dept_user_ids.append(u[0])
    print(f"  ID={u[0]}, {u[2]}({u[1]})")
print(f"\n  部门用户ID列表: {dept_user_ids}")
print(f"  包含lihuawei(15): {15 in dept_user_ids}")

# 2. 加上归属关系
print("\n=== 2. 加上归属关系后 ===")
cursor.execute("SELECT owner_id FROM affiliations WHERE viewer_id = %s", (tonglei_id,))
aff_ids = [row[0] for row in cursor.fetchall()]
all_ids = list(set(dept_user_ids + aff_ids))
print(f"  归属关系ID: {aff_ids}")
print(f"  合并后ID列表: {all_ids}")
print(f"  包含lihuawei(15): {15 in all_ids}")

# 3. 查询项目277
print("\n=== 3. 项目277查询 ===")
ids_str = ','.join(str(x) for x in all_ids)
cursor.execute(f"""
    SELECT id, project_name, owner_id
    FROM projects
    WHERE owner_id IN ({ids_str})
      AND id = 277
""")
result = cursor.fetchone()
if result:
    print(f"  ✓ 找到项目: {result}")
else:
    print(f"  ✗ 未找到项目277")
    # 检查项目277的owner_id
    cursor.execute("SELECT owner_id FROM projects WHERE id = 277")
    owner = cursor.fetchone()
    print(f"  项目277的owner_id = {owner[0] if owner else 'N/A'}")
    if owner:
        print(f"  owner_id {owner[0]} 在ID列表中: {owner[0] in all_ids}")

cursor.close()
conn.close()
