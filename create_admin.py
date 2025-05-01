from app import create_app, db
from app.models.user import User

app = create_app()

with app.app_context():
    # 检查用户是否已存在
    if not User.query.filter_by(username='admin').first():
        user = User(username='admin')
        user.set_password('admin123')
        db.session.add(user)
        db.session.commit()
        print('管理员用户创建成功！')
    else:
        print('管理员用户已存在！') 