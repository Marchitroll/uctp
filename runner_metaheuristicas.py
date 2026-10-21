"""Ejecución de benchmarks multi-corrida para metaheurísticas UCTP."""
import argparse
import json
import os
import time

import pandas as pd
from mealpy import IntegerVar

from cargador_datos import cargar_datos_uctp
from exportador_horarios import exportar_horarios, reconstruir_asignaciones_desde_vector
from problema_uctp import (
    precomputar_combinaciones_inicio,
    precomputar_restricciones_curriculares,
)
from uctp_utils import detectar_escala, obtener_metadatos_entorno


def crear_parser_metaheuristica(nombre_metodo: str, paciencia_defecto: int = 20) -> argparse.ArgumentParser:
    """Crea el parser de argumentos CLI para metaheurísticas."""
    parser = argparse.ArgumentParser(description=f"{nombre_metodo} para UCTP")
    parser.add_argument(
        "--instancia",
        default=None,
        choices=["pequena", "mediana", "grande"],
        help="Escala del problema ('pequena', 'mediana', 'grande'). Por defecto se detecta automáticamente del dataset.",
    )
    parser.add_argument("--corridas", type=int, default=30, help="Cantidad de corridas independientes")
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
    """Ejecuta el benchmark multi-corrida para la metaheurística dada."""
    max_segundos = int(args.minutos * 60) if args.minutos is not None else None

    datos = cargar_datos_uctp(args.dir_datos)
    escala_detectada = detectar_escala(datos.curriculos)
    escala_efectiva = args.instancia if args.instancia is not None else escala_detectada

    config_base = configs_escala[escala_efectiva].copy()
    if args.epocas is not None:
        config_base["epoch"] = args.epocas

    etiqueta_archivo = f"_{args.etiqueta}" if args.etiqueta else ""
    nombre_salida = f"{escala_efectiva}{etiqueta_archivo}"
    resultados_dir = f"resultados_{nombre_metodo}"
    os.makedirs(resultados_dir, exist_ok=True)

    print(f"\n[INFO - {nombre_metodo}] Escala: {escala_efectiva} | Épocas: {config_base['epoch']} | Paciencia: {args.paciencia}")

    inicios_validos = precomputar_combinaciones_inicio(
        eventos=datos.eventos,
        salones=datos.salones,
        franjas_horarias=datos.franjas_horarias,
        franjas_por_dia=datos.franjas_por_dia,
        dias=datos.dias,
        dia_cierre_remoto=datos.dia_cierre_remoto,
        duracion_por_evento=datos.duracion_por_evento,
        seccion_por_evento=datos.seccion_por_evento,
        eventos_por_profesor=datos.eventos_por_profesor,
        alumnos_por_seccion=datos.alumnos_por_seccion,
        seccion_requiere_caracteristica=datos.seccion_requiere_caracteristica,
        salon_tiene_caracteristica=datos.salon_tiene_caracteristica,
        caracteristicas=datos.caracteristicas,
        capacidad_por_salon=datos.capacidad_por_salon,
        es_virtual_por_salon=datos.es_virtual_por_salon,
        disponibilidad_por_profesor=datos.disponibilidad_por_profesor,
    )
    restricciones_curr = precomputar_restricciones_curriculares(
        curriculos=datos.curriculos,
        eventos_por_curriculo=datos.eventos_por_curriculo,
        seccion_por_evento=datos.seccion_por_evento,
        curso_por_seccion=datos.curso_por_seccion,
        eventos=datos.eventos,
    )
    limites_variables = IntegerVar(
        lb=[0] * len(datos.eventos),
        ub=[len(inicios_validos[idx]) - 1 for idx in range(len(datos.eventos))],
    )

    n_corridas = args.corridas
    resultados_runs = []
    mejor_global_solucion = None
    mejor_global_clave = None

    print(f"[INFO - {nombre_metodo}] Iniciando {n_corridas} corridas independientes...")
    print("=" * 80)

    for corrida in range(n_corridas):
        semilla = args.semilla_inicio + corrida
        print(f"\n>>> [{nombre_metodo} - CORRIDA {corrida + 1}/{n_corridas}] Semilla: {semilla} ...")

        problema = clase_problema(
            eventos=datos.eventos,
            salones=datos.salones,
            franjas_horarias=datos.franjas_horarias,
            dias=datos.dias,
            franjas_por_dia=datos.franjas_por_dia,
            profesores=datos.profesores,
            secciones=datos.secciones,
            curriculos=datos.curriculos,
            eventos_por_curriculo=datos.eventos_por_curriculo,
            eventos_por_profesor=datos.eventos_por_profesor,
            eventos_por_seccion=datos.eventos_por_seccion,
            duracion_por_evento=datos.duracion_por_evento,
            seccion_por_evento=datos.seccion_por_evento,
            curso_por_seccion=datos.curso_por_seccion,
            almuerzo_por_dia=datos.almuerzo_por_dia,
            inicios_validos=inicios_validos,
            restricciones_curriculares=restricciones_curr,
            bounds=limites_variables,
            es_virtual_por_salon=datos.es_virtual_por_salon,
        )

        params_mealpy = obtener_parametros_mealpy(config_base, args)
        modelo = clase_optimizador(paciencia=args.paciencia, **params_mealpy)

        diccionario_terminacion = {"max_epoch": config_base["epoch"]}
        if max_segundos is not None:
            diccionario_terminacion["max_time"] = max_segundos

        inicio_cpu = time.process_time()
        mejor_agente = modelo.solve(problema, termination=diccionario_terminacion, seed=semilla)
        tiempo_cpu = time.process_time() - inicio_cpu

        solucion_run = mejor_agente.solution
        metricas = problema.evaluar_solucion(solucion_run)

        violaciones_duras = metricas["violaciones_restricciones_duras"]
        penalizacion_blanda = metricas["penalizacion_blanda"]
        tiempo_primer_factible = modelo.primer_tiempo_factible
        tasa_inicial = modelo.tasa_factibilidad_inicial

        clave_run = (violaciones_duras == 0, -violaciones_duras, -penalizacion_blanda)
        if mejor_global_clave is None or clave_run > mejor_global_clave:
            mejor_global_clave = clave_run
            mejor_global_solucion = solucion_run

        print(
            f"    Resultado: HCV={violaciones_duras} | Z={penalizacion_blanda:.2f} | Factible={'SÍ' if violaciones_duras == 0 else 'NO'} | "
            f"CPU={tiempo_cpu:.2f}s | NFE={problema.evaluaciones_aptitud}"
        )
        if violaciones_duras == 0 and tiempo_primer_factible is not None:
            print(f"    TTF: {tiempo_primer_factible:.2f}s (Gen {modelo.primera_gen_factible})")

        resultados_runs.append({
            "corrida": corrida + 1,
            "semilla": semilla,
            "Z": penalizacion_blanda,
            "HCV": violaciones_duras,
            "factible": violaciones_duras == 0,
            "tiempo_cpu": tiempo_cpu,
            "TTF": tiempo_primer_factible if violaciones_duras == 0 else float("nan"),
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

    df_resultados = pd.DataFrame(resultados_runs)
    ruta_csv = os.path.join(resultados_dir, f"resultados_{nombre_salida}.csv")
    df_resultados.to_csv(ruta_csv, index=False)
    print(f"\n[ÉXITO] Resultados de {nombre_metodo} guardados en '{ruta_csv}'.")

    factibles_df = df_resultados[df_resultados["factible"]]
    total_corridas = len(df_resultados)
    corridas_factibles = len(factibles_df)
    tasa_factibilidad = (corridas_factibles / total_corridas) * 100.0

    resumen = {
        "metodo": nombre_metodo,
        "escala": escala_efectiva,
        "total_corridas": total_corridas,
        "corridas_factibles": corridas_factibles,
        "tasa_factibilidad_final": tasa_factibilidad,
        "mejor_df": int(df_resultados["HCV"].min()),
        "promedio_df": round(float(df_resultados["HCV"].mean()), 2),
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
            "evaluaciones_aptitud_promedio": int(df_resultados["evaluaciones_aptitud"].mean()),
        })
    else:
        resumen.update({
            "mejor_z": None,
            "promedio_z": None,
            "mediana_z": None,
            "peor_z": None,
            "desviacion_z": None,
            "TTF_promedio": None,
            "tiempo_cpu_promedio": round(float(df_resultados["tiempo_cpu"].mean()), 2),
            "evaluaciones_aptitud_promedio": int(df_resultados["evaluaciones_aptitud"].mean()),
        })

    ruta_resumen = os.path.join(resultados_dir, f"resumen_{nombre_salida}.json")
    with open(ruta_resumen, "w", encoding="utf-8") as archivo:
        json.dump(resumen, archivo, indent=2, ensure_ascii=False)
    print(f"[ÉXITO] Resumen de {nombre_metodo} guardado en '{ruta_resumen}'.\n")

    if mejor_global_solucion is not None:
        print(f"[INFO - {nombre_metodo}] Exportando horario de la mejor corrida...")
        asignaciones_mejor = reconstruir_asignaciones_desde_vector(
            mejor_global_solucion, inicios_validos, datos.eventos, datos.duracion_por_evento
        )
        dir_horarios = f"horarios_{escala_efectiva}{etiqueta_archivo}/{nombre_metodo}"
        exportar_horarios(
            asignaciones=asignaciones_mejor,
            curriculos=datos.curriculos,
            eventos_por_curriculo=datos.eventos_por_curriculo,
            franjas_por_dia=datos.franjas_por_dia,
            dias=datos.dias,
            seccion_por_evento=datos.seccion_por_evento,
            curso_por_seccion=datos.curso_por_seccion,
            eventos_por_profesor=datos.eventos_por_profesor,
            dir_salida=dir_horarios,
        )
