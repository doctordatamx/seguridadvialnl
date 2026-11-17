"""Prepara geometría oficial simplificada y POI OSM con atribución y lista blanca."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
import geopandas as gpd

ROOT=Path(__file__).resolve().parents[1]


def prepare():
    raw=ROOT/'data/geospatial/inegi_municipios_19.geojson'
    original=json.loads(raw.read_text(encoding='utf-8'))
    geo=gpd.read_file(raw)
    if len(geo)!=51:raise ValueError('El catálogo municipal no tiene 51 registros')
    # El servicio publica GeoJSON. Se conserva la geometría original local para validaciones.
    geo=geo.to_crs(32614)
    geo.geometry=geo.geometry.simplify(100,preserve_topology=True)
    geo=geo.to_crs(4326)
    result=json.loads(geo[['cvegeo','nomgeo','geometry']].to_json(drop_id=True))
    result['metadatos']=original['metadatos']
    result['processing']={'method':'Simplificación topológica, tolerancia 100 metros en EPSG:32614; exportación GeoJSON EPSG:4326. No apta para delimitación legal ni medición catastral.'}
    folder=ROOT/'release';folder.mkdir(exist_ok=True)
    (folder/'boundaries.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    pois=[];source=ROOT/'data/external/osm_instituciones_nl.json'
    if source.exists():
        data=json.loads(source.read_text(encoding='utf-8'))
        for e in data.get('elements',[]):
            tags=e.get('tags',{});category=tags.get('amenity')
            if category not in ['hospital','school','university']:continue
            point=e.get('center',e);lat,lon=point.get('lat'),point.get('lon')
            if lat is None or lon is None:continue
            # Instituciones públicas/visibles en OSM. No se copian contactos ni direcciones particulares.
            name=str(tags.get('name') or {'hospital':'Hospital','school':'Centro educativo','university':'Universidad'}[category])[:180]
            pois.append({'type':'Feature','geometry':{'type':'Point','coordinates':[lon,lat]},
                         'properties':{'id':str(e['type'])+'/'+str(e['id']),'name':name,'category':category}})
    (folder/'institutions.json').write_text(json.dumps({'type':'FeatureCollection','features':pois,'license':'ODbL 1.0','attribution':'© OpenStreetMap contributors','source':'https://www.openstreetmap.org/copyright','overpass_timestamp':data.get('osm3s',{}).get('timestamp_osm_base') if source.exists() else None},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    movement=[];movement_path=ROOT/'data/external/osm_movilidad_nl.json'
    if movement_path.exists():
        from shapely.geometry import LineString
        from pyproj import Transformer
        forward=Transformer.from_crs(4326,32614,always_xy=True);back=Transformer.from_crs(32614,4326,always_xy=True)
        source_movement=json.loads(movement_path.read_text(encoding='utf-8'))
        for e in source_movement.get('elements',[]):
            tags=e.get('tags',{});cycling=tags.get('highway')=='cycleway' or any(k.startswith('cycleway') and str(v).lower() not in ['no','none','separate'] for k,v in tags.items())
            if e['type']=='node':
                if 'lat' not in e or 'lon' not in e:continue
                geometry={'type':'Point','coordinates':[e['lon'],e['lat']]};category='transit'
            else:
                points=[(p['lon'],p['lat']) for p in e.get('geometry',[]) if 'lon' in p and 'lat' in p]
                if len(points)<2:continue
                projected=LineString([forward.transform(*p) for p in points]).simplify(25,preserve_topology=True)
                geometry={'type':'LineString','coordinates':[list(back.transform(*p)) for p in projected.coords]};category='cycling' if cycling else 'roads'
            movement.append({'type':'Feature','geometry':geometry,'properties':{'id':e['type']+'/'+str(e['id']),'name':str(tags.get('name') or 'Elemento OSM')[:180],'category':category}})
    (folder/'mobility.json').write_text(json.dumps({'type':'FeatureCollection','features':movement,'license':'ODbL 1.0','attribution':'© OpenStreetMap contributors','processing':'Red vial principal e infraestructura registrada, no inventario exhaustivo. Líneas simplificadas 25 metros en UTM 14N.'},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    metadata={'prepared_at':datetime.now(timezone.utc).isoformat(),'sources':[
        {'name':'INEGI · Marco Geoestadístico diciembre 2025 y Censo 2020','url':'https://gaia.inegi.org.mx/wscatgeo/v2/geo/mgem/19','license':'Términos de libre uso INEGI','terms':'https://www.inegi.org.mx/inegi/terminos.html','original_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'processing':'Simplificación de geometrías para visualización; análisis de OSV-NL, no de INEGI.'},
        {'name':'© OpenStreetMap contributors','url':'https://overpass-api.de/api/interpreter','license':'ODbL 1.0','terms':'https://opendatacommons.org/licenses/odbl/1-0/','count':len(pois),'status':'available' if pois else 'unavailable'}],
        'layers':[{'id':'boundaries','label':'Límites municipales','status':'available','records':51},
                  {'id':'institutions','label':'Hospitales y centros educativos OSM','status':'available' if pois else 'unavailable','records':len(pois)},
                  {'id':'roads','label':'Red vial','status':'not_integrated','reason':'Sin conector y revisión de geometría/licencia en esta versión.'},
                  {'id':'cycling','label':'Infraestructura ciclista','status':'not_integrated','reason':'No se infiere de la presencia de bicicletas en siniestros.'},
                  {'id':'transit','label':'Paradas de transporte','status':'not_integrated','reason':'Pendiente de fuente y actualización verificables.'}]}
    for layer in metadata['layers']:
        if layer['id'] in ['roads','cycling','transit']:
            layer['records']=sum(f['properties']['category']==layer['id'] for f in movement)
            layer['status']='available' if layer['records'] else 'unavailable'
            layer['reason']='Inventario OSM parcial; no se interpreta ausencia como falta de infraestructura.'
    (folder/'atlas-metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'municipalities':len(geo),'institutions':len(pois),'mobility_features':len(movement)}))


if __name__=='__main__':prepare()
