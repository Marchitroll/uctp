# Comparación de Rendimiento y Desviación Relativa

Este reporte compara el desempeño del Algoritmo Genético (GA) contra el modelo exacto de Programación Lineal Entera Mixta (MIP) para la planificación horaria de la UCTP.

## Tabla Comparativa

| Escala | $Z_{\text{MIP}}$ | $Z_{\text{AG}}$ (Mejor) | $Z_{\text{AG}}$ (Promedio) | Desviación Relativa (DR %) | Tiempo CPU MIP (s) | Tiempo CPU GA (Prom, s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Pequena | 0.0 | 0.0 | 0.20 | **0.00%** | 44.09 | 1.45 |
| Mediana | 325078.0 | 502.0 | 538.70 | **-99.85%** | 7704.53 | 74.78 |
| Grande | 7328514.0 | 973.0 | 1061.45 | **-99.99%** | 183286.53 | 1210.26 |

## Definiciones

* **$Z_{\text{MIP}}$**: Penalización blanda total obtenida por el solucionador MIP (óptimo o mejor límite entero encontrado).
* **$Z_{\text{AG}}$ (Mejor)**: La menor penalización blanda alcanzada por el Algoritmo Genético a lo largo de las 20 corridas.
* **Desviación Relativa (DR %)**: Medida porcentual de qué tan cerca estuvo la metaheurística del óptimo exacto, calculada como:
  $$\text{DR } (\%) = \frac{Z_{\text{AG}} - Z_{\text{MIP}}}{Z_{\text{MIP}}} \times 100$$
  *Un valor de 0.00% indica que el GA encontró una solución con la misma calidad que el modelo exacto (óptima en este caso).* 
