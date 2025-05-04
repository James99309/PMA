from app import create_app, db
from app.models import User

def check_admin_user():
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print(f"用户ID: {admin.id}")
            print(f"用户名: {admin.username}")
            print(f"角色: {admin.role}")
            print(f"密码哈希: {admin.password_hash[:30]}...")
            if hasattr(admin, 'is_active'):
                print(f"登录状态: {'正常' if admin.is_active else '禁用'}")
        else:
            print("admin用户不存在")

if __name__ == "__main__":
    check_admin_user() 
from app.models import User

def check_admin_user():
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print(f"用户ID: {admin.id}")
            print(f"用户名: {admin.username}")
            print(f"角色: {admin.role}")
            print(f"密码哈希: {admin.password_hash[:30]}...")
            if hasattr(admin, 'is_active'):
                print(f"登录状态: {'正常' if admin.is_active else '禁用'}")
        else:
            print("admin用户不存在")

if __name__ == "__main__":
    check_admin_user() 