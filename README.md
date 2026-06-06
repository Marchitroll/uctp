# Planificación Horaria Universitaria (UCTP) - Ecosistema de Optimización

Este repositorio contiene la infraestructura de optimización matemática y heurística para resolver el problema de planificación de horarios universitarios (University Course Timetabling Problem - UCTP) bajo restricciones académicas e institucionales complejas.

La solución del problema se aborda mediante dos metodologías:
1. **Programación Lineal Entera Mixta (MIP)** utilizando el solucionador de código abierto HiGHS (v1.13.1) mediante la API de `python-mip`.
2. **Algoritmo Genético (GA)** con decodificador heurístico basado en prioridad de saturación (**Most Constrained First**) y reparación de colisiones.

---

## 1. Portal de Documentación

Toda la documentación conceptual, matemática y experimental del proyecto se encuentra centralizada y estructurada en español dentro de la carpeta `docs/`. A continuación se presenta el índice de acceso:

* **[modelo_matematico.md](docs/modelo_matematico.md)**: Especificación teórica del modelo matemático de optimización, incluyendo definiciones de conjuntos, variables de decisión, parámetros y la formulación formal de todas las restricciones duras y blandas.
* **[analisis_complejidad.md](docs/analisis_complejidad.md)**: Estimación teórica y auditoría real del tamaño del espacio de búsqueda (variables, restricciones y dominios factibles) para los escenarios Pequeño, Mediano y Grande.
* **[franjas_horarias.md](docs/franjas_horarias.md)**: Estructuración semanal de las 78 franjas horarias académicas, mapeo de periodos de almuerzo y políticas de operatividad presencial vs. virtual.
* **[pseudocodigo_ga.md](docs/pseudocodigo_ga.md)**: Descripción lógica detallada del Algoritmo Genético, su bucle evolutivo y el operador de reparación heurística.
* **[resultados_experimentales.md](docs/resultados_experimentales.md)**: Reporte consolidado de resultados en las tres escalas, desglosando tiempos de CPU, penalizaciones blandas e indicadores de factibilidad.
* **[comparacion_metodos.md](docs/comparacion_metodos.md)**: Tabla unificada de rendimientos y cálculo del indicador de Desviación Relativa (DR %) entre ambos métodos.

---

## 2. Instalación y Configuración del Entorno

Para asegurar la correcta ejecución del entorno de desarrollo y la reproducibilidad de las pruebas experimentales en sistemas Anaconda:

### Crear y Activar el Entorno Virtual Conda
```bash
# Crear el entorno Conda con Python 3.13
conda create -n uctp python=3.13 -y

# Activar el entorno
conda activate uctp
```

### Instalar Dependencias
Instale el conjunto de librerías y componentes requeridos a través del archivo `requirements.txt`:
```bash
pip install -r requirements.txt
```
*Nota: Para habilitar el solucionador HiGHS en Windows mediante `python-mip`, el paquete `highsbox` se incorpora automáticamente en la instalación.*

---

## 3. Guía de Uso del Ecosistema de Programas

### 3.1 Generación del Conjunto de Datos
Para instanciar los archivos CSV del esquema relacional en base a los parámetros institucionales, ejecute el generador especificando la escala deseada (`pequena`, `mediana` o `grande`):
```bash
python generador_dataset.py --instancia [pequena|mediana|grande]
# O mediante su atajo:
python generador_dataset.py -i [pequena|mediana|grande]
```
*Nota: Si se omite el argumento de escala, el programa instanciará por defecto la escala `pequena`.*

### 3.2 Resolución Mediante Programación Entera Mixta (MIP)
Para resolver el modelo matemático exacto utilizando el solucionador HiGHS, puede parametrizar el límite de tiempo máximo en horas o minutos (el valor por defecto es de 2.0 horas):
```bash
# Limitar tiempo en horas
python modelo_MIP.py --horas [HORAS]

# Limitar tiempo en minutos
python modelo_MIP.py --minutos [MINUTOS]
```

### 3.3 Resolución Mediante Algoritmo Genético (GA)
Para resolver empleando el Algoritmo Genético, configure el número de corridas independientes deseadas para el análisis estadístico (las métricas se exportan en `resultados_GA/`):
```bash
python modelo_GA.py --corridas [NÚMERO_DE_CORRIDAS]
```

#### Parámetros Adicionales del Algoritmo Genético:
* **Límite de Tiempo Máximo**:
  ```bash
  python modelo_GA.py --horas [HORAS]
  # O alternativamente:
  python modelo_GA.py --minutos [MINUTOS]
  ```
* **Generaciones y Población**:
  ```bash
  python modelo_GA.py --epoch [EPOCHS] --pop-size [POPSIZE]
  ```
* **Forzar Escala de la Instancia**:
  ```bash
  python modelo_GA.py --instancia [pequena|mediana|grande]
  # O mediante su atajo:
  python modelo_GA.py -i [pequena|mediana|grande]
  ```

---

## 4. Flujo de Ejecución por Escala

Para ejecutar de manera ordenada un análisis completo sobre cualquiera de los escenarios, aplique la siguiente secuencia de comandos:

### Escenario Pequeño
```bash
# 1. Generar la base de datos de escala pequeña
python generador_dataset.py --instancia pequena

# 2. Resolver con el método MIP y con el Algoritmo Genético (20 corridas)
python modelo_MIP.py
python modelo_GA.py --corridas 20
```

### Escenario Mediano
```bash
# 1. Generar la base de datos de escala mediana
python generador_dataset.py --instancia mediana

# 2. Resolver con el método MIP y con el Algoritmo Genético (20 corridas)
python modelo_MIP.py
python modelo_GA.py --corridas 20
```

### Escenario Grande
```bash
# 1. Generar la base de datos de escala grande
python generador_dataset.py --instancia grande

# 2. Resolver con el método MIP y con el Algoritmo Genético (20 corridas)
python modelo_MIP.py
python modelo_GA.py --corridas 20
```
