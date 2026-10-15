import glob
import os
import pandas as pd

from uctp_utils import cargar_config_institucional, detectar_escala
from cargador_datos import cargar_datos_uctp

METODOS = ["MIP", "HGA", "GA", "TS", "SA"]


def get_slots_config():
    """Obtiene la configuración de franjas por día desde config.json."""
    try:
        cfg = cargar_config_institucional()
        fpd = cfg.get("franjas_por_dia", {})
        d_jue = cfg.get("dia_cierre", "Jueves")
        total_slots_all = sum(fpd.values())
        jueves_slots = fpd.get(d_jue, 15)
        physical_slots = total_slots_all - jueves_slots
        return jueves_slots, physical_slots
    except Exception as e:
        print(f"[AVISO] No se pudo cargar config.json: {e}")
        return 15, 71


def parse_salon_name(cell):
    """Extrae los identificadores de salones asignados desde una celda del horario."""
    if not isinstance(cell, str) or cell == "---":
        return None
    salones = []
    parts = cell.split(" | ")
    for part in parts:
        if "[" in part and "]" in part:
            salon = part.split("[")[-1].split("]")[0].strip()
            salones.append(salon)
    return salones


def calcular_porcentaje_uso(method_dir):
    """Calcula el número de franjas ocupadas por salón a partir de los CSVs de profesores."""
    prof_files = glob.glob(os.path.join(method_dir, "profesores", "Prof_*.csv"))
    if not prof_files:
        return {}
    
    room_slots = {}
    for file in prof_files:
        df = pd.read_csv(file, index_col=0)
        for slot_label, row in df.iterrows():
            for dia, cell in row.items():
                salones = parse_salon_name(cell)
                if salones:
                    for salon in salones:
                        if salon not in room_slots:
                            room_slots[salon] = set()
                        room_slots[salon].add((dia, slot_label))
                        
    return {room: len(slots) for room, slots in room_slots.items()}


def main():
    jueves_slots, physical_slots = get_slots_config()
    
    # -------------------------------------------------------------------------
    # 1. TABLA CONSOLIDADA GENERAL DE OCUPACIÓN FÍSICA (PARA TODOS LOS ESCENARIOS)
    # -------------------------------------------------------------------------
    print("\n" + "=" * 95)
    print(" CUADRO: PORCENTAJE DE OCUPACIÓN DE SALONES FÍSICOS (RESUMEN COMPARATIVO)")
    print("=" * 95)
    print(f" {'Escenario':<12} | {'Solucionador':<13} | {'Salones Físicos':<16} | {'Capacidad (slots)':<18} | {'Franjas Asignadas':<18} | {'Ocupación %':<12}")
    print("-" * 95)
    
    escalas_meta = {
        "pequena": {"nombre": "Pequeño", "salones_fisicos": 20, "slots_por_salon": physical_slots},
        "mediana": {"nombre": "Mediano", "salones_fisicos": 20, "slots_por_salon": physical_slots},
        "grande": {"nombre": "Grande", "salones_fisicos": 100, "slots_por_salon": physical_slots}
    }
    
    for escala_key, info in escalas_meta.items():
        for method in METODOS:
            method_dir = os.path.join(f"horarios_{escala_key}", method)
            num_physical = info["salones_fisicos"]
            capacidad_total = num_physical * info["slots_por_salon"]

            if os.path.exists(method_dir):
                counts = calcular_porcentaje_uso(method_dir)
                physical_slots_assigned = sum(count for room, count in counts.items() if room != "r_virtual")
                ocupacion_pct = (physical_slots_assigned / capacidad_total) * 100
                print(f" {info['nombre']:<12} | {method:<13} | {num_physical:<16d} | {capacidad_total:<18d} | {physical_slots_assigned:<18d} | {ocupacion_pct:<11.2f}%")
            else:
                print(f" {info['nombre']:<12} | {method:<13} | {num_physical:<16d} | {capacidad_total:<18d} | {'N/D':<18} | {'N/D':<12}")
                
    print("=" * 95 + "\n")

    # -------------------------------------------------------------------------
    # 2. DETALLE PASO A PASO PARA EL ESCENARIO ACTIVO EN LA CARPETA 'dataset/'
    # -------------------------------------------------------------------------
    try:
        datos = cargar_datos_uctp()
        R = datos.R
        es_virtual = datos.ES_VIRTUAL
    except Exception:
        print("[AVISO] No se pudo cargar el dataset activo en la carpeta 'dataset/'. Saltando reporte detallado.")
        return

    escala_activa = detectar_escala(datos.K)
    escala_nombre = escala_activa.capitalize()

    metodos_counts = {}
    for m in METODOS:
        m_dir = os.path.join(f"horarios_{escala_activa}", m)
        metodos_counts[m] = calcular_porcentaje_uso(m_dir) if os.path.exists(m_dir) else None

    all_rooms = sorted(list(R))
    totales_slots = {m: 0 for m in METODOS}
    total_operational_capacity = 0

    header_metodos = " | ".join(f"{m:^12}" for m in METODOS)
    sub_header = " | ".join(f"{'Slots (%)':^12}" for _ in METODOS)
    linea_ancho = 26 + 15 * len(METODOS)

    print("=" * linea_ancho)
    print(f" DETALLE DE OCUPACIÓN POR SALÓN - ESCENARIO ACTIVO: {escala_nombre.upper()}")
    print("=" * linea_ancho)
    print(f" {'Salón':<12} | {'Tipo':<8} | {header_metodos}")
    print(f" {'':<12} | {'':<8} | {sub_header}")
    print("-" * linea_ancho)

    for r in all_rooms:
        is_v = es_virtual.get(r, False)
        tipo = "Virtual" if is_v else "Físico"
        total_slots = jueves_slots if is_v else physical_slots
        total_operational_capacity += total_slots
        
        celdas = []
        for m in METODOS:
            counts = metodos_counts[m]
            if counts is not None:
                slots = counts.get(r, 0)
                totales_slots[m] += slots
                pct = (slots / total_slots) * 100
                celdas.append(f"{slots:2d} ({pct:5.1f}%)")
            else:
                celdas.append(f"{'N/D':^12}")
        fila_metodos = " | ".join(celdas)
        print(f" {r:<12} | {tipo:<8} | {fila_metodos}")

    print("-" * linea_ancho)
    celdas_totales = []
    for m in METODOS:
        if metodos_counts[m] is not None:
            tot = totales_slots[m]
            pct = (tot / total_operational_capacity) * 100 if total_operational_capacity > 0 else 0
            celdas_totales.append(f"{tot:3d} ({pct:5.1f}%)")
        else:
            celdas_totales.append(f"{'N/D':^12}")
    fila_totales = " | ".join(celdas_totales)
    print(f" {'TOTAL':<12} | {'-':<8} | {fila_totales}")
    print(f" Capacidad Operativa Total del Campus Activo: {total_operational_capacity} slots")
    print("=" * linea_ancho + "\n")


if __name__ == "__main__":
    main()
