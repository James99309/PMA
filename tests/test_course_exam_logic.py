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
