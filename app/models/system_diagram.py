from app import db
from datetime import datetime


class SystemDiagram(db.Model):
    __tablename__ = 'system_diagrams'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, default='未命名系统图')
    description = db.Column(db.Text)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), index=True)
    diagram_data = db.Column(db.JSON)  # {nodes, edges, viewX, viewY, scale}
    thumbnail_svg = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    is_template = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    owner = db.relationship('User', backref=db.backref('system_diagrams', lazy='dynamic'))
    project = db.relationship('Project', backref=db.backref('system_diagrams', lazy='dynamic'))

    def __repr__(self):
        return f'<SystemDiagram {self.id}: {self.name}>'
