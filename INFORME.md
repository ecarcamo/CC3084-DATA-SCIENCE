# Monitoreo satelital de cianobacteria en los lagos de Atitlán y Amatitlán

**Universidad del Valle de Guatemala — CC3084 Data Science — Laboratorio 4**

## 1. Contexto y objetivo

Los lagos de Atitlán y Amatitlán son dos de los cuerpos de agua más importantes de Guatemala, tanto por su valor ecológico y turístico como por los riesgos que enfrentan debido a la contaminación. En ambos se ha reportado la proliferación de **cianobacterias**, microorganismos capaces de formar floraciones tóxicas cuando el agua está caliente, estancada y rica en nutrientes (por ejemplo, por aguas residuales o escorrentía agrícola y urbana).

Monitorear estas floraciones con muestreos físicos en el lago es costoso y limitado: solo cubre los puntos donde se toma la muestra, en el momento en que se toma. Este informe usa en cambio **imágenes satelitales gratuitas** de la misión Sentinel-2 (programa europeo Copernicus) para observar los dos lagos completos, de forma repetida a lo largo de un año y medio, sin salir a campo.

El objetivo es responder, con evidencia de datos y no solo apreciación visual: **¿cómo ha evolucionado la cianobacteria en cada lago, en qué zonas se concentra, y qué tan fuerte es su relación con otras señales del agua que el satélite puede medir?**

## 2. De dónde vienen los datos

Se usaron 22 imágenes satelitales en total: 11 fechas para Atitlán y 11 para Amatitlán, previamente seleccionadas para el laboratorio por tener la menor nubosidad posible sobre cada lago, entre enero de 2025 y julio de 2026. Las imágenes se obtuvieron directamente de la infraestructura de Copernicus (el programa satelital europeo que opera Sentinel-2) mediante su API oficial, sin necesidad de descargar las escenas completas: solo se piden las franjas del satélite (llamadas "bandas") estrictamente necesarias para calcular los indicadores de este informe, lo que agiliza la descarga y ahorra espacio.

De cada imagen se obtienen tres tipos de información:

- **Índice de cianobacteria**: una medida numérica calculada a partir de las bandas del satélite sensibles al color del agua, que se correlaciona con la presencia de clorofila-a producida por algas y cianobacterias. A valores más altos, mayor indicio de floración.
- **NDVI** (índice de vegetación): mide si una superficie se parece espectralmente a vegetación viva. Sobre agua abierta y limpia normalmente da valores negativos.
- **NDWI** (índice de agua): mide si una superficie se parece espectralmente a agua limpia. Sobre agua abierta normalmente da valores altos.

Además, cada imagen incluye una **máscara de agua**, generada automáticamente a partir de las mismas bandas satelitales, que permite distinguir con precisión los píxeles que corresponden al lago de los que corresponden a tierra firme alrededor. Todo el análisis de este informe se calcula únicamente sobre los píxeles de agua.

Un detalle documentado durante la obtención de los datos: una de las fechas de Amatitlán (7 de febrero de 2026) fue señalada de antemano con cobertura parcial de nubes. Al revisar la imagen descargada se confirmó que, para esa fecha en particular, el satélite sí logró cubrir el lago completo sin nubes, por lo que el dato se mantiene sin advertencias adicionales.

## 3. Mapas del índice de cianobacteria, NDVI y NDWI

Para cada lago se generó un mapa con los tres indicadores, coloreados sobre la forma real del lago ([`indices_atitlan.png`](informe/figuras/indices_atitlan.png), [`indices_amatitlan.png`](informe/figuras/indices_amatitlan.png)).

**Atitlán** muestra un índice de cianobacteria bajo en general, algo más bajo en la zona central (la parte más profunda del lago) y algo más alto cerca de las orillas y bahías. El NDVI es negativo en toda la superficie de agua y el NDWI es alto y uniforme, ambos resultados esperables para un cuerpo de agua abierto y relativamente sano.

**Amatitlán** muestra un índice de cianobacteria notablemente más alto y más variable espacialmente que Atitlán, incluso en la misma fecha del año. Los valores más altos se ubican en el brazo norte del lago y en su franja central, zonas más cercanas a la mancha urbana y a los principales afluentes. Comparando ambos lagos en la misma escala de colores, la diferencia de magnitud es contundente: Amatitlán ya parte de un nivel de cianobacteria varias veces más alto que Atitlán, incluso antes de mirar la evolución en el tiempo.

## 4. Evolución de la cianobacteria a lo largo del tiempo

Se calculó el promedio del índice de cianobacteria dentro de cada lago para cada una de sus 11 fechas, y se graficó como una línea de tiempo por lago ([`evolucion_temporal_cianobacteria.png`](informe/figuras/evolucion_temporal_cianobacteria.png)).

| Lago | Valor mínimo registrado | Valor máximo registrado | Diferencia |
|---|---|---|---|
| Atitlán | 0.27 (nov. 2025) | 2.13 (abr. 2026) | ~8 veces |
| Amatitlán | 4.29 (feb. 2026) | 11.47 (jun. 2026) | ~2.7 veces |

**Amatitlán tiene, en todas las fechas sin excepción, un índice entre 5 y 15 veces más alto que Atitlán.** Esto confirma con datos numéricos el mayor deterioro ambiental de Amatitlán frente a Atitlán, algo ya reportado en estudios previos sobre ambos lagos.

**En ambos lagos la tendencia de fondo es ascendente** durante el año y medio estudiado: no es un valor estable con ruido aleatorio, sino un incremento sostenido. Amatitlán pasa de ~4.4 en enero de 2025 a 11.5 en junio de 2026; Atitlán pasa de 0.39 en enero de 2025 a un máximo de 2.13 en abril de 2026.

**Se observa además un patrón estacional**, consistente en los dos lagos: los valores más bajos ocurren después de la temporada de lluvias (noviembre), y los valores más altos se concentran hacia el final de la temporada seca (marzo–abril). Esto es coherente con el ciclo hidrológico de Guatemala: durante la temporada de lluvias (mayo–octubre) el agua que entra a los lagos diluye y "lava" nutrientes y biomasa de algas, mientras que en la temporada seca (noviembre–abril) el agua se estanca, la temperatura sube y los nutrientes acumulados (de origen agrícola y urbano) se concentran, condiciones que favorecen la floración de cianobacterias. Las fechas identificadas como críticas —notablemente por encima del comportamiento habitual de su propio lago— caen justamente en esa franja de marzo a junio ([`picos_floracion.png`](informe/figuras/picos_floracion.png)).

El pico más alto de todo el estudio (Amatitlán, 19 de junio de 2026) es una excepción que merece cautela: ocurre justo al inicio de la temporada de lluvias, no al final de la temporada seca como el resto de picos, y coincide además con la fecha de mayor nubosidad de todas las estudiadas. Es posible que corresponda a un evento real de "primera lluvia" — cuando las primeras lluvias arrastran de golpe una gran carga de nutrientes acumulados hacia el lago antes de que empiece a diluirlo — o que una parte de la lectura esté afectada por nubosidad residual. Con un solo dato no es posible distinguir ambos escenarios, y se recomienda tratarlo con cautela hasta contar con una imagen adicional cercana a esa fecha.

## 5. Distribución espacial dentro de cada lago

Además del promedio por fecha, se generaron mapas interactivos de cada lago ([`mapa_atitlan_2026-07-22.html`](informe/figuras/mapa_atitlan_2026-07-22.html), [`mapa_amatitlan_2026-06-19.html`](informe/figuras/mapa_amatitlan_2026-06-19.html), abribles en cualquier navegador) y mapas comparativos entre distintas fechas de un mismo lago usando siempre la misma escala de color, para poder comparar de forma justa dónde se concentra la cianobacteria y si esas zonas se repiten con el tiempo ([`comparacion_fechas_atitlan.png`](informe/figuras/comparacion_fechas_atitlan.png), [`comparacion_fechas_amatitlan.png`](informe/figuras/comparacion_fechas_amatitlan.png)).

**En Atitlán, la zona de valores altos no es fija: se mueve entre fechas.** En abril de 2026 se concentra en la franja norte y el cuerpo central del lago; en julio de 2026 el punto más alto se desplaza al brazo este. No se identificó una zona de acumulación persistente clara, lo que sugiere que la ubicación de la cianobacteria depende más de condiciones puntuales (viento, corrientes superficiales) que de una fuente de contaminación fija en un solo punto del lago.

**En Amatitlán, en cambio, sí aparecen zonas persistentes y muy marcadas de acumulación.** En enero de 2025 el índice era bajo y prácticamente uniforme en todo el lago. Para junio de 2026 se identifican dos zonas con valores extremos, muy por encima del resto del lago: el estrecho que conecta el brazo norte con el cuerpo principal, y la bahía sur. Ambas son zonas de agua poco profunda y de circulación reducida — el agua se estanca más fácilmente ahí que en la parte abierta del lago — lo que las convierte en puntos naturales de acumulación de biomasa de algas. El cuerpo central y abierto del lago también sube, pero de forma más moderada que esas dos zonas.

En conjunto, Amatitlán no solo tiene valores promedio más altos: su floración es también más heterogénea espacialmente, con puntos de acumulación bien definidos y persistentes en zonas de baja circulación. Atitlán, en cambio, sube de forma más pareja en toda su superficie y sin una zona fija de acumulación en el período estudiado.

## 6. Relación entre la cianobacteria y los otros indicadores satelitales (NDVI, NDWI)

Se evaluó qué tan fuerte es la relación estadística entre el índice de cianobacteria y cada uno de NDVI y NDWI, usando todos los píxeles de agua de las 11 fechas de cada lago (más de 3 millones de puntos en Atitlán, más de 400 mil en Amatitlán). Esta relación se mide en una escala de -1 a 1: valores cercanos a 1 indican que ambas variables suben y bajan juntas (relación positiva fuerte), cercanos a -1 indican que una sube cuando la otra baja (relación negativa fuerte), y cercanos a 0 indican que no hay relación clara ([`correlacion_indices.png`](informe/figuras/correlacion_indices.png)).

| Lago | Cianobacteria vs. NDVI | Cianobacteria vs. NDWI |
|---|---|---|
| Atitlán | 0.47 (positiva moderada) | -0.45 (negativa moderada) |
| Amatitlán | 0.75 (positiva fuerte) | -0.62 (negativa moderada-fuerte) |

**El patrón de signo es el mismo en ambos lagos**: a mayor cianobacteria, el NDVI sube y el NDWI baja. Esto tiene una explicación ambiental razonable: las floraciones de cianobacteria forman una capa o "nata" de biomasa en la superficie del agua que refleja la luz de forma parecida a la vegetación, alejando la firma espectral del agua de la de "agua limpia" típica.

**Amatitlán tiene la relación más fuerte y más limpia**: la nube de puntos es claramente consistente, sin datos atípicos extremos, señal de que en ese lago la cianobacteria domina y se relaciona de forma predecible con ambos indicadores.

**En Atitlán, la correlación moderada está influida por un pequeño número de píxeles atípicos** ubicados en la orilla del lago, donde la fórmula del índice de cianobacteria es matemáticamente inestable (el mismo fenómeno ya observado al construir los mapas de la sección 3). Si se descartan esos pocos puntos extremos, la relación real dentro del lago es más débil, consistente con que Atitlán está mucho menos afectado por cianobacteria y su señal es más baja y más ruidosa que la de Amatitlán.

En términos prácticos, esto significa que el NDVI y el NDWI no reemplazan al índice de cianobacteria, pero sí funcionan como una señal de alerta indirecta y más rápida de calcular: un NDVI anormalmente alto o un NDWI anormalmente bajo dentro de un cuerpo de agua es indicio de una posible floración, especialmente confiable en el caso de Amatitlán.

## 7. Resumen de hallazgos hasta este punto

- Amatitlán presenta un índice de cianobacteria entre 5 y 15 veces más alto que Atitlán en todas las fechas estudiadas, y su deterioro es visible tanto en el promedio del lago como en la distribución espacial.
- Ambos lagos muestran una tendencia de fondo ascendente entre enero de 2025 y julio de 2026: la cianobacteria no se mantiene estable, está empeorando en el período observado.
- Existe un patrón estacional en ambos lagos, con mínimos después de la temporada de lluvias y máximos hacia el final de la temporada seca.
- Atitlán no muestra una zona fija de acumulación de cianobacteria; Amatitlán sí, concentrada en dos zonas de baja circulación (el estrecho entre sus dos brazos y la bahía sur).
- El NDVI y el NDWI se relacionan de forma consistente con la presencia de cianobacteria en ambos lagos, con mayor fuerza y confiabilidad en Amatitlán que en Atitlán.

## 8. Extensión, persistencia y patrón estacional de la floración

Las secciones anteriores describen el promedio de cianobacteria por fecha, pero un promedio moderado puede esconder cosas muy distintas: una floración débil repartida en todo el lago, o una muy intensa concentrada en un punto pequeño. Para distinguir esos casos se calculó, por cada fecha, **qué porcentaje de la superficie del lago tiene un valor de cianobacteria "alto"** (por encima del percentil 90 de todos los valores de agua observados en ese lago a lo largo del estudio) ([`extension_floracion.png`](informe/figuras/extension_floracion.png)).

**En Amatitlán, la floración se comporta como un evento aislado más que como una tendencia gradual.** La fecha con el promedio más alto de todo el estudio (19 de junio de 2026, ya señalada en la sección 4 como un caso a tratar con cautela) es también la que cubre más superficie del lago: más de la mitad del área de agua (50.7%). El resto de fechas se queda por debajo del 7.3% de cobertura, varias de ellas por debajo del 1%. **En Atitlán, en cambio, hay varios episodios de floración con extensión relevante**, no solo uno: dos fechas superan el 19% de cobertura (abril de 2026) y otras cuatro rondan el 10-11% en distintos momentos del período estudiado.

Ligado a esto, se construyó un mapa por lago que cuenta, píxel por píxel, en cuántas de las 11 fechas ese punto tuvo un valor alto de cianobacteria — es decir, qué tan **persistente** es la acumulación en cada zona ([`persistencia_floracion_atitlan.png`](informe/figuras/persistencia_floracion_atitlan.png), [`persistencia_floracion_amatitlan.png`](informe/figuras/persistencia_floracion_amatitlan.png)). Para que este cálculo no se distorsione por píxeles de borde que el satélite solo detectó como agua en una o dos fechas (el mismo problema de inestabilidad en el borde del lago ya mencionado en la sección 3), se exige que un punto haya sido agua en al menos 9 de las 11 fechas antes de contarlo. El resultado es contraintuitivo: **ninguno de los dos lagos tiene una zona amplia de acumulación fija y repetida.** En Amatitlán, prácticamente 0% de su superficie de agua tuvo valores altos en 9 de las 11 fechas o más; en Atitlán esa fracción es apenas un poco mayor (0.6%) y se limita a un borde muy delgado, no a una región extensa. En ambos lagos, entonces, la floración depende sobre todo de eventos puntuales — no de un punto fijo del lago que acumule cianobacteria de forma constante durante todo el período estudiado.

Este resultado matiza lo observado en la sección 5: las "zonas persistentes y muy marcadas de acumulación" señaladas ahí para Amatitlán se identificaron comparando solo dos fechas puntuales, una de ellas la del pico extremo de junio de 2026. Al mirar las 11 fechas completas, esas mismas zonas se ven muy afectadas en ese evento concreto, pero no se mantienen sistemáticamente por encima del umbral en el resto del período: es concentración espacial dentro de un evento episódico, no una acumulación fija que persista mes tras mes.

Comparar la distribución completa de valores entre fechas (no solo el promedio), mediante histogramas, diagramas de caja y mapas de diferencia entre la primera y la última fecha de cada lago ([`histogramas_distribucion_atitlan.png`](informe/figuras/histogramas_distribucion_atitlan.png), [`histogramas_distribucion_amatitlan.png`](informe/figuras/histogramas_distribucion_amatitlan.png), [`boxplots_distribucion.png`](informe/figuras/boxplots_distribucion.png), [`mapa_diferencia_atitlan.png`](informe/figuras/mapa_diferencia_atitlan.png), [`mapa_diferencia_amatitlan.png`](informe/figuras/mapa_diferencia_amatitlan.png)), confirma que el cambio entre fechas no es un simple desplazamiento uniforme de todo el lago: en las fechas de floración, la distribución se ensancha hacia valores altos y los mapas de diferencia muestran zonas concretas con aumentos marcados junto a otras que apenas cambian.

Por último, se probó explícitamente si el patrón estacional ya observado en la sección 4 se sostiene al separar las fechas en temporada seca (noviembre–abril) y lluviosa (mayo–octubre) ([`patron_estacional.png`](informe/figuras/patron_estacional.png)). Aquí aparece una limitante del propio calendario de fechas: Amatitlán solo tiene **una** fecha oficial en temporada lluviosa, y es justamente la fecha atípica del 19 de junio de 2026, por lo que su comparación entre temporadas está dominada casi por completo por ese único dato. En Atitlán, con una muestra algo más balanceada, la diferencia entre temporada seca y lluviosa resulta mínima. Con las 22 fechas disponibles no hay evidencia sólida de una dicotomía simple "lluvia vs. seca"; lo que sí se sostiene en ambos lagos, como ya se señaló en la sección 4, es que los picos de floración se concentran hacia el **final de la temporada seca** (marzo-abril), y no de forma pareja durante todo el año.

En conjunto, esta exploración adicional matiza la comparación entre lagos: Amatitlán no solo florea con mayor intensidad promedio, sino que lo hace de forma más puntual, concentrada en un solo evento extremo; Atitlán, aunque menos intenso en promedio, reparte su floración relevante en más fechas. Pero en ninguno de los dos casos la cianobacteria se acumula de forma fija en el mismo punto del lago a lo largo de todo el período: ambos comportamientos son predominantemente episódicos. Esto sugiere una misma estrategia de monitoreo para los dos lagos: conviene vigilar la superficie completa del cuerpo de agua en las fechas de mayor riesgo (hacia el final de la temporada seca), en lugar de concentrar la vigilancia en un solo punto fijo de acumulación.
