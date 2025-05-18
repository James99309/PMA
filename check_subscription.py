from app import create_app
app = create_app()

with app.app_context():
    from app.models.notification import EventRegistry, UserEventSubscription
    from app.models.user import User
    
    # 查询事件注册表
    print('事件注册表:')
    events = EventRegistry.query.all()
    for e in events:
        print(f'ID:{e.id}, 键名:{e.event_key}, 名称:{e.label_zh}, 启用:{e.enabled}')
    
    # 查找NIJIE用户
    nijie = User.query.filter_by(username='NIJIE').first()
    print(f'\nNIJIE用户ID: {nijie.id if nijie else "未找到"}')
    
    # 查询NIJIE的订阅情况
    if nijie:
        print('\nNIJIE的订阅情况:')
        subs = UserEventSubscription.query.filter_by(user_id=nijie.id).all()
        
        if not subs:
            print('未找到任何订阅')
        
        for s in subs:
            print(f'事件:{s.event.event_key}, 目标用户:{s.target_user_id}, 启用:{s.enabled}') 