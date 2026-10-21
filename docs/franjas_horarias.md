# Matriz de Franjas Horarias (UCTP)

**Fecha de actualización:** 19 de octubre de 2026

Discretización de la semana académica en 86 franjas horarias de 1 hora (IDs globales 1 al 86).

---

## Matriz Semanal de Franjas (1 a 86)

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
| **15:00 - 16:00** (F9) | **9** | **24** | **39** | **54** | **69** | **84** |
| **16:00 - 17:00** (F10) | **10** | **25** | **40** | **55** | **70** | **85** |
| **17:00 - 18:00** (F11) | **11** | **26** | **41** | **56** | **71** | **86** |
| **18:00 - 19:00** (F12) | **12** | **27** | **42** | **57** | **72** | *No Disponible* |
| **19:00 - 20:00** (F13) | **13** | **28** | **43** | **58** | **73** | *No Disponible* |
| **20:00 - 21:00** (F14) | **14** | **29** | **44** | **59** | **74** | *No Disponible* |
| **21:00 - 22:00** (F15) | **15** | **30** | **45** | **60** | **75** | *No Disponible* |

---

## Reglas Operativas

1. **Jornadas:** Lunes a viernes 15 franjas (07:00–22:00); sábado 11 franjas (07:00–18:00).
2. **Almuerzo ($W_A = 1$):** Franja 6 (12:00–13:00). Penalizado lunes (6), martes (21), miércoles (36) y viernes (66). Exento jueves (virtual) y sábados.
3. **Modalidad:** Jueves es 100% virtual (`r_virtual`, franjas 46–60). Los salones físicos operan de lunes a sábado excepto jueves.
