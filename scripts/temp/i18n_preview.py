#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""i18n 英文预览:以 admin + language=en 渲染指定页面,导出 HTML 供布局/内容确认。
用法: python3 scripts/temp/i18n_preview.py expense.at_list_view[:k=v,...] ...
"""
import sys, os
sys.path.insert(0, os.getcwd())
from app import create_app, db
from app.models.user import User

def main(specs):
    app = create_app()
    app.login_manager.session_protection = None
    with app.app_context():
        admin = User.query.filter_by(role='admin').first() or User.query.filter_by(role='ceo').first()
        if not admin:
            print('无 admin/ceo 用户'); return
        from flask import url_for
        outdir = os.path.join(os.getcwd(), 'i18n_preview')
        os.makedirs(outdir, exist_ok=True)
        client = app.test_client()
        import time
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin.id); sess['_fresh'] = True
            sess['role'] = admin.role; sess['user_id'] = admin.id
            sess['username'] = admin.username; sess['login_time'] = time.time()
            sess['language'] = 'en'
        for spec in specs:
            ep = spec; kw = {}
            if ':' in spec:
                ep, rest = spec.split(':', 1)
                for pair in rest.split(','):
                    if '=' in pair:
                        k, v = pair.split('=', 1); kw[k] = v
            try:
                with app.test_request_context():
                    url = url_for(ep, **kw)
            except Exception as e:
                print(f'  url_for 失败 {ep}: {e}'); continue
            r = client.get(url, follow_redirects=True, headers={'Accept-Language': 'en'})
            fn = os.path.join(outdir, ep.replace('.', '_') + '.html')
            open(fn, 'wb').write(r.data)
            print(f'  [{r.status_code}] {url} -> {fn} ({len(r.data)} bytes)')

if __name__ == '__main__':
    main(sys.argv[1:] or ['expense.at_list_view'])
