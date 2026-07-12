# CC3084 - Data Science: Ejercicio en clase - Lectura de otras fuentes

## Descripción del ejercicio

Este repositorio contiene el desarrollo del ejercicio en clase "Lectura de
otras fuentes", cuyo objetivo es construir un pipeline automatizado para
descargar, consolidar y explorar los datos públicos de importación de
vehículos que publica el Portal SAT (Superintendencia de Administración
Tributaria de Guatemala). La fuente original es la sección "Importación de
Vehículos" del portal
(https://portal.sat.gob.gt/portal/alza-e-importacion-vehiculos/), que
publica un archivo mensual en formato .zip con el detalle de cada póliza
de importación de vehículos ingresada al país.

El objetivo del ejercicio es responder, con datos reales y actualizados, un
conjunto de preguntas de negocio sobre el comportamiento de la importación
de vehículos livianos en Guatemala durante 2025 y lo transcurrido de 2026.

El ejercicio cubre todo el recorrido de un flujo de datos: extracción desde
una fuente web, limpieza y unificación de archivos heterogéneos, control de
calidad de datos, y análisis exploratorio con visualizaciones.

## Estructura del repositorio

```
DATA_SCIENCE/
├── main.py                    Orquestador del pipeline (fases 1 a 4)
├── requirements.txt           Dependencias del proyecto
├── src/
│   ├── download.py            Fase 1: descarga de los .zip desde el Portal SAT
│   ├── extract.py             Fase 2: descompresión de los .zip
│   ├── build_dataset.py       Fase 3: construcción del dataset unificado
│   └── save_dataset.py        Fase 4: guardado del dataset en .csv
├── Datos/                     Datos generados por el pipeline (no versionados)
│   ├── zips/                  Archivos .zip descargados del Portal SAT
│   ├── raw/                   Archivos .txt descomprimidos, uno por mes
│   └── importacion_vehiculos.csv   Dataset unificado final
├── exploracion/
│   └── exploracion_importacion_vehiculos.ipynb   Notebook de análisis exploratorio
└── venv/                      Entorno virtual de Python (no versionado)
```

## Fuente de datos

El Portal SAT publica, mes a mes, un archivo .zip por cada periodo con el
detalle de las pólizas de importación de vehículos. Cada .zip contiene un
único archivo de texto delimitado por el carácter "|", en codificación
ISO-8859-1, con las siguientes 17 columnas: país de proveniencia, aduana de
ingreso, fecha de la póliza, partida arancelaria, año-modelo del vehículo,
marca, línea, centímetros cúbicos, distintivo (liviano o pesado), tipo de
vehículo, tipo de importador, tipo de combustible, asientos, puertas,
tonelaje, valor CIF e impuesto.

Para este ejercicio se descargó el histórico completo de 2025 (12 meses) y
lo transcurrido de 2026 (enero a junio, que es lo publicado por el Portal
SAT al momento de correr el pipeline).

## El pipeline

El pipeline está organizado en cuatro fases, cada una implementada como una
función independiente en su propio módulo dentro de `src/`, y orquestadas
desde `main.py`.

**Fase 1 - Descarga (`download_zip_from_SAT`)**: consulta la página del
Portal SAT, identifica todos los enlaces de descarga disponibles para los
años configurados, y descarga cada .zip a `Datos/zips/`. Es idempotente: si
un archivo ya fue descargado, no se vuelve a descargar.

**Fase 2 - Descompresión (`extract_zips`)**: descomprime cada .zip y guarda
el .txt resultante en `Datos/raw/`, renombrado de forma consistente
(`importacion_vehiculos_<año>_<mes>.txt`), ya que el nombre interno del
archivo original no identifica el periodo al que corresponde.

**Fase 3 - Construcción del dataset unificado (`build_unified_dataset`)**:
lee los 18 archivos mensuales, limpia y homologa los nombres de columnas,
convierte los tipos de dato (fechas, montos, cantidades), agrega columnas
derivadas de año y mes a partir de la fecha real de la póliza, y consolida
todo en un único DataFrame.

**Fase 4 - Guardado (`save_dataset_to_csv`)**: exporta el DataFrame
unificado a `Datos/importacion_vehiculos.csv`.

Para ejecutar el pipeline completo:

```
source venv/bin/activate
python main.py
```

## Calidad de datos: hallazgos durante la construcción del pipeline

Durante la construcción de la fase 3 se identificaron y corrigieron dos
problemas de la fuente de datos que, de no atenderse, habrían corrompido el
dataset de forma silenciosa:

**Desalineación de columnas por el delimitador final.** Cada fila de datos
trae un carácter "|" adicional al final (un campo vacío de cierre), pero el
encabezado del archivo solo declara 17 nombres de columna. Al leer el
archivo con la configuración por defecto de pandas, esta diferencia de un
campo hace que la librería interprete la primera columna como un índice y
desplace el resto de los valores una posición, mezclando por ejemplo el
país de proveniencia con la aduana de ingreso. La solución fue forzar
`index_col=False` en la lectura.

**Filas con un delimitador adicional dentro de un campo.** Se encontraron 5
filas (las 5 correspondientes a un mismo registro de maquinaria pesada,
"BUSH HOG LOADCRAFT", en el archivo de julio de 2025) donde el campo de
centímetros cúbicos contiene un formato de medida de neumático con un "|"
de más, rompiendo el conteo esperado de columnas. El mecanismo estándar de
pandas para descartar filas problemáticas (`on_bad_lines="skip"`) no las
descartaba: las truncaba y desplazaba sus valores, perdiendo el impuesto
real y corrompiendo el campo de distintivo. Se implementó un filtrado
manual, línea por línea, que identifica y descarta explícitamente estas
filas antes de pasarlas a pandas, reportando en consola cuántas se
eliminaron.

**Resultado**: el dataset final tiene 1,078,487 filas y 19 columnas. La
suma de filas de datos de los 18 archivos originales es de 1,078,492; la
diferencia corresponde exactamente a las 5 filas malformadas descartadas.

**Valores de año-modelo fuera de rango.** El campo de año-modelo del
vehículo contiene algunos valores de captura evidentemente erróneos (por
ejemplo, 1900 o 3351). Estos valores no se eliminan del dataset unificado,
pero se excluyen puntualmente de la visualización de distribución por
año-modelo (pregunta 2) para no distorsionar la gráfica; la cantidad
excluida se reporta explícitamente en el notebook.

**Corte de fecha en el archivo más reciente.** El archivo de junio de 2026
se publica en julio de 2026 y por lo tanto incluye pólizas con fecha real
de julio. Esto significa que el mes de julio de 2026 está incompleto en el
dataset. Para la comparación interanual (pregunta 5) se usan únicamente los
meses de enero a junio, que son los que están completos en ambos años.

## Análisis exploratorio

El análisis exploratorio completo, con el código, las tablas y las
gráficas, está en `exploracion/exploracion_importacion_vehiculos.ipynb`. A
continuación se resumen las respuestas a las preguntas planteadas para el
ejercicio, usando 2025 como "el año pasado" y 2026 como el año en curso.

Para la clasificación de carros, pickups y SUV se usó el campo
`Tipo_Vehiculo` del dataset, mapeado de la siguiente forma según se
verificó contra las marcas y líneas reales de los vehículos: `AUTOMOVIL`
corresponde a carros (por ejemplo, Mazda 3, Civic, Prius), `PICK UP`
corresponde a pickups (por ejemplo, Tacoma, Ranger, Frontier), y
`CAMIONETA` corresponde a SUV (por ejemplo, RAV4, Santa Fe, X1, Q7).

### ¿Cuántos vehículos livianos de cada tipo se importaron en 2025?

En 2025 se importaron 674,255 vehículos livianos. La distribución por tipo
fue la siguiente:

| Tipo de vehículo   | Cantidad |
|--------------------|----------|
| Moto               | 508,620  |
| Camioneta          | 60,821   |
| Pick up            | 48,907   |
| Automóvil          | 34,634   |
| Trimoto            | 14,256   |
| Microbús           | 1,960    |
| Camionetilla       | 1,789    |
| Panel              | 925      |
| Jeep               | 846      |
| Vehículo rústico   | 757      |
| Camioneta sport    | 523      |
| Camioneta agrícola | 189      |
| Minibús            | 10       |
| Araña              | 6        |
| Carro fúnebre      | 4        |
| Carreta-carretón   | 4        |
| Monta carga        | 3        |
| Mini tractor       | 1        |

Las motocicletas concentran la gran mayoría de las importaciones de
vehículos livianos: aproximadamente el 75 por ciento del total.

### ¿Cuál es la distribución de modelos (año-modelo) de carros, pickups y SUV que se importaron el año pasado?

Tomando el año-modelo del vehículo (no el nombre comercial) para los
vehículos livianos de 2025, y descartando 7,021 registros con año-modelo
fuera de un rango plausible (1990-2027) de un total de 144,362, la
distribución se concentra en vehículos relativamente recientes, con dos
patrones claros:

- Para carros (automóviles) y SUV, el grueso de las importaciones
  corresponde a modelos de entre 5 y 12 años de antigüedad respecto a 2025
  (años-modelo 2013 a 2020), lo que es consistente con un mercado de
  vehículos usados reacondicionados.
- Para pickups, en cambio, la importación se concentra fuertemente en
  modelos recientes o del mismo año (2025 y 2026), con 2,504 y 12,995
  unidades respectivamente, muy por encima de cualquier año-modelo
  anterior.

En términos generales, las SUV son la categoría con mayor volumen en casi
todos los años-modelo intermedios (2013 a 2019), mientras que los
automóviles pierden peso de forma sostenida a medida que el año-modelo se
acerca al presente, y las pickups muestran el patrón opuesto: crecen con
fuerza en los años-modelo más nuevos.

### ¿Cuál es el tipo de vehículo que más se importó el año pasado?

Considerando todos los vehículos importados en 2025 (livianos y pesados),
el tipo más importado fue moto, con 508,620 unidades, muy por encima del
segundo lugar (camioneta, con 60,822 unidades). El top 10 fue:

| Tipo de vehículo | Cantidad |
|-------------------|---------|
| Moto              | 508,620 |
| Camioneta         | 60,822  |
| Pick up           | 48,907  |
| Automóvil         | 34,634  |
| Camión            | 17,753  |
| Cuatrimoto        | 14,604  |
| Trimoto           | 14,256  |
| Cabezal           | 9,061   |
| Scooter           | 6,350   |
| Microbús          | 3,255   |

### ¿Cuáles son los meses en los que más se importan vehículos livianos?

En 2025, los meses con mayor importación de vehículos livianos fueron:

| Mes        | Cantidad |
|------------|----------|
| Septiembre | 63,281   |
| Julio      | 62,781   |
| Octubre    | 62,597   |
| Enero      | 59,474   |
| Agosto     | 58,317   |
| Abril      | 56,978   |
| Diciembre  | 56,762   |
| Febrero    | 55,608   |
| Mayo       | 54,755   |
| Junio      | 54,317   |
| Marzo      | 48,497   |
| Noviembre  | 40,888   |

El mes con más importaciones de livianos fue septiembre (63,281 unidades),
seguido de cerca por julio y octubre. El tercer trimestre del año (julio a
septiembre) concentra el mayor volumen, mientras que noviembre es
consistentemente el mes más bajo.

### ¿Cómo vamos con la importación de cada tipo de vehículo en los meses que llevamos de este año en comparación con el año pasado?

Comparando enero a junio de 2026 contra el mismo periodo de 2025 (los seis
meses completos disponibles en ambos años), el total de vehículos
importados cayó de 357,685 a 322,112 unidades, una variación de -9.9 por
ciento. Sin embargo, este resultado agregado esconde comportamientos muy
distintos por tipo de vehículo:

| Tipo de vehículo   | Ene-Jun 2025 | Ene-Jun 2026 | Variación |
|--------------------|-------------:|-------------:|----------:|
| Moto               | 250,830      | 198,439      | -20.9 %   |
| Camioneta          | 29,197       | 34,362       | +17.7 %   |
| Pick up            | 21,760       | 26,578       | +22.1 %   |
| Automóvil          | 16,823       | 18,569       | +10.4 %   |
| Camión             | 8,539        | 10,277       | +20.4 %   |
| Trimoto            | 7,705        | 7,090        | -8.0 %    |
| Cuatrimoto         | 6,635        | 7,710        | +16.2 %   |
| Cabezal            | 3,726        | 4,542        | +21.9 %   |
| Scooter            | 2,700        | 3,504        | +29.8 %   |
| Microbús           | 1,578        | 1,866        | +18.3 %   |
| Camión furgón      | 1,096        | 1,118        | +2.0 %    |
| Furgón             | 884          | 937          | +6.0 %    |
| Camionetilla       | 821          | 810          | -1.3 %    |
| Bus                | 668          | 697          | +4.3 %    |
| Porta contenedor   | 545          | 797          | +46.2 %   |

La caída total está explicada casi en su totalidad por las motocicletas,
que retroceden 20.9 por ciento y son, con amplio margen, la categoría de
mayor volumen. En contraste, prácticamente todas las demás categorías
crecen: camionetas (SUV), pick up, automóviles y vehículos de carga pesada
(camión, cabezal, furgón) muestran incrementos de entre 2 y 46 por ciento.
Esto sugiere que la contracción del mercado de importación de vehículos en
2026 no es generalizada, sino que está concentrada en el segmento de
motocicletas, mientras que el segmento de vehículos livianos de cuatro
ruedas (camionetas, pick up y automóviles) e incluso el de carga se
encuentra en expansión respecto al año anterior.

## Cómo reproducir el ejercicio

```
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python main.py

jupyter notebook exploracion/exploracion_importacion_vehiculos.ipynb
```

`Datos/` y `venv/` no se versionan en el repositorio (ver `.gitignore`), ya
que corresponden a datos descargados y a un entorno local reproducible a
partir de `requirements.txt`.
