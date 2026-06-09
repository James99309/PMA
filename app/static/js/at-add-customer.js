/**
 * AT "关联客户" modal 控制
 * ──────────────────────────────────────────
 * 用法:atOpenAddCustomer(projectId)
 *
 * 配对模板:components/at_add_customer_modal.html
 * 后端:
 *   GET  /quotation/search_customers?q=&limit=20    搜索客户(权限过滤)
 *   POST /project/api/add_customer_association      建立关联
 */
(function (g) {
  'use strict';
  var MODAL_ID = 'atAddCustomerModal';
  var State = { projectId: null, timer: null };

  function $(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g,
      function (c) { return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c]; });
  }

  function render(items, term) {
    var box = $(MODAL_ID + '__results');
    if (!items.length) {
      box.innerHTML = '<div style="padding:36px 0;text-align:center;color:var(--ink-4);font-size:12.5px;">' +
        (term ? '未找到匹配的客户' : '输入关键词开始搜索') + '</div>';
      return;
    }
    box.innerHTML = items.map(function (c) {
      return '<button type="button" data-cid="' + c.id + '" ' +
        'style="display:block;width:100%;text-align:left;padding:10px 14px;background:transparent;' +
        'border:0;border-bottom:1px solid var(--line-soft);cursor:pointer;transition:background 100ms;" ' +
        'onmouseover="this.style.background=\'var(--bg-hover)\'" ' +
        'onmouseout="this.style.background=\'transparent\'">' +
          '<div style="font-size:13px;color:var(--ink);">' + esc(c.name) + '</div>' +
          (c.code || c.country ?
            '<div class="at-mono" style="font-size:11px;color:var(--ink-3);margin-top:2px;">' +
              (c.code ? esc(c.code) : '') +
              (c.code && c.country ? ' · ' : '') +
              (c.country ? esc(c.country) : '') +
            '</div>' : '') +
        '</button>';
    }).join('');
    // 绑定点击关联
    box.querySelectorAll('button[data-cid]').forEach(function (btn) {
      btn.addEventListener('click', function () { associate(parseInt(btn.dataset.cid)); });
    });
  }

  function search(term) {
    var box = $(MODAL_ID + '__results');
    if (!term || term.length < 2) {
      render([], '');
      return;
    }
    box.innerHTML = '<div style="padding:36px 0;text-align:center;color:var(--ink-4);font-size:12.5px;">搜索中…</div>';
    fetch('/quotation/search_customers?q=' + encodeURIComponent(term) + '&limit=20')
      .then(function (r) { return r.json(); })
      .then(function (res) { render((res && res.customers) || [], term); })
      .catch(function () {
        box.innerHTML = '<div style="padding:36px 0;text-align:center;color:var(--danger);font-size:12.5px;">搜索失败,请重试</div>';
      });
  }

  function associate(companyId) {
    if (!State.projectId || !companyId) return;
    var csrf = (document.querySelector('meta[name="csrf-token"]') || {}).content || '';
    fetch('/project/api/add_customer_association', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
      body: JSON.stringify({ project_id: State.projectId, company_id: companyId })
    })
      .then(function (r) { return r.json(); })
      .then(function (res) {
        if (res.success) {
          if (g.ATToast) ATToast.success('已关联客户', '刷新中…');
          setTimeout(function () { location.reload(); }, 400);
        } else {
          if (g.ATToast) ATToast.error(res.message || '关联失败');
        }
      })
      .catch(function () { if (g.ATToast) ATToast.error('网络错误,请重试'); });
  }

  // ─── 移除关联客户(由项目详情行右侧按钮触发) ───
  g.atRemoveCustomerAssoc = function (assocId, companyName) {
    if (!assocId) return;
    if (!g.ATConfirm) {
      if (g.ATToast) ATToast.error('确认组件未加载');
      return;
    }
    g.ATConfirm.show({
      title: '移除关联客户',
      message: '确认从本项目移除「' + (companyName || '该客户') + '」?\n该操作不会删除客户档案,只解除项目关联。',
      variant: 'danger', icon: 'trash',
      confirmText: '移除',
      cancelText: '取消',
      onConfirm: function () {
        var csrf = (document.querySelector('meta[name="csrf-token"]') || {}).content || '';
        fetch('/project/api/remove_customer_association/' + assocId, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf }
        })
          .then(function (r) { return r.json(); })
          .then(function (res) {
            if (res.success) {
              if (g.ATToast) ATToast.success('已移除', '刷新中…');
              setTimeout(function () { location.reload(); }, 400);
            } else {
              if (g.ATToast) ATToast.error(res.message || '移除失败');
            }
          })
          .catch(function () { if (g.ATToast) ATToast.error('网络错误,请重试'); });
      }
    });
  };

  g.atOpenAddCustomer = function (projectId) {
    State.projectId = projectId;
    var modal = $(MODAL_ID);
    if (!modal) { console.error('[at-add-customer] modal not found:', MODAL_ID); return; }
    var input = $(MODAL_ID + '__search');
    if (input) { input.value = ''; setTimeout(function () { input.focus(); }, 50); }
    render([], '');  // 重置
    modal.style.display = 'flex';

    // 绑定一次搜索监听
    if (input && !input.dataset.bound) {
      input.dataset.bound = '1';
      input.addEventListener('input', function () {
        clearTimeout(State.timer);
        var term = input.value.trim();
        State.timer = setTimeout(function () { search(term); }, 280);
      });
    }
  };
})(window);
