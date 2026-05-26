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
