"""Búsqueda Tabú (Tabu Search - TS) para el problema UCTP / CB-CTT.

Implementa un vecindario discreto adaptado sobre inicios válidos, memoria tabú
de soluciones recientes, criterio de aspiración y early stopping por estancamiento.
"""
from collections import deque

import numpy as np
from mealpy.math_based.TS import OriginalTS

from base_optimizer_uctp import OptimizerUCTPMixin
from problema_uctp import UCTPProblemBase
from runner_metaheuristicas import crear_parser_metaheuristica, ejecutar_benchmark


class CustomTS(OptimizerUCTPMixin, OriginalTS):
    """Subclase de OriginalTS adaptada para optimización combinatoria discreta en UCTP."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optimización de estructura de datos: deque con maxlen para O(1) tabu list
        self.tabu_deque = deque(maxlen=self.tabu_size)

    def evolve(self, epoch):
        """Generación de vecindario discreto y selección del mejor candidato no tabú."""
        list_candidates = []
        attempts = 0
        max_attempts = self.neighbour_size * 5

        while len(list_candidates) < self.neighbour_size and attempts < max_attempts:
            attempts += 1
            cand = self.x.copy()
            num_flips = 1 if self.generator.random() < 0.75 else 2
            dims_to_change = self.generator.choice(
                self.problem.num_events,
                size=min(num_flips, self.problem.num_events),
                replace=False,
            )
            for d in dims_to_change:
                max_c = self.problem.max_choices[d]
                if max_c > 0:
                    current_c = int(cand[d])
                    new_c = self.generator.integers(0, max_c)
                    if new_c >= current_c:
                        new_c += 1
                    if new_c <= max_c:
                        cand[d] = new_c

            cand = self.correct_solution(cand)
            if np.allclose(cand, self.x):
                continue
            cand_tuple = tuple(cand)
            if cand_tuple in self.tabu_deque or cand_tuple in self.tabu_list:
                continue

            agent = self.generate_empty_agent(cand)
            if self.mode not in self.AVAILABLE_MODES:
                agent.target = self.get_target(cand)
            list_candidates.append(agent)

        # Fallback si todos los candidatos generados eran tabú
        if len(list_candidates) == 0:
            cand = self.x.copy()
            d = self.generator.integers(0, self.problem.num_events)
            max_c = self.problem.max_choices[d]
            if max_c > 0:
                cand[d] = (int(cand[d]) + 1) % (max_c + 1)
            agent = self.generate_empty_agent(cand)
            if self.mode not in self.AVAILABLE_MODES:
                agent.target = self.get_target(cand)
            list_candidates.append(agent)

        list_candidates = self.update_target_for_population(list_candidates)
        best_candidate = self.get_best_agent(list_candidates, self.problem.minmax)
        self.x = best_candidate.solution

        cand_tuple = tuple(self.x)
        self.tabu_deque.append(cand_tuple)
        self.tabu_list.append(cand_tuple)
        self.pop.append(best_candidate)
        if len(self.tabu_list) > self.tabu_size:
            self.tabu_list.pop(0)
            self.pop.pop(0)


CONFIGS_TS = {
    "pequena": {"epoch": 1000, "neighbour_size": 20, "tabu_size": 15},
    "mediana": {"epoch": 2000, "neighbour_size": 30, "tabu_size": 25},
    "grande":  {"epoch": 5000, "neighbour_size": 40, "tabu_size": 40},
}


def obtener_parametros_mealpy(config_base, args):
    neighbour_size = args.tam_vecindario if args.tam_vecindario is not None else config_base["neighbour_size"]
    tabu_size = args.tam_tabu if args.tam_tabu is not None else config_base["tabu_size"]
    return {
        "epoch": config_base["epoch"],
        "neighbour_size": neighbour_size,
        "tabu_size": tabu_size,
    }


def main():
    parser = crear_parser_metaheuristica("Búsqueda Tabú", paciencia_defecto=100)
    parser.add_argument(
        "--tam_vecindario", "--neighbour_size",
        dest="tam_vecindario",
        type=int,
        default=None,
        help="Cantidad de soluciones candidatas generadas en cada iteración",
    )
    parser.add_argument(
        "--tam_tabu", "--tabu_size",
        dest="tam_tabu",
        type=int,
        default=None,
        help="Capacidad máxima de la memoria tabú",
    )
    args = parser.parse_args()

    ejecutar_benchmark(
        nombre_metodo="TS",
        clase_optimizador=CustomTS,
        clase_problema=UCTPProblemBase,
        args=args,
        configs_escala=CONFIGS_TS,
        obtener_parametros_mealpy=obtener_parametros_mealpy,
    )


if __name__ == "__main__":
    main()
