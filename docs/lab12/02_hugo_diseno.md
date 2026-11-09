# Lab 12 · Diseño, navegación y visualizaciones enlazadas

**Responsable:** Hugo. **Actualización:** 8 de noviembre de 2026. **Alcance:** diseño final 4.2, V1–V5, navegación, marcadores y obtención de detalles.

**Estado:** v0.3 guardada y comprobada localmente, con Inicio activa y Desktop cerrado. La evidencia final se registra en `02_hugo_validacion_final.json`. No se ejecuta `git push` ni se envía el traspaso automáticamente.

## 1. Alcance y archivos

La propuesta conserva las preguntas, fuentes y colores del Lab 10. La consulta histórica se realizó contra la rama `lab10`, no contra `lab11`. No se modificaron `insumos/` ni `app/`, ni se entrenaron modelos.

| Entregable | Archivo |
|---|---|
| Tema importable | `powerbi/tema_observatorio.json` |
| Boceto de las cinco páginas | `docs/figuras/lab12_hugo_boceto.png` |
| Informe v0.3 con cinco páginas y Control oculta | `powerbi/observatorio_turismo.pbix` |
| Generador de las cinco páginas PBIR | `docs/scripts/build_lab12_report.py` y `docs/scripts/lab12_final_pages.py` |
| Medidas reproducibles de V3–V5 y detalle | `powerbi/medidas_hugo.json` y `docs/scripts/apply_lab12_measures.ps1` |
| Generador del boceto | `docs/scripts/draw_lab12_wireframe.py` |
| Pruebas automatizadas | `tests/test_lab12_design.py` |
| Capturas reales finales | Índice de páginas, exploración y mensajes en la sección 9 |

La edición del informe fue autorizada por el usuario tras confirmar el traspaso de Diego a Hugo. Se conservan los datos importados, las relaciones y las medidas base. El avance v0.2 agregó `Titulo V1`; v0.3 agrega las 17 medidas declaradas en `medidas_hugo.json`. Las copias anteriores permanecen en TEMP, fuera del control de versiones.

## 2. Paleta y justificación · A2

| Uso | Color | Justificación |
|---|---|---|
| Datos observados | Azul `#1F4E79` | Color frío y estable para datos registrados. Mantiene el significado del Lab 10. |
| Estimaciones | Naranja `#A65E16` | Contrasta con el azul y separa las estimaciones de las observaciones. |
| Selección activa | Verde `#20745A` | Se reserva para selección y página activa, no para otra serie. |
| Alertas y ausencia de datos | Rojo `#B3261E` | Se acompaña de una advertencia escrita, nunca aparece como otra serie. |
| Fondo | `#F4F6F8` | Separa el lienzo de las tarjetas sin competir con los datos. |
| Tarjetas | Blanco `#FFFFFF` | Mantiene una superficie uniforme para gráficas y texto. |
| Texto principal | `#1B2733` | Facilita la lectura de títulos y cantidades. |
| Texto secundario | `#5B6B7A` | Diferencia las ayudas sin perder contraste. |
| Cuadrícula | `#DDE3E9` | Referencia tenue que no sustituye los ejes ni sus etiquetas. |
| Escala de estacionalidad | `#E7EFF6` → `#1F4E79` | Escala secuencial equivalente a G3 para valores de menor a mayor magnitud. |

El tema contiene los cinco colores de modelos, pero una paleta automática no garantiza su correspondencia con cada modelo. Al construir V6 se asignarán explícitamente los siguientes nombres, colores y trazos:

| Modelo | Color | Trazo del Lab 10 |
|---|---|---|
| SARIMA | `#A65E16` | Guiones |
| Holt-Winters | `#6B3A0C` | Puntos |
| SES | `#C46A12` | Guion y punto |
| Seasonal Naive | `#8A4B12` | Guion largo |
| Prophet | `#D07A1E` | Guion largo y punto |

Se conserva **Arial** para evitar que una tipografía diferente afecte la comparación con Dash. Los títulos de gráficas tienen 14 pt; las etiquetas y ayudas, 10 pt. Los mensajes sin datos utilizan 12 pt y la tarjeta del último año completo utiliza 28 pt.

Las pruebas comprueban una relación de contraste de al menos **4,5:1** para los colores de texto del tema tanto sobre blanco como sobre el fondo gris. Los tonos naranjas de los modelos no se emplean como texto pequeño. La cuadrícula es decorativa y no se interpreta como texto.

El significado no depende únicamente del color: los modelos tendrán nombres y trazos diferentes; la página activa tiene una etiqueta; la ausencia de datos se indica con celdas vacías y un mensaje. La selección nativa atenúa las otras barras y cambia el nombre y el contenido de V1. El resaltado verde del boceto no representa el estilo nativo de selección de barras.

## 3. Boceto y navegación · A4

![Boceto de las cinco páginas](../figuras/lab12_hugo_boceto.png)

El dibujo es un boceto con marcas ilustrativas, no una captura de Power BI ni una representación de valores reales.

| Página | Contenido | Navegación y contexto |
|---|---|---|
| Inicio | Propósito, cobertura, leyenda y accesos por pregunta | Botones a cada página analítica. |
| Datos observados | V1, V2 y V5 | Grupo y año filtran solo el ranking. V2 filtra V1 y V5. |
| Estacionalidad y años | V3 y V4 | Selección de serie y años. V4 excluye años incompletos. |
| Predicciones y modelos | V6, V7, V8 y tabla de apoyo | Serie única. Las métricas importadas representan los 63 meses completos. |
| Detalle de serie | Historia y contexto de una serie | Obtención de detalles desde V2 o V7 con `DimSerie[nombre]` y botón de regreso. |

Las cinco páginas incorporan botones de navegación, página activa en verde, ayuda breve y «Restablecer vista». Cada marcador guarda datos, visualización y página actual. El botón Atrás de Detalle de serie conserva el origen y no sustituye el restablecimiento.

### Equivalencia con Lab 10

- Se conservan las ocho preguntas G1–G8, las siete series, los cinco modelos, los colores y el clic ranking → serie temporal.
- Se sustituye la página única con casillas de visibilidad por páginas temáticas. Se reduce la cantidad de gráficos simultáneos y se agrupan preguntas relacionadas.
- V3 sustituye el mapa de calor por una matriz año × mes con formato condicional. Conserva la escala y agrega cantidades por celda, sin cambiar la pregunta.
- Las tarjetas, segmentadores, botones, ayudas y tabla de modelos no cuentan como visualizaciones analíticas.
- No se comparan años incompletos con años completos. Los tres países no representan todos los mercados y nunca se suman con las vías o el total.

En v0.3 existen las cinco páginas del boceto. La página técnica Control se conserva oculta en modo de lectura. Predicciones y modelos contiene el título, la cobertura de evaluación y un aviso de preparación; Diego implementa V6–V8.

## 4. V1, V2 e interacciones · A6

| Aspecto | V1 · Evolución | V2 · Ranking |
|---|---|---|
| Pregunta | ¿Cómo ha evolucionado el ingreso de viajeros y en qué épocas sube o baja? | ¿Qué vías o países concentran más viajeros? |
| Tipo | Gráfica de líneas | Barras horizontales |
| Eje | Calendario: Año > Trimestre > Mes | `DimSerie[nombre]` |
| Valor | `[Viajeros serie]`, en Medidas | `[Viajeros]`, en Medidas |
| Orden | Tiempo ascendente | Viajeros descendente |
| Color base | Azul observado | Azul observado |
| Filtro específico | Una serie seleccionada o Total por defecto | Grupo Vía de ingreso o País de residencia; excluye Total |

La definición PBIR configura **V2 → V1 como `DataFilter`**, equivalente a elegir «Filtrar» en «Editar interacciones». No se utiliza un segmentador compartido como sustituto de esta relación.

Los segmentadores de grupo y año afectan **solo a V2**, como en Lab 10. El estado inicial es «Vía de ingreso», año 2025. Un clic en «Vía Aérea» debe mostrar su historia completa en V1, sin limitarla a 2025. Al retirar la selección, `[Viajeros serie]` debe volver a Total. Con varias series seleccionadas la medida devuelve Total, nunca una suma de vías y países.

Las interacciones inversas y las interacciones entre segmentadores están desactivadas. La selección de una barra no debe reducir las opciones del grupo o del año.

La exploración temporal se prepara con los campos Año, Trimestre y Mes en el eje, inicialmente en Año. No se utiliza la jerarquía automática de fechas. La operación de exploración se verifica en Desktop.

### Título de la serie

La medida `Titulo V1` se creó desde Power BI Desktop y se vinculó al título de V1 mediante una expresión de formato condicional en PBIR:

```dax
Titulo V1 =
"Viajeros: "
    & IF (
        HASONEVALUE ( DimSerie[nombre] ),
        SELECTEDVALUE ( DimSerie[nombre] ),
        "Total"
    )
```

El título debe alternar entre «Viajeros: Total» y «Viajeros: Vía Aérea» durante la prueba de selección. La pregunta de gestión se conserva en esta especificación y en el texto alternativo de la gráfica.

## 5. Protocolo de comprobación en Power BI

1. Abrir el `.pbix` con Power BI Desktop 2.159.1231.0 o una versión compatible. Confirmar que no existen avisos de archivo inválido ni errores de consulta.
2. Confirmar Arial, fondo gris, tarjetas blancas y líneas azules. El tema también puede importarse desde «Vista > Temas > Examinar temas».
3. Seleccionar «Datos observados» y verificar grupo «Vía de ingreso», año 2025.
4. Confirmar el ranking: Terrestre **2.401.323**, Aérea **1.188.971** y Marítima **6.944** viajeros. La suma es **3.597.238**.
5. Confirmar V1 en Total y explorar Año > Trimestre > Mes. El total de 2025 debe redondearse a **3.597.238**.
6. Hacer clic en «Vía Aérea». V1 debe cambiar a esa serie, conservar toda su cobertura y mostrar **1.188.971** al consultar 2025. Guardar la captura con selección.
7. Quitar la selección y confirmar el regreso a Total. Guardar la captura inicial.
8. Cambiar el grupo a «País de residencia». Confirmar El Salvador **1.738.267**, Estados Unidos **679.282** y Honduras **298.542** en 2025. No deben aparecer vías ni Total en ese ranking.
9. Revisar «Formato > Editar interacciones»: V2 filtra V1; grupo y año no filtran V1. Confirmar el título dinámico tras aplicar la medida anterior.
10. Restituir el grupo Vía de ingreso, año 2025 y ninguna barra seleccionada. Guardar, cerrar y reabrir el informe para confirmar la persistencia.

Capturas requeridas:

- `docs/figuras/lab12_hugo_v1_v2_inicial.png`
- `docs/figuras/lab12_hugo_v1_v2_seleccion.png`

Solo se aceptan capturas reales de Power BI como evidencia de A6. El boceto y las pruebas de estructura no reemplazan la prueba gráfica → gráfica.

### Comprobación histórica del avance v0.2

La prueba nativa se ejecutó con Power BI Desktop **2.159.1231.0**. El ranking mostró 2.401.323, 1.188.971 y 6.944 viajeros para las tres vías en 2025. La selección de Vía Aérea cambió el título a «Viajeros: Vía Aérea» y el primer punto anual de V1 a **935.379** viajeros de 2009. Al retirar la selección reaparecieron «Viajeros: Total» y **2.028.776** viajeros de 2009. La permanencia de 2009 confirma que el segmentador 2025 no limita la historia de V1.

Las cantidades de las siete series en 2025 se contrastaron también con los CSV originales. Las capturas siguientes proceden de la ventana nativa de Power BI, no de una recreación. La selección nativa mantiene la barra elegida y atenúa las demás; el título identifica la serie sin depender del color.

Después de guardar y cerrar Desktop, una instancia nueva conservó el tema, los tres valores del ranking, «Viajeros: Total» y la interacción con Vía Aérea. Las **12 pruebas automatizadas** del diseño, el tema, el boceto y la escritura segura del contenedor pasaron. La validación de las cinco definiciones PBIR generadas también pasó contra sus esquemas oficiales. La evidencia y las huellas de los archivos se conservan en [02_hugo_validacion.json](02_hugo_validacion.json).

![Estado inicial, Total](../figuras/lab12_hugo_v1_v2_inicial.png)

![Vía Aérea seleccionada en V2 y reflejada en V1](../figuras/lab12_hugo_v1_v2_seleccion.png)

El registro de tiempo de `TEMP/CONTEXTO.md` recoge **30 minutos reales de Power BI** y **60 minutos estimados de Dash Lab 10**, ambos declarados por Hugo. La estimación de Dash se basa en su recuerdo, no en una medición de commits.

## 6. Reproducción y precauciones

Desde la raíz del repositorio, con el entorno Python académico existente:

```powershell
..\.venv\Scripts\python.exe docs/scripts/draw_lab12_wireframe.py
..\.venv\Scripts\python.exe -m pytest tests/test_lab12_design.py tests/test_wireframe.py tests/test_theme.py -q
```

El generador `build_lab12_report.py` se ejecuta únicamente con Desktop cerrado y sobre una copia controlada del informe que ya contenga las medidas requeridas. Reemplaza las cinco páginas visibles y la referencia al tema; no debe ejecutarse después de ajustes manuales sin respaldarlos primero. Conserva el modelo binario de entrada y la página Control. El contenedor se escribe primero en un archivo temporal y solo reemplaza al original después de comprobar su integridad.

`RutaInsumos` continúa con el valor del equipo de Diego porque forma parte del modelo preservado. Antes de actualizar los datos en otro equipo se deberá cambiar ese parámetro a la carpeta local `insumos`. No es necesario refrescar para comprobar los datos ya importados.

Los esquemas oficiales PBIR se usan para comprobar la estructura de la página y las gráficas. Esa comprobación no certifica la renderización, los nombres del modelo ni el comportamiento de la aplicación. El control nativo de apertura prevalece sobre una validación de JSON.

Las limitaciones de esta comprobación histórica corresponden a v0.2. La evidencia final separada identifica las verificaciones nativas de v0.3, sin presentar los esquemas JSON como prueba de interacción.

## 7. Construcción final de V3–V5

La ficha de Ernesto en `04_ernesto_visualizaciones_costos.md`, secciones 2.1–2.4, determina campos, fórmulas, mensajes e interacciones. Las medidas se conservan como expresiones DAX en `powerbi/medidas_hugo.json`, se aplican a la tabla Medidas y no modifican los CSV ni entrenan modelos.

| Visualización | Construcción | Contexto inicial y ausencia de datos |
|---|---|---|
| V3 | Matriz de Año por Mes, ordenada mediante MesNum, con Viajeros serie. Degradado `#E7EFF6` → `#1F4E79`; texto blanco desde el umbral de 55 % indicado por la ficha. Sin subtotales ni totales generales. | Serie única Total y años 2009–2026. Nota: 210 meses válidos y seis sin dato. Las celdas vacías no son ceros. |
| V4 | Columnas por Año con Total año completo, eje desde cero. Solo se devuelve un valor cuando existen doce meses válidos. | Comparte serie y años con V3. Se muestran 17 años, de 2009 a 2025; la nota excluye 2026 por contar con seis meses. |
| V5 | Columnas de variación mensual, jerarquía Año y Mes expandida, con línea constante discontinua en 0 %. | Fechas propias: 1-ene-2010 a 30-jun-2026. El clic en V2 cambia la serie. Grupo y año del ranking no afectan V5; sus fechas no afectan V1 ni V2. |

Cada visualización incluye una medida Mensaje V3, Mensaje V4 o Mensaje V5 en rojo `#B3261E`, con Arial de 12 pt. Las notas explican el cálculo, los meses omitidos y los límites de interpretación. La falta de base del año anterior o una base igual a cero devuelve vacío, no cero.

Los conteos vacíos se presentan como cero mediante `COALESCE`, para evitar notas como «Se muestran años completos» sin cantidad. Esto no convierte una observación ausente en cero. Las tarjetas usan margen interior de 4 px para mostrar completo el mensaje de V5. V3 y V5 identifican la serie mediante un subtítulo dinámico. V5 oculta los botones de exploración y su marcador desactiva esa exploración.

La validación del modelo abierto compara las 1.470 observaciones con los CSV, los 119 totales completos de las siete series y las 1.344 variaciones válidas. También comprueba meses sin dato, años incompletos y ausencia de base. Los controles de Total incluyen diciembre de 2025 igual a 392.087, 2024 igual a 3.593.876, 2025 igual a 3.597.238, enero de 2025 igual a −8,06 % y 198 meses calculados.

### Diseño final frente al Lab 10

Se conservan Arial, la semántica de los colores, las siete series, las ocho preguntas y los cinco modelos. Se conservan el enlace del ranking con la historia, la exclusión de años incompletos y la advertencia sobre porcentajes altos tras 2020.

Se modifican los controles de granularidad por exploración nativa, las casillas de visibilidad por páginas y el mapa de calor por la matriz. Las marcas de ausencia pasan a celdas vacías o meses omitidos con explicación escrita. Las notas evitan interpretar una ausencia como cero o atribuir causas al patrón temporal.

El lienzo usa una cuadrícula de 1.280 px de ancho. La vista ajusta el ancho y permite desplazamiento vertical para conservar el tamaño del texto, en lugar de comprimir todas las visualizaciones. Los botones repiten su posición entre páginas; el verde y el nombre identifican la página activa.

El eje mensual categórico de V5 conserva el desplazamiento horizontal nativo. La selección inicial contiene 198 meses, aunque una captura solo muestra parte del eje. Se puede desplazar la gráfica o acotar sus fechas para revisar un mes concreto.

## 8. Navegación, marcadores y detalle

Hay cinco botones de página en todas las páginas y tres accesos por pregunta en Inicio. El marcador `Inicial – <página>` guarda la página, los segmentadores y las selecciones. En Desktop los botones se activan con Ctrl + clic; en modo de lectura basta un clic.

Datos observados vuelve a grupo Vía de ingreso, año 2025, ninguna barra seleccionada y fechas iniciales de V5. Estacionalidad y años vuelve a Total y 2009–2026. Predicciones y modelos queda preparada para que Diego actualice su marcador al agregar sus segmentadores. Control no se borra.

Los marcadores incluyen el orden de las consultas y los filtros fijos de cada visualización. Sin ellos, Desktop podía restablecer V2 sin conservar el orden descendente por viajeros ni su filtro que excluye Total. La prueba final compara las posiciones de las tres categorías y el filtro guardado después de restablecer.

Detalle de serie utiliza `DimSerie[nombre]` como campo de obtención de detalles y conserva los filtros del origen, conforme a la ficha de V7. La evolución resume ese contexto. El total del último año completo se calcula retirando los filtros del calendario, por lo que no compara un año incompleto con otro completo. El botón Atrás regresa al origen. Diego debe comprobar el acceso desde V7 cuando esa gráfica exista.

### Reproducción de v0.3

1. Respaldar el informe y abrirlo en Desktop 2.159.1231.0 o posterior, sin actualizar las consultas.
2. Aplicar las medidas al modelo local desde Windows PowerShell 5.1:

```powershell
& "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -File docs/scripts/apply_lab12_measures.ps1
```

3. Guardar desde Desktop y cerrar la aplicación. El script solo modifica las medidas declaradas y el orden de Mes por MesNum; no actualiza los hechos ni cambia RutaInsumos.
4. Regenerar las páginas únicamente cuando se desee reemplazar sus ajustes manuales:

```powershell
..\.venv\Scripts\python.exe -m docs.scripts.build_lab12_report
..\.venv\Scripts\python.exe -m pytest tests/test_lab12_design.py tests/test_wireframe.py tests/test_theme.py -q
..\.venv\Scripts\python.exe -m docs.scripts.lab12_valores_referencia
```

5. Reabrir en Desktop, verificar los valores, probar botones y guardar Inicio como página activa. Una validación de estructura no reemplaza este paso.

El generador conserva el modelo binario que recibe y utiliza una escritura temporal comprobada antes de reemplazar el archivo. La copia original v0.2 permanece en `TEMP/observatorio_turismo_v0.2.pbix`. No debe ejecutarse después de que Diego agregue V6–V8 sin adaptar primero la generación de su página.

## 9. Evidencia y traspaso

La evidencia de apertura, interacciones, controles y huellas finales se conserva en `02_hugo_validacion_final.json`. Pasaron las 18 pruebas del archivo guardado y las 78 definiciones generadas contra los esquemas oficiales. Las pruebas admiten únicamente normalizaciones conocidas de Desktop, como omitir opciones predeterminadas y listas vacías o actualizar versiones internas. Conservan la comprobación de filtros, medidas, interacciones, formatos y estados iniciales.

Durante la validación se corrigieron la transmisión del nombre en drillthrough, las fechas visibles del marcador, el orden y los filtros fijos de V2 al restablecer y el mensaje truncado de V5. Se comprobó de nuevo el contenedor después de guardar en Desktop. Las capturas reales llevan el prefijo `docs/figuras/lab12_hugo_`; no se sustituyen por el boceto.

| Evidencia final | Captura |
|---|---|
| Inicio, propósito y navegación | [Inicio](../figuras/lab12_hugo_inicio.png) |
| V1 y V2 iniciales | [Datos observados](../figuras/lab12_hugo_datos_observados.png) |
| V3, escala y meses | [Estacionalidad y años](../figuras/lab12_hugo_estacionalidad.png) |
| V4, 17 años y exclusión de 2026 | [Años completos](../figuras/lab12_hugo_anios_completos.png) |
| V5, Total y línea de cero | [Variación mensual](../figuras/lab12_hugo_variacion.png) |
| Reserva de V6–V8 para Diego | [Predicciones y modelos](../figuras/lab12_hugo_predicciones.png) |
| Total 2020 y trimestre T2 | [Exploración temporal](../figuras/lab12_hugo_drill.png) |
| Drillthrough de Vía Aérea y 1.188.971 | [Detalle de serie](../figuras/lab12_hugo_detalle.png) |
| Botón Atrás en el detalle | [Regreso](../figuras/lab12_hugo_detalle_regreso.png) |
| V5 sin base anterior y conteo cero | [Mensaje sin datos](../figuras/lab12_hugo_sin_datos.png) |

Permanecen fuera del alcance de Hugo V6–V8, las pruebas cronometradas de comparación 5.3–5.5, el informe PDF final y la entrega en Canvas. No se actualizan las fuentes ni se ejecuta entrenamiento. El traspaso se prepara en TEMP, sin publicar ni enviar mensajes externos.

Los minutos efectivos nuevos de Hugo quedan pendientes de confirmación por decisión del usuario. Se conservan los registros anteriores de 30 minutos de Power BI y 60 minutos estimados de Dash. No se sustituye tiempo efectivo por duración de sesión.

## Referencias

- [Temas de informes de Power BI](https://learn.microsoft.com/power-bi/create-reports/desktop-report-themes)
- [Interacciones entre visualizaciones](https://learn.microsoft.com/power-bi/create-reports/service-reports-visual-interactions)
- [Formato PBIR](https://learn.microsoft.com/power-bi/developer/projects/projects-report)
- [Esquema de página PBIR](https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json)
- [Esquema de visual PBIR](https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.7.0/schema.json)
