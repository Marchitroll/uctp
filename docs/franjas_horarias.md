# Matriz de Franjas Horarias (UCTP)

Esta guía detalla cómo se organizan y codifican las 83 franjas horarias semanales del problema UCTP. 

En el modelo de optimización, el tiempo se representa mediante números enteros continuos del 1 al 83 (IDs globales). Esta matriz detalla cómo se mapea cada ID global a un día, hora local, periodo de almuerzo y restricción de infraestructura.

---

## Matriz Semanal de Franjas (1 a 83)

| Hora / Franja Local | Lunes | Martes | Miércoles | Jueves (Virtual) | Viernes | Sábado |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **07:00 - 08:00** (F1) | **1** | **16** | **31** | **46** | **61** | **76** |
| **08:00 - 09:00** (F2) | **2** | **17** | **32** | **47** | **62** | **77** |
| **09:00 - 10:00** (F3) | **3** | **18** | **33** | **48** | **63** | **78** |
| **10:00 - 11:00** (F4) | **4** | **19** | **34** | **49** | **64** | **79** |
| **11:00 - 12:00** (F5) | **5** | **20** | **35** | **50** | **65** | **80** |
| **12:00 - 13:00** (F6) | **6** (Almuerzo) | **21** (Almuerzo) | **36** (Almuerzo) | **51** | **66** (Almuerzo) | **81** |
| **13:00 - 14:00** (F7) | **7** | **22** | **37** | **52** | **67** | **82** |
| **14:00 - 15:00** (F8) | **8** | **23** | **38** | **53** | **68** | **83** |
| **15:00 - 16:00** (F9) | **9** | **24** | **39** | **54** | **69** | *No Disponible* |
| **16:00 - 17:00** (F10) | **10** | **25** | **40** | **55** | **70** | *No Disponible* |
| **17:00 - 18:00** (F11) | **11** | **26** | **41** | **56** | **71** | *No Disponible* |
| **18:00 - 19:00** (F12) | **12** | **27** | **42** | **57** | **72** | *No Disponible* |
| **19:00 - 20:00** (F13) | **13** | **28** | **43** | **58** | **73** | *No Disponible* |
| **20:00 - 21:00** (F14) | **14** | **29** | **44** | **59** | **74** | *No Disponible* |
| **21:00 - 22:00** (F15) | **15** | **30** | **45** | **60** | **75** | *No Disponible* |

---

## Leyenda y Reglas Especiales de la Configuración

### 1. Franjas Totales por Día
* **Lunes a Viernes:** Cuentan con 15 franjas diarias (de 07:00 a 22:00).
* **Sábado:** Cuenta únicamente con 8 franjas diarias (de 07:00 a 15:00). Las celdas marcadas como *No Disponible* no forman parte del conjunto de variables del modelo.

### 2. Periodos de Almuerzo (Penalizados con peso WA = 1)
El almuerzo está fijado en la F6 (12:00 - 13:00) de cada día, pero con excepciones:
* **Con Almuerzo (Penalizados):** Lunes (6), Martes (21), Miércoles (36) y Viernes (66). Si se programa una clase presencial en estas franjas, se acumula penalización en la función objetivo (Z).
* **Sin Almuerzo (Libres de Penalización):** Jueves (51) y Sábado (81).
  * El Sábado no se penaliza porque la jornada presencial es reducida.
  * El Jueves no se penaliza porque es el día de cierre 100% virtual (alumnos y docentes están en sus hogares y no requieren franja de almuerzo institucional en el campus).

### 3. Operatividad Física vs. Virtual (Regla dia_cierre = Jueves)
El modelo segmenta las aulas de la siguiente manera:
* **Salones Físicos:** Solo operan en los días físicos (Lunes, Martes, Miércoles, Viernes y Sábado). Tienen prohibido programar clases en Jueves.
* **Salones Virtuales (Teams/Zoom):** Solo operan el Jueves (franjas 46 a 60). Tienen prohibido programar clases los demás días.
