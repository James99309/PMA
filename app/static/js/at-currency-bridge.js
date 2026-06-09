/**
 * AT 货币桥(ATCurrencyBridge) — 通用的"货币 ↔ 明细价"联动组件
 *
 * 解决:订单/报价单等模态里有自己的"货币" select(SO 用 atSoCurrency,
 * PO 可类似),但 ATItemTable 内置一个 atItCurrency select。两者要联动:
 *   - 外部 select 变 → ATItemTable.setCurrency() 同步符号 + 批量刷明细价
 *   - 已有明细 → 调用 /api/products/prices-batch 取目标货币价,无价 toast 提示
 *   - 隐藏 ATItemTable 内置的 atItCurrency select(避免双货币 UI)
 *   - ATProductPicker 打开时透传当前货币 → 显示对应货币价,无价产品禁选
 *
 * 用法(任何模块):
 *   <select id="atSoCurrency">...
 *   <button onclick="ATProductPicker.open({ currency: ATCurrencyBridge.getCurrency() })">
 *
 *   ATCurrencyBridge.bind({
 *     selectId: 'atSoCurrency',     // 外部货币 select 的 id(必填)
 *     hideInnerSelect: true,        // 是否隐藏 ATItemTable 内置 select(默认 true)
 *     onChange: (newCur) => {...},  // 可选,变化时额外触发(如 atUpdateSoSubmitBtn)
 *   });
 *
 *   // ATProductPicker.open 时:
 *   ATProductPicker.open({
 *     currency: ATCurrencyBridge.getCurrency(),
 *     onPick: (p) => ATItemTable.addItem(p),
 *   });
 *
 * 依赖:ATItemTable / ATToast(/api/products/prices-batch)
 */
(function (window) {
  'use strict';

  const State = {
    selectId: null,
    onChange: null,
    bound: false,
  };

  function getSelect() {
    return State.selectId ? document.getElementById(State.selectId) : null;
  }

  function getCurrency() {
    const sel = getSelect();
    return (sel && sel.value) ? sel.value.toUpperCase() : 'CNY';
  }

  function setCurrency(code) {
    const sel = getSelect();
    if (sel) {
      sel.value = code;
      // 派发 change 触发联动
      sel.dispatchEvent(new Event('change', { bubbles: true }));
    }
  }

  /**
   * 当外部货币 select 变化时,刷新 ATItemTable 内每个产品的价格
   *  - 调用 /api/products/prices-batch 批量取目标货币价
   *  - 无价产品:price 置 0 + toast warn
   *  - 完成后 ATItemTable.setItems() 重渲染
   */
  function refresh(newCurrency) {
    if (!newCurrency) newCurrency = getCurrency();

    // 1) 同步 ATItemTable 货币符号(无论是否有明细,合计金额也得跟着变)
    if (window.ATItemTable && ATItemTable.setCurrency) {
      ATItemTable.setCurrency(newCurrency);
    }

    // 2) 已有明细 → 批量刷价
    if (!window.ATItemTable || ATItemTable.isEmpty()) return;
    const items = ATItemTable.getItems();
    const ids = items.map(it => it.product_id).filter(Boolean);
    if (!ids.length) return;

    const csrf = document.querySelector('meta[name="csrf-token"]')?.content || '';
    fetch(`/api/products/prices-batch?ids=${ids.join(',')}&currency=${encodeURIComponent(newCurrency)}`, {
      headers: { 'X-CSRFToken': csrf }
    })
      .then(r => r.json())
      .then(res => {
        if (!res.success) {
          (window.ATToast || console).error?.('价格刷新失败', res.message || '');
          return;
        }
        const prices = res.prices || {};
        const noPrice = [];
        items.forEach(it => {
          const pid = String(it.product_id);
          const entry = prices[pid];
          if (entry && entry.price != null) {
            it.price = entry.price;
          } else {
            it.price = 0;
            noPrice.push(it.name || it.product_id);
          }
        });
        ATItemTable.setItems(items);
        if (noPrice.length && window.ATToast) {
          ATToast.warn(`${noPrice.length} 项产品在 ${newCurrency} 下无价格`,
                       noPrice.slice(0, 3).join(' / ') + (noPrice.length > 3 ? '…' : ''));
        } else if (window.ATToast) {
          ATToast.success('价格已按 ' + newCurrency + ' 刷新');
        }
        if (typeof State.onChange === 'function') {
          try { State.onChange(newCurrency); } catch (e) { console.error(e); }
        }
      })
      .catch(err => {
        if (window.ATToast) ATToast.error('价格刷新失败', String(err));
      });
  }

  /**
   * 隐藏 ATItemTable 内置的 atItCurrency select + "货币"标签
   * (避免外部已有 select 时出现两个货币选择器)
   */
  function _hideInnerSelect() {
    const inner = document.getElementById('atItCurrency');
    if (!inner) return;
    const wrapper = inner.closest('div[style*="display:inline-flex"]') || inner.parentElement;
    if (wrapper) wrapper.style.display = 'none';
    // 隐藏前面的"货币"label
    if (wrapper && wrapper.previousElementSibling && wrapper.previousElementSibling.tagName === 'SPAN') {
      wrapper.previousElementSibling.style.display = 'none';
    }
  }

  /**
   * 主入口:绑定外部货币 select 到 ATItemTable / 价格联动
   * 可重复调用,bind 多次以兼容同页面多个模态(自动覆盖前一次)
   */
  function bind(opts) {
    opts = opts || {};
    State.selectId = opts.selectId || null;
    State.onChange = (typeof opts.onChange === 'function') ? opts.onChange : null;

    if (!State.selectId) {
      console.warn('[ATCurrencyBridge] selectId 必填');
      return;
    }

    // 隐藏内置(默认 true,只隐藏一次)
    if (opts.hideInnerSelect !== false) {
      _hideInnerSelect();
    }

    // 初始同步货币给 ATItemTable
    if (window.ATItemTable && ATItemTable.setCurrency) {
      ATItemTable.setCurrency(getCurrency());
    }

    // 监听外部 select 变化(全局监听一次即可,通过 selectId 路由)
    if (!State.bound) {
      document.addEventListener('change', (e) => {
        if (e.target && e.target.id === State.selectId) {
          refresh(e.target.value);
        }
      });
      State.bound = true;
    }
  }

  window.ATCurrencyBridge = {
    bind,
    getCurrency,
    setCurrency,
    refresh,
  };
})(window);
