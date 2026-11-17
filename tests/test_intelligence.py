import math
import pytest
from pipelines.intelligence import normalize,normalize_against,ipiv,priority,bh_adjust,rate_comparison,poisson_rate_interval,protected_counts,protected_spatial_counts,fixed_reference,DIMENSIONS


@pytest.mark.parametrize('method',['minmax','percentile','robust','logminmax'])
def test_normalization_retains_missing_and_constants(method):
    values=normalize([None,0,5,10],method)
    assert values[0] is None
    assert values[1]==0 and values[-1]==100
    assert normalize([2,2,None],method)==[0,0,None]
    assert normalize([None,None],method)==[None,None]


def test_essential_dimension_remains_required_even_at_zero_weight():
    components=dict.fromkeys(DIMENSIONS,50)
    assert ipiv(components)==50
    components['mortality']=None
    assert ipiv(components,dict(zip(DIMENSIONS,[100,0,0,0,0]))) is None
    assert priority(None)=='No calculable'
    assert priority(25)=='Moderada' and priority(75)=='Muy alta'


def test_signed_log_keeps_negative_trend_and_extreme_is_clipped():
    result=normalize([-100,-10,0,100],'logminmax')
    assert result[0]==0 and result[-1]==100 and 0<result[1]<result[2]<100
    result=normalize([0,1,2,3,4,1000],'robust')
    assert result[0]==0 and result[-1]==100


def test_fdr_monotone_and_missing_not_zero():
    values=bh_adjust([.001,.01,.2,None])
    assert values[:3]==pytest.approx([.003,.015,.2])
    assert values[3] is None


def test_rate_comparison_refuses_noncomparability_and_low_counts():
    assert rate_comparison(200,20,30,30,False)['p_value'] is None
    assert rate_comparison(15,5,30,30,True)['p_value'] is None
    identical=rate_comparison(20,20,30,30,True)
    assert identical['p_value']==1 and identical['ratio']==1
    assert identical['ci95'][0]<1<identical['ci95'][1]
    assert rate_comparison(100,20,30,30,True)['p_value']<.001


def test_rates_zero_is_valid_without_invented_denominator():
    assert poisson_rate_interval(None,100000) is None
    assert poisson_rate_interval(5,None) is None
    result=poisson_rate_interval(0,100000)
    assert result[0]==0 and result[1]>0


def test_suppression_precedes_scoring_and_preserves_real_zero():
    assert protected_counts([0,1,10,20])==[0,None,None,20]
    zones=[{'dimensions':dict.fromkeys(DIMENSIONS,0)}, {'dimensions':dict.fromkeys(DIMENSIONS,10)}]
    zones[1]['dimensions']['mortality']=None
    reference=fixed_reference(zones)
    assert zones[1]['score'] is None and zones[0]['score'] is not None
    before=zones[0]['score']
    # Filtrar la población ya materializada no recalibra los parámetros.
    filtered=[zones[0]]
    assert filtered[0]['score']==before and reference['population_size']==2


def test_historical_values_use_fixed_reference_not_filtered_range():
    assert normalize_against([10,20,None],[0,100])==[10,20,None]
    assert normalize_against([10],[0,100])==[10]
    assert normalize_against([200],[0,100])==[100]
    assert normalize_against([0,5,10],[0,5,10],'percentile')==[0,50,100]


def test_complementary_suppression_respects_municipal_margins():
    values,withheld=protected_spatial_counts([1,5,6],[['A'],['B'],['A']])
    assert values==[None,None,None] and withheld=={'A','B'}
    values,withheld=protected_spatial_counts([1,0,10],[['A'],['A'],['B']])
    assert values[0] is None and 'A' in withheld
