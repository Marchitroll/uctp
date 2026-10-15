# Comparación Consolidada de Métodos CB-CTT

**Fecha de última actualización:** 15/10/2026 01:28

Este reporte consolida el rendimiento del modelo exacto (**MIP**) y las 4 metaheurísticas implementadas (**HGA**, **GA**, **TS**, **SA**) para la asignación de horarios en la Universidad.
Se evalúan las métricas formales de la literatura (*Abdipoor et al. 2025; Rohaizad et al. 2026; Bashab et al. 2023*): Distancia a la Factibilidad ($DF$), Tasa de Éxito ($SR$), Penalización Blanda ($Z$), Desviación Relativa Porcentual ($RPD$), Tiempo a la Factibilidad ($TTF$), Tiempo CPU y Evaluaciones de Aptitud ($NFE$) / Nodos B&B.

## Instancia Pequeña - Variante 1 (Semilla 1: 23 eventos)

> [!NOTE]
> Evaluación formal completa de los 5 métodos (`MIP`, `HGA`, `GA`, `TS`, `SA`) en la primera variante de escala pequeña (23 eventos, semilla 1).

| Método | Tasa Éxito (SR %) | DF (Mejor / Prom) | $Z$ Mejor | $Z$ Promedio ± Std | RPD (%) | CPU (s) | TTF (s) | Esfuerzo (NFE / Nodos) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| MIP (HiGHS) | 100.0% | 0 / 0.0 | **68338.0** | 68338.00 ± 0.00 | 0.00% (Ref) | 42.89 | 42.89 | 0 nodos |
| HGA (Algoritmo Genético Híbrido (MCF Memético)) | 100.0% | 0 / 0.0 | **68.0** | 68.00 ± 0.00 | -99.90% | 0.36 | 0.12 | 300 evals |
| GA (Algoritmo Genético Clásico) | 0.0% | 3 / 3.0 | N/A | N/A | N/A | 0.16 | N/A | 300 evals |
| TS (Búsqueda Tabú (Discreta)) | 0.0% | 2 / 2.0 | N/A | N/A | N/A | 0.05 | N/A | 102 evals |
| SA (Recocido Simulado (Discreto)) | 0.0% | 4 / 4.0 | N/A | N/A | N/A | 0.06 | N/A | 52 evals |

## Instancia Pequeña - Variante 2 (Semilla 2: 18 eventos)

> [!NOTE]
> Evaluación formal completa de los 5 métodos (`MIP`, `HGA`, `GA`, `TS`, `SA`) en la segunda variante de escala pequeña (18 eventos, semilla 2).

| Método | Tasa Éxito (SR %) | DF (Mejor / Prom) | $Z$ Mejor | $Z$ Promedio ± Std | RPD (%) | CPU (s) | TTF (s) | Esfuerzo (NFE / Nodos) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| MIP (HiGHS) | 0.0% | N/A | N/A | N/A | 0.00% (Ref) | N/A | N/A | 0 nodos |
| HGA (Algoritmo Genético Híbrido (MCF Memético)) | 100.0% | 0 / 0.0 | **9.0** | 13.40 ± 4.06 | N/A | N/A | N/A | 2,850 evals |
| GA (Algoritmo Genético Clásico) | 100.0% | 0 / 0.0 | **11.0** | 29.33 ± 9.66 | N/A | N/A | N/A | 3,408 evals |
| TS (Búsqueda Tabú (Discreta)) | 100.0% | 0 / 0.0 | **7.0** | 16.67 ± 5.95 | N/A | N/A | N/A | 5,369 evals |
| SA (Recocido Simulado (Discreto)) | 100.0% | 0 / 0.0 | **13.0** | 29.97 ± 9.45 | N/A | N/A | N/A | 1,196 evals |

## Instancia Pequeña - Variante 3 (Semilla 3: 26 eventos)

> [!NOTE]
> Evaluación formal completa de los 5 métodos (`MIP`, `HGA`, `GA`, `TS`, `SA`) en la tercera variante de escala pequeña (26 eventos, semilla 3).

| Método | Tasa Éxito (SR %) | DF (Mejor / Prom) | $Z$ Mejor | $Z$ Promedio ± Std | RPD (%) | CPU (s) | TTF (s) | Esfuerzo (NFE / Nodos) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| MIP (HiGHS) | 0.0% | N/A | N/A | N/A | 0.00% (Ref) | N/A | N/A | 0 nodos |
| HGA (Algoritmo Genético Híbrido (MCF Memético)) | 100.0% | 0 / 0.0 | **22.0** | 30.27 ± 5.69 | N/A | N/A | N/A | 3,516 evals |
| GA (Algoritmo Genético Clásico) | 100.0% | 0 / 0.0 | **47.0** | 65.73 ± 15.32 | N/A | N/A | N/A | 6,161 evals |
| TS (Búsqueda Tabú (Discreta)) | 100.0% | 0 / 0.0 | **30.0** | 59.13 ± 11.43 | N/A | N/A | N/A | 6,008 evals |
| SA (Recocido Simulado (Discreto)) | 100.0% | 0 / 0.0 | **35.0** | 66.63 ± 15.49 | N/A | N/A | N/A | 1,860 evals |

## Instancia Pequeña - Resumen Consolidado Agregado (Promedio 3 Variantes)

> [!NOTE]
> Rendimiento promedio global acumulado sobre las 3 instancias semi-sintéticas de escala pequeña (90 réplicas por metaheurística y 3 corridas de MIP).

| Método | Tasa Éxito (SR %) | DF (Mejor / Prom) | $Z$ Mejor | $Z$ Promedio ± Std | RPD (%) | CPU (s) | TTF (s) | Esfuerzo (NFE / Nodos) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| MIP (HiGHS) | 100.0% | 0 / 0.0 | **68338.0** | 68338.00 ± 0.00 | 0.00% (Ref) | 42.89 | 42.89 | 0 nodos |
| HGA (Algoritmo Genético Híbrido (MCF Memético)) | 100.0% | 0 / 0.0 | **68.0** | 68.00 ± 0.00 | -99.90% | 0.36 | 0.12 | 300 evals |
| GA (Algoritmo Genético Clásico) | 0.0% | 3 / 3.0 | N/A | N/A | N/A | 0.16 | N/A | 300 evals |
| TS (Búsqueda Tabú (Discreta)) | 0.0% | 2 / 2.0 | N/A | N/A | N/A | 0.05 | N/A | 102 evals |
| SA (Recocido Simulado (Discreto)) | 0.0% | 4 / 4.0 | N/A | N/A | N/A | 0.06 | N/A | 52 evals |

## Instancia Mediana

> [!NOTE]
> Registro experimental preliminar correspondiente a la fase de calibración baseline (Fase 2 de escalabilidad).

| Método | Tasa Éxito (SR %) | DF (Mejor / Prom) | $Z$ Mejor | $Z$ Promedio ± Std | RPD (%) | CPU (s) | TTF (s) | Esfuerzo (NFE / Nodos) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| MIP (HiGHS) | 0.0% | N/A | N/A | N/A | 0.00% (Ref) | N/A | N/A | 0 nodos |
| GA (Algoritmo Genético Clásico) | 100.0% | N/A | **457.0** | 540.47 ± 29.75 | N/A | N/A | N/A | 3,576 evals |

## Instancia Grande

> [!NOTE]
> Registro experimental preliminar correspondiente a la fase de calibración baseline (Fase 2 de escalabilidad).

| Método | Tasa Éxito (SR %) | DF (Mejor / Prom) | $Z$ Mejor | $Z$ Promedio ± Std | RPD (%) | CPU (s) | TTF (s) | Esfuerzo (NFE / Nodos) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| MIP (HiGHS) | 0.0% | N/A | N/A | N/A | 0.00% (Ref) | N/A | N/A | 0 nodos |
| GA (Algoritmo Genético Clásico) | 100.0% | N/A | **928.0** | 1050.07 ± 66.56 | N/A | N/A | N/A | 7,960 evals |

## Especificaciones del Entorno Experimental

Para garantizar reproducibilidad científica conforme a *Rohaizad et al. (2026)* y *Bashab et al. (2023)*, se auditan las características de la plataforma de cómputo:

| Parámetro | Valor Registrado |
| :--- | :--- |
| **Sistema Operativo** | Windows 11 |
| **Procesador (CPU)** | Intel64 Family 6 Model 151 Stepping 2, GenuineIntel |
| **Memoria RAM Total** | 15.83 GB |
| **Versión Python** | 3.13.15 |
| **Versión Python-MIP / HiGHS** | 2.0.0 |
| **Versión MEALPY** | 3.0.2 |

## Definiciones de Métricas

1. **$SR$ (Success Rate / Tasa de Éxito %)**: Porcentaje de corridas independientes que convergieron a un horario estrictamente factible ($HCV = 0$).
2. **$DF$ (Distance to Feasibility)**: Número de violaciones a restricciones duras ($HCV$). Para soluciones factibles, $DF = 0$.
3. **$Z$ (Función Objetivo Blanda)**: Suma ponderada de penalizaciones:
   $$\min Z = 1 \cdot P_{\text{almuerzo}} + 10 \cdot P_{\text{espaciado}} + 1 \cdot P_{\text{jueves}} + 3 \cdot P_{\text{sabado}} + 2 \cdot P_{\text{ventanas}}$$
4. **$RPD$ (Relative Percentage Deviation)**: Desviación respecto al óptimo MIP ($Z_{\text{ref}}$):
   - Si $Z_{\text{ref}} > 0$: $RPD = \frac{Z_{\text{alg}} - Z_{\text{ref}}}{Z_{\text{ref}}} \times 100$
   - Si $Z_{\text{ref}} = 0$: $RPD = \frac{Z_{\text{alg}} - Z_{\text{ref}}}{Z_{\text{ref}} + 1} \times 100$ con reporte explícito de $\Delta Z = Z_{\text{alg}} - Z_{\text{ref}}$.
5. **$TTF$ (Time to Feasibility)**: Tiempo transcurrido (en segundos de CPU) hasta encontrar por primera vez una solución con $HCV = 0$.
6. **$NFE$ (Number of Function Evaluations)**: Número total de soluciones evaluadas por el algoritmo a lo largo de la búsqueda.
