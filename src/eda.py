"""Funciones de análisis exploratorio para el dataset de disaster tweets."""

from collections import Counter

import matplotlib.pyplot as plt
import pandas as pd
from wordcloud import WordCloud


def word_frequencies(df: pd.DataFrame, text_col: str = "text", target: int | None = None, top_n: int = 20) -> pd.DataFrame:
    """Cuenta palabras en text_col, opcionalmente filtrando por target. Devuelve top_n como DataFrame."""
    subset = df if target is None else df[df["target"] == target]
    words = " ".join(subset[text_col].dropna()).split()
    counts = Counter(words).most_common(top_n)
    return pd.DataFrame(counts, columns=["word", "count"])


def plot_top_words(freqs: pd.DataFrame, title: str, ax=None):
    """Barra horizontal de palabras más frecuentes (mayor arriba)."""
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 6))
    ordered = freqs.iloc[::-1]
    ax.barh(ordered["word"], ordered["count"])
    ax.set_title(title)
    ax.set_xlabel("Frecuencia")
    return ax


def make_wordcloud(texts: pd.Series, **kwargs) -> WordCloud:
    """Genera una nube de palabras a partir de una serie de texto."""
    text = " ".join(texts.dropna())
    params = {"width": 800, "height": 400, "background_color": "white", "colormap": "viridis"}
    params.update(kwargs)
    return WordCloud(**params).generate(text)


def shared_words(df: pd.DataFrame, text_col: str = "text", top_n: int = 100) -> dict:
    """Compara el top_n de palabras entre target=1 y target=0.

    Devuelve dict con 'shared', 'only_disaster', 'only_non_disaster' (sets de palabras).
    """
    disaster = set(word_frequencies(df, text_col, target=1, top_n=top_n)["word"])
    non_disaster = set(word_frequencies(df, text_col, target=0, top_n=top_n)["word"])
    return {
        "shared": disaster & non_disaster,
        "only_disaster": disaster - non_disaster,
        "only_non_disaster": non_disaster - disaster,
    }


def text_stats(df: pd.DataFrame, text_col: str = "text") -> pd.DataFrame:
    """Añade columnas de longitud en caracteres y en palabras."""
    out = df.copy()
    out["char_len"] = out[text_col].str.len()
    out["word_count"] = out[text_col].str.split().str.len()
    return out


if __name__ == "__main__":
    demo = pd.DataFrame(
        {
            "text": ["fire near the river", "fire truck racing fast", "having a great day today", "great weather today"],
            "target": [1, 1, 0, 0],
        }
    )

    freqs = word_frequencies(demo, target=1, top_n=5)
    assert freqs.iloc[0]["word"] == "fire" and freqs.iloc[0]["count"] == 2

    stats = text_stats(demo)
    assert stats.loc[0, "word_count"] == 4
    assert stats.loc[0, "char_len"] == len("fire near the river")

    shared = shared_words(demo, top_n=10)
    assert "today" in shared["only_non_disaster"]
    assert "fire" in shared["only_disaster"]
    assert shared["shared"] == set()

    wc = make_wordcloud(demo["text"])
    assert wc.words_

    print("eda.py: self-check OK")
