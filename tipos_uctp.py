"""Estructuras de datos tipadas para el ecosistema UCTP."""
from dataclasses import dataclass


@dataclass(frozen=True)
class DatosUCTP:
    """Contenedor inmutable con los datos estructurados de una instancia UCTP."""

    dias: list[str]
    franjas_horarias: list[int]
    franjas_por_dia: dict[str, list[int]]
    dia_cierre_remoto: str
    almuerzo_por_dia: dict[str, int]

    salones: list[str]
    capacidad_por_salon: dict[str, int]
    es_virtual_por_salon: dict[str, bool]
    caracteristicas_por_salon: dict[str, list[str]]

    cursos: list[str]
    requisitos_por_curso: dict[str, list[str]]

    secciones: list[str]
    curso_por_seccion: dict[str, str]
    alumnos_por_seccion: dict[str, int]

    eventos: list[int]
    eventos_por_seccion: dict[str, list[int]]
    eventos_por_profesor: dict[str, list[int]]
    duracion_por_evento: dict[int, int]
    seccion_por_evento: dict[int, str]

    profesores: list[str]
    curriculos: list[str]
    eventos_por_curriculo: dict[str, list[int]]
    disponibilidad_por_profesor: dict[str, list[int]]

    caracteristicas: list[str]
    salon_tiene_caracteristica: dict[tuple[str, str], int]
    seccion_requiere_caracteristica: dict[tuple[str, str], int]
