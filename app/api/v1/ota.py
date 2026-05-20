# -*- coding: utf-8 -*-
"""
自托管 OTA 端点 —— 取代 plugin.capgo.app

为什么自建: Capgo 平台数据面对本 app 整体冻结在一个已删 bundle 上
(GitHub Cap-go/capgo#2068 / #1879), 管理面任何改动都不传播到设备真正
访问的 plugin.capgo.app, 用户侧无任何 API/CLI 能自愈。改为本服务托管。

协议依据: @capgo/capacitor-updater 8.x 自托管规范
  - POST /api/v1/ota/updates       getLatest, 返回 {version,url,checksum} 或 {version,message}
  - GET  /api/v1/ota/bundles/<f>   静态 zip 下发
  - POST /api/v1/ota/stats         no-op (插件不解析响应体)
  - POST|PUT /api/v1/ota/channel_self  单线生产, 常量响应

bundle 存储: <项目根>/ota_bundles/  (可用环境变量 OTA_BUNDLE_DIR 覆盖)
  - latest.json: {"version": "...", "checksum": "<zip sha256 hex>", "file": "pma-<version>.zip"}
  - pma-<version>.zip: dist 平铺打包 (index.html 在根), 无 .DS_Store/__MACOSX

无 @jwt_required: 设备在登录前由 updater 插件调用, 必须公开。
整个 api_v1_bp 已在 app/__init__.py 做 csrf.exempt, 本模块自动豁免。
"""
import os
import json
import logging

from flask import request, jsonify, send_from_directory, current_app
from werkzeug.utils import secure_filename

from app.api.v1 import api_v1_bp

logger = logging.getLogger(__name__)

# 对外可达的 HTTPS 基址 (Cloudflare Tunnel 域名, iOS ATS 要求有效证书)。
# 内网 Flask 看到的 host 是 localhost:5099, 不能用来拼下载地址, 故用此显式基址。
OTA_PUBLIC_BASE = os.environ.get(
    'OTA_PUBLIC_BASE', 'https://pma-test.jamesgpone.win'
).rstrip('/')


def _bundle_dir():
    """bundle 存储目录, 不存在则创建。"""
    d = os.environ.get('OTA_BUNDLE_DIR')
    if not d:
        # current_app.root_path = .../<root>/app, 上一层是项目根
        d = os.path.join(os.path.dirname(current_app.root_path), 'ota_bundles')
    os.makedirs(d, exist_ok=True)
    return d


def _read_latest():
    """读 latest.json, 缺失/损坏返回 None。"""
    path = os.path.join(_bundle_dir(), 'latest.json')
    if not os.path.isfile(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not data.get('version') or not data.get('file'):
            return None
        return data
    except (ValueError, OSError) as e:
        logger.error('[OTA] latest.json 读取失败: %s', e)
        return None


@api_v1_bp.route('/ota/updates', methods=['POST'])
def ota_updates():
    """getLatest: 设备上报当前 version_name, 比对决定是否下发新 bundle。

    成功(有更新):  {version, url, checksum}
    无更新:         {version, message: "NO_UPDATES"}  (插件据此静默跳过)
    """
    info = request.get_json(silent=True) or {}
    device_ver = (info.get('version_name') or '').strip()  # 'builtin' 或 上次 bundle 版本
    app_id = info.get('app_id', '')
    device_id = info.get('device_id', '')

    latest = _read_latest()
    if not latest:
        logger.info('[OTA] 无 latest.json, app_id=%s dev=%s 当前=%s -> NO_UPDATES',
                     app_id, device_id, device_ver)
        return jsonify({'version': device_ver or 'builtin',
                        'message': 'NO_UPDATES'})

    latest_ver = latest['version']
    zip_name = latest['file']
    zip_path = os.path.join(_bundle_dir(), zip_name)

    # 版本名相同 = 已是最新; zip 实体不存在 = 不能下发(防白屏回滚)
    if device_ver == latest_ver:
        return jsonify({'version': latest_ver, 'message': 'NO_UPDATES'})
    if not os.path.isfile(zip_path):
        logger.error('[OTA] latest 指向的 zip 不存在: %s', zip_path)
        return jsonify({'version': device_ver or 'builtin',
                        'message': 'NO_UPDATES'})

    resp = {
        'version': latest_ver,
        'url': f'{OTA_PUBLIC_BASE}/api/v1/ota/bundles/{zip_name}',
    }
    if latest.get('checksum'):
        resp['checksum'] = latest['checksum']
    logger.info('[OTA] 下发更新 app_id=%s dev=%s %s -> %s',
                app_id, device_id, device_ver or 'builtin', latest_ver)
    return jsonify(resp)


@api_v1_bp.route('/ota/bundles/<path:filename>', methods=['GET'])
def ota_bundle_file(filename):
    """静态下发 bundle zip。仅允许 .zip, secure_filename 防目录穿越。"""
    safe = secure_filename(filename)
    if not safe.endswith('.zip'):
        return jsonify({'error': 'not_found'}), 404
    bundle_dir = _bundle_dir()
    if not os.path.isfile(os.path.join(bundle_dir, safe)):
        return jsonify({'error': 'not_found'}), 404
    return send_from_directory(bundle_dir, safe, mimetype='application/zip',
                               as_attachment=True)


@api_v1_bp.route('/ota/stats', methods=['POST'])
def ota_stats():
    """统计上报 no-op —— 插件不解析响应体, 200 即可。"""
    return '', 200


@api_v1_bp.route('/ota/channel_self', methods=['POST', 'PUT'])
def ota_channel_self():
    """单线生产, 不用多 channel。setChannel/getChannel 一律常量成功。"""
    return jsonify({
        'status': 'ok',
        'channel': 'production',
        'allowSet': False,
        'message': '',
        'error': '',
    })
