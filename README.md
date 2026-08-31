# Laboratorio 5 — Clasificación de tweets usando minería de texto

CC3084 Data Science, Universidad del Valle de Guatemala, Semestre II 2026.

Clasificación de tweets del dataset [Natural Language Processing with Disaster
Tweets](https://www.kaggle.com/competitions/nlp-getting-started) de Kaggle, para determinar si
un tweet se refiere a un desastre real o no.

## Estructura

```
src/          funciones reutilizables, cada módulo con self-check ejecutable
notebooks/    análisis y narrativa, importan de src/
models/       clasificador entrenado y serializado
data/         no versionado, se genera con los pasos de abajo
```

## Reproducción

Requiere Python 3.12 y credenciales de Kaggle en `~/.kaggle/kaggle.json`.

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python src/descargar_datos.py
```

Después ejecutar los notebooks en este orden, porque cada uno produce insumos del siguiente:

| # | Notebook | Genera | Ejercicios |
|---|---|---|---|
| 1 | `preprocesamiento_y_limpieza.ipynb` | `data/cleaned/train_cleaned.csv` | 3 |
| 2 | `analisis_frecuencias.ipynb` | — | 4 |
| 3 | `analisis_exploratorio.ipynb` | — | 5 |
| 4 | `modelos_clasificacion.ipynb` | `models/clasificador.joblib` | 6 |
| 5 | `clasificador_tweets.ipynb` | — | 7 |
| 6 | `analisis_sentimiento.ipynb` | `data/cleaned/train_sentimiento.csv` | 8 |
| 7 | `sentimiento_por_categoria.ipynb` | — | 9 |
| 8 | `modelo_con_negatividad.ipynb` | — | 10 |

Los notebooks 4 y 8 tardan varios minutos: entrenan decenas de modelos sobre múltiples
particiones.

## Clasificar un tweet

El modelo entrenado está versionado, así que la función se puede usar sin reentrenar nada.
Recibe el texto crudo y aplica internamente la limpieza del entrenamiento:

```bash
python src/clasificador.py "Massive earthquake hits the city"
```

Sin argumentos entra en modo interactivo. Desde Python:

```python
from src.clasificador import clasificar_tweet
clasificar_tweet("Forest fire near La Ronge Sask. Canada")
```

## Resultados

- **Modelo seleccionado:** Regresión Logística con TF-IDF de unigramas+bigramas, `C=2.0`,
  `class_weight='balanced'`. Accuracy 0.805, F1 0.769 y ROC-AUC 0.869 sobre la clase desastre.
- Se evaluaron 12 configuraciones (4 algoritmos × 3 rangos de n-gramas) más una búsqueda en
  malla de 120 combinaciones. La selección se validó sobre 20 particiones aleatorias con una
  prueba t pareada, no sobre una sola partición.
- Los tweets de desastre real son significativamente más negativos (d de Cohen -0.46), pero
  añadir la negatividad como variable **no** mejora la clasificación: la información ya está
  contenida en el vocabulario del TF-IDF.

## Datos

`data/` no se versiona por tamaño. `train.csv` se obtiene con `src/descargar_datos.py`; su
SHA256 es `61111c6dc31eaffa34d1e1fa62e2395325c9bc3b38bba1941a5f1ed9b3fa60df`.
