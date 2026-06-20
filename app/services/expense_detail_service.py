# -*- coding: utf-8 -*-
"""报销明细「分组合并」共用 service —— web / mobile 的唯一合并逻辑来源。

背景:发票分组合并此前 web(at-expense-form.js)、mobile(ReceiptConfirmView.vue) 各写一份,
口径不一致(mobile 逐张成对比较,交通费等场景漏合并)。此处统一:

- group_invoices(items, default_currency): 按 (category||other, currency||默认) 整组归并 → groups
- build_detail_payloads(items, decision, ...): 按决策(merge_all/separate/by_group)产出待建明细 payload
- create_details(expense, payloads): 落库建 ExpenseDetail(累加/张数/并图/重算/提交)

描述规则(2026-06-20 与用户确认·方案2):
- 合并的明细 → 整条用「一个」描述(调用方传入,否则用摘要「{科目} ×N」);逐张描述不保留。
- 分开的明细 → 各留各自描述。
"""
import json


def _norm_cat(v):
    return (v or 'other')


def group_invoices(items, default_currency='CNY'):
    """按 (category, currency) 分组。items: [{category,currency,invoice_amount,...}]。
    返回 [{'key','category','currency','indices':[..],'total_amount','count'}],顺序稳定(首次出现序)。
    两边字段统一兜底:category→'other'、currency→default_currency。
    """
    order = []
    groups = {}
    for i, it in enumerate(items or []):
        cat = _norm_cat(it.get('category'))
        cur = it.get('currency') or default_currency
        key = cat + '|' + cur
        if key not in groups:
            groups[key] = {'key': key, 'category': cat, 'currency': cur,
                           'indices': [], 'total_amount': 0.0, 'count': 0}
            order.append(key)
        g = groups[key]
        g['indices'].append(i)
        g['count'] += 1
        try:
            g['total_amount'] += float(it.get('invoice_amount') or 0)
        except (TypeError, ValueError):
            pass
    return [groups[k] for k in order]


def _summary_desc(category, count, lang=None):
    """合并明细的默认摘要描述:「{科目} ×N」。"""
    try:
        from app.helpers.expense_labels import expense_category_label
        label = expense_category_label(category, lang)
    except Exception:
        label = category or ''
    return ('%s ×%d' % (label, count)) if count > 1 else label


def _image_entry(it):
    """从一条 item 提取 invoice_images 数组项(仅文件/凭证元数据,不含描述—方案2)。"""
    entry = {}
    for k in ('filename', 'url', 'file_url', 'size', 'invoice_no', 'seller'):
        v = it.get(k)
        if v:
            entry[k] = v
    # 统一用 url 键
    if 'url' not in entry and entry.get('file_url'):
        entry['url'] = entry.pop('file_url')
    return entry


def build_detail_payloads(items, decision='by_group', default_currency='CNY',
                          group_description=None, lang=None):
    """按决策产出待建明细 payload 列表(不落库)。

    decision:
      - 'merge_all' : 所有 item 合成 1 条
      - 'separate'  : 每条 item 各 1 条(各留描述)
      - 'by_group'  : 按 (category,currency) 分组,每组 1 条(默认)
    group_description: {group_key: desc} 可选,合并条的指定描述;缺省用摘要。
    返回 [payload,...];payload 字段对齐 ExpenseDetail 创建口径。
    """
    items = items or []
    group_description = group_description or {}

    def merged_payload(idxs):
        first = items[idxs[0]]
        cat = _norm_cat(first.get('category'))
        cur = first.get('currency') or default_currency
        total = 0.0
        images = []
        for i in idxs:
            it = items[i]
            try:
                total += float(it.get('invoice_amount') or 0)
            except (TypeError, ValueError):
                pass
            ent = _image_entry(it)
            if ent:
                images.append(ent)
        key = cat + '|' + cur
        if len(idxs) > 1:
            desc = (group_description.get(key) or '').strip() or _summary_desc(cat, len(idxs), lang)
        else:
            # 单张组 → 保留该张自己的描述
            desc = (first.get('description') or '').strip()
        return {
            'expense_category': cat,
            'currency': cur,
            'invoice_amount': round(total, 2),
            'expense_date': first.get('expense_date') or first.get('date'),
            'description': desc,
            'document_count': len(idxs),
            'invoice_images': images,
        }

    def single_payload(it):
        return {
            'expense_category': _norm_cat(it.get('category')),
            'currency': it.get('currency') or default_currency,
            'invoice_amount': round(float(it.get('invoice_amount') or 0), 2),
            'expense_date': it.get('expense_date') or it.get('date'),
            'description': (it.get('description') or '').strip(),
            'document_count': 1,
            'invoice_images': ([_image_entry(it)] if _image_entry(it) else []),
        }

    if decision == 'merge_all':
        return [merged_payload(list(range(len(items))))] if items else []
    if decision == 'separate':
        return [single_payload(it) for it in items]
    # by_group(默认)
    return [merged_payload(g['indices']) for g in group_invoices(items, default_currency)]


def create_details(expense, payloads, normalize_desc=None):
    """按 payload 列表落库建 ExpenseDetail。normalize_desc: 可选描述归一函数(如区域语言归一)。
    返回创建的 ExpenseDetail 列表。调用方负责权限/状态校验。"""
    from app import db
    from app.models.expense import ExpenseDetail
    from datetime import date as _date

    created = []
    for p in payloads:
        desc = p.get('description') or ''
        if normalize_desc:
            try:
                desc = normalize_desc(desc)
            except Exception:
                pass
        amt = float(p.get('invoice_amount') or 0)
        ed = ExpenseDetail(
            expense_id=expense.id,
            expense_date=p.get('expense_date') or _date.today(),
            expense_category=p.get('expense_category') or 'other',
            description=desc,
            document_count=int(p.get('document_count') or 1),
            currency=p.get('currency') or expense.currency,
            invoice_amount=amt,
            amount=amt,  # 向后兼容
        )
        imgs = p.get('invoice_images') or []
        if imgs:
            ed.invoice_images = json.dumps(imgs, ensure_ascii=False)
        db.session.add(ed)
        db.session.flush()
        ed.expense = expense
        try:
            ed._recalculate_current_amount()
        except Exception:
            pass
        created.append(ed)

    db.session.commit()
    try:
        expense.calculate_total_amount()
        db.session.commit()
    except Exception:
        db.session.rollback()
    return created
