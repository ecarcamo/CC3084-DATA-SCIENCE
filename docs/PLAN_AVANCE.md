# Lab 7 — Plan de avance (Ejercicios 1–4, 25 pts)

**Entrega:** jueves 24 de septiembre de 2026, 17:20 hrs.
**Alcance:** carga/armonización/calidad (Ej.1), estadística descriptiva (Ej.2),
correlaciones (Ej.3), KMeans (Ej.4).

## Entorno

```bash
export JAVA_HOME="/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home"
uv pip install --python .venv/bin/python "pyspark==3.5.6" openpyxl
```

Ya instalado en este repo (2026-09-24). `pyspark==3.5.6`, `openpyxl==3.1.5`.

## Datos

Descargar de https://www.ine.gob.gt/encuesta-nacional-de-empleo-e-ingresos/
las bases de **Personas** (no Hogares) de I, II, III, IV de 2025 y I de 2026,
con sus diccionarios. Guardar en `data/raw/eneic/` (ignorado por git) con estos
nombres exactos:

| Archivo local | Trimestre real | `TRIMESTRE` original en el archivo |
|---|---|---|
| `personas_2025_T1.xlsx` | 2025 T1 | 2 |
| `personas_2025_T2.xlsx` | 2025 T2 | 3 (175 registros traen 2) |
| `personas_2025_T3.xlsx` | 2025 T3 | 4 |
| `personas_2025_T4.xlsx` | 2025 T4 | 5 |
| `personas_2026_T1.xlsx` | 2026 T1 | 6 |

Verificar conteos originales antes de filtrar: 51,588 / 51,167 / 51,583 / 49,338
(302 columnas) / 49,843.

## Reparto

| Persona | Sección notebook | Ejercicio | Pts |
|---|---|---|---|
| **P1** | S0 Setup + S1 Carga y armonización | Ej.1 | 5 |
| **P2** | S2 Estadística descriptiva + gráficas + S3 Correlaciones | Ej.2, Ej.3 | 10 |
| **P3** | S4 Segmentación KMeans | Ej.4 | 10 |

**Dependencia:** P2 y P3 no pueden empezar hasta que P1 publique
`data/processed/eneic_2025.parquet` (camino crítico). P1 lo prioriza en la
primera hora.

## Detalle por persona

### P1 — S0 Setup + S1 Carga, armonización, calidad (Ej.1, 5 pts)

1. Leer cada `.xlsx` con pandas/openpyxl, uno a la vez (no cargar los 5 juntos).
2. Seleccionar solo las columnas de la tabla de variables (ver reglas técnicas
   abajo) y forzar tipos explícitos antes de convertir a Spark DataFrame.
3. Crear `periodo_archivo`, `anio_archivo`, `trimestre_calendario` y
   `archivo_origen` **a partir del nombre de archivo**, no de `TRIMESTRE`.
   Conservar `TRIMESTRE` y `ANIO` originales.
4. Homologar tipos de códigos (mismo código puede llegar como número o texto)
   **antes** de unir.
5. Unir los 4 trimestres de 2025 con `unionByName` (nunca `union` posicional:
   IV-2025 trae 302 columnas contra 270 de los demás).
6. Aplicar filtros de población y calidad (ver reglas técnicas), **contando**
   cuántos registros caen en cada paso, siempre en el mismo orden.
7. Verificar unicidad de `(periodo_archivo, NUM_HOGAR, NUM_PERSONA)`. Si hay
   claves repetidas, investigar si son iguales o en conflicto — no usar
   `dropDuplicates()` para taparlo.
8. Guardar `data/processed/eneic_2025.parquet` y `data/processed/eneic_2026.parquet`
   (2026 con las mismas transformaciones de armonización pero sin usarse aún
   para entrenar/validar).
9. Mostrar: esquema y 5 registros; conteos por archivo antes/después de filtros;
   cantidad y % de faltantes por variable antes de filtrar; conteo de exclusión
   por paso; verificación de unicidad de la clave.
10. Responder en Markdown:
    - Por qué IV-2025 no puede apilarse por posición de columnas.
    - Diferencia entre dato ausente porque la pregunta no aplica y respuesta no registrada.
    - Por qué una persona observada en dos períodos no se elimina como duplicado.
    - Por qué el conteo final no representa a todos los trabajadores del país.

### P2 — S2 Estadística descriptiva (Ej.2, 5 pts) + S3 Correlaciones (Ej.3, 5 pts)

Depende del Parquet de P1.

**S2:** sobre la población analítica completa de 2025 (no la muestra de graficar):
- Tabla: n, media, mediana, desviación estándar, mínimo, máximo, p25, p75, p95
  de `salario_mensual`, `edad`, `antiguedad`, `horas_semanales`.
- Gráficas (muestra ≤5,000–10,000 filas a pandas si son a nivel de registro;
  tablas agregadas si son conteos/medias por grupo — las métricas siempre sobre
  el total):
  - distribución de registros por categoría ocupacional, nivel educativo y dominio;
  - forma de la distribución del salario (puede usar escala log solo para
    visualizar, identificándola como tal; el objetivo en quetzales se mantiene
    para el modelado);
  - comparación media vs. mediana del salario;
  - salario mediano por nivel educativo y por categoría ocupacional;
  - tamaño de muestra y salario mediano por trimestre.
- Interpretar cada tabla/gráfica en Markdown (obligatorio, sin excepción).

**S3:** con `VectorAssembler` + `Correlation.corr()` de `pyspark.ml.stat`, matriz
de correlación de Pearson entre `salario_mensual`, `edad`, `antiguedad`,
`horas_semanales` (todos los registros elegibles de 2025). Mapa de calor con
etiquetas. Responder: ¿qué variables tienen mayor asociación lineal con el
salario? ¿hay relación entre edad y antigüedad?

### P3 — S4 Segmentación KMeans (Ej.4, 10 pts)

Depende del Parquet de P1 (mientras tanto, prototipar el pipeline contra un
DataFrame sintético con el mismo esquema).

1. Elegir variables numéricas relevantes para el perfil (edad, antigüedad,
   horas_semanales; evaluar si conviene incluir salario y justificar la decisión
   en Markdown — el enunciado pide analizarlo explícitamente, no asumirlo).
2. Estandarizar con `StandardScaler` dentro de un `Pipeline` con `VectorAssembler`.
3. Entrenar `KMeans` con K = 2, 3, 4, 5. Reportar una métrica de calidad (WSSSE
   y/o silueta vía `ClusteringEvaluator`) por K.
4. Elegir el mejor K y justificar el criterio usado.
5. Describir cada cluster en prosa (edad promedio, antigüedad, horas, mezcla de
   categorías/dominios dominante).

## Reglas técnicas comunes (no negociables)

- **Población:** edad ≥ 15, `OCUPADOS = 1`, `P05C16 ∈ {1,2,3,4}`, `P05D01`
  numérico finito y estrictamente positivo → `salario_mensual`.
- **Antigüedad:** `antiguedad_anios + antiguedad_meses/12`, en años.
  Validar: antiguedad_anios ≥ 0; meses entero 0–11; antigüedad ≤ edad.
- **Horas:** `0 < horas_semanales ≤ 168`.
- **Excluir y contar** lo que no cumpla; **no imputar salario**.
- **Categóricas:** validar contra diccionario; ausente/no reconocido → `"DESCONOCIDO"`
  (nunca 0 — el código educativo 0 significa "ninguno", no es faltante).
- **No eliminar outliers de salario.** Sin recortes por percentiles.
- **Sin ponderar por `FACTOR`** en clustering ni estadísticas principales.
  Conservar `FACTOR` y explicar en Markdown para qué serviría en un análisis
  poblacional.
- **6 predictores para modelado (relevante desde ya para nombrar columnas
  igual en S1):** `edad`, `antiguedad`, `horas_semanales`, `nivel_educativo`,
  `categoria_ocupacional`, `dominio`.
- El notebook debe correr de principio a fin sin depender de variables de
  ejecuciones anteriores (`Kernel → Restart & Run All`).

## Flujo de Git

- Rama de integración: `lab7`. Ramas de trabajo: `lab7/p1-carga`,
  `lab7/p2-eda`, `lab7/p3-kmeans`.
- El notebook se versiona como `notebooks/Lab7_Spark_MLlib.py` (formato
  jupytext `py:percent`). **No commitear el `.ipynb`** durante el desarrollo —
  evita conflictos de merge en el JSON de salidas.
- Antes de la entrega, una sola persona corre todo el notebook de principio a
  fin y genera `Lab7_Spark_MLlib.ipynb` con `jupytext --sync`; ese es el único
  commit del `.ipynb`.
- Mínimo 3 commits por persona (requisito del enunciado de participación).

## Checklist antes de entregar

- [ ] Conteos por archivo antes de filtrar coinciden con el enunciado.
- [ ] Cascada de filtros: `n_inicial - Σ excluidos = n_final`, exacto.
- [ ] Unicidad de clave verificada y documentada (no oculta con `dropDuplicates`).
- [ ] Parquet 2025 y 2026 escritos y releídos con el esquema esperado.
- [ ] 8 estadísticas para las 4 variables numéricas.
- [ ] Cada gráfica tiene su interpretación en Markdown.
- [ ] Matriz de correlación con etiquetas + respuestas de S3.
- [ ] WSSSE/silueta para K=2,3,4,5; K elegido justificado; descripción de cada cluster.
- [ ] `Kernel → Restart & Run All` corre sin error.
