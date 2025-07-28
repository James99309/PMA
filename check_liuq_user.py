#!/usr/bin/env python3
"""
检查liuq用户的详细信息
直接读取数据库来检查用户角色和权限
"""

import sqlite3
import os

def check_user_from_db():
    """从数据库直接检查用户信息"""
    
    # 可能的数据库文件位置
    possible_db_paths = [
        'instance/app.db',
        'app.db', 
        'database.db',
        'pma.db'
    ]
    
    db_path = None
    for path in possible_db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ 未找到数据库文件")
        print("请确认数据库文件位置，常见位置:")
        for path in possible_db_paths:
            print(f"   - {path}")
        return
    
    print(f"📁 使用数据库文件: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查用户表结构
        cursor.execute("PRAGMA table_info(user)")
        user_columns = cursor.fetchall()
        print(f"📋 用户表结构: {[col[1] for col in user_columns]}")
        
        # 查找liuq用户
        cursor.execute("SELECT id, username, role, real_name FROM user WHERE username = 'liuq'")
        user_data = cursor.fetchone()
        
        if user_data:
            user_id, username, role, real_name = user_data
            print(f"\n👤 找到liuq用户:")
            print(f"   ID: {user_id}")
            print(f"   用户名: {username}")
            print(f"   角色: {role}")
            print(f"   真实姓名: {real_name}")
            
            # 检查权限表结构
            cursor.execute("PRAGMA table_info(permission)")
            perm_columns = cursor.fetchall()
            print(f"\n📋 权限表结构: {[col[1] for col in perm_columns]}")
            
            # 查找用户的所有权限
            cursor.execute("""
                SELECT module, can_view, can_create, can_edit, can_delete 
                FROM permission 
                WHERE user_id = ?
                ORDER BY module
            """, (user_id,))
            
            permissions = cursor.fetchall()
            print(f"\n🔒 liuq用户的所有权限 ({len(permissions)} 个模块):")
            
            has_performance_perm = False
            for perm in permissions:
                module, can_view, can_create, can_edit, can_delete = perm
                print(f"   {module:20} | 查看: {can_view} | 创建: {can_create} | 编辑: {can_edit} | 删除: {can_delete}")
                
                if module == 'performance_management':
                    has_performance_perm = True
                    if can_view:
                        print(f"   ✅ 有绩效管理查看权限")
                    else:
                        print(f"   ❌ 无绩效管理查看权限")
            
            if not has_performance_perm:
                print(f"\n❌ 未找到performance_management权限记录")
                print(f"   这就是liuq用户无法看到绩效看板的原因！")
                
                # 检查是否有其他用户有performance_management权限
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM permission 
                    WHERE module = 'performance_management'
                """)
                perm_count = cursor.fetchone()[0]
                print(f"   系统中共有 {perm_count} 个performance_management权限记录")
                
                if perm_count == 0:
                    print(f"   💡 建议：需要为所有用户添加performance_management权限模块")
        else:
            print("❌ 未找到liuq用户")
            
            # 显示所有用户
            cursor.execute("SELECT username, role, real_name FROM user LIMIT 10")
            all_users = cursor.fetchall()
            print(f"\n📋 数据库中的用户 (前10个):")
            for user in all_users:
                print(f"   {user[0]:15} | {user[1]:15} | {user[2] or 'N/A'}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 数据库查询失败: {str(e)}")

def main():
    """主函数"""
    print("🔍 检查liuq用户的详细信息...")
    print("=" * 60)
    
    check_user_from_db()

if __name__ == '__main__':
    main()