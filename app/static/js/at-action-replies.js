/**
 * at-action-replies.js —— AT 详情页「跟进记录」回复公共组件
 *
 * 设计(2026-07-04 按用户规格):
 *   - 单级平铺:所有回复都挂在主记录(跟进记录)下,不做二级嵌套(即使历史数据有嵌套也拍平显示)。
 *   - 输入框按需:默认不显示,点"回复"图标才出现;发送后收起。
 *   - 回复/删除用图标(免文字 i18n);删除凭服务端 can_delete。
 *   - API 前缀按 URL 自动识别(/customer/ → /customer,否则 /project),后端项目/客户共用。
 * 幂等:多次引入只初始化一次。i18n(占位/提示)取 window.atReplyI18n。
 */
(function () {
  if (window.__atActionRepliesInit) return;
  window.__atActionRepliesInit = true;

  var I18N = window.atReplyI18n || {};
  function t(k, d) { return I18N[k] || d; }
  function apiPrefix() { return location.pathname.indexOf('/customer/') !== -1 ? '/customer' : '/project'; }
  function csrf() { var m = document.querySelector('meta[name="csrf-token"]'); return m ? m.content : ''; }
  function esc(s) { var d = document.createElement('div'); d.textContent = (s == null ? '' : String(s)); return d.innerHTML; }

  var ICON_REPLY = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 14 4 9 9 4"></polyline><path d="M20 20v-7a4 4 0 0 0-4-4H4"></path></svg>';
  var ICON_TRASH = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>';

  function fmtTime(iso) {
    if (!iso) return '';
    try {
      var dt = new Date(iso), now = new Date(), diff = (now - dt) / 1000;
      if (diff < 60) return t('justNow', '刚刚');
      if (diff < 3600) return Math.floor(diff / 60) + t('minAgo', ' 分钟前');
      if (diff < 86400) return Math.floor(diff / 3600) + t('hourAgo', ' 小时前');
      var p = function (n) { return ('0' + n).slice(-2); };
      return dt.getFullYear() + '-' + p(dt.getMonth() + 1) + '-' + p(dt.getDate()) + ' ' + p(dt.getHours()) + ':' + p(dt.getMinutes());
    } catch (e) { return iso; }
  }

  // 拍平(单级):把树里所有回复收集成一个平列表,再按时间升序
  function flatten(replies, out) {
    out = out || [];
    (replies || []).forEach(function (r) {
      out.push(r);
      if (r.children && r.children.length) flatten(r.children, out);
    });
    return out;
  }

  function renderReply(rep) {
    var del = rep.can_delete
      ? '<button type="button" class="at-reply-del" data-reply-id="' + rep.id + '" title="' + esc(t('delete', '删除')) + '" style="border:0;background:transparent;color:var(--ink-4);cursor:pointer;padding:2px;display:inline-flex;" onmouseover="this.style.color=\'var(--danger)\'" onmouseout="this.style.color=\'var(--ink-4)\'">' + ICON_TRASH + '</button>'
      : '';
    return '' +
      '<div class="at-reply-item" style="padding:1px 0;">' +
        '<div style="display:flex;align-items:baseline;gap:6px;font-size:11.5px;">' +
          '<span style="font-weight:500;color:var(--ink);">' + esc(rep.owner || '—') + '</span>' +
          '<span class="at-mono" style="color:var(--ink-4);font-size:10.5px;">' + esc(fmtTime(rep.created_at)) + '</span>' +
          '<span style="flex:1;"></span>' + del +
        '</div>' +
        '<div style="font-size:12px;color:var(--ink-2);line-height:1.5;white-space:pre-wrap;word-break:break-word;">' + esc(rep.content || '') + '</div>' +
      '</div>';
  }

  function loadReplies(actionId, listEl) {
    listEl.innerHTML = '<div style="color:var(--ink-4);font-size:11px;padding:2px 0;">' + esc(t('loading', '加载中…')) + '</div>';
    return fetch(apiPrefix() + '/action/' + actionId + '/replies', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var tree = Array.isArray(data) ? data : (data.replies || data.data || []);
        var flat = flatten(tree, []);
        flat.sort(function (a, b) { return (a.created_at || '') < (b.created_at || '') ? -1 : 1; });
        listEl.innerHTML = flat.length
          ? flat.map(renderReply).join('')
          : '<div style="color:var(--ink-4);font-size:11px;padding:2px 0;">' + esc(t('noReplies', '暂无回复')) + '</div>';
        syncCount(actionId, flat.length);
      })
      .catch(function () { listEl.innerHTML = '<div style="color:var(--danger);font-size:11px;">' + esc(t('loadFail', '加载失败')) + '</div>'; });
  }

  function syncCount(actionId, n) {
    var block = document.querySelector('.at-reply-block[data-action-id="' + actionId + '"]');
    var span = block && block.querySelector('.at-reply-count');
    if (span) span.textContent = n;
  }

  function submitReply(actionId, content, panel) {
    if (!content || !content.trim()) return;
    fetch(apiPrefix() + '/action/' + actionId + '/reply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf(), 'X-Requested-With': 'XMLHttpRequest' },
      body: JSON.stringify({ content: content.trim(), parent_reply_id: null })   // 始终平级,不嵌套
    }).then(function (r) { return r.json(); }).then(function (data) {
      if (data.success) {
        var compose = panel.querySelector('.at-reply-compose');
        panel.querySelector('.at-reply-input').value = '';
        compose.setAttribute('hidden', '');
        loadReplies(actionId, panel.querySelector('.at-reply-list'));
      } else alert(data.message || t('submitFail', '提交失败'));
    }).catch(function () { alert(t('submitFail', '提交失败')); });
  }

  function deleteReply(replyId, actionId, listEl) {
    if (!confirm(t('confirmDelete', '确定删除这条回复?'))) return;
    fetch(apiPrefix() + '/action/reply/' + replyId + '/delete', {
      method: 'POST', headers: { 'X-CSRFToken': csrf(), 'X-Requested-With': 'XMLHttpRequest' }
    }).then(function (r) { return r.json(); }).then(function (data) {
      if (data.success) loadReplies(actionId, listEl); else alert(data.message || t('delFail', '删除失败'));
    }).catch(function () { alert(t('delFail', '删除失败')); });
  }

  document.addEventListener('click', function (e) {
    var toggle = e.target.closest && e.target.closest('.at-reply-toggle');
    if (toggle) {
      e.preventDefault();
      var block = toggle.closest('.at-reply-block'), panel = block.querySelector('.at-reply-panel');
      var isOpen = !panel.hasAttribute('hidden');
      if (isOpen) panel.setAttribute('hidden', '');
      else {
        panel.removeAttribute('hidden');
        if (!panel.dataset.loaded) { panel.dataset.loaded = '1'; loadReplies(toggle.dataset.actionId, panel.querySelector('.at-reply-list')); }
      }
      var caret = toggle.querySelector('.at-reply-caret'); if (caret) caret.style.transform = isOpen ? '' : 'rotate(180deg)';
      return;
    }
    // "回复"图标 → 显示/收起输入框(按需,不常驻)
    var add = e.target.closest && e.target.closest('.at-reply-add');
    if (add) {
      e.preventDefault();
      var panel2 = add.closest('.at-reply-panel'), compose = panel2.querySelector('.at-reply-compose');
      if (compose.hasAttribute('hidden')) { compose.removeAttribute('hidden'); var ta = compose.querySelector('.at-reply-input'); if (ta) ta.focus(); }
      else compose.setAttribute('hidden', '');
      return;
    }
    var submit = e.target.closest && e.target.closest('.at-reply-submit');
    if (submit) {
      e.preventDefault();
      var panel3 = submit.closest('.at-reply-panel');
      submitReply(submit.dataset.actionId, panel3.querySelector('.at-reply-input').value, panel3);
      return;
    }
    var del = e.target.closest && e.target.closest('.at-reply-del');
    if (del) {
      e.preventDefault();
      var panel4 = del.closest('.at-reply-panel');
      deleteReply(del.dataset.replyId, panel4.dataset.actionId, panel4.querySelector('.at-reply-list'));
      return;
    }
  });

  // 从仪表盘消息点击跳转:URL 带 #at-action-<id> → 滚动定位、高亮、自动展开该条回复
  function scrollToHashAction() {
    var m = (location.hash || '').match(/^#at-action-(\d+)$/);
    if (!m) return;
    var el = document.getElementById('at-action-' + m[1]);
    if (!el) return;
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    var old = el.style.background;
    el.style.transition = 'background .3s'; el.style.background = 'var(--accent-soft, rgba(59,130,246,.10))';
    setTimeout(function () { el.style.background = old || ''; }, 2200);
    var toggle = el.querySelector('.at-reply-toggle');
    if (toggle && el.querySelector('.at-reply-panel[hidden]')) toggle.click();
  }
  if (document.readyState !== 'loading') scrollToHashAction();
  else document.addEventListener('DOMContentLoaded', scrollToHashAction);
})();
