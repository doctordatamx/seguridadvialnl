# Metodología v0.2

Fecha: 17 de noviembre de 2026. Bases RATIV 2019–2026 integradas en modo local. El contrato específico activo y sus excepciones están en docs/RATIV_ADAPTER.md. Los apartados genéricos siguientes se aplican únicamente donde no contradicen ese contrato.

## Auditoría previa a indicadores

Inventario recursivo de originales, hash SHA-256, número de filas/variables, tipos observados, nulos, vacíos, cardinalidad, duplicados exactos, CRS y cambios frente al esquema de la ejecución anterior. No se exportan ejemplos de valores personales en la auditoría. Periodos, cobertura, desenlaces, vehículos y usuarios requieren mapeo de columnas comprobado. Una auditoría sin entradas no valida la calidad de una fuente futura.

## Indicadores implementados

- Registros RATIV: conteo de filas aceptadas y trazables, sujeto a supresión; folios repetidos y duplicados exactos se conservan hasta conciliación. En adaptadores genéricos con ID único validado se admite contar eventos únicos.
- Personas lesionadas/fallecidas: suma de conteos válidos únicamente si no hay valores faltantes en el grupo y el resultado no está suprimido.
- Municipios con registros: número de municipios observados en las celdas públicas. No es una medición de exhaustividad estatal.
- Serie mensual y ranking municipal: agregación de las celdas publicables. Grupos con sumas incompletas no participan del ranking.

No se calculan fatalidad por evento, promedio diario, variación interanual, hora máxima ni tasas sin revisar disponibilidad, exhaustividad y periodos equivalentes. Fórmulas futuras: tasa = eventos / población correspondiente × 100,000; variación = (periodo actual / periodo anterior − 1) × 100, sólo con denominador >0 y coberturas comparables. Letalidad y AVPP requieren denominadores y edades verificables. Fallecimientos de fuente policial no se interpretan como defunciones a 30 días.

## Geografía

Filtro tabular aproximado de extensión 23–28.5° N, −102 a −98° O y declaración EPSG:4326; no reemplaza validación con límite estatal oficial. H3 usa resoluciones 7, 8 y 9, registra número de celdas y diez de mayor frecuencia por resolución. DBSCAN aplica Haversine con radio terrestre 6,371,008.8 m, epsilon 150 m y mínimo 5 puntos. Ruido −1 no entra al ranking. No son resultados públicos hasta revisar ubicación, precisión, duplicados y cobertura. La sensibilidad reporta cambios en concentración; no constituye validación de un punto crítico causal.

## Privacidad

Agregación por municipio y mes. Suprimir grupos con <5 eventos y conteos de desenlaces entre 1 y 4. Mantener nulos y ceros distintos. No publicar microdatos ni sumas que permitan reconstrucción directa. Esta regla no es una garantía universal de anonimización: revisar enlaces externos, universos pequeños y futuras dimensiones antes de ampliar filtros. Exportaciones CSV sólo incluyen las mismas celdas agregadas visibles.

## Reproducibilidad y límites

Los originales permanecen intactos; las tablas derivadas se regeneran. Se bloquea publicación por defecto. Sólo se permite combinar tablas anuales cuando se verifican particiones distintas y fechas correspondientes. La vista local incluye perfiles y capas adicionales que requieren revisión conjunta contra reconstrucción antes de cualquier edición pública. No hay ponderación por subregistro, imputación ni extrapolación estatal. No se declaran causalidad, riesgo absoluto ni predicciones. Licencia y procedencia requieren revisión manual. Los modelos experimentales deben mantener particiones temporales y espaciales y separarse de resultados descriptivos en etapas futuras.
