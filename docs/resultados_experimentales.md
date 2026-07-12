# Reporte Consolidado de Resultados Experimentales - UCTP

Este documento presenta los resultados de la auditoría experimental y la evaluación de escalabilidad de los solucionadores exacto (**MIP** con HiGHS) y metaheurístico (**Algoritmo Genético - GA**) para el Problema de Planificación Horaria Universitaria (UCTP).

---

## 1. Resumen Ejecutivo de Rendimiento

El experimento consistió en someter a ambos solucionadores a tres niveles de escala (Pequeña, Mediana y Grande). Mientras que el solver MIP garantiza optimalidad matemática teórica, la densidad combinatoria y la concurrencia de la malla curricular provocan que en escenarios medianos y grandes se estanque o agote el tiempo de ejecución. En contraste, el Algoritmo Genético, apoyado por su codificador heurístico de asignación (**Most Constrained First** con reparador de colisiones), encontró soluciones de muy alta calidad y 100% factibles en una fracción del tiempo.

**Factibilidad Operativa (HCV):** Ambos solucionadores lograron encontrar soluciones con $HCV = 0$ (cero violaciones a restricciones duras) en todas las escalas, cumpliendo satisfactoriamente con la viabilidad operativa requerida para la planificación institucional.

---

## 2. Tabla Comparativa Consolidada

A continuación se detallan las métricas unificadas para cada escala analizada:

| Escala | Solucionador | Estado Final | CPU Time (s) | $Z$ (Mejor / Único) | $Z$ (Promedio) | Desviación Relativa (DR %) | Nodos B&B / Evals Promedio |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Pequeña** | **MIP** | `OPTIMAL` | 42.03 | 0.0 | N/A | Ref. | 0 |
| | **GA** | `CONVERGED` | 2.49 | 0.0 | 0.10 | **0.00%** | 1,998.3 |
| **Mediana** | **MIP** | `FEASIBLE` | 7,874.11 | 434,144.0 | N/A | Ref. | 0 |
| | **GA** | `CONVERGED` | 119.16 | 457.0 | 540.47 | **-99.89%** | 3,576.0 |
| **Grande** | **MIP** | `FEASIBLE` | 13,935.66 | 3,927,356.0 | N/A | Ref. | 0 |
| | **GA** | `CONVERGED` | 1,839.98 | 928.0 | 1,050.07 | **-99.98%** | 7,960.0 |

* **Desviación Relativa (DR %)**: Calcula la diferencia porcentual de calidad de la metaheurística frente al solver exacto:
  $$\text{DR } (\%) = \frac{Z_{\text{AG}} - Z_{\text{MIP}}}{Z_{\text{MIP}}} \times 100$$
  Un valor negativo indica una mejora porcentual de la metaheurística sobre el solver exacto en tiempo limitado.
* **Tiempo de CPU MIP**: Refleja el tiempo de proceso acumulado en CPU. Las instancias mediana y grande alcanzaron el límite de tiempo de 2 horas reales (7,200 s) por diseño.

---

## 3. Desglose Detallado por Escenario

### A. Escala Pequeña
* **Alcance del escenario**: 23 eventos, 21 salones, 15 profesores (4 activos), 83 franjas semanales.
* **Resultados MIP**:
  * **Estado**: `OPTIMAL` (Óptimo global absoluto certificado).
  * **Z**: 0.0 (Cero penalizaciones de restricciones blandas).
  * **Tiempo CPU**: 42.03 segundos.
  * **Nodos explorados B&B**: 0 (resuelto en pre-solve y nodo raíz).
* **Resultados GA (30 corridas)**:
  * **Tasa de Factibilidad Final**: 100.0% (Las 30 corridas alcanzaron $HCV=0$).
  * **Mejor Z**: 0.0.
  * **Peor Z**: 1.0.
  * **Promedio Z**: 0.10 ($\pm 0.31$).
  * **Tiempo CPU Promedio**: 2.49 segundos.
  * **Tiempo hacia la factibilidad (TTF) Promedio**: 0.15 segundos.
  * **Evaluaciones de aptitud promedio**: 1,998.3.
* **Ocupación y Uso de Salones**:
  * **Capacidad Operativa Total**: 1,375 slots semanales (20 salones físicos $\times$ 68 slots + 1 virtual $\times$ 15 slots).
  * **Slots Utilizados**: 58 slots (100% de los eventos programados en su totalidad).
  * **Porcentaje de Uso General (Global)**: **4.22%** (idéntico en MIP y GA), con **4.26%** de ocupación promedio en salones físicos.
  * **Distribución de Uso por Salón (MIP vs. GA)**:
    * **MIP**: Concentró la mayor ocupación física en `salon_20` (10 slots, **14.71%**), `salon_2` (9 slots, **13.24%**), y `salon_6` (8 slots, **11.76%**).
    * **GA**: Concentró la mayor ocupación física en `salon_3` (11 slots, **16.18%**), `salon_19` (9 slots, **13.24%**), y `salon_2` (7 slots, **10.29%**).

---

### B. Escala Mediana
* **Alcance del escenario**: 176 eventos, 21 salones, 15 profesores (todos activos), 83 franjas semanales.
* **Resultados MIP**:
  * **Estado**: `FEASIBLE` (Límite de tiempo agotado).
  * **Z**: 434,144.0.
  * **Desglose de penalizaciones**: 14 clases programadas en hora de almuerzo ($14 \times 1$) y 43,413 infracciones de espaciado en días consecutivos ($43,413 \times 10$).
  * **Tiempo CPU**: 7,874.11 segundos (limitado por el tiempo de parada de 2h).
  * **Nodos explorados B&B**: 0 (se quedó en el nodo raíz).
* **Resultados GA (30 corridas)**:
  * **Tasa de Factibilidad Final**: 100.0% (Las 30 corridas alcanzaron $HCV=0$).
  * **Mejor Z**: 457.0.
    * *Desglose de la mejor corrida*: 27 clases en hora de almuerzo ($27 \times 1$) y 43 infracciones de espaciado ($43 \times 10$).
  * **Peor Z**: 583.0.
  * **Promedio Z**: 540.47 ($\pm 29.75$).
  * **Tiempo CPU Promedio**: 119.16 segundos.
  * **Tiempo hacia la factibilidad (TTF) Promedio**: 26.38 segundos.
  * **Evaluaciones de aptitud promedio**: 3,576.0.
  * **Mejora en calidad vs MIP**: **99.89% inferior en penalizaciones** y **66 veces más rápido** por corrida en tiempo de ejecución.
* **Ocupación y Uso de Salones**:
  * **Capacidad Operativa Total**: 1,375 slots semanales (20 salones físicos $\times$ 68 slots + 1 virtual $\times$ 15 slots).
  * **Slots Utilizados**: 366 slots para MIP, 379 slots para GA.
  * **Porcentaje de Uso General (Global)**: **26.62%** para MIP y **27.56%** para GA, con **26.91%** y **27.87%** de ocupación física respectivamente.
  * **Distribución de Uso por Salón (MIP vs. GA)**:
    * **MIP**: Concentró la mayor ocupación física en `salon_11` (27 slots, **39.71%**), `salon_3` (27 slots, **39.71%**) y `salon_2` (25 slots, **36.76%**).
    * **GA**: Concentró la mayor ocupación física en `salon_11` (39 slots, **57.35%**), `salon_8` (35 slots, **51.47%**) y `salon_10`/`salon_2` (32 slots, **47.06%** c/u).
    * Ambos programaron la ocupación de `r_virtual` (14 slots, **93.33%**).

---

### C. Escala Grande
* **Alcance del escenario**: 298 eventos, 101 salones, 50 profesores, 83 franjas semanales.
* **Resultados MIP**:
  * **Estado**: `FEASIBLE` (Límite de tiempo agotado).
  * **Z**: 3,927,356.0.
  * **Tiempo CPU**: 13,935.66 segundos (multinúcleo, limitado por el tiempo real de 2 horas).
  * **Nodos explorados B&B**: 0.
* **Resultados GA (30 corridas)**:
  * **Tasa de Factibilidad Final**: 100.0% (Las 30 corridas alcanzaron $HCV=0$).
  * **Mejor Z**: 928.0.
    * *Desglose de la mejor corrida*: 38 clases en hora de almuerzo ($38 \times 1$) y 89 infracciones de espaciado ($89 \times 10$).
  * **Peor Z**: 1,202.0.
  * **Promedio Z**: 1,050.07 ($\pm 66.56$).
  * **Tiempo CPU Promedio**: 1,839.98 segundos.
  * **Tiempo hacia la factibilidad (TTF) Promedio**: 752.16 segundos (~12.5 minutos).
  * **Evaluaciones de aptitud promedio**: 7,960.0.
  * **Mejora en calidad vs MIP**: **99.98% inferior en penalizaciones** y **7.6 veces más rápido** por corrida.
* **Ocupación y Uso de Salones**:
  * **Capacidad Operativa Total**: 6,815 slots semanales (100 salones físicos $\times$ 68 slots + 1 virtual $\times$ 15 slots).
  * **Slots Utilizados**: 651 slots para GA (MIP N/D debido a que la optimización local excedió la memoria RAM del sistema).
  * **Porcentaje de Uso General (Global)**: **9.55%** para GA (MIP N/D), con **9.57%** de ocupación física.
  * **Distribución de Uso por Salón (GA)**:
    * **GA**: Concentró la mayor ocupación física en `salon_14` (22 slots, **32.35%**), `salon_2` (22 slots, **32.35%**), y `salon_44`/`salon_47` (19 slots, **27.94%** c/u).
    * La ocupación del aula virtual `r_virtual` fue de 0 slots (**0.00%**).

---

## 4. Desglose Analítico de Restricciones Duras (HCV)

El éxito operativo radica en asegurar que la tasa de violaciones a restricciones duras ($HCV$) sea exactamente **0**. A continuación se detalla cómo se comportaron estas restricciones en el Algoritmo Genético a lo largo de las corridas para los tres escenarios:

| Restricción Dura | Nomenclatura del Código | Escala Pequeña | Escala Mediana | Escala Grande |
| :--- | :--- | :---: | :---: | :---: |
| **Colisión de Profesores** | `hcv_colision_profesor` | 0 | 0 | 0 |
| **Carga Máxima Docente** | `hcv_carga_maxima_profesor` | 0 | 0 | 0 |
| **Estabilidad de Salones** | `hcv_estabilidad_salones` | 0 | 0 | 0 |
| **Colisión de Salones Físicos** | `hcv_colision_salones_fisicos`| 0 | 0 | 0 |
| **Conflicto Curricular** | `hcv_conflicto_curricular` | 0 | 0 | 0 |

La tasa de factibilidad inicial en el Algoritmo Genético es del **0.0%** en todas las escalas. Esto demuestra que las soluciones generadas de forma puramente aleatoria no son factibles debido a la alta densidad de restricciones del UCTP. Sin embargo, el operador reparador heurístico en el decodificador logra restaurar el 100% de factibilidad ($HCV = 0$) antes de finalizar la primera generación.

---

## 5. Conclusiones Metodológicas

1. **Escalabilidad y Flexibilidad**: A medida que el problema crece a escala institucional completa (Escenario Grande), el enfoque exacto MIP sufre debido a la explosión del espacio de búsqueda y las dependencias de exclusión mutua de la malla curricular.
2. **Eficiencia de la Metaheurística**: El decodificador heurístico del GA, diseñado específicamente para resolver solapamientos y colisiones locales, actúa como un potente filtro que guía la búsqueda directamente en la frontera factible del espacio combinatorio.
3. **Recomendación Operativa**: Para la planificación regular de horarios en la institución, se recomienda adoptar el Algoritmo Genético, ya que genera horarios viables en minutos con penalizaciones insignificantes para docentes y alumnos, mientras que el modelo MIP debe reservarse únicamente para auditorías de subconjuntos de baja escala.
