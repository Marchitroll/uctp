# Pseudocódigo de Alto Nivel: Algoritmos Genéticos para UCTP

Este documento describe el flujo lógico principal del **Algoritmo Genético Híbrido (HGA)** y especifica su relación de contraste con el **Algoritmo Genético Clásico (GA)** para la resolución del problema CB-CTT.

---

## 1. Algoritmo Genético Híbrido (HGA) con Heurística Memética MCF

```text
Algoritmo Optimización_UCTP_AlgoritmoGenéticoHíbrido (HGA)
    Entradas:
        - Datos del problema (Eventos E, Salones R, Profesores P, Mallas Curriculares K, 86 Franjas T)
        - Dominios precomputados de inicio factible: valid_starts
        - Parámetros del HGA: PopSize, MaxGeneraciones, Pc (Crossover), Pm (Mutación), MaxTiempo
    Salidas:
        - Horario óptimo o subóptimo factible (HCV = 0) que minimice las penalizaciones blandas (Z)

    Inicio:
        // 1. Inicializar la Población
        Población <- Crear PopSize individuos aleatorios
                     (cada gen 'e' es un índice entero en [0, |valid_starts[e]| - 1])

        // 2. Corregir y Evaluar la Población Inicial (Aprendizaje Lamarckiano)
        Para cada Individuo en Población Hacer
            Individuo.Genes <- AplicarReparaciónHeurística_MCF(Individuo.Genes)
            Individuo.Fitness <- CalcularAptitud(Individuo.Genes)
        FinPara

        // 3. Ciclo Evolutivo
        Mientras (Generación < MaxGeneraciones) y (TiempoEjecución < MaxTiempo) Hacer
            NuevaPoblación <- []
            NuevaPoblación.Añadir(ObtenerMejorIndividuo(Población)) // Elitismo estricto

            Mientras (NuevaPoblación.Longitud < PopSize) Hacer
                // a. Selección
                Padre1, Padre2 <- SeleccionarPorTorneo(Población)

                // b. Cruzamiento y Mutación
                Hijo1, Hijo2 <- CruzarUniformemente(Padre1, Padre2) con probabilidad Pc
                Hijo1 <- MutarAleatoriamente(Hijo1) con probabilidad Pm
                Hijo2 <- MutarAleatoriamente(Hijo2) con probabilidad Pm

                // c. Reparación Constructiva Memética (Eliminación de colisiones duras)
                // Se ordenan los eventos por dificultad estable (Most Constrained First).
                // Si existe colisión de docente, aula física o currículo:
                //   1) Se busca una opción libre sin conflicto en valid_starts.
                //   2) Si no existe, se aplica desplazamiento en cadena de 1 paso al evento bloqueador.
                Hijo1.Genes <- AplicarReparaciónHeurística_MCF(Hijo1.Genes)
                Hijo2.Genes <- AplicarReparaciónHeurística_MCF(Hijo2.Genes)

                // d. Evaluación de Función de Aptitud Unificada
                // Z = 1*P_almuerzo + 10*P_espaciado + 1*P_jueves + 3*P_sabado + 2*P_ventanas
                // Fitness = (1000 * HCV) + (1 * Z)
                Hijo1.Fitness <- CalcularAptitud(Hijo1.Genes)
                Hijo2.Fitness <- CalcularAptitud(Hijo2.Genes)

                NuevaPoblación.Añadir(Hijo1, Hijo2)
            FinMientras

            Población <- NuevaPoblación

            // e. Criterio de Parada Temprana por Convergencia
            Si (MejorIndividuo.HCV == 0) y (Z no mejora en 20 generaciones consecutivas) Entonces
                Romper Bucle // Salida anticipada por convergencia de calidad
            FinSi
        FinMientras

        Retornar DecodificarHorario(ObtenerMejorIndividuo(Población))
Fin
```

---

## 2. Diferenciación con el Algoritmo Genético Clásico (GA)

El **Algoritmo Genético Clásico** (`modelo_GA.py`) comparte la misma representación genética sobre `valid_starts`, la misma función de aptitud ($\min 1000 \cdot HCV + Z$) y el mismo esquema evolutivo (selección por torneo, cruzamiento uniforme y mutación), pero **omite intencionalmente el paso (c) de reparación constructiva memética MCF**:

* En el **GA Clásico**, la función de corrección se limita exclusivamente a redondear y recortar los genes a los límites enteros discretos:
  $$\text{Individuo.Genes} \leftarrow \text{Clip}(\text{Round}(\text{Genes}), 0, \text{MaxChoices})$$
* Al carecer del operador constructivo inteligente, el GA canónico confía únicamente en la presión selectiva de la función de penalización $1000 \cdot HCV$ para reducir las infracciones duras, lo que permite medir cuantitativamente el beneficio específico que aporta la hibridación memética de **HGA**.
