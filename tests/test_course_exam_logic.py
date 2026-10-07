# -*- coding: utf-8 -*-
"""course_exam.logic 纯逻辑单测(无 DB)。"""
import os, sys, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.course_exam import logic as L


def test_points_by_difficulty():
    assert L.POINTS == {1: 1, 2: 2, 3: 3}


def test_apply_score_caps_at_100():
    assert L.apply_score(99, 3) == 100
    assert L.apply_score(10, 2) == 12


def test_pass_and_perfect_flags():
    assert L.crossed(58, 60) == {'passed': True, 'perfect': False}
    assert L.crossed(97, 100) == {'passed': False, 'perfect': True}
    assert L.crossed(55, 100) == {'passed': True, 'perfect': True}
    assert L.crossed(60, 62) == {'passed': False, 'perfect': False}


def test_weights_by_score_band():
    assert L.weights_for(0) == {1: 6, 2: 3, 3: 1}
    assert L.weights_for(30) == {1: 3, 2: 5, 3: 2}
    assert L.weights_for(60) == {1: 1, 2: 4, 3: 5}


def _q(i, d):
    return {'id': i, 'qtype': 'single', 'difficulty': d}


def test_pick_excludes_correct_ids():
    bank = [_q(1, 1), _q(2, 1)]
    rng = random.Random(0)
    for _ in range(20):
        assert L.pick_question(bank, score=0, correct_ids={1}, recent_ids=[], rng=rng)['id'] == 2


def test_pick_respects_wrong_gap():
    # 题 1 刚答错(recent 末尾),池里还有别的题 → 不抽题 1
    bank = [_q(1, 1), _q(2, 1), _q(3, 1)]
    rng = random.Random(1)
    for _ in range(30):
        got = L.pick_question(bank, 0, set(), recent_ids=[1], rng=rng)
        assert got['id'] != 1


def test_pick_gap_relaxes_when_pool_too_small():
    bank = [_q(1, 1)]
    assert L.pick_question(bank, 0, set(), recent_ids=[1], rng=random.Random(0))['id'] == 1


def test_pick_returns_none_when_all_correct():
    assert L.pick_question([_q(1, 1)], 0, {1}, [], random.Random(0)) is None


def test_pick_weight_redistributes_missing_level():
    bank = [_q(1, 3)]  # 只有难题
    assert L.pick_question(bank, 0, set(), [], random.Random(0))['id'] == 1


def test_pick_biases_easy_when_low_score():
    bank = [_q(i, 1) for i in range(50)] + [_q(100 + i, 3) for i in range(50)]
    rng = random.Random(42)
    easy = sum(L.pick_question(bank, 0, set(), [], rng)['difficulty'] == 1 for _ in range(700))
    assert easy > 500   # 期望 6/7 ≈ 600


def test_shuffle_order_is_permutation():
    order = L.shuffle_order(4, random.Random(3))
    assert sorted(order) == [0, 1, 2, 3]


def test_judge_has_no_order():
    assert L.option_order_for({'qtype': 'judge'}, random.Random(0)) is None


def test_to_original_single_and_multi():
    order = [2, 0, 3, 1]          # 显示位 i → 原始下标 order[i]
    assert L.to_original('single', 0, order) == 2
    assert L.to_original('multi', [1, 3], order) == [0, 1]
    assert L.to_original('judge', True, None) is True


def test_to_original_rejects_bad_input():
    import pytest
    with pytest.raises(ValueError):
        L.to_original('single', 9, [0, 1])
    with pytest.raises(ValueError):
        L.to_original('judge', 'yes', None)


def test_is_correct():
    assert L.is_correct({'qtype': 'single', 'answer': 2}, 2)
    assert L.is_correct({'qtype': 'multi', 'answer': [0, 3]}, [3, 0])
    assert not L.is_correct({'qtype': 'multi', 'answer': [0, 3]}, [0])
    assert L.is_correct({'qtype': 'judge', 'answer': False}, False)


def test_page_estimate_and_required():
    pages = [{'notes': ''}, {'notes': 'x' * 500}]
    assert L.page_estimate(pages[0]) == 20          # 下限 20s
    assert L.page_estimate(pages[1]) == 100         # 500 字 / 5
    assert L.required_read_seconds(pages) == 84     # (20+100)*0.7
    assert L.required_read_seconds(pages, override=30) == 30


def test_ping_seconds_clamped_by_wall_clock():
    assert L.accept_ping_seconds(15, elapsed=16) == 15
    assert L.accept_ping_seconds(60, elapsed=16) == 16    # 不加容差,按真实间隔封顶
    assert L.accept_ping_seconds(-3, elapsed=10) == 0
    assert L.accept_ping_seconds(15, elapsed=None) == 15  # 首次上报
    assert L.accept_ping_seconds(500, elapsed=None) == L.MAX_PING_SECONDS


def test_add_page_seconds_caps_per_page():
    pages = [{'notes': ''}, {'notes': ''}]            # 每页估算 20s → 上限 60s
    ps = L.add_page_seconds({}, 1, 50, pages)
    ps = L.add_page_seconds(ps, 1, 50, pages)
    assert ps == {'1': 60}


def test_unlock_needs_time_and_all_pages():
    pages = [{'notes': ''}, {'notes': ''}]            # required = 28
    assert not L.is_unlocked({'1': 60}, pages)        # 第 2 页没开过
    assert L.is_unlocked({'1': 20, '2': 10}, pages)
    assert not L.is_unlocked({'1': 10, '2': 10}, pages)


def test_bank_health():
    qs = [{'difficulty': 3, 'qtype': 'single'}] * 30 + [{'difficulty': 1, 'qtype': 'judge'}] * 5
    h = L.bank_health(qs)
    assert h['total'] == 35 and h['max_score'] == 95 and not h['ok']
    assert h['by_difficulty'] == {1: 5, 2: 0, 3: 30}
    assert h['by_type'] == {'single': 30, 'multi': 0, 'judge': 5}


def test_empirical_difficulty():
    assert L.empirical_difficulty(9, 10) == 1
    assert L.empirical_difficulty(6, 10) == 2
    assert L.empirical_difficulty(3, 10) == 3
    assert L.empirical_difficulty(5, 9) is None               # 样本不足 10
    assert L.suspicious(1, 10) and not L.suspicious(3, 10)


# ---------- 评审修复:输入校验 + 阅读上报防刷 ----------
import math
import pytest


def test_ping_rapid_fire_earns_nothing():
    # C1:高频上报(间隔 0.1s)不得累积时长
    assert sum(L.accept_ping_seconds(15, elapsed=0.1) for _ in range(10)) == 0


def test_ping_rejects_garbage_seconds():
    for bad in ('abc', None, float('nan'), float('inf'), True, False, [1], {}):
        assert L.accept_ping_seconds(bad, elapsed=None) == 0
    assert L.accept_ping_seconds('12', elapsed=None) == 12
    assert L.accept_ping_seconds(15, elapsed=-5) == 0
    assert L.accept_ping_seconds(15, elapsed=7.9) == 7
    assert not hasattr(L, 'PING_TOLERANCE')


def test_required_read_override_zero_and_negative():
    pages = [{'notes': ''}]
    assert L.required_read_seconds(pages, override=0) == 0
    assert L.required_read_seconds(pages, override=-1) == 0


def test_add_page_seconds_clamps_and_normalises_keys():
    pages = [{'notes': ''}, {'notes': ''}]
    assert L.add_page_seconds({}, 1, -10, pages) == {'1': 0}
    assert L.add_page_seconds({1: 5, '1': 3}, 1, 2, pages) == {'1': 10}
    assert L.add_page_seconds({2: 4}, 3, 5, pages) == {'2': 4}       # 越界页忽略但键已规范


def test_record_ping_validates_page():
    pages = [{'notes': ''}, {'notes': ''}]
    assert L.record_ping({}, pages, 1, 15, None) == {'1': 15}
    assert L.record_ping({}, pages, '2', 15, 10) == {'2': 10}
    for bad in (True, 0, 3, 'x', '1.5', None, 1.0):
        before = {'1': 5}
        got = L.record_ping(before, pages, bad, 15, None)
        assert got == {'1': 5} and got is not before
    assert L.record_ping({}, pages, 1, 15, 0.1) == {'1': 0}


def test_unlock_empty_pages_and_stale_keys():
    assert not L.is_unlocked({}, [])
    assert not L.is_unlocked({'1': 1, '99': 1000}, [{'notes': ''}])
    assert L.effective_read_seconds({'1': 1, '99': 1000}, [{'notes': ''}]) == 1
    assert L.effective_read_seconds({'1': 1, '99': 1000}) == 1001


def _raw(**kw):
    q = {'qtype': 'single', 'difficulty': 2, 'options': ['A', 'B', 'C'], 'answer': 1}
    q.update(kw)
    return q


def test_normalize_question_ok():
    q = L.normalize_question(_raw(difficulty='3', answer='2'))
    assert q['difficulty'] == 3 and q['answer'] == 2
    m = L.normalize_question(_raw(qtype='multi', answer=[2, 0, 2]))
    assert m['answer'] == [0, 2]
    j = L.normalize_question({'qtype': 'judge', 'difficulty': 1, 'answer': 'FALSE'})
    assert j['answer'] is False
    assert L.normalize_question({'qtype': 'judge', 'difficulty': 1, 'answer': True})['answer'] is True
    src = _raw(difficulty='2')
    L.normalize_question(src)
    assert src['difficulty'] == '2'                      # 返回副本,不改原 dict


@pytest.mark.parametrize('bad', [
    _raw(qtype='essay'),
    _raw(difficulty=0), _raw(difficulty=4), _raw(difficulty=True), _raw(difficulty='x'),
    _raw(options=['A']), _raw(options=['A', '']), _raw(options='AB'), _raw(options=['A', 3]),
    _raw(answer=3), _raw(answer=-1), _raw(answer=True), _raw(answer='x'), _raw(answer=None),
    _raw(qtype='multi', options=['A', 'B'], answer=[0, 1]),      # multi 至少 3 个选项
    _raw(qtype='multi', answer=[0]),                              # 至少 2 个正确项
    _raw(qtype='multi', answer=[0, 0]),                           # 去重后不足 2
    _raw(qtype='multi', answer=[0, 1, 2]),                        # 不能全选
    _raw(qtype='multi', answer=[0, 5]),
    _raw(qtype='multi', answer=[0, True]),
    _raw(qtype='multi', answer=1),
    {'qtype': 'judge', 'difficulty': 1, 'answer': 'yes'},
    {'qtype': 'judge', 'difficulty': 1, 'answer': 1},
])
def test_normalize_question_rejects(bad):
    with pytest.raises(ValueError):
        L.normalize_question(bad)


def test_is_correct_multi_as_sets():
    assert L.is_correct({'qtype': 'multi', 'answer': [0, 3]}, [3, 0, 3])
    assert not L.is_correct({'qtype': 'multi', 'answer': [0, 3]}, [0, 1])


def test_to_original_validates_qtype_and_order():
    with pytest.raises(ValueError):
        L.to_original('essay', 0, [0, 1])
    with pytest.raises(ValueError):
        L.to_original('single', 0, None)
    with pytest.raises(ValueError):
        L.to_original('single', 0, [0, 0, 1])          # 非排列
    with pytest.raises(ValueError):
        L.to_original('multi', [0, 1], [1, 2, 3])      # 非 range(n) 排列
    with pytest.raises(ValueError):
        L.to_original('single', 0, [0, True])
    with pytest.raises(ValueError):
        L.to_original('single', 0, (1, 0))             # 须为 list
    with pytest.raises(ValueError):
        L.to_original('single', 0, [1, 0], n_options=3)
    assert L.to_original('single', 0, [1, 0], n_options=2) == 1
    assert L.to_original('judge', False, None, n_options=None) is False


def test_pick_excludes_last_even_when_all_recent():
    # 池里每题都在间隔内,仍不立刻重抽最后一题
    bank = [_q(1, 1), _q(2, 1)]
    rng = random.Random(5)
    for _ in range(30):
        assert L.pick_question(bank, 0, set(), recent_ids=[1, 2], rng=rng)['id'] == 1


def test_as_int_rejects_superscript_digits():
    # '²'.isdigit() 为真但 int('²') 抛错 —— 须判为非法而不是抛 ValueError 以外的异常
    assert L._as_int('²') is None
    assert L._as_int(' 12 ') == 12
    assert L.record_ping({}, [{'notes': ''}], '²', 15, None) == {}
    with pytest.raises(ValueError):
        L.normalize_question({'qtype': 'single', 'difficulty': '²', 'options': ['A', 'B'], 'answer': 0})


def test_record_ping_invalid_page_returns_cleaned_dict():
    pages = [{'notes': ''}, {'notes': ''}]
    assert L.record_ping({1: 5, '1': 3, '2': 'x'}, pages, 9, 15, None) == {'1': 8, '2': 0}


def test_norm_page_seconds_is_public():
    assert L.norm_page_seconds({1: 5, '1': 3, '2': -4, '3': 'x'}) == {'1': 8, '2': 0, '3': 0}
    assert L.norm_page_seconds(None) == {}


def test_read_percent_is_min_of_time_and_pages():
    pages = [{'notes': ''}] * 4                         # 每页估算 20s → required = 56
    assert L.read_percent({}, pages) == 0
    assert L.read_percent({'1': 60}, pages) == 25        # 时长早已达标,但只看了 1/4 页
    assert L.read_percent({'1': 5, '2': 5, '3': 5, '4': 5}, pages) == 35   # 页都看过,时长 20/56
    assert L.read_percent({'1': 60, '2': 60, '3': 60, '4': 60}, pages) == 99  # 未解锁前封顶 99
    assert L.read_percent({'1': 10}, []) == 0


def test_quick_flip_counts_as_seen():
    pages = [{'notes': ''}] * 4                         # required = 56
    # 快速翻过 2、3、4 页(0 秒):仍算看过
    ps = L.record_ping({}, pages, 1, 15, None, visited=[2, 3, 4])
    assert ps == {'1': 15, '2': 0, '3': 0, '4': 0}
    assert L.read_percent(ps, pages) == 26               # 页 100%,时长 15/56
    # 时长达标后解锁,不要求每页 >0 秒
    ps = L.record_ping(ps, pages, 1, 20, 20)
    ps = L.record_ping(ps, pages, 1, 20, 20)
    assert ps['1'] == 55 and not L.is_unlocked(ps, pages)
    ps = L.record_ping(ps, pages, 2, 5, 5)
    assert L.is_unlocked(ps, pages)


def test_visited_is_validated():
    pages = [{'notes': ''}] * 3
    ps = L.record_ping({}, pages, 1, 5, None, visited=[2, '3', 0, 9, True, 'x', None, 2.5])
    assert ps == {'1': 5, '2': 0, '3': 0}
    assert L.record_ping({}, pages, 1, 5, None, visited='notalist') == {'1': 5}
    # 已有时长不被 visited 覆盖成 0
    assert L.record_ping({'2': 30}, pages, 1, 5, None, visited=[2]) == {'1': 5, '2': 30}
