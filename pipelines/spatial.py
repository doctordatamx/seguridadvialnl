"""DBSCAN de investigación por municipio y año; coordenadas repetidas con peso."""
from collections import Counter, defaultdict


def grouped_dbscan(rows, eps_meters=150, min_samples=5, max_unique_points=50000):
    import numpy as np
    from sklearn.cluster import DBSCAN
    groups = defaultdict(Counter)
    for r in rows:
        if r['latitude'] is not None:
            groups[(r['municipality'], r['date'][:4])][(r['latitude'], r['longitude'])] += 1
    results = []
    for (municipality, year), positions in sorted(groups.items()):
        count = sum(positions.values())
        if len(positions) > max_unique_points:
            results.append({'municipality':municipality,'year':year,'status':'deferred_size_guard','records':count})
            continue
        labels = DBSCAN(eps=eps_meters/6371008.8, min_samples=min_samples, metric='haversine', algorithm='ball_tree').fit_predict(np.radians(list(positions)), sample_weight=list(positions.values()))
        totals = Counter()
        for label, weight in zip(labels, positions.values()):
            totals[int(label)] += weight
        results.append({'municipality':municipality,'year':year,'status':'computed','records':count,
                        'unique_positions':len(positions),'noise_records':totals.pop(-1,0),
                        'clusters':[{'cluster':k,'records':v} for k,v in totals.most_common()]})
    return {'scope':'municipality_year','eps_meters':eps_meters,'min_samples':min_samples,
            'weighted_duplicate_positions':True,'groups':results,
            'warning':'Exploración local: datum no declarado, coordenadas no validadas contra límites. No son puntos críticos validados.'}
