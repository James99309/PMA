from app import create_app
from flask import Flask, render_template_string
from flask_login import login_user
from jinja2 import Template
app = create_app()
with app.app_context():
    from app.models.user import User
    # 从数据库获取shengyh用户
    user = User.query.filter_by(username='shengyh').first()
    # 确认用户存在
    if user:
        print(f'找到用户 {user.username}, ID: {user.id}, 角色: {user.role}')
        # 创建一个简单模板测试权限
        test_template = '{{ has_permission("customer", "view") }}'
        # 使用模板引擎渲染
        from flask import _request_ctx_stack
        # 设置用户环境
        login_user(user)
        # 创建调试变量
        debug_vars = {}
        template_factory = app.jinja_env.from_string(test_template)
        # 必须在请求环境中进行测试
        print('尝试测试模板渲染...')
        with app.test_request_context('/'):
            login_user(user)
            result = template_factory.render()
            print(f'用户 {user.username} 的客户模块查看权限: {result}')
    else:
        print('未找到用户 shengyh')
