"""Genera el reporte comparativo analítico consolidado (MIP vs metaheurísticas) y sincroniza docs/resultados_experimentales.md."""
import csv
import json
import os
from datetime import datetime
import pandas as pd


def obtener_dimensiones_instancia(clave_instancia: str) -> dict[str, int]:
    """Inspecciona dinámicamente las dimensiones reales de los archivos CSV de la instancia."""
    directorio_instancia = os.path.join("dataset", clave_instancia)
    if not os.path.isdir(directorio_instancia):
        directorio_instancia = "dataset"

    def contar_filas_csv(nombre_archivo: str) -> int:
        ruta_archivo = os.path.join(directorio_instancia, nombre_archivo)
        if not os.path.exists(ruta_archivo):
            return 0
        with open(ruta_archivo, "r", encoding="utf-8") as archivo_csv:
            lector = csv.reader(archivo_csv)
            next(lector, None)
            return sum(1 for _ in lector)

    return {
        "eventos": contar_filas_csv("eventos.csv"),
        "profesores": contar_filas_csv("profesores.csv"),
        "salones": contar_filas_csv("salones.csv"),
        "secciones": contar_filas_csv("secciones.csv"),
    }


def cargar_resumen(dir_metodo: str, escala: str) -> dict | None:
    """Carga el resumen JSON de métricas para un método y escala específicos."""
    ruta_archivo = os.path.join(dir_metodo, f"resumen_{escala}.json")
    if os.path.exists(ruta_archivo):
        try:
            with open(ruta_archivo, "r", encoding="utf-8") as archivo:
                return json.load(archivo)
        except Exception as error:
            print(f"[WARN] Error al leer {ruta_archivo}: {error}")
            return None
    return None


def obtener_desglose_mejor_solucion(dir_resultados: str, escala: str) -> dict | None:
    """Extrae las penalizaciones blandas unitarias de la mejor solución para una escala."""
    ruta_csv = os.path.join(dir_resultados, f"resultados_{escala}.csv")
    if not os.path.exists(ruta_csv):
        return None
    try:
        df = pd.read_csv(ruta_csv)
        if df.empty or "Z" not in df.columns:
            return None
        df_factibles = df[df["factible"]] if "factible" in df.columns else df
        if df_factibles.empty:
            df_factibles = df
        mejor_fila = df_factibles.sort_values(by="Z").iloc[0]
        return {
            "Z": mejor_fila.get("Z"),
            "alm": int(mejor_fila.get("penalizacion_almuerzo", 0)),
            "esp": int(mejor_fila.get("penalizacion_espaciado", 0)),
            "jue": int(mejor_fila.get("penalizacion_jueves", 0)),
            "sab": int(mejor_fila.get("penalizacion_sabado", 0)),
            "vent": int(mejor_fila.get("penalizacion_ventanas", 0)),
        }
    except Exception:
        return None


def sincronizar_resultados_experimentales_md(filas_por_escala: dict):
    """Actualiza las tablas de escala pequeña en docs/resultados_experimentales.md."""
    ruta_documento = os.path.join("docs", "resultados_experimentales.md")
    if not os.path.exists(ruta_documento):
        return

    with open(ruta_documento, "r", encoding="utf-8") as archivo:
        contenido = archivo.read()

    marcador_inicio = "## 2. Comparativa Benchmark en Escala Pequeña"
    marcador_fin = "## 4. Cumplimiento de Restricciones Duras ($HCV$)"

    if marcador_inicio not in contenido or marcador_fin not in contenido:
        return

    bloque_previo = contenido.split(marcador_inicio)[0]
    bloque_posterior = contenido.split(marcador_fin)[1]

    bloque_seccion_2 = [
        "## 2. Comparativa Benchmark en Escala Pequeña\n\n"
    ]

    configuracion_variantes = [
        ("pequena_s1", 1, "2.1"),
        ("pequena_s2", 2, "2.2"),
        ("pequena_s3", 3, "2.3"),
    ]

    for clave_escala, semilla, seccion_numero in configuracion_variantes:
        if clave_escala not in filas_por_escala:
            continue
        dimensiones = obtener_dimensiones_instancia(clave_escala)
        titulo_variante = (
            f"Variante {semilla} (`{clave_escala}`): Semilla {semilla} "
            f"($|E|={dimensiones['eventos']}$ eventos, $|R|={dimensiones['salones']}$ salones, "
            f"$|S|={dimensiones['secciones']}$ secciones, $|P|={dimensiones['profesores']}$ profesores)"
        )
        filas = filas_por_escala[clave_escala]
        bloque_seccion_2.append(f"### {seccion_numero}. {titulo_variante}\n\n")
        bloque_seccion_2.append(
            "| Método | SR (%) | DF (Mejor / Prom) | $Z$ Mejor | $Z$ Promedio ± Std | RPD (%) | CPU (s) | TTF (s) | Esfuerzo (NFE / Nodos) |\n"
        )
        bloque_seccion_2.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n")
        for fila in filas:
            z_mejor_str = f"**{fila['z_mejor']:.1f}**" if fila["z_mejor"] is not None else "N/A"
            z_prom_str = (
                f"**{fila['z_prom']:.2f} ± {fila['z_std']:.2f}**"
                if fila["tipo"] == "Exacto" and fila["z_prom"] is not None
                else (f"{fila['z_prom']:.2f} ± {fila['z_std']:.2f}" if fila["z_prom"] is not None else "N/A")
            )
            df_prom_val = fila["df_prom"]
            if isinstance(df_prom_val, (int, float)):
                df_str = f"{fila['df_mejor']} / {df_prom_val:.1f}"
            else:
                df_str = str(fila["df_mejor"])
            if fila["df_mejor"] == 0:
                df_str = f"**{df_str}**"

            sr_str = f"**{fila['tasa_exito']:.1f}%**" if fila["tasa_exito"] == 100.0 else f"{fila['tasa_exito']:.1f}%"
            cpu_str = f"{fila['cpu']:.2f}" if fila["cpu"] is not None else "N/A"
            ttf_str = f"{fila['ttf']:.2f}" if fila["ttf"] is not None else "N/A"
            metodo_corto = fila['metodo'].split(' (')[0]
            bloque_seccion_2.append(
                f"| **{metodo_corto}** | {sr_str} | {df_str} | {z_mejor_str} | {z_prom_str} | **{fila['rpd_cadena']}** | {cpu_str} | {ttf_str} | {fila['esfuerzo']} |\n"
            )
        bloque_seccion_2.append("\n---\n\n")

    if "pequena" in filas_por_escala:
        filas_pequena = filas_por_escala["pequena"]
        bloque_seccion_2.append("### 2.4. Resumen Consolidado Agregado (Escala Pequeña - 3 Variantes)\n\n")
        bloque_seccion_2.append(
            "| Método | SR (%) | DF (Mejor / Prom) | $Z$ Mejor Global | $Z$ Promedio ± Std | RPD (%) | CPU Prom (s) | TTF Prom (s) | Esfuerzo Medio |\n"
        )
        bloque_seccion_2.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n")
        for fila in filas_pequena:
            z_mejor_str = f"**{fila['z_mejor']:.1f}**" if fila["z_mejor"] is not None else "N/A"
            z_prom_str = (
                f"**{fila['z_prom']:.2f} ± {fila['z_std']:.2f}**"
                if fila["tipo"] == "Exacto" and fila["z_prom"] is not None
                else (f"{fila['z_prom']:.2f} ± {fila['z_std']:.2f}" if fila["z_prom"] is not None else "N/A")
            )
            df_prom_val = fila["df_prom"]
            if isinstance(df_prom_val, (int, float)):
                df_str = f"{fila['df_mejor']} / {df_prom_val:.1f}"
            else:
                df_str = str(fila["df_mejor"])
            if fila["df_mejor"] == 0:
                df_str = f"**{df_str}**"

            sr_str = f"**{fila['tasa_exito']:.1f}%**" if fila["tasa_exito"] == 100.0 else f"{fila['tasa_exito']:.1f}%"
            cpu_str = f"{fila['cpu']:.2f}" if fila["cpu"] is not None else "N/A"
            ttf_str = f"{fila['ttf']:.2f}" if fila["ttf"] is not None else "N/A"
            metodo_corto = fila['metodo'].split(' (')[0]
            bloque_seccion_2.append(
                f"| **{metodo_corto}** | {sr_str} | {df_str} | {z_mejor_str} | {z_prom_str} | **{fila['rpd_cadena']}** | {cpu_str} | {ttf_str} | {fila['esfuerzo']} |\n"
            )
        bloque_seccion_2.append("\n---\n\n")

    bloque_seccion_3 = [
        "## 3. Desglose de Penalizaciones Blandas en la Mejor Solución\n\n",
        "| Variante | Método | $P_{\\text{alm}}$ ($W_A=1$) | $P_{\\text{esp}}$ ($W_E=10$) | $P_{\\text{jue}}$ ($W_{\\text{jue}}=1$) | $P_{\\text{sab}}$ ($W_{\\text{sab}}=3$) | $P_{\\text{vent}}$ ($W_V=2$) | **Costo Total $Z$** |\n",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n",
    ]

    metodos_desglose = [
        ("MIP", "resultados_MIP"),
        ("HGA", "resultados_HGA"),
        ("TS", "resultados_TS"),
        ("SA", "resultados_SA"),
        ("GA", "resultados_GA"),
    ]

    for clave_escala, etiqueta_variante in [
        ("pequena_s1", "**Variante 1 ($s_1$)**"),
        ("pequena_s2", "**Variante 2 ($s_2$)**"),
        ("pequena_s3", "**Variante 3 ($s_3$)**"),
    ]:
        primera_fila = True
        for nombre_display, dir_metodo in metodos_desglose:
            desglose = obtener_desglose_mejor_solucion(dir_metodo, clave_escala)
            etiqueta_columna_variante = etiqueta_variante if primera_fila else ""
            primera_fila = False

            if desglose:
                z_total = f"**{desglose['Z']:.1f}**" if desglose["Z"] is not None else "N/A"
                bloque_seccion_3.append(
                    f"| {etiqueta_columna_variante} | **{nombre_display}** | **{desglose['alm']}** | **{desglose['esp']}** | **{desglose['jue']}** | **{desglose['sab']}** | **{desglose['vent']}** | {z_total} |\n"
                )
            else:
                bloque_seccion_3.append(
                    f"| {etiqueta_columna_variante} | **{nombre_display}** | N/A | N/A | N/A | N/A | N/A | N/A |\n"
                )

    bloque_seccion_3.append("\n---\n\n")

    meses_es = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]
    ahora = datetime.now()
    fecha_actual_legible = f"{ahora.day} de {meses_es[ahora.month - 1]} de {ahora.year}"
    lineas_previas = bloque_previo.splitlines(keepends=True)
    nuevas_lineas_previas = []
    for linea in lineas_previas:
        if linea.startswith("**Fecha de actualización:**"):
            nuevas_lineas_previas.append(f"**Fecha de actualización:** {fecha_actual_legible}  \n")
        else:
            nuevas_lineas_previas.append(linea)

    contenido_final = (
        "".join(nuevas_lineas_previas)
        + "".join(bloque_seccion_2)
        + "".join(bloque_seccion_3)
        + marcador_fin
        + bloque_posterior
    )

    with open(ruta_documento, "w", encoding="utf-8") as archivo:
        archivo.write(contenido_final)

    print(f"[ÉXITO] Documento de investigación sincronizado en: '{ruta_documento}'.")


def calcular_desviacion():
    """Genera la tabla comparativa de resultados y actualiza los reportes Markdown."""
    subvariantes_pequena = [
        variante for variante in ["pequena_s1", "pequena_s2", "pequena_s3"]
        if os.path.exists(os.path.join("resultados_HGA", f"resumen_{variante}.json"))
    ]
    escalas = subvariantes_pequena + ["pequena", "mediana", "grande"]

    metodos_metaheuristicas = [
        ("HGA", "resultados_HGA", "Algoritmo Genético Híbrido (MCF Memético)"),
        ("GA",  "resultados_GA",  "Algoritmo Genético Clásico"),
        ("TS",  "resultados_TS",  "Búsqueda Tabú (Discreta)"),
        ("SA",  "resultados_SA",  "Recocido Simulado (Discreto)"),
    ]

    print("\n" + "=" * 105)
    print(" CONSOLIDACIÓN DE RESULTADOS Y COMPARACIÓN BENCHMARK CB-CTT (MIP vs HGA, GA, TS, SA)")
    print("=" * 105)

    filas_por_escala: dict[str, list] = {}

    for escala in escalas:
        datos_mip = cargar_resumen("resultados_MIP", escala)
        costo_referencia_mip = None
        if datos_mip:
            costo_referencia_mip = datos_mip.get("mejor_z")

        filas_escala = []

        if datos_mip:
            tasa_exito = datos_mip.get("tasa_factibilidad_final", 0.0)
            mip_factible = (tasa_exito > 0.0)
            nodos = datos_mip.get("nodos_explorados_promedio", 0)
            cadena_nodos = f"{int(nodos):,} nodos" if nodos is not None else "N/A"
            tiempo_cpu = datos_mip.get("tiempo_cpu_promedio")
            tiempo_a_factibilidad = datos_mip.get("TTF_promedio")
            mejor_z = costo_referencia_mip
            promedio_z = datos_mip.get("promedio_z", costo_referencia_mip)
            desviacion_z = datos_mip.get("desviacion_z", 0.0)
            mejor_distancia = datos_mip.get("mejor_df", 0 if mip_factible else "N/A")
            promedio_distancia = datos_mip.get("promedio_df", 0.0 if mip_factible else "N/A")

            filas_escala.append({
                "metodo": "MIP (HiGHS)",
                "tipo": "Exacto",
                "tasa_exito": tasa_exito,
                "df_mejor": mejor_distancia,
                "df_prom": promedio_distancia,
                "z_mejor": mejor_z,
                "z_prom": promedio_z,
                "z_std": desviacion_z,
                "rpd": 0.0,
                "rpd_cadena": "0.00% (Ref)",
                "ttf": tiempo_a_factibilidad,
                "cpu": tiempo_cpu,
                "esfuerzo": cadena_nodos,
            })

        for codigo_metodo, dir_resultados, nombre_completo in metodos_metaheuristicas:
            datos_meta = cargar_resumen(dir_resultados, escala)
            if datos_meta:
                mejor_z = datos_meta.get("mejor_z")
                promedio_z = datos_meta.get("promedio_z")
                desviacion_z = datos_meta.get("desviacion_z", 0.0)
                tasa_exito = datos_meta.get("tasa_factibilidad_final", 0.0)
                mejor_distancia = datos_meta.get("mejor_df", "N/A")
                promedio_distancia = datos_meta.get("promedio_df", "N/A")
                tiempo_a_factibilidad = datos_meta.get("TTF_promedio")
                tiempo_cpu = datos_meta.get("tiempo_cpu_promedio")
                evaluaciones = datos_meta.get("evaluaciones_aptitud_promedio")
                cadena_evaluaciones = f"{int(evaluaciones):,} evals" if evaluaciones is not None else "N/A"

                valor_desviacion = None
                cadena_desviacion = "N/A"
                if costo_referencia_mip is not None and mejor_z is not None:
                    if costo_referencia_mip == 0:
                        if mejor_z == 0:
                            valor_desviacion = 0.0
                            cadena_desviacion = "0.00% (dZ=0)"
                        else:
                            valor_desviacion = ((mejor_z - costo_referencia_mip) / (costo_referencia_mip + 1.0)) * 100.0
                            cadena_desviacion = f"+{valor_desviacion:.1f}% (dZ={mejor_z - costo_referencia_mip:.0f})"
                    else:
                        valor_desviacion = ((mejor_z - costo_referencia_mip) / costo_referencia_mip) * 100.0
                        cadena_desviacion = f"{valor_desviacion:+.2f}%"

                filas_escala.append({
                    "metodo": f"{codigo_metodo} ({nombre_completo})",
                    "tipo": "Metaheurística",
                    "tasa_exito": tasa_exito,
                    "df_mejor": mejor_distancia,
                    "df_prom": promedio_distancia,
                    "z_mejor": mejor_z,
                    "z_prom": promedio_z,
                    "z_std": desviacion_z,
                    "rpd": valor_desviacion,
                    "rpd_cadena": cadena_desviacion,
                    "ttf": tiempo_a_factibilidad,
                    "cpu": tiempo_cpu,
                    "esfuerzo": cadena_evaluaciones,
                })

        if not filas_escala:
            continue

        filas_por_escala[escala] = filas_escala

        print(f"\n>>> INSTANCIA: {escala.upper()} (Z_ref MIP = {costo_referencia_mip if costo_referencia_mip is not None else 'N/D'})")
        print(f"{'Metodo':<22} | {'SR (%)':<7} | {'DF (Mej/Prom)':<14} | {'Z (Mejor)':<10} | {'Z (Prom +/- Std)':<17} | {'RPD (%)':<16} | {'CPU (s)':<9} | {'TTF (s)':<8} | {'NFE / Nodos':<12}")
        print("-" * 125)

        for fila in filas_escala:
            cadena_z_mejor = f"{fila['z_mejor']:.1f}" if fila['z_mejor'] is not None else "N/A"
            cadena_z_prom = (
                f"{fila['z_prom']:.1f} +/- {fila['z_std']:.1f}"
                if (fila['z_prom'] is not None and fila['z_std'] is not None)
                else "N/A"
            )
            cadena_df = (
                f"{fila['df_mejor']} / {fila['df_prom']:.1f}"
                if (fila['df_prom'] != "N/A" and isinstance(fila['df_prom'], (int, float)))
                else str(fila['df_mejor'])
            )
            cadena_cpu = f"{fila['cpu']:.2f}" if fila['cpu'] is not None else "N/A"
            cadena_ttf = f"{fila['ttf']:.2f}" if fila['ttf'] is not None else "N/A"

            print(
                f"{fila['metodo'][:22]:<22} | {fila['tasa_exito']:>6.1f}% | {cadena_df:<14} | {cadena_z_mejor:>10} | {cadena_z_prom:<17} | {fila['rpd_cadena']:<16} | {cadena_cpu:>9} | {cadena_ttf:>8} | {fila['esfuerzo']:<12}"
            )

    sincronizar_resultados_experimentales_md(filas_por_escala)


if __name__ == "__main__":
    calcular_desviacion()
