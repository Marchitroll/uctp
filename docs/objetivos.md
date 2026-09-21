# Objetivos del Proyecto

## Objetivo General

Diseñar e implementar un ecosistema de optimización para la resolución del problema de programación de horarios universitarios (CB-CTT) bajo las restricciones operativas y normativas de una universidad peruana, contrastando el desempeño de un Algoritmo Genético Híbrido frente a la formulación exacta (MIP) y metaheurísticas canónicas.

---

## Objetivos Específicos

1. **Formalizar matemáticamente** el problema de programación de horarios CB-CTT, definiendo los conjuntos, parámetros, variables de decisión y las restricciones duras y blandas propias del contexto universitario peruano (incluyendo almuerzo, espaciado curricular, días de baja preferencia y compacidad de horarios docentes), verificando la consistencia mediante un modelo de Programación Lineal Entera Mixta (MIP).
2. **Generar un banco de instancias semi-sintéticas** categorizadas en tres escalas de complejidad (Pequeña, Mediana y Grande), basadas en la estructura curricular e infraestructura real de una carrera de Ingeniería de Sistemas, garantizando condiciones controladas y reproducibles para la experimentación.
3. **Implementar el algoritmo genético híbrido propuesto (HGA)**, integrando un operador de reparación constructivo basado en la heurística de saturación (*Most Constrained First* - MCF) con aprendizaje lamarckiano y desplazamiento en cadena de 1 paso.
4. **Contrastar cuantitativamente** el desempeño, la viabilidad operativa y la escalabilidad del algoritmo genético híbrido frente al modelo exacto (MIP) y tres metaheurísticas canónicas: Algoritmo Genético Clásico (GA), Búsqueda Tabú (TS) y Recocido Simulado (SA), aplicando métricas estándar de la literatura científica.
