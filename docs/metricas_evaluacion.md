# Marco de Métricas y Criterios de Evaluación

Este documento formaliza el conjunto de indicadores y criterios metodológicos utilizados para evaluar el desempeño, la calidad y la eficiencia de los algoritmos de optimización para el problema CB-CTT en el marco de la investigación.

Siguiendo las directrices y estándares metodológicos de la literatura especializada en optimización de horarios universitarios (*Abdipoor, Yaakob, et al., 2025; Bashab et al., 2023*), el análisis se estructura en **tres dimensiones fundamentales**:

---

## 1. Viabilidad Operativa y Factibilidad

Audita la capacidad de los algoritmos para respetar las restricciones duras ($HCV = 0$) y generar horarios operativamente viables para la institución.

* **Tasa de Éxito / Factibilidad Global ($SR$):**  
  Porcentaje de ejecuciones independientes que culminan con un horario estrictamente factible (cero violaciones a restricciones duras, $HCV = 0$). Permite evaluar la efectividad de la heurística constructiva y los mecanismos de reparación para encontrar configuraciones válidas respetando aforos, disponibilidad docente y requerimientos de infraestructura (*Abdipoor, Li, et al., 2025; Bashab et al., 2023*).
  $$\text{Tasa de Éxito (\%)} = \left(\frac{\text{Corridas con } HCV = 0}{\text{Total de corridas}}\right) \times 100$$

* **Distancia a la Factibilidad ($DF$):**  
  Cuantificación del número o magnitud de las restricciones duras insatisfechas en aquellas soluciones que no alcanzan la viabilidad plena. Esta métrica discrimina el grado de aproximación a la frontera factible en instancias altamente congestionadas, superando la limitación de las funciones de costo convencionales que no guían adecuadamente en espacios infactibles (*Abdipoor, Li, et al., 2025*).

* **Tiempo hacia la Factibilidad ($TTF$ - *Time to Feasibility*):**  
  Registro del tiempo computacional (en segundos) transcurrido desde el inicio de la ejecución hasta que el algoritmo descubre la primera solución que cumple con todas las restricciones duras ($HCV = 0$) (*Chen et al., 2021; Haider et al., 2024*).

---

## 2. Calidad de la Optimización

Mide el grado de satisfacción de las preferencias institucionales y la minimización de las restricciones blandas.

* **Valor de la Función Objetivo ($Z$):**  
  Cuantificación directa de la penalización ponderada por concepto de restricciones blandas institucionales:
  $$\min Z = 1 \cdot P_{\text{almuerzo}} + 10 \cdot P_{\text{espaciado}} + 1 \cdot P_{\text{jueves}} + 3 \cdot P_{\text{sabado}} + 2 \cdot P_{\text{ventanas}}$$
  Dada la naturaleza estocástica de las metaheurísticas, se ejecutan 20 corridas independientes por algoritmo e instancia, reportando:
  * **Mejor Valor $Z$:** El menor costo alcanzado.
  * **Valor Promedio de $Z$:** Rendimiento esperado del método.
  * **Desviación Estándar ($\sigma$):** Medida de la estabilidad y consistencia estocástica (*Abdipoor, Yaakob, et al., 2025*).

* **Gap de Optimalidad MIP ($Gap_{\text{MIP}}$):**  
  Diferencia porcentual entre la mejor solución entera encontrada por el solver exacto y su límite teórico inferior (*Best Bound* o *Lower Bound* continuo del árbol de *Branch and Bound*). Un valor de $0.0\%$ certifica la optimalidad matemática global (*Mikkelsen & Holm, 2022; Rohaizad et al., 2026*):
  $$Gap_{\text{MIP}} = \frac{Z_{\text{MIP}} - LB}{Z_{\text{MIP}}} \times 100$$

* **Desviación Relativa de la Metaheurística ($GAP / RPD$):**  
  Discrepancia porcentual entre la mejor solución producida por la metaheurística ($Z_{\text{meta}}$) y el valor de referencia provisto por el modelo exacto MIP ($Z_{\text{MIP}}$). Para prevenir indeterminaciones cuando el modelo exacto encuentra una solución óptima perfecta sin penalizaciones ($Z_{\text{MIP}} = 0$), se adopta la formulación robusta con offset unitario de *Abdipoor, Yaakob, et al. (2025)* y *Stidsen et al. (2024)*:
  $$RPD (\%) = \begin{cases} \dfrac{Z_{\text{meta}} - Z_{\text{MIP}}}{Z_{\text{MIP}}} \times 100 & \text{si } Z_{\text{MIP}} > 0 \\ \dfrac{Z_{\text{meta}} - Z_{\text{MIP}}}{Z_{\text{MIP}} + 1} \times 100 & \text{si } Z_{\text{MIP}} = 0 \end{cases}$$
  reportando adicionalmente la diferencia absoluta $\Delta Z = Z_{\text{meta}} - Z_{\text{MIP}}$.

---

## 3. Eficiencia Computacional y Entorno de Pruebas

Evalúa los recursos computacionales consumidos y garantiza la reproducibilidad experimental.

* **Tiempo de Procesamiento ($CPU\text{ Time}$):**  
  Medición en segundos del tiempo de CPU total invertido por cada método hasta satisfacer el criterio de parada estipulado (convergencia anticipada o tiempo límite máximo) (*Bashab et al., 2023; Gu et al., 2025*).

* **Trazabilidad del Entorno:**  
  Documentación explícita de las características del hardware (modelo de CPU, memoria RAM disponible, sistema operativo) y del software (versión del intérprete Python, librerías y versión del solver matemático), asegurando la reproducibilidad estricta de las evaluaciones (*Rohaizad et al., 2026*).

* **Auditoría de Esfuerzo Interno:**  
  Métricas que cuantifican la intensidad de exploración propia de cada paradigma computacional:
  * **Número de Evaluaciones de Aptitud ($NFE$ - *Number of Fitness Evaluations*):** Cantidad de soluciones evaluadas durante el ciclo evolutivo de las metaheurísticas.
  * **Nodos de *Branch and Bound* Explorados:** Cantidad de subproblemas ramificados por el solver MIP.  
  Ambas métricas permiten evaluar el costo computacional interno sin forzar analogías artificiales entre métodos exactos y aproximados (*Abdipoor, Yaakob, et al., 2025; Bashab et al., 2023*).

---

## Referencias Bibliográficas Asociadas

* **Abdipoor, M., Li, Y., et al. (2025).** *Distance to Feasibility Performance Assessment of Baseline Metaheuristics on University Course Timetabling Problem*.
* **Abdipoor, M., Yaakob, R., et al. (2025).** *Optimality Versus Generality Performance Assessment of Meta-Heuristics in Educational Timetabling*.
* **Bashab, S., et al. (2023).** *Optimization Techniques in University Timetabling Problem: Constraints, Methodologies, Benchmarks*.
* **Chen, M. C., et al. (2021).** *A Survey of University Course Timetabling Problem: Perspectives, Trends and Opportunities*.
* **Haider, S., et al. (2024).** *Course Timetabling Approaches and Feasibility Benchmarks*.
* **Mikkelsen, V., & Holm, P. (2022).** *Exact Formulations and Bound Tightening in Timetabling Problems*.
* **Rohaizad, N., et al. (2026).** *Mathematical Modeling and Computational Reproducibility in Educational Operations Research*.
* **Stidsen, T., et al. (2024).** *Comparative Performance Analysis of Exact and Heuristic Methods in CB-CTT*.
