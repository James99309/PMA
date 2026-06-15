/**
 * AT 可搜索下拉(combobox)控制器 — 支持单选 / 多选(复选框)
 *
 * DOM 由 at_searchable_select 宏渲染。本 JS 自动扫描 .at-ss 元素并绑定。
 * 多选模式:root[data-multiple="1"],提交时在 .at-ss-values 里写同名多个 hidden。
 *
 * API:
 *   ATSearchableSelect.init()           扫描全页绑定(自动在 DOMContentLoaded 调一次)
 *   ATSearchableSelect.getValue(id)     读取某个 ss 的当前 value(多选返回数组)
 *   ATSearchableSelect.setValue(id, v)  设置 value(单选;自动同步 input + onchange)
 *   ATSearchableSelect.refresh(id, items)  动态替换数据
 */
(function () {
  'use strict';

  function escapeHtml(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  }

  function bind(root) {
    if (root.dataset.atSsBound) return;
    root.dataset.atSsBound = '1';

    const multiple = root.dataset.multiple === '1';
    const fieldName = root.dataset.ssName || '';

    const display = root.querySelector('.at-ss-display');
    const hidden  = root.querySelector('.at-ss-value');        // 单选用
    const valuesWrap = root.querySelector('.at-ss-values');    // 多选用
    const panel   = root.querySelector('.at-ss-panel');
    const listEl  = root.querySelector('.at-ss-list');
    const emptyEl = root.querySelector('.at-ss-empty');
    const chev    = root.querySelector('.at-ss-chev');
    const clearBtn = root.querySelector('.at-ss-clear');
    const wrap    = root.querySelector('.at-ss-input-wrap');
    const dataEl  = root.querySelector('.at-ss-data');

    // 把 panel 移到 <body> 末尾 — 脱离任何 transform 祖先(modal-shell 用了 scale 动画
    // 会让 position:fixed 子元素相对它自己而非 viewport,导致定位错乱)
    document.body.appendChild(panel);

    let items = [];
    try { items = JSON.parse(dataEl.textContent || '[]') || []; } catch (e) { items = []; }
    root._atSsItems = items;

    // 多选已选值(字符串数组),从初始 hidden 读取
    let selected = [];
    if (multiple && valuesWrap) {
      selected = Array.from(valuesWrap.querySelectorAll('input')).map(i => i.value);
    }

    let activeIdx = -1;
    let query = '';
    let open = false;

    const isSel = (val) => multiple
      ? selected.includes(String(val))
      : String(val) === String(hidden ? hidden.value : '');

    const filtered = () => {
      const q = (query || '').toLowerCase().trim();
      if (!q) return items;
      return items.filter(it => {
        const lbl = String(it.label || '').toLowerCase();
        const kw  = String(it.keywords || '').toLowerCase();
        return lbl.includes(q) || kw.includes(q);
      });
    };

    function summaryText() {
      if (!multiple) {
        const cur = items.find(it => String(it.value) === String(hidden ? hidden.value : ''));
        return cur ? cur.label : '';
      }
      if (!selected.length) return '';
      if (selected.length === 1) {
        const it = items.find(i => String(i.value) === String(selected[0]));
        return it ? it.label : '';
      }
      return selected.length + ' 项已选';
    }

    function syncHidden() {
      if (!multiple || !valuesWrap) return;
      valuesWrap.innerHTML = selected
        .map(v => `<input type="hidden" name="${escapeHtml(fieldName)}" value="${escapeHtml(v)}">`)
        .join('');
    }

    function _positionPanel() {
      const r = wrap.getBoundingClientRect();
      panel.style.left  = r.left + 'px';
      panel.style.top   = (r.bottom + 4) + 'px';
      panel.style.width = r.width + 'px';
      const panelH = panel.offsetHeight || 280;
      const vh = window.innerHeight;
      if (r.bottom + panelH + 12 > vh && r.top > panelH + 12) {
        panel.style.top = (r.top - panelH - 4) + 'px';
      }
    }

    function setOpen(v) {
      open = !!v;
      panel.style.display = open ? 'block' : 'none';
      chev.style.transform = open ? 'rotate(180deg)' : 'rotate(0)';
      wrap.style.borderColor = open ? 'var(--accent)' : 'var(--line-2)';
      if (open) {
        activeIdx = -1;
        render();
        _positionPanel();
      } else {
        // 关闭时恢复摘要文字
        query = '';
        display.value = summaryText();
      }
    }

    function _onViewportChange() { if (open) _positionPanel(); }
    window.addEventListener('scroll', _onViewportChange, true);
    window.addEventListener('resize', _onViewportChange);

    const checkboxSvg = (checked) => checked
      ? '<span style="flex-shrink:0;width:15px;height:15px;border-radius:3px;background:var(--accent);border:1px solid var(--accent);display:inline-flex;align-items:center;justify-content:center;"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg></span>'
      : '<span style="flex-shrink:0;width:15px;height:15px;border-radius:3px;border:1px solid var(--line-2);background:var(--bg-elev);"></span>';

    function render() {
      const list = filtered();
      if (!list.length) {
        listEl.innerHTML = '';
        emptyEl.style.display = 'block';
        return;
      }
      emptyEl.style.display = 'none';
      listEl.innerHTML = list.map((it, i) => {
        const selectedNow = isSel(it.value);
        const isActive = i === activeIdx;
        const bg = isActive ? 'var(--bg-hover)' : (selectedNow && !multiple ? 'var(--accent-tint)' : 'transparent');
        const fg = it.muted ? 'var(--ink-4)' : (selectedNow ? 'var(--accent)' : 'var(--ink)');
        const lead = multiple ? checkboxSvg(selectedNow) : '';
        const trail = (!multiple && selectedNow)
          ? '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>'
          : '';
        return `
          <button type="button" data-ss-pick="${i}"
                  style="display:flex;align-items:center;gap:8px;width:100%;
                         padding:8px 10px;border:0;background:${bg};color:${fg};
                         font:inherit;text-align:left;border-radius:4px;cursor:pointer;
                         transition:background 80ms;">
            ${lead}
            <span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
                         font-weight:${selectedNow ? '500' : '400'};">${highlight(it.label, query)}</span>
            ${trail}
          </button>`;
      }).join('');
      listEl.querySelectorAll('[data-ss-pick]').forEach(btn => {
        btn.addEventListener('mousedown', (e) => {
          e.preventDefault();
          e.stopPropagation();
          const idx = parseInt(btn.dataset.ssPick);
          const it = filtered()[idx];
          if (it) pick(it);
        });
        btn.addEventListener('mouseenter', () => {
          activeIdx = parseInt(btn.dataset.ssPick);
          _updateHighlight();
        });
      });
    }

    function _updateHighlight() {
      listEl.querySelectorAll('[data-ss-pick]').forEach(b => {
        const i = parseInt(b.dataset.ssPick);
        const it = filtered()[i];
        if (!it) return;
        const selectedNow = isSel(it.value);
        const isActive = i === activeIdx;
        b.style.background = isActive
          ? 'var(--bg-hover)'
          : (selectedNow && !multiple ? 'var(--accent-tint)' : 'transparent');
      });
    }

    function highlight(text, q) {
      const safe = escapeHtml(text);
      if (!q) return safe;
      try {
        const re = new RegExp('(' + q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi');
        return safe.replace(re, '<mark style="background:var(--accent-tint);color:var(--accent);padding:0;">$1</mark>');
      } catch (e) {
        return safe;
      }
    }

    function pick(it) {
      if (multiple) {
        const v = String(it.value);
        const idx = selected.indexOf(v);
        if (idx >= 0) selected.splice(idx, 1);
        else selected.push(v);
        syncHidden();
        clearBtn.style.display = selected.length ? 'inline-flex' : 'none';
        render();              // 刷新复选框态(保持展开)
        fireChange();
      } else {
        hidden.value = it.value;
        display.value = it.label;
        query = '';
        setOpen(false);
        clearBtn.style.display = it.value ? 'inline-flex' : 'none';
        fireChange();
      }
    }

    function clearVal() {
      if (multiple) {
        selected = [];
        syncHidden();
        query = '';
        display.value = '';
        clearBtn.style.display = 'none';
        if (open) render();
      } else {
        hidden.value = '';
        display.value = '';
        query = '';
        clearBtn.style.display = 'none';
        display.focus();
      }
      fireChange();
    }

    function fireChange() {
      const handler = root.dataset.onchange;
      if (handler) {
        try { (new Function(handler))(); } catch (e) { console.error(e); }
      }
      const evtTarget = multiple ? (valuesWrap || root) : hidden;
      evtTarget.dispatchEvent(new Event('change', { bubbles: true }));
    }

    // ─── events ───
    wrap.addEventListener('mousedown', (e) => {
      if (e.target === clearBtn || clearBtn.contains(e.target)) return;
      if (!open) setOpen(true);
      display.focus();
    });

    display.addEventListener('input', () => {
      query = display.value;
      if (!open) setOpen(true);
      else render();
    });

    display.addEventListener('focus', () => {
      // 多选:聚焦时清空显示让用户直接搜索(失焦再恢复摘要)
      if (multiple) { query = ''; display.value = ''; }
      if (!open) setOpen(true);
    });

    display.addEventListener('blur', () => {
      setTimeout(() => {
        const active = document.activeElement;
        if (!root.contains(active) && !panel.contains(active)) {
          display.value = summaryText();
          setOpen(false);
        }
      }, 150);
    });

    display.addEventListener('keydown', (e) => {
      const list = filtered();
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (!open) { setOpen(true); return; }
        activeIdx = Math.min(activeIdx + 1, list.length - 1);
        render();
        scrollActive();
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (!open) { setOpen(true); return; }
        activeIdx = Math.max(activeIdx - 1, 0);
        render();
        scrollActive();
      } else if (e.key === 'Enter') {
        if (open && activeIdx >= 0) {
          e.preventDefault();
          const it = list[activeIdx];
          if (it) pick(it);
        }
      } else if (e.key === 'Escape') {
        if (open) { setOpen(false); display.blur(); }
      }
    });

    clearBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      clearVal();
    });

    document.addEventListener('mousedown', (e) => {
      if (open && !root.contains(e.target) && !panel.contains(e.target)) {
        setOpen(false);
      }
    });

    function scrollActive() {
      const btn = listEl.querySelector(`[data-ss-pick="${activeIdx}"]`);
      if (btn) btn.scrollIntoView({ block: 'nearest' });
    }

    // 暴露给外部的 setter(单选)
    root._atSsSet = (val) => {
      if (multiple) return;
      const it = items.find(i => String(i.value) === String(val));
      if (it) pick(it); else clearVal();
    };
    root._atSsRefresh = (newItems) => {
      items = newItems || [];
      root._atSsItems = items;
      dataEl.textContent = JSON.stringify(items);
      if (multiple) {
        selected = selected.filter(v => items.find(i => String(i.value) === String(v)));
        syncHidden();
        display.value = summaryText();
        clearBtn.style.display = selected.length ? 'inline-flex' : 'none';
      } else {
        if (!items.find(i => String(i.value) === String(hidden.value))) {
          clearVal();
        } else {
          const cur = items.find(i => String(i.value) === String(hidden.value));
          display.value = cur ? cur.label : '';
        }
      }
      if (open) render();
    };
  }

  function init(scope) {
    (scope || document).querySelectorAll('.at-ss').forEach(bind);
  }

  function find(id) {
    return document.querySelector(`.at-ss[data-ss-id="${id}"]`);
  }

  window.ATSearchableSelect = {
    init,
    getValue(id) {
      const root = find(id);
      if (!root) return '';
      if (root.dataset.multiple === '1') {
        const w = root.querySelector('.at-ss-values');
        return w ? Array.from(w.querySelectorAll('input')).map(i => i.value) : [];
      }
      const h = root.querySelector('.at-ss-value');
      return h ? h.value : '';
    },
    setValue(id, val) {
      const root = find(id);
      if (root && root._atSsSet) root._atSsSet(val);
    },
    refresh(id, items) {
      const root = find(id);
      if (root && root._atSsRefresh) root._atSsRefresh(items);
    },
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => init());
  } else {
    init();
  }
})();
