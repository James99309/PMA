# -*- coding: utf-8 -*-
"""课程考核纯逻辑 —— 零 Flask/DB 依赖,便于单测。

题目在本模块里是 dict:{id, qtype, difficulty, options, answer, ...}
answer:single=int / multi=list[int] / judge=bool(均为「原始选项下标」)。
"""
POINTS = {1: 1, 2: 2, 3: 3}
PASS_SCORE = 60
FULL_SCORE = 100


def apply_score(score, difficulty):
    return min(FULL_SCORE, score + POINTS[difficulty])


def crossed(before, after):
    """本次加分是否跨过及格线 / 满分线。"""
    return {'passed': before < PASS_SCORE <= after,
            'perfect': before < FULL_SCORE <= after}


def weights_for(score):
    if score < 30:
        return {1: 6, 2: 3, 3: 1}
    if score < PASS_SCORE:
        return {1: 3, 2: 5, 3: 2}
    return {1: 1, 2: 4, 3: 5}
