# Análisis de Complejidad del Espacio de Búsqueda (UCTP)

Este documento presenta una estimación teórica del número de variables y restricciones en el problema de Programación de Horarios Universitarios (UCTP) y analiza cómo escala el espacio de búsqueda según los escenarios de prueba (**Pequeño**, **Mediano** y **Grande**).

---

## 1. Formulación Teórica de la Complejidad

El espacio de búsqueda teórico del modelo matemático sin reducción de dominios crece combinatoriamente en función de las dimensiones de los conjuntos de entrada:

### 1.1 Variables de Decisión Teóricas
El número total de variables si se instanciaran todas las combinaciones posibles es:
$$ \text{Variables Totales}_{\text{Teóricas}} = 2 \cdot (|E| \cdot |R| \cdot |T|) + (|S| \cdot |R|) + (|C| \cdot (|D| - 1)) + 2 $$

Donde:
* **$x_{e,r,t}$ e $y_{e,r,t}$**: Variables de asignación e inicio de eventos, respectivamente. Cada una aporta $|E| \cdot |R| \cdot |T|$ variables binarias.
* **$w_{s,r}$**: Variable binaria de uso de salón por sección, aportando $|S| \cdot |R|$.
* **$v_{\text{espaciado}, c, i}$**: Variable continua de holgura por curso y día de transición, aportando $|C| \cdot (|D| - 1)$ variables.
* **$P_{\text{almuerzo}}$ y $P_{\text{espaciado}}$**: Variables acumuladoras de penalización (2 variables).

### 1.2 Restricciones Teóricas
El número máximo de restricciones teóricas crece linealmente con los días, franjas y la combinatoria de eventos y salones:
$$ \text{Restricciones Totales}_{\text{Teóricas}} \approx (|P| \cdot |T|) + (|P| \cdot |D|) + |E| + (|S| \cdot |R| \cdot |E|) + |S| + (|R| \cdot |T|) + |E| + (|D| \cdot |T| \cdot |E| \cdot |R|) + (|C| \cdot (|D| - 1)) + 2 + (|D| \cdot |E| \cdot |R|) $$

---

## 2. Reducción de Dominio (Instanciación Dispersa)

Para hacer el problema resoluble en tiempos prácticos, los códigos de optimización implementan una **instanciación dispersa** filtrando combinaciones infactibles a priori ($Valid\_SR$ y $Valid\_ERT$):
* **$Valid\_SR$**: Solo considera pares sección-salón que cumplen con aforo ($CAP_r \geq Alumno_s$) y requisitos de infraestructura ($Req_{s,f} \leq Tiene_{r,f}$).
* **$Valid\_ERT$**: Solo considera combinaciones evento-salón-franja válidas basadas en la disponibilidad horaria del profesor asignado ($Disp_{p(e), t} = 1$) y restricciones de exclusividad del campus físico.

---

## 3. Comparativa por Escenarios

A continuación se detallan las métricas teóricas frente a las reales obtenidas al procesar los tres escenarios institucionales generados por el proyecto:

| Métrica / Dimensión | Escenario Pequeño | Escenario Mediano | Escenario Grande |
| :--- | :---: | :---: | :---: |
| **Eventos ($\|E\|$)** | 23 | 176 | 298 |
| **Salones ($\|R\|$)** | 21 | 21 | 101 |
| **Franjas Horarias ($\|T\|$)** | 78 | 78 | 78 |
| **Secciones ($\|S\|$)** | 9 | 68 | 115 |
| **Docentes ($\|P\|$)** | 4 | 11 | 19 |
| **Currículos ($\|K\|$)** | 1 | 4 | 8 |
| **Combinaciones *Valid_SR*** | 165 | 1,100 | 8,916 |
| **Combinaciones *Valid_ERT*** | 23,234 | 173,784 | 1,466,940 |
| **Variables Teóricas** | 75,584 | 578,346 | 4,707,480 |
| **Variables Reales (MIP/GA)** | **46,680** | **349,010** | **2,943,373** |
| *Reducción de Variables* | *38.24 %* | *39.65 %* | *37.47 %* |
| **Restricciones Teóricas** | 232,442 | 1,984,348 | 17,557,776 |
| **Restricciones Reales (MIP)** | **30,802** | **287,167** | **2,286,849** |
| *Reducción de Restricciones* | *86.75 %* | *85.53 %* | *86.97 %* |

---

## 4. Análisis y Conclusiones del Escalamiento

1. **Eficiencia de la Instanciación Dispersa**:
   * En todos los escenarios, la **reducción de variables es superior al 37%**, lo cual disminuye de manera sustancial la cantidad de variables binarias que el resolvedor Branch-and-Bound de HiGHS debe ramificar.
   * La **reducción de restricciones supera el 85%** de manera uniforme. Esto se debe a que las restricciones complejas (como continuidad y desbordamiento diario) solo se instancian sobre el dominio factible prefiltrado.

2. **Dificultad de los Escenarios**:
   * **Escenario Pequeño** (46,680 variables reales): Es de baja complejidad. Resuelve en segundos tanto por MIP como por GA (el GA converge a factibilidad en fracciones de segundo).
   * **Escenario Mediano** (349,010 variables reales): Representa un reto intermedio, requiriendo un proceso de presolve robusto en el solucionador MIP y un número de generaciones moderado (800 epochs) en el algoritmo genético.
   * **Escenario Grande** (2,943,373 variables reales): Es un problema de gran escala. Sin la reducción de dominio, las 17 millones de restricciones provocarían fallos por falta de memoria RAM. Con el prefiltrado de variables, el espacio de búsqueda se reduce a un tamaño manejable por resolvedores modernos.
