/**
 * ATKpiDetail —— KPI 实际值下钻明细弹层
 *
 * 回答「绩效上这个数字是怎么来的」。搭配 components/at_kpi_detail_modal.html 使用。
 *
 *   ATKpiDetail.open({ userId, year, quarter, code, cellText })
 *
 * cellText(可选):用户刚点的那个单元格上显示的文本。传了会在合计旁边做一次校验 ——
 * 对不上就当场标红,不等 HR 来问。这是本组件存在的意义:让数字可被追溯,而不是可被怀疑。
 *
 * **对返回结构不做假设**:group 有 rows 就画两层,有 children 就再下一层。
 * 新增 KPI 下钻只需后端加 provider,本文件零改动。
 */
(function (w) {
  'use strict';

  var MODAL_ID = 'atKpiDetail';
  var $ = function (id) { return document.getElementById(id); };

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  // 数量:整数不带小数,小数最多 2 位(87 而不是 87.00;1.5 保留)
  function fmtQty(q) {
    var n = Number(q || 0);
    return Number.isInteger(n) ? String(n) : n.toFixed(2).replace(/\.?0+$/, '');
  }

  function rowsHtml(rows) {
    return (rows || []).map(function (r) {
      return '<div class="kd-row">'
        + '<span class="nm">' + esc(r.name) + '</span>'
        + (r.sub ? '<span class="mn">' + esc(r.sub) + '</span>' : '')
        + (r.qty != null ? '<span class="qt">×' + fmtQty(r.qty) + '</span>' : '')
        + '<span class="vl">' + esc(r.value_display) + '</span>'
        + '</div>';
    }).join('');
  }

  // 递归:children 里的每一项自己也可能带 rows(目前后端最深三层,结构上不限)
  function childrenHtml(children) {
    return (children || []).map(function (c) {
      return '<div class="kd-sub">' + esc(c.label)
        + (c.value_display ? ' · ' + esc(c.value_display) : '') + '</div>'
        + rowsHtml(c.rows)
        + (c.children ? childrenHtml(c.children) : '');
    }).join('');
  }

  var CHEV = '<svg class="kd-cr" width="12" height="12" viewBox="0 0 24 24" fill="none"'
    + ' stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
    + '<polyline points="9 18 15 12 9 6"></polyline></svg>';

  function groupsHtml(groups) {
    if (!groups || !groups.length) {
      return '<div class="at-dim" style="text-align:center;padding:34px 0;font-size:12.5px;">'
        + (w.__I18N_KPI_DETAIL_EMPTY || '本期无明细') + '</div>';
    }
    return groups.map(function (g) {
      return '<div class="kd-g">'
        + '<div class="kd-gh" onclick="this.parentNode.classList.toggle(\'on\')">'
        + CHEV
        + '<span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'
        + esc(g.label)
        + (g.sub ? ' <span class="mn" style="font-size:10.5px;color:var(--ink-4);">'
            + esc(g.sub) + '</span>' : '')
        + '</span>'
        + '<span class="kd-gv">' + esc(g.value_display) + '</span>'
        + '</div>'
        + '<div class="kd-body">'
        + (g.rows ? rowsHtml(g.rows) : '')
        + (g.children ? childrenHtml(g.children) : '')
        + '</div>'
        + '</div>';
    }).join('');
  }

  function render(d, cellText) {
    $(MODAL_ID + 'Title').textContent = d.title || '';
    $(MODAL_ID + 'Sub').textContent =
      [d.period, d.person].filter(Boolean).join(' · ');

    // 合计:at-serif 大字,与被点单元格逐位一致。后端自检发现口径分叉时会挂 mismatch。
    var warn = '';
    if (d.mismatch) {
      warn = '<span style="color:var(--danger,#c0392b);font-size:11px;">⚠ '
        + '明细合计与总额不一致,请报开发</span>';
    }
    // 数字与单位分离(表格里单位也是独立一列);再附原始金额,便于跟别处对账
    $(MODAL_ID + 'Total').innerHTML =
      '<span class="at-serif" style="font-size:26px;font-weight:500;letter-spacing:-0.01em;'
      + 'color:var(--ink);">' + esc(d.total_display) + '</span>'
      + (d.unit ? '<span class="at-dim" style="font-size:12px;">' + esc(d.unit) + '</span>' : '')
      + '<span class="at-dim" style="font-size:11.5px;">' + esc(d.meta || '')
      + (d.total_raw_display ? ' · ' + esc(d.total_raw_display) : '') + '</span>'
      + warn;

    // 跨实例合并:合计含对端(SG)部分,但下面只能列本端明细 —— 必须讲清楚,
    // 否则「合计 1490 / 明细加起来 930」会被当成数字有错。
    var pb = $(MODAL_ID + 'Peer');
    if (d.has_peer) {
      pb.style.display = 'flex';
      pb.innerHTML =
        '<span>' + (w.__I18N_KPI_LOCAL || '本端明细') + ' <b style="color:var(--ink);">'
        + esc(d.local_display) + '</b></span>'
        + '<span style="color:var(--ink-4);">+</span>'
        + '<span>' + (w.__I18N_KPI_PEER || '对端合并') + ' <b style="color:var(--ink);">'
        + esc(d.peer_display) + '</b>'
        + (d.peer_note ? ' <span style="color:var(--ink-4);">· ' + esc(d.peer_note) + '</span>' : '')
        + '</span>';
    } else {
      pb.style.display = 'none';
      pb.innerHTML = '';
    }

    $(MODAL_ID + 'Body').innerHTML = groupsHtml(d.groups);
    $(MODAL_ID + 'Basis').textContent = d.basis || '';
  }

  var API = {
    open: function (o) {
      var el = $(MODAL_ID);
      if (!el) { console.warn('[ATKpiDetail] 未 include at_kpi_detail_modal'); return; }
      el.style.display = 'flex';
      $(MODAL_ID + 'Title').textContent = '';
      $(MODAL_ID + 'Sub').textContent = '';
      $(MODAL_ID + 'Total').innerHTML = '';
      $(MODAL_ID + 'Basis').textContent = '';
      $(MODAL_ID + 'Body').innerHTML =
        '<div class="at-dim" style="text-align:center;padding:34px 0;font-size:12.5px;">…</div>';

      var url = '/performance/config/api/user/' + o.userId
        + '/actual-detail/' + o.year + '/' + o.quarter
        + '?code=' + encodeURIComponent(o.code);
      fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(function (r) { return r.json(); })
        .then(function (j) {
          if (!j.success) throw new Error(j.message || 'failed');
          render(j.data, o.cellText);
        })
        .catch(function (e) {
          $(MODAL_ID + 'Body').innerHTML =
            '<div class="at-dim" style="text-align:center;padding:34px 0;font-size:12.5px;">'
            + esc(e.message || '加载失败') + '</div>';
        });
    },
    close: function () {
      var el = $(MODAL_ID);
      if (el) el.style.display = 'none';
    }
  };

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') API.close();
  });

  w.ATKpiDetail = API;
})(window);
