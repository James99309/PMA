/**
 * AT 组合输入框:前半分组下拉选择 + 后半文本输入(可复用)
 * 配套 templates/components/at_grouped_select.html
 *
 *   var ctl = AtGroupedSelect.init('wiTitleInput');
 *   ctl.getWorkType() / getContent() / getTitle() / setValue(type, fullTitle) / focus()
 */
(function (g) {
  'use strict';
  function init(rootId) {
    var root = typeof rootId === 'string' ? document.getElementById(rootId) : rootId;
    if (!root) return null;
    var trigger = root.querySelector('[data-gsi-trigger]');
    var labelEl = root.querySelector('[data-gsi-label]');
    var input = root.querySelector('[data-gsi-input]');
    var menu = root.querySelector('[data-gsi-menu]');
    var labels = {};
    try { labels = JSON.parse(root.dataset.labels || '{}'); } catch (e) {}
    var selected = '';
    var placeholderLabel = labelEl ? labelEl.textContent : '请选择';

    function refreshLabel() { labelEl.textContent = labels[selected] || placeholderLabel; }
    function open() { menu.hidden = false; }
    function close() { menu.hidden = true; }

    trigger.addEventListener('click', function (e) { e.stopPropagation(); menu.hidden ? open() : close(); });
    menu.querySelectorAll('[data-gsi-val]').forEach(function (el) {
      el.addEventListener('click', function () {
        selected = el.dataset.gsiVal; refreshLabel(); close(); input.focus();
        if (api._onChange) api._onChange(selected);
      });
    });
    document.addEventListener('click', function (e) { if (!root.contains(e.target)) close(); });

    var api = {
      getWorkType: function () { return selected; },
      getContent: function () { return input.value.trim(); },
      getTitle: function () {
        var label = labels[selected] || '';
        var c = input.value.trim();
        if (!label) return c;
        return c ? (label + '-' + c) : (label + '-');
      },
      setValue: function (type, fullTitle) {
        selected = type || '';
        refreshLabel();
        var label = labels[selected] || '';
        var content = fullTitle || '';
        if (label && content.indexOf(label + '-') === 0) content = content.slice((label + '-').length);
        else if (label && content === label) content = '';
        input.value = content;
      },
      onChange: function (fn) { api._onChange = fn; return api; },
      focus: function () { input.focus(); }
    };
    root._atgs = api;
    return api;
  }
  g.AtGroupedSelect = { init: init };
})(window);
