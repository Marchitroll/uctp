"""Mixin de Mealpy para UCTP: seguimiento de factibilidad, TTF y parada temprana."""
import time


class MixinOptimizadorUCTP:
    """Mixin para registrar métricas experimentales y parada temprana."""

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
        resultado = super().solve(problem, **kwargs)

        if self.primera_gen_factible is None:
            violaciones_duras = self.problem.obtener_violaciones_duras(self.g_best.solution)
            if violaciones_duras == 0:
                self.primera_gen_factible = 0
                self.primer_tiempo_factible = 0.0
        return resultado

    def after_initialization(self):
        """Evalúa la tasa de factibilidad inicial en la población generada."""
        super().after_initialization()
        conteo_factibles = 0
        for agente in self.pop:
            if self.problem.obtener_violaciones_duras(agente.solution) == 0:
                conteo_factibles += 1
        self.tasa_factibilidad_inicial = (conteo_factibles / len(self.pop)) * 100.0 if self.pop else 0.0

    def track_optimize_step(self, pop=None, epoch=None, runtime=None):
        """Registra el avance de cada época y el TTF."""
        super().track_optimize_step(pop, epoch, runtime)
        if self.primera_gen_factible is None:
            violaciones_duras = self.problem.obtener_violaciones_duras(self.g_best.solution)
            if violaciones_duras == 0:
                self.primera_gen_factible = epoch
                self.primer_tiempo_factible = time.process_time() - self.tiempo_inicio

    def check_termination(self, mode="start", termination=None, epoch=None):
        """Parada temprana si una solución factible Z no mejora en `self.paciencia` épocas."""
        terminado = super().check_termination(mode, termination, epoch)
        if terminado:
            return True
        if mode == "end" and epoch is not None:
            violaciones_duras = self.problem.obtener_violaciones_duras(self.g_best.solution)
            if violaciones_duras == 0:
                costo_blando = self.problem.evaluar_solucion(self.g_best.solution)["penalizacion_blanda"]
                if costo_blando < self.mejor_z:
                    self.mejor_z = costo_blando
                    self.generaciones_sin_mejora_z = 0
                else:
                    self.generaciones_sin_mejora_z += 1

                if self.generaciones_sin_mejora_z >= self.paciencia:
                    self.logger.warning(
                        f"Criterio de parada temprana: solución factible convergió ({self.paciencia} iteraciones sin mejora)."
                    )
                    return True
        return False
