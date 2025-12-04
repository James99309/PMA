#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将SP8D的specification_options复制到OVS
翻译中文值为英文
"""
import psycopg2

# SP8D数据库配置
SP8D_DB_CONFIG = {
    'host': 'aws-0-ap-southeast-1.pooler.supabase.com',
    'port': 6543,
    'database': 'postgres',
    'user': 'postgres.iqcyimnjtnmomvfuwjzw',
    'password': 'towsys-coGdoq-6gofdi',
    'sslmode': 'require'
}

# OVS数据库配置
OVS_DB_CONFIG = {
    'host': 'aws-0-ap-southeast-1.pooler.supabase.com',
    'port': 6543,
    'database': 'postgres',
    'user': 'postgres.pqzviljbpfoqvyfulakl',
    'password': 'nyjrIc-gubcu4-rukhoc',
    'sslmode': 'require'
}

# SP8D规格名(中文) -> OVS规格名(英文) 映射
SPEC_NAME_MAPPING = {
    '频率范围': 'Frequency Range',
    '输出功率': 'Output Power',
    '工作温度': 'Operating Temp',
    '防护等级': 'IP Rating',
    '尺寸': 'Dimensions',
    '重量': 'Weight',
    '增益': 'Gain',
    '工作湿度': 'Operating Humidity',
    '信道数量': 'Channel Count',
    '信道间隔': 'Channel Spacing',
    '显示方式': 'Display Type',
    '工作模式': 'Operating Mode',
    '阻抗': 'Impedance',
    '电源类型': 'Power Type',
    '增益调节步进': 'Gain Adjustment Step',
    '增益调节线性': 'Gain Adjustment Linearity',
    '射频接口类型': 'RF Interface Type',
    '监控接口类型': 'Monitoring Interface',
    '下行最大允许输入电平': 'Max DL Input Level',
    '上行最大允许输入电平': 'Max UL Input Level',
    '时延': 'Delay',
    '带内波动': 'In-band Ripple',
    '上下行隔离度': 'UL/DL Isolation',
    '安装方式': 'Mounting Type',
    '最大输出功率': 'Max Output Power',
    'ALC自动调节范围': 'ALC Auto Adjustment Range',
    '噪声系数': 'Noise Figure',
    '频率特性': 'Frequency Characteristics',
    '载波容量': 'Carrier Capacity',
    '光口数量': 'Optical Ports',
    '光输出功率': 'Optical Output Power',
    '光接收灵敏度': 'Optical Rx Sensitivity',
    '光波长规格': 'Optical Wavelength',
    '光口规格': 'Optical Port Spec',
    '光口类型': 'Optical Port Type',
    '输入输出驻波比': 'I/O VSWR',
    '防爆等级': 'Explosion-Proof Rating',
    '承载功率': 'Power Handling',
    '辐射方向': 'Radiation Pattern',
    '天线增益': 'Antenna Gain',
    '水平辐射角度': 'Horizontal Beamwidth',
    '垂直辐射角度': 'Vertical Beamwidth',
    '驻波比': 'VSWR',
    '延迟同步功能': 'Delay Synchronization',
    '互调衰减': 'IMD Suppression',
    '功能': 'Functions',
    '带外杂散': 'Out-of-band Spurious',
    '插入损耗': 'Insertion Loss',
    '分配损耗': 'Distribution Loss',
    '馈电功能': 'Power Feeding',
    '馈电电压': 'Feeding Voltage',
    '馈电电流': 'Feeding Current',
    '蓝牙发射功率': 'Bluetooth TX Power',
    '最大接入信道数': 'Max Access Channels',
    '单端口承载功率': 'Per-Port Power Handling',
    '端口隔离度': 'Port Isolation',
    '充电电流': 'Charging Current',
    '充电槽数量': 'Charging Slots',
    '耦合损耗': 'Coupling Loss',
    '输入端口数量': 'Input Ports',
    '收发隔离度': 'TX/RX Isolation',
    '带外抑制': 'Out-of-band Rejection',
    '双工类型': 'Duplex Type',
}

# 中文value值翻译
VALUE_TRANSLATIONS = {
    '机柜安装': 'Cabinet',
    '壁挂安装': 'Wall Mount',
    '壁挂': 'Wall Mount',
    '吊顶 / 壁挂': 'Ceiling/Wall',
    '室外支架': 'Outdoor Bracket',
    '室外壁挂': 'Outdoor Wall',
    '英标 220': 'UK 220V',
    '国标 220': 'CN 220V',
    '双色指示灯': 'Dual LED',
    '彩色触摸屏': 'Color Touch',
    '不可调': 'Fixed',
    '双工器可调': 'Adjustable',
    '垂直极化，全向': 'V-Pol Omni',
    '垂直极化，定向': 'V-Pol Direct',
    '馈电': 'Feeding',
    '无馈电': 'No Feeding',
    '无': 'None',
    '交织': 'Interleave',
    '馈电 / 蓝牙定位': 'Feed/BT Loc',
    '馈电 / 状态指示灯': 'Feed/Status',
    '具备': 'Yes',
    '不具备': 'No',
    '双向收发复用': 'Bidirectional',
    '带通型': 'Band-pass',
    '带阻型': 'Band-stop',
    'DMR / 模拟': 'DMR/Analog',
}


def translate_value(value):
    """翻译value值，如果有中文则翻译"""
    if value in VALUE_TRANSLATIONS:
        return VALUE_TRANSLATIONS[value]
    # 检查是否包含需要翻译的中文
    for cn, en in VALUE_TRANSLATIONS.items():
        if cn in value:
            value = value.replace(cn, en)
    return value


def main():
    print("=" * 60)
    print("复制SP8D specification_options到OVS")
    print("=" * 60)

    # 连接数据库
    sp8d_conn = psycopg2.connect(**SP8D_DB_CONFIG)
    ovs_conn = psycopg2.connect(**OVS_DB_CONFIG)
    ovs_conn.autocommit = True  # 使用自动提交，每条独立事务

    sp8d_cursor = sp8d_conn.cursor()
    ovs_cursor = ovs_conn.cursor()

    # 获取OVS规格字典的ID映射
    ovs_cursor.execute("SELECT id, name FROM specification_dictionary")
    ovs_specs = {name: id for id, name in ovs_cursor.fetchall()}
    print(f"\nOVS规格字典: {len(ovs_specs)} 条")

    # 获取SP8D规格字典的ID到名称映射
    sp8d_cursor.execute("SELECT id, name FROM specification_dictionary")
    sp8d_specs = {id: name for id, name in sp8d_cursor.fetchall()}
    print(f"SP8D规格字典: {len(sp8d_specs)} 条")

    # 获取SP8D的所有specification_options
    sp8d_cursor.execute("""
        SELECT so.id, so.spec_id, so.value, so.code, so.description,
               so.is_active, so.position, so.created_at
        FROM specification_options so
        ORDER BY so.spec_id, so.id
    """)
    sp8d_options = sp8d_cursor.fetchall()
    print(f"SP8D规格选项: {len(sp8d_options)} 条")

    # 复制到OVS
    success_count = 0
    skip_count = 0
    duplicate_count = 0
    error_count = 0

    print("\n开始复制...")
    for row in sp8d_options:
        sp8d_id, sp8d_spec_id, value, code, description, is_active, position, created_at = row

        # 获取SP8D规格名
        sp8d_spec_name = sp8d_specs.get(sp8d_spec_id)
        if not sp8d_spec_name:
            print(f"  跳过: 找不到SP8D规格ID {sp8d_spec_id}")
            skip_count += 1
            continue

        # 获取对应的OVS规格名
        ovs_spec_name = SPEC_NAME_MAPPING.get(sp8d_spec_name)
        if not ovs_spec_name:
            print(f"  跳过: 没有映射 '{sp8d_spec_name}'")
            skip_count += 1
            continue

        # 获取OVS规格ID
        ovs_spec_id = ovs_specs.get(ovs_spec_name)
        if not ovs_spec_id:
            print(f"  跳过: OVS中没有 '{ovs_spec_name}'")
            skip_count += 1
            continue

        # 翻译value值
        translated_value = translate_value(value)

        try:
            ovs_cursor.execute("""
                INSERT INTO specification_options
                (spec_id, value, code, description, is_active, position, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (ovs_spec_id, translated_value, code, description,
                  is_active if is_active is not None else True,
                  position, created_at))
            success_count += 1
        except psycopg2.errors.UniqueViolation:
            duplicate_count += 1
        except Exception as e:
            print(f"  错误: {ovs_spec_name} - {translated_value}: {e}")
            error_count += 1

    print("\n" + "=" * 60)
    print("复制结果:")
    print(f"  成功: {success_count}")
    print(f"  跳过: {skip_count}")
    print(f"  重复: {duplicate_count}")
    print(f"  错误: {error_count}")
    print("=" * 60)

    # 验证
    ovs_cursor.execute("SELECT COUNT(*) FROM specification_options")
    total = ovs_cursor.fetchone()[0]
    print(f"\nOVS specification_options 总数: {total}")

    # 关闭连接
    sp8d_cursor.close()
    ovs_cursor.close()
    sp8d_conn.close()
    ovs_conn.close()


if __name__ == '__main__':
    main()
