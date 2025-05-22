#!/usr/bin/env python3
# 修复 ApprovalRecord 表中的 action 字段

from app import create_app, db
from app.models.approval import ApprovalRecord, ApprovalAction
from sqlalchemy.sql import text

def fix_approval_records():
    """直接使用SQL更新字符串值为枚举表示形式"""
    app = create_app()
    with app.app_context():
        conn = db.engine.connect()
        
        try:
            # 获取记录数量
            count_query = text("SELECT COUNT(*) FROM approval_record")
            total_count = conn.execute(count_query).scalar()
            print(f"总记录数: {total_count}")
            
            # 查看action字段内容
            sample_query = text("SELECT DISTINCT action FROM approval_record")
            action_values = [row[0] for row in conn.execute(sample_query)]
            print(f"发现的action值: {action_values}")
            
            # 更新数据
            for enum_obj in ApprovalAction:
                sql_value = enum_obj.value  # 字符串值，如 'approve'
                enum_name = enum_obj.name   # 枚举名称，如 'APPROVE'
                
                update_query = text(f"UPDATE approval_record SET action = '{enum_name}' WHERE action = '{sql_value}'")
                result = conn.execute(update_query)
                conn.commit()
                print(f"已将 {sql_value} 更新为 {enum_name}, 影响 {result.rowcount} 行")
            
            print("数据修复完成")
            
        except Exception as e:
            print(f"出错: {str(e)}")
            conn.rollback()
        finally:
            conn.close()

if __name__ == "__main__":
    fix_approval_records() 