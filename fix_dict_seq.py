from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    db.session.execute(text("SELECT setval('dictionaries_id_seq', (SELECT MAX(id) FROM dictionaries));"))
    db.session.commit()
    print("已修复dictionaries主键自增序列。") 