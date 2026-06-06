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
| **Pequeña** | **MIP** | `OPTIMAL` | 44.09 | 0.0 | N/A | Ref. | 0 |
| | **GA** | `CONVERGED` | 1.45 | 0.0 | 0.20 | **0.00%** | 2,007.5 |
| **Mediana** | **MIP** | `FEASIBLE` | 7,704.53 | 325,078.0 | N/A | Ref. | 0 |
| | **GA** | `CONVERGED` | 74.78 | 502.0 | 538.70 | **-99.85%** | 3,660.0 |
| **Grande** | **MIP** | `FEASIBLE` | 13,935.66 | 3,927,356.0 | N/A | Ref. | 0 |
| | **GA** | `CONVERGED` | 1,210.26 | 973.0 | 1,061.45 | **-99.98%** | 8,175.0 |

* **Desviación Relativa (DR %)**: Calcula la diferencia porcentual de calidad de la metaheurística frente al solver exacto:
  $$\text{DR } (\%) = \frac{Z_{\text{AG}} - Z_{\text{MIP}}}{Z_{\text{MIP}}} \times 100$$
  Un valor negativo indica una mejora porcentual de la metaheurística sobre el solver exacto en tiempo limitado.
* **Tiempo de CPU MIP**: Refleja el tiempo de proceso acumulado en CPU. Las instancias mediana y grande alcanzaron el límite de tiempo de 2 horas reales (7,200 s) por diseño.

---

## 3. Desglose Detallado por Escenario

### A. Escala Pequeña
* **Alcance del escenario**: 23 eventos, 21 salones, 15 profesores (4 activos), 78 franjas semanales.
* **Resultados MIP**:
  * **Estado**: `OPTIMAL` (Óptimo global absoluto certificado).
  * **Z**: 0.0 (Cero penalizaciones de restricciones blandas).
  * **Tiempo CPU**: 44.09 segundos.
  * **Nodos explorados B&B**: 0 (resuelto en pre-solve y nodo raíz).
* **Resultados GA (20 corridas)**:
  * **Tasa de Factibilidad Final**: 100.0% (Las 20 corridas alcanzaron $HCV=0$).
  * **Mejor Z**: 0.0 (Corrida 1 / Semilla 42).
  * **Peor Z**: 2.0 (Corrida 13 / Semilla 54).
  * **Promedio Z**: 0.20 ($\pm 0.52$).
  * **Tiempo CPU Promedio**: 1.45 segundos.
  * **Tiempo hacia la factibilidad (TTF) Promedio**: 0.09 segundos.
  * **Evaluaciones de aptitud promedio**: 2,007.5.

---

### B. Escala Mediana
* **Alcance del escenario**: 176 eventos, 21 salones, 15 profesores (todos activos), 78 franjas semanales.
* **Resultados MIP**:
  * **Estado**: `FEASIBLE` (Límite de tiempo agotado).
  * **Z**: 325,078.0.
  * **Desglose de penalizaciones**: 18 clases programadas en hora de almuerzo ($18 \times W_A$) y 32,506 infracciones de espaciado en días consecutivos ($32,506 \times W_E$).
  * **Tiempo CPU**: 7,704.53 segundos (2.14 horas de CPU, limitado por el tiempo de parada de 2h).
  * **Nodos explorados B&B**: 0 (se quedó en el nodo raíz debido a la magnitud de la matriz de 9.7M de coeficientes).
* **Resultados GA (20 corridas)**:
  * **Tasa de Factibilidad Final**: 100.0% (Las 20 corridas alcanzaron $HCV=0$).
  * **Mejor Z**: 502.0 (Corrida 13 / Semilla 54).
    * *Desglose de la mejor corrida*: 22 clases en hora de almuerzo ($22 \times 1$) y 48 infracciones de espaciado ($48 \times 10$).
  * **Peor Z**: 600.0.
  * **Promedio Z**: 538.70 ($\pm 26.61$).
  * **Tiempo CPU Promedio**: 74.78 segundos.
  * **Tiempo hacia la factibilidad (TTF) Promedio**: 14.38 segundos.
  * **Evaluaciones de aptitud promedio**: 3,660.0.
  * **Mejora en calidad vs MIP**: **99.85% inferior en penalizaciones** y **103 veces más rápido** en tiempo de ejecución.

---

### C. Escala Grande
* **Alcance del escenario**: 298 eventos, 101 salones, 50 profesores, 78 franjas semanales.
* **Resultados MIP**:
  * **Estado**: `FEASIBLE` (Límite de tiempo agotado).
  * **Z**: 3,927,356.0.
  * **Tiempo CPU**: 13,935.66 segundos (multinúcleo, limitado por el tiempo real de 2 horas).
  * **Nodos explorados B&B**: 0.
* **Resultados GA (20 corridas)**:
  * **Tasa de Factibilidad Final**: 100.0% (Las 20 corridas alcanzaron $HCV=0$).
  * **Mejor Z**: 973.0 (Corrida 3 / Semilla 44).
    * *Desglose de la mejor corrida*: 43 clases en hora de almuerzo ($43 \times 1$) y 93 infracciones de espaciado ($93 \times 10$).
  * **Peor Z**: 1,181.0 (Corrida 20 / Semilla 61).
  * **Promedio Z**: 1,061.45 ($\pm 54.91$).
  * **Tiempo CPU Promedio**: 1,210.26 segundos (~20.1 minutos por corrida).
  * **Tiempo hacia la factibilidad (TTF) Promedio**: 484.20 segundos.
  * **Evaluaciones de aptitud promedio**: 8,175.0.
  * **Mejora en calidad vs MIP**: **99.98% inferior en penalizaciones** y **11.5 veces más rápido** por corrida.

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
