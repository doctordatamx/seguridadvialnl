# OSV-NL | Observatorio de Seguridad Vial de Nuevo León

**Inteligencia territorial para proteger la vida.**

Iniciativa ciudadana independiente. No es una entidad gubernamental ni una plataforma oficial de OCISEVI. Código MIT; las fuentes conservan sus propias licencias.

## Edición pública de GitHub Pages

Repositorio: https://github.com/doctordatamx/seguridadvialnl

Sitio publicado: https://doctordatamx.github.io/seguridadvialnl/

Esta edición presenta estadística derivada de RATIV/OCISEVI con atribución y límites visibles. Incluye IPIV experimental, rankings, fichas compartibles e imprimibles, radar condicionado por cobertura, atlas INEGI/OSM con proximidad agregada, calendario y epidemiología anual protegida. Los originales, microdatos, calles libres y resultados locales detallados no se incluyen. Los conteos sensibles pequeños y sus derivados se protegen antes de calcular índices. MIT cubre código; véase DATA_LICENSES.md.

Los archivos públicos revisados están en `release/`, con hashes y alcance en `release/manifest.json`. El mapa público usa H3 resolución 7 y mínimo veinte registros por celda. La presencia de registros en un periodo no garantiza exhaustividad. El corte de 2026 es junio; no debe compararse sin ajustes con años completos.

El workflow Pages verifica hashes y exclusiones, copia únicamente `release` y compila con base `/seguridadvialnl/`. No descarga ni publica originales. Reproducción: [PUBLICATION.md](docs/PUBLICATION.md). Cálculos: [INTELLIGENCE_METHODS.md](docs/INTELLIGENCE_METHODS.md). Entregas y pendientes: [PROJECT_STATUS.md](PROJECT_STATUS.md). El IPIV no mide riesgo absoluto; el radar no es vigilancia en tiempo real. Datum fuente no declarado: métodos espaciales exploratorios.

## Ver la edición pública localmente

```powershell
python scripts/check_public.py
node scripts/stage_public.mjs
cd web
npm ci
npm run dev
```

Para compilar como GitHub Pages: `npm run build -- --mode pages` desde web. El archivo de despliegue es `.github/workflows/pages.yml`. Pages debe configurarse con origen GitHub Actions.

## Desarrollo con datos locales

El código también admite una edición local de mayor detalle. Esa edición no es la publicada. Los datos originales deben obtenerse de la fuente y permanecer en data/raw; su redistribución no queda autorizada por publicar este repositorio. Los siguientes pasos describen ese entorno de investigación.

## Ejecutar en Windows

Desde `observatorio-vial-nl` con Python 3.14 y Node 24:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
.\.venv\Scripts\python.exe -m pipelines.run
Set-Location web
npm ci
npm run dev
```

Abrir la URL local que imprime Vite (habitualmente http://127.0.0.1:5173). Para actualizar datos y compilar con un solo comando, desde la raíz:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/update.ps1
```

No requiere servidor de base de datos. DuckDB, Parquet e informes permanecen locales; el navegador recibe únicamente agregados autorizados. Linux: sustituir `.venv\Scripts\python.exe` por `.venv/bin/python`.

## Incorporar datos reales

1. Conservar descargas originales en `data/raw`, incluso subdirectorios. No se modifican.
2. Ejecutar `python -m pipelines.run` con el Python del entorno y revisar `reports/audit`.
3. Leer `docs/INGESTION.md` y configurar las equivalencias comprobadas en `config/sources.json`.
4. Verificar unidad de observación, periodos, coordenadas, cobertura, licencia y privacidad. Habilitar los dos campos de aprobación sólo tras esa revisión.
5. Ejecutar el pipeline de nuevo y revisar `data/interim/manifest.json`, auditoría y resultados locales antes de publicar.

También se puede auditar un directorio externo con `python -m pipelines.run --input RUTA`. No usar el propio repositorio como entrada: contiene archivos de configuración y dependencias. Para archivos ya existentes fuera de `data/raw`, seleccionar únicamente la carpeta de las fuentes.

## Pruebas y compilación

```powershell
.\.venv\Scripts\python.exe -m pytest -q
Set-Location web
npm run build
npm run preview
```

Los fixtures de las pruebas son sintéticos, aislados en carpetas temporales y no se publican. Para verificar los artefactos reales actuales: `python scripts/verify_outputs.py` con el Python del entorno. Versiones de Python fijadas en requirements.lock.txt y dependencias web en package-lock.json.

## Cloudflare Pages (publicación actualmente bloqueada)

El resultado es estático: `web/dist`. Para una publicación futura autorizada:

1. Resolver licencia y privacidad, autorizar explícitamente una edición pública y ejecutar `python scripts/check_release.py`. Actualmente debe fallar. Después ejecutar el pipeline con la configuración de edición pública revisada y `npm run build` en web.
2. Revisar exclusivamente `web/dist/data/observatory.json`, sus licencias, cobertura y supresiones. Nunca subir `data/raw`, DuckDB, resultados locales de H3 o auditorías con nombres de columnas sensibles.
3. En Cloudflare Pages usar **Direct Upload** y cargar el contenido de `web/dist`. No necesita funciones, secretos ni base de datos.
4. Alternativa Git: raíz `web`, comando `npm ci && npm run build`, salida `dist`, Node 24. **La salida pública está ignorada por Git por seguridad**: hace falta un mecanismo explícito revisado para incorporar los agregados al build. Sin ello el sitio no tendrá datos. No conectar despliegues automáticos hasta resolverlo.

El flujo CI verifica el proyecto con entrada vacía. El flujo mensual sólo recuerda la revisión: no simula una descarga ni cambia la fecha de corte de datos. Cloudflare puede cambiar condiciones o límites: comprobarlos antes de contratar/publicar.

## Informes

Plantilla Quarto en `reports/annual/observatorio.qmd`. Requiere instalar Quarto, Jupyter e ipykernel en un entorno de informes; para PDF también TeX. Con el entorno activado: `quarto render reports/annual/observatorio.qmd --to html` o `--to pdf`. La generación Quarto/PDF no fue ejecutada en esta sesión. El pipeline genera un informe HTML local disponible en web/public/data/report.html y enlazado desde Informes, sin requerir Quarto.

## Estructura y documentación

- `pipelines/`: lectores, perfilado, adaptadores, normalización, agregación y H3/DBSCAN.
- `data/`: originales, intermedios, analíticos y futuros insumos externos.
- `database/`: DuckDB local regenerable.
- `web/`: React, TypeScript, Vite, Tailwind, ECharts y MapLibre con carga diferida.
- `tests/`: comprobaciones de calidad, privacidad e idempotencia analítica.
- `METHODOLOGY.md`: definiciones y límites.
- `docs/DATA_MODEL.md`: contratos y extensiones.
- `ROADMAP.md` y `PROJECT_STATUS.md`: alcance implementado y siguiente trabajo.

No se incluyeron enlaces ficticios a un repositorio público. Antes de publicar: crear repositorio propio, revisar licencias de todas las fuentes y añadir su URL en la sección Metodología.
