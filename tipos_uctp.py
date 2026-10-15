"""Estructuras de datos tipadas para el ecosistema UCTP."""
from dataclasses import dataclass


@dataclass(frozen=True)
class DatosUCTP:
    """Contenedor inmutable con todos los datos de una instancia UCTP.

    Reemplaza la tupla posicional que retornaba ``cargar_datos_uctp()``,
    proporcionando acceso por nombre, autocompletado en IDE y tipado estático.
    """
    # --- Conjuntos principales (notación matemática estándar OR) ---
    D: list[str]                          # Días de la semana
    T: list[int]                          # Franjas horarias globales
    T_d: dict[str, list[int]]             # Franjas por día
    d_jue: str                            # Día de cierre institucional
    Almuerzo: dict[str, int]              # Franja de almuerzo por día

    R: list[str]                          # Salones
    CAP: dict[str, int]                   # Capacidad por salón
    ES_VIRTUAL: dict[str, bool]           # Virtualidad por salón
    CARACTERISTICAS: dict[str, list[str]] # Features por salón

    CURSOS: list[str]                     # Lista de cursos
    REQ_CURSO: dict[str, list[str]]       # Requisitos por curso

    S: list[str]                          # Secciones
    SECCION_CURSO: dict[str, str]         # Sección → Curso
    Alumno: dict[str, int]               # Alumnos inscritos por sección

    E: list[int]                          # Eventos
    E_s: dict[str, list[int]]             # Eventos por sección
    E_p: dict[str, list[int]]             # Eventos por profesor
    Dur: dict[int, int]                   # Duración por evento (horas)
    EVENTO_SECCION: dict[int, str]        # Evento → Sección

    P: list[str]                          # Profesores
    K: list[str]                          # Currículos
    E_k: dict[str, list[int]]             # Eventos por currículo
    Disp: dict[str, list[int]]           # Disponibilidad horaria por profesor

    F: list[str]                          # Características de salones
    Tiene: dict[tuple[str, str], int]     # (salon, feature) -> 0/1
    Req: dict[tuple[str, str], int]       # (seccion, feature) -> 0/1
