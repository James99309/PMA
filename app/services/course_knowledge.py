# -*- coding: utf-8 -*-
"""把互动课件(deck)逐页讲解析出成带"页锚点"的 Markdown,注册进 Wiki 文章库。

deck → 知识库化:每页(label + speaker-notes)→ Markdown 一节,节末带深链
/wiki/play/<key>#N。这样同一份知识:互动课件能学、文章库能搜/读、问答能引,
且都能跳进课件对应页(deck 认初始 hash)。
"""
import logging
import re
from datetime import datetime

from app import db
from app.models.knowledge import KnowledgeWikiArticle
from app.services.wiki import storage
from app.services.wiki.paths import ensure_wiki_structure

logger = logging.getLogger(__name__)

# 析出文章用固定标识,便于重复析出时 update 而非重复建
DECK_COMPILE_MODEL = 'deck-extract'


def _two_gram_blob(text):
    """把文本切成 FTS 友好 token(英文/数字 + 中文 2-gram),去重空格拼接。
    对齐 querier._tokenize_query 的 2-gram 查询策略,让文档侧能被中文查询命中。"""
    toks = []
    for m in re.findall(r'[A-Za-z][A-Za-z0-9_\-]*|\d[\w\-]*', text):
        if len(m) >= 2:
            toks.append(m.lower())
    for run in re.findall(r'[一-鿿]{2,}', text):
        for i in range(len(run) - 1):
            toks.append(run[i:i + 2])
    return ' '.join(dict.fromkeys(toks))


def relevant_pages(question, pages, top=3):
    """按 2-gram 重叠给每页(label+notes)对问题打分,返回最相关的几页 [(page_1based, label)]。"""
    qset = set(_two_gram_blob(question or '').split())
    if not qset or not pages:
        return []
    scored = []
    for i, p in enumerate(pages, 1):
        text = (p.get('label') or '') + ' ' + (p.get('notes') or '')
        pset = set(_two_gram_blob(text).split())
        score = len(qset & pset)
        if score > 0:
            scored.append((score, i, (p.get('label') or '').strip()))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [(i, lbl) for _s, i, lbl in scored[:top]]


def deck_to_markdown(course, pages):
    """把 [{label, notes}] 逐页拼成带页锚点深链的 Markdown。"""
    key = course['key']
    title = course.get('title') or key
    out = [f"# {title} · 课件知识", "",
           f"> 本文由互动课件《{title}》逐页讲解析出(共 {len(pages)} 页)。"
           f"每节末尾可点击跳到课件对应页查看演示。", ""]
    for i, p in enumerate(pages, 1):
        label = (p.get('label') or f'第{i}页').strip()
        notes = (p.get('notes') or '').strip()
        out.append(f"## {i}. {label}")
        out.append("")
        if notes:
            out.append(notes)
            out.append("")
        out.append(f"[▶ 课件第{i}页]( /wiki/play/{key}#{i} )".replace('( ', '(').replace(' )', ')'))
        out.append("")
    return "\n".join(out)


def ingest_course_knowledge(course, pages, topic, owner_id, scope='company'):
    """把 deck 析出的 Markdown 写成 Wiki 文章(已存在则 update)。返回文章。"""
    if not pages:
        raise ValueError('课件无逐页内容,无法析出知识')
    ensure_wiki_structure()
    key = course['key']
    slug = (key + '-deck')[:200]
    base_title = course.get('title') or key
    # 产品名:从 subtitle 取(如 "PNR2100 · 互动演示" → "PNR2100")
    product = ((course.get('subtitle') or '').split('·')[0]).strip()
    title = (f"{product} · {base_title} · 课件知识").strip(' ·') if product \
        else f"{base_title} · 课件知识"
    content = deck_to_markdown(course, pages)
    # 摘要里塞产品名 + 各页要点标签 —— 全文检索只搜 title+summary,
    # 标签本身就是「两张网/DMR·生命线/4G·频率自由/NetFlex/资质合规」这些关键词。
    _skip = {'封面', '谢谢', ''}
    key_labels = [(p.get('label') or '').strip() for p in pages
                  if (p.get('label') or '').strip() not in _skip]
    # 再从正文抽高价值关键词塞进 summary(全文检索只搜 title+summary,
    # 卡片只显 2 行、关键词在下面不碍观感,但能被搜到)
    all_text = ' '.join((p.get('notes') or '') for p in pages)
    _TERMS = ['数据中心', '覆盖', '衰减', '配电室', '发电机房', '机柜', 'DMR', '4G', 'LTE',
              'AES', '加密', 'DAS', '光纤', '远端', '直放站', '频率', '集群', 'NetFlex',
              '网关', '合规', 'IMDA', '频谱', '案例', 'SLA', '对讲', '专网', '公网', '安全']
    present = [t for t in _TERMS if t in all_text]
    human = ((f"{product}:" if product else '')
             + '、'.join(key_labels[:16])
             + (('。关键词:' + '、'.join(present)) if present else '')
             + f"。互动课件《{base_title}》逐页讲解析出,可搜可问,每节可跳课件对应页。")
    # FTS 补偿:wiki 中文检索是 2-gram,但 PG simple 把中文整段当一个 token,
    # 两边对不上 → 把关键词/标签/正文预切成 2-gram 拼进 summary 尾部,
    # 让文档 token 与查询 2-gram 对齐(卡片只显 2 行,这段藏在下面)。
    blob = _two_gram_blob(' '.join(key_labels) + ' ' + ' '.join(present) + ' ' + all_text)
    # ||| 之后是 FTS 补偿碎词,前端显示时截断只显人读部分(检索仍用整段)
    summary = human + ' ||| ' + blob
    now = datetime.utcnow()

    file_path = storage.write_article(topic, slug, content)
    art = KnowledgeWikiArticle.query.filter_by(topic=topic, slug=slug).first()
    if art:
        art.title = title
        art.file_path = file_path
        art.summary = summary
        art.content_length = len(content)
        art.last_compiled_at = now
        art.compile_model = DECK_COMPILE_MODEL
    else:
        art = KnowledgeWikiArticle(
            topic=topic, slug=slug, title=title, file_path=file_path,
            summary=summary, content_length=len(content),
            source_raw_ids=[], outbound_refs=[],
            last_compiled_at=now, compile_model=DECK_COMPILE_MODEL,
            scope=scope, owner_id=owner_id, owner_department=None,
            image_manifest=None,
        )
        db.session.add(art)
    db.session.commit()
    logger.info('[deck-extract] %s → 文章 %s/%s (id=%s)', key, topic, slug, art.id)
    return art
