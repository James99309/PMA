#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""题库管理页 端到端验证 —— Python Playwright + 本机 pma_local 临时实例。

覆盖(不调真实 AI):
  1. HR(hr_manager)在知识库课程卡上能看到「题库管理」入口,点开题库页
  2. 统计卡 / 健康告警 / 列表渲染;筛选(状态 / 页 / 搜索)
  3. 编辑弹窗:改题干 + 状态,保存后列表与数据库一致
  4. 停用 → 恢复;行内改难度;阅读时长设置与清空
  5. 全部通过待审(确认框)
  6. 生成题库弹窗:合计提示;非法计划(全 0)报错不启动任务
  7. 普通销售访问题库页 → 403
  8. 无未捕获 pageerror / 本页脚本 console error

运行(worktree 根目录):
  export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib
  ../../venv/bin/python tests/e2e_course_bank_page.py [--port 5094] [--shots DIR]

自清理:临时账号 zz_bank_e2e_hr / zz_bank_e2e_s 及关联行、ZZE2B- 临时题全部硬删;该课 course_exam_settings 还原。
"""
import argparse
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


ROOT = get_project_root()
sys.path.insert(0, os.path.join(ROOT, 'tests'))
from _pma_testkit import (make_app, start_server, stop_server, create_temp_user,  # noqa: E402
                          delete_temp_user, add_temp_bank, delete_temp_bank)

HR_USER, SALES_USER = 'zz_bank_e2e_hr', 'zz_bank_e2e_s'
PASSWORD = 'BankE2e-Page-2026!'
KEY = 'smart-task-intercom'
QPREFIX = 'ZZE2B-'

ap = argparse.ArgumentParser()
ap.add_argument('--port', type=int, default=5094)
ap.add_argument('--shots', default=os.path.join(ROOT, 'data', 'temp', 'bank-shots'))
ap.add_argument('--headed', action='store_true')
args = ap.parse_args()
os.makedirs(args.shots, exist_ok=True)
BASE = f'http://127.0.0.1:{args.port}'

app = make_app()
from app import db  # noqa: E402

fails = []
saved_setting = {'exists': False, 'value': None}


def check(cond, msg):
    print(('OK   ' if cond else 'FAIL ') + msg, flush=True)
    if not cond:
        fails.append(msg)


def q_row(tag):
    from app.models.course_exam import CourseQuizQuestion
    with app.app_context():
        q = CourseQuizQuestion.query.filter(CourseQuizQuestion.question.like(QPREFIX + tag + '%')).first()
        return None if q is None else {'id': q.id, 'question': q.question, 'status': q.status,
                                       'difficulty': q.difficulty, 'origin': q.origin}


def setting_value():
    from app.models.course_exam import CourseExamSetting
    with app.app_context():
        row = db.session.get(CourseExamSetting, KEY)
        return None if row is None else row.min_read_seconds


def seed():
    """34 道启用难题(健康)+ 3 道待审题(第 3 / 第 5 页)。"""
    from app.models.course_exam import CourseQuizQuestion, CourseExamSetting
    add_temp_bank(app, KEY, QPREFIX)
    with app.app_context():
        row = db.session.get(CourseExamSetting, KEY)
        saved_setting.update(exists=row is not None, value=row.min_read_seconds if row else None)
        for i, page in enumerate((3, 3, 5)):
            db.session.add(CourseQuizQuestion(
                course_key=KEY, qtype='single', difficulty=1, question=f'{QPREFIX}review {i}',
                options=['R1', 'R2', 'R3'], answer=1, explain='ZZ', source_page=page, status='review',
                ai_difficulty=2, review_note='难度不一致:标注 1 / 复核 2'))
        db.session.commit()


def restore_setting():
    from app.models.course_exam import CourseExamSetting
    with app.app_context():
        row = db.session.get(CourseExamSetting, KEY)
        if saved_setting['exists']:
            if row is not None:
                row.min_read_seconds = saved_setting['value']
        elif row is not None:
            db.session.delete(row)
        db.session.commit()
    return setting_value() == saved_setting['value']


def login(ctx, username):
    page = ctx.new_page()
    page.goto(BASE + '/auth/login')
    page.fill('#username', username)
    page.fill('#password', PASSWORD)
    page.click('button[type=submit]')
    page.wait_for_load_state('networkidle')
    check('/auth/login' not in page.url, f'{username} 登录成功')
    return page


def run_browser():
    from playwright.sync_api import sync_playwright
    errors = []

    def shot(page, name):
        p = os.path.join(args.shots, name + '.png')
        page.screenshot(path=p, full_page=True)
        print('     shot ' + p)

    def rows(page):
        return page.locator('#bkBody tr[data-qid]')

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not args.headed)
        ctx = browser.new_context(viewport={'width': 1440, 'height': 900}, locale='zh-CN')
        ctx.on('page', lambda p: (
            p.on('console', lambda m: m.type == 'error' and errors.append(f'console[{p.url}]: {m.text}')),
            p.on('pageerror', lambda e: errors.append(f'pageerror[{p.url}]: {e}'))))
        page = login(ctx, HR_USER)

        # ---- 1. 知识库入口 ----
        page.goto(BASE + '/wiki/at')
        page.wait_for_load_state('domcontentloaded')
        link = page.locator(f'a[data-bank-link="{KEY}"]')
        check(link.count() == 1, 'HR 在知识库课程卡上看到「题库管理」入口')
        href = link.get_attribute('href') if link.count() else ''
        check(href == f'/wiki/play/{KEY}/bank', f'入口链接正确({href})')

        # ---- 2. 题库页 ----
        page.goto(BASE + f'/wiki/play/{KEY}/bank')
        page.wait_for_selector('#bkBody tr[data-qid]', timeout=20000)
        n_all = rows(page).count()
        check(n_all == 37, f'列表渲染全部临时题(实际 {n_all})')
        stats = page.locator('#bkStats').inner_text()
        check('102' in stats and '待审' in stats, '统计卡:理论总分 102、待审')
        check(page.locator('#bkHealthBanner').is_hidden(), '题库健康 → 不显示告警')
        check(page.locator('#bkApproveAllText').inner_text().endswith('(3)'), '「全部通过待审(3)」')
        check(page.locator('#atSidebar').count() == 1, '页面挂载 AT 侧栏')
        shot(page, '01-bank-list')

        # 筛选
        page.select_option('#bkFStatus', 'review')
        check(rows(page).count() == 3, '筛选 状态=待审 → 3 题')
        page.select_option('#bkFPage', '5')
        check(rows(page).count() == 1, '再筛 第 5 页 → 1 题')
        page.select_option('#bkFPage', '')
        page.select_option('#bkFStatus', '')
        page.fill('#bkFText', 'multi')
        check(rows(page).count() == 2, '搜索题干「multi」→ 2 题')
        page.fill('#bkFText', '')
        page.select_option('#bkFType', 'judge')
        check(rows(page).count() == 2, '筛选 题型=判断 → 2 题')
        page.select_option('#bkFType', '')

        # ---- 3. 编辑弹窗 ----
        r0 = q_row('review 0')
        page.click(f'#bkBody tr[data-qid="{r0["id"]}"] button[data-act=edit]')
        page.wait_for_selector('#bkEditModal', state='visible')
        check(page.locator('#bkEOpts .bk-opt').count() == 3 and
              page.locator('#bkEOpts .bk-opt').nth(1).locator('input[data-correct]').is_checked(),
              '编辑弹窗:3 个选项且正确项为 B')
        check(page.locator('#bkENote').inner_text().startswith('难度不一致'), '编辑弹窗:显示复核存疑说明')
        shot(page, '02-edit-modal')
        page.fill('#bkEQuestion', QPREFIX + 'review 0 已修改')
        page.select_option('#bkEStatus', 'active')
        # 先试一次非法(清空正确项)→ 弹窗内报错不关闭
        page.locator('#bkEOpts .bk-opt').nth(1).locator('input[data-correct]').evaluate('e => e.checked = false')
        page.click('#bkEditSave')
        page.wait_for_function("() => document.getElementById('bkEErr').textContent.length > 0")
        check(page.locator('#bkEditModal').is_visible(), '非法答案:弹窗内报错且不关闭')
        page.locator('#bkEOpts .bk-opt').nth(2).locator('input[data-correct]').check()
        page.click('#bkEditSave')
        page.wait_for_selector('#bkEditModal', state='hidden')
        r1 = q_row('review 0')
        check(r1['question'] == QPREFIX + 'review 0 已修改' and r1['status'] == 'active' and r1['origin'] == 'edited',
              f'保存后数据库已更新 {r1}')
        row_text = page.locator(f'#bkBody tr[data-qid="{r0["id"]}"]').inner_text()
        check('已修改' in row_text and '启用' in row_text, '保存后列表行已刷新')

        # ---- 4. 停用 / 恢复 / 改难度 / 阅读时长 ----
        s0 = q_row('single 0')
        sel = f'#bkBody tr[data-qid="{s0["id"]}"]'
        page.click(sel + ' button[data-act=disable]')
        page.wait_for_function(f"() => document.querySelector('{sel} .bk-chip').textContent.includes('停用')")
        check(q_row('single 0')['status'] == 'disabled', '停用 → 数据库 disabled')
        check('bk-off' in (page.locator(sel).get_attribute('class') or ''), '停用行变灰')
        page.click(sel + ' button[data-act=restore]')
        page.wait_for_function(f"() => document.querySelector('{sel} .bk-chip').textContent.includes('启用')")
        check(q_row('single 0')['status'] == 'active', '恢复 → 数据库 active')
        page.select_option(sel + ' select[data-act=diff]', '2')
        page.wait_for_timeout(800)
        check(q_row('single 0')['difficulty'] == 2, '行内改难度 → 数据库 2')
        page.fill('#bkReadInput', '90')
        page.click('#bkReadSave')
        page.wait_for_timeout(800)
        check(setting_value() == 90, '阅读时长设置 90 秒')
        page.fill('#bkReadInput', '')
        page.click('#bkReadSave')
        page.wait_for_timeout(800)
        check(setting_value() is None, '阅读时长清空 → 自动')

        # ---- 5. 全部通过待审 ----
        page.click('#bkApproveAll')
        page.locator('button[data-act=confirm]').click()
        page.wait_for_function("() => document.getElementById('bkApproveAll').disabled")
        check(q_row('review 1')['status'] == 'active' and q_row('review 2')['status'] == 'active',
              '全部通过待审 → 数据库 active')

        # ---- 6. 生成弹窗 ----
        page.click('#bkGenBtn')
        page.wait_for_selector('#bkGenModal', state='visible')
        check('100' in page.locator('#bkGTotal').inner_text(), f'生成弹窗默认合计 {page.locator("#bkGTotal").inner_text()}')
        for d in (1, 2, 3):
            page.fill(f'#bkG{d}', '0')
        page.click('#bkGenSubmit')
        page.wait_for_function("() => document.getElementById('bkGErr').textContent.length > 0")
        check(page.locator('#bkGenModal').is_visible() and page.locator('#bkGenBanner').is_hidden(),
              f'全 0 计划被拒,未启动生成({page.locator("#bkGErr").inner_text()})')
        shot(page, '03-generate-modal')
        page.click('#bkGenModal footer button:not(#bkGenSubmit)')
        page.select_option('#bkFStatus', 'disabled')
        shot(page, '04-after-ops')

        # ---- 7. 普通销售 403 ----
        ctx2 = browser.new_context(viewport={'width': 1280, 'height': 800}, locale='zh-CN')
        p2 = login(ctx2, SALES_USER)
        resp = p2.goto(BASE + f'/wiki/play/{KEY}/bank')
        check(resp.status == 403, f'普通销售访问题库页 → 403(实际 {resp.status})')
        p2.goto(BASE + '/wiki/at')
        check(p2.locator('a[data-bank-link]').count() == 0, '普通销售看不到「题库管理」入口')
        browser.close()

    print('INFO 全部 console/page 错误:', len(errors))
    for e in errors:
        print('     ' + e[:300])
    own = [e for e in errors if '/bank' in e and 'Failed to load resource' not in e]
    check(not own, f'题库页无脚本 console error({len(own)})')
    check(not any(e.startswith('pageerror') for e in errors), '无未捕获 pageerror')


def cleanup():
    return delete_temp_user(app, HR_USER) & delete_temp_user(app, SALES_USER) & delete_temp_bank(app, QPREFIX)


proc = None
try:
    cleanup()
    create_temp_user(app, HR_USER, PASSWORD, role='hr_manager')
    create_temp_user(app, SALES_USER, PASSWORD, role='sales_manager')
    seed()
    proc = start_server(args.port, os.path.join(args.shots, 'server.log'), KEY)
    print('INFO 服务已启动', BASE)
    run_browser()
finally:
    stop_server(proc)
    check(restore_setting(), '清理:course_exam_settings 已还原')
    check(cleanup(), '清理:临时账号与 ZZE2B 题已硬删')
    print('\n' + ('全部通过' if not fails else f'{len(fails)} 项失败:\n  - ' + '\n  - '.join(fails)))
sys.exit(1 if fails else 0)
