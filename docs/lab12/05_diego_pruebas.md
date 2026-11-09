# Lab 12 — Pruebas comparativas de Diego

**Estado:** T1–T3 completadas en Dash y Power BI mediante control del agente y cronómetro manual. Fecha local: 8 de noviembre de 2026. Responsable del entregable: Diego.

## Modalidad y autorización

Diego comunicó en este chat que el catedrático autorizó que el agente operara las pruebas usando un cronómetro manual. Después de considerar realizarlas él mismo, pidió expresamente que el agente completara todo. Se registra la autorización como comunicación de Diego, sin afirmar una verificación independiente con el catedrático.

Esta modalidad sustituye la condición original de una persona operando las interfaces. **Operador real: Codex**, con conocimiento previo del informe adquirido durante su construcción y verificación. Diego declaró ninguna experiencia con Dash ni Power BI, pero no ejecutó estos recorridos. No se presentan estos tiempos como desempeño de un usuario principiante ni como una prueba humana.

El cronómetro visible se inició y detuvo mediante clics en sus botones. Su fuente se conserva en [cronometro_lab12.html](../scripts/cronometro_lab12.html), el registro íntegro en [05_diego_cronometro.json](05_diego_cronometro.json) y la captura en [lab12_diego_cronometro.png](../figuras/lab12_diego_cronometro.png). Para reproducirlo, servir la carpeta docs/scripts en localhost y abrir el HTML en un navegador; el historial se conserva en el almacenamiento local de ese navegador.

## Entorno

Mismo equipo Windows para ambas versiones: Windows 11 Home Single Language 10.0.26200, compilación 26200; AMD Ryzen 7 8845HS with Radeon 780M Graphics; RAM reportada 16.390.533.120 bytes. Power BI Desktop 2.159.1231.0 de 64 bits, ventana capturada de 1363 × 680 píxeles; informe normalmente al 70 %, vista de datos del gráfico al 100 %.

Dash Lab 10: commit b605afc de origin/lab10, worktree separado, Python 3.13.6, Dash 4.5.0, Plotly 6.5.2 y pandas 2.3.3, en http://127.0.0.1:8050. Entorno virtual con paquetes disponibles del equipo; cumple los mínimos de requirements.txt. Navegador efectivo: Chrome 156.0.0.0, controlado con Playwright, viewport 1040 × 650 píxeles CSS. No se utilizó Edge para estos recorridos.

Las dos versiones usan los mismos CSV, sin entrenamiento ni modificaciones en app/ o insumos/. Power BI conserva la v1.0 congelada con SHA-256 b4cfc73211f2130d8e262ad0a583d2c9566cb22894363f54c107d45ae0f76d54.

## Método y límites de los tiempos

Orden: T1 Power BI → Dash; T2 Dash → Power BI; T3 Power BI → Dash. T2 sigue el protocolo canónico de Esteban §3 (2025/T4), frente al resumen antiguo de 2020.

El reloj se inició antes de cambiar a la interfaz de prueba y se detuvo al regresar al cronómetro, tras leer el resultado y, cuando correspondió, guardar la captura o regresar al nivel anual. Por ello incluye cambios de ventana, llamadas de control, inspección de pantalla, lectura, capturas y pausas de razonamiento. No coincide exactamente con el intervalo humano «primer clic–lectura». No se descontaron estas demoras ni se ajustaron los valores registrados.

Se cuentan los clics realmente enviados a la aplicación, incluidos los clics derechos y cierres de listas. Se excluyen los botones del cronómetro y los cambios de pestaña o ventana. Desplazamientos, movimientos del cursor y atajos se describen aparte. Los tiempos de la tabla están redondeados a dos decimales; el JSON conserva los originales.

Se conservaron los filtros iniciales pertinentes: Vía de ingreso/2025 para T1; Total y rango completo para T2; Total, SARIMA/Holt-Winters/SES y 63 meses para T3. T2 Dash se repitió tras recargar y Power BI se reabrió en Inicio antes de T2. T3 partió de Datos observados en Power BI y de G1 en Dash después de T2; los controles de modelos seguían en su estado inicial. No se afirma una reapertura completa antes de cada una de las seis ejecuciones. El restablecimiento general mediante botones no fue parte de estos recorridos.

## Resultados de T1–T3 (5.3 y 5.4, modalidad adaptada)

| Prueba | Versión | Resultado leído | Clics | Tiempo (s) | Dificultades observadas |
|---|---|---|---:|---:|---|
| T1 | Power BI | Vía Terrestre, 2.401.323 viajeros; Aérea 1.188.971 y Marítima 6.944 | 6 | 74,25 | Pulsar el grupo ya seleccionado lo deseleccionó; se corrigió. La lista de años abrió al principio, aunque 2025 seguía seleccionado. |
| T1 | Dash | Cursor sobre Vía Terrestre: 2.401.323 viajeros | 5 | 35,25 | Segundo intento completo. El primero falló al intentar apuntar directamente a la barra SVG. |
| T2 | Dash | 2025: 3.597.238; T4: 997.817; oct. 277.299, nov. 328.431, dic. 392.087. Diciembre es el máximo; regreso anual confirmado. | 5 | 42,94 | Fue necesario desplazar la página y colocar el cursor en los puntos del gráfico. |
| T2 | Power BI | Mismos totales y meses; regreso a Año confirmado. 2026 aparece con 1.682.636. | 10 | 131,13 | Se usaron menús de detalle y «Show as a table» para leer cifras exactas; tres desplazamientos de la tabla anual. La captura se recuperó con Alt+Espacio y Escape. |
| T3 | Power BI | SES menor en las tres métricas: MAE 175.088,44; RMSE 194.790,81; MAPE 58,11 % | 9 | 105,55 | Página larga: un desplazamiento hasta V7. Las listas permanecen abiertas tras elegir una métrica y requirieron clic fuera. Se comprobó la selección inicial de tres modelos abriendo su lista. |
| T3 | Dash | SES menor: MAE 175.088,44; RMSE 194.790,81; MAPE 58,11 %; cinco modelos y 63 meses en G7 | 6 | 42,47 | G6 y G7 están en secciones diferentes; se utilizó el enlace entre ambas y el cursor para leer las barras. |

### Recorridos efectivamente realizados

- **T1 Power BI, seis clics:** pestaña inferior Datos observados; abrir grupo; pulsar Vía de ingreso ya seleccionada (quedó sin selección); volver a seleccionarla; abrir año; clic fuera para cerrar conservando 2025. Lectura de etiquetas en V2.
- **T1 Dash, cinco clics:** enlace G2; abrir grupo; elegir Vía de ingreso; abrir año; elegir 2025. Cursor sobre la barra mayor y lectura de su etiqueta emergente.
- **T2 Dash, cinco clics:** enlace G1; Anual; Trimestral; Mensual; Anual. Se leyeron 2025, T4 y los tres meses mediante etiquetas emergentes. Total y fechas completas ya estaban seleccionados.
- **T2 Power BI, diez clics:** pestaña Datos observados; clic derecho en el punto 2025; Drill down; clic derecho en T4; Drill down; clic derecho en el gráfico mensual; Show as a table; Drill up a trimestre; Drill up a año; Back to report. La tabla mostró los tres meses y después T4; al subir y desplazar la tabla anual se leyeron 2025 y 2026. Las cifras exactas anual y trimestral se leyeron al regresar, en orden inverso al protocolo previsto.
- **T3 Power BI, nueve clics:** pestaña Predicciones y modelos; abrir modelos de V6; clic fuera tras comprobar SARIMA/Holt-Winters/SES; abrir métrica; RMSE; clic fuera; abrir métrica; MAPE; clic fuera. MAE se leyó en el estado inicial. V7 conservó sus cinco modelos.
- **T3 Dash, seis clics:** enlace G6; enlace de G6 a G7; abrir métrica; RMSE; abrir métrica; MAPE. Total, tres modelos y fechas ya estaban en su estado inicial. Se leyeron las etiquetas de SES en las tres métricas.

### Evidencia real

| Prueba | Power BI | Dash |
|---|---|---|
| T1 | [Ranking 2025](../figuras/lab12_diego_t1_pbi.png) | [Barra y cursor](../figuras/lab12_diego_t1_dash.png) |
| T2 | [Detalle mensual](../figuras/lab12_diego_t2_pbi.png), [regreso anual](../figuras/lab12_diego_t2_pbi_anual.png) | [Detalle mensual](../figuras/lab12_diego_t2_dash.png) |
| T3 | [MAE](../figuras/lab12_diego_t3_pbi_mae.png), [RMSE](../figuras/lab12_diego_t3_pbi_rmse.png), [MAPE](../figuras/lab12_diego_t3_pbi.png) | [MAPE y cursor](../figuras/lab12_diego_t3_dash.png) |

No todas las cifras leídas durante el recorrido caben en una sola captura. El registro describe la secuencia; las consultas técnicas y la comparación de CSV permanecen en 01_diego_validacion_final.json.

### Intentos incompletos conservados

- T1 Dash, 178,12 s (02:39:49–02:42:47 UTC): no se completó la lectura del cursor. La capa de interacción de Plotly interceptó el intento de colocar el cursor directamente sobre el elemento SVG. Se repitió apuntando al gráfico con el mouse, sin cambiar la aplicación.
- T2 Dash, 192,39 s (02:44:58–02:48:11 UTC): interrupción de la sesión antes de completar trimestre, meses y regreso. Excluido de la tabla de ejecuciones completas.
- No se borraron estos registros. Las marcas UTC del JSON corresponden al 9-nov; en Guatemala (UTC−6) todas estas pruebas ocurrieron el 8-nov.

## Carga y respuesta a filtros

| Operación observada | Tiempo (s) | Definición y alcance |
|---|---:|---|
| Reapertura de Power BI | 36,35 | Desde Iniciar, antes de lanzar el PBIX con Desktop cerrado, hasta observar Inicio cargado y regresar a Detener. Incluye lanzamiento y control del agente. |
| Recarga de Dash | 15,75 | Desde Iniciar, antes de recargar la página con el servidor ya en marcha, hasta observar ocho gráficos, verificar G7 y regresar a Detener. No incluye iniciar Python ni el servidor. |
| Selector de métrica Dash | 16,16 | Abrir selector de G7 y cambiar MAE → MAPE; comprobar unidad y estado actualizado; volver a Detener. |
| Selector de métrica Power BI | 44,91 | Cambiar MAPE → MAE en V7; incluye recuperar la posición de la página mediante desplazamiento tras un cambio de estado detectado, tres clics de selector/cierre e inspección. |

**Estos intervalos no aíslan la latencia de renderizado** y los eventos de carga y filtro no son idénticos en ambas aplicaciones. Sirven como registro de lo observado; no sustentan una clasificación de rendimiento. Se midió una sola ejecución por operación, con cachés y aplicaciones previamente utilizadas.

## Consistencia de indicadores (5.5)

| Indicador | Filtros y agregación | Dash leído | Power BI leído |
|---|---|---:|---:|
| Viajeros totales 2025 | Total, doce meses; T2 | 3.597.238 | 3.597.238 |
| MAE SES Total | 63 meses abril 2021–junio 2026; T3 | 175.088,44 | 175.088,44 |

La consulta técnica de Power BI devuelve 3.597.237,9999999995 y 175.088,43650293106; coinciden con lo presentado al redondear. La auditoría de las 105 métricas de las 35 combinaciones pasó con tolerancia relativa 1e-9. G7 recalcula sobre las fechas comunes y V7 importa el CSV: ambos usan los mismos 63 meses.

T2 confirma una diferencia de presentación relevante: Dash omite 2026 del nivel anual y explica que tiene seis de doce meses. V1 incluye 1.682.636; **es un total parcial, no una caída anual comparable con 2025**. V4 es la visualización de Power BI que restringe la comparación a años completos.

En la tabla complementaria de métricas de Power BI se observó una fila Total que agrega métricas entre modelos. No se usa para decidir el mejor modelo: las métricas se comparan por fila/modelo y dentro de la misma unidad; sumar MAPE entre modelos no es un indicador interpretable. Esta limitación queda señalada para la revisión de Esteban, sin modificar la versión congelada.

## Recuperación de Power BI y cierre

La ventana se observó en blanco. Se cerró normalmente, se eligió Don't save y se reabrió el PBIX: Inicio volvió a dibujarse y T2/T3 se completaron. Durante el cambio entre navegador y Desktop una captura volvió a aparecer blanca; Alt+Espacio y Escape permitieron recuperar su dibujo. No se identificó una causa raíz ni se cambiaron ajustes de seguridad o del sistema.

Después de las pruebas se cerró Desktop descartando los cambios de filtros. Se verificó nuevamente el SHA-256 del archivo congelado. Se conservaron Inicio como página inicial y Control oculta en el archivo; no se guardó el estado de las pruebas.

23 pruebas automatizadas del informe y 33 de modelos de Lab 10 habían aprobado durante la congelación. Las 23 del informe se reejecutaron al cerrar esta entrega y volvieron a pasar. Se detuvieron los servidores locales de Dash y del cronómetro y se retiró el worktree temporal de Lab 10. Los tiempos de desarrollo humano previos no se recuerdan y quedan **no registrados**; no se convierten los tiempos de esta ejecución asistida en minutos de desarrollo humano. El mensaje de traspaso a Esteban se prepara, sin enviarlo automáticamente.

## Interpretación para la comparación final

Las cifras y recorridos funcionales coinciden, con la salvedad de 2026 y los detalles de interacción descritos. Se completa el registro 5.3/5.4 en la modalidad adaptada comunicada por Diego y la verificación 5.5. Queda explícito que no se ejecutó el protocolo original con una persona y que no hay evidencia para atribuir las diferencias de tiempo a facilidad de aprendizaje o rendimiento intrínseco.
