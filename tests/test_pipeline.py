"""Fixtures sintéticos exclusivamente de prueba. Nunca son resultados del observatorio."""
import json
from pathlib import Path
import polars as pl
import pytest
from pipelines.run import canonicalize, aggregates, parse_count, run, read_tables


def source():
    return {'id': 'fixture.csv', 'date_format': '%d/%m/%Y', 'observation_unit': 'crash',
            'columns': {'event_id': 'id', 'date': 'fecha', 'municipality': 'municipio', 'deaths': 'muertes', 'latitude': 'lat', 'longitude': 'lon'},
            'coordinate_crs': 'EPSG:4326', 'license': 'TEST ONLY', 'redistribution_approved': True, 'privacy_reviewed': True}


def fixture_rows(n=6):
    return [{'id': str(i), 'fecha': '01/01/2025', 'municipio': ' municipio de prueba ', 'muertes': '0', 'lat': '25.7', 'lon': '-100.3'} for i in range(n)]


def test_null_is_not_zero_and_bad_counts_rejected():
    assert parse_count(None) is None
    assert parse_count('') is None
    assert parse_count('0') == 0
    for value in ['-1', 'NaN', '1.5', 'inf']:
        with pytest.raises(ValueError):
            parse_count(value)


def test_invalid_rows_duplicates_coordinates():
    records = fixture_rows()
    records += [records[0], {**records[1], 'id':'99', 'fecha':'31/02/2025'}, {**records[2], 'id':'100', 'lat':'0'}]
    rows, issues = canonicalize(pl.from_dicts(records), source(), 'test')
    assert len(rows) == 7
    assert issues == {'duplicate_event_id':1, 'rejected_rows':1, 'invalid_coordinates':1}
    assert rows[-1]['latitude'] is None
    assert rows[0]['municipality'] == 'MUNICIPIO DE PRUEBA'


def test_suppression_and_incomplete_sum():
    rows, _ = canonicalize(pl.from_dicts(fixture_rows()), source(), 'test')
    assert aggregates(rows[:4],5)[0]['crashes'] is None
    rows[0]['deaths'] = 1
    out = aggregates(rows,5)[0]
    assert out['crashes'] == 6
    assert out['deaths'] is None
    assert out['injured'] is None
    rows[0]['deaths'] = None
    assert aggregates(rows,5)[0]['deaths'] is None


def setup_root(tmp_path):
    (tmp_path/'config').mkdir()
    (tmp_path/'data/raw').mkdir(parents=True)
    config = {'sources': [], 'privacy': {'minimum_cell_size':5}, 'hotspots':{'h3_resolutions':[7,8,9], 'dbscan_eps_meters':150, 'dbscan_min_samples':5}}
    (tmp_path/'config/sources.json').write_text(json.dumps(config))
    return config


def test_empty_run_and_outputs(tmp_path):
    setup_root(tmp_path)
    payload = run(tmp_path)
    assert payload['rows'] == []
    assert payload['status'] == 'awaiting_data'
    for filename in ['DATA_AUDIT.md','DATA_DICTIONARY.csv','DATA_QUALITY_REPORT.html','SOURCE_CATALOG.json','MUNICIPAL_COVERAGE.csv']:
        assert (tmp_path/'reports/audit'/filename).exists()
    assert pl.read_parquet(tmp_path/'data/processed/crashes.parquet').height == 0


def test_reproducibility_hash_and_revocation(tmp_path):
    config = setup_root(tmp_path)
    pl.from_dicts(fixture_rows()).write_csv(tmp_path/'data/raw/fixture.csv')
    config['sources'] = [source()]
    cfg = tmp_path/'config/sources.json'
    cfg.write_text(json.dumps(config))
    first = run(tmp_path)
    second = run(tmp_path)
    assert first['rows'] == second['rows']
    assert first['rows'][0]['crashes'] == 6
    config['sources'][0]['redistribution_approved'] = False
    cfg.write_text(json.dumps(config))
    assert run(tmp_path)['rows'] == []
    assert not list((tmp_path/'web/public/data').glob('*.parquet'))


def test_json_no_implicit_structure(tmp_path):
    path = tmp_path/'x.json'
    path.write_text('{"datos": []}')
    with pytest.raises(ValueError):
        list(read_tables(path))


def test_schema_drift(tmp_path):
    setup_root(tmp_path)
    path = tmp_path/'data/raw/fixture.csv'
    pl.from_dicts(fixture_rows()).write_csv(path)
    run(tmp_path)
    pl.from_dicts([{**r,'new':'x'} for r in fixture_rows()]).write_csv(path)
    run(tmp_path)
    catalog = json.loads((tmp_path/'reports/audit/SOURCE_CATALOG.json').read_text())
    assert catalog[0]['schema_changed'] is True


def test_excel_all_sheets(tmp_path):
    import pandas as pd
    path = tmp_path/'two.xlsx'
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame({'a':[1,2]}).to_excel(writer,sheet_name='A',index=False)
        pd.DataFrame({'b':[3]}).to_excel(writer,sheet_name='B',index=False)
    assert [(name,frame.height) for name,frame,_ in read_tables(path)] == [('A',2),('B',1)]


def test_gzip_csv_preserves_codes(tmp_path):
    import gzip
    path = tmp_path/'source.csv.gz'
    with gzip.open(path, 'wt', encoding='utf-8') as stream:
        stream.write('code,count\n001,0\n002,\n')
    _, frame, _ = next(read_tables(path))
    assert frame['code'].to_list() == ['001','002']
    assert frame['count'].to_list() == ['0',None]
