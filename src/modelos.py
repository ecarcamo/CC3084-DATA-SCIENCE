"""Modelos de clasificación de tweets de desastre (inciso 6).

El contexto se aborda por dos vías, ambas evaluadas empíricamente:
  1. Representación: TF-IDF de unigramas vs. unigramas+bigramas. El inciso 4
     concluyó que los bigramas construyen contexto real (`suicide bomber`) y
     que los trigramas sobreajustan a titulares de bots; aquí se comprueba.
  2. Ponderación: TF-IDF castiga las palabras que aparecen en ambas clases
     (`like`, `new`, `via`), que la sección 6 del EDA identificó como no
     discriminantes.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_val_score, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

RANDOM_STATE = 42
TEST_SIZE = 0.2


def split_data(df: pd.DataFrame, text_col: str = "text", target_col: str = "target"):
    """Separa 80/20 de forma estratificada para conservar el balance 57/43 en ambos lados."""
    X = df[text_col].fillna("")
    y = df[target_col]
    return train_test_split(X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y)


def build_models(ngram_range: tuple = (1, 1)) -> dict[str, Pipeline]:
    """Cuatro algoritmos, cada uno como Pipeline TF-IDF + clasificador.

    El Pipeline es deliberado: el vectorizador se ajusta SOLO con el fold de
    entrenamiento en cada corte de la validación cruzada, evitando fuga de
    información del conjunto de prueba hacia el vocabulario/IDF.
    """
    vectorizer = lambda: TfidfVectorizer(
        ngram_range=ngram_range,
        min_df=2,             # descarta términos que aparecen en un solo tweet (ruido/typos)
        sublinear_tf=True,    # log(1+tf): un tweet no repite palabras, satura el conteo
    )

    return {
        "Naive Bayes": Pipeline([
            ("tfidf", vectorizer()),
            ("clf", MultinomialNB(alpha=1.0)),
        ]),
        "Regresión Logística": Pipeline([
            ("tfidf", vectorizer()),
            ("clf", LogisticRegression(C=1.0, max_iter=1000, random_state=RANDOM_STATE)),
        ]),
        "SVM Lineal": Pipeline([
            ("tfidf", vectorizer()),
            ("clf", LinearSVC(C=1.0, random_state=RANDOM_STATE)),
        ]),
        "Random Forest": Pipeline([
            ("tfidf", vectorizer()),
            ("clf", RandomForestClassifier(
                n_estimators=300, min_samples_leaf=2,
                random_state=RANDOM_STATE, n_jobs=-1,
            )),
        ]),
    }


# Resultado de la búsqueda en malla (ver notebooks/modelos_clasificacion.ipynb §5).
BEST_PARAMS = {
    "tfidf__ngram_range": (1, 2),
    "tfidf__min_df": 1,
    "tfidf__sublinear_tf": False,
    "clf__C": 2.0,
    "clf__class_weight": "balanced",
}


def build_best_model() -> Pipeline:
    """Modelo ganador: Regresión Logística afinada. Es el que consume el inciso 7."""
    model = build_models()["Regresión Logística"]
    model.set_params(**BEST_PARAMS)
    return model


def _scores(model, X) -> pd.Series | None:
    """Puntajes continuos para ROC-AUC. LinearSVC no tiene predict_proba."""
    if hasattr(model, "predict_proba"):
        return model.predict_proba(X)[:, 1]
    if hasattr(model, "decision_function"):
        return model.decision_function(X)
    return None


def evaluate_model(model, X_test, y_test) -> dict:
    """Métricas sobre la clase positiva (target=1, desastre real)."""
    y_pred = model.predict(X_test)
    scores = _scores(model, X_test)
    return {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_test, scores) if scores is not None else float("nan"),
    }


def compare_over_splits(candidates: dict, X, y, n_splits: int = 20) -> pd.DataFrame:
    """Compara modelos sobre n particiones aleatorias distintas.

    Una sola partición 80/20 tiene un error estándar del orden de +-0.015 en F1,
    suficiente para invertir el orden de dos modelos parecidos. Repetir la
    partición separa la diferencia real del ruido de muestreo.
    """
    rows = []
    for seed in range(n_splits):
        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=TEST_SIZE, random_state=seed, stratify=y)
        for name, factory in candidates.items():
            model = factory().fit(X_tr, y_tr)
            rows.append({"particion": seed, "modelo": name, "f1": f1_score(y_te, model.predict(X_te))})
    return pd.DataFrame(rows)


def compare_models(models: dict, X_train, y_train, X_test, y_test, cv: int = 5) -> pd.DataFrame:
    """Entrena cada modelo, lo evalúa en prueba y añade F1 por validación cruzada.

    El F1 de CV se calcula solo sobre entrenamiento; sirve para detectar si la
    métrica de prueba fue suerte de una partición concreta.
    """
    folds = StratifiedKFold(n_splits=cv, shuffle=True, random_state=RANDOM_STATE)
    rows = []
    for name, model in models.items():
        cv_f1 = cross_val_score(model, X_train, y_train, cv=folds, scoring="f1", n_jobs=-1)
        model.fit(X_train, y_train)
        rows.append({"modelo": name, **evaluate_model(model, X_test, y_test),
                     "f1_cv_media": cv_f1.mean(), "f1_cv_std": cv_f1.std()})
    return pd.DataFrame(rows).set_index("modelo").sort_values("f1", ascending=False)


def tune_model(model: Pipeline, X_train, y_train, grid: dict, cv: int = 5) -> GridSearchCV:
    """Búsqueda en malla optimizando F1 de la clase desastre."""
    folds = StratifiedKFold(n_splits=cv, shuffle=True, random_state=RANDOM_STATE)
    search = GridSearchCV(model, grid, scoring="f1", cv=folds, n_jobs=-1)
    search.fit(X_train, y_train)
    return search


def plot_confusion(model, X_test, y_test, title: str, ax=None):
    """Matriz de confusión con etiquetas legibles."""
    if ax is None:
        _, ax = plt.subplots(figsize=(5, 4))
    ConfusionMatrixDisplay.from_estimator(
        model, X_test, y_test, ax=ax, cmap="Blues", colorbar=False,
        display_labels=["No desastre", "Desastre"],
    )
    ax.set_title(title)
    return ax


def report(model, X_test, y_test) -> str:
    """Reporte de clasificación por clase."""
    return classification_report(
        y_test, model.predict(X_test), target_names=["No desastre (0)", "Desastre (1)"], digits=3,
    )


def save_model(model, path: Path) -> Path:
    """Persiste el pipeline completo (vectorizador + clasificador) para el inciso 7."""
    import joblib

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    return path


if __name__ == "__main__":
    df = pd.read_csv(Path(__file__).resolve().parent.parent / "data" / "cleaned" / "train_cleaned.csv")
    X_train, X_test, y_train, y_test = split_data(df)

    assert len(X_train) + len(X_test) == len(df)
    assert abs(y_train.mean() - y_test.mean()) < 0.01, "la estratificación no conservó el balance"

    modelos = build_models(ngram_range=(1, 2))
    tabla = compare_models(modelos, X_train, y_train, X_test, y_test)
    print(tabla.round(4))
    print("\nmodelos.py: self-check OK")
