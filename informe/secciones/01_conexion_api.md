# Inciso 1. Conexión con el API de Sentinel Hub

## Metodología

Se establece la conexión con Sentinel-2 a través de `sentinelhub-py`, sobre la infraestructura del Copernicus Data Space Ecosystem (CDSE). Se descarta el uso de openEO como mecanismo principal: openEO no expone una forma de ejecutar el evalscript del script de detección de cianobacteria requerido en el inciso 3, por lo que su inclusión solo agregaría una segunda librería y un segundo flujo de autenticación sin aportar al análisis.

Las credenciales (un OAuth client de tipo `sh_client_id` / `sh_client_secret`) se generan en el panel de CDSE y se almacenan en el archivo de configuración global de la librería (`~/.config/sentinelhub/config.toml`), bajo un perfil dedicado (`cdse`), fuera de este repositorio. Como respaldo, se admite la lectura de las variables de entorno `SH_CLIENT_ID` y `SH_CLIENT_SECRET` cuando el perfil no está disponible, lo que permite ejecutar el mismo código en otra máquina o en un entorno de CI sin modificar nada.

La conexión se verifica solicitando un token OAuth real (`SentinelHubSession`) y se confirma consultando la Catalog API para las 22 fechas oficiales del enunciado (11 por lago), usando el bounding box de cada lago.

## Resultados

La autenticación se realiza correctamente contra `https://sh.dataspace.copernicus.eu`, con emisión de un token válido. La consulta al catálogo encuentra una escena Sentinel-2 L1C para cada una de las 22 fechas oficiales, sin fechas sin cobertura.

Se compara la nubosidad reportada por el catálogo, calculada sobre la escena completa (~110x110 km), contra la nubosidad oficial del enunciado, calculada sobre el polígono de cada lago. Ambas series difieren en magnitud, como es esperable dado que corresponden a áreas distintas, pero mantienen una tendencia consistente: las fechas con mayor nubosidad oficial también presentan valores más altos en el catálogo. El caso más marcado es `2026-06-19` en Amatitlán, donde la nubosidad de la escena completa alcanza cerca del 77%, mientras que la nubosidad oficial sobre el lago es de apenas 13%, lo que indica que la nubosidad se concentra fuera del área del lago en esa fecha.

Se documenta explícitamente el caso de `2026-02-07` en Amatitlán, incluido en las fechas oficiales pese a tener una cobertura válida parcial (~57.1%), para que el análisis temporal del inciso 4 la trate con la debida cautela.

## Decisiones técnicas

- Colección: `sentinel-2-l1c`, redefinida con el `service_url` del CDSE mediante `DataCollection.define_from`.
- Resolución de trabajo: 20 metros. A 10 metros el bounding box de Atitlán produce una imagen de aproximadamente 2750x1730 píxeles, que excede el límite de 2500x2500 píxeles de la Process API. Además, la banda B05, usada en el índice NDCI del script de cianobacteria, es nativamente de 20 metros, por lo que trabajar a esa resolución no implica pérdida de información real.
- No se utilizan los archivos geojson de los lagos porque no fueron provistos; la máscara de agua se deriva del propio detector incluido en el script de cianobacteria (inciso 3).
