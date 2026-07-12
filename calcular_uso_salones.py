import os
import glob
import json
import pandas as pd

def get_slots_config():
    config_path = "config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            fpd = cfg.get("franjas_por_dia", {})
            d_jue = cfg.get("dia_cierre", "Jueves")
            total_slots_all = sum(fpd.values())
            jueves_slots = fpd.get(d_jue, 14)
            physical_slots = total_slots_all - jueves_slots
            return jueves_slots, physical_slots
        except Exception:
            pass
    return 14, 64  # fallback default

def parse_salon_name(cell):
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
    print("\n" + "="*95)
    print(" CUADRO: PORCENTAJE DE OCUPACIÓN DE SALONES FÍSICOS (RESUMEN COMPARATIVO)")
    print("="*95)
    print(f" {'Escenario':<12} | {'Solucionador':<13} | {'Salones Físicos':<16} | {'Capacidad (slots)':<18} | {'Franjas Asignadas':<18} | {'Ocupación %':<12}")
    print("-" * 95)
    
    escalas_meta = {
        "pequena": {"nombre": "Pequeño", "salones_fisicos": 20, "slots_por_salon": physical_slots},
        "mediana": {"nombre": "Mediano", "salones_fisicos": 20, "slots_por_salon": physical_slots},
        "grande": {"nombre": "Grande", "salones_fisicos": 100, "slots_por_salon": physical_slots}
    }
    
    for escala_key, info in escalas_meta.items():
        for method in ["MIP", "GA"]:
            method_dir = os.path.join(f"horarios_{escala_key}", method)
            if os.path.exists(method_dir):
                counts = calcular_porcentaje_uso(method_dir)
                # Count only physical rooms (everything except 'r_virtual')
                physical_slots_assigned = sum(count for room, count in counts.items() if room != "r_virtual")
                
                num_physical = info["salones_fisicos"]
                capacidad_total = num_physical * info["slots_por_salon"]
                ocupacion_pct = (physical_slots_assigned / capacidad_total) * 100
                
                print(f" {info['nombre']:<12} | {method:<13} | {num_physical:<16d} | {capacidad_total:<18d} | {physical_slots_assigned:<18d} | {ocupacion_pct:<11.2f}%")
            else:
                # Si no existen los datos para este solucionador en esta escala, mostrar N/D
                num_physical = info["salones_fisicos"]
                capacidad_total = num_physical * info["slots_por_salon"]
                print(f" {info['nombre']:<12} | {method:<13} | {num_physical:<16d} | {capacidad_total:<18d} | {'N/D':<18} | {'N/D':<12}")
                
    print("="*95 + "\n")

    # -------------------------------------------------------------------------
    # 2. DETALLE PASO A PASO PARA EL ESCENARIO ACTIVO EN LA CARPETA 'dataset/'
    # -------------------------------------------------------------------------
    from cargador_datos import cargar_datos_uctp
    try:
        data = cargar_datos_uctp()
        R = data[5]
    except Exception:
        print("[AVISO] No se pudo cargar el dataset activo en la carpeta 'dataset/'. Saltando reporte detallado.")
        return
        
    salones_csv = os.path.join("dataset", "salones.csv")
    es_virtual = {}
    if os.path.exists(salones_csv):
        df_salones = pd.read_csv(salones_csv)
        for _, row in df_salones.iterrows():
            r = str(row['id_salon']).strip()
            is_v = str(row['es_virtual']).strip().lower() == 'true'
            es_virtual[r] = is_v

    # Determinar qué escala está activa basándose en len(data[20]) -> K
    K_len = len(data[20])
    if K_len == 1:
        escala_activa = "pequena"
        escala_nombre = "Pequeña"
    elif K_len in [4, 5]:
        escala_activa = "mediana"
        escala_nombre = "Mediana"
    else:
        escala_activa = "grande"
        escala_nombre = "Grande"

    print("="*80)
    print(f" DETALLE DE OCUPACIÓN POR SALÓN - ESCENARIO ACTIVO: {escala_nombre.upper()}")
    print("="*80)
    
    mip_dir = os.path.join(f"horarios_{escala_activa}", "MIP")
    mip_counts = calcular_porcentaje_uso(mip_dir) if os.path.exists(mip_dir) else {}
    
    ga_dir = os.path.join(f"horarios_{escala_activa}", "GA")
    ga_counts = calcular_porcentaje_uso(ga_dir) if os.path.exists(ga_dir) else {}
    
    all_rooms = sorted(list(R))
    
    total_operational_capacity = 0
    total_mip_slots = 0
    total_ga_slots = 0
    
    print(f" {'Salón':<12} | {'Tipo':<10} | {'MIP Slots':<10} | {'MIP Uso %':<10} | {'GA Slots':<10} | {'GA Uso %':<10}")
    print("-" * 75)
    
    for r in all_rooms:
        is_v = es_virtual.get(r, False)
        tipo = "Virtual" if is_v else "Físico"
        total_slots = jueves_slots if is_v else physical_slots
        total_operational_capacity += total_slots
        
        m_slots = mip_counts.get(r, 0)
        total_mip_slots += m_slots
        m_pct = (m_slots / total_slots) * 100
        
        g_slots = ga_counts.get(r, 0)
        total_ga_slots += g_slots
        g_pct = (g_slots / total_slots) * 100
        
        print(f" {r:<12} | {tipo:<10} | {m_slots:<10d} | {m_pct:<9.2f}% | {g_slots:<10d} | {g_pct:<9.2f}%")
        
    print("-" * 75)
    
    mip_overall_pct = (total_mip_slots / total_operational_capacity) * 100 if total_operational_capacity > 0 else 0
    ga_overall_pct = (total_ga_slots / total_operational_capacity) * 100 if total_operational_capacity > 0 else 0
    
    print(f" {'TOTAL GENERAL':<12} | {'-':<10} | {total_mip_slots:<10d} | {mip_overall_pct:<9.2f}% | {total_ga_slots:<10d} | {ga_overall_pct:<9.2f}%")
    print(f" Capacidad Operativa Total del Campus Activo: {total_operational_capacity} slots")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
