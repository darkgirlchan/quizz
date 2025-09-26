# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    # Nuevo: Nickname generado como 'líder_participantes'
    nickname = db.Column(db.String(50), unique=True, nullable=False)
    # Nuevo: Nombre del líder
    leader_name = db.Column(db.String(50), nullable=False)
    # Nuevo: Número de participantes
    num_participants = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación con los resultados
    results = db.relationship('QuizResult', backref='user', lazy=True)

class QuizResult(db.Model):
    __tablename__ = 'quiz_results'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Campos de puntuación del PRIMER INTENTO
    costs_score_initial = db.Column(db.Float, nullable=False)
    customer_satisfaction_score_initial = db.Column(db.Float, nullable=False)
    risks_score_initial = db.Column(db.Float, nullable=False)
    sustainability_score_initial = db.Column(db.Float, nullable=False)
    total_score_initial = db.Column(db.Float, nullable=False, default=0.0)

    # Campos de puntuación del SEGUNDO INTENTO (Retake) - Pueden ser NULL
    costs_score_retake = db.Column(db.Float, nullable=True)
    customer_satisfaction_score_retake = db.Column(db.Float, nullable=True)
    risks_score_retake = db.Column(db.Float, nullable=True)
    sustainability_score_retake = db.Column(db.Float, nullable=True)
    total_score_retake = db.Column(db.Float, nullable=True)
    
    powers_used = db.Column(db.String(200))
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relación con los intentos de preguntas
    question_attempts = db.relationship('QuestionAttempt', backref='quiz_result', lazy=True)

# Nueva tabla para guardar el score detallado de cada pregunta
class QuestionAttempt(db.Model):
    __tablename__ = 'question_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    result_id = db.Column(db.Integer, db.ForeignKey('quiz_results.id'), nullable=False)
    question_id = db.Column(db.Integer, nullable=False) # ID de la pregunta
    is_retake = db.Column(db.Boolean, nullable=False, default=False) # Es del retake?
    
    # Puntajes obtenidos en esta pregunta
    costs_score = db.Column(db.Float, nullable=False)
    customer_satisfaction_score = db.Column(db.Float, nullable=False)
    risks_score = db.Column(db.Float, nullable=False)
    sustainability_score = db.Column(db.Float, nullable=False)
    
    # Puntaje total de la pregunta (para fácil ordenamiento)
    total_score = db.Column(db.Float, nullable=False)
    
    selected_answer = db.Column(db.String(500))