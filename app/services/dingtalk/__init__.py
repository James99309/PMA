"""钉钉集成服务

仅在 CN (PMA_DB_TYPE=sp8d) 且 DINGTALK_ENABLED=true 时启用。
提供 access_token 管理、日程 CRUD、用户映射等能力。
"""
from app.services.dingtalk.config import DingTalkConfig, is_dingtalk_enabled
from app.services.dingtalk.client import DingTalkClient, DingTalkError, get_client

__all__ = [
    'DingTalkConfig',
    'DingTalkClient',
    'DingTalkError',
    'is_dingtalk_enabled',
    'get_client',
]
