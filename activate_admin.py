from app import create_app, db
from app.models import User

def activate_admin_user():
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print(f"开始激活用户 {admin.username}...")
            
            # 检查is_active属性
            if hasattr(admin, 'is_active'):
                # 显示当前状态
                print(f"当前状态: {'正常' if admin.is_active else '禁用'}")
                
                # 激活账户
                admin.is_active = True
                db.session.commit()
                
                # 验证更改
                admin = User.query.filter_by(username='admin').first()
                print(f"更新后状态: {'正常' if admin.is_active else '禁用'}")
                print("用户admin已成功激活！")
            else:
                print("注意: 该用户模型没有is_active属性")
                
                # 尝试通过不同方式激活账户
                try:
                    # 有些模型使用active或者disabled字段
                    if hasattr(admin, 'active'):
                        admin.active = True
                        db.session.commit()
                        print("已通过active字段激活用户")
                    elif hasattr(admin, 'disabled'):
                        admin.disabled = False
                        db.session.commit()
                        print("已通过disabled字段激活用户")
                    else:
                        print("无法确定激活方式，请检查用户模型")
                except Exception as e:
                    print(f"激活过程发生错误: {e}")
                    db.session.rollback()
        else:
            print("admin用户不存在")

if __name__ == "__main__":
    activate_admin_user() 
from app.models import User

def activate_admin_user():
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print(f"开始激活用户 {admin.username}...")
            
            # 检查is_active属性
            if hasattr(admin, 'is_active'):
                # 显示当前状态
                print(f"当前状态: {'正常' if admin.is_active else '禁用'}")
                
                # 激活账户
                admin.is_active = True
                db.session.commit()
                
                # 验证更改
                admin = User.query.filter_by(username='admin').first()
                print(f"更新后状态: {'正常' if admin.is_active else '禁用'}")
                print("用户admin已成功激活！")
            else:
                print("注意: 该用户模型没有is_active属性")
                
                # 尝试通过不同方式激活账户
                try:
                    # 有些模型使用active或者disabled字段
                    if hasattr(admin, 'active'):
                        admin.active = True
                        db.session.commit()
                        print("已通过active字段激活用户")
                    elif hasattr(admin, 'disabled'):
                        admin.disabled = False
                        db.session.commit()
                        print("已通过disabled字段激活用户")
                    else:
                        print("无法确定激活方式，请检查用户模型")
                except Exception as e:
                    print(f"激活过程发生错误: {e}")
                    db.session.rollback()
        else:
            print("admin用户不存在")

if __name__ == "__main__":
    activate_admin_user() 