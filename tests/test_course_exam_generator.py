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
    out, stats = G.generate_course(PAGES, plan={1: 1, 2: 1, 3: 1}, client=fc)
    assert len(fc.calls) == 4
    assert [q['status'] for q in out] == ['active', 'active', 'review']
    assert stats == {'requested': 3, 'generated': 3, 'failed_batches': 0, 'review_failed_chunks': 0}


def test_generate_course_chunks_and_passes_existing():
    def batch(start, n):
        items = ','.join('{"type":"single","question":"第%d题 内容%s","options":["a","b","c","d"],"answer":0,"page":1}'
                         % (i, '甲乙丙丁戊己庚辛壬癸'[i % 10] * (i % 7 + 1)) for i in range(start, start + n))
        return '```json\n{"questions":[%s]}\n```' % items
    review = '{"reviews":[' + ','.join('{"index":%d,"difficulty":2,"answer_ok":true}' % i for i in range(40)) + ']}'
    replies = [batch(0, 25), batch(25, 5)] + [review]   # 30 题 → 2 次出题 + 1 次复核
    fc = FakeClient(replies)
    out, stats = G.generate_course(PAGES, plan={2: 30}, client=fc)
    assert len(fc.calls) == 3
    assert '第0题' in fc.calls[1]          # 第二批带上第一批题干防重复
    assert all(q['difficulty'] == 2 for q in out) and out and out[0]['status'] == 'active'


def test_generate_course_review_failure_marks_review():
    batch = '{"questions":[{"type":"judge","question":"总部在上海","answer":true,"page":1}]}'
    fc = FakeClient([batch, 'not json at all'])
    out, stats = G.generate_course(PAGES, plan={1: 1}, client=fc)
    assert out[0]['status'] == 'review' and out[0]['review_note']
    assert stats['review_failed_chunks'] == 1


def test_generate_course_salvages_truncated_review():
    batch = '{"questions":[{"type":"judge","question":"甲","answer":true},{"type":"judge","question":"乙乙乙乙","answer":false}]}'
    trunc = '{"reviews":[{"index":0,"difficulty":1,"answer_ok":true},{"index":1,"diffic'
    out, _ = G.generate_course(PAGES, plan={1: 2}, client=FakeClient([batch, trunc]))
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


def test_generate_course_counts_failed_batches():
    batch = '{"questions":[{"type":"judge","question":"总部在上海","answer":true,"page":1}]}'
    review = '{"reviews":[{"index":0,"difficulty":1,"answer_ok":true}]}'
    out, stats = G.generate_course(PAGES, plan={1: 1, 2: 1}, client=FakeClient([batch, 'garbage', review]))
    assert len(out) == 1 and stats == {'requested': 2, 'generated': 1, 'failed_batches': 1,
                                       'review_failed_chunks': 0}


@pytest.mark.parametrize('plan', [{}, {4: 1}, {0: 1}, {1: -1}, {1: 0}, {1: 'x'}, {1: True},
                                  {1: 200, 2: 101}, None, [1, 2]])
def test_validate_plan_rejects(plan):
    with pytest.raises(ValueError):
        G.validate_plan(plan)


def test_validate_plan_accepts_str_keys():
    assert G.validate_plan({'1': 50, '2': '30', 3: 0}) == {1: 50, 2: 30, 3: 0}
    assert G.validate_plan({1: 100, 2: 100, 3: 100}) == {1: 100, 2: 100, 3: 100}


def test_generate_course_invalid_plan_raises_before_calls():
    fc = FakeClient([])
    with pytest.raises(ValueError):
        G.generate_course(PAGES, plan={9: 1}, client=fc)
    assert fc.calls == []


def test_merge_review_shifts_one_based_index():
    qs = [{'question': '甲题', 'difficulty': 1}, {'question': '乙题', 'difficulty': 2}]
    review = {'reviews': [{'index': 1, 'difficulty': 1, 'answer_ok': True},
                          {'index': 2, 'difficulty': 2, 'answer_ok': True}]}
    assert [q['status'] for q in G.merge_review(qs, review)] == ['active', 'active']


def test_merge_review_echo_prefix_mismatch_is_missing():
    qs = [{'question': '和源通信总部位于哪个城市的哪个区', 'difficulty': 1},
          {'question': '直放站 的作用', 'difficulty': 1}]
    review = {'reviews': [{'index': 0, 'q': '直放站的作用', 'difficulty': 1, 'answer_ok': True},
                          {'index': 1, 'q': '直放站的作用', 'difficulty': 1, 'answer_ok': True}]}
    out = G.merge_review(qs, review)
    assert out[0]['status'] == 'review' and out[0]['ai_difficulty'] is None
    assert out[1]['status'] == 'active'          # 去空白后前缀一致


def test_review_prompt_asks_for_question_echo():
    qs = [{'qtype': 'judge', 'difficulty': 1, 'question': '题干', 'options': None, 'answer': True}]
    assert '"q"' in G.build_review_prompt(PAGES, qs)


def test_batch_prompt_multi_rule_matches_logic():
    p = G.build_batch_prompt(PAGES, 2, 3)
    assert '至少 3 个选项' in p and '不能全选' in p


def test_regenerate_one_falls_back_to_model_page_and_uses_existing():
    fc = FakeClient(['{"questions":[{"type":"single","question":"新题","options":["a","b","c"],"answer":1,"page":2}]}'])
    q = G.regenerate_one(PAGES, {'qtype': 'single', 'difficulty': 1, 'question': '旧题'}, client=fc,
                         existing_questions=['别的已有题'])
    assert q['source_page'] == 2 and '别的已有题' in fc.calls[0]
    fc = FakeClient(['{"questions":[{"type":"single","question":"别的已有题?","options":["a","b"],"answer":1}]}'])
    with pytest.raises(ValueError):
        G.regenerate_one(PAGES, {'qtype': 'single', 'difficulty': 1, 'question': '旧题'}, client=fc,
                         existing_questions=['别的已有题'])


def test_merge_review_echo_ignores_punctuation():
    qs = [{'question': '总部在哪？「和源」', 'difficulty': 1}, {'question': '他说"你好"吗', 'difficulty': 1}]
    review = {'reviews': [{'index': 0, 'q': '总部在哪?"和源"', 'difficulty': 1, 'answer_ok': True},
                          {'index': 1, 'q': '他说「你好」吗', 'difficulty': 1, 'answer_ok': True}]}
    assert [q['status'] for q in G.merge_review(qs, review)] == ['active', 'active']


@pytest.mark.parametrize('stats,abort', [
    ({'requested': 100, 'generated': 30, 'failed_batches': 0, 'review_failed_chunks': 0}, False),  # 课薄但无失败
    ({'requested': 100, 'generated': 30, 'failed_batches': 2, 'review_failed_chunks': 0}, True),
    ({'requested': 100, 'generated': 60, 'failed_batches': 1, 'review_failed_chunks': 0}, False),
])
def test_replace_abort_only_on_failures(stats, abort):
    assert (G.replace_abort_reason(stats) is not None) == abort


def test_replace_abort_reason_text():
    r = G.replace_abort_reason({'requested': 100, 'generated': 30, 'failed_batches': 2, 'review_failed_chunks': 0})
    assert '2 批生成失败' in r and '实际 30/计划 100' in r and '旧题库保持不变' in r


def test_stale_minutes():
    # 每块调用后都有心跳,单次调用最长 600s → 20 分钟无心跳即视为僵死
    assert G.STALE_MINUTES == 20


def test_generate_course_heartbeat_after_every_chunk():
    batch = '{"questions":[{"type":"judge","question":"总部在上海","answer":true,"page":1}]}'
    review = '{"reviews":[{"index":0,"difficulty":1,"answer_ok":true}]}'
    beats = []
    G.generate_course(PAGES, plan={1: 1, 2: 1}, client=FakeClient([batch, 'garbage', review]),
                      on_progress=lambda: beats.append(1))
    assert len(beats) == 3          # 2 批出题(含失败批)+ 1 组复核
