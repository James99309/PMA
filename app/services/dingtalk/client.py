"""钉钉 OpenAPI 客户端 — access_token 缓存 + HTTP 封装。"""
import logging
import threading
import time
from typing import Any, Dict, Optional

import requests

from app.services.dingtalk.config import DingTalkConfig

logger = logging.getLogger(__name__)

OLD_API_BASE = 'https://oapi.dingtalk.com'
NEW_API_BASE = 'https://api.dingtalk.com'

TOKEN_SAFETY_MARGIN_SECONDS = 300


class DingTalkError(Exception):
    """钉钉 API 错误。"""

    def __init__(self, message: str, errcode: Optional[int] = None, payload: Any = None):
        super().__init__(message)
        self.errcode = errcode
        self.payload = payload


class DingTalkClient:
    """线程安全的钉钉客户端（access_token 内存缓存）。"""

    def __init__(self, config: DingTalkConfig, timeout: int = 15):
        if not config.is_valid():
            raise DingTalkError('DingTalkConfig 不完整，请检查 DINGTALK_* 环境变量')
        self.config = config
        self.timeout = timeout
        self._token: Optional[str] = None
        self._token_expire_at: float = 0
        self._token_lock = threading.Lock()

    def get_access_token(self, force_refresh: bool = False) -> str:
        now = time.time()
        if not force_refresh and self._token and now < self._token_expire_at:
            return self._token

        with self._token_lock:
            if not force_refresh and self._token and time.time() < self._token_expire_at:
                return self._token

            url = f'{NEW_API_BASE}/v1.0/oauth2/accessToken'
            resp = requests.post(
                url,
                json={'appKey': self.config.app_key, 'appSecret': self.config.app_secret},
                timeout=self.timeout,
            )
            data = self._parse_json(resp)
            token = data.get('accessToken')
            expire_in = int(data.get('expireIn', 7200))
            if not token:
                raise DingTalkError(f'获取 access_token 失败: {data}', payload=data)
            self._token = token
            self._token_expire_at = time.time() + expire_in - TOKEN_SAFETY_MARGIN_SECONDS
            logger.info('钉钉 access_token 已刷新，有效期 %s 秒', expire_in)
            return token

    def request_old(self, method: str, path: str, params: Optional[Dict] = None,
                    json_body: Optional[Dict] = None) -> Dict:
        """调用旧版 oapi.dingtalk.com（access_token 放 query）。"""
        params = dict(params or {})
        params['access_token'] = self.get_access_token()
        url = f'{OLD_API_BASE}{path}'
        resp = requests.request(method, url, params=params, json=json_body, timeout=self.timeout)
        data = self._parse_json(resp)
        errcode = data.get('errcode')
        if errcode not in (None, 0):
            if errcode in (40001, 42001, 42007):
                logger.warning('access_token 失效，重试一次: %s', data)
                params['access_token'] = self.get_access_token(force_refresh=True)
                resp = requests.request(method, url, params=params, json=json_body, timeout=self.timeout)
                data = self._parse_json(resp)
                errcode = data.get('errcode')
            if errcode not in (None, 0):
                raise DingTalkError(f'钉钉旧API错误: {data.get("errmsg")}', errcode=errcode, payload=data)
        return data

    def request_new(self, method: str, path: str, params: Optional[Dict] = None,
                    json_body: Optional[Dict] = None) -> Dict:
        """调用新版 api.dingtalk.com（access_token 放 header）。"""
        headers = {'x-acs-dingtalk-access-token': self.get_access_token()}
        url = f'{NEW_API_BASE}{path}'
        resp = requests.request(method, url, params=params, json=json_body,
                                headers=headers, timeout=self.timeout)
        if resp.status_code == 401:
            headers['x-acs-dingtalk-access-token'] = self.get_access_token(force_refresh=True)
            resp = requests.request(method, url, params=params, json=json_body,
                                    headers=headers, timeout=self.timeout)
        if resp.status_code >= 400:
            try:
                payload = resp.json()
            except Exception:
                payload = {'raw': resp.text}
            raise DingTalkError(
                f'钉钉新API错误 {resp.status_code}: {payload}',
                errcode=resp.status_code, payload=payload,
            )
        if resp.status_code == 204 or not resp.text:
            return {}
        return self._parse_json(resp)

    @staticmethod
    def _parse_json(resp: requests.Response) -> Dict:
        try:
            return resp.json()
        except ValueError:
            raise DingTalkError(f'钉钉响应非 JSON: {resp.status_code} {resp.text[:200]}')


_client_singleton: Optional[DingTalkClient] = None
_client_lock = threading.Lock()


def get_client() -> DingTalkClient:
    """获取进程级单例客户端。调用前应先用 is_dingtalk_enabled() 判断。"""
    global _client_singleton
    if _client_singleton is not None:
        return _client_singleton
    with _client_lock:
        if _client_singleton is None:
            _client_singleton = DingTalkClient(DingTalkConfig.from_env())
        return _client_singleton


def reset_client() -> None:
    """测试用：重置单例。"""
    global _client_singleton
    with _client_lock:
        _client_singleton = None
