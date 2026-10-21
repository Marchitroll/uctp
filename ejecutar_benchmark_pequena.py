"""Orquestador del benchmark en escala pequeña (3 instancias x 30 réplicas por método)."""
import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
import pandas as pd


def ejecutar_comando(comando: list[str], descripcion: str):
    """Ejecuta un subproceso con trazabilidad por consola y control de fallos."""
    print(f"\n{'='*80}")
    print(f"[BENCHMARK] {descripcion}")
    print(f"Comando: {' '.join(comando)}")
    print(f"{'='*80}\n")
    sys.stdout.flush()

    resultado = subprocess.run(comando, text=True)
    if resultado.returncode != 0:
        print(f"\n[ERROR] Falló la ejecución: {descripcion} (Código de salida: {resultado.returncode})")
        sys.exit(resultado.returncode)


def consolidar_archivos(semillas: list[int], metodos: list[str]):
    """Concatena los CSV por instancia y genera el resumen agregado."""
    print("\n[INFO] Consolidando resultados de las 3 instancias...")

    for metodo in metodos:
        dir_resultados = f"resultados_{metodo}"
        dataframes_por_instancia = []
        for semilla in semillas:
            ruta_csv = os.path.join(dir_resultados, f"resultados_pequena_s{semilla}.csv")
            if os.path.exists(ruta_csv):
                df_instancia = pd.read_csv(ruta_csv)
                df_instancia["instancia_tag"] = f"pequena_s{semilla}"
                df_instancia["semilla_instancia"] = semilla
                dataframes_por_instancia.append(df_instancia)

        if dataframes_por_instancia:
            df_total = pd.concat(dataframes_por_instancia, ignore_index=True)
            csv_consolidado = os.path.join(dir_resultados, "resultados_pequena.csv")
            df_total.to_csv(csv_consolidado, index=False)
            print(f"  [OK] Consolidado {csv_consolidado} ({len(df_total)} filas totales)")

            # Resumen estadístico agregado
            factibles = df_total[df_total["factible"]] if "factible" in df_total.columns else df_total
            total_corridas = len(df_total)
            tasa_factibilidad = (len(factibles) / total_corridas * 100.0) if total_corridas > 0 else 0.0

            if metodo == "MIP":
                mejor_z = float(df_total["Z"].min()) if "Z" in df_total.columns else None
                promedio_z = float(df_total["Z"].mean()) if "Z" in df_total.columns else None
                desviacion_z = float(df_total["Z"].std()) if len(df_total) > 1 else 0.0
                tiempo_cpu_promedio = float(df_total["tiempo_cpu"].mean()) if "tiempo_cpu" in df_total.columns else None
                nodos_explorados_promedio = int(df_total["nodos_explorados"].mean()) if "nodos_explorados" in df_total.columns else 0
                resumen_global = {
                    "metodo": "MIP",
                    "escala": "pequena",
                    "total_instancias": len(semillas),
                    "total_corridas": total_corridas,
                    "tasa_factibilidad_final": tasa_factibilidad,
                    "mejor_df": 0 if tasa_factibilidad > 0 else 1,
                    "promedio_df": 0.0 if tasa_factibilidad > 0 else 1.0,
                    "mejor_z": mejor_z,
                    "peor_z": float(df_total["Z"].max()) if "Z" in df_total.columns else None,
                    "promedio_z": promedio_z,
                    "desviacion_z": desviacion_z,
                    "tiempo_cpu_promedio": round(tiempo_cpu_promedio, 2) if tiempo_cpu_promedio is not None else None,
                    "TTF_promedio": round(tiempo_cpu_promedio, 2) if (tasa_factibilidad > 0 and tiempo_cpu_promedio is not None) else None,
                    "evaluaciones_aptitud_promedio": 0,
                    "nodos_explorados_promedio": nodos_explorados_promedio,
                }
            else:
                mejor_z = float(factibles["Z"].min()) if len(factibles) > 0 else None
                peor_z = float(factibles["Z"].max()) if len(factibles) > 0 else None
                promedio_z = float(factibles["Z"].mean()) if len(factibles) > 0 else None
                desviacion_z = float(factibles["Z"].std()) if len(factibles) > 1 else 0.0
                tiempo_a_factibilidad_promedio = round(float(factibles["TTF"].mean()), 2) if ("TTF" in factibles.columns and len(factibles) > 0) else None
                tiempo_cpu_promedio = round(float(df_total["tiempo_cpu"].mean()), 2) if "tiempo_cpu" in df_total.columns else None
                evaluaciones_promedio = int(df_total["evaluaciones_aptitud"].mean()) if "evaluaciones_aptitud" in df_total.columns else None
                resumen_global = {
                    "metodo": metodo,
                    "escala": "pequena",
                    "total_instancias": len(semillas),
                    "total_corridas": total_corridas,
                    "tasa_factibilidad_final": tasa_factibilidad,
                    "mejor_df": int(df_total["HCV"].min()) if "HCV" in df_total.columns else 0,
                    "promedio_df": round(float(df_total["HCV"].mean()), 1) if "HCV" in df_total.columns else 0.0,
                    "mejor_z": mejor_z,
                    "peor_z": peor_z,
                    "promedio_z": promedio_z,
                    "desviacion_z": desviacion_z,
                    "tiempo_cpu_promedio": tiempo_cpu_promedio,
                    "TTF_promedio": tiempo_a_factibilidad_promedio,
                    "evaluaciones_aptitud_promedio": evaluaciones_promedio,
                }

            json_consolidado = os.path.join(dir_resultados, "resumen_pequena.json")
            with open(json_consolidado, "w", encoding="utf-8") as archivo:
                json.dump(resumen_global, archivo, indent=2, ensure_ascii=False)
            print(f"  [OK] Resumen consolidado {json_consolidado}")


def main():
    parser = argparse.ArgumentParser(description="Orquestador del Benchmark UCTP en Escala Pequeña.")
    parser.add_argument(
        "--instancias",
        type=int,
        nargs="+",
        default=[1, 2, 3],
        help="Lista de semillas para generar variantes de la instancia pequeña (default: 1 2 3)",
    )
    parser.add_argument(
        "--corridas",
        type=int,
        default=30,
        help="Número de réplicas independientes por metaheurística (default: 30)",
    )
    parser.add_argument(
        "--mip_minutos",
        type=float,
        default=120.0,
        help="Tiempo límite de optimización en minutos para MIP por instancia (default: 120.0)",
    )
    parser.add_argument(
        "--semilla_inicio",
        type=int,
        default=1,
        help="Semilla inicial para las corridas independientes de metaheurísticas (default: 1)",
    )
    parser.add_argument(
        "--smoke_test",
        action="store_true",
        help="Modo prueba de humo rápida: 1 corrida y pocas iteraciones para validar el pipeline.",
    )
    args = parser.parse_args()

    python_ejecutable = sys.executable
    metodos = ["MIP", "HGA", "GA", "TS", "SA"]

    if args.smoke_test:
        print("\n" + "=" * 80)
        print(" [MODO PRUEBA DE HUMO (SMOKE TEST)] Validando el flujo completo de ejecución...")
        print("=" * 80)
        semillas_a_ejecutar = [args.instancias[0]]
        corridas_metaheuristica = 1
        minutos_mip = 0.5
        epocas_hga = 5
        epocas_ga = 5
        epocas_ts = 5
        epocas_sa = 50
    else:
        print("\n" + "=" * 80)
        print(" [BENCHMARK COMPLETO EN ESCALA PEQUEÑA]")
        print(f" Instancias a evaluar (semillas) : {args.instancias}")
        print(f" Corridas por metaheurística      : {args.corridas} (semillas {args.semilla_inicio}..{args.semilla_inicio + args.corridas - 1})")
        print(f" Tiempo límite MIP               : {args.mip_minutos} minutos")
        print("=" * 80)
        semillas_a_ejecutar = args.instancias
        corridas_metaheuristica = args.corridas
        minutos_mip = args.mip_minutos
        epocas_hga = None
        epocas_ga = None
        epocas_ts = None
        epocas_sa = None

    # 1. Generación de datasets
    print("\n--- FASE 1: Generación de Conjuntos de Datos Semi-sintéticos ---")
    for semilla in semillas_a_ejecutar:
        dir_salida = f"dataset/pequena_s{semilla}"
        comando = [
            python_ejecutable, "generador_dataset.py",
            "--instancia", "pequena",
            "--semilla", str(semilla),
            "--dir_salida", dir_salida,
        ]
        ejecutar_comando(comando, f"Generando dataset pequeña con semilla {semilla} en '{dir_salida}'")

    # 2. Ejecución de modelos
    print("\n--- FASE 2: Ejecución de Modelos de Optimización ---")
    for semilla in semillas_a_ejecutar:
        etiqueta = f"s{semilla}"
        dir_datos = f"dataset/pequena_s{semilla}"
        hora_inicio = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{hora_inicio}] INICIO: Procesando instancia pequeña (Semilla {semilla})")

        # MIP (Exacto)
        comando_mip = [
            python_ejecutable, "modelo_MIP.py",
            "--minutos", str(minutos_mip),
            "--dir_datos", dir_datos,
            "--etiqueta", etiqueta,
        ]
        ejecutar_comando(comando_mip, f"Ejecutando MIP (HiGHS) en instancia pequeña (semilla {semilla})")

        # Metaheurísticas (HGA, GA, TS, SA)
        metaheuristicas = [
            ("HGA", "HGA (Genético Híbrido Lamarckiano)", epocas_hga),
            ("GA",  "GA Clásico",                        epocas_ga),
            ("TS",  "TS (Búsqueda Tabú)",                 epocas_ts),
            ("SA",  "SA (Recocido Simulado)",             epocas_sa),
        ]
        for codigo, nombre_display, epocas in metaheuristicas:
            comando = [
                python_ejecutable, f"modelo_{codigo}.py",
                "--instancia", "pequena",
                "--corridas", str(corridas_metaheuristica),
                "--dir_datos", dir_datos,
                "--etiqueta", etiqueta,
                "--semilla_inicio", str(args.semilla_inicio),
            ]
            if epocas is not None:
                comando.extend(["--epocas", str(epocas)])
            ejecutar_comando(comando, f"Ejecutando {nombre_display} ({corridas_metaheuristica} corridas) en instancia pequeña (semilla {semilla})")

        hora_fin = datetime.now().strftime("%H:%M:%S")
        print(f"[{hora_fin}] FIN: Instancia pequeña (Semilla {semilla}) completada exitosamente.")

    # 3. Resultados
    print("\n--- FASE 3: Consolidación de Resultados y Actualización de Directorios ---")
    consolidar_archivos(semillas_a_ejecutar, metodos)

    # Copiar dataset/pequena_s1 a dataset/ raíz
    fuente_s1 = "dataset/pequena_s1"
    destino_raiz = "dataset"
    if os.path.exists(fuente_s1):
        print(f"\n[INFO] Copiando '{fuente_s1}' a '{destino_raiz}' raíz...")
        for nombre_archivo in os.listdir(fuente_s1):
            ruta_origen = os.path.join(fuente_s1, nombre_archivo)
            ruta_destino = os.path.join(destino_raiz, nombre_archivo)
            if os.path.isfile(ruta_origen):
                shutil.copy2(ruta_origen, ruta_destino)
        print("  [OK] Copia a la raíz dataset/ completada exitosamente.")

    # 4. Reporte analítico de desviación
    print("\n--- FASE 4: Consolidación Analítica con reporte_desviacion.py ---")
    comando_reporte = [python_ejecutable, "reporte_desviacion.py"]
    ejecutar_comando(comando_reporte, "Generando tablas analíticas y sincronizando documentos")

    # 5. Ocupación de salones físicos y virtuales
    print("\n--- FASE 5: Análisis de Ocupación de Salones con calcular_uso_salones.py ---")
    comando_salones = [python_ejecutable, "calcular_uso_salones.py"]
    ejecutar_comando(comando_salones, "Calculando matrices y porcentajes de ocupación de salones")

    print("\n" + "=" * 80)
    print(" [ÉXITO] Benchmark en escala pequeña culminado exitosamente.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
