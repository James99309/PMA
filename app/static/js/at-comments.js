/**
 * AT 通用评论组件 — 聊天气泡布局(自己右/他人左,头像+时间在气泡底,hover 删除)
 * 工作项弹窗与日报弹窗共用一套。
 *
 * 用法:
 *   var c = AtComments.bind({
 *     listEl, inputEl, sendEl,
 *     currentUserId,
 *     threadUrl: function(key){ return '/.../'+key+'/comments'; },  // GET 列表 + POST 新增
 *     deleteUrl: function(commentId){ return '/.../comments/'+commentId; }  // POST 删除
 *   });
 *   c.open(key);   // 切换上下文(工作项 id / 日报日期)并加载
 */
(function (g) {
  'use strict';
  var t = (typeof g.t === 'function') ? g.t : function (s) { return s; };
  // 头像调色板(与 at_avatar 宏一致:idx=(名字长度+1)%6) → 同一人全站同色
  var AV_PALETTE = ['#D97757', '#2A5F8F', '#2F7155', '#7A5AE0', '#B8742E', '#A23B3B'];
  function avColor(name) { return AV_PALETTE[((name || '?').length + 1) % AV_PALETTE.length]; }
  function csrf() { return (document.querySelector('meta[name="csrf-token"]') || {}).content || ''; }
  function toast(m, ty) { if (g.ATToast) ATToast[ty || 'success'](m); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]; }); }

  function bind(cfg) {
    var key = null;

    function render(list) {
      var box = cfg.listEl;
      if (!list || !list.length) { box.innerHTML = '<div class="at-dim" style="font-size:12px;">' + t('暂无评论') + '</div>'; return; }
      box.innerHTML = '';
      list.forEach(function (c) {
        var own = String(c.owner_id) === String(cfg.currentUserId);
        var nm = c.owner_name || '?';
        var row = document.createElement('div'); row.className = 'wc-row ' + (own ? 'own' : 'other');
        var av = document.createElement('div'); av.className = 'wc-av'; av.textContent = nm.charAt(0); av.title = nm;
        av.style.background = avColor(nm); av.style.color = '#fff';
        var bubble = document.createElement('div'); bubble.className = 'wc-bubble';
        var text = document.createElement('div'); text.className = 'wc-text';
        if (window.ATRichNote) { text.classList.add('arn-view'); text.innerHTML = ATRichNote.render(c.content); }
        else text.textContent = c.content;
        var foot = document.createElement('div'); foot.className = 'wc-foot';
        foot.innerHTML = '<span class="wc-time">' + esc(c.created_at || '') + '</span>';
        if (c.can_delete) {
          var x = document.createElement('button'); x.type = 'button'; x.className = 'wc-del'; x.textContent = '×'; x.title = t('删除');
          x.addEventListener('click', function () {
            fetch(cfg.deleteUrl(c.id), { method: 'POST', headers: { 'X-CSRFToken': csrf() } })
              .then(function (r) { return r.json(); })
              .then(function (d) { if (d.success) load(); else toast(d.message || t('删除失败'), 'error'); });
          });
          foot.appendChild(x);
        }
        bubble.appendChild(text); bubble.appendChild(foot);
        row.appendChild(av); row.appendChild(bubble); box.appendChild(row);
      });
    }

    function load() {
      if (key == null || key === '') { render([]); return; }
      fetch(cfg.threadUrl(key), { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(function (r) { return r.json(); })
        .then(function (d) { render(d.comments || []); })
        .catch(function () { render([]); });
    }

    function appendOptimistic(content) {
      // 乐观渲染:发送瞬间先上屏一个半透明气泡,服务端返回后由 load() 对齐替换
      var box = cfg.listEl;
      var ph = box.querySelector('.at-dim');
      if (ph && box.children.length === 1) box.innerHTML = '';
      var nm = cfg.currentUserName || t('我');
      var row = document.createElement('div'); row.className = 'wc-row own'; row.style.opacity = '0.5';
      var av = document.createElement('div'); av.className = 'wc-av'; av.textContent = nm.charAt(0); av.title = nm;
      av.style.background = avColor(nm); av.style.color = '#fff';
      var bubble = document.createElement('div'); bubble.className = 'wc-bubble';
      var text = document.createElement('div'); text.className = 'wc-text';
      if (window.ATRichNote) { text.classList.add('arn-view'); text.innerHTML = ATRichNote.render(content); }
      else text.textContent = content;
      bubble.appendChild(text); row.appendChild(av); row.appendChild(bubble); box.appendChild(row);
      box.scrollTop = box.scrollHeight;
    }

    function post() {
      if (key == null || key === '') return;
      var content = (cfg.inputEl.value || '').trim();
      if (!content) { toast(t('评论不能为空'), 'error'); return; }
      cfg.sendEl.disabled = true;
      appendOptimistic(content);          // 立即上屏
      cfg.inputEl.value = '';
      if (cfg.inputEl._arnCtl) cfg.inputEl._arnCtl.refresh();   // 富文本编辑器同步清空
      fetch(cfg.threadUrl(key), {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() },
        body: JSON.stringify({ content: content })
      }).then(function (r) { return r.json(); })
        .then(function (d) { cfg.sendEl.disabled = false; if (!d.success) toast(d.message || t('评论失败'), 'error'); load(); })
        .catch(function () { cfg.sendEl.disabled = false; toast(t('评论失败'), 'error'); load(); });
    }

    cfg.sendEl.addEventListener('click', post);
    cfg.inputEl.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); post(); }
    });

    return {
      open: function (k) { key = (k == null ? null : String(k)); load(); },
      reload: load
    };
  }

  g.AtComments = { bind: bind };
})(window);
