"""Contrasta coordenadas con geometría INEGI original sin publicar puntos."""
import argparse,json
from pathlib import Path
import geopandas as gpd
import polars as pl
import shapely

ROOT=Path(__file__).resolve().parents[1]


def audit(path):
    geo=gpd.read_file(ROOT/'data/geospatial/inegi_municipios_19.geojson').to_crs(4326)
    boundaries={str(row['cvegeo']):row.geometry for _,row in geo.iterrows()}
    state=shapely.union_all(geo.geometry.to_numpy());shapely.prepare(state)
    data=pl.read_parquet(path).with_columns(pl.col('date').str.slice(0,4).alias('year'))
    results=[]
    for (municipality,year),group in data.group_by(['municipality','year'],maintain_order=True):
        points=group.filter(pl.col('latitude').is_not_null());inside_state=inside_reported=0
        if len(points):
            lon,lat=points['longitude'].to_numpy(),points['latitude'].to_numpy()
            inside_state=int(shapely.intersects_xy(state,lon,lat).sum())
            geometry=boundaries.get('19'+group['municipality_code'][0])
            if geometry is not None:inside_reported=int(shapely.intersects_xy(geometry,lon,lat).sum())
        results.append({'municipality':municipality,'year':year,'records':len(group),'coordinates':len(points),
                        'inside_state':inside_state,'inside_reported_municipality':inside_reported})
    report={'source':'INEGI · Marco Geoestadístico diciembre 2025, geometría original no simplificada.',
            'crs_assumption':'Se interpretan grados RATIV como WGS84 para el contraste; no confirma datum ni precisión.',
            'interpretation':'La discrepancia puede reflejar error de ubicación, captura, límites o jurisdicción de reporte. No se corrige ni elimina sin revisión.',
            'groups':results}
    (ROOT/'release/spatial-quality.json').write_text(json.dumps(report,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print(json.dumps({'known_coordinates':sum(r['coordinates'] for r in results),'inside_state':sum(r['inside_state'] for r in results),'inside_reported_municipality':sum(r['inside_reported_municipality'] for r in results)}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--records',type=Path,required=True);args=parser.parse_args();audit(args.records)
