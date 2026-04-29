# GEO Monitor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a GEO monitoring module in PMA that tracks Evertac's visibility in AI search engines across CN/EN markets.

**Architecture:** New Flask Blueprint `geo_monitor` integrated into PMA. Uses Mac Mini proxy (`https://100.110.41.83:8317`) with Anthropic's `web_search_20250305` tool to perform real-time web-search queries. Results stored in PostgreSQL, displayed in 4 Tailwind pages.

**Tech Stack:** Flask Blueprint, SQLAlchemy, Flask-Migrate, Tailwind + Alpine.js, `schedule` lib (existing), `requests` (existing)

---

## Context

- Design doc: `docs/plans/2026-04-28-geo-monitor-design.md`
- PMA templates use Tailwind (`tw_*.html`), Alpine.js for interactivity
- Blueprints registered in `app/__init__.py`
- Scheduled tasks use `schedule` lib — see `app/utils/scheduled_tasks.py`
- Proxy tested and working: `https://100.110.41.83:8317`, Bearer `sgnas-pma`, tool `web_search_20250305`
- SSL cert is self-signed — use `verify=False` in requests

---

## Task 1: Database Models

**Files:**
- Create: `app/models/geo_monitor.py`

**Step 1: Write the model file**

```python
from app.extensions import db
from datetime import datetime


class GeoIntent(db.Model):
    __tablename__ = 'geo_intent'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    frequency = db.Column(db.String(20), default='daily')  # daily / weekly
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    queries = db.relationship('GeoQuery', backref='intent', lazy='dynamic', cascade='all, delete-orphan')


class GeoQuery(db.Model):
    __tablename__ = 'geo_query'
    id = db.Column(db.Integer, primary_key=True)
    intent_id = db.Column(db.Integer, db.ForeignKey('geo_intent.id'), nullable=False)
    market = db.Column(db.String(10), nullable=False)   # cn / en / my / id ...
    query_text = db.Column(db.Text, nullable=False)
    excluded = db.Column(db.Boolean, default=False)
    results = db.relationship('GeoResult', backref='query', lazy='dynamic', cascade='all, delete-orphan')


class GeoResult(db.Model):
    __tablename__ = 'geo_result'
    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.Integer, db.ForeignKey('geo_query.id'), nullable=False)
    run_at = db.Column(db.DateTime, default=datetime.utcnow)
    mentioned = db.Column(db.String(20))    # yes / no / indirect
    rank = db.Column(db.Integer)            # None = not mentioned
    sentiment = db.Column(db.String(20))    # positive / neutral / negative
    ai_response = db.Column(db.Text)        # full AI answer text
    cited_urls = db.Column(db.JSON)         # list of cited URLs
    error = db.Column(db.Text)              # if run failed


class GeoSettings(db.Model):
    __tablename__ = 'geo_settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text)
```

**Step 2: Add import to `app/models/__init__.py`**

Find the existing model imports and add:
```python
from app.models.geo_monitor import GeoIntent, GeoQuery, GeoResult, GeoSettings
```

**Step 3: Create migration**

```bash
cd /Users/nijie/Documents/PMA
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && flask db migrate -m "add geo monitor tables"
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && flask db upgrade
```

Expected: 4 new tables created — `geo_intent`, `geo_query`, `geo_result`, `geo_settings`

**Step 4: Seed default settings**

```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib && python3 -c "
from app import create_app, db
from app.models.geo_monitor import GeoSettings
app = create_app()
with app.app_context():
    defaults = [
        ('markets_enabled', 'cn,en'),
        ('proxy_url', 'https://100.110.41.83:8317'),
        ('proxy_token', 'sgnas-pma'),
        ('brand_name', 'Evertac'),
    ]
    for key, value in defaults:
        if not GeoSettings.query.filter_by(key=key).first():
            db.session.add(GeoSettings(key=key, value=value))
    db.session.commit()
    print('Settings seeded.')
"
```

**Step 5: Commit**

```bash
git add app/models/geo_monitor.py app/models/__init__.py migrations/
git commit -m "feat: add geo_monitor database models and migration"
```

---

## Task 2: GEO Service Layer

**Files:**
- Create: `app/services/geo_monitor_service.py`

**Step 1: Write the service file**

```python
import requests
import json
import logging
import urllib3
from app.models.geo_monitor import GeoSettings, GeoQuery, GeoResult, GeoIntent
from app.extensions import db
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)


def get_setting(key, default=None):
    s = GeoSettings.query.filter_by(key=key).first()
    return s.value if s else default


def call_proxy(messages, tools=None):
    """Call Mac Mini proxy with optional web_search tool."""
    url = get_setting('proxy_url') + '/v1/messages'
    token = get_setting('proxy_token')
    payload = {
        'model': 'claude-sonnet-4-6-20251101',
        'max_tokens': 2048,
        'messages': messages,
    }
    if tools:
        payload['tools'] = tools
    r = requests.post(
        url,
        headers={
            'Authorization': f'Bearer {token}',
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
        },
        json=payload,
        verify=False,
        timeout=90,
    )
    r.raise_for_status()
    return r.json()


def generate_queries(intent_title, markets):
    """Ask Claude to generate natural language queries for each market."""
    market_labels = {'cn': '简体中文', 'en': 'English', 'my': 'Bahasa Melayu', 'id': 'Bahasa Indonesia'}
    market_list = ', '.join([f"{m}({market_labels.get(m, m)})" for m in markets])
    prompt = f"""For the following product research intent, generate one natural search query per market.
Intent: {intent_title}
Markets: {market_list}

Return ONLY a JSON object like:
{{"cn": "query in Chinese", "en": "query in English"}}

Use natural language that a buyer in each market would actually type."""

    resp = call_proxy([{'role': 'user', 'content': prompt}])
    text = next((b['text'] for b in resp.get('content', []) if b.get('type') == 'text'), '{}')
    # Strip markdown code blocks if present
    text = text.strip().strip('```json').strip('```').strip()
    return json.loads(text)


def run_query(query: GeoQuery, brand_name='Evertac'):
    """Execute one GeoQuery against the proxy and save a GeoResult."""
    try:
        prompt = f"""{query.query_text}

After searching, analyze the results and answer:
1. Is "{brand_name}" mentioned in the response? (yes/no/indirect)
2. If yes, what rank/position is it among recommendations? (1, 2, 3... or null)
3. Sentiment of the mention? (positive/neutral/negative or null)

End your response with a JSON block:
```json
{{"mentioned": "yes|no|indirect", "rank": 1, "sentiment": "positive|neutral|negative"}}
```"""

        tools = [{'type': 'web_search_20250305', 'name': 'web_search'}]
        resp = call_proxy([{'role': 'user', 'content': prompt}], tools=tools)

        # Extract text and cited URLs
        full_text = ''
        cited_urls = []
        for block in resp.get('content', []):
            if block.get('type') == 'text':
                full_text += block.get('text', '')
            elif block.get('type') == 'web_search_tool_result':
                for item in block.get('content', []):
                    if item.get('type') == 'web_search_result' and item.get('url'):
                        cited_urls.append(item['url'])

        # Parse JSON analysis from end of response
        analysis = {'mentioned': 'no', 'rank': None, 'sentiment': None}
        if '```json' in full_text:
            json_str = full_text.split('```json')[-1].split('```')[0].strip()
            try:
                analysis = json.loads(json_str)
            except Exception:
                pass

        result = GeoResult(
            query_id=query.id,
            run_at=datetime.utcnow(),
            mentioned=analysis.get('mentioned', 'no'),
            rank=analysis.get('rank'),
            sentiment=analysis.get('sentiment'),
            ai_response=full_text,
            cited_urls=cited_urls,
        )
        db.session.add(result)
        db.session.commit()
        return result

    except Exception as e:
        logger.error(f"GEO run_query error for query {query.id}: {e}")
        result = GeoResult(query_id=query.id, run_at=datetime.utcnow(), error=str(e))
        db.session.add(result)
        db.session.commit()
        return result


def run_intent(intent: GeoIntent):
    """Run all enabled queries for an intent."""
    results = []
    brand = get_setting('brand_name', 'Evertac')
    for q in intent.queries.filter_by(excluded=False).all():
        results.append(run_query(q, brand))
    return results


def run_all_due():
    """Run all enabled intents (called by scheduler)."""
    for intent in GeoIntent.query.filter_by(enabled=True).all():
        run_intent(intent)
```

**Step 2: Commit**

```bash
git add app/services/geo_monitor_service.py
git commit -m "feat: add geo_monitor service layer with proxy integration"
```

---

## Task 3: Flask Blueprint

**Files:**
- Create: `app/routes/geo_monitor.py`

**Step 1: Write the blueprint**

```python
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, Response, stream_with_context
from flask_login import login_required, current_user
from app.models.geo_monitor import GeoIntent, GeoQuery, GeoResult, GeoSettings
from app.extensions import db
from app.services.geo_monitor_service import generate_queries, run_intent, run_query, get_setting, call_proxy
import json
import logging

logger = logging.getLogger(__name__)
geo_monitor_bp = Blueprint('geo_monitor', __name__)


def get_enabled_markets():
    val = get_setting('markets_enabled', 'cn,en')
    return [m.strip() for m in val.split(',') if m.strip()]


@geo_monitor_bp.route('/')
@login_required
def dashboard():
    intents = GeoIntent.query.order_by(GeoIntent.created_at.desc()).all()
    markets = get_enabled_markets()
    # Build summary: for each intent, latest result per market
    summary = []
    for intent in intents:
        row = {'intent': intent, 'markets': {}}
        for q in intent.queries.filter_by(excluded=False).all():
            latest = q.results.order_by(GeoResult.run_at.desc()).first()
            row['markets'][q.market] = latest
        summary.append(row)
    return render_template('geo_monitor/tw_dashboard.html',
                           active_page='geo_monitor', summary=summary, markets=markets)


@geo_monitor_bp.route('/intents/')
@login_required
def intent_list():
    intents = GeoIntent.query.order_by(GeoIntent.created_at.desc()).all()
    markets = get_enabled_markets()
    return render_template('geo_monitor/tw_intents.html',
                           active_page='geo_monitor', intents=intents, markets=markets)


@geo_monitor_bp.route('/intents/add', methods=['POST'])
@login_required
def intent_add():
    title = request.form.get('title', '').strip()
    frequency = request.form.get('frequency', 'daily')
    excluded = request.form.getlist('exclude_markets')
    if not title:
        flash('请输入意图内容', 'error')
        return redirect(url_for('geo_monitor.intent_list'))
    markets = get_enabled_markets()
    intent = GeoIntent(title=title, frequency=frequency)
    db.session.add(intent)
    db.session.flush()
    # Generate queries via Claude
    active_markets = [m for m in markets if m not in excluded]
    try:
        queries = generate_queries(title, active_markets)
        for market, text in queries.items():
            db.session.add(GeoQuery(intent_id=intent.id, market=market, query_text=text))
        for m in excluded:
            db.session.add(GeoQuery(intent_id=intent.id, market=m, query_text='', excluded=True))
    except Exception as e:
        logger.error(f"generate_queries failed: {e}")
        flash(f'生成查询失败: {e}', 'error')
        db.session.rollback()
        return redirect(url_for('geo_monitor.intent_list'))
    db.session.commit()
    flash('已添加监控意图', 'success')
    return redirect(url_for('geo_monitor.intent_list'))


@geo_monitor_bp.route('/intents/<int:intent_id>/delete', methods=['POST'])
@login_required
def intent_delete(intent_id):
    intent = GeoIntent.query.get_or_404(intent_id)
    db.session.delete(intent)
    db.session.commit()
    flash('已删除', 'success')
    return redirect(url_for('geo_monitor.intent_list'))


@geo_monitor_bp.route('/intents/<int:intent_id>/run', methods=['POST'])
@login_required
def intent_run(intent_id):
    intent = GeoIntent.query.get_or_404(intent_id)
    run_intent(intent)
    flash(f'已完成跑批: {intent.title}', 'success')
    return redirect(url_for('geo_monitor.dashboard'))


@geo_monitor_bp.route('/results/<int:result_id>')
@login_required
def result_detail(result_id):
    result = GeoResult.query.get_or_404(result_id)
    return render_template('geo_monitor/tw_result_detail.html',
                           active_page='geo_monitor', result=result)


@geo_monitor_bp.route('/test/')
@login_required
def test_page():
    markets = get_enabled_markets()
    return render_template('geo_monitor/tw_test.html',
                           active_page='geo_monitor', markets=markets)


@geo_monitor_bp.route('/test/run', methods=['POST'])
@login_required
def test_run():
    """Run a one-off test query, return JSON."""
    title = request.json.get('title', '').strip()
    selected_markets = request.json.get('markets', get_enabled_markets())
    if not title:
        return jsonify({'error': '请输入意图'}), 400
    try:
        queries = generate_queries(title, selected_markets)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    brand = get_setting('brand_name', 'Evertac')
    results = {}
    for market, query_text in queries.items():
        q = GeoQuery(intent_id=0, market=market, query_text=query_text)
        q.id = 0  # temp, not persisted
        # call directly without saving
        try:
            from app.services.geo_monitor_service import call_proxy
            import urllib3
            urllib3.disable_warnings()
            prompt = f"""{query_text}

After searching, analyze: Is "{brand}" mentioned? If yes, rank and sentiment.
End with:
```json
{{"mentioned": "yes|no|indirect", "rank": 1, "sentiment": "positive|neutral|negative"}}
```"""
            resp = call_proxy([{'role': 'user', 'content': prompt}],
                              [{'type': 'web_search_20250305', 'name': 'web_search'}])
            full_text = ''
            cited_urls = []
            for block in resp.get('content', []):
                if block.get('type') == 'text':
                    full_text += block.get('text', '')
                elif block.get('type') == 'web_search_tool_result':
                    for item in block.get('content', []):
                        if item.get('url'):
                            cited_urls.append(item['url'])
            analysis = {'mentioned': 'no', 'rank': None, 'sentiment': None}
            if '```json' in full_text:
                try:
                    js = full_text.split('```json')[-1].split('```')[0].strip()
                    analysis = json.loads(js)
                except Exception:
                    pass
            results[market] = {
                'query_text': query_text,
                'mentioned': analysis.get('mentioned', 'no'),
                'rank': analysis.get('rank'),
                'sentiment': analysis.get('sentiment'),
                'ai_response': full_text,
                'cited_urls': cited_urls,
            }
        except Exception as e:
            results[market] = {'error': str(e), 'query_text': query_text}
    return jsonify({'results': results})


@geo_monitor_bp.route('/settings/', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        for key in ['markets_enabled', 'proxy_url', 'proxy_token', 'brand_name']:
            val = request.form.get(key, '').strip()
            s = GeoSettings.query.filter_by(key=key).first()
            if s:
                s.value = val
            else:
                db.session.add(GeoSettings(key=key, value=val))
        db.session.commit()
        flash('设置已保存', 'success')
        return redirect(url_for('geo_monitor.settings'))
    all_markets = ['cn', 'en', 'my', 'id', 'th', 'vn', 'ph']
    enabled = get_enabled_markets()
    settings_data = {s.key: s.value for s in GeoSettings.query.all()}
    return render_template('geo_monitor/tw_settings.html',
                           active_page='geo_monitor',
                           all_markets=all_markets,
                           enabled_markets=enabled,
                           settings=settings_data)
```

**Step 2: Register blueprint in `app/__init__.py`**

Find the blueprint registration block and add:
```python
from app.routes.geo_monitor import geo_monitor_bp
# ...
app.register_blueprint(geo_monitor_bp, url_prefix='/geo')
```

**Step 3: Commit**

```bash
git add app/routes/geo_monitor.py app/__init__.py
git commit -m "feat: add geo_monitor blueprint and routes"
```

---

## Task 4: Navigation Entry

**Files:**
- Modify: `app/templates/components/tw_nav_menu.html`

**Step 1: Find the product_analysis nav entry**

Locate this line:
```html
<a class="..." href="{{ url_for('product_analysis.tw_analysis') }}">
```

**Step 2: Add GEO Monitor entry immediately after it**

```html
<a class="flex items-center gap-3 px-3 py-2 rounded-lg {% if active_page == 'geo_monitor' %}bg-primary/20 dark:bg-primary/30{% else %}hover:bg-slate-100 dark:hover:bg-slate-800{% endif %}" href="{{ url_for('geo_monitor.dashboard') }}">
    <span class="material-symbols-outlined text-xl">travel_explore</span>
    <span class="text-sm font-medium">GEO 监控</span>
</a>
```

**Step 3: Commit**

```bash
git add app/templates/components/tw_nav_menu.html
git commit -m "feat: add geo_monitor nav entry in product section"
```

---

## Task 5: Templates — Base Structure

**Files:**
- Create: `app/templates/geo_monitor/` (directory)
- Create 4 template files

All templates follow this standard PMA Tailwind header (copy from `product_analysis/tw_analysis.html` head section, change title).

**Template: `tw_dashboard.html`**

```html
{% from 'components/tw_layout.html' import render_tw_layout with context %}
<!DOCTYPE html>
<html lang="{{ session.get('language', 'zh') }}">
<head>
    <script>document.documentElement.classList.add(localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'))</script>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>GEO 监控 - PMA</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <script src="/static/vendor/tailwind/tailwind.forms.min.js"></script>
    <script defer src="{{ url_for('static', filename='vendor/alpine/alpine.min.js') }}"></script>
    <script>tailwind.config = { darkMode: "class", theme: { extend: { colors: { "primary": "#137fec" } } } }</script>
</head>
<body class="bg-background-light dark:bg-background-dark">
{% call(slot) render_tw_layout(active_page='geo_monitor') %}
{% if slot == 'content' %}
<div class="p-6 space-y-6">

    <!-- Header -->
    <div class="flex items-center justify-between">
        <h1 class="text-2xl font-bold text-slate-900 dark:text-white">GEO 监控</h1>
        <a href="{{ url_for('geo_monitor.test_page') }}"
           class="px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary/90">
            手动测试
        </a>
    </div>

    <!-- Metric Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm border border-slate-200 dark:border-slate-700">
            <div class="text-slate-500 dark:text-slate-400 text-sm">监控意图数</div>
            <div class="text-3xl font-bold text-slate-900 dark:text-white mt-1">{{ summary|length }}</div>
        </div>
        {% for market in markets %}
        {% set market_results = [] %}
        {% for row in summary %}
            {% if row.markets.get(market) %}{% set _ = market_results.append(row.markets[market]) %}{% endif %}
        {% endfor %}
        {% set mentioned_count = market_results | selectattr('mentioned', 'equalto', 'yes') | list | length %}
        {% set rate = (mentioned_count / market_results|length * 100)|int if market_results else 0 %}
        <div class="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm border border-slate-200 dark:border-slate-700">
            <div class="text-slate-500 dark:text-slate-400 text-sm">{{ market|upper }} 提及率</div>
            <div class="text-3xl font-bold mt-1 {% if rate >= 50 %}text-green-600{% elif rate > 0 %}text-yellow-500{% else %}text-red-500{% endif %}">
                {{ rate }}%
            </div>
        </div>
        {% endfor %}
    </div>

    <!-- Results Table -->
    <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
        <div class="px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
            <h2 class="font-semibold text-slate-900 dark:text-white">最近跑批结果</h2>
            <a href="{{ url_for('geo_monitor.intent_list') }}" class="text-sm text-primary hover:underline">管理查询</a>
        </div>
        <table class="w-full text-sm">
            <thead class="bg-slate-50 dark:bg-slate-700/50">
                <tr>
                    <th class="px-6 py-3 text-left text-slate-600 dark:text-slate-300 font-medium">意图</th>
                    {% for market in markets %}
                    <th class="px-4 py-3 text-center text-slate-600 dark:text-slate-300 font-medium">{{ market|upper }}</th>
                    {% endfor %}
                    <th class="px-4 py-3 text-center text-slate-600 dark:text-slate-300 font-medium">操作</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
            {% for row in summary %}
            <tr class="hover:bg-slate-50 dark:hover:bg-slate-700/30">
                <td class="px-6 py-4 text-slate-900 dark:text-white">{{ row.intent.title }}</td>
                {% for market in markets %}
                {% set r = row.markets.get(market) %}
                <td class="px-4 py-4 text-center">
                    {% if r %}
                        {% if r.mentioned == 'yes' %}
                            <span class="inline-flex items-center gap-1 text-green-600 font-medium">
                                ✅ {% if r.rank %}#{{ r.rank }}{% endif %}
                            </span>
                        {% elif r.mentioned == 'indirect' %}
                            <span class="text-yellow-500">⚠️ 间接</span>
                        {% else %}
                            <span class="text-red-500">❌ 未提及</span>
                        {% endif %}
                    {% else %}
                        <span class="text-slate-400">—</span>
                    {% endif %}
                </td>
                {% endfor %}
                <td class="px-4 py-4 text-center">
                    <form method="POST" action="{{ url_for('geo_monitor.intent_run', intent_id=row.intent.id) }}" class="inline">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                        <button type="submit" class="text-primary hover:underline text-sm">跑批</button>
                    </form>
                </td>
            </tr>
            {% else %}
            <tr><td colspan="{{ markets|length + 2 }}" class="px-6 py-12 text-center text-slate-400">
                还没有监控意图，<a href="{{ url_for('geo_monitor.intent_list') }}" class="text-primary hover:underline">去添加</a>
            </td></tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endif %}
{% endcall %}
</body>
</html>
```

**Template: `tw_intents.html`**

```html
{% from 'components/tw_layout.html' import render_tw_layout with context %}
<!DOCTYPE html>
<html lang="{{ session.get('language', 'zh') }}">
<head>
    <script>document.documentElement.classList.add(localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'))</script>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>查询管理 - GEO 监控</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <script src="/static/vendor/tailwind/tailwind.forms.min.js"></script>
    <script defer src="{{ url_for('static', filename='vendor/alpine/alpine.min.js') }}"></script>
    <script>tailwind.config = { darkMode: "class", theme: { extend: { colors: { "primary": "#137fec" } } } }</script>
</head>
<body class="bg-background-light dark:bg-background-dark">
{% call(slot) render_tw_layout(active_page='geo_monitor') %}
{% if slot == 'content' %}
<div class="p-6 space-y-6" x-data="{ showForm: false }">

    <div class="flex items-center justify-between">
        <h1 class="text-2xl font-bold text-slate-900 dark:text-white">查询管理</h1>
        <button @click="showForm = !showForm"
                class="px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium">
            + 新增意图
        </button>
    </div>

    <!-- Add Form -->
    <div x-show="showForm" x-cloak
         class="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm border border-slate-200 dark:border-slate-700">
        <h2 class="font-semibold text-slate-900 dark:text-white mb-4">新增监控意图</h2>
        <form method="POST" action="{{ url_for('geo_monitor.intent_add') }}">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            <div class="space-y-4">
                <div>
                    <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">意图描述（中文）</label>
                    <input type="text" name="title" placeholder="例：数据中心应急通讯设备推荐"
                           class="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white text-sm" required>
                </div>
                <div>
                    <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">跑批频率</label>
                    <select name="frequency" class="px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm">
                        <option value="daily">每天</option>
                        <option value="weekly">每周</option>
                    </select>
                </div>
                <div>
                    <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">排除市场（可选）</label>
                    <div class="flex gap-3">
                        {% for m in markets %}
                        <label class="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
                            <input type="checkbox" name="exclude_markets" value="{{ m }}">
                            {{ m|upper }}
                        </label>
                        {% endfor %}
                    </div>
                </div>
                <div class="flex gap-3 justify-end">
                    <button type="button" @click="showForm = false"
                            class="px-4 py-2 border border-slate-300 dark:border-slate-600 rounded-lg text-sm">取消</button>
                    <button type="submit"
                            class="px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium">保存（AI 生成查询版本）</button>
                </div>
            </div>
        </form>
    </div>

    <!-- Intent List -->
    <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
        <table class="w-full text-sm">
            <thead class="bg-slate-50 dark:bg-slate-700/50">
                <tr>
                    <th class="px-6 py-3 text-left font-medium text-slate-600 dark:text-slate-300">意图</th>
                    <th class="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-300">市场覆盖</th>
                    <th class="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-300">频率</th>
                    <th class="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-300">状态</th>
                    <th class="px-4 py-3 text-center font-medium text-slate-600 dark:text-slate-300">操作</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
            {% for intent in intents %}
            <tr class="hover:bg-slate-50 dark:hover:bg-slate-700/30">
                <td class="px-6 py-4">
                    <div class="font-medium text-slate-900 dark:text-white">{{ intent.title }}</div>
                    <div class="text-xs text-slate-400 mt-0.5 space-x-2">
                        {% for q in intent.queries.filter_by(excluded=False).all() %}
                        <span class="italic">{{ q.market }}: {{ q.query_text[:40] }}...</span>
                        {% endfor %}
                    </div>
                </td>
                <td class="px-4 py-4 text-slate-600 dark:text-slate-300">
                    {% for q in intent.queries.filter_by(excluded=False).all() %}
                    <span class="inline-block px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs mr-1">{{ q.market|upper }}</span>
                    {% endfor %}
                </td>
                <td class="px-4 py-4 text-slate-600 dark:text-slate-300">
                    {{ '每天' if intent.frequency == 'daily' else '每周' }}
                </td>
                <td class="px-4 py-4">
                    {% if intent.enabled %}
                    <span class="text-green-600 text-xs font-medium">✅ 启用</span>
                    {% else %}
                    <span class="text-slate-400 text-xs">⏸ 暂停</span>
                    {% endif %}
                </td>
                <td class="px-4 py-4 text-center">
                    <div class="flex items-center justify-center gap-3">
                        <form method="POST" action="{{ url_for('geo_monitor.intent_run', intent_id=intent.id) }}" class="inline">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                            <button type="submit" class="text-primary hover:underline text-xs">立即跑批</button>
                        </form>
                        <form method="POST" action="{{ url_for('geo_monitor.intent_delete', intent_id=intent.id) }}" class="inline"
                              onsubmit="return confirm('确认删除？')">
                            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                            <button type="submit" class="text-red-500 hover:underline text-xs">删除</button>
                        </form>
                    </div>
                </td>
            </tr>
            {% else %}
            <tr><td colspan="5" class="px-6 py-12 text-center text-slate-400">暂无监控意图</td></tr>
            {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endif %}
{% endcall %}
</body>
</html>
```

**Template: `tw_test.html`**

```html
{% from 'components/tw_layout.html' import render_tw_layout with context %}
<!DOCTYPE html>
<html lang="{{ session.get('language', 'zh') }}">
<head>
    <script>document.documentElement.classList.add(localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'))</script>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>手动测试 - GEO 监控</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <script src="/static/vendor/tailwind/tailwind.forms.min.js"></script>
    <script defer src="{{ url_for('static', filename='vendor/alpine/alpine.min.js') }}"></script>
    <script>tailwind.config = { darkMode: "class", theme: { extend: { colors: { "primary": "#137fec" } } } }</script>
</head>
<body class="bg-background-light dark:bg-background-dark">
{% call(slot) render_tw_layout(active_page='geo_monitor') %}
{% if slot == 'content' %}
<div class="p-6 max-w-4xl space-y-6"
     x-data="{
        title: '',
        markets: {{ markets | tojson }},
        selected: {{ markets | tojson }},
        loading: false,
        results: null,
        async run() {
            this.loading = true; this.results = null;
            try {
                const r = await fetch('{{ url_for('geo_monitor.test_run') }}', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json', 'X-CSRFToken': document.querySelector('meta[name=csrf-token]').content},
                    body: JSON.stringify({ title: this.title, markets: this.selected })
                });
                this.results = await r.json();
            } finally { this.loading = false; }
        }
     }">

    <h1 class="text-2xl font-bold text-slate-900 dark:text-white">手动测试</h1>

    <div class="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm border border-slate-200 dark:border-slate-700 space-y-4">
        <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">输入意图</label>
            <input type="text" x-model="title" placeholder="例：数据中心应急通讯设备推荐"
                   class="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white">
        </div>
        <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">测试市场</label>
            <div class="flex gap-4">
                {% for m in markets %}
                <label class="flex items-center gap-2 text-sm cursor-pointer">
                    <input type="checkbox" :value="'{{ m }}'" x-model="selected">
                    <span class="text-slate-700 dark:text-slate-300">{{ m|upper }}</span>
                </label>
                {% endfor %}
            </div>
        </div>
        <button @click="run()" :disabled="loading || !title"
                class="px-6 py-2 bg-primary text-white rounded-lg text-sm font-medium disabled:opacity-50">
            <span x-show="!loading">▶ 同时测试所有市场</span>
            <span x-show="loading">测试中...</span>
        </button>
    </div>

    <!-- Results -->
    <template x-if="results && results.results">
        <div class="space-y-4">
            <template x-for="(r, market) in results.results" :key="market">
                <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
                    <div class="px-6 py-3 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between bg-slate-50 dark:bg-slate-700/50">
                        <span class="font-semibold text-slate-900 dark:text-white" x-text="market.toUpperCase() + ' 结果'"></span>
                        <span x-show="r.mentioned === 'yes'" class="text-green-600 font-medium text-sm">
                            ✅ 已提及 <span x-show="r.rank" x-text="'排名 #' + r.rank"></span>
                        </span>
                        <span x-show="r.mentioned === 'indirect'" class="text-yellow-500 font-medium text-sm">⚠️ 间接提及</span>
                        <span x-show="r.mentioned === 'no'" class="text-red-500 font-medium text-sm">❌ 未提及</span>
                        <span x-show="r.error" class="text-red-500 text-sm" x-text="'错误: ' + r.error"></span>
                    </div>
                    <div class="px-6 py-4 space-y-3">
                        <div class="text-xs text-slate-400">Query: <span class="italic" x-text="r.query_text"></span></div>
                        <div class="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap leading-relaxed max-h-60 overflow-y-auto" x-text="r.ai_response"></div>
                        <template x-if="r.cited_urls && r.cited_urls.length">
                            <div>
                                <div class="text-xs font-medium text-slate-500 mb-1">引用来源:</div>
                                <template x-for="url in r.cited_urls" :key="url">
                                    <div class="text-xs text-primary truncate" x-text="url"></div>
                                </template>
                            </div>
                        </template>
                    </div>
                </div>
            </template>
        </div>
    </template>

</div>
{% endif %}
{% endcall %}
</body>
</html>
```

**Template: `tw_settings.html`**

```html
{% from 'components/tw_layout.html' import render_tw_layout with context %}
<!DOCTYPE html>
<html lang="{{ session.get('language', 'zh') }}">
<head>
    <script>document.documentElement.classList.add(localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'))</script>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>设置 - GEO 监控</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <script src="/static/vendor/tailwind/tailwind.forms.min.js"></script>
    <script>tailwind.config = { darkMode: "class", theme: { extend: { colors: { "primary": "#137fec" } } } }</script>
</head>
<body class="bg-background-light dark:bg-background-dark">
{% call(slot) render_tw_layout(active_page='geo_monitor') %}
{% if slot == 'content' %}
<div class="p-6 max-w-2xl">
    <h1 class="text-2xl font-bold text-slate-900 dark:text-white mb-6">GEO 监控设置</h1>
    <form method="POST" class="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm border border-slate-200 dark:border-slate-700 space-y-5">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

        <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">启用市场</label>
            <div class="flex flex-wrap gap-3">
                {% set market_labels = {'cn': '中文 CN', 'en': '英文 EN', 'my': '马来文 MY', 'id': '印尼文 ID', 'th': '泰文 TH', 'vn': '越南文 VN', 'ph': '菲律宾 PH'} %}
                {% for m in all_markets %}
                <label class="flex items-center gap-2 text-sm cursor-pointer">
                    <input type="checkbox" name="market_{{ m }}" value="{{ m }}"
                           {% if m in enabled_markets %}checked{% endif %}>
                    <span class="text-slate-700 dark:text-slate-300">{{ market_labels[m] }}</span>
                </label>
                {% endfor %}
            </div>
            <input type="hidden" name="markets_enabled" id="marketsHidden" value="{{ settings.get('markets_enabled', 'cn,en') }}">
            <script>
                document.querySelectorAll('input[name^="market_"]').forEach(cb => {
                    cb.addEventListener('change', () => {
                        const checked = [...document.querySelectorAll('input[name^="market_"]:checked')].map(c => c.value);
                        document.getElementById('marketsHidden').value = checked.join(',');
                    });
                });
            </script>
        </div>

        <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">品牌名称</label>
            <input type="text" name="brand_name" value="{{ settings.get('brand_name', 'Evertac') }}"
                   class="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm">
        </div>

        <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">代理地址</label>
            <input type="text" name="proxy_url" value="{{ settings.get('proxy_url', '') }}"
                   class="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm font-mono">
        </div>

        <div>
            <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">Bearer Token</label>
            <input type="password" name="proxy_token" value="{{ settings.get('proxy_token', '') }}"
                   class="w-full px-3 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-sm font-mono">
        </div>

        <div class="flex justify-end">
            <button type="submit" class="px-6 py-2 bg-primary text-white rounded-lg text-sm font-medium">保存设置</button>
        </div>
    </form>
</div>
{% endif %}
{% endcall %}
</body>
</html>
```

**Step 2: Commit**

```bash
git add app/templates/geo_monitor/
git commit -m "feat: add geo_monitor Tailwind templates (dashboard, intents, test, settings)"
```

---

## Task 6: Scheduled Task Integration

**Files:**
- Modify: `app/utils/scheduled_tasks.py`

**Step 1: Add geo monitor daily job**

At the end of `scheduled_tasks.py`, add:

```python
def run_geo_monitor_daily():
    """Run all enabled GEO Monitor intents (daily frequency)."""
    from flask import current_app
    from app import create_app, db
    from app.services.geo_monitor_service import run_all_due

    logger.info(f"[{datetime.now()}] GEO Monitor 定时跑批开始...")
    try:
        try:
            current_app._get_current_object()
            run_all_due()
        except RuntimeError:
            app = create_app()
            with app.app_context():
                run_all_due()
        logger.info(f"[{datetime.now()}] GEO Monitor 跑批完成")
    except Exception as e:
        logger.error(f"GEO Monitor 跑批失败: {e}")
```

**Step 2: Register the schedule in `start_scheduler()`**

Find the `schedule.every().day.at("01:00").do(...)` line and add after it:

```python
schedule.every().day.at("09:00").do(run_geo_monitor_daily)
```

**Step 3: Commit**

```bash
git add app/utils/scheduled_tasks.py
git commit -m "feat: add geo_monitor daily scheduled run at 09:00"
```

---

## Task 7: Smoke Test

**Step 1: Start PMA locally**

```bash
cd /Users/nijie/Documents/PMA
./start.sh
```

**Step 2: Visit these URLs and verify no 500 errors**

- `http://localhost:5000/geo/` — dashboard loads
- `http://localhost:5000/geo/intents/` — intent list loads
- `http://localhost:5000/geo/test/` — test page loads
- `http://localhost:5000/geo/settings/` — settings loads

**Step 3: Add one test intent**

On `/geo/intents/`, add: `数据中心应急通讯设备推荐`

Verify: Claude generates CN and EN query versions (may take ~10s)

**Step 4: Run the intent manually**

Click "立即跑批" — verify result appears in dashboard

**Step 5: Test manual test page**

On `/geo/test/`, enter `数据中心通讯设备` and click run

Verify: CN and EN results appear with mention analysis

**Step 6: Final commit**

```bash
git add .
git commit -m "feat: complete GEO Monitor MVP - dashboard, intents, test, settings, scheduled task"
```

---

## Summary

| Task | Files | Est. Time |
|------|-------|-----------|
| 1. DB Models | `app/models/geo_monitor.py`, migration | 15 min |
| 2. Service Layer | `app/services/geo_monitor_service.py` | 20 min |
| 3. Blueprint | `app/routes/geo_monitor.py` | 20 min |
| 4. Nav Entry | `tw_nav_menu.html` | 5 min |
| 5. Templates | 4 × `tw_*.html` | 30 min |
| 6. Scheduler | `scheduled_tasks.py` | 5 min |
| 7. Smoke Test | — | 15 min |
