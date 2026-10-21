"""Optimizador exacto de programación entera mixta (MIP) para el UCTP con solver HiGHS."""
import argparse
import time
from mip import Model, BINARY, INTEGER, CONTINUOUS, xsum, minimize
from cargador_datos import cargar_datos_uctp
from exportador_horarios import imprimir_metricas, exportar_horarios, exportar_metricas_mip
from tipos_uctp import DatosUCTP
from uctp_utils import detectar_escala, cargar_config_institucional

def crear_parser_mip() -> argparse.ArgumentParser:
    """Crea y retorna el parser de argumentos CLI para el optimizador MIP."""
    parser = argparse.ArgumentParser(description="Optimizador MIP para UCTP")
    grupo_tiempo = parser.add_mutually_exclusive_group()
    grupo_tiempo.add_argument(
        "--horas",
        type=float,
        help="Tiempo máximo de optimización en horas",
    )
    grupo_tiempo.add_argument(
        "--minutos",
        type=float,
        help="Tiempo máximo de optimización en minutos",
    )
    parser.add_argument(
        "--dir_datos",
        type=str,
        default="dataset",
        help="Directorio del dataset (default: 'dataset')",
    )
    parser.add_argument(
        "--etiqueta",
        type=str,
        default=None,
        help="Etiqueta identificadora de la instancia (ej. 's1')",
    )
    return parser


def construir_modelo_mip(datos: DatosUCTP) -> tuple[Model, dict, dict, tuple]:
    """
    Construye la formulación matemática MIP para UCTP usando HiGHS.

    Retorna:
        model: Objeto Model de python-mip con restricciones y función objetivo
        x: Variables de asignación x[evento, salon, franja]
        y: Variables de inicio y[evento, salon, franja]
        vars_blandas: Tupla (penalizacion_almuerzo, penalizacion_espaciado, penalizacion_jueves, penalizacion_sabado, penalizacion_ventanas)
    """
    dias = datos.dias
    franjas_horarias = datos.franjas_horarias
    franjas_por_dia = datos.franjas_por_dia
    dia_cierre_remoto = datos.dia_cierre_remoto
    almuerzo_por_franja = datos.almuerzo_por_dia
    salones = datos.salones
    capacidad_por_salon = datos.capacidad_por_salon
    es_virtual_por_salon = datos.es_virtual_por_salon
    secciones = datos.secciones
    curso_por_seccion = datos.curso_por_seccion
    alumnos_por_seccion = datos.alumnos_por_seccion
    eventos = datos.eventos
    eventos_por_seccion = datos.eventos_por_seccion
    eventos_por_profesor = datos.eventos_por_profesor
    duracion_por_evento = datos.duracion_por_evento
    seccion_por_evento = datos.seccion_por_evento
    profesores = datos.profesores
    curriculos = datos.curriculos
    eventos_por_curriculo = datos.eventos_por_curriculo
    disponibilidad_por_profesor = datos.disponibilidad_por_profesor
    caracteristicas = datos.caracteristicas
    salon_tiene_caracteristica = datos.salon_tiene_caracteristica
    seccion_requiere_caracteristica = datos.seccion_requiere_caracteristica
    cursos_agrupados = list(eventos_por_seccion.values())

    model = Model(name="UCTP_Universidad", solver_name="HiGHS")

    # Dominio válido de salones y franjas por evento
    pares_seccion_salon_validos = set()
    ternas_evento_salon_franja_validas = set()

    for seccion in secciones:
        salones_elegibles = [
            salon for salon in salones 
            if capacidad_por_salon[salon] >= alumnos_por_seccion[seccion] 
            and all(seccion_requiere_caracteristica[(seccion, carac)] <= salon_tiene_caracteristica[(salon, carac)] for carac in caracteristicas)
        ]
        
        for salon in salones_elegibles:
            pares_seccion_salon_validos.add((seccion, salon))
            
            if es_virtual_por_salon[salon]:
                franjas_operativas = franjas_por_dia[dia_cierre_remoto]
            else:
                franjas_operativas = [franja for franja in franjas_horarias if franja not in franjas_por_dia[dia_cierre_remoto]]
                
            for evento in eventos_por_seccion[seccion]:
                profesor_asignado = next(prof for prof, eventos_prof in eventos_por_profesor.items() if evento in eventos_prof)
                for franja in franjas_operativas:
                    if disponibilidad_por_profesor[(profesor_asignado, franja)] == 1:
                        ternas_evento_salon_franja_validas.add((evento, salon, franja))

    # Variables de decisión
    x = {
        (evento, salon, franja): model.add_var(name=f"x_{evento}_{salon}_{franja}", var_type=BINARY)
        for (evento, salon, franja) in ternas_evento_salon_franja_validas
    }

    y = {
        (evento, salon, franja): model.add_var(name=f"y_{evento}_{salon}_{franja}", var_type=BINARY)
        for (evento, salon, franja) in ternas_evento_salon_franja_validas
    }

    indicador_seccion_salon = {
        (seccion, salon): model.add_var(name=f"w_{seccion}_{salon}", var_type=BINARY)
        for (seccion, salon) in pares_seccion_salon_validos
    }

    penalizacion_almuerzo = model.add_var(name="P_almuerzo", var_type=INTEGER, lb=0)
    violaciones_espaciado = {
        (tuple(eventos_curso), indice_dia): model.add_var(
            name=f"violacion_espaciado_{eventos_curso[0]}_{indice_dia}", var_type=CONTINUOUS, lb=0
        )
        for eventos_curso in cursos_agrupados
        for indice_dia in range(len(dias) - 1)
    }
    penalizacion_espaciado = model.add_var(name="P_espaciado", var_type=CONTINUOUS, lb=0)
    penalizacion_jueves = model.add_var(name="P_jueves", var_type=INTEGER, lb=0)
    penalizacion_sabado = model.add_var(name="P_sabado", var_type=INTEGER, lb=0)
    penalizacion_ventanas = model.add_var(name="P_ventanas", var_type=CONTINUOUS, lb=0)

    print("[INFO] Inicialización completa: conjuntos, parámetros y variables.")
    print(f"       Eventos={len(eventos)} | Salones={len(salones)} | Franjas={len(franjas_horarias)} | Profesores={len(profesores)}")

    # 1. Disponibilidad y no colisión de docentes
    for profesor in profesores:
        for franja in franjas_horarias:
            suma_clases_profesor = xsum(
                x[evento, salon, franja]
                for evento in eventos_por_profesor[profesor]
                for salon in salones
                if (evento, salon, franja) in x
            )
            model += suma_clases_profesor <= disponibilidad_por_profesor[profesor, franja], f"DispProf_{profesor}_franja_{franja}"

    # 2. Carga diaria máxima por docente (8h)
    MAX_HORAS_DIARIAS = 8
    for profesor in profesores:
        for dia in dias:
            suma_clases_diarias = xsum(
                x[evento, salon, franja]
                for evento in eventos_por_profesor[profesor]
                for salon in salones
                for franja in franjas_por_dia[dia]
                if (evento, salon, franja) in x
            )
            model += suma_clases_diarias <= MAX_HORAS_DIARIAS, f"CargaMaximaProfesor_{profesor}_{dia}"

    # 3. Cobertura de eventos
    for evento in eventos:
        suma_asignaciones = xsum(
            x[evento, salon, franja]
            for salon in salones
            for franja in franjas_horarias
            if (evento, salon, franja) in x
        )
        model += suma_asignaciones == duracion_por_evento[evento], f"Cobertura_Evento_{evento}"

    # 4. Estabilidad de salones (máximo 2 por sección)
    for seccion in secciones:
        for salon in salones:
            if (seccion, salon) not in indicador_seccion_salon:
                continue
            for evento in eventos_por_seccion[seccion]:
                suma_temporal = xsum(
                    x[evento, salon, franja]
                    for franja in franjas_horarias
                    if (evento, salon, franja) in x
                )
                model += (
                    suma_temporal <= duracion_por_evento[evento] * indicador_seccion_salon[seccion, salon],
                    f"Vincular_salon_{seccion}_{evento}_{salon}",
                )

    for seccion in secciones:
        model += (
            xsum(indicador_seccion_salon[seccion, salon] for salon in salones if (seccion, salon) in indicador_seccion_salon) <= 2,
            f"EstabilidadSalones_{seccion}",
        )

    # 5. No colisión en salones físicos
    for salon in salones:
        if not es_virtual_por_salon[salon]:
            for franja in franjas_horarias:
                suma_eventos_salon = xsum(
                    x[evento, salon, franja]
                    for evento in eventos
                    if (evento, salon, franja) in x
                )
                model += suma_eventos_salon <= 1, f"ColisionSalonesFisicos_{salon}_franja_{franja}"

    # 6. Continuidad y franja única de inicio
    for evento in eventos:
        model += (
            xsum(y[evento, salon, franja] for salon in salones for franja in franjas_horarias if (evento, salon, franja) in y) == 1,
            f"UnicoInicio_Evento_{evento}",
        )

    for dia in dias:
        for franja in franjas_por_dia[dia]:
            for evento in eventos:
                arranques_validos = [
                    tau for tau in franjas_por_dia[dia]
                    if (franja - duracion_por_evento[evento] + 1) <= tau <= franja
                ]
                for salon in salones:
                    if (evento, salon, franja) in x:
                        suma_arranques = xsum(
                            y[evento, salon, tau]
                            for tau in arranques_validos
                            if (evento, salon, tau) in y
                        )
                        model += x[evento, salon, franja] == suma_arranques, f"Continua_d{dia}_t{franja}_e{evento}_r{salon}"

    # 7. Espaciado entre sesiones consecutivas (blanda)
    for eventos_curso in cursos_agrupados:
        for indice_dia in range(len(dias) - 1):
            dia_actual = dias[indice_dia]
            dia_siguiente = dias[indice_dia + 1]
            arranques_hoy = xsum(
                y[evento, salon, franja]
                for evento in eventos_curso
                for salon in salones
                for franja in franjas_por_dia[dia_actual]
                if (evento, salon, franja) in y
            )
            arranques_manana = xsum(
                y[evento, salon, franja]
                for evento in eventos_curso
                for salon in salones
                for franja in franjas_por_dia[dia_siguiente]
                if (evento, salon, franja) in y
            )
            model += (
                arranques_hoy + arranques_manana <= 1 + violaciones_espaciado[tuple(eventos_curso), indice_dia],
                f"Espaciado_Curso_{eventos_curso[0]}_Dia_{indice_dia}",
            )

    model += penalizacion_espaciado == xsum(
        violaciones_espaciado[tuple(eventos_curso), indice_dia]
        for eventos_curso in cursos_agrupados
        for indice_dia in range(len(dias) - 1)
    ), "Calculo_Penalizacion_Espaciado"

    # 8. Sin desborde al final del día
    for dia in dias:
        ultima_franja = max(franjas_por_dia[dia])
        for evento in eventos:
            limite_inicio = ultima_franja - duracion_por_evento[evento] + 1
            for franja in franjas_por_dia[dia]:
                if franja > limite_inicio:
                    for salon in salones:
                        if (evento, salon, franja) in y:
                            model += y[evento, salon, franja] == 0, f"Desborde_d{dia}_e{evento}_r{salon}_t{franja}"

    # 9. No solapamiento curricular
    for curriculo in curriculos:
        cursos_en_curriculo = {}
        for evento in eventos_por_curriculo[curriculo]:
            seccion = seccion_por_evento[evento]
            curso = curso_por_seccion[seccion]
            if curso not in cursos_en_curriculo:
                cursos_en_curriculo[curso] = set()
            cursos_en_curriculo[curso].add(evento)
        
        for curso, eventos_curso in cursos_en_curriculo.items():
            secciones_unicas = set(seccion_por_evento[ev] for ev in eventos_curso)
            if len(secciones_unicas) > 1:
                num_secciones = len(secciones_unicas)
                eventos_otros = [ev for ev in eventos_por_curriculo[curriculo] if ev not in eventos_curso]
                
                for franja in franjas_horarias:
                    vars_multi = [x[ev, salon, franja] for ev in eventos_curso for salon in salones if (ev, salon, franja) in x]
                    if not vars_multi:
                        continue
                    for evento_otro in eventos_otros:
                        vars_otro = [x[evento_otro, salon, franja] for salon in salones if (evento_otro, salon, franja) in x]
                        if vars_otro:
                            model += (
                                xsum(vars_multi) + xsum(vars_otro) <= num_secciones, 
                                f"ConflictoCurricular_{curriculo}_{curso}_{evento_otro}_t{franja}",
                            )

    # Penalizaciones blandas y función objetivo
    model += penalizacion_almuerzo == xsum(
        x[evento, salon, franja]
        for (evento, salon, franja) in x.keys()
        if almuerzo_por_franja[franja] == 1
    ), "Calculo_Penalizacion_Almuerzo"

    dia_sabado = "Sabado"
    model += penalizacion_jueves == xsum(
        x[evento, salon, franja]
        for (evento, salon, franja) in x.keys()
        if franja in franjas_por_dia[dia_cierre_remoto]
    ), "Calculo_Penalizacion_Jueves"

    model += penalizacion_sabado == xsum(
        x[evento, salon, franja]
        for (evento, salon, franja) in x.keys()
        if dia_sabado in franjas_por_dia and franja in franjas_por_dia[dia_sabado]
    ), "Calculo_Penalizacion_Sabado"

    # Penalización de ventanas docentes libres (blanda)
    # Cada variable representa un posible espacio libre entre 2 clases de un profesor.
    variables_brecha = []
    for profesor in profesores:
        for dia in dias:
            franjas_dia = franjas_por_dia[dia]
            if not franjas_dia:
                continue
            
            inicio_jornada = {}
            final_jornada = {}
            for indice_franja, franja in enumerate(franjas_dia):
                # Indicadores de inicio y final de jornada para el profesor en la franja actual. Se minimizarán.
                inicio_jornada[franja] = model.add_var(name=f"primera_ocup_{profesor}_{franja}", var_type=CONTINUOUS, lb=0, ub=1)
                final_jornada[franja] = model.add_var(name=f"ultima_ocup_{profesor}_{franja}", var_type=CONTINUOUS, lb=0, ub=1)
                ocupacion_profesor_franja = xsum(
                    x[evento, salon, franja]
                    for evento in eventos_por_profesor[profesor]
                    for salon in salones
                    if (evento, salon, franja) in x
                )
                
                model += inicio_jornada[franja] >= ocupacion_profesor_franja, f"PrimeraOcup_ge_U_{profesor}_{franja}"
                if indice_franja > 0:
                    franja_anterior = franjas_dia[indice_franja - 1]
                    model += inicio_jornada[franja] >= inicio_jornada[franja_anterior], f"PrimeraOcup_prop_{profesor}_{franja}"
                    
                model += final_jornada[franja] >= ocupacion_profesor_franja, f"UltimaOcup_ge_U_{profesor}_{franja}"
                if indice_franja > 0:
                    franja_anterior = franjas_dia[indice_franja - 1]
                    model += final_jornada[franja_anterior] >= final_jornada[franja], f"UltimaOcup_prop_{profesor}_{franja_anterior}"
            
            # Se calcula la brecha docente si no hay almuerzo en esa franja.      
            for franja in franjas_dia:
                if almuerzo_por_franja[franja] == 0:
                    ocupacion_profesor_franja = xsum(
                        x[evento, salon, franja]
                        for evento in eventos_por_profesor[profesor]
                        for salon in salones
                        if (evento, salon, franja) in x
                    )
                    brecha_profesor_franja = model.add_var(name=f"brecha_{profesor}_{franja}", var_type=CONTINUOUS, lb=0)
                    # La brecha se calcula como la diferencia entre la ocupación del profesor y los indicadores de inicio y final de jornada.
                    model += (
                        brecha_profesor_franja >= inicio_jornada[franja] + final_jornada[franja] - 1 - ocupacion_profesor_franja,
                        f"BrechaDef_{profesor}_{franja}",
                    )
                    variables_brecha.append(brecha_profesor_franja)

    
    model += penalizacion_ventanas == xsum(variables_brecha), "Calculo_Penalizacion_Ventanas"

    pesos = cargar_config_institucional().get("pesos_penalizacion", {})
    peso_almuerzo = pesos.get("W_A", 1)
    peso_espaciado = pesos.get("W_E", 10)
    peso_jueves = pesos.get("W_JUE", 1)
    peso_sabado = pesos.get("W_SAB", 3)
    peso_ventanas = pesos.get("W_V", 2)

    model.objective = minimize(
        peso_almuerzo * penalizacion_almuerzo + 
        peso_espaciado * penalizacion_espaciado + 
        peso_jueves * penalizacion_jueves + 
        peso_sabado * penalizacion_sabado + 
        peso_ventanas * penalizacion_ventanas
    )

    return model, x, y, (penalizacion_almuerzo, penalizacion_espaciado, penalizacion_jueves, penalizacion_sabado, penalizacion_ventanas)


def resolver_mip(minutos: float = None, horas: float = None, dir_datos: str = "dataset", etiqueta: str = None):
    """Ejecuta la optimización del modelo MIP con HiGHS."""
    if horas is not None:
        segundos_maximos = int(horas * 3600)
        descripcion_tiempo = f"{horas} horas"
    elif minutos is not None:
        segundos_maximos = int(minutos * 60)
        descripcion_tiempo = f"{minutos} minutos"
    else:
        segundos_maximos = 7200
        descripcion_tiempo = "2.0 horas (por defecto)"

    datos = cargar_datos_uctp(dir_datos=dir_datos)
    model, x, y, vars_blandas = construir_modelo_mip(datos)
    penalizacion_almuerzo, penalizacion_espaciado, penalizacion_jueves, penalizacion_sabado, penalizacion_ventanas = vars_blandas

    nombre_archivo_lp = f"UCTP_{etiqueta}.lp" if etiqueta else "UCTP_Universidad.lp"
    model.write(nombre_archivo_lp)
    print(f"[INFO] Archivo LP generado exitosamente: {nombre_archivo_lp}")

    model.verbose = 2
    print(f"[INFO] Iniciando el proceso de optimización (máximo {descripcion_tiempo} / {segundos_maximos} segundos)...")

    tiempo_inicio = time.process_time()
    estado = model.optimize(max_seconds=segundos_maximos)
    tiempo_cpu = time.process_time() - tiempo_inicio
    nodos_explorados = 0

    desglose_penalizaciones = None
    if model.num_solutions > 0:
        desglose_penalizaciones = {
            "penalizacion_almuerzo": round(float(penalizacion_almuerzo.x)),
            "penalizacion_espaciado": round(float(penalizacion_espaciado.x)),
            "penalizacion_jueves": round(float(penalizacion_jueves.x)),
            "penalizacion_sabado": round(float(penalizacion_sabado.x)),
            "penalizacion_ventanas": round(float(penalizacion_ventanas.x)),
        }

    escala_base = detectar_escala(datos.curriculos)
    escala_salida = f"{escala_base}_{etiqueta}" if etiqueta else None
    exportar_metricas_mip(
        estado,
        tiempo_cpu,
        nodos_explorados,
        model,
        datos.curriculos,
        dir_salida=escala_salida,
        desglose_penalizaciones=desglose_penalizaciones,
    )

    pesos = cargar_config_institucional().get("pesos_penalizacion", {})
    peso_almuerzo = pesos.get("W_A", 1)
    peso_espaciado = pesos.get("W_E", 10)
    peso_jueves = pesos.get("W_JUE", 1)
    peso_sabado = pesos.get("W_SAB", 3)
    peso_ventanas = pesos.get("W_V", 2)

    if model.num_solutions > 0:
        imprimir_metricas(estado, tiempo_cpu, model, nodos_explorados=nodos_explorados)
        print(" [DETALLE DE RESTRICCIONES BLANDAS]")
        print(" " + "-"*50)
        print(f"   - Almuerzo (franjas de clase) : {penalizacion_almuerzo.x:.0f} (peso {peso_almuerzo})")
        print(f"   - Espaciado (infracciones)     : {penalizacion_espaciado.x:.0f} (peso {peso_espaciado})")
        print(f"   - Jueves (franjas virtuales)  : {penalizacion_jueves.x:.0f} (peso {peso_jueves})")
        print(f"   - Sábado (franjas fin de sem) : {penalizacion_sabado.x:.0f} (peso {peso_sabado})")
        print(f"   - Ventanas docentes (ociosas) : {penalizacion_ventanas.x:.0f} (peso {peso_ventanas})")
        print(f"   => Costo Total Ponderado (Z)   : {model.objective_value:.2f}")
        print(" " + "-"*50 + "\n")

        dir_horarios_salida = f"horarios_{escala_base}_{etiqueta}/MIP" if etiqueta else f"horarios_{escala_base}/MIP"
        exportar_horarios(
            x,
            curriculos=datos.curriculos,
            eventos_por_curriculo=datos.eventos_por_curriculo,
            franjas_por_dia=datos.franjas_por_dia,
            dias=datos.dias,
            seccion_por_evento=datos.seccion_por_evento,
            curso_por_seccion=datos.curso_por_seccion,
            eventos_por_profesor=datos.eventos_por_profesor,
            dir_salida=dir_horarios_salida,
        )
    else:
        print(f"\n[ALERTA] No se encontró ninguna solución factible. Estado final: {estado.name if hasattr(estado, 'name') else estado}")
        print(f"[INFO] Tiempo de Procesamiento CPU: {tiempo_cpu:.2f} segundos")
        print(f"[INFO] Nodos B&B Explorados      : {nodos_explorados}")

    return model, estado, tiempo_cpu

def main():
    parser = crear_parser_mip()
    args = parser.parse_args()
    resolver_mip(
        minutos=args.minutos,
        horas=args.horas,
        dir_datos=args.dir_datos,
        etiqueta=args.etiqueta,
    )

if __name__ == '__main__':
    main()