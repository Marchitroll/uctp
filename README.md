# Planificación Horaria Universitaria (UCTP) - Ecosistema de Optimización

Este repositorio contiene la infraestructura de optimización matemática y metaheurística para resolver el problema de planificación de horarios universitarios (University Course Timetabling Problem - UCTP) bajo restricciones académicas, curriculares e institucionales complejas.

La solución del problema se aborda mediante cinco metodologías comparables bajo un marco unificado de evaluación:
1. **Programación Lineal Entera Mixta (MIP)**: Modelo exacto implementado en `modelo_MIP.py` utilizando el solucionador de código abierto HiGHS (v1.13.1) a través de `python-mip` y `highsbox`.
2. **Algoritmo Genético Híbrido (HGA)**: Metaheurística memética en `modelo_HGA.py` con reducción de dominio (`valid_starts`), operador constructivo *Most Constrained First* (MCF), reparación constructiva de colisiones y aprendizaje lamarckiano.
3. **Algoritmo Genético Clásico (GA)**: Metaheurística poblacional canónica en `modelo_GA.py` basada en cruzamiento uniforme, mutación y selección por torneo sobre variables discretas sin reparación heurística.
4. **Búsqueda Tabú (TS)**: Metaheurística de trayectoria en `modelo_TS.py` con generación de vecindarios discretos sobre inicios factibles, memoria tabú de estados recientes y criterio de aspiración.
5. **Recocido Simulado (SA)**: Metaheurística de trayectoria estocástica en `modelo_SA.py` con perturbación discreta y criterio de aceptación de Metropolis con enfriamiento progresivo.

---

## 1. Portal de Documentación

Toda la documentación conceptual, matemática y experimental del proyecto se encuentra centralizada y estructurada en español dentro de la carpeta `docs/`:

* **[objetivos.md](docs/objetivos.md)**: Definición formal del objetivo general y los objetivos específicos de la investigación.
* **[modelo_matematico.md](docs/modelo_matematico.md)**: Especificación teórica del modelo matemático de optimización, formulación de las 5 restricciones duras, 4 restricciones blandas (Almuerzo, Espaciado, Jueves/Sábado y Huecos docentes) y función objetivo $\min Z$.
* **[franjas_horarias.md](docs/franjas_horarias.md)**: Estructuración semanal de las 86 franjas horarias académicas, mapeo de periodos de almuerzo y políticas de operatividad presencial vs. virtual.
* **[pseudocodigo_ga.md](docs/pseudocodigo_ga.md)**: Descripción lógica detallada del Algoritmo Genético Híbrido, bucle evolutivo y heurística constructiva MCF.
* **[resultados_experimentales.md](docs/resultados_experimentales.md)**: Reporte consolidado de resultados en las tres escalas.
* **[comparacion_metodos.md](docs/comparacion_metodos.md)**: Tabla consolidada de benchmark multi-método con cálculo de $RPD$, $SR$, $DF$, $TTF$, $NFE$, tiempos CPU y auditoría del entorno de cómputo.
* **[metricas_evaluacion.md](docs/metricas_evaluacion.md)**: Marco formal de evaluación estructurado en tres dimensiones (Viabilidad Operativa, Calidad de Optimización y Eficiencia Computacional) con base en la literatura (*Abdipoor et al. 2025; Rohaizad et al. 2026; Bashab et al. 2023*).

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
Instale el conjunto de librerías requeridas a través del archivo `requirements.txt`:
```bash
pip install -r requirements.txt
```
*Nota: Para habilitar el solucionador HiGHS en Windows mediante `python-mip`, el paquete `highsbox` se incorpora automáticamente en la instalación.*

---

## 3. Guía de Uso de los Métodos

### 3.1 Generación del Conjunto de Datos
Para instanciar los archivos CSV del esquema relacional en base a los parámetros institucionales, ejecute el generador especificando la escala deseada (`pequena`, `mediana` o `grande`):
```bash
python generador_dataset.py --instancia [pequena|mediana|grande]
```

### 3.2 Programación Lineal Entera Mixta (MIP)
```bash
# Ejecutar con límite en minutos (por defecto: 120 min)
python modelo_MIP.py --minutos 30
```

### 3.3 Algoritmo Genético Híbrido (HGA)
```bash
# Ejecución multi-corrida (20 corridas por defecto)
python modelo_HGA.py --corridas 20 --minutos 5
```

### 3.4 Algoritmo Genético Clásico (GA)
```bash
python modelo_GA.py --corridas 20 --minutos 5
```

### 3.5 Búsqueda Tabú (TS)
```bash
python modelo_TS.py --corridas 20 --minutos 5
```

### 3.6 Recocido Simulado (SA)
```bash
python modelo_SA.py --corridas 20 --minutos 5
```

### 3.7 Reporte Comparativo Consolidado
Para procesar las salidas JSON de todos los métodos, calcular el $RPD$ robusto y actualizar `docs/comparacion_metodos.md`:
```bash
python reporte_desviacion.py
```

---

## 4. Flujo de Ejecución por Escala

Para ejecutar de manera ordenada un benchmark completo sobre cualquiera de los escenarios:

```bash
# 1. Generar datos de la instancia (ej. pequeña)
python generador_dataset.py --instancia pequena

# 2. Ejecutar los 5 modelos
python modelo_MIP.py
python modelo_HGA.py --corridas 20
python modelo_GA.py --corridas 20
python modelo_TS.py --corridas 20
python modelo_SA.py --corridas 20

# 3. Consolidar métricas y generar reporte comparativo
python reporte_desviacion.py
```
