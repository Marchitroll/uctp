"""Módulo para la exportación de resultados y grillas de horarios del UCTP.

Genera archivos CSV desagregados por currículo y por camino de matrícula,
así como vistas de carga horaria por profesor y trazabilidad del entorno.
"""
import itertools
import json
import os
import pandas as pd

from uctp_utils import (
    construir_evento_profesor,
    construir_franja_a_dia,
    detectar_escala,
    exportar_matriz_horario_csv,
    obtener_metadatos_entorno,
)


def imprimir_metricas(status, cpu_time, model, nodes_explored=0):
    """Imprime métricas de trazabilidad y desempeño del modelo MIP."""
    bestcost = model.objective_value if model.num_solutions > 0 else float("nan")
    lowerbound = model.objective_bound if hasattr(model, "objective_bound") else float("nan")
    epsilon = 1e-10
    gap_pct = (
        ((bestcost - lowerbound) / (abs(bestcost) + epsilon)) * 100
        if model.num_solutions > 0
        else float("nan")
    )

    env = obtener_metadatos_entorno()
    print("\n" + "=" * 60)
    print(" [TRAZABILIDAD DEL ENTORNO]")
    print("=" * 60)
    print(f" Sistema Operativo : {env['sistema_operativo']}")
    print(f" Procesador        : {env['procesador']}")
    print(f" RAM Disponible    : {env['ram_gb']} GB")
    print(f" Versión Python    : {env['version_python']}")
    print(f" Versión Python-MIP: {env['version_mip']}")

    print("\n" + "=" * 60)
    print(" [MÉTRICAS DE EVALUACIÓN]")
    print("=" * 60)
    print(f" Estado Final (Status)      : {status.name if hasattr(status, 'name') else status}")
    print(f" Tiempo de Procesamiento CPU: {cpu_time:.2f} segundos")
    print(f" Nodos B&B Explorados       : {nodes_explored}")
    print(f" Valor Función Objetivo (Z) : {bestcost}")
    print(f" Límite Inferior (LB)       : {lowerbound}")
    print(f" Brecha de Optimalidad (Gap): {gap_pct:.4f} %")
    print("=" * 60 + "\n")


def exportar_metricas_mip(status, cpu_time, nodes_explored, model, K, output_dir=None):
    """Exporta las métricas de la corrida MIP a CSV y JSON bajo 'resultados_MIP/'."""
    if output_dir is None:
        escala = detectar_escala(K)
    else:
        escala = output_dir

    bestcost = model.objective_value if model.num_solutions > 0 else float("nan")
    lowerbound = model.objective_bound if hasattr(model, "objective_bound") else float("nan")
    epsilon = 1e-10
    gap_pct = (
        ((bestcost - lowerbound) / (abs(bestcost) + epsilon)) * 100
        if model.num_solutions > 0
        else float("nan")
    )
    status_str = status.name if hasattr(status, "name") else str(status)
    factible = (status_str in ["OPTIMAL", "FEASIBLE"] and model.num_solutions > 0)
    
    # Registro para CSV (formato de corrida individual compatible con metaheurísticas)
    row_csv = {
        "metodo": "MIP",
        "escala": escala,
        "Z": bestcost,
        "HCV": 0 if factible else 1,
        "tiempo_cpu": round(cpu_time, 4),
        "factible": factible,
        "nodos_explorados": nodes_explored,
        "limite_inferior": lowerbound,
        "brecha_pct": gap_pct,
        "estado": status_str,
    }

    # Registro para JSON resumen (esquema consolidado estándar idéntico a metaheurísticas)
    resumen_json = {
        "metodo": "MIP",
        "escala": escala,
        "mejor_z": bestcost,
        "peor_z": bestcost,
        "promedio_z": bestcost,
        "desviacion_z": 0.0,
        "mejor_df": 0 if factible else 1,
        "promedio_df": 0.0 if factible else 1.0,
        "tasa_factibilidad_final": 100.0 if factible else 0.0,
        "tiempo_cpu_promedio": round(cpu_time, 4),
        "TTF_promedio": round(cpu_time, 4) if factible else None,
        "evaluaciones_aptitud_promedio": 0,
        "nodos_explorados_promedio": nodes_explored,
        "limite_inferior": lowerbound,
        "brecha_pct": gap_pct,
        "estado": status_str,
        "entorno": obtener_metadatos_entorno("python-mip (HiGHS)"),
    }

    resultados_dir = "resultados_MIP"
    os.makedirs(resultados_dir, exist_ok=True)
    csv_filepath = os.path.join(resultados_dir, f"resultados_{escala}.csv")

    df = pd.DataFrame([row_csv])
    df.to_csv(csv_filepath, index=False)
    print(f"[ÉXITO] Métricas MIP persistidas en '{csv_filepath}'.")

    resumen_filepath = os.path.join(resultados_dir, f"resumen_{escala}.json")
    with open(resumen_filepath, "w", encoding="utf-8") as f:
        json.dump(resumen_json, f, indent=2, ensure_ascii=False)
    print(f"[ÉXITO] Resumen MIP guardado en '{resumen_filepath}'.")


def exportar_horarios(
    x, K, E_k, T_d, D, EVENTO_SECCION, SECCION_CURSO, E_p=None, output_dir=None, max_trayectos=20
):
    """Genera archivos CSV de horario desagregados por currículo y por camino de matrícula.

    Parámetros
    ----------
    x : dict
        Diccionario de asignaciones {(e, r, t): var_o_valor}.
    K : list
        Identificadores de currículos.
    E_k : dict
        Eventos por currículo {k: [eventos]}.
    T_d : dict
        Franjas por día {dia: [franjas]}.
    D : list
        Días de la semana.
    EVENTO_SECCION : dict
        Evento -> Sección.
    SECCION_CURSO : dict
        Sección -> Curso.
    E_p : dict, optional
        Eventos por profesor {p: [eventos]}.
    output_dir : str, optional
        Directorio destino. Si es None, se deduce de detectar_escala(K).
    max_trayectos : int
        Límite de caminos por currículo para evitar explosión combinatorial.
    """
    if output_dir is None or output_dir == "horarios_por_camino":
        escala = detectar_escala(K)
        output_dir = f"horarios_{escala}"

    os.makedirs(output_dir, exist_ok=True)

    max_slots = max(len(slots) for slots in T_d.values())
    horas_labels = [f"{7+i}:00 - {8+i}:00" for i in range(max_slots)]

    evento_profesor = construir_evento_profesor(E_p) if E_p is not None else {}
    franja_a_dia = construir_franja_a_dia(T_d)
    mapeo_profesor_horario = {}

    def esta_activo(val):
        return getattr(val, "x", val) >= 0.99

    # Recolectar asignaciones activas para profesores
    if E_p is not None:
        for (e, r, t), var in x.items():
            if esta_activo(var):
                profesor = evento_profesor.get(e)
                if profesor:
                    seccion = EVENTO_SECCION[e]
                    curso = SECCION_CURSO[seccion]
                    dia_actual = franja_a_dia.get(t)
                    if dia_actual and dia_actual in T_d:
                        slot_local = T_d[dia_actual].index(t)
                        if profesor not in mapeo_profesor_horario:
                            mapeo_profesor_horario[profesor] = []
                        mapeo_profesor_horario[profesor].append(
                            {"dia": dia_actual, "slot": slot_local, "info": f"{curso} ({seccion}) [{r}]"}
                        )

    # Recolectar asignaciones por currículo
    for k in K:
        secciones_activas_por_curso = {}
        mapeo_eventos_seccion = {}

        for (e, r, t), var in x.items():
            if esta_activo(var) and e in E_k[k]:
                seccion = EVENTO_SECCION[e]
                curso = SECCION_CURSO[seccion]
                dia_actual = franja_a_dia.get(t)
                if dia_actual and dia_actual in T_d:
                    slot_local = T_d[dia_actual].index(t)

                    if curso not in secciones_activas_por_curso:
                        secciones_activas_por_curso[curso] = set()
                    secciones_activas_por_curso[curso].add(seccion)

                    if seccion not in mapeo_eventos_seccion:
                        mapeo_eventos_seccion[seccion] = []

                    profesor = evento_profesor.get(e, "")
                    prof_suffix = f" - {profesor}" if profesor else ""
                    mapeo_eventos_seccion[seccion].append(
                        {
                            "dia": dia_actual,
                            "slot": slot_local,
                            "info": f"{curso} ({seccion}){prof_suffix} [{r}]",
                        }
                    )

        if not secciones_activas_por_curso:
            continue

        lista_cursos = list(secciones_activas_por_curso.keys())
        bloques_secciones = [list(secciones_activas_por_curso[c]) for c in lista_cursos]

        iterator = itertools.product(*bloques_secciones)
        caminos_matricula = []
        for idx, camino in enumerate(iterator):
            if idx >= max_trayectos:
                print(
                    f"[AVISO] Ciclo {k}: Se detectaron más de {max_trayectos} caminos. "
                    f"Se limita la exportación a los primeros {max_trayectos} para evitar proliferación de archivos."
                )
                break
            caminos_matricula.append(camino)

        ciclo_dir = os.path.join(output_dir, f"ciclo_{k}")
        os.makedirs(ciclo_dir, exist_ok=True)

        for idx, camino in enumerate(caminos_matricula, start=1):
            clases_camino = []
            for seccion in camino:
                clases_camino.extend(mapeo_eventos_seccion.get(seccion, []))

            file_path = os.path.join(ciclo_dir, f"camino_{idx}.csv")
            exportar_matriz_horario_csv(clases_camino, horas_labels, D, file_path)

        print(
            f"[INFO] Ciclo {k}: Generados {len(caminos_matricula)} caminos independientes en '{ciclo_dir.replace(os.sep, '/')}/'."
        )

    # Exportación de horarios docentes
    if E_p is not None and mapeo_profesor_horario:
        prof_dir = os.path.join(output_dir, "profesores")
        os.makedirs(prof_dir, exist_ok=True)
        for prof, clases in mapeo_profesor_horario.items():
            prof_file_path = os.path.join(prof_dir, f"{prof}.csv")
            exportar_matriz_horario_csv(clases, horas_labels, D, prof_file_path)
        print(
            f"[INFO] Exportados {len(mapeo_profesor_horario)} horarios de profesores en '{prof_dir.replace(os.sep, '/')}/'."
        )

    print(
        f"\n[ÉXITO] Exportación desagregada completada. Revisar el directorio '{output_dir.replace(os.sep, '/')}/'."
    )


def imprimir_metricas_metaheuristica(
    metodo, epoch, pop_size, crossover, selection, cpu_time, best_fitness, hard_violations, soft_penalty
):
    """Imprime métricas consolidadas de ejecución de una metaheurística."""
    env = obtener_metadatos_entorno()
    print("\n" + "=" * 60)
    print(f" [TRAZABILIDAD DEL ENTORNO - {metodo}]")
    print("=" * 60)
    print(f" Sistema Operativo       : {env['sistema_operativo']}")
    print(f" Procesador              : {env['procesador']}")
    print(f" RAM Disponible          : {env['ram_gb']} GB")
    print(f" Versión Python          : {env['version_python']}")
    print(f" Versión MEALPY          : {env['version_mealpy']}")

    print("\n" + "=" * 60)
    print(f" [MÉTRICAS DE RENDIMIENTO - {metodo}]")
    print("=" * 60)
    print(f" Generaciones (Epochs)   : {epoch}")
    print(f" Tamaño Población (Pop)  : {pop_size}")
    print(f" Crossover / Selección   : {crossover} / {selection}")
    print(f" Tiempo de Procesamiento : {cpu_time:.2f} segundos")
    print(f" Aptitud (Fitness) Total : {best_fitness:.4f}")
    print(f" Violaciones Duras (HCV) : {hard_violations}")
    print(f" Penalización Blanda (Z) : {soft_penalty}")
    print(f" Factible (HCV == 0)     : {'SI' if hard_violations == 0 else 'NO'}")
    print("=" * 60 + "\n")


imprimir_metricas_ga = imprimir_metricas_metaheuristica


def reconstruir_x_desde_vector(solution, valid_starts, E, Dur):
    """Convierte el vector de decisión discreto en un diccionario de variables {(e, r, t): 1.0}."""
    x_vec = {}
    for idx, e in enumerate(E):
        r, t_start = valid_starts[idx][int(solution[idx])]
        for offset in range(Dur[e]):
            x_vec[(e, r, t_start + offset)] = 1.0
    return x_vec
