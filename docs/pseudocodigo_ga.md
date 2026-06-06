# Pseudocódigo de Alto Nivel del Algoritmo Genético (GA) para UCTP

Este documento describe el flujo lógico principal y consolidado del Algoritmo Genético

---

```text
Algoritmo Optimización_UCTP_AlgoritmoGenético
    Entradas:
        - Datos del problema (Eventos, Salones, Profesores, Mallas Curriculares)
        - Parámetros del GA (Tamaño de Población, Máximo de Generaciones, Probabilidades de Cruzamiento/Mutación)
    Salidas:
        - Mejor horario que minimice las penalizaciones por incumplimiento de restricciones duras y blandas

    Inicio:
        // 1. Inicializar la Población
        Población <- Crear individuos aleatorios (cada gen representa una opción precomputada de Aula y Franja para un evento)

        // 2. Corregir y Evaluar la Población Inicial
        Para cada Individuo en Población Hacer
            Individuo.Genes <- AplicarReparaciónHeurística(Individuo.Genes)
            Individuo.Fitness <- CalcularAptitud(Individuo.Genes)
        FinPara

        // 3. Ciclo Evolutivo (Bucle de Optimización)
        Mientras (Generación < MáximoGeneraciones) y (TiempoEjecución < LímiteTiempo) Hacer
            NuevaPoblación <- []
            NuevaPoblación.Añadir(ObtenerMejorIndividuo(Población)) // Elitismo

            Mientras (NuevaPoblación.Longitud < TamañoPoblación) Hacer
                // a. Selección
                Padre1, Padre2 <- SeleccionarPorTorneo(Población)

                // b. Cruzamiento y Mutación
                Hijo1, Hijo2 <- CruzarUniformemente(Padre1, Padre2) con Probabilidad_Pc
                Hijo1 <- MutarAleatoriamente(Hijo1) con Probabilidad_Pm
                Hijo2 <- MutarAleatoriamente(Hijo2) con Probabilidad_Pm

                // c. Reparación Heurística (Eliminación de colisiones duras)
                // Se ordenan los eventos por dificultad (Most Constrained First) y se colocan secuencialmente.
                // Si hay colisión de docente o aula, se busca una opción libre o se desplaza en cadena
                // al evento bloqueador (1-step displacement).
                Hijo1.Genes <- AplicarReparaciónHeurística(Hijo1.Genes)
                Hijo2.Genes <- AplicarReparaciónHeurística(Hijo2.Genes)

                // d. Evaluación de Aptitud
                // Fitness = (1000 * Restricciones_Duras_Violadas) + (1 * Penalización_Almuerzo + 10 * Penalización_Espaciado)
                Hijo1.Fitness <- CalcularAptitud(Hijo1.Genes)
                Hijo2.Fitness <- CalcularAptitud(Hijo2.Genes)

                NuevaPoblación.Añadir(Hijo1, Hijo2)
            FinMientras

            Población <- NuevaPoblación

            // e. Control de Convergencia
            Si la solución es factible y no mejora en 20 generaciones consecutivas Entonces
                Romper Bucle (Convergencia prematura / Salida anticipada)
            FinSi
        FinMientras

        Retornar DecodificarMejorHorario(ObtenerMejorIndividuo(Población))
Fin
```
