# Edición pública de OSV-NL

El propietario solicitó publicar y continuar la plataforma en doctordatamx/seguridadvialnl. Publicación estática en GitHub Pages.

Sólo código, cartografía contextual con atribución y estadística derivada agregada. No se redistribuyen originales RATIV, microdatos, folios, calles libres, narraciones, contactos, pólizas, placas ni resultados individuales. MIT cubre código; fuentes bajo sus propias condiciones (DATA_LICENSES.md).

Frecuencias mensuales con umbral cinco y protección complementaria. H3 resolución siete con umbral veinte. Desenlaces anuales municipales y de celdas de referencia protegen positivos entre uno y cuatro antes de normalizar o derivar índices/ratios. Se retiran márgenes municipales de variables espaciales ocultas. La protección no demuestra anonimización frente a todo dato externo. Nulo y supresión nunca se convierten en cero.

release/manifest.json enumera once recursos y hashes. check_public.py comprueba esquema, umbrales, derivados, exclusiones y atribución. stage_public.mjs copia sólo esa lista a web/public/data. GitHub Actions no descarga originales ni ejecuta el análisis real; verifica la edición y compila con base /seguridadvialnl/.

## Reproducir localmente

Python 3.14 con requirements.lock.txt; Node 24 y npm ci en web. Desde la raíz:

    powershell -ExecutionPolicy Bypass -File scripts/update_intelligence.ps1 -Records C:\ruta\privada\crashes.parquet
    python -m pytest -q
    node --test tests/frontend.test.mjs

El Parquet debe cumplir el contrato RATIV y permanecer privado. El script conserva caché, rechaza respuestas incompletas, genera agregados, actualiza hashes, verifica y compila. Revisar el diff y protecciones antes de publicar. El piloto mensual se prepara separadamente con prepare_public.py; después hay que regenerar el manifiesto completo.

## Verificar edición preparada

    python scripts/check_public.py
    node scripts/stage_public.mjs
    cd web
    npm ci
    npm run build -- --mode pages

No cambiar banderas de autorización de datos locales para subirlos directamente. Métodos y restricciones: INTELLIGENCE_METHODS.md. Métodos sin condiciones suficientes permanecen no calculables.
