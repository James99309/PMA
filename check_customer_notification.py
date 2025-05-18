from app import create_app
app = create_app()

with app.app_context():
    from app.models.notification import EventRegistry, UserEventSubscription
    from app.models.user import User
    
    # 1. 检查NIJIE用户信息
    nijie = User.query.filter_by(username="NIJIE").first()
    if nijie:
        print(f"NIJIE用户ID: {nijie.id}, 邮箱: {nijie.email}")
    else:
        print("未找到NIJIE用户")
    
    # 2. 检查customer_created事件
    customer_created = EventRegistry.query.filter_by(event_key='customer_created').first()
    if customer_created:
        print(f"\ncustomer_created事件: ID={customer_created.id}, 名称={customer_created.label_zh}, 启用={customer_created.enabled}")
    else:
        print("\n未找到customer_created事件")
    
    # 3. 检查NIJIE的订阅情况
    if nijie and customer_created:
        print("\nNIJIE的订阅情况:")
        subscriptions = UserEventSubscription.query.filter_by(
            user_id=nijie.id,
            event_id=customer_created.id,
            enabled=True
        ).all()
        
        if subscriptions:
            for sub in subscriptions:
                target_user = User.query.get(sub.target_user_id)
                print(f"订阅ID: {sub.id}, 订阅者: {nijie.username}, 目标用户: {target_user.username if target_user else '未知'}, 启用: {sub.enabled}")
        else:
            print("NIJIE没有订阅customer_created事件")
    
    # 4. 检查客户创建通知函数参数
    print("\n检查customer.py中的通知调用问题:")
    print("app/views/customer.py中的调用方式:")
    print("trigger_event_notification('customer_created', target=company, user=current_user)")
    print("正确的调用参数应该是:")
    print("trigger_event_notification('customer_created', target_user_id=current_user.id, context={'target': company, 'user': current_user})")
    
    # 5. 检查邮件模板文件
    import os
    template_path = 'app/templates/emails/customer_created.html'
    print(f"\n邮件模板文件: {template_path}")
    if os.path.exists(template_path):
        print("✅ 邮件模板文件存在")
    else:
        print("❌ 邮件模板文件不存在") 