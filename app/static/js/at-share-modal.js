/**
 * AT 共享设置 modal 控制(客户/项目共用)
 * ──────────────────────────────────────────────────
 * 配对模板:components/at_share_modal.html
 *
 * 全局 API:
 *   atOpenShareModal({
 *     entityType, entityId, saveUrl,
 *     shareEnabled, selectedUserIds, usersTree
 *   })
 *   atSubmitShareForm(modalId)
 */
(function (g) {
  'use strict';
  var MODAL_ID = 'atShareModal';
  var State = { saveUrl: '', selected: new Set(), flatUsers: [] };

  function $(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g,
      function (c) { return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c]; });
  }

  // 把 users_tree 扁平化:[{user_id, name, path}]
  function flattenTree(nodes, parentPath) {
    parentPath = parentPath || '';
    var out = [];
    (nodes || []).forEach(function (n) {
      var path = parentPath ? parentPath + ' / ' + n.name : n.name;
      if (n.type === 'user' && n.user_id) {
        out.push({ user_id: n.user_id, name: n.name, path: parentPath || '' });
      }
      if (n.children && n.children.length) {
        out = out.concat(flattenTree(n.children, path));
      }
    });
    return out;
  }

  function renderChips() {
    var p = MODAL_ID + '__';
    var box = $(p + 'chips');
    var count = $(p + 'selectedCount');
    if (count) count.textContent = State.selected.size;
    if (!box) return;
    box.innerHTML = '';
    State.selected.forEach(function (uid) {
      var u = State.flatUsers.find(function (x) { return x.user_id === uid; });
      var name = u ? u.name : ('#' + uid);
      var chip = document.createElement('span');
      chip.className = 'at-share-chip';
      chip.innerHTML = esc(name) +
        '<button type="button" title="移除" data-uid="' + uid + '">✕</button>';
      box.appendChild(chip);
    });
    box.querySelectorAll('button[data-uid]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        State.selected.delete(parseInt(btn.dataset.uid));
        renderChips();
        renderList(($(p + 'search') || {}).value || '');
      });
    });
  }

  function renderList(filter) {
    var p = MODAL_ID + '__';
    var box = $(p + 'list');
    if (!box) return;
    var term = (filter || '').trim().toLowerCase();
    var items = State.flatUsers.filter(function (u) {
      if (!term) return true;
      return (u.name || '').toLowerCase().indexOf(term) >= 0 ||
             (u.path || '').toLowerCase().indexOf(term) >= 0;
    });
    if (!items.length) {
      box.innerHTML = '<div style="padding:32px;text-align:center;color:var(--ink-4);font-size:12.5px;">' +
        (term ? '未找到匹配的用户' : '暂无可共享的用户') + '</div>';
      return;
    }
    box.innerHTML = items.map(function (u) {
      var checked = State.selected.has(u.user_id);
      return '<div class="at-share-row ' + (checked ? 'is-selected' : '') + '" data-uid="' + u.user_id + '">' +
        '<div style="width:16px;height:16px;border-radius:4px;border:1.5px solid ' +
          (checked ? 'var(--accent)' : 'var(--line-2)') + ';background:' +
          (checked ? 'var(--accent)' : 'transparent') + ';display:inline-flex;align-items:center;justify-content:center;flex-shrink:0;">' +
          (checked ? '<svg width="9" height="6" viewBox="0 0 9 6"><path d="M1 3l2.5 2L8 1" fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>' : '') +
        '</div>' +
        '<div style="flex:1;min-width:0;">' +
          '<div style="font-size:13px;color:var(--ink);">' + esc(u.name) + '</div>' +
          (u.path ? '<div class="at-dim" style="font-size:11px;color:var(--ink-3);">' + esc(u.path) + '</div>' : '') +
        '</div></div>';
    }).join('');
    box.querySelectorAll('.at-share-row').forEach(function (row) {
      row.addEventListener('click', function () {
        var uid = parseInt(row.dataset.uid);
        if (State.selected.has(uid)) State.selected.delete(uid);
        else State.selected.add(uid);
        renderChips();
        renderList(($(p + 'search') || {}).value || '');
      });
    });
  }

  function toggleUsersWrap(enabled) {
    var p = MODAL_ID + '__';
    var wrap = $(p + 'usersWrap');
    if (wrap) wrap.style.display = enabled ? 'block' : 'none';
  }

  g.atOpenShareModal = function (cfg) {
    cfg = cfg || {};
    var modal = $(MODAL_ID);
    if (!modal) { console.error('[at-share-modal] modal not found:', MODAL_ID); return; }
    var p = MODAL_ID + '__';

    State.saveUrl = cfg.saveUrl || '';
    State.flatUsers = flattenTree(cfg.usersTree || []);
    State.selected = new Set((cfg.selectedUserIds || []).map(function (x) { return parseInt(x); }));

    var enabledChk = $(p + 'enabled');
    enabledChk.checked = !!cfg.shareEnabled;
    toggleUsersWrap(enabledChk.checked);
    if (!enabledChk.dataset.bound) {
      enabledChk.dataset.bound = '1';
      enabledChk.addEventListener('change', function () { toggleUsersWrap(enabledChk.checked); });
    }

    var searchInp = $(p + 'search');
    if (searchInp) {
      searchInp.value = '';
      if (!searchInp.dataset.bound) {
        searchInp.dataset.bound = '1';
        searchInp.addEventListener('input', function () { renderList(searchInp.value); });
      }
    }

    renderChips();
    renderList('');
    modal.style.display = 'flex';
  };

  g.atSubmitShareForm = async function (modalId) {
    var p = modalId + '__';
    var body = {
      share_enabled: $(p + 'enabled').checked,
      shared_with_users: Array.from(State.selected)
    };
    var btn = $(modalId + '_submit');
    var oldHtml = btn.innerHTML;
    btn.disabled = true; btn.innerHTML = '保存中…';
    try {
      var csrf = (document.querySelector('meta[name="csrf-token"]') || {}).content || '';
      var resp = await fetch(State.saveUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
        body: JSON.stringify(body)
      });
      var res = await resp.json();
      if (!res.success) {
        if (g.ATToast) ATToast.error(res.message || '保存失败');
        btn.disabled = false; btn.innerHTML = oldHtml;
        return;
      }
      if (g.ATToast) ATToast.success('已保存', '刷新中…');
      setTimeout(function () { location.reload(); }, 400);
    } catch (e) {
      if (g.ATToast) ATToast.error('网络错误,请重试');
      btn.disabled = false; btn.innerHTML = oldHtml;
    }
  };
})(window);
