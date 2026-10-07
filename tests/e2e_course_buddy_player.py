#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""课程播放器 × 小源 端到端验证 —— Python Playwright + 本机 pma_local 临时实例。

覆盖:
  1. 播放页旧「开始考核」按钮已下线;旧 /wiki/play/<key>/quiz 跳回播放页
  2. 进课程 → 小源头顶「阅读 x%」、考核标签禁用
  3. 真实点「下一步」翻遍全部页 → 服务端 pages_seen 随翻页增长(页码 1-based 对齐)
     → 达到临时阅读要求(course_exam_settings.min_read_seconds=20)后服务端解锁
     → 小源头顶切到分数、考核标签可用
  4. 答一题 → 关面板 → 刷新页面 → 再开考核:同一题、同一结果态
  5. 课程内提问:请求带 course_key;/api/wiki/query 课程范围(进程内 mock querier):
     topic 收窄到该课、deck_pages 只含该课
  6. 收集 pageerror / console error

运行(worktree 根目录):
  export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib
  ../../venv/bin/python tests/e2e_course_buddy_player.py [--port 5094] [--shots DIR]

自清理:临时账号 zz_cb_e2e_p 及关联行、ZZE2P- 临时题全部硬删;该课 course_exam_settings 还原;临时服务结束时终止。
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
                          delete_temp_user, add_temp_bank, delete_temp_bank, MAIN_ASSETS,
                          empty_seed_keys, delete_seed_imports)

USERNAME = 'zz_cb_e2e_p'
PASSWORD = 'CbE2e-Player-2026!'
KEY = 'smart-task-intercom'
OTHER_KEY = 'evertac-pnr2100'
QPREFIX = 'ZZE2P-'
MIN_READ = 20

ap = argparse.ArgumentParser()
ap.add_argument('--port', type=int, default=5094)
ap.add_argument('--shots', default=os.path.join(ROOT, 'data', 'temp', 'cb-player-shots'))
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


def set_min_read():
    from app.models.course_exam import CourseExamSetting
    with app.app_context():
        row = db.session.get(CourseExamSetting, KEY)
        if row is not None:
            saved_setting.update(exists=True, value=row.min_read_seconds)
            row.min_read_seconds = MIN_READ
        else:
            db.session.add(CourseExamSetting(course_key=KEY, min_read_seconds=MIN_READ))
        db.session.commit()


def restore_min_read():
    from app.models.course_exam import CourseExamSetting
    with app.app_context():
        row = db.session.get(CourseExamSetting, KEY)
        if saved_setting['exists']:
            if row is not None:
                row.min_read_seconds = saved_setting['value']
        elif row is not None:
            db.session.delete(row)
        db.session.commit()
        row = db.session.get(CourseExamSetting, KEY)
        return (row is None) if not saved_setting['exists'] else (row.min_read_seconds == saved_setting['value'])


def check_query_scope(uid):
    """进程内 test_client + mock querier:验证 /api/wiki/query 的课程范围(本地无 AI 时也可验)。"""
    import app.views.knowledge_wiki as KW
    from flask import g
    if not os.path.isfile(KW._course_html_path(KEY)) and os.path.isdir(MAIN_ASSETS):
        KW.COURSE_ASSETS_DIR = MAIN_ASSETS
    seen = {}

    def fake_query(question, top_k=5, topic=None, current_user_id=None, **kw):
        seen['topic'] = topic
        # 故意引用另一门课的课件文章:课程范围内不应出现它的页
        return {'answer': 'ok', 'cited_articles': [{'slug': OTHER_KEY + '-deck', 'id': 1}], 'usage': {},
                'search_hit_count': 1}

    orig = KW.querier.query_wiki
    KW.querier.query_wiki = fake_query
    app.config['WTF_CSRF_ENABLED'] = False
    try:
        with app.app_context():
            from app.models.user import User
            u = db.session.get(User, uid)
            c = app.test_client()
            with c.session_transaction() as s:
                s['_user_id'] = str(uid)
                s['_fresh'] = True
                s['role'] = u.role
            course, _ = KW._find_course(KEY)
            q = (course or {}).get('topic')
            g.pop('_login_user', None)
            r = c.post('/api/wiki/query', json={'question': '智能任务对讲 主要功能', 'course_key': KEY})
            d = (r.get_json() or {}).get('data') or {}
            keys = {p.get('key') for p in d.get('deck_pages') or []}
            check(r.status_code == 200 and seen.get('topic') == q,
                  f'课程范围:检索 topic 收窄为该课 topic({seen.get("topic")!r})')
            check(keys <= {KEY}, f'课程范围:deck_pages 只含本课(实际 {sorted(keys)})')
            g.pop('_login_user', None)
            r = c.post('/api/wiki/query', json={'question': '智能任务对讲 主要功能'})
            d = (r.get_json() or {}).get('data') or {}
            keys = {p.get('key') for p in d.get('deck_pages') or []}
            check(r.status_code == 200 and seen.get('topic') is None and KEY not in keys,
                  f'全库范围:不收窄 topic,只按被引用的课件文章给页(实际 {sorted(keys)})')
    finally:
        KW.querier.query_wiki = orig
        app.config['WTF_CSRF_ENABLED'] = True


def run_browser():
    from playwright.sync_api import sync_playwright
    errors, asks, pings = [], [], []

    def shot(page, name):
        p = os.path.join(args.shots, name + '.png')
        page.screenshot(path=p)
        print('     shot ' + p)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not args.headed)
        ctx = browser.new_context(viewport={'width': 1440, 'height': 900}, locale='zh-CN')
        page = ctx.new_page()
        page.on('console', lambda m: m.type == 'error' and errors.append(f'console[{page.url}]: {m.text} @ {m.location.get("url", "")}'))
        page.on('pageerror', lambda e: errors.append(f'pageerror[{page.url}]: {e}'))
        page.on('request', lambda r: '/api/wiki/query' in r.url and asks.append(r.post_data))
        page.on('response', lambda r: '/read-ping' in r.url and pings.append(r.status))

        page.goto(BASE + '/auth/login')
        page.fill('#username', USERNAME)
        page.fill('#password', PASSWORD)
        page.click('button[type=submit]')
        page.wait_for_load_state('networkidle')
        check('/auth/login' not in page.url, '登录成功')
        page.evaluate("() => { Object.keys(localStorage).filter(k => k.startsWith('cb-')).forEach(k => localStorage.removeItem(k)); }")

        def progress():
            return page.evaluate("(k) => fetch('/api/learning/' + k + '/progress', {credentials: 'same-origin'})"
                                 ".then(r => r.json()).then(j => j.data.read)", KEY)

        # ---- 1. 旧入口 ----
        page.goto(BASE + f'/wiki/play/{KEY}/quiz')
        page.wait_for_load_state('domcontentloaded')
        check(page.url.split('#')[0].rstrip('/').endswith(f'/wiki/play/{KEY}'), f'旧 /quiz 跳回播放页({page.url})')
        check(page.locator('#cpExam').count() == 0, '播放页旧「开始考核」按钮已移除')

        # ---- 2. 进课程:未解锁 ----
        page.wait_for_selector('#cbWrap .cb-pet', state='visible', timeout=20000)
        page.wait_for_function("() => /\\d+ \\/ \\d+/.test(document.getElementById('cpPageNum').textContent)", timeout=30000)
        page.wait_for_function("() => { const l = document.getElementById('cpLoading'); return !l || l.classList.contains('cp-hide'); }",
                               timeout=30000)
        page.wait_for_function("() => !document.querySelector('#cbWrap .cb-badge').hidden", timeout=15000)
        badge = page.locator('#cbWrap .cb-badge').inner_text()
        check('%' in badge, f'进课程后头顶显示阅读进度「{badge}」')
        total = int(page.locator('#cpPageNum').inner_text().split('/')[1])
        r0 = progress()
        check(not r0['unlocked'] and r0['pages_total'] == total,
              f'服务端页数与播放器一致(server {r0["pages_total"]} / player {total})')
        shot(page, '01-course-locked')

        # ---- 3. 真实翻页 → 服务端计时 → 解锁 ----
        seen_hist = [r0['pages_seen']]
        for i in range(total - 1):
            for k in range(4):                      # 每页约 2s,期间有鼠标活动
                page.mouse.move(500 + k * 40 + i, 500)
                page.wait_for_timeout(500)
            page.click('#cpNext')
            page.wait_for_function("(n) => document.getElementById('cpPageNum').textContent.startsWith(n + ' /')",
                                   arg=i + 2, timeout=10000)
            if i in (2, 6):
                page.wait_for_timeout(700)
                seen_hist.append(progress()['pages_seen'])
        check(seen_hist[-1] > seen_hist[0] and seen_hist == sorted(seen_hist),
              f'翻页时服务端 pages_seen 递增 {seen_hist}')
        unlocked = None
        for _ in range(40):
            page.mouse.move(600, 520)
            page.wait_for_timeout(1500)
            rd = progress()
            if rd['unlocked']:
                unlocked = rd
                break
        check(bool(unlocked), f'阅读达标后服务端解锁(最后 {rd["pages_seen"]}/{rd["pages_total"]} 页,'
                              f'{rd["effective_seconds"]}/{rd["required_seconds"]}s)')
        check(any(s == 200 for s in pings), f'read-ping 正常上报({len(pings)} 次)')
        try:
            page.wait_for_function("() => /\\/100/.test(document.querySelector('#cbWrap .cb-badge').textContent)",
                                   timeout=20000)
            ok = True
        except Exception:
            ok = False
        check(ok, f'解锁后头顶切到分数「{page.locator("#cbWrap .cb-badge").inner_text()}」')
        shot(page, '02-unlocked')

        # ---- 4. 答题 → 关闭 → 刷新 → 续答 ----
        page.click('#cbWrap .cb-pet')
        page.wait_for_timeout(500)
        check(page.locator('#cbPanel [data-tab=exam]').is_enabled(), '考核标签可用')
        page.click('#cbPanel [data-tab=exam]')
        page.wait_for_selector('#cbBody .cb-qtext', timeout=15000)
        qtext = page.locator('#cbBody .cb-qtext').inner_text()
        # 只比选项正文:键位字形在多选题作答前后不同(未作答 ''/'✓',作答后 A/B/C),不能一起比
        OPTS_JS = ("() => [...document.querySelectorAll('#cbBody .cb-opt span:last-child, #cbBody .cb-judge button')]"
                   ".map(e => e.textContent)")
        opts_before = page.evaluate(OPTS_JS)
        if page.locator('#cbBody .cb-judge button').count():
            page.locator('#cbBody .cb-judge button').first.click()
        else:
            page.locator('#cbBody .cb-opt').first.click()
        focused = page.evaluate("() => !!document.activeElement && document.activeElement.matches('[data-i], [data-v]')")
        check(focused, '点选项后键盘焦点仍在该选项上')
        page.click('#cbFoot #cbSubmit')
        page.wait_for_selector('#cbBody .cb-explain', timeout=15000)
        result_before = page.locator('#cbBody .cb-explain').inner_text()
        shot(page, '03-answered')
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)
        page.reload()
        page.wait_for_selector('#cbWrap .cb-pet', state='visible', timeout=20000)
        page.wait_for_function("() => /\\/100/.test(document.querySelector('#cbWrap .cb-badge').textContent)", timeout=20000)
        page.click('#cbWrap .cb-pet')
        page.wait_for_timeout(400)
        if 'cb-on' not in (page.locator('#cbPanel [data-tab=exam]').get_attribute('class') or ''):
            page.click('#cbPanel [data-tab=exam]')
        page.wait_for_selector('#cbBody .cb-qtext', timeout=15000)
        page.wait_for_selector('#cbBody .cb-explain', timeout=15000)
        same_q = page.locator('#cbBody .cb-qtext').inner_text() == qtext
        opts_after = page.evaluate(OPTS_JS)
        same_res = page.locator('#cbBody .cb-explain').inner_text() == result_before
        check(same_q and opts_after == opts_before and same_res, '刷新后续答:同一题、同一选项顺序、同一结果态')
        check(page.locator('#cbFoot #cbNext').is_visible(), '结果态底栏「下一题」可见')
        shot(page, '04-resumed')

        # ---- 5. 课程内提问带 course_key ----
        page.click('#cbPanel [data-tab=ask]')
        chips = page.evaluate("() => [...document.querySelectorAll('#cbBody .cb-chip')].map(c => c.className.includes('cb-on'))")
        check(chips == [True, False], f'课程内提问默认「本课程」范围 {chips}')
        page.fill('#cbInput', '智能任务对讲有哪些功能?')
        page.click('#cbSend')
        page.wait_for_function("() => !document.querySelector('#cbBody .cb-typing')", timeout=150000)
        sent = asks[-1] if asks else ''
        check(f'"course_key": "{KEY}"' in (sent or '').replace('":"', '": "'), f'提问请求带 course_key({sent})')
        shot(page, '05-ask-course')
        browser.close()

    print('INFO 全部 console/page 错误:', len(errors))
    for e in errors:
        print('     ' + e[:300])
    own = [e for e in errors if 'course-buddy' in e or 'CourseBuddy' in e or 'cpCheckExam' in e or 'cpExam' in e]
    check(not own, f'无来自小源/播放器考核残留的错误({len(own)})')
    check(not any(e.startswith('pageerror') for e in errors), '无未捕获 pageerror')


def cleanup():
    return delete_temp_user(app, USERNAME) & delete_temp_bank(app, QPREFIX)


proc = None
SEED_KEYS = []
try:
    cleanup()
    uid = create_temp_user(app, USERNAME, PASSWORD)
    add_temp_bank(app, KEY, QPREFIX)
    set_min_read()
    check_query_scope(uid)
    SEED_KEYS = empty_seed_keys(app)          # 本次可能被自动导入种子题库的课,结束时删掉
    proc = start_server(args.port, os.path.join(args.shots, 'server.log'), KEY)
    print('INFO 服务已启动', BASE)
    run_browser()
finally:
    stop_server(proc)
    check(delete_seed_imports(app, SEED_KEYS), f'清理:自动导入的种子题已硬删({SEED_KEYS})')
    check(restore_min_read(), '清理:course_exam_settings 已还原')
    check(cleanup(), '清理:临时账号与 ZZE2P 题已硬删')
    print('\n' + ('全部通过' if not fails else f'{len(fails)} 项失败:\n  - ' + '\n  - '.join(fails)))
sys.exit(1 if fails else 0)
