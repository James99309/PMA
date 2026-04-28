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
    brand = get_setting('brand_name', 'Evertac')
    results = {}
    for market, query_text in queries.items():
        try:
            from app.services.geo_monitor_service import call_proxy
            import re
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
                    js = re.sub(r'^```(?:json)?\s*|\s*```$', '',
                                full_text.split('```json')[-1].split('```')[0].strip())
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
