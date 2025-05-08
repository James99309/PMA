from app import db, create_app
from app.models.project import Project
from app.models.quotation import Quotation

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        projects = Project.query.all()
        for p in projects:
            total = db.session.query(db.func.sum(Quotation.amount)).filter(Quotation.project_id==p.id).scalar() or 0.0
            p.quotation_customer = total
            print(f'项目ID={p.id} 总额={total}')
        db.session.commit()
        print('所有项目报价总额已修复完成。') 