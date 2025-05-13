from app import create_app
from app.models.user import User, Permission
from app.models.role_permissions import RolePermission

app = create_app()
with app.app_context():
    user = User.query.filter_by(username='shengyh').first()
    print(f'用户信息: ID={user.id if user else None}, 角色={user.role if user else None}')
    
    # 查询用户的个人权限
    if user:
        permissions = Permission.query.filter_by(user_id=user.id, module='customer').first()
        print(f'个人权限: {permissions.__dict__ if permissions else "无个人权限"}')
        
        # 查询角色权限
        role_permissions = RolePermission.query.filter_by(role=user.role, module='customer').first()
        print(f'角色权限: {role_permissions.__dict__ if role_permissions else "无角色权限"}')
