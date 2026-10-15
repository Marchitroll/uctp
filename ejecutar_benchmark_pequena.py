"""
ejecutar_benchmark_pequena.py
Script maestro para orquestar la ejecución reproducible del benchmark UCTP en escala pequeña (Opción A):
- Genera 3 instancias semi-sintéticas en dataset/pequena_s1/, dataset/pequena_s2/, dataset/pequena_s3/ (semillas 1, 2, 3).
- Ejecuta MIP (HiGHS) 1 vez por instancia.
- Ejecuta 30 réplicas independientes de HGA, GA, TS y SA por instancia (semillas 1..30).
- Consolida resultados numéricos en CSV y JSON.
- Exporta cronogramas óptimos en carpetas dedicadas por instancia.
- Copia dataset/pequena_s1/ a la raíz dataset/.
- Invoca la consolidación analítica en reporte_desviacion.py.
"""

import os
import sys
import shutil
import argparse
import subprocess
import json
import pandas as pd


def ejecutar_comando(cmd, descripcion):
    print(f"\n{'='*80}")
    print(f"[BENCHMARK] {descripcion}")
    print(f"Comando: {' '.join(cmd)}")
    print(f"{'='*80}\n")
    sys.stdout.flush()

    res = subprocess.run(cmd, text=True)
    if res.returncode != 0:
        print(f"\n[ERROR] Falló la ejecución: {descripcion} (Código de salida: {res.returncode})")
        sys.exit(res.returncode)


def consolidar_archivos(semillas, metodos):
    """
    Concatena los CSV individuales de cada instancia en resultados_pequena.csv
    y calcula el resumen global ponderado resumen_pequena.json para cada método.
    """
    print("\n[INFO] Consolidando resultados de las 3 instancias...")

    for metodo in metodos:
        dir_res = f"resultados_{metodo}"
        dfs = []
        for s in semillas:
            csv_path = os.path.join(dir_res, f"resultados_pequena_s{s}.csv")
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                df["instancia_tag"] = f"pequena_s{s}"
                df["semilla_instancia"] = s
                dfs.append(df)

        if dfs:
            df_total = pd.concat(dfs, ignore_index=True)
            csv_consolidado = os.path.join(dir_res, "resultados_pequena.csv")
            df_total.to_csv(csv_consolidado, index=False)
            print(f"  [OK] Consolidado {csv_consolidado} ({len(df_total)} filas totales)")

            # Calcular resumen consolidado agregado
            factibles = df_total[df_total["factible"]] if "factible" in df_total.columns else df_total
            total_corridas = len(df_total)
            tasa_factib = (len(factibles) / total_corridas * 100.0) if total_corridas > 0 else 0.0

            if metodo == "MIP":
                mejor_z = float(df_total["Z"].min()) if "Z" in df_total.columns else None
                prom_z = float(df_total["Z"].mean()) if "Z" in df_total.columns else None
                std_z = float(df_total["Z"].std()) if len(df_total) > 1 else 0.0
                cpu_prom = float(df_total["tiempo_cpu"].mean()) if "tiempo_cpu" in df_total.columns else None
                nodos_prom = int(df_total["nodos_explorados"].mean()) if "nodos_explorados" in df_total.columns else 0
                resumen_global = {
                    "metodo": "MIP",
                    "escala": "pequena",
                    "total_instancias": len(semillas),
                    "total_corridas": total_corridas,
                    "tasa_factibilidad_final": tasa_factib,
                    "mejor_df": 0 if tasa_factib > 0 else 1,
                    "promedio_df": 0.0 if tasa_factib > 0 else 1.0,
                    "mejor_z": mejor_z,
                    "peor_z": float(df_total["Z"].max()) if "Z" in df_total.columns else None,
                    "promedio_z": prom_z,
                    "desviacion_z": std_z,
                    "tiempo_cpu_promedio": round(cpu_prom, 2) if cpu_prom is not None else None,
                    "TTF_promedio": round(cpu_prom, 2) if (tasa_factib > 0 and cpu_prom is not None) else None,
                    "evaluaciones_aptitud_promedio": 0,
                    "nodos_explorados_promedio": nodos_prom,
                }
            else:
                mejor_z = float(factibles["Z"].min()) if len(factibles) > 0 else None
                peor_z = float(factibles["Z"].max()) if len(factibles) > 0 else None
                prom_z = float(factibles["Z"].mean()) if len(factibles) > 0 else None
                std_z = float(factibles["Z"].std()) if len(factibles) > 1 else 0.0
                ttf_prom = round(float(factibles["TTF"].mean()), 2) if ("TTF" in factibles.columns and len(factibles) > 0) else None
                cpu_prom = round(float(df_total["tiempo_cpu"].mean()), 2) if "tiempo_cpu" in df_total.columns else None
                evals_prom = int(df_total["evaluaciones_aptitud"].mean()) if "evaluaciones_aptitud" in df_total.columns else None
                resumen_global = {
                    "metodo": metodo,
                    "escala": "pequena",
                    "total_instancias": len(semillas),
                    "total_corridas": total_corridas,
                    "tasa_factibilidad_final": tasa_factib,
                    "mejor_df": int(df_total["HCV"].min()) if "HCV" in df_total.columns else 0,
                    "promedio_df": round(float(df_total["HCV"].mean()), 1) if "HCV" in df_total.columns else 0.0,
                    "mejor_z": mejor_z,
                    "peor_z": peor_z,
                    "promedio_z": prom_z,
                    "desviacion_z": std_z,
                    "tiempo_cpu_promedio": cpu_prom,
                    "TTF_promedio": ttf_prom,
                    "evaluaciones_aptitud_promedio": evals_prom,
                }

            json_consolidado = os.path.join(dir_res, "resumen_pequena.json")
            with open(json_consolidado, "w", encoding="utf-8") as f:
                json.dump(resumen_global, f, indent=2, ensure_ascii=False)
            print(f"  [OK] Resumen consolidado {json_consolidado}")


def main():
    parser = argparse.ArgumentParser(description="Orquestador del Benchmark UCTP en Escala Pequeña (Opción A).")
    parser.add_argument("--instancias", type=int, nargs="+", default=[1, 2, 3],
                        help="Lista de semillas para generar variantes de la instancia pequeña (default: 1 2 3)")
    parser.add_argument("--corridas", type=int, default=30,
                        help="Número de réplicas independientes por metaheurística (default: 30)")
    parser.add_argument("--mip_minutos", type=float, default=120.0,
                        help="Tiempo límite de optimización en minutos para MIP por instancia (default: 120.0)")
    parser.add_argument("--semilla_inicio", type=int, default=1,
                        help="Semilla inicial para las corridas independientes de metaheurísticas (default: 1)")
    parser.add_argument("--smoke_test", action="store_true",
                        help="Modo prueba de humo rápida: 1 corrida y pocas iteraciones para validar el pipeline.")
    args = parser.parse_args()

    python_exe = sys.executable
    metodos = ["MIP", "HGA", "GA", "TS", "SA"]

    if args.smoke_test:
        print("\n" + "=" * 80)
        print(" [MODO PRUEBA DE HUMO (SMOKE TEST)] Validando el flujo completo de ejecución...")
        print("=" * 80)
        semillas_a_ejecutar = [args.instancias[0]]
        corridas_meta = 1
        mip_mins = 0.5
        epoch_hga = 5
        epoch_ga = 5
        epoch_ts = 5
        epoch_sa = 50
    else:
        print("\n" + "=" * 80)
        print(" [BENCHMARK COMPLETO EN ESCALA PEQUEÑA - OPCIÓN A]")
        print(f" Instancias a evaluar (semillas) : {args.instancias}")
        print(f" Corridas por metaheurística      : {args.corridas} (semillas {args.semilla_inicio}..{args.semilla_inicio + args.corridas - 1})")
        print(f" Tiempo límite MIP               : {args.mip_minutos} minutos (7200 s)")
        print("=" * 80)
        semillas_a_ejecutar = args.instancias
        corridas_meta = args.corridas
        mip_mins = args.mip_minutos
        epoch_hga = None
        epoch_ga = None
        epoch_ts = None
        epoch_sa = None

    # FASE 1: GENERACIÓN DE DATASETS
    print("\n--- FASE 1: Generación de Conjuntos de Datos Semi-sintéticos ---")
    for s in semillas_a_ejecutar:
        out_dir = f"dataset/pequena_s{s}"
        cmd = [
            python_exe, "generador_dataset.py",
            "--instancia", "pequena",
            "--semilla", str(s),
            "--dir_salida", out_dir
        ]
        ejecutar_comando(cmd, f"Generando dataset pequeña con semilla {s} en '{out_dir}'")

    # FASE 2: OPTIMIZACIÓN EXACTA Y METAHEURÍSTICA
    print("\n--- FASE 2: Ejecución de Modelos de Optimización ---")
    for s in semillas_a_ejecutar:
        tag = f"s{s}"
        data_dir = f"dataset/pequena_s{s}"
        print(f"\n>>>>>>>>>>>> PROCESANDO INSTANCIA PEQUEÑA (Semilla {s}) <<<<<<<<<<<<")

        # 1. MIP (Exacto)
        cmd_mip = [
            python_exe, "modelo_MIP.py",
            "--minutos", str(mip_mins),
            "--dir_datos", data_dir,
            "--etiqueta", tag
        ]
        ejecutar_comando(cmd_mip, f"Ejecutando MIP (HiGHS) en instancia pequeña (semilla {s})")

        # 2. Metaheurísticas (HGA, GA, TS, SA)
        metaheuristicas = [
            ("HGA", "HGA (Genético Híbrido Lamarckiano)", epoch_hga),
            ("GA",  "GA Clásico",                        epoch_ga),
            ("TS",  "TS (Búsqueda Tabú)",                 epoch_ts),
            ("SA",  "SA (Recocido Simulado)",             epoch_sa),
        ]
        for codigo, nombre_display, epocas in metaheuristicas:
            cmd = [
                python_exe, f"modelo_{codigo}.py",
                "--instancia", "pequena",
                "--corridas", str(corridas_meta),
                "--dir_datos", data_dir,
                "--etiqueta", tag,
                "--semilla_inicio", str(args.semilla_inicio),
            ]
            if epocas is not None:
                cmd.extend(["--epocas", str(epocas)])
            ejecutar_comando(cmd, f"Ejecutando {nombre_display} ({corridas_meta} corridas) en instancia pequeña (semilla {s})")

    # FASE 3: CONSOLIDACIÓN Y COPIAS
    print("\n--- FASE 3: Consolidación de Resultados y Actualización de Directorios ---")
    consolidar_archivos(semillas_a_ejecutar, metodos)

    # Copiar dataset/pequena_s1 a dataset/ raíz
    fuente_s1 = "dataset/pequena_s1"
    destino_root = "dataset"
    if os.path.exists(fuente_s1):
        print(f"\n[INFO] Copiando '{fuente_s1}' a '{destino_root}' raíz...")
        for fname in os.listdir(fuente_s1):
            src_f = os.path.join(fuente_s1, fname)
            dst_f = os.path.join(destino_root, fname)
            if os.path.isfile(src_f):
                shutil.copy2(src_f, dst_f)
        print("  [OK] Copia a la raíz dataset/ completada exitosamente.")

    # FASE 4: REPORTE DE DESVIACIÓN
    print("\n--- FASE 4: Consolidación Analítica con reporte_desviacion.py ---")
    cmd_rep = [python_exe, "reporte_desviacion.py"]
    ejecutar_comando(cmd_rep, "Generando tablas analíticas y actualizando comparacion_metodos.md")

    print("\n" + "=" * 80)
    print(" [ÉXITO] Benchmark en escala pequeña culminado exitosamente.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
