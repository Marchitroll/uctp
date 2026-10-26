"""Modelado y funciones de aptitud del problema UCTP para optimizadores Mealpy."""
import numpy as np
from mealpy import Problem

from uctp_utils import (
    construir_evento_profesor,
    construir_franja_a_dia,
    cargar_config_institucional,
)


class ProblemaUCTPBase(Problem):
    """Clase base del problema UCTP para metaheurísticas estándar."""

    def __init__(
        self,
        eventos: list[int],
        salones: list[str],
        franjas_horarias: list[int],
        dias: list[str],
        franjas_por_dia: dict[str, list[int]],
        profesores: list[str],
        secciones: list[str],
        curriculos: list[str],
        eventos_por_curriculo: dict[str, list[int]],
        eventos_por_profesor: dict[str, list[int]],
        eventos_por_seccion: dict[str, list[int]],
        duracion_por_evento: dict[int, int],
        seccion_por_evento: dict[int, str],
        curso_por_seccion: dict[str, str],
        almuerzo_por_dia: dict[str, int],
        inicios_validos: dict[int, list[tuple[str, int]]],
        restricciones_curriculares: list[dict],
        bounds,
        es_virtual_por_salon: dict[str, bool],
        peso_almuerzo: int = 1,
        peso_espaciado: int = 10,
        peso_jueves: int = 1,
        peso_sabado: int = 3,
        peso_ventanas: int = 2,
        **kwargs,
    ):
        self.eventos = eventos
        self.salones = salones
        self.franjas_horarias = franjas_horarias
        self.dias = dias
        self.franjas_por_dia = franjas_por_dia
        self.profesores = profesores
        self.secciones = secciones
        self.curriculos = curriculos
        self.eventos_por_curriculo = eventos_por_curriculo
        self.eventos_por_profesor = eventos_por_profesor
        self.eventos_por_seccion = eventos_por_seccion
        self.duracion_por_evento = duracion_por_evento
        self.seccion_por_evento = seccion_por_evento
        self.curso_por_seccion = curso_por_seccion
        self.almuerzo_por_dia = almuerzo_por_dia
        self.inicios_validos = inicios_validos
        self.restricciones_curriculares = restricciones_curriculares
        self.es_virtual_por_salon = es_virtual_por_salon

        cfg_pesos = cargar_config_institucional().get("pesos_penalizacion", {})
        self.peso_almuerzo = peso_almuerzo if peso_almuerzo is not None else cfg_pesos.get("W_A", 1)
        self.peso_espaciado = peso_espaciado if peso_espaciado is not None else cfg_pesos.get("W_E", 10)
        self.peso_jueves = peso_jueves if peso_jueves is not None else cfg_pesos.get("W_JUE", 1)
        self.peso_sabado = peso_sabado if peso_sabado is not None else cfg_pesos.get("W_SAB", 3)
        self.peso_ventanas = peso_ventanas if peso_ventanas is not None else cfg_pesos.get("W_V", 2)

        self.cantidad_eventos = len(eventos)
        self.cantidad_salones = len(salones)
        self.cantidad_franjas = len(franjas_horarias)
        self.cantidad_profesores = len(profesores)
        self.cantidad_secciones = len(secciones)
        self.cantidad_dias = len(dias)

        self.indice_por_salon = {salon: i for i, salon in enumerate(salones)}
        self.indice_por_franja = {franja: i for i, franja in enumerate(franjas_horarias)}
        self.indice_por_profesor = {prof: i for i, prof in enumerate(profesores)}
        self.indice_por_seccion = {seccion: i for i, seccion in enumerate(secciones)}

        self.dia_por_franja_idx = {}
        for indice_dia, dia in enumerate(dias):
            for franja in franjas_por_dia[dia]:
                self.dia_por_franja_idx[franja] = indice_dia

        self.franjas_por_dia_indices = {}
        for indice_dia, dia in enumerate(dias):
            self.franjas_por_dia_indices[indice_dia] = [self.indice_por_franja[franja] for franja in franjas_por_dia[dia]]

        evento_a_profesor = construir_evento_profesor(eventos_por_profesor)
        self.indice_profesor_por_evento = [self.indice_por_profesor[evento_a_profesor[evento]] for evento in eventos]
        self.duraciones_eventos = [duracion_por_evento[evento] for evento in eventos]

        self.eventos_de_seccion = []
        for seccion in secciones:
            eventos_sec = eventos_por_seccion[seccion]
            self.eventos_de_seccion.append([eventos.index(evento) for evento in eventos_sec])

        self.indices_salones_fisicos = [
            self.indice_por_salon[salon] for salon in salones if not es_virtual_por_salon[salon]
        ]
        self.conjunto_indices_salones_fisicos = set(self.indices_salones_fisicos)

        self.mascara_almuerzo = np.zeros(self.cantidad_franjas, dtype=np.int32)
        self.mascara_jueves = np.zeros(self.cantidad_franjas, dtype=np.int32)
        self.mascara_sabado = np.zeros(self.cantidad_franjas, dtype=np.int32)

        jueves_franjas = set(franjas_por_dia.get("Jueves", []))
        sabado_franjas = set(franjas_por_dia.get("Sabado", []))

        for franja_idx, franja in enumerate(franjas_horarias):
            self.mascara_almuerzo[franja_idx] = almuerzo_por_dia[franja]
            if franja in jueves_franjas:
                self.mascara_jueves[franja_idx] = 1
            if franja in sabado_franjas:
                self.mascara_sabado[franja_idx] = 1

        self.max_opciones_evento = np.array(
            [len(inicios_validos[idx]) - 1 for idx in range(self.cantidad_eventos)], dtype=np.int32
        )

        self.salones_elegibles_por_evento = [
            [self.indice_por_salon[salon] for salon, franja in inicios_validos[idx]]
            for idx in range(self.cantidad_eventos)
        ]
        self.franjas_validas_inicio = [
            [franja for salon, franja in inicios_validos[idx]] for idx in range(self.cantidad_eventos)
        ]

        self.restricciones_curriculares_por_evento = {idx: [] for idx in range(self.cantidad_eventos)}
        for restriccion in self.restricciones_curriculares:
            for idx in restriccion["eventos_curso"] + restriccion["eventos_otros_cursos"]:
                self.restricciones_curriculares_por_evento[idx].append(restriccion)

        self.franja_minima = min(franjas_horarias)
        self.mapeo_franja_a_dia = [0] * (max(franjas_horarias) + 1)
        for franja, indice_dia in self.dia_por_franja_idx.items():
            self.mapeo_franja_a_dia[franja] = indice_dia

        self.evaluaciones_aptitud = 0
        self.generador_aleatorio = np.random.default_rng(kwargs.get("seed", None))
        super().__init__(bounds=bounds, minmax="min", name="UCTP_Problem", **kwargs)

    def set_seed(self, seed: int = None) -> None:
        super().set_seed(seed)
        self.generador_aleatorio = np.random.default_rng(seed)

    def obj_func(self, solution):
        """Función objetivo exigida por el contrato Mealpy."""
        self.evaluaciones_aptitud += 1
        metricas = self.evaluar_solucion(solution)
        return 1000.0 * metricas["violaciones_restricciones_duras"] + 1.0 * metricas["penalizacion_blanda"]

    def correct_solution(self, solution):
        """Ajuste de límites exigido por el contrato Mealpy."""
        return np.clip(np.round(solution).astype(np.int32), 0, self.max_opciones_evento).astype(np.float64)

    def evaluar_solucion(self, solution):
        """Evalúa restricciones duras y blandas de un vector de decisión."""
        opciones = np.clip(np.round(solution).astype(np.int32), 0, self.max_opciones_evento)
        indices_salones = np.empty(self.cantidad_eventos, dtype=np.int32)
        franjas_inicio = np.empty(self.cantidad_eventos, dtype=np.int32)
        for idx in range(self.cantidad_eventos):
            opcion = opciones[idx]
            indices_salones[idx] = self.salones_elegibles_por_evento[idx][opcion]
            franjas_inicio[idx] = self.franjas_validas_inicio[idx][opcion]

        matriz_profesor_franja = np.zeros((self.cantidad_profesores, self.cantidad_franjas), dtype=np.int32)
        matriz_salon_franja = np.zeros((self.cantidad_salones, self.cantidad_franjas), dtype=np.int32)
        matriz_evento_franja = np.zeros((self.cantidad_eventos, self.cantidad_franjas), dtype=np.int32)

        for idx in range(self.cantidad_eventos):
            indice_profesor = self.indice_profesor_por_evento[idx]
            indice_salon = indices_salones[idx]
            duracion = self.duraciones_eventos[idx]
            franja_inicio = franjas_inicio[idx]

            for offset in range(duracion):
                indice_franja = self.indice_por_franja[franja_inicio + offset]
                matriz_profesor_franja[indice_profesor, indice_franja] += 1
                matriz_salon_franja[indice_salon, indice_franja] += 1
                matriz_evento_franja[idx, indice_franja] = 1

        viol_colision_profesor = int(np.sum(np.maximum(0, matriz_profesor_franja - 1)))

        viol_carga_maxima_profesor = 0
        for indice_dia in range(self.cantidad_dias):
            horas_diarias = np.sum(matriz_profesor_franja[:, self.franjas_por_dia_indices[indice_dia]], axis=1)
            viol_carga_maxima_profesor += int(np.sum(np.maximum(0, horas_diarias - 8)))

        viol_estabilidad_salones = 0
        for indice_seccion in range(self.cantidad_secciones):
            indices_eventos = self.eventos_de_seccion[indice_seccion]
            salones_distintos = len(np.unique(indices_salones[indices_eventos]))
            if salones_distintos > 2:
                viol_estabilidad_salones += salones_distintos - 2

        viol_colision_salones_fisicos = int(
            np.sum(np.maximum(0, matriz_salon_franja[self.indices_salones_fisicos, :] - 1))
        )

        viol_espaciado = 0
        for indice_seccion in range(self.cantidad_secciones):
            indices_eventos = self.eventos_de_seccion[indice_seccion]
            cantidad_eventos_seccion = len(indices_eventos)
            if cantidad_eventos_seccion <= 1:
                continue
            for indice_primera_sesion in range(cantidad_eventos_seccion):
                for indice_segunda_sesion in range(indice_primera_sesion + 1, cantidad_eventos_seccion):
                    dia_primera_sesion = self.dia_por_franja_idx[franjas_inicio[indices_eventos[indice_primera_sesion]]]
                    dia_segunda_sesion = self.dia_por_franja_idx[franjas_inicio[indices_eventos[indice_segunda_sesion]]]
                    if abs(dia_primera_sesion - dia_segunda_sesion) <= 1:
                        viol_espaciado += 1

        viol_conflicto_curricular = 0
        for restriccion in self.restricciones_curriculares:
            eventos_curso = restriccion["eventos_curso"]
            total_secciones = restriccion["total_secciones"]
            eventos_otros_cursos = restriccion["eventos_otros_cursos"]

            secciones_activas_en_franja = np.sum(matriz_evento_franja[eventos_curso, :], axis=0)
            franjas_llenas = np.where(secciones_activas_en_franja == total_secciones)[0]
            if len(franjas_llenas) > 0:
                viol_conflicto_curricular += int(np.sum(matriz_evento_franja[eventos_otros_cursos][:, franjas_llenas]))

        total_restricciones_duras = (
            viol_colision_profesor
            + viol_carga_maxima_profesor
            + viol_estabilidad_salones
            + viol_colision_salones_fisicos
            + viol_conflicto_curricular
        )

        penalizacion_almuerzo = int(np.sum(matriz_evento_franja * self.mascara_almuerzo))
        penalizacion_espaciado = viol_espaciado
        penalizacion_jueves = int(np.sum(matriz_evento_franja * self.mascara_jueves))
        penalizacion_sabado = int(np.sum(matriz_evento_franja * self.mascara_sabado))

        penalizacion_ventanas = 0
        for indice_profesor in range(self.cantidad_profesores):
            for indice_dia in range(self.cantidad_dias):
                franjas_dia = self.franjas_por_dia_indices[indice_dia]
                prof_dia = matriz_profesor_franja[indice_profesor, franjas_dia]
                indices_activos = np.where(prof_dia > 0)[0]
                if len(indices_activos) >= 2:
                    primer_idx = indices_activos[0]
                    ultimo_idx = indices_activos[-1]
                    for paso in range(primer_idx + 1, ultimo_idx):
                        if prof_dia[paso] == 0:
                            franja_global_idx = franjas_dia[paso]
                            if self.mascara_almuerzo[franja_global_idx] == 0:
                                penalizacion_ventanas += 1

        penalizacion_total_blanda = (
            self.peso_almuerzo * penalizacion_almuerzo
            + self.peso_espaciado * penalizacion_espaciado
            + self.peso_jueves * penalizacion_jueves
            + self.peso_sabado * penalizacion_sabado
            + self.peso_ventanas * penalizacion_ventanas
        )

        return {
            "violaciones_restricciones_duras": total_restricciones_duras,
            "penalizacion_blanda": penalizacion_total_blanda,
            "penalizacion_almuerzo": penalizacion_almuerzo,
            "penalizacion_espaciado": penalizacion_espaciado,
            "penalizacion_jueves": penalizacion_jueves,
            "penalizacion_sabado": penalizacion_sabado,
            "penalizacion_ventanas": penalizacion_ventanas,
            "colision_profesor": viol_colision_profesor,
            "carga_maxima_profesor": viol_carga_maxima_profesor,
            "estabilidad_salones": viol_estabilidad_salones,
            "colision_salones_fisicos": viol_colision_salones_fisicos,
            "infracciones_espaciado": viol_espaciado,
            "conflicto_curricular": viol_conflicto_curricular,
        }

    def obtener_violaciones_duras(self, solution):
        """Retorna la cantidad total de violaciones duras."""
        return self.evaluar_solucion(solution)["violaciones_restricciones_duras"]


class _EstadoAsignacion:
    """Estado de ocupación de recursos para la asignación heurística."""

    __slots__ = (
        "opciones_seleccionadas",
        "indices_salones",
        "franjas_inicio",
        "ocupacion_profesor_franja",
        "ocupacion_salon_franja",
        "ocupacion_evento_franja",
        "horas_diarias_profesor",
        "eventos_por_franja",
    )

    def __init__(
        self,
        cantidad_eventos: int,
        cantidad_profesores: int,
        cantidad_salones: int,
        cantidad_franjas: int,
        cantidad_dias: int,
    ):
        self.opciones_seleccionadas = np.full(cantidad_eventos, -1, dtype=np.int32)
        self.indices_salones = np.full(cantidad_eventos, -1, dtype=np.int32)
        self.franjas_inicio = np.full(cantidad_eventos, -1, dtype=np.int32)
        self.ocupacion_profesor_franja = [[0] * cantidad_franjas for _ in range(cantidad_profesores)]
        self.ocupacion_salon_franja = [[0] * cantidad_franjas for _ in range(cantidad_salones)]
        self.ocupacion_evento_franja = [[0] * cantidad_franjas for _ in range(cantidad_eventos)]
        self.horas_diarias_profesor = [[0] * cantidad_dias for _ in range(cantidad_profesores)]
        self.eventos_por_franja = [[] for _ in range(cantidad_franjas)]


class ProblemaUCTPMemetico(ProblemaUCTPBase):
    """Problema UCTP memético con operador heurístico constructivo y de reparación."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.carga_semanal_profesor = {}
        for profesor in self.profesores:
            self.carga_semanal_profesor[profesor] = sum(
                self.duracion_por_evento[evento] for evento in self.eventos_por_profesor[profesor]
            )

        evento_a_profesor = construir_evento_profesor(self.eventos_por_profesor)
        self.dificultad_evento = np.empty(self.cantidad_eventos, dtype=np.float64)
        for idx in range(self.cantidad_eventos):
            evento = self.eventos[idx]
            profesor = evento_a_profesor[evento]
            carga_docente = self.carga_semanal_profesor[profesor]
            opciones_inicio = len(self.inicios_validos[idx])
            self.dificultad_evento[idx] = (1000.0 / max(1, opciones_inicio)) + carga_docente

        self.orden_prioridad_eventos = np.argsort(self.dificultad_evento, kind="stable")[::-1]

    def _asignar_evento(self, estado: _EstadoAsignacion, idx: int, opcion: int) -> None:
        """Asigna un evento con una opción dada y actualiza las matrices de ocupación."""
        estado.opciones_seleccionadas[idx] = opcion
        indice_salon = self.salones_elegibles_por_evento[idx][opcion]
        franja_inicio = self.franjas_validas_inicio[idx][opcion]
        indice_profesor = self.indice_profesor_por_evento[idx]
        duracion = self.duraciones_eventos[idx]
        indice_dia = self.mapeo_franja_a_dia[franja_inicio]

        estado.indices_salones[idx] = indice_salon
        estado.franjas_inicio[idx] = franja_inicio
        for offset in range(duracion):
            indice_franja = franja_inicio + offset - self.franja_minima
            estado.ocupacion_profesor_franja[indice_profesor][indice_franja] += 1
            estado.ocupacion_salon_franja[indice_salon][indice_franja] += 1
            estado.ocupacion_evento_franja[idx][indice_franja] = 1
            estado.eventos_por_franja[indice_franja].append(idx)
        estado.horas_diarias_profesor[indice_profesor][indice_dia] += duracion

    def _desasignar_evento(self, estado: _EstadoAsignacion, idx: int) -> None:
        """Revierte la asignación de un evento y libera sus recursos en las matrices."""
        opcion = estado.opciones_seleccionadas[idx]
        if opcion == -1 or estado.franjas_inicio[idx] == -1:
            return
        indice_salon = estado.indices_salones[idx]
        franja_inicio = estado.franjas_inicio[idx]
        indice_profesor = self.indice_profesor_por_evento[idx]
        duracion = self.duraciones_eventos[idx]
        indice_dia = self.mapeo_franja_a_dia[franja_inicio]

        for offset in range(duracion):
            indice_franja = franja_inicio + offset - self.franja_minima
            estado.ocupacion_profesor_franja[indice_profesor][indice_franja] -= 1
            estado.ocupacion_salon_franja[indice_salon][indice_franja] -= 1
            estado.ocupacion_evento_franja[idx][indice_franja] = 0
            estado.eventos_por_franja[indice_franja].remove(idx)
        estado.horas_diarias_profesor[indice_profesor][indice_dia] -= duracion
        estado.indices_salones[idx] = -1
        estado.franjas_inicio[idx] = -1

    def _es_factible(self, estado: _EstadoAsignacion, idx: int, opcion: int) -> bool:
        """Verifica si asignar la opción al evento no viola ninguna restricción dura."""
        indice_salon = self.salones_elegibles_por_evento[idx][opcion]
        franja_inicio = self.franjas_validas_inicio[idx][opcion]
        indice_profesor = self.indice_profesor_por_evento[idx]
        duracion = self.duraciones_eventos[idx]
        indice_seccion = self.indice_por_seccion[self.seccion_por_evento[self.eventos[idx]]]

        for offset in range(duracion):
            indice_franja = franja_inicio + offset - self.franja_minima
            if estado.ocupacion_profesor_franja[indice_profesor][indice_franja] >= 1:
                return False
            if (
                indice_salon in self.conjunto_indices_salones_fisicos
                and estado.ocupacion_salon_franja[indice_salon][indice_franja] >= 1
            ):
                return False

        indice_dia = self.mapeo_franja_a_dia[franja_inicio]
        if estado.horas_diarias_profesor[indice_profesor][indice_dia] + duracion > 8:
            return False

        otros_eventos = [ev for ev in self.eventos_de_seccion[indice_seccion] if ev != idx]
        salones_asignados = [
            estado.indices_salones[ev] for ev in otros_eventos if estado.indices_salones[ev] != -1
        ]
        salones_unicos = set(salones_asignados)
        if indice_salon not in salones_unicos and len(salones_unicos) >= 2:
            return False

        for restriccion in self.restricciones_curriculares_por_evento[idx]:
            eventos_curso = restriccion["eventos_curso"]
            total_secciones = restriccion["total_secciones"]
            eventos_otros_cursos = restriccion["eventos_otros_cursos"]

            for offset in range(duracion):
                indice_franja = franja_inicio + offset - self.franja_minima
                if idx in eventos_curso:
                    secciones_activas_en_franja = sum(estado.ocupacion_evento_franja[ev][indice_franja] for ev in eventos_curso) + 1
                    if secciones_activas_en_franja == total_secciones:
                        if any(estado.ocupacion_evento_franja[ev][indice_franja] > 0 for ev in eventos_otros_cursos):
                            return False
                elif idx in eventos_otros_cursos:
                    secciones_activas_en_franja = sum(estado.ocupacion_evento_franja[ev][indice_franja] for ev in eventos_curso)
                    if secciones_activas_en_franja == total_secciones:
                        return False

        return True

    def _intentar_asignacion_directa(self, estado: _EstadoAsignacion, idx: int, opcion_actual: int) -> bool:
        """Intenta conservar la asignación actual si es factible sin conflictos."""
        if self._es_factible(estado, idx, opcion_actual):
            self._asignar_evento(estado, idx, opcion_actual)
            return True
        return False

    def _intentar_alternativa_greedy(self, estado: _EstadoAsignacion, idx: int, opcion_actual: int) -> bool:
        """Explora alternativas factibles en orden aleatorio para el evento."""
        total_opciones = len(self.franjas_validas_inicio[idx])
        inicio_aleatorio = int(self.generador_aleatorio.integers(0, total_opciones))

        for offset in range(total_opciones):
            opcion_candidata = (inicio_aleatorio + offset) % total_opciones
            if opcion_candidata == opcion_actual:
                continue
            if self._es_factible(estado, idx, opcion_candidata):
                self._asignar_evento(estado, idx, opcion_candidata)
                return True
        return False

    def _intentar_desplazamiento_1_paso(self, estado: _EstadoAsignacion, idx: int, opcion_actual: int) -> bool:
        """Aplica desplazamiento en cadena de 1 paso si un único evento obstaculiza la asignación."""
        total_opciones = len(self.franjas_validas_inicio[idx])
        inicio_desplazamiento = int(self.generador_aleatorio.integers(0, total_opciones))

        for offset in range(total_opciones):
            opcion_candidata = (inicio_desplazamiento + offset) % total_opciones
            if opcion_candidata == opcion_actual:
                continue

            salon_candidato = self.salones_elegibles_por_evento[idx][opcion_candidata]
            franja_candidata = self.franjas_validas_inicio[idx][opcion_candidata]
            duracion = self.duraciones_eventos[idx]
            indice_profesor = self.indice_profesor_por_evento[idx]

            eventos_bloqueantes = set()
            for offset_dur in range(duracion):
                indice_franja = franja_candidata + offset_dur - self.franja_minima
                for indice_evento in estado.eventos_por_franja[indice_franja]:
                    if indice_evento != idx:
                        if self.indice_profesor_por_evento[indice_evento] == indice_profesor:
                            eventos_bloqueantes.add(indice_evento)
                        if (
                            salon_candidato in self.conjunto_indices_salones_fisicos
                            and estado.indices_salones[indice_evento] == salon_candidato
                        ):
                            eventos_bloqueantes.add(indice_evento)

            if len(eventos_bloqueantes) == 1:
                indice_evento_bloqueante = sorted(eventos_bloqueantes)[0]
                opcion_bloqueante_actual = estado.opciones_seleccionadas[indice_evento_bloqueante]

                self._desasignar_evento(estado, indice_evento_bloqueante)

                total_opciones_bloqueante = len(self.franjas_validas_inicio[indice_evento_bloqueante])
                inicio_bloqueante = int(self.generador_aleatorio.integers(0, total_opciones_bloqueante))
                mejor_opcion_bloqueante = None

                for intento_reubicacion in range(total_opciones_bloqueante):
                    opcion_candidata_bloqueante = (inicio_bloqueante + intento_reubicacion) % total_opciones_bloqueante
                    if opcion_candidata_bloqueante == opcion_bloqueante_actual:
                        continue
                    if self._es_factible(estado, indice_evento_bloqueante, opcion_candidata_bloqueante):
                        mejor_opcion_bloqueante = opcion_candidata_bloqueante
                        break

                if mejor_opcion_bloqueante is not None and self._es_factible(estado, idx, opcion_candidata):
                    self._asignar_evento(estado, indice_evento_bloqueante, mejor_opcion_bloqueante)
                    self._asignar_evento(estado, idx, opcion_candidata)
                    return True
                else:
                    self._asignar_evento(estado, indice_evento_bloqueante, opcion_bloqueante_actual)

        return False

    def correct_solution(self, solution):
        """Ajusta y repara la solución usando heurística constructiva y búsqueda local."""
        opciones = np.clip(np.round(solution).astype(np.int32), 0, self.max_opciones_evento)
        estado = _EstadoAsignacion(
            self.cantidad_eventos,
            self.cantidad_profesores,
            self.cantidad_salones,
            self.cantidad_franjas,
            self.cantidad_dias,
        )
        estado.opciones_seleccionadas[:] = opciones

        for idx in self.orden_prioridad_eventos:
            opcion_actual = estado.opciones_seleccionadas[idx]

            if self._intentar_asignacion_directa(estado, idx, opcion_actual):
                continue
            if self._intentar_alternativa_greedy(estado, idx, opcion_actual):
                continue
            if self._intentar_desplazamiento_1_paso(estado, idx, opcion_actual):
                continue
            self._asignar_evento(estado, idx, opcion_actual)

        return estado.opciones_seleccionadas.astype(np.float64)


def precomputar_combinaciones_inicio(
    eventos: list[int],
    salones: list[str],
    franjas_horarias: list[int],
    franjas_por_dia: dict[str, list[int]],
    dias: list[str],
    dia_cierre_remoto: str,
    duracion_por_evento: dict[int, int],
    seccion_por_evento: dict[int, str],
    eventos_por_profesor: dict[str, list[int]],
    alumnos_por_seccion: dict[str, int],
    seccion_requiere_caracteristica: dict[tuple[str, str], int],
    salon_tiene_caracteristica: dict[tuple[str, str], int],
    caracteristicas: list[str],
    capacidad_por_salon: dict[str, int],
    es_virtual_por_salon: dict[str, bool],
    disponibilidad_por_profesor: dict[tuple[str, int], int],
) -> dict[int, list[tuple[str, int]]]:
    """Calcula las combinaciones válidas (salón, franja) para cada evento."""
    inicios_validos = {}
    evento_a_profesor = construir_evento_profesor(eventos_por_profesor)
    franja_a_dia = construir_franja_a_dia(franjas_por_dia)

    for idx_evento, evento in enumerate(eventos):
        combinaciones = []
        seccion = seccion_por_evento[evento]
        profesor = evento_a_profesor[evento]
        duracion = duracion_por_evento[evento]

        salones_elegibles = [
            salon
            for salon in salones
            if capacidad_por_salon[salon] >= alumnos_por_seccion[seccion]
            and all(
                seccion_requiere_caracteristica[(seccion, requisito_aula)]
                <= salon_tiene_caracteristica[(salon, requisito_aula)]
                for requisito_aula in caracteristicas
            )
        ]

        for salon in salones_elegibles:
            if es_virtual_por_salon[salon]:
                franjas_operativas = franjas_por_dia[dia_cierre_remoto]
            else:
                franjas_operativas = [
                    franja for franja in franjas_horarias if franja not in franjas_por_dia[dia_cierre_remoto]
                ]

            for franja in franjas_operativas:
                dia_franja = franja_a_dia.get(franja)
                if dia_franja is None:
                    continue

                if franja + duracion - 1 > max(franjas_por_dia[dia_franja]):
                    continue

                if all(
                    franja + offset in franjas_operativas
                    and disponibilidad_por_profesor.get((profesor, franja + offset), 0) == 1
                    for offset in range(duracion)
                ):
                    combinaciones.append((salon, franja))

        if not combinaciones:
            raise ValueError(f"El evento {evento} no tiene ninguna combinación de inicio válida.")
        inicios_validos[idx_evento] = combinaciones

    return inicios_validos


def precomputar_restricciones_curriculares(
    curriculos: list[str],
    eventos_por_curriculo: dict[str, list[int]],
    seccion_por_evento: dict[int, str],
    curso_por_seccion: dict[str, str],
    eventos: list[int],
) -> list[dict]:
    """Precomputa los conflictos curriculares para cursos multisección."""
    restricciones_curriculares = []
    for curriculo in curriculos:
        cursos_en_curriculo = {}
        for evento in eventos_por_curriculo[curriculo]:
            seccion = seccion_por_evento[evento]
            curso = curso_por_seccion[seccion]
            if curso not in cursos_en_curriculo:
                cursos_en_curriculo[curso] = []
            cursos_en_curriculo[curso].append(evento)

        for curso, eventos_curso in cursos_en_curriculo.items():
            secciones_unicas = set(seccion_por_evento[evento] for evento in eventos_curso)
            if len(secciones_unicas) > 1:
                total_secciones = len(secciones_unicas)
                eventos_otros = [evento for evento in eventos_por_curriculo[curriculo] if evento not in eventos_curso]

                indices_eventos_curso = [eventos.index(evento) for evento in eventos_curso]
                indices_eventos_otros = [eventos.index(evento) for evento in eventos_otros]

                restricciones_curriculares.append(
                    {
                        "eventos_curso": indices_eventos_curso,
                        "total_secciones": total_secciones,
                        "eventos_otros_cursos": indices_eventos_otros,
                    }
                )
    return restricciones_curriculares
