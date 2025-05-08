from app import create_app, db
from app.models.user import User, Permission

app = create_app()
with app.app_context():
    user = User.query.filter_by(username='NIJIE').first()
    if user:
        # 删除所有 product_code 权限
        Permission.query.filter_by(user_id=user.id, module='product_code').delete()
        db.session.commit()
        # 新建一条明确禁止的权限
        p = Permission(user_id=user.id, module='product_code', can_view=False, can_create=False, can_edit=False, can_delete=False)
        db.session.add(p)
        db.session.commit()
        print('已修复 NIJIE 的 product_code 权限为不可见')
    else:
        print('未找到用户名为 NIJIE 的用户') 