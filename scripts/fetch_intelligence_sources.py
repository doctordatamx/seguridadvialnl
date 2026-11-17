"""Descarga acotada de insumos públicos; conserva y reutiliza los originales existentes."""
import json
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlencode
ROOT=Path(__file__).resolve().parents[1]
queries={
 'osm_instituciones_nl.json':'[out:json][timeout:45];area["ISO3166-2"="MX-NLE"]["admin_level"="4"]->.nl;nwr["amenity"~"^(hospital|school|university)$"](area.nl);out center tags;',
 'osm_movilidad_nl.json':'[out:json][timeout:55];area["ISO3166-2"="MX-NLE"]["admin_level"="4"]->.nl;(way["highway"~"^(motorway|trunk|primary|secondary|cycleway)$"](area.nl);way["cycleway"](area.nl);node["highway"="bus_stop"](area.nl);node["public_transport"="platform"](area.nl););out geom;'}
tasks=[(ROOT/'data/external/inegi_municipios_19.json','https://gaia.inegi.org.mx/wscatgeo/v2/mgem/19'),
       (ROOT/'data/geospatial/inegi_municipios_19.geojson','https://gaia.inegi.org.mx/wscatgeo/v2/geo/mgem/19')]
tasks.extend((ROOT/'data/external'/name,'https://overpass-api.de/api/interpreter?'+urlencode({'data':q})) for name,q in queries.items())
if __name__=='__main__':
    for path,url in tasks:
        if path.exists():print('Conservado: '+path.name);continue
        path.parent.mkdir(parents=True,exist_ok=True)
        with urlopen(Request(url,headers={'User-Agent':'OSV-NL/0.2 research data preparation'}),timeout=65) as response:body=response.read()
        data=json.loads(body)
        if data.get('remark'):raise SystemExit('Fuente con error/resultado parcial; no se conserva como descarga válida: '+path.name)
        path.write_bytes(body);print('Descargado: '+path.name)
