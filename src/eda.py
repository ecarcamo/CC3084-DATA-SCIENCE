"""Análisis exploratorio del Laboratorio 6 (YouTube) — Sección 3.

Funciones puras que consumen la salida de la Etapa 2 (`data/processed/*_clean.csv`)
y producen las tablas de la Sección 3: resúmenes de conteo, concentración de la
participación, frecuencias de palabras/bigramas y co-participación entre videos.

Ejecutar `python src/eda.py` corre un self-check con los números verificados.
"""
from __future__ import annotations

import json
import re
import itertools
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

PROC = Path(__file__).resolve().parent.parent / "data" / "processed"
VIDEOS_CLEAN = PROC / "videos_clean.csv"
COMMENTS_CLEAN = PROC / "comments_clean.csv"

# Columnas que la Etapa 2 serializó a JSON al escribir el CSV.
_LISTAS_VIDEOS = ["keywords_list", "query_hits_list", "dataset_sources_list"]
_LISTAS_COMMENTS = ["hashtags", "menciones", "emojis", "dataset_sources_list"]

_ID_COLS = ["video_id", "comment_id", "channel_id", "author_channel_id"]


# --------------------------------------------------------------------------- #
# Carga
# --------------------------------------------------------------------------- #

def _parsear_listas(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Deshace la serialización JSON de la Etapa 2: '["a"]' -> ['a']."""
    df = df.copy()
    for col in cols:
        if col in df.columns:
            df[col] = df[col].map(
                lambda x: json.loads(x) if isinstance(x, str) and x.startswith("[") else []
            )
    return df


def cargar_procesados() -> tuple[pd.DataFrame, pd.DataFrame]:
    """(videos_clean, comments_clean) con las columnas de lista ya parseadas.

    Requiere haber corrido `notebooks/01_carga_limpieza.ipynb` (Etapa 2), que
    escribe `data/processed/`. Esa carpeta está en .gitignore y se regenera.
    """
    if not COMMENTS_CLEAN.exists():
        raise FileNotFoundError(
            f"No existe {COMMENTS_CLEAN}. Corre notebooks/01_carga_limpieza.ipynb "
            "(Etapa 2) para regenerar data/processed/."
        )
    dtypes = {c: "string" for c in _ID_COLS}
    videos = pd.read_csv(VIDEOS_CLEAN, dtype={k: v for k, v in dtypes.items()
                                              if k in {"video_id", "channel_id"}})
    comments = pd.read_csv(COMMENTS_CLEAN, dtype=dtypes)
    return (_parsear_listas(videos, _LISTAS_VIDEOS),
            _parsear_listas(comments, _LISTAS_COMMENTS))


# --------------------------------------------------------------------------- #
# Resúmenes de conteo (3.1)
# --------------------------------------------------------------------------- #

def resumen_global(videos: pd.DataFrame, comments: pd.DataFrame) -> pd.DataFrame:
    """Tabla de magnitudes básicas: videos, canales, comentarios, autores.

    Separa el universo de videos (293) del subconjunto con comentarios (19),
    porque toda la Sección 3 que use comentarios describe solo ese subconjunto.
    """
    filas = [
        ("videos", videos["video_id"].nunique()),
        ("canales (dueños de video)", videos["channel_id"].nunique()),
        ("comentarios", comments["comment_id"].nunique()),
        ("autores de comentarios", comments["author_channel_id"].nunique()),
        ("videos con ≥1 comentario", comments["video_id"].nunique()),
        ("videos sin comentarios",
         videos["video_id"].nunique() - comments["video_id"].nunique()),
        ("canales con ≥1 comentario", comments["channel_id"].nunique()),
        ("categorías distintas", videos["category"].nunique()),
        ("consultas de búsqueda (videos)", videos["source_query"].nunique()),
        ("consultas de búsqueda (comentarios)", comments["source_query"].nunique()),
    ]
    df = pd.DataFrame(filas, columns=["magnitud", "valor"])
    df["% del total"] = [
        "", "", "", "",
        f"{100 * comments['video_id'].nunique() / videos['video_id'].nunique():.1f} % de los videos",
        f"{100 * (videos['video_id'].nunique() - comments['video_id'].nunique()) / videos['video_id'].nunique():.1f} % de los videos",
        f"{100 * comments['channel_id'].nunique() / videos['channel_id'].nunique():.1f} % de los canales",
        "", "", "",
    ]
    return df


def tabla_por_video(videos: pd.DataFrame, comments: pd.DataFrame) -> pd.DataFrame:
    """Un renglón por video con comentarios: participación, likes y alcance.

    `n_com` = comentarios observados, `n_aut` = autores únicos,
    `com_por_autor` mide si la participación viene de muchas voces o de pocas
    que repiten.
    """
    agg = (comments.assign(_lk=comments["like_count"].fillna(0))
           .groupby("video_id")
           .agg(n_com=("comment_id", "size"),
                n_aut=("author_channel_id", "nunique"),
                likes=("_lk", "sum"),
                respuestas=("reply_count", "sum")))
    cols = ["video_id", "title", "channel_id", "channel_name", "category",
            "view_count", "source_query", "source_group"]
    out = (agg.merge(videos[cols], on="video_id")
           .sort_values("n_com", ascending=False)
           .reset_index(drop=True))
    out["com_por_autor"] = (out["n_com"] / out["n_aut"]).round(2)
    out["com_por_1k_vistas"] = (1000 * out["n_com"] / out["view_count"]).round(2)
    return out


def describir_numerica(serie: pd.Series, nombre: str) -> pd.DataFrame:
    """Resumen robusto (n, nulos, media, mediana, cuartiles, máx) de un conteo."""
    s = pd.to_numeric(serie, errors="coerce")
    val = s.dropna()
    return pd.DataFrame([{
        "variable": nombre,
        "n": int(val.size),
        "nulos": int(s.isna().sum()),
        "media": round(float(val.mean()), 2) if val.size else np.nan,
        "mediana": float(val.median()) if val.size else np.nan,
        "p25": float(val.quantile(0.25)) if val.size else np.nan,
        "p75": float(val.quantile(0.75)) if val.size else np.nan,
        "p95": round(float(val.quantile(0.95)), 1) if val.size else np.nan,
        "máx": float(val.max()) if val.size else np.nan,
    }])


# --------------------------------------------------------------------------- #
# Concentración (3.2)
# --------------------------------------------------------------------------- #

def gini(x) -> float:
    """Índice de Gini de una distribución no negativa. 0 = uniforme, →1 = concentrada."""
    a = np.sort(np.asarray(x, dtype=float))
    n = a.size
    if n == 0 or a.sum() == 0:
        return float("nan")
    idx = np.arange(1, n + 1)
    return float((2 * (idx * a).sum()) / (n * a.sum()) - (n + 1) / n)


def concentracion(conteos: pd.Series) -> pd.DataFrame:
    """Ranking con participación y acumulado. `conteos` = comentarios por unidad."""
    s = conteos.sort_values(ascending=False)
    total = s.sum()
    return pd.DataFrame({
        "unidad": s.index,
        "comentarios": s.values,
        "pct": (100 * s.values / total).round(2),
        "pct_acumulado": (100 * s.cumsum().values / total).round(2),
        "rank": np.arange(1, s.size + 1),
    })


def curva_lorenz(conteos: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    """(x, y) de la curva de Lorenz: proporción de unidades vs. de comentarios."""
    a = np.sort(np.asarray(conteos, dtype=float))
    x = np.insert(np.arange(1, a.size + 1) / a.size, 0, 0.0)
    y = np.insert(np.cumsum(a) / a.sum(), 0, 0.0)
    return x, y


# --------------------------------------------------------------------------- #
# Texto: palabras, bigramas y listas (3.1)
# --------------------------------------------------------------------------- #

def _tokens(serie: pd.Series) -> list[list[str]]:
    return [t.split() for t in serie.fillna("").astype(str)]


def frecuencias_palabras(serie: pd.Series, n: int = 25) -> pd.DataFrame:
    """Top-n palabras de `texto_limpio` (ya lematizado y sin stopwords)."""
    cnt = Counter(w for doc in _tokens(serie) for w in doc)
    return _a_tabla(cnt, n, "palabra")


def frecuencias_bigramas(serie: pd.Series, n: int = 20) -> pd.DataFrame:
    """Top-n bigramas contiguos de `texto_limpio`.

    Los bigramas se forman sobre el texto ya limpio; al haberse quitado las
    stopwords, un bigrama une palabras que no eran necesariamente adyacentes en
    el texto original (se documenta en el notebook).
    """
    cnt = Counter(f"{doc[i]} {doc[i + 1]}"
                  for doc in _tokens(serie) for i in range(len(doc) - 1))
    return _a_tabla(cnt, n, "bigrama")


def frecuencias_lista(serie: pd.Series, n: int = 20, minuscula: bool = True) -> pd.DataFrame:
    """Top-n elementos de una columna de listas (hashtags, menciones, emojis, keywords)."""
    cnt = Counter(str(x).lower() if minuscula else str(x)
                  for lst in serie for x in (lst if isinstance(lst, list) else []))
    return _a_tabla(cnt, n, "elemento")


_HASHTAG = re.compile(r"#(\w+)")


def hashtags_en_texto(serie: pd.Series, n: int = 20) -> pd.DataFrame:
    """Top-n hashtags extraídos de texto plano (títulos o descripciones de video)."""
    cnt = Counter(h.lower() for t in serie.fillna("").astype(str)
                  for h in _HASHTAG.findall(t))
    return _a_tabla(cnt, n, "hashtag")


def _a_tabla(cnt: Counter, n: int, col: str) -> pd.DataFrame:
    df = pd.DataFrame(cnt.most_common(n), columns=[col, "frecuencia"])
    total = sum(cnt.values())
    df["pct_del_total"] = (100 * df["frecuencia"] / total).round(2) if total else np.nan
    return df


# --------------------------------------------------------------------------- #
# Audiencias compartidas (3.5)
# --------------------------------------------------------------------------- #

def autores_puente(comments: pd.DataFrame) -> pd.DataFrame:
    """Autores que comentaron en más de un video de la muestra.

    Es la evidencia previa a la red bipartita (Etapa 4): estos son los únicos
    autores que pueden conectar videos entre sí en la proyección video-video.
    """
    g = comments.groupby("author_channel_id")
    df = pd.DataFrame({
        "author_name": g["author_name"].first(),
        "n_comentarios": g["comment_id"].size(),
        "n_videos": g["video_id"].nunique(),
        "n_canales": g["channel_id"].nunique(),
        "canales": g["channel_name"].apply(lambda s: sorted(set(s))),
    })
    return (df[df["n_videos"] > 1]
            .sort_values(["n_videos", "n_comentarios"], ascending=False)
            .reset_index())


def pares_videos_compartidos(comments: pd.DataFrame,
                             videos: pd.DataFrame) -> pd.DataFrame:
    """Pares de videos que comparten al menos un autor; peso = autores comunes.

    Anticipa la proyección video-video de la Etapa 5. Un par NO implica
    conversación entre audiencias: solo que una misma cuenta comentó en ambos.
    """
    por_autor = comments.groupby("author_channel_id")["video_id"].apply(set)
    pares = Counter()
    for vids in por_autor:
        for a, b in itertools.combinations(sorted(vids), 2):
            pares[(a, b)] += 1
    if not pares:
        return pd.DataFrame(columns=["video_a", "video_b", "autores_compartidos"])
    tit = videos.set_index("video_id")["title"].to_dict()
    can = videos.set_index("video_id")["channel_name"].to_dict()
    filas = [{"video_a": a, "video_b": b, "autores_compartidos": n,
              "titulo_a": tit.get(a), "titulo_b": tit.get(b),
              "canal_a": can.get(a), "canal_b": can.get(b),
              "mismo_canal": can.get(a) == can.get(b)}
             for (a, b), n in pares.most_common()]
    return pd.DataFrame(filas)


# --------------------------------------------------------------------------- #
# Sentimiento preliminar por emojis (3.5 — se cierra en la Etapa 9)
# --------------------------------------------------------------------------- #

_EMOJI_POS = set("😂😀😃😄😁😊🙂😍🥰❤️💙💚👏🎉👍🙌✨🔥💪🇬🇹😸🥳😉😅")
_EMOJI_NEG = set("😡🤬😢😭😠💩👎🤮😞😔🙄😤👹🤡😖😱")


def sentimiento_emoji(comments: pd.DataFrame) -> pd.Series:
    """Proxy grueso de tono: +1 si predominan emojis positivos, -1 negativos, 0 resto.

    NO sustituye el análisis de sentimiento de la Sección 9: solo cubre los
    comentarios que llevan emoji y no interpreta ironía (😂 puede ser burla).
    """
    def uno(lst):
        if not isinstance(lst, list) or not lst:
            return 0
        pos = sum(e in _EMOJI_POS for e in lst)
        neg = sum(e in _EMOJI_NEG for e in lst)
        return int(np.sign(pos - neg))
    return comments["emojis"].map(uno).rename("tono_emoji")


# --------------------------------------------------------------------------- #
# Self-check
# --------------------------------------------------------------------------- #

def _self_check() -> None:
    videos, comments = cargar_procesados()

    assert videos.shape[0] == 293 and comments.shape[0] == 406
    assert comments["author_channel_id"].nunique() == 332
    assert comments["video_id"].nunique() == 19
    assert comments["channel_id"].nunique() == 8

    por_video = tabla_por_video(videos, comments)
    assert len(por_video) == 19
    assert por_video["n_com"].sum() == 406

    conc = concentracion(comments.groupby("video_id").size())
    assert abs(conc.loc[0, "pct_acumulado"] - 39.66) < 0.05, conc.head()
    assert abs(conc.loc[3, "pct_acumulado"] - 69.21) < 0.05
    assert abs(conc.loc[4, "pct_acumulado"] - 75.37) < 0.05

    assert len(autores_puente(comments)) == 9
    assert len(pares_videos_compartidos(comments, videos)) == 11

    top = frecuencias_palabras(comments["texto_limpio"], 3)
    assert top.loc[0, "palabra"] == "hacer" and top.loc[0, "frecuencia"] == 75, top

    assert 0 < gini(comments.groupby("video_id").size()) < 1
    print("eda.py: self-check OK")
    print(f"  videos={videos.shape} comentarios={comments.shape} "
          f"videos_con_comentarios={comments['video_id'].nunique()} "
          f"autores_puente={len(autores_puente(comments))}")


if __name__ == "__main__":
    _self_check()
