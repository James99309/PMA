/**
 * AT 报销单表单(新建 / 编辑共用)
 * ──────────────────────────────────────────────────────
 * 配对模板:expense/at_view.html(is_new / is_edit 态)
 * 依赖:at-search-picker.js · at-toast.js · at-file-preview.js
 *
 * 职责:
 *   - 客户/项目搜索 picker 初始化(复用 ATSearchPicker)
 *   - 客户选中后联动联系人下拉
 *   - 不关联客户模式切换(隐藏/恢复客户相关字段)
 *   - 明细行动态增删 + 货币符号同步
 *   - 实时总额计算 → 顶部「总额」+ 表脚「合计」
 *   - 保存:一步 multipart 提交(主表 + 明细 + 发票文件)
 */
(function (g) {
  'use strict';

  // ─── 配置 / 状态(init 时填充)──────────────────────
  var CFG = null;
  var rawDetails = [];

  var currencySym = function () {
    return (CFG && CFG.currency_symbols[document.getElementById('expCurrency').value]) || '¥';
  };

  // ─── 工具 ────────────────────────────────────────────
  function $(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g,
      function (c) { return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c]; });
  }
  function csrf() {
    var m = document.querySelector('meta[name="csrf-token"]');
    return m ? m.content : '';
  }

  // SVG 转圈(SMIL,无需 CSS keyframes,跨浏览器即点即转)
  var SPINNER_HTML =
    '<svg width="14" height="14" viewBox="0 0 50 50" style="display:block;">' +
      '<circle cx="25" cy="25" r="20" stroke="currentColor" stroke-width="6" fill="none"' +
      ' stroke-linecap="round" stroke-dasharray="32,200">' +
        '<animateTransform attributeName="transform" type="rotate"' +
        ' from="0 25 25" to="360 25 25" dur="0.8s" repeatCount="indefinite"/>' +
      '</circle>' +
    '</svg>';
  function setBtnSpinner(btn, on) {
    if (!btn) return;
    if (on) {
      if (btn._oldHtml == null) btn._oldHtml = btn.innerHTML;
      btn.innerHTML = SPINNER_HTML;
      btn.disabled = true;
    } else {
      if (btn._oldHtml != null) { btn.innerHTML = btn._oldHtml; btn._oldHtml = null; }
      btn.disabled = false;
    }
  }

  // ─── 客户/项目 picker + 联系人联动 ───────────────────
  var customerPicker, projectPicker;

  function loadContacts(cid, selectedId) {
    var sel = $('expContactId');
    if (!cid) {
      sel.innerHTML = '<option value="">— 请先选客户 —</option>';
      return;
    }
    fetch(CFG.customer_contacts_url + '/' + cid)
      .then(function (r) { return r.json(); })
      .then(function (res) {
        var items = (res && res.contacts) || [];
        var opts = ['<option value="">— 选择联系人 —</option>'];
        items.forEach(function (c) {
          opts.push('<option value="' + c.id + '"' +
                    (String(selectedId || '') === String(c.id) ? ' selected' : '') +
                    '>' + esc(c.name || '') + '</option>');
        });
        sel.innerHTML = opts.join('');
      });
  }

  function initPickers() {
    customerPicker = ATSearchPicker({
      inputId: 'expCustomer', hiddenIdId: 'expCustomerId',
      clearId: 'expCustomerClear', dropdownId: 'expCustomerDropdown',
      label: '客户',
      searchUrl: function (t) { return CFG.search_customer_url + '?q=' + encodeURIComponent(t); },
      itemsFromResp: function (r) { return (r && r.customers) || []; },
      itemName: function (it) { return it.name || it.company_name; },
      renderItem: function (it, term) {
        return {
          primary: ATSearchPickerHighlight(it.name || it.company_name || '', term),
          secondary: it.company_code || it.code || ''
        };
      },
      onPick: function (item) { loadContacts(item.id, null); },
      onClear: function () { loadContacts(null); }
    });

    projectPicker = ATSearchPicker({
      inputId: 'expProject', hiddenIdId: 'expProjectId',
      clearId: 'expProjectClear', dropdownId: 'expProjectDropdown',
      label: '项目',
      searchUrl: function (t) { return CFG.search_project_url + '?q=' + encodeURIComponent(t); },
      itemsFromResp: function (r) { return (r && r.projects) || []; },
      itemName: function (it) { return it.name; },
      renderItem: function (it, term) {
        var sub = [it.owner, it.type, it.stage].filter(Boolean).join(' · ');
        return {
          primary: ATSearchPickerHighlight(it.name || '', term),
          secondary: sub
        };
      }
    });

    // 已有客户 → 立即加载联系人
    var existingCustomerId = $('expCustomerId').value;
    if (existingCustomerId) {
      var existingContactId = $('expContactId').value;
      loadContacts(existingCustomerId, existingContactId);
    }
  }

  // ─── 不关联客户模式 ──────────────────────────────────
  function applyNoCustomerMode() {
    var no = $('expNoCustomerMode').checked;
    document.querySelectorAll('[data-needs-customer]').forEach(function (el) {
      el.style.opacity = no ? '0.4' : '1';
      el.style.pointerEvents = no ? 'none' : '';
    });
  }

  // ─── 明细行管理 ──────────────────────────────────────
  var detailIdx = 0;
  function inputStyle() {
    return 'width:100%;box-sizing:border-box;height:30px;padding:0 8px;' +
           'border:1px solid var(--line-2);border-radius:4px;background:var(--bg-elev);' +
           'font-size:12.5px;color:var(--ink);outline:none;';
  }
  function categoryOptions(selected) {
    return CFG.expense_categories.map(function (c) {
      var code = c[0], label = c[1];
      return '<option value="' + code + '"' + (selected === code ? ' selected' : '') + '>' + esc(label) + '</option>';
    }).join('');
  }
  function currencyOptions(selected) {
    return Object.keys(CFG.currency_symbols).map(function (code) {
      return '<option value="' + code + '"' + (selected === code ? ' selected' : '') + '>' + code + '</option>';
    }).join('');
  }

  function buildRow(idx, data) {
    data = data || {};
    var dateVal = data.expense_date || new Date().toISOString().slice(0, 10);
    var amountVal = (data.invoice_amount != null) ? Number(data.invoice_amount).toFixed(2) : '';
    var rowCurrency = data.currency || $('expCurrency').value || CFG.default_currency || 'CNY';
    var rate = data.exchange_rate || 1;
    var currentAmount = (data.current_amount != null) ? Number(data.current_amount).toFixed(2)
                                                       : (Number(amountVal || 0) * rate).toFixed(2);

    var fileBtnId = 'expFile_' + idx;
    return (
      '<tr data-row-idx="' + idx + '" ' + (data.id ? 'data-detail-id="' + data.id + '"' : '') + '>' +
        '<td style="padding:6px 8px;border-bottom:1px solid var(--line-soft);">' +
          '<select data-field="expense_category" style="' + inputStyle() + '">' +
            categoryOptions(data.expense_category || 'other') +
          '</select>' +
        '</td>' +
        '<td style="padding:6px 8px;border-bottom:1px solid var(--line-soft);">' +
          '<input type="date" data-field="expense_date" value="' + esc(dateVal) + '" style="' + inputStyle() + '">' +
        '</td>' +
        '<td style="padding:6px 8px;border-bottom:1px solid var(--line-soft);">' +
          '<input type="text" data-field="description" placeholder="说明" value="' + esc(data.description || '') + '" style="' + inputStyle() + '">' +
        '</td>' +
        '<td style="padding:6px 8px;border-bottom:1px solid var(--line-soft);text-align:right;">' +
          '<input type="number" step="0.01" min="0" data-field="invoice_amount" placeholder="0.00"' +
          ' value="' + esc(amountVal) + '"' +
          ' style="' + inputStyle() + 'text-align:right;" class="at-mono">' +
        '</td>' +
        '<td style="padding:6px 6px;border-bottom:1px solid var(--line-soft);">' +
          '<select data-field="currency" style="' + inputStyle() + '">' +
            currencyOptions(rowCurrency) +
          '</select>' +
        '</td>' +
        '<td style="padding:6px 6px;border-bottom:1px solid var(--line-soft);text-align:right;">' +
          '<input type="number" step="0.0001" min="0" data-field="exchange_rate"' +
          ' value="' + esc(Number(rate).toFixed(4).replace(/\.?0+$/, "")) + '"' +
          ' title="可手动调整;默认按当日中间价"' +
          ' style="' + inputStyle() + 'text-align:right;padding:0 6px;" class="at-mono">' +
        '</td>' +
        '<td style="padding:6px 8px;border-bottom:1px solid var(--line-soft);text-align:right;">' +
          '<input type="text" data-field="current_amount" readonly' +
          ' value="' + esc(currentAmount) + '"' +
          ' title="发票金额 × 汇率 → 报销单货币(自动)"' +
          ' style="' + inputStyle() + 'text-align:right;background:var(--bg-sunk);color:var(--ink-2);cursor:default;" class="at-mono">' +
        '</td>' +
        '<td style="padding:6px 6px;border-bottom:1px solid var(--line-soft);">' +
          '<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">' +
            '<input type="file" id="' + fileBtnId + '" data-field="invoice_files" accept="image/*,application/pdf" multiple style="display:none;">' +
            '<button type="button" data-action="upload"' +
            ' style="font-size:13px;padding:0;width:28px;height:28px;border:1px solid var(--accent);border-radius:4px;' +
            ' background:var(--accent-tint);color:var(--accent);cursor:pointer;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0;font-weight:600;line-height:1;">+</button>' +
            '<div data-field="files-strip" style="display:flex;align-items:center;gap:4px;flex-wrap:wrap;"></div>' +
          '</div>' +
        '</td>' +
        '<td style="padding:6px 4px;border-bottom:1px solid var(--line-soft);text-align:center;">' +
          '<button type="button" data-action="remove-row"' +
          ' style="width:24px;height:24px;border:0;border-radius:4px;background:transparent;' +
          ' color:var(--danger);cursor:pointer;font-size:14px;line-height:1;" title="删除此行">×</button>' +
        '</td>' +
      '</tr>'
    );
  }

  function addRow(data) {
    var tbody = $('expDetailsBody');
    var html = buildRow(detailIdx++, data || {});
    tbody.insertAdjacentHTML('beforeend', html);
    var newRow = tbody.lastElementChild;
    // 把已有发票图传给 bindRow → row._files 初始化
    newRow._existingFiles = (data && data.invoice_images) || [];
    bindRow(newRow);
    $('expDetailsEmpty').style.display = 'none';
    updateTotal();
    updateCount();
  }

  function bindRow(row) {
    row.querySelector('[data-action="remove-row"]').addEventListener('click', function () {
      // 释放 blob URL
      (row._files || []).forEach(function (f) {
        if (f.objectUrl) { try { URL.revokeObjectURL(f.objectUrl); } catch (e) {} }
      });
      row.remove();
      updateTotal();
      updateCount();
      if (!$('expDetailsBody').children.length) $('expDetailsEmpty').style.display = 'block';
    });
    var amountInp = row.querySelector('[data-field="invoice_amount"]');
    if (amountInp) amountInp.addEventListener('input', function () {
      recomputeRowAmount(row);
      updateTotal();
    });
    var currencySel = row.querySelector('[data-field="currency"]');
    if (currencySel) currencySel.addEventListener('change', function () {
      fetchRateAndApply(row);
    });
    var rateInp = row.querySelector('[data-field="exchange_rate"]');
    if (rateInp) rateInp.addEventListener('input', function () {
      recomputeRowAmount(row);
      updateTotal();
    });
    // 首次计算汇率(行的货币 ≠ 主表货币时;若已有有效值则跳过 fetch)
    var initRate = parseFloat(rateInp && rateInp.value);
    if (!initRate || (currencySel && currencySel.value === $('expCurrency').value)) {
      fetchRateAndApply(row);
    } else {
      recomputeRowAmount(row);
    }

    // 行内「+」按钮 — 纯上传附件(不识别);OCR 入口在顶部「添加明细 ▾ → 通过发票添加」
    var uploadBtn = row.querySelector('[data-action="upload"]');
    var fileInp = row.querySelector('[data-field="invoice_files"]');
    if (uploadBtn && fileInp) {
      uploadBtn.addEventListener('click', function () { fileInp.click(); });
      fileInp.addEventListener('change', function () {
        if (!fileInp.files || !fileInp.files.length) return;
        var picked = Array.prototype.slice.call(fileInp.files);
        fileInp.value = '';
        picked.forEach(function (f) { addFileToRow(row, f); });
      });
    }

    // 初始化已有发票图(编辑态)
    if (!row._files) row._files = [];
    var existing = row._existingFiles || [];
    existing.forEach(function (f) {
      row._files.push({ kind: 'existing', name: f.filename || f.name || '附件', url: f.url, meta: f });
    });
    renderFilesStrip(row);
  }

  // ─── 每行文件状态 ─────────────────────────────────────
  // row._files: [{kind:'new'|'existing', file?:File, url?:string, name:string,
  //               objectUrl?:string(blob preview), meta?:obj}]
  function renderFilesStrip(row) {
    var strip = row.querySelector('[data-field="files-strip"]');
    if (!strip) return;
    var files = row._files || [];
    if (!files.length) { strip.innerHTML = ''; return; }
    strip.innerHTML = files.map(function (f, i) {
      var isPdf = (f.file && f.file.type === 'application/pdf') ||
                  (f.name && f.name.toLowerCase().endsWith('.pdf'));
      var src = f.objectUrl || f.url || '';
      var thumb = isPdf
        ? '<div style="width:32px;height:32px;border-radius:4px;background:var(--bg-page);border:1px solid var(--line);display:flex;align-items:center;justify-content:center;font-size:14px;">📄</div>'
        : '<div style="width:32px;height:32px;border-radius:4px;background:#000 url(\'' + src + '\') center/cover no-repeat;border:1px solid var(--line);"></div>';
      return '<div data-file-idx="' + i + '" title="' + esc(f.name) + '"' +
              ' style="position:relative;cursor:pointer;display:inline-block;">' +
                thumb +
                '<button type="button" data-action="remove-file"' +
                ' style="position:absolute;top:-5px;right:-5px;width:14px;height:14px;border-radius:50%;' +
                ' background:var(--danger);color:#fff;border:0;font-size:9px;line-height:1;cursor:pointer;' +
                ' display:flex;align-items:center;justify-content:center;padding:0;">×</button>' +
              '</div>';
    }).join('');

    strip.querySelectorAll('[data-file-idx]').forEach(function (el) {
      var idx = parseInt(el.dataset.fileIdx);
      el.addEventListener('click', function (ev) {
        // 删除按钮?
        if (ev.target.closest('[data-action="remove-file"]')) {
          ev.stopPropagation();
          var f = row._files[idx];
          if (f && f.objectUrl) { try { URL.revokeObjectURL(f.objectUrl); } catch (e) {} }
          row._files.splice(idx, 1);
          renderFilesStrip(row);
          return;
        }
        // 预览
        previewFiles(row, idx);
      });
    });
  }

  function previewFiles(row) {
    if (!g.ATFilePreview) return;
    var files = (row._files || []).map(function (f) {
      // ATFilePreview 从 filename 的扩展名推断类型(把 type 传 MIME 会被误判)
      // → 故意不传 type
      return {
        name: f.name,
        url: f.objectUrl || f.url || '',
        size: f.file ? f.file.size : (f.meta && f.meta.size),
      };
    });
    g.ATFilePreview.open('发票预览', files);
  }

  // ─── 顶部「通过发票添加」入口:OCR 后新增明细行 ──────
  async function addByOcrFlow(picked) {
    if (!picked.length) return;
    if (picked.length === 1) {
      await ocrAndCreateRow(picked[0]);
      return;
    }
    // 多张:row=null → 全部新增行(modal 决策应用时新建)
    batchOcrAndDecide(null, picked);
  }

  async function ocrAndCreateRow(file) {
    var menuBtn = $('expAddByOcrBtn') || $('expAddDetailBtn');
    setBtnSpinner(menuBtn, true);
    var fd = new FormData();
    fd.append('file', file);
    try {
      var resp = await fetch('/expense/api/ocr-invoice', {
        method: 'POST',
        headers: { 'X-CSRFToken': csrf(), 'X-Requested-With': 'XMLHttpRequest' },
        body: fd
      });
      var res = await resp.json();
      var newRow = appendBlankRow();
      if (res && res.success) {
        fillRowFromOcr(newRow, res.fields || {});
        if (g.ATToast) ATToast.success('识别完成', '请核对字段(低置信度已飘黄)');
      } else {
        if (g.ATToast) ATToast.error('识别失败', (res && res.message) || '请手动填写');
      }
      addFileToRow(newRow, file);
    } catch (e) {
      if (g.ATToast) ATToast.error('网络错误', e.message || '');
    } finally {
      setBtnSpinner(menuBtn, false);
    }
  }

  function addFileToRow(row, file) {
    if (!row._files) row._files = [];
    var objectUrl = null;
    // 图片 + PDF 都生成 blob URL,用于预览
    var t = file.type || '';
    if (t.indexOf('image/') === 0 || t === 'application/pdf' ||
        /\.(jpe?g|png|gif|webp|pdf)$/i.test(file.name || '')) {
      try { objectUrl = URL.createObjectURL(file); } catch (e) {}
    }
    row._files.push({ kind: 'new', file: file, name: file.name, objectUrl: objectUrl });
    renderFilesStrip(row);
  }

  async function batchOcrAndDecide(row, files) {
    // row=null 表示从顶部「通过发票添加」触发,全部新增行
    var btn = row ? row.querySelector('[data-action="upload"]') : $('expAddDetailBtn');
    setBtnSpinner(btn, true);

    var results = [];
    await Promise.all(files.map(function (f) {
      var fd = new FormData();
      fd.append('file', f);
      return fetch('/expense/api/ocr-invoice', {
        method: 'POST',
        headers: { 'X-CSRFToken': csrf(), 'X-Requested-With': 'XMLHttpRequest' },
        body: fd
      }).then(function (r) { return r.json(); })
        .then(function (res) {
          results.push({ file: f, fields: (res && res.fields) || {}, success: !!(res && res.success) });
        })
        .catch(function () {
          results.push({ file: f, fields: {}, success: false });
        });
    }));

    setBtnSpinner(btn, false);
    openMergeModal(row, results);
  }

  // ─── 三选一合并 modal ─────────────────────────────────
  function openMergeModal(row, results) {
    // 按 (category, currency) 分组
    var groups = {};
    results.forEach(function (r, i) {
      var key = (r.fields.category || 'other') + '|' + (r.fields.currency || $('expCurrency').value);
      (groups[key] = groups[key] || []).push(i);
    });
    var groupKeys = Object.keys(groups);

    var overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.45);z-index:9998;' +
                            'display:flex;align-items:center;justify-content:center;padding:20px;';
    var panel = document.createElement('div');
    panel.style.cssText = 'background:var(--bg-elev);border-radius:10px;border:1px solid var(--line);' +
                          'max-width:680px;width:100%;max-height:80vh;overflow:hidden;' +
                          'display:flex;flex-direction:column;box-shadow:0 12px 48px rgba(0,0,0,0.18);';

    var header = '<div style="padding:18px 22px;border-bottom:1px solid var(--line);">' +
        '<h3 class="at-serif" style="margin:0;font-size:18px;font-weight:500;color:var(--ink);">' +
          '多张发票 — 如何处理?</h3>' +
        '<p style="margin:6px 0 0;font-size:12.5px;color:var(--ink-3);">' +
          '已识别 ' + results.length + ' 张 · 自动按类别+货币分组为 ' + groupKeys.length + ' 组</p>' +
      '</div>';

    var listHtml = '<div style="padding:14px 22px;overflow-y:auto;flex:1;">';
    groupKeys.forEach(function (k) {
      var idxs = groups[k];
      var parts = k.split('|');
      var catLabel = (CFG.expense_categories.find(function (c) { return c[0] === parts[0]; }) || [])[1] || parts[0];
      var groupSum = idxs.reduce(function (a, i) { return a + (parseFloat(results[i].fields.invoice_amount) || 0); }, 0);
      listHtml +=
        '<div style="margin-bottom:14px;padding:10px 12px;background:var(--bg-page);border-radius:6px;border:1px solid var(--line-soft);">' +
          '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">' +
            '<div>' +
              '<span style="font-size:13px;font-weight:500;color:var(--ink);">' + esc(catLabel) + '</span>' +
              '<span class="at-mono" style="font-size:11px;color:var(--ink-4);margin-left:6px;">' + esc(parts[1]) + '</span>' +
              (idxs.length > 1 ? '<span style="margin-left:8px;font-size:10.5px;padding:1px 6px;border-radius:3px;background:var(--accent-tint);color:var(--accent);">可合并 ' + idxs.length + ' 张</span>' : '') +
            '</div>' +
            '<span class="at-mono" style="font-size:12px;color:var(--ink-2);">合计 ' + groupSum.toFixed(2) + '</span>' +
          '</div>' +
          idxs.map(function (i) {
            var r = results[i];
            return '<div style="display:flex;align-items:center;gap:8px;padding:4px 0;font-size:12px;">' +
                     '<span style="color:var(--ink-2);flex:1;">' + esc(r.fields.seller || r.file.name) + '</span>' +
                     '<span class="at-mono" style="color:var(--ink-3);">' + (r.fields.date || '—') + '</span>' +
                     '<span class="at-mono" style="color:var(--ink);min-width:70px;text-align:right;">' +
                       Number(r.fields.invoice_amount || 0).toFixed(2) + '</span>' +
                   '</div>';
          }).join('') +
        '</div>';
    });
    listHtml += '</div>';

    var footer =
      '<div style="padding:14px 22px;border-top:1px solid var(--line);display:flex;justify-content:flex-end;gap:8px;flex-wrap:wrap;">' +
        '<button type="button" data-modal-action="cancel"' +
        ' style="height:32px;padding:0 14px;border:1px solid var(--line-2);border-radius:5px;' +
        ' background:var(--bg-elev);color:var(--ink-2);cursor:pointer;font-size:12.5px;">取消</button>' +
        '<button type="button" data-modal-action="all-merge"' +
        ' style="height:32px;padding:0 14px;border:1px solid var(--line-2);border-radius:5px;' +
        ' background:var(--bg-elev);color:var(--ink);cursor:pointer;font-size:12.5px;">全部合并 (1 行)</button>' +
        '<button type="button" data-modal-action="all-separate"' +
        ' style="height:32px;padding:0 14px;border:1px solid var(--line-2);border-radius:5px;' +
        ' background:var(--bg-elev);color:var(--ink);cursor:pointer;font-size:12.5px;">全部独立 (' + results.length + ' 行)</button>' +
        '<button type="button" data-modal-action="group-merge"' +
        ' style="height:32px;padding:0 14px;border:0;border-radius:5px;' +
        ' background:var(--accent);color:#fff;cursor:pointer;font-size:12.5px;font-weight:500;">按类别合并 (' + groupKeys.length + ' 行)</button>' +
      '</div>';

    panel.innerHTML = header + listHtml + footer;
    overlay.appendChild(panel);
    document.body.appendChild(overlay);

    function close() { try { document.body.removeChild(overlay); } catch (e) {} }
    overlay.addEventListener('click', function (e) { if (e.target === overlay) close(); });
    panel.querySelectorAll('[data-modal-action]').forEach(function (b) {
      b.addEventListener('click', function () {
        var act = b.dataset.modalAction;
        if (act === 'cancel') { close(); return; }
        applyDecision(row, results, groups, act);
        close();
      });
    });
  }

  // ─── 应用决策 ─────────────────────────────────────────
  // row 为 null 时表示「通过发票添加」入口 → 全部新建明细行
  function applyDecision(row, results, groups, action) {
    function targetRow() { return row || appendBlankRow(); }
    if (action === 'all-merge') {
      mergeIntoRow(targetRow(), results, results.map(function (_, i) { return i; }));
      return;
    }
    if (action === 'all-separate') {
      mergeIntoRow(targetRow(), [results[0]], [0]);
      for (var i = 1; i < results.length; i++) {
        mergeIntoRow(appendBlankRow(), [results[i]], [0]);
      }
      return;
    }
    if (action === 'group-merge') {
      var groupKeys = Object.keys(groups);
      groupKeys.forEach(function (k, gi) {
        var idxs = groups[k];
        var groupResults = idxs.map(function (i) { return results[i]; });
        var tgt = (gi === 0) ? targetRow() : appendBlankRow();
        mergeIntoRow(tgt, groupResults, idxs.map(function (_, j) { return j; }));
      });
    }
  }

  function appendBlankRow() {
    var tbody = $('expDetailsBody');
    var html = buildRow(detailIdx++, {});
    tbody.insertAdjacentHTML('beforeend', html);
    var newRow = tbody.lastElementChild;
    bindRow(newRow);
    $('expDetailsEmpty').style.display = 'none';
    updateCount();
    return newRow;
  }

  function mergeIntoRow(row, results, _ignored) {
    // results 全部累加进 row;字段用第 1 张
    var first = results[0];
    var fields = Object.assign({}, first.fields);
    if (results.length > 1) {
      var total = results.reduce(function (a, r) { return a + (parseFloat(r.fields.invoice_amount) || 0); }, 0);
      fields.invoice_amount = total;
      var sellers = results.map(function (r) { return r.fields.seller; }).filter(Boolean);
      var uniqSellers = sellers.filter(function (s, i) { return sellers.indexOf(s) === i; });
      var sellerDesc = uniqSellers.slice(0, 2).join(' / ') + (uniqSellers.length > 2 ? ' 等' : '');
      var desc = first.fields.description || '';
      fields.description = (sellerDesc ? (sellerDesc + ' · ') : '') + (desc || '') + ' (合并 ' + results.length + ' 张)';
      fields.seller = ''; // 不再 prefix(已在 description 里)
    }
    fillRowFromOcr(row, fields);
    // 文件全挂当前行
    results.forEach(function (r) { addFileToRow(row, r.file); });
    updateTotal();
  }

  // ─── OCR:上传单张图/PDF 自动识别填字段。文件已在 row._files,无需挂回。
  function ocrRow(row, file) {
    var uploadBtn = row.querySelector('[data-action="upload"]');
    setBtnSpinner(uploadBtn, true);

    var fd = new FormData();
    fd.append('file', file);

    fetch('/expense/api/ocr-invoice', {
      method: 'POST',
      headers: { 'X-CSRFToken': csrf(), 'X-Requested-With': 'XMLHttpRequest' },
      body: fd
    }).then(function (r) { return r.json(); })
      .then(function (res) {
        if (!res.success) {
          if (g.ATToast) ATToast.error('识别失败', res.message || '请手动填写');
          return;
        }
        fillRowFromOcr(row, res.fields || {});
        if (g.ATToast) ATToast.success('识别完成', '请核对字段(低置信度已飘黄)');
      })
      .catch(function (e) {
        if (g.ATToast) ATToast.error('网络错误', e.message || '');
      })
      .finally(function () {
        setBtnSpinner(uploadBtn, false);
      });
  }

  function fillRowFromOcr(row, fields) {
    var conf = fields.confidence || {};
    var HI = 0.7;

    function setField(name, value, confKey) {
      var el = row.querySelector('[data-field="' + name + '"]');
      if (!el) return;
      if (value != null && value !== '') {
        el.value = value;
      }
      // 低置信度飘黄
      var c = conf[confKey || name];
      if (typeof c === 'number' && c < HI && value != null && value !== '') {
        el.style.borderColor = 'var(--warn)';
        el.title = '置信度 ' + (c * 100).toFixed(0) + '% — 请核对';
      } else {
        el.style.borderColor = '';
        el.title = '';
      }
    }

    // 类别
    if (fields.category) setField('expense_category', fields.category);
    // 日期
    if (fields.date) setField('expense_date', fields.date);
    // 说明:优先 OCR 的 description,前缀 seller 让用户看到商家
    var desc = '';
    if (fields.description) desc = fields.description;
    if (fields.seller && desc.indexOf(fields.seller) < 0) {
      desc = (desc ? (fields.seller + ' · ' + desc) : fields.seller);
    }
    if (desc) setField('description', desc, 'description');
    // 货币(行级)— 先设货币再算金额,这样汇率/报销金额都同步
    if (fields.currency) {
      var sel = row.querySelector('[data-field="currency"]');
      if (sel && sel.value !== fields.currency) {
        sel.value = fields.currency;
        // fetchRateAndApply 内部会算 current_amount + updateTotal
      }
    }
    // 金额(原币)
    if (fields.invoice_amount != null) {
      setField('invoice_amount', Number(fields.invoice_amount).toFixed(2), 'invoice_amount');
    }
    // 计算并触发汇率拉取
    fetchRateAndApply(row);
  }


  function getRowRate(row) {
    var rateInp = row.querySelector('[data-field="exchange_rate"]');
    var v = parseFloat(rateInp && rateInp.value);
    return (isNaN(v) || v <= 0) ? 1 : v;
  }
  function setRowRate(row, rate) {
    var rateInp = row.querySelector('[data-field="exchange_rate"]');
    if (rateInp) {
      rateInp.value = Number(rate).toFixed(4).replace(/\.?0+$/, '');
    }
  }

  function recomputeRowAmount(row) {
    var amountInp = row.querySelector('[data-field="invoice_amount"]');
    var amount = parseFloat(amountInp && amountInp.value) || 0;
    var current = amount * getRowRate(row);
    var currentInp = row.querySelector('[data-field="current_amount"]');
    if (currentInp) currentInp.value = current.toFixed(2);
  }

  function fetchRateAndApply(row) {
    var currencySel = row.querySelector('[data-field="currency"]');
    if (!currencySel) return;
    var from = currencySel.value;
    var to = $('expCurrency').value;
    if (from === to) {
      setRowRate(row, 1);
      recomputeRowAmount(row);
      updateTotal();
      return;
    }
    var rateInp = row.querySelector('[data-field="exchange_rate"]');
    var prev = rateInp ? rateInp.value : '';
    if (rateInp) rateInp.placeholder = '加载中…';
    fetch('/expense/api/exchange-rate?from=' + encodeURIComponent(from) + '&to=' + encodeURIComponent(to))
      .then(function (r) { return r.json(); })
      .then(function (res) {
        var rate = (res && res.rate) || 1;
        setRowRate(row, rate);
        recomputeRowAmount(row);
        updateTotal();
      })
      .catch(function () {
        if (rateInp && !prev) setRowRate(row, 1);
        recomputeRowAmount(row);
        updateTotal();
      });
  }

  function updateTotal() {
    // 报销合计 = ∑ 各行 current_amount(已按汇率换算到主表货币)
    var total = 0;
    document.querySelectorAll('#expDetailsBody [data-field="current_amount"]').forEach(function (inp) {
      var v = parseFloat(inp.value);
      if (!isNaN(v)) total += v;
    });
    var sym = currencySym();
    var fmt = total.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    $('expGrandTotal').textContent = fmt;
    $('expCurrencySym').textContent = sym;
    $('expTotalDisplay').textContent = sym + fmt;
  }
  function updateCount() {
    $('expDetailCount').textContent = $('expDetailsBody').children.length;
  }

  // ─── 保存:multipart 一步提交 ───────────────────────
  function collectAndSubmit() {
    var btn = $('expSaveBtn');
    btn.disabled = true;
    var oldHtml = btn.innerHTML;
    btn.innerHTML = '保存中…';

    // 审核修改态走独立路径:JSON update-fields,只发白名单字段
    if (CFG.is_approval_edit) {
      submitApprovalFieldUpdates(btn, oldHtml);
      return;
    }

    var fd = new FormData();
    fd.append('csrf_token', csrf());
    fd.append('title', $('expTitle').value.trim());
    fd.append('currency', $('expCurrency').value);
    var noCust = $('expNoCustomerMode').checked;
    if (noCust) fd.append('no_customer_mode', '1');
    if (!noCust) {
      fd.append('customer_id', $('expCustomerId').value);
      fd.append('contact_id', $('expContactId').value);
    }
    var projId = $('expProjectId').value;
    if (projId) fd.append('project_id', projId);
    fd.append('description', $('expDescription').value.trim());
    if ($('expAttributeToSelf').checked) fd.append('attribute_to_self', '1');

    // 明细行
    var rows = document.querySelectorAll('#expDetailsBody tr[data-row-idx]');
    if (!rows.length) {
      if (g.ATToast) ATToast.error('请添加至少一条报销明细');
      btn.disabled = false; btn.innerHTML = oldHtml;
      return;
    }
    var hasError = false;
    rows.forEach(function (row, idx) {
      var prefix = 'details[' + idx + ']';
      var fields = ['expense_category', 'expense_date', 'description', 'invoice_amount'];
      fields.forEach(function (f) {
        var el = row.querySelector('[data-field="' + f + '"]');
        if (el) fd.append(prefix + '[' + f + ']', el.value);
      });
      // 行级货币 + 汇率(后端按 invoice_amount × exchange_rate 算 current_amount)
      var rowCcySel = row.querySelector('[data-field="currency"]');
      fd.append(prefix + '[currency]', (rowCcySel && rowCcySel.value) || $('expCurrency').value);
      fd.append(prefix + '[exchange_rate]', String(getRowRate(row)));

      var amount = parseFloat(row.querySelector('[data-field="invoice_amount"]').value);
      if (isNaN(amount) || amount <= 0) {
        hasError = true;
      }

      // 发票文件 — 字段名必须显式数字索引:
      //   新上传:details[i][invoice_files][n]            (expense.py:1121)
      //   已有的:details[i][existing_invoices][n][url|filename|size]  (expense.py:2101)
      // 已存在的也必须传回,否则后端会清空原 invoice_images
      var fIdx = 0;
      var existIdx = 0;
      (row._files || []).forEach(function (f) {
        if (f.kind === 'new' && f.file) {
          fd.append(prefix + '[invoice_files][' + fIdx + ']', f.file);
          fIdx++;
        } else if (f.kind === 'existing') {
          var ep = prefix + '[existing_invoices][' + existIdx + ']';
          fd.append(ep + '[url]', f.url || '');
          fd.append(ep + '[filename]', f.name || '');
          fd.append(ep + '[size]', String((f.meta && f.meta.size) || 0));
          existIdx++;
        }
      });

      // 已存在的明细带上 detail_id
      var existId = row.dataset.detailId;
      if (existId) fd.append(prefix + '[id]', existId);
    });

    if (hasError) {
      if (g.ATToast) ATToast.error('每条明细金额必须 > 0');
      btn.disabled = false; btn.innerHTML = oldHtml;
      return;
    }

    function atTarget(id) {
      return id ? ('/expense/' + id + '/at_view') : '/expense/at_list';
    }
    function extractIdFromUrl(u) {
      var m = String(u || '').match(/\/expense\/(\d+)(?:\/|$|\?)/);
      return m ? m[1] : null;
    }

    fetch(CFG.submit_url, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrf(), 'X-Requested-With': 'XMLHttpRequest' },
      body: fd
    }).then(function (resp) {
      var ct = resp.headers.get('Content-Type') || '';
      // ── A. AJAX JSON 响应 ──
      if (ct.indexOf('application/json') >= 0) {
        return resp.json().then(function (j) {
          if (j.success === false) {
            if (g.ATToast) ATToast.error(j.message || '保存失败');
            btn.disabled = false; btn.innerHTML = oldHtml;
            return null;
          }
          var newId = j.expense_id || j.id || extractIdFromUrl(j.redirect_url) || CFG.expense_id;
          if (g.ATToast) ATToast.success('已保存', '跳转中…');
          setTimeout(function () { location.href = atTarget(newId); }, 400);
          return null;
        });
      }
      // ── B. 老 form redirect:从 redirect URL 提 expense_id,强制跳 AT 详情 ──
      if (resp.ok || resp.redirected) {
        var newId = extractIdFromUrl(resp.url) || CFG.expense_id;
        if (g.ATToast) ATToast.success('已保存', '跳转中…');
        setTimeout(function () { location.href = atTarget(newId); }, 400);
      } else {
        if (g.ATToast) ATToast.error('保存失败 (HTTP ' + resp.status + ')');
        btn.disabled = false; btn.innerHTML = oldHtml;
      }
    }).catch(function (e) {
      if (g.ATToast) ATToast.error('网络错误', e.message || '');
      btn.disabled = false; btn.innerHTML = oldHtml;
    });
  }

  // ─── 主表字段 → DOM id 映射(审核修改态用 disable) ──
  var MAIN_FIELD_INPUTS = {
    title: 'expTitle',
    currency: 'expCurrency',
    description: 'expDescription',
    no_customer_mode: 'expNoCustomerMode',
    customer_id: 'expCustomerId',
    contact_id: 'expContactId',
    project_id: 'expProjectId',
    attribute_to_self: 'expAttributeToSelf',
    attributed_to_id: 'expAttributedToId'
  };
  // 审核修改态:与客户/项目联动的 picker 文本输入框(name-suffix 没有)
  var MAIN_FIELD_PICKERS = {
    customer_id: 'expCustomer',
    project_id: 'expProject'
  };

  // ─── 审核修改态:JSON update-fields ──────────────────
  function submitApprovalFieldUpdates(btn, oldHtml) {
    var allow = CFG.editable_fields || [];
    var updates = {};
    function maybeAdd(field, value) {
      if (allow.indexOf(field) >= 0 && value !== null && value !== undefined && value !== '') {
        updates[field] = value;
      }
    }
    maybeAdd('title', $('expTitle').value.trim());
    maybeAdd('currency', $('expCurrency').value);
    maybeAdd('description', $('expDescription').value.trim());
    maybeAdd('customer_id', $('expCustomerId').value);
    maybeAdd('contact_id', $('expContactId').value);
    maybeAdd('project_id', $('expProjectId').value);
    if (allow.indexOf('no_customer_mode') >= 0) {
      updates.no_customer_mode = $('expNoCustomerMode').checked ? '1' : '0';
    }
    if (allow.indexOf('attribute_to_self') >= 0) {
      updates.attribute_to_self = $('expAttributeToSelf').checked ? '1' : '0';
    }
    // exchange_rate 是明细级字段 — 收集成 {detail_id: rate} dict
    // 后端 _update_expense_exchange_rate 已升级为 dict 入参时按明细级处理
    if (allow.indexOf('exchange_rate') >= 0) {
      var rateMap = {};
      document.querySelectorAll('#expDetailsBody tr[data-row-idx]').forEach(function (row) {
        var detailId = row.dataset.detailId;
        if (!detailId) return; // 新增行无 id(审核态不该出现新行,但兜底跳过)
        var rateInp = row.querySelector('[data-field="exchange_rate"]');
        var v = rateInp ? parseFloat(rateInp.value) : NaN;
        if (!isNaN(v) && v > 0) rateMap[String(detailId)] = v;
      });
      if (Object.keys(rateMap).length) updates.exchange_rate = rateMap;
    }
    if (!Object.keys(updates).length) {
      if (g.ATToast) ATToast.error('没有可保存的字段修改');
      btn.disabled = false; btn.innerHTML = oldHtml;
      return;
    }
    console.log('[approval-edit] submitting →', CFG.submit_url, '\nfield_updates:', JSON.parse(JSON.stringify(updates)));
    fetch(CFG.submit_url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf(),
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify({ field_updates: updates })
    }).then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (res) {
        console.log('[approval-edit] response ←', res);
        if (res && res.success === false) {
          if (g.ATToast) ATToast.error(res.message || '字段更新失败');
          btn.disabled = false; btn.innerHTML = oldHtml;
          return;
        }
        if (g.ATToast) ATToast.success('已保存', '跳转中…');
        setTimeout(function () {
          location.href = '/expense/' + CFG.expense_id + '/at_view';
        }, 400);
      })
      .catch(function (e) {
        if (g.ATToast) ATToast.error('网络错误', e.message || '');
        btn.disabled = false; btn.innerHTML = oldHtml;
      });
  }

  // ─── 初始化 ─────────────────────────────────────────
  function init() {
    var cfgEl = document.getElementById('expFormConfig');
    if (!cfgEl) {
      console.error('[at-expense-form] expFormConfig 缺失');
      return;
    }
    try { CFG = JSON.parse(cfgEl.textContent); }
    catch (e) { console.error('[at-expense-form] CFG 解析失败', e); return; }

    try {
      var rawEl = document.getElementById('expDetailsRaw');
      if (rawEl) rawDetails = JSON.parse(rawEl.textContent.trim() || '[]');
    } catch (e) { rawDetails = []; }

    initPickers();
    $('expNoCustomerMode').addEventListener('change', applyNoCustomerMode);
    applyNoCustomerMode();

    // 报销说明 blur → 如果标题为空 + 描述非空 → AI 异步生成标题(fire-and-forget)
    var descEl = $('expDescription');
    var titleEl = $('expTitle');
    if (descEl && titleEl) {
      descEl.addEventListener('blur', function () {
        var desc = descEl.value.trim();
        var title = titleEl.value.trim();
        if (!desc || title) return;
        // 占位提示 + 触发
        titleEl.placeholder = 'AI 生成中…';
        fetch('/expense/api/generate-title', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf(),
            'X-Requested-With': 'XMLHttpRequest'
          },
          body: JSON.stringify({ description: desc })
        }).then(function (r) { return r.json().catch(function () { return {}; }); })
          .then(function (res) {
            // 用户已经手填了 → 不覆盖
            if (titleEl.value.trim()) return;
            if (res && res.success && res.title) {
              titleEl.value = res.title;
              // 注:不做背景/外发光高亮 —— 任何对标题框背景或 box-shadow 的临时改动
              // 在暗色下都会造成「闪一下的白方块」,故仅填值,不加视觉特效
            }
          })
          .catch(function () { /* 静默失败,保留用户原占位 */ })
          .finally(function () {
            titleEl.placeholder = '默认 客户名-姓名-YYDDHHS';
          });
      });
    }

    $('expCurrency').addEventListener('change', function () {
      // 主表货币改变 → 所有明细行重新 fetch 汇率
      document.querySelectorAll('#expDetailsBody tr[data-row-idx]').forEach(function (row) {
        fetchRateAndApply(row);
      });
      updateTotal();
    });

    // 「添加明细 ▾」下拉菜单
    var menuWrap = $('expAddDetailMenuWrap');
    var menuBtn  = $('expAddDetailBtn');
    var menu     = $('expAddDetailMenu');
    var globalOcrInp = $('expGlobalOcrFile');
    function closeMenu() { if (menu) menu.style.display = 'none'; }
    function openMenu()  { if (menu) menu.style.display = 'block'; }
    menuBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      if (menu.style.display === 'block') closeMenu(); else openMenu();
    });
    document.addEventListener('click', function (e) {
      if (!menuWrap.contains(e.target)) closeMenu();
    });
    menu.querySelector('[data-action="add-manual"]').addEventListener('click', function () {
      closeMenu();
      addRow();
    });
    menu.querySelector('[data-action="add-by-ocr"]').addEventListener('click', function () {
      closeMenu();
      globalOcrInp.click();
    });
    globalOcrInp.addEventListener('change', function () {
      if (!globalOcrInp.files || !globalOcrInp.files.length) return;
      var picked = Array.prototype.slice.call(globalOcrInp.files);
      globalOcrInp.value = '';
      addByOcrFlow(picked);
    });

    // 加载已有明细(编辑态)
    var existingRows = $('expDetailsBody').querySelectorAll('tr[data-existing]');
    existingRows.forEach(function (r) { r.remove(); });
    if (rawDetails.length) {
      rawDetails.forEach(function (d) { addRow(d); });
    }
    // 新建态:不默认插行,完全靠用户点「+ 添加明细 ▾」生成
    // 空状态 expDetailsEmpty 占位文案已经提示「暂无明细 — 点击右上角…」

    $('expSaveBtn').addEventListener('click', collectAndSubmit);

    // 审核修改态:disable 非白名单字段(主表 + 全部明细行)
    if (CFG.is_approval_edit) applyApprovalEditMask();

    updateTotal();
  }

  function applyApprovalEditMask() {
    var allow = CFG.editable_fields || [];
    // 主表 inputs
    Object.keys(MAIN_FIELD_INPUTS).forEach(function (field) {
      if (allow.indexOf(field) >= 0) return;
      var el = $(MAIN_FIELD_INPUTS[field]);
      if (el) lockInput(el);
    });
    // 主表 picker(text input + clear 按钮)
    Object.keys(MAIN_FIELD_PICKERS).forEach(function (field) {
      if (allow.indexOf(field) >= 0) return;
      var inp = $(MAIN_FIELD_PICKERS[field]);
      var clr = $(MAIN_FIELD_PICKERS[field] + 'Clear');
      if (inp) lockInput(inp);
      if (clr) clr.style.display = 'none';
    });
    // 明细整体禁用 — 但保留 editable_fields 内的明细级字段(如 exchange_rate)
    var detailEditableSet = {};
    allow.forEach(function (f) { detailEditableSet[f] = true; });
    document.querySelectorAll('#expDetailsBody input, #expDetailsBody select, #expDetailsBody textarea').forEach(function (el) {
      var field = el.dataset.field;
      if (field && detailEditableSet[field]) return; // 该字段在白名单 → 不锁
      lockInput(el);
    });
    // 隐藏明细操作按钮(添加/删除行/上传文件)— 因为不允许动结构
    // 同时隐藏附件 ✕ 删除按钮 — 审核修改不能动附件
    document.querySelectorAll('[data-action="upload"], [data-action="remove-row"], [data-action="remove-file"]').forEach(function (b) {
      b.style.display = 'none';
    });
    var addBtn = $('expAddDetailMenuWrap');
    if (addBtn) addBtn.style.display = 'none';

    // 汇率字段独立编辑(每行不同 — 多币种场景);
    // bindRow 已经注册了 'input' → recomputeRowAmount + updateTotal,这里不重复绑。
  }
  function lockInput(el) {
    if (!el) return;
    el.disabled = true;
    el.style.background = 'var(--bg-sunk)';
    el.style.color = 'var(--ink-3)';
    el.style.cursor = 'not-allowed';
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})(window);
