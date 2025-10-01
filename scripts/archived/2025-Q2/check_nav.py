from app import create_app
from flask import render_template, render_template_string, current_app
from flask_login import current_user
import sys

app = create_app()
with app.app_context():
    # 定义一个测试页面的HTML输出用户菜单权限
    print('正在检查has_permission函数...')
    from app.__init__ import has_permission
    print('has_permission函数成功导入')
    print(f'函数内容: {has_permission.__code__}')
