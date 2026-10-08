#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""培训管理 端到端验证 —— Python Playwright + 本机 pma_local 临时实例。

覆盖:
  1. HR(hr_manager):知识库「培训管理」入口 → 总览矩阵 → 某课切「仅指定学员」(页面内确认条)
     → 按人添加 → 按部门添加(限定本公司)→ 行内确认移除 → 设审核人 → 成绩表 + 明细抽屉
  2. 普通销售:被拉入前看不到 restricted 课(知识库无卡片、播放页 404);拉入后可见、有站内通知、「我的培训」出现该课
  3. 审核人:播放页有「题库管理」;题库页无「生成题库」;能编辑(只改 ZZ 临时题)
  4. 有下属的经理:能进培训管理但只看成绩(只含下属);普通人 403
  5. 无未捕获 pageerror / 培训页 console error

全程只用 ZZ 临时课程 zz-train-e2e-course(make_temp_course,课件软链借用 smart-task-intercom),
结束 drop_temp_course 删掉该课全部行;不切换、不改动任何真实课程,真实题与真实进度不碰。

运行(worktree 根目录):
  export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib
  ../../venv/bin/python tests/e2e_training_mgmt.py --port 5093 [--shots DIR]
"""
import argparse
import os
import re
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
                          empty_seed_keys, delete_seed_imports, make_temp_course, drop_temp_course)

PASSWORD = 'TrainE2e-Mgmt-2026!'
XREV = 'zz_tr_e2e_xrev'          # 别的公司的人:验证跨公司审核人可选 / 可显示 / 可移除
XCOMPANY = 'ZZ 外部测试公司'
HR, MGR, SUB, SALES, REV, D1 = ('zz_tr_e2e_hr', 'zz_tr_e2e_mgr', 'zz_tr_e2e_sub',
                                'zz_tr_e2e_s', 'zz_tr_e2e_rev', 'zz_tr_e2e_d1')
USERS = [HR, MGR, SUB, SALES, REV, D1, XREV]
DEPT = 'ZZTRE2E部'
# ZZ 临时课程(课件软链借用 smart-task-intercom):绝不把真实课程切成 restricted、也不给它加临时题
KEY = 'zz-train-e2e-course'
assert KEY.startswith('zz-')
QPREFIX = 'ZZTRE-'

ap = argparse.ArgumentParser()
ap.add_argument('--port', type=int, default=5093)
ap.add_argument('--shots', default=os.path.join(tempfile.gettempdir(), 'pma-e2e-shots', 'train-shots'))
ap.add_argument('--headed', action='store_true')
args = ap.parse_args()
os.makedirs(args.shots, exist_ok=True)
BASE = f'http://127.0.0.1:{args.port}'

app = make_app()
from app import db  # noqa: E402

fails = []
UID = {}


def check(cond, msg):
    print(('OK   ' if cond else 'FAIL ') + msg, flush=True)
    if not cond:
        fails.append(msg)


# ───────────── 数据准备 / 还原 ─────────────

def seed():
    from app.models.user import User, Affiliation
    from app.models.course_exam import CourseLearningProgress
    from app.models.training import get_local_time
    roles = {HR: 'hr_manager'}
    for n in USERS:
        UID[n] = create_temp_user(app, n, PASSWORD, role=roles.get(n, 'sales_manager'))
    add_temp_bank(app, KEY, QPREFIX)
    with app.app_context():
        for n in (SUB, D1):
            db.session.get(User, UID[n]).department = DEPT
        db.session.get(User, UID[XREV]).company_name = XCOMPANY
        db.session.add(Affiliation(owner_id=UID[SUB], viewer_id=UID[MGR]))
        now = get_local_time()
        # 下属有进度(临时账号的进度行,随账号硬删)
        db.session.add(CourseLearningProgress(user_id=UID[SUB], course_key=KEY, page_seconds={'1': 40, '2': 25},
                                              score=66, unlocked_at=now, passed_at=now, last_ping_at=now))
        # 审核人也有一点进度 → 进入成绩范围,用来验证「审核人」徽标
        db.session.add(CourseLearningProgress(user_id=UID[REV], course_key=KEY, page_seconds={'1': 5}, score=0))
        db.session.commit()


def cleanup_users():
    ok = True
    for n in USERS:
        ok = delete_temp_user(app, n) and ok
    return ok


def db_state():
    from app.models.course_exam import CourseEnrollment, CourseReviewer
    from app.services.course_exam import access as A
    with app.app_context():
        d = {'mode': A.course_mode(KEY),
             'enrolled': {e.user_id for e in CourseEnrollment.query.filter_by(course_key=KEY).all()},
             'reviewers': {r.user_id for r in CourseReviewer.query.filter_by(course_key=KEY).all()}}
        db.session.rollback()
        return d


def message_count(uid, mtype):
    from app.models.message import Message
    with app.app_context():
        n = Message.query.filter_by(recipient_id=uid, message_type=mtype).count()
        db.session.rollback()
        return n


def temp_question():
    from app.models.course_exam import CourseQuizQuestion
    with app.app_context():
        q = (CourseQuizQuestion.query.filter(CourseQuizQuestion.question.like(QPREFIX + 'single%'))
             .order_by(CourseQuizQuestion.id).first())
        d = {'id': q.id, 'question': q.question}
        db.session.rollback()
        return d


def question_text(qid):
    from app.models.course_exam import CourseQuizQuestion
    with app.app_context():
        t = db.session.get(CourseQuizQuestion, qid).question
        db.session.rollback()
        return t


# ───────────── 浏览器 ─────────────

def run_browser():
    from playwright.sync_api import sync_playwright
    errors = []

    def shot(page, name):
        p = os.path.join(args.shots, name + '.png')
        page.screenshot(path=p, full_page=True)
        print('     shot ' + p)

    def login(browser, username):
        ctx = browser.new_context(viewport={'width': 1440, 'height': 900}, locale='zh-CN')
        ctx.on('page', lambda p: (
            p.on('console', lambda m: m.type == 'error' and errors.append(f'console[{p.url}]: {m.text}')),
            p.on('pageerror', lambda e: errors.append(f'pageerror[{p.url}]: {e}'))))
        page = ctx.new_page()
        page.goto(BASE + '/auth/login')
        page.fill('#username', username)
        page.fill('#password', PASSWORD)
        page.click('button[type=submit]')
        page.wait_for_load_state('networkidle')
        check('/auth/login' not in page.url, f'{username} 登录成功')
        return page

    def pick(page, root, uid, name):
        """at_people_select:输入姓名过滤后点选。"""
        page.click(f'#{root} [data-ps-input]')
        page.fill(f'#{root} [data-ps-input]', name)
        page.wait_for_selector(f'#{root} [data-ps-menu] [data-uid="{uid}"]', timeout=10000)
        page.click(f'#{root} [data-ps-menu] [data-uid="{uid}"]')
        page.keyboard.press('Escape')
        page.click('#trCTitle')            # 点空白处收起下拉

    card_sel = f'a.kb-card[href="/wiki/play/{KEY}"]'

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not args.headed)

        # ── 普通销售:拉入前(课程设为 restricted 之前先确认 open 时可见)──
        sp = login(browser, SALES)
        sp.goto(BASE + '/wiki/at'); sp.wait_for_load_state('networkidle')   # 等异步请求结束,避免跳转中断 fetch 报错
        check(sp.locator('#kbTrainingLink').count() == 0, '普通销售:知识库无「培训管理」按钮')
        check(sp.locator('#atSidebar a[href="/wiki/training"]').count() == 0, '普通销售:侧栏无「培训管理」')
        r = sp.goto(BASE + '/wiki/training')
        check(r.status == 403, f'普通销售访问培训管理 → 403(实际 {r.status})')

        # ── HR ──
        hp = login(browser, HR)
        hp.goto(BASE + '/wiki/at'); hp.wait_for_load_state('networkidle')   # 等异步请求结束,避免跳转中断 fetch 报错
        check(hp.locator('#kbTrainingLink').count() == 1, 'HR:知识库有「培训管理」按钮')
        check(hp.locator('#atSidebar a[href="/wiki/training"]').count() == 1, 'HR:侧栏有「培训管理」')
        hp.goto(BASE + '/wiki/training')
        hp.wait_for_selector('#trMatrix thead th.tr-ch', timeout=20000)
        n_cols = hp.locator('#trMatrix thead th.tr-ch').count()
        check(n_cols >= 1, f'总览矩阵渲染({n_cols} 门课)')
        check(hp.locator(f'#trMatrix [data-uid="{UID[SUB]}"]').count() >= 1, '总览含有进度的临时下属')
        hp.select_option('#trDeptFilter', DEPT)
        rows = hp.locator('#trMatrix tbody tr').count()
        check(rows == 1, f'总览按部门筛选 → 1 行(实际 {rows})')
        hp.fill('#trNameFilter', 'zz_no_such_name')
        check(hp.locator('#trMatrix tbody .tr-empty').count() == 1, '姓名搜索无匹配 → 空态')
        hp.fill('#trNameFilter', '')
        hp.select_option('#trDeptFilter', '')
        shot(hp, '01-overview')
        hp.locator(f'#trMatrix [data-cell="{KEY}"][data-uid="{UID[SUB]}"]').click()
        hp.wait_for_selector('#trDrawer:not([hidden]) .tr-kv', timeout=10000)
        check('ZZ ' + SUB in hp.locator('#trDTitle').inner_text(), '总览点格子 → 明细抽屉')
        hp.click('#trDClose')

        # 选课 → 学员标签
        hp.click(f'#trSide [data-key="{KEY}"]')
        hp.wait_for_selector('[data-pane="students"]:not([hidden])')
        hp.wait_for_function("document.querySelector('input[name=trMode]:checked') !== null")
        check(hp.locator('input[name=trMode][value=open]').is_checked(), '默认开放模式 = 全员开放')
        hp.wait_for_function("document.getElementById('trEnrollCount').textContent !== ''")
        check('可选' in hp.locator('#trModeHint').inner_text() and not hp.locator('#trModeEmpty').is_visible(),
              '全员开放:说明为「可选…」,无空名单警示')
        hp.check('input[name=trMode][value=restricted]')
        check(hp.locator('#trModeConfirm').is_visible(), '切「仅指定学员」出现页面内确认条')
        check('只有下方名单' in hp.locator('#trModeHint').inner_text() and hp.locator('#trModeEmpty').is_visible(),
              '待确认切换时:说明改为受限文案 + 名单为空红色警示')
        hp.click('#trModeNo')
        check(hp.locator('input[name=trMode][value=open]').is_checked() and db_state()['mode'] == 'open',
              '确认条点取消 → 回到全员开放、未保存')
        hp.check('input[name=trMode][value=restricted]')
        hp.check('input[name=trMode][value=open]')
        check(not hp.locator('#trModeConfirm').is_visible() and db_state()['mode'] == 'open',
              '确认条出现后改选「全员开放」→ 确认条收起、未保存')
        check('可选' in hp.locator('#trModeHint').inner_text() and not hp.locator('#trModeEmpty').is_visible(),
              '改回全员开放:说明恢复「可选…」')
        hp.check('input[name=trMode][value=restricted]')
        hp.click('#trModeYes')
        hp.wait_for_function("document.querySelector('#trSide [data-key=\"%s\"] .tr-chip-restricted') !== null" % KEY)
        check(db_state()['mode'] == 'restricted', '确认后保存为 restricted')
        check('只有下方名单' in hp.locator('#trModeHint').inner_text() and hp.locator('#trModeEmpty').is_visible(),
              '保存为受限且名单为空:红色警示可见')
        shot(hp, '02-students-restricted')

        # 普通销售:拉入前看不到
        sp.goto(BASE + '/wiki/at'); sp.wait_for_load_state('networkidle')   # 等异步请求结束,避免跳转中断 fetch 报错
        check(sp.locator(card_sel).count() == 0, '普通销售(未拉入):知识库无该课卡片')
        r = sp.goto(BASE + f'/wiki/play/{KEY}')
        check(r.status == 404, f'普通销售(未拉入):播放页 404(实际 {r.status})')

        # 按人添加
        pick(hp, 'trEnrollSel', UID[SALES], 'ZZ ' + SALES)
        hp.click('#trEnrollBtn')
        hp.wait_for_selector(f'#trEnrollTable tr[data-uid="{UID[SALES]}"]', timeout=10000)
        check(UID[SALES] in db_state()['enrolled'], '按人添加 → 数据库已拉入')
        hp.wait_for_function("document.getElementById('trModeEmpty').hidden === true", timeout=10000)
        check(not hp.locator('#trModeEmpty').is_visible(), '名单非空后:空名单警示消失')

        # 按部门添加(本公司 temp 部门)
        opt = hp.locator('#trDeptSel option', has_text=DEPT)
        check(opt.count() == 1 and '（2 人）' in opt.inner_text(), f'部门下拉显示「部门（人数）」: {opt.inner_text() if opt.count() else None}')
        hp.select_option('#trDeptSel', opt.get_attribute('value'))
        hp.click('#trDeptBtn')
        check(hp.locator('#trDeptConfirm').is_visible() and DEPT in hp.locator('#trDeptConfirmText').inner_text(),
              '按部门拉入:确认条显示部门与人数')
        hp.click('#trDeptYes')
        hp.wait_for_selector(f'#trEnrollTable tr[data-uid="{UID[D1]}"]', timeout=10000)
        st = db_state()['enrolled']
        check(UID[SUB] in st and UID[D1] in st, '按部门添加 → 部门两人已拉入')
        check(DEPT in hp.locator(f'#trEnrollTable tr[data-uid="{UID[D1]}"]').inner_text(), '来源列显示部门名')
        shot(hp, '03-students-enrolled')

        # 行内确认移除
        hp.click(f'#trEnrollTable tr[data-uid="{UID[D1]}"] [data-rm]')
        hp.click(f'#trEnrollTable tr[data-uid="{UID[D1]}"] [data-rm-yes]')
        hp.wait_for_selector(f'#trEnrollTable tr[data-uid="{UID[D1]}"]', state='detached', timeout=10000)
        check(UID[D1] not in db_state()['enrolled'], '行内确认移除 → 数据库已移除')

        # 审核人
        hp.click('#trTabs [data-tab="reviewers"]')
        hp.wait_for_selector('[data-pane="reviewers"]:not([hidden])')
        check(hp.locator('#trRevBankWrap').is_visible(), '审核人标签显示题库链接')
        pick(hp, 'trRevSel', UID[REV], 'ZZ ' + REV)
        hp.click('#trRevSave')
        hp.wait_for_function('() => !document.getElementById("trRevSave").disabled')
        hp.wait_for_timeout(500)
        check(db_state()['reviewers'] == {UID[REV]}, '保存审核人 → 数据库')
        check(message_count(UID[REV], 'course_reviewer') == 1, '审核人收到站内通知')
        # I1:跨公司人员可选(下拉按「公司 · 部门」分组)→ 保存 → 重进标签仍显示 chip → 可移除
        pick(hp, 'trRevSel', UID[XREV], 'ZZ ' + XREV)
        hp.click('#trRevSave')
        hp.wait_for_function('() => !document.getElementById("trRevSave").disabled')
        hp.wait_for_timeout(400)
        check(db_state()['reviewers'] == {UID[REV], UID[XREV]}, '跨公司审核人可选并保存')
        hp.click('#trTabs [data-tab="scores"]')
        hp.click('#trTabs [data-tab="reviewers"]')
        try:
            hp.wait_for_selector(f'#trRevSel [data-chip="{UID[XREV]}"]', timeout=10000)
            chip_ok = True
        except Exception:
            chip_ok = False
        check(chip_ok, '重进审核人标签:跨公司审核人显示为 chip')
        hp.click(f'#trRevSel [data-chip="{UID[XREV]}"] [data-rm]')
        hp.click('#trRevSave')
        hp.wait_for_function('() => !document.getElementById("trRevSave").disabled')
        hp.wait_for_timeout(400)
        check(db_state()['reviewers'] == {UID[REV]}, '跨公司审核人 chip 可移除并保存')
        hp.click('#trTabs [data-tab="students"]')
        hp.wait_for_selector('[data-pane="students"]:not([hidden])')
        hp.click('#trEnrollSel [data-ps-input]')
        hp.fill('#trEnrollSel [data-ps-input]', 'ZZ ' + XREV)
        try:
            hp.wait_for_selector(f'#trEnrollSel [data-ps-menu] [data-uid="{UID[XREV]}"]', timeout=10000)
            x_ok = True
        except Exception:
            x_ok = False
        check(x_ok and hp.locator('#trEnrollSel [data-ps-menu] .at-ps-grp', has_text=XCOMPANY).count() == 1,
              '学员选择器:跨公司人员可见,分组显示公司名')
        hp.fill('#trEnrollSel [data-ps-input]', '')
        hp.click('#trCTitle')
        hp.click('#trTabs [data-tab="reviewers"]')
        shot(hp, '04-reviewers')

        # 成绩 + 明细
        hp.click('#trTabs [data-tab="scores"]')
        hp.wait_for_selector(f'#trScoreTable tr[data-uid="{UID[SUB]}"]', timeout=10000)
        check('审核人' in hp.locator(f'#trScoreTable tr[data-uid="{UID[REV]}"]').inner_text(), '成绩表:审核人行带「审核人」徽标')
        check('审核人' not in hp.locator(f'#trScoreTable tr[data-uid="{UID[SUB]}"]').inner_text(), '成绩表:非审核人无徽标')
        row_txt = hp.locator(f'#trScoreTable tr[data-uid="{UID[SUB]}"]').inner_text()
        check('66' in row_txt, f'成绩表显示下属分数 66')
        hp.select_option('#trScoreSort', 'activity')
        hp.click(f'#trScoreTable tr[data-uid="{UID[SUB]}"]')
        hp.wait_for_selector('#trDrawer:not([hidden]) .tr-pg', timeout=10000)
        check(hp.locator('#trDBody .tr-pg').count() >= 2, '明细抽屉:逐页阅读条')
        shot(hp, '05-scores-drawer')
        hp.click('#trDClose')
        hp.click('#trSide [data-key=""]')
        # 旧矩阵 DOM 还在(隐藏),等重新拉取渲染出角标
        try:
            hp.wait_for_selector(f'#trMatrix [data-cell="{KEY}"][data-uid="{UID[REV]}"] sup', timeout=10000)
            ok = True
        except Exception:
            ok = False
        check(ok, '总览格子:审核人带「审」角标')
        check(hp.locator(f'#trMatrix [data-cell="{KEY}"][data-uid="{UID[SUB]}"] sup').count() == 0, '总览格子:非审核人无角标')

        # ── 普通销售:拉入后 ──
        sp.goto(BASE + '/wiki/at'); sp.wait_for_load_state('networkidle')   # 等异步请求结束,避免跳转中断 fetch 报错
        check(sp.locator(card_sel).count() == 1, '普通销售(已拉入):知识库出现该课卡片')
        sp.wait_for_selector(f'#kbMyTraining:not([hidden]) [data-my-course="{KEY}"]', state='attached', timeout=10000)
        check(sp.locator(f'[data-my-course="{KEY}"]').count() == 1, '「我的培训」出现该课')
        sp.click('#kbTabs [data-tab-key="courses"]')
        sp.wait_for_selector(f'[data-my-course="{KEY}"]', state='visible', timeout=10000)
        shot(sp, '06-sales-my-training')
        r = sp.goto(BASE + f'/wiki/play/{KEY}')
        check(r.status == 200, f'普通销售(已拉入):播放页 200(实际 {r.status})')
        check(message_count(UID[SALES], 'course_enrolled') == 1, '普通销售收到拉入通知')

        # ── 审核人 ──
        rp = login(browser, REV)
        rp.goto(BASE + f'/wiki/play/{KEY}')
        check(rp.locator('#cpBankLink').count() == 1, '审核人:播放页有「题库管理」按钮')
        rp.goto(BASE + f'/wiki/play/{KEY}/bank')
        rp.wait_for_selector('#bkBody tr[data-qid]', timeout=20000)
        check(rp.locator('#bkGenBtn').count() == 0, '审核人:题库页无「生成题库」')
        check(rp.locator('#bkReadInput').is_disabled(), '审核人:阅读时长只读')
        q = temp_question()
        rp.fill('#bkFText', q['question'])
        rp.click(f'button[data-act="edit"][data-id="{q["id"]}"]')
        rp.wait_for_selector('#bkEditModal', state='visible')
        rp.fill('#bkEQuestion', q['question'] + ' 已审')
        rp.click('#bkEditSave')
        rp.wait_for_selector('#bkEditModal', state='hidden', timeout=10000)
        check(question_text(q['id']) == q['question'] + ' 已审', '审核人编辑临时题 → 数据库已更新')
        shot(rp, '07-reviewer-bank')

        # ── 有下属的经理 ──
        mp = login(browser, MGR)
        mp.goto(BASE + '/wiki/at'); mp.wait_for_load_state('networkidle')   # 等异步请求结束,避免跳转中断 fetch 报错
        check(mp.locator('#kbTrainingLink').count() == 1, '有下属的经理:知识库有「培训管理」按钮')
        check(mp.locator('#atSidebar a[href="/wiki/training"]').count() == 1, '有下属的经理:侧栏有「培训管理」')
        mp.goto(BASE + '/wiki/training')
        mp.wait_for_selector('#trMatrix thead', timeout=20000)
        uids = set(int(x) for x in mp.eval_on_selector_all('#trMatrix [data-uid]', 'els => els.map(e => e.dataset.uid)'))
        check(uids == {UID[SUB]}, f'经理总览只含下属({uids})')
        mp.click(f'#trSide [data-key="{KEY}"]')
        mp.wait_for_selector(f'#trScoreTable tr[data-uid="{UID[SUB]}"]', timeout=10000)
        check(mp.locator('#trTabs [data-tab="students"]').count() == 0 and mp.locator('#trTabs [data-tab="reviewers"]').count() == 0,
              '经理:无学员 / 审核人标签')
        check(mp.locator('#trScoreTable tr[data-uid]').count() == 1, '经理成绩表只含下属')
        shot(mp, '08-manager-scores')
        browser.close()

    print('INFO 全部 console/page 错误:', len(errors))
    for e in errors:
        print('     ' + e[:300])
    own = [e for e in errors if 'Failed to load resource' not in e and ('/wiki/training' in e or '/wiki/at' in e)]
    check(not own, f'培训页 / 知识库无脚本 console error({len(own)})')
    check(not any(e.startswith('pageerror') for e in errors), '无未捕获 pageerror')


proc = None
SEED_KEYS = []
ASSETS = None
try:
    cleanup_users()
    delete_temp_bank(app, QPREFIX)
    ASSETS = make_temp_course(app, KEY, 'ZZ 培训 E2E 课程')
    seed()
    SEED_KEYS = empty_seed_keys(app)
    proc = start_server(args.port, os.path.join(args.shots, 'server.log'), KEY, assets_dir=ASSETS)
    print('INFO 服务已启动', BASE)
    run_browser()
except Exception as e:          # 浏览器步骤异常(超时等)也算失败
    import traceback
    traceback.print_exc()
    check(False, f'浏览器步骤异常: {type(e).__name__}: {str(e)[:200]}')
finally:
    stop_server(proc)
    check(delete_seed_imports(app, SEED_KEYS), f'清理:自动导入的种子题已硬删({SEED_KEYS})')
    if ASSETS:
        check(drop_temp_course(app, KEY, ASSETS), '清理:临时课程及其培训 / 题库 / 进度行已删除')
    check(delete_temp_bank(app, QPREFIX), '清理:ZZTRE 临时题已硬删')
    check(cleanup_users(), '清理:临时账号已硬删')
    print('\n' + ('全部通过' if not fails else f'{len(fails)} 项失败:\n  - ' + '\n  - '.join(fails)))
sys.exit(1 if fails else 0)
