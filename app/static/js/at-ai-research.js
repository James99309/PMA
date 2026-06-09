/**
 * AT AI 调研 — 触发 + 轮询 + 原地展开
 * ──────────────────────────────────────────────
 * 配对模板宏: components/at_detail.html → at_ai_research_card
 *
 * 工作流:
 *   [data-at-ai-trigger]  → POST data-ai-retry-url(触发)
 *                         → 立即更新状态 → 启动轮询
 *   [data-at-ai-toggle]   → fetch + 渲染展开
 *   页面加载时:状态已是 running → 自动启动轮询
 *   轮询命中 completed:自动展开 + 渲染数据 + 停止轮询
 */
(function () {
  'use strict';

  var POLL_INTERVAL = 4000;
  var BTN_LABELS = {
    none: '触发调研', completed: '重新调研', error: '重试调研',
    pre_searching: '调研中…', researching: '调研中…', needs_input: '选择候选'
  };
  var BADGE = {
    completed: { text: '已完成', bg: 'var(--success-soft)', fg: 'var(--success)' },
    pre_searching: { text: '进行中', bg: 'var(--warn-soft)', fg: 'var(--warn)' },
    researching: { text: '进行中', bg: 'var(--warn-soft)', fg: 'var(--warn)' },
    error: { text: '出错', bg: 'var(--danger-soft)', fg: 'var(--danger)' },
    needs_input: { text: '待确认', bg: 'var(--info-soft, #e6f0fa)', fg: 'var(--info, #2563eb)' }
  };
  var pollers = new WeakMap();

  function csrf() {
    var m = document.querySelector('meta[name="csrf-token"]');
    return m ? m.content : '';
  }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g,
      function (c) { return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c]; });
  }
  function $sec(el) { return el.closest('[data-ai-research]'); }
  function $q(sec, sel) { return sec.querySelector(sel); }

  /* ============== 状态机渲染 ============== */
  function applyState(section, status, data, updatedAt, errorMsg) {
    status = status || 'none';
    section.dataset.aiStatus = status;

    // 徽章
    var badge = $q(section, '[data-at-ai-badge]');
    if (badge) {
      var b = BADGE[status];
      if (b) {
        badge.textContent = b.text;
        badge.style.background = b.bg;
        badge.style.color = b.fg;
        badge.style.display = 'inline-block';
      } else {
        badge.style.display = 'none';
      }
    }

    // 触发按钮 + 文案 + disabled
    var trig = $q(section, '[data-at-ai-trigger]');
    var lbl = trig && trig.querySelector('[data-at-ai-label]');
    var isRun = (status === 'pre_searching' || status === 'researching');
    if (trig) {
      trig.disabled = isRun || (status === 'needs_input' && section.dataset.aiViewUrl);
      if (lbl) lbl.textContent = BTN_LABELS[status] || '触发调研';
    }

    // toggle 按钮
    var tgl = $q(section, '[data-at-ai-toggle]');
    if (tgl) tgl.style.display = (status === 'completed') ? 'inline-flex' : 'none';

    // 上次调研时间
    var upd = $q(section, '[data-at-ai-updated]');
    if (upd) {
      if (updatedAt) {
        upd.textContent = '上次调研:' + formatTime(updatedAt);
        upd.style.display = 'block';
      } else if (!upd.textContent.trim()) {
        upd.style.display = 'none';
      }
    }

    // 出错时的提示(toast)
    if (status === 'error' && errorMsg && window.ATToast) {
      ATToast.error('调研失败', errorMsg);
    }

    // 候选确认 — 暂时不在卡内做候选选择 UI,把按钮变成跳转链接
    if (status === 'needs_input') {
      var viewUrl = section.dataset.aiViewUrl;
      if (viewUrl && !$q(section, '[data-at-ai-candidates-link]')) {
        var a = document.createElement('a');
        a.dataset.atAiCandidatesLink = '';
        a.href = viewUrl;
        a.textContent = '选择候选 →';
        a.style.cssText = 'font-size:12px;color:var(--accent);text-decoration:none;margin-left:6px;';
        trig.parentNode.insertBefore(a, trig.nextSibling);
      }
    } else {
      var link = $q(section, '[data-at-ai-candidates-link]');
      if (link) link.remove();
    }

    // 完成态:自动渲染 + 自动展开
    if (status === 'completed' && data) {
      renderDetail(section, data);
      openDetail(section);
    }
  }

  function formatTime(iso) {
    try {
      var d = new Date(iso);
      if (isNaN(d.getTime())) return iso;
      var pad = function (n) { return n < 10 ? '0' + n : '' + n; };
      return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()) +
             ' ' + pad(d.getHours()) + ':' + pad(d.getMinutes());
    } catch (e) { return iso; }
  }

  /* ============== 触发调研 ============== */
  async function trigger(btn) {
    var section = $sec(btn);
    if (!section) return;
    var url = section.dataset.aiRetryUrl;
    if (!url) return;

    applyState(section, 'researching');
    try {
      var resp = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrf(),
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: '{}'
      });
      var data = await resp.json().catch(function () { return {}; });
      if (!resp.ok || data.success === false) {
        if (window.ATToast) ATToast.error(data.message || '触发失败');
        applyState(section, section.dataset.aiStatus === 'researching' ? 'error' : section.dataset.aiStatus);
        return;
      }
      if (window.ATToast) ATToast.success('已触发调研', '后台执行中,请稍候…');
      startPolling(section);
    } catch (e) {
      if (window.ATToast) ATToast.error('网络错误,请重试');
      applyState(section, 'error');
    }
  }

  /* ============== 轮询 ============== */
  function startPolling(section) {
    stopPolling(section);
    var id = setInterval(function () { pollOnce(section); }, POLL_INTERVAL);
    pollers.set(section, id);
    pollOnce(section); // 立即触发一次
  }
  function stopPolling(section) {
    var id = pollers.get(section);
    if (id) { clearInterval(id); pollers.delete(section); }
  }
  async function pollOnce(section) {
    var url = section.dataset.aiFetchUrl;
    if (!url) { stopPolling(section); return; }
    try {
      var resp = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
      var json = await resp.json();
      var payload = (json && json.data) || json || {};
      var status = payload.status || 'none';
      var data = payload.research_data || payload.data || null;
      var updated = payload.updated_at;
      var errMsg = payload.error;
      applyState(section, status, data, updated, errMsg);
      if (status !== 'pre_searching' && status !== 'researching') {
        stopPolling(section);
      }
    } catch (e) {
      // 网络抖动忽略,下一次再试
    }
  }

  /* ============== 展开 / 收起 ============== */
  async function toggleDetail(btn) {
    var section = $sec(btn);
    if (!section) return;
    var panel = $q(section, '[data-at-ai-detail]');
    if (!panel) return;
    if (panel.style.display !== 'none') {
      closeDetail(section);
    } else {
      openDetail(section);
      if (panel.dataset.loaded !== '1') await fetchAndRender(section);
    }
  }
  function openDetail(section) {
    var panel = $q(section, '[data-at-ai-detail]');
    var lbl = $q(section, '[data-at-ai-toggle-label]');
    if (panel) panel.style.display = 'block';
    if (lbl) lbl.textContent = '收起';
  }
  function closeDetail(section) {
    var panel = $q(section, '[data-at-ai-detail]');
    var lbl = $q(section, '[data-at-ai-toggle-label]');
    if (panel) panel.style.display = 'none';
    if (lbl) lbl.textContent = '查看详情';
  }
  async function fetchAndRender(section) {
    var panel = $q(section, '[data-at-ai-detail]');
    var body = $q(section, '[data-at-ai-detail-body]');
    try {
      var resp = await fetch(section.dataset.aiFetchUrl, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      var json = await resp.json();
      var payload = (json && json.data) || json || {};
      renderDetail(section, payload.research_data || payload.data || {});
    } catch (e) {
      if (body) body.innerHTML = '<div style="color:var(--danger);padding:8px 0;">加载失败:' + esc(e.message || '') + '</div>';
    }
  }
  function renderDetail(section, researchData) {
    var body = $q(section, '[data-at-ai-detail-body]');
    var panel = $q(section, '[data-at-ai-detail]');
    if (!body || !panel) return;
    var entityType = section.dataset.aiResearch;
    var html = entityType === 'customer' ? renderCustomer(researchData) : renderProject(researchData);
    body.innerHTML = html || '<div style="color:var(--ink-4);padding:8px 0;">暂无调研数据</div>';
    panel.dataset.loaded = '1';
  }

  /* ============== Renderer:客户 ============== */
  function renderCustomer(d) {
    if (!d || (typeof d === 'object' && !Object.keys(d).length)) return '';
    var out = '';

    if (d.company_profile) {
      var p = d.company_profile;
      var kvs = [];
      if (p.positioning) out += block('公司概况',
        '<p style="margin:0 0 8px;font-weight:500;color:var(--ink);">' + esc(p.positioning) + '</p>');
      if (p.founded) kvs.push(kv('成立', p.founded));
      if (p.headquarters) kvs.push(kv('总部', p.headquarters));
      if (p.revenue) kvs.push(kv('营收', p.revenue));
      if (p.strategy) kvs.push(kv('战略方向', p.strategy));
      if (kvs.length) out += kvGrid(kvs);
      if (p.main_business && p.main_business.length) {
        out += '<div style="margin-top:8px;display:flex;flex-wrap:wrap;gap:4px;">' +
          p.main_business.map(function (b) {
            return '<span style="font-size:11px;padding:2px 8px;border-radius:10px;background:var(--accent-tint);color:var(--accent);">' +
              esc(b) + '</span>';
          }).join('') + '</div>';
      }
    }

    if (d.executives && d.executives.length) {
      out += block('关键人物 · ' + d.executives.length,
        d.executives.map(function (e) {
          return '<div style="display:flex;gap:8px;padding:6px 0;border-bottom:1px solid var(--line-soft);">' +
            '<div style="flex:1;min-width:0;">' +
              '<div><span style="font-weight:500;color:var(--ink);">' + esc(e.name || '—') + '</span>' +
                (e.title ? '<span style="color:var(--ink-4);margin-left:6px;font-size:11.5px;">' + esc(e.title) + '</span>' : '') +
                (e.risk_tag ? '<span style="margin-left:6px;font-size:10.5px;padding:1px 5px;border-radius:3px;background:var(--danger-soft);color:var(--danger);">' + esc(e.risk_tag) + '</span>' : '') +
              '</div>' +
              (e.background ? '<div style="color:var(--ink-3);font-size:11.5px;margin-top:2px;">' + esc(e.background) + '</div>' : '') +
            '</div>' +
          '</div>';
        }).join(''));
    }

    if (d.active_projects && d.active_projects.length) {
      out += block('在建项目 · ' + d.active_projects.length,
        d.active_projects.map(function (proj) {
          return '<div style="padding:6px 0;border-bottom:1px solid var(--line-soft);">' +
            '<div style="display:flex;justify-content:space-between;gap:8px;">' +
              '<span style="font-weight:500;color:var(--ink);">' + esc(proj.name || '—') + '</span>' +
              (proj.amount ? '<span class="at-mono" style="color:var(--success);font-size:11.5px;">' + esc(proj.amount) + '</span>' : '') +
            '</div>' +
            (proj.detail ? '<div style="color:var(--ink-3);font-size:11.5px;margin-top:2px;">' + esc(proj.detail) + '</div>' : '') +
            (proj.partner || proj.status ? '<div style="color:var(--ink-4);font-size:11px;margin-top:2px;">' +
              (proj.partner ? '合作:' + esc(proj.partner) : '') +
              (proj.partner && proj.status ? ' · ' : '') +
              (proj.status ? esc(proj.status) : '') +
            '</div>' : '') +
          '</div>';
        }).join(''));
    }

    if (d.risk_alerts && d.risk_alerts.length) {
      out += block('风险预警 · ' + d.risk_alerts.length,
        d.risk_alerts.map(function (a) {
          var color = a.level === 'high' ? 'var(--danger)' : (a.level === 'medium' ? 'var(--warn)' : 'var(--ink-3)');
          return '<div style="display:flex;gap:6px;padding:4px 0;">' +
            '<span style="flex-shrink:0;width:5px;height:5px;border-radius:50%;background:' + color + ';margin-top:7px;"></span>' +
            '<div style="flex:1;"><div>' + esc(a.content || '') + '</div>' +
              (a.date ? '<div style="color:var(--ink-4);font-size:11px;">' + esc(a.date) + '</div>' : '') +
            '</div></div>';
        }).join(''));
    }

    if (d.partners && d.partners.length) {
      out += block('合作伙伴',
        '<div style="display:flex;flex-wrap:wrap;gap:4px;">' +
        d.partners.map(function (p) {
          return '<span style="font-size:11px;padding:2px 8px;border-radius:10px;background:var(--bg-page);color:var(--ink-2);border:1px solid var(--line);">' +
            esc(typeof p === 'string' ? p : (p.name || '')) + '</span>';
        }).join('') + '</div>');
    }

    return out;
  }

  /* ============== Renderer:项目 ============== */
  function renderProject(d) {
    if (!d || (typeof d === 'object' && !Object.keys(d).length)) return '';
    var out = '';

    if (d.project_overview) {
      var p = d.project_overview;
      if (p.description) out += block('项目概况',
        '<p style="margin:0;color:var(--ink-2);">' + esc(p.description) + '</p>');
      var kvs = [];
      if (p.total_investment) kvs.push(kv('总投资', p.total_investment, 'var(--success)'));
      if (p.total_area) kvs.push(kv('总建面', p.total_area, 'var(--info, #2563eb)'));
      if (p.land_area) kvs.push(kv('占地面积', p.land_area));
      if (p.start_date) kvs.push(kv('开工时间', p.start_date));
      if (p.completion_date) kvs.push(kv('竣工时间', p.completion_date));
      if (p.project_phase) kvs.push(kv('项目阶段', p.project_phase));
      if (p.city) kvs.push(kv('城市', p.city));
      if (p.address) kvs.push(kv('地址', p.address));
      if (kvs.length) out += kvGrid(kvs);
    }

    if (d.stakeholders) {
      var s = d.stakeholders;
      var rows = [];
      if (s.investor) rows.push(stakeholderRow('业主 / 投资方', s.investor,
        [s.investor_legal_rep && '法人:' + s.investor_legal_rep,
         s.investor_address, s.investor_contact].filter(Boolean)));
      if (s.general_contractor) rows.push(stakeholderRow('总包', s.general_contractor, []));
      if (s.design_institute) rows.push(stakeholderRow('设计院', s.design_institute, []));
      if (s.smart_systems_consultant) rows.push(stakeholderRow('智能化顾问', s.smart_systems_consultant, []));
      if (s.smart_systems_integrator) rows.push(stakeholderRow('智能化集成商', s.smart_systems_integrator, []));
      if (s.consultant) rows.push(stakeholderRow('顾问', s.consultant, []));
      if (s.operator) rows.push(stakeholderRow('运营方', s.operator, s.operator_contact ? [s.operator_contact] : []));
      if (rows.length) out += block('参与方', rows.join(''));

      if (s.key_contacts && s.key_contacts.length) {
        out += block('关键联系人',
          s.key_contacts.map(function (kc) {
            return '<div style="display:flex;gap:8px;padding:4px 0;border-bottom:1px solid var(--line-soft);font-size:12px;">' +
              '<span style="font-weight:500;color:var(--ink);">' + esc(kc.name || '—') + '</span>' +
              (kc.role ? '<span style="color:var(--ink-4);">' + esc(kc.role) + '</span>' : '') +
              (kc.contact ? '<span style="color:var(--accent);margin-left:auto;">' + esc(kc.contact) + '</span>' : '') +
            '</div>';
          }).join(''));
      }
    }

    return out;
  }

  /* ============== 渲染工具 ============== */
  function block(title, inner) {
    return '<div style="margin-bottom:14px;">' +
      '<div style="font-size:11px;letter-spacing:0.06em;color:var(--ink-4);text-transform:uppercase;margin-bottom:6px;">' +
        esc(title) + '</div>' + inner + '</div>';
  }
  function kv(label, value, color) {
    return '<div style="display:flex;justify-content:space-between;gap:8px;padding:3px 0;font-size:12px;">' +
      '<span style="color:var(--ink-4);">' + esc(label) + '</span>' +
      '<span class="at-mono" style="color:' + (color || 'var(--ink)') + ';text-align:right;">' + esc(value) + '</span>' +
    '</div>';
  }
  function kvGrid(items) {
    return '<div style="display:grid;grid-template-columns:1fr;border-top:1px solid var(--line-soft);margin-top:6px;">' +
      items.join('') + '</div>';
  }
  function stakeholderRow(role, name, sub) {
    return '<div style="padding:6px 0;border-bottom:1px solid var(--line-soft);">' +
      '<div style="display:flex;gap:8px;align-items:baseline;">' +
        '<span style="font-size:10.5px;color:var(--ink-4);min-width:64px;">' + esc(role) + '</span>' +
        '<span style="font-weight:500;color:var(--ink);">' + esc(name) + '</span>' +
      '</div>' +
      (sub.length ? '<div style="color:var(--ink-3);font-size:11px;margin-top:2px;margin-left:72px;">' +
        sub.map(esc).join(' · ') + '</div>' : '') +
    '</div>';
  }

  /* ============== 入口:事件 + 初始化轮询 ============== */
  document.addEventListener('click', function (ev) {
    var trig = ev.target.closest('[data-at-ai-trigger]');
    if (trig && !trig.disabled) { ev.preventDefault(); trigger(trig); return; }
    var tgl = ev.target.closest('[data-at-ai-toggle]');
    if (tgl) { ev.preventDefault(); toggleDetail(tgl); }
  });

  // 进入页面:状态是 running 时自动启动轮询
  function bootstrap() {
    document.querySelectorAll('[data-ai-research]').forEach(function (section) {
      var st = section.dataset.aiStatus;
      if (st === 'pre_searching' || st === 'researching') {
        startPolling(section);
      }
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrap);
  } else {
    bootstrap();
  }
})();
