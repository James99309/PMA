from app import create_app, db
from app.models.user import User

app = create_app()
with app.app_context():
    users = User.query.all()
    print('id | username | real_name | company_name | department | is_department_manager | is_active')
    for u in users:
        print(f'{u.id} | {u.username} | {u.real_name} | {u.company_name} | {u.department} | {u.is_department_manager} | {u.is_active}') 