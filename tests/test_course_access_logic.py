# -*- coding: utf-8 -*-
"""course_exam.access 纯逻辑单测(无 DB)。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from app.services.course_exam import access as A


# ---------- 可见性判定 ----------

def test_open_by_default_when_no_access_row():
    assert A.decide_visible(['a', 'b'], {}, set(), set(), manager=False) == ['a', 'b']


def test_restricted_hidden_unless_enrolled_or_reviewer():
    modes = {'a': 'restricted', 'b': 'restricted', 'c': 'restricted', 'd': 'open'}
    got = A.decide_visible(['a', 'b', 'c', 'd'], modes, enrolled={'a'}, reviewing={'b'}, manager=False)
    assert got == ['a', 'b', 'd']


def test_manager_sees_everything_in_order():
    modes = {'a': 'restricted', 'b': 'restricted'}
    assert A.decide_visible(['b', 'a'], modes, set(), set(), manager=True) == ['b', 'a']


def test_unknown_mode_treated_as_restricted():
    # 防御:脏数据(非 open/restricted)按受限处理,不意外放开
    assert A.decide_visible(['a'], {'a': 'weird'}, set(), set(), manager=False) == []


def test_visible_dedupes_keys():
    assert A.decide_visible(['a', 'a', 'b'], {}, set(), set(), manager=False) == ['a', 'b']


# ---------- 参数规范化 ----------

def test_normalize_user_ids():
    assert A.normalize_user_ids([3, '5', 3, 7]) == [3, 5, 7]


@pytest.mark.parametrize('bad', [None, 'x', 5, [1, 'a'], [True], [0], [-2], {}])
def test_normalize_user_ids_rejects(bad):
    with pytest.raises(ValueError):
        A.normalize_user_ids(bad)


def test_normalize_user_ids_allows_empty_list():
    assert A.normalize_user_ids([]) == []


def test_normalize_mode():
    assert A.normalize_mode('open') == 'open'
    assert A.normalize_mode('restricted') == 'restricted'
    for bad in ('', None, 'OPEN', 'private', 1):
        with pytest.raises(ValueError):
            A.normalize_mode(bad)


# ---------- 成绩范围 ----------

def test_population_manager_is_enrolled_union_progress():
    assert A.report_population({1, 2}, {2, 3}, manager=True, subordinates=set()) == {1, 2, 3}


def test_population_supervisor_only_subordinates():
    assert A.report_population({1, 2}, {2, 3}, manager=False, subordinates={2, 3, 9}) == {2, 3}


def test_population_plain_user_empty():
    assert A.report_population({1, 2}, {2, 3}, manager=False, subordinates=set()) == set()


# ---------- 反复错题 ----------

def test_repeated_wrong_top5_matches_current_text():
    current = {'1': 'Q1', '2': 'Q2', '3': 'Q3'}
    rows = [
        ('1', 'Q1', False), ('1', 'Q1', False), ('1', 'Q1', True),     # 错 2 次 → 入选
        ('2', 'Q2-old', False), ('2', 'Q2-old', False), ('2', 'Q2', False),  # 旧题干不算 → 只错 1 次
        ('3', 'Q3', False), ('3', 'Q3', False), ('3', 'Q3', False),    # 错 3 次 → 排第一
        ('9', 'gone', False), ('9', 'gone', False),                    # 题已删除 → 不算
    ]
    got = A.repeated_wrong(rows, current)
    assert [(r['question_id'], r['wrong']) for r in got] == [(3, 3), (1, 2)]
    assert got[0]['question'] == 'Q3'
    assert got[1]['attempts'] == 3


def test_repeated_wrong_caps_at_top():
    current = {str(i): f'Q{i}' for i in range(10)}
    rows = [(str(i), f'Q{i}', False) for i in range(10) for _ in range(2)]
    assert len(A.repeated_wrong(rows, current, top=5)) == 5


def test_question_stats_only_current_text():
    current = {'1': 'Q1', '2': 'Q2'}
    rows = [('1', 'Q1', True), ('1', 'Q1', False), ('1', 'old', False), ('2', 'Q2', True)]
    got = {r['question_id']: r for r in A.question_stats(rows, current)}
    assert got[1]['attempts'] == 2 and got[1]['correct'] == 1 and got[1]['wrong'] == 1
    assert got[2]['attempts'] == 1 and got[2]['correct'] == 1
