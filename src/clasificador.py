"""Clasificación de tweets nuevos (inciso 7).

La función pública recibe el texto **crudo** de un tweet, tal como llega de Twitter
(con URLs, hashtags, menciones, emojis y mayúsculas), y devuelve si describe un
desastre real o no.

El punto delicado es que el tweet nuevo debe atravesar exactamente la misma
transformación que atravesaron los tweets de entrenamiento. Se garantiza por dos
vías: la limpieza viene de `limpieza.STEPS`, que es la misma constante que se usó
para generar `train_cleaned.csv`, y la vectorización viaja dentro del Pipeline
serializado, con el vocabulario y los pesos IDF fijados durante el entrenamiento.
"""

import sys
from functools import lru_cache
from pathlib import Path

import joblib

try:
    from src.limpieza import clean_text
except ModuleNotFoundError:
    # Al invocar `python src/clasificador.py` el directorio en sys.path es src/,
    # no la raíz del proyecto. Se agrega para que el paquete resuelva igual que
    # cuando se importa desde los notebooks.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src.limpieza import clean_text

MODELO_PATH = Path(__file__).resolve().parent.parent / "models" / "clasificador.joblib"

# Por encima de este margen alrededor de 0.5 la prediccion se reporta como dudosa.
MARGEN_DUDA = 0.10


@lru_cache(maxsize=1)
def cargar_modelo(ruta: str | Path = MODELO_PATH):
    """Carga el Pipeline entrenado. Se cachea para no releer el archivo en cada llamada."""
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(
            f"No se encontró el modelo en {ruta}. "
            "Ejecute notebooks/modelos_clasificacion.ipynb para generarlo."
        )
    return joblib.load(ruta)


def clasificar_tweet(texto: str, umbral: float = 0.5, modelo=None) -> dict:
    """Clasifica un tweet crudo como desastre real o no.

    Args:
        texto: el tweet sin preprocesar.
        umbral: probabilidad a partir de la cual se declara desastre.
        modelo: Pipeline ya cargado; si se omite se usa el serializado en disco.

    Returns:
        dict con la etiqueta, la probabilidad, el nivel de confianza y el texto
        limpio que realmente vio el modelo.
    """
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError("El texto del tweet no puede estar vacío.")

    modelo = modelo if modelo is not None else cargar_modelo()
    limpio = clean_text(texto)

    # La limpieza puede vaciar un tweet formado solo por URLs, emojis o stopwords.
    # Vectorizar una cadena vacía devuelve el vector nulo y el modelo respondería
    # con su sesgo, una prediccion sin ninguna evidencia detrás.
    if not limpio:
        return {
            "etiqueta": "Indeterminado",
            "es_desastre": None,
            "probabilidad": None,
            "confianza": "nula",
            "texto_original": texto,
            "texto_limpio": "",
            "nota": "El tweet quedó vacío tras la limpieza: no contiene términos evaluables.",
        }

    probabilidad = float(modelo.predict_proba([limpio])[0, 1])
    es_desastre = probabilidad >= umbral

    return {
        "etiqueta": "Desastre real" if es_desastre else "No desastre",
        "es_desastre": bool(es_desastre),
        "probabilidad": probabilidad,
        "confianza": "baja" if abs(probabilidad - 0.5) < MARGEN_DUDA else "alta",
        "texto_original": texto,
        "texto_limpio": limpio,
    }


def clasificar_lote(textos: list[str], umbral: float = 0.5) -> list[dict]:
    """Versión por lotes. Carga el modelo una sola vez para toda la lista."""
    modelo = cargar_modelo()
    resultados = []
    for t in textos:
        try:
            resultados.append(clasificar_tweet(t, umbral=umbral, modelo=modelo))
        except ValueError as e:
            resultados.append({"etiqueta": "Error", "texto_original": t, "nota": str(e)})
    return resultados


def explicar_prediccion(texto: str, top_n: int = 5, modelo=None) -> list[tuple[str, float]]:
    """Términos del tweet que más pesaron en la decisión, con su coeficiente.

    Solo tiene sentido porque el clasificador es lineal: la contribución de cada
    término es su valor TF-IDF multiplicado por el coeficiente aprendido.
    """
    modelo = modelo if modelo is not None else cargar_modelo()
    limpio = clean_text(texto)
    if not limpio:
        return []

    vec, clf = modelo.named_steps["tfidf"], modelo.named_steps["clf"]
    X = vec.transform([limpio])
    nombres = vec.get_feature_names_out()

    contribuciones = [
        (nombres[i], float(X[0, i] * clf.coef_[0][i])) for i in X.nonzero()[1]
    ]
    return sorted(contribuciones, key=lambda x: abs(x[1]), reverse=True)[:top_n]


def _formatear(r: dict) -> str:
    if r["etiqueta"] in ("Indeterminado", "Error"):
        return f"  → {r['etiqueta']}: {r.get('nota', '')}"
    icono = "[DESASTRE]" if r["es_desastre"] else "[no desastre]"
    return (
        f"  → {icono} {r['etiqueta']} "
        f"(probabilidad {r['probabilidad']:.1%}, confianza {r['confianza']})\n"
        f"    texto limpio: '{r['texto_limpio']}'"
    )


def main():
    """Modo interactivo: el usuario escribe tweets y el sistema los clasifica."""
    print("Clasificador de tweets de desastre. Escriba 'salir' para terminar.\n")
    cargar_modelo()
    while True:
        try:
            texto = input("Tweet> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if texto.lower() in {"salir", "exit", "quit"}:
            break
        if not texto:
            continue
        print(_formatear(clasificar_tweet(texto)))
        for termino, peso in explicar_prediccion(texto):
            print(f"      {termino:20s} {peso:+.3f}")
        print()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for r in clasificar_lote([" ".join(sys.argv[1:])]):
            print(_formatear(r))
    else:
        main()
