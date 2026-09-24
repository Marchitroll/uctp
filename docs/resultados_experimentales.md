# Reporte Consolidado de Resultados Experimentales - UCTP

Este documento presenta los resultados de la evaluación experimental y el análisis comparativo del modelo exacto (**MIP** con HiGHS) frente a las cuatro metaheurísticas implementadas (**HGA**, **GA**, **TS**, **SA**) para el Problema de Planificación Horaria Universitaria (UCTP).

---

## 1. Resumen Ejecutivo de Rendimiento

El problema de planificación horaria se evalúa sobre la función objetivo consolidada con cuatro restricciones blandas (cinco componentes ponderados):

$$\min Z = 1 \cdot P_{\text{almuerzo}} + 10 \cdot P_{\text{espaciado}} + 1 \cdot P_{\text{jueves}} + 3 \cdot P_{\text{sabado}} + 2 \cdot P_{\text{ventanas}}$$

Bajo este marco, se contrastan cinco enfoques algorítmicos:
1. **Programación Lineal Entera Mixta (MIP)**: Enfoque exacto con el solver HiGHS v1.13.1.
2. **Algoritmo Genético Híbrido (HGA)**: Metaheurística memética con operador constructivo *Most Constrained First* (MCF), desplazamiento en cadena y aprendizaje lamarckiano.
3. **Algoritmo Genético Clásico (GA)**: Algoritmo poblacional canónico con cruzamiento y mutación sin reparación heurística.
4. **Búsqueda Tabú (TS)**: Metaheurística de trayectoria con vecindario discreto sobre dominios precomputados y memoria tabú.
5. **Recocido Simulado (SA)**: Metaheurística de trayectoria estocástica con perturbaciones discretas y criterio de Metropolis.

**Factibilidad Operativa (HCV):** Todos los algoritmos alcanzaron un $100\%$ de factibilidad operativa ($HCV = 0$, $DF = 0$) en sus soluciones finales, respetando aforos, exclusividad de aulas físicas, carga docente máxima (8h/día), estabilidad de salones y no colisión curricular.

---

## 2. Comparativa Benchmark en Escala Pequeña

La escala pequeña representa el caso base institucional ($|E|=33$ eventos, $|R|=21$ salones, $|S|=13$ secciones, $|P|=4$ docentes, $|T|=86$ franjas semanales):

| Método | Tipo | Tasa Éxito (SR %) | DF (Mejor / Prom) | $Z$ (Mejor) | $Z$ (Promedio $\pm$ Std) | RPD (%) vs MIP | CPU Time (s) | TTF (s) | Esfuerzo (NFE / Nodos) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **MIP (HiGHS)** | Exacto | 100.0% | 0 / 0.0 | **102,457.0** | 102,457.00 $\pm$ 0.00 | 0.00% (Ref) | 213.25 | 213.25 | 0 nodos (Cuts) |
| **HGA (Memético MCF)** | Metaheurística | **100.0%** | **0 / 0.0** | **25.0** | **25.00 $\pm$ 0.00** | **-99.98%** | **9.59** | **0.20** | 5,000 evals |
| **SA (Recocido Simulado)**| Metaheurística | 100.0% | 0 / 0.0 | **48.0** | 48.00 $\pm$ 0.00 | -99.95% | 11.62 | 2.34 | 3,461 evals |
| **TS (Búsqueda Tabú)** | Metaheurística | 100.0% | 0 / 0.0 | **87.0** | 87.00 $\pm$ 0.00 | -99.92% | 3.34 | 1.34 | 5,622 evals |
| **GA (Genético Clásico)** | Metaheurística | 100.0% | 0 / 0.0 | **91.0** | 91.00 $\pm$ 0.00 | -99.91% | 2.14 | 0.86 | 4,200 evals |

### Desglose de Penalizaciones Blandas en la Mejor Solución (Escala Pequeña)

| Método | $P_{\text{almuerzo}}$ ($W=1$) | $P_{\text{espaciado}}$ ($W=10$) | $P_{\text{jueves}}$ ($W=1$) | $P_{\text{sabado}}$ ($W=3$) | $P_{\text{ventanas}}$ ($W=2$) | **Costo Total $Z$** |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **MIP (HiGHS)** | 6 | 10,242 | 10 | 7 | 0 | **102,457.0** |
| **HGA** | 6 | 1 | 3 | 2 | 0 | **25.0** |
| **SA** | 3 | 3 | 0 | 0 | 7 | **48.0** |
| **TS** | 4 | 5 | 0 | 0 | 14 | **87.0** |
| **GA** | 4 | 6 | 0 | 3 | 9 | **91.0** |

> [!NOTE]
> * **Eficacia de HGA**: El Algoritmo Genético Híbrido obtuvo el mejor desempeño global ($Z = 25.0$), encontrando una solución factible en solo 0.20 segundos (Generación 1) gracias a la combinación de Most Constrained First y aprendizaje lamarckiano.
> * **MIP en Límite de Tiempo**: En el límite fijado, el solucionador exacto HiGHS encontró una solución factible pero con alta penalización en espaciado continuo ($Z = 102,457.0$), evidenciando la ventaja de las metaheurísticas para explorar rápidamente horarios de alta calidad bajo restricciones multiobjetivo complejas.

---

## 3. Resultados Históricos en Escalas Mediana y Grande (Baseline Preliminar)

Las escalas mediana y grande fueron evaluadas durante la fase preliminar de calibración (bajo la formulación baseline de almuerzo y espaciado):

| Escala | Solucionador | Estado Final | CPU Time (s) | $Z$ (Mejor) | $Z$ (Promedio $\pm$ Std) | Desviación Relativa (RPD %) | Esfuerzo (NFE / Nodos) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Mediana** | **MIP** | `FEASIBLE` | 7,874.11 | 434,144.0 | 434,144.00 $\pm$ 0.00 | Ref. | 0 nodos |
| | **HGA (Preliminar)** | `CONVERGED` | 119.16 | 457.0 | 540.47 $\pm$ 29.75 | **-99.89%** | 3,576 evals |
| **Grande** | **MIP** | `FEASIBLE` | 13,935.66 | 3,927,356.0 | 3,927,356.00 $\pm$ 0.00 | Ref. | 0 nodos |
| | **HGA (Preliminar)** | `CONVERGED` | 1,839.98 | 928.0 | 1,050.07 $\pm$ 66.56 | **-99.98%** | 7,960 evals |

* **Escala Mediana** ($|E|=176$ eventos, $|R|=21$ salones, $|P|=11$ profesores): HGA superó a MIP en un 99.89% de calidad y resolvió 66 veces más rápido.
* **Escala Grande** ($|E|=298$ eventos, $|R|=101$ salones, $|P|=19$ profesores): El modelo exacto requirió más de 3.8 horas de cómputo multinúcleo estancándose en el nodo raíz, mientras que HGA convergió con una penalización residual significativamente menor ($Z = 928.0$).

---

## 4. Desglose Analítico de Restricciones Duras (HCV)

En todas las soluciones finales reportadas por los 5 métodos, las violaciones a restricciones duras ($HCV$) se mantuvieron en **cero absoluto**:

| Restricción Dura | Indicador en Código | MIP | HGA | GA | TS | SA |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Colisión de Profesores** | `colision_profesor` | 0 | 0 | 0 | 0 | 0 |
| **Carga Máxima Docente (8h/día)** | `carga_maxima_profesor` | 0 | 0 | 0 | 0 | 0 |
| **Estabilidad de Salones ($\le 2$)** | `estabilidad_salones` | 0 | 0 | 0 | 0 | 0 |
| **Colisión de Salones Físicos** | `colision_salones_fisicos`| 0 | 0 | 0 | 0 | 0 |
| **Conflicto Curricular (Malla)** | `conflicto_curricular` | 0 | 0 | 0 | 0 | 0 |

---

## 5. Conclusiones Metodológicas

1. **Aportación de la Heurística Memética**: La comparación directa entre HGA ($Z = 25.0$) y GA clásico ($Z = 91.0$) en la misma instancia demuestra que el operador constructivo Most Constrained First (MCF) reduce drásticamente las penalizaciones blandas y acelera la convergencia a factibilidad ($TTF = 0.20\text{ s}$ frente a $0.86\text{ s}$).
2. **Competitividad de Recocido Simulado**: SA demostró una excelente capacidad de exploración estocástica ($Z = 48.0$), posicionándose como la segunda mejor metaheurística tras HGA.
3. **Escalabilidad**: Mientras que los solucionadores exactos sufren por la densidad combinatoria en horizontes de 86 franjas, las metaheurísticas sobre el espacio reducido de `valid_starts` ofrecen soluciones factibles y de alta calidad operativa en segundos.
