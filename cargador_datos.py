"""Carga y estructura los datos de entrada del UCTP desde CSV y config.json."""
import csv
import os

from tipos_uctp import DatosUCTP
from uctp_utils import cargar_config_institucional


def cargar_configuracion(ruta_archivo: str):
    """Carga la configuración institucional y deriva conjuntos temporales y franjas de almuerzo."""
    cfg = cargar_config_institucional(ruta_archivo)

    dias = cfg["dias"]
    dia_cierre_remoto = cfg["dia_cierre"]
    posicion_almuerzo = cfg["posicion_almuerzo"]
    dias_sin_almuerzo = set(cfg.get("dias_sin_almuerzo", []))
    franjas_por_dia_cfg = cfg["franjas_por_dia"]

    franjas_por_dia = {}
    cursor = 1
    for dia in dias:
        cantidad = franjas_por_dia_cfg[dia]
        franjas_por_dia[dia] = list(range(cursor, cursor + cantidad))
        cursor += cantidad

    franjas_horarias = list(range(1, cursor))

    almuerzo_set = set()
    for dia in dias:
        if dia in dias_sin_almuerzo:
            continue
        franjas_dia = franjas_por_dia[dia]
        if posicion_almuerzo <= len(franjas_dia):
            almuerzo_set.add(franjas_dia[posicion_almuerzo - 1])
    almuerzo_por_dia = {franja: (1 if franja in almuerzo_set else 0) for franja in franjas_horarias}

    return dias, franjas_horarias, franjas_por_dia, dia_cierre_remoto, almuerzo_por_dia


def cargar_datos_salones(ruta_archivo: str):
    """Carga los salones desde un archivo CSV con sus capacidades y atributos de equipamiento."""
    salones = []
    capacidad_por_salon = {}
    es_virtual_por_salon = {}
    caracteristicas_por_salon = {}
    with open(ruta_archivo, "r", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        for fila in lector:
            salon = fila["id_salon"].strip()
            salones.append(salon)
            capacidad_por_salon[salon] = int(fila["capacidad"])
            es_virtual_por_salon[salon] = fila["es_virtual"].strip().lower() == "true"
            texto_carac = fila["caracteristicas"].strip()
            caracteristicas_por_salon[salon] = [c.strip() for c in texto_carac.split(",")] if texto_carac else []
    return salones, capacidad_por_salon, es_virtual_por_salon, caracteristicas_por_salon


def cargar_cursos(ruta_archivo: str):
    """Carga cursos y sus requisitos de equipamiento."""
    cursos = []
    requisitos_por_curso = {}
    with open(ruta_archivo, "r", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        for fila in lector:
            id_curso = fila["id_curso"].strip()
            cursos.append(id_curso)
            reqs = fila["requisitos"].strip()
            requisitos_por_curso[id_curso] = [r.strip() for r in reqs.split(",")] if reqs else []
    return cursos, requisitos_por_curso


def cargar_secciones(ruta_archivo: str):
    """Carga secciones, curso asociado y alumnos inscritos."""
    secciones = []
    curso_por_seccion = {}
    alumnos_por_seccion = {}
    with open(ruta_archivo, "r", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        for fila in lector:
            seccion = fila["id_seccion"].strip()
            secciones.append(seccion)
            curso_por_seccion[seccion] = fila["id_curso"].strip()
            alumnos_por_seccion[seccion] = int(fila["num_alumnos"])
    return secciones, curso_por_seccion, alumnos_por_seccion


def cargar_eventos(ruta_archivo: str):
    """Carga eventos de clase, duraciones y asignaciones a sección y profesor."""
    eventos = []
    eventos_por_seccion = {}
    eventos_por_profesor = {}
    duracion_por_evento = {}
    seccion_por_evento = {}
    with open(ruta_archivo, "r", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        for fila in lector:
            evento = int(fila["id_evento"])
            seccion = fila["id_seccion"].strip()
            profesor = fila["id_profesor"].strip()
            duracion = int(fila["duracion"])

            eventos.append(evento)
            duracion_por_evento[evento] = duracion
            seccion_por_evento[evento] = seccion

            if seccion not in eventos_por_seccion:
                eventos_por_seccion[seccion] = []
            eventos_por_seccion[seccion].append(evento)

            if profesor not in eventos_por_profesor:
                eventos_por_profesor[profesor] = []
            eventos_por_profesor[profesor].append(evento)

    return eventos, eventos_por_seccion, eventos_por_profesor, duracion_por_evento, seccion_por_evento


def cargar_curriculos(ruta_curriculos: str, ruta_puente: str):
    """Carga currículos y la tabla puente currículo-evento."""
    curriculos = []
    with open(ruta_curriculos, "r", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        for fila in lector:
            curriculos.append(fila["id_curriculo"].strip())

    eventos_por_curriculo = {curriculo: [] for curriculo in curriculos}
    with open(ruta_puente, "r", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        for fila in lector:
            curriculo = fila["id_curriculo"].strip()
            evento = int(fila["id_evento"])
            if curriculo in eventos_por_curriculo:
                eventos_por_curriculo[curriculo].append(evento)

    return curriculos, eventos_por_curriculo


def cargar_disponibilidad_profesores(ruta_archivo: str, profesores: list[str], franjas_horarias: list[int]):
    """Carga la matriz binaria de disponibilidad docente."""
    disponibilidad_por_profesor = {(prof, franja): 0 for prof in profesores for franja in franjas_horarias}
    with open(ruta_archivo, "r", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        for fila in lector:
            profesor = fila["id_profesor"].strip()
            if profesor in profesores:
                inicio = int(fila["franja_inicio"])
                fin = int(fila["franja_fin"])
                for franja in range(inicio, fin + 1):
                    if franja in franjas_horarias:
                        disponibilidad_por_profesor[(profesor, franja)] = 1
    return disponibilidad_por_profesor


def cargar_datos_uctp(dir_datos: str = "dataset") -> DatosUCTP:
    """Carga todos los conjuntos y parámetros del problema UCTP."""
    dias, franjas_horarias, franjas_por_dia, dia_cierre_remoto, almuerzo_por_dia = cargar_configuracion(
        os.path.join(os.path.dirname(__file__), "config.json")
    )
    salones, capacidad_por_salon, es_virtual_por_salon, caracteristicas_por_salon = cargar_datos_salones(
        os.path.join(dir_datos, "salones.csv")
    )
    cursos, requisitos_por_curso = cargar_cursos(os.path.join(dir_datos, "cursos.csv"))
    secciones, curso_por_seccion, alumnos_por_seccion = cargar_secciones(os.path.join(dir_datos, "secciones.csv"))
    eventos, eventos_por_seccion, eventos_por_profesor, duracion_por_evento, seccion_por_evento = cargar_eventos(
        os.path.join(dir_datos, "eventos.csv")
    )
    profesores = list(eventos_por_profesor.keys())
    curriculos, eventos_por_curriculo = cargar_curriculos(
        os.path.join(dir_datos, "curriculos.csv"), os.path.join(dir_datos, "curriculo_evento.csv")
    )
    disponibilidad_por_profesor = cargar_disponibilidad_profesores(
        os.path.join(dir_datos, "profesores_disponibilidad.csv"), profesores, franjas_horarias
    )

    caracteristicas = sorted(
        set(carac for lista in caracteristicas_por_salon.values() for carac in lista if carac)
        | set(req for lista in requisitos_por_curso.values() for req in lista if req)
    )

    salon_tiene_caracteristica = {
        (salon, carac): 1 if carac in caracteristicas_por_salon[salon] else 0
        for salon in salones
        for carac in caracteristicas
    }
    seccion_requiere_caracteristica = {
        (seccion, carac): 1 if carac in requisitos_por_curso[curso_por_seccion[seccion]] else 0
        for seccion in secciones
        for carac in caracteristicas
    }

    return DatosUCTP(
        dias=dias,
        franjas_horarias=franjas_horarias,
        franjas_por_dia=franjas_por_dia,
        dia_cierre_remoto=dia_cierre_remoto,
        almuerzo_por_dia=almuerzo_por_dia,
        salones=salones,
        capacidad_por_salon=capacidad_por_salon,
        es_virtual_por_salon=es_virtual_por_salon,
        caracteristicas_por_salon=caracteristicas_por_salon,
        cursos=cursos,
        requisitos_por_curso=requisitos_por_curso,
        secciones=secciones,
        curso_por_seccion=curso_por_seccion,
        alumnos_por_seccion=alumnos_por_seccion,
        eventos=eventos,
        eventos_por_seccion=eventos_por_seccion,
        eventos_por_profesor=eventos_por_profesor,
        duracion_por_evento=duracion_por_evento,
        seccion_por_evento=seccion_por_evento,
        profesores=profesores,
        curriculos=curriculos,
        eventos_por_curriculo=eventos_por_curriculo,
        disponibilidad_por_profesor=disponibilidad_por_profesor,
        caracteristicas=caracteristicas,
        salon_tiene_caracteristica=salon_tiene_caracteristica,
        seccion_requiere_caracteristica=seccion_requiere_caracteristica,
    )
