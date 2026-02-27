/**
 * PMA 系统图编辑器 — 拓扑视图
 * 节点/连线渲染、交互拖拽、属性面板、连线弹窗、图例
 * 依赖: system-diagram-core.js (必须先加载)
 */

// ====== TOPOLOGY RENDER ======
function renderTopologyView(){
  const floorBg=document.getElementById('floorBgImage');if(floorBg)floorBg.remove();
  renderEdges();renderMidHandles();renderNodes();buildLegend();
}

function renderNodes(){
  const layer=document.getElementById('nodesLayer');layer.innerHTML='';
  nodes.forEach(n=>{
    const isSel=selectedNodeIds.has(n.id);
    const g=document.createElementNS('http://www.w3.org/2000/svg','g');g.setAttribute('class',`node-group ${isSel?'selected':''}`);g.setAttribute('transform',`translate(${n.x},${n.y})`);g.dataset.nodeId=n.id;
    const glow=document.createElementNS('http://www.w3.org/2000/svg','circle');glow.setAttribute('class','node-glow');glow.setAttribute('cx',n.w/2);glow.setAttribute('cy',n.h/2);glow.setAttribute('r',n.w/2+8);glow.setAttribute('fill',n.color);glow.setAttribute('opacity',isSel?'0.15':'0');glow.style.transition='opacity .2s';g.appendChild(glow);
    const hit=document.createElementNS('http://www.w3.org/2000/svg','rect');hit.setAttribute('x',-8);hit.setAttribute('y',-8);hit.setAttribute('width',n.w+16);hit.setAttribute('height',n.h+LABEL_OFFSET+28);hit.setAttribute('fill','transparent');g.appendChild(hit);
    const ig=document.createElementNS('http://www.w3.org/2000/svg','g');ig.innerHTML=renderIconSVG(n.iconData,n.w,0,0);g.appendChild(ig);
    if(isSel){const ring=document.createElementNS('http://www.w3.org/2000/svg','rect');ring.setAttribute('x',-6);ring.setAttribute('y',-6);ring.setAttribute('width',n.w+12);ring.setAttribute('height',n.h+12);ring.setAttribute('rx',10);ring.setAttribute('fill','none');ring.setAttribute('stroke',n.color);ring.setAttribute('stroke-width',1.5);ring.setAttribute('stroke-dasharray','4 2');ring.setAttribute('opacity',.6);g.appendChild(ring)}
    if(!n.hideLabel){const nameText=displaySettings.iconLabel?n.name:'',modelText=(displaySettings.iconModel&&n.model)?n.model:'',tagText=n.label||'';
    // Floor/area label for topology view
    const floorAreaText=(n.floor_label&&n.floor_label!=='')?`${n.floor_label}${n.area_label?'·'+n.area_label:''}`:'';
    const lines=[];if(nameText)lines.push(nameText);if(modelText)lines.push(modelText);if(tagText)lines.push(tagText);if(floorAreaText)lines.push(floorAreaText);
    if(!lines.length)lines.push(n.name);
    const lblW=Math.max(...lines.map(t=>t.length))*12+12,lblH=lines.length*12+4;
    const side=n.labelPosition||computeBestLabelSide(edges,n.id);
    const lc=getLabelCoords(side,n.w,n.h,lblW,lblH);
    const lblBg=document.createElementNS('http://www.w3.org/2000/svg','rect');lblBg.setAttribute('class','node-label-bg');lblBg.setAttribute('x',lc.bgX);lblBg.setAttribute('y',lc.bgY);lblBg.setAttribute('width',lblW);lblBg.setAttribute('height',lblH);lblBg.setAttribute('rx',4);g.appendChild(lblBg);
    let ly=lc.firstLineY;
    const lbl=document.createElementNS('http://www.w3.org/2000/svg','text');lbl.setAttribute('class','node-label');lbl.setAttribute('x',lc.textX);lbl.setAttribute('y',ly);if(lc.anchor!=='middle')lbl.style.textAnchor=lc.anchor;lbl.textContent=nameText;g.appendChild(lbl);
    if(modelText){ly+=12;const ml=document.createElementNS('http://www.w3.org/2000/svg','text');ml.setAttribute('class','node-sublabel');ml.setAttribute('x',lc.textX);ml.setAttribute('y',ly);if(lc.anchor!=='middle')ml.style.textAnchor=lc.anchor;ml.textContent=modelText;g.appendChild(ml)}
    if(tagText){ly+=12;const tl=document.createElementNS('http://www.w3.org/2000/svg','text');tl.setAttribute('class','node-tag');tl.setAttribute('x',lc.textX);tl.setAttribute('y',ly);if(lc.anchor!=='middle')tl.style.textAnchor=lc.anchor;tl.textContent=tagText;g.appendChild(tl)}
    if(floorAreaText){ly+=12;const fl=document.createElementNS('http://www.w3.org/2000/svg','text');fl.setAttribute('class','node-sublabel');fl.setAttribute('x',lc.textX);fl.setAttribute('y',ly);if(lc.anchor!=='middle')fl.style.textAnchor=lc.anchor;fl.setAttribute('fill','#64748b');fl.setAttribute('font-size','9');fl.textContent=floorAreaText;g.appendChild(fl)}}
    if(n.qty>1){const bx=n.w-4,by=-4;const bg=document.createElementNS('http://www.w3.org/2000/svg','circle');bg.setAttribute('class','qty-badge-bg');bg.setAttribute('cx',bx);bg.setAttribute('cy',by);bg.setAttribute('r',11);bg.style.fill='var(--bg-panel)';g.appendChild(bg);const qt=document.createElementNS('http://www.w3.org/2000/svg','text');qt.setAttribute('class','node-qty-badge');qt.setAttribute('x',bx);qt.setAttribute('y',by+3.5);qt.setAttribute('text-anchor','middle');qt.textContent=`×${n.qty}`;g.appendChild(qt)}
    const _R=n.w/2+8,_D=_R*.7071,_cx=n.w/2,_cy=n.h/2;
    [{name:'top',cx:_cx,cy:_cy-_R},{name:'right',cx:_cx+_R,cy:_cy},{name:'bottom',cx:_cx,cy:_cy+_R},{name:'left',cx:_cx-_R,cy:_cy},{name:'top-left',cx:_cx-_D,cy:_cy-_D},{name:'top-right',cx:_cx+_D,cy:_cy-_D},{name:'bottom-left',cx:_cx-_D,cy:_cy+_D},{name:'bottom-right',cx:_cx+_D,cy:_cy+_D}].forEach(p=>{const port=document.createElementNS('http://www.w3.org/2000/svg','circle');port.setAttribute('class','port');port.setAttribute('cx',p.cx);port.setAttribute('cy',p.cy);port.setAttribute('r',5);
      port.style.cursor='crosshair';
      if(selectedEdgeId!==null){const se=edges.find(e=>e.id===selectedEdgeId);if(se&&((se.sourceId===n.id&&se.sourcePort===p.name)||(se.targetId===n.id&&se.targetPort===p.name))){port.setAttribute('r',7);port.style.fill='#3b82f6';port.style.stroke='#1d4ed8';port.style.strokeWidth='2';port.style.cursor='grab';port.style.filter='drop-shadow(0 0 3px rgba(59,130,246,.5))'}}
      port.dataset.nodeId=n.id;port.dataset.port=p.name;port.addEventListener('mousedown',onPortMouseDown);g.appendChild(port)});
    g.style.cursor=n.locked?'not-allowed':'move';
    g.addEventListener('mousedown',onNodeMouseDown);
    g.addEventListener('contextmenu',e=>{e.preventDefault();e.stopPropagation();showNodeCtxMenu(e.clientX,e.clientY,n.id)});
    layer.appendChild(g)});
}

// ====== RENDER EDGES ======
function renderEdges(){
  const layer=document.getElementById('edgesLayer');layer.innerHTML='';
  const hitLayer=document.getElementById('edgeHitLayer');hitLayer.innerHTML='';
  const labelEls=[];
  edges.forEach(edge=>{
    if(edge._hidden)return;
    const result=buildEdgePath(edge);if(!result||!result.path)return;
    const w=getEffectiveCableWidth(edge.width);const isSelected=selectedEdgeId===edge.id||selectedEdgeIds.has(edge.id);const ec=getEffectiveCableColor(edge.color);
    const edgeClickHandler=e=>{e.stopPropagation();if(e.shiftKey||e.metaKey||e.ctrlKey){toggleEdgeSelection(edge.id)}else{selectEdge(edge.id)}};
    const hitPath=document.createElementNS('http://www.w3.org/2000/svg','path');hitPath.setAttribute('class','edge-hit');hitPath.setAttribute('d',result.path);hitPath.setAttribute('stroke-width',Math.max(w+12,18));hitPath.dataset.edgeId=edge.id;hitPath.addEventListener('click',edgeClickHandler);hitLayer.appendChild(hitPath);
    if(isSelected){const selPath=document.createElementNS('http://www.w3.org/2000/svg','path');selPath.setAttribute('d',result.path);selPath.setAttribute('stroke','#3b82f6');selPath.setAttribute('stroke-width',w+6);selPath.setAttribute('stroke-opacity','0.3');selPath.setAttribute('fill','none');selPath.setAttribute('stroke-linecap','round');selPath.setAttribute('stroke-linejoin','round');layer.appendChild(selPath)}
    const path=document.createElementNS('http://www.w3.org/2000/svg','path');path.setAttribute('class','edge-line');path.setAttribute('d',result.path);path.setAttribute('stroke',ec);path.setAttribute('stroke-width',isSelected?w+2:w);if(edge.dash)path.setAttribute('stroke-dasharray',edge.dash);path.setAttribute('stroke-linecap','round');path.setAttribute('stroke-linejoin','round');if(isSelected)path.setAttribute('filter','url(#glow)');layer.appendChild(path);
    // Build display: label + length from linked floor route
    const _showLbl=edge.label&&!edge.hideLabel&&displaySettings.cableLabel;
    let _lenStr='';
    if(displaySettings.cableLength&&typeof floorPlans!=='undefined'){
      for(const fp of floorPlans){
        const r=(fp.routes||[]).find(r=>r.linked_edge_id===edge.id);
        if(r&&fp.calibration&&fp.calibration.px_per_meter){
          const sn=nodes.find(n=>n.id===r.sourceNodeId),tn=nodes.find(n=>n.id===r.targetNodeId);
          const sp=fp.placements.find(p=>p.node_id===r.sourceNodeId),tp=fp.placements.find(p=>p.node_id===r.targetNodeId);
          if(sn&&tn&&sp&&tp){
            const _sx=sn.x,_sy=sn.y,_tx=tn.x,_ty=tn.y;
            sn.x=sp.x;sn.y=sp.y;tn.x=tp.x;tn.y=tp.y;
            const rLike={sourceId:r.sourceNodeId,targetId:r.targetNodeId,sourcePort:r.sourcePort||'right',targetPort:r.targetPort||'left',routeMode:r.routeMode||'ortho3',midPos:r.midPos,waypoints:r.waypoints};
            const rr=buildEdgePath(rLike);
            sn.x=_sx;sn.y=_sy;tn.x=_tx;tn.y=_ty;
            if(rr&&rr.path){const tmp=document.createElementNS('http://www.w3.org/2000/svg','path');tmp.setAttribute('d',rr.path);const m=tmp.getTotalLength()/fp.calibration.px_per_meter;_lenStr=m>=1?m.toFixed(1)+'m':Math.round(m*100)+'cm'}
          }
          break;
        }
      }
    }
    const _parts=[];if(_showLbl)_parts.push(edge.label);if(_lenStr)_parts.push(_lenStr);
    if(_parts.length){const _txt=_parts.join(' · ');const mid=getPathMidpoint(result,edge);const mx=mid.x,my=mid.y;const tl=_txt.length*7+16;const bg=document.createElementNS('http://www.w3.org/2000/svg','rect');bg.setAttribute('class','edge-label-bg');bg.setAttribute('x',mx-tl/2);bg.setAttribute('y',my-9);bg.setAttribute('width',tl);bg.setAttribute('height',18);bg.setAttribute('rx',4);bg.style.cursor='pointer';bg.addEventListener('click',edgeClickHandler);labelEls.push(bg);const lbl=document.createElementNS('http://www.w3.org/2000/svg','text');lbl.setAttribute('class','edge-label');lbl.setAttribute('x',mx);lbl.setAttribute('y',my);lbl.setAttribute('fill',ec);lbl.style.cursor='pointer';lbl.style.pointerEvents='auto';lbl.addEventListener('click',edgeClickHandler);lbl.textContent=_txt;labelEls.push(lbl)}
  });
  // Append labels after all hit paths so labels are always on top and clickable
  labelEls.forEach(el=>hitLayer.appendChild(el));
}

// ====== MID-SEGMENT DRAG HANDLES ======
let dragWaypointIdx=null;  // index of waypoint being dragged
function renderMidHandles(){
  const layer=document.getElementById('handlesLayer');layer.innerHTML='';
  edges.forEach(edge=>{
    if(selectedEdgeId!==edge.id)return;
    // Polyline waypoint handles
    if(edge.waypoints&&edge.waypoints.length){
      edge.waypoints.forEach((wp,idx)=>{
        const g=document.createElementNS('http://www.w3.org/2000/svg','g');g.setAttribute('class','mid-handle');g.style.cursor='grab';
        const grip=document.createElementNS('http://www.w3.org/2000/svg','circle');grip.setAttribute('class','mid-handle-grip');
        grip.setAttribute('cx',wp.x);grip.setAttribute('cy',wp.y);grip.setAttribute('r',5);g.appendChild(grip);
        g.addEventListener('mousedown',ev=>{ev.stopPropagation();isDraggingMid=true;midDragMoved=false;dragMidEdgeId=edge.id;dragWaypointIdx=idx});
        layer.appendChild(g);
      });
      return;
    }
    // Ortho3 mid-handle (original logic)
    if(edge.routeMode!=='ortho3')return;
    const result=buildEdgePath(edge);if(!result||!result.c1||!result.c2)return;
    const g=document.createElementNS('http://www.w3.org/2000/svg','g');g.setAttribute('class','mid-handle');
    if(result.isH){g.style.cursor='ew-resize';
      const bar=document.createElementNS('http://www.w3.org/2000/svg','line');bar.setAttribute('class','mid-handle-bar');bar.setAttribute('x1',result.c1.x);bar.setAttribute('y1',result.c1.y);bar.setAttribute('x2',result.c2.x);bar.setAttribute('y2',result.c2.y);g.appendChild(bar);
      const midY=(result.c1.y+result.c2.y)/2;const grip=document.createElementNS('http://www.w3.org/2000/svg','circle');grip.setAttribute('class','mid-handle-grip');grip.setAttribute('cx',result.c1.x);grip.setAttribute('cy',midY);g.appendChild(grip);
    }else{g.style.cursor='ns-resize';
      const bar=document.createElementNS('http://www.w3.org/2000/svg','line');bar.setAttribute('class','mid-handle-bar');bar.setAttribute('x1',result.c1.x);bar.setAttribute('y1',result.c1.y);bar.setAttribute('x2',result.c2.x);bar.setAttribute('y2',result.c2.y);g.appendChild(bar);
      const midX=(result.c1.x+result.c2.x)/2;const grip=document.createElementNS('http://www.w3.org/2000/svg','circle');grip.setAttribute('class','mid-handle-grip');grip.setAttribute('cx',midX);grip.setAttribute('cy',result.c1.y);g.appendChild(grip);
    }
    g.addEventListener('mousedown',e=>{e.stopPropagation();isDraggingMid=true;midDragMoved=false;dragMidEdgeId=edge.id;dragWaypointIdx=null});
    layer.appendChild(g);
  });
}

// ====== SELECTION ======
function selectNode(id){selectedNodeIds=new Set([id]);selectedNodeId=id;selectedEdgeId=null;selectedEdgeIds=new Set();renderAll();if(currentView==='topology')showNodeProps(id);else if(typeof showFloorNodeProps==='function'){showFloorNodeProps(id);if(typeof highlightConnectedInPanel==='function')highlightConnectedInPanel(id)}}
function selectEdge(id){selectedEdgeId=id;selectedEdgeIds=new Set([id]);selectedNodeIds=new Set();selectedNodeId=null;renderAll();showEdgeProps(id)}
function toggleEdgeSelection(id){
  if(selectedEdgeIds.has(id)){selectedEdgeIds.delete(id)}else{selectedEdgeIds.add(id)}
  selectedEdgeId=selectedEdgeIds.size===1?[...selectedEdgeIds][0]:null;
  renderAll();
  if(selectedNodeIds.size===0&&selectedEdgeIds.size===1)showEdgeProps([...selectedEdgeIds][0]);
  else if(selectedNodeIds.size>0||selectedEdgeIds.size>1)showMultiProps();
  else hideProps();
}
function deleteSelected(){
  if(DIAGRAM_CONFIG.readOnly)return;
  pushHistory();let cnt=0;
  if(selectedNodeIds.size){
    const ids=selectedNodeIds;
    // Floor plan view: soft/hard delete based on node origin
    if(typeof currentView!=='undefined'&&currentView!=='topology'&&typeof floorPlans!=='undefined'){
      const fp=typeof getFloorPlan==='function'?getFloorPlan(currentView):null;
      if(fp){
        ids.forEach(nid=>{
          const n=nodes.find(nd=>nd.id===nid);
          fp.placements=fp.placements.filter(p=>p.node_id!==nid);
          if(fp.routes)fp.routes=fp.routes.filter(r=>r.sourceNodeId!==nid&&r.targetNodeId!==nid);
          if(n&&n._floorCreated){
            // Floor-created device: full delete from system
            edges=edges.filter(e=>e.sourceId!==nid&&e.targetId!==nid);
            nodes=nodes.filter(nd=>nd.id!==nid);
            floorPlans.forEach(f=>{f.placements=f.placements.filter(p=>p.node_id!==nid)});
          }else if(n){
            // Existing system device: just unplace from floor
            n.floor_id=null;n.floor_label='';n.area_label='';
          }
        });
        cnt+=ids.size;
        if(typeof syncRiserNodes==='function')syncRiserNodes(fp);
        if(typeof syncFloorAreaLabels==='function')syncFloorAreaLabels();
        if(typeof buildExistingDevicesPanel==='function')buildExistingDevicesPanel();
      }
    }else{
      // Topology view: full delete
      edges=edges.filter(e=>!ids.has(e.sourceId)&&!ids.has(e.targetId));
      nodes=nodes.filter(n=>!ids.has(n.id));
      if(typeof floorPlans!=='undefined'){
        floorPlans.forEach(fp=>{fp.placements=fp.placements.filter(p=>!ids.has(p.node_id))});
      }
      cnt+=ids.size;
    }
  }
  if(selectedEdgeIds.size){
    const eids=selectedEdgeIds;
    edges=edges.filter(e=>!eids.has(e.id));
    cnt+=eids.size;
  }else if(selectedEdgeId&&!selectedNodeIds.size){
    edges=edges.filter(e=>e.id!==selectedEdgeId);cnt++;
  }
  // Floor plan view: also handle selected route deletion
  if(typeof selectedRouteId!=='undefined'&&selectedRouteId!==null&&!selectedNodeIds.size&&!selectedEdgeId){
    const fp=typeof getFloorPlan==='function'?getFloorPlan(currentView):null;
    if(fp&&fp.routes){
      const route=fp.routes.find(r=>r.id===selectedRouteId);
      if(route&&route.linked_edge_id)edges=edges.filter(e=>e.id!==route.linked_edge_id);
      fp.routes=fp.routes.filter(r=>r.id!==selectedRouteId);
      selectedRouteId=null;cnt++;
    }
  }
  if(cnt){selectedNodeIds=new Set();selectedEdgeIds=new Set();selectedNodeId=null;selectedEdgeId=null;
    hasUnsavedChanges=true;renderAll();hideProps();showToast(`${_t('已删除')} ${cnt} ${_t('个元素')}`)}
}

function selectAllNodes(){
  if(currentView!=='topology'){
    // Floor plan: only select nodes placed on current floor
    const fp=typeof getFloorPlan==='function'?getFloorPlan(currentView):null;
    if(fp){
      selectedNodeIds=new Set(fp.placements.map(p=>p.node_id));
      selectedEdgeIds=new Set();
    }
  }else{
    selectedNodeIds=new Set(nodes.map(n=>n.id));
    selectedEdgeIds=new Set(edges.map(e=>e.id));
  }
  selectedEdgeId=null;
  selectedNodeId=selectedNodeIds.size===1?[...selectedNodeIds][0]:null;
  renderAll();
  if(selectedNodeIds.size===1&&selectedEdgeIds.size===0)showNodeProps([...selectedNodeIds][0]);
  else if(selectedNodeIds.size>0||selectedEdgeIds.size>0)showMultiProps();
}

// ====== NODE DRAG ======
function onNodeMouseDown(e){
  if(e.target.classList.contains('port'))return;e.stopPropagation();if(currentTool!=='select')setTool('select');
  const nid=parseInt(e.currentTarget.dataset.nodeId);const node=nodes.find(n=>n.id===nid);if(!node)return;
  if(e.shiftKey||e.metaKey||e.ctrlKey){
    if(selectedNodeIds.has(nid)){selectedNodeIds.delete(nid)}else{selectedNodeIds.add(nid)}
    selectedEdgeId=null;selectedNodeId=selectedNodeIds.size===1?[...selectedNodeIds][0]:null;
    renderAll();
    if(selectedNodeIds.size===1)showNodeProps([...selectedNodeIds][0]);
    else if(selectedNodeIds.size>1)showMultiProps();
    else hideProps();
  } else {
    if(!selectedNodeIds.has(nid))selectNode(nid);
  }
  if(DIAGRAM_CONFIG.readOnly)return; // allow selection but prevent drag
  // Check lock in topology mode
  if(currentView==='topology'&&node.locked)return;
  isDragging=true;dragMoved=false;dragNodeId=nid;
  // Use placement coords in floor plan mode
  if(currentView!=='topology'){
    const fp=getFloorPlan(currentView);
    const pl=fp?fp.placements.find(p=>p.node_id===nid):null;
    const pt=svgPoint(e);dragOffsetX=pt.x-(pl?pl.x:node.x);dragOffsetY=pt.y-(pl?pl.y:node.y);
    dragStartPositions=new Map();selectedNodeIds.forEach(id=>{const p2=fp?fp.placements.find(p=>p.node_id===id):null;if(p2)dragStartPositions.set(id,{x:p2.x,y:p2.y})});
  }else{
    const pt=svgPoint(e);dragOffsetX=pt.x-node.x;dragOffsetY=pt.y-node.y;
    dragStartPositions=new Map();selectedNodeIds.forEach(id=>{const n=nodes.find(n=>n.id===id);if(n)dragStartPositions.set(id,{x:n.x,y:n.y})});
  }
}

// Global mouse event handlers for drag/pan/connect
document.addEventListener('mousemove',e=>{
  if(isDragging&&dragNodeId){if(!dragMoved){pushHistory();dragMoved=true}const pt=svgPoint(e);const dn=nodes.find(n=>n.id===dragNodeId);if(dn){
    // Check lock in floor plan mode
    if(currentView!=='topology'){
      const fp=getFloorPlan(currentView);
      if(fp){const pl=fp.placements.find(p=>p.node_id===dn.id);if(pl&&pl.locked)return}
    }
    const nx=Math.round((pt.x-dragOffsetX)/10)*10,ny=Math.round((pt.y-dragOffsetY)/10)*10;
    if(currentView!=='topology'){
      // Floor plan mode: only update placement coords, not n.x/n.y
      const fp=getFloorPlan(currentView);
      if(fp){
        if(selectedNodeIds.size>1&&dragStartPositions&&dragStartPositions.has(dragNodeId)){
          const dx=nx-dragStartPositions.get(dragNodeId).x,dy=ny-dragStartPositions.get(dragNodeId).y;
          selectedNodeIds.forEach(id=>{const pl=fp.placements.find(p=>p.node_id===id);const s=dragStartPositions.get(id);if(pl&&s){pl.x=s.x+dx;pl.y=s.y+dy}});
        }else{const pl=fp.placements.find(p=>p.node_id===dn.id);if(pl){pl.x=nx;pl.y=ny}}
      }
    }else{
      // Topology mode: update n.x/n.y
      if(selectedNodeIds.size>1&&dragStartPositions&&dragStartPositions.has(dragNodeId)){
        const dx=nx-dragStartPositions.get(dragNodeId).x,dy=ny-dragStartPositions.get(dragNodeId).y;
        selectedNodeIds.forEach(id=>{const n=nodes.find(n=>n.id===id);const s=dragStartPositions.get(id);if(n&&s){n.x=s.x+dx;n.y=s.y+dy}});
      }else{dn.x=nx;dn.y=ny}
    }
    hasUnsavedChanges=true;isDraggingOperation=true;requestRenderThrottled()}}
  if(isPanning){viewX=panViewX+(e.clientX-panStartX);viewY=panViewY+(e.clientY-panStartY);updateTransform()}
  if(isConnecting&&connSourceId){const pt=svgPoint(e);if(typeof isReconnectingFloor!=='undefined'&&isReconnectingFloor)renderFloorReconnectLine(pt.x,pt.y);else renderTempEdge(pt.x,pt.y)}
  if(isDraggingMid&&dragMidEdgeId!==null){
    if(!midDragMoved){pushHistory();midDragMoved=true}const pt=svgPoint(e);const edge=edges.find(e=>e.id===dragMidEdgeId);
    if(edge){
      // Polyline waypoint drag
      if(dragWaypointIdx!==null&&edge.waypoints&&edge.waypoints[dragWaypointIdx]){
        edge.waypoints[dragWaypointIdx]={x:Math.round(pt.x),y:Math.round(pt.y)};
        hasUnsavedChanges=true;isDraggingOperation=true;requestRenderThrottled();
      }else{
        const src=nodes.find(n=>n.id===edge.sourceId),tgt=nodes.find(n=>n.id===edge.targetId);
        if(src&&tgt){const isH=(edge.sourcePort==='left'||edge.sourcePort==='right');
          edge.midPos=isH?Math.round(pt.x/10)*10:Math.round(pt.y/10)*10;
          hasUnsavedChanges=true;isDraggingOperation=true;requestRenderThrottled();}
      }
    }
  }
  // Floor route mid-handle drag
  if(typeof isDraggingFloorMid!=='undefined'&&isDraggingFloorMid&&dragFloorMidRouteId!==null){
    if(!floorMidDragMoved){pushHistory();floorMidDragMoved=true}
    const pt=svgPoint(e);const fp=typeof getFloorPlan==='function'?getFloorPlan(currentView):null;
    if(fp){const route=fp.routes.find(r=>r.id===dragFloorMidRouteId);
      if(route){
        // Polyline waypoint drag for floor routes
        if(typeof dragFloorWaypointIdx==='number'&&route.waypoints&&route.waypoints[dragFloorWaypointIdx]){
          route.waypoints[dragFloorWaypointIdx]={x:Math.round(pt.x),y:Math.round(pt.y)};
          // Sync to linked edge
          if(route.linked_edge_id){const le=edges.find(e2=>e2.id===route.linked_edge_id);if(le&&le.waypoints)le.waypoints[dragFloorWaypointIdx]={x:Math.round(pt.x),y:Math.round(pt.y)}}
          hasUnsavedChanges=true;isDraggingOperation=true;requestRenderThrottled();
        }else{
          const srcPl=fp.placements.find(p=>p.node_id===route.sourceNodeId);const tgtPl=fp.placements.find(p=>p.node_id===route.targetNodeId);
          if(srcPl&&tgtPl){const rMode=route.routeMode||'ortho3';
            const autoP=(!route._userPorts)?findBestPort(srcPl,tgtPl,(nodes.find(n=>n.id===route.sourceNodeId)||{}).w||NODE_SIZE,rMode):null;
            const sp=autoP?autoP.srcPort:(route.sourcePort||'right');
            const isH=(sp==='left'||sp==='right'||sp==='top-left'||sp==='bottom-left'||sp==='top-right'||sp==='bottom-right');
            route.midPos=isH?Math.round(pt.x/10)*10:Math.round(pt.y/10)*10;
            hasUnsavedChanges=true;isDraggingOperation=true;requestRenderThrottled()}
        }
      }}
  }
});

document.addEventListener('mouseup',e=>{
  const wasDraggingOp=isDraggingOperation;
  const wasPanning=isPanning;
  const panMoved=isPanning&&(Math.abs(e.clientX-panStartX)>3||Math.abs(e.clientY-panStartY)>3);
  if(isDragging&&dragMoved&&currentView!=='topology'){
    if(typeof snapToRiserIfNeeded==='function'){const fp=getFloorPlan(currentView);if(fp){selectedNodeIds.forEach(id=>{const pl=fp.placements.find(p=>p.node_id===id);if(pl)snapToRiserIfNeeded(pl,fp)})}}
    if(typeof syncRiserNodes==='function'){const fp=getFloorPlan(currentView);if(fp)syncRiserNodes(fp)}
    if(typeof syncFloorAreaLabels==='function')syncFloorAreaLabels();
    if(typeof tryInsertIntoRoute==='function')tryInsertIntoRoute(dragNodeId,currentView);
  }
  isDragging=false;dragNodeId=null;isPanning=false;isDraggingMid=false;dragMidEdgeId=null;dragWaypointIdx=null;
  if(typeof isDraggingFloorMid!=='undefined'){isDraggingFloorMid=false;dragFloorMidRouteId=null;if(typeof dragFloorWaypointIdx!=='undefined')dragFloorWaypointIdx=null}
  // Reset drag optimization state and force full render to restore skipped elements
  isDraggingOperation=false;
  if(pendingRenderFrame){cancelAnimationFrame(pendingRenderFrame);pendingRenderFrame=null}
  if(wasDraggingOp)renderAll();
  if(typeof isReconnectingFloor!=='undefined'&&isReconnectingFloor&&!isConnecting){isReconnectingFloor=false;reconnectFloorRouteId=null;reconnectFloorEnd='';reconnectFloorFixedPos=null}
  if(isConnecting){
    // Click-persistent mode: only complete connection when clicking a valid target port
    let completed=false,reconnected=false;
    if(e.target.classList&&e.target.classList.contains('port')){
      const tid=parseInt(e.target.dataset.nodeId),tp=e.target.dataset.port;
      if(tid!==connSourceId){
        completed=true;
        if(typeof isReconnectingFloor!=='undefined'&&isReconnectingFloor){
          const fp=typeof getFloorPlan==='function'?getFloorPlan(currentView):null;
          if(fp){const route=fp.routes.find(r=>r.id===reconnectFloorRouteId);
            if(route){pushHistory();if(reconnectFloorEnd==='source'){route.sourceNodeId=tid;route.sourcePort=tp}else{route.targetNodeId=tid;route.targetPort=tp}
              route._userPorts=true;if(route.routeMode==='ortho3')delete route.midPos;
              if(route.linked_edge_id){const le=edges.find(e2=>e2.id===route.linked_edge_id);if(le){if(reconnectFloorEnd==='source'){le.sourceId=tid;le.sourcePort=tp}else{le.targetId=tid;le.targetPort=tp}}}
              hasUnsavedChanges=true;reconnected=true;selectedRouteId=route.id;}}
        }else if(isReconnecting){
          const re=edges.find(e=>e.id===reconnectEdgeId);
          if(re){pushHistory();if(reconnectEnd==='source'){re.sourceId=tid;re.sourcePort=tp}else{re.targetId=tid;re.targetPort=tp}
            delete re._hidden;if(re.routeMode==='ortho3')delete re.midPos;hasUnsavedChanges=true;reconnected=true}
        }else if(currentView==='topology'){
          pushHistory();const defEdge={id:edgeIdCounter++,sourceId:connSourceId,sourcePort:connSourcePort,targetId:tid,targetPort:tp,cableType:null,color:'#94a3b8',width:1.5,dash:'6 4',label:'',routeMode:defaultRouteMode,hideLabel:false,waypoints:polylineWaypoints.length?[...polylineWaypoints]:undefined};
          edges.push(defEdge);pendingEdge=defEdge.id;showConnTypePopup(e.clientX,e.clientY);
        }else{
          // Floor plan mode: create edge + floor route
          createFloorRoute(connSourceId,connSourcePort,tid,tp,e.clientX,e.clientY);
        }
      }
    }
    // Only clean up state when connection was completed; otherwise keep the temp line following mouse
    if(completed){
      if(isReconnecting&&!reconnected){const re=edges.find(e=>e.id===reconnectEdgeId);if(re)delete re._hidden}
      isReconnecting=false;reconnectEdgeId=null;reconnectEnd='';
      const _wasFloorReconnect=typeof isReconnectingFloor!=='undefined'&&isReconnectingFloor;
      if(_wasFloorReconnect){isReconnectingFloor=false;reconnectFloorRouteId=null;reconnectFloorEnd='';reconnectFloorFixedPos=null}
      polylineWaypoints=[];isConnecting=false;connSourceId=null;document.getElementById('tempLayer').innerHTML='';
      setTool('select');renderAll();
      if(reconnected&&typeof selectedRouteId!=='undefined'&&selectedRouteId!==null&&typeof showFloorRouteProps==='function')showFloorRouteProps(selectedRouteId);
    }
    // Not completed: left-click on canvas (not drag/pan, not on a port) places a waypoint
    if(!completed&&!panMoved&&e.button===0&&!isReconnecting&&!(typeof isReconnectingFloor!=='undefined'&&isReconnectingFloor)
      &&!(e.target.classList&&e.target.classList.contains('port'))){
      const pt=svgPoint(e);polylineWaypoints.push({x:Math.round(pt.x),y:Math.round(pt.y)});
    }
  }
});

// ====== CONNECTION DRAWING ======
function onPortMouseDown(e){
  if(DIAGRAM_CONFIG.readOnly)return;
  e.stopPropagation();const nid=parseInt(e.target.dataset.nodeId),port=e.target.dataset.port;
  // Click-persistent mode: if already connecting, don't override source — let mouseup handle completion
  if(isConnecting&&connSourceId!==null)return;
  if(selectedEdgeId!==null){
    const se=edges.find(e=>e.id===selectedEdgeId);
    if(se){
      const isSrc=se.sourceId===nid&&se.sourcePort===port,isTgt=se.targetId===nid&&se.targetPort===port;
      if(isSrc||isTgt){
        isReconnecting=true;reconnectEdgeId=se.id;reconnectEnd=isSrc?'source':'target';
        connSourceId=isSrc?se.targetId:se.sourceId;connSourcePort=isSrc?se.targetPort:se.sourcePort;
        se._hidden=true;isConnecting=true;renderAll();return;
      }
    }
  }
  isConnecting=true;connSourceId=nid;connSourcePort=port;
}
function renderTempEdge(mx,my){const layer=document.getElementById('tempLayer');const src=nodes.find(n=>n.id===connSourceId);if(!src)return;
  const isFloor=currentView!=='topology';
  const comp=(isFloor&&typeof getTempEdgeZoomCompensation==='function')?getTempEdgeZoomCompensation():1;
  const sw=3*comp;const bsw=5*comp;const wr=5*comp;const wsw=2*comp;const da=`${8*comp} ${4*comp}`;
  let posObj=src;
  if(currentView!=='topology'&&typeof getFloorPlan==='function'){const fp=getFloorPlan(currentView);if(fp){const pl=fp.placements.find(p=>p.node_id===connSourceId);if(pl)posObj={x:pl.x,y:pl.y,w:src.w,h:src.h}}}
  const sp=getPortPos(posObj,connSourcePort);
  if(polylineWaypoints.length===0){
    let h='';
    if(isFloor)h+=`<line x1="${sp.x}" y1="${sp.y}" x2="${mx}" y2="${my}" style="stroke:rgba(255,255,255,0.6);stroke-width:${bsw};stroke-dasharray:${da};fill:none"/>`;
    h+=`<line class="edge-temp" x1="${sp.x}" y1="${sp.y}" x2="${mx}" y2="${my}" style="stroke:#3b82f6;stroke-width:${sw};stroke-dasharray:${da};fill:none"/>`;
    layer.innerHTML=h;return}
  const pts=[sp,...polylineWaypoints,{x:mx,y:my}];let html='';
  if(isFloor){for(let i=0;i<pts.length-2;i++){html+=`<line x1="${pts[i].x}" y1="${pts[i].y}" x2="${pts[i+1].x}" y2="${pts[i+1].y}" style="stroke:rgba(255,255,255,0.6);stroke-width:${bsw};fill:none"/>`}
    const bL=pts[pts.length-2],bC=pts[pts.length-1];html+=`<line x1="${bL.x}" y1="${bL.y}" x2="${bC.x}" y2="${bC.y}" style="stroke:rgba(255,255,255,0.6);stroke-width:${bsw};stroke-dasharray:${da};fill:none"/>`}
  for(let i=0;i<pts.length-2;i++){html+=`<line class="edge-temp" x1="${pts[i].x}" y1="${pts[i].y}" x2="${pts[i+1].x}" y2="${pts[i+1].y}" style="stroke:#3b82f6;stroke-width:${sw};stroke-opacity:0.9;fill:none"/>`}
  const last=pts[pts.length-2],cur=pts[pts.length-1];
  html+=`<line class="edge-temp" x1="${last.x}" y1="${last.y}" x2="${cur.x}" y2="${cur.y}" style="stroke:#3b82f6;stroke-width:${sw};stroke-dasharray:${da};fill:none"/>`;
  polylineWaypoints.forEach(wp=>{html+=`<circle cx="${wp.x}" cy="${wp.y}" r="${wr}" style="fill:#3b82f6;fill-opacity:0.8;stroke:#fff;stroke-width:${wsw}"/>`});
  layer.innerHTML=html}

function showConnTypePopup(x,y){
  const popup=document.getElementById('connTypePopup');
  const cats=[...new Set(Object.values(CABLE_TYPES).map(c=>_m(c.category)))];
  let html=`<div class="conn-type-popup-title">${_t('选择线缆类型')}</div>`;
  cats.forEach(cat=>{html+=`<div style="font-size:10px;color:var(--text-muted);padding:4px 10px 2px;font-weight:600;">${cat}</div>`;
    Object.entries(CABLE_TYPES).filter(([,c])=>_m(c.category)===cat).forEach(([key,c])=>{
      html+=`<div class="conn-type-option" data-cable="${key}"><div>${cableLineSVG(key,36,12)}</div><div style="flex:1"><div>${_m(c.shortName)}</div><div style="font-size:10px;color:var(--text-muted);">${_m(c.desc)}</div></div></div>`})});
  document.getElementById('connTypeList').innerHTML=html;
  popup.style.display='block';
  const ppW=document.getElementById('propsPanel').classList.contains('visible')?290:0;
  popup.style.left=Math.min(x,window.innerWidth-ppW-220)+'px';popup.style.top=Math.min(y,window.innerHeight-popup.offsetHeight-20)+'px';popup.style.maxHeight=(window.innerHeight-40)+'px';popup.style.overflowY='auto';popupShowTime=Date.now();
  popup.querySelectorAll('.conn-type-option').forEach(el=>{el.addEventListener('click',()=>setConnType(el.dataset.cable))});
}

// setConnType() defined in floorplan.js (superset: handles both floor routes + topology edges)
document.addEventListener('click',e=>{if(Date.now()-popupShowTime<300)return;if(!e.target.closest('.conn-type-popup')){document.getElementById('connTypePopup').style.display='none';if(pendingEdge!==null){
  // Also clean up pending floor route
  if(typeof pendingFloorRoute!=='undefined'&&pendingFloorRoute!==null){const fp=getFloorPlan(currentView);if(fp)fp.routes=fp.routes.filter(r=>r.id!==pendingFloorRoute);pendingFloorRoute=null}
  edges=edges.filter(ed=>ed.id!==pendingEdge);pendingEdge=null;renderAll()}}});

// ====== PROPERTIES PANEL ======
function showNodeProps(id){
  const n=nodes.find(n=>n.id===id);if(!n)return;
  const panel=document.getElementById('propsPanel');
  panel.classList.add('visible');
  document.getElementById('propsTitle').innerHTML=`<div style="display:flex;align-items:center;gap:8px;">${renderIconPanel(n.iconData).replace('<svg','<svg width="24" height="24"')} ${_t('节点属性')}</div>`;

  let modelHtml='';
  if(n.products&&n.products.length>1){
    let opts=`<option value="">${_t('-- 选择型号 --')}</option>`;
    n.products.forEach(p=>{
      opts+=`<option value="${p.id}" ${n.selectedProductId===p.id?'selected':''}>${p.model||p.mn||p.productName}</option>`;
    });
    modelHtml=`<div class="props-field"><span class="props-label">${_t('选择产品')}</span><select class="props-select" onchange="updateNodeModel(${id},this.value)">${opts}</select></div>`;
  } else if(n.products&&n.products.length===1){
    modelHtml=`<div class="props-field"><span class="props-label">${_t('产品')}</span><input class="props-input" value="${n.products[0].model||n.products[0].mn||n.model}" disabled></div>`;
  }

  let productCard='';
  const selProduct=n.selectedProductId?(n.products||[]).find(p=>p.id===n.selectedProductId):null;
  if(selProduct){
    const esc=s=>(s||'').replace(/"/g,'&quot;').replace(/</g,'&lt;');
    const iconHtml=renderIconPanel(selProduct.iconData||n.iconData).replace('<svg','<svg width="48" height="48"');
    productCard=`<div style="margin:8px 0;padding:10px;border:1px solid var(--border);border-radius:8px;background:var(--bg-canvas);overflow:hidden;">
      <div style="margin:-10px -10px 8px;background:var(--bg-input);text-align:center;min-height:80px;display:flex;align-items:center;justify-content:center;padding:12px;">
        ${selProduct.imageUrl
          ?`<img src="${selProduct.imageUrl}" alt="" style="max-width:100%;max-height:120px;object-fit:contain;" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'"><div style="display:none;flex-direction:column;align-items:center;gap:4px;opacity:.5;">${iconHtml}<span style="font-size:10px;color:var(--text-muted);">${_t('暂无图片')}</span></div>`
          :`<div style="display:flex;flex-direction:column;align-items:center;gap:4px;opacity:.5;">${iconHtml}<span style="font-size:10px;color:var(--text-muted);">${_t('暂无图片')}</span></div>`}
      </div>
      <div style="font-size:12px;line-height:1.8;">
        ${selProduct.productName?`<div style="display:flex;gap:6px;"><span style="color:var(--text-muted);white-space:nowrap;min-width:52px;">${_t('名称')}</span><span style="font-weight:600;color:var(--text-primary);">${esc(selProduct.productName)}</span></div>`:''}
        ${selProduct.mn?`<div style="display:flex;gap:6px;"><span style="color:var(--text-muted);white-space:nowrap;min-width:52px;">MN</span><span style="font-family:monospace;color:var(--text-secondary);">${esc(selProduct.mn)}</span></div>`:''}
        ${selProduct.model?`<div style="display:flex;gap:6px;"><span style="color:var(--text-muted);white-space:nowrap;min-width:52px;">${_t('型号')}</span><span style="color:var(--text-secondary);">${esc(selProduct.model)}</span></div>`:''}
        ${selProduct.specs?`<div style="margin-top:4px;padding-top:4px;border-top:1px solid var(--border);"><span style="color:var(--text-muted);font-size:11px;">${_t('规格')}</span><div style="color:var(--text-secondary);font-size:11px;margin-top:2px;white-space:pre-wrap;max-height:80px;overflow-y:auto;">${esc(selProduct.specs)}</div></div>`:''}
      </div>
      ${selProduct.iconData&&selProduct.iconData!==n.iconData?`<button onclick="replaceNodeIcon(${id})" style="margin-top:6px;width:100%;padding:6px;border:1px solid var(--accent,#3b82f6);border-radius:6px;background:transparent;color:var(--accent,#3b82f6);cursor:pointer;font-size:12px;display:flex;align-items:center;justify-content:center;gap:4px;transition:all .15s;" onmouseenter="this.style.background='var(--accent,#3b82f6)';this.style.color='#fff'" onmouseleave="this.style.background='transparent';this.style.color='var(--accent,#3b82f6)'">${renderIconPanel(selProduct.iconData).replace('<svg','<svg width="16" height="16"')} ${_t('替换当前图标')}</button>`:''}
    </div>`;
  }

  document.getElementById('propsContent').innerHTML=`
    <div class="props-field"><span class="props-label">${_t('子分类')}</span><input class="props-input" value="${n.name}" disabled></div>
    ${modelHtml}
    ${productCard}
    <div class="props-field"><span class="props-label">${_t('位置标签')}</span><input class="props-input" value="${n.label||''}" placeholder="${_t('如：1F-A区')}" oninput="updateNodeProp(${id},'label',this.value)"></div>
    <div class="props-field"><label style="display:flex;align-items:center;gap:8px;cursor:pointer;"><input type="checkbox" ${n.hideLabel?'checked':''} onchange="updateNodeProp(${id},'hideLabel',this.checked)"><span class="props-label" style="margin:0;">${_t('隐藏标签')}</span></label></div>
    <div class="props-field"><span class="props-label">${_t('数量')}</span><input class="props-input" type="number" min="1" value="${n.qty}" oninput="updateNodeProp(${id},'qty',parseInt(this.value)||1)"></div>
    ${typeof buildCoveragePropsHTML==='function'?buildCoveragePropsHTML(id):''}
    <button class="btn-delete" onclick="deleteSelected()">${_t('删除节点')}</button>`;
}

function updateNodeModel(nodeId, productIdStr){
  const n=nodes.find(n=>n.id===nodeId);if(!n)return;
  pushHistory();const pid=parseInt(productIdStr);
  if(!pid){n.selectedProductId=null;n.model='';hasUnsavedChanges=true;renderAll();showNodeProps(nodeId);return;}
  const p=(n.products||[]).find(p=>p.id===pid);
  if(p){
    n.selectedProductId=p.id;
    n.model=p.model||p.mn||p.productName||'';
    hasUnsavedChanges=true;renderAll();showNodeProps(nodeId);
  }
}

function replaceNodeIcon(nodeId){
  const n=nodes.find(n=>n.id===nodeId);if(!n)return;
  const p=n.selectedProductId?(n.products||[]).find(p=>p.id===n.selectedProductId):null;
  if(p&&p.iconData){
    pushHistory();n.iconData=p.iconData;
    hasUnsavedChanges=true;renderAll();showNodeProps(nodeId);
  }
}

function showEdgeProps(id){
  const edge=edges.find(e=>e.id===id);if(!edge)return;
  const srcN=nodes.find(n=>n.id===edge.sourceId),tgtN=nodes.find(n=>n.id===edge.targetId);
  document.getElementById('propsPanel').classList.add('visible');document.getElementById('propsTitle').textContent=_t('连线属性');
  let cableOpts='';[...new Set(Object.values(CABLE_TYPES).map(c=>_m(c.category)))].forEach(cat=>{cableOpts+=`<optgroup label="${cat}">`;Object.entries(CABLE_TYPES).filter(([,ct])=>_m(ct.category)===cat).forEach(([key,ct])=>{cableOpts+=`<option value="${key}" ${edge.cableType===key?'selected':''}>${_m(ct.name)}</option>`});cableOpts+='</optgroup>'});
  const routePreview=(mode)=>{const active=(edge.routeMode||'bezier')===mode?'active':'';const svgs={bezier:`<svg viewBox="0 0 28 16"><path d="M2 14 C10 14 18 2 26 2" fill="none" stroke="${active?'#60a5fa':'var(--text-muted)'}" stroke-width="2"/></svg>`,ortho2:`<svg viewBox="0 0 28 16"><path d="M2 14 L2 2 L26 2" fill="none" stroke="${active?'#60a5fa':'var(--text-muted)'}" stroke-width="2" stroke-linejoin="round"/></svg>`,ortho3:`<svg viewBox="0 0 28 16"><path d="M2 14 L14 14 L14 2 L26 2" fill="none" stroke="${active?'#60a5fa':'var(--text-muted)'}" stroke-width="2" stroke-linejoin="round"/>${active?'<circle cx="14" cy="8" r="2" fill="#3b82f6"/>':''}</svg>`,straight:`<svg viewBox="0 0 28 16"><line x1="2" y1="14" x2="26" y2="2" stroke="${active?'#60a5fa':'var(--text-muted)'}" stroke-width="2"/></svg>`};return `<div class="route-mode-btn ${active}" onclick="updateEdgeRoute(${id},'${mode}')">${svgs[mode]}<span>${_t({bezier:'弧线',ortho2:'一折',ortho3:'二折',straight:'直线'}[mode])}</span></div>`};
  document.getElementById('propsContent').innerHTML=`
    <div class="props-section">${_t('线缆类型')}</div>
    <div class="props-field"><div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">${cableLineSVG(edge.cableType,40,12)}<span style="font-size:12px;color:${edge.color};">${CABLE_TYPES[edge.cableType]?_m(CABLE_TYPES[edge.cableType].name):_t('未知')}</span></div>
    <select class="props-select" onchange="updateEdgeCableType(${id},this.value)">${cableOpts}</select></div>
    <div class="props-section">${_t('路由模式')}</div>
    <div class="props-field"><div class="route-mode-btns">${routePreview('bezier')}${routePreview('ortho2')}${routePreview('ortho3')}${routePreview('straight')}</div></div>
    ${edge.routeMode==='ortho3'?`<div style="font-size:10px;color:var(--text-muted);padding:2px 0;">${_t('提示：选中后拖动中间段调整位置')}</div>`:''}
    ${edge.routeMode==='ortho3'?`<div class="props-field"><span class="props-label">${_t('中间段位置')}</span><div class="props-row"><button onclick="resetMidPos(${id})" style="padding:4px 10px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-secondary);font-size:11px;cursor:pointer;">${_t('重置居中')}</button></div></div>`:''}
    <div class="props-section">${_t('线路样式')}</div>
    <div class="props-field"><span class="props-label">${_t('颜色')}</span><div class="props-row"><input type="color" class="props-color" value="${edge.color||'#3b82f6'}" oninput="updateEdgeProp(${id},'color',this.value)"><input class="props-input" style="flex:1;font-family:monospace;font-size:11px;" value="${edge.color||'#3b82f6'}" oninput="updateEdgeProp(${id},'color',this.value)"></div></div>
    <div class="props-field"><span class="props-label">${_t('虚线样式')}</span><select class="props-select" onchange="updateEdgeProp(${id},'dash',this.value)"><option value="" ${!edge.dash?'selected':''}>${_t('实线')}</option><option value="8 4" ${edge.dash==='8 4'?'selected':''}>${_t('长虚线')}</option><option value="4 4" ${edge.dash==='4 4'?'selected':''}>${_t('中虚线')}</option><option value="2 4" ${edge.dash==='2 4'?'selected':''}>${_t('短虚线')}</option><option value="10 3 2 3" ${edge.dash==='10 3 2 3'?'selected':''}>${_t('点划线')}</option></select></div>
    <div class="props-section">${_t('标签')}</div>
    <div class="props-field"><input class="props-input" value="${edge.label||''}" placeholder="${_t('连线标签')}" oninput="updateEdgeProp(${id},'label',this.value)"></div>
    <div class="props-field"><label style="display:flex;align-items:center;gap:8px;cursor:pointer;"><input type="checkbox" ${edge.hideLabel?'checked':''} onchange="updateEdgeProp(${id},'hideLabel',this.checked)"><span class="props-label" style="margin:0;">${_t('隐藏标签')}</span></label></div>
    <div class="props-section">${_t('连接')}</div>
    <div class="props-field"><span class="props-label">${_t('起点')}</span><input class="props-input" value="${srcN?srcN.name:'?'}" disabled></div>
    <div class="props-field"><span class="props-label">${_t('终点')}</span><input class="props-input" value="${tgtN?tgtN.name:'?'}" disabled></div>
    <button class="btn-delete" onclick="deleteSelected()">${_t('删除连线')}</button>`;
}

function hideProps(){document.getElementById('propsPanel').classList.remove('visible')}
function updateNodeProp(id,p,v){const n=nodes.find(n=>n.id===id);if(n){pushHistoryProp();n[p]=v;hasUnsavedChanges=true;renderAll()}}
function updateEdgeProp(id,p,v){const e=edges.find(e=>e.id===id);if(e){pushHistoryProp();e[p]=v;hasUnsavedChanges=true;renderAll();if(selectedEdgeId===id)showEdgeProps(id)}}
function updateEdgeCableType(id,ck){const e=edges.find(e=>e.id===id);if(!e)return;const c=CABLE_TYPES[ck];if(!c)return;pushHistory();e.cableType=ck;e.color=c.color;e.width=c.width;e.dash=c.dash;e.label=_m(c.shortName);hasUnsavedChanges=true;renderAll();showEdgeProps(id)}
function updateEdgeRoute(id,mode){const e=edges.find(e=>e.id===id);if(!e)return;pushHistory();e.routeMode=mode;if(mode!=='ortho3')delete e.midPos;hasUnsavedChanges=true;renderAll();showEdgeProps(id)}
function resetMidPos(id){const e=edges.find(e=>e.id===id);if(e){pushHistory();delete e.midPos;hasUnsavedChanges=true;renderAll();showEdgeProps(id)}}

// ====== MULTI-SELECT PROPS ======
function showMultiProps(){
  const panel=document.getElementById('propsPanel');panel.classList.add('visible');
  document.getElementById('propsTitle').textContent=_t('多选操作');
  const parts=[];
  if(selectedNodeIds.size)parts.push(`<b>${selectedNodeIds.size}</b> ${_t('个节点')}`);
  if(selectedEdgeIds.size)parts.push(`<b>${selectedEdgeIds.size}</b> ${_t('条连线')}`);
  const summary=parts.length?`${_t('已选中')} ${parts.join(_lang==='zh'?'、':', ')}`:`${_t('未选中任何对象')}`;
  document.getElementById('propsContent').innerHTML=`
    <div style="font-size:12px;color:var(--text-secondary);margin-bottom:8px;">${summary}</div>
    <button style="width:100%;padding:8px;background:var(--bg-input);border:1px solid var(--border);border-radius:6px;color:var(--text-primary);font-size:12px;cursor:pointer;margin-bottom:6px;display:flex;align-items:center;justify-content:center;gap:6px;" onclick="copySelected()"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>${_t('复制选中')}</button>
    <button class="btn-delete" onclick="deleteSelected()">${_t('删除选中')}</button>`;
}

// ====== LEGEND ======
function buildLegend(){const used=[...new Set(edges.map(e=>e.cableType).filter(Boolean))];if(!used.length){document.getElementById('legendPanel').innerHTML='';return}let h=`<div class="legend-title">${_t('图例')}</div>`;used.forEach(k=>{const c=CABLE_TYPES[k];if(!c)return;h+=`<div class="legend-item"><div style="width:36px;height:12px;">${cableLineSVG(k,36,12)}</div><span>${_m(c.shortName)}</span></div>`});document.getElementById('legendPanel').innerHTML=h}

// ====== CANVAS INTERACTION ======
// setTool() and svg are defined in core.js
