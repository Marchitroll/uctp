"""Genera los archivos CSV del dataset UCTP (cursos, secciones, eventos, salones, profesores)."""
import argparse
import csv
import os
import random

from uctp_utils import cargar_config_institucional

MALLA_OBLIGATORIA = {
    'Nivel_03': [
        ('IA_Aplicada', 'mesa,pc'),
        ('Calculo_II', 'mesa'),
        ('Sist_Organizacionales', 'mesa'),
        ('Fisica_Sistemas', 'mesa'),
        ('Estr_Discretas', 'mesa'),
        ('Intro_Programacion', 'mesa,pc'),
    ],
    'Nivel_04': [
        ('Estadistica_Prob', 'mesa'),
        ('Calculo_III', 'mesa'),
        ('Mod_Integracion', 'mesa,pc'),
        ('Costeo_Operaciones', 'mesa'),
        ('POO', 'mesa,pc'),
        ('Arq_Computadoras', 'mesa,pc'),
    ],
    'Nivel_05': [
        ('Estadistica_Aplicada', 'mesa'),
        ('IO_I', 'mesa'),
        ('Sist_Operativos', 'mesa,pc'),
        ('Competencias_Gerenciales', 'mesa'),
        ('ED_I', 'mesa,pc'),
        ('Mod_BD', 'mesa,pc'),
    ],
    'Nivel_06': [
        ('Ing_Procesos_Negocio', 'mesa'),
        ('Redes', 'mesa,pc'),
        ('Simulacion', 'mesa,pc'),
        ('ED_II', 'mesa,pc'),
        ('Prog_Web', 'mesa,pc'),
        ('Gestion_Financiera', 'mesa'),
    ],
    'Nivel_07': [
        ('Sist_Intel_Empresarial', 'mesa,pc'),
        ('Gestion_Operaciones', 'mesa'),
        ('Ing_Software_I', 'mesa,pc'),
        ('Machine_Learning', 'mesa,pc'),
        ('Ciberseguridad', 'mesa,pc'),
    ],
    'Nivel_08': [
        ('Propuesta_Investigacion', 'mesa'),
        ('Sist_ERP', 'mesa,pc'),
        ('Auditoria_Control', 'mesa'),
        ('Ing_Software_II', 'mesa,pc'),
    ],
    'Nivel_09': [
        ('Seminario_I', 'mesa'),
        ('Plan_Estrategico', 'mesa'),
        ('Gestion_Proyectos', 'mesa'),
        ('Seg_Sistemas', 'mesa,pc'),
    ],
    'Nivel_10': [
        ('Seminario_II', 'mesa'),
        ('Gestion_Servicios_Dig', 'mesa'),
        ('Proy_Integrador', 'mesa,pc'),
    ],
}

ELECTIVOS = [
    ('Paradigmas_Prog', 'mesa,pc', 6),
    ('IoT', 'mesa,pc', 6),
    ('Gestion_BD', 'mesa,pc', 6),
    ('Ing_Conocimiento', 'mesa', 6),
    ('Sist_Distribuidos', 'mesa,pc', 6),
    ('Analitica_Negocios', 'mesa', 6),
    ('Cloud', 'mesa,pc', 6),
    ('Innovacion_Digital', 'mesa', 6),
    ('Proy_Videojuegos', 'mesa,pc', 6),
    ('HCI', 'mesa,pc', 6),
    ('Arq_TI', 'mesa', 6),
    ('DevOps', 'mesa,pc', 6),
    ('Arq_Software', 'mesa,pc', 6),
    ('Analisis_Algoritmos', 'mesa,pc', 7),
    ('Redes_Avanzadas', 'mesa,pc', 7),
    ('Prog_Movil', 'mesa,pc', 7),
    ('Seg_Salud_Ocup', 'mesa', 7),
    ('Deep_Learning', 'mesa,pc,deep_learning', 8),
    ('Topicos_Ciberseg', 'mesa,pc', 8),
    ('Analitica_BigData', 'mesa,pc', 8),
    ('Proy_Desarrollo_SW', 'mesa,pc', 9),
    ('Arq_Empresarial', 'mesa', 10),
]

SECCIONES_POR_CURSO = (1, 3)
EVENTOS_POR_SECCION = [2, 3]
DURACION_EVENTOS = [2, 3]
NUM_PROFESORES = 50
NUM_SALONES_FISICOS = 100
NUM_SALONES_CON_PC = 60
NUM_SALONES_DEEP_LEARNING = 1
CAPACIDAD_SALON_FISICO = 36
CAPACIDAD_VIRTUAL = 99999
LIMITE_HORAS_SEMANAL = 48
MIN_DIAS_PROFESOR = 4

PESOS_TURNOS = [30, 30, 40]
UMBRAL_COMPLETO_FRANJAS = 8
FRACCION_BLOQUE_TURNO = 0.7
LETRAS_SECCIONES = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
PROFES_PEQ_INSTANCIA = 15
SALONES_PEQ_INSTANCIA = 20
RATIO_SALONES_CON_PC = 0.6
ALUMNOS_POR_SECCION = (25, 36)
CARACTERISTICAS_POSIBLES = ['mesa', 'pc', 'deep_learning']

SEMILLA_PREDETERMINADA = 50
DIR_SALIDA_PREDETERMINADO = 'dataset'


def generar_cursos(malla: dict[str, list], electivos: list[tuple]) -> list[dict]:
    """Extrae la totalidad de asignaturas únicas combinando los cursos obligatorios y electivos."""
    cursos = []
    cursos_vistos = set()

    for nivel, lista_cursos in malla.items():
        for id_curso, requisitos in lista_cursos:
            if id_curso not in cursos_vistos:
                cursos_vistos.add(id_curso)
                cursos.append({
                    'id_curso': id_curso,
                    'requisitos': requisitos,
                })

    for id_curso, requisitos, _ in electivos:
        if id_curso not in cursos_vistos:
            cursos_vistos.add(id_curso)
            cursos.append({
                'id_curso': id_curso,
                'requisitos': requisitos,
            })

    return cursos


def generar_secciones(cursos: list[dict], rango_secciones: tuple[int, int], rango_alumnos: tuple[int, int]) -> list[dict]:
    """Genera secciones para cada curso."""
    secciones = []
    letras = LETRAS_SECCIONES
    for curso in cursos:
        num_secciones = random.randint(*rango_secciones)
        for indice_seccion in range(num_secciones):
            secciones.append({
                'id_seccion': f"{curso['id_curso']}_{letras[indice_seccion]}",
                'id_curso': curso['id_curso'],
                'num_alumnos': random.randint(*rango_alumnos),
            })
    return secciones


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


def generar_profesores(num_profesores: int) -> list[dict]:
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
    for indice_profesor in range(num_profesores):
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


def generar_eventos(secciones: list[dict], profesores: list[dict], rango_eventos: list[int], duraciones: list[int]) -> tuple[list[dict], dict[str, int]]:
    """Genera los eventos por sección y asigna docentes según especialidad y carga."""
    eventos = []
    id_evento = 1
    
    horas_profesor = {prof['id_profesor']: 0 for prof in profesores}
    cursos_por_profesor = {prof['id_profesor']: set() for prof in profesores}
    areas_por_profesor = {prof['id_profesor']: set() for prof in profesores}

    duraciones_por_curso = {}

    for seccion in secciones:
        id_curso = seccion['id_curso']
        if id_curso not in duraciones_por_curso:
            num_eventos = random.randint(*rango_eventos)
            duraciones_por_curso[id_curso] = [random.choice(duraciones) for _ in range(num_eventos)]

        duraciones_seccion = duraciones_por_curso[id_curso]
        total_horas_seccion = sum(duraciones_seccion)
        
        area = AREAS_CURSOS.get(id_curso, 'INGENIERIA_SOFTWARE')
        
        profesores_compatibles = [
            prof for prof in profesores 
            if area in COMPATIBILIDAD.get(prof['especialidad'], ['INGENIERIA_SOFTWARE'])
        ]
        if not profesores_compatibles:
            profesores_compatibles = profesores

        candidatos = [
            prof for prof in profesores_compatibles 
            if horas_profesor[prof['id_profesor']] + total_horas_seccion <= LIMITE_HORAS_SEMANAL
        ]
        if not candidatos:
            candidatos = profesores_compatibles
            
        candidatos_mismo_curso = [
            prof for prof in candidatos 
            if id_curso in cursos_por_profesor[prof['id_profesor']]
        ]
        candidatos_misma_area = [
            prof for prof in candidatos 
            if area in areas_por_profesor[prof['id_profesor']]
        ]
        
        if candidatos_mismo_curso:
            profesor_asignado_dict = min(candidatos_mismo_curso, key=lambda prof: horas_profesor[prof['id_profesor']])
        elif candidatos_misma_area:
            profesor_asignado_dict = min(candidatos_misma_area, key=lambda prof: horas_profesor[prof['id_profesor']])
        else:
            profesor_asignado_dict = min(candidatos, key=lambda prof: horas_profesor[prof['id_profesor']])
            
        profesor_asignado = profesor_asignado_dict['id_profesor']
        horas_profesor[profesor_asignado] += total_horas_seccion
        cursos_por_profesor[profesor_asignado].add(id_curso)
        areas_por_profesor[profesor_asignado].add(area)
        
        for duracion in duraciones_seccion:
            eventos.append({
                'id_evento': id_evento,
                'id_seccion': seccion['id_seccion'],
                'id_profesor': profesor_asignado,
                'duracion': duracion,
            })
            id_evento += 1

    return eventos, horas_profesor


def generar_curriculos(malla: dict[str, list], electivos: list[tuple], secciones: list[dict], eventos: list[dict]) -> tuple[list[dict], list[dict]]:
    """Genera currículos por nivel y la relación con sus eventos."""
    seccion_a_eventos = {}
    for evento in eventos:
        id_seccion = evento['id_seccion']
        if id_seccion not in seccion_a_eventos:
            seccion_a_eventos[id_seccion] = []
        seccion_a_eventos[id_seccion].append(evento['id_evento'])

    curso_a_secciones = {}
    for seccion in secciones:
        id_curso = seccion['id_curso']
        if id_curso not in curso_a_secciones:
            curso_a_secciones[id_curso] = []
        curso_a_secciones[id_curso].append(seccion['id_seccion'])

    niveles = sorted(malla.keys())
    curriculos = []
    asignaciones_curriculo_evento = []

    def agregar_curso_a_curriculo(nivel_id: str, id_curso: str):
        """Agrega los eventos del curso al currículo."""
        if id_curso in curso_a_secciones:
            for id_seccion in curso_a_secciones[id_curso]:
                if id_seccion in seccion_a_eventos:
                    for id_evento in seccion_a_eventos[id_seccion]:
                        asignaciones_curriculo_evento.append({
                            'id_curriculo': nivel_id,
                            'id_evento': id_evento,
                        })

    for nivel_id in niveles:
        num_nivel = int(nivel_id.split('_')[1])

        curriculos.append({
            'id_curriculo': nivel_id,
            'nombre': f"Ruta {nivel_id.replace('_', ' ')}",
        })

        for id_curso, _ in malla[nivel_id]:
            agregar_curso_a_curriculo(nivel_id, id_curso)

        for id_curso, _, nivel_minimo in electivos:
            if nivel_minimo <= num_nivel:
                agregar_curso_a_curriculo(nivel_id, id_curso)

    return curriculos, asignaciones_curriculo_evento


def generar_disponibilidad(profesores: list[dict], config: dict, horas_profesor: dict[str, int] = None) -> list[dict]:
    """Genera franjas de disponibilidad para cada docente según su carga."""
    disponibilidad = []
    dias = config['dias']
    dia_cierre = config['dia_cierre']

    franjas_por_dia_raw = config['franjas_por_dia']
    franjas_por_dia = franjas_por_dia_raw if isinstance(franjas_por_dia_raw, dict) else {dia: franjas_por_dia_raw for dia in dias}

    base_dia = {}
    cursor = 1
    for dia in dias:
        base_dia[dia] = cursor
        cursor += franjas_por_dia[dia]

    dias_habiles = [dia for dia in dias if dia != dia_cierre]

    for prof in profesores:
        id_profesor = prof['id_profesor']
        horas = horas_profesor.get(id_profesor, 0) if horas_profesor else 0

        if horas > 12:
            dias_disponibles = list(dias_habiles)
        else:
            num_dias = random.randint(MIN_DIAS_PROFESOR, len(dias_habiles))
            dias_disponibles = random.sample(dias_habiles, k=num_dias)

        dias_disponibles.append(dia_cierre)

        for dia in dias_disponibles:
            base = base_dia[dia]
            total_franjas_dia = franjas_por_dia[dia]

            if dia == dia_cierre or total_franjas_dia <= UMBRAL_COMPLETO_FRANJAS or horas > 12:
                turno = 'completo'
            else:
                turno = random.choices(['mañana', 'tarde', 'completo'], weights=PESOS_TURNOS, k=1)[0]

            if turno == 'mañana':
                franja_inicio = base
                franja_fin = base + int(total_franjas_dia * FRACCION_BLOQUE_TURNO) - 1
            elif turno == 'tarde':
                franja_inicio = base + total_franjas_dia - int(total_franjas_dia * FRACCION_BLOQUE_TURNO)
                franja_fin = base + total_franjas_dia - 1
            else:
                franja_inicio = base
                franja_fin = base + total_franjas_dia - 1

            disponibilidad.append({
                'id_profesor': prof['id_profesor'],
                'dia': dia,
                'franja_inicio': franja_inicio,
                'franja_fin': franja_fin,
            })

    return disponibilidad


def generar_salones(
    num_fisicos: int,
    num_con_pc: int,
    num_deep_learning: int,
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

    salon_id = 1

    for _ in range(num_deep_learning):
        salones.append({
            'id_salon': f"salon_{salon_id}",
            'capacidad': capacidad_fisica,
            'es_virtual': False,
            'caracteristicas': 'mesa,pc,deep_learning',
        })
        salon_id += 1

    for _ in range(num_con_pc - num_deep_learning):
        salones.append({
            'id_salon': f"salon_{salon_id}",
            'capacidad': capacidad_fisica,
            'es_virtual': False,
            'caracteristicas': 'mesa,pc',
        })
        salon_id += 1

    salones_tipicos = num_fisicos - num_con_pc
    for _ in range(salones_tipicos):
        salones.append({
            'id_salon': f"salon_{salon_id}",
            'capacidad': capacidad_fisica,
            'es_virtual': False,
            'caracteristicas': 'mesa',
        })
        salon_id += 1

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
        niveles_objetivo = sorted(MALLA_OBLIGATORIA.keys())[:1]
    elif instancia == "mediana":
        niveles_objetivo = sorted(MALLA_OBLIGATORIA.keys())[:4]
    else:
        niveles_objetivo = sorted(MALLA_OBLIGATORIA.keys())
    
    malla_reducida = {nivel: cursos for nivel, cursos in MALLA_OBLIGATORIA.items() if nivel in niveles_objetivo}
    max_nivel = max([int(nivel.split('_')[1]) for nivel in niveles_objetivo])
    electivos_reducidos = [electivo for electivo in ELECTIVOS if electivo[2] <= max_nivel]

    num_profs_instancia = PROFES_PEQ_INSTANCIA if len(niveles_objetivo) < 5 else NUM_PROFESORES
    num_salones_instancia = SALONES_PEQ_INSTANCIA if len(niveles_objetivo) < 5 else NUM_SALONES_FISICOS

    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    config = cargar_config_institucional(config_path)
    print(f"[INFO] Generando instancia para niveles: {niveles_objetivo}")

    cursos = generar_cursos(malla_reducida, electivos_reducidos)
    secciones = generar_secciones(cursos, SECCIONES_POR_CURSO, ALUMNOS_POR_SECCION)
    profesores = generar_profesores(num_profs_instancia)
    eventos, horas_prof = generar_eventos(secciones, profesores, EVENTOS_POR_SECCION, DURACION_EVENTOS)
    curriculos, asignaciones_curriculo_evento = generar_curriculos(malla_reducida, electivos_reducidos, secciones, eventos)
    
    disponibilidad = generar_disponibilidad(profesores, config, horas_prof)
    salones = generar_salones(
        num_salones_instancia, 
        int(num_salones_instancia * RATIO_SALONES_CON_PC),
        NUM_SALONES_DEEP_LEARNING, 
        CAPACIDAD_SALON_FISICO, 
        CAPACIDAD_VIRTUAL,
        CARACTERISTICAS_POSIBLES,
    )

    print("\n[INFO] Escribiendo archivos CSV...")
    escribir_csv(
        os.path.join(dir_salida, 'cursos.csv'), cursos,
        ['id_curso', 'requisitos'],
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
