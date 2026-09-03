# Laboratorio 6 — Análisis de redes sociales (YouTube) · CC3084

**Trabajo secuencial: una persona a la vez.** Cada etapa produce un archivo que la siguiente persona recibe
como insumo. Nadie empieza su etapa hasta que la anterior hizo `push` y avisó.

La nota es **individual según la contribución de cada quien** → cada persona hace **sus propios commits con su
propio usuario de git**.

## Integrantes

| Clave | Nombre |
|---|---|
| **P1** | **Ernesto** |
| **P2** | **Esteban** |
| **P3** | **Hugo** |

## Fechas

| Entrega | Límite | Alcance |
|---|---|---|
| **AVANCE** | **jueves 3 de septiembre de 2026 (HOY)** | Secciones 1 a 4 = **Etapas 1, 2, 3 y 4** |
| **Documento final** | **domingo 6 de septiembre de 2026, 23:59** | Etapas 1 a 10 + material a entregar |

> Sin avance a tiempo **no se califica** esa parte. Hoy hay que cerrar Etapas 1→2→3→4 en cadena
> (Ernesto hace 1 y 2, luego Esteban la 3, luego Hugo la 4). Si al final del día Ernesto va apurado: que
> entregue IDs + conteos limpios y el diagnóstico (2.1–2.4), marque el resto de la Sec. 2 como pendiente, y
> Esteban arranca. La limpieza de texto (2.5–2.7) se termina el viernes sin frenar la cadena.

## Orden de las etapas y rotación

| Etapa | Persona | Sección | Notebook | Pts rúbrica |
|---|---|---|---|---|
| **1** | **Ernesto** | 1 (carga e integración — ligera) | `01_carga_limpieza.ipynb` | — |
| **2** | **Ernesto** | 2 (calidad y limpieza) | `01_carga_limpieza.ipynb` | 18 |
| **3** | **Esteban** | 3 (análisis exploratorio) | `02_eda.ipynb` | 18 |
| **4** | **Hugo** | 4 (red bipartita) | `03_red_bipartita.ipynb` + `src/red.py` | 10 |
| **5** | **Ernesto** | 5 (proyecciones) | `04_proyecciones.ipynb` | 8 |
| **6** | **Esteban** | 6 (topología y fragmentación) | `05_topologia.ipynb` | 12 |
| **7** | **Hugo** | 7 (comunidades) | `06_comunidades.ipynb` | 10 |
| **8** | **Ernesto** | 8 (nodos centrales y puente) | `07_centralidad.ipynb` | 7 |
| **9** | **Esteban** | 9 (contenido y sentimiento) | `08_sentimiento.ipynb` | 5 |
| **10** | **Hugo** | 10 (interpretación y conclusiones) | sección del informe + montaje final | 12 |

**Total por persona:** Ernesto = 33 · Esteban = 35 · Hugo = 32 · (Sec. 1 no tiene puntos propios).

## Cadena de entregas (qué recibe y qué entrega cada etapa)

```
Etapa 1  Ernesto  raw/*.csv                 →  datos integrados por video_id (en el notebook)
Etapa 2  Ernesto  datos integrados          →  data/processed/comments_clean.csv, videos_clean.csv
Etapa 3  Esteban  *_clean.csv               →  outputs/figuras/eda_*, tabla de frecuencias, hallazgos EDA
Etapa 4  Hugo     comments_clean.csv        →  src/red.py (3 funciones), outputs/tablas/nodos.csv, aristas.csv
Etapa 5  Ernesto  src/red.py                →  proyección autor-autor y video-video (objetos + figuras)
Etapa 6  Esteban  red.py + proyecciones     →  métricas de topología (tabla), figuras de fragmentación
Etapa 7  Hugo     proyección autor-autor    →  particion de comunidades (dict nodo→com), modularidad, figuras
Etapa 8  Ernesto  red.py + proyecciones     →  tabla de centralidad autores y videos, nodos puente
Etapa 9  Esteban  comments_clean.csv        →  score de sentimiento por comentario (columna en un csv)
Etapa 10 Hugo     TODO lo anterior          →  informe/Laboratorio6_Grupo.pdf + README + repo ordenado
```

Regla: lo reutilizable va a `src/`, no se copia entre notebooks. Nadie edita el notebook de otra persona.

---

## Estructura del repo

```
notebooks/  01_carga_limpieza  02_eda  03_red_bipartita  04_proyecciones
            05_topologia  06_comunidades  07_centralidad  08_sentimiento
src/        carga.py  limpieza.py  red.py  viz.py
data/       raw/ (CSV originales)   processed/ (salida Etapa 2, NO se versiona → regenerar con nb 01)
outputs/    figuras/   tablas/
informe/    Laboratorio6_Grupo.pdf
README.md   requirements.txt
```

---

## ETAPA 1 — Ernesto · Carga, comprensión e integración (Sec. 1)

**Recibe:** `data/raw/youtube_videos.csv`, `data/raw/youtube_comments.csv`
**Notebook:** `01_carga_limpieza.ipynb` · **Módulo:** `src/carga.py`

- [x] **1.1** Cargar ambos CSV con pandas.
- [x] **1.2** Markdown: unidad de observación de cada archivo, llave primaria (`video_id` / `comment_id`),
      variables relevantes vs. descartables.
- [x] **1.3** Explicar la relación canal → video → autor del comentario → comentario → categoría → consulta de
      búsqueda. Aclarar: el autor del comentario ≠ dueño del canal del video.
- [x] **1.4** Integrar por `video_id`. Reportar cuántos comentarios se asociaron a un video (esperado
      **406/406 = 100 %**) y cuántos videos quedan sin comentarios (**274**).

**Entrega:** el notebook con la carga y el `merge` hecho. Seguir de una con la Etapa 2 (misma persona).

---

## ETAPA 2 — Ernesto · Calidad, limpieza y preprocesamiento (Sec. 2, 18 pts)

**Recibe:** los datos integrados de la Etapa 1 · **Notebook:** `01_carga_limpieza.ipynb` · **Módulo:** `src/limpieza.py`

- [x] **2.1** (4 pts) Diagnóstico de calidad: dimensiones, tipos, faltantes por columna, duplicados,
      **constantes** (`is_pinned`), **vacías** (`viewer_rating`), atípicos, consistencia IDs/nombres/handles.
      Hallazgo extra: 36/406 `comment_id` con `.` son respuestas, no comentarios raíz (se conservan y documenta).
- [x] **2.2** (2 pts) Variables de uso delicado + tratamiento: `published_time`/`published_text` (relativas),
      `view_count_text` (display), `source_query` (muestreo, no tema), listas en texto
      (`dataset_sources`, `query_hits`, `keywords`).
- [x] **2.3** (2 pts) Normalizar IDs y nombres **sin sustituir ID por nombre visible**. IDs canónicos:
      `channel_id`, `video_id`, `comment_id`, `author_channel_id` (a string, `strip`). Handles: quita `/@`,
      decodifica `%XX`, minúsculas (solo presentación). Elimina `viewer_rating`, `is_pinned`, `video_title`,
      `upload_date`, `owner_handle`.
- [x] **2.4** (3 pts) `like_count_text` → `like_count` (`Int64`, 189 `' '` → `<NA>`); `view_count_text` →
      `view_count_text_num` y cotejado con `view_count`. Parser general (miles, coma decimal, `K`/`M`/`mil`).
      `keywords`/`query_hits`/`dataset_sources` → listas (`*_list`).
- [x] **2.5** (3 pts) `texto_original` (intacto, para auditoría/sentimiento) y `texto_limpio`.
- [x] **2.6** (2 pts) 9 pasos de `texto_limpio` documentados en tabla: minúsculas, URLs, separar
      menciones/hashtags, emojis (a columna aparte), números/puntuación, stopwords NLTK-es (313),
      lematización spaCy `es_core_news_sm`, filtro ≥3 letras.
- [x] **2.7** (2 pts) `efecto_limpieza()`: 0 filas eliminadas; long. media 139→86 car.; 6/406 quedan con
      `texto_limpio` vacío (marcadas con `texto_limpio_vacio`).

**Entrega:** `data/processed/comments_clean.csv` (406×23) y `videos_clean.csv` (293×23) con IDs normalizados,
`like_count` numérico, listas parseadas y `texto_original`/`texto_limpio`. `push` + avisar a **Esteban**.
Deps nuevas: `spacy` + modelo `es_core_news_sm`, `nltk` stopwords (ver README).

---

## ETAPA 3 — Esteban · Análisis exploratorio (Sec. 3, 18 pts)

**Recibe:** `data/processed/*_clean.csv` · **Notebook:** `02_eda.ipynb`

- [x] **3.1** (6 pts) Reportado: 293 videos / 97 canales / 406 comentarios / 332 autores; videos por canal
      (mediana 1, máx 32); comentarios y autores por video (19 con actividad, mediana 7, máx 161);
      `view_count`; respuestas (51, solo 7.4 % de comentarios); likes (189 nulos = ' '); categorías;
      consultas; hashtags (1 en comentarios, 104 videos con hashtag en descripción); palabras y bigramas.
- [x] **3.2** (3 pts) Concentración con top-N + Lorenz + Gini. **Confirmado:** 1 video = 39.7 %,
      4 = 69.2 %, 5 = 75.4 % (Gini 0.66). Canales: Quorum 63.1 %, con Gobierno 80.3 %.
      Contraste clave: autores casi uniformes (Gini 0.16).
- [x] **3.3** (2 pts) Spearman 0.811 y Pearson log-log 0.718 sobre los 19; 0.08 sobre los 293.
      Relación sublineal (13.7 vs 0.08 comentarios por mil vistas). Limitaciones documentadas.
- [x] **3.4** (3 pts) 15 figuras `outputs/figuras/eda_*.png`, cada una con su lectura en markdown.
      Nube de palabras incluida como complemento.
- [x] **3.5** (2 pts) Las 6 preguntas respondidas con evidencia. Comunidades/sentimiento marcados como
      preliminares (proxy por canal y por emoji) → se cierran en Etapas 7 y 9.
- [x] **3.6** (2 pts) 4 preguntas propias: sesgo de la estrategia de búsqueda (105 videos `official_gov`
      con 0 comentarios), antigüedad de los comentarios (71.7 % ≥ 1 año, ventanas de horas a 7 años),
      vocabulario por tipo de emisor, y rasgos superficiales vs. likes (correlación nula).

**Entregado:** `notebooks/02_eda.ipynb` corrido · `src/eda.py` (módulo reutilizable con self-check) ·
15 figuras en `outputs/figuras/eda_*.png` · 10 tablas en `outputs/tablas/eda_*.csv`.

**Insumos que la Etapa 4 puede reutilizar:** `eda.cargar_procesados()`, `outputs/tablas/eda_por_video.csv`
(atributos de video para la tabla de nodos) y `eda_autores_puente.csv` (los 9 autores multi-video).
**Predicción verificable para Hugo/Ernesto:** la proyección video–video tendrá **11 aristas** de 171
posibles y peso máximo 2 (ver `eda_pares_videos_compartidos.csv`).

---

## ETAPA 4 — Hugo · Red bipartita autor–video (Sec. 4, 10 pts) — CIERRA EL AVANCE

**Recibe:** `data/processed/comments_clean.csv` · **Notebook:** `03_red_bipartita.ipynb` · **Módulo:** `src/red.py`

- [ ] **4.1** (2 pts) `build_bipartita(comments)`: red **no dirigida**, nodos autor (`author_channel_id`) y
      nodos video (`video_id`), atributo `bipartite` 0/1.
- [ ] **4.2** (2 pts) Arista autor–video si el autor comentó ese video; **peso = nº de comentarios** del
      autor en ese video (hay 40 pares con peso > 1).
- [ ] **4.3** (3 pts) Exportar `outputs/tablas/nodos.csv` (id, tipo, atributos: autores → nº comentarios/handle;
      videos → título/canal/categoría/`view_count`) y `outputs/tablas/aristas.csv` (source, target, weight).
- [ ] **4.4** (2 pts) Visualizar la red **completa** (layout bipartito o spring). No borrar aislados por
      estética — la fragmentación es resultado.
- [ ] **4.5** (1 pt) Explicar qué significa una arista: co-participación observada en un video. **No** es
      amistad, conversación ni aprobación.

**Entrega — contrato clave:** `src/red.py` con 3 funciones puras:
```python
build_bipartita(comments_df) -> nx.Graph
proj_autores(B) -> nx.Graph   # peso = nº videos compartidos
proj_videos(B)  -> nx.Graph   # peso = nº autores compartidos
```
+ `nodos.csv` y `aristas.csv`. `push` + avisar a **Ernesto**.
**→ Aquí se entrega el AVANCE (Sec. 1–4). Hacer el merge/entrega antes de la hora límite de hoy.**

---

## ETAPA 5 — Ernesto · Proyecciones de la red (Sec. 5, 8 pts)

**Recibe:** `src/red.py` · **Notebook:** `04_proyecciones.ipynb`

- [ ] **5.1** (3 pts) Proyección **autor–autor** vía `red.proj_autores(B)`: conectados si comentaron el mismo
      video; peso = nº videos compartidos.
- [ ] **5.2** (3 pts) Proyección **video–video** vía `red.proj_videos(B)`: conectados si comparten ≥ 1 autor;
      peso = nº autores compartidos. Esperado: **11 aristas** (de 171 posibles).
- [ ] **5.3** (1 pt) Comparar ambas: co-audiencia de autores vs. solapamiento de público entre videos.
- [ ] **5.4** (1 pt) Visualizar ambas (grosor de arista = peso).

**Entrega:** notebook + figuras. Si guardas los grafos, `outputs/tablas/proj_autores.graphml` y
`proj_videos.graphml`. `push` + avisar a **Esteban**.

---

## ETAPA 6 — Esteban · Topología y fragmentación (Sec. 6, 12 pts)

**Recibe:** `src/red.py` + proyecciones (Etapa 5) · **Notebook:** `05_topologia.ipynb`

- [ ] **6.1** (5 pts) Para bipartita y proyecciones: nº nodos y aristas, densidad, grado medio, **distribución
      de grados**, componentes conexos, **tamaño de la componente mayor**. Esperado video–video: ~11 aristas,
      varias componentes, muchos videos aislados.
- [ ] **6.2** Cohesión y transitividad. En la bipartita la transitividad es 0 por definición → calcularla
      sobre las proyecciones y explicarlo.
- [ ] **6.3** Autores/videos periféricos y aislados. **Distinguir aislamiento observado** (el autor solo
      comentó 1 video de la muestra) **de ausencia de datos** (no recolectamos sus otros comentarios).
- [ ] **6.4** (7 pts, interpretación) Explicar los hallazgos apoyándose en los gráficos: la red está
      fragmentada porque el muestreo tomó comentarios de pocos videos y casi ningún autor cruza entre ellos.

**Entrega:** tabla de métricas en `outputs/tablas/topologia.csv` + figuras. `push` + avisar a **Hugo**.

---

## ETAPA 7 — Hugo · Comunidades (Sec. 7, 10 pts)

**Recibe:** proyección autor–autor (Etapa 5) + métricas (Etapa 6) · **Notebook:** `06_comunidades.ipynb`

- [ ] **7.1** (2 pts) Elegir la red y justificar (recomendado: **proyección autor–autor pesada**; la bipartita
      cruda y la video–video casi no tienen aristas).
- [ ] **7.2** (3 pts) Aplicar **Louvain** (o Leiden) — `networkx.community` / `python-louvain` / `igraph`.
      Explicar supuestos y **tratamiento de pesos** (weight = videos compartidos). Mencionar que hay métodos
      específicos para bipartito y por qué se usó la proyección.
- [ ] **7.3** (2 pts) Reportar nº de comunidades, tamaños y **modularidad**.
- [ ] **7.4** (1 pt) Visualizar **todas** las comunidades; analizar hasta 3 principales. Si salen < 3,
      justificar (fragmentación).
- [ ] **7.5** (2 pts) Caracterizar cada comunidad: videos, canales, autores, intensidad de participación,
      temas frecuentes (`texto_limpio`). **El sentimiento por comunidad se completa tras la Etapa 9** — deja
      todo lo demás cerrado y Esteban te pasa el score por comentario; añades esa fila y listo.

**Entrega:** `outputs/tablas/comunidades.csv` (nodo → comunidad) + figuras. `push` + avisar a **Ernesto**.

---

## ETAPA 8 — Ernesto · Nodos centrales y participantes puente (Sec. 8, 7 pts)

**Recibe:** `src/red.py` + proyecciones · **Notebook:** `07_centralidad.ipynb`

- [ ] **8.1** (3 pts) Centralidades apropiadas (grado, intermediación, cercanía; opcional PageRank /
      eigenvector) sobre bipartita y/o proyecciones. Justificar. Nota: con red fragmentada la intermediación
      global es ~0 salvo en los 9 autores puente — decirlo.
- [ ] **8.2** (2 pts) Interpretar **por separado**: autores (recurrencia, diversidad de participación) y
      videos (alcance dentro de la red, capacidad de conectar audiencias).
- [ ] **8.3** (2 pts) Participantes recurrentes, autores puente y videos articuladores (si se eliminan, ¿la
      red se segmenta?). Candidatos: los 9 autores multi-video.

**Entrega:** `outputs/tablas/centralidad_autores.csv`, `centralidad_videos.csv`. `push` + avisar a **Esteban**.

---

## ETAPA 9 — Esteban · Análisis de contenido y sentimiento (Sec. 9, 5 pts)

**Recibe:** `data/processed/comments_clean.csv` · **Notebook:** `08_sentimiento.ipynb`

- [ ] **9.1** (2 pts) Sentimiento sobre `texto_original` con herramienta **para español**: `pysentimiento`
      (`robertuito-sentiment`) o léxico es. Justificar (VADER es inglés — no sin justificar). Explicar la
      distribución pos/neg/neu.
- [ ] **9.2** (1 pt) Comparar sentimiento por video / canal / tema / comunidad **cuando la muestra lo
      permita** (con n muy desigual, sólo tiene sentido para los 4–5 videos con más comentarios — decirlo).
- [ ] **9.3** (2 pts) Explicar hallazgos, con la limitación del tamaño muestral y el sesgo de selección.

**Entrega:** `outputs/tablas/sentimiento.csv` (`comment_id`, `sentiment_label`, `sentiment_score`).
Pasar esa tabla a **Hugo** para cerrar 7.5, y avisar a **Hugo** para arrancar Etapa 10.

---

## ETAPA 10 — Hugo · Interpretación, limitaciones, conclusiones + montaje (Sec. 10, 12 pts)

**Recibe:** todos los notebooks y tablas · Cierra 7.5 con la tabla de sentimiento de la Etapa 9.

- [ ] **10.1** (3 pts) Interpretar los hallazgos en el contexto de participación y consumo en YouTube.
- [ ] **10.2** (4 pts) Discutir mínimo estas limitaciones: cobertura de comentarios (solo 19 videos),
      selección por consultas, fechas relativas, conteos al momento de recolección, **ausencia de relaciones
      explícitas entre autores** (no sabemos quién respondió a quién), concentración en pocos videos.
- [ ] **10.3** (2 pts) Distinguir **descripción vs. asociación vs. inferencia**. No generalizar a todo YouTube
      ni a Guatemala.
- [ ] **10.4** (3 pts) Conclusiones que **integren** redes + contenido + sentimiento + limitaciones.

### Montaje final (todo el grupo revisa, Hugo ejecuta)
- [ ] Ensamblar `informe/Laboratorio6_Grupo.pdf` con resultados, visualizaciones, interpretación y
      conclusiones de las 10 secciones.
- [ ] Escribir `README.md`: cómo ejecutar (orden de notebooks 01→08), dependencias, cómo regenerar
      `data/processed/`, enlace al repo y al espacio colaborativo del grupo.
- [ ] `requirements.txt` (`pip freeze` filtrado: pandas, networkx, python-louvain, matplotlib, nltk,
      pysentimiento, wordcloud…).
- [ ] Ordenar el repo (ver "Higiene" abajo).

---

## Trampas de los datos (ya verificadas — NO redescubrir ni reportar mal)

- **Solo 19 de 293 videos tienen comentarios.** 406 comentarios, **332 autores únicos**.
- 100 % de comentarios hace match con un `video_id` → la integración (1.4) no pierde filas.
- Participación **muy concentrada**: 1 video = 161 comentarios (≈ 40 %); 4 videos ≈ 69 %; 5 videos ≈ 75 %.
- **Solo 9 autores comentan en más de un video** →
  - Proyección **video–video: 11 aristas de 171** → red casi desconectada.
  - Bipartita fragmentada en ~11+ componentes; las "comunidades" ≈ 1 por video.
  - **Es el hallazgo principal**, no un error. Interpretarlo como efecto del muestreo (lo pide la Sec. 10.2).
- 40 pares (autor, video) con > 1 comentario → **pesos > 1** en la bipartita.
- `like_count_text` trae `' '` (espacios) como faltante → limpiar antes de convertir a int.
- `is_pinned` constante (`False`) → sin varianza. `viewer_rating` **100 % vacía** → inusable (2.1).
- `published_time` / `published_text` son **relativos** ("hace 2 días") → NO son fecha. En videos hay
  `publish_date` en ISO 8601.
- `view_count_text` es display ("2,390 vistas") → usar `view_count`.
- **`reply_count` NO es una arista entre usuarios.** El enunciado lo dice: no identifica quién respondió a
  quién. No construir aristas autor→autor con respuestas.
- `channel_id` (dueño del video) ≠ `author_channel_id` (autor del comentario).
- `channel_name`, `author_name`, `*_handle` se repiten o cambian → usar siempre los `*_id`.

---

## Material a entregar (PDF pág. 7 — responsable Hugo en Etapa 10)

- [ ] **Informe PDF** con resultados, visualizaciones, interpretación y conclusiones.
- [ ] **Script reproducible** (los 8 notebooks + `src/`).
- [ ] **Enlace al espacio colaborativo del grupo.**
- [ ] **Enlace al repositorio.**
- [ ] **README** con instrucciones de ejecución + dependencias, y `requirements.txt`.

---

## Flujo de git (secuencial)

- Una sola rama de trabajo: **`lab6`**. Antes de tu etapa: `git pull`. Al terminar: `git commit` (con **tu**
  usuario) + `git push` + avisar por el chat del grupo a la siguiente persona.
- No commitear `data/` (está en `.gitignore`) ni `.venv/`. Los CSV originales van a `data/raw/` local; el
  README dice de dónde bajarlos. Los procesados se regeneran corriendo `notebooks/01_carga_limpieza.ipynb`.
- Merge del AVANCE (Etapas 1–4) a `main` hoy antes de la hora límite.

### Higiene pendiente (Ernesto al empezar la Etapa 1, o Hugo en el montaje)

- [ ] Añadir `.DS_Store` al `.gitignore`.
- [ ] Borrar `src/__pycache__/` (de otro lab). Confirmar si `data/raw/train.csv`, `data/preprocessing/*`,
      `data/cleaned/*` son de otro laboratorio → mover fuera del repo o borrar.
- [ ] Reescribir `README.md` (hoy solo tiene el título).
- [ ] Crear `notebooks/`, `data/raw/`, `data/processed/`, `outputs/figuras/`, `outputs/tablas/`, `informe/`.
- [ ] Mover `youtube_videos.csv` y `youtube_comments.csv` a `data/raw/`.
```
