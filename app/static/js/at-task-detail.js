/**
 * AT 任务详情 — 独立页 + 选卡。单一数据源 /task/api/<id>,变更后重拉刷新。
 *
 * 选卡结构(对齐 TW 语义,层级正确):
 *   [概览] + [每个子任务一卡] + [＋新增]
 *   概览   : 主任务信息 + 主任务会审 + 评论(任务级,可发) + 全部附件(只读聚合)
 *   子任务卡: 子任务详情 + 里程碑会审 + 操作 + 进展记录(可记) + 本卡附件(可传)
 *
 * 数据关系(全部走现有接口,无新后端):
 *   进展记录 = reply(subtask_id=该卡, reply_type='update')
 *   任务级评论 = reply(subtask_id 空, reply_type='comment')
 *   子任务附件 = attachment(subtask_id=该卡);上传时带 subtask_id
 */
(function (g) {
  'use strict';
  var t = (typeof g.t === 'function') ? g.t : function (s) { return s; };
  var root = document.getElementById('taskDetail');
  if (!root) return;
  var TID = root.dataset.taskId;
  var UID = String(root.dataset.uid);
  var API = '/task/api/' + TID;
  var data = null;
  var tab = 'overview';   // 'overview' | 'st-<id>' | 'add'

  function csrf() { return (document.querySelector('meta[name="csrf-token"]') || {}).content || ''; }
  function toast(m, ty) { if (g.ATToast) ATToast[ty || 'success'](m); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function jget(url) { return fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } }).then(function (r) { return r.json(); }); }
  function jsend(url, method, body) {
    return fetch(url, { method: method, headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() }, body: body ? JSON.stringify(body) : undefined })
      .then(function (r) { return r.json(); });
  }
  // 统一走公用 ATConfirm.show(无 .open);opts.input 时兼具"确认+收原因",resolve 输入串(取消=null);否则 resolve 布尔
  function confirmAsync(msg, opts) {
    opts = opts || {};
    return new Promise(function (resolve) {
      if (g.ATConfirm && ATConfirm.show) {
        ATConfirm.show({
          title: opts.title || t('确认'), message: msg,
          confirmText: opts.confirmText, variant: opts.variant, icon: opts.icon,
          input: opts.input || null,
          onConfirm: function (val) { resolve(opts.input ? (val == null ? '' : val) : true); },
          onCancel: function () { resolve(opts.input ? null : false); }
        });
      } else {
        resolve(opts.input ? g.prompt(msg) : g.confirm(msg));
      }
    });
  }

  // ── AT 视觉片段 ──
  var STATUS = {
    pending: [t('待办'), 'warn'], in_progress: [t('进行中'), 'info'], delayed: [t('已延期'), 'danger'],
    completed: [t('已完成'), 'success'], paused: [t('已暂停'), 'neutral'], cancelled: [t('已取消'), 'neutral']
  };
  var REVIEW = { pending_review: [t('待复核'), 'warn'], approved: [t('复核通过'), 'success'], rejected: [t('复核驳回'), 'danger'] };
  var PRIORITY = { urgent: [t('紧急'), 'danger'], high: [t('高'), 'warn'], normal: [t('普通'), 'neutral'], low: [t('低'), 'neutral'] };
  var TONE = {
    neutral: ['var(--bg-active)', 'var(--ink-3)'], warn: ['var(--warn-soft)', 'var(--warn)'], info: ['var(--info-soft)', 'var(--info)'],
    success: ['var(--success-soft)', 'var(--success)'], danger: ['var(--danger-soft)', 'var(--danger)']
  };
  function pill(label, tone, dot) {
    var c = TONE[tone] || TONE.neutral;
    return '<span style="display:inline-flex;align-items:center;gap:6px;height:22px;padding:0 9px;border-radius:11px;font-size:11.5px;font-weight:500;white-space:nowrap;background:' + c[0] + ';color:' + c[1] + ';">'
      + (dot !== false ? '<span style="width:6px;height:6px;border-radius:50%;background:' + c[1] + ';"></span>' : '') + esc(label) + '</span>';
  }
  function statusPill(s) { var m = STATUS[s] || [s, 'neutral']; return pill(m[0], m[1]); }
  function progress(p, width) {
    width = width || 280;
    var color = p >= 100 ? 'var(--success)' : (p > 0 ? 'var(--accent)' : 'var(--ink-4)');
    return '<span style="display:inline-flex;align-items:center;gap:10px;"><span style="width:' + width + 'px;height:6px;background:var(--bg-sunk);border-radius:3px;overflow:hidden;">'
      + '<span style="display:block;width:' + p + '%;height:100%;background:' + color + ';border-radius:3px;transition:width .4s cubic-bezier(.2,.7,.2,1);"></span></span>'
      + '<span class="at-mono" style="font-size:13px;font-weight:600;color:var(--ink-2);">' + p + '%</span></span>';
  }
  // 头像调色板(与 at_avatar 宏一致:idx=(名字长度+1)%6,实色+白字 → 同一人到处同色)
  var AV_PALETTE = ['#D97757', '#2A5F8F', '#2F7155', '#7A5AE0', '#B8742E', '#A23B3B'];
  function avIdx(name) { return ((name || '?').length + 1) % AV_PALETTE.length; }
  function avatar(name, size) {
    size = size || 24; name = name || '?';
    var idx = avIdx(name);
    return '<span style="width:' + size + 'px;height:' + size + 'px;border-radius:50%;background:' + AV_PALETTE[idx] + ';color:#fff;display:inline-flex;align-items:center;justify-content:center;font-size:' + Math.round(size * 0.45) + 'px;font-weight:600;flex-shrink:0;" title="' + esc(name) + '">' + esc(name.charAt(0)) + '</span>';
  }
  function who(name) { return '<span style="display:inline-flex;align-items:center;gap:8px;color:var(--ink-2);font-size:13px;">' + avatar(name, 24) + esc(name || '—') + '</span>'; }
  function fdate(iso) { return iso ? iso.slice(0, 10) : '—'; }
  function fdt(iso) { return iso ? iso.slice(0, 16).replace('T', ' ') : '—'; }
  function pctOf(d) { var sc = d.subtask_count || 0, sd = d.subtask_completed || 0; return sc > 0 ? Math.floor(sd * 100 / sc) : (d.status === 'completed' ? 100 : 0); }
  // 提交完成进入审核 / 已完成 / 已取消 → 锁定任务下全部交互(仅审核浮层操作保留)
  function isLocked() { return ['pending_review', 'completed', 'cancelled'].indexOf(data && data.status) >= 0; }

  // ── 数据切片 ──
  function taskComments() { return (data.replies || []).filter(function (r) { return (!r.reply_type || r.reply_type === 'comment') && !r.subtask_id; }); }
  function subUpdates(sid) { return (data.replies || []).filter(function (r) { return r.reply_type === 'update' && String(r.subtask_id) === String(sid); }); }
  function subAttachments(sid) { return (data.attachments || []).filter(function (a) { return String(a.subtask_id) === String(sid); }); }
  function subById(sid) { return (data.subtasks || []).filter(function (s) { return String(s.id) === String(sid); })[0]; }

  function btn(label, onclick, variant) {
    var st = variant === 'primary' ? 'background:var(--accent);color:#fff;border:0;'
      : (variant === 'danger' ? 'background:var(--bg-elev);color:var(--danger);border:1px solid var(--line-2);'
        : 'background:var(--bg-elev);color:var(--ink-2);border:1px solid var(--line-2);');
    return '<button type="button" onclick="' + onclick + '" style="height:32px;padding:0 13px;border-radius:6px;font-size:12.5px;font-weight:500;cursor:pointer;' + st + '">' + esc(label) + '</button>';
  }
  var ICON = {
    pause: '<rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/>',
    play: '<path d="M7 4v16l13-8z"/>',
    edit: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
    ban: '<circle cx="12" cy="12" r="9"/><line x1="5.6" y1="5.6" x2="18.4" y2="18.4"/>',
    trash: '<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="M6 6l1 14h10l1-14"/>',
    file: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/>',
    download: '<path d="M12 3v12"/><path d="M7 10l5 5 5-5"/><path d="M5 21h14"/>',
    plus: '<path d="M12 5v14M5 12h14"/>'
  };
  function svg(name, sz) { return '<svg width="' + (sz || 16) + '" height="' + (sz || 16) + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' + ICON[name] + '</svg>'; }
  function card(title, count, action, body, noPad, anchorId) {
    return '<section class="at-section"' + (anchorId ? ' id="' + anchorId + '"' : '') + ' style="margin-bottom:16px;scroll-margin-top:80px;">'
      + '<header class="at-section-h" style="display:flex;align-items:center;gap:8px;">'
      + '<h3 class="at-section-title">' + esc(title) + '</h3>'
      + (count != null ? '<span class="at-mono at-tab-num" style="font-size:11px;color:var(--ink-4);">' + count + '</span>' : '')
      + (action ? '<div style="margin-left:auto;">' + action + '</div>' : '')
      + '</header><div class="at-section-body"' + (noPad ? ' style="padding:0;"' : '') + '>' + body + '</div></section>';
  }
  function iconBtn(title, onclick, name, danger) {
    return '<button type="button" title="' + esc(title) + '" aria-label="' + esc(title) + '" onclick="' + onclick + '" '
      + 'style="width:32px;height:32px;display:inline-flex;align-items:center;justify-content:center;border:1px solid var(--line-2);border-radius:6px;background:var(--bg-elev);color:' + (danger ? 'var(--danger)' : 'var(--ink-2)') + ';cursor:pointer;">'
      + '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' + ICON[name] + '</svg></button>';
  }

  // ── 渲染 ──
  function render() {
    var d = data, p = pctOf(d), html = '';
    // header:标题/状态(左) + 操作(右,图标按钮)
    html += '<div style="display:flex;align-items:center;gap:14px;margin-bottom:14px;">';
    html += '<div style="flex:1;min-width:0;display:flex;align-items:center;gap:12px;flex-wrap:wrap;">';
    html += '<span style="font-size:21px;font-weight:600;letter-spacing:-.01em;color:var(--ink);">' + esc(d.title) + '</span>';
    // 审核中(pending_review)只显示审核徽章,不再叠加原始状态徽章
    if (d.status !== 'pending_review') html += statusPill(d.status);
    // 审核徽章(可点开浮层) — 仅审计任务进入审核后出现
    if (d.review_status && (d.reviewers || []).length) {
      var rv = REVIEW[d.review_status] || [d.review_status, 'neutral'];
      html += '<span style="position:relative;display:inline-flex;">'
        + '<button type="button" onclick="__toggleReviewPop(event)" style="border:0;background:transparent;padding:0;cursor:pointer;display:inline-flex;align-items:center;gap:3px;">'
        + pill(rv[0], rv[1]) + '<span style="color:var(--ink-4);font-size:10px;">▾</span></button>'
        + '<div id="reviewPop" style="display:none;position:absolute;top:30px;left:0;z-index:60;width:360px;max-width:80vw;background:var(--bg-elev);border:1px solid var(--line-2);border-radius:12px;box-shadow:0 12px 32px rgba(0,0,0,.16);padding:14px;">'
        + '<div style="font-size:11px;font-weight:500;color:var(--ink-3);letter-spacing:.08em;text-transform:uppercase;margin-bottom:12px;">' + t('任务会审') + '</div>'
        + reviewBlock(d) + '</div></span>';
    }
    html += '</div>';
    html += '<div style="display:flex;align-items:center;gap:6px;flex-shrink:0;">' + actionButtons(d) + '</div>';
    html += '</div>';
    html += '<div style="display:flex;align-items:center;gap:16px;margin:0 0 18px;">' + progress(p, 280);
    if ((d.subtask_count || 0) > 0) html += '<span class="at-mono" style="font-size:12.5px;color:var(--ink-3);">' + (d.subtask_completed || 0) + ' / ' + d.subtask_count + ' ' + t('子任务完成') + '</span>';
    html += '</div>';

    // tabs:概览 + 子任务 + 新增
    html += '<div class="td-tabs" style="display:flex;gap:2px;border-bottom:1px solid var(--line);margin-bottom:20px;overflow-x:auto;">';
    html += tabBtn('overview', t('概览'), null);
    (d.subtasks || []).forEach(function (s, i) {
      var dot = s.status === 'completed' ? '' : (s.is_milestone && s.milestone_status === 'pending_confirmation' ? ' ●' : '');
      var lbl = (i + 1) + '. ' + s.title + (s.is_milestone ? ' ★' : '');
      tab; html += tabBtn('st-' + s.id, lbl, null, dot, s.status === 'completed');
    });
    // 子任务可由可访问者(创建/负责/协助等)新建,里程碑确认人除外;锁定态(审核中/完成/取消)不可加
    if (!d.is_milestone_reviewer_only && !isLocked())
      html += '<button type="button" onclick="__subFormOpen()" title="' + t('新增子任务') + '" style="padding:11px 16px;background:transparent;border:0;border-bottom:1.5px solid transparent;margin-bottom:-1px;cursor:pointer;color:var(--accent);font-size:15px;">＋</button>';
    html += '</div>';

    // pane
    html += '<div id="td-pane">' + paneFor(tab) + '</div>';
    root.innerHTML = html;
    afterRender();
  }
  function tabBtn(key, label, n, dot, done) {
    return '<button type="button" data-tab="' + key + '" onclick="__taskTab(\'' + key + '\')" class="' + (tab === key ? 'on' : '') + '" '
      + 'style="padding:11px 16px;background:transparent;border:0;border-bottom:1.5px solid transparent;margin-bottom:-1px;cursor:pointer;'
      + 'color:var(--ink-3);font-size:13px;white-space:nowrap;' + (done ? 'opacity:.6;' : '') + '">'
      + '<span style="max-width:160px;overflow:hidden;text-overflow:ellipsis;display:inline-block;vertical-align:bottom;">' + esc(label) + '</span>'
      + (dot ? '<span style="color:var(--accent);">' + dot + '</span>' : '') + '</button>';
  }
  function paneFor(key) {
    if (key === 'overview') return paneOverview(data);
    if (key === 'add') return paneAddSubtask();
    if (key.indexOf('st-') === 0) { var s = subById(key.slice(3)); return s ? paneSubtask(s) : paneOverview(data); }
    return paneOverview(data);
  }

  function actionButtons(d) {
    var h = '', active = !isLocked();   // 审核中/已完成/已取消 → 锁定,不出操作按钮
    // 主动作:文字主按钮
    if (d.can_complete && active && d.review_status !== 'pending_review') h += btn(t('完成'), '__taskComplete()', 'primary');
    if (d.review_status === 'rejected' && (d.is_creator || d.can_complete)) h += btn(t('重新提交审核'), '__taskResubmit()', 'primary');
    // 次动作:图标按钮(暂停/编辑/取消/删除)
    if (active && (d.can_edit || d.can_complete)) h += (d.status === 'paused')
      ? iconBtn(t('启动'), '__taskResume()', 'play')
      : iconBtn(t('暂停'), '__taskPause()', 'pause');
    if (d.can_edit && active) h += iconBtn(t('编辑'), '__taskEdit()', 'edit');
    if (d.can_edit && active) h += iconBtn(t('取消任务'), '__taskCancel()', 'ban');
    if (d.is_creator && active) h += iconBtn(t('删除'), '__taskDelete()', 'trash', true);
    return h;
  }

  // ── 概览 ──
  function infoRow(label, valueHtml) {
    return '<div style="display:flex;gap:20px;padding:11px 0;border-bottom:1px solid var(--line-soft);">'
      + '<div style="width:96px;flex-shrink:0;color:var(--ink-3);font-size:12.5px;">' + esc(label) + '</div>'
      + '<div style="flex:1;color:var(--ink);font-size:13px;">' + valueHtml + '</div></div>';
  }
  function sectTitle(txt, n) { return '<div style="font-size:11px;font-weight:500;color:var(--ink-3);letter-spacing:.08em;text-transform:uppercase;margin:26px 0 12px;">' + esc(txt) + (n != null ? ' <span class="at-mono" style="color:var(--ink-4);">' + n + '</span>' : '') + '</div>'; }
  // 概览:两列布局(左=基本信息+评论,右=变更历史+附件;会审卡全宽置顶)
  function paneOverview(d) {
    // 基本信息卡
    var info = '';
    if (d.description) info += '<p style="color:var(--ink-2);margin:0 0 10px;white-space:pre-wrap;">' + esc(d.description) + '</p>';
    var prio = PRIORITY[d.priority] || [d.priority, 'neutral'];
    info += '<dl style="margin:0;">';
    // 指派 + 创建 一行(纯名字,无徽章)
    info += '<div class="at-info-row" style="align-items:baseline;">'
      + '<dt>' + t('指派给') + '</dt><dd style="color:var(--ink);">' + esc(d.assignee_name || '—') + '</dd>'
      + '<dt style="width:56px;">' + t('创建人') + '</dt><dd style="color:var(--ink);">' + esc(d.creator_name || '—') + '</dd></div>';
    if ((d.shared_with_users || []).length) info += rowDD(t('协助人员'), '<span style="color:var(--ink);">' + (d.shared_with_users || []).map(function (id) { return esc(uname(id)); }).join('、') + '</span>');
    // 审核人 + 优先级 一行(审核人左、优先级右);无审核人时优先级单独成行
    if ((d.reviewers || []).length) {
      info += '<div class="at-info-row" style="align-items:baseline;">'
        + '<dt>' + t('审核人') + '</dt><dd style="color:var(--ink);">' + d.reviewers.map(function (r) { return esc(r.reviewer_name); }).join('、') + '</dd>'
        + '<dt style="width:56px;">' + t('优先级') + '</dt><dd>' + pill(prio[0], prio[1], false) + '</dd></div>';
    } else {
      info += rowDD(t('优先级'), pill(prio[0], prio[1], false));
    }
    info += rowDD(t('开始 / 截止'), '<span class="at-mono">' + fdate(d.start_date) + '</span><span style="color:var(--ink-4);margin:0 14px;">→</span><span class="at-mono">' + fdate(d.due_date) + '</span>');
    if (d.project_name) info += rowDD(t('关联项目'), '<a href="/project/' + d.project_id + '/at_view" style="color:var(--accent);text-decoration:none;">' + esc(d.project_name) + '</a>');
    if (d.customer_name) info += rowDD(t('关联客户'), esc(d.customer_name));
    if (d.quotation_number) info += rowDD(t('关联报价'), esc(d.quotation_number));
    if (d.external_link) info += rowDD(t('外部链接'), '<a href="' + esc(d.external_link) + '" target="_blank" style="color:var(--accent);text-decoration:none;">' + esc(d.external_link_label || d.external_link) + ' ↗</a>');
    info += '</dl>';
    var cardInfo = card(t('基本信息'), null, null, info);

    // 变更历史卡(报价时间线样式;最近的在最上面)
    var chg = (d.replies || []).filter(function (r) { return r.reply_type === 'update' && !r.subtask_id; }).slice().reverse();
    var cardChange = card(t('变更历史'), chg.length, null, changeTimeline(chg));

    // 附件卡(项目附件上传样式:任务级)
    var atts = d.attachments || [];
    var upAction = (!isLocked())
      ? '<button type="button" onclick="document.getElementById(\'ovAttInput\').click()" style="border:0;background:transparent;color:var(--accent);font-size:12.5px;cursor:pointer;display:inline-flex;align-items:center;gap:4px;">' + svg('plus', 13) + t('上传') + '</button>' : null;
    var attBody = '';
    if (!atts.length) attBody = '<div style="text-align:center;padding:18px;color:var(--ink-4);font-size:12px;">' + t('暂无附件') + '</div>';
    else atts.forEach(function (a, i) { attBody += projAttRow(a, i === atts.length - 1); });
    attBody += '<input type="file" id="ovAttInput" style="display:none;" onchange="__attUpload(this)">';
    var cardAtt = card(t('附件'), atts.length, upAction, attBody, true);

    // 评论卡(公用 at-comments 组件:只刷新评论区,不重载整页)
    var cmts = taskComments();
    var cmtBody = '<div id="ovCmtList" style="margin-bottom:12px;"></div>'
      + '<div style="display:flex;gap:10px;"><textarea id="ovCmtInput" placeholder="' + t('写评论…') + '" ' + (isLocked() ? 'disabled' : '') + ' style="flex:1;min-height:56px;border:1px solid var(--line-2);background:var(--bg-elev);border-radius:10px;padding:10px 12px;font-size:13px;color:var(--ink);resize:vertical;box-sizing:border-box;' + (isLocked() ? 'opacity:.5;' : '') + '"></textarea>'
      + '<button type="button" id="ovCmtSend" ' + (isLocked() ? 'disabled' : '') + ' style="align-self:flex-end;height:36px;padding:0 16px;border:0;border-radius:6px;background:var(--accent);color:#fff;font-size:13px;font-weight:500;cursor:pointer;' + (isLocked() ? 'opacity:.5;' : '') + '">' + t('发送') + '</button></div>';
    var cardCmt = card(t('评论'), cmts.length, null, cmtBody, false, 'card-comments');

    // 会审改为标题旁徽章浮层(见 render 头部),概览不再常驻会审卡
    var h = '';
    // 两列:左=基本信息+附件+评论,右=变更历史
    h += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start;">'
      + '<div>' + cardInfo + cardAtt + cardCmt + '</div>'
      + '<div>' + cardChange + '</div>'
      + '</div>';
    return h;
  }
  function rowDD(label, valueHtml) {
    return '<div class="at-info-row"><dt>' + esc(label) + '</dt><dd>' + valueHtml + '</dd></div>';
  }
  function changeTimeline(chg) {
    if (!chg.length) return '<div style="text-align:center;padding:18px;color:var(--ink-4);font-size:12px;">' + t('暂无变更') + '</div>';
    var h = '';
    chg.forEach(function (r, i) {
      var first = i === 0, last = i === chg.length - 1;
      var color = first ? 'var(--info)' : 'var(--ink-3)';
      h += '<div style="display:grid;grid-template-columns:24px 1fr;gap:10px;position:relative;padding-bottom:' + (last ? 0 : 16) + 'px;">';
      if (!last) h += '<div style="position:absolute;left:11.5px;top:24px;bottom:-4px;width:1px;background:var(--line-2);"></div>';
      h += '<div style="width:24px;height:24px;border-radius:50%;z-index:1;background:' + (first ? color : 'var(--bg-page)') + ';border:' + (first ? '0' : '1.5px solid ' + color) + ';color:' + (first ? '#fff' : color) + ';display:flex;align-items:center;justify-content:center;' + (first ? 'box-shadow:0 0 0 4px ' + color + '22;' : '') + '">' + svg('edit', 11) + '</div>';
      h += '<div style="padding-top:2px;min-width:0;"><div style="font-size:12.5px;color:' + (first ? 'var(--ink)' : 'var(--ink-2)') + ';line-height:1.5;word-break:break-word;white-space:pre-wrap;">' + esc(r.content) + '</div>'
        + '<div class="at-dim" style="font-size:11px;margin-top:3px;display:flex;align-items:center;gap:5px;"><span>' + esc(r.author_name || '') + '</span><span style="color:var(--ink-4);">·</span><span class="at-mono at-tab-num">' + fdt(r.created_at) + '</span></div></div></div>';
    });
    return h;
  }
  function projAttRow(a, last) {
    var del = (String(a.uploaded_by) === UID || data.is_creator)
      ? '<button type="button" onclick="__attDelete(' + a.id + ')" title="' + t('删除') + '" style="border:0;background:transparent;color:var(--ink-4);cursor:pointer;padding:2px;display:inline-flex;flex-shrink:0;">' + svg('trash', 14) + '</button>' : '';
    return '<div style="display:flex;align-items:center;gap:8px;padding:10px 18px;border-bottom:' + (last ? '0' : '1px solid var(--line-soft)') + ';">'
      + '<span style="color:var(--ink-3);flex-shrink:0;">' + svg('file', 14) + '</span>'
      + '<div style="flex:1;min-width:0;"><div onclick="__attPreview(' + a.id + ')" title="' + esc(a.filename) + '" style="font-size:12.5px;color:var(--ink);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;cursor:pointer;" onmouseover="this.style.color=\'var(--accent)\'" onmouseout="this.style.color=\'var(--ink)\'">' + esc(a.filename) + '</div>'
      + '<div class="at-dim" style="font-size:10.5px;">' + fdt(a.created_at) + (a.uploader_name ? ' · ' + esc(a.uploader_name) : '') + (a.subtask_id ? ' · ' + esc(subTitleOf(a.subtask_id) || '') : '') + '</div></div>'
      + '<a href="' + API + '/attachments/' + a.id + '/download" title="' + t('下载') + '" style="color:var(--ink-4);padding:2px;display:inline-flex;flex-shrink:0;">' + svg('download', 14) + '</a>'
      + del + '</div>';
  }
  function subTitleOf(sid) { if (!sid) return null; var s = subById(sid); return s ? s.title : null; }

  function reviewBlock(d) {
    var RATING = { exceed: [t('超出预期'), 'success', '×1.5'], meet: [t('达标'), 'neutral', '×1.0'], below: [t('低于预期'), 'danger', '×0.5'] };
    var h = '';
    (d.reviewers || []).forEach(function (r) {
      h += '<div style="display:flex;align-items:center;gap:12px;padding:12px 14px;border:1px solid var(--line);border-radius:10px;margin-bottom:8px;">' + avatar(r.reviewer_name, 26);
      h += '<div style="flex:1;min-width:0;"><div style="font-size:13px;color:var(--ink);">' + esc(r.reviewer_name) + '</div>'
        + '<div style="font-size:11.5px;color:var(--ink-3);margin-top:2px;">' + (r.status === 'pending' ? t('待复核') : (fdt(r.reviewed_at) + (r.comment ? ' · ' + esc(r.comment) : ''))) + '</div></div>';
      if (r.status === 'approved' && r.rating && RATING[r.rating]) { var rt = RATING[r.rating]; h += '<span style="font-size:12.5px;font-weight:600;color:' + TONE[rt[1]][1] + ';">' + rt[0] + ' ' + rt[2] + '</span>'; }
      else if (r.status === 'rejected') h += pill(t('驳回'), 'danger', false);
      else h += pill(t('待复核'), 'warn');
      h += '</div>';
    });
    if (d.can_review) {
      h += '<div style="margin-top:10px;padding:14px;border:1px solid var(--line);border-radius:10px;background:var(--bg-sunk);">'
        + '<div style="font-size:12px;color:var(--ink-3);margin-bottom:8px;">' + t('我的复核') + '</div>'
        + '<div class="at-seg" id="revRating" style="margin-bottom:10px;"><button type="button" data-r="below">' + t('低于预期') + '</button><button type="button" class="on" data-r="meet">' + t('达标') + '</button><button type="button" data-r="exceed">' + t('超出预期') + '</button></div>'
        + '<textarea id="revComment" placeholder="' + t('复核意见(可选)') + '" style="width:100%;min-height:52px;border:1px solid var(--line-2);background:var(--bg-elev);border-radius:8px;padding:9px 11px;font-size:13px;color:var(--ink);resize:vertical;margin-bottom:10px;box-sizing:border-box;"></textarea>'
        + '<div style="display:flex;gap:8px;">' + btn(t('通过'), '__review(\'approve\')', 'primary') + btn(t('驳回'), '__review(\'reject\')', 'danger') + '</div></div>';
    }
    return h;
  }
  function commentList(rs) {
    if (!rs.length) return '<div class="at-dim" style="font-size:12.5px;">' + t('暂无评论') + '</div>';
    var h = '';
    rs.forEach(function (r) {
      var canDel = String(r.author_id) === UID || data.is_creator;
      h += '<div class="tcmt" style="display:flex;gap:10px;margin-bottom:14px;">' + avatar(r.author_name, 28)
        + '<div style="flex:1;min-width:0;"><div style="font-size:12px;color:var(--ink-3);margin-bottom:3px;display:flex;align-items:center;gap:6px;">'
        + '<b style="color:var(--ink);font-weight:600;">' + esc(r.author_name) + '</b><span>·</span><span class="at-mono">' + fdt(r.created_at) + '</span>'
        + (canDel ? '<button type="button" class="tcmt-del" onclick="__cmtDelete(' + r.id + ')" title="' + t('删除') + '" style="margin-left:auto;border:0;background:transparent;color:var(--ink-4);cursor:pointer;font-size:15px;line-height:1;">×</button>' : '')
        + '</div><div style="font-size:13px;color:var(--ink-2);white-space:pre-wrap;">' + esc(r.content) + '</div></div></div>';
    });
    return h;
  }
  function attRow(a, canDel, subLabel) {
    var icon = (function (n) { var e = (n || '').split('.').pop().toLowerCase(); if (['png', 'jpg', 'jpeg', 'gif', 'webp'].indexOf(e) >= 0) return '🖼️'; if (e === 'pdf') return '📕'; if (['doc', 'docx'].indexOf(e) >= 0) return '📘'; if (['xls', 'xlsx'].indexOf(e) >= 0) return '📗'; return '📄'; })(a.filename);
    var sz = a.file_size ? (a.file_size < 1024 ? a.file_size + ' B' : (a.file_size < 1048576 ? (a.file_size / 1024).toFixed(0) + ' KB' : (a.file_size / 1048576).toFixed(1) + ' MB')) : '';
    var h = '<div style="display:flex;align-items:center;gap:12px;padding:11px 14px;border:1px solid var(--line);border-radius:10px;margin-bottom:8px;">'
      + '<span style="width:34px;height:34px;border-radius:8px;background:var(--bg-sunk);display:inline-flex;align-items:center;justify-content:center;font-size:15px;">' + icon + '</span>'
      + '<div style="flex:1;min-width:0;"><div onclick="__attPreview(' + a.id + ')" title="' + esc(a.filename) + '" style="font-size:13px;color:var(--ink);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;cursor:pointer;" onmouseover="this.style.color=\'var(--accent)\'" onmouseout="this.style.color=\'var(--ink)\'">' + esc(a.filename) + '</div>'
      + '<div class="at-mono" style="font-size:11.5px;color:var(--ink-4);margin-top:2px;">' + sz + (a.uploader_name ? ' · ' + esc(a.uploader_name) : '') + (subLabel ? ' · ' + esc(subLabel) : '') + '</div></div>'
      + '<a href="' + API + '/attachments/' + a.id + '/download" style="height:28px;padding:0 10px;border:1px solid var(--line-2);border-radius:6px;background:var(--bg-elev);color:var(--ink-2);font-size:12px;text-decoration:none;display:inline-flex;align-items:center;">' + t('下载') + '</a>';
    if (canDel && (String(a.uploaded_by) === UID || data.is_creator)) h += '<button type="button" onclick="__attDelete(' + a.id + ')" style="margin-left:6px;width:28px;height:28px;border:1px solid var(--line-2);border-radius:6px;background:var(--bg-elev);color:var(--ink-3);cursor:pointer;">×</button>';
    return h + '</div>';
  }

  // ── 子任务卡 ──
  function paneSubtask(s) {
    var d = data, ro = isLocked();   // 锁定态(审核中/完成/取消):子任务操作/进展/附件全只读
    var h = '<div style="max-width:920px;">';
    // 详情头
    h += '<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:10px;">'
      + '<span style="font-size:16px;font-weight:600;color:var(--ink);">' + esc(s.title) + '</span>' + statusPill(s.status);
    if (s.is_milestone) { var mst = s.milestone_status === 'confirmed' ? [t('里程碑·已确认'), 'success'] : (s.milestone_status === 'pending_confirmation' ? [t('里程碑·待确认'), 'warn'] : (s.milestone_status === 'rejected' ? [t('里程碑·已驳回'), 'danger'] : [t('里程碑'), 'info'])); h += pill('★ ' + mst[0], mst[1], false); }
    h += '</div>';
    h += '<div style="font-size:12.5px;color:var(--ink-3);margin-bottom:10px;">' + (s.assignee_name ? esc(s.assignee_name) + ' · ' : '') + '<span class="at-mono">' + fdate(s.start_date) + ' → ' + fdate(s.due_date) + '</span></div>';
    if (s.description) h += '<p style="color:var(--ink-2);margin:0 0 12px;white-space:pre-wrap;">' + esc(s.description) + '</p>';
    if (s.is_milestone && s.milestone_criteria) h += '<div style="font-size:12.5px;color:var(--ink-3);margin-bottom:12px;"><b>' + t('达标条件') + ':</b> ' + esc(s.milestone_criteria) + '</div>';

    // 里程碑会审人
    if (s.is_milestone && (s.milestone_reviewers || []).length) {
      h += '<div style="display:flex;flex-wrap:wrap;gap:10px;margin-bottom:12px;">';
      s.milestone_reviewers.forEach(function (r) {
        var ic = r.status === 'confirmed' ? '✓' : (r.status === 'rejected' ? '✕' : '○');
        var col = r.status === 'confirmed' ? 'var(--success)' : (r.status === 'rejected' ? 'var(--danger)' : 'var(--ink-4)');
        h += '<span style="display:inline-flex;align-items:center;gap:5px;font-size:12px;color:var(--ink-2);"><span style="color:' + col + ';">' + ic + '</span>' + esc(r.reviewer_name) + (r.comment ? '<span style="color:var(--ink-4);">「' + esc(r.comment) + '」</span>' : '') + '</span>';
      });
      h += '</div>';
    }

    // 操作
    if (!ro) {
      var acts = '';
      if (s.status === 'pending') acts += btn(t('开始'), '__subStatus(' + s.id + ',\'start\')');
      if ((s.status === 'in_progress' || s.status === 'delayed') && !(s.is_milestone && s.milestone_status === 'rejected')) acts += btn(s.is_milestone ? t('提交确认') : t('完成'), '__subStatus(' + s.id + ',\'complete\')', 'primary');
      if (s.is_milestone && s.milestone_status === 'rejected' && !d.is_milestone_reviewer_only) acts += btn(t('再次提交'), '__subStatus(' + s.id + ',\'complete\')', 'primary');
      // 里程碑确认人操作
      if (s.is_milestone && s.milestone_status === 'pending_confirmation') {
        var mine = (s.milestone_reviewers || []).filter(function (r) { return String(r.reviewer_id) === UID && r.status === 'pending'; });
        if (mine.length) { acts += btn(t('确认通过'), '__milestone(' + s.id + ',\'confirm\')', 'primary'); acts += btn(t('驳回'), '__milestone(' + s.id + ',\'reject\')', 'danger'); }
      }
      if (!d.is_milestone_reviewer_only && s.status !== 'completed') acts += btn(t('编辑'), '__subEdit(' + s.id + ')');
      if (!d.is_milestone_reviewer_only && s.status !== 'completed') acts += btn(t('删除'), '__subDelete(' + s.id + ')', 'danger');
      if (acts) h += '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:6px;">' + acts + '</div>';
    }

    // 进展记录(公用 at-comments 组件:键=子任务 id,reply_type=update)
    var ups = subUpdates(s.id);
    h += sectTitle(t('进展记录'), ups.length);
    h += '<div id="upList" style="margin-bottom:12px;"></div>';
    h += '<div style="display:flex;gap:10px;"><textarea id="upInput" placeholder="' + t('记录今日进展…') + '" ' + (ro ? 'disabled' : '') + ' style="flex:1;min-height:50px;border:1px solid var(--line-2);background:var(--bg-elev);border-radius:10px;padding:9px 11px;font-size:13px;color:var(--ink);resize:vertical;box-sizing:border-box;' + (ro ? 'opacity:.5;' : '') + '"></textarea>'
      + '<button type="button" id="upSend" ' + (ro ? 'disabled' : '') + ' style="align-self:flex-end;height:34px;padding:0 14px;border:0;border-radius:6px;background:var(--accent);color:#fff;font-size:12.5px;font-weight:500;cursor:pointer;' + (ro ? 'opacity:.5;' : '') + '">' + t('记录') + '</button></div>';

    // 本卡附件
    var atts = subAttachments(s.id);
    h += sectTitle(t('附件'), atts.length);
    if (!atts.length) h += '<div class="at-dim" style="font-size:12.5px;">' + t('暂无附件') + '</div>';
    atts.forEach(function (a) { h += attRow(a, true, null); });
    if (!ro) h += '<div style="margin-top:8px;"><label style="display:inline-flex;align-items:center;gap:6px;height:32px;padding:0 13px;border:1px solid var(--line-2);border-radius:6px;background:var(--bg-elev);color:var(--ink-2);font-size:12.5px;cursor:pointer;">⬆ ' + t('上传附件') + '<input type="file" style="position:absolute;width:1px;height:1px;opacity:0;" onchange="__attUpload(this,' + s.id + ')"></label></div>';
    h += '</div>';
    return h;
  }

  // ── 新增子任务 ──
  function paneAddSubtask() {
    return '<div style="max-width:520px;">'
      + sectTitle(t('新增子任务'))
      + '<input id="newSubTitle" type="text" placeholder="' + t('子任务标题') + '" style="width:100%;height:36px;border:1px solid var(--line-2);background:var(--bg-elev);border-radius:8px;padding:0 12px;font-size:13px;color:var(--ink);margin-bottom:10px;box-sizing:border-box;">'
      + '<textarea id="newSubDesc" placeholder="' + t('描述(可选)') + '" style="width:100%;min-height:60px;border:1px solid var(--line-2);background:var(--bg-elev);border-radius:8px;padding:9px 11px;font-size:13px;color:var(--ink);resize:vertical;margin-bottom:10px;box-sizing:border-box;"></textarea>'
      + '<label style="display:inline-flex;align-items:center;gap:6px;font-size:12.5px;color:var(--ink-3);margin-bottom:14px;"><input id="newSubMile" type="checkbox">' + t('设为里程碑') + '</label>'
      + '<div style="display:flex;gap:8px;">' + btn(t('创建'), '__subAdd()', 'primary') + btn(t('取消'), '__taskTab(\'overview\')') + '</div></div>';
  }

  // ── 交互 ──
  g.__taskTab = function (k) {
    tab = k;
    document.querySelectorAll('.td-tabs > button').forEach(function (b) { b.classList.toggle('on', b.dataset.tab === k); });
    var pane = document.getElementById('td-pane'); if (pane) pane.innerHTML = paneFor(k);
    afterRender();
  };
  function after(d) { if (d && d.success === false) { toast(d.message || t('操作失败'), 'error'); return; } if (d && d.message) toast(d.message); load(); }

  g.__taskComplete = function () { confirmAsync(t('确认完成此任务?')).then(function (ok) { if (ok) jsend(API + '/complete', 'POST').then(after); }); };
  g.__taskResubmit = function () { jsend(API + '/resubmit-review', 'POST').then(after); };
  g.__taskPause = function () { confirmAsync(t('确认暂停此任务?'), { title: t('暂停任务'), confirmText: t('暂停'), variant: 'warn', input: { label: t('暂停理由'), placeholder: t('请填写暂停理由'), required: true, multiline: true } }).then(function (r) { if (r === null) return; jsend(API + '/pause', 'POST', { reason: r }).then(after); }); };
  g.__taskResume = function () { jsend(API + '/resume', 'POST').then(after); };
  g.__taskCancel = function () { confirmAsync(t('确认取消此任务?'), { title: t('取消任务'), variant: 'warn' }).then(function (ok) { if (ok) jsend(API + '/cancel', 'POST').then(after); }); };
  g.__taskDelete = function () { confirmAsync(t('确认删除此任务?此操作不可恢复。'), { title: t('删除任务'), confirmText: t('删除'), variant: 'danger' }).then(function (ok) { if (ok) jsend(API, 'DELETE').then(function (d) { if (d.success) { toast(d.message || t('已删除')); location.href = '/task/at'; } else toast(d.message || t('删除失败'), 'error'); }); }); };
  g.__taskEdit = function () {
    ensureUsers().then(function () {
      var d = data;
      var body = field('tfTitle', t('标题'), d.title)
        + area('tfDesc', t('描述'), d.description || '')
        + pickField('tfAssignee', t('负责人'), false, d.assignee_id ? [{ id: d.assignee_id, name: d.assignee_name }] : [])
        + selField('tfPriority', t('优先级'), [['urgent', t('紧急')], ['high', t('高')], ['normal', t('普通')], ['low', t('低')]], d.priority || 'normal')
        + dateRow('tfStart', t('开始'), d.start_date, 'tfDue', t('截止'), d.due_date)
        + pickField('tfShared', t('协助人员'), true, (d.shared_with_users || []).map(function (id) { return { id: id, name: uname(id) }; }))
        + pickField('tfReviewers', t('审核人(可选,会审)'), true, (d.reviewers || []).map(function (r) { return { id: r.reviewer_id, name: r.reviewer_name }; }));
      openModal(t('编辑任务'), body, function () {
        var title = (val('tfTitle') || '').trim(); if (!title) { toast(t('任务标题不能为空'), 'error'); return; }
        var aid = pickValue('tfAssignee')[0]; if (!aid) { toast(t('请选择指派人'), 'error'); return; }
        return jsend(API, 'PUT', {
          title: title, description: val('tfDesc').trim(), assignee_id: aid,
          priority: val('tfPriority'), start_date: dpValue('tfStart') || null, due_date: dpValue('tfDue') || null,
          shared_with_users: pickValue('tfShared'), reviewer_ids: pickValue('tfReviewers')
        }).then(function (r) { if (r.success) __modalClose(); after(r); });
      });
    });
  };

  g.__subAdd = function () {
    var title = (document.getElementById('newSubTitle').value || '').trim();
    if (!title) { toast(t('节点标题不能为空'), 'error'); return; }
    jsend(API + '/subtasks', 'POST', { title: title, description: (document.getElementById('newSubDesc').value || '').trim(), is_milestone: document.getElementById('newSubMile').checked })
      .then(function (d) { if (d.success && d.data) tab = 'st-' + d.data.id; after(d); });
  };
  g.__subFormOpen = function (sid) {
    ensureUsers().then(function () {
      var s = sid ? subById(sid) : null;
      var conf = s ? (s.milestone_reviewers || []).map(function (r) { return { id: r.reviewer_id, name: r.reviewer_name }; }) : [];
      var isMile = s ? !!s.is_milestone : false;
      var body = field('sfTitle', t('标题'), s ? s.title : '', 'text', 'placeholder="' + t('留空将由 AI 根据描述生成') + '"')
        + area('sfDesc', t('描述'), s ? (s.description || '') : '', 'placeholder="' + t('输入描述后失焦,标题为空时 AI 自动生成') + '" onblur="__aiSubTitle()"')
        + pickField('sfAssignee', t('负责人'), false, (s && s.assignee_id) ? [{ id: s.assignee_id, name: s.assignee_name }] : [{ id: UID, name: uname(UID) }])
        + dateRow('sfStart', t('开始'), s ? s.start_date : dayISO(0), 'sfDue', t('截止'), s ? s.due_date : dayISO(15))
        + '<label style="display:flex;align-items:center;gap:6px;font-size:12.5px;color:var(--ink-3);margin-bottom:12px;"><input id="sfMile" type="checkbox" ' + (isMile ? 'checked' : '') + ' onchange="__sfMileToggle()">' + t('设为里程碑') + '</label>'
        + '<div id="sfMileBox" style="display:' + (isMile ? 'block' : 'none') + ';">'
        + area('sfCriteria', t('达标条件'), s ? (s.milestone_criteria || '') : '')
        + pickField('sfConfirmers', t('里程碑确认人'), true, conf)
        + '</div>';
      openModal(sid ? t('编辑子任务') : t('新增子任务'), body, function () {
        var title = (val('sfTitle') || '').trim(); if (!title) { toast(t('节点标题不能为空'), 'error'); return; }
        var payload = {
          title: title, description: val('sfDesc').trim(),
          assignee_id: pickValue('sfAssignee')[0] || null,
          start_date: dpValue('sfStart') || null, due_date: dpValue('sfDue') || null,
          is_milestone: document.getElementById('sfMile').checked,
          milestone_criteria: val('sfCriteria').trim(),
          milestone_confirmer_ids: document.getElementById('sfMile').checked ? pickValue('sfConfirmers') : []
        };
        var p = sid ? jsend(API + '/subtasks/' + sid, 'PUT', payload) : jsend(API + '/subtasks', 'POST', payload);
        return p.then(function (r) { if (r.success) { __modalClose(); if (r.data && !sid) tab = 'st-' + r.data.id; } after(r); });
      });
    });
  };
  g.__subEdit = function (sid) { __subFormOpen(sid); };
  g.__sfMileToggle = function () { document.getElementById('sfMileBox').style.display = document.getElementById('sfMile').checked ? 'block' : 'none'; };
  g.__subDelete = function (sid) { confirmAsync(t('删除此子任务?'), { title: t('删除子任务'), confirmText: t('删除'), variant: 'danger' }).then(function (ok) { if (ok) { if (tab === 'st-' + sid) tab = 'overview'; jsend(API + '/subtasks/' + sid, 'DELETE').then(after); } }); };
  g.__subStatus = function (sid, act) { jsend(API + '/subtasks/' + sid + '/status', 'POST', { action: act }).then(after); };
  g.__milestone = function (sid, act) {
    if (act === 'reject') {
      confirmAsync(t('确认驳回此里程碑?'), { title: t('驳回里程碑'), confirmText: t('驳回'), variant: 'danger', input: { label: t('驳回理由'), placeholder: t('请填写驳回理由'), required: true, multiline: true } })
        .then(function (c) { if (c === null) return; jsend(API + '/subtasks/' + sid + '/milestone', 'POST', { action: 'reject', comment: c }).then(after); });
    } else { jsend(API + '/subtasks/' + sid + '/milestone', 'POST', { action: 'confirm', comment: '' }).then(after); }
  };
  g.__review = function (action) {
    var sel = document.querySelector('#revRating button.on');
    var rating = sel ? sel.getAttribute('data-r') : 'meet';
    var comment = (document.getElementById('revComment') || {}).value || '';
    if (action === 'reject' && !comment.trim()) { toast(t('驳回时必须填写意见'), 'error'); return; }
    if (action === 'approve' && rating === 'below' && !comment.trim()) { toast(t('低于预期必须填写原因'), 'error'); return; }
    jsend(API + '/review', 'POST', { action: action, rating: rating, comment: comment }).then(after);
  };

  // 评论/进展统一接公用 at-comments 组件(只刷新评论区,不重载整页)
  function bindComments(listId, inputId, sendId, threadUrl, key) {
    if (!window.AtComments) return;
    var listEl = document.getElementById(listId), inputEl = document.getElementById(inputId), sendEl = document.getElementById(sendId);
    if (!listEl || !inputEl || !sendEl) return;
    var c = AtComments.bind({
      listEl: listEl, inputEl: inputEl, sendEl: sendEl, currentUserId: UID,
      currentUserName: uname(UID),
      threadUrl: function () { return threadUrl; },
      deleteUrl: function (cid) { return API + '/comments/' + cid + '/delete'; }
    });
    c.open(key);
  }
  function afterRender() {
    if (tab === 'overview') bindComments('ovCmtList', 'ovCmtInput', 'ovCmtSend', API + '/comments', TID);
    else if (tab.indexOf('st-') === 0) { var sid = tab.slice(3); bindComments('upList', 'upInput', 'upSend', API + '/comments?subtask_id=' + sid + '&reply_type=update', sid); }
  }

  g.__attUpload = function (input, sid) {
    if (!input.files || !input.files.length) return;
    var fd = new FormData(); fd.append('file', input.files[0]); if (sid) fd.append('subtask_id', sid);
    toast(t('上传中…'), 'info');
    fetch(API + '/attachments', { method: 'POST', headers: { 'X-CSRFToken': csrf() }, body: fd }).then(function (r) { return r.json(); }).then(after).catch(function () { toast(t('上传失败'), 'error'); });
  };
  g.__attDelete = function (aid) { confirmAsync(t('删除此附件?'), { title: t('删除附件'), confirmText: t('删除'), variant: 'danger' }).then(function (ok) { if (ok) jsend(API + '/attachments/' + aid, 'DELETE').then(after); }); };
  g.__attPreview = function (aid) {
    var a = (data.attachments || []).filter(function (x) { return x.id === aid; })[0];
    if (!a || !window.ATFilePreview) return;
    ATFilePreview.open(a.filename, [{ name: a.filename, url: API + '/attachments/' + aid + '/preview', size: a.file_size, type: (a.filename.split('.').pop() || '') }]);
  };

  // .at-seg 复核评分单选
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('#revRating button');
    if (b) { b.parentNode.querySelectorAll('button').forEach(function (x) { x.classList.remove('on'); }); b.classList.add('on'); }
  });
  // 审核浮层:点徽章开关 + 外部点击关闭
  g.__toggleReviewPop = function (e) {
    if (e) e.stopPropagation();
    var pop = document.getElementById('reviewPop'); if (!pop) return;
    pop.style.display = pop.style.display === 'block' ? 'none' : 'block';
  };
  document.addEventListener('click', function (e) {
    var pop = document.getElementById('reviewPop');
    if (pop && pop.style.display === 'block' && !pop.contains(e.target) && !(e.target.closest && e.target.closest('button[onclick*="__toggleReviewPop"]'))) {
      pop.style.display = 'none';
    }
  });

  // ── 表单基础设施(模态框 + 字段 + 人员选择) ──
  function val(id) { var e = document.getElementById(id); return e ? e.value : ''; }
  function field(id, label, value, type, attrs) {
    return '<div style="margin-bottom:14px;"><label style="display:block;font-size:12.5px;color:var(--ink-3);margin-bottom:6px;">' + esc(label) + '</label>'
      + '<input id="' + id + '" type="' + (type || 'text') + '" value="' + esc(value || '') + '" ' + (attrs || '') + ' style="width:100%;height:36px;border:1px solid var(--line-2);background:var(--bg-elev);border-radius:8px;padding:0 12px;font-size:13px;color:var(--ink);box-sizing:border-box;"></div>';
  }
  function area(id, label, value, attrs) {
    return '<div style="margin-bottom:14px;"><label style="display:block;font-size:12.5px;color:var(--ink-3);margin-bottom:6px;">' + esc(label) + '</label>'
      + '<textarea id="' + id + '" ' + (attrs || '') + ' style="width:100%;min-height:60px;border:1px solid var(--line-2);background:var(--bg-elev);border-radius:8px;padding:9px 11px;font-size:13px;color:var(--ink);resize:vertical;box-sizing:border-box;">' + esc(value || '') + '</textarea></div>';
  }
  function selField(id, label, opts, value) {
    var o = opts.map(function (p) { return '<option value="' + p[0] + '"' + (p[0] === value ? ' selected' : '') + '>' + esc(p[1]) + '</option>'; }).join('');
    return '<div style="margin-bottom:14px;"><label style="display:block;font-size:12.5px;color:var(--ink-3);margin-bottom:6px;">' + esc(label) + '</label>'
      + '<select id="' + id + '" style="width:100%;height:36px;border:1px solid var(--line-2);background:var(--bg-elev);border-radius:8px;padding:0 10px;font-size:13px;color:var(--ink);">' + o + '</select></div>';
  }
  // AT 日期选择器(复用公用 at_date_picker 组件,无时间);init 后存入 _dps,取值用 dpValue()
  var _dps = {};
  function dpField(id, label) {
    var wk = [t('日'), t('一'), t('二'), t('三'), t('四'), t('五'), t('六')].map(function (w) { return '<span>' + w + '</span>'; }).join('');
    return '<div style="flex:1;"><label style="display:block;font-size:12.5px;color:var(--ink-3);margin-bottom:6px;">' + esc(label) + '</label>'
      + '<div class="at-dp at-dp-inline" id="' + id + '" data-at-date-picker>'
      + '<button type="button" class="at-dp-trigger" data-dp-trigger><span data-dp-label class="at-dp-ph">' + t('选择日期') + '</span></button>'
      + '<input type="hidden" data-dp-value>'
      + '<div class="at-dp-menu" data-dp-menu hidden>'
      + '<div class="at-dp-head"><span data-dp-title></span><span class="at-dp-nav">'
      + '<button type="button" data-dp-prev><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg></button>'
      + '<button type="button" data-dp-next><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg></button></span></div>'
      + '<div class="at-dp-wk">' + wk + '</div><div class="at-dp-grid" data-dp-grid></div>'
      + '<div class="at-dp-foot"><button type="button" data-dp-today>' + t('今天') + '</button></div>'
      + '</div></div></div>';
  }
  function dateRow(sid, slabel, sval, did, dlabel, dval) {
    return '<div style="display:flex;gap:12px;margin-bottom:14px;" data-dp-pair="' + sid + '|' + (sval ? sval.slice(0, 10) : '') + '|' + did + '|' + (dval ? dval.slice(0, 10) : '') + '">'
      + dpField(sid, slabel) + dpField(did, dlabel) + '</div>';
  }
  function initDP(id, val) { if (!g.AtDatePicker) return; var ctl = AtDatePicker.init(id); if (ctl) { if (val) ctl.setValue(val.slice(0, 10)); _dps[id] = ctl; } }
  function initModalDatePickers() {
    document.querySelectorAll('#tmOv [data-dp-pair]').forEach(function (el) {
      var p = (el.dataset.dpPair || '').split('|');   // sid|sval|did|dval
      initDP(p[0], p[1]); initDP(p[2], p[3]);
    });
  }
  function dpValue(id) { return _dps[id] ? _dps[id].getValue() : ''; }
  function dayISO(offset) { var d = new Date(); d.setDate(d.getDate() + (offset || 0)); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); }

  // 类型+标题 组合输入(复用工作项 at_grouped_select;类型=任务类型 通用+角色绩效)
  var _gsCtl = null;
  function groupedTitleField(id, label, ph) {
    var groups = g.TASK_TYPE_GROUPS || [], labels = g.TASK_TYPE_LABELS || {};
    var menu = groups.map(function (grp) {
      return '<div class="at-gsi-grp">' + esc(grp.label) + '</div>' + (grp.options || []).map(function (o) {
        return '<div class="at-gsi-item" data-gsi-val="' + esc(o.value) + '">' + esc(o.label) + '</div>';
      }).join('');
    }).join('');
    return '<div style="margin-bottom:14px;"><label style="display:block;font-size:12.5px;color:var(--ink-3);margin-bottom:6px;">' + esc(label) + '</label>'
      + '<div class="at-gsi" id="' + id + '" data-at-grouped-select data-labels=\'' + JSON.stringify(labels).replace(/'/g, '&#39;') + '\'>'
      + '<button type="button" class="at-gsi-trigger" data-gsi-trigger><span data-gsi-label>' + t('请选择') + '</span>'
      + '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="opacity:.5;"><path d="m6 9 6 6 6-6"/></svg></button>'
      + '<span class="at-gsi-sep">-</span>'
      + '<input type="text" class="at-gsi-input" data-gsi-input placeholder="' + esc(ph || '') + '">'
      + '<div class="at-gsi-menu" data-gsi-menu hidden>' + menu + '</div></div></div>';
  }
  function initModalGrouped() {
    var el = document.querySelector('#tmOv [data-at-grouped-select]');
    _gsCtl = (el && g.AtGroupedSelect) ? AtGroupedSelect.init(el) : null;
  }

  var USERS = null, USERMAP = {};
  function ensureUsers() {
    if (USERS) return Promise.resolve(USERS);
    return jget('/user/api/users/active').then(function (d) {
      USERS = (d.data || []).map(function (u) { return { id: u.id, name: u.real_name || u.username, sub: u.role_display || u.company_name || '' }; });
      USERS.forEach(function (u) { USERMAP[String(u.id)] = u.name; });
      return USERS;
    }).catch(function () { USERS = []; return USERS; });
  }
  function uname(id) { return USERMAP[String(id)] || ('#' + id); }

  // 人员选择:复用公用 AtPeopleSelect(按部门分组+头像+搜索;多/单选)。签名保持不变,call site 无需改。
  var _psInit = {}, _ps = {};
  function pickField(fid, label, multi, sel) {
    var ids = (sel || []).map(function (x) { return (x && typeof x === 'object') ? x.id : x; });
    _psInit[fid] = { single: !multi, ids: ids };
    return '<div style="margin-bottom:14px;"><label style="display:block;font-size:12.5px;color:var(--ink-3);margin-bottom:6px;">' + esc(label) + '</label>'
      + '<div class="at-ps" id="' + fid + '" data-at-people-select data-users-url="/expense/api/users/same-company" style="flex:1;min-width:0;position:relative;">'
      + '<div class="at-ps-box" data-ps-box><span data-ps-chips style="display:contents;"></span>'
      + '<input type="text" class="at-ps-input" data-ps-input autocomplete="off" placeholder="' + t('搜索人员…') + '"></div>'
      + '<div class="at-ps-menu" data-ps-menu hidden></div></div></div>';
  }
  function initModalPeople() {
    _ps = {};
    Object.keys(_psInit).forEach(function (fid) {
      var cfg = _psInit[fid], el = document.getElementById(fid);
      if (el && g.AtPeopleSelect) {
        var ctl = AtPeopleSelect.init(el, { single: cfg.single, excludeSelf: false });
        if (ctl) { if (cfg.ids && cfg.ids.length) ctl.setValue(cfg.ids); _ps[fid] = ctl; }
      }
    });
    _psInit = {};
  }
  function pickValue(fid) { return _ps[fid] ? _ps[fid].getValue() : []; }

  function openModal(title, body, onSave) {
    __modalClose();
    _dps = {}; _gsCtl = null;
    var ov = document.createElement('div'); ov.id = 'tmOv';
    ov.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:200;display:flex;align-items:flex-start;justify-content:center;padding:48px 16px;overflow-y:auto;';
    ov.innerHTML = '<div style="background:var(--bg-page);border:1px solid var(--line);border-radius:14px;width:100%;max-width:520px;box-shadow:0 20px 60px rgba(0,0,0,.25);">'
      + '<div style="display:flex;align-items:center;justify-content:space-between;padding:16px 20px 4px;"><span style="font-size:15px;font-weight:600;color:var(--ink);">' + esc(title) + '</span><button type="button" onclick="__modalClose()" style="border:0;background:transparent;font-size:20px;color:var(--ink-3);cursor:pointer;line-height:1;">×</button></div>'
      + '<div style="padding:20px;">' + body + '</div>'
      + '<div style="display:flex;justify-content:flex-end;gap:8px;padding:14px 20px;border-top:1px solid var(--line);"><button type="button" onclick="__modalClose()" style="height:36px;padding:0 16px;border:1px solid var(--line-2);border-radius:6px;background:var(--bg-elev);color:var(--ink-2);font-size:13px;cursor:pointer;">' + t('取消') + '</button><button type="button" data-modal-save onclick="__modalSave()" style="height:36px;padding:0 16px;border:0;border-radius:6px;background:var(--accent);color:#fff;font-size:13px;font-weight:500;cursor:pointer;">' + t('保存') + '</button></div></div>';
    ov.addEventListener('click', function (e) { if (e.target === ov) __modalClose(); });
    document.body.appendChild(ov);
    initModalDatePickers();
    initModalGrouped();
    initModalPeople();
    var _saving = false;
    g.__modalSave = function () {
      if (_saving) return;                       // 防重入:慢请求时多次点击不再重复提交
      var saveBtn = ov.querySelector('[data-modal-save]');
      var r = onSave();                          // 校验失败的 onSave 返回 undefined → 不加锁,可立即重试
      if (r && typeof r.then === 'function') {
        _saving = true; if (saveBtn) { saveBtn.disabled = true; saveBtn.style.opacity = '.6'; saveBtn.textContent = t('保存中…'); }
        r.then(function () { }, function () { }).then(function () {
          _saving = false; if (saveBtn && document.body.contains(saveBtn)) { saveBtn.disabled = false; saveBtn.style.opacity = ''; saveBtn.textContent = t('保存'); }
        });
      }
    };
  }
  g.__modalClose = function () { var ov = document.getElementById('tmOv'); if (ov) ov.remove(); g.__modalSave = null; };

  // 描述失焦 → 标题为空时用 AI 生成(domain=task);任务与子任务共用
  function aiFillInto(titleEl, descEl) {
    if (!titleEl || !descEl) return;
    var desc = (descEl.value || '').trim();
    if (!desc || (titleEl.value || '').trim()) return;
    var ph = titleEl.placeholder; titleEl.placeholder = t('AI 生成中…');
    fetch('/task/api/generate-title', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() }, body: JSON.stringify({ description: desc }) })
      .then(function (r) { return r.json(); })
      .then(function (d) { titleEl.placeholder = ph; if (d && d.success && d.title && !(titleEl.value || '').trim()) titleEl.value = d.title; })
      .catch(function () { titleEl.placeholder = ph; });
  }
  g.__aiTitle = function () { aiFillInto(document.querySelector('#ctType [data-gsi-input]'), document.getElementById('ctDesc')); };
  g.__aiSubTitle = function () { aiFillInto(document.getElementById('sfTitle'), document.getElementById('sfDesc')); };

  function openCreateForm() {
    var body = groupedTitleField('ctType', t('类型 / 标题'), t('标题(留空将由 AI 据描述生成)'))
      + area('ctDesc', t('描述'), '', 'placeholder="' + t('输入描述后失焦,标题为空时 AI 自动生成') + '" onblur="__aiTitle()"')
      + pickField('ctAssignee', t('负责人'), false, [{ id: UID, name: uname(UID) }])
      + selField('ctPriority', t('优先级'), [['urgent', t('紧急')], ['high', t('高')], ['normal', t('普通')], ['low', t('低')]], 'normal')
      + dateRow('ctStart', t('开始'), dayISO(0), 'ctDue', t('截止'), dayISO(7))
      + pickField('ctShared', t('协助人员'), true, [])
      + pickField('ctReviewers', t('审计人(可选,会审)'), true, []);
    openModal(t('新建任务'), body, function () {
      var title = _gsCtl ? _gsCtl.getContent() : '';
      if (!title) { toast(t('任务标题不能为空'), 'error'); return; }
      var aid = pickValue('ctAssignee')[0]; if (!aid) { toast(t('请选择指派人'), 'error'); return; }
      var ttype = (_gsCtl && _gsCtl.getWorkType()) || 'general';
      var reviewers = pickValue('ctReviewers');
      if (needReview(ttype) && !reviewers.length) { toast(t('该任务类型需指定审核人'), 'error'); return; }
      return jsend('/task/api/create', 'POST', {
        title: title, task_type: ttype,
        description: val('ctDesc').trim(), assignee_id: aid,
        priority: val('ctPriority'), start_date: dpValue('ctStart') || null, due_date: dpValue('ctDue') || null,
        shared_with_users: pickValue('ctShared'), reviewer_ids: reviewers
      }).then(function (r) {
        if (r.success && r.data) { toast(r.message || t('已创建')); location.href = '/task/at/' + r.data.id; }
        else toast(r.message || t('创建失败'), 'error');
      });
    });
    // 选到"需审核"类型 → 自动带入指派人的上级为审核人(可改)
    if (_gsCtl) _gsCtl.onChange(function (code) {
      if (!needReview(code)) return;
      if (_ps['ctReviewers'] && _ps['ctReviewers'].getValue().length) return;
      var aid = pickValue('ctAssignee')[0] || UID;
      jget('/task/api/superior?user_id=' + aid).then(function (d) {
        if (d && d.id && _ps['ctReviewers'] && !_ps['ctReviewers'].getValue().length) {
          _ps['ctReviewers'].setValue([d.id]);
          toast(t('该类型需审核,已带入上级为审核人,可调整'), 'info');
        } else if (d && !d.id) { toast(t('该任务类型需指定审核人'), 'info'); }
      });
    });
    var origClose = g.__modalClose;   // 创建模式:关闭即返回列表
    g.__modalClose = function () { origClose(); location.href = '/task/at'; };
  }
  function needReview(code) { return (g.TASK_REVIEW_CODES || []).indexOf(code) >= 0; }

  // 通知深链:#comments→评论卡 / #review→会审卡(仅首次加载滚动一次)
  var _hashConsumed = false;
  function handleHashOnce() {
    if (_hashConsumed) return; _hashConsumed = true;
    var h = location.hash || '';
    if (h === '#review') { setTimeout(function () { var pop = document.getElementById('reviewPop'); if (pop) pop.style.display = 'block'; }, 80); return; }
    if (h === '#comments') {
      var el = document.getElementById('card-comments');
      if (el) setTimeout(function () { el.scrollIntoView({ behavior: 'smooth', block: 'start' }); }, 60);
    }
  }

  function load() {
    if (TID === 'new') {
      root.innerHTML = '<div style="padding:40px 0;text-align:center;color:var(--ink-3);">' + t('填写任务信息…') + '</div>';
      ensureUsers().then(openCreateForm);
      return;
    }
    jget(API).then(function (d) {
      if (!d.success) { root.innerHTML = '<div style="padding:60px 0;text-align:center;color:var(--ink-3);">' + esc(d.message || t('加载失败')) + '</div>'; return; }
      data = d.data;
      // 通知深链:#st-<id> 直接打开该子任务选卡
      var hash = location.hash || '';
      if (!_hashConsumed && hash.indexOf('#st-') === 0 && subById(hash.slice(4))) tab = 'st-' + hash.slice(4);
      if (tab.indexOf('st-') === 0 && !subById(tab.slice(3))) tab = 'overview';
      ensureUsers().then(function () { render(); handleHashOnce(); });
    }).catch(function () { root.innerHTML = '<div style="padding:60px 0;text-align:center;color:var(--ink-3);">' + t('加载失败') + '</div>'; });
  }
  load();
})(window);
