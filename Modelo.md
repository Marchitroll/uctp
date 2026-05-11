# Formulación Matemática

**Autor:** Marcelo Angeles

## Definiciones

* **Curso**: representa la asignatura general o programa de estudio. Actúa como un agrupador lógico para los eventos de una misma materia, permitiendo al modelo aplicar reglas de espaciado (días de descanso) entre sesiones correlativas. El modelo asume que los cursos ya han sido divididos en secciones.
* **Sección**: refleja el grupo específico de estudiantes matriculados en un curso. Es la unidad académica que arrastra los parámetros físicos, como la cantidad de alumnos y los requerimientos de infraestructura.
* **Evento**: demanda atómica de programación generada por una sección. Posee una duración preestablecida y un profesor asignado. Computacionalmente, el evento se materializa en una "clase" solo cuando el algoritmo le asigna coordenadas definitivas de espacio y tiempo.
* **Salón**: corresponde al recurso de espacio donde se imparte el evento. Puede ser un espacio físico sujeto a límites de aforo o un elemento virtual con capacidad irrestricta. La naturaleza del salón (físico o virtual) condiciona sus días operativos.
* **Franja horaria**: equivale a los períodos de tiempo indivisibles definidos por la institución.
* **Profesor**: recurso humano responsable de dictar el evento, sujeto a una matriz de disponibilidad horaria estricta.
* **Currículo**: grupo de secciones (ruta sugerida o bloque de malla) que un segmento de estudiantes ideal debe llevar en un mismo ciclo. El modelo utiliza este conjunto para garantizar que los eventos pertenecientes a una misma ruta no se traslapen, facilitando la matrícula sin cruces.

## Definición de conjuntos

Sea la siguiente colección de conjuntos para el problema de programación de horarios:

* **Conjunto Global de Eventos** $E$: conjunto de todas las demandas atómicas de programación generadas por las secciones.
* **Conjunto Global de Salones** $R$: representa todos los espacios disponibles para impartir un evento.
* **Subconjunto de Salones Virtuales** $R_{\text{virtual}} \subseteq R$: conjunto de salones que operan exclusivamente de manera remota.
* **Conjunto Global de Franjas Horarias** $T$: conjunto de bloques de tiempo indivisibles en los que la institución programa sus actividades.
* **Conjunto Secuencial de Días** $D$: tupla ordenada que agrupa las franjas horarias por día de la semana $D = (d_1, d_2, \dots, d_{|D|})$.
* **Día de cierre físico** $d_{\text{jue}}$: elemento distinguido de $D$ que identifica el día de cierre del campus (jueves). Sus franjas asociadas se representan por $T_{d_{\text{jue}}}$.
* **Conjunto de Currículos** $K$: representa las rutas sugeridas o bloques de matrícula.
* **Conjunto de Secciones** $S$: representa las unidades operativas de estudiantes matriculados en un curso específico.
* **Conjunto de Profesores Activos** $P$: incluye al personal docente directamente vinculado (derivado) al dictado de los eventos en $E$.
* **Conjunto de Características** $F$: colección de requerimientos de infraestructura (ej. "mesa", "pc", "deep_learning").

### Agrupaciones Relacionales

* **Agrupación por Curso** $C$: familia de subconjuntos de $E$, donde cada $c \in C$ agrupa los eventos de una misma materia para una sección específica, garantizando el espaciado temporal.
* **Relación Currículo-Evento** $\{E_k\}_{k \in K}$: familia de subconjuntos de $E$ que componen la ruta $k \in K$.
* **Relación Sección-Evento** $\{E_s\}_{s \in S}$: familia de subconjuntos de $E$ para la sección $s \in S$.
* **Relación Profesor-Evento** $\{E_p\}_{p \in P}$: familia de subconjuntos de $E$ dictados por $p \in P$.
* **Franjas por Día** $\{T_d\}_{d \in D}$: familia de subconjuntos de $T$ para el día $d \in D$.

### Reducción Topológica (Dominios Factibles)

Para garantizar la eficiencia computacional (instanciación dispersa) y la viabilidad física del modelo, las variables de decisión no se instancian sobre el producto cartesiano completo. Se definen a priori los siguientes subconjuntos de tuplas válidas basados en los parámetros de aforo ($CAP_r$), cantidad de alumnos ($Alumno_s$), infraestructura disponible ($Tiene_{r,f}$) y requerida ($Req_{s,f}$), así como restricciones operativas de cierre:

* **Tuplas Válidas de Asignación Espacial ($Valid\_SR \subseteq S \times R$)**:
Contiene los pares factibles de sección $s$ y salón $r$, filtrando aquellos que no cumplen con la capacidad o la infraestructura:

$$Valid\_SR = \{(s, r) \in S \times R \mid CAP_r \geq Alumno_s \land \forall f \in F\; (Req_{s,f} \leq Tiene_{r,f})\}$$

* **Tuplas Válidas de Operación ($Valid\_ERT \subseteq E \times R \times T$)**:
Contiene las combinaciones de evento $e$, salón $r$ y franja $t$ temporalmente factibles. Se construye a partir de $Valid\_SR$ e incorpora la restricción del día de cierre garantizando la existencia de la sección correspondiente:

$$Valid\_ERT = \{(e, r, t) \in E \times R \times T \mid \exists s \in S : (s, r) \in Valid\_SR \land e \in E_s \land t \in T_r\}$$

Donde el conjunto de franjas operativas $T_r$ depende de la naturaleza del salón:

$$T_r = \begin{cases} T_{d_{\text{jue}}} & \text{si } r \in R_{\text{virtual}} \\ T \setminus T_{d_{\text{jue}}} & \text{si } r \notin R_{\text{virtual}} \end{cases}$$

## Parámetros y variables de decisión

Se definen los siguientes parámetros del modelo:

* **Capacidad del salón** $CAP_r$: número máximo de estudiantes que puede albergar el salón $r \in R$.
* **Cantidad de alumnos** $Alumno_s$: número de estudiantes matriculados en la sección $s \in S$.
* **Requerimiento de la sección** $Req_{s,f}$: parámetro binario que vale 1 si la sección $s \in S$ requiere la característica $f \in F$, y 0 en caso contrario.
* **Característica del salón** $Tiene_{r,f}$: parámetro binario que vale 1 si el salón $r \in R$ posee la característica $f \in F$, y 0 en caso contrario.
* **Disponibilidad del profesor** $Disp_{p,t}$: parámetro binario que vale 1 si el profesor $p \in P$ puede dictar clase en la franja horaria $t \in T$, y 0 en caso contrario.
* **Almuerzo** $Almuerzo_t$: parámetro binario que vale 1 si la franja horaria $t \in T$ corresponde a la hora de almuerzo, y 0 en caso contrario.
* **Duración del evento** $Dur_e$: parámetro numérico entero que indica cuántas franjas horarias consecutivas ocupa $e \in E$.

Las variables de decisión, instanciadas exclusivamente sobre los dominios topológicamente viables, son:

* **Asignación evento-salón-franja** $x_{e,r,t}$: variable binaria que vale 1 si el evento $e$ se programa en el salón $r$ durante la franja $t$, y 0 en caso contrario.
* **Inicio del evento** $y_{e,r,t}$: variable binaria que toma el valor de 1 si el evento $e$ inicia en el salón $r$ durante la franja $t$, y 0 en caso contrario.
* **Uso de salón por sección** $w_{s,r}$: variable binaria auxiliar que toma el valor de 1 si la sección $s$ utiliza el salón $r$ al menos una vez en la semana, y 0 en caso contrario.
* **Penalización por clases en almuerzo** $P_{\text{almuerzo}}$: variable entera no negativa que contabiliza el total de franjas de clase asignadas durante el período de almuerzo.

### Dominio de las variables

$$ x_{e,r,t} \in \{0,1\} \quad \forall (e,r,t) \in Valid\_ERT $$

$$ y_{e,r,t} \in \{0,1\} \quad \forall (e,r,t) \in Valid\_ERT $$

$$ w_{s,r} \in \{0,1\} \quad \forall (s,r) \in Valid\_SR $$

$$ P_{\text{almuerzo}} \in \mathbb{Z}^{+} \cup \{0\} $$

*(Nota: En todas las sumatorias subsiguientes, si una tupla evaluada no pertenece a los conjuntos válidos, su variable no existe y asume el valor de 0, evitando así la formulación de restricciones redundantes sobre variables nulas).*

## Restricciones duras

### 1. Disponibilidad y no colisión del profesor
Garantiza que un docente no se cruce de horarios y que solo se le programen clases en las franjas donde indicó disponibilidad.

$$ \sum_{\substack{e \in E_p, r \in R \\ (e,r,t) \in Valid\_ERT}} x_{e,r,t} \leq Disp_{p,t} \quad \forall p \in P,\; \forall t \in T $$

### 2. No colisión por currículo (rutas sugeridas)
Garantiza que los eventos pertenecientes a una misma ruta académica no se traslapen.

$$ \sum_{\substack{e \in E_k, r \in R \\ (e,r,t) \in Valid\_ERT}} x_{e,r,t} \leq 1 \quad \forall k \in K,\; \forall t \in T $$

### 3. Cobertura total de eventos
Fuerza a que cada evento sea programado exactamente la cantidad de franjas requeridas por su duración.

$$ \sum_{\substack{r \in R, t \in T \\ (e,r,t) \in Valid\_ERT}} x_{e,r,t} = Dur_e \quad \forall e \in E $$

### 4. Estabilidad de salones
Limita la movilidad de cada sección, garantizando que utilice como máximo dos salones a lo largo de la semana.

$$ \sum_{\substack{t \in T \\ (e,r,t) \in Valid\_ERT}} x_{e,r,t} \leq Dur_e \cdot w_{s,r} \quad \forall (s,r) \in Valid\_SR,\; \forall e \in E_s $$

$$ \sum_{\substack{r \in R \\ (s,r) \in Valid\_SR}} w_{s,r} \leq 2 \quad \forall s \in S $$

### 5. No colisión de salones físicos
Establece que cada salón físico puede albergar a lo sumo un evento por franja horaria.

$$ \sum_{\substack{e \in E \\ (e,r,t) \in Valid\_ERT}} x_{e,r,t} \leq 1 \quad \forall r \in R \setminus R_{\text{virtual}},\; \forall t \in T $$

### 6. Continuidad y no fragmentación
Evita que un evento de varias franjas se fragmente, definiendo un único punto de inicio.

$$ \sum_{\substack{r \in R, t \in T \\ (e,r,t) \in Valid\_ERT}} y_{e,r,t} = 1 \quad \forall e \in E $$

$$ x_{e,r,t} = \sum_{\substack{\tau \in T_d \mid (e,r,\tau) \in Valid\_ERT \\ t - Dur_e + 1 \leq \tau \leq t}} y_{e,r,\tau} \quad \forall d \in D,\; \forall (e,r,t) \in Valid\_ERT \mid t \in T_d $$

### 7. Espaciado de sesiones
Garantiza al menos un día de descanso entre los inicios de eventos pertenecientes al mismo curso.

$$ \sum_{\substack{e \in c, r \in R, t \in T_{d_i} \\ (e,r,t) \in Valid\_ERT}} y_{e,r,t} + \sum_{\substack{e \in c, r \in R, t \in T_{d_{i+1}} \\ (e,r,t) \in Valid\_ERT}} y_{e,r,t} \leq 1 \quad \forall c \in C,\; \forall i \in \{1, \dots, |D|-1\} $$

### 8. Control de desbordamiento diario
Fija a cero la variable de inicio si el tiempo restante en el día es estrictamente menor a la duración del evento.

$$ y_{e,r,t} = 0 \quad \forall d \in D,\; \forall (e,r,t) \in Valid\_ERT \mid t \in T_d \land t > \max(T_d) - Dur_e + 1 $$

## Restricciones blandas

### 1. Penalización por clases en almuerzo
Contabiliza el total de franjas asignadas durante el período de almuerzo.

$$ P_{\text{almuerzo}} = \sum_{(e,r,t) \in Valid\_ERT} \left(x_{e,r,t} \cdot Almuerzo_t\right) $$

## Función objetivo

El propósito de este modelo de optimización es encontrar un horario factible que satisfaga estrictamente todas las restricciones operativas, minimizando al mismo tiempo las penalizaciones por clases en el período de almuerzo:

$$ \min Z = P_{\text{almuerzo}} $$