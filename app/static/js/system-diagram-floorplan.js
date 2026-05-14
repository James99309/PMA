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
const COVERAGE_THRESHOLDS = [-65, -85]; // inner=strong signal, mid=uplink boundary
function coverageRadiiFromN(n) {
  const rx1m = -14.5; // _HM_RX1M
  return COVERAGE_THRESHOLDS.map(th => {
    const r = Math.pow(10, (rx1m - th) / (10 * (n || 5.1)));
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
    {zh:'中圈 (-85dBm 上行边界)', en:'Mid (-85dBm uplink)'},
  ];
  let rows = '';
  for (let i = 0; i < 2; i++) {
    const ring = COVERAGE_RINGS[i];
    rows += `<div style="display:flex;align-items:center;gap:6px;">
      <input type="checkbox" ${vis[i]!==false?'checked':''} onchange="updateCoverageVisible(${nodeId},${i},this.checked)">
      <span style="width:8px;height:8px;border-radius:50%;background:${ring.color};flex-shrink:0;"></span>
      <span style="font-size:11px;color:var(--text-secondary);min-width:90px;">${_m(ringNames[i])}</span>
      <span style="font-size:11px;color:var(--text-primary);font-weight:500;">${radii[i]} m</span>
    </div>`;
  }
  rows += `<div style="margin-top:2px;font-size:10px;color:var(--text-muted);">${_t('自动计算')}</div>`;
  const curN = n.coverageN || 5.1;
  const envOptions = [
    [3.2, {zh:'停车库 (n=3.2)', en:'Parking (n=3.2)'}],
    [4.1, {zh:'普通办公 (n=4.1)', en:'Office (n=4.1)'}],
    [5.1, {zh:'密集区域 (n=5.1)', en:'Dense (n=5.1)'}],
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

// ====== OWNERSHIP HELPERS ======
// 计算某点 (x, y) 在某个 fp 上的归属。返回 {building_id, floor_id}。
// 优先级：落入 area（有归属的）→ area 归属；否则 → fp 默认归属
function computeOwnershipAt(fp, x, y){
  if(!fp)return {building_id:null, floor_id:null};
  // 用节点中心点判定（x, y 是节点左上角，加 NODE_SIZE/2）
  const cx=x+NODE_SIZE/2, cy=y+NODE_SIZE/2;
  // 找所有命中的 area（含 building 与 floor 两种），按面积升序（嵌套时优先内层）
  const hits=(fp.areas||[]).filter(a=>
    cx>=a.x&&cx<=a.x+a.width&&cy>=a.y&&cy<=a.y+a.height
  ).sort((a,b)=>(a.width*a.height)-(b.width*b.height));
  let bld=null, fl=null;
  for(const a of hits){
    if(!bld&&a.building_id)bld=a.building_id;
    if(!fl&&a.floor_id)fl=a.floor_id;
    if(bld&&fl)break;
  }
  return {
    building_id: bld || (fp.building_id||null),
    floor_id: fl || fp.id
  };
}

// 给某节点根据其在 fp 中的 placement 应用归属（含虚拟楼层 label 解析）
function _applyOwnershipToNode(n, fp, px, py){
  if(!n||!fp)return;
  const own=computeOwnershipAt(fp, px, py);
  n.building_id=own.building_id;
  n.floor_id=own.floor_id;
  if(own.floor_id){
    const ff=floorPlans.find(f=>f.id===own.floor_id);
    if(ff){n.floor_label=ff.label||''}
    else{
      // 虚拟楼层（area.id），从 fp.areas 找 label
      const fa=(fp.areas||[]).find(a=>a.id===own.floor_id);
      if(fa)n.floor_label=fa.label||'';
    }
  }
}

// 重新计算某 area 内所有节点的归属（area 改属性时调用）
function recomputeOwnershipForArea(area){
  if(!area||currentView==='topology')return;
  const fp=getFloorPlan(currentView);if(!fp)return;
  fp.placements.forEach(p=>{
    const cx=p.x+NODE_SIZE/2, cy=p.y+NODE_SIZE/2;
    if(cx>=area.x&&cx<=area.x+area.width&&cy>=area.y&&cy<=area.y+area.height){
      const n=nodes.find(n=>n.id===p.node_id);
      _applyOwnershipToNode(n, fp, p.x, p.y);
    }
  });
}

// 重算 fp 全部 placements 的归属（area 拖动/缩放后调用，覆盖"原本在内→现在不在"的节点）
function recomputeAllPlacementOwnership(fp){
  if(!fp||!fp.placements)return;
  fp.placements.forEach(p=>{
    const n=nodes.find(n=>n.id===p.node_id);
    _applyOwnershipToNode(n, fp, p.x, p.y);
  });
}

// 重新继承 floor area 的 building_id（area 移动后调用）
function reinheritFloorAreaBuilding(area, fp){
  if(!area||area.area_type!=='floor'||!fp)return;
  const cx=area.x+area.width/2, cy=area.y+area.height/2;
  const candidates=(fp.areas||[]).filter(a=>a.id!==area.id&&a.area_type==='building'&&
    cx>=a.x&&cx<=a.x+a.width&&cy>=a.y&&cy<=a.y+a.height);
  candidates.sort((a,b)=>(a.width*a.height)-(b.width*b.height));
  area.building_id=candidates[0]?candidates[0].building_id:null;
}

// ====== FLOOR PLAN DATA ======
let floorPlans = [];
let buildings = [];
let buildingIdCounter = 1;
const BUILDING_COLORS=['#3b82f6','#f59e0b','#10b981','#ef4444','#8b5cf6','#ec4899','#06b6d4','#f97316'];

function getFloorPlansForSave(){
  return floorPlans.map(fp=>({
    id:fp.id, label:fp.label, sort_order:fp.sort_order, tab_sort_order:fp.tab_sort_order||0, building_id:fp.building_id||null,
    background:fp.background?Object.assign({url:fp.background.url,width:fp.background.width,height:fp.background.height,offset_x:fp.background.offset_x||0,offset_y:fp.background.offset_y||0,opacity:fp.background.opacity||0.3},fp.background.is_multi_res?{is_multi_res:true,resolutions:fp.background.resolutions,filenames:fp.background.filenames}:{filename:fp.background.filename||''},fp.background.bg_type?{bg_type:fp.background.bg_type}:{},fp.background.dxf_filename?{dxf_filename:fp.background.dxf_filename}:{}):null,
    calibration:fp.calibration||null,
    placements:fp.placements.map(p=>({node_id:p.node_id,x:p.x,y:p.y,locked:p.locked||false,rotation:p.rotation||0,qty:p.qty||1,labelPosition:p.labelPosition||null})),
    routes:(fp.routes||[]).map(r=>{const o={id:r.id,sourceNodeId:r.sourceNodeId,targetNodeId:r.targetNodeId,sourcePort:r.sourcePort,targetPort:r.targetPort,cableType:r.cableType,routeMode:r.routeMode,midPos:r.midPos,color:r.color,width:r.width,dash:r.dash,label:r.label,hideLabel:r.hideLabel||false,linked_edge_id:r.linked_edge_id||null,_userPorts:r._userPorts||false};if(r.waypoints&&r.waypoints.length)o.waypoints=r.waypoints;return o}),
    areas:(fp.areas||[]).map(a=>({id:a.id,label:a.label,x:a.x,y:a.y,width:a.width,height:a.height,color:a.color||'#3b82f6',opacity:a.opacity||0.08,locked:a.locked||false,is_riser:a.is_riser||false,area_type:a.area_type||'normal',_riser_node_id:a._riser_node_id||null,riser_index:a.riser_index||null,building_id:a.building_id||null,floor_id:a.floor_id||null,tab_sort_order:a.tab_sort_order||0})),
    risers:(fp.risers||[]).map(r=>({id:r.id,node_id:r.node_id,edge_id:r.edge_id,target_floor_label:r.target_floor_label,x:r.x,y:r.y})),
    viewX:fp.viewX||0, viewY:fp.viewY||0, scale:fp.scale||1
  }));
}

function getBuildingsForSave(){
  return buildings.map(b=>({id:b.id,name:b.name,color:b.color||'#3b82f6',sort_order:b.sort_order}));
}

function restoreBuildings(data){
  if(!Array.isArray(data)){buildings=[];return}
  buildings=data.map(b=>({id:b.id,name:b.name,color:b.color||'#3b82f6',sort_order:b.sort_order||0}));
  const maxId=Math.max(0,...buildings.map(b=>parseInt(b.id.replace('bld_',''))||0));
  if(maxId>=buildingIdCounter)buildingIdCounter=maxId+1;
}

function restoreFloorPlans(data){
  if(!Array.isArray(data))return;
  floorPlans=data.map(fp=>({
    id:fp.id, label:fp.label, sort_order:fp.sort_order||0, tab_sort_order:fp.tab_sort_order||0, building_id:fp.building_id||null,
    background:fp.background||null,
    calibration:fp.calibration||null,
    placements:(fp.placements||[]).map(p=>({node_id:p.node_id,x:p.x,y:p.y,locked:p.locked||false,rotation:p.rotation||0,qty:p.qty||1,labelPosition:p.labelPosition||null})),
    routes:fp.routes||[],
    areas:fp.areas||[],
    risers:fp.risers||[],
    viewX:fp.viewX||0, viewY:fp.viewY||0, scale:fp.scale||1
  }));
  // 老数据兼容：area_type='building' 的 area 自动补 buildings[] 条目
  if(typeof buildings!=='undefined'){
    floorPlans.forEach(fp=>{
      (fp.areas||[]).forEach(a=>{
        if(a.area_type==='building'){
          const bId='bld_area_'+a.id;
          if(!buildings.find(b=>b.id===bId)){
            buildings.push({
              id:bId,
              name:a.label||_t('新建筑'),
              color:a.color||'#3b82f6',
              sort_order:buildings.length+1,
              _from_area:a.id
            });
          }
          if(!a.building_id)a.building_id=bId;
        }
        if(a.area_type==='floor'&&!a.floor_id){
          a.floor_id=a.id;
        }
      });
    });
  }
  // 加载后兜底：每个 fp 重算 placements 归属（修正历史数据：节点 floor_id 还指向 fp.id 但实际落在虚拟楼层 area 内）
  if(typeof recomputeAllPlacementOwnership==='function'){
    floorPlans.forEach(fp=>{
      // 同时也给 floor area 重新继承 building_id（防止历史数据缺失）
      (fp.areas||[]).forEach(a=>{
        if(a.area_type==='floor'&&typeof reinheritFloorAreaBuilding==='function')reinheritFloorAreaBuilding(a, fp);
      });
      recomputeAllPlacementOwnership(fp);
    });
  }
  rebuildViewTabs();
  _recoverMissingDxfFilenames();
}

/**
 * Recover fp.background.dxf_filename for diagrams saved before the field was persisted.
 * Detects DXF backgrounds heuristically (is_multi_res + multiple PNG resolutions) and
 * asks the server to find the original DXF file.
 */
async function _recoverMissingDxfFilenames(){
  if(!DIAGRAM_CONFIG.diagramId)return;
  for(const fp of floorPlans){
    const bg=fp.background;
    if(!bg||!bg.is_multi_res||bg.dxf_filename)continue;
    try{
      const resp=await fetch(
        DIAGRAM_CONFIG.apiFloorBgBase+DIAGRAM_CONFIG.diagramId+'/floor-plan/find-dxf?floor_id='+encodeURIComponent(fp.id),
        {headers:{'X-CSRFToken':DIAGRAM_CONFIG.csrfToken}}
      );
      const result=await resp.json();
      if(result.success&&result.dxf_filename){
        bg.dxf_filename=result.dxf_filename;
        bg.bg_type='dxf';
      }
    }catch(e){}
  }
  if(typeof updateDwgExportMenuItem==='function')updateDwgExportMenuItem();
}

// ====== BUILDING CRUD ======

function addBuilding(name){
  if(DIAGRAM_CONFIG.readOnly)return null;
  const id='bld_'+buildingIdCounter++;
  const b={id,name:name||_t('新建筑'),color:BUILDING_COLORS[buildings.length%BUILDING_COLORS.length],sort_order:buildings.length+1};
  buildings.push(b);
  hasUnsavedChanges=true;
  rebuildViewTabs();
  return b;
}

function renameBuilding(bldId,name){
  const b=buildings.find(x=>x.id===bldId);
  if(b){pushHistoryProp();b.name=name;hasUnsavedChanges=true;rebuildViewTabs()}
}

function deleteBuilding(bldId){
  if(DIAGRAM_CONFIG.readOnly)return;
  pushHistory();
  floorPlans.forEach(fp=>{if(fp.building_id===bldId)fp.building_id=null});
  buildings=buildings.filter(b=>b.id!==bldId);
  buildings.forEach((b,i)=>b.sort_order=i+1);
  hasUnsavedChanges=true;
  rebuildViewTabs();
  hideProps();
}

function updateBuildingColor(bldId,color){
  const b=buildings.find(x=>x.id===bldId);
  if(b){pushHistoryProp();b.color=color;hasUnsavedChanges=true;rebuildViewTabs()}
}

function showBuildingProps(bldId){
  const b=buildings.find(x=>x.id===bldId);if(!b)return;
  const panel=document.getElementById('propsPanel');
  panel.classList.add('visible');
  document.getElementById('propsTitle').textContent=_t('建筑属性');
  const isRO=DIAGRAM_CONFIG.readOnly;
  const bldFloors=floorPlans.filter(fp=>fp.building_id===bldId);
  const floorsText=bldFloors.map(fp=>fp.label).join(', ')||_t('无');
  let html='';
  if(!isRO){
    html+=`<div class="props-field"><span class="props-label">${_t('建筑名称')}</span><input class="props-input" value="${b.name.replace(/"/g,'&quot;')}" oninput="renameBuilding('${bldId}',this.value)"></div>`;
    html+=`<div class="props-field"><span class="props-label">${_t('颜色')}</span><div style="display:flex;gap:6px;flex-wrap:wrap">`;
    BUILDING_COLORS.forEach(c=>{
      html+=`<div style="width:24px;height:24px;border-radius:6px;background:${c};cursor:pointer;${c===b.color?'box-shadow:0 0 0 2px var(--bg-panel),0 0 0 4px '+c:''}" onclick="updateBuildingColor('${bldId}','${c}');showBuildingProps('${bldId}')"></div>`;
    });
    html+=`</div></div>`;
  } else {
    html+=`<div class="props-field"><span class="props-label">${_t('建筑名称')}</span><div style="font-size:13px;font-weight:600;color:var(--text-primary)">${b.name}</div></div>`;
  }
  html+=`<div class="props-field"><span class="props-label">${_t('包含楼层')}</span><div style="font-size:11px;color:var(--text-secondary);line-height:1.6;">${floorsText}</div></div>`;
  if(!isRO){
    html+=`<button class="btn-delete" onclick="if(confirm(_t('删除建筑将取消所有楼层的建筑分组，楼层本身不会被删除。确认删除？')))deleteBuilding('${bldId}')">${_t('删除建筑')}</button>`;
  }
  document.getElementById('propsContent').innerHTML=html;
}

function assignFloorToBuilding(fpId,bldId){
  const fp=getFloorPlan(fpId);if(!fp)return;
  pushHistory();
  fp.building_id=bldId||null;
  hasUnsavedChanges=true;
  rebuildViewTabs();
}

// ====== BUILDING LABELS IN TOPOLOGY ======

function renderBuildingLabels(){
  if(currentView!=='topology')return;
  if(typeof buildings==='undefined'||!buildings.length)return;
  const nodesLayer=document.getElementById('nodesLayer');
  buildings.forEach(b=>{
    // 只用"被布局的楼层节点"算 bbox（含 floor_id 才算）；共享/中央机房节点(没 floor_id)的位置可能很离散，会把 label 拉偏
    const bNodes=nodes.filter(n=>n.building_id===b.id&&n.floor_id&&n.in_topology!==false);
    if(!bNodes.length)return;
    // 用中位数 X 作为标签横向锚点（防离群节点把 centerX 拉飞）
    const xs=bNodes.map(n=>n.x+(n.w||NODE_SIZE)/2).sort((a,b)=>a-b);
    const centerX=xs[Math.floor(xs.length/2)];
    const minY=Math.min(...bNodes.map(n=>n.y));
    const labelY=minY-60;
    const text=document.createElementNS('http://www.w3.org/2000/svg','text');
    text.setAttribute('class','building-label');
    text.setAttribute('x',centerX);
    text.setAttribute('y',labelY);
    text.setAttribute('text-anchor','middle');
    text.setAttribute('font-size','56');
    text.setAttribute('font-weight','700');
    text.setAttribute('fill',b.color);
    text.setAttribute('opacity','0.6');
    text.textContent=b.name;
    nodesLayer.appendChild(text);
  });
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

  // 0. Optimize initial resolution for multi-res backgrounds
  if(fp.background && fp.background.is_multi_res && fp.background.resolutions){
    const optKey = _getOptimalResolutionKey(scale);
    const optRes = fp.background.resolutions[optKey];
    if(optRes && optRes.url !== fp.background.url){
      fp.background.url = optRes.url;
    }
  }

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
  } else if (displaySettings.coverageMode !== 'heatmap' && displaySettings.showCoverage !== 'off') {
    renderCoverageCirclesLite(fp);  // drag: stroke-only circles, no fill/text/events
  }
  // isDragging + heatmap: leave coverageLayer untouched — heatmap stays visible via SVG transform

  // 5. Render manual routes (floor plan connections)
  renderFloorRoutes(fp);

  // 6. Render placed devices
  renderFloorNodes(fp);

  // 7. Floor route mid-handles
  renderFloorMidHandles(fp);

  // 7b. Floor route endpoint handles (reconnect drag)
  renderFloorRouteEndpoints(fp);

  // 7c. Floor area spotlight (dim everything outside the selected floor area)
  renderFloorSpotlight(fp);

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

  // Reuse existing element if URL unchanged.
  // 用 contains() 而非 parentNode===canvasGroup：背景图实际插在 blurWrap 子节点里，
  // 严格相等永远 false → 复用永远走不通 → calibration 后 fade 路径产生残影。
  if(cachedFloorBgImg && _cachedBgUrl===bg.url && canvasGroup.contains(cachedFloorBgImg)){
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

  // 同步清掉任何不是 oldImg 的残余 floorBgImage 元素。
  // Fade-in 分支用 onload 异步清理 oldImg：当多分辨率 URL 快速连续切换时（fitView→onScaleChanged
  // 触发的 URL swap），后一次的 imgC.onload 会移除 imgB，浏览器中断 imgB 加载导致 imgB.onload
  // 永不触发，imgB 闭包持有的 imgA 就成了画布上残留的"小地图"。
  const _bgHost=document.getElementById('blurWrap')||canvasGroup;
  _bgHost.querySelectorAll('[id="floorBgImage"]').forEach(el=>{if(el!==oldImg)el.remove()});

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
    (document.getElementById('blurWrap')||canvasGroup).insertBefore(img,(document.getElementById('blurWrap')||canvasGroup).firstChild);
  } else {
    img.setAttribute('opacity',bg.opacity||0.3);
    if(oldImg&&oldImg.parentNode)oldImg.remove();
    if(orphan&&orphan!==oldImg)if(orphan&&orphan.parentNode)orphan.remove();
    (document.getElementById('blurWrap')||canvasGroup).insertBefore(img,(document.getElementById('blurWrap')||canvasGroup).firstChild);
  }
  cachedFloorBgImg=img;
  _cachedBgUrl=bg.url;
}

// ====== AREAS ======
const AREA_TYPES={
  normal:{label:{zh:'普通',en:'Normal'},icon:''},
  floor:{label:{zh:'楼层',en:'Floor'},icon:'\uD83D\uDDC2'},
  building:{label:{zh:'建筑',en:'Building'},icon:'\uD83C\uDFE0'},
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
  // 自愈：building 类型 area 的 color 与对应 buildings[] 条目同步（防止 b.color 漂移）
  let _bldDirty=false;
  if(typeof buildings!=='undefined'){
    areas.forEach(area=>{
      if(area.area_type==='building'){
        const bId='bld_area_'+area.id;
        const b=buildings.find(b=>b.id===bId);
        if(b&&b.color!==area.color){b.color=area.color;_bldDirty=true}
        if(b&&b.name!==area.label){b.name=area.label||b.name;_bldDirty=true}
      }
    });
  }
  if(_bldDirty&&typeof rebuildViewTabs==='function')rebuildViewTabs();
  const layer=document.getElementById('edgesLayer');
  areas.forEach(area=>{
    const atype=area.area_type||((area.is_riser)?'riser':'normal');
    const isSel=selectedAreaId===area.id;
    const g=document.createElementNS('http://www.w3.org/2000/svg','g');
    g.setAttribute('class',`floor-area${isSel?' selected':''}`);g.dataset.areaId=area.id;

    // 聚光灯模式下的 floor 区域：去掉填充色，避免干扰内部清晰显示
    const _isFocusedFloor=area.area_type==='floor' && typeof _focusedFloorAreaId!=='undefined' && _focusedFloorAreaId===area.id;
    const rect=document.createElementNS('http://www.w3.org/2000/svg','rect');
    rect.setAttribute('x',area.x);rect.setAttribute('y',area.y);
    rect.setAttribute('width',area.width);rect.setAttribute('height',area.height);
    rect.setAttribute('fill',_isFocusedFloor?'none':(area.color||'#3b82f6'));
    rect.setAttribute('fill-opacity',_isFocusedFloor?0:(area.opacity||0.08));
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
      // 楼层聚光灯锁定状态：该 floor 区域不可拖动（先在 tab 上点击/或点击空白取消聚焦后才可移动）
      if(area.area_type==='floor' && typeof _focusedFloorAreaId!=='undefined' && _focusedFloorAreaId===area.id)return;
      e.stopPropagation();
      const pt=svgPoint(e);
      isDraggingArea=true;dragAreaId=area.id;
      areaDragOffset={x:pt.x-area.x,y:pt.y-area.y};
      dragAreaPrevPos={x:area.x,y:area.y};
      // Capture nodes inside this area at drag start
      if(currentView==='topology'){
        dragAreaContainedNodeIds=nodes.filter(n=>{
          const cx=n.x+(n.w||NODE_SIZE)/2,cy=n.y+(n.h||NODE_SIZE)/2;
          return cx>=area.x&&cx<=area.x+area.width&&cy>=area.y&&cy<=area.y+area.height;
        }).map(n=>n.id);
      }else{
        const fp=getFloorPlan(currentView);
        dragAreaContainedNodeIds=fp?(fp.placements||[]).filter(p=>{
          const cx=p.x+NODE_SIZE/2,cy=p.y+NODE_SIZE/2;
          return cx>=area.x&&cx<=area.x+area.width&&cy>=area.y&&cy<=area.y+area.height;
        }).map(p=>p.node_id):[];
      }
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

// 聚光灯：focused floor area 时，用 4 个 HTML div + backdrop-filter 包围区域外侧实现毛玻璃。
// GPU 合成层负责 blur，缩放/拖动时只需更新 div 位置（不用重做光栅化），性能远优于 SVG filter:blur。
function renderFloorSpotlight(fp){
  const mask=document.getElementById('spotlightMask');
  if(!mask)return;
  const focusedId=(typeof _focusedFloorAreaId!=='undefined')?_focusedFloorAreaId:null;
  if(!focusedId){mask.style.display='none';return}
  const area=(fp.areas||[]).find(a=>a.id===focusedId);
  if(!area||area.area_type!=='floor'){mask.style.display='none';return}
  mask.style.display='block';
  positionSpotlightMask(area);
}

// 计算 area 在屏幕坐标的矩形并定位 4 个 backdrop-filter 面板
function positionSpotlightMask(area){
  const mask=document.getElementById('spotlightMask');
  if(!mask||mask.style.display==='none')return;
  // 世界坐标 → 屏幕坐标（canvasGroup 的 transform 是 translate(viewX,viewY) scale(scale)）
  const sx=(area.x*scale)+viewX;
  const sy=(area.y*scale)+viewY;
  const sw=area.width*scale;
  const sh=area.height*scale;
  const T=document.getElementById('spotPaneT');
  const B=document.getElementById('spotPaneB');
  const L=document.getElementById('spotPaneL');
  const R=document.getElementById('spotPaneR');
  if(T){T.style.height=Math.max(0,sy)+'px'}
  if(B){B.style.top=(sy+sh)+'px';B.style.height='100%'}
  if(L){L.style.top=sy+'px';L.style.height=sh+'px';L.style.width=Math.max(0,sx)+'px'}
  if(R){R.style.top=sy+'px';R.style.height=sh+'px';R.style.left=(sx+sw)+'px'}
}

function showAreaProps(areaId){
  const areas=getAreaStorage();if(!areas)return;
  const area=areas.find(a=>a.id===areaId);if(!area)return;
  const atype=area.area_type||(area.is_riser?'riser':'normal');
  const panel=document.getElementById('propsPanel');
  panel.classList.add('visible');
  document.getElementById('propsTitle').textContent=_t('区域属性');
  // 系统图 topoArea 不允许 building/floor 类型（系统图区域只是视觉框）
  const isTopo=currentView==='topology';
  const typeOptions=Object.entries(AREA_TYPES)
    .filter(([k])=>!(isTopo&&(k==='building'||k==='floor')))
    .map(([k,v])=>`<option value="${k}"${k===atype?' selected':''}>${_m(v.label)}</option>`).join('');

  document.getElementById('propsContent').innerHTML=`
    <div class="props-field"><span class="props-label">${_t('名称')}</span><input class="props-input" value="${area.label}" oninput="updateAreaProp(${areaId},'label',this.value)"></div>
    ${atype==='riser'?`<div class="props-field"><span class="props-label">${_t('编号')}</span><input type="number" class="props-input" min="1" value="${area.riser_index||''}" oninput="updateRiserIndex(${areaId},parseInt(this.value)||null)"></div>`:''}
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
  // Auto-assign riser_index when becoming riser
  if(newType==='riser'&&!area.riser_index){
    const fp=getFloorPlan(currentView);
    if(fp){
      const maxIdx=Math.max(0,...(fp.areas||[]).filter(a=>a.is_riser&&a.riser_index).map(a=>a.riser_index));
      area.riser_index=maxIdx+1;
      area.label=(area.label||_t('弱电井')).replace(/-\d+$/,'') + '-' + area.riser_index;
    }
  }
  if(newType!=='riser'){area.riser_index=null}
  // Floor plan riser node logic
  if(currentView!=='topology'){
    const fp=getFloorPlan(currentView);
    if(fp){
      if(oldType==='riser'&&newType!=='riser')removeRiserNode(fp,area);
      if(oldType!=='riser'&&newType==='riser')toggleRiser(areaId,true);
    }
  }

  // ── building / floor 类型钩子 ──
  if(currentView!=='topology'){
    // 退出 building 类型 → 移除 buildings[] 条目，清节点 building_id
    if(oldType==='building'&&newType!=='building'){
      const oldBldId='bld_area_'+area.id;
      if(typeof buildings!=='undefined'){
        buildings=buildings.filter(b=>b.id!==oldBldId);
        buildings.forEach((b,i)=>b.sort_order=i+1);
      }
      nodes.forEach(n=>{if(n.building_id===oldBldId)n.building_id=null});
      area.building_id=null;
    }
    // 退出 floor 类型 → 清节点 floor_id 关联
    if(oldType==='floor'&&newType!=='floor'){
      const oldFloorId=area.id;
      nodes.forEach(n=>{if(n.floor_id===oldFloorId)n.floor_id=null});
      area.floor_id=null;
    }
    // 进入 building 类型 → 创建 buildings[] 条目
    if(newType==='building'){
      const bId='bld_area_'+area.id;
      if(typeof buildings!=='undefined'&&!buildings.find(b=>b.id===bId)){
        const colorPool=(typeof BUILDING_COLORS!=='undefined')?BUILDING_COLORS:[area.color||'#3b82f6'];
        buildings.push({
          id:bId,
          name:area.label||_t('新建筑'),
          color:area.color||colorPool[buildings.length%colorPool.length],
          sort_order:buildings.length+1,
          _from_area:area.id
        });
      }
      area.building_id=bId;
      area.floor_id=null;
    }
    // 进入 floor 类型 → 设 floor_id = area.id；如果嵌套在 building 区域内，继承 building_id
    if(newType==='floor'){
      area.floor_id=area.id;
      // 给新虚拟楼层分配 tab_sort_order（追加到末尾）
      if(!area.tab_sort_order){
        let _maxSO=0;
        floorPlans.forEach(_fp=>(_fp.areas||[]).forEach(_a=>{if(_a.area_type==='floor'&&_a.tab_sort_order>_maxSO)_maxSO=_a.tab_sort_order}));
        area.tab_sort_order=_maxSO+1;
      }
      const cx=area.x+area.width/2, cy=area.y+area.height/2;
      const fp=getFloorPlan(currentView);
      let parentBldArea=null;
      if(fp){
        const candidates=(fp.areas||[]).filter(a=>a.id!==area.id&&a.area_type==='building'&&
          cx>=a.x&&cx<=a.x+a.width&&cy>=a.y&&cy<=a.y+a.height);
        candidates.sort((a,b)=>a.width*a.height-b.width*b.height);
        parentBldArea=candidates[0]||null;
      }
      area.building_id=parentBldArea?parentBldArea.building_id:null;
    }
    // 重算该 fp 全部节点归属（不只 area 内：area 类型变化可能影响嵌套关系或边界节点）
    if(typeof recomputeAllPlacementOwnership==='function'){
      const _fp2=getFloorPlan(currentView);
      if(_fp2)recomputeAllPlacementOwnership(_fp2);
    }
    if(typeof rebuildViewTabs==='function')rebuildViewTabs();
  }

  hasUnsavedChanges=true;if(currentView!=='topology')syncFloorAreaLabels();renderAll();showAreaProps(areaId);
}

function updateAreaProp(areaId,prop,val){
  const areas=getAreaStorage();if(!areas)return;
  const area=areas.find(a=>a.id===areaId);if(!area)return;
  pushHistoryProp();area[prop]=val;hasUnsavedChanges=true;
  // building 类型 area 改名 → 同步 buildings[] 条目的 name
  if(prop==='label'&&area.area_type==='building'){
    const bId='bld_area_'+area.id;
    const b=(typeof buildings!=='undefined')?buildings.find(b=>b.id===bId):null;
    if(b){b.name=val||_t('新建筑');if(typeof rebuildViewTabs==='function')rebuildViewTabs()}
  }
  // building 类型 area 改颜色 → 同步 building.color
  if(prop==='color'&&area.area_type==='building'){
    const bId='bld_area_'+area.id;
    const b=(typeof buildings!=='undefined')?buildings.find(b=>b.id===bId):null;
    if(b){b.color=val;if(typeof rebuildViewTabs==='function')rebuildViewTabs()}
  }
  // floor 类型 area 改名 → 区域内节点的 floor_label 同步；rebuildViewTabs 让虚拟楼层 tab 名同步
  if(prop==='label'&&area.area_type==='floor'){
    if(currentView!=='topology'){
      const fp=getFloorPlan(currentView);
      if(fp&&fp.placements){
        fp.placements.forEach(p=>{
          const n=nodes.find(n=>n.id===p.node_id);
          if(n&&n.floor_id===area.id)n.floor_label=val||'';
        });
      }
    }
    if(typeof rebuildViewTabs==='function')rebuildViewTabs();
  }
  if(currentView!=='topology')syncFloorAreaLabels();
  renderAll();
}

function updateRiserIndex(areaId,idx){
  const areas=getAreaStorage();if(!areas)return;
  const area=areas.find(a=>a.id===areaId);if(!area)return;
  pushHistoryProp();
  area.riser_index=idx;
  if(idx) area.label=(area.label||'').replace(/-\d+$/,'') + '-' + idx;
  // Sync riser node name
  if(area._riser_node_id){
    const n=nodes.find(n=>n.id===area._riser_node_id);
    if(n) n.name=area.label;
  }
  hasUnsavedChanges=true;
  if(currentView!=='topology')syncFloorAreaLabels();renderAll();
}

function deleteArea(areaId){
  if(DIAGRAM_CONFIG.readOnly)return;
  const areas=getAreaStorage();if(!areas)return;
  const area=areas.find(a=>a.id===areaId);
  if(area&&area.is_riser&&currentView!=='topology'){const fp=getFloorPlan(currentView);if(fp)removeRiserNode(fp,area)}
  pushHistory();
  // building 类型 area 删除 → 同步删除 buildings[] 条目
  if(area&&area.area_type==='building'){
    const bId='bld_area_'+area.id;
    if(typeof buildings!=='undefined'){
      buildings=buildings.filter(b=>b.id!==bId);
      buildings.forEach((b,i)=>b.sort_order=i+1);
    }
  }
  // 如果删除的是当前聚焦的虚拟楼层，先清除聚焦
  if(area&&area.area_type==='floor'&&typeof _focusedFloorAreaId!=='undefined'&&_focusedFloorAreaId===area.id){
    _focusedFloorAreaId=null;
  }
  // 先把 area 从数组里移除，再重算归属 → computeOwnershipAt 不会再命中已删 area，自动回落到底图层（fp.id / fp.building_id）
  const idx=areas.indexOf(area);if(idx>=0)areas.splice(idx,1);
  if(currentView!=='topology'&&typeof recomputeAllPlacementOwnership==='function'){
    const _fp=getFloorPlan(currentView);
    if(_fp)recomputeAllPlacementOwnership(_fp);
  }
  selectedAreaId=null;if(currentView!=='topology')syncFloorAreaLabels();hasUnsavedChanges=true;
  if(typeof rebuildViewTabs==='function')rebuildViewTabs();
  renderAll();hideProps();
  showToast(_t('已删除区域'));
}

// ====== RISER (弱电井) ======
function toggleRiser(areaId, checked){
  const fp=getFloorPlan(currentView);
  const area=fp?fp.areas.find(a=>a.id===areaId):null;
  if(!area)return;
  pushHistoryProp();
  area.is_riser=checked;
  // Auto-assign riser_index
  if(checked&&!area.riser_index){
    const maxIdx=Math.max(0,...(fp.areas||[]).filter(a=>a.is_riser&&a.riser_index).map(a=>a.riser_index));
    area.riser_index=maxIdx+1;
    area.label=(area.label||_t('弱电井')).replace(/-\d+$/,'') + '-' + area.riser_index;
  }
  if(!checked){area.riser_index=null}
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
    px_per_meter:targetPxPerMeter,
    raw_px_per_meter:pxPerMeter
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

// ====== CALIBRATION INHERITANCE ======
function _findRecentCalibration(excludeFpId){
  for(let i=floorPlans.length-1;i>=0;i--){
    const fp=floorPlans[i];
    if(fp.id===excludeFpId)continue;
    if(fp.calibration&&fp.calibration.raw_px_per_meter&&fp.calibration.px_per_meter){
      return {fpId:fp.id, label:fp.label, calibration:fp.calibration};
    }
  }
  return null;
}

function _applyInheritedCalibration(fp,prevCalib){
  const rawPxPerMeter=prevCalib.raw_px_per_meter;
  const targetPxPerMeter=prevCalib.px_per_meter;
  const scaleFactor=targetPxPerMeter/rawPxPerMeter;

  pushHistory();

  if(fp.background){
    fp.background.width=Math.round(fp.background.width*scaleFactor);
    fp.background.height=Math.round(fp.background.height*scaleFactor);
    if(fp.background.offset_x)fp.background.offset_x=Math.round(fp.background.offset_x*scaleFactor);
    if(fp.background.offset_y)fp.background.offset_y=Math.round(fp.background.offset_y*scaleFactor);
  }

  fp.calibration={
    ref_line:null,
    inherited:true,
    real_length:prevCalib.real_length,
    unit:prevCalib.unit,
    px_per_meter:targetPxPerMeter,
    raw_px_per_meter:rawPxPerMeter
  };

  hasUnsavedChanges=true;
  renderAll();
  fitView();
}

async function _offerCalibrationInheritance(fpId){
  const prev=_findRecentCalibration(fpId);
  if(!prev)return;
  const sf=(prev.calibration.px_per_meter/prev.calibration.raw_px_per_meter).toFixed(2);
  const ok=await sdConfirm(
    _t('套用尺寸比例'),
    _t('检测到楼层')+' "'+prev.label+'" '+_t('已标定比例')+' ('+sf+'×)。\n'+_t('是否套用相同比例到当前楼层？'),
    {okText:_t('套用'),cancelText:_t('手动标定')}
  );
  if(!ok)return;
  const fp=getFloorPlan(fpId);
  if(fp)_applyInheritedCalibration(fp,prev.calibration);
}

async function _offerCalibrationInheritanceMulti(fpIds){
  if(!fpIds||!fpIds.length)return;
  const prev=_findRecentCalibration(fpIds[0]);
  if(!prev)return;
  const sf=(prev.calibration.px_per_meter/prev.calibration.raw_px_per_meter).toFixed(2);
  const ok=await sdConfirm(
    _t('批量套用尺寸比例'),
    _t('检测到楼层')+' "'+prev.label+'" '+_t('已标定比例')+' ('+sf+'×)。\n'+_t('是否套用相同比例到所有')+' '+fpIds.length+' '+_t('个新楼层？'),
    {okText:_t('全部套用'),cancelText:_t('手动标定')}
  );
  if(!ok)return;
  for(const id of fpIds){
    const fp=getFloorPlan(id);
    if(fp)_applyInheritedCalibration(fp,prev.calibration);
  }
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
let _coverageHoverG = null; // persistent hover overlay in tempLayer

function renderCoverageCircles(fp) {
  _hideCoverageHover(); // clear any residual hover from previous render
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

  // Transparent hit-area group (on top, receives pointer events)
  const hitG = document.createElementNS(svgNS, 'g');
  hitG.setAttribute('class', 'coverage-hit-layer');
  const comp = getFloorZoomCompensation();

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

      // Transparent hit circle for hover detection
      const hitCircle = document.createElementNS(svgNS, 'circle');
      hitCircle.setAttribute('cx', cx);
      hitCircle.setAttribute('cy', cy);
      hitCircle.setAttribute('r', r);
      hitCircle.setAttribute('fill', 'none');
      hitCircle.setAttribute('stroke', 'transparent');
      hitCircle.setAttribute('stroke-width', 14 * comp);
      hitCircle.setAttribute('pointer-events', 'stroke');
      hitCircle.style.cursor = 'crosshair';
      const ringIdx = i, radiusM = radii[i], rPx = r, hcx = cx, hcy = cy;
      hitCircle.addEventListener('mouseenter', e => _showCoverageHover(ringIdx, radiusM, hcx, hcy, rPx, e));
      hitCircle.addEventListener('mousemove', e => _updateCoverageHoverAngle(hcx, hcy, rPx, e));
      hitCircle.addEventListener('mouseleave', () => _hideCoverageHover());
      hitG.appendChild(hitCircle);
    }
  });

  // Prepend defs + coverage group into edgesLayer (behind routes)
  if (coverageG.childNodes.length > 0) {
    edgesLayer.insertBefore(coverageG, edgesLayer.firstChild);
    edgesLayer.insertBefore(defs, edgesLayer.firstChild);
  }
  // Append hit layer on top so it captures pointer events
  if (hitG.childNodes.length > 0) {
    edgesLayer.appendChild(hitG);
  }
}

// ====== COVERAGE CIRCLES LITE (drag mode — stroke only, no fill/text/events) ======
function renderCoverageCirclesLite(fp) {
  if (!fp.calibration || !fp.calibration.px_per_meter) return;
  const ppm = fp.calibration.px_per_meter;
  const edgesLayer = document.getElementById('edgesLayer');
  const svgNS = 'http://www.w3.org/2000/svg';
  const coverageG = document.createElementNS(svgNS, 'g');
  coverageG.setAttribute('class', 'coverage-layer-lite');
  coverageG.style.pointerEvents = 'none';

  const globalRingKeys = ['showCoverageInner', 'showCoverageMid'];
  const comp = getFloorZoomCompensation();

  fp.placements.forEach(pl => {
    const n = nodes.find(nd => nd.id === pl.node_id);
    if (!n) return;
    if (getNodeIconKey(n) !== 'antenna_indoor') return;
    if (displaySettings.showCoverage === 'individual' && n.showCoverage !== true) return;

    const cx = pl.x + (n.w || NODE_SIZE) / 2;
    const cy = pl.y + (n.h || NODE_SIZE) / 2;
    const radii = n.coverageRadii || coverageRadiiFromN(n.coverageN);
    const vis = n.coverageVisible || [true, true];

    for (let i = radii.length - 1; i >= 0; i--) {
      const r = radii[i] * ppm;
      if (r <= 0) continue;
      if (!displaySettings[globalRingKeys[i]]) continue;
      if (!vis[i]) continue;
      const ring = COVERAGE_RINGS[i] || COVERAGE_RINGS[COVERAGE_RINGS.length - 1];

      const circle = document.createElementNS(svgNS, 'circle');
      circle.setAttribute('cx', cx);
      circle.setAttribute('cy', cy);
      circle.setAttribute('r', r);
      circle.setAttribute('fill', 'none');
      circle.setAttribute('stroke', ring.color);
      circle.setAttribute('stroke-opacity', '1');
      circle.setAttribute('stroke-width', 2.5 * comp);
      coverageG.appendChild(circle);
    }
  });

  if (coverageG.childNodes.length > 0) {
    edgesLayer.insertBefore(coverageG, edgesLayer.firstChild);
  }
}

// ====== COVERAGE HOVER (highlight ring + leader line) ======
function _showCoverageHover(ringIdx, radiusM, cx, cy, rPx, e) {
  _hideCoverageHover();
  const svgNS = 'http://www.w3.org/2000/svg';
  const ring = COVERAGE_RINGS[ringIdx] || COVERAGE_RINGS[COVERAGE_RINGS.length - 1];
  const comp = getFloorZoomCompensation();
  const fontSize = 12 * comp;
  const g = document.createElementNS(svgNS, 'g');
  g.setAttribute('class', 'coverage-hover-overlay');

  // Highlighted ring (bolder, full opacity)
  const hlCircle = document.createElementNS(svgNS, 'circle');
  hlCircle.setAttribute('cx', cx);
  hlCircle.setAttribute('cy', cy);
  hlCircle.setAttribute('r', rPx);
  hlCircle.setAttribute('fill', 'none');
  hlCircle.setAttribute('stroke', ring.color);
  hlCircle.setAttribute('stroke-opacity', '1');
  hlCircle.setAttribute('stroke-width', 2.5 * comp);
  g.appendChild(hlCircle);

  // Leader line (dashed, gray) from center to edge point
  const leader = document.createElementNS(svgNS, 'line');
  leader.setAttribute('x1', cx);
  leader.setAttribute('y1', cy);
  leader.setAttribute('stroke', '#64748b');
  leader.setAttribute('stroke-width', 1.2 * comp);
  leader.setAttribute('stroke-dasharray', `${4 * comp},${3 * comp}`);
  leader.setAttribute('stroke-opacity', '0.85');
  leader.setAttribute('class', 'cov-hover-line');
  g.appendChild(leader);

  // Distance label (white background pill)
  const labelText = `${radiusM}m`;
  const textW = labelText.length * fontSize * 0.6;
  const padX = 6 * comp, padY = 3 * comp;
  const rect = document.createElementNS(svgNS, 'rect');
  rect.setAttribute('rx', 4 * comp);
  rect.setAttribute('ry', 4 * comp);
  rect.setAttribute('width', textW + padX * 2);
  rect.setAttribute('height', fontSize + padY * 2);
  rect.setAttribute('fill', 'rgba(255,255,255,0.95)');
  rect.setAttribute('stroke', '#e2e8f0');
  rect.setAttribute('stroke-width', 0.8 * comp);
  rect.setAttribute('class', 'cov-hover-bg');
  g.appendChild(rect);
  const text = document.createElementNS(svgNS, 'text');
  text.setAttribute('fill', '#1e293b');
  text.setAttribute('font-size', fontSize);
  text.setAttribute('font-family', 'system-ui, sans-serif');
  text.setAttribute('font-weight', '600');
  text.setAttribute('text-anchor', 'middle');
  text.setAttribute('dominant-baseline', 'central');
  text.setAttribute('class', 'cov-hover-text');
  text.textContent = labelText;
  g.appendChild(text);

  // Store center/radius on the group element
  g._cx = cx;
  g._cy = cy;
  g._rPx = rPx;

  g.style.pointerEvents = 'none';
  document.getElementById('tempLayer').appendChild(g);
  _coverageHoverG = g;

  // Position leader + label using initial mouse position
  _updateCoverageHoverAngle(cx, cy, rPx, e);
}

function _updateCoverageHoverAngle(cx, cy, rPx, e) {
  if (!_coverageHoverG) return;
  const mp = svgPoint(e);

  const angle = Math.atan2(mp.y - cy, mp.x - cx);
  const edgeX = cx + rPx * Math.cos(angle);
  const edgeY = cy + rPx * Math.sin(angle);

  const leader = _coverageHoverG.querySelector('.cov-hover-line');
  if (leader) {
    leader.setAttribute('x2', edgeX);
    leader.setAttribute('y2', edgeY);
  }

  const midX = (cx + edgeX) / 2;
  const midY = (cy + edgeY) / 2;
  const rect = _coverageHoverG.querySelector('.cov-hover-bg');
  const text = _coverageHoverG.querySelector('.cov-hover-text');
  if (rect) {
    const rw = parseFloat(rect.getAttribute('width'));
    const rh = parseFloat(rect.getAttribute('height'));
    rect.setAttribute('x', midX - rw / 2);
    rect.setAttribute('y', midY - rh / 2);
  }
  if (text) {
    text.setAttribute('x', midX);
    text.setAttribute('y', midY);
  }
}

function _hideCoverageHover() {
  if (_coverageHoverG) {
    _coverageHoverG.remove();
    _coverageHoverG = null;
  }
}

// ====== COVERAGE HEATMAP ======
// 对讲机信号物理模型：Rx(dBm) = Tx - FSPL(1m) - 10·n·log₁₀(d)
const _HM_TX = 10, _HM_FSPL1M = 24.5, _HM_RX1M = _HM_TX - _HM_FSPL1M; // -14.5 dBm
const _HM_DESIGN = -85, _HM_FLOOR = -95;
const _HM_RANGE = _HM_RX1M - _HM_FLOOR; // 95.5 dB
const HEATMAP_SAMPLE_SIZE = 4;
const HEATMAP_COLORS = [
  { stop: 0.00, r: 59,  g: 130, b: 246 },  // 蓝 (噪声底 -95dBm)
  { stop: 0.04, r: 6,   g: 182, b: 212 },  // 青
  { stop: 0.08, r: 16,  g: 185, b: 145 },  // 青绿
  { stop: 0.12, r: 34,  g: 197, b: 94  },  // 绿 (中圈 -85dBm, s≈0.124)
  { stop: 0.20, r: 100, g: 200, b: 55  },  // 黄绿
  { stop: 0.28, r: 180, g: 200, b: 30  },  // 黄绿偏黄
  { stop: 0.37, r: 240, g: 190, b: 20  },  // 黄 (内圈 -65dBm, s≈0.373)
  { stop: 0.55, r: 245, g: 120, b: 11  },  // 橙
  { stop: 0.78, r: 234, g: 70,  b: 12  },  // 橙红
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
  const rMid = radii[1]; // mid-ring radius in metres, corresponds to -85 dBm
  if (rMid > 0.5) {
    // -85 = -14.5 - 10*n*log10(rMid)  →  n = 70.5 / (10*log10(rMid))
    return 70.5 / (10 * Math.log10(rMid));
  }
  return nd.coverageN || 5.1;
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
      let totalPowerLinear = 0;
      for (const ant of antennasData) {
        const dx = (px - ant.cx) / ppm;
        const dy = (py - ant.cy) / ppm;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const dBm = _hmSignalDbm(dist, ant.n);
        if (dBm > _HM_FLOOR) {
          totalPowerLinear += Math.pow(10, dBm / 10);
        }
      }
      if (totalPowerLinear > 0) {
        const totalDbm = 10 * Math.log10(totalPowerLinear);
        maxS = Math.min(1.0, Math.max(0, (totalDbm - _HM_FLOOR) / _HM_RANGE));
      }
      if (maxS > 0.03) {
        // Fade out near canvas edges to avoid hard boundary
        const edgeM = 50; // canvas pixels (~200 SVG px)
        const distE = Math.min(sx, sy, sw - 1 - sx, sh - 1 - sy);
        const fade = distE < edgeM ? distE / edgeM : 1.0;
        const c = _hmColor(maxS);
        const idx = (sy * sw + sx) * 4;
        data[idx] = c.r; data[idx + 1] = c.g; data[idx + 2] = c.b;
        // Piecewise alpha: mid-circle(s≈0.124) keeps visible, fades outside
        const s_mid = 0.124; // -85 dBm
        let alpha;
        if (maxS >= s_mid) {
          // Center → mid circle: opacity 60→255
          alpha = 60 + 195 * Math.pow((maxS - s_mid) / (1 - s_mid), 0.8);
        } else {
          // Outside mid circle: fade 60→0
          alpha = 60 * ((maxS - 0.03) / (s_mid - 0.03));
        }
        data[idx + 3] = Math.min(255, Math.round(alpha * fade));
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
    const showLabel=route.label&&displaySettings.cableLabel&&!route.hideLabel;
    const ppm=fp.calibration&&fp.calibration.px_per_meter;
    let lengthStr='';
    let pxLen=0;
    if(ppm){
      const tmpSvg=document.createElementNS('http://www.w3.org/2000/svg','path');
      tmpSvg.setAttribute('d',result.path);
      pxLen=tmpSvg.getTotalLength();
      if(displaySettings.cableLength){
        const meters=pxLen/ppm;
        lengthStr=meters>=1?meters.toFixed(1)+'m':Math.round(meters*100)+'cm';
      }
    }
    const parts=[];if(showLabel)parts.push(route.label);if(lengthStr)parts.push(lengthStr);
    if(parts.length){
      const txt=parts.join(' · ');
      const baseTl=txt.length*7+16;
      // Auto-hide label if text wider than line length
      if(pxLen>0&&baseTl>pxLen*0.9){}else{
      const mid=getPathMidpoint(result,edgeLike);
      // Compute angle of line segment at midpoint for label rotation
      let angle=0;
      if(result.pts&&result.pts.length>=2){
        let totalLen=0;const segs=[];
        for(let i=1;i<result.pts.length;i++){
          const dx=result.pts[i].x-result.pts[i-1].x,dy=result.pts[i].y-result.pts[i-1].y;
          segs.push({from:result.pts[i-1],to:result.pts[i],len:Math.sqrt(dx*dx+dy*dy)});totalLen+=segs[segs.length-1].len;
        }
        let rem=totalLen/2;
        for(const seg of segs){
          if(rem<=seg.len){angle=Math.atan2(seg.to.y-seg.from.y,seg.to.x-seg.from.x)*180/Math.PI;break;}
          rem-=seg.len;
        }
      }else if(result.sp&&result.tp){
        angle=Math.atan2(result.tp.y-result.sp.y,result.tp.x-result.sp.x)*180/Math.PI;
      }
      // Keep text readable: flip if upside-down
      if(angle>90)angle-=180; else if(angle<-90)angle+=180;
      const transform=Math.abs(angle)>1?`rotate(${angle.toFixed(1)},${mid.x.toFixed(1)},${mid.y.toFixed(1)})`:'';

      if(comp!==1){
        const tl=baseTl*comp,lh=18*comp;
        const bg=document.createElementNS('http://www.w3.org/2000/svg','rect');
        bg.setAttribute('class','edge-label-bg');bg.setAttribute('x',mid.x-tl/2);bg.setAttribute('y',mid.y-lh/2);
        bg.setAttribute('width',tl);bg.setAttribute('height',lh);bg.setAttribute('rx',4*comp);
        if(transform)bg.setAttribute('transform',transform);
        bg.style.cursor='pointer';
        bg.addEventListener('click',ev=>{ev.stopPropagation();selectFloorRoute(route.id)});
        labelEls.push(bg);
        const lbl=document.createElementNS('http://www.w3.org/2000/svg','text');
        lbl.setAttribute('class','edge-label');lbl.setAttribute('x',mid.x);lbl.setAttribute('y',mid.y);
        lbl.setAttribute('font-size',12*comp);
        if(transform)lbl.setAttribute('transform',transform);
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
        if(transform)bg.setAttribute('transform',transform);
        bg.style.cursor='pointer';
        bg.addEventListener('click',ev=>{ev.stopPropagation();selectFloorRoute(route.id)});
        labelEls.push(bg);
        const lbl=document.createElementNS('http://www.w3.org/2000/svg','text');
        lbl.setAttribute('class','edge-label');lbl.setAttribute('x',mid.x);lbl.setAttribute('y',mid.y);
        if(transform)lbl.setAttribute('transform',transform);
        lbl.setAttribute('fill',rc);lbl.textContent=txt;
        lbl.style.cursor='pointer';
        lbl.style.pointerEvents='auto';
        lbl.addEventListener('click',ev=>{ev.stopPropagation();selectFloorRoute(route.id)});
        labelEls.push(lbl);
      }
      }// end auto-hide check
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
  // Collect connected ports so we can show them as solid dots
  const connectedPorts=new Set();
  if(fp.routes&&fp.routes.length){
    fp.routes.forEach(route=>{
      const srcPl=fp.placements.find(p=>p.node_id===route.sourceNodeId);
      const tgtPl=fp.placements.find(p=>p.node_id===route.targetNodeId);
      const srcN=nodes.find(n=>n.id===route.sourceNodeId);
      if(!srcPl||!tgtPl)return;
      const rMode=route.routeMode||'ortho3';
      const autoP=(!route._userPorts)?findBestPort(srcPl,tgtPl,(srcN?srcN.w:null)||NODE_SIZE,rMode):null;
      const sp=autoP?autoP.srcPort:(route.sourcePort||'right');
      const tp=autoP?autoP.tgtPort:(route.targetPort||'left');
      connectedPorts.add(route.sourceNodeId+':'+sp);
      connectedPorts.add(route.targetNodeId+':'+tp);
    });
  }
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
      const isConn=connectedPorts.has(n.id+':'+p.name);
      port.setAttribute('class','port'+(isConn?' connected':''));
      port.setAttribute('cx',p.cx);port.setAttribute('cy',p.cy);port.setAttribute('r',isConn?4:5);
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
  input.type='file';input.accept='image/png,image/jpeg,image/jpg,application/pdf,.dxf,.dwg';
  input.onchange=async function(){
    const file=input.files[0];if(!file)return;
    if(file.size>12*1024*1024){showToast(_t('文件大小不能超过 12MB'));return}

    const fname=file.name.toLowerCase();
    if(fname.endsWith('.pdf')){
      await _handlePdfUpload(file,fpId);
      return;
    }
    if(fname.endsWith('.dxf')||fname.endsWith('.dwg')){
      await _handleDxfUpload(file,fpId);
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
            if(!fp.calibration)_offerCalibrationInheritance(fpId);
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
  if(fp.background.bg_type==='dxf'&&fp.background.dxf_filename){
    body.dxf_filename=fp.background.dxf_filename;
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

// ====== DXF/DWG IMPORT ======

async function _handleDxfUpload(file, fpId) {
  if (!DIAGRAM_CONFIG.diagramId) {
    await saveDiagram();
    if (!DIAGRAM_CONFIG.diagramId) { showToast(_t('保存失败，无法上传')); return; }
  }

  const isDwg = file.name.toLowerCase().endsWith('.dwg');
  showToast(isDwg ? _t('转换 DWG 中...') : _t('读取图层中...'));

  const formData = new FormData();
  formData.append('file', file, file.name);
  formData.append('floor_id', fpId);

  try {
    const resp = await fetch(
      DIAGRAM_CONFIG.apiFloorBgBase + DIAGRAM_CONFIG.diagramId + '/floor-plan/extract-dxf-layers',
      { method: 'POST', headers: { 'X-CSRFToken': DIAGRAM_CONFIG.csrfToken }, body: formData }
    );
    const result = await resp.json();
    if (!result.success) { showToast(result.message || _t('DXF 读取失败')); return; }

    _showDxfLayerSelector(result.layers, result.temp_dxf, fpId);
  } catch (err) {
    showToast(_t('DXF 读取失败') + ': ' + err.message);
  }
}

function _showDxfLayerSelector(layers, tempDxf, fpId) {
  const base = layers.filter(l => l.category === 'base');
  const equip = layers.filter(l => l.category === 'equipment');

  function layerRow(l) {
    const checked = l.selected ? 'checked' : '';
    const cnt = l.entity_count > 0 ? ` <span style="color:#9ca3af;font-size:11px">(${l.entity_count})</span>` : '';
    return `<label style="display:flex;align-items:center;gap:6px;padding:3px 0;cursor:pointer">
      <input type="checkbox" class="dxf-layer-cb" data-cat="${l.category}" value="${_escHtml(l.name)}" ${checked} style="flex-shrink:0">
      <span style="font-size:13px">${_escHtml(l.name)}${cnt}</span>
    </label>`;
  }

  const baseHtml = base.length ? `
    <div style="margin-bottom:10px">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px">
        <span style="font-size:12px;font-weight:600;color:#374151">🏗 ${_t('基础建筑图层')}（${_t('建议保留')}）</span>
        <span>
          <button onclick="_dxfLayerSelectAll(true,true)" style="font-size:11px;color:#3b82f6;background:none;border:none;cursor:pointer">${_t('全选')}</button>
          <button onclick="_dxfLayerSelectAll(true,false)" style="font-size:11px;color:#6b7280;background:none;border:none;cursor:pointer">${_t('全不选')}</button>
        </span>
      </div>
      ${base.map(layerRow).join('')}
    </div>` : '';

  const equipHtml = equip.length ? `
    <div>
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px">
        <span style="font-size:12px;font-weight:600;color:#374151">🔧 ${_t('设备/叠加图层')}（${_t('可选')}）</span>
        <span>
          <button onclick="_dxfLayerSelectAll(false,true)" style="font-size:11px;color:#3b82f6;background:none;border:none;cursor:pointer">${_t('全选')}</button>
          <button onclick="_dxfLayerSelectAll(false,false)" style="font-size:11px;color:#6b7280;background:none;border:none;cursor:pointer">${_t('全不选')}</button>
        </span>
      </div>
      ${equip.map(layerRow).join('')}
    </div>` : '';

  const modal = document.createElement('div');
  modal.id = 'dxfLayerModal';
  modal.style.cssText = 'position:fixed;inset:0;z-index:9999;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.5)';
  modal.innerHTML = `
    <div style="background:#fff;border-radius:10px;width:360px;max-height:80vh;display:flex;flex-direction:column;box-shadow:0 20px 60px rgba(0,0,0,0.3)">
      <div style="padding:16px 20px;border-bottom:1px solid #e5e7eb;font-size:15px;font-weight:600">${_t('选择要导入的图层')}</div>
      <div style="padding:16px 20px;overflow-y:auto;flex:1">${baseHtml}${equipHtml}</div>
      <div style="padding:12px 20px;border-top:1px solid #e5e7eb;display:flex;gap:8px;justify-content:flex-end">
        <button onclick="document.getElementById('dxfLayerModal').remove()" style="padding:7px 16px;border:1px solid #d1d5db;border-radius:6px;background:#fff;cursor:pointer;font-size:13px">${_t('取消')}</button>
        <button id="dxfLayerImportBtn" style="padding:7px 16px;border:none;border-radius:6px;background:#3b82f6;color:#fff;cursor:pointer;font-size:13px;font-weight:500">${_t('确认导入')}</button>
      </div>
    </div>`;

  document.body.appendChild(modal);

  document.getElementById('dxfLayerImportBtn').onclick = async () => {
    const selected = [...modal.querySelectorAll('.dxf-layer-cb:checked')].map(cb => cb.value);
    if (!selected.length) { showToast(_t('请至少选择一个图层')); return; }
    modal.remove();
    await _renderDxfWithLayers(tempDxf, selected, fpId);
  };
}

window._dxfLayerSelectAll = function(isBase, checked) {
  const modal = document.getElementById('dxfLayerModal');
  if (!modal) return;
  const cat = isBase ? 'base' : 'equipment';
  modal.querySelectorAll(`.dxf-layer-cb[data-cat="${cat}"]`).forEach(cb => { cb.checked = checked; });
};

async function _renderDxfWithLayers(tempDxf, selectedLayers, fpId) {
  showToast(_t('渲染中...'));
  const formData = new FormData();
  formData.append('floor_id', fpId);
  formData.append('temp_dxf', tempDxf);
  formData.append('include_layers', JSON.stringify(selectedLayers));

  try {
    const resp = await fetch(
      DIAGRAM_CONFIG.apiFloorBgBase + DIAGRAM_CONFIG.diagramId + '/floor-plan/analyze-dxf',
      { method: 'POST', headers: { 'X-CSRFToken': DIAGRAM_CONFIG.csrfToken }, body: formData }
    );
    const result = await resp.json();
    if (!result.success) { showToast(result.message || _t('DXF 导入失败')); return; }

    const fp = getFloorPlan(fpId);
    if (!fp) return;
    _cleanupOldBgFiles(fp);

    fp.background = {
      is_multi_res: true,
      url: result.url,
      width: result.width,
      height: result.height,
      resolutions: result.resolutions,
      filenames: result.filenames,
      offset_x: 0, offset_y: 0, opacity: 0.3,
      bg_type: 'dxf',
      dxf_filename: result.dxf_filename,
    };

    hasUnsavedChanges = true;
    renderAll();
    showFloorPlanProps(fpId);
    showToast(_t('DXF 底图已导入'));
    updateFloorBgButton(fpId);
    updateDwgExportMenuItem();
    if (!fp.calibration) _offerCalibrationInheritance(fpId);
  } catch (err) {
    showToast(_t('DXF 导入失败') + ': ' + err.message);
  }
}

function _escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
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
      if(!fp.calibration)_offerCalibrationInheritance(fpId);
    } else {
      // Multiple pages: create new floor plans for each
      let firstNewId=null;
      const newFpIds=[];
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
        newFpIds.push(newId);
        if(!firstNewId)firstNewId=newId;
      }
      if(firstNewId)switchView(firstNewId);
      showToast(_t('已导入')+' '+result.results.length+' '+_t('个楼层'));
      _offerCalibrationInheritanceMulti(newFpIds);
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
  // Building selector
  let buildingHTML='';
  if(!isRO){
    const curBld=fp.building_id||'';
    const blds=(typeof buildings!=='undefined')?buildings.slice().sort((a,b)=>a.sort_order-b.sort_order):[];
    buildingHTML=`<div class="props-field"><span class="props-label">${_t('所属建筑')}</span><select class="props-input" id="floorBuildingSelect" onchange="if(this.value==='__new__'){this.value='${curBld}';const n=prompt('${_t('建筑名称')}');if(n&&n.trim()&&typeof addBuilding==='function'){const b=addBuilding(n.trim());if(b){assignFloorToBuilding('${fpId}',b.id);showFloorPlanProps('${fpId}')}}}else{assignFloorToBuilding('${fpId}',this.value||null);showFloorPlanProps('${fpId}')}"><option value="">${_t('无（独立楼层）')}</option>`;
    blds.forEach(b=>{
      buildingHTML+=`<option value="${b.id}"${b.id===curBld?' selected':''}>${b.name}</option>`;
    });
    buildingHTML+=`<option value="__new__">+ ${_t('创建新建筑...')}</option>`;
    buildingHTML+=`</select></div>`;
  }
  let html=`
    <div class="props-field"><span class="props-label">${_t('楼层名称（导出文件名）')}</span>${nameHTML}</div>${buildingHTML}
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

// 平面图 → 系统图 单向同步：把所有 placements 对应的 node 标 in_topology=true
// 同时同步 building_id / floor_id；首次进系统图的节点会调用自动布局排序
// 已经在系统图里的节点保留用户调过的位置
function syncFromFloorplan(){
  if(DIAGRAM_CONFIG.readOnly){return}
  if(typeof currentView!=='undefined'&&currentView!=='topology'){
    showToast(_t('请切换到系统图视图后再同步'));
    return;
  }
  const allPlacedIds=new Set();
  floorPlans.forEach(fp=>{(fp.placements||[]).forEach(p=>allPlacedIds.add(p.node_id))});

  pushHistory();
  const newlyImported=[];
  let updatedCount=0;
  nodes.forEach(n=>{
    if(allPlacedIds.has(n.id)){
      // 找到该节点所在的楼层 fp + 它在该 fp 上的 placement 坐标
      let owningFp=null, owningP=null;
      for(const fp of floorPlans){
        const p=(fp.placements||[]).find(p=>p.node_id===n.id);
        if(p){owningFp=fp;owningP=p;break}
      }
      const wasInTopo=n.in_topology===true;
      n.in_topology=true;
      // 同步归属：用一站式 helper（虚拟楼层 label 解析已正确处理）
      if(owningFp&&owningP){
        if(typeof _applyOwnershipToNode==='function')_applyOwnershipToNode(n, owningFp, owningP.x, owningP.y);
      }
      if(!wasInTopo){newlyImported.push(n.id)}
      updatedCount++;
    }
  });

  // 在系统图里但平面图找不到对应 placement 的节点 = 平面图删了
  const orphans=nodes.filter(n=>n.in_topology===true&&n._floorCreated&&!allPlacedIds.has(n.id));
  let removedCount=0;
  if(orphans.length){
    const ok=confirm(_t('以下 ')+orphans.length+_t(' 个节点在平面图已被删除，是否从系统图也移除？'));
    if(ok){
      const orphanIds=new Set(orphans.map(n=>n.id));
      nodes=nodes.filter(n=>!orphanIds.has(n.id));
      edges=edges.filter(e=>!orphanIds.has(e.sourceId)&&!orphanIds.has(e.targetId));
      removedCount=orphans.length;
    }
  }

  // 若有新导入节点，调用自动布局重排
  if(newlyImported.length&&typeof relayoutFloorNodesTopo==='function'){
    relayoutFloorNodesTopo();
  }

  hasUnsavedChanges=true;
  renderAll();
  const parts=[];
  if(newlyImported.length)parts.push(_t('新导入')+' '+newlyImported.length);
  if(updatedCount-newlyImported.length>0)parts.push(_t('已更新')+' '+(updatedCount-newlyImported.length));
  if(removedCount)parts.push(_t('移除')+' '+removedCount);
  if(!parts.length)parts.push(_t('无变化'));
  showToast(_t('同步完成')+'：'+parts.join('，'));
}

// Re-layout all floor-plan nodes to compact grid positions in topology view
// Only nodes with actual placements on floor plans participate;
// topology-only devices (主机, 合路平台 etc.) are excluded.
// 给未指定归属的节点加红色脉冲高亮（自动消失或下次 renderAll 时清）
function _highlightUnmarkedNodes(idSet){
  const layer=document.getElementById('nodesLayer');
  if(!layer)return;
  layer.querySelectorAll('.node-group').forEach(g=>{
    const nid=parseInt(g.dataset.nodeId);
    if(idSet.has(nid)){
      g.classList.add('node-unmarked-warn');
      // 加临时 SVG glow circle 增强可视性
      if(!g.querySelector('.unmarked-glow')){
        const n=nodes.find(nd=>nd.id===nid);
        const r=document.createElementNS('http://www.w3.org/2000/svg','circle');
        r.setAttribute('class','unmarked-glow');
        r.setAttribute('cx',(n?n.w:NODE_SIZE)/2);
        r.setAttribute('cy',(n?n.h:NODE_SIZE)/2);
        r.setAttribute('r',(n?n.w:NODE_SIZE)/2+12);
        r.setAttribute('fill','none');
        r.setAttribute('stroke','#ef4444');
        r.setAttribute('stroke-width','3');
        r.setAttribute('opacity','0.85');
        r.style.pointerEvents='none';
        r.style.animation='unmarkedPulse 1s ease-in-out infinite';
        g.insertBefore(r, g.firstChild);
      }
    }
  });
  // 5 秒后自动重渲染清除高亮
  setTimeout(()=>{if(typeof renderAll==='function')renderAll()}, 5000);
}

function relayoutFloorNodesTopo(){
  // 自动布局前校验：在系统图中、是真实设备、归属信息不全的节点
  // 不全 = 既无楼栋又非显式公共  OR  指定了楼栋但没指定楼层
  const _unmarked=nodes.filter(n=>{
    if(n.in_topology===false)return false;
    if(!n.subcategoryId)return false;        // 排除文本标注
    if(n.is_shared===true)return false;       // 显式公共：不需要楼层
    if(!n.building_id)return true;            // 没指定楼栋
    if(!n.floor_id)return true;               // 指定了楼栋但没指定楼层
    return false;
  });
  if(_unmarked.length){
    if(typeof showToast==='function')showToast(`${_t('检测到')} ${_unmarked.length} ${_t('个节点未指定楼层/楼栋归属，请先在节点属性中指定')}`);
    // 高亮：临时给这些节点加 CSS class，下次 renderAll 后清除
    _highlightUnmarkedNodes(new Set(_unmarked.map(n=>n.id)));
    return;
  }

  // Build authoritative set from actual placements (not stale floor_id)
  const placedNodeIds=new Set();
  floorPlans.forEach(fp=>{fp.placements.forEach(p=>placedNodeIds.add(p.node_id))});

  // ── 新模型：把有 building_id 但没 placement 的 topo-only 节点也纳入布局 ──
  // 推断 floor_id：优先用节点本身的 floor_id；没有则用其所属楼栋的第一个楼层
  // 这样 BFS 链式算法能把它们和该楼层的天线一起排
  nodes.forEach(n=>{
    if(placedNodeIds.has(n.id))return;
    if(n.in_topology===false)return;
    if(!n.building_id&&!n.floor_id)return; // 中央机房（共享）→ 不参与楼层分组，保留原位置
    if(!n.floor_id&&n.building_id){
      const firstFp=floorPlans.find(f=>f.building_id===n.building_id);
      if(firstFp){n.floor_id=firstFp.id;n.floor_label=firstFp.label||''}
    }
    if(n.floor_id)placedNodeIds.add(n.id);
  });

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

  // Pre-identify central_room node IDs so we can exclude them from startX/Y
  const _roomNodeIdSet=new Set();
  if(typeof topoAreas!=='undefined'&&topoAreas.length){
    topoAreas.filter(a=>(a.area_type||'normal')==='central_room').forEach(area=>{
      topoNodes.forEach(n=>{
        const cx=n.x+(n.w||NODE_SIZE)/2,cy=n.y+(n.h||NODE_SIZE)/2;
        if(cx>=area.x&&cx<=area.x+area.width&&cy>=area.y&&cy<=area.y+area.height)
          _roomNodeIdSet.add(n.id);
      });
    });
  }
  const nonRoomTopoNodes=topoNodes.filter(n=>!_roomNodeIdSet.has(n.id));

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
    // Align floor chains — exclude room nodes to prevent cascading leftward drift
    if(nonRoomTopoNodes.length){
      startX=Math.min(...nonRoomTopoNodes.map(n=>n.x));
      startY=Math.max(...nonRoomTopoNodes.map(n=>n.y+(n.h||NODE_SIZE)))+100;
    }
    console.log(`startX=${startX} startY=${startY}`);
  }
  // 锚点：若已有 floor 节点位置（不是首次布局），保留它们的 X 起点和 Y 顶部，避免每次重排都把天线推到机房下方
  const _existingFloorAnchor=(function(){
    const placed=floorNodes.filter(n=>(n.x||n.y));
    if(!placed.length)return null;
    return {x:Math.min(...placed.map(n=>n.x)), y:Math.min(...placed.map(n=>n.y))};
  })();
  if(_existingFloorAnchor){startX=_existingFloorAnchor.x}

  // Group by floor
  const groups={};
  floorNodes.forEach(n=>{const fid=n.floor_id;if(!groups[fid])groups[fid]=[];groups[fid].push(n)});

  // ═══ Group floors by building ═══（含虚拟楼层 area.id）
  const BUILDING_GAP=NODE_SIZE+400;
  const hasBuildingsConfig=typeof buildings!=='undefined'&&buildings.length>0;
  // 收集每个 fp 的所有"floor 维度 id"：fp.id（如 fp 没有虚拟子）+ 各 floor area 的 id
  // 按 tab_sort_order 降序排（tab 最右 = 最高楼层，layout 顶端；tab 最左 = 最低楼层，layout 底端）
  function _collectFloorIds(filterFn){
    const items=[];
    floorPlans.forEach(fp=>{
      if(!filterFn(fp.building_id||null))return;
      const _hasVF=(fp.areas||[]).some(a=>a.area_type==='floor');
      if(!_hasVF&&groups[fp.id]){
        const so=(fp.tab_sort_order!=null?fp.tab_sort_order:(fp.sort_order||0));
        items.push({id:fp.id, sortKey:so});
      }
      (fp.areas||[]).forEach(a=>{
        if(a.area_type==='floor'){
          const aBld=a.building_id||fp.building_id||null;
          if(filterFn(aBld)&&groups[a.id])items.push({id:a.id, sortKey:(a.tab_sort_order||0)});
        }
      });
    });
    // sortKey 降序 → 大的在前（layout row 0 = 顶部 = 高层）
    items.sort((a,b)=>b.sortKey-a.sortKey);
    return items.map(it=>it.id);
  }
  const layoutGroups=[];
  if(hasBuildingsConfig){
    const orderedBuildings=buildings.slice().sort((a,b)=>a.sort_order-b.sort_order);
    orderedBuildings.forEach(b=>{
      const bFloorIds=_collectFloorIds(bld=>bld===b.id);
      if(bFloorIds.length) layoutGroups.push({building:b,floorIds:bFloorIds});
    });
    const ungroupedIds=_collectFloorIds(bld=>!bld||!buildings.find(b=>b.id===bld));
    if(ungroupedIds.length) layoutGroups.push({building:null,floorIds:ungroupedIds});
  } else {
    layoutGroups.push({building:null,floorIds:_collectFloorIds(()=>true)});
  }
  const allFloorIds=layoutGroups.flatMap(g=>g.floorIds);

  const floorData={};

  allFloorIds.forEach(fid=>{
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

    // Sort: by riser_index (smaller index = leftmost), non-riser components last
    // fid 可能是真实 fp.id 或虚拟楼层 area.id；后者要找到承载它的 fp
    let fp=floorPlans.find(f=>f.id===fid);
    if(!fp){
      for(const f of floorPlans){
        if((f.areas||[]).some(a=>a.id===fid&&a.area_type==='floor')){fp=f;break}
      }
    }
    const riserAreas=fp?(fp.areas||[]).filter(a=>a.is_riser):[];
    function getCompRiserIndex(cmp){
      const rn=cmp.find(n=>n.is_riser_node);
      if(rn){
        for(const ra of riserAreas){
          if(ra._riser_node_id===rn.id) return ra.riser_index||0;
        }
      }
      for(const ra of riserAreas){
        for(const n of cmp){
          const pl=(fp.placements||[]).find(p=>p.node_id===n.id);
          if(pl){
            const cx=pl.x+NODE_SIZE/2,cy=pl.y+NODE_SIZE/2;
            if(cx>=ra.x&&cx<=ra.x+ra.width&&cy>=ra.y&&cy<=ra.y+ra.height)
              return ra.riser_index||0;
          }
        }
      }
      return Infinity;
    }
    rawComponents.sort((a,b)=>getCompRiserIndex(a)-getCompRiserIndex(b));

    // Process each connected component independently
    const compDataArr=[];
    rawComponents.forEach(comp=>{
      const compIds=new Set(comp.map(n=>n.id));

      // Find root：优先级（新）
      // 1) 连接到 topology-only 节点的边（自然上游，例如 远端直放站 ↔ 光纤近端机）
      // 2) 虚拟 riser 节点
      // 3) 落在 riser area 内的真实设备
      // 4) 连接到其他楼层的跨 component 边
      // 5) fallback comp[0]
      const topoOnlyIds=new Set(nodes.filter(n=>!placedNodeIds.has(n.id)).map(n=>n.id));
      let _isTrunkRoot=false;
      let root=comp.find(n=>edges.some(e=>{
        const other=(e.sourceId===n.id)?e.targetId:(e.targetId===n.id?e.sourceId:null);
        return other!=null && !compIds.has(other) && topoOnlyIds.has(other);
      }));
      if(root)_isTrunkRoot=true;
      if(!root) root=comp.find(n=>n.is_riser_node);
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

      // 干线 trunk root：从 chain 抽出，放到 building 左侧独立列；slot/tier 计算用 chain 剩余部分
      const placedChain=_isTrunkRoot?chain.slice(1):chain;
      // Compute layout metrics for this component
      let nonEndSlots=0;
      placedChain.forEach((cid,ci)=>{
        nonEndSlots++;
        if((leafGroups[cid]||[]).length&&ci<placedChain.length-1)nonEndSlots++;
      });
      let tiersAbove=0,tiersBelow=0;
      placedChain.forEach((cid,ci)=>{
        const lv=leafGroups[cid]||[];
        if(!lv.length)return;
        const isLast=(ci===placedChain.length-1);
        let ta,tb;
        if(!isLast){ta=Math.ceil(lv.length/2);tb=Math.floor(lv.length/2)}
        else{ta=lv.length>=2?Math.ceil((lv.length-1)/2):0;tb=lv.length>=2?Math.floor((lv.length-1)/2):0}
        if(ta>tiersAbove)tiersAbove=ta;
        if(tb>tiersBelow)tiersBelow=tb;
      });

      compDataArr.push({compIds,chain:placedChain,trunkRootId:_isTrunkRoot?root.id:null,leafGroups,nonEndSlots,tiersAbove,tiersBelow,
        hasEndLeaves:(leafGroups[placedChain[placedChain.length-1]]||[]).length>0});
    });

    floorData[fid]={allIds,components:compDataArr};
  });

  // ═══ Phase 2: Place nodes — per building group ═══

  // Pre-compute aligned row Y positions across all buildings (bottom-aligned)
  // Floors are reversed (top floor = index 0), so bottom-align means shorter buildings
  // offset their rows so the LAST row matches the global last row.
  const maxRows=Math.max(0,...layoutGroups.map(g=>g.floorIds.length));
  const rowTiersAbove=new Array(maxRows).fill(0);
  const rowTiersBelow=new Array(maxRows).fill(0);
  layoutGroups.forEach(layoutGroup=>{
    const offset=maxRows-layoutGroup.floorIds.length; // bottom-align offset
    layoutGroup.floorIds.forEach((fid,localIdx)=>{
      const globalIdx=localIdx+offset;
      const fd=floorData[fid];
      const ta=Math.max(0,...fd.components.map(c=>c.tiersAbove));
      const tb=Math.max(0,...fd.components.map(c=>c.tiersBelow));
      if(ta>rowTiersAbove[globalIdx])rowTiersAbove[globalIdx]=ta;
      if(tb>rowTiersBelow[globalIdx])rowTiersBelow[globalIdx]=tb;
    });
  });
  const alignedRowY=[];
  {let y=startY;for(let r=0;r<maxRows;r++){alignedRowY[r]=y+rowTiersAbove[r]*gapV;y=alignedRowY[r]+rowTiersBelow[r]*gapV+gapV+gapV*0.5}}
  // 锚点对齐：把 alignedRowY 整体平移，使顶部行 Y 等于现有 floor 节点 bbox 的最小 Y
  // → 中央机房保持不动，天线区域整体保留之前的 Y 范围
  if(_existingFloorAnchor && alignedRowY.length){
    const _shift=_existingFloorAnchor.y-alignedRowY[0];
    if(_shift)alignedRowY.forEach((_,i)=>{alignedRowY[i]+=_shift});
  }

  let buildingStartX=startX;
  layoutGroups.forEach((layoutGroup,groupIdx)=>{
    const bldFloorIds=layoutGroup.floorIds;

    // Compute column alignment for this building's floors
    const maxCompCount=Math.max(0,...bldFloorIds.map(fid=>floorData[fid].components.length));
    const bldCompSlots=new Array(maxCompCount).fill(0);
    bldFloorIds.forEach(fid=>{
      const fd=floorData[fid];
      fd.components.forEach((comp,compIdx)=>{
        let slotIdx=0;
        comp.chain.forEach((cid,i)=>{
          slotIdx++;
          if((comp.leafGroups[cid]||[]).length)slotIdx++;
        });
        if(slotIdx>bldCompSlots[compIdx])bldCompSlots[compIdx]=slotIdx;
      });
    });
    const bldCompX=[buildingStartX];
    for(let ci=0;ci<maxCompCount;ci++){
      bldCompX[ci+1]=(bldCompX[ci]||buildingStartX)+bldCompSlots[ci]*gapH;
    }

    const bldRowOffset=maxRows-bldFloorIds.length; // bottom-align
    bldFloorIds.forEach((fid,localIdx)=>{
      const fd=floorData[fid];
      const chainY=alignedRowY[localIdx+bldRowOffset];

      fd.components.forEach((comp,compIdx)=>{
        const compX=bldCompX[compIdx];
        // 干线 trunk root：放到本 building 第一列左侧（buildingStartX - gapH）独立列，使 chain 从 compX 起步可与其他楼层对齐
        if(comp.trunkRootId){
          const trunkN=nodes.find(nd=>nd.id===comp.trunkRootId);
          if(trunkN){
            trunkN.x=buildingStartX-gapH;trunkN.y=chainY;
            // trunk root 移动后，与外部 topo 节点的边路由要重置，否则保留老 waypoints 会绕弯
            edges.forEach(e=>{
              if(e.sourceId!==comp.trunkRootId&&e.targetId!==comp.trunkRootId)return;
              const otherId=(e.sourceId===comp.trunkRootId)?e.targetId:e.sourceId;
              if(comp.compIds.has(otherId))return; // 内部边由后面的代码统一处理
              delete e.waypoints;delete e.midPos;
              e.routeMode='ortho3';
              const other=nodes.find(n=>n.id===otherId);
              if(!other)return;
              const trunkCx=trunkN.x+(trunkN.w||NODE_SIZE)/2;
              const otherCx=other.x+(other.w||NODE_SIZE)/2;
              const trunkIsRight=trunkCx>=otherCx;
              if(e.sourceId===comp.trunkRootId){
                e.sourcePort=trunkIsRight?'left':'right';
                e.targetPort=trunkIsRight?'right':'left';
              } else {
                e.targetPort=trunkIsRight?'left':'right';
                e.sourcePort=trunkIsRight?'right':'left';
              }
            });
          }
        }
        // 单节点 chain 且无 leaf（典型情况：某楼层只有 1 个末端天线）→ 放到 building 最右列，与其他楼层末端天线对齐
        const _onlySingleLeaf = comp.chain.length===1 && !(comp.leafGroups[comp.chain[0]]||[]).length && !comp.trunkRootId;
        if(_onlySingleLeaf && bldCompSlots[compIdx]>1){
          const cid=comp.chain[0];
          const n=nodes.find(nd=>nd.id===cid);
          if(n){n.x=compX+(bldCompSlots[compIdx]-1)*gapH;n.y=chainY}
          return;  // skip the regular slot loop
        }
        let slotIdx=0;
        comp.chain.forEach((cid,i)=>{
          const n=nodes.find(nd=>nd.id===cid);
          if(n){n.x=compX+slotIdx*gapH;n.y=chainY}
          slotIdx++;
          const leaves=comp.leafGroups[cid]||[];
          const isLast=(i===comp.chain.length-1);
          if(leaves.length){
            if(!isLast){
              const leafX=compX+slotIdx*gapH;
              leaves.forEach((ln,j)=>{
                ln.x=leafX;
                const t=Math.floor(j/2)+1;
                ln.y=(j%2===0)?chainY-t*gapV:chainY+t*gapV;
              });
              slotIdx++;
            }else{
              const leafX=bldCompX[compIdx]+(bldCompSlots[compIdx]-1)*gapH;
              leaves.forEach((ln,j)=>{
                ln.x=leafX;
                if(j===0)ln.y=chainY;
                else{const t=Math.ceil(j/2);ln.y=(j%2===1)?chainY-t*gapV:chainY+t*gapV}
              });
              slotIdx++;
            }
          }
        });
      });

      // Update edge ports and routing for this floor group
      edges.forEach(e=>{
        if(!fd.allIds.has(e.sourceId)||!fd.allIds.has(e.targetId))return;
        const src=nodes.find(n=>n.id===e.sourceId);
        const tgt=nodes.find(n=>n.id===e.targetId);
        if(!src||!tgt)return;
        const srcCx=src.x+(src.w||NODE_SIZE)/2, srcCy=src.y+(src.h||NODE_SIZE)/2;
        const tgtCx=tgt.x+(tgt.w||NODE_SIZE)/2, tgtCy=tgt.y+(tgt.h||NODE_SIZE)/2;
        const dy=Math.abs(srcCy-tgtCy);
        e.routeMode='ortho3';
        delete e.midPos;
        if(dy>NODE_SIZE){
          const leftIsSource=srcCx<=tgtCx;
          const leftCx=leftIsSource?srcCx:tgtCx;
          const rightCy=leftIsSource?tgtCy:srcCy;
          const rightIsAbove=rightCy<(leftIsSource?srcCy:tgtCy);
          const leftPort=rightIsAbove?'top':'bottom';
          if(leftIsSource){e.sourcePort=leftPort;e.targetPort='left'}
          else{e.sourcePort='left';e.targetPort=leftPort}
          e.waypoints=[{x:leftCx,y:rightCy}];
        }else{
          const leftIsSource=src.x<=tgt.x;
          e.sourcePort=leftIsSource?'right':'left';
          e.targetPort=leftIsSource?'left':'right';
          const left=leftIsSource?src:tgt, right=leftIsSource?tgt:src;
          const lCx=left.x+(left.w||NODE_SIZE)/2, rCx=right.x+(right.w||NODE_SIZE)/2;
          const lCy=left.y+(left.h||NODE_SIZE)/2, rCy=right.y+(right.h||NODE_SIZE)/2;
          const midX=(lCx+rCx)/2;
          e.waypoints=[{x:midX,y:lCy},{x:midX,y:rCy}];
        }
      });

    });

    // Advance X for next building group
    const buildingWidth=(bldCompX[maxCompCount]||buildingStartX)-buildingStartX;
    if(buildingWidth>0&&groupIdx<layoutGroups.length-1) buildingStartX+=buildingWidth+BUILDING_GAP;
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

        // 计算翻译偏移：第一个 building 若有 trunk root（已占 startX-gapH 列），room 要再往左让一个 trunk 列宽
        const _firstBldHasTrunk=(layoutGroups[0]?.floorIds||[]).some(fid=>
          (floorData[fid]?.components||[]).some(c=>c.trunkRootId)
        );
        const _leftmostLayoutX=_firstBldHasTrunk?(startX-gapH):startX;
        const targetAreaX=_leftmostLayoutX-roomGap-area.width;
        const dx=targetAreaX-area.x;
        let dy=0;
        if(anchorRoomNode&&anchorFloorNode){
          // Align anchor room node Y with its connected floor node Y
          dy=anchorFloorNode.y-anchorRoomNode.y;
        }

        // Translate entire group: area + all contained nodes + internal edge waypoints
        area.x+=dx;
        area.y+=dy;
        roomNodes.forEach(n=>{n.x+=dx;n.y+=dy});

        // Translate waypoints of edges BETWEEN room nodes (both ends inside room)
        const roomIdSet=new Set(roomNodes.map(n=>n.id));
        edges.forEach(e=>{
          if(roomIdSet.has(e.sourceId)&&roomIdSet.has(e.targetId)){
            if(e.waypoints&&e.waypoints.length){
              e.waypoints.forEach(wp=>{wp.x+=dx;wp.y+=dy});
            }
            if(e.midPos!==undefined){
              // midPos is a single coordinate (x for horizontal, y for vertical ortho3)
              const isH=(e.sourcePort==='left'||e.sourcePort==='right'||e.sourcePort==='top-left'||e.sourcePort==='bottom-left'||e.sourcePort==='top-right'||e.sourcePort==='bottom-right');
              e.midPos+=isH?dx:dy;
            }
          }
        });

        // Room→floor edges (coax, fiber, etc.) — preserve user's manual routing.
        // Only translate their waypoints by the same (dx,dy) as the room nodes.
        roomNodes.forEach(rn=>{
          edges.forEach(e=>{
            const isSource=e.sourceId===rn.id;
            const isTarget=e.targetId===rn.id;
            if(!isSource&&!isTarget)return;
            const otherNid=isSource?e.targetId:e.sourceId;
            if(!placedNodeIds.has(otherNid))return;
            // Translate waypoints to follow room translation (keep relative shape)
            if(e.waypoints&&e.waypoints.length){
              e.waypoints.forEach(wp=>{wp.x+=dx;wp.y+=dy});
            }
            if(e.midPos!==undefined){
              const isH=(e.sourcePort==='left'||e.sourcePort==='right'||e.sourcePort==='top-left'||e.sourcePort==='bottom-left'||e.sourcePort==='top-right'||e.sourcePort==='bottom-right');
              e.midPos+=isH?dx:dy;
            }
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

  // 平面图新建的节点默认不出现在系统图，要等用户点同步按钮才进
  node.in_topology=false;
  fp.placements.push({node_id:node.id,x:x,y:y,locked:false,rotation:0});
  // 计算归属（含虚拟楼层 label 解析）
  if(typeof _applyOwnershipToNode==='function')_applyOwnershipToNode(node, fp, x, y);

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
    const _px=Math.round(x/10)*10, _py=Math.round(y/10)*10;
    fp.placements.push({node_id:nodeId,x:_px,y:_py,locked:false,rotation:0,qty:1});
    // 计算归属（含虚拟楼层 label 解析）
    if(typeof _applyOwnershipToNode==='function')_applyOwnershipToNode(n, fp, _px, _py);
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
// 只同步 area_label 与 floor_label 显示文本，不再覆盖 floor_id/building_id
// （这两个字段归 _applyOwnershipToNode 管，含虚拟楼层归属逻辑；老逻辑会把 floor_id 强行写回 fp.id 导致虚拟楼层归属丢失）
function syncFloorAreaLabels(){
  floorPlans.forEach(fp=>{
    fp.placements.forEach(p=>{
      const node=nodes.find(n=>n.id===p.node_id);
      if(!node)return;
      // floor_label：根据节点当前 floor_id 解析（真实 fp 或虚拟楼层 area）
      if(node.floor_id){
        const realFp=floorPlans.find(f=>f.id===node.floor_id);
        if(realFp){node.floor_label=realFp.label||''}
        else{
          let fa=null;
          for(const f of floorPlans){
            const a=(f.areas||[]).find(a=>a.id===node.floor_id);
            if(a){fa=a;break}
          }
          node.floor_label=fa?(fa.label||''):(fp.label||'');
        }
      } else {
        node.floor_label=fp.label||'';
      }
      // area_label：保持原最小命中 area 的 label 用于显示
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
let selectedAreaId=null,isDraggingArea=false,dragAreaId=null,areaDragOffset={x:0,y:0},dragAreaPrevPos=null,dragAreaContainedNodeIds=null;
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
    const newX=Math.round((pt.x-areaDragOffset.x)/10)*10;
    const newY=Math.round((pt.y-areaDragOffset.y)/10)*10;
    const adx=newX-(dragAreaPrevPos?dragAreaPrevPos.x:area.x);
    const ady=newY-(dragAreaPrevPos?dragAreaPrevPos.y:area.y);
    area.x=newX;area.y=newY;
    dragAreaPrevPos={x:newX,y:newY};
    // Move contained nodes along with the area
    if(dragAreaContainedNodeIds&&dragAreaContainedNodeIds.length&&(adx||ady)){
      const idSet=new Set(dragAreaContainedNodeIds);
      if(currentView==='topology'){
        nodes.forEach(n=>{if(idSet.has(n.id)){n.x+=adx;n.y+=ady}});
        // Also translate waypoints of edges where both ends are inside the area
        edges.forEach(e=>{
          if(idSet.has(e.sourceId)&&idSet.has(e.targetId)&&e.waypoints&&e.waypoints.length){
            e.waypoints.forEach(wp=>{wp.x+=adx;wp.y+=ady});
          }
        });
      }else{
        const fp=getFloorPlan(currentView);
        if(fp)(fp.placements||[]).forEach(p=>{if(idSet.has(p.node_id)){p.x+=adx;p.y+=ady}});
      }
    }
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
    const _wasDragId=dragAreaId;
    isDraggingArea=false;dragAreaId=null;dragAreaPrevPos=null;dragAreaContainedNodeIds=null;if(currentView!=='topology')syncFloorAreaLabels();
    // area 拖动后：floor 类型重新继承 building_id；全部节点重算归属
    if(currentView!=='topology'){
      const _fp=getFloorPlan(currentView);
      if(_fp){
        const _a=(_fp.areas||[]).find(a=>a.id===_wasDragId);
        if(_a&&_a.area_type==='floor')reinheritFloorAreaBuilding(_a, _fp);
        recomputeAllPlacementOwnership(_fp);
      }
    }
    isDraggingOperation=false;if(pendingRenderFrame){cancelAnimationFrame(pendingRenderFrame);pendingRenderFrame=null}renderAll();
  }
  if(isResizingArea){
    const _wasResizeId=resizeAreaId;
    isResizingArea=false;resizeAreaId=null;resizeAreaStart=null;if(currentView!=='topology')syncFloorAreaLabels();
    if(currentView!=='topology'){
      const _fp=getFloorPlan(currentView);
      if(_fp){
        const _a=(_fp.areas||[]).find(a=>a.id===_wasResizeId);
        if(_a&&_a.area_type==='floor')reinheritFloorAreaBuilding(_a, _fp);
        recomputeAllPlacementOwnership(_fp);
      }
    }
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
