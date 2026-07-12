import os
import json
import math

def calcular_desviacion():
    escalas = ["pequena", "mediana", "grande"]
    resumen_mip_dir = "resultados_MIP"
    resumen_ga_dir = "resultados_GA"
    
    comparativa = []
    
    print("\n" + "="*80)
    print(" CÁLCULO DE DESVIACIÓN RELATIVA (GAP RELATIVO) - GA vs MIP")
    print("="*80)
    
    for escala in escalas:
        mip_path = os.path.join(resumen_mip_dir, f"resumen_{escala}.json")
        ga_path = os.path.join(resumen_ga_dir, f"resumen_{escala}.json")
        
        mip_exist = os.path.exists(mip_path)
        ga_exist = os.path.exists(ga_path)
        
        info = {
            "escala": escala,
            "mip_disponible": mip_exist,
            "ga_disponible": ga_exist,
            "z_mip": None,
            "z_ga_mejor": None,
            "z_ga_promedio": None,
            "dr_pct": None,
            "dr_status": "Sin datos",
            "cpu_mip": None,
            "cpu_ga_prom": None
        }
        
        if mip_exist and ga_exist:
            try:
                with open(mip_path, "r", encoding="utf-8") as f:
                    mip_data = json.load(f)
                with open(ga_path, "r", encoding="utf-8") as f:
                    ga_data = json.load(f)
                
                z_mip = mip_data.get("Z")
                z_ga_mejor = ga_data.get("mejor_z")
                z_ga_promedio = ga_data.get("promedio_z")
                
                info["z_mip"] = z_mip
                info["z_ga_mejor"] = z_ga_mejor
                info["z_ga_promedio"] = z_ga_promedio
                info["cpu_mip"] = mip_data.get("CPU_time")
                info["cpu_ga_prom"] = ga_data.get("cpu_promedio")
                
                if z_mip is not None and z_ga_mejor is not None:
                    if z_mip == 0:
                        if z_ga_mejor == 0:
                            dr = 0.0
                            info["dr_status"] = "0.00% (Ambos óptimos sin penalización)"
                        else:
                            dr = float('inf')
                            info["dr_status"] = "Indefinido (Z_MIP = 0)"
                    else:
                        dr = ((z_ga_mejor - z_mip) / z_mip) * 100
                        info["dr_status"] = f"{dr:+.2f}%"
                    info["dr_pct"] = dr
                else:
                    info["dr_status"] = "Datos incompletos"
            except Exception as e:
                info["dr_status"] = f"Error: {str(e)}"
        else:
            missing = []
            if not mip_exist: missing.append("MIP")
            if not ga_exist: missing.append("GA")
            info["dr_status"] = f"Faltan resultados de: {', '.join(missing)}"
            
        comparativa.append(info)

    # Imprimir en consola con formato
    print(f"{'Escala':<10} | {'Z_MIP':<10} | {'Z_GA (Mejor)':<15} | {'Z_GA (Prom)':<12} | {'Desviación (DR)':<20} | {'CPU MIP (s)':<12} | {'CPU GA (s)':<12}")
    print("-" * 103)
    for c in comparativa:
        z_mip_str = f"{c['z_mip']:.1f}" if c['z_mip'] is not None else "N/A"
        z_ga_m_str = f"{c['z_ga_mejor']:.1f}" if c['z_ga_mejor'] is not None else "N/A"
        z_ga_p_str = f"{c['z_ga_promedio']:.2f}" if c['z_ga_promedio'] is not None else "N/A"
        cpu_mip_str = f"{c['cpu_mip']:.2f}" if c['cpu_mip'] is not None else "N/A"
        cpu_ga_str = f"{c['cpu_ga_prom']:.2f}" if c['cpu_ga_prom'] is not None else "N/A"
        print(f"{c['escala'].capitalize():<10} | {z_mip_str:<10} | {z_ga_m_str:<15} | {z_ga_p_str:<12} | {c['dr_status']:<20} | {cpu_mip_str:<12} | {cpu_ga_str:<12}")
    
    print("="*80 + "\n")
    
    # Generar reporte Markdown
    report_path = os.path.join("docs", "comparacion_metodos.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Comparación de Rendimiento y Desviación Relativa\n\n")
        f.write("Este reporte compara el desempeño del Algoritmo Genético (GA) contra el modelo exacto de Programación Lineal Entera Mixta (MIP) para la planificación horaria de la UCTP.\n\n")
        
        f.write("## Tabla Comparativa\n\n")
        f.write("| Escala | $Z_{\\text{MIP}}$ | $Z_{\\text{AG}}$ (Mejor) | $Z_{\\text{AG}}$ (Promedio) | Desviación Relativa (DR %) | Tiempo CPU MIP (s) | Tiempo CPU GA (Prom, s) |\n")
        f.write("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")
        
        for c in comparativa:
            z_mip_str = f"{c['z_mip']:.1f}" if c['z_mip'] is not None else "N/A"
            z_ga_m_str = f"{c['z_ga_mejor']:.1f}" if c['z_ga_mejor'] is not None else "N/A"
            z_ga_p_str = f"{c['z_ga_promedio']:.2f}" if c['z_ga_promedio'] is not None else "N/A"
            cpu_mip_str = f"{c['cpu_mip']:.2f}" if c['cpu_mip'] is not None else "N/A"
            cpu_ga_str = f"{c['cpu_ga_prom']:.2f}" if c['cpu_ga_prom'] is not None else "N/A"
            
            # Formatear DR para markdown
            dr_md = c['dr_status']
            if c['dr_pct'] is not None and not math.isinf(c['dr_pct']):
                if c['dr_pct'] == 0.0:
                    dr_md = "**0.00%**"
                else:
                    dr_md = f"**{c['dr_pct']:+.2f}%**"
            
            f.write(f"| {c['escala'].capitalize()} | {z_mip_str} | {z_ga_m_str} | {z_ga_p_str} | {dr_md} | {cpu_mip_str} | {cpu_ga_str} |\n")
            
        f.write("\n")
        f.write("## Definiciones\n\n")
        f.write("* **$Z_{\\text{MIP}}$**: Penalización blanda total obtenida por el solucionador MIP (óptimo o mejor límite entero encontrado).\n")
        f.write("* **$Z_{\\text{AG}}$ (Mejor)**: La menor penalización blanda alcanzada por el Algoritmo Genético a lo largo de las 20 corridas.\n")
        f.write("* **Desviación Relativa (DR %)**: Medida porcentual de qué tan cerca estuvo la metaheurística del óptimo exacto, calculada como:\n")
        f.write("  $$\\text{DR } (\\%) = \\frac{Z_{\\text{AG}} - Z_{\\text{MIP}}}{Z_{\\text{MIP}}} \\times 100$$\n")
        f.write("  *Un valor de 0.00% indica que el GA encontró una solución con la misma calidad que el modelo exacto (óptima en este caso).* \n")
        
    print(f"Reporte exportado correctamente a: {report_path}")

if __name__ == "__main__":
    calcular_desviacion()
