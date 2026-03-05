/**
 * PMA 系统图编辑器 — 平面图视图
 * 背景图管理、设备放置、锁定、走线路由、区域框、标定、楼层数据管理
 * 依赖: system-diagram-core.js, system-diagram-topology.js (必须先加载)
 */

// ====== COVERAGE VISUALIZATION ======
const COVERAGE_RINGS = [
  { color: '#16a34a', fillOpacity: 0.12, strokeOpacity: 0.6, strokeWidth: 1.2, labelOpacity: 0.8 },
  { color: '#22c55e', fillOpacity: 0.08, strokeOpacity: 0.5, strokeWidth: 1,   labelOpacity: 0.7 },
];
const COVERAGE_DEFAULT_RADII = [12, 24];
const COVERAGE_THRESHOLDS = [-65, -80]; // inner=strong signal, mid=uplink boundary
function coverageRadiiFromN(n) {
  const rx1m = -14.5; // _HM_RX1M
  return COVERAGE_THRESHOLDS.map(th => {
    const r = Math.pow(10, (rx1m - th) / (10 * (n || 4.7)));
    return Math.round(r * 10) / 10;
  });
}

function getNodeIconKey(n) {
  if (!n) return '';
  const sub = SUBCATEGORIES[n.subcategoryId];
  if (sub) {
    for (const k in SUBCAT_ICON_MAP) { if ((sub.name || '').includes(k)) return SUBCAT_ICON_MAP[k]; }
    if (sub.iconKey) return sub.iconKey;
  }
  return '';
}

function buildCoveragePropsHTML(nodeId) {
  const n = nodes.find(nd => nd.id === nodeId);
  if (!n || getNodeIconKey(n) !== 'antenna_indoor') return '';
  const isAutoRadii = !n.coverageRadii;
  const radii = n.coverageRadii || coverageRadiiFromN(n.coverageN);
  const checked = n.showCoverage === true ? 'checked' : '';
  const vis = n.coverageVisible || [true, true];
  const ringNames = [
    {zh:'内圈 (-65dBm 强信号)', en:'Inner (-65dBm strong)'},
    {zh:'中圈 (-80dBm 上行边界)', en:'Mid (-80dBm uplink)'},
  ];
  let rows = '';
  for (let i = 0; i < 2; i++) {
    const ring = COVERAGE_RINGS[i];
    rows += `<div style="display:flex;align-items:center;gap:6px;">
      <input type="checkbox" ${vis[i]!==false?'checked':''} onchange="updateCoverageVisible(${nodeId},${i},this.checked)">
      <span style="width:8px;height:8px;border-radius:50%;background:${ring.color};flex-shrink:0;"></span>
      <span style="font-size:11px;color:var(--text-secondary);min-width:90px;">${_m(ringNames[i])}</span>
      <input class="props-input" type="number" min="0" step="5" value="${radii[i]}" style="width:60px;flex:0 0 60px;"
        oninput="updateCoverageRadius(${nodeId},${i},this.value)">
      <span style="font-size:11px;color:var(--text-muted);">m</span>
    </div>`;
  }
  if (!isAutoRadii) {
    rows += `<div style="margin-top:2px;"><a href="#" style="font-size:10px;color:var(--text-muted);" onclick="event.preventDefault();resetCoverageRadii(${nodeId})">${_t('重置为自动')}</a></div>`;
  } else {
    rows += `<div style="margin-top:2px;font-size:10px;color:var(--text-muted);">${_t('自动计算')}</div>`;
  }
  const curN = n.coverageN || 4.7;
  const envOptions = [
    [3.0, {zh:'停车库 (n=3.0)', en:'Parking (n=3.0)'}],
    [3.8, {zh:'普通办公 (n=3.8)', en:'Office (n=3.8)'}],
    [4.7, {zh:'密集区域 (n=4.7)', en:'Dense (n=4.7)'}],
  ];
  const envSelect = `<select class="props-input" style="width:auto;padding:2px 4px;font-size:11px;" onchange="updateCoverageEnv(${nodeId},parseFloat(this.value))">` +
    envOptions.map(([v, label]) => `<option value="${v}"${curN==v?' selected':''}>${_m(label)}</option>`).join('') + '</select>';

  const globalMode = displaySettings.showCoverage;
  const overrideNote = globalMode === 'off'
    ? `<span style="font-size:10px;color:var(--text-muted);">(${_t('全局已关闭')})</span>`
    : globalMode === 'all'
    ? `<span style="font-size:10px;color:var(--text-muted);">(${_t('全局已强制开启')})</span>`
    : '';
  return `<div class="props-divider"></div>
    <div class="props-field">
      <label style="display:flex;align-items:center;gap:8px;cursor:pointer;">
        <input type="checkbox" ${checked} onchange="updateNodeProp(${nodeId},'showCoverage',this.checked)">
        <span class="props-label" style="margin:0;">${_t('显示覆盖范围')}</span>
        ${overrideNote}
      </label>
    </div>
    <div class="props-field"><span class="props-label">${_t('覆盖半径')}</span></div>
    <div style="display:flex;flex-direction:column;gap:4px;padding:0 4px;">${rows}</div>
    <div class="props-field" style="margin-top:4px;">
      <span class="props-label">${_t('传播环境')}</span>
      ${envSelect}
    </div>`;
}

// ====== FLOOR ZOOM COMPENSATION ======
/** Floor plan zoom compensation – makes icons/cables bigger when zoomed out */
function getFloorZoomCompensation() {
  if (scale >= 1) return 1;
  return Math.min(Math.pow(1 / scale, 0.5), 3);
}
/** Stronger compensation for temporary drawing lines – must stay visible at extreme zoom-out */
function getTempEdgeZoomCompensation() {
  if (scale >= 1) return 1;
  return Math.min(1 / scale, 12);
}

// ====== FLOOR PLAN DATA ======
let floorPlans = [];


function getFloorPlansForSave(){
  return floorPlans.map(fp=>({
    id:fp.id, label:fp.label, sort_order:fp.sort_order,
    background:fp.background?Object.assign({url:fp.background.url,width:fp.background.width,height:fp.background.height,offset_x:fp.background.offset_x||0,offset_y:fp.background.offset_y||0,opacity:fp.background.opacity||0.3},fp.background.is_multi_res?{is_multi_res:true,resolutions:fp.background.resolutions,filenames:fp.background.filenames}:{filename:fp.background.filename||''}):null,
    calibration:fp.calibration||null,
    placements:fp.placements.map(p=>({node_id:p.node_id,x:p.x,y:p.y,locked:p.locked||false,rotation:p.rotation||0,qty:p.qty||1,labelPosition:p.labelPosition||null})),
    routes:(fp.routes||[]).map(r=>{const o={id:r.id,sourceNodeId:r.sourceNodeId,targetNodeId:r.targetNodeId,sourcePort:r.sourcePort,targetPort:r.targetPort,cableType:r.cableType,routeMode:r.routeMode,midPos:r.midPos,color:r.color,width:r.width,dash:r.dash,label:r.label,linked_edge_id:r.linked_edge_id||null,_userPorts:r._userPorts||false};if(r.waypoints&&r.waypoints.length)o.waypoints=r.waypoints;return o}),
    areas:(fp.areas||[]).map(a=>({id:a.id,label:a.label,x:a.x,y:a.y,width:a.width,height:a.height,color:a.color||'#3b82f6',opacity:a.opacity||0.08,locked:a.locked||false,is_riser:a.is_riser||false,area_type:a.area_type||'normal',_riser_node_id:a._riser_node_id||null})),
    risers:(fp.risers||[]).map(r=>({id:r.id,node_id:r.node_id,edge_id:r.edge_id,target_floor_label:r.target_floor_label,x:r.x,y:r.y})),
    viewX:fp.viewX||0, viewY:fp.viewY||0, scale:fp.scale||1
  }));
}

function restoreFloorPlans(data){
  if(!Array.isArray(data))return;
  floorPlans=data.map(fp=>({
    id:fp.id, label:fp.label, sort_order:fp.sort_order||0,
    background:fp.background||null,
    calibration:fp.calibration||null,
    placements:(fp.placements||[]).map(p=>({node_id:p.node_id,x:p.x,y:p.y,locked:p.locked||false,rotation:p.rotation||0,qty:p.qty||1,labelPosition:p.labelPosition||null})),
    routes:fp.routes||[],
    areas:fp.areas||[],
    risers:fp.risers||[],
    viewX:fp.viewX||0, viewY:fp.viewY||0, scale:fp.scale||1
  }));
  rebuildViewTabs();
}

// ====== FLOOR PLAN RENDERING ======
function renderFloorPlanView(viewId, isDragging){
  const fp=getFloorPlan(viewId);
  if(!fp){renderTopologyView();return}

  const nodesLayer=document.getElementById('nodesLayer');
  const edgesLayer=document.getElementById('edgesLayer');
  const handlesLayer=document.getElementById('handlesLayer');
  const edgeHitLayer=document.getElementById('edgeHitLayer');
  nodesLayer.innerHTML='';edgesLayer.innerHTML='';handlesLayer.innerHTML='';edgeHitLayer.innerHTML='';

  // 1. Render background image (cached, fast even during drag)
  renderFloorBackground(fp);

  // 2. Render areas
  renderFloorAreas(fp);

  // 3. Render calibration line (skip during drag)
  if(!isDragging && fp.calibration&&fp.calibration.ref_line){
    renderCalibrationLine(fp);
  }

  // 4. Render coverage (skip during drag — expensive)
  // Heatmap uses persistent coverageLayer (not cleared above), so zoom/pan keeps existing DOM
  const coverageLayer = document.getElementById('coverageLayer');
  if(!isDragging){
    if (displaySettings.coverageMode === 'heatmap' && displaySettings.showCoverage !== 'off') {
      renderCoverageHeatmap(fp);  // internally skips DOM rebuild when stamp unchanged
    } else {
      coverageLayer.innerHTML = '';  // clear persistent layer when not in heatmap mode
      if (displaySettings.showCoverage !== 'off') {
        renderCoverageCircles(fp);  // circles go into edgesLayer (rebuilt each frame, fine)
      }
    }
  }
  // isDragging: leave coverageLayer untouched — heatmap stays visible via SVG transform

  // 5. Render manual routes (floor plan connections)
  renderFloorRoutes(fp);

  // 6. Render placed devices
  renderFloorNodes(fp);

  // 7. Floor route mid-handles
  renderFloorMidHandles(fp);

  // 7b. Floor route endpoint handles (reconnect drag)
  renderFloorRouteEndpoints(fp);

  // 8. Legend & scale indicator (skip during drag)
  if(!isDragging){
    buildFloorLegend(fp);
    updateScaleIndicator();
  }
}

// ====== BACKGROUND ======
let cachedFloorBgImg=null;
let _cachedBgUrl=null;

function renderFloorBackground(fp){
  if(!fp.background||!fp.background.url){
    // No background — remove cached element and any orphaned DOM element
    if(cachedFloorBgImg&&cachedFloorBgImg.parentNode){cachedFloorBgImg.remove()}
    const orphan=document.getElementById('floorBgImage');if(orphan)orphan.remove();
    cachedFloorBgImg=null;_cachedBgUrl=null;
    return;
  }

  const bg=fp.background;
  const canvasGroup=document.getElementById('canvasGroup');

  // Reuse existing element if URL unchanged
  if(cachedFloorBgImg && _cachedBgUrl===bg.url && cachedFloorBgImg.parentNode===canvasGroup){
    // Only update attributes that may have changed
    cachedFloorBgImg.setAttribute('x',bg.offset_x||0);
    cachedFloorBgImg.setAttribute('y',bg.offset_y||0);
    cachedFloorBgImg.setAttribute('width',bg.width);
    cachedFloorBgImg.setAttribute('height',bg.height);
    cachedFloorBgImg.setAttribute('opacity',bg.opacity||0.3);
    return;
  }

  // Create new element (first render or URL changed)
  const oldImg=cachedFloorBgImg;
  const orphan=document.getElementById('floorBgImage');

  const img=document.createElementNS('http://www.w3.org/2000/svg','image');
  img.setAttribute('id','floorBgImage');
  img.setAttribute('href',bg.url);
  img.setAttribute('x',bg.offset_x||0);
  img.setAttribute('y',bg.offset_y||0);
  img.setAttribute('width',bg.width);
  img.setAttribute('height',bg.height);
  img.style.pointerEvents='none';

  // Insert before all layers so it appears behind everything
  const firstLayer=canvasGroup.querySelector('#coverageLayer')||canvasGroup.querySelector('#edgesLayer')||canvasGroup.firstChild;

  // Multi-res switch: keep old image visible until new one loads to avoid flicker
  if(oldImg&&oldImg.parentNode&&bg.is_multi_res){
    img.setAttribute('opacity','0');
    img.onload=function(){
      if(oldImg&&oldImg.parentNode)oldImg.remove();
      if(orphan&&orphan!==oldImg&&orphan.parentNode)orphan.remove();
      img.setAttribute('opacity',bg.opacity||0.3);
    };
    img.onerror=function(){
      // Fallback: remove broken new image, keep old visible
      if(img.parentNode)img.remove();
      console.error('Failed to load multi-res image:',bg.url);
    };
    canvasGroup.insertBefore(img,firstLayer);
  } else {
    img.setAttribute('opacity',bg.opacity||0.3);
    if(oldImg&&oldImg.parentNode)oldImg.remove();
    if(orphan&&orphan!==oldImg)if(orphan&&orphan.parentNode)orphan.remove();
    canvasGroup.insertBefore(img,firstLayer);
  }
  cachedFloorBgImg=img;
  _cachedBgUrl=bg.url;
}

// ====== AREAS ======
const AREA_TYPES={
  normal:{label:{zh:'普通',en:'Normal'},icon:''},
  riser:{label:{zh:'弱电井',en:'Riser'},icon:'\u26A1'},
  central_room:{label:{zh:'中心机房',en:'Equipment Room'},icon:'\uD83C\uDFE2'}
};

// Get the areas array for the current view (topology or floor plan)
function getAreaStorage(){
  if(currentView==='topology')return topoAreas;
  const fp=getFloorPlan(currentView);
  return fp?(fp.areas||(fp.areas=[])):null;
}

function renderAreas(areas){
  if(!areas||!areas.length)return;
  const layer=document.getElementById('edgesLayer');
  areas.forEach(area=>{
    const atype=area.area_type||((area.is_riser)?'riser':'normal');
    const isSel=selectedAreaId===area.id;
    const g=document.createElementNS('http://www.w3.org/2000/svg','g');
    g.setAttribute('class',`floor-area${isSel?' selected':''}`);g.dataset.areaId=area.id;

    const rect=document.createElementNS('http://www.w3.org/2000/svg','rect');
    rect.setAttribute('x',area.x);rect.setAttribute('y',area.y);
    rect.setAttribute('width',area.width);rect.setAttribute('height',area.height);
    rect.setAttribute('fill',area.color||'#3b82f6');
    rect.setAttribute('fill-opacity',area.opacity||0.08);
    rect.setAttribute('stroke',isSel?(area.color||'#3b82f6'):'none');
    rect.setAttribute('stroke-width',isSel?2:0);
    rect.setAttribute('rx',4);
    g.appendChild(rect);

    // Centered label
    const cx=area.x+area.width/2,cy=area.y+area.height/2;
    const cl=document.createElementNS('http://www.w3.org/2000/svg','text');
    cl.setAttribute('x',cx);cl.setAttribute('y',cy);
    cl.setAttribute('text-anchor','middle');cl.setAttribute('dominant-baseline','central');
    cl.setAttribute('font-size',Math.min(24,Math.max(12,area.width/8)));
    cl.setAttribute('fill',area.color||'#3b82f6');
    cl.setAttribute('fill-opacity',isSel?'0.5':'0.15');
    cl.setAttribute('font-weight','700');cl.setAttribute('letter-spacing','2');
    cl.style.pointerEvents='none';cl.style.userSelect='none';
    cl.textContent=area.label;g.appendChild(cl);

    // Area type icon (riser / central_room)
    const typeInfo=AREA_TYPES[atype];
    if(typeInfo&&typeInfo.icon){
      const ri=document.createElementNS('http://www.w3.org/2000/svg','text');
      ri.setAttribute('x',area.x+12);ri.setAttribute('y',area.y+14);
      ri.setAttribute('font-size','11');ri.setAttribute('fill',area.color||'#3b82f6');
      ri.setAttribute('fill-opacity','0.6');ri.style.pointerEvents='none';
      ri.textContent=typeInfo.icon;g.appendChild(ri);
    }
    // Dashed border for special area types
    if(atype!=='normal'){
      rect.setAttribute('stroke',area.color||'#3b82f6');
      rect.setAttribute('stroke-width',1.5);
      rect.setAttribute('stroke-dasharray','6 3');
      rect.setAttribute('stroke-opacity','0.4');
    }

    // Lock icon
    if(area.locked){
      const li=document.createElementNS('http://www.w3.org/2000/svg','text');
      li.setAttribute('x',area.x+area.width-14);li.setAttribute('y',area.y+14);
      li.setAttribute('font-size','10');li.setAttribute('fill',area.color||'#3b82f6');
      li.setAttribute('fill-opacity','0.5');li.textContent='\uD83D\uDD12';
      g.appendChild(li);
    }

    // Click to select area
    g.addEventListener('mousedown',e=>{
      if(currentTool==='area')return;
      selectedAreaId=area.id;selectedNodeIds=new Set();selectedEdgeId=null;
      if(!DIAGRAM_CONFIG.readOnly)showAreaProps(area.id);
      renderAll();
      if(DIAGRAM_CONFIG.readOnly||area.locked)return;
      e.stopPropagation();
      const pt=svgPoint(e);
      isDraggingArea=true;dragAreaId=area.id;
      areaDragOffset={x:pt.x-area.x,y:pt.y-area.y};
      pushHistory();
    });

    // Resize handles (only when selected and not locked)
    if(isSel&&!area.locked){
      const handles=[
        {id:'tl',cx:area.x,cy:area.y},
        {id:'tr',cx:area.x+area.width,cy:area.y},
        {id:'bl',cx:area.x,cy:area.y+area.height},
        {id:'br',cx:area.x+area.width,cy:area.y+area.height}
      ];
      handles.forEach(h=>{
        const c=document.createElementNS('http://www.w3.org/2000/svg','rect');
        c.setAttribute('x',h.cx-4);c.setAttribute('y',h.cy-4);
        c.setAttribute('width',8);c.setAttribute('height',8);
        c.setAttribute('rx',2);
        c.setAttribute('class','area-resize-handle');
        c.style.cursor=h.id==='tl'||h.id==='br'?'nwse-resize':'nesw-resize';
        c.addEventListener('mousedown',ev=>{
          ev.stopPropagation();
          isResizingArea=true;resizeAreaId=area.id;resizeHandle=h.id;
          const pt=svgPoint(ev);
          resizeAreaStart={x:area.x,y:area.y,w:area.width,h:area.height,mx:pt.x,my:pt.y};
          pushHistory();
        });
        g.appendChild(c);
      });
    }

    layer.appendChild(g);
  });
}

// Backward-compatible wrapper for floor plan view
function renderFloorAreas(fp){ renderAreas(fp.areas); }

function showAreaProps(areaId){
  const areas=getAreaStorage();if(!areas)return;
  const area=areas.find(a=>a.id===areaId);if(!area)return;
  const atype=area.area_type||(area.is_riser?'riser':'normal');
  const panel=document.getElementById('propsPanel');
  panel.classList.add('visible');
  document.getElementById('propsTitle').textContent=_t('区域属性');
  const typeOptions=Object.entries(AREA_TYPES).map(([k,v])=>`<option value="${k}"${k===atype?' selected':''}>${_m(v.label)}</option>`).join('');
  document.getElementById('propsContent').innerHTML=`
    <div class="props-field"><span class="props-label">${_t('名称')}</span><input class="props-input" value="${area.label}" oninput="updateAreaProp(${areaId},'label',this.value)"></div>
    <div class="props-field"><span class="props-label">${_t('类型')}</span><select class="props-input" onchange="changeAreaType(${areaId},this.value)">${typeOptions}</select></div>
    <div class="props-field"><span class="props-label">${_t('颜色')}</span><div class="props-row"><input type="color" class="props-color" value="${area.color||'#3b82f6'}" oninput="updateAreaProp(${areaId},'color',this.value)"><input class="props-input" style="flex:1;font-family:monospace;font-size:11px;" value="${area.color||'#3b82f6'}" oninput="updateAreaProp(${areaId},'color',this.value)"></div></div>
    <div class="props-field"><span class="props-label">${_t('透明度')}</span><div class="props-row"><input type="range" class="props-range" min="0.02" max="0.3" step="0.02" value="${area.opacity||0.08}" oninput="updateAreaProp(${areaId},'opacity',parseFloat(this.value));this.nextElementSibling.textContent=Math.round(this.value*100)+'%'"><span class="props-range-val">${Math.round((area.opacity||0.08)*100)}%</span></div></div>
    <div class="props-field"><span class="props-label">${_t('位置')}</span><input class="props-input" value="${Math.round(area.x)}, ${Math.round(area.y)} — ${Math.round(area.width)}×${Math.round(area.height)}" disabled></div>
    <div class="props-field"><label style="display:flex;align-items:center;gap:8px;cursor:pointer;"><input type="checkbox" ${area.locked?'checked':''} onchange="updateAreaProp(${areaId},'locked',this.checked)"><span class="props-label" style="margin:0;">${_t('锁定区域')}</span></label></div>
    <button class="btn-delete" onclick="deleteArea(${areaId})">${_t('删除区域')}</button>`;
}

function changeAreaType(areaId,newType){
  const areas=getAreaStorage();if(!areas)return;
  const area=areas.find(a=>a.id===areaId);if(!area)return;
  pushHistoryProp();
  const oldType=area.area_type||(area.is_riser?'riser':'normal');
  area.area_type=newType;
  // Backward compat: sync is_riser flag
  area.is_riser=(newType==='riser');
  // Floor plan riser node logic
  if(currentView!=='topology'){
    const fp=getFloorPlan(currentView);
    if(fp){
      if(oldType==='riser'&&newType!=='riser')removeRiserNode(fp,area);
      if(oldType!=='riser'&&newType==='riser')toggleRiser(areaId,true);
    }
  }
  hasUnsavedChanges=true;if(currentView!=='topology')syncFloorAreaLabels();renderAll();showAreaProps(areaId);
}

function updateAreaProp(areaId,prop,val){
  const areas=getAreaStorage();if(!areas)return;
  const area=areas.find(a=>a.id===areaId);if(!area)return;
  pushHistoryProp();area[prop]=val;hasUnsavedChanges=true;
  if(currentView!=='topology')syncFloorAreaLabels();
  renderAll();
}

function deleteArea(areaId){
  if(DIAGRAM_CONFIG.readOnly)return;
  const areas=getAreaStorage();if(!areas)return;
  const area=areas.find(a=>a.id===areaId);
  if(area&&area.is_riser&&currentView!=='topology'){const fp=getFloorPlan(currentView);if(fp)removeRiserNode(fp,area)}
  pushHistory();
  const idx=areas.indexOf(area);if(idx>=0)areas.splice(idx,1);
  selectedAreaId=null;if(currentView!=='topology')syncFloorAreaLabels();hasUnsavedChanges=true;renderAll();hideProps();
  showToast(_t('已删除区域'));
}

// ====== RISER (弱电井) ======
function toggleRiser(areaId, checked){
  const fp=getFloorPlan(currentView);
  const area=fp?fp.areas.find(a=>a.id===areaId):null;
  if(!area)return;
  pushHistoryProp();
  area.is_riser=checked;
  const cx=area.x+area.width/2, cy=area.y+area.height/2;
  if(checked){
    const inside=fp.placements.filter(p=>
      p.x>=area.x && p.x<=area.x+area.width &&
      p.y>=area.y && p.y<=area.y+area.height
    );
    if(inside.length>1){
      area.is_riser=false;
      showToast(_t('弱电井区域最多容纳1个设备'));
      showAreaProps(areaId);return;
    }
    if(inside.length===1){
      inside[0].x=cx;inside[0].y=cy;
    } else {
      createRiserNode(fp,area);
    }
  } else {
    removeRiserNode(fp,area);
  }
  hasUnsavedChanges=true;
  syncFloorAreaLabels();renderAll();showAreaProps(areaId);
}

function createRiserNode(fp,area){
  const cx=area.x+area.width/2, cy=area.y+area.height/2;
  const topoPos=computeNextTopoPosition();
  const node={
    id:nodeIdCounter++, subcategoryId:null, selectedProductId:null,
    name:area.label||_t('弱电井'), model:'',
    category:_t('弱电井'), color:'#f59e0b',
    iconData:DEFAULT_DEVICE_ICONS.riser,
    products:[],
    x:topoPos.x, y:topoPos.y, w:NODE_SIZE, h:NODE_SIZE,
    qty:1, label:'', hideLabel:false,
    floor_id:fp.id, area_label:area.label, floor_label:fp.label,
    is_riser_node:true
  };
  nodes.push(node);
  fp.placements.push({node_id:node.id, x:cx-NODE_SIZE/2, y:cy-NODE_SIZE/2, locked:true, rotation:0, qty:1});
  area._riser_node_id=node.id;
}

function removeRiserNode(fp,area){
  if(!area._riser_node_id)return;
  const nid=area._riser_node_id;
  const n=nodes.find(n=>n.id===nid);
  if(n && n.is_riser_node){
    nodes.splice(nodes.indexOf(n),1);
    fp.placements=fp.placements.filter(p=>p.node_id!==nid);
    edges=edges.filter(e=>e.sourceId!==nid && e.targetId!==nid);
  }
  delete area._riser_node_id;
}

function snapToRiserIfNeeded(placement,fp){
  const node=nodes.find(n=>n.id===placement.node_id);
  if(!node||node.is_riser_node)return;
  const plCx=placement.x+NODE_SIZE/2,plCy=placement.y+NODE_SIZE/2;
  const riserArea=(fp.areas||[]).find(a=>
    a.is_riser && plCx>=a.x && plCx<=a.x+a.width && plCy>=a.y && plCy<=a.y+a.height
  );
  if(!riserArea)return;
  // Check if another real device already occupies this riser
  const hasOtherReal=fp.placements.some(p=>{
    if(p===placement)return false;
    const cx=p.x+NODE_SIZE/2,cy=p.y+NODE_SIZE/2;
    if(cx<riserArea.x||cx>riserArea.x+riserArea.width||cy<riserArea.y||cy>riserArea.y+riserArea.height)return false;
    const n=nodes.find(n=>n.id===p.node_id);return n&&!n.is_riser_node;
  });
  if(hasOtherReal){showToast(_t('弱电井区域只能放置1个设备'));return}
  removeRiserNode(fp,riserArea);
  placement.x=riserArea.x+riserArea.width/2-NODE_SIZE/2;
  placement.y=riserArea.y+riserArea.height/2-NODE_SIZE/2;
}

function syncRiserNodes(fp){
  (fp.areas||[]).forEach(a=>{
    if(!a.is_riser)return;
    const hasRealDevice=fp.placements.some(p=>{
      const cx=p.x+NODE_SIZE/2,cy=p.y+NODE_SIZE/2;
      if(cx<a.x||cx>a.x+a.width||cy<a.y||cy>a.y+a.height)return false;
      const n=nodes.find(n=>n.id===p.node_id);return n&&!n.is_riser_node;
    });
    if(!hasRealDevice&&!a._riser_node_id)createRiserNode(fp,a);
  });
}

// ====== CALIBRATION LINE ======
function renderCalibrationLine(fp){
  if(!fp.calibration||!fp.calibration.ref_line)return;
  const ref=fp.calibration.ref_line;
  const layer=document.getElementById('handlesLayer');

  const g=document.createElementNS('http://www.w3.org/2000/svg','g');
  g.setAttribute('class','calibration-group');
  g.style.cursor='pointer';

  // Hit area for easier clicking
  const hitLine=document.createElementNS('http://www.w3.org/2000/svg','line');
  hitLine.setAttribute('x1',ref.x1);hitLine.setAttribute('y1',ref.y1);
  hitLine.setAttribute('x2',ref.x2);hitLine.setAttribute('y2',ref.y2);
  hitLine.setAttribute('stroke','transparent');hitLine.setAttribute('stroke-width',14);
  g.appendChild(hitLine);

  // Reference line
  const line=document.createElementNS('http://www.w3.org/2000/svg','line');
  line.setAttribute('x1',ref.x1);line.setAttribute('y1',ref.y1);
  line.setAttribute('x2',ref.x2);line.setAttribute('y2',ref.y2);
  line.setAttribute('stroke','#f59e0b');line.setAttribute('stroke-width',2);
  line.setAttribute('stroke-dasharray','6 3');
  g.appendChild(line);

  // End markers
  [ref.x1,ref.y1,ref.x2,ref.y2].forEach((_,i)=>{
    if(i%2!==0)return;
    const c=document.createElementNS('http://www.w3.org/2000/svg','circle');
    c.setAttribute('cx',i===0?ref.x1:ref.x2);
    c.setAttribute('cy',i===0?ref.y1:ref.y2);
    c.setAttribute('r',4);c.setAttribute('fill','#f59e0b');c.setAttribute('stroke','#fff');c.setAttribute('stroke-width',1);
    g.appendChild(c);
  });

  // Label showing real length
  const mx=(ref.x1+ref.x2)/2,my=(ref.y1+ref.y2)/2;
  const label=document.createElementNS('http://www.w3.org/2000/svg','text');
  label.setAttribute('x',mx);label.setAttribute('y',my-8);
  label.setAttribute('text-anchor','middle');
  label.setAttribute('font-size','10');
  label.setAttribute('fill','#f59e0b');
  label.setAttribute('font-weight','600');
  label.textContent=`${fp.calibration.real_length}${fp.calibration.unit||'m'}`;
  g.appendChild(label);

  // Click to select and show calibration props
  g.addEventListener('mousedown',e=>{
    e.stopPropagation();
    selectedNodeIds=new Set();selectedEdgeId=null;selectedAreaId=null;selectedRouteId=null;
    showCalibrationProps(fp);
  });

  layer.appendChild(g);
}

// ====== CALIBRATION PROPS & APPLY ======
function showCalibrationProps(fp){
  const panel=document.getElementById('propsPanel');
  panel.classList.add('visible');
  document.getElementById('propsTitle').textContent=_t('尺寸标定');
  const temp=fp._calibTemp;
  const hasExisting=fp.calibration&&fp.calibration.ref_line;
  let html='';
  if(temp){
    html+=`<div class="props-field"><span class="props-label">${_t('像素长度')}</span><input class="props-input" value="${Math.round(temp.pixelLength)} px" disabled></div>
    <div class="props-field"><span class="props-label">${_t('实际长度')}</span>
      <div class="props-row"><input class="props-input" id="calibRealLen" type="number" min="0.01" step="0.01" placeholder="${_t('输入长度')}" style="flex:1;">
      <select class="props-select" id="calibUnit" style="width:60px;"><option value="m">m</option><option value="cm">cm</option></select></div>
    </div>
    ${hasExisting?`<div style="font-size:11px;color:#f59e0b;margin:4px 0;">${_t('已有标定，将基于当前比例重新调整')}</div>`:''}
    <button style="width:100%;padding:8px;background:#1d4ed8;border:none;border-radius:6px;color:#fff;font-size:12px;cursor:pointer;margin-top:8px;" onclick="applyCalibration()">${_t('应用标定')}</button>`;
  }
  if(hasExisting){
    html+=`<div class="props-section">${_t('当前标定')}</div>
    <div class="props-field"><span class="props-label">${_t('参考长度')}</span><input class="props-input" value="${fp.calibration.real_length} ${fp.calibration.unit||'m'}" disabled></div>
    <div class="props-field"><span class="props-label">${_t('比例')}</span><input class="props-input" value="1m = ${Math.round(fp.calibration.px_per_meter||53)} px" disabled></div>
    <button class="btn-delete" onclick="deleteCalibration()">${_t('删除标定')}</button>`;
  }
  document.getElementById('propsContent').innerHTML=html;
  if(temp)setTimeout(()=>{const inp=document.getElementById('calibRealLen');if(inp)inp.focus()},50);
}

function applyCalibration(){
  const fp=getFloorPlan(currentView);if(!fp||!fp._calibTemp)return;
  const realInput=document.getElementById('calibRealLen');
  const unitSel=document.getElementById('calibUnit');
  if(!realInput||!realInput.value){showToast(_t('请输入实际长度'));return}
  let realLength=parseFloat(realInput.value);
  const unit=unitSel?unitSel.value:'m';
  if(isNaN(realLength)||realLength<=0){showToast(_t('请输入有效的正数'));return}
  if(unit==='cm')realLength=realLength/100; // convert to meters

  const temp=fp._calibTemp;
  const pxPerMeter=temp.pixelLength/realLength;
  const targetPxPerMeter=53; // 64px / 1.2m (含外圈glow)
  const scaleFactor=targetPxPerMeter/pxPerMeter;

  pushHistory();

  // Scale background
  if(fp.background){
    fp.background.width=Math.round(fp.background.width*scaleFactor);
    fp.background.height=Math.round(fp.background.height*scaleFactor);
    if(fp.background.offset_x)fp.background.offset_x=Math.round(fp.background.offset_x*scaleFactor);
    if(fp.background.offset_y)fp.background.offset_y=Math.round(fp.background.offset_y*scaleFactor);
  }

  // Save calibration with scaled ref line
  fp.calibration={
    ref_line:{x1:temp.x1*scaleFactor,y1:temp.y1*scaleFactor,x2:temp.x2*scaleFactor,y2:temp.y2*scaleFactor},
    real_length:parseFloat(realInput.value),
    unit:unit,
    px_per_meter:targetPxPerMeter
  };

  // Scale all placements
  fp.placements.forEach(p=>{p.x=Math.round(p.x*scaleFactor);p.y=Math.round(p.y*scaleFactor)});

  // Scale all areas
  (fp.areas||[]).forEach(a=>{a.x=Math.round(a.x*scaleFactor);a.y=Math.round(a.y*scaleFactor);a.width=Math.round(a.width*scaleFactor);a.height=Math.round(a.height*scaleFactor)});

  // Scale all routes (midPos if any)
  (fp.routes||[]).forEach(r=>{if(r.midPos)r.midPos=r.midPos*scaleFactor});

  // Scale risers
  (fp.risers||[]).forEach(r=>{if(r.x)r.x=Math.round(r.x*scaleFactor);if(r.y)r.y=Math.round(r.y*scaleFactor)});

  delete fp._calibTemp;
  hasUnsavedChanges=true;
  syncFloorAreaLabels();renderAll();
  fitView(); // 居中显示缩放后的内容
  showToast(`${_t('已标定')}: 1m = ${targetPxPerMeter}px, ${_t('比例')}: ${scaleFactor.toFixed(2)}×`);
  showCalibrationProps(fp);
}

function deleteCalibration(){
  const fp=getFloorPlan(currentView);if(!fp)return;
  pushHistory();
  fp.calibration=null;
  hasUnsavedChanges=true;renderAll();hideProps();
  showToast(_t('标定已删除，背景图比例不变'));
}

// ====== BEST PORT SELECTION ======
function findBestPort(srcPl,tgtPl,nodeSize,routeMode){
  const sx=srcPl.x+nodeSize/2,sy=srcPl.y+nodeSize/2;
  const tx=tgtPl.x+nodeSize/2,ty=tgtPl.y+nodeSize/2;
  const dx=tx-sx,dy=ty-sy;
  // For ortho routes (ortho2/ortho3), use only cardinal directions (top/right/bottom/left)
  // This ensures the port aligns with the ortho path direction
  if(routeMode==='ortho2'||routeMode==='ortho3'||routeMode==='straight'){
    const adx=Math.abs(dx),ady=Math.abs(dy);
    if(adx>=ady){return{srcPort:dx>0?'right':'left',tgtPort:dx>0?'left':'right'}}
    return{srcPort:dy>0?'bottom':'top',tgtPort:dy>0?'top':'bottom'};
  }
  // For bezier/other modes, use 8-direction ports
  const angle=Math.atan2(dy,dx)*180/Math.PI;
  const pick=(a)=>{
    if(a>=-22.5&&a<22.5)return'right';
    if(a>=22.5&&a<67.5)return'bottom-right';
    if(a>=67.5&&a<112.5)return'bottom';
    if(a>=112.5&&a<157.5)return'bottom-left';
    if(a<-157.5||a>=157.5)return'left';
    if(a>=-157.5&&a<-112.5)return'top-left';
    if(a>=-112.5&&a<-67.5)return'top';
    return'top-right';
  };
  return{srcPort:pick(angle),tgtPort:pick(angle>0?angle-180:angle+180)};
}

// ====== COVERAGE CIRCLES ======
function renderCoverageCircles(fp) {
  if (displaySettings.showCoverage === 'off') return;
  if (!fp.calibration || !fp.calibration.px_per_meter) return;
  const ppm = fp.calibration.px_per_meter;
  const edgesLayer = document.getElementById('edgesLayer');

  // Collect coverage SVG — build in a fragment, then prepend
  const frag = document.createDocumentFragment();
  const svgNS = 'http://www.w3.org/2000/svg';

  // We need a <defs> for textPath arcs
  const defs = document.createElementNS(svgNS, 'defs');
  const coverageG = document.createElementNS(svgNS, 'g');
  coverageG.setAttribute('class', 'coverage-layer');
  coverageG.style.pointerEvents = 'none';

  let pathIdCounter = 0;

  fp.placements.forEach(pl => {
    const n = nodes.find(nd => nd.id === pl.node_id);
    if (!n) return;
    if (getNodeIconKey(n) !== 'antenna_indoor') return;
    if (displaySettings.showCoverage === 'individual' && n.showCoverage !== true) return;

    const cx = pl.x + (n.w || NODE_SIZE) / 2;
    const cy = pl.y + (n.h || NODE_SIZE) / 2;
    const radii = n.coverageRadii || coverageRadiiFromN(n.coverageN);

    // Draw from outer to inner so inner paints on top
    const globalRingKeys = ['showCoverageInner', 'showCoverageMid'];
    const vis = n.coverageVisible || [true, true];
    for (let i = radii.length - 1; i >= 0; i--) {
      const r = radii[i] * ppm;
      if (r <= 0) continue;
      if (!displaySettings[globalRingKeys[i]]) continue;
      if (!vis[i]) continue;
      const ring = COVERAGE_RINGS[i] || COVERAGE_RINGS[COVERAGE_RINGS.length - 1];

      // Filled circle with solid stroke
      const circle = document.createElementNS(svgNS, 'circle');
      circle.setAttribute('cx', cx);
      circle.setAttribute('cy', cy);
      circle.setAttribute('r', r);
      circle.setAttribute('fill', ring.color);
      circle.setAttribute('fill-opacity', displaySettings.coverageFill ? ring.fillOpacity : 0);
      circle.setAttribute('stroke', ring.color);
      circle.setAttribute('stroke-opacity', ring.strokeOpacity);
      circle.setAttribute('stroke-width', ring.strokeWidth);
      coverageG.appendChild(circle);

      // Arc path for textPath label (clockwise circle starting at right)
      const pathId = `covArc_${pl.node_id}_${i}_${pathIdCounter++}`;
      const arcPath = document.createElementNS(svgNS, 'path');
      // Full circle: two semicircles
      arcPath.setAttribute('d',
        `M ${cx - r},${cy} A ${r},${r} 0 1,1 ${cx + r},${cy} A ${r},${r} 0 1,1 ${cx - r},${cy}`
      );
      arcPath.setAttribute('id', pathId);
      arcPath.setAttribute('fill', 'none');
      arcPath.setAttribute('stroke', 'none');
      defs.appendChild(arcPath);

      // Text label along arc
      const text = document.createElementNS(svgNS, 'text');
      text.setAttribute('fill', ring.color);
      text.setAttribute('fill-opacity', ring.labelOpacity);
      text.setAttribute('font-size', '11');
      text.setAttribute('font-family', 'system-ui, sans-serif');
      const tp = document.createElementNS(svgNS, 'textPath');
      tp.setAttribute('href', `#${pathId}`);
      tp.setAttribute('startOffset', '92%');
      tp.setAttribute('text-anchor', 'middle');
      tp.textContent = `${radii[i]}m`;
      text.appendChild(tp);
      coverageG.appendChild(text);
    }
  });

  // Prepend defs + coverage group into edgesLayer (behind routes)
  if (coverageG.childNodes.length > 0) {
    edgesLayer.insertBefore(coverageG, edgesLayer.firstChild);
    edgesLayer.insertBefore(defs, edgesLayer.firstChild);
  }
}

// ====== COVERAGE HEATMAP ======
// 对讲机信号物理模型：Rx(dBm) = Tx - FSPL(1m) - 10·n·log₁₀(d)
const _HM_TX = 10, _HM_FSPL1M = 24.5, _HM_RX1M = _HM_TX - _HM_FSPL1M; // -14.5 dBm
const _HM_DESIGN = -85, _HM_FLOOR = -95;
const _HM_RANGE = _HM_RX1M - _HM_FLOOR; // 95.5 dB
const HEATMAP_SAMPLE_SIZE = 4;
const HEATMAP_COLORS = [
  { stop: 0.00, r: 59,  g: 130, b: 246 },  // 蓝 (噪声底)
  { stop: 0.08, r: 6,   g: 182, b: 212 },  // 青
  { stop: 0.15, r: 16,  g: 185, b: 145 },  // 青绿
  { stop: 0.25, r: 34,  g: 197, b: 94  },  // 绿 (中圈区域)
  { stop: 0.35, r: 100, g: 200, b: 55  },  // 黄绿
  { stop: 0.42, r: 180, g: 200, b: 30  },  // 黄绿偏黄
  { stop: 0.50, r: 240, g: 190, b: 20  },  // 黄 (内圈区域)
  { stop: 0.60, r: 245, g: 120, b: 11  },  // 橙
  { stop: 0.80, r: 234, g: 70,  b: 12  },  // 橙红
  { stop: 1.00, r: 220, g: 38,  b: 38  },  // 红 (天线中心)
];
let _heatmapCache = { stamp: null, dataUrl: null, bounds: null, mode: null };

function _hmSignalDbm(d, n) {
  if (d < 0.5) return _HM_RX1M;
  return _HM_RX1M - 10 * n * Math.log10(d);
}
function _hmStrength(d, n) {
  const dBm = _hmSignalDbm(d, n);
  if (dBm >= _HM_RX1M) return 1.0;
  if (dBm <= _HM_FLOOR) return 0.0;
  const linear = (dBm - _HM_FLOOR) / _HM_RANGE;
  return linear;
}
function _hmColor(s) {
  for (let i = 1; i < HEATMAP_COLORS.length; i++) {
    if (s <= HEATMAP_COLORS[i].stop) {
      const a = HEATMAP_COLORS[i - 1], b = HEATMAP_COLORS[i];
      const t = (s - a.stop) / (b.stop - a.stop);
      return { r: Math.round(a.r + (b.r - a.r) * t), g: Math.round(a.g + (b.g - a.g) * t), b: Math.round(a.b + (b.b - a.b) * t) };
    }
  }
  return HEATMAP_COLORS[HEATMAP_COLORS.length - 1];
}

// Derive effective n from the coverage radii the user actually sees (circles).
// This ensures the heatmap paints the same contour as the coverage rings.
function _hmEffectiveN(nd) {
  const radii = nd.coverageRadii || coverageRadiiFromN(nd.coverageN);
  const rMid = radii[1]; // mid-ring radius in metres, corresponds to -80 dBm
  if (rMid > 0.5) {
    // -80 = -14.5 - 10*n*log10(rMid)  →  n = 65.5 / (10*log10(rMid))
    return 65.5 / (10 * Math.log10(rMid));
  }
  return nd.coverageN || 4.7;
}

function _hmStamp(fp) {
  const parts = [displaySettings.showCoverage || 'off'];  // include mode so switching individual↔all invalidates
  fp.placements.forEach(pl => {
    const nd = nodes.find(x => x.id === pl.node_id);
    if (!nd || getNodeIconKey(nd) !== 'antenna_indoor') return;
    if (displaySettings.showCoverage === 'individual' && nd.showCoverage !== true) return;
    const radii = nd.coverageRadii || coverageRadiiFromN(nd.coverageN);
    parts.push(`${pl.x},${pl.y},r=${radii.join(',')}`);
  });
  return parts.join('|');
}

function _hmBounds(fp, ppm, antennasData) {
  // Prefer the floor-plan background dimensions so the heatmap matches the drawing
  if (fp.background && fp.background.width && fp.background.height) {
    return {
      x: fp.background.offset_x || 0,
      y: fp.background.offset_y || 0,
      width: fp.background.width,
      height: fp.background.height
    };
  }
  // Fallback: bounding box of antenna positions + padding
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  fp.placements.forEach(pl => {
    const nd = nodes.find(x => x.id === pl.node_id);
    if (!nd) return;
    const cx = pl.x + (nd.w || NODE_SIZE) / 2;
    const cy = pl.y + (nd.h || NODE_SIZE) / 2;
    minX = Math.min(minX, cx); minY = Math.min(minY, cy);
    maxX = Math.max(maxX, cx); maxY = Math.max(maxY, cy);
  });
  if (minX === Infinity) return null;
  const minN = antennasData.reduce((m, a) => Math.min(m, a.n), 4.7);
  const maxRange = Math.pow(10, (_HM_RX1M - _HM_FLOOR) / (10 * minN)) * ppm;
  const pad = Math.min(maxRange, 8000);
  return {
    x: minX - pad, y: minY - pad,
    width: (maxX - minX) + 2 * pad,
    height: (maxY - minY) + 2 * pad
  };
}

function _hmGenerate(fp, ppm, bounds, antennasData) {
  const maxDim = Math.max(bounds.width, bounds.height);
  const ss = maxDim > 6000 ? 8 : maxDim > 3000 ? 6 : HEATMAP_SAMPLE_SIZE;
  const sw = Math.ceil(bounds.width / ss);
  const sh = Math.ceil(bounds.height / ss);
  if (sw <= 0 || sh <= 0) return null;

  const canvas = document.createElement('canvas');
  canvas.width = sw; canvas.height = sh;
  const ctx = canvas.getContext('2d');
  const imageData = ctx.createImageData(sw, sh);
  const data = imageData.data;

  for (let sy = 0; sy < sh; sy++) {
    for (let sx = 0; sx < sw; sx++) {
      const px = bounds.x + (sx + 0.5) * ss;
      const py = bounds.y + (sy + 0.5) * ss;
      let maxS = 0;
      for (const ant of antennasData) {
        const dx = (px - ant.cx) / ppm;
        const dy = (py - ant.cy) / ppm;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const s = _hmStrength(dist, ant.n);
        if (s > maxS) maxS = s;
      }
      if (maxS > 0.03) {
        // Fade out near canvas edges to avoid hard boundary
        const edgeM = 50; // canvas pixels (~200 SVG px)
        const distE = Math.min(sx, sy, sw - 1 - sx, sh - 1 - sy);
        const fade = distE < edgeM ? distE / edgeM : 1.0;
        const c = _hmColor(maxS);
        const idx = (sy * sw + sx) * 4;
        data[idx] = c.r; data[idx + 1] = c.g; data[idx + 2] = c.b;
        data[idx + 3] = Math.min(255, Math.round(Math.pow(maxS, 1.5) * 320 * fade));
      }
    }
  }
  ctx.putImageData(imageData, 0, 0);
  return canvas.toDataURL('image/png');
}

function renderCoverageHeatmap(fp) {
  if (displaySettings.showCoverage === 'off') return;
  if (!fp.calibration || !fp.calibration.px_per_meter) return;
  const ppm = fp.calibration.px_per_meter;
  const coverageLayer = document.getElementById('coverageLayer');  // persistent layer
  const svgNS = 'http://www.w3.org/2000/svg';

  // Collect antenna positions with per-antenna n
  const antennasData = [];
  fp.placements.forEach(pl => {
    const nd = nodes.find(x => x.id === pl.node_id);
    if (!nd || getNodeIconKey(nd) !== 'antenna_indoor') return;
    if (displaySettings.showCoverage === 'individual' && nd.showCoverage !== true) return;
    antennasData.push({
      cx: pl.x + (nd.w || NODE_SIZE) / 2,
      cy: pl.y + (nd.h || NODE_SIZE) / 2,
      n: _hmEffectiveN(nd)
    });
  });
  if (antennasData.length === 0) { coverageLayer.innerHTML = ''; return; }

  const stamp = _hmStamp(fp);

  // ★ Key optimization: stamp unchanged + DOM already has content → skip everything
  if (_heatmapCache.stamp === stamp && _heatmapCache.dataUrl
      && coverageLayer.querySelector('.coverage-layer')) {
    return;
  }

  // Stamp changed or first render: clear and rebuild
  coverageLayer.innerHTML = '';

  const bounds = _hmBounds(fp, ppm, antennasData);
  if (!bounds) return;

  // Generate or use cached dataUrl
  let dataUrl = null;
  if (_heatmapCache.stamp === stamp && _heatmapCache.dataUrl) {
    dataUrl = _heatmapCache.dataUrl;
  } else {
    dataUrl = _hmGenerate(fp, ppm, bounds, antennasData);
    _heatmapCache = { stamp, dataUrl, bounds, mode: displaySettings.showCoverage };
  }
  if (!dataUrl) return;

  // Insert SVG <image> into persistent coverageLayer
  const coverageG = document.createElementNS(svgNS, 'g');
  coverageG.setAttribute('class', 'coverage-layer');
  coverageG.style.pointerEvents = 'none';

  const img = document.createElementNS(svgNS, 'image');
  img.setAttribute('href', dataUrl);
  img.setAttribute('x', bounds.x);
  img.setAttribute('y', bounds.y);
  img.setAttribute('width', bounds.width);
  img.setAttribute('height', bounds.height);
  img.setAttribute('style', 'image-rendering:auto;');
  img.setAttribute('preserveAspectRatio', 'none');
  coverageG.appendChild(img);

  // -85dBm design radius circles (red dashed) — per-antenna n
  for (const ant of antennasData) {
    const designR = Math.pow(10, (_HM_RX1M - _HM_DESIGN) / (10 * ant.n)) * ppm;
    const circle = document.createElementNS(svgNS, 'circle');
    circle.setAttribute('cx', ant.cx);
    circle.setAttribute('cy', ant.cy);
    circle.setAttribute('r', designR);
    circle.setAttribute('fill', 'none');
    circle.setAttribute('stroke', '#ef4444');
    circle.setAttribute('stroke-opacity', '0.35');
    circle.setAttribute('stroke-width', '1');
    circle.setAttribute('stroke-dasharray', '6 4');
    coverageG.appendChild(circle);
  }

  coverageLayer.appendChild(coverageG);
}

// ====== FLOOR ROUTES ======
function renderFloorRoutes(fp){
  if(!fp.routes||!fp.routes.length)return;
  const layer=document.getElementById('edgesLayer');
  const ehl=document.getElementById('edgeHitLayer');
  const labelEls=[];

  fp.routes.forEach(route=>{
    const srcNode=nodes.find(n=>n.id===route.sourceNodeId);
    const tgtNode=nodes.find(n=>n.id===route.targetNodeId);
    if(!srcNode||!tgtNode)return;

    // Use placement coords for path calculation
    const srcPl=fp.placements.find(p=>p.node_id===route.sourceNodeId);
    const tgtPl=fp.placements.find(p=>p.node_id===route.targetNodeId);
    if(!srcPl||!tgtPl)return;
    // Auto-pick best ports based on relative position if not user-set
    const rMode=route.routeMode||'ortho3';
    const autoP=(!route._userPorts)?findBestPort(srcPl,tgtPl,srcNode.w||NODE_SIZE,rMode):null;
    const edgeLike={sourceId:route.sourceNodeId,targetId:route.targetNodeId,sourcePort:autoP?autoP.srcPort:(route.sourcePort||'right'),targetPort:autoP?autoP.tgtPort:(route.targetPort||'left'),routeMode:rMode,midPos:route.midPos,waypoints:route.waypoints};
    // Temporarily set node positions to placement coords for path calc
    const _sx=srcNode.x,_sy=srcNode.y,_tx=tgtNode.x,_ty=tgtNode.y;
    srcNode.x=srcPl.x;srcNode.y=srcPl.y;tgtNode.x=tgtPl.x;tgtNode.y=tgtPl.y;
    const result=buildEdgePath(edgeLike);
    srcNode.x=_sx;srcNode.y=_sy;tgtNode.x=_tx;tgtNode.y=_ty;
    if(!result||!result.path)return;

    const comp=getFloorZoomCompensation();
    const w=getEffectiveCableWidth(route.width)*comp;const rc=getEffectiveCableColor(route.color);
    const isSelected=selectedRouteId===route.id;
    // Hit area — placed on edgeHitLayer (above nodesLayer, easy to click)
    const hitPath=document.createElementNS('http://www.w3.org/2000/svg','path');
    hitPath.setAttribute('class','edge-hit');hitPath.setAttribute('d',result.path);
    hitPath.setAttribute('stroke-width',Math.max(w+16,24));
    hitPath.style.pointerEvents='stroke';
    hitPath.addEventListener('click',ev=>{ev.stopPropagation();selectFloorRoute(route.id)});
    ehl.appendChild(hitPath);

    const path=document.createElementNS('http://www.w3.org/2000/svg','path');
    path.setAttribute('class','edge-line');path.setAttribute('d',result.path);
    path.setAttribute('stroke',rc);path.setAttribute('stroke-width',isSelected?w+1.5:w);
    if(route.dash){
      if(comp!==1){
        path.setAttribute('stroke-dasharray',
          route.dash.split(/[\s,]+/).map(v=>parseFloat(v)*comp).join(' '));
      }else{
        path.setAttribute('stroke-dasharray',route.dash);
      }
    }
    path.setAttribute('stroke-linecap','round');path.setAttribute('stroke-linejoin','round');
    if(isSelected)path.setAttribute('filter','url(#glow)');
    layer.appendChild(path);

    // Build display text: label + length
    const showLabel=route.label&&displaySettings.cableLabel;
    const ppm=fp.calibration&&fp.calibration.px_per_meter;
    let lengthStr='';
    if(displaySettings.cableLength&&ppm){
      const tmpSvg=document.createElementNS('http://www.w3.org/2000/svg','path');
      tmpSvg.setAttribute('d',result.path);
      const pxLen=tmpSvg.getTotalLength();
      const meters=pxLen/ppm;
      lengthStr=meters>=1?meters.toFixed(1)+'m':Math.round(meters*100)+'cm';
    }
    const parts=[];if(showLabel)parts.push(route.label);if(lengthStr)parts.push(lengthStr);
    if(parts.length){
      const txt=parts.join(' · ');
      const mid=getPathMidpoint(result,edgeLike);
      const baseTl=txt.length*7+16;
      if(comp!==1){
        const tl=baseTl*comp,lh=18*comp;
        const bg=document.createElementNS('http://www.w3.org/2000/svg','rect');
        bg.setAttribute('class','edge-label-bg');bg.setAttribute('x',mid.x-tl/2);bg.setAttribute('y',mid.y-lh/2);
        bg.setAttribute('width',tl);bg.setAttribute('height',lh);bg.setAttribute('rx',4*comp);
        bg.style.cursor='pointer';
        bg.addEventListener('click',ev=>{ev.stopPropagation();selectFloorRoute(route.id)});
        labelEls.push(bg);
        const lbl=document.createElementNS('http://www.w3.org/2000/svg','text');
        lbl.setAttribute('class','edge-label');lbl.setAttribute('x',mid.x);lbl.setAttribute('y',mid.y);
        lbl.setAttribute('font-size',12*comp);
        lbl.setAttribute('fill',rc);lbl.textContent=txt;
        lbl.style.cursor='pointer';
        lbl.style.pointerEvents='auto';
        lbl.addEventListener('click',ev=>{ev.stopPropagation();selectFloorRoute(route.id)});
        labelEls.push(lbl);
      }else{
        const tl=baseTl;
        const bg=document.createElementNS('http://www.w3.org/2000/svg','rect');
        bg.setAttribute('class','edge-label-bg');bg.setAttribute('x',mid.x-tl/2);bg.setAttribute('y',mid.y-9);
        bg.setAttribute('width',tl);bg.setAttribute('height',18);bg.setAttribute('rx',4);
        bg.style.cursor='pointer';
        bg.addEventListener('click',ev=>{ev.stopPropagation();selectFloorRoute(route.id)});
        labelEls.push(bg);
        const lbl=document.createElementNS('http://www.w3.org/2000/svg','text');
        lbl.setAttribute('class','edge-label');lbl.setAttribute('x',mid.x);lbl.setAttribute('y',mid.y);
        lbl.setAttribute('fill',rc);lbl.textContent=txt;
        lbl.style.cursor='pointer';
        lbl.style.pointerEvents='auto';
        lbl.addEventListener('click',ev=>{ev.stopPropagation();selectFloorRoute(route.id)});
        labelEls.push(lbl);
      }
    }
  });
  // Append labels after all hit paths so labels stay on top and clickable
  labelEls.forEach(el=>ehl.appendChild(el));
}

// ====== DROP-TO-INSERT (drag device onto cable) ======

function pointToSegmentDist(px,py,ax,ay,bx,by){
  const dx=bx-ax,dy=by-ay,lenSq=dx*dx+dy*dy;
  if(lenSq===0)return Math.hypot(px-ax,py-ay);
  const t=Math.max(0,Math.min(1,(dx*(px-ax)+dy*(py-ay))/lenSq));
  return Math.hypot(px-(ax+t*dx),py-(ay+t*dy));
}

function getRoutePathPoints(route,fp){
  const srcNode=nodes.find(n=>n.id===route.sourceNodeId);
  const tgtNode=nodes.find(n=>n.id===route.targetNodeId);
  if(!srcNode||!tgtNode)return null;
  const srcPl=fp.placements.find(p=>p.node_id===route.sourceNodeId);
  const tgtPl=fp.placements.find(p=>p.node_id===route.targetNodeId);
  if(!srcPl||!tgtPl)return null;
  const rMode=route.routeMode||'ortho3';
  const autoP=(!route._userPorts)?findBestPort(srcPl,tgtPl,srcNode.w||NODE_SIZE,rMode):null;
  const edgeLike={sourceId:route.sourceNodeId,targetId:route.targetNodeId,
    sourcePort:autoP?autoP.srcPort:(route.sourcePort||'right'),
    targetPort:autoP?autoP.tgtPort:(route.targetPort||'left'),
    routeMode:rMode,midPos:route.midPos,waypoints:route.waypoints};
  const _sx=srcNode.x,_sy=srcNode.y,_tx=tgtNode.x,_ty=tgtNode.y;
  srcNode.x=srcPl.x;srcNode.y=srcPl.y;tgtNode.x=tgtPl.x;tgtNode.y=tgtPl.y;
  const result=buildEdgePath(edgeLike);
  srcNode.x=_sx;srcNode.y=_sy;tgtNode.x=_tx;tgtNode.y=_ty;
  if(!result||!result.path)return null;
  if(result.pts)return result.pts;
  // Straight or bezier — approximate with start/end
  return[result.sp,result.tp];
}

function tryInsertIntoRoute(nodeId,viewId){
  if(!nodeId)return;
  const nd=nodes.find(n=>n.id===nodeId);if(!nd)return;
  // Check if device is a splitter or coupler
  const sub=nd.subcategoryId?SUBCATEGORIES[nd.subcategoryId]:null;
  if(!sub)return;
  const ik=sub.iconKey||'';
  let isSplitterOrCoupler=false;
  if(ik==='splitter_2'||ik==='splitter_3'||ik==='coupler')isSplitterOrCoupler=true;
  if(!isSplitterOrCoupler){
    // Also check SUBCAT_ICON_MAP via sub.name
    for(const k in SUBCAT_ICON_MAP){
      if((sub.name||'').includes(k)){
        const mapped=SUBCAT_ICON_MAP[k];
        if(mapped==='splitter_2'||mapped==='splitter_3'||mapped==='coupler'){isSplitterOrCoupler=true;break}
      }
    }
  }
  if(!isSplitterOrCoupler)return;

  const fp=getFloorPlan(viewId);if(!fp||!fp.routes||!fp.routes.length)return;
  const pl=fp.placements.find(p=>p.node_id===nodeId);if(!pl)return;
  const dropCx=pl.x+(nd.w||NODE_SIZE)/2,dropCy=pl.y+(nd.h||NODE_SIZE)/2;

  let bestRoute=null,bestDist=Infinity,bestSegIdx=-1;
  fp.routes.forEach(route=>{
    // Skip routes already connected to this node
    if(route.sourceNodeId===nodeId||route.targetNodeId===nodeId)return;
    const pts=getRoutePathPoints(route,fp);if(!pts||pts.length<2)return;
    for(let i=0;i<pts.length-1;i++){
      const d=pointToSegmentDist(dropCx,dropCy,pts[i].x,pts[i].y,pts[i+1].x,pts[i+1].y);
      if(d<bestDist){bestDist=d;bestRoute=route;bestSegIdx=i}
    }
  });
  if(!bestRoute||bestDist>40)return;

  // Found a close route — insert this device
  pushHistory();

  const origRoute=bestRoute;
  const origEdgeId=origRoute.linked_edge_id;
  const origSrc=origRoute.sourceNodeId,origTgt=origRoute.targetNodeId;
  const cableProps={cableType:origRoute.cableType,color:origRoute.color,width:origRoute.width,dash:origRoute.dash,label:origRoute.label,routeMode:origRoute.routeMode||'ortho3'};

  // Calculate best ports for the two new connections
  const srcPl=fp.placements.find(p=>p.node_id===origSrc);
  const tgtPl=fp.placements.find(p=>p.node_id===origTgt);
  const nSize=nd.w||NODE_SIZE;
  const rMode=cableProps.routeMode;
  const ports1=findBestPort(srcPl||{x:0,y:0},pl,nSize,rMode);
  const ports2=findBestPort(pl,tgtPl||{x:0,y:0},nSize,rMode);

  // Remove original topology edge
  const origEdgeIdx=edges.findIndex(e=>e.id===origEdgeId);
  if(origEdgeIdx>=0)edges.splice(origEdgeIdx,1);

  // Remove original floor route
  const origRouteIdx=fp.routes.indexOf(origRoute);
  if(origRouteIdx>=0)fp.routes.splice(origRouteIdx,1);

  // Split waypoints: pts=[sp, wp0, wp1, ..., wpN, tp], waypoints[i]=pts[i+1]
  const origWp=origRoute.waypoints;
  const wp1=origWp&&origWp.length?origWp.slice(0,bestSegIdx):undefined;
  const wp2=origWp&&origWp.length?origWp.slice(bestSegIdx):undefined;

  // Create two new topology edges
  const edge1={id:edgeIdCounter++,sourceId:origSrc,sourcePort:ports1.srcPort,targetId:nodeId,targetPort:ports1.tgtPort,
    cableType:cableProps.cableType,color:cableProps.color,width:cableProps.width,dash:cableProps.dash,label:cableProps.label,routeMode:rMode,hideLabel:false};
  const edge2={id:edgeIdCounter++,sourceId:nodeId,sourcePort:ports2.srcPort,targetId:origTgt,targetPort:ports2.tgtPort,
    cableType:cableProps.cableType,color:cableProps.color,width:cableProps.width,dash:cableProps.dash,label:cableProps.label,routeMode:rMode,hideLabel:false};
  edges.push(edge1,edge2);

  // Create two new floor routes
  const route1={id:routeIdCounter++,sourceNodeId:origSrc,targetNodeId:nodeId,sourcePort:ports1.srcPort,targetPort:ports1.tgtPort,
    cableType:cableProps.cableType,color:cableProps.color,width:cableProps.width,dash:cableProps.dash,label:cableProps.label,
    routeMode:rMode,linked_edge_id:edge1.id,_userPorts:false,waypoints:wp1&&wp1.length?wp1:undefined};
  const route2={id:routeIdCounter++,sourceNodeId:nodeId,targetNodeId:origTgt,sourcePort:ports2.srcPort,targetPort:ports2.tgtPort,
    cableType:cableProps.cableType,color:cableProps.color,width:cableProps.width,dash:cableProps.dash,label:cableProps.label,
    routeMode:rMode,linked_edge_id:edge2.id,_userPorts:false,waypoints:wp2&&wp2.length?wp2:undefined};
  fp.routes.push(route1,route2);

  hasUnsavedChanges=true;
  renderAll();
  showToast(_t('已将设备插入走线'));
}

// ====== FLOOR ROUTE CREATION ======
let routeIdCounter=300,pendingFloorRoute=null;


function createFloorRoute(srcId,srcPort,tgtId,tgtPort,cx,cy){
  const fp=getFloorPlan(currentView);if(!fp)return;
  pushHistory();
  // Create topology edge
  const _wp=polylineWaypoints.length?[...polylineWaypoints]:undefined;
  const defEdge={id:edgeIdCounter++,sourceId:srcId,sourcePort:srcPort,targetId:tgtId,targetPort:tgtPort,cableType:null,color:'#94a3b8',width:1.5,dash:'6 4',label:'',routeMode:defaultRouteMode,hideLabel:false};
  edges.push(defEdge);
  // Create floor route linked to this edge
  if(!fp.routes)fp.routes=[];
  const route={id:routeIdCounter++,sourceNodeId:srcId,targetNodeId:tgtId,sourcePort:srcPort,targetPort:tgtPort,cableType:null,routeMode:'ortho3',color:'#94a3b8',width:1.5,dash:'6 4',label:'',linked_edge_id:defEdge.id,_userPorts:true,waypoints:_wp};
  fp.routes.push(route);
  polylineWaypoints=[];
  pendingFloorRoute=route.id;pendingEdge=defEdge.id;
  showConnTypePopup(cx,cy);
}

// Override setConnType to handle floor routes (overrides topology.js version; depends on load order)
function setConnType(cableKey){
  if(pendingFloorRoute!==null){
    const fp=getFloorPlan(currentView);
    if(fp){
      const route=fp.routes.find(r=>r.id===pendingFloorRoute);
      if(route){
        const c=CABLE_TYPES[cableKey];
        route.cableType=cableKey;route.color=c.color;route.width=c.width;route.dash=c.dash;route.label=_m(c.shortName);
      }
    }
    pendingFloorRoute=null;
  }
  // Also set the edge type
  if(pendingEdge!==null){
    const edge=edges.find(e=>e.id===pendingEdge);
    if(edge){const c=CABLE_TYPES[cableKey];edge.cableType=cableKey;edge.color=c.color;edge.width=c.width;edge.dash=c.dash;edge.label=_m(c.shortName)}
    pendingEdge=null;
  }
  hasUnsavedChanges=true;renderAll();
  document.getElementById('connTypePopup').style.display='none';
}

// ====== FLOOR ROUTE MID-HANDLES ======
let isDraggingFloorMid=false,dragFloorMidRouteId=null,floorMidDragMoved=false;
// ====== FLOOR ROUTE ENDPOINT RECONNECT ======
let isReconnectingFloor=false,reconnectFloorRouteId=null,reconnectFloorEnd='',reconnectFloorFixedPos=null;
// ====== SNAP-TO-NODE STATE ======
let snapTargetNodeId=null,snapTargetPort=null,snapTargetPos=null;

/** Detect nearest node for snap-to during connect/reconnect (works in both topology and floor plan views) */
function detectConnSnap(mx,my){
  snapTargetNodeId=null;snapTargetPort=null;snapTargetPos=null;
  const isFloor=currentView!=='topology';
  const fp=isFloor&&typeof getFloorPlan==='function'?getFloorPlan(currentView):null;
  const SNAP_R=NODE_SIZE*1.5;
  let bestDist=SNAP_R,bestPos=null,bestNode=null;

  if(isFloor){
    // Floor plan: use placement positions
    if(!fp||!fp.placements)return;
    fp.placements.forEach(pl=>{
      if(pl.node_id===connSourceId)return;
      const n=nodes.find(nd=>nd.id===pl.node_id);if(!n)return;
      const cx=pl.x+n.w/2,cy=pl.y+n.h/2;
      const d=Math.sqrt((mx-cx)*(mx-cx)+(my-cy)*(my-cy));
      if(d<bestDist){bestDist=d;bestPos={x:pl.x,y:pl.y};bestNode=n}
    });
  }else{
    // Topology: use node positions directly
    nodes.forEach(n=>{
      if(n.id===connSourceId)return;
      const cx=n.x+n.w/2,cy=n.y+n.h/2;
      const d=Math.sqrt((mx-cx)*(mx-cx)+(my-cy)*(my-cy));
      if(d<bestDist){bestDist=d;bestPos={x:n.x,y:n.y};bestNode=n}
    });
  }
  if(!bestPos||!bestNode)return;
  // Find best port facing towards mouse
  const srcPl={x:mx-NODE_SIZE/2,y:my-NODE_SIZE/2};
  const bp=findBestPort(srcPl,bestPos,bestNode.w||NODE_SIZE,'bezier');
  snapTargetNodeId=bestNode.id;snapTargetPort=bp.tgtPort;
  snapTargetPos=getPortPos({x:bestPos.x,y:bestPos.y,w:bestNode.w,h:bestNode.h},bp.tgtPort);
}

let dragFloorWaypointIdx=null;  // index of floor route waypoint being dragged
function renderFloorMidHandles(fp){
  if(!fp.routes||!selectedRouteId)return;
  const route=fp.routes.find(r=>r.id===selectedRouteId);
  if(!route)return;

  const srcNode=nodes.find(n=>n.id===route.sourceNodeId);
  const tgtNode=nodes.find(n=>n.id===route.targetNodeId);
  if(!srcNode||!tgtNode)return;
  const srcPl=fp.placements.find(p=>p.node_id===route.sourceNodeId);
  const tgtPl=fp.placements.find(p=>p.node_id===route.targetNodeId);
  if(!srcPl||!tgtPl)return;

  const layer=document.getElementById('handlesLayer');

  // Polyline waypoint handles for floor routes
  if(route.waypoints&&route.waypoints.length){
    route.waypoints.forEach((wp,idx)=>{
      const g=document.createElementNS('http://www.w3.org/2000/svg','g');g.setAttribute('class','mid-handle');g.style.cursor='grab';
      const grip=document.createElementNS('http://www.w3.org/2000/svg','circle');grip.setAttribute('class','mid-handle-grip');
      grip.setAttribute('cx',wp.x);grip.setAttribute('cy',wp.y);grip.setAttribute('r',5);g.appendChild(grip);
      g.addEventListener('mousedown',ev=>{ev.stopPropagation();isDraggingFloorMid=true;floorMidDragMoved=false;dragFloorMidRouteId=route.id;dragFloorWaypointIdx=idx});
      layer.appendChild(g);
    });
    return;
  }

  // Ortho3 mid-handle (original logic)
  if(route.routeMode!=='ortho3')return;

  // Build path with placement coords
  const _sx=srcNode.x,_sy=srcNode.y,_tx=tgtNode.x,_ty=tgtNode.y;
  srcNode.x=srcPl.x;srcNode.y=srcPl.y;tgtNode.x=tgtPl.x;tgtNode.y=tgtPl.y;
  const autoP=(!route._userPorts)?findBestPort(srcPl,tgtPl,srcNode.w||NODE_SIZE,route.routeMode||'ortho3'):null;
  const edgeLike={sourceId:route.sourceNodeId,targetId:route.targetNodeId,sourcePort:autoP?autoP.srcPort:(route.sourcePort||'right'),targetPort:autoP?autoP.tgtPort:(route.targetPort||'left'),routeMode:route.routeMode||'ortho3',midPos:route.midPos};
  const result=buildEdgePath(edgeLike);
  srcNode.x=_sx;srcNode.y=_sy;tgtNode.x=_tx;tgtNode.y=_ty;
  if(!result||!result.c1||!result.c2)return;

  const g=document.createElementNS('http://www.w3.org/2000/svg','g');
  g.setAttribute('class','mid-handle');
  if(result.isH){
    g.style.cursor='ew-resize';
    const bar=document.createElementNS('http://www.w3.org/2000/svg','line');bar.setAttribute('class','mid-handle-bar');
    bar.setAttribute('x1',result.c1.x);bar.setAttribute('y1',result.c1.y);bar.setAttribute('x2',result.c2.x);bar.setAttribute('y2',result.c2.y);g.appendChild(bar);
    const midY=(result.c1.y+result.c2.y)/2;const grip=document.createElementNS('http://www.w3.org/2000/svg','circle');
    grip.setAttribute('class','mid-handle-grip');grip.setAttribute('cx',result.c1.x);grip.setAttribute('cy',midY);g.appendChild(grip);
  }else{
    g.style.cursor='ns-resize';
    const bar=document.createElementNS('http://www.w3.org/2000/svg','line');bar.setAttribute('class','mid-handle-bar');
    bar.setAttribute('x1',result.c1.x);bar.setAttribute('y1',result.c1.y);bar.setAttribute('x2',result.c2.x);bar.setAttribute('y2',result.c2.y);g.appendChild(bar);
    const midX=(result.c1.x+result.c2.x)/2;const grip=document.createElementNS('http://www.w3.org/2000/svg','circle');
    grip.setAttribute('class','mid-handle-grip');grip.setAttribute('cx',midX);grip.setAttribute('cy',result.c1.y);g.appendChild(grip);
  }
  g.addEventListener('mousedown',e=>{e.stopPropagation();isDraggingFloorMid=true;floorMidDragMoved=false;dragFloorMidRouteId=route.id;dragFloorWaypointIdx=null});
  layer.appendChild(g);
}

// ====== FLOOR ROUTE ENDPOINT HANDLES (for reconnect drag) ======
function renderFloorRouteEndpoints(fp){
  if(!fp.routes||selectedRouteId===null||isReconnectingFloor)return;
  const route=fp.routes.find(r=>r.id===selectedRouteId);if(!route)return;
  const srcN=nodes.find(n=>n.id===route.sourceNodeId),tgtN=nodes.find(n=>n.id===route.targetNodeId);if(!srcN||!tgtN)return;
  const srcPl=fp.placements.find(p=>p.node_id===route.sourceNodeId),tgtPl=fp.placements.find(p=>p.node_id===route.targetNodeId);if(!srcPl||!tgtPl)return;
  const rMode=route.routeMode||'ortho3',autoP=(!route._userPorts)?findBestPort(srcPl,tgtPl,srcN.w||NODE_SIZE,rMode):null;
  const effSrc=autoP?autoP.srcPort:(route.sourcePort||'right'),effTgt=autoP?autoP.tgtPort:(route.targetPort||'left');
  const mkPos=(pl,n,port)=>getPortPos({x:pl.x,y:pl.y,w:n.w,h:n.h},port);
  const sPos=mkPos(srcPl,srcN,effSrc),tPos=mkPos(tgtPl,tgtN,effTgt);
  const layer=document.getElementById('nodesLayer'),clr=route.color||'#60a5fa';
  [['source',sPos,effTgt,tgtPl,tgtN],['target',tPos,effSrc,srcPl,srcN]].forEach(([end,pos,fixPort,fixPl,fixN])=>{
    const ring=document.createElementNS('http://www.w3.org/2000/svg','circle');
    ring.setAttribute('cx',pos.x);ring.setAttribute('cy',pos.y);ring.setAttribute('r',10);
    ring.setAttribute('fill','none');ring.setAttribute('stroke',clr);ring.setAttribute('stroke-width','2');ring.setAttribute('opacity','0.5');ring.style.pointerEvents='none';
    const anim=document.createElementNS('http://www.w3.org/2000/svg','animate');
    anim.setAttribute('attributeName','r');anim.setAttribute('values','8;12;8');anim.setAttribute('dur','1.5s');anim.setAttribute('repeatCount','indefinite');
    ring.appendChild(anim);layer.appendChild(ring);
    const c=document.createElementNS('http://www.w3.org/2000/svg','circle');
    c.setAttribute('cx',pos.x);c.setAttribute('cy',pos.y);c.setAttribute('r',7);
    c.setAttribute('fill',clr);c.setAttribute('fill-opacity','0.3');c.setAttribute('stroke','#fff');c.setAttribute('stroke-width','2');c.style.cursor='grab';
    c.addEventListener('mousedown',ev=>{ev.stopPropagation();
      isReconnectingFloor=true;reconnectFloorRouteId=route.id;reconnectFloorEnd=end;
      // Use nearest waypoint as guide anchor (visually closer than the opposite endpoint)
      if(route.waypoints&&route.waypoints.length){
        reconnectFloorFixedPos=end==='source'?{...route.waypoints[0]}:{...route.waypoints[route.waypoints.length-1]};
      }else{
        reconnectFloorFixedPos=mkPos(fixPl,fixN,fixPort);
      }
      connSourceId=end==='source'?route.targetNodeId:route.sourceNodeId;connSourcePort=fixPort;
      isConnecting=true;renderAll();
    });layer.appendChild(c);
  });
}
function renderFloorReconnectLine(mx,my){if(!reconnectFloorFixedPos)return;const p=reconnectFloorFixedPos;const comp=getTempEdgeZoomCompensation();const sw=3*comp;const bsw=5*comp;const da=`${8*comp} ${4*comp}`;document.getElementById('tempLayer').innerHTML=`<line x1="${p.x}" y1="${p.y}" x2="${mx}" y2="${my}" style="stroke:rgba(255,255,255,0.6);stroke-width:${bsw};stroke-dasharray:${da};fill:none"/><line class="edge-temp" x1="${p.x}" y1="${p.y}" x2="${mx}" y2="${my}" style="stroke:#3b82f6;stroke-width:${sw};stroke-dasharray:${da};fill:none"/>`}

/** Render highlight ring around snap target node (appended to tempLayer, works in both views) */
function renderConnSnapHighlight(){
  const old=document.getElementById('snapHighlight');if(old)old.remove();
  if(!snapTargetNodeId||!snapTargetPos)return;
  const n=nodes.find(nd=>nd.id===snapTargetNodeId);if(!n)return;
  const isFloor=currentView!=='topology';
  let cx,cy;
  if(isFloor){
    const fp=typeof getFloorPlan==='function'?getFloorPlan(currentView):null;if(!fp)return;
    const pl=fp.placements.find(p=>p.node_id===snapTargetNodeId);if(!pl)return;
    cx=pl.x+n.w/2;cy=pl.y+n.h/2;
  }else{
    cx=n.x+n.w/2;cy=n.y+n.h/2;
  }
  const comp=isFloor&&typeof getFloorZoomCompensation==='function'?getFloorZoomCompensation():1;
  const r=(n.w/2+14)*comp;
  const g=document.createElementNS('http://www.w3.org/2000/svg','g');g.id='snapHighlight';
  g.innerHTML=`<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="#3b82f6" stroke-width="${2.5*comp}" stroke-opacity="0.7"><animate attributeName="r" values="${r};${r+4*comp};${r}" dur="1s" repeatCount="indefinite"/><animate attributeName="stroke-opacity" values="0.7;0.3;0.7" dur="1s" repeatCount="indefinite"/></circle>`
    +`<circle cx="${snapTargetPos.x}" cy="${snapTargetPos.y}" r="${6*comp}" fill="#3b82f6" fill-opacity="0.8" stroke="#fff" stroke-width="${2*comp}"/>`;
  document.getElementById('tempLayer').appendChild(g);
}

function selectFloorRoute(routeId){
  selectedRouteId=routeId;selectedAreaId=null;selectedNodeIds=new Set();selectedEdgeId=null;
  showFloorRouteProps(routeId);renderAll();highlightConnectedInPanel(null);
}

function showFloorRouteProps(routeId){
  const fp=getFloorPlan(currentView);if(!fp)return;
  const route=fp.routes.find(r=>r.id===routeId);if(!route)return;
  const srcN=nodes.find(n=>n.id===route.sourceNodeId);
  const tgtN=nodes.find(n=>n.id===route.targetNodeId);
  const panel=document.getElementById('propsPanel');
  panel.classList.add('visible');
  document.getElementById('propsTitle').textContent=_t('走线属性');
  let cableOpts='';
  [...new Set(Object.values(CABLE_TYPES).map(c=>_m(c.category)))].forEach(cat=>{
    cableOpts+=`<optgroup label="${cat}">`;
    Object.entries(CABLE_TYPES).filter(([,ct])=>_m(ct.category)===cat).forEach(([key,ct])=>{
      cableOpts+=`<option value="${key}" ${route.cableType===key?'selected':''}>${_m(ct.name)}</option>`;
    });cableOpts+='</optgroup>';
  });
  const rMode=route.routeMode||'ortho3';
  const rPrev=(mode)=>{const act=rMode===mode?'active':'';const clr=act?'#60a5fa':'var(--text-muted)';const svgs={bezier:`<svg viewBox="0 0 28 16"><path d="M2 14 C10 14 18 2 26 2" fill="none" stroke="${clr}" stroke-width="2"/></svg>`,ortho2:`<svg viewBox="0 0 28 16"><path d="M2 14 L2 2 L26 2" fill="none" stroke="${clr}" stroke-width="2" stroke-linejoin="round"/></svg>`,ortho3:`<svg viewBox="0 0 28 16"><path d="M2 14 L14 14 L14 2 L26 2" fill="none" stroke="${clr}" stroke-width="2" stroke-linejoin="round"/></svg>`,straight:`<svg viewBox="0 0 28 16"><line x1="2" y1="14" x2="26" y2="2" stroke="${clr}" stroke-width="2"/></svg>`};return`<div class="route-mode-btn ${act}" onclick="updateFloorRouteMode(${routeId},'${mode}')">${svgs[mode]}<span>${{bezier:_t('弧线'),ortho2:_t('一折'),ortho3:_t('二折'),straight:_t('直线')}[mode]}</span></div>`};
  const portOpts=['top','right','bottom','left','top-left','top-right','bottom-left','bottom-right'];
  const portLabel={
    top:{zh:'上',en:'Top'}, right:{zh:'右',en:'Right'},
    bottom:{zh:'下',en:'Bottom'}, left:{zh:'左',en:'Left'},
    'top-left':{zh:'左上',en:'Top-Left'}, 'top-right':{zh:'右上',en:'Top-Right'},
    'bottom-left':{zh:'左下',en:'Btm-Left'}, 'bottom-right':{zh:'右下',en:'Btm-Right'}
  };
  // Show effective ports (auto-picked or user-set)
  const srcPl=fp.placements.find(p=>p.node_id===route.sourceNodeId);
  const tgtPl=fp.placements.find(p=>p.node_id===route.targetNodeId);
  const autoP=(!route._userPorts&&srcPl&&tgtPl)?findBestPort(srcPl,tgtPl,(srcN?srcN.w:null)||NODE_SIZE,route.routeMode||'ortho3'):null;
  const effSrcPort=autoP?autoP.srcPort:(route.sourcePort||'right');
  const effTgtPort=autoP?autoP.tgtPort:(route.targetPort||'left');
  const srcPortSel=portOpts.map(p=>`<option value="${p}" ${effSrcPort===p?'selected':''}>${_m(portLabel[p])}</option>`).join('');
  const tgtPortSel=portOpts.map(p=>`<option value="${p}" ${effTgtPort===p?'selected':''}>${_m(portLabel[p])}</option>`).join('');
  const autoTag=!route._userPorts?`<span style="font-size:10px;color:#22c55e;margin-left:4px">(${_t('自动')})</span>`:`<span style="font-size:10px;color:var(--text-muted);margin-left:4px;cursor:pointer" onclick="resetFloorRoutePort(${routeId})">[${_t('重置为自动')}]</span>`;
  const srcIsNew=!!(srcN&&srcN.floor_id),tgtIsNew=!!(tgtN&&tgtN.floor_id),isNewRoute=srcIsNew||tgtIsNew;
  document.getElementById('propsContent').innerHTML=`
    <div class="props-field"><span class="props-label">${_t('线缆类型')}</span><div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">${cableLineSVG(route.cableType,40,12)}<span style="font-size:12px;color:${route.color};">${(()=>{const _ct=CABLE_TYPES[route.cableType];return _ct?_m(_ct.name):_t('未设置')})()} </span></div>
    <select class="props-select" onchange="updateFloorRouteCableType(${routeId},this.value)">${cableOpts}</select></div>
    <div class="props-section">${_t('路由模式')}</div>
    <div class="props-field"><div class="route-mode-btns">${rPrev('straight')}${rPrev('ortho2')}${rPrev('ortho3')}${rPrev('bezier')}</div></div>
    ${rMode==='ortho3'?`<div style="font-size:10px;color:var(--text-muted);padding:2px 0;">${_t('提示：选中后拖动中间段调整位置')}</div>`:''}
    ${isNewRoute?`<div class="props-section">${_t('线路样式')}</div>
    <div class="props-field"><span class="props-label">${_t('颜色')}</span><div class="props-row"><input type="color" class="props-color" value="${route.color||'#3b82f6'}" oninput="updateFloorRouteProp(${routeId},'color',this.value);this.nextElementSibling.value=this.value"><input class="props-input" style="flex:1;font-family:monospace;font-size:11px;" value="${route.color||'#3b82f6'}" oninput="updateFloorRouteProp(${routeId},'color',this.value);this.previousElementSibling.value=this.value"></div></div>
    <div class="props-field"><span class="props-label">${_t('虚线样式')}</span><select class="props-select" onchange="updateFloorRouteProp(${routeId},'dash',this.value)"><option value="" ${!route.dash?'selected':''}>${_t('实线')}</option><option value="8 4" ${route.dash==='8 4'?'selected':''}>${_t('长虚线')}</option><option value="4 4" ${route.dash==='4 4'?'selected':''}>${_t('中虚线')}</option><option value="2 4" ${route.dash==='2 4'?'selected':''}>${_t('短虚线')}</option><option value="10 3 2 3" ${route.dash==='10 3 2 3'?'selected':''}>${_t('点划线')}</option></select></div>`:''}
    <div class="props-section">${_t('标签')}</div>
    <div class="props-field"><input class="props-input" value="${route.label||''}" oninput="updateFloorRouteProp(${routeId},'label',this.value)"></div>
    <div class="props-field"><label style="display:flex;align-items:center;gap:8px;cursor:pointer;"><input type="checkbox" ${route.hideLabel?'checked':''} onchange="updateFloorRouteProp(${routeId},'hideLabel',this.checked)"><span class="props-label" style="margin:0;">${_t('隐藏标签')}</span></label></div>
    <div class="props-section">${_t('连接点')} ${autoTag}</div>
    <div class="props-field"><span class="props-label">${_t('起点')}: ${srcN?srcN.name:'?'}</span><select class="props-select" onchange="updateFloorRoutePort(${routeId},'source',this.value)">${srcPortSel}</select></div>
    <div class="props-field"><span class="props-label">${_t('终点')}: ${tgtN?tgtN.name:'?'}</span><select class="props-select" onchange="updateFloorRoutePort(${routeId},'target',this.value)">${tgtPortSel}</select></div>
    ${(()=>{const len=calculateFloorRouteLength(route,fp);if(!len)return'';if(len.meters!==null)return`<div class="props-field"><span class="props-label">${_t('预估长度')}</span><span style="font-size:13px;font-weight:600;">${len.meters.toFixed(1)}m</span> <span style="font-size:10px;color:var(--text-muted);">(${Math.round(len.px)}px)</span></div>`;return`<div class="props-field"><span class="props-label">${_t('路径长度')}</span><span style="font-size:13px;color:var(--text-muted);">${Math.round(len.px)}px</span> <span style="font-size:10px;color:#f59e0b;">(${_t('未标定')})</span></div>`})()}
    ${route.linked_edge_id&&!isNewRoute?`<button class="btn-delete" style="border-color:#64748b;color:#64748b;" onclick="revertFloorRoute(${routeId})">${_t('恢复自动走线')}</button>`:`<button class="btn-delete" onclick="deleteFloorRoute(${routeId})">${_t('删除走线')}</button>`}`;
}

function updateFloorRouteCableType(routeId,cableKey){
  const fp=getFloorPlan(currentView);if(!fp)return;
  const route=fp.routes.find(r=>r.id===routeId);if(!route)return;
  const c=CABLE_TYPES[cableKey];if(!c)return;
  pushHistory();route.cableType=cableKey;route.color=c.color;route.width=c.width;route.dash=c.dash;route.label=_m(c.shortName);
  // Sync to linked edge
  if(route.linked_edge_id){const edge=edges.find(e=>e.id===route.linked_edge_id);if(edge){edge.cableType=cableKey;edge.color=c.color;edge.width=c.width;edge.dash=c.dash;edge.label=_m(c.shortName)}}
  hasUnsavedChanges=true;renderAll();showFloorRouteProps(routeId);
}

function updateFloorRouteMode(routeId,mode){
  const fp=getFloorPlan(currentView);if(!fp)return;
  const route=fp.routes.find(r=>r.id===routeId);if(!route)return;
  pushHistory();route.routeMode=mode;if(mode!=='ortho3')delete route.midPos;
  hasUnsavedChanges=true;renderAll();showFloorRouteProps(routeId);
}

function updateFloorRoutePort(routeId,end,port){
  const fp=getFloorPlan(currentView);if(!fp)return;
  const route=fp.routes.find(r=>r.id===routeId);if(!route)return;
  pushHistory();
  if(end==='source')route.sourcePort=port;else route.targetPort=port;
  route._userPorts=true; // mark as user-set, skip auto-pick
  hasUnsavedChanges=true;renderAll();showFloorRouteProps(routeId);
}

function resetFloorRoutePort(routeId){
  const fp=getFloorPlan(currentView);if(!fp)return;
  const route=fp.routes.find(r=>r.id===routeId);if(!route)return;
  pushHistory();delete route._userPorts;
  hasUnsavedChanges=true;renderAll();showFloorRouteProps(routeId);
}

function updateFloorRouteProp(routeId,prop,val){
  const fp=getFloorPlan(currentView);if(!fp)return;
  const route=fp.routes.find(r=>r.id===routeId);if(!route)return;
  pushHistoryProp();route[prop]=val;
  // Sync visual props to linked topology edge
  if(route.linked_edge_id&&['color','dash','label','hideLabel'].includes(prop)){
    const le=edges.find(e=>e.id===route.linked_edge_id);if(le)le[prop]=val;
  }
  hasUnsavedChanges=true;renderAll();
}

function deleteFloorRoute(routeId){
  const fp=getFloorPlan(currentView);if(!fp)return;
  pushHistory();
  const route=fp.routes.find(r=>r.id===routeId);
  if(route&&route.linked_edge_id){edges=edges.filter(e=>e.id!==route.linked_edge_id)}
  fp.routes=fp.routes.filter(r=>r.id!==routeId);
  selectedRouteId=null;hasUnsavedChanges=true;renderAll();hideProps();
  showToast(_t('已删除走线'));
}
function revertFloorRoute(routeId){
  const fp=getFloorPlan(currentView);if(!fp)return;
  pushHistory();fp.routes=fp.routes.filter(r=>r.id!==routeId);
  selectedRouteId=null;hasUnsavedChanges=true;renderAll();hideProps();
  showToast(_t('已恢复为自动走线'));
}

// ====== CABLE LENGTH CALCULATION ======
function calculateFloorRouteLength(route,fp){
  const srcN=nodes.find(n=>n.id===route.sourceNodeId),tgtN=nodes.find(n=>n.id===route.targetNodeId);if(!srcN||!tgtN)return null;
  const srcPl=fp.placements.find(p=>p.node_id===route.sourceNodeId),tgtPl=fp.placements.find(p=>p.node_id===route.targetNodeId);if(!srcPl||!tgtPl)return null;
  // Node centers (cable measured from center to center, icon size is display-only)
  const srcCx=srcPl.x+srcN.w/2,srcCy=srcPl.y+srcN.h/2,tgtCx=tgtPl.x+tgtN.w/2,tgtCy=tgtPl.y+tgtN.h/2;
  const rMode=route.routeMode||'ortho3';
  const autoP=(!route._userPorts)?findBestPort(srcPl,tgtPl,srcN.w||NODE_SIZE,rMode):null;
  const sp=autoP?autoP.srcPort:(route.sourcePort||'right'),tp=autoP?autoP.tgtPort:(route.targetPort||'left');
  const _sx=srcN.x,_sy=srcN.y,_tx=tgtN.x,_ty=tgtN.y;
  srcN.x=srcPl.x;srcN.y=srcPl.y;tgtN.x=tgtPl.x;tgtN.y=tgtPl.y;
  const edgeLike={sourceId:route.sourceNodeId,targetId:route.targetNodeId,sourcePort:sp,targetPort:tp,routeMode:rMode,midPos:route.midPos,waypoints:route.waypoints};
  const result=buildEdgePath(edgeLike);
  srcN.x=_sx;srcN.y=_sy;tgtN.x=_tx;tgtN.y=_ty;
  if(!result)return null;
  let px=0;
  if(rMode==='straight'){px=Math.sqrt((tgtCx-srcCx)**2+(tgtCy-srcCy)**2)}
  else if(rMode==='bezier'&&result.cp1&&result.cp2){
    // Approximate bezier with center endpoints
    let prev={x:srcCx,y:srcCy};for(let i=1;i<=20;i++){const t=i/20,u=1-t;
      const x=u*u*u*srcCx+3*u*u*t*result.cp1.x+3*u*t*t*result.cp2.x+t*t*t*tgtCx;
      const y=u*u*u*srcCy+3*u*u*t*result.cp1.y+3*u*t*t*result.cp2.y+t*t*t*tgtCy;
      px+=Math.sqrt((x-prev.x)**2+(y-prev.y)**2);prev={x,y}}
  }else if(result.pts){
    // Ortho: replace endpoints with centers, keep mid-points
    const pts=[...result.pts];pts[0]={x:srcCx,y:srcCy};pts[pts.length-1]={x:tgtCx,y:tgtCy};
    for(let i=1;i<pts.length;i++)px+=Math.sqrt((pts[i].x-pts[i-1].x)**2+(pts[i].y-pts[i-1].y)**2);
  }else{px=Math.sqrt((tgtCx-srcCx)**2+(tgtCy-srcCy)**2)}
  if(fp.calibration&&fp.calibration.px_per_meter){const m=px/fp.calibration.px_per_meter;return{px,meters:m}}
  return{px,meters:null};
}
// ====== LEFT PANEL: CONNECTED DEVICE HIGHLIGHT ======
function highlightConnectedInPanel(nodeId){
  const panel=document.getElementById('existingDevicesPanel');if(!panel)return;
  panel.querySelectorAll('.selected-in-panel,.connected-in-panel').forEach(el=>{el.classList.remove('selected-in-panel','connected-in-panel')});
  if(!nodeId||currentView==='topology')return;
  const connected=new Set();
  edges.forEach(e=>{if(e.sourceId===nodeId)connected.add(e.targetId);if(e.targetId===nodeId)connected.add(e.sourceId)});
  panel.querySelectorAll('.existing-device-item').forEach(el=>{
    const nid=parseInt(el.dataset.existingNodeId);
    if(nid===nodeId){el.classList.add('selected-in-panel');el.scrollIntoView({block:'nearest',behavior:'smooth'})}
    else if(connected.has(nid))el.classList.add('connected-in-panel');
  });
}

// ====== LABEL LAYOUT ======
// computeBestLabelSide() and getLabelCoords() moved to core.js as shared functions

// ====== FLOOR NODES ======
function renderFloorNodes(fp){
  const nodesLayer=document.getElementById('nodesLayer');
  fp.placements.forEach(pl=>{
    const n=nodes.find(n=>n.id===pl.node_id);
    if(!n)return;

    const isSel=selectedNodeIds.has(n.id);
    const g=document.createElementNS('http://www.w3.org/2000/svg','g');
    g.setAttribute('class',`node-group ${isSel?'selected':''}`);
    const comp = getFloorZoomCompensation();
    const rotStr = pl.rotation ? ` rotate(${pl.rotation},${n.w/2},${n.h/2})` : '';
    if (comp !== 1) {
      const cx = n.w / 2, cy = n.h / 2;
      g.setAttribute('transform',
        `translate(${pl.x + cx * (1 - comp)},${pl.y + cy * (1 - comp)}) scale(${comp})${rotStr}`);
    } else {
      g.setAttribute('transform', `translate(${pl.x},${pl.y})${rotStr}`);
    }
    g.dataset.nodeId=n.id;

    // Glow
    const glow=document.createElementNS('http://www.w3.org/2000/svg','circle');
    glow.setAttribute('class','node-glow');glow.setAttribute('cx',n.w/2);glow.setAttribute('cy',n.h/2);
    glow.setAttribute('r',n.w/2+8);glow.setAttribute('fill',n.color);
    glow.setAttribute('opacity',isSel?'0.15':'0');g.appendChild(glow);

    // Hit area
    const hit=document.createElementNS('http://www.w3.org/2000/svg','rect');
    hit.setAttribute('x',-8);hit.setAttribute('y',-8);
    hit.setAttribute('width',n.w+16);hit.setAttribute('height',n.h+LABEL_OFFSET+28);
    hit.setAttribute('fill','transparent');g.appendChild(hit);

    // Icon
    const ig=document.createElementNS('http://www.w3.org/2000/svg','g');
    ig.innerHTML=renderIconSVG(n.iconData,n.w,0,0);g.appendChild(ig);

    // Selection ring
    if(isSel){
      const ring=document.createElementNS('http://www.w3.org/2000/svg','rect');
      ring.setAttribute('x',-6);ring.setAttribute('y',-6);
      ring.setAttribute('width',n.w+12);ring.setAttribute('height',n.h+12);ring.setAttribute('rx',10);
      ring.setAttribute('fill','none');ring.setAttribute('stroke',n.color);
      ring.setAttribute('stroke-width',1.5);ring.setAttribute('stroke-dasharray','4 2');ring.setAttribute('opacity',.6);
      g.appendChild(ring);
    }

    // Lock: no per-node badge, only cursor change

    // Qty badge
    const plQty=pl.qty||1;
    if(plQty>1){
      const qG=document.createElementNS('http://www.w3.org/2000/svg','g');
      qG.setAttribute('transform',`translate(${n.w+2},-6)`);
      const qBg=document.createElementNS('http://www.w3.org/2000/svg','rect');
      const qTxt='×'+plQty, qW=Math.max(20,qTxt.length*7+6);
      qBg.setAttribute('x',-qW/2);qBg.setAttribute('y',-8);qBg.setAttribute('width',qW);qBg.setAttribute('height',16);
      qBg.setAttribute('rx',8);qBg.setAttribute('fill','#3b82f6');qBg.setAttribute('stroke','var(--bg-panel,#1e293b)');qBg.setAttribute('stroke-width',1.5);
      qG.appendChild(qBg);
      const qLabel=document.createElementNS('http://www.w3.org/2000/svg','text');
      qLabel.setAttribute('x',0);qLabel.setAttribute('y',4);qLabel.setAttribute('text-anchor','middle');
      qLabel.setAttribute('font-size','10');qLabel.setAttribute('font-weight','600');qLabel.setAttribute('fill','#fff');
      qLabel.textContent=qTxt;qG.appendChild(qLabel);
      g.appendChild(qG);
    }

    // Label
    if(!n.hideLabel){
      const nameText=displaySettings.iconLabel?n.name:'',modelText=(displaySettings.iconModel&&n.model)?n.model:'';
      const lines=[];if(nameText)lines.push(nameText);if(modelText)lines.push(modelText);
      if(!lines.length)lines.push(n.name);
      const lblW=Math.max(...lines.map(t=>t.length))*12+12,lblH=lines.length*12+4;
      const side=pl.labelPosition||computeBestLabelSide((fp.routes||[]).map(r=>({sourceId:r.sourceNodeId,targetId:r.targetNodeId,sourcePort:r.sourcePort,targetPort:r.targetPort})),n.id);
      const lc=getLabelCoords(side,n.w,n.h,lblW,lblH);
      const lblBg=document.createElementNS('http://www.w3.org/2000/svg','rect');
      lblBg.setAttribute('class','node-label-bg');
      lblBg.setAttribute('x',lc.bgX);lblBg.setAttribute('y',lc.bgY);
      lblBg.setAttribute('width',lblW);lblBg.setAttribute('height',lblH);lblBg.setAttribute('rx',4);
      g.appendChild(lblBg);
      let ly=lc.firstLineY;
      const lbl=document.createElementNS('http://www.w3.org/2000/svg','text');
      lbl.setAttribute('class','node-label');lbl.setAttribute('x',lc.textX);lbl.setAttribute('y',ly);
      if(lc.anchor!=='middle')lbl.style.textAnchor=lc.anchor;
      lbl.textContent=nameText;g.appendChild(lbl);
      if(modelText){ly+=12;const ml=document.createElementNS('http://www.w3.org/2000/svg','text');ml.setAttribute('class','node-sublabel');ml.setAttribute('x',lc.textX);ml.setAttribute('y',ly);if(lc.anchor!=='middle')ml.style.textAnchor=lc.anchor;ml.textContent=modelText;g.appendChild(ml)}
    }

    // Ports
    const _R=n.w/2+8,_D=_R*.7071,_cx=n.w/2,_cy=n.h/2;
    [{name:'top',cx:_cx,cy:_cy-_R},{name:'right',cx:_cx+_R,cy:_cy},{name:'bottom',cx:_cx,cy:_cy+_R},{name:'left',cx:_cx-_R,cy:_cy},{name:'top-left',cx:_cx-_D,cy:_cy-_D},{name:'top-right',cx:_cx+_D,cy:_cy-_D},{name:'bottom-left',cx:_cx-_D,cy:_cy+_D},{name:'bottom-right',cx:_cx+_D,cy:_cy+_D}].forEach(p=>{
      const port=document.createElementNS('http://www.w3.org/2000/svg','circle');
      port.setAttribute('class','port');
      port.setAttribute('cx',p.cx);port.setAttribute('cy',p.cy);port.setAttribute('r',5);
      port.style.cursor='crosshair';
      port.dataset.nodeId=n.id;port.dataset.port=p.name;
      port.addEventListener('mousedown',onPortMouseDown);g.appendChild(port);
    });

    g.style.cursor=pl.locked?'not-allowed':'move';
    g.addEventListener('mousedown',onNodeMouseDown);
    g.addEventListener('contextmenu',e=>{e.preventDefault();e.stopPropagation();showNodeCtxMenu(e.clientX,e.clientY,n.id)});
    nodesLayer.appendChild(g);
  });
}

// ====== FLOOR LEGEND ======
function buildFloorLegend(fp){
  const legendPanel=document.getElementById('legendPanel');
  let h='';

  // Heatmap color scale
  if(displaySettings.coverageMode==='heatmap'&&displaySettings.showCoverage!=='off'){
    const hasAntenna=fp.placements&&fp.placements.some(pl=>{
      const nd=nodes.find(x=>x.id===pl.node_id);
      return nd&&getNodeIconKey(nd)==='antenna_indoor'&&
        (displaySettings.showCoverage==='all'||nd.showCoverage===true);
    });
    if(hasAntenna){
      // Build CSS gradient from HEATMAP_COLORS (reversed: strong=red on top)
      const stops=HEATMAP_COLORS.slice().reverse().map(c=>`rgb(${c.r},${c.g},${c.b}) ${Math.round((1-c.stop)*100)}%`).join(',');
      h+=`<div class="legend-title">${_t('信号强度')}</div>`
        +`<div style="display:flex;gap:6px;align-items:stretch;">`
        +`<div style="width:14px;height:100px;border-radius:3px;border:1px solid var(--border);background:linear-gradient(to bottom,${stops});"></div>`
        +`<div style="display:flex;flex-direction:column;justify-content:space-between;font-size:10px;color:var(--text-muted);line-height:1;">`
        +`<span>−15 dBm <span style="opacity:.6">${_t('强')}</span></span>`
        +`<span>−50 dBm</span>`
        +`<span>−85 dBm</span>`
        +`<span>−110 dBm <span style="opacity:.6">${_t('弱')}</span></span>`
        +`</div></div>`;
    }
  }

  // Cable type legend
  const types=new Set();
  if(fp.routes)fp.routes.forEach(r=>{if(r.cableType)types.add(r.cableType)});
  const used=[...types];
  if(used.length){
    if(h)h+='<div style="border-top:1px solid var(--border);margin:8px 0"></div>';
    h+=`<div class="legend-title">${_t('图例')}</div>`;
    used.forEach(k=>{const c=CABLE_TYPES[k];if(!c)return;h+=`<div class="legend-item"><div style="width:36px;height:12px;">${cableLineSVG(k,36,12)}</div><span>${_m(c.shortName)}</span></div>`});
  }

  legendPanel.innerHTML=h;
}

// ====== SCALE INDICATOR ======
function updateScaleIndicator(){
  const el=document.getElementById('scaleIndicator');if(!el)return;
  const legend=document.getElementById('legendPanel');
  if(currentView==='topology'){el.style.display='none';if(legend)legend.style.bottom='50px';return}
  const fp=getFloorPlan(currentView);
  if(!fp||!fp.calibration||!fp.calibration.px_per_meter){el.style.display='none';if(legend)legend.style.bottom='50px';return}
  const ppm=fp.calibration.px_per_meter; // px per meter
  // Show a 1m bar scaled to current px_per_meter
  const barMeters=1;
  const barPx=Math.min(Math.round(barMeters*ppm),120); // cap visual width
  const bar=document.getElementById('scaleBar');
  const lbl=document.getElementById('scaleLabel');
  if(bar){bar.setAttribute('width',barPx);bar.innerHTML=`<line x1="0" y1="4" x2="${barPx}" y2="4" stroke="#f59e0b" stroke-width="2"/><line x1="0" y1="0" x2="0" y2="8" stroke="#f59e0b" stroke-width="1.5"/><line x1="${barPx}" y1="0" x2="${barPx}" y2="8" stroke="#f59e0b" stroke-width="1.5"/>`}
  if(lbl)lbl.textContent=`${barMeters}m (1m=${ppm}px)`;
  el.style.display='';
  if(legend)legend.style.bottom='56px'; // push legend up above scale indicator
}

// ====== BACKGROUND UPLOAD ======

// Helper: delete old background files from server (fire-and-forget)
function _cleanupOldBgFiles(fp){
  if(!fp.background||!DIAGRAM_CONFIG.diagramId)return;
  const body={};
  if(fp.background.filenames&&fp.background.filenames.length){
    body.filenames=fp.background.filenames;
  } else if(fp.background.filename){
    body.filename=fp.background.filename;
  } else return;
  fetch(DIAGRAM_CONFIG.apiFloorBgBase+DIAGRAM_CONFIG.diagramId+'/floor-plan/delete-bg',{
    method:'POST',
    headers:{'Content-Type':'application/json','X-CSRFToken':DIAGRAM_CONFIG.csrfToken},
    body:JSON.stringify(body)
  }).catch(()=>{});
}

async function uploadFloorBg(fpId){
  if(DIAGRAM_CONFIG.readOnly)return;
  const fp=getFloorPlan(fpId);if(!fp)return;

  const input=document.createElement('input');
  input.type='file';input.accept='image/png,image/jpeg,image/jpg,application/pdf';
  input.onchange=async function(){
    const file=input.files[0];if(!file)return;
    if(file.size>12*1024*1024){showToast(_t('文件大小不能超过 12MB'));return}

    const isPdf=file.name.toLowerCase().endsWith('.pdf');
    if(isPdf){
      await _handlePdfUpload(file,fpId);
      return;
    }

    // Image flow: client-side resize then upload
    const img=new Image();
    img.onload=async function(){
      let w=img.width,h=img.height;
      const maxDim=2000;
      if(w>maxDim||h>maxDim){
        const ratio=Math.min(maxDim/w,maxDim/h);
        w=Math.round(w*ratio);h=Math.round(h*ratio);
      }

      const canvas=document.createElement('canvas');
      canvas.width=w;canvas.height=h;
      const ctx=canvas.getContext('2d');
      ctx.drawImage(img,0,0,w,h);

      canvas.toBlob(async function(blob){
        const formData=new FormData();
        const pngName=file.name.replace(/\.[^.]+$/,'.png');
        formData.append('file',blob,pngName);
        formData.append('floor_id',fpId);

        showToast(_t('上传中...'));
        try{
          if(!DIAGRAM_CONFIG.diagramId){await saveDiagram();if(!DIAGRAM_CONFIG.diagramId){showToast(_t('保存失败，无法上传'));return}}
          const resp=await fetch(DIAGRAM_CONFIG.apiFloorBgBase+DIAGRAM_CONFIG.diagramId+'/floor-plan/upload-bg',{
            method:'POST',
            headers:{'X-CSRFToken':DIAGRAM_CONFIG.csrfToken},
            body:formData
          });
          const result=await resp.json();
          if(result.success){
            _cleanupOldBgFiles(fp);
            fp.background={url:result.url,width:result.width,height:result.height,offset_x:0,offset_y:0,opacity:0.3,filename:result.filename||''};
            hasUnsavedChanges=true;renderAll();
            showFloorPlanProps(fpId);
            showToast(_t('背景图已上传'));
            updateFloorBgButton(fpId);
          }else{showToast(_t('上传失败')+': '+(result.message||''))}
        }catch(err){showToast(_t('上传失败')+': '+err.message)}
      },'image/png',0.85);
    };
    img.src=URL.createObjectURL(file);
  };
  input.click();
}

async function deleteFloorBg(fpId){
  if(DIAGRAM_CONFIG.readOnly)return;
  const fp=getFloorPlan(fpId);if(!fp||!fp.background)return;
  const ok=await sdConfirm(_t('移除背景'),_t('确定移除当前楼层的背景图？'),{danger:true,okText:_t('移除')});
  if(!ok)return;

  // Build filenames list for multi-res or single file
  const body={floor_id:fpId};
  if(fp.background.filenames&&fp.background.filenames.length){
    body.filenames=fp.background.filenames;
  } else {
    body.filename=fp.background.filename||'';
  }

  try{
    if(!DIAGRAM_CONFIG.diagramId){showToast(_t('请先保存系统图'));return}
    const resp=await fetch(DIAGRAM_CONFIG.apiFloorBgBase+DIAGRAM_CONFIG.diagramId+'/floor-plan/delete-bg',{
      method:'POST',
      headers:{'Content-Type':'application/json','X-CSRFToken':DIAGRAM_CONFIG.csrfToken},
      body:JSON.stringify(body)
    });
    const result=await resp.json();
    if(result.success){
      fp.background=null;hasUnsavedChanges=true;renderAll();
      showToast(_t('背景图已删除'));
    }else{showToast(_t('删除失败')+': '+(result.message||''))}
  }catch(err){showToast(_t('删除失败')+': '+err.message)}
  updateFloorBgButton(fpId);
}

function toggleFloorBg(fpId){
  const fp=getFloorPlan(fpId);
  if(fp&&fp.background&&fp.background.url){
    deleteFloorBg(fpId);
  }else{
    uploadFloorBg(fpId);
  }
}

function updateFloorBgButton(fpId){
  const btn=document.getElementById('btnFloorBgToggle');
  const label=document.getElementById('btnFloorBgLabel');
  if(!btn||!label)return;
  const fp=getFloorPlan(fpId);
  const hasBg=fp&&fp.background&&fp.background.url;
  const icon=btn.querySelector('.material-symbols-outlined');
  if(hasBg){
    if(icon)icon.textContent='hide_image';
    label.textContent=_t('移除背景');
  }else{
    if(icon)icon.textContent='image';
    label.textContent=_t('背景图');
  }
}

// ====== PDF IMPORT ======

async function _handlePdfUpload(file,fpId){
  if(!DIAGRAM_CONFIG.diagramId){await saveDiagram();if(!DIAGRAM_CONFIG.diagramId){showToast(_t('保存失败，无法上传'));return}}

  showToast(_t('分析 PDF 中...'));
  const formData=new FormData();
  formData.append('file',file,file.name);

  try{
    const resp=await fetch(DIAGRAM_CONFIG.apiFloorBgBase+DIAGRAM_CONFIG.diagramId+'/floor-plan/analyze-pdf',{
      method:'POST',
      headers:{'X-CSRFToken':DIAGRAM_CONFIG.csrfToken},
      body:formData
    });
    const result=await resp.json();
    if(!result.success){showToast(result.message||_t('PDF 分析失败'));return}

    if(result.page_count===1){
      await _renderAndSetPdfBackground(fpId,result.session_id,[{index:0,label:result.pages[0].name}]);
    } else {
      _showPdfPageSelector(result.pages,result.session_id,fpId);
    }
  }catch(err){showToast(_t('PDF 分析失败')+': '+err.message)}
}

async function _renderAndSetPdfBackground(fpId,sessionId,pages){
  const fp=getFloorPlan(fpId);if(!fp)return;
  showToast(_t('渲染中...'));

  try{
    const resp=await fetch(DIAGRAM_CONFIG.apiFloorBgBase+DIAGRAM_CONFIG.diagramId+'/floor-plan/render-pdf-pages',{
      method:'POST',
      headers:{'Content-Type':'application/json','X-CSRFToken':DIAGRAM_CONFIG.csrfToken},
      body:JSON.stringify({session_id:sessionId,pages:pages})
    });
    const result=await resp.json();
    if(!result.success){showToast(result.message||_t('渲染失败'));return}

    if(result.results.length===1&&pages.length===1){
      // Single page: set as current floor background
      _cleanupOldBgFiles(fp);
      const r=result.results[0];
      const defaultRes=r.resolutions['2000']||Object.values(r.resolutions)[0];
      fp.background={
        is_multi_res:true,
        url:defaultRes.url,
        width:defaultRes.width,height:defaultRes.height,
        resolutions:r.resolutions,
        filenames:r.filenames,
        offset_x:0,offset_y:0,opacity:0.3
      };
      hasUnsavedChanges=true;renderAll();
      showFloorPlanProps(fpId);
      showToast(_t('背景图已导入'));
      updateFloorBgButton(fpId);
    } else {
      // Multiple pages: create new floor plans for each
      let firstNewId=null;
      for(const r of result.results){
        const defaultRes=r.resolutions['2000']||Object.values(r.resolutions)[0];
        const newId=addFloorPlanWithBackground(r.label,{
          is_multi_res:true,
          url:defaultRes.url,
          width:defaultRes.width,height:defaultRes.height,
          resolutions:r.resolutions,
          filenames:r.filenames,
          offset_x:0,offset_y:0,opacity:0.3
        });
        if(!firstNewId)firstNewId=newId;
      }
      if(firstNewId)switchView(firstNewId);
      showToast(_t('已导入')+' '+result.results.length+' '+_t('个楼层'));
    }
  }catch(err){showToast(_t('渲染失败')+': '+err.message)}
}

function _showPdfPageSelector(pages,sessionId,fpId){
  const overlay=document.getElementById('pdfPageSelector');
  if(!overlay)return;
  overlay.dataset.sessionId=sessionId;
  overlay.dataset.fpId=fpId;

  const grid=document.getElementById('pdfPageGrid');
  grid.innerHTML='';
  pages.forEach(p=>{
    const card=document.createElement('div');
    card.className='pdf-page-card';
    card.innerHTML=`
      <label class="pdf-page-thumb-wrap">
        <input type="checkbox" checked data-page-index="${p.index}">
        <img src="${p.thumbnail}" alt="Page ${p.index+1}">
        <span class="pdf-page-check">\u2713</span>
      </label>
      <input type="text" class="pdf-page-name" value="${p.name}" placeholder="${_t('楼层名称')}" data-page-index="${p.index}">
    `;
    grid.appendChild(card);
  });

  const selectAll=document.getElementById('pdfSelectAll');
  selectAll.checked=true;
  selectAll.onchange=function(){
    grid.querySelectorAll('input[type=checkbox]').forEach(cb=>{cb.checked=selectAll.checked});
  };

  document.getElementById('pdfProgress').style.display='none';
  overlay.style.display='flex';
}

function closePdfSelector(){
  const overlay=document.getElementById('pdfPageSelector');
  if(overlay)overlay.style.display='none';
}

async function importSelectedPdfPages(){
  const overlay=document.getElementById('pdfPageSelector');
  const sessionId=overlay.dataset.sessionId;
  const fpId=overlay.dataset.fpId;

  const grid=document.getElementById('pdfPageGrid');
  const selectedPages=[];
  grid.querySelectorAll('.pdf-page-card').forEach(card=>{
    const cb=card.querySelector('input[type=checkbox]');
    if(cb&&cb.checked){
      const nameInput=card.querySelector('.pdf-page-name');
      selectedPages.push({
        index:parseInt(cb.dataset.pageIndex),
        label:nameInput?nameInput.value.trim():('Page-'+(parseInt(cb.dataset.pageIndex)+1))
      });
    }
  });

  if(!selectedPages.length){showToast(_t('请至少选择一个页面'));return}

  const progress=document.getElementById('pdfProgress');
  progress.style.display='flex';
  document.getElementById('pdfProgressText').textContent=_t('渲染中...');
  document.getElementById('pdfProgressBar').style.width='30%';

  await _renderAndSetPdfBackground(fpId,sessionId,selectedPages);

  document.getElementById('pdfProgressBar').style.width='100%';
  document.getElementById('pdfProgressText').textContent=_t('完成');
  setTimeout(()=>closePdfSelector(),500);
}

// ====== MULTI-RESOLUTION ZOOM SWITCHING ======

function _getOptimalResolutionKey(currentScale){
  const fp=getFloorPlan(currentView);
  const bgW=fp?.background?.width||2000;
  const displayPx=bgW*currentScale;
  if(displayPx>4000) return '8000';
  if(displayPx>2000) return '4000';
  if(displayPx>1000) return '2000';
  return '1000';
}

function onScaleChanged(newScale){
  if(currentView==='topology')return;

  // Re-render to apply zoom compensation on icons/cables
  requestRenderThrottled();

  const fp=getFloorPlan(currentView);
  if(!fp||!fp.background||!fp.background.is_multi_res)return;

  const optimalKey=_getOptimalResolutionKey(newScale);
  const res=fp.background.resolutions[optimalKey];
  if(!res||res.url===_cachedBgUrl)return;

  // Only swap image URL for better detail; keep SVG coordinate dimensions unchanged
  // so that node positions and icon sizes remain proportionally correct
  fp.background.url=res.url;
  renderFloorBackground(fp);

  _preloadAdjacentResolution(fp,newScale);
}

function _preloadAdjacentResolution(fp,currentScale){
  const bgW=fp?.background?.width||2000;
  const displayPx=bgW*currentScale;
  let preloadKey=null;
  if(displayPx>3000&&displayPx<=4000) preloadKey='8000';
  else if(displayPx>1500&&displayPx<=2000) preloadKey='4000';
  else if(displayPx>700&&displayPx<=1000) preloadKey='2000';

  if(preloadKey&&fp.background.resolutions[preloadKey]){
    const img=new Image();
    img.src=fp.background.resolutions[preloadKey].url;
  }
}

// ====== FLOOR PLAN PROPERTIES PANEL ======

function showFloorPlanProps(fpId){
  const fp=getFloorPlan(fpId);if(!fp)return;
  const panel=document.getElementById('propsPanel');
  panel.classList.add('visible');
  document.getElementById('propsTitle').textContent=_t('楼层属性');

  const hasBg=fp.background&&fp.background.url;
  const bgOpacity=hasBg?(fp.background.opacity||0.3):0.3;
  const deviceCount=fp.placements.length;
  const routeCount=(fp.routes||[]).length;
  const areaCount=(fp.areas||[]).length;

  const isRO=DIAGRAM_CONFIG.readOnly;
  const nameHTML=isRO
    ?`<div style="font-size:13px;font-weight:600;color:var(--text-primary)">${fp.label}</div>`
    :`<input class="props-input" value="${fp.label}" oninput="updateFloorPlanProp('${fpId}','label',this.value)">`;
  let html=`
    <div class="props-field"><span class="props-label">${_t('楼层名称（导出文件名）')}</span>${nameHTML}</div>
    <div class="props-field"><span class="props-label">${_t('背景图透明度')}</span><div class="props-row"><input type="range" class="props-range" min="0.05" max="1" step="0.05" value="${bgOpacity}" ${hasBg?'':'disabled'} oninput="updateFloorBgOpacity('${fpId}',parseFloat(this.value));this.nextElementSibling.textContent=Math.round(this.value*100)+'%'"><span class="props-range-val">${Math.round(bgOpacity*100)}%</span></div></div>`;
  if(!isRO){
    html+=`<div class="props-field" style="flex-direction:row;gap:6px;">`;
    if(hasBg){
      html+=`<button class="props-btn props-btn-warn" onclick="deleteFloorBg('${fpId}');showFloorPlanProps('${fpId}')" style="flex:1;">${_t('移除背景')}</button>`;
    } else {
      html+=`<button class="props-btn" onclick="uploadFloorBg('${fpId}')" style="flex:1;">${_t('上传背景图')}</button>`;
    }
    html+=`</div>`;
  }
  html+=`
    <div class="props-field"><span class="props-label">${_t('统计')}</span><div style="font-size:11px;color:var(--text-secondary);line-height:1.6;">${_t('设备')} ${deviceCount} · ${_t('走线')} ${routeCount} · ${_t('区域')} ${areaCount}</div></div>`+renderDisplaySettingsHTML();
  if(!isRO){
    html+=`<button class="btn-delete" onclick="deleteFloorPlan('${fpId}')">${_t('删除楼层')}</button>`;
  }

  document.getElementById('propsContent').innerHTML=html;
}

function updateFloorPlanProp(fpId,prop,val){
  const fp=getFloorPlan(fpId);if(!fp)return;
  pushHistoryProp();fp[prop]=val;hasUnsavedChanges=true;
  rebuildViewTabs();
  if(typeof syncFloorAreaLabels==='function')syncFloorAreaLabels();
}

function updateFloorBgOpacity(fpId,val){
  const fp=getFloorPlan(fpId);if(!fp||!fp.background)return;
  pushHistoryProp();fp.background.opacity=val;hasUnsavedChanges=true;
  renderAll();
}

let _pendingDeleteFpId=null;

function deleteFloorPlan(fpId){
  const fp=getFloorPlan(fpId);if(!fp)return;
  _pendingDeleteFpId=fpId;
  const deviceCount=fp.placements.length;
  const routeCount=(fp.routes||[]).length;
  const areaCount=(fp.areas||[]).length;
  document.getElementById('deleteFloorTitle').textContent=`${_t('删除楼层')}「${fp.label}」`;
  document.getElementById('deleteFloorMsg').textContent=`${_t('设备')} ${deviceCount} · ${_t('走线')} ${routeCount} · ${_t('区域')} ${areaCount}`;
  document.getElementById('deleteFloorModal').style.display='flex';
}

function dismissDeleteFloorModal(){
  document.getElementById('deleteFloorModal').style.display='none';
  _pendingDeleteFpId=null;
}

function confirmDeleteFloorPlan(){
  const fpId=_pendingDeleteFpId;
  dismissDeleteFloorModal();
  const fp=getFloorPlan(fpId);if(!fp)return;

  pushHistory();

  // Remove floor-specific nodes and their topology edges
  const floorNodeIds=new Set(fp.placements.map(p=>p.node_id));
  nodes=nodes.filter(n=>!floorNodeIds.has(n.id));
  edges=edges.filter(e=>!floorNodeIds.has(e.sourceId)&&!floorNodeIds.has(e.targetId));

  // Clear floor_id from topology nodes that reference this floor
  nodes.forEach(n=>{if(n.floor_id===fpId)delete n.floor_id});

  // Remove from floorPlans array
  const idx=floorPlans.indexOf(fp);
  if(idx>=0)floorPlans.splice(idx,1);

  // Re-number sort_order
  floorPlans.forEach((f,i)=>f.sort_order=i+1);

  hasUnsavedChanges=true;
  hideProps();
  rebuildViewTabs();

  // Switch to first remaining floor or topology
  if(floorPlans.length>0) switchView(floorPlans[0].id);
  else switchView('topology');

  showToast(_t('已删除楼层'));
}

// ====== DEVICE PLACEMENT ======

// Compute a compact grid position for the topology view when creating nodes from floor plan
function computeNextTopoPosition(){
  const gap=NODE_SIZE+30;
  const cols=6;
  const floorNodeCount=nodes.filter(n=>n.floor_id).length;
  const topoNodes=nodes.filter(n=>!n.floor_id);
  if(!topoNodes.length){
    const row=Math.floor(floorNodeCount/cols);
    const col=floorNodeCount%cols;
    return {x:200+col*gap, y:200+row*gap};
  }
  const maxY=Math.max(...topoNodes.map(n=>n.y+(n.h||NODE_SIZE)));
  const minX=Math.min(...topoNodes.map(n=>n.x));
  const col=floorNodeCount%cols;
  const row=Math.floor(floorNodeCount/cols);
  return {x:minX+col*gap, y:maxY+80+row*gap};
}

// Re-layout all floor-plan nodes to compact grid positions in topology view
// Only nodes with actual placements on floor plans participate;
// topology-only devices (主机, 合路平台 etc.) are excluded.
function relayoutFloorNodesTopo(){
  // Build authoritative set from actual placements (not stale floor_id)
  const placedNodeIds=new Set();
  floorPlans.forEach(fp=>{fp.placements.forEach(p=>placedNodeIds.add(p.node_id))});
  const floorNodes=nodes.filter(n=>placedNodeIds.has(n.id));
  if(!floorNodes.length)return;

  // ═══ DEBUG: snapshot before layout ═══
  const _dbgBefore={};
  nodes.forEach(n=>{_dbgBefore[n.id]={name:n.name,x:n.x,y:n.y,floor_id:n.floor_id,placed:placedNodeIds.has(n.id)}});
  console.group('🔧 relayoutFloorNodesTopo DEBUG');
  console.log('All nodes:',nodes.length,'| Placed on floor:',floorNodes.length,'| Topology-only:',nodes.length-floorNodes.length);
  console.log('Topology-only nodes (should NOT move):');
  nodes.filter(n=>!placedNodeIds.has(n.id)).forEach(n=>console.log(`  [${n.id}] ${n.name} x=${n.x} y=${n.y} floor_id=${n.floor_id}`));
  console.log('Floor nodes (WILL move):');
  floorNodes.forEach(n=>console.log(`  [${n.id}] ${n.name} x=${n.x} y=${n.y} floor_id=${n.floor_id}`));
  // ═══ END DEBUG BEFORE ═══

  pushHistory();
  // Sync floor_id for consistency
  syncFloorAreaLabels();

  const gapH=NODE_SIZE+200; // horizontal gap between chain columns (enough room for edge labels)
  const gapV=NODE_SIZE+80;  // vertical gap between leaf rows (also used for floor spacing)

  const topoNodes=nodes.filter(n=>!placedNodeIds.has(n.id));
  let startX=200,startY=200;
  if(topoNodes.length){
    // Find topology nodes that connect to floor devices (cross-view edges)
    const crossTopoXs=[];
    edges.forEach(e=>{
      const sPlaced=placedNodeIds.has(e.sourceId),tPlaced=placedNodeIds.has(e.targetId);
      if(sPlaced!==tPlaced){
        const topoN=sPlaced?nodes.find(n=>n.id===e.targetId):nodes.find(n=>n.id===e.sourceId);
        if(topoN)crossTopoXs.push(topoN.x);
      }
    });
    // Align floor chains with leftmost topology node (consistent left margin)
    startX=Math.min(...topoNodes.map(n=>n.x));
    startY=Math.max(...topoNodes.map(n=>n.y+(n.h||NODE_SIZE)))+100;
    console.log(`startX=${startX} (from ${crossTopoXs.length?'cross-view topo node':'leftmost topo node'}), startY=${startY}`);
  }

  // Group by floor
  const groups={};
  floorNodes.forEach(n=>{const fid=n.floor_id;if(!groups[fid])groups[fid]=[];groups[fid].push(n)});
  // Use floor panel tab order reversed: left→right in tabs = bottom→top in diagram
  // SVG Y increases downward, so rightmost tab (highest floor) gets smallest Y (top)
  const floorIds=floorPlans.map(f=>f.id).filter(id=>groups[id]).reverse();

  const floorData={};
  let curY=startY;

  floorIds.forEach(fid=>{
    const group=groups[fid];
    const allIds=new Set(group.map(n=>n.id));

    // Build adjacency (within this floor only)
    const adj={};
    group.forEach(n=>{adj[n.id]=[]});
    edges.forEach(e=>{
      if(allIds.has(e.sourceId)&&allIds.has(e.targetId)){
        adj[e.sourceId].push(e.targetId);
        adj[e.targetId].push(e.sourceId);
      }
    });

    // ═══ Split into connected components (handles multiple risers) ═══
    const ccVisited=new Set();
    const rawComponents=[];
    group.forEach(n=>{
      if(ccVisited.has(n.id))return;
      const comp=[];
      const q=[n.id];
      ccVisited.add(n.id);
      while(q.length){
        const cur=q.shift();
        comp.push(group.find(nd=>nd.id===cur));
        (adj[cur]||[]).forEach(nb=>{
          if(!ccVisited.has(nb)){ccVisited.add(nb);q.push(nb)}
        });
      }
      rawComponents.push(comp);
    });

    // Sort: riser-containing components first (leftmost in layout)
    const fp=floorPlans.find(f=>f.id===fid);
    const riserAreas=fp?(fp.areas||[]).filter(a=>a.is_riser):[];
    function compHasRiser(cmp){
      if(cmp.some(n=>n.is_riser_node))return true;
      for(const ra of riserAreas){
        for(const n of cmp){
          const pl=(fp.placements||[]).find(p=>p.node_id===n.id);
          if(pl){
            const cx=pl.x+NODE_SIZE/2,cy=pl.y+NODE_SIZE/2;
            if(cx>=ra.x&&cx<=ra.x+ra.width&&cy>=ra.y&&cy<=ra.y+ra.height)return true;
          }
        }
      }
      return false;
    }
    rawComponents.sort((a,b)=>(compHasRiser(b)?1:0)-(compHasRiser(a)?1:0));

    // Process each connected component independently
    const compDataArr=[];
    rawComponents.forEach(comp=>{
      const compIds=new Set(comp.map(n=>n.id));

      // Find root: 1) riser virtual node, 2) real device inside riser area, 3) cross-floor link, 4) fallback
      let root=comp.find(n=>n.is_riser_node);
      if(!root&&fp){
        for(const ra of riserAreas){
          const pl=(fp.placements||[]).find(p=>{
            const cx=p.x+NODE_SIZE/2,cy=p.y+NODE_SIZE/2;
            return cx>=ra.x&&cx<=ra.x+ra.width&&cy>=ra.y&&cy<=ra.y+ra.height;
          });
          if(pl){const n=comp.find(nd=>nd.id===pl.node_id);if(n&&!n.is_riser_node){root=n;break}}
        }
      }
      if(!root) root=comp.find(n=>edges.some(e=>
        (e.sourceId===n.id&&!compIds.has(e.targetId))||(e.targetId===n.id&&!compIds.has(e.sourceId))
      ));
      if(!root) root=comp[0];

      // BFS to get depth and parent
      const depthOf={},parentOf={};
      const bfsQ=[{id:root.id,d:0}];
      const bfsVisited=new Set([root.id]);
      depthOf[root.id]=0;
      while(bfsQ.length){
        const{id,d}=bfsQ.shift();
        (adj[id]||[]).forEach(nid=>{
          if(!bfsVisited.has(nid)){
            bfsVisited.add(nid);depthOf[nid]=d+1;parentOf[nid]=id;
            bfsQ.push({id:nid,d:d+1});
          }
        });
      }

      // Classify: leaf (degree 1 within component) vs chain (degree 2+)
      const isLeaf={};
      comp.forEach(n=>{isLeaf[n.id]=(adj[n.id]||[]).length<=1});

      // Find main chain: greedy walk from root
      function countDesc(nid,vis){
        let c=1;vis.add(nid);
        (adj[nid]||[]).forEach(nb=>{if(!vis.has(nb))c+=countDesc(nb,vis)});
        return c;
      }
      const chain=[];const chainSet=new Set();
      let cur=root.id;const walkVis=new Set();
      while(cur!=null){
        chain.push(cur);chainSet.add(cur);walkVis.add(cur);
        const neighbors=(adj[cur]||[]).filter(nid=>!walkVis.has(nid));
        if(!neighbors.length)break;
        const nonLeafNb=neighbors.filter(nid=>!isLeaf[nid]);
        if(!nonLeafNb.length)break;
        let best=null,bestScore=-1;
        nonLeafNb.forEach(nid=>{
          const score=countDesc(nid,new Set(walkVis));
          if(score>bestScore){bestScore=score;best=nid}
        });
        cur=best;
      }

      // Collect leaves grouped by nearest chain ancestor
      const leafGroups={};
      chain.forEach(cid=>{leafGroups[cid]=[]});
      comp.forEach(n=>{
        if(chainSet.has(n.id))return;
        let p=n.id;
        while(p&&!chainSet.has(p))p=parentOf[p];
        const ancestor=p||chain[chain.length-1];
        if(!leafGroups[ancestor])leafGroups[ancestor]=[];
        leafGroups[ancestor].push(n);
      });

      // Compute layout metrics for this component
      let nonEndSlots=0;
      chain.forEach((cid,ci)=>{
        nonEndSlots++;
        if((leafGroups[cid]||[]).length&&ci<chain.length-1)nonEndSlots++;
      });
      let tiersAbove=0,tiersBelow=0;
      chain.forEach((cid,ci)=>{
        const lv=leafGroups[cid]||[];
        if(!lv.length)return;
        const isLast=(ci===chain.length-1);
        let ta,tb;
        if(!isLast){ta=Math.ceil(lv.length/2);tb=Math.floor(lv.length/2)}
        else{ta=lv.length>=2?Math.ceil((lv.length-1)/2):0;tb=lv.length>=2?Math.floor((lv.length-1)/2):0}
        if(ta>tiersAbove)tiersAbove=ta;
        if(tb>tiersBelow)tiersBelow=tb;
      });

      compDataArr.push({compIds,chain,leafGroups,nonEndSlots,tiersAbove,tiersBelow,
        hasEndLeaves:(leafGroups[chain[chain.length-1]]||[]).length>0});
    });

    // Aggregate floor-level metrics: max nonEndSlots across components (for global column alignment)
    const maxCompNonEndSlots=Math.max(0,...compDataArr.map(c=>c.nonEndSlots));
    floorData[fid]={allIds,components:compDataArr,maxCompNonEndSlots,
      hasEndLeaves:compDataArr.some(c=>c.hasEndLeaves)};
  });

  // ═══ Global column alignment: end leaves right-aligned across all floors ═══
  const maxNonEnd=Math.max(...Object.values(floorData).map(d=>d.maxCompNonEndSlots));
  const anyEnd=Object.values(floorData).some(d=>d.hasEndLeaves);
  const globalEndCol=anyEnd?maxNonEnd:-1;

  // ═══ Phase 2: Place nodes — each component on its own row (stacked vertically) ═══
  floorIds.forEach(fid=>{
    const fd=floorData[fid];

    fd.components.forEach((comp,compIdx)=>{
      if(compIdx>0)curY+=gapV*0.5; // gap between components within same floor
      const chainY=curY+comp.tiersAbove*gapV;

      let slotIdx=0;
      comp.chain.forEach((cid,i)=>{
        const n=nodes.find(nd=>nd.id===cid);
        if(n){n.x=startX+slotIdx*gapH;n.y=chainY}
        slotIdx++;
        const leaves=comp.leafGroups[cid]||[];
        const isLast=(i===comp.chain.length-1);
        if(leaves.length){
          if(!isLast){
            // Non-end: leaves in adjacent column, above/below chainY
            const leafX=startX+slotIdx*gapH;
            leaves.forEach((ln,j)=>{
              ln.x=leafX;
              const t=Math.floor(j/2)+1;
              ln.y=(j%2===0)?chainY-t*gapV:chainY+t*gapV;
            });
            slotIdx++;
          }else{
            // End leaves: right-aligned to global column
            const leafX=startX+(globalEndCol>=0?globalEndCol:slotIdx)*gapH;
            leaves.forEach((ln,j)=>{
              ln.x=leafX;
              if(j===0)ln.y=chainY;
              else{const t=Math.ceil(j/2);ln.y=(j%2===1)?chainY-t*gapV:chainY+t*gapV}
            });
          }
        }
      });

      // Advance Y past this component's below-tiers
      curY=chainY+comp.tiersBelow*gapV+gapV;
    });

    // Update edge ports and routing for this floor group
    edges.forEach(e=>{
      if(!fd.allIds.has(e.sourceId)||!fd.allIds.has(e.targetId))return;
      const src=nodes.find(n=>n.id===e.sourceId);
      const tgt=nodes.find(n=>n.id===e.targetId);
      if(!src||!tgt)return;
      const leftIsSource=src.x<=tgt.x;
      const left=leftIsSource?src:tgt;
      const right=leftIsSource?tgt:src;
      const dy=right.y-left.y;
      let lPort,rPort,rMode;
      if(Math.abs(dy)<NODE_SIZE/2){
        lPort='right';rPort='left';rMode='ortho3';
      }else if(dy<0){
        lPort='top';rPort='left';rMode='ortho2';
      }else{
        lPort='bottom';rPort='left';rMode='ortho2';
      }
      e.sourcePort=leftIsSource?lPort:rPort;
      e.targetPort=leftIsSource?rPort:lPort;
      e.routeMode=rMode;
      delete e.midPos;
    });

    // Extra gap between floors
    curY+=gapV*0.5;
  });

  // ═══ Phase 3: Align central_room areas with floor chains ═══
  // Strategy: preserve relative positions of devices WITHIN the area,
  // translate the entire group (area + devices) as a unit.
  const _roomNodeIds=new Set(); // track moved room nodes for debug
  if(typeof topoAreas!=='undefined'&&topoAreas.length){
    const centralRooms=topoAreas.filter(a=>(a.area_type||'normal')==='central_room');
    if(centralRooms.length){
      const roomGap=gapH*0.6; // gap between area right edge and floor chain left edge

      centralRooms.forEach(area=>{
        // Find topology nodes inside this central_room area (using original positions)
        const roomNodes=topoNodes.filter(n=>{
          const cx=n.x+n.w/2,cy=n.y+n.h/2;
          return cx>=area.x&&cx<=area.x+area.width&&cy>=area.y&&cy<=area.y+area.height;
        });
        if(!roomNodes.length)return;
        roomNodes.forEach(n=>_roomNodeIds.add(n.id));

        // Find anchor: room node connected to a floor chain node, for Y alignment
        let anchorRoomNode=null,anchorFloorNode=null;
        for(const rn of roomNodes){
          for(const e of edges){
            const floorNid=(e.sourceId===rn.id&&placedNodeIds.has(e.targetId))?e.targetId:
                           (e.targetId===rn.id&&placedNodeIds.has(e.sourceId))?e.sourceId:null;
            if(floorNid){
              const fn=nodes.find(n=>n.id===floorNid);
              if(fn){anchorRoomNode=rn;anchorFloorNode=fn;break}
            }
          }
          if(anchorRoomNode)break;
        }

        // Calculate translation deltas (preserve relative positions)
        const targetAreaX=startX-roomGap-area.width;
        const dx=targetAreaX-area.x;
        let dy=0;
        if(anchorRoomNode&&anchorFloorNode){
          // Align anchor room node Y with its connected floor node Y
          dy=anchorFloorNode.y-anchorRoomNode.y;
        }

        // Translate entire group: area + all contained nodes
        area.x+=dx;
        area.y+=dy;
        roomNodes.forEach(n=>{n.x+=dx;n.y+=dy});

        // Update edge ports for room→floor connections (horizontal routing)
        roomNodes.forEach(rn=>{
          edges.forEach(e=>{
            const isSource=e.sourceId===rn.id;
            const isTarget=e.targetId===rn.id;
            if(!isSource&&!isTarget)return;
            const otherNid=isSource?e.targetId:e.sourceId;
            if(!placedNodeIds.has(otherNid))return;
            const fn=nodes.find(n=>n.id===otherNid);
            if(!fn)return;
            // Room node is left, floor node is right
            const dy2=fn.y-rn.y;
            if(Math.abs(dy2)<NODE_SIZE/2){
              // Same row: horizontal connection
              if(isSource){e.sourcePort='right';e.targetPort='left'}
              else{e.sourcePort='left';e.targetPort='right'}
              e.routeMode='ortho3';
            }else{
              // Different row: use ortho2
              if(isSource){e.sourcePort=dy2<0?'top':'bottom';e.targetPort='left'}
              else{e.sourcePort='left';e.targetPort=dy2<0?'top':'bottom'}
              e.routeMode='ortho2';
            }
            delete e.midPos;
          });
        });

        console.log(`Central room "${area.label}": ${roomNodes.length} nodes, translated Δ=(${dx.toFixed(0)},${dy.toFixed(0)}), area at (${area.x.toFixed(0)},${area.y.toFixed(0)}) ${area.width}×${area.height}`);
      });
    }
  }

  // ═══ DEBUG: snapshot after layout ═══
  console.log('--- AFTER LAYOUT ---');
  let movedTopo=0;
  nodes.forEach(n=>{
    const before=_dbgBefore[n.id];
    if(!before)return;
    const dx=Math.abs(n.x-before.x),dy=Math.abs(n.y-before.y);
    if(dx>0.5||dy>0.5){
      const isRoom=_roomNodeIds.has(n.id);
      const tag=before.placed?'✅ FLOOR (expected)':isRoom?'🏢 ROOM (expected)':'❌ TOPO (SHOULD NOT MOVE!)';
      console.log(`  ${tag} [${n.id}] ${n.name}: (${before.x},${before.y}) → (${n.x},${n.y}) Δ=(${dx.toFixed(1)},${dy.toFixed(1)})`);
      if(!before.placed&&!isRoom)movedTopo++;
    }
  });
  // Also check edges that changed
  console.log('Edges connecting topo↔floor:');
  edges.forEach(e=>{
    const sPlaced=placedNodeIds.has(e.sourceId),tPlaced=placedNodeIds.has(e.targetId);
    if(sPlaced!==tPlaced){
      const sn=nodes.find(n=>n.id===e.sourceId),tn=nodes.find(n=>n.id===e.targetId);
      console.log(`  edge ${sn?.name}→${tn?.name} ports: ${e.sourcePort}→${e.targetPort} route:${e.routeMode}`);
    }
  });
  if(movedTopo)console.error(`⚠️ ${movedTopo} topology-only nodes were moved! This is a bug.`);
  else console.log('✅ No topology-only nodes were moved.');
  console.groupEnd();
  // ═══ END DEBUG AFTER ═══

  hasUnsavedChanges=true;
  renderAll();
  // Don't call fitView() — keep viewport stable so topology devices appear unmoved
}

function addNodeToFloorPlan(sub,x,y){
  if(DIAGRAM_CONFIG.readOnly)return null;
  const fpId=currentView;
  const fp=getFloorPlan(fpId);
  if(!fp)return null;

  // Riser constraint check — use drop center for hit-testing
  const dropCx=x+NODE_SIZE/2, dropCy=y+NODE_SIZE/2;
  const riserArea=(fp.areas||[]).find(a=>
    a.is_riser && dropCx>=a.x && dropCx<=a.x+a.width && dropCy>=a.y && dropCy<=a.y+a.height
  );
  if(riserArea){
    const hasRealDevice=fp.placements.some(p=>{
      if(p.x<riserArea.x||p.x>riserArea.x+riserArea.width||p.y<riserArea.y||p.y>riserArea.y+riserArea.height)return false;
      const n=nodes.find(n=>n.id===p.node_id);return n&&!n.is_riser_node;
    });
    if(hasRealDevice){showToast(_t('弱电井区域只能放置1个设备'));return null}
    removeRiserNode(fp,riserArea);
    x=riserArea.x+riserArea.width/2-NODE_SIZE/2; y=riserArea.y+riserArea.height/2-NODE_SIZE/2;
  }

  // Create node with compact topology position (not floor plan coords)
  const topoPos=computeNextTopoPosition();
  const node=addNode(sub,topoPos.x,topoPos.y);
  if(!node)return null;

  // Mark as floor-plan-created (full delete when removed from floor)
  node._floorCreated=true;

  // Add placement to floor plan (placement has its own coords)
  node.floor_id=fpId;
  node.floor_label=fp.label;
  fp.placements.push({node_id:node.id,x:x,y:y,locked:false,rotation:0});

  syncFloorAreaLabels();
  hasUnsavedChanges=true;
  renderAll();
  selectNode(node.id);
  return node;
}

function placeExistingNodeOnFloor(nodeId,x,y){
  const fp=getFloorPlan(currentView);if(!fp)return;
  const n=nodes.find(n=>n.id===nodeId);if(!n)return;
  // Riser constraint check — use drop center for hit-testing
  const dropCx=x+NODE_SIZE/2, dropCy=y+NODE_SIZE/2;
  const riserArea=(fp.areas||[]).find(a=>
    a.is_riser && dropCx>=a.x && dropCx<=a.x+a.width && dropCy>=a.y && dropCy<=a.y+a.height
  );
  if(riserArea){
    const hasRealDevice=fp.placements.some(p=>{
      if(p.x<riserArea.x||p.x>riserArea.x+riserArea.width||p.y<riserArea.y||p.y>riserArea.y+riserArea.height)return false;
      const nd=nodes.find(n=>n.id===p.node_id);return nd&&!nd.is_riser_node;
    });
    if(hasRealDevice){showToast(_t('弱电井区域只能放置1个设备'));return}
    removeRiserNode(fp,riserArea);
    x=riserArea.x+riserArea.width/2-NODE_SIZE/2; y=riserArea.y+riserArea.height/2-NODE_SIZE/2;
  }
  const qty=n.qty||1;
  let totalPlaced=0;
  floorPlans.forEach(f=>{f.placements.forEach(p=>{if(p.node_id===nodeId)totalPlaced+=(p.qty||1)})});
  if(totalPlaced>=qty){showToast(_t('该设备数量已全部放置'));return}
  // If already on this floor, add qty to existing placement (if room)
  const existing=fp.placements.find(p=>p.node_id===nodeId);
  pushHistory();
  if(existing){
    const maxAdd=qty-totalPlaced;
    if(maxAdd>0){existing.qty=(existing.qty||1)+1;showToast(`${_t('数量+1')} (${_t('当前')} ${existing.qty})`)}
    else{showToast(_t('该设备数量已全部放置'));return}
  }else{
    fp.placements.push({node_id:nodeId,x:Math.round(x/10)*10,y:Math.round(y/10)*10,locked:false,rotation:0,qty:1});
    n.floor_id=fp.id;n.floor_label=fp.label;
    showToast(_t('已放置到楼层'));
  }
  syncFloorAreaLabels();
  hasUnsavedChanges=true;renderAll();selectNode(nodeId);
  buildExistingDevicesPanel();
}

// ====== LOCK / UNLOCK ======
function toggleNodeLock(nodeId){
  const fpId=currentView;
  const fp=getFloorPlan(fpId);
  if(!fp)return;
  const pl=fp.placements.find(p=>p.node_id===nodeId);
  if(!pl)return;
  pushHistory();
  pl.locked=!pl.locked;
  hasUnsavedChanges=true;
  renderAll();
  showToast(pl.locked?_t('已锁定'):_t('已解锁'));
}

function toggleAllLocks(){
  pushHistory();
  let anyUnlocked=false;
  if(currentView==='topology'){
    // Topology mode: toggle node.locked
    anyUnlocked=nodes.some(n=>!n.locked);
    nodes.forEach(n=>{n.locked=anyUnlocked});
  } else {
    const fp=getFloorPlan(currentView);
    if(!fp)return;
    anyUnlocked=fp.placements.some(p=>!p.locked);
    fp.placements.forEach(p=>{p.locked=anyUnlocked});
  }
  hasUnsavedChanges=true;
  renderAll();
  _updateLockBtnIcon(anyUnlocked);
  showToast(anyUnlocked?_t('全部已锁定'):_t('全部已解锁'));
}
function _updateLockBtnIcon(locked){
  const btn=document.getElementById('btnToggleLock');
  if(!btn)return;
  const svg=btn.querySelector('svg');
  if(svg){
    // Locked: closed lock (no gap in shackle)
    // Unlocked: open lock (shackle shifted up-right)
    svg.innerHTML=locked
      ?'<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/>'
      :'<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0"/>';
  }
  btn.style.background=locked?'#f59e0b':'';
  btn.style.color=locked?'#fff':'';
  if(locked){btn.querySelector('svg').setAttribute('stroke','#fff')}
  else{btn.querySelector('svg').setAttribute('stroke','currentColor')}
}

// ====== FLOOR/AREA LABEL SYNC ======
function syncFloorAreaLabels(){
  floorPlans.forEach(fp=>{
    fp.placements.forEach(p=>{
      const node=nodes.find(n=>n.id===p.node_id);
      if(!node)return;
      node.floor_id=fp.id;
      node.floor_label=fp.label;
      // Find smallest containing area
      const area=(fp.areas||[]).find(a=>
        p.x>=a.x && p.x<=a.x+a.width &&
        p.y>=a.y && p.y<=a.y+a.height
      );
      node.area_label=area?area.label:'';
    });
  });
}

// ====== CALIBRATION ======
let isCalibrating=false,calibrateStart=null;

// ====== AREA DRAWING ======
let isDrawingArea=false,areaDrawStart=null,areaIdCounter=400;
let selectedAreaId=null,isDraggingArea=false,dragAreaId=null,areaDragOffset={x:0,y:0};
let isResizingArea=false,resizeAreaId=null,resizeHandle='',resizeAreaStart=null;
let selectedRouteId=null;

function onAreaMouseDown(e){
  if(DIAGRAM_CONFIG.readOnly)return;
  if(currentTool==='calibrate'&&currentView!=='topology'){
    const pt=svgPoint(e);
    const fp=getFloorPlan(currentView);
    if(!fp||!fp.background){showToast(_t('请先上传背景图'));setTool('select');return}
    e.preventDefault();e.stopPropagation();
    if(!isCalibrating){
      // First click: record start
      isCalibrating=true;calibrateStart=pt;
    }else{
      // Second click: finish line
      const x1=calibrateStart.x,y1=calibrateStart.y,x2=pt.x,y2=pt.y;
      const pixelLength=Math.sqrt((x2-x1)**2+(y2-y1)**2);
      if(pixelLength<10){showToast(_t('线段太短，请重新画'));isCalibrating=false;calibrateStart=null;document.getElementById('tempLayer').innerHTML='';return}
      isCalibrating=false;calibrateStart=null;
      document.getElementById('tempLayer').innerHTML='';
      // Store temp calibration data for the props panel
      fp._calibTemp={x1,y1,x2,y2,pixelLength};
      setTool('select');
      showCalibrationProps(fp);
    }
    return;
  }
  if(currentTool==='area'){
    isDrawingArea=true;areaDrawStart=svgPoint(e);e.preventDefault();e.stopPropagation();return;
  }
}

function onAreaMouseMove(e){
  if(isCalibrating&&calibrateStart){
    const pt=svgPoint(e);
    const temp=document.getElementById('tempLayer');
    temp.innerHTML=`<line x1="${calibrateStart.x}" y1="${calibrateStart.y}" x2="${pt.x}" y2="${pt.y}" stroke="#f59e0b" stroke-width="2" stroke-dasharray="6 3"/>
    <circle cx="${calibrateStart.x}" cy="${calibrateStart.y}" r="4" fill="#f59e0b" stroke="#fff" stroke-width="1"/>
    <circle cx="${pt.x}" cy="${pt.y}" r="4" fill="#f59e0b" stroke="#fff" stroke-width="1"/>`;
  }
  if(isDrawingArea&&areaDrawStart){
    const pt=svgPoint(e);
    const x=Math.min(areaDrawStart.x,pt.x),y=Math.min(areaDrawStart.y,pt.y);
    const w=Math.abs(pt.x-areaDrawStart.x),h=Math.abs(pt.y-areaDrawStart.y);
    const temp=document.getElementById('tempLayer');
    temp.innerHTML=`<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="rgba(59,130,246,.08)" stroke="#3b82f6" stroke-width="1.5" stroke-dasharray="6 3" rx="4"/>`;
  }
  if(isDraggingArea&&dragAreaId!=null){
    const areas=getAreaStorage();if(!areas)return;
    const area=areas.find(a=>a.id===dragAreaId);if(!area)return;
    const pt=svgPoint(e);
    area.x=Math.round((pt.x-areaDragOffset.x)/10)*10;
    area.y=Math.round((pt.y-areaDragOffset.y)/10)*10;
    hasUnsavedChanges=true;isDraggingOperation=true;requestRenderThrottled();
  }
  if(isResizingArea&&resizeAreaId!=null){
    const areas=getAreaStorage();if(!areas)return;
    const area=areas.find(a=>a.id===resizeAreaId);if(!area||!resizeAreaStart)return;
    const pt=svgPoint(e);const s=resizeAreaStart;
    if(resizeHandle.includes('r')){area.width=Math.max(40,s.w+(pt.x-s.mx))}
    if(resizeHandle.includes('b')){area.height=Math.max(40,s.h+(pt.y-s.my))}
    if(resizeHandle.includes('l')){const dx=pt.x-s.mx;area.x=s.x+dx;area.width=Math.max(40,s.w-dx)}
    if(resizeHandle.includes('t')){const dy=pt.y-s.my;area.y=s.y+dy;area.height=Math.max(40,s.h-dy)}
    hasUnsavedChanges=true;isDraggingOperation=true;requestRenderThrottled();
  }
}

function onAreaMouseUp(e){
  if(isDrawingArea&&areaDrawStart){
    const pt=svgPoint(e);
    const x=Math.min(areaDrawStart.x,pt.x),y=Math.min(areaDrawStart.y,pt.y);
    const w=Math.abs(pt.x-areaDrawStart.x),h=Math.abs(pt.y-areaDrawStart.y);
    document.getElementById('tempLayer').innerHTML='';
    isDrawingArea=false;areaDrawStart=null;
    if(w<40||h<40){showToast(_t('区域太小，请拖大一些'));return}
    const areas=getAreaStorage();if(!areas)return;
    pushHistory();
    const newArea={id:areaIdCounter++,label:_t('区域'),x:Math.round(x),y:Math.round(y),width:Math.round(w),height:Math.round(h),color:'#3b82f6',opacity:0.08,is_riser:false,area_type:'normal'};
    areas.push(newArea);
    selectedAreaId=newArea.id;
    if(currentView!=='topology')syncFloorAreaLabels();
    hasUnsavedChanges=true;renderAll();
    setTool('select');
    showAreaProps(newArea.id);
    // Auto focus name input for immediate editing
    setTimeout(()=>{const inp=document.querySelector('#propsContent .props-input');if(inp){inp.focus();inp.select()}},50);
  }
  if(isDraggingArea){
    isDraggingArea=false;dragAreaId=null;if(currentView!=='topology')syncFloorAreaLabels();
    isDraggingOperation=false;if(pendingRenderFrame){cancelAnimationFrame(pendingRenderFrame);pendingRenderFrame=null}renderAll();
  }
  if(isResizingArea){
    isResizingArea=false;resizeAreaId=null;resizeAreaStart=null;if(currentView!=='topology')syncFloorAreaLabels();
    isDraggingOperation=false;if(pendingRenderFrame){cancelAnimationFrame(pendingRenderFrame);pendingRenderFrame=null}renderAll();
  }
}

// Hook area events into SVG
svg.addEventListener('mousedown',onAreaMouseDown,true);
document.addEventListener('mousemove',onAreaMouseMove);
document.addEventListener('mouseup',onAreaMouseUp);

// ====== FLOOR PLAN PROPERTIES ======
function showFloorNodeProps(id){
  const n=nodes.find(n=>n.id===id);if(!n)return;
  const fp=getFloorPlan(currentView);if(!fp)return;
  const pl=fp.placements.find(p=>p.node_id===id);

  if(n.floor_id){
    // Floor-created device — reuse topology's full editing panel
    showNodeProps(id);
    // Append floor-specific fields (lock, rotation) and replace delete button
    const content=document.getElementById('propsContent');
    const delBtn=content.querySelector('.btn-delete');
    if(delBtn){
      // Insert placement fields before delete button
      const extra=document.createElement('div');
      extra.innerHTML=`${pl?`<div class="props-field"><label style="display:flex;align-items:center;gap:8px;cursor:pointer;"><input type="checkbox" ${pl.locked?'checked':''} onchange="toggleNodeLock(${id})"><span class="props-label" style="margin:0;">${_t('锁定位置')}</span></label></div>
      <div class="props-field"><span class="props-label">${_t('旋转角度')}</span><input class="props-input" type="number" min="0" max="360" step="15" value="${pl.rotation||0}" oninput="updatePlacementRotation(${id},parseInt(this.value)||0)"></div>`:''}`;

      while(extra.firstChild)content.insertBefore(extra.firstChild,delBtn);
      // Replace "删除节点" with "删除设备" using floor-specific delete
      delBtn.textContent=_t('删除设备');
      delBtn.setAttribute('onclick',`deleteFloorCreatedNode(${id})`);
    }
    return;
  }
  // Existing device from topology — simplified placement panel
  const panel=document.getElementById('propsPanel');
  panel.classList.add('visible');
  document.getElementById('propsTitle').innerHTML=`<div style="display:flex;align-items:center;gap:8px;">${renderIconPanel(n.iconData).replace('<svg','<svg width="24" height="24"')} ${_t('设备属性')}</div>`;
  const nodeQty=n.qty||1;
  let usedElsewhere=0;
  floorPlans.forEach(f=>{f.placements.forEach(p=>{if(p.node_id===id&&p!==pl)usedElsewhere+=(p.qty||1)})});
  const maxQty=nodeQty-usedElsewhere;
  const plQty=pl?(pl.qty||1):1;
  document.getElementById('propsContent').innerHTML=`
    <div class="props-field"><span class="props-label">${_t('名称')}</span><input class="props-input" value="${n.name}" disabled></div>
    ${n.model?`<div class="props-field"><span class="props-label">${_t('型号')}</span><input class="props-input" value="${n.model}" disabled></div>`:''}
    <div class="props-field"><span class="props-label">${_t('位置')}</span><input class="props-input" value="X: ${Math.round(pl?pl.x:n.x)}, Y: ${Math.round(pl?pl.y:n.y)}" disabled></div>
    ${pl?`
    <div class="props-field"><span class="props-label">${_t('数量')}</span>
      <div style="display:flex;align-items:center;gap:6px;">
        <input class="props-input" type="number" min="1" max="${maxQty}" value="${plQty}" style="flex:1;"
          oninput="updatePlacementQty(${id},parseInt(this.value)||1,${maxQty})">
        <span style="font-size:10px;color:var(--text-muted);white-space:nowrap;">${_t('上限')} ${maxQty}</span>
      </div>
    </div>
    <div class="props-field">
      <label style="display:flex;align-items:center;gap:8px;cursor:pointer;">
        <input type="checkbox" ${pl.locked?'checked':''} onchange="toggleNodeLock(${id})">
        <span class="props-label" style="margin:0;">${_t('锁定位置')}</span>
      </label>
    </div>
    <div class="props-field"><span class="props-label">${_t('旋转角度')}</span>
      <input class="props-input" type="number" min="0" max="360" step="15" value="${pl.rotation||0}"
        oninput="updatePlacementRotation(${id},parseInt(this.value)||0)">
    </div>
    `:''}
    ${buildCoveragePropsHTML(id)}
    <button class="btn-delete" onclick="removeFromFloorPlan(${id})">${_t('从楼层移除')}</button>`;
}

function deleteFloorCreatedNode(id){
  const n=nodes.find(n=>n.id===id);if(!n||!n.floor_id)return;
  pushHistory();
  // Remove related edges and floor routes
  const relEdgeIds=edges.filter(e=>e.sourceId===id||e.targetId===id).map(e=>e.id);
  edges=edges.filter(e=>e.sourceId!==id&&e.targetId!==id);
  floorPlans.forEach(fp=>{fp.routes=fp.routes.filter(r=>r.sourceNodeId!==id&&r.targetNodeId!==id)});
  // Remove placements
  floorPlans.forEach(fp=>{fp.placements=fp.placements.filter(p=>p.node_id!==id)});
  // Remove node
  nodes=nodes.filter(n=>n.id!==id);
  selectedNodeId=null;selectedNodeIds=new Set();selectedRouteId=null;
  hasUnsavedChanges=true;renderAll();hideProps();
  if(typeof highlightConnectedInPanel==='function')highlightConnectedInPanel(null);
  if(typeof buildExistingDevicesPanel==='function')buildExistingDevicesPanel();
}

function updatePlacementRotation(nodeId,angle){
  const fp=getFloorPlan(currentView);if(!fp)return;
  const pl=fp.placements.find(p=>p.node_id===nodeId);
  if(!pl)return;
  pushHistoryProp();
  pl.rotation=angle;
  hasUnsavedChanges=true;
  renderAll();
}

// updateLabelPosition, showFloorNodeCtxMenu, hideFloorNodeCtxMenu moved to core.js
// as unified showNodeCtxMenu() and updateNodeLabelPosition()

function updateCoverageRadius(nodeId, idx, val) {
  const n = nodes.find(nd => nd.id === nodeId);
  if (!n) return;
  pushHistoryProp();
  if (!n.coverageRadii) n.coverageRadii = [...coverageRadiiFromN(n.coverageN)];
  if (n.coverageRadii.length > 2) n.coverageRadii = n.coverageRadii.slice(0, 2);
  n.coverageRadii[idx] = Math.max(0, parseFloat(val) || 0);
  hasUnsavedChanges = true;
  renderAll();
}

function updateCoverageVisible(nodeId, idx, val) {
  const n = nodes.find(nd => nd.id === nodeId);
  if (!n) return;
  pushHistoryProp();
  if (!n.coverageVisible) n.coverageVisible = [true, true];
  if (n.coverageVisible.length > 2) n.coverageVisible = n.coverageVisible.slice(0, 2);
  n.coverageVisible[idx] = val;
  hasUnsavedChanges = true;
  renderAll();
}

function updateCoverageEnv(nodeId, nVal) {
  const n = nodes.find(nd => nd.id === nodeId);
  if (!n) return;
  pushHistoryProp();
  n.coverageN = nVal;
  if (n.coverageRadii) delete n.coverageRadii;
  hasUnsavedChanges = true;
  _heatmapCache.stamp = null;
  renderAll();
  if (typeof showFloorNodeProps === 'function') showFloorNodeProps(nodeId);
}

function resetCoverageRadii(nodeId) {
  const n = nodes.find(nd => nd.id === nodeId);
  if (!n) return;
  pushHistoryProp();
  delete n.coverageRadii;
  hasUnsavedChanges = true;
  renderAll();
  if (typeof showFloorNodeProps === 'function') showFloorNodeProps(nodeId);
}

function updatePlacementQty(nodeId,val,maxQty){
  const fp=getFloorPlan(currentView);if(!fp)return;
  const pl=fp.placements.find(p=>p.node_id===nodeId);
  if(!pl)return;
  pushHistoryProp();
  pl.qty=Math.max(1,Math.min(val,maxQty));
  hasUnsavedChanges=true;
  renderAll();
  if(typeof buildExistingDevicesPanel==='function')buildExistingDevicesPanel();
}

function removeFromFloorPlan(nodeId){
  const fp=getFloorPlan(currentView);if(!fp)return;
  pushHistory();
  fp.placements=fp.placements.filter(p=>p.node_id!==nodeId);
  const n=nodes.find(n=>n.id===nodeId);
  if(n){n.floor_id=null;n.floor_label='';n.area_label=''}
  syncRiserNodes(fp);
  hasUnsavedChanges=true;
  renderAll();hideProps();
  if(typeof buildExistingDevicesPanel==='function')buildExistingDevicesPanel();
  showToast(_t('已从楼层移除'));
}
