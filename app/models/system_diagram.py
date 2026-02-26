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


class DiagramShareToken(db.Model):
    """外部分享令牌"""
    __tablename__ = 'diagram_share_tokens'

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    project_name = db.Column(db.String(200))
    designated_email = db.Column(db.String(200), nullable=False)
    source_diagram_id = db.Column(db.Integer, db.ForeignKey('system_diagrams.id'))
    expires_at = db.Column(db.DateTime, nullable=False)
    permission = db.Column(db.String(10), default='edit', nullable=False)  # 'view' | 'edit'
    is_active = db.Column(db.Boolean, default=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    created_by = db.relationship('User', backref=db.backref('diagram_shares', lazy='dynamic'))
    source_diagram = db.relationship('SystemDiagram', backref=db.backref('share_tokens', lazy='dynamic'))

    def __repr__(self):
        return f'<DiagramShareToken {self.token[:8]}...>'

    @property
    def is_expired(self):
        return datetime.now() > self.expires_at

    @property
    def is_valid(self):
        return self.is_active and not self.is_expired


class DiagramExternalSession(db.Model):
    """外部用户会话"""
    __tablename__ = 'diagram_external_sessions'

    id = db.Column(db.Integer, primary_key=True)
    share_token_id = db.Column(db.Integer, db.ForeignKey('diagram_share_tokens.id'), nullable=False)
    email = db.Column(db.String(200), nullable=False, index=True)
    diagram_id = db.Column(db.Integer, db.ForeignKey('system_diagrams.id'))
    access_count = db.Column(db.Integer, default=0)
    last_accessed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)

    share_token = db.relationship('DiagramShareToken', backref=db.backref('sessions', lazy='dynamic'))
    diagram = db.relationship('SystemDiagram', backref=db.backref('external_sessions', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('share_token_id', 'email', name='uq_share_token_email'),
    )
