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

    base = f'/api/learning/{KEY}'
    client = app.test_client()
    with client.session_transaction() as s:
        s['_user_id'] = str(UID)
        s['_fresh'] = True
        s['role'] = u.role           # 全局 check_login 会比对 session 角色,不一致即强制登出(302)

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

        # ---- CSRF 开启时无 token 的 POST 被拒 ----
        app.config['WTF_CSRF_ENABLED'] = True
        try:
            before = dict(prog().page_seconds)
            r = client.post(base + '/read-ping', json={'page': 1, 'seconds': 15})
            check(r.status_code == 400, f'CSRF 开启 + 无 token → 400(实际 {r.status_code})')
            check(dict(prog().page_seconds) == before, 'CSRF 拒绝时未进入视图(进度未变)')
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
        db.session.commit()
        left = (CourseLearningProgress.query.filter_by(user_id=UID, course_key=KEY).count()
                + CourseQuizQuestion.query.filter(CourseQuizQuestion.question.like(PREFIX + '%')).count()
                + TrainingQuizAttempt.query.filter_by(user_id=UID, course_slug=KEY, module_slug='bank').count()
                + LearningBuddyPref.query.filter_by(user_id=UID).count())
        print('清理完成,残留行数:', left)

    print('\n' + ('全部通过' if not fails else f'{len(fails)} 项失败:\n  - ' + '\n  - '.join(fails)))
    sys.exit(1 if fails else 0)
