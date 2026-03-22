#!/usr/bin/env python3
"""在 CN NAS 模版下为 SG NAS 产品创建独立配置（锁定MN）"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from app import create_app, db
from app.models.spec_template import (
    SpecTemplate, SpecTemplateItem, ProductConfiguration, ProductConfigValue
)
from sqlalchemy import func

app = create_app()

# SG 产品数据（sg_id, model, product_mn, template_id）
sg_products = [
    (81, 'DFB400A', 'YPARW6GQ3', 1),
    (82, 'DFB400A', 'YPAM56GQ3', 1),
    (80, 'DFB400A', 'YPALP6GQ3', 1),
    (18, 'DRFS-400/M', 'SGR2DI040', 21),
    (73, 'DRFS-400/M', 'ODBCVYL3W5A6', 21),
    (71, 'DRFS-400/M', 'OSCDC4IN', 21),
    (79, 'DRFT-BDA410/M', 'SGR3DI340F', 22),
    (74, 'DRFT-BDA410/M', 'OEBPTM9VXZUD', 22),
    (72, 'DRFT-BDA410/M', 'RSCDXC4IN', 22),
    (19, 'DRFT-BDA410/M', 'SGR3DI340', 22),
    (5, 'E-FH400-8', 'SGCM1B082CZ1', 24),
    (29, 'EVDC-10 LT', 'SGCCN44Y', 3),
    (30, 'EVDC-15 LT', 'SGCCN54Y', 4),
    (31, 'EVDC-20 LT', 'SGCCN64Y', 5),
    (28, 'EVDC-6 LT', 'SGCCN34Y', 2),
    (27, 'EVPD-2 LT', 'SGCDN24Y', 6),
    (21, 'MA10', 'SGAIOCN4Y', 9),
    (14, 'RFS-400 LT/M', 'SGR2SI030', 11),
    (77, 'RFT-BDA400B LT/M', 'SGR3SI14SF', 10),
    (15, 'RFT-BDA400B LT/M', 'SGR3SI14S', 10),
    (16, 'RFT-BDA400B LT/M', 'SGR3SI140', 10),
    (17, 'RFT-BDA400B LT/M', 'SGR3SI340', 10),
]

# SG 产品规格（从文件读取）
sg_specs = {}  # {sg_id: {field_name: field_value}}
with open('/tmp/sg_specs.txt') as f:
    for line in f:
        parts = line.strip().split('|')
        if len(parts) >= 3:
            pid, fname, fval = int(parts[0]), parts[1], parts[2]
            sg_specs.setdefault(pid, {})[fname] = fval

with app.app_context():
    created = 0
    errors = []

    for sg_id, model, mn_code, template_id in sg_products:
        try:
            template = SpecTemplate.query.get(template_id)
            if not template:
                errors.append(f"Template {template_id} not found for {model}")
                continue

            # 从MN推断区域码
            region = mn_code[0] if mn_code else 'X'

            # 创建配置
            config = ProductConfiguration(
                template_id=template_id,
                config_code=f'SG-{sg_id}',
                region=region,
                region_name='新加坡',
                status='production',
                mn_code=mn_code,
                template_version=template.version
            )
            db.session.add(config)
            db.session.flush()

            # 匹配规格值
            specs = sg_specs.get(sg_id, {})
            matched = 0
            for item in template.items:
                spec_name = item.spec_dict.name if item.spec_dict else None
                if not spec_name:
                    continue

                val = specs.get(spec_name)
                if val:
                    cv = ProductConfigValue(
                        configuration_id=config.id,
                        template_item_id=item.id,
                        value=val
                    )
                    db.session.add(cv)
                    matched += 1
                elif item.general_value:
                    cv = ProductConfigValue(
                        configuration_id=config.id,
                        template_item_id=item.id,
                        value=item.general_value
                    )
                    db.session.add(cv)
                    matched += 1

            print(f"  ✅ SG#{sg_id} {model} MN={mn_code} → config {config.id} ({matched}/{len(template.items)} specs)")
            created += 1

        except Exception as e:
            errors.append(f"SG#{sg_id} {model}: {e}")
            print(f"  ❌ SG#{sg_id} {model}: {e}")

    if errors:
        print(f"\n⚠️ {len(errors)} 个错误，回滚")
        for e in errors:
            print(f"  {e}")
        db.session.rollback()
    else:
        db.session.commit()
        print(f"\n✅ 完成: 在 CN 模版下创建 {created} 个 SG 配置")
