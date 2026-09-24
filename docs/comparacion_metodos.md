# Comparación Consolidada de Métodos CB-CTT
Este reporte consolida el rendimiento del modelo exacto (**MIP**) y las 4 metaheurísticas implementadas (**HGA**, **GA**, **TS**, **SA**) para la asignación de horarios en la Universidad.
Se evalúan las métricas formales de la literatura (*Abdipoor et al. 2025; Rohaizad et al. 2026; Bashab et al. 2023*): Distancia a la Factibilidad ($DF$), Tasa de Éxito ($SR$), Penalización Blanda ($Z$), Desviación Relativa Porcentual ($RPD$), Tiempo a la Factibilidad ($TTF$), Tiempo CPU y Evaluaciones de Aptitud ($NFE$) / Nodos B&B.

## Instancia Pequena

> [!NOTE]
> Evaluación formal completa de los 5 métodos (`MIP`, `HGA`, `GA`, `TS`, `SA`) incorporando las cuatro restricciones blandas institucionales y la reducción de dominio `valid_starts`.

| Método | Tasa Éxito (SR %) | DF (Mejor / Prom) | $Z$ Mejor | $Z$ Promedio ± Std | RPD (%) | CPU (s) | TTF (s) | Esfuerzo (NFE / Nodos) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| MIP (HiGHS) | 100.0% | 0 / 0.0 | **102457.0** | 102457.00 ± 0.00 | 0.00% (Ref) | 213.25 | 213.25 | 0 nodos |
| HGA (Algoritmo Genético Híbrido (MCF Memético)) | 100.0% | 0 / 0.0 | **25.0** | 25.00 ± 0.00 | -99.98% | 9.59 | 0.20 | 5,000 evals |
| GA (Algoritmo Genético Clásico) | 100.0% | 0 / 0.0 | **91.0** | 91.00 ± 0.00 | -99.91% | 2.14 | 0.86 | 4,200 evals |
| TS (Búsqueda Tabú (Discreta)) | 100.0% | 0 / 0.0 | **87.0** | 87.00 ± 0.00 | -99.92% | 3.34 | 1.34 | 5,622 evals |
| SA (Recocido Simulado (Discreto)) | 100.0% | 0 / 0.0 | **48.0** | 48.00 ± 0.00 | -99.95% | 11.62 | 2.34 | 3,461 evals |

## Instancia Mediana

> [!NOTE]
> Registro experimental preliminar correspondiente a la fase de calibración baseline.

| Método | Tasa Éxito (SR %) | DF (Mejor / Prom) | $Z$ Mejor | $Z$ Promedio ± Std | RPD (%) | CPU (s) | TTF (s) | Esfuerzo (NFE / Nodos) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| MIP (HiGHS) | 100.0% | 0 / 0.0 | **434144.0** | 434144.00 ± 0.00 | 0.00% (Ref) | 7874.11 | 7874.11 | 0 nodos |
| GA (Algoritmo Genético Clásico) | 100.0% | N/A | **457.0** | 540.47 ± 29.75 | -99.89% | 119.16 | 26.38 | 3,576 evals |

## Instancia Grande

> [!NOTE]
> Registro experimental preliminar correspondiente a la fase de calibración baseline.

| Método | Tasa Éxito (SR %) | DF (Mejor / Prom) | $Z$ Mejor | $Z$ Promedio ± Std | RPD (%) | CPU (s) | TTF (s) | Esfuerzo (NFE / Nodos) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| MIP (HiGHS) | 100.0% | 0 / 0.0 | **3927356.0** | 3927356.00 ± 0.00 | 0.00% (Ref) | 13935.66 | 13935.66 | 0 nodos |
| GA (Algoritmo Genético Clásico) | 100.0% | N/A | **928.0** | 1050.07 ± 66.56 | -99.98% | 1839.98 | 752.16 | 7,960 evals |

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
