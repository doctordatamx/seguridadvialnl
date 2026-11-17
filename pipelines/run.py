"""Auditoría local y publicación agregada con autorización por fuente. Nunca modifica originales."""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import html
import io
import json
import math
import re
import unicodedata
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
SUPPORTED = {'.csv', '.tsv', '.xlsx', '.xls', '.json', '.geojson', '.shp', '.gpkg', '.parquet', '.zip', '.gz'}
CANONICAL = ['event_id', 'date', 'hour', 'municipality', 'injured', 'deaths', 'crash_type', 'vehicle', 'vulnerable_user', 'street', 'intersection', 'latitude', 'longitude']


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def tabular_csv(payload, suffix):
    for encoding in ('utf-8-sig', 'cp1252'):
        try:
            text = payload.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    try:
        dialect = csv.Sniffer().sniff(text[:65536], delimiters=',;\t|') if text.strip() else csv.excel
    except csv.Error:
        dialect = csv.excel
    return pl.read_csv(io.StringIO(text), separator='\t' if suffix == '.tsv' else dialect.delimiter, infer_schema=False)


def read_tables(path):
    """Devuelve cada hoja/capa por separado; ZIP se lee sin extraer rutas."""
    suffix = path.suffix.lower()
    if suffix == '.gz':
        if not path.name.lower().endswith(('.csv.gz', '.tsv.gz')):
            raise ValueError('Gzip requiere CSV/TSV; otro contenido necesita adaptador')
        with gzip.open(path, 'rb') as stream:
            yield '', tabular_csv(stream.read(), Path(path.stem).suffix.lower()), None
    elif suffix in {'.csv', '.tsv'}:
        yield '', tabular_csv(path.read_bytes(), suffix), None
    elif suffix in {'.xlsx', '.xls'}:
        import pandas as pd
        for sheet, frame in pd.read_excel(path, sheet_name=None, dtype=str).items():
            yield sheet, pl.from_pandas(frame), None
    elif suffix == '.parquet':
        yield '', pl.read_parquet(path), None
    elif suffix in {'.geojson', '.shp', '.gpkg'}:
        import geopandas as gpd
        import pyogrio
        layers = pyogrio.list_layers(path) if suffix == '.gpkg' else [('', '')]
        for layer, _ in layers:
            geo = gpd.read_file(path, **({'layer': layer} if layer else {}))
            crs = str(geo.crs) if geo.crs else None
            frame = geo.drop(columns=geo.geometry.name)
            yield layer, pl.from_pandas(frame.astype('string')), crs
    elif suffix == '.json':
        obj = json.loads(path.read_text(encoding='utf-8-sig'))
        if not isinstance(obj, list) or any(not isinstance(row, dict) for row in obj):
            raise ValueError('JSON requiere una lista de objetos; crear adaptador para otra estructura')
        yield '', pl.from_dicts(obj, infer_schema_length=None), None
    elif suffix == '.zip':
        with zipfile.ZipFile(path) as archive:
            if sum(x.file_size for x in archive.infolist()) > 512 * 1024 * 1024:
                raise ValueError('ZIP supera el límite descomprimido de 512 MB')
            for member in archive.infolist():
                if Path(member.filename).suffix.lower() in {'.csv', '.tsv'}:
                    yield member.filename, tabular_csv(archive.read(member), Path(member.filename).suffix.lower()), None
                elif not member.is_dir():
                    raise ValueError('ZIP contiene archivos no CSV/TSV; descomprimir manualmente en data/raw para auditar capas/hojas')


def normalized_text(value):
    return ' '.join(unicodedata.normalize('NFKC', str(value)).upper().split()) if value is not None else None


def parse_count(value):
    if value is None or str(value).strip() == '':
        return None
    number = float(value)
    if not math.isfinite(number) or number < 0 or not number.is_integer():
        raise ValueError('Conteo negativo, no finito o no entero')
    return int(number)


def canonicalize(frame, source, source_key):
    if source.get('adapter') == 'rativ_v1':
        from pipelines.rativ import canonicalize_rativ
        return canonicalize_rativ(frame, source, source_key)
    mapping = source.get('columns', {})
    missing = set(mapping.values()) - set(frame.columns)
    if missing:
        raise ValueError(f'Columnas configuradas ausentes: {sorted(missing)}')
    if not {'event_id', 'date', 'municipality'} <= set(mapping):
        raise ValueError('Se requieren event_id, date y municipality con unidad de observación siniestro')
    if source.get('observation_unit') != 'crash':
        raise ValueError('La base no está validada como una fila por siniestro')
    rows, issues, seen = [], Counter(), set()
    for row in frame.iter_rows(named=True):
        result = {k: row.get(mapping[k]) if k in mapping else None for k in CANONICAL}
        try:
            result['date'] = datetime.strptime(str(result['date']), source['date_format']).date().isoformat()
            if not str(result['event_id'] or '').strip() or not str(result['municipality'] or '').strip():
                raise ValueError('Identificador o municipio ausente')
            municipality = normalized_text(result['municipality'])
            result['municipality'] = source.get('municipality_aliases', {}).get(municipality, municipality)
            for field in ('injured', 'deaths'):
                result[field] = parse_count(result[field])
            result['hour'] = parse_count(result['hour'])
            if result['hour'] is not None and result['hour'] > 23:
                raise ValueError('Hora fuera de 0–23')
            for field in ('street', 'intersection', 'crash_type', 'vehicle', 'vulnerable_user'):
                result[field] = normalized_text(result[field]) or None
            lat, lon = result['latitude'], result['longitude']
            result['latitude'] = result['longitude'] = None
            if lat is not None or lon is not None:
                try:
                    lat, lon = float(lat), float(lon)
                    if source.get('coordinate_crs') != 'EPSG:4326' or not (23 <= lat <= 28.5 and -102 <= lon <= -98):
                        raise ValueError('CRS o extensión inválida')
                    result['latitude'], result['longitude'] = lat, lon
                except (ValueError, TypeError):
                    issues['invalid_coordinates'] += 1
            key = str(result['event_id'])
            if key in seen:
                issues['duplicate_event_id'] += 1
                continue
            seen.add(key)
            result['source'] = source_key
            rows.append(result)
        except (ValueError, TypeError, KeyError):
            issues['rejected_rows'] += 1
    return rows, dict(issues)


def total(rows, field):
    values = [r[field] for r in rows]
    # Un total parcial no equivale al total de personas.
    return sum(values) if values and all(v is not None for v in values) else None


def aggregates(rows, minimum):
    groups = defaultdict(list)
    for row in rows:
        # Sólo celdas mensuales municipales: nunca se exportan microdatos ni coordenadas.
        groups[(row['municipality'], row['date'][:7])].append(row)
    output = []
    for (municipality, month), group in sorted(groups.items()):
        suppressed = len(group) < minimum
        injured, deaths = total(group, 'injured'), total(group, 'deaths')
        output.append({'municipality': municipality, 'month': month,
                       'crashes': None if suppressed else len(group),
                       'injured': None if suppressed or injured is not None and 0 < injured < minimum else injured,
                       'deaths': None if suppressed or deaths is not None and 0 < deaths < minimum else deaths,
                       'injured_status': 'suppressed' if suppressed or injured is not None and 0 < injured < minimum else 'missing' if injured is None else 'known',
                       'deaths_status': 'suppressed' if suppressed or deaths is not None and 0 < deaths < minimum else 'missing' if deaths is None else 'known',
                       'suppressed': suppressed})
    return output


def hotspots(rows, config):
    """Resultados locales de investigación, nunca publicados automáticamente."""
    import h3
    from sklearn.cluster import DBSCAN
    import numpy as np
    points = [r for r in rows if r['latitude'] is not None]
    sensitivity = []
    for resolution in config['h3_resolutions']:
        cells = Counter(h3.latlng_to_cell(r['latitude'], r['longitude'], resolution) for r in points)
        sensitivity.append({'resolution': resolution, 'cells': len(cells), 'top10': cells.most_common(10)})
    clusters = []
    deferred = len(points) > config.get('dbscan_max_points', 50000)
    if points and not deferred:
        coordinates = np.radians([[r['latitude'], r['longitude']] for r in points])
        labels = DBSCAN(eps=config['dbscan_eps_meters'] / 6371008.8,
                        min_samples=config['dbscan_min_samples'], metric='haversine', algorithm='ball_tree').fit_predict(coordinates)
        clusters = [{'cluster': int(k), 'crashes': v} for k, v in Counter(labels).items() if k != -1]
    return {'parameters': config, 'geocoded_rows': len(points), 'h3_sensitivity': sensitivity, 'dbscan': clusters,
            'dbscan_status': 'deferred_size_guard' if deferred else 'computed' if points else 'no_points',
            'warning': 'Concentraciones, no riesgo. Resultados locales; pendientes revisión de privacidad y cobertura.'}


def run(root=ROOT, input_dir=None):
    root = Path(root)
    config = json.loads((root / 'config/sources.json').read_text(encoding='utf-8'))
    minimum = config.get('privacy', {}).get('minimum_cell_size', 5)
    if not isinstance(minimum, int) or minimum < 5:
        raise ValueError('minimum_cell_size debe ser entero >=5')
    folders = ['reports/audit', 'data/processed', 'data/interim', 'database', 'web/public/data']
    for folder in folders:
        (root / folder).mkdir(parents=True, exist_ok=True)
    scan = Path(input_dir) if input_dir else root / 'data/raw'
    files = sorted(p for p in scan.rglob('*') if p.is_file() and p.name != '.gitkeep') if scan.exists() else []
    catalog, dictionary, coverage, analytical, publishable = [], [], [], [], []
    prior_path = root / 'reports/audit/SOURCE_CATALOG.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8')) if prior_path.exists() else []
    prior_schemas = {x['id']: x.get('schema') for x in prior}
    for path in files:
        relative = path.relative_to(scan).as_posix()
        base = {'path': relative, 'sha256': digest(path), 'bytes': path.stat().st_size}
        if path.suffix.lower() not in SUPPORTED:
            catalog.append({**base, 'id': relative, 'status': 'unsupported', 'note': 'Inventariado; requiere adaptador'})
            continue
        try:
            for sheet, frame, crs in read_tables(path):
                key = relative + (f'::{sheet}' if sheet else '')
                source = next((s for s in config['sources'] if s['id'] == key), {})
                schema = {k: str(v) for k, v in frame.schema.items()}
                record = {**base, 'id': key, 'status': 'audited', 'rows': frame.height, 'variables': frame.width,
                          'schema': schema, 'schema_changed': key in prior_schemas and prior_schemas[key] != schema,
                          'exact_duplicate_rows': frame.height - frame.unique().height, 'crs': crs,
                          'license': source.get('license', 'Sin verificar'), 'observation_unit': source.get('observation_unit', 'Sin verificar'),
                          'source_url': source.get('source_url'), 'configured': bool(source)}
                for column in frame.columns:
                    series = frame[column]
                    blank = series.cast(pl.String, strict=False).str.strip_chars().eq('').fill_null(False).sum()
                    dictionary.append({'source': key, 'variable': column, 'dtype': str(series.dtype),
                                       'nulls': series.null_count(), 'blank_strings': blank, 'distinct': series.n_unique(),
                                       'semantic_missing_codes': series.cast(pl.String, strict=False).str.strip_chars().str.to_uppercase().is_in(['99','SD','S/D','NA','N/A']).sum() if source.get('adapter') == 'rativ_v1' else None,
                                       'canonical': next((k for k, v in source.get('columns', {}).items() if v == column), '')})
                if source:
                    cleaned, issues = canonicalize(frame, source, key)
                    record['validation'] = issues
                    record['accepted_rows'] = len(cleaned)
                    record['date_min'] = min((r['date'] for r in cleaned), default=None)
                    record['date_max'] = max((r['date'] for r in cleaned), default=None)
                    record['valid_coordinates'] = sum(r['latitude'] is not None for r in cleaned)
                    analytical.extend(cleaned)
                    approved = source.get('redistribution_approved') is True or (config.get('mode') == 'local_preview' and source.get('local_preview_approved') is True)
                    if approved and source.get('privacy_reviewed') is True and source.get('license'):
                        publishable.extend(cleaned)
                    matrix = defaultdict(list)
                    for row in cleaned:
                        matrix[(row['municipality'], row['date'][:4])].append(row)
                    for (municipality, year), group in sorted(matrix.items()):
                        for field in CANONICAL:
                            n = sum(r[field] is not None for r in group)
                            coverage.append({'source': key, 'municipality': municipality, 'year': year, 'variable': field,
                                             'records': len(group), 'non_null': n, 'available': field in source['columns'] or field in source.get('derived_fields', []),
                                             'coverage_status': 'Registros observados; exhaustividad sin verificar'})
                catalog.append(record)
        except Exception as error:
            catalog.append({**base, 'id': relative, 'status': 'error', 'error': str(error)})
    report = root / 'reports/audit'
    write_json(report / 'SOURCE_CATALOG.json', catalog)
    write_csv(report / 'DATA_DICTIONARY.csv', dictionary, ['source', 'variable', 'dtype', 'nulls', 'blank_strings', 'distinct', 'semantic_missing_codes', 'canonical'])
    comparisons = []
    audited = [c for c in catalog if c['status'] == 'audited']
    for previous, current in zip(audited, audited[1:]):
        comparisons.append({'previous': previous['id'], 'current': current['id'],
                            'added': sorted(set(current['schema']) - set(previous['schema'])),
                            'removed': sorted(set(previous['schema']) - set(current['schema']))})
    write_json(report / 'SCHEMA_COMPARISON.json', comparisons)
    write_csv(report / 'MUNICIPAL_COVERAGE.csv', coverage, ['source', 'municipality', 'year', 'variable', 'records', 'non_null', 'available', 'coverage_status'])
    audit = '# Auditoría de datos OSV-NL\n\n' + f'Archivos inventariados: {len(files)}. Tablas/capas auditadas: {sum(c["status"] == "audited" for c in catalog)}.\n\n'
    audit += ('No hay archivos de entrada. La ausencia de datos NO significa cero siniestros.\n\n' if not files else '')
    audit += '## Hallazgos\n\n'
    audit += '\n'.join(f'- `{c["id"]}`: {c["status"]}; filas {c.get("rows", "ND")}; variables {c.get("variables", "ND")}; licencia {c.get("license", "sin verificar")}.' for c in catalog)
    if any(s.get('adapter') == 'rativ_v1' for s in config['sources']):
        audit += '\n\n## Validación RATIV\n\nUna fila se interpreta como registro reportado de siniestro, no como evento único garantizado. ENCUESTA no es único en todos los años; no se elimina por folio repetido. record_id conserva archivo y posición. Los duplicados exactos se reportan y se conservan hasta conciliación. Particiones anuales unidas sólo tras comprobar fechas disjuntas.\n\nSe deriva día de la semana desde fecha: catálogo y diccionario discrepan. Hora es de REPORTE; seriales de fecha ambiguos permanecen nulos, fracciones Excel del día explícitas se convierten a hora. 99/SD/NA son sin dato, no conteos. Referencia sólo se admite como par numérico estricto en extensión regional; datum no declarado. H3 es exploración provisional, no punto crítico validado. No se publican teléfonos, placas, pólizas, narraciones, folios ni coordenadas individuales.\n\n'
        for c in catalog:
            if c.get('accepted_rows') is not None:
                audit += f'- {c["id"]}: {c["accepted_rows"]} registros; {c["date_min"]} a {c["date_max"]}; pares geográficos plausibles {c["valid_coordinates"]}; diagnósticos: {json.dumps(c["validation"], ensure_ascii=False)}.\n'
    audit += '\n\n## Límites y decisiones\n\nNo se infieren columnas, periodos, unidad de observación ni CRS. CSV se conserva como texto para proteger códigos y fechas. Los nulos y cadenas vacías se cuentan por separado. Duplicados exactos se reportan; event_id duplicados por tabla se excluyen y se registran. No se resuelven solapamientos entre fuentes automáticamente.\n\nCobertura municipal, fechas, gravedad, vehículos, usuarios vulnerables, calles y coordenadas requieren mapeo explícito y validación semántica. Sin adaptador: no evaluables, no ausentes. El CRS de capas se registra; geometrías no se convierten automáticamente en puntos. Coordenadas tabulares sólo se aceptan con EPSG:4326 explícito y filtro aproximado regional (no prueba de pertenencia municipal).\n\nLicencias sujetas a revisión por fuente. La descarga local no autoriza redistribución automática. Consultar data/external/ocisevi-download-manifest.json para la adquisición OCISEVI cuando exista. Una matriz vacía significa cobertura desconocida, no ausencia de siniestros.\n'
    (report / 'DATA_AUDIT.md').write_text(audit, encoding='utf-8')
    (report / 'DATA_QUALITY_REPORT.html').write_text('<!doctype html><html lang="es"><meta charset="utf-8"><title>Auditoría OSV-NL</title><style>body{font:16px system-ui;max-width:1100px;margin:40px auto;padding:24px;background:#f1f5f9;color:#0b1728}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><h1>Calidad y trazabilidad</h1><pre>' + html.escape(audit) + '</pre><h2>Detalle por fuente</h2><pre>' + html.escape(json.dumps(catalog, indent=2, ensure_ascii=False)) + '</pre></html>', encoding='utf-8')
    # Reescribir salidas incluso vacías elimina datos obsoletos si se retira la aprobación.
    schema = {k: pl.String for k in CANONICAL + ['source']}
    frame = pl.from_dicts(analytical, infer_schema_length=None) if analytical else pl.DataFrame(schema=schema)
    frame.write_parquet(root / 'data/processed/crashes.parquet')
    import duckdb
    with duckdb.connect(str(root / 'database/observatory.duckdb')) as connection:
        connection.execute('CREATE OR REPLACE TABLE crashes AS SELECT * FROM read_parquet(?)', [str(root / 'data/processed/crashes.parquet')])
    # Por seguridad, múltiples fuentes autorizadas se bloquean hasta resolver solapamiento.
    from pipelines.rativ import disjoint_partitions
    overlapping = len({r['source'] for r in publishable}) > 1 and not disjoint_partitions(publishable, config['sources'])
    if overlapping:
        publishable = []
    public = aggregates(publishable, minimum)
    stamp = datetime.now(timezone.utc).isoformat()
    payload = {'status': 'ready' if public else 'awaiting_data', 'generated_at': stamp,
               'mode': config.get('mode', 'release'),
               'release_approved': config.get('mode') != 'local_preview' and all(s.get('redistribution_approved') is True for s in config['sources']),
               'data_through': max((r['date'] for r in publishable), default=None),
               'minimum_cell_size': minimum, 'rows': public,
               'limitations': ['Cobertura observada; no equivale a cobertura estatal completa.',
                                'Celdas pequeñas suprimidas; los totales parciales no son totales reales.',
                                'Muertes registradas no equivalen a mortalidad a 30 días.',
                                'Solapamiento de fuentes pendiente; publicación bloqueada.' if overlapping else 'Fuentes revisadas para procesamiento local; condiciones de redistribución registradas por separado.'],
               'sources': [{'id': s['id'], 'license': s.get('license'), 'url': s.get('source_url')} for s in config['sources'] if (s.get('redistribution_approved') or config.get('mode') == 'local_preview' and s.get('local_preview_approved')) and s.get('privacy_reviewed')]}
    if config.get('mode') == 'local_preview':
        from pipelines.rativ import local_views
        profiles, spatial = local_views(publishable, minimum, config.get('experimental_spatial_enabled', False))
        payload['profiles'] = profiles
        payload['record_unit'] = 'crash_record'
        payload['limitations'] += ['Vista local: redistribución pública no aprobada.', 'Registros reportados; folios repetidos y 200 filas exactas repetidas en 2019 pendientes de conciliación.', 'Hora de reporte, no hora exacta del siniestro.', 'Coordenadas plausibles; datum y pertenencia municipal no verificados. H3 provisional.', '2026 sólo incluye enero–junio; no comparar con años completos.']
        write_json(root / 'web/public/data/spatial.json', spatial)
        from pipelines.report import render_local_report
        (root / 'web/public/data/report.html').write_text(render_local_report(payload, catalog), encoding='utf-8')
        from pipelines.spatial import grouped_dbscan
        if config.get('experimental_spatial_enabled'):
            write_json(root / 'data/processed/dbscan_by_municipality_year.json', grouped_dbscan(publishable))
    else:
        write_json(root / 'web/public/data/spatial.json', {'type':'FeatureCollection','features':[]})
        (root / 'web/public/data/report.html').write_text('<!doctype html><html lang="es"><meta charset="utf-8"><title>Informe no disponible</title><p>Sin informe local disponible en esta ejecución.</p></html>', encoding='utf-8')
    write_json(root / 'web/public/data/observatory.json', payload)
    write_json(root / 'data/processed/hotspots.json', hotspots(analytical, config['hotspots']))
    manifest = {'generated_at': stamp, 'inputs': [{k: c[k] for k in ('id', 'sha256', 'status')} for c in catalog], 'accepted_rows': len(analytical), 'public_cells': len(public)}
    write_json(root / 'data/interim/manifest.json', manifest)
    write_json(root / 'data/interim/manifests' / (stamp.replace(':', '-').replace('+', '_') + '.json'), manifest)
    print(f'Auditoría: {len(files)} archivos | {len(analytical)} filas analíticas | {len(public)} celdas agregadas | modo {payload["mode"]}')
    return payload


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, help='Directorio recursivo de originales (predeterminado data/raw)')
    args = parser.parse_args()
    run(input_dir=args.input)
