# -*- coding: utf-8 -*-
"""WikiClaudeClient 连接阶段失败自动重试 1 次(httpx.MockTransport,不连网)。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import httpx
import pytest

from app.services.wiki import claude_client as CC

OK_BODY = {'content': [{'type': 'text', 'text': 'hi'}], 'stop_reason': 'end_turn',
           'usage': {'input_tokens': 1, 'output_tokens': 2}}


def _client(handler, monkeypatch):
    monkeypatch.setattr(CC.time, 'sleep', lambda s: None)      # 不真等 1s
    return CC.WikiClaudeClient(api_key='k', base_url='http://zz.invalid', timeout=30,
                               transport=httpx.MockTransport(handler))


def _seq(*steps):
    calls = []

    def handler(request):
        step = steps[len(calls)]
        calls.append(request)
        if isinstance(step, Exception):
            raise step
        return step
    return handler, calls


def test_connect_timeout_retried_once_then_ok(monkeypatch):
    handler, calls = _seq(httpx.ConnectTimeout('The handshake operation timed out'),
                          httpx.Response(200, json=OK_BODY))
    r = _client(handler, monkeypatch).complete('s', 'u', model='claude-haiku-4-5-20251001')
    assert r.text == 'hi' and len(calls) == 2


def test_connect_error_retried_once_then_ok(monkeypatch):
    handler, calls = _seq(httpx.ConnectError('refused'), httpx.Response(200, json=OK_BODY))
    assert _client(handler, monkeypatch).complete('s', 'u', model='m').text == 'hi'
    assert len(calls) == 2


def test_connect_fails_twice_raises_without_third_try(monkeypatch):
    handler, calls = _seq(httpx.ConnectTimeout('t1'), httpx.ConnectTimeout('t2'),
                          httpx.Response(200, json=OK_BODY))
    with pytest.raises(CC.WikiClaudeError, match='超时'):
        _client(handler, monkeypatch).complete('s', 'u', model='m')
    assert len(calls) == 2


def test_read_timeout_not_retried(monkeypatch):
    handler, calls = _seq(httpx.ReadTimeout('slow'), httpx.Response(200, json=OK_BODY))
    with pytest.raises(CC.WikiClaudeError, match='超时'):
        _client(handler, monkeypatch).complete('s', 'u', model='m')
    assert len(calls) == 1


def test_http_error_not_retried(monkeypatch):
    handler, calls = _seq(httpx.Response(502, text='bad gateway'), httpx.Response(200, json=OK_BODY))
    with pytest.raises(CC.WikiClaudeError, match='HTTP 502'):
        _client(handler, monkeypatch).complete('s', 'u', model='m')
    assert len(calls) == 1


def test_sleeps_one_second_between_attempts(monkeypatch):
    slept = []
    handler, _calls = _seq(httpx.ConnectError('x'), httpx.Response(200, json=OK_BODY))
    c = CC.WikiClaudeClient(api_key='k', base_url='http://zz.invalid', transport=httpx.MockTransport(handler))
    monkeypatch.setattr(CC.time, 'sleep', lambda s: slept.append(s))
    c.complete('s', 'u', model='m')
    assert slept == [CC.CONNECT_RETRY_DELAY] and CC.CONNECT_RETRY_DELAY == 1.0


def test_timeout_config_connect_15_and_read_keeps_timeout():
    c = CC.WikiClaudeClient(api_key='k', base_url='http://zz.invalid', timeout=120)
    t = c._http.timeout
    assert t.connect == 15.0 and t.read == 120 and t.write == 120 and t.pool == 120
    c.close()


def test_short_timeout_caps_connect():
    # 调用方给的总超时比 15s 还短时,连接超时不应被放大
    c = CC.WikiClaudeClient(api_key='k', base_url='http://zz.invalid', timeout=5)
    assert c._http.timeout.connect == 5 and c._http.timeout.read == 5
    c.close()


def test_tls_handshake_timeout_maps_to_connect_timeout():
    """实测报错 `_ssl.c:999: The handshake operation timed out` 来自 ssl.wrap_socket 抛 socket.timeout,
    httpcore 在 start_tls 里把它映射成 ConnectTimeout(与 TCP 连接超时同一类)→ 会被重试。"""
    import inspect
    from httpcore._backends import sync as hsync
    src = inspect.getsource(hsync.SyncStream.start_tls)
    assert 'socket.timeout: ConnectTimeout' in src
    assert issubclass(httpx.ConnectTimeout, httpx.TimeoutException)
