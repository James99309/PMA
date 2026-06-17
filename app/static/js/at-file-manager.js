/**
 * AT 资料管理 — 对接 /files 既有后端 API。
 * 文件夹树 / 网格·列表 / 上传(简单+分块) / 增删改移 / 回收站 / 搜索 / 配额 / 拖拽移动 / 文件夹共享。
 */
(function (g) {
  'use strict';
  var CFG = {};
  var $ = function (id) { return document.getElementById(id); };
  var t = (typeof g.t === 'function') ? g.t : function (s) { return s; };
  var csrf = function () { return (document.querySelector('meta[name="csrf-token"]') || {}).content || ''; };
  var toast = function (m, ty) { if (g.ATToast) ATToast[ty || 'success'](m); };
  var API = '/files/api';

  var state = {
    folderId: null,        // 当前文件夹(null=根)
    view: 'grid',          // grid | list
    nav: 'all',            // all | shared | trash
    tree: [],              // 文件夹树
    expanded: {},          // 展开的文件夹 id
    items: { folders: [], files: [] },
    sel: {},               // 选中文件 id 集
    moveTarget: null,      // 移动目标
    shareUsersCtl: null,
    curShareFolder: null,
  };

  var U = g.AtFileUtils || {};
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]; }); }
  function escAttr(s) { return esc(s).replace(/"/g, '&quot;'); }
  var fmtSize = U.fmtSize, extIcon = U.icon;   // 共享自 at-file-utils.js
  function getJSON(url) { return fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } }).then(function (r) { return r.json(); }); }
  function send(url, method, body) {
    return fetch(url, {
      method: method, headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() },
      body: body ? JSON.stringify(body) : undefined
    }).then(function (r) { return r.json(); });
  }

  /* ───────── 文件夹树 ───────── */
  function loadTree(cb) {
    getJSON(API + '/folders').then(function (d) {
      state.tree = (d && d.data) || [];
      renderTree(); if (cb) cb();
    }).catch(function () { state.tree = []; renderTree(); if (cb) cb(); });
  }
  function treeRowsHtml(nodes, depth) {
    var html = '';
    (nodes || []).forEach(function (f) {
      var hasKids = f.children && f.children.length;
      var open = !!state.expanded[f.id];
      var on = (state.nav === 'all' && String(state.folderId) === String(f.id));
      html += '<div class="fm-tree-row' + (on ? ' on' : '') + '" data-folder="' + f.id + '" draggable="false" style="padding-left:' + (8 + depth * 14) + 'px;">';
      if (hasKids) {
        html += '<span class="fm-tree-caret' + (open ? ' open' : '') + '" data-caret="' + f.id + '">' +
          '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg></span>';
      } else { html += '<span class="fm-tree-caret"></span>'; }
      html += '<span style="flex-shrink:0;">📁</span><span class="fm-tree-name">' + esc(f.name) + '</span>';
      html += '<span class="fm-tree-act" data-folder-menu="' + f.id + '" data-name="' + escAttr(f.name) + '">⋯</span></div>';
      if (hasKids && open) html += treeRowsHtml(f.children, depth + 1);
    });
    return html;
  }
  function renderTree() {
    var box = $('fmTree');
    var rows = treeRowsHtml(state.tree, 0);
    box.innerHTML = rows || '<div class="at-dim" style="font-size:12px;padding:6px 8px;">' + t('暂无文件夹') + '</div>';
    bindTree();
    // 同步左上「全部文件」高亮(根目录)
    $('fmNavAll').classList.toggle('on', state.nav === 'all');
  }
  function bindTree() {
    var box = $('fmTree');
    box.querySelectorAll('[data-caret]').forEach(function (el) {
      el.addEventListener('click', function (e) { e.stopPropagation(); var id = el.dataset.caret; state.expanded[id] = !state.expanded[id]; renderTree(); });
    });
    box.querySelectorAll('.fm-tree-row[data-folder]').forEach(function (el) {
      el.addEventListener('click', function (e) {
        if (e.target.closest('[data-caret]') || e.target.closest('[data-folder-menu]')) return;
        openFolder(el.dataset.folder ? +el.dataset.folder : null);
      });
      // 拖放目标(文件拖到文件夹)
      el.addEventListener('dragover', function (e) { e.preventDefault(); el.classList.add('drop'); });
      el.addEventListener('dragleave', function () { el.classList.remove('drop'); });
      el.addEventListener('drop', function (e) {
        e.preventDefault(); el.classList.remove('drop');
        var fid = e.dataTransfer.getData('text/file-id');
        if (fid) moveFileTo(+fid, el.dataset.folder ? +el.dataset.folder : null);
      });
    });
    box.querySelectorAll('[data-folder-menu]').forEach(function (el) {
      el.addEventListener('click', function (e) { e.stopPropagation(); folderMenu(e, +el.dataset.folderMenu, el.dataset.name); });
    });
  }

  /* ───────── 列表/导航 ───────── */
  function setNav(nav) {
    state.nav = nav; state.sel = {}; updateBatchBar();
    $('fmNavAll').classList.toggle('on', nav === 'all');
    $('fmNavShared').classList.toggle('on', nav === 'shared');
    $('fmNavTrash').classList.toggle('on', nav === 'trash');
    if (nav === 'all') openFolder(state.folderId);
    else if (nav === 'trash') loadTrash();
    else loadShared();
  }
  function openFolder(folderId) {
    state.nav = 'all'; state.folderId = folderId; state.sel = {}; updateBatchBar();
    $('fmNavAll').classList.add('on'); $('fmNavShared').classList.remove('on'); $('fmNavTrash').classList.remove('on');
    getJSON(API + '/list?folder_id=' + (folderId || '')).then(function (d) {
      if (!d.success) { toast(d.message || t('加载失败'), 'error'); return; }
      state.items = d.data || { folders: [], files: [] };
      renderCrumbs(d.breadcrumbs || []);
      renderQuota(d.quota);
      renderTree();
      renderBody();
    }).catch(function () { toast(t('加载失败'), 'error'); });
  }
  function loadTrash() {
    renderCrumbs([{ id: null, name: t('回收站'), _trash: true }]);
    getJSON(API + '/trash').then(function (d) {
      state.items = { folders: [], files: (d && d.data) || [] };
      renderBody();
    });
  }
  function loadShared() {
    renderCrumbs([{ id: null, name: t('共享给我'), _shared: true }]);
    getJSON(API + '/shared-with-me').then(function (d) {
      state.items = { folders: ((d && d.data) || []).map(function (s) { return { id: s.folder_id, name: s.name, _shared: true, share: s }; }), files: [] };
      renderBody();
    });
  }
  function renderQuota(q) {
    if (!q) return;
    $('fmQuotaFill').style.width = Math.min(100, q.percent || 0) + '%';
    $('fmQuotaText').textContent = fmtSize(q.used) + ' / ' + fmtSize(q.quota);
  }
  function renderCrumbs(crumbs) {
    var box = $('fmCrumbs'); var html = '';
    if (state.nav === 'all') {
      html += '<span class="fm-crumb" data-cf="">' + t('全部文件') + '</span>';
      (crumbs || []).forEach(function (c, i) {
        var last = i === crumbs.length - 1;
        html += '<span style="color:var(--ink-4);">/</span><span class="fm-crumb' + (last ? ' cur' : '') + '" data-cf="' + c.id + '">' + esc(c.name) + '</span>';
      });
    } else {
      html += '<span class="fm-crumb cur">' + esc(crumbs[0].name) + '</span>';
    }
    box.innerHTML = html;
    box.querySelectorAll('.fm-crumb[data-cf]').forEach(function (el) {
      el.addEventListener('click', function () { openFolder(el.dataset.cf ? +el.dataset.cf : null); });
    });
  }

  /* ───────── 主体渲染(网格/列表) ───────── */
  function renderBody() {
    var box = $('fmBody');
    var folders = state.items.folders || [], files = state.items.files || [];
    if (!folders.length && !files.length) {
      var ico = state.nav === 'trash' ? '🗑️' : state.nav === 'shared' ? '🤝' : '📂';
      var msg = state.nav === 'trash' ? t('回收站为空') : state.nav === 'shared' ? t('暂无共享') : t('此文件夹为空,拖拽或点上传添加文件');
      box.innerHTML = '<div class="fm-empty"><div style="font-size:40px;margin-bottom:10px;opacity:.6;">' + ico + '</div>' + msg + '</div>';
      return;
    }
    if (state.view === 'grid') box.innerHTML = gridHtml(folders, files);
    else box.innerHTML = listHtml(folders, files);
    if (state.nav === 'trash') box.insertAdjacentHTML('beforeend', '<div style="text-align:right;margin-top:12px;"><button type="button" onclick="fmEmptyTrash()" style="border:0;background:transparent;color:var(--danger);cursor:pointer;font-size:12.5px;">' + t('清空回收站') + '</button></div>');
    bindBody();
  }
  function gridHtml(folders, files) {
    var h = '<div class="fm-grid">';
    folders.forEach(function (f) {
      h += '<div class="fm-tile" data-folder-open="' + f.id + '"' + (f._shared ? '' : ' data-folder-drop="' + f.id + '"') + '>' +
        '<div class="fm-tile-ico">📁</div><div class="fm-tile-name">' + esc(f.name) + '</div>' +
        '<div class="fm-tile-meta">' + (f._shared ? (t('来自') + ' ' + esc(f.share.shared_by || '')) : (f.item_count != null ? f.item_count + ' ' + t('项') : '')) + '</div>' +
        (f._shared ? '' : '<span class="fm-tile-menu" data-folder-menu="' + f.id + '" data-name="' + escAttr(f.name) + '">⋯</span>') + '</div>';
    });
    files.forEach(function (f) {
      var sel = state.sel[f.id];
      h += '<div class="fm-tile' + (sel ? ' sel' : '') + '" data-file="' + f.id + '" draggable="' + (state.nav === 'all') + '">' +
        '<input type="checkbox" class="fm-tile-chk" data-file-chk="' + f.id + '"' + (sel ? ' checked' : '') + '>' +
        '<div class="fm-tile-ico">' + extIcon(f.display_name) + '</div>' +
        '<div class="fm-tile-name" title="' + escAttr(f.display_name) + '">' + esc(f.display_name) + '</div>' +
        '<div class="fm-tile-meta">' + fmtSize(f.file_size) + '</div>' +
        '<span class="fm-tile-menu" data-file-menu="' + f.id + '" data-name="' + escAttr(f.display_name) + '">⋯</span></div>';
    });
    return h + '</div>';
  }
  function listHtml(folders, files) {
    var h = '<table class="fm-list"><thead><tr><th style="width:30px;"></th><th>' + t('名称') + '</th><th style="width:90px;">' + t('大小') + '</th><th style="width:140px;">' + t('修改时间') + '</th><th style="width:40px;"></th></tr></thead><tbody>';
    folders.forEach(function (f) {
      h += '<tr class="file-row" data-folder-open="' + f.id + '"><td>📁</td><td>' + esc(f.name) + '</td><td>—</td><td>' + esc(f.updated_at || '') + '</td>' +
        '<td>' + (f._shared ? '' : '<span class="fm-tile-menu" style="opacity:1;" data-folder-menu="' + f.id + '" data-name="' + escAttr(f.name) + '">⋯</span>') + '</td></tr>';
    });
    files.forEach(function (f) {
      var sel = state.sel[f.id];
      h += '<tr class="file-row' + (sel ? ' sel' : '') + '" data-file="' + f.id + '"><td><input type="checkbox" data-file-chk="' + f.id + '"' + (sel ? ' checked' : '') + '></td>' +
        '<td>' + extIcon(f.display_name) + ' ' + esc(f.display_name) + '</td><td>' + fmtSize(f.file_size) + '</td><td>' + esc((f.created_at || f.deleted_at || '')) + '</td>' +
        '<td><span class="fm-tile-menu" style="opacity:1;" data-file-menu="' + f.id + '" data-name="' + escAttr(f.display_name) + '">⋯</span></td></tr>';
    });
    return h + '</tbody></table>';
  }
  function bindBody() {
    var box = $('fmBody');
    box.querySelectorAll('[data-folder-open]').forEach(function (el) {
      el.addEventListener('click', function (e) {
        if (e.target.closest('[data-folder-menu]')) return;
        var f = (state.items.folders || []).filter(function (x) { return String(x.id) === el.dataset.folderOpen; })[0];
        if (f && f._shared) { openSharedFolder(f.id); return; }
        openFolder(+el.dataset.folderOpen);
      });
    });
    // 文件夹拖放目标
    box.querySelectorAll('[data-folder-drop]').forEach(function (el) {
      el.addEventListener('dragover', function (e) { e.preventDefault(); el.classList.add('sel'); });
      el.addEventListener('dragleave', function () { el.classList.remove('sel'); });
      el.addEventListener('drop', function (e) {
        e.preventDefault(); el.classList.remove('sel');
        var fid = e.dataTransfer.getData('text/file-id');
        if (fid) moveFileTo(+fid, +el.dataset.folderDrop);
      });
    });
    box.querySelectorAll('[data-file]').forEach(function (el) {
      el.addEventListener('click', function (e) {
        if (e.target.closest('[data-file-chk]') || e.target.closest('[data-file-menu]')) return;
        fmOpenFile(+el.dataset.file);
      });
      if (el.getAttribute('draggable') === 'true') {
        el.addEventListener('dragstart', function (e) { e.dataTransfer.setData('text/file-id', el.dataset.file); e.dataTransfer.effectAllowed = 'move'; });
      }
    });
    box.querySelectorAll('[data-file-chk]').forEach(function (el) {
      el.addEventListener('change', function (e) { e.stopPropagation(); var id = el.dataset.fileChk; if (el.checked) state.sel[id] = 1; else delete state.sel[id]; updateBatchBar(); renderBody(); });
      el.addEventListener('click', function (e) { e.stopPropagation(); });
    });
    box.querySelectorAll('[data-file-menu]').forEach(function (el) {
      el.addEventListener('click', function (e) { e.stopPropagation(); fileMenu(e, +el.dataset.fileMenu, el.dataset.name); });
    });
    box.querySelectorAll('[data-folder-menu]').forEach(function (el) {
      el.addEventListener('click', function (e) { e.stopPropagation(); folderMenu(e, +el.dataset.folderMenu, el.dataset.name); });
    });
  }

  /* ───────── 行内菜单 ───────── */
  function showMenu(ev, items) {
    var m = $('fmCtxMenu'); m.innerHTML = '';
    items.forEach(function (it) {
      if (!it) return;
      var d = document.createElement('div'); d.className = 'fm-menu-item' + (it.danger ? ' danger' : ''); d.textContent = it.label;
      d.addEventListener('click', function () { m.hidden = true; it.fn(); });
      m.appendChild(d);
    });
    m.hidden = false;
    var x = Math.min(ev.clientX, window.innerWidth - 170), y = Math.min(ev.clientY, window.innerHeight - m.offsetHeight - 10);
    m.style.left = x + 'px'; m.style.top = y + 'px';
  }
  function fileMenu(ev, id, name) {
    if (state.nav === 'trash') {
      showMenu(ev, [
        { label: t('还原'), fn: function () { send(API + '/trash/' + id + '/restore', 'POST').then(function (d) { d.success ? (toast(t('已还原')), loadTrash(), loadTree()) : toast(d.message, 'error'); }); } },
        { label: t('彻底删除'), danger: true, fn: function () { confirmDo(t('彻底删除该文件?不可恢复'), function () { send(API + '/trash/' + id + '/permanent', 'DELETE').then(function (d) { d.success ? (toast(t('已删除')), loadTrash()) : toast(d.message, 'error'); }); }); } },
      ]); return;
    }
    showMenu(ev, [
      { label: t('预览'), fn: function () { fmOpenFile(id); } },
      { label: t('下载'), fn: function () { window.open(API + '/files/' + id + '/download', '_blank'); } },
      { label: t('重命名'), fn: function () { fmRename('file', id, name); } },
      { label: t('移动到'), fn: function () { openMove([id]); } },
      { label: t('删除'), danger: true, fn: function () { confirmDo(t('将文件移入回收站?'), function () { send(API + '/files/' + id + '/delete', 'POST').then(function (d) { d.success ? (toast(t('已删除')), openFolder(state.folderId)) : toast(d.message, 'error'); }); }); } },
    ]);
  }
  function folderMenu(ev, id, name) {
    showMenu(ev, [
      { label: t('重命名'), fn: function () { fmRename('folder', id, name); } },
      { label: t('共享'), fn: function () { openShare(id, name); } },
      { label: t('删除'), danger: true, fn: function () { confirmDo(t('删除文件夹及其内容?'), function () { send(API + '/folders/' + id, 'DELETE').then(function (d) { d.success ? (toast(t('已删除')), loadTree(), openFolder(state.folderId)) : toast(d.message, 'error'); }); }); } },
    ]);
  }
  function confirmDo(msg, fn) {
    if (g.ATConfirm) ATConfirm.show({ title: t('确认'), message: msg, variant: 'danger', confirmText: t('确定'), cancelText: t('取消'), onConfirm: fn });
    else if (confirm(msg)) fn();
  }

  /* ───────── 上传(XHR 进度面板 + 简单/分块 + 文件夹结构) ───────── */
  var upQueue = [];   // [{name, pct, status:'wait|up|done|err'}]
  function uuid() { return (g.crypto && crypto.randomUUID) ? crypto.randomUUID() : ('xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) { var r = Math.random() * 16 | 0; return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16); })); }
  function renderUpPanel() {
    var panel = $('fmUploadPanel');
    if (!upQueue.length) { panel.hidden = true; return; }   // 无任务不显示空面板
    panel.hidden = false;
    var done = upQueue.filter(function (q) { return q.status === 'done' || q.status === 'err'; }).length;
    $('fmUpTitle').textContent = t('上传') + ' ' + done + '/' + upQueue.length;
    $('fmUpList').innerHTML = upQueue.map(function (q) {
      var stTxt = q.status === 'done' ? '✓' : q.status === 'err' ? t('失败') : (q.status === 'up' ? (q.pct + '%') : '…');
      return '<div class="fm-up-row ' + (q.status === 'done' ? 'done' : q.status === 'err' ? 'err' : '') + '">' +
        '<div class="fm-up-name"><span style="overflow:hidden;text-overflow:ellipsis;">' + esc(q.name) + '</span><span class="st">' + stTxt + '</span></div>' +
        '<div class="fm-up-bar"><div class="fm-up-fill" style="width:' + (q.status === 'done' ? 100 : q.pct) + '%"></div></div></div>';
    }).join('');
  }
  function xhrPost(url, fd, onProg) {
    return new Promise(function (resolve) {
      var xhr = new XMLHttpRequest();
      xhr.open('POST', url);
      xhr.setRequestHeader('X-CSRFToken', csrf());
      if (xhr.upload && onProg) xhr.upload.onprogress = function (e) { if (e.lengthComputable) onProg(e.loaded / e.total); };
      xhr.onload = function () { try { resolve(JSON.parse(xhr.responseText)); } catch (_) { resolve({ success: xhr.status >= 200 && xhr.status < 300 }); } };
      xhr.onerror = function () { resolve({ success: false }); };
      xhr.send(fd);
    });
  }
  function uploadOne(file, folderId, q) {
    q.status = 'up'; q.pct = 0; renderUpPanel();
    if (file.size > CFG.chunk_threshold) return uploadChunkedX(file, folderId, q);
    var fd = new FormData(); fd.append('file', file); if (folderId) fd.append('folder_id', folderId);
    return xhrPost(API + '/upload', fd, function (p) { q.pct = Math.round(p * 100); renderUpPanel(); })
      .then(function (d) { q.status = d && d.success ? 'done' : 'err'; renderUpPanel(); return d; });
  }
  function uploadChunkedX(file, folderId, q) {
    var uid = uuid(), size = CFG.chunk_size, total = Math.ceil(file.size / size);
    function part(idx) {
      if (idx >= total) { q.status = 'done'; renderUpPanel(); return Promise.resolve({ success: true }); }
      var fd = new FormData();
      fd.append('file', file.slice(idx * size, (idx + 1) * size));
      fd.append('upload_id', uid); fd.append('filename', file.name);
      fd.append('chunk_index', idx); fd.append('total_chunks', total);
      if (folderId) fd.append('folder_id', folderId);
      return xhrPost(API + '/upload/chunk', fd, function (p) {
        q.pct = Math.round(((idx + p) / total) * 100); renderUpPanel();
      }).then(function (d) {
        if (d && (d.pending || d.success)) return part(idx + 1);
        q.status = 'err'; renderUpPanel(); return d;
      });
    }
    return part(0);
  }
  // 文件队列上传(可带每文件目标 folderId);files: [{file, folderId}]
  function runUploads(tasks) {
    upQueue = tasks.map(function (x) { return { name: x.file.name, pct: 0, status: 'wait' }; });
    renderUpPanel();
    var i = 0;
    function next() {
      if (i >= tasks.length) { openFolder(state.folderId); loadTree(); setTimeout(function () { upQueue = []; $('fmUploadPanel').hidden = true; }, 1800); return; }
      uploadOne(tasks[i].file, tasks[i].folderId, upQueue[i]).then(function () { i++; next(); });
    }
    next();
  }
  function uploadFiles(fileList) {
    var files = Array.prototype.slice.call(fileList || []);
    if (!files.length) return;
    runUploads(files.map(function (f) { return { file: f, folderId: state.folderId }; }));
  }
  // 文件夹上传:按 webkitRelativePath 重建目录后逐个上传
  function uploadFolder(fileList) {
    var files = Array.prototype.slice.call(fileList || []);
    if (!files.length) return;
    var dirCache = {};  // relDir -> folderId
    function ensureDir(relDir) {
      if (!relDir) return Promise.resolve(state.folderId);
      if (dirCache[relDir] != null) return Promise.resolve(dirCache[relDir]);
      var parts = relDir.split('/');
      var parentRel = parts.slice(0, -1).join('/');
      return ensureDir(parentRel).then(function (parentId) {
        return send(API + '/folders', 'POST', { name: parts[parts.length - 1], parent_id: parentId })
          .then(function (d) { var fid = (d && d.success) ? d.data.id : parentId; dirCache[relDir] = fid; return fid; });
      });
    }
    toast(t('正在创建文件夹结构…'));
    // 依次解析每个文件的目标目录
    var tasks = [];
    var idx = 0;
    function build() {
      if (idx >= files.length) { runUploads(tasks); return; }
      var f = files[idx];
      var rel = f.webkitRelativePath || f.name;
      var dir = rel.split('/').slice(0, -1).join('/');
      ensureDir(dir).then(function (fid) { tasks.push({ file: f, folderId: fid }); idx++; build(); });
    }
    build();
  }
  g.fmCloseUpload = function () { upQueue = []; $('fmUploadPanel').hidden = true; };
  g.fmUploadMenu = function (ev) {
    if (ev) ev.stopPropagation();   // 阻止冒泡到 document 把菜单立刻关掉
    showMenu(ev, [
      { label: t('上传文件'), fn: function () { $('fmUploadInput').click(); } },
      { label: t('上传文件夹'), fn: function () { $('fmFolderInput').click(); } },
    ]);
  };

  /* ───────── 重命名 / 新建文件夹 ───────── */
  var nameCtx = null;
  function fmRename(kind, id, cur) {
    nameCtx = { kind: kind, id: id };
    $('fmNameTitle').textContent = t('重命名');
    $('fmNameInput').value = cur || '';
    openModal('fmNameModal'); setTimeout(function () { $('fmNameInput').focus(); $('fmNameInput').select(); }, 0);
  }
  g.fmNewFolder = function () {
    nameCtx = { kind: 'newfolder' };
    $('fmNameTitle').textContent = t('新建文件夹');
    $('fmNameInput').value = '';
    openModal('fmNameModal'); setTimeout(function () { $('fmNameInput').focus(); }, 0);
  };
  function doName() {
    var v = $('fmNameInput').value.trim(); if (!v) { toast(t('请输入名称'), 'error'); return; }
    var p;
    if (nameCtx.kind === 'newfolder') p = send(API + '/folders', 'POST', { name: v, parent_id: state.folderId });
    else if (nameCtx.kind === 'folder') p = send(API + '/folders/' + nameCtx.id, 'PUT', { name: v });
    else p = send(API + '/files/' + nameCtx.id + '/rename', 'POST', { name: v });
    p.then(function (d) {
      if (d.success) { closeModal('fmNameModal'); toast(t('已保存')); loadTree(); openFolder(state.folderId); }
      else toast(d.message || t('保存失败'), 'error');
    });
  }

  /* ───────── 移动 ───────── */
  var moveCtx = null;
  function openMove(fileIds) {
    moveCtx = { fileIds: fileIds }; state.moveTarget = null;
    $('fmMoveTree').innerHTML = moveTreeHtml(null, t('全部文件'), state.tree, 0);
    openModal('fmMoveModal');
    $('fmMoveTree').querySelectorAll('[data-mv]').forEach(function (el) {
      el.addEventListener('click', function () {
        $('fmMoveTree').querySelectorAll('[data-mv]').forEach(function (x) { x.classList.remove('on'); });
        el.classList.add('on'); state.moveTarget = el.dataset.mv === '' ? null : +el.dataset.mv;
      });
    });
  }
  function moveTreeHtml(rootId, rootLabel, nodes, depth) {
    var html = '';
    if (depth === 0) html += '<div class="fm-tree-row" data-mv="" style="padding-left:8px;"><span>🏠</span> ' + esc(rootLabel) + '</div>';
    (nodes || []).forEach(function (f) {
      html += '<div class="fm-tree-row" data-mv="' + f.id + '" style="padding-left:' + (8 + depth * 16 + 16) + 'px;"><span>📁</span> ' + esc(f.name) + '</div>';
      if (f.children && f.children.length) html += moveTreeHtml(f.id, '', f.children, depth + 1);
    });
    return html;
  }
  function doMove() {
    var ids = moveCtx.fileIds;
    var p = ids.length === 1
      ? send(API + '/files/' + ids[0] + '/move', 'POST', { folder_id: state.moveTarget })
      : send(API + '/files/move-batch', 'POST', { file_ids: ids, folder_id: state.moveTarget });
    p.then(function (d) { if (d.success) { closeModal('fmMoveModal'); toast(t('已移动')); state.sel = {}; updateBatchBar(); openFolder(state.folderId); } else toast(d.message || t('移动失败'), 'error'); });
  }
  function moveFileTo(fileId, folderId) {
    send(API + '/files/' + fileId + '/move', 'POST', { folder_id: folderId })
      .then(function (d) { if (d.success) { toast(t('已移动')); openFolder(state.folderId); } else toast(d.message || t('移动失败'), 'error'); });
  }

  /* ───────── 批量 ───────── */
  function updateBatchBar() {
    var n = Object.keys(state.sel).length;
    $('fmBatchBar').style.display = n ? 'flex' : 'none';
    if (n) $('fmBatchCount').textContent = t('已选 {n} 项').replace('{n}', n);
  }
  g.fmClearSel = function () { state.sel = {}; updateBatchBar(); renderBody(); };
  g.fmBatchMove = function () { openMove(Object.keys(state.sel).map(Number)); };
  g.fmBatchDelete = function () {
    var ids = Object.keys(state.sel).map(Number);
    confirmDo(t('将所选文件移入回收站?'), function () {
      send(API + '/files/delete-batch', 'POST', { file_ids: ids }).then(function (d) { if (d.success) { toast(t('已删除')); state.sel = {}; updateBatchBar(); openFolder(state.folderId); } else toast(d.message, 'error'); });
    });
  };
  g.fmEmptyTrash = function () { confirmDo(t('清空回收站?不可恢复'), function () { send(API + '/trash/empty', 'POST').then(function (d) { d.success ? (toast(t('已清空')), loadTrash()) : toast(d.message, 'error'); }); }); };

  /* ───────── 共享 ───────── */
  function openShare(folderId, name) {
    state.curShareFolder = folderId;
    $('fmShareTitle').textContent = t('共享') + ' · ' + name;
    if (state.shareUsersCtl) state.shareUsersCtl.clear();
    loadShares(folderId);
    openModal('fmShareModal');
  }
  function loadShares(folderId) {
    getJSON(API + '/folders/' + folderId + '/shares').then(function (d) {
      var box = $('fmShareList'); var list = (d && d.data) || [];
      if (!list.length) { box.innerHTML = '<div class="at-dim" style="font-size:12px;padding:8px;">' + t('尚未共享') + '</div>'; return; }
      box.innerHTML = list.map(function (s) {
        return '<div style="display:flex;align-items:center;gap:8px;padding:7px 4px;border-bottom:1px solid var(--line-soft);font-size:13px;">' +
          '<span style="flex:1;">' + esc(s.name || s.user_name || ('#' + s.user_id)) + '</span>' +
          '<span class="at-dim" style="font-size:11px;">' + (s.permission === 'edit' ? t('可编辑') : t('只读')) + '</span>' +
          '<button type="button" data-unshare="' + s.user_id + '" style="border:0;background:transparent;color:var(--danger);cursor:pointer;">×</button></div>';
      }).join('');
      box.querySelectorAll('[data-unshare]').forEach(function (el) {
        el.addEventListener('click', function () {
          send(API + '/folders/' + folderId + '/shares/' + el.dataset.unshare, 'DELETE').then(function (r) { if (r.success) loadShares(folderId); });
        });
      });
    });
  }

  /* ───────── 预览/打开文件 ───────── */
  function fmOpenFile(id) {
    var f = (state.items.files || []).filter(function (x) { return String(x.id) === String(id); })[0];
    if (!f) return;
    U.preview({
      name: f.display_name || '', mime: f.mime_type,
      officeUrl: API + '/files/' + id + '/preview-pdf',
      inlineUrl: API + '/files/' + id + '/preview',
      downloadUrl: API + '/files/' + id + '/download'
    });
  }
  function openSharedFolder(folderId) {
    getJSON(API + '/shared-with-me/' + folderId + '/content').then(function (d) {
      if (!d.success) { toast(d.message || t('无权查看'), 'error'); return; }
      state.items = d.data || { folders: [], files: [] };
      renderCrumbs([{ id: null, name: t('共享给我'), _shared: true }]);
      renderBody();
    });
  }

  /* ───────── 弹窗工具 ───────── */
  function openModal(id) { $(id).classList.add('open'); }
  function closeModal(id) { $(id).classList.remove('open'); }
  g.fmCloseModal = closeModal;

  /* ───────── 搜索 ───────── */
  var searchTimer = null;
  function doSearch(q) {
    if (!q) { openFolder(state.folderId); return; }
    getJSON(API + '/search?q=' + encodeURIComponent(q)).then(function (d) {
      state.nav = 'all';
      state.items = { folders: [], files: (d && d.data) || [] };
      renderCrumbs([{ id: null, name: t('搜索') + ' "' + q + '"' }]);
      $('fmCrumbs').querySelectorAll('.fm-crumb').forEach(function (e) { e.classList.add('cur'); });
      renderBody();
    });
  }

  /* ───────── init ───────── */
  function init() {
    try { CFG = JSON.parse($('fmConfig').textContent); } catch (e) { console.error('fmConfig parse', e); return; }
    state.folderId = CFG.initial_folder_id || null;
    $('fmUploadPanel').hidden = true;   // 防残留空面板

    $('fmNavAll').addEventListener('click', function () { setNav('all'); });
    $('fmNavShared').addEventListener('click', function () { setNav('shared'); });
    $('fmNavTrash').addEventListener('click', function () { setNav('trash'); });
    $('fmNewFolderBtn').addEventListener('click', g.fmNewFolder);
    $('fmViewSeg').addEventListener('click', function (e) {
      var b = e.target.closest('button[data-view]'); if (!b) return;
      state.view = b.dataset.view;
      $('fmViewSeg').querySelectorAll('button').forEach(function (x) { x.classList.toggle('on', x.dataset.view === state.view); });
      renderBody();
    });
    $('fmUploadInput').addEventListener('change', function () { uploadFiles(this.files); this.value = ''; });
    $('fmFolderInput').addEventListener('change', function () { uploadFolder(this.files); this.value = ''; });
    $('fmNameOk').addEventListener('click', doName);
    $('fmNameInput').addEventListener('keydown', function (e) { if (e.key === 'Enter') doName(); });
    $('fmMoveOk').addEventListener('click', doMove);
    $('fmSearch').addEventListener('input', function () { clearTimeout(searchTimer); var q = this.value.trim(); searchTimer = setTimeout(function () { doSearch(q); }, 300); });
    document.addEventListener('click', function (e) { var m = $('fmCtxMenu'); if (!m.hidden && !m.contains(e.target)) m.hidden = true; });

    // 拖拽上传到主区
    var dz = $('fmDropZone');
    dz.addEventListener('dragover', function (e) { if (e.dataTransfer.types.indexOf('Files') >= 0) { e.preventDefault(); dz.classList.add('dragover'); } });
    dz.addEventListener('dragleave', function (e) { if (e.target === dz) dz.classList.remove('dragover'); });
    dz.addEventListener('drop', function (e) {
      if (e.dataTransfer.files && e.dataTransfer.files.length) { e.preventDefault(); dz.classList.remove('dragover'); if (state.nav === 'all') uploadFiles(e.dataTransfer.files); }
    });

    // 共享:人员选择 + 添加
    if (g.AtPeopleSelect) state.shareUsersCtl = AtPeopleSelect.init('fmShareUsers');
    $('fmShareAdd').addEventListener('click', function () {
      var uids = state.shareUsersCtl ? state.shareUsersCtl.getValue() : [];
      if (!uids.length) { toast(t('请选择用户'), 'error'); return; }
      send(API + '/folders/' + state.curShareFolder + '/shares', 'POST', { user_ids: uids, permission: $('fmSharePerm').value })
        .then(function (d) { if (d.success) { if (state.shareUsersCtl) state.shareUsersCtl.clear(); loadShares(state.curShareFolder); toast(t('已共享')); } else toast(d.message, 'error'); });
    });

    loadTree(function () { openFolder(state.folderId); });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})(window);
