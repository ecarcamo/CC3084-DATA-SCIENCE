# Lab 12 — Pruebas comparativas de Diego

**Estado:** protocolo preparado y comprobaciones técnicas ejecutadas; tiempos, clics, dificultades y capturas de ejecución humana pendientes. No se declara completado 5.3/5.4.

## Entorno común

Windows 11 Home Single Language, versión 10.0.26200, compilación 26200. CPU AMD Ryzen 7 8845HS with Radeon 780M Graphics; RAM instalada reportada 16.390.533.120 bytes. Power BI Desktop 2.159.1231.0 de 64 bits. Dash Lab 10 en el mismo Windows, rama origin/lab10, commit b605afc, entorno virtual aislado con paquetes disponibles del equipo: Python 3.13.6, Dash 4.5.0, Plotly 6.5.2, pandas 2.3.3. Cumplen los mínimos de requirements.txt de Lab 10. URL: http://127.0.0.1:8050.

Operador: Diego. Experiencia previa declarada en este chat el 8-nov: **ninguna con Dash y ninguna con Power BI**. Microsoft Edge instalado: 156.0.4314.58; navegador efectivamente utilizado y tamaño de ventana de la prueba humana: pendientes de confirmar. La automatización de verificación no es el operador de las pruebas cronometradas.

## Protocolo humano (5.3 y 5.4)

Usar un cronómetro. Iniciar al primer clic de la tarea y detener al leer el resultado, contando los clics del recorrido y el regreso cuando se indique. Antes de cada tarea, volver al estado inicial. En Power BI los botones requieren Ctrl + clic en Desktop. No sumar tiempos de instalación ni esperas del agente al tiempo de ejecución humano. Registrar aparte carga inicial y respuesta de un filtro.

Orden alterno: T1 Power BI → Dash; T2 Dash → Power BI; T3 Power BI → Dash. Las instrucciones resumidas hablan de 2020 para T2, pero el protocolo canónico de Esteban §3 define 2025/T4; se utiliza este último para que las dos versiones respondan la misma pregunta.

### T1 — Vías de ingreso en 2025

Dash: ir a G2, elegir Vía de ingreso y 2025, leer la barra mayor. Power BI: página Datos observados, elegir grupo Vía de ingreso y año 2025, leer V2. Resultado esperado: Terrestre 2.401.323; Aérea 1.188.971; Marítima 6.944. Sin Total ni países en el ranking. Capturar el resultado de cada versión.

### T2 — Del año al trimestre, al mes y regreso

Dash: G1, Total, anual; leer 2025, cambiar a trimestral y leer T4 2025, cambiar a mensual y leer octubre–diciembre, volver a anual. Power BI: V1, Total, Año; bajar desde 2025 a Trimestre, desde T4 a Mes, leer los tres meses y subir dos niveles. Resultado esperado: año 3.597.238; T4 997.817; octubre 277.299, noviembre 328.431, diciembre 392.087, máximo del trimestre. Contar el recorrido completo y tomar una captura por versión. Registrar si el año parcial 2026 se muestra de manera distinta.

### T3 — Predicciones y desempeño

Dash: G6, Total, SARIMA/Holt-Winters/SES, abril 2021–junio 2026; revisar observado frente a estimados. G7: Total, MAE, luego RMSE y MAPE. Power BI: Predicciones y modelos con los mismos modelos en V6; V7, MAE, luego RMSE y MAPE. Resultado esperado: SES tiene el menor error; MAE 175.088,44 viajeros, RMSE 194.790,81 viajeros y MAPE 58,11 %. La selección de tres modelos en V6 no reduce los cinco modelos comparados en V7. Capturar cada versión.

## Registro de ejecución humana

| Prueba | Versión | Resultado obtenido | Pasos y clics | Tiempo (s) | Dificultades | Evidencia |
|---|---|---|---|---|---|---|
| T1 | Power BI | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| T1 | Dash | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| T2 | Dash | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| T2 | Power BI | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| T3 | Power BI | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| T3 | Dash | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |

Carga inicial y respuesta de un filtro, por versión: pendientes de medición humana. El tiempo de consulta del MCP o de Playwright no sustituye estas mediciones.

## Consistencia de indicadores (5.5)

| Indicador | Filtros y agregación | Valor de control |
|---|---|---:|
| Viajeros totales 2025 | Total, suma de doce meses | 3.597.238 |
| MAE SES Total | 63 meses abril 2021–junio 2026, sin filtro temporal | 175.088,44 |

La consulta real de Power BI devuelve 3.597.237,9999999995 y 175.088,43650293106. Los valores de los CSV y el cálculo de Lab 10 coinciden al redondear; la representación decimal explica el residuo del primer indicador. La comparación de las 105 métricas contra los CSV pasó con rtol=1e-9. La evidencia técnica no reemplaza la lectura y captura de ambas interfaces durante las pruebas humanas.

## Limitaciones

No se atribuirán diferencias de tiempos a la herramienta sin considerar aprendizaje, orden y entorno. Las pruebas parten del estado inicial de cada versión. Las capturas automáticas de verificación se identifican como tales y no se presentarán como evidencia de un recorrido humano cronometrado.


## Estado técnico al congelar v1.0

23 pruebas automatizadas del informe y 33 de modelos de Lab 10 aprobadas. V1–V8 revisadas en Desktop; V7 muestra MAE y MAPE con unidades y orden correctos; el detalle desde V7 recibe Total. Esta evidencia es técnica y automatizada, no una ejecución humana cronometrada. El servidor de Dash está preparado en localhost:8050 para que el operador complete el registro.
