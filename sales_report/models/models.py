from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    project_number = db.Column(db.String(50), unique=True, nullable=False)
    project_name = db.Column(db.String(100), nullable=False)
    current_stage = db.Column(db.String(50))
    authorization_number = db.Column(db.String(50))
    report_time = db.Column(db.DateTime, default=datetime.utcnow)
    distributor = db.Column(db.String(100))
    project_type = db.Column(db.String(50))
    source = db.Column(db.String(50))
    face_value = db.Column(db.Float)
    update_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Project {self.project_name}>'

class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    source = db.Column(db.String(50))
    province = db.Column(db.String(50))
    address = db.Column(db.String(200))
    contact_person = db.Column(db.String(50))
    position = db.Column(db.String(50))
    
    def __repr__(self):
        return f'<Customer {self.company_name}>'

class Quotation(db.Model):
    __tablename__ = 'quotations'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    company_info = db.Column(db.String(200))
    address_info = db.Column(db.String(200))
    quotation_date = db.Column(db.DateTime, default=datetime.utcnow)
    product_type = db.Column(db.String(50))
    
    def __repr__(self):
        return f'<Quotation {self.id}>'

class Score(db.Model):
    __tablename__ = 'scores'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'))
    design_institute_score = db.Column(db.Integer, default=0)
    dealer_score = db.Column(db.Integer, default=0)
    integrator_score = db.Column(db.Integer, default=0)
    user_score = db.Column(db.Integer, default=0)
    total_score = db.Column(db.Integer, default=0)
    update_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Score {self.total_score}>' 