#!/usr/bin/env python3
# 修改数据库表结构，将 action 列从 enum 类型改为 varchar

from app import create_app, db
from sqlalchemy.sql import text

def alter_action_column():
    """将 approval_record 表的 action 列从 enum 类型改为 varchar"""
    app = create_app()
    with app.app_context():
        conn = db.engine.connect()
        
        try:
            # 开始事务
            conn.begin()
            
            # 创建临时表，复制数据
            # 1. 创建临时表，把 action 列定义为 varchar
            print("正在创建临时表...")
            create_temp_table = text("""
                CREATE TABLE approval_record_temp (
                    id INTEGER PRIMARY KEY,
                    instance_id INTEGER NOT NULL,
                    step_id INTEGER NOT NULL,
                    approver_id INTEGER NOT NULL,
                    action VARCHAR(10) NOT NULL,
                    comment TEXT,
                    timestamp TIMESTAMP
                )
            """)
            conn.execute(create_temp_table)
            
            # 2. 将数据从原表复制到临时表
            print("正在复制数据...")
            copy_data = text("""
                INSERT INTO approval_record_temp
                SELECT id, instance_id, step_id, approver_id, action::varchar, comment, timestamp
                FROM approval_record
            """)
            conn.execute(copy_data)
            
            # 3. 删除原表
            print("正在删除原表...")
            drop_original = text("DROP TABLE approval_record")
            conn.execute(drop_original)
            
            # 4. 将临时表重命名为原始表名
            print("正在重命名临时表...")
            rename_table = text("ALTER TABLE approval_record_temp RENAME TO approval_record")
            conn.execute(rename_table)
            
            # 5. 添加外键约束
            print("正在添加外键约束...")
            add_fk1 = text("""
                ALTER TABLE approval_record 
                ADD CONSTRAINT fk_approval_record_instance_id 
                FOREIGN KEY (instance_id) REFERENCES approval_instance(id)
            """)
            conn.execute(add_fk1)
            
            add_fk2 = text("""
                ALTER TABLE approval_record 
                ADD CONSTRAINT fk_approval_record_step_id
                FOREIGN KEY (step_id) REFERENCES approval_step(id)
            """)
            conn.execute(add_fk2)
            
            add_fk3 = text("""
                ALTER TABLE approval_record 
                ADD CONSTRAINT fk_approval_record_approver_id
                FOREIGN KEY (approver_id) REFERENCES users(id)
            """)
            conn.execute(add_fk3)
            
            # 提交事务
            conn.commit()
            print("表结构修改完成！")
            
        except Exception as e:
            print(f"出错: {str(e)}")
            conn.rollback()
        finally:
            conn.close()

if __name__ == "__main__":
    alter_action_column() 