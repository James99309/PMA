from app import create_app
import inspect
app = create_app()
with app.app_context():
    from app.views.user import manage_user_affiliations
    print('成功导入manage_user_affiliations函数')
    # 查看函数定义
    print('函数源代码:')
    print(inspect.getsource(manage_user_affiliations))
