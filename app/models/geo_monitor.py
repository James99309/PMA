from app.extensions import db
from datetime import datetime


class GeoIntent(db.Model):
    __tablename__ = 'geo_intent'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    frequency = db.Column(db.String(20), default='daily')  # daily / weekly
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    queries = db.relationship('GeoQuery', backref='intent', lazy='dynamic', cascade='all, delete-orphan')


class GeoQuery(db.Model):
    __tablename__ = 'geo_query'
    id = db.Column(db.Integer, primary_key=True)
    intent_id = db.Column(db.Integer, db.ForeignKey('geo_intent.id'), nullable=False)
    market = db.Column(db.String(10), nullable=False)   # cn / en / my / id ...
    query_text = db.Column(db.Text, nullable=False)
    excluded = db.Column(db.Boolean, default=False)
    results = db.relationship('GeoResult', backref='query', lazy='dynamic', cascade='all, delete-orphan')


class GeoResult(db.Model):
    __tablename__ = 'geo_result'
    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.Integer, db.ForeignKey('geo_query.id'), nullable=False)
    run_at = db.Column(db.DateTime, default=datetime.utcnow)
    mentioned = db.Column(db.String(20))    # yes / no / indirect
    rank = db.Column(db.Integer)            # None = not mentioned
    sentiment = db.Column(db.String(20))    # positive / neutral / negative
    ai_response = db.Column(db.Text)        # full AI answer text
    cited_urls = db.Column(db.JSON)         # list of cited URLs
    error = db.Column(db.Text)              # if run failed


class GeoSettings(db.Model):
    __tablename__ = 'geo_settings'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text)
