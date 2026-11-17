# Revisión previa a la ampliación de inteligencia territorial

Fecha: 17 de noviembre de 2026. Base: commit 2d7be4a, piloto publicado, sin cambios previos pendientes.

## Arquitectura conservada

Python/Polars transforma originales locales inmutables en Parquet/DuckDB. React/TypeScript/Vite, ECharts y MapLibre consumen archivos agregados. GitHub Pages compila exclusivamente release/ después de verificar hashes. Se conservan mapa, explorador, filtros, métodos de supresión, CI y despliegue estático.

## Auditoría de cálculos y deuda

- ENCUESTA no es único en todos los años: mantener el término registros reportados, IDs técnicos y diagnósticos de duplicación.
- Los filtros no deben recalibrar un índice. Se fija población de referencia antes de filtrar o cambiar pesos.
- La condición estricta de suma incompleta y la distinción cero/nulo son correctas; extenderlas a indicadores derivados e intervalos.
- El histograma horario corresponde al reporte, no a la hora exacta del evento. Una matriz 7×24 debe explicitar esa limitación.
- Los puntos RATIV no declaran datum; el filtro rectangular no valida municipio. H3 y clústeres siguen siendo exploratorios. No presentar celdas contiguas como puntos críticos independientes sin explicar la selección espacial.
- La edición publicada anterior retira todos los conteos clínicos. La nueva solicitud requiere epidemiología: preparar sólo resultados agregados anuales y de celdas amplias con supresión y sin microdatos, revisando índices y cocientes para no recuperar valores ocultos.
- Hay código de rutas y estado concentrado en main.tsx, un tipo que no admitía nulos reales y mensajes genéricos de falta de datos. Añadir módulos y contratos separados, no reconstruir el proyecto.
- El radar no puede usar la fecha del sistema como si hubiese datos recientes. El corte real es junio de 2026 y la geocobertura cae mucho ese año.
- Moran/Gi* necesitan una población espacial y pesos apropiados; aplicarlos a un ranking truncado produciría inferencia sesgada. Publicar su estado y justificación si no se cumplen las condiciones.

## Secuencia de implementación

1. Contratos y pruebas de IPIV, normalización fija, supresión de derivados y vigilancia con control de comparabilidad/FDR.
2. Dataset agregado de celdas persistentes, fichas, sensibilidad, calendario, matriz temporal y epidemiología anual. Mantener resultados detallados privados.
3. Atlas con límites oficiales, capas verificadas y proximidad que muestre incertidumbre de la agregación.
4. UI incremental: rankings, ficha por URL, simulador, radar, comparación, descarga e impresión.
5. Pruebas científicas/de integración, revisión de navegador y compilación bajo /seguridadvialnl/; actualizar el sitio sólo con agregados revisados.

## Insumos nuevos verificados

INEGI, Catálogo Único v2: 51 municipios, geometrías del Marco Geoestadístico diciembre de 2025 y población del Censo 2020, declarados en metadatos del servicio. La población 2020 no se extrapolará a otros años. No hay denominadores válidos para calcular tasas poblacionales de 2025/2026 sin una integración adicional.

## Alcance recibido

El texto adjunto termina en la sección 9, después de «Calendario anual». Se implementa el contenido efectivamente recibido sin inventar requisitos posteriores.
