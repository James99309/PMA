/**
 * favorite-star.js — 通用「关注」星标(个人书签)
 *
 * 用法(模板):用 components/at_favorite.html 的 at_fav_star() 宏渲染,
 *            或手写 <button data-fav-toggle data-fav-type="project" data-fav-id="12"
 *                          data-fav-on="1|0"> …星标 svg… </button>
 * 行为:事件委托(整页一个监听,兼容列表分页/局部刷新后新出现的星标),
 *      乐观更新 → 失败回滚 + toast。行内星标会 stopPropagation,
 *      避免连带触发外层「整行点击跳详情」。
 */
(function () {
  'use strict';

  var t = window.t || function (s) { return s; };

  function paint(btn, on) {
    btn.dataset.favOn = on ? '1' : '0';
    var svg = btn.querySelector('svg');
    if (svg) {
      svg.setAttribute('fill', on ? 'currentColor' : 'none');
    }
    btn.style.color = on ? 'var(--warn, #d98f3d)' : 'var(--ink-4, #9a978f)';
    btn.setAttribute('aria-pressed', on ? 'true' : 'false');
    btn.setAttribute('title', on ? t('取消关注') : t('关注'));
    var label = btn.querySelector('[data-fav-label]');
    if (label) label.textContent = on ? t('已关注') : t('关注');
  }

  function toggle(btn) {
    if (btn.dataset.favBusy === '1') return;
    var was = btn.dataset.favOn === '1';
    btn.dataset.favBusy = '1';
    paint(btn, !was);                       // 乐观更新

    var meta = document.querySelector('meta[name="csrf-token"]');
    fetch('/api/favorites/toggle', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': meta ? meta.getAttribute('content') : '',
      },
      body: JSON.stringify({
        object_type: btn.dataset.favType,
        object_id: parseInt(btn.dataset.favId, 10),
      }),
    })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (d) {
        if (!d || !d.success) throw new Error((d && d.message) || t('操作失败，请重试'));
        paint(btn, !!d.favorited);          // 以服务端为准
      })
      .catch(function (e) {
        paint(btn, was);                    // 回滚
        if (window.ATToast) ATToast.error(e.message || t('操作失败，请重试'));
      })
      .finally(function () { btn.dataset.favBusy = '0'; });
  }

  // 必须用捕获阶段(第三参 true):列表行的跳转是 <tr onclick="location.href=…"> 内联处理器,
  // 冒泡时它先于 document 监听执行 → 在冒泡阶段 stopPropagation 已经晚了,点星会跳走详情页。
  // 捕获阶段在事件下行时就拦下并 stopPropagation,行的 onclick 根本不会触发。
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-fav-toggle]');
    if (!btn) return;
    e.preventDefault();
    e.stopPropagation();
    toggle(btn);
  }, true);
})();
