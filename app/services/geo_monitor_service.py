import re
import requests
import json
import logging
import urllib3
from app.models.geo_monitor import GeoSettings, GeoQuery, GeoResult, GeoIntent
from app.extensions import db
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)

MARKET_LABELS = {
    'cn': '简体中文', 'en': 'English', 'my': 'Bahasa Melayu',
    'id': 'Bahasa Indonesia', 'th': 'ภาษาไทย', 'vn': 'Tiếng Việt', 'ph': 'Filipino'
}


def get_setting(key, default=None):
    s = GeoSettings.query.filter_by(key=key).first()
    return s.value if s else default


def get_brands():
    """Return list of brands to monitor (supports comma-separated)."""
    raw = get_setting('brand_name', 'Evertac')
    return [b.strip() for b in raw.split(',') if b.strip()]


def call_proxy(messages, web_search=True):
    """Call Mac Mini Anthropic proxy. Returns (text, cited_urls)."""
    proxy_url = get_setting('proxy_url')
    if not proxy_url:
        raise ValueError("GEO proxy_url not configured in GeoSettings")
    url = proxy_url.rstrip('/') + '/v1/messages'
    token = get_setting('proxy_token') or ''
    payload = {
        'model': 'claude-haiku-4-5-20251001',
        'max_tokens': 2048,
        'messages': messages,
    }
    if web_search:
        payload['tools'] = [{'type': 'web_search_20250305', 'name': 'web_search'}]
    r = requests.post(
        url,
        headers={
            'Authorization': f'Bearer {token}',
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
        },
        json=payload,
        verify=False,
        timeout=120,
    )
    r.raise_for_status()
    data = r.json()

    text_parts = []
    cited_urls = []
    used_search = False

    for block in data.get('content', []):
        btype = block.get('type')
        if btype == 'text':
            text_parts.append(block.get('text', ''))
        elif btype == 'server_tool_use':
            used_search = True
        elif btype == 'web_search_tool_result':
            used_search = True
            for item in block.get('content', []):
                if item.get('type') == 'web_search_result':
                    url_val = item.get('url', '')
                    title = item.get('title', '')
                    if url_val:
                        cited_urls.append({'url': url_val, 'title': title})

    logger.info(f"GEO call_proxy: web_search={'yes' if used_search else 'no (model skipped)'}, citations={len(cited_urls)}")
    return ''.join(text_parts), cited_urls


def generate_queries(intent_title, markets):
    """Ask AI to generate brand-recommendation queries for each market."""
    market_list = ', '.join([f"{m}({MARKET_LABELS.get(m, m)})" for m in markets])
    prompt = f"""For the following product intent, generate one natural brand-recommendation search query per market.

Intent: {intent_title}
Markets: {market_list}

IMPORTANT: Each query must be phrased as a request for brand/product recommendations — the kind of question where a buyer is asking "which brand" or "what do you recommend". For example:
- CN: "数据中心应急通讯设备哪个品牌好？有什么推荐？"
- EN: "What are the best brands for emergency communication equipment in data centers?"

Return ONLY a JSON object:
{{"cn": "...", "en": "..."}}"""

    text, _ = call_proxy([{'role': 'user', 'content': prompt}], web_search=False)
    text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text.strip(), flags=re.MULTILINE)
    return json.loads(text)


def _parse_brand_analysis(full_text, brands):
    """Extract brand analysis JSON from AI response. Returns (display_text, analysis_dict)."""
    display_text = full_text
    brand_analysis = {b: {'mentioned': 'no', 'rank': None, 'sentiment': None} for b in brands}

    if '```json' in full_text:
        try:
            js_raw = full_text.split('```json')[-1].split('```')[0].strip()
            parsed = json.loads(js_raw)
            if 'brands' in parsed:
                for b, v in parsed['brands'].items():
                    brand_analysis[b] = v
            elif len(brands) == 1:
                brand_analysis[brands[0]] = parsed
        except Exception:
            pass
        display_text = full_text[:full_text.rfind('```json')].strip()

    return display_text, brand_analysis


def run_query(query: GeoQuery, brands=None):
    """Execute one GeoQuery and save a GeoResult."""
    if brands is None:
        brands = get_brands()
    primary = brands[0] if brands else 'Evertac'

    try:
        brands_list = ', '.join(brands)
        brand_json_template = ', '.join(
            f'"{b}": {{"mentioned": "yes|no|indirect", "rank": null, "sentiment": "positive|neutral|negative|null"}}'
            for b in brands
        )
        prompt = f"""You MUST use the web_search tool to find current, real-world recommendations before answering. Do not rely on training knowledge alone.

A buyer asks you: "{query.query_text}"

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

        result = GeoResult(
            query_id=query.id,
            run_at=datetime.utcnow(),
            mentioned=primary_result.get('mentioned', 'no'),
            rank=primary_result.get('rank'),
            sentiment=primary_result.get('sentiment'),
            ai_response=display_text,
            cited_urls={'brands': brand_analysis, 'urls': cited_urls},
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
    brands = get_brands()
    return [run_query(q, brands) for q in intent.queries.filter_by(excluded=False).all()]


def run_all_due():
    """Run all enabled intents (called by scheduler)."""
    for intent in GeoIntent.query.filter_by(enabled=True).all():
        run_intent(intent)
