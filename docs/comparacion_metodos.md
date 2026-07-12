# Comparación de Rendimiento y Desviación Relativa

Este reporte compara el desempeño del Algoritmo Genético (GA) contra el modelo exacto de Programación Lineal Entera Mixta (MIP) para la planificación horaria de la UCTP.

## Tabla Comparativa

| Escala | $Z_{\text{MIP}}$ | $Z_{\text{AG}}$ (Mejor) | $Z_{\text{AG}}$ (Promedio) | Desviación Relativa (DR %) | Tiempo CPU MIP (s) | Tiempo CPU GA (Prom, s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Pequena | 0.0 | 0.0 | 0.10 | **0.00%** | 42.03 | 2.49 |
| Mediana | 434144.0 | 457.0 | 540.47 | **-99.89%** | 7874.11 | 119.16 |
| Grande | 3927356.0 | 928.0 | 1050.07 | **-99.98%** | 13935.66 | 1839.98 |

## Definiciones

* **$Z_{\text{MIP}}$**: Penalización blanda total obtenida por el solucionador MIP (óptimo o mejor límite entero encontrado).
* **$Z_{\text{AG}}$ (Mejor)**: La menor penalización blanda alcanzada por el Algoritmo Genético a lo largo de las 20 corridas.
* **Desviación Relativa (DR %)**: Medida porcentual de qué tan cerca estuvo la metaheurística del óptimo exacto, calculada como:
  $$\text{DR } (\%) = \frac{Z_{\text{AG}} - Z_{\text{MIP}}}{Z_{\text{MIP}}} \times 100$$
  *Un valor de 0.00% indica que el GA encontró una solución con la misma calidad que el modelo exacto (óptima en este caso).* 
