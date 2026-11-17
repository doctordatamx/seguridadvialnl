"""Verificación de integración sobre artefactos reales, sin imprimir microdatos."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import polars as pl

ROOT=Path(__file__).resolve().parents[1]


def main():
    catalog=json.loads((ROOT/'reports/audit/SOURCE_CATALOG.json').read_text(encoding='utf-8'))
    data=pl.read_parquet(ROOT/'data/processed/crashes.parquet')
    payload=json.loads((ROOT/'web/public/data/observatory.json').read_text(encoding='utf-8'))
    spatial=json.loads((ROOT/'web/public/data/spatial.json').read_text(encoding='utf-8'))
    dbscan=json.loads((ROOT/'data/processed/dbscan_by_municipality_year.json').read_text(encoding='utf-8'))
    assert all(s['status']=='audited' for s in catalog)
    assert data.height==sum(s['accepted_rows'] for s in catalog)
    assert data['record_id'].n_unique()==data.height
    assert not set(data.columns).intersection({'Teléfono','Placa','No. Póliza','Licencia','Manifestación de los hechos','Edad','Sexo'})
    assert payload['mode']=='local_preview' and payload['release_approved'] is False
    for s in catalog:
        path=ROOT/'data/raw'/s['path']
        with path.open('rb') as stream:
            assert hashlib.file_digest(stream,'sha256').hexdigest()==s['sha256']
    counts=data.with_columns(pl.col('date').str.slice(0,7).alias('month')).group_by(['municipality','month']).len()
    expected={(r['municipality'],r['month']):r['len'] for r in counts.to_dicts()}
    assert len(expected)==len(payload['rows'])
    for row in payload['rows']:
        count=expected[row['municipality'],row['month']]
        assert row['crashes']==(None if count<payload['minimum_cell_size'] else count)
        for field in ['injured','deaths']:
            assert row[field] is None or row[field]==0 or row[field]>=payload['minimum_cell_size']
            assert row[field+'_status'] in {'known','missing','suppressed'}
    for feature in spatial['features']:
        assert feature['properties']['crashes']>=10
        assert set(feature['properties'])=={'cell','municipality','year','crashes'}
        ring=feature['geometry']['coordinates'][0]
        assert ring[0]==ring[-1]
    for group in dbscan['groups']:
        if group['status']=='computed':
            assert group['noise_records']+sum(c['records'] for c in group['clusters'])==group['records']
    report={'verified_at':datetime.now(timezone.utc).isoformat(),'status':'passed','records':data.height,
            'municipality_year_profiles':len(payload['profiles']),'monthly_cells':len(payload['rows']),
            'h3_features':len(spatial['features']),'dbscan_groups':len(dbscan['groups']),
            'checks':['original_hashes','unique_technical_ids','canonical_whitelist','local_release_gate','monthly_reconciliation','suppression','h3_thresholds','dbscan_mass_balance']}
    (ROOT/'reports/audit/VERIFICATION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=True))


if __name__=='__main__':
    main()
