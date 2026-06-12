/**
 * AT 审批状态 Chip 下拉浮层
 * ──────────────────────────────────────────────────
 * 配对模板:components/at_approval_dropdown.html
 *
 * 流程:
 *   点 chip → 弹浮层 → fetch {api_base}/{id}/flow → 渲染流程节点 + 操作按钮
 *   按钮:[提交审批] [召回] [重新提交] [同意] [驳回]
 *   - 提交审批 / 重新提交 → 弹详细摘要确认 modal
 *   - 召回 / 同意 / 驳回 → ATConfirm 简单确认
 *   - 所有 API 调用成功后 reload 当前页(刷新状态徽章)
 */
(function (g) {
  'use strict';

  var OPEN_PANELS = new Set();

  function $q(root, sel) { return root.querySelector(sel); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g,
      function (c) { return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c]; });
  }
  function csrf() {
    var m = document.querySelector('meta[name="csrf-token"]');
    return m ? m.content : '';
  }
  function fmtAmount(n) {
    n = Number(n || 0);
    return n.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  }

  /* ============== 初始化 ============== */
  function initAll() {
    document.querySelectorAll('[data-at-approval]').forEach(initOne);
    // 全局点击外部 → 关所有
    document.addEventListener('click', function (e) {
      document.querySelectorAll('[data-at-approval]').forEach(function (root) {
        if (!root.contains(e.target)) closePanel(root);
      });
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        document.querySelectorAll('[data-at-approval]').forEach(closePanel);
      }
    });
  }
  function initOne(root) {
    var chip = $q(root, '[data-at-approval-chip]');
    if (!chip) return;
    chip.addEventListener('click', function (e) {
      e.stopPropagation();
      var panel = $q(root, '[data-at-approval-panel]');
      if (panel.style.display === 'block') closePanel(root);
      else openPanel(root);
    });
  }

  function openPanel(root) {
    var panel = $q(root, '[data-at-approval-panel]');
    panel.style.display = 'block';
    OPEN_PANELS.add(root);
    positionPanel(root);
    fetchFlow(root);
  }

  // 智能定位:chip 离视口右边过近时改为右对齐;chip 离右边和左边都不够时,改 left 锁到视口内
  function positionPanel(root) {
    var panel = $q(root, '[data-at-approval-panel]');
    if (!panel) return;
    var chipRect = root.getBoundingClientRect();
    var panelWidth = panel.offsetWidth || 380;
    var vw = window.innerWidth;
    var margin = 16; // 视口边距

    // 默认左对齐 chip(浮层向右展开)
    panel.style.left = '0';
    panel.style.right = 'auto';

    // 检测:chip 左 + 浮层宽 > 视口右边 → 改为右对齐(浮层向左展开,贴 chip 右边)
    if (chipRect.left + panelWidth > vw - margin) {
      // 看 chip 右边到视口右边的距离是否够浮层宽
      // 浮层右对齐 chip → 浮层左边 = chip.right - panelWidth
      // 浮层左边距视口左边 = chip.right - panelWidth
      if (chipRect.right - panelWidth >= margin) {
        panel.style.left = 'auto';
        panel.style.right = '0';
      } else {
        // 两边都不够 → 浮层独立锁定到视口左 margin,跟 chip 解耦
        panel.style.left = (margin - chipRect.left) + 'px';
        panel.style.right = 'auto';
      }
    }
  }
  function closePanel(root) {
    var panel = $q(root, '[data-at-approval-panel]');
    if (panel) panel.style.display = 'none';
    OPEN_PANELS.delete(root);
  }

  /* ============== 拉流程 + 渲染 ============== */
  function fetchFlow(root) {
    var apiBase = root.dataset.apiBase;
    var objId = root.dataset.objectId;
    var body = $q(root, '[data-at-approval-body]');
    body.innerHTML = '<div style="padding:32px 24px;text-align:center;color:var(--ink-4);font-size:12.5px;">加载中…</div>';

    // 并发拉 flow + editable-fields(后者用于判断「审核修改」按钮是否显示)
    var hdr = { 'X-Requested-With': 'XMLHttpRequest' };
    Promise.all([
      fetch(apiBase + '/' + objId + '/flow', { headers: hdr })
        .then(function (r) { return r.json(); }),
      fetch(apiBase + '/' + objId + '/editable-fields', { headers: hdr })
        .then(function (r) { return r.json(); })
        .catch(function () { return { success: false }; })
    ]).then(function (results) {
      var flowRes = results[0];
      var editRes = results[1] || {};
      var editInfo = editRes.data || {};
      var hasEditableFields = !!(editInfo.can_edit && editInfo.editable_fields && editInfo.editable_fields.length);
      renderFlow(root, flowRes, hasEditableFields);
      // 内容渲染完后重新校准浮层位置(此时 offsetWidth 准确)
      positionPanel(root);
    }).catch(function (e) {
      body.innerHTML = '<div style="padding:24px;color:var(--danger);font-size:12px;">加载失败:' + esc(e.message || '') + '</div>';
    });
  }

  function renderFlow(root, res, hasEditableFields) {
    var body = $q(root, '[data-at-approval-body]');
    var actions = $q(root, '[data-at-approval-actions]');
    var ownerStatus = root.dataset.status;
    var control = (res && res.control_info) || {};
    var flow = (res && res.approval_flow) || null;

    // 无审批实例(草稿态)— 只显示提交按钮
    if (!flow) {
      body.innerHTML =
        '<div style="padding:24px;">' +
          '<div style="font-size:13px;color:var(--ink);font-weight:500;margin-bottom:4px;">尚未提交审批</div>' +
          '<div class="at-dim" style="font-size:12px;">填好明细后,提交审批后将由后端自动匹配审批流程模板。</div>' +
        '</div>';
      renderActions(root, actions, {
        can_submit: (control.can_submit !== undefined) ? control.can_submit
                     : (ownerStatus === 'draft'),
        can_recall: false, can_resubmit: false, can_approve: false
      }, null);
      return;
    }

    // 渲染流程节点(时间轴)
    var stages = flow.stages || [];
    var nodesHtml = stages.map(function (s, i) {
      var st = s.status; // approved | rejected | current | pending | skipped
      var dotColor, dotIcon, ringColor;
      if (st === 'approved') {
        dotColor = 'var(--success)'; dotIcon = '✓'; ringColor = 'var(--success)';
      } else if (st === 'rejected') {
        dotColor = 'var(--danger)'; dotIcon = '✕'; ringColor = 'var(--danger)';
      } else if (st === 'current') {
        dotColor = 'var(--warn)'; dotIcon = '⟳'; ringColor = 'var(--warn)';
      } else if (st === 'skipped') {
        dotColor = 'var(--ink-4)'; dotIcon = '—'; ringColor = 'var(--line-2)';
      } else {
        dotColor = 'var(--ink-4)'; dotIcon = ''; ringColor = 'var(--line-2)';
      }

      var isLast = (i === stages.length - 1);
      var subtitleParts = [];
      if (st === 'approved' || st === 'rejected' || st === 'skipped') {
        if (s.processed_at) subtitleParts.push(s.processed_at.slice(0, 16));
        if (s.comment) subtitleParts.push('"' + esc(s.comment.slice(0, 60)) + (s.comment.length > 60 ? '…' : '') + '"');
      } else if (st === 'current') {
        subtitleParts.push('当前节点 · 等待审批');
      } else {
        subtitleParts.push('待处理');
      }

      return (
        '<div style="display:flex;gap:10px;padding:8px 0;position:relative;">' +
          '<div style="position:relative;flex-shrink:0;width:22px;display:flex;justify-content:center;">' +
            '<div style="width:18px;height:18px;border-radius:50%;background:' + (st === 'pending' ? 'transparent' : dotColor) + ';' +
                  'border:1.5px solid ' + ringColor + ';color:#fff;font-size:11px;line-height:1;' +
                  'display:flex;align-items:center;justify-content:center;z-index:2;">' + dotIcon + '</div>' +
            (isLast ? '' :
              '<div style="position:absolute;top:18px;left:50%;width:1.5px;height:calc(100% + 8px);' +
              'background:' + (st === 'approved' || st === 'rejected' ? ringColor : 'var(--line-2)') + ';transform:translateX(-50%);"></div>') +
          '</div>' +
          '<div style="flex:1;min-width:0;">' +
            '<div style="display:flex;justify-content:space-between;gap:8px;font-size:12.5px;color:var(--ink);">' +
              '<span style="font-weight:500;">' + esc(s.stage_name || ('节点 ' + (s.stage_order || (i+1)))) + '</span>' +
              '<span class="at-dim" style="font-size:11px;">' + esc(s.approver_name || '—') + '</span>' +
            '</div>' +
            (subtitleParts.length ?
              '<div class="at-dim" style="font-size:11px;color:var(--ink-4);margin-top:2px;line-height:1.45;">' +
                subtitleParts.join(' · ') + '</div>' : '') +
          '</div>' +
        '</div>'
      );
    }).join('');

    body.innerHTML =
      '<div style="padding:14px 18px 8px;border-bottom:1px solid var(--line-soft);">' +
        '<div style="font-size:12.5px;color:var(--ink);font-weight:500;">' +
          '审批流程 · 共 ' + stages.length + ' 节点' +
        '</div>' +
      '</div>' +
      '<div style="padding:10px 18px 12px;">' + nodesHtml + '</div>';

    renderActions(root, actions, {
      can_submit: false, // 已有 flow,不能再 submit(状态非 draft)
      can_recall: !!flow.can_recall,
      can_resubmit: !!flow.can_resubmit,
      can_approve: !!flow.can_approve,
      can_approval_edit: !!(flow.can_approve && hasEditableFields),
    }, flow);
  }

  function renderActions(root, container, perms, flow) {
    var parts = [];
    if (perms.can_submit)   parts.push(btn('submit',    '提交审批',   'primary'));
    if (perms.can_recall)   parts.push(btn('recall',    '召回',       'ghost'));
    if (perms.can_resubmit) parts.push(btn('resubmit',  '重新提交',   'primary'));
    // 审批人 + 当前节点配置了 editable_fields(非空)才显示「审核修改」
    if (perms.can_approval_edit) parts.push(btn('approval-edit', '✎ 审核修改', 'ghost'));
    if (perms.can_approve)  parts.push(btn('reject',    '驳回',       'danger'));
    if (perms.can_approve)  parts.push(btn('approve',   '同意',       'primary'));
    if (!parts.length) { container.style.display = 'none'; return; }
    container.style.display = 'flex';
    container.innerHTML = parts.join('');
    container.querySelectorAll('[data-act]').forEach(function (b) {
      b.addEventListener('click', function () {
        var act = b.dataset.act;
        if (act === 'submit')        submitApproval(root);
        if (act === 'resubmit')      resubmitApproval(root);
        if (act === 'recall')        recallApproval(root);
        if (act === 'approve')       approveDecision(root, 'approve', flow);
        if (act === 'reject')        approveDecision(root, 'reject',  flow);
        if (act === 'approval-edit') {
          // 跳到审核修改页 — 后端会校验是否真有可编辑字段;无则 flash 提示后跳回
          var objId = root.dataset.objectId;
          var objType = root.dataset.objectType || 'expense';
          location.href = '/' + objType + '/' + objId + '/at_view?action=approval_edit';
        }
      });
    });
  }

  function btn(act, label, variant) {
    var bg, color, border;
    if (variant === 'primary') { bg = 'var(--accent)'; color = '#fff'; border = '0'; }
    else if (variant === 'danger') { bg = 'transparent'; color = 'var(--danger)'; border = '1px solid var(--danger-soft)'; }
    else { bg = 'var(--bg-elev)'; color = 'var(--ink)'; border = '1px solid var(--line-2)'; }
    return '<button type="button" data-act="' + act + '"' +
            ' style="height:28px;padding:0 12px;border:' + border + ';border-radius:5px;' +
            ' background:' + bg + ';color:' + color + ';font-size:12px;font-weight:500;cursor:pointer;">' +
            esc(label) +
           '</button>';
  }

  /* ============== 提交确认 modal — radio 卡片风格(对齐 SM 模态)============== */
  // onConfirm 签名:onConfirm(designated_approvers_dict_or_null, comment_string)
  function openSubmitModal(root, actionLabel, onConfirm, designateSteps) {
    var meta = JSON.parse(root.dataset.meta || '{}');
    designateSteps = designateSteps || [];
    var objectType = root.dataset.objectType || 'object';

    var OBJECT_KICKER = {
      expense: 'EXPENSE · 报销审批',
      project: 'PROJECT · 项目报备',
      quotation: 'TECHNICAL REVIEW · 技术确认',
      purchase_order: 'PURCHASE ORDER · 订单审批',
    };
    var kicker = OBJECT_KICKER[objectType] || (objectType.toUpperCase() + ' · ' + actionLabel);

    // 标题 — 有指定步骤时聚焦"选择审批人",无则"提交审批"
    var headerTitle = designateSteps.length ? '选择审批人' : (actionLabel + '确认');

    var overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.45);z-index:9998;' +
                            'display:flex;align-items:center;justify-content:center;padding:20px;';
    var panel = document.createElement('div');
    panel.style.cssText = 'background:var(--bg-elev);border-radius:14px;border:1px solid var(--line);' +
                          'max-width:560px;width:100%;max-height:88vh;box-shadow:0 24px 64px rgba(0,0,0,0.22);' +
                          'overflow:hidden;display:flex;flex-direction:column;';

    // ─── 1. Header(左色块图标 · kicker · 标题 · ✕)──
    var headerHtml =
      '<div style="padding:22px 26px 18px;display:flex;align-items:flex-start;gap:14px;border-bottom:1px solid var(--line-soft);">' +
        '<div style="width:52px;height:52px;border-radius:10px;background:var(--accent-tint);flex-shrink:0;"></div>' +
        '<div style="flex:1;min-width:0;">' +
          '<div class="at-mono at-dim" style="font-size:10.5px;letter-spacing:0.16em;color:var(--ink-4);margin-bottom:4px;">' +
            esc(kicker) +
          '</div>' +
          '<h3 class="at-serif" style="margin:0;font-size:22px;font-weight:500;color:var(--ink);line-height:1.2;letter-spacing:-0.005em;">' +
            esc(headerTitle) +
          '</h3>' +
        '</div>' +
        '<button type="button" data-modal-action="cancel"' +
        ' style="width:32px;height:32px;border:0;background:transparent;border-radius:50%;cursor:pointer;' +
        ' display:flex;align-items:center;justify-content:center;color:var(--ink-3);font-size:18px;line-height:1;flex-shrink:0;">' +
          '×' +
        '</button>' +
      '</div>';

    // ─── 2. 候选人 radio 卡片(每个 designate step)──
    var designateHtml = '';
    designateSteps.forEach(function (s, sIdx) {
      var cands = s.candidates || [];
      var poolDesc = '';
      var roles = (s.pool && s.pool.roles) || [];
      if (roles.length) {
        // "从方案经理中选择一位" 之类
        var roleLabel = roles[0]; // 简化:展示第一个
        poolDesc = '从' + (roleLabel === 'solution_manager' ? '方案经理' :
                          roleLabel === 'sm' || roleLabel === 'sales_manager' ? '销售经理' :
                          roleLabel === 'finance' || roleLabel === 'finance_director' ? '财务' :
                          roleLabel) + '中选择一位';
      } else {
        poolDesc = '请选择「' + s.step_name + '」审批人';
      }

      designateHtml +=
        '<div style="padding:18px 26px 10px;">' +
          '<div style="font-size:12px;color:var(--ink-3);margin-bottom:10px;">' +
            esc(poolDesc) +
          '</div>' +
          '<div data-designate-step-card="' + s.step_id + '"' +
          ' style="border:1px solid var(--line);border-radius:10px;padding:6px;background:var(--bg-page);">' +
            (cands.length ?
              cands.map(function (c, ci) {
                return (
                  '<label data-cand-row="' + c.id + '"' +
                  ' style="display:flex;align-items:center;gap:14px;padding:14px 16px;border-radius:6px;' +
                  ' cursor:pointer;transition:background 100ms;' +
                  (ci > 0 ? 'border-top:1px solid var(--line-soft);' : '') +
                  '" onmouseover="this.style.background=\'var(--bg-hover)\'"' +
                  ' onmouseout="this.style.background=\'transparent\'">' +
                    '<input type="radio" name="designate_step_' + s.step_id + '" value="' + c.id + '"' +
                    ' data-designate-step="' + s.step_id + '"' +
                    ' style="width:18px;height:18px;accent-color:var(--accent);cursor:pointer;flex-shrink:0;">' +
                    '<span style="flex:1;font-size:14px;font-weight:500;color:var(--ink);">' + esc(c.name) + '</span>' +
                    (c.role ?
                      '<span class="at-mono" style="font-size:11px;color:var(--ink-4);letter-spacing:0.06em;">' +
                        esc(c.role.toUpperCase()) +
                      '</span>' : '') +
                  '</label>'
                );
              }).join('')
              :
              '<div style="padding:24px;text-align:center;color:var(--danger);font-size:12.5px;">' +
                '可选范围内无可用用户 — 请联系管理员调整模板「指定范围」' +
              '</div>'
            ) +
          '</div>' +
        '</div>';
    });

    // ─── 3. 摘要(金额/客户/项目/明细)— 紧凑版,仅当有数据时显示 ──
    var summaryRows = [];
    if (meta.total_amount) {
      summaryRows.push(
        '<div style="display:flex;justify-content:space-between;padding:4px 0;font-size:13px;">' +
          '<span class="at-dim">金额</span>' +
          '<span class="at-mono at-tab-num" style="color:var(--ink);font-weight:500;">' +
            esc(meta.currency_sym || '¥') + fmtAmount(meta.total_amount) +
          '</span>' +
        '</div>');
    }
    if (meta.customer_name) summaryRows.push(row('客户', meta.customer_name));
    if (meta.project_name)  summaryRows.push(row('项目', meta.project_name));
    if (meta.line_count) summaryRows.push(row('明细', meta.line_count + ' 条'));
    var summaryHtml = summaryRows.length ?
      '<div style="padding:14px 26px 4px;border-top:1px solid var(--line-soft);">' +
        summaryRows.join('') +
      '</div>' : '';

    // ─── 4. 留言(可选)──
    var commentHtml =
      '<div style="padding:14px 26px 6px;' + (summaryHtml || designateHtml ? 'border-top:1px solid var(--line-soft);' : '') + '">' +
        '<div style="font-size:12px;color:var(--ink-3);margin-bottom:6px;">留言(可选)</div>' +
        '<textarea data-modal-comment rows="3" placeholder="给确认人的备注…"' +
        ' style="width:100%;box-sizing:border-box;padding:10px 12px;border:1px solid var(--line-2);' +
        ' border-radius:8px;font-family:inherit;font-size:13px;color:var(--ink);background:var(--bg-elev);' +
        ' resize:vertical;outline:none;line-height:1.5;"></textarea>' +
      '</div>';

    // ─── 5. Footer(辅助说明 + 取消 / 确认)──
    var helperText = designateSteps.length ?
      '发起后' + (objectType === 'quotation' ? '报价单' : '单据') + '将被锁定,被指派人会收到日程待办' :
      '提交后将进入审批流程,审批中可召回';
    var primaryLabel = designateSteps.length ? (objectType === 'quotation' ? '技术确认' : actionLabel) : actionLabel;
    var footerHtml =
      '<div style="padding:14px 22px;border-top:1px solid var(--line-soft);background:var(--bg-page);' +
            'display:flex;align-items:center;gap:12px;">' +
        '<div style="flex:1;min-width:0;font-size:11.5px;color:var(--ink-4);line-height:1.5;">' +
          esc(helperText) +
        '</div>' +
        '<button type="button" data-modal-action="cancel"' +
        ' style="height:36px;padding:0 16px;border:1px solid var(--line-2);border-radius:7px;' +
        ' background:var(--bg-elev);color:var(--ink);cursor:pointer;font-size:13px;font-weight:500;">取消</button>' +
        '<button type="button" data-modal-action="confirm"' +
        ' style="height:36px;padding:0 18px;border:0;border-radius:7px;' +
        ' background:var(--accent);color:#fff;cursor:pointer;font-size:13px;font-weight:500;">' +
          esc(primaryLabel) +
        '</button>' +
      '</div>';

    panel.innerHTML =
      headerHtml +
      '<div style="overflow-y:auto;flex:1;">' +
        designateHtml +
        summaryHtml +
        commentHtml +
      '</div>' +
      footerHtml;

    overlay.appendChild(panel);
    document.body.appendChild(overlay);

    function close() { try { document.body.removeChild(overlay); } catch (e) {} }
    overlay.addEventListener('click', function (e) { if (e.target === overlay) close(); });
    panel.querySelectorAll('[data-modal-action="cancel"]').forEach(function (b) {
      b.addEventListener('click', close);
    });
    panel.querySelector('[data-modal-action="confirm"]').addEventListener('click', function () {
      // 收集 designated_approvers
      var designated = null;
      if (designateSteps.length) {
        designated = {};
        var missing = false;
        designateSteps.forEach(function (s) {
          var picked = panel.querySelector('input[name="designate_step_' + s.step_id + '"]:checked');
          var card = panel.querySelector('[data-designate-step-card="' + s.step_id + '"]');
          if (!picked) {
            missing = true;
            if (card) card.style.borderColor = 'var(--danger)';
          } else {
            if (card) card.style.borderColor = 'var(--line)';
            designated[s.step_id] = parseInt(picked.value, 10);
          }
        });
        if (missing) {
          if (g.ATToast) ATToast.error('请为每个步骤选择审批人');
          return;
        }
      }
      var commentEl = panel.querySelector('[data-modal-comment]');
      var comment = commentEl ? commentEl.value.trim() : '';
      close();
      onConfirm(designated, comment);
    });
  }
  function row(label, value) {
    return '<div style="display:flex;justify-content:space-between;gap:10px;padding:5px 0;font-size:12.5px;">' +
      '<span style="color:var(--ink-4);">' + esc(label) + '</span>' +
      '<span style="color:var(--ink);text-align:right;flex:1;">' + esc(value) + '</span>' +
    '</div>';
  }

  /* ============== API 操作 ============== */
  function postAction(root, path, body, onSuccess) {
    var apiBase = root.dataset.apiBase;
    var objId = root.dataset.objectId;
    fetch(apiBase + '/' + objId + '/' + path, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf(),
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify(body || {})
    }).then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (res) {
        if (!res.success && res.success !== undefined) {
          if (g.ATToast) ATToast.error(res.message || '操作失败');
          return;
        }
        if (g.ATToast) ATToast.success('已操作', '刷新中…');
        setTimeout(function () { location.reload(); }, 400);
        if (onSuccess) onSuccess(res);
      })
      .catch(function (e) {
        if (g.ATToast) ATToast.error('网络错误', e.message || '');
      });
  }

  // 先拉模板看是否有 submitter_designate 步骤,再决定 modal 内容
  function fetchTemplatesThenSubmit(root, action, actionLabel) {
    var apiBase = root.dataset.apiBase;
    var objId = root.dataset.objectId;
    function _doSubmit(designateSteps) {
      openSubmitModal(root, actionLabel, function (designated, comment) {
        var body = {};
        if (designated) body.designated_approvers = designated;
        if (comment)    body.comment = comment;
        postAction(root, action, Object.keys(body).length ? body : null);
      }, designateSteps);
    }
    fetch(apiBase + '/' + objId + '/templates', {
      headers: { 'X-Requested-With': 'XMLHttpRequest' }
    }).then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (res) {
        var templates = (res && res.templates) || [];
        var designateSteps = [];
        templates.forEach(function (t) {
          (t.designate_steps || []).forEach(function (s) { designateSteps.push(s); });
        });
        _doSubmit(designateSteps);
      })
      .catch(function () { _doSubmit([]); });
  }

  function submitApproval(root)   { fetchTemplatesThenSubmit(root, 'submit',   '提交审批'); }
  function resubmitApproval(root) { fetchTemplatesThenSubmit(root, 'resubmit', '重新提交'); }
  function recallApproval(root) {
    if (!g.ATConfirm) { if (g.ATToast) ATToast.error('AT 弹窗组件未加载'); return; }
    ATConfirm.show({
      title: '召回审批',
      message: '此操作会撤回当前审批,需要重新提交。',
      variant: 'danger', icon: 'warn',
      confirmText: '召回', cancelText: '取消',
      input: {
        label: '召回原因(可选)',
        placeholder: '说明召回理由,审批人可见…',
        multiline: true, rows: 3, maxLength: 500
      },
      onConfirm: function (reason) {
        postAction(root, 'recall', { reason: reason || '' });
      }
    });
  }

  function approveDecision(root, action, flow) {
    var label = action === 'approve' ? '同意' : '驳回';
    var instanceId = flow && flow.instance_id;
    if (!instanceId) { if (g.ATToast) ATToast.error('找不到审批实例 ID'); return; }
    if (!g.ATConfirm) { if (g.ATToast) ATToast.error('AT 弹窗组件未加载'); return; }

    // 项目失败审核(lost)同意时的归因认定:
    // 步骤1(部门经理)→ 个人因素为主;步骤2(总经理)→ 团队管理失责
    var attribution = null, chkOpt = null;
    if (action === 'approve' && root.dataset.objectType === 'project_hold'
        && root.dataset.status === 'lost') {
      var _steps = (flow && flow.steps) || [];
      var _curIdx = -1;
      for (var i = 0; i < _steps.length; i++) {
        if (_steps[i].status === 'current') { _curIdx = i; break; }
      }
      if (_curIdx === 0) {
        attribution = 'owner_fault';
        chkOpt = { label: '认定:个人因素为主(计入项目负责人的个人失败率)' };
      } else if (_curIdx === 1) {
        attribution = 'mgmt_fault';
        chkOpt = { label: '认定:团队管理失责(计入部门的团队失败率)' };
      }
    }

    ATConfirm.show({
      title: label + '审批',
      message: action === 'approve'
        ? '确认通过当前审批节点?可填写审批意见。'
        : '驳回后该报销单会回到驳回态,申请人可重新提交。请填写驳回原因。',
      variant: action === 'reject' ? 'danger' : 'accent',
      icon: action === 'reject' ? 'warn' : 'send',
      confirmText: label, cancelText: '取消',
      input: {
        label: action === 'reject' ? '驳回原因' : '审批意见',
        placeholder: action === 'reject' ? '请说明驳回原因(必填)' : '请写下你对本次申请的最终评判…',
        required: action === 'reject',
        multiline: true, rows: 3, maxLength: 500,
        defaultValue: ''
      },
      checkbox: chkOpt,
      onConfirm: function (comment, checked) {
        // 审批人 endpoint:/approval/approve/<instance_id> — 后端走 request.form,必须 form-urlencoded
        var body = new URLSearchParams();
        body.append('action', action);
        body.append('comment', comment || '');
        if (chkOpt && checked && attribution) body.append('attribution', attribution);
        body.append('csrf_token', csrf());
        fetch('/approval/approve/' + instanceId, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrf(),
            'X-Requested-With': 'XMLHttpRequest'
          },
          body: body.toString()
        }).then(function (r) { return r.json().catch(function () { return {}; }); })
          .then(function (res) {
            if (!res.success && res.success !== undefined) {
              if (g.ATToast) ATToast.error(res.message || (label + '失败'));
              return;
            }
            if (g.ATToast) ATToast.success('已' + label, '刷新中…');
            setTimeout(function () { location.reload(); }, 400);
          })
          .catch(function (e) {
            if (g.ATToast) ATToast.error('网络错误', e.message || '');
          });
      }
    });
  }

  /* ============== 头部按钮快捷入口 ============== */
  // 模板里写一个 <button data-at-approval-quick="submit|resubmit"
  //   data-api-base="/expense/api/approval" data-object-id="123"
  //   data-meta='{"currency_sym":"¥","total_amount":...,...}'>提交审批</button>
  // 即可直接弹摘要 modal + POST,无需经 chip。
  function bindQuickActionButtons() {
    document.querySelectorAll('[data-at-approval-quick]').forEach(function (btn) {
      if (btn._bound) return;
      btn._bound = true;
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        var action = btn.dataset.atApprovalQuick;
        // 从 api_base 推 object_type(如 '/quotation/api/approval' → 'quotation')
        var apiBase = btn.dataset.apiBase || '';
        var m = apiBase.match(/^\/([a-z_-]+)\/api\/approval$/);
        var objectType = btn.dataset.objectType || (m ? m[1].replace(/-/g, '_') : '');
        var fakeRoot = {
          dataset: {
            apiBase: apiBase,
            objectId: btn.dataset.objectId,
            objectType: objectType,
            meta: btn.dataset.meta || '{}'
          }
        };
        var label = action === 'resubmit' ? '重新提交' : '提交审批';
        function _doQuickSubmit(designateSteps) {
          openSubmitModal(fakeRoot, label, function (designated, comment) {
            var body = {};
            if (designated) body.designated_approvers = designated;
            if (comment)    body.comment = comment;
            postAction(fakeRoot, action, Object.keys(body).length ? body : null);
          }, designateSteps);
        }
        // 拉 templates 看 designate_steps,再弹 modal
        fetch(fakeRoot.dataset.apiBase + '/' + fakeRoot.dataset.objectId + '/templates', {
          headers: { 'X-Requested-With': 'XMLHttpRequest' }
        }).then(function (r) { return r.json().catch(function () { return {}; }); })
          .then(function (res) {
            var templates = (res && res.templates) || [];
            var designateSteps = [];
            templates.forEach(function (t) {
              (t.designate_steps || []).forEach(function (s) { designateSteps.push(s); });
            });
            _doQuickSubmit(designateSteps);
          })
          .catch(function () { _doQuickSubmit([]); });
      });
    });
  }

  /* ============== 入口 ============== */
  function bootstrap() {
    initAll();
    bindQuickActionButtons();
    // 从仪表盘"待审批"代办跳转过来时,hash=#approval → 自动展开 chip dropdown。
    // 支持 #approval(默认第一个 chip,如报备) 或 #approval-<object_type>(精确定位某审批 chip,
    // 如 #approval-project_hold 打开"项目搁置/失败审核"chip,避免误开报备审批)。
    if (window.location.hash.indexOf('#approval') === 0) {
      var _wantType = window.location.hash.slice('#approval'.length).replace(/^-/, '');
      var root = _wantType
        ? document.querySelector('[data-at-approval][data-object-type="' + _wantType + '"]')
        : document.querySelector('[data-at-approval]');
      if (root) {
        // 给页面初始渲染一点时间(layout shift 完成)再打开
        setTimeout(function () {
          try { root.scrollIntoView({ behavior: 'smooth', block: 'center' }); } catch (e) {}
          openPanel(root);
        }, 120);
      }
    }
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrap);
  } else {
    bootstrap();
  }
})(window);
