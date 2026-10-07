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
