from app import create_app
app = create_app()

with app.app_context():
    from app.models.notification import EventRegistry, UserEventSubscription
    from app.models.user import User
    from app import db
    
    # 检查NIJIE用户
    nijie = User.query.filter_by(username="NIJIE").first()
    if not nijie:
        print("未找到NIJIE用户")
        exit(1)
    
    print(f"NIJIE用户ID: {nijie.id}")
    
    # 检查customer_created事件
    customer_created = EventRegistry.query.filter_by(event_key='customer_created').first()
    if not customer_created:
        print("未找到customer_created事件，正在创建...")
        # 创建事件
        customer_created = EventRegistry(
            event_key='customer_created',
            label_zh='客户创建',
            label_en='Customer Created',
            default_enabled=True,
            enabled=True
        )
        db.session.add(customer_created)
        db.session.commit()
        print(f"已创建customer_created事件，ID: {customer_created.id}")
    else:
        print(f"已找到customer_created事件，ID: {customer_created.id}")
    
    # 检查NIJIE是否订阅了自己的customer_created事件
    subscription = UserEventSubscription.query.filter_by(
        user_id=nijie.id,
        target_user_id=nijie.id,
        event_id=customer_created.id
    ).first()
    
    if subscription:
        if not subscription.enabled:
            print("找到订阅记录，但已禁用，正在启用...")
            subscription.enabled = True
            db.session.commit()
            print("订阅已启用")
        else:
            print("已订阅customer_created事件")
    else:
        print("未订阅customer_created事件，正在创建订阅...")
        # 创建订阅
        new_subscription = UserEventSubscription(
            user_id=nijie.id,
            target_user_id=nijie.id,
            event_id=customer_created.id,
            enabled=True
        )
        db.session.add(new_subscription)
        db.session.commit()
        print(f"已创建订阅，ID: {new_subscription.id}")
    
    # 列出所有订阅情况
    print("\n当前所有订阅:")
    all_subscriptions = UserEventSubscription.query.filter_by(user_id=nijie.id).all()
    for sub in all_subscriptions:
        event = EventRegistry.query.get(sub.event_id)
        target_user = User.query.get(sub.target_user_id)
        print(f"事件: {event.event_key} ({event.label_zh}), 目标用户: {target_user.username}, 启用: {sub.enabled}") 