"""Análisis de sentimiento de los tweets (incisos 8 a 10).

Se apoya en VADER (`nltk.sentiment.vader`), un analizador basado en léxico y reglas
diseñado específicamente para texto de redes sociales. Cada término del léxico trae
una valencia de -4 a +4 asignada por anotadores humanos.

Dos decisiones que conviene tener presentes al leer el resto del módulo:

- **El sentimiento se calcula sobre el texto crudo, no sobre `train_cleaned.csv`.**
  La limpieza del inciso 3 elimina 20 de las 59 negaciones que VADER reconoce, por
  ser stopwords. Eso invierte el signo del sentimiento en los tweets que las usan:
  `"never seen anything this bad"` puntúa -0.63 en crudo y +0.43 después de limpiar.
- **VADER usa señales que la limpieza destruye**: mayúsculas sostenidas como
  intensificador, signos de exclamación repetidos y emoticones ASCII.
"""

import re
from functools import lru_cache

import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# VADER trata como neutro todo lo que quede dentro de esta banda alrededor de cero.
UMBRAL_NEUTRO = 0.05

# Artefactos de codificación del dataset original (mezcla CP1252/UTF-8), no emojis.
MOJIBAKE = re.compile(r'[\x80-\xff-ÿŸ‘’“”]+')
URL = re.compile(r'https?://\S+|www\.\S+')


@lru_cache(maxsize=1)
def analizador() -> SentimentIntensityAnalyzer:
    """Instancia única de VADER; construirla implica leer el léxico de disco."""
    import nltk

    try:
        nltk.data.find('sentiment/vader_lexicon')
    except LookupError:
        nltk.download('vader_lexicon', quiet=True)
    return SentimentIntensityAnalyzer()


def preparar(texto: str) -> str:
    """Limpieza mínima previa al análisis de sentimiento.

    Solo se quitan URLs y artefactos de codificación. Se conservan a propósito las
    mayúsculas, la puntuación, las negaciones y los emoticones, porque VADER los usa.
    """
    if not isinstance(texto, str):
        return ''
    return MOJIBAKE.sub(' ', URL.sub(' ', texto)).strip()


def clasificar_lexicon() -> pd.DataFrame:
    """El léxico de VADER como DataFrame, con cada término etiquetado por polaridad."""
    lex = analizador().lexicon
    df = pd.DataFrame({'palabra': list(lex.keys()), 'valencia': list(lex.values())})
    df['polaridad'] = pd.cut(
        df['valencia'], bins=[-5, -UMBRAL_NEUTRO, UMBRAL_NEUTRO, 5],
        labels=['negativa', 'neutra', 'positiva'],
    )
    return df.sort_values('valencia').reset_index(drop=True)


def contar_palabras(texto: str) -> dict:
    """Cuenta cuántas palabras positivas y negativas del léxico aparecen en el tweet.

    Es el procedimiento que pide el enunciado: determinar la polaridad del tweet a
    partir de la cantidad de palabras de cada signo que contiene.
    """
    lex = analizador().lexicon
    palabras = re.findall(r"[a-zA-Z']+", preparar(texto).lower())

    positivas = [p for p in palabras if lex.get(p, 0) > UMBRAL_NEUTRO]
    negativas = [p for p in palabras if lex.get(p, 0) < -UMBRAL_NEUTRO]

    total = len(positivas) + len(negativas)
    score = (len(positivas) - len(negativas)) / total if total else 0.0

    return {
        'n_positivas': len(positivas),
        'n_negativas': len(negativas),
        'n_neutras': len(palabras) - total,
        'palabras_positivas': positivas,
        'palabras_negativas': negativas,
        'score_conteo': score,
    }


def etiquetar(score: float) -> str:
    """Traduce una puntuación continua a positivo / negativo / neutral."""
    if score >= UMBRAL_NEUTRO:
        return 'positivo'
    if score <= -UMBRAL_NEUTRO:
        return 'negativo'
    return 'neutral'


def analizar_tweet(texto: str) -> dict:
    """Analiza un tweet por los dos métodos: conteo de palabras y VADER completo.

    El conteo es el que pide el enunciado. VADER agrega negación, intensificadores,
    mayúsculas y puntuación, así que sirve de contraste sobre los mismos tweets.
    """
    preparado = preparar(texto)
    vader = analizador().polarity_scores(preparado)
    conteo = contar_palabras(texto)

    return {
        'texto': texto,
        'texto_analizado': preparado,
        **conteo,
        'etiqueta_conteo': etiquetar(conteo['score_conteo']),
        'vader_neg': vader['neg'],
        'vader_neu': vader['neu'],
        'vader_pos': vader['pos'],
        'compound': vader['compound'],
        'etiqueta_vader': etiquetar(vader['compound']),
        'negatividad': -vader['compound'],
    }


def analizar_dataframe(df: pd.DataFrame, text_col: str = 'text') -> pd.DataFrame:
    """Añade las columnas de sentimiento al DataFrame. Espera texto crudo."""
    filas = [analizar_tweet(t) for t in df[text_col]]
    sent = pd.DataFrame(filas, index=df.index)
    columnas = [
        'n_positivas', 'n_negativas', 'score_conteo', 'etiqueta_conteo',
        'vader_neg', 'vader_pos', 'compound', 'etiqueta_vader', 'negatividad',
    ]
    return pd.concat([df, sent[columnas]], axis=1)


def palabras_del_corpus(df: pd.DataFrame, text_col: str = 'text', top_n: int = 20) -> dict:
    """Las palabras con carga de sentimiento que más aparecen en el corpus.

    Distinto de `clasificar_lexicon`, que describe el léxico completo de VADER: aquí
    solo interesan los términos que el dataset realmente usa, con su frecuencia.
    """
    from collections import Counter

    lex = analizador().lexicon
    conteo_pos, conteo_neg = Counter(), Counter()

    for texto in df[text_col]:
        for palabra in re.findall(r"[a-zA-Z']+", preparar(texto).lower()):
            valencia = lex.get(palabra, 0)
            if valencia > UMBRAL_NEUTRO:
                conteo_pos[palabra] += 1
            elif valencia < -UMBRAL_NEUTRO:
                conteo_neg[palabra] += 1

    def _tabla(contador):
        return pd.DataFrame(
            [(p, n, lex[p]) for p, n in contador.most_common(top_n)],
            columns=['palabra', 'frecuencia', 'valencia'],
        )

    return {'positivas': _tabla(conteo_pos), 'negativas': _tabla(conteo_neg)}


if __name__ == '__main__':
    casos = [
        'Massive earthquake kills hundreds in Nepal',
        'Beautiful sunset at the beach today, feeling blessed',
        'this is not good at all',
        'The meeting is at 3pm',
    ]
    for texto in casos:
        r = analizar_tweet(texto)
        print(f'{texto!r}')
        print(f"  conteo: +{r['n_positivas']} -{r['n_negativas']} -> {r['etiqueta_conteo']}")
        print(f"  vader : compound={r['compound']:+.4f} -> {r['etiqueta_vader']}\n")

    assert analizar_tweet('Massive earthquake kills hundreds')['etiqueta_vader'] == 'negativo'
    assert analizar_tweet('feeling blessed and happy')['etiqueta_vader'] == 'positivo'
    assert analizar_tweet('The meeting is at 3pm')['etiqueta_vader'] == 'neutral'
    print('sentimiento.py: self-check OK')
