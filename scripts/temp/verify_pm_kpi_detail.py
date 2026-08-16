#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证产品经理 6 个 KPI 下钻明细:明细合计 必须 == 采集器实际值。

逐人 × 逐期 × 逐指标跑一遍,任何一处偏差 >0.5% 即判失败(与后端自检同阈值)。
"""
import sys, os
from datetime import datetime

def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

ROOT = get_project_root()
sys.path.insert(0, ROOT)

DB = os.environ.get('PM_CHECK_DB', 'postgresql://nijie@localhost/pma_local')
os.environ['DATABASE_URL'] = DB
os.environ['SQLALCHEMY_DATABASE_URI'] = DB

from app import create_app, db  # noqa: E402

app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = DB

CODES = ['pm_implant_amount', 'pm_sales_amount', 'pm_new_launch',
         'pm_dev_rate', 'pm_quality_rate', 'pm_support_count']

PERIODS = [('2026Q1', datetime(2026, 1, 1), datetime(2026, 4, 1)),
           ('2026Q2', datetime(2026, 4, 1), datetime(2026, 7, 1)),
           ('2026Q3', datetime(2026, 7, 1), datetime(2026, 10, 1)),
           ('2025Q4', datetime(2025, 10, 1), datetime(2026, 1, 1)),
           ('2025年', datetime(2025, 1, 1), datetime(2026, 1, 1))]

with app.app_context():
    from app.models.user import User
    from app.services import kpi_actual_service as K

    print("注册的下钻 code 总数:", len(K._KPI_DETAIL_FNS))
    print("PM 已注册:", [c for c in CODES if c in K._KPI_DETAIL_FNS])
    print()

    users = User.query.filter_by(role='product_manager').all()
    users = [u for u in users if getattr(u, 'managed_categories', None)] or users

    ok = bad = empty = 0
    fails = []
    for u in users:
        name = u.real_name or u.username
        for pname, s, e in PERIODS:
            for code in CODES:
                fn = K._KPI_ACTUAL_FNS.get(code)
                actual = float(fn(u, s, e) or 0) if fn else 0.0
                d = K.get_actual_detail(u, code, s, e)
                if d is None:
                    fails.append(f"{name} {pname} {code}: get_actual_detail 返回 None(未注册)")
                    bad += 1
                    continue
                dt = float(d.get('total') or 0)
                diff = abs(dt - actual)
                tol = max(abs(actual) * 0.005, 0.01)
                if diff <= tol:
                    ok += 1
                    if actual == 0:
                        empty += 1
                    else:
                        print(f"  ✓ {name:<8}{pname:<8}{code:<20}"
                              f"采集={actual:>16,.2f}  明细={dt:>16,.2f}  "
                              f"组数={len(d.get('groups') or [])}")
                else:
                    bad += 1
                    fails.append(f"{name} {pname} {code}: 采集={actual:,.2f} 明细={dt:,.2f} 差={diff:,.2f}")
                    print(f"  ✗ {name:<8}{pname:<8}{code:<20}采集={actual:,.2f} 明细={dt:,.2f}")

    print()
    print("=" * 66)
    print(f"样本 {ok+bad} 个 · 一致 {ok}(其中两边都为 0 的 {empty} 个)· 不一致 {bad}")
    if fails:
        print("\n失败明细:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("全部一致 ✅")
