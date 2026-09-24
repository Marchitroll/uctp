import os
import sys
import time
import json
import argparse
import random
import numpy as np
import pandas as pd
from mealpy import IntegerVar
from mealpy.evolutionary_based.GA import BaseGA

from cargador_datos import cargar_datos_uctp
from exportador_horarios import (
    exportar_horarios,
    reconstruir_x_desde_ga,
    obtener_metadatos_entorno
)
from problema_uctp import (
    UCTPProblemBase,
    precomputar_combinaciones_inicio,
    precomputar_restricciones_curriculares
)


class CustomGA(BaseGA):
    """
    Subclase de BaseGA adaptada para el algoritmo genético clásico (sin reparación MCF),
    registrando TTF (Time to Feasibility), factibilidad inicial y parada temprana por convergencia de Z.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.primera_gen_factible = None
        self.primer_tiempo_factible = None
        self.tiempo_inicio = None
        self.tasa_factibilidad_inicial = 0.0
        self.generaciones_sin_mejora_z = 0
        self.mejor_z = float('inf')

    def solve(self, problem, **kwargs):
        self.primera_gen_factible = None
        self.primer_tiempo_factible = None
        self.tiempo_inicio = time.process_time()
        self.generaciones_sin_mejora_z = 0
        self.mejor_z = float('inf')
        res = super().solve(problem, **kwargs)
        
        if self.primera_gen_factible is None:
            hcv = self.problem.get_hcv(self.g_best.solution)
            if hcv == 0:
                self.primera_gen_factible = 0
                self.primer_tiempo_factible = 0.0
        return res

    def after_initialization(self):
        super().after_initialization()
        feasible_count = 0
        for agent in self.pop:
            if self.problem.get_hcv(agent.solution) == 0:
                feasible_count += 1
        self.tasa_factibilidad_inicial = (feasible_count / len(self.pop)) * 100.0

    def track_optimize_step(self, pop=None, epoch=None, runtime=None):
        super().track_optimize_step(pop, epoch, runtime)
        if self.primera_gen_factible is None:
            hcv = self.problem.get_hcv(self.g_best.solution)
            if hcv == 0:
                self.primera_gen_factible = epoch
                self.primer_tiempo_factible = time.process_time() - self.tiempo_inicio

    def check_termination(self, mode="start", termination=None, epoch=None):
        finished = super().check_termination(mode, termination, epoch)
        if finished:
            return True
        if mode == "end" and epoch is not None:
            hcv = self.problem.get_hcv(self.g_best.solution)
            if hcv == 0:
                z = self.problem.evaluate_solution(self.g_best.solution)['penalizacion_blanda']
                if z < self.mejor_z:
                    self.mejor_z = z
                    self.generaciones_sin_mejora_z = 0
                else:
                    self.generaciones_sin_mejora_z += 1
                
                # Parada si Z no mejora en 20 generaciones consecutivas
                if self.generaciones_sin_mejora_z >= 20:
                    self.logger.warning("Criterio de parada: solución factible encontrada y Z convergió. ¡Finalizando corrida!")
                    return True
        return False


def main():
    parser = argparse.ArgumentParser(description="Optimizador CB-CTT: Algoritmo Genético Clásico (GA).")
    parser.add_argument("--instancia", choices=["pequena", "mediana", "grande"], default=None,
                        help="Escala de la instancia a resolver (pequena, mediana, grande). Si no se define, se detecta por currículos.")
    parser.add_argument("--epoch", type=int, default=None, help="Número máximo de generaciones (épocas) por corrida.")
    parser.add_argument("--pop_size", type=int, default=None, help="Tamaño de la población de individuos.")
    parser.add_argument("--pc", type=float, default=None, help="Probabilidad de cruzamiento (crossover).")
    parser.add_argument("--pm", type=float, default=None, help="Probabilidad de mutación.")
    parser.add_argument("--corridas", type=int, default=20, help="Número de corridas independientes a ejecutar (default: 20).")
    parser.add_argument("--minutos", type=float, default=None, help="Límite de tiempo computacional por corrida en minutos.")
    args = parser.parse_args()

    max_seconds = int(args.minutos * 60) if args.minutos is not None else None

    # 1. Cargar configuración y datos
    dataset_dir = "dataset"
    (
        D, T, T_d, d_jue, Almuerzo,
        R, CAP, ES_VIRTUAL, CARACTERISTICAS,
        CURSOS, REQ_CURSO,
        S, SECCION_CURSO, Alumno,
        E, E_s, E_p, Dur, EVENTO_SECCION,
        P, K, E_k, Disp,
        F, Tiene, Req, Cursos_Agrupados
    ) = cargar_datos_uctp(dataset_dir)

    if len(K) == 1:
        escala_detectada = "pequena"
    elif len(K) in [4, 5]:
        escala_detectada = "mediana"
    else:
        escala_detectada = "grande"

    escala_efectiva = args.instancia if args.instancia is not None else escala_detectada

    CONFIGS = {
        'pequena': {'epoch': 500, 'pop_size': 50, 'pc': 0.90, 'pm': 0.05, 'crossover': 'uniform', 'selection': 'tournament'},
        'mediana': {'epoch': 800, 'pop_size': 80, 'pc': 0.90, 'pm': 0.08, 'crossover': 'uniform', 'selection': 'tournament'},
        'grande':  {'epoch': 2000, 'pop_size': 150, 'pc': 0.85, 'pm': 0.10, 'crossover': 'uniform', 'selection': 'tournament'},
    }
    config_base = CONFIGS[escala_efectiva].copy()
    if args.epoch is not None:
        config_base['epoch'] = args.epoch
    if args.pop_size is not None:
        config_base['pop_size'] = args.pop_size
    if args.pc is not None:
        config_base['pc'] = args.pc
    if args.pm is not None:
        config_base['pm'] = args.pm

    print(f"\n[INFO - GA Clásico] Escala: {escala_efectiva} | Generaciones: {config_base['epoch']} | Población: {config_base['pop_size']}")

    # 2. Pre-cómputo de dominios válidos
    valid_starts = precomputar_combinaciones_inicio(
        E, R, T, T_d, D, d_jue, Dur, EVENTO_SECCION, E_p, Alumno, Req, Tiene, F, CAP, ES_VIRTUAL, Disp
    )
    restricciones_curriculares = precomputar_restricciones_curriculares(
        K, E_k, EVENTO_SECCION, SECCION_CURSO, E
    )

    bounds = IntegerVar(lb=[0]*len(E), ub=[len(valid_starts[idx]) - 1 for idx in range(len(E))])

    # 3. Ejecución Multi-run
    n_corridas = args.corridas
    resultados_runs = []
    best_global_fitness = float('inf')
    best_global_solution = None
    best_global_hcv = float('inf')
    best_global_z = float('inf')

    print(f"[INFO - GA Clásico] Iniciando {n_corridas} corridas independientes...")
    print("=" * 80)

    for run in range(n_corridas):
        seed = 42 + run
        print(f"\n>>> [GA Clásico - CORRIDA {run + 1}/{n_corridas}] Semilla: {seed} ...")

        problem = UCTPProblemBase(
            E=E, R=R, T=T, D=D, T_d=T_d, P=P, S=S, K=K, E_k=E_k, E_p=E_p, E_s=E_s, Dur=Dur,
            EVENTO_SECCION=EVENTO_SECCION, SECCION_CURSO=SECCION_CURSO, Almuerzo=Almuerzo,
            valid_starts=valid_starts, restricciones_curriculares=restricciones_curriculares,
            bounds=bounds, ES_VIRTUAL=ES_VIRTUAL
        )

        ga_model = CustomGA(
            epoch=config_base['epoch'],
            pop_size=config_base['pop_size'],
            pc=config_base['pc'],
            pm=config_base['pm'],
            crossover=config_base['crossover'],
            selection=config_base['selection']
        )

        term_dict = {"max_epoch": config_base['epoch']}
        if max_seconds is not None:
            term_dict["max_time"] = max_seconds

        start_run_time = time.process_time()
        best_agent = ga_model.solve(problem, termination=term_dict, seed=seed)
        cpu_time = time.process_time() - start_run_time

        run_solution = best_agent.solution
        run_metrics = problem.evaluate_solution(run_solution)

        hcv = run_metrics['violaciones_restricciones_duras']
        z = run_metrics['penalizacion_blanda']
        ttf = ga_model.primer_tiempo_factible
        init_feas = ga_model.tasa_factibilidad_inicial

        is_better = False
        if best_global_solution is None:
            is_better = True
        else:
            if hcv < best_global_hcv:
                is_better = True
            elif hcv == best_global_hcv:
                if hcv == 0:
                    if z < best_global_z:
                        is_better = True
                else:
                    if best_agent.target.fitness < best_global_fitness:
                        is_better = True

        if is_better:
            best_global_fitness = best_agent.target.fitness
            best_global_solution = run_solution
            best_global_hcv = hcv
            best_global_z = z

        print(f"    Resultado: HCV={hcv} | Z={z:.2f} | Factible={'SÍ' if hcv == 0 else 'NO'} | CPU={cpu_time:.2f}s | NFE={problem.evaluaciones_aptitud}")
        if hcv == 0 and ttf is not None:
            print(f"    TTF: {ttf:.2f}s (Gen {ga_model.primera_gen_factible})")

        resultados_runs.append({
            "corrida": run + 1,
            "seed": seed,
            "Z": z,
            "HCV": hcv,
            "DF": hcv,
            "TTF": ttf if hcv == 0 else float('nan'),
            "CPU_time": cpu_time,
            "evaluaciones_aptitud": problem.evaluaciones_aptitud,
            "tasa_factib_inicial": init_feas,
            "factible": hcv == 0,
            "penalizacion_almuerzo": run_metrics['penalizacion_almuerzo'],
            "penalizacion_espaciado": run_metrics['penalizacion_espaciado'],
            "penalizacion_jueves": run_metrics['penalizacion_jueves'],
            "penalizacion_sabado": run_metrics['penalizacion_sabado'],
            "penalizacion_ventanas": run_metrics['penalizacion_ventanas'],
            "penalizacion_huecos": run_metrics['penalizacion_ventanas'],
            "hcv_colision_profesor": run_metrics['colision_profesor'],
            "hcv_carga_maxima_profesor": run_metrics['carga_maxima_profesor'],
            "hcv_estabilidad_salones": run_metrics['estabilidad_salones'],
            "hcv_colision_salones_fisicos": run_metrics['colision_salones_fisicos'],
            "hcv_conflicto_curricular": run_metrics['conflicto_curricular']
        })

    # 4. Consolidación estadística
    df_results = pd.DataFrame(resultados_runs)
    resultados_dir = "resultados_GA"
    os.makedirs(resultados_dir, exist_ok=True)
    csv_filepath = os.path.join(resultados_dir, f"resultados_{escala_efectiva}.csv")
    df_results.to_csv(csv_filepath, index=False)
    print(f"\n[ÉXITO] Resultados individuales GA persistidos en '{csv_filepath}'.")

    total_runs = len(df_results)
    factibles_df = df_results[df_results['factible'] == True]
    tasa_factibilidad = (len(factibles_df) / total_runs) * 100.0

    mejor_df = int(df_results['HCV'].min())
    promedio_df = float(df_results['HCV'].mean())

    if len(factibles_df) > 0:
        mejor_z = float(factibles_df['Z'].min())
        peor_z = float(factibles_df['Z'].max())
        promedio_z = float(factibles_df['Z'].mean())
        mediana_z = float(factibles_df['Z'].median())
        desviacion_z = float(factibles_df['Z'].std()) if len(factibles_df) > 1 else 0.0
        ttf_promedio = float(factibles_df['TTF'].mean())
    else:
        mejor_z = None
        peor_z = None
        promedio_z = None
        mediana_z = None
        desviacion_z = None
        ttf_promedio = None

    cpu_promedio = float(df_results['CPU_time'].mean())
    evals_promedio = float(df_results['evaluaciones_aptitud'].mean())

    resumen = {
        "metodo": "GA",
        "escala": escala_efectiva,
        "total_corridas": int(total_runs),
        "tasa_factibilidad_final": float(tasa_factibilidad),
        "mejor_df": mejor_df,
        "promedio_df": promedio_df,
        "ttf_promedio": ttf_promedio,
        "cpu_promedio": cpu_promedio,
        "evaluaciones_aptitud_promedio": evals_promedio,
        "mejor_z": mejor_z,
        "peor_z": peor_z,
        "promedio_z": promedio_z,
        "mediana_z": mediana_z,
        "desviacion_z": desviacion_z,
        "entorno": obtener_metadatos_entorno("mealpy.evolutionary_based.GA.BaseGA (Classical)", "3.0.x")
    }

    resumen_filepath = os.path.join(resultados_dir, f"resumen_{escala_efectiva}.json")
    with open(resumen_filepath, 'w', encoding='utf-8') as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)
    print(f"[ÉXITO] Resumen estadístico consolidado GA guardado en '{resumen_filepath}'.\n")

    # 5. Exportación del mejor horario encontrado
    if best_global_solution is not None:
        print("[INFO - GA Clásico] Exportando horario de la mejor corrida...")
        x_best = reconstruir_x_desde_ga(best_global_solution, valid_starts, E, Dur)
        out_path = f"horarios_{escala_efectiva}/GA"
        exportar_horarios(
            x=x_best, K=K, E_k=E_k, T_d=T_d, D=D,
            EVENTO_SECCION=EVENTO_SECCION, SECCION_CURSO=SECCION_CURSO, E_p=E_p,
            output_dir=out_path
        )


if __name__ == '__main__':
    main()
