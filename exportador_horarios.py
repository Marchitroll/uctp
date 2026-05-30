"""
exportador_horarios.py
Módulo encargado exclusivamente de la exportación de los resultados de la optimización.
Genera archivos CSV desagregados por currículo y por camino de matrícula, evitando
la sobreescritura que ocurre al proyectar todos los eventos en una única matriz plana.
"""

import os
import itertools
import pandas as pd
import platform
import psutil
import mip


def imprimir_metricas(status, cpu_time, model):
    """
    Imprime las métricas de trazabilidad del entorno de ejecución y los indicadores
    de desempeño alcanzados por el resolutor durante el proceso de optimización.
    """
    bestcost = model.objective_value
    lowerbound = model.objective_bound
    epsilon = 1e-10

    # Calcula la brecha de optimalidad (MIP Gap) previniendo posibles divisiones por cero
    gap_pct = ((bestcost - lowerbound) / (abs(bestcost) + epsilon)) * 100

    print("\n" + "="*60)
    print(" [TRAZABILIDAD DEL ENTORNO]")
    print("="*60)
    print(f" Sistema Operativo : {platform.system()} {platform.release()}")
    print(f" Procesador        : {platform.processor()}")
    print(f" RAM Disponible    : {round(psutil.virtual_memory().total / (1024.0 **3), 2)} GB")
    print(f" Version Python    : {platform.python_version()}")
    print(f" Version Python-MIP: {mip.__version__}")

    print("\n" + "="*60)
    print(" [METRICAS DE EVALUACION]")
    print("="*60)
    print(f" Estado Final (Status) : {status.name if hasattr(status, 'name') else status}")
    print(f" Tiempo de Procesamiento : {cpu_time:.2f} segundos")
    print(f" Valor Funcion Objetivo (Z) : {bestcost}")
    print(f" Limite Inferior (LB) : {lowerbound}")
    print(f" Gap de Optimalidad (MIP) : {gap_pct:.4f} %")
    print("="*60 + "\n")


def exportar_horarios(x, K, E_k, T_d, D, EVENTO_SECCION, SECCION_CURSO, E_p=None, output_dir=None):
    """
    Genera archivos CSV de horario desagregados por currículo y por camino de matrícula.
    Para cada currículo, se construyen todas las combinaciones factibles de secciones
    (una por curso) y se proyecta cada combinación en su propia matriz bidimensional.

    Parámetros:
        x               : Diccionario de variables de decisión {(e, r, t): var}.
        K               : Lista de identificadores de currículos.
        E_k             : Diccionario {k: [eventos]} que asocia cada currículo con sus eventos.
        T_d             : Diccionario {dia: [franjas]} que asocia cada día con sus franjas horarias.
        D               : Lista ordenada de días de la semana académica.
        EVENTO_SECCION  : Diccionario {evento: sección} para resolver la sección de cada evento.
        SECCION_CURSO   : Diccionario {sección: curso} para resolver el curso de cada sección.
        E_p             : Diccionario {profesor: [eventos]} que asocia cada profesor con sus eventos.
        output_dir      : Directorio raíz para almacenar los archivos CSV generados (detectado dinámicamente si es None).
    """
    if output_dir is None or output_dir == "horarios_por_camino":
        if len(K) == 1:
            output_dir = "horarios_pequena"
        elif len(K) in [4, 5]:
            output_dir = "horarios_mediana"
        else:
            output_dir = "horarios_grande"

    os.makedirs(output_dir, exist_ok=True)

    # Determina las etiquetas de los intervalos horarios basándose en el día con mayor cantidad de franjas
    max_slots = max(len(slots) for slots in T_d.values())
    horas_labels = [f"{7+i}:00 - {8+i}:00" for i in range(max_slots)]

    # Mapeo de evento a profesor e inicialización del horario docente
    evento_profesor = {}
    mapeo_profesor_horario = {}
    if E_p is not None:
        for prof, evs in E_p.items():
            for ev in evs:
                evento_profesor[ev] = prof
                
        # Recolectar asignaciones activas para generar horarios de profesores
        for (e, r, t), var in x.items():
            if var.x >= 0.99:
                profesor = evento_profesor.get(e, None)
                if profesor:
                    seccion = EVENTO_SECCION[e]
                    curso = SECCION_CURSO[seccion]
                    dia_actual = next(d for d, slots in T_d.items() if t in slots)
                    slot_local = T_d[dia_actual].index(t)
                    
                    if profesor not in mapeo_profesor_horario:
                        mapeo_profesor_horario[profesor] = []
                    mapeo_profesor_horario[profesor].append({
                        'dia': dia_actual,
                        'slot': slot_local,
                        'info': f"{curso} ({seccion}) [{r}]"
                    })

    for k in K:
        # Identifica las secciones y eventos del currículo que fueron activados por el resolutor
        secciones_activas_por_curso = {}
        mapeo_eventos_seccion = {}

        for (e, r, t), var in x.items():
            if var.x >= 0.99 and e in E_k[k]:
                seccion = EVENTO_SECCION[e]
                curso = SECCION_CURSO[seccion]

                dia_actual = next(d for d, slots in T_d.items() if t in slots)
                slot_local = T_d[dia_actual].index(t)

                if curso not in secciones_activas_por_curso:
                    secciones_activas_por_curso[curso] = set()
                secciones_activas_por_curso[curso].add(seccion)

                if seccion not in mapeo_eventos_seccion:
                    mapeo_eventos_seccion[seccion] = []

                profesor = evento_profesor.get(e, "") if E_p is not None else ""
                prof_suffix = f" - {profesor}" if profesor else ""

                # Almacena la coordenada física de la clase asignada por el resolutor
                mapeo_eventos_seccion[seccion].append({
                    'dia': dia_actual,
                    'slot': slot_local,
                    'info': f"{curso} ({seccion}){prof_suffix} [{r}]"
                })

        if not secciones_activas_por_curso:
            continue

        # Construye los caminos mediante el producto cartesiano de las secciones por curso
        lista_cursos = list(secciones_activas_por_curso.keys())
        bloques_secciones = [list(secciones_activas_por_curso[c]) for c in lista_cursos]

        # Genera todas las combinaciones posibles tomando exactamente una sección de cada curso
        caminos_matricula = list(itertools.product(*bloques_secciones))

        # Crea la subcarpeta correspondiente al ciclo académico
        ciclo_dir = os.path.join(output_dir, f"ciclo_{k}")
        os.makedirs(ciclo_dir, exist_ok=True)

        # Proyecta cada camino independiente en su propia matriz bidimensional
        for idx, camino in enumerate(caminos_matricula, start=1):
            schedule_matrix = pd.DataFrame("---", index=horas_labels, columns=D)

            for seccion in camino:
                for clase in mapeo_eventos_seccion[seccion]:
                    dia = clase['dia']
                    slot = clase['slot']
                    info_str = clase['info']

                    celda_actual = schedule_matrix.at[horas_labels[slot], dia]
                    if celda_actual == "---":
                        schedule_matrix.at[horas_labels[slot], dia] = info_str
                    else:
                        # Concatena eventos si coinciden en la misma celda horaria
                        schedule_matrix.at[horas_labels[slot], dia] = f"{celda_actual} | {info_str}"

            file_path = os.path.join(ciclo_dir, f"camino_{idx}.csv")
            schedule_matrix.to_csv(file_path)

        print(f"[INFO] Ciclo {k}: Generados {len(caminos_matricula)} caminos independientes en '{ciclo_dir.replace(os.sep, '/')}/'.")

    # Exportación de los horarios individuales de cada profesor
    if E_p is not None and mapeo_profesor_horario:
        prof_dir = os.path.join(output_dir, "profesores")
        os.makedirs(prof_dir, exist_ok=True)
        for prof, clases in mapeo_profesor_horario.items():
            prof_matrix = pd.DataFrame("---", index=horas_labels, columns=D)
            for clase in clases:
                dia = clase['dia']
                slot = clase['slot']
                info_str = clase['info']

                celda_actual = prof_matrix.at[horas_labels[slot], dia]
                if celda_actual == "---":
                    prof_matrix.at[horas_labels[slot], dia] = info_str
                else:
                    prof_matrix.at[horas_labels[slot], dia] = f"{celda_actual} | {info_str}"

            prof_file_path = os.path.join(prof_dir, f"{prof}.csv")
            prof_matrix.to_csv(prof_file_path)
        print(f"[INFO] Exportados {len(mapeo_profesor_horario)} horarios de profesores en '{prof_dir.replace(os.sep, '/')}/'.")

    print(f"\n[EXITO] Exportacion desagregada completada. Revisar el directorio '{output_dir.replace(os.sep, '/')}/'.")


def imprimir_metricas_ga(cpu_time, best_fitness, hard_violations, soft_penalty, epoch, pop_size, crossover, selection):
    """
    Imprime las métricas de trazabilidad del entorno de ejecución y los indicadores
    de desempeño alcanzados por el Algoritmo Genético (GA) durante el proceso de optimización.
    """
    print("\n" + "="*60)
    print(" [TRAZABILIDAD DEL ENTORNO]")
    print("="*60)
    print(f" Sistema Operativo : {platform.system()} {platform.release()}")
    print(f" Procesador        : {platform.processor()}")
    print(f" RAM Disponible    : {round(psutil.virtual_memory().total / (1024.0 **3), 2)} GB")
    print(f" Version Python    : {platform.python_version()}")
    print(f" Version MEALPY    : 3.0.3")

    print("\n" + "="*60)
    print(" [METRICAS GA]")
    print("="*60)
    print(f" Generaciones (Epochs)   : {epoch}")
    print(f" Tam. Poblacion (Pop)    : {pop_size}")
    print(f" Crossover / Seleccion   : {crossover} / {selection}")
    print(f" Tiempo Procesamiento    : {cpu_time:.2f} segundos")
    print(f" Fitness Total Obtenido  : {best_fitness:.4f}")
    print(f" Violaciones Duras (HCV) : {hard_violations}")
    print(f" Penalizacion Almuerzo(Z): {soft_penalty} (comparable con Z del MIP)")
    print(f" Factible (HCV == 0)     : {'SI' if hard_violations == 0 else 'NO'}")
    print("="*60 + "\n")


class DummyVar:
    def __init__(self, value):
        self.x = value


def reconstruir_x_desde_ga(solution, valid_starts, E, Dur):
    """
    Convierte la solución del Algoritmo Genético (donde cada gen es el índice en valid_starts[idx])
    en un diccionario x compatible con exportar_horarios.
    """
    x_ga = {}
    for idx, e in enumerate(E):
        r, t_start = valid_starts[idx][int(solution[idx])]
        for offset in range(Dur[e]):
            x_ga[(e, r, t_start + offset)] = DummyVar(1.0)
    return x_ga

