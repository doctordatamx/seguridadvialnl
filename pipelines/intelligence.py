"""Métodos puros de priorización y vigilancia. Nunca imputan datos faltantes."""
from __future__ import annotations
import math
import numpy as np
from scipy.stats import binomtest, rankdata, spearmanr, chi2

DIMENSIONS = ['frequency','mortality','injuries','trend','vulnerable']
DEFAULT_WEIGHTS = dict(zip(DIMENSIONS,[30,30,20,10,10]))
METHODS = ['minmax','percentile','robust','logminmax']


def finite(value):
    return value is not None and math.isfinite(float(value))


def normalize(values, method):
    if method not in METHODS:
        raise ValueError('Normalización desconocida')
    mask=np.array([finite(v) for v in values]); output=[None]*len(values)
    x=np.array([float(v) for v in values if finite(v)])
    if not len(x):return output
    if method=='percentile':
        y=(rankdata(x,method='average')-1)/(len(x)-1)*100 if len(x)>1 and np.ptp(x)>0 else np.zeros(len(x))
    else:
        if method=='logminmax':
            # signed log preserva tendencias negativas sin convertirlas en cero.
            x=np.sign(x)*np.log1p(np.abs(x))
        low,high=np.quantile(x,[.05,.95]) if method=='robust' else (np.min(x),np.max(x))
        y=np.clip((x-low)/(high-low)*100,0,100) if high>low else np.zeros(len(x))
    for i,value in zip(np.flatnonzero(mask),y):output[int(i)]=round(float(value),6)
    return output


def ipiv(components,weights=DEFAULT_WEIGHTS):
    if any(not finite(components.get(d)) for d in DIMENSIONS):return None
    if set(weights)!=set(DIMENSIONS) or any(not finite(v) or v<0 for v in weights.values()) or sum(weights.values())<=0:
        raise ValueError('Pesos inválidos')
    return sum(components[d]*weights[d] for d in DIMENSIONS)/sum(weights.values())


def normalize_against(values,reference,method='minmax'):
    """Aplica calibración ya fijada; la serie histórica no se ajusta a su propio rango."""
    if method not in METHODS:raise ValueError('Normalización desconocida')
    ref=np.array([float(v) for v in reference if finite(v)])
    if not len(ref):return [None]*len(values)
    if np.ptp(ref)==0:return [None if not finite(v) else 0. for v in values]
    if method=='logminmax':ref=np.sign(ref)*np.log1p(np.abs(ref))
    low,high=np.quantile(ref,[.05,.95]) if method=='robust' else (np.min(ref),np.max(ref))
    output=[]
    for value in values:
        if not finite(value):output.append(None);continue
        x=float(value)
        if method=='percentile':
            less=int(sum(ref<x));equal=int(sum(ref==x));position=less+(equal+1)/2
            y=(position-1)/(len(ref)-1)*100
        else:
            if method=='logminmax':x=float(np.sign(x)*np.log1p(abs(x)))
            y=(x-low)/(high-low)*100 if high>low else 0.
        output.append(round(float(np.clip(y,0,100)),6))
    return output


def priority(score):
    return 'No calculable' if score is None else 'Baja' if score<25 else 'Moderada' if score<50 else 'Alta' if score<75 else 'Muy alta'


def bh_adjust(p_values):
    out=[None]*len(p_values);valid=[i for i,p in enumerate(p_values) if finite(p)]
    order=sorted(valid,key=lambda i:p_values[i]);previous=1.
    for rank,i in reversed(list(enumerate(order,start=1))):
        previous=min(previous,p_values[i]*len(order)/rank);out[i]=min(previous,1.)
    return out


def rate_comparison(current,previous,current_days,previous_days,comparable):
    if not comparable or current is None or previous is None or min(current_days,previous_days)<=0 or current+previous<20 or previous<10:
        return {'status':'Información insuficiente','p_value':None,'ratio':None,'ci95':None}
    # Condicional a N, dos Poisson independientes con distinta duración producen una binomial.
    test=binomtest(current,current+previous,p=current_days/(current_days+previous_days),alternative='two-sided')
    interval=test.proportion_ci(confidence_level=.95,method='exact')
    to_ratio=lambda p: p/(1-p)*previous_days/current_days if p<1 else None
    return {'status':'Contraste condicional exploratorio','p_value':float(test.pvalue),
            'ratio':current/current_days/(previous/previous_days),
            'ci95':[to_ratio(interval.low),to_ratio(interval.high)]}


def poisson_rate_interval(count,population):
    if count is None or population is None or population<=0:return None
    low=0. if count==0 else chi2.ppf(.025,2*count)/2
    high=chi2.ppf(.975,2*(count+1))/2
    return [float(low/population*100000),float(high/population*100000)]


def fixed_reference(zones):
    """Parámetros se ajustan una sola vez a la población versionada, nunca a filtros UI."""
    for z in zones:z['normalized']={m:{} for m in METHODS}
    for method in METHODS:
        for dim in DIMENSIONS:
            values=normalize([z['dimensions'][dim] for z in zones],method)
            for z,value in zip(zones,values):z['normalized'][method][dim]=value
    scenarios={'base':DEFAULT_WEIGHTS,'frequency':dict(zip(DIMENSIONS,[50,20,15,10,5])),
               'mortality':dict(zip(DIMENSIONS,[20,45,20,10,5])), 'vulnerable':dict(zip(DIMENSIONS,[25,25,15,10,25]))}
    for z in zones:
        z['score']=ipiv(z['normalized']['minmax']);z['priority']=priority(z['score'])
        scores=[ipiv(z['normalized'][m],w) for m in METHODS for w in scenarios.values()]
        known=[s for s in scores if s is not None]
        z['sensitivity']={'score_min':min(known) if known else None,'score_max':max(known) if known else None}
        z['missing_dimensions']=[d for d in DIMENSIONS if z['dimensions'][d] is None]
    complete=[z for z in zones if z['score'] is not None]
    correlations=[]
    for i,first in enumerate(DIMENSIONS):
        for second in DIMENSIONS[i+1:]:
            a=[z['dimensions'][first] for z in complete];b=[z['dimensions'][second] for z in complete]
            rho=float(spearmanr(a,b).statistic) if len(a)>=10 and np.ptp(a)>0 and np.ptp(b)>0 else None
            correlations.append({'first':first,'second':second,'rho':rho,'n':len(a)})
    stability=[]
    if complete:
        baseline=[z['score'] for z in complete]
        for m in METHODS:
            for name,w in scenarios.items():
                alternative=[ipiv(z['normalized'][m],w) for z in complete]
                rho=float(spearmanr(baseline,alternative).statistic) if len(complete)>2 and np.ptp(baseline)>0 and np.ptp(alternative)>0 else None
                top=lambda values:set(np.argsort(values)[-min(10,len(values)):].tolist())
                stability.append({'method':m,'weights':name,'spearman':rho,'top10_overlap':len(top(baseline)&top(alternative))})
    return {'population_size':len(zones),'complete_cases':len(complete),'weights':DEFAULT_WEIGHTS,'methods':METHODS,
            'correlations_complete_cases':correlations,'rank_stability':stability,
            'constant_dimension_policy':'Dimensión constante=0: no aporta discriminación; nulos permanecen nulos.'}


def protected_counts(values,minimum=5):
    hidden={i for i,n in enumerate(values) if n is not None and 0<n<minimum}
    if len(hidden)==1:
        others=[i for i,n in enumerate(values) if i not in hidden and n is not None and n>0]
        if others:hidden.add(min(others,key=lambda i:values[i]))
    return [None if i in hidden else n for i,n in enumerate(values)]


def protected_spatial_counts(values,memberships,minimum=5):
    """Complementa la supresión considerando los márgenes municipales superpuestos."""
    output=protected_counts(values,minimum);withheld_margins=set()
    municipalities=sorted({m for members in memberships for m in members})
    for municipality in municipalities:
        family=[i for i,members in enumerate(memberships) if municipality in members]
        if not any(values[i] is not None and 0<values[i]<minimum for i in family):continue
        # Una supresión complementaria de tamaño mayor debe existir en la misma familia.
        if any(output[i] is None and values[i] is not None and values[i]>=minimum for i in family):continue
        candidates=[i for i in family if output[i] is not None and values[i]>=minimum]
        if candidates:output[min(candidates,key=lambda i:values[i])]=None
        else:withheld_margins.add(municipality)
    # No publicar un margen municipal que toque una variable espacial oculta:
    # las celdas pueden solaparse con varios municipios y formar sistemas de ecuaciones.
    withheld_margins.update(m for i,members in enumerate(memberships) if output[i] is None for m in members)
    return output,withheld_margins
