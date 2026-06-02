"""
modelo_GA.py
Módulo principal encargado de la optimización del problema UCTP mediante
un Algoritmo Genético (GA) utilizando la librería MEALPY.
"""

import argparse
import time
import os
import random
import numpy as np
import pandas as pd
from mealpy import Problem, IntegerVar
from mealpy.evolutionary_based.GA import BaseGA

from cargador_datos import cargar_datos_uctp
from exportador_horarios import imprimir_metricas_ga, exportar_horarios, reconstruir_x_desde_ga

# ============================================================================
# PARSEO DE ARGUMENTOS CLI
# ============================================================================
parser = argparse.ArgumentParser(description="Optimizador GA para UCTP usando MEALPY")
time_group = parser.add_mutually_exclusive_group()
time_group.add_argument(
    "--horas", "-hr",
    type=float,
    help="Tiempo maximo de optimizacion en horas por corrida"
)
time_group.add_argument(
    "--minutos", "-min",
    type=float,
    help="Tiempo maximo de optimizacion en minutos por corrida"
)
parser.add_argument(
    "--corridas", "-c",
    type=int,
    default=1,
    help="Numero de corridas independientes (default: 1, formal: 20)"
)
parser.add_argument(
    "--epoch", "-ep",
    type=int,
    help="Numero maximo de generaciones (epochs)"
)
parser.add_argument(
    "--pop-size", "-pop",
    type=int,
    help="Tamaño de la poblacion"
)
parser.add_argument(
    "--pc",
    type=float,
    help="Probabilidad de crossover"
)
parser.add_argument(
    "--pm",
    type=float,
    help="Probabilidad de mutacion"
)
parser.add_argument(
    "--instancia", "-i",
    choices=["pequena", "mediana", "grande"],
    help="Forzar configuracion de escala especifica"
)
args = parser.parse_args()

# Determinar límites de tiempo
if args.horas is not None:
    max_seconds = args.horas * 3600.0
    tiempo_desc = f"{args.horas} horas"
elif args.minutos is not None:
    max_seconds = args.minutos * 60.0
    tiempo_desc = f"{args.minutos} minutos"
else:
    max_seconds = None
    tiempo_desc = "sin limite de tiempo"

# Pesos de penalización constantes de la función objetivo (Sección 4.3)
W_A = 1
W_E = 10

# ============================================================================
# CARGA DE DATOS Y CONJUNTOS
# ============================================================================
(
    D, T, T_d, d_jue, Almuerzo,
    R, CAP, ES_VIRTUAL, CARACTERISTICAS,
    CURSOS, REQ_CURSO,
    S, SECCION_CURSO, Alumno,
    E, E_s, E_p, Dur, EVENTO_SECCION,
    P, K, E_k, Disp,
    F, Tiene, Req, Cursos_Agrupados
) = cargar_datos_uctp()

# Auto-detección de escala por len(K)
if len(K) == 1:
    escala_detectada = "pequena"
elif len(K) in [4, 5]:
    escala_detectada = "mediana"
else:
    escala_detectada = "grande"

escala_efectiva = args.instancia if args.instancia is not None else escala_detectada

# Configuraciones por defecto según escala
CONFIGS = {
    'pequena': {
        'epoch': 500,
        'pop_size': 50,
        'pc': 0.90,
        'pm': 0.05,
        'crossover': 'uniform',
        'selection': 'tournament',
    },
    'mediana': {
        'epoch': 800,
        'pop_size': 80,
        'pc': 0.90,
        'pm': 0.08,
        'crossover': 'uniform',
        'selection': 'tournament',
    },
    'grande': {
        'epoch': 2000,
        'pop_size': 150,
        'pc': 0.85,
        'pm': 0.10,
        'crossover': 'uniform',
        'selection': 'tournament',
    },
}

config_base = CONFIGS[escala_efectiva].copy()

# Sobreescribir configuraciones por CLI si están definidas
if args.epoch is not None:
    config_base['epoch'] = args.epoch
if args.pop_size is not None:
    config_base['pop_size'] = args.pop_size
if args.pc is not None:
    config_base['pc'] = args.pc
if args.pm is not None:
    config_base['pm'] = args.pm

print(f"[INFO] Escala detectada: {escala_detectada} | Escala efectiva: {escala_efectiva}")
print(f"       Configuracion: Epochs={config_base['epoch']} | PopSize={config_base['pop_size']} | CrossoverProb={config_base['pc']} | MutationProb={config_base['pm']}")

# ============================================================================
# CLASE DEL PROBLEMA UCTP PARA MEALPY
# ============================================================================
class UCTPProblem(Problem):
    def __init__(self, E, R, T, D, T_d, P, S, K, E_k, E_p, E_s, Dur, EVENTO_SECCION, SECCION_CURSO, 
                 Almuerzo, valid_starts, r9_constraints, bounds, ES_VIRTUAL, **kwargs):
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
        self.r9_constraints = r9_constraints
        
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
        for t_idx, t in enumerate(T):
            self.lunch_slots_mask[t_idx] = Almuerzo[t]
            
        self.max_choices = np.array([len(valid_starts[idx]) - 1 for idx in range(self.num_events)], dtype=np.int32)
        
        self.valid_starts_r_idx = {}
        self.valid_starts_t = {}
        for idx in range(self.num_events):
            self.valid_starts_r_idx[idx] = np.array([self.r_to_idx[r] for r, t in valid_starts[idx]], dtype=np.int32)
            self.valid_starts_t[idx] = np.array([t for r, t in valid_starts[idx]], dtype=np.int32)
            
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
            
        # Ordenar eventos por dificultad descendente (Most Constrained First)
        self.event_priority_order = np.argsort(self.event_difficulty)[::-1]
        
        # Mapear cada evento a las restricciones R9 en las que participa para acelerar la validación
        self.event_r9_constraints = {idx: [] for idx in range(self.num_events)}
        for constraint in self.r9_constraints:
            for idx in constraint['evs_c'] + constraint['evs_other']:
                self.event_r9_constraints[idx].append(constraint)

        # Atributos optimizados para correct_solution (acceso directo sin NumPy)
        self.t_min = min(T)
        self.slot_to_day_idx_list = [0] * (max(T) + 1)
        for t, d_idx in self.slot_to_day_idx.items():
            self.slot_to_day_idx_list[t] = d_idx
        self.event_p_list = list(self.event_p_idx)
        self.event_dur_list = list(self.event_dur)
        self.valid_starts_r_idx_list = {idx: list(self.valid_starts_r_idx[idx]) for idx in range(self.num_events)}
        self.valid_starts_t_list = {idx: list(self.valid_starts_t[idx]) for idx in range(self.num_events)}

        self.fitness_evals = 0
        super().__init__(bounds=bounds, minmax="min", name="UCTP_Problem", **kwargs)

    def obj_func(self, solution):
        self.fitness_evals += 1
        metrics = self.evaluate_solution(solution)
        return 1000.0 * metrics['violaciones_restricciones_duras'] + 1.0 * metrics['penalizacion_blanda']

    def correct_solution(self, solution):
        choices = np.clip(np.round(solution).astype(np.int32), 0, self.max_choices)
        r_indices = np.full(self.num_events, -1, dtype=np.int32)
        t_starts = np.full(self.num_events, -1, dtype=np.int32)
        
        prof_slot = [[0] * self.num_slots for _ in range(self.num_teachers)]
        room_slot = [[0] * self.num_slots for _ in range(self.num_rooms)]
        event_slot = [[0] * self.num_slots for _ in range(self.num_events)]
        prof_daily_hours = [[0] * self.num_days for _ in range(self.num_teachers)]
        slot_events = [[] for _ in range(self.num_slots)]
        
        # Atributos pre-computados cacheados en variables locales para evitar lookups de atributos
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
                
            # 4. Oferta curricular sin conflicto (R9)
            for constraint in self.event_r9_constraints[idx]:
                evs_c = constraint['evs_c']
                num_secciones = constraint['num_secciones']
                evs_other = constraint['evs_other']
                
                for offset in range(dur):
                    t_idx = t_start + offset - t_min
                    if idx in evs_c:
                        active_c_at_t = 0
                        for ev in evs_c:
                            active_c_at_t += event_slot[ev][t_idx]
                        active_c_at_t += 1 # Incluir el candidato actual
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

        # Reparar/Construir eventos en orden de prioridad por saturación (Most Constrained First)
        # Colocamos los eventos uno por uno, validando conflictos solo contra los ya asignados.
        for idx in self.event_priority_order:
            c_curr = choices[idx]
            
            # Si la posición actual es factible con respecto a lo ya asignado, mantenerla
            if check_conflict_free(idx, c_curr):
                add_event(idx, c_curr)
                continue
                
            # Buscar una alternativa factible sin conflictos
            num_choices = len(valid_starts_t_list[idx])
            start_choice = random.randrange(num_choices)
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
                
            # Desplazamiento en cadena de 1 paso (1-step displacement)
            displacement_success = False
            start_disp = random.randrange(num_choices)
            
            for offset in range(num_choices):
                c_cand = (start_disp + offset) % num_choices
                if c_cand == c_curr:
                    continue
                
                # Identificar bloqueadores para este inicio candidato
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
                                
                # Si el bloqueo es causado por un único evento, intentar desplazarlo
                if len(blocking_events) == 1:
                    idx_block = list(blocking_events)[0]
                    c_block_curr = choices[idx_block]
                    
                    remove_event(idx_block)
                    
                    # Buscar una alternativa conflict-free para el evento bloqueador
                    num_block_choices = len(valid_starts_t_list[idx_block])
                    start_block = random.randrange(num_block_choices)
                    best_block_choice = None
                    
                    for offset_block in range(num_block_choices):
                        c_block_cand = (start_block + offset_block) % num_block_choices
                        if c_block_cand == c_block_curr:
                            continue
                        if check_conflict_free(idx_block, c_block_cand):
                            best_block_choice = c_block_cand
                            break
                            
                    # Si el bloqueador se puede reubicar y el candidato de idx ahora está libre:
                    if best_block_choice is not None and check_conflict_free(idx, c_cand):
                        add_event(idx_block, best_block_choice)
                        add_event(idx, c_cand)
                        displacement_success = True
                        break
                    else:
                        # Si falló, restaurar al bloqueador a su estado original
                        add_event(idx_block, c_block_curr)
                        
            if displacement_success:
                continue
                
            # Si todo falla, restaurar la posición original con conflicto
            add_event(idx, c_curr)
            
        return choices.astype(np.float64)

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
                
        prof_collision_viol = int(np.sum(np.maximum(0, prof_slot - 1)))
        
        prof_carga_viol = 0
        for d_idx in range(self.num_days):
            daily_hours = np.sum(prof_slot[:, self.day_slots_indices[d_idx]], axis=1)
            prof_carga_viol += int(np.sum(np.maximum(0, daily_hours - 8)))
            
        salon_estabilidad_viol = 0
        for s_idx in range(self.num_sections):
            ev_indices = self.section_events[s_idx]
            unique_rooms = len(np.unique(r_indices[ev_indices]))
            if unique_rooms > 2:
                salon_estabilidad_viol += (unique_rooms - 2)
                
        salon_collision_viol = int(np.sum(np.maximum(0, room_slot[self.physical_room_indices, :] - 1)))
        
        espaciado_viol = 0
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
                        espaciado_viol += 1
                        
        r9_viol = 0
        for constraint in self.r9_constraints:
            evs_c = constraint['evs_c']
            num_secciones = constraint['num_secciones']
            evs_other = constraint['evs_other']
            
            active_c = np.sum(event_slot[evs_c, :], axis=0)
            full_slots = np.where(active_c == num_secciones)[0]
            if len(full_slots) > 0:
                r9_viol += int(np.sum(event_slot[evs_other][:, full_slots]))
                
        hcv = (prof_collision_viol + 
               prof_carga_viol + 
               salon_estabilidad_viol + 
               salon_collision_viol + 
               r9_viol)
               
        lunch_penalty = int(np.sum(event_slot * self.lunch_slots_mask))
        spacing_penalty = espaciado_viol
        total_soft = W_A * lunch_penalty + W_E * spacing_penalty
        
        return {
            'violaciones_restricciones_duras': hcv,
            'penalizacion_blanda': total_soft,
            'P_almuerzo': lunch_penalty,
            'P_espaciado': spacing_penalty,
            'disponibilidad_y_no_colision_profesor': prof_collision_viol,
            'carga_diaria_maxima_profesor': prof_carga_viol,
            'estabilidad_salones': salon_estabilidad_viol,
            'no_colision_salones_fisicos': salon_collision_viol,
            'infracciones_espaciado': espaciado_viol,
            'oferta_curricular_sin_conflicto': r9_viol
        }

    def get_hcv(self, solution):
        return self.evaluate_solution(solution)['violaciones_restricciones_duras']

# ============================================================================
# CLASE DEL ALGORITMO GENÉTICO PERSONALIZADO (MÉTRICAS Y TRAZABILIDAD)
# ============================================================================
class CustomGA(BaseGA):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.first_feasible_epoch = None
        self.first_feasible_time = None
        self.start_wall_time = None
        self.init_feasibility_rate = 0.0
        self.epochs_no_improve_z = 0
        self.best_z = float('inf')

    def solve(self, problem, **kwargs):
        self.first_feasible_epoch = None
        self.first_feasible_time = None
        self.start_wall_time = time.time()
        self.epochs_no_improve_z = 0
        self.best_z = float('inf')
        res = super().solve(problem, **kwargs)
        
        # Comprobación de factibilidad al final por si ocurrió en inicialización
        if self.first_feasible_epoch is None:
            hcv = self.problem.get_hcv(self.g_best.solution)
            if hcv == 0:
                self.first_feasible_epoch = 0
                self.first_feasible_time = 0.0
        return res

    def after_initialization(self):
        super().after_initialization()
        # Evaluar factibilidad inicial de la población generada
        feasible_count = 0
        for agent in self.pop:
            hcv = self.problem.get_hcv(agent.solution)
            if hcv == 0:
                feasible_count += 1
        self.init_feasibility_rate = (feasible_count / len(self.pop)) * 100.0

    def track_optimize_step(self, pop=None, epoch=None, runtime=None):
        super().track_optimize_step(pop, epoch, runtime)
        if self.first_feasible_epoch is None:
            g_best_sol = self.g_best.solution
            hcv = self.problem.get_hcv(g_best_sol)
            if hcv == 0:
                self.first_feasible_epoch = epoch
                self.first_feasible_time = time.time() - self.start_wall_time

    def check_termination(self, mode="start", termination=None, epoch=None):
        finished = super().check_termination(mode, termination, epoch)
        if finished:
            return True
        if mode == "end" and epoch is not None:
            hcv = self.problem.get_hcv(self.g_best.solution)
            if hcv == 0:
                z = self.problem.evaluate_solution(self.g_best.solution)['penalizacion_blanda']
                if z < self.best_z:
                    self.best_z = z
                    self.epochs_no_improve_z = 0
                else:
                    self.epochs_no_improve_z += 1
                
                # Detener si Z no ha mejorado en 20 generaciones consecutivas
                if self.epochs_no_improve_z >= 20:
                    self.logger.warning("Stopping criterion with feasible solution found and Z converged (no improvement for 20 epochs) occurred. End program!")
                    return True
        return False

# ============================================================================
# PRE-CÓMPUTO DE REDUCCIÓN DE DOMINIO Y ASIGNACIONES
# ============================================================================
print("[INFO] Pre-computando dominio reducido y combinaciones de inicio...")
start_precompute = time.time()

Valid_SR = set()
Valid_ERT = set()

for s in S:
    salones_elegibles = [
        r for r in R 
        if CAP[r] >= Alumno[s] and all(Req[(s, f)] <= Tiene[(r, f)] for f in F)
    ]
    
    for r in salones_elegibles:
        Valid_SR.add((s, r))
        
        if ES_VIRTUAL[r]:
            franjas_operativas = T_d[d_jue]
        else:
            franjas_operativas = [t for t in T if t not in T_d[d_jue]]
            
        for e in E_s[s]:
            p_assigned = next(prof for prof, eventos_prof in E_p.items() if e in eventos_prof)
            
            for t in franjas_operativas:
                if Disp[(p_assigned, t)] == 1:
                    Valid_ERT.add((e, r, t))

# Filtrado de combinaciones válidas por evento
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
            # Encontrar el día al que pertenece t
            dia_t = None
            for d, slots in T_d.items():
                if t in slots:
                    dia_t = d
                    break
            if dia_t is None:
                continue
            
            # Verificar desbordamiento diario
            if t + Dur[e] - 1 > max(T_d[dia_t]):
                continue
                
            # Verificar disponibilidad del profesor y pertenencia a franjas en la duración
            if all(t + offset in franjas_operativas and Disp.get((p_assigned, t + offset), 0) == 1 for offset in range(Dur[e])):
                starts.append((r, t))
                
    if not starts:
        raise ValueError(f"Infactibilidad critica detectada: El evento {e} no tiene ninguna combinacion de inicio valida.")
    valid_starts[idx_e] = starts

# Pre-cómputo de restricciones R9
r9_constraints = []
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
            
            r9_constraints.append({
                'evs_c': evs_c_idx,
                'num_secciones': num_secciones,
                'evs_other': evs_other_idx,
                'curr_id': k,
                'course_id': c
            })

precompute_time = time.time() - start_precompute
print(f"[INFO] Pre-computo completado en {precompute_time:.2f} segundos.")

# Configurar variables del problema
bounds = IntegerVar(lb=[0]*len(E), ub=[len(valid_starts[idx]) - 1 for idx in range(len(E))])

# ============================================================================
# EJECUCIÓN MULTI-RUN (20 CORRIDAS)
# ============================================================================
n_corridas = args.corridas
resultados_runs = []

best_global_fitness = float('inf')
best_global_solution = None
best_global_hcv = float('inf')
best_global_z = float('inf')

print(f"\n[INFO] Iniciando ejecucion de {n_corridas} corridas del Algoritmo Genetico...")
print("="*80)

for run in range(n_corridas):
    seed = 42 + run
    print(f"\n>>> [CORRIDA {run + 1}/{n_corridas}] Seed: {seed} ...")
    
    # Crear problema
    problem = UCTPProblem(
        E=E, R=R, T=T, D=D, T_d=T_d, P=P, S=S, K=K, E_k=E_k, E_p=E_p, E_s=E_s, Dur=Dur,
        EVENTO_SECCION=EVENTO_SECCION, SECCION_CURSO=SECCION_CURSO, Almuerzo=Almuerzo,
        valid_starts=valid_starts, r9_constraints=r9_constraints, bounds=bounds, ES_VIRTUAL=ES_VIRTUAL
    )
    
    # Crear optimizador GA
    ga_model = CustomGA(
        epoch=config_base['epoch'],
        pop_size=config_base['pop_size'],
        pc=config_base['pc'],
        pm=config_base['pm'],
        crossover=config_base['crossover'],
        selection=config_base['selection']
    )
    
    # Resolver
    termination_dict = {"max_epoch": config_base['epoch']}
    if max_seconds is not None:
        termination_dict["max_time"] = max_seconds
        
    start_run_time = time.time()
    best_agent = ga_model.solve(problem, termination=termination_dict, seed=seed)
    cpu_time = time.time() - start_run_time
    
    # Evaluar mejor solución de esta corrida
    run_solution = best_agent.solution
    run_metrics = problem.evaluate_solution(run_solution)
    
    hcv = run_metrics['violaciones_restricciones_duras']
    z = run_metrics['penalizacion_blanda']
    ttf = ga_model.first_feasible_time
    init_feas = ga_model.init_feasibility_rate
    
    # Trazabilidad y almacenamiento de la mejor solución general
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
        
    print(f"    Resultado Corrida: HCV={hcv} | Z={z} | Factible={'SI' if hcv == 0 else 'NO'} | CPU Time={cpu_time:.2f} s")
    if hcv == 0:
        print(f"    TTF (Factibilidad) : {ttf:.2f} s (Generacion {ga_model.first_feasible_epoch})")
    print(f"    Tasa Factib. Inicial: {init_feas:.2f}% | Evaluaciones de Fitness={problem.fitness_evals}")
    
    resultados_runs.append({
        "corrida": run + 1,
        "seed": seed,
        "Z": z,
        "HCV": hcv,
        "TTF": ttf if hcv == 0 else float('nan'),
        "CPU_time": cpu_time,
        "fitness_evals": problem.fitness_evals,
        "tasa_factib_inicial": init_feas,
        "factible": hcv == 0,
        # Desglose de restricciones duras (HCV)
        "hcv_prof_collision": run_metrics['disponibilidad_y_no_colision_profesor'],
        "hcv_prof_carga": run_metrics['carga_diaria_maxima_profesor'],
        "hcv_salon_estabilidad": run_metrics['estabilidad_salones'],
        "hcv_salon_collision": run_metrics['no_colision_salones_fisicos'],
        "hcv_r9": run_metrics['oferta_curricular_sin_conflicto'],
        # Desglose de restricciones blandas
        "soft_lunch": run_metrics['P_almuerzo'],
        "soft_spacing": run_metrics['P_espaciado']
    })

print("="*80 + "\n")

# ============================================================================
# PERSISTENCIA DE RESULTADOS Y CONSOLIDACIÓN ESTADÍSTICA
# ============================================================================
df_results = pd.DataFrame(resultados_runs)
resultados_dir = "resultados_GA"
os.makedirs(resultados_dir, exist_ok=True)
csv_filepath = os.path.join(resultados_dir, f"resultados_{escala_efectiva}.csv")
df_results.to_csv(csv_filepath, index=False)
print(f"[EXITO] Resultados individuales persistidos en '{csv_filepath}'.")

# Estadísticas consolidadas
total_runs = len(df_results)
factibles_df = df_results[df_results['factible'] == True]
tasa_factibilidad = (len(factibles_df) / total_runs) * 100.0

tasa_factib_inicial_promedio = df_results['tasa_factib_inicial'].mean()

if len(factibles_df) > 0:
    mejor_z = factibles_df['Z'].min()
    promedio_z = factibles_df['Z'].mean()
    desviacion_z = factibles_df['Z'].std() if len(factibles_df) > 1 else 0.0
    ttf_promedio = factibles_df['TTF'].mean()
else:
    mejor_z = float('nan')
    promedio_z = float('nan')
    desviacion_z = float('nan')
    ttf_promedio = float('nan')

cpu_promedio = df_results['CPU_time'].mean()
evals_promedio = df_results['fitness_evals'].mean()

print("="*60)
print(" [RESUMEN ESTADISTICO CONSOLIDADO]")
print("="*60)
print(f" Total de corridas ejecutadas     : {total_runs}")
print(f" Tasa de Factibilidad de Inicial. : {tasa_factib_inicial_promedio:.2f} %")
print(f" Tasa de Factibilidad Final       : {tasa_factibilidad:.2f} %")
print(f" Tiempo hacia Factib. (TTF) Prom. : {ttf_promedio:.2f} segundos" if not np.isnan(ttf_promedio) else " Tiempo hacia Factib. (TTF) Prom. : N/A")
print(f" CPU Time Promedio por Corrida    : {cpu_promedio:.2f} segundos")
print(f" Evaluaciones de Fitness Promedio : {evals_promedio:.1f}")
print("-"*60)
print(f" Mejor Valor Funcion Objetivo (Z) : {mejor_z}" if not np.isnan(mejor_z) else " Mejor Valor Funcion Objetivo (Z) : N/A")
print(f" Valor Promedio Objetivo (Z)      : {promedio_z:.2f}" if not np.isnan(promedio_z) else " Valor Promedio Objetivo (Z)      : N/A")
print(f" Desviacion Estandar Objetivo (Z) : {desviacion_z:.4f}" if not np.isnan(desviacion_z) else " Desviacion Estandar Objetivo (Z) : N/A")
print("="*60 + "\n")

# ============================================================================
# EXPORTACIÓN DEL HORARIO DE LA MEJOR CORRIDA
# ============================================================================
if best_global_solution is not None:
    print("[INFO] Reconstruyendo y exportando horario de la mejor solucion encontrada...")
    x_best = reconstruir_x_desde_ga(best_global_solution, valid_starts, E, Dur)
    
    # Imprimir métricas detalladas en consola
    imprimir_metricas_ga(
        cpu_time=df_results['CPU_time'].sum(), # tiempo acumulado de procesamiento
        best_fitness=best_global_fitness,
        hard_violations=best_global_hcv,
        soft_penalty=best_global_z,
        epoch=config_base['epoch'],
        pop_size=config_base['pop_size'],
        crossover=config_base['crossover'],
        selection=config_base['selection']
    )
    
    # Calcular y mostrar el desglose detallado de la mejor solución
    best_metrics = problem.evaluate_solution(best_global_solution)
    print(" [DETALLE DE RESTRICCIONES BLANDAS DE LA MEJOR CORRIDA]")
    print(" " + "-"*50)
    print(f"   - Almuerzo (franjas de clase) : {best_metrics['P_almuerzo']}")
    print(f"   - Espaciado (infracciones)     : {best_metrics['P_espaciado']}")
    print(" " + "-"*50 + "\n")
    
    # Exportar horario en formato CSV desagregado
    out_path = f"horarios_{escala_efectiva}/GA"
    exportar_horarios(
        x=x_best,
        K=K,
        E_k=E_k,
        T_d=T_d,
        D=D,
        EVENTO_SECCION=EVENTO_SECCION,
        SECCION_CURSO=SECCION_CURSO,
        E_p=E_p,
        output_dir=out_path
    )
else:
    print("[ALERTA] No se encontro ninguna solucion factible o valida para exportar.")
