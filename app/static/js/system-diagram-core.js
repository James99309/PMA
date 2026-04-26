/**
 * PMA 系统图编辑器 — 核心引擎
 * 共享常量、状态、工具函数、产品面板、保存/加载、导出、撤销/重做
 * 依赖: 无（第一个加载）
 */

/* ── i18n helpers ── */
const _lang = (document.documentElement.lang||'zh').startsWith('en') ? 'en' : 'zh';
function _t(k){const v=(window.SD_I18N&&window.SD_I18N[k])||k;return(typeof v==='object'&&v!==null)?(v[_lang]||v.zh):v;}
function _m(obj){return (typeof obj==='object'&&obj!==null)?(obj[_lang]||obj.zh):obj;}

// ====== CABLE TYPES ======
const CABLE_TYPES = {
  coax_half:{name:{zh:'1/2" 同轴电缆',en:'1/2" Coax'},shortName:{zh:'1/2" 同轴',en:'1/2" Coax'},color:'#f59e0b',width:2,dash:'',category:{zh:'同轴电缆',en:'Coaxial'},desc:{zh:'室内馈线',en:'Indoor feeder'}},
  coax_78:{name:{zh:'7/8" 同轴电缆',en:'7/8" Coax'},shortName:{zh:'7/8" 同轴',en:'7/8" Coax'},color:'#f59e0b',width:4,dash:'',category:{zh:'同轴电缆',en:'Coaxial'},desc:{zh:'主干馈线',en:'Main feeder'}},
  coax_114:{name:{zh:'1-1/4" 同轴电缆',en:'1-1/4" Coax'},shortName:{zh:'1¼" 同轴',en:'1-1/4" Coax'},color:'#d97706',width:6,dash:'',category:{zh:'同轴电缆',en:'Coaxial'},desc:{zh:'超粗主干',en:'High-power feeder'}},
  coax_flex:{name:{zh:'柔性同轴电缆',en:'Flex Coax'},shortName:{zh:'柔性同轴',en:'Flex Coax'},color:'#fbbf24',width:2,dash:'8 4',category:{zh:'同轴电缆',en:'Coaxial'},desc:{zh:'跳线连接',en:'Jumper cable'}},
  fiber_single:{name:{zh:'单模光纤',en:'SM Fiber'},shortName:{zh:'单模光纤',en:'SM'},color:'#a855f7',width:2,dash:'',category:{zh:'光纤',en:'Fiber'},desc:{zh:'长距离传输',en:'Long-range'}},
  fiber_multi:{name:{zh:'多模光纤',en:'MM Fiber'},shortName:{zh:'多模光纤',en:'MM'},color:'#c084fc',width:2.5,dash:'6 2',category:{zh:'光纤',en:'Fiber'},desc:{zh:'短距离高带宽',en:'Short-range'}},
  fiber_armored:{name:{zh:'铠装光缆',en:'Armored Fiber'},shortName:{zh:'铠装光缆',en:'Armored'},color:'#7c3aed',width:4,dash:'',category:{zh:'光纤',en:'Fiber'},desc:{zh:'室外敷设',en:'Outdoor laying'}},
  power_ac:{name:{zh:'AC 电源线',en:'AC Power'},shortName:{zh:'AC电源',en:'AC'},color:'#ef4444',width:3,dash:'',category:{zh:'电源',en:'Power'},desc:{zh:'交流 220V/380V',en:'AC power'}},
  power_dc48:{name:{zh:'DC -48V 电源线',en:'DC -48V Power'},shortName:{zh:'DC-48V',en:'DC-48V'},color:'#f87171',width:2.5,dash:'10 3',category:{zh:'电源',en:'Power'},desc:{zh:'直流供电',en:'DC power'}},
  power_gnd:{name:{zh:'接地线',en:'Ground'},shortName:{zh:'接地线',en:'GND'},color:'#fca5a5',width:1.5,dash:'4 4',category:{zh:'电源',en:'Power'},desc:{zh:'保护接地',en:'Protective ground'}},
  signal_rf:{name:{zh:'RF 射频信号',en:'RF Signal'},shortName:{zh:'RF信号',en:'RF'},color:'#3b82f6',width:2,dash:'',category:{zh:'信号',en:'Signal'},desc:{zh:'射频传输',en:'RF transmission'}},
  data_eth:{name:{zh:'以太网线 CAT6',en:'Cat6 Ethernet'},shortName:{zh:'网线CAT6',en:'Cat6'},color:'#22c55e',width:2,dash:'',category:{zh:'数据',en:'Data'},desc:{zh:'网络/PoE',en:'Network/PoE'}},
  data_serial:{name:{zh:'控制线',en:'Control Cable'},shortName:{zh:'控制线',en:'Ctrl'},color:'#4ade80',width:1,dash:'3 3',category:{zh:'数据',en:'Data'},desc:{zh:'设备管理',en:'Device mgmt'}},
  gps:{name:{zh:'GPS 天馈线',en:'GPS Cable'},shortName:{zh:'GPS天馈',en:'GPS'},color:'#06b6d4',width:1.5,dash:'5 5',category:{zh:'其他',en:'Other'},desc:{zh:'GPS馈线',en:'GPS signal'}},
};

// ====== DEFAULT DEVICE ICONS (fallback when product has no icon_svg) ======
const DEFAULT_DEVICE_ICONS = {
  rru:'<svg width="47px" height="69px" viewBox="0 0 47 69" xmlns="http://www.w3.org/2000/svg"><g stroke="none" stroke-width="1" fill="none" fill-rule="evenodd"><g><rect stroke="currentColor" stroke-width="1.5" x="3.75" y="0.75" width="38.5" height="67.5" rx="1"/><g transform="translate(0,4)"><line x1="0.5" y1="64.5" x2="46.5" y2="64.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><g transform="translate(6,0)"><rect stroke="currentColor" x="0.5" y="0.5" width="33" height="8" rx="1"/><circle stroke="currentColor" fill="currentColor" cx="3.5" cy="2.5" r="1"/><circle stroke="currentColor" fill="currentColor" cx="5.5" cy="2.5" r="1"/><circle stroke="currentColor" fill="currentColor" cx="7.5" cy="2.5" r="1"/><circle stroke="currentColor" fill="currentColor" cx="3.5" cy="6.5" r="1"/><circle stroke="currentColor" fill="currentColor" cx="5.5" cy="6.5" r="1"/><circle stroke="currentColor" fill="currentColor" cx="7.5" cy="6.5" r="1"/><rect stroke="currentColor" fill="currentColor" x="11.5" y="2.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="11.5" y="4.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="11.5" y="6.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="13.5" y="2.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="13.5" y="4.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="13.5" y="6.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="15.5" y="2.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="15.5" y="4.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="15.5" y="6.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="17.5" y="2.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="17.5" y="4.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="17.5" y="6.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="21.5" y="3.5" width="9" height="3"/></g><g transform="translate(6,11)"><rect stroke="currentColor" x="0.5" y="0.5" width="33" height="8" rx="1"/><circle stroke="currentColor" fill="currentColor" cx="3.5" cy="2.5" r="1"/><circle stroke="currentColor" fill="currentColor" cx="5.5" cy="2.5" r="1"/><circle stroke="currentColor" fill="currentColor" cx="7.5" cy="2.5" r="1"/><circle stroke="currentColor" fill="currentColor" cx="3.5" cy="6.5" r="1"/><circle stroke="currentColor" fill="currentColor" cx="5.5" cy="6.5" r="1"/><circle stroke="currentColor" fill="currentColor" cx="7.5" cy="6.5" r="1"/><rect stroke="currentColor" fill="currentColor" x="11.5" y="2.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="11.5" y="4.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="11.5" y="6.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="13.5" y="2.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="13.5" y="4.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="13.5" y="6.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="15.5" y="2.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="15.5" y="4.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="15.5" y="6.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="17.5" y="2.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="17.5" y="4.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="17.5" y="6.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="21.5" y="3.5" width="9" height="3"/></g><g transform="translate(6,22)"><rect stroke="currentColor" x="0.5" y="0.5" width="33" height="8" rx="1"/><circle stroke="currentColor" fill="currentColor" cx="3.5" cy="2.5" r="1"/><circle stroke="currentColor" fill="currentColor" cx="5.5" cy="2.5" r="1"/><circle stroke="currentColor" fill="currentColor" cx="7.5" cy="2.5" r="1"/><circle stroke="currentColor" fill="currentColor" cx="3.5" cy="6.5" r="1"/><circle stroke="currentColor" fill="currentColor" cx="5.5" cy="6.5" r="1"/><circle stroke="currentColor" fill="currentColor" cx="7.5" cy="6.5" r="1"/><rect stroke="currentColor" fill="currentColor" x="11.5" y="2.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="11.5" y="4.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="11.5" y="6.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="13.5" y="2.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="13.5" y="4.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="13.5" y="6.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="15.5" y="2.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="15.5" y="4.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="15.5" y="6.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="17.5" y="2.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="17.5" y="4.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="17.5" y="6.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="21.5" y="3.5" width="9" height="3"/></g><g transform="translate(6,33)"><rect stroke="currentColor" x="0.5" y="0.5" width="33" height="8" rx="1"/><circle stroke="currentColor" fill="currentColor" cx="3.5" cy="2.5" r="1"/><circle stroke="currentColor" fill="currentColor" cx="5.5" cy="2.5" r="1"/><circle stroke="currentColor" fill="currentColor" cx="7.5" cy="2.5" r="1"/><circle stroke="currentColor" fill="currentColor" cx="3.5" cy="6.5" r="1"/><circle stroke="currentColor" fill="currentColor" cx="5.5" cy="6.5" r="1"/><circle stroke="currentColor" fill="currentColor" cx="7.5" cy="6.5" r="1"/><rect stroke="currentColor" fill="currentColor" x="11.5" y="2.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="11.5" y="4.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="11.5" y="6.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="13.5" y="2.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="13.5" y="4.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="13.5" y="6.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="15.5" y="2.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="15.5" y="4.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="15.5" y="6.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="17.5" y="2.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="17.5" y="4.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="17.5" y="6.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="21.5" y="3.5" width="9" height="3"/></g><g transform="translate(6,44)"><rect stroke="currentColor" x="0.5" y="0.5" width="33" height="8" rx="1"/><circle stroke="currentColor" fill="currentColor" cx="3.5" cy="2.5" r="1"/><circle stroke="currentColor" fill="currentColor" cx="5.5" cy="2.5" r="1"/><circle stroke="currentColor" fill="currentColor" cx="7.5" cy="2.5" r="1"/><circle stroke="currentColor" fill="currentColor" cx="3.5" cy="6.5" r="1"/><circle stroke="currentColor" fill="currentColor" cx="5.5" cy="6.5" r="1"/><circle stroke="currentColor" fill="currentColor" cx="7.5" cy="6.5" r="1"/><rect stroke="currentColor" fill="currentColor" x="11.5" y="2.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="11.5" y="4.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="11.5" y="6.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="13.5" y="2.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="13.5" y="4.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="13.5" y="6.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="15.5" y="2.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="15.5" y="4.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="15.5" y="6.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="17.5" y="2.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="17.5" y="4.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="17.5" y="6.5" width="1" height="1"/><rect stroke="currentColor" fill="currentColor" x="21.5" y="3.5" width="9" height="3"/></g><rect stroke="currentColor" fill="currentColor" opacity="0.3" x="7.5" y="58.5" width="9" height="2"/><rect stroke="currentColor" fill="#D8D8D8" x="7.5" y="56.5" width="1" height="1"/><rect stroke="currentColor" fill="#D8D8D8" x="10.5" y="56.5" width="1" height="1"/><rect stroke="currentColor" fill="#D8D8D8" x="13.5" y="56.5" width="1" height="1"/><rect stroke="currentColor" fill="#D8D8D8" x="16.5" y="56.5" width="1" height="1"/></g></g></g></svg>',
  bbu:{viewBox:'0 0 64 64',paths:[{d:'M8 12h48v44H8z',fill:'none',stroke:'#3b82f6',strokeWidth:2},{d:'M12 16h16v8H12zM32 16h20v8H32z',fill:'#3b82f6',opacity:.12,stroke:'#3b82f6',strokeWidth:1},{d:'M12 28h16v8H12zM32 28h20v8H32z',fill:'#3b82f6',opacity:.12,stroke:'#3b82f6',strokeWidth:1},{d:'M12 40h16v8H12zM32 40h20v8H32z',fill:'#3b82f6',opacity:.12,stroke:'#3b82f6',strokeWidth:1},{d:'M14 18v4M16 18v4M34 18v4M36 18v4',fill:'none',stroke:'#60a5fa',strokeWidth:1},{d:'M46 20a2 2 0 1 1 0-.01',fill:'#22c55e',stroke:'none'},{d:'M46 32a2 2 0 1 1 0-.01',fill:'#22c55e',stroke:'none'}]},
  channel_radio:'<svg width="206px" height="71px" viewBox="0 0 206 71" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><g id="Page-1" stroke="none" stroke-width="1" fill="none" fill-rule="evenodd"><rect id="Rectangle-10" stroke="#3b82f6" stroke-width="7" x="25.5" y="19.5" width="152" height="42" rx="6"></rect><rect id="Rectangle-9-Copy" fill-opacity="0.3" fill="#3b82f6" x="76.6707317" y="30.5555556" width="39" height="20" rx="3"></rect><g id="Group" transform="translate(141.2317, 33.7778)" fill="#3b82f6" fill-opacity="0.3"><rect id="Rectangle-11-Copy-10" x="4" y="0" width="10" height="1.88888889" rx="0.944444444"></rect><rect id="Rectangle-11-Copy-14" x="4" y="12" width="10" height="1.88888889" rx="0.944444444"></rect><rect id="Rectangle-11-Copy-11" x="2" y="3" width="14" height="1.88888889" rx="0.944444444"></rect><rect id="Rectangle-11-Copy-13" x="2" y="9" width="14" height="1.88888889" rx="0.944444444"></rect><rect id="Rectangle-11-Copy-12" x="0" y="6" width="18" height="1.88888889" rx="0.944444444"></rect></g><text id="Mark" font-family="Calibri-Bold, Calibri" font-size="12" font-weight="bold" fill="#3b82f6"><tspan x="83" y="45">Mark </tspan></text></g></svg>',
  fm_processor:{viewBox:'0 0 64 64',paths:[{d:'M8 16h48v32H8z',fill:'none',stroke:'#3b82f6',strokeWidth:2},{d:'M14 22h14v8H14z',fill:'#3b82f6',opacity:.1,stroke:'#3b82f6',strokeWidth:.8},{d:'M16 26c2-4 4 4 6-2 2 4 4-2 4 2',fill:'none',stroke:'#60a5fa',strokeWidth:1.5},{d:'M34 24h16v4H34z',fill:'#3b82f6',opacity:.08,stroke:'#3b82f6',strokeWidth:.8},{d:'M36 26h4M42 26h4',fill:'none',stroke:'#60a5fa',strokeWidth:1,opacity:.5},{d:'M14 36h36v6H14z',fill:'#3b82f6',opacity:.06,stroke:'#3b82f6',strokeWidth:.8},{d:'M18 39a1 1 0 1 1 0-.01M24 39a1 1 0 1 1 0-.01M30 39a1 1 0 1 1 0-.01',fill:'#22c55e',opacity:.5,stroke:'none'},{d:'M2 28h6M56 28h6',fill:'none',stroke:'#3b82f6',strokeWidth:2},{d:'M32 10v6',fill:'none',stroke:'#60a5fa',strokeWidth:2},{d:'M28 10a6 4 0 0 1 8 0',fill:'none',stroke:'#60a5fa',strokeWidth:1,opacity:.4}]},
  antenna_outdoor:{viewBox:'0 0 64 64',paths:[{d:'M18 10h28v36H18z',fill:'#22c55e',opacity:.1,stroke:'#22c55e',strokeWidth:2},{d:'M22 14h20M22 20h20M22 26h20M22 32h20',fill:'none',stroke:'#22c55e',strokeWidth:.6,opacity:.3},{d:'M32 4l-6 6h12z',fill:'#4ade80',opacity:.5,stroke:'none'},{d:'M48 12a20 20 0 0 1 0 20',fill:'none',stroke:'#4ade80',strokeWidth:1,opacity:.4},{d:'M28 46v8h8v-8',fill:'none',stroke:'#64748b',strokeWidth:1.5}]},
  antenna_indoor:{viewBox:'0 0 64 64',paths:[{d:'M16 28a16 8 0 1 1 32 0',fill:'#22c55e',opacity:.1,stroke:'#22c55e',strokeWidth:2},{d:'M16 28v4a16 8 0 0 0 32 0v-4',fill:'none',stroke:'#22c55e',strokeWidth:2},{d:'M24 20h16v8H24z',fill:'#22c55e',opacity:.08,stroke:'#22c55e',strokeWidth:1},{d:'M28 16h8v4h-8z',fill:'#22c55e',opacity:.15,stroke:'#22c55e',strokeWidth:1},{d:'M8 16h48',fill:'none',stroke:'#64748b',strokeWidth:1,strokeDasharray:'4 3'},{d:'M22 38a14 6 0 0 0 20 0',fill:'none',stroke:'#4ade80',strokeWidth:1,opacity:.4},{d:'M18 42a20 8 0 0 0 28 0',fill:'none',stroke:'#4ade80',strokeWidth:.8,opacity:.25},{d:'M32 30a1.5 1.5 0 1 1 0-.01',fill:'#22c55e',stroke:'none'},{d:'M32 12v4',fill:'none',stroke:'#64748b',strokeWidth:1.5}]},
  antenna_exproof:{viewBox:'0 0 64 64',paths:[{d:'M20 12h24v36H20z',fill:'#22c55e',opacity:.08,stroke:'#22c55e',strokeWidth:2.5},{d:'M22 14h20v4H22z',fill:'#f59e0b',opacity:.15,stroke:'#f59e0b',strokeWidth:1},{d:'M26 22h12M26 28h12M26 34h12',fill:'none',stroke:'#22c55e',strokeWidth:.8,opacity:.3},{d:'M44 20a8 8 0 0 1 0 16',fill:'none',stroke:'#4ade80',strokeWidth:1,opacity:.35},{d:'M28 48v8h8v-8',fill:'none',stroke:'#64748b',strokeWidth:1.5},{d:'M30 16a2 2 0 1 1 0-.01',fill:'#f59e0b',stroke:'none'}]},
  repeater:{viewBox:'0 0 64 64',paths:[{d:'M12 18h40v28H12z',fill:'none',stroke:'#3b82f6',strokeWidth:2},{d:'M32 24v14',fill:'none',stroke:'#60a5fa',strokeWidth:2},{d:'M26 28a8 8 0 0 1 12 0',fill:'none',stroke:'#60a5fa',strokeWidth:1.5},{d:'M6 32h6M52 32h6',fill:'none',stroke:'#3b82f6',strokeWidth:2},{d:'M54 30l4 2-4 2',fill:'#3b82f6',stroke:'none'}]},
  oru:{viewBox:'0 0 64 64',paths:[{d:'M16 18h32v32H16z',fill:'none',stroke:'#a855f7',strokeWidth:2},{d:'M20 24h24v4H20z',fill:'#a855f7',opacity:.12,stroke:'#a855f7',strokeWidth:1},{d:'M20 32h24v4H20z',fill:'#a855f7',opacity:.12,stroke:'#a855f7',strokeWidth:1},{d:'M28 12v6M36 12v6',fill:'none',stroke:'#c084fc',strokeWidth:2},{d:'M28 12a2 2 0 1 1 0-.01M36 12a2 2 0 1 1 0-.01',fill:'#c084fc',stroke:'none'},{d:'M48 30h6M48 38h6',fill:'none',stroke:'#60a5fa',strokeWidth:2},{d:'M22 42a1.5 1.5 0 1 1 0-.01',fill:'#22c55e',stroke:'none'},{d:'M28 42a1.5 1.5 0 1 1 0-.01',fill:'#f59e0b',stroke:'none'}]},
  omu:{viewBox:'0 0 64 64',paths:[{d:'M10 14h44v40H10z',fill:'none',stroke:'#a855f7',strokeWidth:2},{d:'M14 18h16v10H14z',fill:'#a855f7',opacity:.12,stroke:'#a855f7',strokeWidth:1},{d:'M34 18h16v10H34z',fill:'#a855f7',opacity:.12,stroke:'#a855f7',strokeWidth:1},{d:'M14 32h16v10H14z',fill:'#a855f7',opacity:.12,stroke:'#a855f7',strokeWidth:1},{d:'M34 32h16v10H34z',fill:'#a855f7',opacity:.12,stroke:'#a855f7',strokeWidth:1},{d:'M20 8v6M28 8v6M36 8v6M44 8v6',fill:'none',stroke:'#c084fc',strokeWidth:1.5},{d:'M20 8a1.5 1.5 0 1 1 0-.01M28 8a1.5 1.5 0 1 1 0-.01M36 8a1.5 1.5 0 1 1 0-.01M44 8a1.5 1.5 0 1 1 0-.01',fill:'#c084fc',stroke:'none'},{d:'M16 48a1.5 1.5 0 1 1 0-.01',fill:'#22c55e',stroke:'none'},{d:'M22 48a1.5 1.5 0 1 1 0-.01',fill:'#22c55e',stroke:'none'}]},
  combiner:{viewBox:'0 0 64 64',paths:[{d:'M8 18h12l24 0h12v28H44L20 46H8z',fill:'none',stroke:'#3b82f6',strokeWidth:2},{d:'M2 24h6M2 32h6M2 40h6',fill:'none',stroke:'#60a5fa',strokeWidth:2},{d:'M56 32h6',fill:'none',stroke:'#60a5fa',strokeWidth:2.5}]},
  signal_stripper:{viewBox:'0 0 64 64',paths:[{d:'M8 18h48v28H8z',fill:'none',stroke:'#3b82f6',strokeWidth:2},{d:'M2 26h6M2 38h6',fill:'none',stroke:'#60a5fa',strokeWidth:2},{d:'M56 26h6M56 32h6M56 38h6',fill:'none',stroke:'#60a5fa',strokeWidth:2},{d:'M20 26h24',fill:'none',stroke:'#60a5fa',strokeWidth:1.5},{d:'M28 26v12',fill:'none',stroke:'#f59e0b',strokeWidth:1.5},{d:'M36 26v12',fill:'none',stroke:'#f59e0b',strokeWidth:1.5},{d:'M24 38l4-4 4 4 4-4 4 4',fill:'none',stroke:'#f59e0b',strokeWidth:1.5}]},
  matrix:{viewBox:'0 0 64 64',paths:[{d:'M6 10h52v44H6z',fill:'none',stroke:'#3b82f6',strokeWidth:2},{d:'M6 22h52M6 34h52M6 46h52',fill:'none',stroke:'#3b82f6',strokeWidth:.6,opacity:.3},{d:'M22 10v44M38 10v44',fill:'none',stroke:'#3b82f6',strokeWidth:.6,opacity:.3},{d:'M14 16a2 2 0 1 1 0-.01M30 16a2 2 0 1 1 0-.01M46 16a2 2 0 1 1 0-.01',fill:'#60a5fa',opacity:.5,stroke:'none'},{d:'M14 28a2 2 0 1 1 0-.01M30 28a2 2 0 1 1 0-.01M46 28a2 2 0 1 1 0-.01',fill:'#60a5fa',opacity:.5,stroke:'none'},{d:'M14 40a2 2 0 1 1 0-.01M30 40a2 2 0 1 1 0-.01M46 40a2 2 0 1 1 0-.01',fill:'#60a5fa',opacity:.5,stroke:'none'}]},
  splitter_2:{viewBox:'0 0 64 64',paths:[{d:'M12 20h16v24H12zM28 20l18-6v36l-18-6z',fill:'#a855f7',opacity:.08,stroke:'#a855f7',strokeWidth:2},{d:'M2 32h10',fill:'none',stroke:'#a855f7',strokeWidth:2.5},{d:'M46 20h12M46 44h12',fill:'none',stroke:'#c084fc',strokeWidth:2},{d:'M22 32h8l14-12M30 32l14 12',fill:'none',stroke:'#a855f7',strokeWidth:1,opacity:.5}]},
  splitter_3:{viewBox:'0 0 64 64',paths:[{d:'M12 18h16v28H12zM28 18l18-6v40l-18-6z',fill:'#a855f7',opacity:.08,stroke:'#a855f7',strokeWidth:2},{d:'M2 32h10',fill:'none',stroke:'#a855f7',strokeWidth:2.5},{d:'M46 16h12M46 32h12M46 48h12',fill:'none',stroke:'#c084fc',strokeWidth:2}]},
  coupler:{viewBox:'0 0 64 64',paths:[{d:'M4 24h56',fill:'none',stroke:'#a855f7',strokeWidth:2.5},{d:'M20 18h24v28H20z',fill:'#a855f7',opacity:.08,stroke:'#a855f7',strokeWidth:2},{d:'M32 46v12',fill:'none',stroke:'#c084fc',strokeWidth:2},{d:'M26 30c4-4 8 4 12 0',fill:'none',stroke:'#c084fc',strokeWidth:1.5,opacity:.6}]},
  radio:'<svg width="78px" height="153px" viewBox="0 0 78 153" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"><g id="Page-1" stroke="none" stroke-width="5" fill="none" fill-rule="evenodd"><path d="M46.6585366,43.8575878 L58.0731707,43.8575878 L58.0731707,40.3495352 C58.0731707,39.1785882 57.6255114,38.5931147 56.7301926,38.5931147 C55.3872145,38.5931147 49.7440633,38.5931147 48.2012999,38.5931147 C47.172791,38.5931147 46.6585366,39.1046334 46.6585366,40.1276709 L46.6585366,43.8575878 Z" id="Path" fill="#F5DBAF"></path><path d="M8.86585366,66.0649048 L21.8658537,66.0649048 L21.8658537,62.5568523 C21.8658537,61.3859053 21.3560194,60.8004317 20.3363508,60.8004317 C18.806848,60.8004317 12.3799257,60.8004317 10.6228897,60.8004317 C9.45153234,60.8004317 8.86585366,61.3119505 8.86585366,62.3349879 L8.86585366,66.0649048 Z" id="Path-Copy-17" fill="#F5DBAF" transform="translate(15.3659, 63.4327) rotate(-90) translate(-15.3659, -63.4327)"></path><path d="M8.86585366,81.0649048 L21.8658537,81.0649048 L21.8658537,77.5568523 C21.8658537,76.3859053 21.3560194,75.8004317 20.3363508,75.8004317 C18.806848,75.8004317 12.3799257,75.8004317 10.6228897,75.8004317 C9.45153234,75.8004317 8.86585366,76.3119505 8.86585366,77.3349879 L8.86585366,81.0649048 Z" id="Path-Copy-18" fill="#F5DBAF" transform="translate(15.3659, 78.4327) rotate(-90) translate(-15.3659, -78.4327)"></path><path d="M56.0750805,66.4249195 L73.0750805,66.4249195 L73.0750805,63.7594656 C73.0750805,62.8697682 72.4083742,62.4249195 71.0749614,62.4249195 C69.0748423,62.4249195 60.1811624,62.4249195 58.1281214,62.4249195 C56.7594275,62.4249195 56.0750805,62.8135766 56.0750805,63.5908908 L56.0750805,66.4249195 Z" id="Path" fill="#F5DBAF" transform="translate(64.5751, 64.4249) rotate(90) translate(-64.5751, -64.4249)"></path><rect id="Rectangle-9" fill-opacity="0.3" fill="#F59E0C" x="24.7317073" y="51" width="30.4390244" height="41.5555556" rx="3"></rect><rect id="Rectangle-8" stroke="#F59E0C" x="17.6219512" y="43.9444444" width="44.6585366" height="89.6666667" rx="3"></rect><rect id="Rectangle-11-Copy-4" fill-opacity="0.3" fill="#F59E0C" x="24.7317073" y="96.3333333" width="11.4146341" height="3.77777778" rx="1.88888889"></rect><rect id="Rectangle-11-Copy-6" fill-opacity="0.3" fill="#F59E0C" x="24.7317073" y="105.777778" width="30.4390244" height="1.88888889" rx="0.944444444"></rect><rect id="Rectangle-11-Copy-7" fill-opacity="0.3" fill="#F59E0C" x="24.7317073" y="109.555556" width="30.4390244" height="1.88888889" rx="0.944444444"></rect><rect id="Rectangle-11-Copy-8" fill-opacity="0.3" fill="#F59E0C" x="24.7317073" y="113.333333" width="30.4390244" height="1.88888889" rx="0.944444444"></rect><rect id="Rectangle-11-Copy-9" fill-opacity="0.3" fill="#F59E0C" x="24.7317073" y="117.111111" width="30.4390244" height="1.88888889" rx="0.944444444"></rect><rect id="Rectangle-11-Copy-5" fill-opacity="0.3" fill="#F59E0C" x="43.7560976" y="96.3333333" width="11.4146341" height="3.77777778" rx="1.88888889"></rect><path d="M23.4235514,13.8819658 L23.4235514,43.8575878 L29.9830751,43.8575878 L29.9830751,13.8819658 C29.5020001,11.8657138 28.4087461,10.8575878 26.7033133,10.8575878 C24.9978804,10.8575878 23.9046264,11.8657138 23.4235514,13.8819658 Z" id="Path" stroke="#F59E0C"></path></g></svg>',
  charger:{viewBox:'0 0 64 64',paths:[{d:'M12 20h40v32H12z',fill:'none',stroke:'#f59e0b',strokeWidth:2},{d:'M16 24h14v20H16z',fill:'#f59e0b',opacity:.08,stroke:'#f59e0b',strokeWidth:1},{d:'M34 24h14v20H34z',fill:'#f59e0b',opacity:.08,stroke:'#f59e0b',strokeWidth:1},{d:'M23 30v8',fill:'none',stroke:'#fbbf24',strokeWidth:1.5},{d:'M21 34h4',fill:'none',stroke:'#fbbf24',strokeWidth:1.5},{d:'M41 30v8',fill:'none',stroke:'#fbbf24',strokeWidth:1.5},{d:'M39 34h4',fill:'none',stroke:'#fbbf24',strokeWidth:1.5},{d:'M20 48a1.5 1.5 0 1 1 0-.01',fill:'#22c55e',stroke:'none'},{d:'M38 48a1.5 1.5 0 1 1 0-.01',fill:'#f59e0b',stroke:'none'},{d:'M12 16h40v4H12z',fill:'#f59e0b',opacity:.06,stroke:'none'}]},
  battery:{viewBox:'0 0 64 64',paths:[{d:'M14 18h36v32H14z',fill:'none',stroke:'#f59e0b',strokeWidth:2},{d:'M26 12h12v6H26z',fill:'#f59e0b',opacity:.15,stroke:'#f59e0b',strokeWidth:1.5},{d:'M18 24h28v20H18z',fill:'#f59e0b',opacity:.06,stroke:'none'},{d:'M18 24h18v20H18z',fill:'#22c55e',opacity:.12,stroke:'none'},{d:'M36 28v12',fill:'none',stroke:'#f59e0b',strokeWidth:1,strokeDasharray:'2 2'},{d:'M24 32h4',fill:'none',stroke:'#22c55e',strokeWidth:2},{d:'M26 30v4',fill:'none',stroke:'#22c55e',strokeWidth:2},{d:'M40 32h4',fill:'none',stroke:'#ef4444',strokeWidth:2}]},
  cable_coax:{viewBox:'0 0 64 64',paths:[{d:'M32 8a24 24 0 1 1 0 48a24 24 0 1 1 0-48z',fill:'#f59e0b',opacity:.08,stroke:'#f59e0b',strokeWidth:2},{d:'M32 14a18 18 0 1 1 0 36a18 18 0 1 1 0-36z',fill:'none',stroke:'#f59e0b',strokeWidth:1,strokeDasharray:'3 2'},{d:'M32 20a12 12 0 1 1 0 24a12 12 0 1 1 0-24z',fill:'#f59e0b',opacity:.12,stroke:'#f59e0b',strokeWidth:1},{d:'M32 26a6 6 0 1 1 0 12a6 6 0 1 1 0-12z',fill:'#f59e0b',opacity:.3,stroke:'#d97706',strokeWidth:1.5}]},
  cable_fiber:{viewBox:'0 0 64 64',paths:[{d:'M32 8a24 24 0 1 1 0 48a24 24 0 1 1 0-48z',fill:'#a855f7',opacity:.06,stroke:'#a855f7',strokeWidth:2},{d:'M32 16a16 16 0 1 1 0 32a16 16 0 1 1 0-32z',fill:'none',stroke:'#a855f7',strokeWidth:1,opacity:.4},{d:'M32 28a4 4 0 1 1 0 8a4 4 0 1 1 0-8z',fill:'#c084fc',opacity:.6,stroke:'#a855f7',strokeWidth:1},{d:'M32 18a3 3 0 1 1 0 6a3 3 0 1 1 0-6z',fill:'#c084fc',opacity:.4,stroke:'none'},{d:'M44 24a3 3 0 1 1 0 6a3 3 0 1 1 0-6z',fill:'#c084fc',opacity:.4,stroke:'none'},{d:'M44 36a3 3 0 1 1 0 6a3 3 0 1 1 0-6z',fill:'#c084fc',opacity:.4,stroke:'none'},{d:'M32 42a3 3 0 1 1 0 6a3 3 0 1 1 0-6z',fill:'#c084fc',opacity:.4,stroke:'none'},{d:'M20 36a3 3 0 1 1 0 6a3 3 0 1 1 0-6z',fill:'#c084fc',opacity:.4,stroke:'none'},{d:'M20 24a3 3 0 1 1 0 6a3 3 0 1 1 0-6z',fill:'#c084fc',opacity:.4,stroke:'none'}]},
  attenuator:{viewBox:'0 0 64 64',paths:[{d:'M4 24h56',fill:'none',stroke:'#a855f7',strokeWidth:2.5},{d:'M16 20h32v24H16z',fill:'#a855f7',opacity:.08,stroke:'#a855f7',strokeWidth:2},{d:'M32 24v16',fill:'none',stroke:'#c084fc',strokeWidth:2},{d:'M28 36l4 4 4-4',fill:'none',stroke:'#c084fc',strokeWidth:2},{d:'M16 32a2 2 0 1 1 0-.01',fill:'#c084fc',stroke:'none'},{d:'M48 32a2 2 0 1 1 0-.01',fill:'#c084fc',stroke:'none'}]},
  grounding:{viewBox:'0 0 64 64',paths:[{d:'M20 12h24v28H20z',fill:'none',stroke:'#f59e0b',strokeWidth:2},{d:'M32 40v8',fill:'none',stroke:'#64748b',strokeWidth:2},{d:'M24 48h16M28 52h8M30 56h4',fill:'none',stroke:'#64748b',strokeWidth:2},{d:'M26 20h12v6H26z',fill:'#f59e0b',opacity:.15,stroke:'#f59e0b',strokeWidth:1},{d:'M32 8v4',fill:'none',stroke:'#f59e0b',strokeWidth:2},{d:'M24 30h16',fill:'none',stroke:'#f59e0b',strokeWidth:1,opacity:.3}]},
  switch:{viewBox:'0 0 64 64',paths:[{d:'M4 22h56v20H4z',fill:'none',stroke:'#06b6d4',strokeWidth:2},{d:'M8 26h4v4H8zM14 26h4v4h-4zM20 26h4v4h-4zM26 26h4v4h-4zM32 26h4v4h-4zM38 26h4v4h-4zM44 26h4v4h-4zM50 26h4v4h-4z',fill:'#06b6d4',opacity:.15,stroke:'#0891b2',strokeWidth:.8},{d:'M8 33h4v4H8zM14 33h4v4h-4zM20 33h4v4h-4zM26 33h4v4h-4zM32 33h4v4h-4zM38 33h4v4h-4zM44 33h4v4h-4zM50 33h4v4h-4z',fill:'#06b6d4',opacity:.15,stroke:'#0891b2',strokeWidth:.8},{d:'M9 24a1 1 0 1 1 0-.01M15 24a1 1 0 1 1 0-.01M21 24a1 1 0 1 1 0-.01M27 24a1 1 0 1 1 0-.01M33 24a1 1 0 1 1 0-.01M39 24a1 1 0 1 1 0-.01M45 24a1 1 0 1 1 0-.01M51 24a1 1 0 1 1 0-.01',fill:'#22c55e',stroke:'none',opacity:.6}]},
  connector:{viewBox:'0 0 64 64',paths:[{d:'M6 24h14v16H6z',fill:'#64748b',opacity:.12,stroke:'#94a3b8',strokeWidth:2},{d:'M20 28h4v8h-4z',fill:'#94a3b8',opacity:.2,stroke:'#94a3b8',strokeWidth:1},{d:'M44 24h14v16H44z',fill:'#64748b',opacity:.12,stroke:'#94a3b8',strokeWidth:2},{d:'M40 28h4v8h-4z',fill:'#94a3b8',opacity:.2,stroke:'#94a3b8',strokeWidth:1},{d:'M28 32h8',fill:'none',stroke:'#cbd5e1',strokeWidth:2},{d:'M30 30v4',fill:'none',stroke:'#cbd5e1',strokeWidth:1.5},{d:'M2 28h4M58 28h4M2 36h4M58 36h4',fill:'none',stroke:'#64748b',strokeWidth:1.5}]},
  dc_blocker:{viewBox:'0 0 64 64',paths:[{d:'M4 32h16M44 32h16',fill:'none',stroke:'#f59e0b',strokeWidth:2.5},{d:'M20 20h24v24H20z',fill:'#f59e0b',opacity:.08,stroke:'#f59e0b',strokeWidth:2},{d:'M30 26v12',fill:'none',stroke:'#f59e0b',strokeWidth:2},{d:'M34 26v12',fill:'none',stroke:'#f59e0b',strokeWidth:2},{d:'M27 32h-4M41 32h-4',fill:'none',stroke:'#f59e0b',strokeWidth:1,opacity:.4}]},
  load:{viewBox:'0 0 64 64',paths:[{d:'M8 32h8l4-10 8 20 8-20 8 20 4-10h8',fill:'none',stroke:'#a855f7',strokeWidth:2},{d:'M54 32v14',fill:'none',stroke:'#64748b',strokeWidth:1.5},{d:'M50 46h12M52 50h8M54 54h4',fill:'none',stroke:'#64748b',strokeWidth:1.5,opacity:.5}]},
  cabinet:{viewBox:'0 0 64 64',paths:[{d:'M14 6h36v52H14z',fill:'none',stroke:'#64748b',strokeWidth:2},{d:'M14 6h36v6H14z',fill:'#64748b',opacity:.1,stroke:'none'},{d:'M18 16h28v14H18z',fill:'#64748b',opacity:.06,stroke:'#64748b',strokeWidth:.8},{d:'M18 34h28v14H18z',fill:'#64748b',opacity:.06,stroke:'#64748b',strokeWidth:.8},{d:'M30 16v14M30 34v14',fill:'none',stroke:'#64748b',strokeWidth:.6,opacity:.3},{d:'M44 22a1.5 1.5 0 1 1 0-.01M44 40a1.5 1.5 0 1 1 0-.01',fill:'#22c55e',opacity:.5,stroke:'none'},{d:'M22 56v4h4v-4M38 56v4h4v-4',fill:'none',stroke:'#64748b',strokeWidth:1.5}]},
  psu:{viewBox:'0 0 64 64',paths:[{d:'M10 14h44v36H10z',fill:'#ef4444',opacity:.08,stroke:'#ef4444',strokeWidth:2},{d:'M2 26h8M2 38h8',fill:'none',stroke:'#ef4444',strokeWidth:2},{d:'M54 26h8M54 38h8',fill:'none',stroke:'#f87171',strokeWidth:2},{d:'M36 28h14v8H36z',fill:'#ef4444',opacity:.12,stroke:'none'},{d:'M16 44a2 2 0 1 1 0-.01',fill:'#22c55e',stroke:'none'}]},
  poi:{viewBox:'0 0 64 64',paths:[{d:'M6 8h52v48H6z',fill:'#ef4444',opacity:.06,stroke:'#ef4444',strokeWidth:2},{d:'M10 12h18v12H10zM32 12h22v12H32z',fill:'none',stroke:'#ef4444',strokeWidth:1,opacity:.5},{d:'M10 28h18v12H10zM32 28h22v12H32z',fill:'none',stroke:'#ef4444',strokeWidth:1,opacity:.5},{d:'M16 4v8M24 4v8M40 4v8M48 4v8',fill:'none',stroke:'#f87171',strokeWidth:1.5}]},
  ups:{viewBox:'0 0 64 64',paths:[{d:'M10 12h44v40H10z',fill:'#ef4444',opacity:.06,stroke:'#ef4444',strokeWidth:2},{d:'M16 18h32v16H16z',fill:'var(--bg-canvas,#0f172a)',stroke:'#ef4444',strokeWidth:1},{d:'M26 24h10v4H26z',fill:'#22c55e',opacity:.4,stroke:'none'},{d:'M20 40a3 3 0 1 1 0-.01',fill:'#ef4444',opacity:.3,stroke:'#ef4444',strokeWidth:1}]},
  spd:{viewBox:'0 0 64 64',paths:[{d:'M18 12h28v40H18z',fill:'#ef4444',opacity:.08,stroke:'#ef4444',strokeWidth:2},{d:'M36 16l-8 14h8l-8 14',fill:'none',stroke:'#fbbf24',strokeWidth:2.5},{d:'M32 52v6M26 58h12M28 61h8',fill:'none',stroke:'#64748b',strokeWidth:1.5},{d:'M32 6v6',fill:'none',stroke:'#ef4444',strokeWidth:2}]},
  software:{viewBox:'0 0 64 64',paths:[{d:'M12 10h40v44H12z',fill:'none',stroke:'#06b6d4',strokeWidth:2},{d:'M12 10h40v8H12z',fill:'#06b6d4',opacity:.1,stroke:'none'},{d:'M16 14a1.5 1.5 0 1 1 0-.01',fill:'#ef4444',opacity:.5,stroke:'none'},{d:'M22 14a1.5 1.5 0 1 1 0-.01',fill:'#f59e0b',opacity:.5,stroke:'none'},{d:'M28 14a1.5 1.5 0 1 1 0-.01',fill:'#22c55e',opacity:.5,stroke:'none'},{d:'M20 26l6 4-6 4',fill:'none',stroke:'#06b6d4',strokeWidth:2},{d:'M30 34h14',fill:'none',stroke:'#06b6d4',strokeWidth:1.5,opacity:.4},{d:'M20 42h24',fill:'none',stroke:'#06b6d4',strokeWidth:1,opacity:.2},{d:'M20 46h16',fill:'none',stroke:'#06b6d4',strokeWidth:1,opacity:.2}]},
  license:{viewBox:'0 0 64 64',paths:[{d:'M16 8h28l8 8v40H16z',fill:'none',stroke:'#06b6d4',strokeWidth:2},{d:'M44 8v8h8',fill:'none',stroke:'#06b6d4',strokeWidth:2},{d:'M24 24h20M24 30h16M24 36h12',fill:'none',stroke:'#06b6d4',strokeWidth:1,opacity:.3},{d:'M32 42a6 6 0 1 1 0 12a6 6 0 1 1 0-12z',fill:'#22c55e',opacity:.15,stroke:'#22c55e',strokeWidth:1.5},{d:'M30 48l2 2 4-4',fill:'none',stroke:'#22c55e',strokeWidth:2}]},
  server:{viewBox:'0 0 64 64',paths:[{d:'M6 10h52v44H6z',fill:'none',stroke:'#06b6d4',strokeWidth:2},{d:'M10 14h44v12H10z',fill:'#06b6d4',opacity:.08,stroke:'#06b6d4',strokeWidth:1},{d:'M10 30h44v12H10z',fill:'#06b6d4',opacity:.08,stroke:'#06b6d4',strokeWidth:1},{d:'M14 18h4v4h-4zM20 18h4v4h-4zM26 18h4v4h-4z',fill:'#06b6d4',opacity:.15,stroke:'#0891b2',strokeWidth:.8},{d:'M14 34h4v4h-4zM20 34h4v4h-4zM26 34h4v4h-4z',fill:'#06b6d4',opacity:.15,stroke:'#0891b2',strokeWidth:.8},{d:'M48 18a2 2 0 1 1 0-.01',fill:'#22c55e',stroke:'none'},{d:'M48 34a2 2 0 1 1 0-.01',fill:'#22c55e',stroke:'none'},{d:'M38 18v4M40 18v4M42 18v4M44 18v4',fill:'none',stroke:'#06b6d4',strokeWidth:.6,opacity:.3},{d:'M38 34v4M40 34v4M42 34v4M44 34v4',fill:'none',stroke:'#06b6d4',strokeWidth:.6,opacity:.3},{d:'M10 46h44v4H10z',fill:'#06b6d4',opacity:.06,stroke:'none'}]},
  service:{viewBox:'0 0 64 64',paths:[{d:'M16 12h28l8 8v36H16z',fill:'none',stroke:'#64748b',strokeWidth:2},{d:'M44 12v8h8',fill:'none',stroke:'#64748b',strokeWidth:2},{d:'M24 28h20M24 34h16M24 40h12',fill:'none',stroke:'#64748b',strokeWidth:1,opacity:.3},{d:'M24 22h4v2h-4z',fill:'#64748b',opacity:.3,stroke:'none'},{d:'M30 22h4v2h-4z',fill:'#64748b',opacity:.3,stroke:'none'}]},
  text_note:{viewBox:'0 0 64 64',paths:[{d:'M12 12h40v40H12z',fill:'#475569',opacity:.08,stroke:'#64748b',strokeWidth:1.5,strokeDasharray:'4 2'},{d:'M20 24h24M20 32h20M20 40h16',fill:'none',stroke:'#64748b',strokeWidth:1.5,opacity:.5}]},
  generic:{viewBox:'0 0 64 64',paths:[{d:'M12 12h40v40H12z',fill:'#475569',opacity:.08,stroke:'#64748b',strokeWidth:2},{d:'M32 24v16M24 32h16',fill:'none',stroke:'#64748b',strokeWidth:2,opacity:.5}]},
  riser:{viewBox:'0 0 64 64',paths:[{d:'M32 16a16 16 0 1 1 0 32a16 16 0 1 1 0-32z',fill:'#f59e0b',opacity:.15,stroke:'#f59e0b',strokeWidth:2},{d:'M36 24l-8 10h8l-6 8',fill:'none',stroke:'#f59e0b',strokeWidth:2.5}]},
};

// ⬇ 来自 app/static/cad_symbols/ 的矢量图标（由 scripts/tools/build_device_icons.py 生成）
// 这些图标作为 DAS 系统图专用图标，替换上方 DEFAULT_DEVICE_ICONS 里对应 key 的默认图形。
// 要更新：修改 app/static/cad_symbols/*.svg 后运行 build_device_icons.py，复制输出粘贴到这里。
Object.assign(DEFAULT_DEVICE_ICONS, {
  antenna_exproof: {viewBox:'0 0 64 64', paths:[{d:'M 12.196 46.452 c -0.147 0.624 -0.223 1.260 -0.223 1.909 c 0.000 7.010 8.925 12.695 19.951 12.727 h 7.414 l -17.342 -6.397 L 12.196 46.452 z',fill:'#22c55e',stroke:'none'},{d:'M 52.053 48.359 c 0.000 -7.030 -8.973 -12.727 -20.039 -12.727 c -9.171 0.000 -16.901 3.912 -19.285 9.250 l 9.784 9.013 l 17.158 7.143 l 4.454 -2.536 h -0.006 C 48.941 56.177 52.053 52.499 52.053 48.359 z M 40.273 39.767 l -0.494 -0.232 l -0.119 0.302 l 0.528 0.246 l -0.158 0.217 l -0.463 -0.217 l -0.105 0.271 c -0.008 0.023 -0.025 0.099 0.054 0.136 l 0.528 0.249 l -0.158 0.217 l -0.635 -0.297 c -0.119 -0.056 -0.147 -0.150 -0.153 -0.220 c -0.006 -0.073 0.020 -0.136 0.020 -0.138 l 0.446 -1.155 l 0.870 0.407 L 40.273 39.767 z M 40.631 41.303 l 0.079 -1.630 l 0.339 0.158 v 0.006 l -0.071 1.102 l 0.675 -0.825 l 0.339 0.158 l -1.014 1.192 L 40.631 41.303 z M 42.204 41.702 l 0.486 0.226 l -0.153 0.220 l -0.585 -0.274 c -0.107 -0.054 -0.133 -0.144 -0.136 -0.212 c -0.003 -0.073 0.023 -0.136 0.023 -0.138 l 0.449 -1.158 l 0.799 0.373 l -0.153 0.220 l -0.455 -0.212 l -0.119 0.305 l 0.486 0.226 l -0.153 0.220 l -0.426 -0.201 l -0.105 0.271 C 42.154 41.589 42.134 41.665 42.204 41.702 z M 44.196 41.795 l -0.017 0.042 c -0.068 0.178 -0.220 0.288 -0.378 0.297 l 0.076 0.624 l -0.305 -0.144 l -0.048 -0.559 l -0.020 -0.249 l 0.090 0.042 c 0.119 0.056 0.254 -0.008 0.308 -0.141 c 0.051 -0.133 -0.003 -0.285 -0.119 -0.342 l -0.147 -0.068 l -0.446 1.152 l -0.294 -0.136 l 0.542 -1.398 l 0.294 0.136 l 0.000 0.000 c 0.051 0.023 0.090 0.042 0.093 0.045 l 0.150 0.071 C 44.193 41.267 44.289 41.549 44.196 41.795 z M 44.374 43.038 l 0.443 -1.150 l -0.342 -0.161 l 0.093 -0.246 l 0.977 0.458 l -0.153 0.217 l -0.282 -0.133 l -0.443 1.150 L 44.374 43.038 z M 46.215 44.009 l -0.339 -0.158 v -0.006 l 0.082 -1.127 l -0.683 0.853 l -0.339 -0.158 l 1.011 -1.192 l 0.350 0.164 L 46.215 44.009 z M 47.509 43.283 l -0.314 -0.147 c -0.102 -0.048 -0.226 0.014 -0.274 0.141 l -0.178 0.463 c -0.048 0.127 -0.006 0.268 0.099 0.316 l 0.393 0.184 l -0.153 0.220 l -0.401 -0.189 c -0.217 -0.102 -0.314 -0.404 -0.209 -0.672 l 0.169 -0.438 c 0.105 -0.268 0.367 -0.404 0.585 -0.302 l 0.373 0.175 c 0.006 0.003 0.051 0.025 0.056 0.028 l 0.006 0.003 L 47.509 43.283 z',fill:'#22c55e',stroke:'none'},{d:'M 34.864 5.872 v 29.224 c -0.966 -0.090 -1.954 -0.181 -2.960 -0.181 c -1.005 0.000 -1.994 0.090 -2.963 0.181 V 5.872 c 0.000 -1.638 1.327 -2.963 2.963 -2.963 c 0.819 0.000 1.559 0.330 2.093 0.867 C 34.536 4.313 34.864 5.053 34.864 5.872 z',fill:'#22c55e',stroke:'none'},{d:'M 22.569 24.648 L 22.569 24.648 c -0.404 -0.785 -0.093 -1.748 0.692 -2.152 l 7.767 -3.985 c 0.785 -0.404 1.748 -0.093 2.152 0.692 l 0.000 0.000 c 0.404 0.785 0.093 1.748 -0.692 2.152 l -7.767 3.985 C 23.936 25.744 22.973 25.433 22.569 24.648 z',fill:'#22c55e',stroke:'none'}]},
  antenna_indoor: {viewBox:'0 0 64 64', paths:[{d:'M 3.233 29.233 c -0.214 0.905 -0.324 1.829 -0.324 2.770 c 0.000 10.176 12.954 18.428 28.957 18.473 h 10.764 l -25.173 -9.285 L 3.233 29.233 z',fill:'#22c55e',stroke:'none'},{d:'M 61.085 32.003 c 0.000 -10.203 -13.023 -18.473 -29.088 -18.473 c -13.311 0.000 -24.531 5.676 -27.993 13.423 l 14.201 13.082 l 24.902 10.369 l 6.465 -3.681 h -0.006 C 56.567 43.351 61.085 38.014 61.085 32.003 z M 43.987 19.529 l -0.715 -0.335 l -0.169 0.439 l 0.766 0.359 l -0.232 0.315 l -0.674 -0.315 l -0.151 0.392 c -0.009 0.033 -0.036 0.142 0.077 0.196 l 0.766 0.359 l -0.232 0.315 l -0.923 -0.433 c -0.172 -0.083 -0.214 -0.220 -0.223 -0.318 c -0.006 -0.110 0.027 -0.199 0.030 -0.202 l 0.647 -1.677 l 1.262 0.591 L 43.987 19.529 z M 44.506 21.762 l 0.113 -2.363 l 0.493 0.232 v 0.009 l -0.104 1.597 l 0.980 -1.196 l 0.493 0.232 l -1.469 1.731 L 44.506 21.762 z M 46.795 22.338 l 0.704 0.329 l -0.223 0.318 l -0.849 -0.398 c -0.157 -0.077 -0.193 -0.211 -0.199 -0.309 c -0.003 -0.107 0.030 -0.196 0.033 -0.199 l 0.650 -1.683 l 1.161 0.543 l -0.223 0.318 l -0.659 -0.309 l -0.172 0.442 l 0.704 0.329 l -0.223 0.318 l -0.617 -0.288 l -0.151 0.392 C 46.718 22.177 46.691 22.287 46.795 22.338 z M 49.680 22.477 l -0.024 0.059 c -0.098 0.258 -0.318 0.416 -0.549 0.430 l 0.110 0.908 l -0.442 -0.208 l -0.068 -0.813 l -0.030 -0.359 l 0.131 0.062 c 0.172 0.080 0.371 -0.012 0.445 -0.205 c 0.074 -0.193 -0.003 -0.416 -0.175 -0.496 l -0.211 -0.098 l -0.647 1.671 l -0.424 -0.199 l 0.787 -2.030 l 0.424 0.199 l 0.000 0.000 c 0.074 0.036 0.134 0.062 0.137 0.065 l 0.220 0.101 C 49.674 21.711 49.817 22.118 49.680 22.477 z M 49.938 24.279 l 0.644 -1.668 l -0.499 -0.232 l 0.137 -0.356 l 1.419 0.665 l -0.223 0.315 l -0.413 -0.193 l -0.644 1.668 L 49.938 24.279 z M 52.613 25.689 l -0.493 -0.232 v -0.009 l 0.119 -1.639 l -0.994 1.235 l -0.493 -0.232 l 1.469 -1.731 l 0.508 0.237 L 52.613 25.689 z M 54.489 24.635 l -0.457 -0.214 c -0.148 -0.068 -0.327 0.021 -0.398 0.205 l -0.261 0.674 c -0.071 0.181 -0.006 0.389 0.142 0.457 l 0.570 0.267 l -0.220 0.321 l -0.582 -0.273 c -0.318 -0.148 -0.454 -0.585 -0.303 -0.977 l 0.246 -0.635 c 0.151 -0.389 0.531 -0.585 0.849 -0.436 l 0.540 0.252 c 0.009 0.003 0.074 0.036 0.083 0.042 l 0.009 0.003 L 54.489 24.635 z',fill:'#22c55e',stroke:'none'}]},
  antenna_outdoor: {viewBox:'0 0 64 64', paths:[{d:'M 37.730 57.505 L 34.076 57.505 L 34.076 47.437 a 0.897 0.897 0.000 0 0 -0.897 -0.893 l 0.000 0.000 l 0.000 -2.514 l 4.396 0.000 L 37.575 31.891 l -4.396 0.000 l 0.000 -29.538 a 0.946 0.946 0.000 0 0 -0.949 -0.946 l -1.407 0.000 a 0.946 0.946 0.000 0 0 -0.949 0.946 l 0.000 29.538 l -4.526 0.000 l 0.000 12.139 L 29.857 44.030 l 0.000 2.514 L 29.857 46.544 a 0.893 0.893 0.000 0 0 -0.893 0.893 l 0.000 14.263 a 0.893 0.893 0.000 0 0 0.893 0.893 l 7.887 0.000 a 0.907 0.907 0.000 0 0 0.907 -0.911 l 0.000 -3.270 A 0.904 0.904 0.000 0 0 37.730 57.505 Z m -3.038 -23.747 a 1.245 1.245 0.000 1 1 -1.241 1.245 A 1.245 1.245 0.000 0 1 34.692 33.758 Z m 0.000 5.918 a 1.241 1.241 0.000 1 1 -1.241 1.241 A 1.241 1.241 0.000 0 1 34.692 39.676 Z m -6.488 2.483 a 1.241 1.241 0.000 1 1 1.245 -1.241 A 1.241 1.241 0.000 0 1 28.204 42.159 Z m 0.000 -5.915 a 1.245 1.245 0.000 1 1 1.245 -1.241 A 1.241 1.241 0.000 0 1 28.204 36.244 Z',fill:'#22c55e',stroke:'none'}]},
  antenna_panel: {viewBox:'0 0 64 64', paths:[{d:'M 58.340 56.703 a 102.648 102.648 0.000 0 1 -52.680 0.000 L 5.660 5.820 a 102.555 102.555 0.000 0 0 52.680 0.000 Z',fill:'#22c55e',stroke:'none'},{d:'M 58.340 1.434 l 0.000 3.152 a 102.648 102.648 0.000 0 1 -52.680 0.000 L 5.660 1.434 Z',fill:'#22c55e',stroke:'none'},{d:'M 35.104 62.196 a 13.268 13.268 0.000 0 1 -6.207 0.000 L 28.896 56.703 a 13.350 13.350 0.000 0 0 6.207 0.000 Z',fill:'#22c55e',stroke:'none'}]},
  base_station: {viewBox:'0 0 64 64', paths:[{d:'M 43.694 39.802 L 20.311 39.802 a 0.752 0.752 0.000 0 0 -0.782 0.719 l 0.000 7.877 a 0.755 0.755 0.000 0 0 0.782 0.722 l 23.391 0.000 a 0.752 0.752 0.000 0 0 0.782 -0.722 l 0.000 -7.877 A 0.752 0.752 0.000 0 0 43.694 39.802 Z M 21.887 44.933 l -0.511 0.000 a 0.172 0.172 0.000 0 1 -0.161 -0.088 a 0.202 0.202 0.000 0 1 -0.022 -0.088 l 0.000 -0.796 l 0.700 0.000 l -0.049 0.170 l -0.402 0.000 l 0.000 0.211 l 0.424 0.000 l -0.049 0.167 l -0.375 0.000 l 0.000 0.189 a 0.071 0.071 0.000 0 0 0.074 0.063 L 21.952 44.761 Z m 0.747 0.000 l -0.252 0.000 l -0.347 -0.971 l 0.254 0.000 l 0.219 0.662 l 0.224 -0.665 l 0.249 0.000 Z m 1.190 0.000 L 23.320 44.933 a 0.164 0.164 0.000 0 1 -0.161 -0.088 a 0.202 0.202 0.000 0 1 -0.022 -0.088 l 0.000 -0.796 l 0.697 0.000 l -0.052 0.170 l -0.397 0.000 l 0.000 0.211 l 0.424 0.000 l -0.055 0.170 l -0.369 0.000 l 0.000 0.186 a 0.063 0.063 0.000 0 0 0.071 0.063 L 23.867 44.761 Z m 0.821 0.000 l -0.189 -0.320 l -0.085 -0.139 l 0.079 0.000 a 0.170 0.170 0.000 1 0 0.000 -0.336 l -0.129 0.000 L 24.321 44.933 l -0.249 0.000 l 0.000 -0.976 l 0.462 0.000 a 0.323 0.323 0.000 0 1 0.334 0.312 l 0.000 0.027 a 0.312 0.312 0.000 0 1 -0.191 0.274 l 0.230 0.347 Z m 0.894 0.000 l -0.252 0.000 l 0.000 -0.801 l -0.293 0.000 l 0.000 -0.170 l 0.837 0.000 l -0.052 0.170 l -0.241 0.000 Z m 0.930 0.000 l 0.000 0.000 l -0.222 -0.678 l -0.224 0.681 L 25.782 44.936 l 0.345 -0.966 l 0.274 0.000 l 0.342 0.966 Z m 1.094 0.000 l -0.367 0.000 a 0.347 0.347 0.000 0 1 -0.361 -0.331 l 0.000 -0.301 a 0.347 0.347 0.000 0 1 0.361 -0.331 l 0.397 0.000 l -0.052 0.167 l -0.274 0.000 a 0.161 0.161 0.000 0 0 -0.167 0.156 l 0.000 0.317 a 0.164 0.164 0.000 0 0 0.167 0.156 l 0.358 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 45.220 40.469 L 47.182 40.469 a 0.801 0.801 0.000 0 1 0.801 0.801 l 0.000 6.376 a 0.801 0.801 0.000 0 1 -0.801 0.801 l -1.972 0.000 a 0.000 0.000 0.000 0 1 0.000 0.000 L 45.209 40.469 A 0.000 0.000 0.000 0 1 45.220 40.469 Z',fill:'#64748b',stroke:'none'},{d:'M 18.774 48.437 l -1.972 0.000 a 0.801 0.801 180.000 0 1 -0.801 -0.801 l 0.000 -6.376 a 0.801 0.801 180.000 0 1 0.801 -0.801 l 1.972 0.000 a 0.000 0.000 0.000 0 1 0.000 0.000 L 18.774 48.437 a 0.000 0.000 0.000 0 1 0.000 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 43.694 28.738 L 20.311 28.738 a 0.755 0.755 0.000 0 0 -0.782 0.722 l 0.000 7.877 a 0.755 0.755 0.000 0 0 0.782 0.722 l 23.391 0.000 a 0.752 0.752 0.000 0 0 0.782 -0.722 l 0.000 -7.877 A 0.755 0.755 0.000 0 0 43.694 28.738 Z m -21.807 5.137 l -0.511 0.000 a 0.172 0.172 0.000 0 1 -0.161 -0.085 a 0.202 0.202 0.000 0 1 -0.022 -0.088 L 21.192 32.898 l 0.700 0.000 l -0.049 0.170 l -0.402 0.000 l 0.000 0.211 l 0.424 0.000 l -0.049 0.167 l -0.375 0.000 l 0.000 0.189 a 0.071 0.071 0.000 0 0 0.074 0.063 L 21.952 33.697 Z m 0.747 0.000 l -0.252 0.000 L 22.034 32.898 l 0.254 0.000 l 0.219 0.662 l 0.224 -0.665 l 0.249 0.000 Z m 1.190 0.000 L 23.320 33.875 a 0.161 0.161 0.000 0 1 -0.161 -0.085 a 0.202 0.202 0.000 0 1 -0.022 -0.088 L 23.137 32.898 l 0.697 0.000 l -0.052 0.170 l -0.397 0.000 l 0.000 0.211 l 0.424 0.000 l -0.055 0.170 l -0.369 0.000 l 0.000 0.186 a 0.063 0.063 0.000 0 0 0.071 0.063 L 23.867 33.697 Z m 0.821 0.000 l -0.189 -0.320 l -0.085 -0.139 l 0.079 0.000 a 0.170 0.170 0.000 1 0 0.000 -0.336 l -0.129 0.000 l 0.000 0.801 l -0.249 0.000 L 24.072 32.898 l 0.462 0.000 a 0.323 0.323 0.000 0 1 0.334 0.309 l 0.000 0.030 a 0.306 0.306 0.000 0 1 -0.191 0.274 l 0.230 0.350 Z m 0.894 0.000 l -0.252 0.000 l 0.000 -0.799 l -0.293 0.000 L 24.994 32.898 l 0.837 0.000 l -0.052 0.170 l -0.241 0.000 Z m 0.930 0.000 l 0.000 0.000 l -0.222 -0.678 l -0.224 0.681 L 25.782 33.878 l 0.345 -0.966 l 0.274 0.000 l 0.342 0.966 Z m 1.094 0.000 l -0.367 0.000 a 0.347 0.347 0.000 0 1 -0.361 -0.331 l 0.000 -0.301 a 0.347 0.347 0.000 0 1 0.361 -0.331 l 0.397 0.000 l -0.052 0.167 l -0.274 0.000 a 0.161 0.161 0.000 0 0 -0.167 0.156 l 0.000 0.317 a 0.164 0.164 0.000 0 0 0.167 0.156 l 0.358 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 45.220 29.403 L 47.182 29.403 a 0.801 0.801 0.000 0 1 0.801 0.801 l 0.000 6.376 a 0.801 0.801 0.000 0 1 -0.801 0.801 l -1.972 0.000 a 0.000 0.000 0.000 0 1 0.000 0.000 L 45.209 29.403 A 0.000 0.000 0.000 0 1 45.220 29.403 Z',fill:'#64748b',stroke:'none'},{d:'M 18.774 37.379 l -1.972 0.000 a 0.801 0.801 180.000 0 1 -0.801 -0.801 l 0.000 -6.376 a 0.801 0.801 180.000 0 1 0.801 -0.801 l 1.972 0.000 a 0.000 0.000 0.000 0 1 0.000 0.000 L 18.774 37.379 a 0.000 0.000 0.000 0 1 0.000 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 43.631 50.776 l -23.394 0.000 a 0.752 0.752 0.000 0 0 -0.780 0.719 l 0.000 2.858 a 0.752 0.752 0.000 0 0 0.780 0.719 l 23.394 0.000 a 0.752 0.752 0.000 0 0 0.782 -0.719 L 44.414 51.498 A 0.752 0.752 0.000 0 0 43.631 50.776 Z m -21.807 2.716 l -0.511 0.000 a 0.170 0.170 0.000 0 1 -0.161 -0.088 a 0.183 0.183 0.000 0 1 -0.025 -0.088 l 0.000 -0.796 l 0.700 0.000 l -0.049 0.170 l -0.399 0.000 l 0.000 0.211 l 0.424 0.000 l -0.052 0.167 l -0.372 0.000 l 0.000 0.189 a 0.068 0.068 0.000 0 0 0.071 0.063 l 0.424 0.000 Z m 0.747 0.000 l -0.254 0.000 l -0.347 -0.971 l 0.254 0.000 l 0.222 0.662 l 0.222 -0.665 l 0.252 0.000 Z m 1.190 0.000 l -0.509 0.000 a 0.164 0.164 0.000 0 1 -0.161 -0.088 a 0.202 0.202 0.000 0 1 -0.022 -0.088 l 0.000 -0.796 l 0.695 0.000 l -0.049 0.170 L 23.320 52.690 l 0.000 0.211 l 0.424 0.000 l -0.055 0.170 L 23.320 53.070 l 0.000 0.186 a 0.063 0.063 0.000 0 0 0.068 0.063 l 0.429 0.000 Z m 0.821 0.000 l -0.189 -0.320 l -0.085 -0.139 l 0.077 0.000 a 0.170 0.170 0.000 1 0 0.000 -0.336 l -0.126 0.000 l 0.000 0.804 l -0.252 0.000 l 0.000 -0.976 l 0.462 0.000 a 0.325 0.325 0.000 0 1 0.336 0.312 l 0.000 0.027 a 0.315 0.315 0.000 0 1 -0.194 0.274 l 0.232 0.347 Z m 0.892 0.000 L 25.235 53.492 l 0.000 -0.801 l -0.293 0.000 l 0.000 -0.170 l 0.821 0.000 l -0.049 0.170 l -0.243 0.000 Z m 0.933 0.000 l 0.000 0.000 l -0.224 -0.678 l -0.222 0.681 l -0.252 0.000 l 0.347 -0.966 l 0.257 0.000 l 0.342 0.966 Z m 1.094 0.000 L 27.149 53.492 a 0.347 0.347 0.000 0 1 -0.361 -0.331 L 26.788 52.865 a 0.347 0.347 0.000 0 1 0.361 -0.331 l 0.397 0.000 l -0.055 0.167 l -0.274 0.000 a 0.161 0.161 0.000 0 0 -0.170 0.156 l 0.000 0.317 a 0.164 0.164 0.000 0 0 0.170 0.156 l 0.358 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 45.157 51.180 l 1.972 0.000 a 0.801 0.801 0.000 0 1 0.801 0.801 l 0.000 1.915 a 0.801 0.801 0.000 0 1 -0.801 0.801 l -1.972 0.000 a 0.000 0.000 0.000 0 1 0.000 0.000 L 45.157 51.180 A 0.000 0.000 0.000 0 1 45.157 51.180 Z',fill:'#64748b',stroke:'none'},{d:'M 18.714 54.692 l -1.972 0.000 a 0.801 0.801 180.000 0 1 -0.801 -0.801 l 0.000 -1.915 a 0.801 0.801 180.000 0 1 0.801 -0.801 L 18.714 51.175 a 0.000 0.000 0.000 0 1 0.000 0.000 L 18.714 54.692 A 0.000 0.000 0.000 0 1 18.714 54.692 Z',fill:'#64748b',stroke:'none'},{d:'M 43.743 6.600 l -23.490 0.000 a 0.755 0.755 0.000 0 0 -0.782 0.722 L 19.472 15.229 a 0.755 0.755 0.000 0 0 0.782 0.725 l 23.490 0.000 a 0.755 0.755 0.000 0 0 0.785 -0.725 L 44.528 7.322 A 0.755 0.755 0.000 0 0 43.743 6.600 Z m -20.607 7.095 a 0.129 0.129 0.000 0 1 -0.068 0.109 l -1.950 1.080 a 0.139 0.139 0.000 0 1 -0.208 -0.109 L 20.910 7.779 a 0.137 0.137 0.000 0 1 0.208 -0.107 l 1.950 1.078 a 0.129 0.129 0.000 0 1 0.068 0.109 Z m 12.664 0.339 l -7.601 0.000 L 28.199 8.520 l 7.601 0.000 Z m 7.289 0.741 a 0.139 0.139 0.000 0 1 -0.211 0.109 l -1.950 -1.080 a 0.131 0.131 0.000 0 1 -0.066 -0.109 L 40.863 8.859 a 0.131 0.131 0.000 0 1 0.066 -0.109 l 1.950 -1.078 a 0.139 0.139 0.000 0 1 0.211 0.107 Z',fill:'#64748b',stroke:'none'},{d:'M 47.223 7.273 l -1.947 0.000 l 0.000 8.009 l 1.947 0.000 a 0.821 0.821 0.000 0 0 0.837 -0.774 L 48.059 8.047 A 0.821 0.821 0.000 0 0 47.223 7.273 Z',fill:'#64748b',stroke:'none'},{d:'M 15.935 8.047 l 0.000 6.460 a 0.804 0.804 0.000 0 0 0.821 0.774 l 1.947 0.000 L 18.703 7.273 l -1.947 0.000 A 0.804 0.804 0.000 0 0 15.935 8.047 Z',fill:'#64748b',stroke:'none'},{d:'M 43.743 17.661 l -23.490 0.000 a 0.755 0.755 0.000 0 0 -0.782 0.725 l 0.000 7.907 a 0.755 0.755 0.000 0 0 0.782 0.722 l 23.490 0.000 a 0.755 0.755 0.000 0 0 0.785 -0.722 L 44.528 18.386 A 0.755 0.755 0.000 0 0 43.743 17.661 Z m -20.607 7.095 a 0.129 0.129 0.000 0 1 -0.068 0.109 l -1.950 1.094 a 0.139 0.139 0.000 0 1 -0.208 -0.109 L 20.910 18.840 a 0.137 0.137 0.000 0 1 0.208 -0.107 l 1.950 1.078 a 0.129 0.129 0.000 0 1 0.068 0.109 Z m 12.664 0.339 l -7.601 0.000 L 28.199 19.581 l 7.601 0.000 Z m 7.289 0.741 a 0.139 0.139 0.000 0 1 -0.211 0.109 l -1.950 -1.094 a 0.131 0.131 0.000 0 1 -0.066 -0.109 L 40.863 19.920 a 0.131 0.131 0.000 0 1 0.066 -0.109 l 1.950 -1.078 a 0.139 0.139 0.000 0 1 0.211 0.107 Z',fill:'#64748b',stroke:'none'},{d:'M 47.223 18.337 l -1.947 0.000 L 45.275 26.334 l 1.947 0.000 a 0.821 0.821 0.000 0 0 0.837 -0.771 L 48.059 19.108 A 0.821 0.821 0.000 0 0 47.223 18.337 Z',fill:'#64748b',stroke:'none'},{d:'M 15.935 19.108 l 0.000 6.463 a 0.804 0.804 0.000 0 0 0.821 0.771 l 1.947 0.000 L 18.703 18.337 l -1.947 0.000 A 0.804 0.804 0.000 0 0 15.935 19.108 Z',fill:'#64748b',stroke:'none'},{d:'M 48.380 3.843 a 1.956 1.956 0.000 0 1 1.956 1.953 l 0.000 50.600 a 1.956 1.956 0.000 0 1 -1.956 1.953 L 15.620 58.349 a 1.956 1.956 0.000 0 1 -1.956 -1.953 l 0.000 -50.600 a 1.956 1.956 0.000 0 1 1.956 -1.953 l 32.759 0.000 m 0.000 -2.735 L 15.620 1.108 a 4.688 4.688 0.000 0 0 -4.691 4.688 l 0.000 50.600 A 4.688 4.688 0.000 0 0 15.620 61.071 l 32.759 0.000 a 4.688 4.688 0.000 0 0 4.691 -4.688 l 0.000 -50.600 a 4.688 4.688 0.000 0 0 -4.691 -4.688 Z',fill:'#64748b',stroke:'none'},{d:'M 20.752 58.893 L 22.062 58.893 A 1.351 1.351 0.000 0 1 23.413 60.245 L 23.413 61.555 A 1.351 1.351 0.000 0 1 22.062 62.906 L 20.752 62.906 A 1.351 1.351 0.000 0 1 19.400 61.555 L 19.400 60.245 A 1.351 1.351 0.000 0 1 20.752 58.893 Z',fill:'#64748b',stroke:'none'},{d:'M 41.935 58.893 L 43.246 58.893 A 1.351 1.351 0.000 0 1 44.597 60.245 L 44.597 61.555 A 1.351 1.351 0.000 0 1 43.246 62.906 L 41.935 62.906 A 1.351 1.351 0.000 0 1 40.584 61.555 L 40.584 60.245 A 1.351 1.351 0.000 0 1 41.935 58.893 Z',fill:'#64748b',stroke:'none'}]},
  charging_cabinet: {viewBox:'0 0 64 64', paths:[{d:'M 48.380 3.843 a 1.956 1.956 0.000 0 1 1.956 1.953 l 0.000 50.600 a 1.956 1.956 0.000 0 1 -1.956 1.953 L 15.620 58.349 a 1.956 1.956 0.000 0 1 -1.956 -1.953 l 0.000 -50.600 a 1.956 1.956 0.000 0 1 1.956 -1.953 l 32.759 0.000 m 0.000 -2.735 L 15.620 1.108 a 4.688 4.688 0.000 0 0 -4.691 4.688 l 0.000 50.600 A 4.688 4.688 0.000 0 0 15.620 61.071 l 32.759 0.000 a 4.688 4.688 0.000 0 0 4.691 -4.688 l 0.000 -50.600 a 4.688 4.688 0.000 0 0 -4.691 -4.688 Z',fill:'#64748b',stroke:'none'},{d:'M 20.752 58.893 L 22.062 58.893 A 1.351 1.351 0.000 0 1 23.413 60.245 L 23.413 61.555 A 1.351 1.351 0.000 0 1 22.062 62.906 L 20.752 62.906 A 1.351 1.351 0.000 0 1 19.400 61.555 L 19.400 60.245 A 1.351 1.351 0.000 0 1 20.752 58.893 Z',fill:'#64748b',stroke:'none'},{d:'M 41.935 58.893 L 43.246 58.893 A 1.351 1.351 0.000 0 1 44.597 60.245 L 44.597 61.555 A 1.351 1.351 0.000 0 1 43.246 62.906 L 41.935 62.906 A 1.351 1.351 0.000 0 1 40.584 61.555 L 40.584 60.245 A 1.351 1.351 0.000 0 1 41.935 58.893 Z',fill:'#64748b',stroke:'none'},{d:'M 18.837 17.792 a 0.131 0.131 0.000 0 1 -0.134 0.134 a 0.134 0.134 0.000 0 1 -0.134 -0.134 a 0.131 0.131 0.000 0 1 0.134 -0.134 A 0.131 0.131 0.000 0 1 18.837 17.792 Z',fill:'#64748b',stroke:'none'},{d:'M 19.595 17.792 a 0.134 0.134 0.000 0 1 -0.134 0.134 a 0.131 0.131 0.000 0 1 -0.134 -0.134 a 0.131 0.131 0.000 0 1 0.134 -0.134 A 0.131 0.131 0.000 0 1 19.595 17.792 Z',fill:'#64748b',stroke:'none'},{d:'M 20.350 17.792 a 0.137 0.137 0.000 0 1 -0.274 0.000 a 0.137 0.137 0.000 0 1 0.274 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 24.250 17.658 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 1 0 0.131 -0.134 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 25.008 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 25.762 17.658 Z m 0.000 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 25.762 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 25.008 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 1 0 0.131 -0.134 Z m 0.000 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 1 0 0.131 -0.134 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 25.008 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 25.762 17.658 Z m 3.460 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 29.222 17.658 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 29.980 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 30.735 17.658 Z m 3.556 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 34.282 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 35.037 17.658 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 35.795 17.658 Z m 0.000 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 35.795 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 35.037 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 34.282 17.658 Z m -3.556 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 30.735 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 29.980 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 29.222 17.658 Z m -3.460 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 25.762 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 25.008 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 1 0 0.131 -0.134 Z m 0.000 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 1 0 0.131 -0.134 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 25.008 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 25.762 17.658 Z m 3.460 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 29.222 17.658 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 29.980 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 30.735 17.658 Z m 3.556 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 34.282 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 35.037 17.658 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 35.795 17.658 Z m 2.907 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 38.703 17.658 Z m 0.758 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.131 -0.134 A 0.131 0.131 0.000 0 0 39.457 17.658 Z m 0.755 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 40.215 17.658 Z m 3.580 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 43.795 17.658 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 44.553 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 45.308 17.658 Z m 0.000 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 45.308 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 44.553 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 43.795 17.658 Z m -3.580 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 40.215 17.658 Z m -0.755 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.131 -0.134 A 0.131 0.131 0.000 0 0 39.457 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 38.703 17.658 Z m -2.907 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 35.795 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 35.037 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 34.282 17.658 Z m -3.556 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 30.735 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 29.980 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 29.222 17.658 Z m -3.460 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 25.762 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 25.008 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 1 0 0.131 -0.134 Z m 0.000 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 1 0 0.131 -0.134 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 25.008 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 25.762 17.658 Z m 3.460 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 29.222 17.658 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 29.980 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 30.735 17.658 Z m 3.556 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 34.282 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 35.037 17.658 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 35.795 17.658 Z m 2.907 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 38.703 17.658 Z m 0.758 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.131 -0.134 A 0.131 0.131 0.000 0 0 39.457 17.658 Z m 0.755 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 40.215 17.658 Z m 3.580 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 43.795 17.658 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 44.553 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 45.308 17.658 Z m 0.000 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 45.308 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 44.553 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 43.795 17.658 Z m -3.580 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 40.215 17.658 Z m -0.755 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.131 -0.134 A 0.131 0.131 0.000 0 0 39.457 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 38.703 17.658 Z m -2.907 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 35.795 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 35.037 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 34.282 17.658 Z m -3.556 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 30.735 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 29.980 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 29.222 17.658 Z m -3.460 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 25.762 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 25.008 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 1 0 0.131 -0.134 Z m 0.000 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 1 0 0.131 -0.134 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 25.008 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 25.762 17.658 Z m 3.460 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 29.222 17.658 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 29.980 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 30.735 17.658 Z m 3.556 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 34.282 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 35.037 17.658 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 35.795 17.658 Z m 2.907 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 38.703 17.658 Z m 0.758 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.131 -0.134 A 0.131 0.131 0.000 0 0 39.457 17.658 Z m 0.755 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 40.215 17.658 Z m 3.580 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 43.795 17.658 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 44.553 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 45.308 17.658 Z m 0.000 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 45.308 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 44.553 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 43.795 17.658 Z m -3.580 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 40.215 17.658 Z m -0.755 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.131 -0.134 A 0.131 0.131 0.000 0 0 39.457 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 38.703 17.658 Z m -2.907 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 35.795 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 35.037 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 34.282 17.658 Z m -3.556 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 30.735 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 29.980 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 29.222 17.658 Z m -3.460 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 25.762 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 25.008 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 1 0 0.131 -0.134 Z m 0.000 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 1 0 0.131 -0.134 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 25.008 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 25.762 17.658 Z m 3.460 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 29.222 17.658 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 29.980 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 30.735 17.658 Z m 3.556 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 34.282 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 35.037 17.658 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 35.795 17.658 Z m 2.907 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 38.703 17.658 Z m 0.758 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.131 -0.134 A 0.131 0.131 0.000 0 0 39.457 17.658 Z m 0.755 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 40.215 17.658 Z m 3.580 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 43.795 17.658 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 44.553 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 45.308 17.658 Z m 0.000 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 45.308 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 44.553 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 43.795 17.658 Z m -3.580 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 40.215 17.658 Z m -0.755 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.131 -0.134 A 0.131 0.131 0.000 0 0 39.457 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 38.703 17.658 Z m -2.907 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 35.795 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 35.037 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 34.282 17.658 Z m -3.556 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 30.735 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 29.980 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 29.222 17.658 Z m -3.460 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 25.762 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 25.008 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 1 0 0.131 -0.134 Z m 23.375 -4.579 L 16.373 13.080 a 0.971 0.971 0.000 0 0 -0.968 0.971 l 0.000 3.512 a 0.968 0.968 0.000 0 0 0.968 0.966 l 31.252 0.000 a 0.968 0.968 0.000 0 0 0.971 -0.966 L 48.596 14.051 A 0.971 0.971 0.000 0 0 47.625 13.080 Z M 24.715 15.393 a 0.274 0.274 0.000 0 1 0.274 -0.274 l 0.301 0.000 l -0.038 0.134 l -0.216 0.000 a 0.129 0.129 0.000 0 0 -0.129 0.129 L 24.906 15.667 a 0.129 0.129 0.000 0 0 0.129 0.126 l 0.274 0.000 l -0.038 0.137 l -0.274 0.000 a 0.274 0.274 0.000 0 1 -0.274 -0.274 Z m -0.347 -0.274 l 0.274 0.780 l -0.191 0.000 l -0.167 -0.547 l -0.167 0.547 l -0.189 0.000 l 0.257 -0.780 Z m -3.753 2.968 a 0.129 0.129 0.000 0 1 -0.129 0.129 l -2.054 0.000 a 0.129 0.129 0.000 0 1 -0.129 -0.129 l 0.000 -0.618 a 0.129 0.129 0.000 0 1 0.129 -0.131 l 2.054 0.000 a 0.129 0.129 0.000 0 1 0.129 0.131 Z m 0.358 -2.188 L 20.585 15.899 a 0.126 0.126 0.000 0 1 -0.120 -0.068 a 0.159 0.159 0.000 0 1 -0.019 -0.071 l 0.000 -0.643 l 0.528 0.000 l -0.038 0.137 l -0.301 0.000 l 0.000 0.170 l 0.320 0.000 l -0.038 0.137 l -0.274 0.000 l 0.000 0.150 a 0.055 0.055 0.000 0 0 0.057 0.052 l 0.320 0.000 Z m 0.566 0.000 l -0.194 0.000 l -0.274 -0.782 l 0.191 0.000 l 0.167 0.547 l 0.167 -0.547 l 0.189 0.000 Z m 0.897 0.000 l -0.386 0.000 a 0.123 0.123 0.000 0 1 -0.120 -0.068 a 0.172 0.172 0.000 0 1 -0.016 -0.071 l 0.000 -0.643 l 0.525 0.000 l -0.038 0.137 l -0.298 0.000 l 0.000 0.170 l 0.317 0.000 l -0.036 0.137 l -0.274 0.000 l 0.000 0.150 a 0.049 0.049 0.000 0 0 0.052 0.052 l 0.323 0.000 Z m 0.624 0.000 l -0.208 -0.369 l 0.057 0.000 a 0.137 0.137 0.000 0 0 0.000 -0.274 l -0.093 0.000 l 0.000 0.645 l -0.191 0.000 L 22.625 15.120 l 0.350 0.000 a 0.252 0.252 0.000 0 1 0.252 0.249 L 23.227 15.393 a 0.252 0.252 0.000 0 1 -0.145 0.227 l 0.175 0.274 Z m 0.673 0.000 l -0.189 0.000 l 0.000 -0.645 L 23.320 15.254 l 0.000 -0.137 l 0.632 0.000 l -0.038 0.137 l -0.183 0.000 Z m 2.432 2.188 a 0.131 0.131 0.000 0 1 -0.131 0.129 l -2.051 0.000 a 0.129 0.129 0.000 0 1 -0.131 -0.129 l 0.000 -0.618 a 0.129 0.129 0.000 0 1 0.131 -0.131 l 2.051 0.000 a 0.131 0.131 0.000 0 1 0.131 0.131 Z m 4.973 0.000 a 0.131 0.131 0.000 0 1 -0.131 0.129 l -2.051 0.000 a 0.129 0.129 0.000 0 1 -0.131 -0.129 l 0.000 -0.618 a 0.129 0.129 0.000 0 1 0.131 -0.131 l 2.051 0.000 a 0.131 0.131 0.000 0 1 0.131 0.131 Z m 5.057 0.000 a 0.129 0.129 0.000 0 1 -0.129 0.129 l -2.054 0.000 a 0.129 0.129 0.000 0 1 -0.129 -0.129 l 0.000 -0.618 a 0.129 0.129 0.000 0 1 0.129 -0.131 l 2.054 0.000 a 0.129 0.129 0.000 0 1 0.129 0.131 Z m 4.420 0.000 a 0.129 0.129 0.000 0 1 -0.129 0.129 l -2.054 0.000 a 0.129 0.129 0.000 0 1 -0.129 -0.129 l 0.000 -0.618 a 0.129 0.129 0.000 0 1 0.129 -0.131 l 2.054 0.000 a 0.129 0.129 0.000 0 1 0.129 0.131 Z m 5.096 0.000 a 0.131 0.131 0.000 0 1 -0.131 0.129 l -2.054 0.000 a 0.129 0.129 0.000 0 1 -0.129 -0.129 l 0.000 -0.618 a 0.129 0.129 0.000 0 1 0.129 -0.131 l 2.054 0.000 a 0.131 0.131 0.000 0 1 0.131 0.131 Z m -0.402 -0.443 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 45.308 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 44.553 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 43.795 17.658 Z m -3.580 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 40.215 17.658 Z m -0.755 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.131 -0.134 A 0.131 0.131 0.000 0 0 39.457 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 38.703 17.658 Z m -2.907 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 35.795 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 35.037 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 34.282 17.658 Z m -3.556 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 30.735 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 29.980 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 29.222 17.658 Z m -3.460 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 25.762 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 25.008 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 1 0 0.131 -0.134 Z m 0.000 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 1 0 0.131 -0.134 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 25.008 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 25.762 17.658 Z m 3.460 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 29.222 17.658 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 29.980 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 30.735 17.658 Z m 3.556 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 34.282 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 35.037 17.658 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 35.795 17.658 Z m 2.907 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 38.703 17.658 Z m 0.758 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.131 -0.134 A 0.131 0.131 0.000 0 0 39.457 17.658 Z m 0.755 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 40.215 17.658 Z m 3.580 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 43.795 17.658 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 44.553 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 45.308 17.658 Z m 0.000 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 45.308 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 44.553 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 43.795 17.658 Z m -3.580 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 40.215 17.658 Z m -0.755 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.131 -0.134 A 0.131 0.131 0.000 0 0 39.457 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 38.703 17.658 Z m -2.907 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 35.795 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 35.037 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 34.282 17.658 Z m -3.556 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 30.735 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 29.980 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 29.222 17.658 Z m -3.460 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 25.762 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 25.008 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 1 0 0.131 -0.134 Z m 0.000 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 1 0 0.131 -0.134 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 25.008 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 25.762 17.658 Z m 3.460 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 29.222 17.658 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 29.980 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 30.735 17.658 Z m 3.556 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 34.282 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 35.037 17.658 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 35.795 17.658 Z m 2.907 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 38.703 17.658 Z m 0.758 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.131 -0.134 A 0.131 0.131 0.000 0 0 39.457 17.658 Z m 0.755 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 40.215 17.658 Z m 3.580 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 43.795 17.658 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 44.553 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 45.308 17.658 Z m 0.000 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 45.308 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 44.553 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 43.795 17.658 Z m -3.580 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 40.215 17.658 Z m -0.755 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.131 -0.134 A 0.131 0.131 0.000 0 0 39.457 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 38.703 17.658 Z m -2.907 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 35.795 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 35.037 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 34.282 17.658 Z m -3.556 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 30.735 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 29.980 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 29.222 17.658 Z m -3.460 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 25.762 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 25.008 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 1 0 0.131 -0.134 Z m 0.000 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 1 0 0.131 -0.134 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 25.008 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 25.762 17.658 Z m 3.460 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 29.222 17.658 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 29.980 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 30.735 17.658 Z m 3.556 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 34.282 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 35.037 17.658 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 35.795 17.658 Z m 2.907 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 38.703 17.658 Z m 0.758 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.131 -0.134 A 0.131 0.131 0.000 0 0 39.457 17.658 Z m 0.755 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 40.215 17.658 Z m 3.580 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 43.795 17.658 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 44.553 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 45.308 17.658 Z m 0.000 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 45.308 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 44.553 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 43.795 17.658 Z m -3.580 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 40.215 17.658 Z m -0.755 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.131 -0.134 A 0.131 0.131 0.000 0 0 39.457 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 38.703 17.658 Z m -2.907 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 35.795 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 35.037 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 34.282 17.658 Z m -3.556 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 30.735 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 29.980 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 29.222 17.658 Z m -3.460 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 25.762 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 25.008 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 1 0 0.131 -0.134 Z m 0.000 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 1 0 0.131 -0.134 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 25.008 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 25.762 17.658 Z m 3.460 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 29.222 17.658 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 29.980 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 30.735 17.658 Z m 3.556 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 34.282 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 35.037 17.658 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 35.795 17.658 Z m 2.907 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 38.703 17.658 Z m 0.758 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.131 -0.134 A 0.131 0.131 0.000 0 0 39.457 17.658 Z m 0.755 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 40.215 17.658 Z m 0.000 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 40.215 17.658 Z m -0.755 0.000 a 0.134 0.134 0.000 0 0 -0.137 0.134 a 0.137 0.137 0.000 0 0 0.137 0.134 a 0.134 0.134 0.000 0 0 0.131 -0.134 A 0.131 0.131 0.000 0 0 39.457 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 38.703 17.658 Z m -2.907 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 35.795 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 35.037 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 34.282 17.658 Z m -3.556 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 30.735 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 29.980 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 29.222 17.658 Z m -3.460 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 25.762 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 25.008 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 1 0 0.131 -0.134 Z m 0.000 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 1 0 0.131 -0.134 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 25.008 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 25.762 17.658 Z m 3.460 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 29.222 17.658 Z m 0.758 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 29.980 17.658 Z m 0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 30.735 17.658 Z m 0.000 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 30.735 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 29.980 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 0 0 0.131 0.134 a 0.137 0.137 0.000 0 0 0.137 -0.134 A 0.134 0.134 0.000 0 0 29.222 17.658 Z m -3.460 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.131 0.131 0.000 0 0 0.131 0.134 a 0.134 0.134 0.000 0 0 0.134 -0.134 A 0.131 0.131 0.000 0 0 25.762 17.658 Z m -0.755 0.000 a 0.131 0.131 0.000 0 0 -0.134 0.134 a 0.137 0.137 0.000 0 0 0.274 0.000 A 0.131 0.131 0.000 0 0 25.008 17.658 Z m -0.758 0.000 a 0.131 0.131 0.000 0 0 -0.131 0.134 a 0.134 0.134 0.000 1 0 0.131 -0.134 Z',fill:'#64748b',stroke:'none'},{d:'M 18.837 17.792 a 0.131 0.131 0.000 0 1 -0.134 0.134 a 0.134 0.134 0.000 0 1 -0.134 -0.134 a 0.131 0.131 0.000 0 1 0.134 -0.134 A 0.131 0.131 0.000 0 1 18.837 17.792 Z',fill:'#64748b',stroke:'none'},{d:'M 19.595 17.792 a 0.134 0.134 0.000 0 1 -0.134 0.134 a 0.131 0.131 0.000 0 1 -0.134 -0.134 a 0.131 0.131 0.000 0 1 0.134 -0.134 A 0.131 0.131 0.000 0 1 19.595 17.792 Z',fill:'#64748b',stroke:'none'},{d:'M 20.350 17.792 a 0.137 0.137 0.000 0 1 -0.274 0.000 a 0.137 0.137 0.000 0 1 0.274 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 18.837 17.792 a 0.131 0.131 0.000 0 1 -0.134 0.134 a 0.134 0.134 0.000 0 1 -0.134 -0.134 a 0.131 0.131 0.000 0 1 0.134 -0.134 A 0.131 0.131 0.000 0 1 18.837 17.792 Z',fill:'#64748b',stroke:'none'},{d:'M 19.595 17.792 a 0.134 0.134 0.000 0 1 -0.134 0.134 a 0.131 0.131 0.000 0 1 -0.134 -0.134 a 0.131 0.131 0.000 0 1 0.134 -0.134 A 0.131 0.131 0.000 0 1 19.595 17.792 Z',fill:'#64748b',stroke:'none'},{d:'M 20.350 17.792 a 0.137 0.137 0.000 0 1 -0.274 0.000 a 0.137 0.137 0.000 0 1 0.274 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 24.387 17.792 a 0.137 0.137 0.000 0 1 -0.274 0.000 a 0.137 0.137 0.000 0 1 0.274 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 25.142 17.792 a 0.137 0.137 0.000 0 1 -0.274 0.000 a 0.137 0.137 0.000 0 1 0.274 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 25.896 17.792 a 0.134 0.134 0.000 0 1 -0.134 0.134 a 0.131 0.131 0.000 0 1 -0.131 -0.134 a 0.131 0.131 0.000 0 1 0.131 -0.134 A 0.131 0.131 0.000 0 1 25.896 17.792 Z',fill:'#64748b',stroke:'none'},{d:'M 24.387 17.792 a 0.137 0.137 0.000 0 1 -0.274 0.000 a 0.137 0.137 0.000 0 1 0.274 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 25.142 17.792 a 0.137 0.137 0.000 0 1 -0.274 0.000 a 0.137 0.137 0.000 0 1 0.274 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 25.896 17.792 a 0.134 0.134 0.000 0 1 -0.134 0.134 a 0.131 0.131 0.000 0 1 -0.131 -0.134 a 0.131 0.131 0.000 0 1 0.131 -0.134 A 0.131 0.131 0.000 0 1 25.896 17.792 Z',fill:'#64748b',stroke:'none'},{d:'M 29.359 17.792 a 0.137 0.137 0.000 0 1 -0.137 0.134 a 0.134 0.134 0.000 0 1 -0.131 -0.134 a 0.131 0.131 0.000 0 1 0.131 -0.134 A 0.134 0.134 0.000 0 1 29.359 17.792 Z',fill:'#64748b',stroke:'none'},{d:'M 30.114 17.792 a 0.137 0.137 0.000 0 1 -0.274 0.000 a 0.137 0.137 0.000 0 1 0.274 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 30.869 17.792 a 0.137 0.137 0.000 0 1 -0.274 0.000 a 0.137 0.137 0.000 0 1 0.274 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 29.359 17.792 a 0.137 0.137 0.000 0 1 -0.137 0.134 a 0.134 0.134 0.000 0 1 -0.131 -0.134 a 0.131 0.131 0.000 0 1 0.131 -0.134 A 0.134 0.134 0.000 0 1 29.359 17.792 Z',fill:'#64748b',stroke:'none'},{d:'M 30.114 17.792 a 0.137 0.137 0.000 0 1 -0.274 0.000 a 0.137 0.137 0.000 0 1 0.274 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 30.869 17.792 a 0.137 0.137 0.000 0 1 -0.274 0.000 a 0.137 0.137 0.000 0 1 0.274 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 34.417 17.792 a 0.137 0.137 0.000 0 1 -0.274 0.000 a 0.137 0.137 0.000 0 1 0.274 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 35.174 17.792 a 0.137 0.137 0.000 0 1 -0.137 0.134 a 0.131 0.131 0.000 0 1 -0.131 -0.134 a 0.131 0.131 0.000 0 1 0.131 -0.134 A 0.134 0.134 0.000 0 1 35.174 17.792 Z',fill:'#64748b',stroke:'none'},{d:'M 35.929 17.792 a 0.137 0.137 0.000 0 1 -0.274 0.000 a 0.137 0.137 0.000 0 1 0.274 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 34.417 17.792 a 0.137 0.137 0.000 0 1 -0.274 0.000 a 0.137 0.137 0.000 0 1 0.274 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 35.174 17.792 a 0.137 0.137 0.000 0 1 -0.137 0.134 a 0.131 0.131 0.000 0 1 -0.131 -0.134 a 0.131 0.131 0.000 0 1 0.131 -0.134 A 0.134 0.134 0.000 0 1 35.174 17.792 Z',fill:'#64748b',stroke:'none'},{d:'M 35.929 17.792 a 0.137 0.137 0.000 0 1 -0.274 0.000 a 0.137 0.137 0.000 0 1 0.274 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 38.837 17.792 a 0.137 0.137 0.000 0 1 -0.274 0.000 a 0.137 0.137 0.000 0 1 0.274 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 39.591 17.792 a 0.134 0.134 0.000 0 1 -0.131 0.134 a 0.137 0.137 0.000 0 1 -0.137 -0.134 a 0.134 0.134 0.000 0 1 0.137 -0.134 A 0.131 0.131 0.000 0 1 39.591 17.792 Z',fill:'#64748b',stroke:'none'},{d:'M 40.349 17.792 a 0.134 0.134 0.000 0 1 -0.134 0.134 a 0.137 0.137 0.000 0 1 -0.137 -0.134 a 0.134 0.134 0.000 0 1 0.137 -0.134 A 0.131 0.131 0.000 0 1 40.349 17.792 Z',fill:'#64748b',stroke:'none'},{d:'M 38.837 17.792 a 0.137 0.137 0.000 0 1 -0.274 0.000 a 0.137 0.137 0.000 0 1 0.274 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 39.591 17.792 a 0.134 0.134 0.000 0 1 -0.131 0.134 a 0.137 0.137 0.000 0 1 -0.137 -0.134 a 0.134 0.134 0.000 0 1 0.137 -0.134 A 0.131 0.131 0.000 0 1 39.591 17.792 Z',fill:'#64748b',stroke:'none'},{d:'M 40.349 17.792 a 0.134 0.134 0.000 0 1 -0.134 0.134 a 0.137 0.137 0.000 0 1 -0.137 -0.134 a 0.134 0.134 0.000 0 1 0.137 -0.134 A 0.131 0.131 0.000 0 1 40.349 17.792 Z',fill:'#64748b',stroke:'none'},{d:'M 43.929 17.792 a 0.134 0.134 0.000 0 1 -0.134 0.134 a 0.131 0.131 0.000 0 1 -0.131 -0.134 a 0.131 0.131 0.000 0 1 0.131 -0.134 A 0.131 0.131 0.000 0 1 43.929 17.792 Z',fill:'#64748b',stroke:'none'},{d:'M 44.687 17.792 a 0.137 0.137 0.000 0 1 -0.274 0.000 a 0.137 0.137 0.000 0 1 0.274 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 45.442 17.792 a 0.137 0.137 0.000 0 1 -0.274 0.000 a 0.137 0.137 0.000 0 1 0.274 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 43.929 17.792 a 0.134 0.134 0.000 0 1 -0.134 0.134 a 0.131 0.131 0.000 0 1 -0.131 -0.134 a 0.131 0.131 0.000 0 1 0.131 -0.134 A 0.131 0.131 0.000 0 1 43.929 17.792 Z',fill:'#64748b',stroke:'none'},{d:'M 44.687 17.792 a 0.137 0.137 0.000 0 1 -0.274 0.000 a 0.137 0.137 0.000 0 1 0.274 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 45.442 17.792 a 0.137 0.137 0.000 0 1 -0.274 0.000 a 0.137 0.137 0.000 0 1 0.274 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 20.858 9.187 l 0.000 0.232 l -0.462 0.000 c -0.074 0.000 -0.137 0.044 -0.137 0.098 l 0.000 0.153 l -0.101 0.000 l 0.000 0.495 l 0.101 0.000 L 20.259 12.932 l 1.094 0.000 L 21.353 10.117 l 0.096 -0.109 l 0.000 -0.821 Z m -0.052 2.563 l 0.000 -0.531 l -0.356 0.000 l 0.356 -0.711 l 0.000 0.547 l 0.356 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 26.017 9.187 l 0.000 0.232 l -0.460 0.000 c -0.077 0.000 -0.139 0.044 -0.139 0.098 l 0.000 0.153 l -0.098 0.000 l 0.000 0.495 l 0.098 0.000 L 25.418 12.932 l 1.094 0.000 L 26.512 10.117 l 0.096 -0.109 l 0.000 -0.821 Z m -0.052 2.563 l 0.000 -0.531 l -0.353 0.000 l 0.353 -0.711 l 0.000 0.547 l 0.356 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 31.189 9.187 l 0.000 0.232 l -0.462 0.000 c -0.077 0.000 -0.139 0.044 -0.139 0.098 l 0.000 0.153 l -0.101 0.000 l 0.000 0.495 l 0.101 0.000 L 30.587 12.932 l 1.094 0.000 L 31.681 10.117 l 0.093 -0.109 l 0.000 -0.821 Z m -0.052 2.563 l 0.000 -0.531 l -0.356 0.000 l 0.356 -0.711 l 0.000 0.547 l 0.353 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 18.837 34.455 a 0.131 0.131 0.000 0 1 -0.134 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.131 0.131 0.000 0 1 18.837 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 19.595 34.455 a 0.134 0.134 0.000 0 1 -0.134 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.134 0.134 0.000 0 1 19.595 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 20.350 34.455 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 20.350 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 24.250 34.321 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 34.321 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 34.321 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.000 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 34.321 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 34.321 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 34.321 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 34.321 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 34.321 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 34.321 Z m 3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 34.321 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 34.321 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 34.321 Z m -3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 34.321 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 34.321 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 34.321 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 34.321 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 34.321 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 34.321 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 34.321 Z m 3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 34.321 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 34.321 Z m 2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 34.321 Z m 0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 34.321 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 34.321 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 34.321 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 34.321 Z m -2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 34.321 Z m -3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 34.321 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 34.321 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 34.321 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 34.321 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 34.321 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 34.321 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 34.321 Z m 3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 34.321 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 34.321 Z m 2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 34.321 Z m 0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 34.321 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 34.321 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 34.321 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 34.321 Z m -2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 34.321 Z m -3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 34.321 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 34.321 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 34.321 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 34.321 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 34.321 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 34.321 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 34.321 Z m 3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 34.321 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 34.321 Z m 2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 34.321 Z m 0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 34.321 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 34.321 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 34.321 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 34.321 Z m -2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 34.321 Z m -3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 34.321 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 34.321 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 34.321 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 34.321 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 34.321 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 34.321 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 34.321 Z m 3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 34.321 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 34.321 Z m 2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 34.321 Z m 0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 34.321 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 34.321 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 34.321 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 34.321 Z m -2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 34.321 Z m -3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 34.321 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 34.321 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 34.321 Z m 23.375 -4.579 L 16.373 29.742 a 0.971 0.971 0.000 0 0 -0.968 0.971 l 0.000 3.512 a 0.971 0.971 0.000 0 0 0.968 0.968 l 31.252 0.000 a 0.971 0.971 0.000 0 0 0.971 -0.968 L 48.596 30.710 A 0.971 0.971 0.000 0 0 47.625 29.742 Z M 24.715 32.078 a 0.274 0.274 0.000 0 1 0.274 -0.274 l 0.301 0.000 l -0.038 0.134 l -0.216 0.000 a 0.129 0.129 0.000 0 0 -0.129 0.129 l 0.000 0.254 a 0.126 0.126 0.000 0 0 0.129 0.126 l 0.274 0.000 l -0.038 0.137 l -0.274 0.000 a 0.274 0.274 0.000 0 1 -0.274 -0.274 Z m -0.347 -0.274 l 0.274 0.780 l -0.191 0.000 l -0.167 -0.547 l -0.167 0.547 l -0.189 0.000 l 0.257 -0.780 Z m -3.753 2.968 a 0.129 0.129 0.000 0 1 -0.129 0.129 l -2.054 0.000 a 0.129 0.129 0.000 0 1 -0.129 -0.129 l 0.000 -0.618 a 0.129 0.129 0.000 0 1 0.129 -0.131 l 2.054 0.000 a 0.129 0.129 0.000 0 1 0.129 0.131 Z m 0.358 -2.188 L 20.585 32.584 a 0.126 0.126 0.000 0 1 -0.120 -0.068 a 0.159 0.159 0.000 0 1 -0.019 -0.071 L 20.445 31.804 l 0.528 0.000 l -0.038 0.137 l -0.301 0.000 l 0.000 0.170 l 0.320 0.000 l -0.038 0.137 l -0.274 0.000 l 0.000 0.150 a 0.055 0.055 0.000 0 0 0.057 0.052 l 0.320 0.000 Z m 0.566 0.000 l -0.194 0.000 l -0.274 -0.782 l 0.191 0.000 l 0.167 0.533 l 0.167 -0.547 l 0.189 0.000 Z m 0.897 0.000 l -0.386 0.000 a 0.123 0.123 0.000 0 1 -0.120 -0.068 a 0.172 0.172 0.000 0 1 -0.016 -0.071 L 21.914 31.804 l 0.525 0.000 l -0.038 0.137 l -0.298 0.000 l 0.000 0.170 l 0.317 0.000 l -0.036 0.139 l -0.274 0.000 l 0.000 0.148 a 0.049 0.049 0.000 0 0 0.052 0.052 l 0.323 0.000 Z m 0.624 0.000 l -0.208 -0.372 l 0.057 0.000 a 0.137 0.137 0.000 0 0 0.000 -0.274 l -0.093 0.000 l 0.000 0.645 l -0.191 0.000 L 22.625 31.804 l 0.350 0.000 a 0.252 0.252 0.000 0 1 0.252 0.249 L 23.227 32.078 a 0.252 0.252 0.000 0 1 -0.145 0.227 l 0.175 0.274 Z m 0.673 0.000 l -0.189 0.000 l 0.000 -0.645 L 23.320 31.938 L 23.320 31.804 l 0.632 0.000 l -0.038 0.137 l -0.183 0.000 Z m 2.432 2.188 a 0.131 0.131 0.000 0 1 -0.131 0.129 l -2.051 0.000 a 0.129 0.129 0.000 0 1 -0.131 -0.129 l 0.000 -0.618 a 0.129 0.129 0.000 0 1 0.131 -0.131 l 2.051 0.000 a 0.131 0.131 0.000 0 1 0.131 0.131 Z m 4.973 0.000 a 0.131 0.131 0.000 0 1 -0.131 0.129 l -2.051 0.000 a 0.129 0.129 0.000 0 1 -0.131 -0.129 l 0.000 -0.618 a 0.129 0.129 0.000 0 1 0.131 -0.131 l 2.051 0.000 a 0.131 0.131 0.000 0 1 0.131 0.131 Z m 5.057 0.000 a 0.129 0.129 0.000 0 1 -0.129 0.129 l -2.054 0.000 a 0.129 0.129 0.000 0 1 -0.129 -0.129 l 0.000 -0.618 a 0.129 0.129 0.000 0 1 0.129 -0.131 l 2.054 0.000 a 0.129 0.129 0.000 0 1 0.129 0.131 Z m 4.420 0.000 a 0.129 0.129 0.000 0 1 -0.129 0.129 l -2.054 0.000 a 0.129 0.129 0.000 0 1 -0.129 -0.129 l 0.000 -0.618 a 0.129 0.129 0.000 0 1 0.129 -0.131 l 2.054 0.000 a 0.129 0.129 0.000 0 1 0.129 0.131 Z m 5.096 0.000 a 0.131 0.131 0.000 0 1 -0.131 0.129 l -2.054 0.000 a 0.129 0.129 0.000 0 1 -0.129 -0.129 l 0.000 -0.618 a 0.129 0.129 0.000 0 1 0.129 -0.131 l 2.054 0.000 a 0.131 0.131 0.000 0 1 0.131 0.131 Z m -0.402 -0.443 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 34.321 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 34.321 Z m -2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 34.321 Z m -3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 34.321 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 34.321 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 34.321 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 34.321 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 34.321 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 34.321 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 34.321 Z m 3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 34.321 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 34.321 Z m 2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 34.321 Z m 0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 34.321 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 34.321 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 34.321 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 34.321 Z m -2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 34.321 Z m -3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 34.321 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 34.321 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 34.321 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 34.321 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 34.321 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 34.321 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 34.321 Z m 3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 34.321 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 34.321 Z m 2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 34.321 Z m 0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 34.321 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 34.321 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 34.321 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 34.321 Z m -2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 34.321 Z m -3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 34.321 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 34.321 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 34.321 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 34.321 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 34.321 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 34.321 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 34.321 Z m 3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 34.321 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 34.321 Z m 2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 34.321 Z m 0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 34.321 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 34.321 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 34.321 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 34.321 Z m -2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 34.321 Z m -3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 34.321 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 34.321 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 34.321 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 34.321 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 34.321 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 34.321 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 34.321 Z m 3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 34.321 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 34.321 Z m 2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 34.321 Z m 0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.000 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 34.321 Z m -2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 34.321 Z m -3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 34.321 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 34.321 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 34.321 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 34.321 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 34.321 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 34.321 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 34.321 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 34.321 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 34.321 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 34.321 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 34.321 Z',fill:'#64748b',stroke:'none'},{d:'M 18.837 34.455 a 0.131 0.131 0.000 0 1 -0.134 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.131 0.131 0.000 0 1 18.837 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 19.595 34.455 a 0.134 0.134 0.000 0 1 -0.134 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.134 0.134 0.000 0 1 19.595 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 20.350 34.455 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 20.350 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 18.837 34.455 a 0.131 0.131 0.000 0 1 -0.134 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.131 0.131 0.000 0 1 18.837 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 19.595 34.455 a 0.134 0.134 0.000 0 1 -0.134 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.134 0.134 0.000 0 1 19.595 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 20.350 34.455 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 20.350 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 24.387 34.455 a 0.134 0.134 0.000 1 1 -0.137 -0.134 A 0.134 0.134 0.000 0 1 24.387 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 25.142 34.455 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 25.142 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 25.896 34.455 a 0.134 0.134 0.000 0 1 -0.134 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.134 0.134 0.000 0 1 25.896 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 24.387 34.455 a 0.134 0.134 0.000 1 1 -0.137 -0.134 A 0.134 0.134 0.000 0 1 24.387 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 25.142 34.455 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 25.142 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 25.896 34.455 a 0.134 0.134 0.000 0 1 -0.134 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.134 0.134 0.000 0 1 25.896 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 29.359 34.455 a 0.137 0.137 0.000 0 1 -0.137 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.137 0.137 0.000 0 1 29.359 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 30.114 34.455 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 30.114 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 30.869 34.455 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 30.869 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 29.359 34.455 a 0.137 0.137 0.000 0 1 -0.137 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.137 0.137 0.000 0 1 29.359 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 30.114 34.455 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 30.114 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 30.869 34.455 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 30.869 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 34.417 34.455 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 34.417 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 35.174 34.455 a 0.137 0.137 0.000 0 1 -0.137 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.137 0.137 0.000 0 1 35.174 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 35.929 34.455 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 35.929 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 34.417 34.455 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 34.417 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 35.174 34.455 a 0.137 0.137 0.000 0 1 -0.137 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.137 0.137 0.000 0 1 35.174 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 35.929 34.455 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 35.929 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 38.837 34.455 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 38.837 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 39.591 34.455 a 0.134 0.134 0.000 0 1 -0.131 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.134 0.134 0.000 0 1 39.591 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 40.349 34.455 a 0.134 0.134 0.000 0 1 -0.134 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.134 0.134 0.000 0 1 40.349 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 38.837 34.455 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 38.837 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 39.591 34.455 a 0.134 0.134 0.000 0 1 -0.131 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.134 0.134 0.000 0 1 39.591 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 40.349 34.455 a 0.134 0.134 0.000 0 1 -0.134 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.134 0.134 0.000 0 1 40.349 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 43.929 34.455 a 0.134 0.134 0.000 0 1 -0.134 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.134 0.134 0.000 0 1 43.929 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 44.687 34.455 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 44.687 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 45.442 34.455 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 45.442 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 43.929 34.455 a 0.134 0.134 0.000 0 1 -0.134 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.134 0.134 0.000 0 1 43.929 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 44.687 34.455 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 44.687 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 45.442 34.455 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 45.442 34.455 Z',fill:'#64748b',stroke:'none'},{d:'M 20.858 25.850 l 0.000 0.232 l -0.462 0.000 c -0.074 0.000 -0.137 0.044 -0.137 0.098 L 20.259 26.334 l -0.101 0.000 l 0.000 0.495 l 0.101 0.000 l 0.000 2.763 l 1.094 0.000 L 21.353 26.783 l 0.096 -0.112 l 0.000 -0.821 Z m -0.052 2.563 l 0.000 -0.531 l -0.356 0.000 l 0.356 -0.711 l 0.000 0.547 l 0.356 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 26.017 25.850 l 0.000 0.232 l -0.460 0.000 c -0.077 0.000 -0.139 0.044 -0.139 0.098 L 25.418 26.334 l -0.098 0.000 l 0.000 0.495 l 0.098 0.000 l 0.000 2.763 l 1.094 0.000 L 26.512 26.783 l 0.096 -0.112 l 0.000 -0.821 Z m -0.052 2.563 l 0.000 -0.531 l -0.353 0.000 l 0.353 -0.711 l 0.000 0.547 l 0.356 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 31.189 25.850 l 0.000 0.232 l -0.462 0.000 c -0.077 0.000 -0.139 0.044 -0.139 0.098 L 30.587 26.334 l -0.101 0.000 l 0.000 0.495 l 0.101 0.000 l 0.000 2.763 l 1.094 0.000 L 31.681 26.783 l 0.093 -0.112 l 0.000 -0.821 Z m -0.052 2.563 l 0.000 -0.531 l -0.356 0.000 l 0.356 -0.711 l 0.000 0.547 l 0.353 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 18.837 51.117 a 0.131 0.131 0.000 0 1 -0.134 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.131 0.131 0.000 0 1 18.837 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 19.595 51.117 a 0.134 0.134 0.000 0 1 -0.134 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.134 0.134 0.000 0 1 19.595 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 20.350 51.117 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 20.350 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 24.250 50.983 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 50.983 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 50.983 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.000 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 50.983 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 50.983 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 50.983 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 50.983 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 50.983 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 50.983 Z m 3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 50.983 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 50.983 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 50.983 Z m -3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 50.983 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 50.983 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 50.983 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 50.983 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 50.983 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 50.983 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 50.983 Z m 3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 50.983 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 50.983 Z m 2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 50.983 Z m 0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 50.983 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 50.983 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 50.983 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 50.983 Z m -2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 50.983 Z m -3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 50.983 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 50.983 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 50.983 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 50.983 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 50.983 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 50.983 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 50.983 Z m 3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 50.983 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 50.983 Z m 2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 50.983 Z m 0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 50.983 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 50.983 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 50.983 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 50.983 Z m -2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 50.983 Z m -3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 50.983 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 50.983 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 50.983 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 50.983 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 50.983 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 50.983 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 50.983 Z m 3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 50.983 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 50.983 Z m 2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 50.983 Z m 0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 50.983 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 50.983 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 50.983 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 50.983 Z m -2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 50.983 Z m -3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 50.983 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 50.983 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 50.983 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 50.983 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 50.983 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 50.983 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 50.983 Z m 3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 50.983 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 50.983 Z m 2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 50.983 Z m 0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 50.983 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 50.983 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 50.983 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 50.983 Z m -2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 50.983 Z m -3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 50.983 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 50.983 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 50.983 Z m 23.375 -4.579 L 16.373 46.405 a 0.971 0.971 0.000 0 0 -0.968 0.971 l 0.000 3.512 a 0.971 0.971 0.000 0 0 0.968 0.968 l 31.252 0.000 a 0.971 0.971 0.000 0 0 0.971 -0.968 L 48.596 47.376 A 0.971 0.971 0.000 0 0 47.625 46.405 Z m -22.910 2.325 a 0.274 0.274 0.000 0 1 0.274 -0.274 l 0.301 0.000 l -0.038 0.134 l -0.216 0.000 a 0.129 0.129 0.000 0 0 -0.129 0.129 l 0.000 0.254 a 0.126 0.126 0.000 0 0 0.129 0.126 l 0.274 0.000 l -0.038 0.137 l -0.274 0.000 a 0.274 0.274 0.000 0 1 -0.274 -0.274 Z m -0.347 -0.274 l 0.274 0.780 l -0.191 0.000 l -0.167 -0.547 l -0.167 0.547 l -0.189 0.000 l 0.257 -0.780 Z m -3.753 2.968 a 0.131 0.131 0.000 0 1 -0.129 0.131 l -2.054 0.000 a 0.131 0.131 0.000 0 1 -0.129 -0.131 l 0.000 -0.618 a 0.129 0.129 0.000 0 1 0.129 -0.131 l 2.054 0.000 a 0.129 0.129 0.000 0 1 0.129 0.131 Z m 0.358 -2.188 L 20.585 49.236 a 0.126 0.126 0.000 0 1 -0.120 -0.068 a 0.159 0.159 0.000 0 1 -0.019 -0.071 l 0.000 -0.643 l 0.528 0.000 l -0.038 0.137 l -0.301 0.000 L 20.634 48.762 l 0.320 0.000 l -0.038 0.137 l -0.274 0.000 l 0.000 0.150 a 0.057 0.057 0.000 0 0 0.057 0.055 l 0.320 0.000 Z m 0.566 0.000 l -0.194 0.000 l -0.274 -0.782 l 0.191 0.000 l 0.167 0.547 l 0.167 -0.547 l 0.189 0.000 Z m 0.897 0.000 l -0.386 0.000 a 0.123 0.123 0.000 0 1 -0.120 -0.068 a 0.172 0.172 0.000 0 1 -0.016 -0.071 l 0.000 -0.643 l 0.525 0.000 l -0.038 0.137 l -0.298 0.000 L 22.103 48.762 l 0.317 0.000 l -0.036 0.139 l -0.274 0.000 l 0.000 0.148 a 0.052 0.052 0.000 0 0 0.052 0.055 l 0.323 0.000 Z m 0.624 0.000 l -0.208 -0.372 l 0.057 0.000 a 0.137 0.137 0.000 0 0 0.000 -0.274 l -0.093 0.000 l 0.000 0.645 l -0.191 0.000 l 0.000 -0.785 l 0.350 0.000 a 0.252 0.252 0.000 0 1 0.252 0.249 l 0.000 0.025 a 0.252 0.252 0.000 0 1 -0.145 0.227 l 0.175 0.274 Z m 0.673 0.000 l -0.189 0.000 l 0.000 -0.645 L 23.320 48.590 l 0.000 -0.137 l 0.632 0.000 l -0.038 0.137 l -0.183 0.000 Z m 2.432 2.188 a 0.134 0.134 0.000 0 1 -0.131 0.131 l -2.051 0.000 a 0.131 0.131 0.000 0 1 -0.131 -0.131 l 0.000 -0.618 a 0.129 0.129 0.000 0 1 0.131 -0.131 l 2.051 0.000 a 0.131 0.131 0.000 0 1 0.131 0.131 Z m 4.973 0.000 a 0.134 0.134 0.000 0 1 -0.131 0.131 l -2.051 0.000 a 0.131 0.131 0.000 0 1 -0.131 -0.131 l 0.000 -0.618 a 0.129 0.129 0.000 0 1 0.131 -0.131 l 2.051 0.000 a 0.131 0.131 0.000 0 1 0.131 0.131 Z m 5.057 0.000 a 0.131 0.131 0.000 0 1 -0.129 0.131 l -2.054 0.000 a 0.131 0.131 0.000 0 1 -0.129 -0.131 l 0.000 -0.618 a 0.129 0.129 0.000 0 1 0.129 -0.131 l 2.054 0.000 a 0.129 0.129 0.000 0 1 0.129 0.131 Z m 4.420 0.000 a 0.131 0.131 0.000 0 1 -0.129 0.131 l -2.054 0.000 a 0.131 0.131 0.000 0 1 -0.129 -0.131 l 0.000 -0.618 a 0.129 0.129 0.000 0 1 0.129 -0.131 l 2.054 0.000 a 0.129 0.129 0.000 0 1 0.129 0.131 Z m 5.096 0.000 a 0.134 0.134 0.000 0 1 -0.131 0.131 l -2.054 0.000 a 0.131 0.131 0.000 0 1 -0.129 -0.131 l 0.000 -0.618 a 0.129 0.129 0.000 0 1 0.129 -0.131 l 2.054 0.000 a 0.131 0.131 0.000 0 1 0.131 0.131 Z m -0.402 -0.443 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 50.983 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 50.983 Z m -2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 50.983 Z m -3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 50.983 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 50.983 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 50.983 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 50.983 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 50.983 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 50.983 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 50.983 Z m 3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 50.983 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 50.983 Z m 2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 50.983 Z m 0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 50.983 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 50.983 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 50.983 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 50.983 Z m -2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 50.983 Z m -3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 50.983 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 50.983 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 50.983 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 50.983 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 50.983 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 50.983 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 50.983 Z m 3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 50.983 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 50.983 Z m 2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 50.983 Z m 0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 50.983 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 50.983 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 50.983 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 50.983 Z m -2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 50.983 Z m -3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 50.983 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 50.983 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 50.983 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 50.983 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 50.983 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 50.983 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 50.983 Z m 3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 50.983 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 50.983 Z m 2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 50.983 Z m 0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 50.983 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 50.983 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 45.308 50.983 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 44.553 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.580 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 50.983 Z m -2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 50.983 Z m -3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 50.983 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 50.983 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 50.983 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 50.983 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 50.983 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 50.983 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 50.983 Z m 3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 50.983 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 50.983 Z m 2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 50.983 Z m 0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.000 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 38.703 50.983 Z m -2.907 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 35.795 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 34.282 50.983 Z m -3.556 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 50.983 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 50.983 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 50.983 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 50.983 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 50.983 Z m 0.755 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m 0.758 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 50.983 Z m 0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 50.983 Z m 0.000 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 30.735 50.983 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 29.980 50.983 Z m -0.758 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -3.460 0.000 a 0.137 0.137 0.000 0 0 0.000 0.274 a 0.137 0.137 0.000 0 0 0.000 -0.274 Z m -0.755 0.000 a 0.134 0.134 0.000 1 0 0.134 0.134 A 0.134 0.134 0.000 0 0 25.008 50.983 Z m -0.758 0.000 a 0.134 0.134 0.000 1 0 0.137 0.134 A 0.134 0.134 0.000 0 0 24.250 50.983 Z',fill:'#64748b',stroke:'none'},{d:'M 18.837 51.117 a 0.131 0.131 0.000 0 1 -0.134 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.131 0.131 0.000 0 1 18.837 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 19.595 51.117 a 0.134 0.134 0.000 0 1 -0.134 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.134 0.134 0.000 0 1 19.595 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 20.350 51.117 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 20.350 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 18.837 51.117 a 0.131 0.131 0.000 0 1 -0.134 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.131 0.131 0.000 0 1 18.837 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 19.595 51.117 a 0.134 0.134 0.000 0 1 -0.134 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.134 0.134 0.000 0 1 19.595 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 20.350 51.117 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 20.350 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 24.387 51.117 a 0.134 0.134 0.000 1 1 -0.137 -0.134 A 0.134 0.134 0.000 0 1 24.387 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 25.142 51.117 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 25.142 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 25.896 51.117 a 0.134 0.134 0.000 0 1 -0.134 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.134 0.134 0.000 0 1 25.896 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 24.387 51.117 a 0.134 0.134 0.000 1 1 -0.137 -0.134 A 0.134 0.134 0.000 0 1 24.387 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 25.142 51.117 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 25.142 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 25.896 51.117 a 0.134 0.134 0.000 0 1 -0.134 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.134 0.134 0.000 0 1 25.896 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 29.359 51.117 a 0.137 0.137 0.000 0 1 -0.137 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.137 0.137 0.000 0 1 29.359 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 30.114 51.117 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 30.114 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 30.869 51.117 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 30.869 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 29.359 51.117 a 0.137 0.137 0.000 0 1 -0.137 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.137 0.137 0.000 0 1 29.359 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 30.114 51.117 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 30.114 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 30.869 51.117 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 30.869 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 34.417 51.117 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 34.417 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 35.174 51.117 a 0.137 0.137 0.000 0 1 -0.137 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.137 0.137 0.000 0 1 35.174 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 35.929 51.117 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 35.929 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 34.417 51.117 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 34.417 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 35.174 51.117 a 0.137 0.137 0.000 0 1 -0.137 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.137 0.137 0.000 0 1 35.174 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 35.929 51.117 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 35.929 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 38.837 51.117 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 38.837 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 39.591 51.117 a 0.134 0.134 0.000 0 1 -0.131 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.134 0.134 0.000 0 1 39.591 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 40.349 51.117 a 0.134 0.134 0.000 0 1 -0.134 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.134 0.134 0.000 0 1 40.349 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 38.837 51.117 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 38.837 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 39.591 51.117 a 0.134 0.134 0.000 0 1 -0.131 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.134 0.134 0.000 0 1 39.591 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 40.349 51.117 a 0.134 0.134 0.000 0 1 -0.134 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.134 0.134 0.000 0 1 40.349 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 43.929 51.117 a 0.134 0.134 0.000 0 1 -0.134 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.134 0.134 0.000 0 1 43.929 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 44.687 51.117 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 44.687 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 45.442 51.117 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 45.442 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 43.929 51.117 a 0.134 0.134 0.000 0 1 -0.134 0.134 a 0.137 0.137 0.000 0 1 0.000 -0.274 A 0.134 0.134 0.000 0 1 43.929 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 44.687 51.117 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 44.687 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 45.442 51.117 a 0.134 0.134 0.000 1 1 -0.134 -0.134 A 0.134 0.134 0.000 0 1 45.442 51.117 Z',fill:'#64748b',stroke:'none'},{d:'M 20.858 42.513 L 20.858 42.745 l -0.462 0.000 c -0.074 0.000 -0.137 0.044 -0.137 0.098 l 0.000 0.153 l -0.101 0.000 l 0.000 0.498 l 0.101 0.000 l 0.000 2.760 l 1.094 0.000 L 21.353 43.445 l 0.096 -0.112 l 0.000 -0.821 Z m -0.052 2.563 l 0.000 -0.531 l -0.356 0.000 l 0.356 -0.711 l 0.000 0.533 l 0.356 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 26.017 42.513 L 26.017 42.745 l -0.460 0.000 c -0.077 0.000 -0.139 0.044 -0.139 0.098 l 0.000 0.153 l -0.098 0.000 l 0.000 0.498 l 0.098 0.000 l 0.000 2.760 l 1.094 0.000 L 26.512 43.445 l 0.096 -0.112 l 0.000 -0.821 Z m -0.052 2.563 l 0.000 -0.531 l -0.353 0.000 l 0.353 -0.711 l 0.000 0.533 l 0.356 0.000 Z',fill:'#64748b',stroke:'none'},{d:'M 31.189 42.513 L 31.189 42.745 l -0.462 0.000 c -0.077 0.000 -0.139 0.044 -0.139 0.098 l 0.000 0.153 l -0.101 0.000 l 0.000 0.498 l 0.101 0.000 l 0.000 2.760 l 1.094 0.000 L 31.681 43.445 l 0.093 -0.112 l 0.000 -0.821 Z m -0.052 2.563 l 0.000 -0.531 l -0.356 0.000 l 0.356 -0.711 l 0.000 0.533 l 0.353 0.000 Z',fill:'#64748b',stroke:'none'}]},
  combiner: {viewBox:'0 0 64 64', paths:[{d:'M 51.375 23.111 H 12.594 c -0.384 0.000 -0.694 -0.310 -0.694 -0.694 l 0.000 0.000 c 0.000 -0.384 0.310 -0.694 0.694 -0.694 h 38.781 c 0.384 0.000 0.694 0.310 0.694 0.694 l 0.000 0.000 C 52.071 22.800 51.758 23.111 51.375 23.111 z',fill:'#3b82f6',stroke:'none'},{d:'M 53.253 23.917 H 10.715 c -0.783 0.000 -1.422 0.637 -1.422 1.422 v 15.508 c 0.000 0.783 0.637 1.422 1.422 1.422 h 42.538 c 0.791 0.000 1.422 -0.637 1.422 -1.422 v -15.508 C 54.675 24.556 54.044 23.917 53.253 23.917 z M 13.598 34.032 h -0.931 c -0.167 0.000 -0.253 -0.091 -0.295 -0.167 c -0.042 -0.083 -0.042 -0.167 -0.042 -0.175 v -1.568 h 1.273 l -0.091 0.337 H 12.784 v 0.412 h 0.770 l -0.091 0.329 H 12.784 v 0.370 c 0.008 0.029 0.021 0.125 0.133 0.125 h 0.770 L 13.598 34.032 z M 14.955 34.032 h -0.462 l -0.629 -1.910 h 0.462 v 0.008 l 0.399 1.302 l 0.407 -1.310 h 0.454 L 14.955 34.032 z M 17.118 34.032 h -0.924 c -0.175 0.000 -0.258 -0.091 -0.295 -0.167 c -0.042 -0.083 -0.042 -0.167 -0.042 -0.175 v -1.568 h 1.268 l -0.091 0.337 h -0.720 v 0.412 h 0.770 l -0.099 0.337 h -0.673 v 0.363 c 0.000 0.029 0.013 0.125 0.125 0.125 h 0.777 L 17.118 34.032 z M 18.616 34.017 l -0.342 -0.629 l -0.154 -0.274 h 0.141 c 0.183 0.000 0.329 -0.146 0.329 -0.337 c 0.000 -0.183 -0.146 -0.329 -0.329 -0.329 h -0.232 v 1.581 h -0.454 v -1.918 h 0.454 c 0.083 0.000 0.146 0.000 0.146 0.000 h 0.237 c 0.337 0.000 0.608 0.274 0.608 0.608 v 0.055 c 0.000 0.245 -0.141 0.454 -0.350 0.553 l 0.420 0.686 L 18.616 34.017 L 18.616 34.017 z M 20.241 34.032 h -0.454 v -1.576 h -0.532 v -0.337 h 1.518 l -0.091 0.337 h -0.441 V 34.032 z M 21.934 34.025 v -0.008 l -0.407 -1.336 l -0.407 1.344 h -0.454 l 0.629 -1.905 h 0.470 l 0.624 1.905 H 21.934 z M 23.922 34.025 h -0.665 c -0.363 0.000 -0.657 -0.295 -0.657 -0.650 v -0.595 c 0.000 -0.357 0.295 -0.650 0.657 -0.650 h 0.720 l -0.099 0.329 h -0.519 c -0.167 0.000 -0.308 0.133 -0.308 0.308 v 0.624 c 0.000 0.167 0.141 0.308 0.308 0.308 h 0.650 L 23.922 34.025 z',fill:'#3b82f6',stroke:'none'},{d:'M 59.559 40.933 h -3.527 v -15.701 h 3.527 c 0.835 0.000 1.513 0.678 1.513 1.513 v 12.675 C 61.073 40.258 60.394 40.933 59.559 40.933 z',fill:'#3b82f6',stroke:'none'},{d:'M 4.412 40.923 h 3.527 v -15.701 h -3.527 c -0.835 0.000 -1.513 0.678 -1.513 1.513 v 12.675 C 2.896 40.245 3.574 40.923 4.412 40.923 z',fill:'#3b82f6',stroke:'none'}]},
  coupler: {viewBox:'0 0 64 64', paths:[{d:'M 52.230 25.040 H 11.702 c -0.938 0.000 -1.694 0.762 -1.694 1.700 v 17.572 c 0.000 0.938 0.759 1.700 1.694 1.700 h 40.525 c 0.938 0.000 1.700 -0.762 1.700 -1.700 v -17.572 C 53.927 25.799 53.165 25.040 52.230 25.040 z M 30.437 40.100 c 0.000 0.423 -0.313 0.783 -0.729 0.836 l -14.390 1.887 c -0.506 0.065 -0.950 -0.324 -0.950 -0.836 v -12.928 c 0.000 -0.509 0.444 -0.899 0.950 -0.836 l 14.390 1.887 c 0.417 0.054 0.729 0.411 0.729 0.833 V 40.100 z M 47.181 35.739 l -7.049 3.783 c -0.211 0.113 -0.432 -0.137 -0.295 -0.333 l 2.554 -3.519 c 0.057 -0.077 0.057 -0.185 0.000 -0.265 l -2.554 -3.548 c -0.143 -0.196 0.077 -0.449 0.289 -0.333 l 7.055 3.816 C 47.342 35.426 47.342 35.652 47.181 35.739 z',fill:'#3b82f6',stroke:'none'},{d:'M 8.609 41.276 h -4.278 c -0.786 0.000 -1.426 -0.637 -1.426 -1.426 v -8.656 c 0.000 -0.786 0.637 -1.426 1.426 -1.426 h 4.278 C 8.609 29.767 8.609 41.276 8.609 41.276 z',fill:'#3b82f6',stroke:'none'},{d:'M 55.394 29.770 h 4.278 c 0.786 0.000 1.426 0.637 1.426 1.426 v 8.656 c 0.000 0.786 -0.637 1.426 -1.426 1.426 h -4.278 V 29.770 z',fill:'#3b82f6',stroke:'none'},{d:'M 14.369 23.698 v -4.278 c 0.000 -0.786 0.637 -1.426 1.426 -1.426 h 8.656 c 0.786 0.000 1.426 0.637 1.426 1.426 v 4.278 C 25.877 23.698 14.369 23.698 14.369 23.698 z',fill:'#3b82f6',stroke:'none'}]},
  mark1000: {viewBox:'0 0 64 64', paths:[{d:'M 12.604 23.048 h 38.782 c 0.384 0.000 0.695 -0.311 0.695 -0.695 s -0.311 -0.695 -0.695 -0.695 h -38.782 c -0.384 0.000 -0.695 0.311 -0.695 0.695 S 12.220 23.048 12.604 23.048 z',fill:'#06b6d4',stroke:'none'},{d:'M 53.268 23.971 h -42.546 c -0.779 0.000 -1.420 0.635 -1.420 1.420 v 15.508 c 0.000 0.787 0.641 1.420 1.420 1.420 h 42.546 c 0.787 0.000 1.420 -0.635 1.420 -1.420 v -15.508 C 54.690 24.607 54.055 23.971 53.268 23.971 z M 15.940 37.890 c 0.000 0.084 -0.047 0.170 -0.120 0.212 l -3.532 2.123 c -0.170 0.097 -0.382 -0.024 -0.382 -0.217 v -13.718 c 0.000 -0.193 0.212 -0.314 0.382 -0.212 l 3.532 2.115 c 0.073 0.042 0.120 0.128 0.120 0.212 V 37.890 z M 38.878 38.554 h -13.767 v -10.816 h 13.767 V 38.554 z M 52.084 40.005 c 0.000 0.193 -0.212 0.314 -0.382 0.217 l -3.532 -2.123 c -0.073 -0.042 -0.120 -0.128 -0.120 -0.212 v -9.485 c 0.000 -0.084 0.047 -0.170 0.120 -0.212 l 3.532 -2.115 c 0.170 -0.102 0.382 0.018 0.382 0.212 V 40.005 z',fill:'#06b6d4',stroke:'none'},{d:'M 59.571 25.297 h -3.529 v 15.702 h 3.529 c 0.837 0.000 1.514 -0.677 1.514 -1.514 V 26.810 C 61.085 25.974 60.408 25.297 59.571 25.297 z',fill:'#06b6d4',stroke:'none'},{d:'M 2.907 26.810 v 12.675 c 0.000 0.837 0.677 1.514 1.514 1.514 h 3.529 v -15.702 h -3.529 C 3.584 25.297 2.907 25.974 2.907 26.810 z',fill:'#06b6d4',stroke:'none'},{d:'M 28.460 32.588 h -0.492 v -2.635 h 0.784 l 0.264 1.224 c 0.042 0.201 0.071 0.405 0.092 0.609 h 0.008 c 0.024 -0.259 0.042 -0.437 0.078 -0.609 l 0.264 -1.224 h 0.776 v 2.635 h -0.492 v -0.829 c 0.000 -0.523 0.010 -1.048 0.042 -1.571 h -0.008 l -0.528 2.400 h -0.298 l -0.518 -2.400 h -0.018 c 0.031 0.523 0.042 1.048 0.042 1.571 v 0.829 H 28.460 z',fill:'#06b6d4',stroke:'none'},{d:'M 30.410 32.588 l 0.630 -2.635 h 0.664 l 0.599 2.635 h -0.528 l -0.131 -0.667 h -0.578 l -0.131 0.667 H 30.410 z M 31.145 31.535 h 0.421 l -0.133 -0.748 c -0.024 -0.123 -0.034 -0.243 -0.050 -0.366 c -0.003 -0.060 -0.010 -0.120 -0.018 -0.175 h -0.008 c -0.008 0.055 -0.013 0.115 -0.018 0.175 c -0.013 0.123 -0.024 0.243 -0.050 0.366 L 31.145 31.535 z',fill:'#06b6d4',stroke:'none'},{d:'M 32.970 31.454 v 1.135 h -0.492 v -2.635 h 0.931 c 0.426 0.000 0.748 0.146 0.748 0.633 c 0.000 0.288 -0.073 0.591 -0.405 0.635 v 0.008 c 0.293 0.039 0.379 0.225 0.379 0.478 c 0.000 0.110 -0.013 0.756 0.105 0.834 v 0.050 h -0.541 c -0.060 -0.170 -0.050 -0.492 -0.052 -0.667 c -0.003 -0.162 0.000 -0.384 -0.170 -0.431 c -0.133 -0.039 -0.277 -0.034 -0.418 -0.034 h -0.084 V 31.454 z M 32.970 31.067 h 0.387 c 0.162 -0.010 0.288 -0.115 0.288 -0.379 c 0.000 -0.295 -0.123 -0.345 -0.308 -0.348 h -0.366 V 31.067 L 32.970 31.067 z',fill:'#06b6d4',stroke:'none'},{d:'M 34.541 32.588 v -2.635 h 0.492 v 1.171 h 0.008 c 0.078 -0.207 0.204 -0.439 0.308 -0.633 l 0.288 -0.539 h 0.554 l -0.651 1.132 l 0.682 1.503 h -0.554 l -0.463 -1.041 l -0.173 0.285 v 0.756 H 34.541 z',fill:'#06b6d4',stroke:'none'},{d:'M 29.362 34.421 h -0.593 v -0.350 c 0.340 -0.003 0.625 -0.094 0.724 -0.458 h 0.361 v 2.635 h -0.492 V 34.421 z',fill:'#06b6d4',stroke:'none'},{d:'M 30.452 34.358 c 0.000 -0.559 0.267 -0.756 0.714 -0.756 c 0.442 0.000 0.711 0.196 0.711 0.756 v 1.184 c 0.000 0.559 -0.267 0.758 -0.714 0.758 c -0.442 0.000 -0.708 -0.201 -0.708 -0.758 v -1.184 H 30.452 z M 30.944 35.542 c -0.013 0.295 0.089 0.371 0.214 0.371 c 0.131 0.000 0.238 -0.078 0.225 -0.371 v -1.184 c 0.013 -0.293 -0.094 -0.369 -0.225 -0.369 c -0.125 0.000 -0.227 0.078 -0.214 0.369 V 35.542 z',fill:'#06b6d4',stroke:'none'},{d:'M 32.120 34.358 c 0.000 -0.559 0.267 -0.756 0.714 -0.756 c 0.442 0.000 0.711 0.196 0.711 0.756 v 1.184 c 0.000 0.559 -0.267 0.758 -0.714 0.758 c -0.442 0.000 -0.708 -0.201 -0.708 -0.758 v -1.184 H 32.120 z M 32.612 35.542 c -0.013 0.295 0.089 0.371 0.214 0.371 c 0.131 0.000 0.238 -0.078 0.225 -0.371 v -1.184 c 0.013 -0.293 -0.094 -0.369 -0.225 -0.369 c -0.125 0.000 -0.227 0.078 -0.214 0.369 V 35.542 z',fill:'#06b6d4',stroke:'none'},{d:'M 33.788 34.358 c 0.000 -0.559 0.267 -0.756 0.714 -0.756 c 0.442 0.000 0.711 0.196 0.711 0.756 v 1.184 c 0.000 0.559 -0.267 0.758 -0.714 0.758 c -0.442 0.000 -0.708 -0.201 -0.708 -0.758 v -1.184 H 33.788 z M 34.280 35.542 c -0.013 0.295 0.089 0.371 0.214 0.371 c 0.131 0.000 0.238 -0.078 0.225 -0.371 v -1.184 c 0.013 -0.293 -0.094 -0.369 -0.225 -0.369 c -0.125 0.000 -0.227 0.078 -0.214 0.369 V 35.542 z',fill:'#06b6d4',stroke:'none'}]},
  multi_charger: {viewBox:'0 0 64 64', paths:[{d:'M 7.617 39.291 a 0.247 0.247 0.000 0 1 -0.247 0.250 a 0.250 0.250 0.000 0 1 -0.250 -0.250 a 0.247 0.247 0.000 0 1 0.250 -0.247 A 0.247 0.247 0.000 0 1 7.617 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 9.020 39.291 a 0.250 0.250 0.000 0 1 -0.250 0.250 a 0.247 0.247 0.000 0 1 -0.247 -0.250 a 0.247 0.247 0.000 0 1 0.247 -0.247 A 0.247 0.247 0.000 0 1 9.020 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 10.419 39.291 a 0.247 0.247 0.000 0 1 -0.247 0.250 a 0.250 0.250 0.000 0 1 -0.250 -0.250 a 0.247 0.247 0.000 0 1 0.250 -0.247 A 0.247 0.247 0.000 0 1 10.419 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 17.649 39.044 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 19.051 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 20.451 39.044 Z m 0.000 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 20.451 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 19.051 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 0.000 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 19.051 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 20.451 39.044 Z m 6.412 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 28.265 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 29.664 39.044 Z m 6.574 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 36.238 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 37.637 39.044 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 39.040 39.044 Z m 0.000 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 39.040 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 37.637 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 36.238 39.044 Z m -6.574 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 29.664 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 28.265 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m -6.412 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 20.451 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 19.051 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 0.000 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 19.051 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 20.451 39.044 Z m 6.412 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 28.265 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 29.664 39.044 Z m 6.574 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 36.238 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 37.637 39.044 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 39.040 39.044 Z m 5.387 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 44.427 39.044 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.497 0.000 A 0.247 0.247 0.000 0 0 45.833 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.500 0.000 A 0.247 0.247 0.000 0 0 47.229 39.044 Z m 6.637 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 53.865 39.044 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 55.268 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 56.667 39.044 Z m 0.000 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 56.667 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 55.268 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 53.865 39.044 Z m -6.637 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.500 0.000 A 0.247 0.247 0.000 0 0 47.229 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.497 0.000 A 0.247 0.247 0.000 0 0 45.833 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 44.427 39.044 Z m -5.387 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 39.040 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 37.637 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 36.238 39.044 Z m -6.574 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 29.664 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 28.265 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m -6.412 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 20.451 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 19.051 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 0.000 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 19.051 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 20.451 39.044 Z m 6.412 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 28.265 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 29.664 39.044 Z m 6.574 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 36.238 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 37.637 39.044 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 39.040 39.044 Z m 5.387 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 44.427 39.044 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.497 0.000 A 0.247 0.247 0.000 0 0 45.833 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.500 0.000 A 0.247 0.247 0.000 0 0 47.229 39.044 Z m 6.637 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 53.865 39.044 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 55.268 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 56.667 39.044 Z m 0.000 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 56.667 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 55.268 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 53.865 39.044 Z m -6.637 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.500 0.000 A 0.247 0.247 0.000 0 0 47.229 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.497 0.000 A 0.247 0.247 0.000 0 0 45.833 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 44.427 39.044 Z m -5.387 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 39.040 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 37.637 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 36.238 39.044 Z m -6.574 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 29.664 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 28.265 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m -6.412 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 20.451 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 19.051 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 0.000 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 19.051 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 20.451 39.044 Z m 6.412 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 28.265 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 29.664 39.044 Z m 6.574 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 36.238 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 37.637 39.044 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 39.040 39.044 Z m 5.387 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 44.427 39.044 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.497 0.000 A 0.247 0.247 0.000 0 0 45.833 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.500 0.000 A 0.247 0.247 0.000 0 0 47.229 39.044 Z m 6.637 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 53.865 39.044 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 55.268 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 56.667 39.044 Z m 0.000 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 56.667 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 55.268 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 53.865 39.044 Z m -6.637 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.500 0.000 A 0.247 0.247 0.000 0 0 47.229 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.497 0.000 A 0.247 0.247 0.000 0 0 45.833 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 44.427 39.044 Z m -5.387 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 39.040 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 37.637 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 36.238 39.044 Z m -6.574 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 29.664 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 28.265 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m -6.412 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 20.451 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 19.051 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 0.000 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 19.051 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 20.451 39.044 Z m 6.412 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 28.265 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 29.664 39.044 Z m 6.574 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 36.238 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 37.637 39.044 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 39.040 39.044 Z m 5.387 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 44.427 39.044 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.497 0.000 A 0.247 0.247 0.000 0 0 45.833 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.500 0.000 A 0.247 0.247 0.000 0 0 47.229 39.044 Z m 6.637 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 53.865 39.044 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 55.268 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 56.667 39.044 Z m 0.000 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 56.667 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 55.268 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 53.865 39.044 Z m -6.637 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.500 0.000 A 0.247 0.247 0.000 0 0 47.229 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.497 0.000 A 0.247 0.247 0.000 0 0 45.833 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 44.427 39.044 Z m -5.387 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 39.040 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 37.637 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 36.238 39.044 Z m -6.574 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 29.664 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 28.265 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m -6.412 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 20.451 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 19.051 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 43.312 -8.483 L 3.045 30.562 a 1.796 1.796 0.000 0 0 -1.796 1.796 l 0.000 6.509 a 1.796 1.796 0.000 0 0 1.796 1.793 l 57.910 0.000 a 1.793 1.793 0.000 0 0 1.796 -1.793 L 62.751 32.358 A 1.793 1.793 0.000 0 0 60.961 30.562 Z m -42.453 4.307 a 0.500 0.500 0.000 0 1 0.503 -0.497 l 0.556 0.000 l -0.072 0.250 l -0.400 0.000 a 0.234 0.234 0.000 0 0 -0.237 0.234 l 0.000 0.475 a 0.234 0.234 0.000 0 0 0.237 0.231 l 0.500 0.000 l -0.072 0.253 l -0.512 0.000 a 0.500 0.500 0.000 0 1 -0.503 -0.497 Z m -0.643 -0.503 l 0.481 1.446 l -0.353 0.000 l 0.000 0.000 l -0.312 -1.012 l -0.312 1.018 l -0.350 0.000 l 0.481 -1.446 Z m -6.952 5.500 a 0.240 0.240 0.000 0 1 -0.237 0.240 l -3.807 0.000 a 0.240 0.240 0.000 0 1 -0.237 -0.240 l 0.000 -1.146 a 0.237 0.237 0.000 0 1 0.237 -0.240 l 3.807 0.000 a 0.237 0.237 0.000 0 1 0.237 0.240 Z m 0.665 -4.060 L 10.853 35.806 a 0.234 0.234 0.000 0 1 -0.225 -0.128 a 0.312 0.312 0.000 0 1 -0.034 -0.131 L 10.594 34.366 l 0.978 0.000 l -0.072 0.256 l -0.556 0.000 l 0.000 0.312 l 0.593 0.000 l -0.072 0.253 l -0.522 0.000 l 0.000 0.281 a 0.100 0.100 0.000 0 0 0.103 0.097 l 0.593 0.000 Z m 1.046 0.000 l -0.359 0.000 L 11.790 34.366 l 0.350 0.000 l 0.000 0.000 l 0.312 0.990 l 0.312 -0.996 l 0.353 0.000 Z m 1.665 0.000 l -0.715 0.000 a 0.237 0.237 0.000 0 1 -0.225 -0.128 a 0.312 0.312 0.000 0 1 -0.031 -0.131 L 13.317 34.366 L 14.289 34.366 l -0.069 0.256 L 13.664 34.622 l 0.000 0.312 l 0.590 0.000 l -0.069 0.256 L 13.664 35.190 l 0.000 0.278 a 0.097 0.097 0.000 0 0 0.100 0.097 l 0.593 0.000 Z m 1.152 0.000 l -0.384 -0.687 l 0.106 0.000 a 0.253 0.253 0.000 1 0 0.000 -0.503 l -0.172 0.000 L 14.991 35.834 l -0.353 0.000 l 0.000 -1.459 l 0.646 0.000 a 0.468 0.468 0.000 0 1 0.468 0.465 l 0.000 0.044 a 0.462 0.462 0.000 0 1 -0.269 0.419 l 0.312 0.522 Z m 1.249 0.000 l -0.350 0.000 l 0.000 -1.196 l -0.412 0.000 l 0.000 -0.256 L 17.099 34.353 l -0.069 0.256 l -0.340 0.000 Z m 4.504 4.060 a 0.244 0.244 0.000 0 1 -0.240 0.240 l -3.804 0.000 a 0.240 0.240 0.000 0 1 -0.240 -0.240 l 0.000 -1.146 a 0.237 0.237 0.000 0 1 0.240 -0.240 l 3.804 0.000 a 0.240 0.240 0.000 0 1 0.240 0.240 Z m 9.213 0.000 a 0.244 0.244 0.000 0 1 -0.240 0.240 l -3.804 0.000 a 0.240 0.240 0.000 0 1 -0.240 -0.240 l 0.000 -1.146 a 0.237 0.237 0.000 0 1 0.240 -0.240 l 3.804 0.000 a 0.240 0.240 0.000 0 1 0.240 0.240 Z m 9.370 0.000 a 0.240 0.240 0.000 0 1 -0.237 0.240 l -3.807 0.000 a 0.240 0.240 0.000 0 1 -0.237 -0.240 l 0.000 -1.146 a 0.237 0.237 0.000 0 1 0.237 -0.240 l 3.807 0.000 a 0.237 0.237 0.000 0 1 0.237 0.240 Z m 8.189 0.000 a 0.240 0.240 0.000 0 1 -0.237 0.240 l -3.807 0.000 a 0.240 0.240 0.000 0 1 -0.237 -0.240 l 0.000 -1.146 a 0.237 0.237 0.000 0 1 0.237 -0.240 l 3.807 0.000 a 0.237 0.237 0.000 0 1 0.237 0.240 Z m 9.441 0.000 a 0.244 0.244 0.000 0 1 -0.240 0.240 l -3.807 0.000 a 0.240 0.240 0.000 0 1 -0.237 -0.240 l 0.000 -1.146 a 0.237 0.237 0.000 0 1 0.237 -0.240 l 3.807 0.000 a 0.240 0.240 0.000 0 1 0.240 0.240 Z m -0.743 -0.821 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 56.667 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 55.268 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 53.865 39.044 Z m -6.637 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.500 0.000 A 0.247 0.247 0.000 0 0 47.229 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.497 0.000 A 0.247 0.247 0.000 0 0 45.833 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 44.427 39.044 Z m -5.387 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 39.040 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 37.637 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 36.238 39.044 Z m -6.574 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 29.664 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 28.265 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m -6.412 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 20.451 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 19.051 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 0.000 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 19.051 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 20.451 39.044 Z m 6.412 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 28.265 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 29.664 39.044 Z m 6.574 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 36.238 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 37.637 39.044 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 39.040 39.044 Z m 5.387 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 44.427 39.044 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.497 0.000 A 0.247 0.247 0.000 0 0 45.833 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.500 0.000 A 0.247 0.247 0.000 0 0 47.229 39.044 Z m 6.637 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 53.865 39.044 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 55.268 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 56.667 39.044 Z m 0.000 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 56.667 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 55.268 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 53.865 39.044 Z m -6.637 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.500 0.000 A 0.247 0.247 0.000 0 0 47.229 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.497 0.000 A 0.247 0.247 0.000 0 0 45.833 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 44.427 39.044 Z m -5.387 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 39.040 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 37.637 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 36.238 39.044 Z m -6.574 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 29.664 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 28.265 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m -6.412 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 20.451 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 19.051 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 0.000 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 19.051 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 20.451 39.044 Z m 6.412 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 28.265 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 29.664 39.044 Z m 6.574 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 36.238 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 37.637 39.044 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 39.040 39.044 Z m 5.387 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 44.427 39.044 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.497 0.000 A 0.247 0.247 0.000 0 0 45.833 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.500 0.000 A 0.247 0.247 0.000 0 0 47.229 39.044 Z m 6.637 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 53.865 39.044 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 55.268 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 56.667 39.044 Z m 0.000 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 56.667 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 55.268 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 53.865 39.044 Z m -6.637 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.500 0.000 A 0.247 0.247 0.000 0 0 47.229 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.497 0.000 A 0.247 0.247 0.000 0 0 45.833 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 44.427 39.044 Z m -5.387 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 39.040 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 37.637 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 36.238 39.044 Z m -6.574 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 29.664 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 28.265 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m -6.412 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 20.451 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 19.051 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 0.000 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 19.051 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 20.451 39.044 Z m 6.412 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 28.265 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 29.664 39.044 Z m 6.574 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 36.238 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 37.637 39.044 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 39.040 39.044 Z m 5.387 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 44.427 39.044 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.497 0.000 A 0.247 0.247 0.000 0 0 45.833 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.500 0.000 A 0.247 0.247 0.000 0 0 47.229 39.044 Z m 6.637 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 53.865 39.044 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 55.268 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 56.667 39.044 Z m 0.000 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 56.667 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 55.268 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 53.865 39.044 Z m -6.637 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.500 0.000 A 0.247 0.247 0.000 0 0 47.229 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.497 0.000 A 0.247 0.247 0.000 0 0 45.833 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 44.427 39.044 Z m -5.387 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 39.040 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 37.637 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 36.238 39.044 Z m -6.574 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 29.664 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 28.265 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m -6.412 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 20.451 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 19.051 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 0.000 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 19.051 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 20.451 39.044 Z m 6.412 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 28.265 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 29.664 39.044 Z m 6.574 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 36.238 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 37.637 39.044 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 39.040 39.044 Z m 5.387 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 44.427 39.044 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.497 0.000 A 0.247 0.247 0.000 0 0 45.833 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.500 0.000 A 0.247 0.247 0.000 0 0 47.229 39.044 Z m 0.000 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.500 0.000 A 0.247 0.247 0.000 0 0 47.229 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 1 0 0.497 0.000 A 0.247 0.247 0.000 0 0 45.833 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 44.427 39.044 Z m -5.387 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 39.040 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 37.637 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 36.238 39.044 Z m -6.574 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 29.664 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 28.265 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m -6.412 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 20.451 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 19.051 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 0.000 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 19.051 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 20.451 39.044 Z m 6.412 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m 1.402 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 28.265 39.044 Z m 1.399 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 29.664 39.044 Z m 0.000 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 29.664 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 28.265 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z m -6.412 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.247 0.247 0.000 0 0 0.247 0.250 a 0.250 0.250 0.000 0 0 0.250 -0.250 A 0.247 0.247 0.000 0 0 20.451 39.044 Z m -1.399 0.000 a 0.247 0.247 0.000 0 0 -0.250 0.247 a 0.250 0.250 0.000 0 0 0.250 0.250 a 0.247 0.247 0.000 0 0 0.247 -0.250 A 0.247 0.247 0.000 0 0 19.051 39.044 Z m -1.402 0.000 a 0.247 0.247 0.000 0 0 -0.247 0.247 a 0.250 0.250 0.000 1 0 0.247 -0.247 Z',fill:'#f59e0b',stroke:'none'},{d:'M 7.617 39.291 a 0.247 0.247 0.000 0 1 -0.247 0.250 a 0.250 0.250 0.000 0 1 -0.250 -0.250 a 0.247 0.247 0.000 0 1 0.250 -0.247 A 0.247 0.247 0.000 0 1 7.617 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 9.020 39.291 a 0.250 0.250 0.000 0 1 -0.250 0.250 a 0.247 0.247 0.000 0 1 -0.247 -0.250 a 0.247 0.247 0.000 0 1 0.247 -0.247 A 0.247 0.247 0.000 0 1 9.020 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 10.419 39.291 a 0.247 0.247 0.000 0 1 -0.247 0.250 a 0.250 0.250 0.000 0 1 -0.250 -0.250 a 0.247 0.247 0.000 0 1 0.250 -0.247 A 0.247 0.247 0.000 0 1 10.419 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 7.617 39.291 a 0.247 0.247 0.000 0 1 -0.247 0.250 a 0.250 0.250 0.000 0 1 -0.250 -0.250 a 0.247 0.247 0.000 0 1 0.250 -0.247 A 0.247 0.247 0.000 0 1 7.617 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 9.020 39.291 a 0.250 0.250 0.000 0 1 -0.250 0.250 a 0.247 0.247 0.000 0 1 -0.247 -0.250 a 0.247 0.247 0.000 0 1 0.247 -0.247 A 0.247 0.247 0.000 0 1 9.020 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 10.419 39.291 a 0.247 0.247 0.000 0 1 -0.247 0.250 a 0.250 0.250 0.000 0 1 -0.250 -0.250 a 0.247 0.247 0.000 0 1 0.250 -0.247 A 0.247 0.247 0.000 0 1 10.419 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 17.899 39.291 a 0.250 0.250 0.000 1 1 -0.497 0.000 a 0.250 0.250 0.000 0 1 0.497 0.000 Z',fill:'#f59e0b',stroke:'none'},{d:'M 19.286 39.291 a 0.247 0.247 0.000 0 1 -0.247 0.250 a 0.250 0.250 0.000 0 1 -0.250 -0.250 a 0.247 0.247 0.000 0 1 0.250 -0.247 A 0.247 0.247 0.000 0 1 19.286 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 20.700 39.291 a 0.250 0.250 0.000 0 1 -0.250 0.250 a 0.247 0.247 0.000 0 1 -0.247 -0.250 a 0.247 0.247 0.000 0 1 0.247 -0.247 A 0.247 0.247 0.000 0 1 20.700 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 17.899 39.291 a 0.250 0.250 0.000 1 1 -0.497 0.000 a 0.250 0.250 0.000 0 1 0.497 0.000 Z',fill:'#f59e0b',stroke:'none'},{d:'M 19.286 39.291 a 0.247 0.247 0.000 0 1 -0.247 0.250 a 0.250 0.250 0.000 0 1 -0.250 -0.250 a 0.247 0.247 0.000 0 1 0.250 -0.247 A 0.247 0.247 0.000 0 1 19.286 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 20.700 39.291 a 0.250 0.250 0.000 0 1 -0.250 0.250 a 0.247 0.247 0.000 0 1 -0.247 -0.250 a 0.247 0.247 0.000 0 1 0.247 -0.247 A 0.247 0.247 0.000 0 1 20.700 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 27.112 39.291 a 0.250 0.250 0.000 1 1 -0.497 0.000 a 0.250 0.250 0.000 0 1 0.497 0.000 Z',fill:'#f59e0b',stroke:'none'},{d:'M 28.511 39.291 a 0.247 0.247 0.000 0 1 -0.247 0.250 a 0.250 0.250 0.000 0 1 -0.250 -0.250 a 0.247 0.247 0.000 0 1 0.250 -0.247 A 0.247 0.247 0.000 0 1 28.511 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 29.904 39.291 a 0.250 0.250 0.000 0 1 -0.250 0.250 a 0.247 0.247 0.000 0 1 -0.247 -0.250 a 0.247 0.247 0.000 0 1 0.247 -0.247 A 0.247 0.247 0.000 0 1 29.904 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 27.112 39.291 a 0.250 0.250 0.000 1 1 -0.497 0.000 a 0.250 0.250 0.000 0 1 0.497 0.000 Z',fill:'#f59e0b',stroke:'none'},{d:'M 28.511 39.291 a 0.247 0.247 0.000 0 1 -0.247 0.250 a 0.250 0.250 0.000 0 1 -0.250 -0.250 a 0.247 0.247 0.000 0 1 0.250 -0.247 A 0.247 0.247 0.000 0 1 28.511 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 29.904 39.291 a 0.250 0.250 0.000 0 1 -0.250 0.250 a 0.247 0.247 0.000 0 1 -0.247 -0.250 a 0.247 0.247 0.000 0 1 0.247 -0.247 A 0.247 0.247 0.000 0 1 29.904 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 36.485 39.291 a 0.247 0.247 0.000 0 1 -0.247 0.250 a 0.250 0.250 0.000 0 1 -0.250 -0.250 a 0.247 0.247 0.000 0 1 0.250 -0.247 A 0.247 0.247 0.000 0 1 36.485 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 37.887 39.291 a 0.250 0.250 0.000 0 1 -0.250 0.250 a 0.247 0.247 0.000 0 1 -0.247 -0.250 a 0.247 0.247 0.000 0 1 0.247 -0.247 A 0.247 0.247 0.000 0 1 37.887 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 39.274 39.291 a 0.247 0.247 0.000 0 1 -0.247 0.250 a 0.250 0.250 0.000 0 1 -0.250 -0.250 a 0.247 0.247 0.000 0 1 0.250 -0.247 A 0.247 0.247 0.000 0 1 39.274 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 36.485 39.291 a 0.247 0.247 0.000 0 1 -0.247 0.250 a 0.250 0.250 0.000 0 1 -0.250 -0.250 a 0.247 0.247 0.000 0 1 0.250 -0.247 A 0.247 0.247 0.000 0 1 36.485 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 37.887 39.291 a 0.250 0.250 0.000 0 1 -0.250 0.250 a 0.247 0.247 0.000 0 1 -0.247 -0.250 a 0.247 0.247 0.000 0 1 0.247 -0.247 A 0.247 0.247 0.000 0 1 37.887 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 39.274 39.291 a 0.247 0.247 0.000 0 1 -0.247 0.250 a 0.250 0.250 0.000 0 1 -0.250 -0.250 a 0.247 0.247 0.000 0 1 0.250 -0.247 A 0.247 0.247 0.000 0 1 39.274 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 44.677 39.291 a 0.250 0.250 0.000 0 1 -0.250 0.250 a 0.247 0.247 0.000 0 1 -0.247 -0.250 a 0.247 0.247 0.000 0 1 0.247 -0.247 A 0.247 0.247 0.000 0 1 44.677 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 46.076 39.291 a 0.250 0.250 0.000 1 1 -0.247 -0.247 A 0.247 0.247 0.000 0 1 46.076 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 47.478 39.291 a 0.250 0.250 0.000 1 1 -0.500 0.000 a 0.250 0.250 0.000 0 1 0.500 0.000 Z',fill:'#f59e0b',stroke:'none'},{d:'M 44.677 39.291 a 0.250 0.250 0.000 0 1 -0.250 0.250 a 0.247 0.247 0.000 0 1 -0.247 -0.250 a 0.247 0.247 0.000 0 1 0.247 -0.247 A 0.247 0.247 0.000 0 1 44.677 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 46.076 39.291 a 0.250 0.250 0.000 1 1 -0.247 -0.247 A 0.247 0.247 0.000 0 1 46.076 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 47.478 39.291 a 0.250 0.250 0.000 1 1 -0.500 0.000 a 0.250 0.250 0.000 0 1 0.500 0.000 Z',fill:'#f59e0b',stroke:'none'},{d:'M 54.115 39.291 a 0.250 0.250 0.000 0 1 -0.250 0.250 a 0.247 0.247 0.000 0 1 -0.247 -0.250 a 0.247 0.247 0.000 0 1 0.247 -0.247 A 0.247 0.247 0.000 0 1 54.115 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 55.514 39.291 a 0.247 0.247 0.000 0 1 -0.247 0.250 a 0.250 0.250 0.000 0 1 -0.250 -0.250 a 0.247 0.247 0.000 0 1 0.250 -0.247 A 0.247 0.247 0.000 0 1 55.514 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 56.917 39.291 a 0.250 0.250 0.000 0 1 -0.250 0.250 a 0.247 0.247 0.000 0 1 -0.247 -0.250 a 0.247 0.247 0.000 0 1 0.247 -0.247 A 0.247 0.247 0.000 0 1 56.917 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 54.115 39.291 a 0.250 0.250 0.000 0 1 -0.250 0.250 a 0.247 0.247 0.000 0 1 -0.247 -0.250 a 0.247 0.247 0.000 0 1 0.247 -0.247 A 0.247 0.247 0.000 0 1 54.115 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 55.514 39.291 a 0.247 0.247 0.000 0 1 -0.247 0.250 a 0.250 0.250 0.000 0 1 -0.250 -0.250 a 0.247 0.247 0.000 0 1 0.250 -0.247 A 0.247 0.247 0.000 0 1 55.514 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 56.917 39.291 a 0.250 0.250 0.000 0 1 -0.250 0.250 a 0.247 0.247 0.000 0 1 -0.247 -0.250 a 0.247 0.247 0.000 0 1 0.247 -0.247 A 0.247 0.247 0.000 0 1 56.917 39.291 Z',fill:'#f59e0b',stroke:'none'},{d:'M 11.340 23.341 l 0.000 0.431 l -0.853 0.000 c -0.141 0.000 -0.256 0.081 -0.256 0.184 l 0.000 0.284 l -0.187 0.000 l 0.000 0.918 l 0.187 0.000 l 0.000 5.119 l 2.039 0.000 L 12.271 25.074 l 0.175 -0.206 L 12.446 23.341 Z m -0.097 4.750 l 0.000 -0.984 l -0.656 0.000 l 0.659 -1.318 L 11.247 26.776 l 0.656 0.000 Z',fill:'#f59e0b',stroke:'none'},{d:'M 20.922 23.341 l 0.000 0.431 l -0.853 0.000 c -0.144 0.000 -0.256 0.081 -0.256 0.184 l 0.000 0.284 l -0.187 0.000 l 0.000 0.918 l 0.187 0.000 l 0.000 5.119 l 2.036 0.000 L 21.850 25.074 l 0.175 -0.206 L 22.025 23.341 Z m -0.097 4.750 l 0.000 -0.984 l -0.656 0.000 l 0.656 -1.318 L 20.825 26.776 L 21.472 26.776 Z',fill:'#f59e0b',stroke:'none'},{d:'M 30.504 23.341 l 0.000 0.431 l -0.856 0.000 c -0.141 0.000 -0.256 0.081 -0.256 0.184 l 0.000 0.284 l -0.187 0.000 l 0.000 0.918 l 0.187 0.000 l 0.000 5.119 l 2.039 0.000 L 31.432 25.074 l 0.175 -0.206 L 31.606 23.341 Z m -0.097 4.750 l 0.000 -0.984 l -0.659 0.000 l 0.659 -1.318 L 30.407 26.776 l 0.656 0.000 Z',fill:'#f59e0b',stroke:'none'}]},
  omu: {viewBox:'0 0 64 64', paths:[{d:'M 12.614 23.046 h 38.784 c 0.384 0.000 0.695 -0.311 0.695 -0.695 s -0.311 -0.695 -0.695 -0.695 h -38.784 c -0.384 0.000 -0.695 0.311 -0.695 0.695 C 11.919 22.735 12.230 23.046 12.614 23.046 z',fill:'#a855f7',stroke:'none'},{d:'M 53.278 23.969 h -42.544 c -0.779 0.000 -1.420 0.635 -1.420 1.420 v 15.508 c 0.000 0.787 0.641 1.420 1.420 1.420 h 42.546 c 0.787 0.000 1.420 -0.635 1.420 -1.420 v -15.508 C 54.701 24.604 54.065 23.969 53.278 23.969 z M 15.953 37.888 c 0.000 0.084 -0.047 0.170 -0.120 0.212 l -3.532 2.123 c -0.170 0.097 -0.382 -0.024 -0.382 -0.217 V 26.288 c 0.000 -0.193 0.212 -0.314 0.382 -0.212 l 3.532 2.115 c 0.073 0.042 0.120 0.128 0.120 0.212 V 37.888 z M 38.889 38.552 h -13.767 v -10.816 h 13.767 V 38.552 z M 52.094 40.003 c 0.000 0.193 -0.212 0.314 -0.382 0.217 l -3.532 -2.123 c -0.073 -0.042 -0.120 -0.128 -0.120 -0.212 v -9.485 c 0.000 -0.084 0.047 -0.170 0.120 -0.212 l 3.532 -2.115 c 0.170 -0.102 0.382 0.018 0.382 0.212 V 40.003 z',fill:'#a855f7',stroke:'none'},{d:'M 59.582 25.294 h -3.529 v 15.702 h 3.529 c 0.837 0.000 1.514 -0.677 1.514 -1.514 v -12.675 C 61.095 25.971 60.418 25.294 59.582 25.294 z',fill:'#a855f7',stroke:'none'},{d:'M 2.918 26.808 v 12.675 c 0.000 0.837 0.677 1.514 1.514 1.514 h 3.529 V 25.294 h -3.529 C 3.595 25.294 2.918 25.971 2.918 26.808 z',fill:'#a855f7',stroke:'none'},{d:'M 27.603 32.609 c 0.029 -0.920 0.102 -1.605 1.182 -1.605 s 1.153 0.685 1.182 1.605 v 0.515 c 0.000 0.965 -0.073 1.668 -1.182 1.668 s -1.182 -0.703 -1.182 -1.668 V 32.609 z M 28.295 33.461 c 0.000 0.298 0.024 0.784 0.486 0.784 c 0.481 0.000 0.486 -0.497 0.486 -0.844 v -0.925 c 0.000 -0.290 0.016 -0.931 -0.486 -0.931 c -0.531 0.000 -0.486 0.630 -0.486 0.910 V 33.461 z',fill:'#a855f7',stroke:'none'},{d:'M 31.129 34.706 h -0.675 v -3.613 h 1.075 l 0.361 1.678 c 0.058 0.275 0.097 0.554 0.125 0.834 h 0.010 c 0.034 -0.356 0.058 -0.599 0.107 -0.834 l 0.361 -1.678 h 1.069 V 34.706 h -0.675 v -1.137 c 0.000 -0.719 0.016 -1.435 0.058 -2.154 h -0.010 l -0.722 3.292 h -0.410 l -0.708 -3.292 h -0.024 c 0.044 0.719 0.058 1.435 0.058 2.154 L 31.129 34.706 L 31.129 34.706 z',fill:'#a855f7',stroke:'none'},{d:'M 35.707 31.093 h 0.675 v 2.520 c 0.000 0.800 -0.261 1.182 -1.142 1.182 c -0.892 0.000 -1.153 -0.382 -1.153 -1.182 v -2.520 h 0.675 v 2.463 c 0.000 0.348 0.024 0.693 0.481 0.693 c 0.439 0.000 0.463 -0.348 0.463 -0.693 L 35.707 31.093 L 35.707 31.093 z',fill:'#a855f7',stroke:'none'}]},
  oru: {viewBox:'0 0 64 64', paths:[{d:'M 12.596 23.046 h 38.782 c 0.384 0.000 0.695 -0.311 0.695 -0.695 s -0.311 -0.695 -0.695 -0.695 H 12.596 c -0.384 0.000 -0.695 0.311 -0.695 0.695 S 12.212 23.046 12.596 23.046 z',fill:'#a855f7',stroke:'none'},{d:'M 53.260 23.969 H 10.714 c -0.779 0.000 -1.420 0.635 -1.420 1.420 v 15.508 c 0.000 0.787 0.641 1.420 1.420 1.420 h 42.546 c 0.787 0.000 1.420 -0.635 1.420 -1.420 v -15.508 C 54.682 24.604 54.047 23.969 53.260 23.969 z M 15.932 37.888 c 0.000 0.084 -0.047 0.170 -0.120 0.212 l -3.532 2.123 c -0.170 0.097 -0.382 -0.024 -0.382 -0.217 V 26.288 c 0.000 -0.193 0.212 -0.314 0.382 -0.212 l 3.532 2.115 c 0.073 0.042 0.120 0.128 0.120 0.212 V 37.888 z M 38.871 38.552 h -13.767 v -10.816 h 13.767 V 38.552 z M 52.076 40.003 c 0.000 0.193 -0.212 0.314 -0.382 0.217 l -3.532 -2.123 c -0.073 -0.042 -0.120 -0.128 -0.120 -0.212 v -9.485 c 0.000 -0.084 0.047 -0.170 0.120 -0.212 l 3.532 -2.115 c 0.170 -0.102 0.382 0.018 0.382 0.212 V 40.003 z',fill:'#a855f7',stroke:'none'},{d:'M 59.563 25.294 h -3.529 v 15.702 h 3.529 c 0.837 0.000 1.514 -0.677 1.514 -1.514 v -12.675 C 61.077 25.971 60.400 25.294 59.563 25.294 z',fill:'#a855f7',stroke:'none'},{d:'M 2.899 26.808 v 12.675 c 0.000 0.837 0.677 1.514 1.514 1.514 h 3.529 V 25.294 h -3.529 C 3.576 25.294 2.899 25.971 2.899 26.808 z',fill:'#a855f7',stroke:'none'},{d:'M 27.984 32.651 c 0.029 -0.920 0.102 -1.605 1.182 -1.605 c 1.080 0.000 1.153 0.685 1.182 1.605 v 0.515 c 0.000 0.965 -0.073 1.668 -1.182 1.668 s -1.182 -0.703 -1.182 -1.668 V 32.651 z M 28.680 33.506 c 0.000 0.298 0.024 0.784 0.486 0.784 c 0.481 0.000 0.486 -0.497 0.486 -0.844 v -0.925 c 0.000 -0.290 0.016 -0.931 -0.486 -0.931 c -0.531 0.000 -0.486 0.630 -0.486 0.910 V 33.506 z',fill:'#a855f7',stroke:'none'},{d:'M 31.508 33.192 v 1.556 h -0.675 v -3.613 h 1.276 c 0.583 0.000 1.027 0.201 1.027 0.868 c 0.000 0.395 -0.102 0.810 -0.554 0.873 v 0.010 c 0.400 0.052 0.520 0.308 0.520 0.656 c 0.000 0.149 -0.018 1.035 0.144 1.142 v 0.068 h -0.742 c -0.081 -0.230 -0.068 -0.675 -0.073 -0.915 c -0.005 -0.222 0.000 -0.525 -0.230 -0.593 c -0.183 -0.052 -0.382 -0.047 -0.573 -0.047 h -0.120 V 33.192 z M 31.508 32.661 h 0.531 c 0.222 -0.016 0.395 -0.159 0.395 -0.520 c 0.000 -0.405 -0.167 -0.473 -0.424 -0.476 h -0.502 V 32.661 z',fill:'#a855f7',stroke:'none'},{d:'M 35.286 31.135 h 0.675 v 2.520 c 0.000 0.800 -0.261 1.182 -1.142 1.182 c -0.892 0.000 -1.153 -0.382 -1.153 -1.182 v -2.520 h 0.675 v 2.463 c 0.000 0.348 0.024 0.693 0.481 0.693 c 0.439 0.000 0.463 -0.348 0.463 -0.693 v -2.463 H 35.286 z',fill:'#a855f7',stroke:'none'}]},
  oru_wall: {viewBox:'0 0 64 64', paths:[{d:'M 22.864 43.627 l -10.371 15.824 c -0.068 -0.217 -0.110 -0.455 -0.110 -0.703 V 6.421 L 22.864 43.627 z',fill:'#a855f7',stroke:'none'},{d:'M 39.528 44.788 l 10.588 16.152 c -0.259 0.098 -0.545 0.158 -0.842 0.158 h -34.542 c -0.298 0.000 -0.586 -0.060 -0.842 -0.158 l 10.588 -16.152 C 24.478 44.788 39.528 44.788 39.528 44.788 z',fill:'#a855f7',stroke:'none'},{d:'M 24.698 42.806 l -11.154 -39.567 c 0.348 -0.208 0.753 -0.327 1.191 -0.327 h 34.542 c 0.467 0.000 0.893 0.140 1.259 0.366 l -11.145 39.528 H 24.698 z',fill:'#a855f7',stroke:'none'},{d:'M 51.626 6.698 v 52.051 c 0.000 0.247 -0.039 0.485 -0.110 0.703 l -10.320 -15.744 L 51.626 6.698 z',fill:'#a855f7',stroke:'none'}]},
  radio_display: {viewBox:'0 0 64 64', paths:[{d:'M 27.015 23.598 h 10.377 v 13.643 h -10.377 z',fill:'#f59e0b',stroke:'none'},{d:'M 36.726 38.585 h -9.044 c -0.369 0.000 -0.666 0.297 -0.666 0.666 v 3.869 h 10.377 v -3.869 C 37.392 38.882 37.092 38.585 36.726 38.585 z M 32.160 39.491 l 0.347 0.520 h -0.697 L 32.160 39.491 z M 28.698 41.473 l -0.520 -0.347 l 0.520 -0.347 V 41.473 z M 32.160 42.773 l -0.347 -0.520 h 0.697 L 32.160 42.773 z M 34.498 41.256 c 0.000 0.036 -0.030 0.066 -0.066 0.066 h -4.571 c -0.036 0.000 -0.066 -0.030 -0.066 -0.066 v -0.273 c 0.000 -0.036 0.030 -0.066 0.066 -0.066 h 4.571 c 0.036 0.000 0.066 0.030 0.066 0.066 V 41.256 z M 35.627 41.473 v -0.697 l 0.520 0.347 L 35.627 41.473 z M 27.015 43.420 v 1.102 c 0.000 0.369 0.297 0.666 0.666 0.666 h 9.044 c 0.369 0.000 0.666 -0.297 0.666 -0.666 v -1.102 H 27.015 z',fill:'#f59e0b',stroke:'none'},{d:'M 22.565 34.861 v -7.215 c -0.127 -1.135 -0.543 -1.583 -0.735 -1.735 v 10.831 C 22.408 36.200 22.565 34.861 22.565 34.861 z',fill:'#f59e0b',stroke:'none'},{d:'M 42.162 35.252 v -10.583 h -0.465 l 0.003 -1.303 c 0.000 0.000 -0.209 -3.073 -0.383 -3.473 c 0.000 0.000 -0.096 -0.289 -0.284 -0.518 l -0.325 -2.894 h -0.482 v -2.261 c 0.000 0.000 -0.124 -0.289 -0.496 -0.330 h -3.362 c 0.000 0.000 -0.358 0.193 -0.413 0.344 c -0.055 0.151 -0.041 2.991 -0.041 2.991 h -7.290 l -0.375 -13.601 c 0.000 0.000 -0.248 -0.490 -0.460 -0.573 c 0.000 0.000 -1.740 -0.347 -3.437 0.000 c 0.000 0.000 -0.372 0.347 -0.289 0.573 l -0.559 13.703 l -0.207 0.229 l -0.124 1.922 c 0.000 0.000 -0.196 5.789 -1.267 5.582 v 0.785 c 0.000 0.000 0.666 0.311 0.832 1.798 v 7.212 c 0.000 0.000 -0.176 1.487 -0.832 1.964 v 0.606 c 0.000 0.000 0.763 0.551 0.804 2.109 c 0.000 0.000 -0.096 18.162 0.565 19.899 c 0.000 0.000 0.931 1.652 2.192 1.652 h 13.436 c 0.000 0.000 1.862 -0.143 2.233 -2.087 c 0.000 0.000 0.724 -13.992 0.526 -19.627 h 0.496 v -3.751 h -0.487 v -0.372 L 42.162 35.252 L 42.162 35.252 z M 34.861 19.134 c 0.000 -0.212 0.176 -0.386 0.391 -0.386 h 0.366 c 0.006 0.000 0.050 0.000 0.058 0.000 h 0.006 l -0.055 0.193 h -0.308 c -0.102 0.000 -0.182 0.080 -0.182 0.179 v 0.366 c 0.000 0.099 0.083 0.182 0.182 0.182 h 0.388 l -0.055 0.196 h -0.394 c -0.215 0.000 -0.391 -0.173 -0.391 -0.386 v -0.344 H 34.861 z M 34.363 18.746 l 0.372 1.115 h -0.273 v -0.003 l -0.240 -0.782 l -0.240 0.785 h -0.270 l 0.372 -1.115 H 34.363 L 34.363 18.746 z M 33.721 18.944 h -0.262 v 0.925 h -0.270 v -0.925 h -0.317 v -0.196 h 0.903 L 33.721 18.944 z M 31.320 17.333 h 1.729 v 0.352 c 0.000 0.146 -0.118 0.262 -0.262 0.262 h -1.206 c -0.143 0.000 -0.262 -0.118 -0.262 -0.262 V 17.333 z M 32.278 18.941 h -0.135 v 0.928 h -0.270 v -1.126 h 0.496 c 0.201 0.000 0.364 0.160 0.364 0.358 v 0.033 c 0.000 0.143 -0.085 0.264 -0.207 0.322 l 0.248 0.402 h -0.281 l -0.297 -0.529 h 0.083 c 0.110 0.000 0.198 -0.088 0.198 -0.196 C 32.476 19.027 32.388 18.941 32.278 18.941 z M 30.852 18.746 h 0.755 l -0.055 0.196 h -0.430 v 0.242 h 0.457 l -0.055 0.196 h -0.402 v 0.215 c 0.000 0.017 0.011 0.074 0.077 0.074 h 0.460 l -0.055 0.196 h -0.554 c -0.102 0.000 -0.151 -0.055 -0.173 -0.099 c -0.025 -0.050 -0.025 -0.099 -0.025 -0.099 L 30.852 18.746 L 30.852 18.746 z M 29.940 18.746 L 29.940 18.746 l 0.240 0.766 l 0.240 -0.768 h 0.270 l -0.372 1.121 h -0.278 l -0.372 -1.121 h 0.273 V 18.746 z M 28.759 18.746 h 0.755 l -0.055 0.196 h -0.430 v 0.242 h 0.457 l -0.055 0.196 h -0.402 v 0.215 c 0.000 0.017 0.008 0.074 0.077 0.074 h 0.460 l -0.055 0.196 h -0.554 c -0.102 0.000 -0.151 -0.055 -0.173 -0.099 c -0.025 -0.050 -0.025 -0.099 -0.025 -0.099 L 28.759 18.746 L 28.759 18.746 z M 25.531 22.901 l 0.487 -1.220 c 0.055 -0.138 0.187 -0.226 0.336 -0.226 h 12.062 l 0.509 1.377 v 22.722 l -0.537 1.776 h -11.988 l -0.867 -1.611 L 25.531 22.901 L 25.531 22.901 z M 34.462 58.982 h -4.505 v -1.115 h 4.505 V 58.982 z M 39.457 55.785 c 0.000 0.085 -0.044 0.165 -0.116 0.209 l -0.554 0.350 c -0.039 0.025 -0.085 0.039 -0.132 0.039 h -13.001 c -0.047 0.000 -0.091 -0.014 -0.129 -0.036 l -0.471 -0.289 c -0.074 -0.044 -0.118 -0.127 -0.118 -0.212 v -1.446 c 0.000 -0.085 0.041 -0.162 0.113 -0.209 l 0.476 -0.311 c 0.039 -0.025 0.085 -0.039 0.132 -0.041 l 13.122 -0.140 c 0.066 0.000 0.132 0.025 0.179 0.072 l 0.427 0.427 c 0.047 0.047 0.072 0.110 0.072 0.176 V 55.785 z M 39.457 51.619 c 0.000 0.085 -0.044 0.165 -0.116 0.209 l -0.554 0.350 c -0.039 0.025 -0.085 0.039 -0.132 0.039 h -13.001 c -0.047 0.000 -0.091 -0.014 -0.129 -0.036 l -0.471 -0.289 c -0.074 -0.044 -0.118 -0.127 -0.118 -0.212 v -1.446 c 0.000 -0.085 0.041 -0.162 0.113 -0.209 l 0.476 -0.311 c 0.039 -0.025 0.085 -0.039 0.132 -0.041 l 13.122 -0.143 c 0.066 0.000 0.132 0.025 0.179 0.072 l 0.427 0.427 c 0.047 0.047 0.072 0.110 0.072 0.176 V 51.619 z',fill:'#f59e0b',stroke:'none'}]},
  radio_handheld: {viewBox:'0 0 64 64', paths:[{d:'M 41.834 21.089 h -0.179 v -0.050 c 0.000 -1.542 -1.019 -2.812 -2.341 -3.010 v -2.085 c 0.000 -0.647 -0.465 -1.173 -1.041 -1.173 h -3.032 c -0.576 0.000 -1.041 0.526 -1.041 1.173 v 2.054 h -5.075 v -12.599 c 0.000 -1.377 -0.991 -2.495 -2.214 -2.495 c -1.223 0.000 -2.214 1.115 -2.214 2.495 v 12.621 c -1.344 0.168 -2.390 1.454 -2.390 3.015 v 5.067 c -0.361 0.099 -0.628 0.463 -0.628 0.898 v 8.917 c 0.000 0.438 0.270 0.801 0.628 0.898 v 21.230 c 0.000 1.683 1.212 3.046 2.699 3.046 h 13.943 c 1.493 0.000 2.704 -1.366 2.704 -3.046 v -21.202 h 0.179 c 0.281 0.000 0.507 -0.256 0.507 -0.570 v -14.618 C 42.341 21.345 42.115 21.089 41.834 21.089 z M 38.246 55.879 c 0.000 0.815 -0.584 1.473 -1.305 1.473 h -9.917 c -0.716 0.000 -1.303 -0.658 -1.303 -1.473 v -17.906 c 0.000 -0.815 0.584 -1.473 1.303 -1.473 h 9.917 c 0.722 0.000 1.305 0.658 1.305 1.473 V 55.879 z M 26.938 31.813 h 10.090 c 0.292 0.000 0.531 0.270 0.531 0.598 v 0.969 c 0.000 0.336 -0.240 0.598 -0.531 0.598 h -10.090 c -0.292 0.000 -0.531 -0.264 -0.531 -0.598 v -0.969 C 26.407 32.083 26.646 31.813 26.938 31.813 z M 26.407 30.089 v -0.969 c 0.000 -0.330 0.240 -0.598 0.531 -0.598 h 10.090 c 0.292 0.000 0.531 0.270 0.531 0.598 v 0.969 c 0.000 0.336 -0.240 0.598 -0.531 0.598 h -10.090 C 26.646 30.689 26.407 30.425 26.407 30.089 z M 38.246 24.746 c 0.000 0.832 -0.600 1.509 -1.338 1.509 h -9.848 c -0.738 0.000 -1.338 -0.677 -1.338 -1.509 v -1.622 c 0.000 -0.832 0.600 -1.509 1.338 -1.509 h 9.848 c 0.738 0.000 1.338 0.677 1.338 1.509 V 24.746 z',fill:'#f59e0b',stroke:'none'},{d:'M 36.142 38.282 c -0.322 0.000 -0.584 0.295 -0.584 0.655 c 0.000 0.364 0.262 0.655 0.584 0.655 s 0.584 -0.295 0.584 -0.655 C 36.726 38.573 36.464 38.282 36.142 38.282 z',fill:'#f59e0b',stroke:'none'},{d:'M 34.748 53.260 h -5.466 c -0.196 0.000 -0.355 0.179 -0.355 0.399 v 1.322 c 0.000 0.220 0.160 0.399 0.355 0.399 h 5.466 c 0.196 0.000 0.355 -0.179 0.355 -0.399 v -1.322 C 35.104 53.439 34.944 53.260 34.748 53.260 z',fill:'#f59e0b',stroke:'none'}]},
  rf_amplifier: {viewBox:'0 0 64 64', paths:[{d:'M 51.024 3.227 a 1.689 1.689 0.000 0 1 1.689 1.689 l 0.000 54.143 a 1.692 1.692 0.000 0 1 -1.689 1.692 L 12.976 60.751 a 1.692 1.692 0.000 0 1 -1.689 -1.692 l 0.000 -54.143 a 1.689 1.689 0.000 0 1 1.689 -1.689 l 38.047 0.000 m 0.000 -1.793 L 12.976 1.434 a 3.482 3.482 0.000 0 0 -3.482 3.482 l 0.000 54.143 a 3.482 3.482 0.000 0 0 3.482 3.485 l 38.047 0.000 a 3.485 3.485 0.000 0 0 3.482 -3.485 l 0.000 -54.143 a 3.482 3.482 0.000 0 0 -3.482 -3.482 Z',fill:'#3b82f6',stroke:'none'},{d:'M 18.559 1.434 L 18.559 62.566 l -5.586 0.000 a 3.478 3.478 0.000 0 1 -3.478 -3.482 l 0.000 -54.143 a 3.478 3.478 0.000 0 1 3.478 -3.482 Z',fill:'#3b82f6',stroke:'none'},{d:'M 54.505 4.916 l 0.000 54.143 a 3.485 3.485 0.000 0 1 -3.485 3.482 l -5.583 0.000 L 45.437 1.434 l 5.583 0.000 A 3.485 3.485 0.000 0 1 54.505 4.916 Z',fill:'#3b82f6',stroke:'none'},{d:'M 18.559 1.434 L 18.559 62.566 l -5.586 0.000 a 3.478 3.478 0.000 0 1 -3.478 -3.482 l 0.000 -54.143 a 3.478 3.478 0.000 0 1 3.478 -3.482 Z',fill:'#3b82f6',stroke:'none'},{d:'M 54.505 4.916 l 0.000 54.143 a 3.485 3.485 0.000 0 1 -3.485 3.482 l -5.583 0.000 L 45.437 1.434 l 5.583 0.000 A 3.485 3.485 0.000 0 1 54.505 4.916 Z',fill:'#3b82f6',stroke:'none'},{d:'M 38.169 15.415 a 3.098 3.098 0.000 0 1 0.000 6.192 l -12.342 0.000 a 3.098 3.098 0.000 0 1 0.000 -6.192 l 12.342 0.000 m 0.000 -1.793 l -12.342 0.000 a 4.891 4.891 0.000 0 0 -4.887 4.891 l 0.000 0.000 a 4.887 4.887 0.000 0 0 4.887 4.887 l 12.342 0.000 a 4.887 4.887 0.000 0 0 4.887 -4.887 l 0.000 0.000 a 4.891 4.891 0.000 0 0 -4.887 -4.891 Z',fill:'#3b82f6',stroke:'none'}]},
  signal_stripper: {viewBox:'0 0 64 64', paths:[{d:'M 11.405 26.180 L 52.593 26.180 A 0.737 0.737 0.000 0 1 53.330 26.917 L 53.330 26.920 A 0.737 0.737 0.000 0 1 52.593 27.657 L 11.405 27.657 A 0.737 0.737 0.000 0 1 10.668 26.920 L 10.668 26.917 A 0.737 0.737 0.000 0 1 11.405 26.180 Z',fill:'#3b82f6',stroke:'none'},{d:'M 54.585 28.832 l -45.164 0.000 a 1.510 1.510 0.000 0 0 -1.510 1.507 L 7.911 36.313 a 1.510 1.510 0.000 0 0 1.510 1.507 l 45.164 0.000 a 1.505 1.505 0.000 0 0 1.510 -1.507 L 56.095 30.339 A 1.505 1.505 0.000 0 0 54.585 28.832 Z m -42.116 5.677 L 11.477 34.509 a 0.327 0.327 0.000 0 1 -0.310 -0.177 a 0.443 0.443 0.000 0 1 -0.044 -0.186 l 0.000 -1.662 l 1.352 0.000 l -0.097 0.357 l -0.773 0.000 l 0.000 0.438 l 0.817 0.000 l -0.097 0.349 l -0.720 0.000 L 11.604 34.013 a 0.144 0.144 0.000 0 0 0.141 0.136 l 0.831 0.000 Z m 1.444 0.000 L 13.416 34.509 l -0.671 -2.028 l 0.490 0.000 l 0.000 0.000 l 0.424 1.385 l 0.432 -1.385 l 0.482 0.000 Z m 2.297 0.000 l -0.984 0.000 a 0.310 0.310 0.000 0 1 -0.310 -0.177 a 0.443 0.443 0.000 0 1 -0.044 -0.186 l 0.000 -1.662 l 1.344 0.000 l -0.097 0.357 L 15.356 32.841 l 0.000 0.438 l 0.831 0.000 l -0.103 0.357 L 15.356 33.636 L 15.356 34.013 a 0.127 0.127 0.000 0 0 0.133 0.136 l 0.831 0.000 Z m 1.590 0.000 l -0.366 -0.668 l -0.163 -0.291 l 0.150 0.000 a 0.355 0.355 0.000 0 0 0.000 -0.707 l -0.247 0.000 l 0.000 1.679 l -0.482 0.000 l 0.000 -2.037 l 0.892 0.000 a 0.646 0.646 0.000 0 1 0.646 0.648 L 18.229 33.182 a 0.637 0.637 0.000 0 1 -0.371 0.587 l 0.446 0.729 Z m 1.723 0.000 l -0.482 0.000 l 0.000 -1.662 l -0.554 0.000 l 0.000 -0.357 l 1.613 0.000 l -0.097 0.357 l -0.468 0.000 Z m 1.798 0.000 l 0.000 0.000 l -0.429 -1.419 l -0.432 1.427 l -0.482 0.000 l 0.668 -2.023 l 0.499 0.000 l 0.659 2.023 Z m 2.111 0.000 l -0.707 0.000 a 0.698 0.698 0.000 0 1 -0.698 -0.693 L 22.028 33.182 a 0.695 0.695 0.000 0 1 0.698 -0.690 l 0.765 0.000 l -0.103 0.349 l -0.554 0.000 a 0.327 0.327 0.000 0 0 -0.327 0.327 l 0.000 0.662 a 0.332 0.332 0.000 0 0 0.327 0.327 l 0.693 0.000 Z',fill:'#3b82f6',stroke:'none'},{d:'M 57.538 29.679 l 3.746 0.000 a 1.607 1.607 0.000 0 1 1.607 1.607 l 0.000 4.140 a 1.607 1.607 0.000 0 1 -1.607 1.607 L 57.538 37.033 a 0.000 0.000 0.000 0 1 0.000 0.000 L 57.538 29.679 A 0.000 0.000 0.000 0 1 57.538 29.679 Z',fill:'#3b82f6',stroke:'none'},{d:'M 6.462 37.019 L 2.715 37.019 a 1.607 1.607 180.000 0 1 -1.607 -1.607 L 1.108 31.287 a 1.607 1.607 180.000 0 1 1.607 -1.607 L 6.462 29.679 a 0.000 0.000 0.000 0 1 0.000 0.000 L 6.462 37.019 a 0.000 0.000 0.000 0 1 0.000 0.000 Z',fill:'#3b82f6',stroke:'none'}]},
  splitter: {viewBox:'0 0 64 64', paths:[{d:'M 20.823 36.762 l 6.526 3.530 c 0.197 0.105 0.400 -0.129 0.268 -0.308 l -2.362 -3.283 c -0.052 -0.074 -0.052 -0.172 0.000 -0.243 l 2.362 -3.255 c 0.129 -0.182 -0.074 -0.416 -0.271 -0.308 l -6.523 3.499 C 20.678 36.472 20.678 36.681 20.823 36.762 z',fill:'#3b82f6',stroke:'none'},{d:'M 50.701 10.293 H 13.367 c -1.679 0.000 -3.040 1.361 -3.040 3.040 v 37.334 c 0.000 1.679 1.361 3.040 3.040 3.040 h 37.334 c 1.679 0.000 3.040 -1.361 3.040 -3.040 V 13.333 C 53.741 11.654 52.380 10.293 50.701 10.293 z M 31.861 43.540 c 0.000 0.915 -0.588 1.608 -1.250 1.494 l -11.793 -3.366 c -0.548 -0.102 -0.967 -0.742 -0.967 -1.494 v -16.348 c 0.000 -0.764 0.416 -1.404 0.967 -1.494 l 11.793 -3.366 c 0.662 -0.123 1.250 0.579 1.250 1.485 V 43.540 z',fill:'#3b82f6',stroke:'none'},{d:'M 8.885 26.894 h -4.380 c -0.890 0.000 -1.611 -0.721 -1.611 -1.611 v -8.245 c 0.000 -0.890 0.721 -1.611 1.611 -1.611 h 4.380 V 26.894 z',fill:'#3b82f6',stroke:'none'},{d:'M 55.099 26.268 h 4.380 c 0.890 0.000 1.611 0.721 1.611 1.611 v 8.245 c 0.000 0.890 -0.721 1.611 -1.611 1.611 h -4.380 V 26.268 z',fill:'#3b82f6',stroke:'none'},{d:'M 8.885 48.357 h -4.380 c -0.890 0.000 -1.611 -0.721 -1.611 -1.611 v -8.245 c 0.000 -0.890 0.721 -1.611 1.611 -1.611 h 4.380 V 48.357 z',fill:'#3b82f6',stroke:'none'}]},
});

const SUBCAT_ICON_MAP={
  // Chinese names
  '数字基站':'base_station','数字信道机':'mark1000','信道机':'mark1000','广播多频点调频处理器':'fm_processor',
  '室外天线':'antenna_outdoor','室内天线':'antenna_indoor','防爆天线':'antenna_exproof',
  '光纤远端直放站':'oru','壁挂光纤远端直放站':'oru_wall','壁挂式光纤远端直放站':'oru_wall',
  '光纤近端机':'omu','射频直放站':'rf_amplifier','直放站配件':'generic',
  '双工器':'combiner','系统合路器':'combiner','合路器':'combiner','信号剥离器':'signal_stripper',
  '分路器':'splitter','功分器':'splitter','多信道分合路器':'splitter_3','一体化分合路矩阵':'matrix',
  '耦合器':'coupler','分配器':'splitter',
  '壁挂ORU':'oru_wall','壁挂式ORU':'oru_wall','MARK1000':'mark1000','MARK 1000':'mark1000',
  '数字对讲机':'radio_handheld','手持对讲机':'radio_handheld','带屏对讲机':'radio_display','显示对讲机':'radio_display',
  '多联充电器':'multi_charger','充电柜':'charging_cabinet','充电器':'multi_charger','电池板':'battery',
  '射频放大器':'rf_amplifier','平板天线':'antenna_panel','基站':'base_station',
  '射频电缆及配件':'cable_coax','光纤电缆及配件':'cable_fiber','衰减器':'attenuator',
  '馈线接地卡':'grounding','交换机':'switch','天线配件':'connector','直流隔断器':'dc_blocker',
  '终端负载':'load','机柜':'base_station','防爆盒':'base_station',
  '应用功能':'software','许可证':'license','服务软件':'software','服务器主机':'server',
  '主站频率占用费':'service','对讲机频率占用费':'service','施工附件':'service',
  '电磁环境检测及申报报告费':'service','调试开通':'service',
  // English names (SG NAS)
  'Base station':'bbu','Digital Channel Machine':'mark1000','Channel Machine':'mark1000','FM Broadcast':'fm_processor',
  'Indoor antenna':'antenna_indoor','Outdoor antenna':'antenna_outdoor','Explosion-proof antenna':'antenna_exproof',
  'ORU':'oru','Wall ORU':'oru_wall','Wall-mounted ORU':'oru_wall','OMU':'omu','RF BDA':'oru_wall','RF Repeater':'oru_wall',
  'RF Combiner':'combiner','Hybrid Combiner':'combiner','System Combiner':'combiner',
  'Duplex':'combiner','Signal Stripper':'signal_stripper','Splitter':'splitter','Power Divider':'splitter',
  'Multi-Coupler':'coupler','Coupler':'coupler','Matrix':'matrix',
  'MARK1000':'mark1000','MARK 1000':'mark1000',
  'Two-way radio':'radio_handheld','Handheld radio':'radio_handheld','Battery':'battery','Charge':'charger',
  'RF Cable':'cable_coax','Fiber Cable':'cable_fiber','Attenuator':'attenuator',
  'Grounding':'grounding','Switch':'switch','Antenna Accessories':'connector',
  'DC Block':'dc_blocker','Dummy Load':'load','Cabinet':'cabinet','Explosion-proof box':'cabinet',
  'License':'license','Software':'software','Applications':'software','Server':'server',
};

// ====== STATE ======
let SUBCATEGORIES = {};
let PRODUCTS = [];
const NODE_SIZE=64, LABEL_OFFSET=12;
let nodes=[],edges=[],nodeIdCounter=100,edgeIdCounter=200;
let selectedNodeId=null,selectedEdgeId=null,selectedNodeIds=new Set(),selectedEdgeIds=new Set(),currentTool='select';
let clipboard=null,dragStartPositions=null;
let viewX=0,viewY=0,scale=1;
let isDragging=false,dragNodeId=null,dragOffsetX=0,dragOffsetY=0;
let isPanning=false,panStartX=0,panStartY=0,panViewX=0,panViewY=0;
let isBoxSelecting=false,boxSelectStart=null;
let isSpaceDown=false;
let isConnecting=false,connSourceId=null,connSourcePort='';
let polylineWaypoints=[];  // waypoints being placed during polyline drawing
let pendingEdge=null,defaultRouteMode='ortho3',popupShowTime=0;
let isDraggingMid=false,dragMidEdgeId=null;
let isReconnecting=false,reconnectEdgeId=null,reconnectEnd='';
let hasUnsavedChanges=false;
let undoStack=[],undoIndex=-1;const MAX_UNDO=50;
let _autoSaveTimer=null;const AUTO_SAVE_INTERVAL=120000; // 2 minutes
let dragMoved=false,midDragMoved=false,_propEditing=false,_propEditTimer=null;

// ====== VIEW MANAGEMENT (Floor Plan) ======
// currentView: 'topology' | 'fp_1' | 'fp_2' ...
let currentView = 'topology';
let exportBlackMode=false;
let displaySettings={cableWidth:1,cableBlack:false,cableLabel:true,cableLength:true,iconWidth:1,iconBlack:false,iconLabel:true,iconModel:true,showCoverage:'individual',showCoverageInner:true,showCoverageMid:true,coverageFill:true,coverageMode:'circles'};
let floorPlanIdCounter = 1;
let topoViewX = 0, topoViewY = 0, topoScale = 1;
let topoAreas = []; // Areas drawn on the topology view

// ====== SVG HELPERS ======
function _buildPathAttrs(a){
  const stroke=a.stroke?(displaySettings.iconBlack?'#1e293b':a.stroke):null;
  const fill=a.fill?(displaySettings.iconBlack&&a.fill!=='none'?'#1e293b':a.fill):null;
  const sw=a.strokeWidth?a.strokeWidth*displaySettings.iconWidth:null;
  return [`d="${a.d}"`,fill?`fill="${fill}"`:'',stroke?`stroke="${stroke}"`:'',
    sw?`stroke-width="${sw}"`:'',a.opacity!==undefined?`opacity="${a.opacity}"`:'',
    a.strokeDasharray?`stroke-dasharray="${a.strokeDasharray}"`:''].filter(Boolean).join(' ');
}

function getEffectiveCableWidth(w){return (w||2)*displaySettings.cableWidth}
function getEffectiveCableColor(c){return displaySettings.cableBlack?'#1e293b':c||'#64748b'}
function getEffectiveIconStroke(sw){return sw?(sw*displaySettings.iconWidth):sw}

function _dsOptBtns(key,options){
  return options.map(([v,label])=>`<button class="ds-opt${displaySettings[key]==v?' active':''}" onclick="updateDisplaySetting('${key}',${typeof v==='boolean'?v:v})">${label}</button>`).join('');
}
function _dsToggle(key,label){
  const on=displaySettings[key];
  return `<label class="ds-toggle"><input type="checkbox" ${on?'checked':''} onchange="updateDisplaySetting('${key}',this.checked)"><span>${label}</span></label>`;
}
function renderDisplaySettingsHTML(){
  return `
    <div class="props-divider"></div>
    <div class="ds-section">
      <div class="ds-title">${_t('线缆')}</div>
      <div class="ds-row"><span class="ds-label">${_t('粗细')}</span><div class="ds-opts">${_dsOptBtns('cableWidth',[[1,'1x'],[1.5,'1.5x'],[2,'2x']])}</div></div>
      <div class="ds-row"><span class="ds-label">${_t('颜色')}</span><div class="ds-opts">${_dsOptBtns('cableBlack',[[false,_t('原色')],[true,_t('黑色')]])}</div></div>
      <div class="ds-toggles">${_dsToggle('cableLabel',_t('标签'))}${_dsToggle('cableLength',_t('长度'))}</div>
    </div>
    <div class="ds-section">
      <div class="ds-title">${_t('图标')}</div>
      <div class="ds-row"><span class="ds-label">${_t('粗细')}</span><div class="ds-opts">${_dsOptBtns('iconWidth',[[1,'1x'],[1.5,'1.5x'],[2,'2x']])}</div></div>
      <div class="ds-row"><span class="ds-label">${_t('颜色')}</span><div class="ds-opts">${_dsOptBtns('iconBlack',[[false,_t('原色')],[true,_t('黑色')]])}</div></div>
      <div class="ds-toggles">${_dsToggle('iconLabel',_t('标签'))}${_dsToggle('iconModel',_t('型号'))}</div>
    </div>
    <div class="ds-section">
      <div class="ds-title">${_t('覆盖')}</div>
      <div class="ds-row"><span class="ds-label">${_t('覆盖')}</span><div class="ds-opts">${['off','individual','all'].map(v=>`<button class="ds-opt${displaySettings.showCoverage===v?' active':''}" onclick="updateDisplaySetting('showCoverage','${v}')">${{off:_t('关闭'),individual:_t('依据天线'),all:_t('全部显示')}[v]}</button>`).join('')}</div></div>
      <div class="ds-row"><span class="ds-label">${_t('模式')}</span><div class="ds-opts">${['circles','heatmap'].map(v=>`<button class="ds-opt${displaySettings.coverageMode===v?' active':''}" onclick="updateDisplaySetting('coverageMode','${v}')">${v==='circles'?_t('圆圈'):_t('热力图')}</button>`).join('')}</div></div>
      ${displaySettings.coverageMode==='circles'?`
      <div class="ds-toggles">${_dsToggle('coverageFill',_t('填充色'))}</div>
      <div class="ds-toggles" style="padding-left:18px;gap:8px;">
        ${_dsToggle('showCoverageInner',_t('内圈'))}
        ${_dsToggle('showCoverageMid',_t('中圈'))}
      </div>`:
      `<div style="font-size:11px;color:var(--text-muted);padding:2px 4px;">${_t('环境在每个天线属性中单独设置')}</div>`}
    </div>`;
}

function updateDisplaySetting(key,val){
  pushHistoryProp();displaySettings[key]=val;hasUnsavedChanges=true;renderAll();
  // Refresh current props panel
  if(currentView==='topology')showTopologyProps();
  else if(typeof showFloorPlanProps==='function')showFloorPlanProps(currentView);
}

function showTopologyProps(){
  const panel=document.getElementById('propsPanel');
  panel.classList.add('visible');
  document.getElementById('propsTitle').textContent=_t('系统图属性');
  const nodeCount=nodes.filter(n=>!n.floor_id).length;
  const edgeCount=edges.length;
  const nameEl=document.getElementById('diagramNameInput');
  const nameVal=nameEl?(nameEl.value||nameEl.textContent||'').trim():'';
  const isRO=DIAGRAM_CONFIG.readOnly;
  const nameHTML=isRO
    ?`<div style="font-size:13px;font-weight:600;color:var(--text-primary)">${nameVal}</div>`
    :`<input class="props-input" value="${nameVal.replace(/"/g,'&quot;')}" oninput="document.getElementById('diagramNameInput').value=this.value;hasUnsavedChanges=true">`;
  document.getElementById('propsContent').innerHTML=`
    <div class="props-field"><span class="props-label">${_t('图纸名称')}</span>${nameHTML}</div>
    <div class="props-field"><span class="props-label">${_t('统计')}</span><div style="font-size:11px;color:var(--text-secondary);line-height:1.6;">${_t('节点')}: ${nodeCount}  ${_t('连线')}: ${edgeCount}</div></div>`+renderDisplaySettingsHTML();
}

function renderIconSVG(iconData,sz,x,y){
  if(!iconData)return '';
  if(typeof iconData==='string'){
    const vbM=iconData.match(/viewBox="([^"]*)"/);const vb=vbM?`viewBox="${vbM[1]}"`:'viewBox="0 0 64 64"';
    let svg=iconData.replace(/<svg[^>]*>/, `<svg x="0" y="0" width="${sz}" height="${sz}" ${vb} overflow="hidden" filter="url(#iconShadow)">`);
    if(displaySettings.iconWidth!==1)svg=svg.replace(/stroke-width="([^"]*)"/g,(_,v)=>`stroke-width="${parseFloat(v)*displaySettings.iconWidth}"`);
    if(displaySettings.iconBlack){svg=svg.replace(/stroke="(?!none)([^"]*)"/g,'stroke="#1e293b"');svg=svg.replace(/fill="(?!none|url)([^"]*)"/g,'fill="#1e293b"')}
    return `<g transform="translate(${x},${y})">${svg}</g>`;
  }
  let p='';iconData.paths.forEach(a=>{p+=`<path ${_buildPathAttrs(a)}/>`});
  return `<svg x="${x}" y="${y}" width="${sz}" height="${sz}" viewBox="${iconData.viewBox}" filter="url(#iconShadow)">${p}</svg>`;
}

function renderIconPanel(iconData){
  if(!iconData)return '<svg viewBox="0 0 64 64"><rect x="12" y="12" width="40" height="40" fill="#475569" opacity=".08" stroke="#64748b" stroke-width="2"/></svg>';
  if(typeof iconData==='string') return iconData.replace(/<svg[^>]*>/, m => { const vb = m.match(/viewBox="([^"]*)"/); return `<svg viewBox="${vb?vb[1]:'0 0 64 64'}">`; });
  let p='';iconData.paths.forEach(a=>{p+=`<path ${_buildPathAttrs(a)}/>`});
  return `<svg viewBox="${iconData.viewBox}">${p}</svg>`;
}

function cableLineSVG(k,w,h){
  const c=CABLE_TYPES[k];if(!c)return '';
  return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}"><line x1="2" y1="${h/2}" x2="${w-2}" y2="${h/2}" stroke="${c.color}" stroke-width="${Math.min(c.width,h-2)}" ${c.dash?`stroke-dasharray="${c.dash}"`:''} stroke-linecap="round"/></svg>`;
}

// 产品级别关键词 → iconKey 映射（优先级高于子类目）。
// 例如一个子类目下有多种型号，不同型号用不同图标时：按产品名或型号里的关键字区分。
const PRODUCT_NAME_ICON_MAP = {
  '壁挂': 'oru_wall', 'wall-mounted': 'oru_wall', 'wall mounted': 'oru_wall',
  'mark1000': 'mark1000', 'mark 1000': 'mark1000',
  '充电柜': 'charging_cabinet', 'charging cabinet': 'charging_cabinet',
  '多联充电器': 'multi_charger', 'multi charger': 'multi_charger',
  '平板天线': 'antenna_panel', 'panel antenna': 'antenna_panel',
  '射频放大器': 'rf_amplifier', 'rf amplifier': 'rf_amplifier',
  '信号剥离器': 'signal_stripper', 'signal stripper': 'signal_stripper',
};

function getIconForProduct(product,subcatName,subcatIconKey){
  if(product.iconSvg) return product.iconSvg;
  // 产品名/型号关键字匹配（优先于子类目 icon）
  const text = ((product.name||'') + ' ' + (product.model||'')).toLowerCase();
  for(const kw in PRODUCT_NAME_ICON_MAP){
    if(text.includes(kw.toLowerCase())){
      const icon = DEFAULT_DEVICE_ICONS[PRODUCT_NAME_ICON_MAP[kw]];
      if(icon) return icon;
    }
  }
  if(subcatIconKey && DEFAULT_DEVICE_ICONS[subcatIconKey]) return DEFAULT_DEVICE_ICONS[subcatIconKey];
  if(subcatName){for(const k in SUBCAT_ICON_MAP){if(subcatName.includes(k))return DEFAULT_DEVICE_ICONS[SUBCAT_ICON_MAP[k]]}}
  return DEFAULT_DEVICE_ICONS.generic;
}

function _catIcon(name){
  const ms='material-symbols-outlined';
  const icons={'基站':'cell_tower','Basestation':'cell_tower',
    '天线':'settings_input_antenna','Antenna':'settings_input_antenna',
    '直放':'broadcast_on_personal','BDA':'broadcast_on_personal',
    '合路':'hub','Combiner':'hub',
    '功率':'power','Splitter':'power',
    '耦合':'power','Coupler':'power',
    '对讲':'perm_phone_msg','Radio':'perm_phone_msg',
    '配件':'extension','Accessories':'extension',
    '服务':'support_agent','Commissioning':'support_agent',
    '应用':'apps','Application':'apps'};
  for(const k in icons){if((name||'').includes(k))return `<span class="${ms}" style="font-size:16px;">${icons[k]}</span>`}
  return `<span class="${ms}" style="font-size:16px;">category</span>`;
}
function toggleCategory(el){
  const wasOpen=el.classList.contains('open');
  document.querySelectorAll('.category-header.open').forEach(h=>h.classList.remove('open'));
  if(!wasOpen)el.classList.add('open');
}

// ====== PRODUCT PANEL (Category → Subcategory tree) ======
function buildProductPanel(categories){
  const panel=document.getElementById('productPanel');
  if(!categories||!categories.length){
    panel.innerHTML='<div style="padding:20px;text-align:center;color:var(--text-muted);font-size:12px;">'+_t('暂无产品')+'</div>';
    return;
  }
  SUBCATEGORIES={};
  PRODUCTS=[];
  let h='';
  categories.forEach(cat=>{
    const subs=cat.subcategories||[];
    let totalProducts=0;
    let subcatHtml='';
    subs.forEach(sub=>{
      const products=sub.products||[];
      products.forEach(p=>{
        p.iconData=getIconForProduct(p,sub.name,sub.iconKey);
        p.subcategoryId=sub.id;p.subcategoryName=sub.name;
        PRODUCTS.push(p);
      });
      let repIcon;
      let mapped=null;
      for(const k in SUBCAT_ICON_MAP){if((sub.name||'').includes(k)){mapped=DEFAULT_DEVICE_ICONS[SUBCAT_ICON_MAP[k]];break;}}
      if(mapped){repIcon=mapped}
      else if(sub.iconKey && DEFAULT_DEVICE_ICONS[sub.iconKey]){repIcon=DEFAULT_DEVICE_ICONS[sub.iconKey]}
      else{repIcon=DEFAULT_DEVICE_ICONS.generic}
      sub.iconData=repIcon;
      sub.color=cat.color||'#64748b';
      sub.categoryName=cat.name;
      SUBCATEGORIES[sub.id]=sub;
      totalProducts+=products.length;
      subcatHtml+=`<div class="subcat-item" draggable="true" data-subid="${sub.id}" data-name="${sub.name}" data-products="${products.map(p=>p.model||p.mn||p.productName).join(',')}">
        <div class="item-icon">${renderIconPanel(repIcon)}</div>
        <div style="flex:1;min-width:0;">
          <div style="font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${sub.name}</div>
        </div>
        <span class="subcat-count">${products.length}</span>
      </div>`;
    });
    h+=`<div class="category-group">
      <div class="category-header" onclick="toggleCategory(this)">
        <span class="arrow">▶</span>
        <span class="cat-icon" style="color:${cat.color||'#64748b'}">${_catIcon(cat.name)}</span>
        <span>${cat.name}</span>
        <span style="margin-left:auto;font-size:11px;color:var(--text-muted);">${totalProducts}</span>
      </div>
      <div class="category-items">${subcatHtml}</div>
    </div>`;
  });
  panel.innerHTML=h;
  panel.querySelectorAll('.subcat-item').forEach(el=>{
    el.addEventListener('dragstart',e=>{
      e.dataTransfer.setData('text/plain',el.dataset.subid);
      e.dataTransfer.effectAllowed='copy';
    });
  });
}

document.getElementById('productSearch').addEventListener('input',function(){
  const q=this.value.toLowerCase();
  document.querySelectorAll('.subcat-item').forEach(el=>{
    const name=el.dataset.name.toLowerCase();
    const models=(el.dataset.products||'').toLowerCase();
    el.style.display=(name.includes(q)||models.includes(q))?'':'none';
  });
  // Also filter existing devices
  document.querySelectorAll('.existing-device-item').forEach(el=>{
    const name=(el.dataset.name||'').toLowerCase();
    el.style.display=name.includes(q)?'':'none';
  });
  if(q){
    document.querySelectorAll('.category-header').forEach(h=>h.classList.add('open'));
    document.querySelectorAll('.category-items').forEach(c=>c.style.display='block');
  }
});

// ====== PANEL TAB SWITCHING ======
let _activePanelTab='products';

function switchPanelTab(tab){
  _activePanelTab=tab;
  document.querySelectorAll('.panel-tab').forEach(t=>t.classList.toggle('active',t.dataset.tab===tab));
  const existSec=document.getElementById('existingDevicesSection');
  const prodSec=document.getElementById('productPanel');
  if(existSec)existSec.style.display=tab==='existing'?'block':'none';
  if(prodSec)prodSec.style.display=tab==='products'?'block':'none';
}

// ====== EXISTING DEVICES PANEL ======
function buildExistingDevicesPanel(){
  const section=document.getElementById('existingDevicesSection');
  const panel=document.getElementById('existingDevicesPanel');
  const tabs=document.getElementById('panelTabs');
  if(!section||!panel)return;
  const isFloor=currentView!=='topology';
  // Show/hide tabs
  if(tabs)tabs.style.display=isFloor?'flex':'none';
  if(!isFloor){
    section.style.display='none';
    document.getElementById('productPanel').style.display='block';
    return;
  }
  // Default to "products" tab when entering floor plan mode
  if(_activePanelTab!=='existing'&&_activePanelTab!=='products')_activePanelTab='products';
  switchPanelTab(_activePanelTab);
  // Build existing devices list
  if(!nodes.length){panel.innerHTML='<div style="padding:8px 10px;font-size:11px;color:var(--text-muted);">'+_t('暂无设备')+'</div>';document.getElementById('existingDevicesCount').textContent='0';return}
  // Count placed qty across ALL floor plans (sum pl.qty)
  const placementCount={};
  if(typeof floorPlans!=='undefined')floorPlans.forEach(fp=>{fp.placements.forEach(p=>{placementCount[p.node_id]=(placementCount[p.node_id]||0)+(p.qty||1)})});
  document.getElementById('existingDevicesCount').textContent=nodes.length;
  let h='';
  nodes.forEach(n=>{
    const qty=n.qty||1;
    const used=placementCount[n.id]||0;
    const remaining=qty-used;
    const allUsed=remaining<=0;
    h+=`<div class="existing-device-item${allUsed?' all-placed':''}" ${allUsed?'':'draggable="true"'} data-existing-node-id="${n.id}" data-name="${n.name} ${n.model||''}">
      <div class="item-icon">${renderIconPanel(n.iconData).replace('<svg','<svg width="24" height="24"')}</div>
      <div style="flex:1;min-width:0;">
        <div style="font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${n.name}</div>
        ${n.model?`<div style="font-size:9px;color:var(--text-muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${n.model}</div>`:''}
      </div>
      ${allUsed?`<span class="placed-badge" style="color:var(--text-muted);">${used}/${qty}</span>`
        :used>0?`<span class="placed-badge" style="color:#f59e0b;">${remaining}/${qty}</span>`
        :qty>1?`<span class="placed-badge" style="color:var(--text-secondary);">×${qty}</span>`:''}
    </div>`;
  });
  panel.innerHTML=h;
  panel.querySelectorAll('.existing-device-item:not(.all-placed)').forEach(el=>{
    el.addEventListener('dragstart',e=>{
      e.dataTransfer.setData('application/x-existing-node',el.dataset.existingNodeId);
      e.dataTransfer.effectAllowed='copy';
    });
  });
}

// ====== DRAG & DROP ======
// wrapper is defined in template inline script (before this file loads)
wrapper.addEventListener('dragover',e=>{e.preventDefault();e.dataTransfer.dropEffect='copy';const di=document.getElementById('dropIndicator'),r=wrapper.getBoundingClientRect();di.style.display='block';di.style.left=(e.clientX-r.left-36)+'px';di.style.top=(e.clientY-r.top-36)+'px';di.style.width='72px';di.style.height='72px';di.innerHTML='<div style="width:72px;height:72px;border:2px dashed #3b82f6;border-radius:12px;background:rgba(59,130,246,.06);"></div>'});
wrapper.addEventListener('dragleave',()=>{document.getElementById('dropIndicator').style.display='none'});
wrapper.addEventListener('drop',e=>{
  e.preventDefault();document.getElementById('dropIndicator').style.display='none';
  if(DIAGRAM_CONFIG.readOnly)return;
  const r=wrapper.getBoundingClientRect(),cx=(e.clientX-r.left-viewX)/scale,cy=(e.clientY-r.top-viewY)/scale;

  // Check for existing device drop (floor plan only)
  const existingNodeId=e.dataTransfer.getData('application/x-existing-node');
  if(existingNodeId && currentView!=='topology'){
    placeExistingNodeOnFloor(parseInt(existingNodeId),cx-NODE_SIZE/2,cy-NODE_SIZE/2);
    return;
  }

  const subId=parseInt(e.dataTransfer.getData('text/plain'));
  const sub=SUBCATEGORIES[subId];
  if(!sub)return;
  if(currentView==='topology'){
    addNode(sub,cx-NODE_SIZE/2,cy-NODE_SIZE/2);
  } else {
    // Floor plan view: add node + placement
    addNodeToFloorPlan(sub,cx-NODE_SIZE/2,cy-NODE_SIZE/2);
  }
});

// ====== NODE MANAGEMENT ======
function addNode(sub,x,y){
  if(DIAGRAM_CONFIG.readOnly)return null;
  const products=sub.products||[];
  const firstProduct=products[0];
  const node={
    id:nodeIdCounter++,
    subcategoryId:sub.id,
    selectedProductId:products.length===1?(firstProduct.id):null,
    name:sub.name,
    model:products.length===1?(firstProduct.model||firstProduct.mn||firstProduct.productName):'',
    category:sub.categoryName||'',
    color:sub.color||'#64748b',
    iconData:sub.iconData||DEFAULT_DEVICE_ICONS.generic,
    products:products,
    x:Math.round(x/10)*10,y:Math.round(y/10)*10,w:NODE_SIZE,h:NODE_SIZE,qty:1,label:'',hideLabel:false,
    floor_id:null, area_label:'', floor_label:'',
    // 楼栋归属：null = 中央机房（共享），跨楼栋设备
    building_id:null,
    // 是否出现在系统图。系统图直接添加默认 true；平面图新建默认 false（要点同步按钮才进系统图）
    in_topology:true
  };
  pushHistory();nodes.push(node);hasUnsavedChanges=true;renderAll();selectNode(node.id);return node;
}

// addNodeToFloorPlan() is defined in system-diagram-floorplan.js

function addTextNode(){
  if(DIAGRAM_CONFIG.readOnly)return;
  pushHistory();
  const cx=(wrapper.clientWidth/2-viewX)/scale,cy=(wrapper.clientHeight/2-viewY)/scale;
  nodes.push({id:nodeIdCounter++,subcategoryId:null,selectedProductId:null,name:_t('文本标注'),model:_t('双击编辑'),category:_t('标注'),color:'#64748b',iconData:DEFAULT_DEVICE_ICONS.text_note,products:[],x:cx-32,y:cy-32,w:NODE_SIZE,h:NODE_SIZE,qty:1,label:'',hideLabel:false,floor_id:null,area_label:'',floor_label:''});
  hasUnsavedChanges=true;renderAll();selectNode(nodeIdCounter-1);
}

// ====== PORT POSITIONS ======
function getPortPos(node,port){const cx=node.x+node.w/2,cy=node.y+node.h/2,R=node.w/2+8,D=R*.7071;switch(port){case'top':return{x:cx,y:cy-R};case'right':return{x:cx+R,y:cy};case'bottom':return{x:cx,y:cy+R};case'left':return{x:cx-R,y:cy};case'top-left':return{x:cx-D,y:cy-D};case'top-right':return{x:cx+D,y:cy-D};case'bottom-left':return{x:cx-D,y:cy+D};case'bottom-right':return{x:cx+D,y:cy+D};default:return{x:cx,y:cy}}}
function portDir(port){const D=.707;switch(port){case'top':return{x:0,y:-1};case'right':return{x:1,y:0};case'bottom':return{x:0,y:1};case'left':return{x:-1,y:0};case'top-left':return{x:-D,y:-D};case'top-right':return{x:D,y:-D};case'bottom-left':return{x:-D,y:D};case'bottom-right':return{x:D,y:D};default:return{x:0,y:0}}}

// ====== EDGE PATH BUILDING ======
function roundedOrthoPath(pts,r){
  let d=`M${pts[0].x},${pts[0].y}`;
  for(let i=1;i<pts.length-1;i++){
    const prev=pts[i-1],cur=pts[i],next=pts[i+1];
    const d1x=cur.x-prev.x,d1y=cur.y-prev.y,d2x=next.x-cur.x,d2y=next.y-cur.y;
    const len1=Math.abs(d1x)+Math.abs(d1y),len2=Math.abs(d2x)+Math.abs(d2y);
    const cr=Math.min(r,len1/2,len2/2);
    const s1x=Math.sign(d1x),s1y=Math.sign(d1y),s2x=Math.sign(d2x),s2y=Math.sign(d2y);
    d+=` L${cur.x-s1x*cr},${cur.y-s1y*cr} Q${cur.x},${cur.y} ${cur.x+s2x*cr},${cur.y+s2y*cr}`;
  }
  d+=` L${pts[pts.length-1].x},${pts[pts.length-1].y}`;return d;
}

function polylinePath(pts,r){
  if(pts.length<2)return'';
  if(pts.length===2)return`M${pts[0].x},${pts[0].y} L${pts[1].x},${pts[1].y}`;
  let d=`M${pts[0].x},${pts[0].y}`;
  for(let i=1;i<pts.length-1;i++){
    const prev=pts[i-1],cur=pts[i],next=pts[i+1];
    const d1x=cur.x-prev.x,d1y=cur.y-prev.y,d2x=next.x-cur.x,d2y=next.y-cur.y;
    const len1=Math.sqrt(d1x*d1x+d1y*d1y),len2=Math.sqrt(d2x*d2x+d2y*d2y);
    if(len1===0||len2===0){d+=` L${cur.x},${cur.y}`;continue}
    const cr=Math.min(r,len1/2,len2/2);
    d+=` L${cur.x-d1x/len1*cr},${cur.y-d1y/len1*cr} Q${cur.x},${cur.y} ${cur.x+d2x/len2*cr},${cur.y+d2y/len2*cr}`;
  }
  d+=` L${pts[pts.length-1].x},${pts[pts.length-1].y}`;return d;
}

function buildEdgePath(edge){
  const src=nodes.find(n=>n.id===edge.sourceId),tgt=nodes.find(n=>n.id===edge.targetId);
  if(!src||!tgt)return '';
  const sp=getPortPos(src,edge.sourcePort),tp=getPortPos(tgt,edge.targetPort);
  const mode=edge.routeMode||'bezier',R=12;
  if(mode==='straight')return{path:`M${sp.x},${sp.y} L${tp.x},${tp.y}`,sp,tp,pts:null};
  if(edge.waypoints&&edge.waypoints.length){const wpts=[sp,...edge.waypoints,tp];return{path:polylinePath(wpts,R),sp,tp,pts:wpts,waypoints:edge.waypoints}}
  if(mode==='bezier'){const tension=Math.max(40,Math.min(Math.abs(tp.x-sp.x),Math.abs(tp.y-sp.y),120)*.5);const sd=portDir(edge.sourcePort),td=portDir(edge.targetPort);const cp1={x:sp.x+sd.x*tension,y:sp.y+sd.y*tension},cp2={x:tp.x+td.x*tension,y:tp.y+td.y*tension};return{path:`M${sp.x},${sp.y} C${cp1.x},${cp1.y} ${cp2.x},${cp2.y} ${tp.x},${tp.y}`,sp,tp,pts:null,cp1,cp2}}
  const isH=(edge.sourcePort==='left'||edge.sourcePort==='right'||edge.sourcePort==='top-left'||edge.sourcePort==='bottom-left'||edge.sourcePort==='top-right'||edge.sourcePort==='bottom-right');
  if(mode==='ortho2'){let corner=isH?{x:tp.x,y:sp.y}:{x:sp.x,y:tp.y};return{path:roundedOrthoPath([sp,corner,tp],R),sp,tp,pts:[sp,corner,tp]}}
  if(mode==='ortho3'){let c1,c2;if(isH){const midX=edge.midPos!==undefined?edge.midPos:(sp.x+tp.x)/2;c1={x:midX,y:sp.y};c2={x:midX,y:tp.y}}else{const midY=edge.midPos!==undefined?edge.midPos:(sp.y+tp.y)/2;c1={x:sp.x,y:midY};c2={x:tp.x,y:midY}}return{path:roundedOrthoPath([sp,c1,c2,tp],R),sp,tp,pts:[sp,c1,c2,tp],c1,c2,isH}}
  return{path:`M${sp.x},${sp.y} L${tp.x},${tp.y}`,sp,tp,pts:null};
}

function getPathMidpoint(result,edge){
  const mode=edge.routeMode||'bezier';
  if(mode==='bezier'&&result.cp1&&result.cp2){
    const s=result.sp,e=result.tp,c1=result.cp1,c2=result.cp2;
    return{x:.125*s.x+.375*c1.x+.375*c2.x+.125*e.x,y:.125*s.y+.375*c1.y+.375*c2.y+.125*e.y};
  }
  if(result.pts&&result.pts.length>=2){
    let totalLen=0;const segs=[];
    for(let i=1;i<result.pts.length;i++){
      const dx=result.pts[i].x-result.pts[i-1].x,dy=result.pts[i].y-result.pts[i-1].y;
      const len=Math.sqrt(dx*dx+dy*dy);segs.push({from:result.pts[i-1],to:result.pts[i],len});totalLen+=len;
    }
    let rem=totalLen/2;
    for(const seg of segs){
      if(rem<=seg.len){const r=seg.len>0?rem/seg.len:0;return{x:seg.from.x+(seg.to.x-seg.from.x)*r,y:seg.from.y+(seg.to.y-seg.from.y)*r};}
      rem-=seg.len;
    }
  }
  return{x:(result.sp.x+result.tp.x)/2,y:(result.sp.y+result.tp.y)/2};
}

// ====== SVG POINT CONVERSION ======
function svgPoint(e){const r=wrapper.getBoundingClientRect();return{x:(e.clientX-r.left-viewX)/scale,y:(e.clientY-r.top-viewY)/scale}}

// ====== CANVAS CONTROLS ======
function setTool(tool){
  if(DIAGRAM_CONFIG.readOnly&&tool!=='select')return;
  // Clean up calibration state when switching away
  if(currentTool==='calibrate'&&tool!=='calibrate'){
    if(typeof isCalibrating!=='undefined'){isCalibrating=false;calibrateStart=null}
    document.getElementById('tempLayer').innerHTML='';
  }
  currentTool=tool;
  document.getElementById('btnSelect').classList.toggle('active',tool==='select');
  document.getElementById('btnConnect').classList.toggle('active',tool==='connect');
  const btnArea=document.getElementById('btnAreaTool');
  if(btnArea)btnArea.classList.toggle('active',tool==='area');
  const btnCal=document.getElementById('btnCalibrate');
  if(btnCal)btnCal.classList.toggle('active',tool==='calibrate');
  document.getElementById('diagramCanvas').style.cursor=tool==='connect'||tool==='area'||tool==='calibrate'?'crosshair':'default';
}
const svg=document.getElementById('diagramCanvas');
svg.addEventListener('mousedown',e=>{if(e.target===svg||(e.target.tagName==='rect'&&!e.target.closest('.node-group')&&!e.target.closest('.mid-handle')&&!e.target.closest('#edgeHitLayer'))){
  // Click-persistent mode: during active connection, only allow panning — don't switch tools or clear selection
  if(!isConnecting&&currentTool!=='select'&&currentTool!=='area'&&currentTool!=='calibrate')setTool('select');
  // Alt/Option + left click: box select; otherwise: pan (preserves Mac trackpad three-finger drag = pan)
  if(e.button===0&&e.altKey&&currentTool==='select'&&!isConnecting){
    isBoxSelecting=true;boxSelectStart=svgPoint(e);
    panStartX=e.clientX;panStartY=e.clientY;
  }else{
    isPanning=true;panStartX=e.clientX;panStartY=e.clientY;panViewX=viewX;panViewY=viewY;
    if(isSpaceDown)document.getElementById('diagramCanvas').style.cursor='grabbing';
  }
  if(!isConnecting&&!isBoxSelecting){const isAreaClick=e.target.closest&&e.target.closest('.floor-area');if(!e.shiftKey&&!isAreaClick){selectedNodeIds=new Set();selectedEdgeIds=new Set();selectedNodeId=null;selectedEdgeId=null;if(typeof selectedAreaId!=='undefined')selectedAreaId=null;if(typeof selectedRouteId!=='undefined')selectedRouteId=null;renderAll();hideProps();if(typeof highlightConnectedInPanel==='function')highlightConnectedInPanel(null)}}}});
svg.addEventListener('wheel',e=>{e.preventDefault();zoomCanvas(e.deltaY>0?1/1.06:1.06,e.clientX,e.clientY)},{passive:false});

function getZoomLimits(){
  if(typeof getFloorPlan!=='function'||typeof currentView==='undefined')return{min:0.05,max:5};
  const fp=getFloorPlan(currentView);
  if(!fp||!fp.background)return{min:0.05,max:5};
  // 已标定的楼层：背景已在物理比例，限制最大缩放为150%
  if(fp.calibration&&fp.calibration.px_per_meter){
    const minZoom=Math.max(0.02,600/fp.background.width);
    return{min:minZoom,max:1.5};
  }
  // 未标定：保持原有逻辑
  const bgW=fp.background.width;
  if(fp.background.is_multi_res&&fp.background.resolutions){
    const best=fp.background.resolutions['8000']||fp.background.resolutions['4000'];
    if(best){
      const highestRes=Math.max(best.width,best.height);
      const maxZoom=Math.max(7,(highestRes*1.5)/bgW);
      const minZoom=Math.max(0.02,600/bgW);
      return{min:minZoom,max:Math.max(maxZoom,minZoom+0.01)};
    }
  }
  return{min:0.05,max:5};
}
function zoomCanvas(f,cx,cy){const old=scale;const limits=getZoomLimits();scale=Math.max(limits.min,Math.min(limits.max,scale*f));if(cx!==undefined){const r=wrapper.getBoundingClientRect();const mx=cx-r.left,my=cy-r.top;viewX=mx-(mx-viewX)*(scale/old);viewY=my-(my-viewY)*(scale/old)}updateTransform();document.getElementById('zoomLevel').textContent=Math.round(scale*100)+'%';if(typeof onScaleChanged==='function')onScaleChanged(scale)}
let _fitViewRetries=0;
function fitView(){
  const cw=wrapper.clientWidth,ch=wrapper.clientHeight;
  // If wrapper has no dimensions yet (page still laying out), retry
  if(cw<50||ch<50){
    if(_fitViewRetries<10){_fitViewRetries++;requestAnimationFrame(()=>setTimeout(fitView,50));return}
    _fitViewRetries=0;return resetZoom();
  }
  _fitViewRetries=0;
  const pad=80;let x1=Infinity,y1=Infinity,x2=-Infinity,y2=-Infinity;
  if(currentView==='topology'){
    if(!nodes.length&&!topoAreas.length)return resetZoom();
    nodes.forEach(n=>{x1=Math.min(x1,n.x);y1=Math.min(y1,n.y);x2=Math.max(x2,n.x+n.w);y2=Math.max(y2,n.y+n.h+30)});
    topoAreas.forEach(a=>{x1=Math.min(x1,a.x);y1=Math.min(y1,a.y);x2=Math.max(x2,a.x+a.width);y2=Math.max(y2,a.y+a.height)});
  } else {
    const fp=getFloorPlan(currentView);if(!fp)return resetZoom();
    // Include background dimensions
    if(fp.background){x1=Math.min(x1,0);y1=Math.min(y1,0);x2=Math.max(x2,fp.background.width||0);y2=Math.max(y2,fp.background.height||0)}
    // Include placed nodes
    if(fp.placements&&fp.placements.length){fp.placements.forEach(pl=>{const n=nodes.find(nd=>nd.id===pl.node_id);if(n){x1=Math.min(x1,pl.x);y1=Math.min(y1,pl.y);x2=Math.max(x2,pl.x+n.w);y2=Math.max(y2,pl.y+n.h+30)}})}
    if(x1===Infinity)return resetZoom();
  }
  const dw=x2-x1+pad*2,dh=y2-y1+pad*2;const limits=getZoomLimits();scale=Math.max(limits.min,Math.min(cw/dw,ch/dh,limits.max));viewX=(cw-dw*scale)/2-x1*scale+pad*scale;viewY=(ch-dh*scale)/2-y1*scale+pad*scale;updateTransform();document.getElementById('zoomLevel').textContent=Math.round(scale*100)+'%';if(typeof onScaleChanged==='function')onScaleChanged(scale);
}
function resetZoom(){scale=1;viewX=0;viewY=0;updateTransform();document.getElementById('zoomLevel').textContent='100%';if(typeof onScaleChanged==='function')onScaleChanged(scale)}
function updateTransform(){document.getElementById('canvasGroup').setAttribute('transform',`translate(${viewX},${viewY}) scale(${scale})`);updateMinimap()}
function updateInfo(){document.getElementById('canvasInfo').textContent=`${_t('节点')}: ${nodes.length} | ${_t('连线')}: ${edges.length}`}
function updateMinimap(){const mn=document.getElementById('minimapNodes');mn.innerHTML='';nodes.forEach(n=>{const r=document.createElementNS('http://www.w3.org/2000/svg','rect');r.setAttribute('x',n.x);r.setAttribute('y',n.y);r.setAttribute('width',n.w);r.setAttribute('height',n.h);r.setAttribute('fill',n.color);r.setAttribute('opacity',.6);r.setAttribute('rx',4);mn.appendChild(r)});edges.forEach(edge=>{const s=nodes.find(n=>n.id===edge.sourceId),t=nodes.find(n=>n.id===edge.targetId);if(!s||!t)return;const l=document.createElementNS('http://www.w3.org/2000/svg','line');l.setAttribute('x1',s.x+s.w/2);l.setAttribute('y1',s.y+s.h/2);l.setAttribute('x2',t.x+t.w/2);l.setAttribute('y2',t.y+t.h/2);l.setAttribute('stroke',edge.color);l.setAttribute('stroke-width',Math.max(edge.width||2,2));l.setAttribute('opacity',.4);mn.appendChild(l)});const cw=wrapper.clientWidth,ch=wrapper.clientHeight,vp=document.getElementById('minimapViewport');vp.setAttribute('x',-viewX/scale);vp.setAttribute('y',-viewY/scale);vp.setAttribute('width',cw/scale);vp.setAttribute('height',ch/scale)}

// ====== UNDO / REDO ======
function snapshotState(){
  const fpData=(typeof getFloorPlansForSave==='function')?getFloorPlansForSave():[];
  return JSON.stringify({
    nodes:nodes.map(n=>({id:n.id,subcategoryId:n.subcategoryId,selectedProductId:n.selectedProductId,
      name:n.name,model:n.model,category:n.category,color:n.color,
      x:n.x,y:n.y,w:n.w,h:n.h,qty:n.qty,label:n.label,hideLabel:n.hideLabel||false,
      floor_id:n.floor_id||null,area_label:n.area_label||'',floor_label:n.floor_label||'',
      building_id:n.building_id||null,
      in_topology:n.in_topology!==false,
      is_riser_node:n.is_riser_node||false,_floorCreated:n._floorCreated||false,
      labelPosition:n.labelPosition||null,locked:n.locked||false,
      showCoverage:n.showCoverage,coverageRadii:n.coverageRadii,coverageVisible:n.coverageVisible,coverageN:n.coverageN})),
    edges:edges.map(e=>({id:e.id,sourceId:e.sourceId,sourcePort:e.sourcePort,targetId:e.targetId,targetPort:e.targetPort,
      cableType:e.cableType,color:e.color,width:e.width,dash:e.dash,label:e.label,
      hideLabel:e.hideLabel||false,routeMode:e.routeMode,midPos:e.midPos,
      selectedProductId:e.selectedProductId,selectedProductName:e.selectedProductName,selectedProductModel:e.selectedProductModel,selectedProductMn:e.selectedProductMn})),
    nodeIdCounter,edgeIdCounter,
    floor_plans:fpData,
    buildings:(typeof getBuildingsForSave==='function')?getBuildingsForSave():[],
    routeIdCounter:typeof routeIdCounter!=='undefined'?routeIdCounter:300,
    areaIdCounter:typeof areaIdCounter!=='undefined'?areaIdCounter:400,
    topoAreas:topoAreas.map(a=>({id:a.id,label:a.label,x:a.x,y:a.y,width:a.width,height:a.height,color:a.color||'#3b82f6',opacity:a.opacity||0.08,locked:a.locked||false,area_type:a.area_type||'normal'})),
  });
}
function _doPush(){undoStack=undoStack.slice(0,undoIndex+1);undoStack.push(snapshotState());if(undoStack.length>MAX_UNDO)undoStack.shift();undoIndex=undoStack.length-1}
function pushHistory(){if(DIAGRAM_CONFIG.readOnly)return;_doPush()}
function pushHistoryProp(){if(DIAGRAM_CONFIG.readOnly)return;if(!_propEditing){_propEditing=true;_doPush()}clearTimeout(_propEditTimer);_propEditTimer=setTimeout(()=>{_propEditing=false},1000)}
function restoreSnapshot(snap){
  const data=JSON.parse(snap);
  nodes=data.nodes.map(n=>{
    const sub=SUBCATEGORIES[n.subcategoryId];
    if(sub){n.iconData=sub.iconData;n.products=sub.products||[];
      if(n.selectedProductId){const p=n.products.find(p=>p.id===n.selectedProductId);if(p&&p.iconData)n.iconData=p.iconData}
    }else if(n.subcategoryId===null){n.iconData=n.is_riser_node?DEFAULT_DEVICE_ICONS.riser:DEFAULT_DEVICE_ICONS.text_note;n.products=[]}
    else{const product=PRODUCTS.find(p=>p.id===(n.selectedProductId||n.productId));n.iconData=product?product.iconData:DEFAULT_DEVICE_ICONS.generic;n.products=product?[product]:[]}
    return n;
  });
  edges=data.edges||[];
  nodeIdCounter=data.nodeIdCounter||100;edgeIdCounter=data.edgeIdCounter||200;
  if(data.routeIdCounter&&typeof routeIdCounter!=='undefined')routeIdCounter=data.routeIdCounter;
  if(data.areaIdCounter&&typeof areaIdCounter!=='undefined')areaIdCounter=data.areaIdCounter;
  if(data.buildings&&typeof restoreBuildings==='function'){restoreBuildings(data.buildings)}
  if(data.floor_plans&&typeof restoreFloorPlans==='function'){restoreFloorPlans(data.floor_plans)}
  if(data.topoAreas)topoAreas=data.topoAreas;
  selectedNodeIds=new Set();selectedEdgeIds=new Set();selectedNodeId=null;selectedEdgeId=null;
  if(typeof selectedAreaId!=='undefined')selectedAreaId=null;
  if(typeof selectedRouteId!=='undefined')selectedRouteId=null;
  hasUnsavedChanges=true;renderAll();hideProps();
}
function undoAction(){if(undoIndex<=0){showToast(_t('没有可撤销的操作'));return}undoIndex--;restoreSnapshot(undoStack[undoIndex]);showToast(_t('已撤销'))}
function redoAction(){if(undoIndex>=undoStack.length-1){showToast(_t('没有可重做的操作'));return}undoIndex++;restoreSnapshot(undoStack[undoIndex]);showToast(_t('已重做'))}
function showToast(msg){const t=document.getElementById('toast');t.textContent=msg;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2000)}

function sdConfirm(title,msg,opts){
  return new Promise(resolve=>{
    const m=document.getElementById('sdConfirmModal');
    if(!m){resolve(confirm(msg));return}
    document.getElementById('sdConfirmTitle').textContent=title;
    document.getElementById('sdConfirmMsg').textContent=msg;
    const icon=document.getElementById('sdConfirmIcon');
    const okBtn=document.getElementById('sdConfirmOk');
    if(opts&&opts.danger){icon.textContent='warning';icon.className='material-symbols-outlined text-5xl text-red-500';okBtn.className='flex-1 py-2.5 px-4 bg-red-500 border-none rounded-xl text-white text-sm font-medium cursor-pointer transition-colors hover:bg-red-600'}
    else{icon.textContent='help';icon.className='material-symbols-outlined text-5xl text-blue-500';okBtn.className='flex-1 py-2.5 px-4 bg-blue-600 border-none rounded-xl text-white text-sm font-medium cursor-pointer transition-colors hover:bg-blue-700'}
    if(opts&&opts.okText)okBtn.textContent=opts.okText;
    m.classList.remove('hidden');m.style.display='flex';
    function close(val){m.style.display='none';m.classList.add('hidden');resolve(val)}
    okBtn.onclick=()=>close(true);
    document.getElementById('sdConfirmCancel').onclick=()=>close(false);
    m.onclick=e=>{if(e.target===m)close(false)};
  });
}

// ====== KEYBOARD SHORTCUTS ======
document.addEventListener('keydown',e=>{
  if(['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName))return;
  const mod=e.metaKey||e.ctrlKey;
  if(DIAGRAM_CONFIG.readOnly){
    // Read-only: only allow Escape
    if(e.key==='Escape'){if(isBoxSelecting){isBoxSelecting=false;boxSelectStart=null;const bsr=document.getElementById('boxSelectRect');if(bsr)bsr.remove();return}selectedNodeIds=new Set();selectedEdgeIds=new Set();selectedNodeId=null;selectedEdgeId=null;renderAll();hideProps()}
    return;
  }
  if(mod&&e.key==='z'){e.preventDefault();if(e.shiftKey)redoAction();else undoAction();return}
  if(mod&&e.key==='y'){e.preventDefault();redoAction();return}
  if(mod&&e.key==='c'){e.preventDefault();copySelected();return}
  if(mod&&e.key==='v'){e.preventDefault();pasteClipboard();return}
  if(mod&&e.key==='a'){e.preventDefault();selectAllNodes();return}
  if(mod&&e.key==='s'){e.preventDefault();saveDiagram();return}
  if(e.key==='v'||e.key==='V')setTool('select');
  if(e.key==='c'||e.key==='C')setTool('connect');
  if(e.key==='a'||e.key==='A')setTool('area');
  if(e.key==='t'||e.key==='T')addTextNode();
  if(e.key==='Delete'||e.key==='Backspace')deleteSelected();
  if(e.key==='Escape'){
    if(isBoxSelecting){isBoxSelecting=false;boxSelectStart=null;const bsr=document.getElementById('boxSelectRect');if(bsr)bsr.remove();return}
    if(typeof isDrawingArea!=='undefined'&&isDrawingArea){isDrawingArea=false;areaDrawStart=null;document.getElementById('tempLayer').innerHTML='';setTool('select');return}
    if(isConnecting){polylineWaypoints=[];isConnecting=false;connSourceId=null;if(isReconnecting){const re=edges.find(e2=>e2.id===reconnectEdgeId);if(re)delete re._hidden;isReconnecting=false;reconnectEdgeId=null;reconnectEnd=''}if(typeof isReconnectingFloor!=='undefined'&&isReconnectingFloor){isReconnectingFloor=false;reconnectFloorRouteId=null;reconnectFloorEnd='';reconnectFloorFixedPos=null}if(typeof snapTargetNodeId!=='undefined'){snapTargetNodeId=null;snapTargetPort=null;snapTargetPos=null}document.getElementById('tempLayer').innerHTML='';setTool('select');renderAll();return}
    selectedNodeIds=new Set();selectedEdgeIds=new Set();selectedNodeId=null;selectedEdgeId=null;if(typeof selectedRouteId!=='undefined')selectedRouteId=null;renderAll();hideProps();setTool('select');if(typeof highlightConnectedInPanel==='function')highlightConnectedInPanel(null)}
});

// Space key tracking for pan-while-space (like Figma/Photoshop)
document.addEventListener('keydown',e=>{
  if(e.code==='Space'&&!['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName)){
    if(!isSpaceDown){isSpaceDown=true;document.getElementById('diagramCanvas').style.cursor='grab'}
    e.preventDefault();
  }
});
document.addEventListener('keyup',e=>{
  if(e.code==='Space'){isSpaceDown=false;if(!isPanning)document.getElementById('diagramCanvas').style.cursor=currentTool==='connect'||currentTool==='area'||currentTool==='calibrate'?'crosshair':'default'}
});

// ====== LABEL LAYOUT (shared by topology + floor plan) ======
function computeBestLabelSide(connections, nodeId){
  const dirCount={top:0,bottom:0,left:0,right:0};
  const portToDir={top:'top','top-left':'top','top-right':'top',bottom:'bottom','bottom-left':'bottom','bottom-right':'bottom',left:'left',right:'right'};
  connections.forEach(c=>{
    if(c.sourceId===nodeId){const d=portToDir[c.sourcePort];if(d)dirCount[d]++}
    if(c.targetId===nodeId){const d=portToDir[c.targetPort];if(d)dirCount[d]++}
  });
  const prio=['bottom','right','left','top'];
  let best=prio[0],bestCount=dirCount[best];
  for(let i=1;i<prio.length;i++){if(dirCount[prio[i]]<bestCount){best=prio[i];bestCount=dirCount[prio[i]]}}
  return best;
}

function getLabelCoords(side, nw, nh, lblW, lblH){
  const LO=LABEL_OFFSET;
  switch(side){
    case 'top': return {bgX:nw/2-lblW/2, bgY:-LO-lblH+2, textX:nw/2, firstLineY:-LO-lblH+12, anchor:'middle'};
    case 'right': return {bgX:nw+LO-2, bgY:nh/2-lblH/2, textX:nw+LO+4, firstLineY:nh/2-lblH/2+10, anchor:'start'};
    case 'left': return {bgX:-LO-lblW+2, bgY:nh/2-lblH/2, textX:-LO-4, firstLineY:nh/2-lblH/2+10, anchor:'end'};
    default: return {bgX:nw/2-lblW/2, bgY:nh+LO-6, textX:nw/2, firstLineY:nh+LO+4, anchor:'middle'};
  }
}

// ====== NODE CONTEXT MENU (label position + copy/paste/delete) ======
function showNodeCtxMenu(x, y, nodeId){
  if(DIAGRAM_CONFIG.readOnly)return;
  hideContextMenu();
  const n=nodes.find(nd=>nd.id===nodeId);
  if(!n)return;

  // Ensure this node is selected (right-click should select it)
  if(!selectedNodeIds.has(nodeId)){
    selectedNodeIds=new Set([nodeId]);selectedNodeId=nodeId;
    selectedEdgeId=null;selectedEdgeIds=new Set();
    renderAll();
  }

  let curPos='auto';
  if(currentView!=='topology'){
    const fp=getFloorPlan(currentView);
    const pl=fp?fp.placements.find(p=>p.node_id===nodeId):null;
    curPos=(pl&&pl.labelPosition)||'auto';
  }else{
    curPos=n.labelPosition||'auto';
  }

  const hasSel=selectedNodeIds.size>0||selectedEdgeIds.size>0;
  const hasClip=clipboard&&clipboard.nodes&&clipboard.nodes.length>0;
  const opts=[['auto',_t('自动')],['bottom',_t('下方')],['top',_t('上方')],['right',_t('右侧')],['left',_t('左侧')]];
  const menu=document.getElementById('nodeCtxMenu');
  menu.innerHTML=`
    <div class="ctx-item${!hasSel?' disabled':''}" onclick="if(!this.classList.contains('disabled')){document.getElementById('nodeCtxMenu').style.display='none';copySelected()}"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>${_t('复制')}<span class="ctx-shortcut">⌘C</span></div>
    <div class="ctx-item${!hasClip?' disabled':''}" onclick="if(!this.classList.contains('disabled')){document.getElementById('nodeCtxMenu').style.display='none';pasteClipboard()}"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>${_t('粘贴')}<span class="ctx-shortcut">⌘V</span></div>
    <div class="ctx-divider"></div>
    <div class="ctx-sub">
      <div class="ctx-item"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6h16M4 12h16M4 18h16"/></svg>${_t('标签位置')}</div>
      <div class="ctx-submenu">${opts.map(([v,l])=>`<div class="ctx-item${curPos===v?' active':''}" onclick="updateNodeLabelPosition(${nodeId},'${v}')">${l}</div>`).join('')}</div>
    </div>
    <div class="ctx-divider"></div>
    <div class="ctx-item" onclick="document.getElementById('nodeCtxMenu').style.display='none';deleteSelected()"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>${_t('删除')}<span class="ctx-shortcut">⌫</span></div>
    <div class="ctx-item" onclick="document.getElementById('nodeCtxMenu').style.display='none';selectAllNodes()"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><path d="M9 12l2 2 4-4"/></svg>${_t('全选')}<span class="ctx-shortcut">⌘A</span></div>`;
  menu.style.left=Math.min(x,window.innerWidth-200)+'px';
  menu.style.top=Math.min(y,window.innerHeight-160)+'px';
  menu.style.display='block';
  const close=function(e){if(!menu.contains(e.target)){menu.style.display='none';document.removeEventListener('mousedown',close)}};
  setTimeout(()=>document.addEventListener('mousedown',close),0);
}

function updateNodeLabelPosition(nodeId, value){
  pushHistoryProp();
  if(currentView!=='topology'){
    const fp=getFloorPlan(currentView);
    if(!fp)return;
    const pl=fp.placements.find(p=>p.node_id===nodeId);
    if(!pl)return;
    pl.labelPosition=value==='auto'?null:value;
  }else{
    const n=nodes.find(nd=>nd.id===nodeId);
    if(!n)return;
    n.labelPosition=value==='auto'?null:value;
  }
  hasUnsavedChanges=true;renderAll();
  document.getElementById('nodeCtxMenu').style.display='none';
}

// ====== COPY / PASTE ======
function copySelected(){
  if(!selectedNodeIds.size&&!selectedEdgeIds.size)return;
  const nodeIdSet=selectedNodeIds;

  if(currentView!=='topology'){
    // Floor plan mode: copy nodes + placements + routes
    const fp=typeof getFloorPlan==='function'?getFloorPlan(currentView):null;
    if(!fp)return;
    const nodeArr=nodes.filter(n=>nodeIdSet.has(n.id));
    const plArr=fp.placements.filter(p=>nodeIdSet.has(p.node_id));
    const routeArr=(fp.routes||[]).filter(r=>nodeIdSet.has(r.sourceNodeId)&&nodeIdSet.has(r.targetNodeId));
    clipboard={mode:'floor',nodes:JSON.parse(JSON.stringify(nodeArr)),placements:JSON.parse(JSON.stringify(plArr)),routes:JSON.parse(JSON.stringify(routeArr))};
    const parts=[];
    if(plArr.length)parts.push(`${plArr.length} ${_t('个节点')}`);
    if(routeArr.length)parts.push(`${routeArr.length} ${_t('条连线')}`);
    showToast(`${_t('已复制')} ${parts.join('、')}`);
  }else{
    // Topology mode: copy nodes + edges
    const nodeArr=nodes.filter(n=>nodeIdSet.has(n.id));
    const edgeSet=new Set();
    edges.forEach(e=>{if(nodeIdSet.has(e.sourceId)&&nodeIdSet.has(e.targetId))edgeSet.add(e.id)});
    selectedEdgeIds.forEach(id=>edgeSet.add(id));
    const edgeArr=edges.filter(e=>edgeSet.has(e.id));
    const allNodeIds=new Set(nodeIdSet);
    edgeArr.forEach(e=>{allNodeIds.add(e.sourceId);allNodeIds.add(e.targetId)});
    const allNodes=nodes.filter(n=>allNodeIds.has(n.id));
    clipboard={mode:'topology',nodes:JSON.parse(JSON.stringify(allNodes)),edges:JSON.parse(JSON.stringify(edgeArr))};
    const parts=[];
    if(nodeArr.length)parts.push(`${nodeArr.length} ${_t('个节点')}`);
    if(edgeArr.length)parts.push(`${edgeArr.length} ${_t('条连线')}`);
    showToast(`${_t('已复制')} ${parts.join('、')}`);
  }
}

function pasteClipboard(){
  if(DIAGRAM_CONFIG.readOnly)return;
  if(!clipboard||!clipboard.nodes.length)return;
  pushHistory();const idMap=new Map(),offset=30;
  selectedNodeIds=new Set();selectedEdgeIds=new Set();selectedEdgeId=null;

  if(clipboard.mode==='floor'&&currentView!=='topology'){
    // Floor plan paste
    const fp=typeof getFloorPlan==='function'?getFloorPlan(currentView):null;
    if(!fp)return;

    clipboard.nodes.forEach(n=>{
      const newId=nodeIdCounter++;idMap.set(n.id,newId);
      const sub=SUBCATEGORIES[n.subcategoryId];
      const newNode={...n,id:newId,_floorCreated:true,
        iconData:sub?sub.iconData:(n.subcategoryId===null?DEFAULT_DEVICE_ICONS.text_note:DEFAULT_DEVICE_ICONS.generic),
        products:sub?sub.products:[]};
      if(newNode.selectedProductId&&newNode.products.length){
        const p=newNode.products.find(p=>p.id===newNode.selectedProductId);
        if(p&&p.iconData)newNode.iconData=p.iconData;
      }
      nodes.push(newNode);selectedNodeIds.add(newId);

      // Create placement
      const origPl=(clipboard.placements||[]).find(p=>p.node_id===n.id);
      if(origPl){
        fp.placements.push({...JSON.parse(JSON.stringify(origPl)),node_id:newId,x:origPl.x+offset,y:origPl.y+offset});
      }else{
        fp.placements.push({node_id:newId,x:n.x+offset,y:n.y+offset,locked:false,rotation:0,qty:1,labelPosition:null});
      }
    });

    // Copy routes (remap IDs)
    (clipboard.routes||[]).forEach(r=>{
      const ns=idMap.get(r.sourceNodeId),nt=idMap.get(r.targetNodeId);
      if(ns!==undefined&&nt!==undefined){
        const newEdgeId=edgeIdCounter++;
        edges.push({id:newEdgeId,sourceId:ns,targetId:nt,sourcePort:r.sourcePort,targetPort:r.targetPort,
          routeMode:r.routeMode||'ortho3',midPos:r.midPos,cableType:r.cableType||'',color:r.color||'',
          width:r.width||2,dash:r.dash||'',label:r.label||''});
        const newRouteId=typeof routeIdCounter!=='undefined'?routeIdCounter++:Date.now();
        fp.routes.push({id:newRouteId,sourceNodeId:ns,targetNodeId:nt,sourcePort:r.sourcePort,targetPort:r.targetPort,
          routeMode:r.routeMode||'ortho3',midPos:r.midPos,cableType:r.cableType,color:r.color,width:r.width,
          dash:r.dash,label:r.label,linked_edge_id:newEdgeId,_userPorts:r._userPorts||false});
      }
    });
  }else{
    // Topology paste (original logic, also handles cross-view paste gracefully)
    clipboard.nodes.forEach(n=>{
      const newId=nodeIdCounter++;idMap.set(n.id,newId);
      const sub=SUBCATEGORIES[n.subcategoryId];
      const newNode={...n,id:newId,x:n.x+offset,y:n.y+offset,
        iconData:sub?sub.iconData:(n.subcategoryId===null?DEFAULT_DEVICE_ICONS.text_note:DEFAULT_DEVICE_ICONS.generic),
        products:sub?sub.products:[]};
      if(newNode.selectedProductId&&newNode.products.length){
        const p=newNode.products.find(p=>p.id===newNode.selectedProductId);
        if(p&&p.iconData)newNode.iconData=p.iconData;
      }
      nodes.push(newNode);selectedNodeIds.add(newId);
    });
    (clipboard.edges||[]).forEach(e=>{
      const ns=idMap.get(e.sourceId),nt=idMap.get(e.targetId);
      if(ns!==undefined&&nt!==undefined)edges.push({...e,id:edgeIdCounter++,sourceId:ns,targetId:nt});
    });
  }

  selectedNodeId=selectedNodeIds.size===1?[...selectedNodeIds][0]:null;
  hasUnsavedChanges=true;renderAll();
  if(selectedNodeIds.size===1)showNodeProps([...selectedNodeIds][0]);
  else if(selectedNodeIds.size>1)showMultiProps();
  showToast(`${_t('已粘贴')} ${clipboard.nodes.length} ${_t('个节点')}`);
}

// ====== CONTEXT MENU ======
svg.addEventListener('contextmenu',e=>{e.preventDefault();
  // Click-persistent mode: right-click undoes last waypoint or cancels active connection
  if(isConnecting){
    if(polylineWaypoints.length>0){polylineWaypoints.pop();const _pt=svgPoint(e);renderTempEdge(_pt.x,_pt.y);return}
    polylineWaypoints=[];
    if(isReconnecting){const re=edges.find(e2=>e2.id===reconnectEdgeId);if(re)delete re._hidden;isReconnecting=false;reconnectEdgeId=null;reconnectEnd=''}
    if(typeof isReconnectingFloor!=='undefined'&&isReconnectingFloor){isReconnectingFloor=false;reconnectFloorRouteId=null;reconnectFloorEnd='';reconnectFloorFixedPos=null}
    if(typeof snapTargetNodeId!=='undefined'){snapTargetNodeId=null;snapTargetPort=null;snapTargetPos=null}
    isConnecting=false;connSourceId=null;document.getElementById('tempLayer').innerHTML='';
    setTool('select');renderAll();return;
  }
  showContextMenu(e.clientX,e.clientY)});
function showContextMenu(x,y){
  if(DIAGRAM_CONFIG.readOnly)return;
  const menu=document.getElementById('ctxMenu');
  const hasSel=selectedNodeIds.size>0||selectedEdgeIds.size>0;
  const hasClip=clipboard&&clipboard.nodes.length>0;
  menu.querySelector('[data-action="copy"]').classList.toggle('disabled',!hasSel);
  menu.querySelector('[data-action="paste"]').classList.toggle('disabled',!hasClip);
  const hasRoute=typeof selectedRouteId!=='undefined'&&selectedRouteId!==null;
  menu.querySelector('[data-action="delete"]').classList.toggle('disabled',!hasSel&&selectedEdgeId===null&&!hasRoute);
  menu.style.left=Math.min(x,window.innerWidth-200)+'px';
  menu.style.top=Math.min(y,window.innerHeight-160)+'px';
  menu.style.display='block';
  const closeOnClick=function(e){if(!menu.contains(e.target)){menu.style.display='none';document.removeEventListener('mousedown',closeOnClick)}};
  setTimeout(()=>document.addEventListener('mousedown',closeOnClick),0);
}
function hideContextMenu(){document.getElementById('ctxMenu').style.display='none'}
function onCtxAction(action){
  hideContextMenu();
  if(action==='copy')copySelected();
  else if(action==='paste')pasteClipboard();
  else if(action==='delete')deleteSelected();
  else if(action==='selectAll')selectAllNodes();
}

// ====== EXPORT ======
async function prepareExportSVG(cropBounds,blackMode){
  const svgEl=document.getElementById('diagramCanvas');
  const clone=svgEl.cloneNode(true);
  clone.querySelectorAll('.port, .edge-hit, .node-glow, .mid-handle, .mid-handle-bar, .mid-handle-grip').forEach(el=>el.remove());
  const tempL=clone.querySelector('#tempLayer');if(tempL)tempL.innerHTML='';
  const handlesL=clone.querySelector('#handlesLayer');if(handlesL)handlesL.innerHTML='';
  const edgeHitL=clone.querySelector('#edgeHitLayer');if(edgeHitL)edgeHitL.innerHTML='';
  clone.querySelectorAll('.node-group').forEach(g=>{g.querySelectorAll('rect[stroke-dasharray]').forEach(r=>r.remove())});
  const cs=getComputedStyle(document.documentElement);
  const v=k=>cs.getPropertyValue(k).trim();
  const styleEl=document.createElementNS('http://www.w3.org/2000/svg','style');
  styleEl.textContent=`
    .grid-small-line{stroke:${v('--grid-small')};stroke-width:.5}
    .grid-large-line{stroke:${v('--grid-large')};stroke-width:.8}
    .node-label-bg{fill:${v('--bg-canvas')};opacity:.85}
    .node-label{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC',sans-serif;font-size:11px;fill:${v('--node-label')};font-weight:500;text-anchor:middle}
    .node-sublabel{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC',sans-serif;font-size:9px;fill:${v('--node-sublabel')};text-anchor:middle}
    .node-tag{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC',sans-serif;font-size:9px;fill:#3b82f6;text-anchor:middle;font-style:italic}
    .node-qty-badge{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC',sans-serif;font-size:9px;fill:#fbbf24;font-weight:700}
    .qty-badge-bg{fill:${v('--bg-panel')};stroke:#f59e0b;stroke-width:1.5}
    .edge-line{fill:none}
    .edge-label-bg{fill:${v('--edge-label-bg')}}
    .edge-label{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC',sans-serif;font-size:9px;text-anchor:middle;dominant-baseline:central}
    .edge-temp{display:none}
  `;
  clone.insertBefore(styleEl,clone.firstChild);
  // Embed all external images as base64 data URIs (required for SVG/PNG export)
  const allImages=Array.from(clone.querySelectorAll('image'));
  if(allImages.length){
    await Promise.all(allImages.map(imgEl=>{
      const href=imgEl.getAttribute('href');
      if(!href||href.startsWith('data:'))return Promise.resolve();
      return new Promise(resolve=>{
        const im=new Image();im.crossOrigin='anonymous';
        im.onload=()=>{try{const c=document.createElement('canvas');c.width=im.naturalWidth;c.height=im.naturalHeight;c.getContext('2d').drawImage(im,0,0);imgEl.setAttribute('href',c.toDataURL('image/png'))}catch(e){}resolve()};
        im.onerror=()=>resolve();
        im.src=href;
      });
    }));
  }
  // Boost floor background opacity for export
  const bgImg=clone.querySelector('#floorBgImage');
  if(bgImg)bgImg.setAttribute('opacity','0.6');
  // Black mode: icons and cables in black
  if(blackMode){
    const defs=clone.querySelector('defs');
    if(defs){const f=document.createElementNS('http://www.w3.org/2000/svg','filter');f.setAttribute('id','exportBlack');f.innerHTML='<feMorphology operator="dilate" radius="0.5" in="SourceGraphic" result="bold"/><feColorMatrix type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0" in="bold"/>';defs.appendChild(f)}
    clone.querySelectorAll('.edge-line').forEach(el=>el.setAttribute('stroke','#000'));
    // Icons are inline <svg> (from renderIconSVG), not <image>
    clone.querySelectorAll('.node-group svg, .node-group image').forEach(el=>el.setAttribute('filter','url(#exportBlack)'));
    // Make all text labels black
    clone.querySelectorAll('.node-label, .node-sublabel, .node-tag, .node-qty-badge, .edge-label').forEach(el=>el.setAttribute('fill','#000'));
  }
  // Thicken edge lines for export clarity
  clone.querySelectorAll('.edge-line').forEach(el=>{
    const sw=parseFloat(el.getAttribute('stroke-width'))||1.5;
    el.setAttribute('stroke-width', sw*2);
  });
  let w=1200,h=800;
  if(cropBounds){
    const pad=20,cx1=cropBounds.x1-pad,cy1=cropBounds.y1-pad;
    w=cropBounds.x2-cropBounds.x1+pad*2;h=cropBounds.y2-cropBounds.y1+pad*2;
    clone.setAttribute('viewBox',`${cx1} ${cy1} ${w} ${h}`);
    clone.setAttribute('xmlns','http://www.w3.org/2000/svg');
    const cg=clone.querySelector('#canvasGroup');if(cg)cg.setAttribute('transform','translate(0,0) scale(1)');
    const bgRect=clone.querySelector(':scope > rect');
    if(bgRect){bgRect.setAttribute('x',cx1);bgRect.setAttribute('y',cy1);bgRect.setAttribute('width',w);bgRect.setAttribute('height',h);bgRect.setAttribute('fill',v('--bg-canvas'))}
  }else if(currentView!=='topology'){
    // Floor plan view — use background + placements bounds
    const fp=getFloorPlan(currentView);
    let x1=Infinity,y1=Infinity,x2=-Infinity,y2=-Infinity;
    if(fp&&fp.background){const bx=fp.background.offset_x||0,by=fp.background.offset_y||0;x1=Math.min(x1,bx);y1=Math.min(y1,by);x2=Math.max(x2,bx+(fp.background.width||0));y2=Math.max(y2,by+(fp.background.height||0))}
    if(fp&&fp.placements){fp.placements.forEach(pl=>{const n=nodes.find(nd=>nd.id===pl.node_id);if(n){x1=Math.min(x1,pl.x-10);y1=Math.min(y1,pl.y-10);x2=Math.max(x2,pl.x+n.w+10);y2=Math.max(y2,pl.y+n.h+50)}})}
    if(x1===Infinity){x1=0;y1=0;x2=1200;y2=800}
    const pad=40;w=x2-x1+pad*2;h=y2-y1+pad*2;
    clone.setAttribute('viewBox',`${x1-pad} ${y1-pad} ${w} ${h}`);
    clone.setAttribute('xmlns','http://www.w3.org/2000/svg');
    const cg=clone.querySelector('#canvasGroup');if(cg)cg.setAttribute('transform','translate(0,0) scale(1)');
    const bgRect=clone.querySelector(':scope > rect');
    if(bgRect){bgRect.setAttribute('x',x1-pad);bgRect.setAttribute('y',y1-pad);bgRect.setAttribute('width',w);bgRect.setAttribute('height',h);bgRect.setAttribute('fill',v('--bg-canvas'))}
  }else if(nodes.length){
    let x1=Infinity,y1=Infinity,x2=-Infinity,y2=-Infinity;
    nodes.forEach(n=>{x1=Math.min(x1,n.x-30);y1=Math.min(y1,n.y-30);x2=Math.max(x2,n.x+n.w+30);y2=Math.max(y2,n.y+n.h+50)});
    edges.forEach(edge=>{
      if(!edge.label||edge.hideLabel)return;
      const result=buildEdgePath(edge);if(!result)return;
      const mid=getPathMidpoint(result,edge);
      x1=Math.min(x1,mid.x-60);y1=Math.min(y1,mid.y-20);x2=Math.max(x2,mid.x+60);y2=Math.max(y2,mid.y+20);
    });
    const pad=40;w=x2-x1+pad*2;h=y2-y1+pad*2;
    clone.setAttribute('viewBox',`${x1-pad} ${y1-pad} ${w} ${h}`);
    clone.setAttribute('xmlns','http://www.w3.org/2000/svg');
    const cg=clone.querySelector('#canvasGroup');if(cg)cg.setAttribute('transform','translate(0,0) scale(1)');
    const bgRect=clone.querySelector(':scope > rect');
    if(bgRect){bgRect.setAttribute('x',x1-pad);bgRect.setAttribute('y',y1-pad);bgRect.setAttribute('width',w);bgRect.setAttribute('height',h);bgRect.setAttribute('fill',v('--bg-canvas'))}
  }
  clone.setAttribute('width',w);clone.setAttribute('height',h);
  return {clone,w,h};
}

function getExportName(){
  const el=document.getElementById('diagramNameInput');
  const base=(el.value||el.textContent||'').trim()||_t('系统图');
  if(currentView!=='topology'){const fp=getFloorPlan(currentView);if(fp)return base+'_'+fp.label}
  return base;
}

async function exportSVG(){
  const {clone}=await prepareExportSVG(null,exportBlackMode);
  const svgData=new XMLSerializer().serializeToString(clone);
  const blob=new Blob([svgData],{type:'image/svg+xml'});
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');a.href=url;a.download=getExportName()+'.svg';
  a.click();URL.revokeObjectURL(url);showToast(_t('已导出 SVG'));
}

async function exportPNG(){
  const {clone,w,h}=await prepareExportSVG(null,exportBlackMode);
  const dpr=2;
  const canvas=document.createElement('canvas');
  canvas.width=w*dpr;canvas.height=h*dpr;
  const ctx=canvas.getContext('2d');
  ctx.scale(dpr,dpr);
  const svgData=new XMLSerializer().serializeToString(clone);
  const img=new Image();
  img.onload=function(){
    ctx.drawImage(img,0,0,w,h);
    canvas.toBlob(function(blob){
      const url=URL.createObjectURL(blob);
      const a=document.createElement('a');a.href=url;a.download=getExportName()+'.png';
      a.click();URL.revokeObjectURL(url);showToast(_t('已导出 PNG'));
    },'image/png');
  };
  img.onerror=function(){showToast(_t('PNG 导出失败，请尝试 SVG 格式'))};
  img.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svgData);
}

async function exportPDF(){
  const {clone,w,h}=await prepareExportSVG(null,exportBlackMode);
  // PDF doesn't need full resolution — cap canvas to 50M pixels (safe for all browsers)
  // e.g. 8000x6250 = 50M, plenty for print-quality PDF
  const maxPixels=50000000;
  let scale=1;
  if(w*h>maxPixels) scale=Math.sqrt(maxPixels/(w*h));
  const cw=Math.round(w*scale);
  const ch=Math.round(h*scale);
  const canvas=document.createElement('canvas');
  canvas.width=cw;canvas.height=ch;
  const ctx=canvas.getContext('2d');
  if(scale!==1) ctx.scale(scale,scale);
  ctx.fillStyle='#fff';ctx.fillRect(0,0,w,h);
  const svgData=new XMLSerializer().serializeToString(clone);
  const img=new Image();
  img.onload=function(){
    ctx.drawImage(img,0,0,w,h);
    canvas.toBlob(function(blob){
      if(!blob){showToast(_t('PDF 导出失败'));return}
      const reader=new FileReader();
      reader.onload=function(){
        const orientation=w>h?'l':'p';
        const pdf=new jspdf.jsPDF({orientation,unit:'px',format:[w,h]});
        pdf.addImage(new Uint8Array(reader.result),'JPEG',0,0,w,h);
        pdf.save(getExportName()+'.pdf');
        showToast(_t('已导出 PDF'));
      };
      reader.readAsArrayBuffer(blob);
    },'image/jpeg',0.92);
  };
  img.onerror=function(){showToast(_t('PDF 导出失败'))};
  img.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svgData);
}

// ====== DWG EXPORT ======

function currentFloorHasDwg() {
  if (currentView === 'topology') return false;
  const fp = typeof getFloorPlan === 'function' ? getFloorPlan(currentView) : null;
  return !!(fp && fp.background && fp.background.bg_type === 'dxf' && fp.background.dxf_filename);
}

function updateDwgExportMenuItem() {
  const item = document.getElementById('exportDwgItem');
  if (!item) return;
  item.style.display = currentFloorHasDwg() ? 'flex' : 'none';
}

async function exportDWG() {
  if (!currentFloorHasDwg()) { showToast(_t('当前楼层无 DXF 底图')); return; }
  const fp = getFloorPlan(currentView);
  document.getElementById('exportMenu').style.display = 'none';

  showToast(_t('生成 CAD 文件中...'));

  try {
    // 收集当前楼层结构化元素（设备/连线/区域）+ 坐标换算参数
    const bg = fp.background || {};
    const iconKeyOf = (n) => {
      try { return (typeof getNodeIconKey === 'function') ? getNodeIconKey(n) : ''; }
      catch (e) { return ''; }
    };
    // 归一化 iconData 为后端可解析的结构 { viewBox: [x,y,w,h], paths: [{d, stroke, fill}] }
    // iconData 可能是 object（内置图标库）或 SVG 字符串（产品自定义图标）
    function normalizeIconData(iconData) {
      if (!iconData) return null;
      if (typeof iconData === 'object' && iconData.paths) {
        const vb = (iconData.viewBox || '0 0 64 64').toString().trim().split(/\s+/).map(parseFloat);
        return {
          viewBox: vb.length === 4 ? vb : [0, 0, 64, 64],
          paths: (iconData.paths || []).filter(p => p && p.d).map(p => ({
            d: p.d,
            stroke: p.stroke || '',
            fill: p.fill || '',
          })),
        };
      }
      if (typeof iconData === 'string' && iconData.indexOf('<') >= 0) {
        // 从 SVG 字符串里抽所有 <path d="..."> + viewBox
        try {
          const parser = new DOMParser();
          const doc = parser.parseFromString(iconData, 'image/svg+xml');
          const svg = doc.querySelector('svg');
          const vb = svg && svg.getAttribute('viewBox');
          const paths = [...doc.querySelectorAll('path')].map(p => ({
            d: p.getAttribute('d') || '',
            stroke: p.getAttribute('stroke') || '',
            fill: p.getAttribute('fill') || '',
          })).filter(p => p.d);
          return {
            viewBox: (vb ? vb.trim().split(/\s+/).map(parseFloat) : [0, 0, 64, 64]),
            paths: paths,
          };
        } catch (e) { return null; }
      }
      return null;
    }

    const nodesArr = (fp.placements || []).map(p => {
      const n = (typeof nodes !== 'undefined') ? nodes.find(nd => nd.id === p.node_id) : null;
      let coverage = null;
      if (n) {
        const coverageMode = displaySettings.showCoverage;
        const isAntenna = (typeof getNodeIconKey === 'function') && getNodeIconKey(n) === 'antenna_indoor';
        const shouldShowCov = isAntenna && (
          coverageMode === 'all' ||
          (coverageMode === 'individual' && n.showCoverage === true)
        );
        if (shouldShowCov) {
          const radii = n.coverageRadii
            || (typeof coverageRadiiFromN === 'function' ? coverageRadiiFromN(n.coverageN) : null);
          if (radii) {
            const vis = n.coverageVisible || [true, true];
            const ringKeys = ['showCoverageInner', 'showCoverageMid'];
            const exportVis = [0, 1].map(i => vis[i] !== false && displaySettings[ringKeys[i]] !== false);
            coverage = { radii: radii, visible: exportVis };
          }
        }
      }
      return {
        id: p.node_id,
        x: p.x, y: p.y,
        w: (n && n.w) || 32,
        h: (n && n.h) || 32,
        rotation: p.rotation || 0,
        qty: p.qty || 1,
        label: (n && (n.label || n.name)) || '',
        model: (n && n.model) || '',
        iconKey: n ? iconKeyOf(n) : '',
        iconData: n ? normalizeIconData(n.iconData) : null,
        coverage: coverage,
      };
    });
    const routesArr = (fp.routes || []).map(r => ({
      id: r.id,
      sourceNodeId: r.sourceNodeId,
      targetNodeId: r.targetNodeId,
      sourcePort: r.sourcePort,
      targetPort: r.targetPort,
      routeMode: r.routeMode,
      midPos: r.midPos,
      waypoints: r.waypoints || [],
      label: r.label || '',
      dash: r.dash || false,
      cableType: r.cableType || '',
    }));
    const areasArr = (fp.areas || []).map(a => ({
      id: a.id,
      x: a.x, y: a.y, width: a.width, height: a.height,
      label: a.label || '',
    }));

    const elements = {
      bg_width_px: bg.width || 0,
      bg_height_px: bg.height || 0,
      offset_x: bg.offset_x || 0,
      offset_y: bg.offset_y || 0,
      nodes: nodesArr,
      routes: routesArr,
      areas: areasArr,
    };

    const resp = await fetch(
      (DIAGRAM_CONFIG.apiLoadBase || '') + DIAGRAM_CONFIG.diagramId + '/export-dwg',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': DIAGRAM_CONFIG.csrfToken },
        body: JSON.stringify({
          dxf_filename: fp.background.dxf_filename,
          diagram_name: document.getElementById('diagramNameInput')?.value || 'diagram',
          elements: elements,
        })
      }
    );

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ message: resp.statusText }));
      showToast(_t('导出失败') + ': ' + (err.message || resp.statusText));
      return;
    }

    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const name = document.getElementById('diagramNameInput')?.value || 'diagram';
    let ext = 'dxf';
    const cd = resp.headers.get('Content-Disposition') || '';
    const m = cd.match(/filename="?([^"]+)"?/i);
    if (m) {
      const fn = m[1];
      const dot = fn.lastIndexOf('.');
      if (dot > 0) ext = fn.slice(dot + 1);
    }
    a.download = name + '.' + ext;
    a.click();
    URL.revokeObjectURL(url);
    showToast(_t('已导出') + ' ' + ext.toUpperCase());
  } catch (err) {
    showToast(_t('导出失败') + ': ' + err.message);
  }
}

function toggleExportMenu(){
  const menu=document.getElementById('exportMenu');
  if(menu.style.display==='block'){menu.style.display='none'}
  else{menu.style.display='block';updateDwgExportMenuItem();setTimeout(()=>{document.addEventListener('click',function closeMenu(){menu.style.display='none';document.removeEventListener('click',closeMenu)})},0)}
}

function startCropExport(){
  const svgEl=document.getElementById('diagramCanvas');
  const cg=document.getElementById('canvasGroup');
  svgEl.style.cursor='crosshair';
  showToast(_t('拖拽框选导出区域，ESC 取消'));
  let start=null;
  const rectEl=document.createElementNS('http://www.w3.org/2000/svg','rect');
  rectEl.setAttribute('fill','rgba(59,130,246,0.08)');
  rectEl.setAttribute('stroke','#3b82f6');
  rectEl.setAttribute('stroke-width',2/scale);
  rectEl.setAttribute('stroke-dasharray',`${6/scale},${4/scale}`);
  rectEl.setAttribute('rx',4/scale);
  rectEl.style.display='none';
  cg.appendChild(rectEl);
  function cleanup(){
    svgEl.style.cursor=currentTool==='connect'||currentTool==='area'||currentTool==='calibrate'?'crosshair':'default';
    if(rectEl.parentNode)rectEl.remove();
    svgEl.removeEventListener('mousedown',onDown,true);
    svgEl.removeEventListener('mousemove',onMove,true);
    svgEl.removeEventListener('mouseup',onUp,true);
    document.removeEventListener('keydown',onKey);
  }
  function onDown(e){
    e.stopPropagation();e.preventDefault();
    start=svgPoint(e);
    rectEl.setAttribute('x',start.x);rectEl.setAttribute('y',start.y);
    rectEl.setAttribute('width',0);rectEl.setAttribute('height',0);
    rectEl.style.display='';
  }
  function onMove(e){
    if(!start)return;
    e.stopPropagation();
    const cur=svgPoint(e);
    rectEl.setAttribute('x',Math.min(start.x,cur.x));
    rectEl.setAttribute('y',Math.min(start.y,cur.y));
    rectEl.setAttribute('width',Math.abs(cur.x-start.x));
    rectEl.setAttribute('height',Math.abs(cur.y-start.y));
  }
  async function onUp(e){
    if(!start)return;
    e.stopPropagation();
    const cur=svgPoint(e);
    const x1=Math.min(start.x,cur.x),y1=Math.min(start.y,cur.y);
    const x2=Math.max(start.x,cur.x),y2=Math.max(start.y,cur.y);
    cleanup();
    if(x2-x1<20||y2-y1<20){showToast(_t('选区太小，已取消'));return}
    const{clone,w,h}=await prepareExportSVG({x1,y1,x2,y2},exportBlackMode);
    const dpr=2;
    const canvas=document.createElement('canvas');
    canvas.width=w*dpr;canvas.height=h*dpr;
    const ctx=canvas.getContext('2d');ctx.scale(dpr,dpr);
    const svgData=new XMLSerializer().serializeToString(clone);
    const img=new Image();
    img.onload=function(){
      ctx.drawImage(img,0,0,w,h);
      canvas.toBlob(function(blob){
        const url=URL.createObjectURL(blob);
        const a=document.createElement('a');a.href=url;
        a.download=getExportName()+'_区域.png';
        a.click();URL.revokeObjectURL(url);showToast(_t('已导出选区 PNG'));
      },'image/png');
    };
    img.onerror=function(){showToast(_t('PNG 导出失败'))};
    img.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svgData);
  }
  function onKey(e){
    if(e.key==='Escape'){cleanup();showToast(_t('已取消框选导出'))}
  }
  svgEl.addEventListener('mousedown',onDown,true);
  svgEl.addEventListener('mousemove',onMove,true);
  svgEl.addEventListener('mouseup',onUp,true);
  document.addEventListener('keydown',onKey);
}

// ====== SAVE / LOAD ======
function serializeDiagram(){
  if(typeof syncFloorAreaLabels==='function')syncFloorAreaLabels();
  const fpData=(typeof getFloorPlansForSave==='function')?getFloorPlansForSave():[];
  return {
    nodes:nodes.map(n=>({id:n.id,subcategoryId:n.subcategoryId,selectedProductId:n.selectedProductId,
      name:n.name,model:n.model,category:n.category,color:n.color,
      x:n.x,y:n.y,w:n.w,h:n.h,qty:n.qty,label:n.label,hideLabel:n.hideLabel||false,
      floor_id:n.floor_id||null,area_label:n.area_label||'',floor_label:n.floor_label||'',
      building_id:n.building_id||null,
      in_topology:n.in_topology!==false,
      is_riser_node:n.is_riser_node||false,_floorCreated:n._floorCreated||false,
      labelPosition:n.labelPosition||null,locked:n.locked||false,
      showCoverage:n.showCoverage,coverageRadii:n.coverageRadii,coverageVisible:n.coverageVisible,coverageN:n.coverageN})),
    edges:edges.map(e=>{const o={id:e.id,sourceId:e.sourceId,sourcePort:e.sourcePort,targetId:e.targetId,targetPort:e.targetPort,cableType:e.cableType,color:e.color,width:e.width,dash:e.dash,label:e.label,hideLabel:e.hideLabel||false,routeMode:e.routeMode,midPos:e.midPos};if(e.waypoints&&e.waypoints.length)o.waypoints=e.waypoints;if(e.selectedProductId)o.selectedProductId=e.selectedProductId;if(e.selectedProductName)o.selectedProductName=e.selectedProductName;if(e.selectedProductModel)o.selectedProductModel=e.selectedProductModel;if(e.selectedProductMn)o.selectedProductMn=e.selectedProductMn;return o}),
    viewX,viewY,scale,nodeIdCounter,edgeIdCounter,
    floor_plans:fpData,
    buildings:(typeof getBuildingsForSave==='function')?getBuildingsForSave():[],
    floorPlanIdCounter,
    buildingIdCounter:typeof buildingIdCounter!=='undefined'?buildingIdCounter:1,
    routeIdCounter:typeof routeIdCounter!=='undefined'?routeIdCounter:300,
    areaIdCounter:typeof areaIdCounter!=='undefined'?areaIdCounter:400,
    topoAreas:topoAreas.map(a=>({id:a.id,label:a.label,x:a.x,y:a.y,width:a.width,height:a.height,color:a.color||'#3b82f6',opacity:a.opacity||0.08,locked:a.locked||false,area_type:a.area_type||'normal'})),
    displaySettings,
  };
}

function deserializeDiagram(data){
  if(!data||!data.nodes)return;
  nodes=data.nodes.map(n=>{
    const sub=SUBCATEGORIES[n.subcategoryId];
    if(sub){
      n.iconData=sub.iconData;
      n.products=sub.products||[];
      if(n.selectedProductId){
        const p=n.products.find(p=>p.id===n.selectedProductId);
        if(p&&p.iconData)n.iconData=p.iconData;
      }
    } else if(n.subcategoryId===null){
      n.iconData=n.is_riser_node?DEFAULT_DEVICE_ICONS.riser:DEFAULT_DEVICE_ICONS.text_note;
      n.products=[];
    } else {
      const product=PRODUCTS.find(p=>p.id===(n.selectedProductId||n.productId));
      n.iconData=product?product.iconData:DEFAULT_DEVICE_ICONS.generic;
      n.products=product?[product]:[];
    }
    return n;
  });
  edges=data.edges||[];
  viewX=data.viewX||0;viewY=data.viewY||0;scale=data.scale||1;
  nodeIdCounter=data.nodeIdCounter||100;edgeIdCounter=data.edgeIdCounter||200;
  if(data.buildings&&typeof restoreBuildings==='function'){restoreBuildings(data.buildings)}
  if(data.floor_plans&&typeof restoreFloorPlans==='function'){restoreFloorPlans(data.floor_plans)}
  if(data.floorPlanIdCounter)floorPlanIdCounter=data.floorPlanIdCounter;
  if(data.buildingIdCounter&&typeof buildingIdCounter!=='undefined')buildingIdCounter=data.buildingIdCounter;
  if(data.routeIdCounter&&typeof routeIdCounter!=='undefined')routeIdCounter=data.routeIdCounter;
  if(data.areaIdCounter&&typeof areaIdCounter!=='undefined')areaIdCounter=data.areaIdCounter;
  if(data.topoAreas)topoAreas=data.topoAreas;
  if(data.displaySettings){const ds=Object.assign({cableWidth:1,cableBlack:false,cableLabel:true,cableLength:true,iconWidth:1,iconBlack:false,iconLabel:true,iconModel:true,showCoverage:'individual',showCoverageInner:true,showCoverageMid:true,coverageFill:true,coverageMode:'circles'},data.displaySettings);delete ds.coverageN;delete ds.showCoverageOuter;if(ds.showCoverage===true)ds.showCoverage='individual';if(ds.showCoverage===false)ds.showCoverage='off';displaySettings=ds;}

  // ── 老格式兼容：补 in_topology / building_id 字段 ──
  // 如果整个 diagram 任何节点都没有 in_topology 字段 → 老格式 → 全部默认 true（保持旧行为）
  const _isLegacyDiagram=nodes.length>0&&nodes.every(n=>n.in_topology===undefined);
  nodes.forEach(n=>{
    if(n.in_topology===undefined){
      n.in_topology=_isLegacyDiagram?true:(n.floor_id?false:true);
    }
    if(n.building_id===undefined){
      // 根据 floor_id 反查 fp.building_id，无 floor_id → null（中央机房）
      if(n.floor_id&&typeof floorPlans!=='undefined'){
        const fp=floorPlans.find(f=>f.id===n.floor_id);
        n.building_id=fp?(fp.building_id||null):null;
      }else{
        n.building_id=null;
      }
    }
  });

  updateTransform();renderAll();
  // 从 localStorage 恢复刷新前的视图（楼栋 / 楼层）
  _restoreViewState();
}

async function saveDiagram(){
  if(DIAGRAM_CONFIG.readOnly)return;
  const btn=document.getElementById('btnSave');
  btn.classList.add('saving');btn.textContent=_t('保存中...');
  try{
    const name=document.getElementById('diagramNameInput').value.trim()||_t('未命名系统图');
    let thumbnailSvg='';
    try{
      const thumbResult=await prepareExportSVG();
      const tc=thumbResult.clone;
      const bgRect=tc.querySelector(':scope > rect');if(bgRect)bgRect.remove();
      tc.querySelectorAll('pattern, [fill="url(#gridSmall)"], [fill="url(#gridLarge)"]').forEach(el=>el.remove());
      tc.removeAttribute('width');tc.removeAttribute('height');
      tc.setAttribute('style','width:100%;height:100%;');
      thumbnailSvg=new XMLSerializer().serializeToString(tc);
    }catch(e){console.warn('缩略图生成失败:',e)}
    const headers={'Content-Type':'application/json'};
    if(!DIAGRAM_CONFIG.externalMode&&DIAGRAM_CONFIG.csrfToken){headers['X-CSRFToken']=DIAGRAM_CONFIG.csrfToken}
    const bodyData=DIAGRAM_CONFIG.externalMode
      ?{name,diagramData:serializeDiagram(),thumbnailSvg}
      :{id:DIAGRAM_CONFIG.diagramId,name,projectId:DIAGRAM_CONFIG.projectId||null,diagramData:serializeDiagram(),thumbnailSvg};
    const resp=await fetch(DIAGRAM_CONFIG.apiSave,{method:'POST',headers,body:JSON.stringify(bodyData)});
    const result=await resp.json();
    if(result.success){
      hasUnsavedChanges=false;showToast('✓ '+_t('系统图已保存'));
      if(!DIAGRAM_CONFIG.externalMode&&!DIAGRAM_CONFIG.diagramId&&result.id){
        DIAGRAM_CONFIG.diagramId=result.id;
        history.replaceState(null,'',DIAGRAM_CONFIG.editorBase+result.id);
      }
    }else{showToast(_t('保存失败')+': '+(result.message||'未知错误'))}
  }catch(err){showToast(_t('保存失败')+': '+err.message)}
  finally{btn.classList.remove('saving');btn.textContent=_t('保存')}
}

// ====== AUTO SAVE ======
async function autoSaveDiagram(){
  if(DIAGRAM_CONFIG.readOnly||!hasUnsavedChanges)return;
  // New unsaved diagram (no id yet) — skip auto-save, user must do first manual save
  if(!DIAGRAM_CONFIG.externalMode&&!DIAGRAM_CONFIG.diagramId)return;
  const btn=document.getElementById('btnSave');
  const origText=btn.textContent;
  btn.classList.add('saving');btn.textContent=_t('自动保存中...');
  try{
    const name=document.getElementById('diagramNameInput').value.trim()||_t('未命名系统图');
    let thumbnailSvg='';
    try{
      const thumbResult=await prepareExportSVG();
      const tc=thumbResult.clone;
      const bgRect=tc.querySelector(':scope > rect');if(bgRect)bgRect.remove();
      tc.querySelectorAll('pattern, [fill="url(#gridSmall)"], [fill="url(#gridLarge)"]').forEach(el=>el.remove());
      tc.removeAttribute('width');tc.removeAttribute('height');
      tc.setAttribute('style','width:100%;height:100%;');
      thumbnailSvg=new XMLSerializer().serializeToString(tc);
    }catch(e){console.warn('Auto-save thumbnail generation failed:',e)}
    const headers={'Content-Type':'application/json'};
    if(!DIAGRAM_CONFIG.externalMode&&DIAGRAM_CONFIG.csrfToken){headers['X-CSRFToken']=DIAGRAM_CONFIG.csrfToken}
    const bodyData=DIAGRAM_CONFIG.externalMode
      ?{name,diagramData:serializeDiagram(),thumbnailSvg}
      :{id:DIAGRAM_CONFIG.diagramId,name,projectId:DIAGRAM_CONFIG.projectId||null,diagramData:serializeDiagram(),thumbnailSvg};
    const resp=await fetch(DIAGRAM_CONFIG.apiSave,{method:'POST',headers,body:JSON.stringify(bodyData)});
    const result=await resp.json();
    if(result.success){
      hasUnsavedChanges=false;showToast('✓ '+_t('已自动保存'));
    }else{console.warn('Auto-save failed:',result.message)}
  }catch(err){console.warn('Auto-save error:',err.message)}
  finally{btn.classList.remove('saving');btn.textContent=origText}
}
function startAutoSave(){
  if(_autoSaveTimer)clearInterval(_autoSaveTimer);
  _autoSaveTimer=setInterval(autoSaveDiagram,AUTO_SAVE_INTERVAL);
}
function stopAutoSave(){if(_autoSaveTimer){clearInterval(_autoSaveTimer);_autoSaveTimer=null}}

async function loadDiagram(){
  if(DIAGRAM_CONFIG.externalMode){
    // 外部模式：从专用 load API 加载
    try{
      const resp=await fetch(DIAGRAM_CONFIG.apiLoad);
      const result=await resp.json();
      if(result.success&&result.diagram){
        const nameEl=document.getElementById('diagramNameInput');
        if(nameEl.tagName==='INPUT')nameEl.value=result.diagram.name||'';else nameEl.textContent=result.diagram.name||'';
        if(result.diagram.diagramData&&Object.keys(result.diagram.diagramData).length>0){
          deserializeDiagram(result.diagram.diagramData);
          requestAnimationFrame(()=>setTimeout(fitView,50));
        }
      }
    }catch(err){console.error('加载系统图失败:',err)}
    return;
  }
  if(!DIAGRAM_CONFIG.diagramId)return;
  try{
    const resp=await fetch(DIAGRAM_CONFIG.apiLoadBase+DIAGRAM_CONFIG.diagramId+'/data');
    const result=await resp.json();
    if(result.success&&result.diagram){
      const nameEl2=document.getElementById('diagramNameInput');
      if(nameEl2.tagName==='INPUT')nameEl2.value=result.diagram.name||'';else nameEl2.textContent=result.diagram.name||'';
      deserializeDiagram(result.diagram.diagramData);
      requestAnimationFrame(()=>setTimeout(fitView,50));
    }
  }catch(err){console.error('加载系统图失败:',err)}
}

// ====== RENDER DISPATCH ======
// ====== DRAG PERFORMANCE OPTIMIZATION ======
let isDraggingOperation=false;
let pendingRenderFrame=null;
let _minimapTimer=null;

function requestRenderThrottled(){
  if(pendingRenderFrame)return;
  pendingRenderFrame=requestAnimationFrame(()=>{
    pendingRenderFrame=null;
    renderAll();
  });
}

function renderAll(){
  if(currentView==='topology'){
    const cl=document.getElementById('coverageLayer');if(cl)cl.innerHTML='';
    renderTopologyView();
    const si=document.getElementById('scaleIndicator');if(si)si.style.display='none';
  } else {
    renderFloorPlanView(currentView, isDraggingOperation);
  }
  updateInfo();
  // Debounce minimap updates during drag operations
  if(isDraggingOperation){
    if(!_minimapTimer){_minimapTimer=setTimeout(()=>{_minimapTimer=null;updateMinimap()},200)}
  } else {
    updateMinimap();
  }
}

// ====== VIEW SWITCHING ======
function switchView(viewId){
  // Save current view state
  if(currentView==='topology'){
    topoViewX=viewX;topoViewY=viewY;topoScale=scale;
  } else {
    const fp=getFloorPlan(currentView);
    if(fp){fp.viewX=viewX;fp.viewY=viewY;fp.scale=scale}
  }
  currentView=viewId;
  // Restore new view state
  let needsFitView=false;
  if(viewId==='topology'){
    viewX=topoViewX;viewY=topoViewY;scale=topoScale;
  } else {
    const fp=getFloorPlan(viewId);
    if(DIAGRAM_CONFIG.readOnly){
      // Preview mode: always fit to page when switching floors
      viewX=0;viewY=0;scale=1;needsFitView=true;
    } else if(fp&&fp.viewX!==undefined){viewX=fp.viewX;viewY=fp.viewY;scale=fp.scale||1}
    else{viewX=0;viewY=0;scale=1;needsFitView=true}
  }
  updateTransform();
  document.getElementById('zoomLevel').textContent=Math.round(scale*100)+'%';
  // Update tab UI — auto-switch building filter if needed
  document.querySelectorAll('.view-tab').forEach(t=>t.classList.toggle('active',t.dataset.view===viewId));
  if(typeof _activeBuildingFilter!=='undefined'&&typeof buildings!=='undefined'&&buildings.length>0){
    const _swFp=typeof floorPlans!=='undefined'?floorPlans.find(f=>f.id===viewId):null;
    if(_swFp){
      const _swBld=_swFp.building_id&&buildings.find(b=>b.id===_swFp.building_id)?_swFp.building_id:'ungrouped';
      if(_swBld!==_resolveActiveBuildingFilter()){_activeBuildingFilter=_swBld;rebuildViewTabs()}
    }
  }
  // Update toolbar visibility
  const fpTools=document.getElementById('floorPlanTools');
  if(fpTools)fpTools.style.display=viewId==='topology'?'none':'flex';
  if(viewId!=='topology'&&typeof updateFloorBgButton==='function')updateFloorBgButton(viewId);
  const btnRelayout=document.getElementById('btnRelayout');
  if(btnRelayout)btnRelayout.style.display=viewId==='topology'?'':'none';
  const btnSyncFromFloor=document.getElementById('btnSyncFromFloor');
  if(btnSyncFromFloor)btnSyncFromFloor.style.display=viewId==='topology'?'':'none';
  // Update lock button icon
  if(typeof _updateLockBtnIcon==='function'){
    let allLocked=false;
    if(viewId==='topology'){allLocked=nodes.length>0&&nodes.every(n=>n.locked)}
    else{const fp=getFloorPlan(viewId);allLocked=fp&&fp.placements.length>0&&fp.placements.every(p=>p.locked)}
    _updateLockBtnIcon(allLocked);
  }
  selectedNodeIds=new Set();selectedEdgeIds=new Set();selectedNodeId=null;selectedEdgeId=null;
  if(typeof syncFloorAreaLabels==='function')syncFloorAreaLabels();
  // Clear cached background image when switching views
  if(typeof cachedFloorBgImg!=='undefined'){
    if(cachedFloorBgImg&&cachedFloorBgImg.parentNode)cachedFloorBgImg.remove();
    cachedFloorBgImg=null;_cachedBgUrl=null;
  }
  renderAll();hideProps();
  // Fit view on first visit to a floor plan
  if(needsFitView)requestAnimationFrame(()=>fitView());
  if(typeof buildExistingDevicesPanel==='function')buildExistingDevicesPanel();
  _saveViewState();
}

// ====== FLOOR PLAN CRUD ======
function getFloorPlan(id){
  if(typeof floorPlans==='undefined')return null;
  return floorPlans.find(fp=>fp.id===id);
}

function addFloorPlan(buildingId){
  if(DIAGRAM_CONFIG.readOnly)return;
  if(typeof floorPlans==='undefined')window.floorPlans=[];
  const id='fp_'+floorPlanIdCounter++;
  // Count existing floors in this building for auto-labeling
  const bldFloors=buildingId?floorPlans.filter(fp=>fp.building_id===buildingId):floorPlans;
  const label=(bldFloors.length+1)+'F';
  floorPlans.push({
    id:id,label:label,sort_order:floorPlans.length+1,
    building_id:buildingId||null,
    background:null,calibration:null,
    placements:[],routes:[],areas:[],
    viewX:0,viewY:0,scale:1
  });
  hasUnsavedChanges=true;
  rebuildViewTabs();
  switchView(id);
}

function addFloorPlanWithBackground(label,background,buildingId){
  if(typeof floorPlans==='undefined')window.floorPlans=[];
  const id='fp_'+floorPlanIdCounter++;
  floorPlans.push({
    id:id,label:label,sort_order:floorPlans.length+1,
    building_id:buildingId||null,
    background:background,calibration:null,
    placements:[],routes:[],areas:[],
    viewX:0,viewY:0,scale:1
  });
  hasUnsavedChanges=true;
  rebuildViewTabs();
  return id;
}

function renameFloorPlan(fpId,newLabel){
  const fp=getFloorPlan(fpId);
  if(fp){fp.label=newLabel;hasUnsavedChanges=true;rebuildViewTabs()}
}

let _activeBuildingFilter=null;
// 记住每个楼栋最后一次查看的楼层，切楼栋时默认回到那个楼层
let _lastFloorByBuilding={};

// 刷新后保持当前视图（按 diagram id 持久化到 localStorage）
function _viewStateKey(){
  const id=(typeof DIAGRAM_CONFIG!=='undefined'&&DIAGRAM_CONFIG.diagramId)?DIAGRAM_CONFIG.diagramId:'__new__';
  return 'pma_sd_view_'+id;
}
function _saveViewState(){
  try{
    const state={
      currentView:currentView,
      activeBuildingFilter:_activeBuildingFilter,
      lastFloorByBuilding:_lastFloorByBuilding,
    };
    localStorage.setItem(_viewStateKey(),JSON.stringify(state));
  }catch(e){/* localStorage 不可用 */}
}
function _restoreViewState(){
  try{
    const raw=localStorage.getItem(_viewStateKey());
    if(!raw)return;
    const s=JSON.parse(raw);
    if(s.lastFloorByBuilding&&typeof s.lastFloorByBuilding==='object'){_lastFloorByBuilding=s.lastFloorByBuilding}
    if(s.activeBuildingFilter)_activeBuildingFilter=s.activeBuildingFilter;
    // 校验 currentView 仍然有效
    if(s.currentView==='topology'){
      switchView('topology');
    }else if(s.currentView&&typeof floorPlans!=='undefined'&&floorPlans.find(f=>f.id===s.currentView)){
      switchView(s.currentView);
    }
  }catch(e){}
}

function _switchToBuildingDefaultFloor(bldFilter){
  // bldFilter: 楼栋 id 或 'ungrouped'
  // 副作用：记住当前楼层（若属于前一个楼栋），然后 currentView 跳到目标楼栋的默认楼层
  if(typeof floorPlans==='undefined')return;
  // 记住当前楼层归属的楼栋
  if(currentView!=='topology'){
    const curFp=floorPlans.find(f=>f.id===currentView);
    if(curFp){
      const key=curFp.building_id||'ungrouped';
      _lastFloorByBuilding[key]=curFp.id;
    }
  }
  _activeBuildingFilter=bldFilter;
  // 选目标楼层：优先"上次看过的"，否则楼栋内第一个
  const bFloors=bldFilter==='ungrouped'
    ?floorPlans.filter(f=>!f.building_id||(typeof buildings!=='undefined'&&!buildings.find(b=>b.id===f.building_id)))
    :floorPlans.filter(f=>f.building_id===bldFilter);
  let target=_lastFloorByBuilding[bldFilter];
  if(!target||!bFloors.find(f=>f.id===target)){
    target=bFloors.length>0?bFloors[0].id:null;
  }
  if(target&&target!==currentView){
    switchView(target); // 这个函数内部会 rebuildViewTabs
  }else{
    rebuildViewTabs();
  }
}

function _resolveActiveBuildingFilter(){
  const hasBlds=typeof buildings!=='undefined'&&buildings.length>0;
  if(!hasBlds)return null;
  if(_activeBuildingFilter){
    if(_activeBuildingFilter==='ungrouped')return 'ungrouped';
    if(buildings.find(b=>b.id===_activeBuildingFilter))return _activeBuildingFilter;
  }
  if(currentView!=='topology'&&typeof floorPlans!=='undefined'){
    const fp=floorPlans.find(f=>f.id===currentView);
    if(fp&&fp.building_id&&buildings.find(b=>b.id===fp.building_id))return fp.building_id;
    if(fp)return 'ungrouped';
  }
  const sorted=buildings.slice().sort((a,b)=>a.sort_order-b.sort_order);
  return sorted[0].id;
}

function rebuildViewTabs(){
  const container=document.getElementById('viewTabs');
  if(!container)return;
  container.innerHTML='';

  const _hasBuildings=typeof buildings!=='undefined'&&buildings.length>0;
  const fps=typeof floorPlans!=='undefined'?floorPlans:[];

  if(_hasBuildings||fps.length>0){
    container.classList.add('has-buildings');
    const activeFilter=_resolveActiveBuildingFilter();
    const orderedBlds=_hasBuildings?buildings.slice().sort((a,b)=>a.sort_order-b.sort_order):[];
    const ungrouped=fps.filter(fp=>!fp.building_id||(_hasBuildings&&!buildings.find(b=>b.id===fp.building_id)));

    // ── Building filter row ──
    const bldRow=document.createElement('div');
    bldRow.className='view-tabs-buildings';
    orderedBlds.forEach(bld=>{
      const pill=document.createElement('div');
      pill.className='building-pill'+(activeFilter===bld.id?' active':'');
      pill.innerHTML=`<span class="building-pill-color" style="background:${bld.color}"></span>${bld.name}`;
      pill.addEventListener('click',()=>_switchToBuildingDefaultFloor(bld.id));
      pill.addEventListener('dblclick',()=>{if(typeof showBuildingProps==='function')showBuildingProps(bld.id)});
      bldRow.appendChild(pill);
    });
    if(_hasBuildings&&ungrouped.length>0){
      const pill=document.createElement('div');
      pill.className='building-pill'+(activeFilter==='ungrouped'?' active':'');
      pill.textContent=_t('独立楼层');
      pill.addEventListener('click',()=>_switchToBuildingDefaultFloor('ungrouped'));
      bldRow.appendChild(pill);
    }
    if(!DIAGRAM_CONFIG.readOnly){
      const addPill=document.createElement('div');
      addPill.className='building-pill building-pill-add';
      addPill.textContent='+';
      addPill.title=_t('添加建筑');
      addPill.addEventListener('click',()=>{
        const name=prompt(_t('建筑名称'));
        if(name&&name.trim()&&typeof addBuilding==='function'){
          const b=addBuilding(name.trim());
          if(b){_activeBuildingFilter=b.id;rebuildViewTabs()}
        }
      });
      bldRow.appendChild(addPill);
    }
    container.appendChild(bldRow);

    // ── Floor tabs row ──
    const floorRow=document.createElement('div');
    floorRow.className='view-tabs-floor-row';

    const arrowL=document.createElement('button');
    arrowL.className='view-tabs-arrow';
    arrowL.innerHTML='&#9664;';
    arrowL.addEventListener('click',()=>{inner.scrollLeft-=120});
    floorRow.appendChild(arrowL);

    const inner=document.createElement('div');
    inner.className='view-tabs-inner';
    floorRow.appendChild(inner);

    const arrowR=document.createElement('button');
    arrowR.className='view-tabs-arrow';
    arrowR.innerHTML='&#9654;';
    arrowR.addEventListener('click',()=>{inner.scrollLeft+=120});
    floorRow.appendChild(arrowR);

    function updateArrows(){
      arrowL.classList.toggle('visible',inner.scrollLeft>0);
      arrowR.classList.toggle('visible',inner.scrollLeft<inner.scrollWidth-inner.clientWidth-1);
    }
    inner.addEventListener('scroll',updateArrows);

    const topoTab=document.createElement('div');
    topoTab.className='view-tab'+(currentView==='topology'?' active':'');
    topoTab.dataset.view='topology';
    topoTab.textContent='🔧 '+_t('系统图');
    topoTab.addEventListener('click',()=>onTabClick('topology'));
    inner.appendChild(topoTab);

    // Filtered floor tabs
    const filteredFloors=activeFilter===null
      ?fps
      :activeFilter==='ungrouped'
        ?ungrouped
        :fps.filter(fp=>fp.building_id===activeFilter);
    filteredFloors.forEach(fp=>{
      const tab=document.createElement('div');
      tab.className='view-tab';
      if(currentView===fp.id)tab.classList.add('active');
      tab.dataset.view=fp.id;
      tab.dataset.fpId=fp.id;
      if(fp.building_id)tab.dataset.buildingId=fp.building_id;
      tab.textContent=fp.label;
      tab.addEventListener('pointerdown',e=>_tabDragStart(e,fp.id));
      inner.appendChild(tab);
    });

    if(!DIAGRAM_CONFIG.readOnly){
      if(activeFilter&&activeFilter!=='ungrouped'){
        const addBtn=document.createElement('div');
        addBtn.className='view-tab-add';
        addBtn.textContent=_t('添加楼层');
        addBtn.addEventListener('click',()=>addFloorPlan(activeFilter));
        inner.appendChild(addBtn);
      } else {
        const addBtn=document.createElement('div');
        addBtn.className='view-tab-add';
        addBtn.textContent=_t('添加楼层')+' ▾';
        addBtn.addEventListener('click',e=>{e.stopPropagation();_showAddFloorDropdown(addBtn)});
        inner.appendChild(addBtn);
      }
    }

    container.appendChild(floorRow);
    requestAnimationFrame(()=>{
      const activeTab=inner.querySelector('.view-tab.active');
      if(activeTab)activeTab.scrollIntoView({block:'nearest',inline:'nearest'});
      updateArrows();
    });

  } else {
    // No floors AND no buildings — simple single-row layout
    container.classList.remove('has-buildings');
    const inner=document.createElement('div');
    inner.className='view-tabs-inner';
    container.appendChild(inner);

    const topoTab=document.createElement('div');
    topoTab.className='view-tab'+(currentView==='topology'?' active':'');
    topoTab.dataset.view='topology';
    topoTab.textContent='🔧 '+_t('系统图');
    topoTab.addEventListener('click',()=>onTabClick('topology'));
    inner.appendChild(topoTab);

    if(!DIAGRAM_CONFIG.readOnly){
      const addBtn=document.createElement('div');
      addBtn.className='view-tab-add';
      addBtn.textContent=_t('添加楼层');
      addBtn.addEventListener('click',()=>addFloorPlan());
      inner.appendChild(addBtn);
    }
  }
}

// ====== ADD FLOOR DROPDOWN ======
function _showAddFloorDropdown(anchor){
  const existing=document.getElementById('addFloorDropdown');
  if(existing){existing.remove();return}
  const menu=document.createElement('div');
  menu.id='addFloorDropdown';
  menu.className='add-floor-dropdown';
  const orderedBlds=(typeof buildings!=='undefined')?buildings.slice().sort((a,b)=>a.sort_order-b.sort_order):[];
  if(orderedBlds.length>0){
    orderedBlds.forEach(b=>{
      const item=document.createElement('div');
      item.className='add-floor-dropdown-item';
      item.innerHTML=`<span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${b.color};margin-right:6px;flex-shrink:0"></span>${_t('添加到')} ${b.name}`;
      item.addEventListener('click',()=>{menu.remove();addFloorPlan(b.id)});
      menu.appendChild(item);
    });
    const divider=document.createElement('div');divider.className='add-floor-dropdown-divider';menu.appendChild(divider);
    const newBldItem=document.createElement('div');
    newBldItem.className='add-floor-dropdown-item';
    newBldItem.textContent=_t('添加到新建筑...');
    newBldItem.addEventListener('click',()=>{
      menu.remove();
      const name=prompt(_t('建筑名称'));
      if(name&&name.trim()&&typeof addBuilding==='function'){
        const b=addBuilding(name.trim());
        if(b)addFloorPlan(b.id);
      }
    });
    menu.appendChild(newBldItem);
    const freeItem=document.createElement('div');
    freeItem.className='add-floor-dropdown-item';
    freeItem.textContent=_t('添加独立楼层');
    freeItem.addEventListener('click',()=>{menu.remove();addFloorPlan()});
    menu.appendChild(freeItem);
  } else {
    // No buildings yet — simplified menu
    const addItem=document.createElement('div');
    addItem.className='add-floor-dropdown-item';
    addItem.textContent=_t('添加楼层');
    addItem.addEventListener('click',()=>{menu.remove();addFloorPlan()});
    menu.appendChild(addItem);
    const newBldItem=document.createElement('div');
    newBldItem.className='add-floor-dropdown-item';
    newBldItem.textContent=_t('添加到新建筑...');
    newBldItem.addEventListener('click',()=>{
      menu.remove();
      const name=prompt(_t('建筑名称'));
      if(name&&name.trim()&&typeof addBuilding==='function'){
        const b=addBuilding(name.trim());
        if(b)addFloorPlan(b.id);
      }
    });
    menu.appendChild(newBldItem);
  }
  const rect=anchor.getBoundingClientRect();
  menu.style.position='fixed';
  menu.style.top=(rect.bottom+4)+'px';
  menu.style.left=rect.left+'px';
  document.body.appendChild(menu);
  setTimeout(()=>{
    const closeHandler=()=>{if(document.getElementById('addFloorDropdown'))menu.remove();document.removeEventListener('click',closeHandler)};
    document.addEventListener('click',closeHandler);
  },10);
}

// ====== TAB CLICK ======
function onTabClick(viewId){
  if(currentView===viewId){
    if(viewId==='topology')showTopologyProps();
    else if(typeof showFloorPlanProps==='function')showFloorPlanProps(viewId);
  } else {
    switchView(viewId);
  }
}

// ====== TAB DRAG REORDER (pointer-based) ======
let _tabDrag={active:false,fpId:null,el:null,ghost:null,startX:0,moved:false};

function _tabDragStart(e,fpId){
  if(e.button!==0)return;
  _tabDrag.fpId=fpId;_tabDrag.el=e.currentTarget;_tabDrag.startX=e.clientX;_tabDrag.moved=false;_tabDrag.active=true;
  document.addEventListener('pointermove',_tabDragMove);
  document.addEventListener('pointerup',_tabDragEnd);
}

function _tabDragMove(e){
  if(!_tabDrag.active)return;
  const dx=e.clientX-_tabDrag.startX;
  // Need 5px movement to start dragging
  if(!_tabDrag.moved&&Math.abs(dx)<5)return;
  if(!_tabDrag.moved){
    _tabDrag.moved=true;
    // Create ghost
    const ghost=_tabDrag.el.cloneNode(true);
    ghost.className='view-tab tab-ghost';
    const rect=_tabDrag.el.getBoundingClientRect();
    ghost.style.cssText=`position:fixed;top:${rect.top}px;left:${rect.left}px;width:${rect.width}px;pointer-events:none;z-index:9999;opacity:0.85;`;
    document.body.appendChild(ghost);
    _tabDrag.ghost=ghost;
    _tabDrag.el.style.opacity='0.3';
  }
  // Move ghost
  const rect=_tabDrag.el.getBoundingClientRect();
  _tabDrag.ghost.style.left=(rect.left+e.clientX-_tabDrag.startX)+'px';

  // Find drop target - highlight nearest tab (restricted to same building)
  const container=document.getElementById('viewTabs');
  const dragBldId=_tabDrag.el.dataset.buildingId||'';
  const tabs=container.querySelectorAll('.view-tab[data-fp-id]');
  tabs.forEach(t=>t.classList.remove('drag-over'));
  for(const t of tabs){
    if(t===_tabDrag.el)continue;
    if((t.dataset.buildingId||'')!==dragBldId)continue; // same building only
    const r=t.getBoundingClientRect();
    if(e.clientX>=r.left&&e.clientX<=r.right){
      t.classList.add('drag-over');break;
    }
  }
}

function _tabDragEnd(e){
  document.removeEventListener('pointermove',_tabDragMove);
  document.removeEventListener('pointerup',_tabDragEnd);
  if(!_tabDrag.active)return;

  if(_tabDrag.ghost){_tabDrag.ghost.remove();_tabDrag.ghost=null}
  _tabDrag.el.style.opacity='';

  if(_tabDrag.moved){
    // Find drop target (restricted to same building)
    const container=document.getElementById('viewTabs');
    const dragBldId=_tabDrag.el.dataset.buildingId||'';
    const tabs=container.querySelectorAll('.view-tab[data-fp-id]');
    let targetId=null;
    for(const t of tabs){
      if(t===_tabDrag.el)continue;
      if((t.dataset.buildingId||'')!==dragBldId)continue;
      const r=t.getBoundingClientRect();
      if(e.clientX>=r.left&&e.clientX<=r.right){targetId=t.dataset.fpId;break}
    }
    tabs.forEach(t=>t.classList.remove('drag-over'));
    if(targetId&&targetId!==_tabDrag.fpId){
      const fromIdx=floorPlans.findIndex(f=>f.id===_tabDrag.fpId);
      const toIdx=floorPlans.findIndex(f=>f.id===targetId);
      if(fromIdx>=0&&toIdx>=0){
        const [moved]=floorPlans.splice(fromIdx,1);
        floorPlans.splice(toIdx,0,moved);
        floorPlans.forEach((f,i)=>f.sort_order=i+1);
        hasUnsavedChanges=true;
        rebuildViewTabs();
      }
    }
  } else {
    // No drag happened — treat as click
    onTabClick(_tabDrag.fpId);
  }
  _tabDrag.active=false;_tabDrag.fpId=null;_tabDrag.el=null;
}

function promptRenameFloor(fpId){
  const fp=getFloorPlan(fpId);if(!fp)return;
  const newLabel=prompt(_t('楼层名称（同时作为导出图纸名称）'),fp.label);
  if(newLabel&&newLabel.trim())renameFloorPlan(fpId,newLabel.trim());
}

// ====== LEAVE CONFIRMATION ======
// _leaveAction: 'href' = navigate to _leaveTargetHref, 'reload' = location.reload()
let _leaveTargetHref=null,_leaveAction='href';
window.addEventListener('beforeunload',e=>{if(hasUnsavedChanges){e.preventDefault();e.returnValue=''}});
window.addEventListener('keydown',e=>{
  if(!hasUnsavedChanges)return;
  const isRefresh=(e.key==='F5')||((e.ctrlKey||e.metaKey)&&e.key==='r');
  if(isRefresh){e.preventDefault();_leaveAction='reload';_leaveTargetHref=null;document.getElementById('leaveModal').style.display='flex';}
});
function confirmLeave(el){
  if(!hasUnsavedChanges){return true}
  _leaveTargetHref=el.href;_leaveAction='href';
  document.getElementById('leaveModal').style.display='flex';
  return false;
}
function leaveCancel(){document.getElementById('leaveModal').style.display='none';_leaveTargetHref=null}
function leaveDiscard(){hasUnsavedChanges=false;if(_leaveAction==='reload')location.reload();else if(_leaveTargetHref)window.location.href=_leaveTargetHref}
async function leaveSaveFirst(){
  await saveDiagram();
  if(!hasUnsavedChanges){if(_leaveAction==='reload')location.reload();else if(_leaveTargetHref)window.location.href=_leaveTargetHref;}
  else document.getElementById('leaveModal').style.display='none';
}

// ====== INIT ======
/* ── Left Panel Toggle ── */
function toggleLeftPanel(){
  const panel=document.querySelector('.panel');
  if(!panel)return;
  const backdrop=document.getElementById('panelBackdrop');
  const collapsed=panel.classList.toggle('collapsed');
  if(backdrop){backdrop.classList.toggle('visible',!collapsed)}
  if(window.innerWidth>767){localStorage.setItem('sd_panel_collapsed',collapsed?'1':'0')}
}
function initPanelToggle(){
  const panel=document.querySelector('.panel');
  if(!panel||panel.style.display==='none')return;
  const isMobile=window.innerWidth<=767;
  if(isMobile){panel.classList.add('collapsed')}
  else{if(localStorage.getItem('sd_panel_collapsed')==='1')panel.classList.add('collapsed')}
  document.getElementById('panelToggle')?.addEventListener('click',toggleLeftPanel);
  document.getElementById('panelBackdrop')?.addEventListener('click',toggleLeftPanel);
}

async function init(){
  try{
    const resp=await fetch(DIAGRAM_CONFIG.apiProducts);
    const result=await resp.json();
    if(result.success){buildProductPanel(result.categories)}
    else{document.getElementById('productPanel').innerHTML='<div style="padding:20px;text-align:center;color:var(--delete-text);font-size:12px;">'+_t('加载产品失败')+'</div>'}
  }catch(err){document.getElementById('productPanel').innerHTML='<div style="padding:20px;text-align:center;color:var(--delete-text);font-size:12px;">'+_t('加载产品失败')+': '+err.message+'</div>'}

  if(DIAGRAM_CONFIG.externalMode){await loadDiagram();rebuildViewTabs()}
  else if(DIAGRAM_CONFIG.diagramId){await loadDiagram()}
  else{rebuildViewTabs()}
  pushHistory();
  initPanelToggle();
  if(!DIAGRAM_CONFIG.readOnly)startAutoSave();
}

init();
