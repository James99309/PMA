/**
 * AT 通用搜索选择器(关键词远程搜索 + 下拉)
 * ──────────────────────────────────────────────
 * 抽取自 quotation/at_view.html 的 ATSearchPicker 工厂
 *
 * 用法:
 *   ATSearchPicker({
 *     inputId, hiddenIdId, clearId, dropdownId,
 *     searchUrl(term) => 'url',         // term 长度足够时调用
 *     suggestUrl?() => 'url'|null,      // 空 term 焦点时拉建议
 *     itemsFromResp(resp) => [items],   // 把响应转成统一 item 数组
 *     renderItem(item, term) => { primary, secondary },
 *     itemName(item) => string,         // pick 时回填 input.value
 *     onPick?(item, picker), onClear?(picker),
 *     label?: '客户' | '项目'           // 无匹配文案
 *   })
 *
 * 配套模板:components/at_search_picker.html
 */
(function (g) {
  'use strict';

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g,
      function (c) { return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c]; });
  }
  function highlight(text, term) {
    var t = esc(text);
    if (!term) return t;
    var safe = String(term).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    return t.replace(new RegExp(safe, 'gi'), function (m) {
      return '<mark style="background:rgba(229,156,75,0.30);color:var(--ink);padding:0 1px;border-radius:2px;">' + m + '</mark>';
    });
  }

  function ATSearchPicker(cfg) {
    var input  = document.getElementById(cfg.inputId);
    var hidden = cfg.hiddenIdId ? document.getElementById(cfg.hiddenIdId) : null;
    var clear  = cfg.clearId ? document.getElementById(cfg.clearId) : null;
    var dd     = document.getElementById(cfg.dropdownId);
    if (!input || !dd) return null;
    var timer = null;
    var picker = { input: input, hidden: hidden, clear: clear, dd: dd, cfg: cfg };

    function position() {
      var r = input.getBoundingClientRect();
      dd.style.top   = (r.bottom + 4) + 'px';
      dd.style.left  = r.left + 'px';
      dd.style.width = r.width + 'px';
    }
    function show() { position(); dd.style.display = 'block'; }
    function hide() { dd.style.display = 'none'; }

    function render(items, term) {
      if (!items || !items.length) {
        dd.innerHTML = '<div class="at-dim" style="padding:10px;font-size:12px;">无匹配' + (cfg.label || '结果') + '</div>';
        show(); return;
      }
      dd.innerHTML = items.slice(0, 10).map(function (it, idx) {
        var r = cfg.renderItem(it, term);
        return '<div data-idx="' + idx + '" style="padding:8px 12px;cursor:pointer;font-size:12.5px;"' +
               ' onmouseenter="this.style.background=\'var(--bg-hover)\'"' +
               ' onmouseleave="this.style.background=\'transparent\'">' +
                 '<div style="color:var(--ink);">' + r.primary + '</div>' +
                 (r.secondary ? '<div class="at-dim" style="font-size:11px;margin-top:2px;">' + r.secondary + '</div>' : '') +
               '</div>';
      }).join('');
      dd.querySelectorAll('[data-idx]').forEach(function (el) {
        el.addEventListener('click', function () {
          var it = items[parseInt(el.dataset.idx)];
          pick(it);
        });
      });
      show();
    }

    function pick(item) {
      var name = cfg.itemName ? cfg.itemName(item) : item.name;
      var id   = item.id;
      input.value = name;
      if (hidden) hidden.value = id;
      if (clear)  clear.style.display = 'inline-flex';
      hide();
      if (cfg.onPick) cfg.onPick(item, picker);
    }
    function clearPick() {
      input.value = '';
      if (hidden) hidden.value = '';
      if (clear)  clear.style.display = 'none';
      hide();
      if (cfg.onClear) cfg.onClear(picker);
    }

    input.addEventListener('input', function () {
      clearTimeout(timer);
      var term = input.value.trim();
      if (!term) {
        if (cfg.suggestUrl) {
          var url = cfg.suggestUrl();
          if (url) {
            fetch(url).then(function (r) { return r.json(); })
                      .then(function (res) { render(cfg.itemsFromResp(res), ''); });
            return;
          }
        }
        hide(); return;
      }
      timer = setTimeout(function () {
        fetch(cfg.searchUrl(term))
          .then(function (r) { return r.json(); })
          .then(function (res) { render(cfg.itemsFromResp(res), term); })
          .catch(function () { hide(); });
      }, 200);
    });
    input.addEventListener('focus', function () {
      if (!input.value.trim() && cfg.suggestUrl) {
        var url = cfg.suggestUrl();
        if (url) fetch(url).then(function (r) { return r.json(); }).then(function (res) {
          render(cfg.itemsFromResp(res), '');
        });
      }
    });
    if (clear) clear.addEventListener('click', clearPick);
    window.addEventListener('scroll', function () { if (dd.style.display === 'block') position(); }, true);
    window.addEventListener('resize', function () { if (dd.style.display === 'block') position(); });
    document.addEventListener('click', function (e) {
      if (!e.target.closest('#' + cfg.inputId) && !e.target.closest('#' + cfg.dropdownId)) hide();
    });

    picker.pick = pick;
    picker.clear = clearPick;
    picker.hide = hide;
    return picker;
  }

  g.ATSearchPicker = ATSearchPicker;
  g.ATSearchPickerHighlight = highlight;
})(window);
