/**
 * AT 人员多选:已选 chips + 可搜索分组下拉(多选)。可复用。
 * 配套 templates/components/at_people_select.html
 *
 *   var ctl = AtPeopleSelect.init('wiParticipants', { usersUrl, excludeSelf });
 *   ctl.getValue() → [id,...] ; setValue([id,...]) ; clear() ; onChange(fn)
 */
(function (g) {
  'use strict';
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

  function init(rootId, opts) {
    opts = opts || {};
    var root = typeof rootId === 'string' ? document.getElementById(rootId) : rootId;
    if (!root) return null;
    var box = root.querySelector('[data-ps-box]');
    var chipsEl = root.querySelector('[data-ps-chips]');
    var input = root.querySelector('[data-ps-input]');
    var menu = root.querySelector('[data-ps-menu]');
    var usersUrl = opts.usersUrl || root.dataset.usersUrl || '/expense/api/users/same-company';
    var excludeSelf = opts.excludeSelf !== false;
    var users = [];            // {id,name,department}
    var byId = {};
    var selected = [];         // [id]
    var api;

    function load() {
      fetch(usersUrl, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          users = (d.users || []).filter(function (u) { return !(excludeSelf && u.is_current_user); })
            .map(function (u) { return { id: u.id, name: u.real_name || u.name || ('#' + u.id), department: u.department || '未分组' }; });
          byId = {}; users.forEach(function (u) { byId[u.id] = u; });
          renderChips();
        })
        .catch(function () {});
    }
    function avatar(name) {
      return '<span class="at-ps-av">' + esc((name || '?')[0]) + '</span>';
    }
    function renderChips() {
      var html = '';
      selected.forEach(function (id) {
        var u = byId[id]; if (!u) return;
        html += '<span class="at-ps-chip" data-chip="' + id + '">' + avatar(u.name) + esc(u.name) +
          '<button type="button" data-rm="' + id + '" aria-label="remove">×</button></span>';
      });
      chipsEl.innerHTML = html;
      chipsEl.querySelectorAll('[data-rm]').forEach(function (b) {
        b.addEventListener('click', function (e) { e.stopPropagation(); toggle(+b.dataset.rm); });
      });
    }
    function renderMenu() {
      var term = (input.value || '').trim().toLowerCase();
      var list = users.filter(function (u) { return !term || (u.name + ' ' + u.department).toLowerCase().indexOf(term) >= 0; });
      var groups = {};
      list.forEach(function (u) { (groups[u.department] = groups[u.department] || []).push(u); });
      var html = '';
      Object.keys(groups).forEach(function (dep) {
        html += '<div class="at-ps-grp">' + esc(dep) + '</div>';
        groups[dep].forEach(function (u) {
          var on = selected.indexOf(u.id) >= 0;
          html += '<div class="at-ps-item' + (on ? ' on' : '') + '" data-uid="' + u.id + '">' +
            avatar(u.name) + '<span style="flex:1;">' + esc(u.name) + '</span>' +
            (on ? '<span class="at-ps-check">✓</span>' : '') + '</div>';
        });
      });
      menu.innerHTML = html || '<div class="at-dim" style="padding:16px;text-align:center;font-size:12px;">无匹配</div>';
      menu.querySelectorAll('[data-uid]').forEach(function (el) {
        el.addEventListener('click', function (e) { e.stopPropagation(); toggle(+el.dataset.uid); });
      });
    }
    function toggle(id) {
      if (opts.single) {
        selected = (selected.length && selected[0] === id) ? [] : [id];
        renderChips(); renderMenu(); close();
      } else {
        var i = selected.indexOf(id);
        if (i >= 0) selected.splice(i, 1); else selected.push(id);
        renderChips(); renderMenu();
      }
      if (api._onChange) api._onChange(selected.slice());
    }
    function open() { renderMenu(); menu.hidden = false; }
    function close() { menu.hidden = true; }

    box.addEventListener('click', function () { input.focus(); if (menu.hidden) open(); });
    input.addEventListener('focus', open);
    input.addEventListener('input', function () { if (menu.hidden) menu.hidden = false; renderMenu(); });
    document.addEventListener('click', function (e) { if (!root.contains(e.target)) close(); });

    api = {
      getValue: function () { return selected.slice(); },
      setValue: function (ids) { selected = (ids || []).map(Number).filter(function (x) { return !isNaN(x); }); renderChips(); },
      clear: function () { selected = []; input.value = ''; renderChips(); },
      onChange: function (fn) { api._onChange = fn; return api; }
    };
    root._atps = api;
    load();
    return api;
  }
  g.AtPeopleSelect = { init: init };
})(window);
