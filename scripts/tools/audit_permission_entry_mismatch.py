#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""审计:模板入口的权限门禁 与 目标路由的权限门槛 是否一致。

起因:沈燕/李芸的 403 白页 —— at_list.html 的「提交报销」按钮没有任何 has_permission
门禁,而 /expense/at_new 要求 expense.create。按钮看得见、点进去 403。
这类"入口可见但路由拒绝"的不一致会散落在各处,必须全量扫。

做法:
  1. 解析 app/views、app/api 下 `X = Blueprint('name',...)` + `@X.route` + 装饰器,
     得到 (蓝图名, 函数名) → (module, action) 门槛(必须按蓝图区分,否则 at_list_view
     这种同名函数会互相串台)
  2. 扫 app/templates 下所有非归档模板里的 url_for('bp.endpoint')
  3. 向上回看若干行找 has_permission(...) 门禁,比对

只报 create/edit/delete 类目标 —— 纯 view 链接(在客户页链到客户页)门禁缺失基本无害,
噪音太大。

运行:python3 scripts/tools/audit_permission_entry_mismatch.py
"""
import os
import re
import sys

PROJECT_ROOT = '/Users/nijie/Documents/PMA'
os.chdir(PROJECT_ROOT)

VIEW_DIRS = ['app/views', 'app/api']
TEMPLATE_DIR = 'app/templates'
LOOKBACK = 12
INTERESTING = {'create', 'edit', 'delete'}   # 只看会"看得见点不了"的高危动作

RE_BP = re.compile(r"^(\w+)\s*=\s*Blueprint\(\s*['\"]([\w\-]+)['\"]", re.M)   # re.M 必须有,否则整文件只匹配首行
RE_ROUTE = re.compile(r"^@(\w+)\.route\(")
RE_PERM = re.compile(r"@permission_required(?:_with_approval_context)?\(\s*'([^']+)'\s*,\s*'([^']+)'")
RE_DEF = re.compile(r'^def\s+(\w+)\s*\(')
RE_URLFOR = re.compile(r"url_for\(\s*'([\w\-]+)\.(\w+)'")
RE_HASPERM = re.compile(r"has_permission\(\s*'([^']+)'\s*,\s*'([^']+)'")

route_perms = {}          # (bp_name, func) -> (module, action)

for vdir in VIEW_DIRS:
    for root, _d, files in os.walk(vdir):
        for fn in sorted(files):
            if not fn.endswith('.py'):
                continue
            text = open(os.path.join(root, fn), encoding='utf-8').read()
            var2bp = dict(RE_BP.findall(text))
            cur_bp, cur_perm = None, None
            for line in text.splitlines():
                r = RE_ROUTE.match(line)
                if r:
                    cur_bp = var2bp.get(r.group(1))
                    continue
                p = RE_PERM.search(line)
                if p:
                    cur_perm = (p.group(1), p.group(2))
                    continue
                d = RE_DEF.match(line)
                if d:
                    if cur_bp and cur_perm:
                        route_perms[(cur_bp, d.group(1))] = cur_perm
                    cur_bp, cur_perm = None, None
                elif line.strip() and not line.lstrip().startswith(('@', '#')):
                    cur_bp, cur_perm = None, None

no_gate, mismatch, stricter = [], [], []
ORDER = {'view': 0, 'create': 1, 'edit': 2, 'delete': 3}

for root, _d, files in os.walk(TEMPLATE_DIR):
    if '_archived' in root.split(os.sep):
        continue
    for fn in sorted(files):
        if not fn.endswith('.html'):
            continue
        path = os.path.join(root, fn)
        rel = os.path.relpath(path, TEMPLATE_DIR)
        raw = open(path, encoding='utf-8').read()
        # 把 {# ... #} 注释整段挖空但保留换行 —— 组件文件顶部常有大段"用法示例",
        # 里面的 url_for 不是真入口,不挖会淹没真实命中
        blanked = re.sub(r'\{#.*?#\}',
                         lambda m: re.sub(r'[^\n]', ' ', m.group(0)),
                         raw, flags=re.S)
        lines = blanked.splitlines()

        for i, line in enumerate(lines):
            for bp, endpoint in RE_URLFOR.findall(line):
                need = route_perms.get((bp, endpoint))
                if not need:
                    continue
                need_mod, need_act = need
                if need_act not in INTERESTING:
                    continue

                gates = []
                for j in range(max(0, i - LOOKBACK), i + 1):
                    gates += RE_HASPERM.findall(lines[j])

                loc, target = f'{rel}:{i+1}', f'{bp}.{endpoint}'
                if not gates:
                    no_gate.append((loc, target, f'需 {need_mod}.{need_act}'))
                elif (need_mod, need_act) in gates:
                    continue
                else:
                    shown = '/'.join(f'{m}.{a}' for m, a in gates)
                    same_mod = [a for m, a in gates if m == need_mod]
                    if same_mod and ORDER.get(same_mod[0], 9) > ORDER.get(need_act, 9):
                        stricter.append((loc, target, f'需 {need_mod}.{need_act}', f'门禁 {shown}'))
                    else:
                        mismatch.append((loc, target, f'需 {need_mod}.{need_act}', f'门禁 {shown}'))


def dump(title, rows):
    print(f'\n{"=" * 90}\n{title}  ({len(rows)} 处)\n{"=" * 90}')
    for r in rows:
        print('  ' + '  |  '.join(str(x) for x in r))


print(f'解析到 {len(route_perms)} 个 (蓝图,函数) 权限门槛')
dump('[无门禁] 路由要 create/edit/delete,模板入口没门禁 → 点进去撞 403', no_gate)
dump('[门禁不符] 门禁的模块/动作与路由要求不一致', mismatch)
dump('[过严] 门禁比路由严 → 有权限的人反而看不到入口', stricter)
print(f'\n合计 {len(no_gate) + len(mismatch) + len(stricter)} 处待人工判断')
sys.exit(0)
