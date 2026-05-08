"""
generate_dataset.py
Genera los CSVs del esquema relacional para el UCTP.
Los cursos provienen de la malla curricular real (Nivel 3-10).
Los electivos se asignan a los niveles donde son elegibles segun prerrequisitos.
"""

import csv
import json
import random
import os

# ============================================================================
# MALLA CURRICULAR OBLIGATORIA (Nivel 3 a Nivel 10)
# Formato: (id_curso, nombre, requisitos_infraestructura)
# ============================================================================

MALLA_OBLIGATORIA = {
    'Nivel_03': [
        ('IA_Aplicada', 'Inteligencia Artificial Aplicada', 'mesa,pc,deep_learning'),
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
        ('Machine_Learning', 'Aprendizaje de Maquina', 'mesa,pc,deep_learning'),
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
# ELECTIVOS DE ESPECIALIDAD
# Formato: (id_curso, nombre, requisitos_infra, nivel_minimo)
# nivel_minimo = primer nivel donde el estudiante puede cursarlo
# ============================================================================

ELECTIVOS = [
    # Disponibles desde Nivel 6 (requieren haber culminado V Ciclo)
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

    # Disponibles desde Nivel 7 (requieren curso de Nivel 6 o VI Ciclo)
    ('Analisis_Algoritmos', 'Analisis y Diseno de Algoritmos', 'mesa,pc', 7),
    ('Redes_Avanzadas', 'Redes Avanzadas', 'mesa,pc', 7),
    ('Prog_Movil', 'Programacion Movil', 'mesa,pc', 7),
    ('Seg_Salud_Ocup', 'Seguridad Salud Ocupacional y Bienestar Organizacional', 'mesa', 7),

    # Disponibles desde Nivel 8 (requieren curso de Nivel 7)
    ('Deep_Learning', 'Deep Learning', 'mesa,pc,deep_learning', 8),
    ('Topicos_Ciberseg', 'Topicos Avanzados en Ciberseguridad', 'mesa,pc', 8),
    ('Analitica_BigData', 'Analitica con Big Data', 'mesa,pc', 8),

    # Disponibles desde Nivel 9 (requieren curso de Nivel 8)
    ('Proy_Desarrollo_SW', 'Proyecto de Desarrollo de Software', 'mesa,pc', 9),

    # Disponibles desde Nivel 10 (requieren curso de Nivel 9)
    ('Arq_Empresarial', 'Arquitectura Empresarial', 'mesa', 10),
]

# ============================================================================
# PARAMETROS DE GENERACION (ajustar segun el escenario deseado)
# ============================================================================

SECCIONES_POR_CURSO = (1, 2)       # rango (min, max)
EVENTOS_POR_SECCION = (2, 3)       # rango (min, max)
DURACION_EVENTOS = [2, 3]          # valores posibles exclusivamente
NUM_PROFESORES = 50                 
NUM_SALONES_FISICOS = 100            
NUM_SALONES_CON_PC = 60             
NUM_SALONES_DEEP_LEARNING = 1       
CAPACIDAD_SALON_FISICO = 40
CAPACIDAD_VIRTUAL = 99999
ALUMNOS_POR_SECCION = (25, 40)     # rango (min, max)
CARACTERISTICAS_POSIBLES = ['mesa', 'pc', 'deep_learning']

SEED = 50
OUTPUT_DIR = 'dataset'

# ============================================================================
# CARGA DE CONFIGURACION INSTITUCIONAL
# ============================================================================

def load_config(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

# ============================================================================
# GENERACION DE DATOS
# ============================================================================

def generate_cursos(malla, electivos):
    """Extrae todos los cursos unicos: obligatorios + electivos."""
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
    """Genera secciones para cada curso."""
    secciones = []
    letras = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
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
    """Genera la tabla de profesores."""
    return [
        {'id_profesor': f"Prof_{i+1}", 'nombre': f"Profesor_{i+1}"}
        for i in range(num_profesores)
    ]


def generate_eventos(secciones, profesores, eventos_rango, duraciones):
    """Genera eventos para cada seccion, asignando profesores con round-robin."""
    eventos = []
    id_evento = 1
    prof_index = 0
    num_profs = len(profesores)

    for seccion in secciones:
        num_eventos = random.randint(*eventos_rango)
        for _ in range(num_eventos):
            eventos.append({
                'id_evento': id_evento,
                'id_seccion': seccion['id_seccion'],
                'id_profesor': profesores[prof_index % num_profs]['id_profesor'],
                'duracion': random.choice(duraciones)
            })
            id_evento += 1
            prof_index += 1

    return eventos


def generate_curriculos(malla, electivos, secciones, eventos):
    """
    Genera curriculos (uno por nivel) y la tabla puente curriculo-evento.
    Para cada nivel, incluye los cursos obligatorios + todos los electivos elegibles.
    """
    # Mapear seccion -> eventos
    seccion_a_eventos = {}
    for ev in eventos:
        s = ev['id_seccion']
        if s not in seccion_a_eventos:
            seccion_a_eventos[s] = []
        seccion_a_eventos[s].append(ev['id_evento'])

    # Mapear curso -> secciones
    curso_a_secciones = {}
    for sec in secciones:
        c = sec['id_curso']
        if c not in curso_a_secciones:
            curso_a_secciones[c] = []
        curso_a_secciones[c].append(sec['id_seccion'])

    # Extraer numeros de nivel para iterar
    niveles = sorted(malla.keys())  # ['Nivel_03', ..., 'Nivel_10']

    curriculos = []
    bridge = []

    def agregar_curso_a_bridge(nivel_id, id_curso):
        """Agrega todos los eventos de un curso al bridge del nivel."""
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

        # Agregar cursos obligatorios del nivel
        for id_curso, _, _ in malla[nivel_id]:
            agregar_curso_a_bridge(nivel_id, id_curso)

        # Agregar electivos elegibles (nivel_minimo <= nivel actual)
        for id_curso, _, _, nivel_minimo in electivos:
            if nivel_minimo <= num_nivel:
                agregar_curso_a_bridge(nivel_id, id_curso)

    return curriculos, bridge


def generate_disponibilidad(profesores, config):
    """Genera bloques de disponibilidad realistas para cada profesor."""
    disponibilidad = []
    dias = config['dias']
    dia_cierre = config['dia_cierre']

    # Soporta franjas_por_dia como dict {dia: n} o int uniforme
    fpd_raw = config['franjas_por_dia']
    fpd = fpd_raw if isinstance(fpd_raw, dict) else {d: fpd_raw for d in dias}

    # Construir base acumulada por dia
    base_dia = {}
    cursor = 1
    for dia in dias:
        base_dia[dia] = cursor
        cursor += fpd[dia]

    # Dias habiles (excluyendo el dia de cierre)
    dias_habiles = [d for d in dias if d != dia_cierre]

    for prof in profesores:
        # Cada profesor esta disponible en 3-4 dias habiles
        num_dias = random.randint(3, min(4, len(dias_habiles)))
        dias_disponibles = random.sample(dias_habiles, k=num_dias)

        # Adicionalmente, todos estan disponibles el dia de cierre (virtual)
        dias_disponibles.append(dia_cierre)

        for dia in dias_disponibles:
            base = base_dia[dia]
            n = fpd[dia]

            # Jornada completa para garantizar factibilidad
            disponibilidad.append({
                'id_profesor': prof['id_profesor'],
                'dia': dia,
                'franja_inicio': base,
                'franja_fin': base + n - 1
            })

    return disponibilidad


def generate_rooms(num_fisicos, num_con_pc, num_dl, cap_fisico, cap_virtual, caracteristicas_posibles):
    """Genera la tabla de salones: virtual + fisicos con distintas caracteristicas."""
    rooms = []

    # Salon virtual (tiene todas las caracteristicas posibles)
    rooms.append({
        'id_salon': 'r_virtual',
        'capacidad': cap_virtual,
        'es_virtual': True,
        'caracteristicas': ','.join(caracteristicas_posibles)
    })

    salon_id = 1

    # Salon de deep learning (tiene mesa + pc + deep_learning)
    for _ in range(num_dl):
        rooms.append({
            'id_salon': f"salon_{salon_id}",
            'capacidad': cap_fisico,
            'es_virtual': False,
            'caracteristicas': 'mesa,pc,deep_learning'
        })
        salon_id += 1

    # Salones con PC (tienen mesa + pc)
    for _ in range(num_con_pc - num_dl):
        rooms.append({
            'id_salon': f"salon_{salon_id}",
            'capacidad': cap_fisico,
            'es_virtual': False,
            'caracteristicas': 'mesa,pc'
        })
        salon_id += 1

    # Salones tipicos (solo mesa)
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
# ESCRITURA DE CSVS
# ============================================================================

def write_csv(filepath, data, fieldnames):
    """Escribe una lista de diccionarios a un archivo CSV."""
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"  [OK] {filepath} ({len(data)} filas)")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    random.seed(SEED)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. DEFINIR NIVELES PARA ESTA INSTANCIA (Modifica esto para escalar)
    # Ejemplo: ['Nivel_03'] o ['Nivel_03', 'Nivel_04', 'Nivel_05']
    niveles_objetivo = ['Nivel_03'] 
    
    # 2. FILTRADO DE MALLA
    malla_reducida = {k: v for k, v in MALLA_OBLIGATORIA.items() if k in niveles_objetivo}
    
    # Obtener el número máximo de nivel para filtrar electivos
    max_nivel = max([int(n.split('_')[1]) for n in niveles_objetivo])
    electivos_reducidos = [e for e in ELECTIVOS if e[3] <= max_nivel]

    # 3. AJUSTE DE RECURSOS PROPORCIONALES (Evita que el solver se relaje)
    # Para una instancia pequeña, reduce los profesores y salones
    num_profs_instancia = 15 if len(niveles_objetivo) < 3 else NUM_PROFESORES
    num_salones_instancia = 20 if len(niveles_objetivo) < 3 else NUM_SALONES_FISICOS

    config = load_config(os.path.join(OUTPUT_DIR, 'config.json'))
    print(f"[INFO] Generando instancia para niveles: {niveles_objetivo}")

    # Generar datos usando los conjuntos filtrados
    cursos = generate_cursos(malla_reducida, electivos_reducidos)
    secciones = generate_secciones(cursos, SECCIONES_POR_CURSO, ALUMNOS_POR_SECCION)
    profesores = generate_profesores(num_profs_instancia)
    eventos = generate_eventos(secciones, profesores, EVENTOS_POR_SECCION, DURACION_EVENTOS)
    
    # Importante: Pasar malla_reducida y electivos_reducidos aquí también
    curriculos, bridge = generate_curriculos(malla_reducida, electivos_reducidos, secciones, eventos)
    
    disponibilidad = generate_disponibilidad(profesores, config)
    rooms = generate_rooms(
        num_salones_instancia, 
        int(num_salones_instancia * 0.6), # Mantener ratio de PCs
        NUM_SALONES_DEEP_LEARNING, 
        CAPACIDAD_SALON_FISICO, 
        CAPACIDAD_VIRTUAL,
        CARACTERISTICAS_POSIBLES
    )

    # Escribir CSVs
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
        os.path.join(OUTPUT_DIR, 'professors_availability.csv'), disponibilidad,
        ['id_profesor', 'dia', 'franja_inicio', 'franja_fin']
    )
    write_csv(
        os.path.join(OUTPUT_DIR, 'rooms.csv'), rooms,
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

    # Resumen
    obligatorios = sum(len(v) for v in MALLA_OBLIGATORIA.values())
    print(f"\n[RESUMEN]")
    print(f"  Cursos:       {len(cursos)}")
    print(f"  Secciones:    {len(secciones)}")
    print(f"  Eventos:      {len(eventos)}")
    print(f"  Profesores:   {len(profesores)}")
    print(f"  Curriculos:   {len(curriculos)}")
    print(f"  Salones:      {len(rooms)} (1 virtual + {len(rooms)-1} fisicos)")
    print(f"  Tabla puente: {len(bridge)} asignaciones curriculo-evento")
