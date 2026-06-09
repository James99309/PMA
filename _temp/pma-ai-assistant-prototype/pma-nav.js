/**
 * PMA · 全局导航条
 * 注入到每个 HTML 页面的 <body> 顶部,位于 .hdr 之内的右上角。
 * 通过 data-pma-page 属性识别当前页,高亮对应 tab。
 */
(function () {
  const PAGES = [
    { id: 'app',     label: '总览',   href: 'PMA App.html' },
    { id: 'lists',   label: '列表',   href: 'PMA Unified Lists.html' },
    { id: 'customers', label: '客户', href: 'PMA Customers.html' },
    { id: 'forms',   label: '新建',   href: 'PMA New Forms.html' },
    { id: 'cardscan', label: '名片',  href: 'PMA Card Scan.html' },
    { id: 'filter',  label: '筛选',   href: 'PMA Filter.html' },
    { id: 'chat',    label: '聊天',   href: 'PMA Chat.html' },
    { id: 'expense', label: '报销',   href: 'PMA Expense.html' },
    { id: 'quotation', label: '报价单', href: 'PMA Quotation.html' },
    { id: 'task',    label: '任务',   href: 'PMA Task.html' },
    { id: 'calendar', label: '日历',   href: 'PMA Calendar.html' },
    { id: 'profile', label: '我的',   href: 'PMA Profile.html' },
    { id: 'splash',  label: '启动+登录', href: 'PMA Splash Login.html' },
  ];

  function currentId() {
    const meta = document.documentElement.getAttribute('data-pma-page')
      || document.body.getAttribute('data-pma-page');
    if (meta) return meta;
    // fallback: detect from filename
    const f = decodeURIComponent(location.pathname.split('/').pop() || '');
    if (/Splash/i.test(f))  return 'splash';
    if (/Profile/i.test(f)) return 'profile';
    if (/Expense/i.test(f)) return 'expense';
    if (/Task/i.test(f))    return 'task';
    if (/Calendar/i.test(f)) return 'calendar';
    if (/Chat/i.test(f))    return 'chat';
    if (/Filter/i.test(f))  return 'filter';
    if (/Forms/i.test(f))   return 'forms';
    if (/Card.?Scan/i.test(f)) return 'cardscan';
    if (/Unified/i.test(f) || /Lists/i.test(f)) return 'lists';
    return 'app';
  }

  function inject() {
    if (document.getElementById('pma-global-nav')) return;
    const here = currentId();

    const bar = document.createElement('nav');
    bar.id = 'pma-global-nav';
    bar.innerHTML = `
      <style>
        #pma-global-nav {
          position: sticky; top: 0; z-index: 1000;
          display: flex; align-items: center; gap: 0;
          padding: 10px 20px; min-height: 44px;
          background: #0E0E0E;
          border-bottom: 1px solid rgba(255,255,255,0.08);
          font-family: -apple-system, "PingFang SC", "SF Pro", system-ui, sans-serif;
          backdrop-filter: blur(12px);
          -webkit-backdrop-filter: blur(12px);
        }
        #pma-global-nav .pma-brand {
          font-size: 12px; font-weight: 700; letter-spacing: 1.5px;
          color: rgba(255,255,255,0.85); padding-right: 18px;
          margin-right: 4px;
          border-right: 1px solid rgba(255,255,255,0.12);
        }
        #pma-global-nav .pma-brand .dot {
          display: inline-block; width: 6px; height: 6px; border-radius: 50%;
          background: #D97757; margin-right: 8px; vertical-align: middle;
          margin-bottom: 1px;
        }
        #pma-global-nav .pma-tabs {
          display: flex; gap: 2px; flex: 1; overflow-x: auto;
          scrollbar-width: none;
        }
        #pma-global-nav .pma-tabs::-webkit-scrollbar { display: none; }
        #pma-global-nav a {
          display: inline-flex; align-items: center; gap: 6px;
          padding: 6px 12px; border-radius: 999px;
          font-size: 13px; font-weight: 500; letter-spacing: 0.2px;
          color: rgba(255,255,255,0.55);
          text-decoration: none; white-space: nowrap;
          transition: color 0.15s, background 0.15s;
        }
        #pma-global-nav a:hover {
          color: rgba(255,255,255,0.95);
          background: rgba(255,255,255,0.06);
        }
        #pma-global-nav a.active {
          color: #1A1A1A;
          background: #F2EFEA;
          font-weight: 600;
        }
        #pma-global-nav .pma-meta {
          font-size: 11px; color: rgba(255,255,255,0.35);
          letter-spacing: 0.4px; padding-left: 12px;
          flex-shrink: 0;
        }
        @media (max-width: 720px) {
          #pma-global-nav .pma-meta { display: none; }
          #pma-global-nav .pma-brand { padding-right: 10px; margin-right: 0; }
        }
      </style>
      <div class="pma-brand"><span class="dot"></span>PMA</div>
      <div class="pma-tabs">
        ${PAGES.map(p => `<a href="${p.href}" class="${p.id === here ? 'active' : ''}" data-id="${p.id}">${p.label}</a>`).join('')}
      </div>
      <div class="pma-meta">EVERTAC · 和源通信</div>
    `;

    document.body.insertBefore(bar, document.body.firstChild);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inject);
  } else {
    inject();
  }
})();
