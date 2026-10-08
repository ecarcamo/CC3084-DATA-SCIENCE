"""Dashboard dinámico (Streamlit) sobre Gapminder. Ejecutar: streamlit run app.py"""
from datetime import datetime

import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Gapminder dinámico", layout="wide")


@st.cache_data(ttl=300)  # el dato vive 5 min en caché; luego se recarga solo
def cargar():
    return px.data.gapminder(), datetime.now().strftime("%H:%M:%S")


df, cargado_a = cargar()

# ---- Controles (sidebar): cada cambio vuelve a ejecutar el script ----
st.sidebar.header("Filtros")
continentes = st.sidebar.multiselect(
    "Continente", sorted(df.continent.unique()), default=sorted(df.continent.unique())
)
anio_min, anio_max = int(df.year.min()), int(df.year.max())
rango = st.sidebar.slider("Rango de años", anio_min, anio_max, (anio_min, anio_max), step=5)
if st.sidebar.button("Actualizar datos"):
    st.cache_data.clear()  # fuerza recarga; la hora de carga cambia
    st.rerun()
st.sidebar.caption(f"Datos cargados a las {cargado_a}")

filtrado = df[df.continent.isin(continentes) & df.year.between(*rango)]
if filtrado.empty:
    st.warning("Selecciona al menos un continente.")
    st.stop()

st.title("Esperanza de vida, ingreso y población (1952–2007)")

# ---- KPIs del último año del rango ----
ult = filtrado[filtrado.year == filtrado.year.max()]
k1, k2, k3 = st.columns(3)
k1.metric(f"Esperanza de vida media ({rango[1]})", f"{ult.lifeExp.mean():.1f} años")
k2.metric("PIB per cápita mediano", f"${ult.gdpPercap.median():,.0f}")
k3.metric("Países", ult.country.nunique())

tab1, tab2, tab3 = st.tabs(["Overview", "Comparar", "Detalle"])

with tab1:
    st.caption("¿Cómo cambia la relación ingreso–salud con el tiempo? Pulsa ▶ en el gráfico.")
    fig = px.scatter(
        filtrado, x="gdpPercap", y="lifeExp", size="pop", color="continent",
        hover_name="country", animation_frame="year", log_x=True, size_max=55,
        range_y=[25, 90], labels={"gdpPercap": "PIB per cápita (log)", "lifeExp": "Esperanza de vida"},
    )
    st.plotly_chart(fig, width="stretch")

with tab2:
    st.caption("¿Qué continente mejoró más? Compara medias por continente.")
    media = filtrado.groupby(["year", "continent"], as_index=False).lifeExp.mean()
    st.plotly_chart(
        px.line(media, x="year", y="lifeExp", color="continent", markers=True,
                labels={"lifeExp": "Esperanza de vida media"}),
        width="stretch",
    )

with tab3:
    st.caption("Detalle bajo demanda: elige un país.")
    pais = st.selectbox("País", sorted(filtrado.country.unique()))
    det = filtrado[filtrado.country == pais]
    st.plotly_chart(px.line(det, x="year", y="lifeExp", markers=True, title=pais), width="stretch")
    st.dataframe(det[["year", "lifeExp", "pop", "gdpPercap"]], hide_index=True)
