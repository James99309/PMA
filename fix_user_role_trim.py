import psycopg2
from psycopg2.extras import RealDictCursor

# 请根据实际情况修改以下数据库连接信息
DB_URI = "postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d"

def fix_user_role_trim():
    conn = psycopg2.connect(DB_URI)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    print("修复前：")
    cur.execute("SELECT id, username, role FROM users ORDER BY id;")
    users_before = cur.fetchall()
    for u in users_before:
        print(f"id={u['id']}, username={u['username']}, role=<{u['role']}> (len={len(u['role'])})")
    # 执行修复
    cur.execute("UPDATE users SET role = TRIM(role);")
    conn.commit()
    print("\n修复后：")
    cur.execute("SELECT id, username, role FROM users ORDER BY id;")
    users_after = cur.fetchall()
    for u in users_after:
        print(f"id={u['id']}, username={u['username']}, role=<{u['role']}> (len={len(u['role'])})")
    cur.close()
    conn.close()
    print("\n所有用户role字段首尾空格已去除！")

if __name__ == '__main__':
    fix_user_role_trim() 