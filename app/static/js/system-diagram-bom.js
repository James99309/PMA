/**
 * PMA 系统图 — BOM提取 & 报价单生成
 * 前置校验、BOM预览、创建报价单
 * 依赖: system-diagram-core.js, system-diagram-topology.js
 */

// ====== HTML ESCAPE ======
function _escHtml(s){if(!s)return'';const d=document.createElement('div');d.textContent=s;return d.innerHTML;}

// ====== FIXED PRODUCT IDS (待用户提供后填入) ======
const BOM_CONFIG = {
  connectorHalfInch: null,     // 1/2" 连接器 Product ID
  patchPanel24Port: null,       // 24口光纤配线架 Product ID
  patchPanel4Port: null,        // 4口光纤配线架 Product ID
  rfJumperDefault: null,        // 射频跳线默认 Product ID
  antennaConnectorQtyMultiplier: 5  // 每个天线的连接器数量
};

// ====== CABLE CATEGORIES ======
const CABLE_CATEGORY_MAP = {
  coax_half: 'coax', coax_78: 'coax', coax_114: 'coax', coax_flex: 'coax',
  fiber_single: 'fiber', fiber_multi: 'fiber', fiber_armored: 'fiber',
  signal_rf: 'rf'
};

// ====== VALIDATION ======
function validateDiagramForBOM() {
  const problems = { unconnected: [], untyped: [], valid: true };
  const connectedNodeIds = new Set();
  edges.forEach(e => { connectedNodeIds.add(e.sourceId); connectedNodeIds.add(e.targetId); });

  nodes.forEach(n => {
    if (n.is_riser_node || n.subcategoryId === null) return; // skip risers and text notes
    // Check connections
    if (!connectedNodeIds.has(n.id)) {
      problems.unconnected.push(n.id);
    }
    // Check product selection
    if (!n.selectedProductId) {
      problems.untyped.push(n.id);
    }
  });

  problems.valid = problems.unconnected.length === 0 && problems.untyped.length === 0;
  return problems;
}

function highlightProblems(problems) {
  // Clear previous highlights
  clearBOMHighlights();

  const nodesLayer = document.getElementById('nodesLayer');
  if (!nodesLayer) return;

  const allProblems = [...problems.unconnected, ...problems.untyped];
  allProblems.forEach(nodeId => {
    const n = nodes.find(x => x.id === nodeId);
    if (!n) return;
    const isUnconnected = problems.unconnected.includes(nodeId);
    const color = isUnconnected ? '#ef4444' : '#f59e0b';

    // Add highlight rect
    const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    rect.setAttribute('x', n.x - 4);
    rect.setAttribute('y', n.y - 4);
    rect.setAttribute('width', (n.w || 64) + 8);
    rect.setAttribute('height', (n.h || 64) + 8);
    rect.setAttribute('rx', '6');
    rect.setAttribute('fill', 'none');
    rect.setAttribute('stroke', color);
    rect.setAttribute('stroke-width', '3');
    rect.setAttribute('class', 'bom-highlight');
    rect.style.animation = 'bomPulse 1s ease-in-out infinite';
    nodesLayer.appendChild(rect);
  });

  // Show summary toast
  const parts = [];
  if (problems.unconnected.length) parts.push(`${problems.unconnected.length} ${_t('个未连线设备')}`);
  if (problems.untyped.length) parts.push(`${problems.untyped.length} ${_t('个未选型设备')}`);
  showToast('⚠ ' + parts.join('、') + '，' + _t('请修复后重试'));
}

function clearBOMHighlights() {
  document.querySelectorAll('.bom-highlight').forEach(el => el.remove());
}

// ====== BOM EXTRACTION (frontend logic) ======
function extractBOMData() {
  const sections = [];
  // Use live global variables (from floorplan.js and core.js)
  const fpList = (typeof floorPlans !== 'undefined') ? floorPlans : [];
  const buildingsData = (typeof buildings !== 'undefined') ? buildings : [];
  const topoAreasData = (typeof topoAreas !== 'undefined') ? topoAreas : [];

  // Build floor → building map
  const floorBuildingMap = {}; // floor_id → building
  const buildingMap = {};      // building_id → building
  buildingsData.forEach(b => { buildingMap[b.id] = b; });
  // Floor plans have building_id field
  fpList.forEach(fp => {
    if (fp.building_id && buildingMap[fp.building_id]) {
      floorBuildingMap[fp.id] = buildingMap[fp.building_id];
    }
  });

  // Identify central_room area node IDs
  const centralRoomAreas = topoAreasData.filter(a => a.area_type === 'central_room');
  const roomNodeIds = new Set();
  centralRoomAreas.forEach(area => {
    nodes.forEach(n => {
      const cx = n.x + (n.w || 64) / 2, cy = n.y + (n.h || 64) / 2;
      if (cx >= area.x && cx <= area.x + area.width && cy >= area.y && cy <= area.y + area.height) {
        roomNodeIds.add(n.id);
      }
    });
  });

  // Classify nodes
  const roomNodes = [];    // Control room nodes
  const buildingNodes = {}; // building_id → node[]
  const looseNodes = [];    // Nodes without building

  nodes.forEach(n => {
    if (n.is_riser_node || n.subcategoryId === null) return;
    if (roomNodeIds.has(n.id)) {
      roomNodes.push(n);
    } else if (n.floor_id) {
      const bld = floorBuildingMap[n.floor_id];
      if (bld) {
        if (!buildingNodes[bld.id]) buildingNodes[bld.id] = [];
        buildingNodes[bld.id].push(n);
      } else {
        looseNodes.push(n);
      }
    } else {
      // topology-only, not in room → treat as room device
      roomNodes.push(n);
    }
  });

  // Classify edges by endpoint location
  const roomEdges = [], fiberEdges = [];
  const buildingEdges = {}; // building_id → edge[]

  edges.forEach(e => {
    const cat = CABLE_CATEGORY_MAP[e.cableType] || null;
    if (cat === 'fiber') {
      fiberEdges.push(e);
    } else if (cat === 'rf') {
      roomEdges.push(e); // RF jumpers belong to control room
    } else {
      // Coax: belongs to the building of source or target node
      const srcN = nodes.find(x => x.id === e.sourceId);
      const tgtN = nodes.find(x => x.id === e.targetId);
      let assignedBldId = null;
      for (const nd of [srcN, tgtN]) {
        if (nd && nd.floor_id) {
          const bld = floorBuildingMap[nd.floor_id];
          if (bld) { assignedBldId = bld.id; break; }
        }
      }
      if (assignedBldId) {
        if (!buildingEdges[assignedBldId]) buildingEdges[assignedBldId] = [];
        buildingEdges[assignedBldId].push(e);
      } else {
        roomEdges.push(e);
      }
    }
  });

  // Helper: aggregate node items by product
  function aggregateNodes(nodeList) {
    const map = {};
    nodeList.forEach(n => {
      const pid = n.selectedProductId || 0;
      const key = pid || `sub_${n.subcategoryId}_${n.name}`;
      if (!map[key]) {
        const prod = pid ? PRODUCTS.find(p => p.id === pid) : null;
        map[key] = {
          product_id: pid || null,
          name: prod ? prod.productName : _nodeDisplayName(n),
          model: prod ? prod.model : (n.model || ''),
          mn: prod ? prod.mn : '',
          qty: 0,
          price: prod ? (prod.retailPrice || 0) : 0,
          auto: false
        };
      }
      map[key].qty += (n.qty || 1);
    });
    return Object.values(map);
  }

  // Helper: aggregate cable items
  function aggregateCables(edgeList) {
    const map = {};
    edgeList.forEach(e => {
      let key;
      if (e.selectedProductId) {
        key = `prod_${e.selectedProductId}`;
        if (!map[key]) {
          map[key] = {
            product_id: e.selectedProductId,
            type: e.cableType,
            name: e.selectedProductName || '',
            model: e.selectedProductModel || '',
            mn: e.selectedProductMn || '',
            count: 0,
            color: CABLE_TYPES[e.cableType] ? CABLE_TYPES[e.cableType].color : '#94a3b8'
          };
        }
      } else {
        key = `type_${e.cableType}`;
        if (!map[key]) {
          const ct = CABLE_TYPES[e.cableType];
          map[key] = {
            product_id: null,
            type: e.cableType,
            name: ct ? _m(ct.name) : _t('未知线缆'),
            model: '',
            mn: '',
            count: 0,
            color: ct ? ct.color : '#94a3b8'
          };
        }
      }
      map[key].count += 1;
    });
    return Object.values(map);
  }

  // Count antennas per building
  function countAntennas(nodeList) {
    let count = 0;
    nodeList.forEach(n => {
      const sub = SUBCATEGORIES[n.subcategoryId];
      if (sub) {
        const sname = (sub.name || '').toLowerCase();
        if (sname.includes('天线') || sname.includes('antenna')) {
          count += (n.qty || 1);
        }
      }
    });
    return count;
  }

  // Count remote repeaters (直放站远端)
  function countRemotes(nodeList) {
    let count = 0;
    nodeList.forEach(n => {
      const sub = SUBCATEGORIES[n.subcategoryId];
      if (sub) {
        const sname = (sub.name || '').toLowerCase();
        if (sname.includes('远端') || sname.includes('remote') || sname.includes('oru')) {
          count += (n.qty || 1);
        }
      }
    });
    return count;
  }

  // Section 1: Control Room
  const roomItems = aggregateNodes(roomNodes);
  const roomCables = aggregateCables(roomEdges);
  // Auto-add 24-port patch panel to control room
  if (BOM_CONFIG.patchPanel24Port) {
    roomItems.push({ product_id: BOM_CONFIG.patchPanel24Port, name: _t('24口光纤配线架'), model: '', mn: '', qty: 1, price: 0, auto: true, autoNote: _t('自动添加') });
  } else {
    roomItems.push({ product_id: null, name: _t('24口光纤配线架'), model: '', mn: '', qty: 1, price: 0, auto: true, autoNote: _t('自动添加'), needConfig: true });
  }

  sections.push({
    name: _t('控制机房'),
    building_id: null,
    icon: 'memory',
    items: roomItems,
    cables: roomCables,
    connectors: []
  });

  // Section 2+: Buildings (sorted by sort_order)
  const sortedBuildings = Object.keys(buildingNodes)
    .map(bId => buildingMap[bId])
    .filter(Boolean)
    .sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));

  sortedBuildings.forEach(bld => {
    const bNodes = buildingNodes[bld.id] || [];
    const bItems = aggregateNodes(bNodes);
    const bCables = aggregateCables(buildingEdges[bld.id] || []);
    const antennaCount = countAntennas(bNodes);

    const connectors = [];
    // Auto-add 4-port patch panels per remote repeater in this building
    const remoteCount = countRemotes(bNodes);
    if (remoteCount > 0) {
      if (BOM_CONFIG.patchPanel4Port) {
        bItems.push({ product_id: BOM_CONFIG.patchPanel4Port, name: _t('4口光纤配线架'), model: '', mn: '', qty: remoteCount, price: 0, auto: true, autoNote: `${_t('直放站远端')}×${remoteCount}` });
      } else {
        bItems.push({ product_id: null, name: _t('4口光纤配线架'), model: '', mn: '', qty: remoteCount, price: 0, auto: true, autoNote: `${_t('直放站远端')}×${remoteCount}`, needConfig: true });
      }
    }
    // Auto-add connectors per antenna
    if (antennaCount > 0) {
      const connQty = antennaCount * BOM_CONFIG.antennaConnectorQtyMultiplier;
      if (BOM_CONFIG.connectorHalfInch) {
        connectors.push({ product_id: BOM_CONFIG.connectorHalfInch, name: _t('1/2" 连接器'), qty: connQty, auto: true, autoNote: `${_t('天线')}${antennaCount}×${BOM_CONFIG.antennaConnectorQtyMultiplier}` });
      } else {
        connectors.push({ product_id: null, name: _t('1/2" 连接器'), qty: connQty, auto: true, autoNote: `${_t('天线')}${antennaCount}×${BOM_CONFIG.antennaConnectorQtyMultiplier}`, needConfig: true });
      }
    }

    sections.push({
      name: bld.name || bld.label || `Building ${bld.id}`,
      building_id: bld.id,
      icon: 'apartment',
      items: bItems,
      cables: bCables,
      connectors: connectors
    });
  });

  // Loose nodes (no building)
  if (looseNodes.length) {
    sections.push({
      name: _t('独立楼层设备'),
      building_id: null,
      icon: 'layers',
      items: aggregateNodes(looseNodes),
      cables: [],
      connectors: []
    });
  }

  // Final section: Fiber (independent)
  if (fiberEdges.length) {
    sections.push({
      name: _t('光纤'),
      building_id: null,
      icon: 'cable',
      is_fiber_section: true,
      items: [],
      cables: aggregateCables(fiberEdges),
      connectors: []
    });
  }

  return sections;
}

// ====== BOM PREVIEW MODAL ======
let _bomSections = [];

function openBOMPreview() {
  // First save if unsaved
  if (hasUnsavedChanges) {
    showToast(_t('请先保存系统图'));
    return;
  }
  if (!DIAGRAM_CONFIG.diagramId) {
    showToast(_t('请先保存系统图'));
    return;
  }
  if (!DIAGRAM_CONFIG.projectId) {
    showToast(_t('该系统图未关联项目，无法生成报价单'));
    return;
  }

  // Validate
  clearBOMHighlights();
  const problems = validateDiagramForBOM();
  if (!problems.valid) {
    highlightProblems(problems);
    return;
  }

  // Extract BOM data
  _bomSections = extractBOMData();

  // Render preview modal
  renderBOMPreview(_bomSections);
  document.getElementById('bomPreviewModal').classList.remove('hidden');
  document.getElementById('bomPreviewModal').style.display = 'flex';
}

function closeBOMPreview() {
  const modal = document.getElementById('bomPreviewModal');
  if (modal) {
    modal.classList.add('hidden');
    modal.style.display = '';
  }
}

function renderBOMPreview(sections) {
  const content = document.getElementById('bomPreviewContent');
  if (!content) return;

  let totalItems = 0;
  let html = '';

  sections.forEach((sec, si) => {
    const allItems = [...(sec.items || []), ...(sec.connectors || []), ...(sec.cables || [])];
    const sectionCount = allItems.length;
    totalItems += sectionCount;

    html += `<div class="mb-6">`;
    // Section header
    html += `<div class="flex items-center gap-2 px-4 py-3 bg-slate-100 dark:bg-slate-800 rounded-t-lg border border-slate-200 dark:border-slate-700">
      <span class="material-symbols-outlined text-lg">${sec.icon || 'category'}</span>
      <span class="font-semibold text-slate-900 dark:text-white">${_escHtml(sec.name)}</span>
      ${sec.is_fiber_section ? '<span class="text-xs px-2 py-0.5 rounded bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400">' + _t('光纤') + '</span>' : ''}
      <span class="text-sm text-slate-500 dark:text-slate-400 ml-auto">${sectionCount} ${_t('项')}</span>
    </div>`;

    if (sectionCount === 0) {
      html += `<div class="border border-t-0 border-slate-200 dark:border-slate-700 rounded-b-lg p-4 text-center text-sm text-slate-400">${_t('无设备')}</div>`;
      html += `</div>`;
      return;
    }

    // Table
    html += `<table class="w-full border-collapse border border-t-0 border-slate-200 dark:border-slate-700 rounded-b-lg overflow-hidden">
      <thead><tr class="bg-slate-50 dark:bg-slate-800/50">
        <th class="w-10 p-3 text-center"><input type="checkbox" checked onchange="toggleSectionChecks(${si},this.checked)"></th>
        <th class="p-3 text-left text-sm font-semibold text-slate-700 dark:text-slate-300">${_t('产品名称')}</th>
        <th class="p-3 text-left text-sm font-semibold text-slate-700 dark:text-slate-300">${_t('型号')}</th>
        <th class="p-3 text-right text-sm font-semibold text-slate-700 dark:text-slate-300 w-24">${_t('数量')}</th>
        <th class="p-3 text-center text-sm font-semibold text-slate-700 dark:text-slate-300 w-28">${_t('备注')}</th>
      </tr></thead><tbody class="text-sm text-slate-700 dark:text-slate-300">`;

    // Device items
    (sec.items || []).forEach((item, ii) => {
      const rowClass = item.auto ? 'bg-blue-50/50 dark:bg-blue-900/10' : '';
      const prefix = item.auto ? `<span class="text-slate-400 mr-1">└</span>` : '';
      const autoTag = item.auto ? `<span class="ml-2 text-xs px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">${_t('自动')}</span>` : '';
      const warnIcon = item.needConfig ? `<span class="ml-1 text-amber-500" title="${_t('未配置产品ID')}">⚠</span>` : '';
      html += `<tr class="${rowClass} border-b border-slate-100 dark:border-slate-800">
        <td class="p-3 text-center"><input type="checkbox" checked data-section="${si}" data-type="item" data-index="${ii}"></td>
        <td class="p-3">${prefix}${_escHtml(item.name)}${autoTag}${warnIcon}</td>
        <td class="p-3 text-slate-500">${_escHtml(item.model || item.mn) || '—'}</td>
        <td class="p-3 text-right"><input type="number" value="${item.qty}" min="1" class="w-16 text-right border border-slate-200 dark:border-slate-600 rounded px-2 py-1 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-sm" data-section="${si}" data-type="item" data-index="${ii}" onchange="updateBOMQty(this)"></td>
        <td class="p-3 text-center text-xs text-slate-400">${_escHtml(item.autoNote || sec.name)}</td>
      </tr>`;
    });

    // Connectors
    (sec.connectors || []).forEach((conn, ci) => {
      const warnIcon = conn.needConfig ? `<span class="ml-1 text-amber-500" title="${_t('未配置产品ID')}">⚠</span>` : '';
      html += `<tr class="bg-blue-50/50 dark:bg-blue-900/10 border-b border-slate-100 dark:border-slate-800">
        <td class="p-3 text-center"><input type="checkbox" checked data-section="${si}" data-type="connector" data-index="${ci}"></td>
        <td class="p-3"><span class="text-slate-400 mr-1">└</span>${_escHtml(conn.name)}<span class="ml-2 text-xs px-1.5 py-0.5 rounded bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">${_t('自动')}</span>${warnIcon}</td>
        <td class="p-3 text-slate-500">—</td>
        <td class="p-3 text-right">${conn.qty}</td>
        <td class="p-3 text-center text-xs text-slate-400">${conn.autoNote || ''}</td>
      </tr>`;
    });

    // Cables
    (sec.cables || []).forEach((cable, ki) => {
      const safeColor = (cable.color||'').replace(/[^a-zA-Z0-9#(),.\s%-]/g,'');
      const colorDot = `<span class="inline-block w-3 h-0.5 mr-2 rounded" style="background:${safeColor}"></span>`;
      const noProduct = !cable.product_id;
      const warnIcon = noProduct ? `<span class="ml-1 text-amber-500" title="${_t('未关联产品')}">⚠</span>` : '';
      html += `<tr class="border-b border-slate-100 dark:border-slate-800">
        <td class="p-3 text-center"><input type="checkbox" checked data-section="${si}" data-type="cable" data-index="${ki}"></td>
        <td class="p-3">${colorDot}${_escHtml(cable.name)}${warnIcon}</td>
        <td class="p-3 text-slate-500">${_escHtml(cable.model || cable.mn) || '—'}</td>
        <td class="p-3 text-right">${cable.count} ${_t('段')}</td>
        <td class="p-3 text-center text-xs text-slate-400">${_escHtml(sec.name)}</td>
      </tr>`;
    });

    html += `</tbody></table></div>`;
  });

  // Summary footer
  html += `<div class="flex items-center justify-between px-4 py-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200 dark:border-slate-700">
    <span class="text-sm text-slate-500 dark:text-slate-400">${_t('总计')}: <b class="text-slate-900 dark:text-white">${totalItems}</b> ${_t('项')}</span>
  </div>`;

  content.innerHTML = html;
}

function toggleSectionChecks(sectionIndex, checked) {
  document.querySelectorAll(`#bomPreviewContent input[type="checkbox"][data-section="${sectionIndex}"]`).forEach(cb => cb.checked = checked);
}

function updateBOMQty(input) {
  const si = parseInt(input.dataset.section);
  const type = input.dataset.type;
  const idx = parseInt(input.dataset.index);
  const val = parseInt(input.value) || 1;
  if (_bomSections[si] && type === 'item' && _bomSections[si].items[idx]) {
    _bomSections[si].items[idx].qty = val;
  }
}

// ====== CREATE QUOTATION ======
async function createQuotationFromBOM() {
  if (!DIAGRAM_CONFIG.projectId) {
    showToast(_t('该系统图未关联项目'));
    return;
  }

  // Collect checked items
  const details = [];
  const checkboxes = document.querySelectorAll('#bomPreviewContent input[type="checkbox"][data-section]');

  checkboxes.forEach(cb => {
    if (!cb.checked) return;
    const si = parseInt(cb.dataset.section);
    const type = cb.dataset.type;
    const idx = parseInt(cb.dataset.index);
    const sec = _bomSections[si];
    if (!sec) return;

    let item;
    if (type === 'item') item = sec.items[idx];
    else if (type === 'connector') item = sec.connectors[idx];
    else if (type === 'cable') item = sec.cables[idx];
    if (!item) return;

    const qty = type === 'cable' ? (item.count || 1) : (item.qty || 1);
    // Get qty from editable input if item type
    if (type === 'item') {
      const qtyInput = document.querySelector(`#bomPreviewContent input[type="number"][data-section="${si}"][data-type="item"][data-index="${idx}"]`);
      if (qtyInput) item.qty = parseInt(qtyInput.value) || 1;
    }

    const detail = {
      product_name: item.name || _t('未知产品'),
      product_model: item.model || '',
      product_mn: item.mn || '',
      brand: '',
      unit: type === 'cable' ? _t('段') : _t('套'),
      quantity: type === 'cable' ? item.count : (item.qty || 1),
      market_price: item.price || 0,
      unit_price: item.price || 0,
      discount_rate: 100,
      total_price: (item.price || 0) * (type === 'cable' ? item.count : (item.qty || 1)),
      product_desc: sec.name // Building name as note
    };
    details.push(detail);
  });

  if (!details.length) {
    showToast(_t('请至少勾选一个项目'));
    return;
  }

  // Calculate total
  const totalAmount = details.reduce((sum, d) => sum + (d.total_price || 0), 0);

  // Submit to create quotation via system diagram API
  const submitBtn = document.getElementById('bomSubmitBtn');
  if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = _t('创建中...'); }

  try {
    const apiUrl = (DIAGRAM_CONFIG.editorBase || '/system-diagram/') + 'api/' + DIAGRAM_CONFIG.diagramId + '/create-quotation';
    const resp = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': DIAGRAM_CONFIG.csrfToken
      },
      body: JSON.stringify({ details: details })
    });
    const result = await resp.json();
    if (result.success || result.status === 'success') {
      showToast('✓ ' + _t('报价单已创建'));
      closeBOMPreview();
      if (result.redirect_url) {
        window.open(result.redirect_url, '_blank');
      } else if (result.quotation_id) {
        window.open(`/quotation/${result.quotation_id}`, '_blank');
      }
    } else {
      showToast(_t('创建失败') + ': ' + (result.message || ''));
    }
  } catch (err) {
    showToast(_t('创建失败') + ': ' + err.message);
  } finally {
    if (submitBtn) { submitBtn.disabled = false; submitBtn.textContent = _t('生成报价单'); }
  }
}

// ====== INJECT CSS for BOM highlight animation ======
(function(){
  const style = document.createElement('style');
  style.textContent = `
    @keyframes bomPulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.3; }
    }
  `;
  document.head.appendChild(style);
})();
