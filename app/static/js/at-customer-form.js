/**
 * AT 客户表单 modal 控制(创建 + 编辑共用)
 * ──────────────────────────────────────────────────
 * 配对模板:components/at_customer_modal.html
 * 字段 id 用 ${modal_id}__${name} 前缀,避免列表/详情同时存在时冲突
 *
 * 全局 API:
 *   atOpenCustomerForm(mode, companyId?)
 *   atSubmitCustomerForm(mode, modalId)
 */
(function (g) {
  'use strict';
  var State = {};  // 每个 modal_id 一份独立 state
  function modalIdFor(mode) { return (mode === 'edit') ? 'atEditCustomerModal' : 'atCreateCustomerModal'; }
  function prefixFor(modalId) { return modalId + '__'; }
  function $(id) { return document.getElementById(id); }

  function initOnce(mode, modalId) {
    var p = prefixFor(modalId);
    var st = State[modalId] = State[modalId] || {};
    if (st.optionsLoaded) return;
    st.optionsLoaded = true;

    // 选项加载(返回 {industries, company_types, sources})
    fetch('/customer/api/company/options')
      .then(function (r) { return r.json(); })
      .then(function (res) {
        if (!(res && res.success)) return;
        var opts = res.data || res;
        var sets = [
          [p + 'industry',    opts.industries    || []],
          [p + 'companyType', opts.company_types || []],
          [p + 'source',      opts.sources       || []]
        ];
        sets.forEach(function (pair) {
          var sel = $(pair[0]); if (!sel) return;
          var placeholder = sel.querySelector('option[value=""]');
          sel.innerHTML = (placeholder ? placeholder.outerHTML : '') +
            pair[1].map(function (it) {
              var code = it.code || it.value || it.key;
              var label = it.label || it.name || it.value || code;
              return '<option value="' + code + '">' + label + '</option>';
            }).join('');
        });
      })
      .catch(function () { if (g.ATToast) ATToast.error('选项加载失败'); });

    // 归属人下拉(所有活跃用户)
    fetch('/user/api/users/active')
      .then(function (r) { return r.json(); })
      .then(function (res) {
        if (!(res && res.success)) return;
        var sel = $(p + 'ownerId'); if (!sel) return;
        sel.innerHTML = '<option value="">— 请选择归属人 —</option>' +
          (res.data || []).map(function (u) {
            return '<option value="' + u.id + '">' + (u.real_name || u.username) +
                   (u.real_name ? ' (' + u.username + ')' : '') + '</option>';
          }).join('');
        // 创建态:默认当前用户(从 meta 读)
        if (mode === 'create') {
          var curUid = (document.querySelector('meta[name="current-user-id"]') || {}).content || '';
          if (curUid) sel.value = curUid;
        }
      })
      .catch(function () {});

    // ─── 创建态:AI 回填 + 查重 ──
    if (mode === 'create' && g.AiFormEnrich && !st.aiInited) {
      st.aiInited = true;
      var nameInp = $(p + 'name');
      var aiBtn   = $(p + 'aiBtn');
      function toggleAi() {
        var has = nameInp.value.trim().length > 0;
        aiBtn.disabled = !has;
        aiBtn.style.borderColor = has ? 'var(--accent)' : 'var(--line-2)';
        aiBtn.style.background  = 'var(--bg-elev)';
        aiBtn.style.color       = has ? 'var(--accent)' : 'var(--ink-4)';
        aiBtn.style.cursor      = has ? 'pointer' : 'not-allowed';
        aiBtn.style.opacity     = has ? '1' : '0.6';
        aiBtn.title             = has ? 'AI 智能回填' : '先输入企业名称';
      }
      nameInp.addEventListener('input', toggleAi);

      g.AiFormEnrich.init({
        nameInputId:   p + 'name',
        similarListId: p + 'similarList',
        aiBtnId:       p + 'aiBtn',
        aiPanelId:     p + 'aiPanel',
        aiContentId:   p + 'aiContent',
        aiCloseId:     p + 'aiClose',
        similarApi:    '/customer/api/similar-companies',
        enrichApi:     '/customer/api/ai-enrich',
        enrichBodyKey: 'company_name',
        fieldMap: [
          { key: 'industry',      label: '行业',     targetId: p + 'industry',    labelKey: 'industry_label' },
          { key: 'company_type',  label: '企业类型', targetId: p + 'companyType', labelKey: 'company_type_label' },
          { key: 'address',       label: '地址',     targetId: p + 'address' },
          { key: 'description',   label: '企业简介', targetId: p + 'notes',       onlyIfEmpty: true }
        ],
        i18n: {
          btnLoading:    '查询中',
          nameHintMulti: '以下为同一企业的不同正式叫法,选一个填入',
          nameHintSingle:'点选后自动填入',
          fieldHint:     '以下信息适用于所有候选名称',
          applyBtn:      '应用到表单',
          emptyName:     '请先输入名称',
          queryFailed:   'AI 查询失败,请稍后重试',
          networkError:  '网络错误,请稍后重试',
          similarHigh:   '高度相似',
          similarMed:    '相似',
          similarView:   '查看',
          similarOwner:  '归属:',
          similarExists: '已存在,请勿重复创建'
        }
      });
    }
  }

  // 编辑态:加载现有数据填充
  function loadAndFill(modalId, companyId) {
    var p = prefixFor(modalId);
    return fetch('/customer/api/company/' + companyId)
      .then(function (r) { return r.json(); })
      .then(function (res) {
        if (!res.success && !res.id) {
          if (g.ATToast) ATToast.error(res.message || '加载客户数据失败');
          return false;
        }
        var d = res.data || res;
        function setVal(suf, val) { var el = $(p + suf); if (el) el.value = (val == null ? '' : val); }
        setVal('name',              d.company_name);
        setVal('address',           d.address);
        setVal('address_country',   d.country);
        setVal('address_region',    d.region);
        setVal('address_city',      d.city);
        setVal('address_latitude',  d.latitude);
        setVal('address_longitude', d.longitude);
        setVal('notes',             d.notes);

        function selectByValue(suf, val) {
          var el = $(p + suf); if (!el) return;
          var trySelect = function () {
            for (var i = 0; i < el.options.length; i++) {
              if (el.options[i].value === String(val || '')) { el.selectedIndex = i; return true; }
            }
            return false;
          };
          if (!trySelect()) setTimeout(trySelect, 300);
          if (!trySelect()) setTimeout(trySelect, 800);
        }
        selectByValue('industry',    d.industry);
        selectByValue('companyType', d.company_type);
        selectByValue('source',      d.source);
        selectByValue('ownerId',     d.owner_id);

        // 归属人:仅 d.can_change_owner=true 时可改;否则 disabled
        var ownerSel = $(p + 'ownerId');
        if (ownerSel && d.can_change_owner === false) {
          ownerSel.disabled = true;
          ownerSel.style.background = 'var(--bg-sunk)';
          ownerSel.style.color = 'var(--ink-3)';
          ownerSel.style.cursor = 'not-allowed';
          ownerSel.title = '您没有权限修改归属人(只有创建人本人或上级管理者可改)';
        }
        return true;
      })
      .catch(function () { if (g.ATToast) ATToast.error('网络错误,加载失败'); return false; });
  }

  g.atOpenCustomerForm = function (mode, companyId) {
    var modalId = modalIdFor(mode);
    var modal = $(modalId);
    if (!modal) { console.error('[at-customer-form] modal not found:', modalId); return; }
    modal.style.display = 'flex';
    initOnce(mode, modalId);
    if (mode === 'edit' && companyId) {
      modal.dataset.companyId = String(companyId);
      loadAndFill(modalId, companyId);
    }
  };

  g.atSubmitCustomerForm = async function (mode, modalId) {
    var p = prefixFor(modalId);
    var name     = ($(p + 'name').value || '').trim();
    var address  = ($(p + 'address').value || '').trim();
    var compType = $(p + 'companyType').value;
    var source   = $(p + 'source').value;

    if (!name)     { ATToast.warn('无法保存', '请填写企业名称'); return; }
    if (!address)  { ATToast.warn('无法保存', '请填写地址(或地图定位)'); return; }
    if (!compType) { ATToast.warn('无法保存', '请选择企业类型'); return; }
    if (!source)   { ATToast.warn('无法保存', '请选择来源'); return; }

    var body = {
      company_name: name,
      address:      address,
      country:      $(p + 'address_country').value || '',
      region:       $(p + 'address_region').value || '',
      city:         $(p + 'address_city').value || '',
      latitude:     parseFloat($(p + 'address_latitude').value) || null,
      longitude:    parseFloat($(p + 'address_longitude').value) || null,
      industry:     $(p + 'industry').value || '',
      company_type: compType,
      source:       source,
      notes:        ($(p + 'notes').value || '').trim(),
      owner_id:     $(p + 'ownerId').value || null
    };

    var btn = $(modalId + '_submit');
    var oldHtml = btn.innerHTML;
    btn.disabled = true; btn.innerHTML = (mode === 'edit') ? '保存中…' : '创建中…';

    var url, companyId;
    if (mode === 'edit') {
      companyId = $(modalId).dataset.companyId;
      url = '/customer/api/company/' + companyId + '/update';
    } else {
      url = '/customer/api/company/create';
    }
    try {
      var csrf = (document.querySelector('meta[name="csrf-token"]') || {}).content || '';
      var resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
        body: JSON.stringify(body)
      });
      var res = await resp.json();
      if (!res.success) {
        ATToast.error(res.message || '保存失败');
        btn.disabled = false; btn.innerHTML = oldHtml;
        return;
      }
      if (mode === 'edit') {
        ATToast.success('已保存', '刷新中…');
        setTimeout(function () { location.reload(); }, 400);
      } else {
        ATToast.success('已创建', '跳转中…');
        var newId = res.company_id || res.id || (res.data && res.data.id);
        setTimeout(function () {
          location.href = newId ? ('/customer/' + newId + '/at_view') : '/customer/at_list';
        }, 400);
      }
    } catch (e) {
      ATToast.error('网络错误,请重试');
      btn.disabled = false; btn.innerHTML = oldHtml;
    }
  };
})(window);
