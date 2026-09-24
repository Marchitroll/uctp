import os
import sys
import time
import json
import argparse
import random
import numpy as np
import pandas as pd
from mealpy import IntegerVar
from mealpy.physics_based.SA import OriginalSA

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


class CustomSA(OriginalSA):
    """
    Subclase de OriginalSA adaptada para optimización combinatoria discreta en UCTP.
    Perturba soluciones discretamente seleccionando eventos e índices de inicio válidos,
    aplicando el criterio de aceptación de Metropolis con enfriamiento progresivo.
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
        self.tasa_factibilidad_inicial = (feasible_count / len(self.pop)) * 100.0 if len(self.pop) > 0 else 0.0

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
                
                # Parada si Z no mejora en 300 iteraciones consecutivas
                if self.generaciones_sin_mejora_z >= 300:
                    self.logger.warning("Criterio de parada: solución factible encontrada y Z convergió. ¡Finalizando corrida!")
                    return True
        return False

    def evolve(self, epoch):
        """
        Perturbación discreta y criterio de Metropolis adaptado para UCTP.
        """
        pos_new = self.agent_current.solution.copy()
        num_flips = 1 if self.generator.random() < 0.75 else 2
        dims_to_change = self.generator.choice(
            self.problem.num_events,
            size=min(num_flips, self.problem.num_events),
            replace=False
        )
        for d in dims_to_change:
            max_c = self.problem.max_choices[d]
            if max_c > 0:
                current_c = int(pos_new[d])
                new_c = self.generator.integers(0, max_c)
                if new_c >= current_c:
                    new_c += 1
                if new_c <= max_c:
                    pos_new[d] = new_c

        pos_new = self.correct_solution(pos_new)
        agent = self.generate_agent(pos_new)

        if self.compare_target(agent.target, self.agent_current.target, self.problem.minmax):
            self.agent_current = agent
        else:
            delta_energy = agent.target.fitness - self.agent_current.target.fitness
            current_temp = max(1e-5, self.temp_init / max(1, epoch))
            p_accept = np.exp(-delta_energy / current_temp)
            if self.generator.random() < p_accept:
                self.agent_current = agent

        self.pop = [self.g_best.copy(), self.agent_current.copy()]


def main():
    parser = argparse.ArgumentParser(description="Optimizador CB-CTT: Recocido Simulado (SA) con Movimiento Discreto.")
    parser.add_argument("--instancia", choices=["pequena", "mediana", "grande"], default=None,
                        help="Escala de la instancia a resolver (pequena, mediana, grande). Si no se define, se detecta por currículos.")
    parser.add_argument("--epoch", type=int, default=None, help="Número máximo de iteraciones por corrida.")
    parser.add_argument("--temp_init", type=float, default=None, help="Temperatura inicial.")
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
        'pequena': {'epoch': 5000, 'temp_init': 1000.0},
        'mediana': {'epoch': 15000, 'temp_init': 1500.0},
        'grande':  {'epoch': 30000, 'temp_init': 2000.0},
    }
    config_base = CONFIGS[escala_efectiva].copy()
    if args.epoch is not None:
        config_base['epoch'] = args.epoch
    if args.temp_init is not None:
        config_base['temp_init'] = args.temp_init

    print(f"\n[INFO - SA] Escala: {escala_efectiva} | Iteraciones: {config_base['epoch']} | Temp Inicial: {config_base['temp_init']}")

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

    print(f"[INFO - SA] Iniciando {n_corridas} corridas independientes de Recocido Simulado...")
    print("=" * 80)

    for run in range(n_corridas):
        seed = 42 + run
        print(f"\n>>> [SA - CORRIDA {run + 1}/{n_corridas}] Semilla: {seed} ...")

        problem = UCTPProblemBase(
            E=E, R=R, T=T, D=D, T_d=T_d, P=P, S=S, K=K, E_k=E_k, E_p=E_p, E_s=E_s, Dur=Dur,
            EVENTO_SECCION=EVENTO_SECCION, SECCION_CURSO=SECCION_CURSO, Almuerzo=Almuerzo,
            valid_starts=valid_starts, restricciones_curriculares=restricciones_curriculares,
            bounds=bounds, ES_VIRTUAL=ES_VIRTUAL
        )

        sa_model = CustomSA(
            epoch=config_base['epoch'],
            pop_size=2,
            temp_init=config_base['temp_init']
        )

        term_dict = {"max_epoch": config_base['epoch']}
        if max_seconds is not None:
            term_dict["max_time"] = max_seconds

        start_run_time = time.process_time()
        best_agent = sa_model.solve(problem, termination=term_dict, seed=seed)
        cpu_time = time.process_time() - start_run_time

        run_solution = best_agent.solution
        run_metrics = problem.evaluate_solution(run_solution)

        hcv = run_metrics['violaciones_restricciones_duras']
        z = run_metrics['penalizacion_blanda']
        ttf = sa_model.primer_tiempo_factible
        init_feas = sa_model.tasa_factibilidad_inicial

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
            print(f"    TTF: {ttf:.2f}s (Iter {sa_model.primera_gen_factible})")

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
    resultados_dir = "resultados_SA"
    os.makedirs(resultados_dir, exist_ok=True)
    csv_filepath = os.path.join(resultados_dir, f"resultados_{escala_efectiva}.csv")
    df_results.to_csv(csv_filepath, index=False)
    print(f"\n[ÉXITO] Resultados individuales SA persistidos en '{csv_filepath}'.")

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
        "metodo": "SA",
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
        "entorno": obtener_metadatos_entorno("mealpy.physics_based.SA.OriginalSA (Discrete)", "3.0.x")
    }

    resumen_filepath = os.path.join(resultados_dir, f"resumen_{escala_efectiva}.json")
    with open(resumen_filepath, 'w', encoding='utf-8') as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)
    print(f"[ÉXITO] Resumen estadístico consolidado SA guardado en '{resumen_filepath}'.\n")

    # 5. Exportación del mejor horario encontrado
    if best_global_solution is not None:
        print("[INFO - SA] Exportando horario de la mejor corrida...")
        x_best = reconstruir_x_desde_ga(best_global_solution, valid_starts, E, Dur)
        out_path = f"horarios_{escala_efectiva}/SA"
        exportar_horarios(
            x=x_best, K=K, E_k=E_k, T_d=T_d, D=D,
            EVENTO_SECCION=EVENTO_SECCION, SECCION_CURSO=SECCION_CURSO, E_p=E_p,
            output_dir=out_path
        )


if __name__ == '__main__':
    main()
