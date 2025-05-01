"""添加display_order列到product_subcategories表

这个脚本用于向product_subcategories表添加display_order列，
并将现有position列的值复制到新列中。
"""

from app import create_app, db
import sqlite3

app = create_app()

def add_display_order_column():
    """向product_subcategories表添加display_order列"""
    try:
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        # 检查列是否存在
        cursor.execute("PRAGMA table_info(product_subcategories)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'display_order' not in columns:
            print("添加列：product_subcategories.display_order (INTEGER)")
            cursor.execute("ALTER TABLE product_subcategories ADD COLUMN display_order INTEGER DEFAULT 0")
            
            # 复制position列的值到display_order列
            cursor.execute("UPDATE product_subcategories SET display_order = position")
            
            conn.commit()
            print("成功添加display_order列并复制数据")
        else:
            print("列 display_order 已存在，跳过")
            
        conn.close()
        return True
    except Exception as e:
        print(f"添加列失败: {str(e)}")
        return False

if __name__ == "__main__":
    with app.app_context():
        print("开始添加display_order列...")
        add_display_order_column()
        print("迁移完成，请重启应用程序") 