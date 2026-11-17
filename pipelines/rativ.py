"""Adaptador RATIV documentado; ninguna columna personal atraviesa esta lista blanca."""
from __future__ import annotations
import math
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import date

MUNICIPALITIES = {'6':'Apodaca', '18':'García', '19':'San Pedro Garza García',
                  '21':'General Escobedo', '26':'Guadalupe', '31':'Juárez', '39':'Monterrey',
                  '41':'Pesquería', '46':'San Nicolás de los Garza', '48':'Santa Catarina', '49':'Santiago'}
VEHICLES = {'1':'Automóvil','2':'Camioneta','3':'Camión urbano','4':'Tráiler','5':'Motocicleta','6':'Bicicleta','7':'Otro'}
MISSING = {'', '99', 'SD', 'S/D', 'NA', 'N/A', 'NAN', 'NONE', 'NULL', 'SIN DATO', 'SIN DATOS', 'NO ESPECIFICADO'}
REQUIRED = {'MUNICIPIO','ENCUESTA','Día','Mes','Año','Hora de reporte','Total de lesionados','Total de fallecidos',
            'Tipo de Hecho de Tránsito','VEHICULO CODIFICADO','VEHICULO CODIFICADO 2','Referencia'}


def clean_text(value):
    if value is None:
        return None
    text = ' '.join(unicodedata.normalize('NFKC', str(value)).upper().split())
    return None if text in MISSING else text


def count_value(value):
    text = clean_text(value)
    if text is None:
        return None
    number = float(text)
    if not math.isfinite(number) or not 0 <= number < 99 or not number.is_integer():
        raise ValueError('Conteo RATIV fuera del dominio documentado 0–98, 99=sin dato')
    return int(number)


def report_hour(value):
    """Hora de reporte, nunca hora del evento. Fechas Excel ambiguas permanecen nulas."""
    text = clean_text(value)
    if text is None:
        return None, 'missing_report_hour'
    match = re.fullmatch(r'([01]?\d|2[0-3]):([0-5]\d)(?::([0-5]\d))?', text)
    if match:
        return int(match.group(1)), 'clock_time'
    # Excel exporta fracciones del día en 2025/2026. No se admiten enteros ni seriales con fecha.
    if re.fullmatch(r'0\.\d+', text):
        fraction = float(text)
        if 0 <= fraction < 1:
            seconds = min(86399, round(fraction * 86400))
            return seconds // 3600, 'excel_fraction_time'
    return None, 'ambiguous_report_hour'


def geographic_pair(value):
    """Sólo par latitud,longitud estricto. No geocodifica ni adivina coordenadas de texto libre."""
    text = clean_text(value)
    if text is None:
        return None, None, 'missing_coordinates'
    match = re.fullmatch(r'([-+]?\d+(?:\.\d+)?)\s*[,;]\s*([-+]?\d+(?:\.\d+)?)', text)
    if match:
        lat, lon = map(float, match.groups())
        if 23 <= lat <= 28.5 and -102 <= lon <= -98:
            return lat, lon, 'plausible_coordinates_datum_unknown'
        return None, None, 'coordinates_outside_regional_bbox'
    return None, None, 'reference_not_coordinate_pair'


def canonicalize_rativ(frame, source, source_key):
    if source.get('observation_unit') != 'crash_record':
        raise ValueError('RATIV requiere unidad crash_record: registro reportado, unicidad no garantizada')
    missing = REQUIRED - set(frame.columns)
    if missing:
        raise ValueError(f'Contrato RATIV incompleto: {sorted(missing)}')
    street_col = source['columns']['street']
    year = source['partition_year']
    records, issues = [], Counter()
    folios = Counter(clean_text(v) for v in frame['ENCUESTA'].to_list())
    issues['missing_source_folio'] = folios.get(None, 0)
    issues['repeated_source_folio_rows'] = sum(n for k, n in folios.items() if k is not None and n > 1)
    for index, raw in enumerate(frame.iter_rows(named=True), start=1):
        try:
            day = date(int(raw['Año']), int(raw['Mes']), int(raw['Día']))
            if day.year != year:
                raise ValueError('Año fuera de partición')
            municipality = MUNICIPALITIES.get(str(raw['MUNICIPIO']).strip())
            if municipality is None:
                raise ValueError('Municipio fuera del catálogo documentado')
        except (ValueError, TypeError):
            issues['rejected_date_or_municipality'] += 1
            continue
        hour, hour_status = report_hour(raw['Hora de reporte'])
        lat, lon, coord_status = geographic_pair(raw['Referencia'])
        issues[hour_status] += 1
        issues[coord_status] += 1
        def parsed(field):
            try:
                result = count_value(raw.get(field))
                if result is None:
                    issues[f'missing_{field}'] += 1
                return result
            except (ValueError, TypeError):
                issues[f'invalid_{field}'] += 1
                return None
        injured, deaths = parsed('Total de lesionados'), parsed('Total de fallecidos')
        pedestrian_injured = parsed('Total de lesionados PEAT')
        pedestrian_deaths = parsed('Total de fallecidos PEAT')
        vehicle_codes = [clean_text(raw.get(k)) for k in ['VEHICULO CODIFICADO','VEHICULO CODIFICADO 2','VEHICULO CODIFICADO 3'] if k in raw]
        vehicle_labels = sorted({VEHICLES[v] for v in vehicle_codes if v in VEHICLES})
        vulnerable = []
        if '5' in vehicle_codes:
            vulnerable.append('Motocicleta involucrada')
        if '6' in vehicle_codes:
            vulnerable.append('Bicicleta involucrada')
        if (pedestrian_injured or 0) > 0 or (pedestrian_deaths or 0) > 0:
            vulnerable.append('Peatón lesionado o fallecido')
        folio = clean_text(raw['ENCUESTA'])
        street = clean_text(raw.get(street_col))
        if street and (len(street) > 120 or re.search(r'\d{7,}|@|https?://', street)):
            street = None
            issues['street_excluded_possible_sensitive_text'] += 1
        records.append({
            'record_id': f'{source_key}:{index}', 'source_row': index, 'event_id': folio,
            'date': day.isoformat(), 'hour': hour, 'weekday': day.weekday(),
            'municipality': municipality, 'municipality_code': str(raw['MUNICIPIO']).zfill(3),
            'injured': injured, 'deaths': deaths, 'crash_type': clean_text(raw['Tipo de Hecho de Tránsito']),
            'vehicle': VEHICLES.get(vehicle_codes[0]), 'vehicles': '; '.join(vehicle_labels) or None,
            'vulnerable_user': '; '.join(vulnerable) or None,
            'pedestrian_injured': pedestrian_injured, 'pedestrian_deaths': pedestrian_deaths,
            'street': street, 'intersection': None, 'latitude': lat, 'longitude': lon,
            'coordinate_status': coord_status, 'source': source_key,
            'folio_status': 'missing' if folio is None else 'repeated_in_file' if folios[folio] > 1 else 'unique_in_file',
        })
    return records, dict(issues)


def disjoint_partitions(rows, sources):
    """Permite unión anual sólo tras comprobar una partición diferente y todas las fechas."""
    active_ids = {r['source'] for r in rows}
    active = [s for s in sources if s['id'] in active_ids]
    years = [s.get('partition_year') for s in active]
    return (len(active) == len(active_ids) and all(isinstance(y, int) for y in years)
            and len(set(years)) == len(years)
            and all(r['date'].startswith(str(next(s['partition_year'] for s in active if s['id'] == r['source'])) + '-') for r in rows))


def protected_histogram(counter, minimum):
    """Suprime al menos dos categorías si hay una celda pequeña; nunca publica el residual."""
    hidden = {k for k, v in counter.items() if 0 < v < minimum}
    if len(hidden) == 1:
        candidates = [k for k in counter if k not in hidden]
        if candidates:
            hidden.add(min(candidates, key=lambda k: counter[k]))
    return [{'name': str(k), 'value': None if k in hidden else int(v), 'suppressed': k in hidden}
            for k, v in sorted(counter.items(), key=lambda x: str(x[0]))]


def local_views(rows, minimum, spatial_enabled):
    """Desgloses locales agregados, jamás registros ni ubicaciones de personas."""
    import h3
    groups = defaultdict(list)
    for r in rows:
        groups[(r['municipality'], r['date'][:4])].append(r)
    profiles, features = [], []
    spatial_min = max(10, minimum)
    for (municipality, year), records in sorted(groups.items()):
        hour = Counter(r['hour'] for r in records if r['hour'] is not None)
        weekday = Counter(r['weekday'] for r in records)
        kind = Counter(r['crash_type'] for r in records if r['crash_type'])
        vehicle = Counter(r['vehicle'] for r in records if r['vehicle'])
        # Indicadores de presencia, NO número de personas ni categorías mutuamente excluyentes.
        vulnerable = Counter(label for r in records for label in (r.get('vulnerable_user') or '').split('; ') if label)
        streets = Counter(r['street'] for r in records if r['street'])
        spatial_records = [r for r in records if r['latitude'] is not None]
        h3_cells = Counter(h3.latlng_to_cell(r['latitude'],r['longitude'],8) for r in spatial_records) if spatial_enabled else Counter()
        for cell, count in sorted(h3_cells.items()):
            if count < spatial_min:
                continue
            boundary = [[lon,lat] for lat,lon in h3.cell_to_boundary(cell)]
            features.append({'type':'Feature','properties':{'cell':cell,'municipality':municipality,'year':year,'crashes':count},
                             'geometry':{'type':'Polygon','coordinates':[boundary+[boundary[0]]]}})
        profiles.append({'municipality':municipality,'year':year,'records':len(records),
                         'date_min':min(r['date'] for r in records),'date_max':max(r['date'] for r in records),
                         'months_observed':sorted({r['date'][:7] for r in records}),
                         'hours_known':sum(hour.values()),'coordinates_plausible':len(spatial_records),
                         'injured_known':sum(r['injured'] is not None for r in records),
                         'deaths_known':sum(r['deaths'] is not None for r in records),
                         'repeated_folio_records':sum(r['folio_status']=='repeated_in_file' for r in records),
                         'weekday':protected_histogram(weekday, minimum),
                         'report_hour':protected_histogram(hour, minimum),
                         'crash_types':protected_histogram(kind,minimum),
                         'primary_vehicle':protected_histogram(vehicle,minimum),
                         'vulnerable_presence':protected_histogram(vulnerable,minimum),
                         'streets':[{'name':name,'value':n} for name,n in streets.most_common() if n>=max(20,minimum)][:10]})
    if spatial_enabled:
        # Vista conjunta calculada desde registros, no sumando sólo las celdas municipales visibles.
        combined = Counter((r['date'][:4], h3.latlng_to_cell(r['latitude'], r['longitude'], 8))
                           for r in rows if r['latitude'] is not None)
        for (year, cell), count in sorted(combined.items()):
            if count < spatial_min:
                continue
            boundary = [[lon,lat] for lat,lon in h3.cell_to_boundary(cell)]
            features.append({'type':'Feature','properties':{'cell':cell,'municipality':'Conjunto observado','year':year,'crashes':count},
                             'geometry':{'type':'Polygon','coordinates':[boundary+[boundary[0]]]}})
    return profiles, {'type':'FeatureCollection','features':features}
