#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""学员端课程考核 API(app/views/learning.py)集成验证(pma_local)。

用 Flask test_client + session 登录;选一门盘上有课件的 HTML 课,插入 ZZTEST- 题,
结束在 finally 里硬删:本人本课进度行 / 作答留痕(module_slug='bank') / ZZTEST 题 / 小源偏好行。
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _report_flow_testkit import make_app, get_project_root

PREFERRED_KEY = 'smart-task-intercom'
PREFIX = 'ZZTEST-'

app = make_app()


from flask import g
from flask.testing import FlaskClient


class FreshUserClient(FlaskClient):
    """脚本外层持有 app_context,请求复用同一个 g;flask-login 把用户缓存在 g._login_user,
    不清掉的话上一个请求(如匿名客户端)的身份会串到下一个请求。"""
    def open(self, *args, **kwargs):
        g.pop('_login_user', None)
        return super().open(*args, **kwargs)


app.test_client_class = FreshUserClient
app.config['WTF_CSRF_ENABLED'] = False       # 仅测试客户端关闭;下面单独验一次开启时无 token 被拒

with app.app_context():
    from app import db
    from app.models.user import User
    from app.models.course import InteractiveCourse
    from app.models.course_exam import CourseQuizQuestion, CourseLearningProgress, LearningBuddyPref
    from app.models.training import TrainingQuizAttempt, get_local_time
    from app.services.course_exam import logic as L
    import app.views.knowledge_wiki as KW
    from app.services.course_exam import service as S

    # 种子题库自动导入另由 check_course_exam_seed.py 验证;这里指向不存在的目录关掉它,
    # 保持本脚本「题库只有 ZZTEST 题」的前提,也不在 pma_local 留下种子题
    S.SEED_DIR = os.path.join(get_project_root(), 'zz-no-seed-dir')
    S.reset_seed_memo()

    # worktree 里课件不入 git;盘上没有就借主仓的 course_assets(只读)
    if not any(os.path.isfile(KW._course_html_path(r.key))
               for r in InteractiveCourse.query.filter_by(media_type='html').all()):
        main_assets = os.path.normpath(os.path.join(get_project_root(), '..', '..', 'app', 'course_assets'))
        if os.path.isdir(main_assets):
            KW.COURSE_ASSETS_DIR = main_assets
            print('INFO 课件目录改指主仓:', main_assets)

    html_rows = InteractiveCourse.query.filter_by(media_type='html').order_by(InteractiveCourse.id).all()
    cands = [r for r in html_rows if KW._find_course(r.key)[0]]
    cands.sort(key=lambda r: r.key != PREFERRED_KEY)
    if not cands:
        sys.exit('没有盘上存在课件的 HTML 课程,无法验证')
    KEY = cands[0].key
    non_html = InteractiveCourse.query.filter(InteractiveCourse.media_type != 'html').first()
    print('INFO 测试课程:', KEY, '| 非 HTML 课程:', non_html.key if non_html else None)

    # 找一个本课无进度、无小源偏好、无留痕的在职用户,保证清理不误伤真实数据
    u = None
    for cand in User.query.filter(User._is_active == True).order_by(User.id).all():
        if (CourseLearningProgress.query.filter_by(user_id=cand.id, course_key=KEY).first() is None
                and db.session.get(LearningBuddyPref, cand.id) is None
                and TrainingQuizAttempt.query.filter_by(user_id=cand.id, course_slug=KEY,
                                                        module_slug='bank').first() is None):
            u = cand
            break
    assert u is not None, '找不到干净的测试用户'
    UID = u.id
    print('INFO 测试用户:', UID, u.username)

    fails = []
    def check(cond, msg):
        print(('OK  ' if cond else 'FAIL') + ' ' + msg)
        if not cond:
            fails.append(msg)

    def find_keys(obj, names):
        """递归扫描 JSON,返回出现的敏感键。"""
        hit = set()
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in names:
                    hit.add(k)
                hit |= find_keys(v, names)
        elif isinstance(obj, list):
            for v in obj:
                hit |= find_keys(v, names)
        return hit

    def add_q(i, difficulty=3):
        n = L.normalize_question({'qtype': 'single', 'difficulty': difficulty,
                                  'options': ['A', 'B', 'C', 'D'], 'answer': 0})
        db.session.add(CourseQuizQuestion(
            course_key=KEY, qtype=n['qtype'], difficulty=n['difficulty'], options=n['options'],
            answer=n['answer'], question=f'{PREFIX}Q{i}', explain='ZZTEST explain', status='active'))

    def prog():
        db.session.expire_all()
        return CourseLearningProgress.query.filter_by(user_id=UID, course_key=KEY).first()

    def buddy_course(c):
        d = c.get('/api/learning/buddy').get_json()['data']
        return d, next((x for x in d['courses'] if x['key'] == KEY), None)

    # ---- _get_course_pages:mtime 变化即重解析;pop(key) 仍可清缓存;读不到文件不缓存 ----
    import tempfile
    def deck(labels):
        secs = ''.join(f'<section data-label="{x}" data-speaker-notes="n{x}"></section>' for x in labels)
        return f'<script type="__bundler/template">{secs}</script>'
    with tempfile.TemporaryDirectory() as td:
        fp, ck = os.path.join(td, 'deck.html'), 'zz-cache-test'
        with open(fp, 'w') as f: f.write(deck(['a']))
        os.utime(fp, (1_000_000, 1_000_000))
        first = KW._get_course_pages(ck, fp)
        with open(fp, 'w') as f: f.write(deck(['a', 'b']))
        os.utime(fp, (1_000_000, 1_000_000))
        check(len(first) == 1 and len(KW._get_course_pages(ck, fp)) == 1, '页面缓存:mtime 未变命中缓存')
        os.utime(fp, (2_000_000, 2_000_000))
        check(len(KW._get_course_pages(ck, fp)) == 2, '页面缓存:mtime 变化后重新解析')
        KW._COURSE_PAGES_CACHE.pop(ck, None)
        check(ck not in KW._COURSE_PAGES_CACHE, '页面缓存:pop(key) 照常清除')
        check(KW._get_course_pages('zz-missing', os.path.join(td, 'nope.html')) == []
              and 'zz-missing' not in KW._COURSE_PAGES_CACHE, '页面缓存:文件不存在返回 [] 且不缓存')
        KW._COURSE_PAGES_CACHE.pop(ck, None)

    base = f'/api/learning/{KEY}'
    client = app.test_client()
    with client.session_transaction() as s:
        s['_user_id'] = str(UID)
        s['_fresh'] = True
        s['role'] = u.role           # 全局 check_login 会比对 session 角色,不一致即强制登出(302)

    # 本课若已有真实题(如试用实例导入的种子),临时停用,结束原样恢复 —— 保持「题库只有 ZZTEST 题」前提
    _parked = {q.id: q.status for q in CourseQuizQuestion.query.filter(
        CourseQuizQuestion.course_key == KEY, CourseQuizQuestion.status != 'disabled',
        ~CourseQuizQuestion.question.like(PREFIX + '%')).all()}
    if _parked:
        CourseQuizQuestion.query.filter(CourseQuizQuestion.id.in_(list(_parked))).update(
            {'status': 'disabled'}, synchronize_session=False)
        db.session.commit()
        print('INFO 临时停用本课已有题:', len(_parked))

    try:
        # ---- 未登录 ----
        anon = app.test_client()
        r = anon.get(base + '/progress')
        check(r.status_code in (401, 302), f'未登录 → 401/302(实际 {r.status_code})')
        r = anon.post(base + '/read-ping', json={'page': 1, 'seconds': 15})
        check(r.status_code in (401, 302), f'未登录 POST → 401/302(实际 {r.status_code})')

        # ---- 404:未知 key / 非 HTML ----
        check(client.get('/api/learning/zz-no-such-course/progress').status_code == 404, '未知课程 → 404')
        if non_html:
            check(client.get(f'/api/learning/{non_html.key}/progress').status_code == 404,
                  f'非 HTML 课程({non_html.media_type}) → 404')

        # ---- 进度:只读不插行 ----
        r = client.get(base + '/progress')
        j = r.get_json()
        check(r.status_code == 200 and j['success'] and 'percent' in j['data']['read']
              and j['data']['read']['percent'] == 0, 'GET progress 200 且含 read.percent')
        check(prog() is None, 'GET progress 不插进度行')

        # ---- 阅读上报 ----
        r = client.post(base + '/read-ping', json={'page': 1, 'seconds': 15})
        j = r.get_json()
        check(r.status_code == 200 and j['success'] and j['data']['read']['page_seconds'].get('1') == 15
              and not j['data']['read']['unlocked'], 'POST read-ping 200,计时 15s、未解锁')
        r = client.post(base + '/read-ping', json={'page': 'abc', 'seconds': 'x'})
        check(r.status_code == 200 and r.get_json()['success'], '非法 page/seconds 不报错(服务层忽略)')
        r = client.post(base + '/read-ping', data='not json', content_type='text/plain')
        check(r.status_code == 200, '非 JSON 请求体也不报错')

        # ---- 非对象 JSON 请求体不 500 ----
        for body in ([1], 'x'):
            r = client.post(base + '/read-ping', json=body)
            check(r.status_code == 200, f'read-ping json={body!r} → 200(实际 {r.status_code})')
            r = client.post('/api/learning/buddy/toggle', json=body)
            check(r.status_code == 400, f'toggle json={body!r} → 400(实际 {r.status_code})')

        # ---- CSRF:开启时无 token 被拒(JSON error=csrf);取新 token 后放行;其他路径行为不变 ----
        app.config['WTF_CSRF_ENABLED'] = True
        try:
            before = dict(prog().page_seconds)
            r = client.post(base + '/read-ping', json={'page': 1, 'seconds': 15})
            j = r.get_json(silent=True) or {}
            check(r.status_code == 400 and j.get('error') == 'csrf' and j.get('message'),
                  f'CSRF 开启 + 无 token → 400 JSON error=csrf(实际 {r.status_code} {j.get("error")})')
            check(dict(prog().page_seconds) == before, 'CSRF 拒绝时未进入视图(进度未变)')
            r = client.get('/api/learning/csrf')
            token = (r.get_json() or {}).get('token')
            check(r.status_code == 200 and token, 'GET /api/learning/csrf 返回 token')
            r = client.post(base + '/read-ping', json={'page': 1, 'seconds': 15}, headers={'X-CSRFToken': token})
            check(r.status_code == 200 and r.get_json()['success'], '带 X-CSRFToken 重试 → 200')
            r = app.test_client().post('/auth/login', data={'username': 'x', 'password': 'y'})
            check(r.status_code == 400 and not (r.is_json and (r.get_json() or {}).get('error') == 'csrf'),
                  f'非 /api/learning/ 路径 CSRF 失败保持原行为(实际 {r.status_code} {r.content_type})')
        finally:
            app.config['WTF_CSRF_ENABLED'] = False

        # ---- 未解锁 ----
        r = client.get(base + '/exam/current')
        check(r.status_code == 403 and r.get_json()['error'] == 'locked' and r.get_json()['message'],
              '未解锁 exam/current → 403 locked(带文案)')
        check(client.post(base + '/exam/answer', json={'answer': 0}).status_code == 403, '未解锁 exam/answer → 403')
        check(client.post(base + '/exam/next').status_code == 403, '未解锁 exam/next → 403')

        # ---- 题库:3 题时不健康,小源不列;补足后列出 ----
        for i in range(1, 4):
            add_q(i)
        db.session.commit()
        d, bc = buddy_course(client)
        check(d['enabled'] is True and bc is None, '小源:默认开启;题库不健康(3 题)不列本课')
        # 题库不健康时即便已解锁也不能进考核(上线前收尾:题库健康门禁)
        p = prog()
        p.unlocked_at = get_local_time()
        db.session.commit()
        for m, path in (('get', '/exam/current'), ('post', '/exam/next'), ('post', '/exam/answer')):
            r = getattr(client, m)(base + path, **({'json': {'answer': 0}} if path.endswith('answer') else {}))
            jj = r.get_json() or {}
            check(r.status_code == 403 and jj.get('error') == 'bank_not_ready' and jj.get('message') == '题库准备中，暂不能考核',
                  f'题库不健康:{path} → 403 bank_not_ready(实际 {r.status_code} {jj.get("error")})')
        jj = client.get(base + '/progress').get_json()
        check(jj['data']['exam'].get('available') is False, '题库不健康:progress exam.available=False')
        check(prog().current_question_id is None, '题库不健康:未抽题落盘')
        p = prog()
        p.unlocked_at = None
        db.session.commit()
        for i in range(4, 35):                           # 34 道难题 × 3 分 = 102 ≥ 100
            add_q(i)
        db.session.commit()
        d, bc = buddy_course(client)
        check(bc is not None and bc['score'] == 0 and not bc['unlocked'] and 0 < bc['read_percent'] < 100
              and bc['play_url'].endswith('/wiki/play/' + KEY) and not bc['perfect'],
              f'小源:题库健康后列出本课(read_percent={bc and bc["read_percent"]})')

        # ---- 解锁后作答 ----
        p = prog()
        p.unlocked_at = get_local_time()
        db.session.commit()
        check(client.get(base + '/progress').get_json()['data']['exam'].get('available') is True,
              '题库健康:progress exam.available=True')
        r = client.get(base + '/exam/current')
        j = r.get_json()
        leaked = find_keys(j, {'answer', 'explain', 'correct_answer'})
        check(r.status_code == 200 and j['data']['question']['question'].startswith(PREFIX)
              and not j['data']['answered'], 'exam/current 200 出 ZZTEST 题')
        check(not leaked, f'exam/current 响应递归无 answer/explain/correct_answer(命中 {leaked or "无"})')
        r2 = client.get(base + '/exam/current').get_json()
        check(r2['data']['question'] == j['data']['question'], '断点幂等:再次打开同题同顺序')
        qid = j['data']['question']['id']
        right = prog().current_option_order.index(0)
        r = client.post(base + '/exam/answer', json={'answer': 'bogus'})
        check(r.status_code == 400 and r.get_json()['error'] == 'bad_answer' and r.get_json()['message'],
              '非法答案 → 400 bad_answer')
        r = client.post(base + '/exam/answer', json={'answer': right})
        j = r.get_json()
        check(r.status_code == 200 and j['data']['correct'] is True and j['data']['score'] == 3
              and j['data']['correct_answer'] == right, 'exam/answer 答对 → correct,得 3 分')
        r = client.post(base + '/exam/answer', json={'answer': right})
        check(r.status_code == 409 and r.get_json()['error'] == 'already_answered',
              '重复提交 → 409 already_answered')
        check(prog().score == 3, '重复提交不重复加分')
        r = client.post(base + '/exam/next')
        j = r.get_json()
        check(r.status_code == 200 and j['data']['question']['id'] != qid and not j['data']['answered'],
              'exam/next 换题')
        check(not find_keys(j, {'answer', 'explain', 'correct_answer'}), 'exam/next 响应不泄露答案')

        # ---- 旧版考核接口已下线:410,不出题不判分不给答案 ----
        for m, path in (('get', f'/wiki/play/{KEY}/quiz/questions'), ('post', f'/wiki/play/{KEY}/quiz/submit')):
            r = getattr(client, m)(path, **({'json': {'answers': {}}} if m == 'post' else {}))
            jj = r.get_json() or {}
            check(r.status_code == 410 and jj.get('success') is False and jj.get('message') == '旧版考核已下线'
                  and not find_keys(jj, {'answer', 'answers', 'questions', 'correct_answer', 'explain', 'details'}),
                  f'旧接口 {path} → 410 且无题目/答案(实际 {r.status_code})')

        # ---- 非对象 JSON 提交答案不 500 ----
        for body in ([1], 'x'):
            r = client.post(base + '/exam/answer', json=body)
            check(r.status_code in (400, 409) and r.status_code != 500,
                  f'exam/answer json={body!r} → 4xx(实际 {r.status_code})')

        # ---- 解析不出页面的课:暂不支持考核 ----
        orig_pages = KW._get_course_pages
        KW._get_course_pages = lambda k, p: [] if k == KEY else orig_pages(k, p)
        try:
            snap = (dict(prog().page_seconds), prog().last_ping_at)
            r = client.get(base + '/progress')
            check(r.status_code == 200 and r.get_json()['data']['read'].get('unavailable') is True,
                  '无页面:progress 带 read.unavailable')
            r = client.post(base + '/read-ping', json={'page': 1, 'seconds': 15})
            check(r.status_code == 200 and (dict(prog().page_seconds), prog().last_ping_at) == snap,
                  '无页面:read-ping 空转 200、进度不变')
            for method, path in (('get', '/exam/current'), ('post', '/exam/answer'), ('post', '/exam/next')):
                r = getattr(client, method)(base + path, json={'answer': 0} if method == 'post' else None)
                check(r.status_code == 403 and r.get_json()['error'] == 'unavailable' and r.get_json()['message'],
                      f'无页面:{path} → 403 unavailable')
            d, bc = buddy_course(client)
            check(bc is None, '无页面:小源不列本课')
        finally:
            KW._get_course_pages = orig_pages
        d, bc = buddy_course(client)
        check(bc is not None, '恢复页面后小源重新列出本课')

        # ---- 小源列表分数 / 排序 / 满分不列 ----
        d, bc = buddy_course(client)
        check(bc is not None and bc['score'] == 3 and bc['unlocked'] and bc['read_percent'] == 100
              and not bc['passed'], '小源:本课分数 3、已解锁、阅读 100%')
        flags = [not c['unlocked'] for c in d['courses']]
        check(flags == sorted(flags), '小源:已解锁的课排在前面')
        p = prog()
        p.perfect_at = get_local_time()
        db.session.commit()
        d, bc = buddy_course(client)
        check(bc is None, '小源:满分课不再列出')

        # ---- 小源开关 ----
        r = client.post('/api/learning/buddy/toggle', json={'enabled': 'no'})
        check(r.status_code == 400, '开关:非 bool → 400')
        r = client.post('/api/learning/buddy/toggle', json={'enabled': False})
        check(r.status_code == 200 and r.get_json()['data']['enabled'] is False
              and client.get('/api/learning/buddy').get_json()['data']['enabled'] is False, '开关:关闭')
        r = client.post('/api/learning/buddy/toggle', json={'enabled': True})
        check(r.status_code == 200 and client.get('/api/learning/buddy').get_json()['data']['enabled'] is True,
              '开关:重新开启')
    finally:
        db.session.rollback()
        TrainingQuizAttempt.query.filter_by(user_id=UID, course_slug=KEY, module_slug='bank').delete()
        CourseLearningProgress.query.filter_by(user_id=UID, course_key=KEY).delete()
        CourseQuizQuestion.query.filter(CourseQuizQuestion.course_key == KEY,
                                        CourseQuizQuestion.question.like(PREFIX + '%')).delete(
            synchronize_session=False)
        LearningBuddyPref.query.filter_by(user_id=UID).delete()
        for _qid, _st in _parked.items():          # 恢复临时停用的真实题
            CourseQuizQuestion.query.filter_by(id=_qid).update({'status': _st}, synchronize_session=False)
        db.session.commit()
        left = (CourseLearningProgress.query.filter_by(user_id=UID, course_key=KEY).count()
                + CourseQuizQuestion.query.filter(CourseQuizQuestion.question.like(PREFIX + '%')).count()
                + TrainingQuizAttempt.query.filter_by(user_id=UID, course_slug=KEY, module_slug='bank').count()
                + LearningBuddyPref.query.filter_by(user_id=UID).count())
        print('清理完成,残留行数:', left)

    print('\n' + ('全部通过' if not fails else f'{len(fails)} 项失败:\n  - ' + '\n  - '.join(fails)))
    sys.exit(1 if fails else 0)
