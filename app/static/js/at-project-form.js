/**
 * AT 项目表单 modal 控制(创建 + 编辑共用)
 * ──────────────────────────────────────────────────
 * 跟 components/at_project_modal.html 配对:
 *   - 字段 id 用 `${modal_id}__${fieldName}` 前缀化(避免列表/详情同时存在时冲突)
 *   - 创建态 modal_id 默认 'atCreateProjectModal'
 *   - 编辑态 modal_id 默认 'atEditProjectModal'
 *
 * 全局 API:
 *   atOpenProjectForm(mode, projectId?)        — 打开并初始化
 *   atSubmitProjectForm(mode, modalId)         — 模态底部"创建/保存"按钮调用
 *
 * 依赖:
 *   ATToast、ATConfirm、AiFormEnrich(create 态)、AddressPicker、MapPicker、
 *   loadVendorSalesManagers
 */
(function (g) {
  'use strict';

  // 每个 modal_id 的状态(选项是否已加载、AI 是否已 init)
  var State = {};

  function modalIdFor(mode) {
    return (mode === 'edit') ? 'atEditProjectModal' : 'atCreateProjectModal';
  }
  function prefixFor(modalId) { return modalId + '__'; }
  function $(id) { return document.getElementById(id); }

  // ─── 初始化 modal 的选项 + AI(仅一次) ─────────────
  function initOnce(mode, modalId) {
    var p = prefixFor(modalId);
    var st = State[modalId] = State[modalId] || {};
    if (st.optionsLoaded) return;
    st.optionsLoaded = true;

    fetch('/project/api/form-options')
      .then(function (r) { return r.json(); })
      .then(function (res) {
        var sets = [
          [p + 'type',              res.project_types       || []],
          [p + 'industry',          res.industries          || []],
          [p + 'reportSource',      res.report_sources      || []],
          [p + 'productSituation',  res.product_situations  || []]
        ];
        sets.forEach(function (pair) {
          var sel = $(pair[0]); if (!sel) return;
          var placeholder = sel.querySelector('option[value=""]');
          sel.innerHTML = (placeholder ? placeholder.outerHTML : '') +
            pair[1].map(function (it) {
              return '<option value="' + it.code + '">' + it.label + '</option>';
            }).join('');
        });

        // 项目类型按创建人角色锁定:
        //   创建态 — 销售/渠道/服务类角色强制选定其类型并禁用;其他角色可自由选
        //   编辑态 — 仅 admin/business_admin 可改,其余禁用(保持原值)
        var typeSel = $(p + 'type');
        var typeHint = $(p + 'typeLock');
        if (typeSel) {
          var locked = false;
          if (mode === 'create' && res.forced_project_type) {
            typeSel.value = res.forced_project_type;
            locked = true;
          } else if (mode === 'edit' && res.can_edit_project_type === false) {
            locked = true;
          }
          if (locked) {
            typeSel.disabled = true;
            typeSel.style.opacity = '0.6';
            typeSel.style.cursor = 'not-allowed';
            if (typeHint) typeHint.style.display = '';
          }
        }
      })
      .catch(function () { if (g.ATToast) ATToast.error('选项加载失败'); });

    // 厂商销售下拉 — 创建态厂商用户自动预选自己(对齐 TW)
    if (g.loadVendorSalesManagers) {
      var meta = function (n) { var el = document.querySelector('meta[name="' + n + '"]'); return el ? el.getAttribute('content') : ''; };
      var curUid    = parseInt(meta('current-user-id'))  || null;
      var curVendor = meta('current-user-is-vendor') === '1';
      var opts = { emptyText: '请选择厂商销售负责人' };
      if (mode === 'create') {
        opts.autoSelectCurrentUser = true;
        opts.currentUserId         = curUid;
        opts.currentUserIsVendor   = curVendor;
      }
      g.loadVendorSalesManagers(p + 'vendorSales', opts);
    }

    // 创建态:报备时间默认今天(TW 一致行为)
    if (mode === 'create') {
      var rt = $(p + 'reportTime');
      if (rt && !rt.value) {
        var today = new Date().toISOString().split('T')[0];
        rt.value = today;
      }
    }

    // ─── AI 回填(仅 create 态) ──
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
        aiBtn.title             = has ? 'AI 智能回填' : '先输入项目名称';
      }
      nameInp.addEventListener('input', toggleAi);

      g.AiFormEnrich.init({
        nameInputId:   p + 'name',
        similarListId: p + 'similarList',
        aiBtnId:       p + 'aiBtn',
        aiPanelId:     p + 'aiPanel',
        aiContentId:   p + 'aiContent',
        aiCloseId:     p + 'aiClose',
        similarApi:    '/project/api/similar-projects',
        enrichApi:     '/project/api/ai-enrich',
        enrichBodyKey: 'project_name',
        fieldMap: [
          { key: 'industry',    label: '行业',     targetId: p + 'industry', labelKey: 'industry_label' },
          { key: 'address',     label: '地址',     targetId: p + 'address' },
          { key: 'description', label: '项目描述', targetId: p + 'description', onlyIfEmpty: true }
        ],
        i18n: {
          btnLoading:    '查询中',
          nameHintMulti: '以下为同一工程的不同正式叫法,选一个填入',
          nameHintSingle:'点选后自动填入',
          fieldHint:     '以下行业、地址、描述信息适用于所有候选名称',
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

  // ─── 编辑态:加载现有项目数据并填充 ────────────────
  function loadAndFill(modalId, projectId) {
    var p = prefixFor(modalId);
    return fetch('/project/api/' + projectId + '/at-data')
      .then(function (r) { return r.json(); })
      .then(function (res) {
        if (!res.success) {
          ATToast.error(res.message || '加载项目数据失败');
          return false;
        }
        var d = res.data || {};
        function setVal(suf, val) {
          var el = $(p + suf);
          if (el) el.value = (val == null ? '' : val);
        }
        setVal('name',             d.project_name);
        setVal('address',          d.address);
        setVal('address_country',  d.country);
        setVal('address_region',   d.region);
        setVal('address_city',     d.city);
        setVal('address_latitude', d.latitude);
        setVal('address_longitude',d.longitude);
        setVal('reportTime',       d.report_time);
        setVal('delivery',         d.delivery_forecast);
        setVal('description',      d.stage_description);
        setVal('authCode',         d.authorization_code || '— 未授权 —');
        setVal('stage',            d.current_stage_label || d.current_stage || '');
        setVal('owner',            d.owner_name || '');

        // 下拉项异步加载,可能晚到 — 用 setTimeout 兜底
        function selectByValue(suf, val) {
          var el = $(p + suf); if (!el) return;
          var trySelect = function () {
            for (var i = 0; i < el.options.length; i++) {
              if (el.options[i].value === String(val || '')) {
                el.selectedIndex = i; return true;
              }
            }
            return false;
          };
          if (!trySelect()) setTimeout(trySelect, 300);
          if (!trySelect()) setTimeout(trySelect, 800);
        }
        selectByValue('type',             d.project_type);
        selectByValue('industry',         d.industry);
        selectByValue('reportSource',     d.report_source);
        selectByValue('productSituation', d.product_situation);
        if (d.vendor_sales_manager_id) {
          selectByValue('vendorSales', d.vendor_sales_manager_id);
        }
        return true;
      })
      .catch(function () { ATToast.error('网络错误,加载失败'); return false; });
  }

  // ─── 打开 ───────────────────────────────────────
  g.atOpenProjectForm = function (mode, projectId, options) {
    options = options || {};
    var modalId = modalIdFor(mode);
    var modal = $(modalId);
    if (!modal) { console.error('[at-project-form] modal not found:', modalId); return; }
    modal.style.display = 'flex';
    initOnce(mode, modalId);
    // 创建态:可缓存 pre_associate_company_id(从客户详情新建时自动关联)
    if (mode === 'create') {
      modal.dataset.preAssociateCompanyId = String(options.preAssociateCompanyId || '');
    }
    if (mode === 'edit' && projectId) {
      modal.dataset.projectId = String(projectId);
      loadAndFill(modalId, projectId);
    }
  };

  // ─── 提交 ───────────────────────────────────────
  g.atSubmitProjectForm = async function (mode, modalId) {
    var p = prefixFor(modalId);
    var name        = ($(p + 'name').value || '').trim();
    var projType    = $(p + 'type').value;
    var industry    = $(p + 'industry').value;
    var reportSrc   = $(p + 'reportSource').value;
    var desc        = ($(p + 'description').value || '').trim();

    if (!name)      { ATToast.warn('无法保存', '请填写项目名称'); return; }
    if (!projType)  { ATToast.warn('无法保存', '请选择项目类型'); return; }
    if (!industry)  { ATToast.warn('无法保存', '请选择项目行业'); return; }
    if (!reportSrc) { ATToast.warn('无法保存', '请选择报备源');   return; }
    if (!desc)      { ATToast.warn('无法保存', '请填写项目描述'); return; }

    var body = {
      project_name:            name,
      project_type:            projType,
      industry:                industry,
      report_source:           reportSrc,
      product_situation:       $(p + 'productSituation').value,
      vendor_sales_manager_id: $(p + 'vendorSales').value,
      report_time:             $(p + 'reportTime').value,   // edit 态 disabled,提交时为空 — 后端忽略
      delivery_forecast:       $(p + 'delivery').value,
      stage_description:       desc,
      address:   $(p + 'address').value || '',
      country:   $(p + 'address_country').value || '',
      region:    $(p + 'address_region').value || '',
      city:      $(p + 'address_city').value || '',
      latitude:  parseFloat($(p + 'address_latitude').value) || null,
      longitude: parseFloat($(p + 'address_longitude').value) || null
    };
    // 创建态:把客户详情传来的 pre_associate_company_id 带上,后端建项目时自动建关联
    if (mode === 'create') {
      var _pre = $(modalId).dataset.preAssociateCompanyId;
      if (_pre) body.pre_associate_company_id = _pre;
    }

    var btn = $(modalId + '_submit');
    var oldHtml = btn.innerHTML;
    btn.disabled = true; btn.innerHTML = (mode === 'edit') ? '保存中…' : '创建中…';

    var url, projectId;
    if (mode === 'edit') {
      projectId = $(modalId).dataset.projectId;
      url = '/project/api/' + projectId + '/at-update';
    } else {
      url = '/project/api/at-create';
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
        setTimeout(function () { location.href = '/project/' + res.project_id + '/at_view'; }, 400);
      }
    } catch (e) {
      ATToast.error('网络错误,请重试');
      btn.disabled = false; btn.innerHTML = oldHtml;
    }
  };
})(window);
