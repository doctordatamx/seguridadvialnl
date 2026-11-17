"""Edición pública de estadística derivada: nunca copia bases ni microdatos."""
import copy
import hashlib
import html
import json
from collections import Counter
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def prepare(root=ROOT):
    import h3
    import polars as pl
    from pipelines.rativ import protected_histogram
    root=Path(root)
    local=json.loads((root/'web/public/data/observatory.json').read_text(encoding='utf-8'))
    records=pl.read_parquet(root/'data/processed/crashes.parquet')
    release=root/'release';release.mkdir(exist_ok=True)
    data=copy.deepcopy(local)
    data['mode']='public_aggregate';data['release_approved']=True
    data['publication_scope']='Estadística derivada, sin redistribución de originales, microdatos ni conteos de víctimas.'
    for r in data['rows']:
        for field in ['injured','deaths']:
            r[field]=None;r[field+'_status']='withheld_public'
    # No publicar un total anual que permita recuperar una única celda mensual suprimida.
    excluded={(r['municipality'],r['month'][:4]) for r in data['rows'] if r['suppressed']}
    data['profiles']=[p for p in data.get('profiles',[]) if (p['municipality'],p['year']) not in excluded]
    for p in data['profiles']:
        p['streets']=[]
        p['repeated_folio_records']=None
        # Presencia de peatón lesionado/fallecido revela un desenlace: fuera de la edición pública.
        p['vulnerable_presence']=[r for r in p['vulnerable_presence'] if r['name']!='Peatón lesionado o fallecido']
    data['limitations']=[
        'Registros reportados de once municipios; no es cobertura estatal exhaustiva ni garantía de eventos únicos.',
        '2026 incluye enero–junio. No comparar con años completos sin controlar cobertura.',
        'Los folios repetidos y las filas exactas repetidas de 2019 requieren conciliación con la fuente.',
        'Hora de reporte, no hora exacta de ocurrencia. Fechas horarias ambiguas permanecen nulas.',
        'Edición pública de estadística derivada: originales, microdatos, conteos de víctimas y calles en texto libre excluidos.',
        'Se omiten perfiles anuales que podrían permitir reconstruir celdas mensuales pequeñas. Ausencia no equivale a cero.',
        'Mapa H3 resolución 7 con mínimo veinte registros. Datum y límites municipales no verificados; exploración provisional, no riesgo.',
    ]
    for s in data['sources']:
        s['license']='Pautas de uso OCISEVI: citar fuente y mantener integridad. Se presentan agregaciones derivadas, sin redistribuir originales.'
    positions=Counter()
    for r in records.select(['date','municipality','latitude','longitude']).iter_rows(named=True):
        if r['latitude'] is None:continue
        year=r['date'][:4];cell=h3.latlng_to_cell(r['latitude'],r['longitude'],7)
        positions[(year,r['municipality'],cell)]+=1
        positions[(year,'Conjunto observado',cell)]+=1
    features=[]
    for (year,municipality,cell),n in sorted(positions.items()):
        if n<20:continue
        ring=[[lon,lat] for lat,lon in h3.cell_to_boundary(cell)]
        features.append({'type':'Feature','properties':{'cell':cell,'municipality':municipality,'year':year,'crashes':n},'geometry':{'type':'Polygon','coordinates':[ring+[ring[0]]]}})
    spatial={'type':'FeatureCollection','features':features}
    # La edición pública no contiene informes locales ni tablas de desenlaces personales.
    report='''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>OSV-NL · Alcance de la edición pública</title><style>body{font:16px/1.8 system-ui;max-width:1000px;margin:auto;padding:30px;color:#18334d}li{margin:12px 0}a{color:#075985}</style></head><body><h1>OSV-NL · Edición pública</h1><p>Observatorio ciudadano independiente. No es un organismo gubernamental ni una plataforma oficial de OCISEVI.</p><p>Corte de los registros: '''+html.escape(data['data_through'])+'''</p><h2>Alcance y método</h2><ul>'''+''.join('<li>'+html.escape(t)+'</li>' for t in data['limitations'])+'''</ul><h2>Fuentes y reproducibilidad</h2><p>Fuente: <a href="https://ocisevi.org.mx/ocisevi-nl/">OCISEVI Nuevo León · RATIV</a>. Se cita la fuente y se preservan los originales localmente. Esta página presenta estadística derivada; no asigna una licencia propia a datos de terceros.</p><p>El código, las reglas de preparación y los hashes de esta edición están en <a href="https://github.com/doctordatamx/seguridadvialnl">doctordatamx/seguridadvialnl</a>. Los archivos originales y los resultados de investigación con mayor detalle no forman parte del repositorio público.</p></body></html>'''
    for name,value in [('observatory.json',data),('spatial.json',spatial)]:
        (release/name).write_text(json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False),encoding='utf-8')
    (release/'report.html').write_text(report,encoding='utf-8')
    manifest={'mode':'public_aggregate','release_approved':True,'owner_authorization':'Solicitud explícita de publicar en doctordatamx/seguridadvialnl, 2026-11-17.',
              'scope':data['publication_scope'],'spatial_resolution':7,'minimum_spatial_count':20,
              'excluded':['raw_data','microdata','victim_counts','source_folios','contact_details','free_text_streets','local_research_results'],
              'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in release.iterdir() if p.name in ['observatory.json','spatial.json','report.html']}}
    (release/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'monthly_cells':len(data['rows']),'municipality_year_profiles':len(data['profiles']),'h3_features':len(features),'release':str(release)}))


if __name__=='__main__':prepare()
