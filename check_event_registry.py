from app import create_app
app = create_app()

with app.app_context():
    from app.models.notification import EventRegistry
    
    # 获取所有事件
    events = EventRegistry.query.all()
    
    print("所有事件注册表记录:")
    for event in events:
        print(f"ID: {event.id}, 键: {event.event_key}, 名称: {event.label_zh}, 启用: {event.enabled}")
    
    # 特别检查customer_created事件
    customer_created = EventRegistry.query.filter_by(event_key='customer_created').first()
    
    if customer_created:
        print("\n找到customer_created事件:")
        print(f"ID: {customer_created.id}, 键: {customer_created.event_key}, 名称: {customer_created.label_zh}, 启用: {customer_created.enabled}")
    else:
        print("\n未找到customer_created事件，这是问题所在!")
        
        # 查找哪些订阅者订阅了customer_created事件
        from app.models.notification import UserEventSubscription
        from app.models.user import User
        
        print("\n检查NIJIE用户的所有订阅:")
        nijie = User.query.filter_by(username="NIJIE").first()
        if nijie:
            subs = UserEventSubscription.query.filter_by(user_id=nijie.id).all()
            for sub in subs:
                try:
                    print(f"事件: {sub.event.event_key}, 目标用户: {sub.target_user_id}, 启用: {sub.enabled}")
                except:
                    print(f"事件ID: {sub.event_id} - 无法获取事件信息，该事件可能不存在") 