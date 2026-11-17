# Edición pública de OSV-NL

Autorización del propietario: solicitud explícita de publicar en doctordatamx/seguridadvialnl, 17 de noviembre de 2026.

## Alcance

Sólo código y estadística derivada agregada. No se redistribuyen las bases originales ni se publica la edición local completa. Atribución OCISEVI/RATIV, fuentes, método, corte y limitaciones visibles. La MIT cubre código, no datos de terceros.

- Frecuencias mensuales por municipio; celdas de menos de cinco registros suprimidas.
- Conteos de lesionadas/fallecidas excluidos de la edición pública, incluso cuando están disponibles localmente.
- Perfiles anuales con celdas mensuales pequeñas excluidos para evitar recuperación desde esos márgenes.
- Calles libres, folios repetidos, narraciones, contactos, pólizas, placas y microdatos no publicados.
- Presencia de peatón lesionado/fallecido excluida de los desgloses públicos de usuarios vulnerables.
- H3 resolución 7, mínimo veinte registros; nunca coordenadas de eventos individuales ni víctimas por celda. La geografía es provisional: datum y pertenencia municipal sin comprobar.

Las pautas de uso del portal piden atribución y conservación de integridad. No se infiere una licencia propia sobre los archivos de terceros. Este repositorio presenta cálculos derivados y enlaza la fuente original.

## Construcción

1. python scripts/check_public.py
2. node scripts/stage_public.mjs
3. npm ci en web
4. npm run build -- --mode pages en web

GitHub Actions usa exclusivamente release/, verifica hashes y publica web/dist. Los originales se excluyen mediante .gitignore y el paquete se revisa antes del commit. Las descargas y los pipelines locales no forman parte del workflow de despliegue.

No cambiar mode ni release_approved en archivos de datos locales para subirlos directamente. Para una nueva edición pública utilizar prepare_public.py, revisar los agregados, verificar exclusiones y hashes, probar el build y publicar el diff resultante.
