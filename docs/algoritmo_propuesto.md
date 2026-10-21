# Algoritmo Genético Híbrido (HGA)

**Fecha de actualización:** 19 de octubre de 2026

---

## 1. Visión General

HGA combina un algoritmo genético con un operador de reparación heurística *Most Constrained First* (MCF) y aprendizaje lamarckiano. Resuelve colisiones duras ($HCV = 0$) y minimiza penalizaciones blandas ($Z$).

---

## 2. Representación y Reducción de Dominios

* **Cromosoma:** Vector discreto donde cada posición representa un evento y su valor es un índice en `valid_starts`.
* **Reducción (`valid_starts`):** Filtra inicios válidos por evento según:
  * Capacidad del salón ($CAP_r \ge Alumno_s$) y equipamiento (`pc`, `deep_learning`).
  * Disponibilidad docente ($Disp_{p,t} = 1$).
  * Duración dentro de la jornada diaria.
  * Modalidad operativa (jueves virtual; otros días presenciales).

---

## 3. Operadores Evolutivos

* **Población inicial:** $N$ individuos generados en `valid_starts`.
* **Selección:** Torneo.
* **Cruzamiento uniforme:** $P_c = 0.90$.
* **Mutación aleatoria:** $P_m = 0.05$ dentro de opciones válidas.
* **Elitismo:** Conserva el mejor individuo por generación.

---

## 4. Reparación Heurística: *Most Constrained First* (MCF)

Tras cruce y mutación, el operador repara colisiones duras:

1. **Orden MCF:** Prioriza eventos por duración, escasez de opciones válidas y carga docente.
2. **Asignación factible:** Conserva la opción actual si no tiene colisión.
3. **Búsqueda alternativa:** Asigna una opción válida libre de conflicto.
4. **Desplazamiento:** Reubica un evento bloqueante secundario si libera la posición.
5. **Aprendizaje lamarckiano:** Sobreescribe el genotipo con la solución reparada.

```text
Algoritmo 1: Algoritmo Genético Híbrido (HGA)
-----------------------------------------------------------------------------------------------------
Entradas: Datos del problema (E, R, P, K, T), dominios valid_starts, tamaño N, Pc, Pm, límites.
Salida:   Horario factible con mínima penalización blanda Z.

 1: Precomputar valid_starts y ordenar eventos por MCF
 2: Población P ← Inicializar N individuos aleatorios en valid_starts
 3: Para cada individuo I en P hacer
 4:     I.Genes ← Reparar_MCF(I.Genes)
 5:     I.Fitness ← EvaluarAptitud(I.Genes)
 6: Fin Para
 7: Mientras no se alcance límite de épocas ni tiempo hacer
 8:     P_nueva ← [ ObtenerMejorIndividuo(P) ]
 9:     Mientras |P_nueva| < N hacer
10:         Padre1, Padre2 ← SeleccionarPorTorneo(P)
11:         Hijo1, Hijo2   ← CruzarUniformemente(Padre1, Padre2, Pc)
12:         Hijo1, Hijo2   ← MutarAleatoriamente(Hijo1, Hijo2, Pm)
13:         Hijo1.Genes    ← Reparar_MCF(Hijo1.Genes)
14:         Hijo2.Genes    ← Reparar_MCF(Hijo2.Genes)
15:         Hijo1.Fitness  ← EvaluarAptitud(Hijo1.Genes)
16:         Hijo2.Fitness  ← EvaluarAptitud(Hijo2.Genes)
17:         P_nueva.Añadir(Hijo1, Hijo2)
18:     Fin Mientras
19:     P ← P_nueva
20:     Si Mejor(P).HCV == 0 y Z sin mejora por 20 épocas entonces
21:         Romper bucle
22:     Fin Si
23: Fin Mientras
24: Retornar DecodificarHorario(ObtenerMejorIndividuo(P))
```

---

## 5. Función de Aptitud (*Fitness*)

$$\text{Fitness} = 1000 \cdot HCV + Z$$

La definición y pesos de las penalizaciones de $Z$ se detallan en [modelo_matematico.md](modelo_matematico.md).

---

## 6. Documentación Relacionada

* Métricas formales: [metricas_evaluacion.md](metricas_evaluacion.md)
* Resultados del benchmark: [resultados_experimentales.md](resultados_experimentales.md)
