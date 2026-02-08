#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批价单数据导入脚本
从 Excel 缺项明细 2.8 导入 7 个批价单 + 结算单到中国 NAS 数据库

使用方式:
  python3 /tmp/import_pricing_orders.py --dry-run   # 验证模式
  python3 /tmp/import_pricing_orders.py              # 正式导入
"""
import sys
import os
import argparse
from datetime import datetime

# 路径修正
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())
from app import create_app, db
from app.models.pricing_order import (
    PricingOrder, PricingOrderDetail,
    SettlementOrder, SettlementOrderDetail
)
from app.models.project import Project
from app.models.quotation import Quotation
from app.models.customer import Company


# ============================================================
# 数据定义
# ============================================================

# 项目映射: Excel项目名称 -> (project_id, quotation_id)
PROJECT_MAP = {
    '阿里达摩院增补改建项目': {'project_id': 601, 'quotation_id': 680},
    '合肥市瑶海区B、C地块商业智能化项目-增补': {'project_id': 675, 'quotation_id': 731},
    '康桥二期集成电路生产线厂房及配套设施建设项目(防爆天线）': {'project_id': 100, 'quotation_id': 428},
    '康桥二期集成电路生产线厂房及配套设施建设项目（硬件+软件）': {'project_id': 100, 'quotation_id': 428},
    '无锡奥林匹克体育产业中心一期项目（硬件产品）': {'project_id': 63, 'quotation_id': 344},
    '无锡奥林匹克体育产业中心一期项目（软件产品）': {'project_id': 63, 'quotation_id': 344},
}

# 公司映射: Excel名称 -> company_id
COMPANY_MAP = {
    '上海瑞康': 496,
    '上海淳泊': 282,
    '敦力（南京）科技': 21,
    '浙江航博智能': 319,
    '上海福玛': 288,
    '合肥四峰': 535,
}

# 7 个批价单定义
PRICING_ORDERS = [
    {
        'label': 'PO1: 阿里达摩院增补改建项目',
        'date': '2025年9月',
        'project_name': '阿里达摩院增补改建项目',
        'approval_flow_type': 'channel_follow',
        'category': '批价单',
        'settlement_party': '上海瑞康',  # distributor
        'pickup_party': '浙江航博智能',  # dealer
        'settlement_discount': 0.347,
        'pickup_discount': 0.37,
        'created_by': 5,
        'items': [
            {'mn': 'ECM1B082CZ1', 'name': '定向耦合合路器 400MHz', 'model': 'E-FH400-8',
             'spec': '频率范围：400-430MHz 单端口承载功率：50W;插入损耗：≤12dB;接入端口数量：8;安装方式：机柜式;尺寸：2U',
             'brand': '和源通信', 'unit': '套', 'qty': 1, 'market_price': 14120,
             'settlement_unit_price': 4899.64, 'pickup_unit_price': 5224.4},
            {'mn': 'EDE1BU8xCZ1', 'name': '分路器 350-430MHz', 'model': 'E-JF350/400-8',
             'spec': '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤10.5dB 接入端口数量：8 安装方式：机柜式 尺寸1U',
             'brand': '和源通信', 'unit': '套', 'qty': 1, 'market_price': 4962,
             'settlement_unit_price': 1721.81, 'pickup_unit_price': 1835.94},
            {'mn': 'HYR3SI340', 'name': '智能光纤远端直放站 400MHz 10W', 'model': 'RFT-BDA410 LT/M',
             'spec': '频率范围：410-414/420-424MHz 带宽：≤4M 输出：10W 功能： 正面状态灯/网讯平台',
             'brand': '和源通信', 'unit': '套', 'qty': 24, 'market_price': 21250,
             'settlement_unit_price': 7373.75, 'pickup_unit_price': 7862.5},
            {'mn': 'HYAIOCN4Y', 'name': '超薄室内全向吸顶天线', 'model': 'MA10',
             'spec': '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi',
             'brand': '和源通信', 'unit': '套', 'qty': 550, 'market_price': 142,
             'settlement_unit_price': 49.27, 'pickup_unit_price': 52.54},
            {'mn': 'HYCCN34Y', 'name': '定向耦合器', 'model': 'EVDC-6 LT',
             'spec': '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;',
             'brand': '和源通信', 'unit': '套', 'qty': 550, 'market_price': 142,
             'settlement_unit_price': 49.27, 'pickup_unit_price': 52.54},
            {'mn': 'HYGCT6P', 'name': '智能多联充电器', 'model': 'CMP2600',
             'spec': '六联智能充电站，具备电池充电管理和维护能力',
             'brand': '和源通信', 'unit': '套', 'qty': 12, 'market_price': 1860,
             'settlement_unit_price': 645.42, 'pickup_unit_price': 688.2},
        ]
    },
    {
        'label': 'PO2: 合肥瑶海区增补',
        'date': '2025年8月',
        'project_name': '合肥市瑶海区B、C地块商业智能化项目-增补',
        'approval_flow_type': 'channel_follow',
        'category': '批价单',
        'settlement_party': '上海淳泊',
        'pickup_party': '合肥四峰',
        'settlement_discount': 0.405,
        'pickup_discount': 0.45,
        'created_by': 5,
        'items': [
            {'mn': 'HYAIOCN4Y', 'name': '超薄室内全向吸顶天线', 'model': 'MA10',
             'spec': '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi',
             'brand': '和源通信', 'unit': '套', 'qty': 70, 'market_price': 142,
             'settlement_unit_price': 57.51, 'pickup_unit_price': 63.9},
        ]
    },
    {
        'label': 'PO3: 康桥二期（防爆天线）',
        'date': '2025年6月',
        'project_name': '康桥二期集成电路生产线厂房及配套设施建设项目(防爆天线）',
        'approval_flow_type': 'sales_focus',
        'category': '批价单',
        'settlement_party': '上海瑞康',
        'pickup_party': '上海福玛',
        'settlement_discount': 0.387,
        'pickup_discount': 0.43,
        'created_by': 5,
        'items': [
            {'mn': 'ACC3OOCXS', 'name': '防爆型高防护全向天线', 'model': 'MAEX 10',
             'spec': '频率范围: 350-470 MHz 增益: 0 dB 工作环境: 室内/室外 极化方向: 全向极化 功能: 防爆 IP防护: IP 65',
             'brand': '和源通信', 'unit': '套', 'qty': 45, 'market_price': 7200,
             'settlement_unit_price': 2786.4, 'pickup_unit_price': 3096},
        ]
    },
    {
        'label': 'PO4: 康桥二期（硬件+软件 - 软件部分 0.28/0.3）',
        'date': '2025年6月',
        'project_name': '康桥二期集成电路生产线厂房及配套设施建设项目（硬件+软件）',
        'approval_flow_type': 'sales_focus',
        'category': '批价单',
        'settlement_party': '上海淳泊',
        'pickup_party': '上海福玛',
        'settlement_discount': 0.28,
        'pickup_discount': 0.3,
        'created_by': 5,
        'items': [
            {'mn': 'HYWSTNB1', 'name': '对讲机终端接入许可', 'model': 'LS-NFX-RAD',
             'spec': '网讯平台终端对讲机接入管理服务许可-对讲机ID呼叫管理-对讲机上下线管理-呼叫组繁忙度分析',
             'brand': '和源通信', 'unit': '套', 'qty': 220, 'market_price': 180,
             'settlement_unit_price': 50.4, 'pickup_unit_price': 54},
            {'mn': 'EHYW521066', 'name': 'MOTOROLA 信道服务软件', 'model': 'GW-MOT-RPT',
             'spec': 'MOTOROLA信道机协议通信服务软件 功能 CP LCP 常规模式互通',
             'brand': '和源通信', 'unit': '套', 'qty': 1, 'market_price': 36667,
             'settlement_unit_price': 10266.76, 'pickup_unit_price': 11000.1},
            {'mn': 'HYWG0NB1', 'name': '网讯网关服务 软件', 'model': 'NFX_GATW',
             'spec': '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理',
             'brand': '和源通信', 'unit': '套', 'qty': 1, 'market_price': 12500,
             'settlement_unit_price': 3500, 'pickup_unit_price': 3750},
            {'mn': 'HYWSPNB1', 'name': '信道机接入许可', 'model': 'LS-NFX-RPT',
             'spec': '网讯平台信道机接入管理服务许可 -信道资源管理 -呼叫类型繁忙度分析',
             'brand': '和源通信', 'unit': '套', 'qty': 4, 'market_price': 2500,
             'settlement_unit_price': 700, 'pickup_unit_price': 750},
            {'mn': 'HYWSRNB1', 'name': '远端站接入许可', 'model': 'LS-NFX-BDA',
             'spec': '网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新',
             'brand': '和源通信', 'unit': '套', 'qty': 26, 'market_price': 1500,
             'settlement_unit_price': 420, 'pickup_unit_price': 450},
            {'mn': 'HYWP0NC1', 'name': '网讯平台服务 软件', 'model': 'NFX_MAST_OPETN',
             'spec': '-账户创建和访问管理-设备数据和系统数据的存储和恢复-产品库数据-系统拓扑和设备位置显示和管理-系统资源统计和告警分析推送-系统工作台主次账号一个-20个远端站授权，4个信道机授权，100个终端授权',
             'brand': '和源通信', 'unit': '套', 'qty': 1, 'market_price': 105000,
             'settlement_unit_price': 29400, 'pickup_unit_price': 31500},
        ]
    },
    {
        'label': 'PO5: 康桥二期（硬件+软件 - 硬件部分 0.348/0.37）',
        'date': '2025年6月',
        'project_name': '康桥二期集成电路生产线厂房及配套设施建设项目（硬件+软件）',
        'approval_flow_type': 'sales_focus',
        'category': '批价单',
        'settlement_party': '上海淳泊',
        'pickup_party': '上海福玛',
        'settlement_discount': 0.348,
        'pickup_discount': 0.37,
        'created_by': 5,
        'items': [
            {'mn': 'HYR3SI340', 'name': '智能光纤远端直放站 400MHz 10W', 'model': 'RFT-BDA410 LT/M',
             'spec': '频率范围：410-414/420-424MHz 带宽：≤4M 输出：10W 功能： 正面状态灯/网讯平台',
             'brand': '和源通信', 'unit': '套', 'qty': 46, 'market_price': 21250,
             'settlement_unit_price': 7395, 'pickup_unit_price': 7862.5},
            {'mn': 'HYGF20000', 'name': '馈电模组', 'model': 'FDPower400',
             'spec': '馈电功能模组,需搭配可扩展远端机;内置远端内向天馈提供电力;',
             'brand': '和源通信', 'unit': '套', 'qty': 46, 'market_price': 1583,
             'settlement_unit_price': 550.88, 'pickup_unit_price': 585.71},
            {'mn': 'ECM1B082CZ1', 'name': '定向耦合合路器 400MHz', 'model': 'E-FH400-8',
             'spec': '频率范围：400-430MHz 单端口承载功率：50W;插入损耗：≤12dB;接入端口数量：8;安装方式：机柜式;尺寸：2U',
             'brand': '和源通信', 'unit': '套', 'qty': 1, 'market_price': 14120,
             'settlement_unit_price': 4913.76, 'pickup_unit_price': 5224.4},
            {'mn': 'EDE1AU6xCZ1', 'name': '上行信号剥离器 350-430MHz', 'model': 'R-EVDC-BLST-U',
             'spec': '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U',
             'brand': '和源通信', 'unit': '套', 'qty': 4, 'market_price': 4569,
             'settlement_unit_price': 1590.01, 'pickup_unit_price': 1690.53},
            {'mn': 'EDE1AD6xCZ1', 'name': '下行信号剥离器 350-430MHz', 'model': 'R-EVDC-BLST-D',
             'spec': '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U',
             'brand': '和源通信', 'unit': '套', 'qty': 4, 'market_price': 4569,
             'settlement_unit_price': 1590.01, 'pickup_unit_price': 1690.53},
            {'mn': 'HYR2SI030', 'name': '智能光纤近端机 350-450MHz', 'model': 'RFS-400 LT/M',
             'spec': '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台',
             'brand': '和源通信', 'unit': '套', 'qty': 18, 'market_price': 9876,
             'settlement_unit_price': 3436.85, 'pickup_unit_price': 3654.12},
            {'mn': 'EANLOMO5HR1', 'name': '室外全向玻璃钢天线 400-430MHz', 'model': 'E-ANTG 400',
             'spec': '频率范围：400-430MHz 增益：5dBi 防护等级：IP65 辐射方向：全向 最大承载功率：50W 接头类型：N-Femade',
             'brand': '和源通信', 'unit': '套', 'qty': 18, 'market_price': 458,
             'settlement_unit_price': 159.38, 'pickup_unit_price': 169.46},
            {'mn': 'EDE1BU8xCZ1', 'name': '分路器 350-430MHz', 'model': 'E-JF350/400-8',
             'spec': '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤10.5dB 接入端口数量：8 安装方式：机柜式 尺寸1U',
             'brand': '和源通信', 'unit': '套', 'qty': 1, 'market_price': 4962,
             'settlement_unit_price': 1726.78, 'pickup_unit_price': 1835.94},
            {'mn': 'EDULB4H1CZ1', 'name': '双工器 400MHz', 'model': 'E-SGQ400D',
             'spec': '频率范围：410-414/420-424MHz 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 隔离方式：带通 工作带宽：4M 安装方式：机柜式 尺寸：2U',
             'brand': '和源通信', 'unit': '套', 'qty': 1, 'market_price': 7876,
             'settlement_unit_price': 2740.85, 'pickup_unit_price': 2914.12},
            {'mn': 'HYAIOCL4Y', 'name': '智能室内全向吸顶天线', 'model': 'MA11',
             'spec': '频率范围：350-470MHz 承载功率：50W 性能：室内全向 天线增益：0dBi 信号电平检测',
             'brand': '和源通信', 'unit': '套', 'qty': 609, 'market_price': 291,
             'settlement_unit_price': 101.27, 'pickup_unit_price': 107.67},
            {'mn': 'HYCCF34Y', 'name': '馈电定向耦合器', 'model': 'MADC-6',
             'spec': '频率范围：350-470MHz 承载功率：50W 耦合规格：6dB 分路端口数量：2 防护等级：IP65 应用：馈电',
             'brand': '和源通信', 'unit': '套', 'qty': 379, 'market_price': 344,
             'settlement_unit_price': 119.71, 'pickup_unit_price': 127.28},
            {'mn': 'HYCDF24Y', 'name': '馈电功率分配器', 'model': 'MAPD-2',
             'spec': '频率范围：350-470MHz 承载功率：50W 分路端口数量：2 防护等级：IP65 应用：馈电',
             'brand': '和源通信', 'unit': '套', 'qty': 265, 'market_price': 291,
             'settlement_unit_price': 101.27, 'pickup_unit_price': 107.67},
        ]
    },
    {
        'label': 'PO6: 无锡奥林匹克（硬件产品）',
        'date': '2025年3月',
        'project_name': '无锡奥林匹克体育产业中心一期项目（硬件产品）',
        'approval_flow_type': 'sales_focus',
        'category': '批价单',
        'settlement_party': '上海淳泊',
        'pickup_party': '敦力（南京）科技',
        'settlement_discount': 0.405,
        'pickup_discount': 0.45,
        'created_by': 5,
        'items': [
            {'mn': 'HYCCN34Y', 'name': '定向耦合器', 'model': 'EVDC-6 LT',
             'spec': '频率范围：88-430MHz;承载功率:100W;耦合规格:6dB;分路端口数量:2;防护等级:IP53;',
             'brand': '和源通信', 'unit': '套', 'qty': 86, 'market_price': 142,
             'settlement_unit_price': 57.51, 'pickup_unit_price': 63.9},
            {'mn': 'HYCDN24Y', 'name': '功率分配器', 'model': 'EVPD-2 LT',
             'spec': '频率范围:88-430MHz;承载功率:100W;分路端口数量:2;防护等级:IP53;',
             'brand': '和源通信', 'unit': '套', 'qty': 7, 'market_price': 142,
             'settlement_unit_price': 57.51, 'pickup_unit_price': 63.9},
            {'mn': 'EDE1AU6xCZ1', 'name': '上行信号剥离器 350-430MHz', 'model': 'R-EVDC-BLST-U',
             'spec': '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U',
             'brand': '和源通信', 'unit': '套', 'qty': 1, 'market_price': 4569,
             'settlement_unit_price': 1850.45, 'pickup_unit_price': 2056.05},
            {'mn': 'EDE1AD6xCZ1', 'name': '下行信号剥离器 350-430MHz', 'model': 'R-EVDC-BLST-D',
             'spec': '频率范围：350-430MHz 单端口承载功率：50W 插入损耗：≤0.5dB 接入端口数量：6 安装方式机：机柜式 尺寸：1U',
             'brand': '和源通信', 'unit': '套', 'qty': 1, 'market_price': 4569,
             'settlement_unit_price': 1850.45, 'pickup_unit_price': 2056.05},
            {'mn': 'EAN2OFD2TE2', 'name': '室外定向板状天线 400-430MHz', 'model': 'E-ANTD 400',
             'spec': '频率范围：400-430MHz 增益：2.5dBi 防护等级：IP65 辐射方向：定向 最大承载功率：50W 接头类型：N-Femade 特性：室外',
             'brand': '和源通信', 'unit': '套', 'qty': 4, 'market_price': 354,
             'settlement_unit_price': 143.37, 'pickup_unit_price': 159.3},
            {'mn': 'HYR2SI030', 'name': '智能光纤近端机 350-450MHz', 'model': 'RFS-400 LT/M',
             'spec': '频率范围：350~450MHz 带宽：≤15M 远端携带：4 功能： 网讯平台',
             'brand': '和源通信', 'unit': '套', 'qty': 2, 'market_price': 9876,
             'settlement_unit_price': 3999.78, 'pickup_unit_price': 4444.2},
            {'mn': 'HYR3SI140', 'name': '智能光纤远端直放站 400MHz 2W', 'model': 'RFT-BDA400B LT/M',
             'spec': '频率范围：410-414/420-424MHz 带宽：≤4M 输出：2W 功能： 网讯平台',
             'brand': '和源通信', 'unit': '套', 'qty': 8, 'market_price': 11851,
             'settlement_unit_price': 4799.66, 'pickup_unit_price': 5332.95},
            {'mn': 'ECM1BB22CZ2', 'name': '系统合路器 300-400MHz', 'model': 'E-FHP2000-2',
             'spec': '频率范围：351-366/410-424MHz 单端口承载功率：50W 插入损耗：≤1.5dB 接入端口数量：2 安装方式：机柜式 尺寸：2U',
             'brand': '和源通信', 'unit': '套', 'qty': 5, 'market_price': 7917,
             'settlement_unit_price': 3206.39, 'pickup_unit_price': 3562.65},
            {'mn': 'HYPSMXI40', 'name': 'DMR数字智能信道机 400MHz 25W', 'model': 'Mark1000 MAX',
             'spec': '频率范围：400-470MHz -功率 25W -网讯平台 -数模兼容',
             'brand': '和源通信', 'unit': '套', 'qty': 3, 'market_price': 13580,
             'settlement_unit_price': 5499.9, 'pickup_unit_price': 6111},
            {'mn': 'ECM1B042CZ1', 'name': '定向耦合合路器 400MHz', 'model': 'E-FH400-4',
             'spec': '频率范围：400-430MHz 单端口承载功率：50W 插入损耗：≤8.5dB 接入端口数量：4 安装方式：机柜式 尺寸2U',
             'brand': '和源通信', 'unit': '套', 'qty': 1, 'market_price': 6642,
             'settlement_unit_price': 2690.01, 'pickup_unit_price': 2988.9},
            {'mn': 'EDE1BU4xCZ1', 'name': '分路器 350-430MHz', 'model': 'E-JF350/400-4',
             'spec': '频率范围：350-430MHz 单端口承载功率：1W 插入损耗：≤7.5dB 接入端口数量：4 安装方式：机柜式 尺寸1U',
             'brand': '和源通信', 'unit': '套', 'qty': 1, 'market_price': 2493,
             'settlement_unit_price': 1009.67, 'pickup_unit_price': 1121.85},
            {'mn': 'HYAIOCN4Y', 'name': '超薄室内全向吸顶天线', 'model': 'MA10',
             'spec': '频率范围:88-430MHz 承载功率：100W 性能：室内全向 天线增益：0dBi',
             'brand': '和源通信', 'unit': '套', 'qty': 98, 'market_price': 142,
             'settlement_unit_price': 57.51, 'pickup_unit_price': 63.9},
            {'mn': 'HYTD4MA', 'name': 'DMR常规对讲机', 'model': 'PNR2000',
             'spec': '频率范围：400~470MHz，锂电池 3800mAh',
             'brand': '和源通信', 'unit': '套', 'qty': 20, 'market_price': 1333,
             'settlement_unit_price': 539.87, 'pickup_unit_price': 599.85},
            {'mn': 'EDULN4N1CZ1', 'name': '窄带双工器 400MHz', 'model': 'E-SGQ400N',
             'spec': '频率范围：410-414/420-424MHz 隔离方式：带阻 工作带宽：1.5M 单端口承载功率：50W 插入损耗：≤2.0dB 收发频率间隔：10M 安装方式：机柜式',
             'brand': '和源通信', 'unit': '套', 'qty': 1, 'market_price': 3753,
             'settlement_unit_price': 1519.97, 'pickup_unit_price': 1688.85},
        ]
    },
    {
        'label': 'PO7: 无锡奥林匹克（软件产品）- 厂家提货',
        'date': '2025年3月',
        'project_name': '无锡奥林匹克体育产业中心一期项目（软件产品）',
        'approval_flow_type': 'sales_focus',
        'category': '渠道直签',  # 厂家提货
        'settlement_party': '敦力（南京）科技',
        'pickup_party': '敦力（南京）科技',
        'settlement_discount': 0.19,
        'pickup_discount': 0.19,
        'created_by': 5,
        'items': [
            {'mn': 'HYWSPNB1', 'name': '信道机接入许可', 'model': 'LS-NFX-RPT',
             'spec': '网讯平台信道机接入管理服务许可 -信道资源管理 -呼叫类型繁忙度分析',
             'brand': '和源通信', 'unit': '套', 'qty': 3, 'market_price': 2500,
             'settlement_unit_price': 475, 'pickup_unit_price': 475},
            {'mn': 'HYWSRNB1', 'name': '远端站接入许可', 'model': 'LS-NFX-BDA',
             'spec': '网讯云端终端直放站接入管理服务许可-远端站告警-远端区域状态更新',
             'brand': '和源通信', 'unit': '套', 'qty': 35, 'market_price': 1500,
             'settlement_unit_price': 285, 'pickup_unit_price': 285},
            {'mn': 'HYWSTNB1', 'name': '对讲机终端接入许可', 'model': 'LS-NFX-RAD',
             'spec': '网讯平台终端对讲机接入管理服务许可-对讲机ID呼叫管理-对讲机上下线管理-呼叫组繁忙度分析',
             'brand': '和源通信', 'unit': '套', 'qty': 60, 'market_price': 180,
             'settlement_unit_price': 34.2, 'pickup_unit_price': 34.2},
            {'mn': 'HYWG0NB1', 'name': '网讯网关服务 软件', 'model': 'NFX_GATW',
             'spec': '用于本地系统设备管理和服务器的同步 -本地系统建立和配置 -设备驱动管理 -设备参数设置 -云同步 -设备报警管理',
             'brand': '和源通信', 'unit': '套', 'qty': 1, 'market_price': 12500,
             'settlement_unit_price': 2375, 'pickup_unit_price': 2375},
            {'mn': 'HYWF0NA1', 'name': '系统工作台', 'model': 'ACC-CWT',
             'spec': '提供某一个项目上所有系统的工作管理，直观全面的反映系统的整体面貌和其中设备的布局，并可以跟踪每个设备及服务的进程。-告警处置模块-告警详情模块-维修情况和完成情况-设备位置地图模块，含一年的在线后台服',
             'brand': '和源通信', 'unit': '个/年', 'qty': 1, 'market_price': 8333,
             'settlement_unit_price': 1583.27, 'pickup_unit_price': 1583.27},
        ]
    },
]

# 日期 -> (created_at, PO编号起始, SO编号起始)
DATE_MAP = {
    '2025年3月':  {'created_at': datetime(2025, 3, 15), 'po_start': 1, 'so_start': 1, 'prefix': '202503'},
    '2025年6月':  {'created_at': datetime(2025, 6, 15), 'po_start': 10, 'so_start': 10, 'prefix': '202506'},
    '2025年8月':  {'created_at': datetime(2025, 8, 15), 'po_start': 14, 'so_start': 14, 'prefix': '202508'},
    '2025年9月':  {'created_at': datetime(2025, 9, 15), 'po_start': 9, 'so_start': 9, 'prefix': '202509'},
}

# 跟踪每月已分配的编号
po_counter = {}
so_counter = {}


def get_next_po_number(date_str):
    """获取下一个批价单号"""
    info = DATE_MAP[date_str]
    prefix = info['prefix']
    if prefix not in po_counter:
        po_counter[prefix] = info['po_start']
    num = po_counter[prefix]
    po_counter[prefix] += 1
    return f"PO{prefix}-{num:03d}"


def get_next_so_number(date_str):
    """获取下一个结算单号"""
    info = DATE_MAP[date_str]
    prefix = info['prefix']
    if prefix not in so_counter:
        so_counter[prefix] = info['so_start']
    num = so_counter[prefix]
    so_counter[prefix] += 1
    return f"SO{prefix}-{num:03d}"


def validate_data(dry_run=True):
    """验证所有关联数据是否存在"""
    errors = []

    # 验证项目
    for name, info in PROJECT_MAP.items():
        proj = Project.query.get(info['project_id'])
        if not proj:
            errors.append(f"项目不存在: id={info['project_id']} ({name})")
        else:
            print(f"  ✓ 项目 {info['project_id']}: {proj.project_name}")

        quot = Quotation.query.get(info['quotation_id'])
        if not quot:
            errors.append(f"报价单不存在: id={info['quotation_id']}")
        else:
            print(f"  ✓ 报价单 {info['quotation_id']}: {quot.quotation_number}")

    # 验证公司
    for name, cid in COMPANY_MAP.items():
        comp = Company.query.get(cid)
        if not comp:
            errors.append(f"公司不存在: id={cid} ({name})")
        else:
            print(f"  ✓ 公司 {cid}: {comp.company_name}")

    # 计算每个月需要几个编号
    month_po_count = {}
    for po_def in PRICING_ORDERS:
        d = po_def['date']
        month_po_count[d] = month_po_count.get(d, 0) + 1

    # 验证现有编号不冲突
    for date_str, count in month_po_count.items():
        info = DATE_MAP[date_str]
        prefix = info['prefix']
        for i in range(info['po_start'], info['po_start'] + count):
            num = f"PO{prefix}-{i:03d}"
            existing = PricingOrder.query.filter_by(order_number=num).first()
            if existing:
                errors.append(f"批价单号已存在: {num} (id={existing.id})")

            num = f"SO{prefix}-{i:03d}"
            existing = SettlementOrder.query.filter_by(order_number=num).first()
            if existing:
                errors.append(f"结算单号已存在: {num} (id={existing.id})")

    return errors


def create_pricing_orders(dry_run=True):
    """创建所有批价单和结算单"""
    results = []

    for po_def in PRICING_ORDERS:
        date_str = po_def['date']
        created_at = DATE_MAP[date_str]['created_at']
        proj_info = PROJECT_MAP[po_def['project_name']]
        is_factory_pickup = po_def['category'] == '渠道直签'

        # 确定 dealer_id 和 distributor_id
        if is_factory_pickup:
            dealer_id = COMPANY_MAP[po_def['pickup_party']]
            distributor_id = None
        else:
            dealer_id = COMPANY_MAP[po_def['pickup_party']]
            distributor_id = COMPANY_MAP[po_def['settlement_party']]

        po_number = get_next_po_number(date_str)
        so_number = get_next_so_number(date_str)

        print(f"\n{'='*60}")
        print(f"  {po_def['label']}")
        print(f"  PO: {po_number}  SO: {so_number}")
        print(f"  项目ID: {proj_info['project_id']}  报价单ID: {proj_info['quotation_id']}")
        print(f"  经销商(dealer): {dealer_id}  分销商(distributor): {distributor_id}")
        print(f"  厂家提货: {is_factory_pickup}")
        print(f"  提货折扣: {po_def['pickup_discount']}  结算折扣: {po_def['settlement_discount']}")
        print(f"  明细数: {len(po_def['items'])}")

        if dry_run:
            # 计算预期金额
            pricing_total = sum(item['pickup_unit_price'] * item['qty'] for item in po_def['items'])
            settlement_total = sum(item['settlement_unit_price'] * item['qty'] for item in po_def['items'])
            market_total = sum(item['market_price'] * item['qty'] for item in po_def['items'])
            print(f"  预计提货批价总额: {pricing_total:,.2f}")
            print(f"  预计结算批价总额: {settlement_total:,.2f}")
            print(f"  预计零售总额: {market_total:,.2f}")
            if market_total > 0:
                print(f"  计算提货折扣率: {pricing_total/market_total:.6f}")
                print(f"  计算结算折扣率: {settlement_total/market_total:.6f}")

            for i, item in enumerate(po_def['items'], 1):
                print(f"    [{i}] {item['name']} ({item['model']}) x{item['qty']} "
                      f"零售:{item['market_price']} 提货:{item['pickup_unit_price']} 结算:{item['settlement_unit_price']}")
            continue

        # === 正式创建 ===

        # 1. 创建 PricingOrder
        po = PricingOrder(
            order_number=po_number,
            project_id=proj_info['project_id'],
            quotation_id=proj_info['quotation_id'],
            dealer_id=dealer_id,
            distributor_id=distributor_id,
            is_direct_contract=False,
            is_factory_pickup=is_factory_pickup,
            approval_flow_type=po_def['approval_flow_type'],
            status='draft',
            created_by=po_def['created_by'],
            created_at=created_at,
            updated_at=created_at,
            currency='CNY',
        )
        db.session.add(po)
        db.session.flush()  # 获取 po.id

        # 2. 创建 PricingOrderDetail (提货)
        pricing_details = []
        for item in po_def['items']:
            pickup_total = round(item['pickup_unit_price'] * item['qty'], 2)
            pd = PricingOrderDetail(
                pricing_order_id=po.id,
                product_name=item['name'],
                product_model=item['model'],
                product_desc=item['spec'],
                brand=item['brand'],
                unit=item['unit'],
                product_mn=item['mn'],
                market_price=item['market_price'],
                discount_rate=po_def['pickup_discount'],
                unit_price=item['pickup_unit_price'],
                quantity=item['qty'],
                total_price=pickup_total,
                source_type='manual',
                currency='CNY',
            )
            db.session.add(pd)
            db.session.flush()
            pricing_details.append(pd)

        # 3. 计算批价单总金额
        po.calculate_pricing_totals()

        # 4. 创建 SettlementOrder
        so = SettlementOrder(
            order_number=so_number,
            pricing_order_id=po.id,
            project_id=proj_info['project_id'],
            quotation_id=proj_info['quotation_id'],
            distributor_id=distributor_id,
            dealer_id=dealer_id,
            is_direct_contract=False,
            is_factory_pickup=is_factory_pickup,
            total_amount=0,
            total_discount_rate=1.0,
            status='draft',
            settlement_status='pending',
            created_by=po_def['created_by'],
            created_at=created_at,
            updated_at=created_at,
            currency='CNY',
        )
        db.session.add(so)
        db.session.flush()

        # 5. 创建 SettlementOrderDetail
        for i, item in enumerate(po_def['items']):
            settlement_total = round(item['settlement_unit_price'] * item['qty'], 2)
            sd = SettlementOrderDetail(
                pricing_order_id=po.id,
                settlement_order_id=so.id,
                product_name=item['name'],
                product_model=item['model'],
                product_desc=item['spec'],
                brand=item['brand'],
                unit=item['unit'],
                product_mn=item['mn'],
                market_price=item['market_price'],
                discount_rate=po_def['settlement_discount'],
                unit_price=item['settlement_unit_price'],
                quantity=item['qty'],
                total_price=settlement_total,
                pricing_detail_id=pricing_details[i].id,
                settlement_status='draft',
                currency='CNY',
            )
            db.session.add(sd)

        db.session.flush()

        # 6. 计算结算单总金额
        so.calculate_totals()

        # 7. 同步结算总金额到批价单
        po.settlement_total_amount = so.total_amount
        po.settlement_total_discount_rate = so.total_discount_rate

        results.append({
            'po_id': po.id,
            'po_number': po_number,
            'so_id': so.id,
            'so_number': so_number,
            'pricing_total': po.pricing_total_amount,
            'settlement_total': so.total_amount,
            'detail_count': len(po_def['items']),
        })

        print(f"  ✓ 创建成功: PO id={po.id}, SO id={so.id}")
        print(f"    提货总额: {po.pricing_total_amount:,.2f}  结算总额: {so.total_amount:,.2f}")

    return results


def main():
    parser = argparse.ArgumentParser(description='导入批价单数据')
    parser.add_argument('--dry-run', action='store_true', help='验证模式，不写入数据库')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        print("="*60)
        print(f"  批价单数据导入 {'(验证模式)' if args.dry_run else '(正式导入)'}")
        print("="*60)

        # 验证
        print("\n[Step 1] 验证关联数据...")
        errors = validate_data(args.dry_run)
        if errors:
            print(f"\n❌ 发现 {len(errors)} 个错误:")
            for e in errors:
                print(f"  - {e}")
            sys.exit(1)
        print("\n✓ 所有关联数据验证通过")

        # 创建
        print(f"\n[Step 2] {'预览' if args.dry_run else '创建'}批价单...")
        results = create_pricing_orders(dry_run=args.dry_run)

        if args.dry_run:
            print("\n" + "="*60)
            print("  验证完成 (dry-run模式，未写入数据库)")
            print("="*60)
        else:
            db.session.commit()
            print("\n" + "="*60)
            print(f"  ✓ 成功创建 {len(results)} 个批价单 + {len(results)} 个结算单")
            print("="*60)
            print("\n创建结果汇总:")
            total_details = 0
            for r in results:
                print(f"  {r['po_number']} (id={r['po_id']}) | {r['so_number']} (id={r['so_id']}) | "
                      f"明细:{r['detail_count']} | 提货:{r['pricing_total']:,.2f} | 结算:{r['settlement_total']:,.2f}")
                total_details += r['detail_count']
            print(f"\n  总计: {len(results)} 批价单, {len(results)} 结算单, {total_details} 条明细")


if __name__ == '__main__':
    main()
