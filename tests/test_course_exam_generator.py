# -*- coding: utf-8 -*-
"""course_exam.generator 离线单测:AI 调用用假 client 注入,不连网、不连库。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
from app.services.course_exam import generator as G

PAGES = [{'label': '公司', 'notes': '总部在上海'}, {'label': '产品', 'notes': '直放站与对讲机'}]


class FakeClient:
    def __init__(self, replies): self.replies = list(replies); self.calls = []; self.closed = False
    def complete(self, system, user, model, max_tokens=16000, temperature=None):
        self.calls.append(user)
        class R: pass
        r = R(); r.text = self.replies.pop(0); return r
    def close(self): self.closed = True


def test_normalize_filters_type_constraints():
    raw = {'questions': [
        {'type': 'judge', 'question': '判断', 'answer': True, 'page': 1},            # 易 judge ok
        {'type': 'multi', 'question': '多选', 'options': ['a', 'b', 'c'], 'answer': [0, 1], 'page': 2},
        {'type': 'single', 'question': '单选', 'options': ['a', 'b'], 'answer': 5},   # 越界丢弃
    ]}
    got = G.normalize(raw, difficulty=1)
    assert [q['qtype'] for q in got] == ['judge']        # 易档不允许 multi


def test_normalize_output_fields_and_page_range():
    raw = {'questions': [
        {'type': 'single', 'question': ' 单选 ', 'options': ['a', 'b', 'c', 'd'], 'answer': '2',
         'explain': '因为', 'page': 2},
        {'type': 'multi', 'question': '多选', 'options': ['a', 'b', 'c', 'd'], 'answer': [3, 1, 1], 'page': 9},
        {'type': 'judge', 'question': '判断', 'answer': True},          # 难档不允许 judge
        {'type': 'single', 'question': '', 'options': ['a', 'b'], 'answer': 0},   # 空题干
        'garbage',
    ]}
    got = G.normalize(raw, difficulty=3, n_pages=2)
    assert len(got) == 2
    assert got[0] == {'qtype': 'single', 'difficulty': 3, 'question': '单选', 'options': ['a', 'b', 'c', 'd'],
                      'answer': 2, 'explain': '因为', 'source_page': 2}
    assert got[1]['answer'] == [1, 3] and got[1]['source_page'] is None and got[1]['explain'] == ''


def test_dedupe_similar_questions():
    qs = [{'question': '和源通信总部位于哪个城市？'}, {'question': '和源通信的总部位于哪个城市'},
          {'question': '直放站的作用是什么'}]
    assert len(G.dedupe(qs)) == 2


def test_dedupe_against_existing():
    qs = [{'question': '直放站的作用是什么？'}, {'question': '对讲机的频段'}]
    assert [q['question'] for q in G.dedupe(qs, existing=['直放站的作用是什么'])] == ['对讲机的频段']


def test_merge_review_marks_disagreement():
    qs = [{'question': 'a', 'difficulty': 1}, {'question': 'b', 'difficulty': 3}]
    review = {'reviews': [{'index': 0, 'difficulty': 1, 'answer_ok': True},
                          {'index': 1, 'difficulty': 1, 'answer_ok': True}]}
    out = G.merge_review(qs, review)
    assert out[0]['status'] == 'active' and out[0]['ai_difficulty'] == 1
    assert out[1]['status'] == 'review'


def test_merge_review_missing_and_doubtful():
    qs = [{'question': 'a', 'difficulty': 2}, {'question': 'b', 'difficulty': 2}]
    out = G.merge_review(qs, {'reviews': [{'index': 0, 'difficulty': 2, 'answer_ok': False, 'note': '两个选项都对'}]})
    assert out[0]['status'] == 'review' and '两个选项都对' in out[0]['review_note']
    assert out[1]['status'] == 'review' and out[1]['ai_difficulty'] is None and out[1]['review_note']


def test_review_prompt_hides_difficulty():
    qs = [{'qtype': 'single', 'difficulty': 3, 'question': '题干X', 'options': ['a', 'b'], 'answer': 1,
           'explain': '', 'source_page': 1}]
    p = G.build_review_prompt(PAGES, qs)
    assert '题干X' in p and '"difficulty": 3' not in p and '难度:3' not in p


def test_batch_prompt_only_own_level_and_existing():
    p = G.build_batch_prompt(PAGES, 1, 5, ['已有题干甲'])
    assert G.DIFF_RULES[1] in p and G.DIFF_RULES[3] not in p
    assert '已有题干甲' in p and '多选' not in p and '"multi"' not in p


def test_generate_course_runs_three_batches_then_review():
    batch = '{"questions":[{"type":"single","question":"Q%d","options":["a","b","c","d"],"answer":0,"explain":"e","page":1}]}'
    replies = [batch % 1, batch % 2, batch % 3,
               '{"reviews":[{"index":0,"difficulty":1,"answer_ok":true},{"index":1,"difficulty":2,"answer_ok":true},{"index":2,"difficulty":3,"answer_ok":false,"note":"答案存疑"}]}']
    fc = FakeClient(replies)
    out = G.generate_course(PAGES, plan={1: 1, 2: 1, 3: 1}, client=fc)
    assert len(fc.calls) == 4
    assert [q['status'] for q in out] == ['active', 'active', 'review']


def test_generate_course_chunks_and_passes_existing():
    def batch(start, n):
        items = ','.join('{"type":"single","question":"第%d题 内容%s","options":["a","b","c","d"],"answer":0,"page":1}'
                         % (i, '甲乙丙丁戊己庚辛壬癸'[i % 10] * (i % 7 + 1)) for i in range(start, start + n))
        return '```json\n{"questions":[%s]}\n```' % items
    review = '{"reviews":[' + ','.join('{"index":%d,"difficulty":2,"answer_ok":true}' % i for i in range(40)) + ']}'
    replies = [batch(0, 25), batch(25, 5)] + [review]   # 30 题 → 2 次出题 + 1 次复核
    fc = FakeClient(replies)
    out = G.generate_course(PAGES, plan={2: 30}, client=fc)
    assert len(fc.calls) == 3
    assert '第0题' in fc.calls[1]          # 第二批带上第一批题干防重复
    assert all(q['difficulty'] == 2 for q in out) and out and out[0]['status'] == 'active'


def test_generate_course_review_failure_marks_review():
    batch = '{"questions":[{"type":"judge","question":"总部在上海","answer":true,"page":1}]}'
    fc = FakeClient([batch, 'not json at all'])
    out = G.generate_course(PAGES, plan={1: 1}, client=fc)
    assert out[0]['status'] == 'review' and out[0]['review_note']


def test_generate_course_salvages_truncated_review():
    batch = '{"questions":[{"type":"judge","question":"甲","answer":true},{"type":"judge","question":"乙乙乙乙","answer":false}]}'
    trunc = '{"reviews":[{"index":0,"difficulty":1,"answer_ok":true},{"index":1,"diffic'
    out = G.generate_course(PAGES, plan={1: 2}, client=FakeClient([batch, trunc]))
    assert [q['status'] for q in out] == ['active', 'review']


def test_generate_course_all_empty_raises():
    with pytest.raises(ValueError):
        G.generate_course(PAGES, plan={1: 1}, client=FakeClient(['{"questions":[]}']))


def test_regenerate_one_keeps_difficulty_and_page():
    fc = FakeClient(['{"questions":[{"type":"single","question":"新题","options":["a","b","c"],"answer":1,"page":1}]}'])
    old = {'qtype': 'judge', 'difficulty': 2, 'question': '旧题干', 'source_page': 2}
    q = G.regenerate_one(PAGES, old, client=fc)
    assert q['difficulty'] == 2 and q['source_page'] == 2 and q['question'] == '新题'
    assert '旧题干' in fc.calls[0]
    with pytest.raises(ValueError):
        G.regenerate_one(PAGES, old, client=FakeClient(['{"questions":[]}']))
