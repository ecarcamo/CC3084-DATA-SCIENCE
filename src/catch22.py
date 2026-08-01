import pandas as pd

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


def catalogo() -> pd.DataFrame:
    return pd.DataFrame(
        CATALOGO,
        columns=["caracteristica", "familia", "descripcion"],
    )
