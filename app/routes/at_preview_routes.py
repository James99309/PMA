# -*- coding: utf-8 -*-
"""
AT 设计系统预览页(开发期临时路由)

用于:
  - 第 1 阶段:验证 at-theme.css + at_base.html 基础组件在浏览器跑通
  - 后续阶段:展示新增的 AT 组件,便于回归

URL: /at-preview
"""
from flask import Blueprint, render_template

at_preview_bp = Blueprint('at_preview', __name__, url_prefix='/at-preview')


@at_preview_bp.route('/')
def index():
    return render_template('at_preview/index.html')
