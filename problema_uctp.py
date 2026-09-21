import random
import numpy as np
from mealpy import Problem, IntegerVar


class UCTPProblemBase(Problem):
    """
    Clase base del problema UCTP para metaheurísticas (GA clásico, Tabu Search, Simulated Annealing).
    Opera sobre el espacio de búsqueda discretizado mediante la reducción de dominio (valid_starts).
    Su método correct_solution realiza únicamente el redondeo y recorte al dominio factible de índices,
    sin aplicar reparación heurística memética ni desplazamiento.
    """
    def __init__(self, E, R, T, D, T_d, P, S, K, E_k, E_p, E_s, Dur, EVENTO_SECCION, SECCION_CURSO, 
                 Almuerzo, valid_starts, restricciones_curriculares, bounds, ES_VIRTUAL, 
                 W_A=1, W_E=10, W_JUE=1, W_SAB=3, W_G=2, **kwargs):
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
        self.W_A = W_A
        self.W_E = W_E
        self.W_JUE = W_JUE
        self.W_SAB = W_SAB
        self.W_G = W_G
        
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
            
        self.event_p_idx = np.empty(self.num_events, dtype=np.int32)
        self.event_dur = np.empty(self.num_events, dtype=np.int32)
        for idx, e in enumerate(E):
            p = next(prof for prof, evs in E_p.items() if e in evs)
            self.event_p_idx[idx] = self.p_to_idx[p]
            self.event_dur[idx] = Dur[e]
            
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
        
        self.valid_starts_r_idx = {}
        self.valid_starts_t = {}
        for idx in range(self.num_events):
            self.valid_starts_r_idx[idx] = np.array([self.r_to_idx[r] for r, t in valid_starts[idx]], dtype=np.int32)
            self.valid_starts_t[idx] = np.array([t for r, t in valid_starts[idx]], dtype=np.int32)

        # Mapear cada evento a las restricciones curriculares en las que participa
        self.event_curriculum_constraints = {idx: [] for idx in range(self.num_events)}
        for constraint in self.restricciones_curriculares:
            for idx in constraint['evs_c'] + constraint['evs_other']:
                self.event_curriculum_constraints[idx].append(constraint)

        self.t_min = min(T)
        self.slot_to_day_idx_list = [0] * (max(T) + 1)
        for t, d_idx in self.slot_to_day_idx.items():
            self.slot_to_day_idx_list[t] = d_idx
        self.event_p_list = list(self.event_p_idx)
        self.event_dur_list = list(self.event_dur)
        self.valid_starts_r_idx_list = {idx: list(self.valid_starts_r_idx[idx]) for idx in range(self.num_events)}
        self.valid_starts_t_list = {idx: list(self.valid_starts_t[idx]) for idx in range(self.num_events)}

        self.evaluaciones_aptitud = 0
        self.generator = np.random.default_rng(kwargs.get("seed", None))
        super().__init__(bounds=bounds, minmax="min", name="UCTP_Problem", **kwargs)

    def set_seed(self, seed: int = None) -> None:
        super().set_seed(seed)
        self.generator = np.random.default_rng(seed)
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

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

        penalizacion_huecos = 0
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
                                penalizacion_huecos += 1

        total_blanda = (
            self.W_A * penalizacion_almuerzo + 
            self.W_E * penalizacion_espaciado + 
            self.W_JUE * penalizacion_jueves + 
            self.W_SAB * penalizacion_sabado + 
            self.W_G * penalizacion_huecos
        )
        
        return {
            'violaciones_restricciones_duras': hcv,
            'penalizacion_blanda': total_blanda,
            'penalizacion_almuerzo': penalizacion_almuerzo,
            'penalizacion_espaciado': penalizacion_espaciado,
            'penalizacion_jueves': penalizacion_jueves,
            'penalizacion_sabado': penalizacion_sabado,
            'penalizacion_huecos': penalizacion_huecos,
            'colision_profesor': viol_colision_profesor,
            'carga_maxima_profesor': viol_carga_maxima_profesor,
            'estabilidad_salones': viol_estabilidad_salones,
            'colision_salones_fisicos': viol_colision_salones_fisicos,
            'infracciones_espaciado': viol_espaciado,
            'conflicto_curricular': viol_conflicto_curricular
        }

    def get_hcv(self, solution):
        return self.evaluate_solution(solution)['violaciones_restricciones_duras']


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
        self.event_difficulty = np.empty(self.num_events, dtype=np.float64)
        for idx in range(self.num_events):
            e = self.E[idx]
            p = next(prof for prof, evs in self.E_p.items() if e in evs)
            p_load = self.teacher_weekly_load[p]
            num_choices = len(self.valid_starts[idx])
            self.event_difficulty[idx] = (1000.0 / max(1, num_choices)) + p_load
            
        # Ordenar eventos por dificultad descendente (Most Constrained First) con orden estable
        self.event_priority_order = np.argsort(self.event_difficulty, kind='stable')[::-1]

    def correct_solution(self, solution):
        choices = np.clip(np.round(solution).astype(np.int32), 0, self.max_choices)
        r_indices = np.full(self.num_events, -1, dtype=np.int32)
        t_starts = np.full(self.num_events, -1, dtype=np.int32)
        
        prof_slot = [[0] * self.num_slots for _ in range(self.num_teachers)]
        room_slot = [[0] * self.num_slots for _ in range(self.num_rooms)]
        event_slot = [[0] * self.num_slots for _ in range(self.num_events)]
        prof_daily_hours = [[0] * self.num_days for _ in range(self.num_teachers)]
        slot_events = [[] for _ in range(self.num_slots)]
        
        event_p_list = self.event_p_list
        event_dur_list = self.event_dur_list
        valid_starts_r_idx_list = self.valid_starts_r_idx_list
        valid_starts_t_list = self.valid_starts_t_list
        slot_to_day_idx_list = self.slot_to_day_idx_list
        t_min = self.t_min
        
        def remove_event(idx):
            c = choices[idx]
            if c == -1 or t_starts[idx] == -1:
                return
            r_idx = r_indices[idx]
            t_start = t_starts[idx]
            p_idx = event_p_list[idx]
            dur = event_dur_list[idx]
            d_idx = slot_to_day_idx_list[t_start]
            
            for offset in range(dur):
                t_idx = t_start + offset - t_min
                prof_slot[p_idx][t_idx] -= 1
                room_slot[r_idx][t_idx] -= 1
                event_slot[idx][t_idx] = 0
                slot_events[t_idx].remove(idx)
            prof_daily_hours[p_idx][d_idx] -= dur
            r_indices[idx] = -1
            t_starts[idx] = -1

        def add_event(idx, c):
            choices[idx] = c
            r_idx = valid_starts_r_idx_list[idx][c]
            t_start = valid_starts_t_list[idx][c]
            p_idx = event_p_list[idx]
            dur = event_dur_list[idx]
            d_idx = slot_to_day_idx_list[t_start]
            
            r_indices[idx] = r_idx
            t_starts[idx] = t_start
            for offset in range(dur):
                t_idx = t_start + offset - t_min
                prof_slot[p_idx][t_idx] += 1
                room_slot[r_idx][t_idx] += 1
                event_slot[idx][t_idx] = 1
                slot_events[t_idx].append(idx)
            prof_daily_hours[p_idx][d_idx] += dur

        def check_conflict_free(idx, c):
            r_idx = valid_starts_r_idx_list[idx][c]
            t_start = valid_starts_t_list[idx][c]
            p_idx = event_p_list[idx]
            dur = event_dur_list[idx]
            s_idx = self.s_to_idx[self.EVENTO_SECCION[self.E[idx]]]
            
            # 1. Colisión de profesor y salón físico
            for offset in range(dur):
                t_idx = t_start + offset - t_min
                if prof_slot[p_idx][t_idx] >= 1:
                    return False
                if r_idx in self.physical_room_indices_set and room_slot[r_idx][t_idx] >= 1:
                    return False
                    
            # 2. Carga diaria máxima del profesor (8 horas)
            d_idx = slot_to_day_idx_list[t_start]
            if prof_daily_hours[p_idx][d_idx] + dur > 8:
                return False
                
            # 3. Estabilidad de salones por sección (máximo 2 salones distintos)
            other_evs = [ev for ev in self.section_events[s_idx] if ev != idx]
            assigned_rooms = [r_indices[ev] for ev in other_evs if r_indices[ev] != -1]
            unique_assigned = set(assigned_rooms)
            if r_idx not in unique_assigned and len(unique_assigned) >= 2:
                return False
                
            # 4. Conflicto curricular
            for constraint in self.event_curriculum_constraints[idx]:
                evs_c = constraint['evs_c']
                num_secciones = constraint['num_secciones']
                evs_other = constraint['evs_other']
                
                for offset in range(dur):
                    t_idx = t_start + offset - t_min
                    if idx in evs_c:
                        active_c_at_t = 0
                        for ev in evs_c:
                            active_c_at_t += event_slot[ev][t_idx]
                        active_c_at_t += 1
                        if active_c_at_t == num_secciones:
                            has_other = False
                            for ev in evs_other:
                                if event_slot[ev][t_idx] > 0:
                                    has_other = True
                                    break
                            if has_other:
                                return False
                    elif idx in evs_other:
                        active_c_at_t = 0
                        for ev in evs_c:
                            active_c_at_t += event_slot[ev][t_idx]
                        if active_c_at_t == num_secciones:
                            return False
                            
            return True

        # Reparar/Construir eventos en orden de prioridad por saturación (MCF)
        for idx in self.event_priority_order:
            c_curr = choices[idx]
            
            if check_conflict_free(idx, c_curr):
                add_event(idx, c_curr)
                continue
                
            num_choices = len(valid_starts_t_list[idx])
            start_choice = int(self.generator.integers(0, num_choices))
            best_choice = None
            
            for offset in range(num_choices):
                c_cand = (start_choice + offset) % num_choices
                if c_cand == c_curr:
                    continue
                if check_conflict_free(idx, c_cand):
                    best_choice = c_cand
                    break
                    
            if best_choice is not None:
                add_event(idx, best_choice)
                continue
                
            # Desplazamiento en cadena de 1 paso
            displacement_success = False
            start_disp = int(self.generator.integers(0, num_choices))
            
            for offset in range(num_choices):
                c_cand = (start_disp + offset) % num_choices
                if c_cand == c_curr:
                    continue
                
                r_cand = valid_starts_r_idx_list[idx][c_cand]
                t_cand = valid_starts_t_list[idx][c_cand]
                dur = event_dur_list[idx]
                p_idx = event_p_list[idx]
                
                blocking_events = set()
                for offset_dur in range(dur):
                    t_idx = t_cand + offset_dur - t_min
                    for ev_idx in slot_events[t_idx]:
                        if ev_idx != idx:
                            if event_p_list[ev_idx] == p_idx:
                                blocking_events.add(ev_idx)
                            if r_cand in self.physical_room_indices_set and r_indices[ev_idx] == r_cand:
                                blocking_events.add(ev_idx)
                                
                if len(blocking_events) == 1:
                    idx_block = sorted(blocking_events)[0]
                    c_block_curr = choices[idx_block]
                    
                    remove_event(idx_block)
                    
                    num_block_choices = len(valid_starts_t_list[idx_block])
                    start_block = int(self.generator.integers(0, num_block_choices))
                    best_block_choice = None
                    
                    for offset_block in range(num_block_choices):
                        c_block_cand = (start_block + offset_block) % num_block_choices
                        if c_block_cand == c_block_curr:
                            continue
                        if check_conflict_free(idx_block, c_block_cand):
                            best_block_choice = c_block_cand
                            break
                            
                    if best_block_choice is not None and check_conflict_free(idx, c_cand):
                        add_event(idx_block, best_block_choice)
                        add_event(idx, c_cand)
                        displacement_success = True
                        break
                    else:
                        add_event(idx_block, c_block_curr)
                        
            if displacement_success:
                continue
                
            add_event(idx, c_curr)
            
        return choices.astype(np.float64)


def precomputar_combinaciones_inicio(E, R, T, T_d, D, d_jue, Dur, EVENTO_SECCION, E_p, Alumno, Req, Tiene, F, CAP, ES_VIRTUAL, Disp):
    """
    Filtra topológicamente las combinaciones válidas (salón, franja) para cada evento (reducción de dominio).
    """
    valid_starts = {}
    for idx_e, e in enumerate(E):
        starts = []
        s = EVENTO_SECCION[e]
        p_assigned = next(prof for prof, eventos_prof in E_p.items() if e in eventos_prof)
        
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
                dia_t = None
                for d, slots in T_d.items():
                    if t in slots:
                        dia_t = d
                        break
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
                    'evs_other': evs_other_idx,
                    'curr_id': k,
                    'course_id': c
                })
    return restricciones_curriculares
