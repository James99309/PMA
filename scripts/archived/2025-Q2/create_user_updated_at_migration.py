from app import create_app, db
from flask_migrate import upgrade, migrate
 
app = create_app()
with app.app_context():
    migrate(message="add updated_at to user")
    upgrade()
    print("数据库迁移已完成：users表已添加updated_at字段") 