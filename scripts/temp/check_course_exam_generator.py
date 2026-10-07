#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""course_exam.generator 出题任务集成验证(pma_local)。

假 client 注入,不调真实 AI;独立 course_key 'zz-exam-gen-test',结束硬删题目、设置行与本次站内通知。
覆盖:落库/复核状态/通知、追加去重、replace 只停用 AI 题、产出不足保护、早期异常也发失败通知、
跨进程生成标记(占用中拒绝 / 过期接管 / 结束释放 / 非法 plan 不抢标记)。
"""
import os, sys, threading, time
from datetime import timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _report_flow_testkit import make_app

KEY = 'zz-exam-gen-test'
PAGES = [{'label': '公司', 'notes': '总部在上海'}, {'label': '产品', 'notes': '直放站与对讲机'}]


class FakeClient:
    def __init__(self, replies, gate=None): self.replies = list(replies); self.calls = []; self.gate = gate
    def complete(self, system, user, model, max_tokens=16000, temperature=None):
        if self.gate is not None:
            self.gate.wait(30)
        self.calls.append(user)
        class R: pass
        r = R(); r.text = self.replies.pop(0); return r
    def close(self): pass


def batch(*qs):
    items = ','.join('{"type":"single","question":"%s","options":["a","b","c","d"],"answer":1,"explain":"e","page":%d}'
                     % (q, p) for q, p in qs)
    return '{"questions":[%s]}' % items


def review_ok(n, d=1):
    return '{"reviews":[%s]}' % ','.join('{"index":%d,"difficulty":%d,"answer_ok":true}' % (i, d) for i in range(n))


REVIEW_OK_2 = '{"reviews":[{"index":0,"difficulty":1,"answer_ok":true},{"index":1,"difficulty":2,"answer_ok":false,"note":"答案存疑"}]}'

app = make_app()
with app.app_context():
    from app import db
    from app.models.user import User
    from app.models.message import Message
    from app.models.course import InteractiveCourse
    from app.models.course_exam import CourseQuizQuestion, CourseExamSetting
    from app.models.training import get_local_time
    from app.services.course_exam import generator as G

    u = User.query.filter(User._is_active == True).order_by(User.id).first()
    msg_ids_before = {m.id for m in Message.query.filter_by(recipient_id=u.id, message_type='course_bank_ready').all()}
    setting_pre = db.session.get(CourseExamSetting, KEY)
    assert setting_pre is None, '测试课已有设置行,先人工清理'
    fails = []
    def check(cond, msg):
        print(('OK  ' if cond else 'FAIL') + ' ' + msg)
        if not cond: fails.append(msg)
    def new_msgs():
        db.session.expire_all()
        return Message.query.filter(Message.recipient_id == u.id, Message.message_type == 'course_bank_ready',
                                    ~Message.id.in_(msg_ids_before or [-1])).order_by(Message.id).all()
    def rows():
        db.session.expire_all()
        return CourseQuizQuestion.query.filter_by(course_key=KEY).order_by(CourseQuizQuestion.id).all()
    def live():
        return [r for r in rows() if r.status != 'disabled']
    def setting():
        db.session.expire_all()
        return db.session.get(CourseExamSetting, KEY)
    def wait_idle(timeout=15):
        end = time.time() + timeout
        while time.time() < end:
            db.session.rollback()
            if not G.is_running(KEY):
                return True
            time.sleep(0.2)
        return False
    try:
        # ---- 第一次生成:易 1 + 中 1 → 1 active / 1 review ----
        fc = FakeClient([batch(('总部在哪个城市', 1)), batch(('直放站与对讲机的区别在于何处', 2)), REVIEW_OK_2])
        G.run_generation_job(app, KEY, PAGES, u.id, plan={1: 1, 2: 1}, client=fc)
        r1 = rows()
        check(len(fc.calls) == 3 and len(r1) == 2, f'首次生成入库 2 题,AI 调用 3 次 (calls={len(fc.calls)}, rows={len(r1)})')
        check([r.status for r in r1] == ['active', 'review'] and all(r.origin == 'ai' and r.created_by == u.id for r in r1),
              "复核结果落库:active/review,origin='ai',created_by=当前用户")
        check(r1[0].ai_difficulty == 1 and r1[1].review_note and '答案存疑' in r1[1].review_note
              and r1[0].source_page == 1 and r1[0].answer == 1 and r1[0].options == ['a', 'b', 'c', 'd'],
              'ai_difficulty / review_note / source_page / 答案选项落库正确')
        m = new_msgs()
        check(len(m) == 1 and m[0].title == '题库生成完成' and '启用 1 题，待审 1 题' in (m[0].content or '')
              and '失败' not in (m[0].content or '') and m[0].related_object_type == 'course',
              f'站内通知:{m[0].title if m else None} / {m[0].content if m else None}')

        # ---- 追加生成(replace=False):已有题干进防重复提示,相似题被去重;部分批失败写进通知 ----
        fc = FakeClient([batch(('总部在哪一个城市？', 1), ('对讲机用于哪类场景', 2)), 'garbage', review_ok(1)])
        G.run_generation_job(app, KEY, PAGES, u.id, plan={1: 2, 2: 1}, client=fc)
        r2 = rows()
        check(len(r2) == 3 and r2[-1].question == '对讲机用于哪类场景' and all(r.status != 'disabled' for r in r2)
              and '总部在哪个城市' in fc.calls[0], f'追加生成:已有题进提示、相似题被去重、旧题不动 (rows={len(r2)})')
        m = new_msgs()
        check('1 批生成失败' in (m[-1].content or ''), f'部分失败可见:{m[-1].content}')

        # ---- replace=True:人工题保留并进防重复提示,旧 AI 题停用 ----
        edited = CourseQuizQuestion(course_key=KEY, qtype='judge', difficulty=1, question='人工题:总部在上海',
                                    answer=True, status='active', origin='edited', created_by=u.id)
        db.session.add(edited); db.session.commit()
        fc = FakeClient([batch(('新题一', 1)), review_ok(1)])
        G.run_generation_job(app, KEY, PAGES, u.id, plan={1: 1}, replace=True, client=fc)
        lv = live()
        check(sorted(r.question for r in lv) == sorted(['人工题:总部在上海', '新题一'])
              and '人工题:总部在上海' in fc.calls[0] and '总部在哪个城市' not in fc.calls[0],
              f'replace=True:旧 AI 题停用、人工题保留且只把人工题作已有题 (live={[r.question for r in lv]})')

        # ---- replace 课件薄但无失败批:计划 4 只出 1 → 照常替换 ----
        fc = FakeClient([batch(('薄课唯一题', 1)), review_ok(1)])
        G.run_generation_job(app, KEY, PAGES, u.id, plan={1: 4}, replace=True, client=fc)
        lv = live()
        m = new_msgs()
        check(sorted(r.question for r in lv) == sorted(['人工题:总部在上海', '薄课唯一题'])
              and m[-1].title == '题库生成完成',
              f'产出少但无失败批:照常替换 (live={[r.question for r in lv]}, {m[-1].content})')

        # ---- replace 失败批 + 产出不足:中止,题库一行不动 ----
        n_before, live_before = len(rows()), sorted(r.id for r in live())
        G.run_generation_job(app, KEY, PAGES, u.id, plan={1: 26}, replace=True,
                             client=FakeClient(['garbage', batch(('孤零零一题', 1)), review_ok(1)]))
        m = new_msgs()
        check(len(rows()) == n_before and sorted(r.id for r in live()) == live_before,
              '失败批 + 产出不足:题库一行不动')
        check(m[-1].title == '题库生成失败' and '1 批生成失败' in (m[-1].content or '')
              and '实际 1/计划 26' in (m[-1].content or '') and '旧题库保持不变' in (m[-1].content or ''),
              f'中止通知:{m[-1].content}')

        # ---- AI 全部无效 → 失败通知 ----
        G.run_generation_job(app, KEY, PAGES, u.id, plan={1: 1}, replace=True, client=FakeClient(['{"questions":[]}']))
        m = new_msgs()
        check(len(rows()) == n_before and m[-1].title == '题库生成失败', f'全部无效:不动题库 + 失败通知 ({m[-1].content})')

        # ---- 早期异常(查课程行就炸)也要发失败通知 ----
        own_query = 'query' in InteractiveCourse.__dict__
        saved = InteractiveCourse.__dict__.get('query')
        class Boom:
            def filter_by(self, **kw): raise RuntimeError('boom-lookup')
        InteractiveCourse.query = Boom()
        try:
            G.run_generation_job(app, KEY, PAGES, u.id, plan={1: 1}, client=FakeClient([]))
        finally:
            if own_query:
                InteractiveCourse.query = saved
            else:
                del InteractiveCourse.query
        m = new_msgs()
        check(m[-1].title == '题库生成失败' and 'boom-lookup' in (m[-1].content or ''),
              f'早期异常:失败通知已写 ({m[-1].content})')

        # ---- 非法 plan:抛错且不抢标记 ----
        try:
            G.start_generation(app, KEY, PAGES, u.id, plan={4: 1})
            check(False, '非法 plan 应抛 ValueError')
        except ValueError:
            s = setting()
            check(s is None or s.generating_since is None, '非法 plan:抛 ValueError 且未设生成标记')

        # ---- 跨进程互斥:标记占用中第二次 start 返回 False;结束后释放 ----
        gate = threading.Event()
        fc = FakeClient([batch(('互斥题一', 1)), review_ok(1)], gate=gate)
        ok1 = G.start_generation(app, KEY, PAGES, u.id, plan={1: 1}, client=fc)
        s = setting()
        check(ok1 and s.generating_since is not None and s.generating_by == u.id and G.is_running(KEY),
              '首次 start_generation 抢到标记(generating_since/by 已写库)')
        check(G.start_generation(app, KEY, PAGES, u.id, plan={1: 1}, client=FakeClient([])) is False,
              '标记未过期 → 第二次 start_generation 返回 False')
        gate.set()
        check(wait_idle() and setting().generating_since is None and setting().generating_by is None,
              '任务结束后标记被清除')
        check(any(r.question == '互斥题一' for r in rows()), '后台线程任务已落库')

        # ---- 心跳:每块调用后刷新 generating_since,令牌不变 ----
        seen = {}

        class HBClient(FakeClient):
            def complete(self, *a, **kw):
                if len(self.calls) == 1:            # 第 2 次调用(复核)前:看出题批之后的心跳
                    row = CourseExamSetting.query.filter_by(course_key=KEY).populate_existing().first()
                    seen.update(since=row.generating_since, token=row.generating_token)
                return super().complete(*a, **kw)
        gate = threading.Event()
        ok_hb = G.start_generation(app, KEY, PAGES, u.id, plan={1: 1},
                                   client=HBClient([batch(('心跳题', 1)), review_ok(1)], gate=gate))
        s = setting()
        token0 = s.generating_token
        check(ok_hb and token0 is not None and s.generating_since == token0, '抢标记时写入令牌 generating_token')
        s.generating_since = get_local_time() - timedelta(minutes=15)      # 模拟单批跑了很久
        db.session.commit()
        check(G.is_running(KEY), f'15 分钟未心跳仍算生成中(< {G.STALE_MINUTES} 分钟)')
        t_mark = get_local_time()
        gate.set()
        check(wait_idle() and seen.get('since') is not None and seen['since'] >= t_mark - timedelta(seconds=1)
              and seen.get('token') == token0, f'出题批之后心跳刷新 since、令牌不变 {seen}')
        check(setting().generating_since is None and setting().generating_token is None, '心跳任务结束后按令牌释放')

        # ---- 过期标记(> STALE_MINUTES 无心跳)可被接管;旧主人的心跳/释放不影响新主人 ----
        old_t = get_local_time() - timedelta(minutes=G.STALE_MINUTES + 1)
        s = setting(); s.generating_since = old_t; s.generating_token = old_t; s.generating_by = u.id
        db.session.commit()
        check(not G.is_running(KEY), '过期标记不算生成中')
        gate2 = threading.Event()
        ok2 = G.start_generation(app, KEY, PAGES, u.id, plan={1: 1},
                                 client=FakeClient([batch(('接管题', 1)), review_ok(1)], gate=gate2))
        new_token = setting().generating_token
        check(ok2 and new_token is not None and new_token != old_t, '过期标记被接管,换新令牌')
        check(G._heartbeat(KEY, old_t) is False and setting().generating_token == new_token,
              '旧令牌心跳无效')
        G._release(KEY, old_t)
        check(setting().generating_token == new_token and G.is_running(KEY), '旧令牌释放不清新主人的标记')
        gate2.set()
        check(wait_idle() and setting().generating_since is None
              and any(r.question == '接管题' for r in rows()), '接管任务完成后释放')
    finally:
        db.session.rollback()
        wait_idle(5)
        CourseQuizQuestion.query.filter_by(course_key=KEY).delete(synchronize_session=False)
        CourseExamSetting.query.filter_by(course_key=KEY).delete(synchronize_session=False)
        ids = [m.id for m in new_msgs()]
        if ids:
            Message.query.filter(Message.id.in_(ids)).delete(synchronize_session=False)
        db.session.commit()
        left = (CourseQuizQuestion.query.filter_by(course_key=KEY).count()
                + CourseExamSetting.query.filter_by(course_key=KEY).count() + len(new_msgs()))
        check(left == 0, f'清理完成,残留 {left} 行')
    print('FAILS:', fails)
    sys.exit(1 if fails else 0)
