# 4. Análisis de las series de tiempo

## Criterio común

Las siete series se estudiaron sobre el conjunto de entrenamiento, desde
enero de 2009 hasta marzo de 2021, con frecuencia mensual y 147
observaciones. Este corte evita usar información del test durante el
diagnóstico.

Se aplicó `log1p` de manera uniforme. La amplitud de las oscilaciones crece
con el nivel en varias series y cuatro de ellas contienen ceros. Por esa
razón, una descomposición multiplicativa en niveles no es válida. La
descomposición aditiva sobre `log1p` representa cambios proporcionales y
tolera los ceros, lo que permite comparar todas las series bajo el mismo
criterio.

Los factores estacionales se estimaron con el tramo prepandemia. Un factor
mayor que uno identifica un mes por encima del nivel medio, mientras uno
menor que uno indica un valle. La estacionariedad en media se contrastó con
ADF al 5 % en niveles transformados, con una diferencia regular y con una
diferencia regular más otra estacional de orden 12.

## Total de viajeros

La serie total tiene media mensual de 237,121 viajeros. Su mínimo es 9,779
en mayo de 2020 y el máximo, 515,820 en diciembre de 2019. El gráfico muestra
crecimiento hasta 2019, estacionalidad anual y una ruptura abrupta durante
el cierre de fronteras.

Diciembre es el pico estacional, con factor 1.372, y septiembre el valle,
con 0.802. Esta concentración implica mayor demanda de personal, control y
servicios turísticos al cierre del año. La desviación estándar aumenta de
31,782 en 2009-2013 a 74,036 en 2014-2019, evidencia de varianza asociada al
nivel que justifica `log1p`.

El ADF en niveles produce p=0.1936, por lo que no se rechaza raíz unitaria.
Con d=1 el p-valor baja a 0.0265 y con d=1, D=1 a menos de 0.0001. La ACF en
niveles presenta persistencia y señal anual; luego de diferenciar se acorta.
Se concluye d=1 y D=1.

## Vía aérea

La media de la vía aérea es 89,141 viajeros por mes. Se observa un mínimo de
489 en abril de 2020 y un máximo de 157,842 en diciembre de 2019. Antes del
cierre existe una tendencia creciente con oscilación anual clara.

El máximo estacional ocurre en diciembre, con factor 1.288, y el mínimo en
septiembre, con 0.815. Para INGUAT, esto sugiere concentrar capacidad
aeroportuaria y atención turística en el cierre del año. La desviación
estándar pasa de 11,554 a 18,464 entre los dos tramos prepandemia, por lo que
la transformación reduce una variación que aumenta con el nivel.

Aunque el ADF en niveles rechaza raíz unitaria con p=0.0013, la ACF conserva
persistencia y estacionalidad. Los resultados con d=1, p=0.0192, y d=1,
D=1, p menor que 0.0001, respaldan una especificación comparable que absorbe
la señal anual. Se emplean d=1 y D=1, con vigilancia de sobrediferenciación.

## Vía terrestre

La vía terrestre concentra una media mensual de 139,988 viajeros. Su mínimo
es 5,715 en diciembre de 2020 y alcanza 348,626 en diciembre de 2019. La
trayectoria crece con fuerza antes de la pandemia y luego se contrae.

Diciembre tiene el factor máximo, 1.400, y febrero el mínimo, 0.806. El
patrón respalda refuerzos fronterizos y de transporte durante las fiestas de
fin de año. La desviación estándar crece de 20,032 a 57,068 viajeros, una
diferencia marcada que `log1p` ayuda a estabilizar.

La ACF en niveles decae lentamente y muestra dependencia en el rezago 12. El
ADF no rechaza raíz unitaria en niveles, p=0.5619, pero sí con d=1,
p=0.0091, y con d=1, D=1, p menor que 0.0001. En consecuencia, se fijan d=1
y D=1.

## Vía marítima

Marítima es la serie más irregular. Su media es 7,991 viajeros, el máximo es
29,506 en enero de 2018 y existen 16 observaciones iguales a cero. Los ceros
incluyen meses aislados antes de la pandemia y el cierre prolongado al final
del entrenamiento. La desviación estándar cambia de 5,148 a 7,742 viajeros.

El factor prepandemia máximo corresponde a diciembre, 3.328, y el mínimo a
junio, 0.153. La amplitud extrema y los cambios de nivel hacen que esos
factores sean menos estables que en las otras vías, por lo que no deben
usarse como una regla operativa rígida.

El ADF arroja p=1.0000 en niveles, p=0.5750 con d=1 y p=0.1327 con d=1,
D=1. Tampoco d=2 resuelve el problema, pues obtiene p=0.6994. Por tanto, no
se afirma estacionariedad al 5 %. Se explora d=2 y D=1 en modelación, pero la
conclusión estadística sigue siendo que persiste una raíz unitaria.

La serie también cambia de régimen fuera del train. El total anual pasa de
130,789 viajeros en 2019 a 41,992 en 2020 y 3,908 en 2021. Tras una
recuperación a 26,030 en 2022, se estabiliza en solo 6,617, 6,605 y 6,944
viajeros durante 2023, 2024 y 2025. Este nivel es muy inferior al
prepandemia y limita cualquier extrapolación de la historia anterior.

## País de residencia: El Salvador

La serie tiene media mensual de 61,502 viajeros, máximo de 165,263 en agosto
de 2019 y cinco ceros, correspondientes al cierre de abril a agosto de 2020.
El gráfico combina crecimiento previo, patrón anual y ruptura pandémica.

Diciembre es el pico, con factor 1.381, y febrero el valle, con 0.800. El
resultado ayuda a anticipar presión en fronteras terrestres al cierre del
año. La desviación estándar sube de 9,515 a 28,199 viajeros, de modo que
`log1p` estabiliza una heterocedasticidad importante.

El ADF en niveles no rechaza raíz unitaria, p=0.4325. Con d=1 y con d=1,
D=1 los p-valores son menores que 0.0001. La ACF diferenciada pierde la
persistencia de niveles, por lo que se adoptan d=1 y D=1.

## País de residencia: Estados Unidos

La media mensual es 27,955 viajeros. La serie alcanza 54,990 en julio de
2019 y presenta cinco ceros durante abril-agosto de 2020. Antes de ese
quiebre mantiene crecimiento y una temporada alta de mitad de año.

Julio registra el factor máximo, 1.449, y septiembre el mínimo, 0.606. Esto
señala mayor demanda turística y aeroportuaria durante el verano boreal. La
desviación estándar aumenta de 6,840 a 9,226 viajeros; el cambio es menor que
en El Salvador, pero aún favorece la escala logarítmica.

El ADF en niveles queda en el límite, con p=0.0501. La primera diferencia
rechaza raíz unitaria con p=0.0307 y la combinación d=1, D=1 lo hace con
p menor que 0.0001. Junto con la señal anual de la ACF, esto lleva a d=1 y
D=1.

## País de residencia: Honduras

Honduras promedia 9,124 viajeros mensuales y alcanza 23,061 en enero de
2020. También contiene cinco ceros por el cierre de abril-agosto de 2020. La
tendencia prepandemia es ascendente, con una estacionalidad menos extrema
que la de Estados Unidos.

Enero es el pico, con factor 1.216, y febrero el valle, con 0.824. El patrón
aconseja reforzar atención terrestre al inicio del año. La desviación
estándar pasa de 1,366 a 3,717 viajeros, por lo que `log1p` mejora la
estabilidad de la varianza.

El ADF ya rechaza raíz unitaria en niveles con p=0.0040. Aun así, la ACF
muestra persistencia y señal estacional. Con d=1 y con d=1, D=1 los
p-valores son menores que 0.0001. Se usan d=1 y D=1 para capturar esa
estructura y mantener comparabilidad, revisando posible sobrediferenciación.

## Comparación de estacionariedad

| Serie | Media | Ceros | ADF nivel | ADF d=1 | ADF d=1, D=1 | d | D |
|---|---:|---:|---:|---:|---:|---:|---:|
| Total | 237,121 | 0 | 0.1936 | 0.0265 | <0.0001 | 1 | 1 |
| Vía aérea | 89,141 | 0 | 0.0013 | 0.0192 | <0.0001 | 1 | 1 |
| Vía terrestre | 139,988 | 0 | 0.5619 | 0.0091 | <0.0001 | 1 | 1 |
| Vía marítima | 7,991 | 16 | 1.0000 | 0.5750 | 0.1327 | 2 | 1 |
| El Salvador | 61,502 | 5 | 0.4325 | <0.0001 | <0.0001 | 1 | 1 |
| Estados Unidos | 27,955 | 5 | 0.0501 | 0.0307 | <0.0001 | 1 | 1 |
| Honduras | 9,124 | 5 | 0.0040 | <0.0001 | <0.0001 | 1 | 1 |

La conclusión común es que la diferenciación regular y estacional resulta
adecuada para seis series. Marítima queda como excepción: sus ceros, quiebres
y cambio de régimen impiden sostener estacionariedad incluso después de
aplicar diferencias adicionales.
