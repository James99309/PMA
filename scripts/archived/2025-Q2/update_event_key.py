from app import create_app, db
from app.models.notification import EventRegistry, UserEventSubscription

# 创建应用上下文
app = create_app()

with app.app_context():
    # 检查新事件键是否已存在
    existing_new_event = EventRegistry.query.filter_by(event_key='project_status_updated').first()
    if existing_new_event:
        print(f"新事件键已存在: ID={existing_new_event.id}, 键名={existing_new_event.event_key}")
    
    # 检查旧事件键是否存在
    old_event = EventRegistry.query.filter_by(event_key='project_stage_changed').first()
    if old_event:
        print(f"找到旧事件: ID={old_event.id}, 键名={old_event.event_key}")
        
        # 更新事件键名
        old_event.event_key = 'project_status_updated'
        print(f"正在更新为: 键名={old_event.event_key}")
        
        # 提交更改
        db.session.commit()
        print("事件注册表更新成功")
    else:
        print("未找到旧事件键，检查是否需要创建新事件...")
        
        # 如果新事件也不存在，则创建
        if not existing_new_event:
            print("创建新事件...")
            new_event = EventRegistry(
                event_key='project_status_updated',
                label_zh='项目阶段变更',
                label_en='Project Stage Changed',
                default_enabled=True,
                enabled=True
            )
            db.session.add(new_event)
            db.session.commit()
            print(f"已创建新事件: ID={new_event.id}, 键名={new_event.event_key}")
    
    # 更新用户订阅表中的event_id
    if old_event and existing_new_event:
        print(f"需要更新用户订阅表中的事件ID: 从{old_event.id}到{existing_new_event.id}")
        # 此情况暂不处理，因为复杂度较高
    
    # 打印所有事件检查结果
    print("\n当前所有事件:")
    for e in EventRegistry.query.all():
        print(f"ID:{e.id}, 键名:{e.event_key}, 名称:{e.label_zh}, 启用:{e.enabled}")
        
    print("\n完成更新！") 