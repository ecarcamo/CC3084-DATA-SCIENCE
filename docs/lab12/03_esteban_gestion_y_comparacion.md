# Lab 12 · Preguntas de gestión, planificación y comparación de herramientas

**Responsable:** Esteban. **Fecha:** 5 de noviembre de 2026; cierre el 8 de noviembre de 2026. **Alcance:** 4.1, 4.6, protocolo de las pruebas, matriz 5.1 y recomendaciones 5.6.

**Punto de partida del cierre:** `5c6090e` en `lab12`, con el `.pbix` v1.0 congelado por Diego (SHA-256 en `powerbi/version_informe.json`). La versión de referencia del Laboratorio 10 es la rama `lab10`, tablero en Dash (`b605afc`). No se modificaron `insumos/`, `app/` ni el `.pbix`.

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

## 2. Planificación de tareas, responsables y tiempo · 4.6

### Tareas con fecha real de terminación

Las fechas y horas salen de `git log origin/lab12`. La columna «Prevista» es la del avance y del contexto compartido del equipo.

| Tarea | Responsable | Prevista | Terminada | Commits |
|---|---|---|---|---|
| Enunciado en el repositorio | Ernesto | 5-nov | 5-nov 12:29 | `2102fba` |
| Importación, relaciones y medidas base (4.4, 4.5) | Diego | 5-nov | 5-nov 15:28 | `f43b181`, `c147d9e` |
| Tema, paleta, boceto y V1–V2 enlazadas (4.2) | Hugo | 5-nov | 5-nov 16:11 | `e668fd8`, `f4eb7b0`, `b47e73d` |
| Preguntas, planificación y protocolo (4.1) | Esteban | 5-nov | 5-nov 16:18 | `8036fb6` |
| Avance consolidado y entregado | Ernesto | 5-nov 17:20 | 5-nov 17:12 | `104e1e0` … `9535812` |
| Valores de referencia, tabla 4.3 y especificación V3–V8 | Ernesto | 6-nov | 7-nov 22:05 | `37599d5`, `756a9c2` |
| Capturas G1–G8 del Lab 10 y costos 5.2 | Ernesto | 7-nov | 7-nov 22:09 | `0f37067`, `3c822b4` |
| V3–V5, navegación, marcadores y drillthrough (v0.3) | Hugo | 7-nov 23:30 | 8-nov 19:34 | `d022104`, `645d311` |
| V6–V8 y `.pbix` v1.0 congelado | Diego | 8-nov 12:30 | 8-nov 20:19 | `a3d5706`, `44eab4e`, `997a493` |
| Pruebas T1–T3 y verificación 5.5 | Diego | 8-nov 15:00 | 8-nov 21:08 | `22e7a58`, `5c6090e` |
| Matriz 5.1, recomendaciones 5.6, README y PDF final | Esteban | 8-nov 22:30 | 8-nov | este documento, `powerbi/README.md`, `informe_final.md` |
| Entrega en Canvas | Esteban | 8-nov 23:30 | 8-nov | — |

Cambios frente a lo planificado: la especificación de V3–V8 pasó de Esteban a Ernesto y las pruebas 5.3–5.5 de Esteban a Diego, porque solo Hugo y Diego tienen Windows para abrir Power BI Desktop. La v0.3 se atrasó unas 20 horas y desplazó las tareas siguientes al 8-nov.

### Tiempo efectivo por persona y herramienta

| Integrante | Dash (Lab 10) | Power BI (Lab 12) | Origen del dato |
|---|---:|---:|---|
| Hugo | 60 min | 30 min (5-nov) | Power BI real; Dash estimado por recuerdo. Los minutos de v0.3 (8-nov) no se registraron |
| Ernesto | No registrado | 15 min (7-nov, sin Power BI: script, especificación, capturas y 5.2) | Real |
| Diego | No registrado | No registrado | Diego declaró que no recuerda sus tiempos de desarrollo y no los sustituyó por duración de sesión |
| Esteban | ≈ 90 min | 0 min en Power BI; ≈ 120 min de documentación (5-nov y 8-nov) | Estimado a partir de sus commits en `lab10` (22-oct y 25-oct) y `lab12` |

**Lectura:** el registro está incompleto, así que no permite concluir qué herramienta fue más rápida de desarrollar. Lo que sí muestra el historial es la duración en calendario: el Lab 10 se construyó entre el 22 y el 25 de octubre con 20 commits de los cuatro integrantes; el Lab 12, entre el 5 y el 8 de noviembre, con el `.pbix` editado por dos personas. Los tiempos de las pruebas T1–T3 miden uso, no desarrollo, y no se suman aquí.

## 3. Criterios de comparación y protocolo de las tres pruebas

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

## 4. Matriz de comparación · 5.1

Fuentes de la evidencia: [05_diego_pruebas.md](05_diego_pruebas.md) (T1–T3, tiempos y 5.5), [04_ernesto_visualizaciones_costos.md](04_ernesto_visualizaciones_costos.md) (4.3 y 5.2), [02_hugo_diseno.md](02_hugo_diseno.md) (diseño y sustituciones), [01_diego_datos.md](01_diego_datos.md) (Power Query y DAX) y `git log` de `lab10` y `lab12`.

| Criterio | Evidencia en Dash (Lab 10) | Evidencia en Power BI (Lab 12) | Implicación para la tarea |
|---|---|---|---|
| Facilidad de aprendizaje | Python y Plotly, que el equipo ya usaba desde el Lab 1. Los cuatro integrantes escribieron código del tablero (20 commits en `lab10`: Hugo 8, Esteban 7, Ernesto 3, Diego 2). | Interfaz visual sin código para gráficos básicos, pero el DAX dio errores reales: la medida `Viajeros` chocó con la columna `viajeros`, `CONCATENATEX` sin orden dio error semántico, el formato dinámico y el estático juntos impidieron guardar y dos campos `nombre` hicieron rechazar una consulta (01_diego §5 y §8). | Para un equipo que ya programa en Python, Dash tuvo menos barrera. Power BI facilita lo básico, pero el contexto de filtro de DAX exige aprendizaje propio. |
| Tiempo de desarrollo | 22 al 25 de octubre, 20 commits, 1.545 líneas en `app/`. Hugo estimó 60 min para G1–G4 y el diseño. | 5 al 8 de noviembre, 17 commits. Hugo registró 30 min reales para V1, V2 y el tema. La v0.3 se atrasó unas 20 h. | Los minutos registrados están incompletos (4.6), así que no hay base para declarar un ganador. Ambas versiones tomaron unos cuatro días de calendario. |
| Preparación y actualización de datos | `app/data.py` lee los CSV de `insumos/` y valida en código. Para actualizar se reemplazan los CSV y se reinicia la app; la ruta es relativa al repositorio. | Power Query con el parámetro `RutaInsumos` y la configuración regional `en-US`. Diego probó el refresco desde otra carpeta: se conservaron 1.470 / 2.205 / 35 filas y el Total 2025 de 3.597.238. La ruta es absoluta y debe cambiarse en cada equipo. | Power BI documenta los pasos de forma visual y se refresca con un botón. Dash no necesita configurar rutas. El README explica el cambio de `RutaInsumos`. |
| Integración de resultados de modelos | `app/model_results.py` alinea predicciones y observado y recalcula MAE, RMSE y MAPE sobre las fechas comunes (G7). | Modelo estrella con 7 relaciones de una sola dirección y sin relaciones entre hechos; `Metricas` se importa del CSV. Las 105 métricas coinciden con el CSV (tolerancia 1e-9). Limitación: la fila «Total» de la tabla complementaria suma métricas entre modelos. | Ambas versiones dan las mismas cifras (5.5). Dash puede recalcular por periodo; en Power BI, V7 no responde a fechas y la fila Total de la tabla debe ignorarse. |
| Interacción y navegación | Una sola página con casillas «Gráficas visibles», enlace G2 → G1 por callback y selector de granularidad. Clics: T1 5, T2 5, T3 6. | Cinco páginas con botones, marcadores `Inicial – <página>`, jerarquía Año > Trimestre > Mes, drillthrough a «Detalle de serie» con Atrás y filtrado V2 → V1 y V5. Clics: T1 6, T2 10, T3 9. | Power BI separa las preguntas por página y ofrece drill y drillthrough nativos, pero en T2 y T3 necesitó más clics. Dash llega a la cifra con menos pasos porque todo está en una página. |
| Personalización | Mapa de calor nativo con × en meses sin dato, trazos por modelo y notas en código; cualquier comportamiento es un callback. | Sin mapa de calor nativo: V3 es una matriz con formato condicional. Las × pasaron a celdas vacías. Colores y trazos se fijan por medida. Para un diseño reproducible se escribieron generadores PBIR (`build_lab12_report.py`, `lab12_model_pages.py`). | Dash reproduce exactamente lo diseñado. Power BI obliga a sustituciones (4.3), aceptables pero documentadas. |
| Rendimiento | Recarga 15,75 s con el servidor ya iniciado; cambio de métrica en G7, 16,16 s. | Reapertura del `.pbix` 36,35 s; cambio de métrica en V7, 44,91 s. Hubo una ventana en blanco que obligó a cerrar y reabrir Desktop. | Los intervalos incluyen el control del agente y una sola ejecución; no aíslan el tiempo de dibujo. Sirven como registro, no como clasificación. |
| Colaboración y control de versiones | Código Python en texto: diferencias legibles por línea; cuatro autores trabajaron en paralelo en `lab10`. | El `.pbix` es binario (240 KB): no se puede combinar. Se usó un solo dueño a la vez, una cadena de traspasos, medidas en `medidas_*.json`, generadores PBIR y SHA-256 en `version_informe.json`. | Dash se adapta mejor a Git y al trabajo simultáneo. Power BI exige coordinación explícita para no sobrescribir trabajo. |
| Requisitos para compartir o desplegar | Python y `requirements.txt` en Windows, macOS o Linux; el repositorio ya trae `Dockerfile` y `docker-compose.yml`. Quien consulta solo necesita un navegador. Licencia MIT. | Desktop gratuito pero solo para Windows: 2 de 4 integrantes pudieron editarlo. Para compartir en la nube: Pro, USD 14 por usuario al mes, para quien publica y quien consume, o una capacidad F64. «Publicar en la web» expone los datos sin autenticación (5.2). | Desarrollar es gratis en ambas; distribuir no. Dash cuesta servidor y mantenimiento; Power BI cuesta licencias por usuario. |

## 5. Recomendaciones · 5.6

Se basan en la matriz, las pruebas T1–T3 y los costos de 5.2 (consultados el 7-nov-2026).

| Escenario | Herramienta | Justificación | Costos y límites encontrados | Limitaciones de la recomendación |
|---|---|---|---|---|
| (a) Consulta periódica de indicadores por directivos | **Power BI** | Páginas por pregunta, marcadores para volver a la vista inicial y drill o drillthrough sin programar. Las cifras coinciden con Dash (5.5). | Para compartir en el servicio se necesita Pro para cada lector (USD 14 al mes) o una capacidad F64. Sin licencias, solo se puede pasar el `.pbix`, que exige Windows. En T2 y T3 se necesitaron más clics que en Dash. | Las pruebas las ejecutó un agente, no directivos. Conviene solo si la organización ya tiene licencias de Microsoft. Si no, sirve mejor Dash desplegado. |
| (b) Exploración con controles o visualizaciones personalizadas | **Dash** | Reproduce el mapa de calor con marcas de meses sin dato, recalcula métricas por fechas comunes y admite cualquier control. En Power BI hubo que sustituir V3 y corregir errores de DAX. | Licencia MIT, sin costo de uso. Requiere programar en Python y mantener las dependencias. | Refleja la experiencia previa del equipo en Python. Un equipo sin programadores podría preferir Power BI con visuales de terceros, que no se evaluaron. |
| (c) Consulta desde un navegador por usuarios externos sin instalar software | **Dash desplegado** | Solo exige un navegador. El contenedor Docker ya existe en el repositorio. | Servidor propio, o Plotly Cloud: Free con 3 lectores privados, Pro a USD 29 al mes. La autenticación debe añadirla el alojamiento o el código. En Power BI, el acceso externo sin licencia solo es posible con «Publicar en la web», que deja los datos públicos sin autenticación. | No se midió el costo real del servidor ni se probó el despliegue con usuarios externos. |
| Observatorio de turismo sostenible | **Dash como plataforma principal** y Power BI opcional para el uso interno | Un observatorio publica para un público amplio, necesita visualizaciones propias (estimaciones rotuladas, meses sin dato) y trabajo con Git entre varias personas. Dash cubre los tres puntos; Power BI encaja solo en la consulta interna si INGUAT ya tiene licencias. | Mantener el servidor y el código recae en el equipo. Mantener dos versiones duplica la verificación de cifras (5.5). | Los precios pueden cambiar; los datos usados son agregados públicos. No hubo pruebas con usuarios reales del observatorio. |
