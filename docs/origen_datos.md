# Origen y Generación del Dataset

Documenta el origen de los datos y las reglas del script `generador_dataset.py` para construir las instancias del problema UCTP.

---

## 1. Fuente Curricular

Los cursos se basan en el plan de estudios de la carrera de Ingeniería de Sistemas:
* **Asignaturas obligatorias:** 40 asignaturas distribuidas del Nivel 03 al Nivel 10 (malla principal).
* **Asignaturas electivas:** 22 asignaturas clasificadas por nivel mínimo de elegibilidad (desde Nivel 06 hasta Nivel 10) y prerrequisitos de infraestructura.

Cada asignatura define sus requisitos de espacio: mobiliario estándar (`mesa`), computadoras (`pc`) o hardware especializado (`deep_learning`).

---

## 2. Parámetros Operativos Institucionales (`config.json`)

Los parámetros temporales e institucionales se configuran en `config.json`:
* **Días lectivos:** 6 días (Lunes a Sábado).
* **Franjas horarias:** 86 franjas semanales de 1 hora.
  * Lunes a Viernes: 15 franjas (07:00 a 22:00).
  * Sábado: 11 franjas (07:00 a 18:00).
* **Modalidad virtual (`dia_cierre`):** Jueves. El campus físico no opera y las clases se asignan a salones virtuales.
* **Horario de almuerzo:** Franja 6 (12:00 a 13:00) de Lunes a Viernes (excluyendo Jueves y Sábado).

---

## 3. Reglas de Generación (`generador_dataset.py`)

El script utiliza una semilla fija (`SEED = 50`) para reproducibilidad.

### 3.1. Cursos y Secciones
* **Secciones por curso:** De 1 a 3 secciones generadas aleatoriamente.
* **Matrícula por sección:** De 25 a 36 alumnos.

### 3.2. Eventos de Clase
* **Eventos por sección:** 2 o 3 eventos semanales.
* **Duración:** Bloques continuos de 2 o 3 horas.
* Todos los eventos de una misma sección se asignan obligatoriamente al mismo docente.

### 3.3. Profesores y Asignación
* **Áreas de especialidad (5 áreas):**
  * `INGENIERIA_SOFTWARE`: Programación, desarrollo web/móvil, estructuras de datos, arquitectura de software, DevOps y videojuegos.
  * `SISTEMAS_INFORMACION`: Bases de datos, modelamiento de procesos, sistemas ERP, inteligencia de negocios y analítica.
  * `TECNOLOGIAS_INFORMACION`: Redes, sistemas operativos, ciberseguridad, cloud, IoT, inteligencia artificial y deep learning.
  * `CIENCIAS_BASICAS`: Cálculo, física, estadística y estructuras discretas.
  * `GESTION_PROYECTOS`: Costeo, finanzas, investigación de operaciones, dirección de proyectos, auditoría y seminarios.
* **Compatibilidad cruzada (`COMPATIBILIDAD`):** Define qué áreas adicionales puede asumir un docente según su especialidad principal:
  * `INGENIERIA_SOFTWARE` $\rightarrow$ puede dictar `SISTEMAS_INFORMACION`.
  * `SISTEMAS_INFORMACION` $\rightarrow$ puede dictar `INGENIERIA_SOFTWARE`.
  * `TECNOLOGIAS_INFORMACION` $\rightarrow$ puede dictar `INGENIERIA_SOFTWARE`.
  * `CIENCIAS_BASICAS` $\rightarrow$ puede dictar `INGENIERIA_SOFTWARE`.
  * `GESTION_PROYECTOS` $\rightarrow$ puede dictar `SISTEMAS_INFORMACION`.
* **Criterio de asignación:** Se filtran los docentes compatibles con el área del curso y se prioriza:
  1. Docente que ya dicte otra sección de la misma asignatura.
  2. Docente que dicte asignaturas de la misma área.
  3. Docente compatible con menor carga acumulada.
* **Carga máxima semanal:** 48 horas por profesor.

### 3.4. Disponibilidad Docente
* **Días disponibles:** Mínimo 4 días hábiles aleatorios, más el Jueves (virtual) obligatorio.
* **Turnos:** Mañana (primer 70% de la jornada), Tarde (último 70%) o Completo (100%).
* **Control de factibilidad:** Docentes con más de 12 horas lectivas semanales reciben disponibilidad en jornada completa durante todos sus días hábiles.

### 3.5. Salones
* **Salón Virtual (`r_virtual`):** 1 salón con capacidad de 99,999 alumnos, habilitado para todas las características técnicas. Opera únicamente los Jueves.
* **Salones Físicos:** Capacidad de 36 alumnos. Operan de Lunes a Sábado (excepto Jueves).
  * 1 salón con soporte para `deep_learning`.
  * ~60% equipados con computadoras (`pc`).
  * ~40% aulas estándar (`mesa`).

### 3.6. Currículos (CB-CTT)
* Se define un currículo por cada nivel académico considerado.
* Cada currículo asocia los eventos de sus asignaturas obligatorias y de las asignaturas electivas cuyo nivel mínimo sea menor o igual al del currículo.

---

## 4. Escalas de Instancias

El parámetro `--instancia` define la escala del problema:

| Escala | Parámetro | Niveles Curriculares | Cursos | Profesores | Salones Físicos | Salones Virtuales |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **Pequeña** | `pequena` | Nivel 03 (1 nivel) | 6 | 15 | 20 | 1 |
| **Mediana** | `mediana` | Niveles 03 al 06 (4 niveles) | 37 | 15 | 20 | 1 |
| **Grande** | `grande` | Niveles 03 al 10 (8 niveles) | 62 | 50 | 100 | 1 |

---

## 5. Estructura de Archivos Generados (`dataset/`)

El generador exporta 8 archivos CSV en formato UTF-8:

| Archivo | Campos | Descripción |
| :--- | :--- | :--- |
| `cursos.csv` | `id_curso`, `nombre`, `requisitos` | Catálogo de asignaturas y requerimientos de infraestructura. |
| `secciones.csv` | `id_seccion`, `id_curso`, `num_alumnos` | Secciones académicas y número de matriculados. |
| `eventos.csv` | `id_evento`, `id_seccion`, `id_profesor`, `duracion` | Unidades indivisibles de programación horaria. |
| `profesores.csv` | `id_profesor`, `nombre`, `especialidad` | Catálogo docente y área de especialidad. |
| `profesores_disponibilidad.csv` | `id_profesor`, `dia`, `franja_inicio`, `franja_fin` | Bloques horarios de disponibilidad docente. |
| `salones.csv` | `id_salon`, `capacidad`, `es_virtual`, `caracteristicas` | Aulas físicas y virtuales con aforo y equipamiento. |
| `curriculos.csv` | `id_curriculo`, `nombre` | Rutas curriculares por nivel de estudio. |
| `curriculo_evento.csv` | `id_curriculo`, `id_evento` | Tabla puente de pertenencia de eventos a currículos. |
