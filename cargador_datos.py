"""
cargador_datos.py
Módulo encargado exclusivamente de la lectura, procesamiento preliminar y estructuración
de los datos de entrada del problema UCTP desde archivos CSV y configuración JSON.
"""

import csv
import json
import os


def load_config(filepath):
    """
    Carga los parámetros institucionales desde un archivo JSON y deriva los conjuntos D, T, T_d, d_jue y Almuerzo.
    Soporta franjas heterogéneas, donde cada día puede tener un número diferente de franjas.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    D = cfg['dias']
    d_jue = cfg['dia_cierre']
    pos_almuerzo = cfg['posicion_almuerzo']
    dias_sin_almuerzo = set(cfg.get('dias_sin_almuerzo', []))

    # El parámetro franjas_por_dia puede ser un diccionario {dia: n} o un entero uniforme
    fpd_raw = cfg['franjas_por_dia']
    if isinstance(fpd_raw, dict):
        fpd = fpd_raw          # Asocia a cada día su respectivo número de franjas
    else:
        fpd = {dia: fpd_raw for dia in D}   # Mantiene la compatibilidad con versiones anteriores

    # Construye el conjunto T_d acumulando las franjas de cada día secuencialmente
    T_d = {}
    cursor = 1
    for dia in D:
        n = fpd[dia]
        T_d[dia] = list(range(cursor, cursor + n))
        cursor += n

    # Representa el conjunto global de todas las franjas horarias
    T = list(range(1, cursor))

    # Define el horario de almuerzo según la posición pos_almuerzo dentro de cada día (índice base 1)
    almuerzo_set = set()
    for dia in D:
        if dia in dias_sin_almuerzo:
            continue
        slots = T_d[dia]
        if pos_almuerzo <= len(slots):
            almuerzo_set.add(slots[pos_almuerzo - 1])
    Almuerzo = {t: (1 if t in almuerzo_set else 0) for t in T}

    return D, T, T_d, d_jue, Almuerzo


def load_rooms_data(filepath):
    """
    Carga los datos de los salones desde un archivo CSV y retorna R, CAP, ES_VIRTUAL y CARACTERISTICAS.
    """
    R = []
    CAP = {}
    ES_VIRTUAL = {}
    CARACTERISTICAS = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            r = row['id_salon'].strip()
            R.append(r)
            CAP[r] = int(row['capacidad'])
            ES_VIRTUAL[r] = row['es_virtual'].strip().lower() == 'true'
            CARACTERISTICAS[r] = [c.strip() for c in row['caracteristicas'].split(',')] if row['caracteristicas'].strip() else []
    return R, CAP, ES_VIRTUAL, CARACTERISTICAS


def load_cursos(filepath):
    """
    Carga los datos de los cursos y sus requisitos de infraestructura asociados.
    """
    CURSOS = []
    REQ_CURSO = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            id_curso = row['id_curso'].strip()
            CURSOS.append(id_curso)
            reqs = row['requisitos'].strip()
            REQ_CURSO[id_curso] = [r.strip() for r in reqs.split(',')] if reqs else []
    return CURSOS, REQ_CURSO


def load_secciones(filepath):
    """
    Carga las secciones académicas y retorna S, el mapeo seccion->curso y el número de alumnos por sección.
    """
    S = []
    SECCION_CURSO = {}
    Alumno = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            s = row['id_seccion'].strip()
            S.append(s)
            SECCION_CURSO[s] = row['id_curso'].strip()
            Alumno[s] = int(row['num_alumnos'])
    return S, SECCION_CURSO, Alumno


def load_eventos(filepath):
    """
    Carga los eventos de clase y retorna E, E_s, E_p, Dur y el mapeo evento->seccion.
    """
    E = []
    E_s = {}
    E_p = {}
    Dur = {}
    EVENTO_SECCION = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            e = int(row['id_evento'])
            s = row['id_seccion'].strip()
            p = row['id_profesor'].strip()
            d = int(row['duracion'])

            E.append(e)
            Dur[e] = d
            EVENTO_SECCION[e] = s

            # Agrupa los eventos correspondientes a cada sección
            if s not in E_s:
                E_s[s] = []
            E_s[s].append(e)

            # Agrupa los eventos correspondientes a cada profesor
            if p not in E_p:
                E_p[p] = []
            E_p[p].append(e)

    return E, E_s, E_p, Dur, EVENTO_SECCION


def load_curriculos(curriculos_path, bridge_path):
    """
    Carga los currículos académicos y la tabla puente, y retorna K y E_k.
    """
    K = []
    with open(curriculos_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            K.append(row['id_curriculo'].strip())

    E_k = {k: [] for k in K}
    with open(bridge_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            k = row['id_curriculo'].strip()
            e = int(row['id_evento'])
            if k in E_k:
                E_k[k].append(e)

    return K, E_k


def load_prof_availability(filepath, P, T):
    """
    Carga la disponibilidad horaria de los profesores y retorna la matriz binaria Disp.
    """
    Disp = {(p, t): 0 for p in P for t in T}
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            p = row['id_profesor'].strip()
            if p in P:
                f_inicio = int(row['franja_inicio'])
                f_fin = int(row['franja_fin'])
                for t in range(f_inicio, f_fin + 1):
                    if t in T:
                        Disp[(p, t)] = 1
    return Disp


def cargar_datos_uctp(data_dir='dataset'):
    """
    Carga la totalidad de conjuntos y parámetros requeridos para el modelo MIP
    desde los archivos JSON y CSV correspondientes dentro del directorio especificado.
    """
    D, T, T_d, d_jue, Almuerzo = load_config(os.path.join(os.path.dirname(__file__), 'config.json'))
    R, CAP, ES_VIRTUAL, CARACTERISTICAS = load_rooms_data(os.path.join(data_dir, 'salones.csv'))
    CURSOS, REQ_CURSO = load_cursos(os.path.join(data_dir, 'cursos.csv'))
    S, SECCION_CURSO, Alumno = load_secciones(os.path.join(data_dir, 'secciones.csv'))
    E, E_s, E_p, Dur, EVENTO_SECCION = load_eventos(os.path.join(data_dir, 'eventos.csv'))
    P = list(E_p.keys())
    K, E_k = load_curriculos(os.path.join(data_dir, 'curriculos.csv'), os.path.join(data_dir, 'curriculo_evento.csv'))
    Disp = load_prof_availability(os.path.join(data_dir, 'profesores_disponibilidad.csv'), P, T)

    # Define el conjunto general de características requeridas o poseídas (unión de cursos y salones)
    F = sorted(
        set(f for carac in CARACTERISTICAS.values() for f in carac if f)
        | set(f for reqs in REQ_CURSO.values() for f in reqs if f)
    )

    # Parámetros binarios Tiene y Req
    Tiene = {(r, f): 1 if f in CARACTERISTICAS[r] else 0 for r in R for f in F}
    Req = {(s, f): 1 if f in REQ_CURSO[SECCION_CURSO[s]] else 0 for s in S for f in F}

    # Agrupa los eventos por sección para su posterior uso en restricciones de espaciado
    Cursos_Agrupados = list(E_s.values())

    return (
        D, T, T_d, d_jue, Almuerzo,
        R, CAP, ES_VIRTUAL, CARACTERISTICAS,
        CURSOS, REQ_CURSO,
        S, SECCION_CURSO, Alumno,
        E, E_s, E_p, Dur, EVENTO_SECCION,
        P, K, E_k, Disp,
        F, Tiene, Req, Cursos_Agrupados
    )
