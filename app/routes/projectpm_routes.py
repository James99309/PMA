from flask import Blueprint
from app.views.projectpm_statistics import projectpm_statistics

# 创建项目管理模块的蓝图
bp = Blueprint('projectpm', __name__, url_prefix='/projectpm')

# 注册项目统计模块的所有路由
bp.register_blueprint(projectpm_statistics, url_prefix='/statistics') 