from mip import Model, BINARY, INTEGER, xsum, minimize
import csv
import json
import pandas as pd
import time
import platform
import psutil
import mip

# ============================================================================
# FUNCIONES DE CARGA DE DATOS
# ============================================================================

def load_config(filepath):
    """
    Carga parametros institucionales desde JSON y deriva D, T, T_d, d_jue, Almuerzo.
    Soporta franjas heterogeneas: cada dia puede tener distinto numero de franjas.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    D = cfg['dias']
    d_jue = cfg['dia_cierre']
    pos_almuerzo = cfg['posicion_almuerzo']
    dias_sin_almuerzo = set(cfg.get('dias_sin_almuerzo', []))

    # franjas_por_dia puede ser un dict {dia: n} o un int uniforme
    fpd_raw = cfg['franjas_por_dia']
    if isinstance(fpd_raw, dict):
        fpd = fpd_raw          # {dia: num_franjas}
    else:
        fpd = {dia: fpd_raw for dia in D}   # retrocompatibilidad

    # Construir T_d acumulando franjas dia a dia
    T_d = {}
    cursor = 1
    for dia in D:
        n = fpd[dia]
        T_d[dia] = list(range(cursor, cursor + n))
        cursor += n

    # Conjunto global de franjas
    T = list(range(1, cursor))

    # Almuerzo: franja numero pos_almuerzo dentro de cada dia (1-indexed)
    almuerzo_set = set()
    for dia in D:
        if dia in dias_sin_almuerzo:
            continue
        slots = T_d[dia]
        if pos_almuerzo <= len(slots):
            almuerzo_set.add(slots[pos_almuerzo - 1])
    Almuerzo = {t: (1 if t in almuerzo_set else 0) for t in T}

    return D, T, T_d, d_jue, Almuerzo


def load_rooms_data(filepath):
    """Carga salones desde CSV. Retorna R, CAP, ES_VIRTUAL, CARACTERISTICAS."""
    R = []
    CAP = {}
    ES_VIRTUAL = {}
    CARACTERISTICAS = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            r = row['id_salon'].strip()
            R.append(r)
            CAP[r] = int(row['capacidad'])
            ES_VIRTUAL[r] = row['es_virtual'].strip().lower() == 'true'
            CARACTERISTICAS[r] = [c.strip() for c in row['caracteristicas'].split(',')] if row['caracteristicas'].strip() else []
    return R, CAP, ES_VIRTUAL, CARACTERISTICAS


def load_cursos(filepath):
    """Carga cursos y sus requisitos de infraestructura."""
    CURSOS = []
    REQ_CURSO = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            id_curso = row['id_curso'].strip()
            CURSOS.append(id_curso)
            reqs = row['requisitos'].strip()
            REQ_CURSO[id_curso] = [r.strip() for r in reqs.split(',')] if reqs else []
    return CURSOS, REQ_CURSO


def load_secciones(filepath):
    """Carga secciones. Retorna S, mapeo seccion->curso, y Alumno."""
    S = []
    SECCION_CURSO = {}
    Alumno = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            s = row['id_seccion'].strip()
            S.append(s)
            SECCION_CURSO[s] = row['id_curso'].strip()
            Alumno[s] = int(row['num_alumnos'])
    return S, SECCION_CURSO, Alumno


def load_eventos(filepath):
    """Carga eventos. Retorna E, E_s, E_p, Dur y mapeo evento->seccion."""
    E = []
    E_s = {}
    E_p = {}
    Dur = {}
    EVENTO_SECCION = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            e = int(row['id_evento'])
            s = row['id_seccion'].strip()
            p = row['id_profesor'].strip()
            d = int(row['duracion'])

            E.append(e)
            Dur[e] = d
            EVENTO_SECCION[e] = s

            # Agrupar eventos por seccion
            if s not in E_s:
                E_s[s] = []
            E_s[s].append(e)

            # Agrupar eventos por profesor
            if p not in E_p:
                E_p[p] = []
            E_p[p].append(e)

    return E, E_s, E_p, Dur, EVENTO_SECCION


def load_curriculos(curriculos_path, bridge_path):
    """Carga curriculos y tabla puente. Retorna K y E_k."""
    K = []
    with open(curriculos_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            K.append(row['id_curriculo'].strip())

    E_k = {k: [] for k in K}
    with open(bridge_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            k = row['id_curriculo'].strip()
            e = int(row['id_evento'])
            if k in E_k:
                E_k[k].append(e)

    return K, E_k


def load_prof_availability(filepath, P, T):
    """Carga disponibilidad de profesores. Retorna Disp[p,t]."""
    Disp = {(p, t): 0 for p in P for t in T}
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            p = row['id_profesor'].strip()
            if p in P:
                f_inicio = int(row['franja_inicio'])
                f_fin = int(row['franja_fin'])
                for t in range(f_inicio, f_fin + 1):
                    if t in T:
                        Disp[(p, t)] = 1
    return Disp


# ============================================================================
# CARGA DE CONJUNTOS Y PARAMETROS DESDE ARCHIVOS
# ============================================================================

# Configuracion institucional
D, T, T_d, d_jue, Almuerzo = load_config('dataset/config.json')

# Salones
R, CAP, ES_VIRTUAL, CARACTERISTICAS = load_rooms_data('dataset/salones.csv')

# Cursos y sus requisitos
CURSOS, REQ_CURSO = load_cursos('dataset/cursos.csv')

# Secciones
S, SECCION_CURSO, Alumno = load_secciones('dataset/secciones.csv')

# Eventos (de aqui se derivan E, E_s, E_p, Dur)
E, E_s, E_p, Dur, EVENTO_SECCION = load_eventos('dataset/eventos.csv')

# Profesores (se deducen de los eventos)
P = list(E_p.keys())

# Curriculos y tabla puente
K, E_k = load_curriculos('dataset/curriculos.csv', 'dataset/curriculo_evento.csv')

# Disponibilidad de profesores
Disp = load_prof_availability('dataset/profesores_disponibilidad.csv', P, T)

# Conjunto de caracteristicas (union de cursos y salones)
F = sorted(
    set(f for carac in CARACTERISTICAS.values() for f in carac if f)
    | set(f for reqs in REQ_CURSO.values() for f in reqs if f)
)

# Parametro Tiene[r,f]: 1 si el salon r posee la caracteristica f
Tiene = {(r, f): 1 if f in CARACTERISTICAS[r] else 0 for r in R for f in F}

# Parametro Req[s,f]: heredado del curso al que pertenece la seccion
Req = {(s, f): 1 if f in REQ_CURSO[SECCION_CURSO[s]] else 0 for s in S for f in F}

# Agrupacion de eventos por seccion (para restriccion de espaciado)
Cursos_Agrupados = list(E_s.values())


# ============================================================================
# INSTANCIACION DEL MODELO
# ============================================================================

model = Model(name="UCTP_Universidad", solver_name="HiGHS")

# ============================================================================
# FILTRADO TOPOLOGICO (REDUCCION DE DOMINIO)
# ============================================================================

Valid_SR = set()   # Tuplas validas (s, r) para la variable w
Valid_ERT = set()  # Tuplas validas (e, r, t) para las variables x e y

for s in S:
    # 1. Aplicar R_s: Filtrar salones por aforo e infraestructura
    salones_elegibles = [
        r for r in R 
        if CAP[r] >= Alumno[s] and all(Req[(s, f)] <= Tiene[(r, f)] for f in F)
    ]
    
    for r in salones_elegibles:
        Valid_SR.add((s, r))
        
        # 2. Aplicar T_r: Filtrar franjas habilitadas operativamente
        if ES_VIRTUAL[r]:
            franjas_operativas = T_d[d_jue]
        else:
            franjas_operativas = [t for t in T if t not in T_d[d_jue]]
            
        for e in E_s[s]:
            for t in franjas_operativas:
                Valid_ERT.add((e, r, t))

# ============================================================================
# VARIABLES DE DECISION (INSTANCIACION DISPERSA)
# ============================================================================

x = {
    (e, r, t): model.add_var(name=f"x_{e}_{r}_{t}", var_type=BINARY)
    for (e, r, t) in Valid_ERT
}

y = {
    (e, r, t): model.add_var(name=f"y_{e}_{r}_{t}", var_type=BINARY)
    for (e, r, t) in Valid_ERT
}

w = {
    (s, r): model.add_var(name=f"w_{s}_{r}", var_type=BINARY)
    for (s, r) in Valid_SR
}

# P_almuerzo: penalizacion por clases en horario de almuerzo
P_almuerzo = model.add_var(name="P_almuerzo", var_type=INTEGER, lb=0)

print("[INFO] Inicializacion completa: conjuntos, parametros y variables.")
print(f"       E={len(E)} eventos | R={len(R)} salones | T={len(T)} franjas | P={len(P)} profesores")


# ============================================================================
# 1. Disponibilidad y no colision del profesor
# ============================================================================
for p in P:
    for t in T:
        # Acumular asignaciones unicamente para tuplas (e, r, t) instanciadas en el dominio
        suma_clases_profesor = xsum(x[e, r, t] for e in E_p[p] for r in R if (e, r, t) in x)
        model += suma_clases_profesor <= Disp[p, t], f"DispProf_{p}_franja_{t}"

# ============================================================================
# 2. No colision de estudiantes por curriculo
# ============================================================================
for k in K:
    for t in T:
        suma_clases_curriculo = xsum(x[e, r, t] for e in E_k[k] for r in R if (e, r, t) in x)
        model += suma_clases_curriculo <= 1, f"NoColis_Curriculo_{k}_franja_{t}"

# ============================================================================
# 3. Cobertura total de eventos
# ============================================================================
for e in E:
    suma_asignaciones = xsum(x[e, r, t] for r in R for t in T if (e, r, t) in x)
    model += suma_asignaciones == Dur[e], f"Cobertura_Evento_{e}"

# ============================================================================
# 4. Estabilidad de salones
# ============================================================================
for s in S:
    for r in R:
        # Ignorar pares seccion-salon que fueron descartados por aforo o infraestructura
        if (s, r) not in w:
            continue
            
        for e in E_s[s]:
            suma_temporal = xsum(x[e, r, t] for t in T if (e, r, t) in x)
            model += suma_temporal <= Dur[e] * w[s, r], f"Vincular_w_{s}_{e}_{r}"

for s in S:
    model += xsum(w[s, r] for r in R if (s, r) in w) <= 2, f"Max_Salones_{s}"

# ============================================================================
# 5. No colision de salones fisicos
# ============================================================================
for r in R:
    if not ES_VIRTUAL[r]:
        for t in T:
            suma_eventos_salon = xsum(x[e, r, t] for e in E if (e, r, t) in x)
            model += suma_eventos_salon <= 1, f"NoColis_SalonFisico_{r}_franja_{t}"

# ============================================================================
# 6. Continuidad y no fragmentacion
# ============================================================================
for e in E:
    model += xsum(y[e, r, t] for r in R for t in T if (e, r, t) in y) == 1, f"UnicoInicio_Evento_{e}"

for d in D:
    for t in T_d[d]:
        for e in E:
            arranques_validos = [tau for tau in T_d[d] if (t - Dur[e] + 1) <= tau <= t]
            for r in R:
                if (e, r, t) in x:
                    # Vincular el estado de una franja con los instantes de inicio factibles
                    suma_arranques = xsum(y[e, r, tau] for tau in arranques_validos if (e, r, tau) in y)
                    model += x[e, r, t] == suma_arranques, f"Continua_d{d}_t{t}_e{e}_r{r}"

# ============================================================================
# 7. Espaciado de sesiones
# ============================================================================
for c in Cursos_Agrupados:
    for i in range(len(D) - 1):
        dia_actual = D[i]
        dia_siguiente = D[i+1]

        arranques_hoy = xsum(y[e, r, t] for e in c for r in R for t in T_d[dia_actual] if (e, r, t) in y)
        arranques_manana = xsum(y[e, r, t] for e in c for r in R for t in T_d[dia_siguiente] if (e, r, t) in y)

        model += arranques_hoy + arranques_manana <= 1, f"Espaciado_Curso_{c[0]}_Dia_{i}"

# ============================================================================
# 8. Control de desbordamiento diario
# ============================================================================
for d in D:
    ultima_franja = max(T_d[d])
    for e in E:
        limite_inicio = ultima_franja - Dur[e] + 1
        for t in T_d[d]:
            if t > limite_inicio:
                for r in R:
                    # Bloquear instantes de inicio que provocarian que el evento sobrepase el final del dia
                    if (e, r, t) in y:
                        model += y[e, r, t] == 0, f"Desborde_d{d}_e{e}_r{r}_t{t}"

# ============================================================================
# RESTRICCIONES BLANDAS Y FUNCION OBJETIVO
# ============================================================================
model += P_almuerzo == xsum(
    x[e, r, t]
    for (e, r, t) in x.keys()
    if Almuerzo[t] == 1
), "Calculo_Penalizacion_Almuerzo"

model.objective = minimize(P_almuerzo)

if __name__ == '__main__':
    model.write("UCTP_Universidad.lp")
    print("[INFO] Archivo LP generado exitosamente.")

    model.verbose = 2

    print("[INFO] Iniciando el proceso de optimizacion (maximo 2 horas)...")
    
    # Registrar la estampa de tiempo inicial para calcular la duracion total del proceso
    start_time = time.time()
    status = model.optimize(max_seconds=7200)
    cpu_time = time.time() - start_time

    # Comprobar la existencia de soluciones factibles antes de acceder a los valores objetivos
    if model.num_solutions > 0:
        
        # Recuperar los valores optimos y limites inferiores alcanzados por el solver
        bestcost = model.objective_value
        lowerbound = model.objective_bound
        epsilon = 1e-10
        
        # Calcular la brecha de optimalidad garantizando la estabilidad numerica (evita div por 0)
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

        # Deducir los intervalos horarios basandose en el dia con la mayor cantidad de franjas
        max_slots = max(len(slots) for slots in T_d.values())
        horas_labels = [f"{7+i}:00 - {8+i}:00" for i in range(max_slots)]
        
        # Estructurar una cuadricula tabular para representar el horario de forma legible
        schedule_matrix = pd.DataFrame("---", index=horas_labels, columns=D)

        # Iterar el diccionario de variables instanciadas buscando aquellas activas en la solucion
        for (e, r, t), var in x.items():
            if var.x >= 0.99:
                dia_actual = next(d for d, slots in T_d.items() if t in slots)
                slot_local = T_d[dia_actual].index(t)
                
                seccion = EVENTO_SECCION[e]
                curso = SECCION_CURSO[seccion]
                
                # Proyectar el evento en la matriz cruzando el indice horario con la columna del dia
                schedule_matrix.at[horas_labels[slot_local], dia_actual] = f"{curso} ({seccion}) [{r}]"

        schedule_matrix.to_csv("horario.csv")
        print("[INFO] Matriz exportada a 'horario.csv'.")
    else:
        print(f"\n[ALERTA] No se encontro ninguna solucion factible. Estado final: {status.name if hasattr(status, 'name') else status}")
        print(f"[INFO] Tiempo de Procesamiento invertido: {cpu_time:.2f} segundos")