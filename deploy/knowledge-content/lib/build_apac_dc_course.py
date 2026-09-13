#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the APAC data-centre PPT export as one offline HTML course."""

import argparse
import base64
import html
import json
import mimetypes
from pathlib import Path


def _data_uri(path):
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _notes_template(pages):
    sections = []
    for page in pages:
        label = html.escape(page.get("label", ""), quote=True)
        notes = html.escape(page.get("notes", ""), quote=True).replace("\n", "&#10;")
        sections.append(f'<section data-label="{label}" data-speaker-notes="{notes}"></section>')
    return "".join(sections)


def build_course_html(manifest_path, output_path):
    manifest_path = Path(manifest_path)
    output_path = Path(output_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    pages = manifest.get("pages") or []
    if not pages:
        raise ValueError("manifest must contain at least one page")

    embedded = []
    for index, page in enumerate(pages, 1):
        image_path = manifest_path.parent / page["image"]
        if not image_path.is_file():
            raise FileNotFoundError(str(image_path))
        embedded.append({
            "number": index,
            "label": page.get("label") or f"第 {index} 页",
            "notes": page.get("notes") or "",
            "src": _data_uri(image_path),
        })

    title = html.escape(manifest.get("title") or "互动课件")
    subtitle = html.escape(manifest.get("subtitle") or "")
    pages_json = json.dumps(embedded, ensure_ascii=False).replace("</", "<\\/")
    template_json = json.dumps(_notes_template(pages), ensure_ascii=False).replace("</", "<\\/")
    document = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>{title}</title>
<style>
  *{{box-sizing:border-box}} html,body{{margin:0;width:100%;height:100%;overflow:hidden;background:#071b20}}
  body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans SC",sans-serif;color:#fff}}
  #deck{{position:fixed;inset:0;display:grid;place-items:center;user-select:none}}
  .slide{{position:absolute;inset:0;display:none;align-items:center;justify-content:center;background:#071b20}}
  .slide.on{{display:flex}}
  .slide img{{display:block;width:100%;height:100%;object-fit:contain}}
  #hud{{position:fixed;right:16px;bottom:12px;padding:5px 10px;border-radius:999px;
       background:rgba(0,0,0,.55);font-size:12px;letter-spacing:.03em;backdrop-filter:blur(8px)}}
  #label{{position:fixed;left:16px;bottom:12px;max-width:70%;overflow:hidden;text-overflow:ellipsis;
         white-space:nowrap;padding:5px 10px;border-radius:999px;background:rgba(0,0,0,.55);font-size:12px}}
  #left,#right{{position:fixed;top:0;bottom:0;width:18%;border:0;background:transparent;cursor:pointer}}
  #left{{left:0}} #right{{right:0}}
  @media (max-width:700px){{#label{{display:none}} #hud{{right:8px;bottom:8px}}}}
</style>
</head>
<body aria-label="{title}">
<main id="deck" aria-live="polite"></main>
<button id="left" aria-label="上一页"></button><button id="right" aria-label="下一页"></button>
<div id="label"></div><div id="hud"></div>
<script type="__bundler/template">{template_json}</script>
<script>
const PAGES={pages_json};
const deck=document.getElementById('deck');
PAGES.forEach((p,i)=>{{
  const s=document.createElement('section'); s.className='slide'; s.dataset.page=String(i+1);
  const image=document.createElement('img'); image.src=p.src; image.alt=p.label;
  if(i===0) image.fetchPriority='high'; else image.loading='lazy';
  s.appendChild(image); deck.appendChild(s);
}});
let current=1;
function wanted(){{const m=(location.hash||'').match(/(\\d+)/);return m?Number(m[1]):1}}
function show(n,push=true){{
  current=Math.max(1,Math.min(PAGES.length,n));
  document.querySelectorAll('.slide').forEach((s,i)=>s.classList.toggle('on',i===current-1));
  document.getElementById('hud').textContent=current+' / '+PAGES.length;
  document.getElementById('label').textContent=PAGES[current-1].label;
  if(push && location.hash!=='#'+current) history.replaceState(null,'','#'+current);
}}
function step(delta){{show(current+delta)}}
document.addEventListener('keydown',e=>{{
  if(['ArrowRight','PageDown',' '].includes(e.key)){{e.preventDefault();step(1)}}
  if(['ArrowLeft','PageUp'].includes(e.key)){{e.preventDefault();step(-1)}}
  if(e.key==='Home')show(1); if(e.key==='End')show(PAGES.length);
}});
document.getElementById('left').addEventListener('click',()=>step(-1));
document.getElementById('right').addEventListener('click',()=>step(1));
window.addEventListener('hashchange',()=>show(wanted(),false));
let touchX=null;
document.addEventListener('touchstart',e=>{{touchX=e.changedTouches[0].clientX}},{{passive:true}});
document.addEventListener('touchend',e=>{{if(touchX===null)return;const d=e.changedTouches[0].clientX-touchX;if(Math.abs(d)>45)step(d<0?1:-1);touchX=null}},{{passive:true}});
show(wanted(),false);
</script>
</body>
</html>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(document, encoding="utf-8")
    return len(pages)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest")
    parser.add_argument("output")
    args = parser.parse_args()
    count = build_course_html(args.manifest, args.output)
    print(f"built {count} pages -> {args.output}")


if __name__ == "__main__":
    main()
