# Algoritmo de Optimización Propuesto: Algoritmo Genético Híbrido (HGA)

**Fecha de última actualización:** 5 de octubre de 2026

---

## 1. Visión General del Enfoque Propuesto

La programación de horarios universitarios constituye un problema de optimización combinatoria de alta complejidad, en el que la búsqueda de soluciones factibles y de alta calidad operativa se vuelve computacionalmente costosa conforme aumenta el tamaño de la institución. Para resolver este desafío de manera eficiente, se propone el desarrollo de un Algoritmo Genético Híbrido (HGA). 

A diferencia de los algoritmos genéticos convencionales, que exploran el espacio de soluciones de forma puramente aleatoria y suelen estancarse en horarios con múltiples cruces de docentes o aulas, la metodología propuesta integra la búsqueda global evolutiva con un mecanismo de reparación inteligente basado en búsqueda local memética. Este operador complementario detecta activamente los conflictos generados durante el proceso de recombinación y redistribuye las clases de forma dirigida, asegurando una convergencia rápida hacia cronogramas completamente viables que promueven el bienestar de docentes y estudiantes.

---

## 2. Representación del Horario y Reducción Previa de Dominios

En términos computacionales, cada propuesta de horario se representa mediante un arreglo o vector unidimensional discreto, análogo a un cromosoma genético. Dentro de esta estructura, cada posición del vector corresponde de forma fija a un evento de clase específico, mientras que el valor numérico entero asignado a dicha posición identifica una combinación concreta de aula (física o virtual) y franja horaria de inicio.

El diseño de esta codificación responde directamente a la necesidad de gestionar una estructura temporal de alta resolución. Mientras que diversas propuestas en la literatura simplifican la semana académica a diez franjas basadas en dos turnos diarios (Ozkan et al., 2025) o a veinticinco bloques fijos de dos horas (Zhu et al., 2026), el presente modelo refleja la operativa real de la institución mediante un horizonte de 86 franjas horarias discretas de una hora. Esta resolución permite admitir clases continuas de dos y tres horas, proteger formalmente el período de almuerzo institucional y gestionar el cierre de las instalaciones físicas durante los días jueves. No obstante, esta granularidad fina expande sustancialmente el número de combinaciones teóricas posibles.

Para controlar este crecimiento combinatorio y evitar que el algoritmo pierda tiempo explorando alternativas inviables, se incorpora una etapa previa de reducción de dominios (`valid_starts`). Antes de comenzar la optimización, se construye para cada evento un catálogo restringido que incluye únicamente los inicios y aulas física y contractualmente posibles. En este proceso de filtrado se descartan de antemano las franjas que desbordan la jornada diaria, los horarios incompatibles con la disponibilidad del docente, las aulas sin la capacidad requerida o carentes del equipamiento técnico necesario (`pc`, `deep_learning`), así como las clases presenciales durante el día de cierre o virtuales fuera de este. De este modo, los genes del cromosoma solo pueden seleccionar valores pertenecientes a este catálogo de alternativas viables, reduciendo significativamente el espacio de búsqueda desde el inicio.

---

## 3. Población Inicial y Mecanismos de Búsqueda Evolutiva

El ciclo de búsqueda imita los principios de la selección natural para mejorar gradualmente la calidad de los horarios a través de sucesivas generaciones. El procedimiento inicia con la creación de una población inicial compuesta por un número definido de individuos. Cada uno de estos horarios se construye asignando al azar opciones válidas del catálogo de cada evento, garantizando una amplia variedad de configuraciones iniciales que favorece la exploración global del espacio de soluciones.

A partir de esta población, la transición hacia nuevas generaciones se articula mediante tres operadores genéticos principales. En primer lugar, la selección de padres se lleva a cabo mediante el método de torneo, seleccionando pequeños grupos de individuos al azar para premiar al de mejor desempeño, lo que equilibra la conservación de buenos horarios con la diversidad poblacional. En segundo lugar, se aplica un operador de cruzamiento uniforme con una probabilidad determinada ($P_c$), el cual combina de manera independiente las asignaciones de ambos progenitores para producir horarios descendientes que hereden las mejores características de cada padre. Por último, un operador de mutación introduce pequeñas modificaciones aleatorias con una probabilidad baja ($P_m$), cambiando la hora o aula de ciertos eventos dentro de sus opciones permitidas para ayudar al algoritmo a escapar de posibles estancamientos en soluciones locales.

---

## 4. Operador de Reparación Inteligente: *Most Constrained First* (MCF)

El elemento central y distintivo del algoritmo propuesto reside en su operador de reparación constructiva memética, diseñado bajo la heurística de saturación *Most Constrained First* (MCF). Luego de aplicar los operadores de cruce y mutación, el algoritmo revisa la solución para identificar posibles colisiones de restricciones duras, tales como la asignación simultánea de un docente a dos clases, la sobreocupación de aulas físicas o el solapamiento de asignaturas pertenecientes a un mismo currículo académico.

Al detectar conflictos, el operador no reasigna las clases de manera arbitraria, sino que establece un orden de atención guiado por el nivel de dificultad de cada evento. Aquellas clases más restrictivas —como las de mayor duración lectiva, las que requieren laboratorios específicos o las dictadas por docentes con poca disponibilidad horaria— se resuelven de forma prioritaria. Para cada una de ellas, el operador examina su catálogo de opciones viables e intenta colocarla en una franja y aula totalmente libre de colisiones. Si no existe una opción completamente vacía, se aplica un mecanismo de desplazamiento en cadena de un paso: el algoritmo verifica si al colocar el evento prioritario en una franja ocupada se afecta a un solo evento secundario; de ser viable, ubica la clase principal en esa posición y desplaza al evento bloqueador hacia otra alternativa válida de su propio catálogo.

Este proceso de ajuste se complementa con la estrategia de aprendizaje lamarckiano (*Lamarckian learning*), un mecanismo de hibridación dentro de los algoritmos meméticos y evolutivos en el cual las mejoras estructurales alcanzadas por un individuo a través de una búsqueda local se sobreescriben directamente en su representación cromosómica o genotipo (El-Mihoub et al., 2021; Kurniawan et al., 2025). Bajo este mecanismo de actualización (*Lamarckian update*), el algoritmo sustituye al individuo original en la población por su versión reparada y optimizada, garantizando que las adaptaciones favorables —como la supresión de colisiones de docentes, grupos o aulas— se transmitan de forma acumulativa y permanente a las siguientes generaciones mediante los operadores de selección, cruce y elitismo (El-Mihoub et al., 2021; Kurniawan et al., 2025; Rezaeipanah et al., 2021).

El flujo de ejecución formal del método propuesto se sintetiza a alto nivel en el Algoritmo 1.

```text
Algoritmo 1: Algoritmo Genético Híbrido (HGA) para UCTP
-----------------------------------------------------------------------------------------------------------------
Entradas: Datos del problema (Eventos E, Salones R, Docentes P, Currículos K, Franjas T),
          Dominios precomputados valid_starts, Tamaño de población (N),
          Probabilidades de cruzamiento (Pc) y mutación (Pm), Límites de ejecución (Épocas, Tiempo).
Salida:   Horario factible óptimo o subóptimo S* con mínima penalización blanda Z.

 1: Precomputar valid_starts y ordenar eventos por dificultad MCF (duración, aforo y carga docente)
 2: Población P ← Inicializar N individuos asignando índices aleatorios en valid_starts
 3: Para cada individuo I en P hacer
 4:     I.Genes ← Reparar_MCF(I.Genes)                     // Aprendizaje lamarckiano inicial
 5:     I.Fitness ← EvaluarAptitud(I.Genes)                // Fitness = (1000 * HCV) + Z
 6: Fin Para
 7: Mientras no se alcance el límite de épocas ni de tiempo máximo hacer
 8:     P_nueva ← [ ObtenerMejorIndividuo(P) ]             // Elitismo estricto
 9:     Mientras |P_nueva| < N hacer
10:         Padre1, Padre2 ← SeleccionarPorTorneo(P)
11:         Hijo1, Hijo2   ← CruzarUniformemente(Padre1, Padre2, Pc)
12:         Hijo1, Hijo2   ← MutarAleatoriamente(Hijo1, Hijo2, Pm)
13:         Hijo1.Genes    ← Reparar_MCF(Hijo1.Genes)      // Reparación memética y actualización lamarckiana
14:         Hijo2.Genes    ← Reparar_MCF(Hijo2.Genes)
15:         Hijo1.Fitness  ← EvaluarAptitud(Hijo1.Genes)
16:         Hijo2.Fitness  ← EvaluarAptitud(Hijo2.Genes)
17:         P_nueva.Añadir(Hijo1, Hijo2)
18:     Fin Mientras
19:     P ← P_nueva
20:     Si Mejor(P).HCV == 0 y Z no mejora en 20 épocas consecutivas entonces
21:         Romper bucle                                   // Parada temprana por convergencia
22:     Fin Si
23: Fin Mientras
24: Retornar DecodificarHorario(ObtenerMejorIndividuo(P))
```

---

## 5. Medición de la Calidad del Horario (Función de Aptitud)

La evaluación de los horarios se realiza mediante una función de aptitud (*fitness*) estructurada en dos niveles jerárquicos, orientada a guiar la búsqueda hacia soluciones operativamente viables y con altos estándares de calidad académica. En el primer nivel, el sistema impone una penalización de gran escala ($1000 \times HCV$) ante cualquier violación de restricciones duras ($HCV$). Esta penalización estricta asegura que el algoritmo concentre sus primeros esfuerzos en eliminar cualquier choque físico o contractual antes de priorizar otros aspectos del horario.

Una vez que el horario alcanza la factibilidad operativa total ($HCV = 0$), su puntuación se determina exclusivamente mediante la minimización de la función objetivo ponderada:

$$\min Z = W_A \cdot P_{\text{almuerzo}} + W_E \cdot P_{\text{espaciado}} + W_{\text{jue}} \cdot P_{\text{jueves}} + W_{\text{sab}} \cdot P_{\text{sabado}} + W_V \cdot P_{\text{ventanas}}$$

Esta función cuantifica el grado de satisfacción de las preferencias institucionales y humanas. En ella se penaliza programar clases durante la franja de almuerzo ($W_A=1$), ubicar sesiones de una misma asignatura en días seguidos sin espaciado pedagógico ($W_E=10$), concentrar carga académica en días de menor preferencia como jueves o sábados ($W_{\text{jue}}=1, W_{\text{sab}}=3$) y fragmentar la jornada diaria de los docentes con ventanas u horas muertas improductivas ($W_V=2$).

---

## 6. Métricas y Criterios de Evaluación del Desempeño

Con el propósito de evaluar de forma rigurosa la efectividad, calidad de solución y eficiencia computacional del Algoritmo Genético Híbrido propuesto, y contrastarlo de manera objetiva frente al modelo exacto de Programación Lineal Entera Mixta (MIP) y las tres metaheurísticas de referencia (el Algoritmo Genético Clásico GA, la Búsqueda Tabú TS y el Recocido Simulado SA), se adopta un marco de evaluación multidimensional. Siguiendo los estándares metodológicos de la literatura especializada en calendarización universitaria (Abdipoor, Yaakob, et al., 2025; Bashab et al., 2023), el análisis se estructura en tres dimensiones fundamentales: viabilidad operativa, calidad de la optimización y eficiencia computacional.

La primera dimensión, correspondiente a la viabilidad operativa y factibilidad, examina la capacidad de los algoritmos para respetar rigurosamente las restricciones duras del sistema hasta erradicar cualquier conflicto físico o contractual ($HCV = 0$). Para ello, se evalúa en primer término la Tasa de Éxito o Factibilidad Global ($SR$), que mide el porcentaje de ejecuciones independientes que culminan en un horario plenamente factible, permitiendo comprobar la eficacia de los operadores constructivos y de reparación (Abdipoor, Li, et al., 2025; Bashab et al., 2023). En segundo lugar, para aquellas ejecuciones que no alcanzan una solución totalmente libre de conflictos, se calcula la Distancia a la Factibilidad ($DF$), una métrica que cuantifica la cantidad y magnitud de restricciones insatisfechas para discriminar qué tan cerca estuvo el método de alcanzar la frontera válida (Abdipoor, Li, et al., 2025). Finalmente, se registra el Tiempo hacia la Factibilidad ($TTF$ o *Time to Feasibility*), que contabiliza el tiempo de cómputo en segundos requerido por el algoritmo para descubrir su primera solución completamente factible desde el inicio de la búsqueda (Chen et al., 2021; Haider et al., 2024).

La segunda dimensión evalúa la calidad de la optimización, centrando su atención en el grado de satisfacción de las preferencias pedagógicas e institucionales una vez asegurada la viabilidad operativa. El indicador principal es el valor de la función objetivo ($Z$), correspondiente a la suma ponderada de penalizaciones blandas. Debido a la naturaleza estocástica de los algoritmos evolutivos y de trayectoria, se ejecutan treinta corridas independientes por cada método e instancia, reportando el mejor valor de $Z$, el promedio obtenido y la desviación estándar ($\sigma$) como medida de estabilidad y consistencia algorítmica (Abdipoor, Yaakob, et al., 2025). A nivel comparativo, se determina el Gap de optimalidad de la formulación exacta ($Gap_{\text{MIP}}$), que certifica la cercanía porcentual entre la solución entera y la cota inferior teórica continua del árbol de búsqueda (Mikkelsen & Holm, 2022; Rohaizad et al., 2026). Asimismo, se calcula la Desviación Porcentual Relativa de las metaheurísticas ($RPD$ o *Relative Percentage Deviation*), que mide la discrepancia porcentual entre la solución generada por cada método aproximado y el óptimo de referencia provisto por el MIP. Para asegurar la robustez del cálculo y prevenir divisiones indeterminadas cuando el modelo exacto alcanza una solución perfecta con penalización nula ($Z_{\text{MIP}} = 0$), se utiliza la formulación normalizada con ajuste unitario recomendada por Abdipoor, Yaakob, et al. (2025) y Stidsen et al. (2024).

La tercera dimensión corresponde a la eficiencia computacional y las condiciones del entorno experimental, la cual busca auditar los recursos consumidos y garantizar la reproducibilidad estricta de las pruebas. En este ámbito, se registra el tiempo de procesamiento total ($CPU\text{ Time}$) invertido por cada técnica hasta alcanzar el criterio de parada estipulado, ya sea por convergencia anticipada o por límite temporal máximo (Bashab et al., 2023; Gu et al., 2025). Adicionalmente, se audita la intensidad del esfuerzo exploratorio interno mediante el conteo del Número de Evaluaciones de Aptitud ($NFE$) en las metaheurísticas y el total de nodos explorados en el árbol de *Branch and Bound* para el caso del solucionador exacto, lo que permite apreciar la carga de cómputo propia de cada paradigma sin establecer comparaciones artificiales (Abdipoor, Yaakob, et al., 2025; Bashab et al., 2023). Por último, se documenta de forma explícita el entorno de ejecución, especificando las características de hardware y el ecosistema de software empleado (Python 3.13 bajo el entorno reproducible Astral UV y el solucionador HiGHS), asegurando las condiciones de trazabilidad experimental exigidas por los estándares contemporáneos de investigación operativa (Rohaizad et al., 2026).
