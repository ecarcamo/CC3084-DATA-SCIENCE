# Datos y limpieza

## Origen y dimensiones

La base de datos contiene el registro mensual del ingreso de viajeros internacionales a Guatemala
entre enero de 2009 y junio de 2026: 210 meses consecutivos, sin huecos, y 161,036 registros en
formato largo (una fila por combinación de mes, vía de ingreso, frontera, país o agrupación de
residencia y tipo de viajero). Los datos se proporcionan únicamente para uso académico y no
corresponden a cifras oficiales de INGUAT ni del Instituto Guatemalteco de Migración.

La base combina tres tramos con distinta fuente y metodología: 2009-2020 proviene de respaldos
históricos, 2021-2022 de una entrega del Instituto Guatemalteco de Migración, y 2023 en adelante
de un sistema depurado de conteos de INGUAT. Esto implica que los niveles no siempre son
perfectamente comparables entre tramos, en particular alrededor del quiebre metodológico de
2022 a 2023.

Además, desde 2023 la columna de país deja de reportar país individual (226 posibles hasta 2022)
y pasa a reportar por agrupación de mercado (27 grupos). Los mercados principales —El Salvador,
Estados Unidos, Honduras, México, entre otros— siguen siendo comparables como serie a lo largo de
todo el período; los países más pequeños quedan absorbidos dentro de su agrupación a partir de
2023.

## Limpieza aplicada

Sobre la base cruda se detectaron y corrigieron cuatro inconsistencias, sin eliminar ninguna fila
y conservando siempre el valor original en una columna paralela con sufijo `_raw`:

- **Región dos**: la categoría de cruceros aparece partida en dos etiquetas según el año
  ("Cruceristas" de 2009 a 2021, "Cruceros" en 2022), cuando en realidad es la misma categoría.
  Se unificó en un solo valor. Adicionalmente existía el valor literal `"0"` en 13 registros de
  2022 (821 viajeros), que se reetiquetó como "Sin especificar".
- **País**: se detectaron 13 pares de valores que representan el mismo país pero con capitalización
  distinta (por ejemplo, "OTROS PAISES DEL MUNDO" frente a "Otros Paises Del Mundo", o variantes
  con conectores en mayúscula como "República De Corea"). En todos los casos la variante mal
  escrita corresponde a un puñado de registros aislados de 2020-2021, mientras que la forma
  correcta se usa de manera consistente en el resto del período. Se unificaron ambas hacia la
  variante con más registros.
- **Regiones OMT**: existían los valores basura `"0x2a"` y `"SIN ESPECIFICAR"`, que se unificaron
  en la etiqueta "Sin especificar".
- **Frontera**: la categoría "Cruceros" aparece mezclada en la misma columna junto con fronteras
  terrestres, aéreas y marítimas legítimas (y junto con la categoría genérica "Otra frontera").
  Se decidió no modificarla, ya que corregirla requeriría inventar una frontera específica que no
  está en los datos; queda documentado aquí para quien la use más adelante.
- **Viajero**: 51,272 registros (cerca de un tercio de la base) tienen valores decimales. No son
  errores: corresponden a estimaciones y prorrateos de la fuente, no a conteos exactos de
  personas. Además, 54 registros valen exactamente 0. En ningún caso se redondeó ni se descartó
  esta información; se documenta como una característica conocida de los datos.

Tras aplicar la limpieza se confirmó por código que la base no contiene valores nulos ni filas
duplicadas exactas.

## Decisiones fijadas

**Guatemala como país de residencia.** El valor "Guatemala" en la columna de país acumula
aproximadamente 14.8 millones de viajeros a lo largo de todo el período, un 28% del total. Estos
registros corresponden a residentes guatemaltecos que regresan al país, no a viajeros
internacionales entrantes en el sentido habitual. Se decidió **mantenerlos dentro de la serie
total** de viajeros, para no alterar el total oficial reportado por la fuente, pero
**excluirlos del ranking de países de residencia**. Bajo este criterio, el Top 3 de países de
residencia queda: El Salvador, Estados Unidos de América y Honduras.

**2026 como año parcial.** El último año de la base solo cubre de enero a junio. Cualquier
comparación de totales anuales que incluya 2026 debe advertir explícitamente que ese año está
incompleto; no es comparable en la misma base que los años completos.

**Quiebre en "Tipo de Viajero".** Esta variable toma cuatro valores: Turista, Excursionista,
Viajero y Cruceristas. Entre 2022 y 2023 la categoría "Viajero" cae fuertemente (de
aproximadamente 1.06 millones a 0.33 millones) porque el sistema depurado de 2023 excluye a los
viajeros no turísticos de alta frecuencia (comercio fronterizo, tránsito), mientras que el tramo
anterior sí los incluía. Esta caída es un efecto de cambio de criterio metodológico, no una caída
real de actividad, y debe tenerse en cuenta al interpretar la serie total o cualquier serie que
dependa de esta variable. Para comparaciones de visitantes consistentes en todo el período se
recomienda usar la suma de Turista + Excursionista.

## Split de entrenamiento y prueba

El split es temporal, nunca aleatorio, sobre los 210 meses de la base:

- **Entrenamiento**: 2009-01 a 2021-03 (147 meses, 70% de los datos).
- **Prueba**: 2021-04 a 2026-06 (63 meses, 30% de los datos).

Este corte no es arbitrario: deja la caída provocada por la pandemia (colapso a partir de marzo de
2020, con un piso en 2020-2021 de aproximadamente 27% del nivel de 2019) **dentro** del conjunto
de entrenamiento, mientras que la **recuperación completa** posterior a 2022 queda **dentro** del
conjunto de prueba. Esto significa que cualquier modelo entrenado con este split aprende a partir
de un choque y su punto más bajo, pero es evaluado prediciendo una dinámica de recuperación
distinta a la que vio durante el entrenamiento. Es un punto que debe justificarse explícitamente
al interpretar el desempeño de los modelos, no una limitación que deba ocultarse.

## Series construidas

Las categorías de análisis elegidas por el equipo son **vías de ingreso** y **países de residencia
(Top 3, excluyendo Guatemala)**. Todas las series son mensuales, con exactamente dos columnas
(`fecha` y `viajeros`) e índice completo sin huecos (los meses sin registros quedan en 0). Cada
serie tiene además una versión de entrenamiento truncada a 2021-03.

| Serie | Inicio | Fin | Frecuencia |
|---|---|---|---|
| Total de viajeros | 2009-01 | 2026-06 | Mensual |
| Vía aérea | 2009-01 | 2026-06 | Mensual |
| Vía terrestre | 2009-01 | 2026-06 | Mensual |
| Vía marítima | 2009-01 | 2026-06 | Mensual |
| País: El Salvador | 2009-01 | 2026-06 | Mensual |
| País: Estados Unidos de América | 2009-01 | 2026-06 | Mensual |
| País: Honduras | 2009-01 | 2026-06 | Mensual |

Se verificó por código que la suma de las series de las tres vías de ingreso reproduce, mes a mes,
la serie total de viajeros.
