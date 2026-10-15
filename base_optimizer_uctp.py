"""Clase base y mixin para optimizadores Mealpy en el ecosistema UCTP.

Centraliza el tracking de factibilidad inicial, TTF (Time-to-Feasibility),
convergencia de la función objetivo Z y parada temprana configurable (paciencia).
"""
import time


class OptimizerUCTPMixin:
    """Mixin que inyecta capacidades de auditoría experimental y parada temprana a Mealpy."""

    def __init__(self, *args, paciencia: int = 20, **kwargs):
        super().__init__(*args, **kwargs)
        self.paciencia = paciencia
        self.primera_gen_factible = None
        self.primer_tiempo_factible = None
        self.tiempo_inicio = None
        self.tasa_factibilidad_inicial = 0.0
        self.generaciones_sin_mejora_z = 0
        self.mejor_z = float("inf")

    def solve(self, problem, **kwargs):
        self.primera_gen_factible = None
        self.primer_tiempo_factible = None
        self.tiempo_inicio = time.process_time()
        self.generaciones_sin_mejora_z = 0
        self.mejor_z = float("inf")
        res = super().solve(problem, **kwargs)

        if self.primera_gen_factible is None:
            hcv = self.problem.get_hcv(self.g_best.solution)
            if hcv == 0:
                self.primera_gen_factible = 0
                self.primer_tiempo_factible = 0.0
        return res

    def after_initialization(self):
        """Evalúa la tasa de factibilidad inicial en la población generada."""
        super().after_initialization()
        feasible_count = 0
        for agent in self.pop:
            if self.problem.get_hcv(agent.solution) == 0:
                feasible_count += 1
        self.tasa_factibilidad_inicial = (feasible_count / len(self.pop)) * 100.0 if self.pop else 0.0

    def track_optimize_step(self, pop=None, epoch=None, runtime=None):
        """Registra el avance de cada época y el TTF."""
        super().track_optimize_step(pop, epoch, runtime)
        if self.primera_gen_factible is None:
            hcv = self.problem.get_hcv(self.g_best.solution)
            if hcv == 0:
                self.primera_gen_factible = epoch
                self.primer_tiempo_factible = time.process_time() - self.tiempo_inicio

    def check_termination(self, mode="start", termination=None, epoch=None):
        """Parada temprana si una solución factible Z no mejora en `self.paciencia` épocas."""
        finished = super().check_termination(mode, termination, epoch)
        if finished:
            return True
        if mode == "end" and epoch is not None:
            hcv = self.problem.get_hcv(self.g_best.solution)
            if hcv == 0:
                z = self.problem.evaluate_solution(self.g_best.solution)["penalizacion_blanda"]
                if z < self.mejor_z:
                    self.mejor_z = z
                    self.generaciones_sin_mejora_z = 0
                else:
                    self.generaciones_sin_mejora_z += 1

                if self.generaciones_sin_mejora_z >= self.paciencia:
                    self.logger.warning(
                        f"Criterio de parada temprana: solución factible convergió ({self.paciencia} iteraciones sin mejora)."
                    )
                    return True
        return False
