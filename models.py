# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación con los resultados
    results = db.relationship('QuizResult', backref='user', lazy=True)

class QuizResult(db.Model):
    __tablename__ = 'quiz_results'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)
    max_score = db.Column(db.Float, nullable=False)
    percentage = db.Column(db.Float, nullable=False)
    powers_used = db.Column(db.String(200))
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)