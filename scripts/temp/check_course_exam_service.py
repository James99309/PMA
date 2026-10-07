#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""course_exam.service 集成验证(pma_local)。用独立 course_key 'zz-exam-test',结束硬删。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _report_flow_testkit import make_app

KEY = 'zz-exam-test'
PAGES = [{'label': 'p1', 'notes': ''}, {'label': 'p2', 'notes': ''}]   # required = 28s,单页封顶 60s

app = make_app()
with app.app_context():
    from app import db
    from app.models.user import User
    from app.models.course_exam import CourseQuizQuestion, CourseLearningProgress
    from app.services.course_exam import service as S
    u = User.query.filter(User._is_active == True).order_by(User.id).first()   # is_active 是 property,列名 _is_active
    fails = []
    def check(cond, msg):
        print(('OK  ' if cond else 'FAIL') + ' ' + msg)
        if not cond: fails.append(msg)
    try:
        # ---- 阅读 ----
        p = S.record_read(u.id, KEY, PAGES, page=1, seconds=15)
        check(p['read']['percent'] > 0 and not p['read']['unlocked'], '首次上报计时、未解锁')
        S._force_last_ping(u.id, KEY, seconds_ago=16)
        p = S.record_read(u.id, KEY, PAGES, page=1, seconds=999)
        check(p['read']['page_seconds']['1'] == 31 and not p['read']['unlocked'],
              '伪造大秒数按真实间隔截断(15+16=31);只看过一页不解锁')
        p = S.record_read(u.id, KEY, PAGES, page=1, seconds=15)
        check(p['read']['page_seconds']['1'] == 31, '紧接着重复上报(间隔≈0s)不计时')
        S._force_last_ping(u.id, KEY, seconds_ago=16)
        p = S.record_read(u.id, KEY, PAGES, page='abc', seconds=15)
        check(p['read']['page_seconds'] == {'1': 31}, '非法页号忽略')
        S._force_last_ping(u.id, KEY, seconds_ago=16)
        p = S.record_read(u.id, KEY, PAGES, page=2, seconds=15)
        check(p['read']['unlocked'] and p['read']['effective_seconds'] == 46 and p['read']['percent'] == 100,
              '两页都开过且时长达标(46≥28) → 解锁')
        # (Task 8 追加考核段)
    finally:
        db.session.rollback()
        CourseLearningProgress.query.filter_by(course_key=KEY).delete()
        CourseQuizQuestion.query.filter_by(course_key=KEY).delete()
        db.session.commit()
        left = (CourseLearningProgress.query.filter_by(course_key=KEY).count()
                + CourseQuizQuestion.query.filter_by(course_key=KEY).count())
        check(left == 0, f'清理完成,残留 {left} 行')
    print('FAILS:', fails)
    sys.exit(1 if fails else 0)
