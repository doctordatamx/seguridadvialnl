# Estado del proyecto

## Publicación en GitHub Pages — 2026-11-17

Solicitud explícita: publicar en doctordatamx/seguridadvialnl. Repositorio existente vacío, cuenta autenticada comprobada y permiso administrativo disponible. Se preparó una edición pública independiente en release/ y un workflow GitHub Pages. Excluye originales, microdatos, conteos de víctimas, calles libres y resultados locales de investigación. H3 público: resolución 7, mínimo veinte registros. Se omiten dos perfiles anuales que permitirían recuperar celdas mensuales pequeñas; quedan 86 perfiles y 986 celdas mensuales. Las secciones siguientes documentan la edición de investigación local y no describen el alcance público.

Estado de despliegue: **publicado y verificado** en https://doctordatamx.github.io/seguridadvialnl/. El workflow de publicación 44129170121 y CI 44129169946 finalizaron correctamente sobre el commit 0e66a9b5d373b1784c6e62d24e6313d1d0365ddf. Verificación de navegador: datos cargados, edición pública identificada, mapa H3 resolución 7 visible con umbral veinte y sin errores de consola. El sitio ya no depende del servidor local.

Actualizado: 17 de noviembre de 2026. Versión 0.2.0. **Vista local con datos reales; no desplegada públicamente.**

## Resultado actual

Se descargaron y preservaron ocho originales OCISEVI (2019–2026), más catálogo de códigos y diccionario RATIV. El pipeline integra **494,646 registros**, sin deduplicar por folios que no son únicos. Hay **11 municipios observados**, **88 perfiles municipio/año** y **986 celdas mensuales**. El corte de eventos es **30 de junio de 2026**; el año 2026 es parcial. En 2025 hay registros en los doce meses, lo cual no demuestra exhaustividad.

No se afirma cobertura estatal completa ni que los registros equivalgan a siniestros únicos. Se conservaron 200 filas exactas repetidas de 2019 hasta conciliación. Los originales contienen campos de contacto y texto libre: se excluyeron de la base canónica y de las salidas web.

## Implementado y verificado

- Descarga reproducible, lectura gzip completa y SHA-256; hashes originales comprobados tras el procesamiento.
- Auditoría multiformato, diccionario con nulos/vacíos/códigos semánticos, comparación entre esquemas, matriz municipio/año/variable y diagnóstico de adaptación por archivo.
- Adaptador RATIV explícito con lista blanca, fecha estricta, día de semana derivado, recuperación de fracciones horarias Excel, conteos y códigos sin dato, trazabilidad por archivo/fila.
- Base analítica Parquet y DuckDB, manifiestos archivados por ejecución.
- Panorama con frecuencias, serie mensual, cobertura y supresión visible. Se inicia en 2025. Nulo, cero, supresión y ausencia de registros se explican por separado.
- Analítica temporal: meses, día del siniestro, hora de reporte, tipo de siniestro y vehículo 1, con tablas accesibles y exportación de imagen.
- Comparador: selección municipal, frecuencias y tabla de disponibilidad temporal/horaria/geográfica y folios repetidos. Sin tasas sin denominadores ni comparaciones de riesgo.
- Ranking Top 10 de calles por municipio/año, mínimo veinte registros; no se presenta como intersección o punto crítico validado.
- Usuarios vulnerables: presencia documentada de motocicleta, bicicleta y peatón lesionado/fallecido; categorías superpuestas, no conteo de personas ni causalidad.
- Salud pública: completitud de desenlaces; sin tasas, letalidad o AVPP inferidos.
- Mapa MapLibre: H3 resolución 8, capa de calor desde centroides, opacidad, filtro anual/municipal, leyenda, popup y tabla Top 10. Coordenadas plausibles con datum no declarado, sin cartografía base o límites oficiales. Sin puntos individuales. La vista conjunta se calcula desde registros antes de aplicar umbral diez.
- **4,471 polígonos H3** entre vistas municipales y conjuntas, años y celdas distintos; no son ubicaciones individuales ni un conteo de siniestros únicos.
- H3 sensibilidad en resoluciones 7/8/9 y DBSCAN local por municipio/año con ponderación de posiciones repetidas: **44 grupos procesados**. No son puntos críticos validados. El cálculo global grande se difiere por memoria.
- Explorador: filtros por año/municipio, búsqueda, ordenamiento, paginación y CSV con estado de supresión, protección contra fórmulas y sin microdatos.
- Informe HTML reproducible de cobertura/calidad, generado por Python y enlazado desde Informes. Plantilla Quarto disponible; renderizado Quarto/PDF no ejecutado.
- Modo local explícito, redistribution_approved=false en todas las fuentes y barrera scripts/check_release.py. No se publicó en GitHub/Cloudflare.

## Pruebas y QA

- Suite: **16 pruebas aprobadas** (última ejecución: 10.46 s) tras integrar RATIV y DBSCAN (incluye nulos/cero, CSV.gz, fechas, folios, privacidad, particiones anuales y ponderación espacial).
- Integración sobre datos reales: scripts/verify_outputs.py **aprobado**. Concilia filas, IDs técnicos, hashes, lista blanca, celdas mensuales, supresión, umbrales H3 y balance de registros DBSCAN. Evidencia en reports/audit/VERIFICATION.json.
- TypeScript y Vite: compilación aprobada con módulos diferidos y worker de MapLibre empaquetado explícitamente. Se corrigió el fallo de worker descubierto en navegador.
- Instalación web: cero vulnerabilidades conocidas tras actualizar MapLibre a 6.19.0. No es una certificación de seguridad.
- HTTP local e informe HTML: respuesta **200**. El servidor de prueba se detuvo al terminar; iniciar con npm run dev -- --port 5187 desde web. Revisión en navegador realizada: panorama real, filtro municipal del mapa, capa H3 visible, cambio a calor, tablas, búsqueda y descarga CSV. Se verificó el CSV descargado con una sola fila tras filtrar Monterrey/2025-02.
- Revisión de gráficas y modo oscuro, y menú móvil a 390×844. Captura real de mapa en reports/audit/mapa-local.jpg. No se declara conformidad WCAG certificada ni cobertura completa de navegadores.
- No se ejecutó CI remota ni despliegue público. No se generó PDF final.

## Decisiones y límites

Las reglas del adaptador están en docs/RATIV_ADAPTER.md. Las instrucciones originales de deduplicar por event_id se mantienen sólo para adaptadores genéricos con contrato de ID único; no aplican a RATIV. Unión anual permitida exclusivamente con particiones verificadas y fechas correspondientes.

La licencia específica de redistribución no está confirmada: las pautas del portal de citar fuente y conservar integridad no se convierten en una autorización jurídica inferida. La aprobación de procesamiento y revisión de campos locales es distinta de la aprobación de publicación.

La combinación de totales, periodos, categorías y mapas locales necesita revisar posibles reconstrucciones de celdas pequeñas antes de publicar. La supresión simple no garantiza anonimización de una edición pública. No subir web/dist en el estado actual.

La hora es de reporte; fechas seriales ambiguas permanecen nulas. Los códigos de día de semana de catálogo/diccionario discrepan; se deriva de fecha. Coordenadas sólo pares estrictos con filtro regional aproximado: sin datum, precisión o pertenencia municipal comprobados. La geocobertura cambia drásticamente por año; no se interpreta su aumento como aumento de siniestros.

Los campos de calle son texto normalizado, no una red vial homologada. Lectura en memoria apropiada a estos archivos, con trabajo pendiente para fuentes mayores. No se compara gravedad/riesgo municipal sin denominadores y cobertura comparable. DBSCAN por municipio puede fragmentar una concentración fronteriza; resultado experimental local.

## Pendientes del MVP y siguientes etapas

1. Conciliar folios repetidos, duplicados y definiciones con la fuente; confirmar condiciones de redistribución.
2. Revisión conjunta de privacidad y texto de calles antes de cualquier edición pública.
3. Integrar límites y denominadores oficiales, validar coordenadas/CRS y revisar atribuciones de cartografía. Coropletas, búsqueda geocodificada de vías y segmentos siguen pendientes.
4. Fichas de puntos críticos validados, rankings de gravedad y comparación de periodos equivalentes con cobertura comprobada.
5. Análisis diario/semanal, matrices 7×24, vacaciones y tasas según disponibilidad y protocolo; no se han implementado todos los módulos del documento maestro.
6. Renderizar y verificar informes científicos Quarto/PDF; fichas municipales y por puntos validados.
7. Auditoría formal de accesibilidad, rendimiento móvil con diversos dispositivos y pruebas de navegador más amplias.
8. Repositorio y despliegue público únicamente tras autorización explícita. Los conectores futuros y modelos predictivos/causales siguen como arquitectura pendiente.
