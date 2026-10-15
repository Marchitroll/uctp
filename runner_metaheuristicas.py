"""Orquestador genérico para la ejecución de benchmarks multi-corrida de metaheurísticas UCTP.

Centraliza la carga de datos, precomputación de dominios, ciclo de optimización con semillas,
selección de la mejor solución global, consolidación estadística en CSV/JSON y exportación
de mallas horarias desagregadas.
"""
import argparse
import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from mealpy import IntegerVar

from cargador_datos import cargar_datos_uctp
from exportador_horarios import exportar_horarios, reconstruir_x_desde_vector
from problema_uctp import (
    precomputar_combinaciones_inicio,
    precomputar_restricciones_curriculares,
)
from uctp_utils import detectar_escala, obtener_metadatos_entorno


def crear_parser_metaheuristica(nombre_metodo: str, paciencia_defecto: int = 20) -> argparse.ArgumentParser:
    """Crea el analizador de argumentos de línea de comandos estándar en español."""
    parser = argparse.ArgumentParser(description=f"{nombre_metodo} para UCTP")
    parser.add_argument("--instancia", default="pequena", help="Escala ('pequena', 'mediana', 'grande')")
    parser.add_argument("--corridas", type=int, default=20, help="Cantidad de corridas independientes")
    parser.add_argument("--minutos", type=float, default=5.0, help="Límite de tiempo por corrida (minutos)")
    parser.add_argument("--semilla_inicio", type=int, default=42, help="Semilla inicial para el generador pseudoaleatorio")
    parser.add_argument("--epocas", type=int, default=None, help="Número máximo de épocas")
    parser.add_argument("--dir_datos", default="dataset", help="Directorio con los archivos CSV del dataset")
    parser.add_argument("--etiqueta", default="", help="Etiqueta identificadora para archivos de salida")
    parser.add_argument("--paciencia", type=int, default=paciencia_defecto, help="Épocas consecutivas sin mejora antes de detener")
    return parser


def ejecutar_benchmark(
    nombre_metodo: str,
    clase_optimizador: type,
    clase_problema: type,
    args: argparse.Namespace,
    configs_escala: dict,
    obtener_parametros_mealpy: callable,
) -> None:
    """Ejecuta el benchmark multi-corrida estándar para la metaheurística configurada."""
    max_segundos = int(args.minutos * 60) if args.minutos is not None else None

    # 1. Cargar datos y detectar escala
    datos = cargar_datos_uctp(args.dir_datos)
    escala_detectada = detectar_escala(datos.K)
    escala_efectiva = args.instancia if args.instancia is not None else escala_detectada

    config_base = configs_escala[escala_efectiva].copy()
    if args.epocas is not None:
        config_base["epoch"] = args.epocas

    file_tag = f"_{args.etiqueta}" if args.etiqueta else ""
    nombre_salida = f"{escala_efectiva}{file_tag}"
    resultados_dir = f"resultados_{nombre_metodo}"
    os.makedirs(resultados_dir, exist_ok=True)

    print(f"\n[INFO - {nombre_metodo}] Escala: {escala_efectiva} | Épocas: {config_base['epoch']} | Paciencia: {args.paciencia}")

    # 2. Precomputar dominios válidos
    valid_starts = precomputar_combinaciones_inicio(
        datos.E, datos.R, datos.T, datos.T_d, datos.D, datos.d_jue, datos.Dur,
        datos.EVENTO_SECCION, datos.E_p, datos.Alumno, datos.Req, datos.Tiene,
        datos.F, datos.CAP, datos.ES_VIRTUAL, datos.Disp
    )
    restricciones_curr = precomputar_restricciones_curriculares(
        datos.K, datos.E_k, datos.EVENTO_SECCION, datos.SECCION_CURSO, datos.E
    )
    bounds = IntegerVar(lb=[0] * len(datos.E), ub=[len(valid_starts[idx]) - 1 for idx in range(len(datos.E))])

    # 3. Multi-corrida independiente
    n_corridas = args.corridas
    resultados_runs = []
    mejor_global_solucion = None
    mejor_global_clave = None

    print(f"[INFO - {nombre_metodo}] Iniciando {n_corridas} corridas independientes...")
    print("=" * 80)

    for run in range(n_corridas):
        semilla = args.semilla_inicio + run
        print(f"\n>>> [{nombre_metodo} - CORRIDA {run + 1}/{n_corridas}] Semilla: {semilla} ...")

        problema = clase_problema(
            E=datos.E, R=datos.R, T=datos.T, D=datos.D, T_d=datos.T_d, P=datos.P, S=datos.S,
            K=datos.K, E_k=datos.E_k, E_p=datos.E_p, E_s=datos.E_s, Dur=datos.Dur,
            EVENTO_SECCION=datos.EVENTO_SECCION, SECCION_CURSO=datos.SECCION_CURSO,
            Almuerzo=datos.Almuerzo, valid_starts=valid_starts,
            restricciones_curriculares=restricciones_curr, bounds=bounds,
            ES_VIRTUAL=datos.ES_VIRTUAL
        )

        params_mealpy = obtener_parametros_mealpy(config_base, args)
        modelo = clase_optimizador(paciencia=args.paciencia, **params_mealpy)

        term_dict = {"max_epoch": config_base["epoch"]}
        if max_segundos is not None:
            term_dict["max_time"] = max_segundos

        inicio_cpu = time.process_time()
        mejor_agente = modelo.solve(problema, termination=term_dict, seed=semilla)
        tiempo_cpu = time.process_time() - inicio_cpu

        solucion_run = mejor_agente.solution
        metricas = problema.evaluate_solution(solucion_run)

        hcv = metricas["violaciones_restricciones_duras"]
        z = metricas["penalizacion_blanda"]
        ttf = modelo.primer_tiempo_factible
        tasa_inicial = modelo.tasa_factibilidad_inicial

        clave_run = (hcv == 0, -hcv, -z)
        if mejor_global_clave is None or clave_run > mejor_global_clave:
            mejor_global_clave = clave_run
            mejor_global_solucion = solucion_run

        print(
            f"    Resultado: HCV={hcv} | Z={z:.2f} | Factible={'SÍ' if hcv == 0 else 'NO'} | "
            f"CPU={tiempo_cpu:.2f}s | NFE={problema.evaluaciones_aptitud}"
        )
        if hcv == 0 and ttf is not None:
            print(f"    TTF: {ttf:.2f}s (Gen {modelo.primera_gen_factible})")

        resultados_runs.append({
            "corrida": run + 1,
            "semilla": semilla,
            "Z": z,
            "HCV": hcv,
            "factible": hcv == 0,
            "tiempo_cpu": tiempo_cpu,
            "TTF": ttf if hcv == 0 else float("nan"),
            "evaluaciones_aptitud": problema.evaluaciones_aptitud,
            "tasa_factib_inicial": tasa_inicial,
            "penalizacion_almuerzo": metricas["penalizacion_almuerzo"],
            "penalizacion_espaciado": metricas["penalizacion_espaciado"],
            "penalizacion_jueves": metricas["penalizacion_jueves"],
            "penalizacion_sabado": metricas["penalizacion_sabado"],
            "penalizacion_ventanas": metricas["penalizacion_ventanas"],
            "hcv_colision_profesor": metricas["colision_profesor"],
            "hcv_carga_maxima_profesor": metricas["carga_maxima_profesor"],
            "hcv_estabilidad_salones": metricas["estabilidad_salones"],
            "hcv_colision_salones_fisicos": metricas["colision_salones_fisicos"],
            "hcv_conflicto_curricular": metricas["conflicto_curricular"],
        })

    # 4. Consolidación estadística
    df_results = pd.DataFrame(resultados_runs)
    csv_filepath = os.path.join(resultados_dir, f"resultados_{nombre_salida}.csv")
    df_results.to_csv(csv_filepath, index=False)
    print(f"\n[ÉXITO] Resultados individuales {nombre_metodo} persistidos en '{csv_filepath}'.")

    factibles_df = df_results[df_results["factible"]]
    total_corridas = len(df_results)
    corridas_factibles = len(factibles_df)
    tasa_factibilidad = (corridas_factibles / total_corridas) * 100.0

    resumen = {
        "metodo": nombre_metodo,
        "escala": escala_efectiva,
        "total_corridas": total_corridas,
        "corridas_factibles": corridas_factibles,
        "tasa_factibilidad_final": tasa_factibilidad,
        "mejor_df": int(df_results["HCV"].min()),
        "promedio_df": round(float(df_results["HCV"].mean()), 2),
        "entorno": obtener_metadatos_entorno(f"mealpy ({nombre_metodo})"),
    }

    if corridas_factibles > 0:
        resumen.update({
            "mejor_z": round(float(factibles_df["Z"].min()), 2),
            "promedio_z": round(float(factibles_df["Z"].mean()), 2),
            "mediana_z": round(float(factibles_df["Z"].median()), 2),
            "peor_z": round(float(factibles_df["Z"].max()), 2),
            "desviacion_z": round(float(factibles_df["Z"].std()), 2) if corridas_factibles > 1 else 0.0,
            "TTF_promedio": round(float(factibles_df["TTF"].mean()), 4),
            "tiempo_cpu_promedio": round(float(factibles_df["tiempo_cpu"].mean()), 2),
            "evaluaciones_aptitud_promedio": int(df_results["evaluaciones_aptitud"].mean()),
        })
    else:
        resumen.update({
            "mejor_z": None,
            "promedio_z": None,
            "mediana_z": None,
            "peor_z": None,
            "desviacion_z": None,
            "TTF_promedio": None,
            "tiempo_cpu_promedio": round(float(df_results["tiempo_cpu"].mean()), 2),
            "evaluaciones_aptitud_promedio": int(df_results["evaluaciones_aptitud"].mean()),
        })

    resumen_filepath = os.path.join(resultados_dir, f"resumen_{nombre_salida}.json")
    with open(resumen_filepath, "w", encoding="utf-8") as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)
    print(f"[ÉXITO] Resumen estadístico consolidado {nombre_metodo} guardado en '{resumen_filepath}'.\n")

    # 5. Exportar mallas del mejor resultado
    if mejor_global_solucion is not None:
        print(f"[INFO - {nombre_metodo}] Exportando horario de la mejor corrida...")
        x_mejor = reconstruir_x_desde_vector(mejor_global_solucion, valid_starts, datos.E, datos.Dur)
        dir_horarios = f"horarios_{escala_efectiva}{file_tag}/{nombre_metodo}"
        exportar_horarios(
            x=x_mejor, K=datos.K, E_k=datos.E_k, T_d=datos.T_d, D=datos.D,
            EVENTO_SECCION=datos.EVENTO_SECCION, SECCION_CURSO=datos.SECCION_CURSO,
            E_p=datos.E_p, output_dir=dir_horarios
        )
