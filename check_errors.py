from app import create_app
import traceback
app = create_app()
with app.app_context():
    try:
        from app.models.user import User
        user = User.query.filter_by(username='shengyh').first()
        if user:
            print(f'找到用户: {user.username}, ID: {user.id}, 角色: {user.role}')
            from app.models.user import Permission
            # 打印用户客户管理模块权限
            permission = Permission.query.filter_by(user_id=user.id, module='customer').first()
            print(f'客户模块个人权限: {permission.__dict__ if permission else "没有个人权限"}')
            # 检查有无被禁用
            print(f'用户是否激活: {user.is_active}')
            # 检查user.has_permission函数
            try:
                has_perm = user.has_permission('customer', 'view')
                print(f'user.has_permission("customer", "view") 结果: {has_perm}')
                # 检查角色权限
                from app.models.role_permissions import RolePermission
                role_perm = RolePermission.query.filter_by(role=user.role, module='customer').first()
                print(f'角色权限: {role_perm.__dict__ if role_perm else "角色没有客户模块权限"}')
            except Exception as e:
                print(f'调用has_permission失败: {str(e)}')
                traceback.print_exc()
        else:
            print('未找到用户shengyh')
    except Exception as e:
        print(f'错误: {str(e)}')
        traceback.print_exc()
