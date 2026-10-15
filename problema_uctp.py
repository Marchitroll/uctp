import numpy as np
from mealpy import Problem, IntegerVar

from uctp_utils import (
    construir_evento_profesor,
    construir_franja_a_dia,
    cargar_config_institucional,
)


class UCTPProblemBase(Problem):
    """
    Clase base del problema UCTP para metaheurísticas (GA clásico, Tabu Search, Simulated Annealing).
    Opera sobre el espacio de búsqueda discretizado mediante la reducción de dominio (valid_starts).
    Su método correct_solution realiza únicamente el redondeo y recorte al dominio factible de índices,
    sin aplicar reparación heurística memética ni desplazamiento.
    """
    def __init__(self, E, R, T, D, T_d, P, S, K, E_k, E_p, E_s, Dur, EVENTO_SECCION, SECCION_CURSO, 
                 Almuerzo, valid_starts, restricciones_curriculares, bounds, ES_VIRTUAL, 
                 W_A=1, W_E=10, W_JUE=1, W_SAB=3, W_V=2, **kwargs):
        self.E = E
        self.R = R
        self.T = T
        self.D = D
        self.T_d = T_d
        self.P = P
        self.S = S
        self.K = K
        self.E_k = E_k
        self.E_p = E_p
        self.E_s = E_s
        self.Dur = Dur
        self.EVENTO_SECCION = EVENTO_SECCION
        self.SECCION_CURSO = SECCION_CURSO
        self.Almuerzo = Almuerzo
        self.valid_starts = valid_starts
        self.restricciones_curriculares = restricciones_curriculares
        self.ES_VIRTUAL = ES_VIRTUAL
        
        cfg_pesos = cargar_config_institucional().get("pesos_penalizacion", {})
        self.W_A = W_A if W_A is not None else cfg_pesos.get("W_A", 1)
        self.W_E = W_E if W_E is not None else cfg_pesos.get("W_E", 10)
        self.W_JUE = W_JUE if W_JUE is not None else cfg_pesos.get("W_JUE", 1)
        self.W_SAB = W_SAB if W_SAB is not None else cfg_pesos.get("W_SAB", 3)
        self.W_V = W_V if W_V is not None else cfg_pesos.get("W_V", 2)
        
        self.num_events = len(E)
        self.num_rooms = len(R)
        self.num_slots = len(T)
        self.num_teachers = len(P)
        self.num_sections = len(S)
        self.num_days = len(D)
        
        # Mapeos rápidos a índices de matriz
        self.r_to_idx = {r: i for i, r in enumerate(R)}
        self.t_to_idx = {t: i for i, t in enumerate(T)}
        self.p_to_idx = {p: i for i, p in enumerate(P)}
        self.s_to_idx = {s: i for i, s in enumerate(S)}
        
        self.slot_to_day_idx = {}
        for d_idx, d in enumerate(D):
            for t in T_d[d]:
                self.slot_to_day_idx[t] = d_idx
                
        self.day_slots_indices = {}
        for d_idx, d in enumerate(D):
            self.day_slots_indices[d_idx] = [self.t_to_idx[t] for t in T_d[d]]
            
        evento_a_prof = construir_evento_profesor(E_p)
        self.event_p_idx = [self.p_to_idx[evento_a_prof[e]] for e in E]
        self.event_dur = [Dur[e] for e in E]
            
        self.section_events = []
        for s_idx, s in enumerate(S):
            evs_in_s = E_s[s]
            self.section_events.append([E.index(e) for e in evs_in_s])
            
        self.physical_room_indices = [
            self.r_to_idx[r] for r in R if not ES_VIRTUAL[r]
        ]
        self.physical_room_indices_set = set(self.physical_room_indices)
        
        self.lunch_slots_mask = np.zeros(self.num_slots, dtype=np.int32)
        self.jueves_slots_mask = np.zeros(self.num_slots, dtype=np.int32)
        self.sabado_slots_mask = np.zeros(self.num_slots, dtype=np.int32)
        
        d_jue_set = set(T_d.get("Jueves", []))
        d_sab_set = set(T_d.get("Sabado", []))
        
        for t_idx, t in enumerate(T):
            self.lunch_slots_mask[t_idx] = Almuerzo[t]
            if t in d_jue_set:
                self.jueves_slots_mask[t_idx] = 1
            if t in d_sab_set:
                self.sabado_slots_mask[t_idx] = 1
            
        self.max_choices = np.array([len(valid_starts[idx]) - 1 for idx in range(self.num_events)], dtype=np.int32)
        
        self.valid_starts_r_idx = [
            [self.r_to_idx[r] for r, t in valid_starts[idx]] 
            for idx in range(self.num_events)
        ]
        self.valid_starts_t = [
            [t for r, t in valid_starts[idx]] 
            for idx in range(self.num_events)
        ]

        # Mapear cada evento a las restricciones curriculares en las que participa
        self.event_curriculum_constraints = {idx: [] for idx in range(self.num_events)}
        for constraint in self.restricciones_curriculares:
            for idx in constraint['evs_c'] + constraint['evs_other']:
                self.event_curriculum_constraints[idx].append(constraint)

        self.t_min = min(T)
        self.slot_to_day = [0] * (max(T) + 1)
        for t, d_idx in self.slot_to_day_idx.items():
            self.slot_to_day[t] = d_idx

        self.evaluaciones_aptitud = 0
        self.generator = np.random.default_rng(kwargs.get("seed", None))
        super().__init__(bounds=bounds, minmax="min", name="UCTP_Problem", **kwargs)

    def set_seed(self, seed: int = None) -> None:
        super().set_seed(seed)
        self.generator = np.random.default_rng(seed)

    def obj_func(self, solution):
        self.evaluaciones_aptitud += 1
        metrics = self.evaluate_solution(solution)
        return 1000.0 * metrics['violaciones_restricciones_duras'] + 1.0 * metrics['penalizacion_blanda']

    def correct_solution(self, solution):
        """
        Redondeo y truncamiento discreto simple sin reparación constructiva ni desplazamiento memético.
        """
        return np.clip(np.round(solution).astype(np.int32), 0, self.max_choices).astype(np.float64)

    def evaluate_solution(self, solution):
        choices = np.clip(np.round(solution).astype(np.int32), 0, self.max_choices)
        r_indices = np.empty(self.num_events, dtype=np.int32)
        t_starts = np.empty(self.num_events, dtype=np.int32)
        for idx in range(self.num_events):
            c = choices[idx]
            r_indices[idx] = self.valid_starts_r_idx[idx][c]
            t_starts[idx] = self.valid_starts_t[idx][c]
            
        prof_slot = np.zeros((self.num_teachers, self.num_slots), dtype=np.int32)
        room_slot = np.zeros((self.num_rooms, self.num_slots), dtype=np.int32)
        event_slot = np.zeros((self.num_events, self.num_slots), dtype=np.int32)
        
        for idx in range(self.num_events):
            p_idx = self.event_p_idx[idx]
            r_idx = r_indices[idx]
            dur = self.event_dur[idx]
            t_start = t_starts[idx]
            
            for offset in range(dur):
                t_idx = self.t_to_idx[t_start + offset]
                prof_slot[p_idx, t_idx] += 1
                room_slot[r_idx, t_idx] += 1
                event_slot[idx, t_idx] = 1
                
        viol_colision_profesor = int(np.sum(np.maximum(0, prof_slot - 1)))
        
        viol_carga_maxima_profesor = 0
        for d_idx in range(self.num_days):
            daily_hours = np.sum(prof_slot[:, self.day_slots_indices[d_idx]], axis=1)
            viol_carga_maxima_profesor += int(np.sum(np.maximum(0, daily_hours - 8)))
            
        viol_estabilidad_salones = 0
        for s_idx in range(self.num_sections):
            ev_indices = self.section_events[s_idx]
            unique_rooms = len(np.unique(r_indices[ev_indices]))
            if unique_rooms > 2:
                viol_estabilidad_salones += (unique_rooms - 2)
                
        viol_colision_salones_fisicos = int(np.sum(np.maximum(0, room_slot[self.physical_room_indices, :] - 1)))
        
        viol_espaciado = 0
        for s_idx in range(self.num_sections):
            ev_indices = self.section_events[s_idx]
            n_evs = len(ev_indices)
            if n_evs <= 1:
                continue
            for i in range(n_evs):
                for j in range(i + 1, n_evs):
                    d1 = self.slot_to_day_idx[t_starts[ev_indices[i]]]
                    d2 = self.slot_to_day_idx[t_starts[ev_indices[j]]]
                    if abs(d1 - d2) <= 1:
                        viol_espaciado += 1
                        
        viol_conflicto_curricular = 0
        for constraint in self.restricciones_curriculares:
            evs_c = constraint['evs_c']
            num_secciones = constraint['num_secciones']
            evs_other = constraint['evs_other']
            
            active_c = np.sum(event_slot[evs_c, :], axis=0)
            full_slots = np.where(active_c == num_secciones)[0]
            if len(full_slots) > 0:
                viol_conflicto_curricular += int(np.sum(event_slot[evs_other][:, full_slots]))
                
        hcv = (viol_colision_profesor + 
               viol_carga_maxima_profesor + 
               viol_estabilidad_salones + 
               viol_colision_salones_fisicos + 
               viol_conflicto_curricular)
               
        penalizacion_almuerzo = int(np.sum(event_slot * self.lunch_slots_mask))
        penalizacion_espaciado = viol_espaciado
        penalizacion_jueves = int(np.sum(event_slot * self.jueves_slots_mask))
        penalizacion_sabado = int(np.sum(event_slot * self.sabado_slots_mask))

        penalizacion_ventanas = 0
        for p_idx in range(self.num_teachers):
            for d_idx in range(self.num_days):
                day_slots = self.day_slots_indices[d_idx]
                prof_day = prof_slot[p_idx, day_slots]
                active_indices = np.where(prof_day > 0)[0]
                if len(active_indices) >= 2:
                    first_idx = active_indices[0]
                    last_idx = active_indices[-1]
                    for step in range(first_idx + 1, last_idx):
                        if prof_day[step] == 0:
                            slot_global_idx = day_slots[step]
                            if self.lunch_slots_mask[slot_global_idx] == 0:
                                penalizacion_ventanas += 1

        total_blanda = (
            self.W_A * penalizacion_almuerzo + 
            self.W_E * penalizacion_espaciado + 
            self.W_JUE * penalizacion_jueves + 
            self.W_SAB * penalizacion_sabado + 
            self.W_V * penalizacion_ventanas
        )
        
        return {
            'violaciones_restricciones_duras': hcv,
            'penalizacion_blanda': total_blanda,
            'penalizacion_almuerzo': penalizacion_almuerzo,
            'penalizacion_espaciado': penalizacion_espaciado,
            'penalizacion_jueves': penalizacion_jueves,
            'penalizacion_sabado': penalizacion_sabado,
            'penalizacion_ventanas': penalizacion_ventanas,
            'colision_profesor': viol_colision_profesor,
            'carga_maxima_profesor': viol_carga_maxima_profesor,
            'estabilidad_salones': viol_estabilidad_salones,
            'colision_salones_fisicos': viol_colision_salones_fisicos,
            'infracciones_espaciado': viol_espaciado,
            'conflicto_curricular': viol_conflicto_curricular
        }

    def get_hcv(self, solution):
        return self.evaluate_solution(solution)['violaciones_restricciones_duras']


class _EstadoAsignacion:
    """Estructura de seguimiento de estado para el operador constructivo heurístico MCF."""
    __slots__ = (
        'choices', 'r_indices', 't_starts',
        'prof_slot', 'room_slot', 'event_slot',
        'prof_daily_hours', 'slot_events'
    )

    def __init__(self, num_events: int, num_teachers: int, num_rooms: int, num_slots: int, num_days: int):
        self.choices = np.full(num_events, -1, dtype=np.int32)
        self.r_indices = np.full(num_events, -1, dtype=np.int32)
        self.t_starts = np.full(num_events, -1, dtype=np.int32)
        self.prof_slot = [[0] * num_slots for _ in range(num_teachers)]
        self.room_slot = [[0] * num_slots for _ in range(num_rooms)]
        self.event_slot = [[0] * num_slots for _ in range(num_events)]
        self.prof_daily_hours = [[0] * num_days for _ in range(num_teachers)]
        self.slot_events = [[] for _ in range(num_slots)]


class UCTPHybridProblem(UCTPProblemBase):
    """
    Variante híbrida memética del problema UCTP.
    Sobrescribe correct_solution incorporando el operador constructivo heurístico
    Most Constrained First (MCF) con aprendizaje lamarckiano y desplazamiento en cadena de 1 paso.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Calcular carga semanal de profesores para el ordenamiento por saturación
        self.teacher_weekly_load = {}
        for p in self.P:
            self.teacher_weekly_load[p] = sum(self.Dur[e] for e in self.E_p[p])
            
        # Calcular dificultad de cada evento (Saturación estructural + carga docente)
        evento_a_prof = construir_evento_profesor(self.E_p)
        self.event_difficulty = np.empty(self.num_events, dtype=np.float64)
        for idx in range(self.num_events):
            e = self.E[idx]
            p = evento_a_prof[e]
            p_load = self.teacher_weekly_load[p]
            num_choices = len(self.valid_starts[idx])
            self.event_difficulty[idx] = (1000.0 / max(1, num_choices)) + p_load
            
        # Ordenar eventos por dificultad descendente (Most Constrained First) con orden estable
        self.event_priority_order = np.argsort(self.event_difficulty, kind='stable')[::-1]

    def _asignar_evento(self, estado: _EstadoAsignacion, idx: int, c: int) -> None:
        """Asigna un evento con la opción c y actualiza las matrices de ocupación."""
        estado.choices[idx] = c
        r_idx = self.valid_starts_r_idx[idx][c]
        t_start = self.valid_starts_t[idx][c]
        p_idx = self.event_p_idx[idx]
        dur = self.event_dur[idx]
        d_idx = self.slot_to_day[t_start]
        
        estado.r_indices[idx] = r_idx
        estado.t_starts[idx] = t_start
        for offset in range(dur):
            t_idx = t_start + offset - self.t_min
            estado.prof_slot[p_idx][t_idx] += 1
            estado.room_slot[r_idx][t_idx] += 1
            estado.event_slot[idx][t_idx] = 1
            estado.slot_events[t_idx].append(idx)
        estado.prof_daily_hours[p_idx][d_idx] += dur

    def _desasignar_evento(self, estado: _EstadoAsignacion, idx: int) -> None:
        """Revierte la asignación de un evento y libera sus recursos en las matrices."""
        c = estado.choices[idx]
        if c == -1 or estado.t_starts[idx] == -1:
            return
        r_idx = estado.r_indices[idx]
        t_start = estado.t_starts[idx]
        p_idx = self.event_p_idx[idx]
        dur = self.event_dur[idx]
        d_idx = self.slot_to_day[t_start]
        
        for offset in range(dur):
            t_idx = t_start + offset - self.t_min
            estado.prof_slot[p_idx][t_idx] -= 1
            estado.room_slot[r_idx][t_idx] -= 1
            estado.event_slot[idx][t_idx] = 0
            estado.slot_events[t_idx].remove(idx)
        estado.prof_daily_hours[p_idx][d_idx] -= dur
        estado.r_indices[idx] = -1
        estado.t_starts[idx] = -1

    def _es_factible(self, estado: _EstadoAsignacion, idx: int, c: int) -> bool:
        """Verifica si asignar la opción c al evento idx no viola ninguna restricción dura."""
        r_idx = self.valid_starts_r_idx[idx][c]
        t_start = self.valid_starts_t[idx][c]
        p_idx = self.event_p_idx[idx]
        dur = self.event_dur[idx]
        s_idx = self.s_to_idx[self.EVENTO_SECCION[self.E[idx]]]
        
        # 1. Colisión de profesor y salón físico
        for offset in range(dur):
            t_idx = t_start + offset - self.t_min
            if estado.prof_slot[p_idx][t_idx] >= 1:
                return False
            if r_idx in self.physical_room_indices_set and estado.room_slot[r_idx][t_idx] >= 1:
                return False
                
        # 2. Carga diaria máxima del profesor (8 horas)
        d_idx = self.slot_to_day[t_start]
        if estado.prof_daily_hours[p_idx][d_idx] + dur > 8:
            return False
            
        # 3. Estabilidad de salones por sección (máximo 2 salones distintos)
        other_evs = [ev for ev in self.section_events[s_idx] if ev != idx]
        assigned_rooms = [estado.r_indices[ev] for ev in other_evs if estado.r_indices[ev] != -1]
        unique_assigned = set(assigned_rooms)
        if r_idx not in unique_assigned and len(unique_assigned) >= 2:
            return False
            
        # 4. Conflicto curricular
        for constraint in self.event_curriculum_constraints[idx]:
            evs_c = constraint['evs_c']
            num_secciones = constraint['num_secciones']
            evs_other = constraint['evs_other']
            
            for offset in range(dur):
                t_idx = t_start + offset - self.t_min
                if idx in evs_c:
                    active_c_at_t = 0
                    for ev in evs_c:
                        active_c_at_t += estado.event_slot[ev][t_idx]
                    active_c_at_t += 1
                    if active_c_at_t == num_secciones:
                        has_other = False
                        for ev in evs_other:
                            if estado.event_slot[ev][t_idx] > 0:
                                has_other = True
                                break
                        if has_other:
                            return False
                elif idx in evs_other:
                    active_c_at_t = 0
                    for ev in evs_c:
                        active_c_at_t += estado.event_slot[ev][t_idx]
                    if active_c_at_t == num_secciones:
                        return False
                        
        return True

    def _intentar_asignacion_directa(self, estado: _EstadoAsignacion, idx: int, c_curr: int) -> bool:
        """Intenta conservar la asignación actual si es factible sin conflictos."""
        if self._es_factible(estado, idx, c_curr):
            self._asignar_evento(estado, idx, c_curr)
            return True
        return False

    def _intentar_alternativa_greedy(self, estado: _EstadoAsignacion, idx: int, c_curr: int) -> bool:
        """Explora alternativas factibles en orden aleatorio para el evento."""
        num_choices = len(self.valid_starts_t[idx])
        start_choice = int(self.generator.integers(0, num_choices))
        
        for offset in range(num_choices):
            c_cand = (start_choice + offset) % num_choices
            if c_cand == c_curr:
                continue
            if self._es_factible(estado, idx, c_cand):
                self._asignar_evento(estado, idx, c_cand)
                return True
        return False

    def _intentar_desplazamiento_1_paso(self, estado: _EstadoAsignacion, idx: int, c_curr: int) -> bool:
        """Aplica desplazamiento en cadena de 1 paso si un único evento obstaculiza la asignación."""
        num_choices = len(self.valid_starts_t[idx])
        start_disp = int(self.generator.integers(0, num_choices))
        
        for offset in range(num_choices):
            c_cand = (start_disp + offset) % num_choices
            if c_cand == c_curr:
                continue
            
            r_cand = self.valid_starts_r_idx[idx][c_cand]
            t_cand = self.valid_starts_t[idx][c_cand]
            dur = self.event_dur[idx]
            p_idx = self.event_p_idx[idx]
            
            blocking_events = set()
            for offset_dur in range(dur):
                t_idx = t_cand + offset_dur - self.t_min
                for ev_idx in estado.slot_events[t_idx]:
                    if ev_idx != idx:
                        if self.event_p_idx[ev_idx] == p_idx:
                            blocking_events.add(ev_idx)
                        if r_cand in self.physical_room_indices_set and estado.r_indices[ev_idx] == r_cand:
                            blocking_events.add(ev_idx)
                            
            if len(blocking_events) == 1:
                idx_block = sorted(blocking_events)[0]
                c_block_curr = estado.choices[idx_block]
                
                self._desasignar_evento(estado, idx_block)
                
                num_block_choices = len(self.valid_starts_t[idx_block])
                start_block = int(self.generator.integers(0, num_block_choices))
                best_block_choice = None
                
                for offset_block in range(num_block_choices):
                    c_block_cand = (start_block + offset_block) % num_block_choices
                    if c_block_cand == c_block_curr:
                        continue
                    if self._es_factible(estado, idx_block, c_block_cand):
                        best_block_choice = c_block_cand
                        break
                        
                if best_block_choice is not None and self._es_factible(estado, idx, c_cand):
                    self._asignar_evento(estado, idx_block, best_block_choice)
                    self._asignar_evento(estado, idx, c_cand)
                    return True
                else:
                    self._asignar_evento(estado, idx_block, c_block_curr)
                    
        return False

    def correct_solution(self, solution):
        """
        Operador constructivo heurístico MCF con aprendizaje lamarckiano y desplazamiento en cadena.
        """
        choices = np.clip(np.round(solution).astype(np.int32), 0, self.max_choices)
        estado = _EstadoAsignacion(
            self.num_events, self.num_teachers, self.num_rooms, 
            self.num_slots, self.num_days
        )
        estado.choices[:] = choices

        for idx in self.event_priority_order:
            c_curr = estado.choices[idx]
            
            if self._intentar_asignacion_directa(estado, idx, c_curr):
                continue
            if self._intentar_alternativa_greedy(estado, idx, c_curr):
                continue
            if self._intentar_desplazamiento_1_paso(estado, idx, c_curr):
                continue
            self._asignar_evento(estado, idx, c_curr)
            
        return estado.choices.astype(np.float64)


def precomputar_combinaciones_inicio(E, R, T, T_d, D, d_jue, Dur, EVENTO_SECCION, E_p, Alumno, Req, Tiene, F, CAP, ES_VIRTUAL, Disp):
    """
    Filtra topológicamente las combinaciones válidas (salón, franja) para cada evento (reducción de dominio).
    """
    valid_starts = {}
    evento_a_prof = construir_evento_profesor(E_p)
    franja_a_dia = construir_franja_a_dia(T_d)

    for idx_e, e in enumerate(E):
        starts = []
        s = EVENTO_SECCION[e]
        p_assigned = evento_a_prof[e]
        
        salones_elegibles = [
            r for r in R 
            if CAP[r] >= Alumno[s] and all(Req[(s, f)] <= Tiene[(r, f)] for f in F)
        ]
        
        for r in salones_elegibles:
            if ES_VIRTUAL[r]:
                franjas_operativas = T_d[d_jue]
            else:
                franjas_operativas = [t for t in T if t not in T_d[d_jue]]
                
            for t in franjas_operativas:
                dia_t = franja_a_dia.get(t)
                if dia_t is None:
                    continue
                
                if t + Dur[e] - 1 > max(T_d[dia_t]):
                    continue
                    
                if all(t + offset in franjas_operativas and Disp.get((p_assigned, t + offset), 0) == 1 for offset in range(Dur[e])):
                    starts.append((r, t))
                    
        if not starts:
            raise ValueError(f"Infactibilidad crítica detectada: El evento {e} no tiene ninguna combinación de inicio válida.")
        valid_starts[idx_e] = starts
        
    return valid_starts


def precomputar_restricciones_curriculares(K, E_k, EVENTO_SECCION, SECCION_CURSO, E):
    """
    Precomputa las estructuras necesarias para la restricción de cursos multi-sección sin conflicto curricular.
    """
    restricciones_curriculares = []
    for k in K:
        cursos_en_k = {}
        for e in E_k[k]:
            s = EVENTO_SECCION[e]
            c = SECCION_CURSO[s]
            if c not in cursos_en_k:
                cursos_en_k[c] = []
            cursos_en_k[c].append(e)
            
        for c, evs_in_c in cursos_en_k.items():
            secciones_unicas = set(EVENTO_SECCION[e] for e in evs_in_c)
            if len(secciones_unicas) > 1:
                num_secciones = len(secciones_unicas)
                evs_other = [e for e in E_k[k] if e not in evs_in_c]
                
                evs_c_idx = [E.index(e) for e in evs_in_c]
                evs_other_idx = [E.index(e) for e in evs_other]
                
                restricciones_curriculares.append({
                    'evs_c': evs_c_idx,
                    'num_secciones': num_secciones,
                    'evs_other': evs_other_idx
                })
    return restricciones_curriculares
