"""Calcula y reporta el porcentaje y detalle de ocupación de salones físicos y virtuales."""
import glob
import os
import pandas as pd

from cargador_datos import cargar_datos_uctp
from uctp_utils import cargar_config_institucional, detectar_escala

METODOS = ["MIP", "HGA", "GA", "TS", "SA"]


def cargar_configuracion_franjas() -> tuple[int, int]:
    """Obtiene la configuración de franjas por día desde config.json."""
    try:
        config = cargar_config_institucional()
        franjas_por_dia = config.get("franjas_por_dia", {})
        dia_cierre_remoto = config.get("dia_cierre", "Jueves")
        total_franjas_semana = sum(franjas_por_dia.values())
        franjas_remotas = franjas_por_dia.get(dia_cierre_remoto, 15)
        franjas_presenciales = total_franjas_semana - franjas_remotas
        return franjas_remotas, franjas_presenciales
    except Exception as error:
        print(f"[AVISO] No se pudo cargar config.json: {error}")
        return 15, 71


def extraer_salones_de_celda(celda: str) -> list[str] | None:
    """Extrae los identificadores de salones asignados desde una celda del horario."""
    if not isinstance(celda, str) or celda == "---":
        return None
    salones = []
    partes = celda.split(" | ")
    for parte in partes:
        if "[" in parte and "]" in parte:
            salon = parte.split("[")[-1].split("]")[0].strip()
            salones.append(salon)
    return salones


def calcular_ocupacion_por_salon(dir_metodo: str) -> dict[str, int]:
    """Calcula el número de franjas ocupadas por salón a partir de los CSVs de profesores."""
    archivos_profesores = glob.glob(os.path.join(dir_metodo, "profesores", "Prof_*.csv"))
    if not archivos_profesores:
        return {}

    franjas_por_salon: dict[str, set[tuple[str, str]]] = {}
    for ruta_archivo in archivos_profesores:
        df_profesor = pd.read_csv(ruta_archivo, index_col=0)
        for etiqueta_franja, fila in df_profesor.iterrows():
            for dia, celda in fila.items():
                salones = extraer_salones_de_celda(celda)
                if salones:
                    for salon in salones:
                        if salon not in franjas_por_salon:
                            franjas_por_salon[salon] = set()
                        franjas_por_salon[salon].add((dia, str(etiqueta_franja)))

    return {salon: len(franjas) for salon, franjas in franjas_por_salon.items()}


def generar_reporte_ocupacion():
    """Genera y muestra por consola los cuadros resumen y detallado de ocupación de salones."""
    franjas_remotas, franjas_presenciales = cargar_configuracion_franjas()

    # 1. Ocupación física por método y escala
    print("\n" + "=" * 95)
    print(" CUADRO: PORCENTAJE DE OCUPACIÓN DE SALONES FÍSICOS (RESUMEN COMPARATIVO)")
    print("=" * 95)
    print(
        f" {'Escenario':<12} | {'Solucionador':<13} | {'Salones Físicos':<16} | {'Capacidad (slots)':<18} | {'Franjas Asignadas':<18} | {'Ocupación %':<12}"
    )
    print("-" * 95)

    configuracion_escalas = {
        "pequena_s1": {"nombre": "Pequeño (s1)", "salones_fisicos": 20, "slots_por_salon": franjas_presenciales},
        "pequena_s2": {"nombre": "Pequeño (s2)", "salones_fisicos": 20, "slots_por_salon": franjas_presenciales},
        "pequena_s3": {"nombre": "Pequeño (s3)", "salones_fisicos": 20, "slots_por_salon": franjas_presenciales},
        "pequena": {"nombre": "Pequeño", "salones_fisicos": 20, "slots_por_salon": franjas_presenciales},
        "mediana": {"nombre": "Mediano", "salones_fisicos": 20, "slots_por_salon": franjas_presenciales},
        "grande": {"nombre": "Grande", "salones_fisicos": 100, "slots_por_salon": franjas_presenciales},
    }

    for clave_escala, info_escala in configuracion_escalas.items():
        for metodo in METODOS:
            dir_metodo = os.path.join(f"horarios_{clave_escala}", metodo)
            salones_fisicos = info_escala["salones_fisicos"]
            capacidad_total = salones_fisicos * info_escala["slots_por_salon"]

            if os.path.exists(dir_metodo):
                conteo_ocupacion = calcular_ocupacion_por_salon(dir_metodo)
                franjas_fisicas_asignadas = sum(
                    conteo for salon, conteo in conteo_ocupacion.items() if salon != "r_virtual"
                )
                porcentaje_ocupacion = (franjas_fisicas_asignadas / capacidad_total) * 100
                print(
                    f" {info_escala['nombre']:<12} | {metodo:<13} | {salones_fisicos:<16d} | {capacidad_total:<18d} | {franjas_fisicas_asignadas:<18d} | {porcentaje_ocupacion:<11.2f}%"
                )
            else:
                print(
                    f" {info_escala['nombre']:<12} | {metodo:<13} | {salones_fisicos:<16d} | {capacidad_total:<18d} | {'N/D':<18} | {'N/D':<12}"
                )

    print("=" * 95 + "\n")

    # 2. Ocupación detallada por salón para la escala activa
    try:
        datos = cargar_datos_uctp()
        salones = datos.salones
        es_virtual_por_salon = datos.es_virtual_por_salon
    except Exception:
        print("[AVISO] No se pudo cargar el dataset activo en la carpeta 'dataset/'. Saltando reporte detallado.")
        return

    escala_activa = detectar_escala(datos.curriculos)
    nombre_escala = escala_activa.capitalize()

    conteos_por_metodo = {}
    for metodo in METODOS:
        dir_metodo = os.path.join(f"horarios_{escala_activa}", metodo)
        conteos_por_metodo[metodo] = (
            calcular_ocupacion_por_salon(dir_metodo) if os.path.exists(dir_metodo) else None
        )

    todos_los_salones = sorted(list(salones))
    totales_franjas = {metodo: 0 for metodo in METODOS}
    capacidad_operativa_total = 0

    encabezado_metodos = " | ".join(f"{metodo:^12}" for metodo in METODOS)
    subencabezado = " | ".join(f"{'Slots (%)':^12}" for _ in METODOS)
    ancho_linea = 26 + 15 * len(METODOS)

    print("=" * ancho_linea)
    print(f" DETALLE DE OCUPACIÓN POR SALÓN - ESCENARIO ACTIVO: {nombre_escala.upper()}")
    print("=" * ancho_linea)
    print(f" {'Salón':<12} | {'Tipo':<8} | {encabezado_metodos}")
    print(f" {'':<12} | {'':<8} | {subencabezado}")
    print("-" * ancho_linea)

    for salon in todos_los_salones:
        es_virtual = es_virtual_por_salon.get(salon, False)
        tipo = "Virtual" if es_virtual else "Físico"
        total_franjas_salon = franjas_remotas if es_virtual else franjas_presenciales
        capacidad_operativa_total += total_franjas_salon

        celdas_metodos = []
        for metodo in METODOS:
            conteo_metodo = conteos_por_metodo[metodo]
            if conteo_metodo is not None:
                franjas_ocupadas = conteo_metodo.get(salon, 0)
                totales_franjas[metodo] += franjas_ocupadas
                porcentaje = (franjas_ocupadas / total_franjas_salon) * 100
                celdas_metodos.append(f"{franjas_ocupadas:2d} ({porcentaje:5.1f}%)")
            else:
                celdas_metodos.append(f"{'N/D':^12}")
        fila_metodos = " | ".join(celdas_metodos)
        print(f" {salon:<12} | {tipo:<8} | {fila_metodos}")

    print("-" * ancho_linea)
    celdas_totales = []
    for metodo in METODOS:
        if conteos_por_metodo[metodo] is not None:
            total_asignado = totales_franjas[metodo]
            porcentaje_total = (
                (total_asignado / capacidad_operativa_total) * 100
                if capacidad_operativa_total > 0
                else 0
            )
            celdas_totales.append(f"{total_asignado:3d} ({porcentaje_total:5.1f}%)")
        else:
            celdas_totales.append(f"{'N/D':^12}")
    fila_totales = " | ".join(celdas_totales)
    print(f" {'TOTAL':<12} | {'':<8} | {fila_totales}")
    print("=" * ancho_linea + "\n")


def main():
    generar_reporte_ocupacion()


if __name__ == "__main__":
    main()
