#!/usr/bin/env python3
"""PMA 自托管 OTA 独立服务 —— 与测试环境完全解耦。

为什么独立: Capgo 平台数据面冻结后改自托管。最初把 ota 逻辑放在 Mac mini
的 pma-test 测试 Flask (:5099) 里图快, 但 App 里烧死的 updateUrl 指向
pma-test.jamesgpone.win, 一旦删测试实例就会搞挂全员 OTA。本服务把 OTA
拆成纯 stdlib、零依赖、launchd 常驻的独立进程, 删任何测试环境都不受影响。

部署 (Mac mini):
  /Users/jing/pma-ota/ota_server.py        本脚本
  /Users/jing/pma-ota/bundles/             bundle zip + latest.json
  ~/Library/LaunchAgents/win.jamesgpone.pma-ota.plist  launchd 常驻
  cloudflared: pma-test.jamesgpone.win → http://localhost:5111

协议同 @capgo/capacitor-updater 自托管规范 (与原 app/api/v1/ota.py 一致)。
"""
import os
import re
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BUNDLE_DIR = os.environ.get('OTA_BUNDLE_DIR', '/Users/jing/pma-ota/bundles')
PUBLIC_BASE = os.environ.get('OTA_PUBLIC_BASE', 'https://pma-test.jamesgpone.win').rstrip('/')
PORT = int(os.environ.get('OTA_PORT', '5111'))
_SAFE_ZIP = re.compile(r'^[A-Za-z0-9._-]+\.zip$')


def _latest():
    """读 latest.json, 缺失/损坏返回 None。"""
    p = os.path.join(BUNDLE_DIR, 'latest.json')
    try:
        with open(p, encoding='utf-8') as f:
            d = json.load(f)
        return d if d.get('version') and d.get('file') else None
    except Exception:
        return None


class Handler(BaseHTTPRequestHandler):
    server_version = 'pma-ota/1.0'

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _no_content(self):
        self.send_response(200)
        self.send_header('Content-Length', '0')
        self.end_headers()

    def _channel(self):
        self._json(200, {'status': 'ok', 'channel': 'production',
                         'allowSet': False, 'message': '', 'error': ''})

    def do_GET(self):
        path = self.path.split('?', 1)[0]
        if path == '/healthz':
            return self._json(200, {'ok': True})
        m = re.match(r'^/api/v1/ota/bundles/(.+)$', path)
        if m:
            fn = m.group(1)
            fp = os.path.join(BUNDLE_DIR, fn)
            if not _SAFE_ZIP.match(fn) or not os.path.isfile(fp):
                return self._json(404, {'error': 'not_found'})
            with open(fp, 'rb') as f:
                data = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'application/zip')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Content-Disposition', f'attachment; filename="{fn}"')
            self.send_header('Cache-Control', 'private, max-age=3600')
            self.end_headers()
            self.wfile.write(data)
            return
        self._json(404, {'error': 'not_found'})

    def do_PUT(self):
        if self.path.split('?', 1)[0] == '/api/v1/ota/channel_self':
            return self._channel()
        self._json(404, {'error': 'not_found'})

    def do_POST(self):
        path = self.path.split('?', 1)[0]
        ln = int(self.headers.get('Content-Length') or 0)
        body = self.rfile.read(ln) if ln else b''
        if path == '/api/v1/ota/stats':
            return self._no_content()
        if path == '/api/v1/ota/channel_self':
            return self._channel()
        if path == '/api/v1/ota/updates':
            try:
                info = json.loads(body or b'{}')
            except Exception:
                info = {}
            dev = (info.get('version_name') or '').strip()
            lt = _latest()
            if not lt:
                return self._json(200, {'version': dev or 'builtin',
                                        'message': 'NO_UPDATES'})
            if dev == lt['version']:
                return self._json(200, {'version': lt['version'],
                                        'message': 'NO_UPDATES'})
            if not os.path.isfile(os.path.join(BUNDLE_DIR, lt['file'])):
                return self._json(200, {'version': dev or 'builtin',
                                        'message': 'NO_UPDATES'})
            resp = {'version': lt['version'],
                    'url': f"{PUBLIC_BASE}/api/v1/ota/bundles/{lt['file']}"}
            if lt.get('checksum'):
                resp['checksum'] = lt['checksum']
            return self._json(200, resp)
        self._json(404, {'error': 'not_found'})

    def log_message(self, fmt, *args):
        import sys
        sys.stderr.write('%s %s\n' % (self.address_string(), fmt % args))


if __name__ == '__main__':
    os.makedirs(BUNDLE_DIR, exist_ok=True)
    ThreadingHTTPServer(('127.0.0.1', PORT), Handler).serve_forever()
