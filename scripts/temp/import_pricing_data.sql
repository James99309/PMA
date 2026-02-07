-- ============================================================
-- 批价单/结算单批量导入 SQL
-- 生成时间: 2026-02-07 08:36:32
-- 项目数: 35, 总明细数: 295
-- ============================================================

BEGIN;

-- ========== 项目 #1: 上海名人苑 (project_id=17) ==========
-- 明细数: 13, 提货总额: 205331.85, 结算总额: 184799.14

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-001', 17, 505, 288, 282, false, false, 'channel_follow', 'approved', 1, 205331.85, 0.450000, 184799.14, 0.405001, 5, NOW(), 14, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (13 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), 'DMR数字智能信道机 400MHz 25W', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '套', 'HYPSMXI40', 13580.00, 6111.00, 8, 0.450000, 48888.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '套', 'ECM1B042CZ1', 6642.00, 2988.90, 2, 0.450000, 5977.80, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 63.90, 20, 0.450000, 1278.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '室外全向玻璃钢天线 400-430MHz', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 'EANLOMO5HR1', 458.00, 206.10, 2, 0.450000, 412.20, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 4444.20, 8, 0.450000, 35553.60, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 5332.95, 7, 0.450000, 37330.65, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.00, 599.85, 80, 0.450000, 47988.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 63.90, 120, 0.450000, 7668.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 63.90, 100, 0.450000, 6390.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU4xCZ1', 2493.00, 1121.85, 2, 0.450000, 2243.70, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1688.85, 2, 0.450000, 3377.70, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 2056.05, 2, 0.450000, 4112.10, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 2056.05, 2, 0.450000, 4112.10, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-001', currval('pricing_orders_id_seq'), 17, 505, 282, 288, false, false, 184799.14, 0.405001, 'approved', 'pending', 5, NOW(), 14, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (13 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (13 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), 'DMR数字智能信道机 400MHz 25W', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '套', 'HYPSMXI40', 13580.00, 5499.90, 8, 0.405000, 43999.20, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '套', 'ECM1B042CZ1', 6642.00, 2690.01, 2, 0.405000, 5380.02, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 57.51, 20, 0.405000, 1150.20, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '室外全向玻璃钢天线 400-430MHz', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 'EANLOMO5HR1', 458.00, 185.49, 2, 0.405000, 370.98, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 3999.78, 8, 0.405000, 31998.24, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 4799.66, 7, 0.405000, 33597.62, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 5 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.00, 539.87, 80, 0.405000, 43189.60, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 6 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 57.51, 120, 0.405000, 6901.20, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 7 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 57.51, 100, 0.405000, 5751.00, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 8 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU4xCZ1', 2493.00, 1009.67, 2, 0.405000, 2019.34, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 9 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1519.97, 2, 0.405000, 3039.94, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 10 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 1850.45, 2, 0.405000, 3700.90, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 11 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 1850.45, 2, 0.405000, 3700.90, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 12 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #2: 上海嘉定集成电路研发中心增补 (project_id=136) ==========
-- 明细数: 2, 提货总额: 52875.00, 结算总额: 47587.50

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-002', 136, 536, 288, 282, false, false, 'channel_follow', 'approved', 1, 52875.00, 0.450000, 47587.50, 0.405000, 5, NOW(), 14, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (2 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '网讯平台服务 软件', 'NFX_MAST_OPETN', '-账户创建和访问管理-设备数据和系统数据的存储和恢复-产品库数据-系统拓扑和设备位置显示和管理-系统资源统计和告警分析推送-系统工作台主次账号一个-20个远端站授权，4个信道机授权，100个终端授权', '和源通信', '套', 'HYWP0NC1', 105000.00, 47250.00, 1, 0.450000, 47250.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '网讯网关服务 软件', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '套', 'HYWG0NB1', 12500.00, 5625.00, 1, 0.450000, 5625.00, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-002', currval('pricing_orders_id_seq'), 136, 536, 282, 288, false, false, 47587.50, 0.405000, 'approved', 'pending', 5, NOW(), 14, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (2 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (2 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '网讯平台服务 软件', 'NFX_MAST_OPETN', '-账户创建和访问管理-设备数据和系统数据的存储和恢复-产品库数据-系统拓扑和设备位置显示和管理-系统资源统计和告警分析推送-系统工作台主次账号一个-20个远端站授权，4个信道机授权，100个终端授权', '和源通信', '套', 'HYWP0NC1', 105000.00, 42525.00, 1, 0.405000, 42525.00, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '网讯网关服务 软件', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '套', 'HYWG0NB1', 12500.00, 5062.50, 1, 0.405000, 5062.50, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #3: 上海市松江区巨人科技园B楼项目弱电智能化投标项目 (project_id=129) ==========
-- 明细数: 8, 提货总额: 39092.85, 结算总额: 35183.58

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-003', 129, 349, 21, 282, false, false, 'channel_follow', 'approved', 1, 39092.85, 0.450000, 35183.58, 0.405000, 5, NOW(), 16, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (8 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 4444.20, 2, 0.450000, 8888.40, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '常规射频直放站 420 2W', 'E-BDA400B LT', '频率范围：410~414/420~424 ,带宽：≤4M 输出：2W 功能：正面状态灯', '和源通信', '套', 'HYR1SN140', 8396.00, 3778.20, 2, 0.450000, 7556.40, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 1044.00, 1, 0.450000, 1044.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 5332.95, 2, 0.450000, 10665.90, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 63.90, 69, 0.450000, 4409.10, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 63.90, 68, 0.450000, 4345.20, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 63.90, 2, 0.450000, 127.80, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-003', currval('pricing_orders_id_seq'), 129, 349, 282, 21, false, false, 35183.58, 0.405000, 'approved', 'pending', 5, NOW(), 16, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (8 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (8 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 3999.78, 2, 0.405000, 7999.56, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '常规射频直放站 420 2W', 'E-BDA400B LT', '频率范围：410~414/420~424 ,带宽：≤4M 输出：2W 功能：正面状态灯', '和源通信', '套', 'HYR1SN140', 8396.00, 3400.38, 2, 0.405000, 6800.76, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 939.60, 1, 0.405000, 939.60, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 4799.66, 2, 0.405000, 9599.32, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 57.51, 69, 0.405000, 3968.19, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 5 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 57.51, 68, 0.405000, 3910.68, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 6 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 57.51, 2, 0.405000, 115.02, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 7 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #4: 上海静安太保家园 (project_id=130) ==========
-- 明细数: 10, 提货总额: 52657.20, 结算总额: 47391.69

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-004', 130, 350, 21, 282, false, false, 'channel_follow', 'approved', 1, 52657.20, 0.450000, 47391.69, 0.405002, 5, NOW(), 16, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (10 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '常规射频直放站 420 2W', 'E-BDA400B LT', '频率范围：410~414/420~424 ,带宽：≤4M 输出：2W 功能：正面状态灯', '和源通信', '套', 'HYR1SN140', 8396.00, 3778.20, 1, 0.450000, 3778.20, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 63.90, 59, 0.450000, 3770.10, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.00, 599.85, 40, 0.450000, 23994.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), 'DMR数字智能信道机 400MHz 25W', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '套', 'HYPSMXI40', 13580.00, 6111.00, 2, 0.450000, 12222.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 1044.00, 1, 0.450000, 1044.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1688.85, 1, 0.450000, 1688.85, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 63.90, 60, 0.450000, 3834.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '室外全向玻璃钢天线 400-430MHz', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 'EANLOMO5HR1', 458.00, 206.10, 1, 0.450000, 206.10, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 63.90, 1, 0.450000, 63.90, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-004', currval('pricing_orders_id_seq'), 130, 350, 282, 21, false, false, 47391.69, 0.405002, 'approved', 'pending', 5, NOW(), 16, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (10 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (10 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '常规射频直放站 420 2W', 'E-BDA400B LT', '频率范围：410~414/420~424 ,带宽：≤4M 输出：2W 功能：正面状态灯', '和源通信', '套', 'HYR1SN140', 8396.00, 3400.38, 1, 0.405000, 3400.38, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 57.51, 59, 0.405000, 3393.09, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.00, 539.87, 40, 0.405000, 21594.80, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), 'DMR数字智能信道机 400MHz 25W', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '套', 'HYPSMXI40', 13580.00, 5499.90, 2, 0.405000, 10999.80, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 939.60, 1, 0.405000, 939.60, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 5 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1519.97, 1, 0.405000, 1519.97, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 6 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 57.51, 60, 0.405000, 3450.60, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 7 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '室外全向玻璃钢天线 400-430MHz', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 'EANLOMO5HR1', 458.00, 185.49, 1, 0.405000, 185.49, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 8 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 57.51, 1, 0.405000, 57.51, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 9 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #5: 东莞市博物馆项目 (project_id=679) ==========
-- 明细数: 9, 提货总额: 31743.00, 结算总额: 28568.73

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-005', 679, 735, 497, 496, false, false, 'channel_follow', 'approved', 1, 31743.00, 0.450000, 28568.73, 0.405000, 5, NOW(), 17, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (9 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 1044.00, 1, 0.450000, 1044.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：402-406/412-416MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ2', 3753.00, 1688.85, 1, 0.450000, 1688.85, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 4444.20, 1, 0.450000, 4444.20, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：403-405/413-415MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI14A', 11851.00, 5332.95, 2, 0.450000, 10665.90, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 63.90, 60, 0.450000, 3834.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 63.90, 61, 0.450000, 3897.90, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-005', currval('pricing_orders_id_seq'), 679, 735, 496, 497, false, false, 28568.73, 0.405000, 'approved', 'pending', 5, NOW(), 17, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (9 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (9 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 939.60, 1, 0.405000, 939.60, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：402-406/412-416MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ2', 3753.00, 1519.97, 1, 0.405000, 1519.97, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 3999.78, 1, 0.405000, 3999.78, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 5 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：403-405/413-415MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI14A', 11851.00, 4799.66, 2, 0.405000, 9599.32, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 6 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 57.51, 60, 0.405000, 3450.60, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 7 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 57.51, 61, 0.405000, 3508.11, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 8 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #6: 中欧轨道智能交通国际研创基地启动区项目智城大厦 (project_id=573) ==========
-- 明细数: 13, 提货总额: 72127.35, 结算总额: 64914.81

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-006', 573, 655, 21, 282, false, false, 'channel_follow', 'approved', 1, 72127.35, 0.450000, 64914.81, 0.405001, 5, NOW(), 16, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (13 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), 'DMR数字智能信道机 350MHz 25W', 'Mark1000 MAX', '频率范围：350~400MHz-功率 25W-网讯平台-数模兼容', '和源通信', '套', 'HYPSMXI30', 14583.00, 6562.35, 2, 0.450000, 13124.70, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 1044.00, 1, 0.450000, 1044.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1688.85, 1, 0.450000, 1688.85, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 4444.20, 2, 0.450000, 8888.40, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 5332.95, 3, 0.450000, 15998.85, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 63.90, 53, 0.450000, 3386.70, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 63.90, 50, 0.450000, 3195.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '室外定向板状天线 400-430MHz', 'E-ANTD 400', '频率范围：400-430MHz 增益：2.5dBi 防护等级：IP65 辐射方向：定向 最大承载功率：50W 接头类型：N-Femade 特性：室外', '和源通信', '套', 'EAN2OFD2TE2', 354.00, 159.30, 4, 0.450000, 637.20, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.00, 599.85, 10, 0.450000, 5998.50, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.00, 599.85, 20, 0.450000, 11997.00, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-006', currval('pricing_orders_id_seq'), 573, 655, 282, 21, false, false, 64914.81, 0.405001, 'approved', 'pending', 5, NOW(), 16, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (13 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (13 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), 'DMR数字智能信道机 350MHz 25W', 'Mark1000 MAX', '频率范围：350~400MHz-功率 25W-网讯平台-数模兼容', '和源通信', '套', 'HYPSMXI30', 14583.00, 5906.12, 2, 0.405000, 11812.24, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 939.60, 1, 0.405000, 939.60, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1519.97, 1, 0.405000, 1519.97, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 5 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 3999.78, 2, 0.405000, 7999.56, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 6 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 4799.66, 3, 0.405000, 14398.98, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 7 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 57.51, 53, 0.405000, 3048.03, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 8 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 57.51, 50, 0.405000, 2875.50, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 9 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '室外定向板状天线 400-430MHz', 'E-ANTD 400', '频率范围：400-430MHz 增益：2.5dBi 防护等级：IP65 辐射方向：定向 最大承载功率：50W 接头类型：N-Femade 特性：室外', '和源通信', '套', 'EAN2OFD2TE2', 354.00, 143.37, 4, 0.405000, 573.48, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 10 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.00, 539.87, 10, 0.405000, 5398.70, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 11 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.00, 539.87, 20, 0.405000, 10797.40, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 12 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #7: 九星城项目 (project_id=187) ==========
-- 明细数: 9, 提货总额: 549825.18, 结算总额: 520104.90

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-007', 187, 546, 288, 282, false, false, 'channel_follow', 'approved', 1, 549825.18, 0.370000, 520104.90, 0.350000, 5, NOW(), 14, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (9 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 52.54, 1561, 0.370000, 82014.94, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 52.54, 1607, 0.370000, 84431.78, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '室外全向玻璃钢天线 400-430MHz', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 'EANLOMO5HR1', 458.00, 169.46, 9, 0.370000, 1525.14, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 1690.53, 3, 0.370000, 5071.59, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 1690.53, 3, 0.370000, 5071.59, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 3654.12, 18, 0.370000, 65774.16, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 4384.87, 69, 0.370000, 302556.03, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '套', 'ECM1B042CZ1', 6642.00, 2457.54, 1, 0.370000, 2457.54, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU4xCZ1', 2493.00, 922.41, 1, 0.370000, 922.41, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-007', currval('pricing_orders_id_seq'), 187, 546, 282, 288, false, false, 520104.90, 0.350000, 'approved', 'pending', 5, NOW(), 14, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (9 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (9 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 49.70, 1561, 0.350000, 77581.70, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 49.70, 1607, 0.350000, 79867.90, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '室外全向玻璃钢天线 400-430MHz', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 'EANLOMO5HR1', 458.00, 160.30, 9, 0.350000, 1442.70, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 1599.15, 3, 0.350000, 4797.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 1599.15, 3, 0.350000, 4797.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 3456.60, 18, 0.350000, 62218.80, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 5 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 4147.85, 69, 0.350000, 286201.65, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 6 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '套', 'ECM1B042CZ1', 6642.00, 2324.70, 1, 0.350000, 2324.70, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 7 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU4xCZ1', 2493.00, 872.55, 1, 0.350000, 872.55, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 8 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #8: 华虹张江工厂配套用房 (project_id=61) ==========
-- 明细数: 10, 提货总额: 69755.40, 结算总额: 62779.91

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-008', 61, 514, 497, 496, false, false, 'channel_follow', 'approved', 1, 69755.40, 0.450000, 62779.91, 0.405000, 5, NOW(), 14, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (10 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 4444.20, 2, 0.450000, 8888.40, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 5332.95, 6, 0.450000, 31997.70, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 63.90, 142, 0.450000, 9073.80, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 63.90, 145, 0.450000, 9265.50, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '套', 'ECM1B042CZ1', 6642.00, 2988.90, 1, 0.450000, 2988.90, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU4xCZ1', 2493.00, 1121.85, 1, 0.450000, 1121.85, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1688.85, 1, 0.450000, 1688.85, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '室外全向玻璃钢天线 400-430MHz', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 'EANLOMO5HR1', 458.00, 206.10, 3, 0.450000, 618.30, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-008', currval('pricing_orders_id_seq'), 61, 514, 496, 497, false, false, 62779.91, 0.405000, 'approved', 'pending', 5, NOW(), 14, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (10 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (10 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 3999.78, 2, 0.405000, 7999.56, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 4799.66, 6, 0.405000, 28797.96, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 57.51, 142, 0.405000, 8166.42, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 57.51, 145, 0.405000, 8338.95, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '套', 'ECM1B042CZ1', 6642.00, 2690.01, 1, 0.405000, 2690.01, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU4xCZ1', 2493.00, 1009.67, 1, 0.405000, 1009.67, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 5 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 6 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 7 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1519.97, 1, 0.405000, 1519.97, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 8 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '室外全向玻璃钢天线 400-430MHz', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 'EANLOMO5HR1', 458.00, 185.49, 3, 0.405000, 556.47, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 9 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #9: 台泥公亮大楼酒店 (project_id=416) ==========
-- 明细数: 12, 提货总额: 58134.60, 结算总额: 52321.27

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-009', 416, 719, 319, 496, false, false, 'channel_follow', 'approved', 1, 58134.60, 0.450000, 52321.27, 0.405001, 5, NOW(), 15, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (12 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.00, 599.85, 20, 0.450000, 11997.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 1044.00, 1, 0.450000, 1044.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 4444.20, 1, 0.450000, 4444.20, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1688.85, 1, 0.450000, 1688.85, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 63.90, 78, 0.450000, 4984.20, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 63.90, 52, 0.450000, 3322.80, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 63.90, 25, 0.450000, 1597.50, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), 'DMR数字智能信道机 400MHz 25W', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '套', 'HYPSMXI40', 13580.00, 6111.00, 2, 0.450000, 12222.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 5332.95, 2, 0.450000, 10665.90, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-009', currval('pricing_orders_id_seq'), 416, 719, 496, 319, false, false, 52321.27, 0.405001, 'approved', 'pending', 5, NOW(), 15, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (12 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (12 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.00, 539.87, 20, 0.405000, 10797.40, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 939.60, 1, 0.405000, 939.60, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 3999.78, 1, 0.405000, 3999.78, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 5 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1519.97, 1, 0.405000, 1519.97, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 6 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 57.51, 78, 0.405000, 4485.78, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 7 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 57.51, 52, 0.405000, 2990.52, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 8 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 57.51, 25, 0.405000, 1437.75, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 9 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), 'DMR数字智能信道机 400MHz 25W', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '套', 'HYPSMXI40', 13580.00, 5499.90, 2, 0.405000, 10999.80, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 10 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 4799.66, 2, 0.405000, 9599.32, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 11 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #10: 合肥机场东区国际货站扩建工程民航专业工程 (project_id=99) ==========
-- 明细数: 9, 提货总额: 11441.25, 结算总额: 11441.25

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-010', 99, 427, 508, NULL, false, false, 'sales_focus', 'approved', 1, 11441.25, 0.450000, 11441.25, 0.450000, 5, NOW(), 13, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (9 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '馈电功率分配器', 'MAPD-2', '频率范围：350-470MHz 承载功率：50W 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '套', 'HYCDF24Y', 291.00, 130.95, 4, 0.450000, 523.80, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '馈电定向耦合器', 'MADC-6', '频率范围：350-470MHz 承载功率：50W 耦合规格：6dB 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '套', 'HYCCF34Y', 344.00, 154.80, 1, 0.450000, 154.80, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '馈电定向耦合器', 'MADC-10', '频率范围：350-470MHz 承载功率：50W 耦合规格：10dB 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '套', 'HYCCF44Y', 344.00, 154.80, 2, 0.450000, 309.60, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '馈电定向耦合器', 'MADC-15', '频率范围：350-470MHz 承载功率：50W 耦合规格：15dB 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '套', 'HYCCF54Y', 344.00, 154.80, 1, 0.450000, 154.80, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '馈电功率分配器', 'MAPD-2', '频率范围：350-470MHz 承载功率：50W 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '套', 'HYCDF24Y', 291.00, 130.95, 12, 0.450000, 1571.40, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '馈电定向耦合器', 'MADC-6', '频率范围：350-470MHz 承载功率：50W 耦合规格：6dB 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '套', 'HYCCF34Y', 344.00, 154.80, 8, 0.450000, 1238.40, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '馈电定向耦合器', 'MADC-10', '频率范围：350-470MHz 承载功率：50W 耦合规格：10dB 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '套', 'HYCCF44Y', 344.00, 154.80, 8, 0.450000, 1238.40, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '馈电定向耦合器', 'MADC-15', '频率范围：350-470MHz 承载功率：50W 耦合规格：15dB 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '套', 'HYCCF54Y', 344.00, 154.80, 4, 0.450000, 619.20, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能室内全向吸顶天线', 'MA11', '频率范围：350-470MHz 承载功率：50W 性能：室内全向 天线增益：0dBi 信号电平检测', '和源通信', '套', 'HYAIOCL4Y', 291.00, 130.95, 43, 0.450000, 5630.85, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-010', currval('pricing_orders_id_seq'), 99, 427, NULL, 508, false, false, 11441.25, 0.450000, 'approved', 'pending', 5, NOW(), 13, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (9 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (9 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '馈电功率分配器', 'MAPD-2', '频率范围：350-470MHz 承载功率：50W 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '套', 'HYCDF24Y', 291.00, 130.95, 4, 0.450000, 523.80, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '馈电定向耦合器', 'MADC-6', '频率范围：350-470MHz 承载功率：50W 耦合规格：6dB 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '套', 'HYCCF34Y', 344.00, 154.80, 1, 0.450000, 154.80, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '馈电定向耦合器', 'MADC-10', '频率范围：350-470MHz 承载功率：50W 耦合规格：10dB 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '套', 'HYCCF44Y', 344.00, 154.80, 2, 0.450000, 309.60, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '馈电定向耦合器', 'MADC-15', '频率范围：350-470MHz 承载功率：50W 耦合规格：15dB 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '套', 'HYCCF54Y', 344.00, 154.80, 1, 0.450000, 154.80, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '馈电功率分配器', 'MAPD-2', '频率范围：350-470MHz 承载功率：50W 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '套', 'HYCDF24Y', 291.00, 130.95, 12, 0.450000, 1571.40, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '馈电定向耦合器', 'MADC-6', '频率范围：350-470MHz 承载功率：50W 耦合规格：6dB 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '套', 'HYCCF34Y', 344.00, 154.80, 8, 0.450000, 1238.40, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 5 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '馈电定向耦合器', 'MADC-10', '频率范围：350-470MHz 承载功率：50W 耦合规格：10dB 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '套', 'HYCCF44Y', 344.00, 154.80, 8, 0.450000, 1238.40, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 6 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '馈电定向耦合器', 'MADC-15', '频率范围：350-470MHz 承载功率：50W 耦合规格：15dB 分路端口数量：2 防护等级：IP65 应用：馈电', '和源通信', '套', 'HYCCF54Y', 344.00, 154.80, 4, 0.450000, 619.20, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 7 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能室内全向吸顶天线', 'MA11', '频率范围：350-470MHz 承载功率：50W 性能：室内全向 天线增益：0dBi 信号电平检测', '和源通信', '套', 'HYAIOCL4Y', 291.00, 130.95, 43, 0.450000, 5630.85, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 8 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #11: 太保家园成都国际颐养社区项目 (project_id=71) ==========
-- 明细数: 10, 提货总额: 42037.20, 结算总额: 37833.55

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-011', 71, 425, 340, 282, false, false, 'channel_follow', 'approved', 1, 42037.20, 0.450000, 37833.55, 0.405001, 5, NOW(), 13, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (10 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 63.90, 35, 0.450000, 2236.50, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '双工器 400MHz', 'E-SGQ400D', '频率范围：410-414/420-424MHz 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 隔离方式：带通 工作带宽：4M 安装方式：机柜式 尺寸：2U', '和源通信', '套', 'EDULB4H1CZ1', 7876.00, 3544.20, 1, 0.450000, 3544.20, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '系统合路器 300-400MHz', 'E-FHP2000-2', '频率范围：351-366/410-424MHz 单端口承载功率：50W 插入损耗：≤1.5dB 接入端口数量：2 安装方式：机柜式 尺寸：2U', '和源通信', '套', 'ECM1BB22CZ2', 7917.00, 3562.65, 2, 0.450000, 7125.30, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '室外全向玻璃钢天线 400-430MHz', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 'EANLOMO5HR1', 458.00, 206.10, 8, 0.450000, 1648.80, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.00, 599.85, 10, 0.450000, 5998.50, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), 'DMR数字智能信道机 400MHz 25W', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '套', 'HYPSMXI40', 13580.00, 6111.00, 2, 0.450000, 12222.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 1044.00, 1, 0.450000, 1044.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1688.85, 1, 0.450000, 1688.85, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 63.90, 70, 0.450000, 4473.00, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-011', currval('pricing_orders_id_seq'), 71, 425, 282, 340, false, false, 37833.55, 0.405001, 'approved', 'pending', 5, NOW(), 13, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (10 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (10 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 57.51, 35, 0.405000, 2012.85, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '双工器 400MHz', 'E-SGQ400D', '频率范围：410-414/420-424MHz 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 隔离方式：带通 工作带宽：4M 安装方式：机柜式 尺寸：2U', '和源通信', '套', 'EDULB4H1CZ1', 7876.00, 3189.78, 1, 0.405000, 3189.78, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '系统合路器 300-400MHz', 'E-FHP2000-2', '频率范围：351-366/410-424MHz 单端口承载功率：50W 插入损耗：≤1.5dB 接入端口数量：2 安装方式：机柜式 尺寸：2U', '和源通信', '套', 'ECM1BB22CZ2', 7917.00, 3206.39, 2, 0.405000, 6412.78, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '室外全向玻璃钢天线 400-430MHz', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 'EANLOMO5HR1', 458.00, 185.49, 8, 0.405000, 1483.92, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.00, 539.87, 10, 0.405000, 5398.70, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), 'DMR数字智能信道机 400MHz 25W', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '套', 'HYPSMXI40', 13580.00, 5499.90, 2, 0.405000, 10999.80, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 5 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 6 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 939.60, 1, 0.405000, 939.60, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 7 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1519.97, 1, 0.405000, 1519.97, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 8 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 57.51, 70, 0.405000, 4025.70, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 9 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #12: 学院路科技园东升园（H地块）项目 (project_id=529) ==========
-- 明细数: 3, 提货总额: 30980.70, 结算总额: 27882.65

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-012', 529, 602, 11, 282, false, false, 'channel_follow', 'approved', 1, 30980.70, 0.450000, 27882.65, 0.405000, 5, NOW(), 16, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (3 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 5332.95, 4, 0.450000, 21331.80, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 63.90, 73, 0.450000, 4664.70, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 63.90, 78, 0.450000, 4984.20, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-012', currval('pricing_orders_id_seq'), 529, 602, 282, 11, false, false, 27882.65, 0.405000, 'approved', 'pending', 5, NOW(), 16, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (3 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (3 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 4799.66, 4, 0.405000, 19198.64, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 57.51, 73, 0.405000, 4198.23, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 57.51, 78, 0.405000, 4485.78, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #13: 张江人工智能岛 (project_id=135) ==========
-- 明细数: 15, 提货总额: 320792.40, 结算总额: 288713.34

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-013', 135, 535, 497, 496, false, false, 'channel_follow', 'approved', 1, 320792.40, 0.450000, 288713.34, 0.405000, 5, NOW(), 14, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (15 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '套', 'ECM1B042CZ1', 6642.00, 2988.90, 1, 0.450000, 2988.90, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU4xCZ1', 2493.00, 1121.85, 2, 0.450000, 2243.70, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1688.85, 1, 0.450000, 1688.85, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 2056.05, 2, 0.450000, 4112.10, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 2056.05, 2, 0.450000, 4112.10, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 4444.20, 6, 0.450000, 26665.20, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 5332.95, 12, 0.450000, 63995.40, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤远端直放站 350MHz 10W', 'RFT-BDA310 LT/M', '频率范围：351-356/361-366MHz 带宽：≤5M 输出：10W 2U机箱 功能： 正面状态灯/网讯平台', '和源通信', '套', 'HYR3SI330', 21250.00, 9562.50, 12, 0.450000, 114750.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '系统合路器 300-400MHz', 'E-FHP2000-2', '频率范围：351-366/410-424MHz 单端口承载功率：50W 插入损耗：≤1.5dB 接入端口数量：2 安装方式：机柜式 尺寸：2U', '和源通信', '套', 'ECM1BB22CZ2', 7917.00, 3562.65, 12, 0.450000, 42751.80, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 63.90, 240, 0.450000, 15336.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 63.90, 200, 0.450000, 12780.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 63.90, 40, 0.450000, 2556.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), 'DMR数字智能信道机 350MHz 25W', 'Mark1000 MAX', '频率范围：350~400MHz-功率 25W-网讯平台-数模兼容', '和源通信', '套', 'HYPSMXI30', 14583.00, 6562.35, 3, 0.450000, 19687.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合合路器 350MHz', 'E-FH350-4', '频率范围：350-390MHz 单端口承载功率：50W;插入损耗：≤8.5dB接入端口数量：4;安装方式：机柜式;尺寸：2U', '和源通信', '套', 'ECM1B042CZ2', 6667.00, 3000.15, 1, 0.450000, 3000.15, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '双工器 350MHz', 'E-SGQ350D', '频率范围：351-356/361-366MHz 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 隔离方式：带通 工作带宽：5M 安装方式：机柜式 尺寸：2U', '和源通信', '套', 'EDUPB5H1CZ1', 9167.00, 4125.15, 1, 0.450000, 4125.15, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-013', currval('pricing_orders_id_seq'), 135, 535, 496, 497, false, false, 288713.34, 0.405000, 'approved', 'pending', 5, NOW(), 14, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (15 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (15 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '套', 'ECM1B042CZ1', 6642.00, 2690.01, 1, 0.405000, 2690.01, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU4xCZ1', 2493.00, 1009.67, 2, 0.405000, 2019.34, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1519.97, 1, 0.405000, 1519.97, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 1850.45, 2, 0.405000, 3700.90, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 1850.45, 2, 0.405000, 3700.90, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 3999.78, 6, 0.405000, 23998.68, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 5 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 4799.66, 12, 0.405000, 57595.92, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 6 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤远端直放站 350MHz 10W', 'RFT-BDA310 LT/M', '频率范围：351-356/361-366MHz 带宽：≤5M 输出：10W 2U机箱 功能： 正面状态灯/网讯平台', '和源通信', '套', 'HYR3SI330', 21250.00, 8606.25, 12, 0.405000, 103275.00, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 7 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '系统合路器 300-400MHz', 'E-FHP2000-2', '频率范围：351-366/410-424MHz 单端口承载功率：50W 插入损耗：≤1.5dB 接入端口数量：2 安装方式：机柜式 尺寸：2U', '和源通信', '套', 'ECM1BB22CZ2', 7917.00, 3206.39, 12, 0.405000, 38476.68, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 8 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 57.51, 240, 0.405000, 13802.40, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 9 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 57.51, 200, 0.405000, 11502.00, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 10 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 57.51, 40, 0.405000, 2300.40, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 11 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), 'DMR数字智能信道机 350MHz 25W', 'Mark1000 MAX', '频率范围：350~400MHz-功率 25W-网讯平台-数模兼容', '和源通信', '套', 'HYPSMXI30', 14583.00, 5906.12, 3, 0.405000, 17718.36, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 12 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合合路器 350MHz', 'E-FH350-4', '频率范围：350-390MHz 单端口承载功率：50W;插入损耗：≤8.5dB接入端口数量：4;安装方式：机柜式;尺寸：2U', '和源通信', '套', 'ECM1B042CZ2', 6667.00, 2700.14, 1, 0.405000, 2700.14, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 13 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '双工器 350MHz', 'E-SGQ350D', '频率范围：351-356/361-366MHz 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 隔离方式：带通 工作带宽：5M 安装方式：机柜式 尺寸：2U', '和源通信', '套', 'EDUPB5H1CZ1', 9167.00, 3712.64, 1, 0.405000, 3712.64, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 14 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #14: 张江创新药基地B03C-02B03K-03 (project_id=102) ==========
-- 明细数: 11, 提货总额: 58349.70, 结算总额: 52514.78

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-014', 102, 530, 288, 282, false, false, 'channel_follow', 'approved', 1, 58349.70, 0.450000, 52514.78, 0.405000, 5, NOW(), 14, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (11 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 1044.00, 1, 0.450000, 1044.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 4444.20, 2, 0.450000, 8888.40, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 63.90, 34, 0.450000, 2172.60, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 63.90, 30, 0.450000, 1917.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 63.90, 70, 0.450000, 4473.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1688.85, 1, 0.450000, 1688.85, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 5332.95, 3, 0.450000, 15998.85, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 5332.95, 3, 0.450000, 15998.85, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-014', currval('pricing_orders_id_seq'), 102, 530, 282, 288, false, false, 52514.78, 0.405000, 'approved', 'pending', 5, NOW(), 14, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (11 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (11 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 939.60, 1, 0.405000, 939.60, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 3999.78, 2, 0.405000, 7999.56, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 57.51, 34, 0.405000, 1955.34, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 5 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 57.51, 30, 0.405000, 1725.30, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 6 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 57.51, 70, 0.405000, 4025.70, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 7 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1519.97, 1, 0.405000, 1519.97, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 8 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 4799.66, 3, 0.405000, 14398.98, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 9 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 4799.66, 3, 0.405000, 14398.98, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 10 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #15: 御桥12C-18地块 (project_id=18) ==========
-- 明细数: 9, 提货总额: 36492.30, 结算总额: 32843.18

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-015', 18, 506, 288, 282, false, false, 'channel_follow', 'approved', 1, 36492.30, 0.450000, 32843.18, 0.405001, 5, NOW(), 14, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (9 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), 'DMR数字智能信道机 400MHz 25W', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '套', 'HYPSMXI40', 13580.00, 6111.00, 2, 0.450000, 12222.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.00, 599.85, 20, 0.450000, 11997.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 1044.00, 1, 0.450000, 1044.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1688.85, 1, 0.450000, 1688.85, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 63.90, 29, 0.450000, 1853.10, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 63.90, 20, 0.450000, 1278.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 63.90, 9, 0.450000, 575.10, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '常规射频直放站 420 2W', 'E-BDA400B LT', '频率范围：410~414/420~424 ,带宽：≤4M 输出：2W 功能：正面状态灯', '和源通信', '套', 'HYR1SN140', 8396.00, 3778.20, 1, 0.450000, 3778.20, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-015', currval('pricing_orders_id_seq'), 18, 506, 282, 288, false, false, 32843.18, 0.405001, 'approved', 'pending', 5, NOW(), 14, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (9 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (9 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), 'DMR数字智能信道机 400MHz 25W', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '套', 'HYPSMXI40', 13580.00, 5499.90, 2, 0.405000, 10999.80, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.00, 539.87, 20, 0.405000, 10797.40, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 939.60, 1, 0.405000, 939.60, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1519.97, 1, 0.405000, 1519.97, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 57.51, 29, 0.405000, 1667.79, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 5 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 57.51, 20, 0.405000, 1150.20, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 6 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 57.51, 9, 0.405000, 517.59, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 7 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '常规射频直放站 420 2W', 'E-BDA400B LT', '频率范围：410~414/420~424 ,带宽：≤4M 输出：2W 功能：正面状态灯', '和源通信', '套', 'HYR1SN140', 8396.00, 3400.38, 1, 0.405000, 3400.38, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 8 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #16: 招商282 &01-10 (project_id=784) ==========
-- 明细数: 1, 提货总额: 130896.00, 结算总额: 118260.00

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-016', 784, 808, 632, 496, false, false, 'channel_follow', 'approved', 1, 130896.00, 0.404000, 118260.00, 0.365000, 5, NOW(), 14, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (1 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '防爆型高防护全向天线', 'MAEX 10', '频率范围: 350-470 MHz 增益: 0 dB 工作环境: 室内/室外 极化方向: 全向极化 功能: 防爆 IP防护: IP 65', '和源通信', '套', 'ACC3OOCXS', 7200.00, 2908.80, 45, 0.404000, 130896.00, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-016', currval('pricing_orders_id_seq'), 784, 808, 496, 632, false, false, 118260.00, 0.365000, 'approved', 'pending', 5, NOW(), 14, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (1 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (1 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '防爆型高防护全向天线', 'MAEX 10', '频率范围: 350-470 MHz 增益: 0 dB 工作环境: 室内/室外 极化方向: 全向极化 功能: 防爆 IP防护: IP 65', '和源通信', '套', 'ACC3OOCXS', 7200.00, 2628.00, 45, 0.365000, 118260.00, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #17: 招商银行深圳总部大厦 (project_id=132) ==========
-- 明细数: 9, 提货总额: 189394.65, 结算总额: 170455.32

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-017', 132, 571, 112, 496, false, false, 'channel_follow', 'approved', 1, 189394.65, 0.450000, 170455.32, 0.405000, 5, NOW(), 17, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (9 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：402-406/412-416MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ2', 3753.00, 1688.85, 4, 0.450000, 6755.40, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 4444.20, 5, 0.450000, 22221.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：403-405/413-415MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI14A', 11851.00, 5332.95, 17, 0.450000, 90660.15, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 63.90, 384, 0.450000, 24537.60, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 63.90, 386, 0.450000, 24665.40, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '套', 'ECM1B042CZ1', 6642.00, 2988.90, 4, 0.450000, 11955.60, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU4xCZ1', 2493.00, 1121.85, 4, 0.450000, 4487.40, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-017', currval('pricing_orders_id_seq'), 132, 571, 496, 112, false, false, 170455.32, 0.405000, 'approved', 'pending', 5, NOW(), 17, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (9 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (9 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：402-406/412-416MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ2', 3753.00, 1519.97, 4, 0.405000, 6079.88, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 3999.78, 5, 0.405000, 19998.90, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：403-405/413-415MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI14A', 11851.00, 4799.66, 17, 0.405000, 81594.22, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 57.51, 384, 0.405000, 22083.84, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 57.51, 386, 0.405000, 22198.86, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 5 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 6 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '套', 'ECM1B042CZ1', 6642.00, 2690.01, 4, 0.405000, 10760.04, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 7 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU4xCZ1', 2493.00, 1009.67, 4, 0.405000, 4038.68, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 8 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #18: 招商银行深圳总部大厦（增补） (project_id=27) ==========
-- 明细数: 1, 提货总额: 53330.40, 结算总额: 47997.36

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-018', 27, 560, 112, 496, false, false, 'channel_follow', 'approved', 1, 53330.40, 0.450000, 47997.36, 0.405000, 5, NOW(), 17, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (1 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 4444.20, 12, 0.450000, 53330.40, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-018', currval('pricing_orders_id_seq'), 27, 560, 496, 112, false, false, 47997.36, 0.405000, 'approved', 'pending', 5, NOW(), 17, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (1 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (1 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 3999.78, 12, 0.405000, 47997.36, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #19: 无锡奥林匹克体育产业中心二期项目 (project_id=127) ==========
-- 明细数: 9, 提货总额: 320491.35, 结算总额: 288442.64

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-019', 127, 348, 21, 282, false, false, 'sales_focus', 'approved', 1, 320491.35, 0.450000, 288442.64, 0.405001, 5, NOW(), 16, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (9 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 63.90, 324, 0.450000, 20703.60, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 4444.20, 7, 0.450000, 31109.40, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 63.90, 422, 0.450000, 26965.80, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 63.90, 74, 0.450000, 4728.60, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '室外定向板状天线 400-430MHz', 'E-ANTD 400', '频率范围：400-430MHz 增益：2.5dBi 防护等级：IP65 辐射方向：定向 最大承载功率：50W 接头类型：N-Femade 特性：室外', '和源通信', '套', 'EAN2OFD2TE2', 354.00, 159.30, 28, 0.450000, 4460.40, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '室外全向玻璃钢天线 400-430MHz', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 'EANLOMO5HR1', 458.00, 206.10, 2, 0.450000, 412.20, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.00, 599.85, 40, 0.450000, 23994.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 5332.95, 27, 0.450000, 143989.65, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '系统合路器 300-400MHz', 'E-FHP2000-2', '频率范围：351-366/410-424MHz 单端口承载功率：50W 插入损耗：≤1.5dB 接入端口数量：2 安装方式：机柜式 尺寸：2U', '和源通信', '套', 'ECM1BB22CZ2', 7917.00, 3562.65, 18, 0.450000, 64127.70, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-019', currval('pricing_orders_id_seq'), 127, 348, 282, 21, false, false, 288442.64, 0.405001, 'approved', 'pending', 5, NOW(), 16, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (9 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (9 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 57.51, 324, 0.405000, 18633.24, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 3999.78, 7, 0.405000, 27998.46, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 57.51, 422, 0.405000, 24269.22, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 57.51, 74, 0.405000, 4255.74, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '室外定向板状天线 400-430MHz', 'E-ANTD 400', '频率范围：400-430MHz 增益：2.5dBi 防护等级：IP65 辐射方向：定向 最大承载功率：50W 接头类型：N-Femade 特性：室外', '和源通信', '套', 'EAN2OFD2TE2', 354.00, 143.37, 28, 0.405000, 4014.36, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '室外全向玻璃钢天线 400-430MHz', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 'EANLOMO5HR1', 458.00, 185.49, 2, 0.405000, 370.98, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 5 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.00, 539.87, 40, 0.405000, 21594.80, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 6 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 4799.66, 27, 0.405000, 129590.82, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 7 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '系统合路器 300-400MHz', 'E-FHP2000-2', '频率范围：351-366/410-424MHz 单端口承载功率：50W 插入损耗：≤1.5dB 接入端口数量：2 安装方式：机柜式 尺寸：2U', '和源通信', '套', 'ECM1BB22CZ2', 7917.00, 3206.39, 18, 0.405000, 57715.02, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 8 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #20: 昆山高新区前进路南侧、江浦路西侧商住用房新建项目 (project_id=666) ==========
-- 明细数: 9, 提货总额: 69908.54, 结算总额: 65714.93

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-020', 666, 729, 21, 282, false, false, 'channel_follow', 'approved', 1, 69908.54, 0.370000, 65714.93, 0.347805, 5, NOW(), 16, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (9 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 1690.53, 1, 0.370000, 1690.53, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 858.40, 1, 0.370000, 858.40, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 1690.53, 1, 0.370000, 1690.53, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 1690.53, 1, 0.370000, 1690.53, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1388.61, 2, 0.370000, 2777.22, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 3654.12, 3, 0.370000, 10962.36, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 4384.87, 7, 0.370000, 30694.09, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 52.54, 186, 0.370000, 9772.44, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 52.54, 186, 0.370000, 9772.44, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-020', currval('pricing_orders_id_seq'), 666, 729, 282, 21, false, false, 65714.93, 0.347805, 'approved', 'pending', 5, NOW(), 16, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (9 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (9 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 1589.10, 1, 0.347800, 1589.10, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 806.90, 1, 0.347800, 806.90, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 1589.10, 1, 0.347800, 1589.10, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 1589.10, 1, 0.347800, 1589.10, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1305.29, 2, 0.347800, 2610.58, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 3434.87, 3, 0.347800, 10304.61, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 5 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 4121.78, 7, 0.347800, 28852.46, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 6 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 49.39, 186, 0.347800, 9186.54, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 7 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 49.39, 186, 0.347800, 9186.54, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 8 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #21: 杭州博览会议中心二期 (project_id=5) ==========
-- 明细数: 16, 提货总额: 458947.02, 结算总额: 415237.78

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-021', 5, 453, 319, 496, false, false, 'sales_focus', 'approved', 1, 458947.02, 0.420000, 415237.78, 0.380000, 5, NOW(), 15, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (16 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '系统合路器', 'E-FHP2000-4 (400)', '频率范围:400-430MHz;单端口承载功率:15W;插入损耗:≤7.5dB;工作带宽:30M;接入端口数量:4;安装方式机:机柜式;尺寸:1U', '和源通信', '套', 'ECMLBD44KT1', 5500.00, 2310.00, 9, 0.420000, 20790.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '远端站接入许可', 'LS-NFX-BDA', '网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新', '和源通信', '套', 'HYWSRNB1', 1500.00, 630.00, 45, 0.420000, 28350.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '信道机接入许可', 'LS-NFX-RPT', '网讯平台信道机接入管理服务许可 -信道资源管理 -呼叫类型繁忙度分析', '和源通信', '套', 'HYWSPNB1', 2500.00, 1050.00, 6, 0.420000, 6300.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '系统工作台', 'ACC-CWT', '提供某一个项目上所有系统的工作管理，直观全面的反映系统的整体面貌和其中设备的布局，并可以跟踪每个设备及服务的进程。-告警处置模块-告警详情模块-维修情况和完成情况-设备位置地图模块，含一年的在线后台服', '和源通信', '个/年', 'HYWF0NA1', 8333.00, 3499.86, 1, 0.420000, 3499.86, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 1918.98, 3, 0.420000, 5756.94, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 974.40, 3, 0.420000, 2923.20, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1576.26, 2, 0.420000, 3152.52, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 1918.98, 3, 0.420000, 5756.94, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 4977.42, 45, 0.420000, 223983.90, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 4147.92, 13, 0.420000, 53922.96, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 59.64, 349, 0.420000, 20814.36, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 59.64, 145, 0.420000, 8647.80, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 59.64, 500, 0.420000, 29820.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '网讯网关服务 软件', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '套', 'HYWG0NB1', 12500.00, 5250.00, 1, 0.420000, 5250.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), 'DMR数字智能信道机 400MHz 25W', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '套', 'HYPSMXI40', 13580.00, 5703.60, 6, 0.420000, 34221.60, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 1918.98, 3, 0.420000, 5756.94, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-021', currval('pricing_orders_id_seq'), 5, 453, 496, 319, false, false, 415237.78, 0.380000, 'approved', 'pending', 5, NOW(), 15, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (16 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (16 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '系统合路器', 'E-FHP2000-4 (400)', '频率范围:400-430MHz;单端口承载功率:15W;插入损耗:≤7.5dB;工作带宽:30M;接入端口数量:4;安装方式机:机柜式;尺寸:1U', '和源通信', '套', 'ECMLBD44KT1', 5500.00, 2090.00, 9, 0.380000, 18810.00, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '远端站接入许可', 'LS-NFX-BDA', '网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新', '和源通信', '套', 'HYWSRNB1', 1500.00, 570.00, 45, 0.380000, 25650.00, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '信道机接入许可', 'LS-NFX-RPT', '网讯平台信道机接入管理服务许可 -信道资源管理 -呼叫类型繁忙度分析', '和源通信', '套', 'HYWSPNB1', 2500.00, 950.00, 6, 0.380000, 5700.00, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '系统工作台', 'ACC-CWT', '提供某一个项目上所有系统的工作管理，直观全面的反映系统的整体面貌和其中设备的布局，并可以跟踪每个设备及服务的进程。-告警处置模块-告警详情模块-维修情况和完成情况-设备位置地图模块，含一年的在线后台服', '和源通信', '个/年', 'HYWF0NA1', 8333.00, 3166.54, 1, 0.380000, 3166.54, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 1736.22, 3, 0.380000, 5208.66, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 881.60, 3, 0.380000, 2644.80, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 5 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1426.14, 2, 0.380000, 2852.28, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 6 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 1736.22, 3, 0.380000, 5208.66, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 7 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 4503.38, 45, 0.380000, 202652.10, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 8 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 3752.88, 13, 0.380000, 48787.44, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 9 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 53.96, 349, 0.380000, 18832.04, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 10 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 53.96, 145, 0.380000, 7824.20, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 11 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 53.96, 500, 0.380000, 26980.00, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 12 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '网讯网关服务 软件', 'NFX_GATW', '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理', '和源通信', '套', 'HYWG0NB1', 12500.00, 4750.00, 1, 0.380000, 4750.00, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 13 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), 'DMR数字智能信道机 400MHz 25W', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '套', 'HYPSMXI40', 13580.00, 5160.40, 6, 0.380000, 30962.40, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 14 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 1736.22, 3, 0.380000, 5208.66, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 15 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #22: 松江海螺水泥 (project_id=517) ==========
-- 明细数: 10, 提货总额: 79339.50, 结算总额: 71405.82

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-022', 517, 595, 497, 496, false, false, 'channel_follow', 'approved', 1, 79339.50, 0.450000, 71405.82, 0.405002, 5, NOW(), 14, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (10 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), 'DMR数字智能信道机 400MHz 25W', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '套', 'HYPSMXI40', 13580.00, 6111.00, 2, 0.450000, 12222.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 1044.00, 1, 0.450000, 1044.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1688.85, 1, 0.450000, 1688.85, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '常规射频直放站 420 2W', 'E-BDA400B LT', '频率范围：410~414/420~424 ,带宽：≤4M 输出：2W 功能：正面状态灯', '和源通信', '套', 'HYR1SN140', 8396.00, 3778.20, 1, 0.450000, 3778.20, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 63.90, 145, 0.450000, 9265.50, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 63.90, 6, 0.450000, 383.40, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 63.90, 129, 0.450000, 8243.10, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.00, 599.85, 50, 0.450000, 29992.50, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 5332.95, 2, 0.450000, 10665.90, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-022', currval('pricing_orders_id_seq'), 517, 595, 496, 497, false, false, 71405.82, 0.405002, 'approved', 'pending', 5, NOW(), 14, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (10 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (10 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), 'DMR数字智能信道机 400MHz 25W', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '套', 'HYPSMXI40', 13580.00, 5499.90, 2, 0.405000, 10999.80, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 939.60, 1, 0.405000, 939.60, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1519.97, 1, 0.405000, 1519.97, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '常规射频直放站 420 2W', 'E-BDA400B LT', '频率范围：410~414/420~424 ,带宽：≤4M 输出：2W 功能：正面状态灯', '和源通信', '套', 'HYR1SN140', 8396.00, 3400.38, 1, 0.405000, 3400.38, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 57.51, 145, 0.405000, 8338.95, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 5 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 57.51, 6, 0.405000, 345.06, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 6 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 57.51, 129, 0.405000, 7418.79, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 7 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.00, 539.87, 50, 0.405000, 26993.50, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 8 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 4799.66, 2, 0.405000, 9599.32, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 9 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #23: 松江站服务中心 (project_id=278) ==========
-- 明细数: 6, 提货总额: 13120.00, 结算总额: 13120.00

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-023', 278, 555, 246, NULL, false, false, 'sales_focus', 'approved', 1, 13120.00, 0.898753, 13120.00, 0.898753, 5, NOW(), 14, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (6 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '室外全向玻璃钢天线 350-380MHz', 'E-ANTG 350', '频率范围：350-380MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade 特性：室外', '和源通信', '套', 'EANPOMO5HR1', 625.00, 450.00, 2, 0.720000, 900.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 130.00, 3, 0.915500, 390.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-10 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:10dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN44Y', 142.00, 130.00, 21, 0.915500, 2730.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-15 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:15dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN54Y', 142.00, 130.00, 27, 0.915500, 3510.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-20 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:20dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN64Y', 142.00, 130.00, 4, 0.915500, 520.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 130.00, 39, 0.915500, 5070.00, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-023', currval('pricing_orders_id_seq'), 278, 555, NULL, 246, false, false, 13120.00, 0.898753, 'approved', 'pending', 5, NOW(), 14, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (6 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (6 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '室外全向玻璃钢天线 350-380MHz', 'E-ANTG 350', '频率范围：350-380MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade 特性：室外', '和源通信', '套', 'EANPOMO5HR1', 625.00, 450.00, 2, 0.720000, 900.00, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 130.00, 3, 0.915500, 390.00, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-10 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:10dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN44Y', 142.00, 130.00, 21, 0.915500, 2730.00, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-15 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:15dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN54Y', 142.00, 130.00, 27, 0.915500, 3510.00, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-20 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:20dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN64Y', 142.00, 130.00, 4, 0.915500, 520.00, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 130.00, 39, 0.915500, 5070.00, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 5 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #24: 海宁经开智创园 (project_id=36) ==========
-- 明细数: 5, 提货总额: 96122.25, 结算总额: 86510.05

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-024', 36, 455, 497, 496, false, false, 'channel_follow', 'approved', 1, 96122.25, 0.450000, 86510.05, 0.405000, 5, NOW(), 15, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (5 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 63.90, 22, 0.450000, 1405.80, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 63.90, 100, 0.450000, 6390.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 5332.95, 5, 0.450000, 26664.75, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 63.90, 103, 0.450000, 6581.70, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '防爆型高防护全向天线', 'MAEX 10', '频率范围: 350-470 MHz 增益: 0 dB 工作环境: 室内/室外 极化方向: 全向极化 功能: 防爆 IP防护: IP 65', '和源通信', '套', 'ACC3OOCXS', 7200.00, 3240.00, 17, 0.450000, 55080.00, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-024', currval('pricing_orders_id_seq'), 36, 455, 496, 497, false, false, 86510.05, 0.405000, 'approved', 'pending', 5, NOW(), 15, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (5 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (5 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 57.51, 22, 0.405000, 1265.22, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 57.51, 100, 0.405000, 5751.00, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 4799.66, 5, 0.405000, 23998.30, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 57.51, 103, 0.405000, 5923.53, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '防爆型高防护全向天线', 'MAEX 10', '频率范围: 350-470 MHz 增益: 0 dB 工作环境: 室内/室外 极化方向: 全向极化 功能: 防爆 IP防护: IP 65', '和源通信', '套', 'ACC3OOCXS', 7200.00, 2916.00, 17, 0.405000, 49572.00, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #25: 海宁经开智创园增补 (project_id=605) ==========
-- 明细数: 1, 提货总额: 25920.00, 结算总额: 23328.00

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-025', 605, 679, 497, 496, false, false, 'channel_follow', 'approved', 1, 25920.00, 0.450000, 23328.00, 0.405000, 5, NOW(), 15, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (1 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '防爆型高防护全向天线', 'MAEX 10', '频率范围: 350-470 MHz 增益: 0 dB 工作环境: 室内/室外 极化方向: 全向极化 功能: 防爆 IP防护: IP 65', '和源通信', '套', 'ACC3OOCXS', 7200.00, 3240.00, 8, 0.450000, 25920.00, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-025', currval('pricing_orders_id_seq'), 605, 679, 496, 497, false, false, 23328.00, 0.405000, 'approved', 'pending', 5, NOW(), 15, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (1 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (1 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '防爆型高防护全向天线', 'MAEX 10', '频率范围: 350-470 MHz 增益: 0 dB 工作环境: 室内/室外 极化方向: 全向极化 功能: 防爆 IP防护: IP 65', '和源通信', '套', 'ACC3OOCXS', 7200.00, 2916.00, 8, 0.405000, 23328.00, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #26: 海灏生物创新港 (project_id=26) ==========
-- 明细数: 7, 提货总额: 52100.10, 结算总额: 46890.10

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-026', 26, 559, 497, 496, false, false, 'channel_follow', 'approved', 1, 52100.10, 0.450000, 46890.10, 0.405000, 5, NOW(), 17, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (7 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '常规射频直放站 413 2W', 'E-BDA400B LT', '频率范围：403-405/413-415MHz 带宽：≤4M 输出：2W 功能：正面状态灯', '和源通信', '套', 'HYR1SN14A', 8396.00, 3778.20, 11, 0.450000, 41560.20, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 1044.00, 1, 0.450000, 1044.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：402-406/412-416MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ2', 3753.00, 1688.85, 1, 0.450000, 1688.85, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 63.90, 43, 0.450000, 2747.70, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 63.90, 14, 0.450000, 894.60, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 63.90, 33, 0.450000, 2108.70, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-026', currval('pricing_orders_id_seq'), 26, 559, 496, 497, false, false, 46890.10, 0.405000, 'approved', 'pending', 5, NOW(), 17, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (7 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (7 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '常规射频直放站 413 2W', 'E-BDA400B LT', '频率范围：403-405/413-415MHz 带宽：≤4M 输出：2W 功能：正面状态灯', '和源通信', '套', 'HYR1SN14A', 8396.00, 3400.38, 11, 0.405000, 37404.18, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 939.60, 1, 0.405000, 939.60, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：402-406/412-416MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ2', 3753.00, 1519.97, 1, 0.405000, 1519.97, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 57.51, 43, 0.405000, 2472.93, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 57.51, 14, 0.405000, 805.14, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 5 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 57.51, 33, 0.405000, 1897.83, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 6 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #27: 深圳市星河智善科技有限公司集采-东湾复建 (project_id=599) ==========
-- 明细数: 6, 提货总额: 91914.38, 结算总额: 85105.91

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-027', 599, 667, 497, 496, false, false, 'channel_follow', 'approved', 1, 91914.38, 0.405000, 85105.91, 0.375000, 5, NOW(), 17, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (6 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 57.51, 459, 0.405000, 26397.09, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '套', 'HYAIOCN4Y', 142.00, 57.51, 452, 0.405000, 25994.52, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 939.60, 4, 0.405000, 3758.40, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 1850.45, 4, 0.405000, 7401.80, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：402-406/412-416MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ2', 3753.00, 1519.97, 3, 0.405000, 4559.91, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '常规射频直放站 413 2W', 'E-BDA400B LT', '频率范围：403-405/413-415MHz 带宽：≤4M 输出：2W 功能：正面状态灯', '和源通信', '套', 'HYR1SN14A', 8396.00, 3400.38, 7, 0.405000, 23802.66, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-027', currval('pricing_orders_id_seq'), 599, 667, 496, 497, false, false, 85105.91, 0.375000, 'approved', 'pending', 5, NOW(), 17, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (6 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (6 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：351-470MHz;承载功率：100W;耦合规格：6dB;分路端口数量：2;防护等级：IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 53.25, 459, 0.375000, 24441.75, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围：351-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi 防护等级：IP65', '和源通信', '套', 'HYAIOCN4Y', 142.00, 53.25, 452, 0.375000, 24069.00, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 870.00, 4, 0.375000, 3480.00, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 1713.38, 4, 0.375000, 6853.52, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：402-406/412-416MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ2', 3753.00, 1407.38, 3, 0.375000, 4222.14, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '常规射频直放站 413 2W', 'E-BDA400B LT', '频率范围：403-405/413-415MHz 带宽：≤4M 输出：2W 功能：正面状态灯', '和源通信', '套', 'HYR1SN14A', 8396.00, 3148.50, 7, 0.375000, 22039.50, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 5 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #28: 美团科技中心 (project_id=518) ==========
-- 明细数: 15, 提货总额: 170570.37, 结算总额: 161350.35

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-028', 518, 596, 288, 282, false, false, 'channel_follow', 'approved', 1, 170570.37, 0.370000, 161350.35, 0.350000, 5, NOW(), 14, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (15 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '室外全向玻璃钢天线 400-430MHz', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 'EANLOMO5HR1', 458.00, 169.46, 1, 0.370000, 169.46, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '常规射频直放站 420 2W', 'E-BDA400B LT', '频率范围：410~414/420~424 ,带宽：≤4M 输出：2W 功能：正面状态灯', '和源通信', '套', 'HYR1SN140', 8396.00, 3106.52, 9, 0.370000, 27958.68, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 52.54, 105, 0.370000, 5516.70, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 52.54, 297, 0.370000, 15604.38, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 52.54, 73, 0.370000, 3835.42, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 1690.53, 1, 0.370000, 1690.53, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 858.40, 1, 0.370000, 858.40, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 1690.53, 1, 0.370000, 1690.53, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 3654.12, 4, 0.370000, 14616.48, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 4384.87, 15, 0.370000, 65773.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 52.54, 476, 0.370000, 25009.04, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '套', 'ECM1B042CZ1', 6642.00, 2457.54, 1, 0.370000, 2457.54, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU4xCZ1', 2493.00, 922.41, 1, 0.370000, 922.41, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1388.61, 2, 0.370000, 2777.22, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 1690.53, 1, 0.370000, 1690.53, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-028', currval('pricing_orders_id_seq'), 518, 596, 282, 288, false, false, 161350.35, 0.350000, 'approved', 'pending', 5, NOW(), 14, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (15 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (15 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '室外全向玻璃钢天线 400-430MHz', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 'EANLOMO5HR1', 458.00, 160.30, 1, 0.350000, 160.30, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '常规射频直放站 420 2W', 'E-BDA400B LT', '频率范围：410~414/420~424 ,带宽：≤4M 输出：2W 功能：正面状态灯', '和源通信', '套', 'HYR1SN140', 8396.00, 2938.60, 9, 0.350000, 26447.40, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 49.70, 105, 0.350000, 5218.50, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 49.70, 297, 0.350000, 14760.90, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 49.70, 73, 0.350000, 3628.10, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 1599.15, 1, 0.350000, 1599.15, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 5 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 812.00, 1, 0.350000, 812.00, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 6 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 1599.15, 1, 0.350000, 1599.15, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 7 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 3456.60, 4, 0.350000, 13826.40, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 8 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 4147.85, 15, 0.350000, 62217.75, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 9 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 49.70, 476, 0.350000, 23657.20, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 10 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '套', 'ECM1B042CZ1', 6642.00, 2324.70, 1, 0.350000, 2324.70, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 11 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU4xCZ1', 2493.00, 872.55, 1, 0.350000, 872.55, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 12 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1313.55, 2, 0.350000, 2627.10, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 13 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 1599.15, 1, 0.350000, 1599.15, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 14 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #29: 舜宇12英寸透明衬底晶圆AR眼镜微纳光学产品 (project_id=39) ==========
-- 明细数: 11, 提货总额: 21413.70, 结算总额: 19272.35

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-029', 39, 509, 497, 496, false, false, 'sales_focus', 'approved', 1, 21413.70, 0.450000, 19272.35, 0.405000, 5, NOW(), 14, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (11 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 63.90, 32, 0.450000, 2044.80, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '室外全向玻璃钢天线 400-430MHz', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 'EANLOMO5HR1', 458.00, 206.10, 2, 0.450000, 412.20, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-15 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:15dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN54Y', 142.00, 63.90, 1, 0.450000, 63.90, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-20 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:20dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN64Y', 142.00, 63.90, 2, 0.450000, 127.80, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '套', 'ECM1B042CZ1', 6642.00, 2988.90, 1, 0.450000, 2988.90, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU4xCZ1', 2493.00, 1121.85, 1, 0.450000, 1121.85, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1688.85, 1, 0.450000, 1688.85, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 4444.20, 1, 0.450000, 4444.20, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 63.90, 69, 0.450000, 4409.10, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-029', currval('pricing_orders_id_seq'), 39, 509, 496, 497, false, false, 19272.35, 0.405000, 'approved', 'pending', 5, NOW(), 14, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (11 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (11 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 57.51, 32, 0.405000, 1840.32, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '室外全向玻璃钢天线 400-430MHz', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 'EANLOMO5HR1', 458.00, 185.49, 2, 0.405000, 370.98, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-15 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:15dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN54Y', 142.00, 57.51, 1, 0.405000, 57.51, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-20 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:20dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN64Y', 142.00, 57.51, 2, 0.405000, 115.02, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '套', 'ECM1B042CZ1', 6642.00, 2690.01, 1, 0.405000, 2690.01, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU4xCZ1', 2493.00, 1009.67, 1, 0.405000, 1009.67, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 5 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1519.97, 1, 0.405000, 1519.97, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 6 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 7 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 8 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 3999.78, 1, 0.405000, 3999.78, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 9 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 57.51, 69, 0.405000, 3968.19, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 10 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #30: 荡口古镇太师府酒店建设项目智能化工程 (project_id=154) ==========
-- 明细数: 10, 提货总额: 85594.74, 结算总额: 80499.88

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-030', 154, 353, 21, 282, false, false, 'channel_follow', 'approved', 1, 85594.74, 0.420000, 80499.88, 0.395000, 5, NOW(), 16, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (10 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 1918.98, 1, 0.420000, 1918.98, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 4147.92, 3, 0.420000, 12443.76, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 4977.42, 9, 0.420000, 44796.78, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 59.64, 160, 0.420000, 9542.40, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 59.64, 160, 0.420000, 9542.40, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '室外全向玻璃钢天线 400-430MHz', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 'EANLOMO5HR1', 458.00, 192.36, 5, 0.420000, 961.80, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 1918.98, 1, 0.420000, 1918.98, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 974.40, 1, 0.420000, 974.40, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1576.26, 1, 0.420000, 1576.26, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 1918.98, 1, 0.420000, 1918.98, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-030', currval('pricing_orders_id_seq'), 154, 353, 282, 21, false, false, 80499.88, 0.395000, 'approved', 'pending', 5, NOW(), 16, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (10 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (10 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 1804.76, 1, 0.395000, 1804.76, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 3901.02, 3, 0.395000, 11703.06, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 4681.15, 9, 0.395000, 42130.35, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 56.09, 160, 0.395000, 8974.40, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 56.09, 160, 0.395000, 8974.40, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '室外全向玻璃钢天线 400-430MHz', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 'EANLOMO5HR1', 458.00, 180.91, 5, 0.395000, 904.55, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 5 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 1804.76, 1, 0.395000, 1804.76, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 6 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 916.40, 1, 0.395000, 916.40, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 7 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1482.44, 1, 0.395000, 1482.44, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 8 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 1804.76, 1, 0.395000, 1804.76, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 9 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #31: 重庆芯联微电子 (project_id=415) ==========
-- 明细数: 11, 提货总额: 139882.50, 结算总额: 125894.35

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-031', 415, 713, 507, 282, false, false, 'channel_follow', 'approved', 1, 139882.50, 0.450000, 125894.35, 0.405000, 5, NOW(), 13, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (11 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 63.90, 206, 0.450000, 13163.40, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 63.90, 50, 0.450000, 3195.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 63.90, 158, 0.450000, 10096.20, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '室外全向玻璃钢天线 400-430MHz', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 'EANLOMO5HR1', 458.00, 206.10, 2, 0.450000, 412.20, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 4444.20, 4, 0.450000, 17776.80, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 5332.95, 16, 0.450000, 85327.20, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '套', 'ECM1B042CZ1', 6642.00, 2988.90, 1, 0.450000, 2988.90, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU4xCZ1', 2493.00, 1121.85, 1, 0.450000, 1121.85, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1688.85, 1, 0.450000, 1688.85, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-031', currval('pricing_orders_id_seq'), 415, 713, 282, 507, false, false, 125894.35, 0.405000, 'approved', 'pending', 5, NOW(), 13, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (11 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (11 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 57.51, 206, 0.405000, 11847.06, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 57.51, 50, 0.405000, 2875.50, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 57.51, 158, 0.405000, 9086.58, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '室外全向玻璃钢天线 400-430MHz', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 'EANLOMO5HR1', 458.00, 185.49, 2, 0.405000, 370.98, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 3999.78, 4, 0.405000, 15999.12, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 4799.66, 16, 0.405000, 76794.56, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 5 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 6 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 7 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '套', 'ECM1B042CZ1', 6642.00, 2690.01, 1, 0.405000, 2690.01, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 8 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU4xCZ1', 2493.00, 1009.67, 1, 0.405000, 1009.67, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 9 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1519.97, 1, 0.405000, 1519.97, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 10 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #32: 静安假日酒店 (project_id=6) ==========
-- 明细数: 12, 提货总额: 85590.00, 结算总额: 77031.24

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-032', 6, 454, 497, 496, false, false, 'channel_follow', 'approved', 1, 85590.00, 0.450000, 77031.24, 0.405001, 5, NOW(), 15, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (12 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 63.90, 118, 0.450000, 7540.20, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 5332.95, 4, 0.450000, 21331.80, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 4444.20, 1, 0.450000, 4444.20, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 63.90, 83, 0.450000, 5303.70, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 63.90, 29, 0.450000, 1853.10, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), 'DMR数字智能信道机 400MHz 25W', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '套', 'HYPSMXI40', 13580.00, 6111.00, 2, 0.450000, 12222.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.00, 599.85, 40, 0.450000, 23994.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 1044.00, 1, 0.450000, 1044.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1688.85, 1, 0.450000, 1688.85, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-032', currval('pricing_orders_id_seq'), 6, 454, 496, 497, false, false, 77031.24, 0.405001, 'approved', 'pending', 5, NOW(), 15, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (12 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (12 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 57.51, 118, 0.405000, 6786.18, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.00, 4799.66, 4, 0.405000, 19198.64, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.00, 3999.78, 1, 0.405000, 3999.78, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 57.51, 83, 0.405000, 4773.33, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.00, 57.51, 29, 0.405000, 1667.79, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 5 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), 'DMR数字智能信道机 400MHz 25W', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '套', 'HYPSMXI40', 13580.00, 5499.90, 2, 0.405000, 10999.80, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 6 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.00, 539.87, 40, 0.405000, 21594.80, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 7 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 8 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 939.60, 1, 0.405000, 939.60, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 9 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1519.97, 1, 0.405000, 1519.97, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 10 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 11 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #33: 静安工人文化宫 (project_id=163) ==========
-- 明细数: 7, 提货总额: 36069.30, 结算总额: 32462.38

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-033', 163, 463, 497, 496, false, false, 'channel_follow', 'approved', 1, 36069.30, 0.450000, 32462.38, 0.405000, 5, NOW(), 15, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (7 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), 'DMR数字智能信道机 400MHz 25W', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '套', 'HYPSMXI40', 13580.00, 6111.00, 2, 0.450000, 12222.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 1044.00, 1, 0.450000, 1044.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1688.85, 1, 0.450000, 1688.85, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 63.90, 90, 0.450000, 5751.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 63.90, 90, 0.450000, 5751.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '常规射频直放站 420 2W', 'E-BDA400B LT', '频率范围：410~414/420~424 ,带宽：≤4M 输出：2W 功能：正面状态灯', '和源通信', '套', 'HYR1SN140', 8396.00, 3778.20, 2, 0.450000, 7556.40, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-033', currval('pricing_orders_id_seq'), 163, 463, 496, 497, false, false, 32462.38, 0.405000, 'approved', 'pending', 5, NOW(), 15, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (7 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (7 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), 'DMR数字智能信道机 400MHz 25W', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '套', 'HYPSMXI40', 13580.00, 5499.90, 2, 0.405000, 10999.80, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 939.60, 1, 0.405000, 939.60, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.00, 1519.97, 1, 0.405000, 1519.97, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.00, 57.51, 90, 0.405000, 5175.90, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.00, 57.51, 90, 0.405000, 5175.90, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 5 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '常规射频直放站 420 2W', 'E-BDA400B LT', '频率范围：410~414/420~424 ,带宽：≤4M 输出：2W 功能：正面状态灯', '和源通信', '套', 'HYR1SN140', 8396.00, 3400.38, 2, 0.405000, 6800.76, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 6 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #34: 马来西亚万国数据中心 (project_id=156) ==========
-- 明细数: 5, 提货总额: 42860.25, 结算总额: 38574.43

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-034', 156, 537, 288, 282, false, false, 'channel_follow', 'approved', 1, 42860.25, 0.450000, 38574.43, 0.405002, 5, NOW(), 14, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (5 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), '双工器 400MHz', 'E-SGQ400D', '频率范围：410-414/420-424MHz 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 隔离方式：带通 工作带宽：4M 安装方式：机柜式 尺寸：2U', '和源通信', '套', 'EDULB4H1CZ1', 7876.00, 3544.20, 1, 0.450000, 3544.20, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.00, 599.85, 40, 0.450000, 23994.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), 'DMR数字智能信道机 400MHz 25W', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '套', 'HYPSMXI40', 13580.00, 6111.00, 2, 0.450000, 12222.00, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 2056.05, 1, 0.450000, 2056.05, 'manual', 'CNY'),
  (currval('pricing_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 1044.00, 1, 0.450000, 1044.00, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-034', currval('pricing_orders_id_seq'), 156, 537, 282, 288, false, false, 38574.43, 0.405002, 'approved', 'pending', 5, NOW(), 14, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (5 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (5 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '双工器 400MHz', 'E-SGQ400D', '频率范围：410-414/420-424MHz 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 隔离方式：带通 工作带宽：4M 安装方式：机柜式 尺寸：2U', '和源通信', '套', 'EDULB4H1CZ1', 7876.00, 3189.78, 1, 0.405000, 3189.78, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.00, 539.87, 40, 0.405000, 21594.80, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 1 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), 'DMR数字智能信道机 400MHz 25W', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '套', 'HYPSMXI40', 13580.00, 5499.90, 2, 0.405000, 10999.80, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 2 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.00, 1850.45, 1, 0.405000, 1850.45, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 3 LIMIT 1), 'draft', 'CNY'),
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.00, 939.60, 1, 0.405000, 939.60, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 4 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ========== 项目 #35: 龙舟计划二期--增补 (project_id=9) ==========
-- 明细数: 1, 提货总额: 26393.40, 结算总额: 23754.28

INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'PO202602-035', 9, 337, 11, 282, false, false, 'channel_follow', 'approved', 1, 26393.40, 0.450000, 23754.28, 0.405004, 5, NOW(), 16, NOW(), NOW(), 'CNY'
);

-- 批价单明细 (1 条)
INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency) VALUES
  (currval('pricing_orders_id_seq'), 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.00, 599.85, 44, 0.450000, 26393.40, 'manual', 'CNY');

INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency) VALUES (
  'SO202602-035', currval('pricing_orders_id_seq'), 9, 337, 282, 11, false, false, 23754.28, 0.405004, 'approved', 'pending', 5, NOW(), 16, NOW(), NOW(), 'CNY'
);

-- 结算单明细 (1 条)
-- 使用子查询关联批价单明细ID
-- 结算单明细 (1 条)
INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_status, currency) VALUES
  (currval('pricing_orders_id_seq'), currval('settlement_orders_id_seq'), 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.00, 539.87, 44, 0.405000, 23754.28, (SELECT id FROM pricing_order_details WHERE pricing_order_id = currval('pricing_orders_id_seq') ORDER BY id OFFSET 0 LIMIT 1), 'draft', 'CNY');

INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval) VALUES (
  currval('pricing_orders_id_seq'), 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', NOW(), false
);

-- ============================================================
-- 更新项目阶段为 signed 并锁定
-- ============================================================
UPDATE projects SET
  current_stage = 'signed',
  is_locked = true,
  locked_reason = '项目已签约，自动锁定',
  locked_by = 5,
  locked_at = NOW()
WHERE id IN (679, 573, 529, 135, 102, 784, 666, 517, 415, 163, 99)
AND current_stage IN ('quoted', 'awarded');

-- ============================================================
-- 更新序列值
-- ============================================================
SELECT setval('pricing_orders_id_seq', (SELECT MAX(id) FROM pricing_orders));
SELECT setval('pricing_order_details_id_seq', (SELECT MAX(id) FROM pricing_order_details));
SELECT setval('settlement_orders_id_seq', (SELECT MAX(id) FROM settlement_orders));
SELECT setval('settlement_order_details_id_seq', (SELECT MAX(id) FROM settlement_order_details));
SELECT setval('pricing_order_approval_records_id_seq', (SELECT MAX(id) FROM pricing_order_approval_records));

COMMIT;

-- ============================================================
-- 验证查询
-- ============================================================
SELECT '批价单数量' as metric, COUNT(*) as value FROM pricing_orders WHERE order_number LIKE 'PO202602%';
SELECT '批价单明细数' as metric, COUNT(*) as value FROM pricing_order_details pd JOIN pricing_orders po ON pd.pricing_order_id = po.id WHERE po.order_number LIKE 'PO202602%';
SELECT '结算单数量' as metric, COUNT(*) as value FROM settlement_orders WHERE order_number LIKE 'SO202602%';
SELECT '结算单明细数' as metric, COUNT(*) as value FROM settlement_order_details sd JOIN settlement_orders so ON sd.settlement_order_id = so.id WHERE so.order_number LIKE 'SO202602%';
SELECT '审批记录数' as metric, COUNT(*) as value FROM pricing_order_approval_records WHERE comment LIKE '%批量导入补录%';
SELECT id, project_name, current_stage, is_locked FROM projects WHERE id IN (679, 573, 529, 135, 102, 784, 666, 517, 415, 163, 99);