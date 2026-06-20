/**
 * AT 联系人表单 modal 控制(暂只 edit)
 * ──────────────────────────────────────────────────
 * 配对模板:components/at_contact_modal.html
 *
 * 全局 API:
 *   atOpenContactForm('edit', contactId)
 *   atSubmitContactForm('edit', modalId)
 *
 * 后端:
 *   POST /customer/api/contacts/<id>/edit
 *   GET  /customer/contacts/<id>            (HTML 详情;数据本身由页面已有)
 *   ↳ 没有专门 GET JSON,所以编辑态预填靠 caller 通过 data-* 注入
 */
(function (g) {
  'use strict';
  var State = {};
  function $(id) { return document.getElementById(id); }
  function prefixFor(modalId) { return modalId + '__'; }

  /**
   * 打开联系人 modal
   * @param {string} mode      'edit' | 'create'
   * @param {object} opts      edit: { contactId, ...initialFields }
   *                            create: { companyId }
   */
  g.atOpenContactForm = function (mode, opts) {
    opts = opts || {};
    var modalId = (mode === 'edit') ? 'atEditContactModal' : 'atCreateContactModal';
    var modal = $(modalId);
    if (!modal) { console.error('[at-contact-form] modal not found:', modalId); return; }
    var p = prefixFor(modalId);

    State[modalId] = { mode: mode, contactId: opts.contactId, companyId: opts.companyId };
    modal.dataset.contactId = String(opts.contactId || '');
    modal.dataset.companyId = String(opts.companyId || '');

    // 字段预填(edit 时 caller 传入,create 时全空)
    $(p + 'name').value       = opts.name || '';
    $(p + 'department').value  = opts.department || '';
    $(p + 'position').value    = opts.position || '';
    $(p + 'phone').value       = opts.phone || '';
    $(p + 'email').value       = opts.email || '';
    $(p + 'notes').value       = opts.notes || '';
    $(p + 'isPrimary').checked = !!opts.is_primary;

    modal.style.display = 'flex';
    setTimeout(function () { $(p + 'name') && $(p + 'name').focus(); }, 80);
  };

  g.atSubmitContactForm = async function (mode, modalId) {
    var p = prefixFor(modalId);
    var name = ($(p + 'name').value || '').trim();
    if (!name) { ATToast.warn('无法保存', '请填写联系人姓名'); return; }

    var body = {
      name:       name,
      department: ($(p + 'department').value || '').trim(),
      position:   ($(p + 'position').value || '').trim(),
      phone:      ($(p + 'phone').value || '').trim(),
      email:      ($(p + 'email').value || '').trim(),
      notes:      ($(p + 'notes').value || '').trim(),
      is_primary: $(p + 'isPrimary').checked
    };

    var btn = $(modalId + '_submit');
    var oldHtml = btn.innerHTML;
    btn.disabled = true; btn.innerHTML = (mode === 'edit') ? '保存中…' : '创建中…';

    var url;
    if (mode === 'edit') {
      var contactId = $(modalId).dataset.contactId;
      url = '/customer/api/contacts/' + contactId + '/edit';
    } else {
      var companyId = $(modalId).dataset.companyId;
      url = '/customer/api/' + companyId + '/add_contact';
    }
    try {
      var csrf = (document.querySelector('meta[name="csrf-token"]') || {}).content || '';
      var resp = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
        body: JSON.stringify(body)
      });
      var res = await resp.json();
      if (!res.success) {
        ATToast.error(res.message || '保存失败');
        btn.disabled = false; btn.innerHTML = oldHtml;
        return;
      }
      ATToast.success(mode === 'edit' ? '已保存' : '已创建', '刷新中…');
      setTimeout(function () { location.reload(); }, 400);
    } catch (e) {
      ATToast.error('网络错误,请重试');
      btn.disabled = false; btn.innerHTML = oldHtml;
    }
  };
})(window);
