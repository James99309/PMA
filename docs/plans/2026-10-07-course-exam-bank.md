# 课程考核题库 + 学习伙伴「小源」 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 CN 知识库 HTML 课件提供 100 题难度分级题库、累积闯关考核(60 及格/100 满分)、有效阅读时长解锁,并以全 PMA 常驻、可拖动吸附的「小源」面板承载提问与考核。

**Architecture:** 纯逻辑(抽题/计分/选项乱序/阅读计时校验/难度校准)放 `app/services/course_exam/logic.py`,零 DB 依赖,pytest 直测;DB 编排放 `service.py`;AI 出题放 `generator.py`;新蓝图 `app/views/learning.py` 提供 API、题库页、成绩页;前端组件 `at_course_buddy.html` + `course-buddy.js/css` 由 `at_sidebar` 宏统一挂载。判分全在服务端。

**Tech Stack:** Flask + SQLAlchemy + Alembic(PostgreSQL 17)、Jinja2 AT 模板、原生 JS(无框架)、WikiClaudeClient、pytest 9、Python Playwright(E2E)。

**设计依据:** `docs/plans/2026-10-07-course-exam-bank-design.md`
**前端原型(已经用户确认):** `docs/plans/assets/2026-10-07-course-buddy-prototype.html`

---

## 全局约定(每个任务都适用)

- 工作目录:`/Users/nijie/Documents/PMA/.worktrees/course-buddy-exam`(分支 `feat/course-buddy-exam`)。
- Python:`../../venv/bin/python`。**所有导入 app 的命令前必须** `export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib`(WeasyPrint)。
- 本地库:`pma_local`(CN 数据副本)。**禁止**用 `run.py` 起服务(`.env.*.local` 的废弃生产串会 override)。建 app 用 `scripts/temp/_report_flow_testkit.make_app()` 的同款方式。
- 模型时间统一用 `app.models.training.get_local_time`(Asia/Shanghai naive)。
- 界面中文 msgid 包 `_()`;JS 文案由模板注入 `window.CB_I18N`。
- 软删,不物理删题。
- 提交信息结尾:`Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`。
- 不修改受保护组件(`ui_helpers.html` / `data-list.js` / `filter-search.js` / `style.css`)。
- 改模板后跑:`../../venv/bin/python scripts/tools/check_all_templates_parse.py`(若路径不同,`find scripts -name check_all_templates_parse.py`)。

---

### Task 0: 本地库升级到 head(准备环境)

**背景:** `pma_local` 当前 `course_cover_url_20260730`,代码 head 为 `announcement_banner_20260913`。新迁移须接在 head 后面。

**Step 1: 备份**
```bash
mkdir -p data/backups && pg_dump -d pma_local -Fc -f data/backups/pma_local_pre_course_exam_$(date +%Y%m%d_%H%M).dump && ls -lh data/backups | tail -1
```
Expected: 生成非空 .dump。

**Step 2: 升级**
```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib
DATABASE_URL=postgresql://nijie@localhost:5432/pma_local PMA_DB_TYPE=sp8d FORCE_LOCAL_STORAGE=true \
  ../../venv/bin/flask --app wsgi db upgrade 2>&1 | tail -5
psql -d pma_local -Atc "select version_num from alembic_version"
```
Expected: `announcement_banner_20260913`。若撞 `DuplicateTable`(create_all 抢建表,见 memory project_create_all_blocks_upgrade),按该 memory 的猴补丁方式让 create_all 成为 no-op 后重跑,**不要** stamp 跳过含 ALTER 的迁移。

(无提交)

---

### Task 1: 纯逻辑 — 计分与难度权重

**Files:**
- Create: `app/services/course_exam/__init__.py`(空)
- Create: `app/services/course_exam/logic.py`
- Test: `tests/test_course_exam_logic.py`

**Step 1: 写失败测试**
```python
# tests/test_course_exam_logic.py
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
```

**Step 2: 运行确认失败**
```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib; ../../venv/bin/python -m pytest tests/test_course_exam_logic.py -q
```
Expected: FAIL(`ModuleNotFoundError: app.services.course_exam`)

**Step 3: 最小实现**
```python
# app/services/course_exam/logic.py
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
```

**Step 4: 运行确认通过** — 同 Step 2 命令,Expected: `4 passed`

**Step 5: 提交**
```bash
git add app/services/course_exam tests/test_course_exam_logic.py
git commit -m "feat(course-exam): 计分与难度权重纯逻辑"
```

---

### Task 2: 纯逻辑 — 抽题(加权、移出已答对、错题间隔)

**Files:** Modify `app/services/course_exam/logic.py`;Test `tests/test_course_exam_logic.py`

**Step 1: 追加失败测试**
```python
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
```

**Step 2:** 运行 → FAIL(`pick_question` 不存在)

**Step 3: 实现**
```python
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
```

**Step 4:** 运行 → `10 passed`

**Step 5:** `git commit -am "feat(course-exam): 加权抽题 + 已答对移出 + 错题间隔"`

---

### Task 3: 纯逻辑 — 选项乱序与判分

**Files:** Modify `logic.py`;Test 同上

**Step 1: 测试**
```python
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
```

**Step 2:** FAIL

**Step 3: 实现**
```python
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
```

**Step 4:** 运行 → 全部通过。**Step 5:** `git commit -am "feat(course-exam): 选项乱序 + 显示位换算 + 判分"`

---

### Task 4: 纯逻辑 — 阅读时长

**Files:** Modify `logic.py`;Test 同上

**Step 1: 测试**
```python
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
```

**Step 2:** FAIL

**Step 3: 实现**
```python
CHARS_PER_SEC = 5
MIN_PAGE_SEC = 20
READ_RATIO = 0.7
PAGE_CAP_FACTOR = 3
MAX_PING_SECONDS = 20       # 前端 15s 一报,留余量
PING_TOLERANCE = 2


def page_estimate(page):
    return max(MIN_PAGE_SEC, len(page.get('notes') or '') // CHARS_PER_SEC)


def required_read_seconds(pages, override=None):
    if override:
        return int(override)
    return int(sum(page_estimate(p) for p in pages) * READ_RATIO)


def accept_ping_seconds(seconds, elapsed):
    """服务端只认:不超过距上次上报真实间隔(+容差),且不超过单次上限。"""
    s = max(0, int(seconds or 0))
    s = min(s, MAX_PING_SECONDS)
    if elapsed is not None:
        s = min(s, max(0, int(elapsed) + PING_TOLERANCE))
    return s


def add_page_seconds(page_seconds, page, seconds, pages):
    """page 为 1 基页号;单页累计封顶 = 该页估算 × 3。返回新 dict。"""
    ps = dict(page_seconds or {})
    if not 1 <= page <= len(pages):
        return ps
    cap = page_estimate(pages[page - 1]) * PAGE_CAP_FACTOR
    key = str(page)
    ps[key] = min(cap, ps.get(key, 0) + seconds)
    return ps


def effective_read_seconds(page_seconds):
    return sum((page_seconds or {}).values())


def is_unlocked(page_seconds, pages, override=None):
    ps = page_seconds or {}
    if any(ps.get(str(i), 0) <= 0 for i in range(1, len(pages) + 1)):
        return False
    return effective_read_seconds(ps) >= required_read_seconds(pages, override)
```

**Step 4:** 通过。**Step 5:** `git commit -am "feat(course-exam): 阅读时长估算/上报校验/单页封顶/解锁判定"`

---

### Task 5: 纯逻辑 — 题库健康与实测难度

**Files:** Modify `logic.py`;Test 同上

**Step 1: 测试**
```python
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
```

**Step 2:** FAIL

**Step 3: 实现**
```python
MIN_SAMPLES = 10


def bank_health(questions):
    by_d = {1: 0, 2: 0, 3: 0}
    by_t = {'single': 0, 'multi': 0, 'judge': 0}
    for q in questions:
        by_d[q['difficulty']] += 1
        by_t[q['qtype']] = by_t.get(q['qtype'], 0) + 1
    max_score = sum(POINTS[d] * n for d, n in by_d.items())
    return {'total': len(questions), 'by_difficulty': by_d, 'by_type': by_t,
            'max_score': max_score, 'ok': max_score >= FULL_SCORE}


def empirical_difficulty(correct_first, n_first):
    """首次作答正确率 → 实测难度;样本 < 10 返回 None。"""
    if not n_first or n_first < MIN_SAMPLES:
        return None
    rate = correct_first / n_first
    return 1 if rate > 0.85 else (2 if rate >= 0.5 else 3)


def suspicious(correct_first, n_first):
    return bool(n_first and n_first >= MIN_SAMPLES and correct_first / n_first < 0.2)
```

**Step 4:** 通过。**Step 5:** `git commit -am "feat(course-exam): 题库健康检查 + 实测难度推断"`

---

### Task 6: 模型 + 迁移

**Files:**
- Create: `app/models/course_exam.py`
- Modify: `app/models/course.py`(加 `min_read_seconds`)
- Modify: `app/models/user.py`(User 加 `learning_buddy_enabled`)
- Modify: `app/models/__init__.py`(若该文件集中 import 模型,则加 `from app.models import course_exam`;先 `grep -n "course" app/models/__init__.py` 看现有写法照抄)
- Create: `migrations/versions/course_exam_bank_20261007.py`

**Step 1: 模型**
```python
# app/models/course_exam.py
# -*- coding: utf-8 -*-
"""课程考核:题库 + 每人每课学习进度。设计见 docs/plans/2026-10-07-course-exam-bank-design.md"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Index

from app import db
from app.models.training import get_local_time


class CourseQuizQuestion(db.Model):
    __tablename__ = 'course_quiz_questions'

    id = Column(Integer, primary_key=True)
    course_key = Column(String(80), nullable=False, index=True)
    qtype = Column(String(10), nullable=False)               # single / multi / judge
    difficulty = Column(Integer, nullable=False, default=2)   # 1 易 / 2 中 / 3 难(生效值)
    ai_difficulty = Column(Integer, nullable=True)            # 复核 AI 独立评级
    question = Column(Text, nullable=False)
    options = Column(JSON, nullable=True)                     # judge 为空
    answer = Column(JSON, nullable=False)                     # int / [int] / bool,原始下标
    explain = Column(Text, nullable=True)
    source_page = Column(Integer, nullable=True)
    status = Column(String(10), nullable=False, default='active', index=True)  # active/review/disabled
    origin = Column(String(10), nullable=False, default='ai')  # ai / edited / legacy
    review_note = Column(Text, nullable=True)                 # 复核 AI 给出的存疑理由
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=get_local_time, nullable=False)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time, nullable=False)

    __table_args__ = (Index('ix_cqq_course_status', 'course_key', 'status'),)

    def as_logic(self):
        """转成 logic.py 用的 dict。"""
        return {'id': self.id, 'qtype': self.qtype, 'difficulty': self.difficulty,
                'options': self.options or [], 'answer': self.answer}

    def to_admin_dict(self):
        return {'id': self.id, 'qtype': self.qtype, 'difficulty': self.difficulty,
                'ai_difficulty': self.ai_difficulty, 'question': self.question,
                'options': self.options or [], 'answer': self.answer, 'explain': self.explain or '',
                'source_page': self.source_page, 'status': self.status, 'origin': self.origin,
                'review_note': self.review_note or ''}


class CourseLearningProgress(db.Model):
    __tablename__ = 'course_learning_progress'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    course_key = Column(String(80), nullable=False, index=True)

    page_seconds = Column(JSON, nullable=False, default=dict)  # {"1": 35, ...}
    last_ping_at = Column(DateTime, nullable=True)
    unlocked_at = Column(DateTime, nullable=True)

    score = Column(Integer, nullable=False, default=0)
    current_question_id = Column(Integer, nullable=True)
    current_option_order = Column(JSON, nullable=True)
    current_answered = Column(Boolean, nullable=False, default=False)
    current_result = Column(JSON, nullable=True)               # 已提交未点下一题时的结果快照
    passed_at = Column(DateTime, nullable=True)
    perfect_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=get_local_time, nullable=False)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time, nullable=False)

    __table_args__ = (Index('ix_clp_user_course', 'user_id', 'course_key', unique=True),)
```

`app/models/course.py` 在 `article_id` 后加:
```python
    min_read_seconds = Column(Integer, nullable=True)   # 考核解锁所需有效阅读秒数;空=按讲解字数自动估算
```
并在 `to_dict()` 加 `'min_read_seconds': self.min_read_seconds,`。

`app/models/user.py` User 类(找 `hr_documents = db.Column` 那行之后)加:
```python
    learning_buddy_enabled = db.Column(db.Boolean, nullable=False, default=True, server_default='true')  # 学习伙伴小源显示开关
```

**Step 2: 迁移**
```python
# migrations/versions/course_exam_bank_20261007.py
"""课程考核题库 + 学习进度 + 小源开关

Revision ID: course_exam_bank_20261007
Revises: announcement_banner_20260913
"""
from alembic import op
import sqlalchemy as sa

revision = 'course_exam_bank_20261007'
down_revision = 'announcement_banner_20260913'
branch_labels = None
depends_on = None


def _has_table(name):
    return name in sa.inspect(op.get_bind()).get_table_names()


def _has_column(table, col):
    return col in [c['name'] for c in sa.inspect(op.get_bind()).get_columns(table)]


def upgrade():
    # 幂等:生产 app 启动 create_all 可能已抢先建表
    if not _has_table('course_quiz_questions'):
        op.create_table(
            'course_quiz_questions',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('course_key', sa.String(80), nullable=False),
            sa.Column('qtype', sa.String(10), nullable=False),
            sa.Column('difficulty', sa.Integer(), nullable=False, server_default='2'),
            sa.Column('ai_difficulty', sa.Integer()),
            sa.Column('question', sa.Text(), nullable=False),
            sa.Column('options', sa.JSON()),
            sa.Column('answer', sa.JSON(), nullable=False),
            sa.Column('explain', sa.Text()),
            sa.Column('source_page', sa.Integer()),
            sa.Column('status', sa.String(10), nullable=False, server_default='active'),
            sa.Column('origin', sa.String(10), nullable=False, server_default='ai'),
            sa.Column('review_note', sa.Text()),
            sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id')),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_course_quiz_questions_course_key', 'course_quiz_questions', ['course_key'])
        op.create_index('ix_course_quiz_questions_status', 'course_quiz_questions', ['status'])
        op.create_index('ix_cqq_course_status', 'course_quiz_questions', ['course_key', 'status'])
    if not _has_table('course_learning_progress'):
        op.create_table(
            'course_learning_progress',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('course_key', sa.String(80), nullable=False),
            sa.Column('page_seconds', sa.JSON(), nullable=False),
            sa.Column('last_ping_at', sa.DateTime()),
            sa.Column('unlocked_at', sa.DateTime()),
            sa.Column('score', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('current_question_id', sa.Integer()),
            sa.Column('current_option_order', sa.JSON()),
            sa.Column('current_answered', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('current_result', sa.JSON()),
            sa.Column('passed_at', sa.DateTime()),
            sa.Column('perfect_at', sa.DateTime()),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_course_learning_progress_user_id', 'course_learning_progress', ['user_id'])
        op.create_index('ix_course_learning_progress_course_key', 'course_learning_progress', ['course_key'])
        op.create_index('ix_clp_user_course', 'course_learning_progress', ['user_id', 'course_key'], unique=True)
    if not _has_column('interactive_courses', 'min_read_seconds'):
        op.add_column('interactive_courses', sa.Column('min_read_seconds', sa.Integer()))
    if not _has_column('users', 'learning_buddy_enabled'):
        op.add_column('users', sa.Column('learning_buddy_enabled', sa.Boolean(),
                                         nullable=False, server_default='true'))


def downgrade():
    op.drop_column('users', 'learning_buddy_enabled')
    op.drop_column('interactive_courses', 'min_read_seconds')
    op.drop_table('course_learning_progress')
    op.drop_table('course_quiz_questions')
```

**Step 3: 跑迁移 + 校验 heads 单一**
```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib
DATABASE_URL=postgresql://nijie@localhost:5432/pma_local PMA_DB_TYPE=sp8d FORCE_LOCAL_STORAGE=true ../../venv/bin/flask --app wsgi db heads
DATABASE_URL=postgresql://nijie@localhost:5432/pma_local PMA_DB_TYPE=sp8d FORCE_LOCAL_STORAGE=true ../../venv/bin/flask --app wsgi db upgrade 2>&1 | tail -3
psql -d pma_local -Atc "\d course_learning_progress" | head -5; psql -d pma_local -Atc "select learning_buddy_enabled from users limit 1"
```
Expected: heads 只有 `course_exam_bank_20261007 (head)`;表存在;`t`。

**Step 4: 测 downgrade/upgrade 往返**(`db downgrade -1` 再 `db upgrade`),均无报错。

**Step 5:** `git add app/models migrations/versions/course_exam_bank_20261007.py && git commit -m "feat(course-exam): 题库/学习进度表 + 课程阅读时长覆盖 + 小源开关列"`

---

### Task 7: DB 服务 — 阅读上报与进度

**Files:**
- Create: `app/services/course_exam/service.py`
- Create: `scripts/temp/check_course_exam_service.py`(集成验证脚本,对 pma_local 跑,自清理)

**Step 1: 先写集成验证脚本(会失败)**
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""course_exam.service 集成验证(pma_local)。用独立 course_key 'zz-exam-test',结束硬删。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _report_flow_testkit import make_app

KEY = 'zz-exam-test'
PAGES = [{'label': 'p1', 'notes': ''}, {'label': 'p2', 'notes': ''}]   # required = 28s

app = make_app()
with app.app_context():
    from app import db
    from app.models.user import User
    from app.models.course_exam import CourseQuizQuestion, CourseLearningProgress
    from app.services.course_exam import service as S
    u = User.query.filter_by(is_active=True).first()
    fails = []
    def check(cond, msg):
        print(('OK  ' if cond else 'FAIL') + ' ' + msg)
        if not cond: fails.append(msg)
    try:
        # ---- 阅读 ----
        p = S.record_read(u.id, KEY, PAGES, page=1, seconds=15)
        check(p['read']['percent'] > 0 and not p['read']['unlocked'], '首次上报计时、未解锁')
        S._force_last_ping(u.id, KEY, seconds_ago=16)
        p = S.record_read(u.id, KEY, PAGES, page=1, seconds=999)
        check(p['read']['page_seconds']['1'] <= 60, '伪造大秒数被截断且单页封顶')
        S._force_last_ping(u.id, KEY, seconds_ago=16)
        p = S.record_read(u.id, KEY, PAGES, page=2, seconds=15)
        check(p['read']['unlocked'], '两页都开过且时长达标 → 解锁')
        # (Task 8 追加考核段)
    finally:
        db.session.rollback()
        CourseLearningProgress.query.filter_by(course_key=KEY).delete()
        CourseQuizQuestion.query.filter_by(course_key=KEY).delete()
        db.session.commit()
    print('FAILS:', fails)
    sys.exit(1 if fails else 0)
```
运行:`export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib; ../../venv/bin/python scripts/temp/check_course_exam_service.py` → 失败(无 service)。

**Step 2: 实现 service 的阅读部分**
```python
# app/services/course_exam/service.py
# -*- coding: utf-8 -*-
"""课程考核 DB 编排。纯规则全部委托 logic.py;本模块只管读写与事务。"""
import random

from app import db
from app.models.course_exam import CourseQuizQuestion, CourseLearningProgress
from app.models.training import TrainingQuizAttempt, get_local_time
from app.services.course_exam import logic as L

MODULE_SLUG = 'bank'


def get_or_create_progress(user_id, course_key):
    p = CourseLearningProgress.query.filter_by(user_id=user_id, course_key=course_key).first()
    if not p:
        p = CourseLearningProgress(user_id=user_id, course_key=course_key, page_seconds={}, score=0)
        db.session.add(p)
        db.session.flush()
    return p


def progress_dict(p, pages, override=None):
    ps = p.page_seconds or {}
    required = L.required_read_seconds(pages, override)
    eff = L.effective_read_seconds(ps)
    unlocked = bool(p.unlocked_at)
    percent = 100 if unlocked else min(99, int(eff * 100 / required)) if required else 0
    return {
        'read': {'percent': percent, 'unlocked': unlocked, 'page_seconds': ps,
                 'required_seconds': required, 'effective_seconds': eff,
                 'pages_seen': sum(1 for v in ps.values() if v > 0), 'pages_total': len(pages)},
        'exam': {'score': p.score, 'passed': bool(p.passed_at), 'perfect': bool(p.perfect_at)},
    }


def record_read(user_id, course_key, pages, page, seconds, override=None):
    p = get_or_create_progress(user_id, course_key)
    if not p.unlocked_at:
        now = get_local_time()
        elapsed = (now - p.last_ping_at).total_seconds() if p.last_ping_at else None
        accepted = L.accept_ping_seconds(seconds, elapsed)
        p.page_seconds = L.add_page_seconds(p.page_seconds, page, accepted, pages)
        p.last_ping_at = now
        if L.is_unlocked(p.page_seconds, pages, override):
            p.unlocked_at = now
        db.session.commit()
    return progress_dict(p, pages, override)


def _force_last_ping(user_id, course_key, seconds_ago):
    """仅测试用:把上次上报时间往前拨。"""
    from datetime import timedelta
    p = get_or_create_progress(user_id, course_key)
    p.last_ping_at = get_local_time() - timedelta(seconds=seconds_ago)
    db.session.commit()
```

**Step 3:** 运行脚本 → 3 个 OK,`FAILS: []`

**Step 4:** `git add app/services/course_exam/service.py scripts/temp/check_course_exam_service.py && git commit -m "feat(course-exam): 阅读上报服务 + 集成验证脚本"`

---

### Task 8: DB 服务 — 当前题(断点)、提交、下一题

**Files:** Modify `service.py`、`scripts/temp/check_course_exam_service.py`

**Step 1: 在验证脚本 `# (Task 8 追加考核段)` 处追加**
```python
        # ---- 考核 ----
        for i, d in enumerate([1, 1, 2, 3], 1):
            db.session.add(CourseQuizQuestion(course_key=KEY, qtype='single', difficulty=d,
                question=f'Q{i}', options=['a', 'b', 'c', 'd'], answer=0, explain='e', status='active'))
        db.session.add(CourseQuizQuestion(course_key=KEY, qtype='judge', difficulty=1,
            question='J', answer=True, status='review'))       # 待审题不进池
        db.session.commit()
        c1 = S.current_question(u.id, KEY)
        c2 = S.current_question(u.id, KEY)
        check(c1['question']['id'] == c2['question']['id'] and c1['question']['options'] == c2['question']['options'],
              '断点幂等:同题同选项顺序')
        check('answer' not in c1['question'] and 'explain' not in c1['question'], '当前题不泄露答案/解析')
        check(c1['question']['question'] != 'J', '待审题不出')
        q = CourseQuizQuestion.query.get(c1['question']['id'])
        prog = S.get_or_create_progress(u.id, KEY)
        right_shown = prog.current_option_order.index(0)          # 原始答案 0 显示在哪
        r = S.submit_answer(u.id, KEY, right_shown)
        check(r['correct'] and r['score'] == L.POINTS[q.difficulty], '答对按难度加分')
        r2 = S.submit_answer(u.id, KEY, right_shown)
        check(r2.get('error') == 'already_answered', '重复提交被拒(不重复加分)')
        c3 = S.current_question(u.id, KEY)
        check(c3['answered'] and c3['result']['correct'], '提交后未点下一题 → 再打开看到结果')
        S.next_question(u.id, KEY)
        c4 = S.current_question(u.id, KEY)
        check(c4['question']['id'] != q.id, '答对的题移出抽题池')
        n_att = TrainingQuizAttempt.query.filter_by(user_id=u.id, course_slug=KEY).count()
        check(n_att == 1, '逐题留痕写入 training_quiz_attempt')
        # 满分后无题可抽
        prog = S.get_or_create_progress(u.id, KEY); prog.score = 100; prog.perfect_at = get_local_time(); db.session.commit()
        check(S.current_question(u.id, KEY).get('done'), '满分后 done=True')
```
清理段加:`TrainingQuizAttempt.query.filter_by(course_slug=KEY, module_slug='bank').delete()`;脚本顶部 import `TrainingQuizAttempt`、`get_local_time`、`logic as L`。

**Step 2:** 运行 → FAIL

**Step 3: 实现**
```python
def _active_bank(course_key):
    return CourseQuizQuestion.query.filter_by(course_key=course_key, status='active').all()


def _user_history(user_id, course_key):
    rows = (TrainingQuizAttempt.query
            .filter_by(user_id=user_id, course_slug=course_key, module_slug=MODULE_SLUG)
            .order_by(TrainingQuizAttempt.attempted_at, TrainingQuizAttempt.id).all())
    correct = {int(r.question_id) for r in rows if r.is_correct}
    recent = [int(r.question_id) for r in rows]
    return correct, recent


def public_question(q, order):
    d = {'id': q.id, 'qtype': q.qtype, 'difficulty': q.difficulty,
         'points': L.POINTS[q.difficulty], 'question': q.question}
    if q.qtype != 'judge':
        d['options'] = [q.options[i] for i in order]
    return d


def current_question(user_id, course_key, rng=None):
    """取断点题;没有就抽一题并落盘(幂等)。"""
    p = get_or_create_progress(user_id, course_key)
    base = {'score': p.score, 'passed': bool(p.passed_at), 'perfect': bool(p.perfect_at)}
    if p.perfect_at:
        return dict(base, done=True)
    q = CourseQuizQuestion.query.get(p.current_question_id) if p.current_question_id else None
    if q is None or q.status != 'active' and not p.current_answered:
        bank = [x.as_logic() for x in _active_bank(course_key)]
        correct, recent = _user_history(user_id, course_key)
        picked = L.pick_question(bank, p.score, correct, recent, rng or random.SystemRandom())
        if not picked:
            return dict(base, done=True, exhausted=True)
        q = CourseQuizQuestion.query.get(picked['id'])
        p.current_question_id = q.id
        p.current_option_order = L.option_order_for(q.as_logic(), rng or random.SystemRandom())
        p.current_answered = False
        p.current_result = None
        db.session.commit()
    return dict(base, question=public_question(q, p.current_option_order),
                answered=p.current_answered, result=p.current_result)


def submit_answer(user_id, course_key, shown_answer):
    p = get_or_create_progress(user_id, course_key)
    if not p.current_question_id:
        return {'error': 'no_question'}
    if p.current_answered:
        return {'error': 'already_answered'}
    q = CourseQuizQuestion.query.get(p.current_question_id)
    try:
        original = L.to_original(q.qtype, shown_answer, p.current_option_order)
    except ValueError as e:
        return {'error': 'bad_answer', 'message': str(e)}
    ok = L.is_correct(q.as_logic(), original)
    before = p.score
    if ok:
        p.score = L.apply_score(p.score, q.difficulty)
    flags = L.crossed(before, p.score)
    now = get_local_time()
    if flags['passed'] or (p.score >= L.PASS_SCORE and not p.passed_at):
        p.passed_at = p.passed_at or now
    if flags['perfect']:
        p.perfect_at = now
    order = p.current_option_order
    shown_correct = (q.answer if q.qtype == 'judge'
                     else order.index(q.answer) if q.qtype == 'single'
                     else sorted(order.index(i) for i in q.answer))
    result = {'correct': ok, 'gained': p.score - before, 'score': p.score,
              'correct_answer': shown_correct, 'your_answer': shown_answer,
              'explain': q.explain or '', 'source_page': q.source_page,
              'just_passed': flags['passed'], 'just_perfect': flags['perfect']}
    p.current_answered = True
    p.current_result = result
    db.session.add(TrainingQuizAttempt(
        user_id=user_id, course_slug=course_key, module_slug=MODULE_SLUG, chapter=1,
        question_id=str(q.id), question_text=q.question, question_type=q.qtype,
        user_answer=str(original), correct_answer=str(q.answer), is_correct=ok, attempted_at=now))
    db.session.commit()
    return result


def next_question(user_id, course_key):
    p = get_or_create_progress(user_id, course_key)
    if p.current_answered:
        p.current_question_id = None
        p.current_option_order = None
        p.current_answered = False
        p.current_result = None
        db.session.commit()
    return current_question(user_id, course_key)
```
注意 `current_question` 中条件写成带括号的明确形式:`if q is None or (q.status != 'active' and not p.current_answered):`(停用题且未作答 → 换题;已作答的保留结果展示)。

**Step 4:** 运行脚本 → 全 OK。

**Step 5:** `git commit -am "feat(course-exam): 断点幂等出题 + 服务端判分 + 下一题推进"`

---

### Task 9: 旧题库导入 + 课程页数据工具

**Files:** Modify `service.py`;Modify 验证脚本

**Step 1: 验证脚本追加**:在临时目录写一个 `zz-exam-test.quiz.json`(2 道:single + judge),调用 `S.import_legacy_json(KEY, tmpdir)` 两次,断言只导入 2 道、`origin='legacy'`、`difficulty=2`。

**Step 2: 实现**
```python
def import_legacy_json(course_key, course_assets_dir):
    """旧版 <key>.quiz.json → 题库(仅当本课题库为空时)。返回导入条数。"""
    import json, os
    if CourseQuizQuestion.query.filter_by(course_key=course_key).first():
        return 0
    path = os.path.join(course_assets_dir, course_key + '.quiz.json')
    if not os.path.isfile(path):
        return 0
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    n = 0
    for q in data.get('questions') or []:
        if q.get('type') not in ('single', 'judge'):
            continue
        db.session.add(CourseQuizQuestion(
            course_key=course_key, qtype=q['type'], difficulty=2, question=q['question'],
            options=q.get('options'), answer=q['answer'], explain=q.get('explain'),
            status='active', origin='legacy'))
        n += 1
    db.session.commit()
    return n
```

**Step 3:** 运行通过。**Step 4:** `git commit -am "feat(course-exam): 旧 quiz.json 题库一次性导入"`

---

### Task 10: AI 出题器(三批 + 复核 + 去重)

**Files:**
- Create: `app/services/course_exam/generator.py`
- Test: `tests/test_course_exam_generator.py`(只测可离线部分:prompt 构建、normalize、去重、复核合并;AI 调用用假 client 注入)

**Step 1: 测试**
```python
# tests/test_course_exam_generator.py
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.course_exam import generator as G

PAGES = [{'label': '公司', 'notes': '总部在上海'}, {'label': '产品', 'notes': '直放站与对讲机'}]


class FakeClient:
    def __init__(self, replies): self.replies = list(replies); self.calls = []
    def complete(self, system, user, model, max_tokens=16000, temperature=None):
        self.calls.append(user)
        class R: pass
        r = R(); r.text = self.replies.pop(0); return r
    def close(self): pass


def test_normalize_filters_type_constraints():
    raw = {'questions': [
        {'type': 'judge', 'question': '判断', 'answer': True, 'page': 1},            # 易 judge ok
        {'type': 'multi', 'question': '多选', 'options': ['a', 'b', 'c'], 'answer': [0, 1], 'page': 2},
        {'type': 'single', 'question': '单选', 'options': ['a', 'b'], 'answer': 5},   # 越界丢弃
    ]}
    got = G.normalize(raw, difficulty=1)
    assert [q['qtype'] for q in got] == ['judge']        # 易档不允许 multi


def test_dedupe_similar_questions():
    qs = [{'question': '和源通信总部位于哪个城市？'}, {'question': '和源通信的总部位于哪个城市'},
          {'question': '直放站的作用是什么'}]
    assert len(G.dedupe(qs)) == 2


def test_merge_review_marks_disagreement():
    qs = [{'question': 'a', 'difficulty': 1}, {'question': 'b', 'difficulty': 3}]
    review = {'reviews': [{'index': 0, 'difficulty': 1, 'answer_ok': True},
                          {'index': 1, 'difficulty': 1, 'answer_ok': True}]}
    out = G.merge_review(qs, review)
    assert out[0]['status'] == 'active' and out[0]['ai_difficulty'] == 1
    assert out[1]['status'] == 'review'


def test_generate_course_runs_three_batches_then_review():
    batch = '{"questions":[{"type":"single","question":"Q%d","options":["a","b","c","d"],"answer":0,"explain":"e","page":1}]}'
    replies = [batch % 1, batch % 2, batch % 3,
               '{"reviews":[{"index":0,"difficulty":1,"answer_ok":true},{"index":1,"difficulty":2,"answer_ok":true},{"index":2,"difficulty":3,"answer_ok":false,"note":"答案存疑"}]}']
    fc = FakeClient(replies)
    out = G.generate_course(PAGES, plan={1: 1, 2: 1, 3: 1}, client=fc)
    assert len(fc.calls) == 4
    assert [q['status'] for q in out] == ['active', 'active', 'review']
```

**Step 2:** FAIL

**Step 3: 实现** — 要点(完整代码写入文件):
- `DIFF_RULES`:三档定义文本(设计文档 §5 表格原文)。
- `TYPE_ALLOWED = {1: ('single', 'judge'), 2: ('single', 'multi', 'judge'), 3: ('single', 'multi')}`。
- `DEFAULT_PLAN = {1: 50, 2: 30, 3: 20}`;每批内题型配比提示:单选 70% / 多选 10% / 判断 20%(按档允许范围归一)。
- `build_batch_prompt(pages, difficulty, n, existing_questions)`:逐页 `【第i页·label】notes`,只给本档规则,附「以下题干已存在,不得重复:…」(最多 200 条截断),要求 JSON:`{"questions":[{"type","question","options","answer","explain","page"}]}`;system 沿用 `course_quiz._SYSTEM` 的「禁英文双引号、只输出 JSON」约束。
- `normalize(raw, difficulty)`:校验结构(single answer 为合法 int;multi answer 为 ≥2 个合法下标的列表、选项 ≥4;judge 为 bool)、题型在 `TYPE_ALLOWED[difficulty]` 内,输出 `{qtype, difficulty, question, options, answer, explain, source_page}`。
- `dedupe(qs)`:去标点空白后 `difflib.SequenceMatcher(None, a, b).ratio() >= 0.85` 视为重复,保留先出现的。
- `build_review_prompt(pages, qs)`:不含 difficulty 字段,只给题干/选项/答案,要求 `{"reviews":[{"index","difficulty","answer_ok","note"}]}`。
- `merge_review(qs, review)`:`ai_difficulty` 写入;`answer_ok and ai_difficulty == difficulty` → `active`,否则 `review` 并写 `review_note`;复核缺项 → `review`。
- `generate_course(pages, plan=DEFAULT_PLAN, client=None)`:三档各一次 `client.complete`(大批量时每次 ≤25 题分多次调用,`max_tokens=min(16000, 2000 + n*600)`),JSON 解析复用 `app.services.course_quiz._extract_json`;去重;复核(每 40 题一次调用);返回题目 dict 列表。`client` 为空时用 `claude_client.WikiClaudeClient()` 并 `finally close()`;模型 `claude_client.QUERY_MODEL`。
- `run_generation_job(app, course_key, pages, user_id, plan, replace)`:后台线程体,`with app.app_context()`;`replace=True` 时把本课 `origin='ai'` 且 `status!='disabled'` 的题置 `disabled`;落库;最后写站内 `Message(message_type='course_bank_ready', sender_id=user_id, recipient_id=user_id, title='题库生成完成', content=f'{title}:启用 X 题,待审 Y 题', related_object_type='course', related_object_id=course_id)`;异常写 `title='题库生成失败'`。
- `regenerate_one(pages, q)`:同难度同页重出一题(调用一次 batch prompt,n=1,附原题干要求换角度)。

**Step 4:** `pytest tests/test_course_exam_generator.py -q` → 4 passed。

**Step 5:** `git add app/services/course_exam/generator.py tests/test_course_exam_generator.py && git commit -m "feat(course-exam): AI 三批分档出题 + 独立复核 + 相似去重"`

---

### Task 11: 学员 API 蓝图

**Files:**
- Create: `app/views/learning.py`
- Modify: `app/__init__.py`(注册蓝图:`grep -n "register_blueprint(knowledge_wiki_bp" app/__init__.py`,在其后照写)
- Modify: `scripts/temp/check_course_exam_service.py` → 新增 `scripts/temp/check_course_exam_api.py`(Flask test_client + 登录态)

**Step 1: API 验证脚本**(用 `app.test_client()`,以 `with client.session_transaction() as s: s['_user_id'] = str(u.id); s['_fresh'] = True` 登录;选一门本地存在的 HTML 课程 key,如 `smart-task-intercom`;在该课插入 3 道 `active` 测试题(question 以 `ZZTEST-` 开头),结束删除):
- `GET /api/learning/<key>/progress` 200,含 `read.percent`
- `POST /api/learning/<key>/read-ping {page:1, seconds:15}` 200
- 未解锁时 `GET /api/learning/<key>/exam/current` → 403 `locked`
- 直接把进度 `unlocked_at` 置为现在后:`exam/current` 200 且无 `answer` 字段;`exam/answer` 返回 `correct`;`exam/next` 换题
- 无 CSRF token 的 POST 应被拒?——先 `grep -n "CSRFProtect\|csrf.exempt" app/__init__.py app/views/knowledge_wiki.py`:若全局开启 CSRF,前端统一带 `X-CSRFToken`(取 `meta[name=csrf-token]`),测试里关 `WTF_CSRF_ENABLED`。

**Step 2: 实现**
```python
# app/views/learning.py
# -*- coding: utf-8 -*-
"""学习伙伴小源 + 课程考核 API。判分全在服务端,前端拿不到答案。"""
from flask import Blueprint, jsonify, request, abort
from flask_login import login_required, current_user

from app import db
from app.models.course import InteractiveCourse
from app.services.course_exam import service as S

learning_bp = Blueprint('learning', __name__)


def _course_or_404(key):
    """只支持 HTML 课件。返回 (row, pages)。"""
    from app.views.knowledge_wiki import _find_course, _get_course_pages
    course, path = _find_course(key)
    if not course or course.get('media_type', 'html') != 'html':
        abort(404)
    row = InteractiveCourse.query.filter_by(key=course['key']).first()
    return row, _get_course_pages(course['key'], path)


@learning_bp.route('/api/learning/<key>/progress')
@login_required
def progress(key):
    row, pages = _course_or_404(key)
    p = S.get_or_create_progress(current_user.id, row.key)
    db.session.commit()
    return jsonify({'success': True, 'data': S.progress_dict(p, pages, row.min_read_seconds)})


@learning_bp.route('/api/learning/<key>/read-ping', methods=['POST'])
@login_required
def read_ping(key):
    row, pages = _course_or_404(key)
    data = request.get_json(silent=True) or {}
    try:
        page, seconds = int(data.get('page')), int(data.get('seconds'))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'bad params'}), 400
    return jsonify({'success': True, 'data': S.record_read(
        current_user.id, row.key, pages, page, seconds, row.min_read_seconds)})


def _require_unlocked(row):
    p = S.get_or_create_progress(current_user.id, row.key)
    if not p.unlocked_at:
        db.session.commit()
        return jsonify({'success': False, 'error': 'locked'}), 403
    return None


@learning_bp.route('/api/learning/<key>/exam/current')
@login_required
def exam_current(key):
    row, _ = _course_or_404(key)
    return _require_unlocked(row) or jsonify({'success': True, 'data': S.current_question(current_user.id, row.key)})


@learning_bp.route('/api/learning/<key>/exam/answer', methods=['POST'])
@login_required
def exam_answer(key):
    row, _ = _course_or_404(key)
    locked = _require_unlocked(row)
    if locked:
        return locked
    r = S.submit_answer(current_user.id, row.key, (request.get_json(silent=True) or {}).get('answer'))
    if r.get('error'):
        return jsonify({'success': False, **r}), 400
    return jsonify({'success': True, 'data': r})


@learning_bp.route('/api/learning/<key>/exam/next', methods=['POST'])
@login_required
def exam_next(key):
    row, _ = _course_or_404(key)
    return _require_unlocked(row) or jsonify({'success': True, 'data': S.next_question(current_user.id, row.key)})
```
另加 `GET /api/learning/buddy`:返回 `{enabled, courses:[{key,title,score,unlocked,read_percent,perfect}]}`(只列 HTML 课 + 题库 health ok 的课;课程外面板用;`perfect` 的不列)以及 `POST /api/learning/buddy/toggle {enabled}`(写 `current_user.learning_buddy_enabled`)。

**Step 3:** 运行 API 脚本 → 全 OK。

**Step 4:** `git add app/views/learning.py app/__init__.py scripts/temp/check_course_exam_api.py && git commit -m "feat(course-exam): 学员端 API(进度/阅读上报/断点/提交/下一题/小源初始化)"`

---

### Task 12: 小源前端组件(从原型移植)

**Files:**
- Create: `app/static/css/course-buddy.css`(原型 `<style>` 中 `.bd-*`、`.seg`、`.prog/.bar/.qmeta/.qtext/.opt*/.judge/.explain/.cheer/.primary/.locked/.clist/.citem/.chat/.msg/.thumbs/.thumb/.scope/.chip/.compose`、窄屏媒体查询;**去掉**模拟页面骨架 `.app/.side/.top/.stage/.slide/.notes/.proto-tip`;颜色全部改用 at-theme 变量:`--card`→`var(--bg-card, #fff)` 先 `grep -n "\-\-bg-card\|\-\-card" app/static/css/at-theme.css` 用真实变量名;`--fill/--ok/--bad` 在 `.bd-panel` 作用域内定义并给暗色覆盖)
- Create: `app/static/js/course-buddy.js`(原型 `CourseBuddy` IIFE 移植,替换模拟后端为 fetch;CSRF 头;i18n 取 `window.CB_I18N`)
- Create: `app/templates/components/at_course_buddy.html`
- Modify: `app/templates/components/at_sidebar.html`(宏末尾 `{% endmacro %}` 前 include)

**JS 对外接口(课程播放器用):**
```javascript
window.CourseBuddy = {
  setCourse({key, title, totalPages}),   // 进入课程上下文(启用计时)
  onPage(pageNo),                        // 翻页(也算活动)
  activity(),                            // 指针/键盘活动
  reflow()                               // 布局变化后重算位置
};
```

**移植要点(逐条核对原型):**
1. 位置:`localStorage['bd-pos']`;`leftInset()` 读 `.at-sidebar` 的 `getBoundingClientRect().right`;监听 sidebar 的 `transitionend` + `ResizeObserver` 调 `applyPos()`。
2. `minBottom()`:存在 `#cpNotes`(课程播放器讲解栏)时取其高度 + 10。
3. 计时器(仅 `setCourse` 后):每秒 tick,`document.visibilityState==='visible'` 且 `Date.now()-lastActivity < 120000` 才累计到当前页;每 15 秒 `POST read-ping {page, seconds}`(seconds=本区间累计);`pagehide` 时 `navigator.sendBeacon` 补报;闲置超 120s → `sleep()` 状态、恢复活动 → `wake()`;解锁后停止计时。
4. 考核数据流:打开考核 tab → `GET exam/current`;`answered=true` 时直接渲染结果态(用 `result`);提交 → `POST exam/answer {answer: 显示位}`;下一题 → `POST exam/next`。前端**不再**持有答案,结果态用服务端返回的 `correct_answer`(显示位)着色。
5. 提问:`POST /api/wiki/query {question, topic?}`;课程内「本课程」范围:请求附 `course_key`(在 Task 13 后端支持;此前先用全库),渲染 `data.answer`(markdown 用现有 wiki 页的渲染函数?先 `grep -n "marked\|renderMarkdown" app/templates/knowledge/at_wiki.html`,能复用则复用,否则纯文本 + 换行)和 `data.deck_pages` 缩略图(点击 `location.href = play_url`)。对话存 `localStorage['bd-chat']` 最多 50 条。
6. 课程外考核列表:`GET /api/learning/buddy` 的 `courses`;点已解锁课 → 进入该课考核;未解锁课点击 → 跳课程页。
7. 气泡节流:课程外「还有 N 门课没满分」每天一次(`localStorage['bd-nag-date']`)。
8. `enabled=false` 时不渲染小源(模板侧已判断,JS 兜底)。

**模板 `at_course_buddy.html`:**
```jinja
{% if current_user.is_authenticated and current_user.learning_buddy_enabled %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/course-buddy.css') }}">
<script>
  window.CB_I18N = {
    ask: "{{ _('提问') }}", exam: "{{ _('考核') }}", read: "{{ _('阅读') }}",
    submit: "{{ _('提交答案') }}", next: "{{ _('下一题') }}", done: "{{ _('完成') }}",
    passed: "{{ _('已及格！可以继续冲 100 分') }}", perfect: "{{ _('满分！这门课的考核完成了') }}",
    unlock: "{{ _('解锁考核啦，来考考你？') }}", sleep: "{{ _('休息中，翻页叫醒我') }}",
    hello: "{{ _('有问题，问我～') }}", nag: "{{ _('还有 %(n)s 门课考核没满分', n='{n}') }}",
    easy: "{{ _('易') }}", mid: "{{ _('中') }}", hard: "{{ _('难') }}", multi: "{{ _('多选') }}",
    judge: "{{ _('判断') }}", yes: "{{ _('正确') }}", no: "{{ _('错误') }}",
    wrong: "{{ _('答错了') }}", wrong_tip: "{{ _('这题之后还会再出现') }}", right: "{{ _('回答正确') }}",
    score: "{{ _('累计得分') }}", pass_line: "{{ _('及格') }}", placeholder: "{{ _('问问这门课的内容…') }}",
    send: "{{ _('发送') }}", scope_course: "{{ _('本课程') }}", scope_all: "{{ _('全部知识库') }}",
    pick_course: "{{ _('选择一门课继续') }}", title_ask: "{{ _('问问小源') }}", title_exam: "{{ _('课程考核') }}"
  };
</script>
<script src="{{ url_for('static', filename='js/course-buddy.js') }}" defer></script>
{% endif %}
```
(补充原型中其余文案到同一字典;JS 内禁止出现裸中文 UI 串。)

**at_sidebar 挂载:** 在 `{% macro at_sidebar(...) %}` 的 `{% endmacro %}`(约 346 行)前加 `{% include 'components/at_course_buddy.html' %}`。宏以 `with context` 导入,`current_user` 可用;若某页以无 context 方式导入,模板检查会暴露,改为 `with context`。

**独立页补挂:** `knowledge/at_course_player.html`、`approval/at_detail.html`、`user/at_person_affiliation.html`、`user/at_person_ai.html` 在 `</body>` 前 `{% include 'components/at_course_buddy.html' %}`(先 `grep -n "at_sidebar" <file>` 确认它们确实没调用宏,避免重复挂载;JS 里 `if (window.__cbLoaded) return;` 防重)。

**验证:** 模板全量解析检查通过;本地起服务(见 Task 15 启动方式)打开任一 AT 页,小源出现、可拖动吸附、侧栏展开跟随;控制台无错。

**提交:** `git add app/static/css/course-buddy.css app/static/js/course-buddy.js app/templates/components/at_course_buddy.html app/templates/components/at_sidebar.html app/templates/approval/at_detail.html app/templates/user/at_person_affiliation.html app/templates/user/at_person_ai.html && git commit -m "feat(course-buddy): 小源组件全 AT 页挂载(拖动吸附/提问/考核面板)"`

---

### Task 13: 课程播放器接入 + 课程内检索范围

**Files:**
- Modify: `app/templates/knowledge/at_course_player.html`
- Modify: `app/templates/knowledge/at_course_quiz.html` 对应路由 `course_quiz_page`(`app/views/knowledge_wiki.py`)
- Modify: `app/views/knowledge_wiki.py` `query_endpoint`(支持 `course_key`)

**Steps:**
1. 删除播放器右上 `#cpExam` 按钮及 `cpCheckExam/cpUnlockExam` 与其 click 拦截 IIFE(约 101-106 行与 268-289 行)。
2. 在播放器页 `cpRender(idx)` 末尾调用 `window.CourseBuddy && CourseBuddy.onPage(idx)`;页面加载后 `CourseBuddy.setCourse({key: COURSE_KEY, title, totalPages: cpTotal})`;`cpFrame` 内的 `pointerdown/keydown` 转发 `CourseBuddy.activity()`(同源 iframe,`try{}` 包裹;跨域包课件失败则只靠外层与翻页事件)。
3. `course_quiz_page` 改为 `return redirect(url_for('knowledge_wiki.play_course', course_key=course_key))`;保留 `quiz/questions`、`quiz/submit` 旧 API 不动(无引用后再清理,本期不删)。
4. `query_endpoint`:若 `data.get('course_key')`,把检索限定到该课析出文章(`InteractiveCourse.article_id` 对应文章的 topic/slug:先读 `querier.query_wiki` 签名,若无文章过滤参数,则在 `topic` 为空时传该课 `topic`,并在结果 `deck_pages` 中只保留该课)。最小实现即可,不改 querier 内部。
5. 浏览器验证:打开课程 → 小源头顶显示「阅读 x%」;连续翻页约 required 秒后解锁(本地可临时把该课 `min_read_seconds` 设 30 加速,验后改回 NULL);考核答题、关闭、刷新续答。
6. 提交:`git commit -am "feat(course-buddy): 课程播放器接入阅读计时 + 旧考核入口下线 + 课程内提问范围"`

---

### Task 14: 题库管理页(admin / HR)

**Files:**
- Modify: `app/views/learning.py`
- Create: `app/templates/knowledge/at_course_bank.html`
- Modify: `app/templates/knowledge/at_wiki.html`(课程卡 ⋮ 菜单加「题库管理」,仅 `can_manage_bank`)

**权限:** `def _can_manage_bank(): return current_user.role in ('admin', 'ceo', 'hr_manager', 'hr')`(先 `psql -d pma_local -Atc "select distinct role from users"` 确认 HR 实际角色名并照填)。

**路由:**
| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/wiki/play/<key>/bank` | 页面(首次访问调 `S.import_legacy_json`) |
| GET | `/api/learning/<key>/bank` | `{health, questions:[to_admin_dict + stats{n_first, correct_first, empirical, suspicious}], min_read_seconds, auto_read_seconds, generating}` |
| POST | `/api/learning/<key>/bank/generate` | `{plan?, replace?}` → 起线程 `generator.run_generation_job`;同课已有运行中任务返回 409(模块级 `_RUNNING = set()`) |
| PUT | `/api/learning/<key>/bank/<qid>` | 编辑(题干/选项/答案/解析/难度/status),`origin='edited'` |
| POST | `/api/learning/<key>/bank/<qid>/regenerate` | 同步调用 `generator.regenerate_one` 覆盖该题内容,`status='review'` |
| POST | `/api/learning/<key>/bank/approve-all` | 全部 review → active |
| POST | `/api/learning/<key>/settings` | `{min_read_seconds}`(空=自动) |

**stats 查询**(首次作答):对 `TrainingQuizAttempt`(`course_slug=key, module_slug='bank'`)按 `(user_id, question_id)` 取最早一条,再按 `question_id` 聚合 `count / sum(is_correct)`;用一条 SQL(`DISTINCT ON (user_id, question_id) ... ORDER BY user_id, question_id, attempted_at`)。

**页面:** AT 风格(参照 `knowledge/at_wiki.html` 的头部/卡片结构与 `components/at_filter_panel.html`):顶部统计卡(总数、易/中/难、题型、待审、理论总分 + 不足 100 红色告警、达标阅读时长输入框);筛选(难度/题型/状态/页);表格列:题干(截断)、题型、标注难度(下拉可改)、AI 复核难度、实测(仅样本≥10,偏差高亮 + 「采纳」按钮)、状态、操作(编辑弹窗 / 停用恢复 / AI 重出)。编辑弹窗复用 `components/at_action_modal.html` 的样式模式(先读其用法)。

**验证:** 以 admin 登录本地,对一门课点「生成题库」(真实调用 AI,小规模 plan `{1:5,2:3,3:2}` 先试),收到站内通知,列表出现题目、存在待审;编辑、停用、采纳流程可用;以普通销售账号访问 `/wiki/play/<key>/bank` → 403。

**提交:** `git commit -am "feat(course-exam): 题库管理页(生成/审题/编辑/停用/重出/实测难度采纳)"`

---

### Task 15: 成绩汇总页

**Files:** Modify `app/views/learning.py`;Create `app/templates/knowledge/at_learning_report.html`;Modify `at_sidebar.html` 无需改(从知识库页顶部加入口链接即可,`at_wiki.html` 加按钮)

**可见范围:** admin/ceo/HR 全部活跃用户;其他人 = 自己 + `Affiliation.viewer_id == current_user.id` 的 `owner_id`(直属下属)。查询:`CourseLearningProgress` 全量按可见用户过滤 + HTML 课程列表。

**矩阵格子状态:** 无记录/未解锁=灰 + 阅读%(按课 pages 计算,课 pages 用 `_get_course_pages` 缓存);解锁未及格=黄 + 分数;及格=绿;满分=金。点格子 → 侧滑明细:阅读有效时长、答题数、正确率、反复错题 Top5(同一 question_id 错 ≥2 次)。

**验证:** admin 看到全部;以一个有下属的经理账号(`psql` 查 affiliations 选一个)只看到自己 + 下属。

**提交:** `git commit -am "feat(course-exam): 学习成绩汇总页(课程×学员矩阵 + 明细)"`

---

### Task 16: 个人开关 + i18n + 文档登记

**Steps:**
1. 小源面板头部加「⋯」菜单 → 「隐藏小源」(调用 `POST /api/learning/buddy/toggle {enabled:false}` 后移除 DOM);个人页(`user/at_person_ai.html` 或个人资料页,先 `grep -rn "个人设置\|偏好" app/templates/user/` 定位)加「显示学习伙伴」开关恢复。
2. 提取翻译:
```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib
../../venv/bin/pybabel extract -F babel.cfg -k _l -o messages.pot . && ../../venv/bin/pybabel update -i messages.pot -d app/translations
```
在 `app/translations/en/LC_MESSAGES/messages.po` 补全本功能新增条目的英文(搜 `#, fuzzy` 与空 msgstr,只处理本功能条目),`pybabel compile -d app/translations`。不提交 `messages.pot`。
3. `CLAUDE-JS-TOOLS.md`:快速索引表加 `course-buddy.js` 一行 + 详细文档(模板见项目 CLAUDE.md「文档更新模板」)。`CLAUDE-TW-COMPONENTS.md`:加 `components/at_course_buddy.html` 用法与挂载规则。
4. 模板全量解析检查。
5. 提交:`git commit -am "feat(course-buddy): 个人显示开关 + 中英文案 + 组件文档登记"`

---

### Task 17: E2E 验证(Python Playwright,本地实例)

**启动本地实例**(参照 memory「本机 5097/5098 本地测试实例」;禁用 run.py、禁用 nohup):
```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib
lsof -i :5097 -sTCP:LISTEN   # 若已有旧实例占用,先确认是哪个目录的进程再决定是否停
DATABASE_URL=postgresql://nijie@localhost:5432/pma_local PMA_DB_TYPE=sp8d FORCE_LOCAL_STORAGE=true \
  ../../venv/bin/python -c "from scripts.temp._report_flow_testkit import make_app; make_app().run(port=5097, use_reloader=False)" &
```
(若 5097 已被其它 worktree 实例占用,改用 5096,并告知用户。)

**Create:** `tests/e2e_course_buddy.py`(参考原型阶段 scratchpad 的 e2e.py 结构),覆盖:
1. 登录测试账号 → 打开课程播放器(该课临时 `min_read_seconds=20`)→ 小源显示「阅读 x%」,考核 tab 禁用。
2. 翻遍所有页 + 等待达标 → 气泡「解锁」、考核 tab 可用。
3. 答一题 → 关闭面板 → 刷新 → 打开 → 同题同选项顺序(或同一结果态)。
4. 用 DB 把分数设 58 → 答对一题 → 出现及格庆祝条;设 98 → 答对 → 满分,考核 tab 消失。
5. 拖动吸附左右、侧栏展开跟随、拖出边缘藏起、点击弹回。
6. 390×844 视口面板为底部抽屉;暗色模式截图。
7. 普通账号访问题库页 403;`exam/current` 响应 JSON 不含 `answer`。
8. 收集 `pageerror` 与 console error,必须为空。

结束:把该课 `min_read_seconds` 还原 NULL;删除测试账号的 `course_learning_progress` 与 `training_quiz_attempt(module_slug='bank')` 记录。

**提交:** `git add tests/e2e_course_buddy.py && git commit -m "test(course-buddy): 端到端验证脚本"`

---

### Task 18: 收尾

1. 全量回归:`pytest tests/test_course_exam_logic.py tests/test_course_exam_generator.py -q`;两个集成脚本;模板解析检查;E2E。
2. `@superpowers:requesting-code-review` 自审 diff(重点:判分不泄露、权限、迁移幂等、计时防伪造)。
3. 向用户汇报并等待确认部署(不自动部署;部署走 `pma-deploy` skill,仅 CN;部署后按 memory 处理 `create_all` 抢建表:迁移已写成幂等,正常 `flask db upgrade` 即可)。
4. 上线后操作清单(给管理员):逐课「生成题库」→ 审待审 → 确认健康检查通过。
