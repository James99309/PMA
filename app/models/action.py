from app import db
from datetime import datetime
from app.models.customer import Company, Contact
from app.models.project import Project
from app.models.user import User

class ActionReply(db.Model):
    __tablename__ = 'action_reply'
    id = db.Column(db.Integer, primary_key=True)
    action_id = db.Column(db.Integer, db.ForeignKey('actions.id'), nullable=False)
    parent_reply_id = db.Column(db.Integer, db.ForeignKey('action_reply.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    parent_reply = db.relationship('ActionReply', remote_side=[id], backref='children')
    owner = db.relationship('User')

class Action(db.Model):
    __tablename__ = 'actions'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'), nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    communication = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # 关联关系
    contact = db.relationship('Contact', backref=db.backref('actions', lazy=True))
    company = db.relationship('Company', backref=db.backref('actions', lazy=True))
    project = db.relationship('Project', backref=db.backref('actions', lazy=True))
    owner = db.relationship('User', backref=db.backref('actions', lazy=True))
    replies = db.relationship('ActionReply', backref='action', lazy='dynamic', cascade='all, delete-orphan')