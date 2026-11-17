# Modelo de datos v0.2

El contrato RATIV activo se documenta en RATIV_ADAPTER.md. Añade record_id (archivo/fila), source_row, folio_status, weekday, municipality_code, vehículos presentes, desenlaces peatonales y coordinate_status. Su unidad es crash_record: no se impone unicidad de ENCUESTA. Los conteos reportan filas aceptadas, no eventos únicos garantizados. Los contratos genéricos descritos debajo aplican sólo a fuentes con ID único validado.

La salida web local añade mode, release_approved, profiles y estados injured_status/deaths_status, además de spatial.json con polígonos H3 e informe HTML. Los perfiles incluyen cobertura, desgloses por municipio/año y rankings de calles con umbral veinte. El despliegue de esta edición está bloqueado. Los manifiestos se archivan ahora en data/interim/manifests.

## Contratos genéricos

## Entrada

Archivos inmutables, SHA-256 por archivo y una entidad de catálogo por tabla/hoja/capa. Adaptador explícito por entidad. Sin fuente configurada se perfila pero no se incorpora a la base de siniestros.

## Tabla local crashes

| Campo | Semántica | Regla |
|---|---|---|
| event_id | ID de siniestro de la fuente | Obligatorio, único por tabla |
| source | Clave del catálogo | Generada por pipeline |
| date | Fecha del evento ISO 8601 | Obligatoria, formato de origen explícito |
| municipality | Nombre/código territorial normalizado | Obligatorio, alias explícitos |
| hour | Hora entera | 0–23 o nulo |
| injured, deaths | Personas registradas por siniestro | Entero >=0 o nulo |
| crash_type, vehicle, vulnerable_user | Categorías verificadas | Texto normalizado o nulo |
| street, intersection | Localización textual | Espacios y mayúsculas normalizados; no geocodificación |
| latitude, longitude | Posición WGS84 | Nulo si falta par, CRS o extensión aproximada válida |

No se incorpora persona identificable ni columnas arbitrarias en la tabla canónica. El esquema Arrow se infiere para tablas no vacías; para vacías se crea un esquema de texto sin valores. DuckDB se reconstruye desde Parquet. La futura tipificación estricta con Pydantic y GeoParquet necesita contratos reales de las fuentes.

## Salidas locales

Cinco archivos de auditoría en reports/audit. Matriz larga municipio × año × variable × fuente con denominador de filas y conteo no nulo. Sólo combina grupos observados, no inventa cobertura para municipios/años sin registros. Manifest de hashes, estado y conteos; H3/DBSCAN de investigación en data/processed/hotspots.json. Las salidas son deterministas salvo marcas de ejecución; los manifiestos se archivan por ejecución en data/interim/manifests.

## Contrato web v0.1

`observatory.json`: estado, hora de ejecución UTC, fecha máxima del evento, tamaño mínimo, limitaciones, fuentes y filas mensuales municipales. Cada fila contiene municipality, month, crashes, injured, deaths, suppressed. Nulos persisten hasta UI y exportación. `suppressed` marca una celda de frecuencia pequeña; un desenlace también puede estar suprimido independientemente.

No hay microdatos, coordenadas ni categorías finas en el payload. No se publica un total general recuperable de las celdas ocultas. Si alguna celda del filtro está suprimida, su total se muestra como sin información. Un mes sin registro no aparece y no se imputa.

## Extensiones previstas

Separar siniestros, vehículos y personas si las unidades de observación lo requieren. Catálogo INEGI de municipios con claves, vigencias y geometrías; denominadores población/parque/aforos con fuente y fecha; fact tables de salud sin enlace individual público. Adaptadores por fuente y versión con pruebas de contrato antes de combinar. No existe aún un conector ATUS/DGIS/CONAGUA.
