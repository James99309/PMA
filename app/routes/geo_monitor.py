from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required
from app.models.geo_monitor import GeoIntent, GeoQuery, GeoResult, GeoSettings
from app.extensions import db
from app.services.geo_monitor_service import generate_queries, run_intent, get_setting
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
    summary = []
    for intent in intents:
        row = {'intent': intent, 'markets': {}}
        for q in intent.queries.filter_by(excluded=False).all():
            latest = q.results.order_by(GeoResult.run_at.desc()).first()
            row['markets'][q.market] = latest
        summary.append(row)
    all_markets = ['cn', 'en', 'my', 'id', 'th', 'vn', 'ph']
    enabled = get_enabled_markets()
    settings_data = {s.key: s.value for s in GeoSettings.query.all()}
    return render_template('geo_monitor/tw_dashboard.html',
                           active_page='geo_monitor', summary=summary, markets=markets,
                           all_markets=all_markets, enabled_markets=enabled, settings=settings_data)


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


@geo_monitor_bp.route('/test/')
@login_required
def test_page():
    markets = get_enabled_markets()
    return render_template('geo_monitor/tw_test.html',
                           active_page='geo_monitor', markets=markets)


@geo_monitor_bp.route('/test/run', methods=['POST'])
@login_required
def test_run():
    title = request.json.get('title', '').strip()
    selected_markets = request.json.get('markets', get_enabled_markets())
    if not title:
        return jsonify({'error': '请输入意图'}), 400
    try:
        queries = generate_queries(title, selected_markets)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    from app.services.geo_monitor_service import call_proxy, get_brands, _parse_brand_analysis
    brands = get_brands()
    primary = brands[0] if brands else 'Evertac'
    results = {}
    for market, query_text in queries.items():
        try:
            brands_list = ', '.join(brands)
            brand_json_template = ', '.join(
                f'"{b}": {{"mentioned": "yes|no|indirect", "rank": null, "sentiment": "positive|neutral|negative|null"}}'
                for b in brands
            )
            prompt = f"""You MUST use the web_search tool to find current, real-world recommendations before answering. Do not rely on training knowledge alone.

A buyer asks you: "{query_text}"

Search the web first, then answer as a knowledgeable AI assistant — recommend specific brands and products based on your search results. Be concrete and name actual brands.

Then at the very end, check whether these brands appeared in your answer: {brands_list}
Output ONLY this JSON block:
```json
{{"brands": {{{brand_json_template}}}}}
```
For each brand: mentioned=yes if directly named, indirect if implied/category mentioned, no if absent. rank=position number if listed among recommendations (1=first), else null."""
            full_text, cited_urls = call_proxy([{'role': 'user', 'content': prompt}], web_search=True)
            display_text, brand_analysis = _parse_brand_analysis(full_text, brands)
            primary_result = brand_analysis.get(primary, {'mentioned': 'no', 'rank': None, 'sentiment': None})
            results[market] = {
                'query_text': query_text,
                'mentioned': primary_result.get('mentioned', 'no'),
                'rank': primary_result.get('rank'),
                'sentiment': primary_result.get('sentiment'),
                'ai_response': display_text,
                'brand_analysis': brand_analysis,
                'cited_urls': cited_urls,
            }
        except Exception as e:
            results[market] = {'error': str(e), 'query_text': query_text}
    return jsonify({'results': results})


@geo_monitor_bp.route('/test/analyze-url', methods=['POST'])
@login_required
def analyze_url():
    """Analyze a single cited URL for GEO methods and generate suggestions."""
    data = request.json or {}
    url = data.get('url', '').strip()
    title = data.get('title', '')
    query_text = data.get('query_text', '')
    brand = data.get('brand', get_setting('brand_name', 'Evertac').split(',')[0].strip())
    if not url:
        return jsonify({'error': '缺少 URL'}), 400
    try:
        from app.services.geo_monitor_service import call_proxy
        prompt = f"""你是一位 GEO（生成式引擎优化）专家。请分析以下被 AI 引擎引用的网页，该网页在回答产品推荐类问题时被引用。

触发引用的搜索问题："{query_text}"
被引用页面：{title} — {url}

任务：
1. 使用网络搜索访问并阅读该页面的实际内容
2. 识别该页面使用了以下哪些 GEO 方法（Princeton KDD 2024 研究框架）：
   - 引用增强：直接引用专家或客户的话（可见度提升 +43%）
   - 数据统计：具体数字、数据、指标（+33%）
   - 流畅性优化：清晰自然的写作风格（+29%）
   - 引用来源：引用外部研究或报告（+28%）
   - 专业术语：正确使用行业术语（+19%）
   - 易于理解：为非专业读者提供简洁解释（+14%）
   - 权威语气：资质、认证、奖项（+12%）
   - 第三方提及：被其他行业网站引用（关键因素）

3. 针对品牌"{brand}"，给出 3-5 条具体可操作的建议，帮助复制或超越该页面的 GEO 优势。要具体——明确说明需要创建的页面类型、需要添加的数据类型、需要使用的引用格式。

请用中文回复，格式如下：
## 该页面使用的 GEO 方法
[列出你发现的方法]

## 针对 {brand} 的优化建议
[编号的具体行动建议]"""

        full_text, _ = call_proxy([{'role': 'user', 'content': prompt}], web_search=True)
        return jsonify({'analysis': full_text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@geo_monitor_bp.route('/test/generate-article', methods=['POST'])
@login_required
def generate_article():
    """Generate a GEO-optimized reference article using knowledge base + cited page analysis."""
    data = request.json or {}
    url = data.get('url', '').strip()
    query_text = data.get('query_text', '')
    analysis = data.get('analysis', '')
    brand = data.get('brand', get_setting('brand_name', 'Evertac').split(',')[0].strip())
    if not query_text:
        return jsonify({'error': '缺少查询词'}), 400
    try:
        from app.models.knowledge import KnowledgeWikiArticle
        from app.services.wiki.storage import read_article_content
        from app.services.geo_monitor_service import call_proxy
        keywords = [w for w in query_text.replace('？', ' ').replace('?', ' ').split() if len(w) > 1][:6]
        articles = []
        for kw in keywords:
            found = KnowledgeWikiArticle.query.filter(
                db.or_(
                    KnowledgeWikiArticle.title.ilike(f'%{kw}%'),
                    KnowledgeWikiArticle.summary.ilike(f'%{kw}%'),
                )
            ).limit(3).all()
            for a in found:
                if a not in articles:
                    articles.append(a)
            if len(articles) >= 5:
                break
        kb_sections = []
        kb_details = []
        for a in articles[:3]:
            content = read_article_content(a.file_path)
            if content:
                kb_sections.append(f"### {a.title}\n{content[:2000]}")
                kb_details.append({'title': a.title, 'content': content})
        kb_text = '\n\n'.join(kb_sections) if kb_sections else '（未找到相关知识库文章）'
        prompt = f"""You are a GEO (Generative Engine Optimization) content strategist for the brand "{brand}".

A buyer searched: "{query_text}"
This page was cited by an AI engine: {url}

GEO analysis of the cited page:
{analysis}

Brand knowledge base excerpts:
{kb_text}

Task: Write a GEO-optimized reference article for {brand} that:
1. Mimics the GEO strengths identified in the analysis above
2. Uses ONLY facts from the knowledge base excerpts above (do not invent specs or claims)
3. Targets the exact buyer intent: "{query_text}"
4. Incorporates: specific statistics/numbers, expert-style quotes (attributed to {brand} engineers or field experience), technical terminology, and clear structure with headers

Output a ready-to-publish article in Chinese with:
- A compelling H1 title
- 400-600 words
- Real data points from the knowledge base
- At least 2 "quote" callouts (use > blockquote markdown)
- Recommended URL slug at the very end (English, SEO-friendly)"""

        full_text, _ = call_proxy([{'role': 'user', 'content': prompt}], web_search=False)
        return jsonify({'article': full_text, 'kb_articles': kb_details})
    except Exception as e:
        logger.error(f"generate_article error: {e}")
        return jsonify({'error': str(e)}), 500


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
        return redirect(url_for('geo_monitor.dashboard'))
    all_markets = ['cn', 'en', 'my', 'id', 'th', 'vn', 'ph']
    enabled = get_enabled_markets()
    settings_data = {s.key: s.value for s in GeoSettings.query.all()}
    return render_template('geo_monitor/tw_settings.html',
                           active_page='geo_monitor',
                           all_markets=all_markets,
                           enabled_markets=enabled,
                           settings=settings_data)
