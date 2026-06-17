/**
 * AT 列表批量选择组件 — 通用「批量模式」交互(默认无复选框,进入模式才出现,跨页保留)。
 *
 * 用法:
 *   var bs = AtBatchSelect.init({
 *     key: 'quot',                  // sessionStorage 命名空间(每个列表唯一)
 *     bodyClass: 'q-selmode',       // 进入模式时加到 <body> 的类(配 CSS 显隐复选框列)
 *     rowSel: 'tr.at-row',          // 行选择器(行内需带 data-href 用于非模式态点击跳转)
 *     cbSel: '.q-sel',             // 行内复选框(需带 data-id)
 *     selectAllSel: '#qSelAll',     // 全选本页复选框(可选)
 *     onCount: function (n) {},     // 选中数变化回调(页面据此更新导出按钮)
 *     onOpen: function (tr) {}      // 非模式态点击行(默认跳 data-href)
 *   });
 *   bs.enter(); bs.exit(); bs.getSelected(); bs.inMode();
 *   // 行 onclick 调 bs.rowClick(tr);复选框 onclick 调 bs.toggle(cb);全选 onclick 调 bs.toggleAll(cb)
 *
 * 一个页面可多实例;每实例独立 storage。
 */
(function (g) {
  'use strict';
  function init(opts) {
    var KEY = 'pma_bs_sel_' + opts.key;
    var MODE = 'pma_bs_mode_' + opts.key;
    var ss = g.sessionStorage;

    function getSel() { try { return JSON.parse(ss.getItem(KEY)) || []; } catch (e) { return []; } }
    function setSel(a) { ss.setItem(KEY, JSON.stringify(a)); }
    function has(id) { return getSel().indexOf(String(id)) >= 0; }
    function add(id) { var a = getSel(); if (a.indexOf(String(id)) < 0) { a.push(String(id)); setSel(a); } }
    function rm(id) { setSel(getSel().filter(function (x) { return x !== String(id); })); }
    function inMode() { return ss.getItem(MODE) === '1'; }

    function applyMode() {
      var on = inMode();
      document.body.classList.toggle(opts.bodyClass, on);
      if (opts.onModeChange) opts.onModeChange(on);
    }
    function count() { return getSel().length; }
    function notify() { if (opts.onCount) opts.onCount(count()); }
    function syncPage() {
      var boxes = document.querySelectorAll(opts.cbSel), all = boxes.length > 0;
      boxes.forEach(function (b) { b.checked = has(b.dataset.id); if (!b.checked) all = false; });
      if (opts.selectAllSel) { var sa = document.querySelector(opts.selectAllSel); if (sa) sa.checked = all; }
      notify();
    }

    var api = {
      inMode: inMode,
      getSelected: getSel,
      enter: function () { ss.setItem(MODE, '1'); applyMode(); },
      exit: function () { ss.removeItem(MODE); setSel([]); applyMode(); syncPage(); },
      clear: function () { setSel([]); syncPage(); },
      toggle: function (cb) { cb.checked ? add(cb.dataset.id) : rm(cb.dataset.id); syncPage(); },
      toggleAll: function (cb) {
        document.querySelectorAll(opts.cbSel).forEach(function (b) { b.checked = cb.checked; cb.checked ? add(b.dataset.id) : rm(b.dataset.id); });
        notify();
      },
      rowClick: function (tr) {
        if (inMode()) { var cb = tr.querySelector(opts.cbSel); if (cb) { cb.checked = !cb.checked; api.toggle(cb); } }
        else if (opts.onOpen) opts.onOpen(tr);
        else if (tr.dataset.href) location.href = tr.dataset.href;
      },
      refresh: function () { applyMode(); syncPage(); }
    };

    // 恢复未导出状态:换页 / 切走再切回都从 sessionStorage 回填模式+勾选。
    // 必须兼容脚本在 DOMContentLoaded 之后才执行的情况(底部脚本/外链),否则监听器永不触发。
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', api.refresh);
    } else {
      api.refresh();
    }
    // 浏览器前进/后退缓存(bfcache)恢复页面时不触发 DOMContentLoaded,补一个 pageshow。
    window.addEventListener('pageshow', api.refresh);
    return api;
  }

  g.AtBatchSelect = { init: init };
})(window);
