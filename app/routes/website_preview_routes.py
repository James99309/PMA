# -*- coding: utf-8 -*-
"""官网预览页(测试用途)

用于在 PMA 内部预览来自 Claude Design 的官网设计稿。
- 需登录访问(login_required),不对外公开暴露
- 纯静态托管:HTML/JS/CSS/图片/视频均从 app/website_<lang>_preview/ 目录读取
- 内部锚点/相对链接沿用设计稿原样(部分二级页尚未导入,点击会 404)

入口:
  /website-preview/cn/  -> 中文站首页(Evertac官网首页.dc.html)
  /website-preview/en/  -> 英文站首页(EN-Home.dc.html)
  /website-preview/<lang>/<path> -> 站点内任意静态资源

仪表盘通栏入口按实例区域选择语言:OVS(新加坡)→ en,其余 → cn。
"""
import os
from flask import Blueprint, send_from_directory, abort, current_app
from flask_login import login_required

website_preview_bp = Blueprint('website_preview', __name__, url_prefix='/website-preview')

_APP_DIR = os.path.dirname(os.path.dirname(__file__))

# 各语言站点:目录名 + 首页文件名(含中文/自定义命名,集中在此便于维护)
_SITES = {
    'cn': ('website_cn_preview', 'Evertac官网首页.dc.html'),
    'en': ('website_en_preview', 'EN-Home.dc.html'),
}


def _site_root(lang):
    """语言 → 站点根目录;未知语言直接 404,不做路径拼接"""
    site = _SITES.get(lang)
    if not site:
        abort(404)
    return os.path.join(_APP_DIR, site[0])


@website_preview_bp.app_context_processor
def inject_website_preview():
    """给模板:本实例该看哪个站 + 该站资产是否真在本机。

    站点快照不进 git(每份 140M+),按区域单独投放到各自 NAS:
    CN 只有中文站、SG 只有英文站。因此入口必须先确认资产存在,
    否则某台缺资产时点进去就是 404。资产投放见 deploy/sync-website-preview.sh。
    """
    lang = 'en' if current_app.config.get('IS_OVS') else 'cn'
    dirname, index_file = _SITES[lang]
    available = os.path.isfile(os.path.join(_APP_DIR, dirname, index_file))
    return {'website_preview_lang': lang, 'website_preview_available': available}


@website_preview_bp.route('/<lang>/')
@login_required
def home(lang):
    """官网首页(中/英)"""
    if lang not in _SITES:
        abort(404)
    return send_from_directory(_site_root(lang), _SITES[lang][1])


@website_preview_bp.route('/<lang>/<path:filename>')
@login_required
def asset(lang, filename):
    """站点内静态资源(dc.html 子页、support.js、mobile.css、assets/*)"""
    root = _site_root(lang)
    # send_from_directory 已做安全路径校验,防止越界访问
    if not os.path.isfile(os.path.join(root, filename)):
        abort(404)
    return send_from_directory(root, filename)
