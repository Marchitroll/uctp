# Origen y Generación del Dataset

**Fecha de actualización:** 19 de octubre de 2026

Reglas y configuración del script `generador_dataset.py` para construir las instancias del problema UCTP.

---

## 1. Fuente Curricular

Basado en la carrera de Ingeniería de Sistemas:
* **40 asignaturas obligatorias:** Niveles 03 al 10.
* **22 asignaturas electivas:** Niveles 06 al 10.
* **Requisitos de espacio:** Mobiliario estándar (`mesa`), computadoras (`pc`) o aceleración GPU (`deep_learning`).

---

## 2. Parámetros Operativos Institucionales (`config.json`)

Parámetros institucionales configurados en `config.json`. La estructura semanal de 86 franjas horarias, la modalidad virtual de los jueves y el horario de almuerzo se detallan en [franjas_horarias.md](franjas_horarias.md).

---

## 3. Reglas de Generación (`generador_dataset.py`)

Generación determinista con semilla base `SEED = 50`.

### 3.1 Cursos y Secciones
* **Secciones por curso:** 1 a 3 secciones aleatorias.
* **Matrícula por sección:** 25 a 36 alumnos.

### 3.2 Eventos de Clase
* **Carga lectiva semanal:** Cada asignatura define sus horas semanales en la malla (4h, 5h, 6h o 7h), las cuales se descomponen en 2 o 3 bloques indivisibles de 2 o 3 horas lectivas:
  * **4 horas semanales (2 días):** Bloques base de `[2, 2]`.
  * **5 horas semanales (2 días):** Bloques base de `[2, 3]`, cuyas secciones permutan en `[2, 3]` y `[3, 2]`.
  * **6 horas semanales (2 días):** Bloques base de `[3, 3]` (política institucional para ciencias básicas).
  * **7 horas semanales (3 días):** Bloques base de `[2, 2, 3]`, cuyas secciones permutan en `[2, 2, 3]`, `[2, 3, 2]` y `[3, 2, 2]`.
* Todos los eventos de una misma sección se asignan al mismo docente.

### 3.3 Profesores y Compatibilidad de Áreas
Cinco áreas de especialidad y sus compatibilidades cruzadas:

| Especialidad Principal | Área Secundaria Permitida |
| :--- | :--- |
| `INGENIERIA_SOFTWARE` | `SISTEMAS_INFORMACION` |
| `SISTEMAS_INFORMACION` | `INGENIERIA_SOFTWARE` |
| `TECNOLOGIAS_INFORMACION` | `INGENIERIA_SOFTWARE` |
| `CIENCIAS_BASICAS` | `INGENIERIA_SOFTWARE` |
| `GESTION_PROYECTOS` | `SISTEMAS_INFORMACION` |

* **Prioridad de asignación:** (1) Misma asignatura preasignada, (2) Misma área, (3) Menor carga acumulada.
* **Carga máxima:** 48 horas semanales por profesor.

### 3.4 Disponibilidad Docente
* **Días disponibles:** Mínimo 4 días hábiles más el jueves (virtual obligatorio).
* **Turnos:** Mañana (primer 70% de la jornada), Tarde (último 70%) o Completo (100%).
* Docentes con más de 12 horas lectivas semanales reciben turno completo.

### 3.5 Salones
* **Salón Virtual (`r_virtual`):** Capacidad 99,999 alumnos, todas las características técnicas. Opera los jueves.
* **Salones Físicos:** Capacidad 36 alumnos. Operan de lunes a sábado (excepto jueves).
  * 1 salón con `deep_learning`.
  * ~60% con computadoras (`pc`).
  * ~40% con mobiliario estándar (`mesa`).

### 3.6 Currículos (CB-CTT)
Un currículo por nivel académico, agrupando sus asignaturas obligatorias y electivas elegibles.

---

## 4. Banco de Instancias (Matriz 3 × 3)

Nueve instancias semi-sintéticas evaluadas (`{escala}_s{semilla}`):

| Escala | Instancia | Semilla | Niveles | Cursos | Secciones | Eventos | Docentes | Salones Físicos | Salón Virtual |
| :--- | :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Pequeña** | `pequena_s1` | 1 | Nivel 03 | 6 | 9 | 18 | 15 | 20 | 1 |
| **Pequeña** | `pequena_s2` | 2 | Nivel 03 | 6 | 8 | 16 | 15 | 20 | 1 |
| **Pequeña** | `pequena_s3` | 3 | Nivel 03 | 6 | 10 | 20 | 15 | 20 | 1 |
| **Mediana** | `mediana_s1` | 1 | Niveles 03–06 | 37 | 74 | 153 | 15 | 20 | 1 |
| **Mediana** | `mediana_s2` | 2 | Niveles 03–06 | 37 | 74 | 153 | 15 | 20 | 1 |
| **Mediana** | `mediana_s3` | 3 | Niveles 03–06 | 37 | 70 | 146 | 15 | 20 | 1 |
| **Grande** | `grande_s1` | 1 | Niveles 03–10 | 62 | 122 | 252 | 50 | 100 | 1 |
| **Grande** | `grande_s2` | 2 | Niveles 03–10 | 62 | 124 | 254 | 50 | 100 | 1 |
| **Grande** | `grande_s3` | 3 | Niveles 03–10 | 62 | 123 | 255 | 50 | 100 | 1 |

Generación por comando:
```bash
uv run python generador_dataset.py --instancia pequena --semilla 1 --dir_salida dataset/pequena_s1
uv run python generador_dataset.py --instancia mediana --semilla 2 --dir_salida dataset/mediana_s2
uv run python generador_dataset.py --instancia grande --semilla 3 --dir_salida dataset/grande_s3
```

---

## 5. Estructura de Archivos Generados (`dataset/`)

Archivos CSV exportados en UTF-8:

| Archivo | Campos Clave | Descripción |
| :--- | :--- | :--- |
| `cursos.csv` | `id_curso`, `requisitos`, `horas_semanales` | Asignaturas, requerimientos de infraestructura y carga lectiva semanal. |
| `secciones.csv` | `id_seccion`, `id_curso`, `num_alumnos` | Secciones y alumnos matriculados. |
| `eventos.csv` | `id_evento`, `id_seccion`, `id_profesor`, `duracion` | Bloques indivisibles de clase. |
| `profesores.csv` | `id_profesor`, `nombre`, `especialidad` | Catálogo docente y especialidad. |
| `profesores_disponibilidad.csv` | `id_profesor`, `dia`, `franja_inicio`, `franja_fin` | Franjas disponibles por profesor. |
| `salones.csv` | `id_salon`, `capacidad`, `es_virtual`, `caracteristicas` | Aulas, aforo y equipamiento. |
| `curriculos.csv` | `id_curriculo`, `nombre` | Currículos por ciclo. |
| `curriculo_evento.csv` | `id_curriculo`, `id_evento` | Pertenencia de eventos a currículos. |
