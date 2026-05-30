# UCTP - Universidad

## 0. Instalación y Configuración del Entorno

Para configurar el entorno de ejecución utilizando Anaconda y asegurar la reproductibilidad de los resultados:

### Crear y activar el entorno Conda
```bash
# Crear el entorno con Python 3.13
conda create -n uctp python=3.13 -y

# Activar el entorno
conda activate uctp
```

### Instalar dependencias
Instale los paquetes necesarios a través del archivo `requirements.txt`:
```bash
pip install -r requirements.txt
```
* Nota: Para utilizar el solucionador HiGHS con la librería `mip` en Windows, se incluye el paquete `highsbox` dentro de las dependencias de forma automática.

## 1. Generación de Dataset

Para generar el conjunto de datos de entrada:

```bash
python generador_dataset.py --instancia [pequena|mediana|grande]
# O alternativamente con el atajo:
python generador_dataset.py -i [pequena|mediana|grande]
```
* Nota: Si no se especifica `--instancia` (o `-i`), por defecto se generará la instancia `pequena`.

## 2. Ejecución del Modelo de Optimización

Para resolver el modelo e importar los horarios:

```bash
python modelo_MIP.py --horas [HORAS]
# O alternativamente en minutos:
python modelo_MIP.py --minutos [MINUTOS]
```
* Nota: Si no se especifica ningún argumento de tiempo, por defecto se empleará un límite de 1.0 hora.

## 3. Ejecución del Algoritmo Genético

Para resolver empleando el Algoritmo Genético basándose en corridas independientes (por defecto se ejecuta 1 corrida y las estadísticas consolidadas se guardan en la carpeta `resultados_GA/` con el nombre `resultados_[pequena|mediana|grande].csv`):

```bash
python modelo_GA.py --corridas [NÚMERO_DE_CORRIDAS]
```

### Opciones Adicionales (Extras)
También es posible parametrizar el proceso de optimización del Algoritmo Genético mediante las siguientes configuraciones adicionales:

* **Por tiempo límite en horas o minutos**:
  ```bash
  python modelo_GA.py --horas [HORAS]
  # O alternativamente:
  python modelo_GA.py --minutos [MINUTOS]
  ```
* **Por número de generaciones (epochs) y tamaño de población**:
  ```bash
  python modelo_GA.py --epoch [EPOCHS] --pop-size [POPSIZE]
  ```
* **Por escala de instancia (forzar configuración de escala específica)**:
  ```bash
  python modelo_GA.py --instancia [pequena|mediana|grande]
  # O usando el atajo:
  python modelo_GA.py -i [pequena|mediana|grande]
  ```

## 4. Guía Rápida por Escala (Pequeña, Mediana, Grande)

Para trabajar con una escala específica (generación de datos y optimización), ejecute los siguientes comandos generales:

### Instancia Pequeña
```bash
# 1. Generar dataset
python generador_dataset.py --instancia pequena

# 2. Ejecutar optimizador (MIP o GA)
python modelo_MIP.py
python modelo_GA.py --corridas 20
```

### Instancia Mediana
```bash
# 1. Generar dataset
python generador_dataset.py --instancia mediana

# 2. Ejecutar optimizador (MIP o GA)
python modelo_MIP.py
python modelo_GA.py --corridas 20
```

### Instancia Grande
```bash
# 1. Generar dataset
python generador_dataset.py --instancia grande

# 2. Ejecutar optimizador (MIP o GA)
python modelo_MIP.py
python modelo_GA.py --corridas 20
```


