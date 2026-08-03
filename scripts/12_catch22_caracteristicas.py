#!/usr/bin/env python
# coding: utf-8

# # Caracterización de las siete series con catch22
# 
# Este cuaderno cierra el Laboratorio 2 con el ejercicio de catch22. Extrae las 22 características canónicas de las siete series mensuales construidas en el Laboratorio 1, arma la matriz serie por característica y la analiza con PCA, clustering, mapa de calor, matriz de correlaciones y mapa de distancias entre series.
# 
# A diferencia de los cuadernos 09 y 10, que modelaron solo total y vía aérea sobre el conjunto de entrenamiento, aquí entran las siete series completas, de enero de 2009 a junio de 2026 (210 meses): el ejercicio es descriptivo y no de pronóstico, así que no hay partición que respetar. Produce `resultados/catch22_*.csv` y las figuras `catch22_*.png`.

# ## 1. La idea detrás de catch22
# 
# Comparar series por su dinámica obliga a elegir indicadores. En el cuaderno 07 los elegimos a mano: fuerza estacional, fuerza de tendencia, pendiente prepandemia, coeficiente de variación e impacto de la pandemia. Son cinco decisiones defendibles, pero arbitrarias, y nada garantiza que sean las que mejor separan estas siete series. La biblioteca `hctsa` lleva la idea al extremo opuesto y calcula miles de operaciones sobre una misma serie: exhaustivo, caro y muy redundante, porque cientos de esas operaciones miden casi lo mismo.
# 
# catch22 es el punto medio. Lubba et al. (2019) partieron de una versión filtrada de `hctsa` con 4,791 características y las evaluaron sobre 93 conjuntos de clasificación de series de tiempo, más de 147,000 series en total. Descartaron las que no superan al azar, agruparon las restantes por la similitud de su desempeño entre conjuntos —dos características que aciertan y fallan en los mismos problemas son redundantes— y conservaron un representante por grupo. De 4,791 quedaron 22. La reducción cuesta en promedio 7 % de exactitud de clasificación y devuelve un factor cercano a 1000 en tiempo de cómputo, con escalamiento casi lineal en la longitud de la serie.
# 
# Las 22 características cubren ocho familias: forma de la distribución de valores, ubicación de los eventos extremos, autocorrelación lineal, autocorrelación no lineal, contenido espectral y periodicidad, diferencias sucesivas y error de pronósticos locales, dinámica simbólica y rachas, y escalamiento de fluctuaciones. El nombre de cada una codifica la operación y sus parámetros: `CO_f1ecac` es el primer cruce de la autocorrelación por 1/e y `SB_BinaryStats_mean_longstretch1` es la racha más larga por encima de la media. La celda siguiente imprime el catálogo completo.
# 
# Un detalle que condiciona todo el ejercicio: las características se calculan sobre la serie estandarizada, así que describen forma y dinámica, no nivel ni escala. Por eso la variante `catch24` reincorpora la media y la desviación como dos características extra. Aquí se usan las 22 canónicas, que es lo que pide el enunciado.
# 
# La importancia práctica es que catch22 convierte una serie de longitud arbitraria en un vector de longitud fija e interpretable. Eso habilita el resto del ejercicio, PCA, clustering y distancias entre series, con herramienta multivariada ordinaria, y pone en el mismo plano a la serie total, con una media de 248,990 viajeros mensuales, y a vía marítima, con 5,851: la invariancia de escala evita que la magnitud domine la comparación, que es justo el problema que tuvo el comparativo del Laboratorio 1, donde cada indicador hubo que normalizarlo a mano. Y a diferencia de un vector aprendido por una red, cada coordenada tiene nombre y significado, de modo que las diferencias entre series se pueden explicar y no solo medir.
# 
# Queda una limitación declarada desde ahora: catch22 se seleccionó para clasificar series de benchmark y varias de sus características necesitan series largas. Las nuestras tienen 210 observaciones mensuales, así que las dos de escalamiento de fluctuaciones, que ajustan pendientes sobre varias escalas temporales, y las que dependen de la matriz de transición son las más expuestas a resultar inestables o constantes. El inciso 2 lo verifica antes de usarlas.
# 
# > Lubba, C. H., Sethi, S. S., Knaute, P., Schultz, S. R., Fulcher, B. D. y Jones, N. S. (2019). catch22: CAnonical Time-series CHaracteristics. *Data Mining and Knowledge Discovery*, 33(6), 1821-1852. arXiv:1901.10200.
# 
# La implementación usada es `pycatch22`, el binding oficial de la versión en C de los autores, agregado a `requirements-lab2.txt`.

# In[1]:


from importlib.metadata import version
from pathlib import Path
import sys

RAIZ = Path.cwd()
if not (RAIZ / "src").exists():
    RAIZ = RAIZ.parent
sys.path.insert(0, str(RAIZ))

from src.catch22 import catalogo

print(f"pycatch22 {version('pycatch22')}")

tabla = catalogo()
print(f"{len(tabla)} características en {tabla['familia'].nunique()} familias")
for familia, grupo in tabla.groupby("familia", sort=False):
    print(f"\n{familia}")
    for _, fila in grupo.iterrows():
        print(f"  {fila['caracteristica']:<44s}{fila['descripcion']}")


# ## 2. Extracción de las 22 características
# 
# Las características se calculan sobre la serie completa, los 210 meses de enero de 2009 a junio de 2026, y no sobre el conjunto de entrenamiento. Los cuadernos 09 y 10 respetaron la partición porque pronosticaban; aquí el objetivo es describir y comparar la dinámica de las siete series, no predecir, así que apartar 63 meses solo desperdiciaría información. Las series por país de residencia y vía marítima tienen meses en cero, y por eso quedaron fuera del modelado LSTM, que dependía de `log1p`; catch22 no necesita esa transformación, así que las siete entran completas.
# 
# `extraer_serie` llama a `pycatch22.catch22_all` y devuelve las 22 características indexadas por nombre, después de comprobar que la biblioteca las entregó en el orden del catálogo. La comprobación no es adorno: el catálogo del inciso 1 asigna familia y descripción por nombre, de modo que un reordenamiento en una versión distinta de `pycatch22` dejaría la matriz mal etiquetada sin que nada fallara.
# 
# La celda siguiente verifica además tres cosas antes de que el resto del cuaderno dependa de ellas.
# 
# - **Invariancia de escala.** `catch22_all` estandariza la serie internamente, así que `2 · serie + 1000` devuelve exactamente los mismos 22 valores. Eso es lo que hace comparable a la serie total, con media de 248,990 viajeros mensuales, con vía marítima, con 5,851, y lo que implica que ni el nivel ni la dispersión entran en la matriz: lo que queda es forma y dinámica.
# - **Ausencia de valores faltantes.** Ninguna de las 154 celdas resulta NaN, ni en las series con meses en cero.
# - **Variabilidad entre series.** Ninguna de las 22 características toma el mismo valor en las siete series. Esto matiza la limitación anunciada en el inciso 1: incluso las dos de escalamiento de fluctuaciones, que son las que más longitud exigen, discriminan entre series. Las 22 se conservan, y el inciso 4 podrá estandarizarlas por columna sin divisiones entre cero.

# In[2]:


import numpy as np
import pandas as pd

from src.catch22 import extraer_serie
from src.utils import SERIES, cargar_serie

completas = {clave: cargar_serie(clave, "completa") for clave in SERIES}
extraidas = pd.DataFrame(
    {clave: extraer_serie(serie) for clave, serie in completas.items()}
).T

assert extraidas.shape == (len(SERIES), len(tabla))
assert np.allclose(extraidas.loc["total"], extraer_serie(2 * completas["total"] + 1000))

meses = sorted({len(serie) for serie in completas.values()})
constantes = list(extraidas.columns[extraidas.std(ddof=0) == 0])
print(f"series: {extraidas.shape[0]}, características: {extraidas.shape[1]}")
print(f"meses por serie: {meses}")
print(f"NaN en la extracción: {int(extraidas.isna().sum().sum())}")
print(f"características constantes entre series: {constantes or 'ninguna'}")
print("invariancia de escala: 2 · serie + 1000 devuelve los mismos 22 valores")

catalogo_indexado = tabla.set_index("caracteristica")
ejemplo = pd.DataFrame(
    {
        "valor": extraidas.loc["total"].round(4),
        "familia": catalogo_indexado["familia"],
        "descripcion": catalogo_indexado["descripcion"],
    }
)
print(f"\nvector de la serie total\n{ejemplo.to_string()}")


# ## 3. Matriz serie por característica
# 
# La matriz lleva las siete series en las filas y las 22 características en las columnas, que es la forma que pide el enunciado y también la que espera `scikit-learn`: una observación por fila. `matriz_caracteristicas` devuelve solo el bloque numérico, indexado por la clave de la serie. La etiqueta y la categoría se agregan al escribir `resultados/catch22_caracteristicas.csv`, con el mismo formato de `comparativo_series.csv` del Laboratorio 1, y las categorías se reutilizan de `src/comparativo.py` en lugar de redefinirlas, para que el inciso 10, que pregunta si las series de una misma categoría se agrupan, use exactamente la clasificación del comparativo anterior.
# 
# La matriz se imprime transpuesta, con las características en las filas, porque 22 columnas no caben legibles a lo ancho; es el mismo recurso que usa el cuaderno 07 para los perfiles estacionales.
# 
# Así impresa se ve el problema que resuelve el inciso 4: las columnas viven en escalas incomparables. `SB_BinaryStats_mean_longstretch1` va de 9 a 50 meses y `PD_PeriodicityWang_th0_01` de 2 a 11, mientras `SB_TransitionMatrix_3ac_sumdiagcov` se mueve entre 0.006 y 0.111. Una distancia euclidiana sobre la matriz cruda quedaría decidida por dos o tres columnas y las diecinueve restantes no aportarían nada.

# In[3]:


from src.catch22 import matriz_caracteristicas
from src.comparativo import CATEGORIAS
from src.utils import RUTA_RESULTADOS

matriz = matriz_caracteristicas(completas)

assert list(matriz.index) == list(SERIES)
assert list(matriz.columns) == list(tabla["caracteristica"])

exportable = matriz.reset_index()
exportable.insert(1, "etiqueta", [SERIES[clave] for clave in matriz.index])
exportable.insert(2, "categoria", [CATEGORIAS[clave] for clave in matriz.index])
exportable.to_csv(RUTA_RESULTADOS / "catch22_caracteristicas.csv", index=False)

print(f"matriz {matriz.shape[0]} x {matriz.shape[1]} en resultados/catch22_caracteristicas.csv")
print(matriz.T.round(3).to_string())

rangos = (matriz.max() - matriz.min()).sort_values(ascending=False)
print("\nrecorrido de cada característica entre las siete series")
print(rangos.round(3).to_string())


# ## 4. Estandarización de las características
# 
# En este ejercicio conviven dos estandarizaciones que actúan en direcciones distintas y conviene no confundirlas.
# 
# | | Qué estandariza | Quién la aplica | Para qué |
# |---|---|---|---|
# | Interna de catch22 | Cada serie, sobre sus 210 meses | `pycatch22`, verificado en el inciso 2 | Que el nivel y la escala de la serie no entren en las características |
# | La de este inciso | Cada característica, sobre las siete series | `StandardScaler` | Que ninguna columna domine distancias, PCA ni clustering |
# 
# La segunda es indispensable por lo que muestra el recorrido impreso en el inciso 3: `SB_BinaryStats_mean_longstretch1` varía 41 meses entre series y `CO_f1ecac` varía 16, mientras `SB_TransitionMatrix_3ac_sumdiagcov` varía 0.106. Sobre la matriz cruda, esas dos columnas decidirían casi solas cualquier distancia euclidiana y las otras veinte no aportarían nada. Después de estandarizar, las 22 entran con el mismo peso a priori. Se usa `StandardScaler` de `scikit-learn`, la misma biblioteca con la que el Laboratorio 2 escaló las series para la LSTM, con su convención de dividir entre la desviación poblacional (`ddof=0`).
# 
# Hay una consecuencia estadística que conviene declarar antes de interpretar el inciso 5: con siete observaciones por columna, el z-score de mayor magnitud posible es √6 ≈ 2.449. En las características donde una sola serie se despega del resto, como las dos de escalamiento de fluctuaciones, esa serie queda cerca del tope y las otras seis comprimidas en un rango estrecho de z positivos. No invalida el análisis, pero explica por qué esas columnas van a pesar tanto en las primeras componentes y en el mapa de distancias.
# 
# Un último punto que evita una confusión frecuente: la matriz de correlaciones entre características del inciso 5 sale idéntica sobre la matriz cruda o sobre la estandarizada, porque la correlación de Pearson es invariante a transformaciones afines por columna. La estandarización cambia el PCA, el clustering, las distancias y el mapa de calor; esa correlación, no.

# In[4]:


from src.catch22 import estandarizar

estandarizada = estandarizar(matriz)

assert np.allclose(estandarizada.mean(), 0)
assert np.allclose(estandarizada.std(ddof=0), 1)

exportable_z = estandarizada.reset_index()
exportable_z.insert(1, "etiqueta", [SERIES[clave] for clave in estandarizada.index])
exportable_z.insert(2, "categoria", [CATEGORIAS[clave] for clave in estandarizada.index])
exportable_z.to_csv(RUTA_RESULTADOS / "catch22_estandarizado.csv", index=False)

print("cada característica queda con media 0 y desviación 1")
print(f"z de mayor magnitud posible con {len(estandarizada)} series: {np.sqrt(len(estandarizada) - 1):.3f}")
print(estandarizada.T.round(3).to_string())

print("\ncaracterística más extrema de cada serie")
for clave, fila in estandarizada.iterrows():
    extrema = fila.abs().idxmax()
    print(f"  {SERIES[clave]:<15s} {extrema:<44s} z = {fila[extrema]:+.2f}")


# ## 5. Análisis sobre la matriz estandarizada
# 
# Los cinco análisis que pide el enunciado parten de la misma matriz 7 × 22 estandarizada del inciso 4. Antes de entrar, la restricción que atraviesa todo el inciso: hay **siete observaciones**. Eso acota el PCA a seis componentes, deja cualquier prueba de significancia sin poder y hace que un solo valor extremo mueva visiblemente los resultados. El análisis es descriptivo, y así se presenta.
# 
# La interpretación de fondo, qué series se parecen, qué características discriminan, qué grupos hay y cuáles series son atípicas, corresponde a los incisos 7 al 13. Estas celdas producen y describen la evidencia.

# ### 5.1 Análisis de componentes principales
# 
# El PCA se calcula sobre la matriz estandarizada, lo que equivale a un PCA sobre la matriz de correlaciones: cada característica llega con la misma varianza inicial y ninguna domina por su escala. Se piden seis componentes porque la matriz centrada de siete series tiene rango seis; una séptima componente tendría varianza numéricamente nula.
# 
# La figura tiene dos paneles. El primero es la varianza explicada por componente con su acumulada. El segundo es el plano PC1-PC2 con las siete series y, como flechas, las ocho características de mayor contribución al plano, medida como la norma de sus cargas en PC1 y PC2. Las flechas son lo que hace del gráfico un biplot: una serie situada en la dirección de una flecha puntúa alto en esa característica, y eso es lo que permitirá responder el inciso 8 con evidencia y no por intuición.
# 
# Las coordenadas de las siete series quedan en `resultados/catch22_pca.csv` y las cargas de las tres primeras componentes, con la familia de cada característica, en `resultados/catch22_pca_cargas.csv`.

# In[5]:


from src.catch22 import FAMILIAS, analizar_pca, figura_pca

coordenadas, cargas, varianza = analizar_pca(estandarizada)
figura_pca(coordenadas, cargas, varianza)

exportable_pca = coordenadas.reset_index()
exportable_pca.insert(1, "etiqueta", [SERIES[clave] for clave in coordenadas.index])
exportable_pca.insert(2, "categoria", [CATEGORIAS[clave] for clave in coordenadas.index])
exportable_pca.round(4).to_csv(RUTA_RESULTADOS / "catch22_pca.csv", index=False)

cargas_exportables = cargas[["pc1", "pc2", "pc3"]].copy()
cargas_exportables.insert(0, "familia", pd.Series(FAMILIAS))
cargas_exportables.index.name = "caracteristica"
cargas_exportables.round(4).to_csv(RUTA_RESULTADOS / "catch22_pca_cargas.csv")

print("varianza explicada")
print(
    pd.DataFrame(
        {"varianza_%": 100 * varianza, "acumulada_%": 100 * varianza.cumsum()}
    )
    .round(1)
    .to_string()
)

print("\ncoordenadas de las series")
print(coordenadas.round(3).to_string())

contribucion = np.hypot(cargas["pc1"], cargas["pc2"]).sort_values(ascending=False)
resumen_cargas = pd.DataFrame(
    {
        "contribucion": contribucion,
        "pc1": cargas["pc1"],
        "pc2": cargas["pc2"],
        "familia": pd.Series(FAMILIAS),
    }
).loc[contribucion.index]
print("\ncaracterísticas de mayor contribución al plano PC1-PC2")
print(resumen_cargas.head(8).round(3).to_string())


# ### 5.2 Clustering
# 
# El agrupamiento corre sobre las 22 características estandarizadas, no sobre las coordenadas del PCA. Reducir a dos componentes y agrupar después descartaría el 36.6 % de la varianza antes de medir la primera distancia; el PCA sirve para ver el resultado, no para producirlo. Así el dendrograma y el mapa de distancias del inciso 5.5 describen el mismo espacio.
# 
# El método es jerárquico aglomerativo con enlace de Ward sobre distancia euclidiana. Con siete series lo informativo es el orden en que se fusionan y a qué distancia, no una partición fija, y Ward es el enlace coherente con la distancia que se reporta en 5.5. El número de grupos se elige por el coeficiente de silueta de las particiones de Ward para k de 2 a 5. Con siete puntos la silueta es una medida gruesa: sirve para ordenar candidatos, no para sostener que existe un número óptimo de grupos.
# 
# Como verificación se corre k-means con ese mismo k, `n_init=10` y semilla 42, y se compara contra Ward con el índice de Rand ajustado. Si los dos métodos devuelven la misma partición, el resultado no depende del algoritmo, que es justo lo que el inciso 9 necesita saber antes de hablar de grupos naturales. Se guarda además la silueta de cada serie por separado: una serie con silueta cercana a cero no pertenece con claridad a ningún grupo, y ese es el primer indicio cuantitativo para el inciso 11.
# 
# El corte del dendrograma se pinta en el umbral exacto que produce el k elegido, de modo que los colores del árbol son los grupos que se reportan en `resultados/catch22_clusters.csv`.

# In[6]:


from sklearn.metrics import adjusted_rand_score

from src.catch22 import agrupar, figura_clusters

enlace, grupos, siluetas = agrupar(estandarizada)
figura_clusters(enlace, grupos, siluetas)

k = int(siluetas.idxmax())
rand = adjusted_rand_score(grupos["grupo_ward"], grupos["grupo_kmeans"])

exportable_grupos = grupos.reset_index()
exportable_grupos.insert(1, "etiqueta", [SERIES[clave] for clave in grupos.index])
exportable_grupos.insert(2, "categoria", [CATEGORIAS[clave] for clave in grupos.index])
exportable_grupos.round(4).to_csv(RUTA_RESULTADOS / "catch22_clusters.csv", index=False)

print("silueta media por número de grupos")
print(siluetas.round(4).to_string())
print(f"\nk elegido: {k}")
print(f"Rand ajustado entre Ward y k-means: {rand:.3f}")

print("\ngrupos de Ward")
for numero, bloque in grupos.groupby("grupo_ward"):
    integrantes = ", ".join(SERIES[clave] for clave in bloque.index)
    print(f"  grupo {numero}: {integrantes}")

print("\ngrupos de k-means")
for numero, bloque in grupos.groupby("grupo_kmeans"):
    integrantes = ", ".join(SERIES[clave] for clave in bloque.index)
    print(f"  grupo {numero}: {integrantes}")

print("\nsilueta por serie")
for clave, fila in grupos.sort_values("silueta").iterrows():
    print(
        f"  {SERIES[clave]:<15s} grupo {int(fila['grupo_ward'])}"
        f"  silueta {fila['silueta']:+.3f}"
    )

print("\naltura de las fusiones de Ward")
print(np.round(np.sort(enlace[:, 2]), 3))


# La silueta es casi plana entre k = 2, 3 y 4 (0.153, 0.163 y 0.161), así que el k = 3 elegido gana por 0.002 sobre k = 4 y no debe leerse como un óptimo nítido. Ward y k-means discrepan en una sola serie, la total: Ward la fusiona con vía aérea y vía marítima, y k-means la coloca con vía terrestre, El Salvador y Honduras. Es también la única serie con silueta negativa, −0.102, es decir la única que queda más cerca del grupo vecino que del propio. El índice de Rand ajustado cae a 0.444 por ese único cambio, penalización esperable con siete observaciones. Las otras seis series salen idénticas con los dos métodos, y Estados Unidos aparece aislado en ambos.

# ### 5.3 Mapa de calor de las características
# 
# La figura dibuja la matriz estandarizada completa. Las 22 características van en las filas, agrupadas por familia y separadas con líneas, y las siete series en las columnas, ordenadas según las hojas del dendrograma de 5.2 y no según `SERIES`, de modo que los bloques de color coincidan con los grupos ya reportados. Es la misma orientación con la que se imprimieron las matrices de los incisos 3 y 4, así que la figura y las tablas se leen igual.
# 
# La escala de color es divergente y está fijada en ±2.449, el z de mayor magnitud posible con siete series, en lugar de ajustarse al máximo observado. Con eso, un rojo intenso significa siempre lo mismo y el blanco es siempre el promedio de las siete series en esa característica.
# 
# No hay CSV nuevo: la matriz dibujada es exactamente `resultados/catch22_estandarizado.csv`.

# In[7]:


from src.catch22 import figura_heatmap, orden_dendrograma

orden = orden_dendrograma(enlace, estandarizada.index)
figura_heatmap(estandarizada, orden)

print("orden de las columnas, el de las hojas del dendrograma")
print(" | ".join(SERIES[clave] for clave in orden))

extremas = estandarizada.stack()
extremas = extremas[extremas.abs() > 2].sort_values()
print("\nceldas con |z| > 2, las que dominan el mapa")
for (clave, caracteristica), valor in extremas.items():
    print(f"  {SERIES[clave]:<15s} {caracteristica:<44s} z = {valor:+.2f}")


# ### 5.4 Matriz de correlaciones entre características
# 
# La matriz es la correlación de Pearson entre las 22 características, tomando las siete series como observaciones, en el mismo orden por familia del mapa de calor para que las dos figuras se lean juntas. Se calcula sobre la matriz estandarizada, aunque el resultado es idéntico al de la matriz cruda por la invariancia anotada en el inciso 4.
# 
# Aquí hace falta una advertencia, porque la figura invita a sobreinterpretar. Cada coeficiente proviene de **siete puntos**. Con n = 7 el umbral nominal de significancia al 5 % es |r| ≈ 0.754, y la matriz tiene 231 pares distintos, así que por puro azar cabe esperar más de diez pares que cruzarían ese umbral sin que exista ninguna relación. La matriz sirve para detectar redundancia gruesa entre características *en este conjunto concreto de siete series*, no para afirmar dependencias generales entre ellas.
# 
# Conviene distinguir esto del diseño de catch22. Sus autores minimizaron la redundancia por similitud de desempeño en clasificación sobre 93 conjuntos de datos, no por correlación lineal en siete series mensuales de turismo. Que dos características salgan casi colineales aquí no contradice el diseño: significa que en estas siete series, y solo en ellas, aportan la misma información.

# In[8]:


from src.catch22 import correlaciones, figura_correlaciones

correlacion = correlaciones(estandarizada)
figura_correlaciones(correlacion)
correlacion.round(4).to_csv(RUTA_RESULTADOS / "catch22_correlaciones.csv")

triangulo = np.triu_indices(len(correlacion), k=1)
pares = pd.Series(
    correlacion.to_numpy()[triangulo],
    index=pd.MultiIndex.from_arrays(
        [correlacion.index[triangulo[0]], correlacion.columns[triangulo[1]]]
    ),
)

print(f"pares distintos: {len(pares)}")
print(f"correlación media en valor absoluto: {pares.abs().mean():.3f}")
print(f"pares con |r| >= 0.9: {int((pares.abs() >= 0.9).sum())}")
print(f"pares con |r| >= 0.95: {int((pares.abs() >= 0.95).sum())}")

print("\npares con |r| >= 0.95")
fuertes = pares[pares.abs() >= 0.95].sort_values(key=abs, ascending=False)
for (una, otra), valor in fuertes.items():
    print(f"  {valor:+.3f}  {una} / {otra}")


# ### 5.5 Mapa de distancias entre series
# 
# El último de los cinco análisis que pide el inciso 2.4 es la matriz de distancias euclidianas entre las siete series, calculada sobre la misma matriz estandarizada de 22 características que alimentó el PCA y el clustering. Es la contraparte numérica del dendrograma de 5.2: Ward decide con esta misma distancia qué series fusionar primero, y aquí se ve el valor exacto detrás de cada fusión, entre todos los pares y no solo entre los que Ward unió.
# 
# `distancias` aplica `scipy.spatial.distance.pdist` con métrica euclidiana sobre las filas de la matriz estandarizada y devuelve la matriz cuadrada de 7 × 7 con las claves de las series en filas y columnas. La diagonal es cero por construcción, la matriz es simétrica, y por eso `figura_distancias` solo necesita anotar el triángulo completo, sin ocultar ninguna mitad: a diferencia del heatmap y la matriz de correlaciones, aquí no hay signo que perder al plegar la matriz.
# 
# Las filas y columnas se ordenan igual que en el mapa de calor de 5.3, según las hojas del dendrograma de Ward, para que las tres figuras, dendrograma, mapa de calor y mapa de distancias, cuenten la misma historia con el mismo orden de series. La escala de color es secuencial y no divergente, porque una distancia euclidiana no tiene signo: cero es el extremo de similitud máxima, no un punto medio neutro entre dos direcciones.
# 
# La matriz completa queda en `resultados/catch22_distancias.csv`.

# In[9]:


from src.catch22 import distancias, figura_distancias

distancia = distancias(estandarizada)
figura_distancias(distancia, orden)
distancia.round(4).to_csv(RUTA_RESULTADOS / "catch22_distancias.csv")

print("matriz de distancias euclidianas (orden del dendrograma)")
print(distancia.loc[orden, orden].rename(columns=SERIES, index=SERIES).round(2).to_string())

triangulo = np.triu_indices(len(distancia), k=1)
pares_dist = pd.Series(
    distancia.to_numpy()[triangulo],
    index=pd.MultiIndex.from_arrays(
        [distancia.index[triangulo[0]], distancia.columns[triangulo[1]]]
    ),
)

mas_cercano = pares_dist.idxmin()
mas_lejano = pares_dist.idxmax()
print(f"\npar más similar:  {SERIES[mas_cercano[0]]} / {SERIES[mas_cercano[1]]}  d = {pares_dist[mas_cercano]:.3f}")
print(f"par más distinto: {SERIES[mas_lejano[0]]} / {SERIES[mas_lejano[1]]}  d = {pares_dist[mas_lejano]:.3f}")

print("\ndistancia media de cada serie al resto (indicio de atipicidad)")
medias = (distancia.sum() / (len(distancia) - 1)).sort_values(ascending=False)
for clave, valor in medias.items():
    print(f"  {SERIES[clave]:<15s} {valor:.3f}")


# ## 6. Análisis e interpretación
# 
# Los incisos 5.1 a 5.5 produjeron la evidencia; los que siguen la interpretan. Antes de responder conviene consolidar en una sola tabla lo que cada análisis dijo de cada serie, porque las preguntas de los incisos 7 a 13 se responden cruzando esas piezas y no mirándolas por separado: el PCA ubica, el clustering agrupa, la matriz de distancias mide y el mapa de calor explica *por qué*.
# 
# La tabla siguiente reúne, para cada una de las siete series, siete piezas de evidencia ya calculadas:
# 
# | Columna | De dónde viene | Qué responde |
# |---|---|---|
# | `grupo_ward`, `grupo_kmeans` | Inciso 5.2 | A qué grupo pertenece y si el resultado depende del algoritmo |
# | `silueta` | Inciso 5.2 | Qué tan bien pertenece a su grupo; cerca de 0 o negativa significa que no pertenece con claridad |
# | `pc1`, `pc2` | Inciso 5.1 | Dónde queda en el plano principal, que explica el 63.4 % de la varianza |
# | `distancia_media` | Inciso 5.5 | Qué tan lejos está del resto en promedio; el indicador directo de atipicidad |
# | `vecino_mas_cercano`, `distancia_vecino` | Inciso 5.5 | Con qué serie se parece más y cuánto |
# | `caracteristica_extrema`, `z_extremo` | Inciso 5.3 | Qué característica la separa más del promedio de las siete |
# 
# Una advertencia que atraviesa todos los incisos que siguen y que no se repetirá en cada uno. Hay **siete series**. Ningún resultado de esta sección tiene respaldo inferencial: no hay pruebas de hipótesis con poder, los intervalos de confianza serían inútiles y una sola serie distinta cambiaría varias de las conclusiones. Todo lo que sigue es descriptivo, y las afirmaciones se acompañan del número que las sostiene para que el lector juzgue qué tan firme es cada una.
# 
# La tabla queda en `resultados/catch22_resumen_series.csv`.

# In[10]:


vecinos = {}
for clave in distancia.index:
    otras = distancia.loc[clave].drop(clave)
    vecinos[clave] = (otras.idxmin(), otras.min())

extremas_serie = {clave: fila.abs().idxmax() for clave, fila in estandarizada.iterrows()}

resumen = pd.DataFrame(
    {
        "etiqueta": [SERIES[clave] for clave in estandarizada.index],
        "categoria": [CATEGORIAS[clave] for clave in estandarizada.index],
        "grupo_ward": grupos["grupo_ward"],
        "grupo_kmeans": grupos["grupo_kmeans"],
        "silueta": grupos["silueta"],
        "pc1": coordenadas["pc1"],
        "pc2": coordenadas["pc2"],
        "distancia_media": distancia.sum() / (len(distancia) - 1),
        "vecino_mas_cercano": [SERIES[vecinos[clave][0]] for clave in estandarizada.index],
        "distancia_vecino": [vecinos[clave][1] for clave in estandarizada.index],
        "caracteristica_extrema": [extremas_serie[clave] for clave in estandarizada.index],
        "z_extremo": [
            estandarizada.loc[clave, extremas_serie[clave]] for clave in estandarizada.index
        ],
    },
    index=estandarizada.index,
)

resumen.round(4).to_csv(RUTA_RESULTADOS / "catch22_resumen_series.csv")

print("evidencia consolidada por serie")
print(
    resumen[
        [
            "etiqueta",
            "categoria",
            "grupo_ward",
            "grupo_kmeans",
            "silueta",
            "pc1",
            "pc2",
            "distancia_media",
        ]
    ]
    .round(3)
    .to_string()
)

print("\nvecino más cercano y característica más extrema de cada serie")
for clave, fila in resumen.iterrows():
    print(
        f"  {fila['etiqueta']:<15s} vecino {fila['vecino_mas_cercano']:<15s} d = {fila['distancia_vecino']:.2f}"
        f"   {fila['caracteristica_extrema']:<44s} z = {fila['z_extremo']:+.2f}"
    )


# ## 7. ¿Cuáles series presentan comportamientos más similares?
# 
# La pregunta admite una respuesta directa porque el inciso 5.5 ya midió la similitud entre los 21 pares posibles. Pero una distancia sola no convence: la matriz de 5.5, el orden de fusión del dendrograma de 5.2 y la posición en el plano principal de 5.1 son tres lecturas del mismo espacio de 22 dimensiones, y solo si las tres coinciden puede afirmarse que dos series se parecen y no que una proyección particular las acercó por casualidad.
# 
# La celda siguiente hace exactamente esa verificación cruzada. Ordena los 21 pares por distancia euclidiana, marca cuáles quedaron en el mismo grupo de Ward, reconstruye la secuencia completa de fusiones del dendrograma con nombres de series y compara el orden de similitud del espacio completo contra el del plano PC1-PC2 con la correlación de Spearman. Si el plano reordenara los pares, las flechas y posiciones de la figura de 5.1 no servirían para responder esta pregunta; si los respeta, la figura puede leerse como un mapa de similitud y no solo como un resumen de varianza.

# In[11]:


from scipy.stats import spearmanr

distancia_plano = distancias(coordenadas[["pc1", "pc2"]])
pares_plano = pd.Series(
    distancia_plano.to_numpy()[triangulo],
    index=pares_dist.index,
)

mismo_grupo = [
    grupos.loc[una, "grupo_ward"] == grupos.loc[otra, "grupo_ward"]
    for una, otra in pares_dist.index
]

ranking = pd.DataFrame(
    {
        "par": [f"{SERIES[una]} / {SERIES[otra]}" for una, otra in pares_dist.index],
        "distancia": pares_dist.to_numpy(),
        "distancia_plano_pc1_pc2": pares_plano.to_numpy(),
        "mismo_grupo_ward": mismo_grupo,
    },
    index=pares_dist.index,
).sort_values("distancia")

print("los 21 pares ordenados por similitud")
print(ranking.reset_index(drop=True).round(3).to_string())

rho, _ = spearmanr(ranking["distancia"], ranking["distancia_plano_pc1_pc2"])
print(f"\nSpearman entre la distancia en 22-D y la distancia en el plano PC1-PC2: {rho:.3f}")

plano_vecino = {
    clave: distancia_plano.loc[clave].drop(clave).idxmin() for clave in distancia_plano.index
}
acuerdos = sum(plano_vecino[clave] == vecinos[clave][0] for clave in vecinos)
print(f"series cuyo vecino más cercano es el mismo en 22-D y en el plano: {acuerdos} de {len(vecinos)}")

print("\nsecuencia de fusiones del dendrograma de Ward")
nombres_fusion = {posicion: SERIES[clave] for posicion, clave in enumerate(estandarizada.index)}
for paso, fila in enumerate(enlace, start=len(estandarizada)):
    una, otra, altura = int(fila[0]), int(fila[1]), fila[2]
    nombres_fusion[paso] = f"({nombres_fusion[una]} + {nombres_fusion[otra]})"
    print(f"  altura {altura:6.3f}   {nombres_fusion[paso]}")


# ### Respuesta
# 
# **El par más similar es vía terrestre y El Salvador, con una distancia de 3.77**, la menor de las 21 y un 21 % por debajo de la siguiente. Las tres fuentes de evidencia coinciden sin excepción:
# 
# - **Matriz de distancias (5.5).** 3.77 contra una distancia media de 7.02 entre los 21 pares; ningún otro par baja de 4.77.
# - **Clustering (5.2).** Es la **primera fusión del dendrograma**, a altura 3.766, y las dos series quedan en el mismo grupo de Ward *y* en el mismo grupo de k-means, es decir sobreviven al cambio de algoritmo.
# - **PCA (5.1).** Quedan contiguas en el plano principal, ambas con PC1 negativo (−1.54 y −3.02), y son vecinas mutuas también en la proyección, a 1.53 en el plano.
# 
# Detrás de la coincidencia estadística hay una explicación de dominio que el Laboratorio 1 ya había documentado: **El Salvador es el principal país de residencia que ingresa por vía terrestre**, y los pasos fronterizos de mayor tráfico del país —Valle Nuevo, San Cristóbal, Pedro de Alvarado— son precisamente los salvadoreños. Las dos series no son independientes: la salvadoreña es una fracción dominante de la terrestre, así que comparten calendario, estacionalidad y respuesta a la pandemia casi por construcción. catch22 lo detecta sin saber nada de fronteras, solo de la forma de las dos curvas.
# 
# **El segundo par más similar es El Salvador y Honduras, a 4.77.** Junto con vía terrestre y Honduras (6.17, sexto lugar) completan el triángulo centroamericano-terrestre: las tres distancias internas de ese trío están entre las seis menores de la tabla, y es el bloque que el inciso 9 describe como el grupo más cohesionado del conjunto.
# 
# **En tercer y cuarto lugar aparece la serie total, con vía terrestre (5.02) y con vía aérea (5.24)**, y esa doble cercanía tiene una lectura aritmética antes que dinámica: la serie total es la suma de sus componentes, así que queda a medio camino entre las dos vías que la dominan sin parecerse de manera particular a ninguna. Es la razón de que su silueta sea negativa (−0.102) y de que Ward y k-means discrepen justamente en ella: Ward la fusiona con vía aérea, su vecino en el plano, y k-means la coloca con vía terrestre, su vecino real en las 22 dimensiones.
# 
# Sobre la validez de leer el plano principal como mapa de similitud: la correlación de Spearman entre las distancias en el espacio completo de 22 dimensiones y las distancias en el plano PC1-PC2 es **0.934**, es decir la proyección conserva el orden de similitud casi intacto pese a dejar fuera el 36.6 % de la varianza. Aun así **solo 5 de 7 series conservan su vecino más cercano exacto** al proyectar, y las dos excepciones son informativas: total pasa de vía terrestre a vía aérea y Estados Unidos de El Salvador a vía terrestre, en ambos casos entre candidatos separados por menos de 0.1 en el espacio real (5.02 contra 5.24; 6.78 contra 6.87). El plano es confiable para el orden grueso y no para desempates finos, y por eso la respuesta se ancla en la matriz de distancias y usa el PCA como corroboración, y no al revés.

# ## 8. ¿Qué características fueron las más importantes para diferenciar las series?
# 
# La pregunta tiene una trampa que conviene desarmar antes de responderla. La tentación es medir importancia por varianza, pero después del inciso 4 **las 22 características tienen exactamente la misma varianza**, uno, por construcción. Y la consecuencia es más fuerte de lo que parece: la contribución de cada característica a la suma de distancias al cuadrado entre los 21 pares es
# 
# $$\sum_{i<j} (z_{ik} - z_{jk})^2 = n^2 \, \mathrm{Var}(z_k) = 49$$
# 
# para *toda* característica $k$. Ninguna aporta más que otra al total. Lo que cambia entre ellas no es cuánto aportan sino **cómo reparten** ese aporte fijo: si lo concentran en apartar una sola serie de las otras seis, o si lo reparten separando bloques de series entre sí. Son dos nociones distintas de importancia y responden a preguntas distintas, así que se miden por separado.
# 
# | Medida | Qué mide | Qué tipo de característica premia |
# |---|---|---|
# | `comunalidad_plano` = $r^2_{PC1} + r^2_{PC2}$ | Varianza que la característica comparte con el plano principal | Las que participan en la estructura dominante del conjunto |
# | `razon_f_ward` | Varianza entre los grupos de Ward sobre varianza dentro de ellos | Las que separan bloques de series |
# | `brecha_z` | Distancia entre el $|z|$ mayor y el segundo mayor | Las que aíslan una única serie del resto |
# 
# La razón F se reporta como estadístico descriptivo y **no** como prueba de hipótesis: los grupos de Ward se estimaron con estas mismas 22 características, así que la F está inflada por construcción y su valor *p* no significaría nada. Sirve para ordenar características entre sí bajo un mismo sesgo, no para declarar significancia.
# 
# La tabla completa queda en `resultados/catch22_importancia.csv` y la figura `catch22_importancia.png` muestra los dos rankings lado a lado.

# In[12]:


from src.catch22 import figura_importancia, importancia

importancias = importancia(estandarizada, coordenadas, grupos)
figura_importancia(importancias)
importancias.round(4).to_csv(RUTA_RESULTADOS / "catch22_importancia.csv")

constante = np.array(
    [
        (np.subtract.outer(estandarizada[nombre].to_numpy(), estandarizada[nombre].to_numpy()) ** 2).sum() / 2
        for nombre in estandarizada.columns
    ]
)
print(f"aporte de cada característica a la suma de distancias al cuadrado: "
      f"entre {constante.min():.1f} y {constante.max():.1f} (n² · var = {len(estandarizada) ** 2})")

print("\ncaracterísticas ordenadas por varianza compartida con el plano principal")
print(
    importancias[["familia", "r_pc1", "r_pc2", "comunalidad_plano"]]
    .head(10)
    .round(3)
    .to_string()
)

print("\ncomposición de PC1 y PC2, correlaciones mayores a 0.7 en valor absoluto")
for componente in ("r_pc1", "r_pc2"):
    fuertes = importancias[importancias[componente].abs() >= 0.7][componente]
    print(f"\n  {componente.upper()[2:]}")
    for nombre, valor in fuertes.sort_values(ascending=False).items():
        print(f"    {valor:+.3f}  {nombre}")

print("\ncaracterísticas que más separan los grupos de Ward")
print(
    importancias.nlargest(6, "razon_f_ward")[
        ["familia", "razon_f_ward", "brecha_z", "serie_responsable"]
    ]
    .round(3)
    .to_string()
)

print("\ncaracterísticas que aíslan una sola serie")
print(
    importancias.nlargest(6, "brecha_z")[
        ["familia", "brecha_z", "z_maximo", "serie_responsable", "razon_f_ward"]
    ]
    .round(3)
    .to_string()
)

print("\ncaracterísticas que menos aportaron")
print(
    importancias.nsmallest(4, "comunalidad_plano")[
        ["familia", "comunalidad_plano", "razon_f_ward", "brecha_z"]
    ]
    .round(3)
    .to_string()
)
print("\nrecorrido en unidades originales de las dos menos informativas")
for nombre in importancias.nsmallest(2, "comunalidad_plano").index:
    print(f"  {nombre:<44s} {matriz[nombre].min():.3f} a {matriz[nombre].max():.3f}")


# ### Respuesta
# 
# No hay una lista única, porque las características importan de tres maneras distintas y cada una responde a una pregunta diferente.
# 
# **1. Las que construyen el eje dominante (PC1, 39.2 % de la varianza).** El eje se define por un contraste limpio entre dos bloques de características que apuntan a lo mismo:
# 
# | Lado positivo de PC1 | r | Lado negativo de PC1 | r |
# |---|---|---|---|
# | `FC_LocalSimple_mean3_stderr` | +0.958 | `CO_f1ecac` | −0.910 |
# | `SP_Summaries_welch_rect_centroid` | +0.899 | `CO_HistogramAMI_even_2_5` | −0.870 |
# | `FC_LocalSimple_mean1_tauresrat` | +0.892 | `SP_Summaries_welch_rect_area_5_1` | −0.801 |
# | `DN_OutlierInclude_n_001_mdrmd` | +0.855 | `SB_BinaryStats_mean_longstretch1` | −0.752 |
# | `PD_PeriodicityWang_th0_01` | +0.825 | `DN_OutlierInclude_p_001_mdrmd` | −0.705 |
# 
# Son las diez características con |r| ≥ 0.7 sobre PC1, cinco de cada lado.
# 
# Leído junto, **PC1 es un eje de memoria y predictibilidad**. En el extremo positivo están las series cuyo error de pronóstico local es alto, cuyo espectro tiene el centro de masa en frecuencias altas y cuya autocorrelación se extingue rápido; en el negativo, las series con memoria larga, potencia concentrada en frecuencias bajas y rachas prolongadas por encima de su media. `FC_LocalSimple_mean3_stderr`, con una comunalidad de 0.980, es la característica que mejor resume el conjunto: casi toda su varianza vive en el plano principal, y es la más importante si la pregunta es *qué distingue a las series en general*.
# 
# **2. Las que separan grupos.** Aquí la ganadora es inequívoca: **`PD_PeriodicityWang_th0_01`, con una razón F de 321**, dos órdenes de magnitud sobre la mayoría. Y a diferencia de otras con F alta, su brecha es de apenas 0.036, es decir **no hay ninguna serie atípica inflándola: es una separación genuina de bloques**. En unidades originales el corte es tajante: el periodo dominante vale 11 meses en total, vía aérea y vía marítima, y 3, 3 y 2 meses en vía terrestre, El Salvador y Honduras. Un grupo está gobernado por el ciclo anual y el otro por ciclos sub-anuales. `IN_AutoMutualInfoStats_40_gaussian_fmmi` (F = 6.8, brecha 0.000) y `SP_Summaries_welch_rect_area_5_1` (F = 6.7, brecha 0.070) repiten exactamente el mismo corte por otras vías. Si la pregunta es *qué produce los grupos*, la respuesta es la escala temporal del ciclo dominante.
# 
# **3. Las que aíslan una serie sola.** Las cuatro mayores brechas señalan cada una a una serie distinta, y son las que explican las celdas saturadas del mapa de calor de 5.3:
# 
# | Característica | Brecha | Serie que aísla |
# |---|---|---|
# | `SC_FluctAnal_2_dfa_50_1_2_logi_prop_r1` | 1.92 | Estados Unidos (z = −2.42) |
# | `SC_FluctAnal_2_rsrangefit_50_1_logi_prop_r1` | 1.87 | Estados Unidos (z = −2.41) |
# | `SB_TransitionMatrix_3ac_sumdiagcov` | 1.79 | Honduras (z = +2.42) |
# | `DN_OutlierInclude_n_001_mdrmd` | 1.72 | Vía Marítima (z = +2.41) |
# 
# Las dos de escalamiento de fluctuaciones merecen una nota: tienen razones F de 104 y 62, pero **esa F es un artefacto**. Estados Unidos es un grupo de un solo elemento, así que aislar esa serie y "separar un grupo" son la misma operación y la F no distingue entre ambas. La brecha sí: 1.9 sobre un máximo posible de 2.4 significa que la separación viene de un único punto extremo. Son las características que crean PC2 (r = +0.905 y +0.882), y por eso **PC2, con su 24.3 % de varianza, es en buena medida el eje de Estados Unidos**: esa serie tiene PC2 = −5.22 cuando ninguna otra pasa de 2.65 en valor absoluto.
# 
# **4. Las que no sirvieron.** `DN_HistogramMode_10` es la menos informativa del conjunto, con una comunalidad de 0.026: prácticamente toda su varianza queda fuera del plano principal. Le sigue `SB_BinaryStats_diff_longstretch0` (0.165), y la razón se ve en unidades originales: toma el valor 5 en cinco series y 6 en las otras dos, sin ningún valor intermedio posible. La racha más larga de caídas mensuales consecutivas es prácticamente la misma en todas, así que apenas puede diferenciarlas. Que dos de las 22 aporten tan poco no contradice el diseño de catch22: sus autores minimizaron la redundancia sobre 93 conjuntos de clasificación heterogéneos, no sobre siete series mensuales de turismo de un mismo país, donde era esperable que algunas dimensiones resultaran casi constantes.

# ## 9. ¿Existen grupos naturales de series?
# 
# "Natural" es una palabra exigente. Cualquier algoritmo de agrupamiento devuelve grupos: Ward parte el conjunto en k bloques aunque las siete series estén uniformemente dispersas, y k-means también. La pregunta no es si el algoritmo produjo grupos, sino si esos grupos existen en los datos o son un artefacto del corte. Para responderla hacen falta pruebas que puedan fallar, y la celda siguiente aplica cuatro.
# 
# 1. **Distancia dentro contra distancia entre.** Un grupo real es más compacto por dentro que respecto de lo que lo rodea. Se compara la distancia media entre miembros del mismo grupo contra la distancia media a las series de otros grupos.
# 2. **Saltos en las alturas de fusión.** Si existen k grupos separados, el dendrograma muestra un salto grande al pasar de k a k−1: fusionar grupos genuinamente distintos cuesta más que fusionar miembros de un mismo grupo. Se busca dónde está el salto mayor.
# 3. **Estabilidad ante la remoción de una serie.** Se quita una serie, se recalcula el enlace de Ward con las seis restantes, se corta en tres grupos y se compara la partición resultante contra la original restringida a esas seis, con el índice de Rand ajustado. Un grupo natural sobrevive a que se le quite un vecino; uno artificial se reorganiza. Con siete series esta es la prueba más informativa disponible, porque no depende de supuestos distribucionales.
# 4. **Perfil de cada grupo.** Para describir *qué tienen en común* sus miembros, se promedia el z de cada característica dentro del grupo y se reportan las que más se apartan de cero. Un grupo cuyo perfil no se aparta de cero en ninguna característica no tiene nada que lo defina.
# 
# Los perfiles quedan en `resultados/catch22_perfil_grupos.csv`.

# In[13]:


from scipy.cluster.hierarchy import fcluster, linkage

etiquetas_ward = grupos["grupo_ward"]

print("cohesión de cada grupo de Ward")
for numero, bloque in grupos.groupby("grupo_ward"):
    miembros = bloque.index
    otras = etiquetas_ward.index.difference(miembros)
    if len(miembros) > 1:
        pares_dentro = distancia.loc[miembros, miembros].to_numpy()[
            np.triu_indices(len(miembros), k=1)
        ]
        dentro = pares_dentro.mean()
    else:
        dentro = np.nan
    entre = distancia.loc[miembros, otras].to_numpy().mean()
    nombres = ", ".join(SERIES[clave] for clave in miembros)
    interno = f"{dentro:.2f}" if len(miembros) > 1 else "  — "
    print(f"  grupo {numero}: {nombres}")
    print(f"    distancia media dentro {interno}   fuera {entre:.2f}   silueta media {bloque['silueta'].mean():+.3f}")

alturas = np.sort(enlace[:, 2])
saltos = pd.Series(
    np.diff(alturas),
    # El salto i separa la fusión que deja (n-1-i) grupos de la que deja (n-2-i): un salto
    # grande significa que pasar de ese número de grupos al siguiente es caro, es decir que
    # ahí está el corte natural.
    index=[f"{len(alturas) - i} → {len(alturas) - 1 - i} grupos" for i in range(len(alturas) - 1)],
)
print("\nsaltos entre alturas de fusión consecutivas")
print(saltos.round(3).to_string())
print(f"salto mayor: {saltos.idxmax()} ({saltos.max():.3f})")

print("\nestabilidad: se quita una serie y se reagrupan las seis restantes")
for omitida in estandarizada.index:
    restantes = estandarizada.drop(index=omitida)
    referencia = etiquetas_ward.drop(index=omitida)
    # Se corta en tantos grupos como queden representados tras la remoción: pedir siempre 3
    # haría imposible un Rand de 1 al quitar Estados Unidos, que es un grupo de un solo
    # elemento y desaparece con ella.
    parcial = fcluster(
        linkage(restantes, method="ward"), referencia.nunique(), criterion="maxclust"
    )
    rand_parcial = adjusted_rand_score(referencia, parcial)
    print(f"  sin {SERIES[omitida]:<15s} Rand ajustado {rand_parcial:+.3f}")

perfil = estandarizada.groupby(etiquetas_ward).mean().T
perfil.columns = [f"grupo_{numero}" for numero in perfil.columns]
perfil.insert(0, "familia", pd.Series(FAMILIAS))
perfil.round(4).to_csv(RUTA_RESULTADOS / "catch22_perfil_grupos.csv")

print("\nperfil de cada grupo: características cuyo z medio más se aparta de cero")
for columna in perfil.columns[1:]:
    print(f"\n  {columna}")
    destacadas = perfil[columna].reindex(perfil[columna].abs().sort_values(ascending=False).index)
    for nombre, valor in destacadas.head(5).items():
        print(f"    z medio {valor:+.2f}  {nombre}")


# ### Respuesta
# 
# **Sí, pero uno solo de los tres grupos merece llamarse natural.** Las cuatro pruebas coinciden en distinguir un grupo cohesionado, dos series aisladas y un residuo mal definido.
# 
# **El grupo natural es el trío vía terrestre, El Salvador y Honduras.** Es el único que aprueba todas las pruebas: distancia media interna de **4.90 contra 7.35** hacia afuera, silueta media de **+0.316** —la más alta del conjunto, y sus tres miembros son las tres series con mejor silueta individual—, aparece idéntico en Ward y en k-means, y se mantiene con k = 3 y con k = 4. Lo que sus miembros comparten es un perfil dinámico consistente:
# 
# | Característica | z medio del grupo | Qué significa |
# |---|---|---|
# | `PD_PeriodicityWang_th0_01` | −1.00 | Periodo dominante corto: 3, 3 y 2 meses |
# | `SP_Summaries_welch_rect_area_5_1` | +0.95 | Potencia concentrada en las frecuencias más bajas |
# | `FC_LocalSimple_mean3_stderr` | −0.94 | El menor error de pronóstico local: son las más predecibles |
# | `SB_MotifThree_quantile_hh` | −0.93 | Baja entropía simbólica: sucesión de valores más regular |
# | `CO_HistogramAMI_even_2_5` | +0.91 | Fuerte dependencia con retardo 2 |
# 
# Es decir: **series dominadas por el nivel y la tendencia, muy predecibles y poco erráticas, sin que el ciclo anual sea su rasgo dominante**. La lectura de dominio es la misma del inciso 7: son el tráfico fronterizo terrestre centroamericano, un flujo cotidiano y de alto volumen que responde más a la tendencia y a ciclos cortos que al calendario turístico anual.
# 
# **El segundo grupo de Ward —total, vía aérea y vía marítima— no es un grupo natural sino un residuo.** Su distancia media interna es 6.71 contra 7.55 hacia afuera: apenas un 11 % más compacto por dentro que por fuera, frente al 33 % del trío. Su silueta media es +0.064, y contiene la única serie con silueta negativa. Lo que sí comparte su perfil es el rasgo opuesto al del trío: `PD_PeriodicityWang_th0_01` con z medio **+1.13** (periodo dominante de 11 meses en las tres) e `IN_AutoMutualInfoStats_40_gaussian_fmmi` con **+1.01**. **El ciclo anual es lo que une a este grupo, y es también lo que lo separa del trío**: la característica que más discrimina de las 22, con razón F de 321, es exactamente esa.
# 
# **El criterio de las alturas de fusión contradice al de la silueta, y conviene decirlo.** El salto mayor del dendrograma, de **2.088**, está al pasar de 4 a 3 grupos: fusionar vía marítima con total y vía aérea cuesta 8.071 cuando la fusión previa costó 5.982. El corte por saltos señala **cuatro grupos**, no tres. La silueta prefirió tres por 0.0019 sobre cuatro (0.1628 contra 0.1609), una diferencia sin ningún contenido con siete observaciones. Con k = 4 la partición es {vía terrestre, El Salvador, Honduras}, {total, vía aérea}, {vía marítima} y {Estados Unidos}, y esa versión es más fiel a todo lo demás: explica por qué el grupo 1 salió incoherente, porque juntaba a vía marítima con dos series que no se le parecen.
# 
# **La prueba de estabilidad matiza el resultado y es la más honesta de las cuatro.** Quitar cualquier serie ajena al trío deja la partición intacta: sin total, sin vía terrestre, sin vía marítima o sin Estados Unidos el índice de Rand ajustado es **+1.000**. Pero quitar un miembro del trío lo desarma: sin El Salvador cae a **+0.118** y sin Honduras a **+0.318**, porque El Salvador es el vecino más cercano de los otros dos y sin él la pareja restante ya no se distingue del resto. La conclusión correcta es que el trío es un grupo real *dado este conjunto de siete series*, sostenido por un miembro central, y no una estructura que sobreviviría a cualquier recomposición de la muestra.
# 
# Hay un subproducto de esa misma prueba que apunta al inciso 11: en las tres reorganizaciones donde la partición se rompe, **vía marítima queda sola las tres veces** y Estados Unidos dos de tres. Su aislamiento es más robusto que cualquiera de los grupos.

# ## 10. ¿Las series de una misma categoría tienden a agruparse?
# 
# Esta es la única pregunta del bloque que admite una respuesta con respaldo estadístico real, y conviene aprovecharlo. Las siete series traen una etiqueta que catch22 nunca vio: la categoría con la que se construyeron, que es la misma de `src/comparativo.py` usada en el Laboratorio 1 —una serie de referencia, tres vías de ingreso y tres países de residencia—. Preguntar si las categorías se agrupan es preguntar si esa etiqueta externa predice la posición en el espacio de características.
# 
# El estadístico natural es la **distancia media entre pares de la misma categoría**. Si las categorías capturan algo de la dinámica, los pares internos deberían estar más cerca que el promedio; si no capturan nada, la distancia interna será indistinguible de la general.
# 
# Y aquí siete series dejan de ser un obstáculo para volverse una ventaja: **la distribución nula puede enumerarse por completo**. Repartir las etiquetas observadas —una de referencia, tres de vía de ingreso y tres de país— entre siete series admite 7!/(1!·3!·3!) = 140 asignaciones distintas, y las 140 caben en un cálculo instantáneo. No hace falta muestrear ni suponer normalidad: el valor *p* que produce la celda es **exacto**, la proporción de asignaciones al azar que agruparían las categorías al menos tan bien como la real. Es la única inferencia legítima de toda esta sección, y lo es precisamente porque la muestra es diminuta.
# 
# Se reporta además el índice de Rand ajustado entre las categorías y los grupos de Ward, que mide lo mismo desde el lado del agrupamiento: cuánto coincide la partición por categoría con la partición por dinámica.

# In[14]:


from itertools import permutations

pares_indices = np.triu_indices(len(distancia), k=1)
distancias_pares = distancia.to_numpy()[pares_indices]
categorias_serie = np.array([CATEGORIAS[clave] for clave in distancia.index])


def media_dentro(etiquetas):
    etiquetas = np.asarray(etiquetas)
    mismo = etiquetas[pares_indices[0]] == etiquetas[pares_indices[1]]
    return distancias_pares[mismo].mean()


observado = media_dentro(categorias_serie)
general = distancias_pares.mean()

print("distancia media entre pares de la misma categoría")
for categoria in pd.unique(categorias_serie):
    miembros = distancia.index[categorias_serie == categoria]
    if len(miembros) < 2:
        print(f"  {categoria:<20s} (una sola serie, sin pares internos)")
        continue
    internas = distancia.loc[miembros, miembros].to_numpy()[
        np.triu_indices(len(miembros), k=1)
    ]
    print(f"  {categoria:<20s} {internas.mean():.3f}   ({len(internas)} pares)")

print(f"\n  todas las categorías juntas {observado:.3f}")
print(f"  los 21 pares               {general:.3f}")

asignaciones = set(permutations(categorias_serie))
nulos = np.array([media_dentro(asignacion) for asignacion in asignaciones])
p_valor = (nulos <= observado).mean()

print(f"\nprueba de permutación exacta sobre {len(asignaciones)} asignaciones posibles")
print(f"  media de la distribución nula {nulos.mean():.3f}")
print(f"  mínimo alcanzable             {nulos.min():.3f}")
print(f"  máximo alcanzable             {nulos.max():.3f}")
print(f"  observado                     {observado:.3f}")
print(f"  p exacto (P[nulo ≤ observado]) {p_valor:.3f}")

rand_categorias = adjusted_rand_score(categorias_serie, grupos["grupo_ward"])
print(f"\nRand ajustado entre categoría y grupo de Ward: {rand_categorias:.3f}")
print("\ncategoría contra grupo de Ward")
print(
    pd.crosstab(
        pd.Series(categorias_serie, index=distancia.index, name="categoria"),
        grupos["grupo_ward"],
    ).to_string()
)

print("\nlos tres pares más cercanos y los tres más lejanos, con sus categorías")
orden_pares = np.argsort(distancias_pares)
for posicion in np.concatenate([orden_pares[:3], orden_pares[-3:]]):
    una = distancia.index[pares_indices[0][posicion]]
    otra = distancia.index[pares_indices[1][posicion]]
    marca = "misma" if CATEGORIAS[una] == CATEGORIAS[otra] else "distinta"
    print(
        f"  d = {distancias_pares[posicion]:.2f}  {SERIES[una]:<15s} ({CATEGORIAS[una]})"
        f"  /  {SERIES[otra]:<15s} ({CATEGORIAS[otra]})  → categoría {marca}"
    )


# ### Respuesta
# 
# **No. Las series de una misma categoría no tienden a agruparse, y la evidencia es inusualmente clara para una muestra de siete.** De las categorías que menciona el enunciado, las siete series del Laboratorio 1 cubren dos con más de un miembro —vía de ingreso y país de residencia—, y ninguna de las dos organiza el espacio de características.
# 
# | Evidencia | Valor | Lectura |
# |---|---|---|
# | Distancia media dentro de categoría | 7.003 | Prácticamente idéntica a la general |
# | Distancia media de los 21 pares | 7.015 | La diferencia es de 0.012 |
# | p exacto de permutación | **0.486** | Casi la mitad de las 140 asignaciones al azar agrupan igual o mejor |
# | Rand ajustado categoría / grupo de Ward | **0.067** | Coincidencia nula entre ambas particiones |
# 
# El valor *p* de 0.486 no es un resultado ambiguo ni un problema de poder: el observado, 7.003, cae prácticamente sobre la media de la distribución nula, 7.015, dentro de un recorrido que va de 5.808 a 7.751. La etiqueta administrativa no aporta **nada** sobre la dinámica de la serie.
# 
# **Vía de ingreso es incluso peor que el azar.** Sus tres pares internos promedian **7.398**, por encima de la media general de 7.015: las tres vías de ingreso son *más distintas entre sí* que dos series tomadas al azar del conjunto. Vía aérea y vía terrestre están a 7.07, y vía marítima a 8.05 de la terrestre. Compartir la condición de ser una vía de ingreso no implica ningún parecido dinámico.
# 
# **País de residencia queda apenas por debajo (6.609), y por una sola razón.** El Salvador y Honduras están a 4.77, pero Estados Unidos está a 6.78 y 8.28 de ellos. La categoría no une a sus tres miembros: une a dos y expulsa al tercero.
# 
# **Lo que sí organiza el espacio es el régimen de viaje, que cruza las categorías.** El par más parecido de todo el conjunto une categorías distintas —vía terrestre con El Salvador, 3.77— y los tres pares más lejanos también las cruzan, los tres involucrando a vía marítima. El grupo natural del inciso 9 mezcla una vía de ingreso con dos países de residencia, y lo hace porque los tres describen el mismo fenómeno: **flujo fronterizo terrestre centroamericano**. Del mismo modo, Estados Unidos se separa de El Salvador y Honduras, sus compañeros de categoría, porque llega por aire y no por tierra.
# 
# La conclusión útil para INGUAT es metodológica: **agrupar las series por la categoría con que se reportan no predice cómo se comportan**. Un modelo, una estrategia de pronóstico o una política diseñada "para las vías de ingreso" como bloque estaría juntando series con dinámicas incompatibles, mientras que vía terrestre, El Salvador y Honduras —que hoy se reportan en tablas separadas— admitirían un tratamiento común. Vale la pena subrayar que catch22 llegó a esa conclusión **sin conocer ninguna etiqueta**: solo con la forma de las siete curvas.

# ## 11. ¿Qué series presentan el comportamiento más atípico?
# 
# "Atípico" también admite más de una lectura, y las dos que importan aquí no coinciden. Una serie puede estar **lejos de todas las demás en promedio**, que es la noción geométrica, o puede estar **estructuralmente sola**, sin ninguna serie que la acompañe aunque su distancia promedio no sea la mayor. La celda calcula seis indicadores para separar ambas cosas:
# 
# | Indicador | Qué mide |
# |---|---|
# | `norma_z` | Distancia al centroide del conjunto; con las características estandarizadas es √(Σ z²) |
# | `distancia_media` | Lejanía promedio respecto de las otras seis |
# | `distancia_vecino` | Lejanía respecto de la serie más parecida: mide aislamiento, no lejanía general |
# | `celdas_extremas` | Cuántas de sus 22 características superan \|z\| > 2 |
# | `silueta` | Qué tan bien pertenece a su grupo |
# | `pc_extrema` | Su coordenada más grande en valor absoluto sobre las seis componentes |
# 
# La distinción entre `distancia_media` y `distancia_vecino` es la que hace el trabajo: una serie puede tener muchas series lejanas y aun así estar acompañada por una cercana, y esa no es atípica sino periférica. La que no tiene a nadie cerca sí lo es.
# 
# Hay una advertencia que conviene hacer antes de leer los resultados, y es sobre la silueta negativa. Que la serie total tenga la peor silueta del conjunto (−0.102) **no la vuelve atípica**: la silueta negativa indica que está más cerca del grupo vecino que del propio, lo cual es un síntoma de estar *en medio*, no *afuera*. Confundir ambas cosas sería el error más fácil de cometer en este inciso.

# In[15]:


atipicidad = pd.DataFrame(
    {
        "etiqueta": [SERIES[clave] for clave in estandarizada.index],
        "norma_z": np.sqrt((estandarizada**2).sum(axis=1)),
        "distancia_media": distancia.sum() / (len(distancia) - 1),
        "distancia_vecino": [vecinos[clave][1] for clave in estandarizada.index],
        "celdas_extremas": (estandarizada.abs() > 2).sum(axis=1),
        "silueta": grupos["silueta"],
        "pc_extrema": coordenadas.abs().max(axis=1),
    },
    index=estandarizada.index,
).sort_values("distancia_media", ascending=False)

atipicidad.round(4).to_csv(RUTA_RESULTADOS / "catch22_atipicidad.csv")

print("indicadores de atipicidad, ordenados por lejanía promedio")
print(atipicidad.round(3).to_string())
print(f"\nnorma esperada si una serie fuera promedio en todo: √22 = {np.sqrt(estandarizada.shape[1]):.2f}")

print("\nposición de cada serie en cada indicador (1 = más atípica)")
ranking_atipicidad = pd.DataFrame(
    {
        "norma_z": atipicidad["norma_z"].rank(ascending=False),
        "distancia_media": atipicidad["distancia_media"].rank(ascending=False),
        "distancia_vecino": atipicidad["distancia_vecino"].rank(ascending=False),
        "celdas_extremas": atipicidad["celdas_extremas"].rank(ascending=False),
        "pc_extrema": atipicidad["pc_extrema"].rank(ascending=False),
    },
    index=atipicidad.index,
).astype(int)
ranking_atipicidad.insert(0, "etiqueta", atipicidad["etiqueta"])
ranking_atipicidad["posicion_media"] = (
    ranking_atipicidad.drop(columns="etiqueta").mean(axis=1).round(2)
)
print(ranking_atipicidad.sort_values("posicion_media").to_string())

print("\nfirma de las dos series más atípicas: sus características con |z| > 1.5")
for clave in ("via_maritima", "pais_estados_unidos"):
    print(f"\n  {SERIES[clave]}")
    fila = estandarizada.loc[clave]
    for nombre, valor in fila[fila.abs() > 1.5].sort_values(key=abs, ascending=False).items():
        print(f"    z = {valor:+.2f}  {nombre:<44s} valor {matriz.loc[clave, nombre]:.3f}"
              f"   resto {matriz.drop(index=clave)[nombre].min():.3f} a {matriz.drop(index=clave)[nombre].max():.3f}")

print("\ncontexto de las series en unidades originales, que catch22 no ve")
for clave in SERIES:
    serie = completas[clave]
    print(
        f"  {SERIES[clave]:<15s} media {serie.mean():>9,.0f}   "
        f"coeficiente de variación {serie.std() / serie.mean():.3f}   "
        f"meses en cero {int((serie == 0).sum()):>3d}"
    )


# ### Respuesta
# 
# **Dos series son atípicas, vía marítima y Estados Unidos, y lo son por razones distintas.** El resultado no depende del indicador que se elija: **vía marítima ocupa el primer lugar en los cinco y Estados Unidos el segundo en los cinco**, sin una sola inversión. Con seis criterios que miden cosas diferentes, esa unanimidad es la evidencia más limpia de toda la sección.
# 
# #### Vía marítima: atípica en todos los sentidos a la vez
# 
# Está a 8.41 de distancia media cuando el promedio general es 7.02, su norma es 6.27 contra los 4.69 que tendría una serie promedio en todo, acumula 4 de las 8 celdas con \|z\| > 2 del mapa de calor y define el extremo del eje dominante con PC1 = 5.62. El dato más elocuente es otro: **su vecino más cercano está a 7.07, más lejos que la distancia media entre dos series cualesquiera del conjunto (7.02)**. No es que esté lejos del centro; es que no tiene a nadie cerca.
# 
# Su firma es coherente y apunta toda en la misma dirección:
# 
# | Característica | Marítima | Las otras seis | Qué implica |
# |---|---|---|---|
# | `SP_Summaries_welch_rect_centroid` | 0.515 | 0.049 – 0.172 | Centro de masa del espectro tres veces más alto: la energía está en frecuencias altas |
# | `CO_HistogramAMI_even_2_5` | 0.123 | 0.207 – 0.537 | La dependencia con retardo 2 más débil del conjunto |
# | `SB_BinaryStats_mean_longstretch1` | 9 meses | 12 – 50 meses | Las rachas más cortas por encima de su media |
# | `FC_LocalSimple_mean1_tauresrat` | 0.200 | 0.016 – 0.071 | Los residuos a un paso cambian de estructura mucho más |
# | `CO_f1ecac` | 2.77 | 6.44 – 18.93 | Su autocorrelación se extingue más de dos veces más rápido |
# 
# Todas dicen lo mismo: **es la serie con menos memoria y menos estructura temporal aprovechable**. La justificación está en unidades que catch22 nunca vio, y que la celda imprime al final: vía marítima promedia **5,851 viajeros mensuales** —el 2 % de la serie total—, pasa **27 de sus 210 meses en cero** y tiene un coeficiente de variación de **1.147**, más del doble que cualquier otra. Es tráfico de cruceros: no es un flujo continuo sino una sucesión de eventos discretos, que ocurren cuando un barco atraca y no ocurren en absoluto cuando no atraca. Una serie construida así no puede tener rachas largas ni autocorrelación persistente, y por eso las 22 características la empujan al mismo extremo. El Laboratorio 1 ya había tropezado con la misma propiedad por otra vía: fue la serie que quedó fuera del modelado LSTM justamente porque sus meses en cero rompían la transformación `log1p`.
# 
# #### Estados Unidos: atípica en una sola dimensión, pero radicalmente
# 
# Su perfil es el opuesto. Solo **2 características** superan \|z\| > 2, contra las 4 de vía marítima, y su distancia media es menor (7.69). Pero esas dos pertenecen a la misma familia y la separación no es de grado sino de régimen:
# 
# | Característica | Estados Unidos | Las otras seis |
# |---|---|---|
# | `SC_FluctAnal_2_dfa_50_1_2_logi_prop_r1` | 0.143 | 0.738 – 0.857 |
# | `SC_FluctAnal_2_rsrangefit_50_1_logi_prop_r1` | 0.167 | 0.762 – 0.857 |
# 
# Las otras seis series se apiñan en un rango estrecho y Estados Unidos está a un quinto de ese valor: **el escalamiento de sus fluctuaciones sigue un régimen distinto al de todas las demás**. A eso se suma `CO_trev_1_num` = +0.012, el **único valor positivo** del conjunto —las otras seis van de −0.175 a −0.036—, es decir que la asimetría temporal de sus diferencias sucesivas tiene el signo contrario: sus subidas y bajadas tienen una forma distinta a la de cualquier otra serie.
# 
# Esa singularidad es la que explica la estructura del PCA. **PC2 concentra el 24.3 % de la varianza total y existe esencialmente para describir a Estados Unidos**: sus dos cargas mayores son justo estas dos características (r = +0.905 y +0.882) y la coordenada de la serie es −5.22 cuando ninguna otra pasa de 2.65 en valor absoluto. Casi una cuarta parte de la variabilidad del conjunto se gasta en una propiedad de una sola serie. Es también la única serie que forma un grupo unipersonal en Ward *y* en k-means. Como contexto, en el Laboratorio 1 fue una de las series más difíciles de modelar: 24 de sus 36 especificaciones SARIMA se descartaron por producir trayectorias explosivas fuera de muestra, más que en ninguna otra serie salvo Honduras.
# 
# #### Dos series que parecen atípicas y no lo son
# 
# **Honduras** aparece tercera en norma y en distancia media, y tiene la celda más extrema del mapa de calor (`SB_TransitionMatrix_3ac_sumdiagcov`, z = +2.42). Pero su vecino está a 4.77 —el segundo más cercano del conjunto— y su silueta es +0.317. Tiene un rasgo extremo, no un comportamiento aislado: pertenece con claridad al grupo natural del inciso 9.
# 
# **La serie total** tiene la peor silueta (−0.102), la única negativa, y sería fácil leerla como anomalía. Es lo contrario: su norma es **3.90, por debajo de los 4.69 de una serie promedio**, y su distancia media es la quinta de siete. Está *en el centro*, no afuera. Su silueta es negativa porque, siendo la suma de las demás, queda equidistante entre los grupos y ninguno la reclama. Confundir centralidad con atipicidad habría invertido por completo la conclusión.
# 
# En el otro extremo, **la serie más típica del conjunto es vía terrestre**: la menor norma (3.50), la menor distancia media (6.16) y ninguna característica con \|z\| > 2. Que la representante más fiel del conjunto sea también su componente de mayor volumen después del total es coherente, y refuerza la lectura del inciso 10: lo que organiza este espacio es el régimen de viaje, no la etiqueta administrativa.

# ## 12. ¿Los agrupamientos son consistentes con el análisis exploratorio del Laboratorio 1?
# 
# Los tres grupos de Ward del inciso 9 son `{total, vía aérea, vía marítima}`, `{vía terrestre, El Salvador, Honduras}` y `{Estados Unidos}` en solitario. La pregunta es si esa partición coincide con las cinco lentes que el Laboratorio 1 ya había aplicado a mano: fuerza de tendencia (`ft`), fuerza estacional (`fs`), volatilidad prepandemia (`cv_2009_2019`), impacto de la pandemia (`caida_pct`, de `comparativo_series.csv`) y autocorrelación. Para esta última no hay una columna del Laboratorio 1 comparable entre las siete series; se usa `CO_f1ecac`, la característica de catch22 que ya midió el inciso 7 y que es, por definición, el primer rezago en que la ACF cae bajo 1/e — la misma lectura que un correlograma, en una sola cifra.

# In[16]:


comparativo = pd.read_csv(RUTA_RESULTADOS / "comparativo_series.csv")

cruce = (
    exportable_grupos[["clave", "etiqueta", "categoria", "grupo_ward"]]
    .merge(
        comparativo[["clave", "ft", "fs", "cv_2009_2019", "caida_pct"]],
        on="clave",
    )
    .merge(
        matriz[["CO_f1ecac"]].reset_index().rename(columns={"CO_f1ecac": "acf_f1ecac"}),
        on="clave",
    )
    .sort_values(["grupo_ward", "clave"])
    .reset_index(drop=True)
)
cruce.round(3).to_csv(RUTA_RESULTADOS / "catch22_vs_eda.csv", index=False)
print(cruce.round(3).to_string(index=False))

print(f"\ncaída_pct: rango de {cruce['caida_pct'].max() - cruce['caida_pct'].min():.2f} puntos entre las siete series")
print(f"acf_f1ecac en el grupo 2 (terrestre/El Salvador/Honduras): {cruce.loc[cruce['grupo_ward'] == 2, 'acf_f1ecac'].round(2).tolist()}")
print(f"distancia vecino más cercano, grupo 2: {resumen.loc[['via_terrestre','pais_el_salvador','pais_honduras'], 'distancia_vecino'].round(2).tolist()}")
print(f"distancia vecino más cercano, grupo 1: {resumen.loc[['total','via_aerea','via_maritima'], 'distancia_vecino'].round(2).tolist()}")


# ### Respuesta
# 
# **Parcialmente, y de forma desigual entre las cinco dimensiones.** No hay una respuesta única de sí o no; hay que revisarlas una por una porque no cuentan la misma historia.
# 
# **El impacto de la pandemia no discrimina nada.** `caida_pct` va de 97.50 % a 100.00 % en las siete series — un rango de menos de tres puntos —, así que no puede explicar por qué Ward separa tres grupos. Es coherente con el diseño de catch22 explicado en el inciso 4: la magnitud del choque es un efecto de nivel, y catch22 estandariza la serie internamente, de modo que dos series con caídas de 97.5 % y 100 % son indistinguibles para el algoritmo aunque para el ojo humano una haya llegado literalmente a cero. El agrupamiento no es inconsistente con la pandemia; es ciego a ella por construcción.
# 
# **La fuerza de tendencia tampoco se alinea con los grupos.** Dentro del grupo 2 (vía terrestre, El Salvador, Honduras) `ft` va de 0.116 a 0.653, un rango tan amplio como el de todo el conjunto. Ward no está agrupando por cuánta tendencia tiene cada serie.
# 
# **La estacionalidad, la volatilidad y la autocorrelación sí se alinean, pero solo en el grupo 2.** Sus tres miembros comparten `fs` bajo y compacto (0.105–0.169), `cv_2009_2019` compacto (0.335–0.453) y `acf_f1ecac` uniformemente lento (9.0–18.9, ninguno por debajo de nueve meses): las tres coordenadas describen series con memoria larga, estacionalidad discreta y volatilidad moderada, y ese es justamente el trío que el inciso 9 ya había identificado como el más cohesionado del conjunto, con distancias internas de 3.77 a 4.77 frente a las de 5.02 a 7.07 del grupo 1.
# 
# **El grupo 1 es la evidencia de que Ward con k = 3 obliga a un residuo.** Total (8.58), vía aérea (6.44) y vía marítima (2.77) no comparten decaimiento de autocorrelación, ni `fs` (0.142–0.405), ni `cv_2009_2019` (0.216–0.790, un rango dominado enteramente por la marítima). Las distancias al vecino más cercano dentro del grupo (5.02–7.07) confirman que su cohesión es mucho más débil que la del grupo 2: no es un grupo natural sino lo que queda después de separar a Estados Unidos y al trío centroamericano-terrestre, exactamente lo que el inciso 9 ya advertía sobre vía marítima como miembro forzado.
# 
# En conjunto: **los agrupamientos de catch22 son consistentes con la estacionalidad, la volatilidad y la autocorrelación del grupo 2, ciegos al impacto de la pandemia por diseño, y no capturan la fuerza de tendencia en ningún grupo.**

# ## 13. Tres descubrimientos que catch22 aportó y el análisis exploratorio tradicional no había mostrado
# 
# **1. Estados Unidos es indistinguible en el EDA tradicional y radicalmente atípica en catch22.** Sus indicadores clásicos son los más discretos del conjunto: `ft` = 0.107, `fs` = 0.109 y `cv_2009_2019` = 0.300, los tres en el rango medio de las siete series, sin nada que la señale. El inciso 11 mostró lo contrario con catch22: sus dos características de escalamiento de fluctuaciones (DFA y rango reescalado) caen a un quinto del valor de las otras seis (0.143–0.167 contra 0.738–0.857), un cambio de régimen, no de grado, que el comparativo del Laboratorio 1 no tenía forma de detectar porque mide dispersión y tendencia, no la estructura de las fluctuaciones a distintas escalas temporales.
# 
# **2. Vía marítima no es solo "una serie con muchos ceros": es un proceso de eventos discretos.** El diagnóstico del Laboratorio 1 la había señalado por sus 27 meses en cero y la excluyó del modelado LSTM por eso. catch22 explica *por qué* tiene esa forma: centroide espectral casi tres veces más alto que el resto (`SP_Summaries_welch_rect_centroid` = 0.515 contra 0.049–0.172) y la dependencia de retardo 2 más débil del conjunto (`CO_HistogramAMI_even_2_5` = 0.123). Es la firma de tráfico de cruceros —eventos puntuales, no un flujo continuo— y no una simple anomalía de conteo.
# 
# **3. El impacto de la pandemia, la variable más dramática del análisis exploratorio, resultó invisible para catch22.** El inciso 12 lo muestra: `caida_pct` varía menos de tres puntos entre las siete series (97.50 %–100.00 %) y no separa ningún grupo. No es un fallo del método; es la consecuencia directa de la invariancia de escala del inciso 4, que el análisis exploratorio tradicional no tenía —cada serie del Laboratorio 1 se leyó con su propio eje— y que aquí queda demostrada con números: catch22 compara *forma*, no *profundidad del choque*.

# ## 14. Un LSTM con características catch22 de ventana móvil frente al mejor LSTM de la serie total
# 
# Los incisos 1 a 11 usaron catch22 para describir siete series completas, un vector de 22 valores por serie. Ese uso no sirve para alimentar una LSTM: una fila por serie da solo 7 observaciones. Aquí catch22 se recalcula de otra manera, **por ventana móvil**: para cada ventana de contexto de 24 meses que ve la LSTM, se extraen sus 22 características y se agregan como canales adicionales de entrada junto al valor escalado. El objetivo es que la red reciba, además de los últimos 24 valores, una descripción explícita de la forma de esa ventana —su memoria, su periodicidad, su distribución— y ver si eso mejora el pronóstico.
# 
# **Protocolo, idéntico al del mejor modelo de la sección 2 salvo por los canales de entrada.** La serie es `total`, con la ventana de 24 meses, dos capas LSTM de 64 unidades, sin dropout y estrategia directa (`Dense(63)`) — exactamente la configuración ganadora de `resultados/lstm_tuneo_total.csv`. El único cambio es el número de canales de entrada: 1 en el modelo base, 1 + 22 en el modelo con catch22. Ambos se tunean de la misma forma que `grid_lstm`: una división de validación del 15 % decide el número de épocas por paro anticipado, y el modelo final se reentrena con las 61 ventanas completas de train por ese número de épocas, sin dejar ninguna fuera. Las 22 características se calculan una vez por ventana, sobre esos mismos 24 meses de contexto —nunca sobre el futuro—, se estandarizan con un `StandardScaler` ajustado solo con las ventanas de entrenamiento y se repiten en los 24 pasos de tiempo, porque catch22 describe la ventana completa y no tiene una lectura por mes.

# In[17]:


import keras
import matplotlib.pyplot as plt
import pycatch22
from sklearn.preprocessing import StandardScaler

from src.evaluacion import metricas
from src.utils import RUTA_FIGURAS
from src.lstm import (
    HORIZONTE,
    crear_ventanas,
    escalar_train,
    entrenar,
    fijar_semilla,
    particionar_validacion,
    _revertir,
)

VENTANA_C22 = 24
UNIDADES_C22, CAPAS_C22, DROPOUT_C22 = 64, 2, 0.0

serie_train = cargar_serie("total", "train")
serie_test = cargar_serie("total", "test")

escalado, escalador = escalar_train(serie_train)
X, y = crear_ventanas(escalado, VENTANA_C22, HORIZONTE)


def catch22_ventana(valores_ventana: np.ndarray) -> np.ndarray:
    return np.array(pycatch22.catch22_all(valores_ventana.tolist())["values"])


caracteristicas_ventanas = np.array([catch22_ventana(X[i, :, 0]) for i in range(len(X))])
escalador_c22 = StandardScaler().fit(caracteristicas_ventanas)
canales_c22 = escalador_c22.transform(caracteristicas_ventanas)
X_c22 = np.concatenate(
    [X, np.repeat(canales_c22[:, None, :], VENTANA_C22, axis=1)], axis=2
)
print(f"ventanas base {X.shape}, ventanas con catch22 {X_c22.shape}")


# In[18]:


def construir_lstm_multivariado(n_canales: int) -> keras.Model:
    modelo = keras.Sequential([keras.layers.Input(shape=(VENTANA_C22, n_canales))])
    for indice in range(CAPAS_C22):
        modelo.add(keras.layers.LSTM(UNIDADES_C22, return_sequences=indice < CAPAS_C22 - 1))
        if DROPOUT_C22 > 0:
            modelo.add(keras.layers.Dropout(DROPOUT_C22))
    modelo.add(keras.layers.Dense(HORIZONTE))
    modelo.compile(
        optimizer=keras.optimizers.Adam(1e-3), loss="mse", metrics=["mae"]
    )
    return modelo


def entrenar_y_evaluar(X_entrada, n_canales, contexto_prediccion):
    X_ajuste, y_ajuste, X_val, y_val = particionar_validacion(X_entrada, y)
    keras.backend.clear_session()
    fijar_semilla()
    modelo_tuneo = construir_lstm_multivariado(n_canales)
    historial = entrenar(modelo_tuneo, X_ajuste, y_ajuste, X_val, y_val, batch_size=16)
    epocas = len(historial.history["loss"])

    keras.backend.clear_session()
    fijar_semilla()
    modelo_final = construir_lstm_multivariado(n_canales)
    modelo_final.fit(
        X_entrada, y, epochs=epocas, batch_size=16, shuffle=False, verbose=0
    )
    prediccion = _revertir(
        modelo_final.predict(contexto_prediccion, verbose=0).ravel(), escalador
    )
    return modelo_final, epocas, prediccion


contexto_base = escalado[-VENTANA_C22:].reshape(1, VENTANA_C22, 1)
modelo_base, epocas_base, pred_base = entrenar_y_evaluar(X, 1, contexto_base)

contexto_valores = escalado[-VENTANA_C22:]
contexto_c22 = escalador_c22.transform(catch22_ventana(contexto_valores).reshape(1, -1))
contexto_c22 = np.concatenate(
    [
        contexto_valores.reshape(1, VENTANA_C22, 1),
        np.repeat(contexto_c22[:, None, :], VENTANA_C22, axis=1),
    ],
    axis=2,
)
modelo_c22, epocas_c22, pred_c22 = entrenar_y_evaluar(X_c22, 1 + 22, contexto_c22)

real = serie_test.to_numpy(dtype=float)
metricas_base = metricas(real, pred_base)
metricas_c22 = metricas(real, pred_c22)

comparacion = pd.DataFrame(
    [
        {
            "modelo": "lstm_directo (reproducido, base publicada)",
            "n_canales": 1,
            "epocas": epocas_base,
            "n_parametros": modelo_base.count_params(),
            **metricas_base,
        },
        {
            "modelo": "lstm_directo_catch22",
            "n_canales": 23,
            "epocas": epocas_c22,
            "n_parametros": modelo_c22.count_params(),
            **metricas_c22,
        },
    ]
)
comparacion.to_csv(RUTA_RESULTADOS / "metricas_lstm_catch22.csv", index=False)
print(comparacion.round(3).to_string(index=False))


# In[19]:


figura, eje = plt.subplots(figsize=(9, 4.5))
eje.plot(serie_train.index[-24:], serie_train.to_numpy()[-24:], color="#444444", label="Train (últimos 24 meses)")
eje.plot(serie_test.index, real, color="black", linewidth=2, label="Real (test)")
eje.plot(serie_test.index, pred_base, color="#1f77b4", linestyle="--", label=f"LSTM base (MAPE {metricas_base['mape']:.1f} %)")
eje.plot(serie_test.index, pred_c22, color="#d62728", linestyle="--", label=f"LSTM + catch22 (MAPE {metricas_c22['mape']:.1f} %)")
eje.set_title("Serie total: LSTM base vs. LSTM con canales catch22 de ventana móvil")
eje.legend()
figura.tight_layout()
figura.savefig(RUTA_FIGURAS / "lstm_catch22_total.png", dpi=150, bbox_inches="tight")
plt.close(figura)


# ### Discusión
# 
# **Añadir catch22 como canales de entrada empeoró el pronóstico, y de forma sustancial.** El modelo base reproduce exactamente la métrica publicada en la sección 2 del informe (MAE 76,957, RMSE 100,290, MAPE 33.76 %) — la misma configuración, el mismo protocolo, confirmando que la comparación es limpia. El modelo con los 23 canales llega a un MAPE de 78.56 %, más del doble de error, con MAE de 216,932 y RMSE de 239,228. El resultado es reproducible: dos corridas con la misma semilla dan exactamente los mismos números en ambos modelos.
# 
# **La causa más probable no es la arquitectura, es el tamaño de muestra.** Ambos modelos tienen un número de parámetros similar (54,015 el base, 59,647 el de catch22 — un incremento de solo 10 %), pero el volumen de entrada por ventana pasa de 24 valores a 552 (24 pasos × 23 canales). El informe ya había señalado, para el modelo base, que 61 ventanas de entrenamiento es una muestra pequeña y que sus curvas muestran sobreajuste desde la época doce. Multiplicar por 23 el número de valores de entrada sin agregar una sola observación nueva agrava exactamente ese problema: el paro anticipado se activó antes en el modelo con catch22 (37 épocas contra 42), consistente con una red que encuentra un mínimo aceptable en el conjunto de validación más rápido, pero uno que generaliza peor al test.
# 
# **Las 22 características no aportan información temporal nueva dentro de la ventana.** Se calculan sobre los mismos 24 valores que ya recibe el canal base y se repiten idénticas en los 24 pasos de tiempo: no describen algo que ocurra *dentro* de la ventana en un momento distinto, sino un resumen constante de la ventana completa. Una LSTM con acceso a los 24 valores crudos ya puede, en principio, aprender cualquier función de ellos, incluida su propia estadística resumida; los canales catch22 no añaden grados de libertad a lo que el modelo puede representar, solo antes ya podía. Lo que sí hacen es diluir la señal: 22 de 23 canales de entrada llevan la misma constante en cada paso de tiempo, y eso desplaza gran parte de la capacidad de la primera capa LSTM hacia pesos que multiplican una descripción redundante en lugar de aprender la dinámica secuencial.
# 
# **Conclusión.** Para la serie `total`, con 61 ventanas de entrenamiento, agregar características catch22 de ventana móvil no mejora el mejor LSTM del laboratorio: lo empeora, y la explicación más defendible es el tamaño de muestra, no la utilidad de catch22 como descriptor. El resultado es coherente con el uso que sí funcionó en los incisos 1 a 11: catch22 aporta valor para *comparar series entre sí* con pocas observaciones por serie y muchas series (7 filas, 22 columnas), no para alimentar directamente un modelo secuencial que ya tiene acceso a la serie cruda y muy pocas ventanas de entrenamiento.
