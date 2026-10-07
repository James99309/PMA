#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""course_exam.generator.run_generation_job 集成验证(pma_local)。

假 client 注入,不调真实 AI;独立 course_key 'zz-exam-gen-test',结束硬删题目与本次站内通知。
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _report_flow_testkit import make_app

KEY = 'zz-exam-gen-test'
PAGES = [{'label': '公司', 'notes': '总部在上海'}, {'label': '产品', 'notes': '直放站与对讲机'}]


class FakeClient:
    def __init__(self, replies): self.replies = list(replies); self.calls = 0
    def complete(self, system, user, model, max_tokens=16000, temperature=None):
        self.calls += 1
        class R: pass
        r = R(); r.text = self.replies.pop(0); return r
    def close(self): pass


def batch(*qs):
    items = ','.join('{"type":"single","question":"%s","options":["a","b","c","d"],"answer":1,"explain":"e","page":%d}'
                     % (q, p) for q, p in qs)
    return '{"questions":[%s]}' % items


REVIEW_OK_2 = '{"reviews":[{"index":0,"difficulty":1,"answer_ok":true},{"index":1,"difficulty":2,"answer_ok":false,"note":"答案存疑"}]}'

app = make_app()
with app.app_context():
    from app import db
    from app.models.user import User
    from app.models.message import Message
    from app.models.course_exam import CourseQuizQuestion
    from app.services.course_exam import generator as G

    u = User.query.filter(User._is_active == True).order_by(User.id).first()
    msg_ids_before = {m.id for m in Message.query.filter_by(recipient_id=u.id, message_type='course_bank_ready').all()}
    fails = []
    def check(cond, msg):
        print(('OK  ' if cond else 'FAIL') + ' ' + msg)
        if not cond: fails.append(msg)
    def new_msgs():
        return Message.query.filter(Message.recipient_id == u.id, Message.message_type == 'course_bank_ready',
                                    ~Message.id.in_(msg_ids_before or [-1])).order_by(Message.id).all()
    def rows():
        db.session.expire_all()
        return CourseQuizQuestion.query.filter_by(course_key=KEY).order_by(CourseQuizQuestion.id).all()
    try:
        # ---- 第一次生成:易 1 + 中 1 → 1 active / 1 review ----
        fc = FakeClient([batch(('总部在哪个城市', 1)), batch(('直放站与对讲机的区别在于何处', 2)), REVIEW_OK_2])
        G.run_generation_job(app, KEY, PAGES, u.id, plan={1: 1, 2: 1}, client=fc)
        r1 = rows()
        check(fc.calls == 3 and len(r1) == 2, f'首次生成入库 2 题,AI 调用 3 次 (calls={fc.calls}, rows={len(r1)})')
        check([r.status for r in r1] == ['active', 'review'] and all(r.origin == 'ai' and r.created_by == u.id for r in r1),
              "复核结果落库:active/review,origin='ai',created_by=当前用户")
        check(r1[0].ai_difficulty == 1 and r1[1].review_note and '答案存疑' in r1[1].review_note
              and r1[0].source_page == 1 and r1[0].answer == 1 and r1[0].options == ['a', 'b', 'c', 'd'],
              'ai_difficulty / review_note / source_page / 答案选项落库正确')
        m = new_msgs()
        check(len(m) == 1 and m[0].title == '题库生成完成' and '启用 1 题,待审 1 题' in (m[0].content or '')
              and m[0].sender_id == u.id and m[0].related_object_type == 'course',
              f'站内通知:{m[0].title if m else None} / {m[0].content if m else None}')

        # ---- 追加生成(replace=False):已有题干进防重复提示,相似题被去重 ----
        fc = FakeClient([batch(('总部在哪一个城市？', 1), ('对讲机用于哪类场景', 2)),
                         '{"reviews":[{"index":0,"difficulty":1,"answer_ok":true}]}'])
        G.run_generation_job(app, KEY, PAGES, u.id, plan={1: 2}, client=fc)
        r2 = rows()
        check(len(r2) == 3 and r2[-1].question == '对讲机用于哪类场景' and all(r.status != 'disabled' for r in r2),
              f'追加生成:与已有题相似的被去重,旧题不动 (rows={len(r2)})')

        # ---- 重新生成(replace=True):旧 AI 题全部停用,新题入库 ----
        fc = FakeClient([batch(('新题一', 1)), '{"reviews":[{"index":0,"difficulty":1,"answer_ok":true}]}'])
        G.run_generation_job(app, KEY, PAGES, u.id, plan={1: 1}, replace=True, client=fc)
        r3 = rows()
        live = [r for r in r3 if r.status != 'disabled']
        check(len(r3) == 4 and len(live) == 1 and live[0].question == '新题一',
              f'replace=True:旧 3 题停用,新 1 题启用 (rows={len(r3)}, live={len(live)})')

        # ---- 失败路径:AI 全部无效 → 不动题库,发失败通知 ----
        G.run_generation_job(app, KEY, PAGES, u.id, plan={1: 1}, replace=True,
                             client=FakeClient(['{"questions":[]}']))
        r4 = rows()
        m = new_msgs()
        check(len(r4) == 4 and len([r for r in r4 if r.status != 'disabled']) == 1,
              '失败时 replace 不生效(事务回滚,旧题保持)')
        check(len(m) == 4 and m[-1].title == '题库生成失败', f'失败通知:{m[-1].title if m else None} / {m[-1].content if m else None}')

        # ---- 并发保护 ----
        G._RUNNING.add(KEY)
        check(G.start_generation(app, KEY, PAGES, u.id) is False and G.is_running(KEY), '同课生成中 → start_generation 返回 False')
        G._RUNNING.discard(KEY)
    finally:
        db.session.rollback()
        CourseQuizQuestion.query.filter_by(course_key=KEY).delete(synchronize_session=False)
        ids = [m.id for m in new_msgs()]
        if ids:
            Message.query.filter(Message.id.in_(ids)).delete(synchronize_session=False)
        db.session.commit()
        left = CourseQuizQuestion.query.filter_by(course_key=KEY).count() + len(new_msgs())
        check(left == 0, f'清理完成,残留 {left} 行')
    print('FAILS:', fails)
    sys.exit(1 if fails else 0)
