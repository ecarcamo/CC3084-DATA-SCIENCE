# 5. Modelos y predicción

## Selección de órdenes

La identificación parte de las ACF y PACF sobre `log1p`. En las series con
persistencia, p y q se exploraron entre 0 y 2. Los picos en el rezago 12
motivaron P y Q entre 0 y 1, con periodo estacional 12. Las conclusiones del
ADF fijaron d=1 y D=1 en seis series. Para marítima se probó d=2 y D=1, sin
interpretar esta decisión como evidencia de estacionariedad.

| Serie | Modelo seleccionado por AIC | Fundamento de p y q |
|---|---|---|
| Total | SARIMA(2,1,2)(1,1,1)12 | PACF corta y ACF persistente con señal anual |
| Vía aérea | SARIMA(2,1,2)(0,1,1)12 | Dependencia corta regular y pico estacional |
| Vía terrestre | SARIMA(0,1,1)(1,1,0)12 | Corte dominante de ACF y componente anual |
| Vía marítima | SARIMA(1,2,2)(1,1,1)12 | ACF irregular, diferencias adicionales y ciclo anual |
| El Salvador | SARIMA(2,1,2)(1,1,1)12 | Dependencia regular mixta y estacionalidad marcada |
| Estados Unidos | SARIMA(1,1,2)(0,1,1)12 | ACF persistente y PACF concentrada en pocos rezagos |
| Honduras | SARIMA(2,1,2)(1,1,0)12 | Dependencia corta con efecto estacional de media móvil |

La rejilla manual evaluó todas las combinaciones de esos rangos y conservó
los tres menores AIC estables por serie. `auto_arima` se ejecutó con la
misma diferenciación y límites. Sus propuestas fueron de orden bajo y
coherentes con las ACF y PACF, aunque no siempre coincidieron con el mínimo
manual porque su búsqueda es escalonada.

## Comparación ARIMA

| Serie | order | seasonal order | AIC | BIC | Ljung-Box p |
|---|---|---|---:|---:|---:|
| Total | (2,1,2) | (1,1,1,12) | 67.96 | 87.41 | 0.0003 |
| Total | (1,1,2) | (1,1,1,12) | 68.55 | 85.22 | 0.0046 |
| Total | (2,1,2) | (1,1,0,12) | 68.96 | 85.69 | 0.0012 |
| Vía aérea | (2,1,2) | (0,1,1,12) | 169.72 | 186.40 | <0.0001 |
| Vía aérea | (0,1,1) | (0,1,1,12) | 176.29 | 184.65 | 0.0060 |
| Vía aérea | (0,1,2) | (0,1,1,12) | 176.98 | 188.10 | 0.0059 |
| Vía terrestre | (0,1,1) | (1,1,0,12) | 124.18 | 132.59 | 0.5395 |
| Vía terrestre | (1,1,0) | (1,1,0,12) | 124.32 | 132.70 | 0.8681 |
| Vía terrestre | (2,1,2) | (0,1,1,12) | 124.94 | 141.62 | <0.0001 |
| Vía marítima | (1,2,2) | (1,1,1,12) | 498.40 | 515.02 | 0.0199 |
| Vía marítima | (2,2,2) | (1,1,1,12) | 500.35 | 519.74 | 0.0202 |
| Vía marítima | (1,2,2) | (0,1,1,12) | 504.06 | 517.91 | 0.0052 |
| El Salvador | (2,1,2) | (1,1,1,12) | 400.62 | 420.07 | 0.1020 |
| El Salvador | (2,1,2) | (0,1,1,12) | 411.54 | 428.21 | 0.0481 |
| El Salvador | (1,1,2) | (0,1,1,12) | 411.80 | 425.70 | 0.0770 |
| Estados Unidos | (1,1,2) | (0,1,1,12) | 367.14 | 381.03 | 0.0427 |
| Estados Unidos | (2,1,1) | (0,1,1,12) | 371.51 | 385.45 | 0.0373 |
| Estados Unidos | (2,1,2) | (0,1,1,12) | 371.96 | 388.64 | 0.0154 |
| Honduras | (2,1,2) | (1,1,0,12) | 359.01 | 375.74 | 0.1854 |
| Honduras | (1,1,2) | (0,1,1,12) | 360.21 | 374.10 | 0.0107 |
| Honduras | (0,1,2) | (0,1,1,12) | 370.32 | 381.44 | 0.0277 |

El menor AIC entre especificaciones estables decide el modelo llevado al
test, pero los residuos matizan la elección. Vía terrestre, El Salvador y
Honduras no rechazan ausencia de autocorrelación al 5 %. Total, vía aérea,
marítima y Estados Unidos sí retienen dependencia residual. Jarque-Bera
rechaza normalidad en todos los modelos seleccionados. Esto limita la
inferencia paramétrica, aunque para pronóstico es más preocupante la
autocorrelación restante.

![Residuos del SARIMA seleccionado, total](../figuras/modelo_total_residuos.png)

![Residuos del SARIMA seleccionado, vía aérea](../figuras/modelo_via_aerea_residuos.png)

![Residuos del SARIMA seleccionado, vía terrestre](../figuras/modelo_via_terrestre_residuos.png)

![Residuos del SARIMA seleccionado, vía marítima](../figuras/modelo_via_maritima_residuos.png)

![Residuos del SARIMA seleccionado, El Salvador](../figuras/modelo_pais_el_salvador_residuos.png)

![Residuos del SARIMA seleccionado, Estados Unidos](../figuras/modelo_pais_estados_unidos_residuos.png)

![Residuos del SARIMA seleccionado, Honduras](../figuras/modelo_pais_honduras_residuos.png)

Además del AIC, la selección exige que el pronóstico a 63 pasos, revertido
a viajeros, no supere tres veces el máximo histórico de la serie. El filtro
es necesario porque el ajuste se hizo sin restricciones de estacionariedad
ni de invertibilidad, de modo que la rejilla completa pudiera converger. De
las 36 especificaciones ajustadas por serie se descartaron 0 en total, 18 en
vía aérea, 2 en terrestre, 2 en marítima, 1 en El Salvador, 24 en Estados
Unidos y 23 en Honduras. Sin ese criterio, varias especificaciones con buen
AIC habrían producido trayectorias explosivas fuera de muestra.

## Algoritmos alternativos

Holt-Winters usa tendencia y estacionalidad aditivas sobre `log1p`. SES
modela únicamente el nivel suavizado. Seasonal naive repite los últimos
doce meses observados y sirve como referencia simple. Prophet incorpora
estacionalidad anual también sobre `log1p`. Los cuatro algoritmos pudieron
ejecutarse, y sus predicciones se revirtieron a viajeros antes de evaluar.

AIC y BIC solo aparecen para SARIMA. No son comparables entre algoritmos
distintos, ni entre series, porque dependen de la función de verosimilitud,
la muestra y la parametrización.

## Resultados fuera de muestra

| Serie | Modelo | AIC | BIC | MAE | RMSE | MAPE |
|---|---|---:|---:|---:|---:|---:|
| Total | SARIMA | 67.96 | 87.41 | 250,723 | 274,290 | 83.48 % |
| Total | Holt-Winters |  |  | 196,956 | 216,457 | 65.30 % |
| Total | SES |  |  | 175,088 | 194,791 | 58.11 % |
| Total | Seasonal naive |  |  | 235,731 | 253,203 | 83.86 % |
| Total | Prophet |  |  | 264,527 | 282,313 | 92.50 % |
| Vía aérea | SARIMA | 169.72 | 186.40 | 73,966 | 77,680 | 77.57 % |
| Vía aérea | Holt-Winters |  |  | 48,043 | 52,231 | 48.51 % |
| Vía aérea | SES |  |  | 36,109 | 41,368 | 35.62 % |
| Vía aérea | Seasonal naive |  |  | 75,104 | 79,077 | 80.58 % |
| Vía aérea | Prophet |  |  | 89,054 | 92,266 | 93.17 % |
| Vía terrestre | SARIMA | 124.18 | 132.59 | 174,971 | 192,354 | 88.63 % |
| Vía terrestre | Holt-Winters |  |  | 148,023 | 164,246 | 73.92 % |
| Vía terrestre | SES |  |  | 140,428 | 156,310 | 71.75 % |
| Vía terrestre | Seasonal naive |  |  | 160,013 | 176,653 | 83.47 % |
| Vía terrestre | Prophet |  |  | 175,767 | 191,877 | 91.07 % |
| Vía marítima | SARIMA | 498.40 | 515.02 | 858 | 1,732 | 100.00 % |
| Vía marítima | Holt-Winters |  |  | 858 | 1,732 | 100.00 % |
| Vía marítima | SES |  |  | 858 | 1,732 | 100.00 % |
| Vía marítima | Seasonal naive |  |  | 858 | 1,732 | 100.00 % |
| Vía marítima | Prophet |  |  | 784 | 1,645 | 86.12 % |
| El Salvador | SARIMA | 400.62 | 420.07 | 113,109 | 123,010 | 97.70 % |
| El Salvador | Holt-Winters |  |  | 101,044 | 111,527 | 81.05 % |
| El Salvador | SES |  |  | 94,064 | 104,531 | 74.32 % |
| El Salvador | Seasonal naive |  |  | 107,474 | 117,633 | 91.60 % |
| El Salvador | Prophet |  |  | 106,744 | 117,498 | 86.64 % |
| Estados Unidos | SARIMA | 367.14 | 381.03 | 42,093 | 45,541 | 88.57 % |
| Estados Unidos | Holt-Winters |  |  | 34,195 | 37,642 | 69.37 % |
| Estados Unidos | SES |  |  | 25,115 | 28,953 | 49.93 % |
| Estados Unidos | Seasonal naive |  |  | 41,168 | 44,196 | 88.19 % |
| Estados Unidos | Prophet |  |  | 43,686 | 46,870 | 91.73 % |
| Honduras | SARIMA | 359.01 | 375.74 | 21,841 | 24,115 | 90.17 % |
| Honduras | Holt-Winters |  |  | 18,900 | 21,200 | 74.17 % |
| Honduras | SES |  |  | 17,240 | 19,587 | 66.05 % |
| Honduras | Seasonal naive |  |  | 21,190 | 23,244 | 90.95 % |
| Honduras | Prophet |  |  | 21,239 | 23,497 | 86.70 % |

El MAPE marítimo excluye 11 meses del test con valor real igual a cero. En
las demás series no fue necesario excluir observaciones.

![Predicción sobre el conjunto de prueba, total](../figuras/pred_total.png)

![Predicción sobre el conjunto de prueba, vía aérea](../figuras/pred_via_aerea.png)

![Predicción sobre el conjunto de prueba, vía terrestre](../figuras/pred_via_terrestre.png)

![Predicción sobre el conjunto de prueba, vía marítima](../figuras/pred_via_maritima.png)

![Predicción sobre el conjunto de prueba, El Salvador](../figuras/pred_pais_el_salvador.png)

![Predicción sobre el conjunto de prueba, Estados Unidos](../figuras/pred_pais_estados_unidos.png)

![Predicción sobre el conjunto de prueba, Honduras](../figuras/pred_pais_honduras.png)

## Modelo seleccionado por serie

| Serie | Mejor modelo | MAE | RMSE | Evaluación |
|---|---|---:|---:|---|
| Total | SES | 175,088 | 194,791 | Error alto, subpredice la recuperación |
| Vía aérea | SES | 36,109 | 41,368 | Mejor resultado relativo, aún insuficiente |
| Vía terrestre | SES | 140,428 | 156,310 | Error alto por cambio de nivel |
| Vía marítima | Prophet | 784 | 1,645 | Menor error absoluto, MAPE todavía alto |
| El Salvador | SES | 94,064 | 104,531 | Baja precisión operativa |
| Estados Unidos | SES | 25,115 | 28,953 | Supera alternativas, pero MAPE cercano a 50 % |
| Honduras | SES | 17,240 | 19,587 | Mejor del grupo, con error relativo alto |

SES gana en seis series porque el final del entrenamiento está dominado por
la pandemia y un modelo de nivel evita extrapolaciones complejas. Esto no
significa que describa bien la recuperación. Los MAPE entre 35.62 % y
74.32 % de esos ganadores muestran que la capacidad predictiva sigue siendo
limitada. El SARIMA estable de vía aérea y de Estados Unidos ya no diverge,
pero sus MAE de 73,966 y 42,093 viajeros siguen por encima de SES.

Prophet es el mejor en marítima, pero su MAPE es 86.12 %. Los otros métodos
producen valores cercanos a cero debido al cierre observado al final del
train. Por eso no aparece la sobrepredicción masiva esperable de un modelo
que extrapolara el nivel prepandemia. El riesgo estructural permanece:
después de 26,030 viajeros en 2022, la serie cae a 6,617 en 2023, 6,605 en
2024 y 6,944 en 2025. Un ajuste que aprendiera el nivel histórico
sobrepredeciría ese régimen.

En conjunto, el corte explica los resultados. El entrenamiento termina en
marzo de 2021, con el choque pandémico incluido y la recuperación excluida.
La mayoría de los modelos subpredice la reapertura, mientras marítima exige
tratar por separado sus ceros y su ruptura de 2023. Las predicciones sirven
como evaluación honesta de ese diseño, no como pronósticos operativos
definitivos.
