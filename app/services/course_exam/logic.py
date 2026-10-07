# -*- coding: utf-8 -*-
"""课程考核纯逻辑 —— 零 Flask/DB 依赖,便于单测。

题目在本模块里是 dict:{id, qtype, difficulty, options, answer, ...}
answer:single=int / multi=list[int] / judge=bool(均为「原始选项下标」)。
写库前须经 normalize_question 清洗。
"""
import math

POINTS = {1: 1, 2: 2, 3: 3}
PASS_SCORE = 60
FULL_SCORE = 100
QTYPES = ('single', 'multi', 'judge')


# ---------- 内部:输入清洗 ----------

def _finite_number(x):
    """转成有限 float;bool / 非数字 / NaN / inf 返回 None。"""
    if isinstance(x, bool):
        return None
    try:
        v = float(x)
    except (ValueError, TypeError, OverflowError):
        return None
    if math.isnan(v) or math.isinf(v):
        return None
    return v


def _as_int(x):
    """接受 int 或纯数字字符串(拒绝 bool / float / 其他),失败返回 None。"""
    if isinstance(x, bool):
        return None
    if isinstance(x, int):
        return x
    if isinstance(x, str) and x.strip().isdecimal():   # isdigit 会放过 '²' 致 int() 抛错
        return int(x.strip())
    return None


def norm_page_seconds(page_seconds):
    """键统一为 str(int 键合并进同名 str 键),值统一为 int >= 0。"""
    out = {}
    for k, v in (page_seconds or {}).items():
        key = str(k)
        n = _finite_number(v)
        out[key] = out.get(key, 0) + (max(0, int(n)) if n is not None else 0)
    return out


# ---------- 计分 ----------

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


# ---------- 抽题 ----------

WRONG_GAP = 5


def pick_question(bank, score, correct_ids, recent_ids, rng):
    """从题库抽一题。

    bank: active 题列表;correct_ids: 本人已答对题 id 集合;
    recent_ids: 本人最近作答的题 id,必须是有序列表(旧→新)。
    已答对的题本就被移出,所以「最近」实际等于「最近答错」:
    最近 WRONG_GAP 题内出现过的不抽;池不足时放宽,但池里多于 1 题时仍不重抽最后一题。
    """
    pool = [q for q in bank if q['id'] not in correct_ids]
    if not pool:
        return None
    recent = set(recent_ids[-WRONG_GAP:])
    fresh = [q for q in pool if q['id'] not in recent]
    if fresh:
        pool = fresh
    elif len(pool) > 1 and recent_ids:
        pool = [q for q in pool if q['id'] != recent_ids[-1]] or pool
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


# ---------- 题目清洗 / 乱序 / 判分 ----------

def normalize_question(q):
    """校验并返回清洗后的副本;不合法抛 ValueError。"""
    out = dict(q)
    qtype = out.get('qtype')
    if qtype not in QTYPES:
        raise ValueError('qtype 须为 single/multi/judge')
    d = _as_int(out.get('difficulty'))
    if d not in POINTS:
        raise ValueError('difficulty 须为 1..3')
    out['difficulty'] = d

    if qtype == 'judge':
        a = out.get('answer')
        if isinstance(a, str) and a.strip().lower() in ('true', 'false'):
            a = a.strip().lower() == 'true'
        if not isinstance(a, bool):
            raise ValueError('judge 答案须为 bool')
        out['answer'] = a
        return out

    opts = out.get('options')
    if not isinstance(opts, list) or not all(isinstance(o, str) and o.strip() for o in opts):
        raise ValueError('options 须为非空字符串列表')
    min_opts = 3 if qtype == 'multi' else 2
    if len(opts) < min_opts:
        raise ValueError('选项数量不足')
    n = len(opts)

    if qtype == 'single':
        a = _as_int(out.get('answer'))
        if a is None or not 0 <= a < n:
            raise ValueError('single 答案下标非法')
        out['answer'] = a
        return out

    raw = out.get('answer')
    if not isinstance(raw, list):
        raise ValueError('multi 答案须为列表')
    idx = set()
    for x in raw:
        i = _as_int(x)
        if i is None or not 0 <= i < n:
            raise ValueError('multi 答案下标非法')
        idx.add(i)
    if not 2 <= len(idx) < n:
        raise ValueError('multi 正确项须 ≥2 且少于选项数')
    out['answer'] = sorted(idx)
    return out


def shuffle_order(n, rng):
    order = list(range(n))
    rng.shuffle(order)
    return order


def option_order_for(q, rng):
    if q['qtype'] == 'judge':
        return None
    return shuffle_order(len(q['options']), rng)


def to_original(qtype, shown, order, n_options=None):
    """把前端提交的「显示位」换算成原始选项下标。非法输入抛 ValueError。

    order 须为 range(len(order)) 的排列;给了 n_options 时长度还须一致。
    """
    if qtype not in QTYPES:
        raise ValueError('未知题型')
    if qtype == 'judge':
        if not isinstance(shown, bool):
            raise ValueError('judge 答案须为 bool')
        return shown
    if not isinstance(order, list) or \
            any(not isinstance(i, int) or isinstance(i, bool) for i in order) or \
            sorted(order) != list(range(len(order))):
        raise ValueError('选项顺序非法')
    if n_options is not None and len(order) != n_options:
        raise ValueError('选项顺序与题目选项数不符')

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
        return set(original) == set(q['answer'])
    return original == q['answer']


# ---------- 阅读时长 ----------

CHARS_PER_SEC = 5
MIN_PAGE_SEC = 20
READ_RATIO = 0.7
PAGE_CAP_FACTOR = 3
MAX_PING_SECONDS = 20       # 前端 15s 一报,留余量


def page_estimate(page):
    return max(MIN_PAGE_SEC, len(page.get('notes') or '') // CHARS_PER_SEC)


def required_read_seconds(pages, override=None):
    if override is not None:
        return max(0, int(override))
    return int(sum(page_estimate(p) for p in pages) * READ_RATIO)


def accept_ping_seconds(seconds, elapsed):
    """服务端只认:不超过距上次上报的真实间隔(向下取整,无容差),且不超过单次上限。

    非法 seconds(非数字/NaN/inf/bool)记 0;elapsed 为 None 表示首次上报。
    """
    v = _finite_number(seconds)
    s = max(0, int(v)) if v is not None else 0
    s = min(s, MAX_PING_SECONDS)
    if elapsed is not None:
        e = _finite_number(elapsed)
        s = min(s, max(0, math.floor(e)) if e is not None else 0)
    return s


def add_page_seconds(page_seconds, page, seconds, pages):
    """page 为 1 基页号;单页累计封顶 = 该页估算 × 3。返回新 dict(键规范为 str)。"""
    ps = norm_page_seconds(page_seconds)
    if not isinstance(page, int) or isinstance(page, bool) or not 1 <= page <= len(pages):
        return ps
    v = _finite_number(seconds)
    add = max(0, int(v)) if v is not None else 0
    cap = page_estimate(pages[page - 1]) * PAGE_CAP_FACTOR
    key = str(page)
    ps[key] = min(cap, ps.get(key, 0) + add)
    return ps


def record_ping(page_seconds, pages, page, seconds, elapsed):
    """处理一次阅读上报:校验页号 → 校验时长 → 累加。返回新 dict。"""
    p = _as_int(page)
    if p is None or not 1 <= p <= len(pages):
        return norm_page_seconds(page_seconds)
    return add_page_seconds(page_seconds, p, accept_ping_seconds(seconds, elapsed), pages)


def _pages_total(page_seconds, pages):
    """只累计 "1".."len(pages)" 的页,忽略过期的多余页。"""
    ps = norm_page_seconds(page_seconds)
    return sum(ps.get(str(i), 0) for i in range(1, len(pages) + 1))


def effective_read_seconds(page_seconds, pages=None):
    if pages is not None:
        return _pages_total(page_seconds, pages)
    return sum(norm_page_seconds(page_seconds).values())


def is_unlocked(page_seconds, pages, override=None):
    if not pages:
        return False
    ps = norm_page_seconds(page_seconds)
    if any(ps.get(str(i), 0) <= 0 for i in range(1, len(pages) + 1)):
        return False
    return _pages_total(ps, pages) >= required_read_seconds(pages, override)


def read_percent(page_seconds, pages, override=None):
    """展示用阅读进度:时长进度与翻页进度取较小者,未解锁前封顶 99。

    解锁要求「时长达标 + 每页都看过」,只按时长算会出现「才看一半就 99%」的误导。
    """
    if not pages:
        return 0
    ps = norm_page_seconds(page_seconds)
    required = required_read_seconds(pages, override)
    time_pct = 100 if required <= 0 else _pages_total(ps, pages) * 100 // required
    seen = sum(1 for i in range(1, len(pages) + 1) if ps.get(str(i), 0) > 0)
    page_pct = seen * 100 // len(pages)
    return min(99, int(time_pct), page_pct)


# ---------- 题库健康 / 实测难度 ----------

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
