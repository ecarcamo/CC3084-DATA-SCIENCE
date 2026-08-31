import re
import string
import nltk
from nltk.corpus import stopwords
import pandas as pd
from pathlib import Path

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

STOPWORDS = set(stopwords.words('english'))

def to_lowercase(text: str) -> str:
    return text.lower()

def remove_urls(text: str) -> str:
    return re.sub(r'https?://\S+|www\.\S+', '', text)

def remove_special_chars(text: str) -> str:
    return re.sub(r'[@#\']', '', text)

def remove_emojis(text: str) -> str:
    """Los emojis quedan fuera del rango ASCII, así que codificar a ASCII los descarta."""
    return text.encode('ascii', 'ignore').decode('ascii')

def remove_punctuation(text: str) -> str:
    return text.translate(str.maketrans('', '', string.punctuation))

def remove_numbers(text: str) -> str:
    return re.sub(r'\d+', '', text)

def remove_stopwords(text: str) -> str:
    return ' '.join([w for w in text.split() if w not in STOPWORDS])

# Orden canonico de la limpieza. Es la unica definicion del pipeline: tanto el
# procesamiento por lotes del dataset como la clasificacion de un tweet suelto
# la consumen, de modo que no puedan quedar desalineados.
STEPS = [
    ('1_lowercase', to_lowercase),
    ('2_no_urls', remove_urls),
    ('3_no_special', remove_special_chars),
    ('4_no_emojis', remove_emojis),
    ('5_no_punct', remove_punctuation),
    ('6_no_numbers', remove_numbers),
    ('7_no_stopwords', remove_stopwords),
]


def clean_text(text: str) -> str:
    """Aplica el pipeline completo a un solo texto crudo."""
    if not isinstance(text, str):
        return ''
    for _, func in STEPS:
        text = func(text)
    return text.strip()


def apply_cleaning_pipeline(df: pd.DataFrame, text_col: str = 'text', preprocessing_dir: Path = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aplica la limpieza por pasos, guarda los intermedios y devuelve (df_final, stats)."""

    steps = STEPS

    if preprocessing_dir:
        preprocessing_dir.mkdir(parents=True, exist_ok=True)
        
    df_clean = df.copy()
    stats = []
    
    for step_name, func in steps:
        len_before = df_clean[text_col].str.len().mean()
        
        df_clean[text_col] = df_clean[text_col].apply(func)
        
        if preprocessing_dir:
            df_clean.to_csv(preprocessing_dir / f"{step_name}.csv", index=False)
            
        len_after = df_clean[text_col].str.len().mean()
        
        stats.append({
            'step': step_name,
            'len_before': len_before,
            'len_after': len_after
        })
        
    return df_clean, pd.DataFrame(stats)
