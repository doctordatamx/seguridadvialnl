# Inteligencia territorial 0.2: protocolo experimental

## Referencia del IPIV

IPIV experimental 2025, H3 resolución 7. Población fijada una vez: todas las celdas con al menos veinte registros geolocalizados en 2024 y veinte en 2025. Esta selección condiciona el universo: no es una evaluación de todas las vías ni de riesgo absoluto. Una misma celda mantiene ID, valores normalizados y score al cambiar filtros. No se mezcla con datos parciales de 2026.

Dimensiones: frecuencia de registros 2025 (30%), personas fallecidas registradas (30%), lesionadas (20%), cambio relativo de registros 2025/2024 (10%), registros con evidencia documentada de usuario vulnerable (10%). Esta última es un proxy de registro que no prueba ausencia de usuarios ni cuenta personas. No se asigna responsabilidad por posición de vehículo. Pesos y umbrales 25/50/75 son hipótesis sin validación científica.

Valores clínicos entre uno y cuatro se suprimen, con una segunda supresión cuando queda un único grupo pequeño. La supresión se realiza ANTES de calcular ratios, normalizar, correlacionar, simular o producir índices públicos. Si falta una dimensión esencial, el IPIV es no calculable aunque su peso sea cero. No se redistribuye ese peso ni se sustituye el nulo por cero. Los rankings de IPIV describen sólo casos completos, que pueden constituir una selección sesgada: nunca asumir que una celda incompleta tiene menor prioridad.

Métodos: Min-Max; percentiles con rango promedio para empates; robusta con percentiles 5/95 y recorte 0–100; Min-Max tras signed-log1p, que conserva tendencias negativas. Una dimensión constante aporta cero discriminación; no es imputación. Cada calibración usa la misma población fija y sus valores publicables, no el subconjunto filtrado. Se reportan correlaciones Spearman y estabilidad del Top 10 sobre casos completos, con tamaño de muestra y valores no calculables para dimensiones constantes. La sensibilidad combina cuatro métodos con escenarios de pesos base, frecuencia, mortalidad y vulnerabilidad.

Las celdas H3 adyacentes no son automáticamente concentraciones distintas. El ranking permite selección representativa que separa centros a menos de 2.6 km mediante Haversine por orden de puntuación. Es una regla transparente de separación visual, no una deduplicación causal de intersecciones o tramos. Fichas muestran centroides de celdas, nunca posiciones individuales; las calles no se inventan.

## Radar condicionado por cobertura

Ventanas de 30, 90, 180 y 365 días al corte real del archivo, comparadas con fechas del año previo. No se utiliza el día del sistema como si hubiese registros actuales. Ajuste estacional básico por calendario equivalente, exposición por días. La comparabilidad es sólo proxy: cada municipio involucrado necesita al menos 95% de pares geográficos disponibles en ambas ventanas y diferencia de cobertura no mayor a 2.5 puntos porcentuales. Sin evidencia de exhaustividad no se hacen correcciones ficticias por subregistro.

Contraste binomial exacto condicionado al total, bajo hipótesis de dos conteos Poisson independientes y misma intensidad diaria. Baseline mínimo diez y total mínimo veinte, con conteos publicables. Intervalo exacto de la razón de intensidades condicionado al mismo modelo. Corrección BH de los contrastes elegibles de todas las zonas y cuatro ventanas antes de los filtros de la interfaz. Las ventanas solapadas, sobredispersión y cambios de captura pueden invalidar supuestos; q no es una garantía de vigilancia validada ni una estimación causal. Sin comparabilidad: información insuficiente, no estable.

Se distingue incremento porcentual de alerta: sólo q<0.05 y razón>1 produce alerta condicional exploratoria. «Emergente» requiere además razón>=2; no prueba una zona nueva. Sin cambio detectado no demuestra equivalencia. El informe debe mostrar fecha de corte, ventana, baseline, conteos, q, intervalo y rezago.

## Epidemiología

Unidad fuente: registro de siniestro; desenlaces: personas contabilizadas en ese registro. Personas fallecidas/lesionadas no son siniestros fatales o con víctimas: estos últimos cuentan registros con desenlace positivo. No sumar fuentes sanitarias/policiales para evitar duplicación de víctimas. Las banderas de conductores no se usan para reconstruir desenlaces por sus contradicciones de codificación.

Se publican agregados anuales municipales, cero explícito o conteos protegidos >=5; supresión complementaria por año y variable. Los cocientes y sus intervalos se anulan cuando su numerador está oculto. Fallecidos o lesionados por cien registros son razones descriptivas, no letalidad entre personas involucradas ni riesgo individual.

INEGI declara población Censo 2020: sólo se calcula una tasa con denominador poblacional para registros de 2020, manteniendo la advertencia de cobertura administrativa incompleta. No se extrapola a 2024–2026. Intervalos Poisson al 95% condicionados al conteo y denominador; no incluyen error de cobertura, subregistro o agrupación de personas por evento. No son mortalidad vial completa ni seguimiento a treinta días. Sexo, edad, escolares, adultos mayores, AVPP y letalidad permanecen no calculables sin variables/denominadores exhaustivos y semánticamente válidos.

## Métodos espaciales y proximidad

La referencia RATIV contiene pares plausibles sin datum. Distancias Haversine y proyección UTM 14N (EPSG:32614) son exploratorias bajo supuesto de grados geográficos WGS84, no una validación del CRS original. Los límites oficiales INEGI se publican con metadatos y simplificación a cien metros para cartografía; no son delimitación legal.

H3, DBSCAN (150 m, mínimo cinco), HDBSCAN (mínimo veinte) y KDE (bandwidth 200 m) describen concentraciones bajo parámetros distintos. No equiparar densidad con riesgo sin exposición. Moran I/Gi* no se calculan sobre una población truncada por frecuencias sin malla completa y pesos preespecificados: producirían inferencia sesgada.

La proximidad pública opera con celdas agregadas, no microdatos. Reporta cotas de registros de las celdas visibles: inferior=total de celdas completamente contenidas, superior=total de celdas posiblemente intersectadas, usando circunferencias que cubren la geometría. Se excluyen celdas suprimidas y registros sin coordenadas; el intervalo no acota el total real de siniestros del entorno. A radios menores que la celda no se muestra un conteo exacto. La proximidad a una institución no prueba causalidad.

## Fuentes técnicas primarias

- SciPy binomtest: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binomtest.html
- Scikit-learn HDBSCAN/DBSCAN/KDE: https://scikit-learn.org/stable/modules/clustering.html
- INEGI Catálogo Único: https://www.inegi.org.mx/servicios/catalogounico/
- Términos de libre uso INEGI: https://www.inegi.org.mx/inegi/terminos.html
- OpenStreetMap/ODbL: https://www.openstreetmap.org/copyright

Los análisis, transformaciones y recomendaciones experimentales corresponden a OSV-NL/Doctor Data, no a las fuentes ni a un organismo oficial.

La auditoría con la geometría INEGI original encontró 152,931 de 152,937 pares dentro del estado y 151,974 dentro del municipio reportado, bajo el supuesto de CRS. Son comprobaciones de coherencia, no validación del datum. Los filtros municipales de fichas/IPIV seleccionan celdas que contienen registros de esos municipios; el conteo de la celda completa no se recalcula ni se interpreta como total administrativo municipal.

La supresión complementaria se evalúa por familias municipales superpuestas. Además, un margen anual municipal que toque una variable espacial oculta no se publica para esa dimensión y año, evitando reconstrucciones directas al cruzar municipios/celdas. Los valores retrospectivos 2024 sólo se calculan si baseline 2023 y geocobertura son comparables; se aplica la calibración 2025, no un rango nuevo. No es validación retrospectiva de un predictor. La supresión no garantiza anonimización frente a todas las fuentes externas.
