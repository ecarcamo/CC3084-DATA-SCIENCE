# Guion de la presentación — Grupo 3: Dashboards dinámicos

15 diapositivas, 5 por persona. Tiempo objetivo: **~19 min** (mínimo 15, máximo 20). El número de diapositiva coincide con `Tarea4_Grupo3.pdf`.

| Persona | Diapositivas | Tiempo |
|---|---|---|
| Ernesto | 1, 2, 3, 4 y 15 | ~6:00 |
| Hugo | 5, 6, 7, 8 y 9 | ~5:00 |
| Esteban | 10, 11, 12, 13 y 14 | ~8:00 |

**Antes de empezar (Hugo):** tener abierta la app (`streamlit run tarea4/demo/app.py`) y la imagen `tarea4/img/dashboard_estatico.png` en otra ventana.

---

## ERNESTO — Investigación (~6:00)

**Diap. 1 · Portada (0:45)**
Buenas tardes. Somos el grupo 3 y nuestro tema es dashboards dinámicos: qué aportan los filtros, la navegación y la actualización de datos. Somos Ernesto, Hugo y Esteban. Yo explico la investigación, Hugo muestra una demo y Esteban habla de la complejidad y dirige una actividad. Les dejo una pregunta guía: ¿qué preguntas no podemos responder con una imagen fija? La retomamos al final.

**Diap. 2 · Estático vs. dinámico (1:30)**
Un dashboard estático muestra una vista fija y ya agregada. Presenta respuestas. Uno dinámico deja que el usuario modifique la vista y le ayuda a descubrir respuestas. Los datos del estático son un corte en el tiempo; los del dinámico pueden actualizarse. El estático cuesta menos de desarrollar, pero no permite preguntas de seguimiento. El dinámico cuesta más y exige cierta pericia del usuario. En resumen, cambia la exploración: pasamos de leer un resultado a hacerle preguntas a los datos. Estas comparaciones vienen de QuantHub, insightsoftware y Qrvey, que son blogs de proveedores; las usamos para contrastar, no como fuente académica.

**Diap. 3 · Mantra de Shneiderman (1:45)**
La base teórica es Shneiderman, 1996: «overview first, zoom and filter, then details-on-demand». Primero una vista global, con KPIs. Luego zoom y filtros: segmentadores y resaltado cruzado. Un ejemplo de la documentación de Power BI: hacemos clic en 2023 en un gráfico de ventas por año. Con cross-filtering, los otros gráficos quitan los datos que no aplican; con cross-highlighting, los atenúan y mantienen el total visible. Y el detalle solo cuando se pide: pestañas, drill-through, que lleva a una página enfocada en un dato, y marcadores, que guardan una vista con sus filtros. Stephen Few recomienda lo esencial en una pantalla y el detalle a un clic.

**Diap. 4 · Actualización y ejemplos reales (1:30)**
Hay tres modos de actualizar: una sola carga, para un informe de cierre; programada, que recarga cada cierto tiempo, como ventas diarias; y tiempo real, con flujo continuo, para monitorear brotes. En Streamlit usamos `st.cache_data` con `ttl`: define cuánto vive el dato en caché. Tres ejemplos reales: el mapa de Johns Hopkins sobre COVID-19, lanzado en enero de 2020; Our World in Data, con más de 14 000 gráficos interactivos; y Gapminder Tools, con un gráfico de burbujas de cinco variables. Gapminder es justamente el conjunto de datos de nuestra demo. Le paso la palabra a Hugo.

**Diap. 15 · Referencias (al final, ~0:15)**
Estas son las fuentes que usamos; quedan en el PDF entregado. ¿Preguntas?

---

## HUGO — Aplicación (~5:00)

**Diap. 5 · Demo: la misma data, dos formas (0:45)**
Para la demo usamos Gapminder: 142 países, de 1952 a 2007, 1 704 filas. Las variables son país, continente, año, esperanza de vida, población y PIB per cápita. Construimos dos versiones con Python: una estática, `static.py`, que genera una imagen, y una dinámica, `app.py`, hecha con Streamlit y Plotly.

**Diap. 6 · Demo estática (0:45)**
Esta es la versión estática. Muestra el 2007 y la tendencia por continente. Responde una pregunta fija. Si quiero ver otro continente o años distintos, tengo que volver a programar.

**Diap. 7 · Demo dinámica: qué incluye (0:45)**
La versión dinámica tiene filtros en la barra lateral —continente y rango de años—, tres KPIs, tres pestañas (Overview con burbujas animadas, Comparar con líneas por continente y Detalle con un país y su tabla) y un botón para actualizar datos. Responde preguntas como: ¿el ingreso explica la salud?, ¿qué continente mejoró más?, ¿cómo evolucionó un país concreto?

**Diap. 8 · Cómo se construye (0:45)**
Los pasos son siete: instalar dependencias; cargar los datos con caché; crear los controles en la barra lateral; filtrar el DataFrame con esos valores; dibujar con `px.scatter` animado y `px.line`; organizar con pestañas y métricas; y ejecutar con `streamlit run`. Lo importante: en Streamlit cada interacción vuelve a ejecutar el script de arriba abajo.

**Diap. 9 · Demo en vivo (2:00)** — *cambiar a la ventana de la app y seguir la lista de la diapositiva:*
1. Dejar solo **Asia** y ver cambiar KPIs y gráficos.
2. Rango de años 1952–1972; los KPIs son del último año del rango.
3. Pestaña **Overview**: pulsar ▶ en la animación.
4. Pestaña **Detalle**: elegir Rwanda y ver su tabla.
5. Botón **Actualizar datos**: señalar que cambia la hora de carga.
6. Quitar todos los continentes: aparece «Selecciona al menos un continente».

*Plan B si la app falla:* describir los pasos con la imagen estática y decir que el código está en el repositorio. Le paso a Esteban.

---

## ESTEBAN — Complejidad y participación (~8:00)

**Diap. 10 · Complejidad de implementación (1:00)**
Un estático necesita Python o Excel y un script que genere una imagen. Uno dinámico agrega manejo de estado, eventos y filtrado de DataFrames, además de un servidor donde correr la app. El estático casi no necesita mantenimiento; el dinámico exige cuidar dependencias, versiones y que los datos estén al día. El cambio de fondo es pasar de entregar un resultado a mantener una app que reacciona.

**Diap. 11 · Dificultades que encontramos (1:15)**
Estas dificultades salieron de verdad al construir la demo. Cada interacción re-ejecuta el script, así que hay que cachear. Con el `ttl` el dato puede quedar viejo, por eso agregamos un botón para forzar la recarga. Un parámetro de Streamlit quedó obsoleto y lo migramos. Asumimos que los datos iban de 1998 a 2007 y el rango real es 1952–2007: lo verificamos antes de graficar. Y sin continentes seleccionados no hay datos, así que mostramos un aviso.

**Diap. 12 · ¿Cuándo NO conviene? (1:00)**
No conviene cuando el mensaje es único y ya conocido, cuando el reporte se imprime o se envía en PDF —la interactividad se pierde—, cuando nadie va a mantener la app, cuando hay demasiados filtros y la audiencia se sobrecarga, o cuando el público no tiene tiempo de explorar. Regla práctica: si no hay preguntas de seguimiento, el estático alcanza.

**Diap. 13 · Herramientas (1:00)**
Streamlit permite apps de datos con pocas líneas. Plotly con Dash da más control con callbacks explícitos. Panel enlaza componentes y controles. R Shiny hace lo mismo en R con entradas reactivas. Power BI y Tableau no requieren código y ofrecen segmentadores y drill-through. Más control significa más código; menos código significa menos personalización.

**Diap. 14 · Actividad y discusión (3:45)**
Dividimos la clase en dos grupos. El grupo A solo ve la imagen estática. El grupo B usa la app dinámica. Les leemos las cuatro preguntas; cada grupo anota su respuesta y quién terminó primero.
1. ¿Qué país de las Américas tuvo la menor esperanza de vida en 2007?
2. ¿Qué país de Asia ganó más años de esperanza de vida entre 1952 y 2007?
3. ¿Qué pasó con la esperanza de vida de Rwanda en 1992?
4. ¿Qué periodo mostró la mayor caída de la media en África?

**Clave de respuestas (no mostrar):**
1. Haití, 60.9 años (2007). *El estático puede responderla.*
2. Omán, +38.1 años; le siguen Vietnam (+33.8) e Indonesia (+33.2). *El estático no tiene 1952.*
3. Cayó a 23.6 años, desde 44.0 en 1987. *Pestaña Detalle.*
4. 1997→2002, −0.27 años en la media africana. *Pestaña Comparar.*

Cierre: ¿cuándo bastó el estático? ¿qué filtro faltó? Volviendo a la pregunta guía: no podemos responder con una imagen fija las preguntas que dependen de un filtro, de un periodo distinto o del detalle de un caso. Gracias; quedamos atentos a sus preguntas.

---

## Si preguntan

- **¿Por qué Streamlit?** Pocas líneas, tiene filtros, pestañas y caché de forma nativa, y corre con un solo comando. Dash da más control, pero requiere más código.
- **¿La app actualiza datos en tiempo real?** No. Gapminder es histórico; el botón solo limpia la caché y recarga la carga inicial. Mostramos el mecanismo, no un flujo real.
- **¿Qué pasa con muchos datos?** Habría que cachear, agregar antes de graficar y limitar los filtros.
- **¿Las fuentes de QuantHub/Qrvey son confiables?** Son blogs de proveedores. Las usamos para la comparación general; la base teórica es Shneiderman y la documentación de Microsoft.
