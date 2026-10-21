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


def imprimir_metricas(estado, tiempo_cpu: float, modelo, nodos_explorados: int = 0):
    """Imprime métricas de trazabilidad y desempeño del modelo MIP."""
    mejor_costo = modelo.objective_value if modelo.num_solutions > 0 else float("nan")
    limite_inferior = modelo.objective_bound if hasattr(modelo, "objective_bound") else float("nan")
    epsilon = 1e-10
    brecha_porcentaje = (
        ((mejor_costo - limite_inferior) / (abs(mejor_costo) + epsilon)) * 100
        if modelo.num_solutions > 0
        else float("nan")
    )

    entorno = obtener_metadatos_entorno()
    print("\n" + "=" * 60)
    print(" [TRAZABILIDAD DEL ENTORNO]")
    print("=" * 60)
    print(f" Sistema Operativo : {entorno['sistema_operativo']}")
    print(f" Procesador        : {entorno['procesador']}")
    print(f" RAM Disponible    : {entorno['ram_gb']} GB")
    print(f" Versión Python    : {entorno['version_python']}")
    print(f" Versión Python-MIP: {entorno['version_mip']}")

    print("\n" + "=" * 60)
    print(" [MÉTRICAS DE EVALUACIÓN]")
    print("=" * 60)
    print(f" Estado Final (Status)      : {estado.name if hasattr(estado, 'name') else estado}")
    print(f" Tiempo de Procesamiento CPU: {tiempo_cpu:.2f} segundos")
    print(f" Nodos B&B Explorados       : {nodos_explorados}")
    print(f" Valor Función Objetivo (Z) : {mejor_costo}")
    print(f" Límite Inferior (LB)       : {limite_inferior}")
    print(f" Brecha de Optimalidad (Gap): {brecha_porcentaje:.4f} %")
    print("=" * 60 + "\n")


def exportar_metricas_mip(
    estado,
    tiempo_cpu: float,
    nodos_explorados: int,
    modelo,
    curriculos: list[str],
    dir_salida: str = None,
    desglose_penalizaciones: dict = None,
):
    """Exporta las métricas de la corrida MIP a CSV y JSON bajo 'resultados_MIP/'."""
    if dir_salida is None:
        escala = detectar_escala(curriculos)
    else:
        escala = dir_salida

    mejor_costo = modelo.objective_value if modelo.num_solutions > 0 else float("nan")
    limite_inferior = modelo.objective_bound if hasattr(modelo, "objective_bound") else float("nan")
    epsilon = 1e-10
    brecha_porcentaje = (
        ((mejor_costo - limite_inferior) / (abs(mejor_costo) + epsilon)) * 100
        if modelo.num_solutions > 0
        else float("nan")
    )
    estado_cadena = estado.name if hasattr(estado, "name") else str(estado)
    factible = estado_cadena in ["OPTIMAL", "FEASIBLE"] and modelo.num_solutions > 0

    fila_csv = {
        "metodo": "MIP",
        "escala": escala,
        "Z": mejor_costo,
        "HCV": 0 if factible else 1,
        "tiempo_cpu": round(tiempo_cpu, 4),
        "factible": factible,
        "nodos_explorados": nodos_explorados,
        "limite_inferior": limite_inferior,
        "brecha_pct": brecha_porcentaje,
        "estado": estado_cadena,
    }
    if desglose_penalizaciones:
        fila_csv.update(desglose_penalizaciones)

    resumen_json = {
        "metodo": "MIP",
        "escala": escala,
        "mejor_z": mejor_costo,
        "peor_z": mejor_costo,
        "promedio_z": mejor_costo,
        "desviacion_z": 0.0,
        "mejor_df": 0 if factible else 1,
        "promedio_df": 0.0 if factible else 1.0,
        "tasa_factibilidad_final": 100.0 if factible else 0.0,
        "tiempo_cpu_promedio": round(tiempo_cpu, 4),
        "TTF_promedio": round(tiempo_cpu, 4) if factible else None,
        "evaluaciones_aptitud_promedio": 0,
        "nodos_explorados_promedio": nodos_explorados,
        "limite_inferior": limite_inferior,
        "brecha_pct": brecha_porcentaje,
        "estado": estado_cadena,
        "entorno": obtener_metadatos_entorno("python-mip (HiGHS)"),
    }
    if desglose_penalizaciones:
        resumen_json.update(desglose_penalizaciones)

    resultados_dir = "resultados_MIP"
    os.makedirs(resultados_dir, exist_ok=True)
    ruta_csv = os.path.join(resultados_dir, f"resultados_{escala}.csv")

    df = pd.DataFrame([fila_csv])
    df.to_csv(ruta_csv, index=False)
    print(f"[ÉXITO] Métricas MIP persistidas en '{ruta_csv}'.")

    ruta_resumen = os.path.join(resultados_dir, f"resumen_{escala}.json")
    with open(ruta_resumen, "w", encoding="utf-8") as archivo:
        json.dump(resumen_json, archivo, indent=2, ensure_ascii=False)
    print(f"[ÉXITO] Resumen MIP guardado en '{ruta_resumen}'.")


def exportar_horarios(
    asignaciones: dict,
    curriculos: list[str],
    eventos_por_curriculo: dict[str, list[int]],
    franjas_por_dia: dict[str, list[int]],
    dias: list[str],
    seccion_por_evento: dict[int, str],
    curso_por_seccion: dict[str, str],
    eventos_por_profesor: dict[str, list[int]] = None,
    dir_salida: str = None,
    max_trayectos: int = 20,
):
    """Genera archivos CSV de horario desagregados por currículo y por camino de matrícula."""
    if dir_salida is None or dir_salida == "horarios_por_camino":
        escala = detectar_escala(curriculos)
        dir_salida = f"horarios_{escala}"

    os.makedirs(dir_salida, exist_ok=True)

    max_franjas = max(len(franjas) for franjas in franjas_por_dia.values())
    etiquetas_horas = [f"{7+i}:00 - {8+i}:00" for i in range(max_franjas)]

    evento_a_profesor = construir_evento_profesor(eventos_por_profesor) if eventos_por_profesor is not None else {}
    franja_a_dia = construir_franja_a_dia(franjas_por_dia)
    mapeo_profesor_horario = {}

    def esta_activo(val):
        return getattr(val, "x", val) >= 0.99

    if eventos_por_profesor is not None:
        for (evento, salon, franja), variable in asignaciones.items():
            if esta_activo(variable):
                profesor = evento_a_profesor.get(evento)
                if profesor:
                    seccion = seccion_por_evento[evento]
                    curso = curso_por_seccion[seccion]
                    dia_actual = franja_a_dia.get(franja)
                    if dia_actual and dia_actual in franjas_por_dia:
                        franja_local = franjas_por_dia[dia_actual].index(franja)
                        if profesor not in mapeo_profesor_horario:
                            mapeo_profesor_horario[profesor] = []
                        mapeo_profesor_horario[profesor].append(
                            {"dia": dia_actual, "slot": franja_local, "info": f"{curso} ({seccion}) [{salon}]"}
                        )

    # Exportación por currículo
    for curriculo in curriculos:
        eventos_curr = eventos_por_curriculo.get(curriculo, [])
        secciones_curr = sorted(list(set(seccion_por_evento[e] for e in eventos_curr if e in seccion_por_evento)))

        cursos_dict = {}
        for seccion in secciones_curr:
            curso = curso_por_seccion[seccion]
            if curso not in cursos_dict:
                cursos_dict[curso] = []
            cursos_dict[curso].append(seccion)

        cursos_ordenados = sorted(cursos_dict.keys())
        combinaciones_secciones = [cursos_dict[c] for c in cursos_ordenados]

        caminos_matricula = []
        for combinacion in itertools.product(*combinaciones_secciones):
            caminos_matricula.append(combinacion)
            if len(caminos_matricula) >= max_trayectos:
                break

        ciclo_dir = os.path.join(dir_salida, f"ciclo_{curriculo}")
        os.makedirs(ciclo_dir, exist_ok=True)

        mapeo_eventos_seccion = {}
        for (evento, salon, franja), variable in asignaciones.items():
            if esta_activo(variable) and evento in eventos_curr:
                seccion = seccion_por_evento[evento]
                curso = curso_por_seccion[seccion]
                dia_actual = franja_a_dia.get(franja)
                if dia_actual and dia_actual in franjas_por_dia:
                    franja_local = franjas_por_dia[dia_actual].index(franja)
                    if seccion not in mapeo_eventos_seccion:
                        mapeo_eventos_seccion[seccion] = []
                    mapeo_eventos_seccion[seccion].append(
                        {"dia": dia_actual, "slot": franja_local, "info": f"{curso} ({seccion}) [{salon}]"}
                    )

        for idx, camino in enumerate(caminos_matricula, start=1):
            clases_camino = []
            for seccion in camino:
                clases_camino.extend(mapeo_eventos_seccion.get(seccion, []))

            ruta_archivo = os.path.join(ciclo_dir, f"camino_{idx}.csv")
            exportar_matriz_horario_csv(clases_camino, etiquetas_horas, dias, ruta_archivo)

        print(
            f"[INFO] Ciclo {curriculo}: Generados {len(caminos_matricula)} caminos independientes en '{ciclo_dir.replace(os.sep, '/')}/'."
        )

    if eventos_por_profesor is not None and mapeo_profesor_horario:
        prof_dir = os.path.join(dir_salida, "profesores")
        os.makedirs(prof_dir, exist_ok=True)
        for prof, clases in mapeo_profesor_horario.items():
            ruta_archivo_prof = os.path.join(prof_dir, f"{prof}.csv")
            exportar_matriz_horario_csv(clases, etiquetas_horas, dias, ruta_archivo_prof)
        print(
            f"[INFO] Exportados {len(mapeo_profesor_horario)} horarios de profesores en '{prof_dir.replace(os.sep, '/')}/'."
        )

    print(
        f"\n[ÉXITO] Exportación desagregada completada. Revisar el directorio '{dir_salida.replace(os.sep, '/')}/'."
    )


def imprimir_metricas_metaheuristica(
    metodo: str,
    epoca: int,
    tam_poblacion: int,
    cruce: str,
    seleccion: str,
    tiempo_cpu: float,
    mejor_fitness: float,
    violaciones_duras: int,
    penalizacion_blanda: float,
):
    """Imprime las métricas de ejecución de la metaheurística."""
    entorno = obtener_metadatos_entorno()
    print("\n" + "=" * 60)
    print(f" [TRAZABILIDAD DEL ENTORNO - {metodo}]")
    print("=" * 60)
    print(f" Sistema Operativo       : {entorno['sistema_operativo']}")
    print(f" Procesador              : {entorno['procesador']}")
    print(f" RAM Disponible          : {entorno['ram_gb']} GB")
    print(f" Versión Python          : {entorno['version_python']}")
    print(f" Versión MEALPY          : {entorno['version_mealpy']}")

    print("\n" + "=" * 60)
    print(f" [MÉTRICAS DE RENDIMIENTO - {metodo}]")
    print("=" * 60)
    print(f" Generaciones (Epochs)   : {epoca}")
    print(f" Tamaño Población (Pop)  : {tam_poblacion}")
    print(f" Crossover / Selección   : {cruce} / {seleccion}")
    print(f" Tiempo de Procesamiento : {tiempo_cpu:.2f} segundos")
    print(f" Aptitud (Fitness) Total : {mejor_fitness:.4f}")
    print(f" Violaciones Duras (HCV) : {violaciones_duras}")
    print(f" Penalización Blanda (Z) : {penalizacion_blanda}")
    print(f" Factible (HCV == 0)     : {'SÍ' if violaciones_duras == 0 else 'NO'}")
    print("=" * 60 + "\n")


def reconstruir_asignaciones_desde_vector(
    solucion: list, inicios_validos: dict, eventos: list[int], duracion_por_evento: dict[int, int]
) -> dict:
    """Convierte el vector de decisión discreto en asignaciones {(evento, salon, franja): 1.0}."""
    asignaciones = {}
    for idx, evento in enumerate(eventos):
        salon, f_inicio = inicios_validos[idx][int(solucion[idx])]
        for offset in range(duracion_por_evento[evento]):
            asignaciones[(evento, salon, f_inicio + offset)] = 1.0
    return asignaciones


# Alias de compatibilidad hacia atrás
reconstruir_x_desde_vector = reconstruir_asignaciones_desde_vector
