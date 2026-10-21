"""Funciones de utilidad compartidas para el proyecto UCTP."""
import json
import os
import platform

import pandas as pd
import psutil


def detectar_escala(curriculos: list[str]) -> str:
    """Determina la escala de la instancia según la cantidad de currículos."""
    if len(curriculos) == 1:
        return "pequena"
    elif len(curriculos) in [4, 5]:
        return "mediana"
    return "grande"


def construir_evento_profesor(eventos_por_profesor: dict[str, list[int]]) -> dict[int, str]:
    """Construye un diccionario inverso {evento: profesor}."""
    return {evento: prof for prof, eventos in eventos_por_profesor.items() for evento in eventos}


def construir_franja_a_dia(franjas_por_dia: dict[str, list[int]]) -> dict[int, str]:
    """Construye un diccionario {franja_global: día}."""
    return {franja: dia for dia, franjas in franjas_por_dia.items() for franja in franjas}


def cargar_config_institucional(ruta: str = "config.json") -> dict:
    """Carga la configuración institucional desde config.json."""
    if not os.path.isabs(ruta):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        ruta_completa = os.path.join(base_dir, ruta)
        if os.path.exists(ruta_completa):
            ruta = ruta_completa

    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def obtener_metadatos_entorno(libreria_opt: str = None, version_opt: str = None) -> dict:
    """Retorna metadatos del entorno de ejecución para trazabilidad."""
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


def exportar_matriz_horario_csv(clases: list[dict], etiquetas_horas: list[str], dias: list[str], ruta_archivo: str) -> None:
    """Exporta una lista de clases a una matriz horaria en CSV."""
    matriz = pd.DataFrame("---", index=etiquetas_horas, columns=dias)
    for clase in clases:
        dia = clase["dia"]
        slot = clase["slot"]
        info_str = clase["info"]

        if slot < len(etiquetas_horas) and dia in dias:
            celda_actual = matriz.at[etiquetas_horas[slot], dia]
            if celda_actual == "---":
                matriz.at[etiquetas_horas[slot], dia] = info_str
            else:
                matriz.at[etiquetas_horas[slot], dia] = f"{celda_actual} | {info_str}"

    matriz.to_csv(ruta_archivo)
