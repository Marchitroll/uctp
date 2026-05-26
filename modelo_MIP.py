from mip import Model, BINARY, INTEGER, xsum, minimize
import time
from exportador_horarios import imprimir_metricas, exportar_horarios
from cargador_datos import cargar_datos_uctp
import argparse

# ============================================================================
# PARSEO DE ARGUMENTOS (Se realiza al inicio para interceptar -h/--help inmediatamente)
# ============================================================================
parser = argparse.ArgumentParser(description="Optimizador MIP para UCTP")
group = parser.add_mutually_exclusive_group()
group.add_argument(
    "--horas", "-hr",
    type=float,
    help="Tiempo maximo de optimizacion en horas"
)
group.add_argument(
    "--minutos", "-min",
    type=float,
    help="Tiempo maximo de optimizacion en minutos"
)
args = parser.parse_args()

if args.horas is not None:
    max_seconds = int(args.horas * 3600)
    tiempo_desc = f"{args.horas} horas"
elif args.minutos is not None:
    max_seconds = int(args.minutos * 60)
    tiempo_desc = f"{args.minutos} minutos"
else:
    max_seconds = 3600
    tiempo_desc = "1.0 horas (por defecto)"


# ============================================================================
# CARGA DE CONJUNTOS Y PARÁMETROS DESDE EL MÓDULO EXTRACCIÓN
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

    print(f"[INFO] Iniciando el proceso de optimizacion (maximo {tiempo_desc} / {max_seconds} segundos)...")
    
    # Registra la estampa de tiempo inicial para medir la duración total del proceso de optimización
    start_time = time.time()
    status = model.optimize(max_seconds=max_seconds)
    cpu_time = time.time() - start_time

    # Verifica si el optimizador ha encontrado al menos una solución factible antes de extraer los resultados
    if model.num_solutions > 0:
        imprimir_metricas(status, cpu_time, model)
        exportar_horarios(x, K, E_k, T_d, D, EVENTO_SECCION, SECCION_CURSO)
    else:
        print(f"\n[ALERTA] No se encontro ninguna solucion factible. Estado final: {status.name if hasattr(status, 'name') else status}")
        print(f"[INFO] Tiempo de Procesamiento invertido: {cpu_time:.2f} segundos")