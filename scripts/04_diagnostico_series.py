#!/usr/bin/env python
# coding: utf-8

# In[1]:


from pathlib import Path
import sys

import pandas as pd

RAIZ = Path.cwd()
if not (RAIZ / "src").exists():
    RAIZ = RAIZ.parent
sys.path.insert(0, str(RAIZ))

from src.diagnostico import analizar_serie
from src.utils import RUTA_RESULTADOS, SERIES, cargar_serie

COLORES = {
    "total": "tab:blue",
    "via_aerea": "tab:orange",
    "via_terrestre": "tab:green",
    "via_maritima": "tab:purple",
    "pais_el_salvador": "tab:red",
    "pais_estados_unidos": "tab:brown",
    "pais_honduras": "tab:cyan",
}

RUTA_RESULTADOS.mkdir(parents=True, exist_ok=True)


# In[2]:


resultados = []
for clave in SERIES:
    serie = cargar_serie(clave, "train")
    resultados.append(analizar_serie(clave, serie, COLORES[clave]))

diagnostico = pd.DataFrame(resultados)
diagnostico.to_csv(RUTA_RESULTADOS / "diagnostico_series.csv", index=False)
print(diagnostico.to_string(index=False))


# ## Vía terrestre
# 
# La serie crece hasta 2019 y se desploma con la pandemia. Diciembre es el pico estacional (factor 1.400) y febrero el valle (0.806), por lo que INGUAT debe reforzar capacidad fronteriza al cierre del año. La desviación estándar aumenta de 20,032 a 57,068 viajeros entre los dos tramos prepandemia, señal de varianza dependiente del nivel que `log1p` estabiliza. La ACF en niveles decae lentamente y conserva señal en el rezago 12; tras diferenciar, la dependencia se concentra en pocos rezagos. El ADF en niveles no rechaza raíz unitaria (p=0.5619), mientras d=1 sí la rechaza (p=0.0091) y d=1, D=1 la rechaza con mayor claridad (p<0.0001). Se adopta d=1 y D=1.

# ## Vía marítima
# 
# La trayectoria es irregular, con 16 ceros en entrenamiento y cambios abruptos de nivel. Diciembre presenta el mayor factor estacional prepandemia (3.328) y junio el menor (0.153), pero estos factores son inestables y no justifican una planificación operativa rígida. La desviación estándar pasa de 5,148 a 7,742 viajeros y `log1p` reduce la dispersión sin eliminar los quiebres. La ACF y PACF mantienen dependencias erráticas después de diferenciar. El ADF no rechaza raíz unitaria en niveles (p=1.0000), con d=1 (p=0.5750), con d=1, D=1 (p=0.1327) ni con d=2 (p=0.6994). Se exploran d=2 y D=1, sin afirmar estacionariedad al 5 %. Los ceros prepandemia y el cierre entre abril de 2020 y octubre de 2021 explican parte de esta conducta. Además, los totales anuales bajan de 130,789 en 2019 a cerca de 6,600 entre 2023 y 2025, un cambio de régimen que hará que los modelos entrenados hasta marzo de 2021 sobrepredigan el test.

# ## País de residencia: El Salvador
# 
# El volumen aumenta durante la década y cae a cero entre abril y agosto de 2020 por el cierre de fronteras. Diciembre es el pico (factor 1.381) y febrero el valle (0.800), útil para anticipar personal y servicios terrestres durante las fiestas de fin de año. La desviación estándar sube de 9,515 a 28,199 viajeros; `log1p` reduce esta heterocedasticidad. La ACF en niveles muestra persistencia y patrón anual, mientras la diferenciada se disipa con rapidez. El ADF no rechaza raíz unitaria en niveles (p=0.4325), pero sí con d=1 y con d=1, D=1 (ambos p<0.0001). Se adopta d=1 y D=1.

# ## País de residencia: Estados Unidos
# 
# La serie crece antes de 2020 y registra cinco ceros consecutivos de abril a agosto de ese año. Julio es el pico estacional (factor 1.449) y septiembre el valle (0.606), por lo que la demanda turística y aeroportuaria requiere mayor capacidad en el verano boreal. La desviación estándar pasa de 6,840 a 9,226 viajeros y la transformación `log1p` estabiliza su amplitud. La ACF revela persistencia y correlación anual; después de diferenciar quedan pocos rezagos relevantes. En niveles, el ADF queda apenas sobre el umbral (p=0.0501); d=1 rechaza raíz unitaria (p=0.0307) y d=1, D=1 lo hace con holgura (p<0.0001). Se adopta d=1 y D=1.

# ## País de residencia: Honduras
# 
# La tendencia previa a la pandemia es ascendente y el cierre fronterizo produce ceros de abril a agosto de 2020. Enero alcanza el factor estacional máximo (1.216) y febrero el mínimo (0.824), una concentración que aconseja reforzar la atención terrestre al inicio del año. La desviación estándar aumenta de 1,366 a 3,717 viajeros, por lo que `log1p` mejora la estabilidad de la varianza. Aunque el ADF ya rechaza raíz unitaria en niveles (p=0.0040), la ACF muestra persistencia y señal estacional; d=1 y d=1, D=1 producen p<0.0001 y una ACF más corta. Para mantener comparabilidad y absorber la estacionalidad se adopta d=1 y D=1, vigilando posible sobrediferenciación.
