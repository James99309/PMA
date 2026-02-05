-- =====================================================
-- 批价单数据导入脚本
-- 导入 5 个线下已审批的批价单到 NAS 数据库
-- 生成日期: 2026-02-06
-- =====================================================

BEGIN;

-- =====================================================
-- Step 1: 备份涉及的表数据
-- =====================================================
CREATE TABLE pricing_orders_backup_20260206 AS SELECT * FROM pricing_orders WHERE id IN (48,44,45,53);
CREATE TABLE pricing_order_details_backup_20260206 AS SELECT * FROM pricing_order_details WHERE pricing_order_id IN (48,44,45,53);
CREATE TABLE settlement_orders_backup_20260206 AS SELECT * FROM settlement_orders WHERE pricing_order_id IN (48,44,45,53);
CREATE TABLE settlement_order_details_backup_20260206 AS SELECT * FROM settlement_order_details WHERE pricing_order_id IN (48,44,45,53);
CREATE TABLE pricing_order_approval_records_backup_20260206 AS SELECT * FROM pricing_order_approval_records WHERE pricing_order_id IN (48,44,45,53);

-- =====================================================
-- Step 2: 删除旧批价单 (IDs: 48, 44, 45, 53)
-- =====================================================
DELETE FROM settlement_order_details WHERE pricing_order_id IN (48,44,45,53);
DELETE FROM settlement_orders WHERE pricing_order_id IN (48,44,45,53);
DELETE FROM pricing_order_details WHERE pricing_order_id IN (48,44,45,53);
DELETE FROM pricing_order_approval_records WHERE pricing_order_id IN (48,44,45,53);
DELETE FROM pricing_orders WHERE id IN (48,44,45,53);

-- =====================================================
-- Step 3-6: 插入新数据 (DO block)
-- =====================================================
DO $$
DECLARE
    v_po_id INTEGER;
    v_so_id INTEGER;
    v_pd_id INTEGER;
BEGIN

    -- ===== 批价单 1: 915项目弱电工程项目 =====
    -- PO: PO202508-010, 项目ID: 566, 报价单ID: 616
    -- 提货方: 497, 结算方: 496, 创建人: 15
    -- 明细行: 15, 提货总额: 287990.1, 结算总额: 259191.52

    INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency)
    VALUES ('PO202508-010', 566, 616, 497, 496, false, false, 'channel_follow', 'approved', 3, 287990.1, 0.45, 259191.52, 0.405001, 5, '2025-08-15 14:00:00+08'::timestamptz, 15, '2025-08-15 10:00:00+08'::timestamptz, NOW(), 'CNY')
    RETURNING id INTO v_po_id;

    INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency)
    VALUES ('SO202508-010', v_po_id, 566, 616, 496, 497, false, false, 259191.52, 0.405001, 'approved', 'pending', 5, '2025-08-15 14:00:00+08'::timestamptz, 15, '2025-08-15 10:00:00+08'::timestamptz, NOW(), 'CNY')
    RETURNING id INTO v_so_id;

    -- 明细 1: DMR数字智能信道机 400MHz 25 qty=3
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, 'DMR数字智能信道机 400MHz 25W', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '套', 'HYPSMXI40', 13580.0, 6111.0, 3, 0.45, 18333.0, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, 'DMR数字智能信道机 400MHz 25W', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '套', 'HYPSMXI40', 13580.0, 5499.9, 3, 0.405, 16499.7, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 2: 定向耦合合路器 400MHz qty=1
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '定向耦合合路器 400MHz', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '套', 'ECM1B042CZ1', 6642.0, 2988.9, 1, 0.45, 2988.9, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '定向耦合合路器 400MHz', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '套', 'ECM1B042CZ1', 6642.0, 2690.01, 1, 0.405, 2690.01, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 3: 分路器 350-430MHz qty=2
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '分路器 350-430MHz', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU4xCZ1', 2493.0, 1121.85, 2, 0.45, 2243.7, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '分路器 350-430MHz', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU4xCZ1', 2493.0, 1009.67, 2, 0.405, 2019.34, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 4: 窄带双工器 400MHz qty=1
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.0, 1688.85, 1, 0.45, 1688.85, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.0, 1519.97, 1, 0.405, 1519.97, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 5: 上行信号剥离器 350-430MHz qty=2
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.0, 2056.05, 2, 0.45, 4112.1, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.0, 1850.45, 2, 0.405, 3700.9, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 6: 下行信号剥离器 350-430MHz qty=2
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.0, 2056.05, 2, 0.45, 4112.1, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.0, 1850.45, 2, 0.405, 3700.9, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 7: 智能光纤近端机 350-450MHz qty=6
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.0, 4444.2, 6, 0.45, 26665.2, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.0, 3999.78, 6, 0.405, 23998.68, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 8: 智能光纤远端直放站 400MHz 2W qty=9
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.0, 5332.95, 9, 0.45, 47996.55, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.0, 4799.66, 9, 0.405, 43196.94, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 9: 超薄室内全向吸顶天线 qty=150
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.0, 63.9, 150, 0.45, 9585.0, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.0, 57.51, 150, 0.405, 8626.5, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 10: 定向耦合器 qty=120
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.0, 63.9, 120, 0.45, 7668.0, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.0, 57.51, 120, 0.405, 6901.2, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 11: DMR常规对讲机 qty=60
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.0, 599.85, 60, 0.45, 35991.0, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.0, 539.87, 60, 0.405, 32392.2, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 12: DMR数字智能信道机 350MHz 25 qty=1
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, 'DMR数字智能信道机 350MHz 25W', 'Mark1000 MAX', '频率范围：350~400MHz-功率 25W-网讯平台-数模兼容', '和源通信', '套', 'HYPSMXI30', 14583.0, 6562.35, 1, 0.45, 6562.35, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, 'DMR数字智能信道机 350MHz 25W', 'Mark1000 MAX', '频率范围：350~400MHz-功率 25W-网讯平台-数模兼容', '和源通信', '套', 'HYPSMXI30', 14583.0, 5906.12, 1, 0.405, 5906.12, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 13: 智能光纤远端直放站 350MHz 10W qty=9
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '智能光纤远端直放站 350MHz 10W', 'RFT-BDA310 LT/M', '频率范围：351-356/361-366MHz 带宽：≤5M 输出：10W 2U机箱 功能： 正面状态灯/网讯平台', '和源通信', '套', 'HYR3SI330', 21250.0, 9562.5, 9, 0.45, 86062.5, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '智能光纤远端直放站 350MHz 10W', 'RFT-BDA310 LT/M', '频率范围：351-356/361-366MHz 带宽：≤5M 输出：10W 2U机箱 功能： 正面状态灯/网讯平台', '和源通信', '套', 'HYR3SI330', 21250.0, 8606.25, 9, 0.405, 77456.25, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 14: 系统合路器 300-400MHz qty=9
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '系统合路器 300-400MHz', 'E-FHP2000-2', '频率范围：351-366/410-424MHz 单端口承载功率：50W 插入损耗：≤1.5dB 接入端口数量：2 安装方式：机柜式 尺寸：2U', '和源通信', '套', 'ECM1BB22CZ2', 7917.0, 3562.65, 9, 0.45, 32063.85, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '系统合路器 300-400MHz', 'E-FHP2000-2', '频率范围：351-366/410-424MHz 单端口承载功率：50W 插入损耗：≤1.5dB 接入端口数量：2 安装方式：机柜式 尺寸：2U', '和源通信', '套', 'ECM1BB22CZ2', 7917.0, 3206.39, 9, 0.405, 28857.51, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 15: 功率分配器 qty=30
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.0, 63.9, 30, 0.45, 1917.0, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.0, 57.51, 30, 0.405, 1725.3, v_pd_id, 496, 'pending', 'CNY');

    -- 审批记录
    INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval)
    VALUES (v_po_id, 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', '2025-08-15 14:00:00+08'::timestamptz, false);


    -- ===== 批价单 2: 学院路科技园东升园（I地块）项目 =====
    -- PO: PO202508-011, 项目ID: 531, 报价单ID: 603
    -- 提货方: 7, 结算方: 282, 创建人: 16
    -- 明细行: 4, 提货总额: 25177.5, 结算总额: 22659.76

    INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency)
    VALUES ('PO202508-011', 531, 603, 7, 282, false, false, 'channel_follow', 'approved', 3, 25177.5, 0.45, 22659.76, 0.405, 5, '2025-08-15 14:00:00+08'::timestamptz, 16, '2025-08-15 10:00:00+08'::timestamptz, NOW(), 'CNY')
    RETURNING id INTO v_po_id;

    INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency)
    VALUES ('SO202508-011', v_po_id, 531, 603, 282, 7, false, false, 22659.76, 0.405, 'approved', 'pending', 5, '2025-08-15 14:00:00+08'::timestamptz, 16, '2025-08-15 10:00:00+08'::timestamptz, NOW(), 'CNY')
    RETURNING id INTO v_so_id;

    -- 明细 1: 智能光纤近端机 350-450MHz qty=2
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.0, 4444.2, 2, 0.45, 8888.4, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.0, 3999.78, 2, 0.405, 7999.56, v_pd_id, 282, 'pending', 'CNY');

    -- 明细 2: 智能光纤远端直放站 400MHz 2W qty=2
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.0, 5332.95, 2, 0.45, 10665.9, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.0, 4799.66, 2, 0.405, 9599.32, v_pd_id, 282, 'pending', 'CNY');

    -- 明细 3: 定向耦合器 qty=43
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.0, 63.9, 43, 0.45, 2747.7, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.0, 57.51, 43, 0.405, 2472.93, v_pd_id, 282, 'pending', 'CNY');

    -- 明细 4: 超薄室内全向吸顶天线 qty=45
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.0, 63.9, 45, 0.45, 2875.5, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.0, 57.51, 45, 0.405, 2587.95, v_pd_id, 282, 'pending', 'CNY');

    -- 审批记录
    INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval)
    VALUES (v_po_id, 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', '2025-08-15 14:00:00+08'::timestamptz, false);


    -- ===== 批价单 3: 1366-E2酒店项目 =====
    -- PO: PO202508-012, 项目ID: 700, 报价单ID: 756
    -- 提货方: 499, 结算方: 282, 创建人: 14
    -- 明细行: 10, 提货总额: 49208.4, 结算总额: 44287.72

    INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency)
    VALUES ('PO202508-012', 700, 756, 499, 282, false, false, 'channel_follow', 'approved', 3, 49208.4, 0.45, 44287.72, 0.405001, 5, '2025-08-15 14:00:00+08'::timestamptz, 14, '2025-08-15 10:00:00+08'::timestamptz, NOW(), 'CNY')
    RETURNING id INTO v_po_id;

    INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency)
    VALUES ('SO202508-012', v_po_id, 700, 756, 282, 499, false, false, 44287.72, 0.405001, 'approved', 'pending', 5, '2025-08-15 14:00:00+08'::timestamptz, 14, '2025-08-15 10:00:00+08'::timestamptz, NOW(), 'CNY')
    RETURNING id INTO v_so_id;

    -- 明细 1: DMR数字智能信道机 400MHz 25 qty=2
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, 'DMR数字智能信道机 400MHz 25W', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '套', 'HYPSMXI40', 13580.0, 6111.0, 2, 0.45, 12222.0, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, 'DMR数字智能信道机 400MHz 25W', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '套', 'HYPSMXI40', 13580.0, 5499.9, 2, 0.405, 10999.8, v_pd_id, 282, 'pending', 'CNY');

    -- 明细 2: 定向耦合合路器 400MHz qty=1
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.0, 2056.05, 1, 0.45, 2056.05, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.0, 1850.45, 1, 0.405, 1850.45, v_pd_id, 282, 'pending', 'CNY');

    -- 明细 3: 分路器 350-430MHz qty=1
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.0, 1044.0, 1, 0.45, 1044.0, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.0, 939.6, 1, 0.405, 939.6, v_pd_id, 282, 'pending', 'CNY');

    -- 明细 4: 常规射频直放站 420 2W qty=2
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '常规射频直放站 420 2W', 'E-BDA400B LT', '频率范围：410~414/420~424 ,带宽：≤4M 输出：2W 功能：正面状态灯', '和源通信', '套', 'HYR1SN140', 8396.0, 3778.2, 2, 0.45, 7556.4, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '常规射频直放站 420 2W', 'E-BDA400B LT', '频率范围：410~414/420~424 ,带宽：≤4M 输出：2W 功能：正面状态灯', '和源通信', '套', 'HYR1SN140', 8396.0, 3400.38, 2, 0.405, 6800.76, v_pd_id, 282, 'pending', 'CNY');

    -- 明细 5: 超薄室内全向吸顶天线 qty=34
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.0, 63.9, 34, 0.45, 2172.6, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.0, 57.51, 34, 0.405, 1955.34, v_pd_id, 282, 'pending', 'CNY');

    -- 明细 6: 超薄室内全向吸顶天线 qty=18
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.0, 63.9, 18, 0.45, 1150.2, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.0, 57.51, 18, 0.405, 1035.18, v_pd_id, 282, 'pending', 'CNY');

    -- 明细 7: 功率分配器 qty=12
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.0, 63.9, 12, 0.45, 766.8, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.0, 57.51, 12, 0.405, 690.12, v_pd_id, 282, 'pending', 'CNY');

    -- 明细 8: 定向耦合器 qty=40
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.0, 63.9, 40, 0.45, 2556.0, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.0, 57.51, 40, 0.405, 2300.4, v_pd_id, 282, 'pending', 'CNY');

    -- 明细 9: DMR常规对讲机 qty=30
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.0, 599.85, 30, 0.45, 17995.5, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.0, 539.87, 30, 0.405, 16196.1, v_pd_id, 282, 'pending', 'CNY');

    -- 明细 10: 窄带双工器 400MHz qty=1
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.0, 1688.85, 1, 0.45, 1688.85, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.0, 1519.97, 1, 0.405, 1519.97, v_pd_id, 282, 'pending', 'CNY');

    -- 审批记录
    INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval)
    VALUES (v_po_id, 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', '2025-08-15 14:00:00+08'::timestamptz, false);


    -- ===== 批价单 4: 华兴新城项目8-01地块项目 =====
    -- PO: PO202508-013, 项目ID: 133, 报价单ID: 533
    -- 提货方: 183, 结算方: 496, 创建人: 14
    -- 明细行: 17, 提货总额: 192483.0, 结算总额: 173235.0

    INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency)
    VALUES ('PO202508-013', 133, 533, 183, 496, false, false, 'channel_follow', 'approved', 3, 192483.0, 0.45, 173235.0, 0.405001, 5, '2025-08-15 14:00:00+08'::timestamptz, 14, '2025-08-15 10:00:00+08'::timestamptz, NOW(), 'CNY')
    RETURNING id INTO v_po_id;

    INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency)
    VALUES ('SO202508-013', v_po_id, 133, 533, 496, 183, false, false, 173235.0, 0.405001, 'approved', 'pending', 5, '2025-08-15 14:00:00+08'::timestamptz, 14, '2025-08-15 10:00:00+08'::timestamptz, NOW(), 'CNY')
    RETURNING id INTO v_so_id;

    -- 明细 1: DMR数字智能信道机 400MHz 25 qty=2
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, 'DMR数字智能信道机 400MHz 25W', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '套', 'HYPSMXI40', 13580.0, 6111.0, 2, 0.45, 12222.0, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, 'DMR数字智能信道机 400MHz 25W', 'Mark1000 MAX', '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容', '和源通信', '套', 'HYPSMXI40', 13580.0, 5499.9, 2, 0.405, 10999.8, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 2: 定向耦合合路器 400MHz qty=1
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.0, 2056.05, 1, 0.45, 2056.05, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '定向耦合合路器 400MHz', 'E-FH400-2', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤5.5dB 接入端口数量：2 安装方式：机柜 尺寸2U', '和源通信', '套', 'ECM1B022CZ1', 4569.0, 1850.45, 1, 0.405, 1850.45, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 3: 分路器 350-430MHz qty=1
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.0, 1044.0, 1, 0.45, 1044.0, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '分路器 350-430MHz', 'E-JF350/400-2', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤3.8dB 接入端口数量：2 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU2xCZ1', 2320.0, 939.6, 1, 0.405, 939.6, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 4: 上行信号剥离器 350-430MHz qty=1
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.0, 2056.05, 1, 0.45, 2056.05, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.0, 1850.45, 1, 0.405, 1850.45, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 5: 下行信号剥离器 350-430MHz qty=1
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.0, 2056.05, 1, 0.45, 2056.05, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.0, 1850.45, 1, 0.405, 1850.45, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 6: 窄带双工器 400MHz qty=1
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.0, 1688.85, 1, 0.45, 1688.85, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.0, 1519.97, 1, 0.405, 1519.97, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 7: 智能光纤近端机 350-450MHz qty=4
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.0, 4444.2, 4, 0.45, 17776.8, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '智能光纤近端机 350-450MHz', 'RFS-400 LT/M', '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台', '和源通信', '套', 'HYR2SI030', 9876.0, 3999.78, 4, 0.405, 15999.12, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 8: 智能光纤远端直放站 400MHz 2W qty=10
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.0, 5332.95, 10, 0.45, 53329.5, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.0, 4799.66, 10, 0.405, 47996.6, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 9: 智能光纤远端直放站 400MHz 2W qty=6
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.0, 5332.95, 6, 0.45, 31997.7, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '智能光纤远端直放站 400MHz 2W', 'RFT-BDA400B LT/M', '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台', '和源通信', '套', 'HYR3SI140', 11851.0, 4799.66, 6, 0.405, 28797.96, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 10: DMR常规对讲机 qty=40
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.0, 599.85, 40, 0.45, 23994.0, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, 'DMR常规对讲机', 'PNR2000', '频率范围：400~470MHz，锂电池 3800mAh', '和源通信', '套', 'HYTD4MA', 1333.0, 539.87, 40, 0.405, 21594.8, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 11: 超薄室内全向吸顶天线 qty=333
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.0, 63.9, 333, 0.45, 21278.7, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.0, 57.51, 333, 0.405, 19150.83, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 12: 超薄室内全向吸顶天线 qty=15
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.0, 63.9, 15, 0.45, 958.5, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.0, 57.51, 15, 0.405, 862.65, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 13: 定向耦合器 qty=281
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.0, 63.9, 281, 0.45, 17955.9, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.0, 57.51, 281, 0.405, 16160.31, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 14: 定向耦合器 qty=12
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.0, 63.9, 12, 0.45, 766.8, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.0, 57.51, 12, 0.405, 690.12, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 15: 功率分配器 qty=32
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.0, 63.9, 32, 0.45, 2044.8, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.0, 57.51, 32, 0.405, 1840.32, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 16: 功率分配器 qty=10
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.0, 63.9, 10, 0.45, 639.0, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '功率分配器', 'EVPD-2 LT', '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCDN24Y', 142.0, 57.51, 10, 0.405, 575.1, v_pd_id, 496, 'pending', 'CNY');

    -- 明细 17: 室外全向玻璃钢天线 400-430MHz qty=3
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '室外全向玻璃钢天线 400-430MHz', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 'EANLOMO5HR1', 458.0, 206.1, 3, 0.45, 618.3, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '室外全向玻璃钢天线 400-430MHz', 'E-ANTG 400', '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade', '和源通信', '套', 'EANLOMO5HR1', 458.0, 185.49, 3, 0.405, 556.47, v_pd_id, 496, 'pending', 'CNY');

    -- 审批记录
    INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval)
    VALUES (v_po_id, 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', '2025-08-15 14:00:00+08'::timestamptz, false);


    -- ===== 批价单 5: 雄安国贸中心（D03-04-41/42/43/44号地块）项 =====
    -- PO: PO202509-008, 项目ID: 609, 报价单ID: 683
    -- 提货方: 288, 结算方: 282, 创建人: 16
    -- 明细行: 9, 提货总额: 16437.6, 结算总额: 14793.86

    INSERT INTO pricing_orders (order_number, project_id, quotation_id, dealer_id, distributor_id, is_direct_contract, is_factory_pickup, approval_flow_type, status, current_approval_step, pricing_total_amount, pricing_total_discount_rate, settlement_total_amount, settlement_total_discount_rate, approved_by, approved_at, created_by, created_at, updated_at, currency)
    VALUES ('PO202509-008', 609, 683, 288, 282, false, false, 'channel_follow', 'approved', 3, 16437.6, 0.45, 14793.86, 0.405001, 5, '2025-09-15 14:00:00+08'::timestamptz, 16, '2025-09-15 10:00:00+08'::timestamptz, NOW(), 'CNY')
    RETURNING id INTO v_po_id;

    INSERT INTO settlement_orders (order_number, pricing_order_id, project_id, quotation_id, distributor_id, dealer_id, is_direct_contract, is_factory_pickup, total_amount, total_discount_rate, status, settlement_status, approved_by, approved_at, created_by, created_at, updated_at, currency)
    VALUES ('SO202509-008', v_po_id, 609, 683, 282, 288, false, false, 14793.86, 0.405001, 'approved', 'pending', 5, '2025-09-15 14:00:00+08'::timestamptz, 16, '2025-09-15 10:00:00+08'::timestamptz, NOW(), 'CNY')
    RETURNING id INTO v_so_id;

    -- 明细 1: 定向耦合合路器 400MHz qty=1
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '定向耦合合路器 400MHz', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '套', 'ECM1B042CZ1', 6642.0, 2988.9, 1, 0.45, 2988.9, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '定向耦合合路器 400MHz', 'E-FH400-4', '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U', '和源通信', '套', 'ECM1B042CZ1', 6642.0, 2690.01, 1, 0.405, 2690.01, v_pd_id, 282, 'pending', 'CNY');

    -- 明细 2: 分路器 350-430MHz qty=1
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '分路器 350-430MHz', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU4xCZ1', 2493.0, 1121.85, 1, 0.45, 1121.85, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '分路器 350-430MHz', 'E-JF350/400-4', '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U', '和源通信', '套', 'EDE1BU4xCZ1', 2493.0, 1009.67, 1, 0.405, 1009.67, v_pd_id, 282, 'pending', 'CNY');

    -- 明细 3: 上行信号剥离器 350-430MHz qty=1
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.0, 2056.05, 1, 0.45, 2056.05, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '上行信号剥离器 350-430MHz', 'R-EVDC-BLST-U', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AU6xCZ1', 4569.0, 1850.45, 1, 0.405, 1850.45, v_pd_id, 282, 'pending', 'CNY');

    -- 明细 4: 下行信号剥离器 350-430MHz qty=1
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.0, 2056.05, 1, 0.45, 2056.05, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '下行信号剥离器 350-430MHz', 'R-EVDC-BLST-D', '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U', '和源通信', '套', 'EDE1AD6xCZ1', 4569.0, 1850.45, 1, 0.405, 1850.45, v_pd_id, 282, 'pending', 'CNY');

    -- 明细 5: 窄带双工器 400MHz qty=1
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.0, 1688.85, 1, 0.45, 1688.85, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '窄带双工器 400MHz', 'E-SGQ400N', '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式', '和源通信', '套', 'EDULN4N1CZ1', 3753.0, 1519.97, 1, 0.405, 1519.97, v_pd_id, 282, 'pending', 'CNY');

    -- 明细 6: 常规射频直放站 420 2W qty=1
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '常规射频直放站 420 2W', 'E-BDA400B LT', '频率范围：410~414/420~424 ,带宽：≤4M 输出：2W 功能：正面状态灯', '和源通信', '套', 'HYR1SN140', 8396.0, 3778.2, 1, 0.45, 3778.2, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '常规射频直放站 420 2W', 'E-BDA400B LT', '频率范围：410~414/420~424 ,带宽：≤4M 输出：2W 功能：正面状态灯', '和源通信', '套', 'HYR1SN140', 8396.0, 3400.38, 1, 0.405, 3400.38, v_pd_id, 282, 'pending', 'CNY');

    -- 明细 7: 定向耦合器 qty=12
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.0, 63.9, 12, 0.45, 766.8, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.0, 57.51, 12, 0.405, 690.12, v_pd_id, 282, 'pending', 'CNY');

    -- 明细 8: 定向耦合器 qty=12
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.0, 63.9, 12, 0.45, 766.8, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '定向耦合器', 'EVDC-6 LT', '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;', '和源通信', '套', 'HYCCN34Y', 142.0, 57.51, 12, 0.405, 690.12, v_pd_id, 282, 'pending', 'CNY');

    -- 明细 9: 超薄室内全向吸顶天线 qty=19
    INSERT INTO pricing_order_details (pricing_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, source_type, currency)
    VALUES (v_po_id, '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.0, 63.9, 19, 0.45, 1214.1, 'manual', 'CNY')
    RETURNING id INTO v_pd_id;

    INSERT INTO settlement_order_details (pricing_order_id, settlement_order_id, product_name, product_model, product_desc, brand, unit, product_mn, market_price, unit_price, quantity, discount_rate, total_price, pricing_detail_id, settlement_company_id, settlement_status, currency)
    VALUES (v_po_id, v_so_id, '超薄室内全向吸顶天线', 'MA10', '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi', '和源通信', '套', 'HYAIOCN4Y', 142.0, 57.51, 19, 0.405, 1092.69, v_pd_id, 282, 'pending', 'CNY');

    -- 审批记录
    INSERT INTO pricing_order_approval_records (pricing_order_id, step_order, step_name, approver_role, approver_id, action, comment, approved_at, is_fast_approval)
    VALUES (v_po_id, 1, '审批', 'approver', 5, 'approve', '线下已审批，系统批量导入补录 (2025年)', '2025-09-15 14:00:00+08'::timestamptz, false);

    RAISE NOTICE '导入完成！';
END $$;

-- =====================================================
-- Step 7: 验证
-- =====================================================
SELECT id, order_number, project_id, status, pricing_total_amount, settlement_total_amount FROM pricing_orders WHERE order_number = 'PO202508-010';
SELECT id, order_number, project_id, status, pricing_total_amount, settlement_total_amount FROM pricing_orders WHERE order_number = 'PO202508-011';
SELECT id, order_number, project_id, status, pricing_total_amount, settlement_total_amount FROM pricing_orders WHERE order_number = 'PO202508-012';
SELECT id, order_number, project_id, status, pricing_total_amount, settlement_total_amount FROM pricing_orders WHERE order_number = 'PO202508-013';
SELECT id, order_number, project_id, status, pricing_total_amount, settlement_total_amount FROM pricing_orders WHERE order_number = 'PO202509-008';

SELECT po.order_number as po_number, count(pod.id) as detail_count, po.pricing_total_amount, po.settlement_total_amount
FROM pricing_orders po
LEFT JOIN pricing_order_details pod ON pod.pricing_order_id = po.id
WHERE po.order_number IN ('PO202508-010','PO202508-011','PO202508-012','PO202508-013','PO202509-008')
GROUP BY po.order_number, po.pricing_total_amount, po.settlement_total_amount
ORDER BY po.order_number;

SELECT so.order_number as so_number, count(sod.id) as detail_count, so.total_amount
FROM settlement_orders so
LEFT JOIN settlement_order_details sod ON sod.settlement_order_id = so.id
WHERE so.order_number IN ('SO202508-010','SO202508-011','SO202508-012','SO202508-013','SO202509-008')
GROUP BY so.order_number, so.total_amount
ORDER BY so.order_number;

SELECT po.order_number, par.step_order, par.action, par.comment
FROM pricing_order_approval_records par
JOIN pricing_orders po ON po.id = par.pricing_order_id
WHERE po.order_number IN ('PO202508-010','PO202508-011','PO202508-012','PO202508-013','PO202509-008')
ORDER BY po.order_number;

-- 确认无误后执行 COMMIT，有问题执行 ROLLBACK
COMMIT;