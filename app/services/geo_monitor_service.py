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
