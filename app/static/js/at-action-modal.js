/**
 * AT 添加跟进记录 modal 控制(project / customer / contact 3 场景共用)
 * ──────────────────────────────────────────────────
 * 配对模板:components/at_action_modal.html
 *
 * 用法:
 *   atOpenActionModal({
 *     modalId: 'atActionModalProject',
 *     scope: 'project' | 'customer' | 'contact',
 *     contextId: 123,
 *     contextName: '项目名 / 客户名 / 联系人名',
 *     apiEndpoint: '/project/api/123/add_action',
 *     contactsApi: '/project/api/get_company_contacts',  // project scope only
 *     companies: [{id, name}],                            // project scope only
 *     projects:  [{id, name}],                            // customer/contact scope only
 *     contacts:  [{id, name, position}],                  // customer scope only(直接填下拉)
 *     sidebarInfo: {                                      // 可选 — 右侧信息栏
 *       title: '项目信息',
 *       items: [{label, value}, ...],
 *       list_title: '关联客户',
 *       list_items: [name1, name2, ...]
 *     }
 *   })
 */
(function (g) {
  'use strict';

  var State = {}; // 每个 modalId 一份独立 state

  function $(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g,
      function (c) { return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c]; });
  }
  function setOpts(sel, items, placeholder) {
    if (!sel) return;
    var opts = ['<option value="">' + esc(placeholder || '— 请选择 —') + '</option>'];
    (items || []).forEach(function (it) {
      var label = it.name + (it.position ? ' (' + it.position + ')' : '');
      opts.push('<option value="' + it.id + '">' + esc(label) + '</option>');
    });
    sel.innerHTML = opts.join('');
  }

  function renderSidebar(p, info) {
    var box = $(p + 'sidebar');
    if (!box) return;
    if (!info) { box.style.display = 'none'; return; }
    var html = '<h4 style="margin:0 0 6px;font-size:12px;font-weight:600;color:var(--ink);' +
               'letter-spacing:0.04em;text-transform:uppercase;">' + esc(info.title || '') + '</h4>';
    (info.items || []).forEach(function (it) {
      html += '<div>' +
        '<div class="at-dim" style="font-size:10.5px;color:var(--ink-3);margin-bottom:2px;">' + esc(it.label) + '</div>' +
        '<div style="font-size:12.5px;color:var(--ink);font-weight:500;">' + esc(it.value || '—') + '</div>' +
      '</div>';
    });
    if (info.list_items && info.list_items.length) {
      var items = info.list_items.slice(0, 3);
      html += '<div>' +
        '<div class="at-dim" style="font-size:10.5px;color:var(--ink-3);margin-bottom:2px;">' + esc(info.list_title || '') + '</div>';
      items.forEach(function (n) {
        html += '<div style="font-size:12px;color:var(--ink-2);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="' + esc(n) + '">' + esc(n) + '</div>';
      });
      if (info.list_items.length > 3) {
        html += '<div class="at-dim" style="font-size:11px;color:var(--ink-3);margin-top:2px;">+' +
                (info.list_items.length - 3) + ' 个更多</div>';
      }
      html += '</div>';
    }
    box.innerHTML = html;
    box.style.display = 'flex';
  }

  function loadCompanyContacts(p, companyId, contactsApi) {
    var sel = $(p + 'contact');
    if (!sel || !companyId) {
      if (sel) { sel.disabled = true; sel.innerHTML = '<option value="">请先选择企业</option>';
                 sel.style.background = 'var(--bg-sunk)'; sel.style.color = 'var(--ink-3)'; }
      return;
    }
    sel.disabled = true;
    sel.innerHTML = '<option value="">加载中…</option>';
    fetch(contactsApi + '/' + companyId)
      .then(function (r) { return r.json(); })
      .then(function (res) {
        var list = (res && res.data) || res.contacts || [];
        setOpts(sel, list, '— 请选择联系人 —');
        sel.disabled = false;
        sel.style.background = 'var(--bg-page)';
        sel.style.color = 'var(--ink)';
      })
      .catch(function () {
        sel.innerHTML = '<option value="">加载失败</option>';
        sel.disabled = false;
      });
  }

  g.atOpenActionModal = function (cfg) {
    cfg = cfg || {};
    var modalId = cfg.modalId;
    var modal = $(modalId);
    if (!modal) { console.error('[at-action-modal] modal not found:', modalId); return; }
    var p = modalId + '__';
    var scope = cfg.scope || 'project';

    State[modalId] = {
      scope: scope,
      apiEndpoint: cfg.apiEndpoint,
      contactsApi: cfg.contactsApi || ''
    };

    // 上下文 label
    var ctxInp = $(p + 'contextLabel');
    if (ctxInp) ctxInp.value = cfg.contextName || '';

    // 日期默认今天
    var dateInp = $(p + 'date');
    if (dateInp) dateInp.value = new Date().toISOString().split('T')[0];

    // 重置文本字段
    var commInp = $(p + 'communication');
    if (commInp) commInp.value = '';
    var sharedInp = $(p + 'isShared');
    if (sharedInp) sharedInp.checked = true;

    // 下拉填充(按 scope)
    if (scope === 'project') {
      var compSel = $(p + 'company');
      setOpts(compSel, cfg.companies, '— 请选择企业 —');
      compSel.value = '';
      // 公司变更联动联系人
      compSel.onchange = function () {
        loadCompanyContacts(p, compSel.value, State[modalId].contactsApi);
      };
      loadCompanyContacts(p, '', '');  // 重置联系人
    } else if (scope === 'contact') {
      var projSel = $(p + 'project');
      setOpts(projSel, cfg.projects, '— 请选择项目 —');
      projSel.value = '';
    } else {
      var projSelC = $(p + 'project');
      setOpts(projSelC, cfg.projects, '— 请选择项目 —');
      projSelC.value = '';
      var contSel = $(p + 'contact');
      setOpts(contSel, cfg.contacts, '— 请选择联系人 —');
      contSel.value = '';
    }

    // sidebar
    renderSidebar(p, cfg.sidebarInfo || null);

    modal.style.display = 'flex';
    setTimeout(function () { commInp && commInp.focus(); }, 100);
  };

  g.atSubmitActionForm = async function (modalId) {
    var st = State[modalId];
    if (!st) return;
    var p = modalId + '__';
    var scope = st.scope;

    var dateVal = ($(p + 'date').value || '').trim();
    var comm    = ($(p + 'communication').value || '').trim();
    if (!dateVal) { g.ATToast && ATToast.warn('无法保存', '请选择日期'); return; }
    if (!comm)    { g.ATToast && ATToast.warn('无法保存', '请填写沟通情况'); return; }

    var body = {
      date: dateVal,
      communication: comm,
      is_shared: $(p + 'isShared').checked
    };
    if (scope === 'project') {
      body.company_id = $(p + 'company').value || null;
      body.contact_id = $(p + 'contact').value || null;
    } else if (scope === 'contact') {
      body.project_id = $(p + 'project').value || null;
    } else {
      body.project_id = $(p + 'project').value || null;
      body.contact_id = $(p + 'contact').value || null;
    }

    var btn = $(modalId + '_submit');
    var oldHtml = btn.innerHTML;
    btn.disabled = true; btn.innerHTML = '保存中…';
    try {
      var csrf = (document.querySelector('meta[name="csrf-token"]') || {}).content || '';
      var resp = await fetch(st.apiEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
        body: JSON.stringify(body)
      });
      var res = await resp.json();
      if (!res.success) {
        g.ATToast && ATToast.error(res.message || '保存失败');
        btn.disabled = false; btn.innerHTML = oldHtml;
        return;
      }
      g.ATToast && ATToast.success('已保存', '刷新中…');
      setTimeout(function () { location.reload(); }, 400);
    } catch (e) {
      g.ATToast && ATToast.error('网络错误,请重试');
      btn.disabled = false; btn.innerHTML = oldHtml;
    }
  };
})(window);
