# Formulación Matemática

**Autor:** Marcelo Angeles

## Definiciones

* **Curso:** Representa la asignatura general o programa de estudio. Actúa como agrupador lógico de los eventos que pertenecen a una misma materia, lo que permite al modelo imponer reglas de espaciado (días de descanso) entre las sesiones de un mismo curso. Se asume que cada curso ya se encuentra dividido en una o más secciones.
* **Sección:** Corresponde a un grupo específico de estudiantes matriculados en un curso. Constituye la unidad académica que determina los parámetros físicos del problema, tales como la cantidad de alumnos inscritos y los requerimientos de infraestructura del salón.
* **Evento:** Representa la unidad mínima de programación generada por una sección. Cada evento posee una duración preestablecida (medida en franjas horarias consecutivas) y un profesor previamente asignado. Un evento se convierte en una "clase" programada únicamente cuando el modelo le asigna coordenadas definitivas de espacio (salón) y tiempo (franja horaria).
* **Salón:** Corresponde al recurso de espacio donde se imparte un evento. Puede tratarse de un espacio físico, sujeto a límites de capacidad y exclusividad de uso, o de un espacio virtual, cuya capacidad es ilimitada y cuya operación se restringe al día de cierre del campus. La naturaleza del salón (físico o virtual) determina los días en los que se encuentra operativo.
* **Franja horaria:** Equivale a cada uno de los períodos de tiempo indivisibles definidos por la institución. Todas las franjas poseen la misma duración y se asignan de forma secuencial a lo largo de cada día de la semana.
* **Profesor:** Corresponde al docente responsable de dictar un evento. Cada profesor cuenta con una matriz de disponibilidad horaria que establece las franjas en las cuales puede ser programado.
* **Currículo:** Representa un grupo de cursos (ruta sugerida o bloque de malla curricular) que un estudiante ideal debería cursar de manera simultánea en un mismo ciclo. El modelo utiliza los currículos para garantizar que, dentro de cada ruta, exista al menos una sección de cada curso que no entre en conflicto horario con los demás cursos de esa misma ruta.
* **Instanciación dispersa:** Estrategia de construcción del modelo en la cual las variables de decisión y sus restricciones asociadas se crean únicamente para las combinaciones que resultan factibles según los datos de entrada, en lugar de considerar todas las combinaciones posibles. Esta estrategia reduce significativamente el tamaño del problema.

## Definición de conjuntos

A continuación se presenta la colección de conjuntos que definen el espacio del problema de programación de horarios:

* **Conjunto global de eventos** $E$: Agrupa todas las unidades mínimas de programación generadas por las secciones.
* **Conjunto global de salones** $R$: Comprende todos los espacios disponibles para impartir eventos.
* **Subconjunto de salones virtuales** $R_{\text{virtual}} \subseteq R$: Contiene los salones que operan exclusivamente de manera remota.
* **Conjunto global de franjas horarias** $T$: Reúne todos los bloques de tiempo indivisibles en los cuales la institución programa sus actividades.
* **Conjunto secuencial de días** $D$: Tupla ordenada que agrupa las franjas horarias según el día de la semana al que pertenecen: $D = (d_1, d_2, \dots, d_{|D|})$.
* **Día de cierre físico** $d_{\text{jue}}$: Elemento distinguido de $D$ que identifica el día en el cual el campus no opera de manera presencial. Las franjas horarias correspondientes a este día se denotan como $T_{d_{\text{jue}}}$.
* **Conjunto de currículos** $K$: Representa las rutas sugeridas o bloques de matrícula que agrupan cursos afines.
* **Conjunto de secciones** $S$: Contiene las unidades operativas de estudiantes matriculados en un curso específico.
* **Conjunto de profesores activos** $P$: Incluye al personal docente vinculado al dictado de los eventos en $E$. Se obtiene directamente a partir de los datos de los eventos.
* **Conjunto de características** $F$: Reúne todos los atributos de infraestructura relevantes para la asignación (por ejemplo: "mesa", "pc", "deep_learning").

### Agrupaciones relacionales

* **Conjunto de agrupaciones curso-sección** $C$: Conjunto de índices que identifican a cada curso dentro de una sección específica. Para cada grupo $c \in C$, se define el conjunto de eventos asociados como $E_c \subseteq E$, lo cual permite aplicar las reglas de espaciado temporal entre las sesiones del mismo curso.
* **Relación currículo-evento** $\{E_k\}_{k \in K}$: Familia de subconjuntos de $E$ que componen la ruta curricular $k \in K$.
* **Relación sección-evento** $\{E_s\}_{s \in S}$: Familia de subconjuntos de $E$ que pertenecen a la sección $s \in S$.
* **Relación profesor-evento** $\{E_p\}_{p \in P}$: Familia de subconjuntos de $E$ dictados por el profesor $p \in P$.
* **Franjas por día** $\{T_d\}_{d \in D}$: Familia de subconjuntos de $T$ correspondientes al día $d \in D$.

### Reducción de dominio (dominios factibles)

Con el propósito de mantener el modelo eficiente en términos de memoria y tiempo de resolución, las variables de decisión no se crean para todas las combinaciones posibles de eventos, salones y franjas. En su lugar, se definen previamente los siguientes subconjuntos de combinaciones válidas, con base en la capacidad de los salones ($CAP_r$), la cantidad de alumnos ($Alumno_s$), la infraestructura disponible ($Tiene_{r,f}$) y requerida ($Req_{s,f}$), las restricciones del día de cierre y la disponibilidad del profesor ($Disp_{p,t}$):

* **Combinaciones válidas de sección-salón ($Valid\_SR \subseteq S \times R$):**
Contiene los pares factibles de sección $s$ y salón $r$, seleccionando únicamente aquellos salones cuya capacidad iguala o supera la cantidad de alumnos de la sección y que poseen todas las características de infraestructura requeridas:

$$Valid\_SR = \{(s, r) \in S \times R \mid CAP_r \geq Alumno_s \land \forall f \in F\; (Req_{s,f} \leq Tiene_{r,f})\}$$

* **Combinaciones válidas de evento-salón-franja ($Valid\_ERT \subseteq E \times R \times T$):**
Contiene las combinaciones de evento $e$, salón $r$ y franja $t$ que resultan factibles tanto temporal como operativamente. Se construye a partir de $Valid\_SR$ e incorpora adicionalmente la restricción del día de cierre y la disponibilidad horaria del profesor asignado al evento:

$$Valid\_ERT = \{(e, r, t) \in E \times R \times T \mid \exists s \in S : (s, r) \in Valid\_SR \land e \in E_s \land t \in T_r \land Disp_{p(e),\, t} = 1\}$$

Donde $p(e)$ denota al profesor asignado al evento $e$, y el conjunto de franjas operativas $T_r$ depende de la naturaleza del salón:

$$T_r = \begin{cases} T_{d_{\text{jue}}} & \text{si } r \in R_{\text{virtual}} \\ T \setminus T_{d_{\text{jue}}} & \text{si } r \notin R_{\text{virtual}} \end{cases}$$

### Subconjuntos derivados de la reducción

A partir de $Valid\_ERT$, se derivan los siguientes conjuntos auxiliares que permiten acotar el dominio de las restricciones de la Sección 9:

* **Franjas factibles por evento** $T^{\text{fact}}_e$: Conjunto de franjas horarias en las que el evento $e$ puede ser programado en al menos un salón:

$$T^{\text{fact}}_e = \{t \in T \mid \exists r \in R : (e, r, t) \in Valid\_ERT\}$$

* **Cursos del currículo** $C_k$: Conjunto de cursos distintos cuyos eventos participan en el currículo $k$:

$$C_k = \{c \mid \exists e \in E_k : SECCION\_CURSO(EVENTO\_SECCION(e)) = c\}$$

* **Eventos del curso en el currículo** $E_{k,c}$: Subconjunto de eventos del currículo $k$ que pertenecen al curso $c$:

$$E_{k,c} = \{e \in E_k \mid SECCION\_CURSO(EVENTO\_SECCION(e)) = c\}$$

* **Secciones del curso en el currículo** $S_{k,c}$: Conjunto de secciones distintas que ofrecen el curso $c$ dentro del currículo $k$:

$$S_{k,c} = \{EVENTO\_SECCION(e) \mid e \in E_{k,c}\}$$

## Parámetros

Se definen los siguientes parámetros del modelo:

* **Capacidad del salón** $CAP_r$: Número máximo de estudiantes que el salón $r \in R$ puede albergar simultáneamente.
* **Cantidad de alumnos** $Alumno_s$: Número de estudiantes matriculados en la sección $s \in S$.
* **Requerimiento de la sección** $Req_{s,f}$: Parámetro binario que vale 1 si la sección $s \in S$ requiere la característica de infraestructura $f \in F$, y 0 en caso contrario.
* **Característica del salón** $Tiene_{r,f}$: Parámetro binario que vale 1 si el salón $r \in R$ posee la característica $f \in F$, y 0 en caso contrario.
* **Disponibilidad del profesor** $Disp_{p,t}$: Parámetro binario que vale 1 si el profesor $p \in P$ se encuentra disponible para dictar clase en la franja horaria $t \in T$, y 0 en caso contrario.
* **Almuerzo** $Almuerzo_t$: Parámetro binario que vale 1 si la franja horaria $t \in T$ corresponde al período de almuerzo, y 0 en caso contrario.
* **Duración del evento** $Dur_e$: Número entero que indica cuántas franjas horarias consecutivas ocupa el evento $e \in E$.
* **Peso de penalización por almuerzo** $W_A$: Escalar abstracto que pondera la importancia de las clases programadas durante el período de almuerzo en la función objetivo.
* **Peso de penalización por espaciado** $W_E$: Escalar abstracto que pondera la importancia de las infracciones por sesiones dictadas en días consecutivos en la función objetivo.

## Variables de decisión

Las variables de decisión se crean exclusivamente sobre las combinaciones de los dominios factibles:

* **Asignación evento-salón-franja** $x_{e,r,t}$: Variable binaria que vale 1 si el evento $e$ se programa en el salón $r$ durante la franja $t$, y 0 en caso contrario.
* **Inicio del evento** $y_{e,r,t}$: Variable binaria que vale 1 si el evento $e$ comienza su bloque de franjas consecutivas en el salón $r$ durante la franja $t$, y 0 en caso contrario.
* **Uso de salón por sección** $w_{s,r}$: Variable binaria auxiliar que vale 1 si la sección $s$ utiliza el salón $r$ en al menos una franja durante la semana, y 0 en caso contrario.
* **Penalización por clases en almuerzo** $P_{\text{almuerzo}}$: Variable entera no negativa que acumula el total de franjas de clase programadas durante el período de almuerzo.
* **Infracción de espaciado por curso y día** $v_{\text{espaciado}, c, i}$: Variable entera no negativa que vale 1 (o más) si el curso $c$ se programa en días consecutivos $i$ e $i+1$, y 0 en caso contrario.
* **Penalización total por espaciado** $P_{\text{espaciado}}$: Variable entera no negativa que acumula el total de infracciones de espaciado temporal de sesiones.

### Dominio de las variables

$$ x_{e,r,t} \in \{0,1\} \quad \forall (e,r,t) \in Valid\_ERT $$

$$ y_{e,r,t} \in \{0,1\} \quad \forall (e,r,t) \in Valid\_ERT $$

$$ w_{s,r} \in \{0,1\} \quad \forall (s,r) \in Valid\_SR $$

$$ v_{\text{espaciado}, c, i} \ge 0 \quad \forall c \in C,\; \forall i \in \{1, \dots, |D|-1\} $$

$$ P_{\text{almuerzo}} \in \mathbb{Z}^{+} \cup \{0\} $$

$$ P_{\text{espaciado}} \ge 0 $$

> **Nota:** En todas las sumatorias que se presentan a continuación, si una combinación evaluada no pertenece al conjunto de combinaciones válidas correspondiente, la variable asociada no existe y se considera con valor 0. Esto evita la formulación de restricciones sobre variables inexistentes.

## Restricciones duras

### 1. Disponibilidad y no colisión del profesor

Garantiza que cada profesor no sea programado en más de una clase por franja horaria y que únicamente se le asignen franjas dentro de su disponibilidad declarada.

$$ \sum_{\substack{e \in E_p, r \in R \\ (e,r,t) \in Valid\_ERT}} x_{e,r,t} \leq Disp_{p,t} \quad \forall p \in P,\; \forall t \in T $$

### 2. Carga diaria máxima del profesor

Limita la cantidad total de franjas de clase que un profesor puede impartir en un mismo día a un máximo de 8.

$$ \sum_{\substack{e \in E_p, r \in R \\ t \in T_d \\ (e,r,t) \in Valid\_ERT}} x_{e,r,t} \leq 8 \quad \forall p \in P,\; \forall d \in D $$

### 3. Cobertura total de eventos

Obliga a que cada evento sea programado en exactamente el número de franjas que indica su duración.

$$ \sum_{\substack{r \in R, t \in T \\ (e,r,t) \in Valid\_ERT}} x_{e,r,t} = Dur_e \quad \forall e \in E $$

### 4. Estabilidad de salones

Restringe el número de salones distintos que una sección puede utilizar a lo largo de la semana, limitándolo a un máximo de dos. La primera desigualdad vincula cada evento de la sección con la variable de uso del salón, y la segunda impone el límite global.

$$ \sum_{\substack{t \in T \\ (e,r,t) \in Valid\_ERT}} x_{e,r,t} \leq Dur_e \cdot w_{s,r} \quad \forall (s,r) \in Valid\_SR,\; \forall e \in E_s $$

$$ \sum_{\substack{r \in R \\ (s,r) \in Valid\_SR}} w_{s,r} \leq 2 \quad \forall s \in S $$

### 5. No colisión de salones físicos

Establece que cada salón físico (no virtual) puede albergar como máximo un evento en cualquier franja horaria.

$$ \sum_{\substack{e \in E \\ (e,r,t) \in Valid\_ERT}} x_{e,r,t} \leq 1 \quad \forall r \in R \setminus R_{\text{virtual}},\; \forall t \in T $$

### 6. Continuidad y no fragmentación

Impide que un evento cuya duración abarca varias franjas sea fragmentado en bloques separados. Para ello, se exige que cada evento posea exactamente un punto de inicio, y se vincula el estado de ocupación de cada franja con los posibles instantes de arranque dentro del mismo día.

$$ \sum_{\substack{r \in R, t \in T \\ (e,r,t) \in Valid\_ERT}} y_{e,r,t} = 1 \quad \forall e \in E $$

$$ x_{e,r,t} = \sum_{\substack{\tau \in T_d \mid (e,r,\tau) \in Valid\_ERT \\ t - Dur_e + 1 \leq \tau \leq t}} y_{e,r,\tau} \quad \forall d \in D,\; \forall (e,r,t) \in Valid\_ERT \mid t \in T_d $$

### 7. Control de desbordamiento diario

Prohíbe que un evento inicie en una franja tan tardía que su duración lo lleve más allá de la última franja del día.

$$ y_{e,r,t} = 0 \quad \forall d \in D,\; \forall (e,r,t) \in Valid\_ERT \mid t \in T_d \land t > \max(T_d) - Dur_e + 1 $$

### 8. Oferta global de secciones sin conflicto

Garantiza que para cada currículo $k \in K$ y cada curso $c \in C_k$ que posea más de una sección ($|S_{k,c}| > 1$), la suma total de franjas ocupadas simultáneamente por todas las secciones de dicho curso más las franjas de cualquier otro evento del mismo currículo no exceda la cantidad de secciones disponibles. De esta manera, se asegura que en cada franja horaria al menos una sección del curso permanezca libre de conflicto con cada evento externo de la malla curricular.

$$ \sum_{\substack{e \in E_{k,c},\; r \in R \\ (e,r,t) \in Valid\_ERT}} x_{e,r,t} + \sum_{\substack{r' \in R \\ (e',r',t) \in Valid\_ERT}} x_{e',r',t} \leq |S_{k,c}| \quad \forall k \in K,\; \forall c \in C_k \mid |S_{k,c}| > 1,\; \forall e' \in E_k \setminus E_{k,c},\; \forall t \in T $$

## Restricciones blandas

### 1. Penalización por clases en almuerzo

Contabiliza el total de franjas de clase programadas durante el período de almuerzo.

$$ P_{\text{almuerzo}} = \sum_{(e,r,t) \in Valid\_ERT} \left(x_{e,r,t} \cdot Almuerzo_t\right) $$

### 2. Penalización por espaciado de sesiones

Contabiliza las infracciones a la regla de espaciado (sesiones dictadas en días consecutivos). Permite la holgura controlada a través de la variable $v_{\text{espaciado}, c, i}$ y la acumula en $P_{\text{espaciado}}$:

$$ \sum_{\substack{e \in E_c, r \in R, t \in T_{d_i} \\ (e,r,t) \in Valid\_ERT}} y_{e,r,t} + \sum_{\substack{e \in E_c, r \in R, t \in T_{d_{i+1}} \\ (e,r,t) \in Valid\_ERT}} y_{e,r,t} \leq 1 + v_{\text{espaciado}, c, i} \quad \forall c \in C,\; \forall i \in \{1, \dots, |D|-1\} $$

$$ P_{\text{espaciado}} = \sum_{c \in C} \sum_{i=1}^{|D|-1} v_{\text{espaciado}, c, i} $$

## Función objetivo

El propósito del modelo consiste en encontrar un horario que cumpla con todas las restricciones operativas duras y, al mismo tiempo, minimice de manera conjunta las penalizaciones por clases en almuerzo y las infracciones de espaciado de sesiones:

$$ \min Z = W_A \cdot P_{\text{almuerzo}} + W_E \cdot P_{\text{espaciado}} $$