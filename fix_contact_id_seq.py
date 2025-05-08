from app import create_app, db
from sqlalchemy import text

def fix_contact_id_seq():
    app = create_app()
    with app.app_context():
        # 获取contacts表当前最大id
        max_id = db.session.execute(text('SELECT MAX(id) FROM contacts')).scalar() or 1
        # 设置序列到最大id
        db.session.execute(text(f"SELECT setval('contacts_id_seq', {max_id}, true);"))
        db.session.commit()
        print(f"contacts_id_seq已重置到{max_id}")

if __name__ == '__main__':
    fix_contact_id_seq() 