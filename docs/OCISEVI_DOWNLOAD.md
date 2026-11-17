# Descarga OCISEVI — 17 de noviembre de 2026

Fuente: https://ocisevi.org.mx/ocisevi-nl/open_metadata.json

Las ocho bases originales CSV.gz se descargaron sin modificar. Se leyeron completas para verificar gzip/CRC y se registró SHA-256. Los conteos siguientes son filas del archivo, todavía no siniestros únicos validados.

| Año | Filas CSV | Columnas | Bytes comprimidos |
|---|---:|---:|---:|
| 2019 | 70,624 | 92 | 1,892,723 |
| 2020 | 58,403 | 92 | 1,934,465 |
| 2021 | 63,300 | 122 | 2,495,291 |
| 2022 | 69,860 | 123 | 3,322,534 |
| 2023 | 73,107 | 121 | 3,442,834 |
| 2024 | 67,956 | 128 | 3,827,723 |
| 2025 | 63,016 | 187 | 3,801,368 |
| 2026 | 28,380 | 127 | 1,380,354 |

Total: 494,646 filas. No se asume año 2026 completo.

Documentos de referencia descargados en data/external/ocisevi: Catalogo-Codigos.pdf y Diccionario_de_datos_RATIV.pdf.

El portal se sirve como aplicación React. La petición HTTP directa a /datos-abiertos dio 404; la portada /ocisevi-nl permitió localizar su JavaScript, que enlaza open_metadata.json y los archivos descargados. La aplicación muestra pautas de citar fuente y conservar integridad; no se ha aprobado la redistribución del contenido.

Diferencias de esquema observadas: entre 92 y 187 columnas según año. Se requiere análisis semántico antes de unificar. No se han habilitado fuentes, indicadores ni publicación web.
