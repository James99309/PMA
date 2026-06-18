/**
 * AT 工作日历 — 纯手写月历网格 + 工作项增删改完成(Phase 1)
 * 后端复用 /worklog/api/*(worklog_service 单一来源)。
 */
(function (g) {
  'use strict';
  var CFG = {};
  var $ = function (id) { return document.getElementById(id); };
  var csrf = function () { return (document.querySelector('meta[name="csrf-token"]') || {}).content || ''; };
  var t = (typeof g.t === 'function') ? g.t : function (s) { return s; };   // 客户端 i18n(中→英,见 _js_i18n.html)
  var toast = function (m, ty) { if (g.ATToast) ATToast[ty || 'success'](m); };

  var anchor = new Date();          // 当前参考日(月:其所在月 / 周:其所在周 / 日:当天)
  var viewMode = 'month';           // month | week | day
  var eventsByDate = {};            // dateISO -> [event]
  var pendingFiles = [];            // 待上传附件(新建/编辑时排队,保存后上传)
  var curItemId = null, curExisting = [];   // 编辑态:当前工作项 id + 已存附件
  var wiCompletePromptId = null;            // 关闭时待提醒"标记完成"的工作项 id
  var tasksData = [], tasksLoaded = false;  // 关联任务:未完成任务(含子任务)列表
  var holidayCountries = [];                 // 已选显示假期的国家(init 时从 localStorage/默认填充)
  var viewOwnerId = null;                     // 正在查看的他人账户 id(null=本人)
  var accountsData = null;                    // 可查看账户缓存
  var contribMode = false;                    // 当前打开的工作项为"他人/共享"态(只读+可评论+可传附件)
  var attachCanDelete = true;                  // 附件是否可删除(仅本人编辑态)
  var logDatesSub = {}, logDatesDraft = {};    // 有日报的日期集合(已提交/草稿) → 日历日记图标
  var customerPicker, projectPicker, titleCtl, startTimeCtl, endTimeCtl, startDateCtl, endDateCtl, peopleCtl, logDateCtl;
  var WK = ['一', '二', '三', '四', '五', '六', '日'];                                  // 周一→周日(表头);init 按语言切换
  var WKFULL = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];               // getDay() 索引;init 按语言切换
  var WK_EN = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  var WKFULL_EN = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  var MONTHS_EN = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December'];
  function isEn() { return (CFG.lang || 'zh') === 'en'; }

  function iso(d) {
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  }
  function parseISO(s) { var p = (s || '').slice(0, 10).split('-'); return new Date(+p[0], +p[1] - 1, +p[2]); }
  function addDays(d, n) { var x = new Date(d); x.setDate(x.getDate() + n); return x; }
  function addMonths(d, n) { var x = new Date(d); x.setDate(1); x.setMonth(x.getMonth() + n); return x; }
  function weekStartOf(d) { var x = new Date(d); x.setHours(0, 0, 0, 0); x.setDate(x.getDate() - ((x.getDay() + 6) % 7)); return x; }  // 周一

  /* ───────── 事件 chip + 状态 ───────── */
  function endMoment(e) {
    if (e.end) return new Date(e.end.length > 10 ? e.end : e.end + 'T00:00:00');
    var d = parseISO(e.start); d.setDate(d.getDate() + 1); return d;  // 无结束 → 当天结束(次日 0 点)
  }
  function isCompleted(e) { return e.extendedProps && e.extendedProps.status === 'completed'; }
  function isOverdue(e) { return !isCompleted(e) && new Date() > endMoment(e); }
  function isDraggable(e) { return e.editable !== false && !isCompleted(e); }

  function chipHtml(e) {
    var cls = 'cal-ev';
    if (isCompleted(e)) cls += ' completed';
    else if (isOverdue(e)) cls += ' ended';
    var tm = (e.start && e.start.indexOf('T') >= 0) ? e.start.slice(11, 16) : '';
    var mark = isCompleted(e) ? '<span class="cal-ev-check" style="color:' + (e.color || 'var(--accent)') + ';">✓</span>' : '';
    return '<div class="' + cls + '" data-evid="' + e.id + '"' + (isDraggable(e) ? ' draggable="true"' : '') + ' title="' + escAttr(e.title) + '">' +
      (mark || '<span class="cal-ev-dot" style="background:' + (e.color || 'var(--accent)') + ';"></span>') +
      (tm ? '<span class="cal-ev-time">' + tm + '</span>' : '') +
      '<span class="cal-ev-title">' + esc(e.title) + '</span></div>';
  }
  function bindCells() {
    var grid = $('calGrid');
    grid.querySelectorAll('.cal-ev').forEach(function (el) {
      el.addEventListener('click', function (ev) { ev.stopPropagation(); wiOpenEdit(+el.dataset.evid); });
      if (el.getAttribute('draggable') === 'true') {
        el.addEventListener('dragstart', function (ev) { ev.dataTransfer.setData('text/plain', el.dataset.evid); ev.dataTransfer.effectAllowed = 'move'; el.style.opacity = '0.4'; });
        el.addEventListener('dragend', function () { el.style.opacity = ''; });
      }
    });
    grid.querySelectorAll('.cal-logmark[data-logdate]').forEach(function (el) {
      el.style.pointerEvents = 'auto'; el.style.cursor = 'pointer';
      el.addEventListener('click', function (ev) { ev.stopPropagation(); g.openLog(el.dataset.logdate); });
    });
    grid.querySelectorAll('[data-date]').forEach(function (cell) {
      cell.addEventListener('click', function () { wiOpenNew(cell.dataset.date); });
      cell.addEventListener('dragover', function (ev) { ev.preventDefault(); cell.classList.add('cal-drop'); });
      cell.addEventListener('dragleave', function () { cell.classList.remove('cal-drop'); });
      cell.addEventListener('drop', function (ev) {
        ev.preventDefault(); cell.classList.remove('cal-drop');
        var id = ev.dataTransfer.getData('text/plain');
        if (id) moveItem(+id, cell.dataset.date);
      });
    });
  }
  function moveItem(id, dateISO) {
    fetch(CFG.items_url + '/' + id, {
      method: 'PUT', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() },
      body: JSON.stringify({ planned_date: dateISO })
    }).then(function (r) { return r.json(); })
      .then(function (d) { if (d.success) { toast(t('已移动')); loadEvents(); } else toast(d.message || t('移动失败'), 'error'); })
      .catch(function () { toast(t('移动失败'), 'error'); });
  }

  /* ───────── 范围 + 渲染(月/周/日)───────── */
  function monthGridRange() {
    var y = anchor.getFullYear(), m = anchor.getMonth();
    var first = new Date(y, m, 1);
    var start = new Date(y, m, 1 - ((first.getDay() + 6) % 7));   // 周一起
    return { start: start, end: addDays(start, 41) };            // 6 周
  }
  function fetchRange() {
    if (viewMode === 'week') { var s = weekStartOf(anchor); return { start: s, end: addDays(s, 6) }; }
    if (viewMode === 'day') { var d = new Date(anchor); d.setHours(0, 0, 0, 0); return { start: d, end: d }; }
    return monthGridRange();
  }

  // 节假日:取当天名称(按语言+已选国家),右上角内部小标签
  function holidayHtml(di) {
    var list = (CFG.holidays || {})[di];
    if (!list || !list.length) return '';
    var zh = (CFG.lang || 'zh') === 'zh';
    var seen = {}, names = [];
    list.forEach(function (h) {
      if (holidayCountries.indexOf(h.country) < 0) return;
      var n = zh ? h.name_zh : h.name_en;
      if (n && !seen[n]) { seen[n] = 1; names.push(n); }
    });
    if (!names.length) return '';
    var full = names.join(' / ');
    return '<span class="cal-holiday" title="' + escAttr(full) + '">' + esc(full) + '</span>';
  }

  // 假期国家选择:下拉勾选,localStorage 持久化
  var HOL_LS = 'pma_at_holidayCountries';
  function renderHolidayMenu() {
    var menu = $('calHolidayMenu'); if (!menu) return;
    var zh = (CFG.lang || 'zh') === 'zh';
    var sc = CFG.supported_countries || {};
    var html = '';
    Object.keys(sc).forEach(function (code) {
      var on = holidayCountries.indexOf(code) >= 0;
      var label = zh ? sc[code].zh : sc[code].en;
      html += '<label class="cal-hol-item">' +
        '<input type="checkbox" data-c="' + code + '"' + (on ? ' checked' : '') + '>' +
        '<img class="cal-hol-flag" src="https://hatscripts.github.io/circle-flags/flags/' + code.toLowerCase() + '.svg" alt="' + code + '" loading="lazy">' +
        '<span>' + esc(label) + '</span></label>';
    });
    menu.innerHTML = html;
    menu.querySelectorAll('input[data-c]').forEach(function (cb) {
      cb.addEventListener('change', function () {
        var code = cb.dataset.c, i = holidayCountries.indexOf(code);
        if (cb.checked && i < 0) holidayCountries.push(code);
        else if (!cb.checked && i >= 0) holidayCountries.splice(i, 1);
        try { localStorage.setItem(HOL_LS, JSON.stringify(holidayCountries)); } catch (e) {}
        render();
      });
    });
  }

  // 日历右下角日记图标:已提交(实心)/有内容草稿(空心待提交)
  function logMarkHtml(di) {
    var sub = logDatesSub[di], draft = !sub && logDatesDraft[di];
    if (!sub && !draft) return '';
    var fill = sub ? 'currentColor' : 'none';
    return '<span class="cal-logmark' + (draft ? ' draft' : '') + '" data-logdate="' + di + '" title="' +
      (sub ? t('已提交日报') : t('日报草稿(待提交)')) + '">' +
      '<svg width="13" height="13" viewBox="0 0 24 24" fill="' + fill + '" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' +
      '<path d="M4 4h12a2 2 0 0 1 2 2v14l-4-2-4 2-4-2-2 1V6a2 2 0 0 1 2-2z" fill="' + fill + '"/></svg></span>';
  }

  // 账户选择(查看他人日历)
  function loadAccounts(cb) {
    if (accountsData) { cb && cb(); return; }
    fetch(CFG.accounts_url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (r) { return r.json(); })
      .then(function (d) { accountsData = d.accounts || []; cb && cb(); })
      .catch(function () { accountsData = []; cb && cb(); });
  }
  function renderAccountMenu() {
    var menu = $('calAccountMenu'); if (!menu) return;
    menu.innerHTML =
      '<div class="cal-acct-search"><input type="text" id="calAcctSearch" placeholder="' + t('搜索姓名 / 部门') + '">/div>' +
      '<div id="calAcctList"></div>';
    var input = $('calAcctSearch');
    input.addEventListener('click', function (e) { e.stopPropagation(); });
    input.addEventListener('input', function () { renderAcctList(input.value.trim()); });
    renderAcctList('');
    setTimeout(function () { try { input.focus(); } catch (e) {} }, 0);
  }
  function renderAcctList(q) {
    var list = $('calAcctList'); if (!list) return;
    q = (q || '').toLowerCase();
    var html = '';
    var selfName = CFG.current_user_name || t('我的日历');
    if (!q || selfName.toLowerCase().indexOf(q) >= 0 || (t('我的日历') + t('本人')).toLowerCase().indexOf(q) >= 0) {
      html += '<div class="cal-acct-item' + (!viewOwnerId ? ' on' : '') + '" data-id="" data-name="">' +
        esc(selfName) + '<span class="acct-dept">' + t('本人') + '</span></div>';
    }
    var curDept = null, leftHeader = false;
    (accountsData || []).forEach(function (a) {
      var hay = (a.name + ' ' + (a.department || '')).toLowerCase();
      if (q && hay.indexOf(q) < 0) return;
      var inactive = a.active === false;
      if (inactive) {
        // 将离职(停用)账号统一归到底部一个组
        if (!leftHeader) { html += '<div class="cal-acct-group">' + t('离职') + '</div>'; leftHeader = true; curDept = null; }
      } else {
        var dept = a.department || t('其他');
        if (dept !== curDept) { html += '<div class="cal-acct-group">' + esc(dept) + '</div>'; curDept = dept; }
      }
      html += '<div class="cal-acct-item' + (String(viewOwnerId) === String(a.id) ? ' on' : '') +
        (inactive ? ' inactive' : '') +
        '" data-id="' + a.id + '" data-name="' + escAttr(a.name) + '">' + esc(a.name) + '</div>';
    });
    if (!html) html = '<div class="at-dim" style="padding:14px;text-align:center;font-size:12px;">' + t('无匹配') + '</div>';
    list.innerHTML = html;
    list.querySelectorAll('[data-id]').forEach(function (el) {
      el.addEventListener('click', function (e) {
        e.stopPropagation(); selectAccount(el.dataset.id, el.dataset.name); $('calAccountMenu').hidden = true;
      });
    });
  }
  function selectAccount(id, name) {
    viewOwnerId = id ? id : null;
    $('calAccountLabel').textContent = viewOwnerId ? (name || t('他人日历')) : (CFG.current_user_name || t('我的日历'));
    loadEvents();
  }

  function render() {
    var grid = $('calGrid');
    var todayISO = iso(new Date());
    if (viewMode === 'day') {
      var d = new Date(anchor); var di = iso(d);
      $('calTitle').textContent = di + ' ' + WKFULL[d.getDay()];
      grid.style.gridTemplateColumns = '1fr';
      var evs = eventsByDate[di] || [];
      var inner = evs.length ? evs.map(chipHtml).join('')
        : '<div class="at-dim" style="padding:48px;text-align:center;font-size:13px;">' + t('当天暂无安排,点击新建') + '</div>';
      grid.innerHTML = '<div class="cal-cell cal-day' + (di === todayISO ? ' today' : '') + '" data-date="' + di + '">' +
        '<span class="cal-daynum">' + d.getDate() + '</span>' + holidayHtml(di) + logMarkHtml(di) + inner + '</div>';
      bindCells(); return;
    }
    var cells, headLabels, otherCheck;
    if (viewMode === 'week') {
      var s = weekStartOf(anchor);
      $('calTitle').textContent = iso(s) + ' ~ ' + iso(addDays(s, 6));
      cells = []; for (var i = 0; i < 7; i++) cells.push(addDays(s, i));
      otherCheck = function () { return false; };
    } else {
      var r = monthGridRange();
      $('calTitle').textContent = isEn() ? (MONTHS_EN[anchor.getMonth()] + ' ' + anchor.getFullYear())
                                         : (anchor.getFullYear() + ' 年 ' + (anchor.getMonth() + 1) + ' 月');
      // 按需行数(4-6 周):避免整行下个月的多余行
      var lastDay = new Date(anchor.getFullYear(), anchor.getMonth() + 1, 0).getDate();
      var leadBlanks = (new Date(anchor.getFullYear(), anchor.getMonth(), 1).getDay() + 6) % 7;  // 周一为首
      var weeks = Math.ceil((leadBlanks + lastDay) / 7);
      cells = []; var dd = new Date(r.start); for (var j = 0; j < weeks * 7; j++) { cells.push(new Date(dd)); dd = addDays(dd, 1); }
      otherCheck = function (x) { return x.getMonth() !== anchor.getMonth(); };
    }
    grid.style.gridTemplateColumns = 'repeat(7,1fr)';
    var html = '';
    WK.forEach(function (w) { html += '<div class="cal-wkhead">' + w + '</div>'; });
    cells.forEach(function (d) {
      var di = iso(d);
      var cls = 'cal-cell' + (viewMode === 'week' ? ' cal-week' : '');
      if (otherCheck(d)) cls += ' other';
      if (di === todayISO) cls += ' today';
      var dow = d.getDay(); if (dow === 0 || dow === 6) cls += ' weekend';
      var evs = eventsByDate[di] || [];
      var chips = '';
      var cap = (viewMode === 'week') ? evs.length : 5;
      evs.slice(0, cap).forEach(function (e) { chips += chipHtml(e); });
      if (evs.length > cap) chips += '<div class="cal-more">+' + (evs.length - cap) + ' ' + t('更多') + '</div>';
      html += '<div class="' + cls + '" data-date="' + di + '"><span class="cal-daynum">' + d.getDate() + '</span>' + holidayHtml(di) + logMarkHtml(di) + chips + '</div>';
    });
    grid.innerHTML = html;
    bindCells();
  }

  function loadEvents() {
    var r = fetchRange();
    var url = CFG.items_url + '?start=' + iso(r.start) + '&end=' + iso(addDays(r.end, 1));
    if (viewOwnerId) url += '&owner_id=' + viewOwnerId;
    fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        // 日报日期集合(日历右下角日记图标):已提交 + 有内容草稿;看他人时已读/未读都算已提交
        logDatesSub = {}; logDatesDraft = {};
        (data.datesWithSubmittedLogs || []).concat(data.datesWithReadLogs || [], data.datesWithUnreadLogs || [])
          .forEach(function (d) { logDatesSub[d] = 1; });
        (data.datesWithDraftLogs || []).forEach(function (d) { logDatesDraft[d] = 1; });
        eventsByDate = {};
        (data.events || []).forEach(function (e) {
          var s = parseISO(e.start);
          var endD = parseISO((e.extendedProps && e.extendedProps.end_date) || e.start);
          var cur = new Date(s);
          while (cur <= endD) { var k = iso(cur); (eventsByDate[k] = eventsByDate[k] || []).push(e); cur = addDays(cur, 1); }
        });
        render();
      })
      .catch(function () { render(); });
  }

  function navigate(delta) {
    if (viewMode === 'month') anchor = addMonths(anchor, delta);
    else if (viewMode === 'week') anchor = addDays(weekStartOf(anchor), delta * 7);
    else anchor = addDays(anchor, delta);
    loadEvents();
  }
  function setView(mode) {
    viewMode = mode;
    $('calViewSeg').querySelectorAll('button').forEach(function (b) { b.classList.toggle('on', b.dataset.view === mode); });
    loadEvents();
  }
  g.calToday = function () { anchor = new Date(); loadEvents(); };

  /* ───────── 工作项弹窗 ───────── */
  function clearModal() {
    $('wiId').value = '';
    if (titleCtl) titleCtl.setValue('meeting', '');
    if (startDateCtl) startDateCtl.clear();
    if (endDateCtl) endDateCtl.clear();
    if (startTimeCtl) startTimeCtl.clear();
    if (endTimeCtl) endTimeCtl.clear();
    $('wiDesc').value = '';
    $('wiProject').value = ''; $('wiProjectId').value = '';
    $('wiCustomer').value = ''; $('wiCustomerId').value = '';
    var c = $('wiContactId'); c.innerHTML = '<option value="">' + t('先选客户') + '</option>'; c.disabled = true;
    if (peopleCtl) peopleCtl.clear();
    selectTask('', '', '');
    $('wiTaskMenu').hidden = true;
    $('wiAllDay').checked = true; toggleAllDay(true);
    $('wiTrip').checked = false;
    pendingFiles = []; curItemId = null; curExisting = [];
    renderAttach();
    wiCompletePromptId = null;
    $('wiDeleteBtn').style.display = 'none';
    $('wiReadonlyNote').style.display = 'none';
    $('wiSaveBtn').style.display = '';
    $('wiCard').classList.remove('wi-view', 'wi-contrib');
    $('wiDesc').readOnly = false;
    contribMode = false;
    attachCanDelete = true;
    var _addBtn = $('wiAttachAddBtn'); if (_addBtn) _addBtn.style.display = '';
    $('wiOwnerBanner').style.display = 'none';
    $('wiAttachSection').style.display = '';
    $('wiCommentSection').style.display = 'none';
    $('wiCommentInput').value = '';
    $('wiCommentList').innerHTML = '';
  }
  function toggleAllDay(allDay) {
    // 全天:显示 开始日期 – 结束日期,隐藏时间
    // 计时:显示 开始日期 开始时间 – 结束时间,隐藏结束日期
    $('wiStartTimeBox').style.display = allDay ? 'none' : '';
    $('wiEndTimeBox').style.display = allDay ? 'none' : '';
    $('wiEndDateBox').style.display = allDay ? '' : 'none';
  }
  function openModal() { $('wiModal').classList.add('open'); }
  function promptMarkComplete(id) {
    if (!id) return;
    var run = function () { completeItem(id); };
    if (g.ATConfirm) ATConfirm.show({ title: t('标记完成?'), message: t('该工作项已过计划结束时间,是否标记为已完成?'), variant: 'accent', confirmText: t('标记完成'), cancelText: t('暂不'), onConfirm: run });
    else if (confirm(t('该工作项已过计划结束时间,是否标记为已完成?'))) run();
  }
  g.wiClose = function () {
    $('wiModal').classList.remove('open');
    // 超过计划结束时间且未完成:打开后关闭 → 提醒是否标记完成
    if (wiCompletePromptId) {
      var id = wiCompletePromptId; wiCompletePromptId = null;
      promptMarkComplete(id);
    }
  };

  g.wiOpenNew = function (dateISO) {
    if (viewOwnerId) return;   // 查看他人日历时不可新建
    clearModal();
    $('wiModalTitle').textContent = t('新建工作项');
    var d0 = dateISO || iso(new Date());
    if (startDateCtl) startDateCtl.setValue(d0);
    if (endDateCtl) endDateCtl.setValue(d0);
    // 默认:不全天,开始=当前时间(向下取整 15 分钟),结束=+1 小时
    $('wiAllDay').checked = false; toggleAllDay(false);
    var p2 = function (n) { return String(n).padStart(2, '0'); };
    var now = new Date();
    var sMin = now.getHours() * 60 + Math.floor(now.getMinutes() / 15) * 15;
    var eMin = Math.min(sMin + 60, 23 * 60 + 45);
    if (startTimeCtl) startTimeCtl.setValue(p2(Math.floor(sMin / 60)) + ':' + p2(sMin % 60));
    if (endTimeCtl) endTimeCtl.setValue(p2(Math.floor(eMin / 60)) + ':' + p2(eMin % 60));
    openModal();
    setTimeout(function () { if (titleCtl) titleCtl.focus(); }, 50);
  };

  g.wiOpenEdit = function (id) {
    clearModal();
    $('wiModalTitle').textContent = t('编辑工作项');
    fetch(CFG.items_url + '/' + id, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (r) { return r.json(); })
      .then(function (res) {
        if (!res.success) { toast(res.message || t('加载失败'), 'error'); return; }
        var it = res.data;
        $('wiId').value = it.id;
        if (titleCtl) titleCtl.setValue(it.work_type || 'other', it.title || '');
        if (startDateCtl) startDateCtl.setValue(it.planned_date || '');
        if (endDateCtl) endDateCtl.setValue(it.end_date || it.planned_date || '');
        $('wiDesc').value = it.description || '';
        // 描述按内容自动撑高(完成只读态也能看全文,封顶 480px 后可滚动/拖拽)
        (function (el) { setTimeout(function () { el.style.height = 'auto'; el.style.height = Math.min(el.scrollHeight, 480) + 'px'; }, 0); })($('wiDesc'));
        $('wiAllDay').checked = !!it.is_all_day;
        toggleAllDay(!!it.is_all_day);
        if (startTimeCtl) startTimeCtl.setValue(it.start_time ? it.start_time.slice(0, 5) : '');
        if (endTimeCtl) endTimeCtl.setValue(it.end_time ? it.end_time.slice(0, 5) : '');
        $('wiTrip').checked = !!it.is_business_trip;
        if (it.project_id) { $('wiProjectId').value = it.project_id; $('wiProject').value = it.project_name || ''; }
        if (it.customer_id) {
          $('wiCustomerId').value = it.customer_id; $('wiCustomer').value = it.customer_name || '';
          loadContacts(it.customer_id, it.contact_id);
        }
        if (peopleCtl) peopleCtl.setValue(it.shared_with_users || []);
        if (it.related_task_id) {
          var tlab = it.related_subtask_title ? (it.related_task_title + ' › ' + it.related_subtask_title) : (it.related_task_title || '');
          selectTask(it.related_task_id, it.related_subtask_id || '', tlab);
        }
        curItemId = it.id; curExisting = it.attachments || [];
        var mine = String(it.owner_id) === String(CFG.current_user_id);
        // 附件可删/可加:本人未完成态才可删;完成态不可加,他人态可加不可删
        attachCanDelete = mine && it.status !== 'completed';
        $('wiAttachAddBtn').style.display = (it.status === 'completed') ? 'none' : '';
        renderAttach();
        $('wiCommentSection').style.display = '';   // 编辑/查看态:显示评论区
        if (wiComments) wiComments.open(it.id);
        if (it.status === 'completed') {
          // 已完成:查看态,全部只读;保存/删除隐藏,仅取消
          $('wiModalTitle').textContent = t('查看工作项');
          $('wiCard').classList.add('wi-view');
          $('wiDesc').readOnly = true;   // 只读防编辑,但仍可滚动/拖拽查看全文
          $('wiSaveBtn').style.display = 'none';
          $('wiDeleteBtn').style.display = 'none';
          $('wiReadonlyNote').style.display = '';
          // 查看态无附件 → 隐藏附件区
          $('wiAttachSection').style.display = (curExisting && curExisting.length) ? '' : 'none';
        } else if (!mine) {
          // 他人/共享:只读核心,但可评论 + 可上传附件
          contribMode = true;
          $('wiModalTitle').textContent = t('查看工作项');
          $('wiCard').classList.add('wi-view', 'wi-contrib');
          $('wiDesc').readOnly = true;
          $('wiSaveBtn').style.display = 'none';
          $('wiDeleteBtn').style.display = 'none';
          $('wiReadonlyNote').style.display = 'none';
          $('wiOwnerBanner').textContent = t('由 {name} 创建,你可以查看、评论与上传附件').replace('{name}', it.owner_name || t('他人'));
          $('wiOwnerBanner').style.display = '';
          $('wiAttachSection').style.display = '';   // 始终显示(可上传)
        } else {
          $('wiDeleteBtn').style.display = '';
          // 未完成且已过计划结束时间:关闭时提醒标记完成
          var endStr = it.end_time && it.planned_date ? (it.planned_date + 'T' + it.end_time.slice(0, 5)) :
                       ((it.end_date || it.planned_date) + 'T23:59');
          if (new Date() > new Date(endStr)) wiCompletePromptId = it.id;
        }
        openModal();
      })
      .catch(function () { toast(t('加载失败'), 'error'); });
  };

  // 文件名截断:基名超过 4 字 → 前4字 + … + 扩展名
  function shortName(fn) {
    fn = fn || t('附件');
    var dot = fn.lastIndexOf('.');
    var ext = dot > 0 ? fn.slice(dot) : '';
    var base = dot > 0 ? fn.slice(0, dot) : fn;
    return base.length > 4 ? (base.slice(0, 4) + '…' + ext) : fn;
  }
  function attChip(fullName, onRemove, onClick) {
    var chip = document.createElement('span');
    chip.style.cssText = 'display:inline-flex;align-items:center;gap:5px;padding:3px 4px 3px 9px;background:var(--bg-sunk);border-radius:14px;font-size:12px;color:var(--ink);';
    var lbl = document.createElement('span');
    lbl.textContent = shortName(fullName); lbl.title = fullName;
    if (onClick) { lbl.style.cursor = 'pointer'; lbl.addEventListener('click', function (e) { e.stopPropagation(); onClick(); }); }
    chip.appendChild(lbl);
    if (onRemove) {
      var x = document.createElement('button'); x.type = 'button'; x.textContent = '×';
      x.style.cssText = 'border:0;background:transparent;color:var(--ink-4);cursor:pointer;line-height:1;padding:0 3px;';
      x.addEventListener('click', function (e) { e.stopPropagation(); onRemove(); });
      chip.appendChild(x);
    }
    return chip;
  }
  function renderAttach() {
    var box = $('wiAttachList');
    box.innerHTML = '';
    // 预览用文件列表(非删除项,顺序与显示一致)
    var pv = [];
    curExisting.forEach(function (a, idx) {
      if (a._removed) return;
      pv.push({ name: a.filename || a.name || t('附件'),
                url: CFG.items_url + '/' + curItemId + '/preview-attachment/' + idx,
                size: a.size, type: a.type, uploaded_at: a.uploaded_at });
    });
    var pvi = 0;
    // 已存附件(点击预览;删除仅本人编辑态)
    curExisting.forEach(function (a, idx) {
      if (a._removed) return;
      var pos = pvi++;
      var onRemove = attachCanDelete ? function () {
        fetch(CFG.items_url + '/' + curItemId + '/delete-attachment/' + idx, { method: 'POST', headers: { 'X-CSRFToken': csrf() } })
          .then(function (r) { return r.json(); })
          .then(function (d) { if (d.success) { a._removed = true; renderAttach(); } else toast(d.message || t('删除失败'), 'error'); });
      } : null;
      box.appendChild(attChip(a.filename || a.name || t('附件'), onRemove, function () {
        if (window.ATFilePreview) { ATFilePreview.open('', pv); ATFilePreview._selectFile(pos); }
        else window.open(pv[pos].url, '_blank');
      }));
    });
    // 待上传(按引用移除,无预览)
    pendingFiles.forEach(function (f) {
      box.appendChild(attChip(f.name, function () { pendingFiles = pendingFiles.filter(function (x) { return x !== f; }); renderAttach(); }, null));
    });
  }

  function loadContacts(custId, selId) {
    var sel = $('wiContactId');
    if (!custId) { sel.innerHTML = '<option value="">' + t('先选客户') + '</option>'; sel.disabled = true; return; }
    sel.disabled = false;
    sel.innerHTML = '<option value="">' + t('加载中…') + '</option>';
    fetch(CFG.contacts_url.replace('{id}', custId), { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var arr = d.data || d.contacts || [];
        sel.innerHTML = '<option value="">' + t('不指定联系人') + '</option>';
        arr.forEach(function (c) {
          var o = document.createElement('option');
          o.value = c.id; o.textContent = c.name + (c.position ? ' · ' + c.position : '');
          if (selId && String(c.id) === String(selId)) o.selected = true;
          sel.appendChild(o);
        });
      })
      .catch(function () { sel.innerHTML = '<option value="">' + t('加载失败') + '</option>'; });
  }

  /* ───────── 关联任务(2 级)───────── */
  function loadTasks(cb) {
    if (tasksLoaded) { if (cb) cb(); return; }
    fetch(CFG.my_tasks_url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (r) { return r.json(); })
      .then(function (d) { tasksData = (d && d.tasks) || []; tasksLoaded = true; if (cb) cb(); })
      .catch(function () { tasksData = []; tasksLoaded = true; if (cb) cb(); });
  }
  function renderTaskMenu() {
    var menu = $('wiTaskMenu'), curT = $('wiTaskId').value, curS = $('wiSubtaskId').value;
    if (!tasksData.length) { menu.innerHTML = '<div class="at-dim" style="padding:16px;text-align:center;font-size:12px;">' + t('无未完成任务') + '</div>'; return; }
    var html = '';
    if (curT) html += '<div class="wi-task-item at-dim" data-clear="1">' + t('— 不关联 —') + '</div>';
    tasksData.forEach(function (t) {
      var on = (String(t.id) === String(curT) && !curS) ? ' on' : '';
      html += '<div class="wi-task-item' + on + '" data-t="' + t.id + '" data-label="' + escAttr(t.title) + '">' + esc(t.title) + '</div>';
      (t.subtasks || []).forEach(function (s) {
        var son = (String(s.id) === String(curS)) ? ' on' : '';
        html += '<div class="wi-task-item sub' + son + '" data-t="' + t.id + '" data-s="' + s.id + '" data-label="' + escAttr(t.title + ' › ' + s.title) + '">' + esc(s.title) + '</div>';
      });
    });
    menu.innerHTML = html;
    var clr = menu.querySelector('[data-clear]');
    if (clr) clr.addEventListener('click', function (e) { e.stopPropagation(); selectTask('', '', ''); $('wiTaskMenu').hidden = true; });
    menu.querySelectorAll('[data-t]').forEach(function (el) {
      el.addEventListener('click', function (e) { e.stopPropagation(); selectTask(el.dataset.t, el.dataset.s || '', el.dataset.label); $('wiTaskMenu').hidden = true; });
    });
  }
  function selectTask(taskId, subId, label) {
    $('wiTaskId').value = taskId || ''; $('wiSubtaskId').value = subId || '';
    var lab = $('wiTaskLabel'); lab.textContent = label || t('选择任务 / 子任务');
    lab.classList.toggle('at-dim', !taskId);
  }

  /* ───────── 评论 ───────── */
  // 评论:工作项 + 日报共用 AtComments 组件(init 中 bind)
  var wiComments = null, logComments = null;

  g.wiSave = function () {
    wiCompletePromptId = null;
    var content = titleCtl ? titleCtl.getContent() : '';
    var title = titleCtl ? titleCtl.getTitle() : '';
    var date = startDateCtl ? startDateCtl.getValue() : '';
    if (!content) { toast(t('请输入工作内容'), 'error'); return; }
    if (!date) { toast(t('请选择开始日期'), 'error'); return; }
    var allDay = $('wiAllDay').checked;
    var payload = {
      title: title,
      work_type: (titleCtl ? titleCtl.getWorkType() : '') || 'other',
      planned_date: date,
      end_date: allDay ? ((endDateCtl ? endDateCtl.getValue() : '') || null) : null,
      is_all_day: allDay,
      start_time: allDay ? '' : (startTimeCtl ? startTimeCtl.getValue() : ''),
      end_time: allDay ? '' : (endTimeCtl ? endTimeCtl.getValue() : ''),
      is_business_trip: $('wiTrip').checked,
      project_id: $('wiProjectId').value || null,
      customer_id: $('wiCustomerId').value || null,
      contact_id: $('wiContactId').value || null,
      description: $('wiDesc').value.trim(),
      shared_with_users: peopleCtl ? peopleCtl.getValue() : [],
      related_task_id: $('wiTaskId').value || null,
      related_subtask_id: $('wiSubtaskId').value || null
    };
    var id = $('wiId').value;
    var endStr = (!allDay && payload.end_time && date) ? (date + 'T' + payload.end_time)
                 : ((payload.end_date || date) + 'T23:59');
    var overdue = new Date() > new Date(endStr);
    // 已过结束时间:先问是否标记完成,再继续保存(确认=保存+完成 / 仅保存=只保存)
    if (overdue) {
      if (g.ATConfirm) {
        ATConfirm.show({
          title: t('标记完成?'), message: t('该工作项已过计划结束时间,是否标记为已完成?'),
          variant: 'accent', confirmText: t('标记完成并保存'), cancelText: t('仅保存'),
          onConfirm: function () { doSaveItem(payload, id, true); },
          onCancel: function () { doSaveItem(payload, id, false); }
        });
      } else {
        doSaveItem(payload, id, confirm(t('该工作项已过计划结束时间,是否标记为已完成?')));
      }
    } else {
      doSaveItem(payload, id, false);
    }
  };

  function doSaveItem(payload, id, markComplete) {
    var method = id ? 'PUT' : 'POST';
    var url = id ? (CFG.items_url + '/' + id) : CFG.items_url;
    var filesQueue = pendingFiles.slice(); pendingFiles = [];
    wiCompletePromptId = null;
    toast(filesQueue.length ? t('已保存,附件上传中…') : t('已保存'));
    g.wiClose();   // 乐观:立即关闭,保存/上传后台进行
    fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() },
      body: JSON.stringify(payload)
    })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (!d.success && !d.id && !(d.data && d.data.id)) { toast(d.message || t('保存失败'), 'error'); return; }
        var newId = id || (d.data && d.data.id) || d.id;
        if (filesQueue.length) { pendingFiles = filesQueue; uploadPending(newId, function () { toast(t('附件已上传')); loadEvents(); }); }
        if (markComplete) completeItem(newId); else loadEvents();   // completeItem 内含 loadEvents
      })
      .catch(function () { toast(t('保存失败,请重试'), 'error'); });
  }

  // 重新拉取工作项附件并刷新(他人/共享态即时上传后用)
  function reloadAttachments(itemId) {
    fetch(CFG.items_url + '/' + itemId, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (r) { return r.json(); })
      .then(function (res) { if (res.success) { curExisting = res.data.attachments || []; renderAttach(); } })
      .catch(function () {});
  }

  function uploadPending(itemId, done) {
    if (!pendingFiles.length || !itemId) { done(); return; }
    var queue = pendingFiles.slice();
    pendingFiles = [];
    var i = 0;
    function next() {
      if (i >= queue.length) { done(); return; }
      var fd = new FormData(); fd.append('file', queue[i]);
      fetch(CFG.items_url + '/' + itemId + '/upload-attachment', { method: 'POST', headers: { 'X-CSRFToken': csrf() }, body: fd })
        .then(function () { i++; next(); })
        .catch(function () { i++; next(); });
    }
    next();
  }

  function completeItem(id) {
    if (!id) return;
    fetch(CFG.items_url + '/' + id + '/complete', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() }, body: '{}' })
      .then(function (r) { return r.json(); })
      .then(function (d) { if (d.success) { toast(t('已标记完成')); loadEvents(); } else toast(d.message || t('操作失败'), 'error'); });
  }

  g.wiDelete = function () {
    var id = $('wiId').value; if (!id) return;
    var run = function () {
      fetch(CFG.items_url + '/' + id, { method: 'DELETE', headers: { 'X-CSRFToken': csrf() } })
        .then(function (r) { return r.json(); })
        .then(function (d) { if (d.success) { toast(t('已删除')); g.wiClose(); loadEvents(); } else toast(d.message || t('删除失败'), 'error'); });
    };
    if (g.ATConfirm) ATConfirm.show({ title: t('删除工作项'), message: t('确定删除这个工作项吗?'), variant: 'danger', confirmText: t('删除'), cancelText: t('取消'), onConfirm: run });
    else if (confirm(t('确定删除?'))) run();
  };

  /* ───────── 初始化 ───────── */
  /* ───────── 日报 ───────── */
  var curLogDate = null, logReadonly = false;
  function logStat(num, lbl) {
    return '<div class="log-stat"><div class="log-stat-num">' + num + '</div><div class="log-stat-lbl">' + esc(lbl) + '</div></div>';
  }
  function renderLogModal(d, dateISO) {
    var log = d.log || {};
    var submitted = log.status === 'submitted';
    logReadonly = submitted || !!d.is_readonly;
    // 状态徽标
    var pill = $('logStatusPill');
    if (submitted) {
      pill.style.display = ''; pill.textContent = t('已提交');
      pill.style.background = 'var(--accent-tint)'; pill.style.color = 'var(--accent)';
    } else if ((log.additional_notes || '').trim()) {
      pill.style.display = ''; pill.textContent = t('草稿');
      pill.style.background = 'var(--bg-sunk)'; pill.style.color = 'var(--ink-3)';
    } else { pill.style.display = 'none'; }
    // 统计
    var st = d.statistics || {};
    $('logStats').innerHTML = logStat(st.total_items || 0, t('工作项')) +
      logStat(st.completed_items || 0, t('已完成')) +
      logStat((st.total_hours || 0) + 'h', t('工时')) +
      logStat(st.project_count || 0, t('关联项目'));
    // 正文
    $('logNotes').value = log.additional_notes || '';
    // 当天工作项(只读上下文)
    var rows = '';
    (d.completed_items || []).concat(d.pending_items || []).forEach(function (it) {
      var done = it.status === 'completed';
      var tm = it.start_time ? it.start_time.slice(0, 5) : '';
      rows += '<div class="log-item-row">' +
        (done ? '<span class="cal-ev-check" style="font-size:11px;color:' + (it.color || 'var(--accent)') + ';">✓</span>'
              : '<span class="log-item-dot" style="background:' + (it.color || 'var(--accent)') + ';"></span>') +
        (tm ? '<span class="log-item-time">' + tm + '</span>' : '') +
        '<span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + esc(it.title || '') + '</span></div>';
    });
    $('logItems').innerHTML = rows;
    // 只读控制
    var card = $('logCard');
    if (logReadonly) {
      card.classList.add('log-view');
      $('logAiBtn').style.display = 'none';
      $('logSaveBtn').style.display = 'none';
      $('logSubmitBtn').style.display = 'none';
      $('logReadonlyNote').style.display = d.is_readonly ? 'none' : '';
    } else {
      card.classList.remove('log-view');
      $('logAiBtn').style.display = ''; $('logAiBtn').disabled = false;
      $('logSaveBtn').style.display = ''; $('logSubmitBtn').style.display = '';
      $('logReadonlyNote').style.display = 'none';
    }
  }
  g.openLog = function (dateISO, ownerId) {
    curLogDate = dateISO;
    $('logDate').value = dateISO;
    if (logDateCtl) logDateCtl.setValue(dateISO);   // setValue 不触发 onChange,无循环
    $('logNotes').value = ''; $('logItems').innerHTML = ''; $('logStats').innerHTML = '';
    var url = CFG.daily_url.replace('{date}', dateISO);
    var oid = ownerId || viewOwnerId;
    if (oid) url += '?owner_id=' + oid;
    fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (r) { return r.json(); })
      .then(function (res) {
        if (!res.success) { toast(res.message || t('加载失败'), 'error'); return; }
        renderLogModal(res.data, dateISO);
        if (logComments) logComments.open(dateISO);
        $('logModal').classList.add('open');
      })
      .catch(function () { toast(t('加载失败'), 'error'); });
  };
  g.logClose = function () { $('logModal').classList.remove('open'); };
  function logBody() { return { additional_notes: $('logNotes').value.trim() }; }
  g.logSave = function () {
    var btn = $('logSaveBtn'); btn.disabled = true;
    fetch(CFG.daily_url.replace('{date}', curLogDate), {
      method: 'PUT', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() },
      body: JSON.stringify(logBody())
    }).then(function (r) { return r.json(); })
      .then(function (d) { btn.disabled = false; if (d.success) { toast(t('已保存')); g.logClose(); loadEvents(); } else toast(d.message || t('保存失败'), 'error'); })
      .catch(function () { btn.disabled = false; toast(t('保存失败'), 'error'); });
  };
  g.logSubmit = function () {
    if (!$('logNotes').value.trim()) { toast(t('请填写工作描述'), 'error'); return; }
    var btn = $('logSubmitBtn'); btn.disabled = true;
    // 先存草稿再提交(确保最新正文)
    fetch(CFG.daily_url.replace('{date}', curLogDate), {
      method: 'PUT', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() }, body: JSON.stringify(logBody())
    }).then(function () {
      return fetch(CFG.daily_submit_url.replace('{date}', curLogDate), {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() }, body: '{}'
      });
    }).then(function (r) { return r.json(); })
      .then(function (d) { btn.disabled = false; if (d.success) { toast(t('提交成功')); g.logClose(); loadEvents(); } else toast(d.message || t('提交失败'), 'error'); })
      .catch(function () { btn.disabled = false; toast(t('提交失败'), 'error'); });
  };
  g.logAiDraft = function () {
    var btn = $('logAiBtn'); btn.disabled = true;
    var span = btn.querySelector('span'); var old = span ? span.textContent : '';
    if (span) span.textContent = t('生成中…');
    fetch(CFG.daily_ai_url.replace('{date}', curLogDate), { method: 'POST', headers: { 'X-CSRFToken': csrf() } })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        btn.disabled = false; if (span) span.textContent = old;
        if (d.success) {
          var cur = $('logNotes').value.trim();
          $('logNotes').value = cur ? (cur + '\n\n' + d.draft) : d.draft;
        } else toast(d.message || t('AI 生成失败'), 'error');
      })
      .catch(function () { btn.disabled = false; if (span) span.textContent = old; toast(t('AI 生成失败'), 'error'); });
  };

  function init() {
    var cfgEl = $('calConfig');
    try { CFG = JSON.parse(cfgEl.textContent); } catch (e) { console.error('calConfig parse failed', e); return; }
    anchor = new Date();
    if (isEn()) { WK = WK_EN; WKFULL = WKFULL_EN; }

    // 假期国家:从 localStorage 恢复,否则用区域默认
    try { holidayCountries = JSON.parse(localStorage.getItem(HOL_LS)); } catch (e) {}
    if (!Array.isArray(holidayCountries)) holidayCountries = (CFG.default_countries || []).slice();

    $('calPrev').addEventListener('click', function () { navigate(-1); });
    $('calNext').addEventListener('click', function () { navigate(1); });
    $('calViewSeg').addEventListener('click', function (e) {
      var b = e.target.closest('button[data-view]'); if (!b) return;
      setView(b.dataset.view);
    });

    // 假期国家选择下拉
    var holBtn = $('calHolidayBtn');
    if (holBtn) {
      holBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        var m = $('calHolidayMenu');
        if (m.hidden) { renderHolidayMenu(); m.hidden = false; } else m.hidden = true;
      });
      document.addEventListener('click', function (e) {
        var m = $('calHolidayMenu');
        if (m && !m.hidden && !m.contains(e.target) && e.target !== holBtn && !holBtn.contains(e.target)) m.hidden = true;
      });
    }

    // 账户选择(查看他人日历;仅有权限者)
    if (CFG.can_view_others) {
      $('calAccountWrap').style.display = '';
      var acctBtn = $('calAccountBtn');
      acctBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        var m = $('calAccountMenu');
        if (m.hidden) loadAccounts(function () { renderAccountMenu(); m.hidden = false; }); else m.hidden = true;
      });
      document.addEventListener('click', function (e) {
        var m = $('calAccountMenu');
        if (m && !m.hidden && !m.contains(e.target) && !acctBtn.contains(e.target)) m.hidden = true;
      });
    }

    // 组合标题输入框(类型选择 + 内容)
    if (g.AtGroupedSelect) titleCtl = AtGroupedSelect.init('wiTitleInput');
    // 时间选择器(小时 + 30 分钟间隔)
    if (g.AtTimePicker) { startTimeCtl = AtTimePicker.init('wiStartTime'); endTimeCtl = AtTimePicker.init('wiEndTime'); }
    // 日期选择器(弹出月历)
    if (g.AtDatePicker) {
      startDateCtl = AtDatePicker.init('wiStartDate'); endDateCtl = AtDatePicker.init('wiEndDate');
      logDateCtl = AtDatePicker.init('logDatePicker');
      if (logDateCtl) logDateCtl.onChange(function (d) { if (d) g.openLog(d); });
    }
    // 关联人员多选
    if (g.AtPeopleSelect) peopleCtl = AtPeopleSelect.init('wiParticipants');
    // 全天勾选 → 控制时间输入显隐
    $('wiAllDay').addEventListener('change', function () {
      toggleAllDay(this.checked);
    });

    // 评论组件:工作项 + 日报共用 AtComments(回车发送/删除/气泡渲染都在组件内)
    if (g.AtComments) {
      wiComments = AtComments.bind({
        listEl: $('wiCommentList'), inputEl: $('wiCommentInput'), sendEl: $('wiCommentSend'),
        currentUserId: CFG.current_user_id,
        threadUrl: function (id) { return CFG.comments_url.replace('{id}', id); },
        deleteUrl: function (cid) { return CFG.comment_del_url.replace('{id}', cid); }
      });
      logComments = AtComments.bind({
        listEl: $('logCommentList'), inputEl: $('logCommentInput'), sendEl: $('logCommentSend'),
        currentUserId: CFG.current_user_id,
        threadUrl: function (date) {
          var u = CFG.daily_comments_url.replace('{date}', date);
          return viewOwnerId ? (u + '?owner_id=' + viewOwnerId) : u;
        },
        deleteUrl: function (cid) { return CFG.daily_comment_del_url.replace('{id}', cid); }
      });
    }

    // 关联任务:点击展开 2 级列表(可选,不选即不关联)
    $('wiTaskBtn').addEventListener('click', function (e) {
      e.stopPropagation();
      var m = $('wiTaskMenu');
      if (m.hidden) {
        // 打开任务菜单前,先关掉类型下拉(at_grouped_select)避免叠加
        document.querySelectorAll('[data-gsi-menu]').forEach(function (g0) { g0.hidden = true; });
        loadTasks(function () { renderTaskMenu(); m.hidden = false; });
      } else m.hidden = true;
    });
    // 捕获阶段关闭:grouped-select 的 trigger 用了 stopPropagation,冒泡阶段收不到 → 用捕获
    document.addEventListener('click', function (e) {
      var box = $('wiTaskBox'); if (box && !box.contains(e.target)) $('wiTaskMenu').hidden = true;
    }, true);

    // 附件选择 → 入队
    $('wiAttachInput').addEventListener('change', function () {
      var files = Array.prototype.slice.call(this.files || []);
      this.value = '';
      if (contribMode && curItemId) {
        // 他人/共享态无保存按钮 → 立即上传并刷新附件
        pendingFiles = files;
        uploadPending(curItemId, function () { reloadAttachments(curItemId); toast(t('附件已上传')); });
      } else {
        pendingFiles = pendingFiles.concat(files);
        renderAttach();
      }
    });

    // 项目/客户搜索 picker(复用 ATSearchPicker)
    if (g.ATSearchPicker) {
      projectPicker = ATSearchPicker({
        inputId: 'wiProject', hiddenIdId: 'wiProjectId', clearId: 'wiProjectClear', dropdownId: 'wiProjectDropdown',
        label: t('项目'),
        searchUrl: function (t) { return CFG.search_project_url + '?q=' + encodeURIComponent(t); },
        itemsFromResp: function (r) { return (r && r.projects) || []; },
        itemName: function (it) { return it.name; },
        renderItem: function (it, term) {
          return { primary: ATSearchPickerHighlight(it.name || '', term), secondary: [it.owner, it.stage].filter(Boolean).join(' · ') };
        }
      });
      customerPicker = ATSearchPicker({
        inputId: 'wiCustomer', hiddenIdId: 'wiCustomerId', clearId: 'wiCustomerClear', dropdownId: 'wiCustomerDropdown',
        label: t('客户'),
        searchUrl: function (t) { return CFG.search_customer_url + '?q=' + encodeURIComponent(t); },
        itemsFromResp: function (r) { return (r && r.customers) || []; },
        itemName: function (it) { return it.name || it.company_name; },
        renderItem: function (it, term) {
          return { primary: ATSearchPickerHighlight(it.name || it.company_name || '', term), secondary: it.company_code || '' };
        },
        onPick: function (item) { loadContacts(item.id, null); },
        onClear: function () { loadContacts(null); }
      });
    }

    // 通知点击跳转:?owner_id=&date=&open_item=(查看他人 / 定位日期 / 打开工作项)
    var params = new URLSearchParams(location.search);
    var pOwner = params.get('owner_id'), pDate = params.get('date'), pOpen = params.get('open_item');
    var pToday = params.get('open_today');   // 顶栏「写日志」:进入即打开当天日报
    var pLog = params.get('open_log');       // 通知:打开某人某天日报
    if (pToday) {
      history.replaceState({}, '', location.pathname);
      loadEvents();
      setTimeout(function () { g.openLog(iso(new Date())); }, 300);
      return;
    }
    if (pOwner || pDate || pOpen) {
      history.replaceState({}, '', location.pathname);
      if (pDate) { var pd = parseISO(pDate); if (!isNaN(pd)) anchor = pd; }
      var afterLoad = function () {
        if (pOpen) setTimeout(function () { g.wiOpenEdit(+pOpen); }, 350);
        else if (pLog && pDate) setTimeout(function () { g.openLog(pDate, pOwner || null); }, 350);
      };
      if (pOwner && CFG.can_view_others && String(pOwner) !== String(CFG.current_user_id)) {
        loadAccounts(function () {
          viewOwnerId = pOwner;
          var found = (accountsData || []).filter(function (a) { return String(a.id) === String(pOwner); })[0];
          $('calAccountLabel').textContent = found ? found.name : t('他人日历');
          loadEvents(); afterLoad();
        });
      } else {
        loadEvents(); afterLoad();
      }
    } else {
      loadEvents();
    }
  }

  function esc(s) { return String(s == null ? '' : s).replace(/[&<>]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]; }); }
  function escAttr(s) { return esc(s).replace(/"/g, '&quot;'); }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})(window);
