#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""course_exam.service 集成验证(pma_local)。用独立 course_key 'zz-exam-test',结束硬删。"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _report_flow_testkit import make_app

KEY = 'zz-exam-test'
LEGACY_KEY = 'zz-exam-test-legacy'     # 旧题库导入用独立课,避免干扰上面的抽题池
PAGES = [{'label': 'p1', 'notes': ''}, {'label': 'p2', 'notes': ''}]   # 估算 required = 28s,单页封顶 60s
OVERRIDE = 40                          # course_exam_settings 覆盖值

app = make_app()
with app.app_context():
    from app import db
    from app.models.user import User
    from app.models.course_exam import (CourseQuizQuestion, CourseLearningProgress,
                                         CourseExamSetting, LearningBuddyPref)
    from app.models.training import TrainingQuizAttempt, get_local_time
    from app.services.course_exam import service as S
    from app.services.course_exam import logic as L

    def force_last_ping(user_id, course_key, seconds_ago):
        """把上次上报时间往前拨,模拟真实间隔。"""
        from datetime import timedelta
        pr = S.get_progress(user_id, course_key)
        pr.last_ping_at = get_local_time() - timedelta(seconds=seconds_ago)
        db.session.commit()

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
    buddy_pre = db.session.get(LearningBuddyPref, u.id)   # 新表,应无真实行;有则跳过开关测试以免改真实数据
    try:
        # ---- 只读路径不插行 ----
        rs = S.read_status(u.id, KEY, PAGES)
        check(S.get_progress(u.id, KEY) is None and rs['read']['percent'] == 0
              and rs['read']['required_seconds'] == 28 and rs['exam']['score'] == 0,
              '只读概览:无进度行返回空进度、不插行、按估算 28s')
        # ---- 课程设置覆盖阅读时长 ----
        db.session.add(CourseExamSetting(course_key=KEY, min_read_seconds=OVERRIDE, updated_by=u.id))
        db.session.commit()
        check(S.get_min_read_seconds(KEY) == OVERRIDE and S.get_min_read_seconds(KEY + '-none') is None,
              'get_min_read_seconds:有行取值 / 无行 None')
        # ---- 阅读 ----
        p = S.record_read(u.id, KEY, PAGES, page=1, seconds=15)
        check(p['read']['percent'] > 0 and not p['read']['unlocked'] and p['read']['required_seconds'] == OVERRIDE,
              '首次上报计时、未解锁、所需时长取课程设置')
        force_last_ping(u.id, KEY, seconds_ago=16)
        p = S.record_read(u.id, KEY, PAGES, page=1, seconds=999)
        check(p['read']['page_seconds']['1'] == 31 and not p['read']['unlocked'],
              '伪造大秒数按真实间隔截断(15+16=31);只看过一页不解锁')
        p = S.record_read(u.id, KEY, PAGES, page=1, seconds=15)
        check(p['read']['page_seconds']['1'] == 31, '紧接着重复上报(间隔≈0s)不计时')
        force_last_ping(u.id, KEY, seconds_ago=16)
        p = S.record_read(u.id, KEY, PAGES, page='abc', seconds=15)
        check(p['read']['page_seconds'] == {'1': 31}, '非法页号忽略')
        force_last_ping(u.id, KEY, seconds_ago=16)
        p = S.record_read(u.id, KEY, PAGES, page=2, seconds=15)
        check(p['read']['unlocked'] and p['read']['effective_seconds'] == 46 and p['read']['percent'] == 100,
              '两页都开过且时长达标(46≥40) → 解锁')
        # ---- _create_progress:非唯一冲突(外键违例)要原样抛出 ----
        from sqlalchemy.exc import IntegrityError
        try:
            S._create_progress(-999999, KEY)
            raised = False
        except IntegrityError:
            raised = True
        db.session.rollback()
        check(raised, '_create_progress 重查不到时抛原始 IntegrityError')
        # ---- 小源开关 ----
        if buddy_pre is None:
            check(S.buddy_enabled(u.id) is True, '小源开关:无行默认开启')
            S.set_buddy_enabled(u.id, False)
            off = S.buddy_enabled(u.id)
            S.set_buddy_enabled(u.id, True)
            check(off is False and S.buddy_enabled(u.id) is True, '小源开关:关闭/重新开启落库')
        else:
            print('SKIP 小源开关(该用户已有真实偏好行)')
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
        prog = S.get_progress(u.id, KEY)
        right_shown = prog.current_option_order.index(0)          # 原始答案 0 显示在哪
        r = S.submit_answer(u.id, KEY, 99)
        check(r == {'error': 'bad_answer'} and S.current_question(u.id, KEY)['question']['id'] == q.id,
              '越界提交被拒且不清断点(不能借乱填跳题)')
        r = S.submit_answer(u.id, KEY, right_shown)
        check(r['correct'] and r['score'] == L.POINTS[q.difficulty] and r['correct_answer'] == right_shown,
              '答对按难度加分,回显正确显示位')
        r2 = S.submit_answer(u.id, KEY, right_shown)
        check(r2 == {'error': 'already_answered'} and S.get_progress(u.id, KEY).score == r['score'],
              '重复提交被拒(不重复加分)')
        c3 = S.current_question(u.id, KEY)
        check(c3['answered'] and c3['result']['correct'] and c3['question']['id'] == q.id,
              '提交后未点下一题 → 再打开看到结果')
        # 已作答后题目被改(选项变 3 个)→ 不按旧顺序索引,展示作答时的题面快照
        q.options = ['a', 'b', 'c']
        db.session.commit()
        c3b = S.current_question(u.id, KEY)
        check(c3b['answered'] and c3b['question'] == c1['question'] and c3b['result']['correct'],
              '已作答题被改 → 不报错,按作答时快照展示')
        att = TrainingQuizAttempt.query.filter_by(user_id=u.id, course_slug=KEY, module_slug='bank').first()
        check(json.loads(att.user_answer) == 0 and json.loads(att.correct_answer) == 0,
              '留痕答案为 JSON(原始下标)')
        c4 = S.next_question(u.id, KEY)
        check(c4['question']['id'] != q.id and not c4['answered'], '答对的题移出抽题池')
        n_att = TrainingQuizAttempt.query.filter_by(user_id=u.id, course_slug=KEY, module_slug='bank').count()
        check(n_att == 1, '逐题留痕写入 training_quiz_attempt(仅有效提交)')
        # 未作答时题目被改成 3 个选项 → 直接打开(不提交)也不报错,重新抽且题面一致
        q4 = db.session.get(CourseQuizQuestion, c4['question']['id'])
        q4.options = ['a', 'b', 'c']
        db.session.commit()
        c4b = S.current_question(u.id, KEY)
        q4b = db.session.get(CourseQuizQuestion, c4b['question']['id'])
        pr = S.get_progress(u.id, KEY)
        check(not c4b['answered'] and len(c4b['question']['options']) == len(q4b.options)
              and len(pr.current_option_order) == len(q4b.options),
              '未作答题被改 → 打开即重新抽,选项顺序与题面一致')
        # 未作答时题目被改 → 提交报 stale_question 且断点作废
        q4b.options = list(q4b.options) + ['zz']
        db.session.commit()
        r = S.submit_answer(u.id, KEY, 0)
        prog = S.get_progress(u.id, KEY)
        check(r == {'error': 'stale_question'} and prog.current_question_id is None,
              '题目改动后提交 → stale_question + 清断点')
        c5 = S.current_question(u.id, KEY)
        check('question' in c5 and not c5['answered'] and c5['question']['id'] != q.id
              and len(c5['question']['options']) == len(db.session.get(CourseQuizQuestion, c5['question']['id']).options),
              '清断点后重新抽题,选项顺序与当前题面一致')
        # multi 题回显:正确显示位 = 原始正确项在乱序中的位置
        prog = S.get_progress(u.id, KEY)
        S._clear_current(prog)
        for x in CourseQuizQuestion.query.filter_by(course_key=KEY, status='active').all():
            x.status = 'disabled'
        mq = add_q(qtype='multi', difficulty=2, question='M', options=['a', 'b', 'c', 'd'], answer=[1, 3])
        db.session.commit()
        cm = S.current_question(u.id, KEY)
        prog = S.get_progress(u.id, KEY)
        shown = sorted(prog.current_option_order.index(i) for i in [1, 3])
        before = prog.score
        rm = S.submit_answer(u.id, KEY, [shown[1], shown[0], shown[0]])     # 乱序 + 重复
        check(cm['question']['id'] == mq.id and rm['correct'] and rm['correct_answer'] == shown
              and rm['score'] == before + 2, 'multi 题乱序判分 + 回显正确显示位')
        check(rm['your_answer'] == shown and S.get_progress(u.id, KEY).current_result['your_answer'] == shown,
              'your_answer 存规范化显示位(去重排序)')
        S.next_question(u.id, KEY)
        check(S.current_question(u.id, KEY).get('exhausted'), '题库答完 → exhausted')
        # 满分后无题可抽
        prog = S.get_progress(u.id, KEY); prog.score = 100; prog.perfect_at = get_local_time(); db.session.commit()
        check(S.current_question(u.id, KEY).get('done'), '满分后 done=True')

        # ---- 旧 quiz.json 导入 ----
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, LEGACY_KEY + '.quiz.json'), 'w', encoding='utf-8') as f:
                json.dump({'questions': [
                    {'type': 'single', 'question': 'LS', 'options': ['a', 'b', 'c', 'd'], 'answer': 2, 'explain': 'x'},
                    {'type': 'judge', 'question': 'LJ', 'answer': False, 'explain': 123},       # 非字符串解析 → str
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
              and rows[1].answer is False and rows[1].options is None and rows[1].explain == '123',
              '答案/选项按原始下标原样入库,explain 转字符串')
    finally:
        db.session.rollback()
        CourseLearningProgress.query.filter_by(course_key=KEY).delete()
        TrainingQuizAttempt.query.filter_by(course_slug=KEY, module_slug='bank').delete()
        CourseQuizQuestion.query.filter(CourseQuizQuestion.course_key.in_([KEY, LEGACY_KEY])).delete(
            synchronize_session=False)
        CourseExamSetting.query.filter(CourseExamSetting.course_key.like('zz-exam-test%')).delete(
            synchronize_session=False)
        if buddy_pre is None:
            LearningBuddyPref.query.filter_by(user_id=u.id).delete()
        db.session.commit()
        left = (CourseLearningProgress.query.filter(CourseLearningProgress.course_key.like('zz-exam-test%')).count()
                + TrainingQuizAttempt.query.filter(TrainingQuizAttempt.course_slug.like('zz-exam-test%')).count()
                + CourseQuizQuestion.query.filter(CourseQuizQuestion.course_key.like('zz-exam-test%')).count()
                + CourseExamSetting.query.filter(CourseExamSetting.course_key.like('zz-exam-test%')).count()
                + (LearningBuddyPref.query.filter_by(user_id=u.id).count() if buddy_pre is None else 0))
        check(left == 0, f'清理完成,残留 {left} 行')
    print('FAILS:', fails)
    sys.exit(1 if fails else 0)
