#!/usr/bin/env python
from app import create_app, db
from app.models.approval import ApprovalProcessTemplate, ApprovalStep, ApprovalInstance, ApprovalStatus
from app.models.project import Project

# 创建Flask应用
app = create_app()

def check_template_validity(template_id):
    """检查审批模板是否有效"""
    with app.app_context():
        template = ApprovalProcessTemplate.query.get(template_id)
        if not template:
            print(f"错误: 审批模板 ID {template_id} 不存在")
            return False
        
        if not template.is_active:
            print(f"错误: 审批模板 '{template.name}' 已被禁用 (is_active=False)")
            return False
            
        # 检查是否有审批步骤
        steps = ApprovalStep.query.filter_by(process_id=template_id).order_by(ApprovalStep.step_order.asc()).all()
        if not steps:
            print(f"错误: 审批模板 '{template.name}' 没有配置审批步骤")
            return False
            
        print(f"审批模板 '{template.name}' 有效，共有 {len(steps)} 个审批步骤:")
        for step in steps:
            approver_name = step.approver.real_name if step.approver and hasattr(step.approver, 'real_name') and step.approver.real_name else step.approver.username if step.approver else '未指定'
            print(f"  步骤 {step.step_order}: {step.step_name} - 审批人: {approver_name}")
            
        # 检查必填字段
        if hasattr(template, 'required_fields') and template.required_fields and len(template.required_fields) > 0:
            print(f"审批模板 '{template.name}' 设置了以下必填字段:")
            for field in template.required_fields:
                print(f"  - {field}")
                
        return True
        

def check_project_existing_approval(project_id):
    """检查项目是否已有审批实例"""
    with app.app_context():
        # 检查项目是否存在
        project = Project.query.get(project_id)
        if not project:
            print(f"错误: 项目 ID {project_id} 不存在")
            return False
            
        print(f"项目信息: ID={project.id}, 名称='{project.project_name}'")
        
        # 检查是否存在审批实例
        instance = ApprovalInstance.query.filter_by(
            object_type='project', 
            object_id=project_id
        ).first()
        
        if instance:
            status_str = "审批中" if instance.status == ApprovalStatus.PENDING else (
                "已通过" if instance.status == ApprovalStatus.APPROVED else 
                "已拒绝" if instance.status == ApprovalStatus.REJECTED else "未知状态"
            )
            
            template_name = instance.process.name if instance.process else '未知模板'
            
            print(f"错误: 项目已存在审批实例:")
            print(f"  审批ID: {instance.id}")
            print(f"  审批模板: {template_name}")
            print(f"  审批状态: {status_str}")
            print(f"  发起时间: {instance.started_at}")
            
            print("\n如需删除现有审批实例并重新发起，请以管理员身份登录系统，执行以下SQL语句:")
            print(f"  DELETE FROM approval_record WHERE instance_id = {instance.id};")
            print(f"  DELETE FROM approval_instance WHERE id = {instance.id};")
            
            return False
        else:
            print("项目当前没有审批实例，可以发起新的审批")
            return True


def check_required_fields(project_id, template_id):
    """检查项目是否填写了审批模板要求的必填字段"""
    with app.app_context():
        project = Project.query.get(project_id)
        if not project:
            print(f"错误: 项目 ID {project_id} 不存在")
            return False
            
        template = ApprovalProcessTemplate.query.get(template_id)
        if not template:
            print(f"错误: 审批模板 ID {template_id} 不存在")
            return False
            
        if not hasattr(template, 'required_fields') or not template.required_fields:
            print(f"审批模板 '{template.name}' 没有设置必填字段")
            return True
            
        # 检查必填字段
        missing_fields = []
        for field in template.required_fields:
            if hasattr(project, field):
                field_value = getattr(project, field)
                if field_value is None or field_value == '' or (isinstance(field_value, list) and len(field_value) == 0):
                    missing_fields.append(field)
            else:
                print(f"警告: 项目对象没有字段 '{field}'")
                missing_fields.append(field)
                
        if missing_fields:
            print(f"错误: 项目缺少以下必填字段:")
            for field in missing_fields:
                print(f"  - {field}")
            return False
        else:
            print(f"项目已填写所有必填字段")
            return True


def main():
    import sys
    
    if len(sys.argv) < 3:
        print("用法: python check_approval_issue.py <项目ID> <模板ID>")
        sys.exit(1)
    
    try:
        project_id = int(sys.argv[1])
        template_id = int(sys.argv[2])
    except ValueError:
        print("错误: 项目ID和模板ID必须是数字")
        sys.exit(1)
    
    print("=" * 60)
    print("项目审批发起问题诊断工具")
    print("=" * 60)
    
    # 检查审批模板是否有效
    print("\n1. 检查审批模板有效性:")
    template_valid = check_template_validity(template_id)
    
    # 检查项目是否已有审批实例
    print("\n2. 检查项目是否已有审批实例:")
    no_existing_approval = check_project_existing_approval(project_id)
    
    # 检查必填字段
    print("\n3. 检查必填字段:")
    fields_valid = check_required_fields(project_id, template_id)
    
    # 总结
    print("\n" + "=" * 60)
    print("诊断结果总结:")
    if template_valid and no_existing_approval and fields_valid:
        print("✅ 所有检查均通过，项目应该可以正常发起审批。")
        print("   如仍然无法发起审批，请检查系统日志或联系管理员。")
    else:
        print("❌ 发现以下问题:")
        if not template_valid:
            print("   - 审批模板无效，请确保模板存在且已添加审批步骤")
        if not no_existing_approval:
            print("   - 项目已有审批实例，需要先删除现有审批")
        if not fields_valid:
            print("   - 项目缺少必填字段，请完善项目信息")
    
    
if __name__ == "__main__":
    main() 