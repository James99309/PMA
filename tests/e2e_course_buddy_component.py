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
import json
import os
import signal
import subprocess
import sys
import time
import urllib.request


def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")


ROOT = get_project_root()
sys.path.insert(0, os.path.join(ROOT, 'scripts', 'temp'))
from _report_flow_testkit import make_app  # noqa: E402

USERNAME = 'zz_cb_e2e'
PASSWORD = 'CbE2e-Only-2026!'
EXAM_KEY = 'smart-task-intercom'       # 课程外考核:给临时账号解锁 + 临时题库
LOCKED_KEY = 'evertac-pnr2100'         # 课程内:临时账号未解锁
QPREFIX = 'ZZE2E-'
MAIN_ASSETS = os.path.normpath(os.path.join(ROOT, '..', '..', 'app', 'course_assets'))

ap = argparse.ArgumentParser()
ap.add_argument('--port', type=int, default=5094)
ap.add_argument('--shots', default=os.path.join(ROOT, 'data', 'temp', 'cb-shots'))
ap.add_argument('--headed', action='store_true')
args = ap.parse_args()
os.makedirs(args.shots, exist_ok=True)
BASE = f'http://127.0.0.1:{args.port}'

app = make_app()

from app import db  # noqa: E402
from sqlalchemy import text  # noqa: E402

fails = []


def check(cond, msg):
    print(('OK   ' if cond else 'FAIL ') + msg, flush=True)
    if not cond:
        fails.append(msg)


def cleanup():
    """硬删临时账号及其所有外键关联行 + 临时题。只动 zz_cb_e2e 和 ZZE2E- 前缀数据。"""
    with app.app_context():
        uid = db.session.execute(text('SELECT id FROM users WHERE username=:u'), {'u': USERNAME}).scalar()
        if uid:
            fks = db.session.execute(text("""
                SELECT tc.table_name, kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage ccu
                  ON ccu.constraint_name = tc.constraint_name AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' AND ccu.table_name = 'users'
                  AND ccu.column_name = 'id' AND tc.table_schema = 'public'""")).fetchall()
            # 作答留痕没有外键,单独删
            db.session.execute(text("DELETE FROM training_quiz_attempt WHERE user_id=:u"), {'u': uid})
            for _ in range(3):           # 关联表之间可能互相引用,多轮删到干净
                for table, col in fks:
                    if table == 'users':
                        continue
                    try:
                        with db.session.begin_nested():
                            db.session.execute(text(f'DELETE FROM "{table}" WHERE "{col}" = :u'), {'u': uid})
                    except Exception:
                        pass
            db.session.execute(text('DELETE FROM users WHERE id=:u'), {'u': uid})
        db.session.execute(text("DELETE FROM course_quiz_questions WHERE question LIKE :p"), {'p': QPREFIX + '%'})
        db.session.commit()
        left = db.session.execute(text('SELECT count(*) FROM users WHERE username=:u'), {'u': USERNAME}).scalar()
        leftq = db.session.execute(text("SELECT count(*) FROM course_quiz_questions WHERE question LIKE :p"),
                                   {'p': QPREFIX + '%'}).scalar()
        return left == 0 and leftq == 0


def setup():
    from app.models.user import User
    from app.models.course_exam import CourseQuizQuestion, CourseLearningProgress
    from app.models.training import get_local_time
    with app.app_context():
        company = db.session.execute(text(
            "SELECT company_name FROM users WHERE company_name IS NOT NULL AND company_name<>'' "
            "GROUP BY company_name ORDER BY count(*) DESC LIMIT 1")).scalar() or 'ZZ'
        u = User(username=USERNAME, real_name='ZZ CB E2E', company_name=company,
                 email='zz_cb_e2e@example.invalid', role='sales_manager')
        u.set_password(PASSWORD)
        u._is_active = True
        db.session.add(u)
        db.session.flush()
        # 34 道难题(3 分)= 102 分,题库健康,小源课程列表会列出该课
        for i in range(30):
            db.session.add(CourseQuizQuestion(course_key=EXAM_KEY, qtype='single', difficulty=3,
                                              question=f'{QPREFIX}single {i}', options=['A1', 'B2', 'C3', 'D4'],
                                              answer=0, explain='ZZ explain', source_page=2, status='active'))
        for i in range(2):
            db.session.add(CourseQuizQuestion(course_key=EXAM_KEY, qtype='multi', difficulty=3,
                                              question=f'{QPREFIX}multi {i}', options=['M1', 'M2', 'M3', 'M4'],
                                              answer=[0, 2], explain='ZZ explain', status='active'))
            db.session.add(CourseQuizQuestion(course_key=EXAM_KEY, qtype='judge', difficulty=3,
                                              question=f'{QPREFIX}judge {i}', options=None,
                                              answer=True, explain='ZZ explain', status='active'))
        db.session.add(CourseLearningProgress(user_id=u.id, course_key=EXAM_KEY, page_seconds={},
                                              score=0, unlocked_at=get_local_time()))
        db.session.commit()
        return u.id


SERVER_CODE = r'''
import os, sys
sys.path.insert(0, os.path.join(os.getcwd(), 'scripts', 'temp'))
from _report_flow_testkit import make_app
flask_app = make_app()
import app.views.knowledge_wiki as KW
main_assets = sys.argv[2]
if not os.path.isfile(KW._course_html_path(sys.argv[3])) and os.path.isdir(main_assets):
    KW.COURSE_ASSETS_DIR = main_assets      # worktree 没有课件(gitignored),只读借用主仓
flask_app.run(host='127.0.0.1', port=int(sys.argv[1]), use_reloader=False, threaded=True)
'''


def start_server():
    env = dict(os.environ)
    env.update({'PORT': str(args.port), 'DYLD_FALLBACK_LIBRARY_PATH': '/opt/homebrew/lib',
                'DATABASE_URL': 'postgresql://nijie@localhost:5432/pma_local',
                'PMA_DB_TYPE': 'sp8d', 'FORCE_LOCAL_STORAGE': 'true'})
    log = open(os.path.join(args.shots, 'server.log'), 'w')
    proc = subprocess.Popen([sys.executable, '-c', SERVER_CODE, str(args.port), MAIN_ASSETS, EXAM_KEY],
                            cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    deadline = time.time() + 120
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError('服务进程提前退出,见 server.log')
        try:
            urllib.request.urlopen(BASE + '/auth/login', timeout=3)
            return proc
        except Exception:
            time.sleep(1)
    raise RuntimeError('服务启动超时')


def stop_server(proc):
    if proc and proc.poll() is None:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=15)
        except Exception:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except Exception:
                pass


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
        page.wait_for_timeout(2500)        # 等登录落地页上的首次问候跑完,再清状态,避免竞态
        page.evaluate("""() => { sessionStorage.removeItem('cb-hello'); localStorage.removeItem('cb-pos'); localStorage.removeItem('cb-chat');
                                 localStorage.removeItem('cb-nag-date'); localStorage.setItem('at-sidebar-pinned','0'); }""")

        # ---- 1. 两个 AT 页挂载 ----
        for path, name in (('/', 'dashboard'), ('/wiki/at', 'wiki')):
            page.goto(BASE + path)
            page.wait_for_selector('#cbWrap .cb-pet', state='visible', timeout=15000)
            n = page.evaluate("() => document.querySelectorAll('.cb-wrap').length")
            check(n == 1, f'{name} 页小源出现且仅 1 个(实际 {n})')
            if name == 'dashboard':
                try:
                    page.wait_for_function("() => !!document.querySelector('.cb-bubble:not(.cb-off)')", timeout=8000)
                except Exception:
                    pass
                bub = page.evaluate("() => { const b = document.querySelector('.cb-bubble:not(.cb-off)'); return b ? b.textContent : null; }")
                check(bool(bub), f'首个页面小源说话气泡(每日提醒/问候)「{bub}」')
                nag = page.evaluate("() => localStorage.getItem('cb-nag-date')")
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
        stored = page.evaluate("() => (JSON.parse(localStorage.getItem('cb-chat'))||[]).length")
        check(stored == 2, f'对话已存 localStorage cb-chat({stored} 条)')
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
            check(page.locator('#cbSubmit').is_disabled(), '未作答时「提交答案」置灰')
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
            check(page.locator('#cbNext').is_visible(), '结果态出现「下一题」')
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

        # ---- 5. 课程内(播放页 + setCourse) ----
        page.goto(BASE + f'/wiki/play/{LOCKED_KEY}')
        page.wait_for_selector('#cbWrap .cb-pet', state='visible', timeout=15000)
        page.evaluate("(k) => window.CourseBuddy.setCourse({key: k, title: 'PNR2100', totalPages: 19})", LOCKED_KEY)
        page.wait_for_function("() => !document.querySelector('#cbWrap .cb-badge').hidden", timeout=15000)
        badge = page.locator('#cbWrap .cb-badge').inner_text()
        check('%' in badge, f'课程内未解锁:头顶小牌显示阅读进度「{badge}」')
        geo = page.evaluate("""() => { const n = document.getElementById('cpNotes'), w = document.getElementById('cbWrap');
            return {nh: n && n.offsetParent ? n.offsetHeight : 0, bottom: parseFloat(w.style.bottom)}; }""")
        check(geo['bottom'] >= geo['nh'] + 10 - 1, f'避让讲解栏(bottom={geo["bottom"]}, 讲解栏高={geo["nh"]})')
        page.click('#cbWrap .cb-pet')
        page.wait_for_timeout(500)
        check(page.locator('#cbPanel [data-tab=exam]').is_disabled(), '未解锁:考核标签禁用(显示阅读进度环)')
        shot(page, '10-course-locked')
        page.keyboard.press('Escape')
        page.evaluate("() => window.CourseBuddy.onPage(2)")
        for _ in range(18):
            page.mouse.move(600 + _ * 3, 400)
            page.wait_for_timeout(1000)
        check(any(s == 200 for s in pings), f'阅读计时 15s 内上报 read-ping({pings})')

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
try:
    cleanup()
    uid = setup()
    print('INFO 临时账号 id', uid)
    proc = start_server()
    print('INFO 服务已启动', BASE)
    run_browser()
finally:
    stop_server(proc)
    check(cleanup(), '清理:临时账号与 ZZE2E 题已硬删')
    print('\n' + ('全部通过' if not fails else f'{len(fails)} 项失败:\n  - ' + '\n  - '.join(fails)))
sys.exit(1 if fails else 0)
