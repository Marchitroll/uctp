# Formulación Matemática

**Fecha de actualización:** 19 de octubre de 2026

## 1. Notación

Notación del modelo MIP (ecuaciones 1 a 17):

| Categoría | Notación | Descripción |
| :--- | :--- | :--- |
| **Conjuntos** | $E$ | Eventos académicos. |
| | $R$ | Salones ($R_{\text{fis}}$: físicos; $R_{\text{virt}}$: virtual). |
| | $T$ | Franjas horarias semanales ($T = \{1, \dots, 86\}$). |
| | $D$ | Días hábiles ($D = \{d_1, \dots, d_6\}$, lunes a sábado). |
| | $T_d$ | Franjas horarias del día $d \in D$. |
| | $T_{\text{jue}}$ | Franjas del jueves (campus cerrado, 100% virtual). |
| | $T_{\text{sab}}$ | Franjas del sábado. |
| | $T_{\text{alm}}$ | Franjas de almuerzo (12:00–13:00). |
| | $T_{\text{reg}}$ | Franjas sin almuerzo ($T_{\text{reg}} = T \setminus T_{\text{alm}}$). |
| | $K, S, P, C$ | Currículos ($K$), secciones ($S$), profesores ($P$) y cursos ($C$). |
| **Subconjuntos** | $E_p, E_s, E_c, E_k$ | Eventos del docente $p$, sección $s$, curso $c$ o currículo $k$. |
| | $E_{k,c}$ | Eventos del curso $c$ en currículo $k$. |
| | $S_{k,c}$ | Secciones del curso $c$ en currículo $k$. |
| | $R_e, R_s$ | Salones compatibles por aforo ($CAP_r \ge Alumno_s$) y equipamiento ($Req_{s,f} \le Tiene_{r,f}$). |
| | $T_p$ | Franjas de disponibilidad del profesor $p$. |
| | $T_e$ | Franjas operativas del evento $e$ ($T_{\text{jue}}$ si virtual; $T \setminus T_{\text{jue}}$ si presencial). |
| | $T_{e,p}$ | Franjas factibles del evento $e$ con docente $p$ ($T_{e,p} = T_e \cap T_p$). |
| | $T_e^{\text{ini}}$ | Inicios válidos del evento $e$ sin desborde de jornada. |
| | $H_{e,t}$ | Inicios $\tau \in T_e^{\text{ini}}$ que cubren la franja $t$ ($\tau \le t < \tau + Dur_e$). |
| **Parámetros** | $Dur_e$ | Duración del evento $e$ en franjas consecutivas. |
| | $\vert S_{k,c} \vert$ | Cantidad de secciones del curso $c$ en currículo $k$. |
| | $W_A, W_E, W_{\text{jue}}, W_{\text{sab}}, W_V$ | Pesos de penalizaciones blandas (detallados en Sección 4). |
| **Variables** | $x_{e,r,t} \in \{0, 1\}$ | 1 si el evento $e$ se dicta en salón $r$ en franja $t$. |
| | $y_{e,r,t} \in \{0, 1\}$ | 1 si el evento $e$ inicia en salón $r$ en franja $t$. |
| | $w_{s,r} \in \{0, 1\}$ | 1 si la sección $s$ usa el aula $r$. |
| | $u_{p,t} \in \{0, 1\}$ | 1 si el profesor $p$ dicta clase en franja $t$. |
| | $gap_{p,t} \in [0, 1]$ | 1 si la franja $t$ es ventana ociosa del docente $p$. |
| | $v_{c,i} \ge 0$ | Infracción de espaciado del curso $c$ entre días $d_i$ y $d_{i+1}$. |
| | $P_{\text{alm}}, P_{\text{jue}}, P_{\text{sab}}$ | Penalizaciones por uso de almuerzo, jueves y sábado. |
| | $P_{\text{esp}}, P_{\text{vent}}$ | Penalizaciones por falta de espaciado y ventanas docentes. |

---

## 2. Restricciones Duras

### 2.1 Exclusividad docente por franja (1)
$$\sum_{e \in E_p} \sum_{r \in R_e} x_{e,r,t} \le 1 \quad \forall p \in P, \; \forall t \in T_p \tag{1}$$

### 2.2 Jornada máxima diaria docente (2)
$$\sum_{e \in E_p} \sum_{r \in R_e} \sum_{t \in T_d \cap T_p} x_{e,r,t} \le 8 \quad \forall p \in P, \; \forall d \in D \tag{2}$$

### 2.3 Cobertura total de duración de evento (3)
$$\sum_{r \in R_e} \sum_{t \in T_{e,p(e)}} x_{e,r,t} = Dur_e \quad \forall e \in E \tag{3}$$

### 2.4 Unicidad de inicio semanal (4)
$$\sum_{r \in R_e} \sum_{t \in T_e^{\text{ini}}} y_{e,r,t} = 1 \quad \forall e \in E \tag{4}$$

### 2.5 Continuidad de bloque lectivo (5)
$$x_{e,r,t} = \sum_{\tau \in H_{e,t}} y_{e,r,\tau} \quad \forall e \in E, \; \forall r \in R_e, \; \forall t \in T_{e,p(e)} \tag{5}$$

### 2.6 Exclusividad de salones físicos (6)
$$\sum_{e \in E} x_{e,r,t} \le 1 \quad \forall r \in R_{\text{fis}}, \; \forall t \in T \setminus T_{\text{jue}} \tag{6}$$

### 2.7 Estabilidad espacial de sección (7–8)
$$\sum_{t \in T_{e,p(e)}} x_{e,r,t} \le Dur_e \cdot w_{s,r} \quad \forall s \in S, \; \forall e \in E_s, \; \forall r \in R_s \tag{7}$$

$$\sum_{r \in R_s} w_{s,r} \le 2 \quad \forall s \in S \tag{8}$$

### 2.8 Oferta curricular sin conflicto de sección (9)
$$\sum_{e \in E_{k,c}} \sum_{r \in R_e} x_{e,r,t} + \sum_{r' \in R_{e'}} x_{e',r',t} \le |S_{k,c}| \quad \forall k \in K, \; \forall c \in C_k \mid |S_{k,c}| > 1, \; \forall e' \in E_k \setminus E_{k,c}, \; \forall t \in T \tag{9}$$

---

## 3. Restricciones Blandas

### 3.1 Horario de Almuerzo (10)
$$P_{\text{almuerzo}} = \sum_{e \in E} \sum_{r \in R_e} \sum_{t \in T_{\text{alm}}} x_{e,r,t} \tag{10}$$

### 3.2 Espaciado Pedagógico (11–12)
$$\sum_{e \in E_c} \sum_{r \in R_e} \sum_{t \in T_{d_i}} y_{e,r,t} + \sum_{e \in E_c} \sum_{r \in R_e} \sum_{t \in T_{d_{i+1}}} y_{e,r,t} \le 1 + v_{c, i} \quad \forall c \in C, \; \forall i \in \{1, \dots, |D|-1\} \tag{11}$$

$$P_{\text{espaciado}} = \sum_{c \in C} \sum_{i=1}^{|D|-1} v_{c, i} \tag{12}$$

### 3.3 Preferencia Temporal (13–14)
$$P_{\text{jueves}} = \sum_{e \in E} \sum_{r \in R_e} \sum_{t \in T_{\text{jue}}} x_{e,r,t} \tag{13}$$

$$P_{\text{sabado}} = \sum_{e \in E} \sum_{r \in R_e} \sum_{t \in T_{\text{sab}}} x_{e,r,t} \tag{14}$$

### 3.4 Compacidad Docente / Ventanas (15–16)
Sea $u_{p,t} = \sum_{e \in E_p} \sum_{r \in R_e} x_{e,r,t}$ la actividad lectiva del docente $p$ en la franja $t$:

$$gap_{p,t} \ge u_{p,t_1} + u_{p,t_2} - 1 - u_{p,t} \quad \forall p \in P, \; \forall d \in D, \; \forall t_1, t, t_2 \in T_d \cap T_{\text{reg}} \text{ con } t_1 < t < t_2 \tag{15}$$

$$P_{\text{ventanas}} = \sum_{p \in P} \sum_{t \in T_{\text{reg}}} gap_{p,t} \tag{16}$$

---

## 4. Función Objetivo (17)

$$\min Z = W_A \cdot P_{\text{almuerzo}} + W_E \cdot P_{\text{espaciado}} + W_{\text{jue}} \cdot P_{\text{jueves}} + W_{\text{sab}} \cdot P_{\text{sabado}} + W_V \cdot P_{\text{ventanas}} \tag{17}$$

Pesos estándar: $W_A = 1$ (almuerzo), $W_E = 10$ (espaciado), $W_{\text{jue}} = 1$ (jueves virtual), $W_{\text{sab}} = 3$ (sábado) y $W_V = 2$ (ventanas ociosas).