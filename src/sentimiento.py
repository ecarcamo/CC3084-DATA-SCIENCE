"""Análisis de sentimiento en español del Laboratorio 6 (YouTube) — Sección 9.

Se usa `pysentimiento` (modelo `robertuito-sentiment-analysis`), un RoBERTa
preentrenado en tuits en español y ajustado con el corpus TASS. Se elige frente a
VADER —diseñado para inglés— y frente a un léxico simple porque:

  * modela el español directamente (no traduce ni asume vocabulario inglés);
  * fue entrenado con lenguaje de redes sociales, cercano al de los comentarios;
  * incorpora negación y contexto (un modelo contextual, no bolsa de palabras).

El modelo se aplica sobre `texto_original`: `pysentimiento` hace su propia
normalización (usuarios, hashtags, risas, emojis) y el texto sin recortar conserva
la negación y la puntuación que el modelo aprovecha. `texto_limpio` —sin stopwords
ni signos— degradaría la señal.

Devuelve una etiqueta por comentario (POS/NEU/NEG) y un puntaje continuo
`score = P(pos) - P(neg)` en [-1, 1]. La predicción se cachea en
`outputs/tablas/sentimiento_comentarios.csv` para que el resto del análisis sea
reproducible sin volver a descargar ni ejecutar el modelo.

Ejecutar `python src/sentimiento.py` corre un self-check con los números verificados.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
TABLAS = REPO / "outputs" / "tablas"
SENT_CSV = TABLAS / "sentimiento_comentarios.csv"

# Etiquetas del modelo -> nombre legible en español.
_ETIQUETAS = {"POS": "positivo", "NEU": "neutral", "NEG": "negativo"}

# Muestra mínima para reportar un promedio de sentimiento por grupo. Debajo de
# este umbral el promedio es demasiado ruidoso para interpretarlo (Sec. 9.2:
# "cuando el tamaño de muestra lo permita").
MIN_MUESTRA = 10


# --------------------------------------------------------------------------- #
# Modelo
# --------------------------------------------------------------------------- #

def _analizador():
    """Crea el analizador de sentimiento en español de pysentimiento."""
    from pysentimiento import create_analyzer

    return create_analyzer(task="sentiment", lang="es")


def analizar_comentarios(
    comments: pd.DataFrame,
    texto: str = "texto_original",
    usar_cache: bool = True,
) -> pd.DataFrame:
    """Etiqueta el sentimiento de cada comentario con el modelo en español.

    Columnas de salida: comment_id, video_id, author_channel_id, channel_id,
    channel_name, etiqueta, prob_pos, prob_neu, prob_neg y score (P_pos - P_neg).

    Con `usar_cache=True` reutiliza `outputs/tablas/sentimiento_comentarios.csv`
    si existe, evitando reejecutar el modelo (reproducibilidad sin red).
    """
    if usar_cache and SENT_CSV.exists():
        cache = pd.read_csv(SENT_CSV, dtype={"comment_id": "string"})
        if len(cache) == len(comments):
            return cache

    if texto not in comments.columns:
        raise ValueError(f"No existe la columna de texto '{texto}'")

    analizador = _analizador()
    textos = comments[texto].fillna("").astype(str).tolist()
    predicciones = analizador.predict(textos)

    probas = pd.DataFrame(
        [
            {f"prob_{_ETIQUETAS[k][:3]}": p.probas.get(k, 0.0) for k in _ETIQUETAS}
            for p in predicciones
        ]
    )
    salida = pd.DataFrame(
        {
            "comment_id": comments["comment_id"].astype("string").values,
            "video_id": comments["video_id"].values,
            "author_channel_id": comments["author_channel_id"].values,
            "channel_id": comments["channel_id"].values,
            "channel_name": comments.get("channel_name", pd.Series(index=comments.index)).values,
            "etiqueta": [_ETIQUETAS[p.output] for p in predicciones],
        }
    )
    salida["prob_pos"] = probas["prob_pos"].values
    salida["prob_neu"] = probas["prob_neu"].values
    salida["prob_neg"] = probas["prob_neg"].values
    salida["score"] = (salida["prob_pos"] - salida["prob_neg"]).round(4)

    TABLAS.mkdir(parents=True, exist_ok=True)
    salida.to_csv(SENT_CSV, index=False)
    return salida


# --------------------------------------------------------------------------- #
# Agregaciones (Sec. 9.2)
# --------------------------------------------------------------------------- #

def _resumen(df: pd.DataFrame, clave: str) -> pd.DataFrame:
    """Distribución de etiquetas y score medio por grupo, con conteo mínimo."""
    grupos = df.groupby(clave)
    resumen = pd.DataFrame(
        {
            "n_comentarios": grupos.size(),
            "score_medio": grupos["score"].mean().round(4),
            "positivo": grupos["etiqueta"].apply(lambda s: (s == "positivo").sum()),
            "neutral": grupos["etiqueta"].apply(lambda s: (s == "neutral").sum()),
            "negativo": grupos["etiqueta"].apply(lambda s: (s == "negativo").sum()),
        }
    )
    resumen["pct_negativo"] = (100 * resumen["negativo"] / resumen["n_comentarios"]).round(1)
    resumen["muestra_suficiente"] = resumen["n_comentarios"] >= MIN_MUESTRA
    return resumen.sort_values("n_comentarios", ascending=False).reset_index()


def por_video(df: pd.DataFrame, por_video_tab: pd.DataFrame | None = None) -> pd.DataFrame:
    """Sentimiento agregado por video. Une título/canal si se pasa eda_por_video."""
    resumen = _resumen(df, "video_id")
    if por_video_tab is not None:
        meta = por_video_tab[["video_id", "title", "channel_name", "source_query"]]
        resumen = resumen.merge(meta, on="video_id", how="left")
    return resumen


def por_canal(df: pd.DataFrame) -> pd.DataFrame:
    """Sentimiento agregado por canal propietario del video comentado."""
    resumen = _resumen(df, "channel_id")
    nombres = df.dropna(subset=["channel_name"]).groupby("channel_id")["channel_name"].first()
    return resumen.merge(nombres.rename("canal"), on="channel_id", how="left")


def por_comunidad(df: pd.DataFrame, comunidades: pd.DataFrame) -> pd.DataFrame:
    """Sentimiento agregado por comunidad de autores (Sec. 7).

    `comunidades` debe tener columnas `nodo` (author_channel_id) y `comunidad`.
    """
    mapa = comunidades.set_index("nodo")["comunidad"]
    con_com = df.assign(comunidad=df["author_channel_id"].map(mapa)).dropna(subset=["comunidad"])
    con_com["comunidad"] = con_com["comunidad"].astype(int)
    return _resumen(con_com, "comunidad")


# --------------------------------------------------------------------------- #
# Self-check
# --------------------------------------------------------------------------- #

def _self_check() -> None:
    import eda

    _, comments = eda.cargar_procesados()
    df = analizar_comentarios(comments)

    assert len(df) == len(comments) == 406, len(df)
    assert set(df["etiqueta"].unique()) <= {"positivo", "neutral", "negativo"}
    assert df["score"].between(-1, 1).all()
    # Las probabilidades deben sumar ~1 por fila.
    suma = df[["prob_pos", "prob_neu", "prob_neg"]].sum(axis=1)
    assert np.allclose(suma, 1.0, atol=1e-3), suma.describe()

    vid = por_video(df)
    assert vid["n_comentarios"].sum() == 406
    assert SENT_CSV.exists()

    dist = df["etiqueta"].value_counts()
    print("sentimiento.py: self-check OK")
    print(f"  {len(df)} comentarios | " + ", ".join(f"{k}={v}" for k, v in dist.items()))
    print(f"  score medio global = {df['score'].mean():.3f}")


if __name__ == "__main__":
    _self_check()
