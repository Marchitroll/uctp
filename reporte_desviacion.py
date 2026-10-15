from datetime import datetime
import json
import os


def cargar_resumen(dir_metodo, escala):
    path = os.path.join(dir_metodo, f"resumen_{escala}.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Error al leer {path}: {e}")
            return None
    return None


def calcular_desviacion():
    sub_pequena = [
        s for s in ["pequena_s1", "pequena_s2", "pequena_s3"]
        if os.path.exists(os.path.join("resultados_HGA", f"resumen_{s}.json"))
    ]
    escalas = sub_pequena + ["pequena", "mediana", "grande"]

    metodos_meta = [
        ("HGA", "resultados_HGA", "Algoritmo Genético Híbrido (MCF Memético)"),
        ("GA",  "resultados_GA",  "Algoritmo Genético Clásico"),
        ("TS",  "resultados_TS",  "Búsqueda Tabú (Discreta)"),
        ("SA",  "resultados_SA",  "Recocido Simulado (Discreto)")
    ]

    print("\n" + "=" * 105)
    print(" CONSOLIDACIÓN DE RESULTADOS Y COMPARACIÓN BENCHMARK CB-CTT (MIP vs HGA, GA, TS, SA)")
    print("=" * 105)

    reporte_md_lineas = []
    reporte_md_lineas.append("# Comparación Consolidada de Métodos CB-CTT\n\n")
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
    reporte_md_lineas.append(f"**Fecha de última actualización:** {fecha_actual}\n\n")
    reporte_md_lineas.append("Este reporte consolida el rendimiento del modelo exacto (**MIP**) y las 4 metaheurísticas implementadas (**HGA**, **GA**, **TS**, **SA**) para la asignación de horarios en la Universidad.\n")
    reporte_md_lineas.append("Se evalúan las métricas formales de la literatura (*Abdipoor et al. 2025; Rohaizad et al. 2026; Bashab et al. 2023*): Distancia a la Factibilidad ($DF$), Tasa de Éxito ($SR$), Penalización Blanda ($Z$), Desviación Relativa Porcentual ($RPD$), Tiempo a la Factibilidad ($TTF$), Tiempo CPU y Evaluaciones de Aptitud ($NFE$) / Nodos B&B.\n\n")

    for escala in escalas:
        mip_data = cargar_resumen("resultados_MIP", escala)
        z_ref = None
        if mip_data:
            z_ref = mip_data.get("mejor_z")

        filas_escala = []

        # 1. Procesar MIP
        if mip_data:
            sr = mip_data.get("tasa_factibilidad_final", 0.0)
            mip_factible = (sr > 0.0)
            nodos = mip_data.get("nodos_explorados_promedio", 0)
            nodos_str = f"{int(nodos):,} nodos" if nodos is not None else "N/A"
            cpu_val = mip_data.get("tiempo_cpu_promedio")
            ttf_val = mip_data.get("TTF_promedio")
            z_m = z_ref
            z_p = mip_data.get("promedio_z", z_ref)
            z_s = mip_data.get("desviacion_z", 0.0)
            df_m = mip_data.get("mejor_df", 0 if mip_factible else "N/A")
            df_p = mip_data.get("promedio_df", 0.0 if mip_factible else "N/A")

            filas_escala.append({
                "metodo": "MIP (HiGHS)",
                "tipo": "Exacto",
                "sr": sr,
                "df_mejor": df_m,
                "df_prom": df_p,
                "z_mejor": z_m,
                "z_prom": z_p,
                "z_std": z_s,
                "rpd": 0.0,
                "rpd_str": "0.00% (Ref)",
                "ttf": ttf_val,
                "cpu": cpu_val,
                "nfe_nodos": nodos_str,
            })

        # 2. Procesar Metaheurísticas
        for code, dir_m, nombre_completo in metodos_meta:
            m_data = cargar_resumen(dir_m, escala)
            if m_data:
                z_m = m_data.get("mejor_z")
                z_p = m_data.get("promedio_z")
                z_std = m_data.get("desviacion_z", 0.0)
                sr = m_data.get("tasa_factibilidad_final", 0.0)
                df_m = m_data.get("mejor_df", "N/A")
                df_p = m_data.get("promedio_df", "N/A")
                ttf = m_data.get("TTF_promedio")
                cpu = m_data.get("tiempo_cpu_promedio")
                nfe = m_data.get("evaluaciones_aptitud_promedio")
                nfe_str = f"{int(nfe):,} evals" if nfe is not None else "N/A"

                rpd_val = None
                rpd_str = "N/A"
                if z_ref is not None and z_m is not None:
                    if z_ref == 0:
                        if z_m == 0:
                            rpd_val = 0.0
                            rpd_str = "0.00% (dZ=0)"
                        else:
                            rpd_val = ((z_m - z_ref) / (z_ref + 1.0)) * 100.0
                            rpd_str = f"+{rpd_val:.1f}% (dZ={z_m - z_ref:.0f})"
                    else:
                        rpd_val = ((z_m - z_ref) / z_ref) * 100.0
                        rpd_str = f"{rpd_val:+.2f}%"

                filas_escala.append({
                    "metodo": f"{code} ({nombre_completo})",
                    "tipo": "Metaheurística",
                    "sr": sr,
                    "df_mejor": df_m,
                    "df_prom": df_p,
                    "z_mejor": z_m,
                    "z_prom": z_p,
                    "z_std": z_std,
                    "rpd": rpd_val,
                    "rpd_str": rpd_str,
                    "ttf": ttf,
                    "cpu": cpu,
                    "nfe_nodos": nfe_str,
                })

        if not filas_escala:
            continue

        print(f"\n>>> INSTANCIA: {escala.upper()} (Z_ref MIP = {z_ref if z_ref is not None else 'N/D'})")
        print(f"{'Metodo':<22} | {'SR (%)':<7} | {'DF (Mej/Prom)':<14} | {'Z (Mejor)':<10} | {'Z (Prom +/- Std)':<17} | {'RPD (%)':<16} | {'CPU (s)':<9} | {'TTF (s)':<8} | {'NFE / Nodos':<12}")
        print("-" * 125)

        for f in filas_escala:
            z_m_str = f"{f['z_mejor']:.1f}" if f['z_mejor'] is not None else "N/A"
            z_p_str = f"{f['z_prom']:.1f} +/- {f['z_std']:.1f}" if (f['z_prom'] is not None and f['z_std'] is not None) else "N/A"
            df_str = f"{f['df_mejor']} / {f['df_prom']:.1f}" if (f['df_prom'] != "N/A" and isinstance(f['df_prom'], (int, float))) else str(f['df_mejor'])
            cpu_str = f"{f['cpu']:.2f}" if f['cpu'] is not None else "N/A"
            ttf_str = f"{f['ttf']:.2f}" if f['ttf'] is not None else "N/A"

            print(f"{f['metodo'][:22]:<22} | {f['sr']:>6.1f}% | {df_str:<14} | {z_m_str:>10} | {z_p_str:<17} | {f['rpd_str']:<16} | {cpu_str:>9} | {ttf_str:>8} | {f['nfe_nodos']:<12}")

        # Título y nota según escala
        if escala == "pequena_s1":
            titulo = "Instancia Pequeña - Variante 1 (Semilla 1: 23 eventos)"
            nota = "> [!NOTE]\n> Evaluación formal completa de los 5 métodos (`MIP`, `HGA`, `GA`, `TS`, `SA`) en la primera variante de escala pequeña (23 eventos, semilla 1).\n\n"
        elif escala == "pequena_s2":
            titulo = "Instancia Pequeña - Variante 2 (Semilla 2: 18 eventos)"
            nota = "> [!NOTE]\n> Evaluación formal completa de los 5 métodos (`MIP`, `HGA`, `GA`, `TS`, `SA`) en la segunda variante de escala pequeña (18 eventos, semilla 2).\n\n"
        elif escala == "pequena_s3":
            titulo = "Instancia Pequeña - Variante 3 (Semilla 3: 26 eventos)"
            nota = "> [!NOTE]\n> Evaluación formal completa de los 5 métodos (`MIP`, `HGA`, `GA`, `TS`, `SA`) en la tercera variante de escala pequeña (26 eventos, semilla 3).\n\n"
        elif escala == "pequena":
            titulo = "Instancia Pequeña - Resumen Consolidado Agregado (Promedio 3 Variantes)"
            nota = "> [!NOTE]\n> Rendimiento promedio global acumulado sobre las 3 instancias semi-sintéticas de escala pequeña (90 réplicas por metaheurística y 3 corridas de MIP).\n\n"
        elif escala == "mediana":
            titulo = "Instancia Mediana"
            nota = "> [!NOTE]\n> Registro experimental preliminar correspondiente a la fase de calibración baseline (Fase 2 de escalabilidad).\n\n"
        else:
            titulo = "Instancia Grande"
            nota = "> [!NOTE]\n> Registro experimental preliminar correspondiente a la fase de calibración baseline (Fase 2 de escalabilidad).\n\n"

        reporte_md_lineas.append(f"## {titulo}\n\n")
        reporte_md_lineas.append(nota)
        reporte_md_lineas.append("| Método | Tasa Éxito (SR %) | DF (Mejor / Prom) | $Z$ Mejor | $Z$ Promedio ± Std | RPD (%) | CPU (s) | TTF (s) | Esfuerzo (NFE / Nodos) |\n")
        reporte_md_lineas.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n")

        for f in filas_escala:
            z_m_str = f"**{f['z_mejor']:.1f}**" if f['z_mejor'] is not None else "N/A"
            z_p_str = f"{f['z_prom']:.2f} ± {f['z_std']:.2f}" if (f['z_prom'] is not None and f['z_std'] is not None) else "N/A"
            df_str = f"{f['df_mejor']} / {f['df_prom']:.1f}" if (f['df_prom'] != "N/A" and isinstance(f['df_prom'], (int, float))) else str(f['df_mejor'])
            cpu_str = f"{f['cpu']:.2f}" if f['cpu'] is not None else "N/A"
            ttf_str = f"{f['ttf']:.2f}" if f['ttf'] is not None else "N/A"
            sr_str = f"{f['sr']:.1f}%"

            reporte_md_lineas.append(
                f"| {f['metodo']} | {sr_str} | {df_str} | {z_m_str} | {z_p_str} | {f['rpd_str']} | {cpu_str} | {ttf_str} | {f['nfe_nodos']} |\n"
            )
        reporte_md_lineas.append("\n")

    # Tabla de entorno de ejecución
    reporte_md_lineas.append("## Especificaciones del Entorno Experimental\n\n")
    reporte_md_lineas.append("Para garantizar reproducibilidad científica conforme a *Rohaizad et al. (2026)* y *Bashab et al. (2023)*, se auditan las características de la plataforma de cómputo:\n\n")

    entorno_ref = None
    for escala in ["pequena_s1", "pequena", "mediana", "grande"]:
        for d in ["resultados_MIP", "resultados_HGA", "resultados_GA", "resultados_TS", "resultados_SA"]:
            dat = cargar_resumen(d, escala)
            if dat and "entorno" in dat and dat["entorno"]:
                entorno_ref = dat["entorno"]
                break
        if entorno_ref:
            break

    if entorno_ref:
        reporte_md_lineas.append("| Parámetro | Valor Registrado |\n")
        reporte_md_lineas.append("| :--- | :--- |\n")
        reporte_md_lineas.append(f"| **Sistema Operativo** | {entorno_ref.get('sistema_operativo', 'N/A')} |\n")
        reporte_md_lineas.append(f"| **Procesador (CPU)** | {entorno_ref.get('procesador', 'N/A')} |\n")
        reporte_md_lineas.append(f"| **Memoria RAM Total** | {entorno_ref.get('ram_gb', 'N/A')} GB |\n")
        reporte_md_lineas.append(f"| **Versión Python** | {entorno_ref.get('version_python', 'N/A')} |\n")
        reporte_md_lineas.append(f"| **Versión Python-MIP / HiGHS** | {entorno_ref.get('version_mip', 'N/A')} |\n")
        reporte_md_lineas.append(f"| **Versión MEALPY** | {entorno_ref.get('version_mealpy', 'N/A')} |\n")
        reporte_md_lineas.append("\n")

    reporte_md_lineas.append("## Definiciones de Métricas\n\n")
    reporte_md_lineas.append("1. **$SR$ (Success Rate / Tasa de Éxito %)**: Porcentaje de corridas independientes que convergieron a un horario estrictamente factible ($HCV = 0$).\n")
    reporte_md_lineas.append("2. **$DF$ (Distance to Feasibility)**: Número de violaciones a restricciones duras ($HCV$). Para soluciones factibles, $DF = 0$.\n")
    reporte_md_lineas.append("3. **$Z$ (Función Objetivo Blanda)**: Suma ponderada de penalizaciones:\n")
    reporte_md_lineas.append("   $$\\min Z = 1 \\cdot P_{\\text{almuerzo}} + 10 \\cdot P_{\\text{espaciado}} + 1 \\cdot P_{\\text{jueves}} + 3 \\cdot P_{\\text{sabado}} + 2 \\cdot P_{\\text{ventanas}}$$\n")
    reporte_md_lineas.append("4. **$RPD$ (Relative Percentage Deviation)**: Desviación respecto al óptimo MIP ($Z_{\\text{ref}}$):\n")
    reporte_md_lineas.append("   - Si $Z_{\\text{ref}} > 0$: $RPD = \\frac{Z_{\\text{alg}} - Z_{\\text{ref}}}{Z_{\\text{ref}}} \\times 100$\n")
    reporte_md_lineas.append("   - Si $Z_{\\text{ref}} = 0$: $RPD = \\frac{Z_{\\text{alg}} - Z_{\\text{ref}}}{Z_{\\text{ref}} + 1} \\times 100$ con reporte explícito de $\\Delta Z = Z_{\\text{alg}} - Z_{\\text{ref}}$.\n")
    reporte_md_lineas.append("5. **$TTF$ (Time to Feasibility)**: Tiempo transcurrido (en segundos de CPU) hasta encontrar por primera vez una solución con $HCV = 0$.\n")
    reporte_md_lineas.append("6. **$NFE$ (Number of Function Evaluations)**: Número total de soluciones evaluadas por el algoritmo a lo largo de la búsqueda.\n")

    reporte_path = os.path.join("docs", "comparacion_metodos.md")
    os.makedirs("docs", exist_ok=True)
    with open(reporte_path, "w", encoding="utf-8") as f:
        f.writelines(reporte_md_lineas)

    print(f"\n[ÉXITO] Reporte comparativo Markdown actualizado en: '{reporte_path}'\n")


if __name__ == "__main__":
    calcular_desviacion()
