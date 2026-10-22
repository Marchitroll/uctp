"""Genera los archivos CSV del dataset UCTP (cursos, secciones, eventos, salones, profesores)."""
import argparse
import csv
import os
import random

from uctp_utils import cargar_config_institucional


# Curso: Asignatura de la malla curricular.
# Evento: Unidad mínima e indivisible de asignación horaria (bloque continuo de clase). Cada curso se
# abre en secciones (ej. Calculo_II_A), y cada sección se descompone en 2 o 3 eventos semanales de 2 o 3 horas lectivas fijas.
# Franja horaria: Unidad atómica y discreta de tiempo semanal (bloque de 1 hora reloj).


SEMILLA_PREDETERMINADA = 50
DIR_SALIDA_PREDETERMINADO = 'dataset'
LETRAS_SECCIONES = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
SECCIONES_POR_CURSO = (1, 3)
ALUMNOS_POR_SECCION = (25, 36)
LIMITE_HORAS_SEMANAL = 48
MIN_DIAS_PROFESOR = 4
PROPORCION_SALONES_CON_PC = 0.6
NUM_SALONES_DEEP_LEARNING = 1
CAPACIDAD_SALON_FISICO = 36
CAPACIDAD_VIRTUAL = 99999
CARACTERISTICAS_POSIBLES = ['mesa', 'pc', 'deep_learning']
PROBABILIDADES_TURNOS_DOCENTE = [30, 30, 40]
# Si un día tiene 8 o menos franjas, es una jornada tan corta que no tiene sentido dividirla en mañana y tarde
LIMITE_FRANJAS_JORNADA_CORTA = 8
# Mañana (primer 70% de todas las franjas de un día), Tarde (último 70%) o Completo (100%).
COBERTURA_TURNO_PARCIAL = 0.7

RECURSOS_POR_ESCALA = {
    'pequena': {
        'profesores': 15,
        'salones_fisicos': 20,
    },
    'mediana': {
        'profesores': 15,
        'salones_fisicos': 20,
    },
    'grande': {
        'profesores': 50,
        'salones_fisicos': 100,
    },
}

MALLA_OBLIGATORIA = {
    'Nivel_03': [
        # id_curso, requisitos, horas_semanales
        ('IA_Aplicada', 'mesa,pc', 5),
        ('Calculo_II', 'mesa', 6),
        ('Sist_Organizacionales', 'mesa', 4),
        ('Fisica_Sistemas', 'mesa', 5),
        ('Estr_Discretas', 'mesa', 4),
        ('Intro_Programacion', 'mesa,pc', 5),
    ],
    'Nivel_04': [
        ('Estadistica_Prob', 'mesa', 4),
        ('Calculo_III', 'mesa', 6),
        ('Mod_Integracion', 'mesa,pc', 5),
        ('Costeo_Operaciones', 'mesa', 4),
        ('POO', 'mesa,pc', 7),
        ('Arq_Computadoras', 'mesa,pc', 5),
    ],
    'Nivel_05': [
        ('Estadistica_Aplicada', 'mesa', 4),
        ('IO_I', 'mesa', 5),
        ('Sist_Operativos', 'mesa,pc', 5),
        ('Competencias_Gerenciales', 'mesa', 4),
        ('ED_I', 'mesa,pc', 7),
        ('Mod_BD', 'mesa,pc', 5),
    ],
    'Nivel_06': [
        ('Ing_Procesos_Negocio', 'mesa', 4),
        ('Redes', 'mesa,pc', 5),
        ('Simulacion', 'mesa,pc', 4),
        ('ED_II', 'mesa,pc', 7),
        ('Prog_Web', 'mesa,pc', 5),
        ('Gestion_Financiera', 'mesa', 4),
    ],
    'Nivel_07': [
        ('Sist_Intel_Empresarial', 'mesa,pc', 4),
        ('Gestion_Operaciones', 'mesa', 4),
        ('Ing_Software_I', 'mesa,pc', 5),
        ('Machine_Learning', 'mesa,pc', 5),
        ('Ciberseguridad', 'mesa,pc', 5),
    ],
    'Nivel_08': [
        ('Propuesta_Investigacion', 'mesa', 4),
        ('Sist_ERP', 'mesa,pc', 5),
        ('Auditoria_Control', 'mesa', 4),
        ('Ing_Software_II', 'mesa,pc', 5),
    ],
    'Nivel_09': [
        ('Seminario_I', 'mesa', 4),
        ('Plan_Estrategico', 'mesa', 4),
        ('Gestion_Proyectos', 'mesa', 4),
        ('Seg_Sistemas', 'mesa,pc', 4),
    ],
    'Nivel_10': [
        ('Seminario_II', 'mesa', 4),
        ('Gestion_Servicios_Dig', 'mesa', 4),
        ('Proy_Integrador', 'mesa,pc', 7),
    ],
}

ELECTIVOS = [
    # id_curso, requisitos, nivel_minimo, horas_semanales
    ('Paradigmas_Prog', 'mesa,pc', 6, 4),
    ('IoT', 'mesa,pc', 6, 4),
    ('Gestion_BD', 'mesa,pc', 6, 4),
    ('Ing_Conocimiento', 'mesa', 6, 4),
    ('Sist_Distribuidos', 'mesa,pc', 6, 4),
    ('Analitica_Negocios', 'mesa', 6, 4),
    ('Cloud', 'mesa,pc', 6, 4),
    ('Innovacion_Digital', 'mesa', 6, 4),
    ('Proy_Videojuegos', 'mesa,pc', 6, 4),
    ('HCI', 'mesa,pc', 6, 4),
    ('Arq_TI', 'mesa', 6, 4),
    ('DevOps', 'mesa,pc', 6, 4),
    ('Arq_Software', 'mesa,pc', 6, 4),
    ('Analisis_Algoritmos', 'mesa,pc', 7, 4),
    ('Redes_Avanzadas', 'mesa,pc', 7, 4),
    ('Prog_Movil', 'mesa,pc', 7, 4),
    ('Seg_Salud_Ocup', 'mesa', 7, 4),
    ('Deep_Learning', 'mesa,pc,deep_learning', 8, 4),
    ('Topicos_Ciberseg', 'mesa,pc', 8, 4),
    ('Analitica_BigData', 'mesa,pc', 8, 4),
    ('Proy_Desarrollo_SW', 'mesa,pc', 9, 4),
    ('Arq_Empresarial', 'mesa', 10, 4),
]

AREAS_CURSOS = {
    'Calculo_II': 'CIENCIAS_BASICAS',
    'Calculo_III': 'CIENCIAS_BASICAS',
    'Fisica_Sistemas': 'CIENCIAS_BASICAS',
    'Estadistica_Prob': 'CIENCIAS_BASICAS',
    'Estadistica_Aplicada': 'CIENCIAS_BASICAS',
    'Estr_Discretas': 'CIENCIAS_BASICAS',
    'Analisis_Algoritmos': 'CIENCIAS_BASICAS',

    'Sist_Organizacionales': 'GESTION_PROYECTOS',
    'Costeo_Operaciones': 'GESTION_PROYECTOS',
    'Competencias_Gerenciales': 'GESTION_PROYECTOS',
    'IO_I': 'GESTION_PROYECTOS',
    'Gestion_Financiera': 'GESTION_PROYECTOS',
    'Gestion_Operaciones': 'GESTION_PROYECTOS',
    'Propuesta_Investigacion': 'GESTION_PROYECTOS',
    'Auditoria_Control': 'GESTION_PROYECTOS',
    'Seminario_I': 'GESTION_PROYECTOS',
    'Plan_Estrategico': 'GESTION_PROYECTOS',
    'Gestion_Proyectos': 'GESTION_PROYECTOS',
    'Seminario_II': 'GESTION_PROYECTOS',
    'Gestion_Servicios_Dig': 'GESTION_PROYECTOS',
    'Analitica_Negocios': 'GESTION_PROYECTOS',
    'Innovacion_Digital': 'GESTION_PROYECTOS',
    'Seg_Salud_Ocup': 'GESTION_PROYECTOS',

    'Intro_Programacion': 'INGENIERIA_SOFTWARE',
    'POO': 'INGENIERIA_SOFTWARE',
    'ED_I': 'INGENIERIA_SOFTWARE',
    'ED_II': 'INGENIERIA_SOFTWARE',
    'Prog_Web': 'INGENIERIA_SOFTWARE',
    'Ing_Software_I': 'INGENIERIA_SOFTWARE',
    'Ing_Software_II': 'INGENIERIA_SOFTWARE',
    'Proy_Integrador': 'INGENIERIA_SOFTWARE',
    'Paradigmas_Prog': 'INGENIERIA_SOFTWARE',
    'Proy_Videojuegos': 'INGENIERIA_SOFTWARE',
    'HCI': 'INGENIERIA_SOFTWARE',
    'DevOps': 'INGENIERIA_SOFTWARE',
    'Arq_Software': 'INGENIERIA_SOFTWARE',
    'Prog_Movil': 'INGENIERIA_SOFTWARE',
    'Proy_Desarrollo_SW': 'INGENIERIA_SOFTWARE',

    'Mod_Integracion': 'SISTEMAS_INFORMACION',
    'Mod_BD': 'SISTEMAS_INFORMACION',
    'Ing_Procesos_Negocio': 'SISTEMAS_INFORMACION',
    'Simulacion': 'SISTEMAS_INFORMACION',
    'Sist_Intel_Empresarial': 'SISTEMAS_INFORMACION',
    'Sist_ERP': 'SISTEMAS_INFORMACION',
    'Gestion_BD': 'SISTEMAS_INFORMACION',
    'Ing_Conocimiento': 'SISTEMAS_INFORMACION',
    'Arq_TI': 'SISTEMAS_INFORMACION',
    'Analitica_BigData': 'SISTEMAS_INFORMACION',
    'Arq_Empresarial': 'SISTEMAS_INFORMACION',

    'IA_Aplicada': 'TECNOLOGIAS_INFORMACION',
    'Arq_Computadoras': 'TECNOLOGIAS_INFORMACION',
    'Sist_Operativos': 'TECNOLOGIAS_INFORMACION',
    'Redes': 'TECNOLOGIAS_INFORMACION',
    'Machine_Learning': 'TECNOLOGIAS_INFORMACION',
    'Ciberseguridad': 'TECNOLOGIAS_INFORMACION',
    'Seg_Sistemas': 'TECNOLOGIAS_INFORMACION',
    'IoT': 'TECNOLOGIAS_INFORMACION',
    'Sist_Distribuidos': 'TECNOLOGIAS_INFORMACION',
    'Cloud': 'TECNOLOGIAS_INFORMACION',
    'Redes_Avanzadas': 'TECNOLOGIAS_INFORMACION',
    'Deep_Learning': 'TECNOLOGIAS_INFORMACION',
    'Topicos_Ciberseg': 'TECNOLOGIAS_INFORMACION',
}

COMPATIBILIDAD = {
    'INGENIERIA_SOFTWARE': ['INGENIERIA_SOFTWARE', 'SISTEMAS_INFORMACION'],
    'SISTEMAS_INFORMACION': ['SISTEMAS_INFORMACION', 'INGENIERIA_SOFTWARE'],
    'TECNOLOGIAS_INFORMACION': ['TECNOLOGIAS_INFORMACION', 'INGENIERIA_SOFTWARE'],
    'CIENCIAS_BASICAS': ['CIENCIAS_BASICAS', 'INGENIERIA_SOFTWARE'],
    'GESTION_PROYECTOS': ['GESTION_PROYECTOS', 'SISTEMAS_INFORMACION'],
}


def deducir_duraciones_eventos(horas_semanales: int) -> list[int]:
    if horas_semanales == 4:
        return [2, 2]
    if horas_semanales == 5:
        return [2, 3]
    if horas_semanales == 6:
        return [3, 3]
    if horas_semanales == 7:
        return [2, 2, 3]
    if horas_semanales == 8:
        return [2, 3, 3]
    raise ValueError(f"Horas semanales no contempladas en la malla: {horas_semanales}")


def generar_cursos(malla: dict[str, list], electivos: list[tuple]) -> list[dict]:
    """Extrae la totalidad de asignaturas únicas combinando los cursos obligatorios y electivos."""
    cursos = []
    cursos_vistos = set()

    for lista_cursos in malla.values():
        for curso_tupla in lista_cursos:
            id_curso = curso_tupla[0]
            requisitos = curso_tupla[1]
            horas_semanales = curso_tupla[2]
            duraciones_eventos_base = deducir_duraciones_eventos(horas_semanales)

            if id_curso not in cursos_vistos:
                cursos_vistos.add(id_curso)
                cursos.append({
                    'id_curso': id_curso,
                    'requisitos': requisitos,
                    'horas_semanales': horas_semanales,
                    'duraciones_eventos': duraciones_eventos_base,
                })

    for electivo_tupla in electivos:
        id_curso = electivo_tupla[0]
        requisitos = electivo_tupla[1]
        horas_semanales = electivo_tupla[3]
        duraciones_eventos_base = deducir_duraciones_eventos(horas_semanales)
        if id_curso not in cursos_vistos:
            cursos_vistos.add(id_curso)
            cursos.append({
                'id_curso': id_curso,
                'requisitos': requisitos,
                'horas_semanales': horas_semanales,
                'duraciones_eventos': duraciones_eventos_base,
            })

    return cursos


def generar_secciones(cursos: list[dict], rango_secciones: tuple[int, int], rango_alumnos: tuple[int, int]) -> list[dict]:
    """Genera secciones para cada curso."""
    secciones = []
    letras = LETRAS_SECCIONES
    min_secciones = rango_secciones[0]
    max_secciones = rango_secciones[1]
    min_alumnos = rango_alumnos[0]
    max_alumnos = rango_alumnos[1]

    for curso in cursos:
        id_curso = curso['id_curso']
        num_secciones = random.randint(min_secciones, max_secciones)
        for indice_seccion in range(num_secciones):
            alumnos_seccion = random.randint(min_alumnos, max_alumnos)
            letra_seccion = letras[indice_seccion]
            secciones.append({
                'id_seccion': f"{id_curso}_{letra_seccion}",
                'id_curso': id_curso,
                'num_alumnos': alumnos_seccion,
            })
    return secciones


def generar_profesores(cantidad_profesores: int) -> list[dict]:
    """Genera los profesores con su especialidad."""
    especialidades = [
        'INGENIERIA_SOFTWARE',
        'SISTEMAS_INFORMACION',
        'TECNOLOGIAS_INFORMACION',
        'CIENCIAS_BASICAS',
        'GESTION_PROYECTOS',
    ]
    pesos = [0.25, 0.20, 0.20, 0.15, 0.20]
    profesores = []
    for indice_profesor in range(cantidad_profesores):
        if indice_profesor < len(especialidades):
            especialidad = especialidades[indice_profesor]
        else:
            especialidad = random.choices(especialidades, weights=pesos, k=1)[0]
            
        profesores.append({
            'id_profesor': f"Prof_{indice_profesor+1}",
            'nombre': f"Profesor_{indice_profesor+1}",
            'especialidad': especialidad,
        })
    return profesores


def generar_eventos(secciones: list[dict], profesores: list[dict], cursos: list[dict]) -> tuple[list[dict], dict[str, int]]:
    """Genera los eventos por sección y asigna docentes según especialidad y carga."""
    eventos = []
    id_evento = 1
    
    horas_por_profesor = {}
    cursos_por_profesor = {}
    areas_por_profesor = {}
    for profesor in profesores:
        id_profesor = profesor['id_profesor']
        horas_por_profesor[id_profesor] = 0
        cursos_por_profesor[id_profesor] = set()
        areas_por_profesor[id_profesor] = set()

    catalogo_duraciones_por_curso = {}
    for curso in cursos:
        id_curso = curso['id_curso']
        catalogo_duraciones_por_curso[id_curso] = list(curso['duraciones_eventos'])

    for seccion in secciones:
        id_seccion = seccion['id_seccion']
        id_curso = seccion['id_curso']

        duraciones_base = catalogo_duraciones_por_curso[id_curso]
        duraciones_seccion = random.sample(duraciones_base, len(duraciones_base))
        total_horas_seccion = sum(duraciones_seccion)
        
        area = AREAS_CURSOS.get(id_curso, 'INGENIERIA_SOFTWARE')
        
        profesores_compatibles = []
        for profesor in profesores:
            especialidad = profesor['especialidad']
            areas_compatibles = COMPATIBILIDAD.get(especialidad, ['INGENIERIA_SOFTWARE'])
            if area in areas_compatibles:
                profesores_compatibles.append(profesor)
        if not profesores_compatibles:
            profesores_compatibles = list(profesores)

        candidatos = []
        for profesor in profesores_compatibles:
            id_profesor = profesor['id_profesor']
            carga_proyectada = horas_por_profesor[id_profesor] + total_horas_seccion
            if carga_proyectada <= LIMITE_HORAS_SEMANAL:
                candidatos.append(profesor)
        if not candidatos:
            candidatos = list(profesores_compatibles)
            
        candidatos_mismo_curso = []
        candidatos_misma_area = []
        for profesor in candidatos:
            id_profesor = profesor['id_profesor']
            if id_curso in cursos_por_profesor[id_profesor]:
                candidatos_mismo_curso.append(profesor)
            if area in areas_por_profesor[id_profesor]:
                candidatos_misma_area.append(profesor)
        
        if len(candidatos_mismo_curso) > 0:
            candidatos_priorizados = candidatos_mismo_curso
        elif len(candidatos_misma_area) > 0:
            candidatos_priorizados = candidatos_misma_area
        else:
            candidatos_priorizados = candidatos

        # Política de balanceo equitativo de carga horaria docente
        profesor_elegido = None
        menor_carga_horas = float('inf')
        for profesor in candidatos_priorizados:
            id_candidato = profesor['id_profesor']
            horas_acumuladas = horas_por_profesor[id_candidato]
            if horas_acumuladas < menor_carga_horas:
                menor_carga_horas = horas_acumuladas
                profesor_elegido = profesor
            
        id_profesor_asignado = profesor_elegido['id_profesor']
        horas_por_profesor[id_profesor_asignado] += total_horas_seccion
        cursos_por_profesor[id_profesor_asignado].add(id_curso)
        areas_por_profesor[id_profesor_asignado].add(area)
        
        for duracion_evento in duraciones_seccion:
            eventos.append({
                'id_evento': id_evento,
                'id_seccion': id_seccion,
                'id_profesor': id_profesor_asignado,
                'duracion': duracion_evento,
            })
            id_evento += 1

    return eventos, horas_por_profesor


def generar_curriculos(malla: dict[str, list], electivos: list[tuple], secciones: list[dict], eventos: list[dict]) -> tuple[list[dict], list[dict]]:
    """Genera currículos por nivel y la relación con sus eventos."""
    eventos_por_seccion = {}
    for evento in eventos:
        id_seccion = evento['id_seccion']
        if id_seccion not in eventos_por_seccion:
            eventos_por_seccion[id_seccion] = []
        eventos_por_seccion[id_seccion].append(evento['id_evento'])

    secciones_por_curso = {}
    for seccion in secciones:
        id_curso = seccion['id_curso']
        if id_curso not in secciones_por_curso:
            secciones_por_curso[id_curso] = []
        secciones_por_curso[id_curso].append(seccion['id_seccion'])

    niveles = sorted(malla.keys())
    curriculos = []
    asignaciones_curriculo_evento = []

    def agregar_curso_a_curriculo(id_nivel: str, id_curso: str):
        """Agrega los eventos del curso al currículo."""
        if id_curso in secciones_por_curso:
            for id_seccion in secciones_por_curso[id_curso]:
                if id_seccion in eventos_por_seccion:
                    for id_evento in eventos_por_seccion[id_seccion]:
                        asignaciones_curriculo_evento.append({
                            'id_curriculo': id_nivel,
                            'id_evento': id_evento,
                        })

    for id_nivel in niveles:
        numero_nivel = int(id_nivel.split('_')[1])

        curriculos.append({
            'id_curriculo': id_nivel,
            'nombre': f"Ruta {id_nivel.replace('_', ' ')}",
        })

        for curso_tupla in malla[id_nivel]:
            id_curso = curso_tupla[0]
            agregar_curso_a_curriculo(id_nivel, id_curso)

        for electivo_tupla in electivos:
            id_curso = electivo_tupla[0]
            nivel_minimo = electivo_tupla[2]
            if nivel_minimo <= numero_nivel:
                agregar_curso_a_curriculo(id_nivel, id_curso)

    return curriculos, asignaciones_curriculo_evento


def generar_disponibilidad(profesores: list[dict], config: dict, horas_por_profesor: dict[str, int] = None) -> list[dict]:
    """Genera franjas de disponibilidad para cada docente según su carga."""
    disponibilidad = []
    dias = config['dias']
    dia_cierre = config['dia_cierre']

    franjas_por_dia_raw = config['franjas_por_dia']
    if isinstance(franjas_por_dia_raw, dict):
        franjas_por_dia = franjas_por_dia_raw
    else:
        franjas_por_dia = {}
        for dia in dias:
            franjas_por_dia[dia] = franjas_por_dia_raw

    franja_inicio_por_dia = {}
    franja_acumulada = 1
    for dia in dias:
        franja_inicio_por_dia[dia] = franja_acumulada
        franja_acumulada += franjas_por_dia[dia]

    dias_habiles = []
    for dia in dias:
        if dia != dia_cierre:
            dias_habiles.append(dia)

    for profesor in profesores:
        id_profesor = profesor['id_profesor']
        horas_asignadas = horas_por_profesor.get(id_profesor, 0) if horas_por_profesor else 0

        if horas_asignadas > 12:
            dias_disponibles = list(dias_habiles)
        else:
            cantidad_dias = random.randint(MIN_DIAS_PROFESOR, len(dias_habiles))
            dias_disponibles = random.sample(dias_habiles, k=cantidad_dias)

        dias_disponibles.append(dia_cierre)

        for dia in dias_disponibles:
            franja_base = franja_inicio_por_dia[dia]
            total_franjas_dia = franjas_por_dia[dia]

            if dia == dia_cierre or total_franjas_dia <= LIMITE_FRANJAS_JORNADA_CORTA or horas_asignadas > 12:
                turno = 'completo'
            else:
                turno = random.choices(['mañana', 'tarde', 'completo'], weights=PROBABILIDADES_TURNOS_DOCENTE, k=1)[0]

            if turno == 'mañana':
                franja_inicio = franja_base
                franja_fin = franja_base + int(total_franjas_dia * COBERTURA_TURNO_PARCIAL) - 1
            elif turno == 'tarde':
                franja_inicio = franja_base + total_franjas_dia - int(total_franjas_dia * COBERTURA_TURNO_PARCIAL)
                franja_fin = franja_base + total_franjas_dia - 1
            else:
                franja_inicio = franja_base
                franja_fin = franja_base + total_franjas_dia - 1

            disponibilidad.append({
                'id_profesor': profesor['id_profesor'],
                'dia': dia,
                'franja_inicio': franja_inicio,
                'franja_fin': franja_fin,
            })

    return disponibilidad


def generar_salones(
    cantidad_fisicos: int,
    cantidad_con_pc: int,
    cantidad_deep_learning: int,
    capacidad_fisica: int,
    capacidad_virtual: int,
    caracteristicas_posibles: list[str],
) -> list[dict]:
    """Genera el catálogo de salones físicos y virtuales."""
    salones = []

    salones.append({
        'id_salon': 'r_virtual',
        'capacidad': capacidad_virtual,
        'es_virtual': True,
        'caracteristicas': ','.join(caracteristicas_posibles),
    })

    for numero_salon in range(1, cantidad_fisicos + 1):
        if numero_salon <= cantidad_deep_learning:
            caracteristicas = 'mesa,pc,deep_learning'
        elif numero_salon <= cantidad_con_pc:
            caracteristicas = 'mesa,pc'
        else:
            caracteristicas = 'mesa'

        salones.append({
            'id_salon': f"salon_{numero_salon}",
            'capacidad': capacidad_fisica,
            'es_virtual': False,
            'caracteristicas': caracteristicas,
        })

    return salones


def escribir_csv(ruta_archivo: str, filas: list[dict], nombres_columnas: list[str]):
    """Escribe una lista de diccionarios en un archivo CSV."""
    with open(ruta_archivo, 'w', newline='', encoding='utf-8') as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=nombres_columnas)
        escritor.writeheader()
        escritor.writerows(filas)
    print(f"  [OK] {ruta_archivo} ({len(filas)} filas)")


def main():
    parser = argparse.ArgumentParser(description="Generador de datasets UCTP")
    parser.add_argument(
        "--instancia",
        type=str,
        choices=["pequena", "pequeña", "mediana", "grande"],
        default="pequena",
        help="Escala del escenario a generar (pequena, mediana, grande)",
    )
    parser.add_argument(
        "--semilla",
        type=int,
        default=SEMILLA_PREDETERMINADA,
        help="Semilla pseudoaleatoria para la generación de datos (default: 50)",
    )
    parser.add_argument(
        "--dir_salida",
        type=str,
        default=DIR_SALIDA_PREDETERMINADO,
        help="Directorio de destino para los archivos CSV generados (default: 'dataset')",
    )
    args = parser.parse_args()

    random.seed(args.semilla)
    dir_salida = args.dir_salida
    os.makedirs(dir_salida, exist_ok=True)

    instancia = args.instancia.lower()
    if instancia in ["pequena", "pequeña"]:
        escala = "pequena"
        niveles_objetivo = sorted(MALLA_OBLIGATORIA.keys())[:1]
    elif instancia == "mediana":
        escala = "mediana"
        niveles_objetivo = sorted(MALLA_OBLIGATORIA.keys())[:4]
    else:
        escala = "grande"
        niveles_objetivo = sorted(MALLA_OBLIGATORIA.keys())
    
    malla_reducida = {}
    for nivel, cursos in MALLA_OBLIGATORIA.items():
        if nivel in niveles_objetivo:
            malla_reducida[nivel] = cursos

    nivel_maximo = 0
    for nivel in niveles_objetivo:
        numero_nivel = int(nivel.split('_')[1])
        if numero_nivel > nivel_maximo:
            nivel_maximo = numero_nivel

    electivos_reducidos = []
    for electivo_tupla in ELECTIVOS:
        nivel_minimo_electivo = electivo_tupla[2]
        if nivel_minimo_electivo <= nivel_maximo:
            electivos_reducidos.append(electivo_tupla)

    recursos_escala = RECURSOS_POR_ESCALA[escala]
    cantidad_profesores_instancia = recursos_escala['profesores']
    cantidad_salones_instancia = recursos_escala['salones_fisicos']

    ruta_configuracion = os.path.join(os.path.dirname(__file__), 'config.json')
    config = cargar_config_institucional(ruta_configuracion)
    print(f"[INFO] Generando instancia para niveles: {niveles_objetivo}")

    cursos = generar_cursos(malla_reducida, electivos_reducidos)
    secciones = generar_secciones(cursos, SECCIONES_POR_CURSO, ALUMNOS_POR_SECCION)
    profesores = generar_profesores(cantidad_profesores_instancia)
    eventos, horas_por_profesor = generar_eventos(secciones, profesores, cursos)
    curriculos, asignaciones_curriculo_evento = generar_curriculos(malla_reducida, electivos_reducidos, secciones, eventos)
    
    disponibilidad = generar_disponibilidad(profesores, config, horas_por_profesor)
    salones = generar_salones(
        cantidad_salones_instancia, 
        int(cantidad_salones_instancia * PROPORCION_SALONES_CON_PC),
        NUM_SALONES_DEEP_LEARNING, 
        CAPACIDAD_SALON_FISICO, 
        CAPACIDAD_VIRTUAL,
        CARACTERISTICAS_POSIBLES,
    )

    print("\n[INFO] Escribiendo archivos CSV...")
    filas_cursos = []
    for curso in cursos:
        filas_cursos.append({
            'id_curso': curso['id_curso'],
            'requisitos': curso['requisitos'],
            'horas_semanales': curso['horas_semanales'],
        })

    escribir_csv(
        os.path.join(dir_salida, 'cursos.csv'), filas_cursos,
        ['id_curso', 'requisitos', 'horas_semanales'],
    )
    escribir_csv(
        os.path.join(dir_salida, 'secciones.csv'), secciones,
        ['id_seccion', 'id_curso', 'num_alumnos'],
    )
    escribir_csv(
        os.path.join(dir_salida, 'eventos.csv'), eventos,
        ['id_evento', 'id_seccion', 'id_profesor', 'duracion'],
    )
    escribir_csv(
        os.path.join(dir_salida, 'profesores.csv'), profesores,
        ['id_profesor', 'nombre', 'especialidad'],
    )
    escribir_csv(
        os.path.join(dir_salida, 'profesores_disponibilidad.csv'), disponibilidad,
        ['id_profesor', 'dia', 'franja_inicio', 'franja_fin'],
    )
    escribir_csv(
        os.path.join(dir_salida, 'salones.csv'), salones,
        ['id_salon', 'capacidad', 'es_virtual', 'caracteristicas'],
    )
    escribir_csv(
        os.path.join(dir_salida, 'curriculos.csv'), curriculos,
        ['id_curriculo', 'nombre'],
    )
    escribir_csv(
        os.path.join(dir_salida, 'curriculo_evento.csv'), asignaciones_curriculo_evento,
        ['id_curriculo', 'id_evento'],
    )

    print("\n[RESUMEN]")
    print(f"  Cursos:       {len(cursos)}")
    print(f"  Secciones:    {len(secciones)}")
    print(f"  Eventos:      {len(eventos)}")
    print(f"  Profesores:   {len(profesores)}")
    print(f"  Curriculos:   {len(curriculos)}")
    print(f"  Salones:      {len(salones)} (1 virtual + {len(salones)-1} fisicos)")
    print(f"  Tabla puente: {len(asignaciones_curriculo_evento)} asignaciones curriculo-evento")


if __name__ == '__main__':
    main()
