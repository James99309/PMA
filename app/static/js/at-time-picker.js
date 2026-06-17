/**
 * AT 时间选择器:单列时间列表(按间隔,默认 15 分钟)。可复用。
 * 配套 templates/components/at_time_picker.html
 *
 *   var ctl = AtTimePicker.init('wiStartTime');   // data-step 控制间隔(默认 15)
 *   ctl.getValue() → 'HH:MM' | '' ; setValue('09:30') ; clear() ; onChange(fn) ; focus()
 */
(function (g) {
  'use strict';
  function pad(n) { return String(n).padStart(2, '0'); }

  function init(rootId) {
    var root = typeof rootId === 'string' ? document.getElementById(rootId) : rootId;
    if (!root) return null;
    var trigger = root.querySelector('[data-tp-trigger]');
    var labelEl = root.querySelector('[data-tp-label]');
    var hidden = root.querySelector('[data-tp-value]');
    var menu = root.querySelector('[data-tp-menu]');
    var list = root.querySelector('[data-tp-list]');
    var step = parseInt(root.dataset.step, 10) || 15;
    var placeholder = labelEl ? labelEl.textContent : '时间';
    var sel = '';
    var api;

    // 构建单列时间列表
    var html = '';
    for (var h = 0; h < 24; h++) {
      for (var m = 0; m < 60; m += step) {
        var v = pad(h) + ':' + pad(m);
        html += '<div class="at-tp-item" data-tp-v="' + v + '">' + v + '</div>';
      }
    }
    list.innerHTML = html;

    function mark() {
      list.querySelectorAll('.at-tp-item').forEach(function (el) { el.classList.toggle('on', el.dataset.tpV === sel); });
    }
    function refreshLabel() {
      if (sel) { labelEl.textContent = sel; labelEl.classList.remove('at-tp-ph'); hidden.value = sel; }
      else { labelEl.textContent = placeholder; labelEl.classList.add('at-tp-ph'); hidden.value = ''; }
    }
    function open() { menu.hidden = false; var on = list.querySelector('.at-tp-item.on'); if (on) on.scrollIntoView({ block: 'center' }); }
    function close() { menu.hidden = true; }

    trigger.addEventListener('click', function (e) { e.stopPropagation(); menu.hidden ? open() : close(); });
    list.addEventListener('click', function (e) {
      var it = e.target.closest('[data-tp-v]'); if (!it) return;
      sel = it.dataset.tpV; mark(); refreshLabel(); close();
      if (api._onChange) api._onChange(sel);
    });
    document.addEventListener('click', function (e) { if (!root.contains(e.target)) close(); });

    api = {
      getValue: function () { return hidden.value || ''; },
      setValue: function (v) { sel = v ? v.slice(0, 5) : ''; mark(); refreshLabel(); },
      clear: function () { sel = ''; mark(); refreshLabel(); },
      onChange: function (fn) { api._onChange = fn; return api; },
      focus: function () { trigger.focus(); }
    };
    root._attp = api;
    return api;
  }
  g.AtTimePicker = { init: init };
})(window);
