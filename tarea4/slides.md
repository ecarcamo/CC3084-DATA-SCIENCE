---
marp: true
theme: default
paginate: true
size: 16:9
footer: 'CC3084 Data Science · Tarea 4 · Grupo 3 · Dashboards dinámicos'
style: |
  :root { --verde: #1b5e20; --verde-claro: #e8f5e9; --acento: #43a047; }
  section { font-family: 'Helvetica Neue', Arial, sans-serif; background: #fff; color: #1f2933; font-size: 26px; }
  section h1 { color: var(--verde); border-bottom: 4px solid var(--acento); padding-bottom: 6px; }
  section h2 { color: var(--verde); }
  section::after { color: var(--verde); font-weight: 700; }
  footer { color: #6b7280; font-size: 14px; }
  section.portada { background: var(--verde); color: #fff; justify-content: center; }
  section.portada h1, section.portada h2 { color: #fff; border: none; }
  section.portada footer, section.portada::after { color: #c8e6c9; }
  table { font-size: 22px; }
  th { background: var(--verde); color: #fff; }
  tr:nth-child(even) td { background: var(--verde-claro); }
  blockquote { border-left: 6px solid var(--acento); background: var(--verde-claro); padding: 4px 18px; }
  .kpi { display: flex; gap: 16px; }
  .kpi div { flex: 1; background: var(--verde-claro); border-radius: 10px; padding: 8px 14px; text-align: center; }
  .small { font-size: 18px; color: #4b5563; }
---

<!-- _class: portada -->
<!-- _paginate: false -->

# Dashboards dinámicos

## Filtros, navegación y actualización de datos

**Grupo 3** · CC3084 Data Science · Universidad del Valle de Guatemala

Ernesto Ascencio (23009) · Hugo Barillas (23556) · Esteban Carcamo (23016)

---

# Agenda (15–20 min)

1. **Investigación** — qué es un dashboard dinámico y qué aporta *(Ernesto)*
2. **Aplicación** — demo en Streamlit con Gapminder *(Hugo)*
3. **Complejidad** — qué se necesita y cuándo no vale la pena *(Esteban)*
4. **Participación** — actividad: dashboard estático vs. dinámico *(Esteban)*

> Pregunta guía: ¿qué preguntas **no** podemos responder con una imagen fija?

---

<!-- ============ INVESTIGACIÓN · Ernesto ============ -->

# Estático vs. dinámico

| | Estático | Dinámico |
|---|---|---|
| Vista | Fija, ya agregada | El usuario la modifica |
| Rol | **Presenta** respuestas | Ayuda a **descubrir** respuestas |
| Datos | Corte en el tiempo | Pueden actualizarse |
| Costo | Menor desarrollo | Mayor desarrollo y mantenimiento |
| Límite | No permite preguntas de seguimiento | Requiere cierta pericia del usuario |

<span class="small">Fuentes: QuantHub; insightsoftware; Qrvey (ver referencias).</span>

---

# Qué aporta la interactividad

- **Filtros / segmentadores:** acotar por categoría, región o periodo.
- **Navegación:** pestañas, páginas y *drill-through* hacia el detalle.
- **Resaltado cruzado:** seleccionar en un gráfico actualiza los demás.
- **Actualización:** los indicadores reflejan datos recientes.

> Cambia la exploración: de **leer** un resultado a **hacer preguntas** a los datos.

---

# Base teórica: el mantra de Shneiderman

> **Overview first, zoom and filter, then details-on-demand.**
> — Shneiderman (1996)

| Paso | En un dashboard |
|---|---|
| Overview | KPIs y vista global |
| Zoom + filter | Segmentadores, rangos de fecha |
| Details-on-demand | Tooltip, drill-through, tabla |

Siete tareas: overview, zoom, filter, details-on-demand, relate, history, extract.

---

# Filtros y resaltado cruzado

Ejemplo en Power BI (Microsoft Learn): clic en **2023** en un gráfico de ventas por año.

- **Cross-filtering:** las otras visuales **quitan** los datos que no aplican.
- **Cross-highlighting:** las otras visuales **atenúan** lo que no aplica y mantienen el total.

El diseñador del reporte decide qué visuales interactúan entre sí.

---

# Navegación

- **Pestañas / páginas:** separar resumen, comparación y detalle.
- **Drill-through:** clic derecho en un punto → página enfocada en ese dato.
- **Marcadores (bookmarks):** guardan una vista con sus filtros y estado.

Regla de diseño (Few, 2006): una pantalla, lo esencial a la vista; el detalle, a un clic.

---

# Actualización de datos

| Modo | Idea | Cuándo |
|---|---|---|
| Estático | Una sola carga | Informe de cierre |
| Programada | Recarga cada N min/horas | Ventas diarias |
| Tiempo real | Flujo continuo | Monitoreo de brotes, operaciones |

En Streamlit: `st.cache_data(ttl=...)` define cuánto vive el dato en caché; al vencer, se recarga.

---

# Dashboards dinámicos reales

- **Johns Hopkins COVID-19** (Dong, Du & Gardner, 2020): mapa en tiempo real, lanzado el 22-ene-2020.
- **Our World in Data:** más de 14 000 gráficos interactivos, reutilizables bajo licencia Creative Commons.
- **Gapminder Tools:** gráfico de burbujas con 5 variables (ejes, tamaño, color, tiempo).

Gapminder es el mismo conjunto de datos que usaremos en la demo.

---

<!-- ============ APLICACIÓN · Hugo ============ -->

# Demo: la misma data, dos formas

**Datos:** Gapminder (`px.data.gapminder()`): 142 países, 1952–2007, 1 704 filas.
Variables: `country, continent, year, lifeExp, pop, gdpPercap`.

**Herramienta:** Streamlit + Plotly (Python).

| Versión | Archivo | Qué ofrece |
|---|---|---|
| Estática | `demo/static.py` | Imagen fija: 2007 + tendencia |
| Dinámica | `demo/app.py` | Filtros, pestañas, animación, detalle |

---

# Demo estática: lo que se ve

![w:900](img/dashboard_estatico.png)

Responde **una** pregunta fija. Para otro continente o años distintos hay que volver a programar.

---

# Demo dinámica: qué incluye

- **Filtros (sidebar):** continente (multiselección) y rango de años.
- **KPIs:** esperanza de vida media, PIB mediano, número de países.
- **Pestañas:** *Overview* (burbujas animadas) · *Comparar* (líneas por continente) · *Detalle* (país elegido + tabla).
- **Botón «Actualizar datos»:** limpia la caché y recarga.

Preguntas que responde: ¿el ingreso explica la salud? ¿qué continente mejoró más? ¿cómo evolucionó un país concreto?

---

# Cómo se construye (pasos)

1. `pip install -r demo/requirements.txt`
2. Cargar datos con `@st.cache_data(ttl=300)`.
3. Crear controles: `st.sidebar.multiselect`, `st.sidebar.slider`.
4. Filtrar el `DataFrame` con esos valores.
5. Dibujar con `px.scatter(animation_frame="year")` y `px.line`.
6. Organizar con `st.tabs` y `st.metric`.
7. Ejecutar: `streamlit run demo/app.py`

Flujo de Streamlit: **cada interacción vuelve a ejecutar el script** de arriba abajo.

---

<!-- ============ COMPLEJIDAD Y PARTICIPACIÓN · Esteban ============ -->
<!-- TODO Esteban: slides de complejidad, cuándo no usar dinámico, herramientas y actividad de clase -->

---

# Referencias

<div class="small">

- Dong, E., Du, H., & Gardner, L. (2020). An interactive web-based dashboard to track COVID-19 in real time. *The Lancet Infectious Diseases, 20*(5), 533–534. https://pubmed.ncbi.nlm.nih.gov/32087114/
- Few, S. (2006). *Information Dashboard Design: The Effective Visual Communication of Data*. O'Reilly Media.
- Shneiderman, B. (1996). The eyes have it: A task by data type taxonomy for information visualizations. *IEEE Symposium on Visual Languages*. https://drum.lib.umd.edu/handle/1903/5784
- Microsoft. (s. f.). Interacciones del usuario final en informes de Power BI. https://learn.microsoft.com/en-us/power-bi/explore-reports/end-user-interactions
- Microsoft. (s. f.). Drillthrough en Power BI Desktop. https://learn.microsoft.com/en-us/power-bi/create-reports/desktop-drillthrough
- Streamlit. (s. f.). `st.cache_data`. https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data
- QuantHub. (s. f.). What is the difference between a static dashboard and an interactive dashboard? https://quanthub.com/what-is-the-difference-between-a-static-dashboard-and-an-interactive-dashboard
- insightsoftware. (s. f.). Dynamic dashboards. https://www.insightsoftware.com/encyclopedia/dynamic-dashboards
- Our World in Data. https://ourworldindata.org/
- Gapminder. Gapminder Tools. https://www.gapminder.org/tools
- Johns Hopkins University. COVID-19 Map FAQ. https://coronavirus.jhu.edu/map-faq

</div>
