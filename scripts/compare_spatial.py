"""Comparación exploratoria local en UTM 14N, sin publicar puntos ni asignaciones."""
import argparse,json,sys
from collections import Counter
from pathlib import Path
import numpy as np
import polars as pl
from pyproj import Transformer
from sklearn.cluster import DBSCAN,HDBSCAN
from sklearn.neighbors import KernelDensity
from scipy.stats import spearmanr

ROOT=Path(__file__).resolve().parents[1]


def compare(path):
    data=pl.read_parquet(path).filter(pl.col('date').str.starts_with('2025')&pl.col('latitude').is_not_null())
    transform=Transformer.from_crs(4326,32614,always_xy=True)
    results=[]
    for (municipality,),group in data.group_by('municipality',maintain_order=True):
        lon,lat=group['longitude'].to_numpy(),group['latitude'].to_numpy()
        x,y=transform.transform(lon,lat);coordinates=np.column_stack([x,y])
        unique,weights=np.unique(coordinates,axis=0,return_counts=True)
        db=DBSCAN(eps=150,min_samples=5).fit_predict(unique,sample_weight=weights)
        hb=HDBSCAN(min_cluster_size=20,min_samples=5,copy=True).fit_predict(coordinates)
        results.append({'municipality':municipality,'records':len(group),'unique_positions':len(unique),
                        'dbscan_clusters':len(set(db)-{-1}),'dbscan_noise_records':int(sum(weights[db==-1])),
                        'hdbscan_clusters':len(set(hb)-{-1}),'hdbscan_noise_records':int(sum(hb==-1))})
    longitude,latitude=data['longitude'].to_numpy(),data['latitude'].to_numpy()
    x,y=transform.transform(longitude,latitude);unique,weights=np.unique(np.column_stack([x,y]),axis=0,return_counts=True)
    kde=KernelDensity(bandwidth=200,kernel='gaussian').fit(unique,sample_weight=weights)
    intelligence=json.loads((ROOT/'release/intelligence.json').read_text(encoding='utf-8'))
    centers=np.array([z['center'] for z in intelligence['zones']]);cx,cy=transform.transform(centers[:,0],centers[:,1])
    density=kde.score_samples(np.column_stack([cx,cy]));relative=np.exp(density-np.max(density))*100
    rho=float(spearmanr(relative,[z['metrics']['frequency'] for z in intelligence['zones']]).statistic)
    result={'year':2025,'crs_working':'EPSG:32614','crs_input_assumption':'WGS84 geográfico supuesto; datum RATIV no declarado.',
            'dbscan':{'eps_meters':150,'min_samples':5,'weighted_duplicate_positions':True},
            'hdbscan':{'min_cluster_size':20,'min_samples':5},'kde':{'bandwidth_meters':200,'kernel':'gaussian','evaluation':'Centroides de las celdas fijas R7; densidad relativa, no riesgo.'},
            'groups':results,'frequency_kde_spearman':rho,
            'kde_cells':[{'zone_id':z['id'],'relative_density':round(float(v),4)} for z,v in zip(intelligence['zones'],relative)],
            'limitations':['Distintas unidades y parámetros: el número de clústeres no mide superioridad metodológica.',
                           'Los clústeres se calculan por municipio: las fronteras pueden fragmentar concentraciones.',
                           'Coordenadas repetidas pueden proceder de geocodificación aproximada; no son necesariamente eventos en un mismo punto.',
                           'KDE evalúa una población seleccionada de celdas; correlación descriptiva sin inferencia causal.',
                           'No se publican geometrías de clústeres ni coordenadas individuales.']}
    (ROOT/'release/methods.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'),allow_nan=False),encoding='utf-8')
    print(json.dumps({'groups':len(results),'dbscan_clusters':sum(g['dbscan_clusters'] for g in results),'hdbscan_clusters':sum(g['hdbscan_clusters'] for g in results),'kde_cells':len(relative),'spearman':rho}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--records',type=Path,required=True);args=parser.parse_args();compare(args.records)
