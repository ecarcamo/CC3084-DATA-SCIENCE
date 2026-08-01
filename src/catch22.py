from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pycatch22
from scipy.cluster.hierarchy import dendrogram, fcluster, leaves_list, linkage
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_samples, silhouette_score
from sklearn.preprocessing import StandardScaler

from src.comparativo import COLORES
from src.utils import RUTA_FIGURAS, SERIES

# La misma semilla del Laboratorio 2. Se repite aquí en lugar de importarla de src/lstm.py
# porque ese módulo carga TensorFlow y este análisis no lo necesita.
SEMILLA = 42

# El orden es el que devuelve pycatch22.catch22_all y no debe alterarse: las columnas de
# la matriz de características se alinean por posición con la salida de la biblioteca.
CATALOGO = (
    (
        "DN_HistogramMode_5",
        "Distribución de valores",
        "Moda de la distribución de valores, histograma de 5 bins",
    ),
    (
        "DN_HistogramMode_10",
        "Distribución de valores",
        "Moda de la distribución de valores, histograma de 10 bins",
    ),
    (
        "CO_f1ecac",
        "Autocorrelación lineal",
        "Primer cruce de la ACF por 1/e",
    ),
    (
        "CO_FirstMin_ac",
        "Autocorrelación lineal",
        "Retardo del primer mínimo de la ACF",
    ),
    (
        "CO_HistogramAMI_even_2_5",
        "Autocorrelación no lineal",
        "Información mutua con retardo 2, histograma de 5 bins",
    ),
    (
        "CO_trev_1_num",
        "Autocorrelación no lineal",
        "Asimetría temporal de las diferencias sucesivas (trev)",
    ),
    (
        "MD_hrv_classic_pnn40",
        "Diferencias y pronóstico local",
        "Proporción de diferencias sucesivas mayores a 0.04 desviaciones",
    ),
    (
        "SB_BinaryStats_mean_longstretch1",
        "Dinámica simbólica y rachas",
        "Racha más larga de meses consecutivos por encima de la media",
    ),
    (
        "SB_TransitionMatrix_3ac_sumdiagcov",
        "Dinámica simbólica y rachas",
        "Traza de la covarianza de la matriz de transición de 3 símbolos",
    ),
    (
        "PD_PeriodicityWang_th0_01",
        "Espectro y periodicidad",
        "Periodo dominante por el método de Wang, umbral 0.01",
    ),
    (
        "CO_Embed2_Dist_tau_d_expfit_meandiff",
        "Autocorrelación no lineal",
        "Ajuste exponencial a las distancias en el espacio embebido 2-D",
    ),
    (
        "IN_AutoMutualInfoStats_40_gaussian_fmmi",
        "Autocorrelación no lineal",
        "Primer mínimo de la información mutua, estimador gaussiano",
    ),
    (
        "FC_LocalSimple_mean1_tauresrat",
        "Diferencias y pronóstico local",
        "Cambio en la longitud de correlación de los residuos a un paso",
    ),
    (
        "DN_OutlierInclude_p_001_mdrmd",
        "Eventos extremos",
        "Ubicación temporal media de los valores extremos positivos",
    ),
    (
        "DN_OutlierInclude_n_001_mdrmd",
        "Eventos extremos",
        "Ubicación temporal media de los valores extremos negativos",
    ),
    (
        "SP_Summaries_welch_rect_area_5_1",
        "Espectro y periodicidad",
        "Potencia en el quinto más bajo del espectro de Welch",
    ),
    (
        "SB_BinaryStats_diff_longstretch0",
        "Diferencias y pronóstico local",
        "Racha más larga de caídas mensuales consecutivas",
    ),
    (
        "SB_MotifThree_quantile_hh",
        "Dinámica simbólica y rachas",
        "Entropía de los pares de símbolos en un alfabeto de 3 por cuantiles",
    ),
    (
        "SC_FluctAnal_2_rsrangefit_50_1_logi_prop_r1",
        "Escalamiento de fluctuaciones",
        "Escalamiento de las fluctuaciones por rango reescalado",
    ),
    (
        "SC_FluctAnal_2_dfa_50_1_2_logi_prop_r1",
        "Escalamiento de fluctuaciones",
        "Escalamiento de las fluctuaciones por DFA",
    ),
    (
        "SP_Summaries_welch_rect_centroid",
        "Espectro y periodicidad",
        "Centroide del espectro de potencia de Welch",
    ),
    (
        "FC_LocalSimple_mean3_stderr",
        "Diferencias y pronóstico local",
        "Error del pronóstico con la media de los 3 meses anteriores",
    ),
)

CARACTERISTICAS = [nombre for nombre, _, _ in CATALOGO]
FAMILIAS = {nombre: familia for nombre, familia, _ in CATALOGO}
FAMILIAS_ORDENADAS = list(dict.fromkeys(FAMILIAS.values()))
CARACTERISTICAS_POR_FAMILIA = [
    nombre
    for familia in FAMILIAS_ORDENADAS
    for nombre in CARACTERISTICAS
    if FAMILIAS[nombre] == familia
]


def catalogo() -> pd.DataFrame:
    return pd.DataFrame(
        CATALOGO,
        columns=["caracteristica", "familia", "descripcion"],
    )


def extraer_serie(serie: pd.Series) -> pd.Series:
    resultado = pycatch22.catch22_all(serie.to_numpy().tolist())
    # El catálogo asigna familia y descripción por nombre; si la biblioteca reordenara su
    # salida, la matriz quedaría mal etiquetada sin que nada más fallara.
    if resultado["names"] != CARACTERISTICAS:
        raise ValueError("pycatch22 devolvió otras características o en otro orden")
    return pd.Series(resultado["values"], index=CARACTERISTICAS)


def matriz_caracteristicas(series: dict[str, pd.Series]) -> pd.DataFrame:
    matriz = pd.DataFrame(
        {clave: extraer_serie(serie) for clave, serie in series.items()}
    ).T
    matriz.index.name = "clave"
    return matriz[CARACTERISTICAS]


def estandarizar(matriz: pd.DataFrame) -> pd.DataFrame:
    valores = StandardScaler().fit_transform(matriz)
    return pd.DataFrame(valores, index=matriz.index, columns=matriz.columns)


def analizar_pca(
    estandarizada: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    # La matriz centrada de n series tiene rango n - 1, así que pedir más componentes
    # solo agregaría direcciones con varianza numéricamente nula.
    componentes = min(len(estandarizada) - 1, estandarizada.shape[1])
    pca = PCA(n_components=componentes)
    nombres = [f"pc{numero}" for numero in range(1, componentes + 1)]

    coordenadas = pd.DataFrame(
        pca.fit_transform(estandarizada),
        index=estandarizada.index,
        columns=nombres,
    )
    cargas = pd.DataFrame(
        pca.components_.T,
        index=estandarizada.columns,
        columns=nombres,
    )
    varianza = pd.Series(pca.explained_variance_ratio_, index=nombres)
    return coordenadas, cargas, varianza


def _guardar(figura: plt.Figure, ruta: Path) -> None:
    figura.tight_layout()
    figura.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(figura)


def figura_pca(
    coordenadas: pd.DataFrame,
    cargas: pd.DataFrame,
    varianza: pd.Series,
    flechas: int = 8,
    ruta_figuras: Path = RUTA_FIGURAS,
) -> None:
    figura, ejes = plt.subplots(1, 2, figsize=(12, 5))

    numero = np.arange(1, len(varianza) + 1)
    ejes[0].bar(numero, 100 * varianza, color="tab:blue", label="Por componente")
    ejes[0].plot(
        numero,
        100 * varianza.cumsum(),
        color="black",
        marker="o",
        markersize=4,
        linewidth=1,
        label="Acumulada",
    )
    ejes[0].set(
        title="Varianza explicada",
        xlabel="Componente",
        ylabel="% de la varianza total",
        xticks=numero,
    )
    ejes[0].legend(fontsize=8)

    contribucion = np.hypot(cargas["pc1"], cargas["pc2"]).sort_values(ascending=False)
    principales = cargas.loc[contribucion.index[:flechas], ["pc1", "pc2"]]
    alcance = np.abs(coordenadas[["pc1", "pc2"]].to_numpy()).max(axis=0)
    # Una sola escala para las dos direcciones: si cada eje se escalara por separado, los
    # ángulos entre flechas dejarían de ser interpretables.
    escala = 0.9 * np.min(alcance / np.abs(principales.to_numpy()).max(axis=0))
    puntas = escala * principales

    for caracteristica, vector in puntas.iterrows():
        ejes[1].annotate(
            "",
            xy=(vector["pc1"], vector["pc2"]),
            xytext=(0, 0),
            arrowprops={"arrowstyle": "->", "color": "grey", "linewidth": 0.9},
        )
        ejes[1].text(
            1.03 * vector["pc1"],
            1.03 * vector["pc2"],
            caracteristica,
            fontsize=6,
            color="dimgrey",
            ha="left" if vector["pc1"] >= 0 else "right",
            va="bottom" if vector["pc2"] >= 0 else "top",
        )

    limites = 1.3 * np.maximum(alcance, np.abs(puntas.to_numpy()).max(axis=0))
    ejes[1].set_xlim(-limites[0], limites[0])
    ejes[1].set_ylim(-limites[1], limites[1])

    for clave in coordenadas.index:
        punto = coordenadas.loc[clave]
        ejes[1].scatter(
            punto["pc1"],
            punto["pc2"],
            color=COLORES[clave],
            s=70,
            zorder=3,
        )
        ejes[1].annotate(
            SERIES[clave],
            (punto["pc1"], punto["pc2"]),
            textcoords="offset points",
            xytext=(6, 5),
            fontsize=8,
            color=COLORES[clave],
        )

    ejes[1].axhline(0, color="grey", linewidth=0.8, linestyle="--")
    ejes[1].axvline(0, color="grey", linewidth=0.8, linestyle="--")
    ejes[1].set(
        title=f"Plano principal y las {flechas} características de mayor contribución",
        xlabel=f"PC1 ({100 * varianza['pc1']:.1f} %)",
        ylabel=f"PC2 ({100 * varianza['pc2']:.1f} %)",
    )
    _guardar(figura, ruta_figuras / "catch22_pca.png")


def agrupar(
    estandarizada: pd.DataFrame,
    k_maximo: int = 5,
) -> tuple[np.ndarray, pd.DataFrame, pd.Series]:
    enlace = linkage(estandarizada, method="ward")
    siluetas = pd.Series(
        {
            grupos: silhouette_score(
                estandarizada,
                fcluster(enlace, grupos, criterion="maxclust"),
            )
            for grupos in range(2, k_maximo + 1)
        }
    )
    siluetas.index.name = "k"

    k = int(siluetas.idxmax())
    ward = fcluster(enlace, k, criterion="maxclust")
    kmeans = KMeans(n_clusters=k, n_init=10, random_state=SEMILLA).fit_predict(
        estandarizada
    )
    grupos = pd.DataFrame(
        {
            "grupo_ward": ward,
            "grupo_kmeans": kmeans + 1,
            "silueta": silhouette_samples(estandarizada, ward),
        },
        index=estandarizada.index,
    )
    return enlace, grupos, siluetas


def figura_clusters(
    enlace: np.ndarray,
    grupos: pd.DataFrame,
    siluetas: pd.Series,
    ruta_figuras: Path = RUTA_FIGURAS,
) -> None:
    k = grupos["grupo_ward"].nunique()
    # Cortar entre las alturas de fusión k-ésima y (k-1)-ésima deja exactamente k grupos,
    # de modo que los colores del dendrograma son los grupos reportados.
    alturas = np.sort(enlace[:, 2])
    umbral = 0.5 * (alturas[-k] + alturas[-(k - 1)])

    figura, ejes = plt.subplots(1, 2, figsize=(12, 4.5))
    dendrogram(
        enlace,
        labels=[SERIES[clave] for clave in grupos.index],
        orientation="right",
        color_threshold=umbral,
        above_threshold_color="grey",
        ax=ejes[0],
    )
    ejes[0].axvline(umbral, color="black", linewidth=0.8, linestyle="--")
    ejes[0].set(
        title=f"Dendrograma de Ward, corte en {k} grupos",
        xlabel="Distancia de fusión",
    )

    colores = ["tab:orange" if numero == k else "tab:blue" for numero in siluetas.index]
    ejes[1].bar(siluetas.index.astype(str), siluetas, color=colores)
    for numero, valor in zip(siluetas.index.astype(str), siluetas):
        ejes[1].text(numero, valor, f"{valor:.3f}", ha="center", va="bottom", fontsize=8)
    ejes[1].set(
        title="Silueta media de las particiones de Ward",
        xlabel="Número de grupos (k)",
        ylabel="Silueta media",
        ylim=(0, 1.15 * siluetas.max()),
    )
    _guardar(figura, ruta_figuras / "catch22_clusters.png")


def orden_dendrograma(enlace: np.ndarray, claves: pd.Index) -> list[str]:
    return [claves[hoja] for hoja in leaves_list(enlace)]


def figura_heatmap(
    estandarizada: pd.DataFrame,
    orden_series: list[str],
    ruta_figuras: Path = RUTA_FIGURAS,
) -> None:
    tabla = estandarizada.loc[orden_series, CARACTERISTICAS_POR_FAMILIA].T
    # El límite es el z de mayor magnitud posible con estas series, no el observado: así
    # el color significa lo mismo en esta figura y en cualquier otra del mismo tipo.
    limite = np.sqrt(len(estandarizada) - 1)

    figura, eje = plt.subplots(figsize=(7.5, 9))
    imagen = eje.imshow(tabla, cmap="RdBu_r", vmin=-limite, vmax=limite, aspect="auto")

    eje.set_xticks(range(len(orden_series)))
    eje.set_xticklabels(
        [SERIES[clave] for clave in orden_series],
        rotation=30,
        ha="right",
    )
    eje.set_yticks(range(len(tabla)))
    eje.set_yticklabels(tabla.index, fontsize=7)

    inicio = 0
    for familia in FAMILIAS_ORDENADAS:
        tamano = sum(FAMILIAS[nombre] == familia for nombre in tabla.index)
        if inicio:
            eje.axhline(inicio - 0.5, color="black", linewidth=0.8)
        eje.text(
            len(orden_series) - 0.35,
            inicio + (tamano - 1) / 2,
            familia,
            fontsize=7,
            color="dimgrey",
            va="center",
            ha="left",
        )
        inicio += tamano

    eje.set_title("Características estandarizadas por serie")
    figura.colorbar(
        imagen,
        ax=eje,
        orientation="horizontal",
        pad=0.08,
        shrink=0.7,
        label="z-score de la característica entre las siete series",
    )
    _guardar(figura, ruta_figuras / "catch22_heatmap.png")


def correlaciones(estandarizada: pd.DataFrame) -> pd.DataFrame:
    ordenada = estandarizada[CARACTERISTICAS_POR_FAMILIA]
    return ordenada.corr()


def _separadores_familia(eje: plt.Axes, nombres: list[str]) -> None:
    inicio = 0
    for familia in FAMILIAS_ORDENADAS:
        tamano = sum(FAMILIAS[nombre] == familia for nombre in nombres)
        if inicio:
            eje.axhline(inicio - 0.5, color="black", linewidth=0.6)
            eje.axvline(inicio - 0.5, color="black", linewidth=0.6)
        inicio += tamano


def figura_correlaciones(
    correlacion: pd.DataFrame,
    ruta_figuras: Path = RUTA_FIGURAS,
) -> None:
    nombres = list(correlacion.columns)

    figura, eje = plt.subplots(figsize=(9.5, 8.5))
    imagen = eje.imshow(correlacion, cmap="RdBu_r", vmin=-1, vmax=1)

    eje.set_xticks(range(len(nombres)))
    eje.set_xticklabels(nombres, rotation=90, fontsize=6)
    eje.set_yticks(range(len(nombres)))
    eje.set_yticklabels(nombres, fontsize=6)
    _separadores_familia(eje, nombres)

    eje.set_title("Correlación de Pearson entre características, sobre las siete series")
    figura.colorbar(imagen, ax=eje, shrink=0.75, label="r")
    _guardar(figura, ruta_figuras / "catch22_correlaciones.png")
