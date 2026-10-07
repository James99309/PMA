#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""种子题库自动导入(service.ensure_seeded / ensure_seeded_many)集成验证(pma_local)。

一、假课(临时种子目录,SEED_DIR 打桩):导入条数/状态/字段、不合法题跳过、幂等、
    已有题(哪怕全停用)不导、course_key 不符不导、无种子文件、并发两线程只导一次、进程记忆零查询。
二、真实三门 CN 课种子:本地为空时经 GET /api/learning/buddy(调用点)+ 服务直调导入,
    打印每课导入数 / active 数 / active 满分,然后硬删,pma_local 保持干净。
所有 ZZSEED- 假课题与本脚本导入的真实课题在 finally 里硬删。
"""
import json
import os
import shutil
import sys
import tempfile
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _report_flow_testkit import make_app, get_project_root

REAL_KEYS = ('smart-task-intercom', 'company-intro-training', 'apac-data-center-critical-comms-cn')
FAKE = 'ZZSEED-fake'
FAKE_DISABLED = 'ZZSEED-has-rows'
FAKE_MISMATCH = 'ZZSEED-mismatch'
FAKE_NOFILE = 'ZZSEED-nofile'
FAKE_MANY = 'ZZSEED-many'

app = make_app()

from flask import g
from flask.testing import FlaskClient


class FreshUserClient(FlaskClient):
    def open(self, *args, **kwargs):
        g.pop('_login_user', None)
        return super().open(*args, **kwargs)


app.test_client_class = FreshUserClient
app.config['WTF_CSRF_ENABLED'] = False

GOOD = [
    {'qtype': 'single', 'difficulty': 1, 'question': '单选题', 'options': ['a', 'b', 'c'], 'answer': 2,
     'explain': '解析1', 'source_page': 3, 'status': 'active', 'ai_difficulty': 1, 'review_note': None},
    {'qtype': 'multi', 'difficulty': 3, 'question': '多选题', 'options': ['a', 'b', 'c', 'd'], 'answer': [3, 0],
     'explain': '解析2', 'source_page': 4, 'status': 'review', 'ai_difficulty': 2, 'review_note': '复核存疑'},
    {'qtype': 'judge', 'difficulty': 2, 'question': '判断题', 'options': None, 'answer': False,
     'explain': '', 'source_page': None, 'status': 'active', 'ai_difficulty': None, 'review_note': None},
]
BAD = [
    {'qtype': 'single', 'difficulty': 1, 'question': '答案越界', 'options': ['a', 'b'], 'answer': 5,
     'status': 'active'},
    {'qtype': 'multi', 'difficulty': 2, 'question': '多选只一个对', 'options': ['a', 'b', 'c'], 'answer': [1],
     'status': 'active'},
    {'qtype': 'single', 'difficulty': 2, 'question': '   ', 'options': ['a', 'b'], 'answer': 0, 'status': 'active'},
    'not-a-dict',
]

with app.app_context():
    from app import db
    from sqlalchemy import event
    from app.models.user import User
    from app.models.course_exam import CourseQuizQuestion
    from app.services.course_exam import service as S, logic as L
    import app.views.knowledge_wiki as KW

    fails = []

    def check(cond, msg):
        print(('OK  ' if cond else 'FAIL') + ' ' + msg)
        if not cond:
            fails.append(msg)

    def rows(key):
        return CourseQuizQuestion.query.filter_by(course_key=key).order_by(CourseQuizQuestion.id).all()

    REAL_SEED_DIR = S.SEED_DIR
    tmp = tempfile.mkdtemp(prefix='cq-seed-')

    def write_seed(key, questions, course_key=None):
        with open(os.path.join(tmp, key + '.json'), 'w', encoding='utf-8') as f:
            json.dump({'course_key': course_key or key, 'version': 1, 'questions': questions}, f,
                      ensure_ascii=False)

    real_pre = {k: CourseQuizQuestion.query.filter_by(course_key=k).count() for k in REAL_KEYS}
    real_touch = [k for k, n in real_pre.items() if n == 0]   # 只碰本地原本为空的真实课
    fake_keys = (FAKE, FAKE_DISABLED, FAKE_MISMATCH, FAKE_NOFILE, FAKE_MANY)
    try:
        # ================= 一、假课 =================
        S.SEED_DIR = tmp
        S.reset_seed_memo()
        write_seed(FAKE, GOOD + BAD)
        write_seed(FAKE_DISABLED, GOOD)
        write_seed(FAKE_MISMATCH, GOOD, course_key='other-course')
        write_seed(FAKE_MANY, GOOD)

        n = S.ensure_seeded(FAKE)
        got = rows(FAKE)
        check(n == 3 and len(got) == 3, f'导入 3 道合法题、跳过 4 道不合法(返回 {n},库中 {len(got)})')
        by_q = {q.question: q for q in got}
        s1, m1, j1 = by_q.get('单选题'), by_q.get('多选题'), by_q.get('判断题')
        check(s1 and s1.status == 'active' and s1.answer == 2 and s1.options == ['a', 'b', 'c']
              and s1.explain == '解析1' and s1.source_page == 3 and s1.ai_difficulty == 1
              and s1.origin == 'ai' and s1.created_by is None and s1.review_note is None,
              '单选题字段原样落库(origin=ai / created_by 空)')
        check(m1 and m1.status == 'review' and m1.answer == [0, 3] and m1.review_note == '复核存疑'
              and m1.ai_difficulty == 2 and m1.difficulty == 3,
              '多选题 review 状态 + review_note + 答案规范化排序')
        check(j1 and j1.options is None and j1.answer is False and j1.explain is None
              and j1.source_page is None and j1.ai_difficulty is None,
              '判断题 options 为空、空解析存 NULL')

        # 进程记忆:已检查过的课不再碰库
        stmts = []

        def _count(conn, cursor, statement, *a):
            stmts.append(statement)
        event.listen(db.engine, 'before_cursor_execute', _count)
        try:
            n2 = S.ensure_seeded(FAKE)
            n3 = S.ensure_seeded_many([FAKE, FAKE])
        finally:
            event.remove(db.engine, 'before_cursor_execute', _count)
        check(n2 == 0 and n3 == 0 and not stmts, f'记忆命中:再次调用零 SQL(实际 {len(stmts)} 条)')

        # 幂等:清记忆后再调,已有题 → 不导
        S.reset_seed_memo()
        n4 = S.ensure_seeded(FAKE)
        check(n4 == 0 and len(rows(FAKE)) == 3, '清记忆后重调:已有题不重复导入')

        # 已有题(哪怕只有一道停用)→ 不导
        db.session.add(CourseQuizQuestion(course_key=FAKE_DISABLED, qtype='judge', difficulty=1,
                                          question='ZZSEED 停用题', answer=True, status='disabled'))
        db.session.commit()
        n5 = S.ensure_seeded(FAKE_DISABLED)
        check(n5 == 0 and len(rows(FAKE_DISABLED)) == 1, '本课已有停用题 → 种子不导入')

        # course_key 不符 → 不导;无种子文件 → 0 且记忆
        check(S.ensure_seeded(FAKE_MISMATCH) == 0 and not rows(FAKE_MISMATCH), '种子 course_key 不符 → 不导入')
        check(S.ensure_seeded(FAKE_NOFILE) == 0 and FAKE_NOFILE in S._SEED_CHECKED, '无种子文件 → 0 且记入记忆')
        check(S.ensure_seeded('../etc') == 0, '路径穿越 key → 不读文件')

        # 批量:只导确实为空且有种子的课
        S.reset_seed_memo()
        nm = S.ensure_seeded_many([FAKE, FAKE_DISABLED, FAKE_NOFILE, FAKE_MANY])
        check(nm == 3 and len(rows(FAKE_MANY)) == 3 and len(rows(FAKE)) == 3 and len(rows(FAKE_DISABLED)) == 1,
              f'ensure_seeded_many 只导空课(返回 {nm})')
        check({FAKE, FAKE_DISABLED, FAKE_NOFILE, FAKE_MANY} <= S._SEED_CHECKED, '批量调用后四课都记入记忆')

        # 并发:两线程同时首访,只导一次(advisory 锁内重判)
        CourseQuizQuestion.query.filter_by(course_key=FAKE).delete()
        db.session.commit()
        S.reset_seed_memo()
        results, errors = [], []
        barrier = threading.Barrier(2)

        def worker():
            with app.app_context():
                try:
                    barrier.wait()
                    results.append(S.ensure_seeded(FAKE))
                except Exception as e:      # noqa
                    errors.append(repr(e))
                finally:
                    db.session.remove()
        ts = [threading.Thread(target=worker) for _ in range(2)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        db.session.expire_all()
        check(not errors and sorted(results) == [0, 3] and len(rows(FAKE)) == 3,
              f'两线程并发首访只导一次(返回 {results},库中 {len(rows(FAKE))},错误 {errors})')

        # ================= 二、真实三门课种子 =================
        S.SEED_DIR = REAL_SEED_DIR
        S.reset_seed_memo()
        skipped = [k for k in REAL_KEYS if k not in real_touch]
        if skipped:
            print('INFO 本地已有题、跳过真实导入验证:', skipped)
        if not os.path.isfile(KW._course_html_path('smart-task-intercom')):
            main_assets = os.path.normpath(os.path.join(get_project_root(), '..', '..', 'app', 'course_assets'))
            KW.COURSE_ASSETS_DIR = main_assets
            print('INFO 课件目录改指主仓:', main_assets)

        admin = User.query.filter(User._is_active == True, User.role == 'admin').order_by(User.id).first()
        c = app.test_client()
        with c.session_transaction() as s:
            s['_user_id'] = str(admin.id)
            s['_fresh'] = True
            s['role'] = admin.role
        r = c.get('/api/learning/buddy')
        check(r.status_code == 200, f'GET /api/learning/buddy 200(实际 {r.status_code})')
        listed = {x['key'] for x in (r.get_json() or {}).get('data', {}).get('courses', [])}
        db.session.expire_all()
        via_api = [k for k in real_touch if rows(k)]
        print('INFO 经小源面板调用点导入的课:', via_api, '| 面板列出:', sorted(listed & set(REAL_KEYS)))
        for k in real_touch:
            if k not in via_api:       # 课件不在本地盘上的课,面板不会列出,直接调服务验证种子本身
                S.ensure_seeded(k)
        for k in real_touch:
            with open(os.path.join(REAL_SEED_DIR, k + '.json'), encoding='utf-8') as f:
                expected = len(json.load(f)['questions'])
            got = rows(k)
            active = [q for q in got if q.status == 'active']
            h = L.bank_health([q.as_logic() for q in active])
            from collections import Counter
            st = Counter(q.status for q in got)
            check(len(got) == expected, f'{k}: 导入 {len(got)}/{expected} 题')
            print(f'INFO {k}: 导入 {len(got)} | 状态 {dict(st)} | active {len(active)} '
                  f'| active 满分 {h["max_score"]} | 健康 {h["ok"]} | 面板列出 {k in listed}')
            check(all(q.status != 'review' or q.review_note for q in got), f'{k}: review 题都带 review_note')
            check(all(q.origin == 'ai' and q.created_by is None for q in got), f'{k}: origin=ai / created_by 空')
    finally:
        S.SEED_DIR = REAL_SEED_DIR
        S.reset_seed_memo()
        db.session.rollback()
        for k in fake_keys + tuple(real_touch):
            CourseQuizQuestion.query.filter_by(course_key=k).delete()
        db.session.commit()
        shutil.rmtree(tmp, ignore_errors=True)
        left = {k: CourseQuizQuestion.query.filter_by(course_key=k).count() for k in fake_keys + REAL_KEYS}
        print('INFO 清理后各课题数:', left, '| 测试前真实课:', real_pre)

    print()
    print('全部通过' if not fails else f'失败 {len(fails)} 项: {fails}')
    sys.exit(1 if fails else 0)
