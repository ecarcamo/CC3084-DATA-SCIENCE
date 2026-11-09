<style>
@page { size: letter; margin: 2cm 2cm; }
html, body { color: #000; }
body { font-family: Arial, "Liberation Sans", Helvetica, sans-serif; font-size: 11pt; font-weight: normal; line-height: 1.4; margin: 0; }
h1 { font-size: 16pt; font-weight: bold; text-align: center; margin: 0 0 .6em; color: #000; }
h2 { font-size: 16pt; font-weight: bold; text-align: center; margin: 1.3em 0 .6em; color: #000; page-break-after: avoid; }
h3 { font-size: 14pt; font-weight: bold; text-align: left; margin: 1em 0 .4em; color: #000; page-break-after: avoid; }
p, ul, ol { margin: .4em 0 .6em; }
li { margin: .2em 0; }
strong, b, th { font-weight: normal; }
a { color: #000; text-decoration: underline; }
table { border-collapse: collapse; width: 100%; margin: .5em 0 .8em; font-size: 11pt; page-break-inside: auto; }
tr { page-break-inside: avoid; }
th, td { border: 1px solid #000; padding: 3px 5px; vertical-align: top; text-align: left; }
th { background: #fff; }
code { font-family: Arial, "Liberation Sans", sans-serif; font-size: 11pt; }
pre { font-family: "Liberation Mono", monospace; font-size: 10pt; border: 1px solid #000; padding: 5px 7px; white-space: pre-wrap; }
.par { display: table; width: 100%; table-layout: fixed; margin: .5em 0; page-break-inside: avoid; }
.par > div { display: table-cell; width: 50%; padding: 0 4px; vertical-align: top; text-align: center; }
.par img, .fig img { max-width: 100%; max-height: 6.2cm; }
.fig { text-align: center; margin: .5em 0; page-break-inside: avoid; }
.pie { font-size: 11pt; margin-top: .2em; }
</style>

# Lab 12 · Visualización interactiva del observatorio de turismo en Power BI

Curso: CC3066 Data Science, Universidad del Valle de Guatemala, semestre II 2026.

Repositorio: <https://github.com/ecarcamo/CC3084-DATA-SCIENCE/tree/lab12> (rama `lab12`).

Informe: `powerbi/observatorio_turismo.pbix`, versión v1.0 (SHA-256 `b4cfc732…f76d54`), Power BI Desktop 2.159.1231.0 de 64 bits.

Documentación detallada: <https://github.com/ecarcamo/CC3084-DATA-SCIENCE/tree/lab12/docs/lab12>. Cada sección resume un documento de esa carpeta.

## 1. Preguntas de gestión, público y alcance (4.1)

El público son directivos y tomadores de decisiones del sector turístico sin formación en estadística. Se conservan las ocho preguntas del Laboratorio 10 y se compara siempre contra la rama `lab10`, porque `lab11` cambió G6 y G7 y retiró G8.

| Lab 10 | Power BI | Pregunta de gestión | Página |
|---|---|---|---|
| G1 | V1 | ¿Cómo ha evolucionado el ingreso de viajeros? | Datos observados |
| G2 | V2 | ¿Qué vías o países concentran más viajeros? | Datos observados |
| G3 | V3 | ¿En qué meses se concentra el ingreso de viajeros? | Estacionalidad y años |
| G4 | V4 | ¿Cómo cambia el total de viajeros entre años completos? | Estacionalidad y años |
| G5 | V5 | ¿Cuánto cambió cada mes frente al mismo mes del año anterior? | Datos observados |
| G6 | V6 | ¿Qué estimaron los modelos frente a lo que se registró? | Predicciones y modelos |
| G7 | V7 | ¿Qué modelo se equivoca menos para esta serie? | Predicciones y modelos |
| G8 | V8 | ¿En qué meses se alejó el modelo de lo observado? | Predicciones y modelos |

Alcance: siete series mensuales de viajeros (Total, tres vías de ingreso y tres países de residencia) de enero de 2009 a junio de 2026, y las predicciones ya existentes de cinco modelos (SARIMA, Holt-Winters, SES, Seasonal Naive y Prophet) de abril de 2021 a junio de 2026, con sus métricas MAE, RMSE y MAPE. No se entrenaron modelos nuevos.

Decisiones que apoya: identificar las vías y mercados que concentran más viajeros, localizar temporadas altas y bajas, revisar si un año o un mes creció frente al anterior y saber qué estimación histórica se acercó más a lo registrado.

Fuera de alcance: explicar las causas de los cambios, pronosticar meses futuros (las estimaciones son de meses ya registrados y no tienen intervalos de confianza), sumar países con vías o con el Total y comparar años incompletos como 2026 con años completos.

## 2. Paleta, fuentes, boceto y navegación (4.2)

| Uso | Color | Justificación |
|---|---|---|
| Observado | Azul `#1F4E79` | Color frío y estable para datos registrados; mismo significado que en el Lab 10. |
| Estimado | Naranja `#A65E16` | Complementario del azul: separa estimación de observación. Cada modelo tiene un tono y un trazo propios. |
| Selección y página activa | Verde `#20745A` | Solo indica selección; nunca representa una serie. |
| Alerta y sin datos | Rojo `#B3261E` | Siempre acompañado de un mensaje escrito. |
| Fondo y tarjetas | `#F4F6F8` y `#FFFFFF` | Separan lienzo y contenido sin competir con los datos. |
| Estacionalidad | `#E7EFF6` a `#1F4E79` | Escala secuencial de un solo tono, equivalente al mapa de calor G3. |

Fuente Arial en todo el informe (títulos de gráficas de 14 pt, etiquetas de 10 pt, mensajes sin datos de 12 pt). Los colores de texto cumplen un contraste de al menos 4,5:1 y el significado nunca depende solo del color: los modelos llevan nombre y trazo, la página activa lleva etiqueta y la ausencia de datos se explica por escrito.

<div class="fig"><img src="../figuras/lab12_hugo_boceto.png" style="max-height:9cm"><div class="pie">Figura 1. Boceto de las cinco páginas.</div></div>

Navegación: cinco páginas (Inicio, Datos observados, Estacionalidad y años, Predicciones y modelos, Detalle de serie) con la misma barra de botones, la página activa en verde y un botón «Restablecer vista» que aplica el marcador «Inicial» de cada página. La página técnica Control queda oculta.

Qué se conservó del Lab 10: las ocho preguntas, las siete series, los cinco modelos, la fuente, el significado de los colores, el enlace ranking → serie temporal y la exclusión de años incompletos. Qué cambió: la página única con casillas «Gráficas visibles» pasó a páginas temáticas con botones y marcadores; el selector de granularidad pasó a la exploración nativa Año > Trimestre > Mes; el mapa de calor pasó a una matriz con formato condicional; y las marcas × de meses sin dato pasaron a celdas vacías con una nota. Detalle en `docs/lab12/02_hugo_diseno.md`.

## 3. Las ocho visualizaciones (4.3)

| V | Lab 10 | Tipo en Dash | Tipo en Power BI | Sustitución y motivo |
|---|---|---|---|---|
| V1 | G1 | Líneas con selector de granularidad | Líneas, jerarquía Año > Trimestre > Mes | Selector de granularidad sustituido por drill down y drill up nativos |
| V2 | G2 | Barras horizontales | Barras horizontales, filtra a V1 y V5 | Desplegables pasan a segmentadores; se conserva el clic ranking → serie |
| V3 | G3 | Mapa de calor año × mes | Matriz con formato condicional | Power BI no tiene mapa de calor nativo; la matriz conserva la escala y añade el valor |
| V4 | G4 | Columnas por año completo | Columnas por año completo | Ninguna; la nota de años excluidos pasa a una medida de texto |
| V5 | G5 | Barras de variación % con línea 0 % | Columnas por mes con línea 0 % | Los meses sin base no se dibujan y se cuentan en la nota |
| V6 | G6 | Líneas observado y modelos | Líneas, una medida por modelo | Casillas de modelos pasan a un segmentador de selección múltiple |
| V7 | G7 | Barras de error ordenadas | Barras horizontales con selector MAE, RMSE o MAPE | Métricas importadas del CSV en lugar de recalcularlas |
| V8 | G8 | Línea con marcadores y línea 0 | Línea con marcadores y línea 0 | Desplegable de modelo pasa a segmentador de selección única |

Tarjetas, segmentadores, botones, textos y la tabla de métricas son complementarios y no se cuentan entre las ocho. Capturas de ambas versiones (Lab 10 a la izquierda, Power BI a la derecha):

<div class="par"><div><img src="../figuras/lab12_ernesto_lab10_g1.png"><div class="pie">G1 (Dash)</div></div><div><img src="../figuras/lab12_hugo_v1_v2_seleccion.png"><div class="pie">V1 y V2: Vía Aérea seleccionada en V2 filtra V1</div></div></div>

<div class="par"><div><img src="../figuras/lab12_ernesto_lab10_g2.png"><div class="pie">G2 (Dash)</div></div><div><img src="../figuras/lab12_hugo_datos_observados.png"><div class="pie">V1 y V2, estado inicial</div></div></div>

<div class="par"><div><img src="../figuras/lab12_ernesto_lab10_g3.png"><div class="pie">G3 (Dash)</div></div><div><img src="../figuras/lab12_hugo_estacionalidad.png"><div class="pie">V3, matriz año × mes</div></div></div>

<div class="par"><div><img src="../figuras/lab12_ernesto_lab10_g4.png"><div class="pie">G4 (Dash)</div></div><div><img src="../figuras/lab12_hugo_anios_completos.png"><div class="pie">V4, 17 años completos; 2026 excluido</div></div></div>

<div class="par"><div><img src="../figuras/lab12_ernesto_lab10_g5.png"><div class="pie">G5 (Dash)</div></div><div><img src="../figuras/lab12_hugo_variacion.png"><div class="pie">V5, variación interanual con línea 0 %</div></div></div>

<div class="par"><div><img src="../figuras/lab12_ernesto_lab10_g6.png"><div class="pie">G6 (Dash)</div></div><div><img src="../figuras/lab12_diego_t3_pbi_mae.png"><div class="pie">Predicciones y modelos: leyenda y nota de V6, V7 con MAE y V8</div></div></div>

<div class="par"><div><img src="../figuras/lab12_ernesto_lab10_g7.png"><div class="pie">G7 (Dash)</div></div><div><img src="../figuras/lab12_diego_mape.png"><div class="pie">V7 con MAPE y V8 con SARIMA</div></div></div>

<div class="par"><div><img src="../figuras/lab12_ernesto_lab10_g8.png"><div class="pie">G8 (Dash)</div></div><div><img src="../figuras/lab12_hugo_drill.png"><div class="pie">Drill down en V1: total 2020 y trimestre T2</div></div></div>

<div class="par"><div><img src="../figuras/lab12_hugo_detalle.png"><div class="pie">Drillthrough a Detalle de serie (Vía Aérea)</div></div><div><img src="../figuras/lab12_hugo_sin_datos.png"><div class="pie">Mensaje cuando una selección no tiene datos</div></div></div>

## 4. Importación, relaciones y DAX (4.4)

Power Query lee las carpetas de `insumos/` a partir del parámetro `RutaInsumos`, con codificación UTF-8 y configuración regional `en-US` para el punto decimal. Pasos: listar los CSV de la carpeta, extraer la clave de serie (y de modelo) del nombre del archivo, promover encabezados, expandir y tipar las columnas. No se redondea, imputa ni agrega nada al importar.

| Tabla | Fuente | Grano | Filas |
|---|---|---|---:|
| Observaciones | `insumos/series/serie_<clave>.csv` | Serie y mes | 1.470 |
| Predicciones | `insumos/resultados/predicciones/<serie>_<modelo>.csv` | Serie, modelo y mes | 2.205 |
| Metricas | `insumos/resultados/metricas_modelos.csv` | Serie y modelo (63 meses) | 35 |

`DimSerie` y `DimModelo` son tablas constantes con clave, nombre y orden; `Calendario` es diario de 2009 a 2026 con Año, Trimestre, MesNum y Mes. Medidas base en la tabla `Medidas`, cada una con una finalidad:

| Medida | Finalidad |
|---|---|
| `Viajeros = SUM(Observaciones[viajeros])` | Suma lo observado en el contexto filtrado. |
| `Viajeros serie` | Usa la serie seleccionada; con ninguna o varias devuelve Total, nunca la suma de grupos distintos. |
| `Estimado` | Devuelve la predicción solo con una serie y un modelo; vacío si la selección es ambigua. |
| `Diferencia` | Observado menos estimado, solo en fechas con ambos valores; una ausencia no se convierte en cero. |

Las medidas de V3 a V8 (meses con dato, total de año completo, variación interanual, error por métrica y mensajes sin datos) están en `powerbi/medidas_hugo.json` y `powerbi/medidas_diego.json`. Detalle y código M en `docs/lab12/01_diego_datos.md`.

## 5. Predicciones y métricas sin duplicar registros (4.5)

Modelo estrella: `DimSerie`, `DimModelo` y `Calendario` filtran en una sola dirección a los tres hechos, y no hay relaciones entre hechos. Así lo observado no se repite por cada modelo, como ocurriría al unir observado y predicciones en una tabla plana. `Metricas` no se relaciona con `Calendario` porque sus valores resumen los 63 meses completos. Controles en Power BI: cero claves duplicadas en los tres hechos, ninguna clave sin correspondencia, Total 2025 = 3.597.238, MAE de SES en Total = 175.088,44 y diferencia de SES en abril de 2021 = −23.077,18. Las 105 métricas coinciden con el CSV con tolerancia relativa de 1e-9.

<div class="fig"><img src="../figuras/lab12_diego_modelo.png" style="max-height:7cm"><div class="pie">Figura 2. Vista de modelo con las siete relaciones.</div></div>

Limitación: en la tabla complementaria de la página de modelos, la fila Total suma métricas entre modelos y no es un indicador interpretable. La comparación se hace con V7 o fila por fila.

## 6. Planificación y tiempo (4.6)

| Tarea | Responsable | Terminada | Commits |
|---|---|---|---|
| Importación, relaciones y medidas base | Diego | 5-nov 15:28 | `f43b181`, `c147d9e` |
| Tema, paleta, boceto y V1–V2 enlazadas | Hugo | 5-nov 16:11 | `e668fd8`, `f4eb7b0`, `b47e73d` |
| Preguntas, planificación y protocolo | Esteban | 5-nov 16:18 | `8036fb6` |
| Avance consolidado y entregado | Ernesto | 5-nov 17:12 | `104e1e0` … `9535812` |
| Valores de referencia, tabla 4.3 y especificación V3–V8 | Ernesto | 7-nov 22:05 | `37599d5`, `756a9c2` |
| Capturas del Lab 10 y costos 5.2 | Ernesto | 7-nov 22:09 | `0f37067`, `3c822b4` |
| V3–V5, navegación, marcadores y drillthrough (v0.3) | Hugo | 8-nov 19:34 | `d022104`, `645d311` |
| V6–V8 y `.pbix` v1.0 congelado | Diego | 8-nov 20:19 | `a3d5706`, `44eab4e`, `997a493` |
| Pruebas T1–T3 y verificación 5.5 | Diego | 8-nov 21:08 | `22e7a58`, `5c6090e` |
| Matriz, recomendaciones, README y documento final | Esteban | 8-nov | `4a09b9e`, `44908ae`, `8134f49` |

Las pruebas pasaron de Esteban a Diego y la especificación de V3–V8 de Esteban a Ernesto, porque solo Hugo y Diego tienen Windows para abrir Power BI Desktop.

| Integrante | Dash (Lab 10) | Power BI (Lab 12) | Origen |
|---|---:|---:|---|
| Hugo | 60 min | 30 min | Power BI real; Dash estimado por recuerdo |
| Ernesto | No registrado | 15 min (sin Power BI) | Real |
| Diego | No registrado | No registrado | Declaró no recordar sus tiempos |
| Esteban | ≈ 90 min | 0 min (≈ 120 min de documentación) | Estimado por sus commits |

El registro está incompleto y no permite concluir qué herramienta fue más rápida. En calendario, ambas versiones tomaron unos cuatro días: el Lab 10 del 22 al 25 de octubre con los cuatro integrantes editando código, y el Lab 12 del 5 al 8 de noviembre con el `.pbix` editado por dos personas.

## 7. Matriz de comparación (5.1)

| Criterio | Evidencia en Dash (Lab 10) | Evidencia en Power BI (Lab 12) | Implicación para la tarea |
|---|---|---|---|
| Facilidad de aprendizaje | Python y Plotly, ya conocidos. Los cuatro integrantes escribieron código (20 commits en `lab10`). | Gráficos básicos sin código, pero el DAX dio cuatro errores reales: nombre de medida igual a una columna, `CONCATENATEX` sin orden, formato dinámico y estático a la vez, y dos campos `nombre` en una consulta. | Para un equipo que ya programa, Dash tuvo menos barrera; el contexto de filtro de DAX exige aprendizaje propio. |
| Tiempo de desarrollo | 22 al 25 de octubre, 20 commits, 1.545 líneas en `app/`. | 5 al 8 de noviembre, 17 commits; la v0.3 se atrasó unas 20 horas. | Minutos incompletos (sección 6): no hay base para declarar un ganador. |
| Preparación y actualización de datos | `app/data.py` lee y valida los CSV; ruta relativa; se actualiza reemplazando los CSV y reiniciando. | Power Query con `RutaInsumos` y `en-US`. El refresco desde otra carpeta conservó 1.470 / 2.205 / 35 filas. La ruta es absoluta. | Power BI actualiza con un botón, pero cada equipo debe editar la ruta (explicado en el README). |
| Integración de resultados de modelos | `app/model_results.py` alinea predicciones y recalcula las métricas sobre fechas comunes. | Modelo estrella sin relaciones entre hechos; métricas importadas, idénticas al CSV (1e-9). La fila Total de la tabla suma métricas. | Mismas cifras en ambas (5.5); V7 no responde a fechas y la fila Total debe ignorarse. |
| Interacción y navegación | Una página con casillas de visibilidad, enlace G2 → G1 y selector de granularidad. Clics T1, T2, T3: 5, 5, 6. | Cinco páginas, botones, marcadores, drill Año > Trimestre > Mes, drillthrough con Atrás y V2 → V1. Clics: 6, 10, 9. | Power BI ordena por pregunta y ofrece drill nativo, pero pidió más clics en T2 y T3. |
| Personalización | Mapa de calor con × en meses sin dato y cualquier comportamiento por callback. | Sin mapa de calor nativo (V3 es una matriz); × pasan a celdas vacías; se escribieron generadores PBIR para un diseño reproducible. | Dash reproduce exactamente el diseño; Power BI requiere sustituciones documentadas. |
| Rendimiento | Recarga 15,75 s; cambio de métrica en G7 16,16 s. | Reapertura 36,35 s; cambio de métrica en V7 44,91 s; una ventana en blanco obligó a reabrir. | Una sola ejecución con el control del agente incluido: es registro, no clasificación. |
| Colaboración y control de versiones | Código en texto, diferencias por línea, cuatro autores en paralelo. | `.pbix` binario de 240 KB que no se puede combinar: un dueño a la vez, traspasos, medidas en JSON y SHA-256. | Dash se integra mejor con Git; Power BI exige coordinación para no sobrescribir trabajo. |
| Requisitos para compartir o desplegar | Python en cualquier sistema; `Dockerfile` en el repositorio; el lector solo necesita navegador. Licencia MIT. | Desktop solo para Windows (2 de 4 integrantes pudieron editar). Compartir en la nube exige Pro (USD 14 por usuario al mes) o capacidad F64. | Desarrollar es gratis en ambas; distribuir no (servidor en Dash, licencias en Power BI). |

## 8. Costos y acceso (5.2)

Fuentes oficiales consultadas el 7 de noviembre de 2026; precios de referencia en USD.

| Aspecto | Power BI | Dash |
|---|---|---|
| Sistema operativo | Desktop solo en Windows 10 / Server 2016 o posterior, x64 | Windows, macOS o Linux con Python |
| Licencia para desarrollar | Desktop gratuito | Código abierto, licencia MIT |
| Compartir sin publicar | Enviar el `.pbix`; quien lo recibe necesita Desktop y Windows | Enviar el repositorio; quien lo recibe necesita Python y `requirements.txt` |
| Publicar en la organización | Gratuita: solo contenido propio. Pro: USD 14 por usuario al mes. Premium por usuario: USD 24 | Servidor propio, o Plotly Cloud: Free (3 lectores privados), Pro USD 29 al mes, Enterprise a convenir |
| Lectores sin licencia | Solo con capacidad Fabric F64 o Premium P1, de precio variable; publicar sigue exigiendo Pro | Cualquiera con navegador y la URL; la autenticación la pone el alojamiento o el código |
| Público en internet | «Publicar en la web»: cualquiera ve el informe y sus datos sin autenticación; requiere licencia y permiso del administrador | Desplegar el contenedor en un servidor público; el costo y el mantenimiento son del equipo |
| Mantenimiento | Desktop se actualiza cada mes; un `.pbix` nuevo no abre en una versión anterior | Dependencias fijadas en `requirements.txt`; mantener el servidor es propio |

El laboratorio no generó costos porque el enunciado no exige publicar. Desarrollar gratis no implica distribuir gratis. Fuentes: Microsoft Learn (*Download Power BI Desktop*, *Service features by license type*, *Publish to web*), página de precios de Power BI, licencia MIT de Dash y página de precios de Plotly. Enlaces en `docs/lab12/04_ernesto_visualizaciones_costos.md` §3.

## 9. Pruebas T1 a T3 (5.3 y 5.4)

Entorno común: un mismo equipo Windows 11 (AMD Ryzen 7 8845HS, 16 GB), Power BI Desktop 2.159.1231.0 y Dash del commit `b605afc` en Chrome, con los mismos CSV. Las pruebas las ejecutó un agente de software con cronómetro manual, modalidad que Diego comunicó como autorizada por el catedrático. Por eso los tiempos incluyen el control del agente y no representan a un usuario principiante.

| Prueba | Pregunta | Versión | Resultado | Clics | Tiempo (s) | Dificultades |
|---|---|---|---|---:|---:|---|
| T1 | ¿Qué vía concentró más viajeros en 2025? | Power BI | Vía Terrestre, 2.401.323 | 6 | 74,25 | Pulsar el grupo ya elegido lo deseleccionó |
| T1 | | Dash | Vía Terrestre, 2.401.323 | 5 | 35,25 | Primer intento falló al apuntar a la barra |
| T2 | ¿Qué mes del T4 de 2025 registró más viajeros? | Dash | 2025 = 3.597.238; T4 = 997.817; diciembre 392.087 | 5 | 42,94 | Desplazar la página para leer los puntos |
| T2 | | Power BI | Mismas cifras; 2026 aparece con 1.682.636 | 10 | 131,13 | Hizo falta «Mostrar como tabla» para leer cifras exactas |
| T3 | Entre SARIMA, Holt-Winters y SES, ¿cuál tiene menor error? | Power BI | SES: MAE 175.088,44; RMSE 194.790,81; MAPE 58,11 % | 9 | 105,55 | Página larga; las listas quedan abiertas |
| T3 | | Dash | SES, mismas tres métricas | 6 | 42,47 | G6 y G7 en secciones distintas |

Las tres tareas dieron el mismo resultado en ambas versiones. La diferencia de tiempo no se atribuye a la herramienta: hay una sola ejecución, el operador conocía el informe y los eventos de interfaz no son equivalentes. Detalle y capturas en `docs/lab12/05_diego_pruebas.md`.

<div class="par"><div><img src="../figuras/lab12_diego_t1_dash.png"><div class="pie">T1 en Dash</div></div><div><img src="../figuras/lab12_diego_t1_pbi.png"><div class="pie">T1 en Power BI</div></div></div>

<div class="par"><div><img src="../figuras/lab12_diego_t2_dash.png"><div class="pie">T2 en Dash</div></div><div><img src="../figuras/lab12_diego_t2_pbi.png"><div class="pie">T2 en Power BI</div></div></div>

<div class="par"><div><img src="../figuras/lab12_diego_t3_dash.png"><div class="pie">T3 en Dash</div></div><div><img src="../figuras/lab12_diego_t3_pbi.png"><div class="pie">T3 en Power BI</div></div></div>

## 10. Consistencia de indicadores (5.5)

| Indicador | Filtros y agregación | Dash | Power BI |
|---|---|---:|---:|
| Viajeros totales 2025 | Serie Total, suma de los 12 meses de 2025 | 3.597.238 | 3.597.238 |
| MAE de SES, serie Total | 63 meses, abril 2021 a junio 2026 | 175.088,44 | 175.088,44 |

Power BI calcula internamente 3.597.237,9999999995 y 175.088,43650293106; la diferencia viene de la representación decimal de los CSV y desaparece al redondear. Discrepancia de presentación: en el nivel anual, Dash omite 2026 porque solo tiene seis meses, mientras que V1 lo muestra con 1.682.636. Es un total parcial, no una caída frente a 2025; V4 es la visualización que compara solo años completos.

## 11. Recomendaciones (5.6)

| Escenario | Herramienta | Justificación | Costos y límites | Limitaciones de la recomendación |
|---|---|---|---|---|
| Consulta periódica de indicadores por directivos | Power BI | Páginas por pregunta, marcadores para volver a la vista inicial y drill sin programar; cifras iguales a Dash (5.5). | Pro para cada lector (USD 14 al mes) o capacidad F64; sin licencias solo se comparte el `.pbix`, que exige Windows. Más clics en T2 y T3. | Pruebas hechas por un agente, no por directivos. Solo conviene si la organización ya tiene licencias de Microsoft. |
| Exploración con controles o visualizaciones personalizados | Dash | Reproduce el mapa de calor con meses sin dato, recalcula métricas y admite cualquier control; Power BI exigió sustituciones y correcciones de DAX. | Licencia MIT sin costo; requiere programar y mantener dependencias. | Refleja la experiencia del equipo en Python; no se evaluaron visuales de terceros de Power BI. |
| Consulta desde un navegador por usuarios externos sin instalar software | Dash desplegado | Solo exige navegador; el contenedor ya existe en el repositorio. | Servidor propio o Plotly Cloud (Free con 3 lectores privados, Pro USD 29 al mes). En Power BI, el acceso externo sin licencia solo es posible con «Publicar en la web», que deja los datos públicos. | No se midió el costo real del servidor ni se probó con usuarios externos. |
| Observatorio de turismo sostenible | Dash como plataforma principal; Power BI opcional para uso interno | Un observatorio publica para un público amplio, necesita visualizaciones propias y trabajo con Git entre varias personas. | El servidor y el código los mantiene el equipo; dos versiones duplican la verificación de cifras. | Los precios pueden cambiar y no hubo pruebas con usuarios reales del observatorio. |

## 12. Reproducción

Las instrucciones completas están en `powerbi/README.md`: versión de Power BI Desktop, estructura de carpetas, cómo abrir el informe, cómo cambiar `RutaInsumos` y actualizar (con los conteos de control 1.470 / 2.205 / 35), las tablas `Predicciones` y `Metricas`, cómo reproducir T1 a T3 y cómo abrir el Lab 10 (`git worktree add ../lab10-tablero lab10`, `pip install -r requirements.txt`, `python -m app.main`, <http://127.0.0.1:8050>). Las versiones del informe son v0.1 `f43b181`, v0.2 `f4eb7b0`, v0.3 `d022104` y v1.0 `a3d5706`.

README: <https://github.com/ecarcamo/CC3084-DATA-SCIENCE/blob/lab12/powerbi/README.md>
