# Formulación Matemática

**Autor:** Marcelo Angeles  
**Referencia de Formato:** Estándar de notación por subconjuntos indexados (*Computational Management Science*, Ozkan et al., 2025; *European Journal of Operational Research*, Daskalaki et al., 2004).

---

## 1. Notación

La **Tabla 1** define los conjuntos, parámetros y variables de decisión del modelo de Programación Lineal Entera Mixta (MIP). Todo símbolo que aparece en las ecuaciones (1) a (17) está declarado en esta tabla; los parámetros de entrada del problema que solo participan en la construcción de los subconjuntos indexados (aforo, equipamiento, disponibilidad) se describen textualmente en la definición de cada subconjunto.

### Tabla 1: Notación del Modelo

| Categoría | Notación | Descripción |
| :--- | :--- | :--- |
| **Conjuntos** | $E$ | Conjunto de eventos académicos. |
| | $R$ | Conjunto de salones ($R_{\text{fis}}$: aulas físicas; $R_{\text{virt}}$: salones virtuales). |
| | $T$ | Franjas horarias semanales ($T = \{1, 2, \dots, 86\}$). |
| | $D$ | Días hábiles ($D = \{d_1, d_2, \dots, d_6\}$, lunes a sábado). |
| | $T_d$ | Franjas horarias del día $d \in D$. |
| | $T_{\text{jue}}$ | Franjas del jueves (campus físico cerrado, modalidad 100% virtual). |
| | $T_{\text{sab}}$ | Franjas del sábado. |
| | $T_{\text{alm}}$ | Franjas del horario institucional de almuerzo (13:00–14:00). |
| | $T_{\text{reg}}$ | Franjas lectivas regulares ($T_{\text{reg}} = T \setminus T_{\text{alm}}$). |
| | $K, S, P, C$ | Currículos ($K$), secciones ($S$), profesores ($P$) y cursos ($C$). |
| **Subconjuntos** | $E_p, E_s, E_c, E_k$ | Eventos del docente $p$, sección $s$, curso $c$ o currículo $k$. |
| | $E_{k,c}$ | Eventos del curso $c$ dentro del currículo $k$. |
| | $S_{k,c}$ | Secciones que dictan el curso $c$ en el currículo $k$. |
| | $R_e, R_s$ | Salones compatibles con el evento $e$ o la sección $s$, filtrados por aforo ($CAP_r \ge Alumno_s$) y requerimientos técnicos ($Req_{s,f} \le Tiene_{r,f}, \; \forall f \in F$). |
| | $T_p$ | Franjas de disponibilidad laboral declarada del profesor $p$. |
| | $T_e$ | Franjas operativas del evento $e$ ($T_{\text{jue}}$ si virtual, $T \setminus T_{\text{jue}}$ si presencial). |
| | $T_{e,p}$ | Franjas factibles del evento $e$ con el docente $p$ ($T_{e,p} = T_e \cap T_p$). |
| | $T_e^{\text{ini}}$ | Franjas de inicio admisibles del evento $e$ sin desbordar la jornada diaria. |
| | $H_{e,t}$ | Inicios $\tau \in T_e^{\text{ini}}$ que cubren la franja $t$ ($\tau \le t < \tau + Dur_e$). |
| **Parámetros** | $Dur_e$ | Duración del evento $e$ en franjas horarias consecutivas ($Dur_e \ge 1$). |
| | $\vert S_{k,c} \vert$ | Número de secciones del curso $c$ en el currículo $k$. |
| | $W_A, W_E, W_G$ | Pesos: Almuerzo ($W_A=1$), Espaciado ($W_E=10$), Huecos ($W_G=2$). |
| | $W_{\text{jue}}, W_{\text{sab}}$ | Pesos: Jueves ($W_{\text{jue}}=1$), Sábado ($W_{\text{sab}}=3$). |
| **Variables** | $x_{e,r,t} \in \{0, 1\}$ | 1 si el evento $e$ se imparte en el salón $r$ durante la franja $t$; 0 en caso contrario. |
| | $y_{e,r,t} \in \{0, 1\}$ | 1 si el evento $e$ inicia su bloque en el salón $r$ en la franja $t$; 0 en caso contrario. |
| | $w_{s,r} \in \{0, 1\}$ | 1 si la sección $s$ utiliza el aula $r$ al menos una vez en la semana; 0 en caso contrario. |
| | $u_{p,t} \in \{0, 1\}$ | 1 si el profesor $p$ dicta clase en la franja $t$; 0 en caso contrario. |
| | $gap_{p,t} \in [0, 1]$ | 1 si la franja $t$ es una ventana ociosa del docente $p$; 0 en caso contrario. |
| | $v_{c,i} \ge 0$ | Infracción de espaciado del curso $c$ entre los días $d_i$ y $d_{i+1}$. |
| | $P_{\text{almuerzo}}, P_{\text{jueves}}, P_{\text{sabado}}$ | Penalizaciones por uso de franjas de almuerzo, jueves y sábado. |
| | $P_{\text{espaciado}}, P_{\text{huecos}}$ | Penalizaciones por falta de espaciado y ventanas docentes. |

---

## 2. Restricciones Duras

### 2.1. Recursos Docentes

La restricción (1) impide que un docente dicte más de una clase simultáneamente:
$$\sum_{e \in E_p} \sum_{r \in R_e} x_{e,r,t} \le 1 \quad \forall p \in P, \; \forall t \in T_p \tag{1}$$

La restricción (2) limita a 8 horas lectivas la jornada diaria de cada profesor:
$$\sum_{e \in E_p} \sum_{r \in R_e} \sum_{t \in T_d \cap T_p} x_{e,r,t} \le 8 \quad \forall p \in P, \; \forall d \in D \tag{2}$$

### 2.2. Cobertura y Continuidad de Bloques

La restricción (3) asegura la cobertura total de cada evento conforme a su duración:
$$\sum_{r \in R_e} \sum_{t \in T_{e,p(e)}} x_{e,r,t} = Dur_e \quad \forall e \in E \tag{3}$$

La restricción (4) exige un único inicio semanal por evento:
$$\sum_{r \in R_e} \sum_{t \in T_e^{\text{ini}}} y_{e,r,t} = 1 \quad \forall e \in E \tag{4}$$

La restricción (5) vincula la ocupación de cada franja con los inicios que la cubren, garantizando continuidad y no fragmentación:
$$x_{e,r,t} = \sum_{\tau \in H_{e,t}} y_{e,r,\tau} \quad \forall e \in E, \; \forall r \in R_e, \; \forall t \in T_{e,p(e)} \tag{5}$$

### 2.3. Infraestructura y Estabilidad Espacial

La restricción (6) garantiza la exclusividad de las aulas físicas:
$$\sum_{e \in E} x_{e,r,t} \le 1 \quad \forall r \in R_{\text{fis}}, \; \forall t \in T \setminus T_{\text{jue}} \tag{6}$$

Las restricciones (7) y (8) vinculan el uso de aulas y limitan a 2 salones distintos por sección:
$$\sum_{t \in T_{e,p(e)}} x_{e,r,t} \le Dur_e \cdot w_{s,r} \quad \forall s \in S, \; \forall e \in E_s, \; \forall r \in R_s \tag{7}$$

$$\sum_{r \in R_s} w_{s,r} \le 2 \quad \forall s \in S \tag{8}$$

### 2.4. Oferta Curricular

La restricción (9) garantiza que al menos una sección de cada curso quede libre de solapamientos dentro del currículo:
$$\sum_{e \in E_{k,c}} \sum_{r \in R_e} x_{e,r,t} + \sum_{r' \in R_{e'}} x_{e',r',t} \le |S_{k,c}| \quad \forall k \in K, \; \forall c \in C_k \mid |S_{k,c}| > 1, \; \forall e' \in E_k \setminus E_{k,c}, \; \forall t \in T \tag{9}$$

---

## 3. Restricciones Blandas

### 3.1. Horario de Almuerzo

$$P_{\text{almuerzo}} = \sum_{e \in E} \sum_{r \in R_e} \sum_{t \in T_{\text{alm}}} x_{e,r,t} \tag{10}$$

### 3.2. Espaciado Pedagógico

$$\sum_{e \in E_c} \sum_{r \in R_e} \sum_{t \in T_{d_i}} y_{e,r,t} + \sum_{e \in E_c} \sum_{r \in R_e} \sum_{t \in T_{d_{i+1}}} y_{e,r,t} \le 1 + v_{c, i} \quad \forall c \in C, \; \forall i \in \{1, \dots, |D|-1\} \tag{11}$$

$$P_{\text{espaciado}} = \sum_{c \in C} \sum_{i=1}^{|D|-1} v_{c, i} \tag{12}$$

### 3.3. Preferencia Temporal (Jueves y Sábado)

$$P_{\text{jueves}} = \sum_{e \in E} \sum_{r \in R_e} \sum_{t \in T_{\text{jue}}} x_{e,r,t} \tag{13}$$

$$P_{\text{sabado}} = \sum_{e \in E} \sum_{r \in R_e} \sum_{t \in T_{\text{sab}}} x_{e,r,t} \tag{14}$$

### 3.4. Compacidad Docente (Ventanas / Huecos)

Sea $u_{p,t} = \sum_{e \in E_p} \sum_{r \in R_e} x_{e,r,t}$ la indicadora de dictado del docente $p$:

$$gap_{p,t} \ge u_{p,t_1} + u_{p,t_2} - 1 - u_{p,t} \quad \forall p \in P, \; \forall d \in D, \; \forall t_1, t, t_2 \in T_d \cap T_{\text{reg}} \text{ con } t_1 < t < t_2 \tag{15}$$

$$P_{\text{huecos}} = \sum_{p \in P} \sum_{t \in T_{\text{reg}}} gap_{p,t} \tag{16}$$

---

## 4. Función Objetivo

$$\min Z = W_A \cdot P_{\text{almuerzo}} + W_E \cdot P_{\text{espaciado}} + W_{\text{jue}} \cdot P_{\text{jueves}} + W_{\text{sab}} \cdot P_{\text{sabado}} + W_G \cdot P_{\text{huecos}} \tag{17}$$