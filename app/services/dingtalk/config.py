"""钉钉集成配置 — 从环境变量读取，双重门禁（CN only + 开关）。"""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DingTalkConfig:
    corp_id: str
    agent_id: str
    app_key: str
    app_secret: str
    callback_token: str = ''
    callback_aes_key: str = ''

    @classmethod
    def from_env(cls) -> 'DingTalkConfig':
        return cls(
            corp_id=os.environ.get('DINGTALK_CORP_ID', ''),
            agent_id=os.environ.get('DINGTALK_AGENT_ID', ''),
            app_key=os.environ.get('DINGTALK_APP_KEY', ''),
            app_secret=os.environ.get('DINGTALK_APP_SECRET', ''),
            callback_token=os.environ.get('DINGTALK_CALLBACK_TOKEN', ''),
            callback_aes_key=os.environ.get('DINGTALK_CALLBACK_AES_KEY', ''),
        )

    def is_valid(self) -> bool:
        return bool(self.corp_id and self.app_key and self.app_secret)

    def has_callback(self) -> bool:
        return bool(self.callback_token and self.callback_aes_key)


def is_dingtalk_enabled() -> bool:
    """钉钉集成启用判定：必须同时满足 CN 数据库 + 显式开关 + 凭证完整。"""
    db_type = (os.environ.get('PMA_DB_TYPE') or os.environ.get('SUPABASE_DB_TYPE', '')).lower()
    if db_type != 'sp8d':
        return False
    if os.environ.get('DINGTALK_ENABLED', '').lower() not in ('true', '1', 'yes'):
        return False
    return DingTalkConfig.from_env().is_valid()
