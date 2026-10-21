"""Algoritmo Genético Híbrido (HGA) para UCTP."""
from mealpy.evolutionary_based.GA import BaseGA

from base_optimizer_uctp import MixinOptimizadorUCTP
from problema_uctp import ProblemaUCTPMemetico
from runner_metaheuristicas import crear_parser_metaheuristica, ejecutar_benchmark


class OptimizadorHGA(MixinOptimizadorUCTP, BaseGA):
    """Algoritmo Genético Híbrido con reparación heurística."""
    pass


CONFIGS_HGA = {
    "pequena": {"epoch": 500, "pop_size": 50, "pc": 0.90, "pm": 0.05, "crossover": "uniform", "selection": "tournament"},
    "mediana": {"epoch": 800, "pop_size": 80, "pc": 0.90, "pm": 0.08, "crossover": "uniform", "selection": "tournament"},
    "grande":  {"epoch": 2000, "pop_size": 150, "pc": 0.85, "pm": 0.10, "crossover": "uniform", "selection": "tournament"},
}


def obtener_parametros_mealpy(config_base, args):
    pc = args.prob_cruce if args.prob_cruce is not None else config_base["pc"]
    pm = args.prob_mutacion if args.prob_mutacion is not None else config_base["pm"]
    pop_size = args.tam_poblacion if args.tam_poblacion is not None else config_base["pop_size"]
    return {
        "epoch": config_base["epoch"],
        "pop_size": pop_size,
        "pc": pc,
        "pm": pm,
        "crossover": config_base["crossover"],
        "selection": config_base["selection"],
    }


def main():
    parser = crear_parser_metaheuristica("HGA Memético", paciencia_defecto=20)
    parser.add_argument("--tam_poblacion", type=int, default=None, help="Tamaño de la población")
    parser.add_argument("--prob_cruce", type=float, default=None, help="Probabilidad de cruzamiento")
    parser.add_argument("--prob_mutacion", type=float, default=None, help="Probabilidad de mutación")
    args = parser.parse_args()

    ejecutar_benchmark(
        nombre_metodo="HGA",
        clase_optimizador=OptimizadorHGA,
        clase_problema=ProblemaUCTPMemetico,
        args=args,
        configs_escala=CONFIGS_HGA,
        obtener_parametros_mealpy=obtener_parametros_mealpy,
    )


if __name__ == "__main__":
    main()
