from mip import Model, BINARY, INTEGER, CONTINUOUS, xsum, minimize
import time
import argparse
from exportador_horarios import imprimir_metricas, exportar_horarios, exportar_metricas_mip
from cargador_datos import cargar_datos_uctp
from tipos_uctp import DatosUCTP
from uctp_utils import detectar_escala, cargar_config_institucional


def crear_parser_mip() -> argparse.ArgumentParser:
    """Crea y retorna el parser de argumentos CLI para el optimizador MIP."""
    parser = argparse.ArgumentParser(description="Optimizador MIP para UCTP")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--horas",
        type=float,
        help="Tiempo maximo de optimizacion en horas"
    )
    group.add_argument(
        "--minutos",
        type=float,
        help="Tiempo maximo de optimizacion en minutos"
    )
    parser.add_argument(
        "--dir_datos",
        type=str,
        default="dataset",
        help="Directorio del dataset (default: 'dataset')"
    )
    parser.add_argument(
        "--etiqueta",
        type=str,
        default=None,
        help="Etiqueta identificadora de la instancia (ej. 's1')"
    )
    return parser


def construir_modelo_mip(datos: DatosUCTP) -> tuple[Model, dict, dict, tuple]:
    """
    Construye la formulación matemática MIP para UCTP usando HiGHS.
    
    Retorna:
        model: Objeto Model de python-mip con restricciones y función objetivo
        x: Variables de asignación x[e, r, t]
        y: Variables de inicio y[e, r, t]
        vars_blandas: Tupla (P_almuerzo, P_espaciado, P_jueves, P_sabado, P_ventanas)
    """
    D, T, T_d, d_jue, Almuerzo = datos.D, datos.T, datos.T_d, datos.d_jue, datos.Almuerzo
    R, CAP, ES_VIRTUAL = datos.R, datos.CAP, datos.ES_VIRTUAL
    S, SECCION_CURSO, Alumno = datos.S, datos.SECCION_CURSO, datos.Alumno
    E, E_s, E_p, Dur, EVENTO_SECCION = datos.E, datos.E_s, datos.E_p, datos.Dur, datos.EVENTO_SECCION
    P, K, E_k, Disp = datos.P, datos.K, datos.E_k, datos.Disp
    F, Tiene, Req = datos.F, datos.Tiene, datos.Req
    Cursos_Agrupados = list(E_s.values())

    model = Model(name="UCTP_Universidad", solver_name="HiGHS")

    # ========================================================================
    # FILTRADO TOPOLÓGICO (REDUCCIÓN DE DOMINIO)
    # ========================================================================
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
                p_asignado = next(prof for prof, eventos_prof in E_p.items() if e in eventos_prof)
                for t in franjas_operativas:
                    if Disp[(p_asignado, t)] == 1:
                        Valid_ERT.add((e, r, t))

    # ========================================================================
    # VARIABLES DE DECISIÓN (INSTANCIACIÓN DISPERSA)
    # ========================================================================
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

    P_almuerzo = model.add_var(name="P_almuerzo", var_type=INTEGER, lb=0)
    v_espaciado = {
        (tuple(c), i): model.add_var(name=f"v_espaciado_{c[0]}_{i}", var_type=CONTINUOUS, lb=0)
        for c in Cursos_Agrupados
        for i in range(len(D) - 1)
    }
    P_espaciado = model.add_var(name="P_espaciado", var_type=CONTINUOUS, lb=0)
    P_jueves = model.add_var(name="P_jueves", var_type=INTEGER, lb=0)
    P_sabado = model.add_var(name="P_sabado", var_type=INTEGER, lb=0)
    P_ventanas = model.add_var(name="P_ventanas", var_type=CONTINUOUS, lb=0)

    print("[INFO] Inicialización completa: conjuntos, parámetros y variables.")
    print(f"       E={len(E)} eventos | R={len(R)} salones | T={len(T)} franjas | P={len(P)} profesores")

    # ========================================================================
    # 1. DISPONIBILIDAD Y NO COLISIÓN DEL PROFESOR
    # ========================================================================
    for p in P:
        for t in T:
            suma_clases_profesor = xsum(x[e, r, t] for e in E_p[p] for r in R if (e, r, t) in x)
            model += suma_clases_profesor <= Disp[p, t], f"DispProf_{p}_franja_{t}"

    # ========================================================================
    # 2. CARGA DIARIA MÁXIMA DEL PROFESOR (MÁXIMO 8 HORAS DE CLASE POR DÍA)
    # ========================================================================
    MAX_HORAS_DIARIAS = 8
    for p in P:
        for d in D:
            suma_clases_diarias = xsum(
                x[e, r, t] 
                for e in E_p[p] 
                for r in R 
                for t in T_d[d] 
                if (e, r, t) in x
            )
            model += suma_clases_diarias <= MAX_HORAS_DIARIAS, f"CargaMaximaProfesor_{p}_{d}"

    # ========================================================================
    # 3. COBERTURA TOTAL DE EVENTOS
    # ========================================================================
    for e in E:
        suma_asignaciones = xsum(x[e, r, t] for r in R for t in T if (e, r, t) in x)
        model += suma_asignaciones == Dur[e], f"Cobertura_Evento_{e}"

    # ========================================================================
    # 4. ESTABILIDAD DE SALONES
    # ========================================================================
    for s in S:
        for r in R:
            if (s, r) not in w:
                continue
            for e in E_s[s]:
                suma_temporal = xsum(x[e, r, t] for t in T if (e, r, t) in x)
                model += suma_temporal <= Dur[e] * w[s, r], f"Vincular_w_{s}_{e}_{r}"

    for s in S:
        model += xsum(w[s, r] for r in R if (s, r) in w) <= 2, f"EstabilidadSalones_{s}"

    # ========================================================================
    # 5. NO COLISIÓN DE SALONES FÍSICOS
    # ========================================================================
    for r in R:
        if not ES_VIRTUAL[r]:
            for t in T:
                suma_eventos_salon = xsum(x[e, r, t] for e in E if (e, r, t) in x)
                model += suma_eventos_salon <= 1, f"ColisionSalonesFisicos_{r}_franja_{t}"

    # ========================================================================
    # 6. CONTINUIDAD Y NO FRAGMENTACIÓN
    # ========================================================================
    for e in E:
        model += xsum(y[e, r, t] for r in R for t in T if (e, r, t) in y) == 1, f"UnicoInicio_Evento_{e}"

    for d in D:
        for t in T_d[d]:
            for e in E:
                arranques_validos = [tau for tau in T_d[d] if (t - Dur[e] + 1) <= tau <= t]
                for r in R:
                    if (e, r, t) in x:
                        suma_arranques = xsum(y[e, r, tau] for tau in arranques_validos if (e, r, tau) in y)
                        model += x[e, r, t] == suma_arranques, f"Continua_d{d}_t{t}_e{e}_r{r}"

    # ========================================================================
    # 7. ESPACIADO DE SESIONES (RESTRICCIÓN BLANDA PENALIZADA)
    # ========================================================================
    for c in Cursos_Agrupados:
        for i in range(len(D) - 1):
            dia_actual = D[i]
            dia_siguiente = D[i+1]
            arranques_hoy = xsum(y[e, r, t] for e in c for r in R for t in T_d[dia_actual] if (e, r, t) in y)
            arranques_manana = xsum(y[e, r, t] for e in c for r in R for t in T_d[dia_siguiente] if (e, r, t) in y)
            model += arranques_hoy + arranques_manana <= 1 + v_espaciado[tuple(c), i], f"Espaciado_Curso_{c[0]}_Dia_{i}"

    model += P_espaciado == xsum(
        v_espaciado[tuple(c), i]
        for c in Cursos_Agrupados
        for i in range(len(D) - 1)
    ), "Calculo_Penalizacion_Espaciado"

    # ========================================================================
    # 8. CONTROL DE DESBORDAMIENTO DIARIO
    # ========================================================================
    for d in D:
        ultima_franja = max(T_d[d])
        for e in E:
            limite_inicio = ultima_franja - Dur[e] + 1
            for t in T_d[d]:
                if t > limite_inicio:
                    for r in R:
                        if (e, r, t) in y:
                            model += y[e, r, t] == 0, f"Desborde_d{d}_e{e}_r{r}_t{t}"

    # ========================================================================
    # 9. OFERTA GLOBAL DE SECCIONES SIN CONFLICTO
    # ========================================================================
    for k in K:
        cursos_en_k = {}
        for e in E_k[k]:
            s = EVENTO_SECCION[e]
            c = SECCION_CURSO[s]
            if c not in cursos_en_k:
                cursos_en_k[c] = set()
            cursos_en_k[c].add(e)
        
        for c, eventos_c in cursos_en_k.items():
            secciones_unicas = set(EVENTO_SECCION[e] for e in eventos_c)
            if len(secciones_unicas) > 1:
                num_secciones = len(secciones_unicas)
                eventos_otros = [e for e in E_k[k] if e not in eventos_c]
                
                for t in T:
                    vars_multi = [x[e, r, t] for e in eventos_c for r in R if (e, r, t) in x]
                    if not vars_multi:
                        continue
                    for e_other in eventos_otros:
                        vars_other = [x[e_other, r, t] for r in R if (e_other, r, t) in x]
                        if vars_other:
                            model += (
                                xsum(vars_multi) + xsum(vars_other) <= num_secciones, 
                                f"ConflictoCurricular_{k}_{c}_{e_other}_t{t}"
                            )

    # ========================================================================
    # RESTRICCIONES BLANDAS Y FUNCIÓN OBJETIVO
    # ========================================================================
    model += P_almuerzo == xsum(
        x[e, r, t]
        for (e, r, t) in x.keys()
        if Almuerzo[t] == 1
    ), "Calculo_Penalizacion_Almuerzo"

    d_sab = "Sabado"
    model += P_jueves == xsum(
        x[e, r, t]
        for (e, r, t) in x.keys()
        if t in T_d[d_jue]
    ), "Calculo_Penalizacion_Jueves"

    model += P_sabado == xsum(
        x[e, r, t]
        for (e, r, t) in x.keys()
        if t in T_d[d_sab]
    ), "Calculo_Penalizacion_Sabado"

    gap_vars = []
    for p in P:
        for d in D:
            slots_d = T_d[d]
            if not slots_d:
                continue
            
            f_p = {}
            l_p = {}
            for idx_t, t in enumerate(slots_d):
                f_p[t] = model.add_var(name=f"f_{p}_{t}", var_type=CONTINUOUS, lb=0, ub=1)
                l_p[t] = model.add_var(name=f"l_{p}_{t}", var_type=CONTINUOUS, lb=0, ub=1)
                u_pt = xsum(x[e, r, t] for e in E_p[p] for r in R if (e, r, t) in x)
                
                model += f_p[t] >= u_pt, f"F_ge_U_{p}_{t}"
                if idx_t > 0:
                    prev_t = slots_d[idx_t - 1]
                    model += f_p[t] >= f_p[prev_t], f"F_prop_{p}_{t}"
                    
                model += l_p[t] >= u_pt, f"L_ge_U_{p}_{t}"
                if idx_t > 0:
                    prev_t = slots_d[idx_t - 1]
                    model += l_p[prev_t] >= l_p[t], f"L_prop_{p}_{prev_t}"
                    
            for t in slots_d:
                if Almuerzo[t] == 0:
                    u_pt = xsum(x[e, r, t] for e in E_p[p] for r in R if (e, r, t) in x)
                    g_pt = model.add_var(name=f"gap_{p}_{t}", var_type=CONTINUOUS, lb=0)
                    model += g_pt >= f_p[t] + l_p[t] - 1 - u_pt, f"GapDef_{p}_{t}"
                    gap_vars.append(g_pt)

    model += P_ventanas == xsum(gap_vars), "Calculo_Penalizacion_Ventanas"

    pesos = cargar_config_institucional().get("pesos_penalizacion", {})
    W_A = pesos.get("W_A", 1)
    W_E = pesos.get("W_E", 10)
    W_JUE = pesos.get("W_JUE", 1)
    W_SAB = pesos.get("W_SAB", 3)
    W_V = pesos.get("W_V", 2)

    model.objective = minimize(
        W_A * P_almuerzo + 
        W_E * P_espaciado + 
        W_JUE * P_jueves + 
        W_SAB * P_sabado + 
        W_V * P_ventanas
    )

    return model, x, y, (P_almuerzo, P_espaciado, P_jueves, P_sabado, P_ventanas)


def resolver_mip(minutos: float = None, horas: float = None, dir_datos: str = "dataset", etiqueta: str = None):
    """
    Carga los datos de la instancia, construye el modelo MIP y ejecuta la optimización con HiGHS.
    """
    if horas is not None:
        max_seconds = int(horas * 3600)
        tiempo_desc = f"{horas} horas"
    elif minutos is not None:
        max_seconds = int(minutos * 60)
        tiempo_desc = f"{minutos} minutos"
    else:
        max_seconds = 7200
        tiempo_desc = "2.0 horas (por defecto)"

    datos = cargar_datos_uctp(data_dir=dir_datos)
    model, x, y, vars_blandas = construir_modelo_mip(datos)
    P_almuerzo, P_espaciado, P_jueves, P_sabado, P_ventanas = vars_blandas

    lp_filename = f"UCTP_{etiqueta}.lp" if etiqueta else "UCTP_Universidad.lp"
    model.write(lp_filename)
    print(f"[INFO] Archivo LP generado exitosamente: {lp_filename}")

    model.verbose = 2
    print(f"[INFO] Iniciando el proceso de optimización (máximo {tiempo_desc} / {max_seconds} segundos)...")

    start_time = time.process_time()
    status = model.optimize(max_seconds=max_seconds)
    cpu_time = time.process_time() - start_time
    nodes_explored = 0

    escala_base = detectar_escala(datos.K)
    escala_salida = f"{escala_base}_{etiqueta}" if etiqueta else None
    exportar_metricas_mip(status, cpu_time, nodes_explored, model, datos.K, output_dir=escala_salida)

    pesos = cargar_config_institucional().get("pesos_penalizacion", {})
    W_A = pesos.get("W_A", 1)
    W_E = pesos.get("W_E", 10)
    W_JUE = pesos.get("W_JUE", 1)
    W_SAB = pesos.get("W_SAB", 3)
    W_V = pesos.get("W_V", 2)

    if model.num_solutions > 0:
        imprimir_metricas(status, cpu_time, model, nodes_explored=nodes_explored)
        print(" [DETALLE DE RESTRICCIONES BLANDAS]")
        print(" " + "-"*50)
        print(f"   - Almuerzo (franjas de clase) : {P_almuerzo.x:.0f} (peso {W_A})")
        print(f"   - Espaciado (infracciones)     : {P_espaciado.x:.0f} (peso {W_E})")
        print(f"   - Jueves (franjas virtuales)  : {P_jueves.x:.0f} (peso {W_JUE})")
        print(f"   - Sábado (franjas fin de sem) : {P_sabado.x:.0f} (peso {W_SAB})")
        print(f"   - Ventanas docentes (ociosas) : {P_ventanas.x:.0f} (peso {W_V})")
        print(f"   => Costo Total Ponderado (Z)   : {model.objective_value:.2f}")
        print(" " + "-"*50 + "\n")

        out_path = f"horarios_{escala_base}_{etiqueta}/MIP" if etiqueta else f"horarios_{escala_base}/MIP"
        exportar_horarios(
            x, datos.K, datos.E_k, datos.T_d, datos.D, 
            datos.EVENTO_SECCION, datos.SECCION_CURSO, 
            E_p=datos.E_p, output_dir=out_path
        )
    else:
        print(f"\n[ALERTA] No se encontró ninguna solución factible. Estado final: {status.name if hasattr(status, 'name') else status}")
        print(f"[INFO] Tiempo de Procesamiento CPU: {cpu_time:.2f} segundos")
        print(f"[INFO] Nodos B&B Explorados      : {nodes_explored}")

    return model, status, cpu_time


def main():
    parser = crear_parser_mip()
    args = parser.parse_args()
    resolver_mip(
        minutos=args.minutos,
        horas=args.horas,
        dir_datos=args.dir_datos,
        etiqueta=args.etiqueta
    )


if __name__ == '__main__':
    main()