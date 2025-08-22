# app.py
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from config import Config
from database import init_db
from models import db, User, QuizResult
import random
import json

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar base de datos
init_db(app)

# Preguntas y respuestas con sus puntuaciones
questions = [
    {
        "id": 1,
        "question": "La naturaleza de la innovación. Escenario: Tu equipo ha estado meses desarrollando un nuevo producto siguiendo un plan riguroso (etapa 1, etapa 2, etapa 3). De repente, un miembro junior del equipo propone una idea radicalmente diferente que surgió de una conversación informal con un cliente, pero que desvía completamente el plan original. ¿Qué haces?",
        "options": [
            {"text": "Desestimar la idea para mantener el enfoque en el plan original y cumplir con los plazos establecidos. La desviación es un riesgo inaceptable.", "score": 0.2},
            {"text": "Pedirle al empleado que documente la idea en un formulario de ideas para una posible revisión en el próximo ciclo de planificación, dentro de 6 meses.", "score": 0.4},
            {"text": "Destinar recursos limitados (ej: 2 personas, 1 semana) para prototipar rápidamente la nueva idea y testearla con el cliente, sin detener por completo el plan original.", "score": 1.0},
            {"text": "Reprogramar inmediatamente todos los recursos hacia la nueva idea porque suena más prometedora.", "score": 0.6}
        ]
    },
    {
        "id": 2,
        "question": "El rol del liderazgo. Escenario: La alta dirección anuncia una nueva iniciativa estratégica: 'Ser la empresa más innovadora del sector'. Sin embargo, no se comunica cómo se integrará esto con los objetivos operativos mensuales, no se asignan recursos adicionales y los bonos siguen ligados únicamente a la eficiencia. ¿Cuál es el principal riesgo?",
        "options": [
            {"text": "Los empleados no sentirán que la innovación sea una prioridad real y las urgencias operativas seguirán desplazando las iniciativas nuevas.", "score": 1.0},
            {"text": "Los competidores se enterarán de nuestra estrategia y copiarán nuestras ideas.", "score": 0.0},
            {"text": "La dirección está siendo demasiado ambiciosa y debería establecer una meta más realista.", "score": 0.3},
            {"text": "Los departamentos de I+D se sentirán presionados y su productividad podría bajar.", "score": 0.1}
        ]
    },
    {
        "id": 3,
        "question": "Gestión del Conocimiento y Colaboración. Escenario: María, una ingeniera senior, es la única que conoce a fondo un proceso crítico complejo (conocimiento tácito). Se jubila en 3 meses. ¿Cuál es la estrategia MÁS efectiva para asegurar que su conocimiento no se pierda?",
        "options": [
            {"text": "Pedirle que escribiera detalladamente todo lo que sabe en un manual de procedimientos.", "score": 0.5},
            {"text": "Asignar un sustituto para que la observe trabajar y le haga preguntas durante sus últimas semanas.", "score": 0.8},
            {"text": "Contratar a un consultor externo para que aprenda el proceso y luego lo enseñe a los demás.", "score": 0.2},
            {"text": "Crear un programa de mentoría donde María entrene a un pequeño grupo de empleados, fomentando sesiones de preguntas, resolución de problemas juntos y narración de experiencias pasadas.", "score": 1.0}
        ]
    },
    {
        "id": 4,
        "question": "Incentivos y Cultura. Escenario: Quieres fomentar que los empleados compartan más ideas y conocimientos entre departamentos. ¿Qué sistema de incentivos es más probable que funcione a largo plazo según la literatura?",
        "options": [
            {"text": "Un bono económico individual para la 'Idea del Mes'.", "score": 0.3},
            {"text": "Reconocimiento público y oportunidades de liderar proyectos para aquellos que colaboren y compartan abiertamente, integrado en sus evaluaciones de desempeño.", "score": 1.0},
            {"text": "Un evento anual de innovación con premios en efectivo.", "score": 0.1},
            {"text": "No implementar incentivos; se espera que los empleados compartan conocimiento por default.", "score": 0.0}
        ]
    },
    {
        "id": 5,
        "question": "Abordando la Complejidad. Escenario: Un proyecto de innovación importante se está volviendo impredecible; los requisitos cambian constantemente y surgen problemas inesperados. El equipo está frustrado. ¿Cuál es la mejor aproximación?",
        "options": [
            {"text": "Aumentar el control, imponer hitos más estrictos y reportes diarios para retomar el control del plan original.", "score": 0.1},
            {"text": "Cancelar el proyecto porque claramente no era viable.", "score": 0.0},
            {"text": "Reconocer que es un proceso complejo. Convocar una reunión con todas las partes involucradas para redefinir colectivamente el problema, aceptar los cambios como parte del proceso y ajustar el plan en base a los nuevos aprendizajes.", "score": 1.0},
            {"text": "Dividir el proyecto en partes más pequeñas y manejables, pero mantener el plan general sin cambios.", "score": 0.5}
        ]
    }
]

# Tipos de poderes disponibles
available_powers = [
    {"id": "corrector", "name": "Corrector", "description": "Revela la respuesta correcta", "uses": 2, "icon": "✓"},
    {"id": "double", "name": "Doble Puntos", "description": "Duplica los puntos de esta pregunta", "uses": 1, "icon": "2×"},
    {"id": "skip", "name": "Salto", "description": "Salta esta pregunta", "uses": 1, "icon": "→"},
    {"id": "time", "name": "Tiempo Extra", "description": "Añade 30 segundos extra", "uses": 1, "icon": "⏱"},
    {"id": "fifty", "name": "50/50", "description": "Elimina dos opciones incorrectas", "uses": 1, "icon": "½"}
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_quiz():
    nickname = request.form.get('nickname')
    if not nickname:
        return redirect(url_for('index'))
    
    # Guardar usuario en sesión
    session['nickname'] = nickname
    session['current_question'] = 0
    session['answers'] = []
    session['score'] = 0
    
    # Asignar poderes aleatorios al usuario
    num_powers = random.randint(2, 4)  # Entre 2 y 4 poderes
    user_powers = random.sample(available_powers, num_powers)
    session['powers'] = user_powers
    
    # Guardar usuario en la base de datos si no existe
    user = User.query.filter_by(nickname=nickname).first()
    if not user:
        user = User(nickname=nickname)
        db.session.add(user)
        db.session.commit()
    
    session['user_id'] = user.id
    
    return redirect(url_for('show_question'))

@app.route('/question')
def show_question():
    if 'current_question' not in session:
        return redirect(url_for('index'))
    
    current_idx = session['current_question']
    if current_idx >= len(questions):
        return redirect(url_for('show_results'))
    
    question = questions[current_idx]
    return render_template('quiz.html', 
                         question=question, 
                         current=current_idx+1, 
                         total=len(questions),
                         powers=session.get('powers', []))

@app.route('/answer', methods=['POST'])
def process_answer():
    if 'current_question' not in session:
        return jsonify({'error': 'Sesión no iniciada'}), 400
    
    current_idx = session['current_question']
    if current_idx >= len(questions):
        return jsonify({'error': 'No hay más preguntas'}), 400
    
    data = request.json
    answer = data.get('answer')
    power_used = data.get('power', None)
    
    # Guardar respuesta
    session['answers'] = session.get('answers', [])
    session['answers'].append({
        'question_id': current_idx,
        'answer': answer,
        'power_used': power_used
    })
    
    # Avanzar a la siguiente pregunta
    session['current_question'] = current_idx + 1
    
    return jsonify({'success': True, 'next_url': url_for('show_question')})

@app.route('/use_power', methods=['POST'])
def use_power():
    data = request.json
    power_id = data.get('power_id')
    question_id = data.get('question_id')
    
    # Buscar el poder en los poderes del usuario
    user_powers = session.get('powers', [])
    for power in user_powers:
        if power['id'] == power_id and power['uses'] > 0:
            # Reducir usos
            power['uses'] -= 1
            
            # Ejecutar efecto del poder
            if power_id == 'corrector':
                # Encontrar la respuesta correcta
                question = questions[question_id]
                correct_answer = next((opt for opt in question['options'] if opt['score'] == 1.0), None)
                return jsonify({
                    'success': True, 
                    'correct_answer': correct_answer['text'] if correct_answer else ''
                })
            
            elif power_id == 'fifty':
                # Eliminar dos opciones incorrectas
                question = questions[question_id]
                incorrect_answers = [opt for opt in question['options'] if opt['score'] < 1.0]
                # Tomar dos opciones incorrectas aleatorias
                to_remove = random.sample(incorrect_answers, min(2, len(incorrect_answers)))
                return jsonify({
                    'success': True,
                    'remove_options': [opt['text'] for opt in to_remove]
                })
            
            elif power_id == 'double':
                # Marcar que esta pregunta tendrá doble puntuación
                return jsonify({'success': True, 'double_points': True})
            
            elif power_id == 'skip':
                # Saltar esta pregunta
                session['current_question'] = session.get('current_question', 0) + 1
                return jsonify({'success': True, 'skip': True})
            
            elif power_id == 'time':
                # Añadir tiempo extra (implementar en frontend)
                return jsonify({'success': True, 'extra_time': 30})
    
    return jsonify({'success': False, 'error': 'Poder no disponible'})

@app.route('/results')
def show_results():
    if 'answers' not in session or len(session['answers']) < len(questions):
        return redirect(url_for('index'))
    
    # Calcular puntuación
    total_score = 0
    max_score = len(questions)
    powers_used = []
    
    for answer in session['answers']:
        question = questions[answer['question_id']]
        selected_option = next((opt for opt in question['options'] if opt['text'] == answer['answer']), None)
        
        if selected_option:
            score = selected_option['score']
            
            # Verificar si se usó doble puntuación
            if answer.get('power_used') == 'double':
                score *= 2
                if score > 1.0:
                    score = 1.0
                powers_used.append('Doble puntos en pregunta ' + str(answer['question_id'] + 1))
            
            total_score += score
    
    # Calcular porcentaje
    percentage = (total_score / max_score) * 100
    
    # Guardar resultado en base de datos
    if 'user_id' in session:
        result = QuizResult(
            user_id=session['user_id'],
            score=total_score,
            max_score=max_score,
            percentage=percentage,
            powers_used=', '.join(powers_used)
        )
        db.session.add(result)
        db.session.commit()
    
    return render_template('results.html', 
                         score=total_score, 
                         max_score=max_score, 
                         percentage=percentage,
                         powers_used=powers_used)

if __name__ == '__main__':
    app.run(debug=True)