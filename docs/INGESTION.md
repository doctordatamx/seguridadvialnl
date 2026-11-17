# Incorporación controlada

Para las ocho bases RATIV ya integradas, usar el contrato específico de RATIV_ADAPTER.md. El siguiente ejemplo es para adaptadores genéricos, no para RATIV. Se admiten CSV.gz/TSV.gz sin extraer ni modificar originales.

Primero auditar, después mapear. CSV/TSV: delimitador detectado y texto sin inferencia para conservar códigos. XLSX/XLS: todas las hojas. JSON: lista de objetos; GeoJSON/SHP/GPKG: todas las capas legibles y CRS registrado. Parquet: esquema nativo. ZIP: CSV/TSV en memoria, sin extracción de rutas y con límite descomprimido de 512 MB. Otros miembros de ZIP requieren descompresión manual en una carpeta de originales (el archivo original se conserva).

La auditoría no adivina equivalencias semánticas. Ejemplo **de configuración, no de esquema real de OCISEVI**:

```json
{
  "id": "archivo.csv",
  "source_url": "URL verificada de procedencia",
  "license": "Licencia exacta y referencia verificadas",
  "observation_unit": "crash",
  "date_format": "%d/%m/%Y",
  "coordinate_crs": "EPSG:4326",
  "redistribution_approved": false,
  "privacy_reviewed": false,
  "municipality_aliases": {},
  "columns": {
    "event_id": "COLUMNA_COMPROBADA_ID",
    "date": "COLUMNA_COMPROBADA_FECHA",
    "municipality": "COLUMNA_COMPROBADA_MUNICIPIO"
  }
}
```

Añadir a `sources` en config/sources.json; identificador exacto del catálogo. Excel usa `archivo.xlsx::Hoja`, ZIP `archivo.zip::ruta/interna.csv`, GPKG `archivo.gpkg::capa`. Los campos opcionales están en docs/DATA_MODEL.md. La hora debe ser un entero 0–23; formatos de tiempo completos requieren un adaptador específico. Claves desconocidas no deben configurarse por semejanza de nombre.

El mapeo municipal sólo normaliza espacios y mayúsculas; las equivalencias de códigos y nombres deben proceder de un catálogo oficial y añadirse explícitamente a municipality_aliases. Una fila por persona/vehículo no es una fila por siniestro: necesita transformación previa documentada. Geometrías no se convierten automáticamente a latitud/longitud; reproyectar y validar localmente antes de configurar.

Las filas con identificador, municipio, fecha, hora o conteo inválidos se excluyen y se contabilizan. Coordenadas inválidas se anulan sin eliminar el siniestro. Revisar los recuentos de rechazo antes de aprobar. Duplicados de identificador dentro de cada tabla: se conserva el primero, con diagnóstico; conflictos deben resolverse en el adaptador de la fuente, no confiar en la primera aparición para interpretación científica.

Si se autorizan varias tablas se bloquea la publicación agregada hasta resolver el solapamiento. Integrar después en una fuente canónica revisada, con trazabilidad de procedencia y contrato específico de deduplicación. No sumar meses/años de archivos distintos sin comprobar solapamiento.

No hay una licencia implícita por llamarse datos abiertos. Las aprobaciones son decisiones humanas registradas en la configuración; el pipeline no verifica jurídicamente una licencia ni detecta todas las posibilidades de reidentificación. Mantener el repositorio privado durante la preparación y revisar cada archivo a incluir.
