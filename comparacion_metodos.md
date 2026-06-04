# Comparación de Rendimiento y Desviación Relativa

Este reporte compara el desempeño del Algoritmo Genético (GA) contra el modelo exacto de Programación Lineal Entera Mixta (MIP) para la planificación horaria de la UCTP.

## Tabla Comparativa

| Escala | $Z_{\text{MIP}}$ | $Z_{\text{AG}}$ (Mejor) | $Z_{\text{AG}}$ (Promedio) | Desviación Relativa (DR %) | Tiempo CPU MIP (s) | Tiempo CPU GA (Prom, s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Pequena | 0.0 | 0.0 | 0.65 | **0.00%** | 37.03 | 1.43 |
| Mediana | N/A | N/A | N/A | Faltan resultados de: MIP | N/A | N/A |
| Grande | N/A | N/A | N/A | Faltan resultados de: MIP, GA | N/A | N/A |

## Definiciones

* **$Z_{\text{MIP}}$**: Penalización blanda total obtenida por el solucionador MIP (óptimo o mejor límite entero encontrado).
* **$Z_{\text{AG}}$ (Mejor)**: La menor penalización blanda alcanzada por el Algoritmo Genético a lo largo de las 20 corridas.
* **Desviación Relativa (DR %)**: Medida porcentual de qué tan cerca estuvo la metaheurística del óptimo exacto, calculada como:
  $$\text{DR } (\%) = \frac{Z_{\text{AG}} - Z_{\text{MIP}}}{Z_{\text{MIP}}} \times 100$$
  *Un valor de 0.00% indica que el GA encontró una solución con la misma calidad que el modelo exacto (óptima en este caso).* 
