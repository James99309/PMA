from app import create_app
import inspect
app = create_app()
with app.app_context():
    # 查看__init__.py中的context_processor
    from app.__init__ import inject_permissions
    print('成功导入权限注入函数')
    # 查看函数定义
    print('函数源代码:')
    print(inspect.getsource(inject_permissions))
