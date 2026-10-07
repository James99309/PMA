#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""题库管理 API(app/views/learning.py bank_*)集成验证(pma_local)。

Flask test_client + session 登录(管理员 / 普通销售各一,只读借用现有账号);
AI 相关(generator.start_generation / regenerate_one)全部打桩,不调真实 AI。
插入 ZZBANK- 题 + 这些题的作答留痕,finally 里硬删;course_exam_settings 还原。
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _report_flow_testkit import make_app, get_project_root

KEY = 'smart-task-intercom'
PREFIX = 'ZZBANK-'

app = make_app()

from flask import g
from flask.testing import FlaskClient


class FreshUserClient(FlaskClient):
    """外层持有 app_context 时清掉 g._login_user,防止上一个请求的身份串到下一个。"""
    def open(self, *args, **kwargs):
        g.pop('_login_user', None)
        return super().open(*args, **kwargs)


app.test_client_class = FreshUserClient
app.config['WTF_CSRF_ENABLED'] = False

with app.app_context():
    from app import db
    from app.models.user import User
    from app.models.course_exam import CourseQuizQuestion, CourseExamSetting
    from app.models.training import TrainingQuizAttempt, get_local_time
    from app.services.course_exam import generator, logic as L
    import app.views.knowledge_wiki as KW

    if not os.path.isfile(KW._course_html_path(KEY)):
        main_assets = os.path.normpath(os.path.join(get_project_root(), '..', '..', 'app', 'course_assets'))
        KW.COURSE_ASSETS_DIR = main_assets
        print('INFO 课件目录改指主仓:', main_assets)
    course, path = KW._find_course(KEY)
    assert course, '测试课程不存在'
    PAGES = KW._get_course_pages(KEY, path)
    assert PAGES, '测试课程没有页面'

    fails = []

    def check(cond, msg):
        print(('OK  ' if cond else 'FAIL') + ' ' + msg)
        if not cond:
            fails.append(msg)

    admin = User.query.filter(User._is_active == True, User.role == 'admin').order_by(User.id).first()
    sales = User.query.filter(User._is_active == True, User.role == 'sales_manager').order_by(User.id).first()
    assert admin and sales, '找不到测试账号'
    print('INFO 管理员', admin.id, admin.username, '| 销售', sales.id, sales.username)

    def login(u):
        c = app.test_client()
        with c.session_transaction() as s:
            s['_user_id'] = str(u.id)
            s['_fresh'] = True
            s['role'] = u.role
        return c

    mc, sc = login(admin), login(sales)
    base = f'/api/learning/{KEY}'

    pre_review = CourseQuizQuestion.query.filter_by(course_key=KEY, status='review').count()
    saved = db.session.get(CourseExamSetting, KEY)
    saved = None if saved is None else {'min_read_seconds': saved.min_read_seconds,
                                        'generating_since': saved.generating_since,
                                        'generating_by': saved.generating_by}

    def add_q(tag, qtype='single', difficulty=2, status='active', origin='ai', page=1):
        opts = None if qtype == 'judge' else ['A', 'B', 'C', 'D']
        ans = True if qtype == 'judge' else ([0, 1] if qtype == 'multi' else 0)
        q = CourseQuizQuestion(course_key=KEY, qtype=qtype, difficulty=difficulty, question=PREFIX + tag,
                               options=opts, answer=ans, explain='e', source_page=page, status=status,
                               origin=origin, review_note='复核存疑' if status == 'review' else None)
        db.session.add(q)
        db.session.flush()
        return q

    orig_start, orig_regen = generator.start_generation, generator.regenerate_one
    calls = {}
    try:
        q1 = add_q('Q1', difficulty=1)
        q2 = add_q('Q2', qtype='multi', difficulty=3, status='review')
        q3 = add_q('Q3', qtype='judge', difficulty=1, status='review')
        q4 = add_q('Q4', difficulty=2, status='disabled')
        db.session.commit()
        ids = [q1.id, q2.id, q3.id, q4.id]

        # 作答留痕:q1 由 12 人首答(3 对 9 错)→ 实测难(3);其中 1 人后来又答对(不应计入)
        uids = [u for (u,) in db.session.query(User.id).order_by(User.id).limit(12).all()]
        t0 = get_local_time()
        from datetime import timedelta
        for i, uid in enumerate(uids):
            db.session.add(TrainingQuizAttempt(user_id=uid, course_slug=KEY, module_slug='bank', chapter=1,
                                               question_id=str(q1.id), question_text='x', is_correct=i < 3,
                                               attempted_at=t0))
        db.session.add(TrainingQuizAttempt(user_id=uids[5], course_slug=KEY, module_slug='bank', chapter=1,
                                           question_id=str(q1.id), question_text='x', is_correct=True,
                                           attempted_at=t0 + timedelta(minutes=1)))
        db.session.commit()

        # ---- 权限 ----
        r = sc.get(f'/wiki/play/{KEY}/bank')
        check(r.status_code == 403, f'普通销售访问题库页 → 403(实际 {r.status_code})')
        for m, u, body in [('get', base + '/bank', None), ('post', base + '/bank/generate', {}),
                           ('put', f'{base}/bank/{q1.id}', {'status': 'disabled'}),
                           ('post', f'{base}/bank/{q1.id}/regenerate', None),
                           ('post', base + '/bank/approve-all', None),
                           ('post', base + '/settings', {'min_read_seconds': 5})]:
            r = getattr(sc, m)(u, json=body) if body is not None else getattr(sc, m)(u)
            j = r.get_json() or {}
            check(r.status_code == 403 and j.get('error') == 'forbidden', f'普通销售 {m.upper()} {u[len(base):]} → 403 JSON')
        db.session.expire_all()
        check(db.session.get(CourseQuizQuestion, q1.id).status == 'active', '无权请求未改动数据')

        r = mc.get(f'/wiki/play/{KEY}/bank')
        html = r.get_data(as_text=True)
        check(r.status_code == 200 and 'bkBody' in html and course['title'] in html, '管理员打开题库页 200')
        r = mc.get('/wiki/play/zz-no-such-course/bank')
        check(r.status_code == 404, f'不存在的课程 → 404(实际 {r.status_code})')
        r = mc.get('/wiki/at')
        check(f'data-bank-link="{KEY}"' in r.get_data(as_text=True), '知识库课程卡:管理员可见「题库管理」入口')
        r = sc.get('/wiki/at')
        check('data-bank-link=' not in r.get_data(as_text=True), '知识库课程卡:普通销售看不到入口')

        # ---- 列表 / 统计 / 健康 ----
        r = mc.get(base + '/bank')
        d = r.get_json()['data']
        mine = {q['id']: q for q in d['questions'] if q['id'] in ids}
        check(len(mine) == 4, '列表含全部状态的题(含停用)')
        s1 = mine[q1.id]['stats']
        check(s1['n_first'] == 12 and s1['correct_first'] == 3 and s1['empirical'] == 3 and not s1['suspicious'],
              f'实测:只计首次作答 {s1}')
        check(mine[q2.id]['stats'] == {'n_first': 0, 'correct_first': 0, 'empirical': None, 'suspicious': False},
              '无作答的题 stats 为空')
        active = [q for q in d['questions'] if q['status'] == 'active']
        exp = L.bank_health([{'qtype': q['qtype'], 'difficulty': q['difficulty']} for q in active])
        check(d['health']['max_score'] == exp['max_score'] and d['health']['total'] == exp['total']
              and d['health']['by_difficulty'] == {str(k): v for k, v in exp['by_difficulty'].items()},
              f'health 只算启用题 {d["health"]["max_score"]}')
        check(d['health']['ok'] is False, '健康检查:分值不足 → ok False')
        check(d['auto_read_seconds'] == L.required_read_seconds(PAGES) and d['pages'] == len(PAGES),
              '自动阅读时长 = 按讲解字数估算')
        check(d['generating'] is False, '未在生成')
        check('answer' in mine[q1.id] and 'explain' in mine[q1.id], '管理端含答案/解析')

        # generating 读库标记
        generator._ensure_setting(KEY).generating_since = get_local_time()
        db.session.commit()
        check(mc.get(base + '/bank').get_json()['data']['generating'] is True, '生成标记未过期 → generating True')
        db.session.get(CourseExamSetting, KEY).generating_since = None
        db.session.commit()

        # ---- 编辑 ----
        r = mc.put(f'{base}/bank/{q1.id}', json={'difficulty': 3})
        db.session.expire_all()
        q = db.session.get(CourseQuizQuestion, q1.id)
        check(r.status_code == 200 and q.difficulty == 3 and q.origin == 'ai', '改难度(采纳):不算改内容,origin 不变')
        r = mc.put(f'{base}/bank/{q1.id}', json={'question': PREFIX + 'Q1 改', 'options': ['x', 'y', 'z'],
                                                 'answer': 2, 'explain': ' 新解析 '})
        db.session.expire_all()
        q = db.session.get(CourseQuizQuestion, q1.id)
        check(r.status_code == 200 and q.options == ['x', 'y', 'z'] and q.answer == 2 and q.explain == '新解析'
              and q.origin == 'edited', '改题干/选项/答案 → origin=edited')
        r = mc.put(f'{base}/bank/{q1.id}', json={'qtype': 'judge', 'answer': False})
        db.session.expire_all()
        q = db.session.get(CourseQuizQuestion, q1.id)
        check(r.status_code == 200 and q.qtype == 'judge' and q.options is None and q.answer is False,
              '改成判断题:options 清空')
        r = mc.put(f'{base}/bank/{q1.id}', json={'qtype': 'multi', 'options': ['a', 'b', 'c'], 'answer': [0, 1, 2]})
        j = r.get_json()
        check(r.status_code == 400 and j['error'] == 'invalid_question' and j['message'], f'多选全选 → 400 ({j.get("message")})')
        r = mc.put(f'{base}/bank/{q1.id}', json={'question': '   '})
        check(r.status_code == 400 and r.get_json()['error'] == 'invalid_question', '空题干 → 400')
        r = mc.put(f'{base}/bank/{q1.id}', json={'status': 'deleted'})
        check(r.status_code == 400 and r.get_json()['error'] == 'bad_params', '非法状态 → 400')
        r = mc.put(f'{base}/bank/{q1.id}', json={'difficulty': 5})
        check(r.status_code == 400, '非法难度 → 400')
        r = mc.put(f'{base}/bank/999999999', json={'status': 'active'})
        check(r.status_code == 404 and r.get_json()['error'] == 'not_found', '不存在的题 → 404')

        # ---- 停用 / 恢复 ----
        r = mc.put(f'{base}/bank/{q4.id}', json={'status': 'active'})
        db.session.expire_all()
        check(r.status_code == 200 and db.session.get(CourseQuizQuestion, q4.id).status == 'active'
              and db.session.get(CourseQuizQuestion, q4.id).origin == 'ai', '恢复停用题(origin 不变)')
        r = mc.put(f'{base}/bank/{q4.id}', json={'status': 'disabled'})
        db.session.expire_all()
        check(r.status_code == 200 and db.session.get(CourseQuizQuestion, q4.id).status == 'disabled', '停用')

        # ---- 全部通过待审 ----
        if pre_review == 0:
            r = mc.post(base + '/bank/approve-all')
            db.session.expire_all()
            check(r.status_code == 200 and r.get_json()['data']['approved'] == 2
                  and db.session.get(CourseQuizQuestion, q2.id).status == 'active'
                  and db.session.get(CourseQuizQuestion, q4.id).status == 'disabled', '全部通过:review → active,停用不动')
        else:
            print('SKIP 本课已有真实待审题,跳过 approve-all')

        # ---- 阅读时长设置 ----
        r = mc.post(base + '/settings', json={'min_read_seconds': '120'})
        db.session.expire_all()
        check(r.status_code == 200 and r.get_json()['data']['min_read_seconds'] == 120
              and db.session.get(CourseExamSetting, KEY).min_read_seconds == 120, '设置阅读时长 120')
        check(mc.get(base + '/bank').get_json()['data']['min_read_seconds'] == 120, '列表回显阅读时长')
        for bad in (-1, 'abc', 1.5, True, 999999):
            r = mc.post(base + '/settings', json={'min_read_seconds': bad})
            check(r.status_code == 400, f'阅读时长非法值 {bad!r} → 400')
        r = mc.post(base + '/settings', json={'min_read_seconds': ''})
        db.session.expire_all()
        check(r.status_code == 200 and db.session.get(CourseExamSetting, KEY).min_read_seconds is None,
              '清空 → 恢复自动')

        # ---- 生成(打桩)----
        def fake_start(app_, key, pages, uid, plan=generator.DEFAULT_PLAN, replace=False, client=None):
            p = generator.validate_plan(plan)
            calls['start'] = dict(key=key, n_pages=len(pages), uid=uid, plan=p, replace=replace,
                                  real_app=app_.__class__.__name__)
            return calls.get('start_result', True)
        generator.start_generation = fake_start
        r = mc.post(base + '/bank/generate', json={'plan': {'1': '5', '2': 3, '3': 2}, 'replace': True})
        st = calls.get('start') or {}
        check(r.status_code == 200 and st.get('plan') == {1: 5, 2: 3, 3: 2} and st.get('replace') is True
              and st.get('uid') == admin.id and st.get('n_pages') == len(PAGES) and st.get('real_app') == 'Flask',
              f'生成:计划解析 + 传真实 app {st}')
        calls.clear()
        r = mc.post(base + '/bank/generate', json={})
        check(r.status_code == 200 and calls['start']['plan'] == generator.DEFAULT_PLAN
              and calls['start']['replace'] is False, '生成:缺省 plan=默认、replace=False')
        r = mc.post(base + '/bank/generate', json={'replace': 'yes'})
        check(calls['start']['replace'] is False, '生成:replace 非 true 一律当 False')
        calls['start_result'] = False
        r = mc.post(base + '/bank/generate', json={})
        check(r.status_code == 409 and r.get_json()['error'] == 'running', '已在生成 → 409')
        for bad in ({'1': -1}, {'4': 3}, {'1': 0, '2': 0, '3': 0}, {'1': 301}, 'abc', None):
            r = mc.post(base + '/bank/generate', json={'plan': bad})
            check(r.status_code == 400 and r.get_json()['error'] == 'invalid_plan', f'非法计划 {bad!r} → 400')

        # ---- 单题重出(打桩)----
        def fake_regen(pages, q, client=None, existing_questions=None):
            calls['regen'] = dict(q=q, existing=list(existing_questions or []))
            if calls.get('regen_fail') == 'value':
                raise ValueError('AI 未生成可用的新题')
            if calls.get('regen_fail') == 'net':
                raise RuntimeError('proxy down')
            return {'qtype': 'single', 'difficulty': q['difficulty'], 'question': PREFIX + 'Q2 重出',
                    'options': ['n1', 'n2', 'n3'], 'answer': 1, 'explain': '新', 'source_page': 2}
        generator.regenerate_one = fake_regen
        r = mc.post(f'{base}/bank/{q2.id}/regenerate')
        db.session.expire_all()
        q = db.session.get(CourseQuizQuestion, q2.id)
        ex = calls['regen']['existing']
        check(r.status_code == 200 and q.question == PREFIX + 'Q2 重出' and q.qtype == 'single' and q.answer == 1
              and q.status == 'review' and q.review_note == '单题重出' and q.origin == 'ai' and q.source_page == 2
              and q.ai_difficulty is None, '重出成功:覆盖内容 + 待审')
        check(PREFIX + 'Q4' not in ex and PREFIX + 'Q2' not in ex and any(t.startswith(PREFIX + 'Q1') for t in ex),
              '重出:防重复列表 = 本课其余未停用题')
        calls['regen_fail'] = 'value'
        r = mc.post(f'{base}/bank/{q2.id}/regenerate')
        check(r.status_code == 422 and r.get_json()['error'] == 'regenerate_failed', '重出无可用结果 → 422')
        calls['regen_fail'] = 'net'
        r = mc.post(f'{base}/bank/{q2.id}/regenerate')
        check(r.status_code == 502 and r.get_json()['error'] == 'regenerate_failed', '重出调用异常 → 502')
        db.session.expire_all()
        check(db.session.get(CourseQuizQuestion, q2.id).question == PREFIX + 'Q2 重出', '重出失败不改原题')

        # ---- CSRF 开启时无 token 被拒 ----
        app.config['WTF_CSRF_ENABLED'] = True
        r = mc.post(base + '/bank/approve-all')
        check(r.status_code == 400 and (r.get_json() or {}).get('error') == 'csrf', 'CSRF:无 token → 400 csrf')
        app.config['WTF_CSRF_ENABLED'] = False
    finally:
        generator.start_generation, generator.regenerate_one = orig_start, orig_regen
        app.config['WTF_CSRF_ENABLED'] = False
        db.session.rollback()
        qids = [str(i) for (i,) in db.session.query(CourseQuizQuestion.id).filter(
            CourseQuizQuestion.question.like(PREFIX + '%')).all()]
        if qids:
            TrainingQuizAttempt.query.filter(TrainingQuizAttempt.course_slug == KEY,
                                             TrainingQuizAttempt.question_id.in_(qids)).delete(
                synchronize_session=False)
        CourseQuizQuestion.query.filter(CourseQuizQuestion.question.like(PREFIX + '%')).delete(
            synchronize_session=False)
        row = db.session.get(CourseExamSetting, KEY)
        if saved is None:
            if row is not None:
                db.session.delete(row)
        else:
            for k, v in saved.items():
                setattr(row, k, v)
        db.session.commit()
        left = CourseQuizQuestion.query.filter(CourseQuizQuestion.question.like(PREFIX + '%')).count()
        left += TrainingQuizAttempt.query.filter(TrainingQuizAttempt.course_slug == KEY,
                                                 TrainingQuizAttempt.question_id.in_(qids or ['-'])).count()
        print('清理完成,残留行数:', left)

    print('\n' + ('全部通过' if not fails else f'{len(fails)} 项失败:\n  - ' + '\n  - '.join(fails)))
    sys.exit(1 if fails else 0)
