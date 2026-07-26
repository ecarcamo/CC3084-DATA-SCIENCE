# 5. Modelos y predicción

## Selección de órdenes

La identificación parte de las ACF y PACF sobre `log1p`. En las series con
persistencia, p y q se exploraron entre 0 y 2. Los picos en el rezago 12
motivaron P y Q entre 0 y 1, con periodo estacional 12. Las conclusiones del
ADF fijaron d=1 y D=1 en seis series. Para marítima se probó d=2 y D=1, sin
interpretar esta decisión como evidencia de estacionariedad.

| Serie | Modelo seleccionado por AIC | Fundamento de p y q |
|---|---|---|
| Total | SARIMA(1,1,2)(1,1,1)12 | PACF corta y ACF persistente con señal anual |
| Vía aérea | SARIMA(2,1,2)(1,1,0)12 | Dependencia corta regular y pico estacional |
| Vía terrestre | SARIMA(0,1,1)(1,1,0)12 | Corte dominante de ACF y componente anual |
| Vía marítima | SARIMA(1,2,2)(1,1,1)12 | ACF irregular, diferencias adicionales y ciclo anual |
| El Salvador | SARIMA(2,1,2)(1,1,1)12 | Dependencia regular mixta y estacionalidad marcada |
| Estados Unidos | SARIMA(1,1,2)(1,1,1)12 | ACF persistente y PACF concentrada en pocos rezagos |
| Honduras | SARIMA(1,1,2)(0,1,1)12 | Dependencia corta con efecto estacional de media móvil |

La rejilla manual evaluó todas las combinaciones de esos rangos y conservó
los tres menores AIC convergentes por serie. `auto_arima` se ejecutó con la
misma diferenciación y límites. Sus propuestas fueron de orden bajo y
coherentes con las ACF y PACF, aunque no siempre coincidieron con el mínimo
manual porque su búsqueda es escalonada.

## Comparación ARIMA

| Serie | order | seasonal order | AIC | BIC | Ljung-Box p |
|---|---|---|---:|---:|---:|
| Total | (1,1,2) | (1,1,1,12) | 68.55 | 85.22 | 0.0046 |
| Total | (2,1,2) | (0,1,1,12) | 69.19 | 85.87 | <0.0001 |
| Total | (1,1,2) | (0,1,1,12) | 69.45 | 83.34 | <0.0001 |
| Vía aérea | (2,1,2) | (1,1,0,12) | 165.06 | 181.78 | 0.1611 |
| Vía aérea | (2,1,2) | (1,1,1,12) | 165.21 | 184.66 | 0.2248 |
| Vía aérea | (0,1,1) | (1,1,0,12) | 166.81 | 175.22 | 1.0000 |
| Vía terrestre | (0,1,1) | (1,1,0,12) | 124.18 | 132.59 | 0.5395 |
| Vía terrestre | (1,1,0) | (1,1,0,12) | 124.32 | 132.70 | 0.8681 |
| Vía terrestre | (2,1,2) | (0,1,1,12) | 124.94 | 141.62 | <0.0001 |
| Vía marítima | (1,2,2) | (1,1,1,12) | 498.40 | 515.02 | 0.0199 |
| Vía marítima | (2,2,2) | (1,1,1,12) | 500.35 | 519.74 | 0.0202 |
| Vía marítima | (1,2,2) | (0,1,1,12) | 504.06 | 517.91 | 0.0052 |
| El Salvador | (2,1,2) | (1,1,1,12) | 400.62 | 420.07 | 0.1020 |
| El Salvador | (2,1,2) | (0,1,1,12) | 411.54 | 428.21 | 0.0481 |
| El Salvador | (1,1,2) | (0,1,1,12) | 411.80 | 425.70 | 0.0770 |
| Estados Unidos | (1,1,2) | (1,1,1,12) | 365.52 | 382.19 | 0.8244 |
| Estados Unidos | (2,1,1) | (1,1,0,12) | 368.34 | 382.28 | 0.7537 |
| Estados Unidos | (1,1,2) | (1,1,0,12) | 368.96 | 382.94 | 0.6696 |
| Honduras | (1,1,2) | (0,1,1,12) | 360.21 | 374.10 | 0.0107 |
| Honduras | (2,1,1) | (1,1,1,12) | 363.13 | 379.86 | 0.1444 |
| Honduras | (2,1,1) | (0,1,1,12) | 365.02 | 378.96 | 0.0050 |

El menor AIC decide la especificación llevada al test, pero los residuos
matizan la elección. Vía aérea, terrestre, El Salvador y Estados Unidos no
rechazan ausencia de autocorrelación al 5 %. Total, marítima y Honduras sí
retienen dependencia residual. Jarque-Bera rechaza normalidad en todos los
modelos seleccionados. Esto limita la inferencia paramétrica, aunque para
pronóstico es más preocupante la autocorrelación restante.

Un AIC bajo tampoco garantiza estabilidad a 63 pasos. Los SARIMA de vía
aérea y Estados Unidos producen trayectorias explosivas fuera de muestra.
Este resultado es consistente con haber desactivado las restricciones de
estacionariedad e invertibilidad para poder ajustar la rejilla. Por ello, la
selección operativa final se hace con MAE y RMSE del test, no con AIC.

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
| Total | SARIMA | 68.55 | 85.22 | 250,565 | 274,180 | 83.32 % |
| Total | Holt-Winters |  |  | 196,956 | 216,457 | 65.30 % |
| Total | SES |  |  | 175,088 | 194,791 | 58.11 % |
| Total | Seasonal naive |  |  | 235,731 | 253,203 | 83.86 % |
| Total | Prophet |  |  | 264,527 | 282,313 | 92.50 % |
| Vía aérea | SARIMA | 165.06 | 181.78 | 5.70e20 | 4.44e21 | 6.10e17 % |
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
| Estados Unidos | SARIMA | 365.52 | 382.19 | 3.67e24 | 2.39e25 | 5.18e21 % |
| Estados Unidos | Holt-Winters |  |  | 34,195 | 37,642 | 69.37 % |
| Estados Unidos | SES |  |  | 25,115 | 28,953 | 49.93 % |
| Estados Unidos | Seasonal naive |  |  | 41,168 | 44,196 | 88.19 % |
| Estados Unidos | Prophet |  |  | 43,686 | 46,870 | 91.73 % |
| Honduras | SARIMA | 360.21 | 374.10 | 19,917 | 22,337 | 86.16 % |
| Honduras | Holt-Winters |  |  | 18,900 | 21,200 | 74.17 % |
| Honduras | SES |  |  | 17,240 | 19,587 | 66.05 % |
| Honduras | Seasonal naive |  |  | 21,190 | 23,244 | 90.95 % |
| Honduras | Prophet |  |  | 21,239 | 23,497 | 86.70 % |

El MAPE marítimo excluye 11 meses del test con valor real igual a cero. En
las demás series no fue necesario excluir observaciones.

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
limitada.

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
