#!/usr/bin/env python3
"""
审批模板版本化迁移脚本
添加 template_snapshot 和 template_version 字段到 approval_instance 表
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.approval import ApprovalInstance, ApprovalProcessTemplate, ApprovalStep
from datetime import datetime
import json
from sqlalchemy import text

def migrate_approval_template_versioning():
    """执行审批模板版本化迁移"""
    
    app = create_app()
    
    with app.app_context():
        print("开始审批模板版本化迁移...")
        
        # 1. 添加新字段（如果不存在）
        try:
            with db.engine.connect() as connection:
                # 检查字段是否已存在 (PostgreSQL语法)
                result = connection.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='approval_instance' AND column_name='template_snapshot'
                """))
                if not result.fetchone():
                    print("添加 template_snapshot 字段...")
                    connection.execute(text("ALTER TABLE approval_instance ADD COLUMN template_snapshot JSON"))
                    connection.commit()
                
                result = connection.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='approval_instance' AND column_name='template_version'
                """))
                if not result.fetchone():
                    print("添加 template_version 字段...")
                    connection.execute(text("ALTER TABLE approval_instance ADD COLUMN template_version VARCHAR(50)"))
                    connection.commit()
                
        except Exception as e:
            print(f"添加字段时出错: {e}")
            return False
        
        # 2. 为现有的审批实例创建快照
        print("为现有审批实例创建模板快照...")
        
        instances = ApprovalInstance.query.filter(
            ApprovalInstance.template_snapshot.is_(None)
        ).all()
        
        updated_count = 0
        
        for instance in instances:
            try:
                # 获取模板和步骤
                template = ApprovalProcessTemplate.query.get(instance.process_id)
                if not template:
                    print(f"警告: 实例 {instance.id} 的模板 {instance.process_id} 不存在")
                    continue
                
                steps = ApprovalStep.query.filter_by(
                    process_id=instance.process_id
                ).order_by(ApprovalStep.step_order.asc()).all()
                
                # 创建模板快照
                template_snapshot = {
                    'template_id': template.id,
                    'template_name': template.name,
                    'object_type': template.object_type,
                    'required_fields': template.required_fields or [],
                    'lock_object_on_start': getattr(template, 'lock_object_on_start', True),
                    'lock_reason': getattr(template, 'lock_reason', '审批流程进行中，暂时锁定编辑'),
                    'created_at': instance.started_at.isoformat() if instance.started_at else datetime.utcnow().isoformat(),
                    'steps': []
                }
                
                # 保存步骤快照
                for step in steps:
                    step_data = {
                        'id': step.id,
                        'step_order': step.step_order,
                        'step_name': step.step_name,
                        'approver_user_id': step.approver_user_id,
                        'approver_username': step.approver.username if step.approver else '',
                        'approver_real_name': step.approver.real_name if step.approver else '',
                        'send_email': step.send_email,
                        'action_type': step.action_type,
                        'action_params': getattr(step, 'action_params', None),
                        'editable_fields': step.editable_fields or [],
                        'cc_users': step.cc_users or [],
                        'cc_enabled': step.cc_enabled
                    }
                    template_snapshot['steps'].append(step_data)
                
                # 更新实例
                instance.template_snapshot = template_snapshot
                instance.template_version = f"migrated_{instance.started_at.strftime('%Y%m%d_%H%M%S')}" if instance.started_at else f"migrated_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                
                updated_count += 1
                
                if updated_count % 10 == 0:
                    print(f"已处理 {updated_count} 个实例...")
                    
            except Exception as e:
                print(f"处理实例 {instance.id} 时出错: {e}")
                continue
        
        # 提交更改
        try:
            db.session.commit()
            print(f"迁移完成！共更新了 {updated_count} 个审批实例")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"提交更改时出错: {e}")
            return False

def rollback_approval_template_versioning():
    """回滚审批模板版本化迁移"""
    
    app = create_app()
    
    with app.app_context():
        print("开始回滚审批模板版本化迁移...")
        
        try:
            with db.engine.connect() as connection:
                # 删除新添加的字段
                connection.execute(text("ALTER TABLE approval_instance DROP COLUMN IF EXISTS template_snapshot"))
                connection.execute(text("ALTER TABLE approval_instance DROP COLUMN IF EXISTS template_version"))
                connection.commit()
            
            print("回滚完成！")
            return True
        except Exception as e:
            print(f"回滚时出错: {e}")
            return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="审批模板版本化迁移")
    parser.add_argument("--rollback", action="store_true", help="回滚迁移")
    
    args = parser.parse_args()
    
    if args.rollback:
        success = rollback_approval_template_versioning()
    else:
        success = migrate_approval_template_versioning()
    
    sys.exit(0 if success else 1) 