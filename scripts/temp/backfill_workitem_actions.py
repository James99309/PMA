#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""工作项 → 跟进记录(Action) 存量回填。

背景:历史上有两套互不知情的同步机制 ——
  A) complete_item 的 sync_action 开关(2026-01 起):条件是「有客户或项目」,但**不写
     related_action_id**,且只有 web 日历传该参数,移动端点完成永远漏同步;
  B) sync_work_item_action(2026-06-17 起):写指针,但门槛是「必须有项目」。
两者都不覆盖「只挂客户 + 从移动端完成」的场景,导致大量日历跟进从未进客户档案。
现已合并为唯一入口 sync_work_item_action(门槛:有归属 / 有描述 / 已完成或日期已到)。

本脚本补齐存量,三步:
  1. 幽灵清理:工作项已删除/作废但 related_action_id 仍在 → 解引用并删掉那条 Action
  2. 认领:候选工作项在 actions 里已有唯一对应记录(机制 A 建的,只是没指针)
     → 只写 related_action_id,**不改正文**(保留用户当初实际写的内容)
  3. 新建:无对应记录的候选 → 调 sync_work_item_action 生成,与线上行为完全一致

默认 dry-run,不写库。确认无误后加 --apply。

用法(在 pma 容器内或本地):
  python3 scripts/temp/backfill_workitem_actions.py            # 预演
  python3 scripts/temp/backfill_workitem_actions.py --apply    # 执行
"""
import argparse
import sys
import os

# 路径修正 - 支持从任何位置运行
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

from datetime import timedelta

from app import create_app, db
from app.models.action import Action
from app.models.user import User
from app.models.worklog import WorkItem
from app.services.worklog_service import sync_work_item_action

# 系统自动记录的标题前缀(work_item_recorder 产出,标题走 _() 翻译故中英文各一套)。
# 这类是业务流水镜像,不是人写的跟进,不应进客户档案。
AUTO_PREFIXES_ZH = ('项目动态', '创建报价单', '编辑报价单', '报价单确认', '创建项目',
                    '项目推进', '创建客户', '编辑客户', '创建联系人', '编辑联系人',
                    '添加行动记录', '创建产品', '编辑产品')
AUTO_PREFIXES_EN = ('Project:', 'Add Action Record:', 'Create Customer:', 'Edit Customer:',
                    'Create Contact:', 'Edit Contact:', 'Create Project:', 'Advance Stage:',
                    'Create Quotation:', 'Edit Quotation:', 'Quotation Confirm:',
                    'Create Product:', 'Edit Product:')


def is_auto_record(title):
    t = (title or '').strip()
    if t.startswith(AUTO_PREFIXES_EN):
        return True
    return any(t.startswith(p) for p in AUTO_PREFIXES_ZH)


def build_comm(wi):
    """与 sync_work_item_action 一致的正文格式(仅用于长度比对,不实际写入认领组)。"""
    return '[工作项] ' + (wi.title or '').strip() + '\n' + (wi.description or '').strip()


def find_existing_action(wi):
    """找机制 A 当初建的那条 Action。严格匹配:同人 + 同归属 + 日期±1天 + 正文包含描述前30字。
    返回 (命中列表)。只有恰好命中 1 条才认领,多条留人工。"""
    text = (wi.description or '').strip()
    if len(text) < 10:                       # 太短的描述匹配不可靠,不认领
        return []
    act_date = wi.end_date or wi.planned_date
    return (Action.query
            .filter(Action.owner_id == wi.owner_id,
                    Action.company_id.is_(None) if wi.customer_id is None
                    else Action.company_id == wi.customer_id,
                    Action.project_id.is_(None) if wi.project_id is None
                    else Action.project_id == wi.project_id,
                    Action.date >= act_date - timedelta(days=1),
                    Action.date <= act_date + timedelta(days=1),
                    Action.communication.like(f'%{text[:30]}%'))
            .all())


def candidates():
    """与 sync_work_item_action 三道门槛一致的候选集(额外排除系统自动记录)。"""
    from datetime import date as date_type
    rows = (WorkItem.query
            .filter(WorkItem.is_deleted == False,            # noqa: E712
                    WorkItem.is_invalidated == False,        # noqa: E712
                    WorkItem.related_action_id.is_(None),
                    db.or_(WorkItem.customer_id.isnot(None),
                           WorkItem.project_id.isnot(None)))
            .order_by(WorkItem.id).all())
    today = date_type.today()
    out = []
    for wi in rows:
        if not (wi.description or '').strip():
            continue
        if wi.status != 'completed' and wi.planned_date > today:
            continue
        if is_auto_record(wi.title):
            continue
        out.append(wi)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true', help='真正写库(默认只预演)')
    args = ap.parse_args()
    apply = args.apply

    app = create_app()
    with app.app_context():
        print(f"数据库: {db.engine.url.database}")
        print(f"模式:   {'【执行】写库' if apply else '【预演】不写库'}\n")

        # ── 1. 幽灵清理 ───────────────────────────────────────────────
        ghosts = (WorkItem.query
                  .filter(WorkItem.related_action_id.isnot(None),
                          db.or_(WorkItem.is_deleted == True,        # noqa: E712
                                 WorkItem.is_invalidated == True))   # noqa: E712
                  .all())
        print(f"[1] 幽灵记录(工作项已删/作废,跟进记录still在): {len(ghosts)} 条")
        for wi in ghosts:
            print(f"    wi#{wi.id} 「{(wi.title or '')[:30]}」 → action#{wi.related_action_id}")
            if apply:
                aid = wi.related_action_id
                wi.related_action_id = None      # 先解引用,FK 要求
                db.session.flush()
                act = Action.query.get(aid)
                if act:
                    db.session.delete(act)
        if apply:
            db.session.commit()

        # ── 2/3. 认领 与 新建 ─────────────────────────────────────────
        cands = candidates()
        print(f"\n[2/3] 候选工作项: {len(cands)} 条")

        adopt, ambiguous, longer, create = [], [], [], []
        for wi in cands:
            hits = find_existing_action(wi)
            if len(hits) == 1:
                act = hits[0]
                # 已有正文比重建的更长 → 说明用户当初写得更细,认领后将来编辑会覆盖它,留人工
                if len(act.communication or '') > len(build_comm(wi)):
                    longer.append((wi, act))
                else:
                    adopt.append((wi, act))
            elif len(hits) > 1:
                ambiguous.append((wi, hits))
            else:
                create.append(wi)

        print(f"    A 认领(已有跟进记录,补指针): {len(adopt)}")
        print(f"    B 歧义(命中多条,人工复核):   {len(ambiguous)}")
        print(f"    C 保留(已有正文更详细,不动): {len(longer)}")
        print(f"    D 新建(确实缺失):            {len(create)}")

        for wi, hits in ambiguous:
            print(f"    [B] wi#{wi.id} 「{(wi.title or '')[:28]}」 → "
                  f"命中 {[a.id for a in hits]}")
        for wi, act in longer:
            print(f"    [C] wi#{wi.id} 「{(wi.title or '')[:28]}」 → action#{act.id} "
                  f"(已有 {len(act.communication)} 字 > 重建 {len(build_comm(wi))} 字)")

        if apply:
            for wi, act in adopt:
                wi.related_action_id = act.id     # 只补指针,不改正文
            db.session.commit()
            print(f"    ✓ 已认领 {len(adopt)} 条")

            done = 0
            for wi in create:
                owner = User.query.get(wi.owner_id)
                if not owner:
                    print(f"    ! wi#{wi.id} owner {wi.owner_id} 不存在,跳过")
                    continue
                if sync_work_item_action(wi, owner):
                    done += 1
            db.session.commit()
            print(f"    ✓ 已新建 {done} 条")

        # ── 4. 影响面 ────────────────────────────────────────────────
        cust_ids = {wi.customer_id for wi in create if wi.customer_id}
        print(f"\n[4] 新建将覆盖 {len(cust_ids)} 个客户的档案")
        by_user = {}
        for wi in create:
            by_user[wi.owner_id] = by_user.get(wi.owner_id, 0) + 1
        for uid, n in sorted(by_user.items(), key=lambda x: -x[1]):
            u = User.query.get(uid)
            print(f"    {u.username if u else uid:<14} {n} 条")

        if not apply:
            print("\n※ 预演结束,未写库。确认无误后加 --apply 执行。")


if __name__ == '__main__':
    sys.exit(main() or 0)
