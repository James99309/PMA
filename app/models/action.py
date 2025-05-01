from app import db
from datetime import datetime
from app.models.customer import Company, Contact
from app.models.project import Project
from app.models.user import User

class Action(db.Model):
    __tablename__ = 'actions'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    communication = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # 关联关系
    contact = db.relationship('Contact', backref=db.backref('actions', lazy=True))
    company = db.relationship('Company', backref=db.backref('actions', lazy=True))
    project = db.relationship('Project', backref=db.backref('actions', lazy=True))
    owner = db.relationship('User', backref=db.backref('actions', lazy=True))