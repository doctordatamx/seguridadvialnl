"""Control obligatorio del paquete público versionado, independiente de los datos locales."""
import hashlib
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
folder=root/'release'
manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
assert manifest['mode']=='public_aggregate' and manifest['release_approved'] is True
for name,checksum in manifest['sha256'].items():
    assert name in ['observatory.json','spatial.json','report.html']
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
