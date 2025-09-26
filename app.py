from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from config import Config
from database import init_db
from models import db, User, QuizResult, QuestionAttempt
import random
import json

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar base de datos
init_db(app)

# --- Preguntas y respuestas con puntuaciones por categoría ---
# (El resto de tu lista de preguntas va aquí... No es necesario cambiarla)
questions = [
    {
        "id": 1,
        "question": "La naturaleza de la innovación. Escenario: Tu equipo ha estado meses desarrollando un nuevo producto siguiendo un plan riguroso (etapa 1, etapa 2, etapa 3). De repente, un miembro junior del equipo propone una idea radicalmente diferente que surgió de una conversación informal con un cliente, pero que desvía completamente el plan original. ¿Qué haces?",
        "options": [
            {"text": "Desestimar la idea para mantener el enfoque en el plan original y cumplir con los plazos establecidos. La desviación es un riesgo inaceptable.", "scores": {"costs": 1.0, "customer_satisfaction": 0.2, "risks": 0.5, "sustainability": 0.1}},
            {"text": "Pedirle al empleado que documente la idea en un formulario de ideas para una posible revisión en el próximo ciclo de planificación, dentro de 6 meses.", "scores": {"costs": 0.9, "customer_satisfaction": 0.4, "risks": 0.6, "sustainability": 0.3}},
            {"text": "Programar una reunión de 30 minutos con el equipo y el miembro junior para escuchar la idea, evaluar rápidamente su potencial y decidir si se justifica una exploración más profunda sin comprometer el plan actual.", "scores": {"costs": 0.7, "customer_satisfaction": 0.8, "risks": 0.8, "sustainability": 0.7}},
            {"text": "Detener inmediatamente el plan actual, asignar a todo el equipo a investigar a fondo la nueva idea y crear un prototipo en una semana. Si la idea es buena, se adoptará de inmediato.", "scores": {"costs": 0.2, "customer_satisfaction": 1.0, "risks": 0.9, "sustainability": 0.9}}
        ]
    },
    {
        "id": 2,
        "question": "El problema de la innovación incremental vs. disruptiva. Escenario: Tu empresa tiene un producto estrella que genera la mayor parte de los ingresos. El equipo ha identificado una oportunidad para hacer una mejora menor (por ejemplo, 'Producto 2.0') que podría aumentar las ventas en un 10%. Simultáneamente, un pequeño grupo de ingenieros ha desarrollado un prototipo de un producto completamente nuevo que podría revolucionar el mercado, pero que también podría canibalizar tu producto estrella. ¿A cuál proyecto le asignas la mayoría de los recursos?",
        "options": [
            {"text": "Al proyecto de mejora incremental ('Producto 2.0') porque es un camino seguro y de bajo riesgo que garantiza un retorno inmediato de la inversión.", "scores": {"costs": 0.9, "customer_satisfaction": 0.5, "risks": 0.2, "sustainability": 0.4}},
            {"text": "Al proyecto disruptivo, porque el potencial de mercado es mucho mayor y, aunque el riesgo es alto, el crecimiento a largo plazo justifica la apuesta.", "scores": {"costs": 0.3, "customer_satisfaction": 0.9, "risks": 0.9, "sustainability": 0.8}},
            {"text": "Dividir los recursos equitativamente entre ambos proyectos para mitigar el riesgo de fracaso, aunque esto podría ralentizar el progreso en ambos frentes.", "scores": {"costs": 0.6, "customer_satisfaction": 0.7, "risks": 0.7, "sustainability": 0.6}},
            {"text": "Crear un spin-off o una unidad de negocio separada para el proyecto disruptivo, para que pueda operar de manera independiente sin interferir con las operaciones del negocio principal.", "scores": {"costs": 0.7, "customer_satisfaction": 0.8, "risks": 0.5, "sustainability": 0.9}}
        ]
    },
    {
        "id": 3,
        "question": "La gestión de la ambigüedad. Escenario: Un cliente te dice que necesita 'una solución para mejorar la productividad en su oficina'. No te da más detalles. Tu equipo de I+D (Investigación y Desarrollo) quiere una especificación clara antes de empezar. ¿Cómo le das dirección al equipo?",
        "options": [
            {"text": "Le pides al cliente que te entregue un documento con los requerimientos detallados y no empiezas a trabajar hasta tenerlo.", "scores": {"costs": 0.9, "customer_satisfaction": 0.1, "risks": 0.1, "sustainability": 0.1}},
            {"text": "Asignas un equipo a la 'solución para la productividad', que se dedique a investigar y a sacar un producto a partir de su propio juicio.", "scores": {"costs": 0.5, "customer_satisfaction": 0.4, "risks": 0.8, "sustainability": 0.3}},
            {"text": "Inicias una etapa de exploración con el cliente. Realizas entrevistas, encuestas, observaciones, y creas prototipos de baja fidelidad para co-crear una solución con ellos.", "scores": {"costs": 0.3, "customer_satisfaction": 0.9, "risks": 0.2, "sustainability": 0.9}},
            {"text": "Analizas el mercado, buscas las 'mejores prácticas' y copias un producto ya existente para tu cliente.", "scores": {"costs": 0.7, "customer_satisfaction": 0.5, "risks": 0.6, "sustainability": 0.4}}
        ]
    },
    {
        "id": 4,
        "question": "La construcción de la cultura de la innovación. Escenario: Eres el gerente de una empresa de manufactura tradicional. Has notado que los empleados tienen miedo de proponer ideas nuevas por temor al fracaso o a ser criticados. ¿Qué iniciativa implementarías para fomentar la innovación y la toma de riesgos?",
        "options": [
            {"text": "Organizar un 'Hackathon' anual donde los empleados compitan para ganar un premio, pero sin darles un presupuesto o tiempo para trabajar en sus ideas durante el horario laboral.", "scores": {"costs": 0.8, "customer_satisfaction": 0.3, "risks": 0.7, "sustainability": 0.2}},
            {"text": "Implementar una política de 'Tolerancia Cero' al fracaso y despedir a los empleados cuyas ideas no resulten en un éxito comercial inmediato.", "scores": {"costs": 0.1, "customer_satisfaction": 0.1, "risks": 0.1, "sustainability": 0.1}},
            {"text": "Crear un 'Fondo de Innovación' para financiar ideas experimentales con un presupuesto pequeño, y celebrar públicamente tanto los éxitos como los aprendizajes de los fracasos, premiando la iniciativa y la experimentación.", "scores": {"costs": 0.6, "customer_satisfaction": 0.8, "risks": 0.5, "sustainability": 0.9}},
            {"text": "Contratar a consultores externos para que desarrollen todas las innovaciones, ya que los empleados actuales no tienen la capacidad para hacerlo.", "scores": {"costs": 0.4, "customer_satisfaction": 0.6, "risks": 0.9, "sustainability": 0.5}}
        ]
    },
    {
        "id": 5,
        "question": "La innovación como un viaje, no un destino. Escenario: Tu equipo ha desarrollado un nuevo prototipo de software que ha recibido comentarios muy positivos en pruebas de usuario iniciales. Sin embargo, un análisis de mercado reciente revela que el producto de un competidor, que está a punto de ser lanzado, ofrece una funcionalidad superior en un área clave. ¿Qué decisión tomas?",
        "options": [
            {"text": "Lanzar tu producto de inmediato para no perder la oportunidad, asumiendo que tu prototipo es lo suficientemente bueno.", "scores": {"costs": 0.8, "customer_satisfaction": 0.5, "risks": 0.7, "sustainability": 0.6}},
            {"text": "Retirar el producto del mercado, considerar el proyecto un fracaso y desmantelar el equipo.", "scores": {"costs": 0.1, "customer_satisfaction": 0.1, "risks": 0.1, "sustainability": 0.1}},
            {"text": "Analizar la funcionalidad del competidor y pausar tu lanzamiento para integrarla, aún si esto retrasa el proyecto por 6 meses más.", "scores": {"costs": 0.3, "customer_satisfaction": 0.3, "risks": 0.8, "sustainability": 0.4}},
            {"text": "Lanzar el producto con un 'producto mínimo viable' (MVP), mientras que se sigue investigando el producto del competidor y se planea una siguiente versión que supere sus funcionalidades clave.", "scores": {"costs": 0.5, "customer_satisfaction": 0.9, "risks": 0.6, "sustainability": 0.9}}
        ]
    },
    {
        "id": 6,
        "question": "Los catalizadores de la innovación. Escenario: Eres el líder de un equipo de diseño. Tu equipo está bloqueado en una etapa de 'ideación' y no consiguen generar nuevas ideas. Han pasado semanas y no hay ningún avance. ¿Qué haces?",
        "options": [
            {"text": "Le pides a tu equipo que se queden en sus puestos de trabajo hasta que generen una idea, e implementas la regla de 'No-distracciones' para que se enfoquen en su trabajo.", "scores": {"costs": 0.6, "customer_satisfaction": 0.1, "risks": 0.3, "sustainability": 0.2}},
            {"text": "Los mandas a casa por el día para que descansen y regresen al otro día a seguir intentando.", "scores": {"costs": 0.8, "customer_satisfaction": 0.3, "risks": 0.5, "sustainability": 0.6}},
            {"text": "Les das un presupuesto y una tarde libre para ir a visitar museos, parques, galerías de arte, y que hagan un ejercicio de 'brainstorming' en un ambiente completamente diferente.", "scores": {"costs": 0.5, "customer_satisfaction": 0.9, "risks": 0.8, "sustainability": 0.9}},
            {"text": "Contratas a un consultor externo para que les diga qué hacer, a pesar de que el consultor no tiene el conocimiento de la organización que tiene tu equipo.", "scores": {"costs": 0.2, "customer_satisfaction": 0.7, "risks": 0.9, "sustainability": 0.5}}
        ]
    },
    {
        "id": 7,
        "question": "El problema de la innovación en grandes empresas. Escenario: Tu gran empresa, líder en el mercado de bebidas, ha notado que las startups de bebidas energéticas están ganando terreno con productos más saludables y envases ecológicos. Sin embargo, los procesos internos para aprobar un nuevo producto son lentos y requieren múltiples aprobaciones de distintos departamentos (marketing, producción, legal). ¿Cómo podrías acelerar el proceso de innovación para competir con las startups?",
        "options": [
            {"text": "Continuar con el proceso actual, confiando en que la marca establecida y la lealtad del cliente son suficientes para mantener la cuota de mercado.", "scores": {"costs": 0.1, "customer_satisfaction": 0.1, "risks": 0.1, "sustainability": 0.1}},
            {"text": "Crear un 'laboratorio de innovación' o 'equipo de proyectos especiales' con autonomía para tomar decisiones, un presupuesto dedicado, y la capacidad de lanzar productos de forma rápida y experimental, sin tener que seguir todos los procesos burocráticos del negocio principal.", "scores": {"costs": 0.9, "customer_satisfaction": 0.9, "risks": 0.9, "sustainability": 0.9}},
            {"text": "Esperar a que una de las startups se vuelva muy exitosa y luego intentar comprarla, en lugar de desarrollar un producto propio.", "scores": {"costs": 0.4, "customer_satisfaction": 0.5, "risks": 0.7, "sustainability": 0.5}},
            {"text": "Lanzar un 'copycat' de la bebida de la startup sin investigar por qué su modelo de negocio está funcionando, confiando en la marca ya establecida.", "scores": {"costs": 0.7, "customer_satisfaction": 0.2, "risks": 0.8, "sustainability": 0.4}}
        ]
    },
    {
        "id": 8,
        "question": "La visión como motor de la innovación. Escenario: Como líder, tienes una visión audaz para el futuro de tu producto: 'Ser el asistente digital personal más intuitivo del mundo'. ¿Qué estrategia usarías para asegurar que todos los miembros de tu equipo, desde ingenieros hasta diseñadores, se alineen y trabajen hacia esta visión, incluso si sus tareas diarias parecen ser solo una pequeña parte del gran panorama?",
        "options": [
            {"text": "Crear un documento de visión muy detallado y enviarlo por correo electrónico a todos, asumiendo que lo leerán y entenderán.", "scores": {"costs": 0.1, "customer_satisfaction": 0.2, "risks": 0.1, "sustainability": 0.1}},
            {"text": "Mantener la visión solo para el equipo de liderazgo y no compartirla con los miembros del equipo para evitar distracciones.", "scores": {"costs": 0.2, "customer_satisfaction": 0.1, "risks": 0.2, "sustainability": 0.3}},
            {"text": "Organizar reuniones regulares donde se comparta el progreso hacia la visión y se muestren 'demos' de los productos, para que todos puedan ver el impacto de su trabajo en el panorama general. Esto genera un sentido de pertenencia y se pueden identificar oportunidades de colaboración.", "scores": {"costs": 0.9, "customer_satisfaction": 0.9, "risks": 0.9, "sustainability": 0.9}},
            {"text": "Ofrecer un bono monetario a cada empleado que ayude a la empresa a conseguir su visión a futuro.", "scores": {"costs": 0.7, "customer_satisfaction": 0.5, "risks": 0.6, "sustainability": 0.4}}
        ]
    },
    {
        "id": 9,
        "question": "La estrategia de innovación. Escenario: Has identificado una nueva tendencia en el mercado de la alimentación saludable: las 'proteínas de insectos'. Tu equipo ha desarrollado un prototipo de una barra energética de insectos que sabe bien, es nutritiva y sostenible. ¿Qué haces ahora?",
        "options": [
            {"text": "Lanzas la barra inmediatamente al mercado sin hacer un 'análisis de riesgos' o una 'validación con clientes' para no perder tiempo.", "scores": {"costs": 0.4, "customer_satisfaction": 0.4, "risks": 0.7, "sustainability": 0.6}},
            {"text": "Organizas una campaña de crowdfunding para validar si hay interés en el producto. Si la campaña es exitosa, usas los fondos para financiar el lanzamiento a mayor escala.", "scores": {"costs": 0.8, "customer_satisfaction": 0.9, "risks": 0.8, "sustainability": 0.9}},
            {"text": "Le pides a tu equipo de desarrollo que 'esconda' el producto hasta que no haya ninguna empresa en el mercado con un producto similar, para que la tuya sea la primera.", "scores": {"costs": 0.3, "customer_satisfaction": 0.6, "risks": 0.5, "sustainability": 0.2}},
            {"text": "Lanzas el producto de forma limitada en una sola tienda, para que te des cuenta de si el producto tiene demanda, y luego sacas el producto de forma masiva en todas las tiendas. ", "scores": {"costs": 0.5, "customer_satisfaction": 0.8, "risks": 0.6, "sustainability": 0.8}}
        ]
    },
    {
        "id": 10,
        "question": "La protección de la propiedad intelectual. Escenario: Tu equipo ha desarrollado una tecnología revolucionaria que podría darle una ventaja competitiva masiva. Te preocupas de que un competidor pueda copiar tu invención y lanzar un producto similar. ¿Qué haces?",
        "options": [
            {"text": "No le dices a nadie del nuevo desarrollo. Lo mantienes en secreto dentro de tu equipo para evitar que te lo roben.", "scores": {"costs": 0.2, "customer_satisfaction": 0.3, "risks": 0.8, "sustainability": 0.4}},
            {"text": "Publicas un artículo científico sobre el nuevo desarrollo para que el mundo conozca tu desarrollo. Esto evita que alguien más pueda patentarlo.", "scores": {"costs": 0.6, "customer_satisfaction": 0.5, "risks": 0.7, "sustainability": 0.5}},
            {"text": "Patentas el desarrollo para tener derechos exclusivos sobre la invención por un periodo de tiempo. Esto te permite comercializar el producto o licenciar la patente.", "scores": {"costs": 0.9, "customer_satisfaction": 0.9, "risks": 0.9, "sustainability": 0.9}},
            {"text": "Intentas vender el desarrollo a la mayor cantidad de empresas posible sin patentar nada.", "scores": {"costs": 0.7, "customer_satisfaction": 0.8, "risks": 0.6, "sustainability": 0.7}}
        ]
    },
]

# Diccionario para buscar preguntas por ID
questions_by_id = {q['id']: q for q in questions}

# Playbook de Innovación
def generate_playbook(scores):
    areas = {
        "costs": scores["costs"],
        "customer_satisfaction": scores["customer_satisfaction"],
        "risks": scores["risks"],
        "sustainability": scores["sustainability"]
    }
    
    mejoras_sugeridas = {
        "costs": {
            "area_mejora": "Gestión de Costos y Eficiencia",
            "procesos": [
                "Implementar un proceso de validación rápida de ideas, utilizando prototipos de baja fidelidad y pruebas de concepto para minimizar la inversión inicial.",
                "Adoptar metodologías ágiles (Scrum, Kanban) para reducir el desperdicio y optimizar el uso de recursos.",
                "Realizar análisis de retorno de inversión (ROI) en las etapas tempranas del proyecto para priorizar las iniciativas más rentables."
            ],
            "roles": [
                "Un <strong>Gerente de Producto o Project Manager</strong> que priorice funcionalidades y gestione el presupuesto eficientemente.",
                "Un <strong>Analista de Negocios</strong> que evalúe la viabilidad financiera de las ideas.",
                "Un <strong>Ingeniero de Software</strong> que se enfoque en la arquitectura del producto para optimizar la eficiencia y los recursos."
            ],
            "metricas": [
                "ROI (Retorno sobre la Inversión) de proyectos de innovación.",
                "Costo de la 'falla' o del prototipo.",
                "Tiempo del 'ciclo de innovación' (desde la ideación hasta el lanzamiento)."
            ],
            "herramientas": [
                "Herramientas de gestión de proyectos como Jira o Trello.",
                "Análisis de costos y hojas de cálculo.",
                "Herramientas de 'Business Model Canvas' para estructurar y validar ideas de negocio."
            ]
        },
        "customer_satisfaction": {
            "area_mejora": "Enfoque en el Cliente y la Satisfacción",
            "procesos": [
                "Adoptar un enfoque de 'Design Thinking' para entender profundamente las necesidades del usuario y generar soluciones centradas en él.",
                "Crear un 'Customer Journey Map' para identificar los puntos de dolor y las oportunidades de innovación a lo largo de la experiencia del cliente.",
                "Implementar 'bucles de retroalimentación' (feedback loops) para recolectar opiniones de los usuarios de manera continua y rápida, utilizando encuestas y entrevistas."
            ],
            "roles": [
                "Un <strong>Investigador de UX</strong> (Experiencia de Usuario) que identifique las necesidades de los usuarios y las comunique al equipo de forma efectiva.",
                "Un <strong>Estratega de Contenido</strong> que se asegure de que las soluciones sean fáciles de entender.",
                "Un <strong>Gerente de Producto</strong> que priorice las funcionalidades que impactarán directamente la experiencia del cliente."
            ],
            "metricas": [
                "NPS (Net Promoter Score) para medir la lealtad del cliente.",
                "CSAT (Customer Satisfaction Score) para medir la satisfacción del cliente.",
                "Número de usuarios que usan una nueva funcionalidad."
            ],
            "herramientas": [
                "Herramientas de encuestas como Typeform o SurveyMonkey.",
                "Mapas de empatía para visualizar las necesidades de los usuarios.",
                "Herramientas de prototipado como Figma o Sketch."
            ]
        },
        "risks": {
            "area_mejora": "Gestión de Riesgos y Experimentación",
            "procesos": [
                "Adoptar una mentalidad de 'fallar rápido y fallar barato', para aprender de los errores y no perder tiempo en proyectos con poca probabilidad de éxito.",
                "Realizar 'pruebas A/B' para validar hipótesis antes de lanzar un producto a gran escala.",
                "Implementar un 'análisis de riesgos' en las etapas iniciales de cada proyecto para identificar y mitigar posibles problemas."
            ],
            "roles": [
                "Un <strong>Ingeniero de Calidad</strong> que se enfoque en las pruebas de los productos para reducir el riesgo de fallas.",
                "Un <strong>Gerente de Riesgos</strong> que evalúe y mitigue los riesgos asociados a los proyectos de innovación.",
                "Un <strong>Analista de Datos</strong> que se asegure de que la toma de decisiones se base en evidencia."
            ],
            "metricas": [
                "Porcentaje de proyectos que se completan sin mayores desviaciones de su alcance y presupuesto.",
                "Número de errores críticos encontrados antes del lanzamiento.",
                "Tiempo que toma identificar un riesgo clave."
            ],
            "herramientas": [
                "Matrices de riesgo para evaluar el impacto y la probabilidad de cada riesgo.",
                "Diagramas de flujo para visualizar los procesos y posibles fallos.",
                "Herramientas de 'Business Case' para justificar las inversiones en innovación."
            ]
        },
        "sustainability": {
            "area_mejora": "Innovación Sostenible y Estratégica",
            "procesos": [
                "Integrar la innovación en la estrategia general de la empresa, alineando los proyectos con los objetivos a largo plazo.",
                "Crear un 'equipo de innovación' o 'laboratorio de innovación' que se dedique exclusivamente a explorar nuevas tecnologías y modelos de negocio.",
                "Implementar 'círculos de innovación' o 'sesiones de ideación' donde los empleados de distintos departamentos colaboren en la generación de ideas para la empresa."
            ],
            "roles": [
                "Un <strong>Estratega de Innovación</strong> que se encargue de identificar oportunidades a largo plazo para la empresa.",
                "Un <strong>Líder de Equipo</strong> que fomente una cultura de colaboración y experimentación.",
                "Un <strong>Analista de Tendencias</strong> que se anticipe a los cambios en el mercado."
            ],
            "metricas": [
                "Número de patentes o propiedad intelectual creada.",
                "Porcentaje de ingresos que proviene de nuevos productos o servicios.",
                "Tasa de retención de empleados que se sienten motivados a innovar."
            ],
            "herramientas": [
                "Análisis de la industria y la competencia.",
                "Plataformas de gestión de ideas (idea management).",
                "Herramientas de planeación estratégica como PESTLE o FODA."
            ]
        }
    }
    
    # Encontrar el área con el puntaje más bajo
    area_mejora = min(areas, key=areas.get)
    return mejoras_sugeridas.get(area_mejora, {})

# Función auxiliar para inicializar la sesión del quiz
def initialize_quiz_session(user_id, total_questions):
    session['user_id'] = user_id
    session['current_question_index'] = 0
    session['answers'] = []
    session['total_questions'] = total_questions
    session['retake_mode'] = False 
    session['retake_question_ids'] = [] 
    session['initial_result_id'] = None 

# HOME
@app.route('/', methods=['GET'])
def index():
    session.clear() 
    return render_template('index.html')

# INICIO DEL QUIZ
@app.route('/start', methods=['POST'])
def start_quiz():
    leader_name = request.form.get('leader_name', '').strip()
    try:
        num_participants = int(request.form.get('num_participants', 1))
    except (ValueError, TypeError):
        num_participants = 1

    if not leader_name or num_participants < 1:
        return redirect(url_for('index'))

    nickname = f"{leader_name.replace(' ', '_').lower()}_{num_participants}"
    
    user = User.query.filter_by(nickname=nickname).first()
    if user is None:
        user = User(nickname=nickname, leader_name=leader_name, num_participants=num_participants)
        db.session.add(user)
        db.session.commit()
    
    initialize_quiz_session(user.id, len(questions))
    
    return redirect(url_for('quiz', q_index=1))

# QUIZ
@app.route('/quiz/<int:q_index>', methods=['GET'])
def quiz(q_index):
    if 'user_id' not in session:
        return redirect(url_for('index'))

    is_retake = session.get('retake_mode', False)
    
    if is_retake:
        retake_q_ids = session.get('retake_question_ids', [])
        total_questions = len(retake_q_ids)
        if 0 <= (q_index - 1) < total_questions:
            question_id = retake_q_ids[q_index - 1]
            question = questions_by_id.get(question_id)
        else:
            return redirect(url_for('calculate_results'))
    else:
        total_questions = len(questions)
        if 0 <= (q_index - 1) < total_questions:
            question = questions[q_index - 1]
        else:
            return redirect(url_for('calculate_results'))
    
    session['current_question_index'] = q_index - 1 
    
    return render_template('quiz.html', 
                           question=question, 
                           current=q_index, 
                           total=total_questions)

# RESPUESTA
@app.route('/answer', methods=['POST'])
def answer():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Sesión no iniciada'}), 400

    data = request.get_json()
    selected_answer_text = data.get('answer')
    
    is_retake = session.get('retake_mode', False)
    q_index = session.get('current_question_index', 0)
    
    if is_retake:
        retake_q_ids = session.get('retake_question_ids', [])
        question_id = retake_q_ids[q_index]
        current_question = questions_by_id.get(question_id)
        total_q = len(retake_q_ids)
    else:
        current_question = questions[q_index]
        question_id = current_question['id']
        total_q = len(questions)

    if not current_question:
        return jsonify({'success': False, 'error': 'Pregunta no encontrada'}), 404

    selected_option = next((opt for opt in current_question['options'] if opt['text'] == selected_answer_text), None)
    
    if not selected_option:
        return jsonify({'success': False, 'error': 'Opción no válida'}), 400

    scores = selected_option['scores']
    
    question_score_details = {
        'question_id': question_id,
        'answer': selected_answer_text,
        'scores': scores,
        'total_score': sum(scores.values()) 
    }
    
    # Usamos session.modified = True para asegurar que el cambio en la lista se guarde
    session.setdefault('answers', []).append(question_score_details)
    session.modified = True
    
    next_index = q_index + 1
    
    if next_index < total_q:
        next_url = url_for('quiz', q_index=next_index + 1)
    else:
        next_url = url_for('calculate_results')
        
    return jsonify({'success': True, 'next_url': next_url})

# CÁLCULO DE RESULTADOS (MODIFICADO Y CORREGIDO)
@app.route('/results', methods=['GET'])
def calculate_results():
    if 'user_id' not in session or not session.get('answers'):
        return redirect(url_for('index'))

    user_id = session['user_id']
    is_retake = session.get('retake_mode', False)
    answers = session['answers']
    
    # Puntaje máximo posible para cada categoría (10 preguntas * 1.0 máx por pregunta)
    max_scores = {'costs': 10.0, 'customer_satisfaction': 10.0, 'risks': 10.0, 'sustainability': 10.0} 

    if not is_retake:
        # --- LÓGICA PARA EL PRIMER INTENTO ---
        
        total_scores = {'costs': 0.0, 'customer_satisfaction': 0.0, 'risks': 0.0, 'sustainability': 0.0}
        all_question_attempts = []
        
        for answer in answers:
            scores = answer['scores']
            for category in total_scores:
                total_scores[category] += scores.get(category, 0.0)

            all_question_attempts.append({
                'question_id': answer['question_id'],
                'total_score': answer['total_score'],
                'scores': scores,
                'answer': answer['answer']
            })
            
        # Guardar el resultado inicial en la base de datos
        result = QuizResult(
            user_id=user_id,
            costs_score_initial=total_scores['costs'],
            customer_satisfaction_score_initial=total_scores['customer_satisfaction'],
            risks_score_initial=total_scores['risks'],
            sustainability_score_initial=total_scores['sustainability'],
            total_score_initial=sum(total_scores.values()),
        )
        db.session.add(result)
        db.session.flush()  # Para obtener el ID del resultado antes de commit

        for attempt_data in all_question_attempts:
            db.session.add(QuestionAttempt(
                result_id=result.id,
                question_id=attempt_data['question_id'],
                is_retake=False,
                costs_score=attempt_data['scores']['costs'],
                customer_satisfaction_score=attempt_data['scores']['customer_satisfaction'],
                risks_score=attempt_data['scores']['risks'],
                sustainability_score=attempt_data['scores']['sustainability'],
                total_score=attempt_data['total_score'],
                selected_answer=attempt_data['answer']
            ))

        db.session.commit()

        # Preparar datos para la plantilla
        normalized_scores = {cat: (total_scores[cat] / max_scores[cat]) for cat in total_scores}
        playbook = generate_playbook(normalized_scores)
        
        low_score_attempts = sorted(all_question_attempts, key=lambda x: x['total_score'])[:5]
        retake_question_ids = [attempt['question_id'] for attempt in low_score_attempts]
        
        low_score_questions_info = [
            {'id': q_id, 'question_title': questions_by_id.get(q_id, {}).get('question', 'Pregunta desconocida')}
            for q_id in retake_question_ids
        ]

        session['retake_question_ids'] = retake_question_ids
        session['initial_result_id'] = result.id
        
        return render_template('results.html', 
                             scores=total_scores, 
                             max_scores=max_scores, 
                             percentages=normalized_scores, 
                             playbook=playbook,
                             low_score_questions=low_score_questions_info,
                             is_retake=False,
                             total_score=sum(total_scores.values()))
    else:
        # --- LÓGICA CORREGIDA PARA EL SEGUNDO INTENTO (RETAKE) ---
        initial_result_id = session.get('initial_result_id')
        if not initial_result_id:
            return redirect(url_for('index'))

        result_initial = QuizResult.query.get(initial_result_id)
        if not result_initial:
            return redirect(url_for('index'))

        # Obtener los 10 intentos originales de la BD
        initial_attempts = QuestionAttempt.query.filter_by(result_id=initial_result_id, is_retake=False).all()
        retake_question_ids = session.get('retake_question_ids', [])
        
        # Separar los 5 mejores intentos originales (los que no se repitieron)
        kept_initial_attempts = [att for att in initial_attempts if att.question_id not in retake_question_ids]
        
        # Calcular el puntaje final combinando los mejores 5 originales y los 5 nuevos
        final_scores = {'costs': 0.0, 'customer_satisfaction': 0.0, 'risks': 0.0, 'sustainability': 0.0}
        
        # Sumar los puntajes de los 5 mejores intentos originales
        for attempt in kept_initial_attempts:
            final_scores['costs'] += attempt.costs_score
            final_scores['customer_satisfaction'] += attempt.customer_satisfaction_score
            final_scores['risks'] += attempt.risks_score
            final_scores['sustainability'] += attempt.sustainability_score
            
        # Sumar los puntajes de los 5 nuevos intentos del retake y guardarlos
        for attempt_data in answers:
            final_scores['costs'] += attempt_data['scores']['costs']
            final_scores['customer_satisfaction'] += attempt_data['scores']['customer_satisfaction']
            final_scores['risks'] += attempt_data['scores']['risks']
            final_scores['sustainability'] += attempt_data['scores']['sustainability']
            
            # Guardar el intento del retake en la BD
            db.session.add(QuestionAttempt(
                result_id=result_initial.id,
                question_id=attempt_data['question_id'],
                is_retake=True,
                costs_score=attempt_data['scores']['costs'],
                customer_satisfaction_score=attempt_data['scores']['customer_satisfaction'],
                risks_score=attempt_data['scores']['risks'],
                sustainability_score=attempt_data['scores']['sustainability'],
                total_score=attempt_data['total_score'],
                selected_answer=attempt_data['answer']
            ))

        # Actualizar el registro original con los puntajes finales del retake
        result_initial.costs_score_retake = final_scores['costs']
        result_initial.customer_satisfaction_score_retake = final_scores['customer_satisfaction']
        result_initial.risks_score_retake = final_scores['risks']
        result_initial.sustainability_score_retake = final_scores['sustainability']
        result_initial.total_score_retake = sum(final_scores.values())
        
        db.session.commit()
        
        # Preparar datos para la plantilla
        retake_data = {
            'initial_total': result_initial.total_score_initial,
            'retake_total': result_initial.total_score_retake,
        }
        
        normalized_scores = {cat: (final_scores[cat] / max_scores[cat]) for cat in final_scores}
        
        session.clear()

        return render_template('results.html', 
                             scores=final_scores,
                             max_scores=max_scores, 
                             percentages=normalized_scores,
                             is_retake=True, 
                             retake_data=retake_data,
                             total_score=sum(final_scores.values()))

# RUTA PARA EMPEZAR EL RETAKE
@app.route('/start_retake', methods=['POST'])
def start_retake():
    if 'user_id' not in session or not session.get('retake_question_ids'):
        return redirect(url_for('index'))
    
    session['current_question_index'] = 0
    session['answers'] = []
    session['retake_mode'] = True 
    
    return redirect(url_for('quiz', q_index=1))
    
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')