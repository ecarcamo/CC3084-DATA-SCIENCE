"""Limpieza y preprocesamiento del Laboratorio 6 (YouTube).

Funciones puras reutilizables por las etapas siguientes. Cubren:
normalización de identificadores y handles, conversión de conteos en texto a
numérico, parseo de columnas serializadas y construcción de `texto_limpio`.

Ejecutar `python src/limpieza.py` corre un self-check.
"""
from __future__ import annotations

import re
import json
import urllib.parse
from typing import Iterable

import pandas as pd

# --------------------------------------------------------------------------- #
# Identificadores y nombres
# --------------------------------------------------------------------------- #

_NULOS_TEXTO = {"", "nan", "none", "null", "na"}


def normalizar_id(serie: pd.Series) -> pd.Series:
    """Identificador -> string sin espacios; marcadores de nulo -> <NA>.

    NO sustituye el id por ningún nombre visible; solo lo estandariza.
    """
    s = serie.astype("string").str.strip()
    return s.mask(s.str.lower().isin(_NULOS_TEXTO))


def normalizar_handle(serie: pd.Series) -> pd.Series:
    """'/@M%C3%A9xicoPoder' -> 'méxicopoder'. Quita '/@', decodifica %XX, minúsculas.

    El handle es una etiqueta visible; se conserva solo para mostrar, nunca como id.
    """
    s = serie.astype("string").str.strip()
    s = s.str.replace(r"^/?@", "", regex=True)
    s = s.map(lambda x: urllib.parse.unquote(x) if pd.notna(x) else x)
    s = s.astype("string").str.lower()
    return s.mask(s.str.lower().isin(_NULOS_TEXTO))


# --------------------------------------------------------------------------- #
# Conteos almacenados como texto -> numérico
# --------------------------------------------------------------------------- #

_MULT = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000,
         "mil": 1_000, "millon": 1_000_000, "millones": 1_000_000}
_RUIDO_CONTEO = re.compile(
    r"\b(vistas?|views?|reproducciones|me\s*gusta|likes?|comentarios?|respuestas?)\b",
    re.IGNORECASE,
)


def _parsear_conteo_uno(x) -> object:
    """Devuelve int o pd.NA. Documenta los casos en el docstring de `parsear_conteo`."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return pd.NA
    t = _RUIDO_CONTEO.sub("", str(x)).strip().lower().replace("\xa0", " ")
    if t in {"", "-", "—"}:
        return pd.NA

    m = re.fullmatch(r"([\d.,]+)\s*(k|m|b|mil|millon|millones)?", t)
    if not m:
        return pd.NA
    num, suf = m.group(1), m.group(2)

    # Resolver separador de miles vs. decimal
    if "," in num and "." in num:
        # el último separador es el decimal
        dec = "," if num.rfind(",") > num.rfind(".") else "."
        mil = "." if dec == "," else ","
        num = num.replace(mil, "").replace(dec, ".")
    elif num.count(",") == 1 and not re.search(r",\d{3}\b", num):
        num = num.replace(",", ".")          # coma decimal: "1,2K"
    else:
        num = num.replace(",", "")           # coma de miles: "29,736"
        if num.count(".") == 1 and re.search(r"\.\d{3}$", num) and not suf:
            num = num.replace(".", "")        # punto de miles: "29.736"

    try:
        val = float(num)
    except ValueError:
        return pd.NA
    if suf:
        val *= _MULT[suf]
    return int(round(val))


def parsear_conteo(serie: pd.Series) -> pd.Series:
    """Conteo en texto -> Int64.

    Maneja: sufijo textual ('2,390 vistas'), separadores de miles (',' o '.'),
    coma decimal, abreviaturas ('1.2K', '3 mil', '2M'), y valores no válidos
    (' ', '', '-', None) -> <NA>.
    """
    return serie.map(_parsear_conteo_uno).astype("Int64")


# --------------------------------------------------------------------------- #
# Columnas serializadas
# --------------------------------------------------------------------------- #

def parsear_lista_json(serie: pd.Series) -> pd.Series:
    """'["a", "b"]' -> ['a', 'b'] ; '[]' o nulo -> []."""
    def uno(x):
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return []
        try:
            v = json.loads(x)
            return v if isinstance(v, list) else [v]
        except (json.JSONDecodeError, TypeError):
            return [p.strip() for p in str(x).split(",") if p.strip()]
    return serie.map(uno)


def separar_pipe(serie: pd.Series) -> pd.Series:
    """'a.csv | b.csv' -> ['a.csv', 'b.csv']."""
    def uno(x):
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return []
        return [p.strip() for p in str(x).split("|") if p.strip()]
    return serie.map(uno)


# --------------------------------------------------------------------------- #
# Texto
# --------------------------------------------------------------------------- #

_URL = re.compile(r"(https?://\S+|www\.\S+)", re.IGNORECASE)
_MENCION = re.compile(r"@[\w.\-]+")
_HASHTAG = re.compile(r"#(\w+)")
_NO_ALFA = re.compile(r"[^a-záéíóúñü\s]", re.IGNORECASE)
_ESPACIOS = re.compile(r"\s+")


def _emojis_de(texto: str):
    import emoji
    return [d["emoji"] for d in emoji.emoji_list(texto)]


def limpiar_texto_serie(
    serie: pd.Series,
    nlp,
    stopwords_es: set[str],
) -> pd.DataFrame:
    """Construye texto_limpio y separa hashtags, menciones y emojis.

    Pasos de `texto_limpio` (en orden, todos documentados en el notebook):
    minúsculas -> quitar URLs -> separar menciones y hashtags -> quitar emojis
    -> quitar números y puntuación -> quitar stopwords en español -> lematizar
    (spaCy `es_core_news_sm`) -> conservar tokens alfabéticos de >= 3 letras.

    El texto original NO se toca (se conserva aparte para auditoría y sentimiento).
    """
    original = serie.astype("string")

    hashtags = original.map(lambda t: _HASHTAG.findall(t) if pd.notna(t) else [])
    menciones = original.map(
        lambda t: [m.lstrip("@") for m in _MENCION.findall(t)] if pd.notna(t) else []
    )
    emojis = original.map(lambda t: _emojis_de(t) if pd.notna(t) else [])

    def pre(t: str) -> str:
        t = t.lower()
        t = _URL.sub(" ", t)
        t = _MENCION.sub(" ", t)
        t = _HASHTAG.sub(r" \1 ", t)          # conserva la palabra del hashtag
        import emoji
        t = emoji.replace_emoji(t, " ")
        t = _NO_ALFA.sub(" ", t)              # quita números y puntuación
        return _ESPACIOS.sub(" ", t).strip()

    pretratado = [pre(t) if isinstance(t, str) else "" for t in original]

    limpios = []
    for doc in nlp.pipe(pretratado, batch_size=64):
        toks = [
            tok.lemma_.lower()
            for tok in doc
            if tok.is_alpha
            and len(tok.lemma_) >= 3
            and tok.lemma_.lower() not in stopwords_es
            and tok.text.lower() not in stopwords_es
        ]
        limpios.append(" ".join(toks))

    return pd.DataFrame(
        {
            "texto_original": original,
            "texto_limpio": pd.array(limpios, dtype="string"),
            "hashtags": hashtags.values,
            "menciones": menciones.values,
            "emojis": emojis.values,
            "n_emojis": [len(e) for e in emojis],
        },
        index=serie.index,
    )


def cargar_recursos_texto():
    """Devuelve (nlp, stopwords_es). Descarga los stopwords de NLTK si faltan."""
    import nltk
    import spacy

    try:
        from nltk.corpus import stopwords
        stopwords.words("spanish")
    except LookupError:
        nltk.download("stopwords", quiet=True)
        from nltk.corpus import stopwords

    stop = set(stopwords.words("spanish"))
    nlp = spacy.load("es_core_news_sm", disable=["ner", "parser", "attribute_ruler"])
    return nlp, stop


# --------------------------------------------------------------------------- #
# Diagnóstico
# --------------------------------------------------------------------------- #

def resumen_duplicados(df: pd.DataFrame, subset: Iterable[str]) -> dict:
    subset = list(subset)
    return {
        "filas": len(df),
        "duplicados_fila_completa": int(df.duplicated().sum()),
        f"duplicados_por_{'+'.join(subset)}": int(df.duplicated(subset=subset).sum()),
    }


def efecto_limpieza(antes: pd.Series, despues: pd.Series) -> pd.DataFrame:
    a = antes.astype("string").fillna("").str.strip()
    d = despues.astype("string").fillna("").str.strip()
    return pd.DataFrame(
        {
            "métrica": ["registros", "textos vacíos", "textos duplicados", "long. media (car.)"],
            "antes": [len(a), int((a == "").sum()), int(a.duplicated().sum()), round(a.str.len().mean(), 1)],
            "después": [len(d), int((d == "").sum()), int(d.duplicated().sum()), round(d.str.len().mean(), 1)],
        }
    )


def _self_check() -> None:
    assert parsear_conteo(pd.Series([" ", "", "1,234", "29,736 vistas", "1.2K", "3 mil", "2M", None]))\
        .tolist() == [pd.NA, pd.NA, 1234, 29736, 1200, 3000, 2_000_000, pd.NA]
    assert normalizar_handle(pd.Series(["/@M%C3%A9xicoPoder", "/@abc"])).tolist() == ["méxicopoder", "abc"]
    assert parsear_lista_json(pd.Series(['["a", "b"]', "[]", None])).tolist() == [["a", "b"], [], []]
    assert separar_pipe(pd.Series(["a.csv | b.csv", None])).tolist() == [["a.csv", "b.csv"], []]
    print("limpieza.py: self-check OK")


if __name__ == "__main__":
    _self_check()
