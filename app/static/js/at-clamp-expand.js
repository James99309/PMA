/*
 * at-clamp-expand.js — 可复用「点击展开/收起」
 * 给被 -webkit-line-clamp 截断的文本元素加 class="at-expandable",
 * 本脚本仅在内容【真的溢出】时,在其后插入一个「展开/收起」按钮;点击切换完整显示。
 * 幂等:重复引入/重复 scan 安全。隐藏(display:none)的元素测不出溢出,
 * 内容变可见后(如切 tab/筛选)再调 window.ATClampExpand.scan() 补扫即可。
 */
(function () {
  if (window.ATClampExpand) return;

  // 注入样式(一次)
  var st = document.createElement('style');
  st.textContent =
    '.at-expandable--open{-webkit-line-clamp:unset !important;max-height:none !important;overflow:visible !important;}' +
    '.at-expand-toggle{display:block;width:100%;text-align:right;margin-top:2px;' +
    'background:none;border:0;padding:0;cursor:pointer;color:var(--ink-4);line-height:1;}' +
    '.at-expand-toggle:hover{color:var(--ink-2);}' +
    '.at-expand-toggle svg{transition:transform 160ms;vertical-align:middle;}' +
    '.at-expand-toggle.at-expand-toggle--open svg{transform:rotate(180deg);}';
  document.head.appendChild(st);

  var CHEVRON = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"' +
                ' stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9l6 6 6-6"/></svg>';

  function wire(el) {
    if (el.dataset.clampWired) return;
    // 截断态下 scrollHeight 明显大于 clientHeight 才算溢出
    if (el.scrollHeight - el.clientHeight < 3) return;
    el.dataset.clampWired = '1';

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'at-expand-toggle';
    btn.setAttribute('aria-label', el.getAttribute('data-expand-label') || '展开/收起');
    btn.innerHTML = CHEVRON;       // 向下箭头,右对齐;展开后 CSS 翻转向上
    btn.addEventListener('click', function (e) {
      e.stopPropagation();   // 行可点击时不误触发跳转
      e.preventDefault();
      var open = el.classList.toggle('at-expandable--open');
      btn.classList.toggle('at-expand-toggle--open', open);
    });
    el.insertAdjacentElement('afterend', btn);
  }

  function scan(root) {
    (root || document).querySelectorAll('.at-expandable').forEach(wire);
  }

  window.ATClampExpand = { scan: scan, wire: wire };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { scan(); });
  } else {
    scan();
  }
})();
