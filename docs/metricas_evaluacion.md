# Métricas de Evaluación

**Fecha de actualización:** 19 de octubre de 2026

Métricas de desempeño para optimización UCTP / CB-CTT en tres dimensiones:

---

## 1. Viabilidad Operativa (Restricciones Duras)

* **Tasa de Éxito ($SR$ %):** Porcentaje de corridas con horario factible ($HCV = 0$):
  $$SR (\%) = \left(\frac{\text{Corridas con } HCV = 0}{\text{Total de corridas}}\right) \times 100$$
* **Distancia a la Factibilidad ($DF$):** Total de violaciones duras ($HCV$). En soluciones factibles, $DF = 0$.
* **Tiempo a la Factibilidad ($TTF$):** Segundos de CPU hasta la primera solución con $HCV = 0$.

---

## 2. Calidad de la Solución (Restricciones Blandas)

* **Función Objetivo ($Z$):** Costo ponderado de penalizaciones blandas (almuerzo, espaciado, preferencia temporal y ventanas). Su formulación y pesos se detallan en [modelo_matematico.md](modelo_matematico.md).
* **Brecha de Optimalidad MIP ($Gap_{\text{MIP}}$ %):**
  $$Gap_{\text{MIP}} = \frac{Z_{\text{MIP}} - LB}{Z_{\text{MIP}}} \times 100$$
* **Desviación Relativa Porcentual ($RPD$ %):** Desviación respecto a la referencia MIP ($Z_{\text{MIP}}$):
  $$RPD (\%) = \begin{cases} \dfrac{Z_{\text{meta}} - Z_{\text{MIP}}}{Z_{\text{MIP}}} \times 100 & \text{si } Z_{\text{MIP}} > 0 \\ \dfrac{Z_{\text{meta}} - Z_{\text{MIP}}}{Z_{\text{MIP}} + 1} \times 100 & \text{si } Z_{\text{MIP}} = 0 \end{cases}$$
  con $\Delta Z = Z_{\text{meta}} - Z_{\text{MIP}}$.

---

## 3. Eficiencia Computacional

* **Tiempo CPU (s):** Tiempo total de cómputo hasta la condición de parada.
* **Evaluaciones de Aptitud ($NFE$):** Soluciones evaluadas por la metaheurística.
* **Nodos B&B:** Nodos de ramificación explorados por el solucionador exacto.
