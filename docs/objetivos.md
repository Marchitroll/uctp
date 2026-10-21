# Objetivos del Proyecto

**Fecha de actualización:** 19 de octubre de 2026

## Objetivo General

Resolver el problema de horarios universitarios (CB-CTT / UCTP) con restricciones institucionales, evaluando el desempeño de un Algoritmo Genético Híbrido (HGA) frente a un modelo exacto (MIP) y tres metaheurísticas (GA, TS, SA).

---

## Objetivos Específicos

1. **Formular el modelo MIP:** Definir restricciones duras y la función objetivo de penalizaciones blandas (almuerzo, espaciado, preferencia temporal y ventanas).
2. **Construir el banco de pruebas:** Generar 9 instancias semi-sintéticas en matriz $3 \times 3$ (escalas pequeña, mediana y grande con 3 semillas deterministas).
3. **Desarrollar el algoritmo HGA:** Implementar reducción de dominios (`valid_starts`), heurística de reparación *Most Constrained First* (MCF) y aprendizaje lamarckiano.
4. **Evaluar y comparar métodos:** Contrastar HGA contra MIP, GA, TS y SA en factibilidad ($SR$, $DF$), calidad ($Z$, $RPD$) y eficiencia (CPU, $TTF$, $NFE$).
