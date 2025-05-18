from app import create_app
app = create_app()

with app.app_context():
    from app.models.notification import EventRegistry, UserEventSubscription
    from app.models.user import User
    
    # 查找NIJIE用户
    nijie = User.query.filter_by(username="NIJIE").first()
    print("Nijie ID:", nijie.id if nijie else "Not found")
    
    # 检查事件注册表
    print("\n事件注册表:")
    for e in EventRegistry.query.all():
        print(f"ID:{e.id}, Key:{e.event_key}, 名称:{e.label_zh}, 启用:{e.enabled}")
    
    # 检查NIJIE的订阅情况
    print("\nNijie账户订阅:")
    if nijie:
        subs = UserEventSubscription.query.filter_by(user_id=nijie.id).all()
        if not subs:
            print("未找到任何订阅")
        for s in subs:
            print(f"事件:{s.event.event_key}, 目标用户:{s.target_user_id}, 启用:{s.enabled}") 