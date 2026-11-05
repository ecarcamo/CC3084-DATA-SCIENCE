<style>
@page { size: letter; margin: 1.5cm 1.6cm; }
body { max-width: none; margin: 0; padding: 0; font-family: Arial, Helvetica, sans-serif; font-size: 10pt; line-height: 1.3; }
h1 { font-size: 18pt; margin: 0 0 .2em; color: #1F4E79; }
h2 { font-size: 14pt; margin: 1em 0 .3em; padding-bottom: 2px; border-bottom: 1.5px solid #1F4E79; color: #1F4E79; }
h3 { font-size: 11.5pt; margin: .8em 0 .25em; }
h4 { font-size: 10.5pt; margin: .6em 0 .2em; }
p, ul, ol { margin: .3em 0; }
li { margin: .1em 0; }
table { display: table; border-collapse: collapse; width: 100%; margin: .4em 0; font-size: 8.5pt; }
th, td { border: 1px solid #5B6B7A; padding: 2px 5px; vertical-align: top; }
th { background: #E7EFF6; text-align: left; }
pre { margin: .4em 0; padding: 5px 7px; background: #F4F6F8; border: 1px solid #DDE3E9; font-size: 7.5pt; }
pre, pre code { white-space: pre-wrap; overflow-wrap: anywhere; }
figure { margin: .4em 0; text-align: center; }
img { max-width: 100%; max-height: 7cm; }
figcaption { font-size: 8.5pt; color: #5B6B7A; }
</style>

# Lab 12 · Observatorio de turismo en Power BI — Avance

**Curso:** CC3066/CC3084 Data Science, UVG. **Equipo:** Diego, Esteban, Hugo, Ernesto. **Fecha:** 5 de noviembre de 2026. **Rama:** `lab12`. **Archivo:** `powerbi/observatorio_turismo.pbix` (v0.2). Detalle completo en `docs/lab12/01_diego_datos.md`, `02_hugo_diseno.md` y `03_esteban_gestion_y_comparacion.md`.

## 1. Preguntas de gestión, público y alcance (A1)

**Público:** directivos del sector turístico sin formación en estadística. Se conservan las ocho preguntas del Lab 10; se compara contra `lab10` (no `lab11`, que cambió G6–G7 y retiró G8).

| Lab 10 | Power BI | Pregunta | Página |
|---|---|---|---|
| G1 | V1 | ¿Cómo ha evolucionado el ingreso de viajeros? | Datos observados |
| G2 | V2 | ¿Qué vías o países concentran más viajeros? | Datos observados |
| G3 | V3 | ¿En qué meses se concentra el ingreso? | Estacionalidad y años |
| G4 | V4 | ¿Cómo cambia el total entre años completos? | Estacionalidad y años |
| G5 | V5 | ¿Cuánto cambió cada mes frente al año anterior? | Datos observados |
| G6 | V6 | ¿Qué estimaron los modelos frente a lo registrado? | Predicciones y modelos |
| G7 | V7 | ¿Qué modelo se equivoca menos? | Predicciones y modelos |
| G8 | V8 | ¿En qué meses se alejó el modelo? | Predicciones y modelos |

**Alcance:** 7 series mensuales (Total, 3 vías, 3 países), ene-2009 a jun-2026; predicciones existentes de 5 modelos (SARIMA, Holt-Winters, SES, Seasonal Naive, Prophet), abr-2021 a jun-2026 (63 meses); métricas MAE, RMSE y MAPE. No se entrenan modelos. **Fuera de alcance:** causas de los cambios, pronósticos futuros, mezclar vías con países, comparar años incompletos.

## 2. Paleta (A2)

Se mantiene el significado de colores del Lab 10 en `powerbi/tema_observatorio.json`, fuente Arial.

| Uso | Color | Justificación |
|---|---|---|
| Observado | Azul `#1F4E79` | Color estable para datos registrados. |
| Estimado | Naranja `#A65E16` | Contrasta con el azul; separa estimación de observación. |
| Selección | Verde `#20745A` | Solo selección y página activa. |
| Alerta / sin datos | Rojo `#B3261E` | Siempre con texto de advertencia. |
| Fondo / tarjetas | `#F4F6F8` / `#FFFFFF` | Separa lienzo y contenido sin competir con los datos. |
| Estacionalidad | `#E7EFF6` → `#1F4E79` | Escala secuencial equivalente a G3. |

## 3. Planificación (A3)

| Tarea | Responsable | Fecha | Estado |
|---|---|---|---|
| Importación, relaciones y medidas (A5) | Diego | 5-nov | Hecho |
| Paleta, tema, boceto, V1–V2 enlazadas (A2, A4, A6) | Hugo | 5-nov | Hecho |
| Preguntas, planificación y protocolo (A1, A3, A7) | Esteban | 5-nov | Hecho |
| Consolidación y entrega del avance | Ernesto | 5-nov | Hecho |
| Especificación V5–V8 | Esteban | 6-nov | Pendiente |
| V5–V8 en Power BI | Diego | 7-nov | Pendiente |
| V3, V4, navegación, marcadores, restablecer, drillthrough | Hugo | 7-nov | Pendiente |
| Tres pruebas en ambas versiones, verificación de indicadores | Esteban, Ernesto | 7-nov | Pendiente |
| Costos y licencias, matriz, recomendaciones, documento final | Ernesto | 8-nov | Pendiente |

## 4. Boceto y navegación (A4)

Cinco páginas: **Inicio**, **Datos observados** (V1, V2, V5), **Estacionalidad y años** (V3, V4), **Predicciones y modelos** (V6–V8) y **Detalle de serie** (drillthrough desde V2 o V7). Cada página tendrá barra de navegación y botón «Restablecer vista».

![Boceto de las cinco páginas](../figuras/lab12_hugo_boceto.png)

## 5. Importación de datos y resultados de modelos (A5)

Power Query con parámetro `RutaInsumos` (configuración regional en-US para el punto decimal). Modelo estrella: dimensiones `DimSerie`, `DimModelo` y `Calendario` filtran en una dirección a los hechos `Observaciones` (1.470 filas), `Predicciones` (2.205) y `Metricas` (35). No hay relaciones entre hechos, por lo que lo observado no se multiplica por modelo. Medidas base: `Viajeros`, `Viajeros serie` (Total por defecto), `Estimado` y `Diferencia`. Control: total 2025 = 3.597.238; total 2020 = 1.266.340; MAE SES total = 175.088,44 (coinciden con los CSV).

![Página Control](../figuras/lab12_diego_control.png)

## 6. Visualizaciones enlazadas V1 y V2 (A6)

V2 (ranking de vías o países, sin Total) filtra a V1 (evolución con jerarquía Año > Trimestre > Mes) mediante «Editar interacciones → Filtrar», no con un segmentador. Al seleccionar «Vía Aérea» en V2, V1 muestra su historia completa; sin selección vuelve a Total.

![Estado inicial](../figuras/lab12_hugo_v1_v2_inicial.png)

![Vía Aérea seleccionada en V2 y reflejada en V1](../figuras/lab12_hugo_v1_v2_seleccion.png)

## 7. Criterios de comparación y protocolo de pruebas (A7)

**Criterios:** facilidad de aprendizaje, tiempo de desarrollo, preparación y actualización de datos, integración de modelos, interacción y navegación, personalización, rendimiento, control de versiones, requisitos para compartir, costos y licencias.

| Prueba | Tarea en ambas versiones | Valor esperado |
|---|---|---|
| 1 | Vía con más viajeros en 2025 usando filtros | Terrestre, 2.401.323 |
| 2 | Del total anual 2020 al detalle trimestral y regreso | 1.266.340; T2 = 31.635 |
| 3 | Comparar SARIMA, Holt-Winters y SES en la serie Total | SES, MAE 175.088,44 |

Mismo equipo y CSV, estado inicial limpio; se registran clics, tiempo y dificultades.
