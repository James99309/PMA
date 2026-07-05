# -*- coding: utf-8 -*-
"""
中国地区官网预览页(测试用途)

用于在 PMA 内部预览来自 Claude Design 的官网首页设计稿。
- 需登录访问(login_required),不对外公开暴露
- 纯静态托管:HTML/JS/CSS/图片/视频均从 app/website_cn_preview/ 目录读取
- 内部锚点/相对链接沿用设计稿原样(部分二级页尚未导入,点击会 404)

入口:
  /website-preview/cn/                       -> 首页(Evertac官网首页.dc.html)
  /website-preview/cn/<path>                 -> 站点内任意静态资源
"""
import os
from flask import Blueprint, send_from_directory, abort
from flask_login import login_required

website_preview_bp = Blueprint('website_preview', __name__, url_prefix='/website-preview')

# 站点根目录:app/website_cn_preview/
_SITE_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'website_cn_preview')

# 首页文件名(含中文,单独常量便于维护)
_INDEX_FILE = 'Evertac官网首页.dc.html'


@website_preview_bp.route('/cn/')
@login_required
def cn_home():
    """中国官网首页"""
    return send_from_directory(_SITE_ROOT, _INDEX_FILE)


@website_preview_bp.route('/cn/<path:filename>')
@login_required
def cn_asset(filename):
    """站点内静态资源(dc.html 子页、support.js、mobile.css、assets/*)"""
    # send_from_directory 已做安全路径校验,防止越界访问
    full = os.path.join(_SITE_ROOT, filename)
    if not os.path.isfile(full):
        abort(404)
    return send_from_directory(_SITE_ROOT, filename)
