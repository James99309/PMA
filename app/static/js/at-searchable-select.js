/**
 * AT 可搜索下拉(combobox)控制器
 *
 * DOM 由 at_searchable_select 宏渲染。本 JS 自动扫描 .at-ss 元素并绑定。
 *
 * API:
 *   ATSearchableSelect.init()           扫描全页绑定(自动在 DOMContentLoaded 调一次)
 *   ATSearchableSelect.getValue(id)     读取某个 ss 的当前 value
 *   ATSearchableSelect.setValue(id, v)  设置 value(自动同步 input + onchange)
 *   ATSearchableSelect.refresh(id, items)  动态替换数据(items: [{value, label, keywords?}])
 */
(function () {
  'use strict';

  function escapeHtml(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  }

  function bind(root) {
    if (root.dataset.atSsBound) return;
    root.dataset.atSsBound = '1';

    const display = root.querySelector('.at-ss-display');
    const hidden  = root.querySelector('.at-ss-value');
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

    let activeIdx = -1;
    let query = '';
    let open = false;

    const filtered = () => {
      const q = (query || '').toLowerCase().trim();
      if (!q) return items;
      return items.filter(it => {
        const lbl = String(it.label || '').toLowerCase();
        const kw  = String(it.keywords || '').toLowerCase();
        return lbl.includes(q) || kw.includes(q);
      });
    };

    function _positionPanel() {
      // 跟随 input wrap 的 viewport 位置定位(避开 overflow 裁剪)
      const r = wrap.getBoundingClientRect();
      panel.style.left  = r.left + 'px';
      panel.style.top   = (r.bottom + 4) + 'px';
      panel.style.width = r.width + 'px';
      // 若下方空间不够,翻到上方
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
      }
    }

    // 滚动 / 缩放时重定位
    function _onViewportChange() {
      if (open) _positionPanel();
    }
    window.addEventListener('scroll', _onViewportChange, true);  // capture 阶段捕获嵌套滚动
    window.addEventListener('resize', _onViewportChange);

    // 只切换高亮背景,不重建 DOM(避免鼠标交互期间 DOM 被替换导致 click 链断裂)
    function _updateHighlight() {
      const curVal = hidden.value;
      listEl.querySelectorAll('[data-ss-pick]').forEach(b => {
        const i = parseInt(b.dataset.ssPick);
        const it = filtered()[i];
        if (!it) return;
        const isSelected = String(it.value) === String(curVal);
        const isActive = i === activeIdx;
        b.style.background = isActive
          ? 'var(--bg-hover)'
          : (isSelected ? 'var(--accent-tint)' : 'transparent');
      });
    }

    function render() {
      const list = filtered();
      const curVal = hidden.value;
      if (!list.length) {
        listEl.innerHTML = '';
        emptyEl.style.display = 'block';
        return;
      }
      emptyEl.style.display = 'none';
      listEl.innerHTML = list.map((it, i) => {
        const isSelected = String(it.value) === String(curVal);
        const isActive = i === activeIdx;
        const bg = isActive ? 'var(--bg-hover)' : (isSelected ? 'var(--accent-tint)' : 'transparent');
        const fg = isSelected ? 'var(--accent)' : 'var(--ink)';
        return `
          <button type="button" data-ss-pick="${i}"
                  style="display:flex;align-items:center;gap:8px;width:100%;
                         padding:8px 10px;border:0;background:${bg};color:${fg};
                         font:inherit;text-align:left;border-radius:4px;cursor:pointer;
                         transition:background 80ms;">
            <span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
                         font-weight:${isSelected ? '500' : '400'};">${highlight(it.label, query)}</span>
            ${isSelected ? '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>' : ''}
          </button>`;
      }).join('');
      // 绑定 — 用 mousedown 直接 pick(避免 click 链被 render() 重建打断 + 避免
      // Safari 下 mousedown.preventDefault 吞 click 的边界情况)
      listEl.querySelectorAll('[data-ss-pick]').forEach(btn => {
        btn.addEventListener('mousedown', (e) => {
          e.preventDefault(); // 阻止 input blur
          e.stopPropagation();
          const idx = parseInt(btn.dataset.ssPick);
          const it = filtered()[idx];
          if (it) pick(it);
        });
        // mouseenter 只切换高亮,不重建 DOM — 否则鼠标按下瞬间 DOM 被替换会断 click 链
        btn.addEventListener('mouseenter', () => {
          activeIdx = parseInt(btn.dataset.ssPick);
          _updateHighlight();
        });
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
      hidden.value = it.value;
      display.value = it.label;
      query = '';
      setOpen(false);
      // 清除按钮显示
      clearBtn.style.display = it.value ? 'inline-flex' : 'none';
      fireChange();
    }

    function clearVal() {
      hidden.value = '';
      display.value = '';
      query = '';
      clearBtn.style.display = 'none';
      display.focus();
      fireChange();
    }

    function fireChange() {
      const handler = root.dataset.onchange;
      if (handler) {
        try {
          // eslint-disable-next-line no-new-func
          (new Function(handler))();
        } catch (e) { console.error(e); }
      }
      // 同时派一个 native event
      hidden.dispatchEvent(new Event('change', { bubbles: true }));
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
      if (!open) setOpen(true);
    });

    display.addEventListener('blur', () => {
      // 延迟关闭让 click 能触发(panel 已移到 body,要排除它内部的焦点)
      setTimeout(() => {
        const active = document.activeElement;
        if (!root.contains(active) && !panel.contains(active)) {
          // 若输入框失焦后值与已选不一致,恢复显示
          const cur = items.find(it => String(it.value) === String(hidden.value));
          display.value = cur ? cur.label : '';
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

    // 外部点击关闭(panel 现在挂在 body 末尾,不在 root 内 — 要单独检查)
    document.addEventListener('mousedown', (e) => {
      if (open && !root.contains(e.target) && !panel.contains(e.target)) {
        setOpen(false);
      }
    });

    function scrollActive() {
      const btn = listEl.querySelector(`[data-ss-pick="${activeIdx}"]`);
      if (btn) btn.scrollIntoView({ block: 'nearest' });
    }

    // 暴露给外部的 setter
    root._atSsSet = (val) => {
      const it = items.find(i => String(i.value) === String(val));
      if (it) pick(it); else clearVal();
    };
    root._atSsRefresh = (newItems) => {
      items = newItems || [];
      root._atSsItems = items;
      dataEl.textContent = JSON.stringify(items);
      // 若当前 value 不在新 items 里 → 清空
      if (!items.find(i => String(i.value) === String(hidden.value))) {
        clearVal();
      } else {
        const cur = items.find(i => String(i.value) === String(hidden.value));
        display.value = cur ? cur.label : '';
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

  // 自动初始化
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => init());
  } else {
    init();
  }
})();
