# Laboratorio 6 — Análisis de redes sociales (YouTube)

**Curso:** CC3084 – Data Science · **Semestre II 2026** · Universidad del Valle de Guatemala
**Integrantes:** Ernesto · Esteban · Hugo

Análisis reproducible de participación en YouTube a partir de dos conjuntos de datos
(`youtube_videos.csv` y `youtube_comments.csv`): calidad y limpieza de datos, exploración,
construcción de la red bipartita autor–video y sus proyecciones, topología, comunidades,
centralidad y análisis de sentimiento en español. Cubre las Secciones 1 a 10 del enunciado.

> **Nota sobre la unidad de observación.** Los datos no permiten saber quién respondió a quién:
> `reply_count` cuenta respuestas pero no identifica autores. Por eso **no** se construyen aristas
> usuario→usuario a partir de respuestas. La red modela **co-participación** (autores que comentan
> los mismos videos), no conversación ni amistad.

---

## Estructura del repositorio

```
.
├── data/
│   └── raw/                 youtube_videos.csv, youtube_comments.csv (únicos versionados)
├── src/                     lógica reutilizable, importada por los notebooks
│   ├── carga.py             carga e integración por video_id (Sec. 1)
│   ├── limpieza.py          calidad, normalización de IDs, conteos y texto (Sec. 2)
│   ├── eda.py               tablas y métricas del análisis exploratorio (Sec. 3)
│   ├── red.py               red bipartita y proyecciones autor-autor / video-video (Sec. 4-5)
│   └── sentimiento.py       sentimiento en español con pysentimiento (Sec. 9)
├── notebooks/               un notebook por bloque de secciones, en orden de ejecución
│   ├── 01_carga_limpieza.ipynb      Secciones 1 y 2
│   ├── 02_eda.ipynb                 Sección 3
│   ├── 03_red_bipartita.ipynb       Sección 4
│   ├── 04_proyecciones.ipynb        Sección 5
│   ├── 05_topologia.ipynb           Sección 6
│   ├── 06_comunidades.ipynb         Sección 7
│   ├── 07_centralidad.ipynb         Sección 8
│   ├── 08_sentimiento.ipynb         Sección 9
│   └── 09_interpretacion.ipynb      Sección 10 (integración y conclusiones)
├── outputs/
│   ├── tablas/              CSV/GraphML de resultados (versionados)
│   └── figuras/             PNG de todas las visualizaciones (versionados)
├── requirements.txt
└── README.md
```

`data/processed/`, `data/preprocessing/` y `data/cleaned/` **no** se versionan: son intermedios
que regenera el notebook 01. Solo se versionan los dos CSV originales en `data/raw/`.

## Requisitos

- **Python 3.12**
- Dependencias en [`requirements.txt`](requirements.txt). Las principales:
  `pandas`, `numpy`, `matplotlib`, `seaborn`, `networkx`, `scipy`, `python-louvain`,
  `nltk`, `spacy` (+ modelo `es_core_news_sm`), `wordcloud`, `emoji`, y
  `pysentimiento` para el sentimiento en español (Sección 9; instala `torch` y
  `transformers`, ~2 GB).

## Instalación

```bash
python -m venv venv
source venv/bin/activate           # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download es_core_news_sm
python -c "import nltk; nltk.download('stopwords')"
```

## Cómo ejecutar el análisis

Los notebooks se ejecutan **en orden** (01 → 09). El notebook 01 regenera `data/processed/`,
del que dependen todos los demás.

```bash
jupyter lab            # o: jupyter notebook
```

Alternativa no interactiva (ejecuta y guarda cada notebook con sus salidas):

```bash
for nb in notebooks/0*.ipynb; do
  jupyter nbconvert --to notebook --execute --inplace "$nb"
done
```

Cada módulo de `src/` incluye un self-check con los números verificados; se corre solo:

```bash
python src/red.py          # imprime "red.py: self-check OK" con nodos/aristas
python src/sentimiento.py  # etiqueta los comentarios y cachea la salida
```

## Reproducibilidad del sentimiento

`notebooks/08_sentimiento.ipynb` ejecuta el modelo `robertuito-sentiment-analysis` una sola vez
y **cachea** el resultado en `outputs/tablas/sentimiento_comentarios.csv`. Si esa tabla existe,
el análisis la reutiliza y no necesita volver a descargar ni correr el modelo (útil sin GPU o
sin conexión). Para forzar el recálculo, borra ese archivo o llama
`sentimiento.analizar_comentarios(comments, usar_cache=False)`.

## Resultados

- `outputs/tablas/` — nodos y aristas de la red, proyecciones (`.graphml`), métricas de
  topología, comunidades, centralidad y sentimiento (por comentario, video, canal y comunidad).
- `outputs/figuras/` — todas las visualizaciones del informe (EDA, red, comunidades,
  centralidad y sentimiento).

## Alcance y limitaciones

Los resultados **describen** la muestra recolectada; no se generalizan a todo YouTube ni a
Guatemala. Las principales limitaciones —cobertura parcial de comentarios, selección por
consultas de búsqueda, fechas relativas, ausencia de relaciones explícitas entre autores y
concentración de la participación en pocos videos— se discuten en
[`notebooks/09_interpretacion.ipynb`](notebooks/09_interpretacion.ipynb) (Sección 10).
