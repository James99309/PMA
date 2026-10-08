#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""培训管理(课程开放模式 / 指定学员 / 审核人 / 成绩)集成验证(pma_local)。

全部用 ZZ 前缀的临时数据,finally 里硬删,不碰真实课程与用户:
  - 临时课程:zztm-course(HTML,课件经临时目录软链借用主仓 smart-task-intercom)/ zztm-video / zztm-ppt
  - 临时账号:zztm_mgr(hr_manager)/ zztm_rev / zztm_stu / zztm_out / zztm_sup / zztm_d1~d3(部门 ZZTM部,d3 停用)
  - 临时题库:ZZTM- 前缀 34 题(健康题库,小源面板才会列出)
AI(wiki 问答 / 单题重出)全部打桩。
"""
import os, sys, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _report_flow_testkit import make_app, get_project_root
sys.path.insert(0, os.path.join(get_project_root(), 'tests'))
import _pma_testkit as TK

KEY, VKEY, PKEY = 'zztm-course', 'zztm-video', 'zztm-ppt'
KEYS = [KEY, VKEY, PKEY]
PREFIX = 'ZZTM-'
DEPT = 'ZZTM部'
SRC_KEY = 'smart-task-intercom'
NAMES = ['zztm_mgr', 'zztm_rev', 'zztm_stu', 'zztm_out', 'zztm_sup', 'zztm_d1', 'zztm_d2', 'zztm_d3']

app = make_app()

from flask import g
from flask.testing import FlaskClient


class FreshUserClient(FlaskClient):
    """外层持有 app_context 时清掉 g 上的登录缓存,防止身份串到下一个请求。"""
    def open(self, *args, **kwargs):
        g.pop('_login_user', None)
        g.pop('_cb_review_bank', None)
        return super().open(*args, **kwargs)


app.test_client_class = FreshUserClient
app.config['WTF_CSRF_ENABLED'] = False

fails = []


def check(cond, msg):
    print(('OK  ' if cond else 'FAIL') + ' ' + msg)
    if not cond:
        fails.append(msg)


tmp_assets = tempfile.mkdtemp(prefix='zztm-assets-')

with app.app_context():
    from app import db
    from app.models.user import User, Affiliation
    from app.models.course import InteractiveCourse
    from app.models.message import Message
    from app.models.course_exam import (CourseAccess, CourseEnrollment, CourseReviewer,
                                        CourseLearningProgress, CourseQuizQuestion)
    from app.models.training import TrainingQuizAttempt, get_local_time
    from app.models.video_watch import VideoWatchState
    from app.services.course_exam import access as A, service as S, generator
    import app.views.knowledge_wiki as KW
    import app.views.learning as LV

    # 种子题库导入另有脚本验证,这里关掉
    S.SEED_DIR = os.path.join(get_project_root(), 'zz-no-seed-dir')
    S.reset_seed_memo()

    main_assets = os.path.normpath(os.path.join(get_project_root(), '..', '..', 'app', 'course_assets'))
    src_html = os.path.join(main_assets, SRC_KEY + '.html')
    assert os.path.isfile(src_html), '主仓课件不存在: ' + src_html
    os.symlink(src_html, os.path.join(tmp_assets, KEY + '.html'))
    if os.path.isdir(os.path.join(main_assets, SRC_KEY + '.thumbs')):
        os.symlink(os.path.join(main_assets, SRC_KEY + '.thumbs'), os.path.join(tmp_assets, KEY + '.thumbs'))
    KW.COURSE_ASSETS_DIR = tmp_assets
    KW._COURSE_PAGES_CACHE.pop(KEY, None)
    has_thumbs = os.path.isfile(os.path.join(tmp_assets, KEY + '.thumbs', '1.png'))

    assert not InteractiveCourse.query.filter(InteractiveCourse.key.in_(KEYS)).count(), '残留 zztm 课程,先清理'
    assert not User.query.filter(User.username.in_(NAMES)).count(), '残留 zztm 账号,先清理'

    uid = {}
    orig_query, orig_regen, orig_client = KW.querier.query_wiki, generator.regenerate_one, LV._regen_client
    try:
        # ---------- 准备 ----------
        roles = {'zztm_mgr': 'hr_manager'}
        for n in NAMES:
            uid[n] = TK.create_temp_user(app, n, 'Zz!' + n, role=roles.get(n, 'sales_manager'))
        for n in ('zztm_d1', 'zztm_d2', 'zztm_d3'):
            db.session.get(User, uid[n]).department = DEPT
        db.session.get(User, uid['zztm_d3'])._is_active = False
        db.session.add(Affiliation(owner_id=uid['zztm_stu'], viewer_id=uid['zztm_sup']))
        n_pages = len(KW._get_course_pages(KEY, KW._course_html_path(KEY)))
        db.session.add(InteractiveCourse(key=KEY, title='ZZTM 培训课', media_type='html', topic='ZZTM主题',
                                         page_count=n_pages, has_thumbs=has_thumbs, cover_page=1))
        db.session.add(InteractiveCourse(key=VKEY, title='ZZTM 视频课', media_type='video',
                                         media_url='zz/none.mp4'))
        db.session.add(InteractiveCourse(key=PKEY, title='ZZTM PPT 课', media_type='ppt',
                                         media_url='zz/none.pdf'))
        db.session.commit()
        TK.add_temp_bank(app, KEY, PREFIX)
        U = {n: db.session.get(User, i) for n, i in uid.items()}
        company = U['zztm_stu'].company_name
        print('INFO 课件页数', n_pages, '| 缩略图', has_thumbs, '| 公司', company)

        def login(n):
            c = app.test_client()
            with c.session_transaction() as s:
                s['_user_id'] = str(uid[n])
                s['_fresh'] = True
                s['role'] = U[n].role
            return c

        C = {n: login(n) for n in NAMES}
        mc = C['zztm_mgr']
        base = f'/api/learning/{KEY}'

        # ---------- 默认 open:存量行为不变 ----------
        check(A.course_mode(KEY) == 'open', '无 course_access 行 = open')
        r = C['zztm_out'].get(f'/wiki/play/{KEY}')
        check(r.status_code == 200, f'open 课:未拉入者可播放(实际 {r.status_code})')

        # ---------- 非管理员不能调管理接口 ----------
        for m, u, body in [('get', '/api/learning/admin/courses', None), ('post', base + '/access', {'mode': 'restricted'}),
                           ('get', base + '/enrollments', None), ('post', base + '/enrollments', {'user_ids': [uid['zztm_out']]}),
                           ('delete', f"{base}/enrollments/{uid['zztm_stu']}", None),
                           ('get', '/api/learning/departments', None), ('get', '/api/learning/users', None),
                           ('get', base + '/reviewers', None), ('put', base + '/reviewers', {'user_ids': [uid['zztm_out']]})]:
            for who in ('zztm_out', 'zztm_rev'):
                r = getattr(C[who], m)(u, json=body) if body is not None else getattr(C[who], m)(u)
                check(r.status_code == 403 and (r.get_json() or {}).get('error') == 'manager_only',
                      f'{who} {m.upper()} {u} → 403 manager_only(实际 {r.status_code})')
        check(A.course_mode(KEY) == 'open' and not CourseEnrollment.query.filter_by(course_key=KEY).count(),
              '无权请求未改动数据')

        # ---------- 模式切换 ----------
        r = mc.post(base + '/access', json={'mode': 'bogus'})
        check(r.status_code == 400, '非法 mode → 400')
        r = mc.post('/api/learning/zz-no-such/access', json={'mode': 'restricted'})
        check(r.status_code == 404, '不存在的课程 → 404')
        r = mc.post(base + '/access', json={'mode': 'restricted'})
        check(r.status_code == 200 and r.get_json()['data']['mode'] == 'restricted', '切换为 restricted')
        r = mc.post(f'/api/learning/{VKEY}/access', json={'mode': 'restricted'})
        r2 = mc.post(f'/api/learning/{PKEY}/access', json={'mode': 'restricted'})
        check(r.status_code == 200 and r2.status_code == 200, '视频 / PPT 课也可设为 restricted')

        # ---------- 个人拉入 ----------
        r = mc.post(base + '/enrollments', json={'user_ids': [uid['zztm_stu'], str(uid['zztm_stu']), uid['zztm_d3']]})
        j = r.get_json() or {}
        check(r.status_code == 200 and j['data']['added'] == 1, f"个人拉入:重复 id 合并 + 停用账号跳过 → 新增 1(实际 {j.get('data', {}).get('added')})")
        r = mc.post(base + '/enrollments', json={'user_ids': [uid['zztm_stu']]})
        check(r.get_json()['data']['added'] == 0, '已存在跳过 → 新增 0')
        r = mc.post(base + '/enrollments', json={'user_ids': ['x']})
        check(r.status_code == 400, '非法 user_ids → 400')
        msgs = Message.query.filter_by(recipient_id=uid['zztm_stu'], message_type='course_enrolled').all()
        check(len(msgs) == 1 and 'ZZTM 培训课' in msgs[0].title and msgs[0].related_object_type == 'course'
              and (msgs[0].extra_data or {}).get('url', '').endswith('/wiki/play/' + KEY),
              f'拉入通知:恰 1 条,标题含课名,链接到播放页({[m.title for m in msgs]})')
        check(not Message.query.filter_by(recipient_id=uid['zztm_d3'], message_type='course_enrolled').count(),
              '停用账号无通知')

        # ---------- 部门拉入 ----------
        r = mc.get('/api/learning/departments')
        deps = r.get_json()['data']['departments']
        mine = [d for d in deps if d['department'] == DEPT]
        check(len(mine) == 1 and mine[0]['count'] == 2, f'部门列表:{DEPT} 在职 2 人(停用不计){mine}')
        r = mc.get('/api/learning/users')
        us = r.get_json()['data']['users']
        check(any(u['id'] == uid['zztm_d1'] for u in us) and not any(u['id'] == uid['zztm_d3'] for u in us),
              '人员选择器:含在职、不含停用')
        r = mc.post(base + '/enrollments', json={'department': DEPT})
        check(r.get_json()['data']['added'] == 2, '按部门拉入 → 新增 2(只拉在职)')
        r = mc.post(base + '/enrollments', json={'department': DEPT})
        check(r.get_json()['data']['added'] == 0, '再次按部门拉入 → 0')
        r = mc.post(base + '/enrollments', json={'department': DEPT, 'company_name': 'ZZ 不存在的公司'})
        check(r.get_json()['data']['added'] == 0, '部门 + 不匹配的公司 → 0')
        e = CourseEnrollment.query.filter_by(course_key=KEY, user_id=uid['zztm_d1']).first()
        check(e is not None and e.source == 'department' and e.source_detail == DEPT, '部门拉入记来源')
        check(Message.query.filter(Message.recipient_id.in_([uid['zztm_d1'], uid['zztm_d2']]),
                                   Message.message_type == 'course_enrolled').count() == 2, '部门拉入各发 1 条通知')
        r = mc.get(base + '/enrollments')
        ens = r.get_json()['data']['enrollments']
        check({x['id'] for x in ens} == {uid['zztm_stu'], uid['zztm_d1'], uid['zztm_d2']}, '学员列表 = stu + d1 + d2')

        # ---------- 移除 ----------
        r = mc.delete(f"{base}/enrollments/{uid['zztm_d2']}")
        check(r.get_json()['data']['removed'] is True, '移除学员')
        r = mc.delete(f"{base}/enrollments/{uid['zztm_d2']}")
        check(r.get_json()['data']['removed'] is False, '重复移除 → False')

        # ---------- 审核人 ----------
        r = mc.put(base + '/reviewers', json={'user_ids': [uid['zztm_rev'], uid['zztm_out']]})
        j = r.get_json()['data']
        check(sorted(j['added']) == sorted([uid['zztm_rev'], uid['zztm_out']]), '审核人:新增 2')
        r = mc.put(base + '/reviewers', json={'user_ids': [uid['zztm_rev']]})
        j = r.get_json()['data']
        check(j['added'] == [] and j['removed'] == [uid['zztm_out']] and [x['id'] for x in j['reviewers']] == [uid['zztm_rev']],
              '审核人全量覆盖:移除 out、保留 rev、不重复通知')
        rm = Message.query.filter_by(recipient_id=uid['zztm_rev'], message_type='course_reviewer').all()
        check(len(rm) == 1 and (rm[0].extra_data or {}).get('url', '').endswith(f'/wiki/play/{KEY}/bank'),
              '审核人通知 1 条,链接到题库页')

        # 评审 #6:并发下审核人已被别的请求插入 —— 不 500、不重复通知
        orig_rows = A._reviewer_rows
        try:
            A._reviewer_rows = lambda key: {}          # 模拟读到的是插入前的旧快照
            r = A.set_reviewers(KEY, [uid['zztm_rev']], uid['zztm_mgr'])
            check(r['added'] == [], f'并发重复插入审核人:on conflict 跳过({r})')
        finally:
            A._reviewer_rows = orig_rows
        check(Message.query.filter_by(recipient_id=uid['zztm_rev'], message_type='course_reviewer').count() == 1,
              '并发重复插入不重复通知')
        # 评审 #7:department 与 user_ids 同时给 → 400
        r = mc.post(base + '/enrollments', json={'department': DEPT, 'user_ids': [uid['zztm_out']]})
        check(r.status_code == 400 and r.get_json()['error'] == 'bad_params', 'department + user_ids 同时给 → 400')

        # ---------- 管理总览 ----------
        r = mc.get('/api/learning/admin/courses')
        row = next((c for c in r.get_json()['data']['courses'] if c['key'] == KEY), None)
        check(row and row['mode'] == 'restricted' and row['enrolled_count'] == 2
              and [x['id'] for x in row['reviewers']] == [uid['zztm_rev']] and row['bank']['ok'], f'admin/courses 行 {row and {k: row[k] for k in ("mode", "enrolled_count")}}')
        vrow = next((c for c in r.get_json()['data']['courses'] if c['key'] == VKEY), None)
        check(vrow and vrow['media_type'] == 'video' and vrow['bank'] is None, 'admin/courses 视频课无题库健康')

        # ---------- 可见性矩阵(restricted)----------
        db.session.expire_all()
        A_VIS = {'zztm_mgr': True, 'zztm_rev': True, 'zztm_stu': True, 'zztm_out': False, 'zztm_d2': False}

        def matrix(expect, label):
            for who, vis in expect.items():
                c = C[who]
                routes = [('get', f'/wiki/play/{KEY}'), ('get', f'/wiki/play/{KEY}/asset'),
                          ('get', f'{base}/progress'), ('get', f'{base}/exam/current')]
                if has_thumbs:
                    routes.append(('get', f'/wiki/play/{KEY}/thumb/1'))
                for m, u in routes:
                    r = getattr(c, m)(u)
                    ok = (r.status_code != 404) if vis else (r.status_code == 404)
                    check(ok, f'[{label}] {who} {u} → {r.status_code}(应{"可见" if vis else "404"})')
                r = c.post(f'{base}/read-ping', json={'page': 1, 'seconds': 0})
                check((r.status_code == 200) if vis else (r.status_code == 404), f'[{label}] {who} read-ping → {r.status_code}')
                r = c.get(f'/wiki/play/{KEY}/pkg/index.html')
                check(r.status_code == 404, f'[{label}] {who} pkg(单文件课恒 404)')
                vv = V_VIS[who]           # 视频课单独的可见性(审核人身份只针对 zztm-course)
                r = c.get(f'/wiki/video/{VKEY}')
                check((r.status_code == 200) if vv else (r.status_code == 404), f'[{label}] {who} 视频播放页 → {r.status_code}')
                r = c.post(f'/wiki/video/{VKEY}/progress', json={'position': 1, 'duration': 100})
                check((r.status_code == 200) if vv else (r.status_code == 404), f'[{label}] {who} video progress → {r.status_code}')
                if not vv:   # 可见时会去连 NAS WebDAV,只验不可见 → 404
                    for u in (f'/wiki/play/{VKEY}/video', f'/wiki/play/{PKEY}/download'):
                        r = c.get(u)
                        check(r.status_code == 404, f'[{label}] {who} {u} → 404')
                html = c.get('/wiki/at').get_data(as_text=True)
                listed = f"/wiki/play/{KEY}" in html
                check(listed == vis, f'[{label}] {who} 知识库列表{"含" if vis else "不含"}本课')
                buddy = c.get('/api/learning/buddy').get_json()['data']['courses']
                check(any(x['key'] == KEY for x in buddy) == vis, f'[{label}] {who} 小源面板{"含" if vis else "不含"}本课')

        # 视频课:只拉入 stu;审核人身份只针对 zztm-course,对视频课按普通人处理
        A.enroll_users(VKEY, [uid['zztm_stu']], uid['zztm_mgr'])
        V_VIS = {'zztm_mgr': True, 'zztm_rev': False, 'zztm_stu': True, 'zztm_out': False, 'zztm_d2': False}
        matrix(A_VIS, 'restricted')

        # 卡片 / 播放页上的「题库管理」入口:审核人可见,学员不可见
        html = C['zztm_rev'].get('/wiki/at').get_data(as_text=True)
        check(f'data-bank-link="{KEY}"' in html, '审核人:知识库卡片显示题库管理入口')
        check(f'id="cpBankLink"' in C['zztm_rev'].get(f'/wiki/play/{KEY}').get_data(as_text=True), '审核人:播放页显示题库管理按钮')
        check('data-bank-link=' not in C['zztm_stu'].get('/wiki/at').get_data(as_text=True), '学员:无卡片入口')
        check('id="cpBankLink"' not in C['zztm_stu'].get(f'/wiki/play/{KEY}').get_data(as_text=True), '学员:播放页无题库按钮')

        # ---------- 问答:course scope 与 deck_pages ----------
        seen = {}

        def fake_query(question, top_k=5, topic=None, current_user_id=None):
            seen['topic'] = topic
            return {'answer': 'zz', 'cited_articles': [{'slug': KEY + '-deck'}]}
        KW.querier.query_wiki = fake_query
        q = '智能任务对讲机 有什么功能'
        r = C['zztm_stu'].post('/api/wiki/query', json={'question': q, 'course_key': KEY})
        dp = r.get_json()['data']['deck_pages']
        check(seen['topic'] == 'ZZTM主题' and all(x['key'] == KEY for x in dp), f'学员:本课范围按课程 topic 收窄({len(dp)} 页)')
        r = C['zztm_out'].post('/api/wiki/query', json={'question': q, 'course_key': KEY})
        check(seen['topic'] is None and not r.get_json()['data']['deck_pages'], '未授权:不按受限课 topic 收窄、无缩略图')
        r = C['zztm_out'].post('/api/wiki/query', json={'question': q})
        check(not r.get_json()['data']['deck_pages'], '未授权:全库问答引用受限课件不出缩略图')
        r = C['zztm_stu'].post('/api/wiki/query', json={'question': q})
        check(any(x['key'] == KEY for x in r.get_json()['data']['deck_pages']) or n_pages == 0,
              '学员:全库问答引用本课出缩略图')

        # ---------- 审核人题库权限 ----------
        qid = db.session.query(CourseQuizQuestion.id).filter(CourseQuizQuestion.question.like(PREFIX + '%')).order_by(CourseQuizQuestion.id).first()[0]
        rc = C['zztm_rev']
        r = rc.get(f'/wiki/play/{KEY}/bank')
        h = r.get_data(as_text=True)
        check(r.status_code == 200 and 'id="bkGenBtn"' not in h and 'id="bkReadSave" hidden' in h,
              '审核人题库页 200,无「生成题库」、阅读时长只读')
        h = mc.get(f'/wiki/play/{KEY}/bank').get_data(as_text=True)
        check('id="bkGenBtn"' in h and 'id="bkReadSave" hidden' not in h, '管理员题库页有生成与保存')
        check(rc.get(base + '/bank').status_code == 200, '审核人 GET 题库 200')
        r = rc.put(f'{base}/bank/{qid}', json={'difficulty': 2})
        check(r.status_code == 200 and r.get_json()['data']['difficulty'] == 2, '审核人改难度 200')
        r = rc.put(f'{base}/bank/{qid}', json={'status': 'disabled'})
        check(r.status_code == 200, '审核人停用 200')
        r = rc.put(f'{base}/bank/{qid}', json={'status': 'review', 'question': PREFIX + 'edited'})
        check(r.status_code == 200 and r.get_json()['data']['origin'] == 'edited', '审核人编辑题干 200')
        r = rc.post(base + '/bank/approve-all')
        check(r.status_code == 200 and r.get_json()['data']['approved'] >= 1, '审核人全部通过待审 200')

        class DummyClient:
            def close(self):
                pass
        LV._regen_client = lambda: DummyClient()
        generator.regenerate_one = lambda pages, src, client=None, existing_questions=None: {
            'qtype': 'single', 'difficulty': 3, 'question': PREFIX + 'regen', 'options': ['a', 'b', 'c', 'd'],
            'answer': 0, 'explain': 'x', 'source_page': 1}
        r = rc.post(f'{base}/bank/{qid}/regenerate')
        check(r.status_code == 200 and r.get_json()['data']['question'] == PREFIX + 'regen', '审核人单题重出 200')
        r = rc.post(base + '/bank/generate', json={})
        check(r.status_code == 403 and r.get_json()['error'] == 'forbidden', '审核人整套生成 → 403')
        r = rc.post(base + '/settings', json={'min_read_seconds': 5})
        check(r.status_code == 403, '审核人改阅读时长 → 403')
        for who, code in (('zztm_stu', 403), ('zztm_out', 404)):
            r = C[who].get(base + '/bank')
            check(r.status_code == code, f'{who} 题库 API → {code}(实际 {r.status_code})')
            r = C[who].get(f'/wiki/play/{KEY}/bank')
            check(r.status_code == code, f'{who} 题库页 → {code}(实际 {r.status_code})')
        # 审核人只管自己那门课:对视频课 / 别的课无题库权限
        check(not A.can_review_bank(U['zztm_rev'], 'evertac-pnr2100'), '审核人对其他课无题库权限')

        # ---------- 成绩 ----------
        now = get_local_time()
        db.session.expire_all()

        def upsert_progress(n, **kw):
            p = CourseLearningProgress.query.filter_by(user_id=uid[n], course_key=KEY).first()
            if p is None:
                p = CourseLearningProgress(user_id=uid[n], course_key=KEY, page_seconds={}, score=0)
                db.session.add(p)
            for k, v in kw.items():
                setattr(p, k, v)
            return p
        # 上面可见性矩阵里的 read-ping 已给 mgr / rev / stu 建了进度行
        upsert_progress('zztm_stu', page_seconds={'1': 30}, score=64, unlocked_at=now, passed_at=now, last_ping_at=now)
        cur = CourseQuizQuestion.query.filter(CourseQuizQuestion.course_key == KEY,
                                              CourseQuizQuestion.question.like(PREFIX + 'single%')).order_by(CourseQuizQuestion.id).limit(2).all()
        for qq, n_wrong in ((cur[0], 3), (cur[1], 1)):
            for i in range(n_wrong):
                db.session.add(TrainingQuizAttempt(user_id=uid['zztm_stu'], course_slug=KEY, module_slug='bank', chapter=1,
                                                   question_id=str(qq.id), question_text=qq.question, is_correct=False,
                                                   attempted_at=now))
        db.session.add(TrainingQuizAttempt(user_id=uid['zztm_stu'], course_slug=KEY, module_slug='bank', chapter=1,
                                           question_id=str(cur[1].id), question_text='旧题干', is_correct=False, attempted_at=now))
        db.session.add(TrainingQuizAttempt(user_id=uid['zztm_stu'], course_slug=KEY, module_slug='bank', chapter=1,
                                           question_id=str(cur[1].id), question_text=cur[1].question, is_correct=True, attempted_at=now))
        # 未拉入但有进度的人(审核人 rev / 管理员 mgr,来自 read-ping)→ 管理员成绩表也应列出
        upsert_progress('zztm_rev', page_seconds={'1': 5})
        db.session.commit()

        r = mc.get(base + '/report')
        rows = r.get_json()['data']['rows']
        ids = {x['user']['id'] for x in rows}
        check(ids == {uid['zztm_stu'], uid['zztm_d1'], uid['zztm_rev'], uid['zztm_mgr']},
              f'管理员成绩表 = 已拉入(stu,d1) ∪ 有进度(stu,rev,mgr)({len(rows)} 行)')
        srow = next(x for x in rows if x['user']['id'] == uid['zztm_stu'])
        check(srow['enrolled'] and srow['score'] == 64 and srow['unlocked'] and srow['read_percent'] == 100
              and srow['attempts'] == 6 and srow['correct'] == 1 and srow['passed_at'], f'学员行数据 {srow}')
        r = C['zztm_sup'].get(base + '/report')
        rows = r.get_json()['data']['rows']
        check(r.status_code == 200 and [x['user']['id'] for x in rows] == [uid['zztm_stu']], '直属上级只看下属')
        r = C['zztm_out'].get(base + '/report')
        check(r.status_code == 403, '普通人看成绩 → 403')
        r = C['zztm_sup'].get('/api/learning/report/overview')
        d = r.get_json()['data']
        check(r.status_code == 200 and list(d['cells']) == [str(uid['zztm_stu'])] and any(c['key'] == KEY for c in d['courses']),
              '上级总览:仅下属')
        r = mc.get('/api/learning/report/overview')
        d = r.get_json()['data']
        check(d['cells'][str(uid['zztm_stu'])][KEY]['score'] == 64 and d['cells'][str(uid['zztm_stu'])][VKEY]['enrolled'],
              '管理员总览:含学员 html + 视频课格子')
        check(next(c for c in d['courses'] if c['key'] == KEY)['summary']['passed'] == 1, '总览汇总:及格 1')
        check(C['zztm_out'].get('/api/learning/report/overview').status_code == 403, '普通人总览 → 403')

        r = C['zztm_sup'].get(f"{base}/report/{uid['zztm_stu']}")
        d = r.get_json()['data']
        rw = d['repeated_wrong']
        check(r.status_code == 200 and [x['question_id'] for x in rw] == [cur[0].id] and rw[0]['wrong'] == 3,
              f'反复错题:只认当前题干、错≥2({[(x["question_id"], x["wrong"]) for x in rw]})')
        check(d['read']['total_seconds'] == 30 and d['exam']['attempts'] == 6, '明细:阅读秒数 + 作答总数')
        check(C['zztm_stu'].get(f"{base}/report/{uid['zztm_stu']}").status_code == 200, '本人看自己明细 200')
        # 评审 #1:未拉入者看自己在受限课上的明细 → 404,且不泄露课名
        r = C['zztm_out'].get(f"{base}/report/{uid['zztm_out']}")
        check(r.status_code == 404 and 'ZZTM 培训课' not in r.get_data(as_text=True), f'未拉入者看自己受限课明细 → 404 不含课名({r.status_code})')
        # 评审 #2:无权者探测不存在的课程 key → 403(先判权限,不暴露存在性)
        check(C['zztm_out'].get('/api/learning/zz-no-such/report').status_code == 403, '无权者探测不存在课程成绩 → 403')
        check(C['zztm_out'].get(f"/api/learning/zz-no-such/report/{uid['zztm_stu']}").status_code == 403,
              '无权者探测不存在课程明细 → 403')
        check(C['zztm_out'].get(f"{base}/report").status_code == 403, '无权者看存在课程成绩 → 403(与不存在同码)')
        check(mc.get('/api/learning/zz-no-such/report').status_code == 404, '管理员看不存在课程 → 404')
        # 评审 #8:审核人标记
        rows = mc.get(base + '/report').get_json()['data']['rows']
        flags = {x['user']['id']: x['is_reviewer'] for x in rows}
        check(flags.get(uid['zztm_rev']) is True and flags.get(uid['zztm_stu']) is False, f'成绩行 is_reviewer 标记')
        d = mc.get('/api/learning/report/overview').get_json()['data']
        check(d['cells'][str(uid['zztm_rev'])][KEY]['is_reviewer'] is True
              and d['cells'][str(uid['zztm_stu'])][KEY]['is_reviewer'] is False, '总览格子 is_reviewer 标记')
        check(C['zztm_sup'].get(f"{base}/report/{uid['zztm_out']}").status_code == 403, '上级看非下属 → 403')
        check(C['zztm_out'].get(f"{base}/report/{uid['zztm_stu']}").status_code == 403, '普通人看他人 → 403')

        # ---------- 我的培训 ----------
        mine = C['zztm_stu'].get('/api/learning/my').get_json()['data']['courses']
        check({x['key'] for x in mine} == {KEY, VKEY} and next(x for x in mine if x['key'] == KEY)['score'] == 64,
              f'学员我的培训 = 已拉入的 {[x["key"] for x in mine]}')
        mine = C['zztm_out'].get('/api/learning/my').get_json()['data']['courses']
        check(not any(x['key'] in KEYS for x in mine), '未拉入者我的培训不含受限课')

        # ---------- 培训管理页门禁(批次 B)----------
        r = mc.get('/wiki/training')
        check(r.status_code == 200 and 'data-mode="full"' in r.get_data(as_text=True), '培训管理页:管理员 full')
        r = C['zztm_sup'].get('/wiki/training')
        h = r.get_data(as_text=True)
        check(r.status_code == 200 and 'data-mode="scores"' in h and 'data-tab="students"' not in h, '培训管理页:有下属的人只看成绩')
        check(C['zztm_out'].get('/wiki/training').status_code == 403, '培训管理页:普通人 403')
        check(A.training_page_mode(U['zztm_rev']) is None, '审核人身份本身不给培训管理页')
        j = mc.get('/api/learning/users').get_json()
        check(isinstance(j.get('users'), list) and j['users'] == j['data']['users'], '/api/learning/users 顶层 users 兼容 at_people_select')
        check('/wiki/training' in C['zztm_sup'].get('/wiki/at').get_data(as_text=True)
              and '/wiki/training' not in C['zztm_out'].get('/wiki/at').get_data(as_text=True), '入口:上级可见、普通人不可见')

        # ---------- 切回 open ----------
        r = mc.post(base + '/access', json={'mode': 'open'})
        db.session.expire_all()
        check(r.status_code == 200 and A.course_mode(KEY) == 'open', '切回 open')
        r = C['zztm_out'].get(f'/wiki/play/{KEY}')
        check(r.status_code == 200, 'open:未拉入者可播放')
        check(C['zztm_out'].get(base + '/bank').status_code == 403, 'open:非审核人题库 → 403(非 404)')
        upsert_progress('zztm_out', page_seconds={'1': 3})
        db.session.commit()
        mine = C['zztm_out'].get('/api/learning/my').get_json()['data']['courses']
        check(any(x['key'] == KEY and not x['enrolled'] for x in mine), 'open 课有进度 → 进我的培训(enrolled=False)')
        check(A.visible_course_keys(U['zztm_out'], [KEY, VKEY, PKEY]) == [KEY], f'批量可见性:open 课可见,受限课不可见')
    finally:
        KW.querier.query_wiki, generator.regenerate_one, LV._regen_client = orig_query, orig_regen, orig_client
        db.session.rollback()
        CourseAccess.query.filter(CourseAccess.course_key.in_(KEYS)).delete(synchronize_session=False)
        CourseEnrollment.query.filter(CourseEnrollment.course_key.in_(KEYS)).delete(synchronize_session=False)
        CourseReviewer.query.filter(CourseReviewer.course_key.in_(KEYS)).delete(synchronize_session=False)
        CourseLearningProgress.query.filter(CourseLearningProgress.course_key.in_(KEYS)).delete(synchronize_session=False)
        VideoWatchState.query.filter(VideoWatchState.course_key.in_(KEYS)).delete(synchronize_session=False)
        TrainingQuizAttempt.query.filter(TrainingQuizAttempt.course_slug.in_(KEYS)).delete(synchronize_session=False)
        InteractiveCourse.query.filter(InteractiveCourse.key.in_(KEYS)).delete(synchronize_session=False)
        db.session.commit()
        TK.delete_temp_bank(app, PREFIX)
        for n in NAMES:
            TK.delete_temp_user(app, n)
        KW._COURSE_PAGES_CACHE.pop(KEY, None)
        shutil.rmtree(tmp_assets, ignore_errors=True)
        left = (CourseAccess.query.filter(CourseAccess.course_key.in_(KEYS)).count()
                + CourseEnrollment.query.filter(CourseEnrollment.course_key.in_(KEYS)).count()
                + CourseReviewer.query.filter(CourseReviewer.course_key.in_(KEYS)).count()
                + InteractiveCourse.query.filter(InteractiveCourse.key.in_(KEYS)).count()
                + CourseQuizQuestion.query.filter(CourseQuizQuestion.question.like(PREFIX + '%')).count()
                + User.query.filter(User.username.in_(NAMES)).count())
        print('清理完成,残留行数:', left)

    print('\n' + ('全部通过' if not fails else f'{len(fails)} 项失败:\n  - ' + '\n  - '.join(fails)))
    sys.exit(1 if fails else 0)
