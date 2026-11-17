"""Verifica la edición real y contratos que previenen recuperación de desenlaces ocultos."""
import json
from pathlib import Path
import pytest
from scripts.build_intelligence import stats
from pipelines.intelligence import ipiv,DEFAULT_WEIGHTS

ROOT=Path(__file__).resolve().parents[1]


def test_units_persons_not_records_and_missing_stays_missing():
    row={'deaths':2,'injured':3,'pedestrian_deaths':0,'pedestrian_injured':0,'vulnerable_user':None}
    result=stats([row,{**row,'deaths':0,'injured':0}])
    assert result['mortality']==2 and result['fatal_records']==1
    assert result['injuries']==3 and result['victim_records']==1
    missing=stats([row,{**row,'deaths':None}])
    assert missing['mortality'] is None and missing['fatal_records'] is None


def test_materialized_reference_and_clinical_derivatives_are_protected():
    data=json.loads((ROOT/'release/intelligence.json').read_text(encoding='utf-8'))
    assert data['reference']['population_size']==len(data['zones'])
    assert len({z['id'] for z in data['zones']})==len(data['zones'])
    for z in data['zones']:
        expected=ipiv(z['normalized']['minmax'],DEFAULT_WEIGHTS)
        assert z['score']==pytest.approx(expected) if expected is not None else z['score'] is None
        for k in ['mortality','injuries','fatal_records','victim_records','pedestrian_records']:
            assert z['metrics'][k] is None or z['metrics'][k]==0 or z['metrics'][k]>=5
        if z['metrics']['fatal_records'] is None:assert z['metrics']['severity'] is None


def test_real_radar_never_labels_missing_coverage_stable_or_fills_low_counts():
    data=json.loads((ROOT/'release/intelligence.json').read_text(encoding='utf-8'))
    for r in data['radar']:
        if r['q_value'] is None:assert r['classification']=='Información insuficiente'
        if r['statistical_alert']:
            assert r['q_value']<.05 and r['ratio']>1 and r['comparable_proxy']
            assert r['current']>=5 and r['previous']>=10
    for r in data['epidemiology']:
        if r['year']!='2020':assert r['registered_mortality_rate'] is None
        if r['metrics']['mortality'] is None:assert r['deaths_per100_records'] is None and r['mortality_ci95'] is None
