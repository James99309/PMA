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


WRONG_GAP = 5


def pick_question(bank, score, correct_ids, recent_ids, rng):
    """从题库抽一题。

    bank: active 题列表;correct_ids: 本人已答对题 id 集合;
    recent_ids: 本人最近作答的题 id(旧→新),最近 WRONG_GAP 题内出现过的不抽(池不足时放宽)。
    """
    pool = [q for q in bank if q['id'] not in correct_ids]
    if not pool:
        return None
    recent = set(recent_ids[-WRONG_GAP:])
    fresh = [q for q in pool if q['id'] not in recent]
    if fresh:
        pool = fresh
    by_d = {1: [], 2: [], 3: []}
    for q in pool:
        by_d[q['difficulty']].append(q)
    w = {d: (wt if by_d[d] else 0) for d, wt in weights_for(score).items()}
    total = sum(w.values())
    r = rng.random() * total
    for d in (1, 2, 3):
        r -= w[d]
        if r <= 0 and by_d[d]:
            return rng.choice(by_d[d])
    for d in (3, 2, 1):           # 浮点兜底
        if by_d[d]:
            return rng.choice(by_d[d])


def shuffle_order(n, rng):
    order = list(range(n))
    rng.shuffle(order)
    return order


def option_order_for(q, rng):
    if q['qtype'] == 'judge':
        return None
    return shuffle_order(len(q['options']), rng)


def to_original(qtype, shown, order):
    """把前端提交的「显示位」换算成原始选项下标。非法输入抛 ValueError。"""
    if qtype == 'judge':
        if not isinstance(shown, bool):
            raise ValueError('judge 答案须为 bool')
        return shown
    def one(i):
        if not isinstance(i, int) or isinstance(i, bool) or not 0 <= i < len(order):
            raise ValueError('选项下标越界')
        return order[i]
    if qtype == 'single':
        return one(shown)
    if not isinstance(shown, list) or not shown:
        raise ValueError('multi 答案须为非空列表')
    return sorted({one(i) for i in shown})


def is_correct(q, original):
    if q['qtype'] == 'multi':
        return sorted(original) == sorted(q['answer'])
    return original == q['answer']
