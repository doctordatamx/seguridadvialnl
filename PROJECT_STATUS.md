# Estado del proyecto

Actualizado: 17 de noviembre de 2026. Ampliación de inteligencia territorial v0.2 sobre el piloto publicado en GitHub Pages.

Sitio: https://doctordatamx.github.io/seguridadvialnl/

## Datos y alcance

Ocho originales OCISEVI/RATIV 2019–2026 preservados; 494,646 registros canónicos de once municipios observados. Corte real: 30 de junio de 2026. No es cobertura estatal completa ni un conteo conciliado de siniestros únicos. Los originales, microdatos, contactos, placas y narraciones no se publican.

Once recursos públicos con hashes. Los desenlaces anuales y de celdas amplias se protegen antes de normalizar o producir índices/cocientes. Los márgenes municipales que podrían reconstruir valores espaciales ocultos también se retiran. Nulo, cero y supresión son estados diferentes.

## Entregado

- Rankings de frecuencia, fallecidos, lesionados, gravedad, crecimiento, peatón, motocicleta y señales emergentes; comparación y CSV. Separación representativa opcional de centroides a 2.6 km: no son intersecciones validadas.
- IPIV experimental: 191 celdas H3 R7 con veinte registros o más en 2024 y 2025; 49 casos completos tras protección. Cinco dimensiones, pesos editables, cuatro normalizaciones, referencia fija, mapa y sensibilidad. Los filtros no recalibran scores. Una dimensión esencial desconocida impide calcular aunque su peso sea cero.
- Fichas con URL persistente, contexto, métricas, perfiles, historia cuando calculable, comparación, enlace compartible e impresión desde el navegador.
- Radar 30/90/180/365 días al corte del archivo, comparación estacional, control de cobertura, contraste exacto e intervalos bajo modelo Poisson y corrección BH. 99 contrastes elegibles y dos señales condicionales de incremento entre cuatro ventanas; no son necesariamente dos zonas distintas ni vigilancia validada.
- Atlas estático: 51 límites municipales INEGI, 1,565 instituciones OSM y 8,646 elementos de movilidad. Capas, opacidad y radios de 100/250/500/1000/2000 m. La proximidad ofrece cotas de registros de celdas visibles, no eventos individuales ni causalidad.
- Epidemiología anual: personas versus registros con desenlace, razones por cien registros e intervalos cuando publicables. Población oficial Censo 2020 únicamente para tasas de 2020.
- Matriz 7×24 y calendario anual. Hora de reporte. Datos temporales y cartográficos cargados por módulo.
- Comparación exploratoria H3/DBSCAN/HDBSCAN/KDE y auditoría contra geometría INEGI original.

## Verificación

31 pruebas Python y cuatro Node aprobadas; hashes, exclusiones y protección pública verificados; TypeScript y build GitHub Pages aprobados. Revisión de navegador de filtros, simulador, ficha, enlace compartible, atlas, proximidad y radar. La publicación usa GitHub Actions y se comprueba para el commit desplegado. No se afirma auditoría formal de accesibilidad ni anonimización frente a todas las fuentes externas.

## Límites y pendientes

Datum RATIV no declarado: H3 y distancias exploratorios. Cambios sustanciales de geocobertura bloquean la mayoría de comparaciones del radar. Sin exposición vial no se interpreta frecuencia como riesgo. El IPIV es una hipótesis de priorización sin validación científica.

Moran I/Gi* no calculados sin malla completa y pesos preespecificados. Intersecciones/segmentos requieren homologación vial. Edad, sexo, escolares, adultos mayores, AVPP y letalidad no calculables con estos contratos. No se extrapola población 2020 a 2025/2026 ni se afirma seguimiento a treinta días. La impresión permite guardar PDF desde el navegador; no se generó un informe científico Quarto/PDF final.

Protocolos: docs/INTELLIGENCE_METHODS.md, docs/V02_REVIEW.md y docs/PUBLICATION.md. Atribuciones: DATA_LICENSES.md.
