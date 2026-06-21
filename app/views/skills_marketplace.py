# -*- coding: utf-8 -*-
"""团队 Skills 商店 — 在 PMA 内嵌入 Cowork marketplace 站点。

Blueprint: skills_marketplace  (url_prefix: '')
端点：
    GET /skills-store — Tailwind 前端页面，iframe 内嵌 marketplace.jamesgpone.win

设计要点：
    - 不搬动 marketplace 本体（仍托管在 Mac Mini / marketplace.jamesgpone.win），
      本模块只提供 PMA 内的入口 + 内嵌外壳 + 返回。
    - 语言按 PMA 部署来源(IS_OVS)决定（OVS 海外→en，其余→zh），与 index.html
      仪表盘入口一致。
    - 所有登录用户可见（团队工具），故只用 login_required，不加额外权限门。
"""
from flask import Blueprint, render_template, current_app
from flask_login import login_required

skills_marketplace_bp = Blueprint('skills_marketplace', __name__)

# 团队私有 Skills 商店站点（托管在 Mac Mini，PMA 只内嵌、不搬动）
MARKETPLACE_BASE_URL = 'https://marketplace.jamesgpone.win/'


@skills_marketplace_bp.route('/skills-store')
@login_required
def marketplace_page():
    lang = 'en' if current_app.config.get('IS_OVS') else 'zh'
    marketplace_url = f'{MARKETPLACE_BASE_URL}?lang={lang}'
    return render_template(
        'skills/at_marketplace.html',
        marketplace_url=marketplace_url,
        active_page='skills_marketplace',
    )
