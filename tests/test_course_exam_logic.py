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
    assert L.accept_ping_seconds(60, elapsed=16) == 18    # elapsed + 2s 容差
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
