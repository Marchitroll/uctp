"""
generador_dataset.py
Genera los archivos CSV correspondientes al esquema relacional para el problema de programación de horarios universitarios (UCTP).
Las asignaturas obligatorias provienen del plan de estudios real (Nivel 03 al Nivel 10).
Las asignaturas electivas se asignan a los niveles en los cuales resultan elegibles de acuerdo con la estructura de prerrequisitos establecida.
"""

import csv
import json
import random
import os

# ============================================================================
# MALLA CURRICULAR OBLIGATORIA (Niveles del 03 al 10)
# Define la estructura de asignaturas obligatorias por cada nivel académico.
# Estructura de la tupla: (id_curso, nombre, requisitos_infraestructura)
# ============================================================================

MALLA_OBLIGATORIA = {
    'Nivel_03': [
        ('IA_Aplicada', 'Inteligencia Artificial Aplicada', 'mesa,pc'),
        ('Calculo_II', 'Calculo II', 'mesa'),
        ('Sist_Organizacionales', 'Sistemas Organizacionales', 'mesa'),
        ('Fisica_Sistemas', 'Fisica para Sistemas', 'mesa'),
        ('Estr_Discretas', 'Estructuras Discretas de Computacion', 'mesa'),
        ('Intro_Programacion', 'Introduccion a la Programacion', 'mesa,pc'),
    ],
    'Nivel_04': [
        ('Estadistica_Prob', 'Estadistica y Probabilidad', 'mesa'),
        ('Calculo_III', 'Calculo III', 'mesa'),
        ('Mod_Integracion', 'Modelacion e Integracion de Sistemas', 'mesa,pc'),
        ('Costeo_Operaciones', 'Costeo de Operaciones', 'mesa'),
        ('POO', 'Programacion Orientada a Objetos', 'mesa,pc'),
        ('Arq_Computadoras', 'Arquitectura de Computadoras', 'mesa,pc'),
    ],
    'Nivel_05': [
        ('Estadistica_Aplicada', 'Estadistica Aplicada', 'mesa'),
        ('IO_I', 'Investigacion de Operaciones I', 'mesa'),
        ('Sist_Operativos', 'Sistemas Operativos', 'mesa,pc'),
        ('Competencias_Gerenciales', 'Desarrollo de Competencias Gerenciales', 'mesa'),
        ('ED_I', 'Estructuras de Datos I', 'mesa,pc'),
        ('Mod_BD', 'Modelamiento de Base de Datos', 'mesa,pc'),
    ],
    'Nivel_06': [
        ('Ing_Procesos_Negocio', 'Ingenieria de Procesos de Negocio', 'mesa'),
        ('Redes', 'Redes de Computadoras', 'mesa,pc'),
        ('Simulacion', 'Simulacion', 'mesa,pc'),
        ('ED_II', 'Estructuras de Datos II', 'mesa,pc'),
        ('Prog_Web', 'Programacion Web', 'mesa,pc'),
        ('Gestion_Financiera', 'Gestion Financiera', 'mesa'),
    ],
    'Nivel_07': [
        ('Sist_Intel_Empresarial', 'Sistemas de Inteligencia Empresarial', 'mesa,pc'),
        ('Gestion_Operaciones', 'Gestion de Operaciones', 'mesa'),
        ('Ing_Software_I', 'Ingenieria de Software I', 'mesa,pc'),
        ('Machine_Learning', 'Aprendizaje de Maquina', 'mesa,pc'),
        ('Ciberseguridad', 'Ciberseguridad', 'mesa,pc'),
    ],
    'Nivel_08': [
        ('Propuesta_Investigacion', 'Propuesta de Investigacion', 'mesa'),
        ('Sist_ERP', 'Sistemas ERP', 'mesa,pc'),
        ('Auditoria_Control', 'Auditoria y Control de Sistemas', 'mesa'),
        ('Ing_Software_II', 'Ingenieria de Software II', 'mesa,pc'),
    ],
    'Nivel_09': [
        ('Seminario_I', 'Seminario de Investigacion I', 'mesa'),
        ('Plan_Estrategico', 'Planeamiento Estrategico', 'mesa'),
        ('Gestion_Proyectos', 'Gestion de Proyectos', 'mesa'),
        ('Seg_Sistemas', 'Seguridad de Sistemas', 'mesa,pc'),
    ],
    'Nivel_10': [
        ('Seminario_II', 'Seminario de Investigacion II', 'mesa'),
        ('Gestion_Servicios_Dig', 'Gestion de Servicios Digitales', 'mesa'),
        ('Proy_Integrador', 'Proyecto Integrador de Sistemas', 'mesa,pc'),
    ],
}

# ============================================================================
# CURSOS ELECTIVOS DE ESPECIALIDAD
# Define los cursos electivos ofertados en la institución.
# Estructura de la tupla: (id_curso, nombre, requisitos_infraestructura, nivel_minimo)
# El parámetro nivel_minimo representa el nivel académico más temprano en el que 
# un estudiante resulta elegible para cursar la asignatura.
# ============================================================================

ELECTIVOS = [
    # Asignaturas disponibles a partir del Nivel 06 (requieren haber culminado el quinto ciclo):
    ('Paradigmas_Prog', 'Paradigmas de Programacion', 'mesa,pc', 6),
    ('IoT', 'Internet de las Cosas', 'mesa,pc', 6),
    ('Gestion_BD', 'Gestion de Base de Datos', 'mesa,pc', 6),
    ('Ing_Conocimiento', 'Ingenieria del Conocimiento', 'mesa', 6),
    ('Sist_Distribuidos', 'Sistemas Distribuidos', 'mesa,pc', 6),
    ('Analitica_Negocios', 'Analitica de Negocios', 'mesa', 6),
    ('Cloud', 'Computacion en la Nube', 'mesa,pc', 6),
    ('Innovacion_Digital', 'Innovacion Digital', 'mesa', 6),
    ('Proy_Videojuegos', 'Proyecto de Videojuegos', 'mesa,pc', 6),
    ('HCI', 'Interaccion Humano Computadora', 'mesa,pc', 6),
    ('Arq_TI', 'Arquitectura de Tecnologias de la Informacion', 'mesa', 6),
    ('DevOps', 'DevOps', 'mesa,pc', 6),
    ('Arq_Software', 'Arquitectura de Software', 'mesa,pc', 6),

    # Asignaturas disponibles a partir del Nivel 07 (requieren un curso del Nivel 06 o haber culminado el sexto ciclo):
    ('Analisis_Algoritmos', 'Analisis y Diseno de Algoritmos', 'mesa,pc', 7),
    ('Redes_Avanzadas', 'Redes Avanzadas', 'mesa,pc', 7),
    ('Prog_Movil', 'Programacion Movil', 'mesa,pc', 7),
    ('Seg_Salud_Ocup', 'Seguridad Salud Ocupacional y Bienestar Organizacional', 'mesa', 7),

    # Asignaturas disponibles a partir del Nivel 08 (requieren un curso del Nivel 07):
    ('Deep_Learning', 'Deep Learning', 'mesa,pc,deep_learning', 8),
    ('Topicos_Ciberseg', 'Topicos Avanzados en Ciberseguridad', 'mesa,pc', 8),
    ('Analitica_BigData', 'Analitica con Big Data', 'mesa,pc', 8),

    # Asignaturas disponibles a partir del Nivel 09 (requieren un curso del Nivel 08):
    ('Proy_Desarrollo_SW', 'Proyecto de Desarrollo de Software', 'mesa,pc', 9),

    # Asignaturas disponibles a partir del Nivel 10 (requieren un curso del Nivel 09):
    ('Arq_Empresarial', 'Arquitectura Empresarial', 'mesa', 10),
]

# ============================================================================
# PARÁMETROS DE GENERACIÓN DEL CONJUNTO DE DATOS
# Define las constantes operativas, capacidades y límites para el generador.
# ============================================================================

SECCIONES_POR_CURSO = (1, 2)       # Rango de secciones por curso (mínimo, máximo).
EVENTOS_POR_SECCION = [2, 3]       # Valores permitidos de eventos de clase por sección.
DURACION_EVENTOS = [2, 3]          # Valores permitidos de duración en horas por evento.
NUM_PROFESORES = 50                 # Número total de profesores disponibles en la base de datos general.
NUM_SALONES_FISICOS = 100            # Número total de salones físicos en la institución.
NUM_SALONES_CON_PC = 60             # Subconjunto de salones equipados con computadoras personales.
NUM_SALONES_DEEP_LEARNING = 1       # Subconjunto de salones equipados con infraestructura para aprendizaje profundo.
CAPACIDAD_SALON_FISICO = 40        # Capacidad máxima de estudiantes admitidos en un salón físico.
CAPACIDAD_VIRTUAL = 99999          # Capacidad virtual teóricamente ilimitada para sesiones no presenciales.
LIMITE_HORAS_SEMANAL = 48          # Límite máximo de horas de carga lectiva semanal permitida para un profesor.
MIN_DIAS_PROFESOR = 4              # Número mínimo de días en los que un profesor debe tener disponibilidad.
PESOS_TURNOS = [30, 30, 40]        # Pesos para la asignación de turnos (mañana, tarde, completo).
UMBRAL_COMPLETO_FRANJAS = 8        # Cantidad de franjas por debajo de la cual se fuerza la disponibilidad completa en el día.
FRACCION_BLOQUE_TURNO = 0.7        # Proporción de la jornada que abarca un turno parcial (mañana o tarde).
LETRAS_SECCIONES = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' # Secuencia utilizada para la nomenclatura alfabética de secciones.
PROFES_PEQ_INSTANCIA = 15          # Cantidad reducida de profesores asignada para escenarios de menor escala.
SALONES_PEQ_INSTANCIA = 20         # Cantidad reducida de salones asignada para escenarios de menor escala.
RATIO_SALONES_CON_PC = 0.6         # Proporción de salones físicos que disponen de computadoras personales.
ALUMNOS_POR_SECCION = (25, 40)     # Rango de cantidad de estudiantes matriculados por sección.
CARACTERISTICAS_POSIBLES = ['mesa', 'pc', 'deep_learning'] # Características de infraestructura reconocidas por el modelo.

SEED = 50                          # Semilla para garantizar la reproducibilidad de la generación de datos.
OUTPUT_DIR = 'dataset'             # Directorio de destino para el almacenamiento de los archivos CSV generados.

# ============================================================================
# CARGA DE CONFIGURACIÓN INSTITUCIONAL
# ============================================================================

def load_config(filepath):
    """Carga los parámetros institucionales desde un archivo JSON."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

# ============================================================================
# GENERACIÓN DE DATOS
# ============================================================================

def generate_cursos(malla, electivos):
    """Extrae la totalidad de asignaturas únicas combinando los cursos obligatorios y electivos."""
    cursos = []
    vistos = set()

    # Cursos obligatorios
    for nivel, lista_cursos in malla.items():
        for id_curso, nombre, requisitos in lista_cursos:
            if id_curso not in vistos:
                vistos.add(id_curso)
                cursos.append({
                    'id_curso': id_curso,
                    'nombre': nombre,
                    'requisitos': requisitos
                })

    # Cursos electivos
    for id_curso, nombre, requisitos, _ in electivos:
        if id_curso not in vistos:
            vistos.add(id_curso)
            cursos.append({
                'id_curso': id_curso,
                'nombre': nombre,
                'requisitos': requisitos
            })

    return cursos


def generate_secciones(cursos, secciones_rango, alumnos_rango):
    """Genera las secciones académicas correspondientes a cada una de las asignaturas."""
    secciones = []
    letras = LETRAS_SECCIONES
    for curso in cursos:
        num_secciones = random.randint(*secciones_rango)
        for j in range(num_secciones):
            secciones.append({
                'id_seccion': f"{curso['id_curso']}_{letras[j]}",
                'id_curso': curso['id_curso'],
                'num_alumnos': random.randint(*alumnos_rango)
            })
    return secciones


def generate_profesores(num_profesores):
    """Genera el conjunto inicial de profesores registrados en el sistema."""
    return [
        {'id_profesor': f"Prof_{i+1}", 'nombre': f"Profesor_{i+1}"}
        for i in range(num_profesores)
    ]


def generate_eventos(secciones, profesores, eventos_rango, duraciones):
    """
    Genera los eventos de clase para cada sección académica.
    Se garantiza que se asigne el mismo docente a la totalidad de los eventos
    pertenecientes a una misma sección, y se restringe la carga horaria semanal
    acumulada por profesor para evitar condiciones de infactibilidad.
    """
    eventos = []
    id_evento = 1
    
    # Registra la carga horaria acumulada por cada docente
    horas_prof = {p['id_profesor']: 0 for p in profesores}

    for seccion in secciones:
        num_eventos = random.randint(*eventos_rango)
        # Determina las duraciones aleatorias para los eventos de la sección
        duraciones_seccion = [random.choice(duraciones) for _ in range(num_eventos)]
        total_horas_seccion = sum(duraciones_seccion)
        
        # Identifica a los docentes con disponibilidad de carga semanal suficiente
        profesores_elegibles = [
            p['id_profesor'] for p in profesores 
            if horas_prof[p['id_profesor']] + total_horas_seccion <= LIMITE_HORAS_SEMANAL
        ]
        
        # Si ningún docente cumple el criterio, se selecciona aquel con menor carga horaria
        if not profesores_elegibles:
            profesor_asignado = min(horas_prof, key=horas_prof.get)
        else:
            # Selecciona el docente elegible que posea la menor carga para asegurar el balance
            profesor_asignado = min(profesores_elegibles, key=lambda p: horas_prof[p])
            
        horas_prof[profesor_asignado] += total_horas_seccion
        
        for duracion in duraciones_seccion:
            eventos.append({
                'id_evento': id_evento,
                'id_seccion': seccion['id_seccion'],
                'id_profesor': profesor_asignado,
                'duracion': duracion
            })
            id_evento += 1

    return eventos


def generate_curriculos(malla, electivos, secciones, eventos):
    """
    Genera la estructura de currículos (uno por nivel académico) y la relación puente entre currículos y eventos.
    Para cada nivel se incorporan los cursos obligatorios correspondientes y las asignaturas electivas elegibles.
    """
    # Asocia cada sección con sus respectivos eventos
    seccion_a_eventos = {}
    for ev in eventos:
        s = ev['id_seccion']
        if s not in seccion_a_eventos:
            seccion_a_eventos[s] = []
        seccion_a_eventos[s].append(ev['id_evento'])

    # Asocia cada curso con sus respectivas secciones
    curso_a_secciones = {}
    for sec in secciones:
        c = sec['id_curso']
        if c not in curso_a_secciones:
            curso_a_secciones[c] = []
        curso_a_secciones[c].append(sec['id_seccion'])

    # Extrae y ordena los identificadores numéricos de los niveles académicos
    niveles = sorted(malla.keys())  # ['Nivel_03', ..., 'Nivel_10']

    curriculos = []
    bridge = []

    def agregar_curso_a_bridge(nivel_id, id_curso):
        """Registra todos los eventos de un curso específico en la relación del currículo del nivel."""
        if id_curso in curso_a_secciones:
            for id_seccion in curso_a_secciones[id_curso]:
                if id_seccion in seccion_a_eventos:
                    for id_evento in seccion_a_eventos[id_seccion]:
                        bridge.append({
                            'id_curriculo': nivel_id,
                            'id_evento': id_evento
                        })

    for nivel_id in niveles:
        num_nivel = int(nivel_id.split('_')[1])  # 'Nivel_06' -> 6

        curriculos.append({
            'id_curriculo': nivel_id,
            'nombre': f"Ruta {nivel_id.replace('_', ' ')}"
        })

        # Incorpora los cursos obligatorios programados para el nivel académico
        for id_curso, _, _ in malla[nivel_id]:
            agregar_curso_a_bridge(nivel_id, id_curso)

        # Incorpora las asignaturas electivas cuyos prerrequisitos de nivel mínimo se cumplen
        for id_curso, _, _, nivel_minimo in electivos:
            if nivel_minimo <= num_nivel:
                agregar_curso_a_bridge(nivel_id, id_curso)

    return curriculos, bridge


def generate_disponibilidad(profesores, config):
    """
    Construye los bloques de disponibilidad horaria para el personal docente.
    Con el fin de emular condiciones reales, se distribuyen las disponibilidades
    en bloques específicos correspondientes a los turnos mañana, tarde o jornada completa.
    """
    disponibilidad = []
    dias = config['dias']
    dia_cierre = config['dia_cierre']

    # Permite la definición de franjas por día como diccionario o entero uniforme
    fpd_raw = config['franjas_por_dia']
    fpd = fpd_raw if isinstance(fpd_raw, dict) else {d: fpd_raw for d in dias}

    # Calcula los índices de inicio absolutos para las franjas de cada día
    base_dia = {}
    cursor = 1
    for dia in dias:
        base_dia[dia] = cursor
        cursor += fpd[dia]

    # Días hábiles (excluyendo el día de cierre virtual)
    dias_habiles = [d for d in dias if d != dia_cierre]

    for prof in profesores:
        # Asigna un subconjunto aleatorio de días hábiles a cada profesor para garantizar
        # la factibilidad matemática de la regla de espaciado no consecutivo.
        num_dias = random.randint(MIN_DIAS_PROFESOR, len(dias_habiles))
        dias_disponibles = random.sample(dias_habiles, k=num_dias)

        # Incorpora de forma obligatoria el día destinado a la modalidad no presencial (cierre)
        dias_disponibles.append(dia_cierre)

        for dia in dias_disponibles:
            base = base_dia[dia]
            n = fpd[dia]

            # Si corresponde al cierre virtual o el día posee pocas franjas, se asigna jornada completa
            if dia == dia_cierre or n <= UMBRAL_COMPLETO_FRANJAS:
                turno = 'completo'
            else:
                # Selecciona probabilísticamente el turno del docente con base en los pesos configurables
                turno = random.choices(['mañana', 'tarde', 'completo'], weights=PESOS_TURNOS, k=1)[0]

            if turno == 'mañana':
                franja_inicio = base
                franja_fin = base + int(n * FRACCION_BLOQUE_TURNO) - 1
            elif turno == 'tarde':
                franja_inicio = base + n - int(n * FRACCION_BLOQUE_TURNO)
                franja_fin = base + n - 1
            else:  # completo
                franja_inicio = base
                franja_fin = base + n - 1

            disponibilidad.append({
                'id_profesor': prof['id_profesor'],
                'dia': dia,
                'franja_inicio': franja_inicio,
                'franja_fin': franja_fin
            })

    return disponibilidad


def generate_rooms(num_fisicos, num_con_pc, num_dl, cap_fisico, cap_virtual, caracteristicas_posibles):
    """Genera el catálogo de salones, incluyendo la infraestructura física y virtual con sus respectivas características."""
    rooms = []

    # Registra el salón virtual equipado teóricamente con todas las características
    rooms.append({
        'id_salon': 'r_virtual',
        'capacidad': cap_virtual,
        'es_virtual': True,
        'caracteristicas': ','.join(caracteristicas_posibles)
    })

    salon_id = 1

    # Genera la infraestructura física especializada para el aprendizaje profundo
    for _ in range(num_dl):
        rooms.append({
            'id_salon': f"salon_{salon_id}",
            'capacidad': cap_fisico,
            'es_virtual': False,
            'caracteristicas': 'mesa,pc,deep_learning'
        })
        salon_id += 1

    # Genera salones equipados con computadoras personales
    for _ in range(num_con_pc - num_dl):
        rooms.append({
            'id_salon': f"salon_{salon_id}",
            'capacidad': cap_fisico,
            'es_virtual': False,
            'caracteristicas': 'mesa,pc'
        })
        salon_id += 1

    # Genera aulas estándar equipadas únicamente con mobiliario básico (mesas)
    salones_tipicos = num_fisicos - num_con_pc
    for _ in range(salones_tipicos):
        rooms.append({
            'id_salon': f"salon_{salon_id}",
            'capacidad': cap_fisico,
            'es_virtual': False,
            'caracteristicas': 'mesa'
        })
        salon_id += 1

    return rooms


# ============================================================================
# ESCRITURA DE ARCHIVOS CSV
# ============================================================================

def write_csv(filepath, data, fieldnames):
    """Exporta una colección de registros estructurados en formato de diccionario hacia un archivo CSV."""
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"  [OK] {filepath} ({len(data)} filas)")


# ============================================================================
# BLOQUE DE EJECUCIÓN PRINCIPAL
# ============================================================================

if __name__ == '__main__':
    random.seed(SEED)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ========================================================================
    # DIRECTRICES PARA LA SELECCIÓN DEL ESCENARIO DE PRUEBA:
    # 
    # Para cambiar la escala de la instancia del problema y generar los
    # diferentes escenarios evaluados, se debe modificar la rebanada (slice)
    # aplicada a la variable 'niveles_objetivo' de acuerdo con las siguientes opciones:
    #
    # A) ESCENARIO PEQUEÑO (1 Currículo / Ruta académica única):
    #    Ideal para validaciones rápidas, pruebas de concepto y depuración rápida.
    #    Configuración: niveles_objetivo = sorted(MALLA_OBLIGATORIA.keys())[:1]
    #
    # B) ESCENARIO MEDIANO (5 Currículos consecutivos - Por defecto):
    #    Representa un escenario intermedio con un nivel de complejidad moderado.
    #    Configuración: niveles_objetivo = sorted(MALLA_OBLIGATORIA.keys())[:5]
    #
    # C) ESCENARIO GRANDE (Todos los Currículos / 8 Rutas académicas):
    #    Consiste en la representación institucional a escala completa para pruebas de estrés.
    #    Configuración: niveles_objetivo = sorted(MALLA_OBLIGATORIA.keys())
    # ========================================================================
    
    # 1. SELECCIÓN DE NIVELES CURRICULARES (Establece el tamaño del problema)
    niveles_objetivo = sorted(MALLA_OBLIGATORIA.keys())[:1]
    
    # 2. FILTRADO DE LA MALLA CURRICULAR Y DE LAS ASIGNATURAS ELECTIVAS ELEGIBLES
    malla_reducida = {k: v for k, v in MALLA_OBLIGATORIA.items() if k in niveles_objetivo}
    
    # Determina el nivel máximo alcanzado para filtrar electivos
    max_nivel = max([int(n.split('_')[1]) for n in niveles_objetivo])
    electivos_reducidos = [e for e in ELECTIVOS if e[3] <= max_nivel]

    # 3. ESCALAMIENTO PROPORCIONAL DE RECURSOS INFRAESTRUCTURALES Y HUMANOS
    # Restringe la cantidad de salones y docentes en instancias de menor escala para mantener la presión de asignación.
    num_profs_instancia = PROFES_PEQ_INSTANCIA if len(niveles_objetivo) < 5 else NUM_PROFESORES
    num_salones_instancia = SALONES_PEQ_INSTANCIA if len(niveles_objetivo) < 5 else NUM_SALONES_FISICOS

    config = load_config(os.path.join(OUTPUT_DIR, 'config.json'))
    print(f"[INFO] Generando instancia para niveles: {niveles_objetivo}")

    # Generación de registros a partir de los subconjuntos estructurados
    cursos = generate_cursos(malla_reducida, electivos_reducidos)
    secciones = generate_secciones(cursos, SECCIONES_POR_CURSO, ALUMNOS_POR_SECCION)
    profesores = generate_profesores(num_profs_instancia)
    eventos = generate_eventos(secciones, profesores, EVENTOS_POR_SECCION, DURACION_EVENTOS)
    
    # Genera la estructura curricular y la relación puente curriculo-evento
    curriculos, bridge = generate_curriculos(malla_reducida, electivos_reducidos, secciones, eventos)
    
    disponibilidad = generate_disponibilidad(profesores, config)
    rooms = generate_rooms(
        num_salones_instancia, 
        int(num_salones_instancia * RATIO_SALONES_CON_PC), # Mantiene la proporción de computadoras personales.
        NUM_SALONES_DEEP_LEARNING, 
        CAPACIDAD_SALON_FISICO, 
        CAPACIDAD_VIRTUAL,
        CARACTERISTICAS_POSIBLES
    )

    # Escritura de archivos CSV resultantes
    print("\n[INFO] Escribiendo archivos CSV...")
    write_csv(
        os.path.join(OUTPUT_DIR, 'cursos.csv'), cursos,
        ['id_curso', 'nombre', 'requisitos']
    )
    write_csv(
        os.path.join(OUTPUT_DIR, 'secciones.csv'), secciones,
        ['id_seccion', 'id_curso', 'num_alumnos']
    )
    write_csv(
        os.path.join(OUTPUT_DIR, 'eventos.csv'), eventos,
        ['id_evento', 'id_seccion', 'id_profesor', 'duracion']
    )
    write_csv(
        os.path.join(OUTPUT_DIR, 'profesores.csv'), profesores,
        ['id_profesor', 'nombre']
    )
    write_csv(
        os.path.join(OUTPUT_DIR, 'profesores_disponibilidad.csv'), disponibilidad,
        ['id_profesor', 'dia', 'franja_inicio', 'franja_fin']
    )
    write_csv(
        os.path.join(OUTPUT_DIR, 'salones.csv'), rooms,
        ['id_salon', 'capacidad', 'es_virtual', 'caracteristicas']
    )
    write_csv(
        os.path.join(OUTPUT_DIR, 'curriculos.csv'), curriculos,
        ['id_curriculo', 'nombre']
    )
    write_csv(
        os.path.join(OUTPUT_DIR, 'curriculo_evento.csv'), bridge,
        ['id_curriculo', 'id_evento']
    )

    # Resumen cuantitativo del conjunto de datos
    obligatorios = sum(len(v) for v in MALLA_OBLIGATORIA.values())
    print(f"\n[RESUMEN]")
    print(f"  Cursos:       {len(cursos)}")
    print(f"  Secciones:    {len(secciones)}")
    print(f"  Eventos:      {len(eventos)}")
    print(f"  Profesores:   {len(profesores)}")
    print(f"  Curriculos:   {len(curriculos)}")
    print(f"  Salones:      {len(rooms)} (1 virtual + {len(rooms)-1} fisicos)")
    print(f"  Tabla puente: {len(bridge)} asignaciones curriculo-evento")
