# Objetivos del Proyecto

## Objetivo General

Diseñar un algoritmo genético híbrido para la resolución del problema de programación de horarios universitarios (CB-CTT), bajo las restricciones operativas y normativas de una universidad peruana.

---

## Objetivos Específicos

1. **Formalizar matemáticamente** el problema de programación de horarios CB-CTT, definiendo los conjuntos, parámetros, variables de decisión y las restricciones duras y blandas propias del contexto universitario peruano, y verificar la consistencia de la formulación mediante su implementación como modelo de Programación Lineal Entera Mixta (MIP).
2. **Generar un banco de 9 instancias semi-sintéticas** (3 pequeñas, 3 medianas y 3 grandes), basadas en la estructura curricular e infraestructura real de una carrera de Ingeniería de Sistemas, con variación por semilla de aleatorización para obtener instancias numéricamente distintas dentro de cada escala.
3. **Implementar el algoritmo genético híbrido propuesto**, integrando un operador de reparación constructivo basado en la heurística de saturación (*Most Constrained First*) con aprendizaje lamarckiano y desplazamiento en cadena, para la resolución de las 9 instancias generadas.
4. **Contrastar estadísticamente** el desempeño y la escalabilidad del algoritmo genético híbrido frente a un algoritmo genético tradicional mediante pruebas de hipótesis no paramétricas.
