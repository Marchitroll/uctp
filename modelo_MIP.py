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
    Carga los parámetros institucionales desde un archivo JSON y deriva los conjuntos D, T, T_d, d_jue y Almuerzo.
    Soporta franjas heterogéneas, donde cada día puede tener un número diferente de franjas.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    D = cfg['dias']
    d_jue = cfg['dia_cierre']
    pos_almuerzo = cfg['posicion_almuerzo']
    dias_sin_almuerzo = set(cfg.get('dias_sin_almuerzo', []))

    # El parámetro franjas_por_dia puede ser un diccionario {dia: n} o un entero uniforme
    fpd_raw = cfg['franjas_por_dia']
    if isinstance(fpd_raw, dict):
        fpd = fpd_raw          # Asocia a cada día su respectivo número de franjas
    else:
        fpd = {dia: fpd_raw for dia in D}   # Mantiene la compatibilidad con versiones anteriores

    # Construye el conjunto T_d acumulando las franjas de cada día secuencialmente
    T_d = {}
    cursor = 1
    for dia in D:
        n = fpd[dia]
        T_d[dia] = list(range(cursor, cursor + n))
        cursor += n

    # Representa el conjunto global de todas las franjas horarias
    T = list(range(1, cursor))

    # Define el horario de almuerzo según la posición pos_almuerzo dentro de cada día (índice base 1)
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
    """
    Carga los datos de los salones desde un archivo CSV y retorna R, CAP, ES_VIRTUAL y CARACTERISTICAS.
    """
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
    """
    Carga los datos de los cursos y sus requisitos de infraestructura asociados.
    """
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
    """
    Carga las secciones académicas y retorna S, el mapeo seccion->curso y el número de alumnos por sección.
    """
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
    """
    Carga los eventos de clase y retorna E, E_s, E_p, Dur y el mapeo evento->seccion.
    """
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

            # Agrupa los eventos correspondientes a cada sección
            if s not in E_s:
                E_s[s] = []
            E_s[s].append(e)

            # Agrupa los eventos correspondientes a cada profesor
            if p not in E_p:
                E_p[p] = []
            E_p[p].append(e)

    return E, E_s, E_p, Dur, EVENTO_SECCION


def load_curriculos(curriculos_path, bridge_path):
    """
    Carga los currículos académicos y la tabla puente, y retorna K y E_k.
    """
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
    """
    Carga la disponibilidad horaria de los profesores y retorna la matriz binaria Disp.
    """
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
# CARGA DE CONJUNTOS Y PARÁMETROS DESDE ARCHIVOS
# ============================================================================

# Carga la configuración institucional general
D, T, T_d, d_jue, Almuerzo = load_config('dataset/config.json')

# Carga la información de los salones disponibles
R, CAP, ES_VIRTUAL, CARACTERISTICAS = load_rooms_data('dataset/salones.csv')

# Carga la información de los cursos y sus requisitos de infraestructura
CURSOS, REQ_CURSO = load_cursos('dataset/cursos.csv')

# Carga las secciones académicas registradas
S, SECCION_CURSO, Alumno = load_secciones('dataset/secciones.csv')

# Carga los eventos de clase (de los cuales se derivan los conjuntos E, E_s, E_p y las duraciones Dur)
E, E_s, E_p, Dur, EVENTO_SECCION = load_eventos('dataset/eventos.csv')

# Obtiene el conjunto de profesores activos a partir de los eventos cargados
P = list(E_p.keys())

# Carga la estructura de currículos académicos y su relación con los eventos
K, E_k = load_curriculos('dataset/curriculos.csv', 'dataset/curriculo_evento.csv')

# Carga la disponibilidad horaria específica de cada profesor
Disp = load_prof_availability('dataset/profesores_disponibilidad.csv', P, T)

# Define el conjunto general de características requeridas o poseídas (unión de cursos y salones)
F = sorted(
    set(f for carac in CARACTERISTICAS.values() for f in carac if f)
    | set(f for reqs in REQ_CURSO.values() for f in reqs if f)
)

# Define el parámetro binario Tiene[r,f], que indica si el salón r cuenta con la característica f
Tiene = {(r, f): 1 if f in CARACTERISTICAS[r] else 0 for r in R for f in F}

# Define el parámetro binario Req[s,f], el cual se hereda del curso asignado a la sección
Req = {(s, f): 1 if f in REQ_CURSO[SECCION_CURSO[s]] else 0 for s in S for f in F}

# Agrupa los eventos por sección para su posterior uso en las restricciones de espaciado
Cursos_Agrupados = list(E_s.values())


# ============================================================================
# INSTANCIACIÓN DEL MODELO
# ============================================================================

model = Model(name="UCTP_Universidad", solver_name="HiGHS")

# ============================================================================
# FILTRADO TOPOLÓGICO (REDUCCIÓN DE DOMINIO)
# ============================================================================

Valid_SR = set()   # Define el conjunto de tuplas válidas (s, r) asignables a la variable w
Valid_ERT = set()  # Define el conjunto de tuplas válidas (e, r, t) asignables a las variables x e y

for s in S:
    # Aplica la regla R_s para filtrar salones en función de la capacidad y los requerimientos de infraestructura
    salones_elegibles = [
        r for r in R 
        if CAP[r] >= Alumno[s] and all(Req[(s, f)] <= Tiene[(r, f)] for f in F)
    ]
    
    for r in salones_elegibles:
        Valid_SR.add((s, r))
        
        # Aplica la regla T_r para determinar las franjas horarias operativas según la naturaleza del salón
        if ES_VIRTUAL[r]:
            franjas_operativas = T_d[d_jue]
        else:
            franjas_operativas = [t for t in T if t not in T_d[d_jue]]
            
        for e in E_s[s]:
            # Determina el profesor que tiene asignado el evento bajo análisis
            p_asignado = next(prof for prof, eventos_prof in E_p.items() if e in eventos_prof)
            
            for t in franjas_operativas:
                # Aplica la reducción maestro-profesor: restringe la instanciación únicamente a las franjas de disponibilidad del docente
                if Disp[(p_asignado, t)] == 1:
                    Valid_ERT.add((e, r, t))

# ============================================================================
# VARIABLES DE DECISIÓN (INSTANCIACIÓN DISPERSA)
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

# Define la variable P_almuerzo para la penalización por programación de clases en horario de almuerzo
P_almuerzo = model.add_var(name="P_almuerzo", var_type=INTEGER, lb=0)

print("[INFO] Inicializacion completa: conjuntos, parametros y variables.")
print(f"       E={len(E)} eventos | R={len(R)} salones | T={len(T)} franjas | P={len(P)} profesores")


# ============================================================================
# 1. DISPONIBILIDAD Y NO COLISIÓN DEL PROFESOR
# ============================================================================
for p in P:
    for t in T:
        # Acumula las asignaciones exclusivamente para las combinaciones del dominio factible
        suma_clases_profesor = xsum(x[e, r, t] for e in E_p[p] for r in R if (e, r, t) in x)
        model += suma_clases_profesor <= Disp[p, t], f"DispProf_{p}_franja_{t}"

# ============================================================================
# 2. CARGA DIARIA MÁXIMA DEL PROFESOR (MÁXIMO 8 HORAS DE CLASE POR DÍA)
# ============================================================================
MAX_HORAS_DIARIAS = 8
for p in P:
    for d in D:
        # Suma el total de franjas asignadas al profesor p durante el transcurso del día d
        suma_clases_diarias = xsum(
            x[e, r, t] 
            for e in E_p[p] 
            for r in R 
            for t in T_d[d] 
            if (e, r, t) in x
        )
        model += suma_clases_diarias <= MAX_HORAS_DIARIAS, f"MaxHorasDiarias_{p}_{d}"

# ============================================================================
# 3. COBERTURA TOTAL DE EVENTOS
# ============================================================================
for e in E:
    suma_asignaciones = xsum(x[e, r, t] for r in R for t in T if (e, r, t) in x)
    model += suma_asignaciones == Dur[e], f"Cobertura_Evento_{e}"

# ============================================================================
# 4. ESTABILIDAD DE SALONES
# ============================================================================
for s in S:
    for r in R:
        # Omite la evaluación de aquellos pares sección-salón que fueron descartados en la etapa de prefiltrado
        if (s, r) not in w:
            continue
            
        for e in E_s[s]:
            suma_temporal = xsum(x[e, r, t] for t in T if (e, r, t) in x)
            model += suma_temporal <= Dur[e] * w[s, r], f"Vincular_w_{s}_{e}_{r}"

for s in S:
    model += xsum(w[s, r] for r in R if (s, r) in w) <= 2, f"Max_Salones_{s}"

# ============================================================================
# 5. NO COLISIÓN DE SALONES FÍSICOS
# ============================================================================
for r in R:
    if not ES_VIRTUAL[r]:
        for t in T:
            suma_eventos_salon = xsum(x[e, r, t] for e in E if (e, r, t) in x)
            model += suma_eventos_salon <= 1, f"NoColis_SalonFisico_{r}_franja_{t}"

# ============================================================================
# 6. CONTINUIDAD Y NO FRAGMENTACIÓN
# ============================================================================
for e in E:
    model += xsum(y[e, r, t] for r in R for t in T if (e, r, t) in y) == 1, f"UnicoInicio_Evento_{e}"

for d in D:
    for t in T_d[d]:
        for e in E:
            arranques_validos = [tau for tau in T_d[d] if (t - Dur[e] + 1) <= tau <= t]
            for r in R:
                if (e, r, t) in x:
                    # Establece el vínculo entre el estado de ocupación de una franja y sus respectivos instantes de inicio factibles
                    suma_arranques = xsum(y[e, r, tau] for tau in arranques_validos if (e, r, tau) in y)
                    model += x[e, r, t] == suma_arranques, f"Continua_d{d}_t{t}_e{e}_r{r}"

# ============================================================================
# 7. ESPACIADO DE SESIONES
# ============================================================================
for c in Cursos_Agrupados:
    for i in range(len(D) - 1):
        dia_actual = D[i]
        dia_siguiente = D[i+1]

        arranques_hoy = xsum(y[e, r, t] for e in c for r in R for t in T_d[dia_actual] if (e, r, t) in y)
        arranques_manana = xsum(y[e, r, t] for e in c for r in R for t in T_d[dia_siguiente] if (e, r, t) in y)

        model += arranques_hoy + arranques_manana <= 1, f"Espaciado_Curso_{c[0]}_Dia_{i}"

# ============================================================================
# 8. CONTROL DE DESBORDAMIENTO DIARIO
# ============================================================================
for d in D:
    ultima_franja = max(T_d[d])
    for e in E:
        limite_inicio = ultima_franja - Dur[e] + 1
        for t in T_d[d]:
            if t > limite_inicio:
                for r in R:
                    # Deshabilita los instantes de inicio que provocarían un desbordamiento del evento más allá del límite diario
                    if (e, r, t) in y:
                        model += y[e, r, t] == 0, f"Desborde_d{d}_e{e}_r{r}_t{t}"

# ============================================================================
# 9. OFERTA GLOBAL DE SECCIONES SIN CONFLICTO
# ============================================================================

for k in K:
    # Agrupa los eventos del currículo k según su id_curso correspondiente
    cursos_en_k = {}
    for e in E_k[k]:
        s = EVENTO_SECCION[e]
        c = SECCION_CURSO[s]
        if c not in cursos_en_k:
            cursos_en_k[c] = set()
        cursos_en_k[c].add(e)
    
    # Identifica los cursos que operan con múltiples secciones en el currículo analizado
    for c, eventos_c in cursos_en_k.items():
        secciones_unicas = set(EVENTO_SECCION[e] for e in eventos_c)
        
        if len(secciones_unicas) > 1:
            num_secciones = len(secciones_unicas)
            eventos_otros = [e for e in E_k[k] if e not in eventos_c]
            
            for t in T:
                # Filtra las variables activas del curso multi-sección correspondientes a la franja horaria t
                vars_multi = [x[e, r, t] for e in eventos_c for r in R if (e, r, t) in x]
                if not vars_multi:
                    continue
                
                # Agrega la restricción de exclusión mutua para cada uno de los otros cursos pertenecientes a la malla curricular
                for e_other in eventos_otros:
                    vars_other = [x[e_other, r, t] for r in R if (e_other, r, t) in x]
                    
                    if vars_other:
                        # Aplica el acoplamiento de capacidad agregada para evitar traslapes horarias en la oferta académica
                        model += (
                            xsum(vars_multi) + xsum(vars_other) <= num_secciones, 
                            f"OfertaDirecta_{k}_{c}_{e_other}_t{t}"
                        )

# ============================================================================
# RESTRICCIONES BLANDAS Y FUNCIÓN OBJETIVO
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
    
    # Registra la estampa de tiempo inicial para medir la duración total del proceso de optimización
    start_time = time.time()
    status = model.optimize(max_seconds=7200)
    cpu_time = time.time() - start_time

    # Verifica si el optimizador ha encontrado al menos una solución factible antes de extraer los resultados
    if model.num_solutions > 0:
        
        # Recupera el valor óptimo de la función objetivo y la cota inferior alcanzados por el resolutor
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

        # Determina las etiquetas de los intervalos horarios basándose en el día que contenga la mayor cantidad de franjas
        max_slots = max(len(slots) for slots in T_d.values())
        horas_labels = [f"{7+i}:00 - {8+i}:00" for i in range(max_slots)]
        
        # Organiza los resultados en una matriz de datos bidimensional para representar el horario de forma estructurada
        schedule_matrix = pd.DataFrame("---", index=horas_labels, columns=D)

        # Recorre el diccionario de variables asignadas para identificar aquellas que se encuentran activas en la solución óptima
        for (e, r, t), var in x.items():
            if var.x >= 0.99:
                dia_actual = next(d for d, slots in T_d.items() if t in slots)
                slot_local = T_d[dia_actual].index(t)
                
                seccion = EVENTO_SECCION[e]
                curso = SECCION_CURSO[seccion]
                
                # Inserta el evento en la celda correspondiente cruzando el intervalo horario con el día asignado
                schedule_matrix.at[horas_labels[slot_local], dia_actual] = f"{curso} ({seccion}) [{r}]"

        schedule_matrix.to_csv("horario.csv")
        print("[INFO] Matriz exportada a 'horario.csv'.")
    else:
        print(f"\n[ALERTA] No se encontro ninguna solucion factible. Estado final: {status.name if hasattr(status, 'name') else status}")
        print(f"[INFO] Tiempo de Procesamiento invertido: {cpu_time:.2f} segundos")