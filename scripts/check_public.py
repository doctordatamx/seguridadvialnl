"""Control obligatorio del paquete público versionado, independiente de los datos locales."""
import hashlib
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
folder=root/'release'
manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
assert manifest['mode']=='public_aggregate' and manifest['release_approved'] is True
allowed=['observatory.json','spatial.json','report.html','intelligence.json','temporal.json','methods.json','boundaries.json','institutions.json','atlas-metadata.json','mobility.json','spatial-quality.json']
for name,checksum in manifest['sha256'].items():
    assert name in allowed
    assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==checksum
data=json.loads((folder/'observatory.json').read_text(encoding='utf-8'))
assert data['mode']=='public_aggregate' and data['release_approved'] is True
for row in data['rows']:
    assert row['injured'] is None and row['deaths'] is None
    assert row['crashes'] is None or row['crashes']>=5
for p in data['profiles']:
    assert p['streets']==[] and p['repeated_folio_records'] is None
    assert all(x['name']!='Peatón lesionado o fallecido' for x in p['vulnerable_presence'])
geo=json.loads((folder/'spatial.json').read_text(encoding='utf-8'))
for feature in geo['features']:
    assert set(feature['properties'])=={'cell','municipality','year','crashes'}
    assert feature['properties']['crashes']>=20
print('Edición pública verificada: hashes, umbrales, exclusiones de víctimas/texto libre y esquema agregado.')
if 'intelligence.json' in manifest['sha256']:
    import math
    intelligence=json.loads((folder/'intelligence.json').read_text(encoding='utf-8'))
    dimensions=['frequency','mortality','injuries','trend','vulnerable']
    for z in intelligence['zones']:
        assert z['id']=='h3-r7-'+z['cell'] and z['metrics']['frequency']>=20 and z['baseline_records']>=20
        assert set(z['dimensions'])==set(dimensions)
        assert z['score'] is None or all(z['dimensions'][d] is not None for d in dimensions)
        assert z['score'] is None or 0<=z['score']<=100
        for field in ['mortality','injuries','fatal_records','victim_records','pedestrian_records','motorcycle_records','bicycle_records','vulnerable']:
            n=z['metrics'][field];assert n is None or n==0 or n>=5
        assert all(a['records'] is None or a['records']>=20 for a in z['annual'])
        assert all(m['value'] is None or m['value']>=5 for m in z['monthly'])
        for method,values in z['normalized'].items():
            for d in dimensions:
                assert values[d] is None if z['dimensions'][d] is None else values[d] is not None and 0<=values[d]<=100
        assert z['metrics']['severity'] is None if z['metrics']['fatal_records'] is None else z['metrics']['severity']>=0
        for historic in z['history']:
            if 'dimensions' in historic:
                assert historic['score'] is None or all(v is not None for v in historic['dimensions'].values())
                for key in ['mortality','injuries','vulnerable']:
                    n=historic['dimensions'][key];assert n is None or n==0 or n>=5
    for row in intelligence['epidemiology']:
        for field in ['mortality','injuries','fatal_records','victim_records','pedestrian_records','motorcycle_records','bicycle_records','vulnerable']:
            n=row['metrics'][field];assert n is None or n==0 or n>=5
        if row['year']!='2020':assert row['population'] is None and row['registered_mortality_rate'] is None and row['mortality_ci95'] is None
        if row['metrics']['mortality'] is None:assert row['deaths_per100_records'] is None and row['registered_mortality_rate'] is None and row['mortality_ci95'] is None
    for r in intelligence['radar']:
        assert not r['statistical_alert'] or r['comparable_proxy'] and r['q_value'] is not None and r['q_value']<.05 and r['ratio']>1
    for filename in ['institutions.json','mobility.json']:
        collection=json.loads((folder/filename).read_text(encoding='utf-8'))
        assert collection['license']=='ODbL 1.0'
        assert all(set(f['properties'])=={'id','name','category'} for f in collection['features'])
    temporal=json.loads((folder/'temporal.json').read_text(encoding='utf-8'))
    for p in temporal['profiles']:
        assert all(d['value'] is None or d['value']>=5 for d in p['calendar'])
        assert all(d['value'] is None or d['value']>=5 for d in p['matrix'])
    print('Inteligencia verificada: referencia fija, nulos estrictos, desenlaces protegidos y sus derivados, denominadores 2020 y atribución OSM.')
