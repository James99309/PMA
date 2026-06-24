/**
 * AT 富文本便签 — 给任意 <textarea> 套一个所见即所得编辑器:
 *   - 框内角标图标:📎插入图片 + ⤢全屏
 *   - 图片内联真实显示,可拖拽改尺寸(span resize:both)
 *   - 内容以 HTML 存入原 textarea(隐藏,作表单值载体);旧的纯文本/Markdown 自动兼容
 *   - 粘贴:图片自动上传内联;其余按纯文本插入(防止脏 HTML)
 *
 *   ATRichNote.enhance(textareaEl|id, { uploadUrl })  → 返回控制器 ctl
 *     ctl.refresh()         从 textarea.value 重新载入编辑器(外部改了 value 后调用,如 AI 草稿)
 *     ctl.setReadonly(bool) 只读/可编辑切换
 *   ATRichNote.render(text) Markdown/纯文本 → 安全 HTML(兼容旧内容)
 *   ATRichNote.renderInto(el, text)
 */
(function (g) {
  'use strict';
  var t = (typeof g.t === 'function') ? g.t : function (s) { return s; };
  function csrf() { return (document.querySelector('meta[name="csrf-token"]') || {}).content || ''; }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }
  function $(x) { return typeof x === 'string' ? document.getElementById(x) : x; }
  function looksHtml(s) { return /<(img|div|br|span|p|b|i|a|ul|ol|li|h[1-6])[\s>/]/i.test(s || ''); }

  var _styled = false;
  function ensureStyle() {
    if (_styled) return; _styled = true;
    var css =
      '.arn-wrap{position:relative;}' +
      '.arn-editor{box-sizing:border-box;width:100%;border:1px solid var(--line-2);border-radius:10px;' +
      'padding:12px 14px;font:inherit;font-size:13px;line-height:1.7;color:var(--ink);background:var(--bg-elev);' +
      'outline:none;white-space:pre-wrap;word-break:break-word;min-height:120px;max-height:56vh;' +
      'overflow:auto;resize:vertical;}' +
      '.arn-editor:empty:before{content:attr(data-ph);color:var(--ink-4);}' +
      '.arn-editor:focus{border-color:var(--accent);}' +
      '.arn-editor[contenteditable="false"]{background:var(--bg-sunk);}' +
      '.arn-tools{position:absolute;top:7px;right:9px;display:flex;gap:4px;z-index:2;}' +
      '.arn-icon{width:28px;height:28px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;' +
      'border:0;border-radius:7px;background:var(--bg-elev);color:var(--ink-3);opacity:.85;' +
      'box-shadow:0 0 0 1px var(--line-soft);transition:opacity 100ms,color 100ms,background 100ms;}' +
      '.arn-icon:hover{opacity:1;background:var(--bg-elev-2);color:var(--ink);}' +
      '.arn-icon .material-symbols-outlined{font-size:17px;}' +
      // 内联可拉伸图片:仅横向拖拽改宽,高度按比例自动(锁定长宽比,不变形)
      '.arn-img{display:inline-block;position:relative;resize:horizontal;overflow:hidden;max-width:100%;' +
      'line-height:0;vertical-align:top;border-radius:8px;margin:4px 0;min-width:64px;}' +
      '.arn-img>img{width:100%;height:auto;display:block;}' +
      '.arn-editor[contenteditable="false"] .arn-img{resize:none;}' +
      // 全屏
      '.arn-fs{position:fixed;inset:0;z-index:3000;display:none;flex-direction:column;background:var(--bg-page);padding:18px 22px;}' +
      '.arn-fs.open{display:flex;}' +
      '.arn-fs-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;}' +
      '.arn-fs-title{font-size:15px;font-weight:600;color:var(--ink);}' +
      '.arn-fs .arn-editor{flex:1;font-size:14px;max-height:none;resize:none;}' +
      '.arn-btn{display:inline-flex;align-items:center;gap:4px;height:28px;padding:0 10px;cursor:pointer;' +
      'border:1px solid var(--line-2);border-radius:7px;background:var(--bg-elev);color:var(--ink-2);font-size:12px;line-height:1;}' +
      '.arn-btn:hover{background:var(--bg-hover);color:var(--ink);}' +
      '.arn-btn .material-symbols-outlined{font-size:16px;}' +
      '.arn-view{font-size:13px;line-height:1.7;color:var(--ink);white-space:pre-wrap;word-break:break-word;}' +
      '.arn-view img,.arn-view .arn-img{max-width:100%;border-radius:8px;margin:6px 0;}';
    var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
  }

  // HTML 白名单清洗(评论等多人可见内容防 XSS;只放行图文基本标签)
  var _ALLOWED = { B:1, I:1, U:1, EM:1, STRONG:1, A:1, BR:1, P:1, DIV:1, SPAN:1, IMG:1, UL:1, OL:1, LI:1 };
  function _safeStyle(style) {
    var out = [];
    String(style || '').split(';').forEach(function (d) {
      var i = d.indexOf(':'); if (i < 0) return;
      var k = d.slice(0, i).trim().toLowerCase(), v = d.slice(i + 1).trim();
      if (['width', 'height', 'max-width', 'object-fit', 'display', 'resize', 'overflow', 'border-radius', 'vertical-align', 'line-height'].indexOf(k) >= 0
          && !/url\s*\(|expression|javascript:/i.test(v)) out.push(k + ':' + v);
    });
    return out.join(';');
  }
  function _sanNode(node) {
    Array.prototype.slice.call(node.childNodes).forEach(function (ch) {
      if (ch.nodeType === 1) {
        if (!_ALLOWED[ch.tagName]) { while (ch.firstChild) node.insertBefore(ch.firstChild, ch); node.removeChild(ch); return; }
        Array.prototype.slice.call(ch.attributes).forEach(function (a) {
          var n = a.name.toLowerCase();
          if (n === 'class' || n === 'contenteditable' || n === 'alt' || n === 'target' || n === 'rel') return;
          if (n === 'style') { var s = _safeStyle(a.value); if (s) ch.setAttribute('style', s); else ch.removeAttribute('style'); return; }
          if (n === 'href' || n === 'src') { if (/^\s*javascript:/i.test(a.value)) ch.removeAttribute(a.name); return; }
          ch.removeAttribute(a.name);
        });
        if (ch.tagName === 'A') { ch.setAttribute('target', '_blank'); ch.setAttribute('rel', 'noopener'); }
        _sanNode(ch);
      } else if (ch.nodeType !== 3) { node.removeChild(ch); }
    });
    return node;
  }
  function sanitize(html) {
    try { var doc = new DOMParser().parseFromString('<div>' + (html || '') + '</div>', 'text/html'); return _sanNode(doc.body.firstChild).innerHTML; }
    catch (e) { return esc(html); }
  }

  // 旧内容(纯文本/Markdown)→ HTML;已是 HTML 则清洗后返回
  function render(text) {
    text = text || '';
    if (looksHtml(text)) return sanitize(text);
    var s = esc(text);
    s = s.replace(/!\[([^\]]*)\]\(([^)\s]+)\)/g, function (_m, alt, url) {
      return '<span class="arn-img" contenteditable="false"><img src="' + url + '" alt="' + alt + '"></span>';
    });
    s = s.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, function (_m, txt, url) {
      return '<a href="' + url + '" target="_blank" rel="noopener" style="color:var(--accent);">' + txt + '</a>';
    });
    return s;
  }
  function renderInto(el, text) { el = $(el); if (el) { el.classList.add('arn-view'); el.innerHTML = render(text); } }

  function imgHtml(url) {
    return '<span class="arn-img" contenteditable="false"><img src="' + url + '"></span> ';
  }

  function insertHtmlAtCaret(editor, html) {
    editor.focus();
    var ok = false;
    try { ok = document.execCommand('insertHTML', false, html); } catch (e) { ok = false; }
    if (!ok) { editor.innerHTML += html; }
  }

  function uploadAndInsert(editor, ctl, file) {
    if (!file || !/^image\//.test(file.type)) { if (g.ATToast) ATToast.error(t('仅支持图片')); return; }
    var fd = new FormData(); fd.append('file', file);
    var ph = '<span data-arn-ph="1" style="color:var(--ink-4);">[' + esc(t('上传中…')) + ']</span>';
    insertHtmlAtCaret(editor, ph);
    ctl.commit();
    fetch(ctl.uploadUrl, { method: 'POST', headers: { 'X-CSRFToken': csrf() }, body: fd })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var holder = editor.querySelector('[data-arn-ph]');
        if (d && d.success && d.data && d.data.url) {
          if (holder) { holder.outerHTML = imgHtml(d.data.url); }
          else { insertHtmlAtCaret(editor, imgHtml(d.data.url)); }
        } else {
          if (holder) holder.remove();
          if (g.ATToast) ATToast.error((d && d.message) || t('上传失败'));
        }
        ctl.commit();
      })
      .catch(function () {
        var holder = editor.querySelector('[data-arn-ph]'); if (holder) holder.remove();
        if (g.ATToast) ATToast.error(t('上传失败')); ctl.commit();
      });
  }

  function pickImage(editor, ctl) {
    var inp = document.createElement('input');
    inp.type = 'file'; inp.accept = 'image/*'; inp.style.display = 'none';
    inp.addEventListener('change', function () { if (inp.files && inp.files[0]) uploadAndInsert(editor, ctl, inp.files[0]); });
    document.body.appendChild(inp); inp.click();
    setTimeout(function () { inp.remove(); }, 1000);
  }

  function bindEditor(editor, ctl) {
    editor.addEventListener('input', function () { ctl.commit(); });
    // 粘贴:图片上传内联;其余纯文本(防脏 HTML)
    editor.addEventListener('paste', function (ev) {
      var items = (ev.clipboardData && ev.clipboardData.items) || [];
      for (var i = 0; i < items.length; i++) {
        if (items[i].type && items[i].type.indexOf('image/') === 0) {
          var f = items[i].getAsFile();
          if (f) { ev.preventDefault(); uploadAndInsert(editor, ctl, f); return; }
        }
      }
      ev.preventDefault();
      var txt = (ev.clipboardData || window.clipboardData).getData('text/plain') || '';
      insertHtmlAtCaret(editor, esc(txt).replace(/\n/g, '<br>'));
      ctl.commit();
    });
  }

  // ── 共享全屏 ──
  var fs = null, fsEditor = null, fsCtl = null;
  function ensureFs() {
    if (fs) return;
    fs = document.createElement('div'); fs.className = 'arn-fs';
    fs.innerHTML =
      '<div class="arn-fs-head"><span class="arn-fs-title"></span><div style="display:flex;gap:8px;">' +
      '<button type="button" class="arn-btn" data-fsimg><svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>' + esc(t('插入图片')) + '</button>' +
      '<button type="button" class="arn-btn" data-fsclose><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3v6H3"/><path d="M15 21v-6h6"/><path d="M3 9l6-6"/><path d="M21 15l-6 6"/></svg>' + esc(t('退出全屏')) + '</button>' +
      '</div></div><div class="arn-editor" contenteditable="true"></div>';
    document.body.appendChild(fs);
    fsEditor = fs.querySelector('.arn-editor');
    var proxy = { uploadUrl: '', commit: function () { if (fsCtl) { fsCtl.editor.innerHTML = fsEditor.innerHTML; fsCtl.commit(); } } };
    bindEditor(fsEditor, proxy);
    fs._proxy = proxy;
    fs.querySelector('[data-fsclose]').addEventListener('click', closeFs);
    fs.querySelector('[data-fsimg]').addEventListener('click', function () { if (fsCtl) pickImage(fsEditor, fs._proxy); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && fs.classList.contains('open')) closeFs(); });
  }
  function openFs(ctl) {
    ensureFs(); fsCtl = ctl; fs._proxy.uploadUrl = ctl.uploadUrl;
    fs.querySelector('.arn-fs-title').textContent = ctl.title || t('全屏编辑');
    fsEditor.innerHTML = ctl.editor.innerHTML;
    fs.classList.add('open'); setTimeout(function () { fsEditor.focus(); }, 30);
  }
  function closeFs() {
    if (!fs) return;
    if (fsCtl) { fsCtl.editor.innerHTML = fsEditor.innerHTML; fsCtl.commit(); }
    fs.classList.remove('open'); fsCtl = null;
  }

  function enhance(el, opts) {
    ensureStyle();
    el = $(el); if (!el) return null;
    opts = opts || {};
    if (el.dataset.arnEnhanced) return el._arnCtl;
    el.dataset.arnEnhanced = '1';

    var ph = el.getAttribute('placeholder') || '';
    var minH = (el.style && el.style.minHeight) || '';

    var wrap = document.createElement('div'); wrap.className = 'arn-wrap';
    // flex 行内的 composer(评论/进展):wrap 需 flex:1 占满;块级父元素忽略 flex,安全
    wrap.style.flex = '1'; wrap.style.minWidth = '0';
    el.parentNode.insertBefore(wrap, el);
    wrap.appendChild(el);
    el.style.display = 'none';   // 原 textarea 隐藏,仅作值载体

    var editor = document.createElement('div');
    editor.className = 'arn-editor';
    editor.setAttribute('contenteditable', 'true');
    if (ph) editor.setAttribute('data-ph', ph);
    if (minH) editor.style.minHeight = minH;
    editor.innerHTML = render(el.value);
    wrap.appendChild(editor);

    var tools = document.createElement('div'); tools.className = 'arn-tools';
    tools.innerHTML =
      '<button type="button" class="arn-icon" data-arn-img title="' + esc(t('插入图片')) + '"><svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg></button>' +
      '<button type="button" class="arn-icon" data-arn-fs title="' + esc(t('全屏')) + '"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 3h6v6"/><path d="M9 21H3v-6"/><path d="M21 3l-6 6"/><path d="M3 21l6-6"/></svg></button>';
    wrap.appendChild(tools);

    var ctl = {
      el: el, editor: editor, tools: tools, wrap: wrap,
      uploadUrl: opts.uploadUrl || '/worklog/api/upload-image', title: opts.title || '',
      commit: function () {
        var html = editor.innerHTML;
        if (!editor.textContent.trim() && !editor.querySelector('img')) html = '';   // 空编辑器 → 空值(兼容必填校验)
        el.value = html; el.dispatchEvent(new Event('input'));
      },
      refresh: function () { editor.innerHTML = render(el.value); },
      setReadonly: function (ro) {
        editor.setAttribute('contenteditable', ro ? 'false' : 'true');
        tools.style.display = ro ? 'none' : '';
      }
    };
    el._arnCtl = ctl;

    bindEditor(editor, ctl);
    tools.querySelector('[data-arn-img]').addEventListener('click', function () { pickImage(editor, ctl); });
    tools.querySelector('[data-arn-fs]').addEventListener('click', function () { openFs(ctl); });
    return ctl;
  }

  g.ATRichNote = { enhance: enhance, render: render, renderInto: renderInto };
})(window);
