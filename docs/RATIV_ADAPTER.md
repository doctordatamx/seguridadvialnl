# Adaptador RATIV v1 — decisiones verificables

## Fuentes y unidad

Ocho archivos originales OCISEVI CSV.gz, 2019–2026, descargados el 17/11/2026 mediante open_metadata.json. Catálogo y diccionario PDF conservados en data/external/ocisevi. SHA-256, URL y recuentos por archivo en el manifiesto de descarga. Los documentos se leyeron íntegramente con pypdf; no se modificaron.

El diccionario identifica ENCUESTA como folio de siniestro y dispone vehículos/conductores en columnas repetidas dentro de una fila. La unidad de trabajo es por tanto **registro de siniestro reportado**, no persona ni vehículo. No se garantiza la unicidad del evento: el folio contradice esa descripción en los archivos antiguos.

## Identificadores y duplicación

ENCUESTA no es único en 2019–2022, incluso después de combinarlo con municipio, mes y día hay colisiones. Hay un folio repetido en 2023; es único dentro del archivo en 2024–2026. El código 99 puede representar sin dato. Una eliminación automática por ENCUESTA descartaría una gran parte de las filas y sería metodológicamente incorrecta.

Se asigna record_id = archivo + posición de fila, únicamente para trazabilidad local. No es un identificador inventado de un evento real. El folio original queda separado como event_id y folio_status. No se exportan folios al navegador. Se conservan las 200 filas exactas repetidas de 2019, que podrían ser duplicados o eventos indistinguibles tras la disociación de información. Deben conciliarse con la fuente. Los demás archivos no tienen duplicados exactos según el perfilado.

Las particiones anuales se unen después de comprobar que cada fecha pertenece al año de su archivo y que los años de las fuentes son distintos. Esta prueba resuelve el solapamiento temporal entre archivos; no resuelve duplicados dentro de un archivo.

## Fechas, hora y códigos

Fecha = date(Año, Mes, Día), con validación estricta. El día de la semana se deriva de la fecha, lunes=0. El catálogo usa domingo=1, mientras el diccionario describe lunes=1; además existen discrepancias entre valores y fechas. No se usa el código original como verdad.

Hora de reporte es la hora de notificación, no hora exacta de ocurrencia. Se admiten HH:MM[:SS] y fracciones decimales explícitas del día de Excel entre cero y uno. Se redondea a segundos antes de obtener la hora; un valor próximo al final del día se limita a 23:59:59. Fechas/seriales ambiguos, horas fuera de rango y formatos irrecuperables permanecen nulos. No se usan fechas ficticias del año 1900 para inferir horarios.

99, SD, NA y equivalentes se interpretan como sin dato cuando corresponden al contrato RATIV. Para conteos se aceptan enteros 0–98: cero es un conteo válido; 99 es sin dato. No se suman banderas Lesionado/Fallecido de conductores: el diccionario contiene descripciones contradictorias 0/1 y 1/2, y la estructura cambia en 2024. Se usan exclusivamente Total de lesionados y Total de fallecidos por registro.

## Territorio y campos repetidos

MUNICIPIO se traduce con el catálogo de once municipios de la fuente; las formas abreviadas se presentan con nombres completos. No se asume que los otros municipios de Nuevo León carezcan de siniestros. Las fechas extremas y la presencia de doce meses no prueban exhaustividad.

Vehículo 1 se presenta como la posición del parte, no como todos los vehículos ni responsabilidad demostrada. Para presencia de bicicleta/motocicleta se consideran las posiciones disponibles 1–3. La ausencia de una posición o código no demuestra ausencia de esa clase de usuario. La categoría peatonal sólo señala lesión o fallecimiento peatonal documentado; no todos los peatones involucrados. Categorías superpuestas, no sumables ni equiparables a conteos de personas.

CALLE de 2019 y Calle de los demás años se normalizan con Unicode NFKC, mayúsculas y espacios. No se fusionan abreviaturas o nombres por aproximación. Se excluyen textos excesivos y patrones de contacto; esto no constituye una revisión humana completa de texto libre. El ranking cuenta registros de calles por municipio y año con mínimo veinte; no identifica intersecciones o segmentos homogéneos.

## Geografía experimental

Referencia se admite sólo como par numérico estricto latitud,longitud o latitud;longitud, dentro de 23–28.5° N y −102 a −98° O. Se rechazan texto libre, pares invertidos y valores fuera de esa extensión. No se geocodifica ni se transforma una referencia textual.

El diccionario indica latitud-longitud, pero no especifica datum, precisión ni método de localización. Por ello el archivo canónico conserva el estado plausible_coordinates_datum_unknown; no se afirma que sea un GeoParquet WGS84 validado. H3 y MapLibre interpretan provisionalmente estos grados geográficos para exploración, con advertencia visible. No hay validación contra límites estatales/municipales oficiales. La disponibilidad espacial es nula con el parser estricto en 2019–2021, reducida en 2022–2023, alta en 2024–2025 y parcial de nuevo en 2026. No comparar concentraciones entre años como si la captura fuera homogénea.

H3: resoluciones 7, 8 y 9 para sensibilidad local; visor de resolución 8 con umbral diez registros por celda. El conjunto municipal agregado se recalcula desde filas, no sumando sólo celdas municipales visibles. El mapa de calor usa centroides H3 ponderados, no puntos individuales. No se publica mortalidad por hexágono.

DBSCAN: Haversine, epsilon 150 m, mínimo cinco registros, radio terrestre 6,371,008.8 m. Se calcula por municipio y año, comprimiendo posiciones idénticas con sample_weight; esto conserva su peso para el umbral de densidad. Resultados exclusivamente locales. El cálculo global se difiere si excede 50,000 puntos; cada grupo también tiene límite de 50,000 posiciones únicas. No se denominan a esos grupos puntos críticos validados ni riesgo.

## Privacidad, modo local y publicación

El adaptador utiliza lista blanca de campos. Excluye teléfonos, placas, pólizas, licencia, edades, sexo y narraciones. El archivo analítico no replica columnas arbitrarias de los originales. En navegador sólo hay agregados mensuales, perfiles municipio/año, calles frecuentes y polígonos H3; nunca microdatos, folios o posiciones individuales.

Celdas mensuales con <5 registros y conteos de personas de 1 a 4 se suprimen. La salida distingue missing de suppressed. Desgloses categóricos suprimen una segunda categoría cuando sólo hay una celda pequeña. **La combinación de desgloses, totales, periodos y mapas requiere una revisión conjunta contra reconstrucción antes de publicar. Esta versión local no garantiza anonimización de una edición pública.**

config/sources.json mantiene redistribution_approved=false para todas las bases. local_preview_approved habilita sólo el procesamiento solicitado en esta máquina. El JSON indica mode=local_preview y release_approved=false. `python scripts/check_release.py` debe fallar en este estado; no subir web/dist. La atribución y conservación de integridad indicadas por el portal se documentan sin convertirlas en una licencia jurídica inferida.

## Reproducibilidad

`python -m pipelines.run` regenera auditoría, comparación entre esquemas, matriz municipal, Parquet, DuckDB, agregados, H3, DBSCAN e informe HTML. Se archivan manifiestos locales por ejecución. Las salidas analíticas son deterministas para las mismas entradas/configuración, salvo tiempos de ejecución y metadatos del informe.
