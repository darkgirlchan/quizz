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

# Preguntas y respuestas con puntuaciones por categoría
questions = [
    {
        "id": 1,
        "question": "La naturaleza de la innovación. Escenario: Tu equipo ha estado meses desarrollando un nuevo producto siguiendo un plan riguroso (etapa 1, etapa 2, etapa 3). De repente, un miembro junior del equipo propone una idea radicalmente diferente que surgió de una conversación informal con un cliente, pero que desvía completamente el plan original. ¿Qué haces?",
        "options": [
            {"text": "Desestimar la idea para mantener el enfoque en el plan original y cumplir con los plazos establecidos. La desviación es un riesgo inaceptable.", "scores": {"costs": 1.0, "customer_satisfaction": 0.2, "risks": 0.5, "sustainability": 0.1}},
            {"text": "Pedirle al empleado que documente la idea en un formulario de ideas para una posible revisión en el próximo ciclo de planificación, dentro de 6 meses.", "scores": {"costs": 0.9, "customer_satisfaction": 0.4, "risks": 0.6, "sustainability": 0.3}},
            {"text": "Destinar recursos limitados (ej: 2 personas, 1 semana) para prototipar rápidamente la nueva idea y testearla con el cliente, sin detener por completo el plan original.", "scores": {"costs": 0.6, "customer_satisfaction": 0.9, "risks": 0.9, "sustainability": 0.9}},
            {"text": "Reprogramar inmediatamente todos los recursos hacia la nueva idea porque suena más prometedora.", "scores": {"costs": 0.1, "customer_satisfaction": 0.7, "risks": 0.1, "sustainability": 0.3}}
        ]
    },
    {
        "id": 2,
        "question": "El rol del liderazgo. Escenario: La alta dirección anuncia una nueva iniciativa estratégica: 'Ser la empresa más innovadora del sector'. Sin embargo, no se comunica cómo se integrará esto con los objetivos operativos mensuales, no se asignan recursos adicionales y los bonos siguen ligados únicamente a la eficiencia. ¿Cuál es el principal riesgo?",
        "options": [
            {"text": "Los empleados no sentirán que la innovación sea una prioridad real y las urgencias operativas seguirán desplazando las iniciativas nuevas.", "scores": {"costs": 0.8, "customer_satisfaction": 0.9, "risks": 0.9, "sustainability": 1.0}},
            {"text": "Los competidores se enterarán de nuestra estrategia y copiarán nuestras ideas.", "scores": {"costs": 0.4, "customer_satisfaction": 0.5, "risks": 0.3, "sustainability": 0.3}},
            {"text": "La dirección está siendo demasiado ambiciosa y debería establecer una meta más realista.", "scores": {"costs": 0.5, "customer_satisfaction": 0.4, "risks": 0.4, "sustainability": 0.3}},
            {"text": "Los departamentos de I+D se sentirán presionados y su productividad podría bajar.", "scores": {"costs": 0.6, "customer_satisfaction": 0.5, "risks": 0.5, "sustainability": 0.4}}
        ]
    },
    {
        "id": 3,
        "question": "Gestión del Conocimiento y Colaboración. Escenario: María, una ingeniera senior, es la única que conoce a fondo un proceso crítico complejo (conocimiento tácito). Se jubila en 3 meses. ¿Cuál es la estrategia MÁS efectiva para asegurar que su conocimiento no se pierda?",
        "options": [
            {"text": "Pedirle que escribiera detalladamente todo lo que sabe en un manual de procedimientos.", "scores": {"costs": 0.7, "customer_satisfaction": 0.2, "risks": 0.2, "sustainability": 0.2}},
            {"text": "Asignar un sustituto para que la observe trabajar y le haga preguntas durante sus últimas semanas.", "scores": {"costs": 0.6, "customer_satisfaction": 0.6, "risks": 0.5, "sustainability": 0.5}},
            {"text": "Contratar a un consultor externo para que aprenda el proceso y luego lo enseñe a los demás.", "scores": {"costs": 0.1, "customer_satisfaction": 0.4, "risks": 0.3, "sustainability": 0.2}},
            {"text": "Crear un programa de mentoría donde María entrene a un pequeño grupo de empleados, fomentando sesiones de preguntas, resolución de problemas juntos y narración de experiencias pasadas.", "scores": {"costs": 0.4, "customer_satisfaction": 0.9, "risks": 0.9, "sustainability": 1.0}}
        ]
    },
    {
        "id": 4,
        "question": "Incentivos y Cultura. Escenario: Quieres fomentar que los empleados compartan más ideas y conocimientos entre departamentos. ¿Qué sistema de incentivos es más probable que funcione a largo plazo según la literatura?",
        "options": [
            {"text": "Un bono económico individual para la 'Idea del Mes'.", "scores": {"costs": 0.6, "customer_satisfaction": 0.4, "risks": 0.3, "sustainability": 0.2}},
            {"text": "Reconocimiento público y oportunidades de liderar proyectos para aquellos que colaboren y compartan abiertamente, integrado en sus evaluaciones de desempeño.", "scores": {"costs": 0.9, "customer_satisfaction": 0.8, "risks": 0.8, "sustainability": 1.0}},
            {"text": "Un evento anual de innovación con premios en efectivo.", "scores": {"costs": 0.4, "customer_satisfaction": 0.5, "risks": 0.5, "sustainability": 0.4}},
            {"text": "No implementar incentivos; se espera que los empleados compartan conocimiento por default.", "scores": {"costs": 1.0, "customer_satisfaction": 0.2, "risks": 0.2, "sustainability": 0.1}}
        ]
    },
    {
        "id": 5,
        "question": "Abordando la Complejidad. Escenario: Un proyecto de innovación importante se está volviendo impredecible; los requisitos cambian constantemente y surgen problemas inesperados. El equipo está frustrado. ¿Cuál es la mejor aproximación?",
        "options": [
            {"text": "Aumentar el control, imponer hitos más estrictos y reportes diarios para retomar el control del plan original.", "scores": {"costs": 0.3, "customer_satisfaction": 0.1, "risks": 0.1, "sustainability": 0.1}},
            {"text": "Cancelar el proyecto porque claramente no era viable.", "scores": {"costs": 0.8, "customer_satisfaction": 0.0, "risks": 0.4, "sustainability": 0.2}},
            {"text": "Reconocer que es un proceso complejo. Convocar una reunión con todas las partes involucradas para redefinir colectivamente el problema, aceptar los cambios como parte del proceso y ajustar el plan en base a los nuevos aprendizajes.", "scores": {"costs": 0.7, "customer_satisfaction": 0.9, "risks": 0.9, "sustainability": 1.0}},
            {"text": "Dividir el proyecto en partes más pequeñas y manejables, pero mantener el plan general sin cambios.", "scores": {"costs": 0.5, "customer_satisfaction": 0.3, "risks": 0.4, "sustainability": 0.4}}
        ]
    },
    {
        "id": 6,
        "question": "Métricas y KPIs de Innovación. Escenario: La junta directiva exige medir el 'retorno de la inversión' (ROI) en innovación para el próximo trimestre. Quieren ver resultados tangibles. ¿Qué enfoque propones para medir el éxito?",
        "options": [
            {"text": "Medir únicamente los ingresos directos generados por los nuevos productos lanzados en los últimos 6 meses.", "scores": {"costs": 0.8, "customer_satisfaction": 0.3, "risks": 0.2, "sustainability": 0.1}},
            {"text": "Implementar un 'conteo de ideas', premiando a los departamentos que más propuestas generen.", "scores": {"costs": 0.9, "customer_satisfaction": 0.2, "risks": 0.2, "sustainability": 0.2}},
            {"text": "Proponer un Cuadro de Mando Balanceado que incluya métricas de proceso (ej. nº de experimentos, velocidad de aprendizaje) y métricas de resultado (ej. % de ingresos por nuevos productos en los últimos 3 años).", "scores": {"costs": 0.5, "customer_satisfaction": 0.9, "risks": 0.9, "sustainability": 1.0}},
            {"text": "Enfocarse en la satisfacción del equipo y la cultura, midiendo el 'engagement' de los empleados en iniciativas de innovación.", "scores": {"costs": 0.7, "customer_satisfaction": 0.5, "risks": 0.4, "sustainability": 0.7}}
        ]
    },
    {
        "id": 7,
        "question": "Gestión del Riesgo y Cultura del Fracaso. Escenario: Un equipo invierte tres meses y un presupuesto significativo en un proyecto piloto que, finalmente, demuestra no ser viable. El proyecto se cancela. ¿Cómo debe la dirección comunicar esto a la organización?",
        "options": [
            {"text": "En una reunión general, se destaca el 'fracaso' del equipo como un ejemplo de mala planificación y se anuncian controles más estrictos para futuros proyectos.", "scores": {"costs": 0.8, "customer_satisfaction": 0.2, "risks": 0.1, "sustainability": 0.0}},
            {"text": "Celebrar una sesión de 'aprendizaje del fracaso' donde el equipo expone qué funcionó, qué no, y cuáles son los aprendizajes clave. El esfuerzo y la valentía del equipo son reconocidos públicamente.", "scores": {"costs": 0.7, "customer_satisfaction": 0.8, "risks": 0.9, "sustainability": 1.0}},
            {"text": "No se comunica nada para no alarmar a otros equipos y se archiva el proyecto discretamente.", "scores": {"costs": 0.6, "customer_satisfaction": 0.4, "risks": 0.3, "sustainability": 0.2}},
            {"text": "Se publica un informe detallado con los errores técnicos, pero sin mencionar nombres, y se distribuye por correo electrónico.", "scores": {"costs": 0.7, "customer_satisfaction": 0.5, "risks": 0.5, "sustainability": 0.4}}
        ]
    },
    {
        "id": 8,
        "question": "Pensamiento Sistémico en la Práctica. Escenario: El departamento de Marketing lanza una campaña exitosa que promete una nueva funcionalidad del producto para el próximo mes. Sin embargo, nunca consultaron al equipo de Desarrollo, que necesita al menos tres meses para construirla de forma estable. ¿Cuál es la causa raíz del problema?",
        "options": [
            {"text": "El equipo de Desarrollo es demasiado lento y debe adoptar metodologías más ágiles para cumplir con las demandas del mercado.", "scores": {"costs": 0.2, "customer_satisfaction": 0.1, "risks": 0.2, "sustainability": 0.1}},
            {"text": "El departamento de Marketing fue irresponsable al hacer promesas sin confirmar la viabilidad técnica.", "scores": {"costs": 0.3, "customer_satisfaction": 0.2, "risks": 0.2, "sustainability": 0.1}},
            {"text": "La empresa carece de un proceso de gobernanza de innovación que asegure la comunicación y colaboración transversal antes de tomar decisiones que afecten a múltiples áreas.", "scores": {"costs": 0.8, "customer_satisfaction": 0.9, "risks": 0.9, "sustainability": 1.0}},
            {"text": "Falta un líder de producto que sirva como puente entre Marketing y Desarrollo.", "scores": {"costs": 0.6, "customer_satisfaction": 0.6, "risks": 0.5, "sustainability": 0.5}}
        ]
    },
    {
        "id": 9,
        "question": "Innovación y Sostenibilidad a Largo Plazo. Escenario: Tu empresa puede lanzar un nuevo producto utilizando un proveedor que ofrece materiales un 30% más baratos, pero cuya producción tiene un alto impacto ambiental. Alternativamente, un proveedor de materiales reciclados y sostenibles es más caro, lo que reduciría el margen de ganancia inicial. ¿Qué decisión tomas?",
        "options": [
            {"text": "Elegir el proveedor más barato para maximizar la rentabilidad a corto plazo y cumplir los objetivos financieros del trimestre.", "scores": {"costs": 1.0, "customer_satisfaction": 0.4, "risks": 0.2, "sustainability": 0.1}},
            {"text": "Posponer el lanzamiento del producto hasta encontrar un proveedor sostenible que sea igual de barato, aunque tome más de un año.", "scores": {"costs": 0.3, "customer_satisfaction": 0.1, "risks": 0.3, "sustainability": 0.4}},
            {"text": "Elegir el proveedor sostenible, asumir el costo inicial más alto y comunicarlo activamente como una ventaja competitiva y un compromiso de la marca, atrayendo a clientes que valoran la sostenibilidad.", "scores": {"costs": 0.3, "customer_satisfaction": 0.9, "risks": 0.7, "sustainability": 1.0}},
            {"text": "Realizar una prueba de mercado con dos versiones del producto, una barata y otra sostenible, para que el cliente decida.", "scores": {"costs": 0.2, "customer_satisfaction": 0.3, "risks": 0.2, "sustainability": 0.2}}
        ]
    },
    {
        "id": 10,
        "question": "Adopción de Herramientas y Prácticas. Escenario: La empresa acaba de invertir en un software de colaboración muy potente para que los equipos compartan conocimiento. Sin embargo, después de un mes, casi nadie lo usa; los empleados siguen prefiriendo el correo electrónico y las reuniones. ¿Cuál es la intervención más efectiva?",
        "options": [
            {"text": "Enviar un comunicado obligatorio de la alta dirección exigiendo que todo el conocimiento se comparta exclusivamente a través de la nueva herramienta.", "scores": {"costs": 0.7, "customer_satisfaction": 0.2, "risks": 0.3, "sustainability": 0.1}},
            {"text": "Organizar más sesiones de capacitación técnica sobre cómo usar todas las funcionalidades del software.", "scores": {"costs": 0.5, "customer_satisfaction": 0.4, "risks": 0.5, "sustainability": 0.4}},
            {"text": "Identificar 'campeones' o líderes informales en varios equipos, formarlos a ellos primero y pedirles que lideren con el ejemplo, mostrando a sus colegas cómo la herramienta resuelve problemas reales de su día a día.", "scores": {"costs": 0.8, "customer_satisfaction": 0.9, "risks": 0.9, "sustainability": 1.0}},
            {"text": "Ofrecer un incentivo económico (bono) a los 10 empleados que más usen la plataforma cada mes.", "scores": {"costs": 0.4, "customer_satisfaction": 0.3, "risks": 0.3, "sustainability": 0.2}}
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


def generate_playbook(scores):
    """Genera un playbook personalizado basado en la categoría con el puntaje más bajo."""
    
    min_category = min(scores, key=scores.get)
    
    playbook = {
        "area_mejora": "",
        "procesos": [],
        "roles": [],
        "metricas": [],
        "herramientas": []
    }

    if min_category == 'costs':
        playbook['area_mejora'] = "Optimización de Costos en Innovación"
        playbook['procesos'] = [
            "Implementar un 'Lean Canvas' para cada nueva idea, para evaluar su viabilidad financiera desde el inicio.",
            "Adoptar un enfoque de 'presupuesto por etapas' (stage-gate funding), donde los fondos se liberan a medida que el proyecto demuestra su valor y reduce la incertidumbre."
        ]
        playbook['roles'] = [
            "**Analista Financiero de Innovación:** Un rol dedicado a evaluar el impacto financiero de los proyectos y a optimizar la asignación de recursos.",
            "**Líder de Proyecto con Enfoque en Eficiencia:** Responsable de mantener el proyecto dentro del presupuesto sin sacrificar la calidad."
        ]
        playbook['metricas'] = [
            "**ROI de Innovación:** Medir el retorno de la inversión de los proyectos completados.",
            "**Tasa de Quema (Burn Rate):** Monitorear el ritmo al que los proyectos consumen su presupuesto."
        ]
        playbook['herramientas'] = [
            "**Software de Gestión de Proyectos (Jira, Asana):** Para un seguimiento detallado de los recursos y el tiempo.",
            "**Plataformas de Simulación Financiera:** Para modelar los posibles resultados económicos de un proyecto."
        ]
    elif min_category == 'customer_satisfaction':
        playbook['area_mejora'] = "Innovación Centrada en el Cliente"
        playbook['procesos'] = [
            "Establecer un ciclo de 'feedback' continuo con los clientes a través de entrevistas, encuestas y pruebas de usabilidad en cada fase del desarrollo.",
            "Utilizar 'Design Thinking' como metodología principal para asegurar que las soluciones respondan a necesidades reales del usuario."
        ]
        playbook['roles'] = [
            "**Investigador de Experiencia de Usuario (UX Researcher):** Dedicado a entender las necesidades y comportamientos del cliente.",
            "**Product Manager Orientado al Cliente:** Actúa como la voz del cliente dentro del equipo, asegurando que sus necesidades sean la máxima prioridad."
        ]
        playbook['metricas'] = [
            "**Net Promoter Score (NPS):** Medir la lealtad y satisfacción del cliente con las nuevas soluciones.",
            "**Customer Effort Score (CES):** Evaluar cuánto esfuerzo le toma a un cliente utilizar el nuevo producto o servicio."
        ]
        playbook['herramientas'] = [
            "**Plataformas de Encuestas (SurveyMonkey, Typeform):** Para recopilar feedback de manera estructurada.",
            "**Herramientas de Prototipado (Figma, Sketch):** Para crear y probar versiones tempranas de las soluciones con usuarios reales."
        ]
    elif min_category == 'risks':
        playbook['area_mejora'] = "Gestión de Riesgos e Incertidumbre"
        playbook['procesos'] = [
            "Crear una 'matriz de riesgos' para cada proyecto, identificando riesgos potenciales y planes de mitigación.",
            "Fomentar una cultura de 'experimentación segura', donde los fracasos a pequeña escala se vean como oportunidades de aprendizaje y no como errores."
        ]
        playbook['roles'] = [
            "**Gestor de Riesgos de Innovación:** Responsable de identificar, evaluar y monitorear los riesgos en todo el portafolio de innovación.",
            "**Equipo de Prototipado Rápido:** Un equipo multifuncional capaz de construir y probar ideas de bajo costo para validar supuestos clave rápidamente."
        ]
        playbook['metricas'] = [
            "**Número de Supuestos Validados/Invalidados:** Medir el progreso en la reducción de la incertidumbre del proyecto.",
            "**Tiempo para Aprender (Time-to-learn):** Medir cuán rápido el equipo puede obtener aprendizajes clave de un experimento."
        ]
        playbook['herramientas'] = [
            "**Análisis FODA (Fortalezas, Oportunidades, Debilidades, Amenazas):** Un marco simple para la evaluación estratégica de riesgos.",
            "**Plataformas de A/B Testing:** Para probar diferentes versiones de una solución y tomar decisiones basadas en datos."
        ]
    else:  # Sostenibilidad
        playbook['area_mejora'] = "Sostenibilidad e Impacto a Largo Plazo"
        playbook['procesos'] = [
            "Integrar criterios de sostenibilidad (ambientales, sociales y de gobernanza - ESG) en el proceso de selección y evaluación de ideas.",
            "Realizar un 'Análisis de Ciclo de Vida' para los nuevos productos, evaluando su impacto desde la creación hasta el desecho."
        ]
        playbook['roles'] = [
            "**Líder de Innovación Sostenible:** Asegura que los objetivos de sostenibilidad estén alineados con la estrategia de innovación.",
            "**Comité de Ética e Impacto:** Un grupo diverso que revisa los proyectos para garantizar que cumplan con los estándares éticos y de impacto social de la empresa."
        ]
        playbook['metricas'] = [
            "**Huella de Carbono del Producto:** Medir el impacto ambiental de las nuevas innovaciones.",
            "**Índice de Impacto Social:** Evaluar cómo los proyectos contribuyen positivamente a la comunidad o a la sociedad."
        ]
        playbook['herramientas'] = [
            "**Marcos de Sostenibilidad (ej. Objetivos de Desarrollo Sostenible de la ONU):** Para guiar la dirección estratégica de la innovación.",
            "**Software de Medición de Huella de Carbono:** Para cuantificar el impacto ambiental."
        ]

    return playbook

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
                question = questions[question_id]
                # La respuesta "correcta" es la que tiene la suma más alta de puntuaciones
                correct_option = max(question['options'], key=lambda opt: sum(opt['scores'].values()))
                return jsonify({
                    'success': True, 
                    'correct_answer': correct_option['text'] if correct_option else ''
                })
            
            elif power_id == 'fifty':
                question = questions[question_id]
                # Ordenar opciones por la suma de sus puntuaciones (de peor a mejor)
                sorted_options = sorted(question['options'], key=lambda opt: sum(opt['scores'].values()))
                # Las dos peores opciones son las que se eliminarán
                to_remove = sorted_options[:2]
                return jsonify({
                    'success': True,
                    'remove_options': [opt['text'] for opt in to_remove]
                })
            
            elif power_id == 'double':
                return jsonify({'success': True, 'double_points': True})
            
            elif power_id == 'skip':
                session['current_question'] = session.get('current_question', 0) + 1
                return jsonify({'success': True, 'skip': True})
            
            elif power_id == 'time':
                return jsonify({'success': True, 'extra_time': 30})
    
    return jsonify({'success': False, 'error': 'Poder no disponible'})

@app.route('/results')
def show_results():
    if 'answers' not in session or len(session.get('answers', [])) < len(questions):
        return redirect(url_for('index'))
    
    # Calcular puntuación por categoría
    total_scores = {
        "costs": 0,
        "customer_satisfaction": 0,
        "risks": 0,
        "sustainability": 0
    }
    max_scores = total_scores.copy()
    powers_used = []
    
    for i, question in enumerate(questions):
        # Calcular la puntuación máxima posible para cada categoría en esta pregunta
        for category in max_scores.keys():
            max_category_score = max(opt['scores'][category] for opt in question['options'])
            max_scores[category] += max_category_score

    for answer in session['answers']:
        question = questions[answer['question_id']]
        selected_option = next((opt for opt in question['options'] if opt['text'] == answer['answer']), None)
        
        if selected_option:
            scores = selected_option['scores'].copy()
            
            # Verificar si se usó doble puntuación
            if answer.get('power_used') == 'double':
                for category in scores:
                    scores[category] *= 2
                powers_used.append('Doble puntos en pregunta ' + str(answer['question_id'] + 1))
            
            for category in total_scores:
                total_scores[category] += scores[category]

    # Calcular porcentajes
    percentages = {category: (total_scores[category] / max_scores[category]) * 100 for category in total_scores}

    normalized_scores = {category: (total_scores[category] / max_scores[category]) for category in total_scores}

    # Generar el playbook personalizado
    playbook = generate_playbook(normalized_scores)
    
    # Guardar resultado en base de datos
    if 'user_id' in session:
        result = QuizResult(
            user_id=session['user_id'],
            costs_score=normalized_scores['costs'],
            customer_satisfaction_score=normalized_scores['customer_satisfaction'],
            risks_score=normalized_scores['risks'],
            sustainability_score=normalized_scores['sustainability'],
            powers_used=', '.join(powers_used)
        )
        db.session.add(result)
        db.session.commit()
    
    return render_template('results.html', 
                         scores=total_scores, 
                         max_scores=max_scores, 
                         percentages=percentages,
                         powers_used=powers_used,
                         playbook=playbook)

if __name__ == '__main__':
    app.run(debug=True)