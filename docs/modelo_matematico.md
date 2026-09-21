# Formulación Matemática

**Autor:** Marcelo Angeles  
**Referencia de Formato:** Estándar de notación y modelado por subconjuntos indexados (*Computational Management Science*, Ozkan et al., 2025; *European Journal of Operational Research*, Daskalaki et al., 2004).

---

## 1. Definición de Notación

La **Tabla 1** reúne la totalidad de conjuntos primarios, subconjuntos indexados precalculados, parámetros y variables de decisión que conforman el modelo de Programación Lineal Entera Mixta (MIP).

### Tabla 1: Definición de Notación del Modelo

| Categoría | Notación | Descripción Formal |
| :--- | :--- | :--- |
| **Conjuntos Primarios** | $E$ | Conjunto universal de eventos académicos. |
| | $R$ | Conjunto universal de salones ($R_{\text{fis}}$: aulas físicas; $R_{\text{virt}}$: salones virtuales). |
| | $T$ | Conjunto de franjas horarias semanales discretas ($T = \{1, 2, \dots, 86\}$). |
| | $D$ | Secuencia ordenada de días hábiles ($D = \{d_1, d_2, \dots, d_6\}$, lunes a sábado). |
| | $T_d$ | Conjunto de franjas horarias pertenecientes a la jornada $d \in D$. |
| | $T_{\text{jue}}$ | Franjas del día jueves (campus presencial cerrado / modalidad 100% remota). |
| | $T_{\text{sab}}$ | Franjas del día sábado (fin de semana institucional). |
| | $T_{\text{alm}}$ | Franjas del horario institucional de almuerzo (13:00 a 14:00 horas). |
| | $T_{\text{reg}}$ | Franjas lectivas regulares fuera del almuerzo ($T_{\text{reg}} = T \setminus T_{\text{alm}}$). |
| | $K$ | Conjunto de currículos o mallas de estudio sugeridas. |
| | $S$ | Conjunto de secciones académicas de estudiantes. |
| | $P$ | Conjunto de profesores activos. |
| | $C$ | Conjunto de cursos o asignaturas. |
| **Subconjuntos Indexados** | $E_p, E_s, E_c, E_k$ | Subconjunto de eventos correspondientes al docente $p$, sección $s$, curso $c$ o currículo $k$. |
| | $E_{k,c}$ | Subconjunto de eventos del curso $c$ que integran el currículo $k$. |
| | $S_{k,c}$ | Secciones que dictan el curso $c$ en el currículo $k$. |
| | $R_e, R_s$ | Salones compatibles con el evento $e$ o sección $s$ (aforo $CAP_r \ge Alumno_s$ y equipamiento). |
| | $T_p$ | Franjas horarias en las que el profesor $p$ tiene disponibilidad laboral declarada. |
| | $T_e$ | Franjas operativas del evento $e$ ($T_{\text{jue}}$ si $r \in R_{\text{virt}}$, o $T \setminus T_{\text{jue}}$ si $r \in R_{\text{fis}}$). |
| | $T_{e,p}$ | Franjas factibles para el evento $e$ con el docente $p$ ($T_{e,p} = T_e \cap T_p$). |
| | $T_e^{\text{ini}}$ | Franjas de inicio admisibles para el evento $e$ sin desbordar el término de la jornada diaria. |
| | $H_{e,t}$ | Franjas de inicio $\tau \in T_e^{\text{ini}}$ que cubren activamente la franja $t$ ($\tau \le t < \tau + Dur_e$). |
| **Parámetros** | $Dur_e$ | Duración del evento $e$, cuantificada en franjas horarias consecutivas ($Dur_e \ge 1$). |
| | $\vert S_{k,c} \vert$ | Número de secciones disponibles del curso $c$ dentro del currículo $k$. |
| | $W_A, W_E, W_G$ | Ponderaciones: Almuerzo ($W_A=1$), Espaciado ($W_E=10$), Huecos docentes ($W_G=2$). |
| | $W_{\text{jue}}, W_{\text{sab}}$ | Ponderaciones: Jueves virtual ($W_{\text{jue}}=1$) y Sábado institucional ($W_{\text{sab}}=3$). |
| **Variables de Decisión** | $x_{e,r,t} \in \{0, 1\}$ | Vale 1 si el evento $e$ se imparte en el salón $r$ durante la franja $t$; 0 en caso contrario. |
| | $y_{e,r,t} \in \{0, 1\}$ | Vale 1 si el evento $e$ arranca su bloque en el salón $r$ en la franja $t$; 0 en caso contrario. |
| | $w_{s,r} \in \{0, 1\}$ | Vale 1 si la sección $s$ utiliza el aula física $r$ al menos una vez en la semana; 0 en caso contrario. |
| | $u_{p,t} \in \{0, 1\}$ | Variable indicadora; vale 1 si el profesor $p$ dicta clase en la franja $t$; 0 en caso contrario. |
| | $gap_{p,t} \in [0, 1]$ | Variable continua; vale 1 si la franja regular $t$ representa una ventana u hora muerta ociosa. |
| | $v_{c,i} \ge 0$ | Infracción de espaciado pedagógico del curso $c$ entre los días consecutivos $d_i$ y $d_{i+1}$. |
| | $P_{\text{almuerzo}}, P_{\text{jueves}}, P_{\text{sabado}}$ | Variables enteras no negativas de conteo de penalizaciones blandas institucionales. |
| | $P_{\text{espaciado}}, P_{\text{huecos}}$ | Variables no negativas de costo por falta de espaciado pedagógico y ventanas docentes. |

---

## 2. Restricciones Duras (*Hard Constraints*)

### 2.1. Gestión de Recursos Docentes

La restricción (1) garantiza que un docente no dicte simultáneamente más de una clase en una misma franja horaria dentro de su disponibilidad:
$$\sum_{e \in E_p} \sum_{r \in R_e} x_{e,r,t} \le 1 \quad \forall p \in P, \; \forall t \in T_p \tag{1}$$

La restricción (2) limita a un máximo de 8 franjas horarias lectivas la jornada diaria asignada a cada profesor:
$$\sum_{e \in E_p} \sum_{r \in R_e} \sum_{t \in T_d \cap T_p} x_{e,r,t} \le 8 \quad \forall p \in P, \; \forall d \in D \tag{2}$$

### 2.2. Cobertura Temporal y Continuidad de Bloques

La restricción (3) asegura la cobertura total de los eventos conforme a su duración obligatoria:
$$\sum_{r \in R_e} \sum_{t \in T_{e,p(e)}} x_{e,r,t} = Dur_e \quad \forall e \in E \tag{3}$$

La restricción (4) exige que cada evento posea exactamente un único punto de inicio semanal:
$$\sum_{r \in R_e} \sum_{t \in T_e^{\text{ini}}} y_{e,r,t} = 1 \quad \forall e \in E \tag{4}$$

La restricción (5) propaga la ocupación secuencial de las franjas horarias contiguas a partir del instante de inicio:
$$x_{e,r,t} = \sum_{\tau \in H_{e,t}} y_{e,r,\tau} \quad \forall e \in E, \; \forall r \in R_e, \; \forall t \in T_{e,p(e)} \tag{5}$$

### 2.3. Infraestructura y Estabilidad Espacial

La restricción (6) garantiza la exclusividad de las aulas físicas presenciales en cualquier franja horaria hábil:
$$\sum_{e \in E} x_{e,r,t} \le 1 \quad \forall r \in R_{\text{fis}}, \; \forall t \in T \setminus T_{\text{jue}} \tag{6}$$

Las restricciones (7) y (8) vinculan el uso de aulas físicas y restringen la asignación semanal de cada sección a un máximo de dos salones distintos:
$$\sum_{t \in T_{e,p(e)}} x_{e,r,t} \le Dur_e \cdot w_{s,r} \quad \forall s \in S, \; \forall e \in E_s, \; \forall r \in R_s \tag{7}$$

$$\sum_{r \in R_s} w_{s,r} \le 2 \quad \forall s \in S \tag{8}$$

### 2.4. Oferta Curricular y Matrícula Estudiantil

La restricción (9) garantiza que, para cada currículo o bloque de matrícula sugerido, exista al menos una sección de cada asignatura completamente libre de solapamientos horarios con el resto de cursos de la misma ruta académica:
$$\sum_{e \in E_{k,c}} \sum_{r \in R_e} x_{e,r,t} + \sum_{r' \in R_{e'}} x_{e',r',t} \le |S_{k,c}| \quad \forall k \in K, \; \forall c \in C_k \mid |S_{k,c}| > 1, \; \forall e' \in E_k \setminus E_{k,c}, \; \forall t \in T \tag{9}$$

---

## 3. Restricciones Blandas (*Soft Constraints*)

### 3.1. Respeto al Horario de Almuerzo

La ecuación (10) contabiliza la cantidad de franjas horarias de clase asignadas durante el intervalo de almuerzo:
$$P_{\text{almuerzo}} = \sum_{e \in E} \sum_{r \in R_e} \sum_{t \in T_{\text{alm}}} x_{e,r,t} \tag{10}$$

### 3.2. Espaciado Pedagógico de Cursos

Las ecuaciones (11) y (12) penalizan la programación de sesiones de clase pertenecientes a un mismo curso en días consecutivos ($d_i$ y $d_{i+1}$):
$$\sum_{e \in E_c} \sum_{r \in R_e} \sum_{t \in T_{d_i}} y_{e,r,t} + \sum_{e \in E_c} \sum_{r \in R_e} \sum_{t \in T_{d_{i+1}}} y_{e,r,t} \le 1 + v_{c, i} \quad \forall c \in C, \; \forall i \in \{1, \dots, |D|-1\} \tag{11}$$

$$P_{\text{espaciado}} = \sum_{c \in C} \sum_{i=1}^{|D|-1} v_{c, i} \tag{12}$$

### 3.3. Preferencia Temporal Institucional (Jueves y Sábado)

Las ecuaciones (13) y (14) cuantifican las franjas horarias asignadas en días con políticas de desincentivo operativo:
$$P_{\text{jueves}} = \sum_{e \in E} \sum_{r \in R_e} \sum_{t \in T_{\text{jue}}} x_{e,r,t} \tag{13}$$

$$P_{\text{sabado}} = \sum_{e \in E} \sum_{r \in R_e} \sum_{t \in T_{\text{sab}}} x_{e,r,t} \tag{14}$$

### 3.4. Compacidad de la Jornada Docente (Ventanas / Huecos)

Sea $u_{p,t} = \sum_{e \in E_p} \sum_{r \in R_e} x_{e,r,t}$ la variable indicadora de dictado del docente $p$. Las restricciones (15) y (16) formulan, mediante el esquema canónico de tripletas temporales, la penalización por franjas ociosas intercaladas entre la primera y la última clase del día:
$$gap_{p,t} \ge u_{p,t_1} + u_{p,t_2} - 1 - u_{p,t} \quad \forall p \in P, \; \forall d \in D, \; \forall t_1, t, t_2 \in T_d \cap T_{\text{reg}} \text{ con } t_1 < t < t_2 \tag{15}$$

$$P_{\text{huecos}} = \sum_{p \in P} \sum_{t \in T_{\text{reg}}} gap_{p,t} \tag{16}$$

---

## 4. Función Objetivo Consolidada

La función objetivo (17) minimiza el costo total ponderado de las penalizaciones blandas, condicionada a la estricta factibilidad de las restricciones duras (1) a (9):

$$\min Z = W_A \cdot P_{\text{almuerzo}} + W_E \cdot P_{\text{espaciado}} + W_{\text{jue}} \cdot P_{\text{jueves}} + W_{\text{sab}} \cdot P_{\text{sabado}} + W_G \cdot P_{\text{huecos}} \tag{17}$$