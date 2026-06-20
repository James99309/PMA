/**
 * AT 日期选择器:点击弹出月历(周日起 · 月份导航 · 今天)。可复用。
 * 配套 templates/components/at_date_picker.html
 *
 *   var ctl = AtDatePicker.init('wiStartDate');
 *   ctl.getValue() → 'YYYY-MM-DD' | '' ; setValue('2026-06-16') ; clear() ; onChange(fn) ; focus()
 */
(function (g) {
  'use strict';
  function pad(n) { return String(n).padStart(2, '0'); }
  function isoOf(y, m, d) { return y + '-' + pad(m + 1) + '-' + pad(d); }

  function init(rootId) {
    var root = typeof rootId === 'string' ? document.getElementById(rootId) : rootId;
    if (!root) return null;
    var trigger = root.querySelector('[data-dp-trigger]');
    var labelEl = root.querySelector('[data-dp-label]');
    var hidden = root.querySelector('[data-dp-value]');
    var menu = root.querySelector('[data-dp-menu]');
    var titleEl = root.querySelector('[data-dp-title]');
    var grid = root.querySelector('[data-dp-grid]');
    var placeholder = labelEl ? labelEl.textContent : '选择日期';
    var sel = '';                 // 已选 'YYYY-MM-DD'
    var viewY, viewM;             // 月历显示的年/月
    var api;

    function setView(y, m) { viewY = y; viewM = m; renderGrid(); }
    function refreshLabel() {
      if (sel) { labelEl.textContent = sel; labelEl.classList.remove('at-dp-ph'); hidden.value = sel; }
      else { labelEl.textContent = placeholder; labelEl.classList.add('at-dp-ph'); hidden.value = ''; }
    }
    function renderGrid() {
      titleEl.textContent = viewY + ' 年 ' + (viewM + 1) + ' 月';
      var first = new Date(viewY, viewM, 1);
      var startOffset = first.getDay();            // 周日起
      var start = new Date(viewY, viewM, 1 - startOffset);
      var todayISO = isoOf(new Date().getFullYear(), new Date().getMonth(), new Date().getDate());
      var html = '';
      var d = new Date(start);
      for (var i = 0; i < 42; i++) {
        var di = isoOf(d.getFullYear(), d.getMonth(), d.getDate());
        var cls = 'at-dp-day';
        if (d.getMonth() !== viewM) cls += ' other';
        if (di === todayISO) cls += ' today';
        if (di === sel) cls += ' on';
        html += '<button type="button" class="' + cls + '" data-dp-d="' + di + '">' + d.getDate() + '</button>';
        d.setDate(d.getDate() + 1);
      }
      grid.innerHTML = html;
    }
    function open() {
      var base = sel ? sel.split('-') : null;
      if (base) setView(+base[0], +base[1] - 1); else setView(new Date().getFullYear(), new Date().getMonth());
      menu.hidden = false;
    }
    function close() { menu.hidden = true; }

    trigger.addEventListener('click', function (e) { e.stopPropagation(); menu.hidden ? open() : close(); });
    root.querySelector('[data-dp-prev]').addEventListener('click', function (e) { e.stopPropagation(); var m = viewM - 1, y = viewY; if (m < 0) { m = 11; y--; } setView(y, m); });
    root.querySelector('[data-dp-next]').addEventListener('click', function (e) { e.stopPropagation(); var m = viewM + 1, y = viewY; if (m > 11) { m = 0; y++; } setView(y, m); });
    root.querySelector('[data-dp-today]').addEventListener('click', function (e) {
      e.stopPropagation(); var n = new Date(); sel = isoOf(n.getFullYear(), n.getMonth(), n.getDate());
      refreshLabel(); close(); if (api._onChange) api._onChange(sel);
    });
    grid.addEventListener('click', function (e) {
      var b = e.target.closest('[data-dp-d]'); if (!b) return;
      sel = b.dataset.dpD; refreshLabel(); close(); if (api._onChange) api._onChange(sel);
    });
    document.addEventListener('click', function (e) { if (!root.contains(e.target)) close(); });

    api = {
      getValue: function () { return hidden.value || ''; },
      setValue: function (v) { sel = v || ''; refreshLabel(); },
      clear: function () { sel = ''; refreshLabel(); },
      onChange: function (fn) { api._onChange = fn; return api; },
      focus: function () { trigger.focus(); }
    };
    root._atdp = api;
    return api;
  }
  g.AtDatePicker = { init: init };
})(window);
