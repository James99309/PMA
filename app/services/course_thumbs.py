# -*- coding: utf-8 -*-
"""互动课件逐页缩略图生成(Playwright)。

临时起一个本地 http server 服务 course_assets 目录,Playwright 加载 deck、
方向键走 1→N 各截一张,存 <key>.thumbs/<N>.png。best-effort:Playwright/
Chromium 未装则抛错,调用方捕获并把 has_thumbs 留 False。
"""
import functools
import http.server
import logging
import os
import socketserver
import threading

logger = logging.getLogger(__name__)


def generate_thumbnails(key, n_pages, assets_dir, viewport=(1024, 576)):
    """为 key 课件生成 1..n_pages 页缩略图。成功返回张数,失败抛异常。"""
    if n_pages <= 0:
        return 0
    from playwright.sync_api import sync_playwright  # 延迟导入:未装时不影响其它功能

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=assets_dir)
    httpd = socketserver.TCPServer(('127.0.0.1', 0), handler)
    httpd.allow_reuse_address = True
    port = httpd.server_address[1]
    th = threading.Thread(target=httpd.serve_forever, daemon=True)
    th.start()

    out = os.path.join(assets_dir, key + '.thumbs')
    os.makedirs(out, exist_ok=True)
    done = 0
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': viewport[0], 'height': viewport[1]})
            page.goto(f'http://127.0.0.1:{port}/{key}.html', wait_until='load')
            page.wait_for_timeout(1500)
            for i in range(1, n_pages + 1):
                if i > 1:
                    page.keyboard.press('ArrowRight')
                    page.wait_for_timeout(650)
                page.screenshot(path=os.path.join(out, f'{i}.png'))
                done = i
            browser.close()
    finally:
        httpd.shutdown()
        httpd.server_close()
    logger.info('[thumbs] %s 生成 %d 张', key, done)
    return done
