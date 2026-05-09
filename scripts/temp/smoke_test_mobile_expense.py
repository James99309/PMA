#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mobile_expense + mobile_approval 路由 + 序列化层 smoke test.

不依赖 DB(因本地 schema 落后于 model 中的 cross_team 字段, 跑全 DB e2e 需要先
flask db upgrade). 验证范围:
  1) 所有 17 个 mobile_expense 路由注册成功
  2) 所有 6 个 mobile_approval 路由注册成功
  3) 所有 OCR / 序列化辅助函数 import 干净
  4) status_block / category 字典数据完整
"""
import os
import sys

def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

OK = '\033[92m✓\033[0m'
FAIL = '\033[91m✗\033[0m'
INFO = '\033[94mℹ\033[0m'


def main():
    from app import create_app
    app = create_app()
    with app.app_context():
        # 1) 验证 mobile_expense 路由注册
        expense_routes = sorted([
            (str(r), ','.join(sorted(r.methods - {'OPTIONS', 'HEAD'})))
            for r in app.url_map.iter_rules()
            if '/mobile/expense' in str(r)
        ])
        expected_expense = {
            '/api/v1/mobile/expense':                               {'GET', 'POST'},
            '/api/v1/mobile/expense/<int:expense_id>':              {'GET', 'PUT', 'DELETE'},
            '/api/v1/mobile/expense/<int:expense_id>/lines':        {'POST'},
            '/api/v1/mobile/expense/<int:expense_id>/lines/<int:line_id>': {'PUT', 'DELETE'},
            '/api/v1/mobile/expense/<int:expense_id>/submit':       {'POST'},
            '/api/v1/mobile/expense/<int:expense_id>/recall':       {'POST'},
            '/api/v1/mobile/expense/<int:expense_id>/resubmit':     {'POST'},
            '/api/v1/mobile/expense/<int:expense_id>/flow':         {'GET'},
            '/api/v1/mobile/expense/categories':                    {'GET'},
            '/api/v1/mobile/expense/currencies':                    {'GET'},
            '/api/v1/mobile/expense/exchange-rate':                 {'GET'},
            '/api/v1/mobile/expense/upload-invoice':                {'POST'},
        }
        actual_expense = {}
        for rule_str, methods in expense_routes:
            actual_expense.setdefault(rule_str, set()).update(methods.split(','))
        missing = []
        for path, expected_methods in expected_expense.items():
            actual_methods = actual_expense.get(path, set())
            if not expected_methods.issubset(actual_methods):
                missing.append(f'{path}: expected {expected_methods}, got {actual_methods}')
        if missing:
            print(f'{FAIL} mobile_expense 缺路由:')
            for m in missing: print(f'  - {m}')
            sys.exit(1)
        print(f'{OK} mobile_expense — {len(expected_expense)} 路由全部注册 ({sum(len(m) for m in expected_expense.values())} 方法)')

        # 2) 验证 mobile_approval 路由注册
        approval_routes = sorted([str(r) for r in app.url_map.iter_rules() if '/mobile/approval' in str(r)])
        expected_approval = [
            '/api/v1/mobile/approval/<int:instance_id>',
            '/api/v1/mobile/approval/<int:instance_id>/action',
            '/api/v1/mobile/approval/<int:instance_id>/forward',
            '/api/v1/mobile/approval/cc',
            '/api/v1/mobile/approval/history',
            '/api/v1/mobile/approval/pending',
        ]
        for path in expected_approval:
            assert path in approval_routes, f'{path} 未注册'
        print(f'{OK} mobile_approval — {len(expected_approval)} 路由全部注册')

        # 3) OCR 服务 import
        from app.services.claude_vision_ocr import extract_with_schema, detect_image_type, detect_prefer_lang
        from app.services.business_card_ocr import extract_card
        from app.services.expense_invoice_ocr import extract_invoice
        from app.api.v1.utils import handle_image_ocr_upload
        # 测图片嗅探
        assert detect_image_type(b'\xff\xd8\xff\xe0') == 'image/jpeg'
        assert detect_image_type(b'\x89PNG\r\n\x1a\n') == 'image/png'
        # 测 helper 边界
        ok, payload, code, msg = handle_image_ocr_upload(None, owner_id=1, business_type='test', ocr_fn=extract_invoice)
        assert ok is False and code == 400
        print(f'{OK} OCR 服务 — claude_vision_ocr / business_card_ocr / expense_invoice_ocr / helper import + 边界 OK')

        # 4) 状态/科目字典完整性
        from app.api.v1.mobile_expense import _STATUS_META, _status_block, _EX_CURRENCIES
        from app.models.expense import EXPENSE_CATEGORIES, EXPENSE_STATUS
        assert len(EXPENSE_CATEGORIES) == 9, f'expect 9 categories, got {len(EXPENSE_CATEGORIES)}'
        assert len(EXPENSE_STATUS) == 6, f'expect 6 statuses, got {len(EXPENSE_STATUS)}'
        for k in ('draft', 'pending', 'approved', 'rejected', 'paid'):
            assert k in _STATUS_META, f'_STATUS_META missing {k}'
            blk = _status_block(k)
            assert 'color' in blk and 'bg' in blk and 'label' in blk
        assert len(_EX_CURRENCIES) == 9
        codes = {c['code'] for c in _EX_CURRENCIES}
        assert codes == {'CNY', 'USD', 'HKD', 'TWD', 'SGD', 'MYR', 'IDR', 'THB', 'VND'}
        print(f'{OK} 字典数据 — 9 科目 / 6 状态 / 9 货币 全完整')

        # 5) 序列化辅助 — 用 mock 对象验证
        from unittest.mock import MagicMock
        from app.api.v1.mobile_expense import _expense_summary, _line_dict
        e = MagicMock()
        e.id = 1
        e.expense_number = 'BX2026050801'
        e.title = '苏州客户拜访'
        e.description = '巴斯夫调试'
        e.total_amount = 713.90
        e.currency = 'CNY'
        e.status = 'pending'
        e.created_at = None  # apply_at None
        e.detail_count = 3
        s = _expense_summary(e)
        assert s['title'] == '苏州客户拜访'
        assert s['amount'] == 713.90
        assert s['status_meta']['label'] == '审批中'
        assert s['status_meta']['color'] == '#C77B22'
        print(f'{OK} 序列化 — _expense_summary 输出完整含 status_meta')

        print()
        print(f'{OK} 路由 + 序列化 + OCR 全套 smoke 通过 ✅')
        print(f'{INFO} 注意: 因本地 DB schema 落后于 mobile-api 分支 model (cross_team 字段缺失),')
        print(f'{INFO} 完整 e2e (创建/提交/审批) 需先运行 flask db upgrade 后再跑.')


if __name__ == '__main__':
    main()
