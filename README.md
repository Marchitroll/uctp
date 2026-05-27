# UCTP - Universidad

## 1. Generación de Dataset

Para generar el conjunto de datos de entrada:

```bash
python generador_dataset.py --instancia [pequena|mediana|grande]
```
* Nota: Si no se especifica `--instancia`, por defecto se generará la instancia `pequena`.

## 2. Ejecución del Modelo de Optimización

Para resolver el modelo e importar los horarios:

```bash
python modelo_MIP.py --horas [HORAS]
# O alternativamente en minutos:
python modelo_MIP.py --minutos [MINUTOS]
```
* Nota: Si no se especifica ningún argumento de tiempo, por defecto se empleará un límite de 1.0 hora.

## 3. Ejecución del Algoritmo Genético

Para resolver empleando el Algoritmo Genético:

```bash
python modelo_GA.py --horas [HORAS]
# O alternativamente:
python modelo_GA.py --minutos [MINUTOS]
# O alternativamente por generaciones:
python modelo_GA.py --epoch [EPOCHS] --pop-size [POPSIZE]
```
* Nota: Soporta el argumento `--corridas N` para especificar el número de ejecuciones independientes (por defecto 1, formal 20) y persiste estadísticas consolidadas en `resultados_GA.csv`.

## 4. Guía Rápida por Escala (Pequeña, Mediana, Grande)

Para trabajar con una escala específica (generación de datos y optimización), ejecute los siguientes comandos generales:

### Instancia Pequeña
```bash
# 1. Generar dataset
python generador_dataset.py --instancia pequena

# 2. Ejecutar optimizador (MIP o GA)
python modelo_MIP.py
python modelo_GA.py --config pequena
```

### Instancia Mediana
```bash
# 1. Generar dataset
python generador_dataset.py --instancia mediana

# 2. Ejecutar optimizador (MIP o GA)
python modelo_MIP.py
python modelo_GA.py --config mediana
```

### Instancia Grande
```bash
# 1. Generar dataset
python generador_dataset.py --instancia grande

# 2. Ejecutar optimizador (MIP o GA)
python modelo_MIP.py
python modelo_GA.py --config grande
```


