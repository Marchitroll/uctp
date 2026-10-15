"""Utilidades compartidas del ecosistema UCTP.

Centraliza lógica auxiliar duplicada previamente en múltiples archivos:
detección de escala, mapeos invertidos, metadatos de entorno,
carga de configuración institucional y exportación de matrices de horarios.
"""
import json
import os
import platform
from pathlib import Path

import pandas as pd
import psutil


def detectar_escala(K: list[str]) -> str:
    """Determina la escala de la instancia según la cantidad de currículos.

    Reglas:
        len(K) == 1          → 'pequena'
        len(K) in [4, 5]     → 'mediana'
        otro                 → 'grande'
    """
    if len(K) == 1:
        return "pequena"
    elif len(K) in [4, 5]:
        return "mediana"
    return "grande"


def construir_evento_profesor(E_p: dict[str, list[int]]) -> dict[int, str]:
    """Construye un diccionario inverso {evento: profesor} en O(|E|).

    Reemplaza el patrón O(|P|) repetido:
        next(prof for prof, evs in E_p.items() if e in evs)
    """
    return {e: p for p, eventos in E_p.items() for e in eventos}


def construir_franja_a_dia(T_d: dict[str, list[int]]) -> dict[int, str]:
    """Construye un diccionario {franja_global: día} para búsquedas en O(1).

    Reemplaza búsquedas lineales con next(d for d, slots in T_d.items() if t in slots).
    """
    return {t: dia for dia, franjas in T_d.items() for t in franjas}


def cargar_config_institucional(ruta: str = "config.json") -> dict:
    """Carga config.json como fuente única de verdad de la institución.

    Reemplaza reimplementaciones locales en varios módulos.
    """
    if not os.path.isabs(ruta):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        ruta_completa = os.path.join(base_dir, ruta)
        if os.path.exists(ruta_completa):
            ruta = ruta_completa

    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def obtener_metadatos_entorno(libreria_opt: str = None, version_opt: str = None) -> dict:
    """Retorna un diccionario estructurado con las especificaciones del entorno de ejecución.

    Garantiza trazabilidad y reproducibilidad experimental.
    """
    try:
        import mealpy
        mealpy_ver = getattr(mealpy, "__version__", "3.0.x")
    except Exception:
        mealpy_ver = "N/A"

    try:
        import mip
        mip_ver = getattr(mip, "__version__", "1.15.x")
    except Exception:
        mip_ver = "N/A"

    meta = {
        "sistema_operativo": f"{platform.system()} {platform.release()}",
        "procesador": platform.processor(),
        "ram_gb": round(psutil.virtual_memory().total / (1024.0 ** 3), 2),
        "version_python": platform.python_version(),
        "version_mip": mip_ver,
        "version_mealpy": mealpy_ver,
    }
    if libreria_opt:
        meta["libreria_optimizacion"] = libreria_opt
    if version_opt:
        meta["version_optimizacion"] = version_opt
    return meta


def exportar_matriz_horario_csv(clases: list[dict], horas_labels: list[str], D: list[str], filepath: str) -> None:
    """Exporta una lista de clases a una grilla horaria en formato CSV.

    Parámetros
    ----------
    clases : list[dict]
        Lista de diccionarios con claves 'dia', 'slot' e 'info'.
    horas_labels : list[str]
        Etiquetas de las franjas horarias (filas).
    D : list[str]
        Días de la semana (columnas).
    filepath : str
        Ruta del archivo CSV destino.
    """
    matriz = pd.DataFrame("---", index=horas_labels, columns=D)
    for clase in clases:
        dia = clase["dia"]
        slot = clase["slot"]
        info_str = clase["info"]

        if slot < len(horas_labels) and dia in D:
            celda_actual = matriz.at[horas_labels[slot], dia]
            if celda_actual == "---":
                matriz.at[horas_labels[slot], dia] = info_str
            else:
                matriz.at[horas_labels[slot], dia] = f"{celda_actual} | {info_str}"

    matriz.to_csv(filepath)
