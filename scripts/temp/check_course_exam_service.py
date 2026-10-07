#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""course_exam.service 集成验证(pma_local)。用独立 course_key 'zz-exam-test',结束硬删。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _report_flow_testkit import make_app

KEY = 'zz-exam-test'
LEGACY_KEY = 'zz-exam-test-legacy'     # 旧题库导入用独立课,避免干扰上面的抽题池
PAGES = [{'label': 'p1', 'notes': ''}, {'label': 'p2', 'notes': ''}]   # required = 28s,单页封顶 60s

app = make_app()
with app.app_context():
    from app import db
    from app.models.user import User
    from app.models.course_exam import CourseQuizQuestion, CourseLearningProgress
    from app.models.training import TrainingQuizAttempt, get_local_time
    from app.services.course_exam import service as S
    from app.services.course_exam import logic as L

    def add_q(**kw):
        # 夹具也走 normalize_question,与正式写库路径一致
        n = L.normalize_question(kw)
        q = CourseQuizQuestion(course_key=KEY, qtype=n['qtype'], difficulty=n['difficulty'],
                               options=n.get('options'), answer=n['answer'],
                               question=kw['question'], explain=kw.get('explain'),
                               status=kw.get('status', 'active'))
        db.session.add(q)
        return q
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
        # ---- 行锁:另一连接持锁时,写路径必须等锁(这里用 lock_timeout 让它快速失败) ----
        from sqlalchemy import text
        from sqlalchemy.exc import OperationalError
        other = db.engine.connect()
        tx = other.begin()
        other.execute(text("select id from course_learning_progress where user_id=:u and course_key=:k for update"),
                      {'u': u.id, 'k': KEY})
        db.session.execute(text("set local lock_timeout = '300ms'"))
        try:
            S.record_read(u.id, KEY, PAGES, page=1, seconds=5)
            blocked = False
        except OperationalError:
            blocked = True
        db.session.rollback()
        tx.rollback(); other.close()
        check(blocked, '写路径对进度行加 FOR UPDATE 锁')

        # ---- 考核 ----
        for i, d in enumerate([1, 1, 2, 3], 1):
            add_q(qtype='single', difficulty=d, question=f'Q{i}', options=['a', 'b', 'c', 'd'],
                  answer=0, explain='e')
        add_q(qtype='judge', difficulty=1, question='J', answer=True, status='review')  # 待审题不进池
        db.session.commit()
        c1 = S.current_question(u.id, KEY)
        c2 = S.current_question(u.id, KEY)
        check(c1['question']['id'] == c2['question']['id'] and c1['question']['options'] == c2['question']['options'],
              '断点幂等:同题同选项顺序')
        check('answer' not in c1['question'] and 'explain' not in c1['question'], '当前题不泄露答案/解析')
        check(c1['question']['question'] != 'J', '待审题不出')
        q = db.session.get(CourseQuizQuestion, c1['question']['id'])
        prog = S.get_or_create_progress(u.id, KEY)
        right_shown = prog.current_option_order.index(0)          # 原始答案 0 显示在哪
        r = S.submit_answer(u.id, KEY, 99)
        check(r.get('error') == 'bad_answer' and S.current_question(u.id, KEY)['question']['id'] == q.id,
              '越界提交被拒且不清断点(不能借乱填跳题)')
        r = S.submit_answer(u.id, KEY, right_shown)
        check(r['correct'] and r['score'] == L.POINTS[q.difficulty] and r['correct_answer'] == right_shown,
              '答对按难度加分,回显正确显示位')
        r2 = S.submit_answer(u.id, KEY, right_shown)
        check(r2.get('error') == 'already_answered' and S.get_or_create_progress(u.id, KEY).score == r['score'],
              '重复提交被拒(不重复加分)')
        c3 = S.current_question(u.id, KEY)
        check(c3['answered'] and c3['result']['correct'] and c3['question']['id'] == q.id,
              '提交后未点下一题 → 再打开看到结果')
        c4 = S.next_question(u.id, KEY)
        check(c4['question']['id'] != q.id and not c4['answered'], '答对的题移出抽题池')
        n_att = TrainingQuizAttempt.query.filter_by(user_id=u.id, course_slug=KEY, module_slug='bank').count()
        check(n_att == 1, '逐题留痕写入 training_quiz_attempt(仅有效提交)')
        # 作答中题目被改成 3 个选项 → 提交报 bad_answer 且断点作废、重新抽
        q4 = db.session.get(CourseQuizQuestion, c4['question']['id'])
        q4.options = ['a', 'b', 'c']
        db.session.commit()
        r = S.submit_answer(u.id, KEY, 0)
        prog = S.get_or_create_progress(u.id, KEY)
        check(r.get('error') == 'bad_answer' and prog.current_question_id is None, '题目改动后提交 → bad_answer + 清断点')
        c5 = S.current_question(u.id, KEY)
        check('question' in c5 and not c5['answered'] and c5['question']['id'] != q.id
              and len(c5['question']['options']) == len(db.session.get(CourseQuizQuestion, c5['question']['id']).options),
              '清断点后重新抽题,选项顺序与当前题面一致')
        # multi 题回显:正确显示位 = 原始正确项在乱序中的位置
        prog = S.get_or_create_progress(u.id, KEY)
        S._clear_current(prog)
        for x in CourseQuizQuestion.query.filter_by(course_key=KEY, status='active').all():
            x.status = 'disabled'
        mq = add_q(qtype='multi', difficulty=2, question='M', options=['a', 'b', 'c', 'd'], answer=[1, 3])
        db.session.commit()
        cm = S.current_question(u.id, KEY)
        prog = S.get_or_create_progress(u.id, KEY)
        shown = sorted(prog.current_option_order.index(i) for i in [1, 3])
        before = prog.score
        rm = S.submit_answer(u.id, KEY, list(reversed(shown)))
        check(cm['question']['id'] == mq.id and rm['correct'] and rm['correct_answer'] == shown
              and rm['score'] == before + 2, 'multi 题乱序判分 + 回显正确显示位')
        S.next_question(u.id, KEY)
        check(S.current_question(u.id, KEY).get('exhausted'), '题库答完 → exhausted')
        # 满分后无题可抽
        prog = S.get_or_create_progress(u.id, KEY); prog.score = 100; prog.perfect_at = get_local_time(); db.session.commit()
        check(S.current_question(u.id, KEY).get('done'), '满分后 done=True')

        # ---- 旧 quiz.json 导入 ----
        import json, tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, LEGACY_KEY + '.quiz.json'), 'w', encoding='utf-8') as f:
                json.dump({'questions': [
                    {'type': 'single', 'question': 'LS', 'options': ['a', 'b', 'c', 'd'], 'answer': 2, 'explain': 'x'},
                    {'type': 'judge', 'question': 'LJ', 'answer': False, 'explain': 'y'},
                    {'type': 'single', 'question': 'BAD', 'options': ['a', 'b'], 'answer': 5},   # 下标越界 → 跳过
                    {'type': 'scenario', 'question': 'SC'},                                       # 不支持题型 → 跳过
                ]}, f, ensure_ascii=False)
            n1 = S.import_legacy_json(LEGACY_KEY, tmpdir)
            n2 = S.import_legacy_json(LEGACY_KEY, tmpdir)
            check(S.import_legacy_json(KEY + '-nofile', tmpdir) == 0, '无 quiz.json → 导入 0')
        rows = CourseQuizQuestion.query.filter_by(course_key=LEGACY_KEY).order_by(CourseQuizQuestion.id).all()
        check(n1 == 2 and n2 == 0 and len(rows) == 2, f'只导入合法的 2 道且不重复导入 (n1={n1}, n2={n2})')
        check(all(r.origin == 'legacy' and r.difficulty == 2 and r.status == 'active' for r in rows),
              "origin='legacy'、difficulty=2、active")
        check(rows[0].answer == 2 and rows[0].options == ['a', 'b', 'c', 'd']
              and rows[1].answer is False and rows[1].options is None, '答案/选项按原始下标原样入库')
    finally:
        db.session.rollback()
        CourseLearningProgress.query.filter_by(course_key=KEY).delete()
        TrainingQuizAttempt.query.filter_by(course_slug=KEY, module_slug='bank').delete()
        CourseQuizQuestion.query.filter(CourseQuizQuestion.course_key.in_([KEY, LEGACY_KEY])).delete(
            synchronize_session=False)
        db.session.commit()
        left = (CourseLearningProgress.query.filter(CourseLearningProgress.course_key.like('zz-exam-test%')).count()
                + TrainingQuizAttempt.query.filter(TrainingQuizAttempt.course_slug.like('zz-exam-test%')).count()
                + CourseQuizQuestion.query.filter(CourseQuizQuestion.course_key.like('zz-exam-test%')).count())
        check(left == 0, f'清理完成,残留 {left} 行')
    print('FAILS:', fails)
    sys.exit(1 if fails else 0)
