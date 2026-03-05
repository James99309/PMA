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

const SUBCAT_ICON_MAP={
  // Chinese names
  '数字基站':'rru','数字信道机':'channel_radio','广播多频点调频处理器':'fm_processor',
  '室外天线':'antenna_outdoor','室内天线':'antenna_indoor','防爆天线':'antenna_exproof',
  '光纤远端直放站':'oru','光纤近端机':'omu','射频直放站':'repeater','直放站配件':'generic',
  '双工器':'combiner','系统合路器':'combiner','合路器':'combiner','信号剥离器':'signal_stripper',
  '分路器':'splitter_2','多信道分合路器':'splitter_3','一体化分合路矩阵':'matrix',
  '耦合器':'coupler','分配器':'splitter_2',
  '数字对讲机':'radio','充电器':'charger','电池板':'battery',
  '射频电缆及配件':'cable_coax','光纤电缆及配件':'cable_fiber','衰减器':'attenuator',
  '馈线接地卡':'grounding','交换机':'switch','天线配件':'connector','直流隔断器':'dc_blocker',
  '终端负载':'load','机柜':'cabinet','防爆盒':'cabinet',
  '应用功能':'software','许可证':'license','服务软件':'software','服务器主机':'server',
  '主站频率占用费':'service','对讲机频率占用费':'service','施工附件':'service',
  '电磁环境检测及申报报告费':'service','调试开通':'service',
  // English names (SG NAS)
  'Base station':'bbu','Repeater':'channel_radio','FM Broadcast':'fm_processor',
  'Indoor antenna':'antenna_indoor','Outdoor antenna':'antenna_outdoor','Explosion-proof antenna':'antenna_exproof',
  'ORU':'oru','OMU':'omu','RF BDA':'repeater',
  'RF Combiner':'combiner','Hybrid Combiner':'combiner','System Combiner':'combiner',
  'Duplex':'combiner','Signal Stripper':'signal_stripper','Splitter':'splitter_2',
  'Multi-Coupler':'coupler','Coupler':'coupler','Matrix':'matrix',
  'Two-way radio':'radio','Battery':'battery','Charge':'charger',
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

function getIconForProduct(product,subcatName,subcatIconKey){
  if(product.iconSvg) return product.iconSvg;
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
    floor_id:null, area_label:'', floor_label:''
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
      is_riser_node:n.is_riser_node||false,_floorCreated:n._floorCreated||false,
      labelPosition:n.labelPosition||null,locked:n.locked||false,
      showCoverage:n.showCoverage,coverageRadii:n.coverageRadii,coverageVisible:n.coverageVisible,coverageN:n.coverageN})),
    edges:edges.map(e=>({id:e.id,sourceId:e.sourceId,sourcePort:e.sourcePort,targetId:e.targetId,targetPort:e.targetPort,
      cableType:e.cableType,color:e.color,width:e.width,dash:e.dash,label:e.label,
      hideLabel:e.hideLabel||false,routeMode:e.routeMode,midPos:e.midPos})),
    nodeIdCounter,edgeIdCounter,
    floor_plans:fpData,
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
    if(isConnecting){polylineWaypoints=[];isConnecting=false;connSourceId=null;if(isReconnecting){const re=edges.find(e2=>e2.id===reconnectEdgeId);if(re)delete re._hidden;isReconnecting=false;reconnectEdgeId=null;reconnectEnd=''}if(typeof isReconnectingFloor!=='undefined'&&isReconnectingFloor){isReconnectingFloor=false;reconnectFloorRouteId=null;reconnectFloorEnd='';reconnectFloorFixedPos=null}document.getElementById('tempLayer').innerHTML='';setTool('select');renderAll();return}
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

function toggleExportMenu(){
  const menu=document.getElementById('exportMenu');
  if(menu.style.display==='block'){menu.style.display='none'}
  else{menu.style.display='block';setTimeout(()=>{document.addEventListener('click',function closeMenu(){menu.style.display='none';document.removeEventListener('click',closeMenu)})},0)}
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
      is_riser_node:n.is_riser_node||false,_floorCreated:n._floorCreated||false,
      labelPosition:n.labelPosition||null,locked:n.locked||false,
      showCoverage:n.showCoverage,coverageRadii:n.coverageRadii,coverageVisible:n.coverageVisible,coverageN:n.coverageN})),
    edges:edges.map(e=>{const o={id:e.id,sourceId:e.sourceId,sourcePort:e.sourcePort,targetId:e.targetId,targetPort:e.targetPort,cableType:e.cableType,color:e.color,width:e.width,dash:e.dash,label:e.label,hideLabel:e.hideLabel||false,routeMode:e.routeMode,midPos:e.midPos};if(e.waypoints&&e.waypoints.length)o.waypoints=e.waypoints;return o}),
    viewX,viewY,scale,nodeIdCounter,edgeIdCounter,
    floor_plans:fpData,
    floorPlanIdCounter,
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
  if(data.floor_plans&&typeof restoreFloorPlans==='function'){restoreFloorPlans(data.floor_plans)}
  if(data.floorPlanIdCounter)floorPlanIdCounter=data.floorPlanIdCounter;
  if(data.routeIdCounter&&typeof routeIdCounter!=='undefined')routeIdCounter=data.routeIdCounter;
  if(data.areaIdCounter&&typeof areaIdCounter!=='undefined')areaIdCounter=data.areaIdCounter;
  if(data.topoAreas)topoAreas=data.topoAreas;
  if(data.displaySettings){const ds=Object.assign({cableWidth:1,cableBlack:false,cableLabel:true,cableLength:true,iconWidth:1,iconBlack:false,iconLabel:true,iconModel:true,showCoverage:'individual',showCoverageInner:true,showCoverageMid:true,coverageFill:true,coverageMode:'circles'},data.displaySettings);delete ds.coverageN;delete ds.showCoverageOuter;if(ds.showCoverage===true)ds.showCoverage='individual';if(ds.showCoverage===false)ds.showCoverage='off';displaySettings=ds;}
  updateTransform();renderAll();
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
  if(viewId==='topology'){
    viewX=topoViewX;viewY=topoViewY;scale=topoScale;
  } else {
    const fp=getFloorPlan(viewId);
    if(fp&&fp.viewX!==undefined){viewX=fp.viewX;viewY=fp.viewY;scale=fp.scale||1}
    else{viewX=0;viewY=0;scale=1}
  }
  updateTransform();
  document.getElementById('zoomLevel').textContent=Math.round(scale*100)+'%';
  // Update tab UI
  document.querySelectorAll('.view-tab').forEach(t=>t.classList.toggle('active',t.dataset.view===viewId));
  // Update toolbar visibility
  const fpTools=document.getElementById('floorPlanTools');
  if(fpTools)fpTools.style.display=viewId==='topology'?'none':'flex';
  if(viewId!=='topology'&&typeof updateFloorBgButton==='function')updateFloorBgButton(viewId);
  const btnRelayout=document.getElementById('btnRelayout');
  if(btnRelayout)btnRelayout.style.display=viewId==='topology'?'':'none';
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
  if(typeof buildExistingDevicesPanel==='function')buildExistingDevicesPanel();
}

// ====== FLOOR PLAN CRUD ======
function getFloorPlan(id){
  if(typeof floorPlans==='undefined')return null;
  return floorPlans.find(fp=>fp.id===id);
}

function addFloorPlan(){
  if(DIAGRAM_CONFIG.readOnly)return;
  if(typeof floorPlans==='undefined')window.floorPlans=[];
  const id='fp_'+floorPlanIdCounter++;
  const label=(floorPlans.length+1)+'F';
  floorPlans.push({
    id:id,label:label,sort_order:floorPlans.length+1,
    background:null,calibration:null,
    placements:[],routes:[],areas:[],
    viewX:0,viewY:0,scale:1
  });
  hasUnsavedChanges=true;
  rebuildViewTabs();
  switchView(id);
}

function addFloorPlanWithBackground(label,background){
  if(typeof floorPlans==='undefined')window.floorPlans=[];
  const id='fp_'+floorPlanIdCounter++;
  floorPlans.push({
    id:id,label:label,sort_order:floorPlans.length+1,
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

function rebuildViewTabs(){
  const container=document.getElementById('viewTabs');
  if(!container)return;
  container.innerHTML='';

  // Left arrow
  const arrowL=document.createElement('button');
  arrowL.className='view-tabs-arrow';
  arrowL.innerHTML='&#9664;';
  arrowL.addEventListener('click',()=>{inner.scrollLeft-=120});
  container.appendChild(arrowL);

  // Scrollable inner container
  const inner=document.createElement('div');
  inner.className='view-tabs-inner';
  container.appendChild(inner);

  // Right arrow
  const arrowR=document.createElement('button');
  arrowR.className='view-tabs-arrow';
  arrowR.innerHTML='&#9654;';
  arrowR.addEventListener('click',()=>{inner.scrollLeft+=120});
  container.appendChild(arrowR);

  // Update arrow visibility based on scroll state
  function updateArrows(){
    const canL=inner.scrollLeft>0;
    const canR=inner.scrollLeft<inner.scrollWidth-inner.clientWidth-1;
    arrowL.classList.toggle('visible',canL);
    arrowR.classList.toggle('visible',canR);
  }
  inner.addEventListener('scroll',updateArrows);

  // Topology tab (not draggable)
  const topoTab=document.createElement('div');
  topoTab.className='view-tab'+(currentView==='topology'?' active':'');
  topoTab.dataset.view='topology';
  topoTab.textContent='🔧 '+_t('系统图');
  topoTab.addEventListener('click',()=>onTabClick('topology'));
  inner.appendChild(topoTab);

  // Floor plan tabs (draggable via pointer events)
  if(typeof floorPlans!=='undefined'){
    floorPlans.forEach(fp=>{
      const tab=document.createElement('div');
      tab.className='view-tab';
      if(currentView===fp.id)tab.classList.add('active');
      tab.dataset.view=fp.id;
      tab.dataset.fpId=fp.id;
      tab.textContent=fp.label;
      tab.addEventListener('pointerdown',e=>_tabDragStart(e,fp.id));
      inner.appendChild(tab);
    });
  }

  // Add floor button (hidden in read-only mode)
  if(!DIAGRAM_CONFIG.readOnly){
    const addBtn=document.createElement('div');
    addBtn.className='view-tab-add';
    addBtn.textContent=_t('添加楼层');
    addBtn.addEventListener('click',()=>addFloorPlan());
    inner.appendChild(addBtn);
  }

  // Scroll active tab into view & update arrows after layout
  requestAnimationFrame(()=>{
    const activeTab=inner.querySelector('.view-tab.active');
    if(activeTab)activeTab.scrollIntoView({block:'nearest',inline:'nearest'});
    updateArrows();
  });
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

  // Find drop target - highlight nearest tab
  const container=document.getElementById('viewTabs');
  const tabs=container.querySelectorAll('.view-tab[data-fp-id]');
  tabs.forEach(t=>t.classList.remove('drag-over'));
  for(const t of tabs){
    if(t===_tabDrag.el)continue;
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
    // Find drop target
    const container=document.getElementById('viewTabs');
    const tabs=container.querySelectorAll('.view-tab[data-fp-id]');
    let targetId=null;
    for(const t of tabs){
      if(t===_tabDrag.el)continue;
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
}

init();
