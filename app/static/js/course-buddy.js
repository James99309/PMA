/* ─────────────────────────────────────────────────────────────
 * 小源 · 学习伙伴(全 AT 页挂载)
 * 移植自原型 docs/plans/assets/2026-10-07-course-buddy-prototype.html
 *
 * 对外接口(课程播放器调用;模板里先放了排队桩,脚本加载后回放):
 *   CourseBuddy.setCourse({key, title, totalPages})  进入课程上下文(启用阅读计时)
 *   CourseBuddy.onPage(pageNo)                         翻页(也算活动)
 *   CourseBuddy.activity()                             指针/键盘活动
 *   CourseBuddy.reflow()                               布局变化后重算位置
 *
 * 依赖模板注入:window.CB_I18N(全部界面文案)、window.CB_CONFIG(接口地址)、window.CB_CSRF。
 * 判分全在服务端;前端不持有答案,结果态用服务端返回的 correct_answer(显示位)着色。
 * ───────────────────────────────────────────────────────────── */
(function () {
  'use strict';
  if (window.__cbLoaded) return;
  window.__cbLoaded = true;
  if (!document.body) return;

  var T = window.CB_I18N || {};
  var C = window.CB_CONFIG || {};
  if (C.enabled === false) return;
  var API = C.apiBase || '/api/learning';

  function t(k, vars) {
    var s = T[k];
    if (s == null) s = k;
    if (vars) Object.keys(vars).forEach(function (n) { s = s.split('{' + n + '}').join(String(vars[n])); });
    return s;
  }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function lsGet(k) { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } }
  function lsSet(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* 忽略 */ } }
  function today() { var d = new Date(); return d.getFullYear() + '-' + (d.getMonth() + 1) + '-' + d.getDate(); }

  // 对话记录 / 每日提醒按用户隔离(同一浏览器换账号互不可见);位置 cb-pos 按设备共用
  var UID = C.uid != null ? String(C.uid) : '';
  var IDLE_MS = 120000, PING_MS = 15000, POS_KEY = 'cb-pos', CHAT_MAX = 50;
  var CHAT_KEY = 'cb-chat:' + UID, NAG_KEY = 'cb-nag-date:' + UID;
  (function purgeOtherUsersChat() {
    try {
      var drop = [];
      for (var i = 0; i < localStorage.length; i++) {
        var k = localStorage.key(i);
        if (k === 'cb-chat' || k === 'cb-nag-date' || (k && k.indexOf('cb-chat:') === 0 && k !== CHAT_KEY)) drop.push(k);
      }
      drop.forEach(function (k) { localStorage.removeItem(k); });
    } catch (e) { /* 忽略 */ }
  })();
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ===================== 接口 ===================== */
  var expired = false;
  function ApiError(info) { this.status = info.status; this.error = info.error; this.message = info.message; this.expired = !!info.expired; }

  function markExpired() {
    if (expired) return;
    expired = true;
    stopTimer();
    if (open) render();
  }

  function expiredError(status) { return new ApiError({ status: status || 0, error: 'expired', message: t('expired'), expired: true }); }

  // 取新 CSRF token;拿到 HTML(被重定向到登录页)或 401 视为会话过期,绝不把 JSON 解析异常抛给界面
  function refreshCsrf() {
    return fetch(C.csrfUrl || (API + '/csrf'), {
      credentials: 'same-origin', headers: { 'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest' }
    }).then(function (r) {
      var ct = r.headers.get('content-type') || '';
      if (r.status === 401 || r.redirected || ct.indexOf('application/json') < 0) { markExpired(); throw expiredError(r.status); }
      return r.json().then(function (j) {
        if (!j || !j.token) throw new ApiError({ status: r.status, error: 'csrf', message: t('err_generic') });
        window.CB_CSRF = j.token;
      }, function () { throw new ApiError({ status: r.status, error: 'csrf', message: t('err_generic') }); });
    }, function () {
      throw new ApiError({ status: 0, error: 'network', message: t('err_network') });
    });
  }

  function api(method, url, body, opts) {
    opts = opts || {};
    var headers = { 'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest' };
    var init = { method: method, credentials: 'same-origin', headers: headers };
    if (method !== 'GET') {
      headers['Content-Type'] = 'application/json';
      headers['X-CSRFToken'] = window.CB_CSRF || '';
      init.body = JSON.stringify(body || {});
      if (opts.keepalive) init.keepalive = true;
    }
    function retry() {
      return refreshCsrf().then(function () { return api(method, url, body, { retried: true, keepalive: opts.keepalive }); });
    }
    return fetch(url, init).then(function (res) {
      var ct = res.headers.get('content-type') || '';
      if (res.status === 401) { markExpired(); throw expiredError(401); }
      if (ct.indexOf('application/json') < 0) {
        // 会话过期时全局登录检查 302 到登录页,fetch 跟随后拿到 HTML 200
        if (res.redirected || res.ok) { markExpired(); throw expiredError(res.status); }
        // 非 /api/learning 路径(如 /api/wiki/query)CSRF 失败是 Flask-WTF 默认的 HTML 400:换 token 重试一次
        if (res.status === 400 && method !== 'GET' && !opts.retried) return retry();
        throw new ApiError({ status: res.status, error: 'http', message: t('err_generic') });
      }
      return res.json().then(function (j) {
        if (res.status === 400 && j && j.error === 'csrf' && !opts.retried) return retry();
        if (!res.ok || !j || j.success === false) {
          throw new ApiError({ status: res.status, error: j && j.error, message: (j && j.message) || t('err_generic') });
        }
        return j.data;
      }, function (e) {
        if (e instanceof ApiError) throw e;
        throw new ApiError({ status: res.status, error: 'http', message: t('err_generic') });
      });
    }, function () {
      throw new ApiError({ status: 0, error: 'network', message: t('err_network') });
    });
  }
  function courseUrl(key, tail) { return API + '/' + encodeURIComponent(key) + tail; }

  /* ===================== 小源形象(移植自官网 mascot.js) ===================== */
  var INK = '#13212A';
  function grad(id, a, b, c) { return '<radialGradient id="' + id + '" cx="38%" cy="30%" r="80%"><stop offset="0" stop-color="' + a + '"/><stop offset=".5" stop-color="' + b + '"/><stop offset="1" stop-color="' + c + '"/></radialGradient>'; }
  var DEFS = '<defs><filter id="cb-felt" x="-10%" y="-10%" width="120%" height="120%"><feTurbulence type="fractalNoise" baseFrequency="1.6" numOctaves="2" seed="7" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="2.4" xChannelSelector="R" yChannelSelector="G" result="fuzzy"/><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="3" seed="3" result="grain"/><feColorMatrix in="grain" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 .2 0" result="grainA"/><feComposite in="grainA" in2="fuzzy" operator="in" result="grainIn"/><feBlend in="grainIn" in2="fuzzy" mode="multiply"/></filter>' +
    '<filter id="cb-soft" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="3"/></filter>' +
    grad('cb-g-teal', '#9AD3E6', '#4DA5C7', '#2A6F8F') +
    '<radialGradient id="cb-g-ball" cx="35%" cy="30%" r="70%"><stop offset="0" stop-color="#FFE7A8"/><stop offset="1" stop-color="#E39B1E"/></radialGradient></defs>';
  function bead(id, x, y, r) { return '<g id="' + id + '"><circle cx="' + x + '" cy="' + y + '" r="' + r + '" fill="' + INK + '"/><circle cx="' + (x - r * .32) + '" cy="' + (y - r * .4) + '" r="' + (r * .32) + '" fill="#fff"/></g>'; }
  var YUAN =
    '<g id="cb-antenna"><path d="M100 66 Q101 48 100 32" stroke="#2A6F8F" stroke-width="4.5" stroke-linecap="round" fill="none"/>' +
    '<circle cx="100" cy="27" r="8.5" fill="url(#cb-g-ball)"/><circle cx="97" cy="24" r="2.4" fill="#fff" opacity=".8"/>' +
    '<g class="cb-signal" fill="none" stroke-width="3" stroke-linecap="round"><path d="M86 18 Q80 27 86 36"/><path d="M114 18 Q120 27 114 36"/></g></g>' +
    '<path filter="url(#cb-felt)" fill="url(#cb-g-teal)" d="M100 52 C136 52 160 78 160 114 C160 150 134 174 100 174 C66 174 40 150 40 114 C40 78 64 52 100 52 Z"/>' +
    '<path d="M46 104 C46 66 72 50 100 50 C128 50 154 66 154 104" stroke="#1E2C34" stroke-width="7" fill="none" stroke-linecap="round"/>' +
    '<rect x="32" y="92" width="18" height="34" rx="9" fill="#1E2C34"/><rect x="150" y="92" width="18" height="34" rx="9" fill="#1E2C34"/>' +
    '<rect x="35.5" y="98" width="6" height="22" rx="3" fill="#4DA5C7"/><rect x="158.5" y="98" width="6" height="22" rx="3" fill="#4DA5C7"/>' +
    '<path d="M44 124 Q52 146 74 146" stroke="#1E2C34" stroke-width="4" fill="none" stroke-linecap="round"/><circle cx="76" cy="146" r="5" fill="#1E2C34"/>' +
    '<ellipse cx="68" cy="130" rx="8.5" ry="5" fill="#F48FA8" opacity=".4"/><ellipse cx="132" cy="130" rx="8.5" ry="5" fill="#F48FA8" opacity=".4"/>' +
    '<g id="cb-eyes"><g class="cb-eye-bead">' + bead('cb-pupil-l', 82, 110, 8) + bead('cb-pupil-r', 118, 110, 8) + '</g></g>' +
    '<g class="cb-sleep-eyes" stroke="' + INK + '" stroke-width="3.6" stroke-linecap="round" fill="none"><path d="M74 110 Q82 116 90 110"/><path d="M110 110 Q118 116 126 110"/></g>' +
    '<path id="cb-mouth" d="M93 131 Q100 138 107 131" stroke="' + INK + '" stroke-width="3.4" stroke-linecap="round" fill="none"/>' +
    '<ellipse id="cb-mouth-open" class="cb-mouth-open" cx="100" cy="133" rx="6" ry="4.5" fill="' + INK + '"/>' +
    '<g class="cb-trophy"><path d="M128 40 h22 v8 a11 11 0 0 1 -22 0z" fill="#F2B544"/><rect x="136" y="58" width="6" height="7" fill="#E39B1E"/><rect x="131" y="64" width="16" height="4" rx="2" fill="#E39B1E"/></g>' +
    '<text class="cb-zz" x="134" y="60" font-size="18" font-weight="700" fill="#2A6F8F">z</text>';

  var DOTS = '<svg viewBox="0 0 24 24" fill="currentColor"><circle cx="5" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/></svg>';
  var CLOSE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>';

  /* ===================== DOM ===================== */
  var wrap = document.createElement('div');
  wrap.className = 'cb-wrap cb-side-right';
  wrap.id = 'cbWrap';
  wrap.innerHTML = '<div class="cb-bubble cb-off" aria-live="polite"></div><span class="cb-badge" hidden></span>' +
    '<button class="cb-pet" type="button" aria-haspopup="dialog" aria-label="' + esc(t('open_label')) + '" aria-expanded="false" aria-controls="cbPanel"><span class="cb-breathe"><svg viewBox="0 0 200 200" aria-hidden="true"></svg></span></button>';
  document.body.appendChild(wrap);
  var pet = wrap.querySelector('.cb-pet'), svg = wrap.querySelector('svg'),
    bubble = wrap.querySelector('.cb-bubble'), badge = wrap.querySelector('.cb-badge');
  svg.innerHTML = DEFS + '<ellipse id="cb-shadow" cx="100" cy="183" rx="50" ry="7" fill="#0A141C" opacity=".14" filter="url(#cb-soft)"/>' +
    '<g id="cb-hop"><g id="cb-lean"><g id="cb-squash">' + YUAN + '</g></g></g>';
  var R = {};
  ['lean', 'squash', 'hop', 'antenna', 'eyes', 'shadow', 'mouth', 'mouth-open'].forEach(function (k) { R[k] = svg.querySelector('#cb-' + k); });
  R.pupils = [svg.querySelector('#cb-pupil-l'), svg.querySelector('#cb-pupil-r')];
  R.eyes.style.transformOrigin = '100px 110px';
  R.antenna.style.transformOrigin = '100px 64px';

  var scrim = document.createElement('div');
  scrim.className = 'cb-scrim';
  scrim.id = 'cbScrim';
  document.body.appendChild(scrim);

  var panel = document.createElement('div');
  panel.className = 'cb-panel cb-off';
  panel.id = 'cbPanel';
  panel.setAttribute('role', 'dialog');
  panel.setAttribute('aria-modal', 'true');
  panel.setAttribute('aria-label', t('panel_label'));
  panel.innerHTML = '<div class="cb-grab"></div>' +
    '<div class="cb-head"><div class="cb-t"><h3 id="cbTitle"></h3><div class="cb-sub" id="cbSub"></div></div>' +
    '<div class="cb-more-wrap"><button class="cb-more" type="button" aria-haspopup="true" aria-expanded="false" aria-controls="cbMenu" aria-label="' + esc(t('more')) + '">' + DOTS + '</button>' +
    '<div class="cb-menu" id="cbMenu" hidden></div></div>' +
    '<button class="cb-x" type="button" aria-label="' + esc(t('close')) + '">' + CLOSE + '</button></div>' +
    '<div class="cb-tabs"><div class="cb-seg" role="tablist"><button type="button" role="tab" data-tab="ask">' + esc(t('ask')) + '</button>' +
    '<button type="button" role="tab" data-tab="exam"></button></div>' +
    '<div class="cb-readhint" id="cbReadHint" hidden></div></div>' +
    '<div class="cb-body" id="cbBody"></div>' +
    '<div class="cb-foot" id="cbFoot" hidden></div>' +
    '<div class="cb-compose" id="cbCompose" hidden><input id="cbInput" maxlength="500" autocomplete="off" placeholder="' + esc(t('placeholder')) + '">' +
    '<button type="button" id="cbSend">' + esc(t('send')) + '</button></div>';
  document.body.appendChild(panel);
  var foot = panel.querySelector('#cbFoot');
  var body = panel.querySelector('#cbBody'), compose = panel.querySelector('#cbCompose'),
    input = panel.querySelector('#cbInput'), sendBtn = panel.querySelector('#cbSend'),
    examBtn = panel.querySelector('[data-tab=exam]');

  /* ===================== 状态 ===================== */
  var tab = 'ask', open = false;
  var course = null;          // 课程上下文 {key,title,totalPages};仅 setCourse 后存在
  var prog = null;            // 本课进度 {read:{percent,unlocked,unavailable}, exam:{score,passed,perfect}}
  var examCourse = null;      // 课程外:选中的课程 {key,title,play_url}
  var buddyList = null;       // 课程外:/api/learning/buddy 的 courses
  var buddyLoading = false;
  var destroyed = false;
  var keepExam = false;       // 本次打开面板内刚考满分:先留在考核页看结果,关面板后考核标签才消失

  /* ===================== 动作 ===================== */
  function anim(el, f, ms) { if (reduce || !el || !el.animate) return; el.animate(f, { duration: ms, easing: 'cubic-bezier(.3,.7,.4,1)' }); }
  var ant = 0, antVel = 0;
  function jelly() { kick(); anim(R.squash, [{ transform: 'scale(1,1)' }, { transform: 'scale(1.2,.78)' }, { transform: 'scale(.9,1.12)' }, { transform: 'scale(1.05,.96)' }, { transform: 'scale(1,1)' }], 560); antVel += 9; }
  function hop(h) {
    kick();
    anim(R.hop, [{ transform: 'translateY(0)' }, { transform: 'translateY(' + -(h || 12) + 'px)' }, { transform: 'translateY(0)' }], 420);
    anim(R.shadow, [{ transform: 'scale(1)', opacity: .14 }, { transform: 'scale(.78)', opacity: .08 }, { transform: 'scale(1)', opacity: .14 }], 420);
    antVel -= 6;
  }
  function blink() { if (wrap.classList.contains('cb-sleeping')) return; anim(R.eyes, [{ transform: 'scaleY(1)' }, { transform: 'scaleY(.08)' }, { transform: 'scaleY(1)' }], 170); }
  // 眨眼只在最近有活动的 ~10s 内进行;之后完全静止(呼吸为合成层动画,不占主线程)
  (function loop() {
    setTimeout(function () {
      if (destroyed) return;
      if (!document.hidden && !idleStill()) { blink(); if (Math.random() < .22) setTimeout(blink, 230); }
      loop();
    }, 2200 + Math.random() * 3800);
  })();
  var talkT;
  function talk(ms) {
    kick(); wrap.classList.add('cb-talking'); clearInterval(talkT); var end = Date.now() + ms;
    talkT = setInterval(function () {
      var mo = R['mouth-open'], mc = R.mouth;
      if (Date.now() > end) { clearInterval(talkT); mo.style.opacity = '0'; mc.style.opacity = '1'; wrap.classList.remove('cb-talking'); return; }
      var o = Math.random() < .6; mo.style.opacity = o ? '1' : '0'; mc.style.opacity = o ? '0' : '1';
    }, 120);
  }
  var bT;
  /* ===================== 庆祝烟花(及格/满分;一次性 DOM,放完即删) ===================== */
  var FW_COLORS = ['#F2B544', '#E0715A', '#4DA5C7', '#7BC47F', '#C78BE0', '#F28CB1'];
  function fireworks(big) {
    if (reduce || destroyed) return;
    var x, y;
    var mobileSheet = open && window.innerWidth <= 640;
    if (mobileSheet) { var pr = panel.getBoundingClientRect(); x = pr.left + pr.width / 2; y = pr.top + 40; }
    else { var r = pet.getBoundingClientRect(); x = r.left + r.width / 2; y = r.top + r.height * .35; }
    var layer = document.createElement('div');
    layer.className = 'cb-fx';
    layer.setAttribute('aria-hidden', 'true');
    document.body.appendChild(layer);
    var bursts = big ? 5 : 3, n = big ? 26 : 20;
    for (var b = 0; b < bursts; b++) {
      // 首轮在小源处,后几轮向屏幕中上方散开(右下角贴边时也看得见)
      var bx = b ? x - 80 - Math.random() * 260 : x, by = b ? y - 120 - Math.random() * 220 : y;
      for (var i = 0; i < n; i++) {
        var a = (Math.PI * 2 * i) / n + Math.random() * .3, dist = (big ? 120 : 95) + Math.random() * 70;
        var sp = document.createElement('span');
        sp.className = 'cb-spark';
        sp.style.left = bx + 'px'; sp.style.top = by + 'px';
        sp.style.setProperty('--dx', (Math.cos(a) * dist).toFixed(1) + 'px');
        sp.style.setProperty('--dy', (Math.sin(a) * dist).toFixed(1) + 'px');
        sp.style.background = sp.style.color = FW_COLORS[(i + b) % FW_COLORS.length];
        sp.style.animationDelay = (b * 230) + 'ms';
        layer.appendChild(sp);
      }
    }
    setTimeout(function () { if (layer.parentNode) layer.parentNode.removeChild(layer); }, 1500 + bursts * 230);
  }

  function say(text, ms) {
    if (open || destroyed) return;
    bubble.textContent = text; bubble.classList.remove('cb-off'); clearTimeout(bT);
    talk(Math.min(1600, (ms || 2800) * .5));
    bT = setTimeout(function () { bubble.classList.add('cb-off'); }, ms || 2800);
  }

  /* 眼神/身体倾斜/天线弹簧:rAF 只在需要时跑,收敛后停帧(空闲页零开销),
     指针移动/跳动/果冻/说话/开关面板时 kick() 重启;无操作时游移最多 ~10s 后归位 */
  var mouse = { x: innerWidth * .4, y: innerHeight * .4, t: Date.now() }, look = { x: 0, y: 0 }, lean = 0;
  var rafId = 0, lastKick = Date.now(), petRect = null, WANDER_MS = 10000, EPS = 0.02;
  var DEBUG = !!window.CB_DEBUG;                    // 仅调试/e2e 打开:暴露帧计数,空闲时不应增长
  if (DEBUG) window.__cbFrames = window.__cbFrames || 0;
  function idleStill() { return Date.now() - Math.max(mouse.t, lastKick) >= WANDER_MS; }
  function updatePetRect() { petRect = pet.getBoundingClientRect(); }
  // 休息态:彻底静止时连呼吸(无限 CSS 动画)也暂停 —— 合成器未接管时它会在主线程逐帧重排
  var restTimer = 0;
  function setResting(on) { wrap.classList.toggle('cb-resting', on); }
  function scheduleRest() {
    clearTimeout(restTimer);
    var wait = WANDER_MS - (Date.now() - Math.max(mouse.t, lastKick));
    restTimer = setTimeout(function () { if (!rafId && idleStill()) setResting(true); else if (!rafId) scheduleRest(); },
      Math.max(0, wait) + 50);
  }
  function kick() {
    lastKick = Date.now();
    clearTimeout(restTimer);
    setResting(false);
    if (!rafId && !destroyed && !document.hidden) rafId = requestAnimationFrame(frame);
  }
  function frame(now) {
    rafId = 0;
    if (destroyed || document.hidden) return;
    if (DEBUG) window.__cbFrames++;
    if (!petRect) updatePetRect();
    var r = petRect, cx = r.left + r.width / 2, cy = r.top + r.height * .55, tx, ty, wander = false;
    var t0 = Date.now(), mouseIdle = t0 - mouse.t > 4500;
    if (open) { tx = pos.side === 'left' ? 2.6 : -2.6; ty = -3; }
    else if (mouseIdle) {
      wander = !reduce && !idleStill();
      if (wander) { var k = now / 1400; tx = Math.sin(k) * 3.4; ty = Math.sin(k * .7) * 1.6; }
      else { tx = 0; ty = 0; }
    }
    else { var dx = mouse.x - cx, dy = mouse.y - cy, d = Math.hypot(dx, dy) || 1, m = Math.min(1, d / 260) * 3.6; tx = dx / d * m; ty = dy / d * m; }
    look.x += (tx - look.x) * .18; look.y += (ty - look.y) * .18;
    var target = reduce || open ? 0 : Math.max(-1, Math.min(1, (mouse.x - cx) / 420)) * 6, prev = lean;
    lean += (target - lean) * .1;
    antVel += (-(lean - prev) * 6) + (-ant * .09); antVel *= .86; ant += antVel * .5;
    var settled = !wander && Math.abs(tx - look.x) < EPS && Math.abs(ty - look.y) < EPS &&
      Math.abs(target - lean) < EPS && Math.abs(antVel) < 0.01 && Math.abs(ant) < EPS;
    if (settled) { look.x = tx; look.y = ty; lean = target; ant = 0; antVel = 0; }
    var tr = 'translate(' + look.x.toFixed(2) + 'px,' + look.y.toFixed(2) + 'px)';
    R.pupils.forEach(function (p) { p.style.transform = tr; });
    R.lean.style.transform = 'rotate(' + lean.toFixed(2) + 'deg)';
    R.antenna.style.transform = 'rotate(' + (reduce ? 0 : ant).toFixed(2) + 'deg)';
    if (!settled) rafId = requestAnimationFrame(frame);
    else scheduleRest();
  }
  addEventListener('pointermove', function (e) {
    mouse.x = e.clientX; mouse.y = e.clientY; mouse.t = Date.now();
    if (!rafId) kick();
  }, { passive: true });
  document.addEventListener('visibilitychange', function () {
    wrap.classList.toggle('cb-paused', document.hidden);
    if (!document.hidden) kick();
  });
  wrap.addEventListener('transitionend', function (e) { if (e.target === wrap) updatePetRect(); });

  /* ===================== 位置:拖动 / 吸附左右 / 藏边 / 记忆 ===================== */
  var pos = lsGet(POS_KEY);
  if (!pos || typeof pos !== 'object') pos = { side: 'right', bottom: 84, tucked: false };
  if (typeof pos.bottom !== 'number' || !isFinite(pos.bottom)) pos.bottom = 84;

  function sidebarEl() { return document.querySelector('aside.at-sidebar') || document.querySelector('.at-sidebar'); }
  function leftInset() {
    // 左吸附时贴在 AT 侧栏右缘(侧栏 64 / 232px,悬停浮层不改 aside 宽度)
    var s = sidebarEl();
    if (!s || getComputedStyle(s).display === 'none') return 12;
    var r = s.getBoundingClientRect();
    if (!r.width) return 12;
    return Math.max(0, r.right) + 12;
  }
  // 课程播放器的讲解栏(#cpNotes,含上一步/下一步)在顶栏下方而非页面底部,课件 iframe 一直铺到底、
  // 右下角没有播放器自己的控件,所以不需要额外避让,统一离底 12px
  function minBottom() { return 12; }
  function applyPos() {
    if (destroyed) return;
    var h = wrap.offsetHeight || 96;
    pos.bottom = Math.max(minBottom(), Math.min(pos.bottom, innerHeight - h - 60));
    wrap.classList.toggle('cb-side-left', pos.side === 'left');
    wrap.classList.toggle('cb-side-right', pos.side !== 'left');
    wrap.classList.toggle('cb-tucked', !!pos.tucked);
    if (pos.side === 'left') { wrap.style.left = (pos.tucked ? leftInset() - 12 : leftInset()) + 'px'; wrap.style.right = ''; }
    else { wrap.style.right = '12px'; wrap.style.left = ''; }
    wrap.style.top = ''; wrap.style.bottom = pos.bottom + 'px';
    updatePetRect();
    placePanel();
  }
  function placePanel() {
    if (innerWidth <= 640) { panel.style.left = panel.style.right = panel.style.top = panel.style.bottom = ''; return; }
    var h = wrap.offsetHeight || 96, ph = panel.offsetHeight || 560;
    if (pos.side === 'left') { panel.style.left = leftInset() + 'px'; panel.style.right = ''; }
    else { panel.style.right = '12px'; panel.style.left = ''; }
    panel.style.top = '';
    panel.style.bottom = Math.max(12, Math.min(pos.bottom + h + 8, innerHeight - ph - 12)) + 'px';
  }
  function savePos() { lsSet(POS_KEY, pos); }

  var drag = null, suppress = false;
  pet.addEventListener('pointerdown', function (e) {
    if (e.button !== 0) return;
    var r = wrap.getBoundingClientRect();
    drag = { id: e.pointerId, x: e.clientX, y: e.clientY, dx: e.clientX - r.left, dy: e.clientY - r.top, moved: false };
  });
  addEventListener('pointermove', function (e) {
    if (!drag || e.pointerId !== drag.id) return;
    if (!drag.moved && Math.hypot(e.clientX - drag.x, e.clientY - drag.y) < 6) return;
    if (!drag.moved) {
      drag.moved = true; wrap.classList.add('cb-dragging'); wrap.classList.remove('cb-tucked');
      // 拖动期间临时禁止选中文字(不在 pointerdown 上 preventDefault,以免页面其他下拉收不到 mousedown 关闭)
      drag.us = document.documentElement.style.userSelect;
      document.documentElement.style.userSelect = 'none';
      document.documentElement.style.webkitUserSelect = 'none';
      try { var sel = window.getSelection(); if (sel) sel.removeAllRanges(); } catch (er) { /* 忽略 */ }
      try { pet.setPointerCapture(drag.id); } catch (er) { /* 忽略 */ }
      bubble.classList.add('cb-off'); if (open) toggle(false);
    }
    wrap.style.right = ''; wrap.style.bottom = '';
    wrap.style.left = (e.clientX - drag.dx) + 'px'; wrap.style.top = (e.clientY - drag.dy) + 'px';
    updatePetRect();
  });
  function endDrag(e) {
    if (!drag || (e && e.pointerId !== drag.id)) return;
    var moved = drag.moved, us = drag.us; drag = null; if (!moved) return;
    document.documentElement.style.userSelect = us || '';
    document.documentElement.style.webkitUserSelect = us || '';
    suppress = true; setTimeout(function () { suppress = false; }, 50);
    var r = wrap.getBoundingClientRect(), w = r.width;
    pos.side = r.left + w / 2 < innerWidth / 2 ? 'left' : 'right';
    var edgeL = pos.side === 'left' ? leftInset() - 12 : 0;
    pos.tucked = r.left < edgeL - w * .35 || r.right > innerWidth + w * .35;
    pos.bottom = innerHeight - r.bottom;
    wrap.classList.remove('cb-dragging'); applyPos(); jelly(); savePos();
  }
  addEventListener('pointerup', endDrag);
  addEventListener('pointercancel', endDrag);
  addEventListener('resize', applyPos);

  // 侧栏折叠/展开、讲解栏收起时跟随
  (function observeLayout() {
    var s = sidebarEl();
    if (s) {
      s.addEventListener('transitionend', function (e) { if (e.target === s) applyPos(); });
      if (window.ResizeObserver) new ResizeObserver(function () { applyPos(); }).observe(s);
    }
  })();

  pet.addEventListener('click', function () {
    if (suppress) return;
    if (pos.tucked) { pos.tucked = false; applyPos(); savePos(); hop(14); return; }
    wake(); jelly(); toggle(!open);
  });
  pet.addEventListener('pointerenter', function () { if (open || drag || pos.tucked) return; hop(10); });

  /* ===================== 面板 ===================== */
  function focusSafe(el) { try { if (el) el.focus({ preventScroll: true }); } catch (e) { /* 忽略 */ } }
  function toggle(o) {
    var was = open;
    open = o;
    panel.classList.toggle('cb-off', !o);
    scrim.classList.toggle('cb-on', o);
    bubble.classList.add('cb-off');
    pet.setAttribute('aria-expanded', o ? 'true' : 'false');
    kick();
    if (o) {
      // 每次打开重新取断点题/课程列表(断点在服务端,幂等)
      ex = null; exNote = ''; buddyList = null; keepExam = false;
      render();
      requestAnimationFrame(placePanel);
      setTimeout(function () {
        // 桌面提问页直接聚焦输入框;其余(含窄屏,避免弹键盘)聚焦面板内第一个可聚焦元素
        if (tab === 'ask' && innerWidth > 640) focusSafe(input);
        else focusSafe(panel.querySelector('button:not([disabled]):not([hidden]), [href], input:not([disabled])'));
      }, 60);
    } else if (was) {
      if (!menuBusy) { menuState = null; menuErr = ''; renderMenu(); }
      focusSafe(pet);
    }
  }
  panel.querySelector('.cb-x').onclick = function () { toggle(false); };
  scrim.onclick = function () { toggle(false); };

  /* ---------- 头部「⋯」菜单:隐藏小源(面板内确认,不用 window.confirm) ---------- */
  var moreBtn = panel.querySelector('.cb-more'), menu = panel.querySelector('#cbMenu');
  var menuState = null, menuErr = '', menuBusy = false;   // null=收起 / 'menu' / 'confirm'
  function renderMenu() {
    menu.hidden = !menuState;
    moreBtn.setAttribute('aria-expanded', menuState ? 'true' : 'false');
    if (!menuState) { menu.innerHTML = ''; return; }
    if (menuState === 'menu') {
      menu.setAttribute('role', 'menu');
      menu.innerHTML = '<button type="button" role="menuitem" class="cb-mi" data-act="ask-hide">' + esc(t('hide')) + '</button>';
    } else {
      menu.setAttribute('role', 'group');
      menu.innerHTML = '<div class="cb-mconfirm"><p>' + esc(t('hide_confirm')) + '</p>' +
        (menuErr ? '<div class="cb-note">' + esc(menuErr) + '</div>' : '') +
        '<div class="cb-mbtns"><button type="button" class="cb-mcancel" data-act="cancel">' + esc(t('cancel')) + '</button>' +
        '<button type="button" class="cb-mdanger" data-act="hide"' + (menuBusy ? ' disabled' : '') + '>' + esc(t('hide_ok')) + '</button></div></div>';
    }
  }
  function closeMenu(refocus) {
    if (!menuState) return;
    menuState = null; menuErr = ''; renderMenu();
    if (refocus) focusSafe(moreBtn);
  }
  function hideBuddy() {
    if (menuBusy) return;
    menuBusy = true; menuErr = ''; renderMenu();
    api('POST', API + '/buddy/toggle', { enabled: false }).then(function () {
      if (course) flush(true);       // 已累计的阅读秒数先报掉(keepalive,不再回写界面)
      try { window.dispatchEvent(new CustomEvent('cb:toggled', { detail: { enabled: false } })); } catch (e) { /* 忽略 */ }
      destroy();
    }, function (err) {
      menuBusy = false; menuErr = (err && err.message) || t('err_generic'); renderMenu();
    });
  }
  moreBtn.onclick = function (e) {
    e.stopPropagation();
    if (menuState) { closeMenu(false); return; }
    menuState = 'menu'; renderMenu();
    focusSafe(menu.querySelector('button'));
  };
  menu.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('[data-act]');
    if (!b || b.disabled) return;
    var act = b.getAttribute('data-act');
    if (act === 'ask-hide') { menuState = 'confirm'; renderMenu(); focusSafe(menu.querySelector('[data-act=cancel]')); }
    else if (act === 'cancel') closeMenu(true);
    else if (act === 'hide') hideBuddy();
  });
  document.addEventListener('pointerdown', function (e) {
    if (menuState && !menuBusy && !moreBtn.parentNode.contains(e.target)) closeMenu(false);
  }, true);

  addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && menuState && !menuBusy) closeMenu(true);
    else if (e.key === 'Escape' && open) toggle(false);
    if (course) markActivity();
  });
  // 课程内活动来源(iframe 内的事件由 Task 13 的播放器转发给 CourseBuddy.activity)
  ['pointermove', 'pointerdown', 'wheel', 'touchstart'].forEach(function (ev) {
    addEventListener(ev, function () { if (course) markActivity(); }, { passive: true });
  });
  addEventListener('scroll', function () { if (course) markActivity(); }, { passive: true, capture: true });
  // 窄屏下拉拖动条关闭
  (function () {
    var g = panel.querySelector('.cb-grab'), y0 = null;
    g.addEventListener('pointerdown', function (e) { y0 = e.clientY; try { g.setPointerCapture(e.pointerId); } catch (er) { /* 忽略 */ } });
    g.addEventListener('pointerup', function (e) { if (y0 !== null && e.clientY - y0 > 60) toggle(false); y0 = null; });
  })();
  panel.querySelectorAll('.cb-seg button').forEach(function (b) {
    b.onclick = function () {
      if (b.disabled) return;
      var to = b.dataset.tab;
      if (to === 'exam' && tab !== 'exam') { ex = null; exNote = ''; if (!course) { examCourse = null; buddyList = null; } }
      tab = to; render();
    };
  });

  function readPercent() { return prog && prog.read ? (prog.read.percent || 0) : 0; }
  // 未解锁时差在哪:还有几页没看 / 还差多少时长(两者都可能缺)
  function readGap() {
    var r = prog && prog.read;
    if (!r || r.unlocked || r.unavailable) return null;
    var total = r.pages_total || 0, seen = r.pages_seen || 0;
    var left = Math.max(0, (r.required_seconds || 0) - (r.effective_seconds || 0));
    return { seen: seen, total: total, pagesLeft: Math.max(0, total - seen), secLeft: left };
  }
  function timeLeftText(sec) {
    return sec >= 60 ? t('hint_min', { m: Math.ceil(sec / 60) }) : t('hint_sec', { s: Math.max(1, Math.ceil(sec)) });
  }
  function readHint() {
    var g = readGap();
    if (!g) return '';
    var parts = [t('hint_seen', { s: g.seen, n: g.total })];
    if (g.pagesLeft > 0) parts.push(t('hint_pages', { n: g.pagesLeft }));
    if (g.secLeft > 0) parts.push(timeLeftText(g.secLeft));
    return parts.join(' · ');
  }
  function unlocked() { return !!(prog && prog.read && prog.read.unlocked); }
  function unavailable() { return !!(prog && prog.read && prog.read.unavailable); }
  function score() { return prog && prog.exam ? (prog.exam.score || 0) : 0; }
  function perfect() { return !!(prog && prog.exam && prog.exam.perfect); }
  // 题库准备中(active 满分 < 100):考核标签锁住并提示;只有进度接口带 available,read-ping 不带时沿用旧值
  function notReady() { return !!(prog && prog.exam && prog.exam.available === false); }

  function ring(p) {
    var c = 2 * Math.PI * 6;
    return '<svg class="cb-ring" viewBox="0 0 16 16"><circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" stroke-opacity=".2" stroke-width="2.4"/>' +
      '<circle cx="8" cy="8" r="6" fill="none" stroke="var(--cb-accent)" stroke-width="2.4" stroke-linecap="round" stroke-dasharray="' + (c * p / 100) + ' ' + c + '" transform="rotate(-90 8 8)"/></svg>';
  }

  function renderHead() {
    var hidden = !!course && (!prog || unavailable() || (perfect() && !keepExam));
    var waiting = !!course && !hidden && notReady();
    var disabled = !!course && !hidden && (waiting || !unlocked());
    examBtn.hidden = hidden;
    examBtn.disabled = disabled;
    if (waiting) examBtn.title = t('bank_not_ready'); else examBtn.removeAttribute('title');
    var hintEl = panel.querySelector('#cbReadHint'), hint = course && !hidden ? readHint() : '';
    hintEl.textContent = hint;
    hintEl.hidden = !hint;
    // 未读完仍显示阅读进度(阅读照常计时);读完了题库还没好才显示「准备中」
    examBtn.innerHTML = (waiting && unlocked()) ? esc(t('exam')) + ' · ' + esc(t('not_ready_short'))
      : disabled ? ring(readPercent()) + esc(t('read')) + ' ' + readPercent() + '%'
      : esc(t('exam')) + (course ? ' ' + score() + '/100' : '');
    if (tab === 'exam' && (hidden || disabled)) tab = 'ask';
    panel.querySelectorAll('.cb-seg button').forEach(function (b) {
      var on = b.dataset.tab === tab;
      b.classList.toggle('cb-on', on);
      b.setAttribute('aria-selected', on ? 'true' : 'false');
    });
    panel.querySelector('#cbTitle').textContent = tab === 'ask' ? t('title_ask') : t('title_exam');
    var sub;
    if (course) sub = course.title || '';
    else if (tab === 'ask') sub = t('scope_all');
    else sub = examCourse ? examCourse.title : t('pick_course');
    panel.querySelector('#cbSub').textContent = sub;
  }

  // 主按钮(提交答案 / 下一题 / 完成)放在不随内容滚动的底栏,长题目时也始终可见
  function setFoot(html) { foot.innerHTML = html || ''; foot.hidden = !html; }

  function render() {
    if (destroyed) return;
    renderHead();
    compose.hidden = tab !== 'ask';
    if (tab === 'ask') setFoot('');
    input.placeholder = course ? t('placeholder') : t('placeholder_all');
    if (tab === 'ask') renderAsk(); else renderExam();
    placePanel();
  }

  function expiredNote() {
    if (!expired) return '';
    var url = C.loginUrl || '/auth/login';
    return '<div class="cb-note">' + esc(t('expired')) + ' <a href="' + esc(url) + '">' + esc(t('relogin')) + '</a></div>';
  }

  /* ===================== 提问 ===================== */
  var chat = lsGet(CHAT_KEY);
  if (!Array.isArray(chat)) chat = [];
  var scope = 'course', asking = false;
  function saveChat() { if (chat.length > CHAT_MAX) chat = chat.slice(-CHAT_MAX); lsSet(CHAT_KEY, chat); }

  // marked + DOMPurify 首次提问时懒加载;失败则降级为转义纯文本
  var libs = null;
  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      if (!src) { reject(); return; }
      var s = document.createElement('script');
      s.src = src; s.async = true;
      s.onload = function () { resolve(); };
      s.onerror = function () { reject(); };
      document.head.appendChild(s);
    });
  }
  function ensureLibs() {
    if (libs) return libs;
    var needMarked = typeof window.marked === 'undefined', needPurify = typeof window.DOMPurify === 'undefined';
    libs = Promise.all([needMarked ? loadScript(C.markedSrc) : null, needPurify ? loadScript(C.purifySrc) : null])
      .then(function () { return true; }, function () { return false; });
    return libs;
  }
  function libsReady() { return typeof window.marked !== 'undefined' && typeof window.DOMPurify !== 'undefined'; }
  function plain(s) { return esc(s).replace(/\n/g, '<br>'); }
  function md(text) {
    if (!libsReady()) return plain(text);
    try {
      var mk = window.marked;
      var raw = typeof mk.parse === 'function' ? mk.parse(String(text || ''), { breaks: true, gfm: true }) : mk(String(text || ''));
      var html = window.DOMPurify.sanitize(raw, {
        USE_PROFILES: { html: true },
        FORBID_TAGS: ['style', 'iframe', 'object', 'embed', 'form', 'input', 'button'],
        FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover', 'style']
      });
      var box = document.createElement('div');
      box.innerHTML = html;
      box.querySelectorAll('a').forEach(function (a) {
        var href = (a.getAttribute('href') || '').trim();
        // 知识库内部引用(topic/slug.md)在小源面板里不可跳转,只留文字
        if (/\.md(?:[#?].*)?$/i.test(href) || !href) {
          var sp = document.createElement('span'); sp.textContent = a.textContent; a.replaceWith(sp); return;
        }
        a.setAttribute('target', '_blank'); a.setAttribute('rel', 'noopener noreferrer');
      });
      box.querySelectorAll('img').forEach(function (img) {
        if (/^_assets\//.test(img.getAttribute('src') || '')) img.remove();
      });
      return box.innerHTML;
    } catch (e) { return plain(text); }
  }
  function safeUrl(u) {
    return (typeof u === 'string' && u.charAt(0) === '/' && u.charAt(1) !== '/' && u.indexOf('\\') < 0) ? u : '';
  }

  function renderAsk() {
    var intro = course ? t('ask_intro_course') : t('ask_intro_all');
    var h = expiredNote();
    if (course) {
      h += '<div class="cb-scope"><button type="button" class="cb-chip' + (scope === 'course' ? ' cb-on' : '') + '" data-s="course">' + esc(t('scope_course')) + '</button>' +
        '<button type="button" class="cb-chip' + (scope === 'all' ? ' cb-on' : '') + '" data-s="all">' + esc(t('scope_all')) + '</button></div>';
    }
    h += '<div class="cb-chat"><div class="cb-msg cb-bot">' + esc(intro) + '</div>';
    chat.forEach(function (m) {
      if (m.me) { h += '<div class="cb-msg cb-me">' + esc(m.t) + '</div>'; return; }
      h += '<div class="cb-msg cb-bot' + (m.err ? ' cb-err' : '') + '">' + (m.err ? plain(m.t) : md(m.t));
      var pages = Array.isArray(m.pages) ? m.pages : [];
      if (pages.length) {
        h += '<div class="cb-thumbs">' + pages.map(function (p) {
          var href = safeUrl(p.play_url), src = safeUrl(p.thumb_url);
          if (!href) return '';
          var label = p.label ? t('page_n', { n: p.page }) + ' ' + p.label : t('page_n', { n: p.page });
          return '<button type="button" class="cb-thumb" data-href="' + esc(href) + '" title="' + esc((p.course_title ? p.course_title + ' · ' : '') + label) + '">' +
            (src ? '<img src="' + esc(src) + '" alt="" loading="lazy">' : '') + '<span>' + esc(t('page_n', { n: p.page })) + '</span></button>';
        }).join('') + '</div>';
      }
      h += '</div>';
    });
    if (asking) h += '<div class="cb-msg cb-bot"><span class="cb-typing" aria-label="' + esc(t('thinking')) + '"><i></i><i></i><i></i></span></div>';
    h += '</div>';
    body.innerHTML = h;
    body.querySelectorAll('.cb-chip').forEach(function (c) { c.onclick = function () { scope = c.dataset.s; renderAsk(); }; });
    body.querySelectorAll('.cb-thumb').forEach(function (b) { b.onclick = function () { var u = safeUrl(b.dataset.href); if (u) location.href = u; }; });
    sendBtn.disabled = asking;
    body.scrollTop = body.scrollHeight;
    if (!libsReady() && chat.some(function (m) { return !m.me && !m.err; })) {
      ensureLibs().then(function (ok) { if (ok && open && tab === 'ask') renderAsk(); });
    }
  }

  function send() {
    var v = input.value.trim();
    if (!v || asking) return;
    input.value = '';
    chat.push({ me: true, t: v }); saveChat();
    asking = true; renderAsk();
    var payload = { question: v };
    if (course && scope === 'course') payload.course_key = course.key;
    var libsP = ensureLibs();
    api('POST', C.wikiQuery || '/api/wiki/query', payload).then(function (d) {
      var pages = (d && Array.isArray(d.deck_pages)) ? d.deck_pages.slice(0, 6).map(function (p) {
        return { page: p.page, label: p.label, course_title: p.course_title, thumb_url: p.thumb_url, play_url: p.play_url };
      }) : [];
      chat.push({ me: false, t: (d && d.answer) || t('no_answer'), pages: pages });
    }, function (err) {
      // 会话过期只在面板顶部提示重新登录,不写入对话记录
      if (!(err && err.expired)) chat.push({ me: false, t: (err && err.message) || t('err_generic'), err: true });
    }).then(function () {
      saveChat();
      return libsP;
    }).then(function () {
      asking = false;
      if (open && tab === 'ask') renderAsk(); else sendBtn.disabled = false;
    });
  }
  sendBtn.onclick = send;
  input.addEventListener('keydown', function (e) { if (e.key === 'Enter' && !e.isComposing && e.keyCode !== 229) { e.preventDefault(); send(); } });

  /* ===================== 考核 ===================== */
  var ex = null, exKey = null, exBusy = false, exNote = '', picked = null, bumpScore = false;

  function currentExamKey() { return course ? course.key : (examCourse && examCourse.key); }

  function noteHtml() { return exNote ? '<div class="cb-note">' + esc(exNote) + '</div>' : ''; }

  function syncExamScore(d) {
    if (!d || !course || exKey !== course.key) return;
    prog = prog || { read: { percent: 100, unlocked: true }, exam: {} };
    var avail = prog.exam ? prog.exam.available : undefined;
    prog.exam = { score: d.score || 0, passed: !!d.passed, perfect: !!d.perfect };
    if (avail !== undefined) prog.exam.available = avail;
    syncPet();
  }

  function loadExam(refresh) {
    var key = currentExamKey();
    if (!key) return;
    exKey = key; exBusy = true;
    if (!refresh) ex = null;
    api('GET', courseUrl(key, '/exam/current')).then(function (d) {
      if (exKey !== key) return;
      ex = d; picked = null; exBusy = false; syncExamScore(d);
      if (open && tab === 'exam') render();
    }, function (err) {
      if (exKey !== key) return;
      exBusy = false;
      ex = { error: true };
      exNote = err.message;
      if (course && err.error === 'locked' && prog) { prog.read.unlocked = false; }
      if (course && err.error === 'unavailable' && prog) { prog.read.unavailable = true; }
      if (course && err.error === 'bank_not_ready' && prog && prog.exam) { prog.exam.available = false; }
      if (open && tab === 'exam') render();
    });
  }

  function loadBuddyList() {
    if (buddyLoading) return;
    buddyLoading = true;
    api('GET', API + '/buddy').then(function (d) {
      buddyLoading = false;
      if (d && d.enabled === false) { destroy(); return; }
      buddyList = (d && Array.isArray(d.courses)) ? d.courses : [];
      if (open && tab === 'exam') render();
    }, function (err) {
      buddyLoading = false;
      buddyList = { error: err.message };
      if (open && tab === 'exam') render();
    });
  }

  function renderCourseList() {
    var h = expiredNote();
    setFoot('');
    if (buddyList == null) {
      body.innerHTML = h + '<div class="cb-loading">' + esc(t('loading')) + '</div>';
      if (!expired) loadBuddyList();
      return;
    }
    if (!Array.isArray(buddyList)) {
      body.innerHTML = h + '<div class="cb-note">' + esc(buddyList.error || t('err_generic')) + '</div>';
      return;
    }
    if (!buddyList.length) {
      body.innerHTML = h + '<div class="cb-locked"><div class="cb-big">' + '✓' + '</div>' + esc(t('no_courses')) + '</div>';
      return;
    }
    h += '<div class="cb-clist">' + buddyList.map(function (c, i) {
      return '<button type="button" class="cb-citem' + (c.unlocked ? '' : ' cb-dim') + '" data-i="' + i + '"><span class="cb-n">' + esc(c.title) + '</span>' +
        '<span class="cb-s">' + (c.unlocked ? esc((c.score || 0) + ' / 100') : esc(t('read') + ' ' + (c.read_percent || 0) + '%')) + '</span></button>';
    }).join('') + '</div><p class="cb-tip">' + esc(t('list_tip')) + '</p>';
    body.innerHTML = h;
    body.querySelectorAll('.cb-citem').forEach(function (b) {
      b.onclick = function () {
        var c = buddyList[+b.dataset.i]; if (!c) return;
        if (!c.unlocked) { var u = safeUrl(c.play_url); if (u) location.href = u; return; }
        examCourse = { key: c.key, title: c.title, play_url: c.play_url };
        ex = null; exNote = ''; picked = null;
        render();
      };
    });
  }

  function diffLabel(d) { return d === 1 ? t('easy') : d === 3 ? t('hard') : t('mid'); }
  function inArr(a, v) { return Array.isArray(a) && a.indexOf(v) >= 0; }

  function renderExam() {
    if (!course && !examCourse) { renderCourseList(); return; }
    var key = currentExamKey();
    var h = expiredNote();
    if (!course) h += '<button type="button" class="cb-back" id="cbBack">‹ ' + esc(t('pick_course')) + '</button>';
    setFoot('');
    if (!ex || exKey !== key) {
      body.innerHTML = h + '<div class="cb-loading">' + esc(t('loading')) + '</div>';
      bindBack();
      if (!exBusy || exKey !== key) { if (!expired) loadExam(); }
      return;
    }
    if (ex.error) {
      body.innerHTML = h + noteHtml();
      bindBack();
      return;
    }
    var sc = ex.answered && ex.result ? ex.result.score : ex.score;
    sc = sc || 0;
    h += '<div class="cb-prog"><div class="cb-prog-row"><span>' + esc(t('score')) + '</span><b id="cbScore"' + (bumpScore ? ' class="cb-bump"' : '') + '>' + sc + ' <small>/ 100</small></b></div>' +
      '<div class="cb-bar"><i style="width:' + Math.max(0, Math.min(100, sc)) + '%"></i><span class="cb-pass" data-label="' + esc(t('pass_line') + ' 60') + '"></span></div></div>';
    bumpScore = false;

    if (ex.done) {
      h += '<div class="cb-locked"><div class="cb-big">' + (ex.perfect ? '🏆' : '☕') + '</div>' +
        esc(ex.perfect ? t('perfect_done') : t('exhausted')) + '</div>' + noteHtml();
      body.innerHTML = h;
      setFoot('<button type="button" class="cb-primary" id="cbClose">' + esc(t('done')) + '</button>');
      bindBack();
      foot.querySelector('#cbClose').onclick = function () { finishExam(); };
      return;
    }

    var answered = !!ex.answered, res = ex.result || {};
    var q = answered ? (res.question || ex.question) : ex.question;
    if (q) {
      var typeTag = q.qtype === 'multi' ? ' · ' + t('multi') : q.qtype === 'judge' ? ' · ' + t('judge') : '';
      h += '<div class="cb-qmeta"><span class="cb-d' + (q.difficulty || 2) + '">●</span> ' + esc(diffLabel(q.difficulty)) + ' · ' +
        esc(t('points', { n: q.points || q.difficulty || 1 })) + esc(typeTag) + '</div>';
      h += '<p class="cb-qtext">' + esc(q.question) + '</p>';
      if (q.qtype === 'judge') {
        h += '<div class="cb-judge' + (answered ? ' cb-done' : '') + '">' + [true, false].map(function (v) {
          var cls = '';
          if (answered) { if (v === res.correct_answer) cls = 'cb-right'; else if (v === res.your_answer) cls = 'cb-wrong'; }
          else if (picked === v) cls = 'cb-sel';
          return '<button type="button" class="' + cls + '" data-v="' + v + '" aria-pressed="' + (answered ? v === res.your_answer : picked === v) + '"' + (answered ? ' tabindex="-1"' : '') + '>' + esc(v ? t('yes') : t('no')) + '</button>';
        }).join('') + '</div>';
      } else {
        var multi = q.qtype === 'multi';
        h += '<div class="cb-opts' + (answered ? ' cb-done' : '') + '">' + (q.options || []).map(function (o, i) {
          var cls = 'cb-opt' + (multi ? ' cb-multi' : ''), sel = false;
          if (answered) {
            var isAns = multi ? inArr(res.correct_answer, i) : res.correct_answer === i;
            var mine = multi ? inArr(res.your_answer, i) : res.your_answer === i;
            if (isAns) cls += ' cb-right'; else if (mine) cls += ' cb-wrong';
          } else {
            sel = multi ? inArr(picked, i) : picked === i;
            if (sel) cls += ' cb-sel';
          }
          var k = (multi && !answered) ? (sel ? '✓' : '') : String.fromCharCode(65 + i);
          var pressed = answered ? (multi ? inArr(res.your_answer, i) : res.your_answer === i) : sel;
          return '<button type="button" class="' + cls + '" data-i="' + i + '" aria-pressed="' + pressed + '"' + (answered ? ' tabindex="-1"' : '') + '><span class="cb-k">' + k + '</span><span>' + esc(o) + '</span></button>';
        }).join('') + '</div>';
      }
    }

    var footHtml;
    if (answered) {
      var head = res.correct ? '<b class="cb-ok">' + esc(t('right')) + ' +' + (res.gained || 0) + '</b>'
        : '<b class="cb-no">' + esc(t('wrong')) + '</b> · ' + esc(t('wrong_tip'));
      var src = res.source_page ? ' <span class="cb-src">(' + linkPages(esc(t('see_page', { n: res.source_page }))) + ')</span>' : '';
      h += '<div class="cb-explain">' + head + (res.explain || src ? '<br>' + linkPages(esc(res.explain || '')) + src : '') + '</div>';
      if (res.just_perfect) h += '<div class="cb-cheer">🏆 ' + esc(t('perfect')) + '</div>';
      else if (res.just_passed) h += '<div class="cb-cheer"><div>🎉 ' + esc(t('pass_title')) + ' ' + esc(t('pass_ask')) + '</div>' +
        '<div class="cb-cheer-acts"><button type="button" class="cb-cheer-go" id="cbKeepGoing">' + esc(t('keep_going')) + '</button>' +
        '<button type="button" class="cb-cheer-rest" id="cbTakeRest">' + esc(t('take_rest')) + '</button></div></div>';
      h += noteHtml();
      footHtml = '<button type="button" class="cb-primary" id="cbNext"' + (exBusy ? ' disabled' : '') + '>' + esc(sc >= 100 ? t('done') : t('next')) + '</button>';
    } else {
      var empty = picked === null || (Array.isArray(picked) && !picked.length);
      h += noteHtml();
      footHtml = '<button type="button" class="cb-primary" id="cbSubmit"' + (empty || exBusy ? ' disabled' : '') + '>' + esc(t('submit')) + '</button>';
    }
    var keepScroll = body.scrollTop;
    body.innerHTML = h;
    setFoot(footHtml);
    bindBack();
    bindPageLinks();
    if (answered) {
      // 结果态把解析滚进可视区
      // 有庆祝条(及格/满分)时滚到庆祝条,否则滚到解析
      var exEl = body.querySelector('.cb-cheer') || body.querySelector('.cb-explain');
      if (exEl && exEl.scrollIntoView) exEl.scrollIntoView({ block: 'nearest' });
    } else {
      body.scrollTop = keepScroll;
    }

    if (!answered && q) {
      body.querySelectorAll('[data-i]').forEach(function (b) {
        b.onclick = function () {
          var i = +b.dataset.i;
          if (q.qtype === 'multi') {
            picked = Array.isArray(picked) ? picked : [];
            var k = picked.indexOf(i); if (k >= 0) picked.splice(k, 1); else picked.push(i);
          } else picked = i;
          exNote = ''; renderExam();
          focusSafe(body.querySelector('[data-i="' + i + '"]'));
        };
      });
      body.querySelectorAll('[data-v]').forEach(function (b) {
        b.onclick = function () {
          var v = b.dataset.v; picked = v === 'true'; exNote = ''; renderExam();
          focusSafe(body.querySelector('[data-v="' + v + '"]'));
        };
      });
      var sb = foot.querySelector('#cbSubmit');
      if (sb) sb.onclick = function () { submitAnswer(key); };
    } else if (answered) {
      foot.querySelector('#cbNext').onclick = function () {
        if ((res.score || 0) >= 100 || ex.perfect) { finishExam(); return; }
        nextQuestion(key);
      };
      var go = body.querySelector('#cbKeepGoing'), rest = body.querySelector('#cbTakeRest');
      if (go) go.onclick = function () { nextQuestion(key); };
      if (rest) rest.onclick = function () { toggle(false); say(t('rest_bye'), 4200); };
    }
  }

  // 解析里的「第 N 页 / 第 5、8 页 / 第 23–24 页」→ 页码变成可点链接(先转义再替换,只注入数字)
  var PAGE_REF = /\u7b2c\s*((?:\d+\s*(?:[\u3001,\uff0c\/\uff0f\u2013\-~]|\u548c|\u53ca)\s*)*\d+)\s*\u9875/g;
  function linkPages(escaped) {
    return escaped.replace(PAGE_REF, function (whole, nums) {
      return whole.replace(/\d+/g, function (n) {
        return '<a href="#' + n + '" class="cb-pg" data-page="' + n + '">' + n + '</a>';
      });
    });
  }
  function gotoPage(n) {
    n = parseInt(n, 10);
    if (!n) return;
    // 课程播放器里且考的就是本课 → 直接翻页;否则打开该课并定位
    if (typeof window.cpJump === 'function' && course && exKey === course.key) { window.cpJump(n); return; }
    var base = safeUrl((examCourse && examCourse.play_url) || (course && course.play_url) || '');
    if (base) location.href = base.split('#')[0] + '#' + n;
  }
  function bindPageLinks() {
    body.querySelectorAll('.cb-pg').forEach(function (a) {
      a.onclick = function (e) { e.preventDefault(); gotoPage(a.dataset.page); };
    });
  }

  function bindBack() {
    var b = body.querySelector('#cbBack');
    if (b) b.onclick = function () { examCourse = null; ex = null; exKey = null; exNote = ''; picked = null; buddyList = null; render(); };
  }

  function submitAnswer(key) {
    if (exBusy || picked === null) return;
    var answer = Array.isArray(picked) ? picked.slice().sort(function (a, b) { return a - b; }) : picked;
    exBusy = true; exNote = ''; renderExam();
    api('POST', courseUrl(key, '/exam/answer'), { answer: answer }).then(function (r) {
      if (exKey !== key) return;
      exBusy = false; picked = null;
      ex = Object.assign({}, ex, { answered: true, result: r, score: r.score, passed: ex.passed || r.just_passed || r.score >= 60, perfect: r.score >= 100 });
      if (!ex.question && r.question) ex.question = r.question;
      bumpScore = !!r.correct;
      syncExamScore(ex);
      if (r.just_perfect) { keepExam = true; hop(18); jelly(); fireworks(true); }
      else if (r.just_passed) { hop(18); jelly(); fireworks(false); }
      render();
    }, function (err) {
      if (exKey !== key) return;
      exBusy = false;
      exNote = err.message;
      if (err.error === 'stale_question' || err.error === 'no_question' || err.error === 'already_answered') { picked = null; loadExam(true); }
      else if (err.error === 'locked' || err.error === 'unavailable' || err.error === 'bank_not_ready') { ex = { error: true }; }
      renderExam();
    });
  }

  function nextQuestion(key) {
    if (exBusy) return;
    exBusy = true; exNote = ''; renderExam();
    api('POST', courseUrl(key, '/exam/next'), {}).then(function (d) {
      if (exKey !== key) return;
      exBusy = false; ex = d; picked = null; syncExamScore(d);
      render();
    }, function (err) {
      if (exKey !== key) return;
      exBusy = false; exNote = err.message;
      if (err.error === 'locked' || err.error === 'unavailable' || err.error === 'bank_not_ready') ex = { error: true };
      renderExam();
    });
  }

  function finishExam() {
    toggle(false);
    if (!course) { examCourse = null; ex = null; exKey = null; }
    syncPet();
  }

  /* ===================== 阅读计时(仅 setCourse 后) ===================== */
  var lastActivity = Date.now();
  var timer = { iv: null, page: 1, pending: 0, lastFlush: 0, visited: {} };   // visited:本区间翻过的页(快翻不足 1 秒也算看过)

  function markActivity() {
    lastActivity = Date.now();
    wake();
  }
  function startTimer() {
    if (timer.iv || !course || expired) return;
    timer.visited[timer.page] = 1;
    timer.lastFlush = Date.now();
    timer.iv = setInterval(tick, 1000);
  }
  function stopTimer() {
    if (timer.iv) { clearInterval(timer.iv); timer.iv = null; }
  }
  // 已知取舍:秒数按整秒累计,翻页/上报时不足 1 秒的零头丢弃,每页最多少记约 1 秒,对解锁判断影响可忽略
  function tick() {
    var now = Date.now();
    if ((timer.pending > 0 || hasVisited()) && now - timer.lastFlush >= PING_MS) flush(false);
    if (now - lastActivity >= IDLE_MS) { sleep(); return; }
    if (document.visibilityState === 'visible') timer.pending += 1;
  }
  // 每次上报只针对一页:翻页时先把上一页的累计报掉,保证上报秒数不超过距上次上报的真实间隔
  function hasVisited() { for (var k in timer.visited) { return true; } return false; }
  function flush(final) {
    timer.lastFlush = Date.now();
    if (!course || expired || (timer.pending <= 0 && !hasVisited())) return;
    var visited = Object.keys(timer.visited).map(Number);
    var payload = { page: timer.page, seconds: timer.pending, visited: visited };
    timer.pending = 0;
    timer.visited = {};
    var key = course.key;
    api('POST', courseUrl(key, '/read-ping'), payload, { keepalive: !!final }).then(function (d) {
      if (!final && course && course.key === key) applyProgress(d);
    }, function () {
      // 上报失败:秒数丢弃(防刷规则下补报也会被截断),翻过的页留到下次再报
      if (course && course.key === key) visited.forEach(function (n) { timer.visited[n] = 1; });
    });
  }
  addEventListener('pagehide', function () { if (timer.iv) flush(true); });
  document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'hidden' && timer.iv) flush(false); });

  var sleeping = false;
  function sleep() {
    if (sleeping || open) return;
    sleeping = true;
    wrap.classList.add('cb-sleeping');
    say(t('sleep') + ' 💤', 3200);
  }
  function wake() {
    if (!sleeping) return;
    sleeping = false;
    wrap.classList.remove('cb-sleeping');
    hop(10);
  }

  var lastCheer = 0;
  var gapHint = null;          // 已提醒过的缺口('time' / 'pages'),每门课各一次
  function applyProgress(d, initial) {
    if (!d || !d.read) return;
    var wasUnlocked = unlocked();
    if (d.exam && d.exam.available === undefined && prog && prog.exam && prog.exam.available !== undefined) {
      d.exam.available = prog.exam.available;
    }
    prog = d;
    if (unavailable() || unlocked()) stopTimer();
    // 广播给播放器:用于在课件缩略图上高亮「还没看过」的页
    try {
      window.dispatchEvent(new CustomEvent('cb:progress', { detail: {
        key: course && course.key, unlocked: unlocked(), unavailable: unavailable(),
        seen: Object.keys((d.read && d.read.page_seconds) || {}).map(Number) } }));
    } catch (e) { /* 忽略 */ }
    if (!initial) {
      if (!wasUnlocked && unlocked()) { hop(18); jelly(); say(notReady() ? t('bank_not_ready') : t('unlock'), 4200); }
      else if (!unlocked() && !unavailable()) {
        var g = readGap(), q = Math.floor(readPercent() / 25) * 25;
        // 只差一项时点明差在哪(各提醒一次),否则按 25% 档鼓励
        if (g && g.pagesLeft === 0 && g.secLeft > 0 && gapHint !== 'time') {
          gapHint = 'time'; say(t('hint_all_pages', { t: timeLeftText(g.secLeft) }), 4200);
        } else if (g && g.secLeft === 0 && g.pagesLeft > 0 && gapHint !== 'pages') {
          gapHint = 'pages'; say(t('hint_time_ok', { n: g.pagesLeft }), 4200);
        } else if (q > lastCheer && q > 0) { lastCheer = q; say(t('read_cheer', { p: readPercent() })); }
      }
    } else {
      lastCheer = Math.floor(readPercent() / 25) * 25;
    }
    syncPet();
    if (open) {
      // 只刷新标签,不打断正在作答/输入的内容;考核标签状态变化时整体重绘
      var tabBefore = tab; renderHead();
      if (tab !== tabBefore) render();
    }
  }

  /* ===================== 状态同步(头顶小牌/奖杯) ===================== */
  function syncPet() {
    if (destroyed) return;
    var pf = !!course && perfect();
    wrap.classList.toggle('cb-perfect', pf);
    if (course && prog && !unavailable() && !pf) {
      badge.hidden = false;
      badge.textContent = unlocked() ? score() + '/100' : t('read') + ' ' + readPercent() + '%';
      var hint = readHint();
      if (hint) pet.title = hint; else pet.removeAttribute('title');
    } else {
      badge.hidden = true;
      pet.removeAttribute('title');
    }
  }

  function destroy() {
    destroyed = true;
    stopTimer();
    [wrap, panel, scrim].forEach(function (el) { if (el.parentNode) el.parentNode.removeChild(el); });
  }

  /* ===================== 欢迎 / 每日提醒 ===================== */
  function greet() {
    if (destroyed || course) return;
    var shownHello = false;
    try { shownHello = sessionStorage.getItem('cb-hello') === '1'; } catch (e) { /* 忽略 */ }
    var d = today();
    var nagged = lsGet(NAG_KEY) === d;
    if (nagged) {
      if (!shownHello) { say(t('hello')); try { sessionStorage.setItem('cb-hello', '1'); } catch (e) { /* 忽略 */ } }
      return;
    }
    api('GET', API + '/buddy').then(function (data) {
      if (data && data.enabled === false) { destroy(); return; }
      lsSet(NAG_KEY, d);
      var n = (data && Array.isArray(data.courses)) ? data.courses.length : 0;
      if (course) return;
      if (n > 0) say(t('nag', { n: n }), 3600);
      else if (!shownHello) say(t('hello'));
      try { sessionStorage.setItem('cb-hello', '1'); } catch (e) { /* 忽略 */ }
    }, function () { /* 静默 */ });
  }

  /* ===================== 对外接口 ===================== */
  var api_ = {
    setCourse: function (o) {
      if (destroyed || !o || !o.key) return;
      if (course && course.key === o.key) { course.title = o.title || course.title; course.totalPages = o.totalPages || course.totalPages; return; }
      if (course) { flush(false); stopTimer(); }
      course = { key: String(o.key), title: o.title || '', totalPages: o.totalPages || 0 };
      prog = null; examCourse = null; ex = null; exKey = null; timer.pending = 0; timer.visited = {}; timer.page = parseInt(o.currentPage, 10) || 1; gapHint = null;
      tab = 'exam';
      markActivity();
      applyPos();
      var key = course.key;
      api('GET', courseUrl(key, '/progress')).then(function (d) {
        if (!course || course.key !== key) return;
        applyProgress(d, true);
        if (!unavailable() && !unlocked()) {
          startTimer();
          say(t('read_first'));
        } else if (!unavailable() && !perfect()) {
          say(t('hello'));
        }
        if (open) render();
      }, function () { /* 进度取不到:不计时,保持安静 */ });
    },
    onPage: function (n) {
      n = parseInt(n, 10);
      markActivity();
      if (!n || n < 1) return;
      if (course) timer.visited[n] = 1;
      if (n !== timer.page) { if (timer.iv && timer.pending > 0) flush(false); timer.page = n; }
    },
    activity: function () { markActivity(); },
    reflow: function () { applyPos(); }
  };

  var queued = (window.__cbQueue || []).slice();
  window.__cbQueue = [];
  window.CourseBuddy = api_;
  applyPos(); syncPet(); kick();
  queued.forEach(function (c) { try { api_[c[0]].apply(null, c[1] || []); } catch (e) { /* 忽略 */ } });
  setTimeout(greet, 900);
})();
