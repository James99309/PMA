// PMA · 库存管理 mock data
(function(){

const COMPANIES = [
  { id: "heyuan",   name: "和源通信(上海)股份有限公司", kind: "厂商",   total: 625, kindIcon: "factory" },
  { id: "skhynix",  name: "SK海力士(无锡)产业发展有限公司", kind: "经销商", total: 133, kindIcon: "store" },
  { id: "jiushi",   name: "上海久事国际体育中心有限公司", kind: "客户",   total: 12,  kindIcon: "store" },
  { id: "dazhan",   name: "上海大展通信电子设备有限公司", kind: "客户",   total: 23,  kindIcon: "store" },
  { id: "xinjing",  name: "上海市长宁区新泾镇人民政府",     kind: "客户",   total: 1,   kindIcon: "store" },
  { id: "changsen", name: "上海常森电子有限公司",          kind: "客户",   total: 268, kindIcon: "store" },
  { id: "chunbo",   name: "上海淳泊信息科技有限公司",      kind: "客户",   total: 2,   kindIcon: "store" },
  { id: "hanwang",  name: "上海瀚网智能科技有限公司",      kind: "客户",   total: 514, kindIcon: "store" },
];

const STOCK = [
  { id: 1, name: "DMR常规对讲机",   model: "HYTD4MA",   qty: 120, unit: "台", last: { date: "2026-05-21", type: "入库", delta: +100, note: "采购订单 CG-2605-002 全部签收自动入库" } },
  { id: 2, name: "多信道分合路器", model: "EMA42",     qty: 1,   unit: "件", last: { date: "2026-05-23", type: "入库", delta: +1,   note: "采购订单 CG-2605-003 全部签收自动入库" } },
  { id: 3, name: "多信道分合路器", model: "EMC46",     qty: 1,   unit: "件", last: { date: "2026-05-23", type: "入库", delta: +1,   note: "采购订单 CG-2601-001 全部签收自动入库" } },
  { id: 4, name: "常规数字基站",   model: "BC4I3X4NN", qty: 100, unit: "台", last: null },
  { id: 5, name: "常规数字基站",   model: "BC4I2X4NN", qty: 101, unit: "台", last: { date: "2026-05-23", type: "入库", delta: +1,   note: "采购订单 CG-2601-001 全部签收自动入库" } },
  { id: 6, name: "数字智能信道机", model: "HYPSMXI40", qty: 2,   unit: "件", last: { date: "2026-05-23", type: "入库", delta: +1,   note: "采购订单 CG-2605-003 全部签收自动入库" } },
  { id: 7, name: "射频直放站",     model: "BDA400BLT", qty: 4,   unit: "套", last: { date: "2026-05-22", type: "入库", delta: +4,   note: "采购订单 CG-2604-001 部分签收" } },
  { id: 8, name: "数字基站 Pro",   model: "M3KPRO",    qty: 8,   unit: "套", last: { date: "2026-05-22", type: "入库", delta: +8,   note: "采购订单 CG-2604-001 全部签收自动入库" } },
  { id: 9, name: "双工器",         model: "EDULN4N1CZ2", qty: 0, unit: "件", last: { date: "2026-05-23", type: "出库", delta: -1, note: "发货单 SHP202605-008 出库到客户" } },
];

const TX = [
  { time: "2026-05-23 21:47", product: "数字智能信道机", model: "HYPSMXI40",   type: "入库", delta: +1,   from: 1,   to: 2,   ref: "order#18", refType: "po", note: "采购订单 CG-2605-003 全部签收自动入库", op: "admin" },
  { time: "2026-05-23 21:47", product: "多信道分合路器", model: "EMA42",       type: "入库", delta: +1,   from: 0,   to: 1,   ref: "order#18", refType: "po", note: "采购订单 CG-2605-003 全部签收自动入库", op: "admin" },
  { time: "2026-05-23 19:53", product: "数字智能信道机", model: "HYPSMXI40",   type: "入库", delta: +1,   from: 0,   to: 1,   ref: "order#8",  refType: "po", note: "采购订单 CG-2601-001 全部签收自动入库", op: "admin" },
  { time: "2026-05-23 19:53", product: "多信道分合路器", model: "EMC46",       type: "入库", delta: +1,   from: 0,   to: 1,   ref: "order#8",  refType: "po", note: "采购订单 CG-2601-001 全部签收自动入库", op: "admin" },
  { time: "2026-05-23 19:53", product: "常规数字基站",   model: "BC4I2X4NN",   type: "入库", delta: +1,   from: 100, to: 101, ref: "order#8",  refType: "po", note: "采购订单 CG-2601-001 全部签收自动入库", op: "admin" },
  { time: "2026-05-21 23:38", product: "DMR常规对讲机", model: "HYTD4MA",     type: "入库", delta: +100, from: 20,  to: 120, ref: "order#17", refType: "po", note: "采购订单 CG-2605-002 全部签收自动入库", op: "admin" },
  { time: "2026-05-21 11:52", product: "DMR常规对讲机", model: "HYTD4MA",     type: "入库", delta: +20,  from: 0,   to: 20,  ref: "order#15", refType: "po", note: "采购订单 CG-2603-002 全部签收自动入库 [修正:从长泽…]", op: "admin" },
];

const TX_GLOBAL = [
  { time: "2026-05-23 22:56", company: "上海淳泊信息科技有限公司", companyIcon: "store",   product: "双工器",        model: "EDULN4N1CZ2", type: "入库", delta: +1, from: 0, to: 1, ref: "发货单 SHP202605-008", refType: "shp", note: "签收入库", op: "admin" },
  { time: "2026-05-23 22:29", company: "上海淳泊信息科技有限公司", companyIcon: "store",   product: "数字智能信道机", model: "HYPSMXI40",   type: "入库", delta: +1, from: 0, to: 1, ref: "发货单 SHP202605-007", refType: "shp", note: "签收入库", op: "admin" },
  ...TX.map(t => ({ ...t, company: "和源通信(上海)股份有限公司", companyIcon: "factory" })),
];

const ADJUST_REASONS = [
  "盘点差异", "调拨入库", "调拨出库", "损坏报废", "样品出库", "退货入库", "维修返回", "其他",
];

window.PMA_INV = { COMPANIES, STOCK, TX, TX_GLOBAL, ADJUST_REASONS };
})();
