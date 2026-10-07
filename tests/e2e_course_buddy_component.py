#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""小源组件(course-buddy.js)浏览器验证 —— Python Playwright + 本机 pma_local 临时实例。

覆盖:
  1. 两个 AT 页(首页仪表盘 / 知识库)都挂载小源且只挂一次
  2. 拖动吸附左右;侧栏收起/固定展开时左吸附跟随;拖出边缘藏起、点击弹回
  3. 面板打开;提问 tab 发问(AI 不可用时应出错误气泡,不能有 JS 错误)
  4. 课程外考核 tab:列出课程 → 进入一门课 → 作答 → 结果着色 → 下一题;
     exam/current 响应不含 answer/explain
  5. 课程播放页 setCourse:头顶小牌「阅读 x%」、考核标签禁用、15s 阅读上报、避让讲解栏
  6. 390×844 底部抽屉;暗色截图
  7. 会话失效:提问出现「重新登录」提示
  8. 收集 pageerror / console error

运行(在 worktree 根目录):
  export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib
  ../../venv/bin/python tests/e2e_course_buddy_component.py [--port 5094] [--shots DIR]

自清理:临时账号 zz_cb_e2e 及其所有关联行、ZZE2E- 临时题全部硬删;临时服务进程结束时终止。
"""
import argparse
import os
import sys
import tempfile


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
                          delete_temp_user, add_temp_bank, delete_temp_bank,
                          empty_seed_keys, delete_seed_imports)

USERNAME = 'zz_cb_e2e'
PASSWORD = 'CbE2e-Only-2026!'
EXAM_KEY = 'smart-task-intercom'       # 课程外考核:给临时账号解锁 + 临时题库
LOCKED_KEY = 'evertac-pnr2100'         # 课程内:临时账号未解锁
QPREFIX = 'ZZE2E-'

ap = argparse.ArgumentParser()
ap.add_argument('--port', type=int, default=5094)
ap.add_argument('--shots', default=os.path.join(tempfile.gettempdir(), 'pma-e2e-shots', 'cb-shots'))
ap.add_argument('--headed', action='store_true')
args = ap.parse_args()
os.makedirs(args.shots, exist_ok=True)
BASE = f'http://127.0.0.1:{args.port}'

app = make_app()

from app import db  # noqa: E402
from sqlalchemy import text  # noqa: E402

fails = []
UID = None


def check(cond, msg):
    print(('OK   ' if cond else 'FAIL ') + msg, flush=True)
    if not cond:
        fails.append(msg)


def cleanup():
    """硬删临时账号(含所有外键关联行)+ ZZE2E- 临时题。"""
    return delete_temp_user(app, USERNAME) & delete_temp_bank(app, QPREFIX)


def setup():
    from app.models.course_exam import CourseLearningProgress
    from app.models.training import get_local_time
    uid = create_temp_user(app, USERNAME, PASSWORD)
    add_temp_bank(app, EXAM_KEY, QPREFIX)          # 题库健康,小源课程列表会列出该课
    with app.app_context():
        db.session.add(CourseLearningProgress(user_id=uid, course_key=EXAM_KEY, page_seconds={},
                                              score=0, unlocked_at=get_local_time()))
        db.session.commit()
    return uid


def run_browser():
    from playwright.sync_api import sync_playwright
    errors, exam_payloads, pings = [], [], []

    def shot(page, name):
        p = os.path.join(args.shots, name + '.png')
        page.screenshot(path=p)
        print('     shot ' + p)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not args.headed)
        ctx = browser.new_context(viewport={'width': 1440, 'height': 900}, locale='zh-CN')
        # 页面级 rAF 计数(含页面自身脚本),用于空闲开销对比
        ctx.add_init_script("""(() => { window.CB_DEBUG = true; window.__rafCalls = 0; const o = window.requestAnimationFrame.bind(window);
            window.requestAnimationFrame = (cb) => o((t) => { window.__rafCalls++; cb(t); }); })()""")
        page = ctx.new_page()

        def on_console(m):
            if m.type == 'error':
                errors.append(f'console[{page.url}]: {m.text} @ {m.location.get("url", "")}')

        def on_response(r):
            u = r.url
            if '/exam/current' in u or '/exam/next' in u:
                try:
                    exam_payloads.append(r.json())
                except Exception:
                    pass
            if '/read-ping' in u:
                pings.append(r.status)

        page.on('console', on_console)
        page.on('pageerror', lambda e: errors.append(f'pageerror[{page.url}]: {e}'))
        page.on('response', on_response)

        # ---- 登录 ----
        page.goto(BASE + '/auth/login')
        page.fill('#username', USERNAME)
        page.fill('#password', PASSWORD)
        page.click('button[type=submit]')
        page.wait_for_load_state('networkidle')
        check('/auth/login' not in page.url, f'登录成功(当前 {page.url})')
        # ---- 0. 空闲渲染开销(CDP):面板关闭、无操作 6s 后,5s 内的重排/样式重算/rAF 次数 ----
        page.goto(BASE + '/')
        page.wait_for_selector('#cbWrap .cb-pet', state='visible')
        page.mouse.move(700, 450)
        # 无操作 ~10s 后小源完全静止(游移/眨眼停止);再多等 1s 余量后开始计 5s
        page.wait_for_timeout(12500)
        cdp = ctx.new_cdp_session(page)
        cdp.send('Performance.enable')

        def metrics():
            m = {x['name']: x['value'] for x in cdp.send('Performance.getMetrics')['metrics']}
            m['cbFrames'] = page.evaluate('() => window.__cbFrames || 0')
            m['rafCalls'] = page.evaluate('() => window.__rafCalls || 0')
            return m
        m1 = metrics()
        page.wait_for_timeout(5000)
        m2 = metrics()
        idle = {k: m2[k] - m1[k] for k in ('LayoutCount', 'RecalcStyleCount', 'cbFrames', 'rafCalls')}
        print('INFO 空闲 5s 指标增量:', idle)
        check(idle['cbFrames'] == 0, f'空闲时小源 rAF 已停帧(cbFrames 增量 {idle["cbFrames"]})')
        check(idle['LayoutCount'] <= 2 and idle['RecalcStyleCount'] <= 6,
              f'空闲时重排/样式重算接近 0(Layout {idle["LayoutCount"]}, RecalcStyle {idle["RecalcStyleCount"]})')
        cdp.detach()
        # 呼吸动画(无限 CSS 动画)空闲时也必须暂停:合成器未接管时它会在主线程逐帧重排(偶发 600 次/5s)
        breath = page.evaluate("() => { const a = document.querySelector('#cbWrap .cb-breathe').getAnimations(); return a.length ? a[0].playState : 'none'; }")
        check(breath == 'paused', f'空闲时呼吸动画暂停(playState {breath})')
        page.mouse.move(720, 470)
        page.wait_for_timeout(300)
        breath = page.evaluate("() => { const a = document.querySelector('#cbWrap .cb-breathe').getAnimations(); return a.length ? a[0].playState : 'none'; }")
        check(breath == 'running', f'有操作后呼吸动画恢复(playState {breath})')

        page.wait_for_timeout(2500)        # 等登录落地页上的首次问候跑完,再清状态,避免竞态
        page.evaluate("""() => { sessionStorage.removeItem('cb-hello');
            Object.keys(localStorage).filter(k => k.startsWith('cb-')).forEach(k => localStorage.removeItem(k));
            localStorage.setItem('at-sidebar-pinned','0');
            // 旧版未分用户的对话 + 其他账号的对话:加载后应被清掉
            localStorage.setItem('cb-chat', '[{"me":true,"t":"legacy"}]');
            localStorage.setItem('cb-chat:999999', '[{"me":true,"t":"other"}]'); }""")

        # ---- 1. 两个 AT 页挂载 ----
        for path, name in (('/', 'dashboard'), ('/wiki/at', 'wiki')):
            page.goto(BASE + path)
            page.wait_for_selector('#cbWrap .cb-pet', state='visible', timeout=15000)
            n = page.evaluate("() => document.querySelectorAll('.cb-wrap').length")
            check(n == 1, f'{name} 页小源出现且仅 1 个(实际 {n})')
            if name == 'dashboard':
                gone = page.evaluate("() => localStorage.getItem('cb-chat') === null && localStorage.getItem('cb-chat:999999') === null")
                check(gone, '加载时清掉旧版未分用户对话与其他账号对话')
                z = page.evaluate("() => +getComputedStyle(document.getElementById('cbWrap')).zIndex")
                check(z < 100, f'小源本体层级低于 AT 模态(z-index={z})')
                try:
                    page.wait_for_function("() => !!document.querySelector('.cb-bubble:not(.cb-off)')", timeout=8000)
                except Exception:
                    pass
                bub = page.evaluate("() => { const b = document.querySelector('.cb-bubble:not(.cb-off)'); return b ? b.textContent : null; }")
                check(bool(bub), f'首个页面小源说话气泡(每日提醒/问候)「{bub}」')
                nag = page.evaluate("(u) => localStorage.getItem('cb-nag-date:' + u)", UID)
                check(bool(nag), f'每日提醒已记日期 cb-nag-date={nag}')
            shot(page, f'01-{name}')

        page.goto(BASE + '/')
        page.wait_for_selector('#cbWrap .cb-pet', state='visible')
        page.wait_for_timeout(1500)
        check(not page.evaluate("() => !!document.querySelector('.cb-bubble:not(.cb-off)')"),
              '同一会话再次进入页面不重复提醒')

        # ---- 2. 拖动吸附 / 侧栏跟随 / 藏边 ----
        def wrap_box():
            return page.evaluate("""() => { const w = document.getElementById('cbWrap'), r = w.getBoundingClientRect();
                const s = document.querySelector('aside.at-sidebar').getBoundingClientRect();
                return {left: r.left, right: r.right, cls: w.className, sb: s.right, styleLeft: w.style.left}; }""")

        def drag_to(x, y):
            b = page.locator('#cbWrap .cb-pet').bounding_box()
            page.mouse.move(b['x'] + b['width'] / 2, b['y'] + b['height'] / 2)
            page.mouse.down()
            page.mouse.move(b['x'] + b['width'] / 2 - 20, b['y'] + b['height'] / 2, steps=3)
            page.mouse.move(x, y, steps=12)
            page.mouse.up()
            page.mouse.move(700, 450)
            page.wait_for_timeout(700)

        drag_to(400, 500)
        sel = page.evaluate("() => window.getSelection().toString() + '|' + (document.documentElement.style.userSelect || '')")
        check(sel == '|', f'拖动不选中页面文字且结束后恢复 user-select({sel!r})')
        b = wrap_box()
        check('cb-side-left' in b['cls'] and abs(b['left'] - (b['sb'] + 12)) < 3,
              f'拖到左半屏吸附左侧并贴侧栏右缘(left={b["left"]:.0f}, 侧栏右缘={b["sb"]:.0f})')
        shot(page, '02-snap-left-collapsed')
        page.mouse.move(900, 450)
        page.evaluate("() => document.getElementById('atSidebarToggle').click()")
        page.wait_for_timeout(900)
        b = wrap_box()
        check(b['sb'] > 200 and abs(b['left'] - (b['sb'] + 12)) < 3,
              f'侧栏固定展开后跟随(left={b["left"]:.0f}, 侧栏右缘={b["sb"]:.0f})')
        shot(page, '03-snap-left-pinned')
        page.mouse.move(900, 450)
        page.evaluate("() => document.getElementById('atSidebarToggle').click()")
        page.wait_for_timeout(900)
        b = wrap_box()
        check(b['sb'] < 100 and abs(b['left'] - (b['sb'] + 12)) < 3,
              f'侧栏收起后跟随回去(left={b["left"]:.0f})')
        drag_to(1100, 400)
        b = wrap_box()
        check('cb-side-right' in b['cls'] and abs(b['right'] - (1440 - 12)) < 3,
              f'拖到右半屏吸附右侧(right={b["right"]:.0f})')
        drag_to(1438, 400)
        page.wait_for_timeout(300)
        b = wrap_box()
        check('cb-tucked' in b['cls'], '拖出右边缘 → 藏边')
        shot(page, '04-tucked')
        page.locator('#cbWrap .cb-pet').click(position={'x': 20, 'y': 48}, force=True)
        page.wait_for_timeout(600)
        b = wrap_box()
        check('cb-tucked' not in b['cls'], '点击藏边的小源 → 弹回')
        pos = page.evaluate("() => JSON.parse(localStorage.getItem('cb-pos'))")
        check(pos and pos.get('side') == 'right' and pos.get('tucked') is False, f'位置已记忆 {pos}')

        # ---- 3. 面板 + 提问 ----
        page.click('#cbWrap .cb-pet')
        page.wait_for_timeout(500)
        check(page.evaluate("() => !document.getElementById('cbPanel').classList.contains('cb-off')"), '点击小源打开面板')
        check(page.locator('#cbTitle').inner_text().strip() != '', '面板标题已渲染')
        shot(page, '05-panel-ask')
        page.fill('#cbInput', '和源的智能任务对讲有什么特点?')
        # 回答可能瞬间返回(本地无 AI 时 500),用 MutationObserver 记录是否出现过输入中状态
        page.evaluate("""() => { window.__cbSeen = {typing: false, disabled: false};
            new MutationObserver(() => {
              if (document.querySelector('#cbBody .cb-typing')) window.__cbSeen.typing = true;
              if (document.getElementById('cbSend').disabled) window.__cbSeen.disabled = true;
            }).observe(document.getElementById('cbPanel'), {subtree: true, childList: true, attributes: true}); }""")
        page.click('#cbSend')
        page.wait_for_timeout(300)
        seen = page.evaluate("() => window.__cbSeen")
        check(seen['typing'] and seen['disabled'], f'发送后出现输入中三点、发送按钮禁用 {seen}')
        page.wait_for_function("() => !document.querySelector('#cbBody .cb-typing')", timeout=150000)
        n_bot = page.evaluate("() => document.querySelectorAll('#cbBody .cb-msg.cb-bot').length")
        err = page.evaluate("() => !!document.querySelector('#cbBody .cb-msg.cb-err')")
        check(n_bot >= 2, f'收到回答气泡({"错误气泡" if err else "正常回答"})')
        stored = page.evaluate("""() => { const k = Object.keys(localStorage).filter(k => k.startsWith('cb-chat:'));
            return {keys: k, n: k.length === 1 ? (JSON.parse(localStorage.getItem(k[0])) || []).length : -1}; }""")
        check(stored['n'] == 2 and stored['keys'] == [f'cb-chat:{UID}'], f'对话按用户存 localStorage {stored}')
        shot(page, '06-ask-answer')

        # ---- 4. 课程外考核 ----
        page.click('#cbPanel [data-tab=exam]')
        page.wait_for_selector('#cbBody .cb-citem, #cbBody .cb-locked', timeout=15000)
        items = page.evaluate("() => [...document.querySelectorAll('#cbBody .cb-citem .cb-n')].map(e => e.textContent)")
        check(len(items) >= 1, f'课程外考核列出课程 {items}')
        shot(page, '07-exam-list')
        idx = page.evaluate("""(key) => { const tt = document.querySelectorAll('#cbBody .cb-citem');
                 for (let i = 0; i < tt.length; i++) if (!tt[i].classList.contains('cb-dim')) return i; return -1; }""", EXAM_KEY)
        check(idx >= 0, '有已解锁课程可进入')
        if idx >= 0:
            page.locator('#cbBody .cb-citem').nth(idx).click()
            page.wait_for_selector('#cbBody .cb-qtext', timeout=15000)
            check(page.locator('#cbFoot #cbSubmit').is_disabled(), '未作答时「提交答案」(底栏)置灰')
            if page.locator('#cbBody .cb-judge button').count():
                page.locator('#cbBody .cb-judge button').first.click()
            else:
                page.locator('#cbBody .cb-opt').first.click()
            check(page.locator('#cbSubmit').is_enabled(), '选择后「提交答案」可点')
            shot(page, '08-exam-question')
            page.click('#cbSubmit')
            page.wait_for_selector('#cbBody .cb-explain', timeout=15000)
            right = page.evaluate("() => document.querySelectorAll('#cbBody .cb-right').length")
            check(right >= 1, f'结果态:正确项绿色标出({right} 个)')
            check(page.locator('#cbFoot #cbNext').is_visible(), '结果态「下一题」在固定底栏且可见')
            shot(page, '09-exam-result')
            page.click('#cbNext')
            page.wait_for_selector('#cbBody .cb-qtext', timeout=15000)
            page.wait_for_function("() => !document.querySelector('#cbBody .cb-explain')", timeout=15000)
            check(True, '下一题已加载')

        def leak(o):
            if isinstance(o, dict):
                return any(k in ('answer', 'explain') or leak(v) for k, v in o.items())
            if isinstance(o, list):
                return any(leak(v) for v in o)
            return False
        unanswered = [p for p in exam_payloads if isinstance(p, dict) and (p.get('data') or {}).get('answered') is False]
        check(unanswered and not any(leak(p) for p in unanswered),
              f'未作答的 exam/current|next 响应不含 answer/explain({len(unanswered)} 个)')
        page.keyboard.press('Escape')
        page.wait_for_timeout(400)
        check(page.evaluate("() => document.getElementById('cbPanel').classList.contains('cb-off')"), 'Esc 关闭面板')
        a11y = page.evaluate("""() => ({focusPet: document.activeElement && document.activeElement.classList.contains('cb-pet'),
            expanded: document.querySelector('.cb-pet').getAttribute('aria-expanded'),
            modal: document.getElementById('cbPanel').getAttribute('aria-modal')})""")
        check(a11y['focusPet'] and a11y['expanded'] == 'false' and a11y['modal'] == 'true', f'关闭后焦点回到小源、aria 状态正确 {a11y}')

        # ---- 5. 课程内(播放页 + setCourse) ----
        page.goto(BASE + f'/wiki/play/{LOCKED_KEY}')
        page.wait_for_selector('#cbWrap .cb-pet', state='visible', timeout=15000)
        page.evaluate("(k) => window.CourseBuddy.setCourse({key: k, title: 'PNR2100', totalPages: 19})", LOCKED_KEY)
        page.wait_for_function("() => !document.querySelector('#cbWrap .cb-badge').hidden", timeout=15000)
        badge = page.locator('#cbWrap .cb-badge').inner_text()
        check('%' in badge, f'课程内未解锁:头顶小牌显示阅读进度「{badge}」')
        geo = page.evaluate("""() => { const r = document.getElementById('cbWrap').getBoundingClientRect();
            return {bottom: innerHeight - r.bottom, top: r.top}; }""")
        check(geo['bottom'] >= 11 and geo['top'] >= 0, f'播放页内小源完整可见、离底 ≥12px {geo}')
        page.click('#cbWrap .cb-pet')
        page.wait_for_timeout(500)
        check(page.locator('#cbPanel [data-tab=exam]').is_disabled(), '未解锁:考核标签禁用(显示阅读进度环)')
        check(page.locator('#cbPanel [data-tab=exam]').get_attribute('title') == '题库准备中，暂不能考核',
              '本课题库未就绪:考核标签悬停提示「题库准备中」')
        shot(page, '10-course-locked')
        page.keyboard.press('Escape')
        page.evaluate("() => window.CourseBuddy.onPage(2)")
        for _ in range(18):
            page.mouse.move(600 + _ * 3, 400)
            page.wait_for_timeout(1000)
        check(any(s == 200 for s in pings), f'阅读计时 15s 内上报 read-ping({pings})')

        # ---- 5a. 已读完但题库准备中:考核标签锁住并显示「准备中」 ----
        nr = ctx.new_page()
        nr.on('pageerror', lambda e: errors.append(f'pageerror[notready]: {e}'))
        nr.route('**/api/learning/zz-not-ready/progress', lambda route: route.fulfill(
            status=200, content_type='application/json',
            body='{"success": true, "data": {"read": {"percent": 100, "unlocked": true, "page_seconds": {}, '
                 '"required_seconds": 1, "effective_seconds": 1, "pages_seen": 1, "pages_total": 1}, '
                 '"exam": {"score": 0, "passed": false, "perfect": false, "available": false}}}'))
        nr.goto(BASE + '/')
        nr.wait_for_selector('#cbWrap .cb-pet', state='visible', timeout=15000)
        nr.evaluate("() => window.CourseBuddy.setCourse({key: 'zz-not-ready', title: 'NR', totalPages: 1})")
        nr.wait_for_timeout(800)
        nr.click('#cbWrap .cb-pet')
        nr.wait_for_timeout(500)
        tb = nr.locator('#cbPanel [data-tab=exam]')
        check(tb.is_disabled() and '准备中' in tb.inner_text() and tb.get_attribute('title') == '题库准备中，暂不能考核'
              and 'cb-on' not in (tb.get_attribute('class') or ''),
              f'已解锁但题库准备中:考核标签禁用并显示「{tb.inner_text()}」')
        shot(nr, '10b-bank-not-ready')
        nr.close()

        # ---- 5b. 面板「⋯」隐藏小源 → 侧栏头像菜单开关找回 ----
        h = ctx.new_page()
        h.on('pageerror', lambda e: errors.append(f'pageerror[hide]: {e}'))
        h.on('console', lambda m: m.type == 'error' and errors.append(f'console[hide]: {m.text}'))
        h.goto(BASE + '/')
        h.wait_for_selector('#cbWrap .cb-pet', state='visible', timeout=15000)
        h.click('#cbWrap .cb-pet')
        h.wait_for_timeout(500)
        h.click('#cbPanel .cb-more')
        check(h.locator('#cbMenu').is_visible() and h.locator('#cbMenu [data-act=ask-hide]').count() == 1,
              '「⋯」打开菜单,含「隐藏小源」')
        check(h.locator('#cbPanel .cb-more').get_attribute('aria-expanded') == 'true', '「⋯」aria-expanded=true')
        shot(h, '15-more-menu')
        h.click('#cbMenu [data-act=ask-hide]')
        check(h.locator('#cbMenu .cb-mconfirm').is_visible(), '点「隐藏小源」先出面板内确认(不弹 window.confirm)')
        shot(h, '16-hide-confirm')
        h.click('#cbMenu [data-act=cancel]')
        h.wait_for_timeout(200)
        check(h.locator('#cbMenu').is_hidden() and h.locator('#cbWrap').count() == 1, '「取消」收起菜单,小源仍在')
        h.click('#cbPanel .cb-more')
        h.keyboard.press('Escape')
        h.wait_for_timeout(200)
        check(h.locator('#cbMenu').is_hidden() and not h.evaluate(
            "() => document.getElementById('cbPanel').classList.contains('cb-off')"), 'Esc 先收起菜单,面板不关')
        h.click('#cbPanel .cb-more')
        h.click('#cbMenu [data-act=ask-hide]')
        h.click('#cbMenu [data-act=hide]')
        h.wait_for_function("() => !document.getElementById('cbWrap') && !document.getElementById('cbPanel')", timeout=10000)
        check(True, '确认隐藏 → 小源与面板从页面移除')
        en = h.evaluate("() => fetch('/api/learning/buddy', {credentials: 'same-origin'}).then(r => r.json()).then(j => j.data.enabled)")
        check(en is False, f'偏好已写为关闭(enabled={en})')
        check(h.locator('#atBuddyToggle').get_attribute('aria-checked') == 'false', '侧栏开关同步显示为关')
        h.reload()
        h.wait_for_load_state('networkidle')
        check(h.locator('#cbWrap').count() == 0 and h.evaluate("() => !window.CB_CONFIG"), '刷新后小源不再挂载')
        h.click('#atUserMenuTrigger')
        h.wait_for_timeout(300)
        check(h.locator('#atBuddyToggle').is_visible() and h.locator('#atBuddyToggle').get_attribute('aria-checked') == 'false',
              '头像菜单里「学习伙伴」开关为关')
        shot(h, '17-user-menu-off')
        # 会话过期(拿到 HTML):开关复原 + 明确提示,不静默
        h.route('**/api/learning/buddy/toggle', lambda route: route.fulfill(
            status=200, content_type='text/html', body='<html><body>login</body></html>'))
        h.click('#atBuddyToggle')
        h.wait_for_selector('#atBuddyToggleErr:not([hidden])', timeout=10000)
        err_txt = h.locator('#atBuddyToggleErr').inner_text()
        check('登录已过期' in err_txt and h.locator('#atBuddyToggle').get_attribute('aria-checked') == 'false',
              f'开关遇会话过期:复原为关并提示「{err_txt}」')
        shot(h, '17b-user-menu-expired')
        h.unroute('**/api/learning/buddy/toggle')
        # CSRF token 失效:自动换新 token 重试一次后成功
        probe = h.evaluate("""() => fetch(document.getElementById('atBuddyToggle').dataset.url, {method: 'POST',
            credentials: 'same-origin', headers: {'Content-Type': 'application/json', 'X-CSRFToken': 'stale-token'},
            body: JSON.stringify({enabled: false})}).then(r => r.json()).then(j => j.error)""")
        check(probe == 'csrf', f'服务端确实拒绝失效 CSRF token(error={probe})')
        h.evaluate("() => { document.getElementById('atBuddyToggle').dataset.csrf = 'stale-token'; delete window.CB_CSRF; }")
        if not h.locator('#atBuddyToggle').is_visible():
            h.click('#atUserMenuTrigger')
        with h.expect_navigation(timeout=15000):
            h.click('#atBuddyToggle')
        h.wait_for_selector('#cbWrap .cb-pet', state='visible', timeout=15000)
        check(True, '打开开关(旧 CSRF token 自动换新重试)→ 页面刷新后小源重新出现')
        h.click('#atUserMenuTrigger')
        h.wait_for_timeout(300)
        check(h.locator('#atBuddyToggle').get_attribute('aria-checked') == 'true', '头像菜单开关为开')
        shot(h, '18-user-menu-on')
        h.close()

        # ---- 6. 窄屏底部抽屉 + 暗色 ----
        m = ctx.new_page()
        m.on('pageerror', lambda e: errors.append(f'pageerror[mobile]: {e}'))
        m.set_viewport_size({'width': 390, 'height': 844})
        m.goto(BASE + '/')
        m.wait_for_selector('#cbWrap .cb-pet', state='visible', timeout=15000)
        m.click('#cbWrap .cb-pet')
        m.wait_for_timeout(600)
        r = m.evaluate("() => { const r = document.getElementById('cbPanel').getBoundingClientRect(); return {l: r.left, w: r.width, b: r.bottom, h: innerHeight}; }")
        check(abs(r['l']) < 1 and abs(r['w'] - 390) < 1 and abs(r['b'] - r['h']) < 1, f'390 宽:面板为全宽底部抽屉 {r}')
        shot(m, '11-mobile-sheet')
        m.evaluate("() => document.documentElement.setAttribute('data-theme','dark')")
        m.wait_for_timeout(300)
        shot(m, '12-mobile-dark')
        m.close()
        page.goto(BASE + '/')
        page.wait_for_selector('#cbWrap .cb-pet', state='visible')
        page.evaluate("() => document.documentElement.setAttribute('data-theme','dark')")
        page.click('#cbWrap .cb-pet')
        page.wait_for_timeout(500)
        shot(page, '13-desktop-dark')

        # ---- 7. 会话失效 ----
        ctx.clear_cookies()
        page.fill('#cbInput', 'ping')
        page.click('#cbSend')
        try:
            page.wait_for_selector('#cbBody .cb-note a[href*="login"]', timeout=15000)
            ok = True
        except Exception:
            ok = False
        check(ok, '会话失效:面板出现「重新登录」提示链接')
        shot(page, '14-expired')

        browser.close()

    own = [e for e in errors if 'course-buddy' in e or 'CourseBuddy' in e or 'cb-' in e]
    print('INFO 全部 console/page 错误:', len(errors))
    for e in errors:
        print('     ' + e[:300])
    check(not own, f'无来自 course-buddy.js 的错误({len(own)})')
    check(not any(e.startswith('pageerror') for e in errors), '无未捕获 pageerror')


proc = None
SEED_KEYS = []
try:
    cleanup()
    uid = setup()
    UID = uid
    print('INFO 临时账号 id', uid)
    SEED_KEYS = empty_seed_keys(app)          # 本次可能被自动导入种子题库的课,结束时删掉
    proc = start_server(args.port, os.path.join(args.shots, 'server.log'), EXAM_KEY)
    print('INFO 服务已启动', BASE)
    run_browser()
finally:
    stop_server(proc)
    check(delete_seed_imports(app, SEED_KEYS), f'清理:自动导入的种子题已硬删({SEED_KEYS})')
    check(cleanup(), '清理:临时账号与 ZZE2E 题已硬删')
    print('\n' + ('全部通过' if not fails else f'{len(fails)} 项失败:\n  - ' + '\n  - '.join(fails)))
sys.exit(1 if fails else 0)
