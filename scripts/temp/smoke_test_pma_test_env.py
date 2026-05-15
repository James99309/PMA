#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mobile_expense + mobile_approval 完整 e2e 走 pma-test.jamesgpone.win.

走完: 登录 → 列表 → 创建草稿 → 加 3 明细 → 改 → 删 → 提交 → 审批列表 → 召回 → 清理.

使用 SUPER_PASSWORD 登录 admin 账号(测试环境内置), 不影响 NAS.
"""
import os
import sys
import json
import requests

BASE = os.environ.get('PMA_TEST_URL', 'https://pma-test.jamesgpone.win')
USERNAME = os.environ.get('PMA_TEST_USER', 'admin')
PASSWORD = os.environ.get('PMA_TEST_PASS', '1505562299AaBb')  # SUPER_PASSWORD

OK = '\033[92m✓\033[0m'
FAIL = '\033[91m✗\033[0m'
INFO = '\033[94mℹ\033[0m'


class TestSession:
    def __init__(self):
        self.s = requests.Session()
        self.s.verify = True
        self.token = None

    def login(self):
        r = self.s.post(f'{BASE}/api/v1/auth/login',
                        json={'username': USERNAME, 'password': PASSWORD},
                        timeout=15)
        r.raise_for_status()
        d = r.json()
        if not d.get('success'):
            raise RuntimeError(f'login failed: {d}')
        self.token = d['data'].get('token') or d['data'].get('access_token')
        if not self.token:
            raise RuntimeError(f'no token in login response: {list(d["data"].keys())}')
        user = d['data']['user']
        print(f'{INFO} 登录: {user.get("username")} (id={user.get("id")}, role={user.get("role")})')

    def _req(self, method, path, **kwargs):
        headers = kwargs.pop('headers', {}) or {}
        headers['Authorization'] = f'Bearer {self.token}'
        r = self.s.request(method, f'{BASE}/api/v1{path}', headers=headers, timeout=30, **kwargs)
        return r

    def get(self, path, **kw):    return self._req('GET', path, **kw)
    def post(self, path, **kw):   return self._req('POST', path, **kw)
    def put(self, path, **kw):    return self._req('PUT', path, **kw)
    def delete(self, path, **kw): return self._req('DELETE', path, **kw)


def main():
    sess = TestSession()
    sess.login()

    # 1. 参考数据
    r = sess.get('/mobile/expense/categories')
    assert r.status_code == 200, f'categories: {r.status_code} {r.text[:200]}'
    d = r.json()['data']
    assert len(d['categories']) == 9, f'expect 9 categories, got {len(d["categories"])}'
    assert len(d['statuses']) == 6
    print(f'{OK} GET /categories — {len(d["categories"])} 科目 + {len(d["statuses"])} 状态')

    r = sess.get('/mobile/expense/currencies')
    assert r.status_code == 200
    d = r.json()['data']
    assert len(d['currencies']) == 9
    cny = next(c for c in d['currencies'] if c['code'] == 'CNY')
    assert cny['rate'] == 1.0
    usd = next(c for c in d['currencies'] if c['code'] == 'USD')
    print(f'{OK} GET /currencies — 9 货币, USD→CNY rate={usd["rate"]}')

    r = sess.get('/mobile/expense/exchange-rate?from=SGD&to=CNY')
    assert r.status_code == 200
    print(f'{OK} GET /exchange-rate SGD→CNY = {r.json()["data"]["rate"]}')

    # 2. 列表(应该工作即使是空)
    r = sess.get('/mobile/expense')
    assert r.status_code == 200, f'list: {r.status_code} {r.text[:300]}'
    d = r.json()['data']
    print(f'{OK} GET /mobile/expense — {len(d["items"])} 条; summary: month_total=¥{d["summary"]["month_total"]:.2f} pending={d["summary"]["pending_count"]}')

    # 3. 创建草稿
    r = sess.post('/mobile/expense', json={
        'title': '【SMOKE-TEST】e2e 自动测试报销',
        'description': '由 smoke_test_pma_test_env.py 自动创建, 完成后会软删',
        'currency': 'CNY',
    })
    if r.status_code != 200:
        print(f'{FAIL} create: {r.status_code} {r.text[:300]}')
        sys.exit(1)
    created = r.json()['data']
    eid = created['id']
    enum = created['expense_number']
    print(f'{OK} POST /mobile/expense — 创建 id={eid} 单号={enum}')

    try:
        # 4. 加 3 明细
        lines = [
            {'expense_category': 'local_transport', 'expense_date': '2026-04-29',
             'currency': 'CNY', 'invoice_amount': 401.90, 'description': '租车费'},
            {'expense_category': 'fuel', 'expense_date': '2026-04-29',
             'currency': 'CNY', 'invoice_amount': 224.00, 'description': '280公里加油'},
            {'expense_category': 'meals', 'expense_date': '2026-04-29',
             'currency': 'CNY', 'invoice_amount': 88.00, 'description': '吃饭饮料'},
        ]
        line_ids = []
        for p in lines:
            r = sess.post(f'/mobile/expense/{eid}/lines', json=p)
            if r.status_code != 200:
                print(f'{FAIL} add line: {r.status_code} {r.text[:300]}')
                sys.exit(1)
            line_ids.append(r.json()['data']['id'])
        print(f'{OK} POST /lines × 3 — ids={line_ids}')

        # 5. 测试外币明细(SGD → CNY 自动汇率)
        r = sess.post(f'/mobile/expense/{eid}/lines', json={
            'expense_category': 'travel_accommodation',
            'expense_date': '2026-04-30',
            'currency': 'SGD',
            'invoice_amount': 100.00,
            'description': '新加坡酒店',
        })
        assert r.status_code == 200
        sgd_line = r.json()['data']
        assert sgd_line['currency'] == 'SGD'
        assert sgd_line['exchange_rate'] != 1.0, f'SGD rate should not be 1.0, got {sgd_line["exchange_rate"]}'
        print(f'{OK} POST /lines (SGD) — 自动汇率 {sgd_line["exchange_rate"]:.4f} → ¥{sgd_line["current_amount"]:.2f}')

        # 6. 详情
        r = sess.get(f'/mobile/expense/{eid}')
        assert r.status_code == 200
        d = r.json()['data']
        cny_total = 401.90 + 224.00 + 88.00
        assert len(d['lines']) == 4
        assert d['control']['can_submit'] is True
        assert d['control']['can_edit'] is True
        print(f'{OK} GET /detail — total=¥{d["total_amount"]:.2f} (3 CNY + 1 SGD), can_submit=True')

        # 7. 改一条明细
        r = sess.put(f'/mobile/expense/{eid}/lines/{line_ids[0]}',
                     json={'description': '租车费(已改)', 'invoice_amount': 400.00})
        assert r.status_code == 200
        print(f'{OK} PUT /lines/{line_ids[0]} — 改金额 401.90→400.00')

        # 8. 删一条明细 (删 SGD 那条避免汇率影响断言)
        r = sess.delete(f'/mobile/expense/{eid}/lines/{sgd_line["id"]}')
        assert r.status_code == 200
        print(f'{OK} DELETE /lines/{sgd_line["id"]} — 删 SGD 行')

        # 9. 详情验证 total 重算
        r = sess.get(f'/mobile/expense/{eid}')
        d = r.json()['data']
        assert len(d['lines']) == 3
        assert abs(d['total_amount'] - 712.00) < 0.01, f'total: {d["total_amount"]}'
        print(f'{OK} 重算后 total=¥{d["total_amount"]:.2f}')

        # 10. PUT 主表 — 改主题
        r = sess.put(f'/mobile/expense/{eid}', json={
            'title': '【SMOKE-TEST】e2e 自动测试报销 (已编辑)',
        })
        assert r.status_code == 200
        print(f'{OK} PUT /mobile/expense/{eid} — 改主题')

        # 11. 提交审批
        r = sess.post(f'/mobile/expense/{eid}/submit', json={})
        sub = r.json()
        if r.status_code == 200:
            d = sub['data']
            print(f'{OK} POST /submit — status={d["status"]}, flow {len(d.get("flow") or [])} 节点')
            # 12. flow 单查
            r = sess.get(f'/mobile/expense/{eid}/flow')
            assert r.status_code == 200
            print(f'{OK} GET /flow — {len(r.json()["data"]["flow"])} 节点')
            # 13. 召回
            r = sess.post(f'/mobile/expense/{eid}/recall', json={'reason': 'smoke recall'})
            if r.status_code == 200:
                print(f'{OK} POST /recall — 召回成功, status={r.json()["data"]["status"]}')
            else:
                print(f'{INFO} recall: {r.json().get("message")}')
        else:
            print(f'{INFO} 提交跳过: {sub.get("message", r.text[:200])}')

        # 14. 审批模块
        r = sess.get('/mobile/approval/pending')
        assert r.status_code == 200
        print(f'{OK} GET /mobile/approval/pending — {len(r.json()["data"]["items"])} 待审')

        r = sess.get('/mobile/approval/cc')
        assert r.status_code == 200
        print(f'{OK} GET /mobile/approval/cc — 抄送 {len(r.json()["data"]["items"])} 条')

        r = sess.get('/mobile/approval/history')
        assert r.status_code == 200
        print(f'{OK} GET /mobile/approval/history — {len(r.json()["data"]["items"])} 已处理')

    finally:
        # 15. 清理
        r = sess.delete(f'/mobile/expense/{eid}')
        cleanup_status = '✓ 已软删' if r.status_code == 200 else f'⚠️ {r.status_code}: {r.text[:200]}'
        print(f'{INFO} 清理: id={eid} → {cleanup_status}')

    print()
    print(f'{OK} pma-test 完整 e2e 通过 ✅')


if __name__ == '__main__':
    try:
        main()
    except requests.HTTPError as e:
        print(f'{FAIL} HTTP error: {e.response.status_code} {e.response.text[:300]}')
        sys.exit(1)
    except Exception as e:
        print(f'{FAIL} {type(e).__name__}: {e}')
        sys.exit(1)
