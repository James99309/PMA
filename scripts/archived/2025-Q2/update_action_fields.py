from app import create_app, db
from sqlalchemy import text

# 创建应用实例
app = create_app()

# 在应用上下文中执行
with app.app_context():
    try:
        # 执行SQL语句修改字段为可为空
        db.session.execute(text("ALTER TABLE actions ALTER COLUMN company_id DROP NOT NULL;"))
        db.session.execute(text("ALTER TABLE actions ALTER COLUMN contact_id DROP NOT NULL;"))
        
        # 提交修改
        db.session.commit()
        
        print("已成功更新actions表，company_id和contact_id字段现在允许为空")
    except Exception as e:
        db.session.rollback()
        print(f"更新失败：{str(e)}") 