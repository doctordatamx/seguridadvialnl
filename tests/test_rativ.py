"""Contratos semánticos RATIV con fixtures aislados, sin datos personales reales."""
import polars as pl
from pipelines.rativ import canonicalize_rativ, report_hour, geographic_pair, count_value, disjoint_partitions, protected_histogram
from collections import Counter
import pytest


def fixture():
    return {'MUNICIPIO':'39','ENCUESTA':'99','Día':'1','Mes':'1','Año':'2025','Hora de reporte':'0.5',
            'Total de lesionados':'0','Total de fallecidos':'0','Tipo de Hecho de Tránsito':'Alcance',
            'VEHICULO CODIFICADO':'1','VEHICULO CODIFICADO 2':'5','Referencia':'25.7,-100.3',
            'Calle':'AVENIDA DE PRUEBA','Total de lesionados PEAT':'0','Total de fallecidos PEAT':'0',
            'Teléfono':'DATO NO EXPORTABLE','Placa':'DATO NO EXPORTABLE','Manifestación de los hechos':'DATO NO EXPORTABLE'}


def test_report_time_excel_and_ambiguous_date():
    assert report_hour('0.5') == (12,'excel_fraction_time')
    assert report_hour(' 09:45:00 ')[0] == 9
    assert report_hour('23:59')[0] == 23
    for value in ['99','1900-04-08 00:00:00','24:00','12:99','45120']:
        assert report_hour(value)[0] is None


def test_missing_codes_and_zero():
    assert count_value('99') is None
    assert count_value('SD') is None
    assert count_value('0') == 0
    with pytest.raises(ValueError):
        count_value('-1')


def test_coordinates_no_geocoding_or_swapping():
    assert geographic_pair('25.7, -100.3')[:2] == (25.7,-100.3)
    for value in ['entre calle 25 y 100','-100.3,25.7','99','0,0','25.7,-100.3 texto']:
        assert geographic_pair(value)[0] is None


def test_repeated_folios_preserved_and_sensitive_fields_excluded():
    source={'observation_unit':'crash_record','partition_year':2025,'columns':{'street':'Calle'}}
    rows,issues=canonicalize_rativ(pl.from_dicts([fixture(),fixture()]),source,'test')
    assert len(rows)==2
    assert rows[0]['record_id'] != rows[1]['record_id']
    assert rows[0]['event_id'] is None
    assert rows[0]['weekday']==2  # 2025-01-01 es miércoles, lunes=0
    assert rows[0]['hour']==12
    assert rows[0]['vulnerable_user']=='Motocicleta involucrada'
    assert 'Teléfono' not in rows[0] and 'Placa' not in rows[0]
    assert 'DATO NO EXPORTABLE' not in str(rows)
    assert issues['missing_source_folio']==2


def test_partition_guard_requires_real_disjoint_years():
    rows=[{'source':'a','date':'2024-01-01'},{'source':'b','date':'2025-01-01'}]
    assert disjoint_partitions(rows,[{'id':'a','partition_year':2024},{'id':'b','partition_year':2025}])
    assert not disjoint_partitions(rows,[{'id':'a','partition_year':2024},{'id':'b','partition_year':2024}])
    assert not disjoint_partitions(rows,[{'id':'a','partition_year':2024},{'id':'b','partition_year':2026}])


def test_histogram_complementary_suppression():
    result=protected_histogram(Counter({'a':1,'b':10,'c':20}),5)
    assert {r['name'] for r in result if r['suppressed']} == {'a','b'}


def test_dbscan_weights_and_time_partition():
    from pipelines.spatial import grouped_dbscan
    rows=[{'municipality':'PRUEBA','date':'2025-01-01','latitude':25.7,'longitude':-100.3} for _ in range(5)]
    rows += [{'municipality':'PRUEBA','date':'2024-01-01','latitude':25.7,'longitude':-100.3}]
    result=grouped_dbscan(rows)
    assert result['groups'][0]['noise_records']==1
    assert result['groups'][1]['clusters']==[{'cluster':0,'records':5}]
    assert result['groups'][1]['unique_positions']==1
