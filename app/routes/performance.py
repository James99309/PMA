from app.views.performance import performance_bp
from flask import current_app

def register_performance_routes(app):
    """注册绩效相关路由"""
    app.register_blueprint(performance_bp) 