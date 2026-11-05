# Lab 12 · Preguntas de gestión, planificación y protocolo de comparación

**Responsable:** Esteban. **Fecha:** 5 de noviembre de 2026. **Alcance:** avance A1, A3 y A7.

**Punto de partida:** `b47e73d` en `lab12`, con la importación de Diego (v0.1) y el diseño de Hugo (v0.2). La versión de referencia del Laboratorio 10 es la rama `lab10`, tablero en Dash. No se modificaron `insumos/`, `app/` ni el `.pbix`; la edición del informe sigue a cargo de Hugo.

## 1. Preguntas de gestión, público y alcance · A1

### Público

Directivos y tomadores de decisiones del sector turístico que no necesariamente tienen formación en estadística. El informe debe leerse sin conocer los procedimientos de los modelos; los términos técnicos (MAE, RMSE, MAPE, estimación) se explican en la página donde aparecen.

### Preguntas

Se conservan las ocho preguntas del Laboratorio 10, con el mismo texto. Cada visualización de Power BI responde a la pregunta de su gráfica equivalente.

| Lab 10 | Power BI | Pregunta de gestión | Página prevista |
|---|---|---|---|
| G1 | V1 | ¿Cómo ha evolucionado el ingreso de viajeros? | Datos observados |
| G2 | V2 | ¿Qué vías o países concentran más viajeros? | Datos observados |
| G3 | V3 | ¿En qué meses se concentra el ingreso de viajeros? | Estacionalidad y años |
| G4 | V4 | ¿Cómo cambia el total de viajeros entre años completos? | Estacionalidad y años |
| G5 | V5 | ¿Cuánto cambió cada mes frente al mismo mes del año anterior? | Datos observados |
| G6 | V6 | ¿Qué estimaron los modelos frente a lo que se registró? | Predicciones y modelos |
| G7 | V7 | ¿Qué modelo se equivoca menos para esta serie? | Predicciones y modelos |
| G8 | V8 | ¿En qué meses se alejó el modelo de lo observado? | Predicciones y modelos |

Se compara contra `lab10` y no contra `lab11`, porque `lab11` cambió G6 y G7 y retiró G8.

### Alcance

Igual al del Laboratorio 10:

- **Datos observados:** siete series mensuales de viajeros (Total, tres vías de ingreso y tres países de residencia), de enero de 2009 a junio de 2026.
- **Estimaciones:** resultados existentes del Laboratorio 1 de cinco modelos (SARIMA, Holt-Winters, SES, Seasonal Naive y Prophet), de abril de 2021 a junio de 2026, 63 meses por serie y modelo. Se cumplen los tres modelos mínimos; SARIMA, Holt-Winters y SES son la selección inicial, como en G6.
- **Métricas:** MAE, RMSE y MAPE de `metricas_modelos.csv`, calculadas sobre los 63 meses completos.
- No se entrenan modelos nuevos ni se recalculan predicciones.

### Decisiones que puede apoyar

- Identificar las vías y los mercados que concentran más viajeros en un año, para priorizar recursos de atención.
- Localizar las temporadas altas y bajas de cada serie para planificar personal y servicios.
- Revisar si un año completo o un mes concreto creció o cayó frente al anterior.
- Saber qué estimación histórica se acercó más a lo registrado en cada serie, para decidir con qué cautela consultarla.

### Fuera de alcance

- Explicar las causas de los cambios. Los datos describen volúmenes registrados, no sus motivos.
- Pronosticar meses futuros. Las estimaciones corresponden a meses ya registrados y no tienen intervalos de confianza.
- Representar todos los mercados de origen. Los tres países no suman el total y nunca se mezclan con las vías.
- Comparar años incompletos, como 2026, con años completos.
- Garantizar la precisión futura de un modelo. Un error histórico menor no la asegura, y los CSV no documentan una separación independiente entre entrenamiento y evaluación.

## 2. Planificación de tareas y responsables · A3

Fechas de terminación propuestas. Las celdas «por confirmar» se acuerdan en el grupo; no se registran fechas de realización que no hayan ocurrido.

| Tarea | Responsable | Terminación | Estado al 5-nov 16:30 |
|---|---|---|---|
| Importación, relaciones y medidas base (A5, 4.4, 4.5) | Diego | 5-nov | Hecho, `f43b181`, `c147d9e` |
| Paleta, tema, boceto y navegación (A2, A4, 4.2) | Hugo | 5-nov | Hecho, `e668fd8`, `b47e73d` |
| V1 y V2 enlazadas (A6) | Hugo | 5-nov | Hecho, `f4eb7b0` |
| Preguntas, alcance, planificación y protocolo (A1, A3, A7) | Esteban | 5-nov | Este documento |
| Entrega del avance en Canvas | Ernesto | 5-nov 17:20 | Pendiente |
| Especificación de V5–V8 y equivalencia con G5–G8 | Esteban | 6-nov | Pendiente |
| V5–V8 en Power BI | Diego | 7-nov | Pendiente |
| V3, V4, navegación final, marcadores, restablecimiento, drillthrough y mensajes sin datos | Hugo | 7-nov | Pendiente |
| Ejecución de las tres pruebas en ambas versiones y verificación de indicadores (5.3–5.5) | Esteban | 7-nov | Pendiente |
| Costos, licencias y condiciones de distribución con fuentes oficiales (5.2) | Por confirmar | 7-nov | Pendiente |
| Matriz de comparación y recomendaciones (5.1, 5.6) | Esteban | 8-nov | Pendiente |
| README de Power BI, documento de diseño y PDF final | Por confirmar | 8-nov 20:00 | Pendiente |
| Revisión cruzada y entrega final | Todo el equipo | 8-nov 23:59 | Pendiente |

Hugo conserva la edición del `.pbix` hasta terminar la sesión 2. Quien edite después recibe el archivo por traspaso explícito, para no sobrescribir trabajo.

### Registro de tiempo efectivo (4.6)

Cada integrante anota sus minutos reales por herramienta al terminar cada tarea. Lo medido se distingue de lo estimado.

| Integrante | Power BI (Lab 12) | Dash (Lab 10) | Tipo |
|---|---:|---:|---|
| Hugo | 30 min | 60 min | Power BI medido; Dash estimado por recuerdo |
| Diego | Por registrar | Por registrar | — |
| Esteban | Por registrar | Por registrar | — |

## 3. Criterios de comparación y protocolo de las tres pruebas · A7

### Criterios de la matriz (5.1)

En la entrega final, la matriz tendrá las columnas criterio, evidencia en Dash, evidencia en Power BI e implicación para la tarea. Para el avance se fija qué evidencia se recoge en cada criterio.

| Criterio | Evidencia a recoger en ambas versiones |
|---|---|
| Facilidad de aprendizaje | Conocimientos previos necesarios y dificultades anotadas por cada integrante. |
| Tiempo de desarrollo | Registro de tiempo de la sección 2, por visualización comparable. |
| Preparación y actualización de datos | Pasos para cargar los CSV y para refrescarlos tras un cambio de ruta o de datos: `app/data.py` frente a Power Query y `RutaInsumos`. |
| Integración de resultados de modelos | Cómo se relacionan predicciones y métricas sin duplicar filas: `model_results.align_models` frente a las relaciones y medidas DAX. |
| Interacción y navegación | Clics de las tres pruebas; enlace G2 → G1 frente a filtrado cruzado V2 → V1; casillas de gráficas visibles frente a páginas y marcadores. |
| Personalización | Qué se pudo reproducir del Lab 10 y qué se sustituyó, por ejemplo el mapa de calor por una matriz con formato condicional. |
| Rendimiento | Tiempo de carga inicial y de respuesta a un filtro, en el mismo equipo cuando sea posible. |
| Colaboración y control de versiones | Diferencias legibles en Git: código Python frente a `.pbix` binario y definiciones PBIR. |
| Requisitos para compartir o desplegar | Qué necesita quien consulta: Python y servidor frente a Power BI Desktop o el servicio con licencia. |

Para costos y acceso (5.2) se registrarán sistema operativo, licencias, alojamiento y restricciones, con enlace a la documentación oficial y fecha de consulta. El uso local gratuito se separa de las condiciones para publicar y compartir. Un dato de entorno ya conocido: Power BI Desktop solo se ejecuta en Windows, mientras que el tablero de Dash corre en Linux, Windows o macOS desde un navegador.

### Condiciones comunes (5.4)

- Mismos CSV de `insumos/`, sin refrescar ni modificar.
- Estado inicial de cada versión: recién abierta, sin selecciones previas. En Power BI, grupo «Vía de ingreso» y año 2025, como deja Hugo la página.
- Para cada prueba se registran el resultado obtenido, los clics desde el estado inicial, el tiempo con cronómetro desde el primer clic hasta leer el resultado, y las dificultades.
- Se anotan el equipo, el sistema operativo, la ventana y la experiencia previa de quien ejecuta. Power BI necesita Windows; si se ejecuta en otro equipo o en una máquina virtual, esa diferencia se informa y no se atribuye a la herramienta.
- Una persona ejecuta las tres pruebas en ambas versiones, en orden alterno, para no favorecer a la que se usa en segundo lugar.

### Prueba 1 · Responder una pregunta de gestión con filtros

**Pregunta:** ¿Qué vía de ingreso concentró más viajeros en 2025 y cuántos registró?

| Paso | Dash (Lab 10) | Power BI |
|---|---|---|
| 1 | En G2, elegir el grupo «Vía de ingreso». | En Datos observados, segmentador de grupo en «Vía de ingreso». |
| 2 | Elegir el año 2025. | Segmentador de año en 2025. |
| 3 | Leer la primera barra y su valor en el cursor. | Leer la primera barra de V2 y su valor. |

**Resultado esperado:** Vía Terrestre, **2.401.323** viajeros, seguida de Vía Aérea con **1.188.971** y Vía Marítima con **6.944**. La suma es **3.597.238**, igual al Total de 2025. Ningún país ni el Total aparecen en el ranking.

### Prueba 2 · De la vista general al detalle y regreso

**Pregunta:** En la serie Total, ¿qué mes del cuarto trimestre de 2025 registró más viajeros?

| Paso | Dash (Lab 10) | Power BI |
|---|---|---|
| 1 | En G1, serie Total y nivel anual. Leer 2025. | V1 sin selección, en Total y nivel Año. Leer 2025. |
| 2 | Cambiar a nivel trimestral y leer T4 2025. | Bajar a Trimestre desde 2025 y leer T4. |
| 3 | Cambiar a nivel mensual y leer octubre a diciembre de 2025. | Bajar a Mes desde T4 y leer octubre a diciembre. |
| 4 | Volver al nivel anual. | Subir dos niveles hasta Año. |

**Resultado esperado:** 2025 suma **3.597.238**; T4 2025, **997.817**; octubre **277.299**, noviembre **328.431** y diciembre **392.087**. Diciembre es el máximo del trimestre. Al regresar se ven de nuevo los totales anuales.

Hay que vigilar 2026, que solo tiene seis meses. Dash no suma periodos incompletos: omite 2026 en el nivel anual y lo menciona en la nota. La jerarquía de Power BI suma lo que haya y mostraría 2026 con **1.682.636**, que puede leerse como una caída anual. La diferencia se registra en la prueba, y en Power BI se marca 2026 como año parcial o se excluye del nivel Año.

En Dash el detalle se cambia con el selector de nivel de G1; en Power BI, con la jerarquía Año > Trimestre > Mes de V1. Se cuentan los clics de ambos recorridos completos, incluido el regreso.

### Prueba 3 · Consultar las predicciones y comparar tres modelos

**Pregunta:** Para la serie Total, entre SARIMA, Holt-Winters y SES, ¿qué modelo tiene menor error medio y cuánto?

| Paso | Dash (Lab 10) | Power BI |
|---|---|---|
| 1 | En G6, serie Total con SARIMA, Holt-Winters y SES. Observar las tres estimaciones frente a lo observado. | En Predicciones y modelos, serie Total y los mismos tres modelos en V6. |
| 2 | En G7, serie Total y medida MAE. Leer el orden de las barras. | Leer V7 con la medida MAE. |
| 3 | Repetir con RMSE y MAPE. | Repetir con RMSE y MAPE. |

**Resultado esperado**, conjunto de evaluación de abril de 2021 a junio de 2026, 63 meses:

| Modelo | MAE (viajeros) | RMSE (viajeros) | MAPE (%) |
|---|---:|---:|---:|
| SES | 175.088,44 | 194.790,81 | 58,11 |
| Holt-Winters | 196.956,01 | 216.457,08 | 65,30 |
| SARIMA | 250.722,71 | 274.289,54 | 83,48 |

SES tiene el menor error en las tres métricas. MAE y RMSE se expresan en viajeros y MAPE en porcentaje, así que solo se comparan modelos dentro de una misma métrica, nunca métricas entre sí. G7 recalcula las métricas sobre las fechas comunes y Power BI importa las del CSV. Ambas cubren los mismos 63 meses y la auditoría del Lab 10 comprobó que las 105 métricas recalculadas coinciden con el CSV, así que no se espera diferencia.

### Verificación de dos indicadores (5.5)

| Indicador | Filtros y agregación | Valor esperado |
|---|---|---:|
| Viajeros totales 2025 | Serie Total, año 2025, suma de los 12 meses | 3.597.238 |
| MAE de SES para la serie Total | 63 meses comunes, sin filtro de fechas | 175.088,44 |

Si alguna versión muestra otro valor, se documenta la diferencia y su causa antes de concluir. Power BI ya mostró 3.597.237,9999999995 para el primer indicador: la diferencia viene de la representación decimal de los CSV y desaparece al redondear a enteros.

## 4. Pendientes para la entrega final

- Ejecutar las tres pruebas en ambas versiones y registrar resultado, clics, tiempo y dificultades.
- Completar la matriz con la evidencia y la implicación de cada criterio.
- Consultar la documentación oficial de licencias y distribución de Power BI, con fecha.
- Formular las recomendaciones de los tres escenarios de 5.6 a partir de esos resultados.
