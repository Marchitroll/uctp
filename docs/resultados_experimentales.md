# Resultados Experimentales - UCTP

**Fecha de actualización:** 19 de octubre de 2026  
**Entorno:** Intel Core i5-12400F, 16 GB RAM DDR5, Windows 11, Python 3.13 con UV, `python-mip` v2.0.0 (HiGHS v1.13.1) y `mealpy` v3.0.2 (detalle en la Sección 7).

---

## 1. Metodología de Evaluación

Comparación experimental entre el modelo exacto (**MIP**) y cuatro metaheurísticas (**HGA**, **GA**, **TS**, **SA**) sobre 9 instancias semi-sintéticas ($3 \times 3$: escalas pequeña, mediana y grande con semillas deterministas $s_1, s_2, s_3$).

En escala pequeña (`pequena_s1`, `pequena_s2`, `pequena_s3`):
* 1 corrida de MIP (HiGHS).
* 30 corridas independientes por metaheurística (semillas 1 a 30).
* Total: 360 corridas metaheurísticas y 3 de MIP (363 en total).

Las escalas mediana y grande analizan la escalabilidad computacional en escenarios de mayor densidad de eventos.

La función objetivo se define en [modelo_matematico.md](modelo_matematico.md) y las métricas en [metricas_evaluacion.md](metricas_evaluacion.md).

---

## 2. Comparativa Benchmark en Escala Pequeña

### 2.1. Variante 1 (`pequena_s1`): Semilla 1 ($|E|=20$ eventos, $|R|=21$ salones, $|S|=9$ secciones, $|P|=15$ profesores)

| Método | SR (%) | DF (Mejor / Prom) | $Z$ Mejor | $Z$ Promedio ± Std | RPD (%) | CPU (s) | TTF (s) | Esfuerzo (NFE / Nodos) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **MIP** | **100.0%** | **0 / 0.0** | **0.0** | **0.00 ± 0.00** | **0.00% (Ref)** | 202.73 | 202.73 | 0 nodos |
| **HGA** | **100.0%** | **0 / 0.0** | **0.0** | 5.83 ± 4.11 | **0.00% (dZ=0)** | 2.08 | 0.09 | 2,725 evals |
| **GA** | **100.0%** | **0 / 0.0** | **3.0** | 16.20 ± 7.96 | **+300.0% (dZ=3)** | 1.55 | 0.21 | 3,876 evals |
| **TS** | **100.0%** | **0 / 0.0** | **0.0** | 7.77 ± 5.32 | **0.00% (dZ=0)** | 2.22 | 0.11 | 5,083 evals |
| **SA** | **100.0%** | **0 / 0.0** | **1.0** | 16.90 ± 10.16 | **+100.0% (dZ=1)** | 2.04 | 0.28 | 1,260 evals |

---

### 2.2. Variante 2 (`pequena_s2`): Semilla 2 ($|E|=17$ eventos, $|R|=21$ salones, $|S|=8$ secciones, $|P|=15$ profesores)

| Método | SR (%) | DF (Mejor / Prom) | $Z$ Mejor | $Z$ Promedio ± Std | RPD (%) | CPU (s) | TTF (s) | Esfuerzo (NFE / Nodos) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **MIP** | **100.0%** | **0 / 0.0** | **0.0** | **0.00 ± 0.00** | **0.00% (Ref)** | 73.53 | 73.53 | 0 nodos |
| **HGA** | **100.0%** | **0 / 0.0** | **1.0** | 5.47 ± 3.74 | **+100.0% (dZ=1)** | 1.47 | 0.07 | 2,313 evals |
| **GA** | **100.0%** | **0 / 0.0** | **2.0** | 13.60 ± 6.67 | **+200.0% (dZ=2)** | 1.31 | 0.12 | 3,176 evals |
| **TS** | **100.0%** | **0 / 0.0** | **0.0** | 7.17 ± 4.80 | **0.00% (dZ=0)** | 1.97 | 0.07 | 4,664 evals |
| **SA** | **100.0%** | **0 / 0.0** | **5.0** | 16.23 ± 7.60 | **+500.0% (dZ=5)** | 1.52 | 0.15 | 1,068 evals |

---

### 2.3. Variante 3 (`pequena_s3`): Semilla 3 ($|E|=25$ eventos, $|R|=21$ salones, $|S|=10$ secciones, $|P|=15$ profesores)

| Método | SR (%) | DF (Mejor / Prom) | $Z$ Mejor | $Z$ Promedio ± Std | RPD (%) | CPU (s) | TTF (s) | Esfuerzo (NFE / Nodos) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **MIP** | **100.0%** | **0 / 0.0** | **0.0** | **0.00 ± 0.00** | **0.00% (Ref)** | 204.08 | 204.08 | 0 nodos |
| **HGA** | **100.0%** | **0 / 0.0** | **2.0** | 6.27 ± 3.43 | **+200.0% (dZ=2)** | 4.59 | 0.15 | 4,088 evals |
| **GA** | **100.0%** | **0 / 0.0** | **16.0** | 38.27 ± 16.82 | **+1600.0% (dZ=16)** | 2.51 | 0.43 | 5,360 evals |
| **TS** | **100.0%** | **0 / 0.0** | **17.0** | 30.47 ± 8.83 | **+1700.0% (dZ=17)** | 2.22 | 0.19 | 4,637 evals |
| **SA** | **100.0%** | **0 / 0.0** | **5.0** | 40.30 ± 17.56 | **+500.0% (dZ=5)** | 2.44 | 0.49 | 1,460 evals |

---

### 2.4. Resumen Consolidado Agregado (Escala Pequeña - 3 Variantes)

| Método | SR (%) | DF (Mejor / Prom) | $Z$ Mejor Global | $Z$ Promedio ± Std | RPD (%) | CPU Prom (s) | TTF Prom (s) | Esfuerzo Medio |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **MIP** | **100.0%** | **0 / 0.0** | **0.0** | **0.00 ± 0.00** | **0.00% (Ref)** | 160.11 | 160.11 | 0 nodos |
| **HGA** | **100.0%** | **0 / 0.0** | **0.0** | 5.86 ± 3.74 | **0.00% (dZ=0)** | 2.71 | 0.10 | 3,042 evals |
| **GA** | **100.0%** | **0 / 0.0** | **2.0** | 22.69 ± 15.85 | **+200.0% (dZ=2)** | 1.79 | 0.25 | 4,137 evals |
| **TS** | **100.0%** | **0 / 0.0** | **0.0** | 15.13 ± 12.69 | **0.00% (dZ=0)** | 2.14 | 0.12 | 4,794 evals |
| **SA** | **100.0%** | **0 / 0.0** | **1.0** | 24.48 ± 16.72 | **+100.0% (dZ=1)** | 2.00 | 0.31 | 1,263 evals |

---

## 3. Desglose de Penalizaciones Blandas en la Mejor Solución

| Variante | Método | $P_{\text{alm}}$ ($W_A=1$) | $P_{\text{esp}}$ ($W_E=10$) | $P_{\text{jue}}$ ($W_{\text{jue}}=1$) | $P_{\text{sab}}$ ($W_{\text{sab}}=3$) | $P_{\text{vent}}$ ($W_V=2$) | **Costo Total $Z$** |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Variante 1 ($s_1$)** | **MIP** | **0** | **0** | **0** | **0** | **0** | **0.0** |
|  | **HGA** | **0** | **0** | **0** | **0** | **0** | **0.0** |
|  | **TS** | **0** | **0** | **0** | **0** | **0** | **0.0** |
|  | **SA** | **1** | **0** | **0** | **0** | **0** | **1.0** |
|  | **GA** | **1** | **0** | **2** | **0** | **0** | **3.0** |
| **Variante 2 ($s_2$)** | **MIP** | **0** | **0** | **0** | **0** | **0** | **0.0** |
|  | **HGA** | **1** | **0** | **0** | **0** | **0** | **1.0** |
|  | **TS** | **0** | **0** | **0** | **0** | **0** | **0.0** |
|  | **SA** | **1** | **0** | **0** | **0** | **2** | **5.0** |
|  | **GA** | **2** | **0** | **0** | **0** | **0** | **2.0** |
| **Variante 3 ($s_3$)** | **MIP** | **0** | **0** | **0** | **0** | **0** | **0.0** |
|  | **HGA** | **2** | **0** | **0** | **0** | **0** | **2.0** |
|  | **TS** | **3** | **0** | **0** | **0** | **7** | **17.0** |
|  | **SA** | **5** | **0** | **0** | **0** | **0** | **5.0** |
|  | **GA** | **4** | **0** | **2** | **2** | **2** | **16.0** |

---

## 4. Cumplimiento de Restricciones Duras ($HCV$)

En las 363 ejecuciones, todos los métodos obtuvieron soluciones factibles ($HCV = 0$, $DF = 0$):
* **Exclusividad docente:** Sin solapamientos de horario por profesor.
* **Jornada máxima diaria:** Máximo 8 horas lectivas al día por docente.
* **Estabilidad espacial:** Máximo 2 salones distintos por sección.
* **Exclusividad física:** Sin colisiones en salones físicos.
* **Oferta curricular:** Sin cruces de asignaturas dentro del mismo ciclo.

---

## 5. Principales Hallazgos

1. **MIP (Exacto):** Alcanza el óptimo ($Z^* = 0.0$) en las 3 variantes pequeñas en 160.11 s promedio.
2. **HGA:** Metaheurística más balanceada ($Z_{\text{prom}} = 5.86 \pm 3.74$), resolviendo en 2.71 s promedio (~59 veces más rápido que MIP) con tiempo a factibilidad $TTF = 0.10\text{ s}$.
3. **Reparación MCF:** Reduce un 74% el costo promedio frente a GA clásico ($22.69 \pm 15.85$), eliminando ventanas docentes y optimizando el espaciado.
4. **TS y SA:** TS alcanza el óptimo ($Z = 0.0$) en $s_1$ y $s_2$, pero decae en $s_3$ ($Z_{\text{prom}} = 30.47 \pm 8.83$). SA presenta la mayor dispersión ($Z_{\text{prom}} = 24.48 \pm 16.72$, $TTF = 0.31\text{ s}$).

---

## 6. Resultados Preliminares en Escalas Mediana y Grande

Evaluación preliminar sobre las instancias representativas `mediana_s1` (184 eventos) y `grande_s1` (305 eventos):

| Escala | Instancia | Eventos | Método | Estado | CPU Time (s) | $Z$ Mejor | $Z$ Promedio $\pm$ Std | RPD (%) vs MIP |
| :--- | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **Mediana** | `mediana_s1` | 184 | **MIP** | `FEASIBLE` | 7,874.11 | 434,144.0 | 434,144.00 $\pm$ 0.00 | Ref. |
| | | | **GA** | `CONVERGED` | 119.16 | 457.0 | 540.47 $\pm$ 29.75 | -99.89% |
| **Grande** | `grande_s1` | 305 | **MIP** | `FEASIBLE` | 13,935.66 | 3,927,356.0 | 3,927,356.00 $\pm$ 0.00 | Ref. |
| | | | **GA** | `CONVERGED` | 1,839.98 | 928.0 | 1,050.07 $\pm$ 66.56 | -99.98% |

---

## 7. Especificaciones del Entorno Experimental

| Parámetro | Valor Registrado |
| :--- | :--- |
| **Sistema Operativo** | Windows 11 |
| **Procesador (CPU)** | Intel Core i5-12400F (Intel64 Family 6 Model 151) |
| **Memoria RAM Total** | 15.83 GB |
| **Versión Python** | 3.13.15 |
| **Versión Python-MIP / HiGHS** | 2.0.0 |
| **Versión MEALPY** | 3.0.2 |
