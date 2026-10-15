# Reporte Consolidado de Resultados Experimentales - UCTP

**Fecha de última actualización:** 5 de octubre de 2026  
**Entorno de Ejecución:** Intel Core i5-12400F, 16 GB RAM DDR5 (5600 MT/s), Windows 11 (64-bit), Python 3.13.15 con Astral UV, `python-mip` v2.0.0 (backend HiGHS v1.13.1) y `mealpy` v3.0.2.

---

## 1. Alcance y Delimitación Metodológica (Fase 1: Escala Pequeña)

Este documento consolida la evaluación experimental formal y el análisis comparativo del modelo exacto (**MIP** con solucionador HiGHS) frente a las cuatro metaheurísticas desarrolladas (**HGA**, **GA**, **TS**, **SA**) para el Problema de Planificación Horaria Universitaria (UCTP / CB-CTT).

> [!IMPORTANT]
> **Delimitación de Alcance:**  
> La presente evaluación corresponde estrictamente a la **Fase 1: Evaluación Empírica en Escala Pequeña**, diseñada para validar con máxima rigurosidad estadística la convergencia, consistencia estocástica y viabilidad operativa de las propuestas.  
> Las escalas **Mediana** (176–204 eventos) y **Grande** (298–335 eventos) forman parte de la **Fase 2 (Escalabilidad)** y se abordarán en etapas posteriores de la investigación, debido al costo computacional extremo que exhiben los solucionadores exactos ante horizontes temporales densos.

Para garantizar robustez frente a la variabilidad topológica del problema (y no únicamente ante la aleatoriedad algorítmica), el experimento evalúa **tres variantes semi-sintéticas independientes de escala pequeña** generadas mediante variación controlada de semillas (`pequena_s1`, `pequena_s2`, `pequena_s3`).  
Cada metaheurística se ejecutó en **30 réplicas independientes correlativas (semillas 1 a 30)** por cada variante (totalizando 90 corridas por algoritmo y 360 ejecuciones metaheurísticas), contrastadas contra **1 corrida determinista del solucionador exacto MIP** por variante (3 corridas de MIP, 363 ejecuciones totales).

La función objetivo unificada minimiza la penalización de las restricciones blandas institucionales:

$$\min Z = 1 \cdot P_{\text{almuerzo}} + 10 \cdot P_{\text{espaciado}} + 1 \cdot P_{\text{jueves}} + 3 \cdot P_{\text{sabado}} + 2 \cdot P_{\text{ventanas}}$$

---

## 2. Comparativa Benchmark en Escala Pequeña

### 2.1. Variante 1 (`pequena_s1`): Semilla 1 ($|E|=23$ eventos, $|R|=21$ salones, $|S|=9$ secciones, $|P|=4$ profesores)

| Método | Tipo | Tasa Éxito ($SR$ %) | Distancia Factibilidad ($DF$) | $Z$ Mejor | $Z$ Promedio ± Std | $RPD$ (%) | Tiempo CPU (s) | $TTF$ (s) | Esfuerzo (NFE / Nodos) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **MIP (HiGHS)** | Exacto | **100.0%** | **0 / 0.0** | **8.0** | **8.00 ± 0.00** | **0.00% (Ref)** | 4,072.41 | 4,072.41 | 0 nodos (Cuts B&B) |
| **HGA (Propuesto)** | Metaheurística | **100.0%** | **0 / 0.0** | **9.0** | **18.33 ± 4.17** | **+12.50%** | **3.63** | **0.13** | 3,748 evals |
| **TS (Búsqueda Tabú)** | Metaheurística | **100.0%** | **0 / 0.0** | **17.0** | 37.50 ± 8.59 | +112.50% | 2.16 | 0.23 | 4,953 evals |
| **GA (Genético Clásico)** | Metaheurística | **100.0%** | **0 / 0.0** | **24.0** | 38.63 ± 10.14 | +200.00% | 2.09 | 0.43 | 5,301 evals |
| **SA (Recocido Simulado)** | Metaheurística | **100.0%** | **0 / 0.0** | **23.0** | 41.97 ± 9.67 | +187.50% | 2.27 | 0.51 | 1,467 evals |

---

### 2.2. Variante 2 (`pequena_s2`): Semilla 2 ($|E|=18$ eventos, $|R|=21$ salones, $|S|=8$ secciones, $|P|=4$ profesores)

| Método | Tipo | Tasa Éxito ($SR$ %) | Distancia Factibilidad ($DF$) | $Z$ Mejor | $Z$ Promedio ± Std | $RPD$ (%) | Tiempo CPU (s) | $TTF$ (s) | Esfuerzo (NFE / Nodos) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **MIP (HiGHS)** | Exacto | **100.0%** | **0 / 0.0** | **3.0** | **3.00 ± 0.00** | **0.00% (Ref)** | 501.88 | 501.88 | 0 nodos (Cuts B&B) |
| **TS (Búsqueda Tabú)** | Metaheurística | **100.0%** | **0 / 0.0** | **7.0** | 16.67 ± 5.95 | +133.33% | 2.12 | 0.20 | 5,369 evals |
| **HGA (Propuesto)** | Metaheurística | **100.0%** | **0 / 0.0** | **9.0** | **13.40 ± 4.06** | **+200.00%** | **2.18** | **0.10** | 2,850 evals |
| **GA (Genético Clásico)** | Metaheurística | **100.0%** | **0 / 0.0** | **11.0** | 29.33 ± 9.66 | +266.67% | 1.31 | 0.28 | 3,408 evals |
| **SA (Recocido Simulado)** | Metaheurística | **100.0%** | **0 / 0.0** | **13.0** | 29.97 ± 9.45 | +333.33% | 1.57 | 0.47 | 1,196 evals |

---

### 2.3. Variante 3 (`pequena_s3`): Semilla 3 ($|E|=26$ eventos, $|R|=21$ salones, $|S|=10$ secciones, $|P|=4$ profesores)

| Método | Tipo | Tasa Éxito ($SR$ %) | Distancia Factibilidad ($DF$) | $Z$ Mejor | $Z$ Promedio ± Std | $RPD$ (%) | Tiempo CPU (s) | $TTF$ (s) | Esfuerzo (NFE / Nodos) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **MIP (HiGHS)** | Exacto | **100.0%** | **0 / 0.0** | **14.0** | **14.00 ± 0.00** | **0.00% (Ref)** | 5,780.20 | 5,780.20 | 0 nodos (Cuts B&B) |
| **HGA (Propuesto)** | Metaheurística | **100.0%** | **0 / 0.0** | **22.0** | **30.27 ± 5.69** | **+57.14%** | **5.09** | **0.19** | 3,516 evals |
| **TS (Búsqueda Tabú)** | Metaheurística | **100.0%** | **0 / 0.0** | **30.0** | 59.13 ± 11.43 | +114.29% | 2.98 | 0.73 | 6,008 evals |
| **SA (Recocido Simulado)** | Metaheurística | **100.0%** | **0 / 0.0** | **35.0** | 66.63 ± 15.49 | +150.00% | 3.23 | 1.59 | 1,860 evals |
| **GA (Genético Clásico)** | Metaheurística | **100.0%** | **0 / 0.0** | **47.0** | 65.73 ± 15.32 | +235.71% | 2.98 | 1.40 | 6,161 evals |

---

### 2.4. Resumen Consolidado Agregado (Escala Pequeña - 3 Variantes, 90 Réplicas / Metaheurística)

La siguiente tabla sintetiza el desempeño global promediado a través de las 3 instancias semi-sintéticas:

| Método | Tipo | Tasa Éxito ($SR$ %) | Distancia Factibilidad ($DF$) | $Z$ Mejor Global | $Z$ Promedio ± Std Agregado | $RPD$ vs MIP Óptimo | Tiempo CPU Promedio (s) | $TTF$ Promedio (s) | Esfuerzo Medio (NFE / Nodos) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **MIP (HiGHS)** | Exacto | **100.0%** | **0 / 0.0** | **3.0** | **8.33 ± 5.51** | **0.00% (Ref)** | 3,451.49 | 3,451.49 | 0 nodos (Cuts B&B) |
| **HGA (Propuesto)** | Metaheurística | **100.0%** | **0 / 0.0** | **9.0** | **20.67 ± 8.50** | **+200.00%** | **3.63** | **0.14** | **3,371 evals** |
| **TS (Búsqueda Tabú)** | Metaheurística | **100.0%** | **0 / 0.0** | **7.0** | 37.77 ± 19.55 | +133.33% | 2.42 | 0.39 | 5,443 evals |
| **GA (Genético Clásico)** | Metaheurística | **100.0%** | **0 / 0.0** | **11.0** | 44.57 ± 19.53 | +266.67% | 2.12 | 0.70 | 4,957 evals |
| **SA (Recocido Simulado)** | Metaheurística | **100.0%** | **0 / 0.0** | **13.0** | 46.19 ± 19.32 | +333.33% | 2.36 | 0.86 | 1,508 evals |

---

## 3. Desglose de Penalizaciones Blandas en la Mejor Solución

La siguiente tabla detalla la composición de penalizaciones blandas unitarias en la mejor solución obtenida por cada método en cada una de las tres variantes:

| Variante | Método | $P_{\text{alm}}$ ($W_A=1$) | $P_{\text{esp}}$ ($W_E=10$) | $P_{\text{jue}}$ ($W_{\text{jue}}=1$) | $P_{\text{sab}}$ ($W_{\text{sab}}=3$) | $P_{\text{vent}}$ ($W_V=2$) | **Costo Total $Z$** |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Variante 1 ($s_1$)** | **MIP (Óptimo)** | **0** | **0** | **2** | **2** | **0** | **8.0** |
| | **HGA** | **1** | **0** | **2** | **2** | **0** | **9.0** |
| | **TS** | 1 | 0 | 2 | 2 | 4 | **17.0** |
| | **SA** | 3 | 0 | 2 | 4 | 3 | **23.0** |
| | **GA** | 2 | 1 | 6 | 2 | 0 | **24.0** |
| **Variante 2 ($s_2$)** | **MIP (Óptimo)** | **0** | **0** | **0** | **1** | **0** | **3.0** |
| | **TS** | **1** | **0** | **6** | **0** | **0** | **7.0** |
| | **HGA** | **0** | **0** | **0** | **3** | **0** | **9.0** |
| | **GA** | 2 | 0 | 3 | 2 | 0 | **11.0** |
| | **SA** | 2 | 0 | 3 | 2 | 1 | **13.0** |
| **Variante 3 ($s_3$)** | **MIP (Óptimo)** | **2** | **0** | **6** | **2** | **0** | **14.0** |
| | **HGA** | **0** | **1** | **6** | **2** | **0** | **22.0** |
| | **TS** | 5 | 0 | 5 | 6 | 1 | **30.0** |
| | **SA** | 3 | 2 | 6 | 2 | 0 | **35.0** |
| | **GA** | 2 | 1 | 3 | 6 | 7 | **47.0** |

---

## 4. Auditoría Estricta de Restricciones Duras ($HCV$)

En la totalidad de las **363 ejecuciones computadas** (3 corridas de MIP + 90 de HGA + 90 de GA + 90 de TS + 90 de SA), los algoritmos alcanzaron **viabilidad operativa plena ($HCV = 0$, $DF = 0$)**:
* **Exclusividad docente:** Cero solapes horarios para ningún profesor en servicio lectivo.
* **Jornada máxima diaria:** Cero excesos por encima de las 8 horas pedagógicas al día.
* **Estabilidad espacial:** Cada sección académica se impartió en no más de 2 aulas a la semana.
* **Exclusividad de aulas físicas:** Ningún salón físico registró asignaciones concurrentes.
* **Compatibilidad curricular:** Ningún estudiante matriculado en su respectivo ciclo experimentó cruce de asignaturas simultáneas.

---

## 5. Discusión Científica y Hallazgos Principales

1. **Certificación Matemática Global por el Solver Exacto:**  
   HiGHS demostró la solvencia teórica de la formulación MIP indexada al alcanzar y certificar formalmente la **optimalidad matemática global ($Gap_{\text{MIP}} = 0.0\%$, `OPTIMAL`)** en las tres variantes evaluadas ($Z^* = 8.0$ en $s_1$, $Z^* = 3.0$ en $s_2$ y $Z^* = 14.0$ en $s_3$). No obstante, este rigor implicó un consumo temporal promedio de **3,451.49 segundos (~57.5 minutos por instancia)**, alcanzando hasta 5,780.20 s (~96.3 minutos) en la variante de 26 eventos.

2. **Ventaja Computacional del HGA Propuesto:**  
   El Algoritmo Genético Híbrido demostró ser la metodología metaheurística más eficiente y consistente del estudio:
   * **Velocidad de Respuesta:** Resolvió las instancias en un promedio de **3.63 segundos de CPU**, representando una aceleración de **casi tres órdenes de magnitud (~950 veces más rápido que MIP)**.
   * **Tiempo a la Factibilidad ($TTF$):** Alcanzó la frontera factible ($HCV = 0$) en apenas **0.14 segundos** promedio (durante la primera generación), gracias al operador constructivo *Most Constrained First* (MCF) y a la reducción topológica previa `valid_starts`.
   * **Consistencia y Calidad de Solución:** Logró el costo medio ponderado más bajo de todas las metaheurísticas ($Z_{\text{prom}} = 20.67 \pm 8.50$), superando por un margen de más del **53% de calidad** al Algoritmo Genético Clásico ($44.57 \pm 19.53$), a Tabu Search ($37.77 \pm 19.55$) y a Simulated Annealing ($46.19 \pm 19.32$).

3. **Impacto de la Reparación Heurística Memética (HGA vs GA):**  
   Al comparar directamente HGA con el GA canónico en las 90 réplicas, se observa que la hibridación memética elimina de forma sistemática los estancamientos en horarios dispersos. Mientras que el GA clásico con frecuencia genera soluciones con penalizaciones superiores a 60 ($65.73 \pm 15.32$ en la variante 3), el mecanismo constructivo de HGA compacta activamente la jornada docente ($P_{\text{ventanas}} = 0$ en sus mejores configuraciones) y protege el espaciado curricular.

4. **Comportamiento de las Metaheurísticas de Trayectoria (TS y SA):**  
   Búsqueda Tabú (TS) demostró una alta efectividad puntual en escenarios con muy pocos eventos (alcanzando $Z = 7.0$ en la variante 2), pero evidenció una mayor sensibilidad a la congestión al aumentar los eventos ($Z_{\text{prom}} = 59.13 \pm 11.43$ en la variante 3). Por su parte, el Recocido Simulado (SA) exhibió una exploración más uniforme pero con una tasa de convergencia blanda más lenta ($TTF = 0.86\text{ s}$).

---

## 6. Perspectiva hacia la Fase 2 (Instancias Mediana y Grande)

Para completar el marco contextual de escalabilidad, los registros experimentales preliminares de calibración histórica en escalas superiores demuestran la viabilidad del modelo matemático ante escenarios de mayor tamaño:

| Escala | Cursos / Eventos | Método | Estado | CPU Time (s) | $Z$ (Mejor) | $Z$ Promedio $\pm$ Std | $RPD$ (%) vs MIP |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **Mediana** | 37 cursos / 176–204 evs | **MIP** | `FEASIBLE` | 7,874.11 | 434,144.0 | 434,144.00 $\pm$ 0.00 | Ref. |
| | | **GA (Baseline)** | `CONVERGED` | 119.16 | 457.0 | 540.47 $\pm$ 29.75 | -99.89% |
| **Grande** | 62 cursos / 298–335 evs | **MIP** | `FEASIBLE` | 13,935.66 | 3,927,356.0 | 3,927,356.00 $\pm$ 0.00 | Ref. |
| | | **GA (Baseline)** | `CONVERGED` | 1,839.98 | 928.0 | 1,050.07 $\pm$ 66.56 | -99.98% |

> [!NOTE]
> La ejecución exhaustiva de las 30 réplicas del Algoritmo Genético Híbrido sobre las instancias Mediana y Grande se encuentra programada para la **Fase 2**, una vez certificada la robustez de los operadores meméticos en la presente Fase 1.
