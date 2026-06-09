/**
 * AT 客户订单创建表单控制器
 *
 * 依赖:ATItemTable / ATToast / ATProductPicker
 *
 * 页面入口:
 *   atOpenSoCreate()        打开模态(清空字段)
 *   atSubmitSoCreate()      提交到 POST /sales-order/api/create-direct
 *   atUpdateSoSubmitBtn()   校验按钮可点性(客户 + 至少 1 明细)
 */
(function () {
  // 读客户值:优先 ATSearchableSelect(combobox),fallback 到 native <select>
  function _getCustomerId() {
    if (window.ATSearchableSelect) {
      const v = ATSearchableSelect.getValue('atSoCustomer');
      if (v) return v;
    }
    const el = document.getElementById('atSoCustomer');
    return el ? el.value : '';
  }

  function atUpdateSoSubmitBtn() {
    const btn = document.getElementById('atSoSubmitBtn');
    if (!btn) return;
    const hasCustomer = !!_getCustomerId();
    const hasItems = window.ATItemTable && !ATItemTable.isEmpty();
    const ok = hasCustomer && hasItems;
    btn.disabled = !ok;
    btn.style.opacity = ok ? '1' : '0.5';
    btn.style.cursor = ok ? 'pointer' : 'not-allowed';
  }
  window.atUpdateSoSubmitBtn = atUpdateSoSubmitBtn;

  function atOpenSoCreate() {
    // 客户:清空 combobox
    if (window.ATSearchableSelect) ATSearchableSelect.setValue('atSoCustomer', '');
    // 重置其他下拉(货币例外:保留模板里的默认 selected,不重置)
    ['atSoIncoterm','atSoShipping','atSoFreight'].forEach(id => {
      const el = document.getElementById(id); if (el) el.selectedIndex = 0;
    });
    ['atSoContact','atSoPhone','atSoEmail','atSoAddress','atSoNote'].forEach(id => {
      const el = document.getElementById(id); if (el) el.value = '';
    });
    // 默认期望交付 = 今天 + 14 天
    const d = new Date(); d.setDate(d.getDate() + 14);
    const dd = document.getElementById('atSoDeliveryDate');
    if (dd) dd.value = d.toISOString().slice(0, 10);
    // 货币:不在 JS 强制覆写,使用模板渲染时的 default selected

    if (window.ATItemTable) ATItemTable.clear();
    atUpdateSoSubmitBtn();
    document.getElementById('atSoCreateModal').style.display = 'flex';
  }
  window.atOpenSoCreate = atOpenSoCreate;

  function atSubmitSoCreate() {
    const get = id => { const el = document.getElementById(id); return el ? el.value : ''; };
    const customerId = _getCustomerId();
    const deliveryDate = get('atSoDeliveryDate');
    if (!customerId) { ATToast.warn('无法创建订单', '请选择客户'); return; }
    if (!ATItemTable || ATItemTable.isEmpty()) {
      ATToast.warn('无法创建订单', '请至少添加一个产品');
      return;
    }

    const items = ATItemTable.getItems();
    const body = {
      customer_id:       parseInt(customerId),
      delivery_date:     deliveryDate,
      delivery_address:  get('atSoAddress'),
      delivery_contact:  get('atSoContact'),
      delivery_phone:    get('atSoPhone'),
      delivery_email:    get('atSoEmail'),
      shipping_method:   get('atSoShipping'),
      freight_terms:     get('atSoFreight'),
      incoterms:         get('atSoIncoterm'),
      notes:             get('atSoNote'),
      currency:          get('atSoCurrency') || 'CNY',
      details:           items.map(it => ({
        product_id:    it.product_id,
        product_name:  it.name,
        product_model: it.model || '',
        quantity:      parseInt(it.qty) || 0,
        unit:          it.unit || '套',
        // 单价 = 市场价 × 折扣率 / 100 — 已在前端算好
        unit_price:    parseFloat(it.price) || 0,
        market_price:  parseFloat(it.marketPrice != null ? it.marketPrice : it.price) || 0,
        // 折扣率:前端 0-100,转换成 0-1 给后端(后端 schema 是 Numeric(5,4))
        discount:      it.discount != null ? (parseFloat(it.discount) / 100) : 1.0,
      })),
    };

    const btn = document.getElementById('atSoSubmitBtn');
    btn.disabled = true; btn.style.opacity = '0.5'; btn.style.cursor = 'wait';
    const csrf = document.querySelector('meta[name="csrf-token"]')?.content || '';
    fetch('/sales-order/api/create-direct', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
      body: JSON.stringify(body),
    })
      .then(r => r.json())
      .then(res => {
        if (res.success) {
          document.getElementById('atSoCreateModal').style.display = 'none';
          ATToast.success('客户订单已创建', res.order_number || '');
          setTimeout(() => location.reload(), 800);
        } else {
          ATToast.error('创建失败', res.message || '');
          btn.disabled = false; btn.style.opacity = '1'; btn.style.cursor = 'pointer';
        }
      })
      .catch(err => {
        ATToast.error('创建失败', String(err));
        btn.disabled = false; btn.style.opacity = '1'; btn.style.cursor = 'pointer';
      });
  }
  window.atSubmitSoCreate = atSubmitSoCreate;
})();
