#!/usr/bin/env python3
# 修复 approval_record 表的主键自增序列

from app import create_app, db
from sqlalchemy.sql import text

def fix_approval_record_sequence():
    """修复 approval_record 表的主键自增序列"""
    app = create_app()
    with app.app_context():
        conn = db.engine.connect()
        
        try:
            # 开始事务
            trans = conn.begin()
            
            # 1. 检查序列是否存在
            check_seq = text("SELECT EXISTS (SELECT 1 FROM pg_sequences WHERE schemaname = 'public' AND sequencename = 'approval_record_id_seq')")
            seq_exists = conn.execute(check_seq).scalar()
            
            if not seq_exists:
                print("需要创建序列 approval_record_id_seq")
                # 创建序列
                create_seq = text("CREATE SEQUENCE approval_record_id_seq START 1")
                conn.execute(create_seq)
                print("序列已创建")
            else:
                print("序列 approval_record_id_seq 已存在")
            
            # 2. 将主键列设置为使用序列
            print("正在修复主键...")
            alter_pk = text("""
                ALTER TABLE approval_record 
                ALTER COLUMN id SET DEFAULT nextval('approval_record_id_seq')
            """)
            conn.execute(alter_pk)
            
            # 3. 更新序列值为当前最大ID+1
            update_seq = text("""
                SELECT setval('approval_record_id_seq', COALESCE((SELECT MAX(id) FROM approval_record), 0) + 1, false)
            """)
            conn.execute(update_seq)
            
            # 提交事务
            trans.commit()
            print("表结构修复完成！")
            
        except Exception as e:
            print(f"出错: {str(e)}")
            trans.rollback()
        finally:
            conn.close()

if __name__ == "__main__":
    fix_approval_record_sequence() 