import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

def get_top_ngrams(texts: pd.Series, ngram_range: tuple = (1, 1), top_k: int = 20) -> pd.DataFrame:
    """Extrae los n-gramas más frecuentes de una serie de textos."""
    texts = texts.dropna()
    if texts.empty:
        return pd.DataFrame(columns=['ngram', 'count'])
        
    vec = CountVectorizer(ngram_range=ngram_range).fit(texts)
    bag_of_words = vec.transform(texts)
    sum_words = bag_of_words.sum(axis=0)
    
    words_freq = [(word, sum_words[0, idx]) for word, idx in vec.vocabulary_.items()]
    words_freq = sorted(words_freq, key=lambda x: x[1], reverse=True)
    
    return pd.DataFrame(words_freq[:top_k], columns=['ngram', 'count'])
