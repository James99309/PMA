"""钉钉事件回调加解密 + 签名验证。

参考: https://open.dingtalk.com/document/orgapp/callbacks-interface

加密协议:
- AES-256-CBC + PKCS7 填充
- AESKey 是 43 字符 Base64 字符串，需补 '=' 后 decode 成 32 字节
- IV = AESKey 解码后的前 16 字节
- 明文 = 16字节随机 + 4字节消息长度(big-endian) + 消息内容 + 应用标识(corp_id 或 suite_key)

签名:
- sorted([token, timestamp, nonce, encrypt]) 拼接后取 sha1
"""
import base64
import hashlib
import logging
import os
import struct
from typing import Tuple

from Crypto.Cipher import AES

logger = logging.getLogger(__name__)


class DingTalkCryptoError(Exception):
    pass


def _decode_aes_key(aes_key_b64: str) -> bytes:
    if len(aes_key_b64) != 43:
        raise DingTalkCryptoError(f'AESKey 必须是 43 字符，实际 {len(aes_key_b64)}')
    raw = base64.b64decode(aes_key_b64 + '=')
    if len(raw) != 32:
        raise DingTalkCryptoError(f'AESKey decode 后必须 32 字节，实际 {len(raw)}')
    return raw


def _pkcs7_pad(data: bytes, block_size: int = 32) -> bytes:
    pad_len = block_size - (len(data) % block_size)
    return data + bytes([pad_len]) * pad_len


def _pkcs7_unpad(data: bytes) -> bytes:
    pad_len = data[-1]
    if pad_len < 1 or pad_len > 32:
        raise DingTalkCryptoError(f'非法 PKCS7 padding 长度: {pad_len}')
    return data[:-pad_len]


def calc_signature(token: str, timestamp: str, nonce: str, encrypt: str) -> str:
    """计算钉钉签名 = sha1(sorted([token,timestamp,nonce,encrypt]).join(''))"""
    parts = sorted([token, timestamp, nonce, encrypt])
    return hashlib.sha1(''.join(parts).encode('utf-8')).hexdigest()


def encrypt(plaintext: str, aes_key_b64: str, app_key: str) -> str:
    """加密返回 base64 字符串。app_key 即应用 AppKey（自建应用）或 corp_id。"""
    key = _decode_aes_key(aes_key_b64)
    iv = key[:16]

    random_prefix = os.urandom(16)
    msg_bytes = plaintext.encode('utf-8')
    msg_len = struct.pack('>I', len(msg_bytes))
    raw = random_prefix + msg_len + msg_bytes + app_key.encode('utf-8')
    padded = _pkcs7_pad(raw)

    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(padded)
    return base64.b64encode(encrypted).decode('utf-8')


def decrypt(encrypted_b64: str, aes_key_b64: str) -> Tuple[str, str]:
    """解密返回 (明文 JSON 字符串, 应用标识)。"""
    key = _decode_aes_key(aes_key_b64)
    iv = key[:16]

    encrypted = base64.b64decode(encrypted_b64)
    if len(encrypted) % 32 != 0:
        raise DingTalkCryptoError(f'密文长度不是 32 倍数: {len(encrypted)}')

    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(encrypted)
    raw = _pkcs7_unpad(decrypted)

    if len(raw) < 20:
        raise DingTalkCryptoError(f'解密内容过短: {len(raw)}')
    msg_len = struct.unpack('>I', raw[16:20])[0]
    if 20 + msg_len > len(raw):
        raise DingTalkCryptoError(f'消息长度异常 msg_len={msg_len} total={len(raw)}')
    msg = raw[20:20 + msg_len].decode('utf-8')
    app_id = raw[20 + msg_len:].decode('utf-8')
    return msg, app_id


def verify_and_decrypt(token: str, aes_key_b64: str,
                       signature: str, timestamp: str, nonce: str,
                       encrypted_b64: str, expected_app_key: str = None) -> str:
    """验签 + 解密一站式。返回明文 JSON 字符串。"""
    expected_sig = calc_signature(token, timestamp, nonce, encrypted_b64)
    if expected_sig != signature:
        raise DingTalkCryptoError(f'签名不匹配 expected={expected_sig} got={signature}')
    msg, app_id = decrypt(encrypted_b64, aes_key_b64)
    if expected_app_key and app_id != expected_app_key:
        logger.warning('AppKey/CorpId 不匹配 expected=%s got=%s', expected_app_key, app_id)
    return msg


def build_success_response(token: str, aes_key_b64: str, app_key: str,
                           timestamp: str, nonce: str) -> dict:
    """构造钉钉规范的 success 响应 dict（JSON 序列化后返回给钉钉）。"""
    encrypted = encrypt('success', aes_key_b64, app_key)
    sig = calc_signature(token, timestamp, nonce, encrypted)
    return {
        'msg_signature': sig,
        'timeStamp': timestamp,
        'nonce': nonce,
        'encrypt': encrypted,
    }
