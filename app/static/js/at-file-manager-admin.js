/**
 * AT 文件管理后台(管理员) — 复用 /api/file-manager/admin/* 后端 + at-file-utils.js。
 */
(function (g) {
  'use strict';
  var $ = function (id) { return document.getElementById(id); };
  var t = (typeof g.t === 'function') ? g.t : function (s) { return s; };
  var csrf = function () { return (document.querySelector('meta[name="csrf-token"]') || {}).content || ''; };
  var toast = function (m, ty) { if (g.ATToast) ATToast[ty || 'success'](m); };
  var U = g.AtFileUtils || {};
  var A = '/api/file-manager/admin';
  var users = [], curUser = null, transferRef = null;
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]; }); }
  function gj(u) { return fetch(u, { headers: { 'X-Requested-With': 'XMLHttpRequest' } }).then(function (r) { return r.json(); }); }

  function loadUsers() {
    gj(A + '/users').then(function (d) {
      users = (d && d.data) || [];
      $('faUsers').innerHTML = users.map(function (u) {
        return '<div class="fa-user" data-uid="' + u.user_id + '"><div class="fa-user-name">' + esc(u.real_name || u.username) +
          (u.has_locked ? ' <span class="fa-lock">🔒</span>' : '') + '</div>' +
          '<div class="fa-user-meta">' + esc(u.department || '') + ' · ' + (u.file_count || 0) + ' ' + t('个文件') + ' · ' + U.fmtSize(u.total_size) + '</div></div>';
      }).join('') || '<div class="fa-empty">' + t('暂无用户') + '</div>';
      $('faUsers').querySelectorAll('[data-uid]').forEach(function (el) {
        el.addEventListener('click', function () { selectUser(+el.dataset.uid); });
      });
    });
  }
  function selectUser(uid) {
    curUser = uid;
    $('faUsers').querySelectorAll('[data-uid]').forEach(function (el) { el.classList.toggle('on', +el.dataset.uid === uid); });
    var u = users.filter(function (x) { return x.user_id === uid; })[0];
    $('faUserTitle').textContent = (u ? (u.real_name || u.username) : '') + ' · ' + t('文件');
    loadFiles();
  }
  function loadFiles() {
    if (!curUser) return;
    var q = '?user_id=' + curUser + '&search=' + encodeURIComponent($('faSearch').value.trim()) +
      '&sort=' + $('faSort').value + '&include_deleted=' + ($('faShowDeleted').checked ? '1' : '0');
    gj(A + '/files' + q).then(function (d) {
      var rows = (d && d.data) || [];
      if (!rows.length) { $('faBody').innerHTML = '<div class="fa-empty">' + t('无文件') + '</div>'; return; }
      var h = '<table class="fa-list"><thead><tr><th>' + t('名称') + '</th><th style="width:90px;">' + t('大小') + '</th><th style="width:150px;">' + t('修改时间') + '</th><th style="width:40px;"></th></tr></thead><tbody>';
      rows.forEach(function (f) {
        var nm = f.original_filename;
        h += '<tr class="frow" data-pv="' + f.file_ref_id + '" data-mime="' + esc(f.mime_type || '') + '" data-name="' + esc(nm) + '">' +
          '<td>' + U.icon(nm) + ' ' + esc(nm) + (f.is_admin_locked ? ' <span class="fa-lock">🔒</span>' : '') + '</td>' +
          '<td>' + U.fmtSize(f.file_size) + '</td><td style="color:var(--ink-4);">' + U.fmtTime(f.created_at) + '</td>' +
          '<td style="text-align:right;"><span class="fa-rowmenu" data-menu="' + f.file_ref_id + '" data-locked="' + (f.is_admin_locked ? 1 : 0) + '" data-mime="' + esc(f.mime_type || '') + '" data-name="' + esc(nm) + '">⋯</span></td></tr>';
      });
      $('faBody').innerHTML = h + '</tbody></table>';
      bindRows();
    });
  }
  function doPreview(ref, mime, nm) {
    U.preview({
      name: nm, mime: mime,
      officeUrl: A + '/files/' + ref + '/preview-pdf',
      inlineUrl: A + '/files/' + ref + '/download',
      downloadUrl: A + '/files/' + ref + '/download'
    });
  }
  function showFaMenu(ev, items) {
    var m = $('faMenu'); m.innerHTML = '';
    items.forEach(function (it) { var d = document.createElement('div'); d.className = 'fa-menu-item'; d.textContent = it.label; d.addEventListener('click', function () { m.hidden = true; it.fn(); }); m.appendChild(d); });
    m.hidden = false;
    m.style.left = Math.min(ev.clientX, window.innerWidth - 160) + 'px';
    m.style.top = Math.min(ev.clientY, window.innerHeight - m.offsetHeight - 10) + 'px';
  }
  function bindRows() {
    var b = $('faBody');
    b.querySelectorAll('tr.frow').forEach(function (el) {
      el.addEventListener('click', function (e) { if (e.target.closest('[data-menu]')) return; doPreview(el.dataset.pv, el.dataset.mime, el.dataset.name); });
    });
    b.querySelectorAll('[data-menu]').forEach(function (el) {
      el.addEventListener('click', function (e) {
        e.stopPropagation();
        var ref = el.dataset.menu, locked = el.dataset.locked === '1', mime = el.dataset.mime, nm = el.dataset.name;
        showFaMenu(e, [
          { label: t('预览'), fn: function () { doPreview(ref, mime, nm); } },
          { label: t('下载'), fn: function () { g.open(A + '/files/' + ref + '/download', '_blank'); } },
          { label: locked ? t('解锁') : t('锁定'), fn: function () {
            fetch(A + '/files/' + ref + '/lock', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() }, body: JSON.stringify({ locked: !locked }) })
              .then(function (r) { return r.json(); }).then(function (d) { d.success ? (toast(locked ? t('已解锁') : t('已锁定')), loadFiles(), loadUsers()) : toast(d.message, 'error'); }); } },
          { label: t('转移'), fn: function () {
            transferRef = ref;
            $('faTransferUser').innerHTML = users.filter(function (u) { return u.user_id !== curUser; }).map(function (u) { return '<option value="' + u.user_id + '">' + esc(u.real_name || u.username) + '</option>'; }).join('');
            $('faTransferModal').classList.add('open'); } },
        ]);
      });
    });
  }
  g.faClose = function () { $('faTransferModal').classList.remove('open'); };

  function init() {
    $('faTransferOk').addEventListener('click', function () {
      var to = $('faTransferUser').value; if (!to) return;
      fetch(A + '/files/' + transferRef + '/transfer', { method: 'PATCH', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() }, body: JSON.stringify({ to_user_id: +to }) })
        .then(function (r) { return r.json(); }).then(function (d) { if (d.success) { g.faClose(); toast(t('已转移')); loadFiles(); loadUsers(); } else toast(d.message, 'error'); });
    });
    document.addEventListener('click', function (e) { var m = $('faMenu'); if (!m.hidden && !m.contains(e.target)) m.hidden = true; });
    $('faSearch').addEventListener('input', function () { clearTimeout(g._faT); g._faT = setTimeout(loadFiles, 300); });
    $('faSort').addEventListener('change', loadFiles);
    $('faShowDeleted').addEventListener('change', loadFiles);
    loadUsers();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})(window);
