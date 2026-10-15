"""Recocido Simulado (Simulated Annealing - SA) para el problema UCTP / CB-CTT.

Implementa perturbación discreta adaptada a inicios válidos y criterio de aceptación
de Metropolis con enfriamiento progresivo y early stopping por convergencia.
"""
import numpy as np
from mealpy.physics_based.SA import OriginalSA

from base_optimizer_uctp import OptimizerUCTPMixin
from problema_uctp import UCTPProblemBase
from runner_metaheuristicas import crear_parser_metaheuristica, ejecutar_benchmark


class CustomSA(OptimizerUCTPMixin, OriginalSA):
    """Subclase de OriginalSA adaptada para optimización combinatoria discreta en UCTP."""

    def evolve(self, epoch):
        """Perturbación discreta y criterio de Metropolis adaptado para UCTP."""
        pos_new = self.agent_current.solution.copy()
        num_flips = 1 if self.generator.random() < 0.75 else 2
        dims_to_change = self.generator.choice(
            self.problem.num_events,
            size=min(num_flips, self.problem.num_events),
            replace=False,
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


CONFIGS_SA = {
    "pequena": {"epoch": 5000, "temp_init": 1000.0},
    "mediana": {"epoch": 15000, "temp_init": 1500.0},
    "grande":  {"epoch": 30000, "temp_init": 2000.0},
}


def obtener_parametros_mealpy(config_base, args):
    temp_init = args.temp_inicial if args.temp_inicial is not None else config_base["temp_init"]
    return {
        "epoch": config_base["epoch"],
        "temp_init": temp_init,
    }


def main():
    parser = crear_parser_metaheuristica("Recocido Simulado", paciencia_defecto=300)
    parser.add_argument(
        "--temp_inicial", "--temp_init",
        dest="temp_inicial",
        type=float,
        default=None,
        help="Temperatura inicial de enfriamiento",
    )
    args = parser.parse_args()

    ejecutar_benchmark(
        nombre_metodo="SA",
        clase_optimizador=CustomSA,
        clase_problema=UCTPProblemBase,
        args=args,
        configs_escala=CONFIGS_SA,
        obtener_parametros_mealpy=obtener_parametros_mealpy,
    )


if __name__ == "__main__":
    main()
